from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("resultados-evaluacion")

router = APIRouter(
    prefix="/api/resultados-evaluacion",
    tags=["Resultados Evaluación"],
)

# ======================================================
# MODELOS (ADMIN.CE_RESULTADO_EVALUACION)
# ======================================================

class ResultadoEvaluacionBase(BaseModel):
    id_evaluacion: int
    score_global: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    perfil: Optional[str] = None
    diagnostico_general: Optional[str] = None


class ResultadoEvaluacionCreate(ResultadoEvaluacionBase):
    # dt_generacion lo maneja la DB
    pass


class ResultadoEvaluacionUpdate(BaseModel):
    score_global: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    perfil: Optional[str] = None
    diagnostico_general: Optional[str] = None


class ResultadoEvaluacionResponse(ResultadoEvaluacionBase):
    id_resultado_eval: int
    dt_generacion: str


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

@router.get("/", response_model=List[ResultadoEvaluacionResponse])
async def listar_resultados_evaluacion():
    """
    Lista resultados de evaluación (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_resultado_evaluacion/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_resultado_eval}", response_model=ResultadoEvaluacionResponse)
async def obtener_resultado_evaluacion(id_resultado_eval: int):
    """
    Obtiene un resultado de evaluación por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_resultado_evaluacion/{id_resultado_eval}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Resultado evaluación no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=ResultadoEvaluacionResponse, status_code=201)
async def crear_resultado_evaluacion(payload: ResultadoEvaluacionCreate):
    """
    Crea resultado de evaluación (dt_generacion automático)
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_resultado_evaluacion/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_resultado_eval}", response_model=ResultadoEvaluacionResponse)
async def actualizar_resultado_evaluacion(
    id_resultado_eval: int,
    payload: ResultadoEvaluacionUpdate,
):
    """
    Actualiza resultado de evaluación
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_resultado_evaluacion/{id_resultado_eval}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Resultado evaluación no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_resultado_eval}", status_code=200)
async def eliminar_resultado_evaluacion(id_resultado_eval: int):
    """
    Elimina resultado de evaluación (mensaje explícito)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_resultado_evaluacion/{id_resultado_eval}",
        )
        return {
            "ok": True,
            "mensaje": "Resultado de evaluación eliminado correctamente",
            "id_resultado_eval": id_resultado_eval,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Resultado evaluación no encontrado",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando resultado_evaluacion {id_resultado_eval}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando resultado_evaluacion {id_resultado_eval}: {str(e)}",
        )
