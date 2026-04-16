"""
main.py - Punto de entrada de la API FastAPI
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Importar los routers
from controlador.api.routers.router_auth import router as auth_router
from controlador.api.routers.router_documentos import router as docs_router
from controlador.api.routers.router_contratos import router as contratos_router

# Ruta a la carpeta 'vista' (frontend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VISTA_DIR = os.path.join(BASE_DIR, "vista")

def _obtener_allowed_origins() -> list[str]:
    cors_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    origins = {"http://localhost:8000", "http://127.0.0.1:8000", "https://arraspro-saas-production.up.railway.app"}
    return list(origins)

# STARTUP
from modelo.db.db_conexion import engine, Base
from modelo.db import models 

@asynccontextmanager
async def lifespan(app):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield

app = FastAPI(title="ArrasPro API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(contratos_router)

@app.get("/", tags=["General"])
def serve_frontend():
    return FileResponse(os.path.join(VISTA_DIR, "index.html"))

@app.get("/api/status", tags=["General"])
def api_status():
    return {"status": "✅ Funcionando"}

app.mount("/css", StaticFiles(directory=os.path.join(VISTA_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(VISTA_DIR, "js")), name="js")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
