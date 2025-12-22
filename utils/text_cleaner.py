"""
Utilidades para limpiar texto antes de enviar a WhatsApp
"""
import re


def clean_markdown_links(text: str) -> str:
    """
    Convierte links Markdown [texto](url) a URLs crudas.
    WhatsApp no renderiza Markdown, así que mostramos la URL directamente.
    """
    if not text:
        return text
    
    # Patrón para [texto](url)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        # Retornar: texto - URL
        return f"{link_text}: {url}"
    
    cleaned = re.sub(pattern, replace_link, text)
    return cleaned


def clean_markdown_formatting(text: str) -> str:
    """
    Limpia formato Markdown que WhatsApp no soporta.
    Mantiene *bold* y _italic_ que sí funcionan.
    """
    if not text:
        return text
    
    # Limpiar links
    text = clean_markdown_links(text)
    
    # Convertir ### Header a *Header*
    text = re.sub(r'^###\s*(.+)$', r'*\1*', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s*(.+)$', r'*\1*', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s*(.+)$', r'*\1*', text, flags=re.MULTILINE)
    
    # Convertir **bold** a *bold* (WhatsApp usa un solo asterisco)
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    
    # Limpiar ``` code blocks
    text = re.sub(r'```[a-z]*\n?', '', text)
    
    return text


