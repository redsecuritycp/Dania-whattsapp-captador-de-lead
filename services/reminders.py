"""
Servicio de recordatorios para reuniones de Cal.com
Envía notificaciones por WhatsApp en momentos clave

LÓGICA ROBUSTA: Si el server se reinicia, envía los recordatorios
que no se enviaron aunque haya pasado su momento ideal.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.mongodb import get_database
from services.whatsapp import send_whatsapp_message, send_template_reminder_24h
from config import format_fecha_es

logger = logging.getLogger(__name__)

# Scheduler global
scheduler: Optional[AsyncIOScheduler] = None


def init_scheduler():
    """Inicializa el scheduler de recordatorios."""
    global scheduler

    if scheduler is not None:
        logger.info("Scheduler ya inicializado")
        return scheduler

    scheduler = AsyncIOScheduler(timezone=pytz.UTC)

    # Job que corre cada 5 minutos para verificar recordatorios
    scheduler.add_job(check_and_send_reminders,
                      IntervalTrigger(minutes=5),
                      id='reminder_checker',
                      name='Verificador de recordatorios',
                      replace_existing=True)

    scheduler.start()
    logger.info("✅ Scheduler de recordatorios iniciado")

    return scheduler


def shutdown_scheduler():
    """Detiene el scheduler."""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler detenido")


async def check_and_send_reminders():
    """
    Verifica bookings próximos y envía recordatorios.
    Corre cada 5 minutos.
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("[REMINDERS] No hay conexión a MongoDB")
            return

        collection = db["leads_fortia"]
        now = datetime.now(pytz.UTC)
        logger.info(
            "[REMINDERS] ══════ Iniciando check de recordatorios ══════")

        # Buscar leads con booking activo
        leads_with_booking = collection.find({
            "$or": [{
                "booking_status": "created",
                "booking_start_time": {
                    "$exists": True,
                    "$ne": ""
                }
            }, {
                "reserva_estado": "created",
                "reserva_fecha_hora": {
                    "$exists": True,
                    "$ne": ""
                }
            }]
        })

        leads_list = list(leads_with_booking)
        logger.info(
            f"[REMINDERS] Encontrados {len(leads_list)} leads con booking")

        for lead in leads_list:
            try:
                phone = (lead.get("phone_whatsapp")
                         or lead.get("telefono_whatsapp", ""))
                name = lead.get("name") or lead.get("nombre", "")
                booking_str = (lead.get("booking_start_time")
                               or lead.get("reserva_fecha_hora", ""))

                if not booking_str:
                    continue

                # Parsear fecha del booking
                try:
                    if booking_str.endswith('Z'):
                        booking_clean = booking_str[:-1] + '+00:00'
                    else:
                        booking_clean = booking_str
                    booking_dt = datetime.fromisoformat(
                        booking_clean.replace('Z', '+00:00'))
                    if booking_dt.tzinfo is None:
                        booking_dt = pytz.UTC.localize(booking_dt)
                except Exception as parse_err:
                    logger.warning(
                        f"[REMINDERS] Error parseando fecha: {parse_err}")
                    continue

                # Si la reunión ya pasó hace más de 1 hora, marcar completed
                if booking_dt < now - timedelta(hours=1):
                    logger.info(
                        f"[REMINDERS] Reunión PASADA - marcando completed: "
                        f"{name} - {phone}")
                    collection.update_one({"_id": lead["_id"]}, {
                        "$set": {
                            "booking_status": "completed",
                            "reserva_estado": "completed"
                        }
                    })
                    continue

                # Procesar recordatorios
                logger.info(f"[REMINDERS] Procesando: {name} - {phone} - "
                            f"Reunión: {booking_str}")
                await process_lead_reminders(lead, now)

            except Exception as e:
                logger.error(f"[REMINDERS] Error procesando lead "
                             f"{lead.get('phone_whatsapp')}: {e}")
                continue

    except Exception as e:
        logger.error(f"[REMINDERS] Error general: {e}")


