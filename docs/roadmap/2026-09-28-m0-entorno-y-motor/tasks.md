---
generacion:
  fuente: estimado
verificacion: obligatoria
---

# Checklist de Tareas — M0 · Entorno, motor por CLI y elección de modelo

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-28 · reencauzado 2026-10-22 ([ADR-0089](../../decisiones/ADR-0089-reencauce-tras-codex.md)) |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Historial** | [`../../archive/codex-2026-10/m0-tasks.md`](../../archive/codex-2026-10/m0-tasks.md): ledger completo con revisiones e intentos hasta 2026-10-12. Las evidencias crudas están en el commit `36d4e99` |

> **Ledger canónico.** Aquí solo va el estado, los criterios y la salida resumida de la Verificación. El diario de intentos y los recibos de revisión no entran (ADR-0089). Solo el orquestador actualiza este fichero.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | Canceladas |
|------|------------|-------|----------|-----------|
| Fase 1 — Preparación | 2 | 2 | 100% | 0 |
| Fase 2 — Cimientos compartidos | 3 | 3 | 100% | 0 |
| Fase 3 — Motor musical | 3 | 3 | 100% | 0 |
| Fase 4 — Medición y elección | 9 | 13 | 69% (9 de 10 vigentes) | 3 |
| **TOTAL** | **17** | **21** | **94% de lo vigente (17/18)** | **3** |

**Para cerrar M0 falta:**

1. La escucha y la decisión del propietario (T-13). T-08, T-09, T-16 y T-20 cerradas técnicamente el 2026-11-06; tomas comparables de T-16 listas.

---

## Fase 1 — Preparación

### T-00 — Prerrequisitos manuales de la máquina
- **Descripción**: Máquina lista: GPU visible en Docker, WSL con 24 GB, Python aislado con uv y herramientas instaladas.
- **Estado**: completado
- **Dependencias**: ninguna
- **Verificación** (ejecutada 2026-09-28): `docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi` → `NVIDIA GeForce RTX 5070, 12227MiB` · `wsl -e free -g` → 23 · Node 22.23.2 / pnpm 9.12.0 / uv 0.12.19 / git 2.47.1.
- **Changelog**: Máquina preparada: GPU visible en Docker, WSL con 24 GB, herramientas instaladas y carpetas pesadas fuera de la sincronización.

### T-01 — Esqueleto del repositorio
- **Descripción**: Estructura del monorepo, tooling Python/Node y script de bootstrap desde los locks.
- **Estado**: completado
- **Dependencias**: T-00
- **Verificación**: `.\scripts\bootstrap.ps1` reconstruye `.venv` y `node_modules` · `uv run ruff check .` limpio (ejecutada al cerrar; detalle en el historial).
- **Changelog**: Repositorio inicializado con el esqueleto del monorepo y un script que reconstruye el entorno de desarrollo desde los ficheros de bloqueo.

## Fase 2 — Cimientos compartidos

### T-02 — `packages/weights`: lock, descarga verificada, auditor de pickle y herramientas
- **Descripción**: Descarga reproducible y segura de modelos y herramientas (ADR-0006).
- **Estado**: completado
- **Dependencias**: T-01
- **Verificación**: `uv run scripts/fetch_models.py --check` y `uv run scripts/fetch_tools.py --check` → todo verificado por SHA-256 (detalle en el historial).
- **Changelog**: Descarga reproducible y verificada (SHA-256, revisión fijada) de los modelos de ACE-Step y de evaluación, con conversión segura de pickle a safetensors y ffmpeg LGPL.

### T-03 — `packages/engine-contract` + `apps/engines/common` + `engine-mock`
- **Descripción**: El contrato `/v1` como código, con el servidor común de engines y un engine simulado.
- **Estado**: completado
- **Dependencias**: T-02
- **Verificación**: `uv run pytest packages/engine-contract apps/engines/common apps/engines/mock -m "not gpu"` en verde; revisión de dos lentes intento 3 sin gaps (historial).
- **Changelog**: Contrato /v1 de engines como código, con servidor común, control de VRAM y engine simulado para pruebas sin GPU.

### T-04 — `packages/audio-post` + manifiesto v1 + verificador
- **Descripción**: Post-proceso CPU (FLAC 24, MP3, forma de onda) y manifiesto verificable.
- **Estado**: completado
- **Dependencias**: T-02
- **Verificación**: `uv run pytest packages/audio-post -m "not gpu"` en verde; QA de la Fase 2, 2026-10-05 (historial).
- **Changelog**: Post-proceso de audio en CPU con FLAC de 24 bits, MP3, forma de onda y manifiesto verificable.

