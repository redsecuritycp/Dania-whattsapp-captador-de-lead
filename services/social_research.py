"""
Servicio de investigación de redes sociales y noticias para DANIA/Fortia
VERSIÓN CORREGIDA:
- LinkedIn empresa: SOLO desde web del cliente (no buscar con Google)
- LinkedIn personal: 2 fases (nombre+empresa, fallback nombre+ubicación)

Flujo:
1. Preparar datos y limpiar inputs
2. Tavily: Verificar nombre completo en sitio web
3. Tavily: Buscar LinkedIn personal (FASE 1: nombre+empresa)
4. Tavily: Buscar LinkedIn personal (FASE 2: nombre+ubicación) - fallback
5. Google: Fallback LinkedIn personal (misma lógica 2 fases)
6. Apify: Crawler de noticias (Google News + Bing News)
7. Google: Noticias fallback
8. Compilar resultados
"""
import logging
import httpx
import re
import asyncio
from typing import Optional, List
from urllib.parse import quote

from config import (TAVILY_API_KEY, GOOGLE_API_KEY, GOOGLE_SEARCH_CX,
                    APIFY_API_TOKEN)

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30.0
APIFY_TIMEOUT = 45.0  # Reducido de 200s a 45s


def es_url_valida_noticia(url: str, texto: str, empresa: str) -> bool:
    """Valida si una URL es una noticia real y relevante."""
    url_lower = url.lower()
    texto_lower = texto.lower()
    empresa_lower = empresa.lower()

    if url_lower.endswith('.pdf'):
        return False

    dominios_basura = [
        # Académicos/documentos
        'pdfcoffee', 'scribd', 'academia.edu', 'slideshare', 'coursehero',
        'repositorio', 'bitstream', 'handle/', 'thesis', 'tesis',
        # Gobierno/legal
        'icj-cij.org', 'cancilleria.gob', 'boletinoficial',
        'sidof.segob.gob', 'segob.gob.mx',
        # Ecommerce/spam
        'cityfilespress', 'amazon.com', 'mercadolibre', 'aliexpress',
        'ebay.com', 'alibaba.com', 'wish.com', 'shopee',
        'olx.com', 'craiglist', 'segundamano', 'vibbo',
        # Redes sociales (NO son noticias)
        'linkedin.com', 'facebook.com', 'instagram.com', 
        'twitter.com', 'x.com', 'youtube.com', 'tiktok.com',
    ]
    if any(d in url_lower for d in dominios_basura):
        return False

    palabras_empresa = [p for p in empresa_lower.split() if len(p) > 2]
    matches = sum(1 for p in palabras_empresa if p in texto_lower)
    if matches < 1:
        return False

    return True


def es_red_social(url: str) -> bool:
    """Verifica si la URL es de una red social."""
    redes = [
        'linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com',
        'youtube.com', 'tiktok.com', 'x.com'
    ]
    return any(red in url.lower() for red in redes)


def es_buscador(url: str) -> bool:
    """Verifica si la URL es de un buscador o página de resultados."""
    url_lower = url.lower()
    
    # Patrones de buscadores y páginas de resultados
    patrones_buscador = [
        'google.com/search',
        'bing.com/search',
        'bing.com/news/search',
        'yahoo.com/search',
        'duckduckgo.com',
        'news.google.com/search',
        'search?q=',
        '/search?',
    ]
    
    # Detectar URLs que son páginas de búsqueda
    if any(p in url_lower for p in patrones_buscador):
        return True
    
    # Detectar news.google.com (cualquier path)
    if 'news.google.com' in url_lower and '/articles/' not in url_lower:
        return True
    
    return False


def es_registro_legal(url: str, texto: str) -> bool:
    """Verifica si es un registro legal o boletín oficial."""
    url_lower = url.lower()
    texto_lower = texto.lower()

    if 'boletinoficial' in url_lower or 'boletin-oficial' in url_lower:
        return True
    if '/contratos' in url_lower or 'contratos.pdf' in url_lower:
        return True

    keywords_legales = [
        'modificación de contrato', 'modificacion de contrato',
        'cesión de cuotas', 'cesion de cuotas', 'constitución de sociedad',
        'constitucion de sociedad', 'designación de gerentes',
        'designacion de gerentes', 'contrato social', 'expte.', 'expediente',
        'autos caratulados', 'inscripción matrícula', 'inscripcion matricula'
    ]

    if any(kw in texto_lower for kw in keywords_legales):
        return True

    return False


def calcular_peso_linkedin(
    url: str,
    texto: str,
    primer_nombre: str,
    apellido: str,
    empresa: str = "",
    provincia: str = "",
    ciudad: str = ""
) -> int:
    """
    Calcula el peso de un perfil de LinkedIn.
    
    PESO MÁXIMO 100:
    - Nombre (obligatorio): 40 puntos
    - Apellido (obligatorio): 40 puntos
    - Empresa: 10 puntos
    - Provincia/Ciudad: 10 puntos
    
    Si no tiene nombre Y apellido, retorna 0 (descartar).
    """
    url_lower = url.lower()
    texto_lower = texto.lower()
    
    # Extraer slug de la URL
    slug = ""
    if "/in/" in url_lower:
        slug = url_lower.split("/in/")[1].split("/")[0].split("?")[0]
    slug_clean = slug.replace("-", " ").replace("_", " ")
    
    # Combinar texto y slug para búsqueda
    contenido = f"{texto_lower} {slug_clean}"
    
    primer_lower = primer_nombre.lower().strip()
    apellido_lower = apellido.lower().strip()
    empresa_lower = empresa.lower().strip() if empresa else ""
    provincia_lower = provincia.lower().strip() if provincia else ""
    ciudad_lower = ciudad.lower().strip() if ciudad else ""
    
    peso = 0
    tiene_nombre = False
    tiene_apellido = False
    
    # Verificar nombre (40 puntos)
    if primer_lower and len(primer_lower) > 1:
        if primer_lower in contenido:
            peso += 40
            tiene_nombre = True
    
    # Verificar apellido (40 puntos)
    if apellido_lower and len(apellido_lower) > 1:
        if apellido_lower in contenido:
            peso += 40
            tiene_apellido = True
    
    # Si no tiene nombre Y apellido, descartar
    if not (tiene_nombre and tiene_apellido):
        return 0
    
    # Verificar empresa (10 puntos)
    if empresa_lower and len(empresa_lower) > 2:
        # Buscar empresa completa o palabras clave
        palabras_empresa = [
            p for p in empresa_lower.split() 
            if len(p) > 2
        ]
        if empresa_lower in contenido:
            peso += 10
        elif any(p in contenido for p in palabras_empresa):
            peso += 5
    
    # Verificar ubicación (10 puntos)
    if provincia_lower and provincia_lower in contenido:
        peso += 5
    if ciudad_lower and ciudad_lower in contenido:
        peso += 5
    
    return min(peso, 100)


