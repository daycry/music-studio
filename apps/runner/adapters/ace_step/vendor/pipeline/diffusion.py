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
#   Copiado el : 2026-09-02
#   Licencia   : MIT — "Copyright (c) 2026 ACEStep" (LICENSE de la raiz, blob
#                SHA-1 600451d484a555c1273baa2602f32a37fdd0d0ab, 1.064 bytes,
#                copiado en D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt).
#                Uso comercial permitido.
#
# Cada cambio va marcado con un comentario "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Bucle de difusion (Euler, ODE) de `text2music` para ACE-Step 1.5 turbo.

El muestreador
--------------
Emparejamiento de flujo con integracion de Euler explicita. El DiT predice la
velocidad `v_t`; el estado avanza con

    x_{t+1} = x_t - v_t * (t_actual - t_siguiente)

y en el **ultimo** paso no se integra: se salta a `x0` de golpe con
`x0 = x_t - v_t * t`. Eso, y no otra cosa, es por lo que la programacion de
`scheduler.py` tiene ocho entradas y no nueve: no hay un `t=0` al que llegar
integrando.

La cache `EncoderDecoderCache` se reutiliza entre los ocho pasos: las claves y
valores de la atencion cruzada dependen solo del condicionamiento, que no cambia
en `text2music`. Se calculan en el paso 1 y se reciclan en los siete restantes.

Por que no hay CFG
------------------
El turbo esta **destilado con la guia ya incorporada**: no existe pasada
incondicional gemela. Upstream lo dice sin rodeos en el repositorio de GitHub
(«Turbo models bake classifier-free guidance into the distillation weights and
do NOT run a twin unconditional forward pass») y sus manejadores fuerzan
`guidance_scale=1.0` antes de llegar al modelo. Anadir CFG aqui duplicaria el
coste por paso a cambio de nada.

Que NO esta aqui
----------------
`infer_method="sde"` (renoise), la rama de `audio_cover_strength < 1.0` con su
condicionamiento gemelo sin cover, `retake_seed`/`retake_variance`, la
inyeccion de repintado (`repaint_mask`, `clean_src_latents`), el muestreador de
Heun, el recorte de norma de velocidad, la EMA de velocidad y la correccion DCW.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import torch
from transformers.cache_utils import DynamicCache, EncoderDecoderCache

try:  # pragma: no cover - depende de como se importe el paquete
    from .scheduler import SHIFT_POR_DEFECTO, programacion_efectiva
except ImportError:  # pragma: no cover
    from scheduler import SHIFT_POR_DEFECTO, programacion_efectiva  # type: ignore[no-redef]

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
    def time_costs(self) -> dict[str, float]:
        return self["time_costs"]


def generar_latentes_text2music(
    *,
    model: Any,
    cond: Any,
    seed: int | None = None,
    shift: float = SHIFT_POR_DEFECTO,
    on_step: Callable[[int, int], None] | None = None,
) -> ResultadoDifusion:
    """Ejecuta los 8 pasos de difusion y devuelve los latentes limpios.

    Args:
        model: `AceStepConditionGenerationModel` ya instanciado y con pesos.
            Se usan `model.decoder`, `model.prepare_noise` y
            `model.get_x0_from_noise`.
        cond: `CondicionamientoText2Music` de `conditioning.py`.
        seed: semilla de la muestra de ruido inicial. `None` = aleatoria. Se
            propaga por trazabilidad; **no** garantiza salida identica entre
            ejecuciones (driver, cuDNN y orden de reduccion en coma flotante
            mandan).
        shift: desplazamiento de la programacion; se redondea al valido mas
            cercano (ver `scheduler.py`).
        on_step: se invoca como `on_step(paso, total)` al terminar **cada** paso,
            con `paso` de 1 a `total`. Si levanta una excepcion —que es como el
            adapter aplica el tope de segundos de GPU— se deja propagar: aqui
            **nunca** se captura.

    Returns:
        `ResultadoDifusion` con `target_latents` de forma `[1, T, 64]` y
        `time_costs`.

    MODIFICADO respecto a upstream, cuatro cosas:

    1. **`on_step`**. Upstream no ofrece ningun punto de control dentro del
       bucle: la unica forma de parar una generacion desbocada es esperar a que
       acabe. Nuestro adapter necesita comprobar el presupuesto de GPU en cada
       paso, asi que se anade el callback. Es la unica linea del bucle que no
       viene de upstream.
    2. **El condicionamiento llega ya calculado**. Upstream llama a
       `prepare_condition` dentro de `generate_audio`; aqui lo hace
       `conditioning.py` y esta funcion recibe el resultado. Motivo: separa lo
       que se paga una vez (codificar el texto) de lo que se paga ocho veces
       (el DiT), y permite medirlos por separado en T-03.
    3. **Sin ramas de cover ni SDE**. Con `audio_cover_strength = 1.0` el
       `cover_steps = int(num_steps * 1.0)` de upstream vale 8, asi que la
       condicion `step_idx >= cover_steps` nunca se cumple y la rama de
       condicionamiento sin cover es codigo muerto. Se elimina junto con la rama
       `infer_method == "sde"`.
    4. **Se valida el resultado** con `validar_latentes()` antes de devolverlo.
       Upstream valida mas tarde, en el manejador de decodificacion; adelantarlo
       hasta aqui hace que un desbordamiento de fp16 se atribuya al paso de
       difusion, que es donde ocurre, y no al VAE.
    """
    shift_efectivo, t_schedule_list = programacion_efectiva(shift)

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

    time_costs: dict[str, float] = {}
    inicio_total = time.time()

    noise = model.prepare_noise(context_latents, seed)
    t_schedule = torch.tensor(t_schedule_list, device=device, dtype=dtype)
    num_steps = len(t_schedule)

    past_key_values = EncoderDecoderCache(DynamicCache(), DynamicCache())

    xt = noise
    for step_idx in range(num_steps):
        current_timestep = t_schedule[step_idx].item()
        t_curr_tensor = current_timestep * torch.ones((bsz,), device=device, dtype=dtype)

        with torch.no_grad():
            decoder_outputs = model.decoder(
                hidden_states=xt,
                timestep=t_curr_tensor,
                timestep_r=t_curr_tensor,
                attention_mask=attention_mask,
                encoder_hidden_states=encoder_hidden_states,
                encoder_attention_mask=encoder_attention_mask,
                context_latents=context_latents,
                use_cache=True,
                past_key_values=past_key_values,
            )

        vt = decoder_outputs[0]
        past_key_values = decoder_outputs[1]

        if step_idx == num_steps - 1:
            # Ultimo paso: salto directo a x0, sin integrar.
            xt = model.get_x0_from_noise(xt, vt, t_curr_tensor)
            if on_step is not None:
                on_step(step_idx + 1, num_steps)
            break

        # Euler explicito: dx/dt = -v  =>  x_{t+1} = x_t - v_t * dt
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
