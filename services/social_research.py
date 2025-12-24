"""
Servicio de investigación de redes sociales y noticias para DANIA/Fortia
RÉPLICA FIEL del workflow n8n: Tool_Investigacion_redes_y_noticias v11.3

Flujo:
1. Preparar datos y limpiar inputs
2. Tavily: Verificar nombre completo en sitio web
3. Tavily: Buscar LinkedIn personal (site:linkedin.com/in)
4. Google: Fallback LinkedIn personal
5. Google: Buscar LinkedIn empresa
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

from config import TAVILY_API_KEY, GOOGLE_API_KEY, GOOGLE_SEARCH_CX, APIFY_API_TOKEN

logger = logging.getLogger(__name__)

# Timeout para requests HTTP
HTTP_TIMEOUT = 30.0
APIFY_TIMEOUT = 200.0  # Apify puede tardar más


async def research_person_and_company(
    nombre_persona: str,
    empresa: str,
    website: str = "",
    linkedin_empresa_input: str = "",
    facebook_empresa_input: str = "",
    instagram_empresa_input: str = "",
    city: str = "",
    province: str = "",
    country: str = ""
) -> dict:
    """
    Función principal que replica el workflow completo de n8n.
    """
    logger.info(f"[RESEARCH] ========== Iniciando investigación ==========")
    logger.info(f"[RESEARCH] Persona: {nombre_persona}, Empresa: {empresa}, Web: {website}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PASO 1: PREPARAR DATOS (equivalente a Preparar_Datos en n8n)
    # ═══════════════════════════════════════════════════════════════════
    
    nombre = nombre_persona.strip()
    nombre_partes = nombre.split()
    primer_nombre = nombre_partes[0] if nombre_partes else ""
    apellido = nombre_partes[-1] if len(nombre_partes) > 1 else ""
    
    # Limpiar website
    website_limpio = website.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    tiene_website = bool(website_limpio)
    
    # empresa_busqueda usa WEBSITE cuando existe (FIX v11.3)
    empresa_busqueda = website_limpio if website_limpio else empresa
    
    # Ubicación
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
    results = {
        "nombre_original": nombre,
        "nombre": nombre,
        "primer_nombre": primer_nombre,
        "apellido": apellido,
        "empresa": empresa,
        "website": website,
        "website_limpio": website_limpio,
        "empresa_busqueda": empresa_busqueda,
        
        # LinkedIn personal
        "linkedin_personal": "No encontrado",
        "linkedin_personal_confianza": 0,
        "linkedin_personal_source": "ninguno",
        
        # LinkedIn empresa
        "linkedin_empresa": linkedin_empresa_input or "No encontrado",
        "linkedin_empresa_source": "web_cliente" if linkedin_empresa_input else "ninguno",
        "buscar_linkedin_empresa": not linkedin_empresa_input or linkedin_empresa_input == "No encontrado",
        
        # Otras redes (SOLO de la web del cliente, NO se buscan)
        "facebook_empresa": facebook_empresa_input or "No encontrado",
        "instagram_empresa": instagram_empresa_input or "No encontrado",
        
        # Noticias
        "noticias_lista": [],
        "noticias_empresa": "No se encontraron noticias",
        "noticias_count": 0,
        "noticias_source": "ninguno"
    }
    
    try:
        # ═══════════════════════════════════════════════════════════════════
        # PASO 2: TAVILY - VERIFICAR NOMBRE EN SITIO WEB
        # ═══════════════════════════════════════════════════════════════════
        if tiene_website and TAVILY_API_KEY:
            logger.info(f"[TAVILY] Verificando nombre en sitio web...")
            nombre_verificado = await tavily_verificar_nombre(
                website_limpio, primer_nombre, apellido
            )
            if nombre_verificado:
                results["nombre"] = nombre_verificado
                results["nombre_verificado"] = True
                # Actualizar partes del nombre
                partes = nombre_verificado.split()
                results["primer_nombre"] = partes[0] if partes else primer_nombre
                results["apellido"] = partes[-1] if len(partes) > 1 else apellido
                logger.info(f"[TAVILY] ✓ Nombre verificado: {nombre_verificado}")
        
        # ═══════════════════════════════════════════════════════════════════
        # PASO 3: TAVILY - BUSCAR LINKEDIN PERSONAL (site:linkedin.com/in)
        # ═══════════════════════════════════════════════════════════════════
        if TAVILY_API_KEY:
            logger.info(f"[TAVILY] Buscando LinkedIn personal...")
            linkedin_result = await tavily_buscar_linkedin_personal(
                results["nombre"],
                empresa_busqueda,
                results["primer_nombre"],
                results["apellido"],
                city  # Agregar ciudad para mayor precisión
            )
            if linkedin_result:
                results["linkedin_personal"] = linkedin_result.get("url", "No encontrado")
                results["linkedin_personal_confianza"] = linkedin_result.get("confianza", 0)
                results["linkedin_personal_source"] = "tavily"
                logger.info(f"[TAVILY] ✓ LinkedIn: {results['linkedin_personal']} (conf: {results['linkedin_personal_confianza']})")
        
        # ═══════════════════════════════════════════════════════════════════
        # PASO 4: GOOGLE - FALLBACK LINKEDIN PERSONAL
        # ═══════════════════════════════════════════════════════════════════
        if (results["linkedin_personal"] == "No encontrado" or 
            results["linkedin_personal_confianza"] < 70) and GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[GOOGLE] Fallback: buscando LinkedIn personal...")
            google_linkedin = await google_buscar_linkedin_personal(
                results["nombre"],
                empresa_busqueda,
                results["primer_nombre"],
                results["apellido"],
                results["linkedin_personal_confianza"],
                city  # Agregar ciudad para mayor precisión
            )
            if google_linkedin:
                results["linkedin_personal"] = google_linkedin.get("url", results["linkedin_personal"])
                results["linkedin_personal_confianza"] = google_linkedin.get("confianza", results["linkedin_personal_confianza"])
                results["linkedin_personal_source"] = "google"
                logger.info(f"[GOOGLE] ✓ LinkedIn: {results['linkedin_personal']}")
        
        # ═══════════════════════════════════════════════════════════════════
        # PASO 5: GOOGLE - BUSCAR LINKEDIN EMPRESA
        # ═══════════════════════════════════════════════════════════════════
        logger.info(f"[RESEARCH] buscar_linkedin_empresa={results['buscar_linkedin_empresa']}, input={linkedin_empresa_input}")
        if results["buscar_linkedin_empresa"] and GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[GOOGLE] Buscando LinkedIn empresa...")
            linkedin_empresa = await google_buscar_linkedin_empresa(
                empresa, empresa_busqueda, country
            )
            if linkedin_empresa:
                results["linkedin_empresa"] = linkedin_empresa
                results["linkedin_empresa_source"] = "google"
                logger.info(f"[GOOGLE] ✓ LinkedIn empresa: {linkedin_empresa}")
        
        # ═══════════════════════════════════════════════════════════════════
        # PASO 6: APIFY - CRAWLER DE NOTICIAS (NUEVO)
        # ═══════════════════════════════════════════════════════════════════
        noticias = []
        if APIFY_API_TOKEN:
            logger.info(f"[APIFY] Buscando noticias con crawler...")
            noticias = await apify_buscar_noticias(empresa_busqueda, ubicacion_query)
            if noticias:
                results["noticias_source"] = "apify"
                logger.info(f"[APIFY] ✓ {len(noticias)} noticias encontradas")
        
        # ═══════════════════════════════════════════════════════════════════
        # PASO 7: GOOGLE - NOTICIAS FALLBACK
        # ═══════════════════════════════════════════════════════════════════
        if not noticias and GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
            logger.info(f"[GOOGLE] Fallback: buscando noticias...")
            noticias = await google_buscar_noticias(
                empresa, empresa_busqueda, ubicacion_query
            )
            if noticias:
                results["noticias_source"] = "google"
        
        # Procesar noticias encontradas
        if noticias:
            results["noticias_lista"] = noticias
            results["noticias_count"] = len(noticias)
            
            # Formatear noticias para mostrar (con [SOURCE] como n8n)
            noticias_texto = []
            for n in noticias[:5]:
                titulo = n.get('titulo', 'Sin título')
                url = n.get('url', '')
                source = n.get('source', '')
                domain = n.get('domain', '')
                
                # Determinar source label
                if source:
                    source_label = source.upper()
                elif domain:
                    source_label = domain.replace('www.', '').split('/')[0].upper()
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
    logger.info(f"[RESEARCH] LinkedIn personal: {results['linkedin_personal']} (conf: {results['linkedin_personal_confianza']})")
    logger.info(f"[RESEARCH] LinkedIn empresa: {results['linkedin_empresa']}")
    logger.info(f"[RESEARCH] Noticias: {results['noticias_count']} ({results['noticias_source']})")
    
    return results


async def tavily_verificar_nombre(website: str, primer_nombre: str, apellido: str) -> Optional[str]:
    """
    Busca en el sitio web para verificar/encontrar el nombre completo.
    Equivalente a Tavily_Verificar_Nombre en n8n.
    """
    if not TAVILY_API_KEY:
        return None
    
    try:
        # Query EXACTO como n8n
        query = f'site:{website} "{primer_nombre}" OR "{apellido}" equipo nosotros about contacto'
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "include_raw_content": True,
                    "max_results": 5
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            results = data.get("results", [])
            
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            
            # 5 Patrones para encontrar nombres completos (como n8n)
            patrones = [
                # Nombre + segundo nombre + apellido
                re.compile(rf'{primer_lower}\s+[a-záéíóúñ]+\s+{apellido_lower}', re.IGNORECASE),
                # Con título profesional
                re.compile(rf'(?:ing\.?|dr\.?|lic\.?|arq\.?|sr\.?|sra\.?|cpa\.?|mba\.?)\s*{primer_lower}\s+(?:[a-záéíóúñ]+\s+)?{apellido_lower}', re.IGNORECASE),
                # Nombre simple
                re.compile(rf'{primer_lower}\s+{apellido_lower}', re.IGNORECASE),
                # Apellido, Nombre
                re.compile(rf'{apellido_lower},?\s+{primer_lower}', re.IGNORECASE),
                # Con "de" o "del"
                re.compile(rf'{primer_lower}\s+(?:de\s+|del\s+)?[a-záéíóúñ]+\s+{apellido_lower}', re.IGNORECASE)
            ]
            
            mejor_match = None
            mejor_longitud = 0
            
            for result in results:
                contenido = ((result.get("content") or "") + " " + (result.get("raw_content") or "")).lower()
                
                for patron in patrones:
                    matches = patron.findall(contenido)
                    for match in matches:
                        # Limpiar el match
                        nombre_limpio = re.sub(r'^(ing\.?|dr\.?|lic\.?|arq\.?|sr\.?|sra\.?|cpa\.?|mba\.?)\s*', '', match, flags=re.IGNORECASE)
                        nombre_limpio = nombre_limpio.strip()
                        
                        # Capitalizar
                        nombre_limpio = " ".join(p.capitalize() for p in nombre_limpio.split())
                        
                        if len(nombre_limpio) > mejor_longitud and len(nombre_limpio.split()) >= 2:
                            mejor_match = nombre_limpio
                            mejor_longitud = len(nombre_limpio)
            
            return mejor_match
            
    except Exception as e:
        logger.error(f"[TAVILY] Error verificando nombre: {e}")
        return None


async def tavily_buscar_linkedin_personal(nombre: str, empresa_busqueda: str, primer_nombre: str, apellido: str, ciudad: str = "") -> Optional[dict]:
    """
    Busca LinkedIn personal usando Tavily con site:linkedin.com/in.
    Equivalente a Tavily_LinkedIn_Personal en n8n.
    """
    if not TAVILY_API_KEY:
        return None
    
    try:
        # Agregar ciudad para mayor precisión si está disponible
        if ciudad and ciudad != "No encontrado":
            query = f'"{nombre}" "{empresa_busqueda}" "{ciudad}" site:linkedin.com/in'
        else:
            query = f'"{nombre}" "{empresa_busqueda}" site:linkedin.com/in'
        
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "include_domains": ["linkedin.com"],
                    "max_results": 15,
                    "include_raw_content": False
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            results = data.get("results", [])
            
            nombre_lower = nombre.lower()
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            empresa_lower = empresa_busqueda.lower()
            
            candidatos = []
            
            for result in results:
                url = result.get("url", "")
                titulo = (result.get("title", "") or "").lower()
                snippet = (result.get("content", "") or "").lower()
                texto = f"{titulo} {snippet}"
                
                # Debe ser perfil personal, no empresa
                if "linkedin.com/in/" not in url:
                    continue
                if "/company/" in url:
                    continue
                
                score = 0
                tiene_match_nombre = False
                
                # Scoring por nombre completo en texto
                if nombre_lower in texto:
                    score += 50
                    tiene_match_nombre = True
                # Match primer_nombre AND apellido en texto
                elif primer_lower in texto and apellido_lower in texto:
                    score += 45
                    tiene_match_nombre = True
                # Match solo primer_nombre OR apellido en texto
                elif primer_lower in texto or apellido_lower in texto:
                    score += 20
                    tiene_match_nombre = True
                
                # Scoring por URL slug
                url_slug = url.split("/in/")[1].split("/")[0].split("?")[0] if "/in/" in url else ""
                url_slug_clean = url_slug.lower().replace("-", " ")
                
                # Match nombre completo en URL slug
                if primer_lower in url_slug_clean and apellido_lower in url_slug_clean:
                    score += 40
                    tiene_match_nombre = True
                # Match apellido en URL slug
                elif apellido_lower in url_slug_clean:
                    score += 25
                    tiene_match_nombre = True
                
                # Scoring por empresa (BONUS, no activa tiene_match_nombre)
                if empresa_lower in texto:
                    score += 35
                
                # SOLO agregar candidatos si tiene_match_nombre AND score >= 50
                if tiene_match_nombre and score >= 50:
                    candidatos.append({
                        "url": url.split("?")[0],  # Limpiar parámetros
                        "confianza": min(score, 100)
                    })
            
            # Ordenar por confianza
            candidatos.sort(key=lambda x: x["confianza"], reverse=True)
            
            if candidatos:
                return candidatos[0]
            
            return None
            
    except Exception as e:
        logger.error(f"[TAVILY] Error buscando LinkedIn personal: {e}")
        return None


async def google_buscar_linkedin_personal(nombre: str, empresa_busqueda: str, primer_nombre: str, apellido: str, confianza_actual: int, ciudad: str = "") -> Optional[dict]:
    """
    Busca LinkedIn personal con Google Custom Search como fallback.
    Equivalente a Google_LinkedIn_Personal en n8n.
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return None
    
    try:
        # Agregar ciudad para mayor precisión si está disponible
        if ciudad and ciudad != "No encontrado":
            query = f"site:linkedin.com/in {nombre} {empresa_busqueda} {ciudad}"
        else:
            query = f"site:linkedin.com/in {nombre} {empresa_busqueda}"
        url = f"https://www.googleapis.com/customsearch/v1?cx={GOOGLE_SEARCH_CX}&q={quote(query)}&num=10&key={GOOGLE_API_KEY}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"[GOOGLE] Error {response.status_code} buscando LinkedIn personal")
                return None
            
            data = response.json()
            items = data.get("items", [])
            
            nombre_lower = nombre.lower()
            primer_lower = primer_nombre.lower()
            apellido_lower = apellido.lower()
            empresa_lower = empresa_busqueda.lower()
            
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
                
                # Scoring por nombre completo en texto
                if nombre_lower in texto:
                    score += 40
                    tiene_match_nombre = True
                # Match primer_nombre AND apellido en texto
                elif primer_lower in texto and apellido_lower in texto:
                    score += 35
                    tiene_match_nombre = True
                # Match solo primer_nombre OR apellido en texto
                elif primer_lower in texto or apellido_lower in texto:
                    score += 20
                    tiene_match_nombre = True
                
                # Scoring por URL slug
                url_slug = link.split("/in/")[1].split("/")[0].split("?")[0] if "/in/" in link else ""
                url_slug_lower = url_slug.lower().replace("-", "")
                
                # Match nombre completo en URL slug (primer_nombre AND apellido)
                if primer_lower in url_slug_lower and apellido_lower in url_slug_lower:
                    score += 30
                    tiene_match_nombre = True
                # Match apellido en URL slug
                elif apellido_lower in url_slug_lower:
                    score += 15
                    tiene_match_nombre = True
                
                # Scoring por empresa (BONUS, no activa tiene_match_nombre)
                if empresa_lower in texto:
                    score += 25
                
                # SOLO agregar candidatos si tiene_match_nombre AND score >= 30
                if tiene_match_nombre and score >= 30:
                    candidatos.append({"url": link, "score": score})
            
            candidatos.sort(key=lambda x: x["score"], reverse=True)
            
            if candidatos:
                mejor = candidatos[0]
                nueva_confianza = min(95, 55 + mejor["score"])
                
                # Solo actualizar si es mejor que la actual
                if mejor["score"] >= 30 and nueva_confianza > confianza_actual:
                    return {"url": mejor["url"], "confianza": nueva_confianza}
            
            return None
            
    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando LinkedIn personal: {e}")
        return None


