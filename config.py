"""
Configuración centralizada para DANIA/Fortia
"""
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================
# OPENAI
# ============================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# ============================================================
# MONGODB
# ============================================================
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "dania_fortia")
MONGODB_DATABASE = MONGODB_DB_NAME

# ============================================================
# WHATSAPP
# ============================================================
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get(
    "WHATSAPP_VERIFY_TOKEN", "fortia2024"
)

# ============================================================
# TAVILY (Búsqueda web)
# ============================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# ============================================================
# JINA AI (Extracción web)
# ============================================================
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")

# ============================================================
# FIRECRAWL (Extracción web avanzada)
# ============================================================
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# ============================================================
# APIFY (Crawler de noticias)
# ============================================================
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN", "")

# ============================================================
# GMAIL
# ============================================================
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NOTIFICATION_EMAIL = os.environ.get(
    "NOTIFICATION_EMAIL", "pansapablo@gmail.com"
)

# ============================================================
# CAL.COM
# ============================================================
CALCOM_API_KEY = os.environ.get("CALCOM_API_KEY", "")
CALCOM_EVENT_URL = os.environ.get(
    "CALCOM_EVENT_URL", 
    "https://cal.com/agencia-fortia-hviska/60min"
)

# ============================================================
# GOOGLE CUSTOM SEARCH (para LinkedIn)
# ============================================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_SEARCH_CX = os.environ.get(
    "GOOGLE_SEARCH_CX", "33f5cc1337cde4799"
)

# ============================================================
# MAPEO DE PAÍSES COMPLETO
# ============================================================
COUNTRY_MAP = {
    # LATAM
    '54': {
        'country': 'Argentina', 
        'timezone': 'America/Argentina/Buenos_Aires', 
        'utc': 'UTC-3', 
        'code': '+54', 
        'emoji': '🇦🇷'
    },
    '52': {
        'country': 'México', 
        'timezone': 'America/Mexico_City', 
        'utc': 'UTC-6', 
        'code': '+52', 
        'emoji': '🇲🇽'
    },
    '56': {
        'country': 'Chile', 
        'timezone': 'America/Santiago', 
        'utc': 'UTC-4', 
        'code': '+56', 
        'emoji': '🇨🇱'
    },
    '57': {
        'country': 'Colombia', 
        'timezone': 'America/Bogota', 
        'utc': 'UTC-5', 
        'code': '+57', 
        'emoji': '🇨🇴'
    },
    '51': {
        'country': 'Perú', 
        'timezone': 'America/Lima', 
        'utc': 'UTC-5', 
        'code': '+51', 
        'emoji': '🇵🇪'
    },
    '58': {
        'country': 'Venezuela', 
        'timezone': 'America/Caracas', 
        'utc': 'UTC-4', 
        'code': '+58', 
        'emoji': '🇻🇪'
    },
    '593': {
        'country': 'Ecuador', 
        'timezone': 'America/Guayaquil', 
        'utc': 'UTC-5', 
        'code': '+593', 
        'emoji': '🇪🇨'
    },
    '591': {
        'country': 'Bolivia', 
        'timezone': 'America/La_Paz', 
        'utc': 'UTC-4', 
        'code': '+591', 
        'emoji': '🇧🇴'
    },
    '595': {
        'country': 'Paraguay', 
        'timezone': 'America/Asuncion', 
        'utc': 'UTC-4', 
        'code': '+595', 
        'emoji': '🇵🇾'
    },
    '598': {
        'country': 'Uruguay', 
        'timezone': 'America/Montevideo', 
        'utc': 'UTC-3', 
        'code': '+598', 
        'emoji': '🇺🇾'
    },
    '502': {
        'country': 'Guatemala', 
        'timezone': 'America/Guatemala', 
        'utc': 'UTC-6', 
        'code': '+502', 
        'emoji': '🇬🇹'
    },
    '503': {
        'country': 'El Salvador', 
        'timezone': 'America/El_Salvador', 
        'utc': 'UTC-6', 
        'code': '+503', 
        'emoji': '🇸🇻'
    },
    '504': {
        'country': 'Honduras', 
        'timezone': 'America/Tegucigalpa', 
        'utc': 'UTC-6', 
        'code': '+504', 
        'emoji': '🇭🇳'
    },
    '505': {
        'country': 'Nicaragua', 
        'timezone': 'America/Managua', 
        'utc': 'UTC-6', 
        'code': '+505', 
        'emoji': '🇳🇮'
    },
    '506': {
        'country': 'Costa Rica', 
        'timezone': 'America/Costa_Rica', 
        'utc': 'UTC-6', 
        'code': '+506', 
        'emoji': '🇨🇷'
    },
    '507': {
        'country': 'Panamá', 
        'timezone': 'America/Panama', 
        'utc': 'UTC-5', 
        'code': '+507', 
        'emoji': '🇵🇦'
    },
    '53': {
        'country': 'Cuba', 
        'timezone': 'America/Havana', 
        'utc': 'UTC-5', 
        'code': '+53', 
        'emoji': '🇨🇺'
    },
    '1809': {
        'country': 'República Dominicana', 
        'timezone': 'America/Santo_Domingo', 
        'utc': 'UTC-4', 
        'code': '+1809', 
        'emoji': '🇩🇴'
    },
    '1829': {
        'country': 'República Dominicana', 
        'timezone': 'America/Santo_Domingo', 
        'utc': 'UTC-4', 
        'code': '+1829', 
        'emoji': '🇩🇴'
    },
    '1849': {
        'country': 'República Dominicana', 
        'timezone': 'America/Santo_Domingo', 
        'utc': 'UTC-4', 
        'code': '+1849', 
        'emoji': '🇩🇴'
    },
    '1787': {
        'country': 'Puerto Rico', 
        'timezone': 'America/Puerto_Rico', 
        'utc': 'UTC-4', 
        'code': '+1787', 
        'emoji': '🇵🇷'
    },
    # BRASIL Y USA
    '55': {
        'country': 'Brasil', 
        'timezone': 'America/Sao_Paulo', 
        'utc': 'UTC-3', 
        'code': '+55', 
        'emoji': '🇧🇷'
    },
    '1': {
        'country': 'Estados Unidos', 
        'timezone': 'America/New_York', 
        'utc': 'UTC-5', 
        'code': '+1', 
        'emoji': '🇺🇸'
    },
    # EUROPA
    '34': {
        'country': 'España', 
        'timezone': 'Europe/Madrid', 
        'utc': 'UTC+1', 
        'code': '+34', 
        'emoji': '🇪🇸'
    },
    '351': {
        'country': 'Portugal', 
        'timezone': 'Europe/Lisbon', 
        'utc': 'UTC+0', 
        'code': '+351', 
        'emoji': '🇵🇹'
    },
    '33': {
        'country': 'Francia', 
        'timezone': 'Europe/Paris', 
        'utc': 'UTC+1', 
        'code': '+33', 
        'emoji': '🇫🇷'
    },
    '39': {
        'country': 'Italia', 
        'timezone': 'Europe/Rome', 
        'utc': 'UTC+1', 
        'code': '+39', 
        'emoji': '🇮🇹'
    },
    '49': {
        'country': 'Alemania', 
        'timezone': 'Europe/Berlin', 
        'utc': 'UTC+1', 
        'code': '+49', 
        'emoji': '🇩🇪'
    },
    '44': {
        'country': 'Reino Unido', 
        'timezone': 'Europe/London', 
        'utc': 'UTC+0', 
        'code': '+44', 
        'emoji': '🇬🇧'
    },
    '353': {
        'country': 'Irlanda', 
        'timezone': 'Europe/Dublin', 
        'utc': 'UTC+0', 
        'code': '+353', 
        'emoji': '🇮🇪'
    },
    '32': {
        'country': 'Bélgica', 
        'timezone': 'Europe/Brussels', 
        'utc': 'UTC+1', 
        'code': '+32', 
        'emoji': '🇧🇪'
    },
    '31': {
        'country': 'Países Bajos', 
        'timezone': 'Europe/Amsterdam', 
        'utc': 'UTC+1', 
        'code': '+31', 
        'emoji': '🇳🇱'
    },
    '352': {
        'country': 'Luxemburgo', 
        'timezone': 'Europe/Luxembourg', 
        'utc': 'UTC+1', 
        'code': '+352', 
        'emoji': '🇱🇺'
    },
    '43': {
        'country': 'Austria', 
        'timezone': 'Europe/Vienna', 
        'utc': 'UTC+1', 
        'code': '+43', 
        'emoji': '🇦🇹'
    },
    '41': {
        'country': 'Suiza', 
        'timezone': 'Europe/Zurich', 
        'utc': 'UTC+1', 
        'code': '+41', 
        'emoji': '🇨🇭'
    },
    '30': {
        'country': 'Grecia', 
        'timezone': 'Europe/Athens', 
        'utc': 'UTC+2', 
        'code': '+30', 
        'emoji': '🇬🇷'
    },
    '45': {
        'country': 'Dinamarca', 
        'timezone': 'Europe/Copenhagen', 
        'utc': 'UTC+1', 
        'code': '+45', 
        'emoji': '🇩🇰'
    },
    '46': {
        'country': 'Suecia', 
        'timezone': 'Europe/Stockholm', 
        'utc': 'UTC+1', 
        'code': '+46', 
        'emoji': '🇸🇪'
    },
    '358': {
        'country': 'Finlandia', 
        'timezone': 'Europe/Helsinki', 
        'utc': 'UTC+2', 
        'code': '+358', 
        'emoji': '🇫🇮'
    },
    '47': {
        'country': 'Noruega', 
        'timezone': 'Europe/Oslo', 
        'utc': 'UTC+1', 
        'code': '+47', 
        'emoji': '🇳🇴'
    },
    '48': {
        'country': 'Polonia', 
        'timezone': 'Europe/Warsaw', 
        'utc': 'UTC+1', 
        'code': '+48', 
        'emoji': '🇵🇱'
    },
    '420': {
        'country': 'República Checa', 
        'timezone': 'Europe/Prague', 
        'utc': 'UTC+1', 
        'code': '+420', 
        'emoji': '🇨🇿'
    },
    '421': {
        'country': 'Eslovaquia', 
        'timezone': 'Europe/Bratislava', 
        'utc': 'UTC+1', 
        'code': '+421', 
        'emoji': '🇸🇰'
    },
    '386': {
        'country': 'Eslovenia', 
        'timezone': 'Europe/Ljubljana', 
        'utc': 'UTC+1', 
        'code': '+386', 
        'emoji': '🇸🇮'
    },
    '385': {
        'country': 'Croacia', 
        'timezone': 'Europe/Zagreb', 
        'utc': 'UTC+1', 
        'code': '+385', 
        'emoji': '🇭🇷'
    },
    '372': {
        'country': 'Estonia', 
        'timezone': 'Europe/Tallinn', 
        'utc': 'UTC+2', 
        'code': '+372', 
        'emoji': '🇪🇪'
    },
    '371': {
        'country': 'Letonia', 
        'timezone': 'Europe/Riga', 
        'utc': 'UTC+2', 
        'code': '+371', 
        'emoji': '🇱🇻'
    },
    '370': {
        'country': 'Lituania', 
        'timezone': 'Europe/Vilnius', 
        'utc': 'UTC+2', 
        'code': '+370', 
        'emoji': '🇱🇹'
    },
    '36': {
        'country': 'Hungría', 
        'timezone': 'Europe/Budapest', 
        'utc': 'UTC+1', 
        'code': '+36', 
        'emoji': '🇭🇺'
    },
    '40': {
        'country': 'Rumania', 
        'timezone': 'Europe/Bucharest', 
        'utc': 'UTC+2', 
        'code': '+40', 
        'emoji': '🇷🇴'
    },
    '359': {
        'country': 'Bulgaria', 
        'timezone': 'Europe/Sofia', 
        'utc': 'UTC+2', 
        'code': '+359', 
        'emoji': '🇧🇬'
    },
    '356': {
        'country': 'Malta', 
        'timezone': 'Europe/Malta', 
        'utc': 'UTC+1', 
        'code': '+356', 
        'emoji': '🇲🇹'
    },
    '357': {
        'country': 'Chipre', 
        'timezone': 'Europe/Nicosia', 
        'utc': 'UTC+2', 
        'code': '+357', 
        'emoji': '🇨🇾'
    },
}

