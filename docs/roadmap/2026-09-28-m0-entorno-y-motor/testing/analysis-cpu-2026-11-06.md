# Verificación CPU del engine de análisis — M0/T-08

Última actualización: 2026-11-06.

**La verificación CPU pasó; al cerrar esta fase T-08 continuaba `en-revision`.** La corrida completa obtuvo **48 pruebas aprobadas, 0 fallidas, 0 omitidas y 4 deseleccionadas**, en **20,43 s**, dentro de Docker sin acceso GPU. Un suplemento independiente aprobó una prueba real de beats CPU. Son dos ejecuciones separadas: sus resultados y cobertura no se agregan como una suite única.

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

Al cerrar esta fase quedaban pendientes las tres pruebas GPU reales de transcripción, CLAP y Aesthetics y residencia/descarga GPU. El batch GPU posterior se documenta en [su informe separado](analysis-gpu-2026-11-06.md). La aceptación musical y la selección del modelo pertenecen a las puertas restantes del proyecto. Este resultado CPU, por sí solo, no cierra T-08, M0 ni M1 ni aprueba calidad musical general.

## Revisión y cierre documental de la fase CPU

Revisión A/B, intento 1: tres Markdown desde `f7d7c39`; alcance sin exclusiones ni avisos, C/D no activadas. Cero hallazgos. Ambas lentes contrastaron fuentes, logs y JUnit sin repetir suites. A comprobó cobertura, tres SHA y siete enlaces; B verificó la cadena test original→backend predeterminado→safetensors CPU→inferencia y descarga.

| Criterio | A | B |
|---|---|---|
| Alcance documental y fuentes intactas | ✓ | Sin defectos |
| Rojo inicial y reparación exclusiva del harness | ✓ | ✓ |
| Cobertura y ejecuciones separadas | ✓ | ✓ |
| Beats real CPU, hijo separado y descarga | ✓ | ✓ |
| Constitución, estado y límites honestos | ✓ | Sin defectos |

QA documental final: `PASS_CPU_EVIDENCE_AND_DOCS_ONLY`; tres documentos coinciden con revisión, siete enlaces resueltos, fuentes 21/49 y 71 archivos ajenos intactos. Ledger: 0 incoherencias y 25 avisos históricos. Los [recibos de revisión](../../../../.cache/dev-cycle/20261106-m0-t08/review-1/verdicts.md) y [QA documental](../../../../.cache/dev-cycle/20261106-m0-t08/qa/final-docs/report.md) conservan el detalle. Este cierre CPU se publicó antes de ejecutar GPU.