async def google_buscar_linkedin_empresa(empresa: str, empresa_busqueda: str, country: str = "") -> Optional[str]:
    """
    Busca LinkedIn de la empresa con Google Custom Search.
    Prioriza resultados del país del usuario.
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return None
    
    # Mapeo país -> código LinkedIn
    country_linkedin_map = {
        "Argentina": "ar",
        "México": "mx",
        "España": "es",
        "Chile": "cl",
        "Colombia": "co",
        "Perú": "pe",
        "Venezuela": "ve",
        "Ecuador": "ec",
        "Bolivia": "bo",
        "Paraguay": "py",
        "Uruguay": "uy",
        "Brasil": "br",
        "Estados Unidos": "us"
    }
    
    country_code = country_linkedin_map.get(country, "")
    
    try:
        # Query con país si está disponible
        if country and country != "Desconocido":
            query = f'site:linkedin.com/company "{empresa_busqueda}" {country}'
        else:
            query = f'site:linkedin.com/company "{empresa_busqueda}"'
        
        url = f"https://www.googleapis.com/customsearch/v1?cx={GOOGLE_SEARCH_CX}&q={quote(query)}&num=10&key={GOOGLE_API_KEY}"
        
        logger.info(f"[GOOGLE] Buscando LinkedIn empresa: {query}")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"[GOOGLE] Error {response.status_code} buscando LinkedIn empresa")
                return None
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                logger.info(f"[GOOGLE] No se encontraron resultados para LinkedIn empresa")
                return None
            
            empresa_lower = empresa.lower()
            empresa_busqueda_lower = empresa_busqueda.lower().replace(".com.ar", "").replace(".com", "").replace("www.", "")
            palabras_clave = [p for p in empresa_lower.split() if len(p) > 2]
            
            candidatos = []
            
            for item in items:
                link = item.get("link", "")
                titulo = (item.get("title", "") or "").lower()
                snippet = (item.get("snippet", "") or "").lower()
                texto = f"{titulo} {snippet}"
                
                if "linkedin.com/company/" not in link:
                    continue
                
                score = 0
                
                # BONUS: Si el link es del país correcto (ar.linkedin.com, mx.linkedin.com, etc)
                if country_code and f"{country_code}.linkedin.com" in link:
                    score += 50
                    logger.info(f"[GOOGLE] Match país ({country_code}): {link}")
                
                # BONUS: Si menciona el país en el texto
                if country and country.lower() in texto:
                    score += 20
                
                # Contar matches de palabras clave
                matches = sum(1 for p in palabras_clave if p in texto)
                score += matches * 10
                
                # Match directo del nombre
                if empresa_lower in texto or empresa_busqueda_lower in texto:
                    score += 30
                
                # Validación: evitar empresas con nombres muy diferentes
                empresa_encontrada = titulo.replace(" | linkedin", "").replace(" - linkedin", "").strip()
                
                # Penalizar si el nombre es muy diferente
                if empresa_lower not in empresa_encontrada and empresa_busqueda_lower not in empresa_encontrada:
                    # Verificar si al menos 2 palabras coinciden
                    palabras_encontradas = empresa_encontrada.split()
                    coincidencias = sum(1 for p in palabras_clave if any(p in pf.lower() for pf in palabras_encontradas))
                    if coincidencias < 1:
                        continue  # Descartar si no hay coincidencia mínima
                
                if score >= 10:
                    candidatos.append({
                        "url": link.split("?")[0],
                        "score": score,
                        "titulo": titulo
                    })
                    logger.info(f"[GOOGLE] Candidato LinkedIn empresa: {link} (score: {score})")
            
            # Ordenar por score
            candidatos.sort(key=lambda x: x["score"], reverse=True)
            
            if candidatos:
                mejor = candidatos[0]
                logger.info(f"[GOOGLE] ✓ Mejor LinkedIn empresa: {mejor['url']} (score: {mejor['score']})")
                return mejor["url"]
            
            return None
            
    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando LinkedIn empresa: {e}")
        return None


def validar_match_empresa(encontrada: str, esperada: str) -> bool:
    """
    Valida que el nombre de empresa encontrado coincida con el esperado.
    Evita falsos positivos como "Red Balloon Security" para "Red Security".
    """
    if not encontrada or not esperada:
        return False
    
    encontrada_lower = encontrada.lower().strip()
    esperada_lower = esperada.lower().strip()
    
    # Coincidencia exacta
    if encontrada_lower == esperada_lower:
        return True
    
    # Palabras a ignorar
    ignore_words = {'srl', 'sa', 'llc', 'inc', 'corp', 'company', 'co', 'ltd', 'the', 'argentina', 'ar'}
    location_prefixes = {'uk', 'us', 'usa', 'eu', 'la', 'latam'}
    
    encontrada_words = set(encontrada_lower.split()) - ignore_words - location_prefixes
    esperada_words = set(esperada_lower.split()) - ignore_words
    
    # Palabras extra significativas que indican empresa diferente
    palabras_significativas = {'balloon', 'global', 'international', 'digital', 'tech', 'solutions', 'group', 'holding'}
    
    palabras_extra = encontrada_words - esperada_words
    if palabras_extra & palabras_significativas:
        return False
    
    # Las palabras de la esperada deben estar en la encontrada
    if esperada_words <= encontrada_words:
        return True
    
    # O compartir la mayoría
    if len(esperada_words) > 0 and len(esperada_words & encontrada_words) >= len(esperada_words) * 0.7:
        return True
    
    return False


async def apify_buscar_noticias(empresa_busqueda: str, ubicacion_query: str = "") -> List[dict]:
    """
    Busca noticias usando Apify website-content-crawler.
    Réplica del nodo Crawler_Noticias en n8n.
    """
    if not APIFY_API_TOKEN:
        return []
    
    try:
        # URLs de búsqueda como en n8n
        search_query = quote(f"{empresa_busqueda} noticias")
        if ubicacion_query:
            search_query = quote(f"{empresa_busqueda} {ubicacion_query} noticias")
        
        start_urls = [
            {"url": f"https://news.google.com/search?q={search_query}&hl=es"},
            {"url": f"https://www.bing.com/news/search?q={search_query}"}
        ]
        
        logger.info(f"[APIFY] Iniciando crawler para: {empresa_busqueda}")
        
        # Usar el actor website-content-crawler
        actor_id = "apify/website-content-crawler"
        
        run_input = {
            "startUrls": start_urls,
            "maxCrawlDepth": 2,
            "maxCrawlPages": 30,
            "maxResultsPerCrawl": 30,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            },
            "crawlerType": "cheerio",
            "includeUrlGlobs": [
                "*noticia*",
                "*news*",
                "*prensa*",
                "*actualidad*",
                "*local*",
                "*municipal*",
                "*regional*",
                "*diario*",
                "*periodico*",
                "*article*"
            ],
            "excludeUrlGlobs": [
                "*facebook.com*",
                "*instagram.com*",
                "*linkedin.com*",
                "*youtube.com*",
                "*twitter.com*",
                "*boletinoficial*",
                "*boletin-oficial*"
            ],
            "maxRequestRetries": 2,
            "requestTimeoutSecs": 30
        }
        
        async with httpx.AsyncClient(timeout=APIFY_TIMEOUT) as client:
            # Iniciar el actor
            run_response = await client.post(
                f"https://api.apify.com/v2/acts/{actor_id}/runs",
                headers={"Authorization": f"Bearer {APIFY_API_TOKEN}"},
                json=run_input,
                params={"waitForFinish": 180}  # Esperar hasta 180 segundos
            )
            
            if run_response.status_code not in [200, 201]:
                logger.warning(f"[APIFY] Error iniciando actor: {run_response.status_code}")
                return []
            
            run_data = run_response.json()
            run_id = run_data.get("data", {}).get("id")
            
            if not run_id:
                logger.warning("[APIFY] No se obtuvo run_id")
                return []
            
            # Esperar a que termine (polling)
            for _ in range(12):  # Max 2 minutos
                await asyncio.sleep(10)
                
                status_response = await client.get(
                    f"https://api.apify.com/v2/actor-runs/{run_id}",
                    headers={"Authorization": f"Bearer {APIFY_API_TOKEN}"}
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("data", {}).get("status")
                    
                    if status == "SUCCEEDED":
                        break
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        logger.warning(f"[APIFY] Crawler terminó con status: {status}")
                        return []
            
            # Obtener resultados
            dataset_id = run_data.get("data", {}).get("defaultDatasetId")
            if not dataset_id:
                return []
            
            items_response = await client.get(
                f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                headers={"Authorization": f"Bearer {APIFY_API_TOKEN}"},
                params={"limit": 50}
            )
            
            if items_response.status_code != 200:
                return []
            
            items = items_response.json()
            
            # Procesar resultados
            noticias = []
            empresa_lower = empresa_busqueda.lower()
            
            for item in items:
                url = item.get("url", "")
                titulo = item.get("title", "") or item.get("metadata", {}).get("title", "")
                texto = item.get("text", "") or item.get("content", "")
                
                # Filtrar
                if es_red_social(url) or es_buscador(url):
                    continue
                if es_registro_legal(url, f"{titulo} {texto}"):
                    continue
                
                texto_lower = f"{titulo} {texto}".lower()
                
                # Verificar relevancia
                if empresa_lower in texto_lower or any(p in texto_lower for p in empresa_lower.split() if len(p) > 3):
                    noticias.append({
                        "titulo": titulo[:200] if titulo else "Sin título",
                        "url": url,
                        "resumen": texto[:300] if texto else "",
                        "source": "apify"
                    })
            
            logger.info(f"[APIFY] ✓ {len(noticias)} noticias procesadas")
            return noticias[:10]
            
    except asyncio.TimeoutError:
        logger.warning("[APIFY] Timeout esperando crawler")
        return []
    except Exception as e:
        logger.error(f"[APIFY] Error: {e}")
        return []


async def google_buscar_noticias(empresa: str, empresa_busqueda: str, ubicacion_query: str) -> List[dict]:
    """
    Busca noticias relevantes de la empresa con Google.
    Equivalente a Google_Noticias_Fallback en n8n.
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return []
    
    try:
        # Query de búsqueda
        query_parts = [f'"{empresa_busqueda}"']
        if ubicacion_query:
            query_parts.append(f'"{ubicacion_query}"')
        query_parts.append("noticias OR inauguró OR anunció OR expansión -boletinoficial")
        
        query = " ".join(query_parts)
        url = f"https://www.googleapis.com/customsearch/v1?cx={GOOGLE_SEARCH_CX}&q={quote(query)}&num=10&key={GOOGLE_API_KEY}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"[GOOGLE] Error {response.status_code} buscando noticias")
                return []
            
            data = response.json()
            items = data.get("items", [])
            
            empresa_lower = empresa.lower()
            empresa_busqueda_lower = empresa_busqueda.lower()
            palabras_clave = [p for p in empresa_lower.split() if len(p) > 2]
            
            noticias = []
            
            for item in items:
                link = item.get("link", "")
                titulo = item.get("title", "")
                snippet = item.get("snippet", "")
                
                # Filtrar redes sociales y buscadores
                if es_red_social(link) or es_buscador(link):
                    continue
                
                # Filtrar registros legales/boletines
                if es_registro_legal(link, f"{titulo} {snippet}"):
                    continue
                
                texto_lower = f"{titulo} {snippet}".lower()
                
                # Contar matches
                matches = sum(1 for p in palabras_clave if p in texto_lower)
                
                if matches >= 2 or empresa_lower in texto_lower or empresa_busqueda_lower in texto_lower:
                    noticias.append({
                        "titulo": titulo,
                        "url": link,
                        "resumen": snippet[:150] if snippet else "",
                        "source": "google",
                        "domain": link.split("/")[2] if "/" in link else ""
                    })
            
            return noticias[:10]
            
    except Exception as e:
        logger.error(f"[GOOGLE] Error buscando noticias: {e}")
        return []


