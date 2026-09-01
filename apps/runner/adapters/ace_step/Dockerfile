# =============================================================================
# Imagen del runner GPU de ACE-Step 1.5 — T-05 (Fase 0, contenerizacion minima)
# =============================================================================
# Es la imagen que ejecutan, en este orden: T-03 (tiempos, VRAM y arranque en
# frio), T-04 (dos inferencias concurrentes), T-09 (las 10 pistas del gate G1)
# y, mucho mas adelante, T-85 (proveedor GPU local de produccion). En Fase 0 se
# invoca **directo** con `docker run --gpus all`: aqui no hay abstraccion de
# proveedor (T-85), ni API de plataforma (T-11), ni registry (T-30).
#
# QUE NO LLEVA ESTA IMAGEN, Y POR QUE
# -----------------------------------
# * **Los pesos no viajan dentro.** Se montan como volumen de solo lectura en
#   `/weights`. Esa es exactamente la propiedad que hace **medible el arranque
#   en frio de T-03**: si el artefacto de 6,16 GB estuviese en una capa, el
#   `docker pull` y la carga del modelo quedarian mezclados en un unico numero
#   y S-01/S-01b dejarian de ser medibles por separado. Ademas mantiene la
#   imagen reconstruible sin mover 6 GB y deja los pesos fuera del registro.
# * **Ninguna credencial** (D-15). No hay ARG ni ENV de secreto, no se copia
#   ningun `.env`/`.netrc`/clave, y `Dockerfile.dockerignore` los excluye del
#   contexto de build por si acaso. El contenedor **no necesita red de salida**
#   para generar (por eso los flags `*_OFFLINE=1` de mas abajo).
# * **Ningun `pickle`** (D-14). La unica puerta de entrada de pesos es
#   `safetensors`; `contracts.assert_safetensors()` lo comprueba antes de abrir
#   el fichero. El `.pt` en cuarentena (el latente de silencio) NO se monta
#   aqui: solo lo toca el fusor offline, que extrae los bytes crudos del ZIP sin
#   ejecutar opcodes.
# * **Nada de `trust_remote_code` / `auto_map`.** Los `.py` de upstream se
#   vendorizan revisados en `adapters/ace_step/vendor/` (trabajo de T-03); no se
#   descargan ni se ejecutan desde el hub.
#
# CONSTRUIR Y EJECUTAR
# --------------------
#   # contexto de build = apps/runner (NO la raiz del repo: el adapter solo
#   # necesita contracts.py, spikes/_timing.py, spikes/_mock.py y adapters/)
#   docker build -t ace-step-runner:t05 \
#       -f apps/runner/adapters/ace_step/Dockerfile apps/runner
#
#   docker run --gpus all --rm ace-step-runner:t05 probe
#   docker run --gpus all --rm -v D:\srv\ace-step\artifacts:/weights:ro \
#       ace-step-runner:t05 generate --duration 30
#
# PRECONDICION OPERATIVA DE ESTA MAQUINA (no es del repositorio, pero sin ella
# no hay build): Docker Desktop guarda sus datos en C:, que esta al 98 % (~5 GB
# libres). Esta imagen ronda los 8-9 GB descomprimida. Hay que **reubicar el
# data-root de WSL2 a D:** antes del primer build; si no, el build fallara a
# mitad y ademas dejara la maquina sin disco de sistema.
#
# BUILDKIT REQUERIDO. El fichero de exclusiones se llama
# `Dockerfile.dockerignore` y no `.dockerignore` **a proposito**: Docker solo
# lee `.dockerignore` en la **raiz del contexto** (aqui `apps/runner`), asi que
# un `.dockerignore` en esta carpeta seria decorativo. BuildKit, en cambio, si
# busca `<ruta-del-dockerfile>.dockerignore`, que es el unico nombre que hace
# efecto teniendo el Dockerfile en un subdirectorio del contexto. Docker 29.7.2
# usa BuildKit por defecto; no fuerces `DOCKER_BUILDKIT=0` o el contexto se
# enviara entero.
#
# TRAMPA MEDIDA (2026-09-01): NO anadas ademas un `.dockerignore` en la raiz del
# contexto (`apps/runner/.dockerignore`) "por si acaso". Se hizo, y BuildKit lo
# SOMBREA en silencio: manda `Dockerfile.dockerignore` y el otro no se aplica
# nunca. El resultado es el peor de los dos mundos: dos ficheros con reglas
# distintas, uno muerto, y nadie avisando de cual esta en vigor. Se elimino.
# =============================================================================


