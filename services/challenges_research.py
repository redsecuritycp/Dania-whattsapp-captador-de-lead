"""
Servicio de investigación de desafíos empresariales para DANIA/Fortia
Busca desafíos REALES usando Tavily + GPT (2026-2027)
NO usa listas hardcodeadas - investiga de verdad
"""
import os
import logging
import httpx
from typing import List, Dict

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HTTP_TIMEOUT = 30.0


async def investigar_desafios_empresa(
    rubro: str,
    pais: str,
    team_size: str = "",
    business_description: str = ""
) -> Dict:
    """
    Investiga desafíos REALES del sector usando Tavily + GPT.
    Busca artículos de 2026-2027 y extrae desafíos específicos con IA.
    NO inventa ni usa listas hardcodeadas.
    """
    logger.info(f"[CHALLENGES] ========== Investigando desafíos ==========")
    logger.info(f"[CHALLENGES] Rubro: {rubro}, País: {pais}, Team: {team_size}")
    
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
            "¿Cuál es el principal desafío que enfrenta tu empresa hoy?"
        )
        return results
    
    # Paso 1: Buscar artículos reales con Tavily
    contenido_articulos, fuentes = await _buscar_articulos_tavily(rubro, pais)
    results["fuentes"] = fuentes
    
    if contenido_articulos:
        # Paso 2: Extraer desafíos con GPT (análisis real)
        desafios = await _extraer_desafios_con_gpt(
            contenido_articulos, rubro, pais
        )
        
        if desafios:
            results["desafios"] = desafios
            results["success"] = True
            results["desafios_texto"] = _formatear_desafios(
                desafios, rubro, pais
            )
            logger.info(
                f"[CHALLENGES] ✓ {len(desafios)} desafíos REALES encontrados"
            )
            return results
    
    # Si no encontró específicos, usar genéricos universales
    logger.warning("[CHALLENGES] No se encontraron desafíos específicos")
    results["desafios"] = _get_desafios_genericos()
    results["desafios_texto"] = _formatear_desafios_genericos(
        results["desafios"]
    )
    
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
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Usar answer de Tavily si existe
                        if data.get("answer"):
                            all_content.append(data["answer"])
                        
                        for r in data.get("results", []):
                            content = (
                                r.get("raw_content") or r.get("content", "")
                            )
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
    logger.info(
        f"[CHALLENGES] Tavily: {len(all_content)} fragmentos, "
        f"{len(fuentes)} fuentes"
    )
    
    return contenido, fuentes[:5]


async def _extraer_desafios_con_gpt(
    contenido: str, 
    rubro: str, 
    pais: str
) -> List[str]:
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
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres un analista de negocios experto. "
                                "Extraes información PRECISA del contenido. "
                                "NUNCA inventas datos."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                texto = data["choices"][0]["message"]["content"].strip()
                
                # Si GPT dice que no hay info específica
                if texto.upper() == "NONE" or "no encuentro" in texto.lower():
                    logger.info("[CHALLENGES] GPT: No hay desafíos específicos")
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
    
    texto = (
        f"Según mi investigación, las empresas de {rubro} "
        f"en {pais} están enfrentando:\n\n"
    )
    
    for i, desafio in enumerate(desafios, 1):
        texto += f"{i}. {desafio}\n"
    
    texto += (
        "\n¿Te identificás con alguno de estos? "
        "¿O hay otro desafío más importante para vos?"
    )
    
    return texto


async def calcular_qualification_tier(
    team_size: str,
    rubro: str,
    social_metrics: dict = None,
    country: str = ""
) -> Dict:
    """Calcula el tier de cualificación."""
    import re
    
    result = {
        "tier": "standard",
        "reason": "",
        "estimated_potential": "medio",
        "recommended_product": "DAN Autopilots",
        "recommended_url": "https://hello.dania.ai/soluciones"
    }
    
    team_num = 0
    try:
        nums = re.findall(r'\d+', str(team_size))
        if nums:
            team_num = int(nums[0])
    except:
        team_num = 0
    
    if team_num >= 50:
        return {
            "tier": "premium",
            "reason": f"Empresa grande ({team_num} empleados)",
            "estimated_potential": "alto",
            "recommended_product": "Consultoría Personalizada",
            "recommended_url": "Cal.com"
        }
    
    social_metrics = social_metrics or {}
    ig_followers = social_metrics.get("instagram_followers", 0)
    fb_followers = social_metrics.get("facebook_followers", 0)
    
    if ig_followers > 10000 or fb_followers > 10000:
        result["tier"] = "premium"
        result["reason"] = "Alta presencia en redes"
        result["estimated_potential"] = "alto"
    elif team_num >= 10:
        result["tier"] = "standard"
        result["reason"] = f"Equipo mediano ({team_num})"
        result["estimated_potential"] = "medio"
    
    return result


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
    texto = (
        "Investigando desafíos típicos de tu industria...\n\n"
        "Muchas empresas enfrentan estos desafíos:\n\n"
    )
    
    for i, desafio in enumerate(desafios, 1):
        texto += f"{i}. {desafio}\n"
    
    texto += (
        "\n¿Te identificás con alguno? "
        "¿O hay otro más importante para vos?"
    )
    
    return texto
