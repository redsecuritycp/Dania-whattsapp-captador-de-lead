"""
Configuración centralizada para DANIA/Fortia
"""
import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# OPENAI
# =============================================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# =============================================================================
# MONGODB
# =============================================================================
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "dania_fortia")
MONGODB_DATABASE = MONGODB_DB_NAME

# =============================================================================
# WHATSAPP
# =============================================================================
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "fortia2024")

# =============================================================================
# TAVILY (Búsqueda web)
# =============================================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# =============================================================================
# JINA AI (Extracción web)
# =============================================================================
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")

# =============================================================================
# FIRECRAWL (Extracción web avanzada)
# =============================================================================
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# =============================================================================
# APIFY (Crawler de noticias)
# =============================================================================
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN", "")

# =============================================================================
# GMAIL
# =============================================================================
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL",
                                    "pansapablo@gmail.com")

# =============================================================================
# CAL.COM
# =============================================================================
CALCOM_API_KEY = os.environ.get("CALCOM_API_KEY", "")
CALCOM_EVENT_URL = os.environ.get(
    "CALCOM_EVENT_URL", "https://cal.com/agencia-fortia-hviska/60min")

# =============================================================================
# GOOGLE CUSTOM SEARCH (para LinkedIn)
# =============================================================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_SEARCH_CX", "33f5cc1337cde4799")

