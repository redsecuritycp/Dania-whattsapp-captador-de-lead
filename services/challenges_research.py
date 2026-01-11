"""
Servicio de investigación de desafíos empresariales para DANIA/Fortia
Busca desafíos REALES usando Tavily + GPT (2026-2027)
NO usa listas hardcodeadas - investiga de verdad

Incluye: Sistema de Cualificación con cálculo de facturación estimada
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
# TABLA DE SALARIOS PROMEDIO POR PAÍS (USD/mes)
# Fuente: Datos de mercado 2024-2025, ajustados para 2026
# ═══════════════════════════════════════════════════════════════════

SALARIOS_POR_PAIS = {
    # LATINOAMÉRICA
    "Argentina": 1500,
    "México": 1800,
    "Chile": 2000,
    "Colombia": 1400,
    "Perú": 1300,
    "Brasil": 1600,
    "Uruguay": 2200,
    "Ecuador": 1200,
    "Bolivia": 1000,
    "Paraguay": 1100,
    "Venezuela": 800,
    "Costa Rica": 1700,
    "Panamá": 1900,
    "Guatemala": 1000,
    "El Salvador": 900,
    "Honduras": 800,
    "Nicaragua": 700,
    "Cuba": 600,
    "República Dominicana": 1100,
    "Puerto Rico": 3500,

    # EUROPA OCCIDENTAL
    "España": 3500,
    "Alemania": 5000,
    "Francia": 4500,
    "Italia": 3800,
    "Reino Unido": 5500,
    "Portugal": 2500,
    "Países Bajos": 5200,
    "Bélgica": 4800,
    "Austria": 5000,
    "Suiza": 7500,
    "Irlanda": 5500,
    "Luxemburgo": 6500,

    # EUROPA NÓRDICA
    "Suecia": 5500,
    "Noruega": 6500,
    "Dinamarca": 6000,
    "Finlandia": 5000,

    # EUROPA DEL ESTE
    "Polonia": 2500,
    "República Checa": 2800,
    "Hungría": 2200,
    "Rumania": 2000,
    "Bulgaria": 1800,
    "Croacia": 2200,
    "Eslovaquia": 2400,
    "Eslovenia": 3000,
    "Estonia": 2800,
    "Letonia": 2400,
    "Lituania": 2500,

    # EUROPA MEDITERRÁNEA
    "Grecia": 2500,
    "Chipre": 3000,
    "Malta": 3200,

    # NORTEAMÉRICA
    "Estados Unidos": 7000,

    # DEFAULT
    "Desconocido": 2000,
}

# ═══════════════════════════════════════════════════════════════════
# MULTIPLICADORES POR RUBRO/INDUSTRIA
# ═══════════════════════════════════════════════════════════════════

MULTIPLICADORES_RUBRO = {
    # ALTO VALOR (1.5x)
    "tech": 1.5,
    "software": 1.5,
    "desarrollo": 1.5,
    "tecnología": 1.5,
    "it": 1.5,
    "saas": 1.5,
    "startup": 1.5,
    "fintech": 1.5,

    # SALUD (1.4x)
    "salud": 1.4,
    "clínica": 1.4,
    "hospital": 1.4,
    "médico": 1.4,
    "dental": 1.4,
    "farmacia": 1.4,
    "laboratorio": 1.4,
    "healthcare": 1.4,

    # LEGAL/FINANZAS (1.3x)
    "legal": 1.3,
    "abogados": 1.3,
    "estudio jurídico": 1.3,
    "finanzas": 1.3,
    "seguros": 1.3,
    "banking": 1.3,
    "banco": 1.3,
    "contable": 1.3,
    "contabilidad": 1.3,
    "inversiones": 1.3,

    # INMOBILIARIA (1.2x)
    "inmobiliaria": 1.2,
    "real estate": 1.2,
    "bienes raíces": 1.2,
    "construcción": 1.2,
    "arquitectura": 1.2,

    # COMERCIO/RETAIL (1.1x)
    "ecommerce": 1.1,
    "comercio electrónico": 1.1,
    "retail": 1.1,
    "tienda": 1.1,

    # DEFAULT (1.0x)
    "default": 1.0
}

# ═══════════════════════════════════════════════════════════════════
# FUNCIONES DE CUALIFICACIÓN
# ═══════════════════════════════════════════════════════════════════


def _obtener_salario_pais(pais: str) -> int:
    """Obtiene el salario promedio del país."""
    if not pais:
        return SALARIOS_POR_PAIS.get("Desconocido", 2000)

    # Buscar coincidencia exacta
    if pais in SALARIOS_POR_PAIS:
        return SALARIOS_POR_PAIS[pais]

    # Buscar coincidencia parcial (case insensitive)
    pais_lower = pais.lower().strip()
    for key, value in SALARIOS_POR_PAIS.items():
        if key.lower() == pais_lower:
            return value

    return SALARIOS_POR_PAIS.get("Desconocido", 2000)


def _obtener_multiplicador_rubro(rubro: str) -> float:
    """Obtiene el multiplicador según el rubro de la empresa."""
    if not rubro:
        return 1.0

    rubro_lower = rubro.lower().strip()

    # Buscar coincidencia en keywords
    for keyword, mult in MULTIPLICADORES_RUBRO.items():
        if keyword in rubro_lower:
            return mult

    return 1.0


def _evaluar_indicadores_inversion(rubro: str, business_description: str,
                                   social_metrics: dict) -> Dict:
    """
    Evalúa los 4 indicadores de inversión.
    Retorna dict con cada indicador y total.
    """
    indicadores = {
        "rubro_alto_valor": False,
        "multiples_sucursales": False,
        "tiene_ecommerce": False,
        "alta_presencia_redes": False,
        "total": 0
    }

    rubro_lower = (rubro or "").lower()
    desc_lower = (business_description or "").lower()

    # 1. RUBRO ALTO VALOR
    rubros_alto_valor = [
        "tech", "software", "desarrollo", "tecnología", "salud", "clínica",
        "hospital", "médico", "legal", "abogados", "finanzas", "seguros",
        "banking"
    ]
    for r in rubros_alto_valor:
        if r in rubro_lower:
            indicadores["rubro_alto_valor"] = True
            break

    # 2. MÚLTIPLES SUCURSALES
    keywords_sucursales = [
        "sucursales", "sedes", "oficinas en", "locales", "ubicaciones",
        "presencia en", "branches"
    ]
    for kw in keywords_sucursales:
        if kw in desc_lower:
            indicadores["multiples_sucursales"] = True
            break

    # 3. TIENE E-COMMERCE
    keywords_ecommerce = [
        "ecommerce", "e-commerce", "tienda online", "comercio electrónico",
        "compra online", "mercado pago", "stripe", "paypal", "carrito"
    ]
    for kw in keywords_ecommerce:
        if kw in desc_lower:
            indicadores["tiene_ecommerce"] = True
            break

    # 4. ALTA PRESENCIA EN REDES
    social_metrics = social_metrics or {}
    ig = social_metrics.get("instagram_followers", 0)
    fb = social_metrics.get("facebook_followers", 0)
    li = social_metrics.get("linkedin_followers", 0)
    tw = social_metrics.get("twitter_followers", 0)
    yt = social_metrics.get("youtube_subscribers", 0)

    # >10K en Instagram O >5K en LinkedIn
    if ig > 10000 or li > 5000:
        indicadores["alta_presencia_redes"] = True
    else:
        # O tiene 3+ redes activas (>1000 cada una)
        redes_activas = sum([
            1 if ig > 1000 else 0, 1 if fb > 1000 else 0,
            1 if li > 1000 else 0, 1 if tw > 1000 else 0, 1 if yt > 1000 else 0
        ])
        if redes_activas >= 3:
            indicadores["alta_presencia_redes"] = True

    # Contar total
    indicadores["total"] = sum([
        indicadores["rubro_alto_valor"], indicadores["multiples_sucursales"],
        indicadores["tiene_ecommerce"], indicadores["alta_presencia_redes"]
    ])

    return indicadores


async def calcular_qualification_tier(team_size: str,
                                      rubro: str,
                                      social_metrics: dict = None,
                                      country: str = "",
                                      business_description: str = "") -> Dict:
    """
    Calcula el tier de cualificación usando DOS caminos:

    CAMINO 1: Facturación estimada
    - facturacion = team_size × salario_pais × 3 × multiplicador_rubro
    - Si facturacion >= $1,000,000/año → PREMIUM

    CAMINO 2: Indicadores de inversión (4 indicadores)
    - rubro_alto_valor
    - multiples_sucursales  
    - tiene_ecommerce
    - alta_presencia_redes
    - Si cumple >= 2 indicadores → PREMIUM

    DECISIÓN:
    - team_size < 10 → STANDARD (sin evaluar más)
    - team_size >= 10 → Evaluar ambos caminos
      - Si CAMINO 1 es SÍ O CAMINO 2 es SÍ → PREMIUM
      - Si ambos son NO → STANDARD
    """
    logger.info(f"[QUALIFICATION] ══════ Calculando tier ══════")
    logger.info(f"[QUALIFICATION] Team: {team_size}, Rubro: {rubro}, "
                f"País: {country}")

    result = {
        "tier": "standard",
        "reason": "",
        "estimated_revenue": 0,
        "revenue_threshold_met": False,
        "indicators": {},
        "indicators_met": False,
        "estimated_potential": "medio",
        "recommended_product": "DAN Autopilots",
        "recommended_url": "https://hello.dania.ai/soluciones",
        "calculation_details": {}
    }

    # Parsear team_size a número
    team_num = 0
    try:
        nums = re.findall(r'\d+', str(team_size))
        if nums:
            team_num = int(nums[0])
    except:
        team_num = 0

    logger.info(f"[QUALIFICATION] Team size parseado: {team_num}")

    # ═══════════════════════════════════════════════════════════════
    # REGLA: team_size < 10 → STANDARD (sin más análisis)
    # ═══════════════════════════════════════════════════════════════
    if team_num < 10:
        result["reason"] = f"Equipo pequeño ({team_num} personas)"
        result["estimated_potential"] = "medio"
        logger.info(f"[QUALIFICATION] → STANDARD (team < 10)")
        return result

    # ═══════════════════════════════════════════════════════════════
    # CAMINO 1: CÁLCULO DE FACTURACIÓN ESTIMADA
    # ═══════════════════════════════════════════════════════════════
    salario = _obtener_salario_pais(country)
    multiplicador = _obtener_multiplicador_rubro(rubro)

    facturacion_mensual = team_num * salario * 3
    facturacion_anual = facturacion_mensual * 12
    facturacion_ajustada = facturacion_anual * multiplicador

    result["calculation_details"] = {
        "team_size": team_num,
        "salario_pais": salario,
        "pais": country,
        "multiplicador_rubro": multiplicador,
        "rubro": rubro,
        "facturacion_mensual_base": facturacion_mensual,
        "facturacion_anual_base": facturacion_anual,
        "facturacion_anual_ajustada": facturacion_ajustada
    }

    result["estimated_revenue"] = facturacion_ajustada

    # ¿Cumple umbral de $1M/año?
    UMBRAL_PREMIUM = 1_000_000
    if facturacion_ajustada >= UMBRAL_PREMIUM:
        result["revenue_threshold_met"] = True

    logger.info(f"[QUALIFICATION] Facturación estimada: "
                f"${facturacion_ajustada:,.0f}/año "
                f"(umbral: ${UMBRAL_PREMIUM:,})")

    # ═══════════════════════════════════════════════════════════════
    # CAMINO 2: INDICADORES DE INVERSIÓN
    # ═══════════════════════════════════════════════════════════════
    indicadores = _evaluar_indicadores_inversion(
        rubro=rubro,
        business_description=business_description,
        social_metrics=social_metrics or {})

    result["indicators"] = indicadores

    # ¿Cumple >= 2 indicadores?
    if indicadores["total"] >= 2:
        result["indicators_met"] = True

    logger.info(f"[QUALIFICATION] Indicadores: {indicadores['total']}/4 "
                f"(mínimo: 2)")
    logger.info(f"[QUALIFICATION] - Rubro alto valor: "
                f"{indicadores['rubro_alto_valor']}")
    logger.info(f"[QUALIFICATION] - Múltiples sucursales: "
                f"{indicadores['multiples_sucursales']}")
    logger.info(f"[QUALIFICATION] - E-commerce: "
                f"{indicadores['tiene_ecommerce']}")
    logger.info(f"[QUALIFICATION] - Alta presencia redes: "
                f"{indicadores['alta_presencia_redes']}")

    # ═══════════════════════════════════════════════════════════════
    # DECISIÓN FINAL
    # ═══════════════════════════════════════════════════════════════
    if result["revenue_threshold_met"] or result["indicators_met"]:
        result["tier"] = "premium"
        result["estimated_potential"] = "alto"
        result["recommended_product"] = "Consultoría Personalizada"
        result["recommended_url"] = "Cal.com"

        # Determinar razón
        if result["revenue_threshold_met"] and result["indicators_met"]:
            result["reason"] = (
                f"Facturación estimada ${facturacion_ajustada:,.0f}/año "
                f"+ {indicadores['total']} indicadores de inversión")
        elif result["revenue_threshold_met"]:
            result["reason"] = (
                f"Facturación estimada ${facturacion_ajustada:,.0f}/año "
                f"(≥$1M)")
        else:
            result["reason"] = (
                f"{indicadores['total']} indicadores de inversión "
                f"(≥2 requeridos)")

        logger.info(f"[QUALIFICATION] → PREMIUM: {result['reason']}")
    else:
        result["reason"] = (
            f"Facturación ${facturacion_ajustada:,.0f}/año (<$1M) "
            f"+ {indicadores['total']} indicadores (<2)")
        logger.info(f"[QUALIFICATION] → STANDARD: {result['reason']}")

    return result


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES DE INVESTIGACIÓN DE DESAFÍOS (sin cambios)
# ═══════════════════════════════════════════════════════════════════


async def investigar_desafios_empresa(rubro: str,
                                      pais: str,
                                      team_size: str = "",
                                      business_description: str = "") -> Dict:
    """
    Investiga desafíos REALES del sector usando Tavily + GPT.
    Busca artículos de 2026-2027 y extrae desafíos específicos con IA.
    NO inventa ni usa listas hardcodeadas.
    """
    logger.info(f"[CHALLENGES] ══════ Investigando desafíos ══════")
    logger.info(f"[CHALLENGES] Rubro: {rubro}, País: {pais}, "
                f"Team: {team_size}")

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

    # Paso 1: Buscar artículos reales con Tavily
    contenido_articulos, fuentes = await _buscar_articulos_tavily(rubro, pais)
    results["fuentes"] = fuentes

    if contenido_articulos:
        # Paso 2: Extraer desafíos con GPT (análisis real)
        desafios = await _extraer_desafios_con_gpt(contenido_articulos, rubro,
                                                   pais)

        if desafios:
            results["desafios"] = desafios
            results["success"] = True
            results["desafios_texto"] = _formatear_desafios(
                desafios, rubro, pais)
            logger.info(f"[CHALLENGES] ✓ {len(desafios)} desafíos REALES "
                        f"encontrados")
            return results

    # Si no encontró específicos, usar genéricos universales
    logger.warning("[CHALLENGES] No se encontraron desafíos específicos")
    results["desafios"] = _get_desafios_genericos()
    results["desafios_texto"] = _formatear_desafios_genericos(
        results["desafios"])

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

    # Queries específicos para 2026-2027
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
                        "content": ("Eres un analista de negocios experto. "
                                    "Extraes información PRECISA del "
                                    "contenido. NUNCA inventas datos.")
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
                texto = (data["choices"][0]["message"]["content"].strip())

                # Si GPT dice que no hay info específica
                if (texto.upper() == "NONE"
                        or "no encuentro" in texto.lower()):
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


def _formatear_desafios(desafios: List[str], rubro: str, pais: str) -> str:
    """Formatea los desafíos para mostrar al usuario."""
    if not desafios:
        return ""

    texto = (f"Según mi investigación, las empresas de {rubro} "
             f"en {pais} están enfrentando:\n\n")

    for i, desafio in enumerate(desafios, 1):
        texto += f"{i}. {desafio}\n"

    texto += ("\n¿Te identificás con alguno de estos? "
              "¿O hay otro desafío más importante para vos?")

    return texto


def _get_desafios_genericos() -> List[str]:
    """
    Desafíos universales que aplican a cualquier empresa.
    Se usan SOLO cuando no se encuentran desafíos específicos.
    """
    return [
        "Captación de nuevos clientes de forma constante",
        "Procesos manuales que consumen tiempo del equipo",
        "Seguimiento inconsistente de leads y oportunidades",
        "Presencia digital que no genera resultados",
        "Falta de automatización en tareas repetitivas"
    ]


def _formatear_desafios_genericos(desafios: List[str]) -> str:
    """Formatea desafíos genéricos (sin mencionar rubro ni país)."""
    texto = ("Investigando desafíos típicos de tu industria...\n\n"
             "Muchas empresas enfrentan estos desafíos:\n\n")

    for i, desafio in enumerate(desafios, 1):
        texto += f"{i}. {desafio}\n"

    texto += ("\n¿Te identificás con alguno? "
              "¿O hay otro más importante para vos?")

    return texto
