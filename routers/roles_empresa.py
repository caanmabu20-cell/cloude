from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("roles-empresa")

router = APIRouter(
    prefix="/api/roles-empresa",
    tags=["Roles Empresa"],
)

# ======================================================
# MODELOS (ADMIN.CE_ROL_EMPRESA)
# ======================================================

class RolEmpresaBase(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    fl_activo: str = "Y"


class RolEmpresaCreate(RolEmpresaBase):
    pass


class RolEmpresaUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    fl_activo: Optional[str] = None


class RolEmpresaResponse(RolEmpresaBase):
    id_rol_empresa: int


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

@router.get("/", response_model=List[RolEmpresaResponse])
async def listar_roles_empresa():
    """
    Lista roles de empresa (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_rol_empresa/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_rol_empresa}", response_model=RolEmpresaResponse)
async def obtener_rol_empresa(id_rol_empresa: int):
    """
    Obtiene rol de empresa por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_rol_empresa/{id_rol_empresa}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Rol de empresa no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=RolEmpresaResponse, status_code=201)
async def crear_rol_empresa(payload: RolEmpresaCreate):
    """
    Crea un rol de empresa
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_rol_empresa/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_rol_empresa}", response_model=RolEmpresaResponse)
async def actualizar_rol_empresa(
    id_rol_empresa: int,
    payload: RolEmpresaUpdate,
):
    """
    Actualiza un rol de empresa
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_rol_empresa/{id_rol_empresa}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Rol de empresa no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_rol_empresa}", status_code=200)
async def eliminar_rol_empresa(id_rol_empresa: int):
    """
    Elimina rol de empresa con confirmación explícita
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_rol_empresa/{id_rol_empresa}",
        )
        return {
            "ok": True,
            "mensaje": "Rol de empresa eliminado correctamente",
            "id_rol_empresa": id_rol_empresa,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Rol de empresa no encontrado",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando rol_empresa {id_rol_empresa}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando rol_empresa {id_rol_empresa}: {str(e)}",
        )
