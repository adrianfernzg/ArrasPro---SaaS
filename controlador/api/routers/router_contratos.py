"""
router_contratos.py - Endpoints de gestión de contratos
POST   /contratos/generar-pdf  → Generar PDF del contrato
POST   /contratos/              → Guardar contrato en la BD
GET    /contratos/              → Obtener contratos del usuario
GET    /contratos/{id}          → Obtener un contrato por ID
DELETE /contratos/{id}          → Eliminar un contrato
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from modelo.db.db_conexion import obtener_sesion
from modelo.db.models import Contrato
from modelo.schemas import ContratoSchema, ContratoResponse
from controlador.servicios.servicio_pdf import generar_contrato_pdf

# Crear el router con prefijo /contratos
router = APIRouter(prefix="/contratos", tags=["Contratos"])


@router.post("/generar-pdf")
async def generar_pdf(contrato: ContratoSchema):
    """
    Genera un PDF a partir de los datos del contrato y lo devuelve para descarga.
    """
    try:
        datos = contrato.model_dump()
        ruta_pdf = generar_contrato_pdf(datos)

        return FileResponse(
            ruta_pdf,
            media_type="application/pdf",
            filename="Contrato_ArrasPro.pdf"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el PDF: {str(e)}")


@router.post("/", response_model=ContratoResponse)
async def guardar_contrato(
    contrato: ContratoSchema,
    user_id: int,
    db: Session = Depends(obtener_sesion)
):
    """
    Guarda un contrato en la base de datos asociado a un usuario.
    """
    nuevo_contrato = Contrato(
        user_id=user_id,
        datos_json=contrato.model_dump(),
        estado="activo"
    )
    db.add(nuevo_contrato)
    db.commit()
    db.refresh(nuevo_contrato)

    return nuevo_contrato


@router.get("/", response_model=list[ContratoResponse])
async def obtener_contratos(user_id: int, db: Session = Depends(obtener_sesion)):
    """
    Obtiene todos los contratos de un usuario ordenados por fecha (más reciente primero).
    """
    contratos = (
        db.query(Contrato)
        .filter(Contrato.user_id == user_id)
        .order_by(Contrato.fecha_creacion.desc())
        .all()
    )
    return contratos


@router.get("/{contrato_id}", response_model=ContratoResponse)
async def obtener_contrato(contrato_id: int, db: Session = Depends(obtener_sesion)):
    """
    Obtiene un contrato específico por su ID.
    """
    contrato = db.query(Contrato).filter(Contrato.id == contrato_id).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato


@router.delete("/{contrato_id}")
async def eliminar_contrato(contrato_id: int, db: Session = Depends(obtener_sesion)):
    """
    Elimina un contrato de la base de datos.
    """
    contrato = db.query(Contrato).filter(Contrato.id == contrato_id).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    db.delete(contrato)
    db.commit()
    return {"mensaje": f"Contrato #{contrato_id} eliminado correctamente"}

@router.put("/{contrato_id}", response_model=ContratoResponse)
async def actualizar_contrato(
    contrato_id: int, 
    contrato_data: ContratoSchema, 
    user_id: int, 
    db: Session = Depends(obtener_sesion)
):
    """
    Actualiza un contrato existente (ej. renombrar o modificar un campo).
    Solo actualiza si el contrato pertenece al usuario facilitado.
    """
    contrato = db.query(Contrato).filter(Contrato.id == contrato_id, Contrato.user_id == user_id).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado o no autorizado")
    
    # Actualiza el JSON del contrato, que ahora incluirá el nuevo titulo
    contrato.datos_json = contrato_data.model_dump()
    db.commit()
    db.refresh(contrato)
    return contrato
