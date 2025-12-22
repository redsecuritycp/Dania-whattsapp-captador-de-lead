"""
Servicio de MongoDB para DANIA/Fortia
Réplica fiel del workflow n8n: Tool__MongoDB_Manager
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pytz

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
        logger.info(f"✓ Conectado a MongoDB: {MONGODB_DATABASE}")
        return _db
    except PyMongoError as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        return None


def get_local_datetime(timezone_str: str) -> str:
    """
    Genera created_at_local en el timezone del cliente.
    Réplica de la lógica en Preparar_Datos de n8n.
    """
    try:
        if not timezone_str or timezone_str == 'No detectado':
            return 'No disponible'
        
        tz = pytz.timezone(timezone_str)
        ahora = datetime.now(tz)
        
        # Formato: DD/MM/YYYY, HH:MM:SS (timezone)
        fecha_local = ahora.strftime('%d/%m/%Y, %H:%M:%S')
        return f"{fecha_local} ({timezone_str})"
    except Exception as e:
        logger.warning(f"Error generando fecha local: {e}")
        return 'No disponible'


def save_lead(lead_data: dict) -> dict:
    """
    Guarda o actualiza un lead en MongoDB.
    Usa phone_whatsapp como identificador único.
    Réplica de la lógica en Tool__MongoDB_Manager de n8n.
    """
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        phone = lead_data.get("phone_whatsapp", "")
        if not phone:
            return {"success": False, "error": "phone_whatsapp es requerido"}
        
        # ═══════════════════════════════════════════════════════════════════
        # Limpiar valores undefined/None → "No proporcionado" (como n8n)
        # ═══════════════════════════════════════════════════════════════════
        cleaned_data = {}
        for key, value in lead_data.items():
            if value is None or value == "" or value == "undefined" or value == "null":
                cleaned_data[key] = "No proporcionado"
            else:
                cleaned_data[key] = value
        
        # ═══════════════════════════════════════════════════════════════════
        # Timestamps
        # ═══════════════════════════════════════════════════════════════════
        now = datetime.now(timezone.utc)
        cleaned_data["updated_at"] = now.isoformat()
        
        # Verificar si existe para saber si es create o update
        existing = collection.find_one({"phone_whatsapp": phone})
        
        if not existing:
            cleaned_data["created_at"] = now.isoformat()
        
        # ═══════════════════════════════════════════════════════════════════
        # created_at_local - Hora local del cliente (NUEVO - como n8n)
        # ═══════════════════════════════════════════════════════════════════
        timezone_detected = cleaned_data.get("timezone_detected", "")
        if timezone_detected and timezone_detected not in ["No detectado", "No proporcionado"]:
            cleaned_data["created_at_local"] = get_local_datetime(timezone_detected)
        else:
            cleaned_data["created_at_local"] = "No disponible"
        
        # ═══════════════════════════════════════════════════════════════════
        # Upsert
        # ═══════════════════════════════════════════════════════════════════
        if existing:
            # Update - no sobrescribir created_at
            if "created_at" in cleaned_data and existing.get("created_at"):
                del cleaned_data["created_at"]
            
            collection.update_one(
                {"phone_whatsapp": phone},
                {"$set": cleaned_data}
            )
            logger.info(f"✓ Lead actualizado: {phone}")
            return {"success": True, "operation": "updated", "phone": phone, "message": "Lead actualizado correctamente"}
        else:
            collection.insert_one(cleaned_data)
            logger.info(f"✓ Lead creado: {phone}")
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
    Réplica de MongoDB_Guardar_Email_CalCom en n8n.
    """
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        # Generar link pre-llenado (como n8n)
        base_url = CALCOM_EVENT_URL if CALCOM_EVENT_URL else "https://cal.com/agencia-fortia-hviska/60min"
        
        from urllib.parse import quote
        encoded_name = quote(name) if name else ""
        encoded_email = quote(email_calcom) if email_calcom else ""
        calcom_link = f"{base_url}?name={encoded_name}&email={encoded_email}"
        
        update_data = {
            "email_calcom": email_calcom,
            "calcom_link": calcom_link,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = collection.update_one(
            {"phone_whatsapp": phone_whatsapp},
            {"$set": update_data}
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            logger.info(f"✓ Email Cal.com guardado para: {phone_whatsapp}")
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
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
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
        
        # Hora Argentina para booking_updated_at
        try:
            tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
            hora_arg = datetime.now(tz_arg).strftime('%d/%m/%Y, %H:%M')
        except:
            hora_arg = datetime.now(timezone.utc).strftime('%d/%m/%Y, %H:%M')
        
        update_data = {
            "booking_uid": booking_data.get("booking_uid", ""),
            "booking_status": booking_data.get("booking_status", ""),
            "booking_start_time": booking_data.get("booking_start_time", ""),
            "booking_cancel_link": booking_data.get("booking_cancel_link", ""),
            "booking_reschedule_link": booking_data.get("booking_reschedule_link", ""),
            "booking_zoom_url": booking_data.get("booking_zoom_url", ""),
            "booking_updated_at": hora_arg
        }
        
        result = collection.update_one(
            {"email_calcom": email_calcom},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"✓ Booking actualizado para: {email_calcom}")
            return {"success": True, "message": "Booking actualizado"}
        else:
            logger.warning(f"⚠ Lead no encontrado con email: {email_calcom}")
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
    Usa UN documento por sesión con array de mensajes.
    """
    try:
        db = get_database()
        if db is None:
            return False
            
        collection = db["chat_history"]
        
        message = {
            "type": msg_type,
            "text": text,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Upsert: crear documento si no existe, agregar mensaje al array
        collection.update_one(
            {"sessionId": session_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        logger.info(f"✓ Mensaje guardado en chat_history: {session_id}")
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
        
        # Buscar documento de la sesión
        doc = collection.find_one({"sessionId": session_id})
        
        if not doc or "messages" not in doc:
            return []
        
        # Tomar últimos N mensajes
        messages = doc["messages"][-limit:] if len(doc["messages"]) > limit else doc["messages"]
        
        # Convertir a formato OpenAI
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
        
    except PyMongoError as e:
        logger.error(f"Error obteniendo historial: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado obteniendo historial: {e}")
        return []


def get_or_create_conversation(phone_whatsapp: str, timeout_hours: int = 24) -> str:
    """
    Obtiene la conversación activa o crea una nueva.
    """
    try:
        db = get_database()
        if db is None:
            return f"conv_{phone_whatsapp}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            
        collection = db["conversations"]
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
        
        active_conv = collection.find_one({
            "phone_whatsapp": phone_whatsapp,
            "last_message_at": {"$gte": cutoff_time},
            "status": "active"
        })
        
        if active_conv:
            collection.update_one(
                {"_id": active_conv["_id"]},
                {"$set": {"last_message_at": datetime.now(timezone.utc)}}
            )
            return str(active_conv.get("conversation_id", active_conv["_id"]))
        
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
