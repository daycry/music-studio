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
# ESTE FICHERO HA SIDO MODIFICADO respecto de los originales.
#
# Obra derivada de la programacion de pasos de tiempo de
# `AceStepConditionGenerationModel.generate_audio`, en sus DOS variantes:
#
# ---------------------------------------------------------------------------
# Origen 1 — turbo (tabla discreta de 8 pasos)
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
# ---------------------------------------------------------------------------
# Origen 2 — sft / modelo base (programacion CONTINUA, anadida el 2026-09-02)
#   Origen          : apps/runner/adapters/ace_step/vendor/sft/modeling_acestep_v15_base.py
#                     (copia local ya vendorizada del repositorio HuggingFace
#                     `ACE-Step/acestep-v15-sft`, revision
#                     c410d249e71ea9385a7b586865e65b1473e1098d)
#   SHA-256 origen  : 5e3b475d46965dcd5b0d037e53a9af359305a7dbd78e2ee08b39e94c4b02ca48
#                     blob SHA-1 3be5113ad1a9bce551c456b8d54073b6c96faac9
#                     (95.910 bytes; los que registra vendor/sft/README.md)
#   Lineas origen   : `generate_audio`, 1864-1872 (construccion de `t`).
#   Licencia        : la misma MIT de la raiz del repositorio de codigo, mas la
#                     cabecera Apache-2.0 propia del fichero, reproducida arriba.
#
#   Los valores por defecto de la variante `sft` (shift 1,0; guia 7,0; intervalo
#   de guia [0,0, 1,0]) NO salen de la firma de `generate_audio` sino de
#   `GenerationParams` de acestep/inference.py, mismo repositorio de GitHub,
#   revision ca1e85fe9430179831e6bc6be790c332190a3866, consultado el 2026-09-02:
#       shift: float = 1.0
#       guidance_scale: float = 7.0        # "Only support for non-turbo model"
#       cfg_interval_start: float = 0.0
#       cfg_interval_end: float = 1.0
#       inference_steps: int = 8           # "e.g., 8 for turbo, 32-100 for base"
#
# Cada cambio va marcado con un comentario "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Programacion de pasos de tiempo (`timestep schedule`) de ACE-Step 1.5.

Aqui conviven **dos** programaciones que no se parecen en nada, una por
variante de pesos, y el resto del modulo existe para que no se mezclen:

* `turbo` — tabla DISCRETA de 8 pasos, tal cual la horneo la destilacion.
* `sft`   — programacion CONTINUA (`linspace` + desplazamiento) de N pasos, la
  del modelo base sin destilar, que es el que necesita guia.

Que es esto (turbo)
-------------------
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

Que es esto (sft)
-----------------
El `sft` es el MISMO entrenamiento sin destilar, y por eso no tiene tablas: su
`generate_audio` construye la programacion en tiempo de ejecucion,

    t = torch.linspace(1.0, 0.0, infer_steps + 1)
    if shift != 1.0:
        t = shift * t / (1 + (shift - 1) * t)

y despues itera sobre los pares `zip(t[:-1], t[1:])`. Es la MISMA forma cerrada
que reproduce la tabla del turbo —la transformada de desplazamiento del
emparejamiento de flujo— pero evaluada en N+1 puntos y **con el 0 final**, no
en 8 y sin el. Lo que hace el turbo con un salto explicito a x0 en el ultimo
paso, el `sft` lo hace integrando hasta `t_prev = 0`; son la misma operacion
(`x - v*t`), y `diffusion.py` las unifica en un solo bucle.

Las tres diferencias que hay que tener en la cabeza al comparar:

===================  ==================  ===============================
                     turbo               sft
===================  ==================  ===============================
pasos                8, fijos            N (por defecto 50)
`shift`              3,0 (tabla)         1,0 (continuo, sin redondeo)
guia                 ninguna (horneada)  APG, escala 7,0 (`diffusion.py`)
===================  ==================  ===============================