# -----------------------------------------------------------------------------
# 1. BASE: la eleccion la manda PASCAL, no la moda
# -----------------------------------------------------------------------------
# Hardware objetivo: GTX 1070 (GP104, **sm_61**, sin BF16, sin tensor cores),
# driver 582.66.
#
# Trampa nº1 — el driver anuncia "CUDA 13.0" y eso NO es lo que hay que
# instalar: es el runtime **maximo** que el driver soporta. CUDA es compatible
# hacia atras (un driver nuevo ejecuta runtimes viejos), asi que un contenedor
# con CUDA 12.6 corre sin problema sobre este driver. Al reves no: CUDA 13
# **elimino** la generacion de codigo para Maxwell/Pascal/Volta, de modo que una
# rueda cu130 no contiene ni un solo kernel ejecutable en esta tarjeta.
#
# Trampa nº2 — las ruedas de release de PyTorch son **SASS-only**: salvo en las
# nightly no llevan PTX, asi que **no hay JIT de rescate**. O el fatbinary trae
# un cubin de la familia sm_6x o la GPU no ejecuta nada. Esto invierte la
# intuicion habitual de "ya lo compilara el driver".
#
# VERIFICADO el 2026-09-01 contra la matriz de build oficial de PyTorch
# (`.ci/manywheel/build_env_setup.py`, `TORCH_CUDA_ARCH_LIST_TABLE`, rama main):
#     "12.6": x86_64 -> {50, 60, 70, 75, 80, 86, 90}              <- Pascal SI
#     "13.0"/"13.2"/"13.4": x86_64 -> {75, 80, 86, 90, 100, 120}  <- Pascal NO
# con el comentario del propio upstream: "CUDA 13.x dropped sm_50/60/70".
# El corte se produjo en la 12.8 (torch 2.7: "removing sm_50-sm_70 architectures
# deprecated in CUDA 12.8"); desde torch 2.9 en adelante **solo la variante
# cu126 conserva 5.0 y 6.0**, y las sigue conservando en la rama main de hoy.
#
# Consecuencia importante, y buena: **NO hace falta un torch antiguo**. La
# bifurcacion "torch viejo por Pascal contra transformers nuevo por el codigo
# vendorizado" que se escalo al propietario **no existe**, siempre que la rueda
# sea la de **CUDA 12.6**. Lo que hay que fijar no es la version de torch: es la
# variante de CUDA. Por eso se usa la ultima etiqueta `cuda12.6` publicada, y no
# la `2.5.1-cuda12.4` del plan original (que tambien traia sm_60, pero obligaba
# a un torch de hace ocho versiones para nada).
#
# `sm_60` vale para `sm_61`: la compatibilidad binaria de CUDA garantiza que un
# cubin de capacidad X.y ejecuta en dispositivos X.z con z >= y (misma major).
# Ninguna rueda oficial ha llevado nunca un cubin `sm_61` literal; el que sirve
# es el `sm_60`. La asercion de mas abajo esta escrita en esos terminos.
#
# Paridad con el host: el Python de la maquina tiene torch 2.13.0, la misma
# version que esta imagen. El fusor offline y el contenedor comparten asi la
# implementacion de safetensors/torch que escribe y lee el artefacto, que es
# justo donde un desparejo se paga caro.
#
# El digest fija la imagen (la etiqueta es movil). Si el registro devuelve
# "manifest unknown", quita `@sha256:...` y deja solo la etiqueta: el digest se
# tomo del catalogo publico el 2026-09-01 (publicada 2026-07-08, amd64,
# 3,61 GiB comprimida, CUDA 12.6.3, Python 3.11).
ARG BASE_IMAGE=pytorch/pytorch:2.13.0-cuda12.6-cudnn9-runtime@sha256:6acf597eeb8e376a96580dde4952f37cc017fef732bb40bfc73f28f25e3f64b4
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="ace-step-runner" \
      org.opencontainers.image.description="Runner GPU minimo de ACE-Step 1.5 (T-05, Fase 0). Pesos montados en /weights, nunca embebidos." \
      com.suno-selfhosted.task="T-05" \
      com.suno-selfhosted.gpu-arch="sm_61 (Pascal), servido por el cubin sm_60 de la rueda cu126" \
      com.suno-selfhosted.weights="montados en /weights:ro, NO incluidos en la imagen (D-14)" \
      com.suno-selfhosted.credentials="ninguna (D-15)"


