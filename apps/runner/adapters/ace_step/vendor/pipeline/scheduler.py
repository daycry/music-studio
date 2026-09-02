# Copyright 2025 The ACESTEO Team. All rights reserved.
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
# (El aviso de arriba se reproduce VERBATIM del fichero origen, incluida la
# errata "ACESTEO" del propio upstream. Alterar un aviso de copyright para
# "arreglar" una errata es justo lo que ni Apache-2.0 ni MIT permiten.)
#
# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION  (Apache License 2.0, seccion 4(b))
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original.
#
# Obra derivada de la tabla de programacion de pasos de tiempo de
# `AceStepConditionGenerationModel.generate_audio`.
#
#   Origen          : apps/runner/adapters/ace_step/vendor/modeling_acestep_v15_turbo.py
#                     (copia local ya vendorizada del repositorio HuggingFace
#                     `ACE-Step/Ace-Step1.5`, revision
#                     19671f406d603126926c1b7e2adc169acbcade22)
#   SHA-256 origen  : c1ab0dd547124fee7ada449b2b86eae8201dc7d15889932643bbb67e3c982444
#                     (96.036 bytes; el mismo que registra vendor/README.md)
#   Copiado el      : 2026-09-01
#   Licencia        : el repositorio de codigo es MIT
#                     (github.com/ace-step/ACE-Step-1.5, LICENSE blob SHA-1
#                     600451d484a555c1273baa2602f32a37fdd0d0ab, "Copyright (c)
#                     2026 ACEStep"); el fichero origen lleva ademas, en su
#                     propia cabecera, el aviso Apache-2.0 reproducido arriba.
#                     Ambas permiten uso comercial. Copia del LICENSE en
#                     D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt
#
#   Verificacion cruzada: la misma tabla aparece identica en
#   acestep/models/turbo/modeling_acestep_v15_turbo.py de
#   github.com/ace-step/ACE-Step-1.5 @ ca1e85fe9430179831e6bc6be790c332190a3866
#   (108.712 bytes), lo que descarta que la copia de HuggingFace este desfasada.
#
# Cada cambio va marcado con un comentario "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Programacion de pasos de tiempo (`timestep schedule`) del turbo de ACE-Step 1.5.

Que es esto
-----------
El turbo esta **destilado** sobre un conjunto DISCRETO de pasos de tiempo. No es
un muestreador continuo al que se le pueda pedir «12 pasos con shift 2,5»: los
pesos solo han visto tres programaciones (`shift` 1, 2 y 3) de ocho pasos cada
una. Upstream lo hace explicito redondeando cualquier `shift` al valido mas
cercano y mapeando cualquier lista de pasos personalizada al valor valido mas
proximo, en lugar de interpolar.

La programacion de `shift=3.0` —la que usa nuestro pipeline por defecto, y la
unica que el brief de T-03 autoriza— es la tabla `SHIFT_TIMESTEPS[3.0]`. Su
forma cerrada es la transformada de desplazamiento habitual del emparejamiento
de flujo:

    t_desplazado = shift * t / (1 + (shift - 1) * t)      con t = 1 - i/8

Se ha verificado a mano que la formula reproduce los ocho valores de la tabla
(por ejemplo t=0,875 -> 3*0,875/(1+2*0,875) = 2,625/2,75 = 0,9545454...). Se
conserva **la tabla literal** y no la formula porque la tabla es la fuente de
verdad de upstream: si algun dia difieren, manda la tabla, que es lo que vieron
los pesos.

Que NO esta aqui
----------------
* **Programacion por `timesteps` a medida.** Upstream acepta una lista de hasta
  20 pasos y mapea cada valor al valido mas cercano (`VALID_TIMESTEPS`). No hace
  falta para `text2music` de 8 pasos y es una superficie de entrada que solo
  puede degradar la calidad en silencio.
* **`infer_steps` variable**, `sampler_mode="heun"`, `velocity_ema_factor`,
  correccion DCW y demas perillas: no existen en la revision del modelo que
  tenemos (son posteriores, del repositorio de GitHub) y no aplican a 8 pasos.
