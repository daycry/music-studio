# Implementación T-19 — producción congelada

Fecha: 2026-10-06. Rama coordinada por root: `m0/t-19-presupuesto-prompts`, base `83fc652`. Este informe es evidencia de implementación, no ledger ni cierre de tarea. Root posee Git, medición, documentación, revisión y QA.

## Alcance entregado

Producción: `apps/engines/acestep/{input_profile.py,preflight.py,adapter.py,descriptor.py,engine_acestep.py}`, `apps/engines/common/engine_common/server.py`, `scripts/generate.py`, `packages/audio-post/audio_post/manifest.py`, `packages/contracts/manifest-v1.schema.json`.

Tests: `apps/engines/acestep/tests/{test_preflight.py,test_adapter.py}`, `apps/engines/common/tests/test_common.py`, `tests/test_generate_preparation.py`. Sin cambios de worker, engine-contract, locks, dependencias ni pesos. Scripts/recibos de T-17 permanecen inmutables.

Perfil PT/tier4 explícito: LM entrada conditional/unconditional más reserva real `int(duration*5)+10` <=4096; DiT texto <=256/letra <=2048; duración <=480. Son políticas operativas, no ventana arquitectónica deducida de tokenizer.model_max_length. Métodos puros upstream extraídos únicamente después de comprobar SHA-256 de las siete fuentes fijadas en input_profile; no plantilla aproximada propia. Tokenizadores offline y sus dieciséis archivos JSON/text/jinja/config verificados contra lock. Config del checkpoint DiT seleccionado verificada antes de tokenizadores/carga. SFT-stems/is_lego_sft se rechaza explícitamente: su plantilla requiere tracks Local/Global que M0 song/instrumental no expone; Turbo/SFT/Base normales no se desactivan.

Hook opcional en create_app; estimate/jobs cuentan fuera del lock y event loop antes de supervisor/registro de trabajo. Fallos de hash/config/tokenizer/timeout son tipados y no exponen stderr upstream. El adaptador directo vuelve a medir por variante antes de generación. Sin hook, mock/otros conservan comportamiento; verified=false no cambia.

Captura real mediante wrappers restaurados con functools.wraps: lm_arguments (language añadido al user_metadata), lm_formatted_prompt (conditional+unconditional/reserva), dit_arguments, dit_tokens. CoT caption/language/metas=false, semillas exactas y shift conservados. Se rechaza extracción SFT y normalización silenciosa de key antes de carga. Administrative caption16384/letra32768 solo con presupuesto nativo activo.

## Interfaz y privacidad

- Estimate añade opcionalmente `input_budget`: kind planned, profile_revision/profile_sha256, request_sha256/effective_sha256, lm y dit. No afirma fronteras alcanzadas.
- DoneData.result añade opcionalmente `input_receipts`: `{filename:"input-receipt-<i>.json", sha256, output_index}`; payload privado `{planned,captured}` en tmp del trabajo. Planned incluye hashes de fuentes/tokenizadores/config checkpoint, request y effective. Captured registra límites realmente alcanzados, hashes de params/config efectivos, flags/defaults y cuatro etapas. No renombra planned como captured.
- Publicación CLI: CAS privada `data/preparations/native-<sha>.json`; referencia pública `{sha256,output_index}` por variante. Escritura temporal confinada seguida de hardlink atómico sin overwrite; interrupción no deja un destino CAS parcial. Repeticiones comprueban igualdad de bytes.
- Validator comprueba hash y estructura, request/seed/variante, cuatro etapas/flags/conteos y presupuesto. Verify_manifest lee cada recibo nativo una vez y valida esos mismos bytes; cuando existe preparation contrasta los params privados completos, incluidos caption/letra/negative_prompt, no solo la proyección pública.
- Nuevos manifiestos excluyen style, lyrics y negative_prompt de request.params. El último tiene ruta real aceptada por JobRequest y descriptor ACE, cubierta con publicación CLI. La referencia privada/effective conserva el contraste. Manifiestos antiguos con negative_prompt se leen y verifican sin reescribirlos.
- stdout/stderr y logger upstream se suprimen en el ámbito de generación del hijo; progreso propio sigue por IPC. Ningún recibo público ni error contiene textos de la solicitud.