# -----------------------------------------------------------------------------
# 2. PRIMERA ASERCION DE BUILD: la imagen base ejecuta Pascal, o no hay imagen
# -----------------------------------------------------------------------------
# Es la linea mas valiosa del fichero. `get_arch_list()` lee el fatbinary y **no
# necesita GPU**, asi que la comprobacion corre en cualquier maquina de build,
# incluido un CI sin acelerador. Va ANTES del `pip install` para que un cambio
# de imagen base falle en segundos y no despues de resolver dependencias.
#
# Comprueba tambien el Python: `contracts.py` usa `enum.StrEnum` (3.11+). La
# imagen base trae 3.11; si upstream la cambia, se sabe aqui y no en runtime.
#
# Nota sobre el parseo: el sufijo numerico esta en `a.split("_")[1]`. Un
# `a[5:]` NO vale — "sm_60" mide 5 caracteres, asi que devuelve cadena vacia y
# el chequeo se cae en silencio hacia el lado equivocado (rechazaria una rueda
# perfectamente valida). Para el PTX la regla es la contraria a la del SASS: el
# PTX de capacidad X compila hacia adelante a cualquier capacidad mayor o igual,
# por eso ahi el criterio es `<= 61` sin suelo.
RUN python -c 'import sys, torch; \
    assert sys.version_info >= (3, 11), f"contracts.py usa enum.StrEnum: exige Python >= 3.11 y la imagen base trae {sys.version.split()[0]}"; \
    al = torch.cuda.get_arch_list(); \
    print(f"[T-05] python={sys.version.split()[0]} torch={torch.__version__} cuda={torch.version.cuda}"); \
    print(f"[T-05] arch_list={al}"); \
    sass = [int(a.split("_")[1]) for a in al if a.startswith("sm_") and a.split("_")[1].isdigit()]; \
    ptx = [int(a.split("_")[1]) for a in al if a.startswith("compute_") and a.split("_")[1].isdigit()]; \
    assert any(60 <= c <= 61 for c in sass) or any(p <= 61 for p in ptx), \
        f"La rueda de torch de esta imagen NO puede ejecutar Pascal sm_61 (GTX 1070). arch_list={al}. " \
        "Las ruedas cu128/cu130 y posteriores retiraron sm_50/60/70 y no llevan PTX de rescate. " \
        "Usa una base cuda12.6 (la matriz oficial mantiene 50/60/70/75/80/86/90 en esa variante) " \
        "o compila torch con TORCH_CUDA_ARCH_LIST=6.1."; \
    print("[T-05] OK: hay cubin de la familia sm_6x; sm_60 ejecuta en sm_61 por compatibilidad binaria")'


