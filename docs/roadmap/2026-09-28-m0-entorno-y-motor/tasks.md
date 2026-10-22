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
| Fase 4 — Medición y elección | 5 | 13 | 38% | 0 / 37h | 0 / 15h | 0 / 3.8h | 0 / — |
| **TOTAL** | **13** | **21** | **62%** | **— / 88h** | **— / 39.5h** | **— / 10h** | **— / —** |

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
- **Estado**: en-revision
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real —
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-03, T-02, T-19 (entrada efectiva y recibos antes de evaluar fidelidad)
- **Tipo**: backend
- **Archivos**: `apps/engines/analysis/` (Dockerfile, proyecto/lock uv independientes, adapters, recursos y tests), `docker-compose.yml`; orquestador: `docs/decisiones/ADR-0030-analisis-local-y-alineacion-secuencial.md`, `docs/decisiones/ADR-0031-transcripcion-segmentada-con-tiempos-globales.md`, `docs/decisiones/README.md`, `docs/legal/licencias.md`, `docs/arquitectura/contrato-engines.md`, `CONTINUE-HERE.md` y `testing/t08/` de esta iniciativa
- **Changelog**: Motor local de análisis con transcripción y alineación secuenciales, similitud CLAP, estética y beats CPU; pesos verificados, caché segura y descarga del proceso hijo.
- **Verificación**:
  - `docker compose --profile engines build engine-analysis` → OK
  - `docker compose run --rm engine-analysis uv run pytest -m gpu -q` → verde: `audio.transcribe` sobre un audio de prueba devuelve texto y tiempos; `audio.clap` y `audio.aesthetics` devuelven puntuaciones; `audio.beats` devuelve BPM ±2 sobre un clic de 120 BPM

**Criterios de aceptación**
- [x] Base `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime`, dependencias fijadas, puerto `127.0.0.1:8130`, y los mismos montajes y token que engine-acestep (contrato §6). `audio.beats` se declara con `device: cpu` (beat_this en CPU).
- [x] Tareas `audio.transcribe` (Qwen3-ASR-1.7B), `audio.clap` (LAION, pesos convertidos), `audio.aesthetics` (Audiobox, `model.safetensors`) y `audio.beats` (beat_this, pesos convertidos). `audio.align_lyrics` (ForcedAligner) queda preparada pero no se verifica hasta M3.
- [x] Un modelo cada vez en el proceso hijo; se cambia de modelo dentro del engine descargando el anterior.

**Contexto de implementación (TDD, subagente fresco):** rama `m0/t-08-analysis` basada en `991dd33` de T-16; integración en main pendiente de integrar primero T-16, sin introducir su entrega parcial por esta tarea. El subagente solo escribe `apps/engines/analysis/` y añade el servicio a `docker-compose.yml`; el orquestador conserva docs, ledger y Git. No tocar fuentes comunes, ACE-Step, root pyproject/uv.lock ni journals ajenos. Leer contrato-engines, datos, convenciones y [ADR-0030](../../decisiones/ADR-0030-analisis-local-y-alineacion-secuencial.md). Interfaces de referencia: `apps/engines/common/engine_common/{server,worker}.py`, `packages/engine-contract/engine_contract/__init__.py`, `apps/engines/acestep/{engine_acestep.py,descriptor.py}`. Prerrequisitos y fuentes fijadas disponibles en `.cache/dev-cycle/t08/prerequisitos-2026-10-06.md` y `.cache/dev-cycle/t08/research/` (sources.json, beat-checkpoint-metadata.json y código consultado). ASR y alineador secuenciales con liberación intermedia; beats CPU sin contexto CUDA; pesos estrictos/offline contra models.lock.json y sin loaders pickle ni descargas runtime. Dependencias nuevas deben tener registro de licencia previo (coordinar con orquestador). Resolver lock propio permite CPU; no sync/instalación de torch en host/root venv. Build Docker CPU autorizado; no modelos GPU, inferencia musical ni descargas de pesos. Preparar tests GPU reales marcados, sin contarlos como ejecutados. Evidencias RED/GREEN dirigidas, sin suite completa/QA inventada. Todos los tasks `verified: false` hasta medición propia; align_lyrics independiente queda para M3.

