"""
db_conexion.py - Configuración de la conexión a PostgreSQL.
Admite `.env` local, Docker y variables inyectadas por Railway.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Cargar variables de entorno ---
# Buscamos el .env en la raíz del proyecto (2 niveles arriba de modelo/db/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Intentar cargar .env local (solo funciona en desarrollo, en Railway las vars vienen del entorno)
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

# Log para Railway
print(f"DEBUG: BASE_DIR es {BASE_DIR}")
print(f"DEBUG: DATABASE_URL detectada: {bool(os.getenv('DATABASE_URL'))}")

def _normalizar_database_url(database_url: str | None) -> str | None:
    """Ajusta formatos de URL comunes para que SQLAlchemy los acepte."""
    if not database_url:
        return None

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)

    return database_url


def _obtener_database_url() -> str:
    """
    Prioriza DATABASE_URL y, si no existe, reconstruye la conexión usando
    variables compatibles con local, Docker y Railway.
    """
    database_url = _normalizar_database_url(os.getenv("DATABASE_URL"))
    if database_url:
        return database_url

    db_user = os.getenv("DB_USER") or os.getenv("PGUSER") or os.getenv("POSTGRES_USER") or "postgres"
    db_pass = os.getenv("DB_PASS") or os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD") or ""
    db_host = os.getenv("DB_HOST") or os.getenv("PGHOST") or "localhost"
    db_port = os.getenv("DB_PORT") or os.getenv("PGPORT") or "5433"
    db_name = os.getenv("DB_NAME") or os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB") or "conversorPDF"

    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


DATABASE_URL = _obtener_database_url()

# --- SQLAlchemy ---
# Motor de conexión
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Fábrica de sesiones (cada petición usará una sesión independiente)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para los modelos ORM
Base = declarative_base()


def obtener_sesion():
    """
    Generador de sesiones para usar con FastAPI Depends().
    Abre una sesión, la entrega al endpoint, y la cierra al terminar.
    """
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