async def research_person_and_company(nombre_persona: str,
                                      empresa: str,
                                      website: str = "",
                                      linkedin_empresa_input: str = "",
                                      facebook_empresa_input: str = "",
                                      instagram_empresa_input: str = "",
                                      city: str = "",
                                      province: str = "",
                                      country: str = "",
                                      email_contacto: str = "") -> dict:
    """
    Función principal que replica el workflow completo de n8n.
    LinkedIn empresa: SOLO desde web del cliente.
    LinkedIn personal: 2 fases de búsqueda.
    """
    logger.info(f"[RESEARCH] ========== Iniciando investigación ==========")
    logger.info(f"[RESEARCH] Persona: {nombre_persona}, "
                f"Empresa: {empresa}, Web: {website}")

    # ═══════════════════════════════════════════════════════════════════
    # PASO 1: PREPARAR DATOS
    # ═══════════════════════════════════════════════════════════════════

    nombre = nombre_persona.strip()
    nombre_partes = nombre.split()
    primer_nombre = nombre_partes[0] if nombre_partes else ""
    apellido = nombre_partes[-1] if len(nombre_partes) > 1 else ""

    website_limpio = (website.replace("https://",
                                      "").replace("http://",
                                                  "").replace("www.",
                                                              "").rstrip("/"))
    tiene_website = bool(website_limpio)

    empresa_busqueda = empresa if empresa else website_limpio

    # Ubicación completa para búsquedas
    ubicacion_query = city or province or country or ""
    ubicacion_completa = ""
    if city and province:
        ubicacion_completa = f"{city}, {province}"
    elif city:
        ubicacion_completa = city
    elif province:
        ubicacion_completa = province
    if country and ubicacion_completa:
        ubicacion_completa += f", {country}"
    elif country:
        ubicacion_completa = country

    # Inicializar resultados
    # NOTA: LinkedIn empresa SOLO viene de web, no se busca
    results = {
        "nombre_original":
        nombre,
        "nombre":
        nombre,
        "primer_nombre":
        primer_nombre,
        "apellido":
        apellido,
        "empresa":
        empresa,
        "website":
        website,
        "website_limpio":
        website_limpio,
        "empresa_busqueda":
        empresa_busqueda,

        # LinkedIn personal
        "linkedin_personal":
        "No encontrado",
        "linkedin_personal_confianza":
        0,
        "linkedin_personal_source":
        "ninguno",

        # LinkedIn empresa - SOLO de la web del cliente
        "linkedin_empresa":
        linkedin_empresa_input or "No encontrado",
        "linkedin_empresa_source":
        ("web_cliente" if linkedin_empresa_input else "ninguno"),

        # Otras redes (SOLO de la web del cliente, NO se buscan)
        "facebook_empresa":
        facebook_empresa_input or "No encontrado",
        "instagram_empresa":
        instagram_empresa_input or "No encontrado",

        # Noticias
        "noticias_lista": [],
        "noticias_empresa":
        "No se encontraron noticias",
        "noticias_count":
        0,
        "noticias_source":
        "ninguno"
    }

    try:
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: TAVILY - VERIFICAR NOMBRE EN SITIO WEB
        # ═══════════════════════════════════════════════════════════════
        if tiene_website and TAVILY_API_KEY:
            logger.info(f"[TAVILY] Verificando nombre en sitio web...")
            nombre_verificado = await tavily_verificar_nombre(
                website_limpio, primer_nombre, apellido)
            if nombre_verificado:
                results["nombre"] = nombre_verificado
                results["nombre_verificado"] = True
                partes = nombre_verificado.split()
                results[
                    "primer_nombre"] = partes[0] if partes else primer_nombre
                results["apellido"] = partes[-1] if len(
                    partes) > 1 else apellido
                logger.info(
                    f"[TAVILY] ✓ Nombre verificado: {nombre_verificado}")

        # ═══════════════════════════════════════════════════════════════
        # PASO 3: LINKEDIN PERSONAL - BÚSQUEDA CON PESO
        # ═══════════════════════════════════════════════════════════════
        # Buscar en TODAS las fuentes, calcular peso, mostrar los mejores
        # ═══════════════════════════════════════════════════════════════
        
        candidatos_linkedin = []  # Lista de {url, peso, source}
        
        primer_nombre_busqueda = results["primer_nombre"]
        apellido_busqueda = results["apellido"]
        
        # ───────────────────────────────────────────────────────────────
        # 3A: BUSCAR EN WEB DEL CLIENTE
        # ───────────────────────────────────────────────────────────────
        if tiene_website:
            logger.info(f"[LINKEDIN] PASO 3A: Buscando en web...")
            try:
                paginas = [
                    f"https://{website_limpio}",
                    f"https://{website_limpio}/nosotros",
                    f"https://{website_limpio}/about",
                    f"https://{website_limpio}/equipo",
                    f"https://{website_limpio}/team",
                    f"https://{website_limpio}/contacto",
                ]
                
                contenido_web = ""
                async with httpx.AsyncClient(timeout=15.0) as client:
                    for pagina in paginas[:4]:
                        try:
                            resp = await client.get(
                                pagina,
                                headers={"User-Agent": "Mozilla/5.0"},
                                follow_redirects=True
                            )
                            if resp.status_code == 200:
                                contenido_web += resp.text + "\n"
                        except:
                            continue
                
                if contenido_web:
                    # Buscar URLs de LinkedIn en el contenido
                    pattern = r'https?://(?:www\.)?(?:ar\.)?linkedin\.com/in/([a-zA-Z0-9_~-]+)'
                    matches = re.findall(pattern, contenido_web, re.IGNORECASE)
                    
                    for slug in matches:
                        if slug.lower() in ['company', 'jobs', 'pulse']:
                            continue
                        
                        url = f"https://linkedin.com/in/{slug}"
                        peso = calcular_peso_linkedin(
                            url=url,
                            texto=contenido_web,
                            primer_nombre=primer_nombre_busqueda,
                            apellido=apellido_busqueda,
                            empresa=empresa_busqueda,
                            provincia=province,
                            ciudad=city
                        )
                        
                        if peso >= 60:
                            ya_existe = any(
                                c["url"] == url for c in candidatos_linkedin
                            )
                            if not ya_existe:
                                candidatos_linkedin.append({
                                    "url": url,
                                    "peso": peso,
                                    "source": "web_cliente"
                                })
                                logger.info(
                                    f"[LINKEDIN-WEB] ✓ {url} (peso: {peso})"
                                )
                        else:
                            logger.info(
                                f"[LINKEDIN-WEB] ✗ {url} descartado "
                                f"(peso: {peso} < 60)"
                            )
            except Exception as e:
                logger.warning(f"[LINKEDIN-WEB] Error: {e}")
        
        # ───────────────────────────────────────────────────────────────
        # 3B: BUSCAR POR EMAIL
        # ───────────────────────────────────────────────────────────────
        if email_contacto and email_contacto != "No encontrado":
            logger.info(f"[LINKEDIN] PASO 3B: Buscando por email...")
            linkedin_email = await buscar_linkedin_por_email(email_contacto)
            if linkedin_email:
                peso = calcular_peso_linkedin(
                    url=linkedin_email,
                    texto=email_contacto,
                    primer_nombre=primer_nombre_busqueda,
                    apellido=apellido_busqueda,
                    empresa=empresa_busqueda,
                    provincia=province,
                    ciudad=city
                )
                # Email tiene peso mínimo 70 si encontró algo
                peso = max(peso, 70)
                ya_existe = any(
                    c["url"] == linkedin_email for c in candidatos_linkedin
                )
                if not ya_existe:
                    candidatos_linkedin.append({
                        "url": linkedin_email,
                        "peso": peso,
                        "source": "email"
                    })
                    logger.info(
                        f"[LINKEDIN-EMAIL] ✓ {linkedin_email} (peso: {peso})"
                    )
        
        # ───────────────────────────────────────────────────────────────
        # 3C: BUSCAR POR NOMBRE+EMPRESA (Tavily)
        # ───────────────────────────────────────────────────────────────
        if TAVILY_API_KEY:
            logger.info(f"[LINKEDIN] PASO 3C: Buscando en Tavily...")
            linkedin_result = await tavily_buscar_linkedin_personal(
                results["nombre"], 
                empresa_busqueda, 
                primer_nombre_busqueda,
                apellido_busqueda, 
                ubicacion_completa, 
                city, 
                province,
                country
            )
            if linkedin_result:
                urls_tavily = linkedin_result.get("url", "")
                confianza = linkedin_result.get("confianza", 0)
                
                # Puede venir una URL o varias separadas por |
                for url in urls_tavily.split(" | "):
                    url = url.strip()
                    if not url or url == "No encontrado":
                        continue
                    
                    ya_existe = any(
                        c["url"] == url for c in candidatos_linkedin
                    )
                    if not ya_existe:
                        candidatos_linkedin.append({
                            "url": url,
                            "peso": confianza,
                            "source": "tavily"
                        })
                        logger.info(
                            f"[LINKEDIN-TAVILY] ✓ {url} (peso: {confianza})"
                        )
        
        # ───────────────────────────────────────────────────────────────
        # 3D: BUSCAR CON GOOGLE (fallback)
        # ───────────────────────────────────────────────────────────────
        if GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[LINKEDIN] PASO 3D: Buscando en Google...")
            google_result = await google_buscar_linkedin_personal(
                results["nombre"], 
                empresa_busqueda, 
                primer_nombre_busqueda,
                apellido_busqueda, 
                0,  # confianza_actual
                ubicacion_completa, 
                city, 
                province, 
                country
            )
            if google_result:
                urls_google = google_result.get("url", "")
                confianza = google_result.get("confianza", 0)
                
                for url in urls_google.split(" | "):
                    url = url.strip()
                    if not url or url == "No encontrado":
                        continue
                    
                    ya_existe = any(
                        c["url"] == url for c in candidatos_linkedin
                    )
                    if not ya_existe:
                        candidatos_linkedin.append({
                            "url": url,
                            "peso": confianza,
                            "source": "google"
                        })
                        logger.info(
                            f"[LINKEDIN-GOOGLE] ✓ {url} (peso: {confianza})"
                        )
        
        # ───────────────────────────────────────────────────────────────
        # 3E: BUSCAR POR CARGO (CEO/fundador)
        # ───────────────────────────────────────────────────────────────
        if len(candidatos_linkedin) < 2:
            logger.info(f"[LINKEDIN] PASO 3E: Buscando por cargo...")
            por_cargo = await buscar_linkedin_por_cargo(
                empresa=empresa_busqueda,
                ubicacion=ubicacion_completa
            )
            for url in por_cargo:
                peso = calcular_peso_linkedin(
                    url=url,
                    texto=f"{empresa_busqueda} {ubicacion_completa}",
                    primer_nombre=primer_nombre_busqueda,
                    apellido=apellido_busqueda,
                    empresa=empresa_busqueda,
                    provincia=province,
                    ciudad=city
                )
                if peso >= 60:
                    ya_existe = any(
                        c["url"] == url for c in candidatos_linkedin
                    )
                    if not ya_existe:
                        candidatos_linkedin.append({
                            "url": url,
                            "peso": peso,
                            "source": "cargo"
                        })
                        logger.info(
                            f"[LINKEDIN-CARGO] ✓ {url} (peso: {peso})"
                        )
        
        # ───────────────────────────────────────────────────────────────
        # CONSOLIDAR RESULTADOS
        # ───────────────────────────────────────────────────────────────
        if candidatos_linkedin:
            # Ordenar por peso (mayor a menor)
            candidatos_linkedin.sort(
                key=lambda x: x["peso"], 
                reverse=True
            )
            
            # Filtrar solo los que tienen peso >= 60
            validos = [
                c for c in candidatos_linkedin 
                if c["peso"] >= 60
            ]
            
            if validos:
                # Formato: uno por línea
                urls_finales = [c["url"] for c in validos[:5]]
                results["linkedin_personal"] = "\n".join(urls_finales)
                results["linkedin_personal_confianza"] = validos[0]["peso"]
                results["linkedin_personal_source"] = validos[0]["source"]
                
                logger.info(
                    f"[LINKEDIN] ✓ {len(urls_finales)} perfiles encontrados"
                )
                for c in validos[:5]:
                    logger.info(
                        f"  - {c['url']} (peso: {c['peso']}, "
                        f"source: {c['source']})"
                    )
            else:
                logger.info("[LINKEDIN] ✗ Ningún candidato con peso >= 60")
        else:
            logger.info("[LINKEDIN] ✗ No se encontraron candidatos")

        # ═══════════════════════════════════════════════════════════════
        # PASO 5: NOTICIAS - GOOGLE PRIMERO (RÁPIDO) + APIFY PARALELO
        # ═══════════════════════════════════════════════════════════════
        noticias = []
        
        # Primero Google (rápido, ~2 seg)
        if GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[GOOGLE] Buscando noticias...")
            noticias = await google_buscar_noticias(
                empresa, empresa_busqueda, ubicacion_query
            )
            if noticias:
                results["noticias_source"] = "google"
        
        # Si Google no encontró, intentar APIFY con timeout corto
        if not noticias and APIFY_API_TOKEN:
            logger.info(f"[APIFY] Intentando crawler (timeout 30s)...")
            try:
                noticias = await asyncio.wait_for(
                    apify_buscar_noticias(empresa_busqueda, ubicacion_query),
                    timeout=30.0
                )
                if noticias:
                    results["noticias_source"] = "apify"
            except asyncio.TimeoutError:
                logger.warning("[APIFY] Timeout - continuando sin noticias")

        if noticias:
            results["noticias_lista"] = noticias
            results["noticias_count"] = len(noticias)

            noticias_texto = []
            for n in noticias[:10]:
                titulo = n.get("titulo", "Sin título")
                url = n.get("url", "")

                # Extraer nombre del dominio como label
                try:
                    dominio = url.split('/')[2].replace('www.', '')
                    source_label = dominio.split('.')[0].upper()
                except:
                    source_label = 'WEB'

                linea = f"• {titulo} [{source_label}]"
                if url:
                    linea += f"\n  {url}"
                noticias_texto.append(linea)

            if noticias_texto:
                results["noticias_empresa"] = "\n\n".join(noticias_texto)

    except Exception as e:
        logger.error(f"[RESEARCH] Error en investigación: {e}", exc_info=True)

    logger.info(f"[RESEARCH] ========== Investigación completada ==========")
    logger.info(
        f"[RESEARCH] LinkedIn personal: {results['linkedin_personal']} "
        f"(conf: {results['linkedin_personal_confianza']})")
    logger.info(f"[RESEARCH] LinkedIn empresa: {results['linkedin_empresa']}")
    logger.info(f"[RESEARCH] Noticias: {results['noticias_count']} "
                f"({results['noticias_source']})")

    return results


