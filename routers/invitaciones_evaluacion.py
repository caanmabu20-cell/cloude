from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("invitaciones-evaluacion")

router = APIRouter(
    prefix="/api/invitaciones-evaluacion",
    tags=["Invitaciones Evaluación"],
)

# ======================================================
# MODELOS (100% alineados a ADMIN.CE_INVITACION_EVALUACION)
# ======================================================

class InvitacionBase(BaseModel):
    id_evaluacion: int
    id_usuario: int
    id_empresa: int
    estado: Optional[str] = "enviada"
    dt_envio: Optional[str] = None
    dt_respuesta: Optional[str] = None
    token: Optional[str] = None


class InvitacionCreate(InvitacionBase):
    pass


class InvitacionUpdate(BaseModel):
    estado: Optional[str] = None
    dt_respuesta: Optional[str] = None
    token: Optional[str] = None


class InvitacionResponse(InvitacionBase):
    id_invitacion: int


# ============================
# HELPERS (ORDS CLEAN)
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

@router.get("/", response_model=List[InvitacionResponse])
async def listar_invitaciones():
    """
    Lista todas las invitaciones (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_invitacion_evaluacion/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_invitacion}", response_model=InvitacionResponse)
async def obtener_invitacion(id_invitacion: int):
    """
    Obtiene una invitación por ID
    """
    try:
        data = await ords_request(
            "GET", f"/ce_invitacion_evaluacion/{id_invitacion}"
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=InvitacionResponse, status_code=201)
async def crear_invitacion(payload: InvitacionCreate):
    """
    Crea una nueva invitación de evaluación
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_invitacion_evaluacion/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_invitacion}", response_model=InvitacionResponse)
async def actualizar_invitacion(
    id_invitacion: int,
    payload: InvitacionUpdate,
):
    """
    Actualiza una invitación existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_invitacion_evaluacion/{id_invitacion}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_invitacion}", status_code=200)
async def eliminar_invitacion(id_invitacion: int):
    """
    Elimina una invitación (respuesta explícita de éxito)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_invitacion_evaluacion/{id_invitacion}",
        )
        return {
            "ok": True,
            "mensaje": "Invitación eliminada correctamente",
            "id_invitacion": id_invitacion,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Invitación no encontrada",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando invitación {id_invitacion}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando invitación {id_invitacion}: {str(e)}",
        )
