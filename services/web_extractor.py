"""
Servicio de extracción de datos web - RÉPLICA FIEL de n8n
Pipeline: Firecrawl (primero) → Jina AI (backup) → Tavily → Regex → GPT-4o → Merge
"""
import os
import re
import httpx
import json
import logging
from typing import Optional
from urllib.parse import urlparse

from config import TAVILY_API_KEY, OPENAI_API_KEY, JINA_API_KEY, FIRECRAWL_API_KEY
from services.social_research import (
    buscar_linkedin_en_web,
    buscar_linkedin_por_email
)

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30.0


def clean_url(url: str) -> str:
    """Limpia y normaliza una URL."""
    url = url.strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url


async def fetch_with_firecrawl(website: str) -> str:
    """
    Extrae contenido web usando Firecrawl (mejor JS rendering).
    MÉTODO PRINCIPAL - ejecuta JavaScript completo como navegador real.
    """
    if not FIRECRAWL_API_KEY:
        logger.warning("[FIRECRAWL] API key no configurada")
        return ""
    
    try:
        url = f"https://{website}" if not website.startswith("http") else website
        
        logger.info(f"[FIRECRAWL] Extrayendo: {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["markdown", "links", "html"],
                    "onlyMainContent": False,
                    "includeTags": ["a", "footer", "header", "nav", "div", "span", "p"],
                    "waitFor": 5000,
                    "timeout": 60000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    logger.warning(f"[FIRECRAWL] Extracción fallida: {data.get('error', 'Unknown')}")
                    return ""
                
                result_data = data.get("data", {})
                content = result_data.get("markdown", "")
                links = result_data.get("links", [])
                
                # Agregar links al final (como hace Jina con X-With-Links-Summary)
                if links:
                    content += "\n\n--- Links encontrados ---\n"
                    for link in links[:50]:  # Limitar a 50 links
                        content += f"- {link}\n"
                
                logger.info(f"[FIRECRAWL] ✓ {len(content)} caracteres extraídos, {len(links)} links")
                return content
            else:
                logger.warning(f"[FIRECRAWL] Error {response.status_code}: {response.text[:200]}")
                return ""
                
    except Exception as e:
        logger.error(f"[FIRECRAWL] Error: {e}")
        return ""


async def fetch_with_jina(website: str) -> str:
    """
    Extrae contenido web usando Jina AI Reader.
    MÉTODO BACKUP si Firecrawl falla.
    """
    try:
        url = f"https://r.jina.ai/{website}"
        
        headers = {
            "Accept": "text/plain",
            "X-With-Links-Summary": "true"
        }
        
        if JINA_API_KEY:
            headers["Authorization"] = f"Bearer {JINA_API_KEY}"
        
        logger.info(f"[JINA] Extrayendo (backup): {website}")
        
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
    Fetch HTML directo como último recurso.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.text[:50000]
            return ""
    except Exception as e:
        logger.error(f"[HTTP] Error: {e}")
        return ""


async def fetch_with_tavily(website: str) -> str:
    """Fallback usando Tavily cuando otros métodos fallan por DNS."""
    if not TAVILY_API_KEY:
        return ""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": f"site:{website} empresa servicios contacto nosotros",
                    "search_depth": "advanced",
                    "include_raw_content": True,
                    "max_results": 5
                }
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                content_parts = []
                for r in results:
                    if r.get("raw_content"):
                        content_parts.append(r["raw_content"])
                    elif r.get("content"):
                        content_parts.append(r["content"])
                return "\n\n".join(content_parts)
    except Exception as e:
        logger.error(f"[TAVILY] Error: {e}")
    return ""


async def search_with_tavily(query: str) -> dict:
    """
    Búsqueda web con Tavily para datos complementarios.
    """
    if not TAVILY_API_KEY:
        return {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5,
                    "include_answer": True,
                    "include_raw_content": True
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"[TAVILY] Error: {e}")
        return {}


