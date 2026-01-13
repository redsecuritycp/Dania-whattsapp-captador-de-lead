"""
Servicio de investigación de desafíos empresariales para DANIA/Fortia
Busca desafíos REALES usando Tavily + GPT (2026-2027)
NO usa listas hardcodeadas - investiga de verdad

VERSIÓN 2.3 - Desafíos reales + genéricos combinados
"""
import os
import re
import logging
import httpx
from typing import List, Dict

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HTTP_TIMEOUT = 30.0

# ═══════════════════════════════════════════════════════════════════
# TABLA DE SALARIOS POR PAÍS (USD/mes)
# ═══════════════════════════════════════════════════════════════════
SALARIOS_POR_PAIS = {
    "argentina": 1500,
    "méxico": 1800,
    "mexico": 1800,
    "chile": 2000,
    "colombia": 1400,
    "perú": 1300,
    "peru": 1300,
    "brasil": 1600,
    "brazil": 1600,
    "uruguay": 2200,
    "ecuador": 1200,
    "bolivia": 1000,
    "paraguay": 1100,
    "venezuela": 800,
    "españa": 3500,
    "spain": 3500,
    "alemania": 5000,
    "germany": 5000,
    "francia": 4500,
    "france": 4500,
    "italia": 3800,
    "italy": 3800,
    "reino unido": 5500,
    "united kingdom": 5500,
    "uk": 5500,
    "portugal": 2500,
    "estados unidos": 7000,
    "united states": 7000,
    "usa": 7000,
    "canadá": 5500,
    "canada": 5500,
}

# ═══════════════════════════════════════════════════════════════════
# RUBROS DE ALTO VALOR (multiplicadores y detección)
# ═══════════════════════════════════════════════════════════════════
RUBROS_ALTO_VALOR = {
    "tech": 1.5,
    "software": 1.5,
    "desarrollo": 1.5,
    "tecnología": 1.5,
    "saas": 1.5,
    "it": 1.5,
    "sistemas": 1.5,
    "programación": 1.5,
    "salud": 1.4,
    "clínica": 1.4,
    "clinica": 1.4,
    "hospital": 1.4,
    "médico": 1.4,
    "medico": 1.4,
    "medicina": 1.4,
    "odontología": 1.4,
    "odontologia": 1.4,
    "dental": 1.4,
    "legal": 1.3,
    "abogado": 1.3,
    "abogados": 1.3,
    "estudio jurídico": 1.3,
    "estudio juridico": 1.3,
    "derecho": 1.3,
    "finanzas": 1.3,
    "financiero": 1.3,
    "seguros": 1.3,
    "banking": 1.3,
    "banco": 1.3,
    "inversiones": 1.3,
    "inmobiliaria": 1.2,
    "real estate": 1.2,
    "bienes raíces": 1.2,
    "bienes raices": 1.2,
    "construcción": 1.2,
    "construccion": 1.2,
}


