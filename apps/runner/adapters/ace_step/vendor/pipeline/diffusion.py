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
# Obra derivada de:
#
#   1. AceStepConditionGenerationModel.generate_audio (el bucle de difusion), en
#      apps/runner/adapters/ace_step/vendor/modeling_acestep_v15_turbo.py
#        Origen         : repositorio HuggingFace ACE-Step/Ace-Step1.5,
#                         revision 19671f406d603126926c1b7e2adc169acbcade22
#        SHA-256 origen : c1ab0dd547124fee7ada449b2b86eae8201dc7d15889932643bbb67e3c982444
#                         (96.036 bytes; el mismo que registra vendor/README.md)
#        Cabecera Apache-2.0 propia, la reproducida arriba.
#
#   2. VaeDecodeStateMixin._prepare_generate_music_decode_state (la validacion de
#      los latentes), en acestep/core/generation/handler/generate_music_decode.py
#        Origen         : https://github.com/ace-step/ACE-Step-1.5
#        Revision       : ca1e85fe9430179831e6bc6be790c332190a3866
#        SHA-256 origen : 5ebe4dfd65635a687a5692d37ab377ab959170e764fbedf54d6e35711cc40416
#        blob SHA-1 git : b7330503c1c8277cdb72281c14ed6b711be2414c  (10.402 bytes)
#                         verificado contra la atestacion de la API de GitHub.
#        Sin cabecera de licencia propia: aplica el MIT de la raiz.
#
#   3. AceStepConditionGenerationModel.generate_audio del MODELO BASE (el bucle
#      con guia), en apps/runner/adapters/ace_step/vendor/sft/modeling_acestep_v15_base.py
#        Origen         : repositorio HuggingFace ACE-Step/acestep-v15-sft,
#                         revision c410d249e71ea9385a7b586865e65b1473e1098d
#        SHA-256 origen : 5e3b475d46965dcd5b0d037e53a9af359305a7dbd78e2ee08b39e94c4b02ca48
#        blob SHA-1 git : 3be5113ad1a9bce551c456b8d54073b6c96faac9  (95.910 bytes)
#        Lineas origen  : 1884-1961 (preparacion del lote de CFG y bucle).
#        Cabecera Apache-2.0 propia, la reproducida arriba.
#        Anadido el     : 2026-09-02.
#
#   La guia APG en si NO se reimplementa: se IMPORTA de
#   `vendor/sft/apg_guidance.py`, que es el fichero de upstream sin una sola
#   modificacion (SHA-256 0c0ce9755952c99307ecad2fac67863d43258e34541cd37ce2f2221f59e76b15,
#   blob SHA-1 0448a3436bb42b0a667a4090087dd688e65229fb, 7.956 bytes). Ver
#   `vendor/sft/README.md`.
#
#   Copiado el : 2026-09-02
#   Licencia   : MIT — "Copyright (c) 2026 ACEStep" (LICENSE de la raiz, blob
#                SHA-1 600451d484a555c1273baa2602f32a37fdd0d0ab, 1.064 bytes,
#                copiado en D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt).
#                Uso comercial permitido.
#
# Cada cambio va marcado con un comentario "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Bucle de difusion (Euler, ODE) de `text2music` para ACE-Step 1.5.

Sirve a las **dos** variantes de pesos, que se piden con `variante=`:

* `turbo` — 8 pasos, SIN guia. Es el camino de produccion y no ha cambiado.
* `sft`   — modelo base sin destilar: N pasos (50 por defecto) y guia APG, que
  cuesta **dos** pasadas del DiT por paso.

La programacion de cada una la da `scheduler.py`; aqui esta el bucle.

El muestreador
--------------
Emparejamiento de flujo con integracion de Euler explicita. El DiT predice la
velocidad `v_t`; el estado avanza con

    x_{t+1} = x_t - v_t * (t_actual - t_siguiente)