# ============================================================
# CÓDIGOS DE ÁREA - ARGENTINA
# ============================================================
AREA_CODES_ARGENTINA = {
    '11': {'city': 'Buenos Aires', 'province': 'Buenos Aires'},
    '341': {'city': 'Rosario', 'province': 'Santa Fe'},
    '342': {'city': 'Santa Fe', 'province': 'Santa Fe'},
    '3401': {'city': '', 'province': 'Santa Fe'},
    '3402': {'city': '', 'province': 'Santa Fe'},
    '3404': {'city': '', 'province': 'Santa Fe'},
    '3405': {'city': '', 'province': 'Santa Fe'},
    '3406': {'city': 'San Jorge', 'province': 'Santa Fe'},
    '3407': {'city': '', 'province': 'Santa Fe'},
    '3408': {'city': '', 'province': 'Santa Fe'},
    '3409': {'city': '', 'province': 'Santa Fe'},
    '3460': {'city': 'Cañada de Gómez', 'province': 'Santa Fe'},
    '3462': {'city': 'Venado Tuerto', 'province': 'Santa Fe'},
    '3464': {'city': 'Rufino', 'province': 'Santa Fe'},
    '3465': {'city': 'Firmat', 'province': 'Santa Fe'},
    '3466': {'city': 'Villa Constitución', 'province': 'Santa Fe'},
    '3469': {'city': 'Arroyo Seco', 'province': 'Santa Fe'},
    '3471': {'city': 'Coronda', 'province': 'Santa Fe'},
    '3482': {'city': 'Gálvez', 'province': 'Santa Fe'},
    '3483': {'city': 'Vera', 'province': 'Santa Fe'},
    '3491': {'city': 'Ceres', 'province': 'Santa Fe'},
    '3492': {'city': 'Sunchales', 'province': 'Santa Fe'},
    '3493': {'city': 'Las Toscas', 'province': 'Santa Fe'},
    '351': {'city': 'Córdoba', 'province': 'Córdoba'},
    '352': {'city': 'Villa Carlos Paz', 'province': 'Córdoba'},
    '353': {'city': 'Villa María', 'province': 'Córdoba'},
    '354': {'city': 'Río Cuarto', 'province': 'Córdoba'},
    '3521': {'city': 'Dean Funes', 'province': 'Córdoba'},
    '3522': {'city': 'Villa Dolores', 'province': 'Córdoba'},
    '3524': {'city': 'Villa del Rosario', 'province': 'Córdoba'},
    '3525': {'city': 'Jesús María', 'province': 'Córdoba'},
    '3537': {'city': 'Bell Ville', 'province': 'Córdoba'},
    '3541': {'city': 'Alta Gracia', 'province': 'Córdoba'},
    '3543': {'city': 'Cosquín', 'province': 'Córdoba'},
    '3544': {'city': 'La Falda', 'province': 'Córdoba'},
    '3546': {'city': 'Santa Rosa de Calamuchita', 'province': 'Córdoba'},
    '3547': {'city': 'Villa General Belgrano', 'province': 'Córdoba'},
    '3548': {'city': 'Cruz del Eje', 'province': 'Córdoba'},
    '3549': {'city': 'Mina Clavero', 'province': 'Córdoba'},
    '3562': {'city': 'Marcos Juárez', 'province': 'Córdoba'},
    '3563': {'city': 'San Francisco', 'province': 'Córdoba'},
    '3564': {'city': 'Morteros', 'province': 'Córdoba'},
    '3571': {'city': 'Río Tercero', 'province': 'Córdoba'},
    '3572': {'city': 'Río Segundo', 'province': 'Córdoba'},
    '3585': {'city': 'Laboulaye', 'province': 'Córdoba'},
    '261': {'city': 'Mendoza', 'province': 'Mendoza'},
    '260': {'city': 'San Rafael', 'province': 'Mendoza'},
    '381': {'city': 'Tucumán', 'province': 'Tucumán'},
    '343': {'city': 'Paraná', 'province': 'Entre Ríos'},
    '345': {'city': 'Concordia', 'province': 'Entre Ríos'},
    '3442': {'city': 'C. del Uruguay', 'province': 'Entre Ríos'},
    '3446': {'city': 'Gualeguaychú', 'province': 'Entre Ríos'},
    '387': {'city': 'Salta', 'province': 'Salta'},
    '388': {'city': 'San Salvador de Jujuy', 'province': 'Jujuy'},
    '376': {'city': 'Posadas', 'province': 'Misiones'},
    '3757': {'city': 'Puerto Iguazú', 'province': 'Misiones'},
    '379': {'city': 'Corrientes', 'province': 'Corrientes'},
    '362': {'city': 'Resistencia', 'province': 'Chaco'},
    '370': {'city': 'Formosa', 'province': 'Formosa'},
    '385': {'city': 'Santiago del Estero', 'province': 'Sgo del Estero'},
    '264': {'city': 'San Juan', 'province': 'San Juan'},
    '266': {'city': 'San Luis', 'province': 'San Luis'},
    '2656': {'city': 'Villa Mercedes', 'province': 'San Luis'},
    '380': {'city': 'La Rioja', 'province': 'La Rioja'},
    '383': {'city': 'Catamarca', 'province': 'Catamarca'},
    '2954': {'city': 'Santa Rosa', 'province': 'La Pampa'},
    '299': {'city': 'Neuquén', 'province': 'Neuquén'},
    '2942': {'city': 'San Martín de los Andes', 'province': 'Neuquén'},
    '294': {'city': 'Bariloche', 'province': 'Río Negro'},
    '2920': {'city': 'Viedma', 'province': 'Río Negro'},
    '297': {'city': 'Comodoro Rivadavia', 'province': 'Chubut'},
    '2945': {'city': 'Esquel', 'province': 'Chubut'},
    '2965': {'city': 'Trelew', 'province': 'Chubut'},
    '2966': {'city': 'Río Gallegos', 'province': 'Santa Cruz'},
    '2902': {'city': 'El Calafate', 'province': 'Santa Cruz'},
    '2901': {'city': 'Ushuaia', 'province': 'Tierra del Fuego'},
    '2964': {'city': 'Río Grande', 'province': 'Tierra del Fuego'},
    '221': {'city': 'La Plata', 'province': 'Buenos Aires'},
    '223': {'city': 'Mar del Plata', 'province': 'Buenos Aires'},
    '2254': {'city': 'Pinamar', 'province': 'Buenos Aires'},
    '2255': {'city': 'Villa Gesell', 'province': 'Buenos Aires'},
    '2284': {'city': 'Olavarría', 'province': 'Buenos Aires'},
    '2293': {'city': 'Tandil', 'province': 'Buenos Aires'},
    '2323': {'city': 'Luján', 'province': 'Buenos Aires'},
    '2346': {'city': 'Chivilcoy', 'province': 'Buenos Aires'},
    '2353': {'city': 'Junín', 'province': 'Buenos Aires'},
    '2362': {'city': 'Pergamino', 'province': 'Buenos Aires'},
    '291': {'city': 'Bahía Blanca', 'province': 'Buenos Aires'},
}

