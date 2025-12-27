"""
DANIA/Fortia WhatsApp Bot - Main Application
FastAPI con webhooks para WhatsApp y Cal.com
Incluye scheduler para recordatorios automáticos
"""
import os
import sys
import json
import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from collections import OrderedDict

import pytz
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse

from config import detect_country, WHATSAPP_VERIFY_TOKEN
from services.whatsapp import send_whatsapp_message, mark_as_read
from services.openai_agent import process_message
from services.mongodb import update_lead_booking, get_database, find_lead_by_email_calcom
from services.reminders import (
    init_scheduler, 
    shutdown_scheduler,
    send_booking_confirmation,
    send_booking_cancellation,
    send_booking_rescheduled,
    reset_reminders_for_lead
)

# Configurar buffering para logs inmediatos
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configurar logging con flush inmediato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

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
    required_vars = ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "OPENAI_API_KEY"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.warning(f"⚠️ Variables faltantes: {missing}")
    else:
        logger.info("✅ Variables de entorno configuradas")
    
    # Iniciar scheduler de recordatorios
    try:
        init_scheduler()
        logger.info("✅ Scheduler de recordatorios iniciado")
    except Exception as e:
        logger.error(f"⚠️ Error iniciando scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 Cerrando aplicación...")
    try:
        shutdown_scheduler()
    except:
        pass


app = FastAPI(
    title="DANIA/Fortia WhatsApp Bot",
    description="Bot de WhatsApp para captación y cualificación de leads con IA",
    version="2.0.0",
    lifespan=lifespan
)


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
    
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", WHATSAPP_VERIFY_TOKEN)
    
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
            logger.debug(f"⏭️ Webhook duplicado ignorado: {message_id[:20]}...")
            return JSONResponse({"status": "ok"})
        
        from_number = message.get("from", "")
        message_type = message.get("type", "")
        
        # Obtener texto del mensaje
        if message_type == "text":
            text_obj = message.get("text", {})
            text = text_obj.get("body", "") if isinstance(text_obj, dict) else ""
            audio_id = ""
        elif message_type == "audio":
            audio_obj = message.get("audio", {})
            audio_id = audio_obj.get("id", "") if isinstance(audio_obj, dict) else ""
            text = ""  # Se obtendrá por transcripción
        else:
            text = f"[Mensaje tipo {message_type} recibido]"
            audio_id = ""
        
        if (not text and not audio_id) or not from_number:
            return JSONResponse({"status": "ok"})
        
        logger.info(f"📩 Mensaje de {from_number}: {text[:50] if text else '[AUDIO]'}...")
        
        original_message_type = message_type
        
        # Procesar en background
        background_tasks.add_task(
            process_whatsapp_message,
            from_number,
            text,
            message_id,
            message_type,
            audio_id,
            original_message_type
        )
        
        # Responder rápido a Meta
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error en webhook WhatsApp: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


