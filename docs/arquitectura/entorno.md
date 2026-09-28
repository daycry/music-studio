---
documento: entorno
titulo: Entorno de desarrollo y ejecución
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
fuentes-verificadas: 2026-09-28
---

# Entorno

## 1. Máquina de referencia (medida el 2026-09-28)

| Elemento | Valor |
|---|---|
| SO | Windows 11 Home (10.0.26200) |
| GPU | **NVIDIA GeForce RTX 5070**: 12.227 MiB (11,94 GiB), compute capability **12.0 (sm_120, Blackwell)** |
| VRAM libre con el escritorio abierto | ~10,7 GB (Windows usa ~1,5 GB) |
| Driver | 616.92 (rama R615, CUDA UMD 13.4) |
| Docker | Docker Desktop, engine 29.8.0 (Linux, backend WSL2) |
| CPU / RAM | AMD Ryzen 7 9800X3D · **32 GB**. Va justo para descargar a RAM los modelos de vídeo de 14B; se recomiendan 64 GB si se usa mucho N2/N3 ([video.md](./video.md) §5) |
| Disco | C: con ~626 GB libres. La carpeta del proyecto y el VHDX de Docker están en C: |

**Tier de ACE-Step:** `acestep/gpu_config.py` calcula `total_memory / 1024³ = 11,94`, así que la 5070 queda en el **tier 4 (≤ 12 GiB)**. Por defecto, ese tier implica LM 0.6B, INT8, offload y `torch.compile`. El adapter **fuerza los modos de forma explícita** en lugar de fiarse de la detección automática ([ADR-0007](../decisiones/ADR-0007-gpu-local-12gb.md)).

## 2. Versiones fijadas

| Pieza | Versión | Motivo |
|---|---|---|
| **engine-acestep** | Base `nvidia/cuda:12.8.1-runtime-ubuntu22.04`, Python **3.11** instalado con `uv python install`, repo de ACE-Step 1.5 **fijado a un tag o commit** e instalado con `uv sync --frozen --no-dev` → `torch==2.10.0+cu128`, `torchaudio==2.10.0+cu128`, `transformers>=4.51,<4.58`, `torchao>=0.16,<0.17`, `torchcodec>=0.9.1` | Es lo que fija upstream para Linux x86_64. Ubuntu 24.04 no trae Python 3.11 en apt. La variante cudnn sobra porque torch ya incluye cuDNN |
| Imagen oficial `ghcr.io/ace-step/ace-step-1.5:0.1.8` | **Solo como referencia**, no se usa | Carga por defecto el LM 4B (OOM en 12 GB) y trae el ffmpeg GPL de apt |
| **engine-analysis** | `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime` + dependencias fijadas con uv | PyTorch 2.14.0 (2 de septiembre de 2026) es la versión estable actual. Desde la 2.12 no hay ruedas cu128; las cu126 no traen sm_120 |
| **engine-comfy** | ComfyUI fijado por commit sobre `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime` (cu130), con `--disable-pinned-memory` | NVFP4 solo rinde con cu130; la memoria *pinned* da problemas en WSL2 ([ADR-0016](../decisiones/ADR-0016-comfyui-como-motor-de-imagen-y-video.md)) |
| **engine-llm** | llama.cpp (build CUDA con sm_120) fijado por tag | GGUF de Gemma 4 ([ADR-0012](../decisiones/ADR-0012-llm-de-letras.md)) |
| **NGC `nvcr.io/nvidia/pytorch`** | No se usa | Su `/etc/pip/constraint.txt` choca con los repos que fijan versión de torch |
| **server** | Python 3.12, uv | Sin torch |
| **web** | Node 22 LTS, pnpm | |
| **ffmpeg (server)** | BtbN `win64-lgpl` (≥ 7.1), en `tools/ffmpeg/` y fijado en `tools/tools.lock.json` | Post-proceso, render y exportaciones ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)) |
| **ffmpeg (engines)** | BtbN `linux64-lgpl-shared` (7.x) con sus `.so` en `LD_LIBRARY_PATH` | torchcodec necesita las **librerías compartidas** de FFmpeg 4–8. El ffmpeg de apt y las builds estáticas de johnvansickle son GPL |