# ============================================================
# CÓDIGOS DE ÁREA - MÉXICO
# ============================================================
AREA_CODES_MEXICO = {
    # CDMX y Área Metropolitana
    '55': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '552': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '553': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '554': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '555': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '556': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '557': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '558': {'city': 'Ciudad de México', 'province': 'CDMX'},
    
    # Jalisco
    '33': {'city': 'Guadalajara', 'province': 'Jalisco'},
    '331': {'city': 'Guadalajara', 'province': 'Jalisco'},
    '332': {'city': 'Guadalajara', 'province': 'Jalisco'},
    '333': {'city': 'Guadalajara', 'province': 'Jalisco'},
    '341': {'city': 'Cihuatlán', 'province': 'Jalisco'},
    '342': {'city': 'Autlán', 'province': 'Jalisco'},
    '343': {'city': 'Ciudad Guzmán', 'province': 'Jalisco'},
    '344': {'city': 'Tamazula', 'province': 'Jalisco'},
    '345': {'city': 'Tuxpan', 'province': 'Jalisco'},
    '346': {'city': 'Sayula', 'province': 'Jalisco'},
    '347': {'city': 'Tequila', 'province': 'Jalisco'},
    '348': {'city': 'Yahualica', 'province': 'Jalisco'},
    '349': {'city': 'Arandas', 'province': 'Jalisco'},
    '322': {'city': 'Puerto Vallarta', 'province': 'Jalisco'},
    '371': {'city': 'Ocotlán', 'province': 'Jalisco'},
    '372': {'city': 'La Barca', 'province': 'Jalisco'},
    '373': {'city': 'Tepatitlán', 'province': 'Jalisco'},
    '374': {'city': 'Ameca', 'province': 'Jalisco'},
    '375': {'city': 'Jocotepec', 'province': 'Jalisco'},
    '376': {'city': 'Chapala', 'province': 'Jalisco'},
    '377': {'city': 'Atotonilco', 'province': 'Jalisco'},
    '378': {'city': 'Teocaltiche', 'province': 'Jalisco'},
    '386': {'city': 'San Juan de los Lagos', 'province': 'Jalisco'},
    '387': {'city': 'Lagos de Moreno', 'province': 'Jalisco'},
    '388': {'city': 'Encarnación de Díaz', 'province': 'Jalisco'},
    '391': {'city': 'Tala', 'province': 'Jalisco'},
    '392': {'city': 'Etzatlán', 'province': 'Jalisco'},
    '393': {'city': 'Magdalena', 'province': 'Jalisco'},
    '395': {'city': 'Villa Hidalgo', 'province': 'Jalisco'},
    
    # Nuevo León
    '81': {'city': 'Monterrey', 'province': 'Nuevo León'},
    '811': {'city': 'Monterrey', 'province': 'Nuevo León'},
    '812': {'city': 'Monterrey', 'province': 'Nuevo León'},
    '818': {'city': 'San Pedro Garza García', 'province': 'Nuevo León'},
    '821': {'city': 'Linares', 'province': 'Nuevo León'},
    '823': {'city': 'Sabinas Hidalgo', 'province': 'Nuevo León'},
    '824': {'city': 'Montemorelos', 'province': 'Nuevo León'},
    '825': {'city': 'Cerralvo', 'province': 'Nuevo León'},
    '826': {'city': 'Doctor Arroyo', 'province': 'Nuevo León'},
    '828': {'city': 'Cadereyta', 'province': 'Nuevo León'},
    '829': {'city': 'China', 'province': 'Nuevo León'},
    
    # Estado de México
    '722': {'city': 'Toluca', 'province': 'Estado de México'},
    '721': {'city': 'Zinacantepec', 'province': 'Estado de México'},
    '723': {'city': 'Tenancingo', 'province': 'Estado de México'},
    '724': {'city': 'Ixtapan de la Sal', 'province': 'Estado de México'},
    '725': {'city': 'Santiago Tianguistenco', 'province': 'Estado de México'},
    '726': {'city': 'Valle de Bravo', 'province': 'Estado de México'},
    '728': {'city': 'Tejupilco', 'province': 'Estado de México'},
    '588': {'city': 'Atlacomulco', 'province': 'Estado de México'},
    '589': {'city': 'Jilotepec', 'province': 'Estado de México'},
    '591': {'city': 'Texcoco', 'province': 'Estado de México'},
    '592': {'city': 'San Martín de las Pirámides', 'province': 'Estado de México'},
    '593': {'city': 'Ecatepec', 'province': 'Estado de México'},
    '594': {'city': 'Tlalnepantla', 'province': 'Estado de México'},
    '595': {'city': 'Naucalpan', 'province': 'Estado de México'},
    '596': {'city': 'Cuautitlán', 'province': 'Estado de México'},
    '597': {'city': 'Tultitlán', 'province': 'Estado de México'},
    
    # Puebla
    '222': {'city': 'Puebla', 'province': 'Puebla'},
    '221': {'city': 'Cholula', 'province': 'Puebla'},
    '223': {'city': 'Atlixco', 'province': 'Puebla'},
    '224': {'city': 'Izúcar de Matamoros', 'province': 'Puebla'},
    '225': {'city': 'Tecamachalco', 'province': 'Puebla'},
    '226': {'city': 'San Martín Texmelucan', 'province': 'Puebla'},
    '227': {'city': 'Huejotzingo', 'province': 'Puebla'},
    '228': {'city': 'Teziutlán', 'province': 'Puebla'},
    '229': {'city': 'Huauchinango', 'province': 'Puebla'},
    '231': {'city': 'Chignahuapan', 'province': 'Puebla'},
    '232': {'city': 'Zacatlán', 'province': 'Puebla'},
    '233': {'city': 'Tehuacán', 'province': 'Puebla'},
    '236': {'city': 'Acatlán', 'province': 'Puebla'},
    '237': {'city': 'Ajalpan', 'province': 'Puebla'},
    '238': {'city': 'Ciudad Serdán', 'province': 'Puebla'},
    '243': {'city': 'Libres', 'province': 'Puebla'},
    '244': {'city': 'Acatzingo', 'province': 'Puebla'},
    '245': {'city': 'Tepeaca', 'province': 'Puebla'},
    '246': {'city': 'Tlaxcala', 'province': 'Tlaxcala'},
    '247': {'city': 'Apizaco', 'province': 'Tlaxcala'},
    '248': {'city': 'Huamantla', 'province': 'Tlaxcala'},
    '249': {'city': 'Calpulalpan', 'province': 'Tlaxcala'},
    
    # Querétaro
    '442': {'city': 'Querétaro', 'province': 'Querétaro'},
    '441': {'city': 'San Juan del Río', 'province': 'Querétaro'},
    '414': {'city': 'Jalpan', 'province': 'Querétaro'},
    '419': {'city': 'Tequisquiapan', 'province': 'Querétaro'},
    '427': {'city': 'Cadereyta', 'province': 'Querétaro'},
    
    # Guanajuato
    '477': {'city': 'León', 'province': 'Guanajuato'},
    '462': {'city': 'Irapuato', 'province': 'Guanajuato'},
    '461': {'city': 'Celaya', 'province': 'Guanajuato'},
    '464': {'city': 'Salamanca', 'province': 'Guanajuato'},
    '466': {'city': 'Acámbaro', 'province': 'Guanajuato'},
    '467': {'city': 'Salvatierra', 'province': 'Guanajuato'},
    '468': {'city': 'Dolores Hidalgo', 'province': 'Guanajuato'},
    '469': {'city': 'San Felipe', 'province': 'Guanajuato'},
    '471': {'city': 'Silao', 'province': 'Guanajuato'},
    '472': {'city': 'Guanajuato', 'province': 'Guanajuato'},
    '473': {'city': 'San Miguel de Allende', 'province': 'Guanajuato'},
    '474': {'city': 'San Francisco del Rincón', 'province': 'Guanajuato'},
    '475': {'city': 'Purísima del Rincón', 'province': 'Guanajuato'},
    '476': {'city': 'Pénjamo', 'province': 'Guanajuato'},
    '478': {'city': 'Valle de Santiago', 'province': 'Guanajuato'},
    
    # Michoacán
    '443': {'city': 'Morelia', 'province': 'Michoacán'},
    '351': {'city': 'Zamora', 'province': 'Michoacán'},
    '352': {'city': 'Jiquilpan', 'province': 'Michoacán'},
    '353': {'city': 'La Piedad', 'province': 'Michoacán'},
    '354': {'city': 'Zacapu', 'province': 'Michoacán'},
    '355': {'city': 'Uruapan', 'province': 'Michoacán'},
    '356': {'city': 'Pátzcuaro', 'province': 'Michoacán'},
    '357': {'city': 'Tacámbaro', 'province': 'Michoacán'},
    '358': {'city': 'Apatzingán', 'province': 'Michoacán'},
    '359': {'city': 'Nueva Italia', 'province': 'Michoacán'},
    '381': {'city': 'Sahuayo', 'province': 'Michoacán'},
    '382': {'city': 'Maravatío', 'province': 'Michoacán'},
    '383': {'city': 'Zitácuaro', 'province': 'Michoacán'},
    '384': {'city': 'Hidalgo', 'province': 'Michoacán'},
    '421': {'city': 'Lázaro Cárdenas', 'province': 'Michoacán'},
    '422': {'city': 'Coalcomán', 'province': 'Michoacán'},
    '423': {'city': 'Los Reyes', 'province': 'Michoacán'},
    '424': {'city': 'Paracho', 'province': 'Michoacán'},
    '425': {'city': 'Huetamo', 'province': 'Michoacán'},
    '426': {'city': 'Ciudad Hidalgo', 'province': 'Michoacán'},
    
    # Veracruz
    '229': {'city': 'Veracruz', 'province': 'Veracruz'},
    '228': {'city': 'Xalapa', 'province': 'Veracruz'},
    '271': {'city': 'Córdoba', 'province': 'Veracruz'},
    '272': {'city': 'Orizaba', 'province': 'Veracruz'},
    '273': {'city': 'Fortín', 'province': 'Veracruz'},
    '274': {'city': 'Tehuacán', 'province': 'Veracruz'},
    '278': {'city': 'Cosamaloapan', 'province': 'Veracruz'},
    '279': {'city': 'Tierra Blanca', 'province': 'Veracruz'},
    '281': {'city': 'Poza Rica', 'province': 'Veracruz'},
    '282': {'city': 'Tuxpan', 'province': 'Veracruz'},
    '283': {'city': 'Papantla', 'province': 'Veracruz'},
    '284': {'city': 'Martínez de la Torre', 'province': 'Veracruz'},
    '285': {'city': 'Misantla', 'province': 'Veracruz'},
    '286': {'city': 'San Andrés Tuxtla', 'province': 'Veracruz'},
    '287': {'city': 'Acayucan', 'province': 'Veracruz'},
    '288': {'city': 'Coatzacoalcos', 'province': 'Veracruz'},
    '289': {'city': 'Minatitlán', 'province': 'Veracruz'},
    '294': {'city': 'Las Choapas', 'province': 'Veracruz'},
    '296': {'city': 'Alvarado', 'province': 'Veracruz'},
    '297': {'city': 'Boca del Río', 'province': 'Veracruz'},
    
    # Chihuahua
    '614': {'city': 'Chihuahua', 'province': 'Chihuahua'},
    '656': {'city': 'Ciudad Juárez', 'province': 'Chihuahua'},
    '625': {'city': 'Nuevo Casas Grandes', 'province': 'Chihuahua'},
    '626': {'city': 'Cuauhtémoc', 'province': 'Chihuahua'},
    '627': {'city': 'Madera', 'province': 'Chihuahua'},
    '628': {'city': 'Parral', 'province': 'Chihuahua'},
    '629': {'city': 'Camargo', 'province': 'Chihuahua'},
    '635': {'city': 'Delicias', 'province': 'Chihuahua'},
    '636': {'city': 'Jiménez', 'province': 'Chihuahua'},
    '639': {'city': 'Ojinaga', 'province': 'Chihuahua'},
    '648': {'city': 'Saucillo', 'province': 'Chihuahua'},
    '649': {'city': 'Meoqui', 'province': 'Chihuahua'},
    '652': {'city': 'Ascensión', 'province': 'Chihuahua'},
    '659': {'city': 'Villa Ahumada', 'province': 'Chihuahua'},
    
    # Baja California
    '664': {'city': 'Tijuana', 'province': 'Baja California'},
    '663': {'city': 'Rosarito', 'province': 'Baja California'},
    '665': {'city': 'Tecate', 'province': 'Baja California'},
    '646': {'city': 'Ensenada', 'province': 'Baja California'},
    '686': {'city': 'Mexicali', 'province': 'Baja California'},
    '653': {'city': 'San Luis Río Colorado', 'province': 'Sonora'},
    '658': {'city': 'San Felipe', 'province': 'Baja California'},
    
    # Baja California Sur
    '612': {'city': 'La Paz', 'province': 'Baja California Sur'},
    '613': {'city': 'Ciudad Constitución', 'province': 'Baja California Sur'},
    '615': {'city': 'Guerrero Negro', 'province': 'Baja California Sur'},
    '624': {'city': 'Los Cabos', 'province': 'Baja California Sur'},
    
    # Sonora
    '662': {'city': 'Hermosillo', 'province': 'Sonora'},
    '622': {'city': 'Guaymas', 'province': 'Sonora'},
    '623': {'city': 'Ciudad Obregón', 'province': 'Sonora'},
    '631': {'city': 'Nogales', 'province': 'Sonora'},
    '632': {'city': 'Puerto Peñasco', 'province': 'Sonora'},
    '633': {'city': 'Caborca', 'province': 'Sonora'},
    '634': {'city': 'Santa Ana', 'province': 'Sonora'},
    '637': {'city': 'Cananea', 'province': 'Sonora'},
    '638': {'city': 'Agua Prieta', 'province': 'Sonora'},
    '641': {'city': 'Navojoa', 'province': 'Sonora'},
    '642': {'city': 'Huatabampo', 'province': 'Sonora'},
    '643': {'city': 'Álamos', 'province': 'Sonora'},
    '644': {'city': 'Empalme', 'province': 'Sonora'},
    '645': {'city': 'Ures', 'province': 'Sonora'},
    '647': {'city': 'San Carlos', 'province': 'Sonora'},
    
    # Sinaloa
    '667': {'city': 'Culiacán', 'province': 'Sinaloa'},
    '668': {'city': 'Los Mochis', 'province': 'Sinaloa'},
    '669': {'city': 'Mazatlán', 'province': 'Sinaloa'},
    '672': {'city': 'El Fuerte', 'province': 'Sinaloa'},
    '673': {'city': 'Guasave', 'province': 'Sinaloa'},
    '674': {'city': 'Guamúchil', 'province': 'Sinaloa'},
    '675': {'city': 'Mocorito', 'province': 'Sinaloa'},
    '687': {'city': 'Escuinapa', 'province': 'Sinaloa'},
    '694': {'city': 'Rosario', 'province': 'Sinaloa'},
    '695': {'city': 'El Dorado', 'province': 'Sinaloa'},
    '696': {'city': 'Eldorado', 'province': 'Sinaloa'},
    '697': {'city': 'La Cruz', 'province': 'Sinaloa'},
    
    # Coahuila
    '844': {'city': 'Saltillo', 'province': 'Coahuila'},
    '871': {'city': 'Torreón', 'province': 'Coahuila'},
    '861': {'city': 'Piedras Negras', 'province': 'Coahuila'},
    '862': {'city': 'Acuña', 'province': 'Coahuila'},
    '864': {'city': 'Múzquiz', 'province': 'Coahuila'},
    '866': {'city': 'Monclova', 'province': 'Coahuila'},
    '867': {'city': 'Sabinas', 'province': 'Coahuila'},
    '869': {'city': 'Nueva Rosita', 'province': 'Coahuila'},
    '872': {'city': 'Gómez Palacio', 'province': 'Durango'},
    '873': {'city': 'Lerdo', 'province': 'Durango'},
    '878': {'city': 'Parras', 'province': 'Coahuila'},
    
    # Tamaulipas
    '833': {'city': 'Tampico', 'province': 'Tamaulipas'},
    '834': {'city': 'Ciudad Victoria', 'province': 'Tamaulipas'},
    '835': {'city': 'Ciudad Mante', 'province': 'Tamaulipas'},
    '836': {'city': 'González', 'province': 'Tamaulipas'},
    '841': {'city': 'San Fernando', 'province': 'Tamaulipas'},
    '842': {'city': 'Soto La Marina', 'province': 'Tamaulipas'},
    '846': {'city': 'Altamira', 'province': 'Tamaulipas'},
    '868': {'city': 'Matamoros', 'province': 'Tamaulipas'},
    '891': {'city': 'Nuevo Laredo', 'province': 'Tamaulipas'},
    '892': {'city': 'Reynosa', 'province': 'Tamaulipas'},
    '893': {'city': 'Río Bravo', 'province': 'Tamaulipas'},
    '894': {'city': 'Valle Hermoso', 'province': 'Tamaulipas'},
    '897': {'city': 'Ciudad Miguel Alemán', 'province': 'Tamaulipas'},
    '899': {'city': 'Reynosa', 'province': 'Tamaulipas'},
    
    # Durango
    '618': {'city': 'Durango', 'province': 'Durango'},
    '671': {'city': 'Santiago Papasquiaro', 'province': 'Durango'},
    '676': {'city': 'Canatlán', 'province': 'Durango'},
    '677': {'city': 'Nuevo Ideal', 'province': 'Durango'},
    
    # Yucatán
    '999': {'city': 'Mérida', 'province': 'Yucatán'},
    '985': {'city': 'Tizimín', 'province': 'Yucatán'},
    '986': {'city': 'Valladolid', 'province': 'Yucatán'},
    '988': {'city': 'Motul', 'province': 'Yucatán'},
    '991': {'city': 'Ticul', 'province': 'Yucatán'},
    '992': {'city': 'Progreso', 'province': 'Yucatán'},
    '997': {'city': 'Izamal', 'province': 'Yucatán'},
    
    # Quintana Roo
    '998': {'city': 'Cancún', 'province': 'Quintana Roo'},
    '984': {'city': 'Playa del Carmen', 'province': 'Quintana Roo'},
    '983': {'city': 'Chetumal', 'province': 'Quintana Roo'},
    '987': {'city': 'Cozumel', 'province': 'Quintana Roo'},
    '994': {'city': 'Felipe Carrillo Puerto', 'province': 'Quintana Roo'},
    
    # Chiapas
    '961': {'city': 'Tuxtla Gutiérrez', 'province': 'Chiapas'},
    '962': {'city': 'San Cristóbal', 'province': 'Chiapas'},
    '963': {'city': 'Comitán', 'province': 'Chiapas'},
    '964': {'city': 'Tapachula', 'province': 'Chiapas'},
    '965': {'city': 'Arriaga', 'province': 'Chiapas'},
    '966': {'city': 'Tonalá', 'province': 'Chiapas'},
    '967': {'city': 'San Cristóbal de las Casas', 'province': 'Chiapas'},
    '968': {'city': 'Villaflores', 'province': 'Chiapas'},
    '916': {'city': 'Palenque', 'province': 'Chiapas'},
    '917': {'city': 'Pichucalco', 'province': 'Chiapas'},
    '918': {'city': 'Ocosingo', 'province': 'Chiapas'},
    '919': {'city': 'Yajalón', 'province': 'Chiapas'},
    '932': {'city': 'Huixtla', 'province': 'Chiapas'},
    '934': {'city': 'Motozintla', 'province': 'Chiapas'},
    
    # Oaxaca
    '951': {'city': 'Oaxaca', 'province': 'Oaxaca'},
    '953': {'city': 'Huajuapan', 'province': 'Oaxaca'},
    '954': {'city': 'Puerto Escondido', 'province': 'Oaxaca'},
    '958': {'city': 'Salina Cruz', 'province': 'Oaxaca'},
    '971': {'city': 'Tehuantepec', 'province': 'Oaxaca'},
    '972': {'city': 'Juchitán', 'province': 'Oaxaca'},
    
    # Guerrero
    '747': {'city': 'Acapulco', 'province': 'Guerrero'},
    '733': {'city': 'Iguala', 'province': 'Guerrero'},
    '734': {'city': 'Taxco', 'province': 'Guerrero'},
    '735': {'city': 'Teloloapan', 'province': 'Guerrero'},
    '736': {'city': 'Chilpancingo', 'province': 'Guerrero'},
    '737': {'city': 'Tixtla', 'province': 'Guerrero'},
    '741': {'city': 'Chilapa', 'province': 'Guerrero'},
    '742': {'city': 'Tlapa', 'province': 'Guerrero'},
    '743': {'city': 'Ayutla', 'province': 'Guerrero'},
    '744': {'city': 'Acapulco', 'province': 'Guerrero'},
    '745': {'city': 'Coyuca de Benítez', 'province': 'Guerrero'},
    '751': {'city': 'Altamirano', 'province': 'Guerrero'},
    '753': {'city': 'Ciudad Altamirano', 'province': 'Guerrero'},
    '754': {'city': 'Zihuatanejo', 'province': 'Guerrero'},
    '755': {'city': 'Ixtapa', 'province': 'Guerrero'},
    '756': {'city': 'Petatlan', 'province': 'Guerrero'},
    '757': {'city': 'Coyuca de Catalán', 'province': 'Guerrero'},
    '758': {'city': 'Ometepec', 'province': 'Guerrero'},
    
    # Morelos
    '777': {'city': 'Cuernavaca', 'province': 'Morelos'},
    '731': {'city': 'Jojutla', 'province': 'Morelos'},
    '734': {'city': 'Cuautla', 'province': 'Morelos'},
    '735': {'city': 'Yautepec', 'province': 'Morelos'},
    '737': {'city': 'Puente de Ixtla', 'province': 'Morelos'},
    '738': {'city': 'Temixco', 'province': 'Morelos'},
    '739': {'city': 'Jiutepec', 'province': 'Morelos'},
    
    # Hidalgo
    '771': {'city': 'Pachuca', 'province': 'Hidalgo'},
    '772': {'city': 'Actopan', 'province': 'Hidalgo'},
    '773': {'city': 'Tulancingo', 'province': 'Hidalgo'},
    '774': {'city': 'Apan', 'province': 'Hidalgo'},
    '775': {'city': 'Tepeji del Río', 'province': 'Hidalgo'},
    '778': {'city': 'Huejutla', 'province': 'Hidalgo'},
    '779': {'city': 'Tula', 'province': 'Hidalgo'},
    '789': {'city': 'Ixmiquilpan', 'province': 'Hidalgo'},
    
    # San Luis Potosí
    '444': {'city': 'San Luis Potosí', 'province': 'San Luis Potosí'},
    '481': {'city': 'Matehuala', 'province': 'San Luis Potosí'},
    '482': {'city': 'Cedral', 'province': 'San Luis Potosí'},
    '483': {'city': 'Ciudad Valles', 'province': 'San Luis Potosí'},
    '485': {'city': 'Tamazunchale', 'province': 'San Luis Potosí'},
    '486': {'city': 'Rioverde', 'province': 'San Luis Potosí'},
    '487': {'city': 'Cerritos', 'province': 'San Luis Potosí'},
    '488': {'city': 'Salinas', 'province': 'San Luis Potosí'},
    '489': {'city': 'Santa María del Río', 'province': 'San Luis Potosí'},
    
    # Aguascalientes
    '449': {'city': 'Aguascalientes', 'province': 'Aguascalientes'},
    '465': {'city': 'Calvillo', 'province': 'Aguascalientes'},
    
    # Zacatecas
    '492': {'city': 'Zacatecas', 'province': 'Zacatecas'},
    '493': {'city': 'Fresnillo', 'province': 'Zacatecas'},
    '494': {'city': 'Jerez', 'province': 'Zacatecas'},
    '495': {'city': 'Jalpa', 'province': 'Zacatecas'},
    '496': {'city': 'Nochistlán', 'province': 'Zacatecas'},
    '498': {'city': 'Río Grande', 'province': 'Zacatecas'},
    '499': {'city': 'Concepción del Oro', 'province': 'Zacatecas'},
    
    # Nayarit
    '311': {'city': 'Tepic', 'province': 'Nayarit'},
    '319': {'city': 'Compostela', 'province': 'Nayarit'},
    '323': {'city': 'Acaponeta', 'province': 'Nayarit'},
    '324': {'city': 'Santiago Ixcuintla', 'province': 'Nayarit'},
    '325': {'city': 'Tecuala', 'province': 'Nayarit'},
    '327': {'city': 'Ixtlán del Río', 'province': 'Nayarit'},
    '329': {'city': 'Bahía de Banderas', 'province': 'Nayarit'},
    
    # Colima
    '312': {'city': 'Colima', 'province': 'Colima'},
    '313': {'city': 'Manzanillo', 'province': 'Colima'},
    '314': {'city': 'Tecomán', 'province': 'Colima'},
    '316': {'city': 'Coquimatlán', 'province': 'Colima'},
    
    # Tabasco
    '993': {'city': 'Villahermosa', 'province': 'Tabasco'},
    '914': {'city': 'Cárdenas', 'province': 'Tabasco'},
    '917': {'city': 'Tenosique', 'province': 'Tabasco'},
    '923': {'city': 'Comalcalco', 'province': 'Tabasco'},
    '933': {'city': 'Macuspana', 'province': 'Tabasco'},
    '934': {'city': 'Emiliano Zapata', 'province': 'Tabasco'},
    '936': {'city': 'Huimanguillo', 'province': 'Tabasco'},
    '937': {'city': 'Paraíso', 'province': 'Tabasco'},
    
    # Campeche
    '981': {'city': 'Campeche', 'province': 'Campeche'},
    '938': {'city': 'Ciudad del Carmen', 'province': 'Campeche'},
    '982': {'city': 'Champotón', 'province': 'Campeche'},
    '996': {'city': 'Calkiní', 'province': 'Campeche'},
}

