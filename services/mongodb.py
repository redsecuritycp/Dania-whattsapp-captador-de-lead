"""
Servicio de MongoDB para DANIA/Fortia
Campos en ESPAÑOL
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pytz

from config import MONGODB_URI, MONGODB_DATABASE, CALCOM_EVENT_URL

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db = None

# ═══════════════════════════════════════════════════════════════════
# MAPEO DE CAMPOS INGLÉS → ESPAÑOL
# ═══════════════════════════════════════════════════════════════════
CAMPO_ESPANOL = {
    # Datos detectados
    "phone_whatsapp": "telefono_whatsapp",
    "country_detected": "pais_detectado",
    "timezone_detected": "zona_horaria",
    "utc_offset": "utc_offset",
    "country_code": "codigo_pais",
    "emoji": "emoji",
    
    # Datos personales
    "name": "nombre",
    "email": "email",
    "role": "cargo",
    
    # Datos empresa
    "business_name": "nombre_empresa",
    "business_activity": "rubro",
    "business_description": "descripcion_empresa",
    "business_model": "modelo_negocio",
    "services_text": "servicios",
    "website": "sitio_web",
    "phone_empresa": "telefono_empresa",
    "whatsapp_empresa": "whatsapp_empresa",
    "horarios": "horarios",
    
    # Ubicación
    "address": "direccion",
    "city": "ciudad",
    "province": "provincia",
    
    # Redes sociales
    "linkedin_personal": "linkedin_personal",
    "linkedin_empresa": "linkedin_empresa",
    "instagram_empresa": "instagram_empresa",
    "facebook_empresa": "facebook_empresa",
    "noticias_empresa": "noticias_empresa",
    
    # Cualificación
    "team_size": "tamanio_equipo",
    "ai_knowledge": "conocimiento_ia",
    "main_challenge": "desafio_principal",
    "past_attempt": "intento_previo",
    "has_website": "tiene_web",
    "qualification_tier": "nivel_calificacion",
    "challenges_detected": "desafios_detectados",
    
    # Timestamps
    "created_at": "creado_en",
    "updated_at": "actualizado_en",
    "created_at_local": "creado_local",
    
    # Booking/Reserva
    "booking_uid": "reserva_uid",
    "booking_status": "reserva_estado",
    "booking_start_time": "reserva_fecha_hora",
    "booking_cancel_link": "reserva_link_cancelar",
    "booking_reschedule_link": "reserva_link_reprogramar",
    "booking_zoom_url": "reserva_zoom_url",
    "booking_updated_at": "reserva_actualizado_en",
    
    # Cal.com
    "email_calcom": "email_calcom",
    "calcom_link": "calcom_link",
    
    # Otros
    "action": "accion",
    "conversation_summary": "resumen_conversacion",
    "summary_date": "fecha_resumen",
    "reminders_sent": "recordatorios_enviados",
}


def traducir_campos(data: dict) -> dict:
    """Traduce campos de inglés a español."""
    traducido = {}
    for key, value in data.items():
        nuevo_key = CAMPO_ESPANOL.get(key, key)
        traducido[nuevo_key] = value
    return traducido


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
        _client.admin.command('ping')
        logger.info(f"✓ Conectado a MongoDB: {MONGODB_DATABASE}")
        return _db
    except PyMongoError as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        return None


def get_local_datetime(timezone_str: str) -> str:
    """Genera fecha local en el timezone del cliente."""
    try:
        if not timezone_str or timezone_str in ['No detectado', 'No proporcionado']:
            return 'No disponible'
        
        tz = pytz.timezone(timezone_str)
        ahora = datetime.now(tz)
        fecha_local = ahora.strftime('%d/%m/%Y, %H:%M:%S')
        return f"{fecha_local} ({timezone_str})"
    except Exception as e:
        logger.warning(f"Error generando fecha local: {e}")
        return 'No disponible'


def save_lead(lead_data: dict) -> dict:
    """
    Guarda o actualiza un lead en MongoDB.
    Usa telefono_whatsapp como identificador único.
    Todos los campos en ESPAÑOL.
    """
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        # Obtener teléfono (puede venir en inglés o español)
        phone = lead_data.get("phone_whatsapp") or lead_data.get("telefono_whatsapp", "")
        if not phone:
            return {"success": False, "error": "telefono_whatsapp es requerido"}
        
        # ═══════════════════════════════════════════════════════════════════
        # Traducir campos a español
        # ═══════════════════════════════════════════════════════════════════
        datos_espanol = traducir_campos(lead_data)
        
        # ═══════════════════════════════════════════════════════════════════
        # Limpiar valores undefined/None → "No proporcionado"
        # ═══════════════════════════════════════════════════════════════════
        cleaned_data = {}
        for key, value in datos_espanol.items():
            if value is None or value == "" or value == "undefined" or value == "null":
                cleaned_data[key] = "No proporcionado"
            else:
                cleaned_data[key] = value
        
        # ═══════════════════════════════════════════════════════════════════
        # Timestamps
        # ═══════════════════════════════════════════════════════════════════
        now = datetime.now(timezone.utc)
        cleaned_data["actualizado_en"] = now.isoformat()
        
        # Verificar si existe (buscar por ambos nombres de campo)
        existing = collection.find_one({
            "$or": [
                {"telefono_whatsapp": phone},
                {"phone_whatsapp": phone}
            ]
        })
        
        if not existing:
            cleaned_data["creado_en"] = now.isoformat()
        
        # ═══════════════════════════════════════════════════════════════════
        # creado_local - Hora local del cliente
        # ═══════════════════════════════════════════════════════════════════
        timezone_detected = (
            cleaned_data.get("zona_horaria") or 
            cleaned_data.get("timezone_detected", "")
        )
        if timezone_detected and timezone_detected not in ["No detectado", "No proporcionado"]:
            cleaned_data["creado_local"] = get_local_datetime(timezone_detected)
        else:
            cleaned_data["creado_local"] = "No disponible"
        
        # ═══════════════════════════════════════════════════════════════════
        # Upsert
        # ═══════════════════════════════════════════════════════════════════
        if existing:
            # Update - no sobrescribir creado_en
            if "creado_en" in cleaned_data and existing.get("creado_en"):
                del cleaned_data["creado_en"]
            if "creado_en" in cleaned_data and existing.get("created_at"):
                del cleaned_data["creado_en"]
            
            # Buscar por el campo que tenga
            filter_query = {"telefono_whatsapp": phone}
            if existing.get("phone_whatsapp"):
                filter_query = {"phone_whatsapp": phone}
            
            collection.update_one(filter_query, {"$set": cleaned_data})
            logger.info(f"✓ Lead actualizado: {phone}")
            return {
                "success": True, 
                "operation": "updated", 
                "phone": phone, 
                "message": "Lead actualizado correctamente"
            }
        else:
            collection.insert_one(cleaned_data)
            logger.info(f"✓ Lead creado: {phone}")
            return {
                "success": True, 
                "operation": "created", 
                "phone": phone, 
                "message": "Lead creado correctamente"
            }
            
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
        # Buscar por ambos campos (compatibilidad)
        lead = collection.find_one({
            "$or": [
                {"telefono_whatsapp": phone_whatsapp},
                {"phone_whatsapp": phone_whatsapp}
            ]
        })
        if lead:
            lead["_id"] = str(lead.get("_id", ""))
        return lead
    except PyMongoError as e:
        logger.error(f"Error buscando lead: {e}")
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


def update_lead_calcom_email(phone_whatsapp: str, email_calcom: str, name: str = "") -> dict:
    """Guarda el email de Cal.com y genera link pre-llenado."""
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        base_url = CALCOM_EVENT_URL or "https://cal.com/agencia-fortia-hviska/60min"
        
        from urllib.parse import quote
        encoded_name = quote(name) if name else ""
        encoded_email = quote(email_calcom) if email_calcom else ""
        calcom_link = f"{base_url}?name={encoded_name}&email={encoded_email}"
        
        update_data = {
            "email_calcom": email_calcom,
            "calcom_link": calcom_link,
            "actualizado_en": datetime.now(timezone.utc).isoformat()
        }
        
        # Buscar por ambos campos
        result = collection.update_one(
            {"$or": [
                {"telefono_whatsapp": phone_whatsapp},
                {"phone_whatsapp": phone_whatsapp}
            ]},
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
            collection.insert_one({
                "telefono_whatsapp": phone_whatsapp,
                "email_calcom": email_calcom,
                "calcom_link": calcom_link,
                "creado_en": datetime.now(timezone.utc).isoformat(),
                "actualizado_en": datetime.now(timezone.utc).isoformat()
            })
            return {
                "success": True,
                "calcom_link": calcom_link,
                "message": "Lead creado con email Cal.com"
            }
            
    except PyMongoError as e:
        logger.error(f"Error actualizando email Cal.com: {e}")
        return {"success": False, "error": str(e)}


def update_lead_booking(email_calcom: str, booking_data: dict) -> dict:
    """Actualiza datos de reserva desde webhook de Cal.com."""
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
            
        collection = db["leads_fortia"]
        
        try:
            tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
            hora_arg = datetime.now(tz_arg).strftime('%d/%m/%Y, %H:%M')
        except:
            hora_arg = datetime.now(timezone.utc).strftime('%d/%m/%Y, %H:%M')
        
        # Campos en español
        update_data = {
            "reserva_uid": booking_data.get("booking_uid", ""),
            "reserva_estado": booking_data.get("booking_status", ""),
            "reserva_fecha_hora": booking_data.get("booking_start_time", ""),
            "reserva_link_cancelar": booking_data.get("booking_cancel_link", ""),
            "reserva_link_reprogramar": booking_data.get("booking_reschedule_link", ""),
            "reserva_zoom_url": booking_data.get("booking_zoom_url", ""),
            "reserva_actualizado_en": hora_arg
        }
        
        result = collection.update_one(
            {"email_calcom": email_calcom},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"✓ Reserva actualizada para: {email_calcom}")
            return {"success": True, "message": "Reserva actualizada"}
        else:
            logger.warning(f"⚠ Lead no encontrado con email: {email_calcom}")
            return {"success": False, "error": "Lead no encontrado"}
            
    except PyMongoError as e:
        logger.error(f"Error actualizando reserva: {e}")
        return {"success": False, "error": str(e)}


def save_chat_message(session_id: str, msg_type: str, text: str) -> bool:
    """Guarda un mensaje en el historial de chat."""
    try:
        db = get_database()
        if db is None:
            return False
            
        collection = db["chat_history"]
        
        message = {
            "tipo": msg_type,
            "texto": text,
            "timestamp": datetime.now(timezone.utc)
        }
        
        collection.update_one(
            {"sessionId": session_id},
            {
                "$push": {"mensajes": message},
                "$set": {"actualizado_en": datetime.now(timezone.utc)},
                "$setOnInsert": {"creado_en": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        return True
        
    except PyMongoError as e:
        logger.error(f"Error guardando mensaje: {e}")
        return False


def get_chat_history(session_id: str, limit: int = 20) -> list:
    """Obtiene historial de chat para un usuario."""
    try:
        db = get_database()
        if db is None:
            return []
            
        collection = db["chat_history"]
        doc = collection.find_one({"sessionId": session_id})
        
        if not doc:
            return []
        
        # Buscar mensajes en ambos formatos
        messages = doc.get("mensajes") or doc.get("messages") or []
        messages = messages[-limit:] if len(messages) > limit else messages
        
        history = []
        for msg in messages:
            msg_type = msg.get("tipo") or msg.get("type", "")
            msg_text = msg.get("texto") or msg.get("text", "")
            
            if not msg_text:
                continue
                
            role = "user" if msg_type == "human" else "assistant"
            history.append({"role": role, "content": msg_text})
        
        return history
        
    except PyMongoError as e:
        logger.error(f"Error obteniendo historial: {e}")
        return []


def update_lead_summary(phone_whatsapp: str, summary: str) -> dict:
    """Actualiza el resumen de conversación de un lead."""
    try:
        db = get_database()
        if db is None:
            return {"success": False, "error": "No hay conexión a MongoDB"}
        
        collection = db["leads_fortia"]
        
        result = collection.update_one(
            {"$or": [
                {"telefono_whatsapp": phone_whatsapp},
                {"phone_whatsapp": phone_whatsapp}
            ]},
            {"$set": {
                "resumen_conversacion": summary,
                "fecha_resumen": datetime.now(timezone.utc).isoformat(),
                "actualizado_en": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count > 0:
            logger.info(f"✓ Resumen actualizado para: {phone_whatsapp}")
            return {"success": True, "message": "Resumen actualizado"}
        else:
            return {"success": False, "error": "Lead no encontrado"}
    
    except Exception as e:
        logger.error(f"Error actualizando resumen: {e}")
        return {"success": False, "error": str(e)}
