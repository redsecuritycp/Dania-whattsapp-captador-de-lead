"""
Servicio de Text-to-Speech (TTS) con OpenAI
Si entra audio → sale audio (como n8n)
"""
import logging
import httpx
import os
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
TTS_VOICE = "nova"
TTS_MODEL = "tts-1"


async def generate_audio_openai(text: str) -> Optional[bytes]:
    if not OPENAI_API_KEY or not text:
        return None
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": TTS_MODEL, "input": text, "voice": TTS_VOICE, "response_format": "mp3"}
            )
            if response.status_code == 200:
                logger.info(f"[TTS] ✓ Audio generado: {len(response.content)} bytes")
                return response.content
        return None
    except Exception as e:
        logger.error(f"[TTS] Error: {e}")
        return None


async def upload_audio_whatsapp(audio_bytes: bytes) -> Optional[str]:
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID or not audio_bytes:
        return None
    try:
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/media"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
                files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
                data={"messaging_product": "whatsapp", "type": "audio/mpeg"}
            )
            if response.status_code == 200:
                media_id = response.json().get("id")
                logger.info(f"[TTS] ✓ Audio subido: {media_id}")
                return media_id
        return None
    except Exception as e:
        logger.error(f"[TTS] Error upload: {e}")
        return None


async def send_audio_whatsapp(phone: str, media_id: str) -> bool:
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        return False
    phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")
    try:
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "recipient_type": "individual", "to": phone_clean, "type": "audio", "audio": {"id": media_id}}
            )
            if response.status_code == 200:
                logger.info(f"[TTS] ✓ Audio enviado a {phone_clean}")
                return True
        return False
    except Exception as e:
        logger.error(f"[TTS] Error send: {e}")
        return False


async def text_to_audio_response(text: str, phone: str) -> bool:
    audio_bytes = await generate_audio_openai(text)
    if not audio_bytes:
        return False
    media_id = await upload_audio_whatsapp(audio_bytes)
    if not media_id:
        return False
    return await send_audio_whatsapp(phone, media_id)