## Fase 3 — Motor musical

### T-05 — Imagen `engine-acestep` para sm_120
- **Descripción**: Imagen Docker de ACE-Step con CUDA para la RTX 5070.
- **Estado**: completado
- **Dependencias**: T-03
- **Verificación**: build de la imagen y prueba GPU en la 5070 (historial, revisión de la Fase 3).
- **Changelog**: Imagen de ACE-Step con CUDA, Python 3.11, FFmpeg LGPL y BF16 comprobada en la RTX 5070.

### T-06 — Adapter ACE-Step (`music.song`, `music.instrumental`)
- **Descripción**: La API Python de ACE-Step detrás de `/v1`, con los modos del tier 4 forzados.
- **Estado**: completado
- **Dependencias**: T-05
- **Verificación**: `docker compose run --rm engine-acestep uv run pytest -m gpu` en verde (historial).
- **Changelog**: ACE-Step genera canciones e instrumentales locales mediante /v1, con pesos verificados, semillas exactas, control de memoria y salida WAV estéreo a 48 kHz.

### T-07 — CLI `scripts/generate.py`: primera canción 🎯
- **Descripción**: CLI que llama al engine, ejecuta audio-post y escribe el manifiesto.
- **Estado**: completado
- **Dependencias**: T-04, T-06
- **Verificación**: primera canción completa generada por CLI y escuchada por el propietario (historial).
- **Changelog**: Generación local por CLI desde letra y estilo o catálogo de briefs, con progreso, cancelación y exportaciones inmutables de master, MP3, forma de onda y manifiesto; primera canción completa generada y escuchada.

## Fase 4 — Medición y elección

### T-08 — `engine-analysis` (transcripción, CLAP, estética y beats)
- **Descripción**: Contenedor de análisis que usan M0 (evaluación) y M1 (beats).
- **Estado**: completado
- **Dependencias**: T-03, T-02, T-19
- **Archivos**: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/analysis-cpu-2026-11-06.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/analysis-gpu-2026-11-06.md`, `CONTINUE-HERE.md`. El engine, sus tests y dependencias se cotejan por SHA sin cambios de producto.
- **TDD n/a: verificación sin código nuevo**. Se ejecutan las pruebas existentes dentro del runtime Docker, sin instalar PyTorch en el host ni acceder a GPU.
- **Verificación**: en el runtime Docker del engine, `python -m pytest tests -m "not gpu"` en verde **y** `uv run pytest -m gpu` en verde dentro del contenedor de Compose. Se conserva la colección completa de 48 casos CPU y cuatro del batch GPU; PyTorch no se instala en el host. El runner GPU usa `docker compose run --rm --no-deps engine-analysis` para preparar el runtime aislado y `docker exec` para ejecutar la suite original, según argv conservado.
- **Verificación CPU ejecutada (2026-11-06)**: 48 pass/0 fail/0 skip/4 deselected,20,43 s; sentencias346/382 (90,58 %), ramas116/142 (81,69 %), combinado88,17 %. Suplemento independiente beats CPU:1 pass,120 BPM/61 beats, hijo y descarga reales; guardCUDA0 en padre/hijo. Fuentes21analysis/49snapshot y71 ajenos intactos. Rojo inicial por lock omitido sólo en QA conservado. A/B sin hallazgos y QA documental aprobada. [Informe CPU y recibos](testing/analysis-cpu-2026-11-06.md).
- **Verificación GPU y cierre técnico**: CPU publicado en `cd40c2b`, luego autorización expresa del propietario. Batch original único: **4 pass/0 fail/0 error/0 skip/48 deselected**,275,83 s. ASR/alineador, CLAP y Aesthetics CUDA/BF16; beats CPU. Cargas secuenciales y descarga real de cuatro hijos;49 fuentes/dependencias y cinco modelos seguros verificados. Pico host6226MiB, tras limpieza1305MiB; Ollama vacío como al inicio. No certifica `spilled:false` ni benchmarkT09. Contenedor retirado, demo intacta. Revisión A/B sin hallazgos y QA final `PASS_T08_CPU_GPU_EVIDENCE_AND_DOCS`, elegible para cierre: **orquestador acepta T-08**. [Informe y revisión](testing/analysis-gpu-2026-11-06.md); raw `.cache/dev-cycle/20261106-m0-t08/gpu/qa/`. M0/M1 continúan abiertos; integración de la rama apilada pendiente de T-16.
- **Changelog**: Motor local de análisis con transcripción y alineación secuenciales, similitud CLAP, estética y beats en CPU; pesos verificados, caché segura y descarga del proceso hijo.

### T-09 — Benchmark básico en la 5070
- **Descripción**: **Recortado (ADR-0089).** Medir tiempo por canción, VRAM de pico y si hay desbordamiento a RAM con el modo por defecto de ACE-Step en la 5070. La auditoría canónica y el presupuesto absoluto quedan fuera.
- **Estado**: completado
- **Dependencias**: T-07, T-19
- **Archivos**: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/benchmark-basico-2026-11-06.md`, `CONTINUE-HERE.md`. Verificación del producto existente, sin cambios de código; TDD n/a: documentación y ejecución.
- **Verificación**: una tabla en este ledger con 3 generaciones (≈2 min de canción): duración, VRAM de pico (`nvidia-smi`) y `spilled=false`.
- **Salida ejecutada (2026-11-06)**: tres jobs CLI independientes en Docker con Turbo/BF16/PT, ocho pasos por defecto, semilla 1/2/3. Tres terminales `done` originales, CLI exit 0; tabla en segundos y MiB:

  | Semilla | Audio real (s) | CLI completa (s) | Inferencia (s) | Pico host (`nvidia-smi`, MiB) | `spilled` |
  |---|---:|---:|---:|---:|---|
  | 1 | 120,00 | 229,56 | 30,69 | 9.376 | `false` |
  | 2 | 120,00 | 185,49 | 33,74 | 9.394 | `false` |
  | 3 | 120,00 | 182,51 | 37,28 | 9.394 | `false` |

