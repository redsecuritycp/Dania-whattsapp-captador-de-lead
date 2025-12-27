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
    '55': {'city': 'Ciudad de México', 'province': 'CDMX'},
    '33': {'city': 'Guadalajara', 'province': 'Jalisco'},
    '81': {'city': 'Monterrey', 'province': 'Nuevo León'},
    '222': {'city': 'Puebla', 'province': 'Puebla'},
    '442': {'city': 'Querétaro', 'province': 'Querétaro'},
    '477': {'city': 'León', 'province': 'Guanajuato'},
    '656': {'city': 'Ciudad Juárez', 'province': 'Chihuahua'},
    '664': {'city': 'Tijuana', 'province': 'Baja California'},
    '999': {'city': 'Mérida', 'province': 'Yucatán'},
    '998': {'city': 'Cancún', 'province': 'Quintana Roo'},
    '449': {'city': 'Aguascalientes', 'province': 'Aguascalientes'},
    '614': {'city': 'Chihuahua', 'province': 'Chihuahua'},
    '667': {'city': 'Culiacán', 'province': 'Sinaloa'},
    '669': {'city': 'Mazatlán', 'province': 'Sinaloa'},
    '662': {'city': 'Hermosillo', 'province': 'Sonora'},
    '871': {'city': 'Torreón', 'province': 'Coahuila'},
    '844': {'city': 'Saltillo', 'province': 'Coahuila'},
    '833': {'city': 'Tampico', 'province': 'Tamaulipas'},
    '443': {'city': 'Morelia', 'province': 'Michoacán'},
    '961': {'city': 'Tuxtla Gutiérrez', 'province': 'Chiapas'},
    '951': {'city': 'Oaxaca', 'province': 'Oaxaca'},
    '229': {'city': 'Veracruz', 'province': 'Veracruz'},
    '228': {'city': 'Xalapa', 'province': 'Veracruz'},
    '984': {'city': 'Playa del Carmen', 'province': 'Quintana Roo'},
    '747': {'city': 'Acapulco', 'province': 'Guerrero'},
    '722': {'city': 'Toluca', 'province': 'Estado de México'},
    '777': {'city': 'Cuernavaca', 'province': 'Morelos'},
    '492': {'city': 'Zacatecas', 'province': 'Zacatecas'},
    '444': {'city': 'San Luis Potosí', 'province': 'San Luis Potosí'},
    '322': {'city': 'Puerto Vallarta', 'province': 'Jalisco'},
    '624': {'city': 'Los Cabos', 'province': 'Baja California Sur'},
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
    '11': {'city': 'São Paulo', 'province': 'São Paulo'},
    '21': {'city': 'Rio de Janeiro', 'province': 'Rio de Janeiro'},
    '31': {'city': 'Belo Horizonte', 'province': 'Minas Gerais'},
    '41': {'city': 'Curitiba', 'province': 'Paraná'},
    '51': {'city': 'Porto Alegre', 'province': 'Rio Grande do Sul'},
    '61': {'city': 'Brasília', 'province': 'Distrito Federal'},
    '71': {'city': 'Salvador', 'province': 'Bahia'},
    '81': {'city': 'Recife', 'province': 'Pernambuco'},
    '85': {'city': 'Fortaleza', 'province': 'Ceará'},
    '91': {'city': 'Belém', 'province': 'Pará'},
    '92': {'city': 'Manaus', 'province': 'Amazonas'},
    '47': {'city': 'Joinville', 'province': 'Santa Catarina'},
    '48': {'city': 'Florianópolis', 'province': 'Santa Catarina'},
    '19': {'city': 'Campinas', 'province': 'São Paulo'},
    '27': {'city': 'Vitória', 'province': 'Espírito Santo'},
    '62': {'city': 'Goiânia', 'province': 'Goiás'},
    '67': {'city': 'Campo Grande', 'province': 'Mato Grosso do Sul'},
    '65': {'city': 'Cuiabá', 'province': 'Mato Grosso'},
    '82': {'city': 'Maceió', 'province': 'Alagoas'},
    '84': {'city': 'Natal', 'province': 'Rio Grande do Norte'},
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
    '212': {'city': 'Nueva York', 'province': 'NY'},
    '213': {'city': 'Los Ángeles', 'province': 'CA'},
    '312': {'city': 'Chicago', 'province': 'IL'},
    '305': {'city': 'Miami', 'province': 'FL'},
    '415': {'city': 'San Francisco', 'province': 'CA'},
    '202': {'city': 'Washington D.C.', 'province': 'DC'},
    '617': {'city': 'Boston', 'province': 'MA'},
    '713': {'city': 'Houston', 'province': 'TX'},
    '214': {'city': 'Dallas', 'province': 'TX'},
    '404': {'city': 'Atlanta', 'province': 'GA'},
    '303': {'city': 'Denver', 'province': 'CO'},
    '206': {'city': 'Seattle', 'province': 'WA'},
    '702': {'city': 'Las Vegas', 'province': 'NV'},
    '602': {'city': 'Phoenix', 'province': 'AZ'},
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
    '91': {'city': 'Lugano', 'province': 'Tesino'},
    '52': {'city': 'Winterthur', 'province': 'Zúrich'},
    '32': {'city': 'Biel/Bienne', 'province': 'Berna'},
    '62': {'city': 'Aarau', 'province': 'Argovia'},
    '26': {'city': 'Friburgo', 'province': 'Friburgo'},
    '27': {'city': 'Sion', 'province': 'Valais'},
    '81': {'city': 'Chur', 'province': 'Grisones'},
    '33': {'city': 'Thun', 'province': 'Berna'},
}

