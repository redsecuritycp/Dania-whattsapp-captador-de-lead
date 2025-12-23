"""
Utilidades de limpieza de texto para DANIA/Fortia
Incluye: limpieza de Markdown, normalización de links
"""
import re


def clean_markdown_formatting(text: str) -> str:
    """
    Limpia formato Markdown de la respuesta.
    WhatsApp no renderiza Markdown, así que convertimos a texto plano.
    
    Réplica de Limpiar_Markdown_Links en n8n.
    """
    if not text:
        return ""
    
    # [texto](url) → url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\2', text)
    
    # **texto** → texto
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    
    # *texto* → texto
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # __texto__ → texto
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # _texto_ → texto
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # `código` → código
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # ### Header → Header
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Limpiar múltiples saltos de línea
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def clean_url(url: str) -> str:
    """
    Limpia y normaliza una URL.
    Remueve https://, http://, www. y trailing slash.
    """
    if not url:
        return ""
    
    url = url.strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    
    return url


def normalize_phone(phone: str) -> str:
    """
    Normaliza un número de teléfono a formato E.164.
    Remueve espacios, guiones, paréntesis.
    """
    if not phone:
        return ""
    
    # Remover todo excepto dígitos y +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Asegurar que empiece con +
    if cleaned and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned


def filter_valid_email(email: str) -> str:
    """
    Filtra emails válidos, descartando los genéricos o inválidos.
    """
    if not email:
        return ""
    
    email = email.lower().strip()
    
    # Emails a descartar
    invalid_patterns = [
        'example@', 'test@', 'sentry@', 'wix@', 
        'support@website', 'noreply@', 'no-reply@',
        '.png', '.jpg', '.gif', '.webp', '.svg'
    ]
    
    for pattern in invalid_patterns:
        if pattern in email:
            return ""
    
    # Validar formato básico
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return ""
    
    return email
