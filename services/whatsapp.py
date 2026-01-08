"""
Servicio WhatsApp Business API para DANIA/Fortia
Incluye: envío de mensajes, descarga de media, transcripción de audio
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
MAX_MESSAGE_LENGTH = 4000


def split_long_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> list:
    """Divide mensajes largos en partes."""
    if len(message) <= max_length:
        return [message]
    
    parts = []
    current = ""
    
    for paragraph in message.split("\n\n"):
        if len(current) + len(paragraph) + 2 <= max_length:
            current = current + "\n\n" + paragraph if current else paragraph
        else:
            if current:
                parts.append(current.strip())
            if len(paragraph) > max_length:
                words = paragraph.split()
                current = ""
                for word in words:
                    if len(current) + len(word) + 1 <= max_length:
                        current = current + " " + word if current else word
                    else:
                        parts.append(current.strip())
                        current = word
            else:
                current = paragraph
    
    if current:
        parts.append(current.strip())
    
    return parts if parts else [message[:max_length]]


async def send_whatsapp_message(to: str, message: str) -> dict:
    """
    Envía un mensaje de texto por WhatsApp.
    Si el mensaje es largo, lo divide en partes.
    """
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        
        if not token or not phone_id:
            logger.error("WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID no configurados")
            return {"success": False, "error": "Credenciales WhatsApp no configuradas"}
        
        to_clean = to.lstrip('+')
        message_parts = split_long_message(message)
        
        url = f"{WHATSAPP_API_URL}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        sent_ids = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, part in enumerate(message_parts):
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to_clean,
                    "type": "text",
                    "text": {
                        "preview_url": True,
                        "body": part
                    }
                }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    if messages:
                        sent_ids.append(messages[0].get("id", ""))
                    
                    if i < len(message_parts) - 1:
                        import asyncio
                        await asyncio.sleep(0.5)
                else:
                    logger.error(f"Error WhatsApp API: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Error API: {response.status_code}",
                        "details": response.text
                    }
        
        logger.info(f"✓ Mensaje enviado a {to_clean} ({len(message_parts)} parte(s))")
        return {
            "success": True,
            "message_ids": sent_ids,
            "to": to_clean,
            "parts_sent": len(message_parts)
        }
    
    except httpx.TimeoutException:
        logger.error("Timeout enviando mensaje WhatsApp")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        logger.error(f"Error enviando WhatsApp: {e}")
        return {"success": False, "error": str(e)}


async def mark_as_read(message_id: str) -> bool:
    """Marca un mensaje como leído."""
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        
        if not token or not phone_id:
            return False
        
        url = f"{WHATSAPP_API_URL}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code == 200
    
    except Exception as e:
        logger.error(f"Error marcando como leído: {e}")
        return False


async def get_media_url(media_id: str) -> str:
    """
    Obtiene la URL de descarga de un media de WhatsApp.
    Paso 1 del flujo de audio.
    """
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        
        if not token:
            logger.error("WHATSAPP_TOKEN no configurado")
            return ""
        
        url = f"{WHATSAPP_API_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                media_url = data.get("url", "")
                logger.info(f"[AUDIO] ✓ URL obtenida para media {media_id}")
                return media_url
            else:
                logger.error(f"[AUDIO] Error obteniendo URL: {response.status_code}")
                return ""
    
    except Exception as e:
        logger.error(f"[AUDIO] Error get_media_url: {e}")
        return ""


async def download_media(media_url: str) -> bytes:
    """
    Descarga el contenido del media desde la URL de WhatsApp.
    Paso 2 del flujo de audio.
    """
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        
        if not token or not media_url:
            return b""
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(media_url, headers=headers)
            
            if response.status_code == 200:
                content = response.content
                logger.info(f"[AUDIO] ✓ Descargado: {len(content)} bytes")
                return content
            else:
                logger.error(f"[AUDIO] Error descargando: {response.status_code}")
                return b""
    
    except Exception as e:
        logger.error(f"[AUDIO] Error download_media: {e}")
        return b""


async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio usando OpenAI Whisper.
    Paso 3 del flujo de audio.
    """
    try:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        
        if not openai_key or not audio_bytes:
            return ""
        
        logger.info(f"[AUDIO] Transcribiendo {len(audio_bytes)} bytes...")
        
        import io
        
        # Crear archivo en memoria
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.ogg"  # WhatsApp envía OGG
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {openai_key}"},
                files={"file": ("audio.ogg", audio_bytes, "audio/ogg")},
                data={"model": "whisper-1", "language": "es"}
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("text", "")
                logger.info(f"[AUDIO] ✓ Transcrito: {text[:50]}...")
                return text
            else:
                logger.error(f"[AUDIO] Error Whisper: {response.status_code} - {response.text}")
                return ""
    
    except Exception as e:
        logger.error(f"[AUDIO] Error transcribe_audio: {e}")
        return ""


async def send_typing_indicator(phone: str, typing_on: bool = True) -> bool:
    """
    Envía indicador de 'escribiendo...' a WhatsApp
    
    Args:
        phone: Número en formato E.164
        typing_on: True para activar, False para desactivar
    """
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        
        if not token or not phone_id:
            logger.error("WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID no configurados")
            return False
        
        phone_clean = phone.lstrip('+')
        
        # Usar v21.0 para typing indicator (según especificación)
        url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_clean,
            "type": "typing",
            "typing": {
                "action": "typing_on" if typing_on else "typing_off"
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Typing indicator {'ON' if typing_on else 'OFF'} sent to {phone_clean}")
                return True
            else:
                logger.warning(f"Typing indicator failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")
        return False


async def send_template_reminder_24h(
    phone: str,
    nombre: str,
    hora: str,
    fecha: str,
    link_modificar: str
) -> bool:
    """
    Envía recordatorio de 24hs usando plantilla aprobada.
    Plantilla: reminder_24h_
    Variables: {{1}}=nombre, {{2}}=hora, {{3}}=fecha, {{4}}=link
    """
    token = os.environ.get("WHATSAPP_TOKEN", "")
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    
    if not token or not phone_id:
        logger.error("WhatsApp no configurado")
        return False
    
    phone_clean = phone.lstrip('+')
    
    url = f"{WHATSAPP_API_URL}/{phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_clean,
        "type": "template",
        "template": {
            "name": "reminder_24h_",
            "language": {
                "code": "es_AR"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": nombre},
                        {"type": "text", "text": hora},
                        {"type": "text", "text": fecha},
                        {"type": "text", "text": link_modificar}
                    ]
                }
            ]
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(
                    f"[TEMPLATE] ✓ reminder_24h_ enviado a {phone}"
                )
                return True
            else:
                logger.error(
                    f"[TEMPLATE] ✗ Error {response.status_code}: "
                    f"{response.text}"
                )
                return False
    except Exception as e:
        logger.error(f"[TEMPLATE] Error enviando plantilla: {e}")
        return False
