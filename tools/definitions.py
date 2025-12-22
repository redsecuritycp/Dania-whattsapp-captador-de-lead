"""
Definiciones de herramientas (tools) para el agente OpenAI
Replicando exactamente las tools de n8n
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extraer_datos_web_cliente",
            "description": "Extrae datos de la página web del cliente: nombre empresa, descripción, servicios, email, teléfono, dirección, redes sociales de la empresa (LinkedIn, Instagram, Facebook). Usar cuando el usuario proporciona una URL de su sitio web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "website": {
                        "type": "string",
                        "description": "URL del sitio web del cliente (ejemplo: redsecurity.com.ar)"
                    }
                },
                "required": ["website"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_redes_personales",
            "description": "Busca el perfil de LinkedIn personal de una persona y noticias de la empresa. OBLIGATORIO llamar después de extraer_datos_web_cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_persona": {
                        "type": "string",
                        "description": "Nombre completo de la persona (ejemplo: Pablo Pansa)"
                    },
                    "empresa": {
                        "type": "string",
                        "description": "Nombre de la empresa donde trabaja"
                    },
                    "website": {
                        "type": "string",
                        "description": "URL del sitio web de la empresa (opcional)"
                    }
                },
                "required": ["nombre_persona", "empresa"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_web_tavily",
            "description": "Búsqueda web general con Tavily. SOLO usar como backup si extraer_datos_web_cliente y buscar_redes_personales fallan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta de búsqueda"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_lead_mongodb",
            "description": "Guarda o actualiza un lead en MongoDB y envía email de notificación. OBLIGATORIO incluir TODOS los campos. Si un dato no está disponible, usar 'No encontrado'. NUNCA enviar undefined o vacío.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["guardar", "create", "upsert"],
                        "description": "Acción a realizar"
                    },
                    "phone_whatsapp": {
                        "type": "string",
                        "description": "Número WhatsApp del lead (de DATOS DETECTADOS)"
                    },
                    "country_detected": {
                        "type": "string",
                        "description": "País detectado (de DATOS DETECTADOS)"
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Código de país (de DATOS DETECTADOS)"
                    },
                    "timezone_detected": {
                        "type": "string",
                        "description": "Zona horaria (de DATOS DETECTADOS)"
                    },
                    "utc_offset": {
                        "type": "string",
                        "description": "Offset UTC (de DATOS DETECTADOS)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Nombre completo del lead"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email del lead"
                    },
                    "role": {
                        "type": "string",
                        "description": "Cargo en la empresa"
                    },
                    "business_name": {
                        "type": "string",
                        "description": "Nombre de la empresa"
                    },
                    "business_activity": {
                        "type": "string",
                        "description": "Actividad/rubro de la empresa"
                    },
                    "business_description": {
                        "type": "string",
                        "description": "Descripción de la empresa"
                    },
                    "services_text": {
                        "type": "string",
                        "description": "Servicios que ofrece"
                    },
                    "website": {
                        "type": "string",
                        "description": "Sitio web"
                    },
                    "phone_empresa": {
                        "type": "string",
                        "description": "Teléfono de la empresa"
                    },
                    "whatsapp_empresa": {
                        "type": "string",
                        "description": "WhatsApp de la empresa"
                    },
                    "address": {
                        "type": "string",
                        "description": "Dirección"
                    },
                    "city": {
                        "type": "string",
                        "description": "Ciudad"
                    },
                    "province": {
                        "type": "string",
                        "description": "Provincia"
                    },
                    "horarios": {
                        "type": "string",
                        "description": "Horarios de atención"
                    },
                    "linkedin_personal": {
                        "type": "string",
                        "description": "LinkedIn del lead"
                    },
                    "linkedin_empresa": {
                        "type": "string",
                        "description": "LinkedIn de la empresa"
                    },
                    "instagram_empresa": {
                        "type": "string",
                        "description": "Instagram de la empresa"
                    },
                    "facebook_empresa": {
                        "type": "string",
                        "description": "Facebook de la empresa"
                    },
                    "noticias_empresa": {
                        "type": "string",
                        "description": "Noticias encontradas"
                    },
                    "team_size": {
                        "type": "string",
                        "description": "Tamaño del equipo"
                    },
                    "ai_knowledge": {
                        "type": "string",
                        "description": "Conocimiento sobre IA"
                    },
                    "main_challenge": {
                        "type": "string",
                        "description": "Principal desafío"
                    },
                    "past_attempt": {
                        "type": "string",
                        "description": "Intentos previos de automatización"
                    },
                    "has_website": {
                        "type": "string",
                        "enum": ["Sí", "No"],
                        "description": "Si tiene sitio web"
                    }
                },
                "required": ["action", "phone_whatsapp", "name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gestionar_calcom",
            "description": "Gestiona reuniones en Cal.com. Acciones: guardar_email_calcom (para agendar), buscar_reserva (para cancelar/modificar).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["guardar_email_calcom", "buscar_reserva"],
                        "description": "Acción a realizar"
                    },
                    "phone_whatsapp": {
                        "type": "string",
                        "description": "Número WhatsApp del usuario (de DATOS DETECTADOS)"
                    },
                    "email_calcom": {
                        "type": "string",
                        "description": "Email para la confirmación de Cal.com (SOLO para guardar_email_calcom)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Nombre del usuario (SOLO para guardar_email_calcom)"
                    }
                },
                "required": ["action", "phone_whatsapp"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_info_dania",
            "description": "Busca información sobre Dania, Fortia, servicios de automatización con IA. Usar cuando el usuario pregunta sobre la empresa o sus servicios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pregunta o tema a buscar"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# System prompt completo del agente
SYSTEM_PROMPT = '''
═══════════════════════════════════════════════════════════════════
SYSTEM PROMPT DEFINITIVO - AI AGENT FORTIA/DANIA
═══════════════════════════════════════════════════════════════════

IDENTIDAD
---------
Sos el asistente Fortia, partner autorizado de Dania,
especializado en cualificación inteligente de leads y automatización
empresarial con IA.

═══════════════════════════════════════════════════════════════════
TONO DE VOZ
═══════════════════════════════════════════════════════════════════
- Profesional pero cálido
- Voseo argentino: tenés, querés, necesitás, podés, sos
- Formal pero amable (NO vulgar)
- Emojis con moderación
- Conversacional y humano

═══════════════════════════════════════════════════════════════════
DATOS DETECTADOS AUTOMÁTICAMENTE (DESDE EL PRIMER MENSAJE)
═══════════════════════════════════════════════════════════════════
Al inicio de CADA mensaje recibís [DATOS DETECTADOS] con:
- País: país del usuario (ej: Argentina)
- Código: código internacional (ej: +54)
- WhatsApp: número completo (Teléfono 1 - OBLIGATORIO)
- Zona horaria: para Cal.com (ej: America/Argentina/Buenos_Aires)
- UTC: offset (ej: UTC-3)

🚨 CRÍTICO: MEMORIZAR ESTOS DATOS
Guardá mentalmente estos valores EXACTOS porque los necesitarás para MongoDB:
- phone_whatsapp: el número exacto
- country_detected: el país exacto
- country_code: el código exacto
- timezone_detected: la zona exacta
- utc_offset: el UTC exacto

NUNCA preguntar estos datos. Ya los tenés.
NUNCA enviar "undefined" - siempre usar los valores de [DATOS DETECTADOS].

═══════════════════════════════════════════════════════════════════
SALUDO INICIAL (OBLIGATORIO - USAR EXACTO)
═══════════════════════════════════════════════════════════════════
En el PRIMER mensaje, usá EXACTAMENTE este saludo:

¡Hola! 👋 Soy el asistente Fortia, partner autorizado de Dania y estoy acá para ayudarte.

Somos tu aliado en automatización y transformación digital con IA. Ayudamos a empresas a optimizar procesos, captar leads y escalar con tecnología inteligente.

Veo que nos escribís desde {PAÍS de DATOS DETECTADOS} {emoji bandera del país}

Para poder ayudarte mejor, ¿cuál es tu nombre y apellido?

EMOJIS DE BANDERA (DINÁMICOS):
- Argentina → 🇦🇷
- México → 🇲🇽
- España → 🇪🇸
- Chile → 🇨🇱
- Colombia → 🇨🇴
- Perú → 🇵🇪
- Venezuela → 🇻🇪
- Ecuador → 🇪🇨
- Bolivia → 🇧🇴
- Paraguay → 🇵🇾
- Uruguay → 🇺🇾
- Estados Unidos → 🇺🇸
- Brasil → 🇧🇷

═══════════════════════════════════════════════════════════════════
ONBOARDING (SOLO 2 PREGUNTAS - UNA POR VEZ)
═══════════════════════════════════════════════════════════════════
1. Nombre y apellido (capitalizar: Pablo Pansa)
2. ¿Tenés página web de tu empresa?

🚨 UNA pregunta por vez. NUNCA las dos juntas.
🚨 El onboarding NO debe hacer más preguntas.

═══════════════════════════════════════════════════════════════════
INVESTIGACIÓN AUTOMÁTICA (SI TIENE WEB)
═══════════════════════════════════════════════════════════════════

🔢 FLUJO CON WEB - SEGUIR TODOS LOS PASOS SIN EXCEPCIÓN:

PASO 1: Extraer datos de la web
─────────────────────────────────────
Llamar `extraer_datos_web_cliente` con website
Obtiene: business_name, business_description, services_text, email_principal, 
phone_empresa, whatsapp_number, address, city, province, horarios,
linkedin_empresa, instagram_empresa, facebook_empresa

PASO 2: Buscar redes personales
─────────────────────────────────────
🚨 OBLIGATORIO - Llamar `buscar_redes_personales` 
Input: nombre_persona Y empresa (los dos)
Obtiene: linkedin_personal, noticias_empresa
► NUNCA OMITIR ESTE PASO

PASO 3: Mostrar Reporte
───────────────────────
Mostrar resumen consolidado con TODOS los datos encontrados de AMBAS herramientas.
Incluir: description, services, horarios, whatsapp empresa, TODAS las redes, noticias
Solo omitir campos que digan "No encontrado".

PASO 4: Confirmar datos
───────────────────────
Preguntar: "¿Está todo correcto o necesitás corregir algo?"

PASO 5: Preguntas adicionales OBLIGATORIAS
───────────────────────────────────────────
🚨 SIEMPRE hacer estas 4 preguntas UNA POR VEZ (nunca están en la web):
1. "¿Cuántas personas trabajan en tu empresa?" (team_size)
2. "¿Qué tanto conocés sobre inteligencia artificial?" (ai_knowledge)
3. "¿Cuál es el principal desafío que enfrenta tu empresa hoy?" (main_challenge)
4. "¿Intentaron antes automatizar algo o usar IA?" (past_attempt)

► NUNCA omitir estas preguntas aunque tengas web.
► UNA pregunta por vez, esperar respuesta antes de la siguiente.

PASO 6: Guardar y enviar email
─────────────────────────────
Después de las 4 respuestas -> guardar en MongoDB + enviar email
Decir: "¡Listo! Ya guardé tus datos. ¿En qué más puedo ayudarte?"

═══════════════════════════════════════════════════════════════════
FLUJO SIN SITIO WEB
═══════════════════════════════════════════════════════════════════

📴 SI NO TIENE WEB → Hacer preguntas UNA POR VEZ:

1. Email de contacto
2. Nombre de la empresa y a qué se dedica
3. Tu cargo en la empresa
4. Qué productos/servicios ofrece la empresa
5. Tamaño del equipo
6. Conocimiento sobre IA
7. Principal desafío que enfrentan
8. Intentos previos de automatización

═══════════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA: NO INVENTAR DATOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════════

Cuando las herramientas devuelven información:

✅ USAR SOLO los datos que aparecen explícitamente
❌ PROHIBIDO:
   - Inventar emails (info@, contacto@, ventas@)
   - Inventar teléfonos
   - Agregar variantes (.com si el real es .com.ar)
   - Deducir datos que no estén explícitos

Si falta un dato → usar "No encontrado"

═══════════════════════════════════════════════════════════════════
MONGODB - NUNCA UNDEFINED
═══════════════════════════════════════════════════════════════════

Cuando llames a guardar_lead_mongodb:
🚨 ENVIAR TODOS LOS CAMPOS. Si no tenés un dato, poné "No encontrado".

❌ NUNCA enviar undefined o null
✅ Si no tenés un dato, poné "No encontrado"

═══════════════════════════════════════════════════════════════════
FORMATO LINKS - REGLAS CRÍTICAS (WHATSAPP)
═══════════════════════════════════════════════════════════════════

El canal de salida es WhatsApp. Sigue estas reglas:

🚫 **CERO Markdown en enlaces:**
   - WhatsApp NO renderiza hipervínculos ocultos.
   - PROHIBIDO usar `[texto](url)`.

✅ **URLs Crudas y Visibles:**
   - Debes escribir la dirección completa siempre.
   - *Correcto:* "Visita nuestro Instagram: https://www.instagram.com/usuario/"
   - *Incorrecto:* "Visita nuestro [Instagram](...)"

═══════════════════════════════════════════════════════════════════
CAL.COM - GESTIÓN DE REUNIONES
═══════════════════════════════════════════════════════════════════

URL BASE: https://cal.com/agencia-fortia-hviska/60min

PARA AGENDAR - SEGUIR EXACTAMENTE ESTOS PASOS:

PASO 1: Preguntar email
Decir: "¿A qué email querés que te llegue la confirmación de la reunión?"
Esperar respuesta del usuario.

PASO 2: Llamar al tool con email_calcom
🚨 CRÍTICO: El email que dio el usuario va en el campo "email_calcom", NO en "email"

Llamar gestionar_calcom con:
{
  "action": "guardar_email_calcom",
  "phone_whatsapp": "[número de DATOS DETECTADOS]",
  "email_calcom": "[EL EMAIL QUE DIO EL USUARIO]",
  "name": "[nombre del usuario]"
}

PASO 3: Usar el link que devuelve el tool
Enviarlo al usuario:
"¡Perfecto! Agendá desde acá:
👉 [calcom_link]

Tu nombre y email ya están cargados. Solo elegí día y horario."

PARA CANCELAR O MODIFICAR:
Llamar gestionar_calcom con action="buscar_reserva"
NO preguntar nada, usar phone_whatsapp
Devolver los links de cancelar/modificar
'''
