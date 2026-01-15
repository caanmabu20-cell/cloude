from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

from core.ords_client import ords_request

router = APIRouter(
    prefix="/api/capacidades",
    tags=["Capacidades"],
)

# ============================
# MODELOS (alineados a la DB)
# ============================

class CapacidadBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    orden: int
    fl_activa: str = "Y"


class CapacidadCreate(CapacidadBase):
    pass


class CapacidadUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    fl_activa: Optional[str] = None


class CapacidadResponse(CapacidadBase):
    id_capacidad: int


# ============================
# HELPERS
# ============================

def limpiar_item(item: dict) -> dict:
    """
    Elimina metadata de ORDS (links, etc)
    """
    item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    """
    Extrae solo los items limpios desde ORDS
    """
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ============================
# CRUD
# ============================

@router.get("/", response_model=List[CapacidadResponse])
async def listar_capacidades():
    """
    Lista todas las capacidades (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_capacidad/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_capacidad}", response_model=CapacidadResponse)
async def obtener_capacidad(id_capacidad: int):
    """
    Obtiene una capacidad por ID
    """
    try:
        data = await ords_request("GET", f"/ce_capacidad/{id_capacidad}")
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Capacidad no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=CapacidadResponse, status_code=201)
async def crear_capacidad(payload: CapacidadCreate):
    """
    Crea una nueva capacidad
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_capacidad/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_capacidad}", response_model=CapacidadResponse)
async def actualizar_capacidad(id_capacidad: int, payload: CapacidadUpdate):
    """
    Actualiza una capacidad existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_capacidad/{id_capacidad}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Capacidad no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_capacidad}", status_code=200)
async def eliminar_capacidad(id_capacidad: int):
    """
    Elimina una capacidad
    """
    try:
        print("🧨 DELETE CAPACIDAD")
        print(f"➡️ ID: {id_capacidad}")
        print(f"➡️ ORDS PATH: /ce_capacidad/{id_capacidad}")

        await ords_request(
            "DELETE",
            f"/ce_capacidad/{id_capacidad}",
            payload={},  # requerido por ORDS
        )

        print("✅ DELETE OK")

        return {
            "message": "Capacidad eliminada correctamente",
            "id_capacidad": id_capacidad,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Capacidad no encontrada")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando capacidad {id_capacidad}: {e.response.text}",
        )
