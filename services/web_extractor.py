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
from services.social_research import (buscar_linkedin_en_web,
                                      buscar_linkedin_por_email)

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
        url = f"https://{website}" if not website.startswith(
            "http") else website

        logger.info(f"[FIRECRAWL] Extrayendo: {url}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "url":
                    url,
                    "formats": ["markdown", "links", "html"],
                    "onlyMainContent":
                    False,
                    "includeTags":
                    ["a", "footer", "header", "nav", "div", "span", "p"],
                    "waitFor":
                    5000,
                    "timeout":
                    60000
                })

            if response.status_code == 200:
                data = response.json()

                if not data.get("success"):
                    logger.warning(
                        f"[FIRECRAWL] Extracción fallida: {data.get('error', 'Unknown')}"
                    )
                    return ""

                result_data = data.get("data", {})
                content = result_data.get("markdown", "")
                links = result_data.get("links", [])

                # Agregar links al final (como hace Jina con X-With-Links-Summary)
                if links:
                    content += "\n\n--- Links encontrados ---\n"
                    for link in links[:50]:  # Limitar a 50 links
                        content += f"- {link}\n"

                logger.info(
                    f"[FIRECRAWL] ✓ {len(content)} caracteres extraídos, {len(links)} links"
                )
                return content
            else:
                logger.warning(
                    f"[FIRECRAWL] Error {response.status_code}: {response.text[:200]}"
                )
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

        headers = {"Accept": "text/plain", "X-With-Links-Summary": "true"}

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
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT,
                                     follow_redirects=True) as client:
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
                    "query":
                    f"site:{website} empresa servicios contacto nosotros",
                    "search_depth": "advanced",
                    "include_raw_content": True,
                    "max_results": 5
                })
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
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "advanced",
                                             "max_results": 5,
                                             "include_answer": True,
                                             "include_raw_content": True
                                         })

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
        if not any(x in email_lower for x in [
                'example', 'sentry', 'wixpress', '.png', '.jpg', 'website.com',
                'domain.com'
        ]):
            emails_filtered.append(email_lower)

    regex_extract['emails'] = list(set(emails_filtered))[:5]
    logger.info(f"[REGEX] Emails encontrados: {regex_extract['emails']}")

    # ═══════════════════════════════════════════════════════════════════
    # 2. TELÉFONOS - Filtrar falsos positivos (IDs de Wix, etc.)
    # ═══════════════════════════════════════════════════════════════════
    phone_patterns = [
        # 1. href="tel:..." - MÁS CONFIABLE
        r'href=["\']tel:([^"\']+)',

        # 2. Con código de país: +54 11 1234-5678
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}',

        # 3. Con código de área entre paréntesis: (011) 1234-5678
        r'\(\d{2,5}\)[\s.-]?\d{3,4}[\s.-]?\d{3,4}',

        # NOTA: NO incluir patrón genérico \d{4}[\s.-]\d{4}
        # porque captura IDs, códigos, etc. (ej: "2050.3359" de Wix)
    ]

    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        for m in matches:
            phone = re.sub(r'[^\d+]', '', m) if isinstance(m, str) else m
            phone_digits = re.sub(r'\D', '', str(phone))
            # Mínimo 8 dígitos para ser un teléfono válido
            # Máximo 15 dígitos (estándar internacional)
            if 8 <= len(phone_digits) <= 15:
                phones.append(m.strip() if isinstance(m, str) else m)

    # También buscar teléfonos con contexto textual
    context_patterns = [
        r'(?:Tel[éeÉE]?fono|Tel\.?|Phone|Fono|Llamar?)[\s:]+([+\d\s\-\(\)\.]{8,20})',
        r'(?:Contacto|Contact)[\s:]+([+\d\s\-\(\)\.]{8,20})',
    ]

    for pattern in context_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        for m in matches:
            phone_digits = re.sub(r'\D', '', str(m))
            if 8 <= len(phone_digits) <= 15:
                phones.append(m.strip())

    regex_extract['phones'] = list(set(phones))[:5]

    # ═══════════════════════════════════════════════════════════════════
    # 3. WHATSAPP - 50+ PATRONES UNIVERSALES
    # Cubre: Elfsight, JoinChat, GetButton, Tawk, Crisp, WhatsHelp,
    # Click to Chat, Social Chat, Chaty, y cualquier widget flotante
    # ═══════════════════════════════════════════════════════════════════

    wa_patterns = [
        # ───────────────────────────────────────────────────────────────
        # GRUPO 1: Links directos WhatsApp (más confiables)
        # ───────────────────────────────────────────────────────────────
        r'wa\.me/(\d+)',
        r'api\.whatsapp\.com/send\?phone=(\d+)',
        r'web\.whatsapp\.com/send\?phone=(\d+)',
        r'href=["\']?whatsapp://send\?phone=(\d+)',
        r'whatsapp://send\?phone=(\d+)',
        r'wa\.me/\+?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 2: Elfsight Widget (muy común en sitios modernos)
        # ───────────────────────────────────────────────────────────────
        r'"whatsAppNumber"\s*:\s*"?\+?(\d{10,15})',
        r"'whatsAppNumber'\s*:\s*'?\+?(\d{10,15})",
        r'whatsAppNumber["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'data-whatsapp-number=["\']?\+?(\d{10,15})',
        r'elfsight.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'elfsight.*?whatsapp.*?(\d{10,15})',
        r'eapps\.widget.*?phone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 3: JoinChat / WhatsApp Chat Plugins
        # ───────────────────────────────────────────────────────────────
        r'joinchat.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'join\.chat.*?(\d{10,15})',
        r'wa_btnSetting.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'qlwapp.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'wabutton.*?phone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 4: GetButton / Chaty / Social Chat
        # ───────────────────────────────────────────────────────────────
        r'getbutton.*?phone.*?(\d{10,15})',
        r'chaty.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'social-chat.*?phone.*?(\d{10,15})',
        r'socialchat.*?whatsapp.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 5: Click to Chat / CTC
        # ───────────────────────────────────────────────────────────────
        r'click-to-chat.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'click2chat.*?phone.*?(\d{10,15})',
        r'ctc-phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'ctc_phone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 6: WhatsHelp / Tawk / Crisp / Drift
        # ───────────────────────────────────────────────────────────────
        r'whatshelp.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'tawk.*?whatsapp.*?(\d{10,15})',
        r'crisp.*?whatsapp.*?(\d{10,15})',
        r'drift.*?phone.*?(\d{10,15})',
        r'intercom.*?phone.*?(\d{10,15})',
        r'zendesk.*?phone.*?(\d{10,15})',
        r'hubspot.*?phone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 7: WordPress plugins específicos
        # ───────────────────────────────────────────────────────────────
        r'wc-whatsapp.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'wp-whatsapp.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'whatsapp-button.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'whatsapp-chat.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'socialintents.*?phone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'floating-wpp.*?phone.*?(\d{10,15})',
        r'flavor-flavor.*?phone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 8: Atributos data-* genéricos (muy comunes)
        # ───────────────────────────────────────────────────────────────
        r'data-phone=["\']?\+?(\d{10,15})',
        r'data-whatsapp=["\']?\+?(\d{10,15})',
        r'data-wa=["\']?\+?(\d{10,15})',
        r'data-tel=["\']?\+?(\d{10,15})',
        r'data-number=["\']?\+?(\d{10,15})',
        r'data-mobile=["\']?\+?(\d{10,15})',
        r'data-contact=["\']?\+?(\d{10,15})',
        r'data-phone-number=["\']?\+?(\d{10,15})',
        r'data-wa-number=["\']?\+?(\d{10,15})',
        r'data-settings.*?phone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 9: JSON/JavaScript objects (phoneNumber, phone, etc.)
        # ───────────────────────────────────────────────────────────────
        r'"phoneNumber"\s*:\s*"?\+?(\d{10,15})',
        r"'phoneNumber'\s*:\s*'?\+?(\d{10,15})",
        r'phoneNumber["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'"phone"\s*:\s*"?\+?(\d{10,15})',
        r"'phone'\s*:\s*'?\+?(\d{10,15})",
        r'"telephone"\s*:\s*"?\+?(\d{10,15})',
        r"'telephone'\s*:\s*'?\+?(\d{10,15})",
        r'"mobile"\s*:\s*"?\+?(\d{10,15})',
        r"'mobile'\s*:\s*'?\+?(\d{10,15})",
        r'"cel"\s*:\s*"?\+?(\d{10,15})',
        r'"celular"\s*:\s*"?\+?(\d{10,15})',
        r'"whatsapp"\s*:\s*"?\+?(\d{10,15})',
        r"'whatsapp'\s*:\s*'?\+?(\d{10,15})",
        r'"wa"\s*:\s*"?\+?(\d{10,15})',
        r'"contact_phone"\s*:\s*"?\+?(\d{10,15})',
        r'"business_phone"\s*:\s*"?\+?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 10: Schema.org / Structured Data / JSON-LD
        # ───────────────────────────────────────────────────────────────
        r'"contactPoint".*?"telephone"\s*:\s*"?\+?(\d{10,15})',
        r'itemprop=["\']telephone["\'].*?content=["\']?\+?(\d{10,15})',
        r'@type.*?ContactPoint.*?telephone["\']?\s*:\s*["\']?\+?(\d{10,15})',
        r'LocalBusiness.*?telephone.*?(\d{10,15})',
        r'Organization.*?telephone.*?(\d{10,15})',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 11: Texto visible con etiquetas comunes
        # ───────────────────────────────────────────────────────────────
        r'(?:whatsapp|wsp|wa)\s*[:\-]?\s*\+?(\d[\d\s\-]{9,14}\d)',
        r'(?:celular|móvil|movil|cel)\s*[:\-]?\s*\+?(\d[\d\s\-]{9,14}\d)',
        r'(?:telefono|teléfono|tel|fono)\s*[:\-]?\s*\+?(\d[\d\s\-]{9,14}\d)',

        # ───────────────────────────────────────────────────────────────
        # GRUPO 12: Formatos internacionales por país - TODOS
        # ───────────────────────────────────────────────────────────────
        r'href=["\']tel:\+?(\d{10,15})',

        # Latinoamérica
        r'\+54\s*9?\s*(\d{10})',  # Argentina
        r'\+52\s*1?\s*(\d{10})',  # México
        r'\+55\s*(\d{10,11})',  # Brasil
        r'\+56\s*9?\s*(\d{8,9})',  # Chile
        r'\+57\s*(\d{10})',  # Colombia
        r'\+51\s*9?\s*(\d{9})',  # Perú
        r'\+58\s*(\d{10})',  # Venezuela
        r'\+593\s*(\d{9})',  # Ecuador
        r'\+591\s*(\d{8})',  # Bolivia
        r'\+595\s*(\d{9})',  # Paraguay
        r'\+598\s*(\d{8})',  # Uruguay

        # Centroamérica
        r'\+502\s*(\d{8})',  # Guatemala
        r'\+503\s*(\d{8})',  # El Salvador
        r'\+504\s*(\d{8})',  # Honduras
        r'\+505\s*(\d{8})',  # Nicaragua
        r'\+506\s*(\d{8})',  # Costa Rica
        r'\+507\s*(\d{7,8})',  # Panamá
        r'\+501\s*(\d{7})',  # Belice

        # Caribe
        r'\+53\s*(\d{8})',  # Cuba
        r'\+1809\s*(\d{7})',  # República Dominicana (809)
        r'\+1829\s*(\d{7})',  # República Dominicana (829)
        r'\+1849\s*(\d{7})',  # República Dominicana (849)
        r'\+1787\s*(\d{7})',  # Puerto Rico (787)
        r'\+1939\s*(\d{7})',  # Puerto Rico (939)
        r'\+1868\s*(\d{7})',  # Trinidad y Tobago
        r'\+1876\s*(\d{7})',  # Jamaica
        r'\+509\s*(\d{8})',  # Haití

        # Norteamérica
        r'\+1\s*(\d{10})',  # USA / Canadá

        # Europa - Principales
        r'\+34\s*(\d{9})',  # España
        r'\+351\s*(\d{9})',  # Portugal
        r'\+39\s*(\d{9,10})',  # Italia
        r'\+33\s*(\d{9})',  # Francia
        r'\+49\s*(\d{10,11})',  # Alemania
        r'\+44\s*(\d{10})',  # Reino Unido
        r'\+31\s*(\d{9})',  # Países Bajos
        r'\+32\s*(\d{8,9})',  # Bélgica
        r'\+41\s*(\d{9})',  # Suiza
        r'\+43\s*(\d{10})',  # Austria
        r'\+353\s*(\d{9})',  # Irlanda
        r'\+45\s*(\d{8})',  # Dinamarca
        r'\+46\s*(\d{9})',  # Suecia
        r'\+47\s*(\d{8})',  # Noruega
        r'\+358\s*(\d{9})',  # Finlandia
        r'\+48\s*(\d{9})',  # Polonia
        r'\+420\s*(\d{9})',  # República Checa
        r'\+36\s*(\d{9})',  # Hungría
        r'\+30\s*(\d{10})',  # Grecia
        r'\+90\s*(\d{10})',  # Turquía
        r'\+7\s*(\d{10})',  # Rusia
        r'\+380\s*(\d{9})',  # Ucrania
        r'\+40\s*(\d{9})',  # Rumania

        # Asia - Principales
        r'\+86\s*(\d{11})',  # China
        r'\+81\s*(\d{10})',  # Japón
        r'\+82\s*(\d{9,10})',  # Corea del Sur
        r'\+91\s*(\d{10})',  # India
        r'\+92\s*(\d{10})',  # Pakistán
        r'\+62\s*(\d{9,12})',  # Indonesia
        r'\+60\s*(\d{9,10})',  # Malasia
        r'\+63\s*(\d{10})',  # Filipinas
        r'\+66\s*(\d{9})',  # Tailandia
        r'\+84\s*(\d{9})',  # Vietnam
        r'\+65\s*(\d{8})',  # Singapur
        r'\+852\s*(\d{8})',  # Hong Kong
        r'\+886\s*(\d{9})',  # Taiwán
        r'\+971\s*(\d{9})',  # Emiratos Árabes Unidos
        r'\+966\s*(\d{9})',  # Arabia Saudita
        r'\+972\s*(\d{9})',  # Israel

        # Oceanía
        r'\+61\s*(\d{9})',  # Australia
        r'\+64\s*(\d{8,9})',  # Nueva Zelanda

        # África - Principales
        r'\+27\s*(\d{9})',  # Sudáfrica
        r'\+20\s*(\d{10})',  # Egipto
        r'\+212\s*(\d{9})',  # Marruecos
        r'\+234\s*(\d{10})',  # Nigeria
        r'\+254\s*(\d{9})',  # Kenia
    ]

    for pattern in wa_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE | re.DOTALL)
        if match:
            wa_num = re.sub(r'[^\d]', '', match.group(1))
            if len(wa_num) >= 10 and len(wa_num) <= 15:
                regex_extract['whatsapp'] = '+' + wa_num
                logger.info(f"[REGEX] ✓ WhatsApp encontrado: +{wa_num}")
                break

    # ═══════════════════════════════════════════════════════════════════
    # 4. REDES SOCIALES
    # ═══════════════════════════════════════════════════════════════════

    # Instagram
    ig_match = re.search(
        r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)',
        all_content, re.IGNORECASE)
    if ig_match and ig_match.group(1) not in [
            'p', 'reel', 'stories', 'explore'
    ]:
        regex_extract[
            'instagram'] = f"https://instagram.com/{ig_match.group(1)}"

    # Facebook
    fb_match = re.search(
        r'(?:https?://)?(?:www\.)?facebook\.com/([a-zA-Z0-9.]+)', all_content,
        re.IGNORECASE)
    if fb_match and fb_match.group(1) not in [
            'sharer', 'share', 'dialog', 'plugins'
    ]:
        regex_extract['facebook'] = f"https://facebook.com/{fb_match.group(1)}"

    # LinkedIn empresa
    li_match = re.search(
        r'(?:https?://)?(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)',
        all_content, re.IGNORECASE)
    if li_match:
        regex_extract[
            'linkedin'] = f"https://linkedin.com/company/{li_match.group(1)}"

    # Twitter/X
    tw_match = re.search(
        r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9_]+)',
        all_content, re.IGNORECASE)
    if tw_match and tw_match.group(1) not in ['share', 'intent', 'home']:
        regex_extract['twitter'] = f"https://twitter.com/{tw_match.group(1)}"

    # YouTube - múltiples formatos de URL
    regex_extract['youtube'] = ''
    yt_patterns = [
        # Canal con prefijo: /channel/, /c/, /user/, /@
        r'(?:https?://)?(?:www\.)?youtube\.com/'
        r'(?:channel|c|user|@)/'
        r'([A-Za-z0-9_-]+)',

        # URL directa: youtube.com/nombrecanal
        r'(?:https?://)?(?:www\.)?youtube\.com/'
        r'([A-Za-z0-9_-]{3,30})'
        r'(?:\?|$|"|\'|\s)',

        # Formato con @: youtube.com/@nombrecanal
        r'(?:https?://)?(?:www\.)?youtube\.com/'
        r'@([A-Za-z0-9_-]+)',

        # En href
        r'href=["\']?(https?://(?:www\.)?youtube\.com/[^"\'>\\s]+)["\']?',
    ]

    for pattern in yt_patterns:
        yt_match = re.search(pattern, all_content, re.IGNORECASE)
        if yt_match:
            matched = yt_match.group(0)
            # Limpiar y construir URL completa
            if 'youtube.com' in matched:
                # Ya es URL completa
                yt_url_match = re.search(
                    r'https?://(?:www\.)?youtube\.com/[^\s"\'<>]+', matched)
                if yt_url_match:
                    yt_url = yt_url_match.group(0).split('?')[0].split('#')[0]
                    # Excluir watch, embed, etc.
                    excluir = [
                        '/watch', '/embed', '/playlist', '/results', '/feed',
                        '/gaming', '/premium', '/music'
                    ]
                    if not any(x in yt_url for x in excluir):
                        regex_extract['youtube'] = yt_url
                        logger.info(f"[REGEX] YouTube encontrado: {yt_url}")
                        break
            else:
                # Es solo el nombre del canal
                canal = yt_match.group(1) if yt_match.lastindex else ""
                if canal:
                    # Excluir palabras comunes que no son canales
                    excluir = [
                        'watch', 'embed', 'playlist', 'results', 'feed',
                        'gaming', 'premium', 'music'
                    ]
                    if canal.lower() not in excluir:
                        regex_extract[
                            'youtube'] = f"https://youtube.com/{canal}"
                        logger.info(
                            f"[REGEX] YouTube encontrado: {regex_extract['youtube']}"
                        )
                        break

    # ═══════════════════════════════════════════════════════════════════
    # 5. GOOGLE MAPS
    # ═══════════════════════════════════════════════════════════════════
    maps_match = re.search(r'https?://(?:www\.)?google\.com/maps[^\s"<>]+',
                           all_content, re.IGNORECASE)
    if maps_match:
        regex_extract['google_maps_url'] = maps_match.group(0).split(
            '"')[0].split("'")[0]

    # ═══════════════════════════════════════════════════════════════════
    # 6. CUIT/CUIL (Argentina)
    # ═══════════════════════════════════════════════════════════════════
    cuit_match = re.search(r'(?:CUIT|CUIL)[:\s]*(\d{2}[-\s]?\d{8}[-\s]?\d{1})',
                           all_content, re.IGNORECASE)
    if cuit_match:
        regex_extract['cuit_cuil'] = cuit_match.group(1)

    # ═══════════════════════════════════════════════════════════════════
    # 7. DIRECCIONES - INTERNACIONAL (Mejorados para detectar más casos)
    # ═══════════════════════════════════════════════════════════════════
    direccion_patterns = [
        # ══════════════════════════════════════════════════════
        # FORMATO GENERAL: Av/Calle + Nombre + Número + Extras
        # ══════════════════════════════════════════════════════

        # Patrón universal flexible (captura la mayoría)
        r'(?:Av\.?|Avenida|Calle|Ca\.?|C/|Bv\.?|Boulevard|Blvd\.?|'
        r'Pasaje|Pje\.?|Paseo|Jr\.?|Jirón|Rua|Alameda|Travessa|'
        r'Carrera|Cra\.?|Transversal|Diagonal|Plaza|Pza\.?)'
        r'\s*[A-Za-záéíóúñüÁÉÍÓÚÑÜçÇ\.\s]{2,40}'
        r'\s*\d{1,5}'
        r'(?:\s*[-,]\s*[A-Za-záéíóúñ\.\s\d]+)?',

        # Argentina: "Av. Congreso 2595, Piso 2 C1428BVM"
        r'(?:Av\.?|Avenida|Calle|Bv\.?|Boulevard)'
        r'\s+[A-Za-záéíóúñÁÉÍÓÚÑ\s\.]+\s+\d{1,5}'
        r'(?:\s*,?\s*(?:Piso|P\.?)\s*\d{1,2}'
        r'(?:\s*,?\s*(?:Dto\.?|Depto\.?|Dpto\.?)\s*[A-Za-z0-9]+)?)?'
        r'(?:\s*[A-Z]\d{4}[A-Z]{3})?',

        # México: "Calle X #123, Col. Centro, CP 12345"
        r'(?:Calle|Av\.?|Avenida|Blvd\.?)'
        r'\s+[A-Za-záéíóúñ\s]+\s*#?\s*\d{1,5}'
        r'(?:\s*,?\s*(?:Col\.?|Colonia)\s+[A-Za-záéíóúñ\s]+)?'
        r'(?:\s*,?\s*(?:CP\.?|C\.?P\.?)\s*\d{5})?',

        # Colombia: "Calle 45 #23-67" o "Carrera 7 No. 123-45"
        r'(?:Calle|Carrera|Cra\.?|Cl\.?|Transversal|Diagonal)'
        r'\s*\d{1,3}[A-Za-z]?\s*(?:#|No\.?|N°)?\s*\d{1,3}[A-Za-z]?'
        r'(?:\s*[-]\s*\d{1,3})?',

        # Chile: "Av. Providencia 1234, Depto 5"
        r'(?:Av\.?|Avenida|Calle|Pasaje)'
        r'\s+[A-Za-záéíóúñ\s]+\s+\d{1,5}'
        r'(?:\s*,?\s*(?:Depto\.?|Oficina|Of\.?|Dpto\.?)\s*\d+)?',

        # España: "C/ Mayor, 12, 3º, 28001 Madrid"
        r'(?:Calle|C/|Avda\.?|Avenida|Plaza|Pza\.?|Paseo)'
        r'\s+[A-Za-záéíóúñ\s]+,?\s*\d{1,4}'
        r'(?:\s*,?\s*\d{1,2}[ºª°]?)?'
        r'(?:\s*,?\s*\d{5})?',

        # Brasil: "Rua das Flores, nº 789, CEP 01234-567"
        r'(?:Rua|Av\.?|Avenida|Alameda|Travessa)'
        r'\s+[A-Za-záéíóúãõçÁÉÍÓÚÃÕÇ\s]+,?\s*(?:n[ºo°]?\.?)?\s*\d{1,5}'
        r'(?:\s*,?\s*(?:CEP|Cep)\s*\d{5}[-]?\d{3})?',

        # Perú: "Jr. Lima 234, Of. 5"
        r'(?:Jr\.?|Jirón|Av\.?|Avenida|Calle|Ca\.?)'
        r'\s+[A-Za-záéíóúñ\s]+\s+\d{1,4}'
        r'(?:\s*,?\s*(?:Of\.?|Oficina|Dpto\.?)\s*\d+)?',

        # USA/UK: "123 Main Street, Suite 456, 90210"
        r'\d{1,5}\s+[A-Za-z\s]{3,40}'
        r'(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|'
        r'Drive|Dr\.?|Lane|Ln\.?|Way|Place|Pl\.?)'
        r'(?:\s*,?\s*(?:Suite|Ste\.?|Apt\.?|Unit|#)\s*[A-Za-z0-9]+)?'
        r'(?:\s*,?\s*\d{5}(?:-\d{4})?)?',

        # Alemania: "Hauptstraße 45, 10115 Berlin"
        r'[A-Za-zäöüÄÖÜß]+(?:straße|strasse|str\.?|weg|platz|allee)'
        r'\s*\d{1,4}[a-z]?'
        r'(?:\s*,?\s*\d{5})?',

        # Francia: "45 Rue de la Paix, 75002 Paris"
        r'\d{1,4}\s+(?:Rue|Avenue|Boulevard|Place|Allée)'
        r'\s+[A-Za-zàâäéèêëïîôùûüÿœæ\s]+'
        r'(?:\s*,?\s*\d{5})?',

        # Italia: "Via Roma 45, 00100 Roma"
        r'(?:Via|Viale|Piazza|Corso|Largo)'
        r'\s+[A-Za-zàèéìòù\s]+,?\s*\d{1,4}'
        r'(?:\s*,?\s*\d{5})?',
    ]

    for pattern in direccion_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match and len(match.group(0)) > 10:
            direccion = match.group(0).strip()
            # Limpiar espacios múltiples
            direccion = re.sub(r'\s+', ' ', direccion)
            regex_extract['address'] = direccion
            logger.info(f"[REGEX] Dirección encontrada: {direccion}")
            break

    # ═══════════════════════════════════════════════════════════════════
    # 7B. PROVINCIAS/ESTADOS - Solo para VALIDACIÓN, no para detección
    # GPT extrae ciudad/barrio del contenido real de la web
    # ═══════════════════════════════════════════════════════════════════

    # Lista mínima solo para validar provincias/estados principales
    # NO incluir ciudades/barrios - eso lo detecta GPT del contenido
    # Diccionario provincia -> país (para asignar país correcto)
    provincia_a_pais = {
        # Argentina
        'Buenos Aires': 'Argentina',
        'CABA': 'Argentina',
        'Capital Federal': 'Argentina',
        'Córdoba': 'Argentina',
        'Santa Fe': 'Argentina',
        'Mendoza': 'Argentina',
        'Tucumán': 'Argentina',
        'Entre Ríos': 'Argentina',
        'Salta': 'Argentina',
        'Misiones': 'Argentina',
        'Chaco': 'Argentina',
        'Corrientes': 'Argentina',
        'Santiago del Estero': 'Argentina',
        'San Juan': 'Argentina',
        'Jujuy': 'Argentina',
        'Río Negro': 'Argentina',
        'Neuquén': 'Argentina',
        'Formosa': 'Argentina',
        'Chubut': 'Argentina',
        'San Luis': 'Argentina',
        'Catamarca': 'Argentina',
        'La Rioja': 'Argentina',
        'La Pampa': 'Argentina',
        'Santa Cruz': 'Argentina',
        'Tierra del Fuego': 'Argentina',
        # México
        'Ciudad de México': 'México',
        'CDMX': 'México',
        'Jalisco': 'México',
        'Nuevo León': 'México',
        'Estado de México': 'México',
        'Puebla': 'México',
        'Guanajuato': 'México',
        'Querétaro': 'México',
        'Yucatán': 'México',
        'Monterrey': 'México',
        'Guadalajara': 'México',
        # Colombia
        'Bogotá': 'Colombia',
        'Antioquia': 'Colombia',
        'Valle del Cauca': 'Colombia',
        'Cundinamarca': 'Colombia',
        'Atlántico': 'Colombia',
        'Santander': 'Colombia',
        'Medellín': 'Colombia',
        'Cali': 'Colombia',
        'Barranquilla': 'Colombia',
        # Chile
        'Santiago': 'Chile',
        'Región Metropolitana': 'Chile',
        'Valparaíso': 'Chile',
        'Biobío': 'Chile',
        'Concepción': 'Chile',
        # España
        'Madrid': 'España',
        'Cataluña': 'España',
        'Barcelona': 'España',
        'Andalucía': 'España',
        'Valencia': 'España',
        'País Vasco': 'España',
        'Sevilla': 'España',
        'Bilbao': 'España',
        'Málaga': 'España',
        'Galicia': 'España',
        # Brasil
        'São Paulo': 'Brasil',
        'Rio de Janeiro': 'Brasil',
        'Minas Gerais': 'Brasil',
        'Bahia': 'Brasil',
        # Perú
        'Lima': 'Perú',
        'Arequipa': 'Perú',
        'Cusco': 'Perú',
        # Uruguay
        'Montevideo': 'Uruguay',
        # Ecuador
        'Quito': 'Ecuador',
        'Guayaquil': 'Ecuador',
    }

    content_lower = all_content.lower()

    # NO buscar provincias genéricas en todo el contenido
    # Solo GPT debe detectar ubicación del contexto real
    # El regex solo se usa como fallback si GPT no encuentra nada
    # y solo si la palabra aparece cerca de palabras clave de ubicación

    ubicacion_keywords = [
        'dirección', 'direccion', 'ubicación', 'ubicacion', 'oficina', 'sede',
        'domicilio', 'address', 'location', 'calle', 'avenida', 'av.', 'av ',
        'carrera', 'piso'
    ]

    # Buscar si hay contexto de ubicación
    tiene_contexto_ubicacion = any(kw in content_lower
                                   for kw in ubicacion_keywords)

    # Solo buscar provincia si hay contexto de ubicación
    if tiene_contexto_ubicacion:
        for provincia, pais in provincia_a_pais.items():
            # Buscar provincia con límites de palabra para evitar
            # falsos positivos
            pattern = r'\b' + re.escape(provincia) + r'\b'
            if re.search(pattern, all_content, re.IGNORECASE):
                regex_extract['province'] = provincia
                regex_extract['country_from_province'] = pais
                logger.info(f"[REGEX] Provincia/Estado: {provincia} "
                            f"-> País: {pais}")
                break

    # Ciudad: NO buscar en lista, dejar que GPT la detecte
    # del contenido real de la página

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
        'SOFTWARE', 'HARDWARE', 'CLOUD', 'CONECTIVIDAD', 'REDES', 'CÁMARAS',
        'CAMARAS', 'CCTV', 'ACCESS POINT', 'ROUTER', 'SWITCH', 'FIBRA ÓPTICA',
        'FIBRA OPTICA', 'UPS', 'ENERGÍA', 'ENERGIA', 'MONITOREO', 'ALARMAS',
        'RASTREO', 'GPS', 'VIGILANCIA'
    ]

    content_upper = all_content.upper()
    servicios_encontrados = []

    for keyword in servicios_keywords:
        if keyword in content_upper:
            servicios_encontrados.append(keyword.title())

    regex_extract['servicios'] = list(set(servicios_encontrados))

    return regex_extract


