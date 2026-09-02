"""Factoria del pipeline real de ACE-Step 1.5 turbo — el shim que pide `adapter.py`.

Que es esto
-----------
`adapter.py` aisla a proposito la construccion del grafo del modelo y su bucle de
muestreo en **un unico punto de integracion**: resuelve
`ACE_STEP_PIPELINE_FACTORY` (por defecto `ace_step_shim:build_pipeline`), mapea el
artefacto con `load_file(ruta, device="cpu")` e invoca

    build_pipeline(*, state_dict, device, dtype, offload)

esperando de vuelta un objeto con `render(...)` (obligatorio) y, opcionalmente,
`warmup()` y `release()`. Este fichero es esa factoria. Hasta hoy no existia, y
por eso `load()` abortaba con «shim ausente».

La factoria recibe **solo esos cuatro argumentos**: ni contexto, ni rutas, ni
directorio de pesos. Todo lo demas —configuraciones del DiT, de Qwen3 y del VAE,
`tokenizer.json` completo y latente de silencio— viaja **dentro** del artefacto,
en el espacio de nombres `aux.*`.

Lo que este fichero NO reimplementa
-----------------------------------
Nada del modelo ni del pipeline. Se limita a **construir** y **despachar** tres
piezas ya vendorizadas, verificadas y medidas en la GPU objetivo:

* `vendor/modeling_acestep_v15_turbo.py` + `vendor/configuration_acestep_v15.py`
  — definicion del grafo (revision HuggingFace `19671f40...`).
* `vendor/pipeline/` — condicionamiento, programacion de pasos, bucle de Euler y
  puente al decode (revision GitHub `ca1e85fe...`, MIT).
* `vendor/oobleck_decoder.py` — decoder del VAE con decode por trozos.
* `vendor/lm/` — planificador de 5 Hz: prompts, decodificacion restringida, bucle
  de generacion y paso de codigos a `lm_hints_25Hz` (revision GitHub
  `ca1e85fe...`, MIT; pesos `acestep-5Hz-lm-0.6B` @ `148d8ea0...`, MIT).
* `text_conditioning.py` — constructores verificados del tokenizer y del Qwen3.

Las CUATRO condiciones medidas que este fichero hace cumplir
------------------------------------------------------------
**C1 — fp16 tal cual, sin upcast.** El artefacto es fp16 entero (1.177 tensores).
Promoverlo a fp32 son +5.878 MiB y no cabe en 8 GB. Ademas no compensa: en sm_61
cuBLAS promociona internamente a fp32 y el ratio fp16/fp32 medido es 0,80-1,11
segun la forma, o sea que el camino lento de Pascal **no** se pisa. Hay dos
excepciones **locales**, ninguna de ellas un upcast del artefacto:

* La conv1d final del VAE, en fp32 porque en fp16 es 3,06-3,74x mas lenta
  (medido: 28,4-33,8 ms frente a 9,0-9,7 ms). Vive dentro de
  `OobleckDecoder._peso_conv2_fp32`; aqui solo se respeta no tocando su dtype.
* El **codificador de letra** del DiT (`encoder.lyric_encoder`, 772 MiB), en fp32
  por RANGO, no por velocidad. Ver la seccion siguiente.

El codificador de letra desborda fp16: medicion y remedio
---------------------------------------------------------
MEDIDO el 2026-09-02 en la GTX 1070 con los pesos reales. Con una letra de mas de
~40 tokens, el flujo residual de `encoder.lyric_encoder` crece capa a capa
(1.388 -> 1.565 -> ... -> 3.756) y el MLP de la ultima capa lo lleva a
**1,75e5**, por encima del maximo de fp16 (65.504). En fp16 esos elementos salen
`inf`, el residual los convierte en `NaN` y —como `pack_sequences` los empaqueta
en `encoder_hidden_states`— la atencion cruzada del DiT propaga el NaN a **todo**
el latente: 48.000 de 48.000 valores. El sintoma llega tarde y lejos, en
`validar_latentes()`, y parece un fallo de la difusion cuando no lo es.

No es un problema de nuestros pesos: con las **mismas** matrices fp16 promovidas
a fp32, la salida es finita y coincide con la de fp16 hasta 0,0048 sobre un
|max| de 4,27 en las letras que no desbordan. Es el rango, no la precision. El
checkpoint publicado es bf16 (`config.json` dice `dtype: bfloat16`) y bf16 tiene
el mismo exponente que fp32: alli 1,75e5 no es nada. Al fusionar el artefacto a
fp16 esa cabecera de rango se perdio, y solo se nota en este modulo.

El remedio es el que prescribe el propio diagnostico de `vendor/pipeline/diffusion.py`
(«hay que promover a fp32 la capa que desborda, no el artefacto completo») y es
barato por tres razones medidas: (1) la RMSNorm final del codificador devuelve la
salida a |max| = 7,56, asi que **solo el interior** necesita rango y todo lo que
sale de ahi sigue siendo fp16; (2) en sm_61 fp32 no cuesta tiempo (ratio medido
0,80-1,11, y la pasada fp32 completa son 57 ms); (3) son 772 -> 1.544 MiB de un
modulo que **no** reside en VRAM salvo mientras se prepara el condicionamiento.
Se implementa en `_CodificadorLetraFp32`, sin tocar el fichero vendorizado.

**C2 — decode del VAE por trozos como camino por defecto.** El decode monolitico
de 180 s proyecta 23,1 GiB: no cabe, y ni siquiera se intenta (un OOM de driver
deja el asignador cacheante de PyTorch inservible). Se llama siempre a
`decodificar_por_trozos` con los parametros medidos (W=256, S=48, G=16).

**C3 — despacho por componente.** Desde el 2026-09-02 el adapter hace
`load_file(..., device="cpu")`, o sea que el artefacto llega **mapeado**, no en
VRAM. Este fichero lo reparte por prefijos, **consume el diccionario
destructivamente** (`pop`) y **materializa** cada tensor donde le toca (un tensor
que siguiera respaldado por el fichero se releeria del disco pagina a pagina en
cada subida a VRAM: 42,91 s frente a 0,43 s medidos):

    componente            MiB      donde vive          cuando esta en VRAM
    dit.decoder         3.004,9    VRAM permanente     siempre
    dit.encoder         1.932      RAM                 solo al condicionar
                       (1.160,4 en el artefacto; el codificador de letra pasa de
                        772 a 1.544 al promoverse a fp32, ver mas abajo)
    text_encoder.       1.136,4    RAM                 solo al codificar texto
    dit.tokenizer         200,3    RAM                 solo al planificar
    dit.detokenizer       200,3    RAM                 solo al planificar
    vae.decoder           161,0    RAM                 solo al decodificar
    lm.                 1.264,4    RAM                 NUNCA (corre en CPU)
    aux.                   14,6    RAM/VRAM            trivial

El planificador de 5 Hz (`lm.*`, opcional)
------------------------------------------
Hasta el 2026-09-02 `dit.tokenizer` y `dit.detokenizer` se cargaban y **no se
usaban**, y `src_latents` era siempre un recorte del latente de SILENCIO: el DiT
componia a ciegas. Upstream no genera asi. En su pipeline un Qwen3 de 0,6 B
(`acestep-5Hz-lm-0.6B`) escribe primero los metadatos de la pieza y despues una
secuencia de codigos de audio a 5 Hz; el cuantizador FSQ y el detokenizador los
estiran a 25 Hz y el resultado **sustituye** a `src_latents`. Y lo activa por
defecto justo en esta tarjeta: `gpu_config.py`, tier de 6-8 GB,
`init_lm_default: True`, `max_duration_with_lm: 480`.

La sustitucion la escribe upstream como
`torch.where(is_covers > 0, lm_hints_25Hz, src_latents)`, y ahi esta la trampa
que mantuvo esto desconectado sin que nada avisara: `is_covers` **no** significa
«es una version de otra cancion». Upstream lo calcula como
`is_cover = (task_type == "cover") or has_code_hint`, o sea **cierto en cuanto
hay codigos**. Significa «hay plan semantico». Pasar los codigos con
`is_covers=False` los descarta en silencio: mismo audio, sin error.

Aqui la cadena entera vive en `PipelineAceStep._planificar` y se enciende y se
apaga con `model_params["usar_lm"]` (por defecto True). Esa perilla es el
entregable: permite generar dos pistas con la misma semilla, la misma letra y el
mismo prompt en las que lo unico distinto es si hubo plan. El LM corre en **CPU
en bf16** (medido: 77 ms/token y 1.265 MiB, frente a 153 ms/token y 2.537 MiB en
fp32); el cuantizador y el detokenizador suben a VRAM solo durante esa llamada.

Un artefacto sin `lm.*` sigue siendo valido: da el pipeline de siempre, y
`usar_lm=True` falla con un mensaje que dice como reconstruirlo. No se degrada en
silencio, porque una pista con plan y otra sin el no son comparables y la
comparacion es justo lo que se esta midiendo.

**C4 — atencion eager forzada.** En sm_61 la ruta SDPA cae al kernel
mem-efficient: 282,20 ms frente a 21,87 ms de eager con softmax en fp32 sobre
`[1,16,2250,128]`, o sea **12,9x mas lenta, y en silencio**. `transformers` elige
SDPA por defecto y `set_attn_implementation("eager")` devuelve `"sdpa"` sin avisar;
dejarlo en `None` da `KeyError`. Por eso se **asigna a mano**
`model.config._attn_implementation = "eager"` y se comprueba con un **assert duro**
sobre cada modulo de atencion. La comprobacion no es tautologica: `transformers`
comparte el objeto de configuracion entre submodulos, pero una capa con copia
propia seguiria diciendo `"sdpa"` y ahi es donde el assert salta. **No simplificar
esto**: sin el assert, un cambio de version convierte una pista de 23 s en una de
5 minutos sin un solo mensaje de aviso.

Guardarrail de VRAM
-------------------
Antes de cada asignacion grande se consulta `torch.cuda.mem_get_info` y se aborta
con un mensaje que dice cuanto hace falta y cuanto hay. **Un OOM de driver nunca
se captura para seguir**: deja el asignador cacheante de PyTorch corrupto y no es
recuperable dentro del proceso. Abortar antes es la unica politica valida.

Verificacion ejecutada (GTX 1070 sm_61, 8.192 MiB, `ace-step-runner:t05`)
--------------------------------------------------------------------------
Con el artefacto real y una letra completa en castellano (111 tokens):

    etapa                    30 s        180 s
    condicionamiento        1,08 s      1,13 s
    difusion (8 pasos)      2,76 s     22,41 s   (2,801 s/paso)
    decode del VAE          3,42 s     18,54 s   (4 y 22 ventanas)
    total                   7,3 s      42,3 s
    salida            30,00 s rms 0,132   180,00 s rms 0,147, 48 kHz estereo

`build_pipeline` tarda 9,5 s y deja el `state_dict` del llamante **vacio** (0 de
1.177 claves) con 3.007 MiB residentes en VRAM y 4.166 MiB libres. El pico de
VRAM de una generacion es **6.190 MiB**, y ocurre en el condicionamiento
(3.007 del `dit.decoder` + 1.932 del `dit.encoder` + 1.136 del Qwen3), no en la
difusion. Los tiempos concuerdan con T-03 (2,867 ms/forward del DiT, 23,05 s por
pista) y con el decode medido aparte (18,6-19,1 s). De punta a punta por el
adapter (`adapter.py generate --duration 60`): `gpu_seconds` 12,587,
`vram_peak_mb` 6.190, WAV de 60,00 s y 11.520.044 bytes.

Por que no se usa `TextConditioner.encode()`
--------------------------------------------
`text_conditioning.py` se escribio cuando el **pipeline** de inferencia de
upstream todavia no estaba vendorizado, asi que su `_preparar_textos()` codifica
el texto tal cual y su propia cabecera dice que ese es el punto de cambio si
aparece la envoltura real. Ya ha aparecido: `vendor/pipeline/constants.py` trae
`SFT_GEN_PROMPT` y `formatear_letra` verbatim de `acestep/constants.py`
(GitHub `ca1e85fe...`, blob SHA-1 verificado contra la atestacion de la API), y
esas plantillas **son parte del contrato con los pesos** —el modelo se entreno
viendo exactamente ese texto—. Asi que el camino de texto lo conduce
`vendor/pipeline/conditioning.py` y de `text_conditioning.py` se reutilizan sus
dos constructores publicos y verificados: `construir_tokenizer()` (que valida el
post-procesador, el punto donde una reconstruccion manual del tokenizer cambia el
condicionamiento sin dar error) y `construir_text_encoder()` (meta + `assign`,
reconstruccion de los buffers de RoPE y atencion eager).

Trampa de la carga que este fichero resuelve
--------------------------------------------
`AceStepConditionGenerationModel` declara **15 buffers no persistentes** que no
viajan en el `state_dict`: `inv_freq` y `original_inv_freq` de los cinco modulos
rotatorios, mas cinco del cuantizador FSQ. `load_state_dict(strict=True)` **no los
detecta**, asi que instanciar en `meta` + `to_empty()` produce un modelo roto sin
dar error: con memoria a cero, `inv_freq = 0` deja RoPE sin posicion y sale audio a
-63 dBFS (basura silenciosa que pasa `validar_latentes`); con memoria sucia,
`text_hidden_states` sale todo NaN. Ademas `ResidualFSQ` **ni siquiera se puede
construir** bajo `torch.device("meta")` (llama a `.item()` sobre un tensor meta al
validar sus niveles). La solucion esta en `_instanciar_dit()`.
"""