def extract_with_regex(all_content: str) -> dict:
    """
    Extracción con regex - Extractor v8 de n8n.
    """
    regex_extract = {
        'emails': [],
        'phones': [],
        'whatsapp': '',
        'instagram': '',
        'facebook': '',
        'linkedin': '',
        'twitter': '',
        'youtube': '',
        'google_maps_url': '',
        'address': '',
        'province': '',
        'horarios': '',
        'cuit_cuil': '',
        'business_activity': '',
        'servicios': []
    }
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. EMAILS
    # ═══════════════════════════════════════════════════════════════════
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails_found = re.findall(email_pattern, all_content)
    
    # Filtrar emails basura
    emails_filtered = []
    for email in emails_found:
        email_lower = email.lower()
        if not any(x in email_lower for x in ['example', 'sentry', 'wixpress', '.png', '.jpg', 'website.com', 'domain.com']):
            emails_filtered.append(email_lower)
    
    regex_extract['emails'] = list(set(emails_filtered))[:5]
    logger.info(f"[REGEX] Emails encontrados: {regex_extract['emails']}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. TELÉFONOS
    # ═══════════════════════════════════════════════════════════════════
    phone_patterns = [
        r'href=["\']tel:([^"\']+)',
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}',
        r'\(\d{2,5}\)[\s.-]?\d{3,4}[\s.-]?\d{3,4}',
        r'\b\d{4}[\s.-]\d{4}\b'
    ]
    
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        for m in matches:
            phone = re.sub(r'[^\d+]', '', m) if isinstance(m, str) else m
            if len(re.sub(r'\D', '', str(phone))) >= 7:
                phones.append(m.strip() if isinstance(m, str) else m)
    
    regex_extract['phones'] = list(set(phones))[:5]
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. WHATSAPP - Búsqueda genérica multipaís
    # ═══════════════════════════════════════════════════════════════════
    # DEBUG: Ver si el contenido tiene telephone
    if 'telephone' in all_content.lower():
        logger.info(f"[REGEX] ✓ Contenido tiene 'telephone'")
    else:
        logger.info(f"[REGEX] ✗ Contenido NO tiene 'telephone'")
    
    wa_patterns = [
        r'wa\.me/(\d+)',
        r'api\.whatsapp\.com/send\?phone=(\d+)',
        r'href="whatsapp://send\?phone=(\d+)"',
        r'data-phone="(\d+)"',
        r'data-whatsapp="(\d+)"',
        r'"telephone"[:\s]*"(\d{10,15})"',
        r'"phone"[:\s]*"(\d{10,15})"',
        r"'phone'[:\s]*'(\d{10,15})'",
        r'(?:whatsapp|wsp|wa)[:\s]*\+?(\d[\d\s-]{9,})',
    ]
    
    for pattern in wa_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            wa_num = re.sub(r'[^\d]', '', match.group(1))
            if len(wa_num) >= 10 and len(wa_num) <= 15:
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
    
    # YouTube - solo URLs completas verificables
    regex_extract['youtube'] = ''
    yt_pattern = r'href=["\']?(https?://(?:www\.)?youtube\.com/(?:channel|c|user|@)[^"\'>\s]+)["\']?'
    yt_match = re.search(yt_pattern, all_content, re.IGNORECASE)
    if yt_match:
        yt_url = yt_match.group(1).split('?')[0].split('#')[0]
        if '/watch' not in yt_url and '/embed' not in yt_url:
            regex_extract['youtube'] = yt_url
    
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
    # 7. DIRECCIONES (Argentina)
    # ═══════════════════════════════════════════════════════════════════
    direccion_patterns = [
        r'(?:Av\.?|Avenida|Calle|Bv\.?|Boulevard)\s+[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+\s+\d{1,5}',
        r'\d{1,5}\s+[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+(?:,\s*[A-Za-z\s]+)?'
    ]
    
    for pattern in direccion_patterns:
        match = re.search(pattern, all_content)
        if match and len(match.group(0)) > 10:
            regex_extract['address'] = match.group(0).strip()
            break
    
    # Provincias argentinas
    provincias = ['Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán', 'Entre Ríos', 
                  'Salta', 'Misiones', 'Chaco', 'Corrientes', 'Santiago del Estero', 'San Juan',
                  'Jujuy', 'Río Negro', 'Neuquén', 'Formosa', 'Chubut', 'San Luis', 'Catamarca',
                  'La Rioja', 'La Pampa', 'Santa Cruz', 'Tierra del Fuego', 'CABA']
    
    for prov in provincias:
        if prov.lower() in all_content.lower():
            regex_extract['province'] = prov
            break
    
    # ═══════════════════════════════════════════════════════════════════
    # 8. HORARIOS
    # ═══════════════════════════════════════════════════════════════════
    horarios_patterns = [
        r'(?:Lun|Mar|Mié|Jue|Vie|Sáb|Dom|L|M|X|J|V|S|D)[a-z]*[\s\-a]+(?:Lun|Mar|Mié|Jue|Vie|Sáb|Dom|L|M|X|J|V|S|D)[a-z]*[:\s]+\d{1,2}[:\.]?\d{0,2}\s*(?:hs|hrs|am|pm)?\s*[\-a]+\s*\d{1,2}[:\.]?\d{0,2}\s*(?:hs|hrs|am|pm)?',
        r'\d{1,2}:\d{2}\s*(?:hs|hrs|am|pm)?\s*[\-a]+\s*\d{1,2}:\d{2}\s*(?:hs|hrs|am|pm)?'
    ]
    
    for pattern in horarios_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            regex_extract['horarios'] = match.group(0).strip()
            break
    
    # ═══════════════════════════════════════════════════════════════════
    # 9. SERVICIOS (Keywords)
    # ═══════════════════════════════════════════════════════════════════
    servicios_keywords = [
        'INFRAESTRUCTURA', 'WIRELESS', 'ISP', 'SEGURIDAD', 'NETWORKING',
        'TELEFONÍA', 'TELEFONIA', 'IP TELEPHONY', 'SMART HOME', 'DOMÓTICA',
        'SOFTWARE', 'HARDWARE', 'CLOUD', 'CONECTIVIDAD', 'REDES',
        'CÁMARAS', 'CAMARAS', 'CCTV', 'ACCESS POINT', 'ROUTER', 'SWITCH',
        'FIBRA ÓPTICA', 'FIBRA OPTICA', 'UPS', 'ENERGÍA', 'ENERGIA',
        'MONITOREO', 'ALARMAS', 'RASTREO', 'GPS', 'VIGILANCIA'
    ]
    
    content_upper = all_content.upper()
    servicios_encontrados = []
    
    for keyword in servicios_keywords:
        if keyword in content_upper:
            servicios_encontrados.append(keyword.title())
    
    regex_extract['servicios'] = list(set(servicios_encontrados))
    
    return regex_extract


