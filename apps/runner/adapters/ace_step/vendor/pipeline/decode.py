# ---------------------------------------------------------------------------
# CODIGO VENDORIZADO — obra derivada de ACE-Step 1.5 (licencia MIT).
#
#   Origen          : https://github.com/ace-step/ACE-Step-1.5
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866
#   Fichero origen  : acestep/core/generation/handler/generate_music_decode.py
#                     (`VaeDecodeStateMixin._decode_generate_music_pred_latents`)
#   SHA-256 origen  : 5ebe4dfd65635a687a5692d37ab377ab959170e764fbedf54d6e35711cc40416
#   blob SHA-1 git  : b7330503c1c8277cdb72281c14ed6b711be2414c  (10.402 bytes)
#                     verificado contra la atestacion de la API de GitHub.
#   Copiado el      : 2026-09-02
#   Licencia        : MIT — "Copyright (c) 2026 ACEStep". El fichero origen no
#                     lleva cabecera de licencia propia; la que aplica es la del
#                     LICENSE de la raiz del repositorio (blob SHA-1
#                     600451d484a555c1273baa2602f32a37fdd0d0ab, 1.064 bytes),
#                     cuya copia esta en
#                     D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt
#
# ESTE FICHERO HA SIDO MODIFICADO respecto del original. Cada cambio va marcado
# con un comentario "MODIFICADO respecto a upstream: que y por que".
# ---------------------------------------------------------------------------
"""Puente entre los latentes de la difusion y el decoder del VAE.

Que es esto, y que NO es
------------------------
**No** es una implementacion del VAE. El decoder Oobleck ya esta vendorizado,
verificado en la GPU y medido, en el directorio padre:

    apps/runner/adapters/ace_step/vendor/oobleck_decoder.py

Este modulo se limita a lo que hace upstream **alrededor** de la llamada al VAE
en `_decode_generate_music_pred_latents`: transponer los latentes de la
orientacion del DiT `[B, T, C]` a la del VAE `[B, C, T]`, ajustar el dtype al
del decoder y delegar. Dos implementaciones del mismo decoder serian una deuda,
no una red de seguridad, asi que aqui se **importa** el que ya existe.

Lo que aporta el decoder importado (medido en la GPU objetivo, GTX 1070 8 GB):
decode por ventanas de 256 tramas latentes con solape 48 y guarda 16, crossfade
lineal en las costuras, `Snake1d` y la conv1d final en fp32, y un guardarrail de
VRAM con `mem_get_info` **antes** de asignar. El decode monolitico de 180 s no
cabe en 8 GB (techo medido ~40-46 s), asi que el troceado no es una optimizacion:
es la unica forma de que la pista salga.

Que NO esta aqui
----------------
El post-proceso de audio (normalizacion de loudness EBU R128, resample, FLAC/MP3)
es `T-19`/`T-45`, no la Fase 0. La conversion a PCM de 16 bit que espera
`RenderedAudio` del adapter la hace el shim, que es quien conoce ese contrato.
Tampoco esta `latent_shift`/`latent_rescale` de upstream: son perillas de
depuracion cuyos valores neutros (`0.0` y `1.0`) hacen la operacion identidad.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import torch

# MODIFICADO respecto a upstream: upstream resuelve el VAE por `self.vae`, un
# atributo del manejador `AceStepHandler` (que arrastra Gradio, loguru, la API
# HTTP y el gestor de LoRA). Aqui el decoder llega como argumento o se importa
# del modulo hermano ya vendorizado. La cadena de tres intentos cubre las tres
# formas en que este paquete puede acabar importado, sin tocar `sys.path`:
#   1. como `vendor.pipeline.decode`  (paquete de espacio de nombres `vendor/`),
#   2. como `pipeline.decode`         (con `vendor/` en `sys.path`, que es lo que
#                                      hace el shim),
#   3. como modulo suelto             (fichero cargado por ruta).
try:  # pragma: no cover - depende de como se importe el paquete
    from ..oobleck_decoder import (
        ErrorDecoderVae,
        OobleckDecoder,
        cargar_decoder,
    )
except ImportError:  # pragma: no cover
    try:
        from oobleck_decoder import (  # type: ignore[no-redef]
            ErrorDecoderVae,
            OobleckDecoder,
            cargar_decoder,
        )
    except ImportError as _exc:  # pragma: no cover
        raise ImportError(
            "No se encuentra 'oobleck_decoder'. Es el decoder del VAE vendorizado "
            "en el directorio PADRE de este paquete "
            "(adapters/ace_step/vendor/oobleck_decoder.py). Para importarlo, o bien "
            "se importa este paquete como 'vendor.pipeline', o bien se anade "
            "'.../adapters/ace_step/vendor' a sys.path. No se duplica aqui a "
            "proposito: ya esta verificado en la GPU."
        ) from _exc

__all__ = [
    "ErrorDecoderVae",
    "OobleckDecoder",
    "cargar_decoder",
    "decodificar_latentes",
]


def decodificar_latentes(
    *,
    decoder: Any,
    target_latents: torch.Tensor,
    on_step: Callable[[int, int], None] | None = None,
    **opciones_de_troceado: Any,
) -> torch.Tensor:
    """Convierte los latentes de la difusion en forma de onda.

    Args:
        decoder: `OobleckDecoder` ya cargado con `cargar_decoder(state_dict, ...)`.
        target_latents: `[B, T, 64]` tal como los devuelve
            `diffusion.generar_latentes_text2music` (orientacion del DiT).
        on_step: `on_step(ventana_hecha, total_ventanas)`, invocado al terminar
            cada ventana del decode. Es el segundo punto de control del
            presupuesto de GPU (**D-17**): si levanta una excepcion se deja
            propagar, **nunca** se captura.
        **opciones_de_troceado: se pasan tal cual a `decodificar_por_trozos`
            (`ventana`, `solape`, `guarda`, `salida_dispositivo`). Los valores
            por defecto son los medidos en la GPU objetivo; no se tocan salvo
            motivo.

    Returns:
        `[B, 2, T*1920]` en fp32 y en CPU (48 kHz).

    Raises:
        ValueError: si `target_latents` no tiene la forma esperada.
        ErrorDecoderVae / VramInsuficiente: las que levante el decoder.

    MODIFICADO respecto a upstream, tres cosas:

    1. **Se delega el troceado en el decoder vendorizado.** Upstream elige entre
       `self.vae.decode()` monolitico y `self.tiled_decode()` segun una politica
       (`_get_auto_decode_chunk_size`, `_should_offload_wav_to_cpu`) que consulta
       VRAM libre, plataforma y variables de entorno de su CLI. Aqui **siempre**
       se trocea: en la GPU objetivo el decode monolitico de 180 s no cabe, asi
       que ofrecer la eleccion solo serviria para elegir mal.
    2. **No hay caminos de MLX, MPS ni de reubicacion del VAE a CPU.** Upstream
       los necesita porque soporta macOS y GPUs de 4 GB; en esta imagen no hay
       ninguno de esos backends y las ramas serian codigo muerto no ejercitado.
    3. **`latent_shift` / `latent_rescale` suprimidos.** Ver el docstring del
       modulo: en sus valores neutros son la identidad.
    """
    if target_latents.dim() != 3:
        raise ValueError(
            "Los latentes deben venir como [B, T, C] desde la difusion; se "
            f"recibio {tuple(target_latents.shape)}."
        )

    # Upstream: `pred_latents.transpose(1, 2).contiguous().to(self.vae.dtype)`.
    # El `.contiguous()` no es cosmetico: sin el, la conv1d del decoder recibe un
    # tensor con zancadas traspuestas y copia por dentro en cada ventana.
    try:
        dtype_decoder = next(decoder.parameters()).dtype
    except StopIteration:  # pragma: no cover - un decoder sin parametros no existe
        dtype_decoder = target_latents.dtype
    latente = target_latents.transpose(1, 2).contiguous().to(dtype_decoder)

    with torch.inference_mode():
        return decoder.decodificar_por_trozos(
            latente,
            al_avanzar=on_step,
            **opciones_de_troceado,
        )
