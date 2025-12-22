"""
Servicio de MongoDB para DANIA/Fortia
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import MONGODB_URI, MONGODB_DATABASE, CALCOM_EVENT_URL

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db = None


def get_database():
    """Obtiene conexión a la base de datos MongoDB."""
    global _client, _db
    
    if _db is not None:
        return _db
    
    try:
        if not MONGODB_URI:
            logger.error("MONGODB_URI no configurada")
            return None
            
        _client = MongoClient(MONGODB_URI)
        _db = _client[MONGODB_DATABASE]
        # Test connection
        _client.admin.command('ping')
        logger.info(f"Conectado a MongoDB: {MONGODB_DATABASE}")
        return _db
    except PyMongoError as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        return None


def save_lead(lead_data: dict) -> dict:
    """
    Guarda o actualiza un lead en MongoDB.
    Usa phone_whatsapp como identificador único.
    Limpia valores None/undefined -> "No encontrado"
    """
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        phone = lead_data.get("phone_whatsapp", "")
        if not phone:
            return {"success": False, "error": "phone_whatsapp es requerido"}
        
        # Limpiar valores None/undefined
        cleaned_data = {}
        for key, value in lead_data.items():
            if value is None or value == "" or value == "undefined" or value == "null":
                cleaned_data[key] = "No encontrado"
            else:
                cleaned_data[key] = value
        
        # Timestamps
        now = datetime.now(timezone.utc)
        cleaned_data["updated_at"] = now
        
        # Verificar si existe
        existing = collection.find_one({"phone_whatsapp": phone})
        
        if existing:
            # Update
            collection.update_one(
                {"phone_whatsapp": phone},
                {"$set": cleaned_data}
            )
            logger.info(f"Lead actualizado: {phone}")
            return {"success": True, "operation": "updated", "phone": phone, "message": "Lead actualizado correctamente"}
        else:
            # Insert
            cleaned_data["created_at"] = now
            collection.insert_one(cleaned_data)
            logger.info(f"Lead creado: {phone}")
            return {"success": True, "operation": "created", "phone": phone, "message": "Lead creado correctamente"}
            
    except PyMongoError as e:
        logger.error(f"Error guardando lead: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado guardando lead: {e}")
        return {"success": False, "error": str(e)}


def find_lead_by_phone(phone_whatsapp: str) -> Optional[dict]:
    """Busca un lead por número de WhatsApp."""
    try:
        db = get_database()
        if db is None:
            return None
            
        collection = db["leads_fortia"]
        lead = collection.find_one({"phone_whatsapp": phone_whatsapp})
        if lead:
            lead["_id"] = str(lead.get("_id", ""))
        return lead
    except PyMongoError as e:
        logger.error(f"Error buscando lead: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado buscando lead: {e}")
        return None


def find_lead_by_email_calcom(email_calcom: str) -> Optional[dict]:
    """Busca un lead por email de Cal.com."""
    try:
        db = get_database()
        if db is None:
            return None
            
        collection = db["leads_fortia"]
        lead = collection.find_one({"email_calcom": email_calcom})
        if lead:
            lead["_id"] = str(lead.get("_id", ""))
        return lead
    except PyMongoError as e:
        logger.error(f"Error buscando lead por email: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado buscando lead por email: {e}")
        return None


def update_lead_calcom_email(phone_whatsapp: str, email_calcom: str, name: str = "") -> dict:
    """
    Guarda el email de Cal.com y genera link pre-llenado.
    """
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        # Generar link pre-llenado
        base_url = CALCOM_EVENT_URL if CALCOM_EVENT_URL else "https://cal.com/agencia-fortia-hviska/60min"
        name_param = name.replace(" ", "%20") if name else ""
        email_param = email_calcom.replace("@", "%40") if email_calcom else ""
        calcom_link = f"{base_url}?email={email_param}&name={name_param}"
        
        update_data = {
            "email_calcom": email_calcom,
            "calcom_link": calcom_link,
            "updated_at": datetime.now(timezone.utc)
        }
        
        result = collection.update_one(
            {"phone_whatsapp": phone_whatsapp},
            {"$set": update_data}
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            logger.info(f"Email Cal.com guardado para: {phone_whatsapp}")
            return {
                "success": True,
                "calcom_link": calcom_link,
                "message": "Email guardado correctamente"
            }
        else:
            # Si no existe el lead, crear uno básico
            collection.insert_one({
                "phone_whatsapp": phone_whatsapp,
                "email_calcom": email_calcom,
                "calcom_link": calcom_link,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            return {
                "success": True,
                "calcom_link": calcom_link,
                "message": "Lead creado con email Cal.com"
            }
            
    except PyMongoError as e:
        logger.error(f"Error actualizando email Cal.com: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return {"success": False, "error": str(e)}


def update_lead_booking(email_calcom: str, booking_data: dict) -> dict:
    """
    Actualiza datos de reserva desde webhook de Cal.com.
    """
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        update_data = {
            "booking_uid": booking_data.get("uid", ""),
            "booking_status": booking_data.get("status", ""),
            "booking_start_time": booking_data.get("start_time", ""),
            "booking_cancel_link": booking_data.get("cancel_link", ""),
            "booking_reschedule_link": booking_data.get("reschedule_link", ""),
            "booking_zoom_url": booking_data.get("zoom_url", ""),
            "booking_updated_at": datetime.now(timezone.utc)
        }
        
        result = collection.update_one(
            {"email_calcom": email_calcom},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Booking actualizado para: {email_calcom}")
            return {"success": True, "message": "Booking actualizado"}
        else:
            logger.warning(f"No se encontró lead con email: {email_calcom}")
            return {"success": False, "error": "Lead no encontrado"}
            
    except PyMongoError as e:
        logger.error(f"Error actualizando booking: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return {"success": False, "error": str(e)}


def save_chat_message(session_id: str, msg_type: str, text: str) -> bool:
    """
    Guarda un mensaje en el historial de chat.
    
    Args:
        session_id: phone_whatsapp del usuario
        msg_type: "human" o "ai"
        text: contenido del mensaje
    """
    try:
        db = get_database()
        if db is None:
            return False
            
        collection = db["chat_history"]
        
        message = {
            "sessionId": session_id,
            "type": msg_type,
            "text": text,
            "timestamp": datetime.now(timezone.utc)
        }
        
        collection.insert_one(message)
        return True
        
    except PyMongoError as e:
        logger.error(f"Error guardando mensaje: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado guardando mensaje: {e}")
        return False


def get_chat_history(session_id: str, limit: int = 20) -> list:
    """
    Obtiene historial de chat para un usuario.
    Retorna en formato para OpenAI.
    """
    try:
        db = get_database()
        if db is None:
            return []
            
        collection = db["chat_history"]
        
        cursor = collection.find(
            {"sessionId": session_id}
        ).sort("timestamp", -1).limit(limit)
        
        messages = list(cursor)
        
        # Convertir a formato OpenAI y revertir orden
        history = []
        for msg in messages:
            msg_type = msg.get("type", "")
            msg_text = msg.get("text", "")
            
            if not msg_text:
                continue
                
            role = "user" if msg_type == "human" else "assistant"
            history.append({
                "role": role,
                "content": msg_text
            })
        
        history.reverse()
        return history
        
    except PyMongoError as e:
        logger.error(f"Error obteniendo historial: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado obteniendo historial: {e}")
        return []


def get_or_create_conversation(phone_whatsapp: str, timeout_hours: int = 24) -> str:
    """
    Obtiene la conversación activa o crea una nueva.
    Si pasaron más de timeout_hours desde el último mensaje, crea nueva conversación.
    Retorna conversation_id.
    """
    try:
        db = get_database()
        if db is None:
            return f"conv_{phone_whatsapp}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            
        collection = db["conversations"]
        
        # Buscar conversación activa
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
        
        active_conv = collection.find_one({
            "phone_whatsapp": phone_whatsapp,
            "last_message_at": {"$gte": cutoff_time},
            "status": "active"
        })
        
        if active_conv:
            # Actualizar timestamp
            collection.update_one(
                {"_id": active_conv["_id"]},
                {"$set": {"last_message_at": datetime.now(timezone.utc)}}
            )
            return str(active_conv.get("conversation_id", active_conv["_id"]))
        
        # Crear nueva conversación
        conv_id = f"conv_{phone_whatsapp}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        new_conv = {
            "conversation_id": conv_id,
            "phone_whatsapp": phone_whatsapp,
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "last_message_at": datetime.now(timezone.utc)
        }
        collection.insert_one(new_conv)
        logger.info(f"Nueva conversación creada: {conv_id}")
        return conv_id
        
    except Exception as e:
        logger.error(f"Error en get_or_create_conversation: {e}")
        return f"conv_{phone_whatsapp}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def save_chat_message_v2(phone_whatsapp: str, msg_type: str, text: str, conversation_id: str = None) -> bool:
    """
    Guarda un mensaje en el historial de chat con conversation_id.
    """
    try:
        db = get_database()
        if db is None:
            return False
            
        # Obtener o crear conversación si no se proporcionó
        if not conversation_id:
            conversation_id = get_or_create_conversation(phone_whatsapp)
            
        collection = db["chat_history"]
        
        message = {
            "sessionId": phone_whatsapp,
            "conversation_id": conversation_id,
            "type": msg_type,
            "text": text,
            "timestamp": datetime.now(timezone.utc)
        }
        
        collection.insert_one(message)
        return True
        
    except Exception as e:
        logger.error(f"Error guardando mensaje v2: {e}")
        return False


def get_chat_history_by_conversation(phone_whatsapp: str, conversation_id: str = None, limit: int = 50) -> list:
    """
    Obtiene historial de chat de una conversación específica.
    Si no se especifica conversation_id, obtiene la conversación activa.
    """
    try:
        db = get_database()
        if db is None:
            return []
            
        # Si no hay conversation_id, obtener la activa
        if not conversation_id:
            conversation_id = get_or_create_conversation(phone_whatsapp)
            
        collection = db["chat_history"]
        
        cursor = collection.find({
            "sessionId": phone_whatsapp,
            "conversation_id": conversation_id
        }).sort("timestamp", 1).limit(limit)
        
        messages = list(cursor)
        
        history = []
        for msg in messages:
            msg_type = msg.get("type", "")
            msg_text = msg.get("text", "")
            
            if not msg_text:
                continue
                
            role = "user" if msg_type == "human" else "assistant"
            history.append({
                "role": role,
                "content": msg_text
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error obteniendo historial por conversación: {e}")
        return []


def list_conversations(phone_whatsapp: str, limit: int = 10) -> list:
    """
    Lista las conversaciones de un usuario, ordenadas por fecha.
    """
    try:
        db = get_database()
        if db is None:
            return []
            
        collection = db["conversations"]
        
        cursor = collection.find({
            "phone_whatsapp": phone_whatsapp
        }).sort("created_at", -1).limit(limit)
        
        conversations = []
        for conv in cursor:
            conversations.append({
                "conversation_id": conv.get("conversation_id", ""),
                "created_at": conv.get("created_at", ""),
                "last_message_at": conv.get("last_message_at", ""),
                "status": conv.get("status", "")
            })
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error listando conversaciones: {e}")
        return []
