# CHANGELOG - Historial de Cambios

Este archivo documenta todos los cambios realizados en el proyecto.
Formato: Fecha | Descripción | Archivo(s) afectado(s)

---

## 2024-12-27

### PASO 4B - Manejo de correcciones del usuario
- **Archivo:** `tools/definitions.py`
- **Descripción:** Agregada nueva sección PASO 4B en SYSTEM_PROMPT entre PASO 4 y PASO 5
- **Detalle:** Instrucciones para manejar cuando el usuario corrige:
  - Nombre/apellido: Actualiza internamente y busca LinkedIn con nombre corregido (sin re-extraer web)
  - Datos empresa: Corrige y continúa a PASO 5 (sin re-extraer)
  - Web diferente: Pide URL correcta y vuelve a PASO 1

### WHATSAPP PATTERNS - Mejora detección WhatsApp
- **Archivo:** `services/web_extractor.py`
- **Descripción:** Ampliados patrones regex para detectar números de WhatsApp
- **Patrones nuevos:**
  - data-phone, data-whatsapp (atributos HTML)
  - whatsapp://send?phone (links nativos)
  - "phone":"..." y 'phone':'...' (JSON)
  - wa_phone y whatsapp_number (variables JS)

### YOUTUBE PATTERNS - Mejora detección canales YouTube
- **Archivo:** `services/web_extractor.py`
- **Descripción:** Nuevo bloque para detectar canales de YouTube
- **Detalle:** 
  - Detecta /channel/, /c/, /user/ y @handles
  - Limpia parámetros de query y anchors
  - Excluye /watch y /embed (solo canales)

---

## Instrucciones

Cuando hagas cambios desde Cursor, avisame con:
- Qué cambiaste
- Para qué
- Nombre que querés darle

Yo lo documento acá con ese nombre.
