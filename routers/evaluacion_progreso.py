from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("evaluacion-progreso")

router = APIRouter(
    prefix="/api/evaluacion-progreso",
    tags=["Evaluación Progreso"],
)

# ============================
# MODELO
# ✅ COMPLETAMENTE REDISEÑADO según ORDS real:
# - id_capacidad agregado (CRÍTICO)
# - fl_completa agregado (Y/N)
# - dt_actualizacion agregado (timestamp)
# - Eliminados: total_items, completados, porcentaje, estado, fl_activo
#
# PROPÓSITO: Trackear si cada capacidad de una evaluación está completa
# Habrá 10 registros por evaluación (1 por capacidad)
# ============================

class EvaluacionProgreso(BaseModel):
    id_progreso: Optional[int] = None
    id_evaluacion: int                    # ✅ OK
    id_capacidad: int                     # ✅ Agregado (CRÍTICO)
    fl_completa: str = "N"                # ✅ Agregado (Y/N)
    dt_actualizacion: Optional[str] = None  # ✅ Agregado (read-only)


# ============================
# HELPERS ORDS
# ============================

def limpiar_item(item: dict) -> dict:
    """Elimina metadata ORDS (links, etc.)"""
    item.pop("links", None)
    return item


def limpiar_lista(data: dict) -> List[dict]:
    """Extrae solo items limpios desde ORDS"""
    items = data.get("items", [])
    return [limpiar_item(i) for i in items]


# ============================
# CRUD
# ============================