# -----------------------------------------------------------------------------
# 3. DEPENDENCIAS DE INFERENCIA — solo lo que importa el codigo, con su licencia
# -----------------------------------------------------------------------------
# La lista sale de leer los imports reales de `modeling_acestep_v15_turbo.py`
# (96 KB de upstream, revision 19671f406d603126926c1b7e2adc169acbcade22), no de
# su README:
#   torch, torch.nn.functional, einops.rearrange,
#   vector_quantize_pytorch.ResidualFSQ, numpy (perezoso) y de transformers:
#   cache_utils, modeling_attn_mask_utils, modeling_flash_attention_utils,
#   modeling_layers, modeling_outputs, modeling_utils, processing_utils, utils
#   y models.qwen3.modeling_qwen3.
#
# `einops` y `vector-quantize-pytorch` son OBLIGATORIOS aunque solo se genere
# text2music: son imports de modulo (fallan al importar, no al usarse) y
# `prepare_condition` ejecuta SIEMPRE tokenize/detokenize sobre el ResidualFSQ.
#
# LO QUE SE DEJA FUERA A PROPOSITO:
#   * `diffusers` — el decoder Oobleck del VAE se vendoriza (unas 125 lineas).
#     Instalar el paquete entero traeria cientos de pipelines que no se usan. La
#     obra derivada conserva el aviso Apache-2.0 y la referencia al commit.
#   * `soundfile` / `libsndfile1` / `torchaudio` — el adapter escribe WAV con el
#     modulo `wave` de la biblioteca estandar. El post-proceso (FLAC de almacen,
#     MP3 320, resample a 48 kHz con soxr, loudness EBU R128) es T-19/T-45 y no
#     vive en esta imagen.
#   * `accelerate`, `bitsandbytes`, `xformers`, `flash-attn`, `triton` — ninguno
#     tiene kernels utiles para sm_61; solo anadirian peso y falsas rutas.
#
# LICENCIAS (invariante: verificadas ANTES de integrar). Comprobadas en los
# metadatos publicados de cada paquete el 2026-09-01:
#   transformers 5.16.1 ............ Apache-2.0
#   tokenizers 0.23.1 .............. Apache-2.0
#   safetensors 0.8.0 .............. Apache-2.0
#   huggingface-hub 1.29.0 ......... Apache-2.0
#   einops 0.8.2 ................... MIT
#   vector-quantize-pytorch 1.31.1 . MIT
#   einx 0.4.3 (transitiva) ........ MIT
#   torch-einops-utils 0.1.22 ...... MIT (transitiva)
#   numpy .......................... BSD-3-Clause
# Todas permiten uso comercial. Las dos transitivas se fijan explicitas justo
# para que queden bajo ficha y no entren por la puerta de atras.
# Queda ABIERTA, y es del propietario, la ficha de licencia del snapshot de
# Qwen3-Embedding-0.6B: la copia local no trae LICENSE ni NOTICE. Eso afecta al
# **artefacto de pesos**, no a esta imagen (aqui no viaja ningun peso), pero hay
# que cerrarlo antes de usar el artefacto.
#
# Por que `safetensors`, `tokenizers` y `huggingface-hub` se fijan aunque
# `transformers` ya los arrastre: son la cadena que lee el artefacto y
# reconstruye el tokenizer desde el blob U8 empotrado. Un pin flotante ahi puede
# cambiar el condicionamiento sin que nada falle.
#
# numpy va con rango y NO con pin exacto, a proposito: las ruedas de numpy >= 2.5
# exigen Python >= 3.12 y esta base trae 3.11. Un `numpy==2.5.x` copiado de una
# lista escrita para otra base rompe el build sin explicar por que.
#
# torch NO aparece en la lista: viene de la imagen base y con la variante de
# CUDA correcta. Pedirlo aqui invita a pip a traer la rueda de PyPI (que es
# CPU-only) y a dejar la GPU muerta en silencio. La segunda asercion re-comprueba
# `arch_list` DESPUES de instalar, que es la garantia de verdad.
#
# `--break-system-packages` (PEP 668): MEDIDO el 2026-09-01, el primer intento de
# build fallo aqui con "externally-managed-environment". La base
# `pytorch/pytorch:2.13.0-cuda12.6-cudnn9-runtime` ya no trae conda: es un Python
# 3.12 de Debian marcado como gestionado por el sistema, y pip se niega a tocarlo.
# En una imagen de contenedor la advertencia no aplica —el "sistema" ES esta
# imagen, desechable y reconstruible desde este fichero—, asi que se acepta la
# ruptura en vez de montar un venv que solo anadiria una capa y una ruta mas que
# recordar en el ENTRYPOINT. Lo que NO se hace es instalar torch por pip (ver el
# parrafo de arriba): eso si romperia la GPU en silencio, y por eso la segunda
# asercion vuelve a comprobar `arch_list` despues de esta linea.
RUN pip install --no-cache-dir --disable-pip-version-check --break-system-packages \
        transformers==5.16.1 \
        tokenizers==0.23.1 \
        safetensors==0.8.0 \
        huggingface-hub==1.29.0 \
        einops==0.8.2 \
        vector-quantize-pytorch==1.31.1 \
        einx==0.4.3 \
        torch-einops-utils==0.1.22 \
        "numpy>=2.1,<2.5"