Por que 50 y no 30: la firma de `generate_audio` trae `infer_steps: int = 30`,
pero ese numero es el del *banco de pruebas* del propio fichero, no el de la
interfaz. La interfaz de upstream (`GenerationParams`, citada en la cabecera)
documenta el rango del modelo base como «32-100» y deja el defecto en 8 porque
lo comparte con el turbo. 50 es el punto medio de ese rango y el que fija el
encargo de esta comparacion; se deja **explicito** en `PASOS_SFT_POR_DEFECTO`,
no escondido en la firma de una funcion.

Que NO esta aqui
----------------
* **Programacion por `timesteps` a medida.** Upstream acepta, en las dos
  variantes, una lista de pasos suministrada por el llamante: el turbo mapea
  cada valor al valido mas cercano (`VALID_TIMESTEPS`) y el `sft` la usa tal
  cual (`timesteps is not None`). No hace falta para `text2music` y es una
  superficie de entrada que solo puede degradar la calidad en silencio.
* **`sampler_mode="heun"`**, `velocity_ema_factor`, recorte de norma de
  velocidad y correccion DCW: no existen en NINGUNA de las dos revisiones de
  modelo que tenemos vendorizadas (son posteriores, del repositorio de GitHub).
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
    "programacion_efectiva",
    # -- variantes ---------------------------------------------------------- #
    "VARIANTES",
    "VARIANTE_POR_DEFECTO",
    "PASOS_SFT_POR_DEFECTO",
    "SHIFT_SFT_POR_DEFECTO",
    "GUIA_SFT_POR_DEFECTO",
    "MAX_PASOS_SFT",
    "construir_programacion_continua",
    "defectos_de_variante",
    "normalizar_variante",
    "programacion_de_variante",
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


# --------------------------------------------------------------------------- #
# Variante `sft`: programacion continua
# --------------------------------------------------------------------------- #
# MODIFICADO respecto a upstream: todo lo que sigue no existe como modulo en
# upstream. Es la programacion que `generate_audio` del modelo base construye
# EN LINEA (lineas 1864-1872 del fichero origen), sacada a funcion para que
# convivan las dos variantes sin que la del turbo se entere. La del turbo, de
# aqui hacia arriba, NO se ha tocado.

#: Variantes de pesos que este pipeline sabe muestrear.
VARIANTES = ("turbo", "sft")

#: Variante por defecto. Sigue siendo el turbo: es el artefacto de produccion, y
#: un defecto distinto convertiria en silenciosa la diferencia entre 8 pasos sin
#: guia y 100 pasadas del DiT con guia.
VARIANTE_POR_DEFECTO = "turbo"

#: Pasos del `sft`. Ver el docstring del modulo: el rango que documenta upstream
#: para el modelo base es 32-100 y 50 es el que fija el encargo.
PASOS_SFT_POR_DEFECTO = 50

#: Desplazamiento del `sft`. `GenerationParams::shift = 1.0`, es decir: **sin**
#: desplazamiento. OJO, no es el 3,0 del turbo; usar el del turbo aqui seria
#: cambiar la programacion entera sin darse cuenta.
SHIFT_SFT_POR_DEFECTO = 1.0

#: Escala de guia del `sft` (`GenerationParams::guidance_scale = 7.0`). Vive en
#: este modulo, y no en `diffusion.py`, porque es un defecto POR VARIANTE: el
#: turbo tiene que quedarse en 1,0 (sin guia) pase lo que pase.
GUIA_SFT_POR_DEFECTO = 7.0

#: Techo de pasos. No es de upstream (que no pone ninguno): es un guardarrail
#: nuestro. En la GTX 1070 cada paso del `sft` son DOS pasadas del DiT de ~2,9 s
#: a 180 s de audio, o sea ~5,7 s por paso: 100 pasos ya son ~9,5 min de pared
#: solo de difusion. Por encima de 100 no hay ni respaldo de upstream (su rango
#: documentado acaba ahi) ni paciencia.
MAX_PASOS_SFT = 100


