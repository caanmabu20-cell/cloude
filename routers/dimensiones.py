from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("dimensiones")

router = APIRouter(
    prefix="/dimensiones",
    tags=["Dimensiones"],
)

# ============================
# MODELO
# Ajusta nombres si tu tabla tiene otros campos
# ============================

class Dimension(BaseModel):
    codigo: str
    nombre: str                      # ✅ Agregado
    descripcion: Optional[str] = None
    orden: int                       # ✅ Agregado
    fl_activa: Optional[str] = "Y"   # ✅ Corregido


# ============================
# GET LIST
# ============================

@router.get("/")
async def listar_dimensiones():
    """
    ORDS: GET /ce_dimension/
    """
    try:
        return await ords_request("GET", "/ce_dimension/")
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

@router.get("/{id_dimension}")
async def obtener_dimension(id_dimension: int):
    """
    ORDS: GET /ce_dimension/{id}
    """
    try:
        return await ords_request("GET", f"/ce_dimension/{id_dimension}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Dimensión no encontrada")
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
async def crear_dimension(data: Dimension):
    """
    ORDS: POST /ce_dimension/
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_dimension"})
        return await ords_request("POST", "/ce_dimension/", payload)
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

@router.put("/{id_dimension}")
async def actualizar_dimension(id_dimension: int, data: Dimension):
    """
    ORDS: PUT /ce_dimension/{id}
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_dimension"})
        return await ords_request(
            "PUT",
            f"/ce_dimension/{id_dimension}",
            payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Dimensión no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# DELETE
# ============================

@router.delete("/{id_dimension}", status_code=204)
async def eliminar_dimension(id_dimension: int):
    """
    ORDS: DELETE /ce_dimension/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_dimension/{id_dimension}")
        return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Dimensión no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
