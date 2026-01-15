from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("respuestas")

router = APIRouter(
    prefix="/api/respuestas",
    tags=["Respuestas"],
)

# ======================================================
# MODELOS (alineados a ADMIN.CE_RESPUESTA)
# ======================================================

class RespuestaBase(BaseModel):
    id_evaluacion: int
    id_pregunta: int
    id_opcion: int
    id_usuario_resp: int


class RespuestaCreate(RespuestaBase):
    # dt_respuesta NO se envía (la DB la asigna por default)
    pass


class RespuestaUpdate(BaseModel):
    # normalmente no se “edita” una respuesta, pero dejamos el PUT por estándar
    id_evaluacion: Optional[int] = None
    id_pregunta: Optional[int] = None
    id_opcion: Optional[int] = None
    id_usuario_resp: Optional[int] = None


class RespuestaResponse(RespuestaBase):
    id_respuesta: int
    dt_respuesta: str  # ORDS suele devolver timestamp como string


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

@router.get("/", response_model=List[RespuestaResponse])
async def listar_respuestas():
    """
    Lista todas las respuestas (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_respuesta/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_respuesta}", response_model=RespuestaResponse)
async def obtener_respuesta(id_respuesta: int):
    """
    Obtiene una respuesta por ID
    """
    try:
        data = await ords_request("GET", f"/ce_respuesta/{id_respuesta}")
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=RespuestaResponse, status_code=201)
async def crear_respuesta(payload: RespuestaCreate):
    """
    Crea una nueva respuesta (dt_respuesta lo pone la DB)
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_respuesta/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_respuesta}", response_model=RespuestaResponse)
async def actualizar_respuesta(id_respuesta: int, payload: RespuestaUpdate):
    """
    Actualiza una respuesta (por estándar)
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_respuesta/{id_respuesta}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_respuesta}", status_code=200)
async def eliminar_respuesta(id_respuesta: int):
    """
    Elimina una respuesta (respuesta explícita para frontend)
    """
    try:
        await ords_request("DELETE", f"/ce_respuesta/{id_respuesta}")
        return {
            "ok": True,
            "mensaje": "Respuesta eliminada correctamente",
            "id_respuesta": id_respuesta,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Respuesta no encontrada")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando respuesta {id_respuesta}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando respuesta {id_respuesta}: {str(e)}",
        )
