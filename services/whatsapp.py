"""
Servicio WhatsApp Business API
Envío de mensajes de texto
"""
import os
import httpx
import logging

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


async def send_whatsapp_message(to: str, message: str) -> dict:
    """
    Envía un mensaje de texto por WhatsApp.
    
    Args:
        to: Número de teléfono (formato: 5493401514509, sin +)
        message: Texto del mensaje
    
    Returns:
        dict con status de la operación
    """
    try:
        token = os.environ.get("WHATSAPP_TOKEN", "")
        phone_id = os.environ.get("WHATSAPP_PHONE_ID", "")
        
        if not token or not phone_id:
            logger.error("WHATSAPP_TOKEN o WHATSAPP_PHONE_ID no configurados")
            return {"success": False, "error": "Credenciales WhatsApp no configuradas"}
        
        # Limpiar número
        to_clean = to.lstrip('+')
        
        url = f"{WHATSAPP_API_URL}/{phone_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Mensaje enviado a {to_clean}")
                messages = data.get("messages", [])
                message_id = messages[0].get("id", "") if messages else ""
                return {
                    "success": True,
                    "message_id": message_id,
                    "to": to_clean
                }
            else:
                logger.error(f"Error WhatsApp API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Error API: {response.status_code}",
                    "details": response.text
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
        phone_id = os.environ.get("WHATSAPP_PHONE_ID", "")
        
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