def normalizar_variante(variante: str) -> str:
    """Valida el nombre de la variante. No adivina: o es una de `VARIANTES` o falla.

    MODIFICADO respecto a upstream: no existe. Upstream distingue las variantes
    por el fichero de modelo que carga (`modeling_..._turbo` frente a
    `modeling_..._base`) y por un campo `is_turbo` del config que, medido, no lee
    nadie. Aqui el codigo del modelo es el mismo para las dos —las 677 claves y
    las formas coinciden— asi que la variante la tiene que decir el llamante.
    """
    if not isinstance(variante, str):
        raise ValueError(f"variante={variante!r} no es una cadena.")
    nombre = variante.strip().lower()
    if nombre not in VARIANTES:
        raise ValueError(
            f"variante={variante!r} desconocida. Admitidas: {list(VARIANTES)}."
        )
    return nombre


def defectos_de_variante(variante: str) -> dict[str, float | int]:
    """Defectos de `shift`, `pasos` y escala de guia de una variante.

    Returns:
        `{"shift": float, "pasos": int, "guidance_scale": float}`.

    MODIFICADO respecto a upstream: no existe. Es el sitio unico donde se
    responde «que numeros van con estos pesos», para que ni el shim ni el
    generador tengan que recordarlo.
    """
    nombre = normalizar_variante(variante)
    if nombre == "turbo":
        # `guidance_scale` 1,0 = sin guia. El turbo la trae horneada en los
        # pesos de la destilacion; ver `diffusion.py`.
        return {
            "shift": SHIFT_POR_DEFECTO,
            "pasos": PASOS_POR_DEFECTO,
            "guidance_scale": 1.0,
        }
    return {
        "shift": SHIFT_SFT_POR_DEFECTO,
        "pasos": PASOS_SFT_POR_DEFECTO,
        "guidance_scale": GUIA_SFT_POR_DEFECTO,
    }


def construir_programacion_continua(
    pasos: int = PASOS_SFT_POR_DEFECTO,
    shift: float = SHIFT_SFT_POR_DEFECTO,
) -> list[float]:
    """Programacion continua del modelo base: `pasos + 1` tiempos, de 1,0 a 0,0.

    Reproduce, en coma flotante de Python:

        t = torch.linspace(1.0, 0.0, pasos + 1)
        if shift != 1.0:
            t = shift * t / (1 + (shift - 1) * t)

    Args:
        pasos: numero de pasos de difusion (N). La lista devuelta tiene N+1
            elementos: el ultimo es 0,0 y es el destino del ultimo paso.
        shift: desplazamiento. A diferencia del turbo **no se redondea a una
            tabla**: el modelo base no esta destilado sobre pasos discretos, asi
            que cualquier valor positivo es legitimo.

    Returns:
        Lista de `pasos + 1` flotantes estrictamente decreciente, de 1,0 a 0,0.

    Raises:
        ValueError: si `pasos` no esta en [1, MAX_PASOS_SFT] o `shift` no es un
            numero finito estrictamente positivo.

    MODIFICADO respecto a upstream, dos cosas:

    1. **Se calcula en `float` de Python (doble), no en el dtype del modelo.**
       Upstream hace el `linspace` y la transformada directamente en fp16, que
       es el dtype de los latentes, asi que sus valores llevan el redondeo de
       cada operacion intermedia; aqui se calcula exacto y se redondea UNA vez,
       cuando `diffusion.py` construye el tensor. La diferencia es como mucho de
       medio ulp de fp16 (~5e-4 cerca de t=1) y va a favor de la precision, pero
       **es una diferencia**: si alguna vez hay que reproducir bit a bit una
       salida de upstream, es aqui donde mirar. Se hace asi porque este modulo
       tiene que poder importarse sin `torch` (la suite de tests corre sin el).
    2. **Techo de pasos** (`MAX_PASOS_SFT`) y validacion de `shift > 0`. Upstream
       clampa `shift <= 0` a 1,0 y `pasos < 1` a 1 en `GenerationParams`, es
       decir corrige en silencio; aqui se aborta. Un `shift=0` que se convierte
       solo en 1,0 es media hora de GPU generando otra cosa distinta de la que
       se pidio.
    """
    if not isinstance(pasos, int) or isinstance(pasos, bool):
        raise ValueError(f"pasos={pasos!r} tiene que ser un entero.")
    if not 1 <= pasos <= MAX_PASOS_SFT:
        raise ValueError(
            f"pasos={pasos} fuera de rango: se admite de 1 a {MAX_PASOS_SFT}. "
            "El rango que documenta upstream para el modelo base es 32-100."
        )
    valor = float(shift)
    if valor != valor or valor in (float("inf"), float("-inf")):
        raise ValueError(f"shift={shift!r} no es un numero finito.")
    if valor <= 0.0:
        raise ValueError(
            f"shift={shift!r} tiene que ser > 0: con shift=0 la transformada da "
            "0/0 y con shift<0 el denominador se anula dentro del intervalo."
        )

    # `torch.linspace(1, 0, n+1)` produce exactamente 1 - i/n.
    t = [1.0 - i / pasos for i in range(pasos + 1)]
    if valor != 1.0:
        t = [valor * x / (1.0 + (valor - 1.0) * x) for x in t]
    # El ultimo punto es 0,0 por construccion en las dos ramas (la transformada
    # manda 0 a 0). Se fuerza para que no dependa del redondeo de la division.
    t[-1] = 0.0
    return t


