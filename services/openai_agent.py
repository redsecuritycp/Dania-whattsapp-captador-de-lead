"""
Agente de OpenAI con function calling para DANIA/Fortia
Versión 2.0 - Incluye tool de investigación de desafíos
"""
import logging
import json
from typing import Optional
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from services.mongodb import (save_lead, find_lead_by_phone,
                              update_lead_calcom_email, save_chat_message,
                              get_chat_history, update_lead_summary)
from services.web_extractor import extract_web_data
from services.social_research import research_person_and_company
from services.gmail import send_lead_notification
from services.dania_knowledge import buscar_info_dania
from services.tts import text_to_audio_response
from services.challenges_research import (investigar_desafios_empresa,
                                          calcular_qualification_tier)
from tools.definitions import SYSTEM_PROMPT, TOOLS as TOOLS_DEFINITIONS
from utils.text_cleaner import clean_markdown_formatting

logger = logging.getLogger(__name__)

# Inicializar cliente OpenAI
client = None
try:
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("Cliente OpenAI inicializado")
    else:
        logger.error("OPENAI_API_KEY no configurada")
except Exception as e:
    logger.error(f"Error inicializando OpenAI: {e}")


async def process_message(user_message: str,
                          phone_whatsapp: str,
                          country_detected: str = "",
                          timezone_detected: str = "",
                          utc_offset: str = "",
                          country_code: str = "",
                          emoji: str = "",
                          city_detected: str = "",
                          province_detected: str = "",
                          original_message_type: str = "text") -> str:
    """
    Procesa un mensaje del usuario y genera respuesta usando el agente.
    """
    try:
        if not client:
            logger.error("Cliente OpenAI no disponible")
            return "Hubo un error de configuración. Por favor intentá más tarde."

        # Guardar mensaje del usuario en historial
        try:
            save_chat_message(phone_whatsapp, "human", user_message)
        except Exception as e:
            logger.error(f"Error guardando mensaje en historial: {e}")

        # Obtener historial de conversación
        chat_history = []
        try:
            chat_history = get_chat_history(phone_whatsapp, limit=20)
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")

        # Construir el mensaje con DATOS DETECTADOS (como hace n8n)
        mensaje_con_datos = f"""[DATOS DETECTADOS]
País: {country_detected}
Ciudad: {city_detected if city_detected else "No detectada"}
Provincia: {province_detected if province_detected else "No detectada"}
WhatsApp: {phone_whatsapp}
Zona horaria: {timezone_detected}
UTC: {utc_offset}

[MENSAJE DEL USUARIO]
{user_message}"""

        # Construir mensajes para OpenAI
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": mensaje_con_datos})

        # Contexto para ejecución de tools
        context = {
            "phone_whatsapp": phone_whatsapp,
            "country_detected": country_detected,
            "timezone_detected": timezone_detected,
            "utc_offset": utc_offset,
            "country_code": country_code,
            "emoji": emoji,
            "city": city_detected,
            "province": province_detected,
            "wait_message_sent": False
        }

        # Loop de function calling
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                model_to_use = OPENAI_MODEL if OPENAI_MODEL else "gpt-4o-mini"
                response = client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    tools=TOOLS_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=2000)
            except Exception as e:
                logger.error(f"Error llamando a OpenAI: {e}", exc_info=True)
                return "Hubo un error procesando tu mensaje. Por favor intentá de nuevo."

            if response is None:
                logger.error("Respuesta de OpenAI es None")
                return "Hubo un error procesando tu mensaje. Por favor intentá de nuevo."

            choices = getattr(response, 'choices', None)
            if not choices or len(choices) == 0:
                logger.error("Respuesta de OpenAI sin choices")
                return "Hubo un error procesando tu mensaje. Por favor intentá de nuevo."

            choice = choices[0]
            message = choice.message

            # Si no hay tool calls, retornar la respuesta
            if not message.tool_calls:
                content = message.content or ""

                # Guardar respuesta en historial
                if content:
                    try:
                        save_chat_message(phone_whatsapp, "ai", content)
                    except Exception as e:
                        logger.error(
                            f"Error guardando respuesta en historial: {e}")

                # Limpiar formato Markdown para WhatsApp
                cleaned_response = clean_markdown_formatting(content)

                # Si el mensaje original era audio, responder con TTS
                if original_message_type == "audio":
                    logger.info(
                        "[AGENT] Mensaje original era audio, enviando TTS...")
                    tts_success = await text_to_audio_response(
                        cleaned_response, phone_whatsapp)
                    if tts_success:
                        logger.info("[AGENT] ✓ Audio TTS enviado")
                    return cleaned_response

                return cleaned_response

            # Procesar tool calls
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                logger.info(f"[AGENT] Ejecutando tool: {tool_name}")

                # Ejecutar la tool
                tool_result = await execute_tool(tool_name, arguments, context)

                # Agregar resultado al mensaje
                messages.append({
                    "role":
                    "tool",
                    "tool_call_id":
                    tool_call.id,
                    "content":
                    json.dumps(tool_result, ensure_ascii=False)
                })

        logger.warning(
            f"Límite de iteraciones alcanzado para {phone_whatsapp}")
        return "Disculpá, hubo un problema procesando tu mensaje. ¿Podés intentar de nuevo?"

    except Exception as e:
        logger.error(f"Error en process_message: {e}", exc_info=True)
        return "Disculpá, hubo un error. ¿Podés intentar de nuevo en unos segundos?"


