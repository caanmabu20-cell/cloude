from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("normalizaciones-semanticas")

router = APIRouter(
    prefix="/api/normalizaciones-semanticas",
    tags=["Normalización Semántica"],
)

# ======================================================
# MODELOS (alineados a ADMIN.CE_NORMALIZACION_SEMANTICA)
# ======================================================

class NormalizacionBase(BaseModel):
    id_version: int
    id_contexto: int
    rango_inferior: float
    rango_superior: float
    estado: str
    descripcion: Optional[str] = None
    orden: int
    fl_activa: str = "Y"


class NormalizacionCreate(NormalizacionBase):
    pass


class NormalizacionUpdate(BaseModel):
    id_version: Optional[int] = None
    id_contexto: Optional[int] = None
    rango_inferior: Optional[float] = None
    rango_superior: Optional[float] = None
    estado: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    fl_activa: Optional[str] = None


class NormalizacionResponse(NormalizacionBase):
    id_normalizacion: int


# ============================
# HELPERS ORDS
# ============================

def limpiar_item(item: dict) -> dict:
    item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ============================
# CRUD
# ============================

@router.get("/", response_model=List[NormalizacionResponse])
async def listar_normalizaciones():
    """
    Lista todas las normalizaciones semánticas
    """
    try:
        data = await ords_request("GET", "/ce_normalizacion_semantica/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_normalizacion}", response_model=NormalizacionResponse)
async def obtener_normalizacion(id_normalizacion: int):
    """
    Obtiene una normalización por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_normalizacion_semantica/{id_normalizacion}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Normalización no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=NormalizacionResponse, status_code=201)
async def crear_normalizacion(payload: NormalizacionCreate):
    """
    Crea una nueva normalización semántica
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_normalizacion_semantica/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_normalizacion}", response_model=NormalizacionResponse)
async def actualizar_normalizacion(
    id_normalizacion: int,
    payload: NormalizacionUpdate,
):
    """
    Actualiza una normalización semántica existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_normalizacion_semantica/{id_normalizacion}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Normalización no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_normalizacion}", status_code=200)
async def eliminar_normalizacion(id_normalizacion: int):
    """
    Elimina una normalización semántica (respuesta explícita)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_normalizacion_semantica/{id_normalizacion}",
        )
        return {
            "ok": True,
            "mensaje": "Normalización semántica eliminada correctamente",
            "id_normalizacion": id_normalizacion,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Normalización no encontrada",
            )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Error ORDS eliminando normalización {id_normalizacion}: "
                f"{e.response.text}"
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error interno eliminando normalización {id_normalizacion}: "
                f"{str(e)}"
            ),
        )
