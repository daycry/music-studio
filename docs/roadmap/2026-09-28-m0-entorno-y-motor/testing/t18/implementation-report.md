# Informe de implementación T-18 (subagente)

Producción estable; no ledger, docs, Git commits, instalación, build ni GPU modificados por este subagente. El orquestador realiza revisión, QA y cierre.

## Alcance exacto escrito

- scripts/input_preparation.py (nuevo)
- tests/test_input_preparation.py (nuevo)
- scripts/generate.py
- tests/test_generate_preparation.py (nuevo)
- apps/engines/acestep/descriptor.py
- apps/engines/acestep/adapter.py
- apps/engines/acestep/tests/test_adapter.py
- packages/contracts/manifest-v1.schema.json
- packages/audio-post/audio_post/manifest.py
- packages/audio-post/tests/test_manifest_errors.py
- .cache/dev-cycle/t18/implementation-report.md, red-*.txt, verification*.txt, coverage*.json/output, changed-coverage.json, contracts-final.txt, manifests-final.txt, lint-final.txt y probe-implementation.txt (evidencia privada ignorada)

No cambiaron tests/test_generate.py, tests/test_generate_shift.py, scripts/verify_manifest.py, engine-v1.json ni ejemplos existentes: su comportamiento legado pasa la verificación. El esquema de referencia opcional se cubre con manifiestos y recibos sintéticos en tests; ningún recibo privado real se incorpora a ejemplos públicos.

## API y límites

prepare(request, sources={lyrics/style: bytes}, strip_tag_markdown=False) produce original (snapshot de petición antes de limpieza), effective, effective_request_sha256 canónico, fields con original, original_bytes_base64, original_bytes_sha256, effective_sha256, diff, transformations y engine_budget=pending. En adaptación manual de estilo, fields.style.original contiene el original aportado, mientras original.params.style ya refleja el caption explícito de la petición. explicit_style y diff registran esta elección, sin transformación automática del estilo.

publish(receipt, data_root) publica data_root/preparations/<sha256>.json usando fichero temporal, fsync y hard link exclusivo; nunca sobrescribe un recibo. verify(reference, request, data_root) comprueba referencia/hash, reconstrucción íntegra del recibo y acuerdo con la petición efectiva. El núcleo usa solo stdlib. Los manifiestos nuevos contienen preparation:{sha256}, sin prompt, letra ni rutas privadas. El verificador comprueba la evidencia privada y sus hashes/diff antes de validar outputs. Las publicaciones de audio mantienen el staging/rollback existente y la referencia opcional conserva compatibilidad v1.

CLI: --prepare-only, --strip-tag-markdown, --source-style-file, --key, --time-signature. --style sigue siendo texto. Prepare-only no consulta configuración, HTTP, catálogo del engine, FFmpeg ni modelos. Key/time_signature se omiten por defecto; time_signature se envía como timesignature upstream. No se implementó T-19, transporte al LM, presupuesto del motor, preflight de tokens ni comprobación artística.

## Evidencia RED real, antes de producción

- RED: tests/test_input_preparation.py::test_identity_and_explicit_tags falló porque effective era None y no existía preparación fiel · 2026-10-05 (red-pure.txt). Criterios original/efectivo y limpieza opt-in.
- RED: tests/test_input_preparation.py::test_receipt_integrity_and_immutable_publication falló porque publish no devolvía referencia SHA-256 · 2026-10-05 (red-receipt.txt). Integridad, procedencia/publicación inmutable.
- RED: tests/test_generate_preparation.py::test_offline_prepare_and_metadata falló con SystemExit 2: opciones prepare-only/key/time-signature no reconocidas · 2026-10-05 (red-cli.txt). CLI offline y metadata.
- RED: apps/engines/acestep/tests/test_adapter.py::test_time_signature_metadata_optional falló con None != '4/4' · 2026-10-05 (red-metadata.txt). Transporte opcional upstream.
- RED: packages/audio-post/tests/test_manifest_errors.py::test_preparation_reference_missing_rejected falló DID NOT RAISE ValueError · 2026-10-05 (red-manifest.txt). Referencia opcional verificada.
- RED: tests/test_input_preparation.py::test_lyrics_source_disagreement_rejected falló DID NOT RAISE ValueError · 2026-10-05 (red-source.txt). No pérdida silenciosa ni fuente de letra discordante.
- RED: tests/test_input_preparation.py::test_effective_request_hash falló None != SHA-256 canónico de la petición · 2026-10-05 (red-request-hash.txt).
- RED: tests/test_generate_preparation.py::test_malformed_receipt_with_matching_reference[structure/field_hash] falló KeyError task / DID NOT RAISE ValueError · 2026-10-05 (red-manifest-integrity.txt). Error tipado e integridad interna en verificador público.

Los errores de import del entrypoint descubiertos por CLI real se corrigieron como fallo de integración; no se presentan como evidencia TDD contractual. Hay regresión subprocess del entrypoint. Tests adicionales cubren autoría, omisión/conflictos de brief, metadata inválida, conservación BOM/CRLF/asteriscos de versos, origen de estilo distinto, fallo atómico sin temporales, desacuerdo de petición antes de HTTP, manipulación de recibos y privacidad.

## Verificación final ejecutada

Entorno cargado con scripts/env.ps1; uv frozen all-packages; basetemp/cache dentro del repositorio.

`uv run --frozen --all-packages pytest tests/test_input_preparation.py tests/test_generate.py tests/test_generate_shift.py tests/test_generate_preparation.py apps/engines/acestep/tests/test_adapter.py packages/audio-post/tests/test_manifest_errors.py -q -m "not gpu" --basetemp=.cache/pytest/t18-green -o cache_dir=.cache/pytest/cache`

Salida real: `177 passed, 1 skipped, 5 warnings in 6.41s` (exit 0). Los cinco warnings son Starlette TestClient timeout de tests existentes. Detalle completo en verification-final.txt.

`uv run --frozen scripts/export_contracts.py --check`: `engine-v1.json up to date` (exit 0).

`uv run --frozen scripts/verify_manifest.py packages/contracts/examples/`: `all valid (4 manifests)` (exit 0).

Ruff sobre los nueve Python escritos: `All checks passed!` (exit 0).

`uv run --frozen --all-packages python .cache/dev-cycle/t18/verify-preparation.py`: status passed_cpu_preparation; 72 versos, 9 tags completos, 32 registros de hashes intactos; repeated_preparation_immutable=true; generated=false; model_loaded=false; engine_budget=pending; musical_compliance_verified=false (exit 0). Salida completa privada en probe-implementation.txt. El original real no tenía decoración Markdown: el probe usa una derivación explícita para probar la retirada opt-in.

## Cobertura medida

coverage.json procede del mismo conjunto de tests con pytest-cov por directorios (evita imports anticipados que interfieren con parches CPU). coverage-output y verification.txt conservan la salida. changed-coverage.json cruza líneas añadidas por git diff HEAD con executed_lines/missing_lines; para módulo nuevo usa todos los statements. No se cuenta documentación ni tests como producción.

- input_preparation: 77/80 statements cambiados = 96.25 %.
- generate: 42/45 = 93.33 %.
- adapter: 2/2 = 100 % (el 78 % de archivo completo incluye código GPU previo no cambiado).
- descriptor: sus cambios están dentro de un literal ejecutado; archivo completo 100 %, sin nuevos statements separados detectables por coverage.
- manifest: 45/52 = 86.54 %.

El dato es cobertura de statements cambiados, no branch coverage ni QA musical. La revisión y QA independiente del orquestador siguen pendientes; no se declara cerrado el hito.
