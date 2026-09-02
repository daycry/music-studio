"""Condicionamiento de texto de ACE-Step 1.5 — de (prompt, letra) a los tensores del DiT.

Que resuelve este fichero
-------------------------
El DiT de ACE-Step no consume texto: consume **estados ocultos de un text
encoder**. Este modulo cubre exactamente ese tramo y nada mas:

    (prompt de estilo, letra)  ->  text_hidden_states   [B, L_text,  1024]
                                   text_attention_mask  [B, L_text]
                                   lyric_hidden_states  [B, L_lyric, 1024]
                                   lyric_attention_mask [B, L_lyric]

Los cuatro tensores son la entrada literal de
`AceStepConditionGenerationModel.prepare_condition()` y de `generate_audio()`
(`vendor/modeling_acestep_v15_turbo.py` L1606-1622 y L1780-1888). Todo lo que
viene despues —proyeccion, encoder de letra, timbre y empaquetado— lo hace el
propio artefacto y se documenta abajo, pero **no** se implementa aqui.

Tanto el tokenizer como los pesos del text encoder viajan DENTRO del artefacto
(`aux.text_tokenizer.*` y `text_encoder.*`): este modulo no abre la red, no
escribe a disco, no usa `from_pretrained` contra el hub y no habilita
`trust_remote_code` ni `auto_map` (CLAUDE.md, invariantes).

Forma exacta que espera el DiT, verificada en el codigo vendorizado
-------------------------------------------------------------------
Cadena completa, con las lineas de `vendor/modeling_acestep_v15_turbo.py`:

1. `AceStepConditionEncoder.forward` (L1523-1551)
   * `text_hidden_states` pasa por `self.text_projector = Linear(text_hidden_dim,
     hidden_size, bias=False)` (L1517) -> **1024 -> 2048**. De ahi que la
     dimension de salida del text encoder tenga que ser 1024 exactos:
     `config.text_hidden_dim = 1024` en `vendor/config.json`, que es justo el
     `hidden_size` de Qwen3-Embedding-0.6B.
   * `lyric_hidden_states` va a `AceStepLyricEncoder(inputs_embeds=...)`, cuyo
     `embed_tokens` es tambien `Linear(text_hidden_dim, hidden_size)` (L587).
     **La letra NO son ids de token: son embeddings del mismo Qwen3.** El
     encoder de letra asegura `input_ids is None` e `inputs_embeds is not None`
     (L615-617), asi que no hay camino alternativo por ids.
   * Empaquetado final: `pack_sequences(lyric, timbre)` y luego
     `pack_sequences(eso, text)` (L1549-1550) -> `encoder_hidden_states`
     `[B, L_lyric + L_timbre + L_text, 2048]` con los tokens validos delante
     (orden estable) y `encoder_attention_mask` `[B, L_enc]` booleana.
2. `AceStepDiTModel.forward` (L1300-1356) aplica
   `condition_embedder = Linear(2048, 2048)` (L1279) sobre esos estados. El
   bench `spikes/dit_forward_bench.py` inyecta exactamente `[1, 210, 2048]`:
   L_enc = 210 es la longitud tipica medida del cross-attention, coherente con
   L_lyric + 1 token de timbre + L_text (el propio `test_forward` de upstream,
   L2004-2009, usa 77 tokens de prompt y 123 de letra).

**Hallazgo que condiciona el diseno**: en `AceStepDiTModel.forward`, L1381-1382,
`encoder_attention_mask` y `attention_mask` se **sobrescriben a None** antes de
construir las mascaras 4D. El DiT descarta las mascaras que recibe y fabrica una
mascara de cross-attention `[B, 1, L_dit, L_enc]` **enteramente visible**
(L1416-1425). Consecuencia practica: todo lo que quede en `encoder_hidden_states`
—incluido el relleno— se atiende. Por eso este modulo trabaja con B=1 y
longitudes exactas: **no genera padding**. La mascara sigue siendo necesaria
aguas arriba (el encoder de letra y `pack_sequences` si la usan), pero no
protege dentro del DiT.

Dtypes del contrato (upstream `test_forward`, L2004-2007): los estados ocultos y
**tambien las mascaras** van en el dtype del modelo, no en bool ni en int64.
`create_4d_mask` hace `.to(torch.bool)` (L114) y `pack_sequences` hace
`argsort`/`sum` sobre la mascara (L155-163), asi que 1.0/0.0 en fp16 es lo
correcto. La suma de `pack_sequences` obliga a un techo: fp16 representa enteros
exactos hasta 2048, de ahi `MAX_TOKENS_CROSS_ATTENTION`.

Despacho por componente (requisito de VRAM)
-------------------------------------------
Los 310 tensores de `text_encoder.*` ocupan **1.136 MiB** en fp16. En la GPU de
referencia de la Fase 0 (GTX 1070, 8.191 MiB totales, ~7.200 libres) esa cifra
no puede quedarse residente durante la difusion: el pico del DiT ya llega a
4.906 MiB a 300 s. Por eso `TextConditioner` mantiene los pesos **en RAM** y
solo los sube a VRAM durante `encode()`, que se ejecuta **una vez por
generacion** y devuelve el modelo a CPU antes de que empiece el bucle de
difusion. Antes de subir nada se comprueba `torch.cuda.mem_get_info()` y se
aborta si no cabe: un OOM de driver deja el caching allocator de PyTorch
corrupto y no es recuperable en proceso, asi que **nunca** se captura.

Atencion en Pascal (sm_61)
--------------------------
Medido en esta GPU: SDPA cae al kernel mem-efficient y es 12,9x mas lento que
eager con softmax en fp32, **en silencio**. `set_attn_implementation("eager")`
devuelve "sdpa" sin avisar. La unica via fiable es asignar
`config._attn_implementation = "eager"` a mano, y este modulo lo comprueba con
un assert sobre una capa concreta. Para L_text ~ 200 el coste absoluto es
pequeno, pero la regla es la misma en todo el runner: nada de degradaciones
silenciosas.

Lo que este modulo NO decide
----------------------------
El **formato** con el que upstream envuelve el prompt y la letra antes de
tokenizar (plantilla de instruccion, etiquetas de seccion, idioma) no esta en el
codigo vendorizado: `vendor/` trae la definicion del modelo, no el pipeline de
inferencia. Aqui se codifica el texto **tal cual**, con la unica adicion del
`<|endoftext|>` que anade el post-procesador del propio tokenizer del artefacto.
Si al cerrar el shim aparece el pipeline upstream y usa otra envoltura, el punto
de cambio es `_preparar_textos()` y solo eso.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import torch

__all__ = [
    "CondicionamientoTexto",
    "TextConditioner",
    "TokenizadorTexto",
    "construir_text_encoder",
    "construir_tokenizer",
]

_LOG = logging.getLogger("ace_step.text_conditioning")


# --------------------------------------------------------------------------- #
# Constantes del contrato (todas verificadas contra el artefacto y contra vendor/)
# --------------------------------------------------------------------------- #

#: Prefijo de los 310 tensores del text encoder dentro del artefacto. Quitarlo
#: devuelve las claves exactas de `Qwen3Model` (embed_tokens/layers/norm), sin
#: `model.` ni `lm_head`: `load_state_dict(strict=True)` sin remapeo.
PREFIJO_TEXT_ENCODER = "text_encoder."
N_CLAVES_TEXT_ENCODER = 310
#: 1.136 MiB en fp16. Es la cifra que justifica el despacho por componente.
MIB_TEXT_ENCODER = 1136

CLAVE_TOKENIZER = "aux.text_tokenizer.tokenizer_json"
CLAVE_TOKENIZER_CONFIG = "aux.text_tokenizer.tokenizer_config_json"
CLAVE_ESPECIALES = "aux.text_tokenizer.special_tokens_map_json"
CLAVE_CONFIG_QWEN3 = "aux.config.qwen3_json"

#: `config.text_hidden_dim` de ACE-Step y `hidden_size` de Qwen3-Embedding-0.6B.
#: Si el text encoder no saca 1024, `text_projector` revienta por forma.
DIM_TEXTO = 1024

#: Techos de longitud. No son estilisticos: `pack_sequences` suma la mascara en
#: el dtype del modelo y fp16 solo representa enteros exactos hasta 2048, asi
#: que L_lyric + L_timbre + L_text tiene que quedar por debajo. Superarlos es
#: error explicito: truncar la letra en silencio es perder estrofas sin avisar.
MAX_TOKENS_PROMPT = 256
MAX_TOKENS_LETRA = 1536
MAX_TOKENS_CROSS_ATTENTION = 2048

#: `--enc-len` por defecto de `spikes/dit_forward_bench.py`: la longitud de
#: cross-attention con la que se midieron los 2.867 ms del forward del DiT. Solo
#: se usa para contrastar en la autocomprobacion.
_L_ENC_BENCH = 210

#: Margen sobre los pesos al comprobar VRAM libre antes de subirlos.
_FACTOR_HOLGURA_VRAM = 1.10
_MARGEN_VRAM_BYTES = 128 * 1024 * 1024

_DTYPES = {
    "float16": torch.float16,
    "fp16": torch.float16,
    "half": torch.float16,
    "bfloat16": torch.bfloat16,
    "bf16": torch.bfloat16,
    "float32": torch.float32,
    "fp32": torch.float32,
    "float": torch.float32,
}


# --------------------------------------------------------------------------- #
# Blobs `aux.*`: bytes inertes dentro del artefacto
# --------------------------------------------------------------------------- #

def _texto_de_tensor(tensor: Any, nombre: str) -> str:
    """Decodifica a UTF-8 un blob `aux.*` almacenado como tensor U8.

    Los blobs del artefacto son dato inerte (JSON), nunca objetos serializados:
    aqui no hay `pickle` ni `torch.load` en ningun punto (D-14).
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"{nombre!r} no es un tensor (es {type(tensor).__name__}).")
    if tensor.dtype is not torch.uint8:
        raise TypeError(f"{nombre!r} deberia ser U8 y es {tensor.dtype}.")
    if tensor.dim() != 1:
        raise ValueError(f"{nombre!r} deberia ser 1-D y tiene forma {tuple(tensor.shape)}.")
    return bytes(tensor.detach().to("cpu").contiguous().numpy().tobytes()).decode("utf-8")


