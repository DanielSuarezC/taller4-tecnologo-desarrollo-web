```
Departamento de Ingeniería de Sistemas y Telemática
```
**Renovación de la acreditación ins�tucional, Res. N° 000020 del 11 de enero de 2023 por el MEN
Cer�ficados en: ISO: 9001 - ISO: 45001 - ISO: 14001 de ICONTEC**

## TALLER – UNIDAD 3

```
Contexto del problema
```
```
Una empresa que ofrece un servicio de pintura de muebles ha contratado el
desarrollo del motor central de su nuevo Sistema de Liquidación de Pagos. El
objetivo es construir una API REST en Python (FastAPI o Flask) que calcule los
pagos semanales de los operarios de pintura.
```
```
Sin embargo, la gerencia ha establecido dos advertencias críticas sobre el
comportamiento del sistema:
```
1. Los viernes a las 6:00 p.m. el sistema recibe un alto número de
    conexiones simultáneas de trabajadores que desean consultar su pago.
2. Se han detectado intentos de fraude por parte de bots que buscan
    engañar al sistema para generar pagos falsos o sobrecargar el servidor.

```
Fase 1: Desarrollo Base
```
```
Se debe aplicar la lógica de programación para construir la API desde cero,
cumpliendo estrictamente con las siguientes reglas de negocio:
```
- **Endpoint:** Se debe crear una ruta POST llamada /liquidar-pago.
- **Datos de Entrada:** El sistema debe recibir en formato JSON la
    identificación del operario y un arreglo (lista) con los metros cuadrados
    (m^2) de pintura realizados por el trabajador en cada día.
- **Lógica de Negocio:**

```
o El sistema debe recorrer el arreglo y sumar los metros cuadrados
totales.
```
```
o El precio base de liquidación es de $1,200 COP por m^2.
```
```
o Bonificaciones: Si el trabajador suma más de 150 m^2 en total,
recibe un bono extra de $20,000 COP. Si suma más de 250 m^2,
el bono es de $50,000 COP.
```
- **Salida Esperada:** La API debe retornar un JSON que contenga: ID del
    trabajador, m^2 Totales, Pago Base, Bono y Pago Neto.

```
(Nota: Se debe asegurar que la API se encuentre en ejecución y funcione
correctamente en el entorno local antes de avanzar a las siguientes fases).
```
```
Fase 2: Escenarios de Rendimiento
```
```
Una vez validado el funcionamiento de la API, se debe someter a condiciones
de estrés utilizando la herramienta Locust (o similares como JMeter) para
simular los siguientes escenarios extremos.
```

```
Departamento de Ingeniería de Sistemas y Telemática
```
**Renovación de la acreditación ins�tucional, Res. N° 000020 del 11 de enero de 2023 por el MEN
Cer�ficados en: ISO: 9001 - ISO: 45001 - ISO: 14001 de ICONTEC**

```
Situación A: Tráfico Masivo
```
- El código puede funcionar correctamente para una persona, pero se
    debe evaluar el comportamiento cuando múltiples trabajadores realizan
    la petición simultáneamente.
- Se debe configurar Locust para simular **2000 usuarios concurrentes**
    con una tasa de entrada de 100 usuarios por segundo.
- Se debe verificar el panel de métricas y analizar si la latencia se
    incrementa de milisegundos a varios segundos.
- **Solución Arquitectónica:** Se debe modificar el código en Python
    implementando una estrategia de _caché en memoria_. Si un mismo
    trabajador consulta su liquidación 5 veces en un minuto, la API no debe
    recalcular el proceso; debe devolver el resultado previamente guardado.
    Se debe ejecutar nuevamente la prueba para demostrar la reducción
    drástica de la latencia.

```
Situación B: Sobrecarga de CPU
```
- ¿Qué sucede si un atacante no envía los datos de los 6 días hábiles, sino
    un arreglo con 1 millón de registros numéricos? El ciclo iterativo
    intentará sumar 1 millón de veces, asfixiando el procesador del servidor
    y bloqueando a los usuarios legítimos.
- Se debe utilizar Postman o Thunder Client para enviar a la API un JSON
    con un arreglo extenso de números y registrar el tiempo de
    procesamiento.
