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
    Recibe un documento (PDF o imagen) y extrae datos con IA (Gemini 3).
    Detecta automáticamente si es una Nota Simple o un DNI.
    """
    # 1. Validar la extensión del archivo
    extension = os.path.splitext(file.filename.lower())[1]
    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: '{extension}'. Usa: {', '.join(EXTENSIONES_PERMITIDAS)}"
        )

    # 2. Guardar el archivo temporalmente
    temp_path = f"/tmp/arraspro_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Intentar extraer datos (por defecto como Nota Simple)
        datos = extraer_datos_nota_simple(temp_path)

        if datos is None:
            raise HTTPException(
                status_code=500,
                detail="La IA no pudo extraer datos del documento. Asegúrate de subir una Nota Simple legible."
            )

        return {
            "mensaje": "Datos extraídos con éxito",
            "datos": datos
        }

    except HTTPException:
        raise  # Re-lanzar excepciones HTTP sin modificar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el documento: {str(e)}")
    finally:
        # 4. Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/upload-dni")
async def upload_dni(file: UploadFile = File(...)):
    """
    Recibe una imagen de DNI y extrae nombre, DNI y domicilio con IA.
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
                detail="La IA no pudo extraer datos del DNI."
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