def es_red_social(url: str) -> bool:
    """Verifica si la URL es de una red social."""
    redes = ['linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com', 'youtube.com', 'tiktok.com', 'x.com']
    return any(red in url.lower() for red in redes)


def es_buscador(url: str) -> bool:
    """Verifica si la URL es de un buscador."""
    buscadores = ['google.com/search', 'bing.com/search', 'yahoo.com/search', 'duckduckgo.com']
    return any(b in url.lower() for b in buscadores)


def es_registro_legal(url: str, texto: str) -> bool:
    """Verifica si es un registro legal o boletín oficial."""
    url_lower = url.lower()
    texto_lower = texto.lower()
    
    # Por URL
    if 'boletinoficial' in url_lower or 'boletin-oficial' in url_lower:
        return True
    if '/contratos' in url_lower or 'contratos.pdf' in url_lower:
        return True
    
    # Por contenido
    keywords_legales = [
        'modificación de contrato', 'modificacion de contrato',
        'cesión de cuotas', 'cesion de cuotas',
        'constitución de sociedad', 'constitucion de sociedad',
        'designación de gerentes', 'designacion de gerentes',
        'contrato social', 'expte.', 'expediente', 'autos caratulados',
        'inscripción matrícula', 'inscripcion matricula'
    ]
    
    if any(kw in texto_lower for kw in keywords_legales):
        return True
    
    return False


# Funciones wrapper para backward compatibility
async def search_linkedin_company(business_name: str, website: str = "") -> Optional[str]:
    """Wrapper para búsqueda de LinkedIn empresa."""
    empresa_busqueda = website.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/") if website else business_name
    return await google_buscar_linkedin_empresa(business_name, empresa_busqueda)


async def search_news(business_name: str, person_name: str = "", location: str = "") -> List[dict]:
    """Wrapper para búsqueda de noticias."""
    if APIFY_API_TOKEN:
        noticias = await apify_buscar_noticias(business_name, location)
        if noticias:
            return noticias
    return await google_buscar_noticias(business_name, business_name, location)
