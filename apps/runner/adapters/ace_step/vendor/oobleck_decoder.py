# Copyright 2025 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION  (Apache License 2.0, seccion 4(b))
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original de HuggingFace.
#
# Obra derivada de `diffusers`, fichero
# `src/diffusers/models/autoencoders/autoencoder_oobleck.py`.
#
#   Origen          : https://github.com/huggingface/diffusers
#   Revision fijada : tag v0.34.0 -> commit 50dea89dc6036e71a00bc3d57ac062a80206d9eb
#                     (objeto de tag anotado a74996a0986d28c02b67f4c08795bc39900968a9)
#   SHA-256 origen  : 1d5df4ff4d1edb5fa6b6cf89753f4af50facf147ab93f70c0fdfce5fdb9a36d5
#   blob SHA-1 git  : a10b616b4e25444c5998b81cc0d137e7dfdd5fd0  (17.085 bytes)
#                     verificado contra la atestacion de la API de GitHub para esa
#                     ruta en ese commit.
#   Copiado el      : 2026-09-01
#   Licencia        : Apache-2.0 (uso comercial permitido). El aviso de copyright
#                     original se conserva integro arriba, sin alterar.
#   Procedencia verificada el 2026-09-02 contra la API de GitHub: el tag v0.34.0
#   es un tag ANOTADO (objeto a74996a0986d28c02b67f4c08795bc39900968a9) que
#   apunta al commit 50dea89dc6036e71a00bc3d57ac062a80206d9eb; la ruta declarada
#   en ese ref devuelve 17.085 bytes, blob SHA-1 a10b616b..., y el contenido
#   descargado tiene el SHA-256 1d5df4ff... anotado arriba. Los tres coinciden.
#
# La version de diffusers no es una eleccion nuestra: el config del VAE que viaja
# en el artefacto declara `"_diffusers_version": "0.34.0"`, asi que se fija esa.
#
# Cambios introducidos por Daycry (plataforma musical IA), 2026-09-01
# -------------------------------------------------------------------
#  1. SUPRIMIDO todo lo que no hace falta para decodificar: `OobleckEncoder`,
#     `OobleckEncoderBlock`, `OobleckDiagonalGaussianDistribution`,
#     `AutoencoderOobleck`, `AutoencoderOobleckOutput`, `OobleckDecoderOutput` y
#     las dependencias de `diffusers` (`ModelMixin`, `ConfigMixin`,
#     `register_to_config`, `BaseOutput`, `apply_forward_hook`, `randn_tensor`) y
#     de `numpy`. El artefacto de pesos NO incluye el encoder del VAE, y el
#     objetivo es no arrastrar `diffusers` entero a la imagen del runner por una
#     clase. Este fichero solo depende de `torch`.
#  2. `Snake1d.forward`: exponencial y reciproco en fp32 sobre parametros fp16
#     (en fp16 el `1e-9` de la formula original ES cero). Eliminado ademas el par
#     `reshape` de ida y vuelta, que para una entrada 3-D es la identidad.
#  3. `OobleckDecoder.forward`: la conv1d FINAL (128 -> 2 canales) se ejecuta
#     SIEMPRE en fp32 con `F.conv1d`, por medicion (ver seccion "fp32 final").
#  4. ANADIDO `OobleckDecoder.decodificar_por_trozos()`: decode por ventanas con
#     solape, guarda y crossfade lineal. Es requisito duro: el decode monolitico
#     de 180 s no cabe en 8 GB.
#  5. ANADIDAS las utilidades de carga (`leer_config_vae`, `construir_decoder`,
#     `cargar_decoder`, `planificar_trozos`), la fusion de weight norm en fp32 y
#     el guardarrail de VRAM.
#  6. Comentarios y nombres de lo anadido en castellano (convencion del repo).
#
# Los nombres de atributo de los modulos (`block`, `conv1`, `conv2`, `conv_t1`,
# `snake1`, `snake2`, `res_unit1..3`, `alpha`, `beta`) NO se tocan: son los que
# fijan las claves del `state_dict` y permiten `load_state_dict(strict=True)`.
# ---------------------------------------------------------------------------
"""Decoder del VAE Oobleck de ACE-Step 1.5, vendorizado y con decode por trozos.

Por que existe este fichero
---------------------------
`diffusers` no esta en la imagen del runner (`ace-step-runner:t05`) y no se
quiere anadir por una sola clase. `CLAUDE.md` ademas prohibe `trust_remote_code`,
asi que el codigo de terceros se vendoriza fijado por hash y revisable en un
diff.

Que carga
---------
Las **182 claves** con prefijo `vae.decoder.` del artefacto
`ace_step_1_5.safetensors`, quitando el prefijo, con
`load_state_dict(..., strict=True)` y **sin remapeo de nombres**. La
configuracion sale del tensor `aux.config.vae_json` del propio artefacto::

    {"_class_name": "AutoencoderOobleck", "_diffusers_version": "0.34.0",
     "audio_channels": 2, "channel_multiples": [1, 2, 4, 8, 16],
     "decoder_channels": 128, "decoder_input_channels": 64,
     "downsampling_ratios": [2, 4, 4, 6, 10], "encoder_hidden_size": 128,
     "sampling_rate": 48000}

De ahi salen los numeros que gobiernan todo lo demas:

* `hop_length = prod(downsampling_ratios) = 1920` muestras por trama latente.
* `sampling_rate = 48000` Hz, es decir **25 tramas latentes por segundo**.
* 180 s de audio = **4500 tramas latentes** = 8.640.000 muestras estereo.

El encoder del VAE **no esta** en el artefacto, y para text2music no hace falta.

DECODE POR TROZOS: ventana, solape y guarda
-------------------------------------------
El decode monolitico de 180 s **no cabe** en los 8 GB de la GTX 1070 (techo
medido: 40-46 s). La causa es la piramide de activaciones: cada trama latente se
convierte en 1920 muestras y el ultimo bloque trabaja con 128 canales sobre esa
longitud completa, asi que el pico crece de forma estrictamente lineal con la
duracion. Medido en esta maquina, con linealidad practicamente perfecta entre
W = 128 y W = 512 (4,926 / 4,924 / 4,923 MiB por trama, ya descontados los
161 MiB de pesos): **4,92 MiB = 5,17 MB de activaciones por trama latente**, o
sea ~129 MB por segundo de audio. Los 180 s de una sola vez pedirian **23,1 GiB**.

La red es una CNN 1-D **no causal** con relleno simetrico. Eso tiene una
consecuencia util: lejos de los bordes reales de la senal, una muestra de salida
depende **solo** de una vecindad finita del latente. Ese campo receptivo se ha
medido perturbando una unica trama latente y viendo hasta donde se mueve la
salida: el soporte no nulo se derrama **16.003 muestras** a cada lado de la trama
tocada, o sea **radio 8,34 tramas latentes (0,333 s)**; en numero entero de
tramas, la perturbacion de la trama 48 toca exactamente las tramas [39, 57],
**radio 9**. Fuera de ahi la diferencia es cero exacto, no "pequena": el soporte
es finito de verdad. Se comprobo con dos amplitudes de perturbacion (delta 3,0 y
0,3) y da el mismo radio, asi que no es un artefacto del tamano del empujon. Es
pequeno porque las dilataciones grandes viven en los bloques de mayor tasa de
muestreo, donde una trama latente ya se ha estirado x1920.

Esa medicion hay que hacerla **en CPU y en fp32**, no en la GPU: en GPU cuDNN
elige algoritmos de convolucion que mezclan globalmente (FFT / Winograd), y una
perturbacion local aparece diluida por TODA la salida con magnitud ~6e-4 del
pico. Medido en GPU y con umbral estricto, el campo receptivo "sale" infinito;
es un suelo de ruido numerico, no una dependencia real.

De ahi el esquema, con tres numeros y no dos::

    ventana   W = 256 tramas = 10,24 s de audio
    solape    S =  48 tramas =  1,92 s
    guarda    G =  16 tramas =  0,64 s por lado, se DESCARTA
    paso      P = W - S = 208 tramas = 8,32 s
    crossfade C = S - 2G = 16 tramas = 0,64 s = 30.720 muestras

* **W = 256** porque el tiempo de decode es casi plano con W y la VRAM no.
  Medido sobre los 4500 latentes de 180 s (S = 32, G = 8 para aislar el efecto
  de W): W = 512 tarda 15,98 s con 2682 MiB de pico, W = 256 tarda 17,26 s con
  1422 MiB y W = 128 tarda 18,76 s con 792 MiB. Duplicar el pico de VRAM para
  ahorrar 1,3 s de 17 es mal negocio en una tarjeta de 8 GB donde el DiT tiene
  que seguir residente; y bajar mas multiplica las costuras sin ganar tiempo.
* **G = 16** porque las primeras y ultimas G tramas de cada ventana estan
  contaminadas por el relleno con CEROS del borde de la ventana, que en mitad de
  la cancion es una mentira (ahi la senal continua). G = 16 da 1,9x sobre el
  radio medido de 8,34 tramas. Esas muestras **no se mezclan: se tiran**.
  Medido contra el decode monolitico (W = 256, S = 48, 600 tramas): con G = 0 el
  error medio en las costuras es 3,00e-4 frente a 2,34e-4 de fondo (**1,28x**, la
  costura se nota); con G = 4, 8 y 16 el ratio baja a **0,93x**, es decir que en
  las costuras el error es incluso algo MENOR que en el resto, porque el
  crossfade promedia dos resultados con ruido de convolucion independiente. A
  partir de G = 4 la costura ya no se distingue; G = 16 deja margen de sobra.
* **S > 2G** es la condicion dura para que no quede hueco entre ventanas
  consecutivas despues de descartar las guardas. S = 48 deja C = 16 tramas de
  solapamiento LIMPIO donde hacer el crossfade, y cuesta un 25 % de computo
  extra sobre los 4500 latentes (22 ventanas de 256 para 4500 tramas).

Crossfade **LINEAL**, no de potencia constante, y es deliberado: como el solape
util queda por completo fuera del campo receptivo, las dos ramas del solape son
**la misma senal** (identicas salvo ruido de coma flotante). Para senales
correlacionadas la rampa lineal suma exactamente 1 y conserva la amplitud,
mientras que una rampa de potencia constante (sen/cos) sumaria ~sqrt(2) y metria
un bulto de +3 dB en **cada** costura. La discontinuidad audible que se quiere
evitar aparece por sumar mal, no por sumar poco.

La ULTIMA ventana se **fija** a `T - W` en lugar de encogerse. Cuesta
redecodificar un trozo ya hecho, pero mantiene la forma del tensor constante en
todas las llamadas: cuDNN autotunea una sola vez y el pico de VRAM es identico en
todas las iteraciones, que es justo lo que se quiere cuando se esta pegado al
techo. El crossfade de esa ultima costura sale mas largo; con rampa lineal sobre
la misma senal eso es inofensivo.

Verificacion de las costuras y coste (medido, no razonado)
----------------------------------------------------------
Todas las cifras de esta seccion son de la GTX 1070 (sm_61, 8192 MiB) dentro de
`ace-step-runner:t05` (torch 2.13.0+cu126), con las 182 claves reales del
artefacto, verificadas el 2026-09-02 en tres ejecuciones independientes.

Decodificando por trozos el latente REAL de silencio del artefacto
(`aux.silence_latent[:, :, :4500]`, 180 s), el salto muestra a muestra
`|x[n+1] - x[n]|` en las 21 costuras llega a 1,45-1,48e-4 frente a un maximo
global de 7,05-7,30e-4: en las costuras el salto es **0,20-0,21 veces** el mayor
salto natural de la senal, asi que no hay escalon que oir. Sobre un latente
aleatorio de 600 tramas —la mayor duracion que permite comparar contra el
monolitico sin salirse de los 8 GB— la diferencia entre decodificar por trozos y
hacerlo de una vez es de **2,30e-4 de media** (maximo 9,3e-3 a 1,6e-2) con una
senal de rms 0,2300, o sea **-60,0 dB**; y dentro de las costuras esa diferencia
es 2,05-2,08e-4, algo MENOR que la global. Ese residuo NO viene de las costuras,
sino de que cuDNN elige distinto algoritmo de convolucion segun la forma del
tensor: es del mismo orden dentro y fuera, y por eso el maximo puntual varia
tanto de una ejecucion a otra sin que las costuras se muevan.

Con los valores por defecto, 4500 tramas latentes (180 s) se decodifican en 22
ventanas, en **18,6-19,1 s** (0,104-0,106 s de computo por segundo de audio,
9,4-9,6x el tiempo real), con **1425 MiB de pico de VRAM asignada** (161 MiB de
pesos + ~1264 MiB de activaciones) y 1552 MiB reservados. Salida
`(1, 2, 8.640.000)` en fp32, finita, con 0 NaN y 0 inf, y con el numero de
muestras exacto (4500 x 1920).

fp16: donde si y donde no
-------------------------
El artefacto es todo fp16 y **no se hace upcast**: en esta Pascal (sm_61) fp16 no
cae por el camino lento porque cuBLAS promociona a fp32 internamente, y el ratio
fp16/fp32 medido es 0,80-1,11. Duplicar memoria de pesos y activaciones para no
ganar nada seria absurdo.

Dos excepciones, ambas por numerica y no por velocidad:

* `Snake1d` calcula `exp(alpha)`, `exp(beta)` y `(beta + 1e-9).reciprocal()` en
  fp32. En fp16 el `1e-9` de la formula original **es cero** (el menor subnormal
  fp16 vale ~6e-8), con lo que el guardarrail contra la division por cero
  desaparece; y `exp()` en fp16 satura a inf para alpha > 11,1. Son tensores
  `(1, C, 1)`: hacerlo en fp32 no cuesta nada medible.
* El peso efectivo de weight norm se calcula en fp32 antes de bajarlo a fp16
  (`fusionar_weight_norm`): la norma L2 de un vector de hasta 20.480 elementos
  acumulada en fp16 pierde precision para nada.

fp32 en la conv1d FINAL (medido)
--------------------------------
La ultima conv (128 -> 2 canales, kernel 7) se ejecuta **siempre en fp32**, y no
por precision sino por velocidad. Medida en esta GPU sobre 720.000 muestras, con
los pesos reales del artefacto y promedio de 10 pasadas, en dos ejecuciones
distintas: **fp16 28,4-33,8 ms frente a fp32 9,0-9,7 ms**, o sea fp16 es
**3,06-3,74x MAS LENTA**. Notese que la dispersion esta toda en fp16 (28,4 /
29,5 / 33,8 ms en tres ejecuciones) mientras que fp32 es estable (9,0 / 9,0 /
9,7 ms): el mal kernel ademas es irregular. Reproduce la medicion previa del
proyecto (28,5 frente a 9,5 ms, 3x). cuDNN no encuentra un kernel decente con
solo 2 canales de salida
y cae a una implementacion mala, mientras que en fp32 usa un kernel razonable. Es
la unica capa del decoder donde esto pasa, porque es la unica con un numero de
canales de salida ridiculo.

Ahorra ~20 ms por ventana; sobre las 22 ventanas de una pista de 180 s son ~0,43 s
de los ~19 s totales.

Como efecto colateral util, la salida ya sale en fp32, que es lo que quiere el
post-proceso de audio.

Uso
---
::

    from oobleck_decoder import cargar_decoder

    decoder = cargar_decoder(state_dict, device="cuda:0", dtype=torch.float16)
    audio = decoder.decodificar_por_trozos(latente)  # (B, 2, T*1920) fp32 en CPU

`state_dict` es el diccionario completo del artefacto tal cual lo entrega el
adapter (`safetensors.torch.load_file`): esta funcion se queda con las claves
`vae.decoder.*` y lee la config de `aux.config.vae_json`.
"""