async def process_lead_reminders(lead: dict, now: datetime):
    """
    Procesa los recordatorios para un lead específico.

    LÓGICA ROBUSTA:
    - Envía recordatorios en orden de prioridad (más urgente primero)
    - Si un recordatorio no se envió y ya pasó su momento, lo envía igual
    - Solo envía UN recordatorio por ciclo para no spamear
    """
    phone = lead.get("phone_whatsapp") or lead.get("telefono_whatsapp", "")
    if not phone:
        return

    booking_start_str = (lead.get("booking_start_time")
                         or lead.get("reserva_fecha_hora", ""))
    if not booking_start_str:
        return

    # Parsear fecha de booking
    try:
        if booking_start_str.endswith('Z'):
            booking_start_str = booking_start_str[:-1] + '+00:00'
        booking_start = datetime.fromisoformat(
            booking_start_str.replace('Z', '+00:00'))
        if booking_start.tzinfo is None:
            booking_start = pytz.UTC.localize(booking_start)
    except Exception as e:
        logger.warning(
            f"[REMINDERS] Error parseando fecha: {booking_start_str} - {e}")
        return

    # Calcular minutos hasta la reunión
    diff = booking_start - now
    minutes_until = diff.total_seconds() / 60

    logger.info(f"[REMINDERS] {phone}: faltan {int(minutes_until)} minutos")

    # Si la reunión ya pasó hace más de 5 minutos, no hacer nada
    if minutes_until < -5:
        return

    # Obtener recordatorios ya enviados
    reminders_sent = (lead.get("reminders_sent")
                      or lead.get("recordatorios_enviados") or [])

    logger.info(
        f"[REMINDERS] {phone}: recordatorios ya enviados: {reminders_sent}")

    # Datos para el mensaje
    zoom_url = (lead.get("booking_zoom_url")
                or lead.get("reserva_zoom_url", ""))
    name = lead.get("name") or lead.get("nombre", "")

    # Formatear fecha/hora para mostrar
    tz_str = (lead.get("timezone_detected")
              or lead.get("zona_horaria", "America/Argentina/Buenos_Aires"))
    try:
        tz = pytz.timezone(tz_str)
        booking_local = booking_start.astimezone(tz)
    except:
        booking_local = booking_start

    fecha_str = format_fecha_es(booking_local)
    hora_str = booking_local.strftime("%H:%M")
    pais = (lead.get("country_detected")
            or lead.get("pais_detectado", "tu país"))

    # ═══════════════════════════════════════════════════════════════════
    # LÓGICA SIMPLIFICADA Y ROBUSTA
    # Prioridad: at_time > 15min > 1hr > 5hr > 24hr
    # Si no se envió uno más urgente, enviarlo aunque haya pasado
    # ═══════════════════════════════════════════════════════════════════

    reminder_to_send = None

    # 1. A LA HORA EXACTA (entre -5 y +5 minutos de la reunión)
    if -5 <= minutes_until <= 5:
        if "at_time" not in reminders_sent:
            reminder_to_send = ("at_time",
                                _get_message_at_time(name, zoom_url))

    # 2. 15 MINUTOS ANTES (o menos, hasta la hora)
    elif 0 < minutes_until <= 20:
        if "15min" not in reminders_sent:
            reminder_to_send = ("15min", _get_message_15min(zoom_url))
        elif "at_time" not in reminders_sent and minutes_until <= 5:
            # Si ya enviamos 15min pero no at_time y estamos cerca
            reminder_to_send = ("at_time",
                                _get_message_at_time(name, zoom_url))

    # 3. 1 HORA ANTES (o menos, hasta 15 min)
    elif 0 < minutes_until <= 65:
        if "1hr" not in reminders_sent:
            reminder_to_send = ("1hr", _get_message_1hr(zoom_url))
        elif "15min" not in reminders_sent and minutes_until <= 20:
            # Si ya enviamos 1hr pero no 15min y estamos cerca
            reminder_to_send = ("15min", _get_message_15min(zoom_url))

    # 4. 5 HORAS ANTES (o menos, hasta 1 hora)
    elif 0 < minutes_until <= 305:
        if "5hr" not in reminders_sent:
            reminder_to_send = ("5hr",
                                _get_message_5hr(fecha_str, hora_str,
                                                 zoom_url))
        elif "1hr" not in reminders_sent and minutes_until <= 65:
            # Si ya enviamos 5hr pero no 1hr y estamos cerca
            reminder_to_send = ("1hr", _get_message_1hr(zoom_url))

    # 5. 24 HORAS ANTES (o menos, hasta 5 horas)
    elif 0 < minutes_until <= 1445:
        if "24hr" not in reminders_sent:
            # Usar plantilla de Meta para 24hr
            await _send_24hr_template(lead, phone, name, hora_str, fecha_str,
                                      pais)
            return  # Terminar aquí, no seguir con flujo normal
        elif "5hr" not in reminders_sent and minutes_until <= 305:
            # Si ya enviamos 24hr pero no 5hr y estamos cerca
            reminder_to_send = ("5hr",
                                _get_message_5hr(fecha_str, hora_str,
                                                 zoom_url))

    # ═══════════════════════════════════════════════════════════════════
    # ENVIAR EL RECORDATORIO
    # ═══════════════════════════════════════════════════════════════════

    if reminder_to_send:
        reminder_type, message = reminder_to_send
        await _send_reminder(phone, reminder_type, message, minutes_until)
    else:
        logger.info(f"[REMINDERS] {phone}: no hay recordatorio para enviar "
                    f"(ya enviados o fuera de rango)")


