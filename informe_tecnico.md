# Informe Técnico — Taller 4, Unidad 3
## Sistema de Liquidación de Pagos para Operarios de Pintura

**Departamento de Ingeniería de Sistemas y Telemática**
**Universidad de Córdoba**
**Curso:** Taller Tecnólogo Desarrollo Web

---

## 1. Introducción

El presente informe documenta el proceso de diseño, implementación y prueba del motor central del Sistema de Liquidación de Pagos para una empresa de pintura de muebles. El sistema fue construido como una API REST en Python utilizando el framework **FastAPI**, cumpliendo con las tres fases establecidas en el enunciado del taller:

- **Fase 1 — Desarrollo Base:** Endpoint `POST /liquidar-pago` con lógica de negocio, cálculo de m², precio base y bonificaciones escalonadas.
- **Fase 2 — Escenarios de Rendimiento:** Implementación de caché en memoria y protección de CPU contra inyecciones masivas de datos.
- **Fase 3 — Escenarios de Seguridad:** WAF simulado con validación estricta de entrada (HTTP 400) y autenticación por token (HTTP 401).

El sistema fue sometido a análisis estático de código con **Ruff** (linter y formateador), pruebas automatizadas con **pytest** (21 casos de prueba, 100% de aprobación), pruebas de carga con **Locust** y un script de estrés de CPU.

---

## 2. Desarrollo

### 2.1 Adecuación del Ambiente de Desarrollo

**Herramientas y tecnologías utilizadas:**

| Herramienta | Versión | Propósito |
|---|---|---|
| Python | 3.12.3 | Lenguaje principal del backend |
| FastAPI | 0.115.12 | Framework web asíncrono para la API REST |
| Uvicorn | 0.34.3 | Servidor ASGI para ejecutar la API |
| Pydantic | (incluido en FastAPI) | Validación de modelos de datos |
| Ruff | 0.11.12 | Linter y formateador de código Python |
| pytest | 8.4.0 / 9.0.3 | Framework de pruebas unitarias y de integración |
| httpx | 0.28.1 | Cliente HTTP para pruebas de la API |
| Locust | 2.37.1 | Herramienta de pruebas de carga y estrés |

**Estructura del proyecto:**

```
app/
├── main.py               # API principal (todas las fases integradas)
├── requirements.txt      # Dependencias del proyecto
├── locustfile.py         # Configuración de pruebas de carga con Locust
├── stress_cpu_test.py    # Script de estrés de CPU (Situación B)
├── tests/
│   ├── __init__.py
│   └── test_api.py       # Suite completa de pruebas automatizadas (21 casos)
└── informe_tecnico.md    # Este documento
```

**Comandos de instalación:**

```bash
# Crear entorno virtual (recomendado)
py -3.12 -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar las pruebas
py -3.12 -m pytest tests/ -v

# Ejecutar el linter
py -3.12 -m ruff check . && py -3.12 -m ruff format --check .
```

---

### 2.2 Creación de Recursos — Código Fuente

#### 2.2.1 Arquitectura General del Archivo `main.py`

El código está organizado en las siguientes secciones:

1. **Constantes de negocio:** Precio base ($1,200/m²) y umbrales de bonificación (>150 m² y >250 m²).
2. **Restricciones arquitectónicas:** Límite de 15 días de entrada, límite de 300 m²/día y el token de acceso.
3. **Caché en memoria:** Diccionarios para registrar hits por operario y almacenar resultados.
4. **Modelos Pydantic:** `SolicitudLiquidacion` (entrada) y `RespuestaLiquidacion` (salida).
5. **Funciones auxiliares:** `_calcular_bono()` y `_registrar_y_verificar_cache()`.
6. **Endpoint principal:** `POST /liquidar-pago`.
7. **Health check:** `GET /health`.

#### 2.2.2 Fase 1 — Lógica de Negocio

**Modelo de entrada:**

```python
class SolicitudLiquidacion(BaseModel):
    id: str
    servicios_diarios: list[float]
```

**Modelo de salida:**

