# T-16 — implementación CPU reanudada

Fecha: 2026-10-06. Contexto: brief-resumed.md completo y referencias específicas; ampliación autorizada por root únicamente de `_capture_fixture` en test_preflight.py. Rama preparada por root: m0/t-16-libre-sft. No he actualizado ledger, medidores, documentación, Git, pesos, locks ni dependencias.

## Resultado y límites

- Descriptor/factoría distinguen `ace-step-1.5-sft`; adapter acepta únicamente la identidad del checkpoint configurado. `/v1`, `verified=False`, motor por defecto y Turbo conservados.
- Pasos efectivos: Turbo 8 por defecto, enteros 1–8; SFT 50 por defecto, enteros 1–200. CFG SFT 7 por defecto, finito 1–20. CFG explícito rechazado para Turbo. Se rechazan booleanos, nulos, cadenas, fracciones, NaN/infinito y enteros enormes fuera del rango sin HTTP.
- CLI admite ambos flags, incluidos overrides sobre briefs. Sus valores explícitos viajan en preparación, request y manifiesto sin publicar caption/letra/negative_prompt. La CLI valida límites generales antes de preparar/publicar/contactar el engine; el descriptor/checkpoint aplica después el límite específico Turbo/SFT.
- `GenerationParams`, progreso/cancelación con pasos efectivos y preflight planned usan los mismos controles. Worker usa su checkpoint configurado también con requests directos legados sin model_id. Captured acredita los flags de GenerationParams y comprueba ambos controles en la frontera real `dit.generate_music` antes de invocar el handler.
- El validador de recibos liga checkpoint, identidad, petición, effective params y flags capturados. Con tipos estrictos, `True` no acredita un paso/CFG de valor 1. Se conservan recibos Turbo legados sin los nuevos campos opcionales y los presupuestos PT/DiT, metadata/idioma/flags de T-19.
- Pendientes de root: revisión fresca, QA independiente, contratos/build/imagen CPU, documentación/ADR y comparación GPU actualizada (seis tomas nuevas emparejadas, según decisión posterior de root). No se ejecutó GPU, inferencia, descarga ni corpus. No se declara ganador, aprobación artística, tarea/M0 completos.

## Evidencia TDD real

Todos los comandos ejecutados tras `. ./scripts/env.ps1` con `uv run --frozen --all-packages pytest <node> -q -o cache_dir=.cache/dev-cycle/t16/resumed/pytest-cache`; cuando se indicó, `--basetemp=.cache/dev-cycle/t16/resumed/pytest` y/o `--tb=short`. Las fixtures existentes usan temporales locales propios. Cada salida completa está en el fichero enlazado.

| RED (2026-10-06) | Fallo observado | Salida |
|---|---|---|
| apps/engines/acestep/tests/test_inference_controls.py::test_descriptor_sft_identity_and_limits | AssertionError: identidad Turbo frente a SFT | red-identity.txt |
| apps/engines/acestep/tests/test_inference_controls.py::test_adapter_sft_load_identity | MODEL_NOT_FOUND frente a VRAM_EXCEEDED: SFT no reconocido | red-load.txt |
| apps/engines/acestep/tests/test_inference_controls.py::test_effective_defaults | None frente a 8/50 pasos efectivos | red-defaults.txt |
| apps/engines/acestep/tests/test_inference_controls.py::test_direct_invalid_controls | 13 casos: DID NOT RAISE EngineError | red-validation.txt |
| apps/engines/acestep/tests/test_inference_controls.py::test_generation_effective_steps_and_cancellation | INTERNAL frente a CANCELLED, controles no propagados a GenerationParams | red-generation.txt |
| tests/test_generate_inference.py::test_cli_inference_options_and_preparation | SystemExit: flags desconocidos | red-cli.txt |
| tests/test_generate_inference.py::test_programmatic_invalid_before_http | HTTP_BEFORE_VALIDATION / serialización NaN, frente a INVALID_PARAMS | red-cli-direct.txt |
| apps/engines/acestep/tests/test_inference_controls.py::test_native_sft_effective_receipt | 8 frente a 50/35 pasos en planned | red-native.txt |
| tests/test_generate_preparation.py::test_native_receipt_checkpoint_controls | INPUT_RECEIPT_INVALID con controles SFT/Turbo válidos | red-receipt.txt |
| tests/test_generate_preparation.py::test_native_receipt_checkpoint_identity_mismatch | 3 casos: DID NOT RAISE ValueError | red-receipt-identity.txt |
| apps/engines/acestep/tests/test_inference_controls.py::test_dit_boundary_rejects_inference_drift | DID NOT RAISE EngineError, DiT admitía ocho en lugar de cincuenta pasos | red-dit-boundary.txt |
| test_direct_invalid_controls[ace-step-1.5-sft-params13] y test_programmatic_invalid_before_http[params7] | OverflowError con CFG 10**400 | red-huge-guidance.txt |
| tests/test_generate_preparation.py::test_native_receipt_rejects_boolean_control_capture | 2 casos: DID NOT RAISE ValueError, True confundido con 1 | red-capture-bool.txt |

