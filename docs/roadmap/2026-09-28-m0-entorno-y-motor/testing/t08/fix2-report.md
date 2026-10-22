# T-08 fix2: entrega CPU para revisión

2026-10-06. Corrige A-T08-DOC-01, B-LONG-01 y B-INPUT-01; conserva antecedentes y fix1. No modifica ledger, documentos root, common, ACE-Step, locks root, BD ni knowledge.

Transcribe hasta600s por intervalos contiguos de hasta180s. Cada intervalo conserva el texto/idioma reconocido y sus límites reales en samples; concatena texto y usa merge_languages de Qwen fijado. Tras reconocer todos, libera ASR una vez y carga alineador una vez. La alineación usa esos mismos slices y suma su offset. Los silencios mantienen sus metadatos sin pedir palabras. Alineación independiente limitada explícitamente a180s hasta M3, conforme decisión root ADR0031; no divide letra esperada por heurística. Todos los tasks siguen verified:false.

Idioma de entrada inválido: enum canónico ligero/preflight y validación backend, sin torch en padre. Audio no decodificable: captura específica LibsndfileError excepto SF_ERR_SYSTEM, conservado como INTERNAL. Los errores de modelo RuntimeError/ValueError y EngineError VRAM_EXCEEDED mantienen clasificación. README y Compose ejecutan fix2; tags históricos intactos.

RED previo real (2026-10-06):
- test_segments.py::test_long_transcription_aligns_recognized_fragments_with_real_offsets: AssertionError, [450] frente a [180,180,90]. red.log/xml.
- test_segments.py::test_worker_classifies_invalid_input_without_hiding_internal[language/audio]: AssertionError, INTERNAL frente a INVALID_PARAMS. red.log/xml. 3failed total6,27s.
- test_segments.py::test_independent_alignment_declares_and_enforces_180_seconds: AssertionError, [0,600] frente a [0,180]. red-independent.log/xml;1failed1,54s.
- test_segments.py::test_worker_keeps_audio_system_failure_internal: AssertionError, INVALID_PARAMS frente a INTERNAL. red-system.log/xml;1failed4,96s.
- TDD n/a: comandos README y tag Compose, prosa/configuración.

GREEN dirigido:4passed6,93s inicialmente;10passed10,16s ampliado. Suite final de la propia imagen:45passed,4deselected,1warning15,24s; CPU_EXIT=0. Incluye450/600s a16/22,05kHz, silencios e idiomas mixtos, offsets, residencia secuencial, worker real y límites180s. ForcedAligner.align/parse upstream reales, processor/logits dobles CPU: palabra global450s y comienzo>399,92s. Estas pruebas demuestran transporte/rango; no precisión ni inferencia con pesos.

Cobertura oficial:346/382=90,5759%, gate80 pasado; mínimo por archivo safety32/36=88,8889%. Build final BUILD_EXIT=0. Imagen fix2 sha256:306e3b0fbc1170ee066e2aed099ef6638ea7dad7faf3ab5b67edfa90e64b70c9. Ruff All checks passed;15 files already formatted. Lock host --check --offline conforme111paquetes, exit0 sin sync/instalación.

Avisos y ensayos conservados: deprecación BlockingPortal de Starlette. Primeras suites propias fallaron por interacción de imports Qwen con fixture torch doble y expectativa antigua sinsegments; corregidos fixtures, no contados como RED. Lock en contenedor aislado exit2 por engine-common apuntando a workspace incompleto; chequeo host autorizado pasa. Primer probe inline falló por quoting PowerShell y siguiente por PYTHONPATH; corregidos, no errores de producto ni RED. PowerShell representa stderr nativo como NativeCommandError incluso con exit0; logs finales incluyen código nativo explícito. Un probe importa factoría/preflight antes de torch y bibliotecas reales después: PARENT_TORCH=False y CUDA_INITIALIZED=False. Compose resuelve fix2 y127.0.0.1:8130:8130.

Verificación completa GPU del brief NO ejecutada por alcance CPU explícito. No modelos/pesos/GPU/red runtime/descargas/instalaciones host, ni suite430, QA o evaluación musical. Pendientes revisión3 independiente, QA e inferencias reales de transcribe/CLAP/Audiobox. El medidor es responsabilidad de root; no se abrió otro.

Comando build: docker compose --profile engines build engine-analysis.
Comando CPU: docker run --rm --network none -e CUDA_VISIBLE_DEVICES= -e STUDIO_ENGINE_TOKEN=prueba-cpu -e STUDIO_TEST_TMP_DIR=/evidence/tmp -e COVERAGE_FILE=/evidence/.coverage -v <raíz>/models:/models:ro -v <raíz>/.cache/dev-cycle/t08/fix2:/evidence music-studio/engine-analysis:m0-t08-fix2 uv run pytest tests -m 'not gpu' --cov=engine_analysis --cov-report=term-missing --cov-report=json:/evidence/coverage.json --cov-fail-under=80 --junitxml=/evidence/cpu.xml -o cache_dir=/evidence/pytest-cache -q.
Comando lock host tras scripts/env.ps1: uv lock --check --offline --directory apps/engines/analysis.

DONE_WITH_CONCERNS: inferencias GPU, revisión3 y QA pendientes; align_lyrics completo sigue preparado para M3.