from __future__ import annotations

import json
import logging
import math
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Arranque de sys.path
# --------------------------------------------------------------------------- #
# El directorio del adapter entra en sys.path para que `vendor` sea un paquete de
# espacio de nombres importable (`vendor.pipeline`, `vendor.oobleck_decoder`) y
# `text_conditioning` un modulo hermano. `adapter.py` ya lo hace, pero este
# fichero no puede depender de que su unico importador sea el adapter: tambien se
# importa desde arneses de prueba.
_AQUI = Path(__file__).resolve().parent
if str(_AQUI) not in sys.path:
    sys.path.insert(0, str(_AQUI))

import torch  # noqa: E402  (tras el arranque de sys.path)

import text_conditioning  # noqa: E402
from vendor.oobleck_decoder import (  # noqa: E402
    GUARDA_LATENTE_POR_DEFECTO,
    SOLAPE_LATENTE_POR_DEFECTO,
    VENTANA_LATENTE_POR_DEFECTO,
    cargar_decoder,
    planificar_trozos,
)
from vendor.pipeline.conditioning import (  # noqa: E402
    longitud_latente,
    preparar_condicionamiento_text2music,
)
from vendor.lm.constants import (  # noqa: E402
    CODIGOS_POR_SEGUNDO,
    VENTANA_AGRUPACION,
    codigos_para_duracion,
)
from vendor.pipeline.constants import LATENT_HOP, SAMPLE_RATE  # noqa: E402
from vendor.pipeline.decode import decodificar_latentes  # noqa: E402
from vendor.pipeline.diffusion import generar_latentes_text2music  # noqa: E402
from vendor.pipeline.scheduler import PASOS_POR_DEFECTO, SHIFT_POR_DEFECTO  # noqa: E402

__all__ = ["AudioRenderizado", "PipelineAceStep", "build_pipeline"]

_LOG = logging.getLogger("ace_step.shim")

_MIB = 1024 * 1024


# --------------------------------------------------------------------------- #
# Contrato con el artefacto (recuentos verificados el 2026-09-02)
# --------------------------------------------------------------------------- #

#: Claves por componente del espacio `dit.*`. Suman los 677 tensores que
#: `AceStepConditionGenerationModel(config).state_dict()` produce **exactamente**,
#: sin remapeo: comprobado clave a clave contra la cabecera del artefacto.
CLAVES_DIT = {"decoder": 476, "encoder": 140, "tokenizer": 32, "detokenizer": 28}
CLAVE_NULL_CONDITION = "dit.null_condition_emb"

CLAVE_CONFIG_ACESTEP = "aux.config.acestep_json"
CLAVE_SILENCE_LATENT = "aux.silence_latent"

# --------------------------------------------------------------------------- #
# El planificador de 5 Hz (`lm.*`). OPCIONAL: solo si el artefacto lo trae.
# --------------------------------------------------------------------------- #
#: Prefijo del planificador y su recuento canonico (28 capas x 11 + embed + norm).
#: NO hay `lm_head.weight`: el config trae `tie_word_embeddings: true`.
PREFIJO_LM = "lm."
CLAVES_LM = 310

CLAVE_LM_CONFIG = "aux.lm.config_json"
#: Los cuatro ficheros que `AutoTokenizer.from_pretrained` necesita ver en un
#: directorio. `chat_template.jinja` es OBLIGATORIO y va aparte: MEDIDO el
#: 2026-09-02, `tokenizer_config.json` de esta revision NO trae `chat_template`,
#: y sin el fichero `apply_chat_template` —que es como `vendor/lm/prompt.py`
#: construye TODOS los prompts— levanta `ValueError: Cannot use chat template
#: functions because tokenizer.chat_template is not set`. Con 4 ficheros falla;
#: con 5 rinde la plantilla correcta. Comprobado montando ambos directorios.
BLOBS_LM_TOKENIZER = {
    "aux.lm_tokenizer.tokenizer_json": "tokenizer.json",
    "aux.lm_tokenizer.tokenizer_config_json": "tokenizer_config.json",
    "aux.lm_tokenizer.special_tokens_map_json": "special_tokens_map.json",
    "aux.lm_tokenizer.chat_template_jinja": "chat_template.jinja",
}

#: dtype del planificador EN EJECUCION. Se decide al construir el pipeline (el LM
#: se carga una sola vez) y por eso es variable de entorno, no `model_params`.
#:
#: BF16 por defecto, y la razon es medida, no heredada. El checkpoint es bf16 y el
#: LM corre en CPU (nunca en la GTX 1070: en fp16 son 1.264 MiB frente a 810 MiB
#: de holgura, y sm_61 no tiene bf16). En CPU, con torch 2.13:
#:
#:     dtype   RAM del modelo   ms/token (incremental)   |max logit|
#:     bf16       1.265 MiB              77                  57,2
#:     fp32       2.537 MiB             153                  57,4
#:
#: es decir bf16 es **el doble de rapido y ocupa la mitad**, sin conversion de los
#: pesos (bf16 es su formato nativo) y con el mismo rango que fp32. Y la RAM
#: importa: el contenedor tiene 7.883 MiB y el resto del pipeline ya ocupa
#: ~3.630 MiB de RAM residente. `fp32` queda como valvula por si alguna vez se
#: sospecha de la precision de las activaciones.
ENV_LM_DTYPE = "ACE_STEP_LM_DTYPE"
_LM_DTYPES = {"bf16": torch.bfloat16, "fp32": torch.float32}

