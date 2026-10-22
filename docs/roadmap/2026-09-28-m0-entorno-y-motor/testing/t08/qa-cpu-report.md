# Informe de QA — T-08, verificación CPU independiente

| Campo | Resultado |
|---|---|
| Fecha | 2026-10-06 |
| Estado CPU | VERDE: 45/45 tests CPU, beats real 1/1 y checks declarados exit 0 |
| Estado global T-08 | PENDIENTE: tres inferencias GPU no ejecutadas; criterios y ledger sin cerrar |
| URL auditada | No aplica, backend sin UI; no se abrió ni probó una URL |
| Imagen final | `sha256:306e3b0fbc1170ee066e2aed099ef6638ea7dad7faf3ab5b67edfa90e64b70c9` |
| Plan | [improvement-plan.md](../../improvement-plan.md) · [T-08](../../tasks.md) |

## Veredicto y puertas

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). `ledger-lint.py` exit 0: 0 incoherencias, 7 avisos de Changelog. `coverage-check.py` exit 0 reconoce el marcador; la puerta de cobertura E2E NO se ejecuta. No se presenta como cobertura OK. `qa-gate.py`: n/a, sin E2E ni results.json Playwright; no se fabricó reporter ni JSON de qa-gate.

Salida literal de coverage-check:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Se listan T-00–T-19, no exigidas por esta puerta: no hay criterios [GWT] rastreables. No aparecen rutas UI ni degradación de comprobación del diff. Logs [ledger](../../../../../.cache/dev-cycle/t08/qa/ledger.log) y [coverage-check](../../../../../.cache/dev-cycle/t08/qa/coverage-check.log).

## Resultados automáticos CPU

| Comprobación ejecutada propia | Resultado | Evidencia |
|---|---|---|
| Suite CPU dentro de imagen final | 45 passed, 4 deselected, 1 aviso, 15,43 s, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/cpu.log), [JUnit](../../../../../.cache/dev-cycle/t08/qa/cpu.xml) |
| Beats con safetensors locales, CPU real | 1 passed, 3 deselected, 120 BPM ±2, 61 beats, unload del hijo, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/beats.log), [JUnit](../../../../../.cache/dev-cycle/t08/qa/beats.xml) |
| Factoría/preflight antes de importar torch | PARENT_TORCH=False; CUDA_INITIALIZED=False, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/imports.log) |
| Exportación de contratos | engine-v1.json up to date, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/contracts.log) |
| Ejemplos de manifiesto | all valid (4 manifests), exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/examples.log) |
| AST anti-pickle del proyecto | 8 passed, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/ast.log) |
| Ruff alcance analysis | All checks passed, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/ruff.log) |
| Formato alcance analysis | 15 files already formatted, exit 0 | [log](../../../../../.cache/dev-cycle/t08/qa/format.log) |
| Integridad antes/después | 20 fuentes + 36 evidencias, todas SHA-256 idénticas | [antes](../../../../../.cache/dev-cycle/t08/qa/freeze-before.json), [después](../../../../../.cache/dev-cycle/t08/qa/freeze-after.json) |
| Enlaces de documentos muestreados | 5 documentos, 37 destinos locales existen; anclas no comprobadas | [JSON](../../../../../.cache/dev-cycle/t08/qa/links.json) |
| Imágenes históricas | 37e935536f52 y 80eee31d9121 conservan sus IDs | [original](../../../../../.cache/dev-cycle/t08/qa/historical-original.log), [fix1](../../../../../.cache/dev-cycle/t08/qa/historical-fix1.log) |

Cobertura oficial de producción nueva completa `engine_analysis`: **346/382 = 90,5759 %**, 36 líneas ausentes, ninguna excluida, umbral 80 % pasado. No se rebajó el umbral ni excluyeron tests adicionales. Mínimos por archivo:

| Archivo | Cubiertas/total | % exacto |
|---|---|---|
| `engine_analysis/__init__.py` | 5/5 | 100.0000 |
| `engine_analysis/adapter.py` | 74/82 | 90.2439 |
| `engine_analysis/backend.py` | 185/208 | 88.9423 |
| `engine_analysis/descriptor.py` | 41/41 | 100.0000 |
| `engine_analysis/safety.py` | 32/36 | 88.8889 |
| `engine_analysis/server.py` | 9/10 | 90.0000 |

[JSON oficial](../../../../../.cache/dev-cycle/t08/qa/coverage.json) · [XML oficial](../../../../../.cache/dev-cycle/t08/qa/coverage.xml). E2E: n/a; capa unitaria de este alcance: 90,58 %. No se repitió coverage-gate del workspace ni la suite completa ajena: el gate oficial pytest-cov midió exclusivamente toda la producción nueva T-08.