# ============================================================
# CÓDIGOS DE ÁREA - COLOMBIA
# ============================================================
AREA_CODES_COLOMBIA = {
    '1': {'city': 'Bogotá', 'province': 'Cundinamarca'},
    '2': {'city': 'Cali', 'province': 'Valle del Cauca'},
    '4': {'city': 'Medellín', 'province': 'Antioquia'},
    '5': {'city': 'Barranquilla', 'province': 'Atlántico'},
    '6': {'city': 'Pereira', 'province': 'Risaralda'},
    '7': {'city': 'Bucaramanga', 'province': 'Santander'},
    '8': {'city': 'Cúcuta', 'province': 'Norte de Santander'},
}

# ============================================================
# CÓDIGOS DE ÁREA - ESPAÑA
# ============================================================
AREA_CODES_SPAIN = {
    '91': {'city': 'Madrid', 'province': 'Madrid'},
    '93': {'city': 'Barcelona', 'province': 'Cataluña'},
    '96': {'city': 'Valencia', 'province': 'Valencia'},
    '95': {'city': 'Sevilla', 'province': 'Andalucía'},
    '94': {'city': 'Bilbao', 'province': 'País Vasco'},
    '98': {'city': 'Oviedo', 'province': 'Asturias'},
    '981': {'city': 'A Coruña', 'province': 'Galicia'},
    '986': {'city': 'Vigo', 'province': 'Galicia'},
    '976': {'city': 'Zaragoza', 'province': 'Aragón'},
    '971': {'city': 'Palma de Mallorca', 'province': 'Baleares'},
    '928': {'city': 'Las Palmas', 'province': 'Canarias'},
    '922': {'city': 'Tenerife', 'province': 'Canarias'},
    '952': {'city': 'Málaga', 'province': 'Andalucía'},
    '958': {'city': 'Granada', 'province': 'Andalucía'},
    '968': {'city': 'Murcia', 'province': 'Murcia'},
    '965': {'city': 'Alicante', 'province': 'Valencia'},
    '983': {'city': 'Valladolid', 'province': 'Castilla y León'},
    '948': {'city': 'Pamplona', 'province': 'Navarra'},
    '943': {'city': 'San Sebastián', 'province': 'País Vasco'},
    '942': {'city': 'Santander', 'province': 'Cantabria'},
}

# ============================================================
# CÓDIGOS DE ÁREA - BRASIL
# ============================================================
AREA_CODES_BRAZIL = {
    # São Paulo
    '11': {'city': 'São Paulo', 'province': 'São Paulo'},
    '12': {'city': 'São José dos Campos', 'province': 'São Paulo'},
    '13': {'city': 'Santos', 'province': 'São Paulo'},
    '14': {'city': 'Bauru', 'province': 'São Paulo'},
    '15': {'city': 'Sorocaba', 'province': 'São Paulo'},
    '16': {'city': 'Ribeirão Preto', 'province': 'São Paulo'},
    '17': {'city': 'São José do Rio Preto', 'province': 'São Paulo'},
    '18': {'city': 'Presidente Prudente', 'province': 'São Paulo'},
    '19': {'city': 'Campinas', 'province': 'São Paulo'},
    
    # Rio de Janeiro
    '21': {'city': 'Rio de Janeiro', 'province': 'Rio de Janeiro'},
    '22': {'city': 'Campos dos Goytacazes', 'province': 'Rio de Janeiro'},
    '24': {'city': 'Volta Redonda', 'province': 'Rio de Janeiro'},
    
    # Espírito Santo
    '27': {'city': 'Vitória', 'province': 'Espírito Santo'},
    '28': {'city': 'Cachoeiro de Itapemirim', 'province': 'Espírito Santo'},
    
    # Minas Gerais
    '31': {'city': 'Belo Horizonte', 'province': 'Minas Gerais'},
    '32': {'city': 'Juiz de Fora', 'province': 'Minas Gerais'},
    '33': {'city': 'Governador Valadares', 'province': 'Minas Gerais'},
    '34': {'city': 'Uberlândia', 'province': 'Minas Gerais'},
    '35': {'city': 'Poços de Caldas', 'province': 'Minas Gerais'},
    '37': {'city': 'Divinópolis', 'province': 'Minas Gerais'},
    '38': {'city': 'Montes Claros', 'province': 'Minas Gerais'},
    
    # Paraná
    '41': {'city': 'Curitiba', 'province': 'Paraná'},
    '42': {'city': 'Ponta Grossa', 'province': 'Paraná'},
    '43': {'city': 'Londrina', 'province': 'Paraná'},
    '44': {'city': 'Maringá', 'province': 'Paraná'},
    '45': {'city': 'Foz do Iguaçu', 'province': 'Paraná'},
    '46': {'city': 'Francisco Beltrão', 'province': 'Paraná'},
    
    # Santa Catarina
    '47': {'city': 'Joinville', 'province': 'Santa Catarina'},
    '48': {'city': 'Florianópolis', 'province': 'Santa Catarina'},
    '49': {'city': 'Chapecó', 'province': 'Santa Catarina'},
    
    # Rio Grande do Sul
    '51': {'city': 'Porto Alegre', 'province': 'Rio Grande do Sul'},
    '53': {'city': 'Pelotas', 'province': 'Rio Grande do Sul'},
    '54': {'city': 'Caxias do Sul', 'province': 'Rio Grande do Sul'},
    '55': {'city': 'Santa Maria', 'province': 'Rio Grande do Sul'},
    
    # Distrito Federal (Brasília)
    '61': {'city': 'Brasília', 'province': 'Distrito Federal'},
    
    # Goiás
    '62': {'city': 'Goiânia', 'province': 'Goiás'},
    '64': {'city': 'Rio Verde', 'province': 'Goiás'},
    
    # Tocantins
    '63': {'city': 'Palmas', 'province': 'Tocantins'},
    
    # Mato Grosso
    '65': {'city': 'Cuiabá', 'province': 'Mato Grosso'},
    '66': {'city': 'Rondonópolis', 'province': 'Mato Grosso'},
    
    # Mato Grosso do Sul
    '67': {'city': 'Campo Grande', 'province': 'Mato Grosso do Sul'},
    
    # Acre
    '68': {'city': 'Rio Branco', 'province': 'Acre'},
    
    # Rondônia
    '69': {'city': 'Porto Velho', 'province': 'Rondônia'},
    
    # Bahia
    '71': {'city': 'Salvador', 'province': 'Bahia'},
    '73': {'city': 'Ilhéus', 'province': 'Bahia'},
    '74': {'city': 'Juazeiro', 'province': 'Bahia'},
    '75': {'city': 'Feira de Santana', 'province': 'Bahia'},
    '77': {'city': 'Vitória da Conquista', 'province': 'Bahia'},
    
    # Sergipe
    '79': {'city': 'Aracaju', 'province': 'Sergipe'},
    
    # Pernambuco
    '81': {'city': 'Recife', 'province': 'Pernambuco'},
    '87': {'city': 'Petrolina', 'province': 'Pernambuco'},
    
    # Alagoas
    '82': {'city': 'Maceió', 'province': 'Alagoas'},
    
    # Paraíba
    '83': {'city': 'João Pessoa', 'province': 'Paraíba'},
    
    # Rio Grande do Norte
    '84': {'city': 'Natal', 'province': 'Rio Grande do Norte'},
    
    # Ceará
    '85': {'city': 'Fortaleza', 'province': 'Ceará'},
    '88': {'city': 'Juazeiro do Norte', 'province': 'Ceará'},
    
    # Piauí
    '86': {'city': 'Teresina', 'province': 'Piauí'},
    '89': {'city': 'Picos', 'province': 'Piauí'},
    
    # Maranhão
    '98': {'city': 'São Luís', 'province': 'Maranhão'},
    '99': {'city': 'Imperatriz', 'province': 'Maranhão'},
    
    # Pará
    '91': {'city': 'Belém', 'province': 'Pará'},
    '93': {'city': 'Santarém', 'province': 'Pará'},
    '94': {'city': 'Marabá', 'province': 'Pará'},
    
    # Amazonas
    '92': {'city': 'Manaus', 'province': 'Amazonas'},
    '97': {'city': 'Coari', 'province': 'Amazonas'},
    
    # Roraima
    '95': {'city': 'Boa Vista', 'province': 'Roraima'},
    
    # Amapá
    '96': {'city': 'Macapá', 'province': 'Amapá'},
}

# ============================================================
# CÓDIGOS DE ÁREA - ALEMANIA
# ============================================================
AREA_CODES_GERMANY = {
    '30': {'city': 'Berlín', 'province': 'Berlín'},
    '40': {'city': 'Hamburgo', 'province': 'Hamburgo'},
    '89': {'city': 'Múnich', 'province': 'Baviera'},
    '221': {'city': 'Colonia', 'province': 'Renania del Norte'},
    '69': {'city': 'Fráncfort', 'province': 'Hesse'},
    '711': {'city': 'Stuttgart', 'province': 'Baden-Wurtemberg'},
    '211': {'city': 'Düsseldorf', 'province': 'Renania del Norte'},
    '511': {'city': 'Hannover', 'province': 'Baja Sajonia'},
}

# ============================================================
# CÓDIGOS DE ÁREA - ITALIA
# ============================================================
AREA_CODES_ITALY = {
    '06': {'city': 'Roma', 'province': 'Lacio'},
    '02': {'city': 'Milán', 'province': 'Lombardía'},
    '011': {'city': 'Turín', 'province': 'Piamonte'},
    '081': {'city': 'Nápoles', 'province': 'Campania'},
    '055': {'city': 'Florencia', 'province': 'Toscana'},
    '010': {'city': 'Génova', 'province': 'Liguria'},
    '051': {'city': 'Bolonia', 'province': 'Emilia-Romaña'},
    '041': {'city': 'Venecia', 'province': 'Véneto'},
}

