"""
db_conexion.py - Configuración de la conexión a PostgreSQL.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Cargar variables de entorno ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

def _normalizar_database_url(database_url: str | None) -> str | None:
    if not database_url:
        return None
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url

def _obtener_database_url() -> str:
    database_url = _normalizar_database_url(os.getenv("DATABASE_URL"))
    if database_url:
        return database_url

    db_user = os.getenv("DB_USER") or os.getenv("PGUSER") or "postgres"
    db_pass = os.getenv("DB_PASS") or os.getenv("PGPASSWORD") or ""
    db_host = os.getenv("DB_HOST") or os.getenv("PGHOST") or "localhost"
    db_port = os.getenv("DB_PORT") or os.getenv("PGPORT") or "5433"
    db_name = os.getenv("DB_NAME") or os.getenv("PGDATABASE") or "conversorPDF"

    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

DATABASE_URL = _obtener_database_url()
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def obtener_sesion():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