def extraer_titulo_pagina(html_content: str) -> str:
    """Extrae el título de la página del HTML."""
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content,
                            re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()
    return ""


def extraer_ciudad_de_titulo(titulo: str) -> str:
    """
    Extrae ciudad/barrio del título de la página.

    Ejemplos:
    - "Empresa X | Núñez" → "Núñez"
    - "Servicios en Madrid | Empresa" → "Madrid"
    - "Company - New York Office" → "New York"
    """
    import re

    if not titulo:
        return ""

    # Separadores comunes en títulos
    separadores = ['|', '-', '–', '—', '•', '·', ':']

    partes = [titulo]
    for sep in separadores:
        nuevas_partes = []
        for parte in partes:
            nuevas_partes.extend(parte.split(sep))
        partes = nuevas_partes

    # Limpiar partes
    partes = [p.strip() for p in partes if p.strip()]

    # Palabras a ignorar (no son ciudades)
    ignorar = [
        'home',
        'inicio',
        'principal',
        'bienvenido',
        'welcome',
        'contacto',
        'contact',
        'nosotros',
        'about',
        'servicios',
        'services',
        'productos',
        'products',
        'blog',
        'empresa',
        'company',
        'oficial',
        'official',
        'sitio',
        'site',
        'web',
        'página',
        'page',
        'tienda',
        'store',
        'shop',
    ]

    # Buscar la parte que parece ciudad (corta, sin palabras comunes)
    for parte in partes:
        parte_lower = parte.lower()

        # Ignorar si es muy larga (probablemente no es ciudad)
        if len(parte) > 30:
            continue

        # Ignorar si contiene palabras comunes
        es_ignorable = False
        for palabra in ignorar:
            if palabra in parte_lower:
                es_ignorable = True
                break

        if es_ignorable:
            continue

        # Ignorar si parece nombre de empresa (tiene SA, SRL, LLC, etc.)
        if re.search(r'\b(?:SA|SRL|LLC|Inc|Corp|Ltd|GmbH|SAS|SAC)\b', parte,
                     re.IGNORECASE):
            continue

        # Si llegó acá, puede ser ciudad
        # Verificar que tenga formato de nombre propio
        if re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+$', parte):
            return parte

    return ""


