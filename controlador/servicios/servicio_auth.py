"""
servicio_auth.py - Servicio de autenticación de usuarios
Gestiona registro, login y verificación de contraseñas.
Usa bcrypt para el hash de contraseñas.
"""

import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from modelo.db.models import Usuario, PasswordResetToken
from controlador.servicios.servicio_email import enviar_email_restablecimiento
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Intentar importar google-auth para verificación profesional
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    print("⚠️  google-auth-library no detectada. La verificación real de Google estará desactivada.")

# Intentar importar bcrypt; si no está instalado, usar hashlib como fallback
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    import hashlib
    BCRYPT_AVAILABLE = False
    print("⚠️  bcrypt no instalado. Usando hashlib como fallback (no recomendado para producción).")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    else:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    if BCRYPT_AVAILABLE:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    else:
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed


def registrar_usuario(db: Session, nombre: str, email: str, password: str) -> Usuario:
    """
    Registra un nuevo usuario en la base de datos.
    
    Args:
        db: Sesión de SQLAlchemy.
        nombre: Nombre del usuario.
        email: Email (debe ser único).
        password: Contraseña en texto plano (se hashea antes de guardar).
    
    Returns:
        Objeto Usuario creado.
    
    Raises:
        ValueError: Si el email ya está registrado.
    """
    # Comprobar si el email ya existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise ValueError("Ya existe una cuenta con este email.")

    # Crear el usuario con la contraseña hasheada
    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email,
        password_hash=hash_password(password),
        metodo_registro="manual"
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    print(f"✅ Usuario registrado: {email}")
    return nuevo_usuario


def login_usuario(db: Session, email: str, password: str) -> Usuario:
    """
    Verifica las credenciales de un usuario.
    
    Returns:
        Objeto Usuario si las credenciales son correctas.
    
    Raises:
        ValueError: Si las credenciales son inválidas.
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        raise ValueError("No existe ninguna cuenta con este email.")

    if not usuario.password_hash:
        raise ValueError("Esta cuenta usa Google para iniciar sesión.")

    if not verify_password(password, usuario.password_hash):
        raise ValueError("Contraseña incorrecta.")

    print(f"✅ Login exitoso: {email}")
    return usuario


def registrar_usuario_google(db: Session, nombre: str, email: str, google_id: str) -> tuple[Usuario, bool]:
    """
    Registra o recupera un usuario autenticado con Google.
    Si ya existe, simplemente lo devuelve.
    Returns: (Usuario, es_nuevo)
    """
    # Buscar si ya existe por google_id o email
    usuario = db.query(Usuario).filter(
        (Usuario.google_id == google_id) | (Usuario.email == email)
    ).first()

    if usuario:
        # Si el usuario existe pero no tenía google_id, actualizarlo
        if not usuario.google_id:
            usuario.google_id = google_id
            db.commit()
        return usuario, False

    # Crear nuevo usuario con Google
    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email,
        google_id=google_id,
        metodo_registro="google"
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    print(f"✅ Usuario Google registrado: {email}")
    return nuevo_usuario, True


def verificar_token_google(credential: str) -> dict:
    """
    Verifica criptográficamente el ID Token (JWT) enviado por Google GSI.
    Si es válido, devuelve los datos del perfil (email, nombre, sub).
    """
    if not GOOGLE_AUTH_AVAILABLE:
        # Si la librería no está, no podemos verificar profesionalmente
        print("⚠️ Verificación saltada: google-auth no instalado.")
        return None

    if not GOOGLE_CLIENT_ID:
        # Modo Dev: si no hay client_id, permitimos tokens falsos en desarrollo (no recomendado)
        return None

    try:
        # Verificar el token contra Google
        idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), GOOGLE_CLIENT_ID)

        # ID Token issuer debe ser accounts.google.com
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Token de origen desconocido.')

        return {
            "email": idinfo['email'],
            "nombre": idinfo.get('name', 'Usuario Google'),
            "google_id": idinfo['sub']
        }
    except Exception as e:
        print(f"❌ Error verificando token Google: {str(e)}")
        raise ValueError("Token de Google inválido o caducado.")


def solicitar_restablecimiento(db: Session, email: str) -> bool:
    """
    Genera un token de restablecimiento y envía un email al usuario.
    Devuelve True si el proceso tiene éxito.
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        # Petición explícita del usuario: fallar si el correo no existe
        raise ValueError("No existe ninguna cuenta asociada a este correo electrónico.")

    # Generar token único
    token = str(uuid.uuid4())
    expiracion = datetime.utcnow() + timedelta(hours=1)

    # Guardar token en la BD
    reset_token = PasswordResetToken(
        user_id=usuario.id,
        token=token,
        expiracion=expiracion
    )
    db.add(reset_token)
    db.commit()

    # Enviar email con el enlace
    enviar_email_restablecimiento(email, usuario.nombre, token)
    print(f"🔑 Token de restablecimiento generado para: {email}")
    return True


def restablecer_password(db: Session, token: str, nueva_password: str) -> bool:
    """
    Valida el token y cambia la contraseña del usuario.
    Raises ValueError si el token es inválido, caducado o ya fue usado.
    """
    # Buscar el token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()

    if not reset_token:
        raise ValueError("El enlace de restablecimiento no es válido.")

    # Verificar que no haya sido usado
    if reset_token.usado == "true":
        raise ValueError("Este enlace ya fue utilizado. Solicita uno nuevo.")

    # Verificar expiración
    if datetime.utcnow() > reset_token.expiracion:
        raise ValueError("El enlace ha caducado. Solicita uno nuevo.")

    # Cambiar la contraseña del usuario
    usuario = db.query(Usuario).filter(Usuario.id == reset_token.user_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado.")

    usuario.password_hash = hash_password(nueva_password)

    # Marcar token como usado
    reset_token.usado = "true"

    db.commit()
    print(f"✅ Contraseña restablecida para: {usuario.email}")
    return True
