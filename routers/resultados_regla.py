from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("resultados-regla")

router = APIRouter(
    prefix="/api/resultados-regla",
    tags=["Resultados Regla"],
)

# ======================================================
# MODELOS (ADMIN.CE_RESULTADO_REGLA)
# ======================================================

class ResultadoReglaBase(BaseModel):
    id_evaluacion: int
    id_regla: int
    fl_cumple: str  # 'Y' | 'N'
    valor_numerico: Optional[float] = None
    detalle_json: Optional[str] = None


class ResultadoReglaCreate(ResultadoReglaBase):
    # dt_calculo lo maneja la DB
    pass


class ResultadoReglaUpdate(BaseModel):
    fl_cumple: Optional[str] = None
    valor_numerico: Optional[float] = None
    detalle_json: Optional[str] = None


class ResultadoReglaResponse(ResultadoReglaBase):
    id_resultado_regla: int
    dt_calculo: str


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

@router.get("/", response_model=List[ResultadoReglaResponse])
async def listar_resultados_regla():
    """
    Lista resultados de reglas (sin metadata ORDS)
    """
    try:
        data = await ords_request("GET", "/ce_resultado_regla/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_resultado_regla}", response_model=ResultadoReglaResponse)
async def obtener_resultado_regla(id_resultado_regla: int):
    """
    Obtiene resultado de regla por ID
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_resultado_regla/{id_resultado_regla}",
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Resultado de regla no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=ResultadoReglaResponse, status_code=201)
async def crear_resultado_regla(payload: ResultadoReglaCreate):
    """
    Crea resultado de evaluación de regla
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_resultado_regla/",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_resultado_regla}", response_model=ResultadoReglaResponse)
async def actualizar_resultado_regla(
    id_resultado_regla: int,
    payload: ResultadoReglaUpdate,
):
    """
    Actualiza resultado de regla
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_resultado_regla/{id_resultado_regla}",
            payload.dict(exclude_unset=True),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Resultado de regla no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_resultado_regla}", status_code=200)
async def eliminar_resultado_regla(id_resultado_regla: int):
    """
    Elimina resultado de regla (mensaje explícito)
    """
    try:
        await ords_request(
            "DELETE",
            f"/ce_resultado_regla/{id_resultado_regla}",
        )
        return {
            "ok": True,
            "mensaje": "Resultado de regla eliminado correctamente",
            "id_resultado_regla": id_resultado_regla,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Resultado de regla no encontrado",
            )

        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando resultado_regla {id_resultado_regla}: {e.response.text}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando resultado_regla {id_resultado_regla}: {str(e)}",
        )