async def tavily_verificar_nombre(website: str, primer_nombre: str,
                                  apellido: str) -> Optional[str]:
    """
    Busca en el sitio web para verificar/encontrar el nombre completo.
    """
    if not TAVILY_API_KEY:
        return None

    try:
        query = (f'site:{website} "{primer_nombre}" OR "{apellido}" '
                 f'equipo nosotros about contacto')

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "advanced",
                                             "include_raw_content": True,
                                             "max_results": 5
                                         })

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])

            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()

            patrones = [
                re.compile(
                    rf'{primer_lower}\s+[a-záéíóúñ]+\s+{apellido_lower}',
                    re.IGNORECASE),
                re.compile(
                    rf'(?:ing\.?|dr\.?|lic\.?|arq\.?|sr\.?|sra\.?|cpa\.?|mba\.?)'
                    rf'\s*{primer_lower}\s+(?:[a-záéíóúñ]+\s+)?{apellido_lower}',
                    re.IGNORECASE),
                re.compile(rf'{primer_lower}\s+{apellido_lower}',
                           re.IGNORECASE),
                re.compile(rf'{apellido_lower},?\s+{primer_lower}',
                           re.IGNORECASE),
                re.compile(
                    rf'{primer_lower}\s+(?:de\s+|del\s+)?'
                    rf'[a-záéíóúñ]+\s+{apellido_lower}', re.IGNORECASE)
            ]

            mejor_match = None
            mejor_longitud = 0

            for result in results:
                contenido = ((result.get("content") or "") + " " +
                             (result.get("raw_content") or "")).lower()

                for patron in patrones:
                    matches = patron.findall(contenido)
                    for match in matches:
                        nombre_limpio = re.sub(
                            r'^(ing\.?|dr\.?|lic\.?|arq\.?|'
                            r'sr\.?|sra\.?|cpa\.?|mba\.?)\s*',
                            '',
                            match,
                            flags=re.IGNORECASE)
                        nombre_limpio = nombre_limpio.strip()
                        nombre_limpio = " ".join(
                            p.capitalize() for p in nombre_limpio.split())

                        if (len(nombre_limpio) > mejor_longitud
                                and len(nombre_limpio.split()) >= 2):
                            mejor_match = nombre_limpio
                            mejor_longitud = len(nombre_limpio)

            return mejor_match

    except Exception as e:
        logger.error(f"[TAVILY] Error verificando nombre: {e}")
        return None