GREEN intermedios: 2 passed identidad/factoría; 52 passed, 1 skipped adapter+controles; 38 passed controles+CLI; 129 passed controles/preflight/preparación; frontera DiT 1 passed; enteros enormes 2 passed; captura bool 2 passed. Los logs green-adapter.txt, green-controls.txt y green-receipts.txt contienen las salidas completas correspondientes.

## Verificación CPU final

```powershell
. ./scripts/env.ps1
uv run --frozen --all-packages pytest tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py -q -o cache_dir=.cache/dev-cycle/t16/resumed/pytest-cache
```

Salida real (declared-cpu.txt): `41 passed in 0.54s`.

```powershell
$env:COVERAGE_FILE='.cache/dev-cycle/t16/resumed/.coverage'
uv run --frozen --all-packages pytest tests/test_generate.py tests/test_generate_preparation.py tests/test_generate_inference.py apps/engines/acestep/tests/test_adapter.py apps/engines/acestep/tests/test_shift.py apps/engines/acestep/tests/test_review_fixes.py apps/engines/acestep/tests/test_preflight.py apps/engines/acestep/tests/test_preflight_vram.py apps/engines/acestep/tests/test_inference_controls.py -q --cov=apps/engines/acestep --cov=scripts --cov=packages/audio-post/audio_post --cov-report=json:.cache/dev-cycle/t16/resumed/coverage.json --cov-report=term-missing -o cache_dir=.cache/dev-cycle/t16/resumed/pytest-cache --tb=short
```

Salida real (coverage-tests.txt): `271 passed, 1 skipped, 5 warnings in 10.55s`; skip de loader real en contenedor no disponible en el host, avisos existentes de TestClient/timeout. No suite global.

Cobertura oficial `pytest-cov` (coverage.json), filtrada con summarize-coverage.py, sin inventar datos: **59/63 = 93,65 %** de líneas ejecutables añadidas/cambiadas; mínimo entre archivos completos propios **88,34 %**. coverage-summary.json recoge numerador/denominador, cada archivo y líneas sin cobertura.

| Producción | Archivo completo | Líneas cambiadas |
|---|---:|---:|
| adapter.py | 92,58 % | 12/13 |
| descriptor.py | 100 % | 4/4 |
| input_profile.py | 100 % | 7/7 |
| preflight.py | 90,48 % | 2/2 |
| manifest.py | 88,34 % | 19/22 |
| generate.py | 93,20 % | 15/15 |

Ruff sobre los 10 Python tocados: `All checks passed!` (ruff.txt). Formato: `10 files already formatted` (format.txt). No regeneración de contratos ni imagen ejecutada por este subagente; corresponde a root/QA.

Incidencias resueltas: primera medición con `--cov=scripts/generate.py` produjo ImportError de NumPy durante colección; se corrigió el objetivo de cobertura a `--cov=scripts`. Una fixture DiT vecina omitía los nuevos controles: se pidió ownership concreto, root lo concedió, y solo se añadieron ambos kwargs en `_capture_fixture`, sin alterar asserts ni relajar validación. Primera reproducción CLI programática usó client=None e intentó conexión local rechazada; se sustituyó por doble Offline, se reejecutó RED antes del cambio de producción y esa salida válida es red-cli-direct.txt.

## Fuente fijada y qué acredita la captura

Upstream auditado: revisión `dce621408bee8c31b4fcf4811682eb9359e1bc94`. `.cache/dev-cycle/t17/upstream-acestep/core/generation/handler/generate_music.py`, SHA-256 `4126b89bea9032d5ad1a5d9f906410ef4ede79a1d2328635aa365010473ee086`, líneas 286–294: Turbo fuerza CFG a 1 **dentro** del handler, tras su frontera de entrada. `inference.py` líneas 832–833 propaga steps/CFG de GenerationParams a la llamada DiT (hash fijado en SOURCE_HASHES `2395a1e6340af075d3f9d2fad293a389beb61f0a11e1db79a5ad120f6d0ce9a2`).

Turbo mantiene el 7 histórico de GenerationParams/planned/captured en la frontera de entrada; esto **no acredita CFG7 en el sampler Turbo**, cuyo valor interno es 1. SFT conserva CFG7 efectivo. Root fue informado y reflejará esta distinción en el ADR/comparación. Estos tests CPU no acreditan naturalidad, comportamiento GPU, telemetría real ni unloading de un modelo cargado.

## Archivos tocados

Producción: apps/engines/acestep/{descriptor.py,adapter.py,preflight.py,input_profile.py}, scripts/generate.py, packages/audio-post/audio_post/manifest.py.

Tests: apps/engines/acestep/tests/test_inference_controls.py, tests/test_generate_inference.py, tests/test_generate_preparation.py, y únicamente `_capture_fixture` en apps/engines/acestep/tests/test_preflight.py.

Evidencia exclusivamente en `.cache/dev-cycle/t16/resumed/`.

DONE_WITH_CONCERNS: CPU implementada y verificada; revisión/QA independiente, documentación y GPU/comparación quedan a root.
