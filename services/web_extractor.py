"""
Servicio de extracción de datos web
Pipeline: Jina AI (scraping) → Tavily (complemento) → GPT-4o (parsing)
"""
import os
import re
import httpx
import json
import logging
from typing import Optional

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
    """
    try:
        url = f"https://r.jina.ai/{website}"
        
        headers = {}
        jina_key = os.environ.get("JINA_API_KEY", "")
        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Jina AI error {response.status_code} para {website}")
                return ""
    
    except Exception as e:
        logger.error(f"Error Jina AI: {e}")
        return ""


async def search_with_tavily(query: str) -> dict:
    """
    Búsqueda web con Tavily.
    """
    try:
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            logger.error("TAVILY_API_KEY no configurada")
            return {}
        
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
            "include_raw_content": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Tavily error {response.status_code}")
                return {}
    
    except Exception as e:
        logger.error(f"Error Tavily: {e}")
        return {}


def extract_with_regex(content: str, website: str) -> dict:
    """
    Extrae datos con regex del contenido web.
    """
    extracted = {}
    
    # Emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
    # Filtrar emails genéricos
    emails = [e for e in emails if not any(x in e.lower() for x in ['example', 'test', 'domain', 'email'])]
    if emails:
        extracted['email_principal'] = emails[0]
        if len(emails) > 1:
            extracted['emails_adicionales'] = emails[1:5]
    
    # Teléfonos argentinos
    phones = re.findall(r'(?:\+54|0)?(?:\s*)?(?:9)?(?:\s*)?(?:11|[2-9]\d{2,3})(?:\s*[-.]?\s*)?\d{3,4}(?:\s*[-.]?\s*)?\d{4}', content)
    if phones:
        extracted['phone_empresa'] = phones[0]
        if len(phones) > 1:
            extracted['phones_adicionales'] = phones[1:3]
    
    # Redes sociales de la EMPRESA (del sitio web, no template)
    domain = clean_url(website)
    
    # LinkedIn empresa
    linkedin_empresa = re.findall(r'https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9_-]+/?', content)
    if linkedin_empresa:
        extracted['linkedin_empresa'] = linkedin_empresa[0].rstrip('/')
    
    # Instagram empresa
    instagram = re.findall(r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+/?', content)
    if instagram:
        extracted['instagram_empresa'] = instagram[0].rstrip('/')
    
    # Facebook empresa
    facebook = re.findall(r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9_.]+/?', content)
    if facebook:
        extracted['facebook_empresa'] = facebook[0].rstrip('/')
    
    # WhatsApp empresa
    wa_links = re.findall(r'https?://(?:wa\.me|api\.whatsapp\.com)/(\d+)', content)
    if wa_links:
        extracted['whatsapp_empresa'] = wa_links[0]
    
    # Dirección (patrones comunes en Argentina)
    direccion = re.findall(r'(?:Av\.|Bv\.|Calle|Boulevard|Avenida)[\s\w]+\d+', content)
    if direccion:
        extracted['address'] = direccion[0]
    
    return extracted


async def parse_with_gpt(content: str, website: str, regex_data: dict) -> dict:
    """
    Usa GPT-4o para extraer datos estructurados.
    """
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.error("OPENAI_API_KEY no configurada")
            return regex_data
        
        prompt = f"""Analiza el siguiente contenido web de {website} y extrae SOLO los datos que encuentres explícitamente.

CONTENIDO:
{content[:8000]}

DATOS YA EXTRAÍDOS POR REGEX:
{json.dumps(regex_data, ensure_ascii=False)}

Devuelve un JSON con estos campos (usa "No encontrado" si no está disponible):
{{
    "business_name": "nombre de la empresa",
    "business_description": "descripción breve de la empresa",
    "business_activity": "rubro o actividad principal",
    "services_text": "servicios que ofrece",
    "email_principal": "email principal",
    "phone_empresa": "teléfono principal",
    "whatsapp_empresa": "número de WhatsApp empresa",
    "address": "dirección completa",
    "city": "ciudad",
    "province": "provincia",
    "horarios": "horarios de atención",
    "linkedin_empresa": "URL LinkedIn empresa",
    "instagram_empresa": "URL Instagram empresa",
    "facebook_empresa": "URL Facebook empresa"
}}

REGLAS CRÍTICAS:
- NO inventar datos
- NO usar emails genéricos (info@, contacto@) a menos que estén explícitamente en el contenido
- Usar EXACTAMENTE las URLs encontradas, sin modificar
- Si un dato no está, poner "No encontrado"

Responde SOLO con el JSON, sin explicaciones."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    return regex_data
                message = choices[0].get("message", {})
                content = message.get("content", "")
                
                if not content:
                    return regex_data
                
                # Limpiar markdown
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                content = content.strip()
                
                try:
                    parsed = json.loads(content)
                    # Combinar con regex (regex tiene prioridad solo si GPT no encontró el dato)
                    for key, value in regex_data.items():
                        if value and value != "No encontrado":
                            # Solo usar regex si GPT no tiene el dato o tiene "No encontrado"
                            if key not in parsed or parsed.get(key) == "No encontrado" or not parsed.get(key):
                                parsed[key] = value
                    return parsed
                except json.JSONDecodeError:
                    logger.warning("GPT no devolvió JSON válido")
                    return regex_data
            else:
                logger.error(f"Error OpenAI: {response.status_code}")
                return regex_data
    
    except Exception as e:
        logger.error(f"Error GPT parsing: {e}")
        return regex_data


async def extract_web_data(website: str) -> dict:
    """
    Pipeline completo de extracción web.
    1. Jina AI (scraping)
    2. Tavily (complemento)
    3. Regex (extracción básica)
    4. GPT-4o (parsing inteligente)
    """
    logger.info(f"Extrayendo datos de: {website}")
    
    # Normalizar URL
    website_clean = clean_url(website)
    website_full = f"https://{website_clean}"
    
    # 1. Jina AI
    jina_content = await fetch_with_jina(website_clean)
    
    # 2. Tavily complemento
    tavily_query = f'"{website_clean}" contacto dirección teléfono email Argentina'
    tavily_data = await search_with_tavily(tavily_query)
    
    # Combinar contenido
    combined_content = jina_content
    if tavily_data.get("answer"):
        combined_content += f"\n\nDESCRIPCIÓN: {tavily_data.get('answer', '')}"
    results = tavily_data.get("results", [])
    if results:
        for result in results[:3]:
            raw_content = result.get("raw_content", "")
            if raw_content:
                combined_content += f"\n\n{raw_content[:1000]}"
    
    if not combined_content:
        logger.warning(f"No se pudo obtener contenido de {website}")
        return {
            "business_name": "No encontrado",
            "business_description": "No encontrado",
            "website": website_full,
            "extraction_status": "failed"
        }
    
    # 3. Extracción con regex
    regex_data = extract_with_regex(combined_content, website_clean)
    
    # 4. Parsing con GPT-4o
    final_data = await parse_with_gpt(combined_content, website_clean, regex_data)
    
    # Agregar website
    final_data["website"] = website_full
    final_data["extraction_status"] = "success"
    
    logger.info(f"Extracción completada: {website_clean}")
    return final_data
