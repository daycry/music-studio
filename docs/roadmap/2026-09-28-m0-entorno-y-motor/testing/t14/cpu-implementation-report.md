# T-14: recibo CPU sanitizado

Alcance: parámetro opcional `shift` finito 1–5, descriptor/adaptador/CLI. No se modifica el contrato genérico, `required`, indicadores `verified` ni defaults globales. La omisión no añade `shift` y mantiene el default upstream 1. El override `--brief SYNTH --shift 3` funciona sin conflicto; el catálogo no recibe defaults nuevos.

## TDD: RED real previo (2026-10-05)

Todos los comandos de pytest se ejecutaron con `uv run --no-sync --all-packages` después de cargar `scripts/env.ps1`.

- RED: apps/engines/acestep/tests/test_shift.py::test_descriptor_shift_optional falló con `KeyError: 'shift'` · 2026-10-05. Resultado: `1 failed, 2 warnings in 0.14s`.
- RED: apps/engines/acestep/tests/test_shift.py::test_adapter_propagates_shift falló con `KeyError: 'shift'` para 1/3/5/2.5 · 2026-10-05. Resultado: `4 failed, 2 warnings in 0.28s`.
- RED: apps/engines/acestep/tests/test_shift.py::test_adapter_rejects_invalid_shift falló con `DID NOT RAISE EngineError` para 0/6/nan/inf/-inf/True/string/null · 2026-10-05. Resultado: `8 failed, 2 warnings in 0.28s`.
- RED: apps/engines/acestep/tests/test_shift.py::test_shift_reaches_generation_params falló con `EngineError: INTERNAL`, porque el GenerationParams simulado carecía de `shift` al entrar en generate_music · 2026-10-05. Resultado: `1 failed, 2 warnings in 0.27s`.
- RED: tests/test_generate_shift.py::test_direct_shift falló con `SystemExit: 2`, `unrecognized arguments: --shift` · 2026-10-05. Resultado: `4 failed in 0.50s`.
- RED: tests/test_generate_shift.py::test_brief_shift_override falló con `SystemExit: 2`, `unrecognized arguments: --shift 3` · 2026-10-05. Resultado: `1 failed, 2 warnings in 0.39s`.
- RED: tests/test_generate_shift.py::test_invalid_shift_rejected_before_enqueue falló con ausencia de ValueError para entradas finitas inválidas; nan/inf/-inf devolvían error del serializer en vez de INVALID_PARAMS · 2026-10-05. Resultado: `8 failed, 1 warning in 0.49s`.

La conservación del parámetro explícito en el manifiesto usa la publicación/validación existente, sin cambio de producto adicional: test nuevo verde a la primera, no contabilizado como RED nuevo. La omisión también conserva un comportamiento preexistente.

## GREEN y verificación

Comando exacto del brief:

```text
uv run --no-sync --all-packages pytest tests/test_generate_shift.py apps/engines/acestep/tests/test_shift.py -q
...................................                                      [100%]
35 passed in 0.40s
```

Suite vecina y cobertura tras formato:

```text
uv run --no-sync --all-packages pytest tests/test_generate.py tests/test_generate_shift.py apps/engines/acestep/tests/test_adapter.py apps/engines/acestep/tests/test_review_fixes.py apps/engines/acestep/tests/test_shift.py -q --cov=scripts --cov=adapter --cov=descriptor --cov-report=json:.cache/dev-cycle/t14/implementation/coverage.json --cov-report=
149 passed, 1 skipped, 6 warnings in 7.41s
```

Recibo de cobertura: `.cache/dev-cycle/t14/implementation/coverage.json`. Medición real por archivo (statement coverage):

| Archivo | Ejecutadas/total | Cobertura |
|---|---:|---:|
| apps/engines/acestep/adapter.py | 155/173 | 90% |
| apps/engines/acestep/descriptor.py | 30/30 | 100% |
| scripts/generate.py | 319/339 | 94% |
| Total | 504/542 | 93% |

Ruff check sobre los cinco archivos: `All checks passed!`. Ruff format --check: `5 files already formatted`.

Casos: límites 1/5 y float 2.5, 3, omisión compatible, override del brief, cero/seis/nonfinite/bool/string/null rechazados en adapter y CLI programático, valor explícito transmitido en POST y manifest.request.params, GenerationParams simulado recibe 3. No se importó torch ni ejecutó GPU.

Advertencias: cinco deprecations de Starlette TestClient ya presentes y una de caché pytest Windows/ACL; no fallos. Un test de upstream en contenedor quedó skipped porque este entorno CPU no es la imagen del engine. GPU/audio/custodia y cierre completo de T-14 corresponden al orquestador.

Archivos editados: apps/engines/acestep/adapter.py, apps/engines/acestep/descriptor.py, apps/engines/acestep/tests/test_shift.py, scripts/generate.py, tests/test_generate_shift.py. El ledger, Git, modelos y documentos de producto no se tocaron.

DONE (alcance CPU)