# ============================================================
# CÓDIGOS DE ÁREA - USA
# ============================================================
AREA_CODES_USA = {
    # New York
    '212': {'city': 'Manhattan', 'province': 'New York'},
    '315': {'city': 'Syracuse', 'province': 'New York'},
    '347': {'city': 'New York City', 'province': 'New York'},
    '516': {'city': 'Long Island', 'province': 'New York'},
    '518': {'city': 'Albany', 'province': 'New York'},
    '585': {'city': 'Rochester', 'province': 'New York'},
    '607': {'city': 'Binghamton', 'province': 'New York'},
    '631': {'city': 'Suffolk County', 'province': 'New York'},
    '646': {'city': 'Manhattan', 'province': 'New York'},
    '716': {'city': 'Buffalo', 'province': 'New York'},
    '718': {'city': 'Brooklyn/Queens', 'province': 'New York'},
    '845': {'city': 'Hudson Valley', 'province': 'New York'},
    '914': {'city': 'Westchester', 'province': 'New York'},
    '917': {'city': 'New York City', 'province': 'New York'},
    '929': {'city': 'New York City', 'province': 'New York'},
    
    # California
    '209': {'city': 'Stockton', 'province': 'California'},
    '213': {'city': 'Los Angeles', 'province': 'California'},
    '310': {'city': 'Santa Monica', 'province': 'California'},
    '323': {'city': 'Los Angeles', 'province': 'California'},
    '408': {'city': 'San Jose', 'province': 'California'},
    '415': {'city': 'San Francisco', 'province': 'California'},
    '424': {'city': 'Los Angeles', 'province': 'California'},
    '442': {'city': 'Oceanside', 'province': 'California'},
    '510': {'city': 'Oakland', 'province': 'California'},
    '530': {'city': 'Redding', 'province': 'California'},
    '559': {'city': 'Fresno', 'province': 'California'},
    '562': {'city': 'Long Beach', 'province': 'California'},
    '619': {'city': 'San Diego', 'province': 'California'},
    '626': {'city': 'Pasadena', 'province': 'California'},
    '650': {'city': 'San Mateo', 'province': 'California'},
    '657': {'city': 'Anaheim', 'province': 'California'},
    '661': {'city': 'Bakersfield', 'province': 'California'},
    '669': {'city': 'San Jose', 'province': 'California'},
    '707': {'city': 'Santa Rosa', 'province': 'California'},
    '714': {'city': 'Anaheim', 'province': 'California'},
    '747': {'city': 'Los Angeles', 'province': 'California'},
    '760': {'city': 'Palm Springs', 'province': 'California'},
    '805': {'city': 'Santa Barbara', 'province': 'California'},
    '818': {'city': 'Burbank', 'province': 'California'},
    '831': {'city': 'Monterey', 'province': 'California'},
    '858': {'city': 'San Diego', 'province': 'California'},
    '909': {'city': 'San Bernardino', 'province': 'California'},
    '916': {'city': 'Sacramento', 'province': 'California'},
    '925': {'city': 'Concord', 'province': 'California'},
    '949': {'city': 'Irvine', 'province': 'California'},
    '951': {'city': 'Riverside', 'province': 'California'},
    
    # Texas
    '210': {'city': 'San Antonio', 'province': 'Texas'},
    '214': {'city': 'Dallas', 'province': 'Texas'},
    '254': {'city': 'Waco', 'province': 'Texas'},
    '281': {'city': 'Houston', 'province': 'Texas'},
    '325': {'city': 'Abilene', 'province': 'Texas'},
    '346': {'city': 'Houston', 'province': 'Texas'},
    '361': {'city': 'Corpus Christi', 'province': 'Texas'},
    '409': {'city': 'Beaumont', 'province': 'Texas'},
    '430': {'city': 'Tyler', 'province': 'Texas'},
    '432': {'city': 'Midland', 'province': 'Texas'},
    '469': {'city': 'Dallas', 'province': 'Texas'},
    '512': {'city': 'Austin', 'province': 'Texas'},
    '682': {'city': 'Fort Worth', 'province': 'Texas'},
    '713': {'city': 'Houston', 'province': 'Texas'},
    '737': {'city': 'Austin', 'province': 'Texas'},
    '806': {'city': 'Lubbock', 'province': 'Texas'},
    '817': {'city': 'Fort Worth', 'province': 'Texas'},
    '830': {'city': 'Fredericksburg', 'province': 'Texas'},
    '832': {'city': 'Houston', 'province': 'Texas'},
    '903': {'city': 'Tyler', 'province': 'Texas'},
    '915': {'city': 'El Paso', 'province': 'Texas'},
    '936': {'city': 'Conroe', 'province': 'Texas'},
    '940': {'city': 'Denton', 'province': 'Texas'},
    '956': {'city': 'Laredo', 'province': 'Texas'},
    '972': {'city': 'Dallas', 'province': 'Texas'},
    '979': {'city': 'College Station', 'province': 'Texas'},
    
    # Florida
    '239': {'city': 'Fort Myers', 'province': 'Florida'},
    '305': {'city': 'Miami', 'province': 'Florida'},
    '321': {'city': 'Orlando', 'province': 'Florida'},
    '352': {'city': 'Gainesville', 'province': 'Florida'},
    '386': {'city': 'Daytona Beach', 'province': 'Florida'},
    '407': {'city': 'Orlando', 'province': 'Florida'},
    '561': {'city': 'West Palm Beach', 'province': 'Florida'},
    '727': {'city': 'St. Petersburg', 'province': 'Florida'},
    '754': {'city': 'Fort Lauderdale', 'province': 'Florida'},
    '772': {'city': 'Port St. Lucie', 'province': 'Florida'},
    '786': {'city': 'Miami', 'province': 'Florida'},
    '813': {'city': 'Tampa', 'province': 'Florida'},
    '850': {'city': 'Tallahassee', 'province': 'Florida'},
    '863': {'city': 'Lakeland', 'province': 'Florida'},
    '904': {'city': 'Jacksonville', 'province': 'Florida'},
    '941': {'city': 'Sarasota', 'province': 'Florida'},
    '954': {'city': 'Fort Lauderdale', 'province': 'Florida'},
    
    # Illinois
    '217': {'city': 'Springfield', 'province': 'Illinois'},
    '224': {'city': 'Chicago Suburbs', 'province': 'Illinois'},
    '309': {'city': 'Peoria', 'province': 'Illinois'},
    '312': {'city': 'Chicago', 'province': 'Illinois'},
    '331': {'city': 'Aurora', 'province': 'Illinois'},
    '618': {'city': 'Belleville', 'province': 'Illinois'},
    '630': {'city': 'Naperville', 'province': 'Illinois'},
    '708': {'city': 'Cicero', 'province': 'Illinois'},
    '773': {'city': 'Chicago', 'province': 'Illinois'},
    '779': {'city': 'Rockford', 'province': 'Illinois'},
    '815': {'city': 'Rockford', 'province': 'Illinois'},
    '847': {'city': 'Evanston', 'province': 'Illinois'},
    '872': {'city': 'Chicago', 'province': 'Illinois'},
    
    # Pennsylvania
    '215': {'city': 'Philadelphia', 'province': 'Pennsylvania'},
    '267': {'city': 'Philadelphia', 'province': 'Pennsylvania'},
    '272': {'city': 'Scranton', 'province': 'Pennsylvania'},
    '412': {'city': 'Pittsburgh', 'province': 'Pennsylvania'},
    '484': {'city': 'Allentown', 'province': 'Pennsylvania'},
    '570': {'city': 'Scranton', 'province': 'Pennsylvania'},
    '610': {'city': 'Allentown', 'province': 'Pennsylvania'},
    '717': {'city': 'Harrisburg', 'province': 'Pennsylvania'},
    '724': {'city': 'New Castle', 'province': 'Pennsylvania'},
    '814': {'city': 'Erie', 'province': 'Pennsylvania'},
    '878': {'city': 'Pittsburgh', 'province': 'Pennsylvania'},
    
    # Ohio
    '216': {'city': 'Cleveland', 'province': 'Ohio'},
    '220': {'city': 'Newark', 'province': 'Ohio'},
    '234': {'city': 'Akron', 'province': 'Ohio'},
    '330': {'city': 'Akron', 'province': 'Ohio'},
    '380': {'city': 'Columbus', 'province': 'Ohio'},
    '419': {'city': 'Toledo', 'province': 'Ohio'},
    '440': {'city': 'Parma', 'province': 'Ohio'},
    '513': {'city': 'Cincinnati', 'province': 'Ohio'},
    '567': {'city': 'Toledo', 'province': 'Ohio'},
    '614': {'city': 'Columbus', 'province': 'Ohio'},
    '740': {'city': 'Lancaster', 'province': 'Ohio'},
    '937': {'city': 'Dayton', 'province': 'Ohio'},
    
    # Georgia
    '229': {'city': 'Albany', 'province': 'Georgia'},
    '404': {'city': 'Atlanta', 'province': 'Georgia'},
    '470': {'city': 'Atlanta', 'province': 'Georgia'},
    '478': {'city': 'Macon', 'province': 'Georgia'},
    '678': {'city': 'Atlanta', 'province': 'Georgia'},
    '706': {'city': 'Augusta', 'province': 'Georgia'},
    '762': {'city': 'Augusta', 'province': 'Georgia'},
    '770': {'city': 'Marietta', 'province': 'Georgia'},
    '912': {'city': 'Savannah', 'province': 'Georgia'},
    '943': {'city': 'Atlanta', 'province': 'Georgia'},
    
    # North Carolina
    '252': {'city': 'Greenville', 'province': 'North Carolina'},
    '336': {'city': 'Greensboro', 'province': 'North Carolina'},
    '704': {'city': 'Charlotte', 'province': 'North Carolina'},
    '743': {'city': 'Greensboro', 'province': 'North Carolina'},
    '828': {'city': 'Asheville', 'province': 'North Carolina'},
    '910': {'city': 'Fayetteville', 'province': 'North Carolina'},
    '919': {'city': 'Raleigh', 'province': 'North Carolina'},
    '980': {'city': 'Charlotte', 'province': 'North Carolina'},
    '984': {'city': 'Raleigh', 'province': 'North Carolina'},
    
    # Michigan
    '231': {'city': 'Muskegon', 'province': 'Michigan'},
    '248': {'city': 'Troy', 'province': 'Michigan'},
    '269': {'city': 'Kalamazoo', 'province': 'Michigan'},
    '313': {'city': 'Detroit', 'province': 'Michigan'},
    '517': {'city': 'Lansing', 'province': 'Michigan'},
    '586': {'city': 'Warren', 'province': 'Michigan'},
    '616': {'city': 'Grand Rapids', 'province': 'Michigan'},
    '734': {'city': 'Ann Arbor', 'province': 'Michigan'},
    '810': {'city': 'Flint', 'province': 'Michigan'},
    '906': {'city': 'Marquette', 'province': 'Michigan'},
    '947': {'city': 'Troy', 'province': 'Michigan'},
    '989': {'city': 'Saginaw', 'province': 'Michigan'},
    
    # New Jersey
    '201': {'city': 'Jersey City', 'province': 'New Jersey'},
    '551': {'city': 'Jersey City', 'province': 'New Jersey'},
    '609': {'city': 'Trenton', 'province': 'New Jersey'},
    '732': {'city': 'Edison', 'province': 'New Jersey'},
    '848': {'city': 'Edison', 'province': 'New Jersey'},
    '856': {'city': 'Camden', 'province': 'New Jersey'},
    '862': {'city': 'Newark', 'province': 'New Jersey'},
    '908': {'city': 'Elizabeth', 'province': 'New Jersey'},
    '973': {'city': 'Newark', 'province': 'New Jersey'},
    
    # Virginia
    '276': {'city': 'Bristol', 'province': 'Virginia'},
    '434': {'city': 'Lynchburg', 'province': 'Virginia'},
    '540': {'city': 'Roanoke', 'province': 'Virginia'},
    '571': {'city': 'Arlington', 'province': 'Virginia'},
    '703': {'city': 'Arlington', 'province': 'Virginia'},
    '757': {'city': 'Norfolk', 'province': 'Virginia'},
    '804': {'city': 'Richmond', 'province': 'Virginia'},
    
    # Washington
    '206': {'city': 'Seattle', 'province': 'Washington'},
    '253': {'city': 'Tacoma', 'province': 'Washington'},
    '360': {'city': 'Olympia', 'province': 'Washington'},
    '425': {'city': 'Bellevue', 'province': 'Washington'},
    '509': {'city': 'Spokane', 'province': 'Washington'},
    '564': {'city': 'Olympia', 'province': 'Washington'},
    
    # Massachusetts
    '339': {'city': 'Boston', 'province': 'Massachusetts'},
    '351': {'city': 'Lowell', 'province': 'Massachusetts'},
    '413': {'city': 'Springfield', 'province': 'Massachusetts'},
    '508': {'city': 'Worcester', 'province': 'Massachusetts'},
    '617': {'city': 'Boston', 'province': 'Massachusetts'},
    '774': {'city': 'Worcester', 'province': 'Massachusetts'},
    '781': {'city': 'Boston', 'province': 'Massachusetts'},
    '857': {'city': 'Boston', 'province': 'Massachusetts'},
    '978': {'city': 'Lowell', 'province': 'Massachusetts'},
    
    # Arizona
    '480': {'city': 'Mesa', 'province': 'Arizona'},
    '520': {'city': 'Tucson', 'province': 'Arizona'},
    '602': {'city': 'Phoenix', 'province': 'Arizona'},
    '623': {'city': 'Glendale', 'province': 'Arizona'},
    '928': {'city': 'Flagstaff', 'province': 'Arizona'},
    
    # Tennessee
    '423': {'city': 'Chattanooga', 'province': 'Tennessee'},
    '615': {'city': 'Nashville', 'province': 'Tennessee'},
    '629': {'city': 'Nashville', 'province': 'Tennessee'},
    '731': {'city': 'Jackson', 'province': 'Tennessee'},
    '865': {'city': 'Knoxville', 'province': 'Tennessee'},
    '901': {'city': 'Memphis', 'province': 'Tennessee'},
    '931': {'city': 'Clarksville', 'province': 'Tennessee'},
    
    # Indiana
    '219': {'city': 'Gary', 'province': 'Indiana'},
    '260': {'city': 'Fort Wayne', 'province': 'Indiana'},
    '317': {'city': 'Indianapolis', 'province': 'Indiana'},
    '463': {'city': 'Indianapolis', 'province': 'Indiana'},
    '574': {'city': 'South Bend', 'province': 'Indiana'},
    '765': {'city': 'Muncie', 'province': 'Indiana'},
    '812': {'city': 'Evansville', 'province': 'Indiana'},
    '930': {'city': 'Evansville', 'province': 'Indiana'},
    
    # Missouri
    '314': {'city': 'St. Louis', 'province': 'Missouri'},
    '417': {'city': 'Springfield', 'province': 'Missouri'},
    '573': {'city': 'Jefferson City', 'province': 'Missouri'},
    '636': {'city': 'Chesterfield', 'province': 'Missouri'},
    '660': {'city': 'Sedalia', 'province': 'Missouri'},
    '816': {'city': 'Kansas City', 'province': 'Missouri'},
    
    # Maryland
    '240': {'city': 'Rockville', 'province': 'Maryland'},
    '301': {'city': 'Rockville', 'province': 'Maryland'},
    '410': {'city': 'Baltimore', 'province': 'Maryland'},
    '443': {'city': 'Baltimore', 'province': 'Maryland'},
    '667': {'city': 'Baltimore', 'province': 'Maryland'},
    
    # Wisconsin
    '262': {'city': 'Kenosha', 'province': 'Wisconsin'},
    '414': {'city': 'Milwaukee', 'province': 'Wisconsin'},
    '534': {'city': 'Milwaukee', 'province': 'Wisconsin'},
    '608': {'city': 'Madison', 'province': 'Wisconsin'},
    '715': {'city': 'Eau Claire', 'province': 'Wisconsin'},
    '920': {'city': 'Green Bay', 'province': 'Wisconsin'},
    
    # Colorado
    '303': {'city': 'Denver', 'province': 'Colorado'},
    '719': {'city': 'Colorado Springs', 'province': 'Colorado'},
    '720': {'city': 'Denver', 'province': 'Colorado'},
    '970': {'city': 'Fort Collins', 'province': 'Colorado'},
    
    # Minnesota
    '218': {'city': 'Duluth', 'province': 'Minnesota'},
    '320': {'city': 'St. Cloud', 'province': 'Minnesota'},
    '507': {'city': 'Rochester', 'province': 'Minnesota'},
    '612': {'city': 'Minneapolis', 'province': 'Minnesota'},
    '651': {'city': 'St. Paul', 'province': 'Minnesota'},
    '763': {'city': 'Minneapolis', 'province': 'Minnesota'},
    '952': {'city': 'Bloomington', 'province': 'Minnesota'},
    
    # South Carolina
    '803': {'city': 'Columbia', 'province': 'South Carolina'},
    '843': {'city': 'Charleston', 'province': 'South Carolina'},
    '854': {'city': 'Charleston', 'province': 'South Carolina'},
    '864': {'city': 'Greenville', 'province': 'South Carolina'},
    
    # Alabama
    '205': {'city': 'Birmingham', 'province': 'Alabama'},
    '251': {'city': 'Mobile', 'province': 'Alabama'},
    '256': {'city': 'Huntsville', 'province': 'Alabama'},
    '334': {'city': 'Montgomery', 'province': 'Alabama'},
    '938': {'city': 'Huntsville', 'province': 'Alabama'},
    
    # Louisiana
    '225': {'city': 'Baton Rouge', 'province': 'Louisiana'},
    '318': {'city': 'Shreveport', 'province': 'Louisiana'},
    '337': {'city': 'Lafayette', 'province': 'Louisiana'},
    '504': {'city': 'New Orleans', 'province': 'Louisiana'},
    '985': {'city': 'Houma', 'province': 'Louisiana'},
    
    # Kentucky
    '270': {'city': 'Bowling Green', 'province': 'Kentucky'},
    '364': {'city': 'Bowling Green', 'province': 'Kentucky'},
    '502': {'city': 'Louisville', 'province': 'Kentucky'},
    '606': {'city': 'Ashland', 'province': 'Kentucky'},
    '859': {'city': 'Lexington', 'province': 'Kentucky'},
    
    # Oregon
    '458': {'city': 'Eugene', 'province': 'Oregon'},
    '503': {'city': 'Portland', 'province': 'Oregon'},
    '541': {'city': 'Eugene', 'province': 'Oregon'},
    '971': {'city': 'Portland', 'province': 'Oregon'},
    
    # Oklahoma
    '405': {'city': 'Oklahoma City', 'province': 'Oklahoma'},
    '539': {'city': 'Tulsa', 'province': 'Oklahoma'},
    '580': {'city': 'Lawton', 'province': 'Oklahoma'},
    '918': {'city': 'Tulsa', 'province': 'Oklahoma'},
    
    # Connecticut
    '203': {'city': 'New Haven', 'province': 'Connecticut'},
    '475': {'city': 'New Haven', 'province': 'Connecticut'},
    '860': {'city': 'Hartford', 'province': 'Connecticut'},
    '959': {'city': 'Hartford', 'province': 'Connecticut'},
    
    # Utah
    '385': {'city': 'Salt Lake City', 'province': 'Utah'},
    '435': {'city': 'St. George', 'province': 'Utah'},
    '801': {'city': 'Salt Lake City', 'province': 'Utah'},
    
    # Nevada
    '702': {'city': 'Las Vegas', 'province': 'Nevada'},
    '725': {'city': 'Las Vegas', 'province': 'Nevada'},
    '775': {'city': 'Reno', 'province': 'Nevada'},
    
    # Iowa
    '319': {'city': 'Cedar Rapids', 'province': 'Iowa'},
    '515': {'city': 'Des Moines', 'province': 'Iowa'},
    '563': {'city': 'Davenport', 'province': 'Iowa'},
    '641': {'city': 'Mason City', 'province': 'Iowa'},
    '712': {'city': 'Sioux City', 'province': 'Iowa'},
    
    # Arkansas
    '479': {'city': 'Fort Smith', 'province': 'Arkansas'},
    '501': {'city': 'Little Rock', 'province': 'Arkansas'},
    '870': {'city': 'Jonesboro', 'province': 'Arkansas'},
    
    # Mississippi
    '228': {'city': 'Gulfport', 'province': 'Mississippi'},
    '601': {'city': 'Jackson', 'province': 'Mississippi'},
    '662': {'city': 'Tupelo', 'province': 'Mississippi'},
    '769': {'city': 'Jackson', 'province': 'Mississippi'},
    
    # Kansas
    '316': {'city': 'Wichita', 'province': 'Kansas'},
    '620': {'city': 'Dodge City', 'province': 'Kansas'},
    '785': {'city': 'Topeka', 'province': 'Kansas'},
    '913': {'city': 'Kansas City', 'province': 'Kansas'},
    
    # New Mexico
    '505': {'city': 'Albuquerque', 'province': 'New Mexico'},
    '575': {'city': 'Las Cruces', 'province': 'New Mexico'},
    
    # Nebraska
    '308': {'city': 'Grand Island', 'province': 'Nebraska'},
    '402': {'city': 'Omaha', 'province': 'Nebraska'},
    '531': {'city': 'Omaha', 'province': 'Nebraska'},
    
    # Idaho
    '208': {'city': 'Boise', 'province': 'Idaho'},
    '986': {'city': 'Boise', 'province': 'Idaho'},
    
    # West Virginia
    '304': {'city': 'Charleston', 'province': 'West Virginia'},
    '681': {'city': 'Charleston', 'province': 'West Virginia'},
    
    # Hawaii
    '808': {'city': 'Honolulu', 'province': 'Hawaii'},
    
    # New Hampshire
    '603': {'city': 'Manchester', 'province': 'New Hampshire'},
    
    # Maine
    '207': {'city': 'Portland', 'province': 'Maine'},
    
    # Rhode Island
    '401': {'city': 'Providence', 'province': 'Rhode Island'},
    
    # Montana
    '406': {'city': 'Billings', 'province': 'Montana'},
    
    # Delaware
    '302': {'city': 'Wilmington', 'province': 'Delaware'},
    
    # South Dakota
    '605': {'city': 'Sioux Falls', 'province': 'South Dakota'},
    
    # North Dakota
    '701': {'city': 'Fargo', 'province': 'North Dakota'},
    
    # Alaska
    '907': {'city': 'Anchorage', 'province': 'Alaska'},
    
    # Vermont
    '802': {'city': 'Burlington', 'province': 'Vermont'},
    
    # Wyoming
    '307': {'city': 'Cheyenne', 'province': 'Wyoming'},
    
    # Washington D.C.
    '202': {'city': 'Washington D.C.', 'province': 'DC'},
}

