---
generacion:
  fuente: estimado        # redactado a mano el 2026-09-28; sin usage-meter
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — M0 · Entorno, motor por CLI y elección de modelo

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-28 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | n/a |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **única fuente de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Preparación | 2 | 2 | 100% | 0 / 6h | 0 / 2h | 0 / 0.5h | 0 / — |
| Fase 2 — Cimientos compartidos | 3 | 3 | 100% | — / 26h | — / 13h | — / 3.3h | — / — |
| Fase 3 — Motor musical | 3 | 3 | 100% | — / 19h | — / 9.5h | — / 2.4h | — / — |
| Fase 4 — Medición y elección | 5 | 12 | 42% | 0 / 37h | 0 / 15h | 0 / 3.8h | 0 / — |
| **TOTAL** | **13** | **20** | **65%** | **— / 88h** | **— / 39.5h** | **— / 10h** | **— / —** |

> Horas orientativas (proyecto personal, sin presupuesto). La T-12 es opcional (8 h): sin ella son 80 h.

---

## Fase 1 — Preparación

**Estado**: completado · **Estimado**: 6h · **Real**: —

### T-00 — Prerrequisitos manuales de la máquina

- **Descripción**: Dejar la máquina lista antes de crear ningún fichero pesado. Es una tarea **manual del propietario**; la IA la guía y comprueba el resultado.
- **Estado**: completado
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Supervisión**: est. 0.1h (≈25 % IA) · real —
- **Dependencias**: ninguna
- **Tipo**: devops
- **Archivos**: `%UserProfile%\.wslconfig` (fuera del repositorio, configuración de WSL), filtro de Synology Drive
- **Verificación** (ejecutada 2026-09-28 — salida: RTX 5070 12227MiB · Mem total 23 · Node 22.23.2 / pnpm 9.12.0 / uv 0.12.19 / git 2.47.1 · filtro confirmado por el propietario):
  - `docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi` → lista `NVIDIA GeForce RTX 5070` y `12227MiB`
  - `wsl -e free -g` → `Mem total` ≥ 22
  - `node --version; pnpm --version; uv --version; git --version` → Node 22.x y las demás versiones presentes
  - lectura: captura del filtro de Synology Drive con las exclusiones de ADR-0005

**Criterios de aceptación**
- [x] Filtro de sincronización de Synology Drive configurado según [ADR-0005](../../decisiones/ADR-0005-todo-en-la-carpeta.md): se excluyen `data/db`, `data/tmp`, `data/cli`, `data/logs`, `data/trash`, `models`, `tools`, `.cache`, `node_modules`, `.venv`, `.next`, `eval/takes` y `eval/capabilities`.
- [x] `%UserProfile%\.wslconfig` con `memory=24GB` y `swap=16GB`; `wsl --shutdown` y Docker Desktop reiniciados. *(Creado y aplicado el 2026-09-28: WSL ve 23 GB.)*
- [x] Python aislado del de la máquina: intérprete 3.12.14 gestionado por uv en `.cache/uv/python/`, `.venv/` en la raíz, `uv.toml` (`only-managed`, `python-downloads = manual`) y `scripts/env.ps1`/`env.sh`. Sin accesos directos en `%USERPROFILE%\.local\bin`.
- [x] La GPU es visible dentro de un contenedor.
- [x] Node 22 LTS, pnpm, uv y git instalados.
- [x] Al menos 80 GB libres en C: para las imágenes (~10–15 GB cada una) y los pesos.

**Notas**: comprobación 2026-09-28 — ✅ `docker run --gpus all …nvidia-smi` → `NVIDIA GeForce RTX 5070, 12227 MiB` · ✅ disco C: 623 GB libres · ✅ node v22.23.2, uv 0.12.19, git 2.47.1 · ✅ pnpm 9.12.0 (standalone en `%PNPM_HOME%\bin`; `env.ps1` lo añade al PATH si la sesión es anterior) · ✅ `.wslconfig` aplicado (WSL ve 23 GB) · ✅ `.venv` con Python 3.12.14 aislado (uv, `.cache/uv/python`) · ✅ filtro de Synology configurado (confirmado por el propietario). `pnpm-lock.yaml` generado y `bootstrap.ps1` probado de cero con pnpm incluido.
- **Changelog**: Máquina preparada: GPU visible en Docker, WSL con 24 GB, herramientas instaladas y carpetas pesadas fuera de la sincronización.

### T-01 — Esqueleto del repositorio

- **Descripción**: Crear la estructura de [sistema.md](../../arquitectura/sistema.md) §2, el tooling Python/Node y las reglas de exclusión. Todavía sin código funcional.
- **Estado**: completado
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real 0.14h (estimado: 8 min de agente)
- **Supervisión**: est. 0.4h (≈25 % IA) · real —
- **Dependencias**: T-00
- **Tipo**: devops
- **Archivos**: `.gitignore`, `.gitattributes`, `.editorconfig`, `.env.example`, `.python-version`, `uv.toml`, `scripts/env.ps1`, `scripts/env.sh`, `scripts/bootstrap.ps1`, `scripts/bootstrap.sh`, `scripts/init_env.py`, `README.md`, `CLAUDE.md`, `pyproject.toml` (workspace de uv), `package.json`, `pnpm-workspace.yaml`, `.pre-commit-config.yaml`, `apps/`, `packages/`, `scripts/`, `models/.gitkeep`, `data/.gitkeep`, `tools/.gitkeep`, `eval/briefs/`, `eval/results/`
- **Verificación** (ejecutada 2026-09-28 — salida: 4 · tracked · 1 · ok · ok):
  - `(git check-ignore models/x.safetensors data/db/studio.sqlite eval/takes/a.wav .env | Measure-Object).Count` → `4`
  - `git check-ignore -q models/models.lock.json || git check-ignore -q eval/briefs/B-02.txt || git check-ignore -q eval/results/x.md || echo tracked` → `tracked`
  - `uv run scripts/init_env.py && uv run scripts/init_env.py && grep -c STUDIO_ENGINE_TOKEN .env` → `1` (idempotente: no regenera el token)
  - `uv run python -c "print('ok')"` → `ok`
  - `Remove-Item -Recurse .venv; .\scripts\bootstrap.ps1; .\.venv\Scripts\python -c "print('ok')"` → `ok` (el entorno se reconstruye desde los locks)

**Criterios de aceptación**
- [x] `git init` con rama `main`. `.gitignore` según ADR-0005, con el patrón exacto para `eval/`: `eval/*` · `!eval/briefs/` · `!eval/results/` · `eval/results/*` · `!eval/results/*.md` (git no reincluye ficheros de un directorio excluido). Los locks se versionan; los `.gitkeep` se añaden con `git add -f`.
- [x] Workspace de uv con los miembros `packages/*`, `apps/server`, `apps/engines/common` y `apps/engines/mock` (vacíos, **ninguno con torch**). `apps/engines/acestep` y `apps/engines/analysis` quedan **fuera** del workspace, con su propio `pyproject.toml`/`uv.lock` ([sistema.md](../../arquitectura/sistema.md) §4). Workspace de pnpm con `apps/web` (vacío). Pre-commit con ruff y prettier.
- [x] `.env.example` con las variables `STUDIO_*` y las de caché de [convenciones.md](../../arquitectura/convenciones.md) §4. `scripts/init_env.py` crea `.env` a partir del ejemplo y genera **una sola vez** `STUDIO_ENGINE_TOKEN` (persistente, lo usan el CLI, el server y los engines).
- [x] `CLAUDE.md` actualizado con los comandos de desarrollo.
- [x] Remoto configurado como copia de seguridad del código, con un nombre sin marcas de terceros: `daycry/music-studio`, **público** por decisión del propietario ([ADR-0021](../../decisiones/ADR-0021-repositorio-publico.md)); el `main` antiguo queda en `archive/legacy-main`.
- [x] **Reconstrucción en un comando:** `scripts/bootstrap.ps1` (y `bootstrap.sh`) carga `env.ps1`, ejecuta `uv python install` (lee `.python-version`), `uv sync --frozen` y `pnpm install --frozen-lockfile`. `uv.lock`, `pnpm-lock.yaml` y `.python-version` se versionan. Probado borrando `.venv/` y `node_modules/` y relanzando el script.

---

**Notas**: implementada el 2026-09-28 por el agente `implementer` (commits `1994f64` en `main` y `4194129` en `m0/t-01-esqueleto`) y verificada de forma independiente por el orquestador: `.venv` sin torch (22 paquetes), sin accesos directos fuera de la carpeta, token de `init_env.py` estable entre ejecuciones y `.env` ignorado. `pnpm` no instalado: `bootstrap` avisa y lo omite (se revalida al cerrar T-00). Remoto: `main` subido con `--force-with-lease` tras copiar el `main` anterior (`5455e68`) a `archive/legacy-main`; rama `m0/t-01-esqueleto` subida; auth con `gh` como helper local.
- **Changelog**: Repositorio inicializado con el esqueleto del monorepo y un script que reconstruye el entorno de desarrollo desde los ficheros de bloqueo.

## Fase 2 — Cimientos compartidos

**Estado**: completado · **Estimado**: 26h · **Real**: —

### T-02 — `packages/weights`: lock, descarga verificada, auditor de pickle y herramientas

- **Descripción**: Descarga reproducible y segura de modelos y herramientas, según [ADR-0006](../../decisiones/ADR-0006-seguridad-de-pesos.md).
- **Estado**: completado
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real 0.4h (estimado: ~25 min de agente en dos tramos; interrumpido por el límite de uso y reanudado)
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `packages/weights/` (lock, verify, seal, audit_pickle, convert), `scripts/fetch_models.py`, `scripts/fetch_tools.py`, `models/models.lock.json`, `tools/tools.lock.json`, `packages/weights/tests/`
- **Verificación** (ejecutada 2026-09-28 por el orquestador — salida: 24 passed · ace-step-1.5 OK · ffmpeg win64-lgpl OK):
  - `uv run pytest packages/weights -q` → todos en verde (hash correcto e incorrecto, sello, pickle tensorial convertido, pickle malicioso rechazado, `.py` remoto con hash distinto rechazado)
  - `uv run scripts/fetch_models.py --model ace-step-1.5 --check` → `OK` para todos los ficheros del lock
  - `uv run scripts/fetch_tools.py --check` → `ffmpeg win64-lgpl OK`

**Criterios de aceptación**
- [x] `models.lock.json` registra, por modelo: repo HF, **revisión (commit)**, ficheros (ruta relativa, SHA-256, bytes, formato, licencia), el `.py` remoto con su hash y los pickle con el hash del original y el del convertido.
- [x] El lock incluye:
  - ACE-Step 1.5: bundle con turbo, LM 1.7B, VAE y Qwen3-Embedding; repos separados de sft, base y LM 0.6B; XL-turbo como opcional;
  - Qwen3-ASR-1.7B, Qwen3-ForcedAligner-0.6B, LAION `larger_clap_music` (convertido desde `.bin`), Audiobox Aesthetics (`model.safetensors`) y beat_this (convertido desde `.ckpt`).
- [x] Auditor y conversor **sin torch y sin `pickle.load`**: primero recorre los opcodes con `pickletools` y rechaza cualquier `GLOBAL`/`STACK_GLOBAL` que no esté en una **allowlist** (`torch._utils._rebuild_tensor_v2`, `torch.FloatStorage`/`HalfStorage`/`BFloat16Storage`, `collections.OrderedDict`, y para los `.ckpt` de Lightning también `builtins` inocuos). Después reconstruye los tensores con un intérprete propio (subclase de `pickle.Unpickler` con `find_class` restringido a la allowlist, que devuelve marcadores) más `numpy` sobre los storages del zip. En los `.ckpt` de Lightning extrae **solo** el `state_dict`. Escribe safetensors con `safetensors.numpy`.
- [x] `fetch_models.py` es idempotente, calcula el hash completo al descargar y escribe el sello `.verified`. Usa `HF_HOME=models/.hf-cache`. **Estructura en disco:** `models/<model_id>/`; en ACE-Step, `models/ace-step-1.5/checkpoints/` replica la estructura que espera upstream (`ACESTEP_CHECKPOINTS_DIR`), con un subdirectorio por repo de HF (p. ej. `acestep-v15-turbo/`, `acestep-5Hz-lm-0.6B/`, `vae/`, `Qwen3-Embedding-0.6B/`). Los pickle convertidos sustituyen al original en su sitio, con la extensión `.safetensors`, y el original se borra.
- [x] `fetch_tools.py` descarga ffmpeg BtbN `win64-lgpl` a `tools/ffmpeg/` y lo verifica con el lock.

**Notas**: commit `1947f02` en `m0/t-02-weights`. Verificación independiente del orquestador: 24 tests en verde; `--check` en OK para los 6 modelos (`ace-step-1.5`, `qwen3-asr-1.7b`, `qwen3-forcedaligner-0.6b`, `clap-larger-music`, `audiobox-aesthetics`, `beat-this`) y para ffmpeg (BtbN `autobuild-2026-09-26-13-03`, LGPL con lame/soxr/opus); 0 ficheros pickle en `models/`; `.hf-cache` vacío (se corrigió una copia duplicada de ~20 GB: ahora se mueve en lugar de copiar); `packages/weights` sin torch. En disco: `models/` 27 GB, `tools/` 0,4 GB. Pickles convertidos: `silence_latent.pt` ×3 (turbo/sft/base), CLAP `pytorch_model.bin` (555 tensores) y beat_this `final0.ckpt` (166 tensores, solo `state_dict`). Licencias sin discrepancias con `docs/legal/licencias.md`. **TDD n/a**: la tarea arrancó antes de activar `tdd` en `.claude/dev.json`. **Pendiente para la revisión de dos lentes de la Fase 2**: (1) el auditor rechaza siempre `STACK_GLOBAL` (protocolo 4+), una decisión *fail-closed* que puede bloquear pickles futuros; (2) el bundle `ACE-Step/Ace-Step1.5` se reparte en 4 subdirectorios de `checkpoints/` (una interpretación de «un subdirectorio por repo», que hay que confirmar contra lo que espera upstream en T-06).
- **Changelog**: Descarga reproducible y verificada (SHA-256, revisión fijada) de los modelos de ACE-Step y de evaluación, con conversión segura de pickle a safetensors y ffmpeg LGPL.

### T-03 — `packages/engine-contract` + `apps/engines/common` + `engine-mock`

- **Descripción**: El contrato `/v1` de [contrato-engines.md](../../arquitectura/contrato-engines.md) como código compartido, el servidor base de cualquier engine y el mock. Al cerrar esta tarea **el contrato queda congelado**.
- **Estado**: completado
- **Tiempo humano**: est. 12h · real —
- **Tiempo IA (ejec.)**: est. 6h · real —
- **Supervisión**: est. 1.5h (≈25 % IA) · real —
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivos**: `packages/engine-contract/` (JobRequest, Event, Telemetry, ModelDescriptor, códigos de error), `packages/contracts/engine-v1.json` (generado), `scripts/export_contracts.py`, `apps/engines/common/` (servidor FastAPI `/v1`, supervisor del proceso hijo, VramGuard, CancelToken, token interno), `apps/engines/mock/`, `tests/`, `conftest.py`, `pytest.ini`, `.gitignore`, `pyproject.toml`, `uv.lock`, `docs/legal/licencias.md`, `docs/arquitectura/contrato-engines.md`, `docs/README.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`
- **Alcance auxiliar**: dependencias y lock reproducibles, configuración de tests locales y registro de licencias necesarios para implementar y verificar el contrato; evidencias de QA y documentación de uso/reanudación. Sin nuevas funciones de producto.
- **Trazabilidad de reanudación (2026-10-05)**: código heredado conservado; sus rojos iniciales no son verificables en esta sesión. Las correcciones de la revisión se ejecutan con TDD y evidencia por defecto; no se atribuye TDD retrospectivo al código heredado. El usuario pidió continuar tras la pausa de coordinación; se preservan los cambios existentes y se retoman las correcciones con responsables de ficheros definidos.
- **Evidencia TDD de corrección A1**: RED: `packages/engine-contract/tests/test_contract.py::test_exported_event_schema_rejects_invalid_payload[progress-data1]` falló con `AssertionError: El esquema exportado debe rechazar el mismo payload que Pydantic` (esquema aceptó `fraction=2`) · 2026-10-05. GREEN: 9 variantes de evento inválido rechazadas; 14 tests del paquete en verde, referencias del esquema autónomo y campos opcionales comprobados. Contrato regenerado desde los modelos.
- **Verificación**:
  - `uv run pytest packages/engine-contract apps/engines/common apps/engines/mock -q` → verde
  - `uv run scripts/export_contracts.py --check` → `engine-v1.json up to date`
  - `uv run pytest -q tests/test_no_pickle.py` → verde (búsqueda por **AST** de llamadas a `torch.load`, `pickle.load(s)` y `Unpickler` en `apps/` y `packages/`; permitido solo lo listado en `tests/no_pickle_allowlist.txt` con su motivo: el `Unpickler` restringido del auditor)

**Criterios de aceptación**
- [x] Modelos Pydantic compatibles con Python 3.11 y 3.12, sin torch. `engine-v1.json` se genera a partir de ellos y un test comprueba que coincide con el versionado.
- [x] Servidor `/v1` con: health (incluye `contract_version`), models, load, unload, estimate, `jobs` (`202`/`409 BUSY`), `GET jobs/{id}`, eventos NDJSON con `seq` y reenganche mediante `?after=`, y `DELETE`. Exige `X-Studio-Engine-Token`.
- [x] El modelo corre en un **proceso hijo**; `unload` lo termina. El proceso padre no importa torch y lee la VRAM total y libre con **NVML** (`nvidia-ml-py`). `POST /v1/jobs` carga el modelo de forma implícita si no está cargado (evento `stage: loading_model`).
- [x] VramGuard: `cap = free − STUDIO_VRAM_MARGIN_MB` al cargar; registra `vram_peak_mb` y `spilled`; excederlo devuelve `VRAM_EXCEEDED`. Tests con una GPU simulada.
- [x] Cancelación cooperativa que limpia `data/tmp/<job_id>/`. Evento terminal único (`done`, `error` o `cancelled`).
- [x] `engine-mock` implementa **todas las tareas del catálogo** ([contrato-engines.md](../../arquitectura/contrato-engines.md) §5), cada una con su salida sintética: audio en barrido de 48 kHz con la duración pedida, `delta` de texto en streaming con letra etiquetada, PNG, MP4 y JSON. Declara todas las features, pone `audio.beats` con `device: cpu` y admite `MOCK_STAGE_DELAY_MS` y las directivas `@mock:fail=`, `@mock:fail_once=` y `@mock:retryable` (§7).

**Correcciones de revisión ejecutadas (2026-10-05)**
- RED: `apps/engines/common/tests/test_review_regressions.py::test_timeout_includes_child_model_load` falló con `2,531 s >= 1,8 s` · 2026-10-05.
- RED: `apps/engines/common/tests/test_review_regressions.py::test_health_during_cancel_cleanup_stays_busy` falló con `HTTP 500 != 200` · 2026-10-05.
- RED: `apps/engines/common/tests/test_review_regressions.py::test_vram_telemetry_is_per_job` falló con `pico 2450 != 100 MB` · 2026-10-05.
- RED: `apps/engines/common/tests/test_review_regressions.py::test_container_data_mount_is_accepted_without_allowing_host_paths` falló con `ValueError al aceptar montaje contractual` · 2026-10-05.
- RED: `apps/engines/common/tests/test_review_regressions.py::test_load_does_not_block_async_events_loop` falló con `heartbeat 1,359 s >= 0,2 s` · 2026-10-05.
- RED: `apps/engines/common/tests/test_review_regressions.py::test_health_reads_loaded_snapshot_once` falló con `HTTP 500 != 200` · 2026-10-05.
- GREEN: regresiones 7 passed, con BUSY concurrente y cancelación durante carga; montaje contractual simulado, sin Docker/GPU.
- **Verificación ejecutada**: `uv run pytest packages/engine-contract apps/engines/common apps/engines/mock -q` → `35 passed in 8.62s`; `uv run scripts/export_contracts.py --check` → `engine-v1.json up to date`; `uv run pytest -q tests/test_no_pickle.py` → `8 passed in 0.05s`.
- **Corrección D2 (2026-10-05)**: RED: `test_submit_input_validation_does_not_block_async_events_loop` falló con `heartbeat 0.297 s >= 0.2 s`, `1 failed in 0.96s`, antes de editar el servidor. GREEN aislado: `1 passed in 0.98s`; regresiones: `12 passed in 7.60s`. Reserva BUSY bajo lock, validación fuera y liberación en `finally`; hash incremental de entradas y salidas. Verificación T-03: `40 passed in 10.56s`, contrato al día, AST `8 passed in 0.05s`; ruff verde y `2 files already formatted`. Cubiertos errores de hash/ausencia/E/S, reintento e idempotencia. La corrección reutilizó un agente disponible al rechazar la herramienta el despacho de otro hilo; el autor no revisará su cambio.
- **Changelog**: Contrato /v1 compartido, ejecución en proceso hijo, eventos reanudables, cancelación y mock de todas las capacidades, con protección de VRAM y plazo de carga.

### T-04 — `packages/audio-post` + manifiesto v1 + verificador

- **Descripción**: El post-proceso y el manifiesto que usarán el CLI (M0) y el worker del server (M1), según [pipeline-audio.md](../../arquitectura/pipeline-audio.md) y [datos.md](../../arquitectura/datos.md) §3.
- **Estado**: completado
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-02 (ffmpeg en `tools/`)
- **Tipo**: backend
- **Archivos**: `packages/audio-post/`, `packages/contracts/manifest-v1.schema.json`, `packages/contracts/examples/`, `packages/contracts/manifest_writer` (en `audio-post` o paquete propio), `scripts/verify_manifest.py`, `uv.lock`, tests, `docs/arquitectura/pipeline-audio.md`
- **Alcance auxiliar**: ejemplos exigidos por la verificación y actualización del lock para las dependencias del post-proceso.
- **Evidencia TDD de reanudación (2026-10-05)**:
  - RED: `packages/audio-post/tests/test_audio_post.py::test_invalid_sample_rate[nan]` falló con `DID NOT RAISE ValueError` · 2026-10-05; corrección verificada en verde.
  - RED: `packages/audio-post/tests/test_manifest_errors.py::test_photo_input_only_reference` falló con `DID NOT RAISE ValueError` · 2026-10-05; corrección verificada en verde.
  - RED: `packages/audio-post/tests/test_manifest_errors.py::test_malformed_inputs_schema_error[None]` falló con `TypeError: NoneType is not iterable` · 2026-10-05; corrección verificada en verde.
  - Código heredado conservado sin atribuirle evidencia TDD original. El fallo de staging observado dentro de la suite no se cuenta como rojo aislado.