- **Alcance medido**: proceso recargado por job, sin vaciar cachés de archivos. `spilled:false` literal del guard allocator, no certificado absoluto de paginación WSL. El extractor QA falló tras la primera generación válida; NDJSON conservado y lectura corregida, sin repetirla. [Informe](testing/benchmark-basico-2026-11-06.md); raw `.cache/dev-cycle/20261106-m0-t09/qa/`.
- **Revisión de dos lentes — intento 1 (T-09)**: A/B sin hallazgos; scope 0, sin exclusiones ni avisos; C/D no activadas. QA sin UI por diseño. QA final `PASS_T09_FINAL_DOCS_EVIDENCE`: 37 comprobaciones conformes, 0 gaps; ledger 0 incoherencias/25 avisos, cobertura n/a, 18 enlaces válidos. El orquestador acepta el cierre técnico; M0/M1 y su aceptación musical siguen abiertos. Detalle en el informe, sin recibos crudos versionados.
- **Changelog**: Benchmark básico de ACE-Step en la RTX 5070: tiempo por canción y VRAM de pico.

### T-10 — Matriz de capacidades verificadas
- **Descripción**: Aplazada al backlog (ADR-0089): no bloquea el MVP.
- **Estado**: cancelado
- **Dependencias**: T-07, T-19
- **Verificación**: n/a (cancelada; el trabajo parcial sigue en el historial y en `scripts/eval`).

### T-11 — Batería de evaluación automatizada (F-84)
- **Descripción**: Aplazada al backlog (ADR-0089). El código parcial sigue en `scripts/eval`.
- **Estado**: cancelado
- **Dependencias**: T-07, T-08, T-19
- **Verificación**: n/a (cancelada).

### T-12 — *(Opcional)* `engine-heartmula` en 4 bits
- **Descripción**: Opcional; aplazada al backlog (ADR-0089).
- **Estado**: cancelado
- **Dependencias**: T-03, T-11, T-19
- **Verificación**: n/a (cancelada).

### T-13 — Escucha y decisión de modelo
- **Descripción**: Escucha a ciegas del propietario (T-14, T-15, T-16 y T-09) y decisión de modelo y modo por defecto registrada en un ADR.
- **Estado**: borrador
- **Dependencias**: T-09
- **Verificación**: ADR con el modelo y el modo por defecto elegidos por el propietario y `models/models.lock.json` coherente.