async def _send_reminder(phone: str, reminder_type: str, message: str,
                         minutes_until: float):
    """Envía un recordatorio y lo marca en MongoDB."""
    phone_clean = phone.lstrip('+')

    logger.info(f"[REMINDERS] 📤 Enviando '{reminder_type}' a {phone} "
                f"(faltan {int(minutes_until)} min)")

    success = await send_whatsapp_message(phone_clean, message)

    if success:
        # Marcar como enviado en MongoDB
        db = get_database()
        if db is not None:
            db["leads_fortia"].update_one(
                {
                    "$or": [{
                        "phone_whatsapp": phone
                    }, {
                        "telefono_whatsapp": phone
                    }]
                }, {
                    "$addToSet": {
                        "reminders_sent": reminder_type,
                        "recordatorios_enviados": reminder_type
                    }
                })
        logger.info(f"[REMINDERS] ✓ Enviado '{reminder_type}' a {phone}")
    else:
        logger.error(
            f"[REMINDERS] ✗ Error enviando '{reminder_type}' a {phone}")


async def _send_24hr_template(lead: dict, phone: str, name: str, hora_str: str,
                              fecha_str: str, pais: str):
    """Envía el template de 24 horas usando la plantilla de Meta."""
    link_modificar = (lead.get("booking_reschedule_link")
                      or lead.get("reserva_link_reprogramar")
                      or lead.get("booking_cancel_link")
                      or lead.get("reserva_link_cancelar", ""))

    logger.info(f"[REMINDERS] 📤 Enviando template 24hr a {phone}")

    template_sent = await send_template_reminder_24h(
        phone=phone,
        nombre=name if name else "usuario",
        hora=hora_str,
        fecha=fecha_str,
        link_modificar=link_modificar if link_modificar else "N/A")

    if template_sent:
        # Marcar como enviado en MongoDB
        db = get_database()
        if db is not None:
            db["leads_fortia"].update_one(
                {
                    "$or": [{
                        "phone_whatsapp": phone
                    }, {
                        "telefono_whatsapp": phone
                    }]
                }, {
                    "$addToSet": {
                        "reminders_sent": "24hr",
                        "recordatorios_enviados": "24hr"
                    }
                })
        logger.info(f"[REMINDERS] ✓ Template 24hr enviado a {phone}")
    else:
        logger.error(f"[REMINDERS] ✗ Error enviando template 24hr a {phone}")


# ============================================================================
# MENSAJES DE RECORDATORIO
# ============================================================================


def _get_message_24hr(name: str, fecha: str, hora: str, pais: str) -> str:
    """Mensaje 24 horas antes."""
    saludo = f"¡Hola {name}! " if name else "¡Hola! "
    return f"""{saludo}⏰ ¡Mañana es tu consultoría gratuita!

📅 Fecha: {fecha}
🕐 Hora: {hora} (hora de {pais})

No te la pierdas, es una oportunidad única para explorar cómo la IA puede transformar tu negocio.

💡 Esta es una sesión exclusiva y no habrá otra disponible si no asistís.

Recordá que podés modificarla o cancelarla con 24hs de antelación desde este mismo chat.

¿Seguimos en pie? Respondé 'Sí' para confirmar 👍"""


def _get_message_5hr(fecha: str, hora: str, zoom_url: str) -> str:
    """Mensaje 5 horas antes."""
    msg = f"""⏰ En unas horas tenés tu consultoría gratuita.

📅 {fecha} a las {hora}"""

    if zoom_url:
        msg += f"\n\n📍 Link de acceso:\n{zoom_url}"

    msg += "\n\nPreparamos todo para ayudarte. ¡Nos vemos pronto! 🚀"

    return msg


def _get_message_1hr(zoom_url: str) -> str:
    """Mensaje 1 hora antes."""
    msg = "⏰ ¡En 1 hora nos vemos!"

    if zoom_url:
        msg += f"\n\n📍 Link de acceso:\n{zoom_url}"

    msg += ("\n\nTené a mano cualquier duda o información de tu negocio "
            "que quieras compartir. 📋")

    return msg


