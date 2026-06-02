# Sistema de Liquidación de Pagos — API REST

**Taller 4, Unidad 3 | Ingeniería de Sistemas | Universidad de Córdoba**  
**Curso:** Taller Tecnólogo Desarrollo Web

---

## Tabla de Contenidos

1. [¿Qué hace este proyecto?](#1-qué-hace-este-proyecto)
2. [Tecnologías utilizadas](#2-tecnologías-utilizadas)
3. [Cómo acceder al código desde GitHub](#3-cómo-acceder-al-código-desde-github)
4. [Cómo instalar y ejecutar el proyecto](#4-cómo-instalar-y-ejecutar-el-proyecto)
5. [Estructura del proyecto](#5-estructura-del-proyecto)
6. [Cómo probar la API con Postman](#6-cómo-probar-la-api-con-postman)
7. [Cómo ejecutar las pruebas automatizadas](#7-cómo-ejecutar-las-pruebas-automatizadas)
8. [Cómo ejecutar las pruebas de carga con Locust](#8-cómo-ejecutar-las-pruebas-de-carga-con-locust)
9. [Capturas de pantalla requeridas por el taller](#9-capturas-de-pantalla-requeridas-por-el-taller)

---

## 1. ¿Qué hace este proyecto?

Esta es una **API REST** (una aplicación de servidor que recibe y responde peticiones por internet) que calcula el pago semanal de los operarios de una empresa de pintura de muebles.

Un operario ingresa cuántos metros cuadrados pintó cada día de la semana, y la API calcula:

- **Pago base:** metros cuadrados totales × $1,200 COP
- **Bono:** $20,000 si superó 150 m², o $50,000 si superó 250 m²
- **Pago neto:** pago base + bono

Además, el sistema implementa protecciones de seguridad y rendimiento para resistir ataques reales.

---

## 2. Tecnologías utilizadas

A continuación se explica cada tecnología, por qué se usó y un contexto básico para entenderla.

---

### Python 3.12

**¿Qué es?**  
Python es un lenguaje de programación de propósito general, famoso por ser fácil de leer y escribir. Es uno de los lenguajes más populares del mundo para desarrollo web, ciencia de datos e inteligencia artificial.

**¿Por qué se usó?**  
El enunciado del taller pedía explícitamente Python. Además, Python tiene un ecosistema maduro de librerías para APIs web y pruebas automatizadas.

**Contexto técnico:**  
En este proyecto, Python es el "motor" de todo: define la lógica de negocio (calcular pagos), las validaciones de seguridad y la estructura de los datos que entran y salen de la API.

---

### FastAPI

**¿Qué es?**  
FastAPI es un **framework web** para Python. Un framework es como una plantilla o andamiaje que ya resuelve los problemas comunes (recibir peticiones HTTP, validar datos, generar respuestas), para que el desarrollador se concentre solo en la lógica del negocio.

**¿Por qué se usó?**  
- Es el framework más moderno y rápido para crear APIs en Python.
- Genera automáticamente una **documentación interactiva** (Swagger UI) accesible en el navegador.
- Integra validación de datos automática a través de Pydantic.
- El enunciado lo permitía explícitamente junto a Flask.

**Contexto técnico:**  
FastAPI usa "decoradores" de Python (líneas que comienzan con `@`) para definir rutas. Por ejemplo, `@app.post("/liquidar-pago")` le dice al framework: "cuando llegue una petición POST a la ruta `/liquidar-pago`, ejecuta esta función".

---

### Uvicorn

**¿Qué es?**  
Uvicorn es el **servidor web** que ejecuta la aplicación FastAPI. Es el programa que "escucha" las conexiones que llegan por internet al puerto 8000 del computador.

**¿Por qué se usó?**  
FastAPI por sí solo es solo código Python; no puede recibir conexiones de red. Uvicorn es el componente que hace posible esa comunicación. Es el servidor recomendado por los creadores de FastAPI.

**Contexto técnico:**  
Uvicorn implementa el estándar **ASGI** (Asynchronous Server Gateway Interface), que permite manejar miles de conexiones simultáneas sin bloquear el procesador, a diferencia del estándar antiguo WSGI.

---

### Pydantic

**¿Qué es?**  
Pydantic es una librería que permite definir la "forma" que deben tener los datos usando clases de Python. Si los datos que llegan no coinciden con esa forma, Pydantic los rechaza automáticamente.

**¿Por qué se usó?**  
FastAPI incluye Pydantic de forma nativa. En el proyecto se usó para definir:
- **`SolicitudLiquidacion`**: qué datos debe enviar el cliente (id y lista de metros cuadrados).
- **`RespuestaLiquidacion`**: qué datos devuelve la API (id, metros totales, pago base, bono, pago neto).

**Contexto técnico:**  
Gracias a Pydantic, si alguien envía un texto donde la API espera un número, o si olvida un campo obligatorio, la API responde automáticamente con un error claro sin necesidad de código adicional.

---

### pytest

**¿Qué es?**  
pytest es un **framework de pruebas automatizadas** para Python. Permite escribir funciones que verifican automáticamente que el código funciona correctamente.

**¿Por qué se usó?**  
Las pruebas manuales (probar a mano con Postman) son lentas y propensas a error humano. Con pytest se escribieron 21 casos de prueba que se ejecutan todos en menos de 2 segundos y verifican automáticamente cada escenario del taller.

**Contexto técnico:**  
Cada función en `tests/test_api.py` que comienza con `test_` es un caso de prueba. pytest los detecta automáticamente, los ejecuta y reporta cuáles pasaron (`PASSED`) y cuáles fallaron (`FAILED`).

---

### httpx

**¿Qué es?**  
httpx es un **cliente HTTP** para Python. Permite hacer peticiones web (GET, POST, etc.) desde código Python, igual que un navegador, pero de forma programática.

**¿Por qué se usó?**  
FastAPI usa `TestClient` (que internamente usa httpx) para simular peticiones HTTP en las pruebas sin necesidad de levantar un servidor real. Esto hace las pruebas más rápidas y confiables.

**Contexto técnico:**  
En `tests/test_api.py`, la línea `client.post("/liquidar-pago", json=payload, headers=...)` simula exactamente lo que haría Postman, pero desde código Python.

---

### Locust

**¿Qué es?**  
Locust es una herramienta de **pruebas de carga y estrés**. Permite simular miles de usuarios usando la API al mismo tiempo para ver cómo se comporta el sistema bajo presión.

**¿Por qué se usó?**  
El taller pedía simular **2,000 usuarios concurrentes** para observar cómo la latencia (tiempo de respuesta) aumenta sin caché y cómo se estabiliza con caché. Locust tiene una interfaz web gráfica que muestra estas métricas en tiempo real.

**Contexto técnico:**  
El archivo `locustfile.py` define dos tipos de usuarios virtuales:
- `OperarioPinturaUser`: simula operarios legítimos consultando su pago.
- `BotAtacanteUser`: simula bots maliciosos enviando datos inválidos.

---

### Ruff

**¿Qué es?**  
Ruff es un **linter y formateador** de código Python. Un linter es una herramienta que analiza el código en busca de errores de estilo, importaciones no usadas, variables mal definidas y otros problemas.

**¿Por qué se usó?**  
Para garantizar que el código sea limpio, legible y siga los estándares profesionales de Python (PEP 8). Es como el corrector ortográfico, pero para código.

**Contexto técnico:**  
Ruff tiene dos funciones principales en este proyecto:
- `ruff check`: detecta problemas (errores de estilo, imports sin usar).
- `ruff format`: reformatea el código automáticamente al estilo correcto.

---

## 3. Cómo acceder al código desde GitHub

### Paso 1: Ir al repositorio

El repositorio del proyecto está en GitHub en la siguiente dirección:

```
https://github.com/DanielSuarezC/taller4-tecnologo-desarrollo-web
```

Abre esa URL en tu navegador. Verás la página principal del repositorio con todos los archivos del proyecto.

---

### Paso 2: Descargar el código (dos opciones)

#### Opción A — Descargar como ZIP (más fácil, sin instalar Git)

1. En la página de GitHub, haz clic en el botón verde que dice **`<> Code`**.
2. En el menú desplegable, haz clic en **`Download ZIP`**.
3. Se descargará un archivo `.zip`. Extráelo en una carpeta de tu computador.

#### Opción B — Clonar con Git (recomendado)

Si tienes Git instalado, abre una terminal (PowerShell o CMD en Windows) y ejecuta:

```bash
git clone https://github.com/DanielSuarezC/taller4-tecnologo-desarrollo-web.git
```

Esto crea una carpeta con todo el código del proyecto en tu computador.

> **¿Qué es Git?** Git es un sistema de control de versiones: guarda el historial completo de cambios de un proyecto. GitHub es un sitio web donde se alojan repositorios Git para compartirlos.

> **¿Qué es `git clone`?** Es el comando que descarga una copia completa del repositorio (código + historial de cambios) a tu computador.

---

## 4. Cómo instalar y ejecutar el proyecto

### Requisitos previos

Antes de empezar, necesitas tener instalado:

| Herramienta | Versión mínima | Cómo verificar que está instalada |
|---|---|---|
| Python | 3.11 o superior | Ejecutar `python --version` en la terminal |

Si Python no está instalado, descárgalo desde [python.org](https://www.python.org/downloads/). Durante la instalación en Windows, **marca la casilla "Add Python to PATH"**.

---

### Paso 1: Abrir la terminal en la carpeta del proyecto

1. Abre **PowerShell** o **CMD**.
2. Navega a la carpeta donde descargaste o clonaste el proyecto:

```powershell
cd "C:\ruta\donde\descargaste\el\proyecto"
```

Por ejemplo:
```powershell
cd "C:\Users\TuNombre\Downloads\taller4-tecnologo-desarrollo-web"
```

---

### Paso 2: Crear un entorno virtual

Un **entorno virtual** es una carpeta aislada donde se instalan las dependencias del proyecto sin afectar el resto del sistema. Es una buena práctica obligatoria en proyectos Python.

```powershell
python -m venv venv
```

Esto crea una carpeta llamada `venv` en el directorio del proyecto.

> **¿Por qué un entorno virtual?** Porque diferentes proyectos pueden necesitar versiones distintas de las mismas librerías. El entorno virtual garantiza que las versiones exactas del proyecto no choquen con otras instalaciones del computador.

---

### Paso 3: Activar el entorno virtual

```powershell
venv\Scripts\activate
```

Sabrás que está activado porque el prompt de la terminal cambiará y mostrará `(venv)` al inicio:

```
(venv) PS C:\ruta\del\proyecto>
```

---

### Paso 4: Instalar las dependencias

```powershell
pip install -r requirements.txt
```

Este comando lee el archivo `requirements.txt` e instala automáticamente todas las librerías necesarias (FastAPI, Uvicorn, pytest, Locust, etc.) con sus versiones exactas.

> **¿Qué es `pip`?** Es el gestor de paquetes de Python. Funciona igual que una tienda de aplicaciones: `pip install <nombre>` descarga e instala una librería desde el repositorio oficial PyPI.

> **¿Qué es `requirements.txt`?** Es un archivo de texto que lista todas las dependencias del proyecto con su versión exacta. Garantiza que cualquier persona que instale el proyecto obtenga exactamente las mismas versiones.

---

### Paso 5: Ejecutar la API

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Explicación de cada parte del comando:**

| Parte | Significado |
|---|---|
| `uvicorn` | El servidor web que ejecuta la API |
| `main:app` | "Busca en el archivo `main.py` la variable llamada `app`" |
| `--reload` | Reinicia automáticamente el servidor cuando modificas el código |
| `--host 0.0.0.0` | Acepta conexiones desde cualquier IP (no solo `localhost`) |
| `--port 8000` | Escucha en el puerto 8000 |

Si todo funcionó correctamente, verás en la terminal algo similar a:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

**La API ya está corriendo.** Para detenerla, presiona `Ctrl + C`.

---

### Paso 6: Verificar que funciona

Abre tu navegador y entra a:

```
http://localhost:8000/health
```

Deberías ver:

```json
{"status": "ok"}
```

También puedes ver la **documentación interactiva automática** que genera FastAPI en:

```
http://localhost:8000/docs
```

---

## 5. Estructura del proyecto

```
app/
├── main.py               # Código principal de la API (toda la lógica)
├── requirements.txt      # Lista de dependencias del proyecto
├── locustfile.py         # Configuración de pruebas de carga (Locust)
├── stress_cpu_test.py    # Script de prueba de estrés de CPU
├── taller4.md            # Enunciado original del taller
├── informe_tecnico.md    # Informe técnico del proyecto
└── tests/
    ├── __init__.py       # Marca la carpeta como paquete Python
    └── test_api.py       # Suite de 21 pruebas automatizadas
```

---

## 6. Cómo probar la API con Postman

**Postman** es una aplicación gratuita que permite hacer peticiones HTTP a una API de forma visual, sin necesidad de escribir código. Descárgala en [postman.com/downloads](https://www.postman.com/downloads/).

> **Importante:** La API debe estar ejecutándose (Paso 5) antes de probar con Postman.

---

### Caso 1: Petición exitosa (HTTP 200)

Configura Postman así:

| Campo | Valor |
|---|---|
| Método | `POST` |
| URL | `http://localhost:8000/liquidar-pago` |
| Headers > Authorization | `ClaveSegura2026` |
| Body > raw > JSON | Ver abajo |

**Body:**
```json
{
  "id": "OP_001",
  "servicios_diarios": [50, 60, 45, 55, 40, 30]
}
```

**Respuesta esperada (HTTP 200):**
```json
{
  "id": "OP_001",
  "metros_cuadrados_totales": 280.0,
  "pago_base": 336000.0,
  "bono": 50000.0,
  "pago_neto": 386000.0,
  "desde_cache": false
}
```

---

### Caso 2: Error HTTP 401 — Sin token de seguridad

Igual que el caso anterior pero **sin el header Authorization**. La API debe rechazar la petición.

**Respuesta esperada (HTTP 401):**
```json
{
  "detail": "Unauthorized: Token de acceso inválido o ausente."
}
```

---

### Caso 3: Error HTTP 400 — Datos inválidos (WAF)

**Body con datos maliciosos:**
```json
{
  "id": "Trabajador1",
  "servicios_diarios": [50000, 999999, -500]
}
```

**Respuesta esperada (HTTP 400):**
```json
{
  "detail": "Bad Request: El valor del día 1 supera el límite físico de 300 m²/día (50000.0 m² recibidos)."
}
```

---

## 7. Cómo ejecutar las pruebas automatizadas

Con la API **no necesariamente corriendo** (pytest usa un servidor de pruebas interno), ejecuta:

```powershell
python -m pytest tests/ -v
```

El flag `-v` (verbose) muestra el nombre de cada prueba y si pasó o falló.

**Resultado esperado:**

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

---

## 8. Cómo ejecutar las pruebas de carga con Locust

Las pruebas de carga miden cómo se comporta la API cuando muchos usuarios la usan al mismo tiempo.

### Paso 1: Tener la API corriendo

En una terminal ejecuta:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 2: Abrir otra terminal y lanzar Locust

**Deja la primera terminal abierta** (la API debe seguir corriendo) y abre una segunda terminal, activa el entorno virtual y ejecuta:

```powershell
venv\Scripts\activate
locust -f locustfile.py --host http://127.0.0.1:8000
```

### Paso 3: Acceder al panel web de Locust

Abre tu navegador en:
```
http://localhost:8089
```

Verás la pantalla de configuración de Locust. Ingresa:

| Campo | Valor |
|---|---|
| Number of users | `2000` |
| Spawn rate | `100` |
| Host | `http://127.0.0.1:8000` |

Haz clic en **Start swarming**.

---

## 9. Capturas de pantalla requeridas por el taller

El taller requiere las siguientes capturas. A continuación se explica exactamente cómo obtener cada una.

---

### Captura 1 — Código fuente con validaciones de seguridad

**Cómo obtenerla:**
1. Abre el archivo [main.py](main.py) en Visual Studio Code (u otro editor).
2. Toma una captura que muestre las secciones de validación: el bloque del token (líneas 96-101), el límite de días (líneas 103-111) y el WAF (líneas 113-131).
3. Si el editor muestra resaltado de sintaxis con colores, la captura queda más profesional.

**Qué debe verse:** El código Python con los bloques `if authorization != TOKEN_REQUERIDO`, `if len(solicitud.servicios_diarios) > MAX_DIAS` y el bucle de validación WAF.

---

### Captura 2 — Locust: latencia ALTA antes del caché (colapso)

Esta captura muestra el problema que el caché resuelve. Para reproducir el escenario sin caché, es necesario modificar temporalmente el código para desactivar el caché, o simplemente observar la latencia en los primeros segundos de la prueba antes de que el caché se active.

**Cómo obtenerla:**

1. Ejecuta la API y Locust con 2,000 usuarios (sigue los pasos del apartado 8).
2. Espera hasta que todos los usuarios estén activos (el contador de usuarios llegue a 2,000).
3. En el panel de Locust, haz clic en la pestaña **Charts**.
4. Observa la gráfica de **Response Times**: en los primeros segundos, antes de que el caché entre en acción, verás la latencia elevarse (puede llegar a varios cientos de milisegundos o segundos).
5. Toma la captura de pantalla en ese momento de alta latencia.

**Qué debe verse:** El gráfico de Locust con la curva de latencia en valores altos (por encima de 200-500 ms o más), con 2,000 usuarios activos visibles en la parte superior de la pantalla.

---

### Captura 3 — Locust: latencia ESTABLE después del caché

**Cómo obtenerla:**

1. Con Locust corriendo y la prueba en marcha, deja que pasen varios minutos (3-5 minutos).
2. El caché se activa automáticamente para operarios que hayan hecho 5 o más consultas en el último minuto.
3. Observa la gráfica **Charts**: la curva de latencia descenderá y se mantendrá plana (estable).
4. Toma la captura cuando la latencia esté estabilizada en valores bajos y constantes.

**Qué debe verse:** El gráfico de Locust con la curva de latencia baja y plana (por debajo de 50-100 ms), demostrando la efectividad del caché. El número de usuarios debe seguir siendo 2,000.

---

### Captura 4 — Postman: Error HTTP 400 (datos negativos o imposibles)

**Cómo obtenerla:**

1. Abre Postman.
2. Crea una nueva petición de tipo **POST** a `http://localhost:8000/liquidar-pago`.
3. En la pestaña **Headers**, agrega:
   - Key: `Authorization`
   - Value: `ClaveSegura2026`
4. En la pestaña **Body**, selecciona **raw** y **JSON**, y escribe:
   ```json
   {
     "id": "Trabajador1",
     "servicios_diarios": [50000, 999999, -500]
   }
   ```
5. Haz clic en **Send**.
6. Toma la captura de pantalla.

**Qué debe verse:** En Postman, la sección superior muestra la petición con el body de datos maliciosos. En la parte inferior (respuesta), debe aparecer el código **400 Bad Request** en rojo/naranja, y en el body de la respuesta el mensaje de error explicando qué valor fue inválido.

---

### Captura 5 — Postman: Error HTTP 401 (sin token de seguridad)

**Cómo obtenerla:**

1. En Postman, crea otra petición **POST** a `http://localhost:8000/liquidar-pago`.
2. **No agregues el header Authorization** (o si lo agregaste antes, elimínalo).
3. En **Body**, escribe cualquier dato válido:
   ```json
   {
     "id": "OP_001",
     "servicios_diarios": [50, 60, 45]
   }
   ```
4. Haz clic en **Send**.
5. Toma la captura de pantalla.

**Qué debe verse:** En Postman, la respuesta muestra el código **401 Unauthorized** en rojo/naranja, con el mensaje `"Unauthorized: Token de acceso inválido o ausente."`. En los headers de la petición no debe aparecer la cabecera `Authorization`.

---

## Comandos de referencia rápida

```powershell
# Activar el entorno virtual (Windows)
venv\Scripts\activate

# Ejecutar la API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar las pruebas automatizadas
python -m pytest tests/ -v

# Ejecutar el linter (verificar calidad de código)
python -m ruff check .

# Ejecutar Locust (pruebas de carga)
locust -f locustfile.py --host http://127.0.0.1:8000

# Ejecutar el script de estrés de CPU (con la API corriendo)
python stress_cpu_test.py
```

---

## Glosario de términos técnicos

| Término | Definición sencilla |
|---|---|
| **API REST** | Aplicación de servidor que recibe y responde peticiones HTTP (como las que hace un navegador web) |
| **Endpoint** | Una URL específica de la API que realiza una acción (ej. `/liquidar-pago`) |
| **HTTP** | Protocolo de comunicación que usan los navegadores y las APIs para intercambiar datos |
| **JSON** | Formato de texto para representar datos estructurados, como un diccionario de Python |
| **Header** | Metadato que se envía junto a una petición HTTP (ej. el token de autorización) |
| **HTTP 200** | Código de respuesta que significa "todo salió bien" |
| **HTTP 400** | Código de respuesta que significa "los datos enviados son incorrectos" |
| **HTTP 401** | Código de respuesta que significa "no tienes permiso para acceder" |
| **Caché** | Almacenamiento temporal de un resultado ya calculado para no repetir el cálculo |
| **Latencia** | Tiempo que tarda la API en responder a una petición |
| **WAF** | Web Application Firewall: capa de seguridad que filtra datos maliciosos |
| **Linter** | Herramienta que analiza el código en busca de errores de estilo |
| **Entorno virtual** | Carpeta aislada con las dependencias de un proyecto Python específico |
| **Pytest fixture** | Función especial de pytest que prepara el estado antes de cada prueba |
