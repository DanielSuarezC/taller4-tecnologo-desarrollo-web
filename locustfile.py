"""
Locust — Prueba de Carga y Estrés
Taller 4 Unidad 3 | Agente de Rendimiento

Escenario: 2000 usuarios concurrentes, spawn rate 100/s.

Ejecutar (sin caché — medir colapso):
    locust -f locustfile.py --users 2000 --spawn-rate 100 --host http://127.0.0.1:8000

Ejecutar (con caché activo — comparar latencia):
    locust -f locustfile.py --users 2000 --spawn-rate 100 --host http://127.0.0.1:8000 \
           --headless --run-time 60s --html reporte_post_cache.html
"""

import random

from locust import HttpUser, between, task

TOKEN = "ClaveSegura2026"
HEADERS = {"Authorization": TOKEN}

# Pool de IDs que se reutilizarán para activar el caché intra-prueba
POOL_IDS = [f"Operario_{i:04d}" for i in range(200)]


class OperarioPinturaUser(HttpUser):
    """
    Simula a un operario que consulta su liquidación.
    wait_time entre 0.5 y 2 segundos imita patrones de uso real.
    """

    wait_time = between(0.5, 2)

    @task(8)
    def consultar_liquidacion_normal(self):
        """Caso principal: operario con datos normales de la semana."""
        operario_id = random.choice(POOL_IDS)
        dias = random.randint(1, 6)
        servicios = [round(random.uniform(10, 50), 1) for _ in range(dias)]
        payload = {"id": operario_id, "servicios_diarios": servicios}
        with self.client.post(
            "/liquidar-pago",
            json=payload,
            headers=HEADERS,
            catch_response=True,
            name="/liquidar-pago [normal]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:120]}")

    @task(2)
    def consultar_liquidacion_alta_produccion(self):
        """Operario de alto rendimiento (activa bono nivel 2 con frecuencia)."""
        operario_id = random.choice(POOL_IDS)
        servicios = [round(random.uniform(40, 60), 1) for _ in range(6)]
        payload = {"id": operario_id, "servicios_diarios": servicios}
        with self.client.post(
            "/liquidar-pago",
            json=payload,
            headers=HEADERS,
            catch_response=True,
            name="/liquidar-pago [alto rendimiento]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:120]}")

    @task(1)
    def health_check(self):
        """Sondeo de disponibilidad del servidor."""
        self.client.get("/health", name="/health")


class BotAtacanteUser(HttpUser):
    """
    Simula ataques de bots (5% de la carga total).
    Intenta inyectar datos inválidos. La API debe responder con 400/401.
    """

    wait_time = between(0.1, 0.5)
    weight = 1

    @task(3)
    def ataque_datos_invalidos(self):
        """Envía valores negativos o excesivos para probar el WAF."""
        payload = {
            "id": "BOT_ATACANTE",
            "servicios_diarios": [random.choice([-500, 99999, 301])],
        }
        with self.client.post(
            "/liquidar-pago",
            json=payload,
            headers=HEADERS,
            catch_response=True,
            name="/liquidar-pago [ataque WAF]",
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(
                    f"WAF falló: esperado 400, recibido {response.status_code}"
                )

    @task(2)
    def ataque_sin_token(self):
        """Intento de acceso sin cabecera Authorization."""
        payload = {"id": "BOT_SIN_TOKEN", "servicios_diarios": [50]}
        with self.client.post(
            "/liquidar-pago",
            json=payload,
            catch_response=True,
            name="/liquidar-pago [sin token]",
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(
                    f"Auth falló: esperado 401, recibido {response.status_code}"
                )

    @task(1)
    def ataque_inyeccion_masiva(self):
        """Simula inyección de arreglo sobredimensionado (truncado por cliente)."""
        payload = {"id": "BOT_CPU", "servicios_diarios": [1] * 500}
        with self.client.post(
            "/liquidar-pago",
            json=payload,
            headers=HEADERS,
            catch_response=True,
            name="/liquidar-pago [inyección masiva]",
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(
                    f"Límite CPU falló: esperado 400, recibido {response.status_code}"
                )