def _get_message_15min(zoom_url: str) -> str:
    """Mensaje 15 minutos antes."""
    msg = "🔔 ¡Empezamos en 15 minutos!"

    if zoom_url:
        msg += f"\n\n📍 Ingresá acá:\n{zoom_url}"

    msg += "\n\n¡Te esperamos! 🎯"

    return msg


def _get_message_at_time(name: str, zoom_url: str) -> str:
    """Mensaje a la hora exacta."""
    saludo = f"¡{name}! " if name else ""
    msg = f"🎯 {saludo}¡Estamos en la sala esperándote!"

    if zoom_url:
        msg += f"\n\n📍 Ingresá ahora:\n{zoom_url}"

    msg += "\n\nSi tenés algún inconveniente, avisanos por acá. 👋"

    return msg


# ============================================================================
# MENSAJES DE CONFIRMACIÓN Y CANCELACIÓN (llamados desde webhook)
# ============================================================================


async def send_booking_confirmation(phone: str,
                                    name: str,
                                    fecha: str,
                                    hora: str,
                                    pais: str,
                                    zoom_url: str = "",
                                    cancel_link: str = "",
                                    reschedule_link: str = "") -> bool:
    """Envía confirmación de reserva por WhatsApp."""
    saludo = f"¡Hola {name}! " if name else "¡Hola! "

    msg = f"""{saludo}✅ ¡Tu reunión está confirmada!

📅 Fecha: {fecha}
🕐 Hora: {hora} (hora de {pais})"""

    if zoom_url:
        msg += f"\n\n📍 Link de la reunión:\n{zoom_url}"

    msg += ("\n\n💡 No te pierdas esta consultoría gratuita, es una "
            "oportunidad única para explorar cómo la IA puede transformar "
            "tu negocio.")

    msg += ("\n\n📝 Recordá que a través de este chat podés modificarla "
            "o cancelarla con 24hs de antelación.")

    phone_clean = phone.lstrip('+')

    result = await send_whatsapp_message(phone_clean, msg)

    if result:
        logger.info(f"[CONFIRMATION] ✓ Confirmación enviada a {phone}")
    else:
        logger.error(f"[CONFIRMATION] ✗ Error enviando confirmación a {phone}")

    return bool(result)


async def send_booking_cancellation(phone: str,
                                    name: str,
                                    fecha: str,
                                    reschedule_link: str = "") -> bool:
    """Envía notificación de cancelación por WhatsApp."""
    saludo = f"Hola {name}, " if name else ""

    msg = f"""{saludo}❌ Tu reunión del {fecha} fue cancelada.

Si querés reagendar, decime y te paso el link para elegir un nuevo horario. 📅"""

    phone_clean = phone.lstrip('+')

    result = await send_whatsapp_message(phone_clean, msg)

    if result:
        logger.info(f"[CANCELLATION] ✓ Cancelación enviada a {phone}")
    else:
        logger.error(f"[CANCELLATION] ✗ Error enviando cancelación a {phone}")

    return bool(result)


async def send_booking_rescheduled(phone: str,
                                   name: str,
                                   nueva_fecha: str,
                                   nueva_hora: str,
                                   pais: str,
                                   zoom_url: str = "") -> bool:
    """Envía notificación de reprogramación por WhatsApp."""
    saludo = f"¡Hola {name}! " if name else "¡Hola! "

    msg = f"""{saludo}📅 Tu reunión fue reprogramada.

📅 Nueva fecha: {nueva_fecha}
🕐 Nueva hora: {nueva_hora} (hora de {pais})"""

    if zoom_url:
        msg += f"\n\n📍 Link de la reunión:\n{zoom_url}"

    msg += "\n\n¡Te esperamos! 🚀"

    phone_clean = phone.lstrip('+')

    result = await send_whatsapp_message(phone_clean, msg)

    if result:
        logger.info(f"[RESCHEDULED] ✓ Reprogramación enviada a {phone}")
    else:
        logger.error(
            f"[RESCHEDULED] ✗ Error enviando reprogramación a {phone}")

    return bool(result)


def reset_reminders_for_lead(phone: str):
    """
    Resetea los recordatorios enviados para un lead.
    Útil cuando se reprograma una reunión.
    """
    try:
        db = get_database()
        if db is not None:
            db["leads_fortia"].update_one(
                {
                    "$or": [{
                        "phone_whatsapp": phone
                    }, {
                        "telefono_whatsapp": phone
                    }]
                },
                {"$set": {
                    "reminders_sent": [],
                    "recordatorios_enviados": []
                }})
            logger.info(f"[REMINDERS] Recordatorios reseteados para {phone}")
    except Exception as e:
        logger.error(f"[REMINDERS] Error reseteando recordatorios: {e}")