def _blob(state_dict: dict[str, Any], clave: str) -> Any:
    if clave not in state_dict:
        raise KeyError(
            f"El artefacto no trae {clave!r}. El condicionamiento de texto necesita el "
            "tokenizer y las configuraciones DENTRO del fichero de pesos: no se "
            "descarga nada de la red. Revisa el fusor (tools/build_artifact.py)."
        )
    return state_dict[clave]


# --------------------------------------------------------------------------- #
# Tokenizer
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class TokenizadorTexto:
    """Tokenizer del artefacto, ya validado.

    Args:
        tokenizer: instancia de `tokenizers.Tokenizer` construida en memoria.
        id_eos: id del token que el post-procesador anade al final.
        n_vocab: tamano del vocabulario incluidos los tokens anadidos.
    """

    tokenizer: Any
    id_eos: int
    n_vocab: int

    def codificar(self, texto: str) -> list[int]:
        """Ids del texto, con los tokens especiales del post-procesador."""
        return self.tokenizer.encode(texto, add_special_tokens=True).ids


def construir_tokenizer(state_dict: dict[str, Any]) -> TokenizadorTexto:
    """Construye el tokenizer desde `aux.text_tokenizer.tokenizer_json`, en memoria.

    Los 11,4 MB del `tokenizer.json` se pasan a la biblioteca `tokenizers` (Rust)
    como buffer: **no se escribe a disco** ni se toca la red.

    Verificacion critica del post-procesador
    ----------------------------------------
    El `tokenizer.json` de Qwen3-Embedding lleva un post-procesador
    `Sequence[ByteLevel, TemplateProcessing]` que anade `<|endoftext|>` al final
    de cada secuencia. Ese componente **se pierde** si alguien reconstruye el
    tokenizer desde `vocab.json` + `merges.txt` (que es lo que ofrece el
    repositorio upstream junto al `tokenizer.json`), y la perdida **no da
    error**: simplemente cambia el condicionamiento —el ultimo estado oculto deja
    de ser el del token de cierre con el que se entreno el modelo—. Por eso aqui
    se comprueba de forma funcional: se codifica una sonda con y sin tokens
    especiales y se exige que la diferencia sea exactamente el EOS declarado en
    la configuracion de Qwen3.

    Se comprueban ademas normalizador (NFC: relevante en castellano, une las
    tildes descompuestas), pre-tokenizador y decodificador, que son las otras
    tres piezas que se pierden en una reconstruccion manual, y que no haya
    truncamiento ni relleno configurados (cortarian la letra en silencio).
    """
    from tokenizers import Tokenizer  # noqa: PLC0415  (dependencia solo del camino real)

    crudo = _blob(state_dict, CLAVE_TOKENIZER)
    datos = bytes(crudo.detach().to("cpu").contiguous().numpy().tobytes())
    tokenizer = Tokenizer.from_buffer(datos)

    faltan = [
        nombre
        for nombre in ("normalizer", "pre_tokenizer", "post_processor", "decoder")
        if getattr(tokenizer, nombre, None) is None
    ]
    if faltan:
        raise RuntimeError(
            f"El tokenizer del artefacto ha perdido componentes: {', '.join(faltan)}. "
            "Es la firma de un tokenizer reconstruido desde vocab+merges en lugar de "
            "cargado desde tokenizer.json. Cambia el condicionamiento SIN dar error, "
            "asi que se aborta aqui."
        )
    for atributo in ("truncation", "padding"):
        valor = getattr(tokenizer, atributo, None)
        if valor is not None:
            raise RuntimeError(
                f"El tokenizer trae {atributo}={valor!r} configurado. Este modulo controla "
                "la longitud a mano (MAX_TOKENS_*) y no admite recortes ni rellenos "
                "implicitos."
            )

    config_qwen3 = json.loads(_texto_de_tensor(_blob(state_dict, CLAVE_CONFIG_QWEN3), CLAVE_CONFIG_QWEN3))
    id_eos = int(config_qwen3["eos_token_id"])

    sonda = "canción de prueba"
    con_especiales = tokenizer.encode(sonda, add_special_tokens=True).ids
    sin_especiales = tokenizer.encode(sonda, add_special_tokens=False).ids
    if con_especiales != [*sin_especiales, id_eos]:
        raise RuntimeError(
            "El post-procesador del tokenizer no anade el token de cierre esperado.\n"
            f"  con especiales : {con_especiales[-4:]}\n"
            f"  sin especiales : {sin_especiales[-4:]}\n"
            f"  eos_token_id declarado en aux.config.qwen3_json: {id_eos}\n"
            "Sin ese token el condicionamiento no es el que vio el modelo al entrenarse."
        )

    # Trampa documentada del artefacto: `tokenizer_config.json` declara
    # `eos_token = "<|im_end|>"` (151645, herencia del chat de Qwen), mientras que
    # el post-procesador anade `<|endoftext|>` (151643), que es el
    # `eos_token_id` de `aux.config.qwen3_json`. Quien construya el
    # condicionamiento a partir de `tokenizer.eos_token` en vez de dejar trabajar
    # al post-procesador cerrara la secuencia con el token equivocado.
    config_tokenizer = json.loads(
        _texto_de_tensor(_blob(state_dict, CLAVE_TOKENIZER_CONFIG), CLAVE_TOKENIZER_CONFIG)
    )
    eos_declarado = config_tokenizer.get("eos_token")
    if eos_declarado is not None and tokenizer.token_to_id(eos_declarado) != id_eos:
        _LOG.info(
            "tokenizer_config declara eos_token=%r (id %s), pero el que cierra la secuencia "
            "es el %d del post-procesador. Es lo esperado en Qwen3-Embedding: no uses "
            "eos_token para cerrar el condicionamiento a mano.",
            eos_declarado,
            tokenizer.token_to_id(eos_declarado),
            id_eos,
        )

    especiales = json.loads(_texto_de_tensor(_blob(state_dict, CLAVE_ESPECIALES), CLAVE_ESPECIALES))
    _LOG.debug("Tokens especiales del artefacto: %s", sorted(especiales))

    n_vocab = tokenizer.get_vocab_size(with_added_tokens=True)
    _LOG.info(
        "Tokenizer construido en memoria: %d entradas de vocabulario, post-procesador "
        "verificado (anade %d), normalizador %s.",
        n_vocab,
        id_eos,
        type(tokenizer.normalizer).__name__,
    )
    return TokenizadorTexto(tokenizer=tokenizer, id_eos=id_eos, n_vocab=n_vocab)


