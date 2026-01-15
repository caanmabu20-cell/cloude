# routers/motor_reglas.py
"""
Motor de Reglas Transversales para MetaBridge
Evalúa las 12 reglas del framework con lógica AND/OR y genera insights
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
import httpx
import logging
import json
from datetime import datetime

from core.ords_client import ords_request

logger = logging.getLogger("motor-reglas")

router = APIRouter(
    prefix="/api/motor-reglas",
    tags=["Motor de Reglas"],
)

# ============================
# MODELOS
# ============================

class ResultadoReglaResponse(BaseModel):
    id_regla: int
    codigo_regla: str
    nombre_regla: str
    fl_cumple: Literal["Y", "N"]
    num_condiciones: int
    condiciones_cumplidas: int
    detalle_json: Dict


class MotorResultadoResponse(BaseModel):
    id_evaluacion: int
    total_reglas: int
    reglas_cumplidas: int
    reglas_no_cumplidas: int
    resultados: List[ResultadoReglaResponse]


# ============================
# FUNCIONES DE EVALUACIÓN
# ============================

def evaluar_operador(valor: float, operador: str, valor1: float, valor2: Optional[float] = None) -> bool:
    """
    Evalúa si un valor cumple con un operador lógico
    
    Operadores soportados:
    - >= : mayor o igual
    - <= : menor o igual
    - >  : mayor estricto
    - <  : menor estricto
    - =  : igual (con tolerancia 0.01)
    - BETWEEN : entre valor1 y valor2 (inclusivo)
    """
    try:
        if operador == ">=":
            return valor >= valor1
        elif operador == "<=":
            return valor <= valor1
        elif operador == ">":
            return valor > valor1
        elif operador == "<":
            return valor < valor1
        elif operador == "=":
            return abs(valor - valor1) < 0.01  # Tolerancia para floats
        elif operador == "BETWEEN":
            if valor2 is None:
                raise ValueError("Operador BETWEEN requiere valor2")
            return valor1 <= valor <= valor2
        else:
            logger.warning(f"Operador desconocido: {operador}")
            return False
    except Exception as e:
        logger.error(f"Error evaluando operador {operador}: {e}")
        return False


async def obtener_scores_evaluacion(id_evaluacion: int) -> Dict:
    """
    Obtiene todos los scores de una evaluación
    Retorna dict con clave (id_capacidad, id_dimension) -> score
    """
    try:
        data = await ords_request("GET", f"/ce_score_cap_dim/?id_evaluacion={id_evaluacion}")
        scores = data.get("items", [])
        
        score_dict = {}
        for score in scores:
            id_cap = score.get("id_capacidad")
            id_dim = score.get("id_dimension")
            score_val = score.get("score", 0)
            
            score_dict[(id_cap, id_dim)] = score_val
        
        logger.info(f"📊 {len(score_dict)} scores cargados para evaluación {id_evaluacion}")
        return score_dict
        
    except Exception as e:
        logger.error(f"Error obteniendo scores: {e}")
        return {}


async def obtener_reglas_activas(id_version: int) -> List[dict]:
    """
    Obtiene todas las reglas activas de una versión
    """
    try:
        data = await ords_request(
            "GET",
            f"/ce_regla/?id_version={id_version}&fl_activa=Y"
        )
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Error obteniendo reglas: {e}")
        return []


async def obtener_condiciones_regla(id_regla: int) -> List[dict]:
    """
    Obtiene todas las condiciones de una regla ordenadas
    """
    try:
        data = await ords_request("GET", f"/ce_condicion_regla/?id_regla={id_regla}")
        condiciones = data.get("items", [])
        
        # Ordenar por ORDEN
        return sorted(condiciones, key=lambda x: x.get("orden", 0))
        
    except Exception as e:
        logger.error(f"Error obteniendo condiciones de regla {id_regla}: {e}")
        return []


def evaluar_condiciones(condiciones: List[dict], scores: Dict) -> tuple[bool, Dict]:
    """
    Evalúa las condiciones de una regla con lógica AND/OR/Grupos
    
    Lógica:
    - Las condiciones se agrupan por GRUPO
    - Dentro de cada grupo se evalúa con AND/OR según CONECTOR
    - Los resultados de grupos se combinan con OR
    
    Retorna:
    - bool: Si la regla se cumple
    - dict: Detalle de evaluación
    """
    if not condiciones:
        return False, {"error": "No hay condiciones"}
    
    # Agrupar condiciones por GRUPO
    grupos = {}
    for cond in condiciones:
        grupo_id = cond.get("grupo", 1)
        if grupo_id not in grupos:
            grupos[grupo_id] = []
        grupos[grupo_id].append(cond)
    
    logger.info(f"🔍 Evaluando {len(grupos)} grupo(s) con {len(condiciones)} condiciones totales")
    
    # Evaluar cada grupo
    resultados_grupos = []
    detalle_grupos = []
    
    for grupo_id, grupo_conds in grupos.items():
        logger.info(f"  📦 Grupo {grupo_id}: {len(grupo_conds)} condiciones")
        
        # Evaluar condiciones del grupo
        resultado_grupo = None
        detalle_condiciones = []
        
        for i, cond in enumerate(grupo_conds):
            id_cap = cond.get("id_capacidad")
            id_dim = cond.get("id_dimension")
            operador = cond.get("operador")
            valor1 = cond.get("valor1")
            valor2 = cond.get("valor2")
            conector = cond.get("conector", "AND")
            metrica = cond.get("metrica", "SCORE_CAP_DIM")
            
            # Obtener valor actual del score
            score_actual = scores.get((id_cap, id_dim), 0)
            
            # Evaluar condición
            cumple = evaluar_operador(score_actual, operador, valor1, valor2)
            
            detalle_condiciones.append({
                "orden": cond.get("orden"),
                "capacidad": id_cap,
                "dimension": id_dim,
                "metrica": metrica,
                "operador": operador,
                "valor_esperado": valor1,
                "valor_actual": score_actual,
                "cumple": cumple,
                "conector": conector if i > 0 else None
            })
            
            # Aplicar lógica AND/OR
            if i == 0:
                resultado_grupo = cumple
            else:
                if conector == "AND":
                    resultado_grupo = resultado_grupo and cumple
                elif conector == "OR":
                    resultado_grupo = resultado_grupo or cumple
            
            logger.info(
                f"    {'✅' if cumple else '❌'} Cond {i+1}: "
                f"Score({id_cap},{id_dim})={score_actual:.2f} {operador} {valor1} "
                f"→ {cumple}"
            )
        
        resultados_grupos.append(resultado_grupo)
        detalle_grupos.append({
            "grupo_id": grupo_id,
            "cumple": resultado_grupo,
            "condiciones": detalle_condiciones
        })
        
        logger.info(f"  📦 Grupo {grupo_id} resultado: {'✅' if resultado_grupo else '❌'}")
    
    # Combinar grupos con OR (si cualquier grupo cumple, la regla cumple)
    resultado_final = any(resultados_grupos)
    
    logger.info(f"🎯 Resultado final: {'✅ CUMPLE' if resultado_final else '❌ NO CUMPLE'}")
    
    return resultado_final, {
        "num_grupos": len(grupos),
        "grupos_cumplidos": sum(1 for r in resultados_grupos if r),
        "logica_global": "OR entre grupos",
        "detalle_grupos": detalle_grupos
    }


async def guardar_resultado_regla(
    id_evaluacion: int,
    id_regla: int,
    fl_cumple: str,
    valor_numerico: Optional[float],
    detalle_json: Dict
) -> dict:
    """
    Guarda el resultado de evaluación de una regla
    """
    try:
        # Verificar si ya existe
        data = await ords_request(
            "GET",
            f"/ce_resultado_regla/?id_evaluacion={id_evaluacion}&id_regla={id_regla}"
        )
        
        items = data.get("items", [])
        
        payload = {
            "id_evaluacion": id_evaluacion,
            "id_regla": id_regla,
            "fl_cumple": fl_cumple,
            "valor_numerico": valor_numerico,
            "detalle_json": json.dumps(detalle_json)
        }
        
        if items:
            # UPDATE
            id_resultado = items[0].get("id_resultado_regla")
            result = await ords_request("PUT", f"/ce_resultado_regla/{id_resultado}", payload)
            logger.info(f"✅ Resultado actualizado: {id_resultado}")
        else:
            # INSERT
            result = await ords_request("POST", "/ce_resultado_regla/", payload)
            logger.info(f"✅ Resultado creado")
        
        return result
        
    except Exception as e:
        logger.error(f"Error guardando resultado de regla: {e}")
        raise


# ============================
# ENDPOINTS
# ============================

@router.post("/ejecutar/{id_evaluacion}")
async def ejecutar_motor_reglas(id_evaluacion: int) -> MotorResultadoResponse:
    """
    Ejecuta el motor de reglas completo para una evaluación
    
    Proceso:
    1. Obtiene la versión de metodología de la evaluación
    2. Carga todas las reglas activas de esa versión
    3. Carga todos los scores de la evaluación
    4. Para cada regla:
       a. Carga sus condiciones
       b. Evalúa con lógica AND/OR/Grupos
       c. Genera detalle JSON
       d. Guarda resultado en CE_RESULTADO_REGLA
    5. Retorna resumen de ejecución
    """
    try:
        logger.info(f"🚀 Ejecutando motor de reglas para evaluación {id_evaluacion}")
        
        # 1. Obtener evaluación
        evaluacion = await ords_request("GET", f"/ce_evaluacion/{id_evaluacion}")
        id_version = evaluacion.get("id_version")
        
        if not id_version:
            raise HTTPException(
                status_code=400,
                detail="La evaluación no tiene versión de metodología"
            )
        
        logger.info(f"📋 Versión metodología: {id_version}")
        
        # 2. Cargar scores
        scores = await obtener_scores_evaluacion(id_evaluacion)
        
        if not scores:
            raise HTTPException(
                status_code=400,
                detail="No hay scores calculados para esta evaluación. Ejecuta primero el cálculo de scores."
            )
        
        # 3. Cargar reglas activas
        reglas = await obtener_reglas_activas(id_version)
        
        if not reglas:
            logger.warning("⚠️  No hay reglas activas para esta versión")
            return MotorResultadoResponse(
                id_evaluacion=id_evaluacion,
                total_reglas=0,
                reglas_cumplidas=0,
                reglas_no_cumplidas=0,
                resultados=[]
            )
        
        logger.info(f"📝 {len(reglas)} reglas activas encontradas")
        
        # 4. Evaluar cada regla
        resultados = []
        reglas_cumplidas = 0
        
        for regla in reglas:
            id_regla = regla.get("id_regla")
            codigo = regla.get("codigo")
            nombre = regla.get("nombre")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Evaluando regla {codigo}: {nombre}")
            logger.info(f"{'='*60}")
            
            # Obtener condiciones
            condiciones = await obtener_condiciones_regla(id_regla)
            
            if not condiciones:
                logger.warning(f"⚠️  Regla {codigo} no tiene condiciones")
                continue
            
            # Evaluar condiciones
            cumple, detalle = evaluar_condiciones(condiciones, scores)
            
            # Guardar resultado
            fl_cumple = "Y" if cumple else "N"
            
            await guardar_resultado_regla(
                id_evaluacion=id_evaluacion,
                id_regla=id_regla,
                fl_cumple=fl_cumple,
                valor_numerico=None,
                detalle_json=detalle
            )
            
            if cumple:
                reglas_cumplidas += 1
            
            resultados.append(ResultadoReglaResponse(
                id_regla=id_regla,
                codigo_regla=codigo,
                nombre_regla=nombre,
                fl_cumple=fl_cumple,
                num_condiciones=len(condiciones),
                condiciones_cumplidas=detalle.get("grupos_cumplidos", 0),
                detalle_json=detalle
            ))
            
            logger.info(f"{'✅ CUMPLE' if cumple else '❌ NO CUMPLE'}: {codigo} - {nombre}\n")
        
        # 5. Resumen final
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 RESUMEN FINAL")
        logger.info(f"{'='*60}")
        logger.info(f"Total reglas evaluadas: {len(resultados)}")
        logger.info(f"Reglas cumplidas: {reglas_cumplidas}")
        logger.info(f"Reglas no cumplidas: {len(resultados) - reglas_cumplidas}")
        logger.info(f"{'='*60}\n")
        
        return MotorResultadoResponse(
            id_evaluacion=id_evaluacion,
            total_reglas=len(resultados),
            reglas_cumplidas=reglas_cumplidas,
            reglas_no_cumplidas=len(resultados) - reglas_cumplidas,
            resultados=resultados
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("💥 Error ejecutando motor de reglas")
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando motor de reglas: {str(e)}"
        )


@router.get("/resultados/{id_evaluacion}")
async def obtener_resultados_reglas(id_evaluacion: int):
    """
    Obtiene los resultados de reglas ya ejecutadas para una evaluación
    """
    try:
        data = await ords_request("GET", f"/ce_resultado_regla/?id_evaluacion={id_evaluacion}")
        resultados = data.get("items", [])
        
        # Enriquecer con información de las reglas
        resultados_enriquecidos = []
        
        for resultado in resultados:
            id_regla = resultado.get("id_regla")
            
            # Obtener info de la regla
            regla = await ords_request("GET", f"/ce_regla/{id_regla}")
            
            resultados_enriquecidos.append({
                "id_resultado": resultado.get("id_resultado_regla"),
                "codigo_regla": regla.get("codigo"),
                "nombre_regla": regla.get("nombre"),
                "descripcion_regla": regla.get("descripcion"),
                "fl_cumple": resultado.get("fl_cumple"),
                "detalle_json": json.loads(resultado.get("detalle_json", "{}")),
                "dt_calculo": resultado.get("dt_calculo")
            })
        
        return {
            "id_evaluacion": id_evaluacion,
            "total_resultados": len(resultados_enriquecidos),
            "reglas_cumplidas": sum(1 for r in resultados_enriquecidos if r["fl_cumple"] == "Y"),
            "resultados": resultados_enriquecidos
        }
        
    except Exception as e:
        logger.exception("Error obteniendo resultados de reglas")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo resultados: {str(e)}"
        )


@router.get("/insights/{id_evaluacion}")
async def obtener_insights_ejecutivos(id_evaluacion: int):
    """
    Genera los insights ejecutivos (lecturas de las reglas que se cumplen)
    """
    try:
        # Obtener resultados de reglas
        data = await ords_request("GET", f"/ce_resultado_regla/?id_evaluacion={id_evaluacion}&fl_cumple=Y")
        resultados_cumplidos = data.get("items", [])
        
        insights = []
        
        for resultado in resultados_cumplidos:
            id_regla = resultado.get("id_regla")
            
            # Obtener regla completa
            regla = await ords_request("GET", f"/ce_regla/{id_regla}")
            
            insights.append({
                "codigo": regla.get("codigo"),
                "nombre": regla.get("nombre"),
                "descripcion": regla.get("descripcion"),
                "tipo": regla.get("tipo_regla"),
                "detalle": json.loads(resultado.get("detalle_json", "{}"))
            })
        
        return {
            "id_evaluacion": id_evaluacion,
            "num_insights": len(insights),
            "insights": insights
        }
        
    except Exception as e:
        logger.exception("Error generando insights")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando insights: {str(e)}"
        )


@router.delete("/limpiar/{id_evaluacion}")
async def limpiar_resultados_reglas(id_evaluacion: int):
    """
    Elimina todos los resultados de reglas de una evaluación
    Útil para re-ejecutar el motor desde cero
    """
    try:
        logger.info(f"🧹 Limpiando resultados de reglas de evaluación {id_evaluacion}")
        
        # Obtener todos los resultados
        data = await ords_request("GET", f"/ce_resultado_regla/?id_evaluacion={id_evaluacion}")
        resultados = data.get("items", [])
        
        # Eliminar cada uno
        eliminados = 0
        for resultado in resultados:
            id_resultado = resultado.get("id_resultado_regla")
            try:
                await ords_request("DELETE", f"/ce_resultado_regla/{id_resultado}")
                eliminados += 1
            except Exception as e:
                logger.warning(f"No se pudo eliminar resultado {id_resultado}: {e}")
        
        logger.info(f"✅ {eliminados} resultados eliminados")
        
        return {
            "ok": True,
            "mensaje": f"Se eliminaron {eliminados} resultados de reglas",
            "id_evaluacion": id_evaluacion,
            "resultados_eliminados": eliminados
        }
        
    except Exception as e:
        logger.exception("Error limpiando resultados")
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando resultados: {str(e)}"
        )
