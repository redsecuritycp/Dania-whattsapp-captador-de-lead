"""
Agente de OpenAI con function calling para DANIA/Fortia
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
            "emoji": emoji
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
            
            # Acceso seguro a la respuesta
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
            
            # Obtener tool_calls de forma segura
            tool_calls = getattr(assistant_message, 'tool_calls', None)
            
            # Si hay tool calls, ejecutarlas
            if tool_calls and len(tool_calls) > 0:
                # Construir mensaje del asistente para el historial
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
                    
                    # Ejecutar tool
                    tool_result = await execute_tool(tool_name, tool_args, context)
                    
                    # Agregar resultado al historial
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": json.dumps(tool_result, ensure_ascii=False, default=str)
                    })
            else:
                # No más tool calls, tenemos la respuesta final
                final_response = getattr(assistant_message, 'content', None) or ""
                
                if final_response:
                    # Guardar respuesta en historial
                    try:
                        save_chat_message(phone_whatsapp, "ai", final_response)
                    except Exception as e:
                        logger.error(f"Error guardando respuesta en historial: {e}")
                
                cleaned_response = clean_markdown_formatting(final_response) if final_response else "¿En qué puedo ayudarte?"
                return cleaned_response
        
        # Si llegamos al límite de iteraciones
        logger.warning(f"Límite de iteraciones alcanzado para {phone_whatsapp}")
        return "Disculpá, hubo un problema procesando tu mensaje. ¿Podés intentar de nuevo?"
        
    except Exception as e:
        logger.error(f"Error en process_message: {e}", exc_info=True)
        return "Disculpá, hubo un error. ¿Podés intentar de nuevo en unos segundos?"


async def execute_tool(tool_name: str, arguments: dict, context: dict) -> dict:
    """
    Ejecuta una tool y retorna el resultado.
    """
    try:
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
            # Agregar datos de contexto
            lead_data = {}
            for key, value in arguments.items():
                lead_data[key] = value
            
            lead_data["phone_whatsapp"] = context.get("phone_whatsapp") or lead_data.get("phone_whatsapp", "")
            lead_data["country_detected"] = context.get("country_detected") or lead_data.get("country_detected", "")
            lead_data["timezone_detected"] = context.get("timezone_detected") or lead_data.get("timezone_detected", "")
            lead_data["utc_offset"] = context.get("utc_offset") or lead_data.get("utc_offset", "")
            lead_data["country_code"] = context.get("country_code") or lead_data.get("country_code", "")
            lead_data["emoji"] = context.get("emoji") or lead_data.get("emoji", "")
            
            # Guardar en MongoDB
            try:
                save_result = save_lead(lead_data)
            except Exception as e:
                logger.error(f"Error guardando lead: {e}")
                return {"operation_status": "error", "message": str(e)}
            
            # Enviar email de notificación
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
            
        elif tool_name == "buscar_info_dania":
            query = arguments.get("query", "").lower()
            
            info = """Dania y Fortia ofrecen servicios de:

🤖 Automatización de procesos con IA
💬 Chatbots inteligentes para WhatsApp y web
🔗 Integración de sistemas y APIs
📊 Análisis de datos con inteligencia artificial
🚀 Transformación digital personalizada

Ayudamos a empresas a optimizar operaciones, captar más leads y escalar con tecnología inteligente.

Para más información, podés agendar una reunión con nuestro equipo."""

            return {"info": info, "query": query}
            
        else:
            logger.warning(f"Tool no reconocida: {tool_name}")
            return {"error": f"Tool no implementada: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Error ejecutando tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}