- **Verificación**:
  - `uv run pytest packages/audio-post -q` → verde
  - `uv run scripts/verify_manifest.py packages/contracts/examples/` → `all valid`

**Criterios de aceptación**
- [x] Validación de duración (±5 %), NaN/Inf, silencio (RMS > −60 dBFS) y clipping sostenido.
- [x] `master.flac` (24 bit, frecuencia nativa, **sin normalizar**) y `listen.mp3` (320 kbps), llevado a −14 LUFS ±0,5 mediante **ganancia lineal**, con **true peak ≤ −1 dBTP medido con ffmpeg `ebur128=peak=true`**. Si hace falta, limitador, que queda anotado en `post`.
- [x] `peaks.json` con ~2.000 pares min/max por canal.
- [x] `manifest-v1.schema.json` con todos los campos de datos.md §3, más ejemplos: `audio_take`, `cli_run`, `image` y proveedor externo. El escritor calcula `commercial_use` como AND de todo lo usado.
- [x] `verify_manifest.py` valida el esquema y los hashes de las salidas, e ignora campos desconocidos.

---

**Correcciones de revisión ejecutadas (2026-10-05)**
- RED: `packages/audio-post/tests/test_manifest_errors.py::test_audio_take_requires_song` falló con `DID NOT RAISE ValueError` · 2026-10-05.
- RED: `packages/audio-post/tests/test_manifest_errors.py::test_verifier_rejects_commercial_permission_tampering[models]` falló con `DID NOT RAISE ValueError` · 2026-10-05.
- RED: `packages/audio-post/tests/test_manifest_errors.py::test_verifier_rejects_false_aggregate` falló con `DID NOT RAISE ValueError` · 2026-10-05.
- RED: `packages/audio-post/tests/test_manifest_errors.py::test_cli_directory_ignores_non_manifest_json` falló con `exit 1, esperado 0` · 2026-10-05.
- RED: `packages/audio-post/tests/test_manifest_errors.py::test_cli_directory_does_not_hide_invalid_manifest[manifest-v2.json-{}]` falló con `exit 0, esperado 1` · 2026-10-05.
- GREEN: directorio real con master/listen/peaks/manifiesto; detección de audio manipulado, JSON malformado y versión desconocida.
- **Verificación ejecutada**: `uv run pytest packages/audio-post -q` → `53 passed in 2.33s`; `uv run scripts/verify_manifest.py packages/contracts/examples/` → `all valid (4 manifests)`; ruff → `All checks passed!` y `6 files already formatted`.
- **Changelog**: Post-proceso con master FLAC de 24 bit sin normalizar, MP3 de escucha medido y picos de onda, más manifiestos inmutables y verificación de procedencia y hashes.

## Fase 3 — Motor musical

**Estado**: completado · **Estimado**: 19h · **Real**: —

### T-05 — Imagen `engine-acestep` para sm_120

- **Descripción**: El contenedor del motor musical con las versiones de [entorno.md](../../arquitectura/entorno.md) §2.
- **Estado**: completado
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-03
- **Tipo**: devops
- **Archivos**: `apps/engines/acestep/` (imagen, dependencias fijadas, arranque y pruebas de entorno; adapter funcional en T-06), `.dockerignore`, `docker-compose.yml` (perfil `engines`), `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/` (incluye recibo final de T-03/T-04 pendiente de integrar)
- **Verificación**:
  - `docker compose --profile engines build engine-acestep` → build OK
  - `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q` → verde (pruebas de entorno **dentro** del contenedor; adapter funcional en T-06)
  - `docker compose run --rm engine-acestep python -c "import torch;assert 'sm_120' in torch.cuda.get_arch_list();a=torch.ones(64,64,device='cuda',dtype=torch.bfloat16);print((a@a).sum().item())"` → `262144.0`
  - `docker compose run --rm engine-acestep sh -c "ffmpeg -buildconf | grep -c -e enable-gpl -e enable-nonfree"` → `0`

**Criterios de aceptación**
- [x] Base `nvidia/cuda:12.8.1-runtime-ubuntu22.04`, Python 3.11 instalado con `uv python install` y el repo de ACE-Step 1.5 fijado a un tag o commit, instalado con `uv sync --frozen --no-dev`.
- [x] ffmpeg BtbN `linux64-lgpl-shared`, con las `.so` en `LD_LIBRARY_PATH`. `-buildconf` incluye lame, soxr y opus.
- [x] La imagen copia e instala `packages/engine-contract` y `apps/engines/common` en su entorno Python 3.11. Mounts según [contrato-engines.md](../../arquitectura/contrato-engines.md) §6: `models/`→`/models` y `data/`→`/data` en solo lectura, y `data/tmp/`→`/data/tmp` en lectura/escritura. Variables: `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `ACESTEP_LM_BACKEND=pt`, `ACESTEP_CHECKPOINTS_DIR`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` y el token del engine.
- [x] Puerto publicado como `127.0.0.1:8101:8101`. Sin xformers ni flash-attn. El log de arranque indica la atención (SDPA) y la versión de torch.

**Reanudación — 2026-10-05:** T-03 (`af181de`) y T-04 (`9da20f0`) integradas mediante commits separados y fast-forward a `main`, con recibo final `6b371e9`; los tres commits están publicados. Trabajo actual en `m0/t-05-acestep-image`. Se han preservado los journals. Docker Desktop 4.92.0 / Engine 29.8.0 accesibles con escalación; WSL/Ollama accesible y sin modelos cargados. VRAM inicial: 1.400 / 12.227 MiB. No hubo que descargar ni recargar ningún modelo de Ollama. Brief regenerado por `task-brief.py` y subagente fresco. Ventana de implementación cerrada: `usage-meter` degradó a `fuente: estimado`, sin tokens ni horas IA medidos; 54 minutos de reloj no se atribuyen a ejecución IA. T-05 no se declara completada.

**Verificación parcial ejecutada — 2026-10-05:**
- Build exacto → `Image music-studio/engine-acestep:m0-t05 Built`, exit 0.
- Pytest exacto en contenedor → `4 passed in 7.01s`, exit 0; arranque `engine-acestep: attention=SDPA torch=2.10.0+cu128`.
- FFmpeg exacto → stdout `0`, exit 1 esperado de `grep` sin coincidencias. Los tests verifican LGPL shared, lame/soxr/opus e importación real de torchcodec.
- Probe CPU adicional `CUDA_VISIBLE_DEVICES= python -c 'import acestep.handler'` → exit 0, sin cargar modelos. Matplotlib utiliza caché temporal en `/tmp` al no poder crear `/studio/.config/matplotlib`; bitsandbytes ausente usa AdamW estándar.
- `uv pip check --python /opt/acestep/.venv/bin/python` → 152 paquetes, exit 1: única incompatibilidad `nano-vllm` → `flash-attn` no instalado, excluido explícitamente por el criterio SDPA/backend `pt`. No se declara check verde; su alcance se contrasta en revisión.
- **RED:** `tests/test_environment.py::test_startup_log` falló porque `attention=SDPA torch=2.10.0+cu128` no estaba en stdout (`command-executed`) · 2026-10-05. **GREEN:** `1 passed in 5.13s`.
- **TDD n/a:** ensamblado Docker, locks y compose (configuración); el comportamiento del log sí tiene RED/GREEN.
- Recibos conservados en [testing/t05/raw](testing/t05/raw/), con códigos y comandos en [receipts.json](testing/t05/raw/receipts.json). La factoría HTTP y la generación no se acreditan: corresponden a T-06.
- Revisión A+B+C, intento 1: sin gaps de corrección o seguridad pendientes; tabla al final del ledger. `pip check` sigue fallido, con incompatibilidad descartada como defecto para el backend `pt` documentado. Adenda GPU verificada después; QA en curso.

**Condición GPU resuelta para esta prueba:** el uso en reposo subió hasta 2.950 MiB, Ollama sin modelos. El propietario respondió «autorizo esa prueba», concediendo excepción exclusivamente para la matmul BF16 de 64×64. Se ejecutó el comando exacto de Verificación: assert `sm_120` y cálculo CUDA BF16 → **`262144.0`**, exit 0 ([recibo](testing/t05/raw/bf16-final.log)). No se cerraron aplicaciones ni cargaron modelos; Ollama inicialmente vacío, sin modelo que restaurar. VRAM posterior 2.965 MiB. La excepción no cubre cargas de modelos ni benchmarks de T-06 en adelante; para ellos sigue vigente AGENTS.md §4 regla 8 / ADR-0022. T-05 pasa a en-revision, pendiente del informe QA.

**Cierre técnico — 2026-10-05:** todas las verificaciones canónicas ejecutadas, revisión A+B+C sin gaps y [QA sin UI](testing/t05/report.md) conforme a la declaración del plan. Suite adicional 125 passed; lint y puertas del ledger exit 0. Gate unitario sin Python de producción medible: no se atribuye porcentaje al shell/config ni verde E2E. `pip check` conserva exit 1 y rebate limitado a backend pt. El PDF del informe queda pendiente por dependencias ausentes; el informe Markdown y los recibos están disponibles. T-05 completada; integración Git posterior con commit propio. La imagen acredita entorno y BF16, no servicio HTTP ni generación.
- **Changelog**: Imagen local de ACE-Step con CUDA 12.8.1, Python 3.11, FFmpeg LGPL y cálculo BF16 comprobados en la RTX 5070; preparada para implementar el adaptador musical.

### T-06 — Adapter ACE-Step (`music.song`, `music.instrumental`)

- **Descripción**: Envolver la **API Python** de ACE-Step (el handler, no la REST) detrás del contrato `/v1`, con los modos forzados para el tier 4.
- **Estado**: completado
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 5h · real —
- **Supervisión**: est. 1.3h (≈25 % IA) · real —
- **Dependencias**: T-05
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/` (adapter.py, descriptor.py, factoría engine_acestep.py, proceso hijo, patches, tests CPU/GPU y ajustes necesarios de empaquetado/imagen), `packages/engine-contract/engine_contract/__init__.py`, `packages/engine-contract/tests/test_contract.py`, `packages/contracts/engine-v1.json`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/entorno.md`, `docs/decisiones/ADR-0024-hashes-de-codigo-remoto-en-descriptores.md`, `docs/decisiones/ADR-0025-limite-de-memoria-wsl.md`, `docs/decisiones/README.md`, `docs/legal/licencias.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t06/`
- **Changelog**: ACE-Step genera canciones e instrumentales locales mediante /v1, con pesos verificados, semillas exactas, control de memoria y salida WAV estéreo a 48 kHz.
- **Verificación**:
  - `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q` → verde
  - `docker compose run --rm engine-acestep uv run pytest -m gpu -q` → verde (30 s de audio, 48 kHz estéreo, sin NaN ni silencio; telemetría completa; `unload` libera la VRAM)

**Criterios de aceptación**
- [x] `load` carga DiT, LM, VAE y text encoder desde `models/ace-step-1.5/`. **Modos forzados**: bf16, sin offload, sin INT8 y sin `torch.compile`, además del modo `offload`. El checkpoint y el LM (0.6B por defecto) se eligen por configuración, **sin fiarse del tier automático**.
- [x] Parche documentado para que `silence_latent` se lea del safetensors convertido. Si aparecen otros `torch.load` en el camino de carga (I-04), se parchean igual y se añaden al test.
- [x] `generate` acepta letra con etiquetas, estilo, duración, semilla, `vocal_language` (por defecto el de la canción, **no** `"en"`), BPM y tonalidad (si el upstream los expone) y `n_outputs`. Emite etapas y progreso reales, lo más fino que permita la API (I-03), y respeta la cancelación.
- [x] Escribe WAV float32 con **soundfile** a partir del tensor en memoria, sin usar `torchaudio.save`.
- [x] Descriptor con licencia MIT, `training_data` literal, `remote_code` con sus hashes y las tareas `music.song` y `music.instrumental` (con sus features: `negative_prompt`, `bpm`, `key`, `timbre_ref`, `lora`) en `verified: false` hasta T-10. El CLI de T-07 funciona con `STUDIO_ALLOW_UNVERIFIED=1`.

**Arranque — 2026-10-05:** T-05 completada, integrada y publicada en `main` (`19ab239`); rama `m0/t-06-acestep-adapter`. Se retoma con brief determinista, subagente fresco y TDD activo. Backend pt obligatorio: la imagen omite flash-attn; upstream usa vllm por defecto en su API si no se fuerza. La autorización previa del propietario cubría solo la matmul BF16, ya ejecutada; no se extiende a carga de modelos o benchmark. Avanza implementación y verificación CPU mientras se mantiene la condición de VRAM para pruebas GPU. No se declara generación ni carga real acreditada.