# -----------------------------------------------------------------------------
# 4. SEGUNDA ASERCION: compatibilidad transformers <-> codigo vendorizado
# -----------------------------------------------------------------------------
# El riesgo estructural de esta imagen es un desparejo entre la version de
# `transformers` y la superficie que importa el `.py` de upstream (que declara
# `transformers_version: 4.57.0.dev0` en su `config.json`, muy por detras del
# 5.16.1 que se fija aqui). Si ese desparejo existe, el build DEBE fallar aqui,
# en minutos, y no seis horas despues delante de la GPU.
#
# Se comprueban tres cosas distintas:
#   (a) la lista **literal** de simbolos que importa `modeling_acestep_v15_turbo.py`;
#   (b) que `Qwen3Model` se construye y produce **exactamente 310 entradas** de
#       `state_dict`, que es el recuento del namespace `text_encoder.*` del
#       artefacto (28 capas x 11 tensores + embed_tokens + norm). Si transformers
#       cambiase la estructura, en T-03 reventaria un `load_state_dict(strict=True)`
#       con los pesos ya en VRAM; se prefiere saberlo en el build;
#   (c) que el `pip install` no ha sustituido torch por una rueda sin Pascal.
# El modelo se construye bajo `set_default_device("meta")`: cero bytes de RAM y
# cero GPU. (`torch.device(...)` como gestor de contexto no cabe en una sola
# linea logica, que es lo unico que admite un `RUN` con continuaciones.)
#
# VERIFICADO en el host el 2026-09-01 con torch 2.13.0+cpu y transformers 5.16.1:
# la superficie de imports resuelve y el recuento da 310 exactos. Lo que NO se
# puede verificar sin GPU es que esos mismos simbolos produzcan kernels
# ejecutables en sm_61; eso lo mide T-03.
RUN python -c 'import torch, transformers; \
    from transformers.cache_utils import Cache, DynamicCache, EncoderDecoderCache; \
    from transformers.modeling_attn_mask_utils import _prepare_4d_causal_attention_mask; \
    from transformers.modeling_flash_attention_utils import FlashAttentionKwargs; \
    from transformers.modeling_layers import GradientCheckpointingLayer; \
    from transformers.modeling_outputs import BaseModelOutput; \
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS, PreTrainedModel; \
    from transformers.processing_utils import Unpack; \
    from transformers.utils import auto_docstring, can_return_tuple, logging; \
    from transformers.models.qwen3.modeling_qwen3 import Qwen3MLP, Qwen3RMSNorm, Qwen3RotaryEmbedding, apply_rotary_pos_emb, eager_attention_forward; \
    from vector_quantize_pytorch import ResidualFSQ; \
    from einops import rearrange; \
    from transformers import Qwen3Config; \
    from transformers.models.qwen3.modeling_qwen3 import Qwen3Model; \
    print(f"[T-05] transformers={transformers.__version__}: superficie de imports del .py vendorizado OK"); \
    torch.set_default_device("meta"); \
    cfg = Qwen3Config(vocab_size=151669, hidden_size=1024, intermediate_size=3072, num_hidden_layers=28, num_attention_heads=16, num_key_value_heads=8, head_dim=128, rms_norm_eps=1e-06, rope_theta=1000000, max_position_embeddings=32768, tie_word_embeddings=True); \
    n = len(Qwen3Model(cfg).state_dict()); \
    print(f"[T-05] Qwen3Model(meta).state_dict() -> {n} entradas"); \
    assert n == 310, \
        f"Qwen3Model construye {n} entradas y el namespace text_encoder.* del artefacto trae 310. " \
        "O el fusor regenera el artefacto, o esta version de transformers no sirve. No sigas."; \
    al = torch.cuda.get_arch_list(); \
    sass = [int(a.split("_")[1]) for a in al if a.startswith("sm_") and a.split("_")[1].isdigit()]; \
    ptx = [int(a.split("_")[1]) for a in al if a.startswith("compute_") and a.split("_")[1].isdigit()]; \
    assert any(60 <= c <= 61 for c in sass) or any(p <= 61 for p in ptx), \
        f"El pip install ha sustituido torch por una rueda sin Pascal (arch_list={al}). " \
        "Alguna dependencia ha pedido un torch mas nuevo y pip ha traido la de PyPI, que es CPU-only."; \
    print("[T-05] OK: torch sigue siendo la rueda con cubin sm_6x tras instalar dependencias")'


