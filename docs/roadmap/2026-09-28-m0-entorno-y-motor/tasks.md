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
| Fase 2 — Cimientos compartidos | 0 | 3 | 0% | 0 / 26h | 0 / 13h | 0 / 3.3h | 0 / — |
| Fase 3 — Motor musical | 0 | 3 | 0% | 0 / 19h | 0 / 9.5h | 0 / 2.4h | 0 / — |
| Fase 4 — Medición y elección | 0 | 6 | 0% | 0 / 37h | 0 / 15h | 0 / 3.8h | 0 / — |
| **TOTAL** | **2** | **14** | **14%** | **0 / 88h** | **0 / 39.5h** | **0 / 10h** | **0 / —** |

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

**Estado**: borrador · **Estimado**: 26h · **Real**: —

### T-02 — `packages/weights`: lock, descarga verificada, auditor de pickle y herramientas

- **Descripción**: Descarga reproducible y segura de modelos y herramientas, según [ADR-0006](../../decisiones/ADR-0006-seguridad-de-pesos.md).
- **Estado**: borrador
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 4h · real —
- **Supervisión**: est. 1h (≈25 % IA) · real —
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `packages/weights/` (lock, verify, seal, audit_pickle, convert), `scripts/fetch_models.py`, `scripts/fetch_tools.py`, `models/models.lock.json`, `tools/tools.lock.json`, `packages/weights/tests/`
- **Verificación**:
  - `uv run pytest packages/weights -q` → todos en verde (hash correcto e incorrecto, sello, pickle tensorial convertido, pickle malicioso rechazado, `.py` remoto con hash distinto rechazado)
  - `uv run scripts/fetch_models.py --model ace-step-1.5 --check` → `OK` para todos los ficheros del lock
  - `uv run scripts/fetch_tools.py --check` → `ffmpeg win64-lgpl OK`

**Criterios de aceptación**
- [ ] `models.lock.json` registra, por modelo: repo HF, **revisión (commit)**, ficheros (ruta relativa, SHA-256, bytes, formato, licencia), el `.py` remoto con su hash y los pickle con el hash del original y el del convertido.
- [ ] El lock incluye:
  - ACE-Step 1.5: bundle con turbo, LM 1.7B, VAE y Qwen3-Embedding; repos separados de sft, base y LM 0.6B; XL-turbo como opcional;
  - Qwen3-ASR-1.7B, Qwen3-ForcedAligner-0.6B, LAION `larger_clap_music` (convertido desde `.bin`), Audiobox Aesthetics (`model.safetensors`) y beat_this (convertido desde `.ckpt`).
- [ ] Auditor y conversor **sin torch y sin `pickle.load`**: primero recorre los opcodes con `pickletools` y rechaza cualquier `GLOBAL`/`STACK_GLOBAL` que no esté en una **allowlist** (`torch._utils._rebuild_tensor_v2`, `torch.FloatStorage`/`HalfStorage`/`BFloat16Storage`, `collections.OrderedDict`, y para los `.ckpt` de Lightning también `builtins` inocuos). Después reconstruye los tensores con un intérprete propio (subclase de `pickle.Unpickler` con `find_class` restringido a la allowlist, que devuelve marcadores) más `numpy` sobre los storages del zip. En los `.ckpt` de Lightning extrae **solo** el `state_dict`. Escribe safetensors con `safetensors.numpy`.
- [ ] `fetch_models.py` es idempotente, calcula el hash completo al descargar y escribe el sello `.verified`. Usa `HF_HOME=models/.hf-cache`. **Estructura en disco:** `models/<model_id>/`; en ACE-Step, `models/ace-step-1.5/checkpoints/` replica la estructura que espera upstream (`ACESTEP_CHECKPOINTS_DIR`), con un subdirectorio por repo de HF (p. ej. `acestep-v15-turbo/`, `acestep-5Hz-lm-0.6B/`, `vae/`, `Qwen3-Embedding-0.6B/`). Los pickle convertidos sustituyen al original en su sitio, con la extensión `.safetensors`, y el original se borra.
- [ ] `fetch_tools.py` descarga ffmpeg BtbN `win64-lgpl` a `tools/ffmpeg/` y lo verifica con el lock.

