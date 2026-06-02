"""
Script de Estrés de CPU — Situación B del Taller 4
Agente de Rendimiento

Simula el ataque descrito en el taller:
  - Envío de un arreglo con 1,000,000 de registros (debe ser bloqueado en ≤1 ms)
  - Envío de arreglos en el límite permitido (15 elementos, debe pasar)
  - Medición del tiempo de respuesta con y sin caché

Uso:
    py -3.12 stress_cpu_test.py
"""

import json
import time
import urllib.request

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "ClaveSegura2026"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": TOKEN,
}


def _post(endpoint: str, payload: dict) -> tuple[int, dict, float]:
    """Realiza un POST y retorna (status_code, body_dict, elapsed_ms)."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers=HEADERS,
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = (time.perf_counter() - t0) * 1000
            return resp.status, json.loads(resp.read()), elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return e.code, {"detail": e.read().decode()}, elapsed


def separador(titulo: str) -> None:
    print(f"\n{'═' * 60}")
    print(f"  {titulo}")
    print("═" * 60)


def test_ataque_millon_registros() -> None:
    separador("PRUEBA 1 — Inyección de 1,000,000 registros (Situación B)")
    payload = {"id": "ATACANTE_CPU", "servicios_diarios": [1] * 1_000_000}
    print(f"  Tamaño del arreglo: {len(payload['servicios_diarios']):,} elementos")
    print("  Enviando petición... ", end="", flush=True)
    status, body, ms = _post("/liquidar-pago", payload)
    print(f"OK ({ms:.1f} ms)")
    print(f"  Status HTTP : {status}")
    print(f"  Detalle     : {body.get('detail', '')[:120]}")
    assert status == 400, f"FALLO: se esperaba 400, recibido {status}"
    print("  RESULTADO   : BLOQUEADO correctamente (HTTP 400) ✓")


def test_limite_exacto_15_dias() -> None:
    separador("PRUEBA 2 — Arreglo de exactamente 15 días (límite máximo)")
    payload = {"id": "OPERARIO_15", "servicios_diarios": [20.5] * 15}
    print(f"  Tamaño del arreglo: {len(payload['servicios_diarios'])} elementos")
    status, body, ms = _post("/liquidar-pago", payload)
    print(f"  Status HTTP : {status} ({ms:.1f} ms)")
    assert status == 200, f"FALLO: se esperaba 200, recibido {status}"
    print(f"  Pago neto   : ${body['pago_neto']:,.0f} COP")
    print("  RESULTADO   : ACEPTADO correctamente (HTTP 200) ✓")


def test_cache_latencia() -> None:
    separador("PRUEBA 3 — Comparación Pre-Caché vs Post-Caché")
    payload = {"id": "OPERARIO_CACHE_BENCH", "servicios_diarios": [50, 60, 40, 55]}
    tiempos = []
    print("  Ejecutando 10 consultas consecutivas del mismo operario...")
    for i in range(10):
        status, body, ms = _post("/liquidar-pago", payload)
        tiempos.append(ms)
        cache_flag = "CACHÉ" if body.get("desde_cache") else "CALC "
        print(f"    [{i + 1:02d}] {cache_flag} | {ms:7.2f} ms | HTTP {status}")

    pre_cache = tiempos[:4]
    post_cache = tiempos[4:]
    avg_pre = sum(pre_cache) / len(pre_cache)
    avg_post = sum(post_cache) / len(post_cache)
    reduccion = ((avg_pre - avg_post) / avg_pre) * 100 if avg_pre > 0 else 0

    print(f"\n  Latencia promedio Pre-Caché  (hits 1-4) : {avg_pre:.2f} ms")
    print(f"  Latencia promedio Post-Caché (hits 5-10): {avg_post:.2f} ms")
    print(f"  Reducción de latencia                   : {reduccion:.1f}%")


def test_waf_valores_invalidos() -> None:
    separador("PRUEBA 4 — WAF: Caso exacto del taller (Situación C)")
    payload = {"id": "Trabajador1", "servicios_diarios": [50000, 999999, -500]}
    status, body, ms = _post("/liquidar-pago", payload)
    print(f"  Payload enviado : {payload['servicios_diarios']}")
    print(f"  Status HTTP     : {status} ({ms:.1f} ms)")
    print(f"  Detalle         : {body.get('detail', '')[:120]}")
    assert status == 400, f"FALLO: se esperaba 400, recibido {status}"
    print("  RESULTADO       : WAF activo, pago fraudulento BLOQUEADO ✓")


if __name__ == "__main__":
    print("=" * 60)
    print("  SCRIPT DE ESTRÉS — Taller 4 Unidad 3")
    print("  Asegúrate de que la API esté corriendo en localhost:8000")
    print("=" * 60)

    try:
        test_ataque_millon_registros()
        test_limite_exacto_15_dias()
        test_cache_latencia()
        test_waf_valores_invalidos()
        print(f"\n{'═' * 60}")
        print("  TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("═" * 60)
    except AssertionError as e:
        print(f"\n  [FALLO] {e}")
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        print("  Verifica que el servidor esté corriendo: uvicorn main:app --reload")
