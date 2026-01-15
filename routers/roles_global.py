from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("roles-global")

router = APIRouter(
    prefix="/api/roles-global",
    tags=["Roles Globales"],
)

# ======================================================
# MODELOS (ADMIN.CE_ROL_GLOBAL)
# ======================================================

class RolGlobalBase(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    fl_activo: str = "Y"


class RolGlobalCreate(RolGlobalBase):
    pass


class RolGlobalUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    fl_activo: Optional[str] = None


class RolGlobalResponse(RolGlobalBase):
    id_rol_global: int


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

@router.get("/", response_model=List[RolGlobalResponse])
async def listar_roles_globales():
    """
    Lista roles globales
    """
    try:
        data = await ords_request("GET", "/ce_rol_global/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_rol_global}", response_model=RolGlobalResponse)
async def obtener_rol_global(id_rol_global: int):
    """
    Obtiene rol global por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_rol_global/{id_rol_global}",
        )
        return limpiar_item(data)

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Rol global no encontrado")

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=RolGlobalResponse, status_code=201)
async def crear_rol_global(payload: RolGlobalCreate):
    """
    Crea un rol global
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_rol_global/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_rol_global}", response_model=RolGlobalResponse)
async def actualizar_rol_global(
    id_rol_global: int,
    payload: RolGlobalUpdate,
):
    """
    Actualiza un rol global
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_rol_global/{id_rol_global}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Rol global no encontrado")

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_rol_global}", status_code=200)
async def eliminar_rol_global(id_rol_global: int):
    """
    Elimina rol global con confirmación explícita
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_rol_global/{id_rol_global}",
        )
        return {
            "ok": True,
            "mensaje": "Rol global eliminado correctamente",
            "id_rol_global": id_rol_global,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Rol global no encontrado",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando rol_global {id_rol_global}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando rol_global {id_rol_global}: {str(e)}",
        )