### T-03 — `packages/engine-contract` + `apps/engines/common` + `engine-mock`

- **Descripción**: El contrato `/v1` de [contrato-engines.md](../../arquitectura/contrato-engines.md) como código compartido, el servidor base de cualquier engine y el mock. Al cerrar esta tarea **el contrato queda congelado**.
- **Estado**: borrador
- **Tiempo humano**: est. 12h · real —
- **Tiempo IA (ejec.)**: est. 6h · real —
- **Supervisión**: est. 1.5h (≈25 % IA) · real —
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivos**: `packages/engine-contract/` (JobRequest, Event, Telemetry, ModelDescriptor, códigos de error), `packages/contracts/engine-v1.json` (generado), `scripts/export_contracts.py`, `apps/engines/common/` (servidor FastAPI `/v1`, supervisor del proceso hijo, VramGuard, CancelToken, token interno), `apps/engines/mock/`, tests
- **Verificación**:
  - `uv run pytest packages/engine-contract apps/engines/common apps/engines/mock -q` → verde
  - `uv run scripts/export_contracts.py --check` → `engine-v1.json up to date`
  - `uv run pytest -q tests/test_no_pickle.py` → verde (búsqueda por **AST** de llamadas a `torch.load`, `pickle.load(s)` y `Unpickler` en `apps/` y `packages/`; permitido solo lo listado en `tests/no_pickle_allowlist.txt` con su motivo: el `Unpickler` restringido del auditor)

**Criterios de aceptación**
- [ ] Modelos Pydantic compatibles con Python 3.11 y 3.12, sin torch. `engine-v1.json` se genera a partir de ellos y un test comprueba que coincide con el versionado.
- [ ] Servidor `/v1` con: health (incluye `contract_version`), models, load, unload, estimate, `jobs` (`202`/`409 BUSY`), `GET jobs/{id}`, eventos NDJSON con `seq` y reenganche mediante `?after=`, y `DELETE`. Exige `X-Studio-Engine-Token`.
- [ ] El modelo corre en un **proceso hijo**; `unload` lo termina. El proceso padre no importa torch y lee la VRAM total y libre con **NVML** (`nvidia-ml-py`). `POST /v1/jobs` carga el modelo de forma implícita si no está cargado (evento `stage: loading_model`).
- [ ] VramGuard: `cap = free − STUDIO_VRAM_MARGIN_MB` al cargar; registra `vram_peak_mb` y `spilled`; excederlo devuelve `VRAM_EXCEEDED`. Tests con una GPU simulada.
- [ ] Cancelación cooperativa que limpia `data/tmp/<job_id>/`. Evento terminal único (`done`, `error` o `cancelled`).
- [ ] `engine-mock` implementa **todas las tareas del catálogo** ([contrato-engines.md](../../arquitectura/contrato-engines.md) §5), cada una con su salida sintética: audio en barrido de 48 kHz con la duración pedida, `delta` de texto en streaming con letra etiquetada, PNG, MP4 y JSON. Declara todas las features, pone `audio.beats` con `device: cpu` y admite `MOCK_STAGE_DELAY_MS` y las directivas `@mock:fail=`, `@mock:fail_once=` y `@mock:retryable` (§7).

### T-04 — `packages/audio-post` + manifiesto v1 + verificador

