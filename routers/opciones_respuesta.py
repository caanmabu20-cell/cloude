from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("opciones-respuesta")

router = APIRouter(
    prefix="/api/opciones-respuesta",
    tags=["Opciones de Respuesta"],
)

# ======================================================
# MODELOS (alineados a ADMIN.CE_OPCION_RESPUESTA)
# ======================================================

class OpcionRespuestaBase(BaseModel):
    id_pregunta: int
    codigo: str
    texto: Optional[str] = None
    valor_base: float
    orden: int


class OpcionRespuestaCreate(OpcionRespuestaBase):
    pass


class OpcionRespuestaUpdate(BaseModel):
    id_pregunta: Optional[int] = None
    codigo: Optional[str] = None
    texto: Optional[str] = None
    valor_base: Optional[float] = None
    orden: Optional[int] = None


class OpcionRespuestaResponse(OpcionRespuestaBase):
    id_opcion: int


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

@router.get("/", response_model=List[OpcionRespuestaResponse])
async def listar_opciones():
    """
    Lista todas las opciones de respuesta
    """
    try:
        data = await ords_request("GET", "/ce_opcion_respuesta/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_opcion}", response_model=OpcionRespuestaResponse)
async def obtener_opcion(id_opcion: int):
    """
    Obtiene una opción por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_opcion_respuesta/{id_opcion}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Opción de respuesta no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=OpcionRespuestaResponse, status_code=201)
async def crear_opcion(payload: OpcionRespuestaCreate):
    """
    Crea una nueva opción de respuesta
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_opcion_respuesta/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_opcion}", response_model=OpcionRespuestaResponse)
async def actualizar_opcion(
    id_opcion: int,
    payload: OpcionRespuestaUpdate,
):
    """
    Actualiza una opción de respuesta existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_opcion_respuesta/{id_opcion}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Opción de respuesta no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_opcion}", status_code=200)
async def eliminar_opcion(id_opcion: int):
    """
    Elimina una opción de respuesta (respuesta explícita)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_opcion_respuesta/{id_opcion}",
        )
        return {
            "ok": True,
            "mensaje": "Opción de respuesta eliminada correctamente",
            "id_opcion": id_opcion,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Opción de respuesta no encontrada",
            )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Error ORDS eliminando opción {id_opcion}: "
                f"{e.response.text}"
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error interno eliminando opción {id_opcion}: "
                f"{str(e)}"
            ),
        )