# -----------------------------------------------------------------------------
# 5. ENTORNO — cada variable con su motivo
# -----------------------------------------------------------------------------
# Se declaran en bloques separados en vez de en un unico ENV encadenado para
# poder comentar cada decision sin meter comentarios dentro de una instruccion
# continuada.

# El defecto del adapter es `bfloat16` y GP104 **no tiene BF16**. Este es el
# primero de los dos cinturones: el shim de T-03 debe ademas RECHAZAR cualquier
# dtype distinto de float16 cuando `torch.cuda.is_bf16_supported()` es False,
# porque `--dtype` en la linea de comandos gana a esta variable.
ENV ACE_STEP_DTYPE=float16
ENV ACE_STEP_DEVICE=cuda:0

# Los pesos se MONTAN aqui (`-v D:\srv\ace-step\artifacts:/weights:ro`). El
# nombre del fichero coincide con DEFAULT_WEIGHTS_FILE del adapter para no tener
# que configurar nada. El artefacto es un unico safetensors que sella con un
# solo sha256 pesos + configs + tokenizer + latente de silencio; si se define
# ACE_STEP_WEIGHTS_SHA256, el adapter lo verifica antes de cargar (integridad,
# NO inocuidad: la inocuidad la da el formato, D-14).
ENV ACE_STEP_WEIGHTS_DIR=/weights
ENV ACE_STEP_WEIGHTS_FILE=ace_step_1_5.safetensors

# Unico punto de integracion con el codigo del modelo. Es ya el defecto del
# adapter; se hace explicito porque es justo la pieza que T-03 tiene que
# escribir, y porque asi aparece en `docker inspect`.
ENV ACE_STEP_PIPELINE_FACTORY=ace_step_shim:build_pipeline
ENV ACE_STEP_OUTPUT_DIR=/outputs

# La consola de control de `serve` **no tiene autenticacion** (es una consola de
# Fase 0, no la API de T-11). Se queda en la loopback DEL CONTENEDOR: con este
# valor el puerto no es alcanzable desde el host ni publicandolo. Para usarla
# desde el host hay que optar explicitamente:
#     -e ACE_STEP_HOST=0.0.0.0 -p 127.0.0.1:8000:8000
# es decir, escuchar dentro del contenedor y publicar SOLO en la loopback del
# host. Nunca `-p 8000:8000` a secas, que lo expone a la red local.
ENV ACE_STEP_HOST=127.0.0.1
ENV ACE_STEP_PORT=8000

# La difusion a 180 s hace del orden de 192 ciclos alloc/free de ~618 MiB. Sin
# segmentos expandibles esa secuencia fragmenta el caching allocator y el OOM
# llega por fragmentacion, no por falta de VRAM. Efecto lateral a tener en
# cuenta al perfilar en T-03: cambia lo que reporta `memory_reserved`.
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Carga perezosa de modulos CUDA: los kernels suben a VRAM cuando se usan, no al
# crear el contexto. Es el defecto en CUDA 12.x, pero se hace explicito porque
# recorta directamente el pico mas estrecho del diseno (el instante de carga,
# con ~810 MiB de holgura sobre los ~6.988 MiB libres de esta tarjeta).
ENV CUDA_MODULE_LOADING=LAZY

# Si algo compilase una extension CUDA en tiempo de ejecucion, que la compile
# para esta tarjeta y no para la del que construyo la imagen.
ENV TORCH_CUDA_ARCH_LIST=6.1

# Capacidades minimas del NVIDIA Container Toolkit: computo y nvidia-smi. Nada
# de video, graphics ni display.
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Sin red de salida: todo lo que el modelo necesita esta en /weights. Si alguna
# libreria intenta resolver un repo del hub, que falle rapido y con mensaje
# claro en vez de colgarse en un timeout de DNS. HF_HOME apunta a un directorio
# escribible por el usuario no-root.
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1
ENV HF_HOME=/tmp/hf

# El tokenizer de Rust paraleliza por defecto y avisa (o se bloquea) al
# combinarse con fork; aqui se tokeniza una letra, no un corpus.
ENV TOKENIZERS_PARALLELISM=false