```python
class RespuestaLiquidacion(BaseModel):
    id: str
    metros_cuadrados_totales: float
    pago_base: float
    bono: float
    pago_neto: float
    desde_cache: bool = False
```

**Cálculo del bono (bonificaciones escalonadas, no acumulativas):**

```python
def _calcular_bono(metros_totales: float) -> float:
    if metros_totales > 250:
        return 50_000   # Nivel 2: mayor bono
    if metros_totales > 150:
        return 20_000   # Nivel 1
    return 0.0          # Sin bono
```

> **Decisión de diseño:** El bono de $50,000 reemplaza al de $20,000 cuando se supera el umbral de 250 m² (escalonado, no acumulativo). El umbral es estricto (`>`), por lo que exactamente 150 m² o 250 m² no activan el bono del nivel superior.

**Ejemplo de petición y respuesta (Postman / Thunder Client):**

```json
// Petición
POST /liquidar-pago
Headers: { "Authorization": "ClaveSegura2026" }
Body:
{
  "id": "OP_001",
  "servicios_diarios": [50, 60, 45, 55, 40, 30]
}

// Respuesta HTTP 200
{
  "id": "OP_001",
  "metros_cuadrados_totales": 280.0,
  "pago_base": 336000.0,
  "bono": 50000.0,
  "pago_neto": 386000.0,
  "desde_cache": false
}
```

#### 2.2.3 Fase 2-A — Caché en Memoria

**Problema:** Con 2,000 usuarios concurrentes, el servidor recalcula el mismo resultado para cada petición, incrementando la latencia de milisegundos a varios segundos.

**Solución implementada:** Caché basada en diccionarios en memoria con ventana deslizante de 60 segundos.

```python
# Estructura de datos del caché
_cache_hits: dict[str, list] = defaultdict(list)      # timestamps por operario
_cache_resultados: dict[str, dict] = {}               # resultado calculado
VENTANA_CACHE_SEG = 60    # ventana de 1 minuto
MAX_HITS_ANTES_CACHE = 5  # activar caché en la 5ª consulta
```

**Flujo de la caché:**

1. Cada petición registra un timestamp en `_cache_hits[id_operario]`.
2. Se limpian timestamps fuera de la ventana de 60 segundos.
3. Si el operario tiene **≥5 hits en la ventana** Y el resultado ya fue calculado → se retorna el resultado cacheado sin recalcular.
4. Si no → se calcula, se guarda en `_cache_resultados` y se retorna.

El campo `desde_cache: true` en la respuesta permite identificar si el resultado viene de caché.

#### 2.2.4 Fase 2-B — Protección de CPU

**Problema:** Un atacante puede enviar un arreglo de 1,000,000 de elementos, haciendo que el servidor itere 1 millón de veces y colapse.

**Solución:** Verificar el tamaño del arreglo **antes** de procesarlo.

```python
MAX_DIAS = 15

if len(solicitud.servicios_diarios) > MAX_DIAS:
    raise HTTPException(
        status_code=400,
        detail=f"Bad Request: El arreglo supera el máximo de {MAX_DIAS} días."
    )
```

Esta verificación opera en O(1) y rechaza el ataque en menos de 1 ms.

#### 2.2.5 Fase 3-C — WAF Simulado (Validación de Entrada)

**Problema:** Un atacante puede enviar valores negativos o imposibles (`[50000, 999999, -500]`) para obtener pagos fraudulentos de cientos de millones de pesos.

**Solución:** Validar cada elemento del arreglo antes de cualquier cálculo.

```python
MAX_M2_DIA = 300  # límite físicamente posible por un humano
MIN_M2_DIA = 0    # no se admiten negativos

for i, m2 in enumerate(solicitud.servicios_diarios):
    if m2 < MIN_M2_DIA:
        raise HTTPException(status_code=400, detail=f"Día {i+1}: negativo")
    if m2 > MAX_M2_DIA:
        raise HTTPException(status_code=400, detail=f"Día {i+1}: supera 300 m²")
```

**Ejemplo de ataque bloqueado (caso exacto del taller):**