from __future__ import annotations

import json
import math
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

# `torch.nn.utils.weight_norm` (parametrizacion antigua, claves `weight_g` y
# `weight_v`) esta deprecada en favor de `torch.nn.utils.parametrizations.
# weight_norm`, que usa las claves `parametrizations.weight.original0/original1`.
# Aqui NO se puede migrar: el checkpoint se guardo con la parametrizacion antigua
# y las claves tienen que coincidir exactamente para que `strict=True` pase. Se
# usa la deprecada a proposito y se silencia su FutureWarning al construir.
from torch.nn.utils import remove_weight_norm, weight_norm

__all__ = [
    "BYTES_COLCHON_VRAM",
    "BYTES_PICO_POR_TRAMA",
    "CLAVES_ESPERADAS",
    "CLAVE_CONFIG_VAE",
    "GUARDA_LATENTE_POR_DEFECTO",
    "PREFIJO_ESTADO",
    "SOLAPE_LATENTE_POR_DEFECTO",
    "VENTANA_LATENTE_POR_DEFECTO",
    "ErrorDecoderVae",
    "OobleckDecoder",
    "OobleckDecoderBlock",
    "OobleckResidualUnit",
    "PlanDeTrozos",
    "Snake1d",
    "VramInsuficiente",
    "cargar_decoder",
    "construir_decoder",
    "leer_config_vae",
    "planificar_trozos",
]