# --------------------------------------------------------------------------- #
# Text encoder (Qwen3-Embedding-0.6B)
# --------------------------------------------------------------------------- #

def _resolver_dtype(dtype: Any) -> torch.dtype:
    if isinstance(dtype, torch.dtype):
        return dtype
    nombre = str(dtype).strip().lower()
    if nombre.startswith("torch."):
        nombre = nombre[len("torch.") :]
    if nombre not in _DTYPES:
        raise ValueError(f"dtype no reconocido: {dtype!r}. Admitidos: {sorted(_DTYPES)}.")
    return _DTYPES[nombre]


def construir_text_encoder(
    state_dict: dict[str, Any],
    *,
    consumir: bool = True,
    materializado: bool = False,
) -> tuple[Any, Any, torch.dtype]:
    """Instancia el Qwen3 del artefacto y le carga sus 310 tensores.

    Sin red, sin `trust_remote_code`, sin `auto_map` y sin `from_pretrained`: la
    clase sale de `transformers` (que viaja fijada en la imagen) y los pesos y la
    configuracion salen del artefacto.

    El modelo se instancia en el dispositivo `meta` y los tensores se **asignan**
    (`assign=True`), asi que los 1.136 MiB existen una sola vez en memoria: no
    hay una copia vacia intermedia. La contrapartida es que los buffers no
    persistentes de RoPE (`inv_freq`, `original_inv_freq`) se quedarian en
    `meta`, asi que el modulo rotatorio se reconstruye despues, en CPU, y se
    verifica que no queda ni un tensor en `meta`.

    Args:
        state_dict: diccionario completo del artefacto.
        consumir: si es `True` (por defecto) **saca** las claves `text_encoder.*`
            del diccionario del llamante. Es deliberado: el artefacto llega entero
            y en una tarjeta de 8 GB esos 1.136 MiB duplicados son la diferencia
            entre generar y no generar. Con `consumir=False` el llamante se queda
            la copia y es cosa suya liberarla.
        materializado: los tensores vienen de `carga_contigua`, o sea que ya estan
            en RAM anonima. Entonces el clon de mas abajo sobra: son 1.136 MiB
            copiados para nada. Con `load_file` (mapeo del fichero) la bandera va
            a `False` y se clona como siempre.

    Returns:
        `(modelo_en_cpu, config, dtype_del_artefacto)`.
    """
    from transformers import Qwen3Config  # noqa: PLC0415
    from transformers.models.qwen3 import modeling_qwen3  # noqa: PLC0415

    claves = [k for k in state_dict if k.startswith(PREFIJO_TEXT_ENCODER)]
    if not claves:
        raise KeyError(
            f"El artefacto no trae ninguna clave {PREFIJO_TEXT_ENCODER!r}. Sin text "
            "encoder no hay condicionamiento posible."
        )
    if len(claves) != N_CLAVES_TEXT_ENCODER:
        _LOG.warning(
            "El artefacto trae %d claves %s; el contrato registrado son %d. "
            "load_state_dict(strict=True) dira exactamente que sobra o falta.",
            len(claves),
            PREFIJO_TEXT_ENCODER,
            N_CLAVES_TEXT_ENCODER,
        )

    pesos: dict[str, torch.Tensor] = {}
    for clave in claves:
        tensor = state_dict.pop(clave) if consumir else state_dict[clave]
        # A RAM: los pesos viven en CPU y solo suben a VRAM durante encode().
        origen = tensor.detach()
        destino = origen.to("cpu")
        if destino.data_ptr() == origen.data_ptr() and not materializado:
            # `.to("cpu")` sobre un tensor que ya esta en CPU NO copia: devuelve
            # el mismo almacenamiento. Si venia de `safe_open`, ese almacenamiento
            # es el fichero mapeado en memoria, y la primera subida a VRAM acaba
            # leyendo del disco pagina a pagina. MEDIDO sobre el bind mount
            # (2026-09-02, GTX 1070): subir los 310 tensores mapeados tarda
            # 42,91 s la primera vez y 0,43 s la segunda, cuando las paginas ya
            # estan en la cache del sistema. El clon paga esa lectura una sola
            # vez, al construir, y no dentro de la generacion.
            destino = destino.clone()
        pesos[clave[len(PREFIJO_TEXT_ENCODER) :]] = destino
    if consumir:
        # La referencia local desaparece al salir; si venian de VRAM, esto es lo
        # que permite recuperarlos. El llamante ya no los tiene.
        del claves

    dtype_artefacto = pesos["embed_tokens.weight"].dtype
    if pesos["embed_tokens.weight"].shape[1] != DIM_TEXTO:
        raise RuntimeError(
            f"El text encoder saca {pesos['embed_tokens.weight'].shape[1]} dimensiones y "
            f"ACE-Step exige text_hidden_dim={DIM_TEXTO} (vendor/config.json). "
            "El artefacto no case con el modelo."
        )

    config_dict = json.loads(_texto_de_tensor(_blob(state_dict, CLAVE_CONFIG_QWEN3), CLAVE_CONFIG_QWEN3))
    # `architectures` y `auto_map` no se usan jamas para resolver codigo: la
    # clase se referencia de forma explicita mas abajo (invariante de CLAUDE.md).
    config_dict.pop("architectures", None)
    config_dict.pop("auto_map", None)
    # El dtype lo manda el artefacto (fp16 tras la fusion), no lo que diga el
    # json heredado del repositorio upstream (bfloat16, que Pascal no ejecuta).
    config_dict["dtype"] = str(dtype_artefacto).removeprefix("torch.")
    config = Qwen3Config(**config_dict)
    if config.hidden_size != DIM_TEXTO:
        raise RuntimeError(
            f"aux.config.qwen3_json declara hidden_size={config.hidden_size}, y ACE-Step "
            f"exige {DIM_TEXTO}."
        )
    config.use_cache = False

    dtype_previo = torch.get_default_dtype()
    torch.set_default_dtype(dtype_artefacto)
    try:
        with torch.device("meta"):
            modelo = modeling_qwen3.Qwen3Model(config)
    finally:
        torch.set_default_dtype(dtype_previo)

    modelo.load_state_dict(pesos, strict=True, assign=True)
    # RoPE: buffers no persistentes, no estan en el state_dict y se quedaron en
    # `meta`. Se reconstruyen en CPU (coste despreciable, tabla de inv_freq).
    modelo.rotary_emb = modeling_qwen3.Qwen3RotaryEmbedding(config)
    en_meta = [n for n, t in (*modelo.named_parameters(), *modelo.named_buffers()) if t.is_meta]
    if en_meta:
        raise RuntimeError(
            f"Quedan tensores en el dispositivo 'meta' tras la carga: {en_meta[:5]}. "
            "Usarlos daria un fallo tardio y confuso dentro del forward."
        )

    modelo.eval()
    modelo.requires_grad_(False)
    # Pascal (sm_61): SDPA cae al kernel mem-efficient y es ~13x mas lento que
    # eager, en silencio. set_attn_implementation() devuelve 'sdpa' sin avisar,
    # asi que se asigna a mano y se comprueba que ha bajado a las capas. La
    # comprobacion NO es tautologica: `transformers` comparte el mismo objeto de
    # configuracion con cada submodulo, asi que una capa que tuviera copia propia
    # seguiria diciendo 'sdpa' y esto abortaria. Verificado ademas por conteo de
    # llamadas (2026-09-02): dos pasadas sobre 28 capas dan 56 invocaciones de
    # `modeling_qwen3.eager_attention_forward` y 0 de la entrada 'sdpa' de
    # ALL_ATTENTION_FUNCTIONS.
    config._attn_implementation = "eager"
    if modelo.layers[0].self_attn.config._attn_implementation != "eager":
        raise RuntimeError(
            "No se pudo forzar la atencion 'eager' en el text encoder: la capa sigue en "
            f"{modelo.layers[0].self_attn.config._attn_implementation!r}."
        )

    bytes_pesos = sum(t.numel() * t.element_size() for t in modelo.parameters())
    _LOG.info(
        "Text encoder listo en CPU: %d capas, hidden=%d, dtype=%s, %.0f MiB.",
        config.num_hidden_layers,
        config.hidden_size,
        dtype_artefacto,
        bytes_pesos / 1048576,
    )
    return modelo, config, dtype_artefacto