def extraer_direccion_por_contexto(all_content: str) -> str:
    """
    Extrae dirección buscando por contexto semántico.

    LÓGICA UNIVERSAL:
    1. Buscar palabras clave que indican dirección
    2. Extraer texto después de esas palabras
    3. Validar que parezca una dirección real

    Funciona para cualquier idioma/país porque busca 
    por SEMÁNTICA, no por formato específico.
    """
    import re

    if not all_content:
        return ""

    # Palabras clave que indican dirección (multi-idioma)
    keywords_direccion = [
        # Español
        r'direcci[oó]n[:\s]+',
        r'ubicaci[oó]n[:\s]+',
        r'domicilio[:\s]+',
        r'oficina[s]?[:\s]+',
        r'sede[:\s]+',
        r'd[oó]nde\s+estamos[:\s]*',
        r'enc[uo]ntranos[:\s]+',
        r'vis[ií]tanos[:\s]+',

        # Inglés
        r'address[:\s]+',
        r'location[:\s]+',
        r'office[:\s]+',
        r'headquarters[:\s]+',
        r'find\s+us[:\s]+',
        r'visit\s+us[:\s]+',

        # Portugués
        r'endere[cç]o[:\s]+',
        r'localiza[cç][aã]o[:\s]+',

        # Alemán
        r'adresse[:\s]+',
        r'standort[:\s]+',

        # Francés
        r'adresse[:\s]+',
        r'si[eè]ge[:\s]+',
    ]

    # Indicadores de que el texto es una dirección
    indicadores_direccion = [
        # Prefijos de calle (multi-país)
        r'\b(?:Av\.?|Avenida|Calle|Ca\.?|C/|Bv\.?|Boulevard|'
        r'Blvd\.?|Pasaje|Pje\.?|Paseo|Jr\.?|Jirón|Rua|'
        r'Alameda|Travessa|Carrera|Cra\.?|Via|Viale|Piazza|'
        r'Corso|Rue|Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|'
        r'Drive|Dr\.?|Lane|Ln\.?|Place|Pl\.?)\b',

        # Números de calle
        r'\b\d{1,5}\b',

        # Pisos/Departamentos
        r'\b(?:Piso|P\.?|Dto\.?|Depto\.?|Dpto\.?|Of\.?|'
        r'Oficina|Suite|Ste\.?|Apt\.?|Floor|Unit)\b',

        # Códigos postales
        r'\b[A-Z]?\d{4,5}[A-Z]{0,3}\b',
    ]

    content = all_content.replace('\n', ' ').replace('\r', ' ')
    content = re.sub(r'\s+', ' ', content)

    # Buscar cada palabra clave
    for keyword in keywords_direccion:
        matches = re.finditer(keyword, content, re.IGNORECASE)

        for match in matches:
            # Extraer texto después de la palabra clave (hasta 150 chars)
            inicio = match.end()
            fin = min(len(content), inicio + 150)
            texto_despues = content[inicio:fin]

            # Cortar en punto, coma seguida de espacio y mayúscula,
            # o salto implícito
            cortes = [
                r'\.\s+[A-Z]',  # Punto seguido de mayúscula
                r'\s{2,}',  # Múltiples espacios
                r'[|]',  # Separador
                r'(?:Tel[éeÉE]?fono|Email|Mail|Contacto)',  # Otra sección
            ]

            for corte in cortes:
                corte_match = re.search(corte, texto_despues)
                if corte_match:
                    texto_despues = texto_despues[:corte_match.start()]
                    break

            texto_despues = texto_despues.strip()

            # Validar que parece dirección (tiene indicadores)
            indicadores_encontrados = 0
            for indicador in indicadores_direccion:
                if re.search(indicador, texto_despues, re.IGNORECASE):
                    indicadores_encontrados += 1

            # Necesita al menos 2 indicadores para ser válida
            if indicadores_encontrados >= 2 and len(texto_despues) >= 10:
                # Limpiar
                texto_despues = texto_despues.strip(' ,.-:')
                logger.info(f"[DIRECCION] ✓ Encontrada por contexto: "
                            f"{texto_despues[:80]}")
                return texto_despues[:100]  # Limitar longitud

    return ""


