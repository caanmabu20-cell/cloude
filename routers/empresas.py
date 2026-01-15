from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("empresas")

router = APIRouter(
    prefix="/empresas",
    tags=["Empresas"],
)

# ============================
# MODELO
# Ajusta campos si tu tabla tiene más columnas
# ============================

class Empresa(BaseModel):
    id_empresa: Optional[int] = None
    razon_social: str
    nit: Optional[str] = None
    sector: Optional[str] = None
    fl_activo: Optional[str] = "Y"


# ============================
# GET LIST
# ============================

@router.get("/")
async def listar_empresas():
    """
    ORDS: GET /ce_empresa/
    """
    try:
        return await ords_request("GET", "/ce_empresa/")
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

@router.get("/{id_empresa}")
async def obtener_empresa(id_empresa: int):
    """
    ORDS: GET /ce_empresa/{id}
    """
    try:
        return await ords_request("GET", f"/ce_empresa/{id_empresa}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
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
async def crear_empresa(data: Empresa):
    """
    ORDS: POST /ce_empresa/
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_empresa"})
        return await ords_request("POST", "/ce_empresa/", payload)
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

@router.put("/{id_empresa}")
async def actualizar_empresa(id_empresa: int, data: Empresa):
    """
    ORDS: PUT /ce_empresa/{id}
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_empresa"})
        return await ords_request(
            "PUT",
            f"/ce_empresa/{id_empresa}",
            payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# DELETE
# ============================

@router.delete("/{id_empresa}", status_code=204)
async def eliminar_empresa(id_empresa: int):
    """
    ORDS: DELETE /ce_empresa/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_empresa/{id_empresa}")
        return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
