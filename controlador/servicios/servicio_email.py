"""
servicio_email.py - Servicio para el envío de correos electrónicos.
Usa la API HTTP de Resend en lugar de SMTP directo (Railway bloquea SMTP saliente).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "ArrasPro <onboarding@resend.dev>")


def _obtener_app_base_url() -> str:
    """Obtiene la URL pública de la app con soporte para Railway."""
    app_base_url = os.getenv("APP_BASE_URL")
    if app_base_url:
        return app_base_url.rstrip("/")

    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    if railway_static_url:
        return railway_static_url.rstrip("/")

    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_public_domain:
        return f"https://{railway_public_domain}".rstrip("/")

    return "http://localhost:8000"


APP_BASE_URL = _obtener_app_base_url()


def _enviar(destinatario: str, asunto: str, html: str) -> bool:
    """Envía un email via Resend API. Devuelve True si tuvo éxito."""
    if not RESEND_API_KEY:
        print(f"⚠️  RESEND_API_KEY no configurado. Saltando envío a {destinatario}.")
        return False

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": [destinatario],
                "subject": asunto,
                "html": html,
            },
            timeout=10,
        )
        if response.status_code in (200, 201):
            return True
        print(f"❌ Resend API error ({response.status_code}): {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error enviando email a {destinatario}: {str(e)}")
        return False


def enviar_bienvenida(destinatario: str, nombre_usuario: str):
    """Envía un correo electrónico de bienvenida al usuario recién registrado."""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h1 style="color: #2563eb; text-align: center;">¡Hola, {nombre_usuario}! 👋</h1>
            <p>Estamos encantados de tenerte en <strong>ArrasPro</strong>, la herramienta definitiva para gestionar tus contratos de arras de forma profesional.</p>
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h2 style="font-size: 1.2rem; color: #1e293b;">¿Qué puedes hacer ahora?</h2>
                <ul style="padding-left: 20px;">
                    <li>Generar contratos de arras con IA en segundos.</li>
                    <li>Subir tu Nota Simple y DNI para autocompletar formularios.</li>
                    <li>Gestionar y descargar tus documentos en PDF profesional.</li>
                </ul>
            </div>
            <p style="text-align: center; margin-top: 30px;">
                <a href="{APP_BASE_URL}" style="background-color: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Ir a mi Dashboard</a>
            </p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.8rem; color: #64748b; text-align: center;">Este es un mensaje automático de ArrasPro. No respondas a este correo.</p>
        </div>
    </body>
    </html>
    """
    if _enviar(destinatario, "¡Bienvenido a ArrasPro! 🏠", html):
        print(f"✅ Email de bienvenida enviado a: {destinatario}")


def enviar_email_restablecimiento(destinatario: str, nombre_usuario: str, token: str):
    """Envía un correo con el enlace para restablecer la contraseña."""
    enlace = f"{APP_BASE_URL}/?reset_token={token}"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h1 style="color: #2563eb; text-align: center;">Restablecer contraseña 🔑</h1>
            <p>Hola, <strong>{nombre_usuario}</strong>,</p>
            <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en <strong>ArrasPro</strong>.</p>
            <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{enlace}" style="background-color: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Restablecer Contraseña</a>
            </p>
            <div style="background-color: #fef3c7; padding: 12px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; font-size: 0.9rem; color: #92400e;">⚠️ Este enlace expira en <strong>1 hora</strong>. Si no has solicitado este cambio, ignora este correo.</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.8rem; color: #64748b; text-align: center;">Este es un mensaje automático de ArrasPro. No respondas a este correo.</p>
        </div>
    </body>
    </html>
    """
    if _enviar(destinatario, "Restablecimiento de contraseña - ArrasPro 🔑", html):
        print(f"✅ Email de restablecimiento enviado a: {destinatario}")