# ============================================================
# CÓDIGOS DE ÁREA - GRECIA
# ============================================================
AREA_CODES_GREECE = {
    '21': {'city': 'Atenas', 'province': 'Ática'},
    '231': {'city': 'Salónica', 'province': 'Macedonia Central'},
    '261': {'city': 'Patras', 'province': 'Grecia Occidental'},
    '281': {'city': 'Heraclión', 'province': 'Creta'},
    '241': {'city': 'Rodas', 'province': 'Egeo Meridional'},
    '251': {'city': 'Kavala', 'province': 'Macedonia Oriental'},
    '2421': {'city': 'Volos', 'province': 'Tesalia'},
    '2651': {'city': 'Ioánina', 'province': 'Epiro'},
    '2661': {'city': 'Corfú', 'province': 'Islas Jónicas'},
    '2810': {'city': 'Chania', 'province': 'Creta'},
}

# ============================================================
# CÓDIGOS DE ÁREA - DINAMARCA
# ============================================================
AREA_CODES_DENMARK = {
    '33': {'city': 'Copenhague', 'province': 'Capital'},
    '38': {'city': 'Copenhague', 'province': 'Capital'},
    '39': {'city': 'Copenhague Norte', 'province': 'Capital'},
    '45': {'city': 'Copenhague', 'province': 'Capital'},
    '86': {'city': 'Aarhus', 'province': 'Jutlandia Central'},
    '98': {'city': 'Aalborg', 'province': 'Jutlandia del Norte'},
    '66': {'city': 'Odense', 'province': 'Dinamarca Meridional'},
    '75': {'city': 'Vejle', 'province': 'Dinamarca Meridional'},
    '76': {'city': 'Fredericia', 'province': 'Dinamarca Meridional'},
}

# ============================================================
# CÓDIGOS DE ÁREA - SUECIA
# ============================================================
AREA_CODES_SWEDEN = {
    '8': {'city': 'Estocolmo', 'province': 'Estocolmo'},
    '31': {'city': 'Gotemburgo', 'province': 'Västra Götaland'},
    '40': {'city': 'Malmö', 'province': 'Escania'},
    '18': {'city': 'Uppsala', 'province': 'Uppsala'},
    '13': {'city': 'Linköping', 'province': 'Östergötland'},
    '19': {'city': 'Örebro', 'province': 'Örebro'},
    '21': {'city': 'Västerås', 'province': 'Västmanland'},
    '33': {'city': 'Borås', 'province': 'Västra Götaland'},
    '36': {'city': 'Jönköping', 'province': 'Jönköping'},
    '42': {'city': 'Helsingborg', 'province': 'Escania'},
    '46': {'city': 'Lund', 'province': 'Escania'},
    '54': {'city': 'Karlstad', 'province': 'Värmland'},
    '60': {'city': 'Sundsvall', 'province': 'Västernorrland'},
    '63': {'city': 'Östersund', 'province': 'Jämtland'},
    '90': {'city': 'Umeå', 'province': 'Västerbotten'},
    '920': {'city': 'Luleå', 'province': 'Norrbotten'},
}

