"""
Sistema de Liquidación de Pagos — API REST
Empresa de pintura de muebles | Universidad de Córdoba — Taller 4 Unidad 3
"""

import time
from collections import defaultdict

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

# ── Constantes de negocio ──────────────────────────────────────────────────────
PRECIO_BASE_M2 = 1_200  # COP por m²
BONO_NIVEL_1 = 20_000  # m² > 150
BONO_NIVEL_2 = 50_000  # m² > 250
UMBRAL_BONO_1 = 150
UMBRAL_BONO_2 = 250

# ── Restricciones arquitectónicas ─────────────────────────────────────────────
MAX_DIAS = 15  # Fase 2-B: protección de CPU
MAX_M2_DIA = 300  # Fase 3-C: límite físico por día
MIN_M2_DIA = 0  # Fase 3-C: no se admiten negativos
TOKEN_REQUERIDO = "ClaveSegura2026"  # Fase 3-D

# ── Caché en memoria ──────────────────────────────────────────────────────────
# Estructura: { id_operario: [ (timestamp_unix, resultado), ... ] }
_cache_hits: dict[str, list] = defaultdict(list)
_cache_resultados: dict[str, dict] = {}
VENTANA_CACHE_SEG = 60  # 1 minuto
MAX_HITS_ANTES_CACHE = 5  # 5 consultas → devuelve caché

app = FastAPI(
    title="API Liquidación de Pagos",
    description="Motor de liquidación semanal para operarios de pintura",
    version="1.0.0",
)


# ── Modelos ───────────────────────────────────────────────────────────────────
class SolicitudLiquidacion(BaseModel):
    id: str
    servicios_diarios: list[float]


class RespuestaLiquidacion(BaseModel):
    id: str
    metros_cuadrados_totales: float
    pago_base: float
    bono: float
    pago_neto: float
    desde_cache: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────
def _calcular_bono(metros_totales: float) -> float:
    if metros_totales > UMBRAL_BONO_2:
        return BONO_NIVEL_2
    if metros_totales > UMBRAL_BONO_1:
        return BONO_NIVEL_1
    return 0.0


def _registrar_y_verificar_cache(id_operario: str) -> dict | None:
    """
    Registra el hit actual y devuelve el resultado cacheado si el operario
    ha superado MAX_HITS_ANTES_CACHE consultas dentro de VENTANA_CACHE_SEG.
    Retorna None si se debe recalcular.
    """
    ahora = time.time()
    ventana_inicio = ahora - VENTANA_CACHE_SEG

    # Limpiar hits vencidos
    _cache_hits[id_operario] = [
        ts for ts in _cache_hits[id_operario] if ts >= ventana_inicio
    ]

    # Registrar hit actual
    _cache_hits[id_operario].append(ahora)

    # Si ya alcanzó el umbral Y hay un resultado guardado → devolver caché
    if (
        len(_cache_hits[id_operario]) >= MAX_HITS_ANTES_CACHE
        and id_operario in _cache_resultados
    ):
        return _cache_resultados[id_operario]

    return None


# ── Endpoint principal ────────────────────────────────────────────────────────
@app.post("/liquidar-pago", response_model=RespuestaLiquidacion)
def liquidar_pago(
    solicitud: SolicitudLiquidacion,
    authorization: str | None = Header(default=None),
) -> RespuestaLiquidacion:
    # ── Fase 3-D: Autenticación por token ────────────────────────────────────
    if authorization != TOKEN_REQUERIDO:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Token de acceso inválido o ausente.",
        )

    # ── Fase 2-B: Protección de CPU — límite de arreglo ──────────────────────
    if len(solicitud.servicios_diarios) > MAX_DIAS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Bad Request: El arreglo supera el máximo permitido de "
                f"{MAX_DIAS} días ({len(solicitud.servicios_diarios)} recibidos)."
            ),
        )

    # ── Fase 3-C: WAF simulado — validación de valores diarios ───────────────
    for i, m2 in enumerate(solicitud.servicios_diarios):
        if m2 < MIN_M2_DIA:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Bad Request: El valor del día {i + 1} es negativo "
                    f"({m2} m²). No se admiten valores negativos."
                ),
            )
        if m2 > MAX_M2_DIA:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Bad Request: El valor del día {i + 1} supera el límite "
                    f"físico de {MAX_M2_DIA} m²/día ({m2} m² recibidos)."
                ),
            )

    # ── Fase 2-A: Caché en memoria ────────────────────────────────────────────
    resultado_cacheado = _registrar_y_verificar_cache(solicitud.id)
    if resultado_cacheado is not None:
        return RespuestaLiquidacion(**resultado_cacheado, desde_cache=True)

    # ── Fase 1: Lógica de negocio ─────────────────────────────────────────────
    metros_totales = sum(solicitud.servicios_diarios)
    pago_base = metros_totales * PRECIO_BASE_M2
    bono = _calcular_bono(metros_totales)
    pago_neto = pago_base + bono

    resultado = {
        "id": solicitud.id,
        "metros_cuadrados_totales": metros_totales,
        "pago_base": pago_base,
        "bono": bono,
        "pago_neto": pago_neto,
    }

    # Guardar en caché para futuros hits
    _cache_resultados[solicitud.id] = resultado

    return RespuestaLiquidacion(**resultado, desde_cache=False)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
