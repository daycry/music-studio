# Verificación CPU del engine de análisis — M0/T-08

Última actualización: 2026-11-06.

**La verificación CPU pasa; T-08 continúa `en-revision`.** La corrida completa obtuvo **48 pruebas aprobadas, 0 fallidas, 0 omitidas y 4 deseleccionadas**, en **20,43 s**, dentro de Docker sin acceso GPU. Un suplemento independiente aprobó una prueba real de beats CPU. Son dos ejecuciones separadas: sus resultados y cobertura no se agregan como una suite única.

## Corrida completa y corrección del entorno

La primera ejecución terminó con **39 aprobadas y 9 fallidas** porque el entorno QA omitió `/models/models.lock.json`. Los nueve fallos correspondían a ese recurso ausente. Se conservan íntegros el [informe inicial](../../../../.cache/dev-cycle/20261106-m0-t08/qa/run1-report.md) y sus artefactos.

La corrección afectó exclusivamente al harness: copiar el lock sin modificarlo y comprobar su SHA-256 y los recursos CLAP antes y después. Se repitió la suite completa con las mismas fuentes, dependencias, argumentos e imagen; no hubo cambios de producto ni instalaciones. Véanse el [informe QA](../../../../.cache/dev-cycle/20261106-m0-t08/qa/report.md) y el [resumen de la segunda corrida](../../../../.cache/dev-cycle/20261106-m0-t08/qa/run2/summary.json).

Se verificaron el procesador y el prefijo CLAP reales en CPU/BF16, segmentos con Torch real y el padre HTTP libre de Torch. Esto no acredita inferencia GPU de ASR, CLAP o Aesthetics.

La cobertura oficial de `engine_analysis` fue:

| Medida | Resultado |
|---|---:|
| Sentencias | 346/382 — 90,58 % |
| Ramas | 116/142 — 81,69 % |
| Combinada | 88,17 % |

Es cobertura del directorio, sin exclusiones nuevas. No representa cobertura diferencial ni incluye el suplemento beats. Fuente: [JSON de cobertura](../../../../.cache/dev-cycle/20261106-m0-t08/qa/run2/coverage.json).

## Suplemento real de beats CPU

El test original `tests/test_gpu.py::test_beats_cpu_returns_120_bpm_with_two_bpm_tolerance`, agrupado bajo la marca GPU pero ejecutado íntegramente en CPU, pasó **una vez en 4,79 s**. Sobre un clic sintético de 30 segundos obtuvo **120,000000 BPM y 61 beats**.

Se utilizó el safetensor existente de **81.031.368 bytes**, verificado por SHA-256 en host y contenedor antes y después; no hubo descargas. El test comprobó terminación `done`, proceso hijo distinto del padre y `/v1/unload` HTTP 200 seguido de hijo terminado. La instrumentación exclusiva del suplemento registró **cero intentos CUDA y `cuda_initialized=false`**, también al terminar el hijo. Véanse [informe](../../../../.cache/dev-cycle/20261106-m0-t08/qa/beats-cpu/report.md), [resumen](../../../../.cache/dev-cycle/20261106-m0-t08/qa/beats-cpu/summary.json) y [seguridad](../../../../.cache/dev-cycle/20261106-m0-t08/qa/beats-cpu/safety-summary.json).

## Aislamiento, integridad y límites

Ambas ejecuciones usaron `runc`, red desactivada, sin dispositivos GPU ni puertos publicados, UID 10001 y capacidades retiradas. El suplemento montó únicamente el peso en lectura; generó su audio en almacenamiento temporal QA. Permanecieron intactos **21 archivos analysis, 49 del snapshot y 71 ajenos**. Los overlays copiaron fuentes actuales sin instalar dependencias. Los contenedores QA fueron retirados y las imágenes conservadas.

Ruff pasó y ledger-lint informó **0 incoherencias y 25 avisos**. El alcance carece de UI; no se ejecutaron Playwright ni aceptación visual.

Quedan pendientes las tres pruebas GPU reales de transcripción, CLAP y Aesthetics y residencia/descarga GPU. El batch GPU completo aún no se ha ejecutado. La aceptación musical y la selección del modelo pertenecen a las puertas restantes del proyecto. Este resultado no cierra T-08, M0 ni M1, ni aprueba calidad musical general.
