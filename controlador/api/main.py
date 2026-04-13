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

# ========================
# CREAR LA INSTANCIA
# ========================
app = FastAPI(
    title="ArrasPro API",
    description="API para la generación de contratos inmobiliarios con IA",
    version="1.0.0"
)

# ========================
# CONFIGURAR CORS
# ========================
# Permite que el frontend (HTML estático abierto con file://) se comunique con la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir al dominio real
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


# ========================
# SERVIR ARCHIVOS ESTÁTICOS (CSS, JS, imágenes)
# ========================
# IMPORTANTE: Esto va al final para no interceptar las rutas de la API
app.mount("/css", StaticFiles(directory=os.path.join(VISTA_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(VISTA_DIR, "js")), name="js")
