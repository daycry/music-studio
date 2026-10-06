# T-16 — fallo real de preflight y corrección del supervisor

Fecha: 2026-10-06. El estado sigue en el ledger. Este informe separa el intento de ejecución, el diagnóstico CPU y la revisión/QA pendientes del arnés. No reabre las pruebas de producto de T-16 ni declara calidad musical.

Actualización: el [intento 1 de revisión](harness-fix2-review-1.md) encontró A-F2-01 y motivó [fix3](harness-fix3-report.md). Este informe y su recibo describen el snapshot histórico de fix2, no el runner actual.

## Intento real detenido

Tras observar Ollama vacío y GPU por debajo de 1.600 MiB, el preflight del runner pasó con 1.391 MiB. Se inició sesión privada `01M47AYMT21MACX62R4VXTXBP7`, con SFT primero; el baseline del grupo fue 1.361 MiB. En 2,047 s el supervisor paró con `monitor_failed` y `ValueError`. El job reservado respondía 404, `owned-outputs.json` está vacío y no hay toma terminada. No se reutilizó la excepción anterior ni se elevó el umbral.

El arnés identificó su contenedor por etiqueta/imagen/ID y ejecutó stop y remove, ambos exit0. No afirmó `unload_confirmed`: el recibo mantiene false. Retirar el contenedor acredita limpieza del proceso Docker; no convierte este intento en una generación correcta. El servicio previo 8101 se conserva. Los archivos del intento permanecen en caché privada y no se sobrescriben.

## Diagnóstico con debug-root-cause

**Reproducción mínima:** el test CPU `test_real_preflight_loading_without_cap_does_not_abort` invoca `/v1/jobs` con preflight bloqueado mediante Event. El servidor real devuelve `state=loading`, sin modelo, sin job aceptado y `cap_mb=0`; el job responde 404 y no existe hijo. NVML se sustituye por una medida válida de 12.000/11.000 MiB. La guarda anterior falla con `ValueError: INVALID_GPU_MONITOR_DATA`.

**Aislamiento:** `server.py` usa maintenance durante validación/preflight y publica ese estado como loading. `load()` calcula y asigna el cap antes de cargar el proceso hijo. El supervisor heredado de T-15 interpreta todo loading como carga GPU y exige un cap positivo incluso en esta fase previa. Los logs del intento acreditan health/model catalog y 404 del job; no se atribuye el fallo a calidad SFT, pesos, voz o inferencia terminada.

**Hipótesis probada:** la guarda confunde la validación previa al job con carga del modelo. El test HTTP reproduce la combinación y el error sin Docker, CUDA ni modelos. El primer fixture usaba CpuGpu (total/free=0), que también dispara la validación por otra razón; se corrigió a una medida válida, se retiró el primer fix y se repitió el RED correcto antes de reescribirlo. Ese fallo inicial no cuenta como evidencia TDD del criterio.

**Fix:** wrapper local en el runner T-16: únicamente permite `cap=0` mientras loading no tiene ni job ni modelo, con total/free finitos y válidos. Una vez hay job/modelo, cap ausente sigue fallando; datos no finitos, free fuera del total y cap negativo siguen rechazados. Al aparecer cap positivo conserva el umbral conservador del 95 %. Las utilidades y fuentes históricas T-15 permanecen intactas.

## Evidencia y límites

- RED correcto: test HTTP dirigido, 1 failed por `INVALID_GPU_MONITOR_DATA`, sin hijo/job aceptado, 2026-10-06.
- GREEN dirigido: 1 passed en 0,32 s, exit0.
- Suite privada del arnés: 20 passed en 0,87 s, cero avisos, exit0; incluye las 12 regresiones previas y ocho casos nuevos de estado/preflight/datos inválidos/umbral.
- Snapshot previo reconstruido byte a byte y comprobado contra el SHA revisado `58af0f7266404985d331bf39795084480cddf9848dc3942eb01f4434dae4ee85`; no se sobrescriben los recibos anteriores.
- Fuente actual y SHA en [recibo](harness-fix2-receipt.json). Revisión fresca y QA independientes todavía pendientes. No se ha vuelto a cargar un modelo ni generado una nueva sesión después del fix.

La corrección de orquestación privada no cambia la imagen de producto ni justifica repetir sus 430 pruebas/build. No se escriben ni se promueven journals ajenos. Los tiempos de reloj son solo ventanas; el meter degrada a estimado con tokens/coste/horas IA reales desconocidos. T-16 permanece en-progreso y sus criterios GPU/escucha abiertos.
