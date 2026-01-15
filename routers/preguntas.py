from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("preguntas")

router = APIRouter(
    prefix="/api/preguntas",
    tags=["Preguntas"],
)

# ======================================================
# MODELOS (alineados a ADMIN.CE_PREGUNTA)
# ======================================================

class PreguntaBase(BaseModel):
    id_version: int
    codigo: str
    texto: str
    id_capacidad: int
    id_dimension: int
    orden: int
    fl_activa: str = "Y"


class PreguntaCreate(PreguntaBase):
    pass


class PreguntaUpdate(BaseModel):
    id_version: Optional[int] = None
    codigo: Optional[str] = None
    texto: Optional[str] = None
    id_capacidad: Optional[int] = None
    id_dimension: Optional[int] = None
    orden: Optional[int] = None
    fl_activa: Optional[str] = None


class PreguntaResponse(PreguntaBase):
    id_pregunta: int


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

@router.get("/", response_model=List[PreguntaResponse])
async def listar_preguntas():
    """
    Lista todas las preguntas
    """
    try:
        data = await ords_request("GET", "/ce_pregunta/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_pregunta}", response_model=PreguntaResponse)
async def obtener_pregunta(id_pregunta: int):
    """
    Obtiene una pregunta por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_pregunta/{id_pregunta}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=404,
            detail="Pregunta no encontrada",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=PreguntaResponse, status_code=201)
async def crear_pregunta(payload: PreguntaCreate):
    """
    Crea una nueva pregunta
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_pregunta/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_pregunta}", response_model=PreguntaResponse)
async def actualizar_pregunta(
    id_pregunta: int,
    payload: PreguntaUpdate,
):
    """
    Actualiza una pregunta existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_pregunta/{id_pregunta}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=404,
            detail="Pregunta no encontrada",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_pregunta}", status_code=200)
async def eliminar_pregunta(id_pregunta: int):
    """
    Elimina una pregunta (respuesta explícita)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_pregunta/{id_pregunta}",
        )
        return {
            "ok": True,
            "mensaje": "Pregunta eliminada correctamente",
            "id_pregunta": id_pregunta,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Pregunta no encontrada",
            )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Error ORDS eliminando pregunta {id_pregunta}: "
                f"{e.response.text}"
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error interno eliminando pregunta {id_pregunta}: "
                f"{str(e)}"
            ),
        )
