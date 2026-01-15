from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chequeo Ejecutivo API",
    description="Backend FastAPI para Chequeo Ejecutivo",
    version="1.0.0",

    # 🔑 CLAVE para reverse proxy /api
    root_path="/api",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS (ajustaremos luego en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from routers.capacidades import router as capacidades_router
from routers.condiciones_regla import router as condiciones_regla_router
from routers.contextos_semanticos import router as contextos_semanticos_router
from routers.dimensiones import router as dimensiones_router
from routers.empresas import router as empresas_router
from routers.evaluaciones import router as evaluaciones_router
from routers.evaluacion_progreso import router as evaluacion_progreso_router
from routers.reglas import router as reglas_router
from routers.invitaciones_evaluacion import router as invitaciones_evaluacion_router
from routers.normalizaciones_semanticas import router as normalizaciones_semanticas_router
from routers.opciones_respuesta import router as opciones_respuesta_router
from routers.ponderaciones import router as ponderaciones_router
from routers.preguntas import router as preguntas_router
from routers.respuestas import router as respuestas_router
from routers.resultados_capacidad import router as resultados_capacidad_router
from routers.resultados_evaluacion import router as resultados_evaluacion_router
from routers.resultados_regla import router as resultados_regla_router
from routers.roles_empresa import router as roles_empresa_router
from routers.roles_global import router as roles_global_router
from routers.score_cap_dim import router as score_cap_dim_router
from routers.usuarios import router as usuarios_router
from routers.usuario_empresa import router as usuario_empresa_router
from routers.version_metodologia import router as version_metodologia_router
from routers.motor_reglas import router as motor_reglas_router
from routers.calculo_scores import router as calculo_scores_router


app.include_router(calculo_scores_router)
app.include_router(motor_reglas_router)
app.include_router(version_metodologia_router)
app.include_router(usuario_empresa_router)
app.include_router(usuarios_router)
app.include_router(score_cap_dim_router)
app.include_router(roles_global_router)
app.include_router(roles_empresa_router)
app.include_router(resultados_regla_router)
app.include_router(resultados_evaluacion_router)
app.include_router(resultados_capacidad_router)
app.include_router(respuestas_router)
app.include_router(preguntas_router)
app.include_router(ponderaciones_router)
app.include_router(opciones_respuesta_router)
app.include_router(normalizaciones_semanticas_router)
app.include_router(invitaciones_evaluacion_router)
app.include_router(reglas_router)
app.include_router(evaluacion_progreso_router)
app.include_router(evaluaciones_router)
app.include_router(empresas_router)
app.include_router(dimensiones_router)
app.include_router(contextos_semanticos_router)
app.include_router(condiciones_regla_router)
app.include_router(capacidades_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

