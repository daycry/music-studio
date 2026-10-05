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
| Fase 4 — Medición y elección | 2 | 8 | 25% | 0 / 37h | 0 / 15h | 0 / 3.8h | 0 / — |
| **TOTAL** | **10** | **16** | **63%** | **— / 88h** | **— / 39.5h** | **— / 10h** | **— / —** |

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
- **Dependencias**: T-03, T-02
- **Tipo**: backend
- **Archivos**: `apps/engines/analysis/` (Dockerfile y adapters), `docker-compose.yml`
- **Verificación**:
  - `docker compose --profile engines build engine-analysis` → OK
  - `docker compose run --rm engine-analysis uv run pytest -m gpu -q` → verde: `audio.transcribe` sobre un audio de prueba devuelve texto y tiempos; `audio.clap` y `audio.aesthetics` devuelven puntuaciones; `audio.beats` devuelve BPM ±2 sobre un clic de 120 BPM

**Criterios de aceptación**
- [ ] Base `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime`, dependencias fijadas, puerto `127.0.0.1:8130`, y los mismos montajes y token que engine-acestep (contrato §6). `audio.beats` se declara con `device: cpu` (beat_this en CPU).
- [ ] Tareas `audio.transcribe` (Qwen3-ASR-1.7B), `audio.clap` (LAION, pesos convertidos), `audio.aesthetics` (Audiobox, `model.safetensors`) y `audio.beats` (beat_this, pesos convertidos). `audio.align_lyrics` (ForcedAligner) queda preparada pero no se verifica hasta M3.
- [ ] Un modelo cada vez en el proceso hijo; se cambia de modelo dentro del engine descargando el anterior.

### T-09 — Benchmark en la 5070

- **Descripción**: Números reales para decidir la configuración por defecto y el modo de alta calidad.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 2h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Dependencias**: T-07
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
- **Dependencias**: T-07
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
- **Dependencias**: T-07, T-08
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
- **Dependencias**: T-03, T-11
- **Tipo**: backend
- **Archivos**: `apps/engines/heartmula/`, `models/models.lock.json`, `docs/legal/licencias.md`
- **Verificación**:
  - `uv run pytest apps/engines/heartmula -m gpu -q` → conformidad básica en verde
  - `uv run scripts/eval/run.py --candidate heartmula-oss-3b` → 30 tomas

**Criterios de aceptación**
- [ ] Contenedor con las versiones de heartlib (`torch<2.11`, `bitsandbytes==0.49`, `transformers==4.57`) en **build cu128**, y el modelo oss-3B «happy-new-year» con el codec 20260123 en NF4/FP4.
- [ ] Mismo contrato `/v1`; la batería de T-11 se genera como candidato B.

### T-13 — Escucha y decisión de modelo

- **Descripción**: Sesión de escucha a ciegas y decisión registrada.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Supervisión**: est. 0.1h (≈25 % IA) · real —
- **Dependencias**: T-09, T-10, T-11 (y T-12 si se hizo)
- **Tipo**: docs
- **Archivos**: `eval/results/escucha-m0.md`, `docs/decisiones/ADR-0011-seleccion-de-modelos.md`, `docs/arquitectura/modelos.md`, `docs/memory/`
- **Verificación**:
  - lectura: `eval/results/escucha-m0.md` tiene las hojas completas, el mapa abierto solo al final y el veredicto según §5 del protocolo
  - lectura: ADR-0011 está en «aceptada (confirmada)» o sustituida por otra, y `modelos.md` recoge la configuración por defecto y la de alta calidad con los números de T-09

**Criterios de aceptación**
- [ ] Sesión con los umbrales fijados antes de escuchar.
- [ ] Veredicto: modelo aprobado / elección entre candidatos / replantear.
- [ ] Nota en `docs/memory/` con la decisión y la fecha.


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