def programacion_de_variante(
    variante: str = VARIANTE_POR_DEFECTO,
    *,
    shift: float | None = None,
    pasos: int | None = None,
) -> tuple[str, float, int, list[float]]:
    """Programacion completa de una variante, lista para el bucle de difusion.

    Args:
        variante: "turbo" o "sft".
        shift: desplazamiento; `None` = el de la variante.
        pasos: numero de pasos; `None` = el de la variante. En el turbo el UNICO
            valor admitido es 8 (ver `Raises`).

    Returns:
        `(variante, shift_efectivo, pasos, tiempos)`, donde `tiempos` tiene
        **`pasos + 1`** elementos y acaba en 0,0 en las dos variantes. Ese 0,0
        final es el destino del ultimo paso: integrar hasta el es exactamente el
        `get_x0_from_noise` que el turbo hacia por separado (`x - v*t`), asi que
        un unico bucle sirve para las dos. Lo congela
        `tests/test_scheduler_variantes.py`, que compara los 9 valores del turbo
        contra la tabla literal.

    Raises:
        ValueError: variante desconocida, o `pasos` distinto de 8 en el turbo.

    MODIFICADO respecto a upstream: no existe; upstream tiene dos ficheros de
    modelo distintos y cada uno construye lo suyo. Aqui hay un solo pipeline, y
    esta funcion es la frontera donde se decide cual de las dos programaciones
    sale.
    """
    nombre = normalizar_variante(variante)
    defectos = defectos_de_variante(nombre)
    shift_pedido = defectos["shift"] if shift is None else float(shift)

    if nombre == "turbo":
        if pasos is not None and int(pasos) != PASOS_POR_DEFECTO:
            raise ValueError(
                f"pasos={pasos} no es valido para la variante 'turbo': la "
                f"destilacion solo vio programaciones de {PASOS_POR_DEFECTO} "
                "pasos y no hay forma de interpolar entre ellas. Si quieres mas "
                "pasos, la variante es 'sft'."
            )
        shift_efectivo, tiempos = programacion_efectiva(shift_pedido)
        # El 0,0 que la tabla del turbo NO trae. No cambia ni un valor de la
        # tabla: la extiende con el destino que el bucle ya usaba de forma
        # implicita al saltar a x0.
        return nombre, shift_efectivo, PASOS_POR_DEFECTO, [*tiempos, 0.0]

    n = defectos["pasos"] if pasos is None else int(pasos)
    return (
        nombre,
        float(shift_pedido),
        int(n),
        construir_programacion_continua(n, shift_pedido),
    )