## TDD: evidencia RED contractual conservada

Todas las salidas completas están junto a este informe. Fechas del tramo 2026-10-05/06; root mide tiempo/tokens, este agente no abrió usage-meter.

1. RED: `test_preflight.py::test_http_preflight_hook_is_optional` falló con ausencia de parámetro preflight; `red-hook.txt`. Presupuestos/reserva: `red-budget.txt`, `red-native.txt` (native_plan/preflight inexistentes antes de producción).
2. RED: rutas de transformación/directadapter fallaron DID NOT RAISE y acceso runtime antes de preflight; `red-transform.txt`, `red-direct.txt`. Malformed/hash/timeout: `red-malformed.txt`, `red-list.txt`. Checkpoint seleccionado ausente/alterado aceptado antes del fix: `red-checkpoint.txt`.
3. RED: caption>512 rechazado por schema previo: `red-caption.txt`; después se acepta si cabe y se bloquea exceso nativo. Límites exactos/+1 y conservación seed/shift cubiertos en tests.
4. RED: captura/idioma no existían (`red-capture.txt`); key con espacios se normalizaba silenciosamente (`red-key.txt`). Pruebas diferenciales verifican YAML/metadata/PT ambas ramas reales.
5. RED: publicación inexistente (`red-publish.txt`), captura sin defaults aceptada (`red-defaults.txt`); interrupción dejaba CAS parcial (`red-atomic.txt`); item None producía AttributeError (`red-ref.txt`); lectura nativa dos veces (`red-single-read.txt`); recibo nativo divergente de preparation aceptado (`red-preparation-binding.txt`); negative_prompt se publicaba (`red-negative.txt`); negative efectivo sustituido aceptado (`red-negative-effective.txt`). Todas corregidas y verdes.
6. Corpus/probe es verificación diferencial CPU; inferencia musical no ejecutada. Recibos anteriores preservados: native-public/private originales y probe3. Probe2 falló por fixture skip_genres incorrecta antes de forward; se corrigió invocando dispatcher PT original, sin adaptar producción. Probe3: exit0,16 casos/6 bloqueados; código PT real construye ambas ramas y reserva, forward sustituido. Candidato fiel LM1131/unconditional33, DiT172/970. Tags transportados no prueban obediencia musical.
7. Verificación CPU y cobertura oficial abajo; revisión fresca/build CPU/QA son puertas del orquestador y aún no se declaran realizadas por este agente.

## Verificación ejecutada sobre freeze

`uv run --frozen --all-packages pytest apps/engines/acestep/tests/test_preflight.py apps/engines/acestep/tests/test_adapter.py apps/engines/common/tests/test_common.py tests/test_generate_preparation.py packages/engine-contract/tests/test_contract.py -q -m "not gpu"`

Salida real: `120 passed, 1 skipped in 4.10s`; `verification-final-tests.txt`.

`uv run --frozen scripts/export_contracts.py --check`: `engine-v1.json up to date`; exit0, `verification-final-contracts.txt`.

`uv run --frozen scripts/verify_manifest.py packages/contracts/examples/`: `all valid (4 manifests)`; exit0, `verification-final-manifests.txt`.

Ruff del alcance: `All checks passed!`; exit0, `verification-ruff.txt`.

Cobertura oficial por directorios, sin forzar imports de módulos: `uv run --frozen --all-packages pytest tests apps/engines/acestep/tests/test_preflight.py apps/engines/acestep/tests/test_adapter.py apps/engines/common/tests/test_common.py packages/engine-contract/tests/test_contract.py -q -m "not gpu" --cov=scripts --cov=apps/engines/acestep --cov=apps/engines/common/engine_common --cov=packages/audio-post/audio_post --cov-report=json:.cache/dev-cycle/t19/coverage-freeze.json --cov-report=term`, COVERAGE_FILE privado `.cache/dev-cycle/t19/coverage-data/.coverage-freeze`. Resultado real: `222 passed, 1 skipped, 5 warnings in 12.84s` (advertencias heredadas de timeout TestClient). Adapter85%, preflight90%, common/server87%, manifest88%, generate93%, descriptor/engine factory/input_profile100%. Agregado81% incluye fuera del alcance; root calcula statements añadidos del diff sin confundir agregado histórico con gate del cambio. coverage-freeze.txt/json conservados. Intentos de instrumentación fallidos/no-data preservados, no tratados como verde.