- **Solución Arquitectónica:** La API no debe confiar en el tamaño de los
    datos de entrada. Se debe limitar dinámicamente la longitud del arreglo
    (ej. máximo 15 días) para proteger los recursos del servidor.

```
Fase 3: Escenarios de Seguridad
```
```
Se debe evaluar la resistencia del código frente a ataques reales de inyección
de datos y accesos no autorizados.
```
```
Situación C: Fraude Lógico e Inyección de Datos
```
- El algoritmo matemático inicial asume que los números ingresados son
    siempre positivos y coherentes. Un atacante podría enviar el siguiente
    JSON:

```
{"id": "Trabajador1", "servicios_diarios": [50000, 999999, -500]}
```
- Al enviar estos datos a la API, si el sistema responde con un pago neto
    de cientos de millones de pesos, se evidencia una vulnerabilidad crítica.


```
Departamento de Ingeniería de Sistemas y Telemática
```
**Renovación de la acreditación ins�tucional, Res. N° 000020 del 11 de enero de 2023 por el MEN
Cer�ficados en: ISO: 9001 - ISO: 45001 - ISO: 14001 de ICONTEC**

- **Solución Arquitectónica:** Se debe implementar el pilar de _Validación_
    **Estricta de Entrada (WAF simulado)**. El código debe verificar que los
    valores diarios no sean negativos ni superen los límites físicamente
    posibles para un humano (ej. no más de 300 m^2 pintados en un solo
    día). En caso de detectar una anomalía, la API debe interrumpir el
    proceso y retornar un _Error HTTP 400 Bad Request_.

```
Situación D: Acceso No Autorizado
```
- En la configuración actual, cualquier persona que conozca la dirección de
    la API puede realizar consultas. Esto permite que un bot pueda iterar
    identificaciones para extraer información confidencial de nómina.
- Si se intenta acceder a la API desde un navegador en modo incógnito o
    desde otro equipo en la misma red, el sistema entregará los datos sin
    requerir identificación.
- **Solución Arquitectónica:** Se debe implementar el _Principio de Menor_
    _Privilegio y Autenticación_. La API debe modificarse para exigir
    obligatoriamente un "Token de Acceso" en las cabeceras (Headers) de la
    petición (Ej. Authorization: ClaveSegura2026). Si la petición carece de
    esta clave exacta, el código debe rechazar la solicitud retornando un
    _Error HTTP 401 Unauthorized_.

```
Entregables
```
```
Se debe elaborar y entregar un informe técnico (en formato PDF) que contenga
la explicación del código y de las modificaciones arquitectónicas
implementadas, respaldado por las siguientes evidencias (capturas de
pantalla):
```
1. Código fuente de la API evidenciando las validaciones de datos y
    seguridad implementadas.
2. Captura de Locust evidenciando la latencia alta (colapso) antes de
    implementar el Caché.
3. Captura de Locust demostrando la estabilidad (latencia plana) luego de
    aplicar el Caché.
4. **Auditoría de Seguridad:**

```
o Captura de Postman donde se observe el Error HTTP 400 al
intentar enviar metros cuadrados negativos o cantidades
imposibles.
```
```
o Captura de Postman donde se observe el Error HTTP 401 al
realizar la consulta sin el Token de Seguridad respectivo.
```

```
Departamento de Ingeniería de Sistemas y Telemática
```
**Renovación de la acreditación ins�tucional, Res. N° 000020 del 11 de enero de 2023 por el MEN
Cer�ficados en: ISO: 9001 - ISO: 45001 - ISO: 14001 de ICONTEC**

```
¡Para tener en cuenta...!
```
```
Para la realización de esta actividad, se deben considerar los siguientes
lineamientos:
```
- El trabajo podrá ser realizado en grupos de máximo 3 integrantes.
- El envío del trabajo debe realizarse estrictamente antes de los plazos
    establecidos en la plataforma.

```
El documento entregable debe cumplir, como mínimo, con la siguiente
estructura:
```
1. Introducción
2. Desarrollo

```
o Adecuación del ambiente de desarrollo.
```
```
o Creación de recursos (código fuente).
```
```
o Pruebas de funcionamiento y estrés.
```
```
o Fallas encontradas durante la ejecución del trabajo.
```
3. Conclusiones


