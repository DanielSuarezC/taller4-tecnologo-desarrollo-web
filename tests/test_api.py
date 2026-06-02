"""
Suite de pruebas automatizadas — Taller 4 Unidad 3
Agente Tester: cubre todos los escenarios de negocio y seguridad.
"""

import pytest
from fastapi.testclient import TestClient

from main import MAX_DIAS, TOKEN_REQUERIDO, _cache_hits, _cache_resultados, app

TOKEN = TOKEN_REQUERIDO
HEADERS_VALIDOS = {"Authorization": TOKEN}


@pytest.fixture(autouse=True)
def limpiar_cache():
    """Reinicia el estado del caché antes de cada test para evitar contaminación."""
    _cache_hits.clear()
    _cache_resultados.clear()
    yield
    _cache_hits.clear()
    _cache_resultados.clear()


@pytest.fixture()
def client():
    return TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# FASE 1 — Flujo feliz y lógica de negocio
# ══════════════════════════════════════════════════════════════════════════════


class TestFaseUno:
    def test_flujo_feliz_sin_bono(self, client):
        """Operario con ≤150 m² no recibe bono."""
        payload = {"id": "OP001", "servicios_diarios": [20, 30, 25, 10]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "OP001"
        assert data["metros_cuadrados_totales"] == 85.0
        assert data["pago_base"] == 85 * 1_200
        assert data["bono"] == 0.0
        assert data["pago_neto"] == 85 * 1_200
        assert data["desde_cache"] is False

    def test_flujo_feliz_bono_nivel_1(self, client):
        """Operario con >150 m² recibe bono de $20,000."""
        payload = {"id": "OP002", "servicios_diarios": [30, 30, 30, 30, 40]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200
        data = r.json()
        assert data["metros_cuadrados_totales"] == 160.0
        assert data["bono"] == 20_000.0
        assert data["pago_neto"] == 160 * 1_200 + 20_000

    def test_flujo_feliz_bono_nivel_2(self, client):
        """Operario con >250 m² recibe bono de $50,000 (no acumulativo)."""
        payload = {"id": "OP003", "servicios_diarios": [60, 60, 60, 60, 60]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200
        data = r.json()
        assert data["metros_cuadrados_totales"] == 300.0
        assert data["bono"] == 50_000.0
        assert data["pago_neto"] == 300 * 1_200 + 50_000

    def test_respuesta_contiene_todos_los_campos(self, client):
        """La respuesta debe incluir todos los campos requeridos por el taller."""
        payload = {"id": "OP004", "servicios_diarios": [50]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        data = r.json()
        campos_requeridos = {
            "id",
            "metros_cuadrados_totales",
            "pago_base",
            "bono",
            "pago_neto",
        }
        assert campos_requeridos.issubset(data.keys())

    def test_exactamente_150m2_no_recibe_bono(self, client):
        """El umbral es estricto: 150 m² exactos no activan bono."""
        payload = {"id": "OP005", "servicios_diarios": [50, 50, 50]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200
        assert r.json()["bono"] == 0.0

    def test_exactamente_250m2_recibe_bono_nivel_1(self, client):
        """250 m² exactos activan bono nivel 1 ($20k), no el nivel 2."""
        payload = {"id": "OP006", "servicios_diarios": [50, 50, 50, 50, 50]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200
        assert r.json()["bono"] == 20_000.0


# ══════════════════════════════════════════════════════════════════════════════
# FASE 2 — Rendimiento: caché y protección de CPU
# ══════════════════════════════════════════════════════════════════════════════


class TestFaseDos:
    def test_cache_se_activa_en_quinta_consulta(self, client):
        """Las primeras 4 consultas recalculan; la 5ª retorna desde caché."""
        payload = {"id": "OP-CACHE", "servicios_diarios": [100, 80]}
        for i in range(4):
            r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
            assert r.json()["desde_cache"] is False, f"Hit {i + 1} debería NO ser caché"
        r5 = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r5.json()["desde_cache"] is True

    def test_cache_devuelve_datos_correctos(self, client):
        """El resultado retornado desde caché debe ser idéntico al calculado."""
        payload = {"id": "OP-CACHE2", "servicios_diarios": [200, 60]}
        resultados = []
        for _ in range(5):
            r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
            resultados.append(r.json())
        for campo in ("metros_cuadrados_totales", "pago_base", "bono", "pago_neto"):
            assert resultados[0][campo] == resultados[4][campo]

    def test_limite_max_dias_retorna_400(self, client):
        """Arreglo con más de MAX_DIAS elementos → HTTP 400."""
        payload = {"id": "OP-CPU", "servicios_diarios": [10] * (MAX_DIAS + 1)}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 400

    def test_exactamente_max_dias_es_valido(self, client):
        """Arreglo con exactamente MAX_DIAS elementos debe ser aceptado."""
        payload = {"id": "OP-CPU2", "servicios_diarios": [10] * MAX_DIAS}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200

    def test_inyeccion_millon_registros_bloqueada(self, client):
        """Simular ataque con 1,000,000 de registros → debe ser rechazado (400)."""
        payload = {"id": "ATACANTE", "servicios_diarios": [1] * 1_000_000}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# FASE 3-C — Seguridad: WAF simulado (fraude lógico)
# ══════════════════════════════════════════════════════════════════════════════


class TestFaseTresWAF:
    def test_valor_negativo_retorna_400(self, client):
        """Valores negativos en servicios_diarios → HTTP 400."""
        payload = {"id": "OP-WAF1", "servicios_diarios": [50, -10, 30]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 400

    def test_valor_mayor_300_retorna_400(self, client):
        """Valor diario >300 m² → HTTP 400 (límite físico)."""
        payload = {"id": "OP-WAF2", "servicios_diarios": [50, 301, 30]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 400

    def test_ataque_del_taller_retorna_400(self, client):
        """Caso exacto del taller: [50000, 999999, -500] → HTTP 400."""
        payload = {"id": "Trabajador1", "servicios_diarios": [50000, 999999, -500]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 400

    def test_exactamente_300m2_es_valido(self, client):
        """300 m²/día es el límite físico máximo — debe ser aceptado."""
        payload = {"id": "OP-WAF3", "servicios_diarios": [300]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200

    def test_cero_m2_es_valido(self, client):
        """0 m²/día (día sin trabajo) es válido."""
        payload = {"id": "OP-WAF4", "servicios_diarios": [0, 0, 100]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# FASE 3-D — Seguridad: autenticación por token
# ══════════════════════════════════════════════════════════════════════════════


class TestFaseTresAuth:
    def test_sin_token_retorna_401(self, client):
        """Petición sin cabecera Authorization → HTTP 401."""
        payload = {"id": "OP-AUTH1", "servicios_diarios": [50]}
        r = client.post("/liquidar-pago", json=payload)
        assert r.status_code == 401

    def test_token_incorrecto_retorna_401(self, client):
        """Token equivocado → HTTP 401."""
        payload = {"id": "OP-AUTH2", "servicios_diarios": [50]}
        r = client.post(
            "/liquidar-pago",
            json=payload,
            headers={"Authorization": "TokenFalso123"},
        )
        assert r.status_code == 401

    def test_token_correcto_retorna_200(self, client):
        """Token exacto 'ClaveSegura2026' → HTTP 200."""
        payload = {"id": "OP-AUTH3", "servicios_diarios": [50]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 200

    def test_token_vacio_retorna_401(self, client):
        """Cabecera Authorization vacía → HTTP 401."""
        payload = {"id": "OP-AUTH4", "servicios_diarios": [50]}
        r = client.post("/liquidar-pago", json=payload, headers={"Authorization": ""})
        assert r.status_code == 401

    def test_validaciones_waf_no_bypass_por_token(self, client):
        """El WAF actúa DESPUÉS del token: token válido + datos inválidos → 400."""
        payload = {"id": "OP-AUTH5", "servicios_diarios": [-1]}
        r = client.post("/liquidar-pago", json=payload, headers=HEADERS_VALIDOS)
        assert r.status_code == 400
