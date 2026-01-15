from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("version-metodologia")

router = APIRouter(
    prefix="/api/versiones-metodologia",
    tags=["Versiones Metodología"],
)

# ======================================================
# MODELOS (ADMIN.CE_VERSION_METODOLOGIA)
# ======================================================

class VersionMetodologiaBase(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    fl_activa: str = "Y"


class VersionMetodologiaCreate(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    fl_activa: Optional[str] = "Y"


class VersionMetodologiaUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    fl_activa: Optional[str] = None


class VersionMetodologiaResponse(VersionMetodologiaBase):
    id_version: int
    dt_inicio: Optional[str] = None


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

@router.get("/", response_model=List[VersionMetodologiaResponse])
async def listar_versiones():
    """
    Lista versiones de metodología
    """
    try:
        data = await ords_request("GET", "/ce_version_metodologia/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_version}", response_model=VersionMetodologiaResponse)
async def obtener_version(id_version: int):
    """
    Obtiene versión por ID
    """
    try:
        data = await ords_request(
            "GET", f"/ce_version_metodologia/{id_version}"
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Versión de metodología no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=VersionMetodologiaResponse, status_code=201)
async def crear_version(payload: VersionMetodologiaCreate):
    """
    Crea nueva versión de metodología
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_version_metodologia/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_version}", response_model=VersionMetodologiaResponse)
async def actualizar_version(id_version: int, payload: VersionMetodologiaUpdate):
    """
    Actualiza versión de metodología
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_version_metodologia/{id_version}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Versión de metodología no encontrada")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_version}", status_code=200)
async def eliminar_version(id_version: int):
    """
    Elimina versión de metodología con confirmación explícita
    """
    try:
        await ords_request(
            "DELETE", f"/ce_version_metodologia/{id_version}"
        )
        return {
            "ok": True,
            "mensaje": "Versión de metodología eliminada correctamente",
            "id_version": id_version,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Versión de metodología no encontrada")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando versión {id_version}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando versión {id_version}: {str(e)}",
        )
