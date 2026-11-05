---
documento: entorno
titulo: Entorno de desarrollo y ejecución
estado: vigente
fecha: 2026-09-28
actualizado: 2026-11-06
fuentes-verificadas: 2026-11-06
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
| **engine-analysis** | `pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime` + dependencias fijadas con uv | Base fijada por digest en [su Dockerfile](../../apps/engines/analysis/Dockerfile); no expresa cuál es la última versión disponible |
| **engine-comfy** | Objetivo: ComfyUI fijado por commit, CUDA y `--disable-pinned-memory`; no implementado en el Compose actual | Integración futura según [ADR-0016](../decisiones/ADR-0016-comfyui-como-motor-de-imagen-y-video.md); M2/M3 congelados por [ADR-0089](../decisiones/ADR-0089-reencauce-tras-codex.md). Base, kernels y VRAM pendientes de validar |
| **engine-llm** | Adaptador Docker `/v1`, sin inferencia propia, hacia Ollama compartido en Ubuntu WSL2; implementación M2 pendiente | Modelo y conectividad privada a validar ([ADR-0035](../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md)) |
| **NGC `nvcr.io/nvidia/pytorch`** | No se usa | Su `/etc/pip/constraint.txt` choca con los repos que fijan versión de torch |
| **server / engine-mock** | Python **3.12.14**, uv **0.12.19**, bases fijadas por digest en [apps/server/Dockerfile](../../apps/server/Dockerfile); perfil `studio` de Compose | Sin torch ni GPU; server con worker CPU, mock con audio simulado |
| **web** | Node **22.23.2**, pnpm fijado por el proyecto; [apps/web/Dockerfile](../../apps/web/Dockerfile) | Despliegue Docker del perfil `studio` |
| **ffmpeg (server)** | BtbN `linux64-lgpl` **n9.0.2-17-g2a571b6068**, revisión y SHA-256 en [tools/ffmpeg-linux.lock.json](../../tools/ffmpeg-linux.lock.json); preparación con `scripts/fetch_ffmpeg_linux.py --download` y copia/verificación en el Dockerfile del server. `win64-lgpl` queda para utilidades nativas | FFmpeg Linux y medios reales probados en la [QA Docker T-15](../roadmap/2026-09-28-m1-mvp-estudio/testing/docker-ui-2026-11-05.md). El lock conserva metadatos históricos de candidato (`runtime_verified: false`); la evidencia de ejecución está en los informes |
| **ffmpeg (engines)** | BtbN `linux64-lgpl-shared` (7.x) con sus `.so` en `LD_LIBRARY_PATH` | torchcodec necesita las **librerías compartidas** de FFmpeg 4–8. El ffmpeg de apt y las builds estáticas de johnvansickle son GPL |

**Comprobaciones por tipo de imagen:**

- Solo en imágenes GPU que incluyen torch: `python -c "import torch; assert 'sm_120' in torch.cuda.get_arch_list()"`, más una multiplicación de matrices en BF16 en la GPU durante su validación. No corresponde a web, server ni mock; estos últimos no deben incorporar torch para superar una comprobación GPU.
- En imágenes que incorporan FFmpeg, `ffmpeg -buildconf`:
  - **incluye** `--enable-libmp3lame`, `--enable-libsoxr` y `--enable-libopus`;
  - **no incluye** `--enable-gpl` ni `--enable-nonfree`.

Ollama permanece como servicio compartido en Ubuntu WSL2; el adaptador no instala otra instancia ni gestiona su servicio. La ruta privada Docker→WSL2 se valida en M2. Docker Desktop utiliza WSL2 como backend: ComfyUI en Docker ya corre en Linux sobre WSL2, con CUDA prevista para la RTX y validación pendiente ([ADR-0035](../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md)).

**Herramientas frontend de desarrollo:** [ADR-0048](../decisiones/ADR-0048-herramientas-frontend-portatiles.md) fija Node 22.23.2/pnpm 9.12.0 portátiles bajo `tools/`, con extracción/hash y cachés confinadas. En Windows, `scripts/bootstrap.ps1` prepara las herramientas con el Python gestionado y `scripts/fetch_web_tools.py` antes de instalar dependencias; los pins están en su constante `PINS`. El launcher conserva la comprobación de solo lectura (`check=True`) y las verificaciones de hashes. El [arranque desde un clon nuevo del 2026-11-06](../roadmap/2026-09-28-m1-mvp-estudio/testing/readme-arranque-2026-11-06.md) verificó Python 3.12.14, Node 22.23.2 y pnpm 9.12.0, seguido de una corrida integrada CPU/mock de 14/14. La web de producto continúa en Docker; el pin portable de Node para el launcher Linux sigue pendiente y no se deduce de esta prueba Windows. Lock transitivo e imagen Linux se verifican por separado.

## 3. Problemas conocidos en sm_120, WSL2 y Docker (y qué hacer)