async def investigar_desafios_empresa(rubro: str,
                                      pais: str,
                                      team_size: str = "",
                                      business_description: str = "") -> Dict:
    """
    Investiga desafíos REALES del sector usando Tavily + GPT.
    Busca artículos de 2026-2027 y extrae desafíos específicos con IA.

    VERSIÓN 2.3: Siempre incluye genéricos (solos o combinados).
    """
    logger.info(f"[CHALLENGES] ========== Investigando desafíos ==========")
    logger.info(
        f"[CHALLENGES] Rubro: {rubro}, País: {pais}, Team: {team_size}")

    results = {
        "desafios": [],
        "desafios_texto": "",
        "fuentes": [],
        "rubro_analizado": rubro,
        "pais_analizado": pais,
        "success": False
    }

    if not rubro:
        results["desafios_texto"] = (
            "¿Cuál es el principal desafío que enfrenta tu empresa hoy?")
        return results

    # Obtener genéricos siempre (se usarán solos o combinados)
    genericos = _get_desafios_genericos()

    # Paso 1: Buscar artículos reales con Tavily
    contenido_articulos, fuentes = await _buscar_articulos_tavily(rubro, pais)
    results["fuentes"] = fuentes

    if contenido_articulos:
        # Paso 2: Extraer desafíos con GPT (análisis real)
        desafios_reales = await _extraer_desafios_con_gpt(
            contenido_articulos, rubro, pais)

        if desafios_reales:
            # NUEVO: Combinar reales + genéricos
            results["desafios"] = desafios_reales[:5] + genericos[:3]
            results["success"] = True
            results["desafios_texto"] = _formatear_desafios_combinados(
                desafios_reales, genericos, rubro, pais)
            logger.info(f"[CHALLENGES] ✓ {len(desafios_reales)} reales + "
                        f"3 genéricos combinados")
            return results

    # Si no encontró específicos, usar solo genéricos universales
    logger.warning("[CHALLENGES] No se encontraron desafíos específicos")
    results["desafios"] = genericos
    results["desafios_texto"] = _formatear_desafios_genericos(genericos)

    return results


async def _buscar_articulos_tavily(rubro: str, pais: str) -> tuple:
    """
    Busca artículos reales sobre desafíos del sector en 2026-2027.
    Returns: (contenido_concatenado, lista_fuentes)
    """
    if not TAVILY_API_KEY:
        logger.warning("[CHALLENGES] TAVILY_API_KEY no configurada")
        return "", []

    rubro_limpio = rubro.lower().strip()

    # Queries específicos para 2026-2027 (fecha actual dic 2025)
    queries = [
        f"desafíos {rubro_limpio} {pais} 2026 2027 tendencias",
        f"retos empresas {rubro_limpio} {pais} 2026 problemas",
        f"challenges {rubro_limpio} {pais} 2026 2027 trends"
    ]

    all_content = []
    fuentes = []

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            for query in queries[:2]:  # Solo 2 queries
                try:
                    logger.info(f"[CHALLENGES] Tavily query: {query}")
                    response = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": TAVILY_API_KEY,
                            "query": query,
                            "search_depth": "advanced",
                            "include_raw_content": True,
                            "max_results": 5
                        })

                    if response.status_code == 200:
                        data = response.json()

                        # Usar answer de Tavily si existe
                        if data.get("answer"):
                            all_content.append(data["answer"])

                        for r in data.get("results", []):
                            content = (r.get("raw_content")
                                       or r.get("content", ""))
                            if content and len(content) > 100:
                                all_content.append(content[:2000])
                            url = r.get("url", "")
                            if url and url not in fuentes:
                                fuentes.append(url)

                except Exception as e:
                    logger.warning(f"[CHALLENGES] Error en query: {e}")
                    continue

    except Exception as e:
        logger.error(f"[CHALLENGES] Error Tavily: {e}")

    contenido = "\n\n---\n\n".join(all_content[:5])
    logger.info(f"[CHALLENGES] Tavily: {len(all_content)} fragmentos, "
                f"{len(fuentes)} fuentes")

    return contenido, fuentes[:5]


