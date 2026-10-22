# T-08 — QA independiente de la caché ASR

2026-10-06. **48 pruebas CPU verdes**, cuatro pruebas GPU excluidas, cero fallos y una advertencia de deprecación de Starlette; 15,97 s. QA fresca independiente de la implementación y las cuatro lentes de revisión. [Recibo de QA](asr-cache-qa-receipt.json).

La imagen inmutable `sha256:d20ae562803cb577c290f0229c0df07551a20647be92feca3d678f523b300c62` ejecuta `FileCacheManager` real con UID 10001, ruta predeterminada `/studio/.cache/triton`, propietario 10001 y permisos 0755. Escribe y lee la caché sin overrides ni CUDA inicializada. Las regresiones de CLAP con Conv2d real también pasan; no se cargaron pesos completos ni se atribuye calidad musical a esas pruebas.

El orquestador corroboró el JUnit de 48 pruebas, 22 fuentes, 39 evidencias previas, tres baselines, 41 artefactos sellados de QA y los 19 SHA del probe de imagen. Los snapshots anteriores y posteriores son idénticos. Ruff, formato y Compose dan exit 0. La lectura final de Compose usa `--no-interpolate`.

Incidencia: el primer probe de Compose interpoló el token interno en una salida privada de herramienta. El log conservado está redactado y el helper está corregido. Root verificó los 42 archivos propios de QA en memoria contra el valor real: cero coincidencias. El valor no se copia a informes públicos. La salida histórica de herramienta no puede retirarse desde este flujo. No se modificaron token, servicios ni configuración.

Evidencias privadas: `.cache/dev-cycle/t08/asr-cache-qa/`; el recibo indica rutas y hashes. No se publican los logs privados. Cobertura de configuración y E2E sin UI: n/a; qa-gate y coverage-check no ejecutados. PDF pendiente, sin instalar herramientas.

Esta evidencia permite preparar la siguiente prueba real de transcripción y alineación de 30 segundos. No acredita precisión ASR, memoria GPU ni el cierre de T-08 o M0. Los criterios de la tarea permanecen abiertos.
