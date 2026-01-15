from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("reglas")

router = APIRouter(
    prefix="/api/reglas",
    tags=["Reglas"],
)

# ============================
# MODELOS (alineados a ADMIN.CE_REGLA)
# ============================

class ReglaBase(BaseModel):
    id_version: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_regla: Literal["umbral", "conteo", "comparacion", "combinada"]
    fl_activa: Literal["Y", "N"] = "Y"


class ReglaCreate(ReglaBase):
    pass


class ReglaUpdate(BaseModel):
    id_version: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_regla: Optional[
        Literal["umbral", "conteo", "comparacion", "combinada"]
    ] = None
    fl_activa: Optional[Literal["Y", "N"]] = None


class ReglaResponse(ReglaBase):
    id_regla: int


# ============================
# HELPERS
# ============================

def limpiar_item(item: dict) -> dict:
    """
    Elimina metadata ORDS (links, etc)
    """
    item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    """
    Extrae solo los items desde ORDS sin metadata
    """
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ============================
# CRUD
# ============================

@router.get("/", response_model=List[ReglaResponse])
async def listar_reglas():
    """
    Lista todas las reglas
    """
    try:
        data = await ords_request("GET", "/ce_regla/")
        return limpiar_lista(data)

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_regla}", response_model=ReglaResponse)
async def obtener_regla(id_regla: int):
    """
    Obtiene una regla por ID
    """
    try:
        data = await ords_request("GET", f"/ce_regla/{id_regla}")
        return limpiar_item(data)

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=ReglaResponse, status_code=201)
async def crear_regla(payload: ReglaCreate):
    """
    Crea una nueva regla
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_regla/",
            payload.dict(exclude_unset=True),
        )

        return limpiar_item(data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail=f"Error de validación ORDS: {e.response.text}",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS creando regla: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_regla}", response_model=ReglaResponse)
async def actualizar_regla(id_regla: int, payload: ReglaUpdate):
    """
    Actualiza una regla existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_regla/{id_regla}",
            payload.dict(exclude_unset=True),
        )

        return limpiar_item(data)

    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))



@router.delete("/{id_regla}", status_code=200)
async def eliminar_regla(id_regla: int):
    """
    Elimina una regla (devuelve mensaje de éxito)
    """
    try:
        logger.info("DELETE REGLA id=%s -> ORDS /ce_regla/%s", id_regla, id_regla)

        await ords_request("DELETE", f"/ce_regla/{id_regla}")

        return {
            "ok": True,
            "mensaje": "Regla eliminada correctamente",
            "id_regla": id_regla,
        }

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        body = e.response.text

        logger.error("ORDS DELETE regla error %s: %s", status, body)

        if status == 404:
            raise HTTPException(status_code=404, detail="Regla no encontrada")

        raise HTTPException(
            status_code=502,
            detail=f"ORDS error eliminando regla {id_regla}: {body}",
        )

    except Exception as e:
        logger.exception("Error interno eliminando regla %s", id_regla)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando regla {id_regla}: {str(e)}",
        )
