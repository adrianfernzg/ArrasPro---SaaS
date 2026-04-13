"""
db_conexion.py - Configuración de la conexión a PostgreSQL
Carga las variables de entorno del archivo .env de la raíz del proyecto
y crea el engine + sesión de SQLAlchemy.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Cargar variables de entorno ---
# Buscamos el .env en la raíz del proyecto (2 niveles arriba de modelo/db/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Configuración de la BD ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "conversorPDF")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- SQLAlchemy ---
# Motor de conexión
engine = create_engine(DATABASE_URL, echo=False)

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