# El text encoder corre en CPU y en fp32 (en Pascal el fp16 nativo va a 1/64 del
# fp32, asi que compensa sacarlo de la GPU). Ajusta este numero al recuento de
# nucleos fisicos de la maquina anfitriona.
ENV OMP_NUM_THREADS=8

# Logs sin buffer: el arranque en frio de T-03 se cronometra leyendolos.
ENV PYTHONUNBUFFERED=1
# Sin .pyc: /app pertenece a root y el proceso corre como uid 10001.
ENV PYTHONDONTWRITEBYTECODE=1


# -----------------------------------------------------------------------------
# 6. USUARIO NO-ROOT Y DIRECTORIOS
# -----------------------------------------------------------------------------
# uid/gid 10001 fijos (fuera del rango de usuarios del sistema) para que un
# fichero escrito en un volumen tenga siempre el mismo dueno. El shell es
# `nologin`: este contenedor ejecuta un proceso, no una sesion. Para depurar,
# `docker exec -u 0 -it <cid> bash`.
#
# /weights se crea vacio y **sin permiso de escritura para el usuario**: se
# monta `:ro` y el proceso solo tiene que poder leerlo. En bind mounts de Docker
# Desktop sobre Windows los ficheros aparecen legibles por todos, asi que uid
# 10001 los lee sin ajustes; en un host Linux hay que asegurarse de que el
# artefacto tenga permiso de lectura para "otros".
RUN groupadd --gid 10001 runner \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin runner \
    && mkdir -p /app /outputs /weights /tmp/hf \
    && chown -R 10001:10001 /outputs /tmp/hf

WORKDIR /app

# COPIA SELECTIVA. El contexto de build es `apps/runner`. No se copia el
# directorio entero: `tests/`, los informes JSON de los spikes y los
# perfiladores (`vram_profile.py`, `capability_probe.py`) no hacen falta para
# inferir y solo anaden superficie. El diagnostico de GPU dentro del contenedor
# se hace con el subcomando `probe` del propio adapter, no con esos scripts.
#
# El adapter se apana el `sys.path` solo (mete su directorio, `spikes/` y la
# raiz del runner), asi que no hace falta PYTHONPATH ni un paquete instalable.
COPY --chown=10001:10001 contracts.py /app/contracts.py
COPY --chown=10001:10001 spikes/_timing.py /app/spikes/_timing.py
COPY --chown=10001:10001 spikes/_mock.py /app/spikes/_mock.py
COPY --chown=10001:10001 adapters/ace_step/ /app/adapters/ace_step/

# CODIGO VENDORIZADO DE UPSTREAM — ya existe (2026-09-01) en
# `adapters/ace_step/vendor/`: `configuration_acestep_v15.py`,
# `modeling_acestep_v15_turbo.py` y `config.json`, fijados a la revision
# 19671f406d603126926c1b7e2adc169acbcade22 y con sus SHA-256 en el README del
# directorio. Estan aqui, y no se descargan en arranque, porque CLAUDE.md
# prohibe `trust_remote_code`/`auto_map`.
#
# NO hace falta un COPY propio: el `COPY adapters/ace_step/` de arriba ya los
# arrastra. Un COPY adicional solo anadiria una capa redundante. (El README.md
# del directorio no viaja: `.dockerignore` excluye `**/*.md`, y la documentacion
# no se ejecuta.)
#
# Es codigo, no pesos: por eso viaja en la imagen y no en /weights.
#
# PENDIENTE de T-03, y conviene no confundirlo con "hecho": los parches
# (centinela de mascara en fp16, reconstruccion de `rotary_emb.inv_freq`,
# construccion en meta-device) y `oobleck_decoder.py` (obra derivada de
# diffusers, Apache-2.0, con su aviso de copyright y su nota de modificacion).
# Y sobre todo la REVISION de seguridad linea a linea: son 109 KB de Python que
# se EJECUTAN al importarse, y vendorizarlos los hace inmutables, no inocuos.

USER 10001:10001


# -----------------------------------------------------------------------------
# 7. PUERTO, SONDA Y ARRANQUE
# -----------------------------------------------------------------------------
# EXPOSE es documentacion: no publica nada por si solo. Ver la nota de
# ACE_STEP_HOST sobre como publicarlo sin dejarlo abierto a la red local.
EXPOSE 8000

