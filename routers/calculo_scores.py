# routers/calculo_scores.py
"""
Motor de cálculo de scores para MetaBridge
Implementa la fórmula: SCORE = Σ(RESPUESTA.VALOR × PESO) / Σ(PESO)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import logging

from core.ords_client import ords_request

logger = logging.getLogger("calculo-scores")

router = APIRouter(
    prefix="/api/calculo-scores",
    tags=["Cálculo de Scores"],
)

# ============================
# MODELOS
# ============================

class ScoreCalculadoResponse(BaseModel):
    id_evaluacion: int
    id_capacidad: int
    id_dimension: int
    score: float
    num_respuestas: int
    peso_total: float
    detalle: Dict


class CalculoCompletaResponse(BaseModel):
    id_evaluacion: int
    scores_calculados: int
    scores_detalle: List[ScoreCalculadoResponse]


# ============================
# LÓGICA DE CÁLCULO
# ============================

async def obtener_respuestas_evaluacion(id_evaluacion: int) -> List[dict]:
    """
    Obtiene todas las respuestas de una evaluación
    """
    try:
        data = await ords_request("GET", f"/ce_respuesta/?id_evaluacion={id_evaluacion}")
        items = data.get("items", [])
        return [item for item in items if item.get("links")]  # Limpiar
    except Exception as e:
        logger.error(f"Error obteniendo respuestas: {e}")
        raise


async def obtener_pregunta(id_pregunta: int) -> dict:
    """
    Obtiene información de una pregunta (capacidad, dimensión, versión)
    """
    try:
        return await ords_request("GET", f"/ce_pregunta/{id_pregunta}")
    except Exception as e:
        logger.error(f"Error obteniendo pregunta {id_pregunta}: {e}")
        raise


async def obtener_opcion(id_opcion: int) -> dict:
    """
    Obtiene el valor_base de una opción de respuesta
    """
    try:
        return await ords_request("GET", f"/ce_opcion_respuesta/{id_opcion}")
    except Exception as e:
        logger.error(f"Error obteniendo opción {id_opcion}: {e}")
        raise


async def obtener_ponderacion(id_version: int, id_pregunta: int) -> Optional[dict]:
    """
    Obtiene la ponderación de una pregunta en una versión específica
    """
    try:
        # ORDS AutoREST suele permitir filtros en query params
        data = await ords_request(
            "GET",
            f"/ce_ponderacion/?id_version={id_version}&id_pregunta={id_pregunta}"
        )
        items = data.get("items", [])
        return items[0] if items else None
    except Exception as e:
        logger.warning(f"Ponderación no encontrada para pregunta {id_pregunta}: {e}")
        return None


async def obtener_evaluacion(id_evaluacion: int) -> dict:
    """
    Obtiene información de la evaluación (incluyendo versión)
    """
    try:
        return await ords_request("GET", f"/ce_evaluacion/{id_evaluacion}")
    except Exception as e:
        logger.error(f"Error obteniendo evaluación {id_evaluacion}: {e}")
        raise


async def guardar_score(
    id_evaluacion: int,
    id_capacidad: int,
    id_dimension: int,
    score: float
) -> dict:
    """
    Guarda el score calculado en CE_SCORE_CAP_DIM
    """
    try:
        # Verificar si ya existe
        data = await ords_request(
            "GET",
            f"/ce_score_cap_dim/?id_evaluacion={id_evaluacion}&id_capacidad={id_capacidad}&id_dimension={id_dimension}"
        )
        
        items = data.get("items", [])
        
        payload = {
            "id_evaluacion": id_evaluacion,
            "id_capacidad": id_capacidad,
            "id_dimension": id_dimension,
            "score": round(score, 2)
        }
        
        if items:
            # UPDATE
            id_score = items[0].get("id_score")
            result = await ords_request("PUT", f"/ce_score_cap_dim/{id_score}", payload)
            logger.info(f"✅ Score actualizado: {id_score}")
        else:
            # INSERT
            result = await ords_request("POST", "/ce_score_cap_dim/", payload)
            logger.info(f"✅ Score creado")
        
        return result
        
    except Exception as e:
        logger.error(f"Error guardando score: {e}")
        raise


# ============================
# ENDPOINTS
# ============================

@router.post("/calcular/{id_evaluacion}/{id_capacidad}/{id_dimension}")
async def calcular_score_especifico(
    id_evaluacion: int,
    id_capacidad: int,
    id_dimension: int
) -> ScoreCalculadoResponse:
    """
    Calcula el score para una capacidad/dimensión específica
    
    Fórmula:
    SCORE = Σ(RESPUESTA.VALOR_BASE × PONDERACION.PESO) / Σ(PONDERACION.PESO)
    
    Proceso:
    1. Obtener todas las respuestas de la evaluación
    2. Filtrar por capacidad y dimensión
    3. Obtener valor_base de cada respuesta
    4. Obtener peso de cada pregunta
    5. Calcular score ponderado
    6. Guardar en CE_SCORE_CAP_DIM
    """
    try:
        logger.info(f"🧮 Calculando score: eval={id_evaluacion}, cap={id_capacidad}, dim={id_dimension}")
        
        # 1. Obtener evaluación (para saber la versión)
        evaluacion = await obtener_evaluacion(id_evaluacion)
        id_version = evaluacion.get("id_version")
        
        if not id_version:
            raise HTTPException(
                status_code=400,
                detail="La evaluación no tiene versión de metodología asociada"
            )
        
        # 2. Obtener todas las respuestas de esta evaluación
        respuestas = await obtener_respuestas_evaluacion(id_evaluacion)
        
        if not respuestas:
            raise HTTPException(
                status_code=400,
                detail=f"No hay respuestas para la evaluación {id_evaluacion}"
            )
        
        # 3. Filtrar respuestas por capacidad/dimensión
        numerador = 0.0
        denominador = 0.0
        respuestas_procesadas = []
        
        for respuesta in respuestas:
            id_pregunta = respuesta.get("id_pregunta")
            id_opcion = respuesta.get("id_opcion")
            
            # Obtener info de la pregunta
            pregunta = await obtener_pregunta(id_pregunta)
            
            # Verificar si pertenece a esta capacidad/dimensión
            if (pregunta.get("id_capacidad") == id_capacidad and 
                pregunta.get("id_dimension") == id_dimension):
                
                # Obtener valor de la opción seleccionada
                opcion = await obtener_opcion(id_opcion)
                valor_base = opcion.get("valor_base", 0)
                
                # Obtener ponderación
                ponderacion = await obtener_ponderacion(id_version, id_pregunta)
                
                if ponderacion:
                    peso = ponderacion.get("peso", 1.0)
                else:
                    # Si no hay ponderación definida, usar peso 1.0
                    peso = 1.0
                    logger.warning(
                        f"⚠️  No hay ponderación para pregunta {id_pregunta}, usando peso=1.0"
                    )
                
                # Acumular
                numerador += valor_base * peso
                denominador += peso
                
                respuestas_procesadas.append({
                    "id_pregunta": id_pregunta,
                    "codigo_pregunta": pregunta.get("codigo"),
                    "valor_base": valor_base,
                    "peso": peso,
                    "contribucion": valor_base * peso
                })
        
        # 4. Validar que haya respuestas
        if denominador == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No hay respuestas para capacidad {id_capacidad} / dimensión {id_dimension}"
            )
        
        # 5. Calcular score final
        score = numerador / denominador
        
        logger.info(f"📊 Score calculado: {score:.2f} (numerador={numerador:.2f}, denominador={denominador:.2f})")
        
        # 6. Guardar en base de datos
        await guardar_score(id_evaluacion, id_capacidad, id_dimension, score)
        
        # 7. Retornar respuesta
        return ScoreCalculadoResponse(
            id_evaluacion=id_evaluacion,
            id_capacidad=id_capacidad,
            id_dimension=id_dimension,
            score=round(score, 2),
            num_respuestas=len(respuestas_procesadas),
            peso_total=round(denominador, 2),
            detalle={
                "formula": "Σ(VALOR_BASE × PESO) / Σ(PESO)",
                "numerador": round(numerador, 2),
                "denominador": round(denominador, 2),
                "respuestas": respuestas_procesadas
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("💥 Error calculando score")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculando score: {str(e)}"
        )


@router.post("/calcular-todos/{id_evaluacion}")
async def calcular_todos_scores(id_evaluacion: int) -> CalculoCompletaResponse:
    """
    Calcula todos los scores para una evaluación (10 capacidades × 5 dimensiones = 50 scores)
    
    Este endpoint:
    1. Obtiene la evaluación y su versión
    2. Obtiene todas las capacidades activas
    3. Obtiene todas las dimensiones activas
    4. Calcula score para cada combinación capacidad/dimensión
    5. Guarda resultados en CE_SCORE_CAP_DIM
    """
    try:
        logger.info(f"🚀 Calculando TODOS los scores para evaluación {id_evaluacion}")
        
        # 1. Obtener capacidades activas
        cap_data = await ords_request("GET", "/ce_capacidad/?fl_activa=Y")
        capacidades = cap_data.get("items", [])
        
        # 2. Obtener dimensiones activas
        dim_data = await ords_request("GET", "/ce_dimension/?fl_activa=Y")
        dimensiones = dim_data.get("items", [])
        
        logger.info(f"📋 {len(capacidades)} capacidades × {len(dimensiones)} dimensiones")
        
        # 3. Calcular cada combinación
        scores_calculados = []
        errores = []
        
        for capacidad in capacidades:
            id_capacidad = capacidad.get("id_capacidad")
            codigo_cap = capacidad.get("codigo")
            
            for dimension in dimensiones:
                id_dimension = dimension.get("id_dimension")
                codigo_dim = dimension.get("codigo")
                
                try:
                    score_result = await calcular_score_especifico(
                        id_evaluacion,
                        id_capacidad,
                        id_dimension
                    )
                    scores_calculados.append(score_result)
                    logger.info(f"✅ {codigo_cap}-{codigo_dim}: {score_result.score:.2f}")
                    
                except HTTPException as e:
                    # Si no hay respuestas para esta combinación, es OK
                    if e.status_code == 400:
                        logger.warning(f"⚠️  {codigo_cap}-{codigo_dim}: {e.detail}")
                        errores.append({
                            "capacidad": codigo_cap,
                            "dimension": codigo_dim,
                            "error": e.detail
                        })
                    else:
                        raise
        
        logger.info(f"🎯 Cálculo completo: {len(scores_calculados)} scores calculados")
        
        if errores:
            logger.warning(f"⚠️  {len(errores)} combinaciones sin respuestas")
        
        return CalculoCompletaResponse(
            id_evaluacion=id_evaluacion,
            scores_calculados=len(scores_calculados),
            scores_detalle=scores_calculados
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("💥 Error calculando todos los scores")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculando scores: {str(e)}"
        )


@router.get("/resumen/{id_evaluacion}")
async def obtener_resumen_scores(id_evaluacion: int):
    """
    Obtiene resumen de scores calculados para una evaluación
    Agrupa por capacidad mostrando el promedio de las 5 dimensiones
    """
    try:
        # 1. Obtener todos los scores de la evaluación
        data = await ords_request("GET", f"/ce_score_cap_dim/?id_evaluacion={id_evaluacion}")
        scores = data.get("items", [])
        
        if not scores:
            return {
                "id_evaluacion": id_evaluacion,
                "total_scores": 0,
                "score_global": 0,
                "por_capacidad": []
            }
        
        # 2. Agrupar por capacidad
        por_capacidad = {}
        
        for score in scores:
            id_cap = score.get("id_capacidad")
            score_val = score.get("score", 0)
            
            if id_cap not in por_capacidad:
                por_capacidad[id_cap] = {
                    "scores": [],
                    "promedio": 0
                }
            
            por_capacidad[id_cap]["scores"].append(score_val)
        
        # 3. Calcular promedios por capacidad
        resumen_capacidades = []
        suma_global = 0
        
        for id_cap, info in por_capacidad.items():
            promedio = sum(info["scores"]) / len(info["scores"])
            suma_global += promedio
            
            resumen_capacidades.append({
                "id_capacidad": id_cap,
                "num_dimensiones": len(info["scores"]),
                "score_promedio": round(promedio, 2)
            })
        
        # 4. Score global (promedio de promedios de capacidades)
        score_global = suma_global / len(por_capacidad) if por_capacidad else 0
        
        return {
            "id_evaluacion": id_evaluacion,
            "total_scores": len(scores),
            "score_global": round(score_global, 2),
            "por_capacidad": sorted(resumen_capacidades, key=lambda x: x["id_capacidad"])
        }
        
    except Exception as e:
        logger.exception("Error obteniendo resumen de scores")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo resumen: {str(e)}"
        )


@router.delete("/limpiar/{id_evaluacion}")
async def limpiar_scores(id_evaluacion: int):
    """
    Elimina todos los scores calculados de una evaluación
    Útil para recalcular desde cero
    """
    try:
        logger.info(f"🧹 Limpiando scores de evaluación {id_evaluacion}")
        
        # 1. Obtener todos los scores
        data = await ords_request("GET", f"/ce_score_cap_dim/?id_evaluacion={id_evaluacion}")
        scores = data.get("items", [])
        
        # 2. Eliminar cada uno
        eliminados = 0
        for score in scores:
            id_score = score.get("id_score")
            try:
                await ords_request("DELETE", f"/ce_score_cap_dim/{id_score}")
                eliminados += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar score {id_score}: {e}")
        
        logger.info(f"✅ {eliminados} scores eliminados")
        
        return {
            "ok": True,
            "mensaje": f"Se eliminaron {eliminados} scores",
            "id_evaluacion": id_evaluacion,
            "scores_eliminados": eliminados
        }
        
    except Exception as e:
        logger.exception("Error limpiando scores")
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando scores: {str(e)}"
        )
