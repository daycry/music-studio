# ---------------------------------------------------------------------------
# CODIGO VENDORIZADO — obra derivada de ACE-Step 1.5 (licencia MIT).
#
#   Origen          : https://github.com/ace-step/ACE-Step-1.5
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866
#   Ficheros origen : acestep/constants.py
#                       SHA-256    7b8d4ce49649c819d1b3be87a434be2d90768308768d4620639328f906209b22
#                       blob SHA-1 9e6df5323d7e0a2f43237a63910d55ebbf2b39e8  (8.333 bytes)
#                     acestep/core/generation/handler/prompt_utils.py  (PromptMixin)
#                       SHA-256    242835ae29cc1bfcc40aadf1c46d8156230349d6e2f05436b2c85b3491484fae
#                       blob SHA-1 f51a49c622f60b048c96e27aa48292321aeade63  (6.826 bytes)
#                     acestep/core/generation/handler/metadata_utils.py (MetadataMixin)
#                       SHA-256    b8485fe9c3a8ffdf0ee0147df68366770abfe6b68e6cd286dd4722d9379cdc5b
#                       blob SHA-1 2dee45ea724c80f899ab7aa224473efc4c406844  (3.062 bytes)
#                     Los tres blob SHA-1 estan verificados contra la atestacion
#                     de la API de GitHub para esas rutas en ese commit.
#   Copiado el      : 2026-09-02
#   Licencia        : MIT — "Copyright (c) 2026 ACEStep". Ninguno de los tres
#                     ficheros origen lleva cabecera de licencia propia; la que
#                     aplica es la del LICENSE de la raiz del repositorio (blob
#                     SHA-1 600451d484a555c1273baa2602f32a37fdd0d0ab, 1.064
#                     bytes), copiado en
#                     D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt
#
# ESTE FICHERO HA SIDO MODIFICADO respecto de los originales. Cada cambio va
# marcado con un comentario "MODIFICADO respecto a upstream: que y por que".
# ---------------------------------------------------------------------------
"""Constantes y formateo de texto del condicionamiento de ACE-Step 1.5.

Contiene lo unico que `text2music` necesita de los tres ficheros de origen: la
plantilla del prompt del codificador de texto, la instruccion por defecto y el
formateo de metadatos y letra. Todo lo demas de esos ficheros (idiomas validos,
tonalidades, tareas `cover`/`repaint`/`lego`, memoria de GPU, interruptores de
depuracion, parseo de captions en formato SFT) se ha dejado fuera a proposito.

Estos strings **no son cosmeticos**: forman parte del contrato con los pesos.
El modelo se entreno viendo exactamente esta plantilla, asi que cambiar un salto
de linea cambia la distribucion de entrada del codificador de texto.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "DEFAULT_DIT_INSTRUCTION",
    "SFT_GEN_PROMPT",
    "SAMPLE_RATE",
    "LATENT_HOP",
    "LATENT_HZ",
    "MAX_TEXT_TOKENS",
    "MAX_LYRIC_TOKENS",
    "REFER_AUDIO_LATENT_FRAMES",
    "MIN_LATENT_LENGTH",
    "formatear_instruccion",
    "formatear_letra",
    "meta_por_defecto",
    "meta_dict_a_texto",
    "normalizar_meta",
    "construir_meta_dict",
]


# --------------------------------------------------------------------------- #
# Plantillas de prompt (acestep/constants.py, verbatim)
# --------------------------------------------------------------------------- #

#: Instruccion por defecto del DiT para `text2music`.
#: Upstream: `acestep/constants.py::DEFAULT_DIT_INSTRUCTION`, identica a
#: `TASK_INSTRUCTIONS["text2music"]`.
DEFAULT_DIT_INSTRUCTION = "Fill the audio semantic mask based on the given conditions:"

#: Plantilla del prompt que ve el codificador de texto (Qwen3-Embedding-0.6B).
#: Upstream: `acestep/constants.py::SFT_GEN_PROMPT`, verbatim.
#: Los tres huecos son, por orden: instruccion, caption (nuestro `style_prompt`)
#: y bloque de metadatos.
SFT_GEN_PROMPT = """# Instruction
{}

# Caption
{}

