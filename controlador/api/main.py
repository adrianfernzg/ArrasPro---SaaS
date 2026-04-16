"""
main.py - Punto de entrada de la API FastAPI de ArrasPro.
"""

import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

# Importar los routers
from controlador.api.routers.router_auth import router as auth_router
from controlador.api.routers.router_documentos import router as docs_router
from controlador.api.routers.router_contratos import router as contratos_router

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VISTA_DIR = os.path.join(BASE_DIR, "vista")


def _obtener_allowed_origins() -> list[str]:
    """Devuelve los orígenes permitidos por CORS."""
    cors_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if cors_env:
        return [o.strip() for o in cors_env.split(",") if o.strip()]

    orígenes = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://arraspro-saas-production.up.railway.app",
    ]

    for var in ("APP_BASE_URL", "RAILWAY_STATIC_URL"):
        val = os.getenv(var, "").strip().rstrip("/")
        if val and val not in orígenes:
            orígenes.append(val)

    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if domain:
        orígenes.append(f"https://{domain}")

    return orígenes


# ========================
# STARTUP / LIFESPAN
# ========================
from modelo.db.db_conexion import engine, Base
from modelo.db import models  # Registra los modelos en Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas en la BD al arrancar (en un hilo para no bloquear el event loop)."""
    try:
        await asyncio.to_thread(Base.metadata.create_all, engine)
        print("✅ Tablas de la BD listas.")
    except Exception as e:
        print(f"⚠️  No se pudieron crear las tablas: {e}")
    yield


# ========================
# INSTANCIA DE FASTAPI
# ========================
app = FastAPI(
    title="ArrasPro API",
    description="API para la generación de contratos inmobiliarios con IA",
    version="1.0.0",
    lifespan=lifespan,
)

# ========================
# CORS
# ========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=_obtener_allowed_origins(),  # Nunca ["*"] con allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# ROUTERS
# ========================
app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(contratos_router)


# ========================
# MANEJADOR DE ERRORES 422
# ========================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"❌ Error de Validación (422): {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# ========================
# ENDPOINTS GENERALES
# ========================
@app.get("/", tags=["General"])
def serve_frontend():
    """Sirve el frontend (index.html)."""
    return FileResponse(os.path.join(VISTA_DIR, "index.html"))


@app.get("/api/status", tags=["General"])
def api_status():
    return {"app": "ArrasPro API", "version": "1.0.0", "status": "✅ OK"}


# ========================
# ARCHIVOS ESTÁTICOS  (al final para no interceptar rutas de la API)
# ========================
app.mount("/css", StaticFiles(directory=os.path.join(VISTA_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(VISTA_DIR, "js")), name="js")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
