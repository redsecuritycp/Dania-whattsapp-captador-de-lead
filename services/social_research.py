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
APIFY_TIMEOUT = 200.0


def es_url_valida_noticia(url: str, texto: str, empresa: str) -> bool:
    """Valida si una URL es una noticia real y relevante."""
    url_lower = url.lower()
    texto_lower = texto.lower()
    empresa_lower = empresa.lower()

    if url_lower.endswith('.pdf'):
        return False

    dominios_basura = [
        'pdfcoffee', 'scribd', 'academia.edu', 'slideshare', 'coursehero',
        'repositorio', 'bitstream', 'handle/', 'thesis', 'tesis',
        'icj-cij.org', 'cancilleria.gob', 'boletinoficial'
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
    """Verifica si la URL es de un buscador."""
    buscadores = [
        'google.com/search', 'bing.com/search', 'yahoo.com/search',
        'duckduckgo.com'
    ]
    return any(b in url.lower() for b in buscadores)


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


async def research_person_and_company(nombre_persona: str,
                                      empresa: str,
                                      website: str = "",
                                      linkedin_empresa_input: str = "",
                                      facebook_empresa_input: str = "",
                                      instagram_empresa_input: str = "",
                                      city: str = "",
                                      province: str = "",
                                      country: str = "") -> dict:
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
        # PASO 3: TAVILY - BUSCAR LINKEDIN PERSONAL (2 FASES)
        # ═══════════════════════════════════════════════════════════════
        if TAVILY_API_KEY:
            logger.info(f"[TAVILY] Buscando LinkedIn personal...")
            linkedin_result = await tavily_buscar_linkedin_personal(
                results["nombre"], empresa_busqueda, results["primer_nombre"],
                results["apellido"], ubicacion_completa, city, province,
                country)
            if linkedin_result:
                results["linkedin_personal"] = linkedin_result.get(
                    "url", "No encontrado")
                results["linkedin_personal_confianza"] = linkedin_result.get(
                    "confianza", 0)
                results["linkedin_personal_source"] = "tavily"
                logger.info(
                    f"[TAVILY] ✓ LinkedIn: {results['linkedin_personal']} "
                    f"(conf: {results['linkedin_personal_confianza']})")

        # ═══════════════════════════════════════════════════════════════
        # PASO 4: GOOGLE - FALLBACK LINKEDIN PERSONAL (2 FASES)
        # ═══════════════════════════════════════════════════════════════
        if ((results["linkedin_personal"] == "No encontrado"
             or results["linkedin_personal_confianza"] < 70) and GOOGLE_API_KEY
                and GOOGLE_SEARCH_CX):
            logger.info(f"[GOOGLE] Fallback: buscando LinkedIn personal...")
            google_linkedin = await google_buscar_linkedin_personal(
                results["nombre"], empresa_busqueda, results["primer_nombre"],
                results["apellido"], results["linkedin_personal_confianza"],
                ubicacion_completa, city, province, country)
            if google_linkedin:
                nueva_conf = google_linkedin.get("confianza", 0)
                if nueva_conf > results["linkedin_personal_confianza"]:
                    results["linkedin_personal"] = google_linkedin.get(
                        "url", results["linkedin_personal"])
                    results["linkedin_personal_confianza"] = nueva_conf
                    results["linkedin_personal_source"] = "google"
                    logger.info(
                        f"[GOOGLE] ✓ LinkedIn: {results['linkedin_personal']}")

        # ═══════════════════════════════════════════════════════════════
        # PASO 5: NOTICIAS - APIFY + GOOGLE FALLBACK
        # ═══════════════════════════════════════════════════════════════
        noticias = []

        if APIFY_API_TOKEN:
            logger.info(f"[APIFY] Buscando noticias con crawler...")
            noticias = await apify_buscar_noticias(empresa_busqueda,
                                                   ubicacion_query)
            if noticias:
                results["noticias_source"] = "apify"

        if not noticias and GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[GOOGLE] Fallback: buscando noticias...")
            noticias = await google_buscar_noticias(empresa, empresa_busqueda,
                                                    ubicacion_query)
            if noticias:
                results["noticias_source"] = "google"

        if noticias:
            results["noticias_lista"] = noticias
            results["noticias_count"] = len(noticias)

            noticias_texto = []
            for n in noticias[:10]:
                titulo = n.get("titulo", "Sin título")
                url = n.get("url", "")
                source = n.get("source", "web")

                if 'linkedin.com' in url.lower():
                    source_label = 'LINKEDIN'
                elif 'facebook.com' in url.lower():
                    source_label = 'FACEBOOK'
                elif 'instagram.com' in url.lower():
                    source_label = 'INSTAGRAM'
                elif source == 'apify':
                    source_label = url.split('/')[2].replace(
                        'www.', '').split('.')[0].upper()
                else:
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
        # Construir query
        if incluir_empresa and empresa_busqueda:
            if ubicacion and ubicacion != "No encontrado":
                query = (f'"{nombre}" "{empresa_busqueda}" '
                         f'"{ubicacion}" site:linkedin.com/in')
            else:
                query = f'"{nombre}" "{empresa_busqueda}" site:linkedin.com/in'
        else:
            # Sin empresa, usar ubicación más prominente
            if ubicacion and ubicacion != "No encontrado":
                query = f'"{nombre}" "{ubicacion}" site:linkedin.com/in'
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
                tiene_match_nombre = False
                tiene_match_empresa = False

                # Scoring por nombre completo en texto
                if nombre_lower in texto:
                    score += 50
                    tiene_match_nombre = True
                elif primer_lower in texto and apellido_lower in texto:
                    score += 45
                    tiene_match_nombre = True

                # Scoring por URL slug
                url_slug = ""
                if "/in/" in url:
                    url_slug = (
                        url.split("/in/")[1].split("/")[0].split("?")[0])
                url_slug_clean = url_slug.lower().replace("-", " ")

                if primer_lower in url_slug_clean and apellido_lower in url_slug_clean:
                    score += 40
                    tiene_match_nombre = True
                elif apellido_lower in url_slug_clean:
                    score += 25

                if apellido_lower in texto and primer_lower in texto:
                    tiene_match_nombre = True
                    score += 10

                # Scoring por empresa (si aplica)
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
                        "score": score
                    })

            candidatos.sort(key=lambda x: x["confianza"], reverse=True)

            if candidatos:
                resultados = []
                for c in candidatos[:3]:
                    conf = min(95,
                               confianza_base + (c["score"] - umbral_score))
                    resultados.append({"url": c["url"], "confianza": conf})

                if len(resultados) == 1:
                    return resultados[0]
                else:
                    urls = [r["url"] for r in resultados]
                    mejor_conf = resultados[0]["confianza"]
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
        # Construir query
        if incluir_empresa and empresa_busqueda:
            if ubicacion and ubicacion != "No encontrado":
                query = (f"site:linkedin.com/in {nombre} "
                         f"{empresa_busqueda} {ubicacion}")
            else:
                query = f"site:linkedin.com/in {nombre} {empresa_busqueda}"
        else:
            if ubicacion and ubicacion != "No encontrado":
                query = f"site:linkedin.com/in {nombre} {ubicacion}"
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
                tiene_match_nombre = False
                tiene_match_empresa = False

                # Scoring por nombre completo en texto
                if nombre_lower in texto:
                    score += 40
                    tiene_match_nombre = True
                elif primer_lower in texto and apellido_lower in texto:
                    score += 35
                    tiene_match_nombre = True

                # Scoring por URL slug
                url_slug = ""
                if "/in/" in link:
                    url_slug = (
                        link.split("/in/")[1].split("/")[0].split("?")[0])
                url_slug_lower = url_slug.lower().replace("-", "")

                if (primer_lower in url_slug_lower
                        and apellido_lower in url_slug_lower):
                    score += 30
                    tiene_match_nombre = True
                elif apellido_lower in url_slug_lower:
                    score += 15

                if apellido_lower in texto and primer_lower in texto:
                    tiene_match_nombre = True
                    score += 10

                # Scoring por empresa (si aplica)
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
                    candidatos.append({"url": link, "score": score})

            candidatos.sort(key=lambda x: x["score"], reverse=True)

            if candidatos:
                resultados = []
                for c in candidatos[:3]:
                    conf = min(95,
                               confianza_base + (c["score"] - umbral_score))
                    resultados.append({"url": c["url"], "confianza": conf})

                mejor = resultados[0]
                if mejor["confianza"] > confianza_actual:
                    if len(resultados) == 1:
                        return mejor
                    else:
                        urls = [r["url"] for r in resultados]
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
        # Query para Google News
        query_parts = [empresa_busqueda]
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
                f"/runs?token={APIFY_API_TOKEN}&waitForFinish=180",
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
            noticias_redes_sociales = []

            for item in items:
                url = item.get("url", "")
                titulo = item.get("title", "") or ""
                texto = item.get("text", "") or ""
                texto_lower = texto.lower()

                # Detectar si es red social de empresa
                es_red_social_empresa = (es_red_social(url)
                                         and empresa_lower in texto_lower)

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

                    if es_red_social_empresa:
                        noticias_redes_sociales.append(noticia)
                    else:
                        noticias.append(noticia)

            noticias_finales = noticias_redes_sociales + noticias

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
        if empresa:
            query_parts.append(f'"{empresa}"')
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
            noticias_redes_sociales = []

            for item in items:
                url = item.get("link", "")
                titulo = item.get("title", "") or ""
                snippet = item.get("snippet", "") or ""
                texto = f"{titulo} {snippet}"
                texto_lower = texto.lower()

                es_red_social_empresa = (es_red_social(url)
                                         and empresa_lower in texto_lower)

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

                    if es_red_social_empresa:
                        noticias_redes_sociales.append(noticia)
                    else:
                        noticias.append(noticia)

            noticias_finales = noticias_redes_sociales + noticias

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