# ============================================================
# CÓDIGOS DE ÁREA - CHILE
# ============================================================
AREA_CODES_CHILE = {
    '2': {'city': 'Santiago', 'province': 'Metropolitana'},
    '32': {'city': 'Valparaíso', 'province': 'Valparaíso'},
    '33': {'city': 'Quillota', 'province': 'Valparaíso'},
    '34': {'city': 'San Felipe', 'province': 'Valparaíso'},
    '35': {'city': 'San Antonio', 'province': 'Valparaíso'},
    '41': {'city': 'Concepción', 'province': 'Biobío'},
    '42': {'city': 'Chillán', 'province': 'Ñuble'},
    '43': {'city': 'Los Ángeles', 'province': 'Biobío'},
    '45': {'city': 'Temuco', 'province': 'Araucanía'},
    '51': {'city': 'La Serena', 'province': 'Coquimbo'},
    '52': {'city': 'Copiapó', 'province': 'Atacama'},
    '53': {'city': 'Ovalle', 'province': 'Coquimbo'},
    '55': {'city': 'Antofagasta', 'province': 'Antofagasta'},
    '57': {'city': 'Iquique', 'province': 'Tarapacá'},
    '58': {'city': 'Arica', 'province': 'Arica y Parinacota'},
    '61': {'city': 'Punta Arenas', 'province': 'Magallanes'},
    '63': {'city': 'Valdivia', 'province': 'Los Ríos'},
    '64': {'city': 'Osorno', 'province': 'Los Lagos'},
    '65': {'city': 'Puerto Montt', 'province': 'Los Lagos'},
    '67': {'city': 'Coyhaique', 'province': 'Aysén'},
    '71': {'city': 'Talca', 'province': 'Maule'},
    '72': {'city': 'Rancagua', 'province': "O'Higgins"},
    '73': {'city': 'Linares', 'province': 'Maule'},
    '75': {'city': 'Curicó', 'province': 'Maule'},
}

# ============================================================
# CÓDIGOS DE ÁREA - PERÚ
# ============================================================
AREA_CODES_PERU = {
    '1': {'city': 'Lima', 'province': 'Lima'},
    '44': {'city': 'Trujillo', 'province': 'La Libertad'},
    '54': {'city': 'Arequipa', 'province': 'Arequipa'},
    '64': {'city': 'Huancayo', 'province': 'Junín'},
    '74': {'city': 'Chiclayo', 'province': 'Lambayeque'},
    '76': {'city': 'Cajamarca', 'province': 'Cajamarca'},
    '84': {'city': 'Cusco', 'province': 'Cusco'},
    '51': {'city': 'Puno', 'province': 'Puno'},
    '53': {'city': 'Tacna', 'province': 'Tacna'},
    '56': {'city': 'Ica', 'province': 'Ica'},
    '41': {'city': 'Chimbote', 'province': 'Áncash'},
    '43': {'city': 'Huaraz', 'province': 'Áncash'},
    '61': {'city': 'Pucallpa', 'province': 'Ucayali'},
    '65': {'city': 'Iquitos', 'province': 'Loreto'},
    '82': {'city': 'Puerto Maldonado', 'province': 'Madre de Dios'},
    '66': {'city': 'Ayacucho', 'province': 'Ayacucho'},
    '67': {'city': 'Huancavelica', 'province': 'Huancavelica'},
    '73': {'city': 'Piura', 'province': 'Piura'},
    '72': {'city': 'Tumbes', 'province': 'Tumbes'},
    '42': {'city': 'Tarapoto', 'province': 'San Martín'},
}

# ============================================================
# CÓDIGOS DE ÁREA - VENEZUELA
# ============================================================
AREA_CODES_VENEZUELA = {
    '212': {'city': 'Caracas', 'province': 'Distrito Capital'},
    '241': {'city': 'Valencia', 'province': 'Carabobo'},
    '261': {'city': 'Maracaibo', 'province': 'Zulia'},
    '251': {'city': 'Barquisimeto', 'province': 'Lara'},
    '243': {'city': 'Maracay', 'province': 'Aragua'},
    '281': {'city': 'Puerto La Cruz', 'province': 'Anzoátegui'},
    '283': {'city': 'Barcelona', 'province': 'Anzoátegui'},
    '271': {'city': 'Mérida', 'province': 'Mérida'},
    '276': {'city': 'San Cristóbal', 'province': 'Táchira'},
    '291': {'city': 'Cumaná', 'province': 'Sucre'},
    '255': {'city': 'Acarigua', 'province': 'Portuguesa'},
    '257': {'city': 'Barinas', 'province': 'Barinas'},
    '286': {'city': 'Ciudad Bolívar', 'province': 'Bolívar'},
    '285': {'city': 'Ciudad Guayana', 'province': 'Bolívar'},
    '263': {'city': 'Cabimas', 'province': 'Zulia'},
    '252': {'city': 'Coro', 'province': 'Falcón'},
    '253': {'city': 'Punto Fijo', 'province': 'Falcón'},
    '295': {'city': 'Porlamar', 'province': 'Nueva Esparta'},
    '258': {'city': 'San Fernando', 'province': 'Apure'},
    '244': {'city': 'Los Teques', 'province': 'Miranda'},
}

# ============================================================
# CÓDIGOS DE ÁREA - ECUADOR
# ============================================================
AREA_CODES_ECUADOR = {
    '2': {'city': 'Quito', 'province': 'Pichincha'},
    '4': {'city': 'Guayaquil', 'province': 'Guayas'},
    '7': {'city': 'Cuenca', 'province': 'Azuay'},
    '3': {'city': 'Ambato', 'province': 'Tungurahua'},
    '6': {'city': 'Ibarra', 'province': 'Imbabura'},
    '5': {'city': 'Portoviejo', 'province': 'Manabí'},
    '42': {'city': 'Machala', 'province': 'El Oro'},
    '62': {'city': 'Tulcán', 'province': 'Carchi'},
    '32': {'city': 'Riobamba', 'province': 'Chimborazo'},
    '72': {'city': 'Loja', 'province': 'Loja'},
    '52': {'city': 'Manta', 'province': 'Manabí'},
    '63': {'city': 'Esmeraldas', 'province': 'Esmeraldas'},
    '22': {'city': 'Santo Domingo', 'province': 'Santo Domingo'},
    '45': {'city': 'Milagro', 'province': 'Guayas'},
    '47': {'city': 'Durán', 'province': 'Guayas'},
}

# ============================================================
# CÓDIGOS DE ÁREA - BOLIVIA
# ============================================================
AREA_CODES_BOLIVIA = {
    '2': {'city': 'La Paz', 'province': 'La Paz'},
    '3': {'city': 'Santa Cruz', 'province': 'Santa Cruz'},
    '4': {'city': 'Cochabamba', 'province': 'Cochabamba'},
    '46': {'city': 'Sucre', 'province': 'Chuquisaca'},
    '52': {'city': 'Oruro', 'province': 'Oruro'},
    '62': {'city': 'Potosí', 'province': 'Potosí'},
    '66': {'city': 'Tarija', 'province': 'Tarija'},
    '38': {'city': 'Trinidad', 'province': 'Beni'},
    '39': {'city': 'Cobija', 'province': 'Pando'},
}

# ============================================================
# CÓDIGOS DE ÁREA - PARAGUAY
# ============================================================
AREA_CODES_PARAGUAY = {
    '21': {'city': 'Asunción', 'province': 'Asunción'},
    '61': {'city': 'Ciudad del Este', 'province': 'Alto Paraná'},
    '71': {'city': 'Encarnación', 'province': 'Itapúa'},
    '31': {'city': 'San Lorenzo', 'province': 'Central'},
    '24': {'city': 'Luque', 'province': 'Central'},
    '28': {'city': 'Lambaré', 'province': 'Central'},
    '32': {'city': 'Caaguazú', 'province': 'Caaguazú'},
    '36': {'city': 'Coronel Oviedo', 'province': 'Caaguazú'},
    '41': {'city': 'Villarrica', 'province': 'Guairá'},
    '46': {'city': 'Pilar', 'province': 'Ñeembucú'},
    '38': {'city': 'San Juan Bautista', 'province': 'Misiones'},
    '81': {'city': 'Concepción', 'province': 'Concepción'},
    '83': {'city': 'Pedro Juan Caballero', 'province': 'Amambay'},
    '72': {'city': 'San Ignacio', 'province': 'Misiones'},
}

# ============================================================
# CÓDIGOS DE ÁREA - URUGUAY
# ============================================================
AREA_CODES_URUGUAY = {
    '2': {'city': 'Montevideo', 'province': 'Montevideo'},
    '42': {'city': 'Maldonado', 'province': 'Maldonado'},
    '44': {'city': 'Paysandú', 'province': 'Paysandú'},
    '45': {'city': 'Salto', 'province': 'Salto'},
    '52': {'city': 'Colonia', 'province': 'Colonia'},
    '54': {'city': 'Mercedes', 'province': 'Soriano'},
    '53': {'city': 'Trinidad', 'province': 'Flores'},
    '43': {'city': 'Rivera', 'province': 'Rivera'},
    '47': {'city': 'Artigas', 'province': 'Artigas'},
    '72': {'city': 'Melo', 'province': 'Cerro Largo'},
    '73': {'city': 'Treinta y Tres', 'province': 'Treinta y Tres'},
    '74': {'city': 'Rocha', 'province': 'Rocha'},
    '64': {'city': 'Tacuarembó', 'province': 'Tacuarembó'},
    '62': {'city': 'Durazno', 'province': 'Durazno'},
    '56': {'city': 'Florida', 'province': 'Florida'},
}

