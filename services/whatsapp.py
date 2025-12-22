"""
Servicio WhatsApp Business API
Envío de mensajes de texto con soporte para mensajes largos
"""
import os
import httpx
import logging
from typing import List

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
MAX_MESSAGE_LENGTH = 1500  # WhatsApp recomienda máximo 4096, pero n8n usa 1500


def split_long_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Divide un mensaje largo en partes.
    Réplica de la lógica Dividir_Texto en n8n.
    """
    if len(message) <= max_length:
        return [message]
    
    parts = []
    current_part = ""
    
    # Intentar dividir por párrafos primero
    paragraphs = message.split("\n\n")
    
    for paragraph in paragraphs:
        # Si el párrafo solo cabe en la parte actual
        if len(current_part) + len(paragraph) + 2 <= max_length:
            if current_part:
                current_part += "\n\n" + paragraph
            else:
                current_part = paragraph
        else:
            # Guardar parte actual si tiene contenido
            if current_part:
                parts.append(current_part.strip())
            
            # Si el párrafo es muy largo, dividir por oraciones
            if len(paragraph) > max_length:
                sentences = paragraph.replace(". ", ".|").split("|")
                current_part = ""
                
                for sentence in sentences:
                    if len(current_part) + len(sentence) + 1 <= max_length:
                        if current_part:
                            current_part += " " + sentence
                        else:
                            current_part = sentence
                    else:
                        if current_part:
                            parts.append(current_part.strip())
                        current_part = sentence
            else:
                current_part = paragraph
    
    # Agregar última parte
    if current_part:
        parts.append(current_part.strip())
    
    # Agregar indicadores de continuación
    if len(parts) > 1:
        for i in range(len(parts)):
            parts[i] = f"({i+1}/{len(parts)})\n\n{parts[i]}"
    
    return parts


async def send_whatsapp_message(to: str, message: str) -> dict:
    """
    Envía un mensaje de texto por WhatsApp.
    Si el mensaje es largo, lo divide en partes.
    
    Args:
        to: Número de teléfono (formato: 5493401514509, sin +)
        message: Texto del mensaje
    
    Returns:
        dict con status de la operación
    """
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        
        if not token or not phone_id:
            logger.error("WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID no configurados")
            return {"success": False, "error": "Credenciales WhatsApp no configuradas"}
        
        # Limpiar número
        to_clean = to.lstrip('+')
        
        # Dividir mensaje si es necesario
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
                    
                    # Pequeña pausa entre partes para mantener orden
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