#: Techo duro de duracion. MEDIDO en la GTX 1070: 420 s pasan y 480 s revientan.
#: Se expresa en tramas latentes (25 Hz) porque es la magnitud que manda en la
#: memoria de la atencion.
MAX_TRAMAS_LATENTES = 420 * (SAMPLE_RATE // LATENT_HOP)  # 10.500

#: Pico de VRAM del bucle de difusion **descontados los pesos del DiT**, medido
#: de punta a punta con los pesos reales: 4.613 MiB a 750 tramas (30 s) y
#: 5.291 MiB a 4.500 tramas (180 s), menos los 3.004,9 MiB de `dit.decoder`.
_PICO_DIFUSION_MEDIDO = ((750, 1608.0), (4500, 2286.0))
#: Pendiente para extrapolar por encima de 4.500 tramas. Se toma la del bench del
#: forward entre 4.500 y 7.500 tramas (0,396 MiB/trama), que es mayor que la
#: interpolada (0,181): la atencion no es lineal en la longitud y un guardarrail
#: optimista no es un guardarrail.
_PENDIENTE_PICO_MIB_POR_TRAMA = 0.396

#: Holgura sobre cualquier estimacion antes de asignar.
_FACTOR_HOLGURA = 1.10
_MARGEN_BYTES = 256 * _MIB

#: Perillas admitidas en `model_params`. Lista blanca: un parametro desconocido
#: se rechaza en vez de ignorarse en silencio (no hay `params_schema` hasta T-30,
#: pero eso no autoriza a tragarse lo que el llamante pida).
_PARAMS_ADMITIDOS = frozenset(
    {
        "shift",
        "vocal_language",
        "bpm",
        "keyscale",
        "timesignature",
        "ventana_vae",
        "solape_vae",
        "guarda_vae",
        # -- planificador de 5 Hz ------------------------------------------- #
        # `usar_lm` es la perilla del A/B y por eso existe todo lo demas: con el
        # mismo artefacto, la misma semilla, la misma letra y el mismo prompt se
        # generan las dos versiones y se comparan. Por defecto True porque es lo
        # que hace upstream en esta tarjeta (`gpu_config.py`, tier3 de 6-8 GB:
        # `init_lm_default: True`). Con False el camino es EXACTAMENTE el de
        # antes de conectar el planificador: `src_latents` = latente de silencio.
        "usar_lm",
        # Muestreo del LM. Los defectos son los de `GenerationParams` de upstream
        # (`lm_cfg_scale=2.0`, `lm_temperature=0.85`). `lm_cfg=1.0` desactiva el
        # CFG y **divide por dos** el coste del planificador (una pasada por
        # codigo en vez de dos), a cambio de perder el guiado.
        "lm_cfg",
        "lm_temperatura",
    }
)


# --------------------------------------------------------------------------- #
# Utilidades de dispositivo y VRAM
# --------------------------------------------------------------------------- #

def _normalizar_dispositivo(device: Any) -> torch.device:
    """Devuelve un `torch.device` con indice explicito si es CUDA.

    `torch.device("cuda")` y `torch.device("cuda:0")` **no son iguales**, y este
    fichero compara dispositivos para decidir si un tensor ya esta donde toca (y
    ahorrarse una copia de 3 GiB). Sin normalizar, esa comparacion falla siempre.
    """
    dispositivo = torch.device(device)
    if dispositivo.type == "cuda" and dispositivo.index is None:
        dispositivo = torch.device("cuda", torch.cuda.current_device())
    return dispositivo


def _vram_disponible(dispositivo: torch.device) -> int:
    """Bytes realmente disponibles: los libres del driver mas la cache ociosa.

    Los bloques que PyTorch ya reservo y no esta usando cuentan como ocupados a
    ojos del driver, pero el asignador los puede reutilizar sin pedir mas.
    """
    libre, _total = torch.cuda.mem_get_info(dispositivo)
    return libre + (
        torch.cuda.memory_reserved(dispositivo) - torch.cuda.memory_allocated(dispositivo)
    )


def _exigir_vram(dispositivo: torch.device, necesarios: int, motivo: str) -> None:
    """Aborta ANTES de asignar si no hay margen. Nunca captura un OOM de driver.

    Un `torch.cuda.OutOfMemoryError` del driver deja el asignador cacheante de
    PyTorch en un estado del que no se sale dentro del proceso: capturarlo y
    seguir produce fallos posteriores en sitios que no tienen nada que ver. La
    unica politica valida es comprobar antes y parar.
    """
    if dispositivo.type != "cuda":
        return
    disponible = _vram_disponible(dispositivo)
    if disponible >= necesarios:
        return
    _libre, total = torch.cuda.mem_get_info(dispositivo)
    raise RuntimeError(
        f"VRAM insuficiente para {motivo}.\n"
        f"  necesarios : {necesarios / _MIB:.0f} MiB\n"
        f"  disponibles: {disponible / _MIB:.0f} MiB de {total / _MIB:.0f} MiB totales\n"
        f"  reservados por PyTorch: {torch.cuda.memory_reserved(dispositivo) / _MIB:.0f} MiB "
        f"(en uso {torch.cuda.memory_allocated(dispositivo) / _MIB:.0f} MiB)\n"
        "Se aborta ANTES de reservar: un OOM de driver corrompe el asignador cacheante "
        "de PyTorch y no es recuperable en este proceso."
    )


def _pico_difusion_bytes(tramas: int) -> int:
    """Estimacion conservadora del pico de difusion sin contar los pesos del DiT."""
    (t0, p0), (t1, p1) = _PICO_DIFUSION_MEDIDO
    if tramas <= t0:
        mib = p0
    elif tramas <= t1:
        mib = p0 + (p1 - p0) * (tramas - t0) / (t1 - t0)
    else:
        mib = p1 + _PENDIENTE_PICO_MIB_POR_TRAMA * (tramas - t1)
    return int(mib * _MIB)


# --------------------------------------------------------------------------- #
# Conversion entre tramas latentes (25 Hz) y codigos del planificador (5 Hz)
# --------------------------------------------------------------------------- #

def _codigos_para_tramas(tramas: int) -> int:
    """Codigos de 5 Hz que hacen falta para cubrir `tramas` fotogramas a 25 Hz.

    Division **hacia arriba**: cada codigo rinde exactamente
    `VENTANA_AGRUPACION` = 5 fotogramas, asi que quedarse corto dejaria el final
    de la pista sin plan. Upstream resuelve el desajuste al reves, recortando
    (`lm_hints_25Hz[:, :src_latents.shape[1], :]`), y eso es lo que hace el
    condicionamiento con el sobrante: nunca hay que rellenar.

    Casi siempre es exacto: para una duracion entera de segundos, `longitud_latente`
    da `25*d` tramas y `25*d/5 = 5*d` codigos, sin resto. El techo solo actua en el
    borde de abajo, donde upstream impone un suelo de 128 tramas (5,12 s): ahi
    hacen falta 26 codigos (130 fotogramas) y sobran 2.
    """
    return -(-tramas // VENTANA_AGRUPACION)


def _duracion_para_codigos(codigos: int) -> float:
    """Duracion en segundos que hay que pedirle al planificador para `codigos` codigos.

    `codigos_para_duracion` de upstream es `int(duracion * 5)`, y el redondeo
    binario muerde: `int(1.4 * 5)` es **6**, no 7, porque `1.4*5` vale
    6,999999999999999. Como la decodificacion restringida fuerza el EOS en ese
    entero exacto, un codigo de menos no es un detalle: `planificar()` aborta.
    Aqui se comprueba y se corrige con el minimo incremento representable.
    """
    duracion = codigos / CODIGOS_POR_SEGUNDO
    intentos = 0
    while codigos_para_duracion(duracion) < codigos:
        duracion = math.nextafter(duracion, math.inf)
        intentos += 1
        if intentos > 8:  # no puede pasar; si pasa, mejor ruidoso que en bucle
            raise RuntimeError(
                f"No se encontro una duracion que rinda {codigos} codigos "
                f"(ultimo intento {duracion!r})."
            )
    return duracion


# --------------------------------------------------------------------------- #
# Extraccion destructiva del state_dict
# --------------------------------------------------------------------------- #

def _extraer(
    state_dict: dict[str, torch.Tensor],
    prefijo: str,
    destino: torch.device,
    esperadas: int | None,
) -> dict[str, torch.Tensor]:
    """Saca del `state_dict` las claves con `prefijo` y las coloca en `destino`.

    **Consume** (`pop`) tensor a tensor: construir un sub-diccionario sin sacar las
    claves del original mantendria dos referencias vivas al mismo tensor y, con
    ellas, el mapeo entero del artefacto.

    MATERIALIZACION OBLIGATORIA (2026-09-02). Desde que `adapter.py` mapea el
    artefacto con `load_file(..., device="cpu")`, los tensores que entran aqui
    estan **respaldados por el fichero**, no por RAM anonima. Un `.to(cuda)`
    materializa; un destino CPU no haria nada y dejaria el tensor mapeado. Eso es
    justo la trampa que `text_conditioning.construir_text_encoder` ya evitaba
    clonando: un peso mapeado se relee del disco pagina a pagina en **cada**
    subida a VRAM (42,91 s frente a 0,43 s medidos) y ademas es desalojable. Por
    eso, cuando el destino es CPU, se **clona**.

    El clon no duplica el pico: el original se suelta en la misma vuelta del
    bucle, y lo que se suelta son paginas de cache de fichero, no RAM anonima.

    Returns:
        Sub-diccionario con el prefijo ya quitado, listo para
        `load_state_dict(strict=True, assign=True)`.
    """
    claves = [k for k in state_dict if k.startswith(prefijo)]
    if esperadas is not None and len(claves) != esperadas:
        raise RuntimeError(
            f"El artefacto trae {len(claves)} claves con prefijo {prefijo!r} y el "
            f"contrato verificado son {esperadas}. Este shim no sabe cargar ese "
            "artefacto: o el fusor lo regenera, o hay que revisar el contrato."
        )
    if not claves:
        raise RuntimeError(f"El artefacto no trae ninguna clave con prefijo {prefijo!r}.")

    fuera: dict[str, torch.Tensor] = {}
    for clave in claves:
        tensor = state_dict.pop(clave)
        if tensor.device != destino:
            colocado = tensor.to(destino)
        else:
            # Mismo dispositivo: `.to()` seria un no-op y dejaria el tensor
            # respaldado por el mapeo del artefacto. `clone()` lo pasa a RAM
            # anonima. Ver el docstring.
            colocado = tensor.clone()
        fuera[clave[len(prefijo) :]] = colocado
        # Soltar la referencia local libera la copia de origen en cuanto la
        # conversion ha terminado, sin esperar al final del bucle.
        del tensor, colocado
    return fuera


def _texto_de_blob(state_dict: dict[str, torch.Tensor], clave: str) -> str:
    """Decodifica un blob `aux.*` (tensor U8 con JSON dentro) y lo saca del dict.

    Dato inerte, nunca objetos serializados: aqui no hay `pickle` ni `torch.load`
    en ningun punto (D-14).
    """
    if clave not in state_dict:
        raise RuntimeError(
            f"El artefacto no trae {clave!r}. Las configuraciones viajan DENTRO del "
            "fichero de pesos: este shim no descarga nada de la red."
        )
    tensor = state_dict.pop(clave)
    if tensor.dtype is not torch.uint8 or tensor.dim() != 1:
        raise RuntimeError(
            f"{clave!r} deberia ser un tensor U8 de una dimension y es "
            f"{tensor.dtype} con forma {tuple(tensor.shape)}."
        )
    return bytes(tensor.detach().to("cpu").contiguous().numpy().tobytes()).decode("utf-8")


def _colocar_buffers_no_persistentes(modulo: torch.nn.Module, destino: torch.device) -> int:
    """Mueve a `destino` los buffers que NO viajan en el `state_dict`.

    `load_state_dict(assign=True)` solo toca las claves del `state_dict`, asi que
    los buffers no persistentes se quedan donde los dejo la construccion. Los del
    `dit.decoder` (`rotary_emb.inv_freq`, `original_inv_freq`) se construyen en
    CPU y el forward corre en GPU: sin este paso, RoPE falla por dispositivos
    mezclados.
    """
    persistentes = set(modulo.state_dict().keys())
    movidos = 0
    for nombre_mod, submodulo in modulo.named_modules():
        for nombre_buf, buffer in list(submodulo._buffers.items()):  # noqa: SLF001
            if buffer is None:
                continue
            completo = f"{nombre_mod}.{nombre_buf}" if nombre_mod else nombre_buf
            if completo in persistentes or buffer.device == destino:
                continue
            submodulo._buffers[nombre_buf] = buffer.to(destino)  # noqa: SLF001
            movidos += 1
    return movidos


# --------------------------------------------------------------------------- #
# Residencia temporal en VRAM (el nucleo del despacho por componente, C3)
# --------------------------------------------------------------------------- #

class _Residencia:
    """Modulo cuya copia maestra vive en RAM y que sube a VRAM solo cuando se usa.

    Subir es una copia por PCIe; **bajar no lo es**: se restaura el `.data` de
    cada tensor desde la copia maestra de RAM, que no ha cambiado (aqui no se
    entrena nada), y las replicas de VRAM se quedan sin referencias. La bajada es
    exacta por construccion y cuesta microsegundos.
    """

    def __init__(self, nombre: str, modulo: torch.nn.Module, dispositivo: torch.device) -> None:
        self.nombre = nombre
        self._modulo = modulo
        self._dispositivo = dispositivo
        self._maestro: dict[str, torch.Tensor] = {
            n: t.detach() for n, t in (*modulo.named_parameters(), *modulo.named_buffers())
        }
        self.bytes_pesos = sum(t.numel() * t.element_size() for t in self._maestro.values())
        self._arriba = False

    @property
    def modulo(self) -> torch.nn.Module:
        return self._modulo

    @property
    def residente(self) -> bool:
        return self._arriba

    def subir(self, extra_bytes: int = 0) -> None:
        """Sube el modulo a VRAM tras comprobar que cabe (guardarrail obligatorio)."""
        if self._dispositivo.type != "cuda" or self._arriba:
            return
        necesarios = int(self.bytes_pesos * _FACTOR_HOLGURA) + extra_bytes + _MARGEN_BYTES
        _exigir_vram(
            self._dispositivo,
            necesarios,
            f"subir '{self.nombre}' a VRAM ({self.bytes_pesos / _MIB:.0f} MiB de pesos)",
        )
        self._modulo.to(self._dispositivo)
        self._arriba = True

    def bajar(self) -> None:
        """Devuelve el modulo a RAM y libera su VRAM. Idempotente."""
        if not self._arriba:
            return
        for nombre, tensor in (
            *self._modulo.named_parameters(),
            *self._modulo.named_buffers(),
        ):
            tensor.data = self._maestro[nombre]
        self._arriba = False
        if self._dispositivo.type == "cuda":
            torch.cuda.empty_cache()

    def soltar(self) -> None:
        """Suelta el modulo y su copia maestra. Idempotente."""
        self.bajar()
        self._modulo = None  # type: ignore[assignment]
        self._maestro = {}


@contextmanager
def _residentes(*residencias: _Residencia, extra_bytes: int = 0):
    """Sube varios modulos a VRAM y los baja pase lo que pase.

    El `finally` no es decorativo: si `on_step` levanta `GpuBudgetExceeded` a
    mitad de una pasada, los pesos tienen que bajar igual antes de que la
    excepcion siga subiendo. Y la excepcion **no se captura**: D-17 exige que
    llegue al adapter.
    """
    subidas: list[_Residencia] = []
    try:
        for residencia in residencias:
            residencia.subir(extra_bytes=extra_bytes)
            subidas.append(residencia)
        yield
    finally:
        for residencia in reversed(subidas):
            residencia.bajar()


# --------------------------------------------------------------------------- #
# Tokenizer: adaptador a la superficie que espera el pipeline vendorizado
# --------------------------------------------------------------------------- #

class _TokenizadorParaPipeline:
    """Envuelve `TokenizadorTexto` con la firma que usa `pipeline/conditioning.py`.

    `_tokenizar()` del pipeline llama al tokenizer como lo haria `transformers`
    (`tokenizer(texto, padding=..., truncation=..., max_length=..., return_tensors="pt")`)
    y lee `salida["input_ids"]` y `salida["attention_mask"]`. El tokenizer del
    artefacto es un `tokenizers.Tokenizer` de Rust, construido y **validado** por
    `text_conditioning.construir_tokenizer()` (que comprueba que el
    post-procesador sigue anadiendo `<|endoftext|>`, el componente que se pierde
    sin dar error si alguien reconstruye el tokenizer desde vocab+merges).

    Diferencia deliberada con upstream: upstream pasa `truncation=True` y **corta
    en silencio**. Aqui se levanta un error. Perder estrofas de una letra sin que
    nadie se entere es peor que fallar, y la longitud es tambien lo que decide si
    el empaquetado del condicionamiento sigue siendo exacto en fp16.
    """

    def __init__(self, tokenizador: Any) -> None:
        self._tokenizador = tokenizador

    def __call__(
        self,
        texto: str,
        *,
        padding: str | bool | None = None,
        truncation: bool | None = None,
        max_length: int | None = None,
        return_tensors: str | None = None,
        **_ignorados: Any,
    ) -> dict[str, torch.Tensor]:
        if return_tensors not in (None, "pt"):
            raise ValueError(f"Solo se admite return_tensors='pt'; llego {return_tensors!r}.")
        ids = self._tokenizador.codificar(texto)
        if max_length is not None and len(ids) > max_length:
            raise ValueError(
                f"El texto ocupa {len(ids)} tokens y el techo de esta entrada es "
                f"{max_length}. No se trunca en silencio: recorta el texto. "
                f"(primeros 80 caracteres: {texto[:80]!r})"
            )
        if not ids:
            raise ValueError("El tokenizer devolvio una secuencia vacia.")
        input_ids = torch.tensor([ids], dtype=torch.long)
        return {"input_ids": input_ids, "attention_mask": torch.ones_like(input_ids)}


# --------------------------------------------------------------------------- #
# Promocion local a fp32 del codificador de letra (excepcion medida de C1)
# --------------------------------------------------------------------------- #

class _CodificadorLetraFp32(torch.nn.Module):
    """Ejecuta `AceStepLyricEncoder` en fp32 y devuelve la salida en el dtype del DiT.

    Por que existe: con letras de mas de ~40 tokens el flujo residual interno del
    codificador de letra llega a **1,75e5**, por encima del maximo de fp16
    (65.504). En fp16 aparecen `inf`, el residual los vuelve `NaN` y la atencion
    cruzada del DiT los reparte por **todo** el latente. El fallo se manifiesta
    en `validar_latentes()`, ocho pasos de difusion mas tarde, y aparenta ser un
    problema de la difusion. Medicion completa en el docstring del modulo.

    Por que basta con esto: la `RMSNorm` final del codificador devuelve la salida
    a |max| = 7,56, asi que **nada de lo que sale de aqui necesita rango extra**;
    el resto del pipeline sigue siendo fp16 tal cual (C1). Y no cuesta tiempo: en
    sm_61 fp32 va igual de rapido que fp16 (ratio medido 0,80-1,11), la pasada
    completa son 57 ms.

    Se envuelve en vez de editar el fichero vendorizado para que
    `modeling_acestep_v15_turbo.py` siga siendo comparable byte a byte con su
    SHA-256 registrado en `vendor/README.md`.
    """

    def __init__(self, interno: torch.nn.Module, dtype_salida: torch.dtype) -> None:
        super().__init__()
        self.interno = interno.float()
        self._dtype_salida = dtype_salida

    def forward(
        self,
        *,
        inputs_embeds: torch.Tensor,
        attention_mask: torch.Tensor,
        **kwargs: Any,
    ) -> Any:
        from transformers.modeling_outputs import BaseModelOutput  # noqa: PLC0415

        salida = self.interno(
            inputs_embeds=inputs_embeds.to(torch.float32),
            attention_mask=attention_mask,
            **kwargs,
        )
        estados = salida.last_hidden_state
        if not torch.isfinite(estados).all():
            raise RuntimeError(
                "El codificador de letra produjo valores no finitos incluso en fp32 "
                f"(nan={int(torch.isnan(estados).sum())}, inf={int(torch.isinf(estados).sum())}). "
                "Eso ya no es el desbordamiento de rango conocido de fp16: revisa los pesos."
            )
        techo = torch.finfo(self._dtype_salida).max
        pico = float(estados.abs().max())
        if pico > techo:
            raise RuntimeError(
                f"La salida del codificador de letra llega a {pico:.3g} y no cabe en "
                f"{self._dtype_salida} (maximo {techo:.6g}). La RMSNorm final deberia dejarla "
                "en el orden de 10: si no lo hace, promover solo este modulo ya no basta y "
                "hay que revisar el rango de todo el condicionamiento."
            )
        return BaseModelOutput(last_hidden_state=estados.to(self._dtype_salida))


# --------------------------------------------------------------------------- #
# Instanciacion del DiT
# --------------------------------------------------------------------------- #

def _instanciar_dit(config: Any) -> torch.nn.Module:
    """Instancia `AceStepConditionGenerationModel` sin materializar 2,45 G de pesos.

    El modelo se construye en el dispositivo `meta` (cero bytes, 0,11 s) para
    poder **asignar** despues los tensores del artefacto (`assign=True`) en vez de
    copiarlos sobre una plantilla vacia: los 4.566 MiB de `dit.*` existen una sola
    vez.

    Dos clases NO admiten el dispositivo `meta`, y por motivos distintos:

    * `ResidualFSQ` (cuantizador del tokenizador de audio) llama a `.item()` sobre
      un tensor de niveles al validarlo, y `Tensor.item()` **no existe** en meta:
      revienta durante `__init__`. Medido: `RuntimeError: Tensor.item() cannot be
      called on meta tensors`.
    * `Qwen3RotaryEmbedding` calcula `inv_freq` en el constructor y lo registra
      como buffer **no persistente**. En meta ese calculo no ocurre y el buffer no
      viaja en el `state_dict`, asi que `load_state_dict(strict=True)` lo da por
      bueno. El modelo queda roto **sin dar error**: con memoria a cero,
      `inv_freq = 0` deja RoPE sin posicion y el audio sale a -63 dBFS (basura que
      pasa `validar_latentes`); con memoria sucia, salen NaN.

    La solucion es construir **solo esas dos clases** en CPU, anidando un contexto
    de dispositivo dentro del de meta (verificado: el contexto interior manda y el
    exterior se restaura al salir). Se hace rebindeando el nombre en el espacio de
    nombres del modulo vendorizado durante la construccion y restaurandolo en
    `finally`: **el fichero vendorizado no se toca**, que es lo que permite seguir
    comparandolo con su SHA-256 registrado. Son 15 buffers y ~1 MiB en total.
    """
    from vendor import modeling_acestep_v15_turbo as modelado  # noqa: PLC0415

    def _construida_en_cpu(clase: type) -> type:
        class _EnCpu(clase):  # type: ignore[valid-type, misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                with torch.device("cpu"):
                    super().__init__(*args, **kwargs)

        _EnCpu.__name__ = clase.__name__
        _EnCpu.__qualname__ = clase.__qualname__
        return _EnCpu

    rotatorio_original = modelado.Qwen3RotaryEmbedding
    fsq_original = modelado.ResidualFSQ
    dtype_previo = torch.get_default_dtype()
    modelado.Qwen3RotaryEmbedding = _construida_en_cpu(rotatorio_original)
    modelado.ResidualFSQ = _construida_en_cpu(fsq_original)
    # El dtype por defecto decide el de los parametros creados en meta. Es fp16
    # porque el artefacto es fp16 y no se hace upcast (C1).
    torch.set_default_dtype(torch.float16)
    try:
        with torch.device("meta"):
            modelo = modelado.AceStepConditionGenerationModel(config)
    finally:
        torch.set_default_dtype(dtype_previo)
        modelado.Qwen3RotaryEmbedding = rotatorio_original
        modelado.ResidualFSQ = fsq_original

    persistentes = set(modelo.state_dict().keys())
    buffers = dict(modelo.named_buffers())
    no_persistentes = [n for n in buffers if n not in persistentes]
    en_meta = [n for n in no_persistentes if buffers[n].is_meta]
    if en_meta:
        raise RuntimeError(
            "Quedan buffers no persistentes en el dispositivo 'meta': "
            f"{en_meta[:5]}. Usarlos daria audio silenciosamente incorrecto "
            "(RoPE sin posicion), no un error. Se aborta."
        )
    _LOG.info(
        "DiT instanciado en meta: %d claves de state_dict, %d buffers no persistentes "
        "materializados en CPU.",
        len(persistentes),
        len(no_persistentes),
    )
    return modelo


# --------------------------------------------------------------------------- #
# Instanciacion del planificador de 5 Hz (Qwen3 0,6 B)
# --------------------------------------------------------------------------- #

def _instanciar_lm(config_json: dict[str, Any], dtype: torch.dtype) -> torch.nn.Module:
    """Instancia `Qwen3ForCausalLM` desde el config del artefacto, sin red.

    Mismo patron que `_instanciar_dit` y por el **mismo** motivo medido:
    `Qwen3RotaryEmbedding` calcula `inv_freq` en el constructor y lo registra como
    buffer NO persistente, asi que no viaja en el `state_dict`. Construido en
    `meta` ese calculo no ocurre, `load_state_dict(strict=...)` no lo echa en
    falta y el modelo queda roto **sin dar error**. Se construye esa unica clase
    en CPU rebindeando el nombre en el modulo de `transformers` y restaurandolo
    en `finally`.

    VERIFICADO el 2026-09-02 contra el camino de referencia: los logits de este
    modelo y los de `Qwen3ForCausalLM.from_pretrained(directorio)` sobre la misma
    entrada dan `max|diff| = 0` (identicos bit a bit), con
    `inv_freq[:3] = [1,0, 0,8058, 0,6494]` en ambos.

    Nada de `trust_remote_code` ni `auto_map` (invariante de CLAUDE.md): la clase
    se referencia por nombre y el config se rechaza si declara otra arquitectura.
    """
    from transformers import Qwen3Config, Qwen3ForCausalLM  # noqa: PLC0415
    from transformers.models.qwen3 import modeling_qwen3  # noqa: PLC0415

    arquitecturas = config_json.get("architectures") or []
    if arquitecturas != ["Qwen3ForCausalLM"]:
        raise RuntimeError(
            f"El config del planificador declara architectures={arquitecturas!r} y este "
            "shim solo carga ['Qwen3ForCausalLM']."
        )
    if "auto_map" in config_json:
        raise RuntimeError(
            "El config del planificador declara 'auto_map': eso pide cargar codigo de "
            "terceros en tiempo de ejecucion. Prohibido por CLAUDE.md."
        )
    limpio = {k: v for k, v in config_json.items() if k not in ("architectures", "auto_map")}
    config = Qwen3Config(**limpio)

    class _RotatorioEnCpu(modeling_qwen3.Qwen3RotaryEmbedding):  # type: ignore[misc, name-defined]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            with torch.device("cpu"):
                super().__init__(*args, **kwargs)

    _RotatorioEnCpu.__name__ = modeling_qwen3.Qwen3RotaryEmbedding.__name__
    _RotatorioEnCpu.__qualname__ = modeling_qwen3.Qwen3RotaryEmbedding.__qualname__

    original = modeling_qwen3.Qwen3RotaryEmbedding
    dtype_previo = torch.get_default_dtype()
    modeling_qwen3.Qwen3RotaryEmbedding = _RotatorioEnCpu
    torch.set_default_dtype(dtype)
    try:
        with torch.device("meta"):
            modelo = Qwen3ForCausalLM(config)
    finally:
        torch.set_default_dtype(dtype_previo)
        modeling_qwen3.Qwen3RotaryEmbedding = original

    persistentes = set(modelo.state_dict().keys())
    buffers = dict(modelo.named_buffers())
    en_meta = [n for n in buffers if n not in persistentes and buffers[n].is_meta]
    if en_meta:
        raise RuntimeError(
            f"Quedan buffers no persistentes del planificador en 'meta': {en_meta}. "
            "Con `inv_freq` a cero RoPE pierde la posicion y el LM emitiria codigos "
            "sin sentido SIN dar error. Se aborta."
        )
    return modelo


def _construir_tokenizer_lm(state_dict: dict[str, torch.Tensor], destino: Path) -> Any:
    """Reconstruye el tokenizer del planificador desde los blobs `aux.lm_tokenizer.*`.

    `transformers` solo sabe cargar un tokenizer rapido **desde un directorio**, y
    el tokenizer de este checkpoint no es reconstruible a mano: son 65.561
    `added_tokens_decoder` (los `<|audio_code_N|>`) y una plantilla de chat de la
    que depende cada prompt. Asi que los CUATRO ficheros se vuelcan a un directorio
    temporal y se carga de ahi. No es red: son bytes que ya viajaban dentro del
    artefacto y que salen de el byte a byte (el fusor lo verifica con
    `--verify`).

    Los blobs se **auditan antes de escribirlos**: si algun JSON declara
    `auto_map`, se aborta. `AutoTokenizer` no ejecuta codigo con
    `trust_remote_code=False` (el defecto), pero la comprobacion explicita es
    barata y no depende de que ese defecto siga siendo el mismo manana.
    """
    destino.mkdir(parents=True, exist_ok=True)
    for clave, nombre in BLOBS_LM_TOKENIZER.items():
        texto = _texto_de_blob(state_dict, clave)
        if nombre.endswith(".json"):
            try:
                datos = json.loads(texto)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{clave!r} no es JSON valido: {exc}") from exc
            if isinstance(datos, dict) and "auto_map" in datos:
                raise RuntimeError(
                    f"{clave!r} declara 'auto_map': cargarlo ejecutaria codigo de terceros. "
                    "Prohibido por CLAUDE.md."
                )
        (destino / nombre).write_text(texto, encoding="utf-8")

    from transformers import AutoTokenizer  # noqa: PLC0415

    tokenizer = AutoTokenizer.from_pretrained(str(destino))
    if tokenizer.chat_template is None:
        raise RuntimeError(
            "El tokenizer del planificador se cargo SIN plantilla de chat. Todos los "
            "prompts de `vendor/lm/prompt.py` se construyen con `apply_chat_template`, "
            f"asi que sin ella no hay planificacion. Falta el blob "
            f"'aux.lm_tokenizer.chat_template_jinja' en el artefacto."
        )
    return tokenizer


def _forzar_atencion_eager(modelo: torch.nn.Module, config: Any) -> None:
    """C4: atencion eager por asignacion directa, con assert duro.

    En sm_61 SDPA cae al kernel mem-efficient y va **12,9x mas lento** que eager
    con softmax en fp32 (282,20 ms frente a 21,87 ms a `[1,16,2250,128]`), sin un
    solo mensaje. `set_attn_implementation("eager")` devuelve `"sdpa"` sin avisar
    y dejar el valor en `None` da `KeyError`, asi que la unica via fiable es
    asignar el atributo privado a mano.

    La comprobacion recorre **todos** los modulos de atencion, no solo el primero,
    y **no es tautologica**: `transformers` comparte el objeto de configuracion
    entre submodulos, de modo que la asignacion unica normalmente basta; pero si
    una version futura le da a alguna capa su propia copia de la config, esa capa
    seguira en `"sdpa"` y este assert es lo unico que lo detecta. Aqui **no se
    repara en silencio**: se aborta. Un fallo ruidoso en el arranque cuesta
    segundos; una pista de 5 minutos que deberia durar 23 s cuesta una tarde de
    depuracion y contamina las mediciones de T-03.

    NO SIMPLIFICAR esto por un `set_attn_implementation()` de una linea.
    """
    from vendor import modeling_acestep_v15_turbo as modelado  # noqa: PLC0415

    previo = getattr(config, "_attn_implementation", None)
    config._attn_implementation = "eager"  # noqa: SLF001

    desviados = [
        (nombre, submodulo.config._attn_implementation)  # noqa: SLF001
        for nombre, submodulo in modelo.named_modules()
        if isinstance(submodulo, modelado.AceStepAttention)
        and submodulo.config._attn_implementation != "eager"  # noqa: SLF001
    ]
    if getattr(modelo.decoder.config, "_attn_implementation", None) != "eager":
        desviados.append(("decoder(config del modulo)", modelo.decoder.config._attn_implementation))
    if desviados:
        raise RuntimeError(
            "No se pudo forzar la atencion 'eager' en el DiT: "
            f"{len(desviados)} modulo(s) siguen en otra implementacion "
            f"(por ejemplo {desviados[:3]}).\n"
            "En sm_61 la ruta SDPA cae al kernel mem-efficient y es 12,9x mas lenta "
            "que eager, en silencio. Se aborta en lugar de generar a un doceavo de "
            "velocidad sin avisar."
        )
    _LOG.info(
        "Atencion forzada a 'eager' en el DiT (venia de %r); verificados %d modulos de atencion.",
        previo,
        sum(
            1
            for _, m in modelo.named_modules()
            if isinstance(m, modelado.AceStepAttention)
        ),
    )


# --------------------------------------------------------------------------- #
# Audio devuelto al adapter
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class AudioRenderizado:
    """Equivalente local de `adapter.RenderedAudio`.

    Se define aqui, y no se importa de `adapter`, porque en el contenedor el
    adapter corre como `__main__` (`ENTRYPOINT ["python", "adapters/ace_step/adapter.py"]`):
    un `from adapter import RenderedAudio` volveria a ejecutar el fichero entero
    como un segundo modulo. El adapter consume este objeto por duck typing
    (`getattr(rendered, "sample_rate", 0)`, etc.), asi que lo unico que importa
    son los nombres de los campos, que son exactamente estos.
    """

    sample_rate: int
    channels: int
    duration_s: float | None = None
    pcm16: bytes | None = None
    path: str | None = None


def _a_pcm16(onda: torch.Tensor) -> tuple[bytes, int, int]:
    """Convierte `[1, C, N]` en fp32 a PCM de 16 bit entrelazado little-endian.

    El adapter escribe el WAV con el modulo `wave` de la biblioteca estandar, asi
    que la conversion desde tensores es responsabilidad del shim, que es quien
    tiene torch a mano.

    No se normaliza el loudness: eso es `T-19`/`T-45` (EBU R128 por destino). Aqui
    solo se recorta a [-1, 1] para no envolver la senal, y se avisa si hubo
    recorte, porque un recorte silencioso se oye en G1 y nadie sabria de donde
    salio.
    """
    if onda.dim() != 3 or onda.shape[0] != 1:
        raise RuntimeError(
            f"Se esperaba una forma de onda [1, C, N] y llego {tuple(onda.shape)}."
        )
    if sys.byteorder != "little":
        raise RuntimeError(
            "Este conversor emite PCM little-endian tal como lo espera el modulo "
            f"'wave' del adapter, y esta maquina es {sys.byteorder}-endian."
        )
    onda = onda[0].detach().to("cpu", torch.float32)
    if not torch.isfinite(onda).all():
        raise RuntimeError(
            "El decode del VAE devolvio muestras no finitas (NaN o inf). No se "
            "entrega audio corrupto."
        )
    pico = float(onda.abs().max())
    if pico > 1.0:
        _LOG.warning(
            "La forma de onda llega a %.3f de pico y se recorta a 1,0 (%.1f%% por encima). "
            "La normalizacion de loudness es T-19/T-45, no esta etapa.",
            pico,
            (pico - 1.0) * 100.0,
        )
    enteros = (onda.clamp(-1.0, 1.0) * 32767.0).round().to(torch.int16)
    canales, muestras = enteros.shape
    # [C, N] -> [N, C] entrelazado, que es el orden que exige un WAV.
    return enteros.transpose(0, 1).contiguous().numpy().tobytes(), canales, muestras


# --------------------------------------------------------------------------- #
# El pipeline
# --------------------------------------------------------------------------- #

class PipelineAceStep:
    """Pipeline `text2music` de ACE-Step 1.5 turbo con despacho por componente.

    Construir esta clase a mano no es el camino: usa `build_pipeline()`, que es lo
    que invoca el adapter y lo unico que sabe consumir el `state_dict` sin
    duplicar VRAM.
    """

    def __init__(
        self,
        *,
        modelo: torch.nn.Module,
        residencia_dit_encoder: _Residencia,
        residencia_text_encoder: _Residencia,
        residencia_vae: _Residencia,
        tokenizador: Any,
        silence_latent: torch.Tensor,
        dispositivo: torch.device,
        dtype: torch.dtype,
        offload: bool,
        planificador: Any = None,
        residencia_audio_tokenizer: _Residencia | None = None,
        residencia_detokenizer: _Residencia | None = None,
        dir_tokenizer_lm: Path | None = None,
    ) -> None:
        self._modelo = modelo
        self._dit_encoder = residencia_dit_encoder
        self._text_encoder = residencia_text_encoder
        self._vae = residencia_vae
        self._tokenizador = tokenizador
        self._silence_latent = silence_latent
        self._dispositivo = dispositivo
        self._dtype = dtype
        self._offload = offload
        self._liberado = False
        # -- planificador de 5 Hz (puede no existir: artefacto sin `lm.*`) --- #
        self._planificador = planificador
        self._audio_tokenizer = residencia_audio_tokenizer
        self._detokenizer = residencia_detokenizer
        self._dir_tokenizer_lm = dir_tokenizer_lm

    # -- ciclo de vida ------------------------------------------------------ #

    def warmup(self) -> None:
        """Primera pasada completa en vacio: compila kernels y valida el camino.

        Genera la pista mas corta que el modelo admite (128 tramas latentes, 5,12 s
        —el suelo que impone upstream con `max(128, ...)`) y la decodifica. Cuesta
        unos pocos segundos y hace dos cosas que valen ese coste: paga aqui la
        seleccion de algoritmo de cuDNN y la carga de modulos de CUDA, que si no
        contaminarian la medicion de la primera inferencia (S-01: el warm-up es un
        termino de 30-120 s del arranque en frio, no un detalle); y **falla en el
        arranque** si el despacho, la carga o la atencion no estan bien, en lugar
        de fallar en medio de la primera generacion de verdad.
        """
        self._comprobar_vivo()
        inicio = time.perf_counter()
        rendered = self.render(
            style_prompt="warmup, instrumental test tone",
            lyrics=None,
            duration_s=6,
            instrumental=True,
            seed=0,
            params={},
            on_step=lambda paso, total: None,
        )
        _LOG.info(
            "Warm-up completado en %.2f s (%.2f s de audio descartados).",
            time.perf_counter() - inicio,
            rendered.duration_s or 0.0,
        )

    def release(self) -> None:
        """Suelta pesos y VRAM. Idempotente; segura tras un fallo de construccion."""
        if self._liberado:
            return
        self._liberado = True
        for residencia in (
            self._vae,
            self._text_encoder,
            self._dit_encoder,
            self._audio_tokenizer,
            self._detokenizer,
        ):
            if residencia is None:
                continue
            try:
                residencia.soltar()
            except Exception as exc:  # noqa: BLE001  (release no puede tumbar el unload)
                _LOG.warning("Fallo al soltar '%s' (se ignora): %r", residencia.nombre, exc)
        self._modelo = None  # type: ignore[assignment]
        self._silence_latent = None  # type: ignore[assignment]
        self._tokenizador = None
        # El planificador son ~1.265 MiB de RAM; soltarlo es la mitad del sentido
        # de release() cuando el proceso sigue vivo tras un unload().
        self._planificador = None
        if self._dir_tokenizer_lm is not None:
            shutil.rmtree(self._dir_tokenizer_lm, ignore_errors=True)
            self._dir_tokenizer_lm = None
        if self._dispositivo.type == "cuda":
            torch.cuda.empty_cache()

    def _comprobar_vivo(self) -> None:
        if self._liberado:
            raise RuntimeError("El pipeline ya fue liberado con release(); no se puede usar.")

    # -- generacion --------------------------------------------------------- #

    def render(
        self,
        *,
        style_prompt: str,
        lyrics: str | None,
        duration_s: int,
        instrumental: bool,
        seed: int | None,
        params: dict[str, Any],
        on_step: Callable[[int, int], None],
    ) -> AudioRenderizado:
        """Genera una pista completa: condicionamiento, difusion y decode.

        `on_step(paso, total)` se invoca en **cada** paso de difusion y en cada
        ventana del decode, con un contador unico y monotono sobre el total de
        pasos reales. Es el punto de control de D-17: si levanta `GpuBudgetExceeded`
        la excepcion **se deja propagar** intacta; aqui no se captura nunca.
        """
        self._comprobar_vivo()
        opciones = self._validar_params(params)

        tramas, duracion = longitud_latente(duration_s)
        if tramas > MAX_TRAMAS_LATENTES:
            raise ValueError(
                f"Duracion pedida {duration_s} s ({tramas} tramas latentes) por encima "
                f"del techo medido de {MAX_TRAMAS_LATENTES // (SAMPLE_RATE // LATENT_HOP)} s. "
                "En la GPU objetivo 420 s pasan y 480 s revientan; no se intenta."
            )

        plan = planificar_trozos(
            tramas,
            ventana=opciones["ventana_vae"],
            solape=opciones["solape_vae"],
            guarda=opciones["guarda_vae"],
        )
        # `usar_lm` pedido explicitamente y sin planificador = error duro. Sin
        # pedir nada y sin planificador = camino de siempre con un aviso. La
        # diferencia importa: degradar en silencio una peticion EXPLICITA es
        # exactamente lo que dejo el planificador desconectado sin que nadie se
        # enterara; pero abortar porque el llamante no dijo nada impediria cargar
        # el artefacto anterior, que sigue siendo valido.
        hay_planificador = self._planificador is not None
        if opciones["usar_lm"] is True and not hay_planificador:
            raise RuntimeError(
                "Se pidio usar_lm=True pero este artefacto no trae el planificador de 5 Hz "
                f"(prefijo {PREFIJO_LM!r}). Reconstruyelo con "
                "`build_artifact.py --incluir-lm`, o pasa usar_lm=False para generar por el "
                "camino de siempre. No se degrada en silencio: una pista sin plan y otra con "
                "plan no son comparables, y el A/B es justo lo que se esta midiendo."
            )
        usar_lm = hay_planificador if opciones["usar_lm"] is None else bool(opciones["usar_lm"])
        codigos_objetivo = _codigos_para_tramas(tramas) if usar_lm else 0
        # El total incluye los codigos del planificador porque en esta tarjeta el
        # planificador es la MAYORIA del tiempo de pared: MEDIDO en CPU, 342-448
        # ms por codigo con CFG 2,0, frente a ~2,8 s por los ocho pasos enteros de
        # difusion. Un progreso que solo contase la difusion se quedaria clavado en
        # 0 durante casi toda la generacion. Si ademas se dispara la fase de
        # razonamiento, esta emite tokens que no estaban en la cuenta; por eso el
        # total se ensancha en vez de mentir hacia abajo.
        total_pasos = PASOS_POR_DEFECTO + len(plan.inicios) + codigos_objetivo
        hechos = 0

        def _avanzar(_hecho: int = 0, _total: int = 0) -> None:
            nonlocal hechos
            hechos += 1
            on_step(hechos, max(total_pasos, hechos))

        tiempos: dict[str, float] = {}

        # -- 0. Planificador de 5 Hz ---------------------------------------- #
        lm_hints: torch.Tensor | None = None
        info_plan: dict[str, Any] | None = None
        if usar_lm:
            marca = time.perf_counter()
            lm_hints, info_plan = self._planificar(
                style_prompt=style_prompt,
                lyrics=None if instrumental else lyrics,
                tramas=tramas,
                codigos_objetivo=codigos_objetivo,
                seed=seed,
                opciones=opciones,
                on_token=_avanzar,
            )
            tiempos["planning_s"] = time.perf_counter() - marca
            # El prefijo y el orden de los argumentos son contrato con
            # `spikes/generate_smoke.py::EscuchaEtapas`, que lee `args[0]` como la
            # duracion declarada de la etapa. No reordenar.
            _LOG.info(
                "Planificador listo en %.2f s: %d codigos a 5 Hz -> hints %s "
                "(fase1 %.2f s, fase2 %.2f s, rms %.4f). Metadatos del plan: %s",
                tiempos["planning_s"],
                codigos_objetivo,
                tuple(lm_hints.shape),
                info_plan["tiempos"].get("fase1", 0.0),
                info_plan["tiempos"].get("fase2", 0.0),
                info_plan["hints_rms"],
                info_plan["metadatos"],
            )
        else:
            _LOG.info(
                "Planificador NO usado (%s): `src_latents` sera el latente de silencio, "
                "que es el camino que el pipeline tenia antes de conectarlo.",
                "usar_lm=False" if opciones["usar_lm"] is False
                else "el artefacto no trae lm.*",
            )

        # -- 1. Condicionamiento -------------------------------------------- #
        # Suben a la vez el Qwen3 (1.136 MiB) y el `dit.encoder` (1.160 MiB)
        # porque la funcion vendorizada los usa dentro de la misma llamada: el
        # codificador de texto produce los estados ocultos y el codificador de
        # condicion los empaqueta con el timbre y la letra. Los dos bajan al
        # salir, asi que la difusion arranca con solo `dit.decoder` residente.
        marca = time.perf_counter()
        with _residentes(self._text_encoder, self._dit_encoder):
            cond = preparar_condicionamiento_text2music(
                model=self._modelo,
                text_encoder=self._text_encoder.modulo,
                text_tokenizer=self._tokenizador,
                silence_latent=self._silence_latent,
                style_prompt=style_prompt,
                lyrics=None if instrumental else lyrics,
                duracion_s=float(duration_s),
                device=self._dispositivo,
                dtype=self._dtype,
                vocal_language=opciones["vocal_language"],
                bpm=opciones["bpm"],
                keyscale=opciones["keyscale"],
                timesignature=opciones["timesignature"],
                lm_hints_25Hz=lm_hints,
            )
        tiempos["conditioning_s"] = time.perf_counter() - marca
        del lm_hints

        # Comprobacion de finitud AQUI, y no ocho pasos de difusion mas tarde: un
        # solo NaN en el condicionamiento se reparte por todo el latente via la
        # atencion cruzada, y entonces el sintoma aparece en `validar_latentes()`
        # aparentando un fallo de la difusion. Es exactamente como se manifesto el
        # desbordamiento del codificador de letra.
        for etiqueta, tensor in (
            ("encoder_hidden_states", cond.encoder_hidden_states),
            ("context_latents", cond.context_latents),
        ):
            if not torch.isfinite(tensor).all():
                raise RuntimeError(
                    f"El condicionamiento produjo '{etiqueta}' con valores no finitos "
                    f"(nan={int(torch.isnan(tensor).sum())}, inf={int(torch.isinf(tensor).sum())}). "
                    "Condicionar el DiT con esto convierte el latente entero en NaN. "
                    "Sospechoso habitual: desbordamiento de rango de fp16 en algun modulo "
                    "del codificador de condicion."
                )

        l_enc = int(cond.encoder_hidden_states.shape[1])
        if l_enc > text_conditioning.MAX_TOKENS_CROSS_ATTENTION:
            raise ValueError(
                f"La secuencia de atencion cruzada mide {l_enc} tokens y el techo es "
                f"{text_conditioning.MAX_TOKENS_CROSS_ATTENTION}: `pack_sequences` suma la "
                "mascara en el dtype del modelo y fp16 deja de representar enteros exactos "
                "a partir de 2048, asi que por encima el empaquetado es incorrecto SIN dar "
                "error. Acorta la letra o el prompt de estilo."
            )
        _LOG.info(
            "Condicionamiento listo en %.2f s: L_enc=%d, %d tramas latentes (%.1f s).",
            tiempos["conditioning_s"],
            l_enc,
            cond.latent_length,
            cond.duracion_s,
        )

        # -- 2. Difusion ----------------------------------------------------- #
        # Guardarrail ANTES de asignar el ruido inicial y las caches de atencion.
        _exigir_vram(
            self._dispositivo,
            int(_pico_difusion_bytes(tramas) * _FACTOR_HOLGURA) + _MARGEN_BYTES,
            f"el bucle de difusion de {tramas} tramas latentes ({duracion:.1f} s)",
        )
        marca = time.perf_counter()
        resultado = generar_latentes_text2music(
            model=self._modelo,
            cond=cond,
            seed=seed,
            shift=opciones["shift"],
            on_step=_avanzar,
        )
        tiempos["diffusion_s"] = time.perf_counter() - marca
        latentes = resultado.target_latents
        # El condicionamiento ya no hace falta y ocupa VRAM que el decode va a
        # necesitar: la cache de atencion cruzada del DiT vive dentro de
        # `generar_latentes_text2music` y muere con ella, pero estos tensores no.
        del cond, resultado
        if self._dispositivo.type == "cuda":
            torch.cuda.empty_cache()
        _LOG.info(
            "Difusion completada en %.2f s (%.3f s/paso, %d pasos).",
            tiempos["diffusion_s"],
            tiempos["diffusion_s"] / PASOS_POR_DEFECTO,
            PASOS_POR_DEFECTO,
        )

        # -- 3. Decode del VAE, siempre por trozos (C2) ---------------------- #
        marca = time.perf_counter()
        with _residentes(self._vae):
            onda = decodificar_latentes(
                decoder=self._vae.modulo,
                target_latents=latentes,
                on_step=_avanzar,
                ventana=opciones["ventana_vae"],
                solape=opciones["solape_vae"],
                guarda=opciones["guarda_vae"],
            )
        del latentes
        if self._dispositivo.type == "cuda":
            torch.cuda.empty_cache()
        tiempos["decode_s"] = time.perf_counter() - marca

        pcm16, canales, muestras = _a_pcm16(onda)
        del onda
        duracion_real = muestras / float(SAMPLE_RATE)
        _LOG.info(
            "Decode en %.2f s (%d ventanas). Pista: %.2f s, %d canales, %d muestras. "
            "Totales: condicionamiento %.2f s + difusion %.2f s + decode %.2f s.",
            tiempos["decode_s"],
            len(plan.inicios),
            duracion_real,
            canales,
            muestras,
            tiempos["conditioning_s"],
            tiempos["diffusion_s"],
            tiempos["decode_s"],
        )
        return AudioRenderizado(
            sample_rate=SAMPLE_RATE,
            channels=canales,
            duration_s=duracion_real,
            pcm16=pcm16,
        )

    # -- planificador ------------------------------------------------------- #

    def _planificar(
        self,
        *,
        style_prompt: str,
        lyrics: str | None,
        tramas: int,
        codigos_objetivo: int,
        seed: int | None,
        opciones: dict[str, Any],
        on_token: Callable[..., None],
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        """Ejecuta el planificador y devuelve `(lm_hints_25Hz, info)`.

        Cadena completa, que es lo unico que hace esta funcion:

            prompt del planificador
              -> generacion restringida (lista blanca de 64.000 `<|audio_code_N|>`
                 + EOS forzado en el codigo `int(duracion*5)`)
              -> codigos a 5 Hz
              -> `model.tokenizer.quantizer.get_output_from_indices`  [1, N, 2048]
              -> `model.detokenizer`                                  [1, N*5, 64]
              -> `lm_hints_25Hz`

        Donde corre cada pieza y por que:

        * El **LM** en CPU. En fp16 son 1.264 MiB frente a 810 MiB de holgura de
          VRAM, y sm_61 no ejecuta bf16. Ademas el diseno de upstream ya es
          secuencial: `gpu_config.py` del tier de 6-8 GB descarga el DiT antes de
          arrancar el LM, o sea que los dos nunca son residentes a la vez.
        * El **cuantizador y el detokenizador** suben a VRAM el rato justo. Son
          401 MiB y en ese momento solo `dit.decoder` esta residente, asi que
          sobran ~4 GiB. En CPU tendrian que correr en fp16, que en x86 no tiene
          kernels vectorizados y es la via lenta por nada.

        Aviso que vale la generacion entera: los cinco bufferes NO persistentes
        del FSQ (`_levels`, `_basis`, `implicit_codebook`, `scales`,
        `soft_clamp_input_value`) no viajan en el `state_dict`. Hasta que se
        conecto el planificador daba igual porque `text2music` no llamaba a
        `tokenize`/`detokenize`; ahora si se llaman. `_instanciar_dit` los
        materializa construyendo `ResidualFSQ` en CPU, y por eso ahi hay un
        `assert` que aborta si alguno se queda en `meta`: con esos bufferes a cero
        los hints serian basura **sin levantar ningun error**.
        """
        from vendor.lm.planificador import hints_25Hz  # noqa: PLC0415

        duracion_lm = _duracion_para_codigos(codigos_objetivo)
        metadatos = {
            "bpm": opciones["bpm"],
            "keyscale": opciones["keyscale"],
            "timesignature": opciones["timesignature"],
        }
        plan = self._planificador.planificar(
            estilo=style_prompt,
            letra=lyrics or "",
            duracion_s=duracion_lm,
            metadatos_usuario=metadatos,
            temperatura=float(opciones["lm_temperatura"]),
            escala_cfg=float(opciones["lm_cfg"]),
            # La MISMA semilla que la difusion. Es lo que permite generar la
            # version con planificador y la version sin el y saber que la unica
            # diferencia entre las dos es el planificador.
            semilla=seed,
            on_token=on_token,
        )
        if len(plan.codigos) != codigos_objetivo:
            raise RuntimeError(
                f"El planificador devolvio {len(plan.codigos)} codigos y hacian falta "
                f"{codigos_objetivo} para {tramas} tramas latentes."
            )

        # Codigos -> hints. El cuantizador y el detokenizador viven en RAM: suben
        # a VRAM solo para esta llamada.
        with _residentes(self._audio_tokenizer, self._detokenizer):
            with torch.inference_mode():
                hints = hints_25Hz(
                    self._modelo,
                    plan.codigos,
                    device=self._dispositivo,
                    dtype=self._dtype,
                )
            # `.clone()` saca el tensor de `inference_mode`: va a viajar dentro
            # del condicionamiento y a acabar en la cache de atencion del DiT
            # durante ocho pasos, y un tensor de inferencia ahi dentro es una
            # trampa que solo salta mas tarde y lejos.
            hints = hints.to(device=self._dispositivo, dtype=self._dtype).clone()

        if not torch.isfinite(hints).all():
            raise RuntimeError(
                "El detokenizador produjo hints no finitos "
                f"(nan={int(torch.isnan(hints).sum())}, inf={int(torch.isinf(hints).sum())}). "
                "Esto sustituye a `src_latents`: condicionar el DiT con esto convierte el "
                "latente entero en NaN."
            )
        esperadas = codigos_objetivo * VENTANA_AGRUPACION
        if hints.dim() != 3 or hints.shape[0] != 1 or hints.shape[1] != esperadas:
            raise RuntimeError(
                f"Los hints tienen forma {tuple(hints.shape)} y se esperaba "
                f"[1, {esperadas}, 64] ({codigos_objetivo} codigos x "
                f"{VENTANA_AGRUPACION} fotogramas)."
            )
        info = {
            "metadatos": plan.metadatos,
            "codigos": len(plan.codigos),
            "duracion_pedida_al_lm_s": duracion_lm,
            "segundos_de_plan": plan.segundos,
            "tiempos": plan.tiempos,
            "hints_rms": float(hints.float().pow(2).mean().sqrt()),
            "hints_min": float(hints.float().min()),
            "hints_max": float(hints.float().max()),
        }
        return hints, info

    # -- parametros --------------------------------------------------------- #

    @staticmethod
    def _validar_params(params: dict[str, Any]) -> dict[str, Any]:
        """Valida `model_params` contra una lista blanca y aplica los defectos.

        El adapter no interpreta `model_params` (no hay `params_schema` hasta
        T-30), pero eso no autoriza a tragarse en silencio lo que llegue: un
        parametro desconocido se rechaza con la lista de los admitidos.
        """
        desconocidos = sorted(set(params) - _PARAMS_ADMITIDOS)
        if desconocidos:
            raise ValueError(
                f"model_params desconocidos: {desconocidos}. Admitidos: "
                f"{sorted(_PARAMS_ADMITIDOS)}."
            )
        opciones = {
            "shift": float(params.get("shift", SHIFT_POR_DEFECTO)),
            "vocal_language": str(params.get("vocal_language", "es")),
            "bpm": params.get("bpm"),
            "keyscale": params.get("keyscale"),
            "timesignature": params.get("timesignature"),
            "ventana_vae": int(params.get("ventana_vae", VENTANA_LATENTE_POR_DEFECTO)),
            "solape_vae": int(params.get("solape_vae", SOLAPE_LATENTE_POR_DEFECTO)),
            "guarda_vae": int(params.get("guarda_vae", GUARDA_LATENTE_POR_DEFECTO)),
            # OJO: `None` significa «el llamante no dijo nada», y NO es lo mismo
            # que `True`. Lo resuelve `render()`, que es quien sabe si el
            # artefacto trae planificador. Sin esta distincion, el defecto True
            # haria que un artefacto SIN `lm.*` fallara ya en el warm-up y no se
            # pudiera ni cargar.
            "usar_lm": None if params.get("usar_lm") is None else bool(params["usar_lm"]),
            "lm_cfg": float(params.get("lm_cfg", 2.0)),
            "lm_temperatura": float(params.get("lm_temperatura", 0.85)),
        }
        if opciones["lm_cfg"] < 1.0:
            raise ValueError(f"lm_cfg debe ser >= 1,0; llego {opciones['lm_cfg']}.")
        if opciones["lm_temperatura"] <= 0.0:
            raise ValueError(
                f"lm_temperatura debe ser > 0; llego {opciones['lm_temperatura']}."
            )
        return opciones


# --------------------------------------------------------------------------- #
# Construccion del planificador desde el artefacto
# --------------------------------------------------------------------------- #

def _construir_planificador(
    state_dict: dict[str, torch.Tensor],
    dispositivo: torch.device,
) -> tuple[Any, Path]:
    """Saca del artefacto el planificador de 5 Hz y lo deja listo en CPU.

    Consume `lm.*` (310 tensores) y los cinco blobs `aux.lm*` (config del modelo
    mas los cuatro ficheros del tokenizer). Devuelve el
    `PlanificadorLM` y el directorio temporal del tokenizer, que el pipeline
    borra en `release()`.

    Tres detalles que no son opcionales:

    1. **El LM se queda en CPU**, siempre, aunque el resto corra en CUDA. En fp16
       son 1.264 MiB frente a los 810 MiB de holgura de la GTX 1070, y sm_61 no
       tiene bf16. No es un apano: `gpu_config.py` de upstream descarga el DiT
       antes de arrancar el LM en este mismo tier de 6-8 GB, o sea que el plan
       secuencial es el diseno.
    2. **`tie_weights()` despues de cargar.** El checkpoint no trae
       `lm_head.weight` (`tie_word_embeddings: true`), asi que `strict=True`
       fallaria. Se carga con `strict=False`, se comprueba que la UNICA clave que
       falta es esa y se atan. Si faltara cualquier otra cosa, se aborta.
    3. **Los pesos se clonan** al sacarlos del mapeo (lo hace `_extraer`): un LM
       mapeado se releeria del disco en cada generacion.
    """
    nombre_dtype = os.environ.get(ENV_LM_DTYPE, "bf16").strip().lower()
    if nombre_dtype not in _LM_DTYPES:
        raise RuntimeError(
            f"{ENV_LM_DTYPE}={nombre_dtype!r} no es valido; admitidos: "
            f"{sorted(_LM_DTYPES)}."
        )
    dtype_lm = _LM_DTYPES[nombre_dtype]
    inicio = time.perf_counter()

    config_lm = json.loads(_texto_de_blob(state_dict, CLAVE_LM_CONFIG))
    modelo_lm = _instanciar_lm(config_lm, dtype_lm)

    pesos = _extraer(state_dict, PREFIJO_LM, torch.device("cpu"), CLAVES_LM)
    # El dtype de ejecucion manda sobre el de almacenamiento. Se convierte tensor
    # a tensor **sacandolo del diccionario**: hacerlo por comprension mantendria
    # vivas las dos versiones enteras a la vez (1.265 + 2.529 MiB en fp32).
    for clave in list(pesos):
        tensor = pesos[clave]
        if tensor.dtype is not dtype_lm:
            pesos[clave] = tensor.to(dtype_lm)
        del tensor
    faltan, sobran = modelo_lm.load_state_dict(pesos, strict=False, assign=True)
    del pesos
    if sobran:
        raise RuntimeError(
            f"El artefacto trae claves del planificador que el modelo no espera: "
            f"{list(sobran)[:5]}."
        )
    if list(faltan) != ["lm_head.weight"]:
        raise RuntimeError(
            f"Al planificador le faltan claves distintas de la esperada: {list(faltan)}. "
            "La unica ausencia legitima es 'lm_head.weight' (`tie_word_embeddings: true`)."
        )
    modelo_lm.tie_weights()
    modelo_lm.eval()
    modelo_lm.requires_grad_(False)

    en_meta = [
        n for n, t in (*modelo_lm.named_parameters(), *modelo_lm.named_buffers()) if t.is_meta
    ]
    if en_meta:
        raise RuntimeError(
            f"Quedan {len(en_meta)} tensores del planificador en 'meta' (por ejemplo "
            f"{en_meta[:5]}). Usarlos daria codigos sin sentido, no un error."
        )
    if modelo_lm.lm_head.weight.data_ptr() != modelo_lm.model.embed_tokens.weight.data_ptr():
        raise RuntimeError(
            "`lm_head.weight` no comparte almacenamiento con `embed_tokens.weight` tras "
            "`tie_weights()`: la cabeza de salida quedaria sin inicializar."
        )

    dir_tokenizer = Path(tempfile.mkdtemp(prefix="ace_step_lm_tok_"))
    try:
        tokenizer = _construir_tokenizer_lm(state_dict, dir_tokenizer)
        from vendor.lm.planificador import PlanificadorLM  # noqa: PLC0415

        planificador = PlanificadorLM(modelo_lm, tokenizer)
    except BaseException:
        shutil.rmtree(dir_tokenizer, ignore_errors=True)
        raise

    bytes_lm = sum(p.numel() * p.element_size() for p in modelo_lm.parameters())
    _LOG.info(
        "Planificador de 5 Hz listo en %.2f s: %d parametros en %s sobre CPU (%.0f MiB de "
        "RAM). El dispositivo de computo del resto del pipeline es %s; el LM NO sube a el.",
        time.perf_counter() - inicio,
        sum(p.numel() for p in modelo_lm.parameters()),
        nombre_dtype,
        bytes_lm / _MIB,
        dispositivo,
    )
    return planificador, dir_tokenizer


# --------------------------------------------------------------------------- #
# La factoria
# --------------------------------------------------------------------------- #

def build_pipeline(
    *,
    state_dict: dict[str, torch.Tensor],
    device: Any,
    dtype: Any,
    offload: bool,
) -> PipelineAceStep:
    """Construye el pipeline real desde el `state_dict` completo del artefacto.

    Es la funcion que resuelve `adapter._resolve_pipeline_factory()`. Recibe
    exactamente estos cuatro argumentos por palabra clave y nada mas.

    El `state_dict` llega **mapeado en CPU** (el adapter hace
    `load_file(ruta, device="cpu")` desde el 2026-09-02: ver el bloque de
    comentario de `adapter.py`, etapa 3). Los tensores estan respaldados por el
    fichero, no por RAM: quien decide que sube a VRAM es esta funcion, componente
    a componente. Se consume destructivamente —cada componente se saca con `pop`,
    se **materializa** donde le toca y la entrada del mapeo se libera acto
    seguido— y al volver el diccionario del llamante esta vacio.

    Args:
        state_dict: los 1.177 tensores del artefacto, o 1.492 si trae ademas el
            planificador de 5 Hz (`lm.*`, 310 tensores + 5 blobs `aux.lm*`).
        device: dispositivo de computo (`"cuda:0"`).
        dtype: precision pedida por el `RunnerContext`. **Manda el artefacto**: es
            fp16 y no se hace upcast (C1); si se pide otra cosa se avisa.
        offload: bandera del adapter. Se registra, pero el despacho por componente
            es **incondicional**: es la unica configuracion en la que el modelo
            entra en 8 GB, y desactivarlo no daria mas velocidad sino un fallo de
            memoria en la primera generacion.

    Returns:
        `PipelineAceStep`, conforme al protocolo `adapter._AceStepPipeline`.
    """
    if not isinstance(state_dict, dict):
        raise TypeError(f"Se esperaba un dict de tensores; llego {type(state_dict).__name__}.")
    dispositivo = _normalizar_dispositivo(device)
    inicio = time.perf_counter()
    if dispositivo.type != "cuda":
        _LOG.warning(
            "El pipeline se esta construyendo en %s. Todas las cifras de coste de este "
            "fichero estan medidas en CUDA (sm_61) y no aplican; una generacion real en "
            "CPU no es viable.",
            dispositivo,
        )
    else:
        libre, total = torch.cuda.mem_get_info(dispositivo)
        _LOG.info(
            "Construyendo el pipeline en %s: %.0f MiB libres de %.0f MiB, %d tensores en "
            "el state_dict, offload=%s.",
            dispositivo,
            libre / _MIB,
            total / _MIB,
            len(state_dict),
            offload,
        )
        if not offload:
            _LOG.warning(
                "offload=False, pero el despacho por componente se aplica igual: es la "
                "unica configuracion en la que el modelo entra en 8 GB (medido: pico de "
                "6.190 MiB de 8.192 con el despacho activo). Desactivarlo no daria mas "
                "velocidad, daria un fallo de memoria en la primera generacion."
            )

    pipeline: PipelineAceStep | None = None
    residencia_vae: _Residencia | None = None
    residencia_texto: _Residencia | None = None
    residencia_encoder: _Residencia | None = None
    residencia_audio_tok: _Residencia | None = None
    residencia_detok: _Residencia | None = None
    dir_tokenizer_lm: Path | None = None
    try:
        # -- 0. dtype: manda el artefacto (C1) ------------------------------- #
        muestra = state_dict.get("dit.decoder.layers.0.mlp.up_proj.weight")
        if muestra is None:
            raise RuntimeError(
                "El artefacto no trae 'dit.decoder.layers.0.mlp.up_proj.weight': no es el "
                "checkpoint de ACE-Step 1.5 turbo que este shim sabe cargar."
            )
        dtype_artefacto = muestra.dtype
        del muestra
        if dtype_artefacto is not torch.float16:
            _LOG.warning(
                "El artefacto viene en %s y este shim esta medido sobre fp16.", dtype_artefacto
            )
        if dtype is not None:
            pedido = text_conditioning._resolver_dtype(dtype)  # noqa: SLF001
            if pedido is not dtype_artefacto:
                _LOG.warning(
                    "Se pidio dtype=%s pero el artefacto es %s y NO se hace upcast: "
                    "promoverlo a fp32 son +5.878 MiB (no cabe en 8 GB) y en sm_61 no "
                    "compensa (cuBLAS ya promociona internamente; ratio fp16/fp32 medido "
                    "0,80-1,11). Se genera en %s.",
                    pedido,
                    dtype_artefacto,
                    dtype_artefacto,
                )

        # -- 1. Tokenizer (blobs aux.*, ni un byte de VRAM) ------------------ #
        tokenizador = text_conditioning.construir_tokenizer(state_dict)

        # -- 2. Decoder del VAE: 161 MiB que bajan a RAM --------------------- #
        # Se saca primero porque es el componente mas pequeno y liberar VRAM
        # cuanto antes da aire a los pasos siguientes. `cargar_decoder` lee las
        # claves sin sacarlas, asi que se le entrega un sub-diccionario ya
        # extraido, mas la referencia (no copia) al config del VAE.
        pesos_vae = _extraer(state_dict, "vae.decoder.", torch.device("cpu"), 182)
        sub_vae: dict[str, Any] = {f"vae.decoder.{k}": v for k, v in pesos_vae.items()}
        sub_vae["aux.config.vae_json"] = state_dict["aux.config.vae_json"]
        vae = cargar_decoder(sub_vae, device="cpu", dtype=dtype_artefacto)
        del pesos_vae, sub_vae
        residencia_vae = _Residencia("vae.decoder", vae, dispositivo)

        # -- 3. Codificador de texto (Qwen3): 1.136 MiB que bajan a RAM ------ #
        # `construir_text_encoder(consumir=True)` saca las 310 claves del
        # diccionario del llamante y clona a CPU; el clon no es cosmetico: sin el,
        # un tensor que venga de `safe_open` mantiene el fichero mapeado y la
        # primera subida a VRAM lee del disco pagina a pagina (42,91 s medidos
        # frente a 0,43 s).
        text_encoder, _config_qwen, _dtype_qwen = text_conditioning.construir_text_encoder(
            state_dict, consumir=True
        )
        residencia_texto = _Residencia("text_encoder", text_encoder, dispositivo)

        # -- 4. El DiT -------------------------------------------------------- #
        config_json = json.loads(_texto_de_blob(state_dict, CLAVE_CONFIG_ACESTEP))
        # `architectures` y `auto_map` NO se usan jamas para resolver codigo: la
        # clase se referencia de forma explicita (invariante de CLAUDE.md, ningun
        # `trust_remote_code`).
        config_json.pop("architectures", None)
        config_json.pop("auto_map", None)
        # El dtype lo manda el artefacto, no el json heredado (que dice bfloat16,
        # que Pascal no ejecuta).
        config_json["dtype"] = str(dtype_artefacto).removeprefix("torch.")
        from vendor.configuration_acestep_v15 import AceStepConfig  # noqa: PLC0415

        config = AceStepConfig(**config_json)
        modelo = _instanciar_dit(config)

        # 4a. `dit.decoder` -> se queda en VRAM. Los tensores ya estan ahi, asi que
        #     `assign=True` los adopta sin copiar ni un byte.
        pesos = _extraer(state_dict, "dit.decoder.", dispositivo, CLAVES_DIT["decoder"])
        modelo.decoder.load_state_dict(pesos, strict=True, assign=True)
        del pesos
        movidos = _colocar_buffers_no_persistentes(modelo.decoder, dispositivo)
        _LOG.info("dit.decoder cargado en %s (%d buffers de RoPE movidos).", dispositivo, movidos)

        # 4b. `dit.encoder` -> RAM; sube solo mientras se prepara el condicionamiento.
        pesos = _extraer(state_dict, "dit.encoder.", torch.device("cpu"), CLAVES_DIT["encoder"])
        modelo.encoder.load_state_dict(pesos, strict=True, assign=True)
        del pesos
        # Excepcion medida de C1: el codificador de letra desborda fp16 (1,75e5 de
        # pico interno frente a un maximo de 65.504) y saca NaN con cualquier letra
        # de mas de ~40 tokens. Se promueve SOLO ese submodulo, despues de cargar
        # sus pesos y antes de fijar la copia maestra de la residencia, para que
        # la que viva en RAM sea ya la de fp32 y no se convierta en cada
        # generacion. Cuesta 772 MiB mas de RAM y de VRAM temporal; no cuesta
        # tiempo (en sm_61 fp32 va igual que fp16).
        modelo.encoder.lyric_encoder = _CodificadorLetraFp32(
            modelo.encoder.lyric_encoder, dtype_artefacto
        )

        # 4c. `dit.tokenizer` y `dit.detokenizer` -> RAM (200,3 MiB cada uno).
        #     DEJARON de ser peso muerto el 2026-09-02: con el planificador
        #     conectado son justamente la cadena
        #     `quantizer.get_output_from_indices` -> `detokenizer` que convierte
        #     los codigos de 5 Hz en `lm_hints_25Hz`. Suben a VRAM solo durante esa
        #     llamada (ver `PipelineAceStep._planificar`).
        #
        # Y en cuanto se usan aparece un desajuste de dtype que estando sin usar
        # no podia salir. MEDIDO el 2026-09-02: `get_output_from_indices` revienta
        # con `RuntimeError: mat1 and mat2 must have the same dtype, but got Float
        # and Half`.
        #
        # El culpable es `quantizer.scales`, que `vector_quantize_pytorch`
        # construye como `levels_tensor.float() ** -ind`: ese `.float()` es
        # **explicito**, asi que sale fp32 pase lo que pase con el dtype por
        # defecto, mientras que `project_out` es un `Linear` con los pesos fp16 del
        # artefacto. (Los otros bufferes del FSQ si respetan el dtype por defecto y
        # ya salen fp16: `implicit_codebook` y `soft_clamp_input_value`. Tambien
        # estaban en fp32 los `inv_freq` de los dos modulos rotatorios.)
        #
        # Lo que NO hay que tocar: `_levels` y `_basis` son **int32** por
        # construccion. `_basis` llega a valores de ~10^4 y fp16 deja de
        # representar enteros exactos a partir de 2.048, asi que convertirlos
        # corromperia `indices // _basis` EN SILENCIO.
        #
        # `Module.to(dtype)` hace exactamente lo correcto: convierte solo los
        # tensores en coma flotante y deja los enteros donde estan. Es ademas lo
        # que hace upstream, que carga el modelo entero con `dtype=bfloat16`.
        #
        # Y fp16 basta aqui, medido y no supuesto: la cadena completa de hints en
        # fp16 frente a la misma en fp32 da max|diff| = 0,0031 sobre un |max| de
        # 5,77 (0,053 %), correlacion 0,99999946 y cero valores no finitos. No es
        # el caso del codificador de letra.
        for nombre in ("tokenizer", "detokenizer"):
            pesos = _extraer(state_dict, f"dit.{nombre}.", torch.device("cpu"), CLAVES_DIT[nombre])
            submodulo = getattr(modelo, nombre)
            submodulo.load_state_dict(pesos, strict=True, assign=True)
            del pesos
            submodulo.to(dtype_artefacto)
            enteros = {
                n: t.dtype
                for n, t in submodulo.named_buffers()
                if not t.is_floating_point()
            }
            desalineados = [
                n
                for n, t in (*submodulo.named_parameters(), *submodulo.named_buffers())
                if t.is_floating_point() and t.dtype is not dtype_artefacto
            ]
            if desalineados:
                raise RuntimeError(
                    f"dit.{nombre}: quedan tensores en coma flotante fuera de "
                    f"{dtype_artefacto}: {desalineados[:5]}. La cadena de hints mezclaria "
                    "dtypes y fallaria dentro del cuantizador."
                )
            _LOG.debug("dit.%s alineado a %s; bufferes enteros intactos: %s",
                       nombre, dtype_artefacto, enteros)

        # 4d. `null_condition_emb`: un solo tensor, a VRAM con el decoder.
        nulo = _extraer(state_dict, CLAVE_NULL_CONDITION, dispositivo, 1)
        if set(nulo) != {""}:
            raise RuntimeError(f"Se esperaba una unica clave {CLAVE_NULL_CONDITION!r}.")
        modelo.null_condition_emb = torch.nn.Parameter(nulo[""], requires_grad=False)
        del nulo

        modelo.eval()
        modelo.requires_grad_(False)
        en_meta = [
            nombre
            for nombre, tensor in (*modelo.named_parameters(), *modelo.named_buffers())
            if tensor.is_meta
        ]
        if en_meta:
            raise RuntimeError(
                f"Quedan {len(en_meta)} tensores del DiT en el dispositivo 'meta' "
                f"(por ejemplo {en_meta[:5]}). Usarlos daria un fallo tardio y confuso "
                "dentro del forward, o audio silenciosamente incorrecto."
            )
        _forzar_atencion_eager(modelo, config)
        residencia_encoder = _Residencia("dit.encoder", modelo.encoder, dispositivo)
        residencia_audio_tok = _Residencia("dit.tokenizer", modelo.tokenizer, dispositivo)
        residencia_detok = _Residencia("dit.detokenizer", modelo.detokenizer, dispositivo)

        # -- 4e. El planificador de 5 Hz (opcional) -------------------------- #
        # Solo si el artefacto lo trae. Un artefacto sin `lm.*` sigue siendo
        # valido: da el pipeline de siempre y `usar_lm=True` falla con un mensaje
        # que dice como reconstruirlo, en vez de degradar en silencio.
        planificador = None
        if any(clave.startswith(PREFIJO_LM) for clave in state_dict):
            planificador, dir_tokenizer_lm = _construir_planificador(state_dict, dispositivo)
        else:
            _LOG.warning(
                "El artefacto NO trae el planificador de 5 Hz (prefijo %r). `src_latents` "
                "seguira siendo el latente de silencio, que es lo que upstream llama "
                "componer a ciegas. Reconstruye con `build_artifact.py --incluir-lm` para "
                "poder hacer el A/B.",
                PREFIJO_LM,
            )

        # -- 5. Latente de silencio y limpieza del resto de aux.* ------------ #
        silence_latent = state_dict.pop(CLAVE_SILENCE_LATENT, None)
        if silence_latent is None:
            raise RuntimeError(
                f"El artefacto no trae {CLAVE_SILENCE_LATENT!r}. En text2music el latente "
                "objetivo ES un recorte del latente de silencio: sin el no hay generacion "
                "posible (y el codificador del VAE no viaja en el artefacto a proposito)."
            )
        silence_latent = silence_latent.to(device=dispositivo, dtype=dtype_artefacto)

        sobrantes = sorted(state_dict)
        for clave in sobrantes:
            state_dict.pop(clave)
        inesperadas = [c for c in sobrantes if not c.startswith("aux.")]
        if inesperadas:
            raise RuntimeError(
                f"El artefacto trae claves que este shim no sabe colocar: {inesperadas[:10]}. "
                "El contrato son los prefijos dit./text_encoder./vae./aux."
            )
        if sobrantes:
            _LOG.debug("Blobs aux.* no usados y descartados: %s", sobrantes)
        if dispositivo.type == "cuda":
            torch.cuda.empty_cache()

        pipeline = PipelineAceStep(
            modelo=modelo,
            residencia_dit_encoder=residencia_encoder,
            residencia_text_encoder=residencia_texto,
            residencia_vae=residencia_vae,
            tokenizador=_TokenizadorParaPipeline(tokenizador),
            silence_latent=silence_latent,
            dispositivo=dispositivo,
            dtype=dtype_artefacto,
            offload=bool(offload),
            planificador=planificador,
            residencia_audio_tokenizer=residencia_audio_tok,
            residencia_detokenizer=residencia_detok,
            dir_tokenizer_lm=dir_tokenizer_lm,
        )
    except BaseException:
        # M-5 del adapter: un fallo aqui no puede dejar pesos huerfanos en VRAM.
        # El adapter llamara ademas a release() si el objeto llego a existir, pero
        # si el fallo ocurre a mitad de construccion no hay objeto que liberar.
        for residencia in (
            residencia_vae,
            residencia_texto,
            residencia_encoder,
            residencia_audio_tok,
            residencia_detok,
        ):
            if residencia is not None:
                try:
                    residencia.soltar()
                except Exception:  # noqa: BLE001, S110
                    pass
        if dir_tokenizer_lm is not None:
            shutil.rmtree(dir_tokenizer_lm, ignore_errors=True)
        state_dict.clear()
        if dispositivo.type == "cuda":
            torch.cuda.empty_cache()
        raise

    if dispositivo.type == "cuda":
        libre, total = torch.cuda.mem_get_info(dispositivo)
        _LOG.info(
            "Pipeline listo en %.2f s. Residente en VRAM: dit.decoder (%.0f MiB). "
            "En RAM: dit.encoder %.0f MiB, text_encoder %.0f MiB, vae.decoder %.0f MiB. "
            "VRAM libre: %.0f MiB de %.0f MiB.",
            time.perf_counter() - inicio,
            torch.cuda.memory_allocated(dispositivo) / _MIB,
            residencia_encoder.bytes_pesos / _MIB,
            residencia_texto.bytes_pesos / _MIB,
            residencia_vae.bytes_pesos / _MIB,
            libre / _MIB,
            total / _MIB,
        )
    return pipeline