async def execute_tool(tool_name: str, arguments: dict, context: dict) -> dict:
    """
    Ejecuta una tool y retorna el resultado.
    Context es mutable para mantener estado entre calls.
    """
    try:
        # ═══════════════════════════════════════════════════════════════════
        # MENSAJE DE ESPERA ÚNICO para tools de investigación
        # ═══════════════════════════════════════════════════════════════════
        if tool_name in [
                "extraer_datos_web_cliente", "buscar_redes_personales",
                "investigar_desafios_empresa"
        ]:
            if not context.get("wait_message_sent", False):
                from services.whatsapp import send_whatsapp_message
                phone = context.get("phone_whatsapp", "")
                if phone:
                    try:
                        await send_whatsapp_message(
                            phone, "Dame un momento por favor 🔍")
                        context["wait_message_sent"] = True
                        logger.info(f"✓ Mensaje de espera enviado a {phone}")
                    except Exception as e:
                        logger.warning(
                            f"Error enviando mensaje de espera: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # EXTRAER DATOS WEB
        # ═══════════════════════════════════════════════════════════════════
        if tool_name == "extraer_datos_web_cliente":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            website = arguments.get("website", "")
            if not website:
                logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                return {"error": "No se proporcionó website"}
            result = await extract_web_data(website)

            # Guardar datos importantes en context
            # NO sobrescribir city/province que vienen del número
            if result:
                context["linkedin_empresa"] = result.get(
                    "linkedin_empresa", "")
                context["facebook_empresa"] = result.get(
                    "facebook_empresa", "")
                context["instagram_empresa"] = result.get(
                    "instagram_empresa", "")
                # Ubicación de la WEB en campos separados
                context["city_web"] = result.get("city", "")
                context["province_web"] = result.get("province", "")
                context["email_principal"] = result.get("email_principal", "")
                context["business_activity"] = result.get(
                    "business_activity", "")
                context["business_name"] = result.get("business_name", "")
                logger.info(f"[CONTEXT] Datos guardados: "
                            f"LinkedIn={context.get('linkedin_empresa')}, "
                            f"Rubro={context.get('business_activity')}")

            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return result or {"error": "No se pudo extraer datos"}

        # ═══════════════════════════════════════════════════════════════════
        # BUSCAR REDES PERSONALES
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "buscar_redes_personales":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            nombre = arguments.get("nombre_persona", "")
            empresa = arguments.get("empresa", "")
            website = arguments.get("website", "")

            linkedin_empresa = context.get("linkedin_empresa", "")
            facebook_empresa = context.get("facebook_empresa", "")
            instagram_empresa = context.get("instagram_empresa", "")

            # Priorizar ubicación de la web, si no hay usar la del número
            city_web = context.get("city_web", "")
            province_web = context.get("province_web", "")
            city_phone = context.get("city", "")
            province_phone = context.get("province", "")

            city = city_web if city_web else city_phone
            province = province_web if province_web else province_phone
            country = context.get("country_detected", "")

            result = await research_person_and_company(
                nombre_persona=nombre,
                empresa=empresa,
                website=website,
                linkedin_empresa_input=linkedin_empresa,
                facebook_empresa_input=facebook_empresa,
                instagram_empresa_input=instagram_empresa,
                city=city,
                province=province,
                country=country)
            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return result or {"error": "No se pudieron encontrar redes"}

        # ═══════════════════════════════════════════════════════════════════
        # INVESTIGAR DESAFÍOS EMPRESA
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "investigar_desafios_empresa":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            rubro = arguments.get("rubro", "") or context.get(
                "business_activity", "")
            pais = arguments.get("pais", "") or context.get(
                "country_detected", "")
            team_size = arguments.get("team_size", "")
            business_description = arguments.get("business_description", "")

            if not rubro:
                logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                return {
                    "error": "No se proporcionó rubro/actividad de la empresa"
                }

            result = await investigar_desafios_empresa(
                rubro=rubro,
                pais=pais,
                team_size=team_size,
                business_description=business_description)

            context["challenges_detected"] = result.get("desafios", [])

            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return result

        # ═══════════════════════════════════════════════════════════════════
        # BUSCAR WEB TAVILY
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "buscar_web_tavily":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            from services.tavily_search import search_tavily
            query = arguments.get("query", "")
            result = await search_tavily(query)
            if result and isinstance(result, dict):
                answer = result.get("answer", "")
                results_list = result.get("results", [])
                content = answer
                if results_list:
                    for r in results_list[:3]:
                        content += (
                            f"\n\n{r.get('title', '')}: {r.get('url', '')}\n"
                            f"{r.get('content', '')[:500]}")
                logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                return {
                    "content":
                    content[:5000]
                    if content else "No se encontraron resultados"
                }
            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return {"content": "No se encontraron resultados"}

        # ═══════════════════════════════════════════════════════════════════
        # GUARDAR LEAD MONGODB
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "guardar_lead_mongodb":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            lead_data = {}
            for key, value in arguments.items():
                lead_data[key] = value

            # Usar datos del context si no vienen en arguments
            lead_data["phone_whatsapp"] = (context.get("phone_whatsapp")
                                           or lead_data.get(
                                               "phone_whatsapp", ""))
            lead_data["country_detected"] = (context.get("country_detected")
                                             or lead_data.get(
                                                 "country_detected", ""))
            lead_data["timezone_detected"] = (context.get("timezone_detected")
                                              or lead_data.get(
                                                  "timezone_detected", ""))
            lead_data["utc_offset"] = (context.get("utc_offset")
                                       or lead_data.get("utc_offset", ""))
            lead_data["country_code"] = (context.get("country_code")
                                         or lead_data.get("country_code", ""))
            lead_data["emoji"] = (context.get("emoji")
                                  or lead_data.get("emoji", ""))

            # Agregar challenges_detected del context si existe
            if context.get("challenges_detected"
                           ) and not lead_data.get("challenges_detected"):
                lead_data["challenges_detected"] = ", ".join(
                    context["challenges_detected"][:3])

            try:
                save_result = save_lead(lead_data)
            except Exception as e:
                logger.error(f"Error guardando lead: {e}")
                logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                return {"operation_status": "error", "message": str(e)}

            email_result = {"success": False, "error": "No enviado"}
            if save_result and save_result.get("success"):
                try:
                    email_result = send_lead_notification(lead_data)
                except Exception as e:
                    logger.error(f"Error enviando notificación: {e}")

            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return {
                "operation_status":
                "success" if save_result.get("success") else "error",
                "message": save_result.get("message", ""),
                "email_sent": email_result.get("success", False)
            }

        # ═══════════════════════════════════════════════════════════════════
        # GESTIONAR CAL.COM
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "gestionar_calcom":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            action = arguments.get("action", "")
            phone = (arguments.get("phone_whatsapp", "")
                     or context.get("phone_whatsapp", ""))

            if action == "guardar_email_calcom":
                email = arguments.get("email_calcom", "")
                name = arguments.get("name", "")

                if not email:
                    logger.info(
                        f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                    return {"error": "No se proporcionó email"}

                result = update_lead_calcom_email(phone, email, name)
                logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                return result

            elif action == "buscar_reserva":
                lead = find_lead_by_phone(phone)
                if lead and lead.get("booking_uid"):
                    logger.info(
                        f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                    return {
                        "found":
                        True,
                        "booking_uid":
                        lead.get("booking_uid"),
                        "booking_status":
                        lead.get("booking_status"),
                        "booking_start_time":
                        lead.get("booking_start_time"),
                        "booking_cancel_link":
                        lead.get("booking_cancel_link"),
                        "booking_reschedule_link":
                        lead.get("booking_reschedule_link"),
                        "booking_zoom_url":
                        lead.get("booking_zoom_url")
                    }
                else:
                    logger.info(
                        f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                    return {
                        "found": False,
                        "message": "No se encontró reserva"
                    }

            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return {"error": f"Acción no reconocida: {action}"}

        # ═══════════════════════════════════════════════════════════════════
        # BUSCAR INFO DANIA
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "buscar_info_dania":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            query = arguments.get("query", "")
            result = await buscar_info_dania(query)
            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return {"content": result}

        # ═══════════════════════════════════════════════════════════════════
        # RESUMIR CONVERSACIÓN
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "resumir_conversacion":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            phone = (arguments.get("phone_whatsapp", "")
                     or context.get("phone_whatsapp", ""))
            incluir_en_lead = arguments.get("incluir_en_lead", False)

            history = get_chat_history(phone, limit=50)

            if not history:
                logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                return {"summary": "No hay historial para resumir"}

            try:
                summary_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role":
                        "system",
                        "content":
                        ("Resumí esta conversación en español en máximo "
                         "200 palabras, destacando: datos del lead, empresa, "
                         "desafíos mencionados, y cualquier compromiso o "
                         "siguiente paso.")
                    }, {
                        "role":
                        "user",
                        "content":
                        json.dumps(history, ensure_ascii=False)
                    }],
                    temperature=0.3,
                    max_tokens=500)
                summary = summary_response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generando resumen: {e}")
                summary = "Error generando resumen"

            if incluir_en_lead and phone:
                update_lead_summary(phone, summary)

            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            return {"summary": summary}

        # ═══════════════════════════════════════════════════════════════════
        # TOOL NO RECONOCIDA
        # ═══════════════════════════════════════════════════════════════════
        else:
            logger.warning(f"Tool no reconocida: {tool_name}")
            return {"error": f"Tool no reconocida: {tool_name}"}

    except Exception as e:
        logger.error(f"Error ejecutando tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}
