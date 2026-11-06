# Verificación real del batch GPU — M0/T-08

Fecha: 2026-11-06.

**El batch original pasó en una única corrida: 4 aprobadas, 0 fallidas, 0 errores, 0 omitidas y 48 deseleccionadas**, salida 0 y **275,83 s**. Tres pruebas ejecutan inferencia GPU; beats permanece en CPU aunque comparte la marca `gpu`. El [JUnit original](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/qa/raw/junit.xml) acredita las cuatro pruebas.

La ejecución siguió a la publicación del informe CPU en `cd40c2b3fbb2ee4c9538392fbc4930d9f89e70a9`, conforme a la autorización expresa del propietario. La secuencia consta en el [preflight de autorización](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/authorization-preflight.json).

## Resultados funcionales

| Prueba original | Ejecución | Resultado observado |
|---|---|---|
| Transcripción y alineación | CUDA/BF16 | 87 palabras con tiempos válidos; ASR liberado antes de cargar el alineador. |
| CLAP | CUDA/BF16 | Similitud finita 0,00440384, dentro de `[-1,1]`, sin truncamiento. |
| Aesthetics | CUDA/BF16 | Cuatro ejes finitos: CE, CU, PC y PQ. |
| Beats | CPU | 120,000000 BPM y 61 beats, dentro de la tolerancia original de ±2 BPM. |

Las cuatro pruebas verificaron terminal `done` único, hijo distinto del padre y `/v1/unload` HTTP 200 seguido de hijo terminado. Cargas y resultados constan en el [resumen QA](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/qa/summary.json). No se publica el texto reconocido.

La [verificación CPU anterior](analysis-cpu-2026-11-06.md) conserva sus 48 pruebas aprobadas y cobertura de 90,58 % de sentencias y 81,69 % de ramas. Es una corrida independiente; esas cifras no se combinan con el batch GPU.

## Procedencia y aislamiento

La imagen producto `3923255f1148` se construyó desde el Dockerfile actual y el lock de dependencias. La derivada QA `1de59a66fa52` sólo añadió directorios y permisos. Los 49 archivos de fuentes y dependencias coincidieron entre imagen, checkout y snapshot CPU antes y después.

El [preflight de runtime](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/qa/raw/preflight-runtime.json) verificó cinco modelos seguros contra revisiones, tamaños y SHA-256 del lock antes de cargar CUDA. No hubo descargas de modelos ni cambios de producto. Un error de importación del harness se corrigió mediante `PYTHONPATH` antes de cargar modelos; no se repitió el batch.

Se utilizó el contenedor de Compose con un override QA y la suite original `uv run pytest -m gpu`, ejecutada mediante `docker exec` tras preparar sus datos. El [argv exacto](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/qa/command.json) conserva esa equivalencia. Se solicitó una GPU NVIDIA, sin red ni puertos publicados. Modelos, fixture y harness fueron de lectura; las salidas usaron almacenamiento Linux efímero, sin bases de datos ni datos vivos montados.

## Memoria, limpieza y alcance

VRAM del host: 1.364 MiB en el preflight, 1.309 MiB al comenzar el monitor y máximo 6.226 MiB. La última muestra fue 1.349 MiB; tras retirar QA se midieron 1.305 MiB. Una lectura posterior del orquestador dio 1.290 MiB. La carga fría de ASR observada tardó 73,37 s; no se aisló su causa.

No se observaron OOM ni límites excedidos. **No se certifica `spilled:false`**: el observador no retuvo ese campo terminal y los contadores globales de Windows no atribuyen paginación CUDA de WSL. La instrumentación añade sobrecarga; sus tiempos no son un benchmark de ACE-Step ni completan T-09.

El [recibo de limpieza](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/qa/cleanup.json) acredita contenedor retirado, ningún volumen QA creado y tres servicios demo conservados. Ollama permaneció vacío, como al inicio; no hubo un modelo previo que restaurar.

## Cierre técnico

Revisión A/B de cuatro documentos, intento 1: sin hallazgos; ambas contrastaron JUnit, fuentes, cargas/descargas y métricas. Alcance sin exclusiones ni avisos; C/D no activadas. Se aplicó el proceso ligero de ADR-0089: detalle en los informes y resumen en el ledger, sin recibos crudos en Git. [Revisión](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/review-1-final/verdicts.md).

QA final `PASS_T08_CPU_GPU_EVIDENCE_AND_DOCS`: cuatro documentos coinciden con revisión; fuentes 21/49 y 71 archivos ajenos intactos, enlaces válidos, ledger sin incoherencias. No se repitieron suites ni GPU. [Informe final](../../../../.cache/dev-cycle/20261106-m0-t08/gpu/qa/final-docs/report.md).

El orquestador acepta el cierre técnico de T-08. El estado actual pertenece al [ledger canónico](../tasks.md). La rama está apilada sobre la entrega T-16 aún abierta; su integración queda pendiente de esa tarea. M0 y M1 siguen abiertos; escucha y decisión musical corresponden a sus tareas de aceptación. Claude CLI continúa pendiente del cierre real de M1.
