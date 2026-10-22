# ADR-0045 — Recuperación y transporte de auditoría del benchmark

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** M0/T-09, R09-T03 y R09-T07; complementa ADR-0042

La revisión detectó que un timeout anunciaba consultar el mismo job después de eliminar el contenedor que guardaba su estado. También detectó que cada auditoría transportaba todo el historial: una sesión larga podía superar el límite de 64 Mi caracteres. Las reproducciones CPU conservadas confirman ambos problemas; no acreditan una sesión GPU ni una cadena válida de 48.000 episodios.

Para el timeout se elige recuperación acotada del recurso propio y una disposición durable y explícita: eliminado, conservado con terminal confirmado, o desconocido/en cuarentena. No se implementa un supervisor permanente nuevo. La CLI conserva intención, cursor, error original y evidencias; nunca promete consultar un recurso eliminado ni repite un POST de inferencia. El éxito que ya estuviera confirmado se conserva. Un ACK incierto no acredita cancelación ni permite liberar una reserva como si la GPU estuviese descargada. Recuperar exige ownership verificable y confirmación; no se cancelan recursos ajenos. Una sesión cuya cadena se interrumpió necesita un plan nuevo para acreditación v3, aunque conserve sus evidencias históricas.

Se compararon conservar un supervisor permanente, conservar el padre/API tras cancelación y descarga confirmadas, y terminar/reconciliar el recurso propio. Se elige la última como comportamiento mínimo: coincide con la recuperación existente y evita dejar trabajo GPU sin observador ni reserva. Conservar el padre es una extensión posible, sin cambiar la disposición ni inventar continuidad.

Para la auditoría se elige transporte aditivo **wddm_audit_delta_v1**: un consumidor propio mantiene un prefijo verificado, identificado por stream, posiciones y hash encadenado. Sólo recibe nuevas entradas y un encabezado acotado cuando no hay cambios. Verifica orden, identidad, custodia y anclas independientes antes de publicar atómicamente el nuevo prefijo. Un segmento incompleto, repetido, omitido o con prefijo falso se rechaza; no se confía en resúmenes autodeclarados ni rutas elegidas por el solicitante.

La auditoría final offline relee el historial original completo con el validador canónico. El transporte no cambia la política wddm_auto_v3, los relojes, la aceptación de episodios ni la confianza de las anclas. Se conservan RAW e intentos rechazados y los límites de tamaño, fragmentos, 2 s por episodio y cadencia de 2,5 s. No se aumenta el límite para ocultar el crecimiento. La validación de volumen usa datos CPU identificados como sintéticos; no equivale a horas de benchmark real.

Ambas correcciones requieren RED/GREEN, ownership y limpieza nativos, revisión 3 y QA antes de GPU. T-09 permanece abierto. [Revisión que origina la decisión](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/transition-review2-report.md).

**Complemento posterior:** [ADR-0046](ADR-0046-capsulas-canonicas-y-auditoria-incremental.md) fija la autoridad online de los originales protegidos y resuelve el diseño de renovación y validación acumulativa señalado por la revisión3. La próxima revisión es intento4 explícito; los resultados anteriores se conservan y esta decisión no acredita la implementación.


**Desarrollo de integración:** [ADR-0050](ADR-0050-autoridad-canonica-aislada-del-benchmark.md) fija la autoridad online en proceso propio, lectura por pasos e ingreso prioritario. La ratificación del diseño no acredita implementación, plazos, FINAL ni rendimiento.