# --------------------------------------------------------------------------- #
# Contrato con el artefacto
# --------------------------------------------------------------------------- #

#: Prefijo de las 182 claves del decoder dentro del `state_dict` del artefacto.
PREFIJO_ESTADO = "vae.decoder."

#: Tensor U8 del artefacto que contiene el `config.json` del VAE.
CLAVE_CONFIG_VAE = "aux.config.vae_json"

#: Numero exacto de claves que debe aportar el artefacto. Se comprueba al cargar:
#: si el artefacto cambia, se quiere un fallo ruidoso, no un modelo a medias.
CLAVES_ESPERADAS = 182

# --------------------------------------------------------------------------- #
# Parametros del decode por trozos (justificados en el docstring del modulo)
# --------------------------------------------------------------------------- #

VENTANA_LATENTE_POR_DEFECTO = 256  # 10,24 s de audio a 25 tramas/s
SOLAPE_LATENTE_POR_DEFECTO = 48  # 1,92 s
GUARDA_LATENTE_POR_DEFECTO = 16  # 0,64 s por lado, descartadas

#: Pico de VRAM por trama latente y elemento de lote. MEDIDO en la GTX 1070 con
#: los pesos fp16 reales, descontados los 161 MiB de parametros: 4,92 MiB/trama
#: (5,17 MB) de pico del ASIGNADOR, con linealidad practicamente perfecta entre
#: W = 128 y W = 512, y 5,43 MiB/trama (5,70 MB) si se cuenta la memoria
#: RESERVADA (fragmentacion incluida). Se fija en 5,5 MB y la diferencia contra
#: lo reservado la absorbe `BYTES_COLCHON_VRAM`: para W = 256 el guardarrail
#: exige 1726 MiB frente a los 1552 MiB reservados de verdad, o sea que es
#: conservador, que es como tiene que ser. Solo se usa para abortar ANTES de
#: asignar, nunca para reservar: un OOM de driver deja el asignador cacheante de
#: PyTorch corrupto y no se puede capturar y continuar.
BYTES_PICO_POR_TRAMA = 5_500_000

