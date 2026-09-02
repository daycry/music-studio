# ---------------------------------------------------------------------------
# CODIGO VENDORIZADO — obra derivada de ACE-Step 1.5 (licencia MIT).
#
#   Origen          : https://github.com/ace-step/ACE-Step-1.5
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866
#   Ficheros origen : acestep/core/generation/handler/conditioning_batch.py
#                       (_prepare_batch)
#                       SHA-256    5bc46879830c5e35a48e7ef4a18ca41b4c3f30f7887928b31cea3cf259e82958
#                       blob SHA-1 9a4115adfc6c4fb6caa7e8072adb2ad0090197d9  (6.868 bytes)
#                     acestep/core/generation/handler/conditioning_target.py
#                       (_get_silence_latent_slice, _prepare_target_latents_and_wavs)
#                       SHA-256    472b302837800f54972b5b5a3d6374b7855ee3eac9e05762757fcb41d5455068
#                       blob SHA-1 4446b2897e818c8f3ac55b1b152035a41720a6aa  (8.663 bytes)
#                     acestep/core/generation/handler/conditioning_masks.py
#                       (_build_chunk_masks_and_src_latents)
#                       SHA-256    5d9c1fdb249931794af76db83166347be0e8a081f958338c9a7963131e87a365
#                       blob SHA-1 7973c6a4285af2f072506d3673e0edff547d24ac  (4.738 bytes)
#                     acestep/core/generation/handler/conditioning_text.py
#                       (_prepare_text_conditioning_inputs)
#                       SHA-256    0313ef5fc5ade1baa5a806f3748e5c853961768d057045e040fcb28a33a153b6
#                       blob SHA-1 5641afdb921d4393aa6f3c842e238a3a8c141543  (9.177 bytes)
#                     acestep/core/generation/handler/conditioning_embed.py
#                       (infer_refer_latent, infer_text_embeddings,
#                        infer_lyric_embeddings, preprocess_batch)
#                       SHA-256    45e80702219496edcef5712fa8403583c61f0df128833b9657d0d129d035a3f2
#                       blob SHA-1 ef9e4a572233ce3646782f8cd397c1ae080e0121  (6.741 bytes)
#                     acestep/core/generation/handler/task_utils.py
#                       (create_target_wavs)
#                       SHA-256    a5c90c6af54d1eb207cbf79db39535e115361542cb37735ed4359287bd257a66
#                       blob SHA-1 e39b09e16bb6de0cf3f028300df40fa89745923b  (5.568 bytes)
#                     Los seis blob SHA-1 estan verificados contra la atestacion
#                     de la API de GitHub para esas rutas en ese commit.
#   Ademas deriva de: AceStepConditionGenerationModel.prepare_condition, en
#                     apps/runner/adapters/ace_step/vendor/modeling_acestep_v15_turbo.py
#                     (revision HuggingFace ACE-Step/Ace-Step1.5
#                     19671f406d603126926c1b7e2adc169acbcade22, SHA-256
#                     c1ab0dd547124fee7ada449b2b86eae8201dc7d15889932643bbb67e3c982444).
#                     Ese fichero lleva su propia cabecera Apache-2.0, que se
#                     reproduce verbatim en scheduler.py de este directorio.
#   Copiado el      : 2026-09-02
#   Licencia        : MIT — "Copyright (c) 2026 ACEStep". Ninguno de los seis
#                     ficheros origen de GitHub lleva cabecera de licencia
#                     propia; la que aplica es la del LICENSE de la raiz (blob
#                     SHA-1 600451d484a555c1273baa2602f32a37fdd0d0ab, 1.064
#                     bytes), copiado en
#                     D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt
#
# ESTE FICHERO HA SIDO MODIFICADO respecto de los originales. Cada cambio va
# marcado con un comentario "MODIFICADO respecto a upstream: que y por que".
# ---------------------------------------------------------------------------
"""Preparacion del condicionamiento de `text2music` para ACE-Step 1.5 turbo.

Que produce
-----------
Los tres tensores que el bucle de difusion necesita y nada mas:

* `encoder_hidden_states` / `encoder_attention_mask`: la secuencia empaquetada de
  letra + timbre + estilo que consume la atencion cruzada del DiT.
* `context_latents`: `[src_latents | chunk_masks]` concatenados por el eje de
  canal, de donde el muestreador saca ademas la forma del ruido inicial (el DiT
  lo parte por la mitad: `context_latents.shape[-1] // 2 == 64`).

Camino de `text2music` puro
---------------------------
En `text2music` **no hay audio de entrada**: ni pista objetivo, ni audio de
referencia, ni codigos previos. Upstream llega a este caso pasando por todo el
aparato de `cover`/`repaint` y quedandose en la rama trivial de cada rama. Aqui
se recorre solo esa rama trivial, que es exactamente:

* `target_wavs` = silencio estereo de la duracion pedida -> `is_silence()` cierto
  -> `target_latents` = recorte del latente de silencio pre-calculado. **El
  codificador del VAE no interviene**, que es la razon por la que nuestro
  artefacto de pesos no lo incluye.
* `chunk_masks` = todo a 1 (se genera la pista entera), `spans` = ("full", 0, T).
* `src_latents` = latente de silencio **si no hay plan**. Si el planificador de
  5 Hz esta activo, `lm_hints_25Hz` ocupa su lugar: es la rama que upstream
  selecciona con `is_covers > 0`, y `is_covers` significa «hay plan semantico»,
  no «esto es una version» (ver el bloque de comentario del punto de sustitucion).
* `refer_audios` = un tensor de ceros -> el codificador de timbre recibe los
  primeros 750 fotogramas del latente de silencio.

Que NO esta aqui
----------------
Cover, repaint, lego, extract, complete, LoRA, `source_repaint_latents`, la rama
sin cover del CFG (`audio_cover_strength < 1.0`), el formato SFT-lego de captions
y el lote (B>1). Si esta el equivalente de `precomputed_lm_hints_25Hz`: el
argumento `lm_hints_25Hz`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch

try:  # pragma: no cover - depende de como se importe el paquete
    from .constants import (
        DEFAULT_DIT_INSTRUCTION,
        LATENT_HOP,
        MAX_LYRIC_TOKENS,
        MAX_TEXT_TOKENS,
        MIN_LATENT_LENGTH,
        REFER_AUDIO_LATENT_FRAMES,
        SAMPLE_RATE,
        SFT_GEN_PROMPT,
        construir_meta_dict,
        formatear_instruccion,
        formatear_letra,
        normalizar_meta,
    )
except ImportError:  # pragma: no cover
    from constants import (  # type: ignore[no-redef]
        DEFAULT_DIT_INSTRUCTION,
        LATENT_HOP,
        MAX_LYRIC_TOKENS,
        MAX_TEXT_TOKENS,
        MIN_LATENT_LENGTH,
        REFER_AUDIO_LATENT_FRAMES,
        SAMPLE_RATE,
        SFT_GEN_PROMPT,
        construir_meta_dict,
        formatear_instruccion,
        formatear_letra,
        normalizar_meta,
    )

__all__ = [
    "CondicionamientoText2Music",
    "longitud_latente",
    "normalizar_latente_de_silencio",
    "preparar_condicionamiento_text2music",
]


@dataclass(frozen=True)
class CondicionamientoText2Music:
    """Salida de `preparar_condicionamiento_text2music`.

    `prompt_texto` y `letra_texto` viajan con los tensores para que quede
    registrado **el texto exacto** que vio el modelo, no el que pidio el usuario:
    es lo que hace reproducible un informe de escucha de G1 cuando alguien
    pregunta por que dos pistas con el mismo prompt suenan distinto.
    """

    encoder_hidden_states: torch.Tensor
    encoder_attention_mask: torch.Tensor
    context_latents: torch.Tensor
    attention_mask: torch.Tensor
    latent_length: int
    duracion_s: float
    prompt_texto: str
    letra_texto: str


# --------------------------------------------------------------------------- #
# Latente de silencio y longitudes
# --------------------------------------------------------------------------- #

def normalizar_latente_de_silencio(
    silence_latent: torch.Tensor,
    *,
    device: torch.device | str,
    dtype: torch.dtype,
) -> torch.Tensor:
    """Devuelve el latente de silencio como `[1, T, C]` en el device y dtype dados.

    Upstream (`init_service_loader.py`, linea 214) lo carga asi:

        self.silence_latent = torch.load(ruta, weights_only=True).transpose(1, 2)

    es decir, el fichero `silence_latent.pt` esta en orientacion `[1, C, T]` y
    upstream lo **transpone** al cargarlo. Todo el resto del codigo asume ya
    `[1, T, C]` (`self.silence_latent[0, :length, :]`).

    MODIFICADO respecto a upstream: aqui la transposicion se decide por la forma
    y no por el punto de carga. Motivo: nuestro artefacto guarda el tensor tal
    cual venia (`aux.silence_latent`, F32 `[1, 64, 15000]`), asi que la factoria
    del shim lo entrega en la orientacion cruda; hacer la transposicion aqui, y
    no en el shim, evita que dos rutas de carga distintas discrepen. Se detecta
    por el eje de 64 canales, que es `audio_acoustic_hidden_dim` y no cambia.
    """
    if silence_latent.dim() == 2:
        silence_latent = silence_latent.unsqueeze(0)
    if silence_latent.dim() != 3:
        raise ValueError(
            "El latente de silencio debe tener forma [1, T, C] o [1, C, T]; "
            f"se recibio {tuple(silence_latent.shape)}."
        )
    if silence_latent.shape[1] == 64 and silence_latent.shape[2] != 64:
        # Orientacion cruda [1, C, T]: hay que transponer, como hace upstream.
        silence_latent = silence_latent.transpose(1, 2)
    elif silence_latent.shape[2] != 64:
        raise ValueError(
            "El latente de silencio no tiene 64 canales en ninguno de sus dos "
            f"ejes finales: {tuple(silence_latent.shape)}. No es el tensor "
            "'aux.silence_latent' de este artefacto."
        )
    return silence_latent.to(device=device, dtype=dtype).contiguous()


def longitud_latente(duracion_s: float) -> tuple[int, float]:
    """Longitud de la secuencia latente (en fotogramas) para una duracion.

    Reproduce la cadena de upstream sin materializar el audio de silencio:

    1. `task_utils.create_target_wavs`: `duracion = max(0.1, round(d, 1))`,
       `frames = int(duracion * 48000)`.
    2. `conditioning_target._prepare_target_latents_and_wavs`:
       `latentes = frames // 1920` y despues `max(128, latentes)`.

    Returns:
        `(fotogramas_latentes, duracion_redondeada_s)`.

    MODIFICADO respecto a upstream: upstream crea de verdad un tensor de ceros
    de `[2, duracion*48000]` solo para dividir su longitud entre 1920 y tirarlo.
    A 300 s son 115 MB de RAM que no aportan nada. Aqui se calcula el mismo
    entero con aritmetica. El resultado es identico por construccion: se
    conservan el mismo `max(0.1, round(., 1))`, el mismo `int()` y la misma
    division entera.
    """
    duracion = max(0.1, round(float(duracion_s), 1))
    frames = int(duracion * SAMPLE_RATE)
    latentes = max(MIN_LATENT_LENGTH, frames // LATENT_HOP)
    return latentes, duracion


def _recorte_de_silencio(silence_latent: torch.Tensor, longitud: int) -> torch.Tensor:
    """Recorte `[longitud, C]` del latente de silencio, repitiendolo si hace falta.

    Upstream: `conditioning_target._get_silence_latent_slice`, verbatim salvo por
    recibir el tensor como argumento en vez de leerlo de `self`.
    """
    disponible = silence_latent.shape[1]
    if longitud <= disponible:
        return silence_latent[0, :longitud, :]
    repeticiones = (longitud + disponible - 1) // disponible  # division techo
    repetido = silence_latent[0].repeat(repeticiones, 1)
    return repetido[:longitud, :]


# --------------------------------------------------------------------------- #
# Texto: prompt, letra y embeddings
# --------------------------------------------------------------------------- #

def _dispositivo_de(modulo: Any, *, por_defecto: torch.device | str) -> torch.device:
    """Dispositivo donde viven los parametros de un modulo.

    MODIFICADO respecto a upstream: no existe en upstream, que asume que todo
    esta en `self.device` porque su gestor de descarga mueve los modulos justo
    antes de usarlos. Ver el comentario del punto de llamada.
    """
    try:
        return next(modulo.parameters()).device
    except (AttributeError, StopIteration):
        return torch.device(por_defecto)


def _tokenizar(tokenizer: Any, texto: str, max_length: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Tokeniza un texto y devuelve `(input_ids [1, L], attention_mask [1, L] bool)`.

    Upstream: `conditioning_text._prepare_text_conditioning_inputs`, con los
    mismos `padding="longest"`, `truncation=True` y `max_length`.

    MODIFICADO respecto a upstream (dos cosas):
    1. Se accede por clave (`salida["input_ids"]`) y no por atributo
       (`salida.input_ids`). `BatchEncoding` soporta ambos; un `dict` plano
       —que es lo que devuelve un tokenizador envuelto a mano— solo el primero.
    2. Se elimina el relleno por lote (`_pad_sequences` de `prompt_utils.py`).
       Con B=1 y `padding="longest"` no hay nada que rellenar: la funcion
       upstream calcularia `max_length = len(unica_secuencia)` y haria un `pad`
       de cero elementos.
    """
    salida = tokenizer(
        texto,
        padding="longest",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    input_ids = salida["input_ids"]
    attention_mask = salida["attention_mask"].bool()
    if input_ids.dim() == 1:  # tokenizadores que no anaden el eje de lote
        input_ids = input_ids.unsqueeze(0)
        attention_mask = attention_mask.unsqueeze(0)
    return input_ids, attention_mask


def _construir_prompt(
    *,
    style_prompt: str,
    duracion_s: float,
    bpm: int | str | None,
    keyscale: str | None,
    timesignature: str | None,
    instruccion: str,
) -> str:
    """Monta el prompt del codificador de texto.

    Upstream: `conditioning_text._prepare_text_conditioning_inputs` en su rama
    NO lego (`is_lego_sft` falso, que es siempre en el turbo), combinada con
    `batch_prep.prepare_batch_data` (que es quien mete la duracion en los metas).
    """
    meta = construir_meta_dict(
        bpm=bpm,
        keyscale=keyscale,
        timesignature=timesignature,
        duration=duracion_s,
    )
    return SFT_GEN_PROMPT.format(
        formatear_instruccion(instruccion),
        style_prompt,
        normalizar_meta(meta),
    )


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

def preparar_condicionamiento_text2music(
    *,
    model: Any,
    text_encoder: Any,
    text_tokenizer: Any,
    silence_latent: torch.Tensor,
    style_prompt: str,
    lyrics: str | None = None,
    duracion_s: float,
    device: torch.device | str,
    dtype: torch.dtype,
    vocal_language: str = "en",
    bpm: int | str | None = None,
    keyscale: str | None = None,
    timesignature: str | None = None,
    instruccion: str = DEFAULT_DIT_INSTRUCTION,
    lm_hints_25Hz: torch.Tensor | None = None,
) -> CondicionamientoText2Music:
    """Prepara todo el condicionamiento de una generacion `text2music`.

    Args:
        model: `AceStepConditionGenerationModel` ya instanciado y con pesos.
            Solo se usa su submodulo `.encoder`.
        text_encoder: `Qwen3Model` (Qwen3-Embedding-0.6B) ya instanciado.
        text_tokenizer: tokenizador rapido de ese mismo modelo.
        silence_latent: `aux.silence_latent` del artefacto, en cualquiera de las
            dos orientaciones (ver `normalizar_latente_de_silencio`).
        style_prompt: descripcion del estilo (el `caption` de upstream).
        lyrics: letra. `None` o cadena vacia generan una pista instrumental, que
            es como upstream trata la ausencia de letra (`lyrics = [""]`).
        duracion_s: duracion pedida en segundos.
        device / dtype: donde y en que precision viven los tensores.
        vocal_language: codigo de idioma de la letra para la cabecera
            `# Languages`.
        bpm / keyscale / timesignature: metadatos opcionales del prompt.
        instruccion: instruccion del DiT. El unico valor con sentido en
            `text2music` es el de por defecto.
        lm_hints_25Hz: salida del planificador de 5 Hz ya detokenizada,
            `[1, T', 64]`. Si se da, **sustituye** al latente de silencio como
            `src_latents`. Si es `None`, el camino es el de siempre. Ver el bloque
            «Planificador» mas abajo.

    Returns:
        `CondicionamientoText2Music` listo para `diffusion.generar_latentes_text2music`.
    """
    latent_length, duracion = longitud_latente(duracion_s)
    silencio = normalizar_latente_de_silencio(silence_latent, device=device, dtype=dtype)

    # -- Latentes de origen y mascaras ------------------------------------- #
    # `conditioning_target`: sin audio de entrada, el latente objetivo ES el
    # recorte del latente de silencio. `conditioning_masks`: sin repintado,
    # `chunk_mask` es todo unos, `is_cover` falso y `src_latents` el silencio.
    src_latents = _recorte_de_silencio(silencio, latent_length).unsqueeze(0)  # [1, T, 64]
    canales = src_latents.shape[-1]

    # -- Planificador de 5 Hz ---------------------------------------------- #
    # MODIFICADO respecto a upstream: se admiten hints precalculados.
    #
    # Upstream escribe esto en `prepare_condition` (modeling, linea 1646):
    #
    #     lm_hints_25Hz = precomputed_lm_hints_25Hz[:, :src_latents.shape[1], :]
    #     src_latents = torch.where(is_covers.unsqueeze(-1).unsqueeze(-1) > 0,
    #                               lm_hints_25Hz, src_latents)
    #
    # OJO A LA SEMANTICA DE `is_covers`, que es lo mas facil de leer al reves:
    # los hints entran cuando `is_covers` es **cierto**, y `is_covers` NO
    # significa «esto es una version de otra cancion». Upstream lo calcula en
    # `conditioning_masks.py` como `is_cover = (task_type == "cover") or
    # has_code_hint`, es decir: **cierto en cuanto hay codigos**. Traducido:
    # `is_covers` quiere decir «hay plan semantico». Pasar los codigos con
    # `is_covers=False` los descarta en silencio —mismo audio, sin error ni
    # aviso—, que es la razon de que el planificador pudiera estar desconectado
    # sin que nada chillara.
    #
    # Con B=1 ese `torch.where` es una eleccion entre dos tensores completos, asi
    # que aqui se expresa como lo que es: si hay plan, `src_latents` ES el plan.
    # No se propaga ninguna bandera `is_covers` porque en este modulo no hay lote
    # que enmascarar, y una bandera que solo puede valer «todo si» o «todo no»
    # es una trampa esperando a que alguien la ponga al reves.
    if lm_hints_25Hz is not None:
        if lm_hints_25Hz.dim() != 3 or lm_hints_25Hz.shape[0] != 1:
            raise ValueError(
                f"`lm_hints_25Hz` deberia ser [1, T', 64] y llego "
                f"{tuple(lm_hints_25Hz.shape)}."
            )
        if lm_hints_25Hz.shape[-1] != canales:
            raise ValueError(
                f"`lm_hints_25Hz` trae {lm_hints_25Hz.shape[-1]} canales y el latente "
                f"acustico tiene {canales}."
            )
        if lm_hints_25Hz.shape[1] < latent_length:
            # Upstream solo recorta, nunca rellena, porque su tokenizador anade
            # relleno y siempre le sobra. Si aqui faltan fotogramas, el final de
            # la pista se quedaria sin plan: es un error de quien pidio los
            # codigos, no algo que se pueda apanar sin mentir.
            raise ValueError(
                f"`lm_hints_25Hz` cubre {lm_hints_25Hz.shape[1]} fotogramas y hacen falta "
                f"{latent_length}. Pide al planificador `ceil(T/5)` codigos."
            )
        src_latents = lm_hints_25Hz[:, :latent_length, :].to(device=device, dtype=dtype)

    # `conditioning_target`: `latent_masks` = unos hasta la longitud real. Con
    # B=1 y sin relleno, es todo unos.
    attention_mask = torch.ones(1, latent_length, dtype=torch.long, device=device)

    # `conditioning_masks` construye la mascara como `[1, T]` booleana y
    # `conditioning_embed.preprocess_batch` la expande a `[1, T, 64]`.
    chunk_masks = torch.ones(1, latent_length, dtype=torch.bool, device=device)
    chunk_masks = chunk_masks.unsqueeze(-1).repeat(1, 1, canales)

    # -- Audio de referencia (timbre) --------------------------------------- #
    # `conditioning_embed.infer_refer_latent`, rama de audio de referencia todo a
    # cero: 750 fotogramas del latente de silencio y un solo elemento en el lote.
    refer_audio_acoustic_hidden_states_packed = silencio[:, :REFER_AUDIO_LATENT_FRAMES, :]
    refer_audio_order_mask = torch.tensor([0], dtype=torch.long, device=device)

    # -- Texto --------------------------------------------------------------- #
    prompt_texto = _construir_prompt(
        style_prompt=style_prompt,
        duracion_s=duracion,
        bpm=bpm,
        keyscale=keyscale,
        timesignature=timesignature,
        instruccion=instruccion,
    )
    letra_texto = formatear_letra(lyrics or "", vocal_language)

    text_ids, text_attention_mask = _tokenizar(text_tokenizer, prompt_texto, MAX_TEXT_TOKENS)
    lyric_ids, lyric_attention_mask = _tokenizar(text_tokenizer, letra_texto, MAX_LYRIC_TOKENS)

    # MODIFICADO respecto a upstream: los identificadores de token van al
    # dispositivo del **codificador de texto**, no al del pipeline, y los estados
    # ocultos vuelven despues al del pipeline. Upstream puede permitirse mandarlo
    # todo a `self.device` porque su gestor mueve el codificador de texto a la GPU
    # justo antes (`_load_model_context("text_encoder")`). Aqui el codificador
    # puede quedarse en CPU: en la GPU objetivo (8 GB) el DiT y el Qwen3 no caben
    # a la vez, asi que la descarga la decide el shim y este modulo tiene que
    # funcionar con las dos piezas en dispositivos distintos.
    dispositivo_texto = _dispositivo_de(text_encoder, por_defecto=device)
    text_ids = text_ids.to(dispositivo_texto)
    lyric_ids = lyric_ids.to(dispositivo_texto)
    text_attention_mask = text_attention_mask.to(device)
    lyric_attention_mask = lyric_attention_mask.to(device)

    with torch.inference_mode():
        # `conditioning_embed.infer_text_embeddings`.
        #
        # MODIFICADO respecto a upstream: upstream llama
        # `self.text_encoder(input_ids=..., lyric_attention_mask=None)`. Ese
        # `lyric_attention_mask` NO figura en la firma de `Qwen3Model.forward`
        # (comprobado en la imagen: transformers 5.16.1 no lo declara); se cuela
        # por `**kwargs`, hoy se tolera —tambien comprobado, la llamada con el
        # kwarg no falla— y no lo lee nadie. Se elimina porque su valor es None
        # y porque depender de que una version futura siga tolerando un kwarg
        # desconocido es una bomba de relojeria por cero beneficio.
        text_hidden_states = text_encoder(input_ids=text_ids).last_hidden_state
        # `conditioning_embed.infer_lyric_embeddings`: la letra NO pasa por el
        # transformer, solo por la tabla de embeddings. El codificador de letra
        # del propio ACE-Step (`model.encoder.lyric_encoder`) es quien la procesa.
        lyric_hidden_states = text_encoder.embed_tokens(lyric_ids)

    # `conditioning_batch._prepare_batch` convierte al dtype del pipeline todo
    # tensor en coma flotante del lote. Al `.to(dtype)` de upstream se le suma
    # aqui el `device`, por lo mismo que el bloque anterior: el codificador de
    # texto puede haber estado en CPU. `.clone()` porque estos tensores salen de
    # un bloque `inference_mode` y el DiT los guardara en su cache de atencion
    # cruzada durante los ocho pasos; un tensor de inferencia ahi dentro es una
    # trampa que solo salta mas tarde y lejos.
    text_hidden_states = text_hidden_states.to(device=device, dtype=dtype).clone()
    lyric_hidden_states = lyric_hidden_states.to(device=device, dtype=dtype).clone()

    # -- Condicion (parte de `prepare_condition` del modelo) ----------------- #
    with torch.no_grad():
        encoder_hidden_states, encoder_attention_mask = model.encoder(
            text_hidden_states=text_hidden_states,
            text_attention_mask=text_attention_mask,
            lyric_hidden_states=lyric_hidden_states,
            lyric_attention_mask=lyric_attention_mask,
            refer_audio_acoustic_hidden_states_packed=refer_audio_acoustic_hidden_states_packed,
            refer_audio_order_mask=refer_audio_order_mask,
        )

    # MODIFICADO respecto a upstream: no se llama a `model.tokenize()`.
    # `prepare_condition` la ejecuta SIEMPRE para derivar unos hints del propio
    # `hidden_states` —que en `text2music` es el latente de silencio, o sea, un
    # plan de la nada— y luego los descarta o no segun `is_covers`. Aqui los
    # hints, si los hay, llegan ya hechos por `lm_hints_25Hz` (el bloque de mas
    # arriba), y si no los hay no se calcula nada: la pasada por el tokenizador
    # de audio (32 tensores) mas el detokenizador (28) se ahorra entera.
    context_latents = torch.cat([src_latents, chunk_masks.to(dtype)], dim=-1)

    return CondicionamientoText2Music(
        encoder_hidden_states=encoder_hidden_states,
        encoder_attention_mask=encoder_attention_mask,
        context_latents=context_latents,
        attention_mask=attention_mask,
        latent_length=latent_length,
        duracion_s=duracion,
        prompt_texto=prompt_texto,
        letra_texto=letra_texto,
    )