y en el **ultimo** paso el destino es `t = 0`, con lo que la integracion se
reduce a `x0 = x_t - v_t * t`: exactamente el salto a x0 que el turbo hacia con
`get_x0_from_noise`. Por eso `scheduler.py` devuelve ahora, en las dos
variantes, `pasos + 1` tiempos acabados en 0,0 y este modulo tiene UN solo
bucle. Los valores del turbo no cambian: son los ocho de la tabla mas ese 0,0.

La cache `EncoderDecoderCache` se reutiliza entre pasos: las claves y valores de
la atencion cruzada dependen solo del condicionamiento, que no cambia en
`text2music`. Se calculan en el paso 1 y se reciclan en los demas.

La guia: el turbo no la necesita y el sft si
--------------------------------------------
(Antes aqui ponia «por que no hay CFG». Ya no es que no haya: es que depende de
la variante.)

**turbo.** Esta **destilado con la guia ya incorporada**: no hay pasada
incondicional gemela. Upstream lo dice sin rodeos en el repositorio de GitHub
(«Turbo models bake classifier-free guidance into the distillation weights and
do NOT run a twin unconditional forward pass») y sus manejadores fuerzan
`guidance_scale=1.0` antes de llegar al modelo. Con `variante="turbo"` este
modulo se comporta igual que siempre: una pasada por paso y ni un tensor de mas.

**sft.** El modelo base NO tiene la guia horneada, y sin ella genera peor de lo
que sabe. Upstream guia con **APG** (Adaptive Projected Guidance), que no es el
CFG clasico: en vez de `uncond + s*(cond - uncond)`, APG (1) acumula la
diferencia en un buffer de momento con momento **negativo** (-0,75), (2) le
recorta la norma a `norm_threshold=2,5`, (3) la **proyecta** sobre `pred_cond` y
se queda solo con la componente ORTOGONAL (`eta=0,0`), y (4) devuelve
`pred_cond + (s-1)*ortogonal`. Guiar solo en la direccion ortogonal es lo que
evita la sobresaturacion tipica del CFG alto. Nada de eso se reimplementa aqui:
se llama a `apg_forward` del fichero vendorizado sin tocar, con `dims=[1]`, que
es como lo llama el modelo base.

Por lote no, SECUENCIAL: la pasada gemela y la VRAM
---------------------------------------------------
Upstream hace la pasada gemela **por lote**: `torch.cat([xt, xt])` y el
condicionamiento concatenado con `null_condition_emb`, una sola llamada al DiT
con lote 2. Aqui se hacen **dos llamadas de lote 1**, condicional y despues
incondicional.

MEDIDO el 2026-09-02 con `spikes/dit_forward_bench.py --bsz 1|2` sobre los pesos
reales (GTX 1070, 8.191,8 MiB, attn eager, `dit.decoder` residente = 3.005,0 MiB,
contexto CUDA 1.006,8 MiB, 3 repeticiones tras 1 de calentamiento):

===========  ===  ==============  =================  ===========
L (tokens)   bsz  mediana/forward  activaciones MiB  pico MiB
===========  ===  ==============  =================  ===========
312 (25 s)     1        328,47 ms              31,7     3.036,7
312 (25 s)     2        607,36 ms              54,6     3.059,5
2250 (180 s)   1      2.898,81 ms             712,9     3.717,8
2250 (180 s)   2      5.969,34 ms           1.387,5     4.392,5
===========  ===  ==============  =================  ===========

Y lo primero que dice la medida es que **la sospecha de partida era falsa**: por
lote habria cabido. A 180 s el lote 2 solo anade 674,6 MiB de activaciones sobre
el lote 1, no los ~2.300 MiB que sugeria «duplicar las activaciones»: el grueso
de la VRAM son los pesos residentes (3.005,0 MiB), que no se duplican. Sumados
al pico de difusion de punta a punta del turbo —5.941 MiB a 180 s, del perfil de
T-03; 4.103 MiB a 25 s, medidos en la corrida de regresion del 2026-09-02—
quedarian unos 6.616 MiB, por debajo del pico GLOBAL de una generacion, que esta
en el CONDICIONAMIENTO y no aqui (7.606 MiB en T-03; 7.489 MiB en esa misma
corrida de 25 s). Asi que la eleccion no se justifica con un OOM. Se justifica
con esto:

1. **En tiempo es un empate, y a 180 s gana el secuencial.** Dos pasadas de lote
   1 son 5.797,6 ms frente a 5.969,3 ms de una de lote 2: un 2,9 % MAS RAPIDO.
   La GTX 1070 con atencion eager esta limitada por computo, no por ocupacion,
   asi que agrupar no compra nada. (A 25 s se invierte: 656,9 ms frente a
   607,4 ms, un 7,5 % a favor del lote. Irrelevante en los dos sentidos.)
2. **Devuelve 674,6 MiB de pico a 180 s** en una tarjeta cuyo margen sobre el
   pico global son 585 MiB (8.191 - 7.606). Pagar eso por un 2,9 % de perdida
   seria absurdo.
3. **El perfil de VRAM de la difusion queda IDENTICO al del turbo**, que es el
   que ya esta medido y del que cuelga el guardarrail `_exigir_vram` del shim
   (`_PICO_DIFUSION_MEDIDO`). Con lote 2 habria que volver a derivarlo.

`apg_forward` **no se entera** de la diferencia: recibe `pred_cond` y
`pred_uncond` como dos tensores ya calculados y le da igual como se obtuvieron.
La guia es identica, y que lo es esta comprobado, no supuesto:
`tests/test_diffusion_guia.py` ejecuta el bucle POR LOTE de upstream y el
secuencial con el mismo modelo determinista y exige que coincidan (el residuo,
~3e-7 RMS relativo, es el reparto del propio GEMM, y el test lo demuestra
aparte).

Lo que NO se ahorra secuencialmente es la cache: `AceStepAttention` solo cachea
la atencion CRUZADA, asi que hacen falta **dos** `EncoderDecoderCache`, una por
rama, y suman lo mismo que la del lote 2. Y hay una trampa silenciosa: reusar
UNA sola cache para las dos ramas haria que la incondicional reutilizase la K/V
cruzada de la condicional (via el flag `is_updated[layer_idx]` de
`EncoderDecoderCache`) y saldria audio incorrecto SIN error. Por eso son dos
objetos distintos y por eso este parrafo existe.

Que NO esta aqui
----------------
`infer_method="sde"` (renoise), la rama de `audio_cover_strength < 1.0` con su
condicionamiento gemelo sin cover, `retake_seed`/`retake_variance`, la
inyeccion de repintado (`repaint_mask`, `clean_src_latents`), el muestreador de
Heun, el recorte de norma de velocidad, la EMA de velocidad y la correccion DCW.

Tampoco esta `adg_forward` (Angle-based Dynamic Guidance, el `use_adg=True` de
upstream). Existe en el modulo vendorizado y se podria enchufar en una linea,
pero es una segunda guia que nadie ha pedido: la comparacion turbo-vs-sft se
hace con la guia por defecto, que es APG.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import torch
from transformers.cache_utils import DynamicCache, EncoderDecoderCache

try:  # pragma: no cover - depende de como se importe el paquete
    from .scheduler import (
        VARIANTE_POR_DEFECTO,
        defectos_de_variante,
        programacion_de_variante,
    )
except ImportError:  # pragma: no cover
    from scheduler import (  # type: ignore[no-redef]
        VARIANTE_POR_DEFECTO,
        defectos_de_variante,
        programacion_de_variante,
    )

