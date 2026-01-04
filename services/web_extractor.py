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
    email_basura = [
        'example', 'sentry', 'wixpress', '.png', '.jpg', 'website.com',
        'domain.com', 'email.com', 'test.com', 'sample', 'yourcompany',
        'yourdomain', 'company.com', 'mail.com', 'email@', '@example',
        'noreply', 'no-reply', 'donotreply', 'unsubscribe', 'wordpress',
        'schema.org', 'w3.org', 'sentry.io', 'cloudflare', 'google.com',
        'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
        'support@wix', 'privacy@', 'abuse@', 'postmaster@', 'webmaster@'
    ]

    for email in emails_found:
        email_lower = email.lower()
        if not any(x in email_lower for x in email_basura):
            emails_filtered.append(email_lower)

    regex_extract['emails'] = list(set(emails_filtered))[:5]
    logger.info(f"[REGEX] Emails encontrados: {regex_extract['emails']}")

    # ═══════════════════════════════════════════════════════════════════
    # DETECCIÓN DE CARGO/ROL ASOCIADO A EMAIL
    # ═══════════════════════════════════════════════════════════════════
    cargos_keywords = [
        # Español
        'gerente', 'director', 'ceo', 'cfo', 'cto', 'coo', 'presidente',
        'vicepresidente', 'fundador', 'cofundador', 'socio', 'dueño',
        'propietario', 'jefe', 'responsable', 'coordinador', 'supervisor',
        'encargado', 'administrador', 'ejecutivo', 'comercial', 'ventas',
        'marketing', 'recursos humanos', 'rrhh', 'finanzas', 'operaciones',
        'general manager', 'managing director',
        # Inglés
        'manager', 'director', 'chief', 'head', 'lead', 'senior',
        'founder', 'co-founder', 'owner', 'partner', 'principal',
        'executive', 'officer', 'vp', 'vice president', 'president',
        # Portugués
        'gerente', 'diretor', 'sócio', 'proprietário', 'coordenador',
    ]

    # Buscar cargo cerca de cada email encontrado
    for email in regex_extract['emails'][:3]:  # Solo primeros 3
        # Buscar contexto alrededor del email (200 chars antes y después)
        email_pos = all_content.lower().find(email)
        if email_pos > 0:
            contexto_inicio = max(0, email_pos - 200)
            contexto_fin = min(len(all_content), email_pos + 200)
            contexto = all_content[contexto_inicio:contexto_fin].lower()

            for cargo in cargos_keywords:
                if cargo in contexto:
                    # Extraer el cargo con formato
                    cargo_pattern = rf'({cargo}[a-záéíóúñ\s]{{0,30}})'
                    cargo_match = re.search(cargo_pattern, contexto, 
                                           re.IGNORECASE)
                    if cargo_match:
                        cargo_encontrado = cargo_match.group(1).strip()
                        cargo_encontrado = ' '.join(cargo_encontrado.split())
                        if not regex_extract.get('cargo_detectado'):
                            regex_extract['cargo_detectado'] = cargo_encontrado
                            regex_extract['email_con_cargo'] = email
                            logger.info(f"[REGEX] ✓ Cargo '{cargo_encontrado}' "
                                       f"asociado a {email}")
                        break

    # ═══════════════════════════════════════════════════════════════════
    # 2. TELÉFONOS
    # ═══════════════════════════════════════════════════════════════════
    phone_patterns = [
        r'href=["\']tel:([^"\']+)',
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}',
        r'\(\d{2,5}\)[\s.-]?\d{3,4}[\s.-]?\d{3,4}', r'\b\d{4}[\s.-]\d{4}\b'
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
    # 7. DIRECCIONES (Argentina)
    # ═══════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════
    # 7. DIRECCIÓN/ADDRESS (Internacional)
    # ═══════════════════════════════════════════════════════════════════
    direccion_patterns = [
        # Español con prefijo: Av. / Avenida / Calle / Bv. / Boulevard + nombre + número
        r'(?:Av\.?|Avenida|Calle|Bv\.?|Boulevard|Paseo|Pje\.?|Pasaje|'
        r'Diagonal|Ruta|Camino)\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s\.]+\s+\d{1,5}'
        r'(?:\s*(?:bis|piso|dto|depto|of|oficina|local|pb|ep)\.?\s*\d*)?',

        # Español sin prefijo: Nombre + número (+ bis/piso/etc)
        r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-Za-záéíóúñ]+)*\s+\d{1,5}'
        r'(?:\s*bis|\s*piso\s*\d+|\s*(?:dto|depto)\.?\s*\d+)?',

        # Inglés flexible: número + texto + ST/AVE/RD/etc
        r'\d{1,5}\s+[A-Z0-9\s]+(?:ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|'
        r'BOULEVARD|DR|DRIVE|LN|LANE|WAY|PL|PLACE|CT|COURT|CIR|CIRCLE|'
        r'HWY|HIGHWAY|UNIT|SUITE|STE)',

        # Inglés tradicional: 123 Main Street / 456 Fifth Avenue
        r'\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}(?:Street|St\.?|Avenue|Ave\.?|'
        r'Road|Rd\.?|Boulevard|Blvd\.?|Drive|Dr\.?|Lane|Ln\.?|Way|Place|'
        r'Pl\.?|Court|Ct\.?|Circle|Cir\.?|Highway|Hwy\.?)',

        # Portugués: Rua / Av. + nombre + número
        r'(?:Rua|Av\.?|Avenida|Alameda|Travessa|Praça|Largo)\s+'
        r'[A-ZÁÉÍÓÚÑÃÕa-záéíóúñãõ\s\.]+[,\s]+(?:n[º°]?\s*)?\d{1,5}',

        # Francés: Rue / Avenue / Boulevard + nombre + numéro
        r'(?:Rue|Avenue|Boulevard|Place|Allée|Chemin|Impasse)\s+'
        r'[A-ZÀÂÄÇÉÈÊËÎÏÔÙÛÜŸa-zàâäçéèêëîïôùûüÿ\s\-]+[,\s]+\d{1,5}',

        # Alemán: Straße / Str. / Weg + nombre + número
        r'[A-ZÄÖÜa-zäöüß]+(?:straße|str\.?|weg|platz|gasse|ring|allee)\s*'
        r'\d{1,5}[a-z]?',

        # Italiano: Via / Viale / Piazza + nombre + numero
        r'(?:Via|Viale|Piazza|Corso|Largo|Vicolo)\s+'
        r'[A-ZÀÈÉÌÒÙa-zàèéìòù\s\.]+[,\s]+(?:n[°\.]?\s*)?\d{1,5}',

        # Con código postal explícito
        r'(?:CP|C\.P\.|Código Postal|Zip|ZIP|Postal Code|CEP|CAP|PLZ)[:\s]*'
        r'[\d\-]{4,10}',

        # Dirección con CP: cualquier texto + CP/código + número
        r'[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s\.,]+(?:CP|C\.P\.)[:\s]*\d{4,6}',
    ]

    for pattern in direccion_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match and len(match.group(0)) > 10:
            direccion = match.group(0).strip()
            # Limpiar espacios múltiples
            direccion = ' '.join(direccion.split())
            regex_extract['address'] = direccion
            logger.info(f"[REGEX] ✓ Dirección encontrada: {direccion}")
            break

    # ═══════════════════════════════════════════════════════════════════
    # PROVINCIAS/ESTADOS/REGIONES (Internacional completo)
    # ═══════════════════════════════════════════════════════════════════

    # Argentina - Todas las provincias
    provincias_ar = [
        'Buenos Aires', 'Córdoba', 'Cordoba', 'Santa Fe', 'Mendoza', 
        'Tucumán', 'Tucuman', 'Entre Ríos', 'Entre Rios', 'Salta', 
        'Misiones', 'Chaco', 'Corrientes', 'Santiago del Estero', 
        'San Juan', 'Jujuy', 'Río Negro', 'Rio Negro', 'Neuquén', 
        'Neuquen', 'Formosa', 'Chubut', 'San Luis', 'Catamarca', 
        'La Rioja', 'La Pampa', 'Santa Cruz', 'Tierra del Fuego', 
        'CABA', 'Capital Federal', 'Ciudad Autónoma', 'Ciudad Autonoma',
        'Rosario', 'Mar del Plata', 'La Plata', 'Bahía Blanca'
    ]

    # México - Estados y ciudades principales
    estados_mx = [
        'Ciudad de México', 'CDMX', 'Estado de México', 'Jalisco',
        'Nuevo León', 'Nuevo Leon', 'Puebla', 'Guanajuato', 'Chihuahua',
        'Veracruz', 'Baja California', 'Querétaro', 'Queretaro',
        'Yucatán', 'Yucatan', 'Quintana Roo', 'Monterrey', 'Guadalajara',
        'Tijuana', 'Cancún', 'Cancun', 'Aguascalientes', 'Morelos',
        'Oaxaca', 'Chiapas', 'Tabasco', 'Campeche', 'Sonora', 'Sinaloa',
        'Durango', 'Zacatecas', 'San Luis Potosí', 'San Luis Potosi',
        'Tamaulipas', 'Coahuila', 'Nayarit', 'Colima', 'Michoacán',
        'Michoacan', 'Guerrero', 'Hidalgo', 'Tlaxcala'
    ]

    # Colombia - Departamentos y ciudades
    deptos_co = [
        'Bogotá', 'Bogota', 'Cundinamarca', 'Antioquia', 'Medellín',
        'Medellin', 'Valle del Cauca', 'Cali', 'Atlántico', 'Atlantico',
        'Barranquilla', 'Santander', 'Bolívar', 'Bolivar', 'Cartagena',
        'Norte de Santander', 'Cúcuta', 'Cucuta', 'Tolima', 'Ibagué',
        'Huila', 'Neiva', 'Risaralda', 'Pereira', 'Caldas', 'Manizales',
        'Meta', 'Villavicencio', 'Nariño', 'Narino', 'Pasto', 'Cauca',
        'Popayán', 'Popayan', 'Córdoba', 'Montería', 'Monteria',
        'Magdalena', 'Santa Marta', 'Cesar', 'Valledupar', 'Boyacá',
        'Boyaca', 'Tunja', 'Quindío', 'Quindio', 'Armenia'
    ]

    # Chile - Regiones y ciudades
    regiones_cl = [
        'Santiago', 'Región Metropolitana', 'Region Metropolitana',
        'Valparaíso', 'Valparaiso', 'Viña del Mar', 'Biobío', 'Biobio',
        'Concepción', 'Concepcion', 'Antofagasta', 'La Serena', 
        'Coquimbo', 'Temuco', 'La Araucanía', 'La Araucania',
        'Puerto Montt', 'Los Lagos', 'Talca', 'Maule', 'Rancagua',
        "O'Higgins", 'Arica', 'Iquique', 'Tarapacá', 'Tarapaca',
        'Punta Arenas', 'Magallanes', 'Valdivia', 'Los Ríos', 'Los Rios'
    ]

    # Perú - Departamentos y ciudades
    deptos_pe = [
        'Lima', 'Arequipa', 'Trujillo', 'La Libertad', 'Chiclayo',
        'Lambayeque', 'Piura', 'Cusco', 'Cuzco', 'Iquitos', 'Loreto',
        'Huancayo', 'Junín', 'Junin', 'Tacna', 'Puno', 'Cajamarca',
        'Ayacucho', 'Ica', 'Callao', 'Ancash', 'Huaraz', 'Moquegua',
        'Tumbes', 'Madre de Dios', 'Puerto Maldonado', 'Amazonas',
        'San Martín', 'San Martin', 'Tarapoto', 'Ucayali', 'Pucallpa'
    ]

    # Ecuador - Provincias y ciudades
    provincias_ec = [
        'Quito', 'Pichincha', 'Guayaquil', 'Guayas', 'Cuenca', 'Azuay',
        'Ambato', 'Tungurahua', 'Manta', 'Manabí', 'Manabi', 'Machala',
        'El Oro', 'Loja', 'Esmeraldas', 'Ibarra', 'Imbabura', 'Riobamba',
        'Chimborazo', 'Santo Domingo', 'Portoviejo', 'Durán', 'Duran',
        'Latacunga', 'Cotopaxi', 'Orellana', 'Sucumbíos', 'Sucumbios'
    ]

    # Venezuela - Estados y ciudades
    estados_ve = [
        'Caracas', 'Distrito Capital', 'Miranda', 'Maracaibo', 'Zulia',
        'Valencia', 'Carabobo', 'Barquisimeto', 'Lara', 'Maracay',
        'Aragua', 'Puerto La Cruz', 'Anzoátegui', 'Anzoategui',
        'Ciudad Guayana', 'Bolívar', 'Bolivar', 'Mérida', 'Merida',
        'San Cristóbal', 'San Cristobal', 'Táchira', 'Tachira',
        'Barinas', 'Maturín', 'Maturin', 'Monagas', 'Portuguesa',
        'Falcón', 'Falcon', 'Coro', 'Nueva Esparta', 'Margarita'
    ]

    # Bolivia - Departamentos y ciudades
    deptos_bo = [
        'La Paz', 'Santa Cruz', 'Santa Cruz de la Sierra', 'Cochabamba',
        'Sucre', 'Chuquisaca', 'Oruro', 'Potosí', 'Potosi', 'Tarija',
        'Trinidad', 'Beni', 'Cobija', 'Pando'
    ]

    # Paraguay - Departamentos y ciudades
    deptos_py = [
        'Asunción', 'Asuncion', 'Ciudad del Este', 'Alto Paraná',
        'Alto Parana', 'Encarnación', 'Encarnacion', 'Itapúa', 'Itapua',
        'San Lorenzo', 'Luque', 'Central', 'Pedro Juan Caballero',
        'Amambay', 'Concepción', 'Concepcion'
    ]

    # Uruguay - Departamentos y ciudades
    deptos_uy = [
        'Montevideo', 'Punta del Este', 'Maldonado', 'Salto',
        'Paysandú', 'Paysandu', 'Rivera', 'Las Piedras', 'Canelones',
        'Colonia', 'Colonia del Sacramento', 'Tacuarembó', 'Tacuarembo',
        'Melo', 'Cerro Largo', 'Durazno', 'Florida', 'Rocha'
    ]

    # Brasil - Estados y ciudades principales
    estados_br = [
        'São Paulo', 'Sao Paulo', 'Rio de Janeiro', 'Minas Gerais',
        'Belo Horizonte', 'Bahia', 'Salvador', 'Paraná', 'Parana',
        'Curitiba', 'Rio Grande do Sul', 'Porto Alegre', 'Pernambuco',
        'Recife', 'Ceará', 'Ceara', 'Fortaleza', 'Santa Catarina',
        'Florianópolis', 'Florianopolis', 'Goiás', 'Goias', 'Goiânia',
        'Goiania', 'Brasília', 'Brasilia', 'Distrito Federal',
        'Pará', 'Para', 'Belém', 'Belem', 'Amazonas', 'Manaus',
        'Maranhão', 'Maranhao', 'São Luís', 'Sao Luis', 'Espírito Santo',
        'Espirito Santo', 'Vitória', 'Vitoria', 'Rio Grande do Norte',
        'Natal', 'Paraíba', 'Paraiba', 'João Pessoa', 'Joao Pessoa',
        'Alagoas', 'Maceió', 'Maceio', 'Piauí', 'Piaui', 'Teresina',
        'Sergipe', 'Aracaju', 'Mato Grosso', 'Cuiabá', 'Cuiaba',
        'Mato Grosso do Sul', 'Campo Grande', 'Tocantins', 'Palmas',
        'Rondônia', 'Rondonia', 'Porto Velho', 'Acre', 'Rio Branco',
        'Amapá', 'Amapa', 'Macapá', 'Macapa', 'Roraima', 'Boa Vista'
    ]

    # Centroamérica y Caribe
    centroamerica = [
        # Guatemala
        'Guatemala', 'Ciudad de Guatemala', 'Quetzaltenango', 'Escuintla',
        # Honduras
        'Honduras', 'Tegucigalpa', 'San Pedro Sula', 'La Ceiba',
        # El Salvador
        'El Salvador', 'San Salvador', 'Santa Ana', 'San Miguel',
        # Nicaragua
        'Nicaragua', 'Managua', 'León', 'Leon', 'Granada', 'Masaya',
        # Costa Rica
        'Costa Rica', 'San José', 'San Jose', 'Alajuela', 'Cartago',
        'Heredia', 'Limón', 'Limon', 'Puntarenas', 'Guanacaste',
        # Panamá
        'Panamá', 'Panama', 'Ciudad de Panamá', 'Ciudad de Panama',
        'Colón', 'Colon', 'David', 'Chiriquí', 'Chiriqui',
        # Cuba
        'Cuba', 'La Habana', 'Habana', 'Santiago de Cuba', 'Camagüey',
        'Camaguey', 'Holguín', 'Holguin', 'Varadero',
        # República Dominicana
        'República Dominicana', 'Republica Dominicana', 'Santo Domingo',
        'Santiago de los Caballeros', 'Punta Cana', 'Puerto Plata',
        # Puerto Rico
        'Puerto Rico', 'San Juan', 'Bayamón', 'Bayamon', 'Carolina',
        'Ponce', 'Caguas', 'Mayagüez', 'Mayaguez'
    ]

    # España - Comunidades y ciudades
    ccaa_es = [
        'Madrid', 'Barcelona', 'Cataluña', 'Catalunya', 'Andalucía',
        'Andalucia', 'Sevilla', 'Málaga', 'Malaga', 'Granada', 'Almería',
        'Almeria', 'Cádiz', 'Cadiz', 'Córdoba', 'Cordoba', 'Jaén', 'Jaen',
        'Huelva', 'Valencia', 'Comunidad Valenciana', 'Alicante',
        'Castellón', 'Castellon', 'País Vasco', 'Pais Vasco', 'Euskadi',
        'Bilbao', 'San Sebastián', 'San Sebastian', 'Vitoria', 'Álava',
        'Alava', 'Vizcaya', 'Guipúzcoa', 'Guipuzcoa', 'Galicia',
        'La Coruña', 'A Coruña', 'Vigo', 'Santiago de Compostela',
        'Pontevedra', 'Ourense', 'Lugo', 'Castilla y León', 'Valladolid',
        'León', 'Salamanca', 'Burgos', 'Palencia', 'Zamora', 'Segovia',
        'Ávila', 'Avila', 'Soria', 'Castilla-La Mancha', 'Toledo',
        'Ciudad Real', 'Albacete', 'Cuenca', 'Guadalajara', 'Aragón',
        'Aragon', 'Zaragoza', 'Huesca', 'Teruel', 'Murcia', 'Cartagena',
        'Extremadura', 'Badajoz', 'Cáceres', 'Caceres', 'Navarra',
        'Pamplona', 'La Rioja', 'Logroño', 'Logrono', 'Cantabria',
        'Santander', 'Asturias', 'Oviedo', 'Gijón', 'Gijon',
        'Islas Baleares', 'Baleares', 'Mallorca', 'Palma', 'Ibiza',
        'Menorca', 'Islas Canarias', 'Canarias', 'Las Palmas',
        'Gran Canaria', 'Tenerife', 'Santa Cruz de Tenerife',
        'Lanzarote', 'Fuerteventura', 'Ceuta', 'Melilla'
    ]

    # Portugal
    portugal = [
        'Portugal', 'Lisboa', 'Lisbon', 'Porto', 'Oporto', 'Braga',
        'Coimbra', 'Amadora', 'Funchal', 'Madeira', 'Setúbal', 'Setubal',
        'Almada', 'Aveiro', 'Évora', 'Evora', 'Faro', 'Algarve',
        'Leiria', 'Viseu', 'Guimarães', 'Guimaraes', 'Açores', 'Acores'
    ]

    # Francia
    francia = [
        'Francia', 'France', 'París', 'Paris', 'Marsella', 'Marseille',
        'Lyon', 'Toulouse', 'Niza', 'Nice', 'Nantes', 'Estrasburgo',
        'Strasbourg', 'Montpellier', 'Burdeos', 'Bordeaux', 'Lille',
        'Rennes', 'Reims', 'Le Havre', 'Toulon', 'Grenoble', 'Dijon',
        'Angers', 'Nîmes', 'Nimes', 'Île-de-France', 'Ile-de-France',
        'Provenza', 'Provence', 'Normandía', 'Normandie', 'Bretaña',
        'Bretagne', 'Alsacia', 'Alsace', 'Aquitania', 'Aquitaine'
    ]

    # Alemania
    alemania = [
        'Alemania', 'Germany', 'Deutschland', 'Berlín', 'Berlin',
        'Múnich', 'Munich', 'München', 'Hamburgo', 'Hamburg',
        'Fráncfort', 'Frankfurt', 'Colonia', 'Köln', 'Cologne',
        'Stuttgart', 'Düsseldorf', 'Dusseldorf', 'Dortmund', 'Essen',
        'Leipzig', 'Bremen', 'Dresde', 'Dresden', 'Hannover', 'Núremberg',
        'Nuremberg', 'Nürnberg', 'Baviera', 'Bayern', 'Bavaria',
        'Baden-Württemberg', 'Baden-Wurttemberg', 'Hessen', 'Sajonia',
        'Sachsen', 'Renania', 'Nordrhein-Westfalen'
    ]

    # Italia
    italia = [
        'Italia', 'Italy', 'Roma', 'Rome', 'Milán', 'Milan', 'Milano',
        'Nápoles', 'Napoli', 'Naples', 'Turín', 'Turin', 'Torino',
        'Palermo', 'Génova', 'Genova', 'Genoa', 'Bolonia', 'Bologna',
        'Florencia', 'Florence', 'Firenze', 'Venecia', 'Venice', 'Venezia',
        'Bari', 'Catania', 'Verona', 'Padua', 'Padova', 'Trieste',
        'Lombardía', 'Lombardia', 'Piamonte', 'Piemonte', 'Lazio',
        'Campania', 'Sicilia', 'Sicily', 'Cerdeña', 'Sardegna', 'Toscana',
        'Emilia-Romaña', 'Emilia-Romagna', 'Véneto', 'Veneto'
    ]

    # Reino Unido
    reino_unido = [
        'Reino Unido', 'United Kingdom', 'UK', 'Inglaterra', 'England',
        'Londres', 'London', 'Manchester', 'Birmingham', 'Leeds',
        'Glasgow', 'Liverpool', 'Bristol', 'Sheffield', 'Edinburgh',
        'Edimburgo', 'Cardiff', 'Belfast', 'Newcastle', 'Nottingham',
        'Southampton', 'Leicester', 'Escocia', 'Scotland', 'Gales',
        'Wales', 'Irlanda del Norte', 'Northern Ireland'
    ]

    # Otros países europeos
    otros_europa = [
        # Países Bajos
        'Países Bajos', 'Paises Bajos', 'Netherlands', 'Holanda', 'Holland',
        'Ámsterdam', 'Amsterdam', 'Róterdam', 'Rotterdam', 'La Haya',
        'The Hague', 'Utrecht', 'Eindhoven',
        # Bélgica
        'Bélgica', 'Belgica', 'Belgium', 'Bruselas', 'Brussels', 'Bruxelles',
        'Amberes', 'Antwerp', 'Antwerpen', 'Gante', 'Ghent', 'Gent', 'Lieja',
        # Suiza
        'Suiza', 'Switzerland', 'Schweiz', 'Zúrich', 'Zurich', 'Zürich',
        'Ginebra', 'Geneva', 'Genève', 'Basilea', 'Basel', 'Berna', 'Bern',
        'Lausana', 'Lausanne',
        # Austria
        'Austria', 'Viena', 'Vienna', 'Wien', 'Salzburgo', 'Salzburg',
        'Innsbruck', 'Graz', 'Linz',
        # Irlanda
        'Irlanda', 'Ireland', 'Dublín', 'Dublin', 'Cork', 'Galway', 'Limerick'
    ]

    # USA - Estados y ciudades principales
    estados_us = [
        'California', 'CA', 'New York', 'NY', 'Texas', 'TX', 'Florida',
        'FL', 'Illinois', 'IL', 'Pennsylvania', 'PA', 'Ohio', 'OH',
        'Georgia', 'GA', 'North Carolina', 'NC', 'Michigan', 'MI',
        'New Jersey', 'NJ', 'Virginia', 'VA', 'Washington', 'WA',
        'Arizona', 'AZ', 'Massachusetts', 'MA', 'Colorado', 'CO',
        'Tennessee', 'TN', 'Indiana', 'IN', 'Missouri', 'MO',
        'Maryland', 'MD', 'Wisconsin', 'WI', 'Minnesota', 'MN',
        'Oregon', 'OR', 'South Carolina', 'SC', 'Kentucky', 'KY',
        'Louisiana', 'LA', 'Alabama', 'AL', 'Oklahoma', 'OK',
        'Connecticut', 'CT', 'Utah', 'UT', 'Iowa', 'IA', 'Nevada', 'NV',
        'Arkansas', 'AR', 'Mississippi', 'MS', 'Kansas', 'KS',
        'New Mexico', 'NM', 'Nebraska', 'NE', 'Idaho', 'ID',
        'West Virginia', 'WV', 'Hawaii', 'HI', 'New Hampshire', 'NH',
        'Maine', 'ME', 'Montana', 'MT', 'Rhode Island', 'RI',
        'Delaware', 'DE', 'South Dakota', 'SD', 'North Dakota', 'ND',
        'Alaska', 'AK', 'Vermont', 'VT', 'Wyoming', 'WY',
        # Ciudades principales
        'Miami', 'Los Angeles', 'LA', 'Chicago', 'Houston', 'Phoenix',
        'San Francisco', 'Seattle', 'Boston', 'Atlanta', 'Denver',
        'Dallas', 'San Diego', 'San Antonio', 'Austin', 'Jacksonville',
        'San Jose', 'Fort Worth', 'Columbus', 'Charlotte', 'Indianapolis',
        'Detroit', 'El Paso', 'Memphis', 'Baltimore', 'Milwaukee',
        'Albuquerque', 'Tucson', 'Nashville', 'Portland', 'Las Vegas',
        'Louisville', 'Oklahoma City', 'Kansas City', 'Tampa',
        'New Orleans', 'Cleveland', 'Pittsburgh', 'Raleigh', 'Orlando',
        'Salt Lake City', 'Sacramento', 'St. Louis', 'Minneapolis'
    ]

    # Canadá
    canada = [
        'Canadá', 'Canada', 'Toronto', 'Ontario', 'Montreal', 'Quebec',
        'Québec', 'Vancouver', 'British Columbia', 'Columbia Británica',
        'Calgary', 'Alberta', 'Edmonton', 'Ottawa', 'Winnipeg', 'Manitoba',
        'Halifax', 'Nova Scotia', 'Victoria', 'Saskatchewan', 'Saskatoon',
        'Regina', 'New Brunswick', 'Newfoundland', 'Prince Edward Island'
    ]

    # Australia y Nueva Zelanda
    oceania = [
        'Australia', 'Sídney', 'Sydney', 'Melbourne', 'Brisbane',
        'Perth', 'Adelaida', 'Adelaide', 'Canberra', 'Gold Coast',
        'New South Wales', 'NSW', 'Victoria', 'VIC', 'Queensland', 'QLD',
        'Western Australia', 'WA', 'South Australia', 'SA', 'Tasmania',
        'TAS', 'Northern Territory', 'NT', 'ACT',
        # Nueva Zelanda
        'Nueva Zelanda', 'New Zealand', 'Auckland', 'Wellington',
        'Christchurch', 'Hamilton', 'Dunedin', 'North Island', 'South Island'
    ]

    # Combinar todas las ubicaciones
    todas_ubicaciones = (
        provincias_ar + estados_mx + deptos_co + regiones_cl + 
        deptos_pe + provincias_ec + estados_ve + deptos_bo + 
        deptos_py + deptos_uy + estados_br + centroamerica + 
        ccaa_es + portugal + francia + alemania + italia + 
        reino_unido + otros_europa + estados_us + canada + oceania
    )

    for ubicacion in todas_ubicaciones:
        # Buscar coincidencia exacta (case insensitive)
        pattern = r'\b' + re.escape(ubicacion) + r'\b'
        if re.search(pattern, all_content, re.IGNORECASE):
            regex_extract['province'] = ubicacion
            logger.info(f"[REGEX] ✓ Provincia/Estado: {ubicacion}")
            break

    # ═══════════════════════════════════════════════════════════════════
    # 8. HORARIOS
    # ═══════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════
    # 8. HORARIOS (Internacionales)
    # ═══════════════════════════════════════════════════════════════════
    horarios_patterns = [
        # Español: Lun-Vie 9:00 - 18:00
        r'(?:Lun|Mar|Mié|Mie|Jue|Vie|Sáb|Sab|Dom|L|M|X|J|V|S|D)[a-z]*'
        r'[\s\-a]+(?:Lun|Mar|Mié|Mie|Jue|Vie|Sáb|Sab|Dom|L|M|X|J|V|S|D)[a-z]*'
        r'[:\s]+\d{1,2}[:\.]?\d{0,2}\s*(?:hs|hrs|am|pm|AM|PM)?'
        r'\s*[\-a]+\s*\d{1,2}[:\.]?\d{0,2}\s*(?:hs|hrs|am|pm|AM|PM)?',

        # Inglés: Mon-Fri 9:00AM - 6:00PM
        r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|'
        r'Friday|Saturday|Sunday)[a-z]*[\s\-]+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun|'
        r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[a-z]*'
        r'[:\s]+\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm|AM|PM)?'
        r'\s*[\-–—to]+\s*\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm|AM|PM)?',

        # Portugués: Seg-Sex 9h - 18h
        r'(?:Seg|Ter|Qua|Qui|Sex|Sáb|Sab|Dom)[a-z]*[\s\-a]+(?:Seg|Ter|Qua|Qui|'
        r'Sex|Sáb|Sab|Dom)[a-z]*[:\s]+\d{1,2}[h:\.]?\d{0,2}'
        r'\s*[\-a]+\s*\d{1,2}[h:\.]?\d{0,2}',

        # Francés: Lun-Ven 9h00 - 18h00
        r'(?:Lun|Mar|Mer|Jeu|Ven|Sam|Dim)[a-z]*[\s\-à]+(?:Lun|Mar|Mer|Jeu|Ven|'
        r'Sam|Dim)[a-z]*[:\s]+\d{1,2}[h:\.]?\d{0,2}'
        r'\s*[\-à]+\s*\d{1,2}[h:\.]?\d{0,2}',

        # Alemán: Mo-Fr 9:00 - 18:00
        r'(?:Mo|Di|Mi|Do|Fr|Sa|So|Montag|Dienstag|Mittwoch|Donnerstag|'
        r'Freitag|Samstag|Sonntag)[a-z]*[\s\-]+(?:Mo|Di|Mi|Do|Fr|Sa|So)[a-z]*'
        r'[:\s]+\d{1,2}[:\.]?\d{0,2}\s*(?:Uhr)?'
        r'\s*[\-–]+\s*\d{1,2}[:\.]?\d{0,2}\s*(?:Uhr)?',

        # Italiano: Lun-Ven 9:00 - 18:00
        r'(?:Lun|Mar|Mer|Gio|Ven|Sab|Dom|Lunedì|Martedì|Mercoledì|Giovedì|'
        r'Venerdì|Sabato|Domenica)[a-z]*[\s\-]+(?:Lun|Mar|Mer|Gio|Ven|Sab|Dom)'
        r'[a-z]*[:\s]+\d{1,2}[:\.]?\d{0,2}\s*[\-]+\s*\d{1,2}[:\.]?\d{0,2}',

        # Formato genérico: 9:00 - 18:00 / 9:00AM - 6:00PM
        r'\d{1,2}:\d{2}\s*(?:hs|hrs|am|pm|AM|PM|h)?\s*[\-–—to]+\s*'
        r'\d{1,2}:\d{2}\s*(?:hs|hrs|am|pm|AM|PM|h)?',

        # Formato 24h: 09:00-18:00
        r'\b\d{2}:\d{2}\s*[\-–]\s*\d{2}:\d{2}\b',

        # Con palabras clave
        r'(?:Horario|Hours|Horário|Orario|Öffnungszeiten|Heures)[:\s]+'
        r'[^\n]{10,50}',
    ]

    for pattern in horarios_patterns:
        match = re.search(pattern, all_content, re.IGNORECASE)
        if match:
            horario_encontrado = match.group(0).strip()
            # Limpiar espacios extra
            horario_encontrado = ' '.join(horario_encontrado.split())
            regex_extract['horarios'] = horario_encontrado
            logger.info(f"[REGEX] ✓ Horarios encontrados: {horario_encontrado}")
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
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature": 0.1,
                    "max_tokens": 1500
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
                  website: str = "") -> dict:
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
    website_domain = website.replace("https://",
                                     "").replace("http://",
                                                 "").replace("www.",
                                                             "").split("/")[0]

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

    # Validar que phone_empresa no sea un año (ej: 2024-2025)
    phone_empresa = resultado.get("phone_empresa", "No encontrado")
    if phone_empresa and phone_empresa != "No encontrado":
        # Si parece un año o rango de años, descartarlo
        import re
        if re.match(r'^[\d\-\s]+$', phone_empresa) and len(phone_empresa) < 12:
            # Parece año (ej: "2024-2025", "2024", "2025")
            if any(str(year) in phone_empresa for year in range(2020, 2030)):
                resultado['phone_empresa'] = "No encontrado"
                logger.warning(
                    f"[EXTRACTOR] phone_empresa descartado (parece año): {phone_empresa}"
                )

    # Teléfono
    if not resultado.get('phone_empresa') or resultado.get(
            'phone_empresa') == 'No encontrado':
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
    if not resultado.get('google_maps_url') and regex_data.get(
            'google_maps_url'):
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
    if not resultado.get('business_activity') and regex_data.get(
            'business_activity'):
        resultado['business_activity'] = regex_data['business_activity']

    # ═══════════════════════════════════════════════════════════════
    # CARGO DETECTADO (de email con contexto)
    # ═══════════════════════════════════════════════════════════════
    if regex_data.get('cargo_detectado'):
        resultado['cargo_detectado'] = regex_data['cargo_detectado']
        if regex_data.get('email_con_cargo'):
            resultado['email_contacto_principal'] = regex_data['email_con_cargo']
            logger.info(f"[MERGE] Cargo detectado: {regex_data['cargo_detectado']} "
                       f"- Email: {regex_data['email_con_cargo']}")

    # ═══════════════════════════════════════════════════════════════
    # Business model - Asegurar que tenga valor
    # ═══════════════════════════════════════════════════════════════
    if not resultado.get('business_model') or \
       resultado.get('business_model') == 'No encontrado':
        # Combinar varios campos para buscar el modelo de negocio
        activity = resultado.get('business_activity', '').lower()
        description = resultado.get('business_description', '').lower()
        services_text = resultado.get('services_text', '').lower()

        # Combinar todo para búsqueda
        todo_texto = f"{activity} {description} {services_text}"

        # Orden de prioridad de detección
        if any(x in todo_texto for x in ['mayorista', 'distribuidor', 
                                          'wholesale', 'distributor']):
            resultado['business_model'] = 'B2B - Mayorista/Distribuidor'
        elif any(x in todo_texto for x in ['software', 'saas', 'plataforma',
                                            'platform', 'app', 'aplicación']):
            resultado['business_model'] = 'SaaS'
        elif any(x in todo_texto for x in ['ecommerce', 'e-commerce', 
                                            'tienda online', 'online store']):
            resultado['business_model'] = 'Ecommerce'
        elif any(x in todo_texto for x in ['tienda', 'venta al público',
                                            'retail', 'store', 'shop']):
            resultado['business_model'] = 'B2C - Retail'
        elif any(x in todo_texto for x in ['consultor', 'asesor', 
                                            'consulting', 'advisory']):
            resultado['business_model'] = 'B2B - Consultoría'
        elif any(x in todo_texto for x in ['agencia', 'agency', 'marketing',
                                            'publicidad', 'advertising']):
            resultado['business_model'] = 'B2B - Agencia'
        elif any(x in todo_texto for x in ['fabricación', 'manufactura',
                                            'manufacturing', 'factory']):
            resultado['business_model'] = 'B2B - Fabricante'
        elif any(x in todo_texto for x in ['servicio', 'service', 
                                            'solución', 'solution']):
            resultado['business_model'] = 'B2B - Servicios'
        elif any(x in todo_texto for x in ['franquicia', 'franchise']):
            resultado['business_model'] = 'Franquicia'
        elif any(x in todo_texto for x in ['suscripción', 'subscription',
                                            'membresía', 'membership']):
            resultado['business_model'] = 'Suscripción'
        elif any(x in todo_texto for x in ['marketplace', 'mercado']):
            resultado['business_model'] = 'Marketplace'
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
    Extrae contenido de páginas secundarias importantes.
    Incluye variantes internacionales en español, inglés, portugués,
    francés, alemán, italiano y más.
    """
    # Lista completa de páginas secundarias (internacionales)
    paginas = [
        # ═══════════════════════════════════════════════════════════════
        # ESPAÑOL
        # ═══════════════════════════════════════════════════════════════
        '/contacto', '/contactenos', '/contactanos', '/contacto.html',
        '/nosotros', '/sobre-nosotros', '/sobreNosotros', '/quienes-somos',
        '/quienessomos', '/acerca', '/acerca-de', '/la-empresa', '/empresa',
        '/equipo', '/nuestro-equipo', '/el-equipo', '/staff',
        '/ubicacion', '/ubicaciones', '/sucursales', '/sedes',
        '/direccion', '/donde-estamos', '/como-llegar',

        # ═══════════════════════════════════════════════════════════════
        # INGLÉS
        # ═══════════════════════════════════════════════════════════════
        '/contact', '/contact-us', '/contactus', '/contact.html',
        '/get-in-touch', '/reach-us', '/connect',
        '/about', '/about-us', '/aboutus', '/about.html',
        '/who-we-are', '/our-story', '/our-company', '/company',
        '/team', '/our-team', '/ourteam', '/the-team', '/meet-the-team',
        '/staff', '/people', '/leadership', '/management',
        '/locations', '/location', '/offices', '/branches',
        '/find-us', '/where-we-are', '/directions',

        # ═══════════════════════════════════════════════════════════════
        # PORTUGUÉS (Brasil, Portugal)
        # ═══════════════════════════════════════════════════════════════
        '/contato', '/fale-conosco', '/contatos',
        '/sobre', '/sobre-nos', '/quem-somos', '/a-empresa',
        '/equipe', '/nossa-equipe', '/time',
        '/localizacao', '/onde-estamos', '/unidades',

        # ═══════════════════════════════════════════════════════════════
        # FRANCÉS
        # ═══════════════════════════════════════════════════════════════
        '/contact', '/nous-contacter', '/contactez-nous',
        '/a-propos', '/qui-sommes-nous', '/notre-entreprise',
        '/equipe', '/notre-equipe', '/lequipe',

        # ═══════════════════════════════════════════════════════════════
        # ALEMÁN
        # ═══════════════════════════════════════════════════════════════
        '/kontakt', '/kontaktieren',
        '/ueber-uns', '/uber-uns', '/wir-ueber-uns',
        '/team', '/unser-team', '/mitarbeiter',
        '/standorte', '/anfahrt',

        # ═══════════════════════════════════════════════════════════════
        # ITALIANO
        # ═══════════════════════════════════════════════════════════════
        '/contatti', '/contattaci',
        '/chi-siamo', '/la-nostra-azienda', '/azienda',
        '/team', '/il-team', '/squadra',
        '/dove-siamo', '/sedi',

        # ═══════════════════════════════════════════════════════════════
        # HOLANDÉS
        # ═══════════════════════════════════════════════════════════════
        '/contact', '/neem-contact-op',
        '/over-ons', '/wie-zijn-wij',
        '/team', '/ons-team',

        # ═══════════════════════════════════════════════════════════════
        # VARIANTES COMUNES (CMS, frameworks)
        # ═══════════════════════════════════════════════════════════════
        '/info', '/information', '/informacion',
        '/company-info', '/corporate', '/corp',
        '/hq', '/headquarters', '/main-office',
    ]

    contenido_extra = ""
    paginas_exitosas = 0
    max_paginas = 5  # Aumentado para cubrir más variantes
    paginas_probadas = set()

    for pagina in paginas:
        if paginas_exitosas >= max_paginas:
            break

        # Evitar duplicados (ej: /contact aparece en varios idiomas)
        pagina_lower = pagina.lower()
        if pagina_lower in paginas_probadas:
            continue
        paginas_probadas.add(pagina_lower)

        url = f"https://{website}{pagina}"

        try:
            async with httpx.AsyncClient(timeout=10.0,
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
                    # Verificar que tenga contenido sustancial
                    # y no sea un redirect a home (comparar longitud)
                    if len(texto) > 1000:
                        # No verificar que el nombre de página esté en el
                        # texto porque puede estar en otro idioma
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

                            resultado = '+' + num
                            logger.info(
                                f"[WA-EXTERNO] ✓ Encontrado: {resultado}")
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
            logger.info(
                f"[TAVILY] ✓ {len(tavily_content)} caracteres extraídos")

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
    resultado = merge_results(gpt_data, regex_data, tavily_answer,
                              website_full)

    # ═══════════════════════════════════════════════════════════════
    # BÚSQUEDA DE WHATSAPP EN HTML CRUDO (widgets JS)
    # Primero intentamos extraer del HTML directo (más confiable)
    # ═══════════════════════════════════════════════════════════════
    if resultado.get('_necesita_wa_externo'):
        # Paso 1: Buscar en HTML crudo (scripts, widgets)
        wa_html = await buscar_whatsapp_en_html_crudo(website_clean)
        if wa_html:
            resultado['whatsapp_empresa'] = wa_html
            resultado['whatsapp_source'] = 'html_widget'
            resultado.pop('_necesita_wa_externo', None)
        else:
            # Paso 2: Buscar en fuentes externas (directorios)
            empresa_nombre = resultado.get('business_name', '')
            wa_externo = await buscar_whatsapp_externo(website_clean,
                                                       empresa_nombre)
            if wa_externo:
                resultado['whatsapp_empresa'] = wa_externo
                resultado['whatsapp_source'] = 'externo'

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

    return resultado