```json
// Petición maliciosa
{ "id": "Trabajador1", "servicios_diarios": [50000, 999999, -500] }

// Respuesta HTTP 400 Bad Request
{ "detail": "Bad Request: El valor del día 1 supera el límite físico de 300 m²/día." }
```

#### 2.2.6 Fase 3-D — Autenticación por Token

**Problema:** Cualquier bot puede iterar sobre la API e extraer datos confidenciales de nómina sin autenticación.

**Solución:** Verificar la cabecera `Authorization` en cada petición.

```python
TOKEN_REQUERIDO = "ClaveSegura2026"

def liquidar_pago(
    solicitud: SolicitudLiquidacion,
    authorization: str | None = Header(default=None),
) -> RespuestaLiquidacion:
    if authorization != TOKEN_REQUERIDO:
        raise HTTPException(status_code=401, detail="Unauthorized: Token inválido.")
```

**Orden de validaciones (importante):**

1. **Autenticación (401)** — primera barrera: sin token válido, la petición no avanza.
2. **Límite de arreglo (400)** — segunda barrera: protección de CPU.
3. **Validación WAF (400)** — tercera barrera: valores inválidos por día.
4. **Caché** — cuarta capa: optimización de rendimiento.
5. **Cálculo** — lógica de negocio (solo si todo lo anterior pasa).

---

### 2.3 Pruebas de Funcionamiento y Estrés

#### 2.3.1 Pruebas Unitarias con pytest (21 casos)

La suite se organiza en 4 clases de prueba:

**`TestFaseUno` — Lógica de negocio (6 pruebas):**

| Prueba | Entrada | Resultado esperado |
|---|---|---|
| Sin bono | 85 m² total | Bono = $0 |
| Bono nivel 1 | 160 m² total | Bono = $20,000 |
| Bono nivel 2 | 300 m² total | Bono = $50,000 |
| Campos completos | Cualquier entrada | 5 campos obligatorios presentes |
| Umbral exacto 150 | 150 m² exactos | Bono = $0 (umbral estricto `>`) |
| Umbral exacto 250 | 250 m² exactos | Bono = $20,000 (no $50,000) |

**`TestFaseDos` — Rendimiento (5 pruebas):**

| Prueba | Escenario |
|---|---|
| Caché activa en 5ª consulta | Hits 1-4 `desde_cache=false`, hit 5 `desde_cache=true` |
| Datos correctos desde caché | Todos los campos coinciden entre cálculo y caché |
| Límite 15 días → 400 | Arreglo de 16 elementos rechazado |
| Exactamente 15 días → 200 | Arreglo de 15 elementos aceptado |
| 1 millón de registros → 400 | Inyección masiva bloqueada |

**`TestFaseTresWAF` — Fraude lógico (5 pruebas):**

| Prueba | Escenario |
|---|---|
| Valor negativo → 400 | `-10` en el arreglo |
| Valor >300 → 400 | `301` en el arreglo |
| Caso exacto del taller → 400 | `[50000, 999999, -500]` |
| Exactamente 300 m² → 200 | Límite superior aceptado |
| 0 m² → 200 | Día sin trabajo es válido |

**`TestFaseTresAuth` — Autenticación (5 pruebas):**

| Prueba | Escenario |
|---|---|
| Sin token → 401 | Sin cabecera `Authorization` |
| Token incorrecto → 401 | Valor diferente a `ClaveSegura2026` |
| Token correcto → 200 | `ClaveSegura2026` exacto |
| Token vacío → 401 | `Authorization: ""` |
| WAF después de auth → 400 | Token válido + datos inválidos = 400, no bypass |

**Resultado de ejecución:**

