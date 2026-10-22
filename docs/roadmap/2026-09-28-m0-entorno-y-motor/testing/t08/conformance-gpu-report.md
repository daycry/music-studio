# T-08 — Verificación GPU canónica de la imagen final

2026-10-06. **Cuatro pruebas reales verdes**, cero fallos/errores/skips, exit 0. Pytest 174.94 s; launcher 177.69 s de reloj. [Recibo](conformance-gpu-receipt.json).

Se ejecutó `docker compose run --rm --no-deps --name music-studio-t08-conformance-gpu-20261006a --label music-studio.diagnostic.owner=t08-conformance-gpu-20261006a engine-analysis uv run pytest -m gpu -q --junitxml=/data/tmp/t08-conformance-gpu-20261006a/gpu.xml`. Los parámetros de nombre/owner/JUnit no cambian el conjunto declarado `-m gpu`. Fixture por `STUDIO_ANALYSIS_TEST_AUDIO` y token por entorno; imagen final `d20ae562…`, sin rebuild ni cambio de fuentes.

| Tarea | Evidencia real |
|---|---|
| audio.transcribe | ASR seguido de ForcedAligner; texto no vacío y 87 palabras con tiempos válidos. Autodetección English; precisión/idioma pendientes de contraste. |
| audio.clap | Score coseno finito entre -1 y 1; text_truncated=false. |
| audio.aesthetics | Cuatro ejes CE/CU/PC/PQ finitos. No se interpretan como una aprobación musical. |
| audio.beats | Beat_this en CPU sobre clic sintético 120 BPM; resultado 120.000000, tolerancia ±2 BPM acreditada. |

Cada prueba real comprueba hijo vivo con PID distinto y `unload` que lo termina. Root corroboró los cuatro casos JUnit, cuatro salidas crudas y sus SHA, 22 fuentes congeladas e identidad final de imagen. Salidas en `data/tmp/` y logs privados bajo `.cache/dev-cycle/t08/conformance-gpu-20261006a/`. No se publican transcripción ni letras.

Baseline 1314 MiB, Ollama vacío y engine externo8101 idle/unloaded. Contenedor propio retirado; GPU posterior1314 MiB. No se detuvieron servicios ni restauró un modelo que no estaba cargado. No hay medición de pico/spill de esta suite: ambos campos null.

La construcción final ya estaba ejecutada y revisada en la corrección de caché; no se repite sin cambios. Las 48 pruebas CPU y revisión fresca A+B+C+D del delta siguen acreditadas por separado. Pendiente cotejo independiente de integración y cierre de tarea conforme al ledger; M0, capacidades/fidelidad/calidad musical continúan abiertos.