async def buscar_linkedin_por_cargo(
    empresa: str,
    ubicacion: str = "",
    cargos: list = None
) -> list:
    """
    Busca LinkedIn de fundadores/CEO/directores de una empresa.
    Retorna lista de URLs encontradas.
    """
    if not TAVILY_API_KEY:
        return []
    
    if cargos is None:
        cargos = [
            'fundador', 'founder', 'CEO', 'director', 
            'dueño', 'owner', 'gerente general'
        ]
    
    resultados = []
    
    for cargo in cargos[:3]:  # Limitar a 3 cargos
        query = f'{cargo} "{empresa}" site:linkedin.com/in'
        if ubicacion:
            query = f'{cargo} "{empresa}" {ubicacion} site:linkedin.com/in'
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "basic",
                        "include_domains": ["linkedin.com"],
                        "max_results": 5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for r in data.get("results", []):
                        url = r.get("url", "")
                        if "linkedin.com/in/" in url and \
                           "/company/" not in url:
                            url_clean = url.split("?")[0]
                            if url_clean not in resultados:
                                resultados.append(url_clean)
                                logger.info(
                                    f"[CARGO] LinkedIn por {cargo}: "
                                    f"{url_clean}"
                                )
        except Exception as e:
            logger.error(f"[CARGO] Error buscando {cargo}: {e}")
    
    return resultados[:5]  # Máximo 5 resultados


