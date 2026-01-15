from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("ponderaciones")

router = APIRouter(
    prefix="/api/ponderaciones",
    tags=["Ponderaciones"],
)

# ======================================================
# MODELOS (alineados a ADMIN.CE_PONDERACION)
# ======================================================

class PonderacionBase(BaseModel):
    id_version: int
    id_pregunta: int
    id_capacidad: int
    id_dimension: int
    peso: float


class PonderacionCreate(PonderacionBase):
    pass


class PonderacionUpdate(BaseModel):
    id_version: Optional[int] = None
    id_pregunta: Optional[int] = None
    id_capacidad: Optional[int] = None
    id_dimension: Optional[int] = None
    peso: Optional[float] = None


class PonderacionResponse(PonderacionBase):
    id_ponderacion: int


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

@router.get("/", response_model=List[PonderacionResponse])
async def listar_ponderaciones():
    """
    Lista todas las ponderaciones
    """
    try:
        data = await ords_request("GET", "/ce_ponderacion/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_ponderacion}", response_model=PonderacionResponse)
async def obtener_ponderacion(id_ponderacion: int):
    """
    Obtiene una ponderación por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_ponderacion/{id_ponderacion}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=404,
            detail="Ponderación no encontrada",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=PonderacionResponse, status_code=201)
async def crear_ponderacion(payload: PonderacionCreate):
    """
    Crea una nueva ponderación
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_ponderacion/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_ponderacion}", response_model=PonderacionResponse)
async def actualizar_ponderacion(
    id_ponderacion: int,
    payload: PonderacionUpdate,
):
    """
    Actualiza una ponderación existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_ponderacion/{id_ponderacion}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=404,
            detail="Ponderación no encontrada",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_ponderacion}", status_code=200)
async def eliminar_ponderacion(id_ponderacion: int):
    """
    Elimina una ponderación (respuesta explícita)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_ponderacion/{id_ponderacion}",
        )
        return {
            "ok": True,
            "mensaje": "Ponderación eliminada correctamente",
            "id_ponderacion": id_ponderacion,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Ponderación no encontrada",
            )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Error ORDS eliminando ponderación {id_ponderacion}: "
                f"{e.response.text}"
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error interno eliminando ponderación {id_ponderacion}: "
                f"{str(e)}"
            ),
        )
