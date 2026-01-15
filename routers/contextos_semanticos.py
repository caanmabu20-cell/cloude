from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("contextos-semanticos")

router = APIRouter(
    prefix="/contextos-semanticos",
    tags=["Contexto Semántico"],
)

# ============================
# MODELO (ajústalo si tu tabla tiene más columnas)
# ============================

class ContextoSemantico(BaseModel):
    id_contexto: Optional[int] = None
    codigo: str
    descripcion: Optional[str] = None
    fl_activo: Optional[str] = "Y"


# ============================
# CRUD (ORDS AutoREST)
# ============================

@router.get("/")
async def listar_contextos():
    """
    GET /ce_contexto_semantico/
    """
    try:
        return await ords_request("GET", "/ce_contexto_semantico/")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        # si ORDS responde 4xx/5xx
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")


@router.get("/{id_contexto}")
async def obtener_contexto(id_contexto: int):
    """
    GET /ce_contexto_semantico/{id}
    """
    try:
        return await ords_request("GET", f"/ce_contexto_semantico/{id_contexto}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Contexto no encontrado")
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


@router.post("/", status_code=201)
async def crear_contexto(data: ContextoSemantico):
    """
    POST /ce_contexto_semantico/
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_contexto"})
        return await ords_request("POST", "/ce_contexto_semantico/", payload)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")


@router.put("/{id_contexto}")
async def actualizar_contexto(id_contexto: int, data: ContextoSemantico):
    """
    PUT /ce_contexto_semantico/{id}
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_contexto"})
        return await ords_request("PUT", f"/ce_contexto_semantico/{id_contexto}", payload)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Contexto no encontrado")
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


@router.delete("/{id_contexto}", status_code=204)
async def eliminar_contexto(id_contexto: int):
    """
    DELETE /ce_contexto_semantico/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_contexto_semantico/{id_contexto}")
        return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Contexto no encontrado")
        raise HTTPException(status_code=502, detail=f"Error ORDS: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
