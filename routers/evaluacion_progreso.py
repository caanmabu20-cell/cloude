from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("evaluacion-progreso")

router = APIRouter(
    prefix="/evaluacion-progreso",
    tags=["Evaluación Progreso"],
)

# ============================
# MODELO
# Ajusta nombres/campos si tu tabla difiere
# ============================

class EvaluacionProgreso(BaseModel):
    id_progreso: Optional[int] = None
    id_evaluacion: int
    total_items: Optional[int] = None
    completados: Optional[int] = None
    porcentaje: Optional[float] = None
    estado: Optional[str] = None
    fl_activo: Optional[str] = "Y"


# ============================
# GET LIST
# ============================

@router.get("/")
async def listar_progreso():
    """
    ORDS: GET /ce_evaluacion_progreso/
    """
    try:
        return await ords_request("GET", "/ce_evaluacion_progreso/")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")


# ============================
# GET BY ID
# ============================

@router.get("/{id_progreso}")
async def obtener_progreso(id_progreso: int):
    """
    ORDS: GET /ce_evaluacion_progreso/{id}
    """
    try:
        return await ords_request("GET", f"/ce_evaluacion_progreso/{id_progreso}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Progreso no encontrado")
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# POST
# ============================

@router.post("/", status_code=201)
async def crear_progreso(data: EvaluacionProgreso):
    """
    ORDS: POST /ce_evaluacion_progreso/
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_progreso"})
        return await ords_request("POST", "/ce_evaluacion_progreso/", payload)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")


# ============================
# PUT
# ============================

@router.put("/{id_progreso}")
async def actualizar_progreso(id_progreso: int, data: EvaluacionProgreso):
    """
    ORDS: PUT /ce_evaluacion_progreso/{id}
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_progreso"})
        return await ords_request("PUT", f"/ce_evaluacion_progreso/{id_progreso}", payload)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Progreso no encontrado")
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# DELETE
# ============================

@router.delete("/{id_progreso}", status_code=204)
async def eliminar_progreso(id_progreso: int):
    """
    ORDS: DELETE /ce_evaluacion_progreso/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_evaluacion_progreso/{id_progreso}")
        return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Progreso no encontrado")
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
