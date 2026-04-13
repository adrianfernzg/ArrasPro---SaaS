"""
schemas.py - Esquemas Pydantic para validación de datos
Definen la forma de los datos que entran y salen de la API.
Separados de los modelos ORM (SQLAlchemy) para mantener la separación de capas.
"""

import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ========================
# ESQUEMAS DE AUTENTICACIÓN
# ========================

class LoginSchema(BaseModel):
    """Datos necesarios para iniciar sesión."""
    email: str
    password: str


class RegisterSchema(BaseModel):
    """Datos necesarios para registrar un nuevo usuario."""
    nombre: str
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validar_password(cls, v: str) -> str:
        """
        Validación avanzada de contraseña profesional:
        - Mínimo 8 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        - Al menos un carácter especial
        """
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r"[a-z]", v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula.')
        if not re.search(r"[A-Z]", v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula.')
        if not re.search(r"\d", v):
            raise ValueError('La contraseña debe tener al menos un número.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('La contraseña debe tener al menos un carácter especial.')
        return v

class GoogleLoginSchema(BaseModel):
    """Datos recibidos del SDK de Google (GSI)."""
    credential: str


class ForgotPasswordSchema(BaseModel):
    """Datos para solicitar restablecimiento de contraseña."""
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    """Datos para restablecer la contraseña con un token."""
    token: str
    nueva_password: str

    @field_validator('nueva_password')
    @classmethod
    def validar_password(cls, v: str) -> str:
        """Mismas reglas de validación que en el registro."""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r"[a-z]", v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula.')
        if not re.search(r"[A-Z]", v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula.')
        if not re.search(r"\d", v):
            raise ValueError('La contraseña debe tener al menos un número.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('La contraseña debe tener al menos un carácter especial.')
        return v


class UsuarioResponse(BaseModel):
    """Datos del usuario que se devuelven al frontend."""
    id: int
    nombre: str
    email: str
    metodo_registro: str

    class Config:
        from_attributes = True  # Permite crear desde objetos ORM


# ========================
# ESQUEMAS DEL CONTRATO
# ========================

class PersonaSchema(BaseModel):
    """Esquema para vendedores y compradores."""
    nombre: str = ""
    dni: str = ""
    domicilio: str = ""


class FincaSchema(BaseModel):
    """Datos de la finca/inmueble."""
    direccion: str = ""
    precio: str = ""
    arras: str = ""


class FechasSchema(BaseModel):
    """Fechas del contrato."""
    firma: str = ""
    limite: str = ""


class ContratoSchema(BaseModel):
    """
    Esquema completo del contrato que envía el frontend.
    Coincide con la estructura de Alpine.js definida en AGENT.md.
    """
    titulo: str = "Contrato sin título"
    tipo: str = ""
    vendedores: List[PersonaSchema] = []
    compradores: List[PersonaSchema] = []
    finca: FincaSchema = FincaSchema()
    fechas: FechasSchema = FechasSchema()
    clausulas: List[dict] = []


class ContratoResponse(BaseModel):
    """Datos del contrato que se devuelven al frontend."""
    id: int
    user_id: int
    datos_json: dict
    fecha_creacion: datetime
    estado: str

    class Config:
        from_attributes = True
