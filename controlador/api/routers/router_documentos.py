"""
router_documentos.py - Endpoints de procesamiento de documentos con IA
POST /documentos/upload  → Subir Nota Simple o DNI para extracción con Gemini
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from controlador.servicios.servicio_ia import extraer_datos_nota_simple, extraer_datos_dni

# Crear el router con prefijo /documentos
router = APIRouter(prefix="/documentos", tags=["Documentos / IA"])

# Extensiones permitidas
EXTENSIONES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}


@router.post("/upload")
async def upload_documento(file: UploadFile = File(...)):
    """
    Recibe una Nota Simple (PDF/imagen) y extrae dirección, ref catastral y nº finca.
    Devuelve 422 si el documento no es una Nota Simple.
    """
    extension = os.path.splitext(file.filename.lower())[1]
    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: '{extension}'. Usa: {', '.join(EXTENSIONES_PERMITIDAS)}"
        )

    temp_path = f"/tmp/arraspro_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        datos = extraer_datos_nota_simple(temp_path)

        if datos is None:
            raise HTTPException(
                status_code=500,
                detail="La IA no pudo procesar el documento. Inténtalo de nuevo."
            )

        if isinstance(datos, dict) and datos.get("error") == "no_es_nota_simple":
            raise HTTPException(
                status_code=422,
                detail="Por favor envíe una nota simple (PDF o imagen) o ingrese los datos manualmente."
            )

        return {
            "mensaje": "Datos extraídos con éxito",
            "datos": datos
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el documento: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/upload-dni")
async def upload_dni(file: UploadFile = File(...)):
    """
    Recibe un DNI/NIE/pasaporte y extrae nombre, número e identidad.
    Devuelve 422 si el documento no es un documento de identidad.
    """
    extension = os.path.splitext(file.filename.lower())[1]
    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: '{extension}'. Usa: {', '.join(EXTENSIONES_PERMITIDAS)}"
        )

    temp_path = f"/tmp/arraspro_dni_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        datos = extraer_datos_dni(temp_path)

        if datos is None:
            raise HTTPException(
                status_code=500,
                detail="La IA no pudo procesar el documento. Inténtalo de nuevo."
            )

        if isinstance(datos, dict) and datos.get("error") == "no_es_dni":
            raise HTTPException(
                status_code=422,
                detail="Envía tu DNI o ingresa los datos manualmente."
            )

        return {
            "mensaje": "Datos del DNI extraídos con éxito",
            "datos": datos
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el DNI: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