# --------------------------------------------------------------------------- #
# Resultado
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class CondicionamientoTexto:
    """Los cuatro tensores que consume `prepare_condition()` del artefacto.

    Todos en el dispositivo y el dtype del DiT. Las mascaras van en el dtype del
    modelo (no bool ni int64): es lo que hace upstream en su propio
    `test_forward` (`vendor/modeling_acestep_v15_turbo.py` L2004-2007) y lo que
    esperan `create_4d_mask` y `pack_sequences`.
    """

    text_hidden_states: torch.Tensor      # [B, L_text,  1024]
    text_attention_mask: torch.Tensor     # [B, L_text]
    lyric_hidden_states: torch.Tensor     # [B, L_lyric, 1024]
    lyric_attention_mask: torch.Tensor    # [B, L_lyric]
    tokens_prompt: int
    tokens_letra: int
    instrumental: bool

    def longitud_cross_attention(self, tokens_timbre: int = 1) -> int:
        """L_enc que vera el DiT: `L_lyric + L_timbre + L_text`.

        `tokens_timbre` es el numero de embeddings de timbre que devuelve
        `AceStepTimbreEncoder` tras desempaquetar; en text2music, con un unico
        audio de referencia ficticio por elemento del lote, es 1. El bench midio
        L_enc = 210 como longitud tipica.
        """
        return self.tokens_letra + tokens_timbre + self.tokens_prompt

    def como_kwargs(self) -> dict[str, torch.Tensor]:
        """Los cuatro tensores con el nombre exacto del parametro de upstream."""
        return {
            "text_hidden_states": self.text_hidden_states,
            "text_attention_mask": self.text_attention_mask,
            "lyric_hidden_states": self.lyric_hidden_states,
            "lyric_attention_mask": self.lyric_attention_mask,
        }