| # | Problema | Mitigación |
|---|---|---|
| E-01 | **Desbordamiento silencioso de VRAM a RAM.** En WSL2 el driver no respeta la «CUDA sysmem fallback policy» | Tope por proceso calculado a partir de la VRAM **libre** menos un margen de 512 MB (no una fracción fija). Registrar el pico y marcar `spilled` ([contrato-engines.md](./contrato-engines.md) §1). `MAX_CUDA_VRAM` de ACE-Step **no** sirve como tope: solo lo aplica si el valor es menor que la VRAM física |
| E-02 | Memoria *pinned* limitada en WSL2 | `pin_memory=False` si falla el offload; `--disable-pinned-memory` en ComfyUI |
| E-03 | Límite de RAM y recuperación de caché de WSL2 | `%UserProfile%\.wslconfig`: `memory=16GB`, `swap=8GB`; `[experimental] autoMemoryReclaim=dropCache`. Perfil aplicado y comprobado el 2026-10-05; sustituye los 24/16 GB de T-00 ([ADR-0025](../decisiones/ADR-0025-limite-de-memoria-wsl.md)) |
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
| E-16 | **Otros procesos en la GPU.** El stack `knowledge-graphs` (Ollama con `qwen3.5:9b`, ≈ 8,9 GB) ocupa la VRAM mientras Kwipu indexa o responde: el 2026-09-28 la 5070 marcaba 11.621 de 12.227 MiB en uso | Observar primero `ollama ps`; descargar solo los modelos que impiden el turno sin parar el servicio ni borrar pesos; comprobar VRAM usada ≤ ~1,6 GB. Al terminar restaurar solo lo observado y descargado por esta operación; si estaba vacío, dejarlo vacío. Comprobar interferencias de consumidores ajenos sin prometer exclusión global ([ADR-0022](../decisiones/ADR-0022-memoria-tecnica-kwipu-graphiti.md), [ADR-0035](../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md)) |
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
| `tools/` (FFmpeg nativo) | `tools/tools.lock.json` | `uv run scripts/fetch_tools.py` |
| `tools/ffmpeg-linux/` (server Docker) | `tools/ffmpeg-linux.lock.json` | `uv run --frozen --no-sync scripts/fetch_ffmpeg_linux.py --download`, antes del build |
| `.cache/uv`, `.cache/pnpm` | — (son cachés de descarga) | Se rellenan solas |
| `data/db/` | `data/backups/` (copia diaria) | Restaurar el último `.backup` |

Los tres primeros los rehace de una vez `.\scripts\bootstrap.ps1` en Windows, incluida la preparación de Node/pnpm portátiles. El launcher Linux sigue bloqueado hasta disponer de un pin de Node Linux verificado; `bootstrap.sh` no ofrece actualmente el bootstrap web en WSL/Linux. `.venv/` tampoco se sincronizaría aunque se pudiera: guarda rutas absolutas y binarios de esta máquina, así que no es portable, y cada `uv sync` reescribe miles de ficheros.

## 5. Puesta en marcha de M1 y laboratorio M0

El perfil `studio` de [docker-compose.yml](../../docker-compose.yml) arranca web, server y mock CPU, sin GPU ni Ollama. Sigue el [primer arranque del README](../../README.md#primer-arranque) y la [receta de ámbito privado](../calidad/pruebas.md#preparar-el-ámbito-privado-y-ejecutar-la-suite): bootstrap Windows, inicialización del token, preparación de FFmpeg Linux y selección explícita de proyecto Compose, entorno y datos bajo `.cache/`, antes de `scripts/e2e_stack.py up`. No ejecutes una segunda QA sobre los mismos puertos ni abras SQLite viva desde Windows.

La [QA Docker T-15](../roadmap/2026-09-28-m1-mvp-estudio/testing/docker-ui-2026-11-05.md) obtuvo 14/14 en tres corridas, con HTTP/SSE, persistencia, recuperación, FFmpeg, `Range` y descargas. El [arranque T-16 del 2026-11-06](../roadmap/2026-09-28-m1-mvp-estudio/testing/readme-arranque-2026-11-06.md) verificó un clon nuevo sin copiar herramientas ni cachés, una corrida integrada 14/14 y 103/103 pruebas host separadas; Docker reutilizó capas normales. Este recorrido usa audio simulado y no cierra la aceptación de M1 con ACE-Step real y escucha del propietario.

El siguiente bloque es solo el laboratorio GPU de M0. Requiere pesos preparados y cumplir previamente la política de GPU/Ollama de §3; no es la receta CPU/mock anterior. Inicializa el token antes de resolver o arrancar Compose:

```powershell
# Requisitos: Docker Desktop (WSL2), uv, git; entorno gestionado preparado; GPU disponible según §3
. .\scripts\env.ps1                               # intérprete, cachés y .venv dentro de la carpeta
uv run scripts/init_env.py                          # .env + STUDIO_ENGINE_TOKEN (una vez)
uv run scripts/fetch_tools.py                       # ffmpeg LGPL para utilidades nativas
uv run scripts/fetch_models.py --model ace-step-1.5 # descarga fijada por revisión, verificada y convertida
docker compose --profile engines up -d engine-acestep engine-analysis
uv run scripts/generate.py --brief B-02              # M0: primera canción
```

El Compose actual no incluye `engine-llm` ni `engine-comfy`. Ollama no es requisito del MVP M1; la conectividad privada y convivencia del adaptador se validarán en M2, actualmente congelado junto con M3 por ADR-0089. Los comandos nativos siguen disponibles para desarrollo.

## Almacenamiento operativo

[ADR-0089](../decisiones/ADR-0089-reencauce-tras-codex.md) aparca el VHDX ext4 y el journal Windows de ADR-0069/0075. Los datos viven en `data/`, montado en los contenedores. Cada take se publica así:

1. Se escribe en un directorio de staging.
2. Se mueve con `rename` normal a `data/songs/<song_id>/<take_ulid>/`. El id es único, así que no hay colisión y no hace falta `NOREPLACE`.
3. Se confirma la fila en SQLite. Esa fila es la autoridad: un directorio sin fila es huérfano y se limpia al arrancar.
