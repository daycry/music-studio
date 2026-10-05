# T-06 — fix2: causa raíz del rechazo previo de VRAM

Fecha: 2026-10-05. Despacho bajo `custom-agents:debug-root-cause`, ejecución manual del SKILL.md en el plugin Codex 1.21.1. Informes anteriores conservados intactos. Este recibo no actualiza ledger ni afirma generación GPU.

## Fase 1 — reproducción mínima

Fuente real del commit upstream `dce621408bee8c31b4fcf4811682eb9359e1bc94`: `acestep/core/generation/handler/generate_music.py`, SHA-256 `4126b89bea9032d5ad1a5d9f906410ef4ede79a1d2328635aa365010473ee086`. `GenerateMusicMixin._vram_preflight_check` empieza en línea 105, produce la frase en línea 166 y retorna `success=False`, `error` y `status_message` en líneas 172–178. El test verifica el hash y extrae el método mediante AST; no importa torch/modelos ni ejecuta cálculos GPU. Las constantes de presupuesto se extraen por `ast.literal_eval` de gpu_config.py; sólo se controlan disponibilidad/dispositivo/VRAM libre para ejercitar el método real.

RED: `test_real_preflight_failure_classified_vram[1-30]`, `[2-120]` y `test_preflight_isolation_and_equivalent_statuses` fallaron con INTERNAL frente a VRAM_EXCEEDED · 2026-10-05. Comando: `. ./scripts/env.ps1; uv run --frozen --all-packages pytest apps/engines/acestep/tests/test_preflight_vram.py -q --tb=short -o cache_dir=.cache/pytest/cache`, exit 1: 3 failed. Recibo `raw/fix2/red-preflight.log`. Dos avisos de cache ACL de Windows no originan el fallo de los asserts; la suite posterior usa `-p no:cacheprovider`.

## Fase 2 — aislamiento y descartes

El método real devuelve `Insufficient free VRAM: need ~0.8 GB, only 0.1 GB available...` con CFG=1, batch=1 y duración=30. La cifra depende de las constantes y CFG; el defecto de clasificación es el mismo que la reproducción del revisor con ~1.1 GB. El test integra ese resultado real en `AceStepAdapter.generate` y demuestra error contractual incorrecto antes de escribir WAV.

Descartes probados: con 8 GB libres el método retorna None; con CUDA no disponible retorna None; con offload_to_cpu retorna None. Por tanto el fallo se localiza después del rechazo real del preflight y antes de escritura de artefactos, en `upstream_error`, no en carga, semillas, cálculo de presupuesto, GPU, conversión WAV ni contrato. El predicado de dispositivo existente resulta verdadero; el predicado de motivo resulta falso.

Se buscaron los retornos/textos de memoria en handler, inference.py, llm_inference.py y gpu_config.py, y se amplió lectura a los .py upstream salvo tests/third_parts/training/UI. Única frase de insuficiencia equivalente adicional: llm_inference.py:737, `vLLM disabled due to insufficient free VRAM`, aviso que inicia fallback a PT y no retorno de fracaso; adapter fuerza backend PT. gpu_config.py:1339/1371 producen avisos de duración/batch que se limitan, no rechazos por VRAM libre. No se amplió la clasificación a cualquier `exceeds`/`insufficient`. Recibo `raw/fix2/relevant-status-search.log`.

## Fase 3 — hipótesis probada antes de editar producción

Hipótesis falsable: «El adapter produce INTERNAL porque su lista de causas sólo reconoce OOM/presupuesto excedido/asignación fallida; el rechazo previo usa la frase `Insufficient free VRAM` y no contiene ninguno de esos motivos».

Prueba CPU previa al cambio, exit 0 (`raw/fix2/hypothesis-before-fix.log`):

```text
device predicate: True
current reason predicate: False
proposed exact predicate: True
Hypothesis confirmed: classifier misses preflight phrase; sufficient VRAM, CPU and offload paths excluded
```

Comando exacto:

```powershell
. ./scripts/env.ps1; uv run --frozen --all-packages python -c "import sys, runpy; sys.path.insert(0,'apps/engines/acestep'); ns=runpy.run_path('apps/engines/acestep/tests/test_preflight_vram.py'); import adapter; p=ns['real_preflight']; result=p(0.1)(1,30); text=result['error'].casefold(); print(result); print('device predicate:', any(s in text for s in ('cuda','gpu','vram'))); print('current reason predicate:', any(s in text for s in ('out of memory','outofmemoryerror','budget exceeded','memory allocation failed'))); print('proposed exact predicate:', 'insufficient free vram' in text); assert adapter.upstream_error('generación',result['error']).code == 'INTERNAL'; assert p(8)(1,30) is None and p(0.1,cuda=False)(1,30) is None and p(0.1,offload=True)(1,30) is None; print('Hypothesis confirmed: classifier misses preflight phrase; sufficient VRAM, CPU and offload paths excluded')"
```

## Fase 4 — fix mínimo y regresión

Diff de producción limitado a una entrada en la lista de motivos de `adapter.upstream_error`: `insufficient free vram`. Conserva el requisito CUDA/GPU/VRAM y toda clasificación/mensajería de fix1. No toca semillas ni carga. La suite ahora conserva la reproducción upstream AST/hash para dos combinaciones batch/duración y prueba las dos representaciones reales (`error` y `Error: ...` en status_message). Comprueba VRAM_EXCEEDED con mensaje constante `VRAM insuficiente durante generación`, sin paths/tokens ni artefactos; insuficiencia de memoria CPU conserva INTERNAL y `Fallo interno durante generación`.

GREEN host final: `. ./scripts/env.ps1; uv run --frozen --all-packages pytest apps/engines/acestep/tests -m "not gpu" -q --tb=short -p no:cacheprovider`, 53 passed, 5 skipped de entorno/contenedor, 1 deselected GPU. Ruff check y format --check verdes: 11 archivos ya formateados. Recibo `raw/fix2/host-final.log`. El primer check de lint detectó UP006 en un namespace de test y se corrigió a dict antes del build final; no afectó a producción.

Candidato de gotcha, sin aprobar/publicar ni modificar journals: `fix2-knowledge-candidate.md`. Cruza el umbral de conocimiento por ciclo de depuración y garantía CA-05 afectada. Root decide su propuesta formal.

## Terminación de imagen y GREEN final

Build `docker compose --profile engines build engine-acestep`, exit 0: export 170,7 s, unpack 67,7 s. Tag `music-studio/engine-acestep:m0-t05`. Imagen/config ID `sha256:ecae5c354e3ec7350e1a6a6fc0118c8f3faf5ff4dc976a83e1444e82f3cd95b3`; manifiesto `sha256:f98f9bd4990a33069d04c8bc9a890994a8eae0407ee0ed23b4eca2980e620be4`; índice `sha256:10cd807439dacf561306cde2270c00984c66e2ebbc275babee2741da9b8c8ccb`. `raw/fix2/build-final.log` conserva terminación, hashes y exit; un segmento intermedio de listado de paquetes fue truncado por la herramienta y se indica expresamente.

Verificación contractual CPU exacta: `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q`, exit 0: **58 passed, 1 deselected, 5 warnings in 13.51s**. Recibo `raw/fix2/container-cpu-final.log`. La prueba GPU fue excluida; las cinco deprecaciones proceden de torchao/Starlette upstream.

Cobertura final Python 3.11.14: `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q --cov=adapter --cov=patches --cov=descriptor --cov=engine_acestep --cov-report=term-missing --cov-fail-under=80`, exit 0: **58 passed, 1 deselected, 5 warnings in 14.73s**. **92,96 %** total (270 sentencias, 19 sin cubrir); adapter 89 %, patches 98 %, descriptor y factoría 100 %. Recibo `raw/fix2/container-coverage-final.log`. Ningún caso rojo pendiente. Las regresiones B1/B2 de fix1 siguen verdes dentro de esta suite.

Estado de este despacho: **DONE_WITH_CONCERNS**. Fuentes estables para revisión intento 3. Root ejecutará posteriormente la prueba GPU de 30 s autorizada con ocupación/cap actuales; este agente no la ha ejecutado. No se acredita aún generación real ni medidas de tiempo/VRAM. Informes originales, Git, ledger, documentación/root y journals conservados.