# --------------------------------------------------------------------------- #
# El condicionador
# --------------------------------------------------------------------------- #

class TextConditioner:
    """Tokenizer + Qwen3 del artefacto, con despacho por componente.

    Los pesos viven en RAM. `encode()` los sube a VRAM, ejecuta las dos pasadas
    (prompt y letra) y los devuelve a CPU antes de salir, para que el bucle de
    difusion no compita con 1.136 MiB residentes.
    """

    def __init__(
        self,
        *,
        tokenizador: TokenizadorTexto,
        modelo: Any,
        config: Any,
        dtype: torch.dtype,
        device: str | torch.device,
    ) -> None:
        self._tok = tokenizador
        self._modelo = modelo
        self._config = config
        self._dtype = dtype
        self._device = torch.device(device)
        self._bytes_pesos = sum(t.numel() * t.element_size() for t in modelo.parameters())
        self._residente = False
        #: Copia maestra en RAM de cada parametro y buffer. Subir a VRAM sustituye
        #: el `.data` de cada tensor; bajar **restaura** desde esta copia en lugar
        #: de traerse 1.136 MiB de vuelta por PCIe. El maestro nunca se toca, asi
        #: que la bajada es exacta por construccion y cuesta microsegundos.
        self._maestro: dict[str, torch.Tensor] = {
            nombre: tensor.detach()
            for nombre, tensor in (*modelo.named_parameters(), *modelo.named_buffers())
        }

    # -- construccion ------------------------------------------------------- #

    @classmethod
    def desde_state_dict(
        cls,
        state_dict: dict[str, Any],
        *,
        device: str | torch.device,
        dtype: Any = None,
        consumir: bool = True,
    ) -> TextConditioner:
        """Construye el condicionador desde el diccionario completo del artefacto.

        Args:
            state_dict: el `state_dict` que recibe la factoria del shim.
            device: dispositivo de **computo** (donde correra el forward). Los
                pesos no se quedan ahi.
            dtype: dtype pedido por el `RunnerContext`. Solo se usa para avisar:
                manda el dtype real de los tensores del artefacto, porque
                reinterpretar 1.136 MiB al vuelo no es gratis ni inocuo.
            consumir: ver `construir_text_encoder()`.
        """
        tokenizador = construir_tokenizer(state_dict)
        modelo, config, dtype_artefacto = construir_text_encoder(state_dict, consumir=consumir)
        if dtype is not None:
            pedido = _resolver_dtype(dtype)
            if pedido is not dtype_artefacto:
                _LOG.warning(
                    "Se pidio dtype=%s pero el artefacto esta en %s. Manda el artefacto: "
                    "el condicionamiento sale en %s, que es tambien el dtype del DiT.",
                    pedido,
                    dtype_artefacto,
                    dtype_artefacto,
                )
        return cls(
            tokenizador=tokenizador,
            modelo=modelo,
            config=config,
            dtype=dtype_artefacto,
            device=device,
        )

    # -- despacho por componente ------------------------------------------- #

    def _subir(self) -> None:
        """Mueve el text encoder a la GPU tras comprobar que cabe.

        Se consulta `mem_get_info` **antes** de reservar. Un OOM de driver deja
        el caching allocator de PyTorch en un estado del que no se sale dentro
        del proceso, asi que aqui se aborta antes; el OOM nunca se captura.
        """
        if self._device.type != "cuda":
            return
        necesarios = int(self._bytes_pesos * _FACTOR_HOLGURA_VRAM) + _MARGEN_VRAM_BYTES
        libre, total = torch.cuda.mem_get_info(self._device)
        if libre < necesarios:
            raise RuntimeError(
                "VRAM insuficiente para subir el text encoder.\n"
                f"  necesarios : {necesarios / 1048576:.0f} MiB "
                f"({self._bytes_pesos / 1048576:.0f} MiB de pesos + holgura)\n"
                f"  libres     : {libre / 1048576:.0f} MiB de {total / 1048576:.0f} MiB\n"
                "Se aborta ANTES de reservar: un OOM de driver corrompe el caching "
                "allocator y no es recuperable en este proceso."
            )
        self._modelo.to(self._device)
        self._residente = True

    def _bajar(self) -> None:
        """Devuelve el text encoder a CPU y libera su VRAM.

        No hay transferencia de vuelta: se restaura la copia maestra de RAM, que
        no ha cambiado (el forward no entrena nada), y las replicas de VRAM se
        quedan sin referencias y las libera el asignador.
        """
        if self._device.type != "cuda" or not self._residente:
            return
        for nombre, tensor in (*self._modelo.named_parameters(), *self._modelo.named_buffers()):
            tensor.data = self._maestro[nombre]
        self._residente = False
        torch.cuda.empty_cache()

    @property
    def residente_en_gpu(self) -> bool:
        """`True` solo mientras dura una llamada a `encode()`."""
        return self._residente

    @property
    def bytes_pesos(self) -> int:
        return self._bytes_pesos

    @property
    def tokenizador(self) -> TokenizadorTexto:
        """El tokenizer ya validado del artefacto (solo lectura)."""
        return self._tok

    # -- codificacion ------------------------------------------------------- #

    def _preparar_textos(self, style_prompt: str, lyrics: str | None, instrumental: bool) -> tuple[str, str]:
        """Punto unico donde se decide QUE texto se tokeniza.

        Se codifica el texto tal cual, sin plantilla de instruccion: el pipeline
        de inferencia de upstream no esta vendorizado y no hay forma de verificar
        otra envoltura sin inventarla. Para una pista instrumental la letra pasa
        a ser la cadena vacia, que el post-procesador convierte en **un unico
        token** `<|endoftext|>`. No se usa una mascara de ceros porque el DiT
        descarta `encoder_attention_mask` (L1381-1382): un hueco enmascarado se
        atenderia igualmente, mientras que un token de cierre es la
        representacion mas corta y honesta de "sin letra".
        """
        prompt = (style_prompt or "").strip()
        if not prompt:
            raise ValueError("El prompt de estilo no puede estar vacio.")
        letra = (lyrics or "").strip()
        if instrumental and letra:
            raise ValueError(
                "instrumental=True con letra no vacia: la peticion se contradice. "
                "Decide una de las dos cosas antes de condicionar."
            )
        if instrumental:
            letra = ""
        return prompt, letra

    def _ids(self, texto: str, *, maximo: int, etiqueta: str) -> list[int]:
        ids = self._tok.codificar(texto)
        if len(ids) > maximo:
            raise ValueError(
                f"{etiqueta}: {len(ids)} tokens, por encima del techo de {maximo}. "
                "No se trunca en silencio (perder estrofas sin avisar es peor que "
                "fallar): recorta el texto o sube el techo a sabiendas de que "
                f"L_enc no puede pasar de {MAX_TOKENS_CROSS_ATTENTION} tokens."
            )
        return ids

    @torch.no_grad()
    def _pasada(self, ids: list[int]) -> torch.Tensor:
        """Una pasada del Qwen3 sobre una secuencia sin relleno (B=1)."""
        entrada = torch.tensor([ids], dtype=torch.long, device=self._device)
        mascara = torch.ones_like(entrada)
        salida = self._modelo(input_ids=entrada, attention_mask=mascara, use_cache=False)
        estados = salida.last_hidden_state
        if estados.shape[-1] != DIM_TEXTO:
            raise RuntimeError(
                f"El text encoder saco {estados.shape[-1]} dimensiones; ACE-Step exige "
                f"{DIM_TEXTO}."
            )
        return estados.to(self._dtype)

    def encode(
        self,
        *,
        style_prompt: str,
        lyrics: str | None = None,
        instrumental: bool = False,
    ) -> CondicionamientoTexto:
        """Codifica prompt y letra y devuelve los tensores del DiT.

        Sube el text encoder a la GPU, hace las **dos** pasadas en una sola
        residencia y lo devuelve a CPU pase lo que pase. Los tensores resultantes
        se quedan en la GPU: son ~1 MiB, no 1.136 MiB.
        """
        prompt, letra = self._preparar_textos(style_prompt, lyrics, instrumental)
        ids_prompt = self._ids(prompt, maximo=MAX_TOKENS_PROMPT, etiqueta="prompt de estilo")
        ids_letra = self._ids(letra, maximo=MAX_TOKENS_LETRA, etiqueta="letra")
        # +1 por el token de timbre de text2music (ver longitud_cross_attention).
        l_enc = len(ids_prompt) + len(ids_letra) + 1
        if l_enc > MAX_TOKENS_CROSS_ATTENTION:
            raise ValueError(
                f"L_enc = {l_enc} tokens supera el techo de {MAX_TOKENS_CROSS_ATTENTION}. "
                "pack_sequences suma la mascara en el dtype del modelo y fp16 deja de "
                "representar enteros exactos a partir de 2048: por encima de ese punto el "
                "empaquetado del condicionamiento es incorrecto sin dar error."
            )

        self._subir()
        try:
            estados_prompt = self._pasada(ids_prompt)
            estados_letra = self._pasada(ids_letra)
        finally:
            # Requisito de VRAM: el text encoder no puede seguir residente
            # durante la difusion, ni siquiera si la pasada ha fallado.
            self._bajar()

        for nombre, tensor in (("prompt", estados_prompt), ("letra", estados_letra)):
            if not torch.isfinite(tensor).all():
                n_nan = int(torch.isnan(tensor).sum())
                n_inf = int(torch.isinf(tensor).sum())
                raise RuntimeError(
                    f"El condicionamiento de {nombre} contiene valores no finitos "
                    f"({n_nan} NaN, {n_inf} inf). Condicionar el DiT con esto propaga la "
                    "corrupcion a todo el audio."
                )

        mascara_prompt = torch.ones(estados_prompt.shape[:2], dtype=self._dtype, device=estados_prompt.device)
        mascara_letra = torch.ones(estados_letra.shape[:2], dtype=self._dtype, device=estados_letra.device)
        return CondicionamientoTexto(
            text_hidden_states=estados_prompt,
            text_attention_mask=mascara_prompt,
            lyric_hidden_states=estados_letra,
            lyric_attention_mask=mascara_letra,
            tokens_prompt=len(ids_prompt),
            tokens_letra=len(ids_letra),
            instrumental=instrumental,
        )

    def release(self) -> None:
        """Suelta el text encoder. Idempotente."""
        self._bajar()
        self._modelo = None
        self._maestro = {}
        self._residente = False