async def buscar_linkedin_en_web(
    contenido_web: str,
    nombre: str = "",
    apellido: str = ""
) -> list:
    """
    Busca URLs de LinkedIn personal en el contenido de la web.
    Busca en secciones Equipo, Nosotros, About, etc.
    """
    resultados = []
    
    # Patrón para LinkedIn personal
    pattern = r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)'
    matches = re.findall(pattern, contenido_web, re.IGNORECASE)
    
    for slug in matches:
        # Filtrar slugs genéricos
        if slug.lower() in ['company', 'jobs', 'pulse', 'learning']:
            continue
        
        url = f"https://linkedin.com/in/{slug}"
        
        # Si tenemos nombre/apellido, priorizar matches
        if nombre or apellido:
            slug_lower = slug.lower().replace("-", " ")
            nombre_lower = nombre.lower() if nombre else ""
            apellido_lower = apellido.lower() if apellido else ""
            
            if nombre_lower in slug_lower or apellido_lower in slug_lower:
                # Match con nombre, agregar al principio
                if url not in resultados:
                    resultados.insert(0, url)
                    logger.info(f"[WEB] LinkedIn en web (match nombre): {url}")
            else:
                if url not in resultados:
                    resultados.append(url)
                    logger.info(f"[WEB] LinkedIn en web: {url}")
        else:
            if url not in resultados:
                resultados.append(url)
    
    return resultados[:5]


async def buscar_linkedin_por_email(email: str) -> Optional[str]:
    """
    Busca LinkedIn usando el email como query.
    """
    if not TAVILY_API_KEY or not email or email == "No encontrado":
        return None
    
    # Extraer nombre del email (antes del @)
    nombre_email = email.split("@")[0]
    # Limpiar (quitar números, puntos, guiones)
    nombre_limpio = re.sub(r'[0-9._-]', ' ', nombre_email).strip()
    
    if len(nombre_limpio) < 3:
        return None
    
    query = f'"{email}" site:linkedin.com/in'
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "basic",
                    "include_domains": ["linkedin.com"],
                    "max_results": 3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for r in data.get("results", []):
                    url = r.get("url", "")
                    if "linkedin.com/in/" in url:
                        url_clean = url.split("?")[0]
                        logger.info(f"[EMAIL] LinkedIn por email: {url_clean}")
                        return url_clean
    except Exception as e:
        logger.error(f"[EMAIL] Error: {e}")
    
    return None


async def tavily_buscar_linkedin_personal(nombre: str,
                                          empresa_busqueda: str,
                                          primer_nombre: str,
                                          apellido: str,
                                          ubicacion: str = "",
                                          city: str = "",
                                          province: str = "",
                                          country: str = "") -> Optional[dict]:
    """
    Busca LinkedIn personal usando Tavily con 2 FASES:
    - FASE 1: nombre + empresa + ubicación (alta confianza)
    - FASE 2: nombre + ubicación sin empresa (fallback)
    """
    if not TAVILY_API_KEY:
        return None

    # ═══════════════════════════════════════════════════════════════════
    # FASE 1: Búsqueda con nombre + empresa
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[TAVILY] FASE 1: nombre + empresa + ubicación")
    resultado = await _tavily_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda=empresa_busqueda,
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        incluir_empresa=True,
        umbral_score=50,
        confianza_base=70)

    if resultado and resultado.get("confianza", 0) >= 70:
        return resultado

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: Fallback solo nombre + ubicación (sin empresa)
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[TAVILY] FASE 2: nombre + ubicación (sin empresa)")
    resultado_fallback = await _tavily_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda="",  # Sin empresa
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        incluir_empresa=False,
        umbral_score=40,
        confianza_base=50  # Menor confianza porque no validó empresa
    )

    # Retornar el mejor resultado
    if resultado and resultado_fallback:
        if resultado["confianza"] >= resultado_fallback["confianza"]:
            return resultado
        return resultado_fallback

    return resultado or resultado_fallback