# Metas
{}<|endoftext|>
"""


# --------------------------------------------------------------------------- #
# Constantes numericas del pipeline
# --------------------------------------------------------------------------- #
# MODIFICADO respecto a upstream: estas cinco constantes NO existen como tales en
# upstream, que las repite como numeros magicos por el codigo (`48000` en
# `task_utils.create_target_wavs` y `padding_utils`, `1920` en
# `conditioning_masks` y `conditioning_target`, `750` en
# `conditioning_embed.infer_refer_latent`, `128` en
# `conditioning_target._prepare_target_latents_and_wavs`, `256`/`2048` en
# `conditioning_text._prepare_text_conditioning_inputs`). Se les da nombre aqui
# porque un numero magico repetido en seis sitios es exactamente lo que se
# desincroniza en la primera modificacion; el valor es el mismo.

#: Frecuencia de muestreo nativa del VAE (`aux.config.vae_json::sampling_rate`).
SAMPLE_RATE = 48000

#: Muestras de audio por fotograma latente. Es el producto de los factores de
#: submuestreo del VAE Oobleck (2*4*4*6*10 = 1920).
LATENT_HOP = 1920

#: Fotogramas latentes por segundo: 48000 / 1920 = 25 Hz.
#: OJO al leer las mediciones de T-03: la longitud de secuencia que ve la
#: atencion del DiT es la MITAD de esta, porque `config.patch_size = 2` y
#: `AceStepDiTModel.proj_in` es una `Conv1d(kernel=2, stride=2)`. Por eso 180 s
#: son 4.500 fotogramas latentes aqui y `L = 2.250` en el perfil del DiT. Las
#: longitudes impares las rellena el propio DiT (`F.pad` antes de `proj_in`) y
#: las recorta al salir, asi que este modulo no tiene que alinearlas.
LATENT_HZ = SAMPLE_RATE // LATENT_HOP

#: Longitud minima de la secuencia latente. Upstream la impone con
#: `max(128, max_latent_length)`: por debajo de 128 fotogramas (5,12 s) el
#: troceado por ventanas del DiT no tiene sentido.
MIN_LATENT_LENGTH = 128

#: Tope de tokens del prompt de estilo (upstream `max_length=256`).
MAX_TEXT_TOKENS = 256

#: Tope de tokens de la letra (upstream `max_length=2048`).
MAX_LYRIC_TOKENS = 2048

#: Fotogramas latentes de "audio de referencia" que consume el codificador de
#: timbre. En `text2music` no hay audio de referencia y upstream le pasa los
#: primeros 750 fotogramas (30 s) del latente de silencio.
REFER_AUDIO_LATENT_FRAMES = 750


# --------------------------------------------------------------------------- #
# Formateo de prompt (prompt_utils.py::PromptMixin)
# --------------------------------------------------------------------------- #
# MODIFICADO respecto a upstream: eran metodos de un mixin (`self` sin usar) y
# aqui son funciones de modulo. Motivo: nuestro pipeline no construye la clase
# `AceStepHandler` (arrastra Gradio, loguru, la API HTTP y el gestor de LoRA);
# el cuerpo de cada funcion es identico.


def formatear_instruccion(instruccion: str) -> str:
    """Garantiza que la instruccion termina en dos puntos.

    Upstream: `PromptMixin._format_instruction`.
    """
    if not instruccion.endswith(":"):
        instruccion = instruccion + ":"
    return instruccion


def formatear_letra(letra: str, idioma: str) -> str:
    """Envuelve la letra con su cabecera de idioma.

    Upstream: `PromptMixin._format_lyrics`. La cadena es parte del contrato con
    los pesos: no se toca.
    """
    return f"# Languages\n{idioma}\n\n# Lyric\n{letra}<|endoftext|>"


# --------------------------------------------------------------------------- #
# Formateo de metadatos (metadata_utils.py::MetadataMixin)
# --------------------------------------------------------------------------- #


def meta_por_defecto() -> str:
    """Bloque de metadatos por defecto.

    Upstream: `MetadataMixin._create_default_meta`.
    """
    return (
        "- bpm: N/A\n"
        "- timesignature: N/A\n"
        "- keyscale: N/A\n"
        "- duration: 30 seconds\n"
    )


def meta_dict_a_texto(meta: dict[str, Any]) -> str:
    """Convierte el diccionario de metadatos al bloque de texto del prompt.

    Upstream: `MetadataMixin._dict_to_meta_string`.
    """
    bpm = meta.get("bpm", meta.get("tempo", "N/A"))
    timesignature = meta.get("timesignature", meta.get("time_signature", "N/A"))
    keyscale = meta.get("keyscale", meta.get("key", meta.get("scale", "N/A")))
    duration = meta.get("duration", meta.get("length", 30))

    if isinstance(duration, (int, float)):
        duration = f"{int(duration)} seconds"
    elif not isinstance(duration, str):
        duration = "30 seconds"

    return (
        f"- bpm: {bpm}\n"
        f"- timesignature: {timesignature}\n"
        f"- keyscale: {keyscale}\n"
        f"- duration: {duration}\n"
    )


def normalizar_meta(meta: Any) -> str:
    """Normaliza un metadato (None, texto o diccionario) a su bloque de texto.

    Upstream: `MetadataMixin._parse_metas`, reducido a **un** elemento.

    MODIFICADO respecto a upstream: upstream recibe y devuelve una lista porque
    trabaja por lote; aqui B=1 por contrato (`text2music` del turbo, una pista
    por trabajo), asi que la lista sobra y esconderia un lote no soportado.
    """
    if meta is None:
        return meta_por_defecto()
    if isinstance(meta, str):
        return meta
    if isinstance(meta, dict):
        return meta_dict_a_texto(meta)
    return meta_por_defecto()


def construir_meta_dict(
    bpm: int | str | None = None,
    keyscale: str | None = None,
    timesignature: str | None = None,
    duration: float | None = None,
) -> dict[str, Any]:
    """Construye el diccionario de metadatos con los valores ausentes a `N/A`.

    Upstream: `MetadataMixin._build_metadata_dict`.

    MODIFICADO respecto a upstream: `keyscale` y `timesignature` admiten `None`.
    Upstream llama a `.strip()` sobre ellos sin comprobar, asi que un `None`
    —perfectamente normal cuando el usuario no fija tonalidad ni compas— revienta
    con `AttributeError`. Aqui `None` se trata como ausente, que es lo que la UI
    de upstream garantiza por otra via (rellena "" antes de llamar).
    """
    meta: dict[str, Any] = {}
    meta["bpm"] = bpm if bpm else "N/A"
    meta["keyscale"] = keyscale if keyscale and keyscale.strip() else "N/A"
    if timesignature and timesignature.strip() and timesignature != "N/A":
        meta["timesignature"] = timesignature
    else:
        meta["timesignature"] = "N/A"
    if duration is not None:
        meta["duration"] = f"{int(duration)} seconds"
    return meta