# ============================================================
# CÓDIGOS DE ÁREA - GUATEMALA
# ============================================================
AREA_CODES_GUATEMALA = {
    '2': {'city': 'Ciudad de Guatemala', 'province': 'Guatemala'},
    '7': {'city': 'Quetzaltenango', 'province': 'Quetzaltenango'},
    '9': {'city': 'Escuintla', 'province': 'Escuintla'},
    '8': {'city': 'Puerto Barrios', 'province': 'Izabal'},
    '5': {'city': 'Mazatenango', 'province': 'Suchitepéquez'},
    '6': {'city': 'Cobán', 'province': 'Alta Verapaz'},
    '4': {'city': 'Antigua Guatemala', 'province': 'Sacatepéquez'},
}

# ============================================================
# CÓDIGOS DE ÁREA - EL SALVADOR
# ============================================================
AREA_CODES_EL_SALVADOR = {
    '2': {'city': 'San Salvador', 'province': 'San Salvador'},
    '24': {'city': 'Santa Ana', 'province': 'Santa Ana'},
    '26': {'city': 'San Miguel', 'province': 'San Miguel'},
    '25': {'city': 'Sonsonate', 'province': 'Sonsonate'},
    '23': {'city': 'Santa Tecla', 'province': 'La Libertad'},
    '27': {'city': 'Usulután', 'province': 'Usulután'},
    '28': {'city': 'La Unión', 'province': 'La Unión'},
}

# ============================================================
# CÓDIGOS DE ÁREA - HONDURAS
# ============================================================
AREA_CODES_HONDURAS = {
    '2': {'city': 'Tegucigalpa', 'province': 'Francisco Morazán'},
    '5': {'city': 'San Pedro Sula', 'province': 'Cortés'},
    '4': {'city': 'La Ceiba', 'province': 'Atlántida'},
    '7': {'city': 'Choluteca', 'province': 'Choluteca'},
    '6': {'city': 'Comayagua', 'province': 'Comayagua'},
    '8': {'city': 'Santa Rosa de Copán', 'province': 'Copán'},
}

# ============================================================
# CÓDIGOS DE ÁREA - NICARAGUA
# ============================================================
AREA_CODES_NICARAGUA = {
    '2': {'city': 'Managua', 'province': 'Managua'},
    '25': {'city': 'León', 'province': 'León'},
    '27': {'city': 'Bluefields', 'province': 'RACCS'},
    '28': {'city': 'Puerto Cabezas', 'province': 'RACCN'},
    '23': {'city': 'Granada', 'province': 'Granada'},
    '24': {'city': 'Masaya', 'province': 'Masaya'},
    '26': {'city': 'Chinandega', 'province': 'Chinandega'},
    '22': {'city': 'Matagalpa', 'province': 'Matagalpa'},
}

# ============================================================
# CÓDIGOS DE ÁREA - COSTA RICA
# ============================================================
AREA_CODES_COSTA_RICA = {
    '2': {'city': 'San José', 'province': 'San José'},
    '24': {'city': 'Alajuela', 'province': 'Alajuela'},
    '25': {'city': 'Heredia', 'province': 'Heredia'},
    '26': {'city': 'Liberia', 'province': 'Guanacaste'},
    '27': {'city': 'Puntarenas', 'province': 'Puntarenas'},
    '22': {'city': 'Cartago', 'province': 'Cartago'},
    '2758': {'city': 'Limón', 'province': 'Limón'},
}

# ============================================================
# CÓDIGOS DE ÁREA - PANAMÁ
# ============================================================
AREA_CODES_PANAMA = {
    '2': {'city': 'Ciudad de Panamá', 'province': 'Panamá'},
    '7': {'city': 'Colón', 'province': 'Colón'},
    '9': {'city': 'David', 'province': 'Chiriquí'},
    '99': {'city': 'Boquete', 'province': 'Chiriquí'},
    '95': {'city': 'Santiago', 'province': 'Veraguas'},
    '96': {'city': 'Chitré', 'province': 'Herrera'},
    '97': {'city': 'Las Tablas', 'province': 'Los Santos'},
    '98': {'city': 'Penonomé', 'province': 'Coclé'},
}

# ============================================================
# CÓDIGOS DE ÁREA - REP. DOMINICANA
# ============================================================
AREA_CODES_DOMINICAN_REPUBLIC = {
    '809': {'city': 'Santo Domingo', 'province': 'Distrito Nacional'},
    '829': {'city': 'Santo Domingo', 'province': 'Distrito Nacional'},
    '849': {'city': 'Santo Domingo', 'province': 'Distrito Nacional'},
}

# ============================================================
# CÓDIGOS DE ÁREA - PUERTO RICO
# ============================================================
AREA_CODES_PUERTO_RICO = {
    '787': {'city': 'San Juan', 'province': 'San Juan'},
    '939': {'city': 'San Juan', 'province': 'San Juan'},
}

# ============================================================
# CÓDIGOS DE ÁREA - PORTUGAL
# ============================================================
AREA_CODES_PORTUGAL = {
    '21': {'city': 'Lisboa', 'province': 'Lisboa'},
    '22': {'city': 'Oporto', 'province': 'Porto'},
    '231': {'city': 'Coímbra', 'province': 'Coímbra'},
    '234': {'city': 'Aveiro', 'province': 'Aveiro'},
    '239': {'city': 'Coímbra', 'province': 'Coímbra'},
    '241': {'city': 'Castelo Branco', 'province': 'Castelo Branco'},
    '244': {'city': 'Leiria', 'province': 'Leiria'},
    '249': {'city': 'Santarém', 'province': 'Santarém'},
    '251': {'city': 'Viana do Castelo', 'province': 'Viana do Castelo'},
    '253': {'city': 'Braga', 'province': 'Braga'},
    '256': {'city': 'Viseu', 'province': 'Viseu'},
    '259': {'city': 'Vila Real', 'province': 'Vila Real'},
    '261': {'city': 'Torres Vedras', 'province': 'Lisboa'},
    '263': {'city': 'Vila Franca', 'province': 'Lisboa'},
    '265': {'city': 'Setúbal', 'province': 'Setúbal'},
    '266': {'city': 'Évora', 'province': 'Évora'},
    '268': {'city': 'Elvas', 'province': 'Portalegre'},
    '269': {'city': 'Beja', 'province': 'Beja'},
    '281': {'city': 'Tavira', 'province': 'Faro'},
    '282': {'city': 'Portimão', 'province': 'Faro'},
    '289': {'city': 'Faro', 'province': 'Faro'},
    '291': {'city': 'Funchal', 'province': 'Madeira'},
    '292': {'city': 'Horta', 'province': 'Azores'},
    '295': {'city': 'Angra do Heroísmo', 'province': 'Azores'},
    '296': {'city': 'Ponta Delgada', 'province': 'Azores'},
}

# ============================================================
# CÓDIGOS DE ÁREA - FRANCIA
# ============================================================
AREA_CODES_FRANCE = {
    '1': {'city': 'París', 'province': 'Île-de-France'},
    '2': {'city': 'Noroeste', 'province': 'Normandía/Bretaña'},
    '3': {'city': 'Noreste', 'province': 'Grand Est'},
    '4': {'city': 'Sureste', 'province': 'Auvergne-Rhône-Alpes'},
    '5': {'city': 'Suroeste', 'province': 'Nouvelle-Aquitaine'},
}

# ============================================================
# CÓDIGOS DE ÁREA - REINO UNIDO
# ============================================================
AREA_CODES_UK = {
    '20': {'city': 'Londres', 'province': 'Greater London'},
    '121': {'city': 'Birmingham', 'province': 'West Midlands'},
    '131': {'city': 'Edimburgo', 'province': 'Escocia'},
    '141': {'city': 'Glasgow', 'province': 'Escocia'},
    '151': {'city': 'Liverpool', 'province': 'Merseyside'},
    '161': {'city': 'Mánchester', 'province': 'Greater Manchester'},
    '113': {'city': 'Leeds', 'province': 'West Yorkshire'},
    '114': {'city': 'Sheffield', 'province': 'South Yorkshire'},
    '115': {'city': 'Nottingham', 'province': 'Nottinghamshire'},
    '116': {'city': 'Leicester', 'province': 'Leicestershire'},
    '117': {'city': 'Bristol', 'province': 'Bristol'},
    '118': {'city': 'Reading', 'province': 'Berkshire'},
    '191': {'city': 'Newcastle', 'province': 'Tyne and Wear'},
    '23': {'city': 'Southampton', 'province': 'Hampshire'},
    '24': {'city': 'Coventry', 'province': 'West Midlands'},
    '28': {'city': 'Belfast', 'province': 'Irlanda del Norte'},
    '29': {'city': 'Cardiff', 'province': 'Gales'},
}

# ============================================================
# CÓDIGOS DE ÁREA - IRLANDA
# ============================================================
AREA_CODES_IRELAND = {
    '1': {'city': 'Dublín', 'province': 'Leinster'},
    '21': {'city': 'Cork', 'province': 'Munster'},
    '61': {'city': 'Limerick', 'province': 'Munster'},
    '91': {'city': 'Galway', 'province': 'Connacht'},
    '51': {'city': 'Waterford', 'province': 'Munster'},
    '41': {'city': 'Drogheda', 'province': 'Leinster'},
    '42': {'city': 'Dundalk', 'province': 'Leinster'},
    '71': {'city': 'Sligo', 'province': 'Connacht'},
    '74': {'city': 'Letterkenny', 'province': 'Ulster'},
    '66': {'city': 'Tralee', 'province': 'Munster'},
}

# ============================================================
# CÓDIGOS DE ÁREA - BÉLGICA
# ============================================================
AREA_CODES_BELGIUM = {
    '2': {'city': 'Bruselas', 'province': 'Bruselas'},
    '3': {'city': 'Amberes', 'province': 'Amberes'},
    '4': {'city': 'Lieja', 'province': 'Lieja'},
    '9': {'city': 'Gante', 'province': 'Flandes Oriental'},
    '50': {'city': 'Brujas', 'province': 'Flandes Occidental'},
    '51': {'city': 'Roeselare', 'province': 'Flandes Occidental'},
    '52': {'city': 'Dendermonde', 'province': 'Flandes Oriental'},
    '56': {'city': 'Kortrijk', 'province': 'Flandes Occidental'},
    '59': {'city': 'Ostende', 'province': 'Flandes Occidental'},
    '10': {'city': 'Wavre', 'province': 'Brabante Valón'},
    '11': {'city': 'Hasselt', 'province': 'Limburgo'},
    '13': {'city': 'Diest', 'province': 'Brabante Flamenco'},
    '14': {'city': 'Turnhout', 'province': 'Amberes'},
    '15': {'city': 'Malinas', 'province': 'Amberes'},
    '16': {'city': 'Lovaina', 'province': 'Brabante Flamenco'},
    '19': {'city': 'Waremme', 'province': 'Lieja'},
    '65': {'city': 'Mons', 'province': 'Henao'},
    '67': {'city': 'Nivelles', 'province': 'Brabante Valón'},
    '69': {'city': 'Tournai', 'province': 'Henao'},
    '71': {'city': 'Charleroi', 'province': 'Henao'},
    '81': {'city': 'Namur', 'province': 'Namur'},
    '87': {'city': 'Verviers', 'province': 'Lieja'},
}

# ============================================================
# CÓDIGOS DE ÁREA - PAÍSES BAJOS
# ============================================================
AREA_CODES_NETHERLANDS = {
    '20': {'city': 'Ámsterdam', 'province': 'Holanda Septentrional'},
    '10': {'city': 'Róterdam', 'province': 'Holanda Meridional'},
    '70': {'city': 'La Haya', 'province': 'Holanda Meridional'},
    '30': {'city': 'Utrecht', 'province': 'Utrecht'},
    '40': {'city': 'Eindhoven', 'province': 'Brabante Septentrional'},
    '50': {'city': 'Groninga', 'province': 'Groninga'},
    '24': {'city': 'Nimega', 'province': 'Güeldres'},
    '26': {'city': 'Arnhem', 'province': 'Güeldres'},
    '15': {'city': 'Delft', 'province': 'Holanda Meridional'},
    '71': {'city': 'Leiden', 'province': 'Holanda Meridional'},
    '23': {'city': 'Haarlem', 'province': 'Holanda Septentrional'},
    '35': {'city': 'Hilversum', 'province': 'Holanda Septentrional'},
    '43': {'city': 'Maastricht', 'province': 'Limburgo'},
    '45': {'city': 'Heerlen', 'province': 'Limburgo'},
    '55': {'city': 'Apeldoorn', 'province': 'Güeldres'},
    '53': {'city': 'Enschede', 'province': 'Overijssel'},
    '38': {'city': 'Zwolle', 'province': 'Overijssel'},
    '58': {'city': 'Leeuwarden', 'province': 'Frisia'},
    '72': {'city': 'Alkmaar', 'province': 'Holanda Septentrional'},
    '76': {'city': 'Breda', 'province': 'Brabante Septentrional'},
    '13': {'city': 'Tilburg', 'province': 'Brabante Septentrional'},
    '73': {'city': "s-Hertogenbosch", 'province': 'Brabante Septentrional'},
    '78': {'city': 'Dordrecht', 'province': 'Holanda Meridional'},
    '79': {'city': 'Zoetermeer', 'province': 'Holanda Meridional'},
}

# ============================================================
# CÓDIGOS DE ÁREA - AUSTRIA
# ============================================================
AREA_CODES_AUSTRIA = {
    '1': {'city': 'Viena', 'province': 'Viena'},
    '316': {'city': 'Graz', 'province': 'Estiria'},
    '732': {'city': 'Linz', 'province': 'Alta Austria'},
    '662': {'city': 'Salzburgo', 'province': 'Salzburgo'},
    '512': {'city': 'Innsbruck', 'province': 'Tirol'},
    '463': {'city': 'Klagenfurt', 'province': 'Carintia'},
    '2742': {'city': 'St. Pölten', 'province': 'Baja Austria'},
    '5572': {'city': 'Dornbirn', 'province': 'Vorarlberg'},
    '5574': {'city': 'Bregenz', 'province': 'Vorarlberg'},
    '7252': {'city': 'Wels', 'province': 'Alta Austria'},
    '2622': {'city': 'Wiener Neustadt', 'province': 'Baja Austria'},
    '3842': {'city': 'Leoben', 'province': 'Estiria'},
    '2236': {'city': 'Mödling', 'province': 'Baja Austria'},
}