async def _tavily_buscar_linkedin_interno(
        nombre: str, empresa_busqueda: str, primer_nombre: str, apellido: str,
        ubicacion: str, city: str, province: str, country: str,
        incluir_empresa: bool, umbral_score: int,
        confianza_base: int) -> Optional[dict]:
    """
    Función interna de búsqueda LinkedIn con Tavily.
    """
    try:
        # Construir ubicación simplificada (solo provincia + país)
        ubicacion_simple = ""
        if province and province != "No encontrado":
            ubicacion_simple = province
            if country and country != "No encontrado":
                ubicacion_simple += f", {country}"
        elif country and country != "No encontrado":
            ubicacion_simple = country
        
        # Construir query - usar ubicación simplificada, no completa
        if incluir_empresa and empresa_busqueda:
            if ubicacion_simple:
                query = (f'"{nombre}" "{empresa_busqueda}" '
                         f'{ubicacion_simple} site:linkedin.com/in')
            else:
                query = (f'"{nombre}" "{empresa_busqueda}" '
                         f'site:linkedin.com/in')
        else:
            # Sin empresa, usar ubicación
            if ubicacion_simple:
                query = (f'"{nombre}" {ubicacion_simple} '
                         f'site:linkedin.com/in')
            else:
                query = f'"{nombre}" site:linkedin.com/in'

        logger.info(f"[TAVILY] Query: {query}")

        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "advanced",
                                             "include_domains":
                                             ["linkedin.com"],
                                             "max_results": 15,
                                             "include_raw_content": False
                                         })

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results", [])

            nombre_lower = nombre.lower()
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            empresa_lower = empresa_busqueda.lower(
            ) if empresa_busqueda else ""
            city_lower = city.lower() if city else ""
            province_lower = province.lower() if province else ""
            country_lower = country.lower() if country else ""

            rubros_incompatibles = [
                'pinturas', 'pintura', 'inmobiliaria', 'real estate',
                'abogado', 'lawyer', 'médico', 'doctor', 'dentist'
            ]

            candidatos = []

            for result in results:
                url = result.get("url", "")
                titulo = (result.get("title", "") or "").lower()
                snippet = (result.get("content", "") or "").lower()
                texto = f"{titulo} {snippet}"

                if "linkedin.com/in/" not in url:
                    continue
                if "/company/" in url:
                    continue

                score = 0

                # Scoring por nombre en texto
                if nombre_lower in texto:
                    score += 50
                elif primer_lower in texto and apellido_lower in texto:
                    score += 45

                # Scoring por URL slug
                url_slug = ""
                if "/in/" in url:
                    url_slug = (
                        url.split("/in/")[1].split("/")[0].split("?")[0])
                url_slug_clean = url_slug.lower().replace("-", " ")

                if primer_lower in url_slug_clean and apellido_lower in url_slug_clean:
                    score += 40
                elif apellido_lower in url_slug_clean:
                    score += 25

                # ═══════════════════════════════════════════════════════
                # VALIDACIÓN ESTRICTA: debe tener nombre Y apellido
                # en texto O en URL
                # ═══════════════════════════════════════════════════════
                tiene_primer_nombre = (
                    primer_lower in texto or 
                    primer_lower in url_slug_clean
                )
                tiene_apellido = (
                    apellido_lower in texto or 
                    apellido_lower in url_slug_clean
                )
                tiene_match_nombre = tiene_primer_nombre and tiene_apellido
                
                # Scoring por empresa (solo si ya tiene match de nombre)
                tiene_match_empresa = False
                if empresa_lower and empresa_lower in texto:
                    tiene_match_empresa = True
                    score += 30

                # ═══════════════════════════════════════════════════════
                # SCORING POR UBICACIÓN (NUEVO)
                # ═══════════════════════════════════════════════════════
                if city_lower and city_lower in texto:
                    score += 15
                    logger.debug(f"[TAVILY] +15 por ciudad: {city}")
                if province_lower and province_lower in texto:
                    score += 10
                    logger.debug(f"[TAVILY] +10 por provincia: {province}")
                if country_lower and country_lower in texto:
                    score += 5
                    logger.debug(f"[TAVILY] +5 por país: {country}")

                # Detectar rubros incompatibles
                tiene_rubro_incompatible = False
                for rubro in rubros_incompatibles:
                    if rubro in texto and not tiene_match_empresa:
                        tiene_rubro_incompatible = True
                        break

                if tiene_rubro_incompatible:
                    logger.info(
                        f"[TAVILY] Descartado (rubro incompatible): {url}")
                    continue

                # Aceptar si tiene match de nombre y supera umbral
                if tiene_match_nombre and score >= umbral_score:
                    logger.info(
                        f"[TAVILY] Candidato: {url} "
                        f"(nombre: {tiene_match_nombre}, "
                        f"empresa: {tiene_match_empresa}, score: {score})")
                    candidatos.append({
                        "url": url.split("?")[0],
                        "confianza": min(score, 100),
                        "score": score,
                        "tiene_empresa": tiene_match_empresa
                    })

            candidatos.sort(key=lambda x: x["confianza"], reverse=True)

            if candidatos:
                # Devolver hasta 3 candidatos separados por " | "
                resultados = []
                for c in candidatos[:3]:
                    conf = min(95, confianza_base + (c["score"] - umbral_score))
                    resultados.append({"url": c["url"], "confianza": conf})
                
                mejor_conf = resultados[0]["confianza"]
                
                if len(resultados) == 1:
                    logger.info(f"[TAVILY] ✓ LinkedIn: {resultados[0]['url']}")
                    return resultados[0]
                else:
                    urls = [r["url"] for r in resultados]
                    logger.info(f"[TAVILY] ✓ LinkedIn múltiples: {len(urls)}")
                    return {"url": " | ".join(urls), "confianza": mejor_conf}

            return None

    except Exception as e:
        logger.error(f"[TAVILY] Error buscando LinkedIn personal: {e}")
        return None