@router.get("/", response_model=List[EvaluacionProgreso])
async def listar_progresos():
    """
    Lista todos los registros de progreso
    ORDS: GET /ce_evaluacion_progreso/
    """
    try:
        data = await ords_request("GET", "/ce_evaluacion_progreso/")
        return limpiar_lista(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{id_progreso}", response_model=EvaluacionProgreso)
async def obtener_progreso(id_progreso: int):
    """
    Obtiene un registro de progreso por ID
    ORDS: GET /ce_evaluacion_progreso/{id}
    """
    try:
        data = await ords_request("GET", f"/ce_evaluacion_progreso/{id_progreso}")
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Progreso no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/", response_model=EvaluacionProgreso, status_code=201)
async def crear_progreso(payload: EvaluacionProgreso):
    """
    Crea un registro de progreso
    ORDS: POST /ce_evaluacion_progreso/
    """
    try:
        data = await ords_request(
            "POST",
            "/ce_evaluacion_progreso/",
            payload.model_dump(exclude_unset=True, exclude={"id_progreso", "dt_actualizacion"}),
        )
        return limpiar_item(data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{id_progreso}", response_model=EvaluacionProgreso)
async def actualizar_progreso(id_progreso: int, payload: EvaluacionProgreso):
    """
    Actualiza un registro de progreso
    ORDS: PUT /ce_evaluacion_progreso/{id}
    """
    try:
        data = await ords_request(
            "PUT",
            f"/ce_evaluacion_progreso/{id_progreso}",
            payload.model_dump(exclude_unset=True, exclude={"id_progreso", "dt_actualizacion"}),
        )
        return limpiar_item(data)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Progreso no encontrado")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{id_progreso}", status_code=200)
async def eliminar_progreso(id_progreso: int):
    """
    Elimina un registro de progreso
    ORDS: DELETE /ce_evaluacion_progreso/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_evaluacion_progreso/{id_progreso}")
        return {
            "ok": True,
            "mensaje": "Progreso eliminado correctamente",
            "id_progreso": id_progreso,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Progreso no encontrado")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS eliminando progreso {id_progreso}: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno eliminando progreso {id_progreso}: {str(e)}",
        )


# ============================
# ENDPOINTS ESPECÍFICOS ÚTILES
# ============================

@router.get("/evaluacion/{id_evaluacion}")
async def obtener_progreso_evaluacion(id_evaluacion: int):
    """
    Obtiene el progreso completo de una evaluación (10 capacidades)
    
    Retorna lista de 10 registros (1 por capacidad) con estado de completitud
    """
    try:
        import json
        filtro = json.dumps({"id_evaluacion": id_evaluacion})
        data = await ords_request("GET", f"/ce_evaluacion_progreso/?q={filtro}")
        items = limpiar_lista(data)
        
        # Calcular resumen
        total = len(items)
        completas = sum(1 for item in items if item.get("fl_completa") == "Y")
        porcentaje = (completas / total * 100) if total > 0 else 0
        
        return {
            "id_evaluacion": id_evaluacion,
            "total_capacidades": total,
            "capacidades_completas": completas,
            "porcentaje_completado": round(porcentaje, 2),
            "detalle": items
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.patch("/evaluacion/{id_evaluacion}/capacidad/{id_capacidad}/marcar-completa")
async def marcar_capacidad_completa(id_evaluacion: int, id_capacidad: int):
    """
    Marca una capacidad como completa
    
    Busca el registro de progreso y actualiza fl_completa = 'Y'
    """
    try:
        # Buscar el registro
        import json
        filtro = json.dumps({
            "id_evaluacion": id_evaluacion,
            "id_capacidad": id_capacidad
        })
        data = await ords_request("GET", f"/ce_evaluacion_progreso/?q={filtro}")
        items = data.get("items", [])
        
        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró progreso para evaluación {id_evaluacion} y capacidad {id_capacidad}"
            )
        
        # Actualizar
        id_progreso = items[0].get("id_progreso")
        resultado = await ords_request(
            "PUT",
            f"/ce_evaluacion_progreso/{id_progreso}",
            {"fl_completa": "Y"}
        )
        
        return limpiar_item(resultado)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.patch("/evaluacion/{id_evaluacion}/capacidad/{id_capacidad}/marcar-incompleta")
async def marcar_capacidad_incompleta(id_evaluacion: int, id_capacidad: int):
    """
    Marca una capacidad como incompleta
    
    Busca el registro de progreso y actualiza fl_completa = 'N'
    """
    try:
        # Buscar el registro
        import json
        filtro = json.dumps({
            "id_evaluacion": id_evaluacion,
            "id_capacidad": id_capacidad
        })
        data = await ords_request("GET", f"/ce_evaluacion_progreso/?q={filtro}")
        items = data.get("items", [])
        
        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró progreso para evaluación {id_evaluacion} y capacidad {id_capacidad}"
            )
        
        # Actualizar
        id_progreso = items[0].get("id_progreso")
        resultado = await ords_request(
            "PUT",
            f"/ce_evaluacion_progreso/{id_progreso}",
            {"fl_completa": "N"}
        )
        
        return limpiar_item(resultado)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/evaluacion/{id_evaluacion}/inicializar")
async def inicializar_progreso_evaluacion(id_evaluacion: int):
    """
    Crea los 10 registros de progreso iniciales para una evaluación
    (1 por cada capacidad activa)
    
    Útil cuando se crea una nueva evaluación
    """
    try:
        # Obtener capacidades activas
        capacidades_data = await ords_request("GET", "/ce_capacidad/?fl_activa=Y")
        capacidades = capacidades_data.get("items", [])
        
        if not capacidades:
            raise HTTPException(
                status_code=400,
                detail="No hay capacidades activas en el sistema"
            )
        
        # Crear registro de progreso para cada capacidad
        progresos_creados = []
        
        for capacidad in capacidades:
            id_capacidad = capacidad.get("id_capacidad")
            
            try:
                payload = {
                    "id_evaluacion": id_evaluacion,
                    "id_capacidad": id_capacidad,
                    "fl_completa": "N"
                }
                
                resultado = await ords_request(
                    "POST",
                    "/ce_evaluacion_progreso/",
                    payload
                )
                
                progresos_creados.append(limpiar_item(resultado))
                
            except Exception as e:
                logger.warning(f"Error creando progreso para capacidad {id_capacidad}: {e}")
        
        return {
            "ok": True,
            "mensaje": "Progreso inicializado correctamente",
            "id_evaluacion": id_evaluacion,
            "total_creados": len(progresos_creados),
            "detalle": progresos_creados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
