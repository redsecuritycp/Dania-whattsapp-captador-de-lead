"""
Configuración del proyecto DANIA/Fortia WhatsApp Bot
Todas las variables sensibles se leen de Replit Secrets (os.environ)
"""
import os

# =============================================================================
# WHATSAPP BUSINESS API
# =============================================================================
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "fortia_verify_2024")

# =============================================================================
# MONGODB ATLAS
# =============================================================================
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "dania_fortia")

# =============================================================================
# OPENAI
# =============================================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# =============================================================================
# TAVILY (Búsqueda web)
# =============================================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# =============================================================================
# JINA AI (Extracción web)
# =============================================================================
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")

# =============================================================================
# GMAIL
# =============================================================================
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", "pansapablo@gmail.com")

# =============================================================================
# CAL.COM
# =============================================================================
CALCOM_API_KEY = os.environ.get("CALCOM_API_KEY", "")
CALCOM_EVENT_URL = os.environ.get("CALCOM_EVENT_URL", "https://cal.com/agencia-fortia-hviska/60min")

# =============================================================================
# GOOGLE CUSTOM SEARCH (para LinkedIn)
# =============================================================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_SEARCH_CX", "33f5cc1337cde4799")

# =============================================================================
# MAPEO DE PAÍSES
# =============================================================================
COUNTRY_MAP = {
    '54': {'country': 'Argentina', 'timezone': 'America/Argentina/Buenos_Aires', 'utc': 'UTC-3', 'code': '+54', 'emoji': '🇦🇷'},
    '52': {'country': 'México', 'timezone': 'America/Mexico_City', 'utc': 'UTC-6', 'code': '+52', 'emoji': '🇲🇽'},
    '34': {'country': 'España', 'timezone': 'Europe/Madrid', 'utc': 'UTC+1', 'code': '+34', 'emoji': '🇪🇸'},
    '56': {'country': 'Chile', 'timezone': 'America/Santiago', 'utc': 'UTC-4', 'code': '+56', 'emoji': '🇨🇱'},
    '57': {'country': 'Colombia', 'timezone': 'America/Bogota', 'utc': 'UTC-5', 'code': '+57', 'emoji': '🇨🇴'},
    '51': {'country': 'Perú', 'timezone': 'America/Lima', 'utc': 'UTC-5', 'code': '+51', 'emoji': '🇵🇪'},
    '58': {'country': 'Venezuela', 'timezone': 'America/Caracas', 'utc': 'UTC-4', 'code': '+58', 'emoji': '🇻🇪'},
    '593': {'country': 'Ecuador', 'timezone': 'America/Guayaquil', 'utc': 'UTC-5', 'code': '+593', 'emoji': '🇪🇨'},
    '591': {'country': 'Bolivia', 'timezone': 'America/La_Paz', 'utc': 'UTC-4', 'code': '+591', 'emoji': '🇧🇴'},
    '595': {'country': 'Paraguay', 'timezone': 'America/Asuncion', 'utc': 'UTC-4', 'code': '+595', 'emoji': '🇵🇾'},
    '598': {'country': 'Uruguay', 'timezone': 'America/Montevideo', 'utc': 'UTC-3', 'code': '+598', 'emoji': '🇺🇾'},
    '1': {'country': 'Estados Unidos', 'timezone': 'America/New_York', 'utc': 'UTC-5', 'code': '+1', 'emoji': '🇺🇸'},
    '55': {'country': 'Brasil', 'timezone': 'America/Sao_Paulo', 'utc': 'UTC-3', 'code': '+55', 'emoji': '🇧🇷'},
}

def detect_country(phone_raw: str) -> dict:
    """Detecta país, timezone y UTC offset desde el número de teléfono."""
    default = {
        'country': 'Desconocido',
        'timezone': 'America/Argentina/Buenos_Aires',
        'utc': 'UTC-3',
        'code': '+?',
        'emoji': '🌎'
    }
    
    # Limpiar el número
    phone_clean = phone_raw.lstrip('+')
    
    # Intentar con 3, 2 y 1 dígitos
    for length in [3, 2, 1]:
        prefix = phone_clean[:length]
        if prefix in COUNTRY_MAP:
            return COUNTRY_MAP[prefix]
    
    return default
