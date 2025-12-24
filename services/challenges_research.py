"""
Servicio de investigación de desafíos empresariales para DANIA/Fortia
Busca desafíos específicos por rubro + país + año usando Tavily
"""
import logging
import httpx
from typing import Optional, List, Dict
from config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30.0


async def investigar_desafios_empresa(
    rubro: str,
    pais: str,
    team_size: str = "",
    business_description: str = ""
) -> Dict:
    """
    Investiga desafíos específicos para el tipo de empresa.
    Busca tendencias 2026-2027 para el rubro y país.
    
    Returns:
        {
            "desafios": ["desafío 1", "desafío 2", ...],
            "desafios_texto": "texto formateado para mostrar",
            "fuentes": ["url1", "url2"],
            "rubro_analizado": "rubro",
            "pais_analizado": "país"
        }
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
    
    if not TAVILY_API_KEY:
        logger.warning("[CHALLENGES] TAVILY_API_KEY no configurada")
        results["desafios"] = _get_desafios_genericos(rubro)
        results["desafios_texto"] = _formatear_desafios(results["desafios"], rubro, pais)
        return results
    
    try:
        # Normalizar rubro para búsqueda
        rubro_normalizado = _normalizar_rubro(rubro)
        
        # Query específico para tendencias futuras
        queries = [
            f"desafíos {rubro_normalizado} {pais} 2026 2027 tendencias",
            f"retos empresas {rubro_normalizado} {pais} futuro automatización",
            f"challenges {rubro_normalizado} industry {pais} 2026 trends"
        ]
        
        all_content = []
        fuentes = []
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            for query in queries[:2]:  # Solo 2 queries para no demorar
                try:
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
                        tavily_results = data.get("results", [])
                        
                        for r in tavily_results:
                            content = r.get("content", "") or r.get("raw_content", "")
                            if content:
                                all_content.append(content[:1500])
                            url = r.get("url", "")
                            if url and url not in fuentes:
                                fuentes.append(url)
                        
                        # Si hay answer directo de Tavily, usarlo
                        answer = data.get("answer", "")
                        if answer:
                            all_content.insert(0, answer)
                            
                except Exception as e:
                    logger.warning(f"[CHALLENGES] Error en query '{query}': {e}")
                    continue
        
        results["fuentes"] = fuentes[:5]
        
        # Extraer desafíos del contenido
        if all_content:
            desafios = _extraer_desafios_de_contenido(
                "\n\n".join(all_content), 
                rubro_normalizado,
                pais
            )
            if desafios:
                results["desafios"] = desafios
                results["success"] = True
        
        # Si no encontró nada específico, usar genéricos del rubro
        if not results["desafios"]:
            results["desafios"] = _get_desafios_genericos(rubro_normalizado)
        
        results["desafios_texto"] = _formatear_desafios(
            results["desafios"], 
            rubro, 
            pais
        )
        
        logger.info(f"[CHALLENGES] ✓ {len(results['desafios'])} desafíos encontrados")
        
    except Exception as e:
        logger.error(f"[CHALLENGES] Error general: {e}")
        results["desafios"] = _get_desafios_genericos(rubro)
        results["desafios_texto"] = _formatear_desafios(results["desafios"], rubro, pais)
    
    return results


def _normalizar_rubro(rubro: str) -> str:
    """Normaliza el nombre del rubro para búsquedas más efectivas."""
    rubro_lower = rubro.lower().strip()
    
    # Mapeo de rubros comunes
    mapeo = {
        "tecnología": "tecnología software",
        "tech": "tecnología software",
        "software": "desarrollo software",
        "salud": "sector salud clínicas",
        "medicina": "sector salud médico",
        "dental": "clínicas dentales odontología",
        "odontología": "clínicas dentales",
        "inmobiliaria": "sector inmobiliario real estate",
        "real estate": "sector inmobiliario",
        "retail": "comercio minorista retail",
        "comercio": "comercio minorista",
        "restaurante": "gastronomía restaurantes",
        "gastronomía": "restaurantes gastronomía",
        "turismo": "turismo hotelería",
        "hotel": "hotelería turismo",
        "educación": "sector educativo",
        "legal": "servicios legales abogados",
        "abogados": "servicios legales",
        "contabilidad": "servicios contables",
        "marketing": "agencia marketing digital",
        "publicidad": "agencia publicidad marketing",
        "construcción": "sector construcción",
        "manufactura": "industria manufactura",
        "logística": "logística transporte",
        "transporte": "transporte logística",
        "seguros": "sector seguros",
        "finanzas": "servicios financieros",
        "consultoría": "consultoría empresarial",
        "recursos humanos": "RRHH recursos humanos",
        "ecommerce": "comercio electrónico ecommerce",
        "fitness": "gimnasios fitness",
        "belleza": "estética belleza",
        "peluquería": "peluquerías estética",
    }
    
    for key, value in mapeo.items():
        if key in rubro_lower:
            return value
    
    return rubro


def _extraer_desafios_de_contenido(contenido: str, rubro: str, pais: str) -> List[str]:
    """Extrae desafíos específicos del contenido encontrado."""
    desafios = []
    contenido_lower = contenido.lower()
    
    # Patrones de desafíos comunes
    patrones_desafios = [
        # Captación y ventas
        ("captación de clientes", "Dificultad para captar nuevos clientes de forma constante"),
        ("adquisición de clientes", "Alto costo de adquisición de clientes"),
        ("generar leads", "Generación de leads calificados"),
        ("competencia", "Alta competencia en el mercado"),
        
        # Operaciones
        ("procesos manuales", "Procesos manuales que consumen tiempo y recursos"),
        ("automatización", "Falta de automatización en procesos clave"),
        ("eficiencia operativa", "Necesidad de mejorar la eficiencia operativa"),
        ("productividad", "Baja productividad del equipo"),
        
        # Clientes
        ("retención", "Retención y fidelización de clientes"),
        ("satisfacción del cliente", "Mejorar la experiencia y satisfacción del cliente"),
        ("atención al cliente", "Atención al cliente lenta o inconsistente"),
        ("seguimiento", "Falta de seguimiento a clientes potenciales"),
        
        # Digital
        ("presencia digital", "Presencia digital débil o desactualizada"),
        ("marketing digital", "Estrategias de marketing digital ineficientes"),
        ("redes sociales", "Gestión de redes sociales sin resultados"),
        
        # Recursos
        ("talento", "Dificultad para encontrar y retener talento"),
        ("capacitación", "Falta de capacitación del equipo"),
        ("costos", "Control y reducción de costos operativos"),
        
        # Tecnología
        ("tecnología", "Adopción de nuevas tecnologías"),
        ("digitalización", "Transformación digital del negocio"),
        ("inteligencia artificial", "Implementación de IA para mejorar procesos"),
        
        # Específicos por sector
        ("no-show", "Cancelaciones y no-shows de última hora"),
        ("inventario", "Gestión de inventario y stock"),
        ("facturación", "Procesos de facturación y cobro"),
        ("citas", "Gestión de citas y agenda"),
    ]
    
    for patron, desafio in patrones_desafios:
        if patron in contenido_lower and desafio not in desafios:
            desafios.append(desafio)
            if len(desafios) >= 5:
                break
    
    return desafios[:5]


def _get_desafios_genericos(rubro: str) -> List[str]:
    """Retorna desafíos genéricos por rubro cuando no se encuentra info específica."""
    rubro_lower = rubro.lower()
    
    # Desafíos por tipo de negocio
    desafios_por_rubro = {
        "dental": [
            "Cancelaciones y no-shows de pacientes",
            "Captación de nuevos pacientes en un mercado competitivo",
            "Gestión manual de citas y recordatorios",
            "Seguimiento post-tratamiento inconsistente",
            "Presencia digital limitada frente a la competencia"
        ],
        "salud": [
            "Gestión de citas y tiempos de espera",
            "Seguimiento de pacientes entre consultas",
            "Documentación y registros manuales",
            "Comunicación con pacientes fuera del consultorio",
            "Captación de nuevos pacientes"
        ],
        "inmobiliaria": [
            "Seguimiento de leads que no concretan",
            "Respuesta lenta a consultas de propiedades",
            "Gestión de múltiples propiedades y clientes",
            "Calificación de compradores potenciales",
            "Competencia de portales online"
        ],
        "retail": [
            "Gestión de inventario y stock",
            "Competencia del ecommerce",
            "Fidelización de clientes",
            "Atención al cliente en múltiples canales",
            "Análisis de ventas y tendencias"
        ],
        "restaurante": [
            "Gestión de reservas y capacidad",
            "No-shows y cancelaciones",
            "Presencia en apps de delivery",
            "Fidelización de clientes frecuentes",
            "Gestión de reseñas online"
        ],
        "software": [
            "Generación de leads B2B calificados",
            "Ciclos de venta largos",
            "Retención de clientes (churn)",
            "Soporte técnico escalable",
            "Competencia global"
        ],
        "consultoría": [
            "Generación constante de nuevos clientes",
            "Diferenciación en un mercado saturado",
            "Escalabilidad del servicio",
            "Gestión del conocimiento interno",
            "Seguimiento de propuestas"
        ],
        "educación": [
            "Captación de estudiantes",
            "Retención y deserción",
            "Adaptación a modalidades híbridas",
            "Seguimiento del progreso estudiantil",
            "Comunicación con familias"
        ],
        "legal": [
            "Captación de nuevos casos",
            "Gestión de documentación",
            "Seguimiento de plazos y vencimientos",
            "Comunicación con clientes",
            "Facturación de horas"
        ],
        "marketing": [
            "Demostrar ROI a clientes",
            "Retención de clientes",
            "Escalabilidad de servicios",
            "Mantenerse actualizado con tendencias",
            "Gestión de múltiples cuentas"
        ],
    }
    
    # Buscar coincidencia
    for key, desafios in desafios_por_rubro.items():
        if key in rubro_lower:
            return desafios
    
    # Desafíos genéricos si no hay match
    return [
        "Captación de nuevos clientes de forma constante",
        "Procesos manuales que consumen tiempo del equipo",
        "Seguimiento inconsistente de leads y oportunidades",
        "Presencia digital que no genera resultados",
        "Falta de automatización en tareas repetitivas"
    ]


def _formatear_desafios(desafios: List[str], rubro: str, pais: str) -> str:
    """Formatea los desafíos para mostrar al usuario."""
    if not desafios:
        return ""
    
    texto = f"Según mi investigación, las empresas de {rubro} en {pais} suelen enfrentar:\n\n"
    
    for i, desafio in enumerate(desafios, 1):
        texto += f"{i}. {desafio}\n"
    
    texto += "\n¿Te identificás con alguno de estos? ¿O hay otro desafío más importante para vos?"
    
    return texto


async def calcular_qualification_tier(
    team_size: str,
    rubro: str,
    social_metrics: dict = None,
    country: str = ""
) -> Dict:
    """
    Calcula el tier de cualificación basado en múltiples factores.
    
    Returns:
        {
            "tier": "premium" | "standard" | "education" | "agency",
            "reason": "explicación",
            "estimated_potential": "alto" | "medio" | "bajo",
            "recommended_product": "producto recomendado",
            "recommended_url": "url"
        }
    """
    result = {
        "tier": "standard",
        "reason": "",
        "estimated_potential": "medio",
        "recommended_product": "DAN Autopilots",
        "recommended_url": "https://hello.dania.ai/soluciones"
    }
    
    # Parsear team_size
    team_num = 0
    try:
        # Extraer número del string
        import re
        nums = re.findall(r'\d+', str(team_size))
        if nums:
            team_num = int(nums[0])
    except:
        team_num = 0
    
    social_metrics = social_metrics or {}
    
    # Indicadores de inversión/potencial
    tiene_inversion = False
    razones_premium = []
    
    # Check métricas sociales
    ig_followers = social_metrics.get("instagram_followers", 0)
    fb_followers = social_metrics.get("facebook_followers", 0)
    tiene_ads = social_metrics.get("tiene_ads_activos", False)
    tiene_ecommerce = social_metrics.get("tiene_ecommerce", False)
    multiples_sucursales = social_metrics.get("multiples_sucursales", False)
    
    if ig_followers >= 5000 or fb_followers >= 5000:
        tiene_inversion = True
        razones_premium.append("presencia fuerte en redes sociales")
    
    if tiene_ads:
        tiene_inversion = True
        razones_premium.append("invierte en publicidad digital")
    
    if tiene_ecommerce:
        tiene_inversion = True
        razones_premium.append("tiene ecommerce activo")
    
    if multiples_sucursales:
        tiene_inversion = True
        razones_premium.append("múltiples sucursales")
    
    # Rubros de alta facturación
    rubros_premium = [
        "tech", "software", "tecnología", "fintech",
        "inmobiliaria", "real estate",
        "salud", "médico", "clínica",
        "legal", "abogados",
        "consultoría",
        "construcción",
        "manufactura"
    ]
    
    rubro_lower = rubro.lower()
    for rp in rubros_premium:
        if rp in rubro_lower:
            tiene_inversion = True
            razones_premium.append(f"rubro de alta facturación ({rubro})")
            break
    
    # Lógica de clasificación
    if team_num >= 10 and tiene_inversion:
        result["tier"] = "premium"
        result["reason"] = f"Equipo de {team_num} personas + {', '.join(razones_premium[:2])}"
        result["estimated_potential"] = "alto"
        result["recommended_product"] = "Consultoría Personalizada"
        result["recommended_url"] = "Cal.com"  # Se reemplaza por link real
    
    elif team_num >= 10:
        result["tier"] = "standard"
        result["reason"] = f"Equipo de {team_num} personas"
        result["estimated_potential"] = "medio"
        result["recommended_product"] = "DAN Autopilots"
        result["recommended_url"] = "https://hello.dania.ai/soluciones"
    
    elif team_num > 0 and team_num < 10:
        result["tier"] = "standard"
        result["reason"] = f"Equipo pequeño ({team_num} personas)"
        result["estimated_potential"] = "medio"
        result["recommended_product"] = "DAN Autopilots"
        result["recommended_url"] = "https://hello.dania.ai/soluciones"
    
    else:
        result["tier"] = "standard"
        result["reason"] = "Información de equipo no disponible"
        result["estimated_potential"] = "medio"
        result["recommended_product"] = "DAN Autopilots"
        result["recommended_url"] = "https://hello.dania.ai/soluciones"
    
    return result


# URLs de derivación por tier
DERIVATION_URLS = {
    "premium": {
        "product": "Consultoría Personalizada",
        "description": "Reunión con nuestro equipo para diseñar una solución a medida",
        "url": "Cal.com",  # Se genera dinámicamente
        "message": "Por el perfil de tu empresa, te recomiendo agendar una consultoría gratuita con nuestro equipo. Vamos a analizar tu caso específico y diseñar una solución a medida."
    },
    "standard": {
        "product": "DAN Autopilots",
        "description": "Automatizaciones pre-configuradas por sector",
        "url": "https://hello.dania.ai/soluciones",
        "message": "Te recomiendo explorar nuestras soluciones de automatización. Tenemos Autopilots específicos para tu rubro que podés implementar rápidamente."
    },
    "education": {
        "product": "Dania University",
        "description": "Formación certificada en IA",
        "url": "https://dania.university/programas/integrador-ia",
        "message": "Si querés formarte en IA y automatización, tenemos programas diseñados para que domines estas herramientas en semanas."
    },
    "agency": {
        "product": "Lanzá tu Agencia IA",
        "description": "Programa para crear tu propia agencia",
        "url": "https://lanzatuagencia.dania.ai/",
        "message": "Si querés lanzar tu propia agencia de IA, tenemos un programa completo con todo lo que necesitás para empezar."
    }
}


def get_derivation_message(tier: str, calcom_link: str = "") -> Dict:
    """Obtiene el mensaje y URL de derivación según el tier."""
    derivation = DERIVATION_URLS.get(tier, DERIVATION_URLS["standard"])
    
    result = derivation.copy()
    
    # Si es premium, usar el link de Cal.com
    if tier == "premium" and calcom_link:
        result["url"] = calcom_link
    
    return result