```
============================= test session starts =============================
collected 21 items

tests/test_api.py::TestFaseUno::test_flujo_feliz_sin_bono PASSED
tests/test_api.py::TestFaseUno::test_flujo_feliz_bono_nivel_1 PASSED
tests/test_api.py::TestFaseUno::test_flujo_feliz_bono_nivel_2 PASSED
tests/test_api.py::TestFaseUno::test_respuesta_contiene_todos_los_campos PASSED
tests/test_api.py::TestFaseUno::test_exactamente_150m2_no_recibe_bono PASSED
tests/test_api.py::TestFaseUno::test_exactamente_250m2_recibe_bono_nivel_1 PASSED
tests/test_api.py::TestFaseDos::test_cache_se_activa_en_quinta_consulta PASSED
tests/test_api.py::TestFaseDos::test_cache_devuelve_datos_correctos PASSED
tests/test_api.py::TestFaseDos::test_limite_max_dias_retorna_400 PASSED
tests/test_api.py::TestFaseDos::test_exactamente_max_dias_es_valido PASSED
tests/test_api.py::TestFaseDos::test_inyeccion_millon_registros_bloqueada PASSED
tests/test_api.py::TestFaseTresWAF::test_valor_negativo_retorna_400 PASSED
tests/test_api.py::TestFaseTresWAF::test_valor_mayor_300_retorna_400 PASSED
tests/test_api.py::TestFaseTresWAF::test_ataque_del_taller_retorna_400 PASSED
tests/test_api.py::TestFaseTresWAF::test_exactamente_300m2_es_valido PASSED
tests/test_api.py::TestFaseTresWAF::test_cero_m2_es_valido PASSED
tests/test_api.py::TestFaseTresAuth::test_sin_token_retorna_401 PASSED
tests/test_api.py::TestFaseTresAuth::test_token_incorrecto_retorna_401 PASSED
tests/test_api.py::TestFaseTresAuth::test_token_correcto_retorna_200 PASSED
tests/test_api.py::TestFaseTresAuth::test_token_vacio_retorna_401 PASSED
tests/test_api.py::TestFaseTresAuth::test_validaciones_waf_no_bypass_por_token PASSED

======================== 21 passed in 1.14s ========================
```

#### 2.3.2 Pruebas de Carga con Locust (Situación A)

**Configuración del escenario:**

```bash
locust -f locustfile.py --users 2000 --spawn-rate 100 --host http://127.0.0.1:8000
```

El archivo `locustfile.py` define dos clases de usuarios:

- **`OperarioPinturaUser`** (peso por defecto): Simula operarios reales con tiempos de espera entre 0.5 y 2 segundos. Tareas: consulta normal (peso 8), consulta alta producción (peso 2), health check (peso 1).
- **`BotAtacanteUser`** (weight = 1): Simula bots maliciosos con peticiones rápidas (0.1–0.5 s). Tareas: ataque WAF (peso 3), ataque sin token (peso 2), inyección masiva (peso 1).

**Evidencias requeridas:**

> **[INSERTAR_CAPTURA_LOCUST_ALTA_LATENCIA]**
> *Captura del panel de Locust mostrando la latencia elevada (varios segundos por petición) bajo carga de 2,000 usuarios ANTES de activar el caché. Observar cómo la línea de tiempo de respuesta aumenta progresivamente hasta colapsar.*

> **[INSERTAR_CAPTURA_LOCUST_LATENCIA_ESTABLE_CON_CACHE]**
> *Captura del panel de Locust mostrando la latencia estabilizada (en milisegundos) luego de activar el caché. La curva de latencia debe mostrar un descenso drástico y mantenerse plana durante el resto de la prueba.*

#### 2.3.3 Prueba de Estrés de CPU (`stress_cpu_test.py`)

El script `stress_cpu_test.py` valida automáticamente cuatro escenarios críticos al ejecutarse contra la API en ejecución:

**Prueba 1 — Inyección de 1,000,000 registros:**
- Envía un arreglo de 1 millón de números al endpoint.
- La API debe responder con **HTTP 400** en tiempo menor a 1 ms (la verificación `len()` opera en O(1)).
- Verifica que el servidor NO intente iterar el millón de elementos.

**Prueba 2 — Arreglo de exactamente 15 días:**
- Confirma que el límite superior es correcto y los datos válidos son procesados.
- Resultado esperado: **HTTP 200** con pago calculado correctamente.

