from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("evaluaciones")

router = APIRouter(
    prefix="/evaluaciones",
    tags=["Evaluaciones"],
)

# ============================
# MODELO
# Ajusta campos si tu tabla tiene más columnas
# ============================

class Evaluacion(BaseModel):
    id_evaluacion: Optional[int] = None
    id_empresa: int
    nombre: str
    periodo: Optional[str] = None
    estado: Optional[str] = None
    porcentaje_avance: Optional[float] = None
    fl_activo: Optional[str] = "Y"


# ============================
# GET LIST
# ============================

@router.get("/")
async def listar_evaluaciones():
    """
    ORDS: GET /ce_evaluacion/
    """
    try:
        return await ords_request("GET", "/ce_evaluacion/")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )


# ============================
# GET BY ID
# ============================

@router.get("/{id_evaluacion}")
async def obtener_evaluacion(id_evaluacion: int):
    """
    ORDS: GET /ce_evaluacion/{id}
    """
    try:
        return await ords_request("GET", f"/ce_evaluacion/{id_evaluacion}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# POST
# ============================

@router.post("/", status_code=201)
async def crear_evaluacion(data: Evaluacion):
    """
    ORDS: POST /ce_evaluacion/
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_evaluacion"})
        return await ords_request("POST", "/ce_evaluacion/", payload)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )


# ============================
# PUT
# ============================

@router.put("/{id_evaluacion}")
async def actualizar_evaluacion(id_evaluacion: int, data: Evaluacion):
    """
    ORDS: PUT /ce_evaluacion/{id}
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_evaluacion"})
        return await ords_request(
            "PUT",
            f"/ce_evaluacion/{id_evaluacion}",
            payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# DELETE
# ============================

@router.delete("/{id_evaluacion}", status_code=204)
async def eliminar_evaluacion(id_evaluacion: int):
    """
    ORDS: DELETE /ce_evaluacion/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_evaluacion/{id_evaluacion}")
        return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
