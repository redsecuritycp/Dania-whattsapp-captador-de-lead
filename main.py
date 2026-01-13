"""
DANIA/Fortia WhatsApp Bot - Main Application
FastAPI con webhooks para WhatsApp y Cal.com
Incluye scheduler para recordatorios automáticos
"""
import os
import sys
import json
import logging
import warnings

warnings.filterwarnings("ignore", message="Can not find any timezone")
import time
from datetime import datetime
from contextlib import asynccontextmanager
from collections import OrderedDict

import pytz
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse

from config import detect_country, WHATSAPP_VERIFY_TOKEN, format_fecha_es
from services.whatsapp import send_whatsapp_message, mark_as_read
from services.openai_agent import process_message
from services.mongodb import (update_lead_booking, get_database,
                              find_lead_by_email_calcom, get_lead_field)
from services.reminders import (init_scheduler, shutdown_scheduler,
                                send_booking_confirmation,
                                send_booking_cancellation,
                                send_booking_rescheduled,
                                reset_reminders_for_lead)

# Configurar buffering para logs inmediatos
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configurar logging con flush inmediato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True)

# Forzar flush en cada log
for handler in logging.root.handlers:
    handler.flush()

logger = logging.getLogger(__name__)

# =============================================================================
# DEDUPLICACIÓN DE WEBHOOKS (evita rate limit por retries de WhatsApp)
# =============================================================================


class MessageDeduplicator:
    """Cache de message_ids procesados. TTL 5 minutos, max 1000 entries."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self._cache = OrderedDict()
        self._ttl = ttl_seconds
        self._max_size = max_size

    def is_duplicate(self, message_id: str) -> bool:
        """Retorna True si el mensaje ya fue procesado (webhook duplicado)."""
        self._cleanup()
        if message_id in self._cache:
            return True
        self._cache[message_id] = time.time()
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
        return False

    def _cleanup(self):
        """Elimina entries expirados."""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v > self._ttl]
        for k in expired:
            del self._cache[k]


message_dedup = MessageDeduplicator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup y shutdown de la aplicación."""
    # Startup
    logger.info("🚀 Iniciando DANIA/Fortia WhatsApp Bot...")

    # Verificar conexión a MongoDB
    db = get_database()
    if db is not None:
        logger.info("✅ MongoDB conectado")
    else:
        logger.warning("⚠️ MongoDB no conectado - verificar MONGODB_URI")

    # Verificar variables de entorno críticas
    required_vars = [
        "WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "OPENAI_API_KEY"
    ]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.warning(f"⚠️ Variables faltantes: {missing}")
    else:
        logger.info("✅ Variables de entorno configuradas")

    # Iniciar scheduler de recordatorios
    try:
        from services.reminders import init_scheduler
        sched = init_scheduler()
        if sched and sched.running:
            logger.info("✅ Scheduler de recordatorios ACTIVO")
        else:
            logger.error("❌ Scheduler NO está corriendo")
    except Exception as e:
        logger.error(f"⚠️ Error iniciando scheduler: {e}")

    # Recovery de recordatorios pendientes
    try:
        from services.reminders import recuperar_recordatorios_pendientes
        import asyncio
        asyncio.create_task(recuperar_recordatorios_pendientes())
        logger.info("✅ Recovery de recordatorios iniciado")
    except Exception as e:
        logger.error(f"⚠️ Error en recovery de recordatorios: {e}")

    yield

    # Shutdown
    logger.info("👋 Cerrando aplicación...")
    try:
        shutdown_scheduler()
    except:
        pass


app = FastAPI(title="DANIA/Fortia WhatsApp Bot",
              description=
              "Bot de WhatsApp para captación y cualificación de leads con IA",
              version="2.0.0",
              lifespan=lifespan)

