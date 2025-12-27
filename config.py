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
    '3401': {'city': 'Reconquista', 'province': 'Santa Fe'},
    '3402': {'city': 'Rafaela', 'province': 'Santa Fe'},
    '3404': {'city': 'Casilda', 'province': 'Santa Fe'},
    '3405': {'city': 'San Lorenzo', 'province': 'Santa Fe'},
    '3406': {'city': 'San Jorge', 'province': 'Santa Fe'},
    '3407': {'city': 'Esperanza', 'province': 'Santa Fe'},
    '3408': {'city': 'San Cristóbal', 'province': 'Santa Fe'},
    '3409': {'city': 'San Justo', 'province': 'Santa Fe'},
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
    
    if area_map:
        # Intentar con 4, 3, 2, 1 dígitos
        for length in [4, 3, 2, 1]:
            area_code = rest[:length]
            if area_code in area_map:
                country_data['city'] = area_map[area_code]['city']
                country_data['province'] = area_map[area_code]['province']
                break
    
    return country_data
