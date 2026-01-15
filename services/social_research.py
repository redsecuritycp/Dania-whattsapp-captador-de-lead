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
APIFY_TIMEOUT = 45.0

# ═══════════════════════════════════════════════════════════════════
# DOMINIOS A EXCLUIR DE RESULTADOS DE NOTICIAS
# ═══════════════════════════════════════════════════════════════════
DOMINIOS_EXCLUIR_NOTICIAS = [
    # Sitios de descarga de apps
    'softonic.com', 'softonic.', 
    'play.google.com', 'apps.apple.com',
    'apkpure.com', 'apkmirror.com', 
    'uptodown.com', 'aptoide.com',
    'getjar.com', 'apkmonk.com',
    
    # Redes sociales (no son noticias)
    'facebook.com', 'twitter.com', 'x.com',
    'instagram.com', 'linkedin.com',
    'tiktok.com', 'pinterest.com',
    
    # Otros no relevantes
    'youtube.com', 'vimeo.com',
    'wikipedia.org', 'wikimedia.org',
    'amazon.com', 'mercadolibre.',
    'ebay.com', 'aliexpress.com',
]


def es_noticia_valida(
    url: str, 
    titulo: str, 
    nombre_empresa: str = ""
) -> bool:
    """
    Verifica si una URL es una noticia válida y RELEVANTE.
    
    LÓGICA UNIVERSAL:
    1. El nombre de la empresa DEBE aparecer en el título
    2. Excluir dominios de descarga/apps
    3. Excluir títulos con palabras genéricas irrelevantes
    
    Args:
        url: URL de la noticia
        titulo: Título de la noticia
        nombre_empresa: Nombre de la empresa para validar relevancia
    """
    url_lower = url.lower()
    titulo_lower = titulo.lower() if titulo else ""
    
    # ═══════════════════════════════════════════════════════════════
    # 1. VALIDAR RELEVANCIA: Empresa debe estar en título
    # ═══════════════════════════════════════════════════════════════
    if nombre_empresa:
        empresa_lower = nombre_empresa.lower()
        
        # Buscar nombre completo o palabras principales
        palabras_empresa = [
            p for p in empresa_lower.split() 
            if len(p) >= 4  # Ignorar palabras cortas
        ]
        
        empresa_en_titulo = False
        
        # Verificar nombre completo
        if empresa_lower in titulo_lower:
            empresa_en_titulo = True
        else:
            # Verificar palabras principales (al menos 1)
            for palabra in palabras_empresa:
                if palabra in titulo_lower:
                    empresa_en_titulo = True
                    break
        
        if not empresa_en_titulo:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # 2. EXCLUIR DOMINIOS NO VÁLIDOS
    # ═══════════════════════════════════════════════════════════════
    dominios_excluir = [
        # Descargas de apps
        'softonic', 'play.google.com', 'apps.apple.com',
        'apkpure', 'apkmirror', 'uptodown', 'aptoide',
        'getjar', 'apkmonk', 'appbrain', 'apk',
        
        # Redes sociales
        'facebook.com', 'twitter.com', 'x.com',
        'instagram.com', 'linkedin.com', 'tiktok.com',
        'pinterest.com', 'reddit.com',
        
        # Otros no relevantes
        'youtube.com', 'vimeo.com', 'dailymotion',
        'wikipedia.org', 'wikimedia.org',
        'amazon.', 'mercadolibre.', 'ebay.', 'aliexpress',
        
        # Foros y Q&A
        'stackoverflow.', 'quora.com', 'yahoo.com/answers',
        
        # Directorios
        'yelp.', 'tripadvisor.', 'foursquare.',
        'yellowpages.', 'paginasamarillas.',
    ]
    
    for dominio in dominios_excluir:
        if dominio in url_lower:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # 3. EXCLUIR POR PALABRAS EN TÍTULO
    # ═══════════════════════════════════════════════════════════════
    palabras_excluir_titulo = [
        # Descargas
        'descargar', 'download', 'apk', 'app store',
        'google play', 'instalar', 'install', 'gratis',
        'free download', 'descarga gratis', 'bajar',
        
        # Empleos (no son noticias de la empresa)
        'empleo', 'trabajo', 'vacante', 'búsqueda laboral',
        'busqueda laboral', 'cv', 'currículum', 'curriculum',
        'postular', 'postulate', 'job', 'hiring', 'career',
        'trabaja con nosotros', 'únete', 'join us',
        
        # Reviews genéricos
        'opiniones de usuarios', 'user reviews',
        'rating', 'calificación', 'reseña de',
    ]
    
    for palabra in palabras_excluir_titulo:
        if palabra in titulo_lower:
            return False
    
    return True


def construir_query_noticias(empresa: str, pais: str = "") -> str:
    """Construye query optimizada para encontrar noticias reales."""
    # Términos que indican contenido periodístico
    terminos_noticias = "noticias OR prensa OR nota OR artículo OR noticia"
    
    # Términos a excluir
    excluir = "-softonic -apk -download -descargar -\"google play\" -\"app store\""
    
    query = f'"{empresa}" ({terminos_noticias}) {excluir}'
    
    if pais:
        query += f' {pais}'
    
    return query

