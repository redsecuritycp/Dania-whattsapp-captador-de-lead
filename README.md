# 🤖 DANIA/Fortia WhatsApp Bot

Bot de WhatsApp para captación y cualificación inteligente de leads con IA.

## 📋 Características

- ✅ Recepción de mensajes WhatsApp vía webhook
- ✅ Detección automática de país y zona horaria
- ✅ Extracción de datos de sitios web (Jina AI + Tavily + GPT-4o)
- ✅ Búsqueda de perfiles LinkedIn y noticias
- ✅ Guardado de leads en MongoDB Atlas
- ✅ Envío de emails de notificación (Gmail)
- ✅ Integración con Cal.com para agendamiento
- ✅ Voseo argentino profesional

## 🚀 Configuración en Replit

### 1. Crear nuevo Repl

1. Ir a [Replit](https://replit.com)
2. Crear nuevo Repl → Template: Python
3. Subir todos los archivos de este proyecto

### 2. Configurar Secrets

En Replit, ir a **Tools → Secrets** y agregar:

| Secret | Descripción |
|--------|-------------|
| `WHATSAPP_TOKEN` | Token de WhatsApp Business API |
| `WHATSAPP_PHONE_ID` | ID del número de teléfono |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificación webhook |
| `MONGODB_URI` | URI de MongoDB Atlas |
| `OPENAI_API_KEY` | API Key de OpenAI |
| `TAVILY_API_KEY` | API Key de Tavily |
| `GMAIL_USER` | Email de Gmail |
| `GMAIL_APP_PASSWORD` | App Password de Gmail |

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar

Click en **Run** o:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔗 Configurar Webhooks

### WhatsApp Business API (Meta)

1. Ir a [Meta for Developers](https://developers.facebook.com)
2. Tu App → WhatsApp → Configuración
3. Webhook URL: `https://tu-repl.replit.app/webhook/whatsapp`
4. Verify Token: el mismo que configuraste en `WHATSAPP_VERIFY_TOKEN`
5. Suscribir a: `messages`

### Cal.com

1. Ir a [Cal.com](https://cal.com) → Settings → Webhooks
2. URL: `https://tu-repl.replit.app/webhook/calcom`
3. Eventos: `BOOKING.CREATED`, `BOOKING.CANCELLED`, `BOOKING.RESCHEDULED`

## 📁 Estructura del Proyecto

```
dania-whatsapp/
├── main.py                 # FastAPI - endpoints y webhooks
├── config.py               # Configuración y variables de entorno
├── requirements.txt        # Dependencias Python
├── .replit                 # Configuración Replit
├── replit.nix              # Dependencias sistema
├── services/
│   ├── __init__.py
│   ├── whatsapp.py         # Cliente WhatsApp Business API
│   ├── mongodb.py          # Operaciones MongoDB
│   ├── openai_agent.py     # Agente con function calling
│   ├── web_extractor.py    # Jina AI + Tavily + GPT-4o
│   ├── social_research.py  # LinkedIn + noticias
│   └── gmail.py            # Envío de emails
└── tools/
    ├── __init__.py
    └── definitions.py      # Definiciones de tools y system prompt
```

## 🧪 Probar localmente

Endpoint de prueba (sin WhatsApp):

```bash
curl -X POST https://tu-repl.replit.app/test/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5493401514509", "message": "Hola"}'
```

## 📊 Colecciones MongoDB

### leads_fortia
Almacena todos los datos de los leads calificados.

### chat_history
Historial de conversaciones por sesión (phone_whatsapp).

## 🔧 Flujo del Bot

1. **Saludo inicial** con detección de país
2. **Onboarding**: nombre + ¿tiene web?
3. **Con web**:
   - Extracción automática de datos
   - Búsqueda de LinkedIn personal
   - Reporte consolidado
   - Confirmación
   - 4 preguntas de cualificación
   - Guardar + email
4. **Sin web**:
   - 8 preguntas manuales
   - Guardar + email
5. **Continuación**: info Dania, agendar reunión

## 📝 Notas importantes

- Todos los links deben ser URLs crudas (WhatsApp no renderiza Markdown)
- NUNCA inventar datos - usar "No encontrado" si falta información
- Voseo argentino obligatorio (tenés, querés, podés)
- Email se envía inmediatamente después de guardar en MongoDB

## 🆘 Troubleshooting

### El webhook no responde
- Verificar que el Repl esté corriendo
- Verificar `WHATSAPP_VERIFY_TOKEN` coincida

### No se guardan los leads
- Verificar `MONGODB_URI` en Secrets
- Verificar permisos de la IP en MongoDB Atlas (0.0.0.0/0 para Replit)

### No llegan emails
- Verificar `GMAIL_APP_PASSWORD` (no es la contraseña normal)
- Generar App Password en: https://myaccount.google.com/apppasswords

---

**Versión:** 1.0.0  
**Última actualización:** Diciembre 2024
