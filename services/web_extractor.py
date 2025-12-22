"""
Servicio de extracción de datos web - RÉPLICA FIEL de n8n Tool_Extractor_Web_INTELIGENTE
Pipeline: Jina AI (scraping) → Tavily (complemento) → Regex (extracción) → GPT-4o (parsing)
"""
import os
import re
import httpx
import json
import logging
from typing import Optional

from config import TAVILY_API_KEY, OPENAI_API_KEY, JINA_API_KEY

logger = logging.getLogger(__name__)


def clean_url(url: str) -> str:
    """Limpia y normaliza una URL."""
    url = url.strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url


async def fetch_with_jina(website: str) -> str:
    """
    Extrae contenido web usando Jina AI Reader.
    Réplica de 2_Jina_AI en n8n.
    """
    try:
        url = f"https://r.jina.ai/{website}"
        
        # Headers como en n8n
        headers = {
            "Accept": "text/plain",
            "X-With-Links-Summary": "true"  # CRÍTICO: Faltaba en versión anterior
        }
        
        if JINA_API_KEY:
            headers["Authorization"] = f"Bearer {JINA_API_KEY}"
        
        logger.info(f"[JINA] Extrayendo: {website}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.text
                # Filtrar contenido de error/placeholder
                if "https://r.jina.ai/YOUR_URL" in content:
                    logger.warning("[JINA] Contenido de placeholder detectado")
                    return ""
                logger.info(f"[JINA] ✓ {len(content)} caracteres extraídos")
                return content
            else:
                logger.warning(f"[JINA] Error {response.status_code} para {website}")
                return ""
    
    except Exception as e:
        logger.error(f"[JINA] Error: {e}")
        return ""


async def search_with_tavily(query: str) -> dict:
    """
    Búsqueda web con Tavily.
    Réplica de 4_Tavily_Complemento en n8n.
    """
    try:
        if not TAVILY_API_KEY:
            logger.error("[TAVILY] API key no configurada")
            return {}
        
        logger.info(f"[TAVILY] Buscando: {query[:50]}...")
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
            "include_raw_content": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[TAVILY] ✓ Respuesta recibida")
                return data
            else:
                logger.warning(f"[TAVILY] Error {response.status_code}")
                return {}
    
    except Exception as e:
        logger.error(f"[TAVILY] Error: {e}")
        return {}


def extract_with_regex(all_content: str, website: str) -> dict:
    """
    Extrae datos con regex del contenido combinado.
    Réplica EXACTA de la lógica de 5_Combinar en n8n.
    """
    regex_extract = {}
    
    # ═══════════════════════════════════════════════════════════════════
    # EMAILS
    # ═══════════════════════════════════════════════════════════════════
    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_content, re.IGNORECASE)
    # Filtrar emails inválidos
    filtered_emails = []
    for e in email_matches:
        e_lower = e.lower()
        if not any(x in e_lower for x in ['example', 'sentry', 'wixpress', '.png', '.jpg', 'website.com', 'domain.com']):
            filtered_emails.append(e)
    regex_extract['emails'] = list(dict.fromkeys(filtered_emails))[:5]  # Unique, max 5
    
    # ═══════════════════════════════════════════════════════════════════
    # TELÉFONOS (múltiples patrones como n8n)
    # ═══════════════════════════════════════════════════════════════════
    phone_patterns = [
        r'href=["\']tel:([^"\']+)["\']',
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}',
        r'\(\d{2,5}\)[\s.-]?\d{3,4}[\s.-]?\d{3,4}',
        r'\b\d{4}[\s.-]\d{4}\b'
    ]
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        for p in matches:
            cleaned = re.sub(r'href=["\']tel:', '', p).replace('"', '').replace("'", "")
            if len(re.sub(r'\D', '', cleaned)) >= 7:
                phones.append(cleaned)
    regex_extract['phones'] = list(dict.fromkeys(phones))[:5]
    
    # ═══════════════════════════════════════════════════════════════════
    # WHATSAPP
    # ═══════════════════════════════════════════════════════════════════
    wa_match = re.search(r'wa\.me/(\+?\d{10,15})|api\.whatsapp\.com/send\?phone=(\d{10,15})', all_content, re.IGNORECASE)
    regex_extract['whatsapp'] = (wa_match.group(1) or wa_match.group(2)) if wa_match else ''
    
    # ═══════════════════════════════════════════════════════════════════
    # REDES SOCIALES
    # ═══════════════════════════════════════════════════════════════════
    # LinkedIn empresa
    li_match = re.search(r'https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9_-]+', all_content, re.IGNORECASE)
    regex_extract['linkedin'] = li_match.group(0).split('?')[0] if li_match else ''
    
    # Instagram (excluir posts)
    ig_match = re.search(r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+', all_content, re.IGNORECASE)
    if ig_match and '/p/' not in ig_match.group(0):
        regex_extract['instagram'] = ig_match.group(0).split('?')[0]
    else:
        regex_extract['instagram'] = ''
    
    # Facebook (excluir posts)
    fb_match = re.search(r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.]+', all_content, re.IGNORECASE)
    if fb_match and '/posts/' not in fb_match.group(0):
        regex_extract['facebook'] = fb_match.group(0).split('?')[0]
    else:
        regex_extract['facebook'] = ''
    
    # ═══════════════════════════════════════════════════════════════════
    # SERVICIOS - Extraer categorías/productos (CRÍTICO - Faltaba)
    # ═══════════════════════════════════════════════════════════════════
    servicios_keywords = [
        'INFRAESTRUCTURA', 'WIRELESS', 'ISPS', 'SEGURIDAD', 'NETWORKING',
        'TELEFONÍA', 'TELEFONIA', 'IP TELEPHONY', 'SMART HOME', 'DOMÓTICA', 'DOMOTICA',
        'SOFTWARE', 'HARDWARE', 'CLOUD', 'CONECTIVIDAD', 'REDES',
        'CÁMARAS', 'CAMARAS', 'CCTV', 'ACCESS POINT', 'ROUTER', 'SWITCH',
        'FIBRA ÓPTICA', 'FIBRA OPTICA', 'UPS', 'ENERGÍA', 'ENERGIA',
        'ALARMAS', 'MONITOREO', 'VIDEOVIGILANCIA', 'CONTROL DE ACCESO',
        'CERCO ELÉCTRICO', 'CERCO ELECTRICO', 'AUTOMATIZACIÓN', 'AUTOMATIZACION'
    ]
    
    servicios_encontrados = []
    content_upper = all_content.upper()
    
    for keyword in servicios_keywords:
        if keyword in content_upper:
            servicios_encontrados.append(keyword.title())
    
    # También buscar en menús/navegación
    menu_patterns = [
        r'(?:productos|servicios|soluciones)[:\s]*([A-ZÁÉÍÓÚÑ\s,]+)',
        r'(?:categorías|categorias)[:\s]*([A-ZÁÉÍÓÚÑ\s,]+)'
    ]
    
    for pattern in menu_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        for match in matches:
            items = re.split(r'[,|•·-]', match)
            for item in items:
                item_clean = item.strip()
                if 3 < len(item_clean) < 30:
                    servicios_encontrados.append(item_clean.title())
    
    regex_extract['servicios'] = list(dict.fromkeys(servicios_encontrados))[:10]
    
    logger.info(f"[REGEX] Emails: {len(regex_extract['emails'])}, Phones: {len(regex_extract['phones'])}, Servicios: {len(regex_extract['servicios'])}")
    
    return regex_extract


async def parse_with_gpt(web_content: str, website: str, regex_data: dict, tavily_answer: str) -> dict:
    """
    Usa GPT-4o para extraer datos estructurados.
    Réplica de 6_GPT4o_Extraer en n8n con el prompt EXACTO.
    """
    try:
        if not OPENAI_API_KEY:
            logger.error("[GPT] API key no configurada")
            return {}
        
        logger.info("[GPT] Procesando con GPT-4o...")
        
        # Prompt EXACTO de n8n
        prompt = f"""Sos un experto extrayendo datos de sitios web empresariales.

Sitio: {website}

═══════════════════════════════════════════════════════════════════
DATOS YA ENCONTRADOS (USAR DIRECTAMENTE):
═══════════════════════════════════════════════════════════════════
- Emails: {regex_data.get('emails', [])}
- Teléfonos: {regex_data.get('phones', [])}
- WhatsApp: {regex_data.get('whatsapp', '')}
- LinkedIn: {regex_data.get('linkedin', '')}
- Instagram: {regex_data.get('instagram', '')}
- Facebook: {regex_data.get('facebook', '')}
- DESCRIPCIÓN TAVILY: {tavily_answer}

═══════════════════════════════════════════════════════════════════
CONTENIDO DEL SITIO:
═══════════════════════════════════════════════════════════════════
{web_content[:15000]}

═══════════════════════════════════════════════════════════════════
INSTRUCCIONES CRÍTICAS:
═══════════════════════════════════════════════════════════════════

1. **business_description**: 
   - SI existe "DESCRIPCIÓN TAVILY" arriba → COPIARLA TEXTUALMENTE
   - Si no existe → buscar en "about", "quienes somos", "nosotros"
   - NO poner datos de contacto como descripción

2. **services** (MUY IMPORTANTE):
   - Buscar categorías, productos, soluciones que ofrece
   - Ejemplos: "INFRAESTRUCTURA", "WIRELESS", "SEGURIDAD", "SOFTWARE"
   - Buscar en menús, secciones de productos/servicios
   - Si hay palabras como: infraestructura, wireless, ISPs, seguridad, networking → EXTRAERLAS
   - Devolver como array: ["servicio1", "servicio2", ...]

3. **business_activity**: Rubro/industria (ej: "distribución mayorista de tecnología")

4. Emails/teléfonos: Usar los del regex si son válidos
5. Ignorar "support@website.com" (es falso)
6. Si un dato no existe → "No encontrado"
7. NUNCA inventar datos

═══════════════════════════════════════════════════════════════════
RESPONDER SOLO JSON (sin ```, sin markdown):
═══════════════════════════════════════════════════════════════════

{{
  "business_name": "nombre de la empresa",
  "business_activity": "rubro o industria",
  "business_description": "descripción de qué hace la empresa (USAR TAVILY SI EXISTE)",
  "services": ["servicio1", "servicio2"],
  "email_principal": "",
  "emails_adicionales": [],
  "phone_empresa": "",
  "phones_adicionales": [],
  "whatsapp_number": "",
  "website": "{website}",
  "linkedin_empresa": "",
  "instagram_empresa": "",
  "facebook_empresa": "",
  "address": "",
  "city": "",
  "province": "",
  "country": "",
  "horarios": ""
}}"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1500
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not content:
                    logger.warning("[GPT] Respuesta vacía")
                    return {}
                
                # Limpiar markdown
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                content = content.strip()
                
                # Encontrar JSON
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    content = content[start:end + 1]
                
                parsed = json.loads(content)
                logger.info("[GPT] ✓ Datos extraídos correctamente")
                return parsed
            else:
                logger.error(f"[GPT] Error {response.status_code}")
                return {}
    
    except json.JSONDecodeError as e:
        logger.warning(f"[GPT] JSON inválido: {e}")
        return {}
    except Exception as e:
        logger.error(f"[GPT] Error: {e}")
        return {}


def merge_results(gpt_data: dict, regex_data: dict, tavily_answer: str) -> dict:
    """
    Merge de resultados GPT + Regex.
    Réplica EXACTA de la lógica de 7_Output en n8n.
    """
    resultado = gpt_data.copy() if gpt_data else {}
    
    # ═══════════════════════════════════════════════════════════════════
    # DESCRIPCIÓN - usar Tavily si GPT puso datos de contacto o no encontró
    # ═══════════════════════════════════════════════════════════════════
    desc_gpt = resultado.get('business_description', '')
    es_descripcion_mala = (
        not desc_gpt or
        desc_gpt == 'No encontrado' or
        'contact' in desc_gpt.lower() or
        'teléfono' in desc_gpt.lower() or
        'telefono' in desc_gpt.lower() or
        'email' in desc_gpt.lower() or
        'address' in desc_gpt.lower() or
        len(desc_gpt) < 50
    )
    
    if es_descripcion_mala and tavily_answer:
        resultado['business_description'] = tavily_answer
        logger.info("[MERGE] Usando descripción de Tavily")
    
    # ═══════════════════════════════════════════════════════════════════
    # SERVICIOS - usar regex si GPT no encontró
    # ═══════════════════════════════════════════════════════════════════
    servicios_gpt = resultado.get('services', [])
    if (not servicios_gpt or len(servicios_gpt) == 0) and regex_data.get('servicios'):
        resultado['services'] = regex_data['servicios']
        logger.info(f"[MERGE] Usando servicios de regex: {regex_data['servicios']}")
    
    # ═══════════════════════════════════════════════════════════════════
    # ACTIVIDAD - derivar de descripción si no existe
    # ═══════════════════════════════════════════════════════════════════
    actividad = resultado.get('business_activity', '')
    descripcion = resultado.get('business_description', '')
    
    if (not actividad or actividad == 'No encontrado') and descripcion and descripcion != 'No encontrado':
        desc_lower = descripcion.lower()
        if 'distributor' in desc_lower or 'mayorista' in desc_lower:
            resultado['business_activity'] = 'Distribución mayorista'
        elif 'technology' in desc_lower or 'tecnología' in desc_lower or 'IT' in descripcion:
            resultado['business_activity'] = 'Tecnología'
        elif 'security' in desc_lower or 'seguridad' in desc_lower:
            resultado['business_activity'] = 'Seguridad'
        elif 'software' in desc_lower:
            resultado['business_activity'] = 'Software'
        elif 'networking' in desc_lower or 'redes' in desc_lower:
            resultado['business_activity'] = 'Networking/Redes'
    
    # ═══════════════════════════════════════════════════════════════════
    # Email - ignorar support@website.com
    # ═══════════════════════════════════════════════════════════════════
    email_principal = resultado.get('email_principal', '')
    if email_principal == 'support@website.com':
        email_principal = ''
    
    if (not email_principal or email_principal == 'No encontrado') and regex_data.get('emails'):
        resultado['email_principal'] = regex_data['emails'][0]
        if len(regex_data['emails']) > 1:
            resultado['emails_adicionales'] = regex_data['emails'][1:]
    
    # ═══════════════════════════════════════════════════════════════════
    # Teléfono
    # ═══════════════════════════════════════════════════════════════════
    phone = resultado.get('phone_empresa', '')
    if (not phone or phone == 'No encontrado') and regex_data.get('phones'):
        resultado['phone_empresa'] = regex_data['phones'][0]
        if len(regex_data['phones']) > 1:
            resultado['phones_adicionales'] = regex_data['phones'][1:]
    
    # ═══════════════════════════════════════════════════════════════════
    # WhatsApp
    # ═══════════════════════════════════════════════════════════════════
    wa = resultado.get('whatsapp_number', '')
    if (not wa or wa == 'No encontrado') and regex_data.get('whatsapp'):
        resultado['whatsapp_number'] = regex_data['whatsapp']
    
    # ═══════════════════════════════════════════════════════════════════
    # Redes sociales
    # ═══════════════════════════════════════════════════════════════════
    if (not resultado.get('linkedin_empresa') or resultado.get('linkedin_empresa') == 'No encontrado') and regex_data.get('linkedin'):
        resultado['linkedin_empresa'] = regex_data['linkedin']
        logger.info(f"[MERGE] LinkedIn: {regex_data['linkedin']}")
    
    if (not resultado.get('instagram_empresa') or resultado.get('instagram_empresa') == 'No encontrado') and regex_data.get('instagram'):
        resultado['instagram_empresa'] = regex_data['instagram']
        logger.info(f"[MERGE] Instagram: {regex_data['instagram']}")
    
    if (not resultado.get('facebook_empresa') or resultado.get('facebook_empresa') == 'No encontrado') and regex_data.get('facebook'):
        resultado['facebook_empresa'] = regex_data['facebook']
        logger.info(f"[MERGE] Facebook: {regex_data['facebook']}")
    
    # ═══════════════════════════════════════════════════════════════════
    # Limpiar URLs (quitar parámetros)
    # ═══════════════════════════════════════════════════════════════════
    for field in ['linkedin_empresa', 'instagram_empresa', 'facebook_empresa']:
        url = resultado.get(field, '')
        if url and url != 'No encontrado':
            resultado[field] = url.split('?')[0].strip()
    
    # ═══════════════════════════════════════════════════════════════════
    # services_text
    # ═══════════════════════════════════════════════════════════════════
    services = resultado.get('services', [])
    if isinstance(services, list) and len(services) > 0:
        resultado['services_text'] = ', '.join([s for s in services if s and s != 'No encontrado'])
    else:
        resultado['services_text'] = 'No encontrado'
    
    return resultado


async def extract_web_data(website: str) -> dict:
    """
    Pipeline completo de extracción web.
    Réplica FIEL del workflow n8n Tool_Extractor_Web_INTELIGENTE.
    
    Flujo:
    1. Preparar URL
    2. Jina AI (scraping)
    3. Procesar Jina
    4. Tavily (complemento)
    5. Combinar + Regex
    6. GPT-4o (parsing)
    7. Merge output
    """
    logger.info(f"[EXTRACTOR] ========== Iniciando: {website} ==========")
    
    # 1. Preparar URL
    website_clean = clean_url(website)
    website_full = f"https://{website_clean}"
    
    # 2-3. Jina AI
    jina_content = await fetch_with_jina(website_clean)
    
    # 4. Tavily complemento
    tavily_query = f'"{website_clean}" contacto dirección teléfono email CUIT Argentina'
    tavily_data = await search_with_tavily(tavily_query)
    
    # Extraer contenido de Tavily
    tavily_content = ""
    tavily_answer = tavily_data.get("answer", "")
    
    if tavily_answer:
        tavily_content += f"DESCRIPCIÓN DE LA EMPRESA: {tavily_answer}\n\n"
    
    results = tavily_data.get("results", [])
    for r in results:
        tavily_content += f"[{r.get('url', '')}]\n"
        if r.get('content'):
            tavily_content += r['content'] + "\n"
        if r.get('raw_content'):
            tavily_content += r['raw_content'][:2000] + "\n---\n"
    
    logger.info(f"[TAVILY] ✓ {len(tavily_content)} caracteres extraídos")
    
    # 5. Combinar contenido
    all_content = ""
    if len(jina_content) > 100:
        all_content += f"=== SITIO WEB ===\n{jina_content}\n\n"
    if len(tavily_content) > 50:
        all_content += f"=== DATOS ADICIONALES ===\n{tavily_content}"
    
    # Truncar si es muy largo
    if len(all_content) > 20000:
        all_content = all_content[:20000]
    
    if not all_content:
        logger.warning(f"[EXTRACTOR] No se pudo obtener contenido de {website}")
        return {
            "business_name": "No encontrado",
            "business_description": "No encontrado",
            "website": website_full,
            "extraction_status": "failed"
        }
    
    # 5. Extracción con regex
    regex_data = extract_with_regex(all_content, website_clean)
    
    # 6. Parsing con GPT-4o
    gpt_data = await parse_with_gpt(all_content, website_clean, regex_data, tavily_answer)
    
    # 7. Merge de resultados
    final_data = merge_results(gpt_data, regex_data, tavily_answer)
    
    # Agregar metadatos
    final_data["website"] = website_full
    final_data["extraction_status"] = "success"
    final_data["source"] = "jina_tavily_regex_gpt4o"
    
    logger.info(f"[EXTRACTOR] ========== Completado ==========")
    
    return final_data