# La guia APG viene del fichero de upstream vendorizado SIN modificar
# (`vendor/sft/apg_guidance.py`): aqui no se reimplementa una linea de guia.
#
# OJO al import. `vendor/` no es un paquete con `__init__.py` sino un espacio de
# nombres implicito, y este modulo se importa a veces como `vendor.pipeline.X`
# (shim, spikes) y a veces como modulo suelto con `vendor/pipeline` en el
# `sys.path`. En el primer caso vale el relativo; en el segundo `vendor/sft` no
# esta en ninguna ruta y hay que abrirlo por fichero. La misma trampa, del otro
# lado, que documenta `vendor/sft/README.md` para `modeling_acestep_v15_base.py`.
try:  # pragma: no cover - depende de como se importe el paquete
    from ..sft.apg_guidance import MomentumBuffer, apg_forward
except ImportError:  # pragma: no cover
    import importlib.util as _util
    from pathlib import Path as _Path

    _ruta_apg = _Path(__file__).resolve().parent.parent / "sft" / "apg_guidance.py"
    _spec = _util.spec_from_file_location("vendor_sft_apg_guidance", _ruta_apg)
    if _spec is None or _spec.loader is None:  # pragma: no cover
        raise ImportError(f"No se pudo cargar la guia APG desde {_ruta_apg}")
    _apg = _util.module_from_spec(_spec)
    _spec.loader.exec_module(_apg)
    MomentumBuffer = _apg.MomentumBuffer  # type: ignore[misc]
    apg_forward = _apg.apg_forward  # type: ignore[misc]

__all__ = [
    "ResultadoDifusion",
    "generar_latentes_text2music",
    "validar_latentes",
]


class ResultadoDifusion(dict):
    """Diccionario con los latentes generados y los tiempos por etapa.

    Se mantiene como `dict` —y no como dataclass— por compatibilidad con la forma
    que devuelve `generate_audio` upstream (`{"target_latents": ..., "time_costs":
    ...}`), de modo que un lector que venga del codigo original encuentre las
    mismas claves.
    """

    @property
    def target_latents(self) -> torch.Tensor:
        return self["target_latents"]

    @property
    def time_costs(self) -> dict[str, Any]:
        # `Any` y no `float`: ademas de los tiempos lleva el `shift`, el numero de
        # pasos, el nombre de la variante (una cadena) y las pasadas del DiT.
        return self["time_costs"]


