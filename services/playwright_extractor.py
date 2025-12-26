"""
Extractor con Playwright para widgets JS
"""
import asyncio
import logging
import re

logger = logging.getLogger(__name__)

async def fetch_with_playwright(url: str) -> str:
    """
    Usa Playwright para renderizar JS completo.
    Captura widgets flotantes como Joinchat.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("[PLAYWRIGHT] No instalado")
        return ""
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Esperar 3 segundos extra para widgets
            await asyncio.sleep(3)
            
            html = await page.content()
            await browser.close()
            
            logger.info(f"[PLAYWRIGHT] ✓ {len(html)} caracteres")
            return html
            
    except Exception as e:
        logger.error(f"[PLAYWRIGHT] Error: {e}")
        return ""


def extract_whatsapp_from_html(html: str) -> str:
    """Extrae WhatsApp de HTML con widgets."""
    patterns = [
        r'"telephone"[:\s]*"(\d{10,15})"',
        r'data-phone="(\d{10,15})"',
        r'wa\.me/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            num = re.sub(r'[^\d]', '', match.group(1))
            if 10 <= len(num) <= 15:
                return '+' + num
    return ""

