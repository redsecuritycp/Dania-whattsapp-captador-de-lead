"""
Servicio de extracción de datos web - RÉPLICA FIEL de n8n
Pipeline: Jina AI (primero) → Tavily → HTTP Fetch → Regex (Extractor_v8) → GPT-4o → Merge
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


async def fetch_with_jina(website: str) -> str:
    """
    Extrae contenido web usando Jina AI Reader.
    MÉTODO PRINCIPAL (como en n8n Tool_Extractor_Web_INTELIGENTE).
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


async def fetch_html_direct(url: str) -> str:
    """
    Fetch HTML directo como backup si Jina falla.
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
    Réplica COMPLETA del Extractor_v8 de n8n.
    """
    regex_extract = {
        'emails': [],
        'phones': [],
        'whatsapp': '',
        'linkedin': '',
        'instagram': '',
        'facebook': '',
        'twitter': '',
        'youtube': '',
        'address': '',
        'city': '',
        'province': '',
        'horarios': '',
        'cuit_cuil': '',
        'razon_social': '',
        'google_maps_url': '',
        'servicios': [],
        'business_name': '',
        'business_activity': '',
        'business_description': ''
    }
    
    if not all_content:
        return regex_extract
    
    search_text = all_content.lower()
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. EMAILS (filtrar inválidos)
    # ═══════════════════════════════════════════════════════════════════
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_matches = re.findall(email_pattern, all_content, re.IGNORECASE)
    
    invalid_patterns = ['example', 'test', 'sentry', 'wix', 'wordpress', 
                       'noreply', 'no-reply', '.png', '.jpg', '.gif', '.webp', '.svg']
    
    valid_emails = []
    seen = set()
    for email in email_matches:
        email_lower = email.lower()
        if email_lower not in seen and not any(inv in email_lower for inv in invalid_patterns):
            valid_emails.append(email)
            seen.add(email_lower)
    
    regex_extract['emails'] = valid_emails[:5]
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. TELÉFONOS
    # ═══════════════════════════════════════════════════════════════════
    phone_patterns = [
        r'\+54\s*9?\s*\d{2,4}\s*\d{3,4}\s*\d{4}',
        r'\+54\s*\d{10,12}',
        r'\(\d{2,5}\)\s*\d{3,4}[\s-]?\d{4}',
        r'\d{4}[\s-]\d{4}',
        r'\d{10,12}'
    ]
    
    phones = []
    seen_phones = set()
    for pattern in phone_patterns:
        matches = re.findall(pattern, all_content)
        for match in matches:
            cleaned = re.sub(r'[^\d+]', '', match)
            if len(cleaned) >= 8 and cleaned not in seen_phones:
                phones.append(match.strip())
                seen_phones.add(cleaned)
    
    regex_extract['phones'] = phones[:5]
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. WHATSAPP
    # ═══════════════════════════════════════════════════════════════════
    wa_patterns = [
        r'wa\.me/(\d+)',
        r'whatsapp[:\s]*\+?(\d[\d\s-]{8,})',
        r'api\.whatsapp\.com/send\?phone=(\d+)'
    ]
    
    for pattern in wa_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            wa_num = re.sub(r'[^\d]', '', match.group(1))
            if len(wa_num) >= 10:
                regex_extract['whatsapp'] = '+' + wa_num
                break
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. REDES SOCIALES
    # ═══════════════════════════════════════════════════════════════════
    
    # Instagram
    ig_match = re.search(r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)', all_content, re.IGNORECASE)
    if ig_match and ig_match.group(1) not in ['p', 'reel', 'stories', 'explore']:
        regex_extract['instagram'] = f"https://instagram.com/{ig_match.group(1)}"
    
    # Facebook
    fb_match = re.search(r'(?:https?://)?(?:www\.)?facebook\.com/([a-zA-Z0-9.]+)', all_content, re.IGNORECASE)
    if fb_match and fb_match.group(1) not in ['sharer', 'share', 'dialog', 'plugins']:
        regex_extract['facebook'] = f"https://facebook.com/{fb_match.group(1)}"
    
    # LinkedIn empresa
    li_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)', all_content, re.IGNORECASE)
    if li_match:
        regex_extract['linkedin'] = f"https://linkedin.com/company/{li_match.group(1)}"
    
    # Twitter/X
    tw_match = re.search(r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9_]+)', all_content, re.IGNORECASE)
    if tw_match and tw_match.group(1) not in ['share', 'intent', 'home']:
        regex_extract['twitter'] = f"https://twitter.com/{tw_match.group(1)}"
    
    # YouTube
    yt_match = re.search(r'(?:https?://)?(?:www\.)?youtube\.com/(?:channel/|c/|@)([a-zA-Z0-9_-]+)', all_content, re.IGNORECASE)
    if yt_match:
        regex_extract['youtube'] = f"https://youtube.com/{yt_match.group(1)}"
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. GOOGLE MAPS
    # ═══════════════════════════════════════════════════════════════════
    maps_match = re.search(r'https?://(?:www\.)?google\.com/maps[^\s"<>]+', all_content, re.IGNORECASE)
    if maps_match:
        regex_extract['google_maps_url'] = maps_match.group(0).split('"')[0].split("'")[0]
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. CUIT/CUIL (Argentina)
    # ═══════════════════════════════════════════════════════════════════
    cuit_match = re.search(r'(?:CUIT|CUIL)[:\s]*(\d{2}[-\s]?\d{8}[-\s]?\d{1})', all_content, re.IGNORECASE)
    if cuit_match:
        regex_extract['cuit_cuil'] = cuit_match.group(1)
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. SERVICIOS
    # ═══════════════════════════════════════════════════════════════════
    servicios = []
    service_patterns = [
        r'(?:servicios|ofrecemos|brindamos)[:\s]*([^.]{20,200})',
        r'(?:nuestros servicios|qué hacemos)[:\s]*([^.]{20,200})'
    ]
    
    for pattern in service_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            if ',' in text:
                servicios.extend([s.strip().capitalize() for s in text.split(',') if len(s.strip()) > 3])
            else:
                servicios.append(text.capitalize())
    
    regex_extract['servicios'] = servicios[:10]
    
    # ═══════════════════════════════════════════════════════════════════
    # 8. DIRECCIÓN Y UBICACIÓN
    # ═══════════════════════════════════════════════════════════════════
    address_patterns = [
        r'(?:dirección|direccion|domicilio|ubicación|ubicacion)[:\s]*([^<\n]{10,100})',
        r'(?:calle|av\.|avenida|bv\.|boulevard)\s+[^<\n]{5,80}',
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            addr = clean_text(match.group(1) if match.lastindex else match.group(0))
            if 10 < len(addr) < 150:
                regex_extract['address'] = addr
                break
    
    # Provincias argentinas
    provincias = [
        'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba', 'Corrientes',
        'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja', 'Mendoza', 'Misiones',
        'Neuquén', 'Río Negro', 'Salta', 'San Juan', 'San Luis', 'Santa Cruz', 'Santa Fe',
        'Santiago del Estero', 'Tierra del Fuego', 'Tucumán'
    ]
    
    for prov in provincias:
        if prov.lower() in search_text:
            regex_extract['province'] = prov
            break
    
    # ═══════════════════════════════════════════════════════════════════
    # 9. HORARIOS
    # ═══════════════════════════════════════════════════════════════════
    horario_patterns = [
        r'(?:horario|atención|atencion)[s]?[:\s]*([^<\n]{10,100})',
        r'(?:lunes\s+a\s+viernes|lun\s*-\s*vie)[:\s]*([^<\n]{5,50})',
        r'\d{1,2}:\d{2}\s*(?:a|hs|-)\s*\d{1,2}:\d{2}\s*(?:hs)?'
    ]
    
    for pattern in horario_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            regex_extract['horarios'] = clean_text(match.group(1) if match.lastindex else match.group(0))
            break
    
    # ═══════════════════════════════════════════════════════════════════
    # 10. BUSINESS ACTIVITY (nuevo - como n8n)
    # ═══════════════════════════════════════════════════════════════════
    activity_patterns = [
        r'(?:somos|empresa de|dedicados a|especializados en)\s+([^.]{10,100})',
        r'(?:líder en|lider en|expertos en)\s+([^.]{10,80})'
    ]
    
    for pattern in activity_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            activity = match.group(1).strip().capitalize()
            if len(activity) > 10:
                regex_extract['business_activity'] = activity
                break
    
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
- Twitter: {regex_data.get('twitter', '')}
- YouTube: {regex_data.get('youtube', '')}
- Dirección: {regex_data.get('address', '')}
- Provincia: {regex_data.get('province', '')}
- Horarios: {regex_data.get('horarios', '')}
- CUIT/CUIL: {regex_data.get('cuit_cuil', '')}
- Google Maps: {regex_data.get('google_maps_url', '')}
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
  "twitter": "",
  "youtube": "",
  "google_maps_url": "",
  "address": "",
  "city": "",
  "province": "",
  "country": "Argentina",
  "horarios": "",
  "cuit_cuil": "",
  "razon_social": ""
}}"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
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
    Merge de resultados.
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
    if not resultado.get('twitter') and regex_data.get('twitter'):
        resultado['twitter'] = regex_data['twitter']
    if not resultado.get('youtube') and regex_data.get('youtube'):
        resultado['youtube'] = regex_data['youtube']
    if not resultado.get('google_maps_url') and regex_data.get('google_maps_url'):
        resultado['google_maps_url'] = regex_data['google_maps_url']
    
    # Ubicación
    if not resultado.get('address') and regex_data.get('address'):
        resultado['address'] = regex_data['address']
    if not resultado.get('province') and regex_data.get('province'):
        resultado['province'] = regex_data['province']
    if not resultado.get('horarios') and regex_data.get('horarios'):
        resultado['horarios'] = regex_data['horarios']
    
    # CUIT/CUIL
    if not resultado.get('cuit_cuil') and regex_data.get('cuit_cuil'):
        resultado['cuit_cuil'] = regex_data['cuit_cuil']
    
    # Business activity
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
    Orden corregido: Jina PRIMERO → Tavily → HTTP → Regex → GPT-4o → Merge
    """
    logger.info(f"[EXTRACTOR] ========== Iniciando: {website} ==========")
    
    website_clean = clean_url(website)
    website_full = f"https://{website_clean}"
    
    # 1. JINA AI PRIMERO (como n8n)
    jina_content = await fetch_with_jina(website_clean)
    
    # 2. Si Jina falló o trajo poco, intentar HTTP directo
    html_content = ""
    if len(jina_content) < 500:
        html_content = await fetch_html_direct(website_full)
    
    # 3. Tavily para búsqueda complementaria y descripción
    tavily_query = f'"{website_clean}" contacto dirección teléfono email Argentina'
    tavily_data = await search_with_tavily(tavily_query)
    
    tavily_answer = tavily_data.get("answer", "")
    tavily_raw = ""
    
    for r in tavily_data.get("results", []):
        if r.get('raw_content'):
            tavily_raw += r['raw_content'][:3000] + "\n"
    
    # 4. Combinar todo el contenido (prioridad: Jina > HTTP > Tavily)
    all_content = ""
    if jina_content:
        all_content += "=== SITIO WEB (JINA) ===\n" + jina_content + "\n\n"
    if html_content:
        all_content += "=== SITIO WEB (HTTP) ===\n" + html_content + "\n\n"
    if tavily_raw:
        all_content += "=== DATOS ADICIONALES (TAVILY) ===\n" + tavily_raw
    
    if len(all_content) > 20000:
        all_content = all_content[:20000]
    
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
    final_data["source"] = "jina_tavily_regex_gpt4o"
    
    logger.info(f"[EXTRACTOR] ========== Completado ==========")
    
    return final_data
