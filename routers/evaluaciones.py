from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("evaluaciones")

router = APIRouter(
    prefix="/evaluaciones",
    tags=["Evaluaciones"],
)

# ============================
# MODELO
# ✅ CORREGIDO según ORDS real:
# - id_usuario_lider agregado
# - id_version agregado
# - tipo agregado (inicial/seguimiento)
# - modo_evaluacion agregado (consultor/cliente)
# - porcentaje_completado (no porcentaje_avance)
# - dt_inicio y dt_cierre agregados
# - Eliminado: periodo, fl_activo
# ============================

class Evaluacion(BaseModel):
    id_evaluacion: Optional[int] = None
    id_empresa: int                           # ✅ OK
    id_usuario_lider: int                     # ✅ Agregado (quién lidera la evaluación)
    id_version: int                           # ✅ Agregado (versión de metodología)
    nombre: str                               # ✅ OK
    tipo: str = "seguimiento"                 # ✅ Agregado (inicial/seguimiento)
    modo_evaluacion: str = "consultor"        # ✅ Agregado (consultor/cliente)
    estado: str = "en_progreso"               # ✅ OK
    porcentaje_completado: float = 0.0        # ✅ Renombrado (era porcentaje_avance)
    dt_inicio: Optional[str] = None           # ✅ Agregado
    dt_cierre: Optional[str] = None           # ✅ Agregado


# ============================
# GET LIST
# ============================

@router.get("/")
async def listar_evaluaciones():
    """
    ORDS: GET /ce_evaluacion/
    """
    try:
        return await ords_request("GET", "/ce_evaluacion/")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )


# ============================
# GET BY ID
# ============================

@router.get("/{id_evaluacion}")
async def obtener_evaluacion(id_evaluacion: int):
    """
    ORDS: GET /ce_evaluacion/{id}
    """
    try:
        return await ords_request("GET", f"/ce_evaluacion/{id_evaluacion}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# POST
# ============================

@router.post("/", status_code=201)
async def crear_evaluacion(data: Evaluacion):
    """
    ORDS: POST /ce_evaluacion/
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_evaluacion"})
        return await ords_request("POST", "/ce_evaluacion/", payload)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )


# ============================
# PUT
# ============================

@router.put("/{id_evaluacion}")
async def actualizar_evaluacion(id_evaluacion: int, data: Evaluacion):
    """
    ORDS: PUT /ce_evaluacion/{id}
    """
    try:
        payload = data.model_dump(exclude_unset=True, exclude={"id_evaluacion"})
        return await ords_request(
            "PUT",
            f"/ce_evaluacion/{id_evaluacion}",
            payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# DELETE
# ============================

@router.delete("/{id_evaluacion}", status_code=204)
async def eliminar_evaluacion(id_evaluacion: int):
    """
    ORDS: DELETE /ce_evaluacion/{id}
    """
    try:
        await ords_request("DELETE", f"/ce_evaluacion/{id_evaluacion}")
        return
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


# ============================
# ENDPOINTS ADICIONALES ÚTILES
# ============================

@router.get("/empresa/{id_empresa}")
async def listar_evaluaciones_por_empresa(id_empresa: int):
    """
    Lista todas las evaluaciones de una empresa
    ORDS: GET /ce_evaluacion/?q={"id_empresa":123}
    """
    try:
        # ORDS permite filtros con el parámetro q
        import json
        filtro = json.dumps({"id_empresa": id_empresa})
        return await ords_request("GET", f"/ce_evaluacion/?q={filtro}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )


@router.patch("/{id_evaluacion}/progreso")
async def actualizar_progreso(id_evaluacion: int, porcentaje: float):
    """
    Actualiza solo el porcentaje de completado
    """
    try:
        payload = {"porcentaje_completado": porcentaje}
        return await ords_request(
            "PUT",
            f"/ce_evaluacion/{id_evaluacion}",
            payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")


@router.patch("/{id_evaluacion}/cerrar")
async def cerrar_evaluacion(id_evaluacion: int):
    """
    Cierra una evaluación (cambia estado y pone fecha de cierre)
    """
    try:
        from datetime import datetime
        payload = {
            "estado": "completada",
            "dt_cierre": datetime.now().isoformat(),
            "porcentaje_completado": 100.0
        }
        return await ords_request(
            "PUT",
            f"/ce_evaluacion/{id_evaluacion}",
            payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        raise HTTPException(
            status_code=502,
            detail=f"Error ORDS: {e.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="No fue posible conectar con ORDS")
