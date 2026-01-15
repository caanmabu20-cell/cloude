from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("usuario-empresa")

router = APIRouter(
    prefix="/api/usuario-empresa",
    tags=["Usuario Empresa"],
)

# ======================================================
# MODELOS (ADMIN.CE_USUARIO_EMPRESA)
# ======================================================

class UsuarioEmpresaBase(BaseModel):
    id_usuario: int
    id_empresa: int
    id_rol_empresa: Optional[int] = None
    fl_puede_responder: str = "N"
    fl_puede_ver_resultados: str = "Y"
    fl_activo: str = "Y"


class UsuarioEmpresaCreate(UsuarioEmpresaBase):
    pass


class UsuarioEmpresaUpdate(BaseModel):
    id_usuario: Optional[int] = None
    id_empresa: Optional[int] = None
    id_rol_empresa: Optional[int] = None
    fl_puede_responder: Optional[str] = None
    fl_puede_ver_resultados: Optional[str] = None
    fl_activo: Optional[str] = None


class UsuarioEmpresaResponse(UsuarioEmpresaBase):
    id_usuario_empresa: int
    dt_creacion: Optional[str] = None


# ======================================================
# HELPERS ORDS
# ======================================================

def limpiar_item(item: dict) -> dict:
    item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ======================================================
# CRUD
# ======================================================

@router.get("/", response_model=List[UsuarioEmpresaResponse])
async def listar_usuario_empresa():
    """
    Lista asignaciones usuario-empresa (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_usuario_empresa/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_usuario_empresa}", response_model=UsuarioEmpresaResponse)
async def obtener_usuario_empresa(id_usuario_empresa: int):
    """
    Obtiene asignación usuario-empresa por ID
    """
    try:
        data = await ords_request("GET", f"/ce_usuario_empresa/{id_usuario_empresa}")
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Usuario-empresa no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=UsuarioEmpresaResponse, status_code=201)
async def crear_usuario_empresa(payload: UsuarioEmpresaCreate):
    """
    Crea asignación usuario-empresa
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_usuario_empresa/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_usuario_empresa}", response_model=UsuarioEmpresaResponse)
async def actualizar_usuario_empresa(id_usuario_empresa: int, payload: UsuarioEmpresaUpdate):
    """
    Actualiza asignación usuario-empresa (parcial)
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_usuario_empresa/{id_usuario_empresa}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Usuario-empresa no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_usuario_empresa}", status_code=200)
async def eliminar_usuario_empresa(id_usuario_empresa: int):
    """
    Elimina asignación usuario-empresa con confirmación explícita
    """
    try:
        await ords_request("DELETE", f"/ce_usuario_empresa/{id_usuario_empresa}")
        return {
            "ok": True,
            "mensaje": "Usuario-empresa eliminado correctamente",
            "id_usuario_empresa": id_usuario_empresa,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario-empresa no encontrado")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando usuario-empresa {id_usuario_empresa}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando usuario-empresa {id_usuario_empresa}: {str(e)}",
        )