Los casos CPU incluyen salida JSON cruda, residencia secuencial, rechazo de entradas, worker/API real en memoria, segmentación 450/600 s a 16/22,05 kHz, silencios, idiomas mixtos, límites180 s de align_lyrics y offsets globales posteriores a399,92 s. ForcedAligner.align y parse_timestamp upstream reales se ejercitan con processor/logits dobles CPU; CLAP usa processor/tokenizer reales sin inferencia con pesos. Esto acredita transporte, rango y clasificación, no precisión ASR/alineación, similitud real ni calidad musical. La ausencia de escritura de BD fue comprobada por AST/tests y revisión3, no por integración con una BD real.

## Comandos y aislamiento

Host: `. ./scripts/env.ps1`, `uv run --frozen scripts/export_contracts.py --check`, `uv run --frozen scripts/verify_manifest.py packages/contracts/examples/`, `uv run --frozen pytest tests/test_no_pickle.py -q -o cache_dir=.cache/dev-cycle/t08/qa/host-pytest-cache --basetemp=.cache/dev-cycle/t08/qa/host-tmp`, `uv run --frozen ruff check apps/engines/analysis`, `uv run --frozen ruff format --check apps/engines/analysis`. Scripts plugin ledger/coverage-check ejecutados con Python gestionado por uv. No torch host ni instalaciones.

Suite: `docker run --rm --network none -e CUDA_VISIBLE_DEVICES= -e STUDIO_ENGINE_TOKEN=<token temporal> -e STUDIO_TEST_TMP_DIR=/evidence/tmp -e COVERAGE_FILE=/evidence/.coverage -v <raíz>/models:/models:ro -v <qa>:/evidence music-studio/engine-analysis:m0-t08-fix2 uv run pytest tests -m 'not gpu' --cov=engine_analysis --cov-report=term-missing --cov-report=json:/evidence/coverage.json --cov-report=xml:/evidence/coverage.xml --cov-fail-under=80 --junitxml=/evidence/cpu.xml --basetemp=/evidence/tmp -o cache_dir=/evidence/pytest-cache -q`.

Beats: la misma imagen/red/CUDA/token y models readonly, montando `<qa>/data:/data`; `uv run pytest tests/test_gpu.py -k beats --junitxml=/evidence/beats.xml --basetemp=/evidence/beat-tmp -o cache_dir=/evidence/beat-pytest-cache -q -s`. Es un test marcado gpu por convención del hito, ejecutado físicamente en CPU. No se usó `--gpus`. Writes sólo dentro de QA privado.

Imports: mismo aislamiento, `PYTHONPATH=/studio/apps/engines/analysis`, `uv run python /evidence/import_probe.py`. Primer intento con PYTHONPATH incorrecto `/opt/analysis` falló con ModuleNotFoundError; conservado en [log](../../../../../.cache/dev-cycle/t08/qa/imports-path-failed.log), corregido sin editar producto. No es fallo de producto ni RED TDD. El único aviso de suite/beats es la deprecación Starlette/anyio BlockingPortal.

No se repitió build: evidencia previa congelada [fix2-report](fix2-report.md) y [recibo](fix2-delivery-receipt.json), leída y verificada por hashes, no nueva ejecución. ADR-0031/README/contrato fueron muestreados para coherencia y enlaces; [review-3](review-3.md) acredita tres lentes sin gaps, como evidencia previa separada. El montaje offline y CUDA oculto respetan local por defecto, pesos seguros, padre sin torch y residencia secuencial de CONSTITUTION §2/§4; el aislamiento network none sólo aplica a estos contenedores efímeros de test, no modifica Compose/puertos.

## Checklist pendiente y trazabilidad

No existen bloques M-xx/UI que trasladar a manual. Pendientes de T-08:

- [ ] Inferencia GPU real de transcripción con texto/timestamps y residencia ASR→alineador.
- [ ] Inferencia GPU real CLAP con puntuación finita y sin truncamiento oculto.
- [ ] Inferencia GPU real Audiobox con cuatro ejes finitos y descarga real de VRAM.

T-08: CPU conforme, GPU pendiente; align_lyrics completa sigue para M3. Ninguna calidad artística ni WER se acredita aquí. No se cerraron criterios, plan/spec ni ledger, no hubo handoff documenter, Jira/Confluence ni cambios de fuentes.

PDF pendiente: se leyó custom-agents:to-pdf y se comprobaron cachés usuario/proyecto; dependencias ausentes. No se instaló ni descargó Chromium por autorización de alcance CPU. Sólo se entrega Markdown + recibo, limitación explícita.