#: Colchon fijo sobre la estimacion anterior: fragmentacion del asignador,
#: workspace de cuDNN y contexto de CUDA.
BYTES_COLCHON_VRAM = 384 * 1024 * 1024


class ErrorDecoderVae(RuntimeError):
    """Fallo al construir, cargar o ejecutar el decoder del VAE."""


class VramInsuficiente(ErrorDecoderVae):
    """No hay VRAM libre para decodificar la ventana pedida.

    Se levanta **antes** de intentar la asignacion. Deliberadamente no se captura
    ningun `torch.cuda.OutOfMemoryError` para reintentar: cuando el driver
    devuelve OOM, el asignador cacheante de PyTorch queda en un estado del que no
    se recupera dentro del mismo proceso.
    """


# --------------------------------------------------------------------------- #
# Bloques del modelo (obra derivada de diffusers, ver nota de modificacion)
# --------------------------------------------------------------------------- #


def _conv_norm(conv: nn.Module) -> nn.Module:
    """Aplica la weight norm ANTIGUA (claves `weight_g` / `weight_v`).

    La parametrizacion nueva generaria claves distintas y romperia el
    `strict=True` contra el checkpoint. Se silencia el FutureWarning porque es
    una decision consciente, no un descuido.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        return weight_norm(conv)


class Snake1d(nn.Module):
    """Activacion Snake 1-D.

    MODIFICADO respecto de diffusers: `exp()` y `reciprocal()` en fp32 (el `1e-9`
    original es cero en fp16), y sin el par `reshape` de ida y vuelta, que para
    una entrada 3-D es la identidad.
    """

    def __init__(self, hidden_dim: int, logscale: bool = True) -> None:
        super().__init__()
        self.alpha = nn.Parameter(torch.zeros(1, hidden_dim, 1))
        self.beta = nn.Parameter(torch.zeros(1, hidden_dim, 1))
        self.logscale = logscale

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        alpha = self.alpha.float()
        beta = self.beta.float()
        if self.logscale:
            alpha = torch.exp(alpha)
            beta = torch.exp(beta)

        dtype = hidden_states.dtype
        alpha = alpha.to(dtype)
        inv_beta = (beta + 1e-9).reciprocal().to(dtype)

        return hidden_states + inv_beta * torch.sin(alpha * hidden_states).pow(2)


class OobleckResidualUnit(nn.Module):
    """Unidad residual: Snake1d + conv1d con weight norm y dilatacion.

    Identica a la de diffusers salvo el silenciado del FutureWarning.
    """

    def __init__(self, dimension: int = 16, dilation: int = 1) -> None:
        super().__init__()
        pad = ((7 - 1) * dilation) // 2

        self.snake1 = Snake1d(dimension)
        self.conv1 = _conv_norm(
            nn.Conv1d(dimension, dimension, kernel_size=7, dilation=dilation, padding=pad)
        )
        self.snake2 = Snake1d(dimension)
        self.conv2 = _conv_norm(nn.Conv1d(dimension, dimension, kernel_size=1))

    def forward(self, hidden_state: torch.Tensor) -> torch.Tensor:
        output_tensor = hidden_state
        output_tensor = self.conv1(self.snake1(output_tensor))
        output_tensor = self.conv2(self.snake2(output_tensor))

        padding = (hidden_state.shape[-1] - output_tensor.shape[-1]) // 2
        if padding > 0:
            hidden_state = hidden_state[..., padding:-padding]
        return hidden_state + output_tensor


class OobleckDecoderBlock(nn.Module):
    """Bloque de sobremuestreo del decoder. Identico al de diffusers."""

    def __init__(self, input_dim: int, output_dim: int, stride: int = 1) -> None:
        super().__init__()

        self.snake1 = Snake1d(input_dim)
        self.conv_t1 = _conv_norm(
            nn.ConvTranspose1d(
                input_dim,
                output_dim,
                kernel_size=2 * stride,
                stride=stride,
                padding=math.ceil(stride / 2),
            )
        )
        self.res_unit1 = OobleckResidualUnit(output_dim, dilation=1)
        self.res_unit2 = OobleckResidualUnit(output_dim, dilation=3)
        self.res_unit3 = OobleckResidualUnit(output_dim, dilation=9)

    def forward(self, hidden_state: torch.Tensor) -> torch.Tensor:
        hidden_state = self.snake1(hidden_state)
        hidden_state = self.conv_t1(hidden_state)
        hidden_state = self.res_unit1(hidden_state)
        hidden_state = self.res_unit2(hidden_state)
        hidden_state = self.res_unit3(hidden_state)
        return hidden_state


class OobleckDecoder(nn.Module):
    """Decoder Oobleck (Stable Audio / ACE-Step 1.5).

    Anadidos respecto de diffusers: `hop_length` y `sampling_rate` como
    atributos, la conv final en fp32, `fusionar_weight_norm()` y
    `decodificar_por_trozos()`.
    """

    def __init__(
        self,
        channels: int,
        input_channels: int,
        audio_channels: int,
        upsampling_ratios: Sequence[int],
        channel_multiples: Sequence[int],
        sampling_rate: int = 48000,
    ) -> None:
        super().__init__()

        strides = list(upsampling_ratios)
        channel_multiples = [1] + list(channel_multiples)

        self.conv1 = _conv_norm(
            nn.Conv1d(input_channels, channels * channel_multiples[-1], kernel_size=7, padding=3)
        )

        block = []
        for stride_index, stride in enumerate(strides):
            block += [
                OobleckDecoderBlock(
                    input_dim=channels * channel_multiples[len(strides) - stride_index],
                    output_dim=channels * channel_multiples[len(strides) - stride_index - 1],
                    stride=stride,
                )
            ]

        self.block = nn.ModuleList(block)
        output_dim = channels
        self.snake1 = Snake1d(output_dim)
        self.conv2 = _conv_norm(
            nn.Conv1d(channels, audio_channels, kernel_size=7, padding=3, bias=False)
        )

        # --- anadidos nuestros: escalares, no parametros; no tocan el state_dict
        self.input_channels = int(input_channels)
        self.audio_channels = int(audio_channels)
        self.sampling_rate = int(sampling_rate)
        #: Muestras de audio por trama latente. En ACE-Step 1.5: 1920.
        self.hop_length = int(math.prod(strides))
        self._weight_norm_fusionada = False

    # ------------------------------------------------------------------ #
    # Forward monolitico (upstream + conv final en fp32)
    # ------------------------------------------------------------------ #

    def _peso_conv2_fp32(self) -> torch.Tensor:
        """Peso efectivo de la conv final, en fp32.

        Funciona tanto antes como despues de fusionar la weight norm, para que el
        `forward` no dependa del orden de inicializacion. Son 2*128*7 = 1792
        elementos: calcularlo en cada llamada no se mide.
        """
        conv = self.conv2
        if hasattr(conv, "weight_g"):
            g = conv.weight_g.float()
            v = conv.weight_v.float()
            norma = v.norm(dim=tuple(range(1, v.dim())), keepdim=True)
            return g * v / norma
        return conv.weight.float()

    def forward(self, hidden_state: torch.Tensor) -> torch.Tensor:
        hidden_state = self.conv1(hidden_state)

        for layer in self.block:
            hidden_state = layer(hidden_state)

        hidden_state = self.snake1(hidden_state)

        # MODIFICADO: la conv final va en fp32 a proposito. Medido en la GTX 1070
        # sobre 720.000 muestras: fp16 28,4-29,5 ms frente a fp32 9,0-9,7 ms
        # (3,1x mas lenta en fp16), porque cuDNN no tiene kernel decente con solo
        # 2 canales de salida. Ademas la salida ya sale en fp32, que es lo que
        # quiere el post-proceso de audio.
        return F.conv1d(
            hidden_state.float(),
            self._peso_conv2_fp32(),
            bias=None,
            stride=1,
            padding=self.conv2.padding[0],
        )

    # ------------------------------------------------------------------ #
    # Fusion de la weight norm
    # ------------------------------------------------------------------ #

    def fusionar_weight_norm(self) -> OobleckDecoder:
        """Colapsa `weight_g` / `weight_v` en un unico `weight`.

        Debe llamarse **despues** de `load_state_dict(strict=True)`: al fusionar
        cambian los nombres de los parametros, y un `load_state_dict` posterior
        con las claves del artefacto fallaria.

        El producto `g * v / ||v||` se calcula en fp32 y se baja a fp16 despues.
        Ahorra ademas recalcular la norma de los 84.395.776 parametros (161 MiB en
        fp16) en cada una de las 22 ventanas de una pista de 180 s.
        """
        if self._weight_norm_fusionada:
            return self

        with torch.no_grad():
            for modulo in self.modules():
                if not hasattr(modulo, "weight_g"):
                    continue
                dtype_original = modulo.weight_g.dtype
                modulo.weight_g.data = modulo.weight_g.data.float()
                modulo.weight_v.data = modulo.weight_v.data.float()
                remove_weight_norm(modulo)
                modulo.weight.data = modulo.weight.data.to(dtype_original)

        self._weight_norm_fusionada = True
        return self

    # ------------------------------------------------------------------ #
    # Decode por trozos
    # ------------------------------------------------------------------ #

    @torch.no_grad()
    def decodificar_por_trozos(
        self,
        latente: torch.Tensor,
        *,
        ventana: int = VENTANA_LATENTE_POR_DEFECTO,
        solape: int = SOLAPE_LATENTE_POR_DEFECTO,
        guarda: int = GUARDA_LATENTE_POR_DEFECTO,
        salida_dispositivo: str | torch.device = "cpu",
        al_avanzar: Callable[[int, int], None] | None = None,
    ) -> torch.Tensor:
        """Decodifica un latente largo por ventanas solapadas con crossfade.

        Args:
            latente: `(B, decoder_input_channels, T)`, con T tramas latentes.
            ventana: tramas latentes por ventana (W).
            solape: tramas latentes compartidas entre ventanas consecutivas (S).
            guarda: tramas latentes descartadas en cada borde interior (G).
            salida_dispositivo: donde se acumula el audio. Por defecto `"cpu"`,
                para no gastar VRAM en el buffer de salida (180 s estereo en fp32
                son 69 MiB).
            al_avanzar: callback `(ventana_hecha, total_ventanas)` que se invoca
                al terminar cada ventana. Sirve para que quien llama vigile el
                presupuesto de GPU; si levanta una excepcion, se deja propagar.

        Returns:
            `(B, audio_channels, T * hop_length)` en fp32.

        Raises:
            ErrorDecoderVae: parametros incoherentes o entrada mal formada.
            VramInsuficiente: no hay VRAM libre suficiente para una ventana.
        """
        if latente.dim() != 3:
            raise ErrorDecoderVae(
                f"El latente debe ser (B, C, T); recibido {tuple(latente.shape)}."
            )

        lote, canales, tramas = latente.shape
        if canales != self.input_channels:
            raise ErrorDecoderVae(
                f"El latente tiene {canales} canales y el decoder espera "
                f"{self.input_channels}."
            )
        if tramas < 1:
            raise ErrorDecoderVae("El latente no tiene ni una trama.")

        plan = planificar_trozos(tramas, ventana=ventana, solape=solape, guarda=guarda)

        # Una sola comprobacion, ANTES del bucle: todas las ventanas tienen la
        # misma forma, y a partir de la segunda la memoria ya viene del cache del
        # asignador (comprobarlo por iteracion daria falsos positivos, porque el
        # cache de PyTorch cuenta como ocupado a ojos del driver).
        self._comprobar_vram(latente.device, lote, plan.ventana)

        salto = self.hop_length
        salida = torch.zeros(
            (lote, self.audio_channels, tramas * salto),
            dtype=torch.float32,
            device=torch.device(salida_dispositivo),
        )

        fin_escrito = 0  # primera muestra global todavia sin escribir
        total = len(plan.inicios)

        for indice, inicio in enumerate(plan.inicios):
            fin = inicio + plan.ventana
            trozo = latente[:, :, inicio:fin].contiguous()
            audio = self(trozo).to(salida.device)

            # Recorte de guardas, solo en los bordes que NO son el borde real de
            # la cancion: ahi el relleno con ceros del modelo es el
            # comportamiento correcto y hay que conservarlo.
            recorte_izq = 0 if inicio == 0 else plan.guarda
            recorte_der = 0 if fin >= tramas else plan.guarda

            ini_valido = (inicio + recorte_izq) * salto
            fin_valido = (fin - recorte_der) * salto
            audio = audio[:, :, recorte_izq * salto : audio.shape[-1] - recorte_der * salto]

            if ini_valido >= fin_escrito:
                # Sin solapamiento util: solo ocurre en la primera ventana.
                salida[:, :, ini_valido:fin_valido] = audio
            else:
                largo_mezcla = fin_escrito - ini_valido
                # Crossfade LINEAL: en el solape util las dos ramas son la misma
                # senal (el solape supera el campo receptivo), y la rampa lineal
                # es la unica que conserva la amplitud al sumar senales iguales.
                # Una de potencia constante metria +3 dB en cada costura.
                rampa = torch.linspace(
                    0.0, 1.0, largo_mezcla + 2, dtype=torch.float32, device=salida.device
                )[1:-1]
                salida[:, :, ini_valido:fin_escrito] = (
                    salida[:, :, ini_valido:fin_escrito] * (1.0 - rampa)
                    + audio[:, :, :largo_mezcla] * rampa
                )
                salida[:, :, fin_escrito:fin_valido] = audio[:, :, largo_mezcla:]

            fin_escrito = max(fin_escrito, fin_valido)
            del trozo, audio

            if al_avanzar is not None:
                al_avanzar(indice + 1, total)

        if fin_escrito != tramas * salto:
            raise ErrorDecoderVae(
                "El plan de trozos no cubrio todo el latente: escritas "
                f"{fin_escrito} de {tramas * salto} muestras."
            )

        return salida

    def _comprobar_vram(self, dispositivo: torch.device, lote: int, ventana: int) -> None:
        """Aborta ANTES de asignar si la VRAM libre no da para una ventana."""
        if dispositivo.type != "cuda":
            return

        necesario = lote * ventana * BYTES_PICO_POR_TRAMA + BYTES_COLCHON_VRAM
        libre, _total = torch.cuda.mem_get_info(dispositivo)
        # Los bloques ya reservados por PyTorch y sin usar tambien estan
        # disponibles, aunque el driver los vea ocupados.
        libre += torch.cuda.memory_reserved(dispositivo) - torch.cuda.memory_allocated(
            dispositivo
        )

        if libre < necesario:
            segundos = ventana * self.hop_length / self.sampling_rate
            raise VramInsuficiente(
                f"Decode por trozos: una ventana de {ventana} tramas latentes "
                f"({segundos:.2f} s) con lote {lote} necesita ~"
                f"{necesario / 2**20:.0f} MiB y solo hay {libre / 2**20:.0f} MiB "
                f"disponibles en {dispositivo}. Reduce `ventana` o libera VRAM; "
                f"NO se reintenta, porque un OOM de driver deja el asignador de "
                f"PyTorch inservible en este proceso."
            )


# --------------------------------------------------------------------------- #
# Planificacion de las ventanas
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PlanDeTrozos:
    """Reparto de un latente de `tramas` tramas en ventanas solapadas."""

    tramas: int
    ventana: int
    solape: int
    guarda: int
    inicios: tuple[int, ...]

    @property
    def paso(self) -> int:
        return self.ventana - self.solape

    @property
    def crossfade(self) -> int:
        """Tramas de solapamiento limpio, ya sin guardas."""
        return self.solape - 2 * self.guarda

    @property
    def sobrecoste(self) -> float:
        """Fraccion de tramas decodificadas de mas por culpa del solape."""
        return len(self.inicios) * self.ventana / self.tramas - 1.0


def planificar_trozos(
    tramas: int,
    *,
    ventana: int = VENTANA_LATENTE_POR_DEFECTO,
    solape: int = SOLAPE_LATENTE_POR_DEFECTO,
    guarda: int = GUARDA_LATENTE_POR_DEFECTO,
) -> PlanDeTrozos:
    """Calcula los inicios de ventana, validando que no quede ningun hueco."""
    if ventana < 1:
        raise ErrorDecoderVae("`ventana` debe ser >= 1.")
    if solape < 0 or guarda < 0:
        raise ErrorDecoderVae("`solape` y `guarda` no pueden ser negativos.")

    if tramas <= ventana:
        # Cabe entera: una sola ventana y ninguna costura que disimular.
        return PlanDeTrozos(tramas, tramas, 0, 0, (0,))

    if solape >= ventana:
        raise ErrorDecoderVae(
            f"`solape` ({solape}) debe ser menor que `ventana` ({ventana})."
        )
    if solape <= 2 * guarda:
        # Condicion dura: tras tirar las guardas de los dos lados tiene que
        # quedar solapamiento limpio, o entre ventanas apareceria un HUECO.
        raise ErrorDecoderVae(
            f"`solape` ({solape}) debe ser > 2*guarda ({2 * guarda}): si no, al "
            f"descartar las guardas queda un hueco sin audio entre ventanas."
        )

    paso = ventana - solape
    inicios = list(range(0, tramas - ventana + 1, paso))
    if inicios[-1] + ventana < tramas:
        # Ultima ventana FIJADA al final en lugar de encogida: misma forma de
        # tensor en todas las llamadas (cuDNN autotunea una vez y el pico de VRAM
        # es constante). Cuesta redecodificar un trozo ya hecho.
        inicios.append(tramas - ventana)

    return PlanDeTrozos(tramas, ventana, solape, guarda, tuple(inicios))


# --------------------------------------------------------------------------- #
# Carga desde el artefacto
# --------------------------------------------------------------------------- #


def leer_config_vae(state_dict: dict, clave: str = CLAVE_CONFIG_VAE) -> dict:
    """Extrae y parsea el config del VAE del tensor U8 del artefacto."""
    tensor = state_dict.get(clave)
    if tensor is None:
        raise ErrorDecoderVae(
            f"El artefacto no trae {clave!r}. Sin config no se puede construir el "
            f"decoder con la topologia correcta."
        )

    crudo = tensor.detach().to("cpu").contiguous().view(torch.uint8).numpy().tobytes()
    try:
        config = json.loads(crudo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ErrorDecoderVae(f"{clave!r} no contiene un JSON UTF-8 valido: {exc}") from exc

    clase = config.get("_class_name")
    if clase != "AutoencoderOobleck":
        raise ErrorDecoderVae(
            f"El VAE del artefacto declara `_class_name` = {clase!r}; este fichero "
            f"solo implementa 'AutoencoderOobleck'."
        )
    return config


def construir_decoder(config: dict) -> OobleckDecoder:
    """Instancia el decoder con la topologia que declara el config del VAE."""
    try:
        ratios_bajada = [int(r) for r in config["downsampling_ratios"]]
        multiplos = [int(m) for m in config["channel_multiples"]]
        canales = int(config["decoder_channels"])
        canales_entrada = int(config["decoder_input_channels"])
        canales_audio = int(config["audio_channels"])
        tasa = int(config["sampling_rate"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ErrorDecoderVae(f"Config del VAE incompleta o mal formada: {exc}") from exc

    # `AutoencoderOobleck` invierte los ratios de bajada para el decoder.
    return OobleckDecoder(
        channels=canales,
        input_channels=canales_entrada,
        audio_channels=canales_audio,
        upsampling_ratios=ratios_bajada[::-1],
        channel_multiples=multiplos,
        sampling_rate=tasa,
    )


def cargar_decoder(
    state_dict: dict,
    *,
    device: str | torch.device = "cpu",
    dtype: torch.dtype = torch.float16,
    prefijo: str = PREFIJO_ESTADO,
    claves_esperadas: int | None = CLAVES_ESPERADAS,
) -> OobleckDecoder:
    """Construye el decoder y carga sus pesos desde el `state_dict` completo.

    Se queda con las claves `vae.decoder.*`, les quita el prefijo y hace
    `load_state_dict(strict=True)` **sin remapeo**. Despues fusiona la weight
    norm y deja el modulo en evaluacion y sin gradientes.

    Args:
        state_dict: el diccionario completo del artefacto (1.177 tensores).
        device: dispositivo destino. El adapter ya carga ahi los tensores, asi que
            construir el modulo en el mismo evita una copia de ida y vuelta.
        dtype: `torch.float16`. El artefacto es fp16 y no se hace upcast.
        prefijo: prefijo de las claves del decoder.
        claves_esperadas: si no es `None`, se exige ese numero exacto de claves.
    """
    config = leer_config_vae(state_dict)

    pesos = {
        clave[len(prefijo) :]: valor
        for clave, valor in state_dict.items()
        if clave.startswith(prefijo)
    }
    if not pesos:
        raise ErrorDecoderVae(f"El artefacto no trae ninguna clave con prefijo {prefijo!r}.")
    if claves_esperadas is not None and len(pesos) != claves_esperadas:
        raise ErrorDecoderVae(
            f"Se esperaban {claves_esperadas} claves con prefijo {prefijo!r} y hay "
            f"{len(pesos)}. El artefacto no es el que este codigo sabe cargar."
        )

    dispositivo = torch.device(device)

    # Construccion en `meta` y luego `to_empty`: evita inicializar 84 M de
    # parametros con kaiming para pisarlos acto seguido, y evita el pico
    # transitorio de tenerlos en fp32 (el cambio de dtype se hace en `meta`, que
    # no reserva memoria).
    with torch.device("meta"):
        decoder = construir_decoder(config)
    decoder = decoder.to(dtype=dtype).to_empty(device=dispositivo)

    decoder.load_state_dict(pesos, strict=True)
    decoder.fusionar_weight_norm()
    decoder.eval()
    decoder.requires_grad_(False)
    return decoder