# ═══════════════════════════════════════════════════════════════════════════════
# DICCIONARIO DE UBICACIONES COMPLETO - VARIANTES Y ABREVIACIONES
# Todos los países hispanohablantes + USA + Brasil + UE principales
# Todos los estados/provincias + ciudades principales
# ═══════════════════════════════════════════════════════════════════════════════
UBICACIONES_VARIANTES = {
    # ═══════════════════════════════════════════════════════════════════════════
    # PAÍSES - Códigos ISO, gentilicios, códigos WhatsApp
    # ═══════════════════════════════════════════════════════════════════════════
    "paises": {
        "argentina": ["argentina", "ar", "arg", "🇦🇷", "+54"],
        "brasil": ["brasil", "brazil", "br", "bra", "🇧🇷", "+55"],
        "chile": ["chile", "cl", "chi", "🇨🇱", "+56"],
        "colombia": ["colombia", "co", "col", "🇨🇴", "+57"],
        "peru": ["peru", "perú", "pe", "per", "🇵🇪", "+51"],
        "venezuela": ["venezuela", "ve", "ven", "🇻🇪", "+58"],
        "ecuador": ["ecuador", "ec", "ecu", "🇪🇨", "+593"],
        "bolivia": ["bolivia", "bo", "bol", "🇧🇴", "+591"],
        "paraguay": ["paraguay", "py", "par", "🇵🇾", "+595"],
        "uruguay": ["uruguay", "uy", "uru", "🇺🇾", "+598"],
        "guatemala": ["guatemala", "gt", "gua", "🇬🇹", "+502"],
        "honduras": ["honduras", "hn", "hon", "🇭🇳", "+504"],
        "el_salvador": ["el salvador", "sv", "sal", "🇸🇻", "+503"],
        "nicaragua": ["nicaragua", "ni", "nic", "🇳🇮", "+505"],
        "costa_rica": ["costa rica", "cr", "cri", "🇨🇷", "+506"],
        "panama": ["panama", "panamá", "pa", "pan", "🇵🇦", "+507"],
        "cuba": ["cuba", "cu", "cub", "🇨🇺", "+53"],
        "dominicana": [
            "dominicana", "república dominicana", "do", "dom", "rd", "🇩🇴",
            "+1809", "+1829", "+1849"
        ],
        "puerto_rico":
        ["puerto rico", "pr", "boricua", "🇵🇷", "+1787", "+1939"],
        "mexico": ["mexico", "méxico", "mx", "mex", "🇲🇽", "+52"],
        "usa": [
            "usa", "united states", "estados unidos", "us", "eeuu", "ee.uu",
            "🇺🇸", "+1"
        ],
        "canada": ["canada", "canadá", "ca", "can", "🇨🇦", "+1"],
        "espana": ["españa", "espana", "spain", "es", "🇪🇸", "+34"],
        "portugal": ["portugal", "pt", "por", "🇵🇹", "+351"],
        "italia": ["italia", "italy", "it", "ita", "🇮🇹", "+39"],
        "francia": ["francia", "france", "fr", "fra", "🇫🇷", "+33"],
        "alemania":
        ["alemania", "germany", "de", "deu", "deutschland", "🇩🇪", "+49"],
        "reino_unido": [
            "reino unido", "united kingdom", "uk", "gb", "britain", "england",
            "inglaterra", "🇬🇧", "+44"
        ],
        "paises_bajos": [
            "países bajos", "paises bajos", "holanda", "netherlands", "nl",
            "🇳🇱", "+31"
        ],
        "belgica": ["bélgica", "belgica", "belgium", "be", "🇧🇪", "+32"],
        "suiza": ["suiza", "switzerland", "ch", "sui", "🇨🇭", "+41"],
        "austria": ["austria", "at", "aut", "🇦🇹", "+43"],
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ARGENTINA
    # ═══════════════════════════════════════════════════════════════════════════
    "argentina": {
        "provincias": {
            "buenos_aires":
            ["buenos aires", "bs as", "bs. as.", "bsas", "ba", "pba"],
            "caba": [
                "caba", "capital federal", "ciudad autónoma",
                "ciudad autonoma", "c.a.b.a"
            ],
            "catamarca": ["catamarca", "cat"],
            "chaco": ["chaco", "cha"],
            "chubut": ["chubut", "chu"],
            "cordoba": ["córdoba", "cordoba", "cba"],
            "corrientes": ["corrientes", "corr", "ctes"],
            "entre_rios": ["entre ríos", "entre rios", "er"],
            "formosa": ["formosa", "for"],
            "jujuy": ["jujuy", "juj"],
            "la_pampa": ["la pampa", "lpampa", "lp"],
            "la_rioja": ["la rioja", "rioja", "lr"],
            "mendoza": ["mendoza", "mza", "mdz"],
            "misiones": ["misiones", "mis"],
            "neuquen": ["neuquén", "neuquen", "nqn"],
            "rio_negro": ["río negro", "rio negro", "rn"],
            "salta": ["salta", "sal"],
            "san_juan": ["san juan", "sj"],
            "san_luis": ["san luis", "sl"],
            "santa_cruz": ["santa cruz", "sc"],
            "santa_fe": ["santa fe", "sf", "sta fe", "sta. fe", "santafe"],
            "santiago_estero": ["santiago del estero", "sgo estero", "sde"],
            "tierra_fuego": ["tierra del fuego", "tdf"],
            "tucuman": ["tucumán", "tucuman", "tuc"],
        },
        "ciudades": {
            "caba_ciudad": ["buenos aires", "caba", "capital federal"],
            "la_plata": ["la plata"],
            "mar_del_plata": ["mar del plata", "mdp", "mdq", "mardel"],
            "bahia_blanca": ["bahía blanca", "bahia blanca"],
            "tandil": ["tandil"],
            "olavarria": ["olavarría", "olavarria"],
            "rosario": ["rosario", "ros"],
            "santa_fe_ciudad": ["santa fe ciudad", "santa fe capital"],
            "rafaela": ["rafaela"],
            "venado_tuerto": ["venado tuerto"],
            "reconquista": ["reconquista"],
            "san_jorge": ["san jorge"],
            "esperanza": ["esperanza"],
            "san_justo": ["san justo"],
            "cordoba_ciudad": ["córdoba ciudad", "córdoba capital"],
            "villa_maria": ["villa maría", "villa maria"],
            "rio_cuarto": ["río cuarto", "rio cuarto"],
            "san_francisco": ["san francisco"],
            "mendoza_ciudad": ["mendoza ciudad", "mendoza capital"],
            "san_rafael": ["san rafael"],
            "tucuman_ciudad": ["san miguel de tucumán", "tucumán capital"],
            "salta_ciudad": ["salta ciudad", "salta capital"],
            "parana": ["paraná", "parana"],
            "concordia": ["concordia"],
            "neuquen_ciudad": ["neuquén ciudad", "neuquén capital"],
            "bariloche": ["san carlos de bariloche", "bariloche"],
            "comodoro_rivadavia": ["comodoro rivadavia", "comodoro"],
            "ushuaia": ["ushuaia"],
            "rio_gallegos": ["río gallegos", "rio gallegos"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # MÉXICO
    # ═══════════════════════════════════════════════════════════════════════════
    "mexico": {
        "estados": {
            "aguascalientes": ["aguascalientes", "ags"],
            "baja_california": ["baja california", "bc"],
            "baja_california_sur": ["baja california sur", "bcs"],
            "campeche": ["campeche", "camp"],
            "chiapas": ["chiapas", "chis"],
            "chihuahua": ["chihuahua", "chih"],
            "coahuila": ["coahuila", "coah"],
            "colima": ["colima", "col"],
            "cdmx": [
                "cdmx", "ciudad de méxico", "ciudad de mexico", "df", "d.f.",
                "distrito federal"
            ],
            "durango": ["durango", "dgo"],
            "guanajuato": ["guanajuato", "gto"],
            "guerrero": ["guerrero", "gro"],
            "hidalgo": ["hidalgo", "hgo"],
            "jalisco": ["jalisco", "jal"],
            "estado_mexico": ["estado de méxico", "edomex", "edo mex"],
            "michoacan": ["michoacán", "michoacan", "mich"],
            "morelos": ["morelos", "mor"],
            "nayarit": ["nayarit", "nay"],
            "nuevo_leon": ["nuevo león", "nuevo leon", "nl"],
            "oaxaca": ["oaxaca", "oax"],
            "puebla": ["puebla", "pue"],
            "queretaro": ["querétaro", "queretaro", "qro"],
            "quintana_roo": ["quintana roo", "qroo"],
            "san_luis_potosi": ["san luis potosí", "san luis potosi", "slp"],
            "sinaloa": ["sinaloa", "sin"],
            "sonora": ["sonora", "son"],
            "tabasco": ["tabasco", "tab"],
            "tamaulipas": ["tamaulipas", "tamps"],
            "tlaxcala": ["tlaxcala", "tlax"],
            "veracruz": ["veracruz", "ver"],
            "yucatan": ["yucatán", "yucatan", "yuc"],
            "zacatecas": ["zacatecas", "zac"],
        },
        "ciudades": {
            "cdmx_ciudad": ["ciudad de méxico", "cdmx", "df", "mexico city"],
            "guadalajara": ["guadalajara", "gdl"],
            "monterrey": ["monterrey", "mty"],
            "puebla_ciudad": ["puebla"],
            "tijuana": ["tijuana", "tj"],
            "leon": ["león", "leon"],
            "juarez": ["ciudad juárez", "juárez", "juarez"],
            "merida": ["mérida", "merida"],
            "cancun": ["cancún", "cancun"],
            "queretaro_ciudad": ["querétaro", "queretaro"],
            "morelia": ["morelia"],
            "veracruz_ciudad": ["veracruz"],
            "oaxaca_ciudad": ["oaxaca"],
            "playa_del_carmen": ["playa del carmen"],
            "los_cabos": ["los cabos", "cabo san lucas"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ESPAÑA
    # ═══════════════════════════════════════════════════════════════════════════
    "espana": {
        "comunidades": {
            "andalucia": ["andalucía", "andalucia", "and"],
            "aragon": ["aragón", "aragon", "ara"],
            "asturias": ["asturias", "principado de asturias", "ast"],
            "baleares": ["islas baleares", "baleares", "ib"],
            "canarias": ["canarias", "islas canarias", "ic"],
            "cantabria": ["cantabria", "cant"],
            "castilla_mancha": ["castilla-la mancha", "clm"],
            "castilla_leon": ["castilla y león", "castilla y leon", "cyl"],
            "cataluna": ["cataluña", "catalunya", "cat"],
            "extremadura": ["extremadura", "ext"],
            "galicia": ["galicia", "gal"],
            "madrid": ["madrid", "comunidad de madrid", "mad"],
            "murcia": ["murcia", "región de murcia", "mur"],
            "navarra": ["navarra", "nav"],
            "pais_vasco": ["país vasco", "pais vasco", "euskadi", "pv"],
            "la_rioja": ["la rioja", "rioja", "rio"],
            "valencia": ["comunidad valenciana", "valencia", "val"],
        },
        "ciudades": {
            "madrid_ciudad": ["madrid"],
            "barcelona": ["barcelona", "bcn", "barna"],
            "valencia_ciudad": ["valencia", "valència"],
            "sevilla": ["sevilla"],
            "zaragoza": ["zaragoza", "zgz"],
            "malaga": ["málaga", "malaga"],
            "bilbao": ["bilbao"],
            "alicante": ["alicante"],
            "cordoba_es": ["córdoba", "cordoba"],
            "valladolid": ["valladolid"],
            "granada": ["granada"],
            "san_sebastian": ["san sebastián", "donostia"],
            "santander": ["santander"],
            "salamanca": ["salamanca"],
            "pamplona": ["pamplona", "iruña"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # COLOMBIA
    # ═══════════════════════════════════════════════════════════════════════════
    "colombia": {
        "departamentos": {
            "antioquia": ["antioquia", "ant"],
            "atlantico": ["atlántico", "atlantico", "atl"],
            "bolivar_col": ["bolívar", "bolivar"],
            "boyaca": ["boyacá", "boyaca"],
            "caldas": ["caldas"],
            "cundinamarca": ["cundinamarca", "cund"],
            "huila": ["huila"],
            "meta": ["meta"],
            "narino": ["nariño", "narino"],
            "norte_santander": ["norte de santander"],
            "risaralda": ["risaralda"],
            "santander": ["santander", "stder"],
            "tolima": ["tolima"],
            "valle_cauca": ["valle del cauca", "valle"],
            "bogota_dc": ["bogotá d.c.", "bogota dc", "bogotá", "bogota"],
        },
        "ciudades": {
            "bogota": ["bogotá", "bogota", "bog"],
            "medellin": ["medellín", "medellin", "med"],
            "cali": ["cali", "santiago de cali"],
            "barranquilla": ["barranquilla", "baq"],
            "cartagena_col": ["cartagena", "cartagena de indias"],
            "cucuta": ["cúcuta", "cucuta"],
            "bucaramanga": ["bucaramanga"],
            "pereira": ["pereira"],
            "santa_marta": ["santa marta"],
            "manizales": ["manizales"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CHILE
    # ═══════════════════════════════════════════════════════════════════════════
    "chile": {
        "regiones": {
            "arica_parinacota": ["arica y parinacota", "arica", "xv"],
            "tarapaca": ["tarapacá", "tarapaca", "i"],
            "antofagasta": ["antofagasta", "ii"],
            "atacama": ["atacama", "iii"],
            "coquimbo": ["coquimbo", "iv"],
            "valparaiso": ["valparaíso", "valparaiso", "v"],
            "ohiggins": ["o'higgins", "ohiggins", "vi"],
            "maule": ["maule", "vii"],
            "biobio": ["biobío", "biobio", "viii"],
            "araucania": ["araucanía", "araucania", "ix"],
            "los_rios": ["los ríos", "los rios", "xiv"],
            "los_lagos": ["los lagos", "x"],
            "aysen": ["aysén", "aysen", "xi"],
            "magallanes": ["magallanes", "xii"],
            "metropolitana": ["metropolitana", "rm", "santiago", "xiii"],
        },
        "ciudades": {
            "santiago": ["santiago", "santiago de chile", "stgo"],
            "valparaiso_ciudad": ["valparaíso", "valparaiso", "valpo"],
            "concepcion": ["concepción", "concepcion"],
            "vina_del_mar": ["viña del mar", "vina del mar"],
            "antofagasta_ciudad": ["antofagasta"],
            "temuco": ["temuco"],
            "puerto_montt": ["puerto montt"],
            "la_serena": ["la serena"],
            "punta_arenas": ["punta arenas"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PERÚ
    # ═══════════════════════════════════════════════════════════════════════════
    "peru": {
        "departamentos": {
            "amazonas_pe": ["amazonas"],
            "arequipa": ["arequipa", "aqp"],
            "ayacucho": ["ayacucho"],
            "cajamarca": ["cajamarca"],
            "cusco": ["cusco", "cuzco"],
            "huanuco": ["huánuco", "huanuco"],
            "ica": ["ica"],
            "junin": ["junín", "junin"],
            "la_libertad": ["la libertad"],
            "lambayeque": ["lambayeque"],
            "lima": ["lima"],
            "loreto": ["loreto"],
            "piura": ["piura"],
            "puno": ["puno"],
            "tacna": ["tacna"],
        },
        "ciudades": {
            "lima_ciudad": ["lima", "lima metropolitana"],
            "arequipa_ciudad": ["arequipa"],
            "trujillo": ["trujillo"],
            "chiclayo": ["chiclayo"],
            "piura_ciudad": ["piura"],
            "iquitos": ["iquitos"],
            "cusco_ciudad": ["cusco", "cuzco"],
            "huancayo": ["huancayo"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # GUATEMALA
    # ═══════════════════════════════════════════════════════════════════════════
    "guatemala": {
        "departamentos": {
            "alta_verapaz": ["alta verapaz"],
            "baja_verapaz": ["baja verapaz"],
            "chimaltenango": ["chimaltenango"],
            "chiquimula": ["chiquimula"],
            "el_progreso": ["el progreso"],
            "escuintla": ["escuintla"],
            "guatemala_depto": ["guatemala"],
            "huehuetenango": ["huehuetenango"],
            "izabal": ["izabal"],
            "jalapa_gt": ["jalapa"],
            "jutiapa": ["jutiapa"],
            "peten": ["petén", "peten"],
            "quetzaltenango": ["quetzaltenango", "xela"],
            "quiche": ["quiché", "quiche"],
            "retalhuleu": ["retalhuleu"],
            "sacatepequez": ["sacatepéquez", "sacatepequez"],
            "san_marcos_gt": ["san marcos"],
            "santa_rosa_gt": ["santa rosa"],
            "solola": ["sololá", "solola"],
            "suchitepequez": ["suchitepéquez", "suchitepequez"],
            "totonicapan": ["totonicapán", "totonicapan"],
            "zacapa": ["zacapa"],
        },
        "ciudades": {
            "ciudad_guatemala": ["ciudad de guatemala", "guatemala city"],
            "mixco": ["mixco"],
            "villa_nueva": ["villa nueva"],
            "quetzaltenango_ciudad": ["quetzaltenango", "xela"],
            "escuintla_ciudad": ["escuintla"],
            "coban": ["cobán", "coban"],
            "antigua_guatemala": ["antigua guatemala", "antigua"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # HONDURAS
    # ═══════════════════════════════════════════════════════════════════════════
    "honduras": {
        "departamentos": {
            "atlantida": ["atlántida", "atlantida"],
            "choluteca": ["choluteca"],
            "colon_hn": ["colón", "colon"],
            "comayagua": ["comayagua"],
            "copan": ["copán", "copan"],
            "cortes": ["cortés", "cortes"],
            "francisco_morazan": ["francisco morazán", "francisco morazan"],
            "intibuca": ["intibucá", "intibuca"],
            "la_paz_hn": ["la paz"],
            "lempira": ["lempira"],
            "olancho": ["olancho"],
            "santa_barbara_hn": ["santa bárbara", "santa barbara"],
            "yoro": ["yoro"],
        },
        "ciudades": {
            "tegucigalpa": ["tegucigalpa", "tegus"],
            "san_pedro_sula": ["san pedro sula", "sps"],
            "choloma": ["choloma"],
            "la_ceiba": ["la ceiba"],
            "comayagua_ciudad": ["comayagua"],
            "roatan": ["roatán", "roatan"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # EL SALVADOR
    # ═══════════════════════════════════════════════════════════════════════════
    "el_salvador": {
        "departamentos": {
            "ahuachapan": ["ahuachapán", "ahuachapan"],
            "cabanas": ["cabañas", "cabanas"],
            "chalatenango": ["chalatenango"],
            "cuscatlan": ["cuscatlán", "cuscatlan"],
            "la_libertad_sv": ["la libertad"],
            "la_paz_sv": ["la paz"],
            "la_union_sv": ["la unión", "la union"],
            "morazan": ["morazán", "morazan"],
            "san_miguel_sv": ["san miguel"],
            "san_salvador": ["san salvador"],
            "san_vicente": ["san vicente"],
            "santa_ana_sv": ["santa ana"],
            "sonsonate": ["sonsonate"],
            "usulutan": ["usulután", "usulutan"],
        },
        "ciudades": {
            "san_salvador_ciudad": ["san salvador"],
            "santa_ana_ciudad": ["santa ana"],
            "san_miguel_ciudad": ["san miguel"],
            "santa_tecla": ["santa tecla"],
            "soyapango": ["soyapango"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # NICARAGUA
    # ═══════════════════════════════════════════════════════════════════════════
    "nicaragua": {
        "departamentos": {
            "boaco": ["boaco"],
            "carazo": ["carazo"],
            "chinandega": ["chinandega"],
            "chontales": ["chontales"],
            "esteli": ["estelí", "esteli"],
            "granada_ni": ["granada"],
            "jinotega": ["jinotega"],
            "leon_ni": ["león", "leon"],
            "madriz": ["madriz"],
            "managua": ["managua"],
            "masaya": ["masaya"],
            "matagalpa": ["matagalpa"],
            "nueva_segovia": ["nueva segovia"],
            "rivas": ["rivas"],
            "raccn": ["raccn", "raan", "costa caribe norte"],
            "raccs": ["raccs", "raas", "costa caribe sur"],
        },
        "ciudades": {
            "managua_ciudad": ["managua"],
            "leon_ciudad": ["león", "leon"],
            "masaya_ciudad": ["masaya"],
            "chinandega_ciudad": ["chinandega"],
            "granada_ciudad_ni": ["granada"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # COSTA RICA
    # ═══════════════════════════════════════════════════════════════════════════
    "costa_rica": {
        "provincias": {
            "san_jose_cr": ["san josé", "san jose"],
            "alajuela": ["alajuela"],
            "cartago": ["cartago"],
            "heredia": ["heredia"],
            "guanacaste": ["guanacaste"],
            "puntarenas": ["puntarenas"],
            "limon": ["limón", "limon"],
        },
        "ciudades": {
            "san_jose_ciudad_cr": ["san josé", "san jose"],
            "alajuela_ciudad": ["alajuela"],
            "cartago_ciudad": ["cartago"],
            "heredia_ciudad": ["heredia"],
            "liberia": ["liberia"],
            "puntarenas_ciudad": ["puntarenas"],
            "escazu": ["escazú", "escazu"],
            "santa_ana_cr": ["santa ana"],
            "tamarindo": ["tamarindo"],
            "jaco": ["jacó", "jaco"],
            "la_fortuna": ["la fortuna"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PANAMÁ
    # ═══════════════════════════════════════════════════════════════════════════
    "panama": {
        "provincias": {
            "bocas_toro": ["bocas del toro"],
            "chiriqui": ["chiriquí", "chiriqui"],
            "cocle": ["coclé", "cocle"],
            "colon_pa": ["colón", "colon"],
            "darien": ["darién", "darien"],
            "herrera": ["herrera"],
            "los_santos": ["los santos"],
            "panama_prov": ["panamá", "panama"],
            "panama_oeste": ["panamá oeste", "panama oeste"],
            "veraguas": ["veraguas"],
        },
        "ciudades": {
            "panama_ciudad": ["ciudad de panamá", "panama city"],
            "colon_ciudad": ["colón", "colon"],
            "david": ["david"],
            "santiago_pa": ["santiago"],
            "chitre": ["chitré", "chitre"],
            "boquete": ["boquete"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CUBA
    # ═══════════════════════════════════════════════════════════════════════════
    "cuba": {
        "provincias": {
            "pinar_rio": ["pinar del río", "pinar del rio"],
            "artemisa": ["artemisa"],
            "la_habana": ["la habana", "habana"],
            "mayabeque": ["mayabeque"],
            "matanzas": ["matanzas"],
            "villa_clara": ["villa clara"],
            "cienfuegos": ["cienfuegos"],
            "sancti_spiritus": ["sancti spíritus", "sancti spiritus"],
            "ciego_avila": ["ciego de ávila", "ciego de avila"],
            "camaguey": ["camagüey", "camaguey"],
            "las_tunas": ["las tunas"],
            "holguin": ["holguín", "holguin"],
            "granma": ["granma"],
            "santiago_cuba": ["santiago de cuba"],
            "guantanamo": ["guantánamo", "guantanamo"],
        },
        "ciudades": {
            "habana_ciudad": ["la habana", "habana", "havana"],
            "santiago_cuba_ciudad": ["santiago de cuba"],
            "camaguey_ciudad": ["camagüey", "camaguey"],
            "holguin_ciudad": ["holguín", "holguin"],
            "santa_clara": ["santa clara"],
            "varadero": ["varadero"],
            "trinidad_cu": ["trinidad"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # REPÚBLICA DOMINICANA
    # ═══════════════════════════════════════════════════════════════════════════
    "dominicana": {
        "provincias": {
            "distrito_nacional": ["distrito nacional", "dn"],
            "santo_domingo_prov": ["santo domingo"],
            "santiago_rd": ["santiago"],
            "la_vega": ["la vega"],
            "san_cristobal_rd": ["san cristóbal", "san cristobal"],
            "la_romana": ["la romana"],
            "puerto_plata": ["puerto plata"],
            "duarte": ["duarte"],
            "san_pedro_macoris": ["san pedro de macorís"],
            "la_altagracia": ["la altagracia"],
            "espaillat": ["espaillat"],
            "peravia": ["peravia"],
            "samana": ["samaná", "samana"],
        },
        "ciudades": {
            "santo_domingo": ["santo domingo", "sd"],
            "santiago_rd_ciudad": ["santiago de los caballeros"],
            "la_romana_ciudad": ["la romana"],
            "puerto_plata_ciudad": ["puerto plata"],
            "higuey": ["higüey", "higuey"],
            "san_pedro_ciudad": ["san pedro de macorís"],
            "punta_cana": ["punta cana", "bávaro"],
            "samana_ciudad": ["samaná", "samana"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PUERTO RICO
    # ═══════════════════════════════════════════════════════════════════════════
    "puerto_rico": {
        "regiones": {
            "area_metro": ["área metropolitana", "metro"],
            "norte": ["norte", "region norte"],
            "sur": ["sur", "region sur"],
            "este": ["este", "region este"],
            "oeste": ["oeste", "region oeste"],
        },
        "ciudades": {
            "san_juan_pr": ["san juan"],
            "bayamon": ["bayamón", "bayamon"],
            "carolina": ["carolina"],
            "ponce": ["ponce"],
            "caguas": ["caguas"],
            "mayaguez": ["mayagüez", "mayaguez"],
            "arecibo": ["arecibo"],
            "aguadilla": ["aguadilla"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BOLIVIA
    # ═══════════════════════════════════════════════════════════════════════════
    "bolivia": {
        "departamentos": {
            "la_paz_bo": ["la paz"],
            "santa_cruz_bo": ["santa cruz"],
            "cochabamba": ["cochabamba"],
            "potosi": ["potosí", "potosi"],
            "chuquisaca": ["chuquisaca"],
            "oruro": ["oruro"],
            "tarija": ["tarija"],
            "beni": ["beni"],
            "pando": ["pando"],
        },
        "ciudades": {
            "la_paz_ciudad": ["la paz"],
            "santa_cruz_ciudad": ["santa cruz de la sierra", "santa cruz"],
            "cochabamba_ciudad": ["cochabamba"],
            "sucre": ["sucre"],
            "oruro_ciudad": ["oruro"],
            "tarija_ciudad": ["tarija"],
            "el_alto": ["el alto"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PARAGUAY
    # ═══════════════════════════════════════════════════════════════════════════
    "paraguay": {
        "departamentos": {
            "asuncion_dc": ["asunción", "asuncion", "capital"],
            "central_py": ["central"],
            "alto_parana": ["alto paraná", "alto parana"],
            "itapua": ["itapúa", "itapua"],
            "caaguazu": ["caaguazú", "caaguazu"],
            "san_pedro_py": ["san pedro"],
            "cordillera_py": ["cordillera"],
            "guaira": ["guairá", "guaira"],
            "concepcion_py": ["concepción", "concepcion"],
            "amambay": ["amambay"],
        },
        "ciudades": {
            "asuncion_ciudad": ["asunción", "asuncion"],
            "ciudad_del_este": ["ciudad del este", "cde"],
            "san_lorenzo_py": ["san lorenzo"],
            "luque": ["luque"],
            "encarnacion": ["encarnación", "encarnacion"],
            "pedro_juan": ["pedro juan caballero"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # URUGUAY
    # ═══════════════════════════════════════════════════════════════════════════
    "uruguay": {
        "departamentos": {
            "montevideo": ["montevideo", "mdeo"],
            "canelones": ["canelones"],
            "maldonado": ["maldonado"],
            "salto_uy": ["salto"],
            "paysandu": ["paysandú", "paysandu"],
            "colonia": ["colonia"],
            "rivera": ["rivera"],
            "tacuarembo": ["tacuarembó", "tacuarembo"],
            "cerro_largo": ["cerro largo"],
            "rocha": ["rocha"],
        },
        "ciudades": {
            "montevideo_ciudad": ["montevideo"],
            "salto_ciudad": ["salto"],
            "paysandu_ciudad": ["paysandú", "paysandu"],
            "maldonado_ciudad": ["maldonado"],
            "punta_del_este": ["punta del este"],
            "colonia_sacramento": ["colonia del sacramento", "colonia"],
            "rivera_ciudad": ["rivera"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # VENEZUELA
    # ═══════════════════════════════════════════════════════════════════════════
    "venezuela": {
        "estados": {
            "caracas_dc": ["distrito capital", "caracas", "dc"],
            "miranda": ["miranda"],
            "zulia": ["zulia"],
            "carabobo": ["carabobo"],
            "lara": ["lara"],
            "aragua": ["aragua"],
            "bolivar_ve": ["bolívar", "bolivar"],
            "anzoategui": ["anzoátegui", "anzoategui"],
            "tachira": ["táchira", "tachira"],
            "merida_ve": ["mérida", "merida"],
            "falcon": ["falcón", "falcon"],
            "barinas": ["barinas"],
        },
        "ciudades": {
            "caracas": ["caracas", "ccs"],
            "maracaibo": ["maracaibo"],
            "valencia_ve": ["valencia"],
            "barquisimeto": ["barquisimeto"],
            "maracay": ["maracay"],
            "ciudad_guayana": ["ciudad guayana", "puerto ordaz"],
            "merida_ciudad": ["mérida", "merida"],
            "san_cristobal": ["san cristóbal", "san cristobal"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ECUADOR
    # ═══════════════════════════════════════════════════════════════════════════
    "ecuador": {
        "provincias": {
            "pichincha": ["pichincha"],
            "guayas": ["guayas"],
            "azuay": ["azuay"],
            "manabi": ["manabí", "manabi"],
            "tungurahua": ["tungurahua"],
            "el_oro": ["el oro"],
            "loja": ["loja"],
            "esmeraldas": ["esmeraldas"],
            "imbabura": ["imbabura"],
            "chimborazo": ["chimborazo"],
            "galapagos": ["galápagos", "galapagos"],
        },
        "ciudades": {
            "quito": ["quito"],
            "guayaquil": ["guayaquil", "gye"],
            "cuenca": ["cuenca"],
            "santo_domingo_ciudad": ["santo domingo"],
            "machala": ["machala"],
            "manta": ["manta"],
            "portoviejo": ["portoviejo"],
            "ambato": ["ambato"],
            "riobamba": ["riobamba"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # USA
    # ═══════════════════════════════════════════════════════════════════════════
    "usa": {
        "estados": {
            "california": ["california", "ca", "calif"],
            "texas": ["texas", "tx", "tex"],
            "florida": ["florida", "fl", "fla"],
            "new_york": ["new york", "ny"],
            "pennsylvania": ["pennsylvania", "pa"],
            "illinois": ["illinois", "il"],
            "ohio": ["ohio", "oh"],
            "georgia_us": ["georgia", "ga"],
            "north_carolina": ["north carolina", "nc"],
            "michigan": ["michigan", "mi"],
            "new_jersey": ["new jersey", "nj"],
            "virginia": ["virginia", "va"],
            "washington": ["washington", "wa"],
            "arizona": ["arizona", "az"],
            "massachusetts": ["massachusetts", "ma"],
            "tennessee": ["tennessee", "tn"],
            "indiana": ["indiana", "in"],
            "missouri": ["missouri", "mo"],
            "maryland": ["maryland", "md"],
            "colorado": ["colorado", "co"],
            "minnesota": ["minnesota", "mn"],
            "wisconsin": ["wisconsin", "wi"],
            "dc": ["district of columbia", "dc", "washington dc"],
        },
        "ciudades": {
            "new_york_city": ["new york city", "nyc", "nueva york"],
            "los_angeles": ["los angeles", "la", "l.a."],
            "chicago": ["chicago"],
            "houston": ["houston"],
            "phoenix": ["phoenix"],
            "philadelphia": ["philadelphia", "philly"],
            "san_antonio": ["san antonio"],
            "san_diego": ["san diego"],
            "dallas": ["dallas"],
            "san_jose_us": ["san jose"],
            "austin": ["austin"],
            "san_francisco": ["san francisco", "sf"],
            "seattle": ["seattle"],
            "denver": ["denver"],
            "boston": ["boston"],
            "washington_dc": ["washington dc"],
            "miami": ["miami"],
            "atlanta": ["atlanta", "atl"],
            "las_vegas": ["las vegas", "vegas"],
            "portland": ["portland"],
            "silicon_valley": ["silicon valley"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BRASIL
    # ═══════════════════════════════════════════════════════════════════════════
    "brasil": {
        "estados": {
            "sao_paulo": ["são paulo", "sao paulo", "sp"],
            "rio_janeiro": ["rio de janeiro", "rj"],
            "minas_gerais": ["minas gerais", "mg"],
            "bahia": ["bahia", "ba"],
            "parana": ["paraná", "parana", "pr"],
            "rio_grande_sul": ["rio grande do sul", "rs"],
            "pernambuco": ["pernambuco", "pe"],
            "ceara": ["ceará", "ceara", "ce"],
            "santa_catarina": ["santa catarina", "sc"],
            "goias": ["goiás", "goias", "go"],
            "distrito_federal_br": ["distrito federal", "df", "brasília"],
        },
        "ciudades": {
            "sao_paulo_cidade": ["são paulo", "sao paulo", "sp", "sampa"],
            "rio_de_janeiro": ["rio de janeiro", "rio", "rj"],
            "brasilia": ["brasília", "brasilia", "bsb"],
            "salvador": ["salvador"],
            "fortaleza": ["fortaleza"],
            "belo_horizonte": ["belo horizonte", "bh"],
            "manaus": ["manaus"],
            "curitiba": ["curitiba"],
            "recife": ["recife"],
            "porto_alegre": ["porto alegre", "poa"],
            "florianopolis": ["florianópolis", "florianopolis", "floripa"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CANADÁ
    # ═══════════════════════════════════════════════════════════════════════════
    "canada": {
        "provincias": {
            "ontario": ["ontario", "on"],
            "quebec": ["quebec", "québec", "qc"],
            "british_columbia": ["british columbia", "bc"],
            "alberta": ["alberta", "ab"],
            "manitoba": ["manitoba", "mb"],
            "saskatchewan": ["saskatchewan", "sk"],
            "nova_scotia": ["nova scotia", "ns"],
            "new_brunswick": ["new brunswick", "nb"],
        },
        "ciudades": {
            "toronto": ["toronto"],
            "montreal": ["montreal", "montréal"],
            "vancouver_ca": ["vancouver"],
            "calgary": ["calgary"],
            "edmonton": ["edmonton"],
            "ottawa": ["ottawa"],
            "winnipeg": ["winnipeg"],
            "quebec_city": ["quebec city", "québec"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PORTUGAL
    # ═══════════════════════════════════════════════════════════════════════════
    "portugal": {
        "distritos": {
            "lisboa": ["lisboa", "lisbon"],
            "porto": ["porto", "oporto"],
            "braga": ["braga"],
            "setubal": ["setúbal", "setubal"],
            "coimbra": ["coimbra"],
            "faro": ["faro"],
            "aveiro": ["aveiro"],
            "leiria": ["leiria"],
            "madeira": ["madeira"],
            "acores": ["açores", "acores", "azores"],
        },
        "ciudades": {
            "lisboa_cidade": ["lisboa", "lisbon"],
            "porto_cidade": ["porto", "oporto"],
            "braga_cidade": ["braga"],
            "coimbra_cidade": ["coimbra"],
            "funchal": ["funchal"],
            "faro_cidade": ["faro"],
            "cascais": ["cascais"],
            "sintra": ["sintra"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ITALIA
    # ═══════════════════════════════════════════════════════════════════════════
    "italia": {
        "regiones": {
            "lombardia": ["lombardia", "lombardía"],
            "lazio": ["lazio", "lacio"],
            "campania": ["campania"],
            "sicilia": ["sicilia", "sicily"],
            "veneto": ["veneto", "véneto"],
            "piemonte": ["piemonte", "piamonte"],
            "emilia_romagna": ["emilia-romagna", "emilia romagna"],
            "toscana": ["toscana", "tuscany"],
            "puglia": ["puglia", "apulia"],
            "sardegna": ["sardegna", "cerdeña"],
        },
        "ciudades": {
            "roma": ["roma", "rome"],
            "milano": ["milano", "milán", "milan"],
            "napoli": ["napoli", "nápoles", "naples"],
            "torino": ["torino", "turín"],
            "palermo": ["palermo"],
            "genova": ["genova", "génova"],
            "bologna": ["bologna", "bolonia"],
            "firenze": ["firenze", "florencia", "florence"],
            "venezia": ["venezia", "venecia", "venice"],
            "verona": ["verona"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # FRANCIA
    # ═══════════════════════════════════════════════════════════════════════════
    "francia": {
        "regiones": {
            "ile_de_france": ["île-de-france", "ile de france"],
            "provence": ["provence-alpes-côte d'azur", "provence", "paca"],
            "auvergne": ["auvergne-rhône-alpes"],
            "occitanie": ["occitanie", "occitania"],
            "nouvelle_aquitaine": ["nouvelle-aquitaine"],
            "bretagne": ["bretagne", "bretaña"],
            "normandie": ["normandie", "normandía"],
            "hauts_de_france": ["hauts-de-france"],
        },
        "ciudades": {
            "paris": ["paris", "parís"],
            "marseille": ["marseille", "marsella"],
            "lyon": ["lyon"],
            "toulouse": ["toulouse"],
            "nice": ["nice", "niza"],
            "nantes": ["nantes"],
            "strasbourg": ["strasbourg", "estrasburgo"],
            "bordeaux": ["bordeaux", "burdeos"],
            "lille": ["lille"],
            "montpellier": ["montpellier"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ALEMANIA
    # ═══════════════════════════════════════════════════════════════════════════
    "alemania": {
        "estados": {
            "bayern": ["bayern", "baviera", "bavaria"],
            "nordrhein_westfalen": ["nordrhein-westfalen", "nrw"],
            "baden_wurttemberg": ["baden-württemberg"],
            "niedersachsen": ["niedersachsen", "baja sajonia"],
            "hessen": ["hessen", "hesse"],
            "sachsen": ["sachsen", "sajonia"],
            "berlin": ["berlin", "berlín"],
            "hamburg": ["hamburg", "hamburgo"],
        },
        "ciudades": {
            "berlin_ciudad": ["berlin", "berlín"],
            "hamburg_ciudad": ["hamburg", "hamburgo"],
            "munchen": ["münchen", "munich", "múnich"],
            "koln": ["köln", "cologne", "colonia"],
            "frankfurt": ["frankfurt"],
            "stuttgart": ["stuttgart"],
            "dusseldorf": ["düsseldorf"],
            "leipzig": ["leipzig"],
            "dortmund": ["dortmund"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # REINO UNIDO
    # ═══════════════════════════════════════════════════════════════════════════
    "reino_unido": {
        "naciones": {
            "england": ["england", "inglaterra"],
            "scotland": ["scotland", "escocia"],
            "wales": ["wales", "gales"],
            "northern_ireland": ["northern ireland", "irlanda del norte"],
        },
        "ciudades": {
            "london_ciudad": ["london", "londres"],
            "birmingham": ["birmingham"],
            "manchester": ["manchester"],
            "glasgow": ["glasgow"],
            "liverpool": ["liverpool"],
            "leeds": ["leeds"],
            "edinburgh": ["edinburgh", "edimburgo"],
            "bristol": ["bristol"],
            "cardiff": ["cardiff"],
            "belfast": ["belfast"],
            "oxford": ["oxford"],
            "cambridge": ["cambridge"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PAÍSES BAJOS
    # ═══════════════════════════════════════════════════════════════════════════
    "paises_bajos": {
        "provincias": {
            "noord_holland": ["noord-holland", "holanda septentrional"],
            "zuid_holland": ["zuid-holland", "holanda meridional"],
            "utrecht": ["utrecht"],
            "noord_brabant": ["noord-brabant"],
            "gelderland": ["gelderland"],
            "limburg_nl": ["limburg"],
        },
        "ciudades": {
            "amsterdam": ["amsterdam", "ámsterdam"],
            "rotterdam": ["rotterdam"],
            "den_haag": ["den haag", "the hague", "la haya"],
            "utrecht_ciudad": ["utrecht"],
            "eindhoven": ["eindhoven"],
            "tilburg": ["tilburg"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BÉLGICA
    # ═══════════════════════════════════════════════════════════════════════════
    "belgica": {
        "provincias": {
            "antwerpen": ["antwerpen", "amberes"],
            "bruselas": ["bruxelles", "brussels", "bruselas"],
            "flandes_oriental": ["oost-vlaanderen"],
            "flandes_occidental": ["west-vlaanderen"],
            "liege": ["liège", "lieja"],
        },
        "ciudades": {
            "bruselas_ciudad": ["bruxelles", "brussels", "bruselas"],
            "antwerpen_ciudad": ["antwerpen", "amberes"],
            "gent": ["gent", "gante", "ghent"],
            "brugge": ["brugge", "brujas", "bruges"],
            "liege_ciudad": ["liège", "lieja"],
            "leuven": ["leuven", "lovaina"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # SUIZA
    # ═══════════════════════════════════════════════════════════════════════════
    "suiza": {
        "cantones": {
            "zurich": ["zürich", "zurich", "zúrich"],
            "berna": ["bern", "berne", "berna"],
            "ginebra": ["genève", "geneva", "ginebra"],
            "vaud": ["vaud"],
            "ticino": ["ticino", "tesino"],
            "basilea": ["basel", "basilea"],
        },
        "ciudades": {
            "zurich_ciudad": ["zürich", "zurich"],
            "ginebra_ciudad": ["genève", "geneva", "ginebra"],
            "basilea_ciudad": ["basel", "basilea"],
            "lausana": ["lausanne", "lausana"],
            "berna_ciudad": ["bern", "berna"],
            "lugano": ["lugano"],
            "zermatt": ["zermatt"],
            "interlaken": ["interlaken"],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # AUSTRIA
    # ═══════════════════════════════════════════════════════════════════════════
    "austria": {
        "estados": {
            "viena": ["wien", "vienna", "viena"],
            "salzburgo": ["salzburg", "salzburgo"],
            "tirol": ["tirol", "tyrol"],
            "estiria": ["steiermark", "styria", "estiria"],
            "alta_austria": ["oberösterreich", "upper austria"],
            "baja_austria": ["niederösterreich", "lower austria"],
        },
        "ciudades": {
            "viena_ciudad": ["wien", "vienna", "viena"],
            "graz": ["graz"],
            "linz": ["linz"],
            "salzburgo_ciudad": ["salzburg", "salzburgo"],
            "innsbruck": ["innsbruck"],
            "klagenfurt": ["klagenfurt"],
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UBICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
def obtener_variantes_ubicacion(ubicacion: str) -> list:
    """
    Dado un nombre de ubicación, retorna todas sus variantes.
    Busca en países, provincias/estados y ciudades.
    Itera sobre TODOS los países del diccionario.
    """
    if not ubicacion:
        return []

    ubicacion_lower = ubicacion.lower().strip()
    variantes = [ubicacion_lower]

    # ═══════════════════════════════════════════════════════════════════
    # Buscar en lista de países
    # ═══════════════════════════════════════════════════════════════════
    paises_dict = UBICACIONES_VARIANTES.get("paises", {})
    for pais, lista in paises_dict.items():
        if ubicacion_lower in [v.lower() for v in lista]:
            variantes.extend([v.lower() for v in lista])
            return list(set(variantes))

    # ═══════════════════════════════════════════════════════════════════
    # Buscar en TODOS los países del diccionario
    # ═══════════════════════════════════════════════════════════════════
    for pais_key, pais_data in UBICACIONES_VARIANTES.items():
        # Saltar la clave "paises"
        if pais_key == "paises":
            continue
        if not isinstance(pais_data, dict):
            continue

        # Buscar en subdivisiones (provincias, estados, etc)
        for subdiv_key in [
                "provincias", "estados", "comunidades", "departamentos",
                "regiones", "distritos", "cantones", "naciones"
        ]:
            subdiv = pais_data.get(subdiv_key, {})
            if not isinstance(subdiv, dict):
                continue
            for nombre, lista in subdiv.items():
                if not isinstance(lista, list):
                    continue
                if ubicacion_lower in [v.lower() for v in lista]:
                    variantes.extend([v.lower() for v in lista])
                    return list(set(variantes))

        # Buscar en ciudades
        ciudades = pais_data.get("ciudades", {})
        if isinstance(ciudades, dict):
            for nombre, lista in ciudades.items():
                if not isinstance(lista, list):
                    continue
                if ubicacion_lower in [v.lower() for v in lista]:
                    variantes.extend([v.lower() for v in lista])
                    return list(set(variantes))

    return variantes


def ubicacion_en_texto(ubicacion: str, texto: str) -> bool:
    """
    Verifica si alguna variante de la ubicación está en el texto.
    """
    if not ubicacion or not texto:
        return False

    texto_lower = texto.lower()
    variantes = obtener_variantes_ubicacion(ubicacion)

    for v in variantes:
        if v in texto_lower:
            return True

    return False


def es_url_valida_noticia(url: str, texto: str, empresa: str) -> bool:
    """Valida si una URL es una noticia real y relevante."""
    url_lower = url.lower()
    texto_lower = texto.lower()
    empresa_lower = empresa.lower()

    if url_lower.endswith('.pdf'):
        return False

    dominios_basura = [
        # Académicos/documentos
        'pdfcoffee',
        'scribd',
        'academia.edu',
        'slideshare',
        'coursehero',
        'repositorio',
        'bitstream',
        'handle/',
        'thesis',
        'tesis',
        # Gobierno/legal
        'icj-cij.org',
        'cancilleria.gob',
        'boletinoficial',
        'sidof.segob.gob',
        'segob.gob.mx',
        # Ecommerce/spam
        'cityfilespress',
        'amazon.com',
        'mercadolibre',
        'aliexpress',
        'ebay.com',
        'alibaba.com',
        'wish.com',
        'shopee',
        'olx.com',
        'craiglist',
        'segundamano',
        'vibbo',
        # Redes sociales (NO son noticias)
        'linkedin.com',
        'facebook.com',
        'instagram.com',
        'twitter.com',
        'x.com',
        'youtube.com',
        'tiktok.com',
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


def calcular_peso_linkedin(url: str,
                           texto: str,
                           primer_nombre: str,
                           apellido: str,
                           empresa: str = "",
                           provincia: str = "",
                           ciudad: str = "",
                           pais: str = "") -> int:
    """
    Calcula el peso de un perfil de LinkedIn.

    VALIDACIÓN ESTRICTA EN URL SLUG:
    - Nombre Y Apellido DEBEN estar en el SLUG de la URL
    - Si no están ambos en el slug → retorna 0 (descartar)
    - Empresa/ubicación: bonus en texto (no obligatorio)

    PESO MÁXIMO 100:
    - Nombre en slug (obligatorio): 40 puntos
    - Apellido en slug (obligatorio): 40 puntos
    - Empresa en texto: 10 puntos
    - Ubicación en texto: 10 puntos
    """
    url_lower = url.lower()
    texto_lower = texto.lower()

    # ═══════════════════════════════════════════════════════════════════
    # EXTRAER SLUG DE LA URL - ESTO ES LO ÚNICO QUE IMPORTA
    # ═══════════════════════════════════════════════════════════════════
    slug = ""
    if "/in/" in url_lower:
        slug = url_lower.split("/in/")[1].split("/")[0].split("?")[0]
    slug_clean = slug.replace("-", " ").replace("_", " ")

    # ═══════════════════════════════════════════════════════════════════
    # CRÍTICO: Validar nombre y apellido SOLO en el SLUG
    # NO usar texto del snippet - solo la URL
    # ═══════════════════════════════════════════════════════════════════
    primer_lower = primer_nombre.lower().strip()
    apellido_lower = apellido.lower().strip()
    empresa_lower = empresa.lower().strip() if empresa else ""

    peso = 0
    tiene_nombre = False
    tiene_apellido = False

    # ═══════════════════════════════════════════════════════════════════
    # VERIFICACIÓN DE NOMBRE EN SLUG (40 puntos)
    # ═══════════════════════════════════════════════════════════════════
    if primer_lower and len(primer_lower) > 1:
        if primer_lower in slug_clean:
            peso += 40
            tiene_nombre = True

    # ═══════════════════════════════════════════════════════════════════
    # VERIFICACIÓN DE APELLIDO EN SLUG (40 puntos)
    # ═══════════════════════════════════════════════════════════════════
    if apellido_lower and len(apellido_lower) > 1:
        if apellido_lower in slug_clean:
            peso += 40
            tiene_apellido = True

    # ═══════════════════════════════════════════════════════════════════
    # CRÍTICO: Si no tiene AMBOS en el SLUG, DESCARTAR
    # Esto evita falsos positivos como jose-filippini o samuel-rodriguez
    # cuando buscamos rafael-driuzzi
    # ═══════════════════════════════════════════════════════════════════
    if not (tiene_nombre and tiene_apellido):
        return 0

    # ═══════════════════════════════════════════════════════════════════
    # BONUS: Empresa en TEXTO (no slug) - 10 puntos máximo
    # ═══════════════════════════════════════════════════════════════════
    if empresa_lower and len(empresa_lower) > 2:
        palabras_empresa = [p for p in empresa_lower.split() if len(p) > 2]
        if empresa_lower in texto_lower:
            peso += 10
        elif any(p in texto_lower for p in palabras_empresa):
            peso += 5

    # ═══════════════════════════════════════════════════════════════════
    # BONUS: Ubicación en TEXTO (no slug) - 10 puntos máximo
    # ═══════════════════════════════════════════════════════════════════
    puntos_ubicacion = 0

    if provincia and ubicacion_en_texto(provincia, texto_lower):
        puntos_ubicacion += 5

    if ciudad and ubicacion_en_texto(ciudad, texto_lower):
        puntos_ubicacion += 5

    if pais and puntos_ubicacion == 0:
        if ubicacion_en_texto(pais, texto_lower):
            puntos_ubicacion += 3

    peso += min(puntos_ubicacion, 10)

    # ═══════════════════════════════════════════════════════════════════
    # PENALIZACIÓN: LinkedIn de país diferente al del lead
    # Subdominios como py.linkedin.com, pe.linkedin.com, mx.linkedin.com
    # indican que el perfil está registrado en otro país
    # ═══════════════════════════════════════════════════════════════════
    # Diccionario COMPLETO de subdominios LinkedIn → país
    # Cubre todos los países donde LinkedIn tiene subdominio local
    SUBDOMINIO_A_PAIS = {
        # América Latina
        'ar': 'argentina',
        'bo': 'bolivia',
        'br': 'brasil',
        'cl': 'chile',
        'co': 'colombia',
        'cr': 'costa rica',
        'cu': 'cuba',
        'do': 'dominicana',
        'ec': 'ecuador',
        'sv': 'el salvador',
        'gt': 'guatemala',
        'hn': 'honduras',
        'mx': 'mexico',
        'ni': 'nicaragua',
        'pa': 'panama',
        'py': 'paraguay',
        'pe': 'peru',
        'pr': 'puerto rico',
        'uy': 'uruguay',
        've': 'venezuela',
        # América del Norte
        'us': 'estados unidos',
        'ca': 'canada',
        # Europa Occidental
        'es': 'españa',
        'pt': 'portugal',
        'fr': 'francia',
        'it': 'italia',
        'de': 'alemania',
        'at': 'austria',
        'ch': 'suiza',
        'be': 'belgica',
        'nl': 'holanda',
        'lu': 'luxemburgo',
        'uk': 'reino unido',
        'ie': 'irlanda',
        'dk': 'dinamarca',
        'se': 'suecia',
        'no': 'noruega',
        'fi': 'finlandia',
        'is': 'islandia',
        # Europa del Sur
        'gr': 'grecia',
        'mt': 'malta',
        'cy': 'chipre',
        # Europa del Este
        'pl': 'polonia',
        'cz': 'republica checa',
        'sk': 'eslovaquia',
        'hu': 'hungria',
        'ro': 'rumania',
        'bg': 'bulgaria',
        'hr': 'croacia',
        'si': 'eslovenia',
        'rs': 'serbia',
        'ba': 'bosnia',
        'me': 'montenegro',
        'mk': 'macedonia',
        'al': 'albania',
        'xk': 'kosovo',
        'ua': 'ucrania',
        'by': 'bielorrusia',
        'md': 'moldavia',
        'ee': 'estonia',
        'lv': 'letonia',
        'lt': 'lituania',
        'ru': 'rusia',
        # Asia
        'cn': 'china',
        'jp': 'japon',
        'kr': 'corea del sur',
        'kp': 'corea del norte',
        'tw': 'taiwan',
        'hk': 'hong kong',
        'mo': 'macao',
        'mn': 'mongolia',
        'in': 'india',
        'pk': 'pakistan',
        'bd': 'bangladesh',
        'lk': 'sri lanka',
        'np': 'nepal',
        'bt': 'butan',
        'mm': 'myanmar',
        'th': 'tailandia',
        'vn': 'vietnam',
        'kh': 'camboya',
        'la': 'laos',
        'my': 'malasia',
        'sg': 'singapur',
        'id': 'indonesia',
        'ph': 'filipinas',
        'bn': 'brunei',
        'tl': 'timor oriental',
        # Asia Central y Medio Oriente
        'kz': 'kazajstan',
        'uz': 'uzbekistan',
        'tm': 'turkmenistan',
        'kg': 'kirguistan',
        'tj': 'tayikistan',
        'af': 'afganistan',
        'ir': 'iran',
        'iq': 'irak',
        'sa': 'arabia saudita',
        'ae': 'emiratos arabes',
        'qa': 'qatar',
        'kw': 'kuwait',
        'bh': 'bahrein',
        'om': 'oman',
        'ye': 'yemen',
        'jo': 'jordania',
        'lb': 'libano',
        'sy': 'siria',
        'il': 'israel',
        'ps': 'palestina',
        'tr': 'turquia',
        'ge': 'georgia',
        'am': 'armenia',
        'az': 'azerbaiyan',
        # África
        'za': 'sudafrica',
        'eg': 'egipto',
        'ma': 'marruecos',
        'dz': 'argelia',
        'tn': 'tunez',
        'ly': 'libia',
        'ng': 'nigeria',
        'gh': 'ghana',
        'ke': 'kenia',
        'tz': 'tanzania',
        'ug': 'uganda',
        'rw': 'ruanda',
        'et': 'etiopia',
        'sd': 'sudan',
        'ao': 'angola',
        'mz': 'mozambique',
        'zw': 'zimbabwe',
        'bw': 'botsuana',
        'na': 'namibia',
        'zm': 'zambia',
        'mw': 'malawi',
        'mg': 'madagascar',
        'mu': 'mauricio',
        'sn': 'senegal',
        'ci': 'costa de marfil',
        'cm': 'camerun',
        'cd': 'congo',
        'cg': 'congo brazzaville',
        'ga': 'gabon',
        # Oceanía
        'au': 'australia',
        'nz': 'nueva zelanda',
        'fj': 'fiyi',
        'pg': 'papua nueva guinea',
        # Caribe
        'jm': 'jamaica',
        'tt': 'trinidad y tobago',
        'bb': 'barbados',
        'bs': 'bahamas',
        'ht': 'haiti',
        'gy': 'guyana',
        'sr': 'surinam',
        'bz': 'belice',
    }
    
    # Detectar subdominio del LinkedIn
    subdominio_linkedin = None
    url_lower = url.lower()
    match_subdominio = re.match(
        r'https?://([a-z]{2})\.linkedin\.com', 
        url_lower
    )
    if match_subdominio:
        subdominio_linkedin = match_subdominio.group(1)
    
    # Si el perfil tiene subdominio de otro país, penalizar
    if subdominio_linkedin and pais:
        pais_lower = pais.lower().strip()
        pais_del_subdominio = SUBDOMINIO_A_PAIS.get(
            subdominio_linkedin, ''
        )
        
        # Verificar si el país del subdominio NO coincide con el país del lead
        if pais_del_subdominio and pais_del_subdominio != pais_lower:
            # Verificar también variantes del país
            variantes_pais = [pais_lower]
            if pais_lower == 'argentina':
                variantes_pais.extend(['ar', 'arg'])
            elif pais_lower == 'brasil' or pais_lower == 'brazil':
                variantes_pais.extend(['br', 'bra', 'brasil', 'brazil'])
            elif pais_lower == 'mexico' or pais_lower == 'méxico':
                variantes_pais.extend(['mx', 'mex', 'mexico', 'méxico'])
            elif pais_lower == 'españa' or pais_lower == 'espana':
                variantes_pais.extend(['es', 'esp', 'españa', 'espana'])
            
            if pais_del_subdominio not in variantes_pais:
                # Penalización fuerte: -30 puntos
                peso -= 30
                logger.debug(
                    f"[LINKEDIN] Penalización -30 por país diferente: "
                    f"subdominio={subdominio_linkedin} "
                    f"({pais_del_subdominio}), lead={pais_lower}"
                )

    return peso


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
        # FUNCIÓN AUXILIAR: Búsqueda de LinkedIn Personal
        # ═══════════════════════════════════════════════════════════════
        async def _buscar_linkedin_personal():
            """Encapsula toda la búsqueda de LinkedIn personal."""
            candidatos = []
            primer_nombre_b = results["primer_nombre"]
            apellido_b = results["apellido"]
            
            # 3A: BUSCAR EN WEB DEL CLIENTE
            if tiene_website:
                logger.info(f"[LINKEDIN] PASO 3A: Buscando en web...")
                try:
                    paginas = [
                        f"https://{website_limpio}",
                        f"https://{website_limpio}/nosotros",
                        f"https://{website_limpio}/about",
                        f"https://{website_limpio}/equipo",
                    ]
                    contenido_web = ""
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        for pagina in paginas[:4]:
                            try:
                                resp = await client.get(
                                    pagina,
                                    headers={"User-Agent": "Mozilla/5.0"},
                                    follow_redirects=True)
                                if resp.status_code == 200:
                                    contenido_web += resp.text + "\n"
                            except:
                                continue
                    
                    if contenido_web:
                        pattern = (r'https?://(?:www\.)?(?:ar\.)?'
                                   r'linkedin\.com/in/([a-zA-Z0-9_~-]+)')
                        matches = re.findall(
                            pattern, contenido_web, re.IGNORECASE)
                        for slug in matches:
                            if slug.lower() in ['company', 'jobs', 'pulse']:
                                continue
                            url = f"https://linkedin.com/in/{slug}"
                            peso = calcular_peso_linkedin(
                                url=url,
                                texto=contenido_web,
                                primer_nombre=primer_nombre_b,
                                apellido=apellido_b,
                                empresa=empresa_busqueda,
                                provincia=province,
                                ciudad=city)
                            if peso >= 60:
                                ya_existe = any(
                                    c["url"] == url for c in candidatos)
                                if not ya_existe:
                                    candidatos.append({
                                        "url": url,
                                        "peso": peso,
                                        "source": "web_cliente"
                                    })
                                    logger.info(
                                        f"[LINKEDIN-WEB] ✓ {url} "
                                        f"(peso: {peso})")
                except Exception as e:
                    logger.warning(f"[LINKEDIN-WEB] Error: {e}")
            
            # 3B: BUSCAR POR EMAIL
            if email_contacto and email_contacto != "No encontrado":
                logger.info(f"[LINKEDIN] PASO 3B: Buscando por email...")
                linkedin_email = await buscar_linkedin_por_email(
                    email_contacto)
                if linkedin_email:
                    peso = calcular_peso_linkedin(
                        url=linkedin_email,
                        texto=email_contacto,
                        primer_nombre=primer_nombre_b,
                        apellido=apellido_b,
                        empresa=empresa_busqueda,
                        provincia=province,
                        ciudad=city)
                    if peso >= 60:
                        ya_existe = any(
                            c["url"] == linkedin_email for c in candidatos)
                        if not ya_existe:
                            candidatos.append({
                                "url": linkedin_email,
                                "peso": peso,
                                "source": "email"
                            })
                            logger.info(
                                f"[LINKEDIN-EMAIL] ✓ {linkedin_email} "
                                f"(peso: {peso})")
            
            # 3C-3D: BUSCAR CON TAVILY + GOOGLE (ya paralelizado)
            linkedin_tavily_result = None
            linkedin_google_result = None
            tasks = []
            
            if TAVILY_API_KEY:
                tasks.append(("tavily", tavily_buscar_linkedin_personal(
                    results["nombre"], empresa_busqueda, primer_nombre_b,
                    apellido_b, ubicacion_completa, city, province, 
                    country)))
            
            if GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
                tasks.append(("google", google_buscar_linkedin_personal(
                    results["nombre"], empresa_busqueda, primer_nombre_b,
                    apellido_b, 0, ubicacion_completa, city, province,
                    country)))
            
            if tasks:
                logger.info(
                    "[LINKEDIN] Ejecutando búsquedas en paralelo: "
                    "Tavily + Google")
                coroutines = [task[1] for task in tasks]
                results_parallel = await asyncio.gather(
                    *coroutines, return_exceptions=True)
                
                for i, (source, _) in enumerate(tasks):
                    result = results_parallel[i]
                    if isinstance(result, Exception):
                        logger.error(
                            f"[LINKEDIN-{source.upper()}] Error: {result}")
                        continue
                    if source == "tavily":
                        linkedin_tavily_result = result
                    elif source == "google":
                        linkedin_google_result = result
                
                logger.info(
                    f"[LINKEDIN] Paralelización completada: "
                    f"Tavily={'✅' if linkedin_tavily_result else '❌'}, "
                    f"Google={'✅' if linkedin_google_result else '❌'}")
            
            # Procesar Tavily
            if linkedin_tavily_result:
                urls_tavily = linkedin_tavily_result.get("url", "")
                for url in urls_tavily.split(" | "):
                    url = url.strip()
                    if not url or url == "No encontrado":
                        continue
                    peso = calcular_peso_linkedin(
                        url=url,
                        texto=f"{results['nombre']} {empresa_busqueda}",
                        primer_nombre=primer_nombre_b,
                        apellido=apellido_b,
                        empresa=empresa_busqueda,
                        provincia=province,
                        ciudad=city)
                    if peso >= 60:
                        ya_existe = any(c["url"] == url for c in candidatos)
                        if not ya_existe:
                            candidatos.append({
                                "url": url,
                                "peso": peso,
                                "source": "tavily"
                            })
                            logger.info(
                                f"[LINKEDIN-TAVILY] ✓ {url} (peso: {peso})")
            
            # Procesar Google
            if linkedin_google_result:
                url_google = linkedin_google_result.get("url", "")
                if url_google and url_google != "No encontrado":
                    # Google puede devolver múltiples URLs separadas por |
                    for url in url_google.split(" | "):
                        url = url.strip()
                        if not url:
                            continue
                        peso = linkedin_google_result.get("confianza", 0)
                        # Si no tiene confianza, calcular peso
                        if peso == 0:
                            peso = calcular_peso_linkedin(
                                url=url,
                                texto=f"{results['nombre']} {empresa_busqueda}",
                                primer_nombre=primer_nombre_b,
                                apellido=apellido_b,
                                empresa=empresa_busqueda,
                                provincia=province,
                                ciudad=city)
                        ya_existe = any(c["url"] == url for c in candidatos)
                        if not ya_existe and peso >= 60:
                            candidatos.append({
                                "url": url,
                                "peso": peso,
                                "source": "google"
                            })
                            logger.info(
                                f"[LINKEDIN-GOOGLE] ✓ {url} (peso: {peso})")
            
            # 3E: BUSCAR POR CARGO (CEO/fundador)
            if len(candidatos) < 2:
                logger.info(f"[LINKEDIN] PASO 3E: Buscando por cargo...")
                por_cargo = await buscar_linkedin_por_cargo(
                    empresa=empresa_busqueda, ubicacion=ubicacion_completa)
                for url in por_cargo:
                    peso = calcular_peso_linkedin(
                        url=url,
                        texto=f"{empresa_busqueda} {ubicacion_completa}",
                        primer_nombre=primer_nombre_b,
                        apellido=apellido_b,
                        empresa=empresa_busqueda,
                        provincia=province,
                        ciudad=city)
                    if peso >= 60:
                        ya_existe = any(c["url"] == url for c in candidatos)
                        if not ya_existe:
                            candidatos.append({
                                "url": url,
                                "peso": peso,
                                "source": "cargo"
                            })
                            logger.info(
                                f"[LINKEDIN-CARGO] ✓ {url} (peso: {peso})")
            
            return candidatos
        
        # ═══════════════════════════════════════════════════════════════
        # FUNCIÓN AUXILIAR: Búsqueda de Noticias
        # ═══════════════════════════════════════════════════════════════
        async def _buscar_noticias():
            """Encapsula toda la búsqueda de noticias."""
            noticias = []
            noticias_tasks = []
            task_sources = []
            
            if GOOGLE_API_KEY and GOOGLE_SEARCH_CX:
                noticias_tasks.append(google_buscar_noticias(
                    empresa, empresa_busqueda, ubicacion_query))
                task_sources.append("google")
            
            if APIFY_API_TOKEN:
                async def apify_with_timeout():
                    try:
                        return await asyncio.wait_for(
                            apify_buscar_noticias(
                                empresa_busqueda, ubicacion_query),
                            timeout=30.0)
                    except asyncio.TimeoutError:
                        logger.warning("[NOTICIAS-APIFY] Timeout")
                        return []
                
                noticias_tasks.append(apify_with_timeout())
                task_sources.append("apify")
            
            source_used = "ninguno"
            
            if noticias_tasks:
                logger.info(
                    "[NOTICIAS] Ejecutando búsquedas en paralelo: "
                    "Google + Apify")
                noticias_results = await asyncio.gather(
                    *noticias_tasks, return_exceptions=True)
                
                for i, source in enumerate(task_sources):
                    result = noticias_results[i]
                    if isinstance(result, Exception):
                        logger.error(
                            f"[NOTICIAS-{source.upper()}] Error: {result}")
                        continue
                    if result and not noticias:
                        noticias = result
                        source_used = source
                        logger.info(
                            f"[NOTICIAS-{source.upper()}] "
                            f"✓ {len(noticias)} noticias")
            
            return {"noticias": noticias, "source": source_used}

        # ═══════════════════════════════════════════════════════════════
        # PASO 3+5: LINKEDIN Y NOTICIAS EN PARALELO
        # ═══════════════════════════════════════════════════════════════
        logger.info(
            "[RESEARCH] Ejecutando LinkedIn + Noticias en PARALELO...")
        
        # Ejecutar ambas búsquedas simultáneamente
        linkedin_task = _buscar_linkedin_personal()
        noticias_task = _buscar_noticias()
        
        linkedin_result, noticias_result = await asyncio.gather(
            linkedin_task,
            noticias_task,
            return_exceptions=True
        )
        
        # Procesar resultado de LinkedIn
        if isinstance(linkedin_result, Exception):
            logger.error(f"[LINKEDIN] Error: {linkedin_result}")
            candidatos_linkedin = []
        else:
            candidatos_linkedin = linkedin_result or []

        # Seleccionar mejor candidato LinkedIn
        if candidatos_linkedin:
            validos = [c for c in candidatos_linkedin if c["peso"] >= 60]
            if validos:
                validos.sort(key=lambda x: x["peso"], reverse=True)
                mejor = validos[0]
                # Formato: múltiples URLs separadas por \n
                urls_finales = [c["url"] for c in validos[:5]]
                results["linkedin_personal"] = "\n".join(urls_finales)
                results["linkedin_personal_confianza"] = mejor["peso"]
                results["linkedin_personal_source"] = mejor["source"]
                logger.info(
                    f"[LINKEDIN] ✓ Mejor: {mejor['url']} "
                    f"(peso: {mejor['peso']}, source: {mejor['source']})")
                
                # Log de candidatos
                logger.info(f"[LINKEDIN] ✓ {len(validos)} perfiles encontrados")
                for c in validos[:5]:
                    logger.info(
                        f"  - {c['url']} (peso: {c['peso']}, "
                        f"source: {c['source']})")
            else:
                logger.info("[LINKEDIN] ✗ Ningún candidato con peso >= 60")
        else:
            logger.info("[LINKEDIN] ✗ No se encontraron candidatos")
        
        # Procesar resultado de Noticias
        if isinstance(noticias_result, Exception):
            logger.error(f"[NOTICIAS] Error: {noticias_result}")
        elif noticias_result:
            noticias = noticias_result.get("noticias", [])
            results["noticias_source"] = noticias_result.get(
                "source", "ninguno")
            
            if noticias:
                results["noticias_lista"] = noticias
                results["noticias_count"] = len(noticias)
                
                noticias_texto = []
                for n in noticias[:10]:
                    titulo = n.get("titulo", "Sin título")
                    url = n.get("url", "")
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
        
        logger.info(
            f"[RESEARCH] Paralelización completada: "
            f"LinkedIn={'✅' if results['linkedin_personal'] != 'No encontrado' else '❌'}, "
            f"Noticias={'✅' if results.get('noticias_count', 0) > 0 else '❌'}")

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


async def buscar_linkedin_por_cargo(empresa: str,
                                    ubicacion: str = "",
                                    cargos: list = None) -> list:
    """
    Busca LinkedIn de fundadores/CEO/directores de una empresa.
    Retorna lista de URLs encontradas.
    """
    if not TAVILY_API_KEY:
        return []

    if cargos is None:
        cargos = [
            'fundador', 'founder', 'CEO', 'director', 'dueño', 'owner',
            'gerente general'
        ]

    resultados = []

    for cargo in cargos[:3]:  # Limitar a 3 cargos
        query = f'{cargo} "{empresa}" site:linkedin.com/in'
        if ubicacion:
            query = f'{cargo} "{empresa}" {ubicacion} site:linkedin.com/in'

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.tavily.com/search",
                                             json={
                                                 "api_key":
                                                 TAVILY_API_KEY,
                                                 "query":
                                                 query,
                                                 "search_depth":
                                                 "basic",
                                                 "include_domains":
                                                 ["linkedin.com"],
                                                 "max_results":
                                                 5
                                             })

                if response.status_code == 200:
                    data = response.json()
                    for r in data.get("results", []):
                        url = r.get("url", "")
                        if "linkedin.com/in/" in url and \
                           "/company/" not in url:
                            url_clean = url.split("?")[0]
                            if url_clean not in resultados:
                                resultados.append(url_clean)
                                logger.info(f"[CARGO] LinkedIn por {cargo}: "
                                            f"{url_clean}")
        except Exception as e:
            logger.error(f"[CARGO] Error buscando {cargo}: {e}")

    return resultados[:5]  # Máximo 5 resultados


async def buscar_linkedin_en_web(contenido_web: str,
                                 nombre: str = "",
                                 apellido: str = "") -> list:
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
            response = await client.post("https://api.tavily.com/search",
                                         json={
                                             "api_key": TAVILY_API_KEY,
                                             "query": query,
                                             "search_depth": "basic",
                                             "include_domains":
                                             ["linkedin.com"],
                                             "max_results": 3
                                         })

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
                tiene_primer_nombre = (primer_lower in texto
                                       or primer_lower in url_slug_clean)
                tiene_apellido = (apellido_lower in texto
                                  or apellido_lower in url_slug_clean)
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
                    # ═══════════════════════════════════════════════════════
                    # VALIDACIÓN ADICIONAL CON calcular_peso_linkedin
                    # Esto descarta perfiles donde nombre/apellido aparecen
                    # en el snippet pero NO corresponden a ESE perfil
                    # Ejemplo: descarta "Samuel Rodriguez" cuando buscamos
                    # "Rafael Driuzzi"
                    # ═══════════════════════════════════════════════════════
                    peso_verificacion = calcular_peso_linkedin(
                        url=url,
                        texto=texto,
                        primer_nombre=primer_lower,
                        apellido=apellido_lower,
                        empresa=empresa_lower,
                        provincia=province,
                        ciudad=city,
                        pais=country)

                    # Si peso < 60, significa que NO tiene nombre+apellido
                    # en la URL/texto de ESE perfil específico
                    if peso_verificacion < 60:
                        logger.info(f"[TAVILY] Descartado por peso: {url} "
                                    f"(peso: {peso_verificacion} < 60)")
                        continue

                    logger.info(f"[TAVILY] ✓ Candidato: {url} "
                                f"(score: {score}, peso: {peso_verificacion})")
                    candidatos.append({
                        "url": url.split("?")[0],
                        "confianza": min(score, 100),
                        "score": score,
                        "peso_slug": peso_verificacion,
                        "tiene_empresa": tiene_match_empresa
                    })

            candidatos.sort(key=lambda x: x["confianza"], reverse=True)

            if candidatos:
                # Devolver cada URL con su peso real (del slug)
                resultados = []
                for c in candidatos[:3]:
                    resultados.append({
                        "url": c["url"],
                        "confianza": c.get("peso_slug", c["confianza"])
                    })

                if len(resultados) == 1:
                    logger.info(f"[TAVILY] ✓ LinkedIn: {resultados[0]['url']}")
                    return resultados[0]
                else:
                    # Devolver URLs separadas, cada una con su confianza
                    urls_str = " | ".join([r["url"] for r in resultados])
                    # Guardar lista completa para re-validación
                    logger.info(
                        f"[TAVILY] ✓ LinkedIn múltiples: {len(resultados)}")
                    return {
                        "url": urls_str,
                        "confianza": resultados[0]["confianza"],
                        "urls_detalle": resultados
                    }

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
                tiene_primer_nombre = (primer_lower in texto
                                       or primer_lower in url_slug_clean)
                tiene_apellido = (apellido_lower in texto
                                  or apellido_lower in url_slug_clean)
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
                    # ═══════════════════════════════════════════════════════
                    # VALIDACIÓN ADICIONAL CON calcular_peso_linkedin
                    # ═══════════════════════════════════════════════════════
                    peso_verificacion = calcular_peso_linkedin(
                        url=link,
                        texto=texto,
                        primer_nombre=primer_lower,
                        apellido=apellido_lower,
                        empresa=empresa_lower,
                        provincia=province,
                        ciudad=city,
                        pais=country)

                    if peso_verificacion < 60:
                        logger.info(f"[GOOGLE] Descartado por peso: {link} "
                                    f"(peso: {peso_verificacion} < 60)")
                        continue

                    logger.info(f"[GOOGLE] ✓ Candidato: {link} "
                                f"(score: {score}, peso: {peso_verificacion})")
                    candidatos.append({
                        "url": link,
                        "score": score,
                        "peso_slug": peso_verificacion,
                        "tiene_empresa": tiene_match_empresa
                    })

            candidatos.sort(key=lambda x: x["score"], reverse=True)

            if candidatos:
                # Devolver cada URL con su peso real
                resultados = []
                for c in candidatos[:3]:
                    resultados.append({
                        "url": c["url"],
                        "confianza": c.get("peso_slug", c["score"])
                    })

                mejor = resultados[0]
                if mejor["confianza"] > confianza_actual:
                    if len(resultados) == 1:
                        logger.info(f"[GOOGLE] ✓ LinkedIn: {mejor['url']}")
                        return mejor
                    else:
                        # Devolver URLs separadas, cada una con su confianza
                        urls_str = " | ".join([r["url"] for r in resultados])
                        logger.info(
                            f"[GOOGLE] ✓ LinkedIn múltiples: {len(resultados)}")
                        return {
                            "url": urls_str,
                            "confianza": mejor["confianza"],
                            "urls_detalle": resultados
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
        # Usar query optimizada para noticias reales
        query = construir_query_noticias(empresa_busqueda, ubicacion_query)

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
                
                # Filtrar noticias basura (Softonic, Play Store, APK, etc.)
                if not es_noticia_valida(url, titulo):
                    logger.debug(f"[NOTICIAS] Descartado (basura): {url[:50]}...")
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
            dominio = empresa_busqueda.replace("https://", "").replace(
                "http://", "").replace("www.", "").split("/")[0]
            if "." in dominio:
                query_parts.append(f'OR "{dominio}"')

        # Usar query optimizada para noticias reales
        query = construir_query_noticias(empresa or empresa_busqueda, ubicacion_query)
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
                
                # Filtrar noticias basura (Softonic, Play Store, APK, etc.)
                # Validar que la empresa esté en el título
                if not es_noticia_valida(url, titulo, empresa or empresa_busqueda):
                    logger.debug(
                        f"[NOTICIAS] Descartado (no relevante): {titulo[:50]}..."
                    )
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