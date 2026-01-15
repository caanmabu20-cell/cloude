from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("resultados-capacidad")

router = APIRouter(
    prefix="/api/resultados-capacidad",
    tags=["Resultados Capacidad"],
)

# ======================================================
# MODELOS (alineados a ADMIN.CE_RESULTADO_CAPACIDAD)
# ======================================================

class ResultadoCapacidadBase(BaseModel):
    id_evaluacion: int
    id_capacidad: int
    score_final: float
    id_normalizacion: Optional[int] = None
    id_lectura: Optional[int] = None


class ResultadoCapacidadCreate(ResultadoCapacidadBase):
    # dt_generacion lo pone la DB por default
    pass


class ResultadoCapacidadUpdate(BaseModel):
    id_evaluacion: Optional[int] = None
    id_capacidad: Optional[int] = None
    score_final: Optional[float] = None
    id_normalizacion: Optional[int] = None
    id_lectura: Optional[int] = None


class ResultadoCapacidadResponse(ResultadoCapacidadBase):
    id_resultado_cap: int
    dt_generacion: str  # ORDS suele devolver timestamp como string


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

@router.get("/", response_model=List[ResultadoCapacidadResponse])
async def listar_resultados_capacidad():
    """
    Lista resultados por capacidad (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_resultado_capacidad/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_resultado_cap}", response_model=ResultadoCapacidadResponse)
async def obtener_resultado_capacidad(id_resultado_cap: int):
    """
    Obtiene un resultado por ID
    """
    try:
        data = await ords_request("GET", f"/ce_resultado_capacidad/{id_resultado_cap}")
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Resultado capacidad no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=ResultadoCapacidadResponse, status_code=201)
async def crear_resultado_capacidad(payload: ResultadoCapacidadCreate):
    """
    Crea un resultado por capacidad (dt_generacion lo pone la DB)
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_resultado_capacidad/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_resultado_cap}", response_model=ResultadoCapacidadResponse)
async def actualizar_resultado_capacidad(id_resultado_cap: int, payload: ResultadoCapacidadUpdate):
    """
    Actualiza un resultado por capacidad
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_resultado_capacidad/{id_resultado_cap}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Resultado capacidad no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_resultado_cap}", status_code=200)
async def eliminar_resultado_capacidad(id_resultado_cap: int):
    """
    Elimina un resultado por capacidad (mensaje explícito para frontend)
    """
    try:
        await ords_request("DELETE", f"/ce_resultado_capacidad/{id_resultado_cap}")
        return {
            "ok": True,
            "mensaje": "Resultado por capacidad eliminado correctamente",
            "id_resultado_cap": id_resultado_cap,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Resultado capacidad no encontrado")

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando resultado_capacidad {id_resultado_cap}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando resultado_capacidad {id_resultado_cap}: {str(e)}",
        )