def extraer_cargo_de_equipo(all_content: str, nombre_persona: str = "") -> str:
    """
    Extrae el cargo de una persona específica del contenido.

    LÓGICA UNIVERSAL:
    1. Si hay nombre, buscar cargo ASOCIADO a ese nombre
    2. Buscar en bloques cercanos al nombre
    3. Solo si no encuentra, buscar cargo genérico (CEO/Fundador)

    Args:
        all_content: Contenido HTML/texto de la página
        nombre_persona: Nombre de la persona a buscar

    Returns:
        Cargo encontrado o "No detectado"
    """
    import re

    if not all_content:
        return "No detectado"

    # Limpiar contenido
    content = all_content.replace('\n', ' ').replace('\r', ' ')
    content = re.sub(r'\s+', ' ', content)

    # Lista de cargos ejecutivos (internacional)
    cargos_ejecutivos = [
        # C-Level
        'CEO',
        'CFO',
        'CTO',
        'COO',
        'CMO',
        'CIO',
        'CISO',
        'CPO',
        'Chief Executive Officer',
        'Chief Financial Officer',
        'Chief Technology Officer',
        'Chief Operating Officer',
        'Chief Marketing Officer',
        'Chief Information Officer',

        # Dirección
        'Director General',
        'Director Ejecutivo',
        'Director Comercial',
        'Director de Tecnología',
        'Director de Marketing',
        'Director de Operaciones',
        'Director de Ventas',
        'Director Financiero',
        'Director de RRHH',
        'Managing Director',
        'Executive Director',

        # Presidencia
        'Presidente',
        'President',
        'Vicepresidente',
        'Vice President',
        'VP',
        'Chairman',
        'Chairwoman',

        # Fundadores
        'Fundador',
        'Founder',
        'Co-Fundador',
        'Co-Founder',
        'Cofundador',
        'Cofounder',
        'Socio Fundador',

        # Gerencia
        'Gerente General',
        'Gerente Comercial',
        'Gerente de Ventas',
        'Gerente de Marketing',
        'Gerente de Operaciones',
        'Gerente de Tecnología',
        'Gerente de Sistemas',
        'Gerente de Administración',
        'Gerente de RRHH',
        'General Manager',
        'Sales Manager',
        'Marketing Manager',

        # Propiedad
        'Propietario',
        'Owner',
        'Dueño',
        'Socio',
        'Partner',

        # Otros
        'Head of',
        'Jefe de',
        'Líder de',
        'Lead',
        'Country Manager',
        'Regional Manager',
    ]

    # Palabras que invalidan un cargo (falsos positivos)
    invalidos = [
        'negocio',
        'servicio',
        'comercio',
        'inicio',
        'ejercicio',
        'beneficio',
        'precio',
        'espacio',
        'edificio',
        'oficio',
        'cliente',
        'usuario',
        'nuestro',
        'nuestra',
        'empresa',
        'solución',
        'soluciones',
        'producto',
        'productos',
    ]

    def es_cargo_valido(texto: str, cargo: str) -> bool:
        """Verifica que el cargo no sea un falso positivo."""
        texto_lower = texto.lower()
        cargo_lower = cargo.lower()

        for invalido in invalidos:
            # Si el cargo está dentro de una palabra inválida
            if cargo_lower in invalido:
                if invalido in texto_lower:
                    return False
        return True

    def buscar_cargo_cerca_de_nombre(contenido: str,
                                     nombre: str,
                                     ventana: int = 200) -> str:
        """
        Busca un cargo dentro de una ventana de caracteres 
        alrededor del nombre.
        """
        nombre_lower = nombre.lower()
        contenido_lower = contenido.lower()

        # Buscar todas las ocurrencias del nombre
        pos = 0
        while True:
            idx = contenido_lower.find(nombre_lower, pos)
            if idx == -1:
                break

            # Extraer ventana alrededor del nombre
            inicio = max(0, idx - ventana)
            fin = min(len(contenido), idx + len(nombre) + ventana)
            bloque = contenido[inicio:fin]

            # Buscar cargos en este bloque
            for cargo in cargos_ejecutivos:
                # Usar word boundary para evitar falsos positivos
                pattern = r'\b' + re.escape(cargo) + r'\b'
                match = re.search(pattern, bloque, re.IGNORECASE)
                if match:
                    cargo_encontrado = match.group(0)
                    if es_cargo_valido(bloque, cargo_encontrado):
                        # Buscar cargo compuesto (ej: "Presidente y Director")
                        cargo_extendido = extraer_cargo_completo(
                            bloque, match.start())
                        return cargo_extendido or cargo_encontrado

            pos = idx + 1

        return ""

    def extraer_cargo_completo(texto: str, pos_inicio: int) -> str:
        """
        Extrae cargo compuesto como "Presidente y Director Comercial".
        """
        # Buscar desde un poco antes hasta un poco después
        inicio = max(0, pos_inicio - 20)
        fin = min(len(texto), pos_inicio + 80)
        fragmento = texto[inicio:fin]

        # Patrón para cargos compuestos
        patron_compuesto = (
            r'((?:Presidente|Director|Gerente|CEO|Fundador|Socio)'
            r'(?:\s+y\s+|\s*/\s*|\s*,\s*)?'
            r'(?:Director|Gerente|Comercial|Ejecutivo|General|'
            r'de\s+\w+)?'
            r'(?:\s+y\s+|\s*/\s*)?'
            r'(?:Director|Gerente|Comercial|Ejecutivo|General|'
            r'de\s+\w+)?)')

        match = re.search(patron_compuesto, fragmento, re.IGNORECASE)
        if match:
            cargo = match.group(1).strip()
            # Limpiar espacios extras
            cargo = re.sub(r'\s+', ' ', cargo)
            return cargo

        return ""

    def buscar_en_estructura_equipo(contenido: str, nombre: str) -> str:
        """
        Busca cargo en estructuras típicas de página de equipo.
        Patrones: "Nombre - Cargo", "Nombre | Cargo", etc.
        """
        nombre_parts = nombre.lower().split()
        if len(nombre_parts) < 2:
            return ""

        # Patrones comunes de estructura nombre-cargo
        patrones_estructura = [
            # "Juan Pérez - Director General"
            rf'{re.escape(nombre)}\s*[-–—]\s*([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)',
            # "Juan Pérez | CEO"
            rf'{re.escape(nombre)}\s*\|\s*([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)',
            # "Juan Pérez, Presidente"
            rf'{re.escape(nombre)}\s*,\s*([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)',
            # Apellido seguido de cargo (en listas)
            rf'{re.escape(nombre_parts[-1])}\s+([A-Za-záéíóúñ]+\s+(?:de\s+)?[A-Za-záéíóúñ]+)',
        ]

        for patron in patrones_estructura:
            match = re.search(patron, contenido, re.IGNORECASE)
            if match:
                posible_cargo = match.group(1).strip()
                # Verificar que sea un cargo válido
                for cargo in cargos_ejecutivos:
                    if cargo.lower() in posible_cargo.lower():
                        return posible_cargo[:50]  # Limitar longitud

        return ""

    # ═══════════════════════════════════════════════════════════════
    # LÓGICA PRINCIPAL
    # ═══════════════════════════════════════════════════════════════

    # PASO 1: Si hay nombre, buscar cargo asociado
    if nombre_persona and len(nombre_persona) >= 3:
        logger.info(f"[CARGO] Buscando cargo para: {nombre_persona}")

        # 1A: Buscar en estructura típica de equipo
        cargo = buscar_en_estructura_equipo(content, nombre_persona)
        if cargo:
            logger.info(f"[CARGO] ✓ Encontrado en estructura: {cargo}")
            return cargo

        # 1B: Buscar en ventana cercana al nombre
        cargo = buscar_cargo_cerca_de_nombre(content, nombre_persona)
        if cargo:
            logger.info(f"[CARGO] ✓ Encontrado cerca del nombre: {cargo}")
            return cargo

        # 1C: Intentar solo con el apellido
        partes_nombre = nombre_persona.split()
        if len(partes_nombre) >= 2:
            apellido = partes_nombre[-1]
            cargo = buscar_cargo_cerca_de_nombre(content, apellido)
            if cargo:
                logger.info(
                    f"[CARGO] ✓ Encontrado cerca del apellido: {cargo}")
                return cargo

    # PASO 2: Si no hay nombre o no encontró, buscar cargo principal
    # Solo CEO, Presidente, Fundador, Director General
    cargos_principales = [
        'CEO', 'Presidente', 'Fundador', 'Director General', 'Founder',
        'President', 'Propietario', 'Owner'
    ]

    for cargo in cargos_principales:
        pattern = r'\b' + re.escape(cargo) + r'\b'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            bloque = content[max(0, match.start() - 50):match.end() + 50]
            if es_cargo_valido(bloque, cargo):
                logger.info(f"[CARGO] ✓ Cargo principal encontrado: {cargo}")
                return match.group(0)

    logger.info("[CARGO] ✗ No se encontró cargo")
    return "No detectado"