# --------------------------------------------------------------------------- #
# Autocomprobacion (`python text_conditioning.py --weights /weights/...`)
# --------------------------------------------------------------------------- #

def _leer_cabecera(ruta: str) -> tuple[dict[str, Any], int]:
    """Cabecera JSON de un safetensors: 8 bytes de longitud + JSON. Sin pickle."""
    with open(ruta, "rb") as fichero:
        n = int.from_bytes(fichero.read(8), "little")
        return json.loads(fichero.read(n).decode("utf-8")), 8 + n


def _cargar_parcial(ruta: str) -> dict[str, torch.Tensor]:
    """Carga solo `aux.*` y `text_encoder.*`, en orden de offset en el fichero.

    El orden importa: leer las claves en orden alfabetico sobre un disco lento
    provoca busqueda aleatoria. Ordenando por `data_offsets` la lectura es
    practicamente secuencial.
    """
    from safetensors import safe_open  # noqa: PLC0415

    cabecera, _ = _leer_cabecera(ruta)
    quiero = [
        clave
        for clave, meta in cabecera.items()
        if clave != "__metadata__"
        and (clave.startswith("aux.") or clave.startswith(PREFIJO_TEXT_ENCODER))
    ]
    quiero.sort(key=lambda c: cabecera[c]["data_offsets"][0])
    parcial: dict[str, torch.Tensor] = {}
    with safe_open(ruta, framework="pt", device="cpu") as fichero:
        for clave in quiero:
            parcial[clave] = fichero.get_tensor(clave)
    return parcial


