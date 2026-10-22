# ADR-0040 — Frontera entre parser HTTP y aplicación

- **Estado:** aceptada; revisión del rebate y QA de evidencia conformes, integración Git pendiente
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** M1/T-01; precisa la ampliación de ADR-0038 sin cambiar CA14 para peticiones válidas

La QA Docker acredita19criterios HTTP y detecta dos respuestas400 `text/plain` ante mensajes con dos líneas Host. ADR-0038 había extendido403 a ese caso sin distinguir el parser del middleware. Esa ampliación fue incorrecta: [RFC9112 §3.2](https://www.rfc-editor.org/rfc/rfc9112.html#section-3.2) exige400 cuando una petición contiene más de una línea Host; también para Host inválido y para HTTP/1.1 sin Host.

Se conserva el parser estricto de Uvicorn/h11. Los mensajes HTTP mal formados rechazados antes de ASGI producen400 y pueden usar el cuerpo del servidor HTTP. Las peticiones aceptadas por el parser con un Host único y bien formado fuera de la lista permitida producen403 `INVALID_HOST` y `application/problem+json`. Origin ajeno conserva403 en cualquier método conforme a CA14 y ADR-0038. Si un transporte entrega a ASGI un scope con Host ausente o duplicado, el middleware sigue rechazándolo403 como defensa adicional.

Se descartan modificar el parser para forzar403, añadir un proxy o interceptar sus errores: aumentan superficie y contradicen la norma. No se acepta ninguna petición previamente rechazada, no se amplían autoridades permitidas y no se reduce el control de Origin.

Los dos resultados previos y su QA con gaps permanecen originales. Un suplemento nuevo debe contrastar los mensajes/respuestas contra esta frontera y la norma, con revisión fresca y validación independiente de la evidencia existente. La clasificación nueva no se presenta como una prueba de red ejecutada otra vez. Código, imagen y pruebas CPU permanecen iguales; si su hash cambia, la prueba anterior deja de acreditar la paridad vigente.