# ============================================================
# CÓDIGOS DE ÁREA - FINLANDIA
# ============================================================
AREA_CODES_FINLAND = {
    '9': {'city': 'Helsinki', 'province': 'Uusimaa'},
    '2': {'city': 'Turku', 'province': 'Finlandia Sudoccidental'},
    '3': {'city': 'Tampere', 'province': 'Pirkanmaa'},
    '5': {'city': 'Lahti', 'province': 'Päijät-Häme'},
    '6': {'city': 'Vaasa', 'province': 'Ostrobotnia'},
    '8': {'city': 'Oulu', 'province': 'Ostrobotnia del Norte'},
    '13': {'city': 'Joensuu', 'province': 'Carelia del Norte'},
    '14': {'city': 'Jyväskylä', 'province': 'Finlandia Central'},
    '15': {'city': 'Mikkeli', 'province': 'Savonia del Sur'},
    '16': {'city': 'Rovaniemi', 'province': 'Laponia'},
    '17': {'city': 'Kuopio', 'province': 'Savonia del Norte'},
    '19': {'city': 'Espoo', 'province': 'Uusimaa'},
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
    '69': {'city': 'Fredrikstad', 'province': 'Viken'},
    '33': {'city': 'Drammen', 'province': 'Viken'},
    '32': {'city': 'Kristiansand', 'province': 'Agder'},
    '75': {'city': 'Bodø', 'province': 'Nordland'},
    '77': {'city': 'Tromsø', 'province': 'Troms og Finnmark'},
    '62': {'city': 'Hamar', 'province': 'Innlandet'},
    '61': {'city': 'Lillehammer', 'province': 'Innlandet'},
    '70': {'city': 'Ålesund', 'province': 'Møre og Romsdal'},
}

# ============================================================
# CÓDIGOS DE ÁREA - POLONIA
# ============================================================
AREA_CODES_POLAND = {
    '22': {'city': 'Varsovia', 'province': 'Mazovia'},
    '12': {'city': 'Cracovia', 'province': 'Pequeña Polonia'},
    '71': {'city': 'Breslavia', 'province': 'Baja Silesia'},
    '61': {'city': 'Poznan', 'province': 'Gran Polonia'},
    '58': {'city': 'Gdansk', 'province': 'Pomerania'},
    '32': {'city': 'Katowice', 'province': 'Silesia'},
    '42': {'city': 'Lodz', 'province': 'Lodz'},
    '91': {'city': 'Szczecin', 'province': 'Pomerania Occidental'},
    '85': {'city': 'Bialystok', 'province': 'Podlaquia'},
    '81': {'city': 'Lublin', 'province': 'Lublin'},
    '89': {'city': 'Olsztyn', 'province': 'Varmia y Masuria'},
    '52': {'city': 'Bydgoszcz', 'province': 'Cuyavia y Pomerania'},
    '56': {'city': 'Torun', 'province': 'Cuyavia y Pomerania'},
    '17': {'city': 'Rzeszów', 'province': 'Subcarpacia'},
    '41': {'city': 'Kielce', 'province': 'Santa Cruz'},
    '68': {'city': 'Zielona Góra', 'province': 'Lubusz'},
    '77': {'city': 'Opole', 'province': 'Opole'},
    '15': {'city': 'Tarnów', 'province': 'Pequeña Polonia'},
}

# ============================================================
# CÓDIGOS DE ÁREA - CROACIA
# ============================================================
AREA_CODES_CROATIA = {
    '1': {'city': 'Zagreb', 'province': 'Zagreb'},
    '21': {'city': 'Split', 'province': 'Split-Dalmacia'},
    '51': {'city': 'Rijeka', 'province': 'Primorje-Gorski Kotar'},
    '31': {'city': 'Osijek', 'province': 'Osijek-Baranja'},
    '23': {'city': 'Zadar', 'province': 'Zadar'},
    '52': {'city': 'Pula', 'province': 'Istria'},
    '42': {'city': 'Varaždin', 'province': 'Varaždin'},
    '20': {'city': 'Dubrovnik', 'province': 'Dubrovnik-Neretva'},
    '35': {'city': 'Slavonski Brod', 'province': 'Brod-Posavina'},
    '47': {'city': 'Karlovac', 'province': 'Karlovac'},
    '48': {'city': 'Koprivnica', 'province': 'Koprivnica-Križevci'},
    '49': {'city': 'Krapina', 'province': 'Krapina-Zagorje'},
    '44': {'city': 'Sisak', 'province': 'Sisak-Moslavina'},
    '43': {'city': 'Bjelovar', 'province': 'Bjelovar-Bilogora'},
    '22': {'city': 'Šibenik', 'province': 'Šibenik-Knin'},
    '53': {'city': 'Gospić', 'province': 'Lika-Senj'},
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
