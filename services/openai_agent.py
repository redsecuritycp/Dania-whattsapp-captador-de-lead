"""
Agente de OpenAI con function calling para DANIA/Fortia
Versión con fix de mensaje de espera único
"""
import logging
import json
from typing import Optional
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from services.mongodb import (
    save_lead, find_lead_by_phone, update_lead_calcom_email,
    save_chat_message, get_chat_history
)
from services.web_extractor import extract_web_data
from services.social_research import research_person_and_company
from services.gmail import send_lead_notification
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


async def process_message(
    user_message: str,
    phone_whatsapp: str,
    country_detected: str = "",
    timezone_detected: str = "",
    utc_offset: str = "",
    country_code: str = "",
    emoji: str = ""
) -> str:
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
            "wait_message_sent": False  # FLAG para mensaje de espera único
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
                    max_tokens=2000
                )
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
            
            first_choice = choices[0]
            assistant_message = getattr(first_choice, 'message', None)
            
            if assistant_message is None:
                logger.error("Message de OpenAI es None")
                return "Hubo un error procesando tu mensaje. Por favor intentá de nuevo."
            
            tool_calls = getattr(assistant_message, 'tool_calls', None)
            
            if tool_calls and len(tool_calls) > 0:
                assistant_content = getattr(assistant_message, 'content', None) or ""
                
                tool_calls_list = []
                for tc in tool_calls:
                    tc_id = getattr(tc, 'id', '')
                    tc_function = getattr(tc, 'function', None)
                    if tc_function:
                        tc_name = getattr(tc_function, 'name', '')
                        tc_args = getattr(tc_function, 'arguments', '{}')
                    else:
                        tc_name = ''
                        tc_args = '{}'
                    
                    tool_calls_list.append({
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": tc_name,
                            "arguments": tc_args
                        }
                    })
                
                messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                    "tool_calls": tool_calls_list
                })
                
                for tc in tool_calls:
                    tc_id = getattr(tc, 'id', '')
                    tc_function = getattr(tc, 'function', None)
                    
                    if tc_function:
                        tool_name = getattr(tc_function, 'name', '')
                        tool_args_str = getattr(tc_function, 'arguments', '{}')
                    else:
                        tool_name = ''
                        tool_args_str = '{}'
                    
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parseando argumentos de tool: {e}")
                        tool_args = {}
                    
                    logger.info(f"Ejecutando tool: {tool_name}")
                    
                    # Ejecutar tool (pasando context mutable)
                    tool_result = await execute_tool(tool_name, tool_args, context)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": json.dumps(tool_result, ensure_ascii=False, default=str)
                    })
            else:
                final_response = getattr(assistant_message, 'content', None) or ""
                
                if final_response:
                    try:
                        save_chat_message(phone_whatsapp, "ai", final_response)
                    except Exception as e:
                        logger.error(f"Error guardando respuesta en historial: {e}")
                
                cleaned_response = clean_markdown_formatting(final_response) if final_response else "¿En qué puedo ayudarte?"
                return cleaned_response
        
        logger.warning(f"Límite de iteraciones alcanzado para {phone_whatsapp}")
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
        if tool_name in ["extraer_datos_web_cliente", "buscar_redes_personales"]:
            # Solo enviar si no se envió antes en esta sesión
            if not context.get("wait_message_sent", False):
                from services.whatsapp import send_whatsapp_message
                phone = context.get("phone_whatsapp", "")
                if phone:
                    try:
                        await send_whatsapp_message(
                            phone, 
                            "Dame un momento mientras investigo tu empresa... 🔍"
                        )
                        context["wait_message_sent"] = True  # Marcar como enviado
                        logger.info(f"✓ Mensaje de espera enviado a {phone}")
                    except Exception as e:
                        logger.warning(f"Error enviando mensaje de espera: {e}")
        
        if tool_name == "extraer_datos_web_cliente":
            website = arguments.get("website", "")
            if not website:
                return {"error": "No se proporcionó website"}
            result = await extract_web_data(website)
            return result if result else {"error": "No se pudo extraer datos"}
            
        elif tool_name == "buscar_redes_personales":
            nombre = arguments.get("nombre_persona", "")
            empresa = arguments.get("empresa", "")
            website = arguments.get("website", "")
            if not nombre or not empresa:
                return {"error": "Faltan nombre_persona o empresa"}
            result = await research_person_and_company(nombre, empresa, website)
            return result if result else {"error": "No se encontraron resultados"}
            
        elif tool_name == "buscar_web_tavily":
            from services.web_extractor import search_with_tavily
            query = arguments.get("query", "")
            if not query:
                return {"error": "No se proporcionó query"}
            result = await search_with_tavily(query)
            if result and isinstance(result, dict):
                answer = result.get("answer", "")
                results_list = result.get("results", [])
                content = answer
                if results_list:
                    for r in results_list[:3]:
                        content += f"\n\n{r.get('title', '')}: {r.get('url', '')}\n{r.get('content', '')[:500]}"
                return {"content": content[:5000] if content else "No se encontraron resultados"}
            return {"content": "No se encontraron resultados"}
            
        elif tool_name == "guardar_lead_mongodb":
            lead_data = {}
            for key, value in arguments.items():
                lead_data[key] = value
            
            lead_data["phone_whatsapp"] = context.get("phone_whatsapp") or lead_data.get("phone_whatsapp", "")
            lead_data["country_detected"] = context.get("country_detected") or lead_data.get("country_detected", "")
            lead_data["timezone_detected"] = context.get("timezone_detected") or lead_data.get("timezone_detected", "")
            lead_data["utc_offset"] = context.get("utc_offset") or lead_data.get("utc_offset", "")
            lead_data["country_code"] = context.get("country_code") or lead_data.get("country_code", "")
            lead_data["emoji"] = context.get("emoji") or lead_data.get("emoji", "")
            
            try:
                save_result = save_lead(lead_data)
            except Exception as e:
                logger.error(f"Error guardando lead: {e}")
                return {"operation_status": "error", "message": str(e)}
            
            email_result = {"success": False, "error": "No enviado"}
            if save_result and save_result.get("success"):
                try:
                    email_result = send_lead_notification(lead_data)
                except Exception as e:
                    logger.error(f"Error enviando email: {e}")
                    email_result = {"success": False, "error": str(e)}
            
            return {
                "operation_status": "success" if (save_result and save_result.get("success")) else "error",
                "message": save_result.get("message", "") if save_result else "Error guardando",
                "email_sent": email_result.get("success", False) if email_result else False,
                "email_error": email_result.get("error", "") if email_result else ""
            }
            
        elif tool_name == "gestionar_calcom":
            action = arguments.get("action", "")
            phone = arguments.get("phone_whatsapp") or context.get("phone_whatsapp", "")
            
            if action == "guardar_email_calcom":
                email_calcom = arguments.get("email_calcom", "")
                name = arguments.get("name", "")
                if not email_calcom:
                    return {"error": "No se proporcionó email_calcom"}
                try:
                    result = update_lead_calcom_email(phone, email_calcom, name)
                    return result if result else {"error": "Error guardando email"}
                except Exception as e:
                    return {"error": str(e)}
                
            elif action == "buscar_reserva":
                try:
                    lead = find_lead_by_phone(phone)
                    if lead and lead.get("booking_uid"):
                        return {
                            "found": True,
                            "booking_uid": lead.get("booking_uid", ""),
                            "booking_status": lead.get("booking_status", ""),
                            "booking_start_time": lead.get("booking_start_time", ""),
                            "cancel_link": lead.get("booking_cancel_link", ""),
                            "reschedule_link": lead.get("booking_reschedule_link", "")
                        }
                    else:
                        return {"found": False, "message": "No se encontró reserva"}
                except Exception as e:
                    return {"error": str(e)}
            
            return {"error": f"Acción no reconocida: {action}"}
            
        elif tool_name == "resumir_conversacion":
            phone = arguments.get("phone_whatsapp") or context.get("phone_whatsapp", "")
            incluir_en_lead = arguments.get("incluir_en_lead", False)
            
            if not phone:
                return {"error": "No se proporcionó phone_whatsapp"}
            
            try:
                # Obtener historial
                history = get_chat_history(phone, limit=50)
                
                if not history or len(history) < 2:
                    return {"summary": "Conversación muy corta para resumir", "message_count": len(history) if history else 0}
                
                # Construir texto de conversación
                conversation_text = ""
                for msg in history:
                    role = "Usuario" if msg.get("role") == "user" else "Asistente"
                    content = msg.get("content", "")[:500]  # Limitar cada mensaje
                    conversation_text += f"{role}: {content}\n\n"
                
                # Llamar a GPT para resumir
                summary_prompt = f"""Resumí esta conversación en máximo 3 párrafos cortos.
Incluí:
- Datos clave del lead (nombre, empresa, web)
- Temas principales discutidos
- Próximos pasos acordados (si los hay)

CONVERSACIÓN:
{conversation_text[:8000]}

RESUMEN (en español, máximo 500 palabras):"""

                summary_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.3,
                    max_tokens=600
                )
                
                summary = summary_response.choices[0].message.content if summary_response.choices else "No se pudo generar resumen"
                
                # Guardar en lead si se solicita
                if incluir_en_lead:
                    from datetime import datetime, timezone
                    from services.mongodb import get_database
                    
                    db = get_database()
                    if db:
                        db["leads_fortia"].update_one(
                            {"phone_whatsapp": phone},
                            {"$set": {
                                "conversation_summary": summary,
                                "summary_date": datetime.now(timezone.utc).isoformat()
                            }},
                            upsert=False
                        )
                        logger.info(f"✓ Resumen guardado para {phone}")
                
                return {
                    "summary": summary,
                    "message_count": len(history),
                    "saved_to_lead": incluir_en_lead
                }
                
            except Exception as e:
                logger.error(f"Error resumiendo conversación: {e}")
                return {"error": str(e)}
            
        elif tool_name == "buscar_info_dania":
            query = arguments.get("query", "").lower()
            
            # Información más completa sobre Dania/Fortia
            info_base = """🏢 **SOBRE DANIA Y FORTIA**

Dania es una empresa especializada en transformación digital e inteligencia artificial aplicada a negocios.

Fortia es el partner autorizado de Dania, enfocado en implementación y soporte.

🤖 **SERVICIOS PRINCIPALES:**

1. **Automatización de Procesos con IA**
   - Chatbots inteligentes para WhatsApp, web y redes sociales
   - Automatización de tareas repetitivas
   - Flujos de trabajo automatizados

2. **Captación y Cualificación de Leads**
   - Bots de atención 24/7
   - Enriquecimiento automático de datos
   - Integración con CRMs

3. **Integración de Sistemas**
   - Conexión de APIs y plataformas
   - Sincronización de datos entre sistemas
   - Webhooks y automatizaciones personalizadas

4. **Análisis de Datos con IA**
   - Reportes automatizados
   - Insights de conversaciones
   - Métricas de rendimiento

5. **Transformación Digital**
   - Consultoría estratégica
   - Implementación de soluciones a medida
   - Capacitación de equipos

💼 **BENEFICIOS:**
- Reducción de costos operativos
- Atención al cliente 24/7
- Mayor captación de leads
- Datos enriquecidos automáticamente
- Escalabilidad sin aumentar personal

📅 **¿QUERÉS SABER MÁS?**
Podés agendar una reunión con nuestro equipo para conocer cómo podemos ayudarte."""

            # Respuestas específicas según query
            if any(word in query for word in ["precio", "costo", "cuanto", "cuánto", "valor"]):
                info = info_base + "\n\n💰 **PRECIOS:**\nLos precios varían según el proyecto y las necesidades específicas. Te recomiendo agendar una reunión para hacer un diagnóstico gratuito y darte un presupuesto personalizado."
            
            elif any(word in query for word in ["tiempo", "demora", "cuanto tarda", "implementar"]):
                info = info_base + "\n\n⏱️ **TIEMPOS:**\nUna implementación básica puede estar lista en 1-2 semanas. Proyectos más complejos pueden tomar 4-8 semanas. Te damos un cronograma detallado después del diagnóstico inicial."
            
            elif any(word in query for word in ["reunion", "reunión", "agendar", "llamada", "demo"]):
                info = "¡Perfecto! Para agendar una reunión, necesito tu email para enviarte la confirmación. ¿Cuál es tu email?"
            
            elif any(word in query for word in ["ejemplo", "caso", "cliente", "resultados"]):
                info = info_base + "\n\n📊 **CASOS DE ÉXITO:**\nHemos ayudado a empresas a:\n- Reducir tiempo de respuesta de 24h a minutos\n- Aumentar captación de leads en 300%\n- Automatizar procesos que tomaban 8 horas diarias\n- Mejorar satisfacción del cliente en 40%"
            
            else:
                info = info_base

            return {"info": info, "query": query}
            
        else:
            logger.warning(f"Tool no reconocida: {tool_name}")
            return {"error": f"Tool no implementada: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Error ejecutando tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}