**Contexto resuelto:** el contrato descartaba `remote_code` como extra. Se amplía con lista opcional de rutas relativas y SHA-256, sin romper `/v1`, según [ADR-0024](../../decisiones/ADR-0024-hashes-de-codigo-remoto-en-descriptores.md); se regenera el JSON Schema en el mismo cambio. Se amplía el ownership del implementer únicamente a modelo/test de contrato y esquema generado; los documentos los mantiene el orquestador. La literalidad de `training_data` se obtiene de la [model card en la revisión fijada](https://huggingface.co/ACE-Step/Ace-Step1.5/blob/19671f406d603126926c1b7e2adc169acbcade22/README.md), como declaración del proveedor, sin atribuirle una auditoría.

**Verificación CPU T-06 — 2026-10-05:** imagen final `sha256:6fbddce9961c7ac6d3ae4e38dfdc39f947c5fe0607637d7215b03aa1ddc7a75e`; comando declarado `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q` → **35 passed, 1 deselected**, exit 0. Cobertura real Python 3.11.14 de adapter/patches/descriptor/factoría: **92,31 %**, todos los ficheros ≥80 %. Host adapter+contrato: **45 passed, 1 skipped**; lint, formato y esquema verdes. Hashes locales reales comprobados sin deserialización y factoría sin torch/proceso acreditada. [Recibo de implementación y RED/GREEN por criterio](testing/t06/implementation-report.md), con salidas individuales en `testing/t06/raw/`. RED adicional: `test_pretrained_loads_bf16_before_cuda_transfer` falló por falta de dtype en la deserialización · 2026-10-05; GREEN 1 passed y suite final verde. TDD n/a: configuración/empaquetado. **GPU no ejecutada**: Ollama vacío y baseline 2.874 MiB; resolución solicitada al propietario conforme AGENTS.md regla 8. No se acredita carga de modelos, audio ni liberación real de VRAM; T-06 sigue en-progreso. Medición de implementación cerrada 11:45:20–12:30:29 UTC, `fuente: estimado`, sin tokens/horas/coste medidos; 45 min son duración de reloj.

**Cierre técnico T-06 — 2026-10-05:** revisión A+B+C intento 3 sin gaps y [QA CPU/GPU](testing/t06/report.md) conforme. CPU host 179 passed/5 skipped/1 deselected, gate del diff **94,58 %** (mínimo 80 %). Prueba real autorizada → **1 passed/58 deselected**, exit 0: 30 s, 48 kHz, estéreo FLOAT, sin NaN/silencio, RMS 0,17382145, 31 eventos. Carga implícita real de DiT/LM/VAE/text encoder BF16, pico VRAM 7.806,80 MiB bajo cap 8.810,31 MiB, spilled=false. Unload termina el proceso y loaded=null; free antes 9.322,31/después 10.512,50 MiB, diferencia afectada por actividad del escritorio. Ollama vacío, sin modelo que restaurar; nvidia-smi posterior 1.338/12.227 MiB. load_s=122,87 y run_s=142,50 (este último incluye carga); RTF null. [Salida y herramienta](testing/t06/raw/gpu-30s-tool-receipt.json). RAM WSL pico excluyendo memoria recuperable 4.567,90 MiB; swap pico 1,293 MiB, caché final 16.121,92 MiB. Se mide, sin cambiar .wslconfig. QA sin UI por diseño, sin gate E2E ficticio; PDF pendiente de herramientas. Ventana QA cerrada estimada sin horas/tokens/coste medidos. Capacidades verified:false hasta T-10; esta prueba no cierra T-07 ni la escucha de M0. Integrada con fast-forward a main y publicada en origin/main y rama de tarea, commit 11c1884; preparación T-07 y journals preexistentes preservados.

**Cambio de perfil WSL posterior a la prueba GPU — 2026-10-05:** el propietario eligió y escribió 16 GB de RAM / 8 GB de swap / `autoMemoryReclaim=dropCache` y solicitó reiniciar. `wsl --shutdown` → exit 0; Ubuntu tras el arranque informa MemTotal 16.375.452 kB y swap 8.388.608 KiB, sin uso. Docker Desktop vuelve a responder. [ADR-0025](../../decisiones/ADR-0025-limite-de-memoria-wsl.md) y entorno E-03 actualizados. No se ha repetido audio con el nuevo límite; el recibo de 30 s corresponde a los 24 GB anteriores.

### T-07 — CLI `scripts/generate.py`: primera canción 🎯

- **Descripción**: CLI que hace de «server» para M0: llama al engine, ejecuta audio-post y escribe el manifiesto. Hito: la **primera canción** del proyecto.
- **Estado**: completado
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Supervisión**: est. 0.3h (≈25 % IA) · real —
- **Dependencias**: T-04, T-06
- **Tipo**: backend
- **Archivos**: `scripts/generate.py`, `tests/test_generate.py`, `pyproject.toml`, `uv.lock` (herramientas CLI), `eval/briefs/B-02.txt`, `eval/briefs/briefs.yaml` (solo B-02), `data/inputs/libre/` (entrada privada, excluida de Git), `docs/decisiones/ADR-0023-primera-cancion-con-material-privado.md`, `docs/decisiones/README.md`, `docs/legal/licencias.md`, `docs/arquitectura/pipeline-audio.md` (uso del CLI), `docs/roadmap/2026-09-28-m0-entorno-y-motor/spec.md`, `docs/calidad/evaluacion-escucha.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/`
- **Verificación**:
  - `uv run scripts/generate.py --lyrics data/inputs/libre/lyrics-acestep.txt --style (Get-Content -Raw -Encoding utf8 data/inputs/libre/style-acestep-compact.txt) --duration 255 --language es --bpm 94 --seed 1 --lyrics-declaration own` → carpeta en `data/cli/<fecha>/<run_id>/` con 4 ficheros (entrada privada de «Libre», [ADR-0023](../../decisiones/ADR-0023-primera-cancion-con-material-privado.md))
  - `uv run scripts/verify_manifest.py data/cli/` → `all valid`
  - lectura: se escucha la canción y se anotan en el ledger el tiempo total, `vram_peak_mb` y una primera impresión

**Criterios de aceptación**
- [x] Letra y estilo de **«Libre»** entregados por el propietario y preservados en una entrada privada, con declaración de autoría antes de generar. B-02 conserva su definición de evaluación; el CLI sigue admitiendo `--brief <ID>` ([ADR-0023](../../decisiones/ADR-0023-primera-cancion-con-material-privado.md)).
- [x] El CLI acepta dos formas: `--brief <ID>` (lee `eval/briefs/briefs.yaml` y `eval/briefs/<ID>.txt`) o `--lyrics <fichero> --style "…" --duration <s> --language <xx>`. Opcionales: `--seed`, `--variants`, `--task music.instrumental` y `--engine` (por defecto, `STUDIO_ENGINES`). Envía el token. Muestra el progreso por eventos y deja `master.flac`, `listen.mp3`, `peaks.json` y `manifest.json` (`kind: cli_run`).
- [x] **Hito cumplido**: «Libre» en castellano generado con objetivo 255 s y escuchado por el propietario; duración real y primera impresión registradas.

**Material recibido — 2026-10-05:** el propietario entregó «Libre» con su letra, prompt y notas creativas, y aclaró «así las usaba para suno». Material guardado en `data/inputs/libre/` (excluido de Git): original y adaptación para ACE-Step con los mismos versos y nueve secciones. Preferencias recibidas: hip hop, orquesta y electrónica, dueto en castellano, 94 BPM, 240–270 s; duración de prueba propuesta: 255 s. La declaración de autoría está pendiente de respuesta; no se ha generado audio. B-02 mantiene su definición en la batería fija. Criterio de primera canción actualizado según ADR-0023; T-07 sigue en borrador y sus verificaciones no se han ejecutado.

**Arranque CLI — 2026-10-05:** T-06 integrada y publicada (11c1884), dependencias técnicas completas. Rama m0/t-07-cli-first-song, subagente fresco con brief determinista y TDD. El perfil WSL 16/8 GB ya está aplicado; la generación de una canción completa con ese perfil no se ha verificado. La declaración de autoría de «Libre» sigue pendiente; se implementa y prueba el CLI con entradas sintéticas sin encolar esa letra. El orquestador mantiene documentos, ledger, datos privados, Git y prueba real. Brief determinista: exit 0, 13.259 caracteres; aviso de exceso preexistente frente al límite orientativo de 10.000, sin truncar criterios.

**Contexto adicional resuelto:** el catálogo `eval/briefs/briefs.yaml` no existía. Se crea `version: 1`, `briefs` como mapping por ID, con estilo/duración/idioma/BPM/tarea y declaración de autoría; solo metadata B-02 del protocolo, sin crear su letra y con declaración null. El CLI usa `yaml.safe_load`; PyYAML se incorpora al grupo dev del workspace virtual y al lock, con licencia MIT registrada. Ownership ampliado al implementer solo para pyproject.toml/uv.lock. TDD n/a: catálogo y documentación; el parser y las validaciones siguen TDD de código.

**Declaración recibida — 2026-10-05:** el propietario respondió expresamente «Es mi letra, con o sin ayuda de IA». Se registra own en data/inputs/libre/brief.json sin versionar texto ni datos privados. Declaración resuelta; generación real y escucha aún pendientes. La prueba real usará la misma letra, 255 s, idioma es, BPM 94 y caption en mayor.

**Entrega CPU — 2026-10-05:** CLI directo/catálogo y postproceso con mock real implementados; 38 tests verdes, generate.py 94,86 % (240/253 statements), ruff y formato exit 0. [Informe](testing/t07/cpu-implementation-report.md), [RED/GREEN](testing/t07/cpu-tdd-evidence.md) y cobertura real conservados. RED: tests/test_generate.py::test_direct_request_and_rights falló con assert None is not None; integración mock/postproceso también antes de implementar. RED: test_brief_catalog falló BRIEF_CATALOG_REQUIRED; test_direct_bpm falló unrecognized arguments --bpm 94; test_long_stage_stream_timeout falló assert 30 > 300; test_song_manifest_privacy_and_rights falló assert True is False; test_engine_errors[no_modes-CAPABILITY_UNAVAILABLE] falló IndexError · 2026-10-05. GREEN final 38 passed. El informe identifica tests adicionales como cobertura, sin fabricar rojos. La entrega BLOCKED reservaba generación real y escucha a root; se valida código/CPU, sin cerrar esos criterios.

**Validación de entrada real:** el primer intento del CLI terminó exit 1 antes de cargar modelos porque el caption adaptado tenía 755 caracteres frente a maxLength=512 del descriptor. Reproducción contra el JSON Schema real: style rechazado por maxLength 512. Root prepara style-acestep-compact.txt de 490 caracteres, validado con la misma letra/255 s/es/94 BPM. Letra, prompt Suno y adaptación anterior preservados; no se toca código para superar el límite. El nuevo intento está en curso, sin resultado acreditado todavía.

**Primera toma real generada y postproceso recuperado — 2026-10-05:** GPU produjo WAV de 255 s (4:15), 48 kHz estéreo, semilla 1, BF16. Pico VRAM 8.463,03 MiB / cap 10.097,89 MiB, spilled=false; load_s=123,79 y run_s=175,55 (incluye carga, RTF null). WSL 16/8 aplicado: pico VM usado excluyendo MemAvailable 4.578,54 MiB, swap cero, 173 muestras. CLI exit 1 en publicación final de carpeta, Windows PermissionError errno13/winerror5; no se atribuye a falta de RAM/GPU. Reproducción CPU sin regenerar, mismo fallo en rename dentro/fuera del aislamiento; instrumentalizar stat/print antes permitió renombrar a la primera. No se identifica proceso externo del bloqueo. Hipótesis de robustez entregada al implementer para RED/regresión y reintento acotado; único re-despacho de validación.

Se recuperaron master.flac (PCM24), listen.mp3, peaks.json y manifest.json desde el mismo WAV/eventos; verify_manifest.py data/cli/ → all valid (1 manifests), exit 0. Escucha -14,0045 LUFS / true peak -1,0 dBTP. [Recibo técnico público sin letra/prompt](testing/t07/first-song-technical-receipt.json). Se entregó enlace al MP3 al propietario y se solicitó primera impresión; pendiente. La verificación CLI original NO se declara verde con esta recuperación instrumentada. Fix, revisión, QA y nueva comprobación de publicación pendientes; T-07 sigue en-progreso.

**Corrección de publicación — 2026-10-05:** reintento exclusivo Windows WinError 5/32, máximo cinco intentos con pausas 0,1/0,2/0,4/0,8 s; destino nuevo y sin sobrescritura. Ante fallo persistente de una variante se retiran solo carpetas propias y staging; un error de limpieza no sustituye al primario. RED: test_publication_transient_windows_lock[5] falló PermissionError WinError 5; test_publication_persistent_lock_rolls_back_variants falló por variante previa publicada; test_publication_cleanup_keeps_original_error falló porque cleanup sustituía el error original · 2026-10-05. GREEN: 50 tests CLI, 176 tests CPU sin GPU; cobertura generate.py 263/279 = 94,27 %, ruff/formato exit 0. [Informe y cuatro fases de depuración](testing/t07/fix-publication-report.md). No se identifica el proceso externo del bloqueo original. El candidato de gotcha queda en ese informe, sin aprobación ni publicación como conocimiento. La toma privada recuperada se conserva; una nueva ejecución GPU verifica el CLI sin instrumentación. Revisión/QA y escucha pendientes.

**Verificación CLI completa sin instrumentación — 2026-10-05:** nueva toma 01M467F5TCCR83V5E2XR9MR6QK, anterior conservada. El comando de Verificación se ejecutó con --engine http://127.0.0.1:8101 y STUDIO_ALLOW_UNVERIFIED=1 explícito tanto en CLI como engine, ya que verified:false hasta T-10. Exit 0 en 170.22 s de reloj; 255 s de audio. Cuatro ficheros publicados y verify_manifest.py data/cli/ → all valid (2 manifests), exit 0. Pico VRAM 8463.03 MiB / cap 9970.62, spilled=False; run_s incluye load_s, RTF null. WSL pico excluyendo MemAvailable 4608.17 MiB, swap 0 MiB. [Recibo técnico](testing/t07/cli-full-generation-receipt.json). Ollama estaba vacío; unload se comprobó tras la ejecución. Escucha del propietario y revisión/QA siguen pendientes.

**Medición implementación T-07:** marcador cerrado antes de revisión, 2026-10-05T13:41:23Z–2026-10-05T14:32:36Z; fuente estimado, horas/tokens/coste medidos None/None/None. Duración de reloj 51m no equivale a horas IA. [Recibo](testing/t07/implementation-usage.json).

**Fix1 de revisión — 2026-10-05:** B1 corroborado y corregido con TDD. RED: tests/test_generate.py::test_ctrl_c_during_loading_waits_for_unload reprodujo main exit 1 / ENGINE_HTTP_409; GREEN Ctrl+C con mock real stage_delay_ms=1000 → exit 130, health idle/loaded=None. RED: tests/test_generate.py::test_cleanup_waits_beyond_ten_seconds falló ENGINE_CLEANUP_TIMEOUT con el plazo de 10 s · 2026-10-05; GREEN con carga sintética de 20 s y máximo 300 s. Se espera terminal/idle del job propio y se confirma unload; errores de limpieza preservan el error primario y muestran ENGINE_CLEANUP_UNCONFIRMED sin datos privados. No descarga jobs/modelos ajenos. 63 tests CLI, 189 CPU, cobertura 304/324=93,83 %, ruff/formato exit 0. [Informe RED/GREEN](testing/t07/fix1-cancellation-report.md). El mismo helper se aplica antes del postproceso normal. [Comprobación HTTP real solo lectura](testing/t07/cleanup-live-contract-receipt.json): contrato del job completado compatible, idle/loaded=None; no nueva generación ni cancelación GPU real. Los dos audios se conservan. Revisión intento 2 y QA pendientes; escucha pendiente.

**Fix2 de revisión — 2026-10-05:** B2/D2 deduplicado corregido con una única ventana de limpieza por ejecución, marcada antes de iniciarse. RED: tests/test_generate.py::test_generate_has_one_cleanup_budget falló assert 600.0 <= (300 + 1e-9) · 2026-10-05, generate completo con done/unload409persistente y reloj sintético. GREEN una llamada finish_job, ≤300 s simulados, aviso/nota y error primario preservados, sentinel previo intacto y sin salidas parciales. 64 tests CLI/190 CPU verdes, cobertura 312/332=93,98 %, ruff/formato exit0. [Informe](testing/t07/fix2-cleanup-budget-report.md). No nueva GPU: el fix controla repetición de limpieza, las regresiones mock/FFmpeg/Ctrl+C y contrato real ya acreditados se mantienen. Escucha pendiente; revisión3última y QA pendientes.

**Escucha del propietario — 2026-10-05:** escuchada la primera toma de 255 s, job 01M465ZQTFYQK9ATZNG2X63KYJ. Primera impresión literal: «la voz y la música parece que no van acorde». [Recibo](testing/t07/owner-first-impression.json). El criterio de primera canción y escucha está acreditado, con valoración negativa; NO se declara calidad musical aprobada. Se pregunta si el desajuste es de ritmo/letra, afinación o carácter de voz para investigar sin diagnosticar por suposición. T-07 espera QA técnica; la selección por calidad de M0 sigue pendiente de batería y T-13.

**Cierre T-07 — 2026-10-05:** todos los criterios acreditados y Verificación ejecutada: CLI real exit 0 en 170,22 s, audio 255 s, pico VRAM 8.463,03 MiB, spilled=false, swap cero; cuatro salidas por toma y `verify_manifest.py data/cli/` → all valid (2 manifests), exit 0. Primera toma escuchada por el propietario con valoración negativa. [QA independiente](testing/t07/report.md): **243 passed, 5 skipped, 1 deselected**, exit 0; cobertura del fichero de producción cambiado **93,98 %** (312/332, mínimo 80 %), gate exit 0; ruff/formato/contratos/manifiestos/diffcheck conformes. Revisión A+B+D intento 3 sin gaps; qa: sin UI por diseño (`test-plan: n/a (sin UI)`), sin E2E ficticio. PDF pendiente de herramientas, sin bloquear CLI. [Medición QA cerrada](testing/t07/qa-usage.json): fuente estimado, sin horas IA/tokens/coste medidos. M0 sigue abierto; faltan T-08–T-13.

**Aclaración de calidad — 2026-10-05:** el propietario concreta los tres desajustes: ritmo/encaje, afinación y carácter de voz, y aporta el corpus original de Suno. [Respuesta](testing/t07/owner-quality-details.json) y [diagnóstico inicial](testing/t07/prompt-model-diagnosis.md). El ajuste actual shift=1 difiere del recomendado 3 para Turbo; no hay prueba A/B ni causa artística demostrada todavía. El post-proceso WAV→master conserva la alineación de muestras. Originales preservados, copias privadas; ninguna audición por el agente. Calidad musical **no aprobada**, separada del cierre técnico del CLI.

- **Changelog**: Generación local por CLI desde letra y estilo o catálogo de briefs, con progreso, cancelación y exportaciones inmutables de master, MP3, forma de onda y manifiesto; primera canción completa generada y escuchada.

---

## Fase 4 — Medición y elección

**Estado**: en-progreso · **Estimado**: 37h · **Real**: —

### T-08 — `engine-analysis` (transcripción, CLAP, estética y beats)

- **Descripción**: Contenedor con las tareas de análisis y evaluación que usan M0 (evaluación) y M1 (beats).
- **Estado**: borrador
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real —
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-03, T-02, T-19 (entrada efectiva y recibos antes de evaluar fidelidad)
- **Tipo**: backend
- **Archivos**: `apps/engines/analysis/` (Dockerfile y adapters), `docker-compose.yml`
- **Verificación**:
  - `docker compose --profile engines build engine-analysis` → OK
  - `docker compose run --rm engine-analysis uv run pytest -m gpu -q` → verde: `audio.transcribe` sobre un audio de prueba devuelve texto y tiempos; `audio.clap` y `audio.aesthetics` devuelven puntuaciones; `audio.beats` devuelve BPM ±2 sobre un clic de 120 BPM

**Criterios de aceptación**
- [ ] Base `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime`, dependencias fijadas, puerto `127.0.0.1:8130`, y los mismos montajes y token que engine-acestep (contrato §6). `audio.beats` se declara con `device: cpu` (beat_this en CPU).
- [ ] Tareas `audio.transcribe` (Qwen3-ASR-1.7B), `audio.clap` (LAION, pesos convertidos), `audio.aesthetics` (Audiobox, `model.safetensors`) y `audio.beats` (beat_this, pesos convertidos). `audio.align_lyrics` (ForcedAligner) queda preparada pero no se verifica hasta M3.
- [ ] Un modelo cada vez en el proceso hijo; se cambia de modelo dentro del engine descargando el anterior.

**Fidelidad al evaluar:** contrastar letra efectiva sin tags con transcripción y tiempos, conservando el suelo WER. Los resultados de análisis alimentan [evaluacion-escucha §3.1](../../calidad/evaluacion-escucha.md#31-fidelidad-de-instrucciones-y-naturalidad) y la [rúbrica T-18](testing/t18/preparation-report.md#rúbrica-para-la-evaluación-musical-posterior); no atribuyen naturalidad ni obediencia por sí solos. Los recibos planned/captured siguen siendo evidencia de transporte, no de calidad.

### T-09 — Benchmark en la 5070

- **Descripción**: Números reales para decidir la configuración por defecto y el modo de alta calidad.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-07, T-19 (entradas musicales verificadas)
- **Tipo**: investigación
- **Archivos**: `scripts/eval/benchmark.py`, `eval/results/benchmark-5070.md`
- **Verificación**:
  - `uv run scripts/eval/benchmark.py --matrix default` → escribe `eval/results/benchmark-5070.md`
  - lectura: la tabla tiene VRAM pico, carga, inferencia, RTF y `spilled` para cada configuración y duración

**Criterios de aceptación**
- [ ] Matriz de configuraciones: turbo + LM 0.6B (inicial), turbo + LM 1.7B, sft, base y XL-turbo con offload + INT8 si cabe. Duraciones: 30, 60, 180 y 300 s.
- [ ] Carga desde el bind mount frente a una copia dentro del contenedor (I-02). Si la diferencia supera 30 s, se abre un ADR.
- [ ] **Antes de medir**, el modelo de Ollama queda descargado de la VRAM (`ollama stop <modelo>`; sin parar el servicio ni borrar el modelo), y `nvidia-smi` muestra ≤ ~1,6 GB usados (E-16, [ADR-0022](../../decisiones/ADR-0022-memoria-tecnica-kwipu-graphiti.md)). Se anota la VRAM en reposo en el informe.
- [ ] Medido con el navegador abierto (la UI también consume VRAM). Se registra si hubo desbordamiento (Administrador de tareas y caída de RTF por encima de 1,5×).
- [ ] Opcional: `torch.compile` activado como experimento, anotando si falla en sm_120.
- [ ] Recomendación argumentada con números para la configuración por defecto y la de alta calidad.

### T-10 — Matriz de capacidades verificadas

- **Descripción**: Qué operaciones funcionan de verdad en ACE-Step, con qué checkpoint y con qué evidencia.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 2.5h · real —
- **Supervisión**: est. 0.6h (≈25 % IA) · real —
- **Dependencias**: T-07, T-19 (entradas musicales verificadas)
- **Tipo**: investigación
- **Archivos**: `eval/results/capacidades-acestep.md`, `eval/capabilities/` (git-ignored), `apps/engines/acestep/descriptor.py`
- **Verificación**:
  - lectura: `eval/results/capacidades-acestep.md` tiene una fila por tarea con el checkpoint, el comando exacto, la ruta del audio de evidencia y el veredicto
  - `uv run pytest apps/engines/acestep -k descriptor -q` → `verified` coincide con la matriz

**Criterios de aceptación**
- [ ] Tareas evaluadas: **`music.song`**, `music.instrumental`, `music.retake`, `music.extend`, `music.repaint`, `music.cover`, `music.complete` y `audio.stems` (extract). Features de `music.song`: `negative_prompt`, `bpm`, `key`, `timbre_ref` y `lora`. Veredicto de cada una: funciona · degradada · no funciona.
- [ ] En `repaint`: ¿el audio fuera de la región queda bit a bit intacto, o hace falta un empalme? Queda documentado.
- [ ] El descriptor pone `verified: true` solo en las tareas y features que funcionan. Como mínimo, `music.song` y `music.instrumental` deben quedar verificadas: si no, M1 no puede empezar.

### T-11 — Batería de evaluación automatizada (F-84)

- **Descripción**: Generar y medir los 10 briefs de forma reproducible y anónima.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-07, T-08, T-19 (entradas musicales verificadas)
- **Tipo**: investigación
- **Archivos**: `scripts/eval/run.py`, `scripts/eval/metrics.py`, `eval/briefs/B-01…B-10.txt`, `eval/briefs/briefs.yaml`, `eval/results/sheet-<candidato>.md`
- **Verificación**:
  - `uv run scripts/eval/run.py --candidate ace-step-1.5-turbo --dry-run` → lista 30 tomas planificadas
  - `uv run scripts/eval/run.py --candidate ace-step-1.5-turbo` → 30 tomas en `eval/takes/`, mapa en `eval/takes/.map.json` y hoja de puntuación con WER/CLAP/Audiobox

**Criterios de aceptación**
- [ ] Los 10 briefs de evaluacion-escucha.md §4, con letras **propias**. Cada brief tiene un único prompt de estilo, literal para todos los candidatos.
- [ ] 3 tomas por brief con semillas fijas, loudness igualado a −16 LUFS mediante ganancia lineal y códigos aleatorios. El mapa se guarda aparte.
- [ ] Antes se mide el **suelo del WER** del transcriptor sobre 2–3 grabaciones cantadas reales, y se anota.
- [ ] Hoja de puntuación en Markdown lista para rellenar.
- [ ] Para medir con `engine-analysis`, las tomas se copian a `data/tmp/<job_id>/in/` (el engine solo ve `data/`).

### T-12 — *(Opcional)* `engine-heartmula` en 4 bits

- **Descripción**: Segundo candidato para comparar el castellano. Si no se hace, se marca `cancelado` con justificación.
- **Estado**: borrador
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real —
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-03, T-11, T-19 (entradas musicales verificadas)
- **Tipo**: backend
- **Archivos**: `apps/engines/heartmula/`, `models/models.lock.json`, `docs/legal/licencias.md`
- **Verificación**:
  - `uv run pytest apps/engines/heartmula -m gpu -q` → conformidad básica en verde
  - `uv run scripts/eval/run.py --candidate heartmula-oss-3b` → 30 tomas

**Criterios de aceptación**
- [ ] Contenedor con las versiones de heartlib (`torch<2.11`, `bitsandbytes==0.49`, `transformers==4.57`) en **build cu128**, y el modelo oss-3B «happy-new-year» con el codec 20260123 en NF4/FP4.
- [ ] Mismo contrato `/v1`; la batería de T-11 se genera como candidato B.

**Fidelidad del candidato B:** el adaptador de HeartMuLa demuestra su propio recorrido de letra/tags y límites; no hereda el perfil ACE-Step. Comparar el mismo texto efectivo, con original/diff preservados, y aplicar [evaluacion-escucha §3.1](../../calidad/evaluacion-escucha.md#31-fidelidad-de-instrucciones-y-naturalidad) y la [rúbrica T-18](testing/t18/preparation-report.md#rúbrica-para-la-evaluación-musical-posterior). Registrar naturalidad y cumplimiento por separado, sin reinterpretar un recibo de entrada como una aprobación musical.

### T-13 — Escucha y decisión de modelo

- **Descripción**: Sesión de escucha a ciegas y decisión registrada.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Supervisión**: est. 0.1h (≈25 % IA) · real —
- **Dependencias**: T-09, T-10, T-11 (y T-12 si se hizo), T-19 (entradas musicales verificadas)
- **Tipo**: docs
- **Archivos**: `eval/results/escucha-m0.md`, `docs/decisiones/ADR-0011-seleccion-de-modelos.md`, `docs/arquitectura/modelos.md`, `docs/memory/`
- **Verificación**:
  - lectura: `eval/results/escucha-m0.md` tiene las hojas completas, el mapa abierto solo al final y el veredicto según §5 del protocolo
  - lectura: ADR-0011 está en «aceptada (confirmada)» o sustituida por otra, y `modelos.md` recoge la configuración por defecto y la de alta calidad con los números de T-09

**Criterios de aceptación**
- [ ] Sesión con los umbrales fijados antes de escuchar.
- [ ] Veredicto: modelo aprobado / elección entre candidatos / replantear.
- [ ] Nota en `docs/memory/` con la decisión y la fecha.


**Verificación de fidelidad en la escucha:** las hojas incorporan [evaluacion-escucha §3.1](../../calidad/evaluacion-escucha.md#31-fidelidad-de-instrucciones-y-naturalidad) y la [rúbrica T-18](testing/t18/preparation-report.md#rúbrica-para-la-evaluación-musical-posterior), con tiempos del audio, recibos de preparación/entrada y notas separadas de naturalidad y cumplimiento. No verificar arco/outro desde fragmentos ni abrir el mapa antes de terminar. Los umbrales D1–D5/WER fijados permanecen iguales.

### T-14 — Comparación privada de «Libre»: shift 1 frente a 3

- **Descripción**: Prueba acotada autorizada por el propietario («adelante», 2026-10-05) para investigar ritmo, afinación y carácter de voz con sus referencias Suno. Se añade a M0 sin sustituir los criterios ni la batería de T-08–T-13. No se declara ganador sin escucha humana.
- **Estado**: completado
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: T-06, T-07
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/tests/test_shift.py`, `scripts/generate.py`, `tests/test_generate_shift.py`, `docs/arquitectura/pipeline-audio.md`, `apps/engines/acestep/README.md`, `CONTINUE-HERE.md`, `docs/decisiones/ADR-0026-comparacion-controlada-shift.md`, `docs/decisiones/README.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t14/`, `data/inputs/libre/shift-ab/` y `data/eval/libre-shift/` (privados), `.cache/dev-cycle/t14/` (orquestación efímera, excluida de Git).
- **Verificación**:
  - `uv run --no-sync --all-packages pytest tests/test_generate_shift.py apps/engines/acestep/tests/test_shift.py -q` → verde, RED previo registrado.
  - `uv run --no-sync --all-packages python .cache/dev-cycle/t14/run-comparison.py` → seis tomas nuevas: tres semillas fijas por dos valores de shift, WAV/master/MP3/manifiestos válidos, eventos y unload confirmado. Audio y mapa de códigos privados; informe público sin letra, prompt ni rutas personales.
  - `uv run --no-sync scripts/verify_manifest.py data/cli/` → all valid; recibo de igualación de volumen con ganancia lineal y hoja de escucha sin revelar shift.

**Criterios de aceptación**
- [x] Parámetro opcional `shift` 1–5 en descriptor, adaptador y CLI `--shift`; rechaza valores no finitos/fuera de rango. Si se omite, se conserva el comportamiento anterior (1). No cambia la API genérica /v1 ni se declara una capacidad verificada nueva. Los manifiestos conservan el parámetro explícito.
- [x] Tres pares de tomas de 90 s sobre el primer verso y primer estribillo de «Libre», con las mismas palabras, etiquetas, caption, BPM 94, idioma es, modo BF16/PT, Turbo/LM0.6B y semillas 1/2/3; solo varía shift 1/3. Entradas y configuración identificadas por hash; original y tomas anteriores intactos. Autoría own ya declarada.
- [x] Audios de escucha a volumen comparable por ganancia lineal, sin compresor, con códigos aleatorios y mapa privado; referencia Suno disponible como objetivo artístico. Hoja separa ritmo, afinación, carácter de voz y preferencia. No se presenta la referencia como control causal entre motores ni la prueba como entrenamiento.
- [x] TDD, revisión adversarial y QA sin UI conformes; cobertura ≥80 % de los archivos de producción cambiados. GPU con comprobación de Ollama/VRAM libre y descarga real del hijo; telemetría y salidas acreditadas. Calidad y ganador pendientes de respuesta del propietario; no se genera la canción completa con una configuración elegida por suposición.

**Arranque — 2026-10-05:** rama m0/t-14-libre-shift-ab, base cd9b79d. Alcance adicional aprobado por la respuesta del propietario al plan de seis tomas; no presupuesto ni replanificación del resto de M0. La omisión de shift conserva 1 hasta disponer de evidencia artística. Subagente fresco con TDD para parámetros/tests; root conserva ledger/documentación/custodia privada/GPU/Git. TDD n/a: prosa, preparación de entrada y orquestación efímera; el cambio de producto exige RED antes de implementación.

**Entrega CPU — 2026-10-05:** subagente fresco DONE para alcance de parámetro/tests. [Informe RED/GREEN](testing/t14/cpu-implementation-report.md): Verificación exacta 35 passed/0,40 s; vecinos 149 passed, 1 skipped, 6 warnings/7,41 s. Cobertura real adapter 155/173, descriptor 30/30, generate 319/339; ruff/formato conformes. RED: test_descriptor_shift_optional falló KeyError shift; test_adapter_propagates_shift falló KeyError shift; test_adapter_rejects_invalid_shift falló DID NOT RAISE EngineError; test_shift_reaches_generation_params falló INTERNAL por ausencia de shift; test_direct_shift/test_brief_shift_override fallaron unrecognized arguments --shift; test_invalid_shift_rejected_before_enqueue falló ausencia de INVALID_PARAMS · 2026-10-05. Omisión/manifiesto preservan rutas existentes (cobertura adicional, sin RED inventado). Imagen nueva en construcción; no GPU repetida ni calidad atribuida a tests. Root prepara orquestación efímera y custodia de seis nuevas tomas.


**Fix1 y GPU autorizada — 2026-10-05:** B1 corregido con rango antes de math.isfinite, tras validar tipo; RED: test_invalid_shift_rejected_before_enqueue[huge-positive/huge-negative] y test_adapter_rejects_invalid_shift[huge-positive/huge-negative] fallaron OverflowError · 2026-10-05; GREEN 4 casos, 39 tests shift; vecinos 153 passed, 1 skipped/16,05s. Cobertura adapter89,60%,descriptor100%,generate94,10%; ruff/formato verdes. [Informe](testing/t14/fix1-report.md). Imagen final construida, [75 tests CPU](testing/t14/image-final-cpu-receipt.json), digest ca67e3d…; engine recreado idle sin modelo. [Autorización expresa](testing/t14/gpu-authorization.json): seis tomas90s con baseline2613MiB, cap dinámico y parada si spilled; Ollama vacío. Aún no se generan las seis tomas ni se declara calidad. Marcador fix1 cerrado antes de revisión2; sin imputar reloj de pared como horasIA.

- **Changelog**: Añade shift opcional validado a la CLI y ACE-Step, conservando su omisión; prepara seis tomas privadas comparables de Libre y una hoja de escucha a ciegas con referencia Suno. Calidad y ganador pendientes de escucha.


**Cierre técnico T-14 — 2026-10-05:** revisión A+B, intento 2, sin gaps; [QA independiente](testing/t14/report.md) conforme: **282 passed, 5 skipped, 1 deselected**, 25,80 s, exit 0. Cobertura de lo cambiado **94,57 %** (adaptador 89,60 %, descriptor 100 %, CLI 94,10 %), mínimo 80 %. Ruff, formato, contratos y ledger conformes. Sin UI por diseño, sin resultados E2E ficticios.

[Generación real y recibo](testing/t14/generation-receipt.json): seis tomas nuevas de **90 s**, tres semillas por dos valores de shift, con las mismas palabras y configuración identificadas por hash. WAV, master, MP3 y manifiestos válidos. Pico VRAM **7.889,16 MiB**, todos `spilled: false`; descarga del hijo confirmada entre tandas y al acabar. Swap WSL pico **0,4375 MiB**; tiempo total **512,77 s**, que incluye carga, postproceso y recuperación del empaquetado. `run_s` corresponde a cada tanda y está compartido por sus tomas: no se suma por toma ni se declara RTF. Ollama vacío antes y después, sin modelo que restaurar. Se corrigió exclusivamente la semilla del manifiesto derivado (entero 0 para una operación no estocástica); **no se regeneró ningún audio en GPU**.

Seis copias privadas codificadas al nivel común **−16,47 LUFS**, mediante ganancia lineal sin limitador ni compresor; seis manifiestos derivados válidos. Referencia Suno original intacta, verificada también por SHA-256 en su origen: tema completo, sin sincronización de secciones, atenuado al reproducir en `listen.html`. [Verificación de escucha](testing/t14/listening-verification.json): siete recursos HTTP disponibles y siete reproductores con metadatos cargados, sin errores; seis duraciones de 90 s y referencia de 227,64 s. El botón de exportación está presente, pero no se ha probado su descarga. Esta comprobación no acredita audición ni calidad musical.

Página, hoja de escucha y mapa de ajustes privados y separados. Calidad musical y ganador **pendientes del propietario** (`false`/`null`). No se genera una canción completa por suposición. T-08–T-13 y M0 siguen abiertos. [Ventana QA cerrada](testing/t14/qa-usage.json): fuente estimado, sin horas IA, tokens ni coste medidos; el tiempo de reloj no se imputa como IA. PDF pendiente de herramientas. Sin candidatos nuevos de conocimiento que curar; journals ajenos intactos.

### T-15 — Calidad de Libre: revisión de candidatos y comparación de prompts

- **Descripción**: El propietario pide continuar tras valorar T-14 y revisar si existe un modelo mejor. Investigación de alternativas locales y prueba acotada del prompt actual frente a uno orientado a interpretación natural, sin cambiar letra ni modelo durante esa prueba. No se atribuye superioridad musical sin escucha ni se instalan candidatos por suposición.
- **Estado**: completado
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: T-14
- **Tipo**: investigación
- **Archivos**: `CONTINUE-HERE.md`, `docs/arquitectura/modelos.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t15/`, `data/inputs/libre/prompt-ab/` y `data/eval/libre-prompt/` (privados), `.cache/dev-cycle/t15/` (efímero).
- **Verificación**:
  - `uv run --no-sync --all-packages python .cache/dev-cycle/t15/prepare.py` → letra idéntica por SHA-256, dos captions ≤512 caracteres y configuración constante.
  - `uv run --no-sync --all-packages python .cache/dev-cycle/t15/run-comparison.py` → seis tomas nuevas de90s, tres pares de semillas, solo varía caption; hashes, telemetría, unload y salidas válidos.
  - `uv run --no-sync scripts/verify_manifest.py data/cli/` y sesión de escucha → todos válidos; revisión/QA sin UI y comprobación HTTP/metadatos.

**Criterios de aceptación**
- [x] Revisión fechada con fuentes primarias de SFT/LM1.7B/XL, HeartMuLa, MiniMax Music3, SongGeneration y YuE2: disponibilidad, español, licencias y límites de GPU/RAM. Separar declaraciones del autor, inferencias y mediciones locales; sin ganador garantizado.
- [x] Seis tomas nuevas en tres pares, 90s, semillas1/2/3, shift1 fijo (conserva el anterior; no ganador consistente de T-14), BF16/PT, Turbo/LM0.6B, BPM94, es y misma letra/etiquetas por hash. Solo varía caption; no se cambian modelos, pesos, contratos ni parámetros de producto. Autoría own ya registrada.
- [x] Escuchas privadas codificadas con volumen comparable por ganancia lineal, sin compresor, referencia Suno original intacta y mapa separado. Valorar ritmo, afinación, voz e instrumentos; sin aprobación musical por métricas.
- [x] Revisión A+B y QA independientes conformes. Ollama vacío/VRAM ≤1600MiB antes de cargar, cap dinámico y parada ante spill, unload confirmado. TDD/cobertura n/a para prosa/config/orquestación efímera; producción sin cambios. Calidad y candidato definitivo pendientes del propietario; M0 abierto.

**Arranque — 2026-10-05:** autorización «continua» a la siguiente comparación y petición adicional de revisar mejores modelos. Rama m0/t-15-libre-prompt-ab. TDD n/a: prosa, configuración privada y orquestación efímera, sin cambios de código de producto. Subagente fresco prepara entradas/harness; root conserva ledger, investigación, GPU y Git. VRAM inicial1448MiB, Ollama vacío; se exige ≤1600MiB al arrancar cada tanda, sin extender la excepción de T-14.

- **Changelog**: Revisa candidatos locales y sus licencias, y prepara seis tomas privadas para comparar prompts con escucha ciega; calidad pendiente del propietario.

**Cierre técnico — 2026-10-05:** T-15 completada técnicamente, calidad musical y candidato definitivo pendientes del propietario. Investigación primaria fechada: [modelos](testing/t15/model-review.md); recomendación de probar SFT 2B/LM 0,6B y después HeartMuLa 3B, sin instalación ni cambio de motor. Revisión A+B intento 2 y [QA independiente](testing/t15/report.md) conformes. TDD/cobertura n/a, sin producto cambiado ni suite de producto repetida.

**Verificación ejecutada:** `prepare.py` exit 0: letra/control idénticos por bytes, SHA-256 acorde, captions 415/426 caracteres, configuración fija. `run-comparison.py`, mediante wrapper con entorno gestionado, exit 0: seis tomas nuevas de 90 s, semillas 1/2/3 × dos captions, shift 1/BF16/PT/Turbo/LM 0,6B/BPM 94/es; solo varía caption. Pares privados por ganancia lineal y sin limitador, nivel -16.39 LUFS; seis manifiestos derivados válidos con linaje. `verify_manifest.py data/cli/`: all valid (14 manifests); sesión: all valid (6 manifests). [Recibo GPU](testing/t15/generation-receipt.json), [preservación](testing/t15/preservation-receipt.json) y [metadatos HTTP/navegador](testing/t15/listening-receipt.json): siete reproductores sin error, seis fragmentos y referencia original; no se atribuye audición al agente ni se prueba exportación de valoraciones.

**GPU:** Ollama vacío; baselines por tanda [1327.0, 1327.0] MiB, todos ≤1600, sin excepción T-14. Pico 7891.26 MiB; caps dinámicos [10104.17578125] MiB; `spilled: false` en seis salidas, sin parada del monitor y unload confirmado en ambas tandas. Muestreo WSL: pico RAM usada excluyendo disponible 4805.84 MiB; swap 0.5195 MiB; 177 muestras. No se garantizan picos entre muestras ni se suman tiempos compartidos de la tanda. Orquestación 383.28 s, tiempo de reloj, no horas IA ni RTF. Sin modelo previo de Ollama que restaurar.

Privados: `data/eval/libre-prompt/01M46QBFERQBK6XCH2Z4QQP9B1/listen.html`, mapa separado y sesión efímera bajo `.cache/dev-cycle/t15/runtime/`. Original de Suno, entradas/escuchas T-14 y manifiestos previos preservados por hashes. No se sobrescribe ningún take ni manifiesto. M0 sigue abierto; faltan T-08–T-13. Coste/tokens/horas IA desconocidos, ventanas estimadas; presupuesto adicional no fijado.


---

### T-16 — Controles de inferencia y comparación privada SFT frente a Turbo

- **Descripción**: Continuación autorizada de la investigación de naturalidad. Habilitar SFT con su identidad, pasos y CFG correctos y comparar seis fragmentos nuevos emparejados, tres Turbo y tres SFT; preservar los controles antiguos como referencia histórica y no atribuir mejora sin escucha humana.
- **Estado**: en-progreso
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: T-06, T-07, T-15, T-19 (entradas musicales verificadas)
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/adapter.py`, `apps/engines/acestep/tests/test_inference_controls.py`, `scripts/generate.py`, `tests/test_generate_inference.py`, `apps/engines/acestep/README.md`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/modelos.md`, `docs/decisiones/ADR-0027-controles-de-inferencia-sft.md`, `docs/decisiones/README.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t16/`, `data/inputs/libre/sft-ab/`, `data/eval/libre-sft/`, `.cache/dev-cycle/t16/` (últimas tres rutas privadas/efímeras)., `apps/engines/acestep/preflight.py`, `apps/engines/acestep/input_profile.py`, `packages/audio-post/audio_post/manifest.py` (perfil/recibos coherentes con pasos y defaults SFT/Turbo), `tests/test_generate_preparation.py` (regresión de procedencia y publicación de nuevos parámetros), `apps/engines/acestep/tests/test_preflight.py` (solo factory de captura: controles efectivos en doble DiT)
- **Verificación**:
  - `uv run --no-sync --all-packages pytest tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py -q` → validación, defaults, identidad, propagación y progreso correctos; RED previo registrado.
  - QA sin UI: tests vecinos CPU, ruff/formato, contratos y cobertura ≥80 % de producción cambiada; imagen final con tests CPU del adaptador; revisión A+B y lentes condicionales conformes.
  - `uv run --no-sync --all-packages python .cache/dev-cycle/t16/run-comparison.py` → seis nuevas tomas de90s/semillas1,2,3 por configuración: SFT50pasos/CFG7 y Turbo8pasos/defaults anteriores, con LM0,6B/BF16/PT y shift1; entrada efectiva/metadata LM emparejadas y recibos actuales verificados. Los controles de T-15 permanecen intactos como referencia histórica separada.
  - `uv run --no-sync scripts/verify_manifest.py data/cli/` y carpeta de escucha → salidas/manifiestos/telemetría/unload/HTTP válidos; hashes de tomas anteriores conservados.

**Criterios de aceptación**
- [x] Descriptor distingue SFT (`ace-step-1.5-sft`) de Turbo; factoría/adapter usan identidad coherente. Turbo mantiene su identidad y defaults; no cambia /v1 ni se activa `verified`. Pasos opcionales enteros1–8 Turbo y1–200 SFT; CFG opcional finito1–20 solo SFT. Adaptador rechaza inválidos también sin HTTP y usa defaults SFT50/CFG7. CLI expone `--inference-steps` y `--guidance-scale`, también sobre briefs, con validación y manifiesto del pedido explícito. Progreso Euler/cancelación usan número efectivo de pasos.
- [x] TDD con RED por comportamiento, revisión fresca y QA CPU conformes, cobertura ≥80 % de los archivos de producción cambiados. Registro ADR/documentos en castellano; sin cambios de pesos, locks, dependencias ni motor por defecto.
- [ ] Seis nuevas tomas emparejadas90s, SFT y Turbo por semillas1/2/3, caption de control T-15 y misma letra por hash, BPM94/es, shift1/LM0,6B/BF16/PT. SFT50pasos/CFG7 frente a Turbo8pasos/defaults anteriores; la prueba compara configuraciones completas, no solo el checkpoint. Caption/letra/metadata y controles LM efectivos iguales por par; perfiles/capturas actuales, hashes/identidad/pasos/CFG/telemetría/unload acreditados. Controles Turbo antiguos preservados como referencia histórica, no controles equivalentes del experimento nuevo. Ollama descargado y VRAM≤1600MiB; cap dinámico, parada conservadora y sin excepción de T-14.
- [ ] Pares privados ciegos y referencia Suno original conservada; ganancia lineal con nivel común, sin compresor, sin sobrescribir takes/manifiestos/valoraciones previos. Valorar ritmo/afinación/voz/instrumentos; no declarar ganador ni generar canción completa por suposición. M0 y T-08–T-13 siguen abiertos.

**Arranque — 2026-10-05:** «continua» después de recoger otra valoración de la página8766 (T-14: P1B/P2B/Ninguna, campos numéricos/comentarios vacíos). La página8767 de T-15 permanece sin valorar en la pestaña disponible; no se interpreta como empate ni aprobación. Recibo privado nuevo con timestamp, anterior intacto. Investigación propone SFT como siguiente prueba local. Rama m0/t-16-libre-sft; presupuesto adicional no fijado. TDD activo para producto; TDD n/a para prosa/config/orquestación efímera. Subagente fresco implementa controles; root conserva ledger/documentación/GPU/Git.

**Cambio de prioridad explícito — 2026-10-05:** el propietario pide asegurar primero los prompts y revisar qué llega al LM, antes de perfeccionar o cambiar modelo. T-16 vuelve a borrador. Sin producto cambiado, build ni GPU. El subagente conserva el test parcial fuera de la colección pytest en `.cache/dev-cycle/t16/test_inference_controls.deferred.py`: RED real `test_descriptor_sft_identity_and_limits` falló AssertionError por identidad Turbo en descriptor SFT, 1 failed/0,18s; sin GREEN, no se declara implementación. Ventana inicial cerrada, fuente estimado; horas/tokens/coste medidos null. La auditoría se registra en T-17 y condiciona retomar SFT.

**Compatibilidad tras T-19:** los nuevos controles deben viajar también por el perfil planned/captured y su validador, con identidad de checkpoint y defaults coherentes. Acreditar SFT50/CFG7 y opciones explícitas sin relajar los presupuestos PT/DiT ni la correspondencia de idioma, metadata y flags con el request. No basta cambiar GenerationParams dejando un recibo que siga declarando ocho pasos.

**Reanudación tras T-19 — 2026-10-06:** T-19 integrada por fast-forward y publicada en main y su rama, commit `ef66a36bedf08fb996f88ef6cb9633b5f51f13b8`. QA actual 381 pruebas CPU y 92,84 % de cobertura añadida, revisión A+B+C fresca sin gaps; prompts/metadata/recibos protegidos. Retomar la rama T-16 mediante fast-forward a main; ningún commit propio previo de producto. Nuevo brief determinista y implementer fresco para controles CPU y pruebas de perfil/recibos. Los textos de control T-15 se conservan por hash; tres generaciones SFT posteriores requieren guardas actuales de GPU, no reutilizan excepciones. Las nuevas opciones deben aparecer en la solicitud/manifiesto y en planned/captured; no basta modificar GenerationParams dejando recibos con ocho pasos. Root lleva ledger/docs/ADR/Git/GPU, subagente únicamente producción/tests declarados y evidencia privada. Marcador T-16 nuevo iniciado tras cerrar QA T-19. Sin aprobación artística ni cierre de M0; prosa/orquestación TDD n/a, producción TDD activo.

**Comparación corregida — 2026-10-06:** [ADR-0027](../../decisiones/ADR-0027-controles-de-inferencia-sft.md) y plan actualizados: seis tomas nuevas emparejadas, no tres SFT frente a Turbo histórico. La auditoría T-17 acredita ausencia del idioma estructurado LM en el recorrido anterior; T-19 lo añade. Las capturas anteriores CPU no se presentan como históricas GPU. Se conserva el mismo control caption/letra, sin modificar originales, y los audios T-15 quedan como referencia histórica separada. Tres Turbo adicionales evitan confundir transporte y configuración; consumo adicional sin medir, no se altera el motor por defecto ni las puertas de escucha. La parte CPU del brief original no cambia; root notificó al implementer el ajuste GPU que solo ejecutará el orquestador. Brief determinista completo de 16.395 caracteres, sobre tope de 10.000 por exceso preexistente de contexto: aviso declarado, sin truncar ni omitir criterios.

**Contexto adicional CPU — 2026-10-06:** único re-despacho acotado del implementer: la fixture `_capture_fixture` de `apps/engines/acestep/tests/test_preflight.py` usa generation_options reales pero no transporta inference_steps/guidance_scale al doble DiT. Se autoriza editar solo esa factory para incorporar ambos campos, sin alterar asserts ni relajar captura estricta. Se añade ese archivo al alcance de T-16. Evidencia dirigida del implementer: 266 passed, un fallo de fixture y un skip; no se declara GREEN final hasta corregir y ejecutar la Verificación. Producción medida provisionalmente ≥88 % por archivo, revisión/QA todavía pendientes.

**Entrega CPU T-16 — 2026-10-06:** [implementación](testing/t16/cpu-implementation-report.md) e [integración](testing/t16/cpu-integration-report.md) verificadas por root. 41 pruebas declaradas y 271 dirigidas verdes, un skip/cinco avisos; cobertura añadida 59/63=93,65 %, mínimo del diff por archivo 86,36 % (archivo completo mínimo 88,34 %, medida distinta). Imagen nueva: 156 passed/1 deselected/5 warnings, sin GPU. Probe upstream/tokenizadores reales: 19 casos, 13 admitidos/seis bloqueados; 13 recibos validados intactos y entradas LM/DiT/metadata idénticas entre los controles nuevos Turbo/SFT. Fallos del doble y causa de inspect.signature conservados; corrección solo del probe, no producción ni validación. Contratos/examples/Ruff global/diff-check exit 0. Revisión fresca y QA independiente pendientes, servicio anterior todavía vigente; sin GPU, tomas nuevas, ganador ni cierre de T-16/M0. Turbo CFG7 en entrada y CFG1 interno se distinguen en ADR y evidencia.

- RED: apps/engines/acestep/tests/test_inference_controls.py::test_descriptor_sft_identity_and_limits falló con AssertionError: Turbo frente a SFT · 2026-10-06.
- RED: apps/engines/acestep/tests/test_inference_controls.py::test_adapter_sft_load_identity falló con MODEL_NOT_FOUND frente a VRAM_EXCEEDED · 2026-10-06.
- RED: apps/engines/acestep/tests/test_inference_controls.py::test_effective_defaults falló con None frente a 8/50 pasos · 2026-10-06.
- RED: apps/engines/acestep/tests/test_inference_controls.py::test_direct_invalid_controls falló DID NOT RAISE EngineError en 13 casos · 2026-10-06.
- RED: apps/engines/acestep/tests/test_inference_controls.py::test_generation_effective_steps_and_cancellation falló con INTERNAL frente a CANCELLED · 2026-10-06.
- RED: tests/test_generate_inference.py::test_cli_inference_options_and_preparation falló con SystemExit por flags desconocidos · 2026-10-06.
- RED: tests/test_generate_inference.py::test_programmatic_invalid_before_http falló HTTP_BEFORE_VALIDATION/serialización NaN frente a INVALID_PARAMS · 2026-10-06.
- RED: apps/engines/acestep/tests/test_inference_controls.py::test_native_sft_effective_receipt falló con ocho frente a 50/35 pasos · 2026-10-06.
- RED: tests/test_generate_preparation.py::test_native_receipt_checkpoint_controls falló INPUT_RECEIPT_INVALID para controles válidos · 2026-10-06.
- RED: tests/test_generate_preparation.py::test_native_receipt_checkpoint_identity_mismatch falló DID NOT RAISE ValueError en tres casos · 2026-10-06.
- RED: apps/engines/acestep/tests/test_inference_controls.py::test_dit_boundary_rejects_inference_drift falló DID NOT RAISE EngineError con ocho frente a cincuenta pasos · 2026-10-06.
- RED: test_direct_invalid_controls[ace-step-1.5-sft-params13] y test_programmatic_invalid_before_http[params7] fallaron OverflowError con CFG enorme · 2026-10-06.
- RED: tests/test_generate_preparation.py::test_native_receipt_rejects_boolean_control_capture falló DID NOT RAISE ValueError confundiendo True con 1 en dos casos · 2026-10-06.

**API CPU T-16 — 2026-10-06:** [recibo HTTP](testing/t16/http-controls-receipt.json) de dos contenedores efímeros de la imagen nueva: catálogos/identidades/límites, estimates default y override, diez rechazos por motor en estimate/jobs y model_id cruzado404. Ningún job válido/load, estados finales idle/loaded null/job null; contenedores retirados. Sonda CpuGpu sintética: no acredita NVML/telemetría ni es la instancia GPU final. Intento inicial health500 sin GPU/NVML conservado, factory efímera corregida sin modificar producto. Marcador de implementación cerrado antes de revisión, fuente estimado y tokens/eur/horas IA null; 30m de reloj no son horas IA.

**Puerta CPU T-16 conforme — 2026-10-06:** [QA independiente](testing/t16/cpu-qa-report.md) y [recibo](testing/t16/cpu-qa-receipt.json): 41 declaradas y430 completas passed/5skipped/1deselected/6warnings, exit0; cinco avisos Starlette y uno cache WinError5, sin fallo. Medida nueva59/63=93,65 %, mínimo del diff86,36 %. Contratos/4examples/14CLI/Ruffglobal/formato10/diff-check conformes. Trece recibos intactos, siete contradicciones rehasheadas rechazadas,32 hashes históricos y16tokenizer,72versos/nueve tags verificados con alcance explícito.17 documentos/237 enlaces de archivo, cero hallazgos en el alcance; anchors no comprobados. Ledger0 incoherencias/7avisos; coverage-check applies=false con degradación de base sin commits propios declarada; qa-gate E2E n/a, sin UI por diseño. PDF pendiente sin herramientas. Root corrobora seis SHA256 actuales de producción iguales a los del freeze QA. Se marcan solo CA1/2; CA3/4 y la tarea permanecen abiertas. Revisión conjunta8m de reloj, QA5m; fuentes estimadas, tokens/coste/horas IA reales null, sin inferir consumo del reloj.

**Preparación de comparación — 2026-10-06:** [recibo CPU](testing/t16/comparison-preparation-receipt.json): mismo control caption/letra T-15 por bytes/hash, siete pesos locales verificados contra lock, sin descargas ni GPU. Runner privado nuevo pasa prepare-only; su supervisión se reutiliza desde fuente T-15 fijada por hash. Antes de generar faltan comprobación del arnés GPU/paquete de escucha y preflight/permiso actual. Lectura actual: Ollama vacío, engine8101 anterior idle/loaded null, GPU2706MiB usados/12227total/9238libres. Supera1600MiB: no cargar modelo ni reutilizar excepciones anteriores. Consulta explícita pendiente al propietario para liberar GPU o autorizar estas seis tomas con cap dinámico/parada/descarga; sin respuesta no se ejecuta ese trabajo. No es un bloqueo de toda la iniciativa: quedan trabajos CPU y T-08–T-13 pendientes.

**Guardas del arnés — 2026-10-06:** [recibo CPU](testing/t16/guards-cpu-receipt.json): cuatro escenarios con dobles, corte al95 % del presupuesto agregado, fallo de monitor, job ajeno y ausencia de job propio; solo se cancela el ID reservado y no se afirma descarga si hay job ajeno. Si no existe job aceptado, se termina la CLI pendiente para impedir un envío posterior. Ollama cargado y baseline1601MiB rechazados; AST3.11 de runner/shim conforme. Preflight real en modo solo lectura rechazó ocupación actual por GPU_BASELINE_ABOVE_CEILING, sin crear contenedor de comparación ni cargar modelos/encolar jobs. Prepare-only exit0. Pruebas del arnés por root distintas de QA de producto, sin inferencia ni audio; TDD n/a para orquestación efímera. El empaquetado/escucha y revisión del arnés final siguen pendientes; no ejecutar GPU por este recibo ni por el paso de las guardas CPU.

**Paquete de escucha preparado — 2026-10-06:** `.cache/dev-cycle/t16/pack-comparison.py --session <sesión>` solo admite seis salidas terminadas, manifiestos/recibos nativos actuales, semillas/configuraciones completas y entradas LM/DiT/metadata emparejadas. Ganancia lineal común, mapa privado estable, checkpoint de copias y recuperación CPU; originales y valoraciones previas intactos. [Regresión CPU](testing/t16/packer-cpu-receipt.json): MP3 sinusoidal sintético existente de90s, manifiesto hijo válido, padre intacto, cero dB/sin limitador; recibos de generación no se atribuyen al hijo de remaster. AST3.11 conforme. No se ha empaquetado una comparación musical real ni se ha hecho escucha; faltan seis audios y revisión del arnés final. Ampliación efímera posterior al medidor: sin ventana propia, consumo desconocido y sin backdating. Entrega CPU se conserva en rama T-16; no merge a main ni cierre de tarea hasta CA3/4.

### T-17 — Auditoría de fidelidad de prompts hasta LM y DiT

- **Descripción**: Revisar el recorrido real de las instrucciones musicales entregadas por el propietario: originales/adaptaciones, petición CLI/HTTP, GenerationParams, plantilla del LM, texto/metadata del DiT y tokenización. Identificar pérdidas, presupuestos y controles ausentes antes de cambiar modelos. Auditoría CPU, sin generación ni aprobación artística.
- **Estado**: completado
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: T-06, T-07, T-15
- **Tipo**: investigación
- **Changelog**: Audita el transporte de prompts, tags y metadata hasta LM/DiT con evidencia CPU; documenta pérdidas y conserva las propuestas de vídeo para M4, sin cambiar modelos ni producto.
- **Archivos**: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t17/`, `docs/arquitectura/modelos.md`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/video.md`, `docs/roadmap/referencias/2026-10-05-video-local-por-planos.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `.cache/dev-cycle/t17/` y `data/inputs/libre/` (privados; originales/manifiestos de solo lectura; candidato nuevo en `prompt-faithful/`). La nota de vídeo recoge la aportación posterior del propietario como investigación para M4, sin implementar ni cambiar decisiones.
- **Verificación**:
  - `uv run --no-sync --all-packages python .cache/dev-cycle/t17/audit-prompts.py` → informe privado de longitudes/hashes y comparación de originales frente a entradas locales.
  - Probe CPU con fuente y tokenizadores fijados del contenedor → captura de fronteras LM/DiT y tokenización real; sin CUDA ni carga de pesos musicales; distingue captura reproducida CPU de una inferencia nueva.
  - Revisión A+B y QA sin UI → fuentes/capturas/recibos/publicación sin letras/rutas personales/secrets; preservación de originales y modelos existentes; ledger coherente.

**Criterios de aceptación**
- [x] Trazabilidad de Libre: original, adaptación de canción completa y fragmentos T-14/T-15; diferencias explícitas de instrucciones, letra/etiquetas y parámetros. Inventario privado del corpus Suno aportado, sin atribuir generaciones a canciones no ejecutadas. No confundir límite local de caracteres con presupuestos nativos de tokens.
- [x] Verificar en fuente realmente instalada y con probe CPU qué caption/letra/metadata llegan a `generate_with_stop_condition`, qué plantilla/token IDs recibe el LM y qué recibe/tokeniza el text encoder del DiT. Medir truncamiento con tokenizadores locales fijados. Registrar thinking y CoT explícitos/efectivos; no se afirma ejecutar inferencia GPU ni audición.
- [x] Informe en castellano con pérdidas/controles ausentes y prioridades de corrección para transportar íntegramente las instrucciones; separar transporte verificable de cumplimiento musical no garantizado. Pesos/producto/contratos/manifiestos/takes sin cambios. SFT aplazado; sin entrenamiento, servicios externos ni subida del corpus.
- [x] Revisión fresca y QA CPU sin UI conformes; salidas públicas solo hashes, cantidades, fuentes y conclusiones. TDD/cobertura n/a para prosa y probe efímero; no se fabrican tests de producto ni métricas de cobertura/calidad. M0 permanece abierto.

**Arranque — 2026-10-05:** prioridad literal del propietario: «sobretodo los prompts de las canciones, tienes que asegurarte de que se cumplen, revisa que le llega al llm, luego podremos ir perfeccionando el modelo, o cambiarlo». Se audita el LM musical de ACE-Step y su DiT; el LLM de composición de letras es otra función futura. TDD n/a: auditoría/prosa/probe efímero sin producto cambiado. No se ejecuta GPU. Código upstream instalado copiado a caché privada para lectura; no se actualiza el upstream.

**Evidencia de implementación — 2026-10-05:** inventario CPU completado; run-cpu-audit.ps1 exit 0 con 16 casos, CUDA oculta y tokenizadores/plantillas instalados; commit dce621408bee8c31b4fcf4811682eb9359e1bc94 verificado. CLI y POST /v1/estimate: 422 INVALID_PARAMS para original de Libre, 200 para tres adaptaciones; cero load/jobs, engine idle/unloaded, 32 registros de hash preservados. Recibos públicos en testing/t17; textos/capturas/candidato privados. Fuente de consumo estimado, horas/tokens/eur null; 38m de reloj no se convierten en horas IA. Los controles de producto identificados siguen pendientes. Nota de vídeo y referencia Markdown conservada por petición posterior del propietario para M4; sin adopción ni implementación. Revisión A+B y QA pendientes.

**Cierre técnico T-17 — 2026-10-05:** revisión A+B intento 2 conforme y [QA independiente CPU](testing/t17/report.md), status passed_cpu_documentation. Verificación de inventario y probe nativo exit 0: 16 casos; CLI/estimate 422 para original y 200 para tres adaptaciones, sin load/jobs. QA reconstruye fronteras/flags de 16 capturas, seis hashes de fuente, 16 archivos de tokenizer contra lock, 32 registros de hash preservados, 72 líneas idénticas y nueve tags del candidato. Alias T-14/control T-15 verificado por bytes/parámetros. Publicación: 17 archivos, cero fugas detectadas y 181 enlaces locales válidos. Ledger-lint exit 0, cero incoherencias; coverage-check exit 0 con applies=false por sin UI, degradación de lectura de base documentada y ninguna ruta UI en el alcance. No porcentaje ficticio, Playwright ni qa-gate aplicado; git diff --check exit 0. PDF no generado por dependencias ausentes. Costes/tokens/horas desconocidos (fuente estimado); no se infieren del reloj. Producto/pesos/takes/originales intactos. Preparación privada nueva sin audio, controles de producto pendientes; calidad musical no aprobada. Referencia de vídeo conservada a petición del propietario, sin iniciar M4. M0 abierto con 11/18 tareas completadas; T-16 borrador y T-08–T-13 pendientes. Integración preparada por allowlist, fast-forward y publicación conforme convenciones.

---


### T-18 — Preparación fiel y procedencia privada de instrucciones

- **Descripción**: Separar original y entrada efectiva, retirar únicamente decoración Markdown mediante acción explícita, exponer metadata opcional y guardar preparación/diff/hashes privados reutilizables por CLI y futuro M1. Sin resumir, traducir, sobrescribir letras ni generar audio en prepare-only.
- **Estado**: completado
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Tokens**: est. — · real — (sin medición disponible)
- **Coste**: n/a económico, ADR-0001; consumo desconocido, no igualarlo a0tokens.
- **Dependencias**: T-07, T-17
- **Tipo**: backend
- **Archivos**: `scripts/input_preparation.py`, `tests/test_input_preparation.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/adapter.py`, `apps/engines/acestep/tests/test_adapter.py`, `packages/contracts/engine-v1.json`, `scripts/generate.py`, `tests/test_generate.py`, `tests/test_generate_shift.py`, `tests/test_generate_preparation.py`, `packages/contracts/manifest-v1.schema.json`, `packages/contracts/examples/cli_run.json`, `packages/audio-post/audio_post/manifest.py`, `packages/audio-post/tests/test_manifest_errors.py`, `scripts/verify_manifest.py`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/convenciones.md`, `docs/decisiones/ADR-0028-preparacion-fiel-de-instrucciones.md` (decisión del orquestador), `docs/decisiones/README.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t18/`, `.cache/dev-cycle/t18/`, `data/inputs/libre/` (originales solo lectura), `data/preparations/`, `data/cli/` (solo publicaciones nuevas).
- **Verificación**: `uv run --frozen --all-packages pytest tests/test_input_preparation.py tests/test_generate.py tests/test_generate_shift.py tests/test_generate_preparation.py apps/engines/acestep/tests/test_adapter.py packages/audio-post/tests/test_manifest_errors.py -q -m "not gpu"` → verde; tests prueban cero HTTP/catalog/load/jobs/FFmpeg en prepare-only, defaults idénticos, hash bytes versus efectivo distinto y privacidad. `uv run --frozen scripts/export_contracts.py --check` →0. `uv run --frozen scripts/verify_manifest.py packages/contracts/examples/` → manifiestos antiguos y ejemplo opcional válidos. Probe privado `.cache/dev-cycle/t18/verify-preparation.py` →72 versos originales idénticos,9 tags íntegros, hashes anteriores intactos, adaptación con diff explícito. Comandos de entorno y basetemp local aplicados antes de ejecutar.

**Criterios de aceptación**

- [x] Original/efectivo separados; diff explícito por campo, transformaciones listadas y hashes verificables; no se sobrescriben originales ni takes/manifiestos existentes.
- [x] Default conserva texto; retirada de envoltorio Markdown opt-in conserva cada verso y cada indicación de los9 tags de Libre. No hay traducción/resumen automático ni pérdida silenciosa.
- [x] Key y compás opcionales se exponen en descriptor, CLI y generation_options (time_signature externo → timesignature upstream), sin inventar valores; briefs/conflictos/omisión y autoría cubiertos por tests. Transporte de idioma estructurado al LM queda para T-19.
- [x] Prepare-only es offline, no consulta catálogo/engine ni carga modelos/encola jobs/requiere FFmpeg; distingue preparación local y presupuesto del motor aún pendiente. Recibo privado inmutable referenciado por manifiestos nuevos.
- [x] CLI normal reutiliza preparación y publicación atómica; datos privados confinados, recibos públicos sin letras/prompt/rutas personales.
- [x] RED real por comportamiento, implementación GREEN, revisión fresca A+B y lentes condicionales, QA CPU y >=80% de producción cambiada; no declara cumplimiento artístico.

**Subtareas**

- [x] Tests RED de preservación/transformación/diff/hash; módulo puro.
- [x] Tests RED CLI optional fields/prepare-only/procedencia/conflictos; conexión al módulo.
- [x] Schema opcional y verificadores si hay referencia nueva, fixtures sintéticos públicos.
- [x] Preparación privada fiel y rúbrica de voz/rap/instrumentos/ritmo/crecimiento/outro; registrar límites.
- [x] ADR/documentación, revisión y QA con preservación de originales.


**Implementación T-18 — 2026-10-05:** subagente fresco, producción estable para revisión. [Informe y RED](testing/t18/implementation-report.md). Verificación declarada: 177 passed, 1 skipped, 5 warnings Starlette existentes; exportador `engine-v1.json up to date`; ejemplos `all valid (4 manifests)`; Ruff `All checks passed!`, todos exit 0. Probe CLI real: 72 líneas, nueve tags completos, 32 registros de hashes anteriores intactos, recibo privado inmutable; engine inaccesible, sin generación/GPU. Statements cambiados medidos: preparación 96,25 %, CLI 93,33 %, adaptador 100 %, manifiesto 86,54 %; descriptor literal en archivo con 100 %. Revisión fresca y QA aún pendientes; no se cierra por estos resultados.



- RED: tests/test_input_preparation.py::test_identity_and_explicit_tags falló porque effective era None y no existía preparación fiel · 2026-10-05 (red-pure.txt). Criterios original/efectivo y limpieza opt-in.
- RED: tests/test_input_preparation.py::test_receipt_integrity_and_immutable_publication falló porque publish no devolvía referencia SHA-256 · 2026-10-05 (red-receipt.txt). Integridad, procedencia/publicación inmutable.
- RED: tests/test_generate_preparation.py::test_offline_prepare_and_metadata falló con SystemExit 2: opciones prepare-only/key/time-signature no reconocidas · 2026-10-05 (red-cli.txt). CLI offline y metadata.
- RED: apps/engines/acestep/tests/test_adapter.py::test_time_signature_metadata_optional falló con None != '4/4' · 2026-10-05 (red-metadata.txt). Transporte opcional upstream.
- RED: packages/audio-post/tests/test_manifest_errors.py::test_preparation_reference_missing_rejected falló DID NOT RAISE ValueError · 2026-10-05 (red-manifest.txt). Referencia opcional verificada.
- RED: tests/test_input_preparation.py::test_lyrics_source_disagreement_rejected falló DID NOT RAISE ValueError · 2026-10-05 (red-source.txt). No pérdida silenciosa ni fuente de letra discordante.
- RED: tests/test_input_preparation.py::test_effective_request_hash falló None != SHA-256 canónico de la petición · 2026-10-05 (red-request-hash.txt).
- RED: tests/test_generate_preparation.py::test_malformed_receipt_with_matching_reference[structure/field_hash] falló KeyError task / DID NOT RAISE ValueError · 2026-10-05 (red-manifest-integrity.txt). Error tipado e integridad interna en verificador público.

Los errores de import del entrypoint descubiertos por CLI real se corrigieron como fallo de integración; no se presentan como evidencia TDD contractual. Hay regresión subprocess del entrypoint. Tests adicionales cubren autoría, omisión/conflictos de brief, metadata inválida, conservación BOM/CRLF/asteriscos de versos, origen de estilo distinto, fallo atómico sin temporales, desacuerdo de petición antes de HTTP, manipulación de recibos y privacidad.



**Fix1 — 2026-10-05:** [RED/GREEN y cobertura](testing/t18/fix1-report.md). A1 restaurado schema key; B1 binding exacto semilla/variante incluida base aleatoria; B2 hash fuente cruzado con bytes reales en preparación/verificador. RED: legacy key falló ValidationError; declared_lyrics_hash y manifest_false_source_hash fallaron DID NOT RAISE; execution_binding falló None frente a binding; variant_seed_binding explícita/nula fallaron DID NOT RAISE, todo antes del código correspondiente. GREEN: 185 passed/1 skipped/5 warnings existentes; exportador y cuatro ejemplos verdes, Ruff/diff-check0. Probe72/9/32 intacto. Statements cambiados 96,84/93,62/100/88,14 por ciento; descriptor literalarchivo100. El límite de agentes impidió reactivar/despachar implementer: fix ejecutado en contexto principal, degradación explícita; revisión y QA pendientes, sin cierre. Consumo estimado/null, no inferido del reloj.

**Cierre técnico T-18 — 2026-10-05:** [QA independiente](testing/t18/report.md) y [recibo](testing/t18/qa-receipt.json): Verificación declarada **185 passed, 1 skipped**, exit 0; workspace completo explícito **309 passed, 5 skipped, 1 deselected**, exit 0. Cobertura añadida **190/203 = 93,60 %**, mínimo por archivo medible **88,14 %**; descriptor literal 30/30. Exportador, cuatro manifiestos legados, Ruff y CLI real conformes. Probe **72 versos, nueve tags y 32 hashes** preservados, recibo repetido sin alterar payload ni mtime. Revisión A+B intento 2 sin gaps; primer intento fresco y segunda pasada con contextos reutilizados por límite de threads, independientes del fix. Fix en contexto principal y degradación de revisión declarados. qa: sin UI por diseño (`test-plan: n/a (sin UI)`); ledger-lint 0 incoherencias, coverage-check exit 0/applies=false, sin E2E ficticio. 129 enlaces públicos comprobados; cero fugas en el alcance examinado. PDF pendiente por dependencias ausentes. Ventana QA parcial 21:40:08–21:46:16 UTC, fuente estimado; horas IA/tokens/coste reales desconocidos. Imagen Docker T-14 sin reconstruir: nuevas opciones acreditadas en fuente CPU, integración runtime pendiente de T-19. Sin audio nuevo ni cumplimiento artístico; M0 abierto, 12/20 tareas.
- **Changelog**: El CLI conserva letra y estilo originales, permite preparar entradas offline y registra cambios explícitos y procedencia privada sin perder las indicaciones de los tags.

### T-19 — Preflight nativo de tokens y captura de entradas efectivas

- **Descripción**: Medir plantillas completas y reserva de salida LM con tokenizadores locales fijados; rechazar truncamiento, extracción o clamp no explícitos en estimate/jobs y adaptador directo; transportar idioma/metadata en formato entrenado y capturar recibo efectivo privado sin textos públicos.
- **Estado**: completado
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Tokens**: est. — · real — (sin medición disponible)
- **Coste**: n/a económico, ADR-0001; consumo desconocido.
- **Dependencias**: T-06, T-18
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/preflight.py`, `apps/engines/acestep/input_profile.py`, `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/engine_acestep.py`, `apps/engines/acestep/tests/test_preflight.py`, `apps/engines/acestep/tests/test_adapter.py`, `apps/engines/common/engine_common/server.py`, `apps/engines/common/engine_common/worker.py` (solo si recibo requiere IPC adicional), `apps/engines/common/tests/test_common.py`, `scripts/generate.py`, `tests/test_generate_preparation.py`, `packages/engine-contract/engine_contract/__init__.py` (solo campos opcionales si necesarios), `packages/engine-contract/tests/test_contract.py`, `packages/contracts/engine-v1.json`, `packages/contracts/openapi.json` (si el export genera cambios), `packages/contracts/manifest-v1.schema.json` (solo aditivo si se necesita), `packages/audio-post/audio_post/manifest.py`, `packages/audio-post/tests/test_manifest_errors.py`, `scripts/export_contracts.py`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/modelos.md`, `docs/decisiones/ADR-0029-presupuesto-operativo-de-texto-acestep.md` (reservado), `docs/decisiones/README.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t19/`, `.cache/dev-cycle/t19/`, `data/preparations/`, `data/tmp/`, `data/cli/` (recibos nuevos); locks/tokenizadores/fuente T-17 solo lectura., `apps/engines/acestep/tests/test_preflight_vram.py`, `apps/engines/acestep/tests/test_review_fixes.py`, `apps/engines/acestep/tests/test_shift.py`, `docs/calidad/evaluacion-escucha.md` (puente canónico a rúbrica de fidelidad, sin cambiar umbrales)
- **Verificación**: `uv run --frozen --all-packages pytest apps/engines/acestep/tests/test_preflight.py apps/engines/acestep/tests/test_adapter.py apps/engines/common/tests/test_common.py tests/test_generate_preparation.py packages/engine-contract/tests/test_contract.py -q -m "not gpu"` → límites exactos y +1 LM/DiT, bypass directo, idioma YAML, ausencia de CUDA/torch parent y cero load/jobs ante rechazo. `uv run --frozen scripts/export_contracts.py --check` →0. `uv run --frozen scripts/verify_manifest.py packages/contracts/examples/` →0. Probe nativo CPU `.cache/dev-cycle/t19/verify-native-preflight.py` → perfiles/hashes reales y conteos coinciden con captura del upstream fijado, original Libre bloqueado sin truncar y candidato fiel íntegro. Si requiere contenedor, ejecutar imagen existente con CUDA_VISIBLE_DEVICES vacío y sin GPU/model load; no instalar herramientas. El orquestador puede reconstruir la imagen con código local al congelar producción, reutilizando pesos y dependencias fijados, para acreditar la integración runtime.

**Criterios de aceptación**

- [x] Presupuesto nativo LM entrada+reserva real y DiT256/2048, incluye todas las cabeceras/metadatos/ramas activas; no infiere contexto de131072 ni duplica plantilla aproximada.
- [x] Estimate y jobs rechazan antes de carga/cola toda pérdida/truncamiento o duración limitada; adaptador directo protege el mismo criterio. Fallo de tokenizer/config/hash/timeout no se convierte en aceptación.
- [x] Caption largo que cabe se acepta, exceso nativo se rechaza; elevar límites administrativos solo cuando el preflight ya protege. Música instrumental y seeds/shift anteriores conservan comportamiento compatible.
- [x] Idioma validado llega como language al YAML entrenado LM y al DiT; key/compás opcionales viajan en formato upstream, sin valores inventados, conflictos ni reescritura por CoT.
- [x] Recibo planned/captured distingue estimate de frontera real, hashes token/input/flags y defaults efectivos, referencias privadas validables; logs/eventos/errores públicos no contienen letras ni prompts.
- [x] Tests diferenciales del upstream/tokenizadores fijados y regresión de16 casos auditados. Los casos que exceden presupuesto se bloquean; adaptaciones conservadas y nueva preparación cuentan íntegramente. Presencia de tags en tokens no se declara obediencia musical.
- [x] TDD, revisión fresca A+B+C/D cuando apliquen, QA CPU y >=80% producción cambiada, code-first aditivo compatible, padre sin torch/CUDA y server sin torch. Sin nuevos modelos, carga GPU ni instalaciones de herramientas en este tramo. Reconstrucción CPU de imagen permitida por el orquestador para integrar el código, sin cambiar locks ni dependencias.

**Subtareas**

- [x] RED perfil/hashes/ventana/reserva/limites; conteo local diferencial CPU.
- [x] RED estimate/jobs/directadapter y compatibilidad mock; hook opcional sin modelos.
- [x] RED idioma/compás/key/CFG/SFT extraction; wrapper mínimo y captura de frontera.
- [x] RED privacidad/publicación/recibo/integridad; logger ámbito hijo y procedencia CLI.
- [x] Exportar contratos aditivos, ADR/docs, ampliar dependencias/rúbrica T-08/T-12/T-13, revisión y QA.


**Arranque T-19 — 2026-10-05:** T-18 integrada por fast-forward y publicada como `83fc652` en main y rama de tarea. Rama actual `m0/t-19-presupuesto-prompts`. Decisión técnica dentro del objetivo autorizado: permitir reconstrucción CPU de la imagen con código local al congelar producción, porque la imagen T-14 aún no incorpora T-18; no basta un probe del código antiguo para probar el nuevo producto. No hay instalación de herramientas ni nuevos modelos, cambios de locks, GPU o audio.

**Fuentes de implementación y verificación:** [auditoría T-17](testing/t17/audit-report.md), `.cache/dev-cycle/t17/native-probe.py`, `.cache/dev-cycle/t17/upstream-acestep/`, `.cache/dev-cycle/t17/audit-input-private.json`, `models/models.lock.json` y `models/ace-step-1.5/checkpoints/` (solo lectura). Código upstream fijado a `dce621408bee8c31b4fcf4811682eb9359e1bc94`. Los 4096 tokens son política operativa explícita del backend pt, no una inferencia de model_max_length=131072. Revisar YAML entrenado, reserva completa de códigos de audio, límite LM de duración tier4 y ramas activas antes de fijar perfil. Los recibos privados originales y journals ajenos no se modifican. Orquestador propietario exclusivo de ledger, ADR-0029, arquitectura y CONTINUE; implementer propietario de producción/tests y evidencia T-19. Sin medidores propios solapados.

**Contexto adicional verificado — 2026-10-05:** corpus host T-17 en `.cache/dev-cycle/t17/audit-input-private.json`, 16 casos incluido el candidato fiel. La ruta `.cache/huggingface/t17-audit-input-private.json` del brief era una copia interna del contenedor; referencia corregida sin regenerar ni sobrescribir la auditoría. Imagen existente `music-studio/engine-acestep:m0-t14-shift`, upstream `/opt/acestep`, intérprete `/opt/acestep/.venv/bin/python`; probe CPU autorizado con repo solo lectura y salida privada nueva. Límites administrativos permitidos 16384 caracteres de estilo y 32768 de letra, solo con preflight nativo activo y tests de aceptación/rechazo; no sustituyen presupuesto de tokens ni acreditan musicalidad.

**Validación ampliada — 2026-10-06:** la suite completa explícita descubrió seis regresiones de fixtures en `apps/engines/acestep/tests/test_preflight_vram.py`, `test_review_fixes.py` y `test_shift.py`: los dobles de runtime anteriores no proporcionan la nueva dependencia CPU de preflight. Se incorporan esos tres ficheros al alcance de T-19 para mantener sus comprobaciones de VRAM, semillas y shift, sin omitir tests ni desactivar controles en producción. Evidencia RED: `.cache/dev-cycle/t19/root-full-suite.txt`, `6 failed, 349 passed, 5 skipped, 1 deselected`; exit 1. En el contenedor, el mock necesita la profundidad original y los temporales de los tests common necesitan un montaje escribible; los fallos de fixture no se declaran verificación verde. Se aplica `debug-root-cause` para separar esos problemas de los controles de producto.

**Implementación congelada y Verificación ejecutada — 2026-10-06:** [informe TDD](testing/t19/implementation-report.md), [integración](testing/t19/integration-report.md) y [cobertura](testing/t19/implementation-coverage.json). RED reales conservados, entre otros: `test_http_preflight_hook_is_optional` falló por ausencia del hook (`red-hook.txt`); `test_long_caption_is_not_rejected_by_administrative_limit` falló por límite previo de 512 (`red-caption.txt`); `test_native_receipt_interrupted_write_cannot_leave_partial_cas` reprodujo destino parcial (`red-atomic.txt`); `test_manifest_checks_the_same_native_bytes_it_hashes` reprodujo doble lectura (`red-single-read.txt`). Perfil/reserva, bypass, idioma/captura, hash/timeout/checkpoint, privacidad y vínculo con preparation tienen RED/GREEN adicionales en el informe y la caché privada. Un único re-despacho por validación corrigió los tres módulos de fixtures; producción no cambió. Verificación declarada cinco módulos **120 passed, 1 skipped**, exit 0 (`root-declared-tests.txt`); export **engine-v1.json up to date**, exit 0; cuatro ejemplos **all valid (4 manifests)**, exit 0; Ruff global **All checks passed!**, exit 0. Suite completa explícita **355 passed, 5 skipped, 1 deselected**, exit 0; imagen reconstruida **133 passed, 1 deselected**, exit 0. Cobertura de statements añadidos **327/354 = 92,37 %**, mínimo medible por fichero **86,05 %**, descriptor literal 30/30. Probe integrado **16 casos, diez aceptados/seis bloqueados**, exit 0, con producción desde imagen y ambas ramas PT antes del forward sustituido. [HTTP real](testing/t19/http-receipt.json): ocho comprobaciones, dos estimates aceptados y seis rechazos estimate/jobs, health idle, loaded/job_id null; ningún job aceptable enviado, sin GPU/audio/pesos cargados. Digest imagen en los recibos; no cambian locks ni dependencias. Revisión fresca A+B+C y QA independiente pendientes: esta nota no cierra criterios ni declara musicalidad.

**Medición de implementación:** ventana 2026-10-05T21:48:38Z–22:36:52Z, `fuente: estimado`; tokens/coste/horas IA reales desconocidos (`null`), reloj contextual 48 min, sin transformarlo en coste IA. Marcador cerrado antes de abrir revisión. Jira/Confluence desactivados; journals ajenos preservados y no promovidos.

**Fix de revisión 1 — 2026-10-06:** [informe](testing/t19/fix1-report.md). Subagente implementer fresco corrige B-01 únicamente en manifest.py y test_generate_preparation.py; no repite el re-despacho previo de fixtures ni reabre lo aprobado. RED: `test_native_receipt_rejects_rehashed_semantic_contradiction[language]` falló con **DID NOT RAISE ValueError** (`fix1/red-language.txt`); regresión de publicación real y flag legacy tienen RED contractuales adicionales. La primera fixture de integración colocaba input_receipts fuera de done.result: sus errores no cuentan como RED y se conservaron. GREEN del validador y publicación/CAS/verify, baseline válido y mutaciones recalculadas rechazadas; **98 vecinos passed**. Verificación declarada **146 passed, 1 skipped**, export up to date, cuatro ejemplos válidos y Ruff verdes. [Cobertura actual del diff](testing/t19/fix1-coverage.json) **349/377 = 92,57 %**, mínimo por fichero **86,05 %**; en el fix 22/23 = 95,65 %. Cruce oficial con base 83fc652; producción no alterada usa el freeze previo y manifest usa la medición nueva. [Diez capturas nativas integradas válidas](testing/t19/fix1-native-validation.json) con validador nuevo, originales intactos, sin repetir forward ni GPU. Se mantiene compatibilidad con campos opcionales ausentes de la fixture anterior: captured metadata se contrasta siempre contra la solicitud; planned metadata/legacy se contrastan cuando existen. El puente documental A1 queda incorporado en evaluación-escucha §3.1 y T-08/T-12/T-13, sin modificar umbrales. T-16 declara también actualizar perfil/validador al habilitar pasos/defaults SFT. Revisión 2 y QA pendientes; no se cierra la tarea aún. TDD n/a para este puente de prosa.

**Cierre técnico T-19 — 2026-10-06:** [QA independiente](testing/t19/report.md) y [recibo](testing/t19/qa-receipt.json): Verificación declarada **146 passed, 1 skipped**, suite explícita completa **381 passed, 5 skipped, 1 deselected**, cinco avisos de terceros, exit 0. Cobertura independiente actual **350/377 = 92,84 %**, mínimo por fichero **87,50 %**, descriptor literal 30/30. Ruff global, formato de 15 Python, exportador, cuatro ejemplos, 14 manifiestos CLI y diff-check conformes. Diez capturas privadas intactas validadas, baseline válido y tres contradicciones originales rechazadas; 32 hashes, 72 versos y nueve tags preservados por lectura. Padre sin torch/transformers en el probe. Imagen actual y health descargado coinciden con digest acreditado; 133 tests de imagen/16 casos/ocho comprobaciones HTTP son antecedentes de integración, no nuevas ejecuciones QA. A+B+C intento 2 frescas sin gaps; C secuencial por límite de threads. qa: sin UI por diseño (`test-plan: n/a (sin UI)`); ledger-lint 0 incoherencias, coverage-check exit 0/applies=false y degradación de base documentada; qa-gate E2E n/a, sin resultados ficticios. 252 enlaces locales y privacidad del alcance comprobados sin hallazgos. PDF pendiente por dependencias ausentes; no bloquea el backend CPU. Ventana QA 23:02:19–23:07:47 UTC, fuente estimado, tokens/horas/coste IA reales null. No GPU/audio nuevo ni cumplimiento artístico: M0 abierto con 13/20 tareas. Siguiente: controles SFT y comparación T-16; T-08–T-13 permanecen pendientes.
- **Changelog**: La generación comprueba el presupuesto real antes de aceptar letra y estilo, transporta idioma y metadata sin reescritura y registra entradas efectivas verificables de forma privada.

## Revisión de dos lentes — intento 1: Fase 2 (T-03, T-04) — correcciones pendientes

Revisión recuperada de la pasada provisional del 2026-10-05. Lentes ejecutadas: A+B+D; C no aplicó según selector automático. Contexto fresco y lectura completa del diff de producto: 41 ficheros, con hashes/mtime estables durante las reproducciones. Se mantuvo en pausa el cierre al detectar otro escritor; el usuario pidió retomar. No se han declarado completas las tareas.

Puerta previa: scope-check exit 0, sin ficheros fuera de alcance. Evidencia de aquella pasada: 87 tests verdes; cobertura del diff 84,26 % (mínimo 80 %); contratos al día; 4 ejemplos de manifiesto válidos. Ese verde no sustituye las correcciones reproducidas por los revisores. Jira y Confluence desactivados.

| ID | Grado | Tarea | Fichero:línea | Escenario reproducido | Veredicto |
|---|---|---|---|---|---|
| A1 | Important | T-03 | `packages/engine-contract/engine_contract/__init__.py:143` | `progress.fraction=2` pasa JSON Schema exportado, Pydantic lo rechaza | pendiente |
| A2 | Important | T-04 | `packages/contracts/manifest-v1.schema.json:43` | `audio_take` con `song_id=null` es aceptado, contra datos.md §3 | pendiente |
| B1 | Important | T-03 | `apps/engines/common/engine_common/server.py:223` | `timeout_s=1`, carga 2,2 s: sigue loading al vencer el plazo | pendiente |
| B2 | Important | T-03 | `apps/engines/common/engine_common/server.py:332` | Cancelación con limpieza lenta hace que health devuelva 500 | pendiente |
| B3 | Important | T-03 | `apps/engines/common/engine_common/server.py:252` | Dos jobs mismo modelo con picos 2450/100 MB informan ambos el pico/spill anterior | pendiente |
| B4 | Important | T-03 | `apps/engines/common/engine_common/server.py:49` | `/data` del montaje contractual se rechaza por PROJECT_ROOT | pendiente |
| B5 | Important | T-04 | `scripts/verify_manifest.py:14` | `peaks.json` se interpreta como manifiesto, bloqueando verificación recursiva del CLI | pendiente |
| B6 | Important | T-04 | `packages/audio-post/audio_post/manifest.py:86` | Dependencia comercial=false y raíz commercial_use=true pasa el verificador | pendiente |
| D1 | Important | T-03 | `apps/engines/common/engine_common/server.py:410` | RLock de precarga bloquea event loop: carga 300 ms retrasa heartbeat 10 ms a 300 ms | pendiente |

Veredictos por criterio: T-03 contrato exportado ✗; endpoints/token/replay ✓; hijo/NVML/unload ✓; VRAM ✓; cancelación/terminal ✓; catálogo mock ✓. T-04 validación/audio/picos ✓; esquema de procedencia ✗; hashes y ejemplos ✓. Los gaps B/D limitan los verdes de comportamiento en escenarios no cubiertos previamente. TDD original heredado: no verificable; las correcciones llevarán RED real. No hay gaps Critical ni Minor de esta pasada.

## Revisión de dos lentes — intento 2: Fase 2 (T-03, T-04) — un gap pendiente

Lentes A+B+D con contexto fresco, 2026-10-05; C no aplica según selector. Scope-check: exit 0, 43 ficheros y 0 fuera de alcance. Jira desactivado. A verificó 96 tests de contrato/engine/audio/AST y 24 de pesos; B ejecutó 49 regresiones y la integración real audio/manifiesto; D reprodujo precarga y validación concurrentes.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T-03 modelos y exportación | ✓ A1 corregido | 9 payloads de eventos inválidos rechazados por JSON Schema; referencias autónomas válidas; exportación al día |
| T-03 endpoints, token, BUSY, replay y catálogo mock | ✓ conservado | Tests de conformidad y medios sintéticos verdes |
| T-03 hijo, NVML, VRAM, cancelación y timeout | ✓ B1–B4 corregidos | Plazo durante carga, health durante limpieza, telemetría por job y montaje simulado verdes |
| T-04 validación, master, MP3 medido y picos | ✓ conservado | ffmpeg real, LUFS, true peak y pares por canal comprobados |
| T-04 esquema, procedencia, hashes y escaneo | ✓ A2/B5/B6 corregidos | audio_take exige canción; agregado comercial coherente; directorio real y manipulación detectados |
| D1 precarga y event loop | ✓ corregido | Operación lenta fuera del lock; test de heartbeat verde |
| Cobertura de los ficheros cambiados | ✓ | Gate oficial exit 0: 93,40 % ≥ 80 %; conftest sin dato declarado |
| Compatibilidad y TDD históricos | no verificable en parte | AST 3.11 y ejecución 3.12; intérprete 3.11 no disponible. No se atribuye TDD retrospectivo al código heredado |
| T-02 STACK_GLOBAL y layout | ✓ / pendiente T-06 | Rechazo fail-closed confirmado; layout contra upstream real requiere integración ACE-Step |

| ID | Grado | Tarea | Fichero:línea | Escenario reproducido | Veredicto |
|---|---|---|---|---|---|
| A1, A2, B1–B6, D1 | Important | T-03, T-04 | ver intento 1 | Correcciones reevaluadas sin nuevos defectos de corrección | corregidos |
| D2 | Important | T-03 | `apps/engines/common/engine_common/server.py:419` | Validación de entradas bajo RLock: lectura controlada de 300 ms retrasa heartbeat de 10 ms a 297 ms. Audio de 600 s PCM32 estéreo ≈230 MB retendría el lock ≈460 ms a un caudal ilustrativo de 500 MB/s, más hash | pendiente |

No hay Critical ni Minor. D2 bloquea el cierre de T-03 y la fase. T-04 conserva sus verdes y queda en revisión hasta QA. El siguiente intento será el 3.º y último del bucle acotado.

## Revisión de dos lentes — intento 3: Fase 2 (T-03, T-04) — sin gaps pendientes

Lentes A+B+D, 2026-10-05. A en contexto fresco; B y D reutilizan contextos de revisión por límite de hilos de la herramienta, con revisores independientes del autor de D2. Se reevalúan los dos ficheros corregidos y se conservan los verdes previos. C no aplica según selector; no hay cambios nuevos de seguridad. Scope-check exit 0: 43 ficheros y 0 fuera antes de añadir los informes de QA. Jira desactivado.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T-03 contrato, endpoints, hijo, VRAM, cancelación y catálogo | ✓ | A: 48 tests de contrato/common/mock/AST; exportador al día. Verdes del intento 2 conservados |
| T-04 validación, formatos, medición, picos y manifiesto | ✓ conservado | Sin cambios desde intento 2; audio real y escaneo verificados allí |
| D2 reserva BUSY, E/S y event loop | ✓ corregido | B: 12 regresiones verdes. D: 40 tests T-03, apertura retardada 300 ms con heartbeat <200 ms, operaciones competidoras rechazadas |
| D2 errores, idempotencia y reintento | ✓ | Reserva liberada por finally ante hash incorrecto, ausencia y E/S; misma ID admite reintento |
| D2 memoria del hash | ✓ | SHA-256 incremental. Benchmark sintético del revisor: 230 MiB, 0,109 s y pico Python 0,751 MiB; no representa caudal de disco |
| Alcance, constitución y evidencia RED/GREEN | ✓ | Puerta de alcance sin gaps, principios contrastados y RED real registrado en T-03 |

| ID | Grado original | Tarea | Veredicto |
|---|---|---|---|
| A1, B1–B4, D1 | Important | T-03 | corregidos en intento 2, conservados |
| A2, B5, B6 | Important | T-04 | corregidos en intento 2, conservados |
| D2 | Important | T-03 | corregido y reevaluado en intento 3 |

Resultado: 0 Critical, 0 Important y 0 Minor pendientes. QA es la siguiente puerta. Se mantienen las limitaciones declaradas de Python 3.11 real, TDD heredado y Docker/GPU. Ventanas usage-meter de implementación/revisión cerradas: sin tokens ni horas IA medidos disponibles; las duraciones de reloj no se imputan como ejecución IA.

## QA y cierre técnico de Fase 2 — 2026-10-05

qa: sin UI por diseño (`test-plan: n/a (sin UI)`). Agente QA independiente: exit 0 por la excepción canónica sin UI. `qa-gate.py` de Playwright no aplica; no hay resultados E2E fabricados. [Informe](testing/report.md) y [evidencias](testing/raw/).

- `uv run pytest -m "not gpu" -q` → `125 passed in 13.15s`, exit 0.
- `uv run ruff check .` → `All checks passed!`, exit 0; formato de los 23 Python cambiados → `23 files already formatted`, exit 0.
- Exportación → `engine-v1.json up to date`; ejemplos → `all valid (4 manifests)`; ambos exit 0.
- Gate oficial unitario `--changed-only --min 80` → exit 0, 93,62 % de media de ficheros cambiados. Global 72,81 % incluye scripts históricos; `conftest.py` sin datos se excluye y se declara. [Recibo](testing/raw/coverage-gate.json).
- `ledger-lint` → `0 incoherencias · 9 avisos`; avisos de Changelog de T-05…T-13 futuras.
- `coverage-check` → exit 0 declarativo. Lista T-00…T-13 para revisión, `eximidos_exigidos=false`, sin criterios rastreables; `rutas_ui=[]`. Aviso: base main/HEAD sin commits propios, solo alcance y cambios sin comitear comprobados. No se confunde con cobertura de UI.

El orquestador marca T-03/T-04 y Fase 2 como completadas técnicamente al cumplir sus verificaciones, revisión sin gaps y QA sin UI. M0 permanece en-progreso: 5/14 tareas. `—` en métricas significa que no existe medición completa; no se imputan como IA los minutos de reloj ni se inventan tokens.

**Pendientes de entorno e integración:** `.git` es de solo lectura en este perfil: cambios sin commit, fast-forward ni publicación en `m0/t-03-engine-contract`. La separación de commits/ramas por tarea y su integración deberán hacerse en un entorno con escritura Git, preservando el árbol y los journals ajenos. Pre-commit completo no pudo crear su entorno (`WinError 5`, directorio 0700); lint directo y formato del alcance sí pasaron. Formato global muestra 14 ficheros históricos fuera de alcance, sin modificar.

**Siguiente: T-05.** Brief determinista preparado en `.cache/dev-cycle/T-05-brief.md`. Docker devuelve acceso denegado al pipe `dockerDesktopLinuxEngine`; `wsl -d Ubuntu -e ollama ps` devuelve `Wsl/Service/E_ACCESSDENIED`. No se ha ejecutado trabajo GPU ni cambiado Ollama. T-05 permanece borrador hasta poder construir y verificar la imagen; no se sustituye su verificación por simulación. Python 3.11 real se comprobará en ese contenedor; ahora solo se ejecutó 3.12 y gramática AST 3.11. La congelación efectiva de `/v1` es la de este árbol verificado, pendiente de integración Git.

**Documentación del tramo:** documenter actualizó índice, contrato congelado en el árbol y API/uso de audio-post; orquestador actualizó CONTINUE-HERE. 71 enlaces/anclas locales comprobados, comandos PowerShell parseados y ejemplo JobRequest validado; sin nuevas pruebas GPU ni generación de datos. Sin candidatos de conocimiento que curar. Changelog/retro y cierre completo del hito se mantienen pendientes hasta T-13 y la integración Git.

**Comprobación final documental:** alcance exit 0, sin ficheros fuera tras incluir informes/documentación ([recibo](testing/raw/scope-final.json)); ledger-lint exit 0, `0 incoherencias · 9 avisos`; git diff --check exit 0. Otros 42 enlaces locales de reanudación/ledger/informe válidos y sin rutas personales. Sin cambios nuevos de código después de QA.

## Revisión de dos lentes — intento 1: Fase 3 (T-05) — fuentes sin gaps; GPU pendiente

**Fecha:** 2026-10-05. **Lentes ejecutadas:** A (conformidad), B (corrección) y C (seguridad), revisores de contexto fresco. C activada por Dockerfile, compose y contexto Docker; D no activada por el selector determinista. C se lanzó al liberarse un puesto de concurrencia. Base `main` = `6b371e9`, unión del diff y ficheros nuevos; journals preexistentes excluidos de alcance, sin código de producción oculto. [Alcance](testing/t05/raw/scope-review.json) sin salidas ni avisos; [selector](testing/t05/raw/lenses.json).

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T-05: CUDA 12.8.1 por digest, Python 3.11.14 gestionado y ACE-Step fijado por commit | ✓ | Dockerfile y build final exit 0, [recibo](testing/t05/raw/build-fixed-cache.log) |
| T-05: FFmpeg 7 LGPL shared, lame/soxr/opus, torchcodec | ✓ | Test de entorno real y [FFmpeg](testing/t05/raw/ffmpeg-final.log): stdout 0, exit 1 esperado |
| T-05: common/contrato, mounts y variables, usuario sin root y puerto localhost | ✓ | Compose y cuatro tests reales dentro del contenedor, [pytest](testing/t05/raw/pytest-final.log) |
| T-05: sin xformers/flash-attn, log SDPA/torch | ✓ | Dockerfile, test de arranque con [RED](testing/t05/raw/red-startup.log) y [GREEN](testing/t05/raw/green-startup.log) |
| T-05: importación CPU del handler | ✓ | [Probe](testing/t05/raw/handler-import-cpu.log), CUDA oculta, exit 0, sin carga de modelos |
| T-05: consistencia completa de dependencias | ✗ | [pip check](testing/t05/raw/pip-check-combined.log), 152 paquetes, exit 1: nano-vllm requiere flash-attn |
| Ausencia de flash-attn impide backend pt | Descartado (rebatido) | Upstream fijado `acestep/llm_inference.py:706-707` utiliza `_load_pytorch_model` para pt; import nano-vllm en rama vllm, línea 734. T-06 debe forzar pt: el argumento upstream por defecto es vllm. No se afirma pip check verde ni carga/generación probadas |
| T-05: sm_120 y matmul BF16 real | ✓ (adenda posterior) | Autorización expresa del propietario; comando exacto → 262144.0, exit 0, [recibo](testing/t05/raw/bf16-final.log). Lente A verificó el recibo, sin cambios de código |
| Constitución y seguridad introducida | ✓ | C: 110 artefactos HTTPS con SHA-256, 2 imágenes por digest, token externo obligatorio, contexto sin datos/env; sin inyección o nuevos lectores de pesos |
| Servicio HTTP y autenticación efectiva ACE-Step | No verificable | Factoría pendiente de T-06; no se acredita motor operativo |
| T-07: cambio documental por material privado | ✓ | ADR-0023, spec y protocolo mantienen B-02; letra privada no versionada, autoría pendiente, sin audio ni cierre |

| # | Grado | Gap | Tarea | Corrección / veredicto | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin gaps de requisitos, corrección o seguridad pendientes | T-05 | No requiere corrección de fuentes; no habilita cierre con BF16 pendiente | A y adenda CPU, B y adenda de dependencias, C sin hallazgos |

**Evidencia ejecutada por los revisores:** lectura completa del diff y nuevos archivos por bloques, lock TOML válido, AST Python 3.11, `git diff --check` exit 0, `ledger-lint` 0 incoherencias y 9 avisos de Changelog futuro; C comprobó estáticamente hashes, digests, usuario, puertos y mounts. Docker ejecutado por implementer; los revisores leyeron los recibos, sin repetir GPU ni acceder a secretos/entrada privada. Matplotlib usa caché temporal en `/tmp`; el import CPU termina correctamente. Cobertura Python del shell no se inventa.

**Medición:** ventana de revisión cerrada; `usage-meter` degradó a `fuente: estimado`, sin tokens, coste u horas IA medidos. 10 minutos de reloj no se imputan como IA. Jira/Confluence desactivados. No se han promovido journals ni candidatos ajenos. Tras la adenda GPU, T-05 pasa a **en-revision** hasta QA; M0 permanece abierto, 5/14 tareas completadas.

**QA y cierre posterior:** [informe T-05](testing/t05/report.md), cuatro verificaciones canónicas acreditadas, 125 pruebas locales sin GPU verdes, lint/ledger sin incoherencias. QA sin UI por diseño (`test-plan: n/a (sin UI)`); sin qa-gate E2E fabricado y sin porcentaje de cobertura Python para shell/config. Ventana QA cerrada con degradación estimada, sin horas IA medidas; sus 11 minutos de reloj no se imputan como ejecución IA. T-05 marcada completado; M0 en-progreso, 6/14 tareas. PDF pendiente por herramientas ausentes, sin instalar ni escribir fuera del proyecto.

## Revisión de dos lentes — intento 1: Fase 3 (T-06) — dos defectos de corrección pendientes

**Fecha:** 2026-10-05. **Lentes:** A+B+C en paralelo, contexto fresco; C activada por Dockerfile y `exec` fijado por SHA en el parche, D no activada. Base `main` = `19ab239`, diff y archivos nuevos, sin reabrir T-05. Alcance exit 0, sin salidas ni avisos; journals preexistentes fuera de autoría T-06. T-07 es preparación documental existente, sin cierre. Jira/Confluence desactivados; no se promueve conocimiento ajeno.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Modos BF16/offload, PT, sin INT8/compile y carga configurable | ✓ fuentes CPU; GPU pendiente | `adapter.py:54,116,162`, tests CPU del borde de carga; cuatro componentes reales aún sin cargar |
| Parche seguro silence_latent y hashes previos | ✓ CPU | `patches.py:18,85`, parche sobre upstream real y hash recalculado por C |
| Parámetros/variantes y semilla ejecutada | ✗ | B1: upstream convierte semilla por float y pierde precisión; meta puede discrepar de la ejecución |
| Clasificación del agotamiento VRAM | ✗ | B2: retorno OOM capturado por upstream termina como INTERNAL |
| Callbacks, cancelación y WAV FLOAT/48 kHz/estéreo | ✓ borde CPU | Muestras exactas, hooks retirados; no acredita modelo GPU |
| Descriptor MIT/literal/hashes/capacidades false y contrato opcional | ✓ | Tests de contrato 15 passed, exportador al día; ADR-0024 |
| Constitución, autenticación y seguridad introducida | ✓ fuentes | C sin hallazgos; [informe C](testing/t06/review-c-attempt-1.md) |
| Documentos y recibos públicos | ✓ tras corrección | Texto de Python 3.11 actualizado; A1 anonimizado y búsqueda sin rutas personales |
| Verificación/cobertura/estado | ✓ CPU; GPU no verificable | 35 passed, 1 deselected; 92,31 % en el contenedor. T-06 sigue en-progreso |

| # | Grado | Gap | Tarea | Corrección / veredicto | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Rutas personales en repr de tracebacks | T-06 | Corregido: anonimización de barras normales, duplicadas y slash; ninguna ruta personal restante | `testing/t06/raw/red-pretrained-bf16.log:10` antes del arreglo; búsqueda completa sin coincidencias después |
| B1 | Important | Semillas grandes pierden precisión y variantes pueden repetirse | T-06 | Corregido en fix1; pendiente validación del intento 2 | `adapter.py:95,253` del intento 1; seed=9007199254740992/n_outputs=2 terminaba con dos semillas ejecutadas iguales pero meta de la segunda=9007199254740993; reproducción CPU con parser upstream real |
| B2 | Important | OOM capturado por upstream pierde código VRAM_EXCEEDED | T-06 | Corregido en fix1; pendiente validación del intento 2 | `adapter.py:175,184` del intento 1; retorno ('CUDA out of memory…', False) se traducía a INTERNAL; LM/generación tenían traducción genérica equivalente |

**Evidencia independiente:** A ejecutó contrato (15 passed), exportador, ledger-lint (0 incoherencias/8 avisos futuros), diff-check y anonimización; B y C ejecutaron adapter+contrato (45 passed, 1 skipped). B reprodujo ambos fallos CPU; C recalculó el SHA upstream. No se ejecutó GPU ni reconstrucción por revisores. Interop/OpenAPI no aplican.

**Medición:** revisión cerrada antes de abrir `T-06-fix1`; `usage-meter` degrada a estimado, sin tokens/coste/horas IA medidos. Los defectos vuelven al mismo implementer para corrección, seguida del intento 2 de 3. No se cierra T-06 ni M0 con estos resultados.

**Fix1 — 2026-10-05:** [recibo separado](testing/t06/fix1-report.md). RED: `test_large_seeds_exact_distinct_after_real_parser` falló por segunda semilla 9007199254740992 frente a 9007199254740993; `test_cuda_oom_status_becomes_vram_exceeded` falló en DiT/LM/generación por INTERNAL frente a VRAM_EXCEEDED; ambos el 2026-10-05. GREEN inicial 4 passed; casos adicionales inválidos RED y GREEN conservados. Parser exacto uint64, rechazo de desbordamiento antes de generar, status/error/excepciones OOM clasificados sin exponer texto upstream. Torch CPU conserva las tres semillas límite comprobadas. Imagen corregida `sha256:9934f4f4cc13bdde43f534b961c1fda7620f5cc0b1df67372148b0959e0d2403`; build exit 0. Verificación CPU contractual → **55 passed, 1 deselected**, exit 0; cobertura real **92,96 %**, todos los ficheros ≥80 %. Ruff/formato verdes. Fix1 cerrado 12:37:49–12:53:46 UTC, estimado sin horas/tokens/coste medidos; 16 min son reloj. Segunda revisión abierta después; GPU sigue sin ejecutar, última ocupación 2.906 MiB, resolución pendiente del propietario.

## Revisión de dos lentes — intento 2: Fase 3 (T-06) — insuficiencia VRAM upstream pendiente

**Lentes A+B+C**, frescas y en paralelo. Puerta de alcance exit 0, sin avisos; C activada por los mismos motivos, D no activada. Se conserva lo aprobado del intento 1; A1 corregido y sin rutas personales, B1 validado con semillas exactas. A y C sin gaps nuevos. B detecta un caso adicional dentro de B2 con evidencia del método upstream real.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| B1: semillas, límites, overflow, sin fallback | ✓ corregido | Parser real y tests independientes, metadatos coincidentes |
| B2: OOM por status/error/excepción en DiT/LM/generación | ✓ corregido | Pruebas de los tres caminos y mensajes públicos constantes |
| B2: insuficiencia de VRAM detectada antes de difusión | ✗ | `_vram_preflight_check` real devuelve `Insufficient free VRAM…`, aún clasificado como INTERNAL |
| Seguridad del parser/errores y autenticación | ✓ | C sin hallazgos; SHA de loader/parser coincide y mensajes no filtran texto upstream |
| Conformidad, documentos, RED/GREEN, cobertura y estado | ✓ CPU | A conserva aprobados; contrato/exportador verdes; 92,96 % contenedor, estado abierto |
| Carga/generación/descarga real GPU | No verificable | Test preparado, aún no ejecutado |

| # | Grado | Gap | Tarea | Corrección / veredicto | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Rutas personales | T-06 | Corregido, conservado | Búsqueda pública sin coincidencias |
| B1 | Important | Semillas grandes | T-06 | Corregido y validado | Valores efectivos 9007199254740992/993 distintos; overflow previo sin artefactos |
| B2 | Important | Clasificación incompleta del preflight VRAM upstream | T-06 | Pendiente de fix2 | `adapter.py:57,326`; método real `_vram_preflight_check`, SHA `4126b89bea9032d5ad1a5d9f906410ef4ede79a1d2328635aa365010473ee086`: 1,1 GB necesarios/0,1 GB libres produce INTERNAL en vez de VRAM_EXCEEDED |

**Ejecución independiente:** A regresiones+contrato 35 passed, exportador/ledger verdes; B y C adapter+regresiones+contrato **65 passed, 1 skipped**. B reprodujo el preflight real mediante AST sin torch/GPU; C verificó SHA del parser. Sin cambios de producción durante la pasada. Revisión cerrada antes de abrir fix2; medición estimada, sin horas/tokens/coste medidos. Se aplica debug-root-cause a B2 y después revisión **intento 3 de 3**, sin reabrir aprobados salvo evidencia nueva.

**Autorización GPU recibida — 2026-10-05:** el propietario autoriza expresamente la prueba de **30 s** con ocupación 2.874 MiB y el límite de VRAM del adaptador. Cubre esa prueba preparada, sin cerrar aplicaciones ni cambiar servicios. Ollama no tenía modelo cargado; se volverá a comprobar justo antes de ejecutar. La autorización no acredita ejecución ni se extiende a la canción privada de 255 s.

**Fix2 — 2026-10-05:** [cuatro fases de debug-root-cause](testing/t06/fix2-report.md). RED `test_real_preflight_failure_classified_vram[1-30]`, `[2-120]` y `test_preflight_isolation_and_equivalent_statuses` reproducen el retorno real con insuficiencia VRAM · 2026-10-05; aislamiento y prueba previos al fix confirman predicado de dispositivo True/motivo False. Se añade únicamente `insufficient free vram` a la clasificación; casos suficientes, CPU y offload descartados con evidencia, semillas intactas. GREEN 3 casos y suite; imagen `sha256:ecae5c354e3ec7350e1a6a6fc0118c8f3faf5ff4dc976a83e1444e82f3cd95b3`, build exit 0. CPU contractual **58 passed, 1 deselected**, exit 0; cobertura real **92,96 %**, todos los ficheros ≥80 %. Fix2 cerrado antes de abrir intento 3, estimado sin tokens/coste/horas IA medidos. Candidato de gotcha devuelto sin aprobar/publicar; journals existentes preservados. GPU aún no ejecutada.

## Revisión de dos lentes — intento 3: Fase 3 (T-06) — fuentes sin gaps pendientes

**A+B+C**, contexto fresco y paralelo, reevaluación exclusiva de fix2 y aprobados conservados. Puerta alcance exit 0, 0 salidas/avisos; C por Dockerfile/exec, D no activada. No se han reabierto T-05 ni journals ajenos. Jira/Confluence desactivados.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| A1: recibos sin rutas personales | ✓ conservado | Anonimización verificada en intentos anteriores |
| B1: semillas exactas, límites y variantes | ✓ conservado | Regresiones verdes, sin cambios en fix2 |
| B2: OOM y preflight de VRAM insuficiente | ✓ corregido | `adapter.py:62,327`; `test_preflight_vram.py:59,83` integra método real por AST/hash |
| Suficiente VRAM, CPU/offload y errores sin información privada | ✓ | `test_preflight_vram.py:84,90,105,109`; CPU conserva INTERNAL, mensajes constantes y sin artefactos |
| Constitución, alcance y causa raíz/TDD | ✓ | Presupuesto intacto, RED 3 failed e hipótesis antes de cambiar producción; 4 fases documentadas |
| Descriptor, factoría, generado, WAV/cancelación y modos | ✓ fuentes CPU conservadas | Exportador al día, aprobados anteriores conservados |
| Imagen y cobertura reales CPU | ✓ | Imagen `ecae5c35…`, 58 passed/1 deselected, 92,96 % y todos los archivos ≥80 % |
| Carga/generación/descarga real GPU | No verificable en esta revisión | Autorización recibida; ejecución siguiente por el orquestador |

| # | Grado | Gap | Tarea | Corrección / veredicto | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Rutas personales | T-06 | Corregido y validado | Sin coincidencias públicas |
| B1 | Important | Semillas grandes | T-06 | Corregido y validado | Semillas consecutivas exactas, uint64 y overflow previo |
| B2 | Important | OOM/preflight VRAM clasificado como INTERNAL | T-06 | Corregido y validado | Retorno upstream real ahora VRAM_EXCEEDED, 23 regresiones B verdes |

**Evidencia independiente:** A regresiones+contrato 38 passed, exportador/ledger/alcance verdes; B regresiones fix1+fix2 23 passed; C preflight+regresiones+adapter+contrato **68 passed, 1 skipped**, SHA upstream coincidente, diff-check exit 0. Sin hallazgos de seguridad nuevos. No se repitió build ni ejecutó GPU por revisores. Ventana de revisión cerrada antes de QA, estimada sin horas/tokens/coste medidos. **0 gaps pendientes**; aún no habilita cerrar T-06 sin su verificación GPU.

## Revisión de dos lentes — intento 1: Fase 3 (T-07) — corrección pendiente

2026-10-05, base main=11c1884. Lentes A+B+D frescas; scope exit 0, sin avisos/exclusiones de usuario. C false, D true por espera en publicador síncrono. [Tabla completa y evidencia ejecutada](testing/t07/review-attempt1.md). A confirma criterios técnicos, TDD, 94,27 % y constitución; escucha pendiente correctamente declarada. D sin hallazgos, pruebas 1/8/64 variantes sintéticas con post stub. Journals ajenos preservados. Jira/Confluence desactivados; no promoción de conocimiento.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | generate.py:479 cancela y descarga antes del terminal; 409 reemplaza KeyboardInterrupt y conserva modelo | T-07 | pendiente, root corroboró; fix1 con TDD | mock real stage_delay_ms=1000: propagated=ValueError ENGINE_HTTP_409; después idle con loaded=mock/cpu |

T-07 sigue en-progreso. 0 Critical / 1 Important / 0 Minor. Escucha humana pendiente separada del gap; no cierre por pruebas verdes parciales.

## Revisión de dos lentes — intento 2: Fase 3 (T-07) — corrección pendiente

2026-10-05, lentes A+B+D frescas; D secuencial tras A/B por límite de threads, sin degradar contexto fresco. Scope exit0 sinavisos, Cfalse Dtrue. [Tabla/evidencia completa](testing/t07/review-attempt2.md). Técnica/constitución/docs aprobados; B1 corregido con exit130 y loadedNone. Revisión solo del fix y evidencia nueva, aprobados anteriores conservados. Jira/Confluence desactivados; journals ajenos intactos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Cancelación inmediata y error primario | T-07 | corregido fix1 | 63CLI verdes, mockreal exit130/idle/loadedNone; cobertura93,83% |
| B2 | Important | generate.py:412/413/536 duplica cleanup al fallar antes accepted=False | T-07 | pendiente fix2, deduplicado con D | jobdone+unload409persistente: 600s sintéticos/6001POST; dos deadlines300 |

0 Critical / 1 Important pendiente / 0 Minor. T-07 permanece en-progreso. Revisión3 será última; escucha pendiente correctamente declarada.

## Revisión de dos lentes — intento 3: Fase 3 (T-07) — sin gaps pendientes

2026-10-05. Lentes A+B+D frescas y secuenciales por límite de threads; scope0 sinavisos niusuarioexclusiones, Cfalse Dtrue. [Tabla completa y evidencia](testing/t07/review-attempt3.md). A técnica/constitución/docs/alcance conforme; B confirma errorprimario/nooutputs y una ventana; D confirma presupuesto único y conserva escalado aprobado. 64CLI verdes, cobertura93,98%. Jira/Confluence desactivados; journals ajenos intactos, sin promoción de conocimiento.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Cancelación inmediata/409/error primario/modelo cargado | T-07 | corregido fix1 | mockreal130 e idle/loadedNone; primario/sanitización/ajenos verdes |
| B2/D2 | Important | Cleanup fallido reinicia presupuesto300→600 | T-07 | corregido fix2 | flag anteshelper yfinallyguard; B3cuatrorepros yD3regresión:300súnico/nooutputs/sentinelintacto |

0 Critical / 0 Important pendiente / 0 Minor. Revisión cerrada sin gaps técnicos, no cierre de T-07: faltan QA y primera impresión del propietario. QA sin UI por diseño; no porcentaje E2E ficticio.

## Revisión de dos lentes — intento 1: Fase 4 (T-14) — corrección pendiente

Lentes A+B frescas, B recuperada después de interrupción sin veredicto previo duradero. Scope0/avisos[]; Cfalse/Dfalse. [Informe y criterios](testing/t14/review-attempt1.md). A conforme CPU/preparación con GPU/QA/escucha pendientes; B reproduce gap programático. Jira/Confluence desactivados; journals ajenos intactos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | shift entero enorme desborda math.isfinite antes del rango | T-14 | pendiente fix1 | generate.py:290, adapter.py:142; 10**400→OverflowError en ambos helpers, no INVALID_PARAMS |

0 Critical / 1 Important / 0 Minor; no GPU generada ni calidad aprobada. Fix acotado con TDD antes de revisión2.

## Revisión de dos lentes — intento 2: Fase 4 (T-14) — sin gaps pendientes

Lentes A+B frescas en paralelo, traspaso completo del intento1. [Criterios y evidencia](testing/t14/review-attempt2.md). Scope0sinavisos/usuarioexclusiones; Cfalse/Dfalse. B1 corregido y corroborado con entradas enormes/NaN/inf/tipos/válidos, error tipado y no POST. A39tests0,39s yB39tests0,41s verdes, sin nueva GPU ni privados. Jira/Confluence desactivados, journals ajenos preservados.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Entero enorme desborda finitud antes de rango | T-14 | corregido fix1 | rango antes de finite tras tipo; RED4→GREEN4/39, reproducción B independiente INVALID_PARAMS |

0 Critical / 0 Important pendiente / 0 Minor. T-14 permanece en-progreso para QA sin UI y seis tomas GPU autorizadas. Calidad y ganador siguen pendientes del propietario.


**Escucha del propietario T-14 — 2026-10-05:** preferencias recuperadas de su formulario abierto, sin recargarlo: B/B/B; mapa privado: shift1 preferido en dos pares y shift3 en uno. Sin notas ni puntuaciones numéricas. El propietario sigue percibiendo falta de naturalidad de voces, ritmo e instrumentos frente a Suno y su prompt. Calidad no aprobada; no hay ganador consistente del ajuste. Recibo privado owner-feedback-2026-10-05.json. T-14 permanece completada técnicamente; T-15 investiga el siguiente paso sin alterar audios/manifiestos anteriores.

## Revisión de dos lentes — intento 1: T-15 — preparación requiere fix1

Lentes A+B frescas, C/D=false; alcance exit0 sin avisos. [Informe](testing/t15/review-attempt1.md). Generación y QA pendientes, T-15 en-progreso.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R1 (A1/B1) | Important | Spill comprobado después de tres salidas | T-15 | Pendiente fix1 de supervisión privada | CPU cap1000/pico960 marca spill sin excepción; arnés esperaba final de tanda |
| R2 (B2) | Important | MP3 parcial adoptado con metadato fijo90s | T-15 | Pendiente fix1 de empaquetado privado | MP3 decodificable10,032s cumple LUFS/pico; falta comprobar duración/procedencia |

No rebates; 0 Critical, 2 Important, 0 Minor pendientes. TDD n/a: prosa/config/orquestación efímera sin cambios de producto. Ventanas implementación/revisión estimadas, tokens/horas IA/€ desconocidos; no se convierten los minutos de reloj en coste.

## Revisión de dos lentes — intento 2: T-15 — correcciones conformes

Lentes A+B de contexto fresco; C/D=false. [Informe](testing/t15/review-attempt2.md) y [fix1 con evidencia CPU](testing/t15/fix1-report.md). Los dos revisores ejecutaron el probe CPU real, exit 0; no GPU ni cambios de producto. Generación y QA aún pendientes en esta puerta.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R1 (A1/B1) | Important | Parada tardía ante presupuesto/spill | T-15 | Corregido: monitor 2 s, umbral conservador 95 %, ID propio reservado y cancelación exclusiva; idle/unloaded exigido | Probe reproduce umbral, fallo de monitor y job ajeno; no cancela ajeno ni declara spill real por crecimiento agregado |
| R2 (B2) | Important | MP3 parcial certificado como 90 s | T-15 | Corregido: ffprobe duración/layout, checkpoint de hashes/procedencia/ganancia antes de rename, archivos exclusivos | MP3 real de 10 s rechazado; 90 s/48 kHz/estéreo aceptado; checkpoint ausente/hash distinto rechazados |

Fusión: 0 Critical / 0 Important / 0 Minor pendientes, sin rebates. TDD/cobertura n/a para prosa/config/orquestación efímera; sin suite de producto nueva. Journals ajenos preservados, sin promoción de conocimiento. Coste/tokens/horas IA desconocidos, ventanas estimadas; no se infieren a partir del reloj.

## Revisión de dos lentes — intento 1: T-17 — trazabilidad pendiente de revalidación

A+B de contexto fresco; selector C/D=false. Scope exit 0, sin avisos ni exclusiones de usuario; siete journals ajenos excluidos por regla predeterminada y preservados. [Informe](testing/t17/review-attempt1.md). A/B verificaron 16 casos, seis hashes de fuente, 16 archivos de tokenizadores/configuración, 32 hashes preservados y 72 líneas cantadas; cuatro recibos coinciden con las fuentes privadas. Ningún cambio de producto ni inferencia. QA final aún pendiente.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Equivalencia T-14/control T-15 no publicada | T-17 | Recibo de alias y diferencias de parámetros añadidos; pendiente revalidar | Archivos caption/letra idénticos por bytes; T-14 shifts 1/3, T-15 shift 1 |
| A2 | Minor | Frase del candidato agrupa tres afirmaciones | T-17 | Separadas preparación, conservación y traducción; pendiente revalidar | Informe actualizado, sin cambio de conclusión |

B sin defectos. Sin rebates. Ventana revisión inicial fuente estimado, tokens/horas/eur null; corrección documental iniciada durante la revisión, sin atribuir duración de reloj a consumo IA. No se declara cierre hasta revalidación y QA.
## Revisión de dos lentes — intento 2: T-17 — correcciones conformes

A+B de contexto fresco; C/D=false por selector automático. Scope exit 0, cero avisos y exclusiones de usuario; journals ajenos preservados. [Informe](testing/t17/review-attempt2.md). A1 y A2 corregidos; no se reabren criterios aprobados ni hay rebates. A y B reconstruyeron independientemente el recibo de linaje en memoria, sin ejecutar sus escrituras: identidad de caption/letra, ocho parámetros comunes, hashes de configuración, diferencias de shift y alias único entre 16 casos, PASS/exit 0.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Trazabilidad explícita T-14/control T-15 omitida | T-17 | Corregido y revalidado | fragment-lineage-receipt.json y párrafo de equivalencia; ambas reconstrucciones independientes coinciden |
| A2 | Minor | Frase del candidato agrupa tres afirmaciones | T-17 | Corregido y revalidado | Preparación/conservación/traducción separadas, conclusiones conservadas |

Fusión: 0 Critical / 0 Important / 0 Minor pendientes. Fuente de consumo estimado; tokens/horas/coste null. QA final sigue pendiente en esta puerta; no se declara calidad musical ni cierre de M0.

## Revisión de dos lentes — intento 1: T-18 — tres correcciones pendientes

A+B frescas; C/D=false por selector, alcance exit0 sin avisos ni exclusiones de usuario. Journals ajenos preservados. [Informe y evidencia](testing/t18/review-attempt1.md). A1 Important: descriptor key restringe schema legado (longitudes0/33); B1 Important: seed/variante sin vincular al recibo; B2 Important: lyrics_sha256 declarado puede discrepar de bytes fuente. Sin rebates, cero Critical/tres Important/cero Minor. A17 tests verdes, B177passed/1skipped y dos reproducciones; exportador y cuatro ejemplos verdes. T-18 vuelve a en-progreso para fix1TDD; QA pendiente. Medición estimada, consumo real desconocido; revisión cerrada antes del fix.


## Revisión de dos lentes — intento 2: T-18 — correcciones conformes

[Tabla y evidencia](testing/t18/review-attempt2.md). A1/B1/B2 corregidos y aprobados anteriores conservados; cero gaps pendientes. A7 regresiones/exportador/ejemplos verdes; B185passed/1skipped/5warnings y nueve casos de ejecución malformada rechazados. Alcance0 sin avisos ni exclusiones de usuario, C/Dfalse. Contextos de revisión reutilizados por límite de threads, independientes de implementación; degradación explícita. Journals ajenos preservados, sin promoción de conocimiento. QA pendiente; T-18 en-revision, no cierre. Consumo estimado/null; revisión cerrada antes de QA.

## Revisión de dos lentes — intento 1: T-19 — corrección pendiente

Lentes A+B+C frescas; C ejecutada después de A por límite de threads. D no aplica. [Veredictos y gaps completos](testing/t19/review-1.md). Scope exit 0; A: CA1–CA6 acreditados, CA7 pendiente de puertas. B reproduce contradicción de solicitud/efectivo: CA5 no acreditado para cierre. C sin hallazgos.

| ID | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Minor | Falta puente desde T-08/T-12/T-13 a la rúbrica existente y recibos de fidelidad | T-19 | pendiente documental | tasks.md:674; testing/t18/preparation-report.md:23 |
| B-01 | Important | Recibo autoconsistente acepta idioma/shift distintos de la solicitud y CoT true | T-19 | pendiente, confirmado por root | manifest.py:207/267; publicación y verify_manifest reales reproducidos por B |

Revisión: 120 tests declarados A/B y 72 C verdes, sin sustituir el gap reproducido. Ventana conjunta 22:37:20–22:45:07 UTC, fuente estimado; tokens/coste/horas IA reales null. Marcador cerrado antes de fix1. T-19 vuelve a en-progreso; QA pendiente. Jira/Confluence desactivados, journals ajenos intactos.

## Revisión de dos lentes — intento 2: T-19 — correcciones conformes

[Veredictos completos y evidencia](testing/t19/review-2.md). A+B+C frescas, independientes de implementación; A/B paralelas y C posterior por límite de threads. D no aplica. Scope exit 0, sin avisos ni exclusiones de usuario. Traspaso íntegro del intento 1, aprobaciones conservadas, sin rebates.

| ID | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Minor | Puente documental desde T-08/T-12/T-13 a rúbrica y recibos | T-19 | corregido y revalidado | evaluación-escucha §3.1, notas/dependencias tasks.md, umbrales conservados |
| B-01 | Important | Recibo autoconsistente contradice idioma/shift/CoT solicitados | T-19 | corregido y revalidado | manifest.py:217/232/246; B acepta baseline y rechaza tres contradicciones originales, diez capturas válidas intactas |

Fusión: cero gaps pendientes. A 26 regresiones verdes; B 264 passed/1 skipped y probes independientes; C 38 passed/17 deselected, sin hallazgos. CA1–CA6 conformes; CA7 pendiente de QA independiente, tarea en-revision. Cobertura leída 349/377 = 92,57 %, mínimo 86,05 %. Ventana 22:53:00–23:01:38 UTC, fuente estimado/null, cerrada antes de QA. No se promueven journals ajenos ni se declara calidad musical. Jira/Confluence desactivados; sin GPU/audio nuevo.

## Revisión de dos lentes — intento 1: T-16 — tramo CPU conforme, GPU pendiente

[Tabla completa y evidencia](testing/t16/review-1.md). A+B frescas, independientes de implementación; B posterior a A por límite de threads, sin reutilizar contexto. C/D=false por selector. Scope exit0, sin fuera de alcance, avisos ni exclusiones de usuario; journals ajenos excluidos por regla predeterminada y preservados. A valida CA1 y obligaciones CPU de CA2, sin declarar QA terminado; 104 pruebas propias y una del hook real verdes, cobertura oficial cruzada59/63=93,65 %, mínimo del diff86,36 %. B ejecuta271passed/1skipped/5warnings y reproduce SFT50/CFG7, progreso/cancelación, trece recibos nativos intactos y transporte LM/DiT/metadata emparejado.

| ID | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin hallazgos en el tramo CPU | T-16 | no necesaria | Revisión fresca A/B y reproducciones independientes |

Fusión: cero Critical/Important/Minor pendientes, sin rebates. Se pasa a QA CPU independiente; T-16 sigue en-progreso, CA3/4 sin ejecutar ni marcar completas. Imagen HTTP aislada acreditada con sonda CPU sintética, no telemetría GPU. Jira/Confluence desactivados, sin nuevos candidatos ni promoción de journals. Fuente estimado y consumo real desconocido; cerrar revisión antes de abrir QA.

## Revisión de dos lentes — intento 1: T-16 — arnés privado, cuatro correcciones pendientes

[Tabla completa](testing/t16/harness-review-1.md). A+B frescas, B antes de A por límite de threads; no reabre la revisión/QA CPU de producto. Scope0, selectorC/Dfalse sobre Git; privados declarados y leídos expresamente, sin hallazgos adicionales concretos de seguridad/rendimiento. Se conserva snapshot previo al fix en caché.

| ID | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| H1 | Important | Timeouts de arranque/logs omiten limpieza | T-16 | pendiente | Dobles B, run-comparison.py:116/162 |
| H2 | Important | Referencia parcial bloquea recuperación | T-16 | pendiente | Doble B, pack-comparison.py:165/167 |
| H3 | Important | Validación MP3 sin import math | T-16 | pendiente | Doble A reproduce NameError |
| H4 | Important | Stop indirecto de job ajeno detectado | T-16 | pendiente | Lectura A del finally tras supervise |

Verificaciones CPU independientes, sin Docker/GPU/audio original ni escrituras por revisores. Ventana de revisión00:16:45–00:22:14 UTC; fuente estimado, tokens/coste/horas IA reales null. Investigación CPU de prerrequisitos T-08 realizada por root durante la espera de revisores, sin ventana propia ni consumo atribuido a esa tarea. T-16 sigue en-progreso; corrección del arnés por root (TDD n/a: orquestación efímera), con regresiones CPU antes de segunda revisión fresca. No ejecutar modelos por el paso de guardas anteriores. Jira/Confluence desactivados, journals ajenos intactos.

**Fix1 del arnés — 2026-10-06:** [informe y evidencia](testing/t16/harness-fix1-report.md), [recibo de fuentes](testing/t16/harness-fix1-receipt.json). Siete fallos reproducidos antes de código (limpieza, job ajeno, copia parcial y math); primer GREEN7, ampliado12passed/exit0/sinavisos root. Labels de sesión/imagen e ID preciso, stop/rm independientes de logs, cleanup diferido ante job ajeno, publicación atómica de referencia sin overwrite, import math. FFprobe real sobre senoide existente, ningún audio original/generado nuevo. Prepare-only0/AST3.11 conforme. Ventana00:22:14–00:26:14 UTC, estimado/null; fuentes/recibos anteriores conservados, gates CPU de producto no reabiertos. Segunda revisión fresca y QA del arnés pendientes. Lectura real posterior: Ollama vacío,2676MiB usados/9268libres de12227; sigue faltando baseline≤1600 o respuesta a excepción específica ya solicitada, sin nueva pregunta ni carga.

## Revisión de dos lentes — intento 2: T-16 — arnés privado conforme CPU

[Veredictos completos](testing/t16/harness-review-2.md). A+B frescas y secuenciales por límite de threads, traspaso completo del intento1; sin rebates ni reapertura de aprobados. C/Dfalse sobre Git; privados leídos expresamente. Scope0 previo, sin hallazgos adicionales de seguridad/rendimiento.

| ID | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| H1 | Important | Timeouts de arranque/logs/stop | T-16 | corregido y revalidado | Finally y cleanup por etiqueta/imagen/ID; tres escenarios CPU |
| H2 | Important | Referencia parcial irrecuperable | T-16 | corregido y revalidado | Publicación atómica sin sustitución, retry/preservación |
| H3 | Important | math ausente al validar MP3 | T-16 | corregido y revalidado | Import, doble y FFprobe real sobre senoide existente |
| H4 | Important | Contenedor con job ajeno detenido | T-16 | corregido y revalidado | Deferred sin stop/rm en dos escenarios, sin nueva configuración |

Fusión: cero gaps pendientes. A12passed/sinavisos y B12passed/unavisoWinError5cache, exit0; hashes actuales/históricos conformes, AST3.11/diff-check0. Se pasa a QA CPU dirigida del arnés; no repetir suite de producto sin cambios. CA3/4 siguen abiertas, sin modelos/audio original ni paquete musical real. Consumo estimado/null; marcador de revisión se cierra antes de abrir QA. Journals ajenos intactos, sin promociones; Jira/Confluence desactivados.

**QA del arnés — 2026-10-06:** [informe independiente](testing/t16/harness-qa-report.md), [recibo](testing/t16/harness-qa-receipt.json):12passed/ceroavisos/exit0; cuatro fuentes actuales, dos snapshots y supervisión T-15 coinciden; seis fuentes de producto sin cambios. AST3.11/prepare-only0 y ledger0incoherencias/7avisosChangelog. Coverage-check applies=false por marcador sinUI; cobertura de código efímero n/a, no se sustituye por porcentaje de producto. Qa-gateE2E n/a sin UI por diseño; ninguna salida inventada, fullpack real/sintético no ejecutado, PDF pendiente. Cuatro documentos/cuatro enlaces y privacidad en alcance acotado comprobados. VentanaQA00:29:44–00:33:03 UTC, fuente estimado; tokens/coste/horas IA reales null. Ni GPU ni modelos ni audio original; CA3/4 y T-16 siguen en-progreso, M0 abierto13/20. Entrega documental en rama T-16, sin merge a main. No repetir pruebas/builds de producto por estas correcciones privadas.

**Intento GPU y fix2 — 2026-10-06:** baseline conforme (1.391 MiB preflight, 1.361 MiB grupo; Ollama vacío), sin excepción ni nuevo umbral. Sesión `01M47AYMT21MACX62R4VXTXBP7` detenida tras 2,047 s: `monitor_failed`/ValueError antes de job aceptado, cero tomas; contenedor propio retirado stop/rm exit0, sin declarar unload confirmado. [Diagnóstico y fix CPU](testing/t16/harness-fix2-report.md), [recibo de fuentes](testing/t16/harness-fix2-receipt.json). RED: `test_harness_fix2.py::test_real_preflight_loading_without_cap_does_not_abort` falló con `ValueError: INVALID_GPU_MONITOR_DATA` durante preflight HTTP real con NVML sintético válido · 2026-10-06. GREEN dirigido1 y suite privada20passed/ceroavisos; wrapper distingue preflight sin job/modelo/cap de carga real, sin omitir fallos tras aceptación ni umbral95 %. Primer fixture total0 corregido y RED repetido antes de reescribir; no cuenta como TDD. Fuentes históricas y producto intactos; no se repiten generaciones ni gates de producto. Revisión/QA frescas del fix2 pendientes; CA3/4 siguen abiertas. Ventanas GPU00:48:52–00:51:28 y fix00:51:28–cierre medidor; estimado/null, no sumar horas de reloj como IA ni atribuir consumo solapado con T-08. No tocar/promover journals ajenos.

## Revisión de dos lentes — intento 1: T-16 — fix2, null explícito pendiente

Lentes A+B+C+D con degradación declarada por límite de threads: A reutiliza QA T-19, B revisión T-17; C/D comparten contexto con B. Independientes de la implementación, sin afirmar cuatro contextos frescos. [Informe](testing/t16/harness-fix2-review-1.md). A/B: 20 tests cada una, exit0 con un aviso distinto declarado; C/D lectura. No GPU ni generaciones. H1–H4 anteriores conservados.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-F2-01 | Important | Ausencia/falsy confundidos con null | T-16 | fix3, pendiente de revalidación | run-comparison.py:55; seis reproducciones rojas |

**Fix3:** RED `test_harness_fix3.py::test_preflight_requires_explicit_null_job_and_model` → 6 failed `DID NOT RAISE ValueError`, antes de cambiar runner, 2026-10-06. GREEN fix1+fix2+fix3 → 26 passed/sin avisos/exit0. [Informe y fuentes](testing/t16/harness-fix3-report.md). Se exige presencia y None explícito, manteniendo preflight válido y guardas de carga. Intento 2 de revisión y QA pendientes; tarea en-progreso, CA3/4 abiertas. Snapshot y recibos anteriores preservados, sin nuevas tomas ni afirmación artística. Consumo estimado/null; lote concurrente con T-08 sin atribución duplicada de horas.

## Revisión de dos lentes — intento 2: T-16 — fix3 conforme CPU

Lentes A+B+C+D con la misma degradación de contexto del intento 1, declarada en [informe](testing/t16/harness-fix3-review-2.md). A ejecuta26passed/ceroavisos/exit0; B/C/D lectura de diff/AST/nueveSHA/recibo, sin repetir suite. Ninguno implementó fix3. Fusión sin gaps nuevos; CA1/2 y H1–H4 conservados, CA3/4 pendientes. Jira/Confluence desactivados; journals ajenos intactos, sin promoción.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-F2-01 | Important | Null no explícito | T-16 | corregido y revalidado | Presencia+is None; seis regresiones y preflight HTTP válido |

QA CPU independiente de la implementación pendiente; no ejecutar retry GPU hasta QA y baseline nuevo. No afirmar revisión fresca ni consumo IA real; ventanas concurrentes estimadas/null.

**QA fix3 conforme CPU — 2026-10-06:** [informe](testing/t16/harness-fix3-qa-report.md) y [recibo](testing/t16/harness-fix3-qa-receipt.json), contexto A/T-19 reutilizado y declarado, independiente de implementar. 26passed/ceroavisos/exit0; nueve SHA, seis fuentes de producto, AST3.11 y prepare-only ready_cpu conformes. Ledger0incoherencias/7avisos; coverage-check applies=false y qa-gate n/a sin UI, sin resultados ficticios. Seis documentos/nueve enlaces y privacidad acotada conformes. Recibo fix3 anterior a revisión preservado con flags históricos, revisión posterior enlazada. PDF pendiente. CPU permite un retry cuando el baseline nuevo cumpla≤1600MiB y Ollama vacío; lectura posterior2750MiB lo impide por ahora. No repetir suite430/builds ni pedir de nuevo la excepción pendiente; CA3/4 abiertas, cero nuevas tomas/calidadfalse, M0 abierto13/20.
