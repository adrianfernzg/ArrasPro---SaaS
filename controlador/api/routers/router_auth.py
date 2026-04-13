"""
router_auth.py - Endpoints de autenticación
POST /auth/login            → Iniciar sesión
POST /auth/register         → Registrar usuario
POST /auth/forgot-password  → Solicitar restablecimiento de contraseña
POST /auth/reset-password   → Restablecer contraseña con token
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from modelo.db.db_conexion import obtener_sesion
from modelo.schemas import LoginSchema, RegisterSchema, UsuarioResponse, GoogleLoginSchema, ForgotPasswordSchema, ResetPasswordSchema
from controlador.servicios.servicio_auth import registrar_usuario, login_usuario, registrar_usuario_google, verificar_token_google, solicitar_restablecimiento, restablecer_password
from controlador.servicios.servicio_email import enviar_bienvenida

# Crear el router con prefijo /auth
router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=UsuarioResponse)
async def login(data: LoginSchema, db: Session = Depends(obtener_sesion)):
    """
    Inicia sesión con email y contraseña.
    Devuelve los datos del usuario si las credenciales son correctas.
    """
    try:
        usuario = login_usuario(db, data.email, data.password)
        return usuario
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=UsuarioResponse)
async def register(
    data: RegisterSchema, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(obtener_sesion)
):
    """
    Registra un nuevo usuario con email y contraseña y envía bienvenida.
    """
    try:
        usuario = registrar_usuario(db, data.nombre, data.email, data.password)
        # Enviar email de bienvenida en segundo plano
        background_tasks.add_task(enviar_bienvenida, usuario.email, usuario.nombre)
        return usuario
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/google", response_model=UsuarioResponse)
async def google_auth(
    data: GoogleLoginSchema, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(obtener_sesion)
):
    """
    Inicia sesión o registra un usuario mediante Google Auth (GSI).
    """
    try:
        # 1. Verificar el token contra Google
        perfil = verificar_token_google(data.credential)
        
        # 2. Lógica de Fallback para Desarrollo/TFG
        if not perfil:
            if data.credential == "SIMULATED_TOKEN_12345":
                print("⚠️ Usando perfil de SIMULACIÓN (Dev Mode)")
                perfil = {
                    "nombre": "Usuario Demo TFG",
                    "email": "demo.tfg@arraspro.doc",
                    "google_id": "sim_12345678"
                }
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Token inválido o google-auth no configurado. Usa el botón 'Simular Google' para pruebas."
                )

        # 3. Registrar o logear al usuario
        usuario, es_nuevo = registrar_usuario_google(db, perfil["nombre"], perfil["email"], perfil["google_id"])
        
        # 4. Si es nuevo, enviar bienvenida por email
        if es_nuevo:
             background_tasks.add_task(enviar_bienvenida, usuario.email, usuario.nombre)

        return usuario
    except HTTPException:
        # Re-lanzar excepciones HTTP de FastAPI para que no las capture el Exception genérico
        raise
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en autenticación Google: {str(e)}")


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordSchema,
    db: Session = Depends(obtener_sesion)
):
    """
    Solicita un restablecimiento de contraseña.
    Envía un email con un enlace de un solo uso (válido durante 1 hora).
    """
    try:
        # Ejecutamos síncronamente en lugar de BackgroundTasks
        # para poder decirle al usuario explícitamente si el email existe o no
        solicitar_restablecimiento(db, data.email)
        return {"mensaje": "Te hemos enviado un correo con las instrucciones. Revisa tu bandeja de entrada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error procesando forgot-password: {e}")
        raise HTTPException(status_code=500, detail="No se pudo procesar la solicitud debido a un error del servidor.")


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordSchema,
    db: Session = Depends(obtener_sesion)
):
    """
    Restablece la contraseña usando un token válido recibido por email.
    """
    try:
        restablecer_password(db, data.token, data.nueva_password)
        return {"mensaje": "¡Contraseña restablecida con éxito! Ya puedes iniciar sesión."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