async def process_whatsapp_message(from_number: str, text: str, message_id: str, message_type: str = "text", audio_id: str = "", original_message_type: str = "text"):
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
                await send_whatsapp_message(from_number, "No pude procesar el audio. ¿Podés escribirme el mensaje?")
                return
            
            # Paso 2: Descargar
            audio_bytes = await download_media(media_url)
            if not audio_bytes:
                await send_whatsapp_message(from_number, "No pude descargar el audio. ¿Podés intentar de nuevo?")
                return
            
            # Paso 3: Transcribir
            text = await transcribe_audio(audio_bytes)
            if not text:
                await send_whatsapp_message(from_number, "No pude transcribir el audio. ¿Podés escribirme el mensaje?")
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
            original_message_type=original_message_type
        )
        
        if response is not None and response and original_message_type == "text":
            result = await send_whatsapp_message(from_number, response)
            
            if result.get("success"):
                logger.info(f"✅ Respuesta enviada a {from_number}")
            else:
                logger.error(f"❌ Error enviando respuesta: {result.get('error')}")
    
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
            return JSONResponse({"status": "ignored", "reason": "Missing uid or attendees"})
        
        first_attendee = attendees[0] if attendees else {}
        email_calcom = first_attendee.get("email", "").lower().strip()
        attendee_name = first_attendee.get("name", "")
        start_time = payload.get("startTime", "")
        video_call_data = payload.get("videoCallData", {})
        zoom_url = video_call_data.get("url", "") if isinstance(video_call_data, dict) else ""
        
        if not email_calcom:
            return JSONResponse({"status": "ignored", "reason": "Missing email"})
        
        # Determinar status
        status = "created"
        if "CANCELLED" in trigger_event:
            status = "cancelled"
        elif "RESCHEDULED" in trigger_event:
            status = "rescheduled"
        
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
            "booking_updated_at": hora_arg
        }
        
        result = update_lead_booking(email_calcom, booking_data)
        
        # Buscar el lead para obtener phone_whatsapp y timezone
        lead = find_lead_by_email_calcom(email_calcom)
        
        if lead:
            phone_whatsapp = lead.get("phone_whatsapp", "")
            lead_name = lead.get("name", attendee_name)
            lead_tz = lead.get("timezone_detected", "America/Argentina/Buenos_Aires")
            lead_country = lead.get("country_detected", "tu país")
            
            # Formatear fecha/hora en timezone del lead
            fecha_str, hora_str = _format_booking_datetime(start_time, lead_tz)
            
            if phone_whatsapp:
                # Enviar notificación por WhatsApp según el evento
                if status == "created":
                    # Resetear recordatorios anteriores si existían
                    reset_reminders_for_lead(phone_whatsapp)
                    
                    background_tasks.add_task(
                        send_booking_confirmation,
                        phone_whatsapp,
                        lead_name,
                        fecha_str,
                        hora_str,
                        lead_country,
                        zoom_url,
                        cancel_link,
                        reschedule_link
                    )
                    logger.info(f"📱 Confirmación programada para {phone_whatsapp}")
                
                elif status == "cancelled":
                    background_tasks.add_task(
                        send_booking_cancellation,
                        phone_whatsapp,
                        lead_name,
                        fecha_str,
                        reschedule_link
                    )
                    logger.info(f"📱 Cancelación programada para {phone_whatsapp}")
                
                elif status == "rescheduled":
                    # Resetear recordatorios para la nueva fecha
                    reset_reminders_for_lead(phone_whatsapp)
                    
                    background_tasks.add_task(
                        send_booking_rescheduled,
                        phone_whatsapp,
                        lead_name,
                        fecha_str,
                        hora_str,
                        lead_country,
                        zoom_url
                    )
                    logger.info(f"📱 Reprogramación programada para {phone_whatsapp}")
        
        if result.get("success"):
            logger.info(f"✅ Booking actualizado: {email_calcom} - {status}")
        else:
            logger.warning(f"⚠️ Lead no encontrado para email_calcom: {email_calcom}")
        
        return JSONResponse({
            "status": "processed",
            "booking_uid": uid,
            "booking_status": status,
            "whatsapp_notification": "scheduled" if lead else "no_phone"
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
            return JSONResponse({"error": "phone y message son requeridos"}, status_code=400)
        
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
            province_detected=country_info.get("province", "")
        )
        
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
        reminder_type = body.get("type", "confirmation")  # confirmation, 24hr, 1hr, 15min, at_time
        
        if not phone:
            return JSONResponse({"error": "phone es requerido"}, status_code=400)
        
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
            result = await send_booking_confirmation(
                phone, test_data["name"], test_data["fecha"], 
                test_data["hora"], test_data["pais"], test_data["zoom_url"]
            )
        elif reminder_type == "cancellation":
            result = await send_booking_cancellation(
                phone, test_data["name"], test_data["fecha"]
            )
        else:
            result = await send_whatsapp_message(phone_clean, f"Test reminder: {reminder_type}")
        
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
    from services.reminders import scheduler
    
    if scheduler and scheduler.running:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            })
        
        return JSONResponse({
            "status": "running",
            "jobs": jobs
        })
    else:
        return JSONResponse({
            "status": "stopped",
            "jobs": []
        })