Probe final listo: `.cache/dev-cycle/t19/verify-native-preflight.py --output /output/probe4`; intérprete /opt/acestep/.venv/bin/python, CUDA_VISIBLE_DEVICES vacío, upstream /opt/acestep, workspace host ro, salida privada rw. Script final incluye checkpoint config/flags de captura además del diferencial PT reforzado. Root ejecuta sin GPU ni carga de pesos y preserva probe3. Root también construye imagen CPU nueva para integración real del código congelado.

## Límites y handoff

Actualización comunicada por root tras freeze: construcción de imagen nueva exit0; probe integrado final16 casos/6 bloqueados exit0, sin forward/GPU. Suite common inicial en imagen no inició por fixture engine_mock ausente; root repetirá con montaje de fixture manteniendo profundidad original. Esta evidencia pertenece al orquestador; no se confunde con la suite host ejecutada por este agente.

### Único re-despacho de validación: fixtures CPU anteriores

RED existente conservado en `root-full-suite.txt`: suite explícita `tests packages apps/engines`, `6 failed, 349 passed, 5 skipped, 1 deselected`. Los seis fallos se producían antes del comportamiento evaluado: sus runtimes sintéticos no proporcionaban el nuevo conteo CPU nativo y alcanzaban un worker sin entorno/tokenizadores adecuado. No eran defectos de producción ni fallos VRAM reales.

Ownership adicional autorizado por root: exclusivamente `apps/engines/acestep/tests/{test_preflight_vram.py,test_review_fixes.py,test_shift.py}`. Se inyecta un doble CPU explícito de la dependencia preflight en esos runtimes, manteniendo el parser upstream fijado, error VRAM real, saneamiento de mensajes y asserts de semillas/shift. Se añaden comprobaciones de invocación por semilla/variante (`n_outputs=1`), checkpoint y shift; las fases de error durante load comprueban cero invocaciones. Los tests de presupuesto nativo real y bypass siguen en test_preflight.py. Los nuevos dobles no afirman medición de tokens ni inferencia real. Sin cambios de producción, sin skips añadidos ni guardas relajadas.

Verificación real tras corregir fixtures:

- `. scripts/env.ps1` y `uv run --frozen --all-packages pytest apps/engines/acestep/tests/test_preflight_vram.py apps/engines/acestep/tests/test_review_fixes.py apps/engines/acestep/tests/test_shift.py -q -m "not gpu" -o cache_dir=.cache/dev-cycle/t19/fixture-validation/cache` → `40 passed in 0.42s`; exit0, `fixture-modules-green.txt`.
- `uv run --frozen --all-packages pytest tests packages apps/engines -q -m "not gpu" -o cache_dir=.cache/dev-cycle/t19/fixture-validation/cache` → `355 passed, 5 skipped, 1 deselected, 5 warnings in 20.12s`; exit0, `fixture-full-suite-green.txt`. Los cinco avisos son deprecaciones existentes de TestClient timeout; no hubo aviso WinError5 al precrear caché local.
- `uv run --frozen ruff check apps/engines/acestep/tests/test_preflight_vram.py apps/engines/acestep/tests/test_review_fixes.py apps/engines/acestep/tests/test_shift.py` → `All checks passed!`; exit0, `fixture-ruff.txt`.

Freeze reafirmado: producción e imagen sin mutaciones; tests de fixtures listos para revisión/QA del orquestador. Ledger, Git, journals y recibos históricos intactos; sin medidor propio.

No se ejecutó inferencia/audio/GPU ni se afirma calidad/obediencia musical. La prueba nativa es CPU con forward sustituido, explícita en recibos. Los tests diferenciales usan copia local upstream T-17 fijada, no descargan fuentes. Revisión A/B/C, QA independiente, gate por statements del diff y reconstrucción de imagen pertenecen a root. Este informe no cierra el ledger.
