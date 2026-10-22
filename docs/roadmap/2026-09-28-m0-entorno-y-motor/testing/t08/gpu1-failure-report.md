# T-08 — primera verificación GPU: dos fallos

2026-10-06. [Recibo](gpu1-failure-receipt.json). Revisión3 y [QA CPU independiente](qa-cpu-report.md) conformes; no acreditan la ejecución con pesos. Se ejecutó la Verificación real de T08 en imagen306e3b0 y fixture privada30s, sin letra esperada ni cambios de fuentes.

`docker compose run --rm --no-deps --name <contenedor propio> -e STUDIO_ANALYSIS_TEST_AUDIO=<fixture privada> engine-analysis uv run pytest tests/test_gpu.py -m gpu -q --junitxml=<salida privada> -o cache_dir=/tmp/pytest-cache` → exec80352 **terminalexit1**,2failed/2passed/1aviso132,62s.

Transcripción Qwen y CLAP fallan con evento terminalerror; pytest resume el diccionario y no conserva una causa nativa identificable. Estética Audiobox con GPU y clicbeatsCPU pasan, incluidas sus comprobaciones de resultado, proceso hijo y unload. No se atribuye el fallo a OOM, dtype, modelo o instrucciones sin prueba causal.

Baseline1315MiB/Ollama vacío, dentro≤1600. Durante el proceso se observó5218MiB, muestra que no es pico. Al terminar se comprobó contenedorpropio--rm ausente y GPU1315MiB; servicio8101 anterior preservado. No había modelo Ollama que restaurar. El adaptador conserva el cap dinámico/margen, pero no se presenta esta observación como medición de spill ni WER/calidad.

La tarea vuelve a en-progreso para debug-root-cause fases1–3 y corrección con RED previo cuando la causa esté probada. Nueva fase de integraciónGPU, conservando revisión3/CPU anteriores como antecedentes, sin ocultar el rojo ni cerrar ningúnCA. Worker fresco diagnose_t08_gpu1 sóloCPU/caché propia; producto congelado y rawdatos privados. T16diagnóstico se ejecutará separado, nunca modelosGPU simultáneos.