async def extract_with_gpt(all_content: str,
                           website: str,
                           titulo_pagina: str = "") -> dict:
    """
    Usa GPT-4o-mini para extraer datos estructurados.
    """
    if not OPENAI_API_KEY:
        return {}

    # Instrucción sobre el título
    instruccion_titulo = ""
    ciudad_del_titulo = ""
    if titulo_pagina:
        # Extraer ciudad del título
        ciudad_del_titulo = extraer_ciudad_de_titulo(titulo_pagina)
        if ciudad_del_titulo:
            instruccion_titulo = f"""
TÍTULO DE LA PÁGINA: {titulo_pagina}
CIUDAD DETECTADA EN TÍTULO: {ciudad_del_titulo}
IMPORTANTE: Usar "{ciudad_del_titulo}" como city si no encuentras otra ciudad en el contenido.
"""
        else:
            instruccion_titulo = f"""
TÍTULO DE LA PÁGINA: {titulo_pagina}
IMPORTANTE: El título puede contener la ciudad/barrio/localidad. 
Por ejemplo "Empresa X | Núñez" - extraer "Núñez" como city.
Otro ejemplo: "Servicios en Madrid | Empresa Y" → city = "Madrid"
Si no encuentras ciudad en el contenido, buscar en el título.
"""

    # Construir instrucción de city
    instruccion_city = "- city: Ciudad (revisar también el TÍTULO de la página)"
    if ciudad_del_titulo:
        instruccion_city = f'- city: Ciudad (revisar también el TÍTULO de la página. Si el título tiene "{ciudad_del_titulo}", usar ese valor)'

    prompt = f"""Extraé los siguientes datos del contenido de este sitio web ({website}).

Respondé SOLO con JSON válido, sin explicaciones ni markdown.
Si no encontrás un dato, usá "No encontrado".

{instruccion_titulo}

IMPORTANTE PARA business_activity:
- Identificá el RUBRO/INDUSTRIA principal de la empresa
- Ejemplos: "Distribuidora de alarmas y seguridad", "Servicios de TI", 
  "Clínica dental", "E-commerce de indumentaria", "Consultoría empresarial"
- Si no está explícito, INFERILO de: servicios, productos, descripción, 
  o título del sitio
- Si la empresa vende productos → describir QUÉ vende
- Si la empresa ofrece servicios → describir QUÉ servicios
- NUNCA inventes, pero SÍ infiere del contexto disponible

DATOS A EXTRAER:
- business_name: Nombre de la empresa
- business_activity: Rubro/industria principal (OBLIGATORIO - inferir 
  del contexto si no está explícito)
- business_model: Modelo de negocio (B2B, B2C, B2B2C, SaaS, Ecommerce, 
  Servicios profesionales, Retail, Mayorista, Minorista, Franquicia, 
  Suscripción, Marketplace, o el que corresponda)
- business_description: Descripción breve de qué hace la empresa 
  (máx 200 chars)
- services: Lista de 3-5 servicios/productos principales
- email_principal: Email de contacto principal
- phone_empresa: Teléfono principal (formato E.164 si es posible)
- whatsapp_empresa: Número WhatsApp de la empresa (buscar en widgets 
  flotantes, botones de chat, atributos data-settings, data-phone, 
  telephone, o cerca de palabras whatsapp/chat/contacto. Solo números 
  con código país, ej: 5493416469327)
- address: Dirección física
{instruccion_city}
- province: Provincia
- country: País (default Argentina si no está especificado)
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
                    "model": "gpt-4o",
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature": 0.1,
                    "max_tokens": 2000
                })

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


def merge_results(gpt_data: dict,
                  regex_data: dict,
                  tavily_answer: str,
                  website: str = "",
                  all_content: str = "") -> dict:
    """
    Combina resultados de GPT, Regex y Tavily.
    Prioridad: GPT > Regex > Tavily
    """
    resultado = gpt_data.copy() if gpt_data else {}

    # Descripción - solo de GPT (sin fuentes externas)
    desc_gpt = resultado.get('business_description', '')
    if not desc_gpt or desc_gpt == 'No encontrado' or len(desc_gpt) < 50:
        resultado['business_description'] = "No encontrado"

    # Servicios
    if not resultado.get('services') and regex_data.get('servicios'):
        resultado['services'] = regex_data['servicios']

    # ══════════════════════════════════════════════════════════════════
    # EMAILS - Prioridad mejorada: dominio > genéricos > GPT > otros
    # ══════════════════════════════════════════════════════════════════
    gpt_email = resultado.get('email_principal', '')
    regex_emails = regex_data.get('emails', [])
    website_domain = website.replace("https://",
                                     "").replace("http://",
                                                 "").replace("www.",
                                                             "").split("/")[0]

    # Separar emails por tipo
    domain_email = None
    generic_emails = []
    other_emails = []

    generic_prefixes = [
        'info', 'contacto', 'contact', 'ventas', 'sales', 'hola', 'hello',
        'soporte', 'support', 'admin', 'consultas', 'atencion', 'comercial'
    ]

    for email in regex_emails:
        if "@" not in email:
            continue
        email_prefix = email.split("@")[0].lower()
        email_domain = email.split("@")[1].lower()

        if website_domain in email_domain or email_domain in website_domain:
            if any(p in email_prefix for p in generic_prefixes):
                domain_email = email
                break
            elif not domain_email:
                domain_email = email
        elif any(p in email_prefix for p in generic_prefixes):
            generic_emails.append(email)
        else:
            other_emails.append(email)

    if domain_email:
        resultado['email_principal'] = domain_email
        logger.info(f"[MERGE] Email del dominio: {domain_email}")
    elif generic_emails:
        resultado['email_principal'] = generic_emails[0]
        logger.info(f"[MERGE] Email genérico: {generic_emails[0]}")
    elif gpt_email and gpt_email != "No encontrado" and "@" in gpt_email:
        resultado['email_principal'] = gpt_email
        logger.info(f"[MERGE] Email de GPT: {gpt_email}")
    elif other_emails:
        resultado['email_principal'] = other_emails[0]
        logger.info(f"[MERGE] Email alternativo: {other_emails[0]}")
    else:
        resultado['email_principal'] = "No encontrado"

    todos_emails = list(
        set([e for e in [domain_email] + generic_emails + other_emails if e]))
    if len(todos_emails) > 1:
        resultado['emails_adicionales'] = todos_emails[1:4]

    # ══════════════════════════════════════════════════════════════════
    # TELÉFONO - Validación mejorada + fallback agresivo a regex
    # ══════════════════════════════════════════════════════════════════
    phone_empresa = resultado.get("phone_empresa", "No encontrado")
    phone_valido = False

    if phone_empresa and phone_empresa != "No encontrado":
        phone_limpio = re.sub(r'[^\d+]', '', str(phone_empresa))

        es_invalido = (len(phone_limpio) < 7 or any(
            str(y) == phone_limpio for y in range(2020, 2030))
                       or len(set(phone_limpio.replace('+', ''))) <= 2)

        if es_invalido:
            logger.warning(
                f"[MERGE] phone_empresa descartado: {phone_empresa}")
            resultado['phone_empresa'] = "No encontrado"
        else:
            phone_valido = True

    if not phone_valido:
        regex_phones = regex_data.get('phones', [])
        for phone in regex_phones:
            phone_limpio = re.sub(r'[^\d+]', '', str(phone))
            if 7 <= len(phone_limpio) <= 15:
                if not any(str(y) == phone_limpio for y in range(2020, 2030)):
                    resultado['phone_empresa'] = phone
                    logger.info(f"[MERGE] Teléfono de regex: {phone}")
                    phone_valido = True
                    break

    if regex_data.get('phones') and len(regex_data['phones']) > 1:
        resultado['phones_adicionales'] = regex_data['phones'][1:4]

    # ══════════════════════════════════════════════════════════════════
    # WHATSAPP - Validación de país + fallback
    # ══════════════════════════════════════════════════════════════════
    wa_empresa = resultado.get('whatsapp_empresa', '')
    wa_valido = False

    codigos_pais_validos = [
        '54',
        '52',
        '57',
        '56',
        '51',
        '55',
        '598',
        '595',
        '593',
        '58',
        '591',
        '506',
        '507',
        '34',
        '1',
    ]

    def validar_whatsapp(numero):
        if not numero or numero == "No encontrado":
            return False
        num_limpio = re.sub(r'[^\d]', '', str(numero))
        if not (10 <= len(num_limpio) <= 15):
            return False
        for codigo in codigos_pais_validos:
            if num_limpio.startswith(codigo):
                return True
        return False

    if validar_whatsapp(wa_empresa):
        wa_valido = True
    else:
        wa_regex = regex_data.get('whatsapp', '')
        if validar_whatsapp(wa_regex):
            resultado['whatsapp_empresa'] = wa_regex
            logger.info(f"[MERGE] WhatsApp de regex: {wa_regex}")
            wa_valido = True
        else:
            resultado['whatsapp_empresa'] = "No encontrado"

    if not wa_valido:
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
    if not resultado.get('google_maps_url') and regex_data.get(
            'google_maps_url'):
        resultado['google_maps_url'] = regex_data['google_maps_url']

    # Ubicación - COMPLETA (address, city, province, country)
    # PRIORIDAD:
    # 1. GPT
    # 2. Contexto semántico
    # 3. Regex
    if not resultado.get('address') or resultado.get(
            'address') == 'No encontrado':
        if regex_data.get('address'):
            # Validar que sea una dirección real, no texto basura
            addr = regex_data['address']
            # Rechazar si es muy corto o tiene palabras sospechosas
            palabras_invalidas = [
                'aumentar', 'facturación', 'strongest', 'click', 'here', 'más',
                'more', 'ver'
            ]
            es_valida = (len(addr) > 10
                         and not any(p in addr.lower()
                                     for p in palabras_invalidas))
            if es_valida:
                resultado['address'] = addr
            else:
                logger.info(f"[MERGE] Address descartada (basura): {addr}")
        elif all_content:
            # Intentar extracción por contexto
            direccion_contexto = extraer_direccion_por_contexto(all_content)
            if direccion_contexto:
                resultado['address'] = direccion_contexto

    # City - prioridad: GPT > Regex (con validación anti-basura)
    city_actual = resultado.get('city', '')

    # Validar que city no sea basura
    if city_actual and city_actual != 'No encontrado':
        palabras_invalidas_city = [
            'pizza', 'comida', 'domicilio', 'delivery', 'envío', 'servicio',
            'producto', 'tienda', 'online', 'shop', 'alfajor', 'café',
            'coffee', 'restaurant', 'bar', 'empresa', 'company', 'negocio',
            'business', 'contacto', 'contact', 'inicio', 'home', 'about',
            'gratis', 'free', 'descuento', 'oferta', 'promo'
        ]
        city_lower = city_actual.lower()
        nombre_empresa = resultado.get('business_name', '').lower()

        # Rechazar si es basura
        es_invalida = (any(p in city_lower for p in palabras_invalidas_city)
                       or len(city_actual) > 40 or city_lower == nombre_empresa
                       or nombre_empresa in city_lower
                       or city_lower in nombre_empresa)

        if es_invalida:
            logger.info(f"[MERGE] City descartada: {city_actual}")
            resultado['city'] = 'No encontrado'

    # Fallback a regex
    if not resultado.get('city') or resultado.get('city') == 'No encontrado':
        if regex_data.get('city'):
            resultado['city'] = regex_data['city']

    # Province - prioridad: GPT > Regex
    if not resultado.get('province') or resultado.get(
            'province') == 'No encontrado':
        if regex_data.get('province'):
            resultado['province'] = regex_data['province']

    # Country - asegurar que tenga valor
    if not resultado.get('country') or resultado.get(
            'country') == 'No encontrado':
        # Prioridad 1: País inferido de la provincia detectada
        if regex_data.get('country_from_province'):
            resultado['country'] = regex_data['country_from_province']
            logger.info(f"[MERGE] País inferido de provincia: "
                        f"{resultado['country']}")
        # Prioridad 2: Inferir país del TLD del website
        elif website:
            tld = website.split('.')[-1].lower().replace('/', '')
            tld_pais = {
                # Latinoamérica
                'ar': 'Argentina',
                'mx': 'México',
                'co': 'Colombia',
                'cl': 'Chile',
                'pe': 'Perú',
                'br': 'Brasil',
                'uy': 'Uruguay',
                'py': 'Paraguay',
                'ec': 'Ecuador',
                've': 'Venezuela',
                'bo': 'Bolivia',
                'cr': 'Costa Rica',
                'pa': 'Panamá',
                'do': 'República Dominicana',
                'gt': 'Guatemala',
                'sv': 'El Salvador',
                'hn': 'Honduras',
                'ni': 'Nicaragua',
                'cu': 'Cuba',
                'pr': 'Puerto Rico',
                # Europa
                'es': 'España',
                'pt': 'Portugal',
                'uk': 'Reino Unido',
                'de': 'Alemania',
                'fr': 'Francia',
                'it': 'Italia',
                'nl': 'Países Bajos',
                'be': 'Bélgica',
                'at': 'Austria',
                'ch': 'Suiza',
                'pl': 'Polonia',
                'se': 'Suecia',
                'no': 'Noruega',
                'dk': 'Dinamarca',
                'fi': 'Finlandia',
                'ie': 'Irlanda',
                'gr': 'Grecia',
                'cz': 'República Checa',
                # Otros
                'us': 'Estados Unidos',
                'ca': 'Canadá',
                'au': 'Australia',
                'nz': 'Nueva Zelanda',
                'jp': 'Japón',
                'kr': 'Corea del Sur',
                'cn': 'China',
                'in': 'India',
                'za': 'Sudáfrica',
                'ae': 'Emiratos Árabes',
                'il': 'Israel',
                'ru': 'Rusia',
            }
            if tld in tld_pais:
                resultado['country'] = tld_pais[tld]
                logger.info(f"[MERGE] País inferido por TLD: {tld_pais[tld]}")

    if not resultado.get('horarios') and regex_data.get('horarios'):
        resultado['horarios'] = regex_data['horarios']

    # CUIT/CUIL
    if not resultado.get('cuit_cuil') and regex_data.get('cuit_cuil'):
        resultado['cuit_cuil'] = regex_data['cuit_cuil']

    # Business activity
    if not resultado.get('business_activity') and regex_data.get(
            'business_activity'):
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
        resultado['services_text'] = ', '.join(
            [s for s in services if s and s != 'No encontrado'])
    else:
        resultado['services_text'] = 'No encontrado'

    return resultado


async def extraer_paginas_secundarias(website: str) -> str:
    """
    Extrae contenido de páginas secundarias importantes:
    /contacto, /contact, /nosotros, /about, /equipo, /team, etc.
    """
    paginas = [
        '/contacto', '/contact', '/contactenos', '/contact-us', '/nosotros',
        '/about', '/about-us', '/quienes-somos', '/equipo', '/team',
        '/nuestro-equipo', '/our-team'
    ]

    contenido_extra = ""
    paginas_exitosas = 0
    max_paginas = 3  # Limitar para no demorar mucho

    for pagina in paginas:
        if paginas_exitosas >= max_paginas:
            break

        url = f"https://{website}{pagina}"

        try:
            async with httpx.AsyncClient(timeout=15.0,
                                         follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0 (Windows NT 10.0; "
                        "Win64; x64) AppleWebKit/537.36"
                    })

                if response.status_code == 200:
                    texto = response.text
                    # Verificar que no sea redirect a home
                    if len(texto) > 1000 and pagina.strip(
                            '/') in texto.lower():
                        contenido_extra += f"\n\n=== PÁGINA: {pagina} ===\n"
                        contenido_extra += texto[:10000]
                        paginas_exitosas += 1
                        logger.info(f"[SECUNDARIA] ✓ {pagina} - "
                                    f"{len(texto)} chars")
        except Exception as e:
            logger.debug(f"[SECUNDARIA] {pagina} no disponible: {e}")
            continue

    if paginas_exitosas > 0:
        logger.info(f"[SECUNDARIA] Extraídas {paginas_exitosas} páginas extra")

    return contenido_extra


async def buscar_whatsapp_en_html_crudo(website: str) -> str:
    """
    Hace GET directo al sitio y busca WhatsApp en el HTML crudo,
    incluyendo scripts JS donde los widgets guardan el número.

    Soporta: Elfsight, Joinchat, SocialChat, Click to Chat,
    WhatsApp Chat Button, y widgets genéricos.
    """
    if not website:
        return ""

    url = website if website.startswith("http") else f"https://{website}"

    logger.info(f"[WA-HTML] Buscando WhatsApp en HTML crudo: {url}")

    try:
        async with httpx.AsyncClient(timeout=15.0,
                                     follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120.0.0.0"
                })

            if response.status_code != 200:
                logger.warning(
                    f"[WA-HTML] Error {response.status_code} en {url}")
                return ""

            html = response.text
            logger.info(f"[WA-HTML] {len(html)} bytes descargados")

            # ═══════════════════════════════════════════════════════════
            # PATRONES PARA WIDGETS DE WHATSAPP EN SCRIPTS
            # Ordenados por especificidad (más específicos primero)
            # ═══════════════════════════════════════════════════════════

            patrones_widgets = [
                # wa.me links (el más confiable)
                r'wa\.me/(\d{10,15})',
                r'api\.whatsapp\.com/send\?phone=(\d{10,15})',
                r'web\.whatsapp\.com/send\?phone=(\d{10,15})',

                # Joinchat (WordPress plugin muy popular)
                r'joinchat[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'joinchat[^}]*?"telephone"[:\s]*"?\+?(\d{10,15})',
                r'"telephone"[:\s]*"\+?(\d{10,15})"[^}]*joinchat',

                # Elfsight WhatsApp Chat
                r'elfsight[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'elfsight[^}]*?"whatsapp"[:\s]*"?\+?(\d{10,15})',

                # Click to Chat / Social Chat
                r'click-to-chat[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'socialchat[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'social-chat[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',

                # WhatsApp Button / Chat Button genéricos
                r'whatsapp-button[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'whatsapp-chat[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'wc-button[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'wa-button[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',

                # WP WhatsApp / WhatsApp for WordPress
                r'wp-whatsapp[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',
                r'wc-whatsapp[^}]*?"phone"[:\s]*"?\+?(\d{10,15})',

                # Data attributes en HTML
                r'data-phone="?\+?(\d{10,15})"?',
                r'data-whatsapp="?\+?(\d{10,15})"?',
                r'data-wa-phone="?\+?(\d{10,15})"?',
                r'data-number="?\+?(\d{10,15})"?',
                r'data-telephone="?\+?(\d{10,15})"?',

                # JSON genérico en scripts (WhatsApp context)
                r'whatsapp[^}]{0,100}"phone"[\s]*:[\s]*"?\+?(\d{10,15})',
                r'"phone"[\s]*:[\s]*"?\+?(\d{10,15})"?[^}]{0,100}whatsapp',
                r'"whatsapp"[\s]*:[\s]*"?\+?(\d{10,15})"?',
                r'"wa_phone"[\s]*:[\s]*"?\+?(\d{10,15})"?',
                r'"whatsappNumber"[\s]*:[\s]*"?\+?(\d{10,15})"?',
                r'"waNumber"[\s]*:[\s]*"?\+?(\d{10,15})"?',
                r"'phone'[\s]*:[\s]*'?\+?(\d{10,15})'?",
            ]

            numeros_encontrados = []

            for patron in patrones_widgets:
                matches = re.findall(patron, html, re.IGNORECASE)
                for match in matches:
                    # Limpiar número
                    num = re.sub(r'[^\d]', '', match)

                    # Validar longitud (10-15 dígitos)
                    if len(num) < 10 or len(num) > 15:
                        continue

                    # ═══════════════════════════════════════════════════
                    # FILTRAR FIJOS ARGENTINOS
                    # Fijos AR: +54 + área (sin 9) = NO es WhatsApp
                    # Celulares AR: +54 9 + área = SÍ es WhatsApp
                    # ═══════════════════════════════════════════════════
                    if num.startswith('54') and len(num) >= 12:
                        if not num.startswith('549'):
                            logger.debug(
                                f"[WA-HTML] Descartando fijo AR: +{num}")
                            continue

                    # Evitar duplicados
                    if num not in numeros_encontrados:
                        numeros_encontrados.append(num)
                        logger.info(f"[WA-HTML] ✓ WhatsApp encontrado: +{num}")

            if numeros_encontrados:
                return '+' + numeros_encontrados[0]

            logger.info("[WA-HTML] No se encontró WhatsApp en HTML")
            return ""

    except httpx.TimeoutException:
        logger.warning(f"[WA-HTML] Timeout en {url}")
        return ""
    except Exception as e:
        logger.error(f"[WA-HTML] Error: {e}")
        return ""


async def buscar_whatsapp_externo(website: str, empresa: str = "") -> str:
    """
    Busca WhatsApp de la empresa en fuentes externas (directorios).
    Útil cuando el widget está en JS y no lo capturamos.
    """
    if not TAVILY_API_KEY:
        logger.warning("[WA-EXTERNO] No hay TAVILY_API_KEY")
        return ""

    dominio = website.replace("https://",
                              "").replace("http://",
                                          "").replace("www.", "").split("/")[0]

    queries = [
        f'"{dominio}" whatsapp contacto',
        f'"{dominio}" teléfono celular',
    ]

    if empresa and empresa != "No encontrado":
        queries.insert(0, f'"{empresa}" whatsapp')

    for query in queries:
        logger.info(f"[WA-EXTERNO] Buscando: {query}")

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.tavily.com/search",
                                             json={
                                                 "api_key": TAVILY_API_KEY,
                                                 "query": query,
                                                 "search_depth": "basic",
                                                 "max_results": 10,
                                                 "include_answer": False
                                             })

                if response.status_code != 200:
                    continue

                data = response.json()
                results = data.get("results", [])

                wa_patterns = [
                    r'wa\.me/(\d{10,15})',
                    r'whatsapp\.com/send\?phone=(\d{10,15})',
                    r'phone\s+(?:number\s+)?(?:is\s+)?\+?(\d[\d\s\-]{9,14})',
                    r'teléfono[:\s]+\+?(\d[\d\s\-]{9,14})',
                    r'celular[:\s]+\+?(\d[\d\s\-]{9,14})',
                    r'whatsapp[:\s]+\+?(\d[\d\s\-]{9,14})',
                    r'\+(\d{2,4}\s?\d{6,12})',
                ]

                for r in results:
                    texto = f"{r.get('title', '')} {r.get('content', '')}"
                    url = r.get('url', '')

                    for pattern in wa_patterns:
                        matches = re.findall(pattern, texto, re.IGNORECASE)
                        for match in matches:
                            num = re.sub(r'[^\d]', '', match)

                            if len(num) < 10 or len(num) > 15:
                                continue

                            # Filtrar fijos argentinos
                            if num.startswith('54') and len(num) >= 12:
                                if not num.startswith('549'):
                                    continue

                            # Validar código de país (LATAM + España + USA)
                            codigos_validos = [
                                '54', '52', '57', '56', '51', '55',
                                '598', '595', '593', '58', '591',
                                '506', '507', '34', '1',
                            ]
                            es_valido = any(
                                num.startswith(c) for c in codigos_validos
                            )
                            if not es_valido:
                                logger.debug(
                                    f"[WA-EXTERNO] Descartado (país): +{num}"
                                )
                                continue

                            resultado = '+' + num
                            logger.info(
                                f"[WA-EXTERNO] ✓ Encontrado: {resultado}")
                            return resultado

        except Exception as e:
            logger.error(f"[WA-EXTERNO] Error: {e}")
            continue

    logger.info("[WA-EXTERNO] No encontrado en fuentes externas")
    return ""


async def extract_web_data(website: str, nombre_contacto: str = "", phone: str = None) -> dict:
    """
    Pipeline completo de extracción web.
    Orden: Firecrawl → Jina → HTTP directo → Tavily (fallback) → Regex → GPT-4o → Merge

    Args:
        website: URL del sitio web
        nombre_contacto: Nombre del contacto para buscar cargo asociado
        phone: Número de WhatsApp (opcional, para typing indicator)
    """
    logger.info(f"[EXTRACTOR] ========== Iniciando: {website} ==========")
    
    # Activar typing indicator
    typing_active = False
    if phone:
        try:
            from services.whatsapp import send_typing_indicator
            await send_typing_indicator(phone, typing_on=True)
            typing_active = True
        except Exception as e:
            logger.warning(f"[EXTRACTOR] Error activando typing indicator: {e}")

    try:
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

        # 5. Contenido final (solo de la web de la empresa)
        all_content = main_content

        if len(all_content) > 20000:
            all_content = all_content[:20000]

        # Fallback 4: Tavily
        if not all_content:
            logger.info(f"[TAVILY] Fallback: extrayendo {website}...")
            tavily_content = await fetch_with_tavily(website_clean)
            if tavily_content:
                all_content = tavily_content
                logger.info(
                    f"[TAVILY] ✓ {len(tavily_content)} caracteres extraídos")

        if not all_content:
            logger.warning(f"[EXTRACTOR] Los 4 métodos fallaron para {website}")
            resultado = {
                "business_name": "No encontrado",
                "business_description": "No encontrado",
                "website": website_full,
                "extraction_status": "failed"
            }
            # Desactivar typing antes de retornar
            if phone and typing_active:
                try:
                    from services.whatsapp import send_typing_indicator
                    await send_typing_indicator(phone, typing_on=False)
                except Exception as e:
                    logger.warning(f"[EXTRACTOR] Error desactivando typing indicator: {e}")
            return resultado

        logger.info(f"[EXTRACTOR] Contenido total: {len(all_content)} chars")

        # 8. Extraer título de la página (para detectar ciudad)
        titulo_pagina = ""
        if http_content:
            titulo_pagina = extraer_titulo_pagina(http_content)
            if titulo_pagina:
                logger.info(f"[TITULO] Extraído: {titulo_pagina}")

        # 9. Extracción Regex
        logger.info(f"[EXTRACTOR] Aplicando regex...")
        regex_data = extract_with_regex(all_content)

        # 10. Extracción GPT (con título para detectar ciudad)
        logger.info(f"[GPT] Extrayendo datos estructurados...")
        gpt_data = await extract_with_gpt(all_content, website_clean,
                                          titulo_pagina)

        # 10. Merge de resultados (pasar all_content para extracción por contexto)
        resultado = merge_results(gpt_data, regex_data, "",
                                  website_full, all_content)

        # ═══════════════════════════════════════════════════════════════
        # 10B. DETECCIÓN DE CARGO desde sección Equipo/Team
        # ═══════════════════════════════════════════════════════════════
        if secundarias_content or main_content:
            # Buscar cargo en contenido de páginas de equipo
            contenido_equipo = secundarias_content + "\n" + main_content
            # Usar nombre_contacto del parámetro o del resultado
            nombre_para_cargo = nombre_contacto or resultado.get(
                'contact_name', '')

            cargo = extraer_cargo_de_equipo(contenido_equipo, nombre_para_cargo)

            if cargo:
                resultado['cargo_detectado'] = cargo
                logger.info(f"[CARGO] ✓ Detectado: {cargo}")
            else:
                resultado['cargo_detectado'] = 'No encontrado'

        # ═══════════════════════════════════════════════════════════════
        # BÚSQUEDA DE WHATSAPP EN HTML CRUDO (widgets JS)
        # Primero intentamos extraer del HTML directo (más confiable)
        # ═══════════════════════════════════════════════════════════════
        # Búsqueda de WhatsApp solo en HTML de la web (widgets JS)
        if resultado.get('_necesita_wa_externo'):
            wa_html = await buscar_whatsapp_en_html_crudo(website_clean)
            if wa_html:
                resultado['whatsapp_empresa'] = wa_html
                resultado['whatsapp_source'] = 'html_widget'
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
                apellido=apellido)

            if linkedin_en_web:
                logger.info(f"[LINKEDIN-WEB] ✓ Encontrados en web: "
                            f"{len(linkedin_en_web)}")
                linkedin_encontrados.extend(linkedin_en_web)

        # 2. Buscar LinkedIn por email
        email = resultado.get('email_principal', '')
        if email and email != 'No encontrado' and '@' in email:
            linkedin_por_email = await buscar_linkedin_por_email(email)
            if linkedin_por_email and linkedin_por_email not in linkedin_encontrados:
                logger.info(f"[LINKEDIN-EMAIL] ✓ Encontrado: {linkedin_por_email}")
                linkedin_encontrados.append(linkedin_por_email)

        # 3. Guardar resultados si encontramos algo
        if linkedin_encontrados:
            # Si ya hay linkedin_personal, agregar los nuevos
            actual = resultado.get('linkedin_personal_web', '')
            if actual and actual != 'No encontrado':
                todos = [actual] + [u for u in linkedin_encontrados if u != actual]
            else:
                todos = linkedin_encontrados

            # Guardar máximo 3 URLs separadas por |
            resultado['linkedin_personal_web'] = ' | '.join(todos[:3])
            logger.info(f"[LINKEDIN] Total en web: "
                        f"{resultado['linkedin_personal_web']}")

        resultado['website'] = website_full
        resultado['extraction_status'] = 'success'

        logger.info(f"[EXTRACTOR] ========== Completado ==========")

        # Desactivar typing antes de retornar
        if phone and typing_active:
            try:
                from services.whatsapp import send_typing_indicator
                await send_typing_indicator(phone, typing_on=False)
            except Exception as e:
                logger.warning(f"[EXTRACTOR] Error desactivando typing indicator: {e}")

        return resultado
    
    except Exception as e:
        # Desactivar typing en caso de error
        if phone and typing_active:
            try:
                from services.whatsapp import send_typing_indicator
                await send_typing_indicator(phone, typing_on=False)
            except Exception as e2:
                logger.warning(f"[EXTRACTOR] Error desactivando typing indicator: {e2}")
        raise