async def _extraer_desafios_con_gpt(contenido: str, rubro: str,
                                    pais: str) -> List[str]:
    """
    Usa GPT para extraer desafíos ESPECÍFICOS del contenido real.
    NO inventa - solo extrae lo que está en el contenido.
    """
    if not OPENAI_API_KEY or not contenido:
        return []

    prompt = f"""Analiza el siguiente contenido sobre el sector 
"{rubro}" en {pais}.

CONTENIDO DE ARTÍCULOS REALES:
{contenido[:8000]}

---

Tu tarea: Extraer exactamente 5 desafíos ESPECÍFICOS y REALES 
que enfrentan las empresas de este sector SEGÚN EL CONTENIDO.

REGLAS ESTRICTAS:
- SOLO desafíos que APAREZCAN en el contenido
- NO inventar ni agregar desafíos genéricos
- Específicos del sector "{rubro}" (no genéricos)
- Relevantes para 2026-2027
- En español
- Máximo 15 palabras cada uno
- Sin numeración ni bullets en tu respuesta

Si el contenido no tiene desafíos específicos del sector, 
responde exactamente: NONE

Responde SOLO con los 5 desafíos, uno por línea:"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model":
                    "gpt-4o-mini",
                    "messages": [{
                        "role":
                        "system",
                        "content":
                        ("Eres un analista de negocios experto. "
                         "Extraes información PRECISA del contenido. "
                         "NUNCA inventas datos.")
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature":
                    0.2,
                    "max_tokens":
                    500
                })

            if response.status_code == 200:
                data = response.json()
                texto = data["choices"][0]["message"]["content"].strip()

                # Si GPT dice que no hay info específica
                if texto.upper() == "NONE" or "no encuentro" in texto.lower():
                    logger.info(
                        "[CHALLENGES] GPT: No hay desafíos específicos")
                    return []

                # Parsear respuesta (una línea por desafío)
                desafios = []
                for linea in texto.split("\n"):
                    linea = linea.strip()
                    # Quitar numeración si existe
                    linea = linea.lstrip("0123456789.-•) ")
                    if linea and len(linea) > 10 and len(linea) < 200:
                        desafios.append(linea)

                logger.info(f"[CHALLENGES] GPT extrajo: {desafios}")
                return desafios[:5]

    except Exception as e:
        logger.error(f"[CHALLENGES] Error GPT: {e}")

    return []


def _formatear_desafios_combinados(desafios_reales: List[str],
                                   desafios_genericos: List[str], rubro: str,
                                   pais: str) -> str:
    """
    Formatea desafíos reales + genéricos combinados.
    Máximo 5 reales + 3 genéricos = 8 total.
    """
    # Limitar cantidades
    reales = desafios_reales[:5]
    genericos = desafios_genericos[:3]

    texto = f"🔍 *Desafíos actuales en {rubro} ({pais}):*\n\n"

    for i, desafio in enumerate(reales, 1):
        texto += f"{i}. {desafio}\n"

    # Agregar genéricos como sección adicional
    texto += "\n📌 *Desafíos comunes adicionales:*\n\n"

    start_num = len(reales) + 1
    for i, desafio in enumerate(genericos, start_num):
        texto += f"{i}. {desafio}\n"

    texto += "\n¿Cuál de estos es más relevante para tu negocio?"

    return texto


def _formatear_desafios_genericos(desafios: List[str]) -> str:
    """Formatea desafíos genéricos cuando NO hay específicos."""
    texto = "🔍 *Desafíos comunes en tu industria:*\n\n"

    for i, desafio in enumerate(desafios, 1):
        texto += f"{i}. {desafio}\n"

    texto += ("\n¿Te identificás con alguno? "
              "¿O hay otro más importante para vos?")

    return texto


def _get_desafios_genericos() -> List[str]:
    """
    Desafíos universales que aplican a cualquier empresa.
    Se muestran SIEMPRE (solos o junto a los específicos).
    """
    return [
        "Captar nuevos clientes de forma constante",
        "Reducir tareas manuales y repetitivas",
        "Mejorar seguimiento de leads y oportunidades",
        "Optimizar tiempos de respuesta al cliente",
        "Escalar operaciones sin aumentar costos"
    ]


# ═══════════════════════════════════════════════════════════════════
# CALCULAR QUALIFICATION TIER - VERSIÓN COMPLETA
# ═══════════════════════════════════════════════════════════════════
def calcular_qualification_tier(team_size: str,
                                country: str,
                                business_activity: str = "",
                                business_description: str = "",
                                linkedin_empresa: str = "",
                                instagram_empresa: str = "",
                                facebook_empresa: str = "",
                                instagram_followers: int = 0,
                                linkedin_followers: int = 0,
                                main_challenge: str = "",
                                ai_knowledge: str = "") -> Dict:
    """
    Calcula el tier de cualificación usando la lógica completa:

    1. Si team_size < 10 → STANDARD
    2. Si team_size >= 10:
       - CAMINO 1: facturación >= $1M/año → PREMIUM
       - CAMINO 2: 2+ indicadores de inversión → PREMIUM
       - Sino → STANDARD

    Casos especiales:
    - Menciona formación/educación → EDUCATION
    - Menciona crear agencia → AGENCY

    Returns:
        {
            "tier": "premium" | "standard" | "education" | "agency",
            "reason": str,
            "facturacion_estimada": float,
            "indicadores_cumplidos": int,
            "detalle_indicadores": dict,
            "recommended_url": str
        }
    """
    logger.info("[TIER] ══════ Calculando qualification_tier ══════")

    result = {
        "tier": "standard",
        "reason": "",
        "facturacion_estimada": 0,
        "indicadores_cumplidos": 0,
        "detalle_indicadores": {},
        "recommended_url": "https://hello.dania.ai/soluciones"
    }

    # ═══════════════════════════════════════════════════════════════
    # CASOS ESPECIALES: EDUCATION y AGENCY
    # ═══════════════════════════════════════════════════════════════
    challenge_lower = (main_challenge or "").lower()
    knowledge_lower = (ai_knowledge or "").lower()
    activity_lower = (business_activity or "").lower()

    # Detectar si quiere EDUCACIÓN
    education_keywords = [
        "formación", "formacion", "capacitación", "capacitacion", "aprender",
        "curso", "estudiar", "educar", "enseñar", "training", "learning"
    ]
    if any(kw in challenge_lower for kw in education_keywords) or \
       any(kw in knowledge_lower for kw in education_keywords):
        logger.info("[TIER] → EDUCATION (menciona formación)")
        return {
            "tier": "education",
            "reason": "Interés en formación/capacitación",
            "facturacion_estimada": 0,
            "indicadores_cumplidos": 0,
            "detalle_indicadores": {},
            "recommended_url":
            "https://dania.university/programas/integrador-ia"
        }

    # Detectar si quiere AGENCIA
    agency_keywords = [
        "crear agencia", "lanzar agencia", "mi propia agencia",
        "montar agencia", "abrir agencia", "emprender agencia",
        "negocio de ia", "negocio de automatización"
    ]
    combined_text = f"{challenge_lower} {knowledge_lower} {activity_lower}"
    if any(kw in combined_text for kw in agency_keywords):
        logger.info("[TIER] → AGENCY (quiere crear agencia)")
        return {
            "tier": "agency",
            "reason": "Interés en crear agencia de IA",
            "facturacion_estimada": 0,
            "indicadores_cumplidos": 0,
            "detalle_indicadores": {},
            "recommended_url": "https://lanzatuagencia.dania.ai/"
        }

    # ═══════════════════════════════════════════════════════════════
    # EXTRAER NÚMERO DE TEAM_SIZE
    # ═══════════════════════════════════════════════════════════════
    team_num = 0
    try:
        nums = re.findall(r'\d+', str(team_size))
        if nums:
            team_num = int(nums[0])
    except Exception:
        team_num = 0

    logger.info(f"[TIER] team_size extraído: {team_num}")

    # Si team_size < 10 → STANDARD directamente
    if team_num < 10:
        result["reason"] = f"Equipo pequeño ({team_num} personas)"
        logger.info(f"[TIER] → STANDARD (team < 10)")
        return result

    # ═══════════════════════════════════════════════════════════════
    # CAMINO 1: CÁLCULO DE FACTURACIÓN ESTIMADA
    # ═══════════════════════════════════════════════════════════════
    country_lower = (country or "").lower().strip()
    salario = SALARIOS_POR_PAIS.get(country_lower, 2000)  # Default 2000

    # Facturación base
    facturacion_base = team_num * salario * 3

    # Multiplicador por rubro
    multiplicador = 1.0
    for rubro_key, mult in RUBROS_ALTO_VALOR.items():
        if rubro_key in activity_lower:
            multiplicador = mult
            break

    facturacion_estimada = facturacion_base * multiplicador
    result["facturacion_estimada"] = facturacion_estimada

    logger.info(
        f"[TIER] Facturación: {team_num} × ${salario} × 3 × {multiplicador} "
        f"= ${facturacion_estimada:,.0f}/año")

    # ═══════════════════════════════════════════════════════════════
    # CAMINO 2: INDICADORES DE INVERSIÓN (4 indicadores)
    # ═══════════════════════════════════════════════════════════════
    indicadores = {
        "rubro_alto_valor": False,
        "multiples_sucursales": False,
        "tiene_ecommerce": False,
        "alta_presencia_redes": False
    }

    # 1. Rubro alto valor
    for rubro_key in RUBROS_ALTO_VALOR.keys():
        if rubro_key in activity_lower:
            indicadores["rubro_alto_valor"] = True
            break

    # 2. Múltiples sucursales
    description_lower = (business_description or "").lower()
    sucursales_keywords = [
        "sucursales", "sedes", "oficinas en", "ubicaciones", "locales en",
        "puntos de venta", "branches"
    ]
    if any(kw in description_lower for kw in sucursales_keywords):
        indicadores["multiples_sucursales"] = True

    # 3. Tiene ecommerce
    ecommerce_keywords = [
        "ecommerce", "e-commerce", "tienda online", "tienda virtual",
        "compra online", "carrito", "mercado pago", "stripe", "paypal",
        "shopify", "woocommerce", "magento"
    ]
    if any(kw in description_lower for kw in ecommerce_keywords):
        indicadores["tiene_ecommerce"] = True

    # 4. Alta presencia en redes
    redes_activas = 0
    if linkedin_empresa and linkedin_empresa != "No encontrado":
        redes_activas += 1
    if instagram_empresa and instagram_empresa != "No encontrado":
        redes_activas += 1
    if facebook_empresa and facebook_empresa != "No encontrado":
        redes_activas += 1

    # Check followers
    if instagram_followers > 10000:
        indicadores["alta_presencia_redes"] = True
    elif linkedin_followers > 5000:
        indicadores["alta_presencia_redes"] = True
    elif redes_activas >= 3:
        indicadores["alta_presencia_redes"] = True

    # Contar indicadores cumplidos
    indicadores_cumplidos = sum(indicadores.values())
    result["indicadores_cumplidos"] = indicadores_cumplidos
    result["detalle_indicadores"] = indicadores

    logger.info(f"[TIER] Indicadores: {indicadores}")
    logger.info(f"[TIER] Total indicadores: {indicadores_cumplidos}/4")

    # ═══════════════════════════════════════════════════════════════
    # DECISIÓN FINAL
    # ═══════════════════════════════════════════════════════════════
    es_premium = False
    razones = []

    # Camino 1: Facturación >= $1M
    if facturacion_estimada >= 1000000:
        es_premium = True
        razones.append(
            f"facturación estimada ${facturacion_estimada:,.0f}/año")

    # Camino 2: 2+ indicadores
    if indicadores_cumplidos >= 2:
        es_premium = True
        indicadores_activos = [k for k, v in indicadores.items() if v]
        razones.append(
            f"{indicadores_cumplidos} indicadores ({', '.join(indicadores_activos)})"
        )

    if es_premium:
        result["tier"] = "premium"
        result["reason"] = " + ".join(razones)
        result["recommended_url"] = "Cal.com"
        logger.info(f"[TIER] → PREMIUM: {result['reason']}")
    else:
        result["tier"] = "standard"
        result["reason"] = (
            f"Equipo de {team_num}, facturación ~${facturacion_estimada:,.0f}, "
            f"{indicadores_cumplidos} indicadores")
        logger.info(f"[TIER] → STANDARD: {result['reason']}")

    logger.info("[TIER] ══════ Cálculo completado ══════")
    return result
