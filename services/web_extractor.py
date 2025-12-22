"""
Servicio de extracción de datos web - RÉPLICA FIEL de n8n
Pipeline: Tavily (búsqueda) → HTTP Fetch (HTML directo) → Regex (extracción) → GPT-4o (parsing)
Fallback: Jina AI si HTTP fetch falla
"""
import os
import re
import httpx
import json
import logging
from typing import Optional
from urllib.parse import urlparse

from config import TAVILY_API_KEY, OPENAI_API_KEY, JINA_API_KEY

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30.0


def clean_url(url: str) -> str:
    """Limpia y normaliza una URL."""
    url = url.strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url


async def fetch_html_direct(url: str) -> str:
    """
    Fetch HTML directo como hace n8n en Fetch_HTML.
    """
    try:
        if not url.startswith('http'):
            url = f"https://{url}"
        
        logger.info(f"[HTTP] Fetching: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.text
                logger.info(f"[HTTP] ✓ {len(content)} caracteres obtenidos")
                return content
            else:
                logger.warning(f"[HTTP] Error {response.status_code}")
                return ""
    except Exception as e:
        logger.error(f"[HTTP] Error: {e}")
        return ""


async def fetch_with_jina(website: str) -> str:
    """
    Extrae contenido web usando Jina AI Reader (backup).
    """
    try:
        url = f"https://r.jina.ai/{website}"
        
        headers = {
            "Accept": "text/plain",
            "X-With-Links-Summary": "true"
        }
        
        if JINA_API_KEY:
            headers["Authorization"] = f"Bearer {JINA_API_KEY}"
        
        logger.info(f"[JINA] Extrayendo: {website}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.text
                if "https://r.jina.ai/YOUR_URL" in content:
                    return ""
                logger.info(f"[JINA] ✓ {len(content)} caracteres extraídos")
                return content
            else:
                logger.warning(f"[JINA] Error {response.status_code}")
                return ""
    except Exception as e:
        logger.error(f"[JINA] Error: {e}")
        return ""


async def search_with_tavily(query: str) -> dict:
    """
    Búsqueda web con Tavily.
    """
    try:
        if not TAVILY_API_KEY:
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


def clean_text(text: str) -> str:
    """Limpia texto HTML."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_with_regex(all_content: str, website: str) -> dict:
    """
    Extrae datos con regex del contenido.
    Réplica del Extractor_v8 de n8n Tool_Buscar_Web_Tavily_OpenAI.
    """
    regex_extract = {}
    search_text = clean_text(all_content)
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. BUSINESS NAME
    # ═══════════════════════════════════════════════════════════════════
    business_name = ""
    title_match = re.search(r'<title>([^<]+)</title>', all_content, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        title = re.split(r'\s*[|\-–—]\s*', title)[0].strip()
        if len(title) > 2 and len(title) < 100:
            business_name = title
    
    # Meta og:site_name
    if not business_name:
        og_match = re.search(r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']', all_content, re.IGNORECASE)
        if og_match:
            business_name = og_match.group(1).strip()
    
    regex_extract['business_name'] = business_name
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. BUSINESS DESCRIPTION
    # ═══════════════════════════════════════════════════════════════════
    business_description = ""
    
    # Meta description
    meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', all_content, re.IGNORECASE)
    if meta_desc:
        business_description = meta_desc.group(1).strip()
    
    # og:description como fallback
    if not business_description or len(business_description) < 50:
        og_desc = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', all_content, re.IGNORECASE)
        if og_desc:
            business_description = og_desc.group(1).strip()
    
    regex_extract['business_description'] = business_description
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. BUSINESS ACTIVITY
    # ═══════════════════════════════════════════════════════════════════
    business_activity = ""
    
    activity_patterns = [
        r'somos\s+(?:una\s+)?(?:empresa|compañía)\s+(?:de|dedicada\s+a)\s+([^.<\n]{5,80})',
        r'empresa\s+de\s+([^.<\n]{5,60})',
        r'dedicad[oa]s?\s+(?:a(?:l)?|en)\s+([^.<\n]{5,60})',
        r'especialistas?\s+en\s+([^.<\n]{5,60})',
        r'l[íi]deres?\s+en\s+([^.<\n]{5,60})',
        r'nos\s+dedicamos\s+(?:a(?:l)?)?\s+([^.<\n]{5,60})',
        r'servicios?\s+de\s+([^.<\n]{5,50})',
        r'soluciones?\s+(?:de|en|para)\s+([^.<\n]{5,50})'
    ]
    
    for pattern in activity_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            activity = clean_text(match.group(1))
            if 5 < len(activity) < 100:
                business_activity = activity
                break
    
    # Inferir de keywords
    if not business_activity:
        keywords_map = {
            'monitoreo': 'Monitoreo de alarmas',
            'alarma': 'Sistemas de alarmas',
            'seguridad': 'Seguridad y vigilancia',
            'rastreo': 'Rastreo satelital',
            'cámaras': 'CCTV y videovigilancia',
            'cctv': 'CCTV y videovigilancia',
            'software': 'Desarrollo de software',
            'tecnología': 'Tecnología',
            'redes': 'Networking y redes'
        }
        
        lower_text = search_text.lower()
        for keyword, activity in keywords_map.items():
            if keyword in lower_text:
                business_activity = activity
                break
    
    regex_extract['business_activity'] = business_activity
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. SERVICIOS
    # ═══════════════════════════════════════════════════════════════════
    services = set()
    
    # Keywords de servicios comunes
    common_services = [
        'Monitoreo 24/7', 'Monitoreo de alarmas', 'Alarmas residenciales', 'Alarmas comerciales',
        'CCTV', 'Cámaras de seguridad', 'Videovigilancia', 'Rastreo vehicular', 'GPS',
        'Control de acceso', 'Cercos eléctricos', 'Seguridad electrónica',
        'INFRAESTRUCTURA', 'WIRELESS', 'NETWORKING', 'TELEFONÍA', 'DOMÓTICA',
        'SOFTWARE', 'HARDWARE', 'CLOUD', 'CONECTIVIDAD', 'FIBRA ÓPTICA', 'UPS'
    ]
    
    lower_content = search_text.lower()
    for svc in common_services:
        if svc.lower() in lower_content:
            services.add(svc)
    
    # Buscar en menú de navegación
    nav_links = re.findall(r'<a[^>]*>([^<]{3,40})</a>', all_content, re.IGNORECASE)
    service_keywords = ['servicio', 'solución', 'producto', 'monitoreo', 'alarma', 'cámara', 'rastreo', 'seguridad']
    
    for link in nav_links:
        text = clean_text(link)
        if 3 < len(text) < 40:
            lower_text = text.lower()
            if any(kw in lower_text for kw in service_keywords):
                services.add(text)
    
    regex_extract['servicios'] = list(services)[:10]
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. EMAILS
    # ═══════════════════════════════════════════════════════════════════
    emails = set()
    
    # Desde href="mailto:"
    mailto_pattern = re.findall(r'href=["\']mailto:([^"\'?]+)', all_content, re.IGNORECASE)
    for email in mailto_pattern:
        email = email.lower().strip()
        if '@' in email and 'example' not in email and len(email) < 50:
            emails.add(email)
    
    # Desde texto
    email_text_pattern = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_content)
    for email in email_text_pattern:
        email = email.lower()
        if not any(x in email for x in ['example', 'sentry', 'wix', '.png', '.jpg', 'website.com']):
            if len(email) < 50:
                emails.add(email)
    
    regex_extract['emails'] = list(emails)[:5]
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. TELÉFONOS
    # ═══════════════════════════════════════════════════════════════════
    phones = set()
    
    # Desde href="tel:"
    tel_pattern = re.findall(r'href=["\']tel:([^"\']+)', all_content, re.IGNORECASE)
    for phone in tel_pattern:
        phone = phone.strip()
        if len(re.sub(r'\D', '', phone)) >= 8:
            phones.add(phone)
    
    # Formato argentino y otros
    phone_patterns = [
        r'\(0\d{2,4}\)\s*\d{3,4}[\s.-]?\d{3,4}',
        r'\+54\s*9?\s*\d{2,4}\s*\d{3,4}\s*\d{3,4}',
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}',
        r'\b\d{4}[\s.-]\d{4}\b'
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, all_content)
        for phone in matches:
            if len(re.sub(r'\D', '', phone)) >= 8:
                phones.add(phone)
    
    regex_extract['phones'] = list(phones)[:5]
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. WHATSAPP
    # ═══════════════════════════════════════════════════════════════════
    wa_match = re.search(r'wa\.me/(\+?\d{10,15})|api\.whatsapp\.com/send\?phone=(\d{10,15})', all_content, re.IGNORECASE)
    regex_extract['whatsapp'] = (wa_match.group(1) or wa_match.group(2)) if wa_match else ''
    
    # ═══════════════════════════════════════════════════════════════════
    # 8. REDES SOCIALES
    # ═══════════════════════════════════════════════════════════════════
    
    # INSTAGRAM
    instagram_url = ""
    ig_patterns = [
        r'href=["\']?(https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._]+/?)["\'\s>]',
        r'instagram\.com/([a-zA-Z0-9._]+)'
    ]
    
    for pattern in ig_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            url = match.group(1)
            if '/p/' not in url and '/reel/' not in url and '/explore/' not in url:
                if not url.startswith('http'):
                    url = f"https://www.instagram.com/{url}/"
                if not url.endswith('/'):
                    url += '/'
                instagram_url = url.split('?')[0]
                break
    
    regex_extract['instagram'] = instagram_url
    
    # FACEBOOK
    facebook_url = ""
    fb_patterns = [
        r'href=["\']?(https?://(?:www\.)?facebook\.com/[^"\'\s>]+)["\'\s>]',
        r'facebook\.com/([a-zA-Z0-9./_-]+)'
    ]
    
    for pattern in fb_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            url = match.group(1)
            if '/posts/' not in url and '/sharer' not in url:
                if not url.startswith('http'):
                    url = f"https://www.facebook.com/{url}"
                facebook_url = url.split('?')[0]
                break
    
    regex_extract['facebook'] = facebook_url
    
    # LINKEDIN
    linkedin_url = ""
    li_match = re.search(r'https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9_-]+', all_content, re.IGNORECASE)
    if li_match:
        linkedin_url = li_match.group(0).split('?')[0]
    
    regex_extract['linkedin'] = linkedin_url
    
    # ═══════════════════════════════════════════════════════════════════
    # 9. DIRECCIÓN Y UBICACIÓN
    # ═══════════════════════════════════════════════════════════════════
    address = ""
    city = ""
    province = ""
    
    # Buscar dirección
    address_patterns = [
        r'(?:dirección|direccion|domicilio|ubicación|ubicacion)[:\s]*([^<\n]{10,100})',
        r'(?:calle|av\.|avenida|bv\.|boulevard)\s+[^<\n]{5,80}',
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            addr = clean_text(match.group(1) if match.lastindex else match.group(0))
            if 10 < len(addr) < 150:
                address = addr
                break
    
    # Provincias argentinas
    provincias = [
        'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba', 'Corrientes',
        'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja', 'Mendoza', 'Misiones',
        'Neuquén', 'Río Negro', 'Salta', 'San Juan', 'San Luis', 'Santa Cruz', 'Santa Fe',
        'Santiago del Estero', 'Tierra del Fuego', 'Tucumán'
    ]
    
    for prov in provincias:
        if prov.lower() in search_text.lower():
            province = prov
            break
    
    regex_extract['address'] = address
    regex_extract['city'] = city
    regex_extract['province'] = province
    
    # ═══════════════════════════════════════════════════════════════════
    # 10. HORARIOS
    # ═══════════════════════════════════════════════════════════════════
    horarios = ""
    horario_patterns = [
        r'(?:horario|atención|atencion)[s]?[:\s]*([^<\n]{10,100})',
        r'(?:lunes\s+a\s+viernes|lun\s*-\s*vie)[:\s]*([^<\n]{5,50})',
        r'\d{1,2}:\d{2}\s*(?:a|hs|-)\s*\d{1,2}:\d{2}\s*(?:hs)?'
    ]
    
    for pattern in horario_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            horarios = clean_text(match.group(1) if match.lastindex else match.group(0))
            break
    
    regex_extract['horarios'] = horarios
    
    logger.info(f"[REGEX] Emails: {len(regex_extract['emails'])}, Phones: {len(regex_extract['phones'])}, Servicios: {len(regex_extract['servicios'])}")
    
    return regex_extract


async def parse_with_gpt(web_content: str, website: str, regex_data: dict, tavily_answer: str) -> dict:
    """
    Usa GPT-4o para extraer datos estructurados.
    """
    try:
        if not OPENAI_API_KEY:
            return {}
        
        logger.info("[GPT] Procesando con GPT-4o...")
        
        # Preparar datos regex para el prompt
        regex_emails = regex_data.get('emails', [])
        regex_phones = regex_data.get('phones', [])
        
        prompt = f"""Sos un experto extrayendo datos de sitios web empresariales.

Sitio: {website}

═══════════════════════════════════════════════════════════════════
DATOS YA ENCONTRADOS (USAR DIRECTAMENTE SI SON VÁLIDOS):
═══════════════════════════════════════════════════════════════════
- Nombre empresa: {regex_data.get('business_name', '')}
- Descripción: {regex_data.get('business_description', '')}
- Actividad: {regex_data.get('business_activity', '')}
- Emails: {regex_emails}
- Teléfonos: {regex_phones}
- WhatsApp: {regex_data.get('whatsapp', '')}
- LinkedIn: {regex_data.get('linkedin', '')}
- Instagram: {regex_data.get('instagram', '')}
- Facebook: {regex_data.get('facebook', '')}
- Dirección: {regex_data.get('address', '')}
- Provincia: {regex_data.get('province', '')}
- Horarios: {regex_data.get('horarios', '')}
- DESCRIPCIÓN TAVILY: {tavily_answer}

═══════════════════════════════════════════════════════════════════
CONTENIDO DEL SITIO (primeros 12000 chars):
═══════════════════════════════════════════════════════════════════
{web_content[:12000]}

═══════════════════════════════════════════════════════════════════
INSTRUCCIONES:
═══════════════════════════════════════════════════════════════════
1. USAR los datos ya encontrados arriba si son válidos
2. COMPLETAR solo los campos que faltan buscando en el contenido
3. Si hay DESCRIPCIÓN TAVILY → usarla como business_description
4. Si un dato no existe → "No encontrado"
5. NUNCA inventar datos

RESPONDER SOLO JSON (sin ```, sin markdown):

{{
  "business_name": "",
  "business_activity": "",
  "business_description": "",
  "services": [],
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
  "country": "Argentina",
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
                    return {}
                
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                content = content.strip()
                
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
    Prioridad: GPT > Regex > Tavily
    """
    resultado = gpt_data.copy() if gpt_data else {}
    
    # Descripción - usar Tavily si GPT no encontró buena
    desc_gpt = resultado.get('business_description', '')
    es_mala = not desc_gpt or desc_gpt == 'No encontrado' or len(desc_gpt) < 50
    
    if es_mala and tavily_answer:
        resultado['business_description'] = tavily_answer
    
    # Servicios
    if not resultado.get('services') and regex_data.get('servicios'):
        resultado['services'] = regex_data['servicios']
    
    # Email
    if not resultado.get('email_principal') or resultado.get('email_principal') == 'No encontrado':
        if regex_data.get('emails'):
            resultado['email_principal'] = regex_data['emails'][0]
            if len(regex_data['emails']) > 1:
                resultado['emails_adicionales'] = regex_data['emails'][1:]
    
    # Teléfono
    if not resultado.get('phone_empresa') or resultado.get('phone_empresa') == 'No encontrado':
        if regex_data.get('phones'):
            resultado['phone_empresa'] = regex_data['phones'][0]
            if len(regex_data['phones']) > 1:
                resultado['phones_adicionales'] = regex_data['phones'][1:]
    
    # WhatsApp
    if not resultado.get('whatsapp_number') and regex_data.get('whatsapp'):
        resultado['whatsapp_number'] = regex_data['whatsapp']
    
    # Redes sociales
    if not resultado.get('linkedin_empresa') and regex_data.get('linkedin'):
        resultado['linkedin_empresa'] = regex_data['linkedin']
    if not resultado.get('instagram_empresa') and regex_data.get('instagram'):
        resultado['instagram_empresa'] = regex_data['instagram']
    if not resultado.get('facebook_empresa') and regex_data.get('facebook'):
        resultado['facebook_empresa'] = regex_data['facebook']
    
    # Ubicación
    if not resultado.get('address') and regex_data.get('address'):
        resultado['address'] = regex_data['address']
    if not resultado.get('province') and regex_data.get('province'):
        resultado['province'] = regex_data['province']
    if not resultado.get('horarios') and regex_data.get('horarios'):
        resultado['horarios'] = regex_data['horarios']
    
    # Business name y activity
    if not resultado.get('business_name') and regex_data.get('business_name'):
        resultado['business_name'] = regex_data['business_name']
    if not resultado.get('business_activity') and regex_data.get('business_activity'):
        resultado['business_activity'] = regex_data['business_activity']
    
    # services_text
    services = resultado.get('services', [])
    if isinstance(services, list) and len(services) > 0:
        resultado['services_text'] = ', '.join([s for s in services if s and s != 'No encontrado'])
    else:
        resultado['services_text'] = 'No encontrado'
    
    return resultado


async def extract_web_data(website: str) -> dict:
    """
    Pipeline completo de extracción web.
    Flujo: Tavily → HTTP Fetch → Regex → GPT-4o → Merge
    """
    logger.info(f"[EXTRACTOR] ========== Iniciando: {website} ==========")
    
    website_clean = clean_url(website)
    website_full = f"https://{website_clean}"
    
    # 1. Tavily para búsqueda inicial y descripción
    tavily_query = f'"{website_clean}" contacto dirección teléfono email Argentina'
    tavily_data = await search_with_tavily(tavily_query)
    
    tavily_answer = tavily_data.get("answer", "")
    tavily_raw = ""
    
    for r in tavily_data.get("results", []):
        if r.get('raw_content'):
            tavily_raw += r['raw_content'][:3000] + "\n"
    
    logger.info(f"[TAVILY] ✓ {len(tavily_raw)} caracteres extraídos")
    
    # 2. HTTP Fetch directo (como hace n8n)
    html_content = await fetch_html_direct(website_full)
    
    # 3. Jina como backup si HTTP falló o trajo poco
    jina_content = ""
    if len(html_content) < 5000:
        jina_content = await fetch_with_jina(website_clean)
    
    # 4. Combinar todo el contenido
    all_content = ""
    if html_content:
        all_content += html_content + "\n\n"
    if jina_content:
        all_content += jina_content + "\n\n"
    if tavily_raw:
        all_content += tavily_raw
    
    if len(all_content) > 25000:
        all_content = all_content[:25000]
    
    if not all_content:
        logger.warning(f"[EXTRACTOR] No se pudo obtener contenido de {website}")
        return {
            "business_name": "No encontrado",
            "business_description": tavily_answer or "No encontrado",
            "website": website_full,
            "extraction_status": "failed"
        }
    
    logger.info(f"[EXTRACTOR] Contenido total: {len(all_content)} chars")
    
    # 5. Extracción con regex (Extractor_v8)
    regex_data = extract_with_regex(all_content, website_clean)
    
    # 6. Parsing con GPT-4o
    gpt_data = await parse_with_gpt(all_content, website_clean, regex_data, tavily_answer)
    
    # 7. Merge de resultados
    final_data = merge_results(gpt_data, regex_data, tavily_answer)
    
    # Metadatos
    final_data["website"] = website_full
    final_data["extraction_status"] = "success"
    final_data["source"] = "tavily_http_regex_gpt4o"
    
    logger.info(f"[EXTRACTOR] ========== Completado ==========")
    
    return final_data