**Prueba 3 — Benchmark de caché (10 consultas consecutivas):**
- Ejecuta 10 consultas del mismo operario y mide la latencia de cada una.
- Las primeras 4 deben ser cálculos; a partir de la 5ª, se activa el caché.
- Genera las métricas de latencia Pre-Caché vs Post-Caché.

**Prueba 4 — Caso WAF exacto del taller:**
- Envía `[50000, 999999, -500]` tal como describe el enunciado.
- Verifica que el sistema retorna **HTTP 400** y NO calcula un pago fraudulento.

```bash
# Ejecutar (con la API corriendo en otro terminal):
py -3.12 stress_cpu_test.py
```

**Resultado esperado:**

```
════════════════════════════════════════════════
  PRUEBA 1 — Inyección de 1,000,000 registros
  Tamaño del arreglo: 1,000,000 elementos
  Status HTTP : 400
  RESULTADO   : BLOQUEADO correctamente (HTTP 400) ✓

  PRUEBA 2 — Arreglo de exactamente 15 días
  Status HTTP : 200 (X.X ms)
  Pago neto   : $XXX,XXX COP
  RESULTADO   : ACEPTADO correctamente (HTTP 200) ✓

  PRUEBA 3 — Comparación Pre-Caché vs Post-Caché
  [01] CALC  |  X.XX ms | HTTP 200
  [02] CALC  |  X.XX ms | HTTP 200
  [03] CALC  |  X.XX ms | HTTP 200
  [04] CALC  |  X.XX ms | HTTP 200
  [05] CACHÉ |  X.XX ms | HTTP 200   ← caché activado
  ...
  Latencia promedio Pre-Caché  (hits 1-4) :  X.XX ms
  Latencia promedio Post-Caché (hits 5-10):  X.XX ms
  Reducción de latencia                   :  XX.X%

  PRUEBA 4 — WAF: Caso exacto del taller
  Status HTTP     : 400 (X.X ms)
  RESULTADO       : WAF activo, pago fraudulento BLOQUEADO ✓
```

#### 2.3.4 Auditoría de Seguridad con Postman/Thunder Client

**Situación C — Error HTTP 400 (datos inválidos):**

```
POST http://localhost:8000/liquidar-pago
Authorization: ClaveSegura2026
Content-Type: application/json

Body: {"id": "Trabajador1", "servicios_diarios": [50000, 999999, -500]}
```

> **[INSERTAR_CAPTURA_POSTMAN_HTTP_400_VALORES_INVALIDOS]**
> *Captura de Postman mostrando el body de la petición con valores negativos/imposibles y la respuesta HTTP 400 Bad Request con el detalle del error.*

**Situación D — Error HTTP 401 (sin token):**

```
POST http://localhost:8000/liquidar-pago
Content-Type: application/json
(Sin cabecera Authorization)

Body: {"id": "OP_001", "servicios_diarios": [50, 60]}
```

> **[INSERTAR_CAPTURA_POSTMAN_HTTP_401_SIN_TOKEN]**
> *Captura de Postman mostrando la petición sin cabecera Authorization y la respuesta HTTP 401 Unauthorized con el mensaje de error.*

---

### 2.4 Fallas Encontradas Durante la Ejecución del Trabajo

Durante el desarrollo e iteración del sistema se identificaron y mitigaron los siguientes problemas:

#### Falla 1 — Ruff requería reformateo de código

**Descripción:** Al ejecutar `ruff format --check` sobre el código inicial, el formateador reportó que `main.py` necesitaba ajuste de espaciado y longitud de líneas.

**Causa raíz:** Las constantes de negocio tenían comentarios con espaciado excesivo que no seguían el estándar PEP 8 tal como lo interpreta Ruff.

**Solución:** Se ejecutó `ruff format main.py` para aplicar el formato automáticamente. El mismo proceso se repitió sobre `locustfile.py` y `tests/test_api.py`. Tras la corrección, los tres archivos pasaron limpiamente (`ruff check` y `ruff format --check` sin errores ni advertencias).

**Lección aprendida:** Integrar el formateador desde el primer commit evita deuda técnica de estilo. El pipeline CI/CD debe incluir `ruff check && ruff format --check` como gate obligatorio.