* **SDE.** Upstream ofrece `infer_method="sde"` (renoise). Nuestro camino es ODE
  puro; ver `diffusion.py`.
"""

from __future__ import annotations

__all__ = [
    "VALID_SHIFTS",
    "SHIFT_TIMESTEPS",
    "SHIFT_POR_DEFECTO",
    "PASOS_POR_DEFECTO",
    "construir_programacion",
]


#: Desplazamientos que el turbo admite. Upstream:
#: `generate_audio::VALID_SHIFTS`, verbatim.
VALID_SHIFTS = [1.0, 2.0, 3.0]

#: Programacion por desplazamiento, con `fix_nfe=8` y sin el 0 final (el ultimo
#: paso salta a x0 directamente, no integra hasta t=0).
#: Upstream: `generate_audio::SHIFT_TIMESTEPS`, verbatim.
SHIFT_TIMESTEPS = {
    1.0: [1.0, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125],
    2.0: [
        1.0,
        0.9333333333333333,
        0.8571428571428571,
        0.7692307692307693,
        0.6666666666666666,
        0.5454545454545454,
        0.4,
        0.2222222222222222,
    ],
    3.0: [
        1.0,
        0.9545454545454546,
        0.9,
        0.8333333333333334,
        0.75,
        0.6428571428571429,
        0.5,
        0.3,
    ],
}

#: Desplazamiento por defecto del pipeline. Es el que fija el brief de T-03 y el
#: que usa la interfaz de upstream para el turbo.
SHIFT_POR_DEFECTO = 3.0

#: Numero de pasos de la programacion. Constante por construccion: las tres
#: tablas tienen ocho entradas. Upstream lo expone como `fix_nfe=8` pero **no lo
#: usa**: la tabla esta fijada a 8 pasos.
PASOS_POR_DEFECTO = 8


def construir_programacion(shift: float = SHIFT_POR_DEFECTO) -> list[float]:
    """Devuelve la lista de pasos de tiempo para el `shift` pedido.

    Args:
        shift: desplazamiento de la programacion. Se redondea al valor valido
            mas cercano de `VALID_SHIFTS`, igual que upstream.

    Returns:
        Lista de 8 flotantes en orden descendente, de 1.0 al ultimo paso.

    Raises:
        ValueError: si `shift` no es un numero finito.

    MODIFICADO respecto a upstream: donde upstream **avisa por log** de que ha
    redondeado el `shift`, aqui se devuelve la tabla igual pero el redondeo se
    deja explicito en el valor devuelto por `programacion_efectiva()`. Motivo:
    en el runner nadie lee los logs de una biblioteca vendorizada durante una
    generacion, y un `shift=2.5` silenciosamente convertido en 3.0 es
    exactamente el tipo de diferencia que luego nadie sabe explicar en G1.
    """
    if shift != shift or shift in (float("inf"), float("-inf")):  # NaN o infinito
        raise ValueError(f"shift={shift!r} no es un numero finito.")
    shift_efectivo = min(VALID_SHIFTS, key=lambda valido: abs(valido - float(shift)))
    return list(SHIFT_TIMESTEPS[shift_efectivo])


def programacion_efectiva(shift: float = SHIFT_POR_DEFECTO) -> tuple[float, list[float]]:
    """Como `construir_programacion`, pero devolviendo tambien el `shift` real.

    MODIFICADO respecto a upstream: no existe en upstream. Es el par que permite
    al llamante registrar en la telemetria el `shift` que se aplico de verdad,
    no el que se pidio.
    """
    if shift != shift or shift in (float("inf"), float("-inf")):
        raise ValueError(f"shift={shift!r} no es un numero finito.")
    shift_efectivo = min(VALID_SHIFTS, key=lambda valido: abs(valido - float(shift)))
    return shift_efectivo, list(SHIFT_TIMESTEPS[shift_efectivo])