async def google_buscar_linkedin_personal(nombre: str,
                                          empresa_busqueda: str,
                                          primer_nombre: str,
                                          apellido: str,
                                          confianza_actual: int,
                                          ubicacion: str = "",
                                          city: str = "",
                                          province: str = "",
                                          country: str = "") -> Optional[dict]:
    """
    Busca LinkedIn personal con Google Custom Search (2 FASES).
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return None

    # ═══════════════════════════════════════════════════════════════════
    # FASE 1: Búsqueda con nombre + empresa
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[GOOGLE] FASE 1: nombre + empresa + ubicación")
    resultado = await _google_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda=empresa_busqueda,
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        confianza_actual=confianza_actual,
        incluir_empresa=True,
        umbral_score=50,
        confianza_base=70)

    if resultado and resultado.get("confianza", 0) >= 70:
        return resultado

    # ═══════════════════════════════════════════════════════════════════
    # FASE 2: Fallback solo nombre + ubicación (sin empresa)
    # ═══════════════════════════════════════════════════════════════════
    logger.info(f"[GOOGLE] FASE 2: nombre + ubicación (sin empresa)")
    resultado_fallback = await _google_buscar_linkedin_interno(
        nombre=nombre,
        empresa_busqueda="",
        primer_nombre=primer_nombre,
        apellido=apellido,
        ubicacion=ubicacion,
        city=city,
        province=province,
        country=country,
        confianza_actual=confianza_actual,
        incluir_empresa=False,
        umbral_score=40,
        confianza_base=50)

    if resultado and resultado_fallback:
        if resultado["confianza"] >= resultado_fallback["confianza"]:
            return resultado
        return resultado_fallback

    return resultado or resultado_fallback


async def _google_buscar_linkedin_interno(
        nombre: str, empresa_busqueda: str, primer_nombre: str, apellido: str,
        ubicacion: str, city: str, province: str, country: str,
        confianza_actual: int, incluir_empresa: bool, umbral_score: int,
        confianza_base: int) -> Optional[dict]:
    """
    Función interna de búsqueda LinkedIn con Google.
    """
    try:
        # Construir ubicación simplificada (solo provincia + país)
        ubicacion_simple = ""
        if province and province != "No encontrado":
            ubicacion_simple = province
            if country and country != "No encontrado":
                ubicacion_simple += f" {country}"
        elif country and country != "No encontrado":
            ubicacion_simple = country
        
        # Construir query con ubicación simplificada
        if incluir_empresa and empresa_busqueda:
            if ubicacion_simple:
                query = (f"site:linkedin.com/in {nombre} "
                         f"{empresa_busqueda} {ubicacion_simple}")
            else:
                query = f"site:linkedin.com/in {nombre} {empresa_busqueda}"
        else:
            if ubicacion_simple:
                query = f"site:linkedin.com/in {nombre} {ubicacion_simple}"
            else:
                query = f"site:linkedin.com/in {nombre}"

        url = (f"https://www.googleapis.com/customsearch/v1"
               f"?cx={GOOGLE_SEARCH_CX}"
               f"&q={quote(query)}&num=10&key={GOOGLE_API_KEY}")

        logger.info(f"[GOOGLE] Query: {query}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(f"[GOOGLE] Error {response.status_code} "
                               f"buscando LinkedIn personal")
                return None

            data = response.json()
            items = data.get("items", [])

            nombre_lower = nombre.lower()
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            empresa_lower = empresa_busqueda.lower(
            ) if empresa_busqueda else ""
            city_lower = city.lower() if city else ""
            province_lower = province.lower() if province else ""
            country_lower = country.lower() if country else ""

            rubros_incompatibles = [
                'pinturas', 'pintura', 'inmobiliaria', 'real estate',
                'abogado', 'lawyer', 'médico', 'doctor', 'dentist'
            ]

            candidatos = []

            for item in items:
                link = item.get("link", "")
                titulo = (item.get("title", "") or "").lower()
                snippet = (item.get("snippet", "") or "").lower()
                texto = f"{titulo} {snippet}"

                if "linkedin.com/in/" not in link:
                    continue

                score = 0

                # Scoring por nombre en texto
                if nombre_lower in texto:
                    score += 40
                elif primer_lower in texto and apellido_lower in texto:
                    score += 35

                # Scoring por URL slug
                url_slug = ""
                if "/in/" in link:
                    url_slug = (
                        link.split("/in/")[1].split("/")[0].split("?")[0])
                url_slug_lower = url_slug.lower().replace("-", "")
                url_slug_clean = url_slug.lower().replace("-", " ")

                if (primer_lower in url_slug_lower
                        and apellido_lower in url_slug_lower):
                    score += 30
                elif apellido_lower in url_slug_lower:
                    score += 15

                # ═══════════════════════════════════════════════════════
                # VALIDACIÓN ESTRICTA: debe tener nombre Y apellido
                # en texto O en URL
                # ═══════════════════════════════════════════════════════
                tiene_primer_nombre = (
                    primer_lower in texto or 
                    primer_lower in url_slug_clean
                )
                tiene_apellido = (
                    apellido_lower in texto or 
                    apellido_lower in url_slug_clean
                )
                tiene_match_nombre = tiene_primer_nombre and tiene_apellido
                
                # Scoring por empresa (solo si ya tiene match de nombre)
                tiene_match_empresa = False
                if empresa_lower and empresa_lower in texto:
                    tiene_match_empresa = True
                    score += 30

                # ═══════════════════════════════════════════════════════
                # SCORING POR UBICACIÓN (NUEVO)
                # ═══════════════════════════════════════════════════════
                if city_lower and city_lower in texto:
                    score += 15
                if province_lower and province_lower in texto:
                    score += 10
                if country_lower and country_lower in texto:
                    score += 5

                # Detectar rubros incompatibles
                tiene_rubro_incompatible = False
                for rubro in rubros_incompatibles:
                    if rubro in texto and not tiene_match_empresa:
                        tiene_rubro_incompatible = True
                        break

                if tiene_rubro_incompatible:
                    logger.info(
                        f"[GOOGLE] Descartado (rubro incompatible): {link}")
                    continue

                if tiene_match_nombre and score >= umbral_score:
                    logger.info(
                        f"[GOOGLE] Candidato: {link} "
                        f"(nombre: {tiene_match_nombre}, "
                        f"empresa: {tiene_match_empresa}, score: {score})")
                    candidatos.append({
                        "url": link, 
                        "score": score,
                        "tiene_empresa": tiene_match_empresa
                    })

            candidatos.sort(key=lambda x: x["score"], reverse=True)

            if candidatos:
                # Devolver hasta 3 candidatos separados por " | "
                resultados = []
                for c in candidatos[:3]:
                    conf = min(95, confianza_base + (c["score"] - umbral_score))
                    resultados.append({"url": c["url"], "confianza": conf})
                
                mejor = resultados[0]
                if mejor["confianza"] > confianza_actual:
                    if len(resultados) == 1:
                        logger.info(f"[GOOGLE] ✓ LinkedIn: {mejor['url']}")
                        return mejor
                    else:
                        urls = [r["url"] for r in resultados]
                        logger.info(f"[GOOGLE] ✓ LinkedIn múltiples: {len(urls)}")
                        return {
                            "url": " | ".join(urls),
                            "confianza": mejor["confianza"]
                        }

            return None

    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando LinkedIn personal: {e}")
        return None


async def apify_buscar_noticias(empresa_busqueda: str,
                                ubicacion_query: str = "") -> List[dict]:
    """
    Busca noticias usando Apify website-content-crawler.
    """
    if not APIFY_API_TOKEN:
        return []

    try:
        # Query para Google News - usar nombre completo
        # Si empresa_busqueda es solo siglas (DPM), agregar contexto
        query_parts = []
        
        # Usar nombre completo entre comillas para exactitud
        if empresa_busqueda:
            # Si parece sigla (menos de 5 chars), buscar con 
            # más contexto
            if len(empresa_busqueda.replace(" ", "")) <= 5:
                query_parts.append(f'"{empresa_busqueda}"')
            else:
                query_parts.append(f'"{empresa_busqueda}"')
        
        # Agregar rubro si está disponible (viene del context)
        # Por ahora solo ubicación
        if ubicacion_query:
            query_parts.append(ubicacion_query)
        
        query = " ".join(query_parts)

        # URLs de noticias
        news_urls = [
            f"https://news.google.com/search?q={quote(query)}&hl=es-419",
            f"https://www.bing.com/news/search?q={quote(query)}"
        ]

        start_urls = [{"url": u} for u in news_urls]

        async with httpx.AsyncClient(timeout=APIFY_TIMEOUT) as client:
            # Iniciar el crawler
            response = await client.post(
                f"https://api.apify.com/v2/acts/apify~website-content-crawler"
                f"/runs?token={APIFY_API_TOKEN}&waitForFinish=30",
                json={
                    "startUrls": start_urls,
                    "maxCrawlPages": 20,
                    "maxCrawlDepth": 1,
                    "proxyConfiguration": {
                        "useApifyProxy": True
                    }
                })

            if response.status_code != 201:
                logger.warning(
                    f"[APIFY] Error iniciando crawler: {response.status_code}")
                return []

            run_data = response.json()
            dataset_id = run_data.get("data", {}).get("defaultDatasetId")

            if not dataset_id:
                return []

            # Obtener resultados
            results_response = await client.get(
                f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                f"?token={APIFY_API_TOKEN}")

            if results_response.status_code != 200:
                return []

            items = results_response.json()

            empresa_lower = empresa_busqueda.lower()
            noticias = []

            for item in items:
                url = item.get("url", "")
                titulo = item.get("title", "") or ""
                texto = item.get("text", "") or ""
                texto_lower = texto.lower()

                # Las redes sociales ya se filtran en es_url_valida_noticia
                # No las procesamos como noticias

                # Saltar buscadores y registros legales
                if es_buscador(url):
                    continue
                if es_registro_legal(url, f"{titulo} {texto}"):
                    continue

                if not es_url_valida_noticia(url, f"{titulo} {texto}",
                                             empresa_busqueda):
                    logger.debug(f"[NOTICIAS] Descartado: {url[:50]}...")
                    continue

                # Verificar relevancia
                palabras_empresa = [
                    p for p in empresa_lower.split() if len(p) > 3
                ]
                if (empresa_lower in texto_lower
                        or any(p in texto_lower for p in palabras_empresa)):
                    noticia = {
                        "titulo": titulo[:200] if titulo else "Sin título",
                        "url": url,
                        "resumen": texto[:300] if texto else "",
                        "source": "apify"
                    }

                    noticias.append(noticia)

            noticias_finales = noticias

            logger.info(
                f"[APIFY] ✓ {len(noticias_finales)} noticias procesadas")
            return noticias_finales[:10]

    except asyncio.TimeoutError:
        logger.warning("[APIFY] Timeout esperando crawler")
        return []
    except Exception as e:
        logger.error(f"[APIFY] Error: {e}")
        return []


async def google_buscar_noticias(empresa: str, empresa_busqueda: str,
                                 ubicacion_query: str) -> List[dict]:
    """
    Busca noticias relevantes de la empresa con Google.
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return []

    try:
        query_parts = []
        
        # Usar nombre completo de empresa
        if empresa:
            query_parts.append(f'"{empresa}"')
        
        # Si empresa_busqueda es diferente (tiene dominio), 
        # agregarlo
        if empresa_busqueda and empresa_busqueda != empresa:
            # Extraer dominio limpio si es URL
            dominio = empresa_busqueda.replace(
                "https://", "").replace(
                "http://", "").replace(
                "www.", "").split("/")[0]
            if "." in dominio:
                query_parts.append(f'OR "{dominio}"')
        
        query_parts.append("noticias OR prensa OR nota")

        query = " ".join(query_parts)
        url = (f"https://www.googleapis.com/customsearch/v1"
               f"?cx={GOOGLE_SEARCH_CX}&q={quote(query)}"
               f"&num=10&key={GOOGLE_API_KEY}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(
                    f"[GOOGLE] Error {response.status_code} buscando noticias")
                return []

            data = response.json()
            items = data.get("items", [])

            empresa_lower = empresa.lower()
            palabras_clave = [p for p in empresa_lower.split() if len(p) > 2]

            noticias = []

            for item in items:
                url = item.get("link", "")
                titulo = item.get("title", "") or ""
                snippet = item.get("snippet", "") or ""
                texto = f"{titulo} {snippet}"
                texto_lower = texto.lower()

                # Las redes sociales ya se filtran en es_url_valida_noticia
                # No las procesamos como noticias

                if es_buscador(url):
                    continue
                if es_registro_legal(url, texto):
                    continue

                if not es_url_valida_noticia(url, texto, empresa_busqueda):
                    continue

                # Verificar relevancia
                matches = sum(1 for p in palabras_clave if p in texto_lower)
                if matches >= 1 or empresa_lower in texto_lower:
                    noticia = {
                        "titulo": titulo[:200] if titulo else "Sin título",
                        "url": url,
                        "resumen": snippet[:300] if snippet else "",
                        "source": "google"
                    }

                    noticias.append(noticia)

            noticias_finales = noticias

            logger.info(
                f"[GOOGLE] ✓ {len(noticias_finales)} noticias encontradas")
            return noticias_finales[:10]

    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando noticias: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES WRAPPER PARA BACKWARD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════


async def search_news(business_name: str,
                      person_name: str = "",
                      location: str = "") -> List[dict]:
    """Wrapper para búsqueda de noticias."""
    if APIFY_API_TOKEN:
        noticias = await apify_buscar_noticias(business_name, location)
        if noticias:
            return noticias
    return await google_buscar_noticias(business_name, business_name, location)