# =============================================================================
# MAPEO DE PAÍSES COMPLETO
# LATAM + USA/Canadá + Unión Europea completa
# =============================================================================
COUNTRY_MAP = {
    # ═══════════════════════════════════════════════════════════════════════
    # LATINOAMÉRICA HISPANOHABLANTE
    # ═══════════════════════════════════════════════════════════════════════
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
    '1939': {
        'country': 'Puerto Rico',
        'timezone': 'America/Puerto_Rico',
        'utc': 'UTC-4',
        'code': '+1939',
        'emoji': '🇵🇷'
    },
    # ═══════════════════════════════════════════════════════════════════════
    # BRASIL
    # ═══════════════════════════════════════════════════════════════════════
    '55': {
        'country': 'Brasil',
        'timezone': 'America/Sao_Paulo',
        'utc': 'UTC-3',
        'code': '+55',
        'emoji': '🇧🇷'
    },
    # ═══════════════════════════════════════════════════════════════════════
    # ESTADOS UNIDOS Y CANADÁ
    # ═══════════════════════════════════════════════════════════════════════
    '1': {
        'country': 'Estados Unidos',
        'timezone': 'America/New_York',
        'utc': 'UTC-5',
        'code': '+1',
        'emoji': '🇺🇸'
    },
    # ═══════════════════════════════════════════════════════════════════════
    # UNIÓN EUROPEA COMPLETA
    # ═══════════════════════════════════════════════════════════════════════
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

# =============================================================================
# CÓDIGOS DE ÁREA → CIUDAD/PROVINCIA
# Solo para países donde es posible detectar ubicación
# =============================================================================

# ARGENTINA: formato +54 9 XXXX (móviles) o +54 XXXX (fijos)
AREA_CODES_ARGENTINA = {
    # Buenos Aires / AMBA
    '11': {
        'city': 'Buenos Aires',
        'province': 'Buenos Aires'
    },
    # Santa Fe
    '341': {
        'city': 'Rosario',
        'province': 'Santa Fe'
    },
    '342': {
        'city': 'Santa Fe',
        'province': 'Santa Fe'
    },
    '3401': {
        'city': 'Reconquista',
        'province': 'Santa Fe'
    },
    '3402': {
        'city': 'Rafaela',
        'province': 'Santa Fe'
    },
    '3404': {
        'city': 'Casilda',
        'province': 'Santa Fe'
    },
    '3405': {
        'city': 'San Lorenzo',
        'province': 'Santa Fe'
    },
    '3406': {
        'city': 'San Jorge',
        'province': 'Santa Fe'
    },
    '3407': {
        'city': 'Esperanza',
        'province': 'Santa Fe'
    },
    '3408': {
        'city': 'San Cristóbal',
        'province': 'Santa Fe'
    },
    '3409': {
        'city': 'San Justo',
        'province': 'Santa Fe'
    },
    '3460': {
        'city': 'Cañada de Gómez',
        'province': 'Santa Fe'
    },
    '3462': {
        'city': 'Venado Tuerto',
        'province': 'Santa Fe'
    },
    '3464': {
        'city': 'Rufino',
        'province': 'Santa Fe'
    },
    '3465': {
        'city': 'Firmat',
        'province': 'Santa Fe'
    },
    '3466': {
        'city': 'Villa Constitución',
        'province': 'Santa Fe'
    },
    '3469': {
        'city': 'Arroyo Seco',
        'province': 'Santa Fe'
    },
    '3471': {
        'city': 'Coronda',
        'province': 'Santa Fe'
    },
    '3482': {
        'city': 'Gálvez',
        'province': 'Santa Fe'
    },
    '3483': {
        'city': 'Vera',
        'province': 'Santa Fe'
    },
    '3491': {
        'city': 'Ceres',
        'province': 'Santa Fe'
    },
    '3492': {
        'city': 'Sunchales',
        'province': 'Santa Fe'
    },
    '3493': {
        'city': 'Las Toscas',
        'province': 'Santa Fe'
    },
    '3496': {
        'city': 'Tostado',
        'province': 'Santa Fe'
    },
    # Córdoba
    '351': {
        'city': 'Córdoba',
        'province': 'Córdoba'
    },
    '352': {
        'city': 'Villa Carlos Paz',
        'province': 'Córdoba'
    },
    '353': {
        'city': 'Villa María',
        'province': 'Córdoba'
    },
    '354': {
        'city': 'Río Cuarto',
        'province': 'Córdoba'
    },
    '3521': {
        'city': 'Dean Funes',
        'province': 'Córdoba'
    },
    '3522': {
        'city': 'Villa Dolores',
        'province': 'Córdoba'
    },
    '3524': {
        'city': 'Villa del Rosario',
        'province': 'Córdoba'
    },
    '3525': {
        'city': 'Jesús María',
        'province': 'Córdoba'
    },
    '3532': {
        'city': 'Oliva',
        'province': 'Córdoba'
    },
    '3533': {
        'city': 'Las Varillas',
        'province': 'Córdoba'
    },
    '3537': {
        'city': 'Bell Ville',
        'province': 'Córdoba'
    },
    '3541': {
        'city': 'Alta Gracia',
        'province': 'Córdoba'
    },
    '3543': {
        'city': 'Cosquín',
        'province': 'Córdoba'
    },
    '3544': {
        'city': 'La Falda',
        'province': 'Córdoba'
    },
    '3546': {
        'city': 'Santa Rosa de Calamuchita',
        'province': 'Córdoba'
    },
    '3547': {
        'city': 'Villa General Belgrano',
        'province': 'Córdoba'
    },
    '3548': {
        'city': 'Cruz del Eje',
        'province': 'Córdoba'
    },
    '3549': {
        'city': 'Mina Clavero',
        'province': 'Córdoba'
    },
    '3562': {
        'city': 'Marcos Juárez',
        'province': 'Córdoba'
    },
    '3563': {
        'city': 'San Francisco',
        'province': 'Córdoba'
    },
    '3564': {
        'city': 'Morteros',
        'province': 'Córdoba'
    },
    '3571': {
        'city': 'Río Tercero',
        'province': 'Córdoba'
    },
    '3572': {
        'city': 'Río Segundo',
        'province': 'Córdoba'
    },
    '3574': {
        'city': 'Arroyito',
        'province': 'Córdoba'
    },
    '3575': {
        'city': 'La Carlota',
        'province': 'Córdoba'
    },
    '3576': {
        'city': 'General Deheza',
        'province': 'Córdoba'
    },
    '3582': {
        'city': 'Sampacho',
        'province': 'Córdoba'
    },
    '3583': {
        'city': 'Vicuña Mackenna',
        'province': 'Córdoba'
    },
    '3584': {
        'city': 'Huinca Renancó',
        'province': 'Córdoba'
    },
    '3585': {
        'city': 'Laboulaye',
        'province': 'Córdoba'
    },
    # Mendoza
    '261': {
        'city': 'Mendoza',
        'province': 'Mendoza'
    },
    '260': {
        'city': 'San Rafael',
        'province': 'Mendoza'
    },
    '262': {
        'city': 'Tunuyán',
        'province': 'Mendoza'
    },
    '263': {
        'city': 'San Martín',
        'province': 'Mendoza'
    },
    '2622': {
        'city': 'Tupungato',
        'province': 'Mendoza'
    },
    '2624': {
        'city': 'Alvear',
        'province': 'Mendoza'
    },
    '2625': {
        'city': 'General Alvear',
        'province': 'Mendoza'
    },
    '2626': {
        'city': 'La Paz',
        'province': 'Mendoza'
    },
    # Tucumán
    '381': {
        'city': 'San Miguel de Tucumán',
        'province': 'Tucumán'
    },
    '3863': {
        'city': 'Monteros',
        'province': 'Tucumán'
    },
    '3865': {
        'city': 'Concepción',
        'province': 'Tucumán'
    },
    '3867': {
        'city': 'Tafí del Valle',
        'province': 'Tucumán'
    },
    # Entre Ríos
    '343': {
        'city': 'Paraná',
        'province': 'Entre Ríos'
    },
    '345': {
        'city': 'Concordia',
        'province': 'Entre Ríos'
    },
    '3435': {
        'city': 'Nogoyá',
        'province': 'Entre Ríos'
    },
    '3436': {
        'city': 'Victoria',
        'province': 'Entre Ríos'
    },
    '3437': {
        'city': 'La Paz',
        'province': 'Entre Ríos'
    },
    '3438': {
        'city': 'Bovril',
        'province': 'Entre Ríos'
    },
    '3442': {
        'city': 'Concepción del Uruguay',
        'province': 'Entre Ríos'
    },
    '3444': {
        'city': 'Gualeguay',
        'province': 'Entre Ríos'
    },
    '3445': {
        'city': 'Rosario del Tala',
        'province': 'Entre Ríos'
    },
    '3446': {
        'city': 'Gualeguaychú',
        'province': 'Entre Ríos'
    },
    '3447': {
        'city': 'Colón',
        'province': 'Entre Ríos'
    },
    '3454': {
        'city': 'Chajarí',
        'province': 'Entre Ríos'
    },
    '3456': {
        'city': 'Federación',
        'province': 'Entre Ríos'
    },
    '3458': {
        'city': 'San José de Feliciano',
        'province': 'Entre Ríos'
    },
    # Salta
    '387': {
        'city': 'Salta',
        'province': 'Salta'
    },
    '3873': {
        'city': 'Tartagal',
        'province': 'Salta'
    },
    '3876': {
        'city': 'San Ramón de la Nueva Orán',
        'province': 'Salta'
    },
    '3878': {
        'city': 'Cafayate',
        'province': 'Salta'
    },
    # Jujuy
    '388': {
        'city': 'San Salvador de Jujuy',
        'province': 'Jujuy'
    },
    '3884': {
        'city': 'San Pedro de Jujuy',
        'province': 'Jujuy'
    },
    '3885': {
        'city': 'La Quiaca',
        'province': 'Jujuy'
    },
    '3886': {
        'city': 'Libertador Gral. San Martín',
        'province': 'Jujuy'
    },
    '3887': {
        'city': 'Humahuaca',
        'province': 'Jujuy'
    },
    # Misiones
    '376': {
        'city': 'Posadas',
        'province': 'Misiones'
    },
    '3751': {
        'city': 'Eldorado',
        'province': 'Misiones'
    },
    '3752': {
        'city': 'Oberá',
        'province': 'Misiones'
    },
    '3754': {
        'city': 'Leandro N. Alem',
        'province': 'Misiones'
    },
    '3755': {
        'city': 'Puerto Rico',
        'province': 'Misiones'
    },
    '3757': {
        'city': 'Puerto Iguazú',
        'province': 'Misiones'
    },
    '3758': {
        'city': 'Apóstoles',
        'province': 'Misiones'
    },
    # Corrientes
    '379': {
        'city': 'Corrientes',
        'province': 'Corrientes'
    },
    '3772': {
        'city': 'Paso de los Libres',
        'province': 'Corrientes'
    },
    '3773': {
        'city': 'Mercedes',
        'province': 'Corrientes'
    },
    '3774': {
        'city': 'Curuzú Cuatiá',
        'province': 'Corrientes'
    },
    '3775': {
        'city': 'Monte Caseros',
        'province': 'Corrientes'
    },
    '3777': {
        'city': 'Goya',
        'province': 'Corrientes'
    },
    '3781': {
        'city': 'Esquina',
        'province': 'Corrientes'
    },
    '3782': {
        'city': 'Ituzaingó',
        'province': 'Corrientes'
    },
    '3786': {
        'city': 'Santo Tomé',
        'province': 'Corrientes'
    },
    # Chaco
    '362': {
        'city': 'Resistencia',
        'province': 'Chaco'
    },
    '364': {
        'city': 'Presidencia Roque Sáenz Peña',
        'province': 'Chaco'
    },
    '3624': {
        'city': 'Villa Ángela',
        'province': 'Chaco'
    },
    '3644': {
        'city': 'Gral. José de San Martín',
        'province': 'Chaco'
    },
    '3731': {
        'city': 'Charata',
        'province': 'Chaco'
    },
    '3734': {
        'city': 'Juan José Castelli',
        'province': 'Chaco'
    },
    # Formosa
    '370': {
        'city': 'Formosa',
        'province': 'Formosa'
    },
    '3704': {
        'city': 'Clorinda',
        'province': 'Formosa'
    },
    '3711': {
        'city': 'Pirané',
        'province': 'Formosa'
    },
    '3716': {
        'city': 'El Colorado',
        'province': 'Formosa'
    },
    '3718': {
        'city': 'Las Lomitas',
        'province': 'Formosa'
    },
    # Santiago del Estero
    '385': {
        'city': 'Santiago del Estero',
        'province': 'Santiago del Estero'
    },
    '3841': {
        'city': 'Añatuya',
        'province': 'Santiago del Estero'
    },
    '3843': {
        'city': 'Quimilí',
        'province': 'Santiago del Estero'
    },
    '3844': {
        'city': 'Frías',
        'province': 'Santiago del Estero'
    },
    '3846': {
        'city': 'Termas de Río Hondo',
        'province': 'Santiago del Estero'
    },
    '3854': {
        'city': 'La Banda',
        'province': 'Santiago del Estero'
    },
    # San Juan
    '264': {
        'city': 'San Juan',
        'province': 'San Juan'
    },
    '2646': {
        'city': 'Jáchal',
        'province': 'San Juan'
    },
    '2647': {
        'city': 'San José de Jáchal',
        'province': 'San Juan'
    },
    '2648': {
        'city': 'Calingasta',
        'province': 'San Juan'
    },
    # San Luis
    '266': {
        'city': 'San Luis',
        'province': 'San Luis'
    },
    '2652': {
        'city': 'Mercedes',
        'province': 'San Luis'
    },
    '2656': {
        'city': 'Villa Mercedes',
        'province': 'San Luis'
    },
    '2657': {
        'city': 'Merlo',
        'province': 'San Luis'
    },
    # La Rioja
    '380': {
        'city': 'La Rioja',
        'province': 'La Rioja'
    },
    '3825': {
        'city': 'Chilecito',
        'province': 'La Rioja'
    },
    '3826': {
        'city': 'Aimogasta',
        'province': 'La Rioja'
    },
    '3827': {
        'city': 'Chamical',
        'province': 'La Rioja'
    },
    # Catamarca
    '383': {
        'city': 'San Fernando del Valle',
        'province': 'Catamarca'
    },
    '3832': {
        'city': 'Andalgalá',
        'province': 'Catamarca'
    },
    '3833': {
        'city': 'Tinogasta',
        'province': 'Catamarca'
    },
    '3835': {
        'city': 'Belén',
        'province': 'Catamarca'
    },
    '3837': {
        'city': 'Santa María',
        'province': 'Catamarca'
    },
    '3838': {
        'city': 'Recreo',
        'province': 'Catamarca'
    },
    # La Pampa
    '2954': {
        'city': 'Santa Rosa',
        'province': 'La Pampa'
    },
    '2952': {
        'city': 'General Pico',
        'province': 'La Pampa'
    },
    '2953': {
        'city': 'General Acha',
        'province': 'La Pampa'
    },
    '2302': {
        'city': 'Realicó',
        'province': 'La Pampa'
    },
    # Neuquén
    '299': {
        'city': 'Neuquén',
        'province': 'Neuquén'
    },
    '2942': {
        'city': 'San Martín de los Andes',
        'province': 'Neuquén'
    },
    '2946': {
        'city': 'Villa La Angostura',
        'province': 'Neuquén'
    },
    '298': {
        'city': 'Zapala',
        'province': 'Neuquén'
    },
    '2972': {
        'city': 'Junín de los Andes',
        'province': 'Neuquén'
    },
    '2948': {
        'city': 'Chos Malal',
        'province': 'Neuquén'
    },
    # Río Negro
    '2920': {
        'city': 'Viedma',
        'province': 'Río Negro'
    },
    '294': {
        'city': 'San Carlos de Bariloche',
        'province': 'Río Negro'
    },
    '2941': {
        'city': 'El Bolsón',
        'province': 'Río Negro'
    },
    '2931': {
        'city': 'Cipolletti',
        'province': 'Río Negro'
    },
    '2934': {
        'city': 'General Roca',
        'province': 'Río Negro'
    },
    '2940': {
        'city': 'Ingeniero Jacobacci',
        'province': 'Río Negro'
    },
    # Chubut
    '280': {
        'city': 'Rawson',
        'province': 'Chubut'
    },
    '297': {
        'city': 'Comodoro Rivadavia',
        'province': 'Chubut'
    },
    '2945': {
        'city': 'Esquel',
        'province': 'Chubut'
    },
    '2965': {
        'city': 'Trelew',
        'province': 'Chubut'
    },
    '2804': {
        'city': 'Puerto Madryn',
        'province': 'Chubut'
    },
    # Santa Cruz
    '2966': {
        'city': 'Río Gallegos',
        'province': 'Santa Cruz'
    },
    '2902': {
        'city': 'El Calafate',
        'province': 'Santa Cruz'
    },
    '2903': {
        'city': 'Caleta Olivia',
        'province': 'Santa Cruz'
    },
    '2962': {
        'city': 'Puerto Deseado',
        'province': 'Santa Cruz'
    },
    '2963': {
        'city': 'Perito Moreno',
        'province': 'Santa Cruz'
    },
    # Tierra del Fuego
    '2901': {
        'city': 'Ushuaia',
        'province': 'Tierra del Fuego'
    },
    '2964': {
        'city': 'Río Grande',
        'province': 'Tierra del Fuego'
    },
    # Buenos Aires interior
    '221': {
        'city': 'La Plata',
        'province': 'Buenos Aires'
    },
    '223': {
        'city': 'Mar del Plata',
        'province': 'Buenos Aires'
    },
    '2241': {
        'city': 'Chascomús',
        'province': 'Buenos Aires'
    },
    '2245': {
        'city': 'Dolores',
        'province': 'Buenos Aires'
    },
    '2252': {
        'city': 'San Clemente del Tuyú',
        'province': 'Buenos Aires'
    },
    '2254': {
        'city': 'Pinamar',
        'province': 'Buenos Aires'
    },
    '2255': {
        'city': 'Villa Gesell',
        'province': 'Buenos Aires'
    },
    '2257': {
        'city': 'Mar de Ajó',
        'province': 'Buenos Aires'
    },
    '2262': {
        'city': 'Necochea',
        'province': 'Buenos Aires'
    },
    '2266': {
        'city': 'Balcarce',
        'province': 'Buenos Aires'
    },
    '2281': {
        'city': 'Azul',
        'province': 'Buenos Aires'
    },
    '2284': {
        'city': 'Olavarría',
        'province': 'Buenos Aires'
    },
    '2291': {
        'city': 'Miramar',
        'province': 'Buenos Aires'
    },
    '2293': {
        'city': 'Tandil',
        'province': 'Buenos Aires'
    },
    '2314': {
        'city': 'Bolívar',
        'province': 'Buenos Aires'
    },
    '2316': {
        'city': '25 de Mayo',
        'province': 'Buenos Aires'
    },
    '2317': {
        'city': '9 de Julio',
        'province': 'Buenos Aires'
    },
    '2323': {
        'city': 'Luján',
        'province': 'Buenos Aires'
    },
    '2324': {
        'city': 'Mercedes',
        'province': 'Buenos Aires'
    },
    '2326': {
        'city': 'San Antonio de Areco',
        'province': 'Buenos Aires'
    },
    '2342': {
        'city': 'Bragado',
        'province': 'Buenos Aires'
    },
    '2344': {
        'city': 'Saladillo',
        'province': 'Buenos Aires'
    },
    '2346': {
        'city': 'Chivilcoy',
        'province': 'Buenos Aires'
    },
    '2352': {
        'city': 'Chacabuco',
        'province': 'Buenos Aires'
    },
    '2353': {
        'city': 'Junín',
        'province': 'Buenos Aires'
    },
    '2355': {
        'city': 'Lincoln',
        'province': 'Buenos Aires'
    },
    '2362': {
        'city': 'Pergamino',
        'province': 'Buenos Aires'
    },
    '2392': {
        'city': 'Trenque Lauquen',
        'province': 'Buenos Aires'
    },
    '291': {
        'city': 'Bahía Blanca',
        'province': 'Buenos Aires'
    },
    '2921': {
        'city': 'Coronel Dorrego',
        'province': 'Buenos Aires'
    },
    '2922': {
        'city': 'Coronel Pringles',
        'province': 'Buenos Aires'
    },
    '2923': {
        'city': 'Pigüé',
        'province': 'Buenos Aires'
    },
    '2926': {
        'city': 'Coronel Suárez',
        'province': 'Buenos Aires'
    },
    '2932': {
        'city': 'Punta Alta',
        'province': 'Buenos Aires'
    },
}

# MÉXICO
AREA_CODES_MEXICO = {
    '55': {
        'city': 'Ciudad de México',
        'province': 'CDMX'
    },
    '33': {
        'city': 'Guadalajara',
        'province': 'Jalisco'
    },
    '81': {
        'city': 'Monterrey',
        'province': 'Nuevo León'
    },
    '222': {
        'city': 'Puebla',
        'province': 'Puebla'
    },
    '442': {
        'city': 'Querétaro',
        'province': 'Querétaro'
    },
    '477': {
        'city': 'León',
        'province': 'Guanajuato'
    },
    '656': {
        'city': 'Ciudad Juárez',
        'province': 'Chihuahua'
    },
    '664': {
        'city': 'Tijuana',
        'province': 'Baja California'
    },
    '999': {
        'city': 'Mérida',
        'province': 'Yucatán'
    },
    '998': {
        'city': 'Cancún',
        'province': 'Quintana Roo'
    },
    '449': {
        'city': 'Aguascalientes',
        'province': 'Aguascalientes'
    },
    '614': {
        'city': 'Chihuahua',
        'province': 'Chihuahua'
    },
    '618': {
        'city': 'Durango',
        'province': 'Durango'
    },
    '686': {
        'city': 'Mexicali',
        'province': 'Baja California'
    },
    '667': {
        'city': 'Culiacán',
        'province': 'Sinaloa'
    },
    '669': {
        'city': 'Mazatlán',
        'province': 'Sinaloa'
    },
    '662': {
        'city': 'Hermosillo',
        'province': 'Sonora'
    },
    '871': {
        'city': 'Torreón',
        'province': 'Coahuila'
    },
    '844': {
        'city': 'Saltillo',
        'province': 'Coahuila'
    },
    '833': {
        'city': 'Tampico',
        'province': 'Tamaulipas'
    },
    '868': {
        'city': 'Reynosa',
        'province': 'Tamaulipas'
    },
    '867': {
        'city': 'Matamoros',
        'province': 'Tamaulipas'
    },
    '899': {
        'city': 'Nuevo Laredo',
        'province': 'Tamaulipas'
    },
    '443': {
        'city': 'Morelia',
        'province': 'Michoacán'
    },
    '961': {
        'city': 'Tuxtla Gutiérrez',
        'province': 'Chiapas'
    },
    '951': {
        'city': 'Oaxaca',
        'province': 'Oaxaca'
    },
    '229': {
        'city': 'Veracruz',
        'province': 'Veracruz'
    },
    '228': {
        'city': 'Xalapa',
        'province': 'Veracruz'
    },
    '981': {
        'city': 'Campeche',
        'province': 'Campeche'
    },
    '984': {
        'city': 'Playa del Carmen',
        'province': 'Quintana Roo'
    },
    '747': {
        'city': 'Acapulco',
        'province': 'Guerrero'
    },
    '771': {
        'city': 'Pachuca',
        'province': 'Hidalgo'
    },
    '722': {
        'city': 'Toluca',
        'province': 'Estado de México'
    },
    '777': {
        'city': 'Cuernavaca',
        'province': 'Morelos'
    },
    '492': {
        'city': 'Zacatecas',
        'province': 'Zacatecas'
    },
    '444': {
        'city': 'San Luis Potosí',
        'province': 'San Luis Potosí'
    },
    '312': {
        'city': 'Colima',
        'province': 'Colima'
    },
    '311': {
        'city': 'Tepic',
        'province': 'Nayarit'
    },
    '322': {
        'city': 'Puerto Vallarta',
        'province': 'Jalisco'
    },
    '612': {
        'city': 'La Paz',
        'province': 'Baja California Sur'
    },
    '624': {
        'city': 'Los Cabos',
        'province': 'Baja California Sur'
    },
}

# COLOMBIA
AREA_CODES_COLOMBIA = {
    '1': {
        'city': 'Bogotá',
        'province': 'Cundinamarca'
    },
    '2': {
        'city': 'Cali',
        'province': 'Valle del Cauca'
    },
    '4': {
        'city': 'Medellín',
        'province': 'Antioquia'
    },
    '5': {
        'city': 'Barranquilla',
        'province': 'Atlántico'
    },
    '6': {
        'city': 'Pereira',
        'province': 'Risaralda'
    },
    '7': {
        'city': 'Bucaramanga',
        'province': 'Santander'
    },
    '8': {
        'city': 'Cúcuta',
        'province': 'Norte de Santander'
    },
    '300': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '301': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '310': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '311': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '312': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '313': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '314': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '315': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '316': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '317': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '318': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '319': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '320': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
    '321': {
        'city': 'Nacional',
        'province': 'Colombia'
    },
}

# ESPAÑA
AREA_CODES_SPAIN = {
    '91': {
        'city': 'Madrid',
        'province': 'Madrid'
    },
    '93': {
        'city': 'Barcelona',
        'province': 'Cataluña'
    },
    '96': {
        'city': 'Valencia',
        'province': 'Valencia'
    },
    '95': {
        'city': 'Sevilla',
        'province': 'Andalucía'
    },
    '94': {
        'city': 'Bilbao',
        'province': 'País Vasco'
    },
    '98': {
        'city': 'Oviedo',
        'province': 'Asturias'
    },
    '981': {
        'city': 'A Coruña',
        'province': 'Galicia'
    },
    '986': {
        'city': 'Vigo',
        'province': 'Galicia'
    },
    '988': {
        'city': 'Ourense',
        'province': 'Galicia'
    },
    '976': {
        'city': 'Zaragoza',
        'province': 'Aragón'
    },
    '974': {
        'city': 'Huesca',
        'province': 'Aragón'
    },
    '971': {
        'city': 'Palma de Mallorca',
        'province': 'Islas Baleares'
    },
    '928': {
        'city': 'Las Palmas',
        'province': 'Canarias'
    },
    '922': {
        'city': 'Santa Cruz de Tenerife',
        'province': 'Canarias'
    },
    '952': {
        'city': 'Málaga',
        'province': 'Andalucía'
    },
    '954': {
        'city': 'Sevilla',
        'province': 'Andalucía'
    },
    '956': {
        'city': 'Cádiz',
        'province': 'Andalucía'
    },
    '957': {
        'city': 'Córdoba',
        'province': 'Andalucía'
    },
    '958': {
        'city': 'Granada',
        'province': 'Andalucía'
    },
    '959': {
        'city': 'Huelva',
        'province': 'Andalucía'
    },
    '968': {
        'city': 'Murcia',
        'province': 'Murcia'
    },
    '965': {
        'city': 'Alicante',
        'province': 'Valencia'
    },
    '964': {
        'city': 'Castellón',
        'province': 'Valencia'
    },
    '983': {
        'city': 'Valladolid',
        'province': 'Castilla y León'
    },
    '987': {
        'city': 'León',
        'province': 'Castilla y León'
    },
    '923': {
        'city': 'Salamanca',
        'province': 'Castilla y León'
    },
    '947': {
        'city': 'Burgos',
        'province': 'Castilla y León'
    },
    '948': {
        'city': 'Pamplona',
        'province': 'Navarra'
    },
    '943': {
        'city': 'San Sebastián',
        'province': 'País Vasco'
    },
    '945': {
        'city': 'Vitoria',
        'province': 'País Vasco'
    },
    '942': {
        'city': 'Santander',
        'province': 'Cantabria'
    },
    '941': {
        'city': 'Logroño',
        'province': 'La Rioja'
    },
    '926': {
        'city': 'Ciudad Real',
        'province': 'Castilla-La Mancha'
    },
    '925': {
        'city': 'Toledo',
        'province': 'Castilla-La Mancha'
    },
    '927': {
        'city': 'Cáceres',
        'province': 'Extremadura'
    },
    '924': {
        'city': 'Badajoz',
        'province': 'Extremadura'
    },
}

# BRASIL
AREA_CODES_BRAZIL = {
    '11': {
        'city': 'São Paulo',
        'province': 'São Paulo'
    },
    '12': {
        'city': 'São José dos Campos',
        'province': 'São Paulo'
    },
    '13': {
        'city': 'Santos',
        'province': 'São Paulo'
    },
    '14': {
        'city': 'Bauru',
        'province': 'São Paulo'
    },
    '15': {
        'city': 'Sorocaba',
        'province': 'São Paulo'
    },
    '16': {
        'city': 'Ribeirão Preto',
        'province': 'São Paulo'
    },
    '17': {
        'city': 'São José do Rio Preto',
        'province': 'São Paulo'
    },
    '18': {
        'city': 'Presidente Prudente',
        'province': 'São Paulo'
    },
    '19': {
        'city': 'Campinas',
        'province': 'São Paulo'
    },
    '21': {
        'city': 'Rio de Janeiro',
        'province': 'Rio de Janeiro'
    },
    '22': {
        'city': 'Campos dos Goytacazes',
        'province': 'Rio de Janeiro'
    },
    '24': {
        'city': 'Volta Redonda',
        'province': 'Rio de Janeiro'
    },
    '27': {
        'city': 'Vitória',
        'province': 'Espírito Santo'
    },
    '28': {
        'city': 'Cachoeiro de Itapemirim',
        'province': 'Espírito Santo'
    },
    '31': {
        'city': 'Belo Horizonte',
        'province': 'Minas Gerais'
    },
    '32': {
        'city': 'Juiz de Fora',
        'province': 'Minas Gerais'
    },
    '33': {
        'city': 'Governador Valadares',
        'province': 'Minas Gerais'
    },
    '34': {
        'city': 'Uberlândia',
        'province': 'Minas Gerais'
    },
    '35': {
        'city': 'Poços de Caldas',
        'province': 'Minas Gerais'
    },
    '37': {
        'city': 'Divinópolis',
        'province': 'Minas Gerais'
    },
    '38': {
        'city': 'Montes Claros',
        'province': 'Minas Gerais'
    },
    '41': {
        'city': 'Curitiba',
        'province': 'Paraná'
    },
    '42': {
        'city': 'Ponta Grossa',
        'province': 'Paraná'
    },
    '43': {
        'city': 'Londrina',
        'province': 'Paraná'
    },
    '44': {
        'city': 'Maringá',
        'province': 'Paraná'
    },
    '45': {
        'city': 'Foz do Iguaçu',
        'province': 'Paraná'
    },
    '46': {
        'city': 'Francisco Beltrão',
        'province': 'Paraná'
    },
    '47': {
        'city': 'Joinville',
        'province': 'Santa Catarina'
    },
    '48': {
        'city': 'Florianópolis',
        'province': 'Santa Catarina'
    },
    '49': {
        'city': 'Chapecó',
        'province': 'Santa Catarina'
    },
    '51': {
        'city': 'Porto Alegre',
        'province': 'Rio Grande do Sul'
    },
    '53': {
        'city': 'Pelotas',
        'province': 'Rio Grande do Sul'
    },
    '54': {
        'city': 'Caxias do Sul',
        'province': 'Rio Grande do Sul'
    },
    '55': {
        'city': 'Santa Maria',
        'province': 'Rio Grande do Sul'
    },
    '61': {
        'city': 'Brasília',
        'province': 'Distrito Federal'
    },
    '62': {
        'city': 'Goiânia',
        'province': 'Goiás'
    },
    '63': {
        'city': 'Palmas',
        'province': 'Tocantins'
    },
    '64': {
        'city': 'Rio Verde',
        'province': 'Goiás'
    },
    '65': {
        'city': 'Cuiabá',
        'province': 'Mato Grosso'
    },
    '66': {
        'city': 'Rondonópolis',
        'province': 'Mato Grosso'
    },
    '67': {
        'city': 'Campo Grande',
        'province': 'Mato Grosso do Sul'
    },
    '68': {
        'city': 'Rio Branco',
        'province': 'Acre'
    },
    '69': {
        'city': 'Porto Velho',
        'province': 'Rondônia'
    },
    '71': {
        'city': 'Salvador',
        'province': 'Bahia'
    },
    '73': {
        'city': 'Ilhéus',
        'province': 'Bahia'
    },
    '74': {
        'city': 'Juazeiro',
        'province': 'Bahia'
    },
    '75': {
        'city': 'Feira de Santana',
        'province': 'Bahia'
    },
    '77': {
        'city': 'Barreiras',
        'province': 'Bahia'
    },
    '79': {
        'city': 'Aracaju',
        'province': 'Sergipe'
    },
    '81': {
        'city': 'Recife',
        'province': 'Pernambuco'
    },
    '82': {
        'city': 'Maceió',
        'province': 'Alagoas'
    },
    '83': {
        'city': 'João Pessoa',
        'province': 'Paraíba'
    },
    '84': {
        'city': 'Natal',
        'province': 'Rio Grande do Norte'
    },
    '85': {
        'city': 'Fortaleza',
        'province': 'Ceará'
    },
    '86': {
        'city': 'Teresina',
        'province': 'Piauí'
    },
    '87': {
        'city': 'Petrolina',
        'province': 'Pernambuco'
    },
    '88': {
        'city': 'Juazeiro do Norte',
        'province': 'Ceará'
    },
    '89': {
        'city': 'Picos',
        'province': 'Piauí'
    },
    '91': {
        'city': 'Belém',
        'province': 'Pará'
    },
    '92': {
        'city': 'Manaus',
        'province': 'Amazonas'
    },
    '93': {
        'city': 'Santarém',
        'province': 'Pará'
    },
    '94': {
        'city': 'Marabá',
        'province': 'Pará'
    },
    '95': {
        'city': 'Boa Vista',
        'province': 'Roraima'
    },
    '96': {
        'city': 'Macapá',
        'province': 'Amapá'
    },
    '97': {
        'city': 'Coari',
        'province': 'Amazonas'
    },
    '98': {
        'city': 'São Luís',
        'province': 'Maranhão'
    },
    '99': {
        'city': 'Imperatriz',
        'province': 'Maranhão'
    },
}

# ALEMANIA
AREA_CODES_GERMANY = {
    '30': {
        'city': 'Berlín',
        'province': 'Berlín'
    },
    '40': {
        'city': 'Hamburgo',
        'province': 'Hamburgo'
    },
    '89': {
        'city': 'Múnich',
        'province': 'Baviera'
    },
    '221': {
        'city': 'Colonia',
        'province': 'Renania del Norte-Westfalia'
    },
    '69': {
        'city': 'Fráncfort',
        'province': 'Hesse'
    },
    '711': {
        'city': 'Stuttgart',
        'province': 'Baden-Wurtemberg'
    },
    '211': {
        'city': 'Düsseldorf',
        'province': 'Renania del Norte-Westfalia'
    },
    '231': {
        'city': 'Dortmund',
        'province': 'Renania del Norte-Westfalia'
    },
    '201': {
        'city': 'Essen',
        'province': 'Renania del Norte-Westfalia'
    },
    '341': {
        'city': 'Leipzig',
        'province': 'Sajonia'
    },
    '351': {
        'city': 'Dresde',
        'province': 'Sajonia'
    },
    '511': {
        'city': 'Hannover',
        'province': 'Baja Sajonia'
    },
    '911': {
        'city': 'Núremberg',
        'province': 'Baviera'
    },
    '421': {
        'city': 'Bremen',
        'province': 'Bremen'
    },
}

# FRANCIA
AREA_CODES_FRANCE = {
    '1': {
        'city': 'París',
        'province': 'Île-de-France'
    },
    '4': {
        'city': 'Lyon/Marsella',
        'province': 'Sudeste'
    },
    '5': {
        'city': 'Toulouse/Burdeos',
        'province': 'Sudoeste'
    },
    '2': {
        'city': 'Noroeste',
        'province': 'Noroeste'
    },
    '3': {
        'city': 'Noreste',
        'province': 'Noreste'
    },
}

# ITALIA
AREA_CODES_ITALY = {
    '06': {
        'city': 'Roma',
        'province': 'Lacio'
    },
    '02': {
        'city': 'Milán',
        'province': 'Lombardía'
    },
    '011': {
        'city': 'Turín',
        'province': 'Piamonte'
    },
    '081': {
        'city': 'Nápoles',
        'province': 'Campania'
    },
    '055': {
        'city': 'Florencia',
        'province': 'Toscana'
    },
    '010': {
        'city': 'Génova',
        'province': 'Liguria'
    },
    '051': {
        'city': 'Bolonia',
        'province': 'Emilia-Romaña'
    },
    '041': {
        'city': 'Venecia',
        'province': 'Véneto'
    },
    '091': {
        'city': 'Palermo',
        'province': 'Sicilia'
    },
    '080': {
        'city': 'Bari',
        'province': 'Apulia'
    },
}

# USA (ciudades principales por area code)
AREA_CODES_USA = {
    '212': {
        'city': 'Nueva York',
        'province': 'NY'
    },
    '213': {
        'city': 'Los Ángeles',
        'province': 'CA'
    },
    '312': {
        'city': 'Chicago',
        'province': 'IL'
    },
    '305': {
        'city': 'Miami',
        'province': 'FL'
    },
    '415': {
        'city': 'San Francisco',
        'province': 'CA'
    },
    '202': {
        'city': 'Washington D.C.',
        'province': 'DC'
    },
    '617': {
        'city': 'Boston',
        'province': 'MA'
    },
    '713': {
        'city': 'Houston',
        'province': 'TX'
    },
    '214': {
        'city': 'Dallas',
        'province': 'TX'
    },
    '404': {
        'city': 'Atlanta',
        'province': 'GA'
    },
    '303': {
        'city': 'Denver',
        'province': 'CO'
    },
    '206': {
        'city': 'Seattle',
        'province': 'WA'
    },
    '702': {
        'city': 'Las Vegas',
        'province': 'NV'
    },
    '602': {
        'city': 'Phoenix',
        'province': 'AZ'
    },
    '215': {
        'city': 'Filadelfia',
        'province': 'PA'
    },
    '619': {
        'city': 'San Diego',
        'province': 'CA'
    },
}


def detect_country(phone_raw: str) -> dict:
    """
    Detecta país, timezone, UTC offset, ciudad y provincia 
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

    # Detectar país primero (probar 4, 3, 2, 1 dígitos)
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

    # Agregar campos vacíos por defecto
    country_data['city'] = ''
    country_data['province'] = ''

    # Obtener el resto del número
    rest = phone_clean[len(country_prefix):]

    # Para Argentina: quitar el 9 de móviles
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
    elif country_prefix == '33':
        area_map = AREA_CODES_FRANCE
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