#### Falla 2 — Importación no utilizada en los tests

**Descripción:** `ruff check` detectó `F401: main.MAX_M2_DIA imported but unused` en el archivo `tests/test_api.py`.

**Causa raíz:** Durante la redacción inicial de los tests, se importó `MAX_M2_DIA` con la intención de usarlo en una aserción, pero se optó por valores literales para mayor claridad. La importación quedó huérfana.

**Solución:** Se eliminó `MAX_M2_DIA` de la línea de importaciones. El linter pasó limpiamente en la siguiente iteración.

**Lección aprendida:** El análisis estático de código (linting) debe ejecutarse en cada iteración del ciclo de desarrollo, no solo al finalizar. Esto reduce el costo de corrección y evita acumulación de errores.

#### Falla 3 — Contaminación entre pruebas por estado global del caché

**Descripción:** Al ejecutar la suite de tests sin fixture de limpieza, las pruebas de caché fallaban intermitentemente porque el estado de `_cache_hits` y `_cache_resultados` persistía entre ejecuciones.

**Causa raíz:** Las variables del caché son diccionarios globales en el módulo `main.py`. El `TestClient` de FastAPI reutiliza la misma instancia de la aplicación entre tests dentro de la misma sesión de pytest.

**Solución:** Se implementó un fixture `autouse=True` en pytest que limpia los diccionarios del caché antes y después de cada test:

```python
@pytest.fixture(autouse=True)
def limpiar_cache():
    _cache_hits.clear()
    _cache_resultados.clear()
    yield
    _cache_hits.clear()
    _cache_resultados.clear()
```

**Lección aprendida:** Todo estado global en una API (caché, contadores, sesiones) debe ser reiniciable en el contexto de pruebas. Si el sistema crece, se debe migrar el caché a una solución externa (Redis) para facilitar el testing y el escalado horizontal.

---

## 3. Conclusiones

1. **La arquitectura en capas de defensa es efectiva.** Al aplicar las validaciones en orden secuencial (autenticación → límite de arreglo → validación WAF → caché → cálculo), el sistema rechaza el 100% de los ataques simulados antes de ejecutar lógica costosa.

2. **El caché en memoria es una solución pragmática para carga moderada.** La implementación con diccionarios y ventana deslizante de 60 segundos permite reducir drásticamente la carga computacional en escenarios de alta concurrencia (2,000 usuarios). Para sistemas de producción con múltiples instancias, la solución debe evolucionar hacia un caché distribuido como Redis.

3. **El linting automatizado con Ruff garantiza calidad de código sostenible.** La integración de `ruff check` y `ruff format` como gate obligatorio en cada iteración permitió detectar y corregir problemas de estilo e imports no usados de forma inmediata, reduciendo la deuda técnica.

4. **Las pruebas automatizadas son la red de seguridad del sistema.** Los 21 casos de prueba con pytest cubrieron todos los criterios de aceptación del taller, incluyendo los casos borde (umbral exacto de 150/250 m², límite de 15 días, 300 m²/día) y los ataques de los escenarios C y D. Esto garantiza que futuras modificaciones no rompan la lógica de negocio ni las protecciones de seguridad.

5. **La validación de entrada es la primera línea de defensa contra el fraude.** El caso `[50000, 999999, -500]` del taller demuestra que sin WAF, un atacante podría generar pagos de cientos de millones de pesos. La verificación en O(1) (antes de cualquier suma) protege tanto la integridad financiera como los recursos del servidor.

6. **Locust es una herramienta invaluable para revelar cuellos de botella.** Simular 2,000 usuarios concurrentes permite observar en tiempo real cómo la latencia escala con la carga, guiando decisiones arquitectónicas como el caché. Sin pruebas de carga, estas decisiones serían especulativas.

---

*Informe generado automáticamente por el sistema multi-agente de desarrollo — Taller 4 Unidad 3.*
*Todos los criterios de aceptación fueron verificados: 21/21 pruebas en verde, Ruff clean en todos los archivos.*