def generar_latentes_text2music(
    *,
    model: Any,
    cond: Any,
    seed: int | None = None,
    variante: str = VARIANTE_POR_DEFECTO,
    shift: float | None = None,
    pasos: int | None = None,
    guidance_scale: float | None = None,
    cfg_interval: tuple[float, float] = (0.0, 1.0),
    on_step: Callable[[int, int], None] | None = None,
) -> ResultadoDifusion:
    """Ejecuta los pasos de difusion de la variante y devuelve los latentes limpios.

    Args:
        model: `AceStepConditionGenerationModel` ya instanciado y con pesos.
            Se usan `model.decoder`, `model.prepare_noise` y —solo si hay guia—
            `model.null_condition_emb`.
        cond: `CondicionamientoText2Music` de `conditioning.py`.
        seed: semilla de la muestra de ruido inicial. `None` = aleatoria. Se
            propaga por trazabilidad; **no** garantiza salida identica entre
            ejecuciones (driver, cuDNN y orden de reduccion en coma flotante
            mandan).
        variante: `"turbo"` (8 pasos, sin guia) o `"sft"` (N pasos con guia APG).
        shift: desplazamiento de la programacion. `None` = el de la variante
            (3,0 en turbo, redondeado al valido mas cercano; 1,0 en sft, sin
            redondeo). Ver `scheduler.py`.
        pasos: numero de pasos. `None` = el de la variante (8 / 50). En turbo
            solo se admite 8.
        guidance_scale: escala de la guia APG. `None` = la de la variante (1,0 en
            turbo, o sea sin guia; 7,0 en sft). Un valor <= 1,0 desactiva la guia
            y con ella la pasada gemela, tambien en `sft`.
        cfg_interval: `(inicio, fin)` en unidades de `t`. La guia se aplica solo
            mientras `inicio <= t_actual <= fin`; fuera de ese intervalo se usa
            la prediccion condicional a secas y **no se paga** la pasada gemela.
            Upstream: `cfg_interval_start=0.0`, `cfg_interval_end=1.0`, es decir
            siempre.
        on_step: se invoca como `on_step(paso, total)` al terminar **cada** paso,
            con `paso` de 1 a `total`. Si levanta una excepcion —que es como el
            adapter aplica el tope de segundos de GPU— se deja propagar: aqui
            **nunca** se captura. OJO: cuenta PASOS, no pasadas del DiT; con guia
            hay dos pasadas por paso.

    Returns:
        `ResultadoDifusion` con `target_latents` de forma `[1, T, 64]` y
        `time_costs`.

    MODIFICADO respecto a upstream, seis cosas:

    1. **`on_step`**. Upstream no ofrece ningun punto de control dentro del
       bucle: la unica forma de parar una generacion desbocada es esperar a que
       acabe. Nuestro adapter necesita comprobar el presupuesto de GPU en cada
       paso, asi que se anade el callback. Es la unica linea del bucle que no
       viene de upstream.
    2. **El condicionamiento llega ya calculado**. Upstream llama a
       `prepare_condition` dentro de `generate_audio`; aqui lo hace
       `conditioning.py` y esta funcion recibe el resultado. Motivo: separa lo
       que se paga una vez (codificar el texto) de lo que se paga en cada paso
       (el DiT), y permite medirlos por separado en T-03.
    3. **Sin ramas de cover ni SDE**. Con `audio_cover_strength = 1.0` el
       `cover_steps = int(infer_steps * 1.0)` de upstream vale N, asi que la
       condicion `step_idx >= cover_steps` nunca se cumple y la rama de
       condicionamiento sin cover es codigo muerto. Se elimina junto con la rama
       `infer_method == "sde"`.
    4. **Se valida el resultado** con `validar_latentes()` antes de devolverlo.
       Upstream valida mas tarde, en el manejador de decodificacion; adelantarlo
       hasta aqui hace que un desbordamiento de fp16 se atribuya al paso de
       difusion, que es donde ocurre, y no al VAE.
    5. **La pasada gemela es SECUENCIAL, no por lote** (ver el docstring del
       modulo). Upstream concatena y hace una llamada de lote 2; aqui son dos
       llamadas de lote 1 con **dos** caches distintas. El resultado de
       `apg_forward` es el mismo: recibe los dos tensores ya calculados.
    6. **Fuera de `cfg_interval` no se calcula la pasada incondicional.**
       Upstream la calcula igual (va en el mismo lote) y luego descarta la mitad
       con `vt = pred_cond`. Secuencialmente eso seria pagar una pasada del DiT
       para tirarla. No cambia la salida: la K/V de atencion cruzada de la rama
       nula no depende de `t`, asi que da igual en que paso se calcule por
       primera vez, y el buffer de momento upstream tampoco se actualiza en los
       pasos que no aplican guia.
    """
    nombre_variante, shift_efectivo, num_steps, t_schedule_list = programacion_de_variante(
        variante, shift=shift, pasos=pasos
    )
    escala = (
        defectos_de_variante(nombre_variante)["guidance_scale"]
        if guidance_scale is None
        else float(guidance_scale)
    )
    # Upstream: `do_cfg_guidance = diffusion_guidance_sale > 1.0`, verbatim.
    hay_guia = escala > 1.0
    cfg_inicio, cfg_fin = (float(cfg_interval[0]), float(cfg_interval[1]))
    if cfg_inicio > cfg_fin:
        raise ValueError(
            f"cfg_interval={cfg_interval!r} esta al reves: el inicio ({cfg_inicio}) "
            f"tiene que ser <= el fin ({cfg_fin})."
        )
    if hay_guia and nombre_variante == "turbo":
        raise ValueError(
            f"guidance_scale={escala} con variante 'turbo'. El turbo esta destilado "
            "con la guia incorporada y no tiene rama incondicional util: guiarlo "
            "duplica el coste y degrada la salida. Si quieres guia, la variante es "
            "'sft'."
        )

    context_latents = cond.context_latents
    encoder_hidden_states = cond.encoder_hidden_states
    encoder_attention_mask = cond.encoder_attention_mask
    attention_mask = cond.attention_mask

    bsz = context_latents.shape[0]
    device = context_latents.device
    dtype = context_latents.dtype
    if bsz != 1:
        raise ValueError(
            f"Este pipeline es de lote 1 por contrato; llego un lote de {bsz}. "
            "El lote de upstream arrastra el camino de cover y de repintado, que "
            "no esta vendorizado."
        )

    time_costs: dict[str, Any] = {}
    inicio_total = time.time()

    noise = model.prepare_noise(context_latents, seed)
    t_schedule = torch.tensor(t_schedule_list, device=device, dtype=dtype)
    if len(t_schedule) != num_steps + 1:
        raise RuntimeError(
            f"La programacion de '{nombre_variante}' trajo {len(t_schedule)} tiempos "
            f"y se esperaban {num_steps + 1} (N pasos + el 0,0 final)."
        )

    past_key_values = EncoderDecoderCache(DynamicCache(), DynamicCache())

    # Rama incondicional. Se prepara UNA vez: ni el condicionamiento nulo ni su
    # cache dependen de `t`.
    #
    # `null_condition_emb` es un `nn.Parameter` ENTRENADO que viene en los dos
    # checkpoints (`dit.null_condition_emb`, [1, 1, 2048]); el turbo lo tiene y
    # simplemente no lo usa. `.contiguous()` porque `expand_as` devuelve una
    # vista de zancada 0 y upstream le entrega al DiT el resultado de un
    # `torch.cat`, que es contiguo; son 0,9 MiB y evitan depender de que ningun
    # `view()` del modelo tropiece con la zancada.
    encoder_hidden_states_nulo = None
    past_key_values_nulo = None
    if hay_guia:
        encoder_hidden_states_nulo = (
            model.null_condition_emb.detach()
            .expand_as(encoder_hidden_states)
            .to(device=device, dtype=dtype)
            .contiguous()
        )
        # DOS caches. Ver el docstring del modulo: compartir una sola haria que
        # la rama nula reutilizase la K/V cruzada de la condicional sin avisar.
        past_key_values_nulo = EncoderDecoderCache(DynamicCache(), DynamicCache())
    momentum_buffer = MomentumBuffer() if hay_guia else None
    pasadas_dit = 0

    def _pasada(x, t_tensor, enc, cache):
        """Una pasada del DiT. Devuelve `(velocidad, cache actualizada)`."""
        nonlocal pasadas_dit
        with torch.no_grad():
            salidas = model.decoder(
                hidden_states=x,
                timestep=t_tensor,
                timestep_r=t_tensor,
                attention_mask=attention_mask,
                encoder_hidden_states=enc,
                encoder_attention_mask=encoder_attention_mask,
                context_latents=context_latents,
                use_cache=True,
                past_key_values=cache,
            )
        pasadas_dit += 1
        return salidas[0], salidas[1]

    xt = noise
    for step_idx in range(num_steps):
        current_timestep = t_schedule[step_idx].item()
        t_curr_tensor = current_timestep * torch.ones((bsz,), device=device, dtype=dtype)

        vt, past_key_values = _pasada(
            xt, t_curr_tensor, encoder_hidden_states, past_key_values
        )

        # Upstream: `apply_cfg_guidance = t_curr >= cfg_interval_start and
        # t_curr <= cfg_interval_end`, verbatim.
        if hay_guia and cfg_inicio <= current_timestep <= cfg_fin:
            vt_nulo, past_key_values_nulo = _pasada(
                xt, t_curr_tensor, encoder_hidden_states_nulo, past_key_values_nulo
            )
            vt = apg_forward(
                pred_cond=vt,
                pred_uncond=vt_nulo,
                guidance_scale=escala,
                momentum_buffer=momentum_buffer,
                dims=[1],
            )
            del vt_nulo

        # Euler explicito: dx/dt = -v  =>  x_{t+1} = x_t - v_t * dt.
        # En el ultimo paso `next_timestep` vale 0, con lo que `dt = t_actual` y
        # esto ES el salto a x0 (`get_x0_from_noise`), sin caso especial.
        next_timestep = t_schedule[step_idx + 1].item()
        dt = current_timestep - next_timestep
        dt_tensor = dt * torch.ones((bsz,), device=device, dtype=dtype).unsqueeze(-1).unsqueeze(-1)
        xt = xt - vt * dt_tensor

        if on_step is not None:
            on_step(step_idx + 1, num_steps)

    fin = time.time()
    time_costs["diffusion_time_cost"] = fin - inicio_total
    time_costs["diffusion_per_step_time_cost"] = time_costs["diffusion_time_cost"] / num_steps
    time_costs["total_time_cost"] = fin - inicio_total
    time_costs["shift"] = shift_efectivo
    time_costs["num_steps"] = float(num_steps)
    # MODIFICADO respecto a upstream: no existen. Con guia, el numero de pasadas
    # del DiT ya no se deduce del de pasos, y es LA magnitud que manda en el
    # tiempo de pared. Sin registrarla, comparar un tiempo del sft con uno del
    # turbo no significa nada.
    time_costs["variante"] = nombre_variante
    time_costs["guidance_scale"] = float(escala)
    time_costs["dit_forward_passes"] = float(pasadas_dit)

    validar_latentes(xt)
    return ResultadoDifusion(target_latents=xt, time_costs=time_costs)