async def extract_with_gpt(all_content: str, website: str) -> dict:
    """
    Usa GPT-4o-mini para extraer datos estructurados.
    """
    if not OPENAI_API_KEY:
        return {}
    
    prompt = f"""Extraé los siguientes datos del contenido de este sitio web ({website}).
Respondé SOLO con JSON válido, sin explicaciones.
Si no encontrás un dato, usá "No encontrado".

DATOS A EXTRAER:
- business_name: Nombre de la empresa
- business_activity: Actividad/rubro principal
- business_model: Modelo de negocio (B2B, B2C, SaaS, Ecommerce, 
  Servicios profesionales, Retail, Mayorista, Franquicia, 
  Suscripción, Marketplace, o el que corresponda)
- business_description: Descripción breve (máx 200 chars)
- services: Lista de servicios/productos principales
- email_principal: Email de contacto principal
- phone_empresa: Teléfono principal
- whatsapp_empresa: Número WhatsApp de la empresa (buscar en widgets flotantes, botones de chat, atributos data-settings, data-phone, telephone, o cerca de palabras whatsapp/chat/contacto. Solo números con código país, ej: 5493416469327)
- address: Dirección física
- city: Ciudad
- province: Provincia
- country: País (default Argentina)
- horarios: Horarios de atención
- linkedin_empresa: URL LinkedIn de la empresa
- instagram_empresa: URL Instagram de la empresa  
- facebook_empresa: URL Facebook de la empresa

CONTENIDO DEL SITIO:
{all_content[:15000]}

JSON:"""

    try:
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
                content = data["choices"][0]["message"]["content"]
                
                # Limpiar respuesta
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                logger.info(f"[GPT] ✓ Datos extraídos correctamente")
                return json.loads(content.strip())
            else:
                logger.error(f"[GPT] Error {response.status_code}")
                return {}
                
    except json.JSONDecodeError as e:
        logger.error(f"[GPT] Error parseando JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"[GPT] Error: {e}")
        return {}


def merge_results(gpt_data: dict, regex_data: dict, tavily_answer: str, website: str = "") -> dict:
    """
    Combina resultados de GPT, Regex y Tavily.
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
    
    # Emails - Priorizar email del dominio del sitio
    gpt_email = resultado.get('email_principal', '')
    regex_emails = regex_data.get('emails', [])
    website_domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    
    # Buscar email que coincida con el dominio del sitio
    domain_email = None
    other_emails = []
    for email in regex_emails:
        email_domain = email.split("@")[1] if "@" in email else ""
        if website_domain in email_domain or email_domain in website_domain:
            domain_email = email
            break
        else:
            other_emails.append(email)
    
    # Prioridad: 1) Email del dominio, 2) GPT, 3) Otros emails
    if domain_email:
        resultado['email_principal'] = domain_email
        logger.info(f"[MERGE] Email del dominio: {domain_email}")
    elif not gpt_email or gpt_email == "No encontrado":
        if other_emails:
            resultado['email_principal'] = other_emails[0]
            logger.info(f"[MERGE] Email alternativo: {other_emails[0]}")
    
    # Teléfono
    if not resultado.get('phone_empresa') or resultado.get('phone_empresa') == 'No encontrado':
        if regex_data.get('phones'):
            resultado['phone_empresa'] = regex_data['phones'][0]
            if len(regex_data['phones']) > 1:
                resultado['phones_adicionales'] = regex_data['phones'][1:]
    
    # WhatsApp - de regex
    if not resultado.get('whatsapp_empresa') and regex_data.get('whatsapp'):
        resultado['whatsapp_empresa'] = regex_data['whatsapp']
    
    # Marcar si necesita búsqueda externa (se hace después)
    if not resultado.get('whatsapp_empresa') or \
       resultado.get('whatsapp_empresa') == 'No encontrado':
        resultado['_necesita_wa_externo'] = True
    
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
    
    # ═══════════════════════════════════════════════════════════════
    # Business model - Asegurar que tenga valor
    # ═══════════════════════════════════════════════════════════════
    if not resultado.get('business_model') or \
       resultado.get('business_model') == 'No encontrado':
        # Intentar inferir del business_activity
        activity = resultado.get('business_activity', '').lower()
        if any(x in activity for x in ['software', 'saas', 'plataforma']):
            resultado['business_model'] = 'SaaS'
        elif any(x in activity for x in ['tienda', 'venta', 'retail']):
            resultado['business_model'] = 'Retail'
        elif any(x in activity for x in ['mayorista', 'distribuidor']):
            resultado['business_model'] = 'Mayorista'
        elif any(x in activity for x in ['servicio', 'consultor']):
            resultado['business_model'] = 'Servicios profesionales'
        elif any(x in activity for x in ['fabricación', 'manufactura']):
            resultado['business_model'] = 'Fabricante/Mayorista'
        else:
            resultado['business_model'] = 'No especificado'
    
    # services_text
    services = resultado.get('services', [])
    if isinstance(services, list) and len(services) > 0:
        resultado['services_text'] = ', '.join([s for s in services if s and s != 'No encontrado'])
    else:
        resultado['services_text'] = 'No encontrado'
    
    return resultado


async def extraer_paginas_secundarias(website: str) -> str:
    """
    Extrae contenido de páginas secundarias importantes:
    /contacto, /contact, /nosotros, /about, /equipo, /team, etc.
    """
    paginas = [
        '/contacto', '/contact', '/contactenos', '/contact-us',
        '/nosotros', '/about', '/about-us', '/quienes-somos',
        '/equipo', '/team', '/nuestro-equipo', '/our-team'
    ]
    
    contenido_extra = ""
    paginas_exitosas = 0
    max_paginas = 3  # Limitar para no demorar mucho
    
    for pagina in paginas:
        if paginas_exitosas >= max_paginas:
            break
        
        url = f"https://{website}{pagina}"
        
        try:
            async with httpx.AsyncClient(
                timeout=15.0, 
                follow_redirects=True
            ) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; "
                                      "Win64; x64) AppleWebKit/537.36"
                    }
                )
                
                if response.status_code == 200:
                    texto = response.text
                    # Verificar que no sea redirect a home
                    if len(texto) > 1000 and pagina.strip('/') in texto.lower():
                        contenido_extra += f"\n\n=== PÁGINA: {pagina} ===\n"
                        contenido_extra += texto[:10000]
                        paginas_exitosas += 1
                        logger.info(
                            f"[SECUNDARIA] ✓ {pagina} - "
                            f"{len(texto)} chars"
                        )
        except Exception as e:
            logger.debug(f"[SECUNDARIA] {pagina} no disponible: {e}")
            continue
    
    if paginas_exitosas > 0:
        logger.info(
            f"[SECUNDARIA] Extraídas {paginas_exitosas} páginas extra"
        )
    
    return contenido_extra


async def buscar_whatsapp_externo(
    website: str, 
    empresa: str = ""
) -> str:
    """
    Busca WhatsApp de la empresa en fuentes externas.
    Útil cuando el widget está en JS y no lo capturamos.
    Soporta números internacionales.
    """
    if not TAVILY_API_KEY:
        return ""
    
    # Limpiar dominio
    dominio = website.replace("https://", "").replace(
        "http://", "").replace("www.", "").split("/")[0]
    
    # Queries a intentar (en orden de prioridad)
    queries = [
        f'"{dominio}" teléfono contacto',
        f'"{dominio}" whatsapp',
    ]
    
    # Si tenemos nombre de empresa, agregar query adicional
    if empresa and empresa != "No encontrado":
        queries.append(f'"{empresa}" teléfono whatsapp')
    
    for query in queries:
        logger.info(f"[WA-EXTERNO] Buscando: {query}")
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": 10,
                        "include_answer": False
                    }
                )
                
                if response.status_code != 200:
                    logger.warning(
                        f"[WA-EXTERNO] Tavily error: {response.status_code}"
                    )
                    continue
                
                data = response.json()
                results = data.get("results", [])
                
                # Patrones para WhatsApp (internacionales)
                wa_patterns = [
                    # Links directos de WhatsApp
                    r'wa\.me/(\d{10,15})',
                    r'whatsapp\.com/send\?phone=(\d{10,15})',
                    # Números con + (cualquier país)
                    r'\+(\d{1,4}[\s\-]?\d{6,14})',
                    # Formato ZoomInfo y directorios
                    r'phone[:\s]+\+?(\d{10,15})',
                    r'tel[:\s]+\+?(\d{10,15})',
                ]
                
                for r in results:
                    texto = f"{r.get('title', '')} {r.get('content', '')}"
                    url = r.get('url', '')
                    
                    # Priorizar resultados de directorios
                    es_directorio = any(d in url.lower() for d in [
                        'zoominfo', 'linkedin', 'cylex', 
                        'paginasamarillas', 'yellowpages',
                        'guia', 'directorio', 'kompass'
                    ])
                    
                    for pattern in wa_patterns:
                        matches = re.findall(pattern, texto, re.IGNORECASE)
                        for match in matches:
                            # Limpiar: solo dígitos
                            num = re.sub(r'[^\d]', '', match)
                            
                            # Validar longitud (10-15 dígitos)
                            if len(num) < 10 or len(num) > 15:
                                continue
                            
                            # Evitar números que son años o IDs
                            if num.startswith('20') and len(num) == 4:
                                continue
                            if num.startswith('19') and len(num) == 4:
                                continue
                            
                            resultado = '+' + num
                            logger.info(
                                f"[WA-EXTERNO] ✓ Encontrado: {resultado} "
                                f"(fuente: {url[:50]})"
                            )
                            return resultado
                
        except Exception as e:
            logger.error(f"[WA-EXTERNO] Error: {e}")
            continue
    
    logger.info("[WA-EXTERNO] No encontrado en fuentes externas")
    return ""


async def extract_web_data(website: str) -> dict:
    """
    Pipeline completo de extracción web.
    Orden: Firecrawl → Jina → HTTP directo → Tavily (fallback) → Regex → GPT-4o → Merge
    """
    logger.info(f"[EXTRACTOR] ========== Iniciando: {website} ==========")
    
    website_clean = clean_url(website)
    website_full = f"https://{website_clean}"
    
    # ═══════════════════════════════════════════════════════════════════
    # EXTRACCIÓN MÚLTIPLE: Firecrawl → Jina → HTTP → Tavily (máxima cobertura)
    # ═══════════════════════════════════════════════════════════════════
    
    # 1. FIRECRAWL (mejor JS rendering, contenido dinámico)
    firecrawl_content = await fetch_with_firecrawl(website_clean)
    logger.info(f"[FIRECRAWL] {len(firecrawl_content)} caracteres")
    
    # 2. JINA (X-With-Links-Summary captura TODOS los links incluyendo mailto:)
    jina_content = await fetch_with_jina(website_clean)
    logger.info(f"[JINA] {len(jina_content)} caracteres")
    
    # 3. HTTP DIRECTO (HTML raw, a veces tiene datos que los otros no ven)
    http_content = await fetch_html_direct(website_full)
    logger.info(f"[HTTP] {len(http_content)} caracteres")
    
    # 4. PÁGINAS SECUNDARIAS (contacto, nosotros, equipo)
    secundarias_content = await extraer_paginas_secundarias(website_clean)
    logger.info(f"[SECUNDARIAS] {len(secundarias_content)} caracteres")
    
    # 5. COMBINAR TODO (el regex busca en todos los métodos)
    main_content = ""
    if firecrawl_content:
        main_content += "=== FIRECRAWL ===\n" + firecrawl_content + "\n\n"
    if jina_content:
        main_content += "=== JINA ===\n" + jina_content + "\n\n"
    if http_content:
        main_content += "=== HTTP ===\n" + http_content[:30000] + "\n\n"
    if secundarias_content:
        main_content += "=== PÁGINAS SECUNDARIAS ===\n" 
        main_content += secundarias_content + "\n\n"
    
    # 5. Tavily para búsqueda complementaria y descripción
    tavily_query = f'"{website_clean}" contacto dirección teléfono email Argentina'
    tavily_data = await search_with_tavily(tavily_query)
    
    tavily_answer = tavily_data.get("answer", "")
    tavily_raw = ""
    
    for r in tavily_data.get("results", []):
        if r.get('raw_content'):
            tavily_raw += r['raw_content'][:3000] + "\n"
    
    # 7. Combinar todo el contenido
    all_content = ""
    if main_content:
        all_content += "=== SITIO WEB ===\n" + main_content + "\n\n"
    if tavily_raw:
        all_content += "=== DATOS ADICIONALES (TAVILY) ===\n" + tavily_raw
    
    if len(all_content) > 20000:
        all_content = all_content[:20000]
    
    # Fallback 4: Tavily
    if not all_content:
        logger.info(f"[TAVILY] Fallback: extrayendo {website}...")
        tavily_content = await fetch_with_tavily(website_clean)
        if tavily_content:
            all_content = tavily_content
            logger.info(f"[TAVILY] ✓ {len(tavily_content)} caracteres extraídos")
    
    if not all_content:
        logger.warning(f"[EXTRACTOR] Los 4 métodos fallaron para {website}")
        return {
            "business_name": "No encontrado",
            "business_description": tavily_answer or "No encontrado",
            "website": website_full,
            "extraction_status": "failed"
        }
    
    logger.info(f"[EXTRACTOR] Contenido total: {len(all_content)} chars")
    
    # 8. Extracción Regex
    logger.info(f"[EXTRACTOR] Aplicando regex...")
    regex_data = extract_with_regex(all_content)
    
    # 9. Extracción GPT
    logger.info(f"[GPT] Extrayendo datos estructurados...")
    gpt_data = await extract_with_gpt(all_content, website_clean)
    
    # 10. Merge de resultados
    resultado = merge_results(gpt_data, regex_data, tavily_answer, website_full)
    
    # ═══════════════════════════════════════════════════════════════
    # BÚSQUEDA EXTERNA DE WHATSAPP (si no lo encontramos)
    # ═══════════════════════════════════════════════════════════════
    if resultado.get('_necesita_wa_externo'):
        empresa_nombre = resultado.get('business_name', '')
        wa_externo = await buscar_whatsapp_externo(
            website_clean, 
            empresa_nombre
        )
        if wa_externo:
            resultado['whatsapp_empresa'] = wa_externo
            resultado['whatsapp_source'] = 'externo'
        
        # Limpiar flag temporal
        resultado.pop('_necesita_wa_externo', None)
    
    # ═══════════════════════════════════════════════════════════════
    # BÚSQUEDA DE LINKEDIN PERSONAL EN CONTENIDO WEB
    # ═══════════════════════════════════════════════════════════════
    linkedin_encontrados = []
    
    # 1. Buscar LinkedIn en el contenido web extraído
    if main_content:
        nombre_contacto = resultado.get('contact_name', '')
        primer_nombre = nombre_contacto.split()[0] if nombre_contacto else ''
        apellido = nombre_contacto.split()[-1] if len(
            nombre_contacto.split()) > 1 else ''
        
        linkedin_en_web = await buscar_linkedin_en_web(
            contenido_web=main_content,
            nombre=primer_nombre,
            apellido=apellido
        )
        
        if linkedin_en_web:
            logger.info(
                f"[LINKEDIN-WEB] ✓ Encontrados en web: "
                f"{len(linkedin_en_web)}"
            )
            linkedin_encontrados.extend(linkedin_en_web)
    
    # 2. Buscar LinkedIn por email
    email = resultado.get('email_principal', '')
    if email and email != 'No encontrado' and '@' in email:
        linkedin_por_email = await buscar_linkedin_por_email(email)
        if linkedin_por_email and linkedin_por_email not in linkedin_encontrados:
            logger.info(
                f"[LINKEDIN-EMAIL] ✓ Encontrado: {linkedin_por_email}"
            )
            linkedin_encontrados.append(linkedin_por_email)
    
    # 3. Guardar resultados si encontramos algo
    if linkedin_encontrados:
        # Si ya hay linkedin_personal, agregar los nuevos
        actual = resultado.get('linkedin_personal_web', '')
        if actual and actual != 'No encontrado':
            todos = [actual] + [
                u for u in linkedin_encontrados if u != actual
            ]
        else:
            todos = linkedin_encontrados
        
        # Guardar máximo 3 URLs separadas por |
        resultado['linkedin_personal_web'] = ' | '.join(todos[:3])
        logger.info(
            f"[LINKEDIN] Total en web: "
            f"{resultado['linkedin_personal_web']}"
        )
    
    resultado['website'] = website_full
    resultado['extraction_status'] = 'success'
    
    logger.info(f"[EXTRACTOR] ========== Completado ==========")
    
    return resultado