- **Descripción**: El post-proceso y el manifiesto que usarán el CLI (M0) y el worker del server (M1), según [pipeline-audio.md](../../arquitectura/pipeline-audio.md) y [datos.md](../../arquitectura/datos.md) §3.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-02 (ffmpeg en `tools/`)
- **Tipo**: backend
- **Archivos**: `packages/audio-post/`, `packages/contracts/manifest-v1.schema.json`, `packages/contracts/manifest_writer` (en `audio-post` o paquete propio), `scripts/verify_manifest.py`, tests
- **Verificación**:
  - `uv run pytest packages/audio-post -q` → verde
  - `uv run scripts/verify_manifest.py packages/contracts/examples/` → `all valid`

**Criterios de aceptación**
- [ ] Validación de duración (±5 %), NaN/Inf, silencio (RMS > −60 dBFS) y clipping sostenido.
- [ ] `master.flac` (24 bit, frecuencia nativa, **sin normalizar**) y `listen.mp3` (320 kbps), llevado a −14 LUFS ±0,5 mediante **ganancia lineal**, con **true peak ≤ −1 dBTP medido con ffmpeg `ebur128=peak=true`**. Si hace falta, limitador, que queda anotado en `post`.
- [ ] `peaks.json` con ~2.000 pares min/max por canal.
- [ ] `manifest-v1.schema.json` con todos los campos de datos.md §3, más ejemplos: `audio_take`, `cli_run`, `image` y proveedor externo. El escritor calcula `commercial_use` como AND de todo lo usado.
- [ ] `verify_manifest.py` valida el esquema y los hashes de las salidas, e ignora campos desconocidos.

---

## Fase 3 — Motor musical

**Estado**: borrador · **Estimado**: 19h · **Real**: —

### T-05 — Imagen `engine-acestep` para sm_120

- **Descripción**: El contenedor del motor musical con las versiones de [entorno.md](../../arquitectura/entorno.md) §2.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 3h · real —
- **Supervisión**: est. 0.8h (≈25 % IA) · real —
- **Dependencias**: T-03
- **Tipo**: devops
- **Archivos**: `apps/engines/acestep/Dockerfile`, `apps/engines/acestep/pyproject.toml`, `docker-compose.yml` (perfil `engines`)
- **Verificación**:
  - `docker compose --profile engines build engine-acestep` → build OK
  - `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q` → verde (tests del adapter **dentro** del contenedor)
  - `docker compose run --rm engine-acestep python -c "import torch;assert 'sm_120' in torch.cuda.get_arch_list();a=torch.ones(64,64,device='cuda',dtype=torch.bfloat16);print((a@a).sum().item())"` → `262144.0`
  - `docker compose run --rm engine-acestep sh -c "ffmpeg -buildconf | grep -c -e enable-gpl -e enable-nonfree"` → `0`

**Criterios de aceptación**
- [ ] Base `nvidia/cuda:12.8.1-runtime-ubuntu22.04`, Python 3.11 instalado con `uv python install` y el repo de ACE-Step 1.5 fijado a un tag o commit, instalado con `uv sync --frozen --no-dev`.
- [ ] ffmpeg BtbN `linux64-lgpl-shared`, con las `.so` en `LD_LIBRARY_PATH`. `-buildconf` incluye lame, soxr y opus.
- [ ] La imagen copia e instala `packages/engine-contract` y `apps/engines/common` en su entorno Python 3.11. Mounts según [contrato-engines.md](../../arquitectura/contrato-engines.md) §6: `models/`→`/models` y `data/`→`/data` en solo lectura, y `data/tmp/`→`/data/tmp` en lectura/escritura. Variables: `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `ACESTEP_LM_BACKEND=pt`, `ACESTEP_CHECKPOINTS_DIR`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` y el token del engine.
- [ ] Puerto publicado como `127.0.0.1:8101:8101`. Sin xformers ni flash-attn. El log de arranque indica la atención (SDPA) y la versión de torch.

### T-06 — Adapter ACE-Step (`music.song`, `music.instrumental`)

