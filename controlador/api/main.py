"""
main.py - Punto de entrada de la API FastAPI
Solo se encarga de:
  1. Crear la instancia de FastAPI
  2. Configurar CORS
  3. Montar los routers (auth, documentos, contratos)
  4. Endpoint raíz de bienvenida

Para ejecutar (desde la raíz del proyecto):
    uvicorn controlador.api.main:app --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Importar los routers
from controlador.api.routers.router_auth import router as auth_router
from controlador.api.routers.router_documentos import router as docs_router
from controlador.api.routers.router_contratos import router as contratos_router
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Ruta a la carpeta 'vista' (frontend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VISTA_DIR = os.path.join(BASE_DIR, "vista")


def _obtener_allowed_origins() -> list[str]:
    """
    Permite configurar CORS por variable de entorno y añade orígenes comunes
    de desarrollo si no se define nada.
    """
    cors_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]

    origins = {
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    }

    app_base_url = os.getenv("APP_BASE_URL", "").strip()
    railway_static_url = os.getenv("RAILWAY_STATIC_URL", "").strip()
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()

    if app_base_url:
        origins.add(app_base_url.rstrip("/"))
    if railway_static_url:
        origins.add(railway_static_url.rstrip("/"))
    if railway_public_domain:
        origins.add(f"https://{railway_public_domain}".rstrip("/"))

    return sorted(origins)

# ========================
# STARTUP: Crear tablas automáticamente
# ========================
from contextlib import asynccontextmanager
from modelo.db.db_conexion import engine, Base
from modelo.db import models  # Importar para registrar los modelos en Base

@asynccontextmanager
async def lifespan(app):
    """Crea las tablas en la BD al arrancar si no existen."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas de la BD listas.")
    except Exception as e:
        print(f"⚠️  No se pudieron crear las tablas: {e}")
    yield

# ========================
# CREAR LA INSTANCIA
# ========================
app = FastAPI(
    title="ArrasPro API",
    description="API para la generación de contratos inmobiliarios con IA",
    version="1.0.0",
    lifespan=lifespan
)

# ========================
# CONFIGURAR CORS
# ========================
# Permite que el frontend (HTML estático abierto con file://) se comunique con la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=_obtener_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# MONTAR ROUTERS
# ========================
app.include_router(auth_router)       # /auth/login, /auth/register
app.include_router(docs_router)       # /documentos/upload, /documentos/upload-dni
app.include_router(contratos_router)  # /contratos/generar-pdf, CRUD contratos

# ========================
# MANEJO DE ERRORES 422 (DEBUG)
# ========================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Middleware para capturar y logear errores de validación de esquemas (422).
    Imprime en la consola el detalle exacto de qué campo falló.
    """
    print(f"❌ Error de Validación (422): {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# ========================
# ENDPOINT RAÍZ -> Sirve el frontend
# ========================
@app.get("/", tags=["General"])
def serve_frontend():
    """Sirve la página principal del frontend (vista/index.html)."""
    return FileResponse(os.path.join(VISTA_DIR, "index.html"))


@app.get("/api/status", tags=["General"])
def api_status():
    """Endpoint para verificar que la API está funcionando."""
    return {
        "app": "ArrasPro API",
        "version": "1.0.0",
        "status": "✅ Funcionando correctamente"
    }


@app.get("/api/db-status", tags=["General"])
def db_status():
    """Endpoint de diagnóstico: verifica la conexión con la base de datos."""
    from sqlalchemy import text
    from modelo.db.db_conexion import engine, DATABASE_URL
    import re

    # Ocultar la contraseña de la URL para no exponerla
    url_segura = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', DATABASE_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
        return {
            "status": "✅ Conectado",
            "db_url": url_segura,
            "postgres_version": version
        }
    except Exception as e:
        return {
            "status": "❌ Error de conexión",
            "db_url": url_segura,
            "error": str(e)
        }


# ========================
# SERVIR ARCHIVOS ESTÁTICOS (CSS, JS, imágenes)
# ========================
# IMPORTANTE: Esto va al final para no interceptar las rutas de la API
app.mount("/css", StaticFiles(directory=os.path.join(VISTA_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(VISTA_DIR, "js")), name="js")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
