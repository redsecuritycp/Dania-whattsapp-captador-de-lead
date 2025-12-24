"""
Servicio Gmail para envío de notificaciones de leads
Usa smtplib con App Password de Gmail
Versión completa con todas las secciones como n8n
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote

logger = logging.getLogger(__name__)


def generate_lead_email_html(lead_data: dict) -> str:
    """
    Genera el HTML del email de notificación de lead.
    Diseño elegante con CSS inline para compatibilidad.
    Incluye TODAS las secciones como n8n.
    """
    # Extraer datos con fallback
    def get(key, default="No proporcionado"):
        val = lead_data.get(key, default)
        if val is None or val == "" or val == "undefined" or val == "null":
            return default
        return val
    
    phone_clean = get("phone_whatsapp", "").replace("+", "")
    nombre_simple = get("name", "").split()[0] if get("name") else ""
    
    # Generar links de contacto
    email_lead = get("email", "No proporcionado")
    wa_link = f"https://wa.me/{phone_clean}?text=Hola%20{quote(nombre_simple)},%20soy%20Pablo%20de%20Fortia"
    
    # Formatear noticias si existen
    noticias_html = get("noticias_empresa", "No se encontraron noticias")
    if noticias_html and noticias_html != "No se encontraron noticias":
        noticias_html = noticias_html.replace('\n', '<br>')
    
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;max-width:700px;margin:0 auto;padding:20px;background-color:#f5f5f5;">

<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px;text-align:center;border-radius:10px 10px 0 0;">
<h1 style="margin:0;font-size:24px;">🤖 Nuevo Lead Capturado</h1>
<p style="margin:10px 0 0 0;opacity:0.9;">Sistema de Captación Automática - Fortia</p>
</div>

<div style="background:white;padding:30px;border:1px solid #e0e0e0;">

<p style="margin:0 0 20px 0;">Hola Pablo,</p>
<p style="margin:0 0 20px 0;">Se registró un nuevo lead en el sistema:</p>

<!-- Datos Personales -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">👤 Datos Personales</h3>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;font-weight:bold;color:#666;width:180px;">Nombre:</td><td style="padding:8px 0;">{get("name")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Email:</td><td style="padding:8px 0;">{get("email")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">WhatsApp:</td><td style="padding:8px 0;">{get("phone_whatsapp")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Cargo:</td><td style="padding:8px 0;">{get("role")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">LinkedIn Personal:</td><td style="padding:8px 0;">{get("linkedin_personal", "No encontrado")}</td></tr>
</table>
</div>

<!-- Datos Empresa -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">🏢 Datos de la Empresa</h3>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;font-weight:bold;color:#666;width:180px;">Empresa:</td><td style="padding:8px 0;">{get("business_name")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Actividad:</td><td style="padding:8px 0;">{get("business_activity")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Descripción:</td><td style="padding:8px 0;">{get("business_description")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Servicios:</td><td style="padding:8px 0;">{get("services_text")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Sitio Web:</td><td style="padding:8px 0;">{get("website", "No tiene")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Tiene Web:</td><td style="padding:8px 0;">{get("has_website", "No especificado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Modelo Negocio:</td><td style="padding:8px 0;">{get("business_model", "No especificado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Tamaño Equipo:</td><td style="padding:8px 0;">{get("team_size")}</td></tr>
</table>
</div>

<!-- Contacto Empresa -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">📞 Contacto Empresa</h3>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;font-weight:bold;color:#666;width:180px;">Tel. Empresa:</td><td style="padding:8px 0;">{get("phone_empresa", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">WhatsApp Empresa:</td><td style="padding:8px 0;">{get("whatsapp_empresa", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Horarios:</td><td style="padding:8px 0;">{get("horarios", "No encontrado")}</td></tr>
</table>
</div>

<!-- Ubicación -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">📍 Ubicación</h3>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;font-weight:bold;color:#666;width:180px;">Dirección:</td><td style="padding:8px 0;">{get("address", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Ciudad:</td><td style="padding:8px 0;">{get("city", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Provincia:</td><td style="padding:8px 0;">{get("province", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">País:</td><td style="padding:8px 0;">{get("country_detected", "No detectado")} ({get("utc_offset", "UTC?")})</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Zona Horaria:</td><td style="padding:8px 0;">{get("timezone_detected", "No detectada")}</td></tr>
</table>
</div>

<!-- Redes Sociales -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">🔗 Redes Sociales</h3>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;font-weight:bold;color:#666;width:180px;">LinkedIn Personal:</td><td style="padding:8px 0;">{get("linkedin_personal", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">LinkedIn Empresa:</td><td style="padding:8px 0;">{get("linkedin_empresa", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Instagram:</td><td style="padding:8px 0;">{get("instagram_empresa", "No encontrado")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Facebook:</td><td style="padding:8px 0;">{get("facebook_empresa", "No encontrado")}</td></tr>
</table>
</div>

<!-- Cualificación -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">🎯 Cualificación del Lead</h3>
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:8px 0;font-weight:bold;color:#666;width:180px;">Tamaño Equipo:</td><td style="padding:8px 0;">{get("team_size")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Conocimiento IA:</td><td style="padding:8px 0;">{get("ai_knowledge")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Desafío Principal:</td><td style="padding:8px 0;">{get("main_challenge")}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold;color:#666;">Intentos Previos:</td><td style="padding:8px 0;">{get("past_attempt")}</td></tr>
</table>
</div>

<!-- Noticias -->
<div style="background:#f9f9f9;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
<h3 style="margin:0 0 15px 0;color:#667eea;border-bottom:2px solid #667eea;padding-bottom:10px;">📰 Noticias de la Empresa</h3>
<p style="margin:0;white-space:pre-line;">{noticias_html}</p>
</div>

<!-- Botones CTA -->
<div style="text-align:center;margin:30px 0;">
<a href="mailto:{email_lead}" style="display:inline-block;padding:12px 30px;margin:10px;background:#667eea;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">📧 Contactar por Email</a>
<a href="{wa_link}" style="display:inline-block;padding:12px 30px;margin:10px;background:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">💬 WhatsApp</a>
</div>

<!-- Timestamps -->
<div style="background:#e8e8e8;padding:15px;margin:20px 0;border-radius:8px;font-size:12px;color:#666;">
<p style="margin:5px 0;"><strong>Fecha creación:</strong> {get("created_at", "No disponible")}</p>
<p style="margin:5px 0;"><strong>Hora local cliente:</strong> {get("created_at_local", "No disponible")}</p>
</div>

</div>

<div style="text-align:center;padding:20px;color:#999;font-size:12px;">
<p>Sistema de Captación Automática - Fortia/Dania</p>
<p>Generado automáticamente</p>
</div>

</body>
</html>'''
    
    return html


def send_lead_notification(lead_data: dict) -> dict:
    """
    Envía email de notificación de nuevo lead.
    """
    try:
        gmail_user = os.environ.get("GMAIL_USER", "")
        gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")
        notification_email = os.environ.get("NOTIFICATION_EMAIL", "pansapablo@gmail.com")
        
        if not gmail_user or not gmail_password:
            logger.error("GMAIL_USER o GMAIL_APP_PASSWORD no configurados")
            return {"success": False, "error": "Credenciales Gmail no configuradas"}
        
        msg = MIMEMultipart("alternative")
        
        business_name = lead_data.get("business_name", "Sin empresa")
        name = lead_data.get("name", "Sin nombre")
        
        msg["Subject"] = f"Nuevo lead guardado — {business_name} | {name}"
        msg["From"] = gmail_user
        msg["To"] = notification_email
        
        # Versión texto plano
        text_content = f"""
Nuevo Lead: {name}
Empresa: {business_name}
WhatsApp: {lead_data.get('phone_whatsapp', 'N/A')}
Email: {lead_data.get('email', 'N/A')}
País: {lead_data.get('country_detected', 'N/A')}
Actividad: {lead_data.get('business_activity', 'N/A')}
Sitio Web: {lead_data.get('website', 'N/A')}
Tamaño Equipo: {lead_data.get('team_size', 'N/A')}
Conocimiento IA: {lead_data.get('ai_knowledge', 'N/A')}
Desafío: {lead_data.get('main_challenge', 'N/A')}
"""
        
        html_content = generate_lead_email_html(lead_data)
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, notification_email, msg.as_string())
        
        logger.info(f"✓ Email enviado: {notification_email}")
        return {"success": True, "message": "Email enviado correctamente"}
    
    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación Gmail")
        return {"success": False, "error": "Error de autenticación Gmail"}
    
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return {"success": False, "error": str(e)}