### T-14 — Comparación privada de «Libre»: shift 1 frente a 3
- **Descripción**: Tomas privadas comparables con hoja de escucha a ciegas.
- **Estado**: completado
- **Dependencias**: T-06, T-07
- **Verificación**: seis tomas y hoja de escucha generadas (historial).
- **Changelog**: Añade un shift opcional validado en la CLI y en ACE-Step, y prepara seis tomas privadas de Libre con hoja de escucha a ciegas.

### T-15 — Calidad de Libre: revisión de candidatos y comparación de prompts
- **Descripción**: Revisión de modelos locales alternativos y prueba de prompts.
- **Estado**: completado
- **Dependencias**: T-14
- **Verificación**: candidatos y licencias documentados; seis tomas privadas (historial).
- **Changelog**: Revisa candidatos locales y sus licencias, y prepara seis tomas privadas para comparar prompts con escucha a ciegas.

### T-16 — Controles de inferencia y comparación privada SFT frente a Turbo
- **Descripción**: Controles de inferencia (pasos, CFG, SFT/Turbo) en la CLI y el adapter, con tomas comparables.
- **Estado**: completado
- **Dependencias**: T-06, T-07, T-15, T-19
- **Archivos**: `apps/engines/acestep/adapter.py`, `packages/audio-post/audio_post/manifest.py`, `apps/engines/acestep/tests/test_dit_resolution.py`, `apps/engines/acestep/tests/test_preflight.py`, `apps/engines/acestep/tests/test_lm_seed.py`, `tests/test_generate_preparation.py`, `packages/audio-post/tests/test_audio_post.py`, `packages/audio-post/audio_post/pipeline.py`, `packages/audio-post/tests/test_directory_attributes.py`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/condicionamiento-cpu-2026-11-06.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/comparacion-gpu-2026-11-06.md`, `docs/knowledge/README.md`, `docs/knowledge/candidates/pending/2026-11-06-identidad-directorios-windows-residencia.md`, `docs/knowledge/candidates/pending/2026-11-06-semilla-lm-pt-individual.md`, `docs/decisiones/ADR-0032-condicionamiento-dit-segun-rama-nativa.md`, `docs/arquitectura/pipeline-audio.md`, `CONTINUE-HERE.md`. Controles y tests canónicos actuales se verifican sin cambios; se extiende la evidencia opcional de condicionamiento, no el auditor canónico aplazado. Alcance adicional justificado por QA: corregir la falsa identidad de directorios de audio ante los flags mutables PINNED/UNPINNED; afecta al postproceso que debe conservar/publicar los recibos. No se relajan controles de sustitución ni de reparse.
- **Verificación**: `uv run pytest tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py` en verde y las tomas SFT/Turbo preparadas para T-13.
- **Verificación actual (2026-11-06)**: 41 pass/0 skip/0 fail, sin importar Torch real. Seis MP3/90 s/48 kHz/estéreo íntegros; seis fuentes CLI locales y 18 salidas válidas, seis preparaciones/capturas; tres controles T-15 preservados coinciden por hashes de caption/letra con las seis T-16. Recibos en `.cache/dev-cycle/20261106-m0-t16/qa/`. Los tokens/resolución observados coinciden por par, pero **no está demostrada la igualdad de los códigos de audio LM**: falta su huella independiente y el hash de argumentos incluye pasos/CFG distintos. Tampoco se conserva la inicialización histórica PT. No se cierra la comparación por estos resultados parciales.
- **Corrección elegida**: campos observados opcionales de v2, manteniendo cinco etapas y lectura histórica: huella de `audio_code_string` real en `dit_resolution` y backend observado en la frontera LM. Hash de envelope JSON tipado, sin códigos en claro ni valores planificados como si fueran observados; validar semántica cuando estén presentes y exigir presencia para certificar condicionamiento. No reescribir activos antiguos ni completarles hashes. La evidencia que falta sólo puede obtenerse en futuras tomas cuando la GPU esté disponible.
- **RED histórico**: `test_descriptor_sft_identity_and_limits` falló por identidad Turbo frente a SFT; `test_adapter_sft_load_identity` por MODEL_NOT_FOUND frente a VRAM_EXCEEDED; `test_effective_defaults` por ausencia de 8/50 pasos · 2026-10-06, ledger de `36d4e99`. Los seis archivos de controles actuales son iguales al rescate.
- **RED del fix (2026-11-06)**: `test_capture_binds_native_resolution_and_instructions[False-False-None]` falló por `KeyError: audio_codes_sha256`; `test_capture_observes_runtime_backend_without_plan_fallback[pt]` por `KeyError: lm_backend_observed`, y `[vllm]` por no lanzar EngineError; `test_conditioning_present_malformed_is_rejected[audio_codes_sha256-None]` por no rechazar el campo; `test_conditioning_strict_requires_both_observations_in_v2[2-fields0]` por falta del argumento nuevo. Cada rojo se ejecutó solo antes del código; logs en `.cache/dev-cycle/20261106-m0-t16/fix1/red-*.log`.
- **Fix software, previo a revisión/QA**: 230 tests focales y 41 canónicos verdes; 163 tests con cobertura oficial. Delta ejecutable contra `3dede62`: 16/16 líneas, 100 %, sin exclusiones; no es la cobertura global de los módulos. Ruff verde. La corrida ampliada inicial tuvo dos fallos: fixture de ULID corregida y fallo Windows de atributos de directorio intermitente; contraste aislado baseline/actual/workingtree pasó, sin demostrar defecto preexistente ni regresión. No se declara verde de toda la suite. Evidencia en `fix1/evidence.md` y `changed-lines-coverage.json`. Los seis recibos históricos pasan el lector compatible y fallan el modo fuerte por observaciones ausentes; activos preservados. T-16 continúa en-progreso.
- **Entrega CPU aceptada (2026-11-06)**: tras fix2 y segunda revisión A/B sin gaps, QA2 ejecuta una única selección ampliada: **437 pass / 9 skip / 0 fail**, 446 casos, exit 0, 23,11 s. Incluye los 41 canónicos, dos tests nativos antes rojos y 13 regresiones nuevas. Ruff8 exit 0; ledger0 incoherencias/25 avisos históricos; scope congelado14 archivos exit 0 sin exclusiones/avisos. Cobertura oficial nueva: **18/18 sentencias afectadas**, 100 %, con expresión pipeline38→Return32 incluida; directorios completos74,56 % combinado, sin afirmar80 % global. Seis copias/seis fuentes/18 salidas fuente válidas, legacy6 válidos/strict6 rechazos por ausencia histórica. 14 SHA propios iguales antes/después y71 ajenos iguales al estado al retomar (dos journals ya diferían del original). Sin Torch/GPU/Ollama/SQLite/Claude. [Informe](testing/condicionamiento-cpu-2026-11-06.md); raw `.cache/dev-cycle/20261106-m0-t16/qa-fixed2/`. La entrega queda en la rama; T-16 permanece en-progreso hasta completar evidencia real de las comparaciones.
- **Primer ensayo GPU (2026-11-06)**: dos jobs de tres variantes, Turbo8 y SFT50/CFG7, 90 s, semillas1/2/3; CLI0, seis manifests/recibos fuertes y audios válidos, ambos terminales `spilled:false`. **0/3 parejas certificadas**: prompts/argumentos LM, backend PT, códigos no vacíos, tokens y controles comunes coinciden, pero las huellas de códigos LM difieren por pareja. Sin repetir generaciones ni alterar históricos. Fuentes68/ajenos71/modelos33 preservados; QA propio retirado, demo intacta, Ollama vacío y GPU final1227MiB. [Informe y diagnóstico CPU](testing/comparacion-gpu-2026-11-06.md); raw `.cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa/`. La prueba AST/mock de la fuente exacta demuestra que la ruta PT individual no aplica la semilla al muestreo. Ese resultado negativo se conserva.
- **RED semilla LM (2026-11-06)**: `test_lm_seed.py::test_same_effective_seed_ignores_prior_rng_and_checkpoint` falló con `AssertionError: La ruta LM individual sigue dependiendo del RNG anterior`; `test_variants_use_effective_seed_without_changing_lm_inputs[0]` falló por códigos incorrectos para la semilla efectiva 0. Cada rojo se ejecutó solo antes del código; logs en `gpu-pairs/seed-fix/red*.log`. Shim propio separado de captura aplica la semilla en PT single y restaura el método; ocho regresiones verdes. Implementador:180 pass/1 skip focales,41 canónicos pass/0 skip, Ruff verde; cobertura delta15/15 sentencias (100 %), archivo completo67,77 %. Pendientes revisión y QA CPU independientes y nueva comprobación GPU; el 0/3 previo se conserva.
- **Revisión de dos lentes — intento 1 (semilla LM) y QA CPU**: A/B sin hallazgos, scope ocho archivos/0 exclusiones/0 avisos, C/D no activadas. QA independiente **478 pass/10 skip/0 fail**, 488 casos,30,75 s; incluye41 canónicos y8 regresiones, sin Torch. Cobertura delta15/15=100 %; adapter completo322/394=81,73 % con esta selección. Ruff/diff/ledger verdes;25 avisos históricos. Ocho pins,67 fuentes intactas+adapter autorizado,71 ajenos intactos. [Informe y límites](testing/comparacion-gpu-2026-11-06.md); raw `gpu-pairs/seed-fix/qa/`. Orquestador acepta entrega CPU; T-16 permanece en-progreso hasta nuevas tomas GPU, sin reescribir el0/3 anterior.
- **Verificación GPU tras fix (2026-11-06)**: código/informe CPU publicados en `b642b58` antes de GPU. Imagen `86e0e7aa`, dos lotes nuevos de tres variantes90 s, semillas1/2/3; seis salidas válidas y **3/3 parejas certificadas**,20 checks por pareja, códigos efectivos no vacíos idénticos/PT/thinking capturados. CLI0 y `spilled:false` ambos lotes; pico host Turbo9515/SFT9575MiB. Fuentes69/imagen54/ajenos71/modelos33 contrastados; sin cambios de producto ni reescritura del0/3 anterior. QA propio retirado, demo intacta, Ollama vacío/GPU final1298MiB. [Informe y hoja de escucha](testing/comparacion-gpu-2026-11-06.md); raw `gpu-pairs/qa-seeded/`. Pendiente revisión documental final; sin elección ni aceptación musical del propietario.
- **Revisión de dos lentes — intento 1 (cierre GPU) y QA final**: A/B sin hallazgos, scope tres documentos/0 exclusiones/0 avisos; C/D no activadas. `PASS_T16_FINAL_DOCS_EVIDENCE`:62/62 comprobaciones,0 gaps,117 hashes íntegros,69 fuentes y71 ajenos intactos, ledger0incoherencias/25avisos; sinUI/cobertura n/a para este cierre documental. Orquestador acepta cierre técnico de T-16. [Informe y hoja de escucha](testing/comparacion-gpu-2026-11-06.md); QA en `gpu-pairs/qa-seeded/final-docs/`. Sin ganador ni aceptación musical; T-13 y M1 permanecen abiertos.
- **Changelog**: Controles de inferencia SFT/Turbo y semilla efectiva del LM PT por variante, con tres parejas privadas de Libre verificadas mediante códigos observados iguales.

### T-17 — Auditoría de fidelidad de prompts hasta LM y DiT
- **Descripción**: Auditoría del transporte de prompts y metadata hasta LM/DiT.
- **Estado**: completado
- **Dependencias**: T-06, T-07, T-15
- **Verificación**: informe de auditoría con evidencia en CPU (historial).
- **Changelog**: Audita el transporte de prompts, tags y metadata hasta LM/DiT con evidencia en CPU.

### T-18 — Preparación fiel y procedencia privada de instrucciones
- **Descripción**: Original y entrada efectiva separados, preparación offline y procedencia privada.
- **Estado**: completado
- **Dependencias**: T-07, T-17
- **Verificación**: `uv run pytest tests/test_generate_preparation.py tests/test_input_preparation.py` en verde (historial).
- **Changelog**: El CLI conserva la letra y el estilo originales, permite preparar entradas offline y registra la procedencia sin perder los tags.

### T-19 — Preflight nativo de tokens y captura de entradas efectivas
- **Descripción**: Presupuesto real de tokens antes de aceptar letra y estilo, sin truncar en silencio.
- **Estado**: completado
- **Dependencias**: T-06, T-18
- **Verificación**: `uv run pytest apps/engines/acestep/tests/test_preflight.py` en verde (historial).
- **Changelog**: La generación comprueba el presupuesto real antes de aceptar letra y estilo y registra entradas efectivas verificables.

### T-20 — Arquitectura de despliegue Docker y Ollama compartido
- **Descripción**: Registrar la arquitectura de despliegue (producto en Docker sobre WSL2, Ollama compartido) en `docs/arquitectura/`.
- **Estado**: completado
- **Dependencias**: T-00
- **Archivos**: `docs/decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md`, `docs/arquitectura/entorno.md`, `CONTINUE-HERE.md`. `docker-compose.yml` y los Dockerfiles sólo se cotejan; no cambia la arquitectura ni se arrancan engines GPU.
- **TDD n/a: prosa**. Se corrigen referencias de implementación pendientes que ya contradicen los recibos Docker de M1; sin cambios de código, modelos ni decisiones.
- **Verificación**: ADR-0035 y `docs/arquitectura/entorno.md` coherentes con `docker-compose.yml`; `docker compose config -q` sin errores.
- **Verificación ejecutada (2026-11-06)**: `docker compose --project-directory <repo> --project-name music-studio-m0-t20-verificacion --env-file <privado> --file docker-compose.yml config -q` → exit 0; también `--profile studio`, `--profile engines` y `--profile '*'` → exit 0. La resolución por defecto no activa servicios, por eso se cotejan además los perfiles explícitos. JSON completo: cinco servicios, puertos sólo loopback, server→mock interno; sólo los dos engines del perfil `engines` declaran GPU. Sin servicio Ollama/ComfyUI implementado ni contenedores arrancados. Recibo privado: `.cache/dev-cycle/20261106-m0-t20/compose-verification.json`. TDD n/a: prosa; no se acredita conectividad Ollama ni ejecución GPU.
- **QA documental**: PASS_DOCUMENTARY; ledger-lint exit 0 (0 incoherencias/25 avisos históricos), coverage-check exit 0 con `applies:false` por plan sin UI, sin porcentaje medido. Aviso de diff degradado conservado: el delta propio congelado sí contiene sólo tres Markdown. Dos SHA documentales y seis de configuración iguales; 50 destinos/4 anclas, ninguno roto; diff-check exit 0. Sin qa-gate/Playwright ni runtime. Informe y recibos en `.cache/dev-cycle/20261106-m0-t20/qa/`; aceptación del orquestador limitada a T-20.
- **Changelog**: Documenta el despliegue en Docker sobre WSL2 y el uso compartido de la GPU con Ollama.

## Revisión de dos lentes — intento 1: T-20, arquitectura documentada — sin gaps

Lentes A/B sobre tres archivos propios congelados desde `6ac6920`; scope exit 0, sin avisos ni exclusiones nuevas. C/D no aplican al delta documental. Ambas leen el diff completo y no encuentran Critical/Important/Minor: fuentes, comandos y separación CPU/mock frente a GPU/Ollama coherentes. A verifica ledger, tres SHA propios y seis de configuración; B repite `config -q` con default/studio/engines/* (exit 0) y comprueba 52 destinos locales, ninguno roto. Raw en `.cache/dev-cycle/20261106-m0-t20/review-1/`; QA documental posterior aprobada y T-20 cerrada. No se cierra M0/M1 ni se aprueba conectividad o inferencia por estos checks.

## Revisión de dos lentes — intento 1: T-16, captura compatible — sin gaps

Lentes A/B sobre diez archivos congelados desde `3dede62`; scope exit 0, sin exclusiones ni avisos; selector C/D false. Cero Critical/Important/Minor. A verifica conformidad, cinco RED, cobertura oficial 16/16 líneas del delta y ejecuta 19 tests del snapshot; B ejecuta 67 tests y siete sondas adicionales. Observaciones runtime/resolver, privacidad, compatibilidad y límites documentados coherentes. Raw en `.cache/dev-cycle/20261106-m0-t16/review-1/`. Esta aprobación del delta no cierra T-16 ni sustituye QA.

| Criterio | A | B | Evidencia |
|---|---|---|---|
| Huella real tipada y backend observado | ✓ | ✓ | Resolver y llamada LM, sin fallback al plan |
| Compatibilidad, rechazo semántico y modo fuerte | ✓ | ✓ | Matriz versión/presencia/malformados |
| Privacidad y publicación exacta | ✓ | Sin defectos | Sin códigos en claro, payload preservado |
| Alcance, constitución, TDD y límites | ✓ | Sin defectos | Cinco RED, revisión completa y fuentes congeladas |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin hallazgos | T-16 | No necesaria | `.cache/dev-cycle/20261106-m0-t16/review-1/verdicts.md` |

**QA posterior, no aprobada:** una corrida ampliada de 433 tests: 422 pass, 9 skip, 2 fail, exit 1 (23,29 s). Fallan `test_native_child_creation_preserves_directory_identity` y `test_native_empty_enumeration_preserves_directory_identity`, con atributos Windows 16→1572880 y FileId estable. Fixture ULID corregida ya pasa. Diez SHA propios y 71 ajenos intactos; seis recibos históricos válidos y seis rechazos fuertes correctos. Sin Torch/GPU/Ollama. Ruff/ledger exit 0. Evidencia `.cache/dev-cycle/20261106-m0-t16/qa-final/`; no se repite para obtener verde. Depuración sistemática en curso: aún no está probada la clasificación baseline/regresión ni la causa del cambio de atributos.

**Depuración posterior (fases 1–3):** AST exacto de `_directory_identity` actual y base `3dede62`, con el mismo SHA, reproduce determinísticamente falsa desigualdad con 0x10→0x180010 y dev/ino/mode/tag iguales. Una máscara acotada sólo en memoria conserva esa identidad y mantiene rechazo de reparse/tipo y diferenciación por dev/ino/mode/otros atributos. Prueba nativa única: ambos directorios nacen ya con 0x180010 y no cambian; no reproduce el disparador intermitente del SO. La causa del falso cambio de identidad sí está aislada al código previo, no a la nueva captura. No se atribuye a ningún proveedor del SO. Evidencia `.cache/dev-cycle/20261106-m0-t16/windows-diagnosis/`; se autoriza corrección mínima con nuevo TDD antes de otra revisión y QA.

**Fix2, fase 4 previa a revisión/QA:** RED `test_residency_metadata_preserves_same_directory[pinned]` falló con `AssertionError: 524304 != 16`, exit 1, 2026-11-06T01:37:49+01:00; después del cambio mínimo el mismo FQ pasa. Regresión final 22 pass; paquete completo `audio-post`: 231 pass/9 skip, exit 0, Ruff/formato verdes. Pipeline sólo excluye PINNED/UNPINNED además del bit ya excluido; conserva dev/ino/mode/tag, resto de atributos y guardas. Cobertura oficial combinada del paquete 87,53 %, pipeline 95,56 %; sentencia Return que contiene la expresión cambiada cubierta (línea 32, expresión 38). No es un porcentaje de todas las líneas nuevas. Evidencia `.cache/dev-cycle/20261106-m0-t16/fix2/{evidence.md,red-pinned.log,full-final.log,coverage-final.json,freeze.json}`. Candidato de conocimiento propuesto, sin curación ni exportación. QA anterior sigue roja; hace falta nueva QA del conjunto.

## Revisión de dos lentes — intento 2: T-16, identidad Windows — sin gaps

Traspaso del intento 1 conservado: seis archivos de captura/lectura sin cambios ni evidencia nueva que reabra su aprobación. Catorce archivos congelados desde `3dede62`, scope exit 0 sin exclusiones/avisos, C/D false. A/B leen el diff completo y evalúan el incremental. A ejecuta22 tests y verifica14 SHA, AST/coverage y ledger; B ejecuta19 pass/3 deselected para limitar escrituras fuera de sus temporales. Esos tres casos sí se ejecutan en la QA2 posterior.

| Criterio | A | B | Evidencia |
|---|---|---|---|
| Alcance adicional justificado | ✓ | Sin defectos | Postproceso/publicación, Archivos de T-16 |
| Residencia mutable conserva identidad | ✓ | ✓ | Cinco variantes y transiciones inversas |
| Sustitución/dev/ino/mode/otros atributos diferenciados | ✓ | ✓ | Controles con flags iguales y sustitución nativa |
| Reparse/tag/no directorio rechazados | ✓ | ✓ | Guardas intactas, flags combinados |
| TDD, documentación y límites coherentes | ✓ | ✓ | RED real, propuesta pendiente, sin afirmaciones GPU |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin hallazgos | T-16 | No necesaria | `.cache/dev-cycle/20261106-m0-t16/review-2/verdicts.md` |

**QA2 posterior aceptada sólo como software CPU:** única corrida437 pass/9 skip/0 fail,446 casos,23,11 s; dos nativas antes rojas y13 regresiones nuevas pasan. Delta18/18 sentencias afectadas100 %, directorios completos74,56 % combinado (no80 % global). Scope14 exit0; Ruff8/ledger exit0. Activos históricos íntegros y archivos ajenos preservados contra estado al retomar. Candidato pendiente, sin promoción ni exportación. [Informe](testing/condicionamiento-cpu-2026-11-06.md); raw `.cache/dev-cycle/20261106-m0-t16/qa-fixed2/`. T-16 continúa en-progreso; entrega en su rama hasta completar comparaciones reales. No se integra en main ni se cierran M0/M1 por estos resultados.