def _mib_libres() -> tuple[float, float]:
    libre, total = torch.cuda.mem_get_info()
    return libre / 1048576, total / 1048576


def _autocomprobacion(ruta: str, device: str) -> int:
    """Codifica un prompt y una letra reales en castellano y reporta lo medido."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    hay_cuda = torch.cuda.is_available() and device.startswith("cuda")
    if device.startswith("cuda") and not hay_cuda:
        print("CUDA no disponible: la comprobacion de VRAM no es posible.", file=sys.stderr)
        return 2

    print("=" * 78)
    print("AUTOCOMPROBACION DEL CONDICIONAMIENTO DE TEXTO — ACE-Step 1.5")
    print("=" * 78)
    if hay_cuda:
        props = torch.cuda.get_device_properties(0)
        libre0, total0 = _mib_libres()
        print(f"GPU: {props.name} sm_{props.major}{props.minor} — "
              f"{total0:.0f} MiB totales, {libre0:.0f} MiB libres al empezar")
    print(f"torch {torch.__version__} · transformers "
          f"{__import__('transformers').__version__} · tokenizers "
          f"{__import__('tokenizers').__version__}")

    t0 = time.perf_counter()
    parcial = _cargar_parcial(ruta)
    t_carga = time.perf_counter() - t0
    n_te = sum(1 for k in parcial if k.startswith(PREFIJO_TEXT_ENCODER))
    print(f"\n[1] Artefacto: {len(parcial)} tensores leidos ({n_te} de text_encoder.*) "
          f"en {t_carga:.1f} s")

    t0 = time.perf_counter()
    conditioner = TextConditioner.desde_state_dict(parcial, device=device, dtype="bfloat16")
    t_build = time.perf_counter() - t0
    quedan = [k for k in parcial if k.startswith(PREFIJO_TEXT_ENCODER)]
    print(f"[2] Condicionador construido en {t_build:.1f} s · "
          f"{conditioner.bytes_pesos / 1048576:.0f} MiB de pesos en RAM · "
          f"claves text_encoder.* que quedan en el state_dict del llamante: {len(quedan)}")

    # Evidencia del tokenizer: los cuatro componentes que se pierden al
    # reconstruirlo desde vocab+merges, y el efecto real del post-procesador.
    tokenizador = conditioner.tokenizador
    interno = tokenizador.tokenizer
    print(f"    componentes: normalizer={type(interno.normalizer).__name__} · "
          f"pre_tokenizer={type(interno.pre_tokenizer).__name__} · "
          f"post_processor={type(interno.post_processor).__name__} · "
          f"decoder={type(interno.decoder).__name__}")
    sonda = "canción de prueba"
    print(f"    sonda {sonda!r}: sin especiales "
          f"{interno.encode(sonda, add_special_tokens=False).ids} → con especiales "
          f"{interno.encode(sonda, add_special_tokens=True).ids} "
          f"(el post-procesador cierra con {tokenizador.id_eos})")

    prompt = (
        "flamenco pop moderno, guitarra española, palmas, cajón, bajo cálido, "
        "voz femenina con cuerpo, tempo medio 96 BPM, producción luminosa"
    )
    # Letra de canción completa (estructura de una pista de ~3 min), no un
    # fragmento: es lo que decide el L_enc real del cross-attention.
    letra = (
        "[Verso 1]\n"
        "Se apagan las farolas de mi calle,\n"
        "y el eco de tus pasos ya no está.\n"
        "Guardé tu nombre dentro de un detalle,\n"
        "que el viento del invierno se llevará.\n\n"
        "[Estribillo]\n"
        "Y si vuelves, que sea de verdad,\n"
        "que ya no queda sitio en mi ciudad\n"
        "para el humo de una despedida.\n"
        "Y si vuelves, que sea sin mirar\n"
        "la sombra de lo que no supe dar\n"
        "cuando aún nos sobraba la vida.\n\n"
        "[Verso 2]\n"
        "Aprendí a coser el desconsuelo\n"
        "con hilo de otras noches sin dormir.\n"
        "La casa se quedó del mismo suelo,\n"
        "pero nadie me enseñó a vivir aquí.\n\n"
        "[Estribillo]\n"
        "Y si vuelves, que sea de verdad,\n"
        "que ya no queda sitio en mi ciudad\n"
        "para el humo de una despedida.\n\n"
        "[Puente]\n"
        "No me llames si es por costumbre,\n"
        "no me busques si es por no estar solo.\n"
        "Que este cuerpo ya tiene su lumbre\n"
        "y ha aprendido a encenderse él solo.\n\n"
        "[Final]\n"
        "Se apagan las farolas de mi calle.\n"
    )

    if hay_cuda:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        libre_antes, _ = _mib_libres()

    t0 = time.perf_counter()
    cond = conditioner.encode(style_prompt=prompt, lyrics=letra)
    t_enc = time.perf_counter() - t0

    print(f"\n[3] encode() en {t_enc * 1000:.0f} ms")
    print(f"    prompt : {cond.tokens_prompt} tokens · letra: {cond.tokens_letra} tokens")
    for nombre, tensor in (
        ("text_hidden_states ", cond.text_hidden_states),
        ("text_attention_mask", cond.text_attention_mask),
        ("lyric_hidden_states ", cond.lyric_hidden_states),
        ("lyric_attention_mask", cond.lyric_attention_mask),
    ):
        finito = bool(torch.isfinite(tensor).all())
        print(f"    {nombre} {str(tuple(tensor.shape)):>18} {str(tensor.dtype):>14} "
              f"{str(tensor.device):>7}  finito={finito}  "
              f"|min={tensor.min().item():+.4f} max={tensor.max().item():+.4f}|")
    l_enc = cond.longitud_cross_attention()
    print(f"    L_enc = L_lyric + 1 (timbre) + L_text = {cond.tokens_letra} + 1 + "
          f"{cond.tokens_prompt} = {l_enc}")
    print(f"    frente a los {_L_ENC_BENCH} del bench (spikes/dit_forward_bench.py "
          f"--enc-len): {l_enc - _L_ENC_BENCH:+d} tokens · "
          f"techo del modulo {MAX_TOKENS_CROSS_ATTENTION}")

    if hay_cuda:
        libre_despues, _ = _mib_libres()
        pico = torch.cuda.max_memory_allocated() / 1048576
        reservado = torch.cuda.memory_allocated() / 1048576
        print(f"\n[4] VRAM: libre antes {libre_antes:.0f} MiB · libre despues "
              f"{libre_despues:.0f} MiB · delta {libre_antes - libre_despues:+.0f} MiB")
        print(f"    pico asignado durante encode(): {pico:.0f} MiB · "
              f"residente al terminar: {reservado:.1f} MiB")
        print(f"    text encoder residente en GPU tras encode(): "
              f"{conditioner.residente_en_gpu}")
        devuelto = (libre_antes - libre_despues) < (MIB_TEXT_ENCODER / 2)
        print(f"    ¿devolvio el encoder a CPU? {'SI' if devuelto else 'NO'} "
              f"(criterio: el delta de VRAM libre queda muy por debajo de los "
              f"{MIB_TEXT_ENCODER} MiB de pesos)")

    t0 = time.perf_counter()
    instr = conditioner.encode(style_prompt=prompt, lyrics=None, instrumental=True)
    t_instr = time.perf_counter() - t0
    print(f"\n[5] instrumental: letra -> {instr.tokens_letra} token(s), "
          f"lyric_hidden_states {tuple(instr.lyric_hidden_states.shape)} · "
          f"segunda llamada a encode() en {t_instr * 1000:.0f} ms")

    conditioner.release()
    if hay_cuda:
        torch.cuda.empty_cache()
        libre_fin, _ = _mib_libres()
        print(f"\n[6] Tras release(): {libre_fin:.0f} MiB libres")
    print("\nOK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Autocomprobacion del condicionamiento de texto de ACE-Step 1.5: tokeniza un "
            "prompt y una letra reales, ejecuta el text encoder y reporta formas, dtypes, "
            "VRAM y ausencia de NaN."
        )
    )
    parser.add_argument(
        "--weights",
        default=os.path.join("/weights", "ace_step_1_5.safetensors"),
        help="Ruta del artefacto safetensors.",
    )
    parser.add_argument("--device", default="cuda:0", help="Dispositivo de computo.")
    args = parser.parse_args(argv)
    if not args.weights.endswith(".safetensors"):
        parser.error("Solo se admiten pesos en formato safetensors (D-14).")
    return _autocomprobacion(args.weights, args.device)


if __name__ == "__main__":
    raise SystemExit(main())