# La sonda usa el subcomando `healthcheck` del adapter, que habla por urllib con
# `GET /health` en la loopback del contenedor (nada de meter `curl` en la
# imagen: menos superficie y menos bytes en el arranque en frio). Devuelve 0
# solo si el adapter reporta `ready=True`.
#
# El `start-period` es largo a proposito: el arranque en frio documentado es de
# 2 a 6 minutos y encima va la carga de un artefacto de 6,16 GB con offloading.
# Marcar "unhealthy" durante esa ventana seria un falso positivo.
#
# AVISO: la sonda solo tiene sentido en modo `serve`. En `generate` o `probe`
# (procesos de una sola pasada, que es como los usan T-03/T-04/T-09) no hay
# servidor escuchando y Docker marcara el contenedor como unhealthy; es
# esperado, no un fallo, y no afecta al codigo de salida del comando.
HEALTHCHECK --start-period=900s --interval=30s --timeout=15s --retries=3 \
    CMD ["python", "adapters/ace_step/adapter.py", "healthcheck"]

ENTRYPOINT ["python", "adapters/ace_step/adapter.py"]
CMD ["serve"]


# =============================================================================
# ACEPTACION DE T-05 (lo comprobable HOY, sin shim y sin pista generada)
# =============================================================================
#   a) `docker build` termina y las dos aserciones pasan (Pascal en la base;
#      superficie de transformers + recuento 310 + Pascal tras el pip install).
#   b) `docker run --gpus all --rm <img> probe` ve la GPU y NO imprime
#      "NO VIABLE". Depende del arreglo del suelo de VRAM en `spikes/_timing.py`
#      (esta tarjeta reporta 8191 MiB frente a un suelo nominal de 8192): los dos
#      cambios se validan juntos.
#   c) `docker run --gpus all --rm -v D:\srv\ace-step\artifacts:/weights:ro \
#          -e ACE_STEP_MOCK=1 <img> healthcheck` responde OK.
#   d) Con ACE_STEP_MOCK apagado, el fallo ESPERADO Y CORRECTO es el RuntimeError
#      de `_resolve_pipeline_factory` ("No se pudo importar el shim del modelo
#      'ace_step_shim:build_pipeline'"). Que llegue hasta ahi demuestra que las
#      puertas previas —suelo de VRAM, assert_safetensors, isfile, sha256— se han
#      superado y que lo unico que falta es T-03.
#
# LO QUE ESTA IMAGEN NO PUEDE DEMOSTRAR, Y HAY QUE MEDIR EN T-03
# --------------------------------------------------------------
# * **Velocidad.** Es el riesgo nº1 y no esta medido. GP104 ejecuta el FP16
#   nativo a 1/64 del FP32; si cuBLAS no promociona a FP32 en sm_61, las 10
#   pistas de G1 pasan de unos 20 minutos a un orden de horas. Obligatorio un
#   smoke test cronometrado a 30 s (1 pista, 8 pasos) ANTES de comprometer las
#   10 pistas, y con el umbral de plan B fijado de antemano.
# * **Atencion.** No hay kernels de flash-attention ni de Triton para sm_61, y
#   `torch.compile` queda descartado. El shim tiene que forzar atencion eager (o
#   SDPA por el camino matematico); ninguna variable de entorno lo garantiza
#   desde aqui.
# * **Estabilidad numerica en fp16.** El residual stream del DiT se midio en
#   17.248 con condicionamiento sintetico y 125 tokens, frente al techo 65.504
#   de fp16; con 2.250 tokens y embeddings reales ese margen puede evaporarse.
#   Guardia de inf/NaN por paso en el shim, no opcional.
# * **VRAM libre en el instante de la carga.** Lo que manda no es la VRAM total
#   (8.191 MiB) sino la libre con el escritorio arrancado (~6.988 MiB) frente a
#   los ~6.178 MiB del pico de carga. Esa comprobacion es del shim; ninguna
#   variable de esta imagen la sustituye. Abrir un navegador durante una
#   generacion puede tumbarla.
# * **Que el build corra de verdad.** Este fichero se ha escrito y razonado en
#   una maquina donde `docker build` no se puede lanzar (C: al 98 %). Las dos
#   aserciones se han probado por separado en el Python del host (torch
#   2.13.0+cpu, transformers 5.16.1); el build completo esta SIN EJECUTAR.
# =============================================================================
