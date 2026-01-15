from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("score-cap-dim")

router = APIRouter(
    prefix="/api/score-cap-dim",
    tags=["Score Capacidad x Dimensión"],
)

# ======================================================
# MODELOS (ADMIN.CE_SCORE_CAP_DIM)
# ======================================================

class ScoreCapDimBase(BaseModel):
    id_evaluacion: int
    id_capacidad: int
    id_dimension: int
    score: float


class ScoreCapDimCreate(ScoreCapDimBase):
    pass


class ScoreCapDimUpdate(BaseModel):
    score: Optional[float] = None


class ScoreCapDimResponse(ScoreCapDimBase):
    id_score: int
    dt_calculo: Optional[str] = None


# ======================================================
# HELPERS ORDS
# ======================================================

def limpiar_item(item: dict) -> dict:
    """
    Elimina metadata ORDS (links, etc.)
    """
    item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    """
    Extrae solo los items limpios desde ORDS
    """
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ======================================================
# CRUD
# ======================================================

@router.get("/", response_model=List[ScoreCapDimResponse])
async def listar_scores():
    """
    Lista scores por capacidad y dimensión
    """
    try:
        data = await ords_request("GET", "/ce_score_cap_dim/")
        return limpiar_lista(data)

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_score}", response_model=ScoreCapDimResponse)
async def obtener_score(id_score: int):
    """
    Obtiene score por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_score_cap_dim/{id_score}",
        )
        return limpiar_item(data)

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Score no encontrado")

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=ScoreCapDimResponse, status_code=201)
async def crear_score(payload: ScoreCapDimCreate):
    """
    Crea un score capacidad-dimensión
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_score_cap_dim/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_score}", response_model=ScoreCapDimResponse)
async def actualizar_score(id_score: int, payload: ScoreCapDimUpdate):
    """
    Actualiza únicamente el score
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_score_cap_dim/{id_score}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Score no encontrado")

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_score}", status_code=200)
async def eliminar_score(id_score: int):
    """
    Elimina score con confirmación explícita
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_score_cap_dim/{id_score}",
        )
        return {
            "ok": True,
            "mensaje": "Score eliminado correctamente",
            "id_score": id_score,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Score no encontrado",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando score {id_score}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando score {id_score}: {str(e)}",
        )