- **Descripción**: Envolver la **API Python** de ACE-Step (el handler, no la REST) detrás del contrato `/v1`, con los modos forzados para el tier 4.
- **Estado**: borrador
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 5h · real —
- **Supervisión**: est. 1.3h (≈25 % IA) · real —
- **Dependencias**: T-05
- **Tipo**: backend
- **Archivos**: `apps/engines/acestep/adapter.py`, `apps/engines/acestep/descriptor.py`, `apps/engines/acestep/patches/`, tests `gpu`
- **Verificación**:
  - `docker compose run --rm engine-acestep uv run pytest -m "not gpu" -q` → verde
  - `docker compose run --rm engine-acestep uv run pytest -m gpu -q` → verde (30 s de audio, 48 kHz estéreo, sin NaN ni silencio; telemetría completa; `unload` libera la VRAM)

**Criterios de aceptación**
- [ ] `load` carga DiT, LM, VAE y text encoder desde `models/ace-step-1.5/`. **Modos forzados**: bf16, sin offload, sin INT8 y sin `torch.compile`, además del modo `offload`. El checkpoint y el LM (0.6B por defecto) se eligen por configuración, **sin fiarse del tier automático**.
- [ ] Parche documentado para que `silence_latent` se lea del safetensors convertido. Si aparecen otros `torch.load` en el camino de carga (I-04), se parchean igual y se añaden al test.
- [ ] `generate` acepta letra con etiquetas, estilo, duración, semilla, `vocal_language` (por defecto el de la canción, **no** `"en"`), BPM y tonalidad (si el upstream los expone) y `n_outputs`. Emite etapas y progreso reales, lo más fino que permita la API (I-03), y respeta la cancelación.
- [ ] Escribe WAV float32 con **soundfile** a partir del tensor en memoria, sin usar `torchaudio.save`.
- [ ] Descriptor con licencia MIT, `training_data` literal, `remote_code` con sus hashes y las tareas `music.song` y `music.instrumental` (con sus features: `negative_prompt`, `bpm`, `key`, `timbre_ref`, `lora`) en `verified: false` hasta T-10. El CLI de T-07 funciona con `STUDIO_ALLOW_UNVERIFIED=1`.

### T-07 — CLI `scripts/generate.py`: primera canción 🎯

- **Descripción**: CLI que hace de «server» para M0: llama al engine, ejecuta audio-post y escribe el manifiesto. Hito: la **primera canción** del proyecto.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Supervisión**: est. 0.3h (≈25 % IA) · real —
- **Dependencias**: T-04, T-06
- **Tipo**: backend
- **Archivos**: `scripts/generate.py`, `eval/briefs/B-02.txt`, `eval/briefs/briefs.yaml` (solo B-02)
- **Verificación**:
  - `uv run scripts/generate.py --brief B-02 --seed 1` → carpeta en `data/cli/<fecha>/<run_id>/` con 4 ficheros (la letra, el estilo, la duración y el idioma se leen de `eval/briefs/briefs.yaml`)
  - `uv run scripts/verify_manifest.py data/cli/` → `all valid`
  - lectura: se escucha la canción y se anotan en el ledger el tiempo total, `vram_peak_mb` y una primera impresión

**Criterios de aceptación**
- [ ] Letra de **B-02** escrita por el propietario, con su prompt de estilo, según [evaluacion-escucha.md](../../calidad/evaluacion-escucha.md) §4.
- [ ] El CLI acepta dos formas: `--brief <ID>` (lee `eval/briefs/briefs.yaml` y `eval/briefs/<ID>.txt`) o `--lyrics <fichero> --style "…" --duration <s> --language <xx>`. Opcionales: `--seed`, `--variants`, `--task music.instrumental` y `--engine` (por defecto, `STUDIO_ENGINES`). Envía el token. Muestra el progreso por eventos y deja `master.flac`, `listen.mp3`, `peaks.json` y `manifest.json` (`kind: cli_run`).
- [ ] **Hito cumplido**: B-02 de 3:00 en castellano generado y escuchado.

---

## Fase 4 — Medición y elección

**Estado**: borrador · **Estimado**: 37h · **Real**: —

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