**Comprobaciones obligatorias al construir cada imagen:**

- `python -c "import torch; assert 'sm_120' in torch.cuda.get_arch_list()"`, más una multiplicación de matrices en BF16 en la GPU.
- `ffmpeg -buildconf`:
  - **incluye** `--enable-libmp3lame`, `--enable-libsoxr` y `--enable-libopus`;
  - **no incluye** `--enable-gpl` ni `--enable-nonfree`.

## 3. Problemas conocidos en sm_120, WSL2 y Docker (y qué hacer)

| # | Problema | Mitigación |
|---|---|---|
| E-01 | **Desbordamiento silencioso de VRAM a RAM.** En WSL2 el driver no respeta la «CUDA sysmem fallback policy» | Tope por proceso calculado a partir de la VRAM **libre** menos un margen de 512 MB (no una fracción fija). Registrar el pico y marcar `spilled` ([contrato-engines.md](./contrato-engines.md) §1). `MAX_CUDA_VRAM` de ACE-Step **no** sirve como tope: solo lo aplica si el valor es menor que la VRAM física |
| E-02 | Memoria *pinned* limitada en WSL2 | `pin_memory=False` si falla el offload; `--disable-pinned-memory` en ComfyUI |
| E-03 | WSL2 usa por defecto el 50 % de la RAM | `%UserProfile%\.wslconfig`: `memory=24GB`, `swap=16GB` (M0 T-00) |
| E-04 | Instalar un driver NVIDIA de Linux dentro de WSL2 | No hacerlo. WSL2 usa el driver de Windows |
| E-05 | flash-attn: FA3 no funciona en sm_120; FA4 tiene errores en varlen | SDPA por defecto. ACE-Step no necesita flash-attn en Linux |
| E-06 | xformers puede degradar torch a una build sin sm_120 | No usarlo, o instalar con `--no-deps` |
| E-07 | `torchaudio.save` delega en torchcodec, que necesita las librerías compartidas de FFmpeg (issue #1078 de ACE-Step: `libnvrtc.so.13` con cu128) | ffmpeg `lgpl-shared` en la imagen. El **adapter recibe el tensor en memoria y lo escribe con `soundfile`**, sin pasar por el guardado de upstream |
| E-08 | Backend vLLM de ACE-Step con torch 2.10: segfault (issue #135) | `ACESTEP_LM_BACKEND=pt` |
| E-09 | Triton y `torch.compile` en sm_120: segfaults puntuales. El tier 4 de ACE-Step activa compile por defecto | Desactivar compile en el adapter. Probarlo solo como experimento de M0 T-09 |
| E-10 | FP8/NVFP4 sin kernels validados en sm_120 | No usar en los engines de audio. En ComfyUI, solo si lo valida el spike de M4 |
| E-11 | Fragmentación de VRAM | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (verificar en WSL2) |
| E-12 | Lectura lenta de `models/` a través del bind mount de Windows | Medir en M0 T-09 ([ADR-0005](../decisiones/ADR-0005-todo-en-la-carpeta.md)) |
| E-13 | Liberar un modelo en torch no libera el contexto CUDA (0,3–0,5 GB) | Modelo en un **proceso hijo** que se termina al descargar ([ADR-0007](../decisiones/ADR-0007-gpu-local-12gb.md)) |
| E-14 | Docker publica los puertos en `0.0.0.0` | `127.0.0.1:P:P` en compose ([ADR-0020](../decisiones/ADR-0020-seguridad-local.md)) |
| E-16 | **Otros procesos en la GPU.** El stack `knowledge-graphs` (Ollama con `qwen3.5:9b`, ≈ 8,9 GB) ocupa la VRAM mientras Kwipu indexa o responde: el 2026-09-28 la 5070 marcaba 11.621 de 12.227 MiB en uso | Antes de medir o generar con GPU: `wsl -d Ubuntu -e ollama stop <modelo>` (sin parar el servicio ni borrar el modelo) y comprobar con `nvidia-smi` que la VRAM usada es ≤ ~1,6 GB. Después, `ollama run <modelo>` para volver a cargarlo ([ADR-0022](../decisiones/ADR-0022-memoria-tecnica-kwipu-graphiti.md)) |
| E-15 | Las cachés de HF, uv y pnpm van por defecto a `%USERPROFILE%` y duplican gigas | Variables `HF_HOME`, `UV_CACHE_DIR`, `npm_config_store_dir` y `TORCH_HOME` apuntando dentro de la carpeta ([convenciones.md](./convenciones.md) §4) |

## 4. Sincronización con Synology Drive

La carpeta está sincronizada con Synology Drive. **Antes de crear `.venv`, `node_modules`, `models/` o `data/` (M0 T-00)**, configura en Synology Drive → Tarea de sincronización → **Filtro de sincronización** lo que indica [ADR-0005](../decisiones/ADR-0005-todo-en-la-carpeta.md):

- **Excluir:** `data/db`, `data/tmp`, `data/cli`, `data/logs`, `data/trash`, `models`, `tools`, `.cache`, `node_modules`, `.venv`, `.next`, `eval/takes`, `eval/capabilities`.
- **Sincronizar:** el código, `docs/`, `data/songs`, `data/characters`, `data/uploads` y `data/backups` (la biblioteca y la copia diaria de la base de datos).

**¿Cómo se recupera lo excluido?** No se pierde nada: se sincronizan las **recetas**, no los resultados, y todo lo excluido se regenera desde ellas.

| Excluido (resultado) | Receta (versionada en git y sincronizada) | Cómo se reconstruye |
|---|---|---|
| `.cache/uv/python/` (intérprete) | `.python-version`, `uv.toml` | `uv python install` |
| `.venv/` (paquetes Python) | `pyproject.toml` + `uv.lock` (versión y hash de cada paquete) | `uv sync --frozen` |
| `node_modules/` | `package.json` + `pnpm-lock.yaml` | `pnpm install --frozen-lockfile` |
| `models/` | `models/models.lock.json` (repo, revisión, SHA-256) | `uv run scripts/fetch_models.py` |
| `tools/` (ffmpeg) | `tools/tools.lock.json` | `uv run scripts/fetch_tools.py` |
| `.cache/uv`, `.cache/pnpm` | — (son cachés de descarga) | Se rellenan solas |
| `data/db/` | `data/backups/` (copia diaria) | Restaurar el último `.backup` |

Los tres primeros los rehace de una vez `.\scripts\bootstrap.ps1` (o `source scripts/bootstrap.sh`). `.venv/` tampoco se sincronizaría aunque se pudiera: guarda rutas absolutas y binarios de esta máquina, así que no es portable, y cada `uv sync` reescribe miles de ficheros.

## 5. Puesta en marcha (objetivo al final de M0 y M1)

```powershell
# Requisitos (M0 T-00): Docker Desktop (WSL2), Node 22, pnpm, uv, git; .wslconfig; filtro de Synology
. .\scripts\env.ps1                               # intérprete, cachés y .venv dentro de la carpeta
uv run scripts/fetch_tools.py                       # ffmpeg LGPL del server en tools/
uv run scripts/fetch_models.py --model ace-step-1.5 # descarga fijada por revisión, verificada y convertida
docker compose --profile engines up -d engine-acestep engine-analysis
uv run scripts/init_env.py                          # .env + STUDIO_ENGINE_TOKEN (una vez)
uv run scripts/generate.py --brief B-02              # M0: primera canción
# M1:
cd apps/server; uv run alembic upgrade head; uv run fastapi dev --host 127.0.0.1
cd apps/web; pnpm dev
```