# ============================================================
# CÓDIGOS DE ÁREA - SUIZA
# ============================================================
AREA_CODES_SWITZERLAND = {
    '44': {'city': 'Zúrich', 'province': 'Zúrich'},
    '22': {'city': 'Ginebra', 'province': 'Ginebra'},
    '61': {'city': 'Basilea', 'province': 'Basilea'},
    '31': {'city': 'Berna', 'province': 'Berna'},
    '21': {'city': 'Lausana', 'province': 'Vaud'},
    '41': {'city': 'Lucerna', 'province': 'Lucerna'},
    '71': {'city': 'San Galo', 'province': 'San Galo'},
    '81': {'city': 'Coira', 'province': 'Grisones'},
    '91': {'city': 'Lugano', 'province': 'Tesino'},
    '52': {'city': 'Winterthur', 'province': 'Zúrich'},
    '62': {'city': 'Olten', 'province': 'Soleura'},
    '32': {'city': 'Biel', 'province': 'Berna'},
    '26': {'city': 'Friburgo', 'province': 'Friburgo'},
    '27': {'city': 'Sion', 'province': 'Valais'},
    '33': {'city': 'Thun', 'province': 'Berna'},
    '34': {'city': 'Burgdorf', 'province': 'Berna'},
    '55': {'city': 'Rapperswil', 'province': 'San Galo'},
    '56': {'city': 'Baden', 'province': 'Argovia'},
}

# ============================================================
# CÓDIGOS DE ÁREA - GRECIA
# ============================================================
AREA_CODES_GREECE = {
    '21': {'city': 'Atenas', 'province': 'Ática'},
    '231': {'city': 'Tesalónica', 'province': 'Macedonia Central'},
    '241': {'city': 'Larisa', 'province': 'Tesalia'},
    '251': {'city': 'Kavala', 'province': 'Macedonia Oriental'},
    '261': {'city': 'Patras', 'province': 'Grecia Occidental'},
    '271': {'city': 'Trípoli', 'province': 'Peloponeso'},
    '281': {'city': 'Heraclión', 'province': 'Creta'},
}

# ============================================================
# CÓDIGOS DE ÁREA - DINAMARCA
# ============================================================
AREA_CODES_DENMARK = {
    '33': {'city': 'Copenhague', 'province': 'Hovedstaden'},
    '35': {'city': 'Copenhague', 'province': 'Hovedstaden'},
    '86': {'city': 'Aarhus', 'province': 'Jutlandia Central'},
    '87': {'city': 'Aarhus', 'province': 'Jutlandia Central'},
    '98': {'city': 'Aalborg', 'province': 'Jutlandia Septentrional'},
    '65': {'city': 'Odense', 'province': 'Dinamarca Meridional'},
    '79': {'city': 'Esbjerg', 'province': 'Dinamarca Meridional'},
}

# ============================================================
# CÓDIGOS DE ÁREA - SUECIA
# ============================================================
AREA_CODES_SWEDEN = {
    '8': {'city': 'Estocolmo', 'province': 'Estocolmo'},
    '31': {'city': 'Gotemburgo', 'province': 'Västra Götaland'},
    '40': {'city': 'Malmö', 'province': 'Escania'},
    '46': {'city': 'Lund', 'province': 'Escania'},
    '18': {'city': 'Uppsala', 'province': 'Uppsala'},
    '13': {'city': 'Linköping', 'province': 'Östergötland'},
    '90': {'city': 'Umeå', 'province': 'Västerbotten'},
    '920': {'city': 'Luleå', 'province': 'Norrbotten'},
}

# ============================================================
# CÓDIGOS DE ÁREA - FINLANDIA
# ============================================================
AREA_CODES_FINLAND = {
    '9': {'city': 'Helsinki', 'province': 'Uusimaa'},
    '2': {'city': 'Turku', 'province': 'Finlandia Propia'},
    '3': {'city': 'Tampere', 'province': 'Pirkanmaa'},
    '8': {'city': 'Oulu', 'province': 'Ostrobotnia del Norte'},
    '14': {'city': 'Jyväskylä', 'province': 'Finlandia Central'},
    '17': {'city': 'Kuopio', 'province': 'Savonia del Norte'},
    '16': {'city': 'Rovaniemi', 'province': 'Laponia'},
}

# ============================================================
# CÓDIGOS DE ÁREA - NORUEGA
# ============================================================
AREA_CODES_NORWAY = {
    '21': {'city': 'Oslo', 'province': 'Oslo'},
    '22': {'city': 'Oslo', 'province': 'Oslo'},
    '23': {'city': 'Oslo', 'province': 'Oslo'},
    '55': {'city': 'Bergen', 'province': 'Vestland'},
    '73': {'city': 'Trondheim', 'province': 'Trøndelag'},
    '51': {'city': 'Stavanger', 'province': 'Rogaland'},
    '77': {'city': 'Tromsø', 'province': 'Troms'},
    '75': {'city': 'Bodø', 'province': 'Nordland'},
}

# ============================================================
# CÓDIGOS DE ÁREA - POLONIA
# ============================================================
AREA_CODES_POLAND = {
    '22': {'city': 'Varsovia', 'province': 'Mazovia'},
    '12': {'city': 'Cracovia', 'province': 'Pequeña Polonia'},
    '61': {'city': 'Poznań', 'province': 'Gran Polonia'},
    '71': {'city': 'Wrocław', 'province': 'Baja Silesia'},
    '58': {'city': 'Gdańsk', 'province': 'Pomerania'},
    '32': {'city': 'Katowice', 'province': 'Silesia'},
    '42': {'city': 'Łódź', 'province': 'Łódź'},
    '91': {'city': 'Szczecin', 'province': 'Pomerania Occidental'},
    '81': {'city': 'Lublin', 'province': 'Lublin'},
}

# ============================================================
# CÓDIGOS DE ÁREA - CROACIA
# ============================================================
AREA_CODES_CROATIA = {
    '1': {'city': 'Zagreb', 'province': 'Zagreb'},
    '21': {'city': 'Split', 'province': 'Split-Dalmacia'},
    '20': {'city': 'Dubrovnik', 'province': 'Dubrovnik-Neretva'},
    '51': {'city': 'Rijeka', 'province': 'Primorje-Gorski Kotar'},
    '52': {'city': 'Pula', 'province': 'Istria'},
    '31': {'city': 'Osijek', 'province': 'Osijek-Baranja'},
    '23': {'city': 'Zadar', 'province': 'Zadar'},
}


def detect_country(phone_raw: str) -> dict:
    """
    Detecta país, timezone, UTC, ciudad y provincia
    desde el número de teléfono.
    """
    default = {
        'country': 'Desconocido',
        'timezone': 'America/Argentina/Buenos_Aires',
        'utc': 'UTC-3',
        'code': '+?',
        'emoji': '🌎',
        'city': '',
        'province': ''
    }
    
    phone_clean = phone_raw.lstrip('+')
    
    # Detectar país (probar 4, 3, 2, 1 dígitos)
    country_data = None
    country_prefix = ""
    
    for length in [4, 3, 2, 1]:
        prefix = phone_clean[:length]
        if prefix in COUNTRY_MAP:
            country_data = COUNTRY_MAP[prefix].copy()
            country_prefix = prefix
            break
    
    if not country_data:
        return default
    
    # Agregar campos vacíos
    country_data['city'] = ''
    country_data['province'] = ''
    
    # Resto del número
    rest = phone_clean[len(country_prefix):]
    
    # Argentina: quitar 9 de móviles
    if country_prefix == '54' and rest.startswith('9'):
        rest = rest[1:]
    
    # México: quitar 1 de móviles
    if country_prefix == '52' and rest.startswith('1'):
        rest = rest[1:]
    
    # Seleccionar mapa de códigos de área
    area_map = None
    if country_prefix == '54':
        area_map = AREA_CODES_ARGENTINA
    elif country_prefix == '52':
        area_map = AREA_CODES_MEXICO
    elif country_prefix == '57':
        area_map = AREA_CODES_COLOMBIA
    elif country_prefix == '34':
        area_map = AREA_CODES_SPAIN
    elif country_prefix == '55':
        area_map = AREA_CODES_BRAZIL
    elif country_prefix == '49':
        area_map = AREA_CODES_GERMANY
    elif country_prefix == '39':
        area_map = AREA_CODES_ITALY
    elif country_prefix == '1':
        area_map = AREA_CODES_USA
    elif country_prefix == '56':
        area_map = AREA_CODES_CHILE
    elif country_prefix == '51':
        area_map = AREA_CODES_PERU
    elif country_prefix == '58':
        area_map = AREA_CODES_VENEZUELA
    elif country_prefix == '593':
        area_map = AREA_CODES_ECUADOR
    elif country_prefix == '591':
        area_map = AREA_CODES_BOLIVIA
    elif country_prefix == '595':
        area_map = AREA_CODES_PARAGUAY
    elif country_prefix == '598':
        area_map = AREA_CODES_URUGUAY
    elif country_prefix == '502':
        area_map = AREA_CODES_GUATEMALA
    elif country_prefix == '503':
        area_map = AREA_CODES_EL_SALVADOR
    elif country_prefix == '504':
        area_map = AREA_CODES_HONDURAS
    elif country_prefix == '505':
        area_map = AREA_CODES_NICARAGUA
    elif country_prefix == '506':
        area_map = AREA_CODES_COSTA_RICA
    elif country_prefix == '507':
        area_map = AREA_CODES_PANAMA
    elif country_prefix in ['1809', '1829', '1849']:
        area_map = AREA_CODES_DOMINICAN_REPUBLIC
    elif country_prefix in ['1787', '1939']:
        area_map = AREA_CODES_PUERTO_RICO
    elif country_prefix == '351':
        area_map = AREA_CODES_PORTUGAL
    elif country_prefix == '33':
        area_map = AREA_CODES_FRANCE
    elif country_prefix == '44':
        area_map = AREA_CODES_UK
    elif country_prefix == '353':
        area_map = AREA_CODES_IRELAND
    elif country_prefix == '32':
        area_map = AREA_CODES_BELGIUM
    elif country_prefix == '31':
        area_map = AREA_CODES_NETHERLANDS
    elif country_prefix == '43':
        area_map = AREA_CODES_AUSTRIA
    elif country_prefix == '41':
        area_map = AREA_CODES_SWITZERLAND
    elif country_prefix == '30':
        area_map = AREA_CODES_GREECE
    elif country_prefix == '45':
        area_map = AREA_CODES_DENMARK
    elif country_prefix == '46':
        area_map = AREA_CODES_SWEDEN
    elif country_prefix == '358':
        area_map = AREA_CODES_FINLAND
    elif country_prefix == '47':
        area_map = AREA_CODES_NORWAY
    elif country_prefix == '48':
        area_map = AREA_CODES_POLAND
    elif country_prefix == '385':
        area_map = AREA_CODES_CROATIA
    
    if area_map:
        # Intentar con 4, 3, 2, 1 dígitos
        for length in [4, 3, 2, 1]:
            area_code = rest[:length]
            if area_code in area_map:
                country_data['city'] = area_map[area_code]['city']
                country_data['province'] = area_map[area_code]['province']
                break
    
    return country_data


# ============================================================
# TRADUCCIÓN DE MESES
# ============================================================
MESES_ES = {
    'January': 'enero',
    'February': 'febrero',
    'March': 'marzo',
    'April': 'abril',
    'May': 'mayo',
    'June': 'junio',
    'July': 'julio',
    'August': 'agosto',
    'September': 'septiembre',
    'October': 'octubre',
    'November': 'noviembre',
    'December': 'diciembre'
}


def format_fecha_es(dt) -> str:
    """Formatea fecha en español: '29 de diciembre'"""
    dia = dt.strftime("%d").lstrip('0')
    mes_en = dt.strftime("%B")
    mes_es = MESES_ES.get(mes_en, mes_en)
    return f"{dia} de {mes_es}"


# ═══════════════════════════════════════════════════════════════════
# SALARIOS PROMEDIO POR PAÍS (USD/mes) - Para cálculo de facturación
# ═══════════════════════════════════════════════════════════════════

SALARIOS_PROMEDIO = {
    # LATAM
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
    "Costa Rica": 1500,
    "Panamá": 1600,
    "Guatemala": 1200,
    "El Salvador": 1100,
    "Honduras": 900,
    "Nicaragua": 800,
    "República Dominicana": 1300,
    "Cuba": 900,
    "Puerto Rico": 2500,
    
    # EUROPA
    "España": 3500,
    "Alemania": 5000,
    "Francia": 4500,
    "Italia": 3800,
    "Reino Unido": 5500,
    "Portugal": 2500,
    "Países Bajos": 5200,
    "Bélgica": 4800,
    "Suiza": 7500,
    "Austria": 4500,
    "Suecia": 5000,
    "Noruega": 6000,
    "Dinamarca": 5500,
    "Finlandia": 4500,
    "Irlanda": 5000,
    "Polonia": 2000,
    "República Checa": 2200,
    "Grecia": 2000,
    "Rumania": 1500,
    "Bulgaria": 1200,
    
    # NORTEAMÉRICA
    "Estados Unidos": 7000,
    "Canadá": 5500,
    
    # ASIA
    "Japón": 4000,
    "Corea del Sur": 3500,
    "China": 2000,
    "India": 1000,
    "Singapur": 5500,
    "Hong Kong": 4500,
    "Taiwán": 2500,
    "Tailandia": 1200,
    "Malasia": 1500,
    "Indonesia": 800,
    "Filipinas": 800,
    "Vietnam": 700,
    
    # OCEANÍA
    "Australia": 6000,
    "Nueva Zelanda": 5000,
    
    # MEDIO ORIENTE
    "Israel": 4000,
    "Emiratos Árabes Unidos": 4500,
    "Arabia Saudita": 4000,
    "Turquía": 1500,
    
    # ÁFRICA
    "Sudáfrica": 1800,
    "Egipto": 800,
    "Nigeria": 700,
    "Kenia": 800,
    "Marruecos": 1000,
}


def get_salario_promedio(country: str) -> int:
    """
    Retorna el salario promedio en USD/mes para un país.
    Si el país no está en la tabla, retorna 2000 (default).
    """
    return SALARIOS_PROMEDIO.get(country, 2000)
