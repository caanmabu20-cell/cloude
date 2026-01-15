from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

# =====================================================
# LOGGING
# =====================================================

logger = logging.getLogger("condiciones-regla")

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/api/condiciones-regla",
    tags=["Condiciones de Regla"],
)

# =====================================================
# MODELOS (ALINEADOS 100% A ORACLE)
# =====================================================

class CondicionReglaBase(BaseModel):
    id_regla: int
    orden: int
    conector: str = "AND"
    metrica: str = "SCORE_CAP_DIM"
    id_capacidad: Optional[int] = None
    id_dimension: Optional[int] = None
    operador: str
    valor1: float
    valor2: Optional[float] = None
    grupo: int = 1


class CondicionReglaCreate(CondicionReglaBase):
    pass


class CondicionReglaUpdate(BaseModel):
    id_regla: Optional[int] = None
    orden: Optional[int] = None
    conector: Optional[str] = None
    metrica: Optional[str] = None
    id_capacidad: Optional[int] = None
    id_dimension: Optional[int] = None
    operador: Optional[str] = None
    valor1: Optional[float] = None
    valor2: Optional[float] = None
    grupo: Optional[int] = None


class CondicionReglaResponse(CondicionReglaBase):
    id_condicion: int

# =====================================================
# HELPERS (LIMPIEZA ORDS)
# =====================================================

def limpiar_item(item: dict) -> dict:
    """
    Elimina metadata innecesaria de ORDS (links, etc.)
    """
    if isinstance(item, dict):
        item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    """
    Extrae items y elimina metadata de ORDS
    """
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]

# =====================================================
# CRUD
# =====================================================

@router.get("/", response_model=List[CondicionReglaResponse])
async def listar_condiciones():
    """
    Lista todas las condiciones de regla
    """
    try:
        data = await ords_request("GET", "/ce_condicion_regla/")
        return limpiar_lista(data)
    except Exception as e:
        logger.exception("Error listando condiciones")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_condicion}", response_model=CondicionReglaResponse)
async def obtener_condicion(id_condicion: int):
    """
    Obtiene una condición por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_condicion_regla/{id_condicion}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Condición no encontrada")
    except Exception as e:
        logger.exception("Error obteniendo condición")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=CondicionReglaResponse, status_code=201)
async def crear_condicion(payload: CondicionReglaCreate):
    """
    Crea una nueva condición de regla
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_condicion_regla/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        logger.exception("Error creando condición")
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_condicion}", response_model=CondicionReglaResponse)
async def actualizar_condicion(id_condicion: int, payload: CondicionReglaUpdate):
    """
    Actualiza una condición existente
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_condicion_regla/{id_condicion}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Condición no encontrada")
    except Exception as e:
        logger.exception("Error actualizando condición")
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_condicion}", status_code=204)
async def eliminar_condicion(id_condicion: int):
    """
    Elimina una condición de regla
    """
    try:
        logger.info("🧨 DELETE CONDICION_REGLA")
        logger.info("➡️ ID: %s", id_condicion)
        logger.info("➡️ ORDS PATH: /ce_condicion_regla/%s", id_condicion)

        # ORDS requiere body vacío en DELETE
        await ords_request(
            "DELETE",
            f"/ce_condicion_regla/{id_condicion}",
            payload={},
        )

        logger.info("✅ DELETE OK")
        return

    except httpx.HTTPStatusError as e:
        logger.error("❌ ORDS HTTP ERROR %s", e.response.status_code)
        logger.error("❌ BODY: %s", e.response.text)

        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Condición no encontrada")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando condición {id_condicion}: {e.response.text}",
        )

    except Exception as e:
        logger.exception("🔥 ERROR NO ESPERADO EN DELETE")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando condición {id_condicion}: {str(e)}",
        )
