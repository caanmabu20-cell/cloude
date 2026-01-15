from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("lecturas-ejecutivas")

router = APIRouter(
    prefix="/api/lecturas-ejecutivas",
    tags=["Lecturas Ejecutivas"],
)

# ======================================================
# MODELOS (100% alineados a ADMIN.CE_LECTURA_EJECUTIVA)
# ======================================================

class LecturaBase(BaseModel):
    id_version: int
    id_contexto: int
    id_capacidad: Optional[int] = None
    id_dimension: Optional[int] = None
    rango_inferior: float
    rango_superior: float
    estado: str
    lectura: str
    orden: int
    fl_activa: str = "Y"


class LecturaCreate(LecturaBase):
    pass


class LecturaUpdate(BaseModel):
    id_version: Optional[int] = None
    id_contexto: Optional[int] = None
    id_capacidad: Optional[int] = None
    id_dimension: Optional[int] = None
    rango_inferior: Optional[float] = None
    rango_superior: Optional[float] = None
    estado: Optional[str] = None
    lectura: Optional[str] = None
    orden: Optional[int] = None
    fl_activa: Optional[str] = None


class LecturaResponse(LecturaBase):
    id_lectura: int


# ============================
# HELPERS (LIMPIEZA ORDS)
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

@router.get("/", response_model=List[LecturaResponse])
async def listar_lecturas():
    """
    Lista todas las lecturas ejecutivas
    """
    try:
        data = await ords_request("GET", "/ce_lectura_ejecutiva/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_lectura}", response_model=LecturaResponse)
async def obtener_lectura(id_lectura: int):
    """
    Obtiene una lectura ejecutiva por ID
    """
    try:
        data = await ords_request(
            "GET", f"/ce_lectura_ejecutiva/{id_lectura}"
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=LecturaResponse, status_code=201)
async def crear_lectura(payload: LecturaCreate):
    """
    Crea una nueva lectura ejecutiva
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_lectura_ejecutiva/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_lectura}", response_model=LecturaResponse)
async def actualizar_lectura(
    id_lectura: int,
    payload: LecturaUpdate,
):
    """
    Actualiza una lectura ejecutiva existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_lectura_ejecutiva/{id_lectura}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_lectura}", status_code=200)
async def eliminar_lectura(id_lectura: int):
    """
    Elimina una lectura ejecutiva (respuesta explícita)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_lectura_ejecutiva/{id_lectura}",
        )
        return {
            "ok": True,
            "mensaje": "Lectura ejecutiva eliminada correctamente",
            "id_lectura": id_lectura,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Lectura no encontrada",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando lectura {id_lectura}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando lectura {id_lectura}: {str(e)}",
        )
