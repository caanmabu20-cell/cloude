from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("usuarios")

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"],
)

# ======================================================
# MODELOS (ADMIN.CE_USUARIO)
# ======================================================

class UsuarioBase(BaseModel):
    nombre: str
    email: str
    id_rol_global: int
    fl_activo: str = "Y"


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    id_rol_global: Optional[int] = None
    fl_activo: Optional[str] = None


class UsuarioResponse(UsuarioBase):
    id_usuario: int
    dt_creacion: Optional[str] = None


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
    Extrae solo items limpios desde ORDS
    """
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ======================================================
# CRUD
# ======================================================

@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios():
    """
    Lista usuarios (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_usuario/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_usuario}", response_model=UsuarioResponse)
async def obtener_usuario(id_usuario: int):
    """
    Obtiene un usuario por ID
    """
    try:
        data = await ords_request("GET", f"/ce_usuario/{id_usuario}")
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=UsuarioResponse, status_code=201)
async def crear_usuario(payload: UsuarioCreate):
    """
    Crea un usuario (dt_creacion lo maneja DB)
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_usuario/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_usuario}", response_model=UsuarioResponse)
async def actualizar_usuario(id_usuario: int, payload: UsuarioUpdate):
    """
    Actualiza un usuario (parcial)
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_usuario/{id_usuario}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_usuario}", status_code=200)
async def eliminar_usuario(id_usuario: int):
    """
    Elimina usuario con confirmación explícita
    """
    try:
        await ords_request("DELETE", f"/ce_usuario/{id_usuario}")
        return {
            "ok": True,
            "mensaje": "Usuario eliminado correctamente",
            "id_usuario": id_usuario,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando usuario {id_usuario}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando usuario {id_usuario}: {str(e)}",
        )
