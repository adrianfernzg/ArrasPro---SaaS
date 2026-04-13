"""
models.py - Modelos ORM de SQLAlchemy
Define las tablas de la base de datos según la especificación del AGENT.md:
  - usuarios: id, nombre, email (Unique), password_hash (Nullable), google_id (Nullable), metodo_registro
  - contratos: id, user_id (FK), datos_json (JSONB), fecha_creacion, estado
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from modelo.db.db_conexion import Base


class Usuario(Base):
    """Tabla 'usuarios' - Almacena los datos de los usuarios registrados."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)   # Nullable para login con Google
    google_id = Column(String(255), nullable=True, unique=True)
    metodo_registro = Column(String(20), nullable=False, default="manual")  # 'manual' | 'google'

    # Relación con contratos (un usuario puede tener muchos contratos)
    contratos = relationship("Contrato", back_populates="usuario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nombre='{self.nombre}', email='{self.email}')>"


class Contrato(Base):
    """Tabla 'contratos' - Almacena los contratos generados por cada usuario."""
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    datos_json = Column(JSONB, nullable=False)       # Guarda todo el JSON del contrato
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    estado = Column(String(20), nullable=False, default="activo")  # 'activo' | 'vencido'

    # Relación inversa
    usuario = relationship("Usuario", back_populates="contratos")

    def __repr__(self):
        return f"<Contrato(id={self.id}, user_id={self.user_id}, estado='{self.estado}')>"


class PasswordResetToken(Base):
    """Tabla 'password_reset_tokens' - Almacena tokens para restablecer contraseñas."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expiracion = Column(DateTime, nullable=False)
    usado = Column(String(5), nullable=False, default="false")  # 'true' | 'false'

    # Relación con usuario
    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, usado={self.usado})>"
