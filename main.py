"""
DANIA/Fortia WhatsApp Bot - Main Application
FastAPI con webhooks para WhatsApp y Cal.com
"""
import os
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse

from config import detect_country, WHATSAPP_VERIFY_TOKEN
from services.whatsapp import send_whatsapp_message, mark_as_read
from services.openai_agent import process_message
from services.mongodb import update_lead_booking, get_database

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    
    yield
    
    # Shutdown
    logger.info("👋 Cerrando aplicación...")


app = FastAPI(
    title="DANIA/Fortia WhatsApp Bot",
    description="Bot de WhatsApp para captación y cualificación de leads con IA",
    version="1.0.0",
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
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    """Health check detallado."""
    db = get_database()
    return {
        "status": "healthy",
        "mongodb": "connected" if db is not None else "disconnected",
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
        # logger.debug(f"Webhook recibido: {json.dumps(body, indent=2)}")  # Comentado: solo para debugging
        
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
        
        # Procesar en background
        background_tasks.add_task(
            process_whatsapp_message,
            from_number,
            text,
            message_id,
            message_type,
            audio_id
        )
        
        # Responder rápido a Meta
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Error en webhook WhatsApp: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


async def process_whatsapp_message(from_number: str, text: str, message_id: str, message_type: str = "text", audio_id: str = ""):
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
            emoji=country_info.get("emoji", "")
        )
        
        if response is not None and response:
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
# CAL.COM WEBHOOK
# =============================================================================

@app.post("/webhook/calcom")
async def calcom_webhook(request: Request):
    """
    Recibe webhooks de Cal.com para actualizar reservas.
    Eventos: BOOKING.CREATED, BOOKING.CANCELLED, BOOKING.RESCHEDULED
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
        
        # Hora Argentina
        now = datetime.utcnow()
        hora_arg = now.strftime("%d/%m/%Y, %H:%M")
        
        # Actualizar en MongoDB
        booking_data = {
            "booking_uid": uid,
            "booking_status": status,
            "booking_start_time": start_time,
            "booking_cancel_link": f"https://cal.com/booking/{uid}?cancel=true",
            "booking_reschedule_link": f"https://cal.com/reschedule/{uid}",
            "booking_zoom_url": zoom_url,
            "booking_updated_at": hora_arg
        }
        
        result = update_lead_booking(email_calcom, booking_data)
        
        if result.get("success"):
            logger.info(f"✅ Booking actualizado: {email_calcom} - {status}")
        else:
            logger.warning(f"⚠️ Lead no encontrado para email_calcom: {email_calcom}")
        
        return JSONResponse({
            "status": "processed",
            "booking_uid": uid,
            "booking_status": status
        })
    
    except Exception as e:
        logger.error(f"Error en webhook Cal.com: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


# =============================================================================
# ENDPOINTS DE PRUEBA
# =============================================================================

@app.post("/test/message")
async def test_message(request: Request):
    """
    Endpoint de prueba para simular un mensaje de WhatsApp.
    Body: {"phone": "+5493401514509", "message": "Hola"}
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")
        message = body.get("message", "")
        
        if not phone or not message:
            raise HTTPException(status_code=400, detail="Faltan phone o message")
        
        # Limpiar phone
        phone_clean = phone.lstrip("+")
        phone_whatsapp = f"+{phone_clean}"
        
        # Detectar país
        country_info = detect_country(phone_clean)
        
        # Procesar con el agente
        response = await process_message(
            user_message=message,
            phone_whatsapp=phone_whatsapp,
            country_detected=country_info.get("country", ""),
            country_code=country_info.get("code", ""),
            timezone_detected=country_info.get("timezone", ""),
            utc_offset=country_info.get("utc", ""),
            emoji=country_info.get("emoji", "")
        )
        
        return {
            "input": {
                "phone": phone_whatsapp,
                "message": message,
                "country": country_info
            },
            "response": response
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/summary")
async def test_summary(request: Request):
    """
    Endpoint de prueba para generar resumen de conversación.
    Body: {"phone": "+5493401514509"}
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")
        
        if not phone:
            raise HTTPException(status_code=400, detail="Falta phone")
        
        from services.mongodb import get_chat_history
        
        history = get_chat_history(phone, limit=50)
        
        if not history:
            return {"error": "No hay historial para este número", "phone": phone}
        
        # Construir texto
        conversation_text = ""
        for msg in history:
            role = "Usuario" if msg.get("role") == "user" else "Asistente"
            conversation_text += f"{role}: {msg.get('content', '')[:200]}...\n\n"
        
        return {
            "phone": phone,
            "message_count": len(history),
            "preview": conversation_text[:2000]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en test summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
