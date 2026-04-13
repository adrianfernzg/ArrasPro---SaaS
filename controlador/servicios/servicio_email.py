"""
servicio_email.py - Servicio para el envío de correos electrónicos.
Permite enviar correos de bienvenida con plantillas HTML.
Configuración mediante variables de entorno (.env).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from dotenv import load_dotenv

load_dotenv()

# Configuración SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
# IMPORTANTE: Quitar espacios de contraseñas de Google App (vienen como 'xxxx xxxx xxxx xxxx')
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip().replace(" ", "")

def enviar_bienvenida(destinatario: str, nombre_usuario: str):
    """
    Envía un correo electrónico de bienvenida al usuario recién registrado.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️  Configuración SMTP incompleta. Saltando el envío de correo a {destinatario}.")
        return

    try:
        # Crear el mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "¡Bienvenido a ArrasPro! 🏠"
        msg["From"] = f"ArrasPro <{SMTP_USER}>"
        msg["To"] = destinatario

        # Cuerpo del mensaje en HTML
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
                    <a href="http://localhost:8000" style="background-color: #2563eb; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Ir a mi Dashboard</a>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 0.8rem; color: #64748b; text-align: center;">Este es un mensaje automático de ArrasPro. No respondas a este correo.</p>
            </div>
        </body>
        </html>
        """

        # Adjuntar versión HTML
        parte_html = MIMEText(html, "html")
        msg.attach(parte_html)

        # Conectar y enviar
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Seguridad TLS
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, destinatario, msg.as_string())
        
        print(f"✅ Email de bienvenida enviado a: {destinatario}")

    except Exception as e:
        print(f"❌ Error enviando email a {destinatario}: {str(e)}")


def enviar_email_restablecimiento(destinatario: str, nombre_usuario: str, token: str):
    """
    Envía un correo electrónico con el enlace para restablecer la contraseña.
    El enlace lleva al frontend con el token como parámetro en la URL.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️  Configuración SMTP incompleta. Saltando el envío de correo a {destinatario}.")
        print(f"🔑 Token de restablecimiento (debug): {token}")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Restablecimiento de contraseña - ArrasPro 🔑"
        msg["From"] = f"ArrasPro <{SMTP_USER}>"
        msg["To"] = destinatario

        # Enlace de restablecimiento (apunta al frontend servido por FastAPI en el 8000)
        enlace = f"http://localhost:8000/?reset_token={token}"

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

        parte_html = MIMEText(html, "html")
        msg.attach(parte_html)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, destinatario, msg.as_string())

        print(f"✅ Email de restablecimiento enviado a: {destinatario}")

    except Exception as e:
        print(f"❌ Error enviando email de restablecimiento a {destinatario}: {str(e)}")
