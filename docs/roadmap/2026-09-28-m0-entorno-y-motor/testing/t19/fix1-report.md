# Corrección B-01 — T-19, intento 1

Producción congelada: `packages/audio-post/audio_post/manifest.py`. Tests: `tests/test_generate_preparation.py`. Ningún otro fichero de producto, ledger, Git, lock o recibo histórico cambiado.

El validador comprueba correspondencia de idioma/alias, instrumental, BPM, tonalidad, compás y shift con la solicitud. Los defaults PT (thinking, CFG, steps, LM CFG, cover strength, CoT false, normalización false, prompt negativo por defecto) y presupuesto LM fijado ya no se toman de planned para validar planned. La captura de metadata se compara siempre con lo derivado de la solicitud; `planned.effective.lm_metadata` se compara cuando existe. `legacy_cfg_prompt`, si existe, debe ser false. Se conserva la omisión de esos dos campos del baseline sintético anterior, sin permitir que contradigan controles. No se importan engine, torch ni transformers.

Tests de 18 mutaciones semánticas con hashes internos recalculados; casos válidos de alias, metadata explícita, omisión e instrumental. Publicación real con transporte/audio sintéticos: baseline genera manifiesto verificado; idioma, shift y CoT se rechazan antes de CAS; un CAS hostil recalculado se rechaza en verify_manifest. Los originales review-B se leyeron sin escribir: baseline accepted, language/shift/cot_flags INPUT_RECEIPT_INVALID (script con asserts; review-receipts.json).

RED: `test_native_receipt_rejects_rehashed_semantic_contradiction[language]` falló DID NOT RAISE ValueError · 2026-10-06 (`red-language.txt`).
RED: `test_generation_native_semantics_before_cas[language/shift/cot_flags]` falló DID NOT RAISE ValueError; baseline publicó, pero verify aceptó CAS hostil · 2026-10-06 (`red-integration-real.txt`).
RED: `test_native_receipt_rejects_rehashed_semantic_contradiction[legacy_cfg_prompt]` falló DID NOT RAISE ValueError · 2026-10-06 (`red-legacy.txt`).
Los intentos iniciales de fixture con receipts fuera de done.result o CAPABILITY_UNAVAILABLE no se cuentan como RED. La producción se retiró temporalmente y restauró después de reproducir el RED de integración correcto.

Verificación final declarada cinco módulos: **146 passed, 1 skipped in 4.19s**, exit 0 (`declared-tests.txt`). Vecinos con cobertura: **98 passed in 2.06s**, exit 0 (`coverage-tests.txt`). Exportador: **engine-v1.json up to date**, exit 0 (`export.txt`). Ejemplos: **all valid (4 manifests)**, exit 0 (`examples.txt`). Ruff alcance: **All checks passed!**, exit 0 (`ruff.txt`). Cobertura fix en changed-coverage.json y datos completos coverage-final.json, sin instalaciones. El primer intento coverage con source de módulo preimportó numpy y falló; el definitivo usa source por directorio y pasa. La medición del diff completo contra 83fc652 corresponde a root.

El probe nativo previo sigue vigente: engine/preflight no cambian. Root contrastará las diez capturas reales con este validador CPU. Sin GPU, inferencia, descargas, instalaciones, medidor propio ni actualización del ledger. Revisión 2 y QA independiente pendientes del orquestador.