# =============================================================================
# HEALTH CHECK
# =============================================================================


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "DANIA/Fortia WhatsApp Bot",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    """Health check detallado."""
    db = get_database()
    return {
        "status": "healthy",
        "mongodb": "connected" if db is not None else "disconnected",
        "scheduler": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# WHATSAPP WEBHOOK
# =============================================================================


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Verificación del webhook de WhatsApp (GET).
    Meta envía este request para verificar el endpoint.
    """
    params = request.query_params

    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")

    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN",
                                  WHATSAPP_VERIFY_TOKEN)

    if mode == "subscribe" and token == verify_token:
        logger.info("✅ Webhook verificado correctamente")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        logger.warning(f"❌ Verificación fallida: mode={mode}, token={token}")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe mensajes de WhatsApp (POST).
    Procesa en background para responder rápido a Meta.
    """
    try:
        body = await request.json()

        # Extraer datos del webhook
        entry_list = body.get("entry", [])
        if not entry_list:
            return JSONResponse({"status": "ok"})
        entry = entry_list[0] if entry_list else {}

        changes_list = entry.get("changes", [])
        if not changes_list:
            return JSONResponse({"status": "ok"})
        changes = changes_list[0] if changes_list else {}
        value = changes.get("value", {})

        # Verificar si es un mensaje (no status update)
        messages = value.get("messages", [])

        if not messages:
            # Es un status update, ignorar
            return JSONResponse({"status": "ok"})

        message = messages[0] if messages else {}
        message_id = message.get("id", "")

        # Deduplicación: ignorar webhooks duplicados (retries de WhatsApp)
        if message_id and message_dedup.is_duplicate(message_id):
            logger.debug(
                f"⏭️ Webhook duplicado ignorado: {message_id[:20]}...")
            return JSONResponse({"status": "ok"})

        from_number = message.get("from", "")
        message_type = message.get("type", "")

        # Obtener texto del mensaje
        if message_type == "text":
            text_obj = message.get("text", {})
            text = text_obj.get("body", "") if isinstance(text_obj,
                                                          dict) else ""
            audio_id = ""
        elif message_type == "audio":
            audio_obj = message.get("audio", {})
            audio_id = audio_obj.get("id", "") if isinstance(audio_obj,
                                                             dict) else ""
            text = ""  # Se obtendrá por transcripción
        else:
            text = f"[Mensaje tipo {message_type} recibido]"
            audio_id = ""

        if (not text and not audio_id) or not from_number:
            return JSONResponse({"status": "ok"})

        logger.info(
            f"📩 Mensaje de {from_number}: {text[:50] if text else '[AUDIO]'}..."
        )

        original_message_type = message_type

        # Procesar en background
        background_tasks.add_task(process_whatsapp_message, from_number, text,
                                  message_id, message_type, audio_id,
                                  original_message_type)

        # Responder rápido a Meta
        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Error en webhook WhatsApp: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


async def process_whatsapp_message(from_number: str,
                                   text: str,
                                   message_id: str,
                                   message_type: str = "text",
                                   audio_id: str = "",
                                   original_message_type: str = "text"):
    """
    Procesa un mensaje de WhatsApp en background.
    Soporta texto y audio.
    """
    try:
        # Marcar como leído
        await mark_as_read(message_id)

        # Si es audio, transcribir primero
        if message_type == "audio" and audio_id:
            from services.whatsapp import get_media_url, download_media, transcribe_audio

            logger.info(f"[AUDIO] Procesando audio de {from_number}...")

            # Paso 1: Obtener URL
            media_url = await get_media_url(audio_id)
            if not media_url:
                await send_whatsapp_message(
                    from_number,
                    "No pude procesar el audio. ¿Podés escribirme el mensaje?")
                return

            # Paso 2: Descargar
            audio_bytes = await download_media(media_url)
            if not audio_bytes:
                await send_whatsapp_message(
                    from_number,
                    "No pude descargar el audio. ¿Podés intentar de nuevo?")
                return

            # Paso 3: Transcribir
            text = await transcribe_audio(audio_bytes)
            if not text:
                await send_whatsapp_message(
                    from_number,
                    "No pude transcribir el audio. ¿Podés escribirme el mensaje?"
                )
                return

            logger.info(f"[AUDIO] ✓ Transcrito: {text[:50]}...")

        # Detectar país y zona horaria
        phone_whatsapp = f"+{from_number}"
        country_info = detect_country(from_number)

        # Procesar con el agente
        response = await process_message(
            user_message=text,
            phone_whatsapp=phone_whatsapp,
            country_detected=country_info.get("country", ""),
            country_code=country_info.get("code", ""),
            timezone_detected=country_info.get("timezone", ""),
            utc_offset=country_info.get("utc", ""),
            emoji=country_info.get("emoji", ""),
            city_detected=country_info.get("city", ""),
            province_detected=country_info.get("province", ""),
            original_message_type=original_message_type)

        if response is not None and response and original_message_type == "text":
            result = await send_whatsapp_message(from_number, response)

            if result.get("success"):
                logger.info(f"✅ Respuesta enviada a {from_number}")
            else:
                logger.error(
                    f"❌ Error enviando respuesta: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        try:
            await send_whatsapp_message(
                from_number,
                "Lo siento, hubo un error procesando tu mensaje. Por favor intentá de nuevo."
            )
        except:
            pass


# =============================================================================
# CAL.COM WEBHOOK - MEJORADO CON NOTIFICACIONES WHATSAPP
# =============================================================================


@app.post("/webhook/calcom")
async def calcom_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe webhooks de Cal.com para actualizar reservas.
    Eventos: BOOKING.CREATED, BOOKING.CANCELLED, BOOKING.RESCHEDULED
    Ahora envía notificaciones por WhatsApp.
    """
    try:
        body = await request.json()
        logger.info(f"📅 Webhook Cal.com recibido")

        payload = body.get("payload", {})
        trigger_event = body.get("triggerEvent", "")

        # Extraer datos
        uid = payload.get("uid", "")
        attendees = payload.get("attendees", [])

        if not uid or not attendees:
            logger.warning("Webhook Cal.com sin uid o attendees")
            return JSONResponse({
                "status": "ignored",
                "reason": "Missing uid or attendees"
            })

        first_attendee = attendees[0] if attendees else {}
        email_calcom = first_attendee.get("email", "").lower().strip()
        attendee_name = first_attendee.get("name", "")
        start_time = payload.get("startTime", "")
        video_call_data = payload.get("videoCallData", {})
        zoom_url = video_call_data.get("url", "") if isinstance(
            video_call_data, dict) else ""

        if not email_calcom:
            return JSONResponse({
                "status": "ignored",
                "reason": "Missing email"
            })

        # Determinar status para scheduler
        # FIX: RESCHEDULED debe tratarse como "created" para que scheduler lo encuentre
        status = "created"
        if "CANCELLED" in trigger_event:
            status = "cancelled"
        # Si es RESCHEDULED, status sigue siendo "created" (reserva activa)

        # Hora Argentina para timestamp
        try:
            tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz_arg)
            hora_arg = now.strftime("%d/%m/%Y, %H:%M")
        except:
            hora_arg = datetime.utcnow().strftime("%d/%m/%Y, %H:%M")

        # Links de cancelar/modificar
        cancel_link = f"https://cal.com/booking/{uid}?cancel=true"
        reschedule_link = f"https://cal.com/reschedule/{uid}"

        # Actualizar en MongoDB
        booking_data = {
            "booking_uid": uid,
            "booking_status": status,
            "booking_start_time": start_time,
            "booking_cancel_link": cancel_link,
            "booking_reschedule_link": reschedule_link,
            "booking_zoom_url": zoom_url,
            "booking_updated_at": hora_arg,
            "booking_event_type":
            trigger_event  # Para tracking: CREATED/RESCHEDULED/CANCELLED
        }

        result = update_lead_booking(email_calcom, booking_data)

        # Buscar el lead para obtener phone_whatsapp y timezone
        lead = find_lead_by_email_calcom(email_calcom)

        if lead:
            phone_whatsapp = get_lead_field(lead, "phone_whatsapp", "")
            lead_name = get_lead_field(lead, "name", attendee_name)
            lead_tz = get_lead_field(lead, "timezone_detected",
                                     "America/Argentina/Buenos_Aires")
            lead_country = get_lead_field(lead, "country_detected", "tu país")

            # Formatear fecha/hora en timezone del lead
            fecha_str, hora_str = _format_booking_datetime(start_time, lead_tz)

            if phone_whatsapp:
                # Enviar notificación por WhatsApp según el evento
                if "CREATED" in trigger_event:
                    # Resetear recordatorios anteriores si existían
                    reset_reminders_for_lead(phone_whatsapp)

                    background_tasks.add_task(send_booking_confirmation,
                                              phone_whatsapp, lead_name,
                                              fecha_str, hora_str,
                                              lead_country, zoom_url,
                                              cancel_link, reschedule_link)
                    logger.info(
                        f"📱 Confirmación programada para {phone_whatsapp}")

                elif "CANCELLED" in trigger_event:
                    background_tasks.add_task(send_booking_cancellation,
                                              phone_whatsapp, lead_name,
                                              fecha_str, reschedule_link)
                    logger.info(
                        f"📱 Cancelación programada para {phone_whatsapp}")

                elif "RESCHEDULED" in trigger_event:
                    # Resetear recordatorios para la nueva fecha
                    reset_reminders_for_lead(phone_whatsapp)

                    background_tasks.add_task(send_booking_rescheduled,
                                              phone_whatsapp, lead_name,
                                              fecha_str, hora_str,
                                              lead_country, zoom_url)
                    logger.info(
                        f"📱 Reprogramación programada para {phone_whatsapp}")

        if result.get("success"):
            logger.info(f"✅ Booking actualizado: {email_calcom} - {status}")
        else:
            logger.warning(
                f"⚠️ Lead no encontrado para email_calcom: {email_calcom}")

        return JSONResponse({
            "status":
            "processed",
            "booking_uid":
            uid,
            "booking_status":
            status,
            "booking_event":
            trigger_event,
            "whatsapp_notification":
            "scheduled" if lead else "no_phone"
        })

    except Exception as e:
        logger.error(f"Error en webhook Cal.com: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


def _format_booking_datetime(start_time: str, timezone_str: str) -> tuple:
    """
    Formatea la fecha/hora del booking en el timezone del lead.
    Returns: (fecha_str, hora_str)
    """
    try:
        # Parsear ISO datetime
        if start_time.endswith('Z'):
            start_time = start_time[:-1] + '+00:00'

        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        # Convertir a timezone del lead
        try:
            tz = pytz.timezone(timezone_str)
            dt_local = dt.astimezone(tz)
        except:
            dt_local = dt

        fecha_str = dt_local.strftime("%d/%m/%Y")
        hora_str = dt_local.strftime("%H:%M")

        return fecha_str, hora_str

    except Exception as e:
        logger.warning(f"Error formateando fecha: {e}")
        return start_time[:10] if start_time else "fecha", "hora"


# =============================================================================
# ENDPOINTS DE PRUEBA
# =============================================================================


@app.post("/test/message")
async def test_message(request: Request):
    """
    Endpoint de prueba para simular un mensaje de WhatsApp.
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")
        message = body.get("message", "")

        if not phone or not message:
            return JSONResponse({"error": "phone y message son requeridos"},
                                status_code=400)

        # Simular procesamiento
        phone_clean = phone.lstrip('+')
        country_info = detect_country(phone_clean)

        response = await process_message(
            user_message=message,
            phone_whatsapp=phone,
            country_detected=country_info.get("country", ""),
            country_code=country_info.get("code", ""),
            timezone_detected=country_info.get("timezone", ""),
            utc_offset=country_info.get("utc", ""),
            emoji=country_info.get("emoji", ""),
            city_detected=country_info.get("city", ""),
            province_detected=country_info.get("province", ""))

        return JSONResponse({
            "status": "success",
            "phone": phone,
            "message_received": message,
            "response": response,
            "country_detected": country_info
        })

    except Exception as e:
        logger.error(f"Error en test/message: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/test/reminder")
async def test_reminder(request: Request):
    """
    Endpoint de prueba para enviar un recordatorio manualmente.
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")
        reminder_type = body.get(
            "type", "confirmation")  # confirmation, 24hr, 1hr, 15min, at_time

        if not phone:
            return JSONResponse({"error": "phone es requerido"},
                                status_code=400)

        # Datos de prueba
        test_data = {
            "name": "Test User",
            "fecha": "25/12/2025",
            "hora": "15:00",
            "pais": "Argentina",
            "zoom_url": "https://zoom.us/j/test123"
        }

        phone_clean = phone.lstrip('+')

        if reminder_type == "confirmation":
            result = await send_booking_confirmation(phone, test_data["name"],
                                                     test_data["fecha"],
                                                     test_data["hora"],
                                                     test_data["pais"],
                                                     test_data["zoom_url"])
        elif reminder_type == "cancellation":
            result = await send_booking_cancellation(phone, test_data["name"],
                                                     test_data["fecha"])
        else:
            result = await send_whatsapp_message(
                phone_clean, f"Test reminder: {reminder_type}")

        return JSONResponse({
            "status": "sent" if result else "failed",
            "phone": phone,
            "type": reminder_type
        })

    except Exception as e:
        logger.error(f"Error en test/reminder: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scheduler/status")
async def scheduler_status():
    """Verifica el estado del scheduler."""
    try:
        from services.reminders import scheduler

        if scheduler is None:
            return JSONResponse({
                "status": "not_initialized",
                "message": "Scheduler no fue inicializado",
                "jobs": []
            })

        if not scheduler.running:
            return JSONResponse({
                "status": "stopped",
                "message": "Scheduler existe pero no está corriendo",
                "jobs": []
            })

        jobs = []
        for job in scheduler.get_jobs():
            next_run = None
            if job.next_run_time:
                next_run = job.next_run_time.isoformat()
            jobs.append({"id": job.id, "name": job.name, "next_run": next_run})

        return JSONResponse({
            "status": "running",
            "jobs_count": len(jobs),
            "jobs": jobs
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e), "jobs": []})


@app.post("/scheduler/check-now")
async def scheduler_check_now():
    """Fuerza una verificación inmediata de recordatorios."""
    try:
        from services.reminders import check_and_send_reminders

        await check_and_send_reminders()

        return JSONResponse({
            "status": "executed",
            "message": "Check de recordatorios ejecutado"
        })
    except Exception as e:
        logger.error(f"Error en check manual: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        },
                            status_code=500)


@app.post("/test/send-reminder-manual")
async def send_reminder_manual(request: Request):
    """
    Envía recordatorio manual a un lead específico.
    Útil para testing.
    Body: {"phone": "+5493401514509"}
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")

        if not phone:
            return JSONResponse({"error": "phone es requerido"},
                                status_code=400)

        # Limpiar phone
        phone_clean = phone.lstrip('+')

        # Buscar lead en MongoDB
        from services.mongodb import get_database
        db = get_database()

        if db is None:
            return JSONResponse({"error": "No hay conexión a MongoDB"},
                                status_code=500)

        # Buscar por phone_whatsapp (con o sin +)
        lead = db["leads_fortia"].find_one({
            "$or": [{
                "phone_whatsapp": phone
            }, {
                "phone_whatsapp": f"+{phone_clean}"
            }, {
                "phone_whatsapp": phone_clean
            }]
        })

        if not lead:
            return JSONResponse({"error": f"Lead no encontrado: {phone}"},
                                status_code=404)

        # Extraer datos (compatible inglés/español)
        name = get_lead_field(lead, "name", "")
        booking_start = get_lead_field(lead, "booking_start_time", "")
        zoom_url = get_lead_field(lead, "booking_zoom_url", "")
        tz_str = get_lead_field(lead, "timezone_detected",
                                "America/Argentina/Buenos_Aires")
        pais = get_lead_field(lead, "country_detected", "tu país")

        if not booking_start:
            return JSONResponse(
                {
                    "error": "Lead no tiene reunión agendada",
                    "lead_name": name
                },
                status_code=400)

        # Formatear fecha/hora
        try:
            bs = booking_start
            if bs.endswith('Z'):
                bs = bs[:-1] + '+00:00'
            booking_dt = datetime.fromisoformat(bs)
            tz = pytz.timezone(tz_str)
            booking_local = booking_dt.astimezone(tz)
            fecha_str = booking_local.strftime("%d/%m/%Y")
            hora_str = booking_local.strftime("%H:%M")
        except Exception as e:
            fecha_str = "fecha pendiente"
            hora_str = "hora pendiente"
            logger.error(f"Error parseando fecha: {e}")

        # Construir mensaje
        saludo = f"¡Hola {name}! " if name else "¡Hola! "

        msg = f"""{saludo}Te recordamos tu reunión:

📅 Fecha: {fecha_str}
🕐 Hora: {hora_str} (hora de {pais})"""

        if zoom_url:
            msg += f"""

📍 Link de Zoom:
{zoom_url}"""

        msg += """

¡Te esperamos! 🚀"""

        # Enviar WhatsApp
        from services.whatsapp import send_whatsapp_message
        result = await send_whatsapp_message(phone_clean, msg)

        if result:
            logger.info(f"[MANUAL] ✓ Recordatorio enviado a {phone}")
            return JSONResponse({
                "status": "sent",
                "phone": phone,
                "name": name,
                "fecha": fecha_str,
                "hora": hora_str,
                "message_preview": msg[:100] + "..."
            })
        else:
            logger.error(f"[MANUAL] ✗ Error enviando a {phone}")
            return JSONResponse(
                {
                    "status": "failed",
                    "phone": phone,
                    "error": "Error enviando WhatsApp"
                },
                status_code=500)

    except Exception as e:
        logger.error(f"Error en send-reminder-manual: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/test/send-template-24h")
async def test_template_24h(request: Request):
    """
    Prueba envío de plantilla reminder_24h_.
    Body: {"phone": "+5493401514509"}
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")

        if not phone:
            return JSONResponse({"error": "phone es requerido"},
                                status_code=400)

        # Buscar lead
        from services.mongodb import get_database
        db = get_database()

        if db is None:
            return JSONResponse({"error": "No hay conexión a MongoDB"},
                                status_code=500)

        phone_clean = phone.lstrip('+')
        lead = db["leads_fortia"].find_one({
            "$or": [{
                "phone_whatsapp": phone
            }, {
                "phone_whatsapp": f"+{phone_clean}"
            }, {
                "phone_whatsapp": phone_clean
            }]
        })

        if not lead:
            return JSONResponse({"error": f"Lead no encontrado: {phone}"},
                                status_code=404)

        # Extraer datos (compatible inglés/español)
        name = get_lead_field(lead, "name", "usuario")
        booking_start = get_lead_field(lead, "booking_start_time", "")
        tz_str = get_lead_field(lead, "timezone_detected",
                                "America/Argentina/Buenos_Aires")
        link_modificar = (get_lead_field(lead, "booking_reschedule_link", "")
                          or get_lead_field(lead, "booking_cancel_link",
                                            "N/A"))

        # Formatear fecha/hora
        fecha_str = "fecha pendiente"
        hora_str = "hora pendiente"

        if booking_start:
            try:
                bs = booking_start
                if bs.endswith('Z'):
                    bs = bs[:-1] + '+00:00'
                booking_dt = datetime.fromisoformat(bs)
                tz = pytz.timezone(tz_str)
                booking_local = booking_dt.astimezone(tz)
                fecha_str = format_fecha_es(booking_local)
                hora_str = booking_local.strftime("%H:%M")
            except Exception as e:
                logger.error(f"Error parseando fecha: {e}")

        # Enviar plantilla
        from services.whatsapp import send_template_reminder_24h

        result = await send_template_reminder_24h(
            phone=phone,
            nombre=name,
            hora=hora_str,
            fecha=fecha_str,
            link_modificar=link_modificar)

        if result:
            return JSONResponse({
                "status": "sent",
                "template": "reminder_24h_",
                "phone": phone,
                "variables": {
                    "1_nombre": name,
                    "2_hora": hora_str,
                    "3_fecha": fecha_str,
                    "4_link": link_modificar[:50] + "..."
                }
            })
        else:
            return JSONResponse(
                {
                    "status": "failed",
                    "error": "Error enviando plantilla"
                },
                status_code=500)

    except Exception as e:
        logger.error(f"Error en test-template-24h: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/test/extract-web")
async def test_extract_web(request: Request):
    """
    Prueba extracción de datos web sin pasar por el flujo completo.
    Body: {"website": "dpmsa.com.ar"}
    """
    try:
        body = await request.json()
        website = body.get("website", "")

        if not website:
            return JSONResponse({"error": "website es requerido"},
                                status_code=400)

        from services.web_extractor import extract_web_data

        logger.info(f"[TEST] Extrayendo: {website}")

        resultado = await extract_web_data(website)

        # Campos importantes para verificar
        resumen = {
            "website": resultado.get("website"),
            "business_name": resultado.get("business_name"),
            "business_model": resultado.get("business_model"),
            "whatsapp_empresa": resultado.get("whatsapp_empresa"),
            "whatsapp_source": resultado.get("whatsapp_source", "web"),
            "phone_empresa": resultado.get("phone_empresa"),
            "email_principal": resultado.get("email_principal"),
            "linkedin_empresa": resultado.get("linkedin_empresa"),
            "extraction_status": resultado.get("extraction_status")
        }

        return JSONResponse({
            "status": "success",
            "resumen": resumen,
            "datos_completos": resultado
        })

    except Exception as e:
        logger.error(f"[TEST] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT DE PRUEBA - Extracción Web sin WhatsApp
# ═══════════════════════════════════════════════════════════════════════
@app.get("/test-extract-web")
async def test_extract_web(website: str):
    """
    Endpoint de prueba para extraer datos de una web.
    No envía mensajes de WhatsApp.

    Uso: curl "http://localhost:8000/test-extract-web?website=globant.com"
    """
    from services.web_extractor import extract_web_data

    try:
        logger.info(f"[TEST] ══════ Extrayendo: {website} ══════")

        resultado = await extract_web_data(website)

        # Resumen de campos importantes
        resumen = {
            "website": resultado.get("website"),
            "business_name": resultado.get("business_name"),
            "business_activity": resultado.get("business_activity"),
            "business_model": resultado.get("business_model"),
            "business_description": resultado.get("business_description"),
            "services": resultado.get("services"),
            "phone_empresa": resultado.get("phone_empresa"),
            "whatsapp_empresa": resultado.get("whatsapp_empresa"),
            "email_principal": resultado.get("email_principal"),
            "address": resultado.get("address"),
            "city": resultado.get("city"),
            "province": resultado.get("province"),
            "country": resultado.get("country"),
            "linkedin_empresa": resultado.get("linkedin_empresa"),
            "instagram_empresa": resultado.get("instagram_empresa"),
            "facebook_empresa": resultado.get("facebook_empresa"),
            "youtube": resultado.get("youtube"),
            "twitter": resultado.get("twitter"),
            "extraction_status": resultado.get("extraction_status")
        }

        logger.info(f"[TEST] ══════ Extracción completada ══════")

        return JSONResponse({
            "status": "success",
            "resumen": resumen,
            "datos_completos": resultado
        })

    except Exception as e:
        logger.error(f"[TEST] Error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        },
                            status_code=500)


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT DE PRUEBA - Investigación completa (LinkedIn + Noticias)
# ═══════════════════════════════════════════════════════════════════════
@app.get("/test-full-research")
async def test_full_research(nombre: str, website: str, empresa: str = ""):
    """
    Endpoint de prueba para investigación completa.
    Extrae web + LinkedIn personal + Noticias.
    No envía mensajes de WhatsApp.

    Uso: curl "http://localhost:8000/test-full-research?nombre=Martin%20Migoya&website=globant.com&empresa=Globant"
    """
    from services.web_extractor import extract_web_data
    from services.social_research import research_person_and_company

    try:
        logger.info(f"[TEST-FULL] ══════ Iniciando ══════")
        logger.info(f"[TEST-FULL] Nombre: {nombre}")
        logger.info(f"[TEST-FULL] Website: {website}")
        logger.info(f"[TEST-FULL] Empresa: {empresa or website}")

        # Paso 1: Extraer datos web
        logger.info(f"[TEST-FULL] Paso 1: Extrayendo web...")
        datos_web = await extract_web_data(website)

        empresa_nombre = empresa or datos_web.get("business_name") or website

        # Paso 2: Investigar persona (LinkedIn + Noticias)
        logger.info(f"[TEST-FULL] Paso 2: Investigando persona...")
        datos_research = await research_person_and_company(
            nombre_persona=nombre,
            empresa=empresa_nombre,
            website=website,
            linkedin_empresa_input=datos_web.get("linkedin_empresa"),
            facebook_empresa_input=datos_web.get("facebook_empresa"),
            instagram_empresa_input=datos_web.get("instagram_empresa"),
            city=datos_web.get("city", ""),
            province=datos_web.get("province", ""),
            country=datos_web.get("country", ""),
            email_contacto=datos_web.get("email_principal", ""))

        logger.info(f"[TEST-FULL] ══════ Completado ══════")

        return JSONResponse({
            "status": "success",
            "datos_web": {
                "business_name": datos_web.get("business_name"),
                "business_activity": datos_web.get("business_activity"),
                "business_model": datos_web.get("business_model"),
                "business_description": datos_web.get("business_description"),
                "services": datos_web.get("services"),
                "email": datos_web.get("email_principal"),
                "phone": datos_web.get("phone_empresa"),
                "linkedin_empresa": datos_web.get("linkedin_empresa"),
                "city": datos_web.get("city"),
                "province": datos_web.get("province")
            },
            "datos_persona": {
                "nombre":
                datos_research.get("nombre"),
                "linkedin_personal":
                datos_research.get("linkedin_personal"),
                "linkedin_confianza":
                datos_research.get("linkedin_personal_confianza"),
                "linkedin_source":
                datos_research.get("linkedin_personal_source")
            },
            "noticias": {
                "count": datos_research.get("noticias_count"),
                "source": datos_research.get("noticias_source"),
                "lista": datos_research.get("noticias_lista", [])[:5]
            }
        })

    except Exception as e:
        logger.error(f"[TEST-FULL] Error: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "error": str(e)
        },
                            status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