**Fidelidad al evaluar:** contrastar letra efectiva sin tags con transcripción y tiempos, conservando el suelo WER. Los resultados de análisis alimentan [evaluacion-escucha §3.1](../../calidad/evaluacion-escucha.md#31-fidelidad-de-instrucciones-y-naturalidad) y la [rúbrica T-18](testing/t18/preparation-report.md#rúbrica-para-la-evaluación-musical-posterior); no atribuyen naturalidad ni obediencia por sí solos. Los recibos planned/captured siguen siendo evidencia de transporte, no de calidad.

**Entrega CPU T-08 — 2026-10-06:** [informe de implementación](testing/t08/cpu-delivery-report.md) y [recibo de fuentes](testing/t08/cpu-delivery-receipt.json). Build final exit0, imagen37e9355; Python3.12.3/Torch2.14cu130/audio2.11/vision0.29 e imports reales sin CUDA. 31passed/4deselected/1aviso Starlette; cobertura oficial307/341=90,03 %, mínimo por fichero87,50 %. Clic real en CPU:120 BPM/61beats,1passed/3deselected y unload comprobado. Ruff/formato13Python/lock propio conformes. RED previos: descriptores, salida cruda y residencia fallaron con AssertionError de implementación ausente; recursos alterados, beats sinCUDA, dependencia alineador, preflight y BF16 Audiobox tienen RED detallado en informe, todos verdes. ImportError/UnboundLocalError de fixtures no contados como TDD. Config apt/asserts/prosa TDD n/a. Medidor cerrado00:45:21–01:11:06UTC, estimado/null y solape T-16 no sumado como consumo IA. Revisión/QA y tres inferencias GPU pendientes; todos los criterios siguen abiertos hasta validación. Fixture30s privada preparada CPU, original intacto; no se declara calidad ni capacidad verificada.

**Revisión parcial T-08:** [evidencia A/C](testing/t08/review-in-progress.md), cero gaps detectados en esas lentes y límites CPU explícitos. A/C comparten contexto reutilizado por límite de threads, independientes de implementar; B sigue vivo en `/root/review_t17_b`, sin fusión global ni QA todavía. Selector C=true por Docker/eval de modelos, D=false. Medidor de calidad en lote abierto desde01:13:24UTC incluye QA T-16 y revisión T-08 sin duplicar ventanas. Observar el handle vivo antes de reiniciar. T-16 publicó sus evidencias CPU en8663287, main intacto; rama T-08 avanzó a ese commit conservando sus dieciocho fuentes y documentos locales. No mezclar integración parcial con cierre de T-16.

**Diagnóstico CPU CLAP — 2026-10-06:** [reproducción real](testing/t08/clap-preprocessing-diagnosis.md) confirma `NotImplementedError: data_truncating False not implemented` con kwargs actuales y audio de30s. Extractor de audio fusion/repeatpad separado de tokenizer truncation=False pasa, conserva texto y devuelve tensores esperados. CUDA no inicializada, recursos por SHA verificados, sin red/pesos/modelo; producto intacto. Hallazgo enviado a B, cuya revisión completa sigue pendiente. Esta investigación es evidencia de un defecto, no RED de una corrección implementada ni QA. Corregir tras su retorno con regresión de la ruta real antes de código; conservar recibos originales.

**Fix1 CPU — 2026-10-06:** [entrega nueva](testing/t08/fix1-report.md) y [19 fuentes congeladas](testing/t08/fix1-delivery-receipt.json). R-CLAP-01/02 corregidos tras RED reales dentro del engine:2failed/2avisos3,63s; GREEN real largo/corto/exceso texto3passed4,00s. Modelo embeddings doble, procesador/tokenizer reales, sin pesos/GPU. Nuevaimagen80eee31, histórica37e9355 conservada; Compose apuntafix1 y config/resoluciónlocalhost8130 exit0, TDD n/a tag. CPU33passed4deselected1avisoStarlette7,12s; coverage309/34390,09 %, mínimo87,50 %; ruff14Python/lock111 conformes; host1skip explícito sinTorch. Medidorfix1 cerrado01:47:49UTC estimado/null, reloj7m noIA. Revisión2 abierta mismahora en lote propio: A/B frescas admitidas (`review_t08_fix1_a`, `review_t08_fix1_b`); C fresca y reactivación de contexto anterior rechazadas por threadlimit, se despachará secuencialmente al liberar cupo. A señaló provisionalmente comandos README54/64 con tag histórico; pendiente salida final y fusión, no corregir el snapshot mientras revisan. T-08 en-progreso y tres criterios abiertos; no QA/GPU ni ganador.

**Entrega fix2 T-08 — 2026-10-06:** [informe CPU](testing/t08/fix2-report.md) y [freeze20fuentes](testing/t08/fix2-delivery-receipt.json), todas las fuentes/evidencias SHA corroboradas por root. Cinco RED reales: segmentación450s, idioma/audio INVALID_PARAMS, límite independiente180s y error de sistema no oculto; GREEN dirigidos y suite final45passed/4deselected/1aviso15,24s. Cobertura346/382=90,58 %, mínimo88,89 %. Imagen final306e3b0,17fuentes copiadas con SHA coincidente; build/Ruff15/formato/lockhost111 exit0. Lock aisladoDocker exit2 por workspace incompleto, primeras suites con fallos de fixtures/imports conservadas y no contadas como RED. Padre sinTorch/CUDA; no GPU ni QA. [ADR-0031](../../decisiones/ADR-0031-transcripcion-segmentada-con-tiempos-globales.md): fragmentos propios≤180s, hasta600s, tiempos globales y residencia única; ruta independiente180s provisional hastaM3, sin recortar su requisito futuro. Revisión3 siguiente, todos los CA permanecen abiertos. Medidor fix2 cerrado01:55:26–02:07:08UTC:12m de reloj, fuente estimado/tokens/coste/horasIA null, aviso de transcripción no disponible; incluye supervisión/diagnóstico paraleloT16 y no atribuye consumo individual. Alcance exit0 sin fuera/avisos, selector C=true/D=false; journals ajenos excluidos por default y preservados.

**QA CPU y ejecución GPU1 T-08 — 2026-10-06:** [CPU independiente](testing/t08/qa-cpu-report.md)/[recibo](testing/t08/qa-cpu-receipt.json)45passed4deselected1aviso15,43s/cobertura90,58%mín88,89, beatsreal120BPM61beats/unload, contratos/examples4/AST8/ruff15/formato/ledger0incoherencias7avisos conformes; coverage-checksinUIappliesfalse, qa-gaten/a sinreporterfabricado/PDFpendientetools. [GPU real rojo](testing/t08/gpu1-failure-report.md)/[recibo](testing/t08/gpu1-failure-receipt.json): exec80352terminalexit1,2failed2passed1aviso132,62s. ASR/CLAPfallan terminalerror, AudioboxGPU/beatsCPUpasan. Imagen306e3b0, fixture30s intacta sinletraesperada, baseline1315/Ollamavacío, contenedor--rmretirado y GPUvuelve1315. Muestra5218noespico, spill/causa/precisiónnoacreditados. T08vuelveen-progreso y todos losCAabiertos; revisión3/CPUconformes se conservan como antecedentes, no validaciónGPU. Diagnóstico fresco diagnose_t08_gpu1 sóloCPU/caché propia, producto congelado hasta hipótesisprobada.

**Integración T08 — diagnóstico CLAP probado CPU (2026-10-06):** [Informe](testing/t08/gpu1-diagnosis-report.md)/[recibo](testing/t08/gpu1-diagnosis-receipt.json):20fuentes/76artefactos SHA íntegros. Fusión4canales incompatible con proyección1canal; backend/extractor/tokenizer/prefijo reales fallan1s/30s, rand_trunc nativo supera ambos. Sin pesos/GPU/scoringcompleto. Fix mínimo con regresión real antes de código; ASR causa pendiente, instrumentación propuesta sóloCPU. Nueva fase tras integraciónGPU, review3/QA anteriores no reiniciadas ni borradas. CA abiertos. TDD n/a: informe de diagnóstico.

**Entrega integración CLAP T08 — 2026-10-06:** [informe](testing/t08/integration-clap-report.md)/[recibo](testing/t08/integration-clap-receipt.json). Root verifica21fuentes/14artefactosSHA,18fuentesimagen coincidentes según evidencia congelada; dockerimageinspect confirmaId7d0733f. RED: test_clap_checkpoint_real_projection_preserves_text_and_window1s/30s falla RuntimeError Conv2d espera1canal recibe4,2failed13,75s antes de código. Cambio mínimo estrategia extractor; GREEN8passed13,43s; imagenfinal47passed4deselected1aviso27,16s,cobertura346/38290,58%,backend185/20888,94%, Ruff16/formato/Compose conformes. Texto íntegro/presupuesto y ventana10s/rand_trunc documentados, sin escorecompleto niGPU. TDD n/a: tags y prosa. Imagenhistórica306e3b0 intacta; bugASR pendiente. Reviewintegración1 nueva fase posteriorGPUrojo, conservar review3 y todaslasconformidades previas; no ocultar ni reiniciarviejobucle. TodosCA/T08/M0 abiertos.

**CLAP integración verificada — 2026-10-06:** [QA CPU independiente](testing/t08/integration-qa-report.md)47passed/4GPUdeselected/1aviso27,52s,cobertura90,58global88,94backend,21fuentes14históricos19evidenciasQA18imagenSHA conformes; qa-gaten/aSinUI/PDFpendientetools. [ScoreGPUreal](testing/t08/clap-gpu-report.md)/[recibo](testing/t08/clap-gpu-receipt.json):27104terminalexit0,1passed1aviso36,65s, scorefinito[-1,1]/textoíntegro/procesohijodistinto/unload probado, sin dobles. Imagen7d0733f, fixture30s íntegra; baseline/post1314/Ollamavacío, contenedorpropio--rmretirado/8101antiguopreservado. Sin picoVRAM/spill/precisiónmusical medidos, no audio nuevo ni calidadaprobada. CLAPconforme; ASRpendiente y todosCA completos/T08/M0 abiertos.

**Fusión final ASR — 2026-10-06:** [revisión1](testing/t08/asr-diagnostic-review-1.md) con A+B+D frescas, cero gaps; dos SHA intactos. D revisa ambos scripts completos, AST/proxy CPU exit0 sin escrituras; O(bytes+eventos+trazas), doce emisiones/dos fases. Cfalse/Dtrue. Rechazo inicial por cupo preservado en parcial, no se presenta como revisión. QA independiente y prueba GPU diagnóstica pendientes; no causaASR ni precisión/cancelación real acreditadas.

**QA independiente ASR privada — 2026-10-06:** [informe](testing/t08/asr-diagnostic-qa-report.md)/[recibo](testing/t08/asr-diagnostic-qa-receipt.json). Fresh QA40checks CPU conformes; runner real doneexit0/errorinyectadoexit2, PID/PPID real y padre sinTorch, unload y TMPfallidoborrado; negativos SHA/path rechazanexit1 antestraza. Root verifica2fuentes/56artefactosSHA. Sin GPU/pesos/UI/coverage; qa-gate n/a. Incidencia PYTHONPATH de fixture corregida y preservada, sin producto. Preflight nuevo y una sola prueba GPUASR diagnóstica siguientes; causa/precisiónASR y T08/M0 pendientes.

**ASR causa probada — 2026-10-06:** [informe](testing/t08/asr-cache-diagnosis-report.md)/[recibo](testing/t08/asr-cache-diagnosis-receipt.json). Exec61484TERMINAL: runnerexit2/host1/103,5s, Qwen carga y falla durante inferencia por PermissionError13 `/studio/.triton`; no alineador ni precisión. PadrePID1 sinTorch/hijo11, unload y TMPfallidoborrado, --rmcontenedor ausente y post1314MiB/Ollamavacío. CPU mismaimagenUID10001 reproduce FileCacheManager noescribible; contrafactual TRITON_CACHE_DIR dentro/studio/.cache escribe/lee, sin GPU/modelos. Fuentes2SHA intactas y trazas privadas congeladas; sin pico/spill/OOM afirmado. Nuevo fixTDD de caché de imagen con implementer fresco, luego revisión/QA/retryASR; T08/M0 siguen abiertos.

**Entrega CPU caché ASR — 2026-10-06:** [informe](testing/t08/asr-cache-fix-report.md)/[recibo](testing/t08/asr-cache-fix-receipt.json). Root verifica22fuentes/39artefactos/19imagenSHA e Idd20ae562; históricos7d0733f/306e3b0 intactos. REDreal FileCacheManager default UID10001 PermissionError13/1failed0,39s previoDocker; GREEN1passed0,37 y vecinos14passed0,61s. ENVTRITON_CACHE_DIR=/studio/.cache/triton/permisos0755/engine, sinrootruntime ni cambiosbackend/modelos/locks. Baselines de los tres archivos reconstruidos y SHA idénticos al reciboCLAP anterior; nuevo test completo. Scope0/selector privado, review integracióncaché1 nueva fase luego causaGPUroja, no reiniciar revisionesprevias. Cobertura config n/a sinPythonproducción nueva; revisión/QA/retryASR pendientes y todosCA/T08/M0 abiertos.


**Aceptación técnica y QA final — 2026-10-06:** [cotejo QA independiente](testing/t08/conformance-qa-report.md) y [recibo](testing/t08/conformance-qa-receipt.json). Sin gaps técnicos; verifica22fuentes39previos3baselines41QAartefactos19imagenSHA/JUnitGPU4/crudos4/CPU48 y freezeantes-después conforme. Los tres CA técnicos quedan checked con Verificación real. T-08 pasa a en-revision: cierre Git/integración espera resolver el stack T-16, sin introducir su entrega parcial en main. No nuevos GPU/suites/build. Precisión/idioma ASR, picos/spill, capacidades y calidad siguen en sus tareas futuras; M0 continúa13/20.

### T-09 — Benchmark en la 5070

- **Descripción**: Números reales para decidir la configuración por defecto y el modo de alta calidad.
- **Estado**: en-progreso
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-07, T-19 (entradas musicales verificadas)
- **Tipo**: investigación
- **Archivos**: `scripts/eval/benchmark.py`, módulos/observadores/pruebas en `scripts/eval/`, `eval/results/benchmark-5070.md`; soporte aditivo de perfiles/INT8/relojes en `apps/engines/acestep/` y `apps/engines/common/engine_common/server.py` con pruebas vecinas; orquestador: `testing/t09/`, `docs/decisiones/ADR-0033-perfiles-y-medicion-directa-del-benchmark.md` ([ADR-0033](../../decisiones/ADR-0033-perfiles-y-medicion-directa-del-benchmark.md)), `docs/decisiones/ADR-0036-observabilidad-wddm-autonoma.md`, `docs/decisiones/README.md`, `docs/arquitectura/modelos.md`, documentos afectados y licencia torchao. Sin modificar `/v1` ni pesos/locks por suposición.; soporte E/S: `docs/decisiones/ADR-0072-copia-de-pesos-con-presupuesto-de-io.md` y `scripts/eval/tests/test_benchmark_storage_pacing.py`
- **Verificación**:
  - `uv run scripts/eval/benchmark.py --matrix default` → escribe `eval/results/benchmark-5070.md`
  - lectura: la tabla tiene VRAM pico, carga, inferencia, RTF y `spilled` para cada configuración y duración

**Criterios de aceptación**
- [ ] Matriz de configuraciones: turbo + LM 0.6B (inicial), turbo + LM 1.7B, sft, base y XL-turbo con offload + INT8 si cabe. Duraciones: 30, 60, 180 y 300 s.
- [ ] Carga desde el bind mount frente a una copia dentro del contenedor (I-02). Si la diferencia supera 30 s, se abre un ADR.
- [ ] **Antes de medir**, el modelo de Ollama queda descargado de la VRAM (`ollama stop <modelo>`; sin parar el servicio ni borrar el modelo), y `nvidia-smi` muestra ≤ ~1,6 GB usados (E-16, [ADR-0022](../../decisiones/ADR-0022-memoria-tecnica-kwipu-graphiti.md)). Se anota la VRAM en reposo en el informe.
- [ ] Medido con el navegador abierto (la UI también consume VRAM). Se registra si hubo desbordamiento (Administrador de tareas y caída de RTF por encima de 1,5×).
  - Mecanismo vigente de observación: contraste manual `task_manager_v1` o acreditación automática `wddm_auto_v3` conforme a [ADR-0042](../../decisiones/ADR-0042-proveedor-wddm-aislado-y-preparacion-observada.md), con los límites de [ADR-0039](../../decisiones/ADR-0039-readquisicion-wddm-acotada.md) y recuperación/transporte de [ADR-0045](../../decisiones/ADR-0045-recuperacion-y-transporte-de-auditoria-del-benchmark.md). V1/v2 conservan interpretación histórica de [ADR-0036](../../decisiones/ADR-0036-observabilidad-wddm-autonoma.md); no acreditan v3. Implementación y QA actuales pendientes. El modo automático preserva memoria compartida Windows, declara su confianza limitada y no la calibra con NVML. No sustituye la matriz real ni el navegador visible.
- [ ] Opcional: `torch.compile` activado como experimento, anotando si falla en sm_120.
- [ ] Recomendación argumentada con números para la configuración por defecto y la de alta calidad.

**Preparación de T-09 — 2026-10-06:** [investigación de interfaces e inventario](testing/t09/preparation-report.md). Sin benchmark/GPU/modelos: Turbo, SFT, base, ambos LM y componentes compartidos presentes por metadata/sellos vigentes; XL ausente. `run_s` incluye carga, CLI fija BF16 y no selecciona modo/checkpoint/LM; definir relojes antes de RTF. Identidad/defaults de base/XL, INT8, bind/copia y observación sharedGPU requieren resolución explícita antes de medir; no suponer que disponibilidad de pesos acredita soporte. Contexto reutilizado, sin nueva QA ni ventana individual. T-09 sigue borrador, todos los criterios abiertos; esta nota no cambia la matriz ni el alcance aprobado de rendimiento.


**Arranque de implementación T-09 — 2026-10-06:** [diseño elegido O1](testing/t09/benchmark-design.md)/[recibo](testing/t09/benchmark-design-receipt.json), root36fuentes locales y7oficiales fijadas cotejadas; deriva documental autorizada si la hubo en publicación. [ADR-0033](../../decisiones/ADR-0033-perfiles-y-medicion-directa-del-benchmark.md) aceptada bajo autorización del propietario; soporte aún no implementado, cero números de benchmark. Matriz veinteceldas/dosbrazos/cold+3warm, nominal160jobs; no reducir duraciones ni matriz. Perfilbase32CFG7/XL8 con identidad propia, INT8 aplicado/rechazo de downgrade, relojes directos extra opcionales, copia efímera .cache guest, WDDM DXGI exacto y observación verificable TaskManager. FreezeT16 liberado trasQA113. Siguiente implementer fresco con TDD; rootdocs/ledger/GPU/Git, sin knowledge/memoria. CPU primero, ninguna ejecución GPU antes revisión/QA y preflight.

**Matriz parcial y diagnóstico — 2026-10-07:** sesión01M4A20D9G46C2DSV5DYS8E8VM terminó con18done/1cancelled por observability_lost_auto_dedicated_disagreement, hijoexit2; unload/contenedorretirado propios conformes, VRAM1233MiB. Replay contra el validador vigente: anterior9670/9683,68PASS; original9304/9009,68rechazado; siguiente8996/9009,68PASS133,42ms después. No error de reloj/escala/LUID demostrado; mecanismo interno driver desconocido. Arquitecto fresco comparó3opciones y raíz eligióO2 bajo delegación: [ADR-0039](../../decisiones/ADR-0039-readquisicion-wddm-acotada.md)/[diseño](testing/t09/bounded-reacquisition-design.md), un reintento completo2s, originales retenidos y umbrales intactos. Fix/TDD/revisión/QA/acreditación nueva pendientes. No modificar sesión anterior ni combinar sus18tomas con fuentes nuevas como matriz completa.


**Readquisición CPU — 2026-10-07:** [entrega con reservas](testing/t09/transition-fix1-report.md),300casos/1312of1452=90,36%, ceroexclusiones. RED: test_benchmark_reacquisition falló al recuperar discrepancia aislada; red-budget por persistencia fuera del presupuesto; red-policy-guard por v2 sin contexto; red-lifecycle por fase anterior al proof. Argv/UTC/exits originales cotejados,473protegidos/7server intactos. ReservasC1consulta síncrona no interrumpida a2s yC2preparación3s aborta: revisión/QA pendientes, ninguna GPU nueva ni criterios cerrados.

**Coordinador v3 candidata CPU — 2026-10-07:** [Informe](testing/t09/coordinator-cpu-delivery-report.md),416pass/5deselect históricos; siete módulos completos1826/2103=86,83%sinexclusiones,11hijosnativos medidos. CLIoriginaltimeout1/limpiezahistóricanoacreditada; nuevaspruebas/observación0procesos no la sustituyen. Rootcustodiafuentes/originales; transiciónreview2/QA pendientes, noGPU/160/cierreR09/T09/M0.

### T-10 — Matriz de capacidades verificadas

- **Descripción**: Qué operaciones funcionan de verdad en ACE-Step, con qué checkpoint y con qué evidencia.
- **Estado**: en-progreso
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 2.5h · real —
- **Supervisión**: est. 0.6h (≈25 % IA) · real —
- **Dependencias**: T-07, T-19 (entradas musicales verificadas)
- **Tipo**: investigación
- **Archivos**: `eval/results/capacidades-acestep.md`, `eval/capabilities/` (git-ignored), `apps/engines/acestep/descriptor.py`; harness/pruebas nuevos `scripts/eval/capabilities*.py` y `scripts/eval/tests/`, tests vecinos del descriptor; root: `testing/t10/`, `docs/decisiones/ADR-0034-capacidades-nativas-y-accesibles-por-v1.md`, índice y modelos, docs/legal/licencias.md y entradas privadas data/inputs/t10-capabilities/. Laboratorio privado derivado de infraestructura congelada; sin ampliar tareas de producción por esta decisión.
- **Verificación**:
  - lectura: `eval/results/capacidades-acestep.md` tiene una fila por tarea con el checkpoint, el comando exacto, la ruta del audio de evidencia y el veredicto
  - `uv run pytest apps/engines/acestep -k descriptor -q` → `verified` coincide con la matriz

**Criterios de aceptación**
- [ ] Tareas evaluadas: **`music.song`**, `music.instrumental`, `music.retake`, `music.extend`, `music.repaint`, `music.cover`, `music.complete` y `audio.stems` (extract). Features de `music.song`: `negative_prompt`, `bpm`, `key`, `timbre_ref` y `lora`. Veredicto de cada una: funciona · degradada · no funciona.
- [ ] En `repaint`: ¿el audio fuera de la región queda bit a bit intacto, o hace falta un empalme? Queda documentado.
- [ ] El descriptor pone `verified: true` solo en las tareas y features que funcionan. Como mínimo, `music.song` y `music.instrumental` deben quedar verificadas: si no, M1 no puede aceptarse para uso musical real. La apertura técnica contra mock sigue [ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md); T-13 y este criterio permanecen abiertos.

**Inicio de implementación — 2026-10-06:** O1/ADR-0034 aprobados. Freeze T-09 de 33 fuentes cotejado SHA/tamaño antes del despacho. Ownership exclusivo de archivos nuevos `scripts/eval/capabilities*.py`, pruebas nuevas `scripts/eval/tests/test_capabilities*.py` y laboratorio privado `eval/capabilities/`; el implementer no modifica fuentes existentes, descriptor, contratos, locks ni Git. Harness completo de ocho operaciones y cinco features, dos superficies; fase CPU con TDD, sin inferencia ni capacidades verificadas. Recursos musicales/LoRA/evaluador tonal siguen siendo prerrequisitos explícitos; no se sustituyen por mocks. Root conserva ledger y publicación; `docs/knowledge/` excluido por alcance del propietario.

### T-11 — Batería de evaluación automatizada (F-84)

- **Descripción**: Generar y medir los 10 briefs de forma reproducible y anónima.
- **Estado**: en-progreso
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-07, T-08, T-19 (entradas musicales verificadas)
- **Tipo**: investigación
- **Archivos**: `scripts/eval/run.py`, `scripts/eval/metrics.py`, helpers nuevos `scripts/eval/evaluation_*.py`, tests nuevos `scripts/eval/tests/test_evaluation_*.py`, `eval/briefs/B-01…B-10.txt`, `eval/briefs/briefs.yaml`, `eval/results/sheet-<candidato>.md`
- **Verificación**:
  - `uv run scripts/eval/run.py --candidate ace-step-1.5-turbo --dry-run` → lista 30 tomas planificadas
  - `uv run scripts/eval/run.py --candidate ace-step-1.5-turbo` → 30 tomas en `eval/takes/`, mapa en `eval/takes/.map.json` y hoja de puntuación con WER/CLAP/Audiobox

**Criterios de aceptación**
- [ ] Los 10 briefs de evaluacion-escucha.md §4, con letras **propias**. Cada brief tiene un único prompt de estilo, literal para todos los candidatos.
- [ ] 3 tomas por brief con semillas fijas, loudness igualado a −16 LUFS mediante ganancia lineal y códigos aleatorios. El mapa se guarda aparte.
- [ ] Antes se mide el **suelo del WER** del transcriptor sobre 2–3 grabaciones cantadas reales, y se anota.
- [ ] Hoja de puntuación en Markdown lista para rellenar.
- [ ] Para medir con `engine-analysis`, las tomas se copian a `data/tmp/<job_id>/in/` (el engine solo ve `data/`).

**Unidad CPU independiente iniciada — 2026-10-07:** ADR-0037 permite construir el plan, orquestador, anonimización, ganancia lineal y métricas contra contratos/mock sin cerrar T-08. Implementer fresco sólo archivos nuevos; engines, preparación T-19, catálogo original y pesos permanecen protegidos. El catálogo real contiene sólo B-02 con declaración nula: letras restantes, declaraciones, suelo ASR real y ejecución de30tomas son prerrequisitos pendientes. Dry-run conserva30slots e informa bloqueos; ninguna autoría, GT, escucha ni calidad se inventa. La comparación mantiene prompt efectivo literal y rúbrica de naturalidad/cumplimiento. Brief determinista emitido con aviso previo de11398caracteres, conservado; suplemento estimado3 en lote raíz ya abierto, sin precios/tokens/horasIA reales supuestos. Revisión y QA de la unidad pendientes; no tarea completada.

**Unidad CPU entregada, pendiente revisión/QA — 2026-10-07:** [Informe](testing/t11/cpu-delivery-report.md),48pruebas y30vecinas distintas; módulos completos86,83%/90,76%sinexclusiones. Root4fuentes/copias,491protegidas y originales cerrados verificados. Dry-run30slots; comando completoexit2porprerrequisitos. NoGPU,30tomas reales,sueloWER,escucha ni cierreT11.

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
- **Estado**: en-revision
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: T-06, T-07, T-15, T-19 (entradas musicales verificadas)
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/adapter.py`, `apps/engines/acestep/tests/test_inference_controls.py`, `scripts/generate.py`, `tests/test_generate_inference.py`, `apps/engines/acestep/README.md`, `docs/arquitectura/pipeline-audio.md`, `docs/arquitectura/modelos.md`, `docs/decisiones/ADR-0027-controles-de-inferencia-sft.md`, `docs/decisiones/README.md`, `CONTINUE-HERE.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md`, `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t16/`, `data/inputs/libre/sft-ab/`, `data/eval/libre-sft/`, `.cache/dev-cycle/t16/` (últimas tres rutas privadas/efímeras)., `apps/engines/acestep/preflight.py`, `apps/engines/acestep/input_profile.py`, `packages/audio-post/audio_post/manifest.py` (perfil/recibos coherentes con pasos y defaults SFT/Turbo), `tests/test_generate_preparation.py` (regresión de procedencia y publicación de nuevos parámetros), `apps/engines/acestep/tests/test_preflight.py` (solo factory de captura: controles efectivos en doble DiT), `docs/decisiones/ADR-0032-condicionamiento-dit-segun-rama-nativa.md`, `apps/engines/acestep/tests/test_dit_resolution.py`, `packages/audio-post/tests/test_audio_post.py` (corrección de integración: ramas DiT, captura y validación de recibos, sin cambiar pesos/contratos)
- **Verificación**:
  - `uv run --no-sync --all-packages pytest tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py -q` → validación, defaults, identidad, propagación y progreso correctos; RED previo registrado.
  - QA sin UI: tests vecinos CPU, ruff/formato, contratos y cobertura ≥80 % de producción cambiada; imagen final con tests CPU del adaptador; revisión A+B y lentes condicionales conformes.
  - `uv run --frozen --no-sync --all-packages python .cache/dev-cycle/t16/native-resolution-comparison/run-comparison.py` → seis nuevas tomas de90s/semillas1,2,3 por configuración: SFT50pasos/CFG7 y Turbo8pasos/defaults anteriores, con LM0,6B/BF16/PT y shift1; entrada efectiva/metadata LM emparejadas y recibos actuales verificados. Los controles de T-15 permanecen intactos como referencia histórica separada.
  - `uv run --no-sync scripts/verify_manifest.py data/cli/` y carpeta de escucha → salidas/manifiestos/telemetría/unload/HTTP válidos; hashes de tomas anteriores conservados.

**Criterios de aceptación**
- [x] Descriptor distingue SFT (`ace-step-1.5-sft`) de Turbo; factoría/adapter usan identidad coherente. Turbo mantiene su identidad y defaults; no cambia /v1 ni se activa `verified`. Pasos opcionales enteros1–8 Turbo y1–200 SFT; CFG opcional finito1–20 solo SFT. Adaptador rechaza inválidos también sin HTTP y usa defaults SFT50/CFG7. CLI expone `--inference-steps` y `--guidance-scale`, también sobre briefs, con validación y manifiesto del pedido explícito. Progreso Euler/cancelación usan número efectivo de pasos.
- [x] TDD con RED por comportamiento, revisión fresca y QA CPU conformes, cobertura ≥80 % de los archivos de producción cambiados. Registro ADR/documentos en castellano; sin cambios de pesos, locks, dependencias ni motor por defecto.
- [x] Seis nuevas tomas emparejadas90s, SFT y Turbo por semillas1/2/3, caption de control T-15 y misma letra por hash, BPM94/es, shift1/LM0,6B/BF16/PT. SFT50pasos/CFG7 frente a Turbo8pasos/defaults anteriores; la prueba compara configuraciones completas, no solo el checkpoint. Caption/letra/metadata y controles LM efectivos iguales por par; perfiles/capturas actuales, hashes/identidad/pasos/CFG/telemetría/unload acreditados. Controles Turbo antiguos preservados como referencia histórica, no controles equivalentes del experimento nuevo. Ollama descargado y VRAM≤1600MiB; cap dinámico, parada conservadora y sin excepción de T-14.
- [ ] Pares privados ciegos y referencia Suno original conservada; ganancia lineal con nivel común, sin compresor, sin sobrescribir takes/manifiestos/valoraciones previos. Valorar ritmo/afinación/voz/instrumentos; no declarar ganador ni generar canción completa por suposición. M0 y T-08–T-13 siguen abiertos.

**RED contrato de empaquetado — 2026-10-06:** `.cache/dev-cycle/t16/native-packer-contract-fix1/test_contract.py::test_six_real_v2_receipts_complete_validation_contract` falló con `KeyError: request` en packer89 · 2026-10-06T04:35:21UTC, 1failed/exit1. [Diagnóstico/fix](testing/t16/native-packer-contract-fix-report.md)/[recibo portable](testing/t16/native-packer-contract-fix-receipt.json). Bloque íntegro con seis envelopes reales y validador real; dobles sólo audio/hashmanifest/medición, sin normalizar. Hipótesis inicial incompleta conservada (checkpointKeyError7failed2passed); checkpoint6/6 probado antes de corregirlo. GREEN9passed0,20s, ocho vecinos rechazan conflictos; tres accesos mínimos y controles/validador intactos. Root87rutas/artefactos/JUnit verificados. Revisión/QA pendientes antes nuevo fullpack. Temporal fuera de ownership creado/eliminado por implementer, ausencia verificada; no repetir. Memoria/gotcha omitida por ownership expresamente prohibido, diagnóstico en ledger/reporte.

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

**Retry2 GPU T-16 — 2026-10-06:** [fallo observado](testing/t16/retry2-failure-report.md) y [recibo](testing/t16/retry2-failure-receipt.json), sesión01M47EM0TM0XV6EFJHXX7ETSR7. Baseline normal1315MiB/Ollama vacío y15SHA del arnés/producto conformes a QA. Exec72134 terminal exit1; primer grupoSFT INTERNAL tras187,406s, cero audios publicados. Unload confirmado y logs/stop/remove del contenedor propio exit0; servicio8101 anterior preservado. Monitor93muestras sin stop, swap WSL pico1,359MiB; no se atribuye causa/OOM/spill ni calidad por esas medidas. GPU volvió1315MiB; Ollama vacío, sin modelo previo que restaurar. CA3/4 permanecen abiertas. Diagnóstico fresco `/root/diagnose_t16_retry2` CPU en caché propia, fases1–3 de debug-root-cause: error nativo descartado por adaptador y salida fallida eliminada por server, pérdida reproducida CPU; causa real aún no demostrada. Instrumentación temporal privada y prueba mínima30s propuestas, no ejecutadas; revisar antes de GPU, no repetir seis tomas sin hipótesis.

**Diagnóstico CPU retry2 T-16 — 2026-10-06:** [resumen sanitizado](testing/t16/retry2-diagnosis-cpu-report.md) y [recibo29SHA](testing/t16/retry2-diagnosis-cpu-receipt.json): pérdida de error/captura parcial reproducidaCPU; causa nativa real no probada. Propuesta inicial parent-only corregida antes de GPU; HTTP→supervisor→worker real en otroPID conserva trazas privadas fueraTMP, padre sinTorch, cómputo/preflight dobles explícitos. Propuesta1toma30s aún sin revisión ni ejecuciónGPU, no reproduce exactamente90s. Descriptores/preflight originales, imagen9e4fc86/producto/arnés congelado intactos. Root corroboró29SHA, sin publicar inputs/tracebacks. Fases1–3 parciales; fase4 no procede aún. Trabajo paralelo T08 sin consumo individual imputado.


**Diagnóstico nativo SFT30 — 2026-10-06:** [Informe](testing/t16/native30-diagnosis-report.md)/[recibo](testing/t16/native30-diagnosis-receipt.json), root verifica27archivosprevios/15fuentesimagen/27evidenciasSHA. DefectoCPU probado: plantext2music151tokens vs instruccióncoverresuelta150, letra256idéntica; control sincodes y contrafactualplanresuelto pasan guarda intacta. LM397/33/reserva160/SHA coinciden captura real. Error real INVALID_PARAMS en guardaadapter224, noOOMobservado; rama/IDs finalesGPU no capturados directamente. Corrección al resumen inicial: boundaries sí conservaLMargs/LMprompt/DiTargs; no estaba vacío. [ADR-0032](../../decisiones/ADR-0032-condicionamiento-dit-segun-rama-nativa.md) decide medir ambasramasposibles con fuentespuras fijadas, presupuestoambas/capturaresolución/validaciónexacta y fallbacksin-codes; no perder contenido ni quitar guardas. TDD/regresiones necesarias antes de fixproductivo. CA3/4/M0 abiertos, sin inferencia nueva desdeworker ni calidad.

**Entrega CPU de resolución DiT — 2026-10-06:** [informe](testing/t16/native-resolution-fix-report.md) y [recibo](testing/t16/native-resolution-fix-receipt.json). Orquestador verifica nueve fuentes y todos los artefactos congelados; imagen final18d94fd y seis fuentes imagen coinciden. Cobertura oficial recalculada contra Git8663287:64/68=94,12%, mínimo92,31%; no se usa cobertura acumulada. GREEN314passed/5skipped/1deselected; imagen158passed/1deselected/5avisos; verificación declarada CPU41passed. RED previos para plan/captura/manifest/instrucción/HTTP/perfil/v2 conservados en informe. Recibos v2 contienen candidatos canónicos y resolución nativa vinculada a perfil/SHA; ocho recibos CPU con orquestación/tokenizadores reales y forwards doblados se validan y publican por CLI, ocho ramas incompatibles rechazadas. Trece v1 históricos,32originales y27evidencias preservadas según recibo. No GPU ni calidad nueva. CA2 sigue abierta hasta revisión fresca y QA de esta fase; CA3/4 pendientes. No modificar common/Compose ni integrar main antes de cerrarT16.

**QA independiente nativa T16 conforme — 2026-10-06:** [informe](testing/t16/native-resolution-qa-report.md)/[recibo](testing/t16/native-resolution-qa-receipt.json). Fresh314passed/5skipped/1GPUdeselected/0avisos;41declarados incluidos en el mismoJUnit319/5skip/0errores. Root verifica9fuentes/64evidencias y7artefactosQA antespublicar; QA before/after eimage6SHA probeCPU independientes, padre sinTorch. Cobertura recalculadaGit8663287 porQA:64/68=94,12%, mínimo92,31%; noappend. Primer checkpoint dehashes fuepost-suite: QA repitió una vez la misma colección acotada para reparar before/after, no suiteglobal ni build. Recibos integración sanitizados acreditan8CPU/8rechazos/13históricos sinrerunprivateinputs. QA sinUI/coverage-checkfalse/qa-gate n/a/PDF no declarado. CA2 vuelvechecked trasTDD+reviewfreshA+B+C+QAactual; CA3/4, T16/M0 siguen abiertas. HarnessSFT30nuevo sóloprepare0, revisión/QA privada siguiente antesinferenciacon18d94fd.

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

### T-20 — Arquitectura de despliegue Docker y Ollama compartido

- **Descripción**: Registrar la arquitectura elegida por el propietario al concretar el roadmap: producto en Docker Compose, Ollama compartido en Ubuntu WSL2, ComfyUI CUDA y cola SQLite. Esta tarea documenta la decisión; su implementación y pruebas reales pertenecen a M1–M4.
- **Estado**: en-revision
- **Tiempo humano**: est. — · real —
- **Tiempo IA (ejec.)**: est. — · real —
- **Supervisión**: est. — · real —
- **Dependencias**: T-00
- **Tipo**: docs
- **Archivos**: `docs/decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md`, `docs/decisiones/ADR-0003-stack.md`, `docs/decisiones/ADR-0012-llm-de-letras.md`, `docs/decisiones/README.md`, `docs/CONSTITUTION.md`, `docs/arquitectura/sistema.md`, `docs/arquitectura/diagramas.md`, `docs/arquitectura/entorno.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md`, `docs/roadmap/2026-09-28-m1-mvp-estudio/test-plan.md`; root: `testing/t20/` y `.cache/dev-cycle/t20/`.
- **Verificación**:
  - `. .\scripts\env.ps1; uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t20/current-document-verification-20261011/repeatable/verify_current_root.py` → enlaces locales de los doce documentos válidos; hashes y recibo de verificación conservados.
  - lectura y revisión independiente: ADR-0035, constitución, arquitectura y plan M1 concuerdan; no presentan conectividad, GPU ni despliegue futuro como ya verificados.

**Criterios de aceptación**
- [x] ADR-0035 y documentos vigentes fijan Docker para web/server/engines y Ollama compartido en WSL2, sin segunda instancia ni gestión del servicio ajeno.
- [x] La cola conserva SQLite, carriles y dependencias; ComfyUI Docker/CUDA y el despliegue M1 quedan como requisitos de sus hitos con pruebas reales pendientes.
- [x] Enlaces locales, revisión independiente y ledger conformes; no se confunde documentación con implementación.

**Contexto — 2026-10-07:** decisión solicitada y elegida explícitamente por el propietario, documentada el 2026-10-06 mediante ADR-0035. Se incorpora esta tarea documental al ledger para trazar sus doce archivos y su revisión pendiente; no se amplía la implementación M0 ni se elimina un gate de otro hito. Medición histórica `.cache/dev-cycle/architecture-docker-usage.json` cerrada21:57:14UTC, fuente estimado, sin tokens/coste/horasIA medidos. **TDD n/a: prosa de arquitectura y planificación.** No nuevo presupuesto ni horas retrospectivas inventadas.

**Verificación parcial ejecutada:** helper documental exit0, `DOCUMENT_LINKS_PASS`, doce documentos y 156 enlaces locales, cero errores. [Informe](testing/t20/document-verification-report.md)/[recibo](testing/t20/document-verification-receipt.json), SHA del recibo `fda27437fbe33bb92e5c763d392db8c7692598776b9f3504d800b4677f264c54`; root cotejó doce hashes antes de publicar. Revisión independiente pendiente; ninguna prueba de despliegue o CUDA acreditada por este resultado.


**QA documental independiente conforme — 2026-10-07:**12documentos/156enlaces/0errores, coherencia de arquitectura conforme y ledger0. A+B anteriores aprobados. [QA combinado CPU/documental](testing/t09/autonomous-observability-qa-report.md). Tres criterios documentales conformes; estadoen-revisión conserva integraciónGit por tarea pendiente, sin acreditar despliegue futuro.

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

## Revisión de dos lentes — intento 1: T-08 — pasada incompleta y dos defectos CLAP

Lentes: A/C completadas CPU con contexto reutilizado; B interrumpida expresamente por defectos reproducidos, estado interrupted confirmado; D=false. No aprobación global ni B conforme. [Informe de intento 1](testing/t08/review-1.md). Los hallazgos los confirmó root mediante procesador/ruta real; no se atribuyen a un informe B inexistente.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | R-CLAP-01: truncation=False de texto llega al extractor y falla con30s | T-08 | Corregido CPU en fix1, pendiente inferencia/QA | RED real NotImplementedError; GREEN real y recibo fix1 |
| 2 | Important | R-CLAP-02: chunk_length_s no existe y rompe retorno con1s | T-08 | Corregido CPU en fix1, pendiente inferencia/QA | RED real AttributeError; GREEN real y recibo fix1 |

RED: test_clap_real_route_preserves_complete_text_and_audio_metadata[long_30s] falló con NotImplementedError: data_truncating False not implemented · 2026-10-06. RED: mismo test[short_1s] falló con AttributeError: ClapFeatureExtractor sin chunk_length_s · 2026-10-06. Evidencia .cache/dev-cycle/t08/clap-route-regression/red.log/red.xml; RED dirigido final: dos fallos/dos avisos deprecación en4,06s; primera observación añadió dos avisos de caché, destino corregido antes de captura final; sin pesos/GPU. Se incorporará/regenerará RED dirigido en el engine antes de producto. Revisión2 cubre también B pendiente, no solo fix. Lote calidad cerrado01:40:45UTC, estimado/tokens/coste/horas IA null; reloj27m no atribuido a IA. Fix1 abierto misma hora, sin solape de marcadores. Jira/Confluence desactivados, journals ajenos intactos. T-08 en-progreso, criterios abiertos y QA/GPU pendientes.

## Revisión de dos lentes — intento 2: T-08 — tres Important pendientes

Lentes A+B+C frescas, C secuencial tras completar A por límite de threads; D=false. [Informe completo](testing/t08/review-2.md). R-CLAP-01/02 corregidos CPU; inferenciaGPU y QA no aprobadas. Root acepta tres escenarios nuevos, ninguno rebatido como estilo.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A-T08-DOC-01: README58/68 ejecuta m0-t08 histórico en vez de fix1 | T-08 | Pendiente fix2 documental | README/Compose/freeze19SHA; E3 |
| 2 | Important | B-LONG-01: alineación completa no representa tiempos>399,92s pese a aceptar600s | T-08 | Pendiente fix2 segmentado con texto reconocido/offsets | Probe450s→artifact399,92s; align/parse upstream real, doblesASR/logits, no precisión |
| 3 | Important | B-INPUT-01: idioma inválido/audio no decodificable devuelven INTERNAL | T-08 | Pendiente fix2 validación/error específico | Worker real CPU, ValueError/LibsndfileError |

B ejecutó33passed4deselected1aviso4,08s enimagen80eee31, CUDAfalse. A validó19SHAfuentes/12evidencias/XML/cobertura; C19SHA/AST/lock y probesHTTPtoken/rutas CPU enmemoria sinTorch. Los tres contextos frescos independientes de implementar; no inferenciaGPU ni QA. T-08 sigue en-progreso/CA abiertas. Revisión3 reevaluará fixes y conservará conformidades salvo evidencia nueva. Jira/Confluence desactivados, journals ajenos intactos.

## Revisión de dos lentes — intento 3: T-08 — sin gaps CPU pendientes

**A+B+C frescas**, D=false; alcanceexit0sinavisos. [Informe](testing/t08/review-3.md). Reevaluación de fix2, conformidades previas conservadas. No conocimientos ajenos/Jira/Confluence.

| Criterio | Veredicto y evidencia |
|---|---|
| Base, dependencias, puerto, montajes, token y beats | Conforme CPU conservado;12fuentes idénticas a fix1 |
| Transcripción hasta600s y tiempos globales | B-LONG-01 corregido CPU; backend257/302 y regresiones450/600s, parser upstream real |
| Correspondencia texto/audio/idioma y silencios | Conforme CPU; fragmentos propios, idiomas upstream y offsets reales; precisión pendiente |
| Residencia secuencial | Conforme CPU; adapter93–102 y tests de una liberaciónASR/una cargaalineador; memoria GPU pendiente |
| Alineación independiente180s hastaM3 | Conforme al ADR0031; descriptor y rechazo181s, no sustituye el requisito completo deM3 |
| Clasificación idioma/audio inválidos | B-INPUT-01 corregido CPU; worker INVALID_PARAMS sin ocultar INTERNAL/VRAM_EXCEEDED |
| Comandos del README | A-T08-DOC-01 corregido; README69/79 y Compose2 usanfix2 |
| CLAP01/02, loaders y recursos | ConformidadesCPU anteriores conservadas, sin nueva evidencia que las reabra |
| Alcance, constitución y documentación | Conformes;20SHAfuentes y36evidencias; ADR0031/contrato/README actualizados |
| TDD y cobertura | Cinco RED reales,45CPU verdes,346/382=90,58 % mínimo88,89 %; no sustituye requisitos |
| Seguridad introducida/reabierta | C sin hallazgos, probesHTTP/AST/lock; no auditoría universal |
| Generados/interop/OpenAPI | N/a: sin cambios en esas piezas |
| Verificación completa, QA y cierre | No acreditados todavía: tres inferenciasGPU y QA pendientes; todos los CA abiertos |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A-T08-DOC-01, README usa tag antiguo | T-08 | Corregido CPU, A3 confirma | README69/79, Compose2 usanfix2/imagen306e3b0 |
| 2 | Important | B-LONG-01,600s sin tiempos representables | T-08 | Corregido CPU, B3 confirma | Fragmentos≤180s propios/offsets,12regresiones verdes; precisiónGPU pendiente |
| 3 | Important | B-INPUT-01, idioma/audio inválidosINTERNAL | T-08 | Corregido CPU, B3 confirma | Entrada INVALID_PARAMS, erroresinternos/VRAM conservados |

Cero gaps pendientes; sin rebates/deuda. T08 pasa a en-revision para QA, todos losCA siguenabiertos. A SHA/AST/XML/diffcheck; B12passed5,06s enimagenfinal sinred/CUDA/sólock, ensayo inicialsinlock conservado; C probesHTTP/AST/lock sinTorch/hijo. TresinferenciasGPU y QA pendientes, no cierre porCPU. Lote review3/diagnósticoT16 sigueabierto sin atribución individual ni cifras IA inventadas.

## Revisión de dos lentes — intento 1: T-16 instrumentación diagnóstica — un Important

A+B frescas, contexto independiente/secuencial por cupo. [Informe](testing/t16/diagnostic-review-1.md); sólo propuesta privada30s, no reinicio de revisiones previas de producto/arnés6.

| Criterio | A | B |
|---|---|---|
| Alcance privado e integridad29SHA | Conforme | Conforme |
| Una toma30s, parámetros/entradas originales | Conforme CPU, no reproduce90s | Conforme leído |
| Factoría ligera y módulo hijo importable | Conforme, IPC previo con dobles declarado | Conforme, wrappers normal/class/static CPU |
| Guardas, cap, monitor y cleanup propio | Conforme leído, antecedente sellado | Conforme leído, sinGPU |
| Propagación de fallo/parada/unload | No detectado enA | **B-01 Important** |
| Honestidad causal y CA3/4 abiertas | Conforme | Inferencia no verificable |
| E2/E3/OpenAPI | Conforme/n/a | Fuera de lente |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B-01, wrapper termina0 ante CLI error/parada/unloadfalse | T-16 | CorregidoCPU en candidato separado, pendiente revisión2/QA | AST exacto CPU demuestra3fallos; RED3failed1passed, GREEN4passed0,06s; originalbc798009 intacto y candidatore6fd237 |

Sin rebates/deuda. T16 mantieneen-progreso y CA3/4 abiertas. C/Dno disparan cachéignorada; Bcomprueba ownership/privacidad. GPUde diagnóstico todavía no ejecutada. Meterfix1 cerrado02:19:55UTC estimado/null,2m reloj con trabajoT08 concurrente no imputado comoIAindividual; loteT08GPU/T16review2 abierto mismahora. Journals ajenos preservados, Jira/Confluence desactivados.

## Revisión de dos lentes — intento 2: T-16 instrumentación diagnóstica — sin gaps CPU pendientes

A+B frescas/paralelas, [informe](testing/t16/diagnostic-review-2.md), conformidades previas conservadas.

| Criterio | Veredicto |
|---|---|
| B-01, propagación CLI/error/parada/unload | CorregidoCPU; cuatro escenariosexit1/1/1/0 |
| Cleanup y recibos antes de propagar | Conforme; bloque finally y contador único conservados |
| RED/GREEN, original y SHA | Conforme;3REDreales+1baselinepass,4GREEN; original29/fix12SHA intactos |
| Parámetros, guardas, factoryhijo/IPC, privacidad | Conformidadesprevias conservadas; sin cambios ni nueva evidencia adversa |
| Estado, límites30/90 y CA3/4 | Conforme; causa nativa/inferencia/calidad no verificablesCPU |
| E2/E3/OpenAPI/cobertura producción | N/a al diff privado; no contratos/producto tocados |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B-01, wrapperoriginalexit0antefallo | T-16 | CorregidoCPU, A2/B2 confirman; QA pendiente | Candidatoe6fd237,4escenariosCPUexit1/1/1/0, cleanup/recibos antesexit |

Cero gaps pendientes, sinrebate/deuda; QA CPUfresh qa_t16_diagnostic_fix1 en curso al publicar. CA3/4 yT16siguenabiertas, GPUdiagnóstico todavía no ejecutado. Fuente estimada/null, no consumoIAindividual ni calidadinferida.

## Evidencia posterior — T-16 QA diagnóstica y ejecución SFT30

[QA independiente](testing/t16/diagnostic-qa-report.md) conforme4/4,41fuentesSHA/prepareonly0/padresinTorch. [SFT30 real](testing/t16/native30-failure-report.md)/[recibo](testing/t16/native30-failure-receipt.json):53788terminalexit1,179,343s,stop_reasonnull/unloadtrue; traza52%/service_generate→conditioning_batch117→adapter224, causa todavía pendiente. Baseline y posterior1315/Ollama vacío, contenedor propio retirado; fuente/imagen/runner6 intactos. DiagnósticoCPU fresco native30-diagnosis; CA3/4 y M0 abiertos, sin calidad inferida.

Medición: loteGPU/diagreview2 cerrado02:19:55–02:36:02UTC,16mreloj estimado/tokens/coste/horasIA null; loteintegration-clap-sft-diagnosis abierto02:36:02, sin doble ventana ni atribución individual. BriefT08 determinista exit0 con aviso tamaño conservado en .cache/dev-cycle/t08/integration-record-verification.json. Implementer fresco implement_t08_clap_integration sóloanalysis/**+tagCompose+caché propia, REDreal previo/preservacióntexto/ventana y buildCPU. Root mantieneledger. Helperrecord-integration-diagnoses.py completó todos los writes; sólo su printfinal falló porcp1252: verificado porlectura, NOrepetir writerexclusivo.

## Revisión de dos lentes — intento 1: T-08 integración CLAP — sin gaps CPU pendientes

A+B+C frescas, Csecuencial, D=false. [Fusión](testing/t08/integration-review-1.md), parcialhistórico preservado. Nueva faseGPUfix; review3 previa no reiniciada.

| Criterio | Veredicto fusionado A+B+C |
|---|---|
| Estrategia de audio y proyección real local | Conforme CPU, una línea de estrategia corregida; backend348 y prefix65–80 |
| Texto completo/presupuesto y metadatos de ventana | Conforme, tokenizer sin truncamiento; rechazo de exceso antes del modelo; duración original y ventana10s explícitas |
| TDD/cobertura y alcance | Conforme, REDreal2/GREEN8/47CPU;90,58% global/88,94% backend; delta4files/21SHA+14artefactos |
| E3 README/tag e imagen histórica | Conforme, inversión del delta reproduce SHAfix2;7d0733f actual/306e3b0 original preservada |
| Constitución/loaders/recursos locales/auth/permisos | Conforme, sin riesgos introducidos;17fuentes previas idénticas,18fuentesimagen; User=engine |
| E2/interop/OpenAPI | N/a, contratos no tocados |
| GPUscore/ASR/QA completa/CA cierre | Pendientes; esta revisión no los acredita |

CeroCritical/Important/Minor, sinrebates/deuda. A2passed13,24/B5passed13,93s/CAst+hash21/14/18+comparacióndelta/User=engine conforme; Cprimerfixturecomillasfallido corregidoexit0. QA CPUindependiente siguiente; noGPU/scorecompleto/ASR niCA cerrados. T16implementación separada activa, todavía sin aceptaciónfinal.

## Revisión de dos lentes — intento 1: T-08 diagnóstico ASR privado — A+B+D conformes

[Informeparcial](testing/t08/asr-diagnostic-review-1-in-progress.md). A+Bfreshterminales0gaps, Cfalse/Dtrueporcache; Dfresh rechazado threadlimit, pendiente.

| Criterio | A | B |
|---|---|---|
| Factory importable en hijo y padre sinTorch | Conforme, import/preflight propios CPU | Conforme, cadena fresh éxitoPID7→11/errorPID16→20 |
| Algoritmo/loaders/cap/preflight originales | Conforme, delegación a imagen306e3b0 | Conforme, lectura completa/guardaslibre−512 |
| Inputconfined/SHA/n_outputs2/terminal yexit | Conforme, preflightrechaza2/error→2 | Conforme, éxitoexit0/error2 yterminalúnico |
| Trazasprivadas exclusivas fueraTMP/normal sincontenido | Conforme, UUID/x/mínimometadata | Conforme, delegaciónerrores ynormalcontenidoomitido |
| Unload/PID/PPID/borradoTMPfallido | Conforme evidenciaCPU | Conforme propiaCPU, descargado yTMPfallidoborrado |
| Alcance/estado/constitución/documentación | Conforme,2SHA/no producto niCA cerrado | No defectos nuevos, sinlectura conocimientoajeno |
| GPUreal/cancelación/QA yperformanceD | Pendientes | Pendientes |

CPUtransportefresh2casos/runnerexit0y2/unload/TMPcleanup/padresinTorch conformes, sin inferenciaGPU ni fixASR. No avanzarGPU antesD/fusión/QA/preflight.

**CA2 T16 reabierto para la corrección de integración actual:** conservar evidencias CPU/review/QA de controles anteriores; la nueva ramaDiT/recibov2 cambia producción y requiere revisión/QA actuales antes de volver a acreditarCA2. CA1controlesanteriores mantiene su evidencia, CA3/4 siguenabiertos. No confundir pruebas preliminares de worker con aprobación final.

## Revisión de dos lentes — intento 1: T-16 resolución nativa — A+B+C conformes

[Parcial](testing/t16/native-resolution-review-1-in-progress.md): A fresh termina lectura12rutas y59regresiones propias verdes,0gaps;9SHA/8fuentespuras/probe sinTorch conformes. B fresh activa después terminalA; C requerida pendiente, Dfalse. No QA/GPU/escucha ni cierreCA2-4; CA1 histórico preservado. Rechazo inicial B por cupo no se presenta como ejecución. TDD/coverage/imagen CPU son evidencia limitada, no calidad musical.


**Fusión final nativa T16 — 2026-10-06:** [revisión1](testing/t16/native-resolution-review-1.md). A+B+C fresh0gaps, Cexec/Dfalse; A59/B108+17/C49+probe propios CPU y avisos cache_dir declarados. Root9fuentes64evidencias congeladas conformes. Toda tabla de criterios publicada, sin sumar suites ni atribuir GPU. QA independiente siguiente, CA2/3/4 abiertas; oldcontrols/históricos preservados.

## Revisión de dos lentes — intento 1: T-08 caché ASR — A+B+C+D conformes

[Parcial](testing/t08/asr-cache-review-1-in-progress.md): A fresh0gaps/4deltafiles/22source39evidence hashes ydefaultFileCacheManager real1passed0,36s enIdd20ae562. Bfresh activa; C+Drequeridas pendientes. ConsultaADRknowledge0aciertos declarada porA pese alNO deldespacho, sinresultadousado/ningúnwrite, restricciónreforzada pararesto. Sinfusiónfinal/QA/GPU/precisión niCAcerradas; oldCLAPconformidades preservadas.

**B caché ASR terminada — 2026-10-06:** fresh0gaps/4deltafiles/22sourceSHA conformes; defaultcachepropia1passed0,37s/exit0 sinGPU/red/mounts/overrides. No knowledge consultado. Cfresh activa, D/QA pendientes; noGPUactual niASRprecision/M0cierre.

**C caché ASR terminada — 2026-10-06:** fresh0hallazgos/4deltafiles/3baselineSHA; permisosmínimos/rutafija/tokenportsmountsunchanged/testsinnewexecution, defaultcache propia1passed0,36s/exit0. Sin consultas knowledge. Dfresh activa, QA/GPUretry pendientes.

**Fusión caché ASR completa — 2026-10-06:** [revisión1](testing/t08/asr-cache-review-1.md). A+B+C+D frescas, cuatro deltas completos, cero gaps; pruebas defaultcache independientes1passed cada una. D3baselines22fuentes39artefactos19imagenSHA conformes, sin trabajo nuevo por duración. Root22/39 SHA verificados; desviación A de consulta0hits conservada, no resultado usado. QA independiente siguiente; no ASRGPU/precisión/memoria ni cierreCA/T08/M0.

**QA caché ASR corroborada — 2026-10-06:** [informe](testing/t08/asr-cache-qa-report.md) y [recibo](testing/t08/asr-cache-qa-receipt.json). Fresh48passed/4GPUdeselected/0failed/0skip/1Starlettewarning/15,97s; caché Triton real UID10001/defaultENV/0755 y regresiones CLAP CPU. Root22fuentes39previos3baselines41QAartefactos19imagenSHA/JUnit48 conformes. Incidente de interpolación Compose privado documentado sin valor; helper corregido/no-interpolate/log sanitizado y42archivos QA cero coincidencias de token real. NoGPU ni precisión/VRAM/cierre. Una sola pruebaASR30 siguiente tras preflight nuevo.

## Revisión de dos lentes — intento 1: T-16 harness de resolución nativa — A+B+C+D conformes

[Parcial](testing/t16/native-harness-review-1-in-progress.md). Dos revisores frescos, un archivo completo cada uno y delta de cuatro literales+cabecera, cero gaps. A reversión exacta/AST/prepare real/inspect; B probe CPU de imagen, seis escenarios cleanup y exits1/1/1/0, boundary1600/1601. Sin lecturaRAW/knowledge/GPU. RootdosSHA/nuevefuentes conformes; C activa y D requerida por selector, QA independiente y GPU posteriores. Producto nativo ya revisado/QA acreditado: no repetir ni confundir ámbitos. CA3/4six90/escucha pendientes.

**ASR GPU tras caché conforme técnicamente — 2026-10-06:** [informe](testing/t08/asr-cache-gpu-report.md) y [recibo](testing/t08/asr-cache-gpu-receipt.json). Exec53673 TERMINALexit0/114,19s, imagen d20ae562/job01DBAD4B3D43D84F54BC221837; texto no vacío y87palabras/último29,92s/tiemposmonótonos. ASRrelease antesForcedAlignerload, unloadhijo11/padre1sinTorch, contenedorpropioausente ypost1314. Origenpreservado/22fuentes2wrappers conformes. AutodetecciónEnglish pesealetra castellana: precisión/fidelidad pendiente, no WER ni aprobación musical. Pico/spillnull porharness no registra. No repetir originalexec61484 ni nuevo53673; próxima Verificacióncanónica actual4tareas, después contrasteidioma. T08/M0 abiertos.

**Fusión harness nativo completa — 2026-10-06:** [revisión1](testing/t16/native-harness-review-1.md). Cuatro revisores frescos, fichero completo/delta4literales+cabecera, cero gaps. C4ownershipprobes/argv/offlineUSER conforme; Dbyte/ASTidéntico/84llamadas/no mayorcarga. Rootbaseline/candidato9fuentes conformes; QA privada independiente siguiente antesexecute. No T16GPU/six90/escucha ni cierre. ASR conformanceGPU exec35808 vivo, única GPU actual; serialize posteriores.

**Contraste de idioma ASR ? 2026-10-06:** [probe l?xico privado sanitizado](testing/t08/asr-language-probe-receipt.json) sobre salida anterior congelada: 84/86tokens en vocabulario original, tramo continuo43tokens, marcadores castellanos40/ingleses3. La anomal?a parece etiqueta English aunque texto castellano coincide ampliamente; no atribuir WER/precisi?n/timestamps exactos ni corregir etiqueta a ciegas. Futuro contraste real params.language=Spanish declarado, sin suministrar letra alASR. No repetirjob original ni cambiar backend por esta heur?stica.

**VerificacióncanónicaGPU T08 actual — 2026-10-06:** [informe](testing/t08/conformance-gpu-report.md) y [recibo](testing/t08/conformance-gpu-receipt.json). Exec35808 TERMINALexit0/177,69s; pytest4passed/0errores/174,94s, ASR+ForcedAligner/CLAP/Audiobox/beatsCPU±2 reales, cadaunoassert childPIDdiferente+unload. RootJUnit4/salidas4/22fuentes conformes; imagenfinald20ae562/tagcorrecto/contendorpropioausente/post1314. Sinpico/spill ni precisión ASR o calidadinventadas; pending cotejoQAinteg yT08closure/main dependeT16. No re-poll/restart de exec35808.

**QA nueva harnessnativo corroborada — 2026-10-06:** [informe](testing/t16/native-harness-qa-report.md) y [recibo](testing/t16/native-harness-qa-receipt.json). Fresh14passed/0failed/1cachewarning/exit0; bloqueASTexits1/1/1/0+cleanup/close, prepare-only completoHTTP0/subprocess0/Torchfalse, boundary1600admitido1601rechazado/6ownershipcasos. Root44frozen11QAartefactos/JUnit14 SHA conformes; no Docker/GPU/productsuite rerun, coverageappliesfalse/qa-gaten.a/PDFpendiente. Harness5a3bfa6f ahora revisiónA+B+C+D+QA14 conformes; siguiente rootpreflightfresh yONE SFT30 image18d94fd, sin six90/escucha acreditadas.

**SFT30 real conforme tras resoluciónnativa — 2026-10-06:** [informe](testing/t16/native30-success-report.md) y [recibo](testing/t16/native30-success-receipt.json). Exec75371 TERMINAL0/group181,38s/job01M47NPBCBBRBG9V3GVAD4JAEF; no re-poll/restart. WAVFLOAT48k/2/30s exactos/RMS0,18726/finito ymanifestvalid1. Receiptv2 actualramacover text150previstos=150capturados/lyrics256/instructionSHAigual; controlsSFT50CFG7shift1/esBPM94. Pico7807,94cap10117,13spilledfalse/unloadconfirmado/post1314/propioausente. WSL74muestras peakused4763,93/swap6,04MiB; run162,42incluyeload124,26/RTFnull. Root9fuentes intactas. No prueba90/six6/escucha; CA3/4abiertas. Implementerfresh prepare_t16_native_comparison activo sólocache nueva para derivarconfigimagen18d94 ynamespace delrunner6tomasyplan, conservaoriginales; necesita review/QAantesGPU.

**Preparación comparación nativa recibida — 2026-10-06:** [informe](testing/t16/native-comparison-config-report.md)/[recibo](testing/t16/native-comparison-config-receipt.json). FreshREADY_CONFIG_ONLY; runnera349bb27/plana68a2ff5, planúnicocambioimage18d94fd yrunner6tipos7ocurrencias+cabecera configdestinospropios. Root51frozen12artefactos/dosoriginalesdosderivados/rollbackexacto conformes, prepare-only0/AST3.11. Briefdeterminista31kcharswarnheredado/trazable, memoriaomitidaporscope; no lookupdocs/knowledge. Scope0/sinavisos yselectorC+Dtrue explicitfiles2 enprivate review-scope.json. Review1fresh4lenses+QA pendientes antes6new90, sinGPU ni código producto. Verificadorprimerofallópor prerequisiteinexistente corregido antescandidatos, noRED/nologicalfix.

## Revisión de dos lentes — intento 1: configuración comparación nativa T-16

[Parcial](testing/t16/native-comparison-review-1-in-progress.md): A/B frescas conformes, cero gaps; C/D activas, QA pendiente. Verificación de T-16 actualizada al ejecutor derivado con imagen inmutable actual, conservando ejecutor/plan históricos. El delta sólo configura destinos e imagen y mantiene toda la lógica revisada. Prepare-only real por B exit0; pruebas de ownership/limpieza con dobles, no contenedores reales. Primeros probes de A/B fallaron por codificación JSON Windows y se corrigieron a UTF-8, sin tocar candidatos. No seis90 ni aprobación musical. Ninguna consulta a knowledge o memoria.

**Fusión comparación nativa — 2026-10-06:** [revisión completa](testing/t16/native-comparison-review-1.md). A+B+C+D frescas conformes, cero gaps. El pool obligó a escalonar; candidato y plan SHA constantes. Probes CPU e inspect sin GPU, CA3/4 abiertas. QA independiente siguiente antes de seis90. Incidencias locales de probes declaradas, sin cambios del candidato ni RED de producto.

**QA comparación nativa — 2026-10-06:** [informe independiente](testing/t16/native-comparison-qa-report.md)/[recibo](testing/t16/native-comparison-qa-receipt.json). 14/14CPU, cero fallos/errores/omitidas; un aviso de opción cache_dir con cacheprovider desactivado, declarado. Prepare-only real0 y completo con dobles0, guardas baseline1600/1601, ownership/colisión/shutdown/fallos probados. Root54fuentes16artefactos/JUnit verificados, freeze intacto. Ledger0incoherencias/6avisos; coverage y qa-gate n/a sinUI, sin porcentaje/E2E inventado. PDF pendiente por runtime inexistente, sin instalar. Cuatro lentes y QA conformes: siguiente preflight nuevo y una comparación seis90 por root con runner derivado. Sin GPU de QA, qualityfalse/winnernull y CA3/4 pendientes.

**Ejecución seis90 y preparación de empaquetado — 2026-10-06:** comparación aprobada en curso, exec82669/sesión01M47Q4EJZK09RBPA0ECWC57D4, primer grupo Turbo, contenedor propio bd71e7406f31 y job01M47Q4HNW4F6191D0EZ3V927D; baseline1314/Ollamavacío/8101idle-unloaded. No inferir resultados de un proceso vivo ni reiniciar por timeout de observación. Fresh worker entregó [packer derivado](testing/t16/native-packer-config-report.md)/[recibo](testing/t16/native-packer-config-receipt.json): sólo tres rutas y comentarios, SHAe09d8143, original226b3122 preservado. Root71rutas69existentes9artefactos verificados, scope0 sin avisos ni exclusiones de usuario. Revisión/QA fresca del packer pendientes antes de usarlo. La creación de nuevas salidas/puntero por la GPU de root es una mutación externa esperada, no modificación del candidato ni de datos históricos.

## Revisión de dos lentes — intento 1: configuración del empaquetador nativo T-16

[Fusión completa](testing/t16/native-packer-review-1.md): A+B+C+D frescas sin gaps; revisión estática/CPU únicamente, candidatoe09d8143 intacto. QA independiente pendiente antes de empaquetar. Las salidas nuevas de GPU root no se confunden con los69archivos existentes congelados. Tres Turbo ya terminaron: groupsexit0/unloadtrue/stopreasonnull/258,08s, SFT en curso; sin seis90 ni calidad acreditados aún.

**QA del packer nativo — 2026-10-06:** [informe independiente](testing/t16/native-packer-qa-report.md)/[recibo](testing/t16/native-packer-qa-receipt.json). 20/20CPU, pytest0; AST3.11gramática/host3.12. Rutas/regex, referencia atómica con colisiones/interrupción/carreras y manifiesto hijo/linaje probados con dobles. Root71rutas existentes y artefactos propios SHA/JUnit conformes; dos null no observados por generación externa autorizada. El mensaje intermedio decía73: se usan freeze/recibo/informe verificables71. Ledger0incoherencias6avisos; coverage/qa-gate no ejecutados, porcentajesnull; PDF pendiente. Finalización falló por log UTF16 de PowerShell, se decodificó BOM sin repetir tests. Revisiones y QA completas permiten el pack real de la sesión seis90 ya terminalexec82669exit0, ambos gruposunloadtrue/stopreasonnull. Calidad y CA3/4 aún por acreditar con pack real/escucha.

**Fallo de integración real del pack — 2026-10-06:** [diagnóstico inicial](testing/t16/native-packer-integration-failure.md). GPUexec82669terminal0 con seis90 preservadas; pack CPUe09d8143exit1KeyErrorrequest89 antes de normalización/copia. Pasa a debug-root-cause/TDD, freshimplementerfix_t16_native_packer_contract, ownership nuevo native-packer-contract-fix1, sin regenerar ni relajar validador. CA3/4 abiertas. [Listener preparado](testing/t16/native-listener-config-report.md): sólo cuatro literales,20fuentes8artefactos verificados; baseline38líneas (brief decía40, setupassert corregida antescandidato). Revisión/QA y fullpack pendientes antes de servir8768; servidores8766/8767 conservados.

**Proyección de rutas para documentación pública — 2026-10-06:** el recibo público de QA de comparación contenía rutas absolutas locales en argv; se sustituyeron por rutas relativas o <plugin> antes de Git. El recibo privado original y copia previa permanecen por SHA; publicación actual distingue digest privado de público. No cambiaron resultados, fuentes, tests ni evidencia de ejecución. La proyección de recibo del fix ya aplica esa misma regla.

## Revisión de dos lentes — intento 1: configuración del listener nativo T-16

[Fusión](testing/t16/native-listener-review-1.md): A+B+D frescas sin gaps, Cfalse por selector. B88casosCPUcon doblesexit0, A/DverificacionesAST/SHA; ningún puerto/servidor real. QA independiente y fullpack verificado pendientes antes8768.

## Revisión de dos lentes — intento 1: contrato real del packer nativo T-16

[Fusión completa](testing/t16/native-packer-contract-review-1.md): A+B+C+D frescas sin gaps, mismafuente182e7f91 y9tests independientes por lente; baselineKeyError y ocho guardas corroborados por B. Scope0/selectorC+D; QA independiente siguiente antes nuevo fullpack. Dobles sóloaudio/medida/manifest, realvalidator/6envelopes; no calidad o CA3/4 acreditadas aún.

**QA final de contrato y listener — 2026-10-06:** [contrato](testing/t16/native-packer-contract-qa-report.md)/[recibo](testing/t16/native-packer-contract-qa-receipt.json), 9/9 CPU con seis envelopes reales y ocho conflictos rechazados; root90rutas/artefactos/JUnit intactos. [Listener HTTP](testing/t16/native-listener-qa-report.md)/[recibo](testing/t16/native-listener-qa-receipt.json), 54/54 sobre fixtures de bytes y handler original, puerto efímero cerrado; root28rutas/22artefactos intactos. Ambas QA independientes conformes, ledger0incoherencias6avisos, puertas sinUI n/a y porcentajesnull, PDFpendiente. Fullpack/audio real/escucha siguen pendientes; CA3/4 aún abiertas. Se permite ejecutar el packer corregido182e7f91 una vez sobre la sesión terminal preservada, sin regenerar GPU.

**Integración real seis90 y pack — 2026-10-06:** [informe](testing/t16/native-six90-success-report.md)/[recibo](testing/t16/native-six90-success-receipt.json). Runnerexec82669terminal0; packercorregido182e7f91exec21757terminal0, seis90 y trespares, nativeinputs matched, target−17,0425LUFS, referenciaSHAintacta, no compresor/limiter. Root verifica seismaestros/recibos/manifiestos y HTTP22/22 sobre8archivos reales; privados404. Ambosunload y contenedorespropiosremoved; baseline1314, peak7893,35MiB, capmín10114,70, spilledfalse heurístico, sin sharedGPU/RTFinferencia medidos. Listenerexec84042 vivo en8768, históricos8766/8767 intactos. Browser rechazó abrir el origen por política; no workaround ni render/escucha inventados. QA independiente fullpack en curso; CA3/4 se resolverán con evidencia y valoración, sin ganador ni M0cierre.

**QA de integración real T-16 — 2026-10-06:** [informe](testing/t16/native-fullpack-qa-report.md)/[recibo](testing/t16/native-fullpack-qa-receipt.json). 113/113comprobaciones, exit0, root61fuentes/13artefactos/JUnit intactos. Seisparents+seischilds reales: codec/48k2/90s/finito/no silencio, nativeplanned ycaptured LM/DiT/metadata iguales por trespares, hashes/linaje; seis recodificaciones volume-only idénticas SHA. Referencia exacta227,640979s. Verificación canónica scripts/verify_manifest.py: data/cli/ allvalid21, carpeta escucha allvalid6, ambosexit0. CA3checked; T-16 pasa a en-revision con CA4manual de ritmo/afinación/voz/instrumentos aún pendiente. Calidadfalse/winnernull; no cancióncompleta por suposición, no Gitcierre ni M0cierre. HTTPreal22 de root separado; browserrender rechazado por política. PDFpendiente sininstalación.

**Preparación real XL T-09 — 2026-10-06:** [informe](testing/t09/weights-preparation-report.md)/[recibo](testing/t09/weights-preparation-receipt.json). Fetchcanónicoexec11975terminalexit0,05:11:19–05:16:01UTC, lockSHA9ca1c954intacto; rootJSONvsHEAD confirmaúnicoregistrosilenceXLclasificadopickle/convertedauditadoigualTurbo. Cuatroshards19949340504bytes y10archivos finales con sellosSHA/tamaño/mtimeconformes, sinrehashear20GBroot. Tensorconvertido1, no.ptfinal/noTorchpickleload. CodeTDDregistro/T09 permanece con implementer activo; copiarRED/GREENfinal delrecibo al aceptar. NoCPU/GPUfit/INT8/RTF/benchmarkcalidad acreditados por esta descarga. No repetirexec11975/writers.

**Valoración parcial nativa T-16 — 2026-10-06:** [Informe](testing/t16/owner-native-feedback-report.md)/[recibo](testing/t16/owner-native-feedback-receipt.json). JSON descargado por propietario, copia885bytes/SHA2143e5fe inmutable dentro de sesión. Preferencia explícita P1A; cuatro comentarios sobre sincronía/ritmo/voz/chorus conservados literalmente. Pares2/3 sin preferencia y24puntuaciones vacías: no inferir votos ni ganador, no aprobación musical. Mapa sigueprivado, T16en-revision/CA4pendiente; T09 continúa. Lectura browser rechazada incluso con autorización por preferencia guardada; alternativa es archivo entregado por usuario, sin workaround ni cambio de permisos. TDDn/a feedback/prosa, ceroGPU/audio nuevo.

**Entradas offline T-09 — 2026-10-06:** [Informe](testing/t09/inputs-preparation-report.md)/[recibo](testing/t09/inputs-preparation-receipt.json). Cuatrofixtures propias y declaradas, caption/letra del fragmentoT16 idénticos para30/60/180/300, sólo duración varía; manifestSHAa1c83e0776ef1ef5bd39e51e14a423ff8918a7039dd28409d51bc2af37da8e41. Ningún job/código histórico reutilizado ni HTTP/modelo/GPU. Originales intactos; los180/300s miden rendimiento con condicionamiento constante, no cancióncompleta/calidad. Harness aún activo/nofreeze; no ejecutarCLI hasta revisión/QA/imagen/prerrequisitos. TDDn/a datos/prosa; todosCAbenchmark abiertos.

**Sonda Windows real T-09 — 2026-10-06:** Inventario DXGI identifica RTX5070 y adaptador software; sólo lectura, sin GPU/modelos/ventanas/browser/Docker. Fuentes intactas durante sonda (.cache/dev-cycle/t09/windows-native-read-probe/receipt.json). Constructor PDH falla con IndexError en benchmark_windows.localized: registro Perflib009 real12521entradas, termina en cadena vacía y tiene longitud impar. registry-shape.json confirma causa; fix TDD del implementer pendiente antes freeze/revisión/QA. No mapping PDH ni sharedGPU acreditados aún; no benchmark. Root comunicó evidencia y no modificó producción.

**Diagnóstico Windows T-09 conforme lectura — 2026-10-06:** [Informe](testing/t09/windows-native-probe-report.md)/[recibo](testing/t09/windows-native-probe-receipt.json). Sonda3 nativa: DXGI5070→LUIDexacto→PDH agregado, dosadaptadores/tresmuestras/todosstatus0; shared85,4648MiB/dedicated1343,4844MiB en reposo. Fuentes antes/después idénticas; sinGPU/modelos/browserventanas. Diagnóstico4fases aplicado: terminadorREG_MULTI_SZ yaliasesPerflib confirmados contra registro/API nativa, fixTDD por implementer ylectura real verde. FaltaQA/cobertura/calibraciónTaskManager/navegador/preflight/inferencia; noRTF/nofit/nobenchmark. Prohibiciónownershipknowledge respetada, gotchaomitido por instrucción superior.

- RED: scripts/eval/tests/test_benchmark_windows_cpu.py::test_registry_multisz_trailing_empty_terminator_is_supported falló con IndexError de terminador impar vacío · 2026-10-06T05:33:54.9084721Z. Recibo privado SHA8003a189c83b6d85ce06e788bfb130618a3af047acd596e910a10bcf9eb768fd; fuentes/corrección documentadas en el recibo portable.

- RED: scripts/eval/tests/test_benchmark_windows_cpu.py::test_duplicate_counter_indices_accept_only_unique_localized_name falló con ValueError localized_counter_unresolved ante dos índices con igual traducción · 2026-10-06T05:35:49.8415124Z. Recibo privado SHA8d49c7656033d12f7c86152ae110f5978f36b642de915a5fcb36b867f3162402; fuentes/corrección documentadas en el recibo portable.

**Diseño aprobado T-10 — 2026-10-06:** [Diseño](testing/t10/capabilities-design.md)/[recibo](testing/t10/capabilities-design-receipt.json)/[publicación](testing/t10/capabilities-design-publication.json), O1 elegida bajo autorización del propietario, [ADR-0034](../../decisiones/ADR-0034-capacidades-nativas-y-accesibles-por-v1.md). Root coteja30fuentes locales/11oficiales/snapshotfijado/seisbaselines/originales; deriva concurrente T09 registrada, interfaces deberán revalidarse al freeze. Ochoops/cincofeatures y superficies /v1/nativa separadas; permisosverified sólo evidencia accesible real. Materiales propios/autorizados y LoRA seguro/evaluador tonal pendientes; separación estimada no groundtruth, sin trainingM5 implícito. T10 continúa borrador, ceroGPU/pruebas/opsverificadas, implementación posterior con ownershiptrasT09. TDDn/a prosa/diseño.


**Entrega CPU T-09 congelada — 2026-10-06:** [Informe](testing/t09/cpu-delivery-report.md)/[recibo](testing/t09/cpu-delivery-receipt.json). Root verifica32SHA/tamaños, receipt542ecba4/freeze4e08be1e, suite223passed/5skipped/1GPUdeselected/1aviso22,02s y JSON oficial: media aritmética15archivos85,33%, no mínimo individual ni cobertura de líneas del diff. Ruffdirigidoexit0. Diff completo aislado contra seisbaselinesproducción/tests recuperados y HEAD8663287, sin revertir cambios previos. ADR33 se declara con ruta literal en Archivos para scope-check (la decisión ya aprobada era necesaria; el enlace solo no lo reconocía). Revisión/QA pendientes; no build/GPU/RTF/fit/INT8real/benchmark/calidad, todosCA abiertos. TDDn/a publicación/prosa.

- RED: `scripts/eval/tests/test_benchmark_plan.py::test_default_matrix_has_160_fresh_jobs_and_alternates_arms` falló con `E       AssertionError: Falta matriz �ntegra` · 2026-10-06T05:11:35.9062807Z (T-09, evidencia red-harness-1.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_runtime_uses_loopback_no_global_teardown_and_secret_env` falló con `E       AssertionError: Falta backend propio` · 2026-10-06T05:13:47.5856516Z (T-09, evidencia red-harness-10.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_storage_copies_locked_safe_files_and_preserves_layout` falló con `E       AssertionError: Falta copia verificada` · 2026-10-06T05:13:48.0132775Z (T-09, evidencia red-harness-11.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_observers.py::test_sensor_errors_are_null_not_zero_and_pdh_localized_paths` falló con `E       AssertionError: Falta sensor NVML separado` · 2026-10-06T05:13:48.3716007Z (T-09, evidencia red-harness-12.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_runner_timeout_preserves_existing_job_and_does_not_duplicate` falló con `E       AssertionError: Falta runner de job vivo` · 2026-10-06T05:16:23.2984166Z (T-09, evidencia red-harness-13.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_manual_prerequisites_require_real_taskmanager_browser_and_sha` falló con `E       AssertionError: Falta preflight WDDM manual` · 2026-10-06T05:16:23.7421731Z (T-09, evidencia red-harness-14.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_row_rejects_fake_timing_or_missing_sensor` falló con `E       AssertionError: Falta row validity` · 2026-10-06T05:16:24.0890747Z (T-09, evidencia red-harness-15.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_session_runner_submits_once_after_estimate_and_resume_uses_receipt` falló con `E       AssertionError: Falta ejecuci�n/reanudaci�n idempotente` · 2026-10-06T05:18:58.7180970Z (T-09, evidencia red-harness-16.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_gpu_lease_refuses_live_or_other_owner_and_ollama_restores_identity` falló con `E       AssertionError: Falta lease GPU de due�o exacto` · 2026-10-06T05:20:24.5822403Z (T-09, evidencia red-harness-17.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_cli.py::test_prepare_only_writes_plan_but_no_public_report` falló con `E       AssertionError: Falta CLI can�nica` · 2026-10-06T05:20:51.2129844Z (T-09, evidencia red-harness-18.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_cli.py::test_canonical_missing_inputs_fails_without_fake_report` falló con `E       AssertionError: Falta CLI can�nica` · 2026-10-06T05:20:51.5936154Z (T-09, evidencia red-harness-19.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_plan.py::test_inputs_require_authorship_no_audio_codes_and_all_durations` falló con `E       AssertionError: Falta puerta de autor�a` · 2026-10-06T05:11:36.2859560Z (T-09, evidencia red-harness-2.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_resume_lease_can_resume_again_after_dead_owner_preserving_old_claim` falló con `E       FileExistsError: [Errno 17] File exists: '<repo>\\.cache\\pytest-tmp\\55978390fb4349ddb9374c871748c805\\gpu.resume-claim'` · 2026-10-06T05:26:41.7552345Z (T-09, evidencia red-harness-20.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_copy_refuses_low_space_instead_of_partial_or_external_storage` falló con `E       AssertionError: Falta puerta de espacio de copia` · 2026-10-06T05:32:50.0692286Z (T-09, evidencia red-harness-21.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_fidelity_uses_actual_wav_duration_and_rejects_rehashed_wrong_seed` falló con `E       Failed: DID NOT RAISE ValueError` · 2026-10-06T05:35:24.2837106Z (T-09, evidencia red-harness-22.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_evidence.py::test_event_sequence_and_single_terminal` falló con `E       AssertionError: Falta puerta de eventos` · 2026-10-06T05:11:36.6409337Z (T-09, evidencia red-harness-3.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_evidence.py::test_reference_uses_exact_three_valid_warm_same_cell` falló con `E       AssertionError: Falta referencia elegible` · 2026-10-06T05:11:37.0026338Z (T-09, evidencia red-harness-4.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_evidence.py::test_report_redacts_private_fields_and_preserves_missing_rows` falló con `E       AssertionError: Falta reporte honesto` · 2026-10-06T05:11:37.3618656Z (T-09, evidencia red-harness-5.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_resume_queries_existing_job_without_resubmitting` falló con `E       AssertionError: Falta recuperaci�n real` · 2026-10-06T05:11:37.7129002Z (T-09, evidencia red-harness-6.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_container_cleanup_requires_id_and_all_labels` falló con `E       AssertionError: Falta ownership exacto` · 2026-10-06T05:11:38.0689099Z (T-09, evidencia red-harness-7.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_observers.py::test_windows_luid_mapping_rejects_ambiguous_5070` falló con `E       AssertionError: Falta mapping DXGI exacto` · 2026-10-06T05:11:38.4197286Z (T-09, evidencia red-harness-8.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_observers.py::test_shared_gpu_requires_two_samples_and_missing_stays_unknown` falló con `E       AssertionError: Falta observaci�n separada` · 2026-10-06T05:11:38.8015146Z (T-09, evidencia red-harness-9.json; GREEN suite223).

- RED: `apps/engines/acestep/tests/test_benchmark_profiles.py::test_int8_requires_all_decoder_linears_and_pinned_versions` falló con `E       Failed: DID NOT RAISE Exception` · 2026-10-06T05:37:22.4867750Z (T-09, evidencia red-int8-partial-quantization.json; GREEN suite223).

- RED: `apps/engines/acestep/tests/test_benchmark_profiles.py::test_each_warm_run_resets_peak_and_cold_preserves_load_peak` falló con `E       assert (1000.0 == 1000 and 1000.0 == 200)` · 2026-10-06T05:30:30.7133606Z (T-09, evidencia red-peak-per-run.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_windows_cpu.py::test_duplicate_counter_indices_accept_only_unique_localized_name` falló con `E           ValueError: localized_counter_unresolved` · 2026-10-06T05:35:49.8415124Z (T-09, evidencia red-windows-duplicate-indices.json; GREEN suite223).

- RED: `scripts/eval/tests/test_benchmark_windows_cpu.py::test_registry_multisz_trailing_empty_terminator_is_supported` falló con `E       IndexError: list index out of range` · 2026-10-06T05:33:54.9084721Z (T-09, evidencia red-windows-reg-multisz.json; GREEN suite223).


## Revisión de dos lentes — intento 1: T-09 CPU — siete Important pendientes

Lentes A+B+C+D; C sin hallazgos, D contexto reutilizado deC por límite de threads y separado de implementación/A/B. [Informe](testing/t09/review1-report.md)/[recibo](testing/t09/review1-receipt.json). Scope0/sinavisos/32SHAintactos/exportcontractcheck0; cobertura media85,33% oficial. A45/B18/C18/D20testsdirigidos CPU se solapan; noGPU/RTFreal/calidad. SieteImportant deduplicados, ningunoCritical/Minor; T09en-progreso, todosCAbenchmark abiertos. Corregir conTDD antes intento2/QA/GPU. No promociónknowledge/jira (ownership ajeno/desactivado).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R09-01 | Important | Duración solicitada no validada | T-09 | pendiente | A1/B3; `scripts/eval/benchmark_runner.py:297`; Solicitud30s, WAV8frames/48k y telemetría concordante pasan output/fidelity/row valid con duración real0,0001666667s. |
| R09-02 | Important | VRAM en reposo ausente del informe | T-09 | pendiente | A2; `scripts/eval/benchmark_evidence.py:170`; Baseline1497,123MiB existe en plan privado pero no aparece en Markdown canónico, pese a CA3. |
| R09-03 | Important | Copia, amortización y dispersión omitidas | T-09 | pendiente | A3; `scripts/eval/benchmark_evidence.py:167`; copy_s12345,678 desaparece del informe; falta amortización bind/copia y dispersión previstas por diseño§5.6/§5.9. |
| R09-04 | Important | Stream bloquea muestreo periódico | T-09 | pendiente | B1/D1; `scripts/eval/benchmark_runtime.py:56`; 51eventos en2,516s producen1muestra con interval_s1. La inactividad no limita duración de llamada. SFT50pasos×0,8s daría1frente≈40muestras (escenario, noGPUmedido). |
| R09-05 | Important | Cleanup por error rompe resume | T-09 | pendiente | B2; `scripts/eval/benchmark.py:365`; Error health transitorio elimina contenedor sin cleanup.json; resume inspeccionaIDeliminado y fallaDOCKER_ACTION_FAILED después deTRANSPORT_UNAVAILABLE. |
| R09-06 | Important | Carga cold mezclada con warm sin carga | T-09 | pendiente | B4; `scripts/eval/benchmark_evidence.py:141`; 8cold×31s+24warm×0s producen recomendación carga mediana0,000s pese a mediana cold31s. |
| R09-07 | Important | Verificador acepta captura contradictoria | T-09 | pendiente | B5; `scripts/eval/benchmark_runner.py:367`; Recibos rehasheados con guidance_scale1frenteCFG7, metadataLMduración300frente30 o arguments_sha256DiTincorrecto pasan fidelity_valid. La captura actualrechaza esos parámetros conINVALID_PARAMS: fallo del verificador, no prueba de inferencia incorrecta. |


**Arranque fix1 T-09 — 2026-10-06:** implementer fresco `/root/fix_t09_cpu_review1`, brief determinista exit0/12375chars con aviso preexistente+suplemento de sieteImportant. Ownership cuatro módulosbenchmark/scripts/eval y tests, rootdocs/ledger/Git; noCPUfreezeaceptadoaún, esperarRED/GREEN/freeze. Review1cerradaantesventanafix1(17:29:32UTC), estimado/nullsinimputarrelojhorasIA. MatizR09-07 SHAkwargsDiTno reconstruibleconesquemaactual se debatirá conevidencia; sí corregirCFG/metadatos verificables, sinchangeengine. NoGPU/Docker/pesos/red/knowledge ni nuevos informesbenchmark.


**API INT8 real CPU — 2026-10-06:** [Informe](testing/t09/cpu-int8-api-report.md)/[recibo](testing/t09/cpu-int8-api-receipt.json). Imagen18d94inmutable/Torch2.10cu128/torchao0.16, LinearCPU32×16BF16→INT8configv1real, verificadoractual1/1capasAQT/Plain/storageint8, exit0/CUDAfalse. Objetooffloadsintético, ningúnDiTreal/GPU/fit/cargaXL/benchmarkacreditado. ContenedorruncsinGPU/modelos/red, sololectura/tmpfslimitado, inspecciónIDlabelsimageexited/removalconforme, fuenteadapter92caintacta. Advertenciadeprecaciónv1futura nojustificacambioperfilfijadoahora. PrerrequisitoAPI despejado, resto pendiente; CPUfix1worker continúa sin colisión, TDDn/a observación/prosa.


**Aceptación fix1 T-09 CPU — 2026-10-06:** [Informe](testing/t09/fix1-report.md)/[recibo](testing/t09/fix1-receipt.json). Root32fuentes/32preimágenes/76artefactosSHA/tamaños, ochoarchivoscambiados/24ajenosintactos, receipte4566e7c/freezee98697e6. Suite243passed/5skipped/1GPUdeselected/1aviso22,93s; coberturaoficialmedia15archivos86,81%, mínimoindividual64,11%, Ruff/formato8exit0. TransporteHTTPResponseenmemoria/cadencia/deadline/cleanupresume/estadocoldwarm/duración/CFGmetadatos conREDGREEN. R09-07subcasoSHA64hexdescartado(rebatido): faltankwargsdinámicos/códigosLMpreimagen enreceipt, adapter269–294guardas/shaactual ypreflight228–255planned; casosCFG/metadata sícorregidospendienterevalidar. Restogaps aún pendientesrevisión2/QA; ningúnGPU/modelo/benchmark/calidad ni cierreCA. Costemedidordelroot estimado/nullsinhorasfalsas.

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_requested_duration_rejects_tiny_wav_even_with_matching_telemetry` falló con `E       Failed: DID NOT RAISE ValueError` · 2026-10-06T17:30:29.8827527Z (T-09fix1/R09-01-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_evidence.py::test_report_publishes_baseline_without_private_fields` falló con `E       AssertionError: assert ('1497.1230' in '# Benchmark RTX 5070\n\nSesi�n: `CPU`.\n\nTiempos en segundos; memoria en MiB. `run_s` incluye carga; RTF usa el relo...uraciones.\n\nNVML/CUDA, sharedGPU WDDM y RAM/swap WSL son �mbitos separados; null conserva una observaci�n ausente.\n')` · 2026-10-06T17:31:14.8678001Z (T-09fix1/R09-02-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_evidence.py::test_report_copy_amortization_and_warm_dispersion` falló con `E       AssertionError: assert ('copy_s' in '# Benchmark RTX 5070\\n\\nSesi\xf3n: `CPU`.\\n\\nTiempos en segundos; memoria en MiB. `run_s` incluye carga; RTF usa el relo...s; null conserva una observaci\xf3n ausente.\\n\\nComparaci\xf3n de carga por parejas:\\n\\n- base, 30 s: bind\u2212copia=30.000 s.\\n')` · 2026-10-06T17:31:20.8027850Z (T-09fix1/R09-03-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_real_http_response_continuous_events_keep_sampling_and_deadline[False]` falló con `E           Failed: DID NOT RAISE ObservationTimeout` · 2026-10-06T17:33:19.5710348Z (T-09fix1/R09-04-deadline-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_json_status_transport_has_deadline_even_with_continuous_bytes` falló con `E       Failed: DID NOT RAISE ApiError` · 2026-10-06T17:40:18.5225495Z (T-09fix1/R09-04-json-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_runtime.py::test_real_http_response_continuous_events_keep_sampling_and_deadline[True]` falló con `E       assert 1 >= 3` · 2026-10-06T17:33:17.8616403Z (T-09fix1/R09-04-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_integration_cpu.py::test_cleanup_error_receipt_and_resume_never_inspect_dead_container_or_duplicate[after_post]` falló con `E       AssertionError: durable cleanup receipt missing` · 2026-10-06T17:34:39.4883338Z (T-09fix1/R09-05-ack-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_integration_cpu.py::test_cleanup_error_receipt_and_resume_never_inspect_dead_container_or_duplicate[after_rows]` falló con `E               ValueError: removed_container_has_submitted_job_requires_inspection` · 2026-10-06T17:38:23.1218979Z (T-09fix1/R09-05-known-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_integration_cpu.py::test_cleanup_error_receipt_and_resume_never_inspect_dead_container_or_duplicate[before_post]` falló con `E       AssertionError: durable cleanup receipt missing` · 2026-10-06T17:34:39.0075429Z (T-09fix1/R09-05-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_evidence.py::test_recommendation_load_uses_cold_only` falló con `E       AssertionError: assert 'carga cold mediana 31.000 s' in 'Default operativo candidato: `base`; RTF mediana 0.2000, carga mediana 0.000 s, pico 7000.0 MiB, sin aumento sharedGPU observado. Modo de alta calidad pendiente de ejecuci�n v�lida y escucha.'` · 2026-10-06T17:31:15.6797365Z (T-09fix1/R09-06-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_rehashed_capture_rejects_verifiable_contradictions[cfg-effective_controls_mismatch]` falló con `E       Failed: DID NOT RAISE ValueError` · 2026-10-06T17:36:09.6352236Z (T-09fix1/R09-07-cfg-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_rehashed_capture_rejects_verifiable_contradictions[dit_hash-capture_hash_invalid]` falló con `E       Failed: DID NOT RAISE ValueError` · 2026-10-06T17:36:10.5936986Z (T-09fix1/R09-07-hash-red; GREENdirigido y suite243).

- RED: `scripts/eval/tests/test_benchmark_runner.py::test_rehashed_capture_rejects_verifiable_contradictions[lm_duration-effective_lm_metadata_mismatch]` falló con `E       Failed: DID NOT RAISE ValueError` · 2026-10-06T17:36:10.1322631Z (T-09fix1/R09-07-metadata-red; GREENdirigido y suite243).


## Revisión de dos lentes — intento 2: T-09 CPU — dos Important residuales

Lentes A+B+C+D frescas, solo lectura. [Informe](testing/t09/review2-report.md)/[recibo](testing/t09/review2-receipt.json). 32 SHA intactos, scope0/sin avisos. A39/B39/C13/D16 tests CPU se solapan. Resultado0Critical/2Important/0Minor; T09 en-progreso, todos CA GPU abiertos. R09-01/02/03/05/06 corregidos; R09-07 CFG/metadatos/formato corregidos y subcaso SHA64hex descartado (rebatido) por ausencia de preimagen dinámica, con guardas/hash reales del adapter. R09-04 permanece parcial por dos causas reproducidas. Corrección TDD y diagnóstico antes revisión3 de3/QA/GPU. No knowledge/Jira.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R09-04a | Important | El parser chunked puede superar el plazo global | T-09 | pendiente | B2; `scripts/eval/benchmark_runtime.py:94`; HTTPResponse válido: cabecera de chunk 36\r\n enviada byte a byte cada 25 ms. Un presupuesto de 40 ms devuelve done tras aproximadamente 109 ms. read1 llama internamente a readline y efectúa varias lecturas con timeout de inactividad; el límite externo no las interrumpe. |
| R09-04b | Important | El presupuesto del stream no descuenta el coste del sensor | T-09 | pendiente | D2; `scripts/eval/benchmark_runner.py:119`; Observación CPU de 4 s, intervalo de 1 s y sensor síncrono de 0,5 s: tres muestras, intervalos 1,500/1,500 s. Concede otro segundo al stream después del sensor. La latencia real de los sensores no se ha medido; el caso sintético demuestra el defecto de programación. |


**Arranque fix2 T-09 — 2026-10-06:** contexto implementer normal `/root/implement_t09_benchmark` tras dos rechazos de spawn fresco por límite de threads con revisores terminales. Se registra reutilización; no se declara contexto fresco. Brief determinista exit0 más suplemento de R09-04a/b y diagnóstico sistemático antes del código/TDD. Ownership runtime/runner/tests; rootdocs/ledger/Git, no knowledge. Review2 cerrada antes fix2, estimado/null sin horas falsas. Nueva revisión será intento3de3 con tabla y rebate completos; ningún GPU/QA/CA cerrado.


**Aceptación fix2 T-09 CPU — 2026-10-06:** [Informe](testing/t09/fix2-report.md)/[recibo](testing/t09/fix2-receipt.json). Root33fuentes/32preimágenes/23artefactosSHA/tamaños; cuatroarchivoscambiadosincluyenun testnuevo,29baselineintactos. CincoRED/GREEN, suite267passed/5skipped/1GPUdeselected/1aviso23,32s, mediaoficial15producción87,45%, mínimoindividual67,96%; Ruff/formatoexit0. Diagnóstico previo probó parserchunked y sensorfuera delpresupuesto; transporte stdlibdeadlineporrawread/cierre y guardas derivadas. Contexto implementer reutilizado tras límite threads declarado. R09-04a/b entregadospendienterevisión3de3, noQA/GPU/CAcerrado ni knowledge/journal. Rebate parcialR09-07preservado.

- RED: `scripts/eval/tests/test_benchmark_deadline.py::test_deadline_bounds_real_http_parser[events-extension]` falló con `E       AssertionError: ('extension', 'events', 0.3)` · 2026-10-06T18:02:57.8906318Z (T-09fix2/red-http; GREENdirigido y suite267; fecha: run-check record).

- RED: `scripts/eval/tests/test_benchmark_deadline.py::test_sampling_budget_includes_sensor_and_global_deadline[0.5]` falló con `E           assert [0.0, 1.5, 3.0] == [0, 1, 2, 3]` · 2026-10-06T18:03:23.8703716Z (T-09fix2/red-cadence; GREENdirigido y suite267; fecha: run-check record).

- RED: `scripts/eval/tests/test_benchmark_deadline.py::test_terminal_received_after_global_deadline_is_not_accepted` falló con `E       Failed: DID NOT RAISE ObservationTimeout` · 2026-10-06T18:03:58.949890+00:00 (T-09fix2/red-late-terminal; GREENdirigido y suite267; fecha: output file modification time after command).

- RED: `scripts/eval/tests/test_benchmark_deadline.py::test_status_query_keeps_original_global_deadline` falló con `E       AssertionError: assert None == 3.0` · 2026-10-06T18:06:07.399215+00:00 (T-09fix2/red-original-deadline; GREENdirigido y suite267; fecha: output file modification time after command).

- RED: `scripts/eval/tests/test_benchmark_deadline.py::test_event_line_limit_applies_before_json_decode` falló con `E       AssertionError: assert [{'seq': 1, '...xxxxxxxxxx'}}] == []` · 2026-10-06T18:06:51.522939+00:00 (T-09fix2/red-line-limit; GREENdirigido y suite267; fecha: output file modification time after command).


## Revisión de dos lentes — intento 3: T-09 CPU — una regresión Important pendiente

[Informe](testing/t09/review3-report.md)/[recibo](testing/t09/review3-receipt.json). A+B+C+D frescas, readonly,33SHAintactos,scope0/sinavisos. A50/B50/C29+3/D27 testsCPUsolapados. Resultado0Critical/1Important/0Minor; R09-04a/b conformes, R09-08 regresiónnueva; aprobados/rebateparcialR09-07preservados. T09en-progreso/todosCAabiertos, noQA/GPU.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R09-08 | Important | Sensor que consume periodo impide consultar terminal | T-09 | pendiente | B3-01; runner123/136; sensor1,5s/intervalo1s/horizonte4s/done listo: fix1done1,51s, fix2timeout4,5s, ceroevents/status; A/D fuera de lente corroboran. |

**Decisión delegada root tras tercera revisión:** bajo instrucción vigente del propietario «implementar todo el roadmap, y toma las mejores deciciones en caso de que haya alternativas», root elige seguir con corrección concreta y una revisión adicional. No es nueva aprobación puntual; se conservan intentos1/2/3 y próxima revisión4, sin reset ni aceptación como deuda. QA/GPU mantienen puertas; el control del equipo sigue detenido trasEscape, sin capturaGPU/calibración.


**Arranque fix3 T-09 — 2026-10-06:** implementer fresco `/root/fix_t09_cpu_review3`, briefdeterministaexit0 másR09-08/diagnóstico/TDD. Ownershiprunner+test_deadline/testrunner, baseline33/preimágenes33; rootdocs/ledger/Git. Review3cerradaantesfix3(18:23:07UTC), estimado/null. Correcciónconcreta elegidaporrootbajo delegaciónvigente; contadores1/2/3preservados,siguienterevisión4. NoGPU/Docker/red/UI/knowledge; ComputerUsecontinúadetenidoporEscape, capturapanelGPUnorealizada. No CA cerrado.


**Aceptación fix3 T-09 CPU — 2026-10-06:** [Informe](testing/t09/fix3-report.md)/[recibo](testing/t09/fix3-receipt.json). Root33fuentes/33preimágenes/16artefactosSHA/tamaños; sólo runner/test_deadline cambiados,31baselineintactos. RED propio/GREEN55, suite272passed/5skip/1GPUdeselect/1warning/24.64s, mediaoficial15producción87,55%, mínimo67,96%; Ruff/formatoexit0. Sensor lento tiene oportunidad acotada de consultar mismojob y deadlinecompartido events/status; transporte intacto. R09-08 pendiente revisión4. Contadores1/2/3 preservados y continuación elegida porroot bajo delegaciónvigente. No QA/GPU/CAcerrado; ComputerUse no reiniciado.

- RED: `scripts/eval/tests/test_benchmark_deadline.py::test_slow_sensor_still_observes_ready_done[1.5]` falló con `E       benchmark_runner.ObservationTimeout: existing_job_preserved_resume_required` · 2026-10-06T18:24:25.399474+00:00 (T-09fix3/red-starvation; GREEN55 y suite272; fecha: output file modification time after command).


**Arranque revisión4 T-09 — 2026-10-06:** scope-check4exit0 sin fuera/avisos/info/exclusiones usuario; root33SHA intactos yledgerlint0/6avisosfuturos. A4/B4/C4 contextosfrescosdespachados, D4esperaplaza; packets incluyen tablas1/2/3yrebateR09-07. Fix3cerrado18:33:17UTC antesreview4, estimado/null; no reset/nuevaaprobaciónpuntual. SóloCPU, no UI/GPU/knowledge/QA todavía; T09 sigueen-progreso.


## Revisión de dos lentes — intento 4: T-09 CPU — sin gaps pendientes

[Informe](testing/t09/review4-report.md)/[recibo](testing/t09/review4-receipt.json). A+B+C+D contextosfrescos, delta2 íntegro,33SHAintactos/scope4exit0 sinavisos/info/exclusionesusuario. 0Critical/0Important/0Minor. A55/B55/C32+3/D32 testsCPUsolapados; tiempos3700s deD simulados, noRTFreal. Historia1/2/3/arbitrajeparcialR09-07 preservados. Continuaciónrootbajo delegaciónexistente, noreset/nuevaaprobaciónpuntual. QA aún pendiente, todosCA GPU abiertos, T09en-progreso.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R09-08 | Important previo | Inanición por sensor que consume periodo | T-09 | corregido CPU | A/B/D: sensor1/1,5s observa done dentrohorizonte; presupuesto compartido events/status; sensor4/5s no consulta; identidad/seq/cadencia500ms conservados |
| R09-07 | Important previo | SHA64hex dinámico sin preimagen disponible | T-09 | descartado (rebatido), subcaso preservado | Guardas/hash adapter reales; kwargs/códigosLM no reconstruibles desde receipt; camposverificables corregidos |

**Investigación T-10, sin adopción — 2026-10-06:** [candidato LoRA revisado](testing/t10/lora-candidate-screening.md), ficha oficial fijada. Restriccióncomercial/texto frente metadatos y compatibilidad/consentimiento no acreditados; root decide no incorporarlo. Sin pesos/lock/código descargado; LoRAnativo pending_prerequisite, noveredictofalse. No cambia arquitecturaaprobada ni estadoT10. TDDn/a: prosa.


**Arranque QA T-09 CPU — 2026-10-06:** agente fresco `/root/qa_t09_cpu`, privateownership `.cache/dev-cycle/t09/qa-cpu/`; fuentes33congeladas. qa: sin UI por diseño (`test-plan: n/a (sin UI)`); pytest/JUnit CPU reales, qa-gatePlaywrightn/a por exención explícita, noE2E inventado. Review4cerrada18:37:34UTC antesQA, estimado/null. NoCA/estadoM0cerrado; GPU/UI/knowledgefuera de esta auditoría.


**QA T-09 CPU — intento1/3 rojo por formato, 2026-10-06:** [Informe](testing/t09/cpu-qa1-report.md)/[recibo](testing/t09/cpu-qa1-receipt.json). Funcional272passed/5skip/1GPUdeselect/1warning23,13s, JUnit0fallos/errores, mediaoficial15módulos87,551085%;33SHAantes/después íntegros. Ruffcheck32Python0/formato1, tresfixtures cambiadasT09original, baselinepre-T09formato0; no deuda/rebatedeformato. Ledgerlint0/6avisos/coberturaE2Eexenta sinUI/qa-gatePlaywrightn/a. Freshimplementer `/root/fix_t09_qa_format` sóloformat3tests/preimágenes/ASTigual/freeze33; rootdocs/ledger. CorrecciónQA nueva, no reabreR09-08/historiarevisiones1–4; siguiente revisión5deltaformat, luegoQA2. No producción/contratos/GPU/UI/modelos/knowledge/CAcerrado. TDDn/a formato automático sincomportamientonuevo.


**Aceptación corrección formatoQA T-09 — 2026-10-06:** [Informe](testing/t09/qa-format-fix-report.md)/[recibo](testing/t09/qa-format-fix-receipt.json). Sólo3tests, ASTigual3/3, root33SHA/15artefactos verificados/30ajenosintactos; dirigidos70passed/1skip,32Ruffcheck/formato0. Nuevo deltaQA nosemántico; próximas lentesA/B revisión5, selectorC/Dfalse auto--files3, scope5exit0sinavisos. No reset historia1–4, no CA/M0cierre. TDDn/aformato automático tests existentes. Ventanamediciónabierta despuéscomandos18:42:20–21, no esfuerzo/tokens inferido.


## Revisión de dos lentes — intento 5: T-09 CPU — formato conforme, sin gaps

[Informe](testing/t09/review5-report.md)/[recibo](testing/t09/review5-receipt.json). A/Bfrescas, selectorC/Dfalseauto--files3, scope5exit0sinavisos; delta3íntegro/ASTigual3/33SHA/15artefactosconformes/30ajenosintactos. 0Critical/0Important/0Minor. Sin repetir suites;70pass/1skip son evidenciaformatterworker y272/cov87,55 previosQA1. Historia1–4/rebateR09-07 intactos, noreset. QA2siguiente, todosCA GPU abiertos/T09en-progreso; UI/knowledge fuera.


**Arranque QA T-09 CPU — intento2/3, 2026-10-06:** agente fresco `/root/qa_t09_cpu2`, privateownership `.cache/dev-cycle/t09/qa-cpu2/`, freeze33formato vigente. Review5cerrada18:47:34UTC antesQA2. Suiteposteriorformato yRuff32/checkformal/cobertura15/JUnit/freeze. SóloCPU/sinUI por diseño/E2Eexentas; no CAreal/M0cierre. Ownerreportó1,1/12GBdedicada y0,1/15,8GBcompartida sinhora; rootPDHposterior133,10/1137,91MiB yNVML1125MiB/Ollamavacío a18:45:41–43UTC. Lectura compatible alredondeo, noformalcalibración/simultaneidad/GPUspill/captura/UIcontrol.


**QA T-09 CPU — intento2/3 verde CPU, 2026-10-06:** [Informe](testing/t09/cpu-qa2-report.md)/[recibo](testing/t09/cpu-qa2-receipt.json). Nuevaúnicasuite272passed/5skip/1GPUdeselect/1warning23,17s, JUnit0fallos/errores; root33SHA/artefactos/JSONofficialverificados/media15producción87,551085%>=80. Ruffcheck32/formato32/lockJSON/freeze0, ledgerlint0/6avisos, E2Eexentas sinUI/qa-gatePlaywrightn/a. RojoQA1formatoresuelto/review5sin gaps. Siguienteimagenaislada; todosCA realesT09 siguenabiertos/T09en-progreso/M0no cerrado; ComputerUse detenido. SinGPU/UI/modelos/knowledge enauditoría.


**Imagen T-09 preparada — 2026-10-06:** [Informe](testing/t09/image-ready-report.md)/[recibo](testing/t09/image-ready-receipt.json). BuildaisladoID00c32a76,tagm0-t09-20261006-fa293f05,fuentes33intactas; primerintentorednoneapt100conservado, defaultbuild0. SondaCPUrunc/read-only/rednone/noGPU:14fuentesSHAconformes,Torch2.10cu128/torchao0.16/CUDAfalse,owncontainerexit0/removido. Servicio/taganterior intactos. Owner1,1/12dedicada y0,1/15,8compartida sinhora;PDHposterior1137,91/133,10MiBcompatiblealredondeo,noformalcalibración. QA2verdeCPU noesmatrizreal; T09/M0/CAabiertos; GUI/browser/preflight/GPU160pendientes. ComputerUse detenido trasEscape.


**Capturas T-09 autorizadas, intento pendiente — 2026-10-06:** [Informe](testing/t09/gui-capture-attempt-report.md). Owner «Sí, autoriza esas dos capturas» revoca Escape sólo para esa lectura/captura. TaskManager identificado por API soportada pero minimizado en intento y único reintento; Edge ausente de los inventarios de esa API, sin inferir proceso detenido. Cero capturas guardadas, sin activación/navegación/permisos/inferencia. Se pidió restaurar las dos ventanas; autorización vigente sin repetir pregunta. Calibración y matriz GPU pendientes, QA CPU/imagen aceptados. TDD n/a: evidencia operativa/prosa.


**Inspección PEFT T-10 — 2026-10-06:** [Informe](testing/t10/peft-loader-inspection-report.md)/[recibo](testing/t10/peft-loader-inspection-receipt.json). Imagen00c32, PEFT0.18.1; cuatrofuentes/metadatos reales sin importarPEFT/torch niGPU/modelos. Contenedorpropio runc/rednone/readonly exit0/removido. Fuente instalada admitebin/torch_load y resoluciónHub; offline noacreditaloaderseguro. LicenciaApache2oficial/local catalogada, sin pesosadoptados; seguridadLoRA siguependiente. WorkerCPU informado, T10en-progreso sincapacidadesverificadas; rootmeterúnico19:09:41UTC. TDDn/a lectura/prosa.


**Entradas originales T-10 — 2026-10-06:** [Informe](testing/t10/original-input-preparation-report.md). Siete textos privados SHA/tamaño cotejados, manifest91852a97; declaraciónassistant/es/tagscanónicos, captionbase sinBPM/key para preservar controles causales. Sin audio/GT/validacióntokens ni calidad; recetas de componentes no acreditan aislamiento, no separación estimada comoGT. Worker informado, recursos reales siguenpendientes. TDDn/a textos/procedencia.


**Captura GPU T-09 obtenida — 2026-10-06:** [Informe](testing/t09/gpu-baseline-capture-report.md)/[recibo](testing/t09/gpu-baseline-capture-receipt.json). TaskManagerGPU5070 a19:16:33.980UTC, dedicada1,3/12GB/shared0,1/15,8GB, PNG1920x1032/SHA1ecbc876/172951bytes privado. PDHposterior19:18:23–25UTC145,61MiBshared/1330–1342MiBdedicated/status0 compatible redondeo sin simultaneidad, NVML1330/Ollamavacío históricos. Edgeventana8062574inventariada, snapshot+únicoreintento falla minimizada; distintoHWNDhistórico330702, sincaptura/substitución/activación/8768. Calibraciónrepresentativa/browser/preflight/matriz160 aúnpendientes; ceroGPUinferencia. Rootactividadcaptura ocurrió durante única ventana T10CPU; no imputación individual medida ni doblecontador. TDDn/a evidencia operativa/prosa.


**Entrega CPU T-10 aceptada por root — 2026-10-06:** [Informe](testing/t10/cpu-delivery-report.md)/[recibo](testing/t10/cpu-delivery-receipt.json). Workerterminal DONE_CPU_WITH_CONCERNS;45existentes/13nuevos/71artefactos ylab cotejadosSHA/tamaño. Matriz522 con13casos/3perfiles/2superficies/3seeds/controles sinveredictos/verifiedfalse. Suite37passed2,81s/JUnit37sinfallos/mediaoficial6producción85,5084445%; Ruff/formato13exit0, CLI2passed0,48s, descriptor5passed164deselected. CLIimportbridge reescrito trasREDsubprocess, errores previospreservados/noREDporTypeErrorfixture. Incidencia.coverageraíz53248bytes/SHA153490fc registrada/copiaprivada/norestaurar sinbaseline; siguientescoverageprivados. Revisión/QA/GPU/recursos/escucha pendientes, T10en-progreso, sinflags de capacidadeshabilitados. Ventana incluyeinspecciónPEFTroot/capturasT09; estimado/null noimputaciónindividualmedida.
- RED: test_matrix_contains_all_cases_surfaces_controls_and_profiles: empty cases != 13 required cases · 2026-10-06T19:11:05.649988+00:00 · log privado `red-plan.txt`, SHA `3069d9b256d4897122dfc50a5df68e1583a39add8a7d4ff081308b97bd25ccab`.
- RED: test_signed_zero_outside_is_not_bitexact: +0/-0 wrongly declared intact · 2026-10-06T19:11:51.310541+00:00 · log privado `red-pcm.txt`, SHA `20388490ace014a7df8a18f2860c2618fa912742740543c99b3ae1bd6ddd5efd`.
- RED: test_native_success_cannot_enable_verified: native success wrongly eligible · 2026-10-06T19:11:51.700426+00:00 · log privado `red-verified.txt`, SHA `0d2bced4d8eaa08135764c2635ffbb29db33b7845ea82a62cd66c7663a92e681`.
- RED: test_retake_is_cover_with_source_overlay: text2music != cover · 2026-10-06T19:12:41.949537+00:00 · log privado `red-native-map.txt`, SHA `37740ac2b67f5f7408061f7cb141fe651e9462d2ba25d0d6e773f589593ab1cc`.
- RED: test_lora_absence_is_prerequisite_not_mock_success: missing safe resource did not reject · 2026-10-06T19:12:42.285448+00:00 · log privado `red-lora.txt`, SHA `a6922019d4a08c9b70dfadc04ecec92a20ec20a5afc8d2afc8913ebcd32ff04d`.
- RED: test_v1_rejection_is_real_422_null_audio_and_unload: planned != rejected · 2026-10-06T19:14:15.246102+00:00 · log privado `red-runtime.txt`, SHA `f35c241e676bf4e78d60cf0a0feca8014349d9e9acab8c69cc38396d86c49300`.
- RED: test_plan_cli_writes_complete_immutable_plan: return1 !=0 · 2026-10-06T19:15:33.970171+00:00 · log privado `red-cli-behavior.txt`, SHA `7bc372ce4119acac27d77721787b94cd45dbad6681708d22dc10e8151cca8a7f`.
- RED: test_native_lifecycle_uses_nvml_tuple_and_always_unloads: actual NVML tuple incompatible · 2026-10-06T19:16:40.760751+00:00 · log privado `red-nvml.txt`, SHA `3310635539f640a8be64e378cd79b4e9b85879298f109b9aee563d2660cba67e`.
- RED: test_native_boundary_records_formatted_lm_and_language: effective language missing · 2026-10-06T19:17:07.797813+00:00 · log privado `red-boundaries.txt`, SHA `d850a60f10e5c446a0dcd882c8af18791cc0b59ef800a6aebce2e0d06ca2f8aa`.
- RED: test_unsealed_upstream_cannot_load: unsealed upstream allowed load · 2026-10-06T19:17:50.327328+00:00 · log privado `red-upstream-seal.txt`, SHA `583fb1e2df725a719c45240b733728477409aed52ea250b460cb35838370341b`.
- RED: test_dit_tokenizer_rejects_truncation_before_generation: oversized prompt not rejected · 2026-10-06T19:20:49.972060+00:00 · log privado `red-dit-budget.txt`, SHA `21832e4ccfa4e05f7ced85e2205010e3979c8d111ddc95457f23d6f278f01f87`.
- RED: test_audio_requires_seal_rights_and_voice_consent: unsealed audio without rights accepted · 2026-10-06T19:21:24.262138+00:00 · log privado `red-audio-rights.txt`, SHA `c803f2524a81b26d624ab8142b4a2a1f890a644b1d7957d6c60b645263f1f2ed`.
- RED: test_stem_metrics_compare_real_ground_truth_without_verdict: exact target did not produce honest metrics · 2026-10-06T19:21:57.354488+00:00 · log privado `red-stems-metrics.txt`, SHA `2e985d864ff2ecf6f0ac72f038b40a338ef1b9461610c0618d0abc9471cb7164`.
- RED: test_timbre_without_captured_consumption_does_not_invent_noop: no-op fabricated · 2026-10-06T19:22:56.515419+00:00 · log privado `red-noop.txt`, SHA `4b9a8b3fa09fb1598cc511ecbd864d22a2f278b3b4fb8ae492aec305d15e2538`.
- RED: test_canonical_cli_subprocess_plan_and_report_original_bundle: public command returncode1 !=0; not collection ImportError, per root instruction · 2026-10-06T19:25:43.107661+00:00 · log privado `red-cli-subprocess.txt`, SHA `b284f5b1f144937543078c00ce64fbe2b5e7b797d04c12a58ddc1142d7d49e9c`.


**Dos capturas iniciales T-09 guardadas — 2026-10-06:** [Edge en blanco](testing/t09/browser-baseline-capture-report.md)/[recibo](testing/t09/browser-baseline-capture-receipt.json), además del panelGPU anterior. JPEG921×873/5069bytes/SHA40f12d76, captura19:26:32.851UTC por extensión soportada. PID6932/HWND8062574 correlacionados, página y heartbeat visibles en observaciones posteriores. Reemplaza identidad histórica6532/330702 sin cerrar aquella ventana. Fallos minimizada preservados; bytesJPEG renombrados.png→.jpg sin conversión. Sin contenido8768, activación/navegación niGPU. Calibración representativa y160jobs pendientes; no pedir al propietario que envíe capturas. TDDn/a evidencia operativa/prosa.


## Revisión de dos lentes — intento 1: Fase capacidades (T-10) — seis Important pendientes

LentesA+B frescas terminales; selectorC/Dfalseauto, scope0 sinavisos/info/exclusiones,58fuentes SHA intactas. [Informe](testing/t10/review1-report.md)/[recibo](testing/t10/review1-receipt.json). 0Critical/6Important/0Minor; arbitraje acepta6, sinrebates. A36/B6tests solapados; reprosCPU, sinGPU. QA pendiente. Jira desactivado; knowledge excluido por propietario.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R10-01 | Important | Instrucción text2music en retake/cover/repaint/extend | T-10 | pendiente | `scripts/eval/capabilities_native.py:437`; Cuatro mappings nativos conservan el default de GenerationParams en vez de su instrucción específica; AST/templates upstream y repro CPU:4/4 mismatch. |
| R10-02 | Important | Referencia timbre con raíz incorrecta en /v1 | T-10 | pendiente | `scripts/eval/capabilities_plan.py:138`; data/inputs/reference.wav se transmite intacta y el servidor busca data/data/inputs/reference.wav. Repro A con servidor CPU:422; cambiar sólo a inputs/reference.wav:200, sin iniciar hijo. |
| R10-03 | Important | Gate LoRA acepta licencia/auditoría vacías y falta de lock | T-10 | pendiente | `scripts/eval/capabilities_native.py:104`; license vacía/commercial_use null, sin models.lock, archivos auto-sellados y marker ajeno a PEFT con approved=true pasan validate_lora y pending=[]. Viola Constitución24 y diseño38/141/188. |
| R10-04 | Important | Recursos sobrescriben texto/declaración después de validar corpus | T-10 | pendiente | `scripts/eval/capabilities.py:150`; fixture.update(resources) sustituye style/lyrics/lyrics_declaration tras comprobar fixture==plan.fixture. Root repro CPU exit0 con ambos textos sobrescritos y sello original aceptado. |
| R10-05 | Important | Salidas /v1 se resuelven desde raíz del proyecto | T-10 | pendiente | `scripts/eval/capabilities_runtime.py:22`; server común339 emite tmp/<job>/output.wav relativo a data/. copy_outputs interpreta root/tmp y termina failed/output_not_raw_job aunque el job terminó done. |
| R10-06 | Important | Complete genera códigos LM que desplazan la voz fuente | T-10 | pendiente | `scripts/eval/capabilities_native.py:30`; Complete no está en skip_lm_tasks. thinking=true con LM inicializado genera códigos, y generate_music_request160–161 ignora src_audio con códigos no vacíos. Repro mapping CPU y recorrido estático fijado; no inferencia GPU. |

Complete: ✓ CPU de mapping enA se sustituye por ✗ tras recorrido efectivoB1-03; no es garantía musical. Pendiente no se convierte en nofunciona; intentos inmutables no se sobrescriben. Se mantiene matriz522/CA abiertos/descriptorfalse.


**Fix1 T-10 CPU aceptado — 2026-10-06:** [Informe](testing/t10/fix1-report.md)/[recibo](testing/t10/fix1-receipt.json). Workerterminal, ochofuentescambiadas incltestnuevo,45ajenas/13preimagesintactas;14fuentes/917artefactos/9lab SHA cotejados. 79passed5,18s/JUnit79sinfallos/mediaoficial6=89.8051%>=80, descriptor5/Ruff14/formato14/CLI522verifiedfalse. SieteREDlogs/13casos conductuales, erroresdesonda noRED; siguienteslíneas registranevidencia. Docecarpetas temporalesfueraownership porconftest dentrocacheconservadas/SHA, pluginprivadoaísla; .coverageraízintacta. R10-01..06 corregidossegúnentrega, nocerradoshasta review2; sinrebates/GPU/músicaverified/QA. T10en-progreso ymatrizíntegra.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r01_effective_generation_params_instruction falló con AssertionError: 4 instrucciones efectivas conservaron el default text2music · 2026-10-06 (R10-01); logs privados sellados en fix1/red-evidence.json.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r02_input_contract_data_relative falló con AssertionError: data/inputs/ref.wav frente inputs/ref.wav · 2026-10-06 (R10-02); logs privados sellados en fix1/red-evidence.json.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r03_unregistered_marker_is_not_audited_lora falló con Failed: DID NOT RAISE ValueError ante marker ajeno/licencia vacia/commercial_use null · 2026-10-06 (R10-03); logs privados sellados en fix1/red-evidence.json.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r04_cli_resources_cannot_override_original_text falló con AssertionError: API.calls no vacia, override llego a POST · 2026-10-06 (R10-04); logs privados sellados en fix1/red-evidence.json.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r05_contract_output_is_relative_to_data falló con ValueError: output_not_raw_job con ruta contractual tmp/job/output.wav · 2026-10-06 (R10-05); logs privados sellados en fix1/red-evidence.json.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r06_complete_initialized_lm_keeps_source falló con AssertionError: LM codes would bypass vocals source; use_lm True · 2026-10-06 (R10-06); logs privados sellados en fix1/red-evidence.json.
- RED: scripts/eval/tests/test_capabilities_fix1.py::test_r03_registered_metadata_rejected falló con Failed: DID NOT RAISE ValueError para licencia, commercial_use, revision y consent · 2026-10-06 (R10-03); logs privados sellados en fix1/red-evidence.json.


## Revisión de dos lentes — intento 2: Fase capacidades (T-10) — sin gaps CPU pendientes

LentesA+B frescasterminales; selectorautoCfalse/Dfalse14files, scope0sinavisos/info/exclusiones. [Informe](testing/t10/review2-report.md)/[recibo](testing/t10/review2-receipt.json). 0Critical/0Important/0Minor nuevos; seisImportantanteriores corregidosCPU, sinrebates/deuda/noreaperturas. A54/B47dirigidos solapados; JUnitB47SHAcotejado. 14T10+45congelados conformes. QA frescapendiente, noGPU/verifiedmúsica/T10cerrada. Jira desactivado; knowledgeexcluido.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R10-01 | Important | Instrucción text2music en retake/cover/repaint/extend | T-10 | corregido | CPU; capabilities_native.py:524; ocho instrucciones efectivas contrastadas con dispatcher upstream AST |
| R10-02 | Important | Referencia timbre con raíz incorrecta en /v1 | T-10 | corregido | CPU; capabilities_plan.py:161; input data-relative, estimate real200vs422 sin hijo |
| R10-03 | Important | Gate LoRA acepta licencia/auditoría vacías y falta de lock | T-10 | corregido | CPU; capabilities_native.py:109/139/189/219; lock/licencia/uso/auditoría/runtime/alias safetensors ypositivo privado |
| R10-04 | Important | Recursos sobrescriben texto/declaración después de validar corpus | T-10 | corregido | CPU; capabilities.py:147/159/167; override corpus bloqueado antesPOST; recursospermitidos sellados |
| R10-05 | Important | Salidas /v1 se resuelven desde raíz del proyecto | T-10 | corregido | CPU; capabilities_runtime.py:22/191; salida data-relative limitada a jobpropio/copiaSHA |
| R10-06 | Important | Complete genera códigos LM que desplazan la voz fuente | T-10 | corregido | CPU; capabilities_native.py:68/70/634; thinkingfalse/códigosvacíos/fuente consumida ycapturada; text2musicLMthinkingtrue |

QA: sinUI por diseño (`test-plan: n/a (sin UI)`), gateE2EPlaywrightn/a; ledger-lint ycoverage-check obligatorios, además suite/covoficial/Ruff/CLI. Recursos/GT/auditoríaLoRA/GPU/escucha yCA musicales abiertos.


**QA CPU T-10 intento 1 aceptado — 2026-10-06:** [Informe](testing/t10/cpu-qa1-report.md)/[recibo](testing/t10/cpu-qa1-receipt.json). QA fresco terminal, root59fuentes/318artefactos/6lab/JUnit/JSONoficial cotejados. Suiteúnica79passed7,60s/JUnit79sinfallos/media6=89.8051%>=80; descriptor5/Ruff14/formato14/CLIreal2sesiones522verifiedfalse. Ledger0/6avisos/coverage-check0sinUI/appliesfalse; gatePlaywrightn/a, nofalsoE2Everde. OriginaltestCLIintacto autorizadonuevoprefijoUUIDporroot, sininterposición/rewrites. SieteRED/13regresionesverificados; corpus/lock/.coverageraíz/freeze59intactos. QA_CPU_PASS sóloCPU; GPU/música/GT/LoRAauditado/bitexact/escucha pendientes, T10en-progreso, objetivoTODOroadmapactivo.


**Referencias T-10, candidato S1 inspeccionado — 2026-10-06:** [Informe](testing/t10/suno-stem-candidate-inspection-report.md)/[recibo](testing/t10/suno-stem-candidate-inspection-receipt.json). Búsqueda de ZIP/stems en carpeta Suno facilitada por propietario encontró material adicional a MP3. Un ZIP de otro tema, 168794837bytes/SHA89ada770, contiene7WAV etiquetados lead/backing vocals/drums/bass/guitar/keyboard/synth; cabeceras PCM16/48k/stereo/219,6000208s. Sólo headers, no decode/extract/play/GPU. Candidato de referencia/vocal trasvalidación; NOgroundtruth aprobado ni derechos/aislamiento inferidos. Recursosderivados futuros dentrorepo/lineage/SHA/FLOAT explícito. No tocaT16 ni corpusT10, pesos o motor. TDDn/a inspección/prosa.


**Preflight real T-10 intento 1 — 2026-10-06:** [Informe](testing/t10/runtime-preflight1-report.md)/[recibo](testing/t10/runtime-preflight1-receipt.json). Contenedor CPU propio imagen00c32, sin red/GPU, readonly, eliminado; 59 fuentes/lock/.coverage preservados. Fallo nuevo R10-07 Important: source_seal Windows usa backslash y consumidor Linux busca nombre literal. Error antes de factoría/upstream/modelo. QA79 y revisión2 permanecen con su alcance; fix2 TDD de portabilidad y nueva revisión del delta requeridos. Planes previos inmutables. T10 en-progreso, ningún CA musical cerrado.


**Fix2 T-10 R10-07 aceptado CPU — 2026-10-06:** [Informe](testing/t10/fix2-report.md)/[recibo](testing/t10/fix2-receipt.json). Implementer fresco terminal; root59fuentes/29artefactos/JUnit/sellos cotejados; sólo capabilities.py/test_capabilities_cli.py cambian, 57 fuentes y .coverage raíz preservados. RED: scripts/eval/tests/test_capabilities_cli.py::test_windows_source_seal_resolves_as_posix_paths fallo con AssertionError por separadores Windows en source_seal · 2026-10-06. GREEN inicial80/coberturaarchivo72,2689% insuficiente; ocho tests de custodia/guardas adicionales justifican suitefinal88passed6,01s/JUnit88sinfallos/coberturaúnicoarchivo82,3529%>=80. Ambas suites y cobertura conservadas. Ruff2/formato2exit0 con caché privada final; incidente cachéRuffcompartida inicial declarado sin reversión. Rutas fuente nuevosplanesPOSIX, anterioresinmutables. Revisión3/QA/preflightreal/GPU pendientes, T10en-progreso.


## Revisión de dos lentes — intento 3: Fase capacidades (T-10) — corrección de portabilidad CPU conforme

Lentes A+B frescas terminales; selector auto Cfalse/Dfalse sobre dosarchivos, scopeexit0sinavisos/info/exclusionesusuario. [Informe](testing/t10/review3-report.md)/[recibo](testing/t10/review3-receipt.json). 0Critical/0Important/0Minor; R10-01…06 corregidosCPU preservados, R10-07 corregidoCPU. Cada lente11dirigidos solapados; rootJUnitambos11sinfallos y freeze59verificados. NoDocker/GPU/modelos/audio ni aceptaciónmusical. QA fresca/preflightLinux pendiente.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R10-07 | Important | Plan Windows emite barras no portables | T-10 | corregido CPU | capabilities.py:97; RED/GREEN; 98/119 cobertura y pruebas POSIX/CLI reales |


**QA T-10 intento 2 y preflight real aceptados — 2026-10-06:** [Informe](testing/t10/cpu-qa2-report.md)/[recibo](testing/t10/cpu-qa2-receipt.json). QA fresca terminal; root31artefactos/freeze59/protegidos/JUnit11/sellos cotejados. CLI11/Ruff2/formato2/gatesoficialesexit0; ledger0incoherencias/6avisos/sinUI/appliesfalse, Playwrightn/a. Suite88/coberturaoficial98/119=82,352941% reutilizadas sin rerun. Preflight CPU REAL imagen00c32runc/sinred/sinGPU/readonly exit0:6fuenteslab/14imagen/436upstream exactos, fixtureidéntico, factoría/supervisorinstanciadossinload/torchausente/owncontainerremoved. Nuevo plan Windows→Linux válido, anterior intacto; R10-07 corregido y corroborado integraciónCPU. ParserprivadoJSONKeyErrorantescomandos corregido sin duplicartests/runtime. GPU/modelos/audio/GT/LoRA/escucha/verified/T10cerrada pendientes.


**T-10 primera toma native song60 GPU — 2026-10-06:** [Informe](testing/t10/native-song60-first-report.md)/[recibo](testing/t10/native-song60-first-receipt.json). Modelo cargado en hijo, casoTurbo/LM0.6/BF16/8steps/seed101/60s de matriz original; ERROR INTERNAL sinWAV, no inferenciaverde/calidad. NVMLbaseline<=1600/Ollamavacío/lockadquirido;125muestrasNVML+PDH, guardas noactivadas, calibraciónTaskMgrbajocarganoacreditada. Childalivefalse/freeRecoveredtrue/owncontainerremoved/lockreleased/Ollamaintacto;59fuentes/protegidos preservados. Usagecerrada enprivado. Causa noestablecida; diagnósticoCPUinterfacesreales requerido antesrerunGPU. T10abierta, ningúnCAcerrado.


**Diagnóstico native song60 T-10 — 2026-10-06:** [Informe](testing/t10/native-song60-diagnosis-report.md)/[recibo](testing/t10/native-song60-diagnosis-receipt.json). Implementer de diagnóstico fresco terminal, NOsourcefix; root59fuentes/29artefactos cotejados,3CPUprobes realesimagen00c32exit0/torchenCPU/CUDAsininicializar/nomodelos/GPU/ownremoved. R10-08 Important probado: wrapperdit_arguments pierdefirma; inspect.signature sóloargs/kwargs y filtroupstream descartacaptions/todosparams, TypeError real versuscontrolModelnotinitialized. DefectoconfirmadoDiT; primeraexcepciónhistóricaGPU NOdemostrada, no asumircausaúnica. Fix3TDDpreservarsignatures+regresiónfiltroreal, scopeNative/testNative. T10en-progreso/GPUretake trasfix/review/QA; ningúnCAcerrado.


**Fix3 T-10 R10-08 aceptado CPU — 2026-10-06:** [Informe](testing/t10/fix3-report.md)/[recibo](testing/t10/fix3-receipt.json). RED: test_capture_preserves_signature_filtered_captions_and_restores[False] falló con missing captions tras filtro por firma · 2026-10-06. GREEN91passed6,13s/JUnit91sinfallos; únicoarchivoproducciónnative307/346=88,7283%>=80/Ruff2formato2exit0. Root59fuentes/artefactos/sellos/JSONoficial/JUnit cotejados;2sourcechanges/57ajenosintactos/protectedpreserved. CPUinstalledgenerator control=capturadoModelnotinitialized, signaturesiguales/captionspresente/paramsconservados/restoredtrue/CUDAfalse/noGPU/nopesos/ownremoved. Wrapssólofunciones, tokenizerobjectconservado. PrimeraexcepciónhistóricaGPU aúnnoestablecida. Revisión4 mantienehistoria1–3; defecto nuevo detectadotrasGPU, noreset/no3reviewscongapsconsecutivos. QA/nuevaGPU pendientes, T10abierta.


## Revisión de dos lentes — intento 4: Fase capacidades (T-10) — firma de capturas CPU conforme

A+B frescos terminales, selectorC/Dfalse/scope0sinavisos/info/exclusiones; [informe](testing/t10/review4-report.md)/[recibo](testing/t10/review4-receipt.json). 0Critical/0Important/0Minor; R10-08corregidoCPU, R10-01…07preservados. Cada lente9dirigidos solapados/rootJUnitambos9sinfallos/freeze59cotejado; filtrotestASTidenticoaupstream salvo receptor; firmas/params/tokenizer/restauraciónconformes. NoGPU/modelos/QAfinal/aceptaciónmusical. Historia1–3intacta, nuevogapruntime posteriorreviewlimpia, noreset.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R10-08 | Important | Captura oculta firma y descarta captions | T-10 | corregido CPU | Wraps de funciones, filtro real, restauración, tokenizer, cobertura307/346 |


**QA T-10 intento 3 aceptada — 2026-10-06:** [Informe](testing/t10/cpu-qa3-report.md)/[recibo](testing/t10/cpu-qa3-receipt.json). FreshQA9dirigidos/Ruff2/formato2/gatesexit0; suite91/cov307/346=88,7283% y380artefactosfix3 cotejados, no rerunsuite. RootQAmanifest+addendum/freeze59/protegidos30/currenthelpers3SHA verificados. Concern escriturahelperprivada sustituía error corregido porrootbestEffort, v2separada9combinaciones PASS identidad/firmas/restauraciónaunOSError/FileExists; no cambiosproducción59/no9testsproducto repetidos. Configuredvsobserved sólo marcadorgeneratepruebaentrada real. QA_CPU_PASS scopeCPU, Playwrightn/a/sinUI. NuevaGPU60diagnóstica autorizada si freshbaseline<=1600; propietario autorizóuna capturaadicionalGPUbajocarga, rootúnicoUI,8768prohibido. T10abierta.


**T-10 segunda song60 GPU: audio e input efectivos — 2026-10-06:** [Informe](testing/t10/native-song60-second-report.md)/[recibo](testing/t10/native-song60-second-receipt.json). WAVreal60s/48k2/FLOAT/5.760.000muestrasfinitas/raw=copia=PCM; entradaoriginalconacentos/tags/styleexactaLM+DiT; LM198+310<=4096/DiT94<=256+120<=2048/seed101/Turbo8/BF16PT/CFG2/noCotrewrites. Actualinfer22,9289sCUDAsync sólo1call/noT09ranking. QA40/41 con1falloestrictofullscale preservado:1muestra−1. ValidadorcanónicoaudioPASAclippingsostenido1/5.760.000<0,005; no ocultarstrictfail/nocertificarclippingcero. Post canónico masterFLAC24sinormalizar/MP3−14,0005LUFS/−1,3dBTP/limitertrue/picos/rawintacto. Metadatadrivercp1252mojibake documentado; autoridadnativeUTF8intacta.126samplesNVML9747/PDHded9761,14/shared224,40/guardsnoactivadas/unloadrecovered/ownremoved/lockreleased/Ollamaintacto/freeze59protegidosintactos. CapturaTaskMgrimagenerróneanoguardada/noT09calibración, propietario panelprimerplanolisto próxima prueba. T10abierta/verifiedfalse/verdictnull/sinaceptaciónmusical.


**Nuevo R10-09 Important — preparación instrumental:** request_for ignora fixture.instrumental_style preparado/sellado y envía elcaption de canción que pidelead vocals; lyrics originales tambiénviajanenrequest envez[Instrumental] y sóloadapterloscambia. ReproducciónCPUconfixtureoriginal `.cache/dev-cycle/t10/fix4/instrumental-request-repro.json`; ningúnnuevoGPU paraeseerror. Fix4TDD centralrequestsstyleinstrumentalespecífico/lyrics[Instrumental] enambassuperficies, fuentesplan+tests/fixtures4archivos. Planes/corpus/audioanterioresinmutables. Publisherprimero guardóinforme/ledger/cerróaudioqa ypreimages; importscript fallóporrootnoenPYTHONPATH, recuperaciónseparada sin repetirescrituras/checks/audio. Revisión5posteriorconhistoria1–4preservada necesaria.


**Fix4 T-10 R10-09 aceptado CPU — 2026-10-06:** [Informe](testing/t10/fix4-report.md)/[recibo](testing/t10/fix4-receipt.json). RED: test_instrumental_request_uses_dedicated_sealed_caption_and_lyrics[turbo-v1-101] falló con AssertionError: caption de canción con lead vocals en vez del instrumental sellado · 2026-10-06; 24 RED JUnit conservados. GREEN37/suite127passed6,23s/coverage único archivo54/55=98,1818%>=80/Ruff4/formato4 conformes. Root59fuentes/376artefactos/55ajenas/preimages4/protegidos previos cotejados; un plan testCLI nuevo permitido. Implementer original ausente inventario, entrega completada por contexto fresco sin repetir suite ni fuentes. Límites: argv/exits originales no registrados, custodia histórica exhaustiva de audio no inventariada; no afirmar más. Request instrumental usa caption dedicado+[Instrumental] en ambas superficies y rechaza prerequisito malformado. Revisión5/QA4/GPU pendientes, T10abierta.


## Revisión de dos lentes — intento 5: Fase capacidades (T-10) — prompt instrumental conforme CPU

Lentes A+B frescas terminales, scope0sinavisos/info/exclusiones, selectorautoCfalseDfalse; [informe](testing/t10/review5-report.md)/[recibo](testing/t10/review5-receipt.json). 0Critical/0Important/0Minor. A37/B36dirigidos solapados, JUnit ambos verdes cotejados/rootfreeze59intacto. Aviso A cache_dir desconocido por cacheprovider desactivado conservado. R10-09 corregidoCPU; R10-01…08 preservados. Historia1–4 intacta; nuevo defecto tras pasada limpia, no reinicio. QA4/GPU/escucha pendientes, T10abierta. Jira desactivado/knowledge excluido.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R10-09 | Important | Instrumental hereda caption con voz | T-10 | corregido CPU | request_for dedicado, 18 combinaciones/6 negativos/12 otros, cobertura54/55 |


**QA T-10 intento4 aceptada — 2026-10-06:** [Informe](testing/t10/cpu-qa4-report.md)/[recibo](testing/t10/cpu-qa4-receipt.json). QA_CPU_PASS dirigido37/JUnit37sinfallos/Ruff4/formato4/ledger0incoherencias6avisos/coverage-check0sinUIappliesfalse, Playwrightn/a. Históricos127/coverageúnicoarchivo54/55=98,18% y376artefactosfix4 cotejados, no rerunsuite. Rootfreeze59/protegidos/sellos/publicdocs verificó; runner instrumental preparado sólo4reemplazos+UTF8sinsemánticaextra/helpersv2intactos, no GPU aún. R10-09 corregidoCPU corroborado. Fuentevigente qa-cpu4/sources-after59.json. Siguiente nueva toma instrumental60+capturaTaskMgr autorizada si preflightfresco<=1600. T10abierta/verifiedfalse/ningúnCAmusicalcerrado.


**T-10 native instrumental60 real aceptado técnico — 2026-10-06:** [Informe](testing/t10/native-instrumental60-report.md)/[recibo](testing/t10/native-instrumental60-receipt.json). Nueva sesión t10-native-instrumental60-839a483c9fef4ab3b8db11e1ef3838c2/job01M49HZQ7K5WFE9PA1N3WDN92K, TurboLM0.6/BF16/8steps/seed101/60s. QA48/48/JUnitverde/WAVFLOAT48k2/raw=copia=PCM/5.76Mmuestrasfinitas. Captioninstrumental EXACT LM+DiT/lyrics[Instrumental]/LM89+310/DiT90+15/noCotrewrites, fidelidad de entrada no aceptación acústica. Una muestra fullscale10,6381875s/canal1/cero>1; canónicoPASS fracción1/5760000<0.005; strictobservationfalse no gateproducto. PostFLAC24rawpreservado/MP3−14,025LUFS/−1,2dBTP/limitertrue/picos. Captura adicional autorizada del panelGPU correcto guardada: muestra1.3/12ded+0.1/15.8shared frente sensor simultáneoNVML8904/PDH8918.34+223.60MiB/delta0.214s; calibraciónT09NOvalidada/causadesconocida/noextracapturas. Hijofalse/freeRecovered/owncontainerremoved/lockreleased/Ollamaemptyconservado/freeze59yprotegidos cotejados;126samples/guardasnoactivadas. Sesión31404TERMINAL0/runner EXCLUSIVOyaejecutado no rerun. T09/T10en-progreso/verifiedfalse/aceptaciónmusicalnull/objetivoTODOroadmapactivo.


**Continuidad tras instrumental60 — 2026-10-06:** propietario informa TaskManager velocidadNormal; sólo declaración del ajuste, no valoresmanuales durantecarga ni causaestablecida. Registrado privado sin nuevaUIcaptura. Freshprepare_t10_v1_runtime inspecciona ruta/v1/recetaCPU propia/nomodelos/noGPU/fuentesreadonly, ownership privado; meter iniciado21:38:22UTC tras cerrarQAaudio. TodoM0–M5 sigueactivo, T09calibraciónpendiente, M013/20.


**T-10 preparación/v1 real CPU aceptada — 2026-10-06:** [Informe](testing/t10/v1-preparation-report.md)/[recibo](testing/t10/v1-preparation-receipt.json). ASGIrealmodels200auth/401sinToken,UIDGID10001/14imagefuentes/torchausente/sinhijo/modelos/GPU;3owncontainers eliminados/freeze59/protegidos32cotejados. Incidencias privadas mountRO/sys.path probadas y resueltas por setup/PYTHONPATH; no sourcefix/noinstall. Tresrecibosretained/hashesintermediosscript no disponibles. Reutilizar factory Python−muvicorn/cliente/harness; conservar input_receiptsJSONraw ademásWAV, no confiar sólo enlinks. SocketHTTP/GPU/v1todavíanoejecutado. Autorizaciónobjetivoexistente+preflightAGENTS cubrepróximoensayolocal, noextracapturasUI. T10abierta/calibraciónT09yaceptaciónmusicalpendientes.

**T-10 preparación HTTP de song60 entregada — 2026-10-06:** nueva sonda CPU con socket real en `.cache/dev-cycle/t10/v1-song60-next/`: REAL_FACTORY_CPU_SOCKET_PASS, autenticado200/sin-token401, UID10001 y permisos propios, sin torch/hijo/modelo/GPU; contenedor propio eliminado. Root verifica15sellos/59fuentes/32protegidos; plan522 intacto y job vacío. RunnerGPU preparado, NO ejecutado ni aprobado por QA independiente aún. Marker de preparación cerrado21:51:37UTC; fuente estimado/tokensEURhorasIAnull, no convertir duración reloj en horasIA. La sonda socket supera el límite de la evidencia ASGI anterior; no acredita guardas bajo carga, descarga real ni calidad acústica. T10 permanece en-progreso.


**QA privada /v1 song60 intento1 — 2026-10-06:** [Informe](testing/t10/v1-runner-qa1-report.md)/[recibo](testing/t10/v1-runner-qa1-receipt.json). Root74sellos/JUnit26(25PASS/1FAIL)/dossondascleanup cotejados;59fuentes32protegidos15entrega intactos. R10-V1QA-01 Important hashesLM/DiT/CFG ausentes aceptados; R10-V1QA-02 Important dobleTimeoutlogs impideOllamarestore/lease.release/receipt.save. SinGPU/main/torch/Docker/UI; no fallo musical demostrado. Runner original no ejecutado y preservado; corrección privada derivada y QA nuevas antesGPU. T10en-progreso/verifiedfalse.


**T-10 fuentes/referencias propias preparadas — 2026-10-06:** [Informe](testing/t10/own-audio-inputs-report.md)/[recibo](testing/t10/own-audio-inputs-receipt.json). Tresinputs WAVFLOAT48k2: source60s/refA30s/refB30s, derivados de tomas propiasT10 con gananciafija0.75 explícita/pico≤0.8/PCMroundtrip exacto. Padres intactos; noT16/nofuentesSunoexternas/novoiceisolation niGT. Validadorreal derechos/procedencia/sellos PASS; resources.json restringido sinfalseprerequisites. Import inicialhelperfallóantescrearinputs, corregido sólo sys.path privado. Fuentesedit/references listas técnicamente; GT/LoRA/tonal y aceptaciónmusical pendientes. NoGPU/noactualizaciónverified.


**T-10 fix privado runner/v1 intento1 — 2026-10-06:** [Informe](testing/t10/v1-runner-fix1-report.md)/[recibo](testing/t10/v1-runner-fix1-receipt.json). RED27subcasoshash/cuatroexcepcionesfuncionalescleanup sobrepreimagen; GREEN25/0fail/0error/exit0. R10-V1QA01/02 corregidosCPU: SHA64obligatorios y cierresmonitor/logs aislados, siemprecontinúarestauraciónOllama/lease/receipt y erroresmantienenexit1. Root355artefactos/JUnit25/custodia74/59/32/15 verificó. Originalrun/plan/CPUsocketpreservados, derivadoimportacommon.OUT original. Sinmain/GPU/modelos/Docker/productsource; QA2independiente pendiente antesGPU. T10continúaen-progreso.


**QA privada runner/v1 intento2 — 2026-10-07 (local):** [Informe](testing/t10/v1-runner-qa2-report.md)/[recibo](testing/t10/v1-runner-qa2-receipt.json). QA_PRIVATE_RUNNER_CPU_PASS17/17/0fail/0error; Root72artefactos/JUnit17 verificó. R10-V1QA01/02 cerradosCPU privado con27hashsubcases/finallytimeouts yreturnexit1enfallos; importreal-B sinTorch/OUToriginal. Custodia15/59/32/74/355/.coverage intactos. GPU/mainNOejecutados porQA; avanzara nueva song60/v1 traspreflight fresco yguardas, sincapturasUI. T10abierta/verifiedfalse. QA1pathsplugin públicos simbolizados; exactosoriginalesprivados conservados.


**T-10 song60 /v1 real — 2026-10-07:** [Informe](testing/t10/v1-song60-report.md)/[recibo](testing/t10/v1-song60-receipt.json). APIrealexecuted/done, rawWAV=copiaSHA y JSONinputs=copiaSHA, cincoetapasLM/DiT capturadas. TurboLM0.6/BF16PT/seed101/8steps/60s; infer22.579957sCUDAsync excluyecarga. Root151samples/fuentes59/protegidos32/originales15/plan522 verificó; guardsnoactivadas/childgone/owncontainerremoved/leasefree/VRAMrecovered/Ollamaemptyconservado. CapturasUIninguna, calibraciónT09pendiente/nospillcertification. QAaudioindependiente pendiente/verifiedfalse/T10en-progreso. Runner exclusivo YAejecutado terminal0: no repetir.


**QA song60 /v1 aceptada — 2026-10-07:** [Informe](testing/t10/v1-song60-audio-qa-report.md)/[recibo](testing/t10/v1-song60-audio-qa-receipt.json). Fresh QA21/21/JUnitexit0/13artefactos cotejados. PCMraw=copia/5.76Mmuestrasfinite/FLOAT48k2/60s/RMS−14.90318/canónicoPASS; fullscale1/>1zero/fracción1.7361e−7. Inputs exactos/capturedLM198+310/DiTresolvedcover94+lyrics120/16tokenizers+checkpointconfig+8sources contra locks/originales. PrimeraexpectativaQA defaultsinputs[] corregida conJobRequest, histórico20/21preservado; nodefectoproducto. SinGPUniUI adicional/freeze59/32/15intacto. Aceptaciónmusicalpendiente/verifiedfalse/T10en-progreso; siguiente cinco filas defaultv1 restantes, matriz522 íntegra.


**Escucha individual song60 /v1 preparada — 2026-10-07:** [Informe](testing/t10/v1-song60-audition-post-report.md)/[recibo](testing/t10/v1-song60-audition-post-receipt.json). PostcanónicoCPUlaboratorioM0host3.12/FFmpegfijado; inferenciaDocker y productopostDockerpendienteM1. MasterFLAC24sinormalizar/MP3-13.99841LUFS/-1.50dBTP/limiterFalse/peaks, WAVrawintacto. NO rendercomparativo−16lineal niGTPCM; aceptaciónmusicalnull/verifiedfalse/T10abierta. Sinmeteradicionalsolapado: orquestación dentrofaseT10actual.


**Informe canónico parcial T-10 iniciado — 2026-10-07:** `eval/results/capacidades-acestep.md` y JSON vecino: 39 filas tarea/feature×checkpoint, dos superficies; matriz522 íntegra, tres ejecuciones técnicas Turboseed101 cotejadas SHA. Comandos reales root separados del CLI planificado heredado. Verdictmusicalpending/verifiedfalse; ningún CA cerrado por informe parcial. Fuentes/GT/LoRA/key/escucha/repaint pendientes explícitos.


**Cinco defaults /v1 preparados — 2026-10-07:** [Informe](testing/t10/v1-defaults-preparation-report.md)/[recibo](testing/t10/v1-defaults-preparation-receipt.json). Root113global/16×5sellos/custodia59/32/15+fix1 cotejados, plan522 intacto; song102/103 e instrumental101/102/103, sin repetir song101. CPU socket5PASS/exit0/UID10001/models200auth+401sinToken/health401sinToken/owncontainersremoved/rawempty/sinTorch niGPU. REDselectorinstrumental+seed102/GREEN10; fallos privadosUTF8/session/probes preservados. Derivados mínimos/noGPuclaims/QA fresca pendiente/T10abierta/verifiedfalse.


**QA independiente cinco drivers /v1 aceptada — 2026-10-07:** [Informe](testing/t10/v1-defaults-runner-qa-report.md)/[recibo](testing/t10/v1-defaults-runner-qa-receipt.json). CPUQA89/89/JUnit0fails0errors0skips, Root434artefactos verificó. Guards/lifecycle/cleanupASTequivalentesfix1, seed/request/selectorpositivo-negativo; imports5intérpretesaisladossinTorch/main. Custodia113+5×16/59/32/16 conforme; fallos inicialesharnessCRLF/mockApiErrorpreservados. Próxima GPU5filassecuencialesexplicitRoot, baselinefresco≤1600/sinrerun song101/abortprimererror/noretry. T10abierta/verifiedfalse/aceptaciónmusicalnull.


**Lectura manual GPU bajo carga recibida — 2026-10-07:** [Recibo](testing/t09/owner-under-load-20261007.json). Literal «8.8 dedicada y 0.1 compartida»; unidades por contexto de pregunta, escala y hora de observación no proporcionadas. RegistroUTC22:41:29 es de root, NO hora de lectura. No se empareja con pico/muestra elegida ni se declara calibraciónT09; valor dedicado refleja subida respecto a anteriores lecturas de reposo.


**Primer default /v1 nuevo completado — 2026-10-07:** songseed102/job01M49JY83KDDC5C1YA0JPMQ5FK, exec31036 TERMINALexit0, errors[]/guardnull. Root145muestras/picoNVML9738/raw=copiaSHA+inputs/eventos/custodia59/32/16/plan522/unloadchildgone/ownremoved/leasefree/VRAMrecovered/Ollamarestaurado verificó en root-gpu-verification.json del case. AudioQA y aceptaciónmusicalpendientes; no repetir. Songseed103/job01M49JY83KW7CE93GGAHGZ4FSV iniciado exec61224 vivo a esta actualización; siguientes instrumental101/102/103 sólo tras terminal0 y verificación de cleanup. MeterGPUlote sigueabierto, no otrofase.


**Lote GPU default /v1 terminado — 2026-10-07:** [Informe](testing/t10/v1-defaults-gpu-report.md)/[recibo](testing/t10/v1-defaults-gpu-receipt.json). Cinco ejecuciones reales terminal0, errors vacíos, guard null, custodia y descarga confirmadas individualmente. Audio QA independiente siguiente; verified false, aceptación musical null, T10 sin cerrar. Owner delega continuación autónoma de TODO M0–M5 sin más lecturas manuales; máximo comunicado 9,5 GB dedicada y 0,2 GB compartida sin hora, no calibración temporal ni autorización de nuevas capturas.


**QA independiente cinco audios default /v1 aceptada — 2026-10-07:** [Informe](testing/t10/v1-defaults-audio-qa-report.md)/[recibo](testing/t10/v1-defaults-audio-qa-receipt.json). 41/41/JUnit0fails0errors0skips; root38artefactos/318freeze cotejados. Cinco PCM completos finitos, raw=copia, validatorPASS; bindings/tags/capturas/tokenbudget reales conformes. Sin GPU nueva ni escucha/ganador/cumplimiento acústico inferido. T10abierta, verifiedfalse, aceptación musicalnull.


**T09 observabilidad autónoma — diseño O1 aprobado, 2026-10-07:** [Diseño](testing/t09/autonomous-observability-design.md)/[recibo](testing/t09/autonomous-observability-design-receipt.json); [ADR-0036](../../decisiones/ADR-0036-observabilidad-wddm-autonoma.md). Root24fuentes y artefactos cotejados; el propietario delega elección y no aportará más lecturas. Puerta automáticaWDDM con estado/unidad/frescura/mapping y contraste SOLOdedicada; sharedproviderverified/independentfalse, históricoTaskMgrconflictivo intacto. Mantener requisito navegador/matriz160/preflight/cleanup/3warm. TDDn/a prosa; siguiente implementaciónTDD/review/QA/piloto reales, no CAcerrado por diseño.

**T09 observabilidad autónoma — entrega CPU aceptada, 2026-10-07:** implementer fresco terminal DONE_CPU_WITH_CONCERNS. [Informe](testing/t09/autonomous-observability-implementation-report.md)/[recibo](testing/t09/autonomous-observability-implementation-receipt.json). Root cotejó83artefactos/64fuentes/62preimágenes/56ajenasintactas y JUnit135sinfallos/errores/skips;43RED conservados. Ruff/formato8exit0; coverage.py oficial1107/1370=80,802919708%, ponderado7archivosproducción cambiados, no líneasdiff ni mínimoindividual. Runtime íntegro,8fuentesmodificadas. RecibooriginalSHA90e66936e205188551572820413ad90730725069c11d9912be6649185d0c2f49. Roothelper primero falló antesescrituras al leer REDUTF16 comoUTF8; detecciónBOMcorregida/mismosoriginales, no nuevo testfallido. Meterimpl cerradoantesreview; estimado/tokensEURhorasIAnull. Packetroot deltaoriginal209206bytes/SHA cc9e4597ce229dac50fa04a08f0269905ea5b3a63beb022f1ec85bd31997b6ca; lectura normalizada91141bytes/SHA4c3e8c1348e884eb9e195a3c9c1e02fda00503124c9081642ad2e34fadb5cc84 preserva ambos. Revisión/QA/piloto/160/canónica pendientes; ningunaCA ni rendimiento/qualidadGPU acreditados porCPU. Historial reviews1–5 anterior íntegro; la revisión siguiente pertenece a nueva subfase ADR36, sin reabrir ni resetear bugs aprobados anteriores.


## Revisión de dos lentes — intento 1: Observabilidad autónoma (T-09) y arquitectura documental (T-20) — cinco Important

[Informe](testing/t09/autonomous-observability-review1-report.md)/[recibo](testing/t09/autonomous-observability-review1-receipt.json). A+B+D frescas terminales, Cfalse/Dtrue auto;64fuentes/12docs intactos/scope0/sinavisos/info/exclusionesusuario. 0Critical/5Important/0Minor. A7tests y B/DreproduccionesCPU, no sumar a implementación ni considerar GPU. T20tresCA conformes documentales A+B, QA/cierre pendientes. Historial previo reviews1–5 preservado; nueva subfase ADR36, sin rebates ni deuda.

| ID | Grado | Tarea | Fichero:línea | Gap y escenario | Veredicto |
|---|---|---|---|---|---|
| R09-O1 (A1-01) | Important | T-09 | `scripts/eval/benchmark_observation.py:125` | La fecha general actualizada permite aceptar operaciones PDH/NVML antiguas; enlazar sustantivamente brackets y FILETIMEs a la muestra. | pendiente |
| R09-O2 (B1-01) | Important | T-09 | `scripts/eval/benchmark_observation.py:414` | Originales de otra sesión pasan al cambiar conjuntamente context y plan; ligar originales de adquisición a session/plan/source/image/lock/policy. | pendiente |
| R09-O3 (B1-02) | Important | T-09 | `scripts/eval/benchmark.py:369` | Resume valida frescura del baseline histórico antes de observar el nuevo y falla tras900s aun con continuidad fresca. | pendiente |
| R09-O4 (B1-03) | Important | T-09 | `scripts/eval/benchmark_observation.py:497` | Una acreditación nueva falla al conservar muestras anteriores a su recuperación; segmentar continuidad y acreditaciones preservando la historia. | pendiente |
| R09-O5 (D-01) | Important | T-09 | `scripts/eval/benchmark_observation.py:561` | Esperar1s además del coste de muestreo1,6s produce gap2,602s y aborta sensores válidos; respetar periodo sin sumar espera fija. | pendiente |

Siguiente: fix1 con RED propios → revisión2 de3 con traspaso completo → QA → piloto real y matriz160. No nuevas cargas mientras los gaps estén pendientes.

**T09 observabilidad fix1 CPU aceptado — 2026-10-07:** implementer fresco terminal DONE_CPU_WITH_CONCERNS. [Informe](testing/t09/autonomous-observability-fix1-report.md)/[recibo](testing/t09/autonomous-observability-fix1-receipt.json). Root84artefactos/64fuentes/64preimágenes/60ajenas/12docsintactos/.coverage raíz intacta; delta4archivos, runtime íntegro. Suite138passed/10s +suplementofinal11passed/0.55s,5solapados/6nuevoscanónicos=144únicos, NOsuite144;7logsREDpropiosaceptados. Oficial coverage.py3producción597/745=80,1342281879%; Ruff/formato4 ygateexit0. Primer79,3289%noaceptado; extracción inicial proviene transcript, no original. Dos suplementosintermedios metadata/logsobrescritosprivados, no contar/reconstruiroriginales. Comandos/logsfinalesoriginales; portablepublicreceipt elimina prefijosabsolutos sin mutar privado. RecibooriginalSHA2f8359e58fbd70822d78dc3164783fc9716c3d5e149c31ff62da19723dccf8cd. Roothelper primerfallo antesescrituras por nombremetadataRuff supuesto, corrigió a archivos entregados, sin repetir tests. Delta29196bytes/SHAb6bbec8db8d06f9520c24713b468e0fa1992841bf93ab4f5b7f8cb8a3f024081. R09-O1…O5 pendientes hasta revisión2; noGPU/QA/CAcerrado. Meterfixcierra antesreview2; historiaT09previa/T20docapproval intactas.


## Revisión de dos lentes — intento 2: Observabilidad autónoma (T-09) — un residuo Important

[Informe](testing/t09/autonomous-observability-review2-report.md)/[recibo](testing/t09/autonomous-observability-review2-receipt.json). A+B+D frescas terminales/CfalseDtrueauto/scope0/sinavisos-info-excluidosusuario/64fuentes+12docsintactos.0Critical/1Important/0Minor. Asonda+84seals/B18tests+D2testsysondasCPUsolapadas,noGPU. Aaprobaciónnominalcadena superada por reproducción secuencial específicaB. No rebates/deuda ni resetcontador; T20docaprobaciónpreservada/QApendiente.

| ID | Grado | Tarea | Corrección/veredicto | Evidencia |
|---|---|---|---|---|
| R09-O1 | Important previo | T-09 | corregido CPU | Relojes de operaciones y FILETIMEs ligados a la adquisición; control y variantes inválidas comprobados. |
| R09-O2 | Important previo | T-09 | corregido CPU | Originales/contexto previo completos; prueba de préstamo de sesión rechazada. |
| R09-O3 | Important previo | T-09 | corregido CPU | Baseline histórico preservado y nuevo baseline sólo tras health idle/loadednull. |
| R09-O4 | Important previo | T-09 | corregido CPU con residuo R09-O4a | Cadena preserva y valida segmentos; nuevo defecto de reloj histórico cuando WSL/browser siguen a Windows. |
| R09-O5 | Important previo | T-09 | corregido CPU | Muestra1,6s no suma espera fija; operación5s termina con gapmáx1,602996s. |
| R09-O4a (B2-01) | Important pendiente | T-09 | pendiente | benchmark_observation.py:585 usa finWindows+1ms para now histórico. Windows90,01/WSL90,21: muestra válida con now90,3, cadena rechazada auto_query_bracket_invalid con now90,011. |

Siguiente fix2 REDpropio con consultas secuenciales → revisión3de3 sin reabriraprobados salvo nuevaevidencia → QA → piloto/matrizreal. No cargas GPU antespuertas conformes.


### Entrega CPU Fix2 de observabilidad autónoma (T-09)

R09-O4a corregido propuesto; pendiente revisión3/QA. RED conductual auto_query_bracket_invalid conservado antes del cambio. Root verificó64fuentes/preimágenes,62ajenas,12docs y originales anteriores. Suite95/0fallos;9dirigidos previos con parametrización ampliada, no sumados. Cobertura oficial1módulo258/301=85,7143%;Ruff/formatoexit0. [Informe](testing/t09/autonomous-observability-fix2-report.md). No GPU ni cierre T-09.


## Revisión de dos lentes — intento 3: Observabilidad autónoma (T-09) — Important nuevo


Lentes A+B+D frescas, Cfalse/Dtrue por selector; scope0 y 64fuentes/12docs intactos. Resultado: **0Critical/1Important/0Minor**. Delta completo de dos archivos leído. A aprobó nominal; B encontró un caso nuevo reproducible, confirmado por root. D sin hallazgos.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| O4a consultas secuenciales con/sin historia | ✓ CPU | Diez dirigidos por lente; no sumados a suite95 |
| Guardas anteriores/custodia/TDD/constitución/alcance | ✓ preservado | 37sellos,64fuentes,12docs;coverage258/301=85,7143% |
| Futuro externo del piloto con continuidad | ✗ | B3-01 confirmado por root |
| Rendimiento del extremo máximo | ✓ CPU | Cuatro conversiones por muestra;24k→96k llamadas/0,0859424s; no RTF |
| Generated/OpenAPI | n/a | No comandos/agentes/hooks/specs en delta |
| GPU/T-09 cerrada | pendiente | Piloto/matriz160 no ejecutados |

| ID | Grado | Tarea | Corrección | Evidencia |
|---|---|---|---|---|
| R09-O4b/B3-01 | Important | T-09 | Pendiente | observation.py:612. now externo132,100;Windows131,030;WSL132,240/browser132,260;live132,000. validate_samples rechaza futuro;validate_auto usa el final futuro y acepta provider_verified. |

La aprobación nominal de A queda limitada por el escenario específico de B. No se reabre O1/O2/O3/O5 sin evidencia. O4a anterior está corregido; el nuevo gap no se transforma en deuda ni se baja de grado. El repro es sintético CPU, no adquisición real. Root conservó un original propio en review3/root-future-repro/receipt.json; su primer lanzamiento falló antes de escribir por import path, corregido sin repetir tests del agente.

Cada lente ejecutó10dirigidos propios con resultados solapados. B tuvo un error del envoltorio PowerShell después de pytestverde; freeze posterior Python salió0. D tuvo aviso de cacheprovider desactivado, sin fallos. Los revisores son de solo lectura: sus informes fueron mensajes originales, esta publicación es una síntesis del orquestador, no archivos originales producidos por los revisores.

**Decisión del orquestador al alcanzar el límite de3intentos:** continuar con una corrección acotada de este gap y una revisión excepcional explícita, bajo la delegación del propietario para decidir alternativas y finalizar autónomamente. No reiniciar el contador, no afirmar verde ni aceptar deuda. No cargar GPU antes de revisión y QA conformes. T-20 documental conserva aprobación y QA pendiente.

[Informe](testing/t09/autonomous-observability-review3-report.md)/[recibo](testing/t09/autonomous-observability-review3-receipt.json).


### Entrega CPU Fix3 de observabilidad autónoma (T-09)

B3-01 corregido propuesto: no usar completion futuro frente reloj externo, continuidad posterior al final completo. DosRED DIDNOTRAISE antes código;104suite/19dirigidos incluidos,cobertura1módulo261/304=85,8553%,Ruff/formatoexit0. Root41sellos/64fuentes/preimages/62ajenas/12docs/.coverage/históricosintactos. [Informe](testing/t09/autonomous-observability-fix3-report.md). Pendiente revisiónexcepcional4,sinreset y QA/GPU.


## Revisión de dos lentes — intento 4: Observabilidad autónoma (T-09) — excepcional


A+B+D frescas terminaron. El delta de producto de dos archivos queda conforme: **0Critical/0Important/0Minor**. El ejecutor privado preparado tiene **cuatroImportant** que bloquean el piloto. Ninguna GPU ejecutada. Scope0 y64fuentes/12docsintactos. D inició al liberarse capacidad; no se reutilizó un revisor ni se ocultó una lente ausente.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| O4b reloj externo del original | ✓ CPU | observation.py546;A9/B19dirigidos y futuros WSL/browser rechazados |
| Continuidad después del piloto completo | ✓ CPU | observation.py608;live132<finish132,26rechazado |
| Coste de validación | ✓ CPU | D9dirigidos;30originales×4conversiones=120extras,sinE/S nueva |
| Alcance/TDD/cobertura/constitución | ✓ |64fuentes/12docs;261/304=85,8553%;REDconductuales originales |
| Generated/OpenAPI | n/a |Sin delta en comandos/agentes/hooks/spec |
| Ejecutor privado de laboratorio | ✗ |B4-L01–04;cleanup ante fallos de IO |
| QA y GPU | pendiente |No cierre T-09 ni matriz160 |

| ID | Grado | Tarea | Corrección | Evidencia |
|---|---|---|---|---|
| B4-L01 | Important | T-09 laboratorio | Pendiente |Snapshot/persistencia Ollama antes try tras acquire deja lease |
| B4-L02 | Important | T-09 laboratorio | Pendiente |IO failure.json bloquea recuperación |
| B4-L03 | Important | T-09 laboratorio | Pendiente |IO container.json antes API impide cleanup contenedor propio conocido |
| B4-L04 | Important | T-09 laboratorio | Pendiente |IO cleanup.json después rm conserva estado local y reintenta recurso ausente |

B verificó estos escenarios con espejos AST selectivos y todo IO/hardware simulado, no ejecutó el script original. El control limpia/restaura/libera. No demuestra integración ni GPU. Su script original SHA bfe6ee8ff04990619a78b289b219035b865328e0de8f60d7e2bc1fec66466ca9 se conserva antes de corregir.

A9/B19/D9 tests dirigidos se solapan con104 de implementación y no se suman. A/D tuvieron aviso por cacheprovider desactivado; un envoltorio D falló con SyntaxError antes de ejecutar pytest y se corrigió. Reportes originales son mensajes de agentes solo lectura; esta publicación es una síntesis root. No nueva evaluación de calidad musical ni lecturas manuales.

El orquestador mantiene la decisión explícita excepcional tras3intentos, sin reset ni deuda. Aprobaciones O1/O2/O3/O4/O4a/O4b/O5 preservadas. Siguiente: corregir el ejecutor privado con RED propio → revisión de ese delta → QA CPU independiente (incluida documentación T-20) → piloto real → matriz160.

[Informe](testing/t09/autonomous-observability-review4-report.md).


### Entrega privada de custodia del piloto (T-09)

B4-L01–04 corregidos propuestos con4RED AssertionError antes cambio. Script real conhardware/IOmock:27pass; coverageoficialentero170/184=92,3913%;Ruff/formatoexit0. Rootsellos/64fuentes/12docs/.coverageintactos,suite tras últimocambioSHA. [Informe](testing/t09/autonomous-pilot-fix1-report.md). No GPU/prepare/run real. Reviewdeestedelta yQApendientes; aprobaciónproducto revisión4preservada.


## Revisión de dos lentes — intento 1: Piloto privado (T-09) — un Important


A+B+D frescas revisan únicamente el ejecutor privado y sus pruebas. Los cuatro defectos previos B4-L01–04 están corregidos en CPU. **Queda un Important B-L05**: al fallar Docker start con contenedor propio detenido, el GET de salud de la recuperación falla antes de llegar al cleanup existente. No se han ejecutado prepare/run reales ni GPU.

| ID | Grado | Tarea | Estado | Evidencia |
|---|---|---|---|---|
| B4-L01–04 | Important anterior | T-09 laboratorio | corregidos CPU | A11 y B16 dirigidos, solapados con27; cobertura completa170/184=92,3913% |
| B-L05 | Important | T-09 laboratorio | pendiente | autonomous-pilot-root.py:335; start falla/GET TRANSPORT_UNAVAILABLE: cleanup_calls0, contenedor detenido sin retirar y lease conservado |

La reproducción B ejecuta run() completo con el rig CPU y falla una aserción de recuperación (exit1, 00:21:49.6998616–00:21:49.9429658Z). La misma primitiva real DockerBackend.cleanup con procesos/HTTP simulados reconoce ownership y procesos muertos y retira el contenedor. A nominal no cubrió ese transporte indisponible; el caso específico B prevalece. D no detecta degradación introducida. Fuentes64 y documentos12 intactos. Los originales de revisión son mensajes de agentes de solo lectura; esta publicación es síntesis del orquestador.

Los criterios de producto O1/O2/O3/O4/O4a/O4b/O5 siguen aprobados; no se reabren sin evidencia nueva. D se despachó fresco después de A/B por capacidad, sin reutilizar contexto. QA independiente y piloto GPU siguen pendientes. No se suman tests dirigidos solapados. Incidentes instrumentales y de decodeBOM se conservan en recibo. Siguiente: RED propio para B-L05 → corrección acotada → revisión privada2 → QA CPU independiente → piloto real.

[Informe](testing/t09/autonomous-pilot-review1-report.md).


### Entrega CPU privada Fix2 de recuperación (T-09)


Corrección acotada de B-L05: la API indisponible no impide limpiar un contenedor propio cuya inspección confirma procesos muertos. Los recursos activos, ajenos o inciertos mantienen las guardas de recuperación. Fuentes de producto64 y documentos12 intactos;52 evidencias anteriores inmutables y el sello del ejecutor anterior cotejado contra la copia previa conservada. El ejecutor vivo es el único cambio deliberado de ese índice histórico53.

Suite final **32 casos**, 0 errores/fallos/skips; cobertura oficial del ejecutor completo **172/186=92.4731%**, sin exclusiones. RED conductual anterior al cambio, logs originales y metadata conservados en la carpeta privada. Ruff/formato exit0; última suite posterior al último edit. Recibo privado original conserva SHA; publicación derivada portable.

Revisión privada2 y QA independiente pendientes. No se ejecutó prepare/run real ni GPU; no se cierra T-09 ni se declara calidad musical. Producto O1–O5 y cuatro gaps privados anteriores permanecen aprobados sujeto a nueva revisión del delta.

[Informe](testing/t09/autonomous-pilot-fix2-report.md).


## Revisión de dos lentes — intento 2: Piloto privado (T-09) — conforme CPU


**A+B+D frescas: 0 Critical / 0 Important / 0 Minor.** B-L05 queda corregido en CPU: la inspección del contenedor detenido permite reutilizar cleanup con ownership y procesos muertos verificados, sin depender de una consulta HTTP imposible. Los controles de recurso activo, ajeno y estado incierto mantienen el bloqueo.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| B-L05 recuperación con transporte indisponible | ✓ CPU | autonomous-pilot-root.py:334–343; test_pilot.py:383–393 |
| Recursos activos/ajenos/inciertos | ✓ CPU | test_pilot.py:396–423; cleanup conserva assert_owner |
| Constitución/alcance/RED | ✓ | 64 fuentes y12documentos intactos; RED antes del cambio, suite32/coverage172of18692,4731% |
| Trabajo en recuperación | ✓ | Una inspección adicional fuera de bucles; sleep/cadencia no modificados |
| Producto O1–O5 y B4-L01–04 | aprobación preservada | Sin nueva evidencia que los reabra |
| QA y GPU | pendientes | Revisión CPU no cierra T-09 ni acredita matriz160 |

A ejecutó cinco casos dirigidos solapados con32; no se suman. B y D aportan sus mensajes originales en la recepción del orquestador. Por capacidad los despachos se completaron secuencialmente con contextos nuevos, sin omitir ni reutilizar lentes. Recibo derivado root; no atribuir al reviewer archivos que no escribió.

Siguiente: QA independiente de producto y ejecutor, documentación T-20 y puertas sin UI. Después, piloto real con originales nuevos y contexto previo; matriz160 sigue pendiente. No más lecturas manuales del propietario.

[Informe](testing/t09/autonomous-pilot-review2-report.md).


### QA CPU independiente de observabilidad y piloto (T-09)

**205passed (173producto+32piloto), 0fallos/skips.** Cobertura oficial7módulos1188/1439=82,5573%;2949sellos y160protegidos. qa-gateexit0 mediante conversión explícita JUnitCPU; E2En/a por marcador sinUI, no Playwright fingido. [Informe](testing/t09/autonomous-observability-qa-report.md). QACPU conforme habilita piloto real; no cierra T-09/M0/matriz160 ni evalúa calidad musical. PDF no generado por dependencias ausentes; evidenciaMD/JSON/JUnitcompleta.


### Integración real del piloto y depuración de relojes (T-09)

GPU1falló configuración antescreate;tokenexplicitporlectorCLIexisting enGPU2. GPU2arrancóAPI/imagenfuentes conformes, primera baseline rechazó observability_lost_auto_collection_timestamp_invalid. OriginalNDJSON yUTC/runexit1 preservados. Se limpiaron contenedorpropio/loadedNone yleasefree; no job/model cargado. NuevaevidenciaR09-O6 sólo relojes, mantieneaprobacionesCPUprevias; no acreditaciónGPU/matriz. Skilldebug-root-cause activada4fases, hipótesis primero, sinrelajaciónumbral/policy. GPU2metercerradoantesdebug.


### Corrección de FILETIME local y precisión temporal (T-09)

# R09-O6 — diagnóstico y corrección CPU

1. Reproducción mínima: `diagnose.py` sobre el original GPU2 `baseline.ndjson`, con su UTC histórico real `2026-10-07T00:41:20.157634+00:00`, reproduce `auto_collection_timestamp_invalid`. No modelo ni job. Original sellado en receipt; no se reescribe ni se recalifica.
2. Aislamiento: query/raw local FILETIME `134358144800888324` representa `2026-10-07T02:41:20.0888324` local; colección UTC `00:41:20.088832` produce diferencia exacta `7200.0000004 s`. Float grande añade `233075/512 ns` (455,224609375 ns). El reloj preciso tampoco encierra la consulta normalizada: sus cinco pruebas fallan porque PDH conserva ticks gruesos anteriores. Quedan descartados status/escala/LUID y cualquier supuesto de carga de modelo como causa de este fallo de reloj.
3. Hipótesis literal probada: «Falla porque se compara FILETIME local de PDH como si fuera UTC, y la fracción nativa de 100 ns se pierde entre datetime de microsegundos y la conversión float de época.» `coarse-proof.py` conserva cinco muestras reales: `GetSystemTimeAsFileTime` + conversión nativa `LocalFileTimeToFileTime` encierra 5/5 consultas, incluso con intervalos UTC de cero ticks. Diferencia local→UTC nativa de 72000000000 ticks observada; no constante del producto. Total sensores WindowsGpuMemory=10, ninguna lectura adicional tras el fix.
4. Fix aplicado tras RED: emisor UTC compartido de siete dígitos desde el mismo reloj nativo observado; aritmética racional exacta en parseo/FILETIME/comparaciones y límites externos/históricos; raw local conservado, UTC nativo añadido por adquisición; zona/DST completa antes/después, coherencia del bias y de cada conversión, fallo cerrado ante API/cambio/discrepancia o metadata ausente. El validador consume la conversión sellada y no usa la zona actual para históricos. Umbrales y hash O1 intactos. El descubrimiento dinámico existente ya sella el módulo nuevo: prueba de hash real + rechazo de cambio, sin alterar benchmark_plan.py.

RED: nueve tests individuales reales, argv/UTC/exit1/salida original y render UTF8 explícito en receipt. No rojos por import/setup ni pruebas vacías. Incluyen precisión/bracket, emisor nativo, conversión local, zona/DST, ausencia de metadata, now implícito y parser que antes descartaba fracción con formatos no canónicos. Tests adicionales prueban UTC, offsets positivos/negativos/+05:30, DST estándar/verano, errores API, cambio de zona, manipulación query/raw-normalizado, histórico/replay/futuro y fuente sellada.

Verificación final: `207 passed in 14.07s`; cobertura oficial de todos los módulos de producción cambiados: **599/665=90,0751879699 %**, ponderada por líneas/statement oficiales, no líneas del diff. Ruff `All checks passed!`; formato `7 files already formatted`; exits0. JUnit y coverage JSON originales. Baseline64→actual66: cinco fuentes previas cambiadas + dos nuevas; 59 ajenas, 64 preimágenes y 12 documentos protegidos intactos. `.coverage` raíz preservada SHA153490fc…; nada de ledger/Git/docs/locks.

Limitaciones: siete dígitos conservan representación; no prometen resolución física100ns. API de conversión usa zona/DST actuales y sólo se llama durante adquisición; no resuelve arbitrariamente timestamps históricos ni horas repetidas fuera del bracket contemporáneo. Final CPU no acredita GPU/calibración/respuesta512MiB/cero spill ni binding browser. Hace falta plan y originales nuevos después de revisión y QA, sin modificar los del piloto fallido. Memoria/gotcha omitidos por alcance explícito de root y escritor separado; no conocimiento leído/escrito.

Incidentes preservados: wrappers RED convert/zone imprimieron UnicodeEncodeError después de guardar salida/exits reales de pytest (cp1252); receipt distingue original y render UTF8. Test suplementario de sellado corrigió fixture bajo `.cache` que la regla existente excluye; no se contó como RED. Ruff inicial tuvo un import fuera de orden y fue corregido. Primera suite204 verde antes del último fix de parser; entrega final207.

DONE_CPU_READY_FOR_REVIEW


Fuentes oficiales: [PDH_RAW_COUNTER: FILETIME local](https://learn.microsoft.com/en-us/windows/win32/api/pdh/ns-pdh-pdh_raw_counter), [conversión local a UTC y límite de zona actual](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-localfiletimetofiletime). La implementación aplica la conversión durante adquisición; nunca recalcula originales históricos.

[Informe](testing/t09/autonomous-clock-debug-report.md). Revisión y QA pendientes; T-09/M0 siguen abiertos.


## Revisión de dos lentes — intento 5: Observabilidad relojes (T-09) — 1 Important

# Revisión de dos lentes — observabilidad, intento5 (clock1)

Lentes A+B+D frescas: **0 Critical / 1 Important / 0 Minor**. A conforme con alcance, constitución, TDD y documentación. B detecta B-clock-01: StandardBias se usa cuando StandardDate no tiene mes; Windows ignora ese campo. Reproducción CPU legítima sinDST rechazada con auto_filetime_conversion_invalid. D no detecta regresión material; validación histórica lineal fuera del tick y reinicio de previous_sample conservado.

| Hallazgo | Grado | Evidencia | Decisión |
|---|---|---|---|
| B-clock-01: ajuste horario ignorado aplicado | Important | benchmark_clock.py:119; JUnit independiente1failed; control45passed | Corregir con RED propio antes de QA/GPU |
| Requisitos/precisión/conversión/históricos | Conforme CPU | A34 dirigidos, B45 dirigidos; solapados, no sumarlos | Mantener aprobaciones salvo este caso nuevo |
| Coste de validación | Conforme | D28 dirigidos y sonda24.059samples3,974s fuera del tick | No microoptimización ni cambio de cadencia |

Sesenta y seis fuentes y doce documentos intactos. Contextos nuevos despachados secuencialmente por límite real de threads; ningún revisor reutilizado. La historia previa no se resetea: este seguimiento5 corresponde al nuevo fallo realR09-O6; clock1 es sólo la identificación del delta. Root continúa la corrección acotada bajo delegación explícita del propietario. Sin deuda, umbrales relajados, acreditación GPU o cierre M0.

Semántica oficial: [TIME_ZONE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/timezoneapi/ns-timezoneapi-time_zone_information) indica que StandardBias y DaylightBias se ignoran cuando no están sus respectivas fechas. La revisión reproduce el caso sin cambiar la configuración del equipo.



### Ajustes de zona sin fecha de transición (T-09)

RED: scripts/eval/tests/test_benchmark_clock.py::test_timezone_offset_ignores_seasonal_bias_without_its_transition_date[0-0-0-0-0] falló con AssertionError (-36000000000 != 0) · 2026-10-07T01:07:23.474534+00:00

GREEN8 dirigidos; suitefinal215passed/covoficialhelpercompleto47/49=95,9184%/Ruff-formato0. Primerasuite214+1falló por fixtureDSTsinfechasválidas; originalesconservados, alinear fixture autorizado antes repetir suite por nuevaedición. Fuentes66/preimages66/docs12/rootcoverage intactos,62ajenas. [Entrega](testing/t09/autonomous-clock-fix1-report.md). Revisión/QA/GPU pendientes, sin cierre de tarea.


## Revisión de dos lentes — intento 6: Observabilidad relojes (T-09) — conforme CPU

# Revisión de dos lentes — intento6, relojes clock2

**A+B frescas conformes: 0 Critical / 0 Important / 0 Minor.** B-clock-01 queda corregido: el ajuste de temporada sólo se aplica cuando existe su fecha. Los fixtures ahora representan fechas DST reales. Los controles de representación, conversión nativa, API, contexto, frescura, históricos y cadencia permanecen aprobados.

A y B ejecutaron ocho regresiones cada una, solapadas; no se cuentan como dieciséis únicas. B añadió control de324combinaciones y nueve entradas inválidas. Fuentes66 y documentos12 intactos; JUnit originales cotejados. Selector C=false/D=false; D anterior conserva su aprobación porque este delta constante no lo activa. Despachos secuenciales por capacidad, ambos contextos nuevos.

Revisión global6, clockdelta2: el número local identifica la corrección del nuevo fallo realR09-O6 y no borra la historia1–5. QA independiente y piloto real pendientes. Sin cierre T-09/M0 ni acreditación GPU o musical.



### QA independiente de relojes (T-09)

247passed=215producto+32piloto/0errores-skips; covoficial8módulos1277/1526=83,6828%;191protegidos intactos. Ruff/formato/ledger0/qa-gate0 por adaptadorJUnit→statsCPU explícito, noPlaywright/E2E. T20carryforward12docs/156linkschecksums, sinreruns ni Dockerfuturoacreditado. [Informe](testing/t09/autonomous-clock-qa-report.md). QA habilita pilotoreal3nuevo; T-09/M0/matriz160abiertos.


### Piloto GPU3 y continuidad de llamadas (T-09)

GPU3 terminalexit1 a01:24:56UTC. Diez muestras baseline conformes; estimacion real interrumpio cadencia15,6891821s antes del POSTjobs. Rechazo auto_replayed_or_paused_sample correcto; sin accepted/job/model. Contenedor propio eliminado/unloaded y lease liberado. R09-O7 reabre solo llamadas bloqueantes; aprobacion clocks/QA247 intacta. Debug sistematico + TDD, sin subir umbrales ni reutilizar pilotos fallidos. MedidorGPU3 cerrado antes de debug.


### Correccion de estimacion y reanudacion observadas (T-09)

RED: slow_estimate y slow_resume reprodujeron auto_replayed_or_paused_sample antes del cambio; originales01:27:10/14UTC en entrega. GREEN2; controles14; suitefinal229pass/covrunner228/265=86,0377%; privado32pass (fuente y tests intactos), Ruff/formato0. Primera suite224/cov197/265 conservada; nuevos controles relevantes justifican suitefinal. Baseline66 a67,65ajenos/66preimagenes/doc12/piloto3original27/rootcoverage intactos. Dos llamadas ahora usan monitor existente; sin cambiar policy/clock. Riesgo heredado de espera de hilo bajo perdida de observacion pasa a B. [Entrega](testing/t09/autonomous-cadence-debug-report.md). Revision/QA/GPU nuevas pendientes; M0 abierto.


## Revisión de dos lentes — intento 7: T-09, continuidad R09-O7 sin gaps

A+B+D0gaps/Cfalse/Dtrue por sleep197preexistente. Tres contextos CLI nuevos, paqueteinlineexacto sin comandos/tests ni hash live por revisores; root67sources/doc12intactos. PrimerCLI A sinlecturas no aprobado; fallbackporcapacidad colaboración, permisosreadonly sinrelajar. Hiloespera70s preocupaciónheredada, no nuevohallazgo. Dictamenes1-6/rebates intactos; nocontextoimplementerreusado. [Informe](testing/t09/autonomous-cadence-review1-report.md). QA/GPU/matriz160 pendientes.


### QA independiente de continuidad R09-O7 (T-09)

CPU261=229producto+32privado,0errores/skips/flaky/interrupted. Cobertura8modulos1320/1526=86,5007%sinexclusiones;194protegidos67fuentes12docsintactos. FreshCLIQAporcapacidad, modofullaccessyaautorizado, escriturasprivadassolamente, noGPU. PublicacionharnessJSONDecodeError recuperada sin repetirtests. Rootcorrigioheadercanon y ejecuto detectiondiffrealGitRO trasNoGitoverbroad: coverage-check n/a sin degradacion, ledger0/7avisosfuturos. [Informe](testing/t09/autonomous-cadence-qa-report.md). QA habilita piloto4 NUEVO; no cierreM0/T09/calidad/matriz.


### Audio real y guarda de contrato del piloto (T-09)

GPU4 produjo realDONE31/WAV60sFLOAT48k2/PCMfinitohash98d0ccfd, load100,334s/infer22,448s/RTF0,37414. Guardprivadoexigiaexecuted=True, campoausente deDoneData115: fallo pilot_job_not_done DESPUESaudio, antesloaded/unloaded10. Noacreditarcalibracion ni matriz; artefactosrealtecnicos preservados. Contenedorremovedunloaded/leasefree. NuevoR09-P3 soloorquestadorprivado; fuentesproducto67/QA261/reviews1-7 intactas. FixnuevoVersion2 sin sobrescribir originalcbe68, TDD+review+QAprivados. GPU4meter cerrado antesfix.


### Fix privado de contrato del piloto (T-09)

RED: typed_actual_done_without_flag falló pilot_job_not_done antesfix01:53:10UTC. Event/DoneData validó terminalGPU4 sin campoexecuted; v2retira sólo exigenciainventada. GREEN1/suite35=32controles+3nuevos, cov173/186=93,01075%/RufftargetPythonreal312/formato0. Version1cbe68/GPU4audio+eventos/prod67/doc12/227protegidosintactos. Primerimportfalló noRED; REDscratchnuevo dentrocachepero fueraphase preservado y alcanceposteriorconfinado, rootaceptaretención del temporal propio. [Entrega](testing/t09/private-pilot-contract-fix-report.md). Reviewprivate3/QA/GPU5 NUEVOS pendientes; sourceproducto no cambió/no rerun229.


### Revisión privada de contrato R09-P3 — intento 3

A+B+D: cero gaps nuevos. Suplemento mismo intento incluye implementación validate_events, plan completo y fixture done original. Precisión: validate_events valida secuencia/identidad/terminal, no cuerpo tipado; fixture sí validado con Event. Retirar executed no altera guardas físicas. Revisión estática sin tests propios; root custodia de fuentes/originales. Historial privado1/2 y producto1–7 preservado. [Informe](testing/t09/private-pilot-contract-review3-report.md). Pendiente QA35 independiente y piloto5 nuevo; T09/M0 abiertos.


### QA independiente privada R09-P3 (T-09)

35pass/0fallos/errors/skips, cobertura completa173/186=93,01%sinexclusiones;310protegidos67fuentes12docsintactos. Ruff/formato py312 y gateCPU conformes. Harness QA omitió argv obligatorio coverage-check: original FAIL conservado, root ejecuta solamente puerta corregida exit0/sinUI/nodegradado. No rerunCPU. [Informe](testing/t09/private-pilot-contract-qa-report.md). Habilita piloto5 nuevo con v2 aprobado, no calibración ni cierre porCPU.


### Piloto GPU autonomo acreditado (T-09)

NuevoGPU4 terminaldoneconformecontrato/instrumental60FLOAT48k2/PCMfinito+hashválido; baseline/loaded/unloaded10muestrascada+30originales/contextonuevo. Lifecycleloaded/unloaded y cleanupremovedunloadedtrue/leasefree/NVMLreposo<=1600. R09-O7 estimacionobservada conformeenGPU. SharedproviderverifiedNOindependiente/cero spill; no calidad niwinner. [Informe](testing/t09/autonomous-pilot5-report.md). Matriz160 pendiente conplanEXACTO.

## Revisión de dos lentes — intento 1: T-09 transición WDDM

[Informe](testing/t09/transition-review1-report.md). A/B/D frescas, C no seleccionada; scope0sinavisos/exclusiones y fuentes8 intactas. DosImportant corroborados R09-T01 (consulta no interrumpida/plazo y persistencia final) y R09-T02 (preparación3s sin observación). Pendientes de corrección, ceroCritical/Minor, sin rebates ni cambio de umbral. Revisiones anteriores1–7 de otros fixes conservadas. T09 en-progreso; GPU/QA gated.


## T-09 transición: entrega parcial fix2 y continuación aislada

[Informe](testing/t09/transition-fix2-partial-report.md): dos regresiones nativas RAW verdes, 300 vecinos verdes, cinco RED de los defectos principales todavía fallan. RED: proceso bloqueado2,252s; validación/publicación/continuidad2,205s aceptadas tarde; preparación3s aborta por cadencia · 2026-10-07. No suite global verde ni revisión2/QA/GPU habilitadas. Custodia root71protegidos/22preimágenes/originales verificados. R09-T01/R09-T02 siguen abiertos. Se continúa ADR0042 en una unidad concreta: proveedor persistente aislado/JobObject con pruebas CPU Windows reales; integración y publicación v3 siguen después. Estado T09 en-progreso; contador de revisión sin reset.


**T09 proceso aislado entregado — 2026-10-07:** [Unidad](testing/t09/isolated-provider-unit-report.md):49CPUWindows/nativePDH, cobertura4módulos655/756sinexclusiones, cleanupJob vacío/lectorunido/propiosmuertos/ajeno preservado. Rootcustodiafuentes/copias/originales/protegidos. GapTDDprovider(test después) reconocido: freshimplementerretirará implementación/REDfuncional/reescritura antes de integrar publicaciónv3. No QA/GPU ni R09-T01/R09-T02 cerrados; coordinadorcontinuo sigue después. Suplementoproporcionalestimado3 agregadoactual.


**T09 unidad publicación v3 entregada — 2026-10-07:** [Informe](testing/t09/publication-v3-unit-report.md): root4fuentes/copias/169originales/81protegidos/JUnit384, cobertura3módulos completos≥80%sinexclusiones. CincoREDv2 históricos excluidos explícitos. Corrección TDDprovider retirado→REDfuncional→reescritura. Jobvacío/lectorunido/siete bloqueos reales≈1,75–1,77s; ninguna inferencia/calibraciónGPU. Primer sello de log vivo falló y se preserva inventario corregido posterior. Coordinadorfresh ACTIVO exec76717, una supervisión continua e integraciónCLI/runner/evidence/planv3; R09-T01/R09-T02 abiertos y próximo intento2/3 másQA antesGPU. No cierreT09 ni aceptación artística.


**T09 adaptador v3 entregado — 2026-10-07:** [Unidad](testing/t09/v3-calibration-unit-report.md):257CPU/12deselect explícitos, cobertura2módulos89,61%/86,52%sinexclusiones. Rootfuentes/copia/frozenproduction/originales/cleanupJob3episodios conformes; no GPUcalibración. REDanteriorcódigo preservado, UTC/exitindividualoriginal no inventados, replayposteriorseparado. Manifestrootinicialrecalculadoporworker yprimerCLIseal vivo fallido conservados; basespreviascríticas verificadasseparadamente. IntegracióncoordinatorACTIVA/review2+QA pendientes; T09abierta.


## Revisión de dos lentes — intento 1: T11 — corrección CPU pendiente

[Informe](testing/t11/review1-report.md). A/B/D,selectorCfalseDtrue,0Critical5Important1Minor,lecturaestática. T11continúaen-progreso, sinQA/GPU/quality.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R11-01 | Important | Códigos ULID filtran orden temporal de las tomas. | T-11 | pendiente reproducción | A1,`run.py:628` |
| R11-02 | Important | Al filtrar tomas no listas, agrupar cada tres mezcla briefs diferentes. | T-11 | pendiente reproducción | A2/B1,`run.py:708` |
| R11-03 | Important | Suelo WER positivo acepta audio inválido y procedencia/cobertura autodeclaradas sin ejecución acreditada. | T-11 | pendiente reproducción | A3/B2,`metrics.py:283` |
| R11-04 | Important | CLAPnull o Audiobox no numérico levanta TypeError no aislado y aborta toda batería. | T-11 | pendiente reproducción | B3,`metrics.py:339;run.py:452` |
| R11-05 | Important | Stream continuo de eventos no terminales no revisa plazo global dentro del iterador. | T-11 | pendiente reproducción | B4,`run.py:281` |
| R11-06 | Minor | Repite lecturaZIP/binario y-version deFFmpeg por cada normalización. No bloquea por sí solo. | T-11 | pendiente reproducción | D1,`metrics.py:219` |


## Revisión de dos lentes — intento 2: T09 transición — cinco Important nuevos

[Informe](testing/t09/transition-review2-report.md). A/B/D, CfalseDtrue,0Critical5Important0Minor. R09-T01/T02corregidosestáticamente pendientesQA. TodosIDs/historial/limpiezahistóricadesconocida conservados.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R09-T03 | Important | ObservationTimeout elimina contenedor que comunica conservar/query_same_job. | T-09 | pendiente reproducción | A-03,`benchmark.py:428;benchmark_runtime.py:1099` |
| R09-T04 | Important | Fallo sampler durante shutdown puede publicar complete=true y exit0. | T-09 | pendiente reproducción | A-04/B-03,`benchmark.py:443,455,1247` |
| R09-T05 | Important | Snapshot entre publicación de custodia y registro contiene recibo sin muestra, v3_audit_summary_mismatch. | T-09 | pendiente reproducción | B-01,`benchmark_coordinator.py:145,146,410` |
| R09-T06 | Important | finished_session pasa observed_utc str como now al validador que exige datetime/Fraction; AttributeError en relectura legítima. | T-09 | pendiente reproducción | B-02,`benchmark.py:1125` |
| R09-T07 | Important | Auditoría transmite historial completo repetidamente;48000episodios superan64Mi caracteres y cada60Mi demanda≈52429RPC. | T-09 | pendiente reproducción | D-03,`benchmark_coordinator.py:409,426;benchmark_runtime.py:830` |


**T11 fix1 custodiado — 2026-10-07:** [Informe](testing/t11/fix1-report.md).126CPUpass/cobertura90,17%y98,42%completa0exclusiones/Ruff0/format0. Cincofuentes y1112originales intactos. R11-01..05candidatos, revisión2/QApendientes; R11-06Minor abierto. No30canciones/GT/sueloWER/escucha/cierreT11.


## Revisión de dos lentes — intento 2: T11 — un Important nuevo

[Informe](testing/t11/review2-report.md). A/B/Dfrescos0C1I1Minor;root5fuentes/paquetes verificados. R11-01..05corregidosestáticamente, R11-06Minorpendiente, R11-07timeout1sconjobválido pendienteRED/corrección. Próxima revisión3finalregular,sinreset; QA/T11/M0pendientes.

**T09 adjudicación — 2026-10-07:** ADR-0045aceptada bajo delegación vigente: recuperación propia con disposición durable honesta tras timeout y transporte wddm_audit_delta_v1 sin cambiar política v3 ni límites. Primera corrección parcialR09-T04/05/06 custodiada;R03REDexpectativahistórica de conservar recurso incompatible con nueva decisión conservada intacta/declarada, NEWtestsdepolítica requeridos. R07volumen sintético184MBNOcadena48000válida/no13h. Continuación fresca privada, revisión3/QA/GPUpendientes. No nuevas anclas históricas recapturadas.


**T11fix2 custodiado — 2026-10-07:** [Informe](testing/t11/fix2-report.md).130CPUpass,run439/48390,89%metrics187/19098,42%whole0excl/Ruff0/format0;6fuentes/4protegidos. REDnativoquiet2santesproducto, GETreattachcursor,noPOSTduplicate/successcancel. SelloCLIprematurooriginalinválidoconservado/rootterminalhashnuevo,norewrite. R11-07candidatocorregido,R11-06Minorpendiente,revisión3finalregular/QA/T11M0pendientes.


## Revisión de dos lentes — intento 3: T11 — sin Important pendientes

[Informe](testing/t11/review3-report.md). A/B/Dfrescos0C0I1Minorprevio,root6fuentes/paquetes verificados. R11-07corregidoestático;R11-01..05conservados,R11-06Minorpending. Contador3sinreset; QAunidadCPU siguiente, T11full/M0/GPU/GT/30tomaspendientes.


**T11 unidad CPU aceptada técnicamente — 2026-10-07:** [QA3 independiente](testing/t11/qa-cpu3-report.md).130casosdistinctospass,4sondasextra+1symlinkWindowsprivilegeskip,wholecurrentrun90,89%/metrics98,42%0excl/Ruffformat0/unitqa-gate0. Root6fuentes/1134nonCLI/1397originales/CLIterminal0verificados. Dry30slots/comandocompletoexit2ANTESHTTP. Revisión3A/B/D0Critical0Important1Minor(R11-06pendiente). T11continúaen-progreso:letrasderechoscorpusGT/sueloWER/30tomasGPU/escuchanoaceptados,nil quality/winner/closure. Esta dependenciaCPUyautilizable bajoADR0037, ningún modelo aprobado por métricasmock.


**T09 entrega parcial y diagnóstico — 2026-10-07:** [custodia](testing/t09/adjudicated-fix-report.md) y [causa raíz phases1–3](testing/t09/legacy-transition-diagnosis3-report.md). TimeoutCLI90minexitNULL/historicalcleanupUNKNOWN; finisherfrescoterminal0, root53.218originales/21fuentes/6cambiadas/700asserts/37positivos/COVwhole4≥83,66%0exclusiones. CPU6real469pass6fail5sensoresdeselectedexplicit. CincoREDtécnicosV2vivosporinyecciónPython/noCLI normal; sextocontradicciónADR45. Sinverdeamplio niresetcontador. Deltatransporte acotado pero validaciónprefixnuevoO(historia), sin48.000episodioscanónicos niGPU13h. Revisión3regularfinal siguiente; QA/GPU/160/T09/M0pendientes.


## Revisión de dos lentes — intento 3: T09 transición — seis Important

[Informe](testing/t09/transition-review3-report.md). A/B/Dfrescos21fuentes0Critical6Important0Minor fusionados R09-T08..13; veredictos previos íntegros. Máximo regular3 alcanzado, raíz continúa corrección por autorización autónoma explícita del propietario, sin reset/aceptardeuda; siguiente revisión4 visible. REDdirigidos antesfix, diseño de crecimiento/renovación; CPU6realrojo y timeoutoriginalpreservados. QA/GPU/160/T09/M0pendientes.


**Diseño de crecimiento elegido — 2026-10-07:** raíz custodia16fuentes congeladas y29artefactos del arquitecto terminal0; eligeO2 según[ADR0046](../../decisiones/ADR-0046-capsulas-canonicas-y-auditoria-incremental.md): originales en cápsulas propias protegidas como autoridad online, referencias acotadas y FINAL completo independiente. R09-T10/T13 no corregidos todavía. Boundaryfix T08/T09/T11/T12 activo; migraciónlegacy separada con originales preservados. Siguiente revisión4 sinreset; GPU/160/QA/T09/M0 abiertos.


**Corrección de fronteras custodiada — 2026-10-07:** [Unidad](testing/t09/boundary-fix-report.md) terminal0/custodia raíz;118PASS en freeze previo y78PASS en selección final. Cinco coberturas whole18,29–70,63%/0exclusiones: gate80% NOcumplido, unidad NOaceptada. Se permite continuación correctiva de la misma tarea segúnADR37/46, no GPU: canonical-growth-unit exec48742 implementaR09-T10/T13. Después migraciónlegacy/cobertura completa/revisión4 sinreset/QA.


**Adjudicación de crecimiento — rebate con evidencia, sin intento nuevo — 2026-10-07:** [Prueba canónica](testing/t09/growth-functional-probe-report.md). R09-T10/B3-01 **descartado (rebatido)**: runtime:1099–1111 envía seal, no arrays;130episodios323.202bytes, dosresponses21.138/prereqs21.694PASS. T13sigueRED70/140relecturas antiguas paraN10/20. No producción implementada; nextactor recibe contexto corregido y conserva regresión positiva acotada. BindingREDinterno no bypassRPCprobado. Revisión4 sinreset/QA/cobertura80/migraciónlegacy/GPU pendientes.


## Continuación autónoma — 2026-10-07T21:28:09.340481+00:00

T09 canonical-growth-continuation1 terminal0/root custodia: runtime+testgrowth sólo binding interno. RED funcional de binding corregido; final109PASS/2T13FAIL,139/72019,31%0exclusiones. T13 relecturas70/140 persiste. O2 no implementado. Próxima unidad de custodia nativa no acredita integración/cierre; revisión4 formal posterior sin reset.


## Inspección temprana del componente de custodia — intento1, previa a revisión formal4

Dos nuevas fuentes/cápsulas individuales,59PASS1skip/315of334líneas+93of104ramas93,15%combinada0exclusiones. Fixture corregida sin cambiar59tests/producto, fase previa sellada intacta. A0gaps; B1Important CUST-B01: slot del guard reutilizado, close cierrahandle ajeno y descarta principal propio. Reproducción nativa readonly confirmada; corrección TDD pendiente. No aceptación de componente/T09; revisión formal4 conjunta tras integración sigue pendiente, sin reset de revisión3. Incidente29dirs vacíos fuera del ownership en cache repo conservado, no plena conformidad operacional.


## Continuación autónoma — 2026-10-07T22:21:32.394161+00:00

CUST-B01 corrección entregada: RED nativo reutilización real guard/foreign-samefile antes código; witness protegido y quarantine explícita conserva referencias.92PASS1skip histórico,352/370sentencias+106/118ramas cobertura93,85% cero exclusiones. Fuentes originales/pruebas AST preservadas, inspección2 A/B y QA independientes pendientes. No aceptación ni T13/packs/FINAL/integración; próxima revisión formal4 sin reset.


## Inspección temprana del componente de custodia — intento2, previa a revisión formal4

Lentes frescas A+B0Critical/0Important/0Minor sobre dos fuentes completas selladas: CUST-B01 corregido dentro del alcance nativo declarado. Lectura estática por ambos revisores, sin probes propios; no sumar ejecuciones. QA nativa independiente siguiente. Unknown_quarantined exige integración failclosed y terminación sólo del worker propio antes de afirmar recursos devueltos. No aceptación/T13/integración/GPU/cierre; revisión formal integrada4 preservada.


## QA nativa independiente — dependencia de custodia individual

Root acepta únicamente componente técnico Windows:92PASS1skip histórico/JUnit93 sin fallos, cobertura whole352/370sentencias+106/118ramas93,85% ceroexclusiones, Ruff/formato0. Tres sondas nativas adicionales byte-golden/handles propios cerrados/controles ajenos al store sobreviven; archivos privados completos y fuentes protegidas exactas. Unknown_quarantined conserva referencias y requiere integración de terminación del worker propio, no recursos retornados. NoT13/packs/FINAL/runtime/GPU/UI/matriz160/Git/cierreT09. Próxima unidad: semántica compartida de un intento y estado canónico incremental, antes de integrar callers; revisión formal siguiente4 conservada.


## Inspección de componente canónico — intento1, anterior a formal4

2026-10-07T23:11:05.852755+00:00: lentes frescas A+B0Critical/1Important/0Minor consolidado; selectorC/Dfalse. CANONICAL-TDD01 confirma19find_spec+3ausencias de atributos/API, frente a3RED funcionales progreso/ownership. Root rechaza clasificación histórica25RED funcionales y mantiene originales.63PASS y whole84,03%/81,74%zeroexcluded siguen evidencia forward, no TDD retrospectivo. Nuevo implementer normal reconstruye capacidades nuevas tras RED de efectos esperados; extracción del cuerpo ya cubierto puede declararse refactor, no nueva capacidad. Prueba/fixture propia deja de escribir entregas cerradas. Próxima inspección componente2/QA; revisión formal integrada4 preservada, T13/FINAL/packs/runtime/GPU siguen abiertos. TDD n/a: adjudicación/prosa del ledger.


## Revisión de componente T-09 — canonical-component-inspection2

2026-10-08T00:15:45.838458+00:00: A limpia; B01 Important reproducido por intercalación simulada sobre originales aceptados, sin procesos ni escrituras. Corrección normal fresh con RED funcional de mutación durante I/O. No aceptación. Próximo componente3; formal integrada4 sin reset; T13/runtime/FINAL/GPU pendientes. TDD n/a: adjudicación/prosa.


## Entrega técnica canonical-anchor-fix2 para revisión independiente

2026-10-08T00:22:52.648074+00:00: B01 corregido snapshot previo a I/O;94PASS=88previos+6nuevos,3RED identidad conductuales. Wholecanonical87,24%zeroexcluded actual; episode81,32% solo predecessor samebytes.62protegidos exactos y94nacimientos/cierres propios actuales. HelperRED temprano bytesUNKNOWN cualificado; verificacion final helperactual samebytes. Inspeccion componente3/QA pendientes, formalintegrada4/T13/FINAL/runtime/GPU abiertos.

RED: `test_caller_identity_is_frozen_before_request_io[attempt]` falló por aceptar pid=0 · 2026-10-08T00:17:02.626986+00:00 · `runs/red-attempt/`.

RED: `test_caller_identity_is_frozen_before_request_io[both]` falló por aceptar pid=0 · 2026-10-08T00:17:07.948471+00:00 · `runs/baseline-both/`.

RED: `test_caller_identity_is_frozen_before_request_io[transition]` falló por aceptar pid=0 · 2026-10-08T00:17:08.702251+00:00 · `runs/baseline-transition/`.



## Revisión de dos lentes — intento 3: T09 componente canónico conforme

2026-10-08T00:31:04.629487+00:00: A+B0Critical/0Important/0Minor; B01 corregido,94PASS/wholecanonical87,24%zeroexcluded. Revisores verificaron lectura/AST/proofsinventario, no rerun funcional propio. QA1 independiente actual posterior; formal integrada4 sin reset, runtime/T13/FINAL/GPU siguen abiertos. No aceptación técnica ni tarea por revisión. TDD n/a: adjudicación/prosa.


## Entrega técnica canonical-native-qa1 para revisión independiente

2026-10-08T00:41:36.986237+00:00: Componente canonico aceptado root:94PASS=69actuales+25vecinos nativos,wholecanonical87,24%zeroexcluded/fuentes75 y64protegidos exactos/2493inventario verificado/94nacimientos-cierres.44capsulas indicesSHA y3equivalencias originales byteexactas. Payload ysemantica O(delta), witnessidentidadprefijo cero-byte sigue lineal. Episodio81,32 solo predecessor unchanged. Runtime/coordinator/rowreader/packsFINAL/T13/GPU/160/calibracion/calidad abiertos; siguiente arquitectura de integracion preservaADR0046/formal4.



## Arbitraje de arquitectura para integración canónica

2026-10-08T00:55:42.675208+00:00: architect privado compara3layouts yrecomiendaO1supervisor condicional. Root eligeO2proceso canónico propio: mantiene interrupción de I/O nativo y sampler independiente deADR0042, sin handles ctypes transportados ni dependencia del worker deoperaciones largas. Segundo handoff debeconcretar ingest/readarbitraje yvistas antescódigo/ADR decontrato, no aceptar deadline/cadencia por prosa. Componentes canónico/custodia actuales permanecen aceptaciones acotadas; formal integrada4/runtime/T13/FINAL/GPU pendientes. TDD n/a: diseño/arbitraje.


## Integración canónica aislada — decisión ADR0050

2026-10-08T01:04:09.963091+00:00: O2 dedicado y arbitraje A ratificados; contrato publicado. Primero dependencia checkout/witness_step/finish/release; luego IPC/ingest/watchdog y callers. Whole EACH80zeroexcluded/TDD/revisión/QA propios. No aceptación de ejecución. Formal integrada4 sin reset; packs/FINAL/restore/GPU/matriz/calibración siguen abiertos. TDD n/a: diseño/prosa.


## Continuación autónoma — dependencia lease canónica

2026-10-08T01:05:28.317760+00:00: implementador fresco limitado a canonical.py y test existente, métodos aditivos y accredit compartido; fixture/custody/episode/proveedor protegidos. RED funcional por intercalación realpasante y presupuesto acumulado previo, wholecanonical80zeroexcluded, revisión/QA posteriores. No IPC/nativeblocking/cadencia/runtime/FINAL/GPU aceptados. Peso2estimado/consumo realNULL.


## Entrega técnica canonical-lease-unit1 para revisión independiente

2026-10-08T01:22:33.353758+00:00: Dependencia lease terminal127PASS94previos+33nuevos=102canonical+25vecinos;3REDfuncionales,wholecanonical90,35%líneas+ramaszeroexcluded/65protegidos exactos/129birth-cleanup corrida final. Inventario original y2fuentes rootverificados por preparación review4, Aen curso Bpendiente; no aceptación. Unreadlease<=1/checkoutsnapshotO1/witnesspasantezero bytes/state lockbrief/ownthread/fixed2s budget/freshclock; storelocknativo aúnnointerruptible, prefixesidentityO(n) explícito. No IPC/runtime/episode/cadencia/13h/160/packsFINAL/GPU/calibración aceptados. Formalintegrada4distinta sinreset. Corrida preformat/PowerShell5inventario/reporting incidentes conservados yúltima fuentecongelada actual; nada deunion histórica.



## Revisión de dos lentes — intento 4: T09 dependencia lease conforme

2026-10-08T01:29:47.524321+00:00: A+B0Critical/Important/Minor;127PASS/3RED/currentwhole90,35zeroexcluded/65protegidos y129birth-cleanup final contrastados porlectura propia, no rerun funcional de revisores. QA lease independiente siguiente. No aceptación porrevisión ni IRQkernel/storelock/cadencia/IPC/runtime/FINAL/GPU. Formalintegrada4 distinta sin reset. TDD n/a adjudicación/prosa.


## Entrega técnica canonical-lease-native-qa1 para revisión independiente

2026-10-08T01:36:22.105290+00:00: Root acepta sólo dependencia técnica lease:127PASS102canonical+25vecinos/current90,35wholezeroexcluded/65protected67QAmap/129birth-cleanup propio/inventario2265original verificados. Exitcodes conocidos incluyen controles negativos, no todos0 inferidos. No bloqueo store nativo/IPC/episodio/runtime/T13/cadencia/13h/160/FINAL/GPU/calibración/calidad/M0aceptados. Próximo proceso canónico aislado typedbootstrap/ingreso bajoADR0050; formalintegrada4sinreset. TDD n/a QA independiente.



## Continuación autónoma — proceso canónico aislado, primera dependencia

2026-10-08T01:44:38.366677+00:00: leaseQA1 técnicaaceptada127PASS/current90,35whole/65protegidos129birthcleanup/inventario2265. Implementadorfresco recibeprocess+testexisting ycanonical_runtime+testnew, cuatrofuentes; canon/custody/episode/runtime/callersprotegidos. OptinclosedMUX/bootstrapauténtico/ingresoprioritario/abortknownJob conoriginalbudget, fuenteanclaobservada no JSONcaller; bloqueokernel/pipe gate nativoreal ylímites seguros. REDfuncional existentescall/close antescódigo, no APIabsence; whole EACH80zeroexcluded parentchildfresh. No callbacksrow niEpisode/fullruntime/FINAL/GPU/cadencia13h/160aceptados. Peso4estimado realNULL; component5/QA después yformalintegrada4distinta.


## Revisión de componente T-09 — canonical-component-inspection5

2026-10-08T02:44:30.533111+00:00: Process componentinspection5Aclean/B2Important/Dclean. B5-01 progressvalid thirdframe overflowswaiter2 vs64legal; B5-02 muxpayload/value bridge losesoriginalfailure afterprogress. Reviewer in-memoryreproduction notnativeprocess load. Fixthreeownedfiles runtime/process/testruntime, originalprocess/tests/canonical/custody/episode otherwiseprotected. Native REDgate/checkcleanup originalownedJob beforefix,64priorcasebaseline plusnewwholecurrentparentchild80zeroexcluded. Rootdecidescontinuationunderexistingautonomy withoutreset component6/formal4; no process/T09/GPU/cadence/matrix/qualityaccepted. TDD n/a: adjudicación/prosa.


## Proceso canónico: entrega corregida e inspección 6

2026-10-08T03:15:56.444992+00:00: Root verifica inventario11320 y tres fuentes selladas/dos cambiadas. B5-01/B5-02 corregidos en runtime/test; process byteexacto. 76PASS/1PDH expresamente deseleccionado, whole runtime85,34/process81,58zeroexcluded padre+hijos frescos. 108birth-cleanup:91ClosedConfirmed/17UnknownQuarantined; incidentes RED de cierre importado incompleto y setup nativo rescatado conservados, no procedencia perfecta retroactiva. Selector real A+B, C/Dfalse; A despachada, B pendiente. Root continúa bajo autorización autónoma, componente6/formalintegrada4 conservan contadores. No QA/proceso/T09/160/cadencia/GPU/calibración/ReadFile físico/FINAL aceptados. Peso por lente0,5estimado/consumo realNULL. TDD n/a: custodia y orquestación.


## Revisión de dos lentes — intento 6: T09 proceso, componente aislado

2026-10-08T03:20:41.125295+00:00: A+B0Critical0Important0Minor; B5-01/B5-02 corregidos, fuentes3 exactas/dos cambiadas. Pruebas archivadas76PASS/currentwhole runtime85,34/process81,58zeroexcluded parentchild. Probes AST en memoria por B, lectura hash/copies por A: no suite propia. QA independiente actual siguiente; no proceso/T09/160/cadencia/GPU/calibración/ReadFile físico/FINAL aceptados. Contador6 y formalintegrada4 distintos preservados bajo autorización autónoma. Consumo realNULL/peso QA1,5estimado. TDD n/a: adjudicación/revisión.


## QA T09: incidencia de bootstrap privado y nueva pasada independiente

2026-10-08T03:29:47.062996+00:00: QA1 yielded42PASS34setup errors1PDH deselected due private import path missing test_benchmark_observation. Those34cases did not execute assertions; no productdefect proven/no nativecomponent acceptance. Preserve original evidence and qualifiedcoverage/cleanup; root authorizes fresh QA2 privatebootstrap repair and complete current76baseline, justified by actualfailure. Source3 exact/review6clean retained, no review rerun/counter reset/olddata union. ActualconsumptionNULL estimated1.5. TDD n/a: independentQA.


## Entrega técnica canonical-process-native-qa2 para revisión independiente

2026-10-08T03:40:05.660661+00:00: Root acepta SOLO dependencia tecnica proceso ADR0050:76PASS1PDHdeselected/currentwhole runtime85,34/process81,58zeroexcluded parentchild/69protegidos/18440inventario exactos. 108launch-cleanup107assign/91ClosedConfirmed17UnknownQuarantined sin recursos propios vivos observados; errores negativos y ausencia de EOF no se vuelven confirmados. QA1 original42PASS34setup/5282inventario readonly conservada, QA2 bootstrap privado corregido/una pasada nueva sin union historica. Rootcabeceras normalizadas despues de QA (8avisos original=7Changelog+1cabecera, actual7); contadores6/formalintegrada4 separados. Proximo handoff integracion Episode/provider/coordinator/filas/CLI/prerrequisitos; ReadFile fisico/FINAL/restore/cadencia13h/160/GPU/calibracion/calidad/T09/M0 abiertos. TDD n/a QA independiente; reales NULL.



## Continuación autónoma: handoff de integración canónica actual

2026-10-08T03:42:29.156179+00:00: Dependencia proceso aceptada QA2; architect fresco delimita la siguiente unidad Episode/provider/coordinator contra APIs actuales ADR0050, sin reabrir O2/arbitrajeA ni implementar por prosa. Fuentes eval selladas, root decide/publica contrato si cambia documentación. Formalintegrada4 distinta/componente6 sin reset; matriz160/cadencia/ReadFile físico/GPU/calibración/FINAL/calidad abiertos. Peso1 estimado/realesNULL. TDD n/a: diseño y handoff.


## T09: ingreso canonico y status base en callers reales

2026-10-08T04:09:01.544862+00:00: Root elige handoff1/ADR0050 sin reabrir: cinco modulos y testnuevo; factoryoptin con Episode real/statusbase independientes/guard consumidoresrestantes. LegacyCLI sinactivar pendiente. Rejected/interrupted/deadlineoriginal2s, no arrays certificadosporpadre. Wholecada cinco>=80zeroexcluded padre+hijos; runtimehistorico19% noaceptado. ProcesoQA76 solo dependencia, counterscomponent6/formalnext4. Peso5estimado/realesNULL.


## T-09 — causa raíz del cierre nativo de error de protocolo

2026-10-08T05:08:27.254099+00:00: Integración actual mantiene fallo protegido resources_returned=false pese a Job vacío. Se autoriza diagnóstico privado fases1–3 con el único parámetro error-native_protocol_error; sin cambios de transporte/tests ni PDH/GPU/UI. Aceptación completa sigue pendiente.


## T-09 — corrección causal del observador de EOF

2026-10-08T05:15:45.857398+00:00: Root verificó diagnóstico542artefactos/68protegidos. Error terminal admitido seguido de otro terminal rechazado mata observador EOF. Se autoriza transición de drain en proceso propio revocado, sin aceptar respuestas ni fingir EOF; proceso/runtime y nuevo test owned, fixture/test protegido original byte idéntico. Review/QA/formalnext4/component6 pendientes.


## Entrega técnica canonical-integration-unit1 para revisión independiente

2026-10-08T05:16:23.008993+00:00: Entrega parcial:242PASS1fallo protegido13deselected, cinco WHOLE80,52–86,51 sin exclusiones. Root verificó352700artefactos/66protegidos antes del fix posterior; no aceptación. Una sonda PDH accidental baseline1 conservada/cualificada. Causa nativa probada independientemente; proceso/runtime se corrigen en unidad nueva sin debilitar fixture/asserts.



## Entrega técnica native-protocol-cleanup-diagnosis1 para revisión independiente

2026-10-08T05:16:23.523575+00:00: Diagnóstico privado fases1–3: dos nodeids exactos exit1 sin coverage, secuencia error/result rechazada antesEOF probada;542artefactos/68protegidos root exactos. Sin cambios de producto en diagnóstico. Root autoriza phase4 causal en proceso/runtime y nuevo test manteniendo protegido original; ni cleanup ni T09 aceptados.



## Entrega técnica native-protocol-cleanup-fix1 para revisión independiente

2026-10-08T06:03:13.691038+00:00: Corrección causal entregada:253PASS13deselected/finalbaseline3 runtime84,38process81,90 WHOLE sinexcluidos;253trazasUUID+padre actuales ydosstartupscoverageindividualUNKNOWN preservados. Rootinventario16994archivos66protegidos actualexacto. Test/fixture original byteAST intactos; physicalReadFileBLOCKEDUNTESTED. Inspection7A limpia Bactual/Csuplementaria-Dpendientes; formalintegrated4 distinto, sin aceptaciónT09. Baselines fallidoscheckpoint y20trazasfaltantes anteriores preservados, no uniónhistórica.



## Parada solicitada para apagar el ordenador

2026-10-08T06:27:22.369342+00:00: Parada expresa para apagar. Inspection7 A/B/C/D terminales sin hallazgos; adjudicación root y QA independiente pendientes al reanudar. T09 sigue abierto; no nuevo actor.


## T09: revisión componente canónico — intento 7 adjudicado

2026-10-08T18:14:22.490451+00:00: A/B/C/D terminal0 con0Critical/0Important/0Minor; tres fuentes actuales exactas. C suplementaria por frontera de autoridad, D automática; counters previos conservados. QA independiente autorizada; ReadFile bloqueado/cierre desde lector UNTESTED y dos startup coverage UNKNOWN. Integración/fullT09 abiertos. TDD n/a: adjudicación.


## T09 componente canónico: aceptación técnica acotada de QA1 actual

2026-10-08T18:26:56.658108+00:00:253PASS/13deselected, WHOLEruntime84,58418/process81,90184 ceroexclusiones,254trazas del mismo run. Root5348originales/78fuentes66protegidos/JUnit/JSON actuales exactos. Agent nativo, no CLIexitpadre inventado. Dos startupcoverageUNKNOWN, ReadFilebloqueado/closelectorUNTESTED conservados. El warning17UIrutas de coverage-check procede WIPM1 separado, no UI del componenteM0; marker sinUI M0 conservado, ningúnverdeE2E/global. Inspection7 limpia; siguiente integración formal4, T09 abierta. [Aceptación](testing/t09/native-protocol-cleanup-qa1-root-acceptance.json). TDD n/a: adjudicaciónQA.


## T09: exploración de cobertura integrada antes de nueva revisión

2026-10-08T23:23:35.965454+00:00: Explorer-role readonly porCLIfallback cuotaAgent. Pregunta específica: seis módulos actuales y comando/baseline/coverage pendiente para revisiónintegrada4, conúltimaQAcleanup253 dosmódulos accepted. No implementación/inferencia/GPU/gate verde, rootelige siguientesacciones desdefuentesactuales noold5coverage. M1Linux/SQL productores disjuntos.


## T09: baseline integrado actual de seis fuentes WHOLE

2026-10-08T23:38:14.660618+00:00: Ownership[] mediciónprivate de6WHOLE actuales antesreviewformal4;7testsbyteexact selecciónCPU253/13original; branchformula perfile80zeroexcl oneUUID. NoactualGPU/CLI/calib/cadence13h/QAaccepted. No heavy overlap con801pair, rootprecondition.


## T09: Revisión integrada — intento 4

2026-10-08T23:52:07.550933+00:00: Root verifica originales/current6/253PASS13deselected/254RAWsameUUID y cobertura WHOLE individual80+0excl. Formal4 continúa formal3/T08–T13 con rebateT10 conservado; contexto fresco A/B/C/D readonly, QA independiente pendiente. Scope referenciaHEAD acumulada6 explícita, ownershipmedición[]; no cierreT09/GPU/160/calib/CLI/cadencia/FINAL.


## Entrega técnica current-integrated-six-baseline1 para revisión independiente

2026-10-08T23:53:23.804889+00:00: Rootmedición253PASS13deselected, seisWHOLE80+0excl y254RAWsameUUID cotejados. Entrega measurement-only ownership[], noaceptación. Formalintegrada4preserva3/T08-T13/rebateT10; revisión A/B en curso, C/D y QA pendientes. Límites nativeUNKNOWN/GPU/cadence13h/CLI/FINAL conservados.



## T09: fusión formal integrada — intento 4

2026-10-09T00:04:11.744703+00:00: 0Critical/5Important/0Minor fusionados. Cuatrocurrentgaps y R09T13CLIlegacypendiente; T10rebatidoconservado. [Informe](testing/t09/current-integrated-review4-report.md). FIRSTcause3fronteras autorizadoTDD; deadline+binding diseñoacotado separado antesfix. Revisión5 futura sinreset; QA/GPU160/CLI/cadencia/calib/FINAL/T09/M0 abiertos.


## T09: arquitectura de deadline completo y contexto-plan

2026-10-09T00:04:42.482723+00:00: Architect-role freshreadonly porCLI para B4-02/B4-03/B4-04; compara alternativas concretas sinimplementar. Rootelige bajo delegación del propietario ypublicaADR sólo sicambia contrato vigente. FIRSTcauseotraunidad owned3 no interfacerewrite; contexto leerarchivedfreezeactual paraevitar mezclas. No QA/gates verdes porprosa.


## T09: corrección causal FIRSTcause después de formal4

2026-10-09T00:04:56.556117+00:00: Fresh implementer para B4-01/R09-T09 en episode/process/coordinator y tres tests, seisowned. Deadline/contextbinding yCLIlegacy separados. Sourcecheck/diseño paralelo readonly sobre copias; no resets. RED nativo controlado antesminimumfix; baseline253original+newcases y seisWHOLEcurrent80zeroexcl con trazasfreshsameUUID. Revisión/QA pendientes.


## T09: diseño deadline/context adoptado por delegación

2026-10-09T00:24:56.049608+00:00: Rootverifica inventario e102copies (100hashBefore+2suplementoshashAfter), seisprotectedexact; cifrareceiptphysical_input_count3 son grupos, no archivos. EligeO2 mediante [ADR0059](../../decisiones/ADR-0059-fuentes-y-presupuesto-absoluto-del-benchmark.md). U1startup/U2verificador/U3binding/U4propagación, fuentesFIRSTcause aúnno transferidas. Protocolo acotado/guardprivado, UNKNOWN no free, sinhardRT ni snapshotatómico atribuido. ImplementaciónTDD/reviewformal5/QA pendientes; noaceptaciónporprosa.


## Entrega técnica deadline-binding-design1 para revisión independiente

2026-10-09T00:25:53.334376+00:00: Rootadopta O2 medianteADR0059 bajo delegación delpropietario. Inventario/102copias(señaladas3grupos enreceipt)/100before+2hashsuplementoafter/seisprotected verificados. Diseñoestático sincode/test/nativeproof; OLDreport propuesta conserva estadohistorico yroot-adoption fija decisiónreal. U1startup/U2verificador/U3binding/U4propagación trasliberarownershipFIRSTcause; ningunaaceptaciónT09/GPU/calib/CLI/FINALporprosa.



## Entrega técnica integrated-firstcause-fix1 para revisión independiente

2026-10-09T00:50:43.424841+00:00: Rootcurrent263PASS(original253+10)/13deselected/267RAWfreshUUIDfinal03 yseisWHOLE80+0excl conowned6/protectedexact/inventario verificados. Tresfronteras primaryfailure+secondarycleanup preservadas; controllednativeREDantesfix+refsetteradditionalRED, sincausaprevialimpiezaerrorsepropaga. Componentinspection1A/Bstarted C/Dpending; formal4→5sinreset, otrosB4deadline/binding/CLIlegacy pendientesADR59. Native268235closed33UNKNOWN/twoindividualstartupcoverageUNKNOWN ymetadataearlylimitationsconservados. NoQAindependiente/acceptance/T09/M0/GPU/cadence/CLI/FINALclaim.



## T09: FIRSTcause inspección de componente — intento1

2026-10-09T01:02:29.688966+00:00: A/C/D0newgaps, BFC01Important residuo episodio698(recordloggercanoningest masksprimary/skipssensorcleanup). [Informe](testing/t09/integrated-firstcause-inspection1-report.md). Known3boundariescorrectedperoQAblockeduntilresiduefix. Owned2configpreparedNOTlaunched; wait801isolatedmeasurementterminalthenTDD. Componentreview2 future/formal4→5unchanged, noacceptance.


## T09 FIRSTcause: corregir residuo FC01

2026-10-09T01:11:30.255520+00:00: FreshTDD FC01 episode698: canonicalingest primary+canonicalclose secondary+cleanuprecording tertiary mustpreserveprimaryand attemptsensorclose/interruption. Episode+integrationtest OWNED2, otherfirstcausefix sourcesprotected. Original263/newcase current6WHOLE80+0excl/RAWsameUUID. Launchafter801measurement heavy isolation; componentinspection2/formal4→5/noQA yet.


## Entrega técnica integrated-firstcause-fix2 para revisión independiente

2026-10-09T01:30:30.541615+00:00: Rootcurrent266PASS/13sameCPUdeselect(original263+3)/sixWHOLE80zeroexcl/current276RAWallphysicalcopies/coreowned2+protected/sourcevalidated. Nativecontrolledcanoningestclose/logger errorRED beforeminimalguard; in-memoryinterrupt notdurableIO proof. Rootinspection2A/Bstarted CpendingDselectorfalsepreserved; formal4→5othergapsB4sourceD/startup/binding/R09T13CLIremainopen. Native277241closed36UNKNOWN/twostartupstderr/RPC limits retained. NoindependentQA/component/T09/GPU160/calib/cadence/CLI/FINAL/M0accepted.



## T09 FIRSTcause: inspección del componente — intento2

2026-10-09T01:38:13.935527+00:00: A1ImportantFC02canonicalruntime1059/1142, B/CFC01episodiocorrected. [Informe](testing/t09/integrated-firstcause-inspection2-report.md). Owned2newconfigpreparedNOTlaunchuntilqueued801isolatedfinish. ActualnativeREDbeforeminimumguard/full266+new/freshreview3/QA required, formal4→5/T10/otherB4preserved. No acceptance.


## T09 FIRSTcause: corregir frontera interior FC02

2026-10-09T02:14:55.627829+00:00: FreshTDD canonicalruntime1059/1142 primaryingest+abort+record failure debeconservarPrimary. Owned2canonicalruntime/integrationtest, EPISODEguardfixedreadonly. ConfigpreparedNOTlauncheduntilisolatedqueued801terminal; actualnativeRED beforeminimumguard/fullold266+new/6WHOLEcurrent80zeroexcl/freshRAWsameUUID, componentinspection3/formal4→5preservados.


## Entrega técnica integrated-firstcause-fix3 para revisión independiente

2026-10-09T02:29:43.023624+00:00: 274 PASS/13 deseleccionados, seis módulos WHOLE ≥80% sin exclusiones, 300 RAW misma UUID; fuentes/inventario/copias/AST verificados por Root. Metadata de preimágenes contiene copy adicional: ambos ejemplares y SHA/bytes comprobados sin reescribir originales. Revisión componente3 iniciada; QA/ADR59/otras brechas pendientes. Sin aceptación de tarea.



## T09 FIRSTcause: inspección del componente — intento3

2026-10-09T02:36:21.755646+00:00: A/B/C sin gaps nuevos. [Informe](testing/t09/integrated-firstcause-inspection3-report.md). Config QA fresca274 preparada, no aceptación. Otras brechas/formal4→5/T10 intactas.


## T09 FIRSTcause: revisión3 limpia y QA independiente

2026-10-09T02:36:28.042435+00:00: Componentinspection3 A/B/C0gaps, Dselectorfalse. FC02 corregido, formal4→5/T10 y otras brechas intactas. QA independiente fresca de274/same13/6WHOLE80zeroexcl/newRAW antes de eventual transferencia ADR0059; no aceptación ni cierre de T09.


## FIRSTcause: aceptación técnica acotada y transferencia ADR0059

2026-10-09T02:58:42.193931+00:00: QAindependiente274PASS/13desel/6WHOLE80+0excl/300RAW nuevoUUID y5404copias verificadas. Revisión3 A/B/C limpia. Sólo preservación de causa primaria aceptada, no universalcleanup/cierreT09. Límites nativos/TCB/recursos noobservados UNKNOWN persistentes. Root autoriza transferencia para U1startup ADR0059; formal4→5/T10 y B4-02/03/04+CLI abiertos. [Aceptación](testing/t09/integrated-firstcause-native-qa1-acceptance.json).


## Entrega técnica integrated-firstcause-native-qa1 para revisión independiente

2026-10-09T03:00:10.626981+00:00: QA independiente274PASS/13CPUdesel, seis WHOLE80+0excl,300RAW UUID nueva; Root inventario y5404copias físicas cotejados. Se acepta sólo preservación de primera causa, sin certificado universal de limpieza ni cierre de T09/M0. B4-02/03/04+CLI y todosUNKNOWN siguen abiertos; transferencia ADR0059 autorizada para siguiente unidad.



## T09: transferencia FIRSTcause y comienzo U1 de ADR-0059

2026-10-09T04:58:08.306999+00:00: Root verifica las seis fuentes de FIRSTcause QA274 aceptada y transfiere proceso/episodio/coordinador para U1. Presupuesto absoluto y retención de nacimiento; verificador SourceGuard, binding canónico y propagación final U2–U4 siguen pendientes. Nuevas pruebas primero, cada módulo completo >=80 %, revisión y QA independientes. Pruebas nativas pesadas sólo tras terminar SSE; no GPU ni cierre de benchmark.


## T09: frontera nativa liberada; U1 continúa sin reducir alcance

2026-10-09T05:12:11.204149+00:00: Primer actor sólo completó StartupBudget20pure/100 % y se detuvo ante SSE no terminal. Root verifica entrega y actual SSE CLI0; no aceptación U1. Continúa misma unidad con RED nativo, custodia/propagación y baseline adecuada. Historial puro y source FIRSTcause conservados; no reinicio de hipótesis o revisión.


## Entrega técnica startup-budget-birth-unit1-resume1 para revisión independiente

2026-10-09T05:43:31.876388+00:00: U1 implementación actual NOaceptada: current300=269PASS1FAILworkerpipeEOF30fixtureERROR, new26PASS, coordinatorWHOLE71.93/fromFAILED. OriginalstderrDEVNULL no causa reconstruida; no cuarto baseline. Rootdiagnóstico readonlyONE originalcase preparado con captura stderracotada, sinfix/historiawaiver.

RED: test_delayed_actual_popen_revokes_before_late_gate falló con caller blocked past original startup budget in native birth — red-native/command.json, stdout/JUnit y witnesses previos a la aserción. Producción nativa antigua byteexact en su archivo before.

RED: test_episode_entry_budget_includes_real_context_read falló con failure=None y nacimiento completado después de demora de contexto — red-propagation-fixture-repair. El primer intento red-propagation PASS no es RED; fixture inicial incorrecta/margen demasiado corto, conservado. La corrección de fixture ocurrió antes del cambio al episodio.



## T09 U1: baseline fallida, diagnóstico de EOF antes de fix

2026-10-09T05:44:05.376469+00:00: Current300=269PASS1FAIL30fixtureERROR, new26PASS, fourWHOLEgateFalse(coordinator71.93). Único fallo functional pipeEOF en factoryconsume; stderr originalDEVNULL causaUNKNOWN. No cuarto baseline. Diagnóstico UNO originalcase constderractual acotado y fixtureprivate prereparada, fuente productoreadonly. No aceptación/review/gate de suitefallida.


## T09: reproducción inválida por coverage; un probe corregido autorizado

2026-10-09T05:51:54.626266+00:00: PrimerprobeONE salió antes de consume por importcoverage ausente en hijo (237bytesstderrreal). OriginalEOF causalUNKNOWN. Rootautoriza ONEprobe NUEVO conenvigualfinal03/preflightbasePythoncoverage antesnative, sinreset de H1 ni cambio producto. Historial bootstraperror/captura/owncleanup preservado; no full300/rerun-until-pass.


## Entrega técnica startup-eof-diagnosis1 para revisión independiente

2026-10-09T05:52:04.578837+00:00: DiagnósticoUNO invalidadoantesconsume por envhijocoverageausente, stderr237bytesreal/exit1/ownrefs. OriginalproductoEOF UNKNOWN, nofix/RED/waiver. Rootautoriza ONEcorrectedprobe nuevoNamespace conpreflightmanagedchildenv antesnative, no reset H1 ni historia.



## T09: caso nativo corregido pasa; causa histórica pendiente

2026-10-09T06:13:25.080616+00:00: ONE originalcase PASS,4Popen reales/esperas directas/stderr0, propias salidas de cleanup no crashes previos ni exit0 inventado. H1 UNPROVEN y original300FAILED se conserva. Presupuesto1invalid+1corrected consumido, no nuevos probes originales autorizados. Workload nativo terminado: se libera orden de pruebas futuras de cola, sin promesa de exclusividad ni aceptación U1.


## Entrega técnica startup-eof-diagnosis2 para revisión independiente

2026-10-09T06:13:25.442080+00:00: ONE originalcasePASS/4realchildren directwaits/stderr0; cleanup exit1 no natural exit0/crashproof. H1producto UNPROVEN, original300FAIL kept, no patch/newprobes; Roottiming workload finished/release forqueue tests. Source7 intactall, snapshots/source artifacts validated.



## Revisión de dos lentes — intento 1: U1 compuesto ADR0059

2026-10-09T06:44:29.194475+00:00: scope0 sin avisos/exclusiones; A/B/D contexto fresco terminal0, C no seleccionada. Ocho Important y un Minor aceptados; seis defectos lifecycle aún estáticos, requieren RED real. A04 cobertura coordinator71.92623 y A05 baseline300 FAILED siguen históricos, EOF causaUNKNOWN. T-09 en-progreso; no reinicio de contador fullformal3/4. Sourcehandoff liberado para fix1 sólo process/coordinator+test nuevo; no canonicalruntime/U2–U4. [Informe](testing/t09/startup-budget-birth-composite-review1.md).


## T-09 · U1 revisión compuesto intento1 — corrección causal de lifecycle

2026-10-09T06:46:49.591969+00:00: Root adjudicará A/B/D antes de despacho. Cinco defectos de lifecycle estáticos requieren RED real; cobertura coordinator71.92623 y baseline300 fallida siguen históricos. Cambiar sólo process/coordinator y nuevo test; no H1 guessedfix/timeoutpadding/U2–U4. Baseline nativa original300+newwholefile autorizada una vez tras cambios materiales y reparaciónbootstrap uniqueharness, con carga cronometrada exclusiva Root.


## T-09 · U1 primera baseline amplia fallida; nueva corrección material

2026-10-09T07:24:03.178622+00:00: final01 original308=253PASS43FAIL12ERROR/13CPUdeselected, exit1. Root agrupó31 rechazos de ruta privada API,12 padres de fixtures inexistentes,6 job_empty ausente,5 resources_returnedfalse y1 query inyectada no alcanzada. No aceptación. RED05 real del productor prueba segunda operación indebidamente admitida mientras la primera seguía viva; corregir dentroOWNED2runtime+nuevotest. Root autoriza sólo UNA nueva baseline completa tras cambios materiales y bootstrap correcto; preservar casos originales/plazos/RAW actual y declarar módulos copiados/atribucióncov. No tercerbaseline ni H1guessedfix/canonicalruntime. QA294/801 esperando fin de workload y adjudicación.


## T-09 · Entrega interrumpida por límite del proveedor; sin aceptación

2026-10-09T08:20:45.410229+00:00: actor27982 terminal1, originalturn.failed por usage limit. final02 queda sin completion/JUnit/cobertura completa, no inferir exit0 ni éxitos restantes. PID25840 no observado y namespace de procesos vacío en consulta08:11; cierre universal desconocido. Root conserva originales/fuentes3 actuales en u1-interrupted-delivery-adjudication-root1 y no repite baseline. Causa privada de12setup comprobada por prefijoAST original: parentcanonical-fixtures ausente; mismo código pasa al crear sólo padre. QA294 independiente nativa reutilizada ahora activa; native/801 no concurrentes. Continuación manual del plugin preparada tras QA, sin ampliar scope/asserts/plazos ni declarar U1/M0 terminado.


## T-09 ? Continuaci?n aislada del bootstrap preparada

2026-10-09T08:57:10.148690+00:00: Nuevo arn?s privado u1-native-continuation-bootstrap-root1 integra el helper corregido que crea ambos padres de fixtures antes de pytest y rechaza un namespace fuera de .cache/dev-cycle. Compilaci?n sint?ctica y prefijo de fixture original verdes; 18 fuentes protegidas actuales sin cambio. No se modifican runtime/tests ni entregas hist?ricas. No se ejecuta baseline nativa en paralelo con la unidad sint?tica; final01 fallido y final02 interrumpido siguen sin aceptaci?n. TDD n/a: arn?s/configuraci?n ya derivada del RED causal del bootstrap.


## T-09 ? Baseline aislada fallida y causa de arnes corregida

2026-10-09T09:06:42.860239+00:00: Sesion real57477 terminal exit1; 133PASS/125FAIL/51ERROR y13deselected. Root omitio native_trace.py al clonar el arnes: 180 capturas originales de stderr acreditan archivo ausente antes de arrancar el worker. Fuentes runtime actuales sin cambio; no se acepta cobertura/custodia ni producto. Resultado conservado en u1-native-continuation-bootstrap-root1/root-failed-baseline-adjudication.json.

RED: guard_regression.py fallo con AssertionError: missing native_trace was not rejected before fixture/test startup, antes del guard. Mismo test GREEN exit0 despues del guard y antes de copiar el wrapper. Nuevo namespace root2 incluye wrapper original exacto y preflight positivo/prefijo original de fixture verdes; runtime/tests originales intactos. Suite completa despues del fix pendiente; ventana temporal devuelta a unidad sintetica. No gotcha aprobado: Fase4 global de debugging aun incompleta.


## T-09 ? Caso original verifica el arnes corregido

2026-10-09T09:15:33.601205+00:00: Sesion real59093 terminal exit0; test_persistent_pid_and_close original1PASS con wrapper native_trace/cobertura de hijo activos, stderr vacio y fuentes runtime actuales exactas. ProcesoPID27592 termina (exit nativo1, distinto de pytest0); Job vacio/reader ywriter joined ycleanup CLOSED_CONFIRMED registrados en este caso; callbacks observados son Job DLL, no todos los handles OS. Root verifica solo esta reparacion/caso, no QA independiente, suite completa, gate WHOLE o U1/T09. Evidencia: u1-native-continuation-bootstrap-root2/root-bootstrap-probe-adjudication.json. Ventana temporal liberada para baseline de unidad sintetica.


## T-09 ? Baseline CPU actual acordada verde

2026-10-09T09:46:23.861318+00:00: Ejecucion real3858 terminal0;309PASS0fail/error/skip,13deselected explicitos en seleccion. WHOLE4 cobertura combinada lineas+ramas85.08/86.57/86.95/100%, cero exclusiones; porcentajes de ramas separados conservados, no se afirma ramas>=80. 30 fuentes actuales/18 protegidos/43 copias de tests y assertsAST/313 trazas de ESTA ejecucion cotejados. No se mezcla historia/probe ni se acepta U1/T09 por este resultado: revision/QA independiente y U2/U3/U4/validacionGPU siguen pendientes. Evidencia u1-native-continuation-bootstrap-root2/root-corrected-baseline-verification.json. Ventana temporal liberada para nueva baseline599 de unidad sintetica.

## Revisión de dos lentes — intento 1: T-09, método del sensor en fixture original

Reparación acotada: una inserción de 50 bytes declara
`Sensors.observation_method="task_manager_v1"` en el test original de
envío/reanudación. Se conservan todas las assertions, tiempos y entradas; no
se cambia producto ni se relaja el rechazo de sesiones legacy. TDD/cobertura
de producto n/a: configuración de fixture, reproducción causal conservada.

Root verificó originales y actual, 33 artefactos, 74 fuentes/locks protegidos
y JUnits: RED1FAIL legacy → GREEN1PASS → fichero completo16PASS, exit1/0/0.
Lentes A/B frescas leyeron el diff entero y confirmaron ausencia de defectos:
0 Critical, 0 Important y 0 Minor. Scope0 sin avisos; C/D no seleccionadas.
Adjudicación limpia y FINAL completos preservados en
`.cache/dev-cycle/t09/benchmark-sensor-fixture-review1`.

QA independiente del fichero completo en curso en
`benchmark-sensor-fixture-independent-qa1`; aceptación de este arreglo aún
pendiente. No acredita matriz GPU, benchmark real ni cierre de T-09/M0.

**QA y aceptación del arreglo de fixture:** ejecución independiente única
16/16 PASS, 0FAIL/ERROR/SKIP, terminal0. Root verificó inventario16 de QA,
33 artefactos originales, 74 protegidos y SHA antes/después del test original,
con todos sus nodeids/assertions intactos. Componente aceptado en
`.cache/dev-cycle/t09/benchmark-sensor-fixture-independent-qa1/root-acceptance.json`.
Las nuevas regresiones del helper M1/T-05 deben incluir este caso sin deselect.
T-09 sigue en progreso: no benchmark GPU ni CA completos acreditados aquí.

**T-09 v3 — 2026-10-10:** se corrige la auditoría incremental de prefijos: `read_publications_delta` y `read_attempt_inventory_delta` validan únicamente el segmento nuevo, anclan la primera predecesora al resumen sellado del prefijo y preservan los rechazos/interrupciones sin reabrir episodios anteriores. RED reproducido en `test_benchmark_canonical_growth.py::test_new_delta_does_not_reopen_canonical_prefix` (2 casos, reabría 70/140 lecturas); GREEN focalizado 2/2 y bloque v3 completo **130 passed** en 287,83 s. Ruff dirigido de `benchmark_runtime.py` y `benchmark_episode.py`: exit 0. La validación v3 no se declara cerrada: la sesión real nueva `01M4HS0VY5629RGYXVR7PD9AA9` preparó plan160 y preflight GPU 1.234 MiB, pero quedó detenida en `lease_acquire` por el `gpu.lock` cuarentenado de una sesión CPU ajena (`CPU-OWNED`, plan `01M4C19WT5PD91MA5AVCCERKTM`); auditoría final con 1 recibo, recuperación `unknown_quarantined`, sin eliminar ni reclamar la reserva. T-09 sigue en-progreso y la matriz v1 anterior no se reutiliza.

**T-10 CLI robustness — 2026-10-10:** RED reproducido al ejecutar directamente `scripts/eval/capabilities.py --help` (`ModuleNotFoundError: No module named 'scripts'`). Se añadió el bootstrap de raíz para la entrada directa y una regresión específica en `test_capabilities_cli.py`; GREEN: **128 pruebas T-10 pasan**, Ruff dirigido exit 0 y el CLI directo devuelve ayuda con exit 0. No se afirma ninguna capacidad GPU ni se cambian veredictos de modelo.


## 2026-10-10 - regresion CPU de evaluacion M0

Se ejecuto el bloque CPU focal de T-10/T-11 con el interprete gestionado: `test_evaluation_cpu.py`, guards/fix1/stream-silence y los tests de plan, runtime, metricas, evidencia, CLI, checks y fix1 de capacidades. Resultado: **219 passed en 28,07 s**, exit 0. La evidencia solo acredita contratos, planificadores, metricas y guards; no sustituye la matriz GPU de T-09/T-10, el suelo WER cantado, las tomas reales de T-11 ni la escucha de T-13.


**Dry-run T-11 actualizado - 2026-10-10:** `scripts/eval/run.py --candidate ace-step-1.5-turbo --dry-run` termina exit 0 y planifica las 30 posiciones (10 briefs x 3 semillas), marcando prerequisitos ausentes sin inferencia. Se mantiene abierto por letras/declaraciones propias, entradas musicales, suelo WER y GPU.

**T-09 continuidad de reserva GPU - 2026-10-10:** se reconcilio la reserva propia en cuarentena de la sesion `01M4C19WT5PD91MA5AVCCERKTM` (`owner=CPU-OWNED`). La comprobacion previa encontro PID 9656 muerto, cero contenedores Docker con esa etiqueta y sin `resume-claim`; `GpuLease.release(reconciled=True)` libero solo `.cache/dev-cycle/t09/gpu.lock`. No se borro ni reclamo una reserva ajena. El benchmark puede continuar con una sesion nueva; la matriz 160 y la aceptacion T-09 siguen pendientes.

**T-09 plan v3 preparado - 2026-10-10:** tras reconciliar la reserva propia, `benchmark.py --matrix default --inputs data/inputs/libre/benchmark-5070/2026-10-06-perf-v1/inputs.json --image music-studio/engine-acestep:m0-t05 --prepare-only --observation-method wddm_auto_v3` creo la sesion `01M4JD9JT61V9VCGJ04HXJJ0Y5` con **160 ejecuciones**. No cargo GPU ni publico resultados; el plan queda listo para una sesion con navegador/prerrequisitos WDDM actuales. La matriz y la aceptacion de T-09 siguen abiertas.

**T-09 adquisición paralela - 2026-10-10:** la última sesión terminó con `worker_pipe_eof` secundario a un `worker_deadline` del muestreador al consultar WSL en serie. Se añadió una regresión TDD que obliga al solapamiento WSL/PDH en el proveedor nativo; RED por `TypeError` y GREEN **1/1**, vecinos de observadores/proveedor **21/21**, Ruff/formato limpios. Sonda real WDDM sin modelo y con Ollama vacío: **10/10** muestras sin errores, máximo 84,49 ms; evidencia en [parallel-observer-probe-2026-10-10.md](testing/t09/parallel-observer-probe-2026-10-10.md). Esto reduce el riesgo del timeout, pero no acredita la matriz de 160 ejecuciones ni cierra T-09.

**Actualizacion CPU T-11 — 2026-10-10:** la correccion de R11-06 (cache de verificacion FFmpeg invalidable por lock/ZIP/binario) pasa el foco y vecinos **29/29**; el bloque actualizado T-10/T-11 con `test_evaluation_fix2.py` termina **220 passed en 27,92 s**, exit 0. La repeticion aislada confirma la regresion y mantiene T-11 abierta por entradas propias, GPU, suelo WER, 30 tomas y escucha. La primera pasada amplia tuvo una colision transitoria de arnes y no se usa como evidencia verde.

**T-09 v3 — sesión 01M4K60FPPJ9RNRT4VXDQ9CT4J en ejecución (2026-10-10):** tras la corrección de orden del protocolo en `benchmark_process.py`, Ruff dirigido y la regresión de proceso/observadores/proveedor pasan (**42/42**). Se preparó una matriz nueva de **160** ejecuciones con la imagen fijada por digest `sha256:d8d39e3a08df2883118e63457f0fb8d167e82d53612dcdb9660433ea023aa4c6`, WDDM v3 y prerrequisitos actuales (NVML 1.137 MiB usados / 10.807 MiB libres). La sesión superó plan, reserva, descarga de Ollama y piloto V3; el piloto produjo WAV 30 s, `vram_peak_mb=7815.66845703125`, `spilled=false`, y pruebas de carga/descarga válidas. La matriz sigue en progreso; no se marcan filas ni T-09 como completadas hasta el cierre supervisor y QA.

**T-09 v3 — segunda corrección de orden de progreso y sesión 01M4K6VGJ0T5PZ5F3K3BG2HMB2 (2026-10-10):** la sesión anterior reprodujo `observability_lost_v3_progress_order_invalid`: el proveedor WDDM paralelo emitía callbacks PDH concurrentes y `EpisodeProvider.progress` podía registrar `progress-1, progress-3, progress-2`. RED reproducido en `test_concurrent_sensor_progress_keeps_episode_refs_in_wire_order`; GREEN **1/1**, vecinos de episodio **54/54**, proceso/observadores/proveedor **42/42**, Ruff dirigido limpio. Se añadió lock alrededor de emisión, numeración, escritura y hash de cada progreso. La nueva matriz de 160 ejecuciones ya superó piloto V3 y publicó **4 filas válidas** sin spill; continúa en ejecución. No se cierra T-09 hasta auditoría supervisor completa.

**T-09 v3 — tolerancia acotada al desfase WDDM/NVML (2026-10-10):** la tercera matriz llegó a 4 filas y fue rechazada por `auto_dedicated_disagreement` durante una transición de carga: dos lecturas consecutivas mostraron WDDM por detrás de NVML, sin error de sensor. Se amplió la reacquisición dentro del mismo episodio de 1 a 2 reintentos (máximo 3 RAW, mismo deadline de 2 s), sin aceptar una lectura desalineada ni reintentar errores estructurales. RED/GREEN: `test_transient_dedicated_mismatch_gets_one_bounded_extra_sample`; `test_benchmark_episode_v3.py` **55/55**, observación/política **6/6**, proceso/observadores/proveedor **42/42**, Ruff limpio. La sesión anterior sigue descartada; requiere plan/hash nuevo antes de repetir GPU.


## T-09 ? Continuidad desde el fin de adquisici?n y matriz WDDM ? 2026-10-10

Se corrigi? `scripts/eval/benchmark_observation.py`: la guarda `auto_replayed_or_paused_sample` compara ahora el fin de la adquisici?n anterior con el fin de la actual, sin contar dos veces el trabajo de la muestra previa. RED/GREEN y control de pausa >2,5 s documentados en `testing/t09/continuity-fix-2026-10-10.md`; `test_benchmark_episode_v3.py` 55/55, `test_benchmark_canonical.py` 102/102 y Ruff dirigido verdes.

La matriz WDDM v3 sigue abierta. `01M4KAKGKA5FEZW41XASDN7Z7G` lleg? a 746 recibos y fall? el borde de continuidad; `01M4KBMWS4W3684HC02SA97089` lleg? a 706 y `01M4KCDRQWR0B3B0B15PQNQR59` a 723, ambas con `worker_deadline` del sensor nativo durante lecturas WDDM parciales. Las recuperaciones conservan evidencia y fueron reconciliadas; no se cuentan filas, calibraci?n, 160 ejecuciones ni cierre supervisor como verdes. T-09 permanece `en-progreso`; no se relaja el presupuesto de episodio de 2 s ni la cadencia de 2,5 s.

## T-09 — Revisión de continuidad y reproducción de E/S — 2026-10-10

Revisión A+B del cambio de continuidad terminada sin gaps, tras rebate contractual: el tick inicio-a-inicio de 2,5 s sigue vigente y la guarda adicional compara el fin previo con la finalización actual. El contraejemplo del primer Important incumplía el tick contractual. Diagnóstico independiente de tres escenarios exit 0; el negativo existente ahora aísla la finalización tardía (`start=1,754`, `completion=2,7`) tras comprobar que `validate_samples` pasa. Focal **2/2** y Ruff limpio; resto de tests y AST de producto intactos. TDD n/a para este ajuste de regresión/comentario; la corrección anterior conserva su RED.

La causa del nuevo timeout se reprodujo sin inferencia: copia/verificación Docker de 7.709.380.305 bytes, sin GPU, con sonda nativa en proceso propio. Reposo **100/100**, máximo 93,6804 ms; durante la copia **278** muestras completas y la siguiente `worker_deadline`, con `fsync` de progreso de **237–443 ms**. El contenedor diagnóstico terminó exit 0 y se retiró por su ID; engine persistente intacto. Véase [storage-contention-diagnosis-2026-10-10.md](testing/t09/storage-contention-diagnosis-2026-10-10.md). ADR-0072 decide copia a 128 MiB/s/8 MiB sin crédito acumulado; implementación TDD y repetición nativa pendientes. No se amplían los 2 s ni se reduce la durabilidad. T-09 sigue en-progreso; ninguna de estas sondas acredita GPU ni matriz160.

## T-09 - Sonda de sincronizacion por bloque - 2026-10-10

La copia limitada a 128 MiB/s paso TDD y revision A/B/D, pero fallo la repeticion nativa en la muestra 379 (fsync de 1,3 s). Una segunda reproduccion privada, sin inferencia ni GPU, mantuvo el limite y sincronizo cada bloque: copia Docker de 7.709.380.305 bytes exit 0, 941 bloques; sonda 1.000/1.000 sin timeout, maximo 342,964 ms, cleanup CLOSED_CONFIRMED/resources_returned=true. Evidencia en `.cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/native-during-synced-copy.json` y `storage-sync-receipt.json`. El contenedor diagnostico propio se retiro por ID. La sincronizacion sigue siendo experimental: falta implementarla mediante TDD, revisar el delta y repetir con producto antes de la matriz GPU. T-09 sigue en-progreso; esta sonda no acredita la matriz de 160 ejecuciones ni la calidad musical.

## T-09 - Sincronizacion por bloque: entrega CPU - 2026-10-10

Delta minimo de ADR-0072: write/flush/fsync por bloque, politica monotonic_bounded_sync_v2. Nueve RED aislados previos, nueve GREEN; focal15 y vecinos4 verdes, cobertura de modulo95/113=84,0708% sin exclusiones; Ruff y formato exit0. Dos tests vecinos intactos por SHA. Fuentes congeladas en `.cache/dev-cycle/t09/storage-sync-20261010/`; revision A/B/D y reproduccion directa pendientes. No cierra T-09 ni acredita matriz160. TDD n/a para documentos/recibos diagnosticos del orquestador.

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_sync_failure_propagates_without_valid_receipt[4-flush] falló con Failed: DID NOT RAISE OSError · 2026-10-10T17:45:00.3462072Z (exit 1; red-flush-final.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_sync_failure_propagates_without_valid_receipt[0-flush] falló con Failed: DID NOT RAISE OSError · 2026-10-10T17:44:58.0361104Z (exit 1; red-flush-lock.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_sync_failure_propagates_without_valid_receipt[2-flush] falló con Failed: DID NOT RAISE OSError · 2026-10-10T17:44:59.0822312Z (exit 1; red-flush-tail.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_sync_failure_propagates_without_valid_receipt[4-fsync] falló con Failed: DID NOT RAISE OSError · 2026-10-10T17:45:01.0581033Z (exit 1; red-fsync-final.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_sync_failure_propagates_without_valid_receipt[0-fsync] falló con Failed: DID NOT RAISE OSError · 2026-10-10T17:44:58.5588218Z (exit 1; red-fsync-lock.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_sync_failure_propagates_without_valid_receipt[2-fsync] falló con Failed: DID NOT RAISE OSError · 2026-10-10T17:44:59.6554357Z (exit 1; red-fsync-tail.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_copy_syncs_each_block_before_next_write_including_lock_and_tail falló con AssertionError: assert [('write', 'm...safetensors')] == [('write', 'm...ensors'), ...] · 2026-10-10T17:44:56.2413500Z (exit 1; red-order.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_receipt_declares_copy_policy_rate_and_chunk falló con AssertionError: assert 'monotonic_no_burst_v1' == 'monotonic_bounded_sync_v2' · 2026-10-10T17:44:56.9806044Z (exit 1; red-policy.xml)

RED: scripts/eval/tests/test_benchmark_storage_pacing.py::test_slow_sync_is_in_copy_time_without_credit_for_following_chunks falló con AssertionError: assert 0.125005172 >= (5 * 3) · 2026-10-10T17:44:57.5177290Z (exit 1; red-slow-sync.xml)

## Revisión de dos lentes — intento 2: T-09 — delta de sincronización de copia

Segunda entrega ADR-0072; delta de sincronización revisado por A/B/D de contexto fresco, C no seleccionada. **0 Critical, 0 Important, 0 Minor**. [Informe](testing/t09/storage-sync-review-2026-10-10.md). Nueve RED previos y nueve GREEN cotejados; A/B repiten19CPU/41deselected, D15CPU. Inventario93/93, fuentes2 y vecinos2 intactos por SHA; cobertura WHOLE95/113=84,0708%, exclusiones0. Scope del componente5dentro0fuera0excluidos0avisos; fullworktree compartido mantiene459paths ajenos a M0, no gate global verde. La revisión se limita al delta posterior a la primera entrega aprobada; no reinicia ni sustituye las revisiones generales históricas de T-09.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin defectos del delta | T-09 | n/a | testing/t09/storage-sync-review-2026-10-10.md |

QA CPU y reproducción nativa directa siguientes. Matriz160, generación/aceptación musical y cierre T-09 pendientes; T-09 sigue en-progreso.
## T-09 - Copia v2 validada y matriz nueva en ejecucion - 2026-10-10

QA CPU independiente19/19, coberturaWHOLE95/113=84,0708%excl0, SHA4fuentes intactos. La reproduccion directa Docker (sin GPU/inferencia/envoltura) copio7.709.380.305bytes con mismos archivos/hashes y politica monotonic_bounded_sync_v2: origen35,056s/copia88,931s/destino3,941s, contenedor exit0 retirado por ID propio. Sonda concurrente1000/1000, errores0, navegador visible, max255,4281ms; CLOSED_CONFIRMED/resources_returned=true. [Diagnostico y evidencia](testing/t09/storage-contention-diagnosis-2026-10-10.md), [revision/QA](testing/t09/storage-sync-review-2026-10-10.md). TDD n/a: documentos y herramientas privadas de reproduccion, producto conserva9RED previos.

Plan oficial nuevo `01M4KF9XPEXY1GFA6RCSN9WHTR`,160jobs,wddm_auto_v3, imagen fijada por digest y hashes de fuente v2. Preflight actual Ollama vacio, NVML1023MiB, gpu.lock ausente. Comando real iniciado: `uv run scripts/eval/benchmark.py --matrix default --resume 01M4KF9XPEXY1GFA6RCSN9WHTR --prerequisites .cache/dev-cycle/t09/runtime/01M4KF9XPEXY1GFA6RCSN9WHTR/prerequisites.json`. Handle ejecutor5696 vivo al arranque; no se reinicia por timeout de observacion. Piloto, matriz completa y cierre supervisor pendientes. T-09 sigue en-progreso; objetivo global activo.
## T-09 - Ultima sesion terminada y preparacion por corregir - 2026-10-10

La sesion `01M4KF9XPEXY1GFA6RCSN9WHTR` termino exit 1; el handle 5696 ya no esta vivo. El piloto GPU genero WAV de 30 s, pico 7.815,7 MiB y `spilled=false`, con 264 recibos/264 intentos de observacion. Despues fallo con `KeyError: evidence`: el fichero privado de arranque preparado por el orquestador omitia los campos de evidencia host/viewport. No se acredita como matriz completada ni como fallo de calidad musical. Se conserva la sesion fallida; la siguiente requiere plan y evidencias nuevos, sin reutilizar su calibracion.

El recibo `recovery-01M4KFJSN0QA3VVXRQKSD8NJ1G.json` confirma retirada del contenedor temporal propio, worker `CLOSED_CONFIRMED`, `resources_returned=true`, reserva GPU liberada y estado previo de Ollama restaurado. El siguiente paso es corregir y comprobar los prerrequisitos antes de repetir la matriz oficial de 160 ejecuciones. T-09 sigue en-progreso y el objetivo global permanece activo. TDD n/a: registro documental y preparacion privada; no cambia producto.

## T-09 - Preparacion corregida y sesion nueva - 2026-10-10

Nueva sesion oficial `01M4KG1EQ2D9TEWFEZYR4RRV19`, plan SHA `77beef4b18f493a8d53b8ef5cae0ad22d387cdfbaa07d1e8ca607913724aa93c`, 160 posiciones. El helper privado adquiere host actual con contexto fijado antes de leer, persiste host/viewport y comprueba ambos sellos, campos requeridos, identidad, hashes de fuentes/lock y preflight. La vinculacion HWND/pestana sigue `unproven`; no se presenta como prueba de UI. Registro `.cache/dev-cycle/t09/progress-persistence-diagnosis-20261010/matrix-prepare-after-sync2.json`; cleanup de los dos hijos propios `CLOSED_CONFIRMED/resources_returned=true`. La reproduccion CPU de campos pasa `bootstrap_fields: host y viewport presentes`; no equivale a acreditacion completa.

Preflight repetido: Ollama vacio, NVML 1.014 MiB, reserva ausente. Comando `uv run scripts/eval/benchmark.py --matrix default --resume 01M4KG1EQ2D9TEWFEZYR4RRV19 --prerequisites .cache/dev-cycle/t09/runtime/01M4KG1EQ2D9TEWFEZYR4RRV19/prerequisites.json`, ejecutor 47329 vivo al arranque. Pendientes piloto/calibracion nuevos, matriz y cierre supervisor; no reutiliza recibos de sesiones fallidas. TDD n/a: herramientas privadas de preparacion y prosa; producto no cambia.

**Knowledge Gate del componente de copia - 2026-10-10:** knowledge-curator aprobo GOT-002 como GOTCHA/validated_case, gate approve sin errores/avisos e indice valido. Archivo vigente docs/knowledge/approved/gotchas/GOT-002-copia-de-pesos-y-persistencia-de-observaciones.md; alcance exclusivo CPU/Docker, sin exportacion a backends ni aceptacion GPU/T-09.

## T-09 - Sesion terminal, cuatro filas y diagnostico - 2026-10-10

El ejecutor 47329 termino exit 1, sesion 01M4KG1EQ2D9TEWFEZYR4RRV19: incomplete_or_preflight_failed, supervisor_anchor_sha256 96409df15520b86985cb2b1fcc76cb67510c52b6310fc4a6f79350573120b53e, 939 recibos y 940 intentos. El piloto/calibracion nuevos constan y cuatro row.json tienen valid=true; no acredita matriz160. Las cuatro filas shared_gpu_observed=true pese a spilled_engine=false: señal agregada del adaptador, no prueba de ausencia de spill ni de atribucion al proceso. El audit registra auto_dedicated_disagreement; la causa se investiga con debug-root-cause sin cambiar tolerancias, reiniciar a ciegas ni reutilizar observaciones como aceptacion.

Recovery recovery-01M4KGYTKC1V1WAZDY7KK33GJF.json confirma contenedor temporal15432a... removed, worker CLOSED_CONFIRMED/resources_returned=true, reserva liberada y Ollama previo vacio restaurado. original_error worker_pipe_eof es sintoma, no causa demostrada. Watchdog propio26439 detenido, terminal watchdog:stop. TDD n/a: registro y diagnostico privado. T-09 sigue en-progreso; objetivo global activo.

## T-09 - Cadena de cancelacion probada; causa fisica abierta - 2026-10-10

Debug-root-cause fases1-3: tres RAW autenticos delintento940 reproducen auto_dedicated_disagreement por259,0078/307,0039/215MiB contra128. Prueba procesoCPUWindowspropio acredita que ContinuousCoordinator._fail terminaJob y produce worker_pipe_eof/exit1/CLOSED_CONFIRMED/resourcesreturned; rechazo anterioralEOF. Root repite replay3 y coteja4fuentesSHA+4rows conexit0 sin sobrescribir pruebasoriginales. Guardcorrecto; causa fisicaWDDM/NVML no probada, ningunpatchni tolerancias ampliadas. [Informe](testing/t09/worker-cancellation-diagnosis-2026-10-10.md). Sinfase4/nuevoGOT sin causa/fix.

Preflightnuevo Ollamavacio/NVML1023MiB. SondaGPUsololecturaenreposo30muestras(noinferencia/CUDA): NVMLdirectamediana0,0110ms vsCLI31,1733ms; PDH0,1044ms. Evidencia privada native-nvml-idle-probe.json (fuentesSHA/relojes/RAW). No pruebadurantecarga, no modifica proveedor/politica/calibracion ni valida160. Próximaexperimentaciónacotada antesrepeticionmatriz; T09en-progreso yobjetivoglobalactivo.

## T-09 — Precarga y semántica NVML: diagnóstico parcial — 2026-10-10

Una precarga BF16 propia, sin inferencia; 456 RAW (10 reposo/446 carga), cero loaded_idle. Parada sustained_shared_risk y POSTload HTTP 504 desde log original acotado; no cuerpo HTTP exacto retenido. Root verificó 22 artefactos, 456 muestras y nueve hashes fuente, exit0 2026-10-10T19:14:33Z. NVMLv1.used=v2.used+reserved284MiB en todas; máximo delta PDH-v2 13,2578125MiB, CLI15,203125MiB. No explica el desacuerdo histórico ni justifica cambiar proveedor/tolerancia. Custodia del intento GPU CLOSED_CONFIRMED/resourcesreturned, engine original idle sin modelo/job, Ollama vacío/reserva liberada; primer fallo CPU anterior perdió identidad y su booleano reaped vacuo está expresamente invalidado. Informe testing/t09/native-nvml-preload-diagnosis-2026-10-10.md y recibos .cache/dev-cycle/t09/native-nvml-load-probe-20261010/. Sin rebuild, cambio de pesos, calibración ni matrix; T-09 permanece en-progreso. Sigue análisis readonly/CPU del 504 antes de otra carga.
## T-09 — Presupuesto de precarga y captura HTTP — 2026-10-10

Análisis readonly de diez fuentes reales de imagen: POSTload sin deadline→supervisor60s; jobs trasladan deadline. Logoriginal504+hashApiErrorTIMEOUT coinciden, primera muestra→50460,443409s. No fase/PIDexit del hijo original, stderrDEVNULL; no atribución de coste hashing/copia/CUDA. Metadata lock7.709.380.305bytes sin rehash/copia ejecutada. Antecedente carga122,866s en otraimagen no reconstruye petición ni reproduceactual. FixtureHTTPCPU4PASS mantiene body/status/envelope/rechaza payloadinválido; proceso propio CLOSED_CONFIRMED/hilo cerrado. Root50artefactos yterminal0/hasherror verificados, exit0 2026-10-10T19:22:53Z; sin nuevaGPU ni cambiodeproducto. Informe ampliado testing/t09/native-nvml-preload-diagnosis-2026-10-10.md; recibos http504-analysis/ bajo carpeta sonda. T-09 abierta; se requieren fases/custodia de carga antes de nueva sonda, sin ampliartolerancias ni presupuesto a ciegas.

## T-20: verificación estructural actual — 2026-10-11T12:29:03.710459+00:00

Helper actual ejecutado exit0: DOCUMENT_LINKS_PASS,12documentos/348enlaces/0errores. Primera ejecución actualroja2targets en M1tasks conservada; ROOT reemplaza únicamente ambos enlaces a reports reales y deja resto bytes exacto. [Informe actual](testing/t20/current-document-verification-2026-10-11.md); recibos/snapshots propios nuevos en `.cache/dev-cycle/t20/current-document-verification-20261011/`, históricos intactos.

Se actualiza sólo VerificaciónT20 al helper reproducible actual, pues históricohardcodea namespaceexistente. Ocho documentos distintos al freeze7octubre; semántica actual/review/QA yGitacotado siguen pendientes, T20en-revision. No repetición de pruebasGPU/CPU ni afirmación de despliegue porenlaces. TDDn/a: dos targets documentales y comandoactual. Sin markerindividual/horasreales añadidas, objetivoM0–M5activo.


## T-20: verificación documental repetible — 2026-10-11T12:44:32.954665+00:00

El comando declarado usa ahora el helper repeatable/verify_current_root.py. Cada ejecución crea un directorio de evidencia nuevo dentro de su carpeta runs; rechaza sobrescribir resultados anteriores. ROOT lo ejecutó dos veces consecutivas: ambas 12 documentos, 348 enlaces locales y 0 errores; paths de evidencia distintos, doce snapshots y hashes del verificador comprobados. Helper/recibo attempt2 anteriores permanecen byte exactos. TDD n/a: corrección del procedimiento documental, sin cambio de producto. T20 sigue en-revision, no cierre semántico/Docker/GPU por esta prueba. Recibo `.cache/dev-cycle/t20/current-document-verification-20261011/repeatable/prepare-root.receipt.json`.