def validar_latentes(pred_latents: torch.Tensor) -> None:
    """Aborta si los latentes salieron con NaN/Inf o completamente a cero.

    Upstream: `generate_music_decode._prepare_generate_music_decode_state`.

    MODIFICADO respecto a upstream: la lista de causas probables se ha reescrito
    para este despliegue. Las de upstream hablan de LoRA, de `--backend pt` y de
    variables de entorno de su CLI, ninguna de las cuales existe aqui; la que si
    aplica —desbordamiento de fp16 en una GPU pre-Ampere— se conserva y se
    concreta, porque nuestro artefacto es fp16 y la GPU objetivo es Pascal.
    """
    if torch.isnan(pred_latents).any() or torch.isinf(pred_latents).any():
        n_nan = int(torch.isnan(pred_latents).sum().item())
        n_inf = int(torch.isinf(pred_latents).sum().item())
        raise RuntimeError(
            "La difusion produjo latentes con NaN o Inf "
            f"(forma={list(pred_latents.shape)}, dtype={pred_latents.dtype}, "
            f"device={pred_latents.device}, nan={n_nan}, inf={n_inf}).\n"
            "Causas probables, por orden:\n"
            "  1. Desbordamiento de fp16. El artefacto es fp16 entero; en una GPU "
            "pre-Ampere no hay bf16 al que caer. Si se repite, hay que promover a "
            "fp32 la capa que desborda, no el artefacto completo.\n"
            "  2. Pesos y configuracion desparejados: el 'config.json' vendorizado "
            "tiene que ser el de la MISMA revision que los pesos.\n"
            "  3. Descarga a CPU a medias, con parametros en dispositivos distintos."
        )
    if pred_latents.numel() > 0 and pred_latents.abs().sum() == 0:
        raise RuntimeError(
            "La difusion produjo latentes identicamente cero. Suele significar que "
            "los pesos no se cargaron (state_dict vacio o claves sin emparejar) o "
            "que la configuracion no corresponde al checkpoint."
        )
