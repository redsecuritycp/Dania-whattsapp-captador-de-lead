"""
Agente de OpenAI con function calling para DANIA/Fortia
Versión 2.0 - Incluye tool de investigación de desafíos
"""
import logging
import json
import asyncio
from typing import Optional
from datetime import datetime, timezone
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from services.mongodb import (
    save_lead, 
    find_lead_by_phone, 
    update_lead_calcom_email,
    save_chat_message,
    get_chat_history, 
    update_lead_summary,
    get_lead_field,
    get_database
)
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

# ═════════════════════════════════════════════════════════
# MENSAJES DE PROGRESO
# ═════════════════════════════════════════════════════════

async def send_progress_message(
    phone: str, 
    message: str
) -> None:
    """
    Envía mensaje de progreso al usuario.
    No bloquea si falla (fire-and-forget).
    """
    try:
        from services.whatsapp import send_whatsapp_message
        await send_whatsapp_message(phone, message)
    except Exception as e:
        logger.warning(
            f"[PROGRESS] No se pudo enviar mensaje de progreso: {e}"
        )

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


# ============================================================================
# INVESTIGACIÓN EN BACKGROUND
# ============================================================================

async def iniciar_investigacion_background(
    phone: str,
    nombre: str,
    web: str,
    ubicacion: str
):
    """
    Ejecuta investigación completa en background mientras el 
    usuario responde las preguntas de cualificación.
    
    Guarda resultados en MongoDB para que GPT los lea después.
    """
    try:
        db = get_database()
        if db is None:
            logger.error("[BACKGROUND] No hay conexión a MongoDB")
            return
        
        collection = db["leads_fortia"]
        
        # Marcar como "en progreso"
        collection.update_one(
            {"phone_whatsapp": phone},
            {
                "$set": {
                    "investigacion_status": "en_progreso",
                    "investigacion_started_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                }
            },
            upsert=True
        )
        
        logger.info(
            f"[BACKGROUND] Iniciando investigación para {phone}"
        )
        
        # ═══════════════════════════════════════════════════════════
        # 1. EXTRACCIÓN WEB
        # ═══════════════════════════════════════════════════════════
        logger.info(f"[BACKGROUND] Extrayendo web: {web}")
        datos_web = await extract_web_data(web)
        
        if datos_web:
            collection.update_one(
                {"phone_whatsapp": phone},
                {"$set": {
                    "datos_web_background": datos_web,
                    "business_name": datos_web.get(
                        "business_name", "No encontrado"
                    ),
                    "business_activity": datos_web.get(
                        "business_activity", "No encontrado"
                    ),
                    "linkedin_empresa": datos_web.get(
                        "linkedin_empresa", "No encontrado"
                    ),
                    "facebook_empresa": datos_web.get(
                        "facebook_empresa", "No encontrado"
                    ),
                    "instagram_empresa": datos_web.get(
                        "instagram_empresa", "No encontrado"
                    )
                }}
            )
            logger.info(f"[BACKGROUND] ✓ Datos web guardados")
        
        # ═══════════════════════════════════════════════════════════
        # 2. BÚSQUEDA LINKEDIN PERSONAL + NOTICIAS
        # ═══════════════════════════════════════════════════════════
        empresa = datos_web.get("business_name", "") if datos_web else ""
        
        logger.info(f"[BACKGROUND] Buscando LinkedIn: {nombre}")
        linkedin_data = await research_person_and_company(
            nombre_persona=nombre,
            empresa=empresa,
            website=web,
            linkedin_empresa_input=datos_web.get(
                "linkedin_empresa", ""
            ) if datos_web else "",
            facebook_empresa_input=datos_web.get(
                "facebook_empresa", ""
            ) if datos_web else "",
            instagram_empresa_input=datos_web.get(
                "instagram_empresa", ""
            ) if datos_web else "",
            city="",
            province="",
            country=ubicacion
        )
        
        if linkedin_data:
            collection.update_one(
                {"phone_whatsapp": phone},
                {"$set": {
                    "linkedin_personal": linkedin_data.get(
                        "linkedin_personal", "No encontrado"
                    ),
                    "linkedin_personal_confianza": linkedin_data.get(
                        "linkedin_personal_confianza", 0
                    ),
                    "noticias_empresa": linkedin_data.get(
                        "noticias_empresa", "No se encontraron noticias"
                    )
                }}
            )
            logger.info(
                f"[BACKGROUND] ✓ LinkedIn y noticias guardados"
            )
        
        # ═══════════════════════════════════════════════════════════
        # 3. DESAFÍOS DEL RUBRO
        # ═══════════════════════════════════════════════════════════
        rubro = datos_web.get(
            "business_activity", ""
        ) if datos_web else ""
        
        if rubro and rubro != "No encontrado":
            logger.info(
                f"[BACKGROUND] Investigando desafíos: {rubro}"
            )
            desafios_data = await investigar_desafios_empresa(
                rubro=rubro,
                pais=ubicacion
            )
            
            if desafios_data:
                collection.update_one(
                    {"phone_whatsapp": phone},
                    {"$set": {
                        "desafios_rubro": desafios_data.get(
                            "desafios", []
                        ),
                        "desafios_texto": desafios_data.get(
                            "texto_formateado", ""
                        )
                    }}
                )
                logger.info(f"[BACKGROUND] ✓ Desafíos guardados")
        
        # ═══════════════════════════════════════════════════════════
        # MARCAR COMO COMPLETADA
        # ═══════════════════════════════════════════════════════════
        collection.update_one(
            {"phone_whatsapp": phone},
            {"$set": {
                "investigacion_status": "completada",
                "investigacion_completada_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }}
        )
        
        logger.info(
            f"[BACKGROUND] ✅ Investigación completa para {phone}"
        )
    
    except Exception as e:
        logger.error(f"[BACKGROUND] Error: {e}", exc_info=True)
        try:
            db = get_database()
            if db is not None:
                db["leads_fortia"].update_one(
                    {"phone_whatsapp": phone},
                    {"$set": {"investigacion_status": "fallida"}}
                )
        except:
            pass


async def esperar_investigacion_completa(
    phone: str,
    max_wait_seconds: int = 180
) -> dict:
    """
    Espera a que termine la investigación en background.
    Hace polling cada 5 segundos.
    
    Returns:
        {
            "completada": bool,
            "rubro": str,
            "datos": dict (opcional)
        }
    """
    try:
        db = get_database()
        if db is None:
            return {"completada": False, "rubro": "tu empresa"}
        
        collection = db["leads_fortia"]
        elapsed = 0
        
        while elapsed < max_wait_seconds:
            lead = collection.find_one({"phone_whatsapp": phone})
            
            if lead:
                status = lead.get("investigacion_status", "")
                
                if status == "completada":
                    rubro = lead.get(
                        "business_activity", "tu empresa"
                    )
                    if not rubro or rubro == "No encontrado":
                        rubro = "tu empresa"
                    
                    logger.info(
                        f"[BACKGROUND] ✓ Completada para {phone}, "
                        f"rubro: {rubro}"
                    )
                    return {
                        "completada": True,
                        "rubro": rubro,
                        "datos": {
                            "business_name": lead.get(
                                "business_name", ""
                            ),
                            "linkedin_personal": lead.get(
                                "linkedin_personal", ""
                            ),
                            "noticias_empresa": lead.get(
                                "noticias_empresa", ""
                            ),
                            "desafios_rubro": lead.get(
                                "desafios_rubro", []
                            )
                        }
                    }
                
                elif status == "fallida":
                    logger.warning(
                        f"[BACKGROUND] Investigación falló para {phone}"
                    )
                    return {
                        "completada": False,
                        "rubro": "tu empresa"
                    }
            
            # Esperar 5 segundos
            await asyncio.sleep(5)
            elapsed += 5
        
        logger.warning(
            f"[BACKGROUND] Timeout esperando investigación ({phone})"
        )
        return {"completada": False, "rubro": "tu empresa"}
    
    except Exception as e:
        logger.error(f"[BACKGROUND] Error esperando: {e}")
        return {"completada": False, "rubro": "tu empresa"}


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
        # EXTRAER DATOS WEB (CON BACKGROUND)
        # ═══════════════════════════════════════════════════════════════════
        if tool_name == "extraer_datos_web_cliente":
            logger.info(f"[TOOL] ══════ INICIANDO: {tool_name} ══════")
            
            website = arguments.get("website", "")
            phone = context.get("phone_whatsapp", "")
            
            if not website:
                logger.info(
                    f"[TOOL] ══════ COMPLETADO: {tool_name} ══════"
                )
                return {"error": "No se proporcionó URL"}
            
            # 1. Enviar ÚNICO mensaje de espera
            from services.whatsapp import send_whatsapp_message
            await send_whatsapp_message(
                phone,
                "Perfecto! Dame un minuto para preparar todo..."
            )
            logger.info(f"[TOOL] ✓ Mensaje de espera enviado")
            
            # 2. Lanzar investigación en background (NO esperar)
            nombre_usuario = context.get("name", "")
            ubicacion = context.get("country_detected", "Argentina")
            
            asyncio.create_task(
                iniciar_investigacion_background(
                    phone=phone,
                    nombre=nombre_usuario,
                    web=website,
                    ubicacion=ubicacion
                )
            )
            logger.info(f"[TOOL] ✓ Investigación lanzada en background")
            
            # 3. ESPERAR 50 SEGUNDOS (temporizador real)
            logger.info(f"[TOOL] Esperando 50 segundos...")
            await asyncio.sleep(50)
            
            # 4. Enviar mensaje de transición
            await send_whatsapp_message(
                phone,
                "Mientras termino de preparar todo, te hago unas "
                "preguntas rápidas."
            )
            logger.info(f"[TOOL] ✓ Mensaje de transición enviado")
            
            # 5. Esperar 10 segundos más
            await asyncio.sleep(10)
            
            logger.info(f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
            
            # 6. Retornar señal para empezar preguntas
            return {
                "status": "ready",
                "website": website,
                "message": "Listo para preguntas de cualificación"
            }

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

            # Obtener email del contexto
            email_contacto = context.get("email_principal", "")
            
            result = await research_person_and_company(
                nombre_persona=nombre,
                empresa=empresa,
                website=website,
                linkedin_empresa_input=linkedin_empresa,
                facebook_empresa_input=facebook_empresa,
                instagram_empresa_input=instagram_empresa,
                city=city,
                province=province,
                country=country,
                email_contacto=email_contacto)
            
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

            # Mensaje de progreso
            phone = context.get("phone_whatsapp", "")
            if phone:
                await send_progress_message(
                    phone,
                    "📊 Investigando desafíos típicos de tu industria..."
                )

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
            if context.get("challenges_detected") and not lead_data.get("challenges_detected"):
                lead_data["challenges_detected"] = ", ".join(
                    context["challenges_detected"][:3])
            
            # Agregar business_model del context si no viene en arguments
            if context.get("business_model") and not lead_data.get("business_model"):
                lead_data["business_model"] = context.get("business_model")
                logger.info(
                    f"[GUARDAR] business_model del context: "
                    f"{lead_data['business_model']}"
                )
            
            # Si aún no hay business_model, intentar inferirlo
            if not lead_data.get("business_model") or \
               lead_data.get("business_model") in ["", "No encontrado", "No proporcionado"]:
                activity = lead_data.get("business_activity", "").lower()
                if activity:
                    if any(x in activity for x in ['software', 'saas', 'plataforma', 'app']):
                        lead_data["business_model"] = "SaaS"
                    elif any(x in activity for x in ['tienda', 'venta', 'retail', 'comercio']):
                        lead_data["business_model"] = "Retail"
                    elif any(x in activity for x in ['mayorista', 'distribuidor', 'distribución']):
                        lead_data["business_model"] = "Mayorista"
                    elif any(x in activity for x in ['servicio', 'consultor', 'asesor', 'agencia']):
                        lead_data["business_model"] = "Servicios profesionales"
                    elif any(x in activity for x in ['fabricación', 'manufactura', 'fábrica', 'industria']):
                        lead_data["business_model"] = "Fabricante"
                    elif any(x in activity for x in ['agro', 'campo', 'agrícola', 'ganadería']):
                        lead_data["business_model"] = "Agroindustria"
                    elif any(x in activity for x in ['construcción', 'inmobiliaria', 'obra']):
                        lead_data["business_model"] = "Construcción/Inmobiliaria"
                    elif any(x in activity for x in ['salud', 'médico', 'clínica', 'hospital']):
                        lead_data["business_model"] = "Salud"
                    elif any(x in activity for x in ['educación', 'escuela', 'universidad', 'capacitación']):
                        lead_data["business_model"] = "Educación"
                    elif any(x in activity for x in ['restaurant', 'gastronom', 'comida', 'bar']):
                        lead_data["business_model"] = "Gastronomía"
                    else:
                        lead_data["business_model"] = "B2B"  # Default
                    
                    logger.info(
                        f"[GUARDAR] business_model inferido de '{activity}': "
                        f"{lead_data['business_model']}"
                    )

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
                booking_uid = get_lead_field(lead, "booking_uid", "")
                if lead and booking_uid:
                    logger.info(
                        f"[TOOL] ══════ COMPLETADO: {tool_name} ══════")
                    return {
                        "found": True,
                        "booking_uid": booking_uid,
                        "booking_status": get_lead_field(
                            lead, "booking_status", ""
                        ),
                        "booking_start_time": get_lead_field(
                            lead, "booking_start_time", ""
                        ),
                        "booking_cancel_link": get_lead_field(
                            lead, "booking_cancel_link", ""
                        ),
                        "booking_reschedule_link": get_lead_field(
                            lead, "booking_reschedule_link", ""
                        ),
                        "booking_zoom_url": get_lead_field(
                            lead, "booking_zoom_url", ""
                        )
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
        # VERIFICAR INVESTIGACIÓN COMPLETA
        # ═══════════════════════════════════════════════════════════════════
        elif tool_name == "verificar_investigacion_completa":
            logger.info(
                f"[TOOL] ══════ INICIANDO: {tool_name} ══════"
            )
            
            phone = context.get("phone_whatsapp", "")
            
            try:
                db = get_database()
                if db is None:
                    logger.info(
                        f"[TOOL] ══════ COMPLETADO: {tool_name} ══════"
                    )
                    return {
                        "completada": False,
                        "datos": {},
                        "desafios": []
                    }
                
                collection = db["leads_fortia"]
                lead = collection.find_one({"phone_whatsapp": phone})
                
                if not lead:
                    logger.info(
                        f"[TOOL] ══════ COMPLETADO: {tool_name} ══════"
                    )
                    return {
                        "completada": False,
                        "datos": {},
                        "desafios": []
                    }
                
                status = lead.get("investigacion_status", "")
                
                # Si NO completó, esperar
                if status != "completada":
                    logger.info(
                        "[TOOL] Investigación no completada, "
                        "esperando..."
                    )
                    
                    from services.whatsapp import send_whatsapp_message
                    await send_whatsapp_message(
                        phone,
                        "Dejame chequear un par de cosas antes "
                        "de la última pregunta..."
                    )
                    
                    resultado = await esperar_investigacion_completa(
                        phone, 180
                    )
                    
                    lead = collection.find_one(
                        {"phone_whatsapp": phone}
                    )
                    if not lead:
                        logger.info(
                            f"[TOOL] ══════ COMPLETADO: "
                            f"{tool_name} ══════"
                        )
                        return {
                            "completada": False,
                            "datos": {},
                            "desafios": []
                        }
                
                # ═══════════════════════════════════════════════════
                # LEER TODOS LOS DATOS DE MONGODB
                # ═══════════════════════════════════════════════════
                
                # datos_web_background tiene TODO lo extraído
                dwb = lead.get("datos_web_background", {})
                
                # Helper para obtener con fallback
                def get_val(campo, default="No encontrado"):
                    # Primero de lead, luego de datos_web_background
                    val = lead.get(campo)
                    if val in [None, "", "null", "No encontrado"]:
                        val = dwb.get(campo)
                    if val in [None, "", "null", "No encontrado"]:
                        return default
                    return val
                
                # Construir objeto con TODOS los datos
                datos = {
                    # ═══════════════════════════════════════════
                    # EMPRESA
                    # ═══════════════════════════════════════════
                    "business_name": get_val("business_name"),
                    "business_activity": get_val("business_activity"),
                    "business_model": get_val("business_model"),
                    "business_description": get_val(
                        "business_description"
                    ),
                    "services": get_val("services"),
                    "services_text": get_val("services_text"),
                    
                    # ═══════════════════════════════════════════
                    # TU PERFIL (persona que escribe)
                    # ═══════════════════════════════════════════
                    "name": lead.get("name", "No encontrado"),
                    "cargo_detectado": get_val("cargo_detectado"),
                    "linkedin_personal": lead.get(
                        "linkedin_personal", "No encontrado"
                    ),
                    "linkedin_personal_confianza": lead.get(
                        "linkedin_personal_confianza", 0
                    ),
                    
                    # ═══════════════════════════════════════════
                    # UBICACIÓN
                    # ═══════════════════════════════════════════
                    "address": get_val("address"),
                    "city": get_val("city"),
                    "province": get_val("province"),
                    "country": lead.get(
                        "country_detected", 
                        get_val("country")
                    ),
                    "timezone": lead.get(
                        "timezone_detected", "No encontrado"
                    ),
                    "utc_offset": lead.get(
                        "utc_offset", "No encontrado"
                    ),
                    "google_maps_url": get_val("google_maps_url"),
                    
                    # ═══════════════════════════════════════════
                    # CONTACTO
                    # ═══════════════════════════════════════════
                    "phone_empresa": get_val("phone_empresa"),
                    "phones_adicionales": get_val(
                        "phones_adicionales", []
                    ),
                    "whatsapp_empresa": get_val("whatsapp_empresa"),
                    "email_empresa": get_val("email_principal"),
                    "emails_adicionales": get_val(
                        "emails_adicionales", []
                    ),
                    "horarios": get_val("horarios"),
                    
                    # ═══════════════════════════════════════════
                    # REDES EMPRESA
                    # ═══════════════════════════════════════════
                    "website": lead.get("website") or dwb.get(
                        "url", "No encontrado"
                    ),
                    "linkedin_empresa": get_val("linkedin_empresa"),
                    "instagram_empresa": get_val("instagram_empresa"),
                    "facebook_empresa": get_val("facebook_empresa"),
                    "youtube": get_val("youtube"),
                    "twitter": get_val("twitter"),
                    
                    # ═══════════════════════════════════════════
                    # NOTICIAS
                    # ═══════════════════════════════════════════
                    "noticias_empresa": lead.get(
                        "noticias_empresa", 
                        "No se encontraron noticias recientes"
                    ),
                }
                
                # Construir ubicación completa para mostrar
                ubicacion_parts = []
                if datos["address"] != "No encontrado":
                    ubicacion_parts.append(datos["address"])
                if datos["city"] != "No encontrado":
                    ubicacion_parts.append(datos["city"])
                if datos["province"] != "No encontrado":
                    ubicacion_parts.append(datos["province"])
                if datos["country"] != "No encontrado":
                    ubicacion_parts.append(datos["country"])
                datos["ubicacion_completa"] = ", ".join(
                    ubicacion_parts
                ) if ubicacion_parts else "No encontrado"
                
                # Obtener desafíos
                desafios = lead.get("desafios_rubro", [])
                if not desafios:
                    desafios = []
                desafios = desafios[:5]
                
                # Logs para debug
                logger.info(f"[TOOL] Empresa: {datos['business_name']}")
                logger.info(f"[TOOL] Rubro: {datos['business_activity']}")
                logger.info(f"[TOOL] Modelo: {datos['business_model']}")
                logger.info(f"[TOOL] Tel: {datos['phone_empresa']}")
                logger.info(f"[TOOL] WA: {datos['whatsapp_empresa']}")
                logger.info(f"[TOOL] Email: {datos['email_empresa']}")
                logger.info(f"[TOOL] Dirección: {datos['address']}")
                logger.info(
                    f"[TOOL] LinkedIn personal: "
                    f"{datos['linkedin_personal']}"
                )
                logger.info(f"[TOOL] Instagram: {datos['instagram_empresa']}")
                logger.info(f"[TOOL] Facebook: {datos['facebook_empresa']}")
                logger.info(f"[TOOL] YouTube: {datos['youtube']}")
                logger.info(f"[TOOL] Desafíos: {len(desafios)}")
                logger.info(
                    f"[TOOL] ══════ COMPLETADO: {tool_name} ══════"
                )
                
                return {
                    "completada": True,
                    "datos": datos,
                    "desafios": desafios
                }
            
            except Exception as e:
                logger.error(f"[TOOL] Error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                logger.info(
                    f"[TOOL] ══════ COMPLETADO: {tool_name} ══════"
                )
                return {
                    "completada": False,
                    "datos": {},
                    "desafios": []
                }

        # ═══════════════════════════════════════════════════════════════════
        # TOOL NO RECONOCIDA
        # ═══════════════════════════════════════════════════════════════════
        else:
            logger.warning(f"Tool no reconocida: {tool_name}")
            return {"error": f"Tool no reconocida: {tool_name}"}

    except Exception as e:
        logger.error(f"Error ejecutando tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}
