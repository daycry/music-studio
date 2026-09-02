# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original.
#
# Obra derivada de `acestep/llm_inference.py` (metodos `build_formatted_prompt`,
# `build_formatted_prompt_with_cot`, `_format_metadata_as_cot`,
# `_build_unconditional_prompt`, `_has_meaningful_negative_prompt` y
# `parse_lm_output` de la clase `LLMHandler`).
#
#   Origen          : github.com/ace-step/ACE-Step-1.5, ruta `acestep/llm_inference.py`
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866  (2026-08-29)
#   Bytes origen    : 192383
#   SHA-256 origen  : afe1baf01d8a594bd06148bf9c79a0f66f84072b5158ae598340b34cc215b9c6
#   blob SHA-1      : 3690af56d8fe5c6a51844917e8e56c54fc088953  (verificado contra
#                     la atestacion del arbol de la API de GitHub)
#   Copiado el      : 2026-09-02
#   Licencia        : MIT (LICENSE de la raiz del repositorio, blob SHA-1
#                     600451d484a555c1273baa2602f32a37fdd0d0ab)
#
# Cada cambio va marcado con "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Construccion del prompt del planificador de 5 Hz y lectura de su salida.

Por que el formato importa tanto
--------------------------------
El LM se entreno viendo un turno de asistente con esta forma exacta::

    <|im_start|>system
    # Instruction
    Generate audio semantic tokens based on the given conditions:

    <|im_end|>
    <|im_start|>user
    # Caption
    {estilo}

    # Lyric
    {letra}
    <|im_end|>
    <|im_start|>assistant
    <think>
    bpm: 120
    caption: ...
    duration: 30
    keyscale: G major
    language: es
    timesignature: 4
    </think>

    <|audio_code_...|><|audio_code_...|>...<|im_end|>

Dos detalles que parecen cosmeticos y no lo son:

- El turno de asistente se deja **ABIERTO**. Si el razonamiento se metiese como
  un mensaje `role="assistant"`, la plantilla de Qwen lo cerraria con
  `<|im_end|>` y el modelo leeria "fin de turno" donde tiene que leer "aqui van
  los codigos".
- Entre `</think>` y el primer codigo van **dos** saltos de linea, porque es lo
  que inserta la plantilla de Qwen al renderizar un mensaje de asistente con
  razonamiento. Reproducirlo a mano es lo que hace que entrenamiento e
  inferencia vean el mismo prefijo justo antes del primer codigo.

Y en el prompt incondicional del CFG, el mensaje de usuario es el texto
`"NO USER INPUT"` **a pelo**, no envuelto en `# Caption ... # Lyric ...`: asi es
como upstream reproduce el "dropout" de condicion del entrenamiento.

Que se ha quitado
-----------------
- `use_legacy_cfg_prompt`: interruptor A/B de upstream para comparar el formato
  anterior. Un experimento suyo, no una via de produccion.
- Los prompts de `understand`, `inspiration` y `format` (comprension de audio,
  ampliacion de la idea y reformateo de texto). Otras tareas.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# NOTA DE DEPENDENCIA: PyYAML esta en la imagen (6.0.3, comprobado dentro del
# contenedor) pero llega de forma TRANSITIVA por `huggingface-hub`, no por un pin
# del Dockerfile. Se usa a proposito en vez de reimplementarlo: `yaml.dump` pliega
# los captions largos en lineas de continuacion indentadas, y ese plegado FORMA
# PARTE del formato que vio el modelo al entrenarse. Reimplementarlo "a mano"
# produciria un prompt distinto sin que nada fallase. Recomendacion registrada en
# el README de este directorio: fijar `pyyaml` en el Dockerfile.
import yaml

from .constants import CAMPOS_COT, DEFAULT_LM_INSTRUCTION
from .decodificacion_restringida import limpiar_caption

__all__ = [
    "SIN_ENTRADA_USUARIO",
    "hay_prompt_negativo",
    "metadatos_a_cot",
    "parsear_salida",
    "prompt_codigos",
    "prompt_codigos_uncond",
    "prompt_cot",
    "prompt_cot_uncond",
]

#: Marcador de "el usuario no ha dado prompt negativo". Literal de upstream.
SIN_ENTRADA_USUARIO = "NO USER INPUT"

#: Razonamiento vacio del prompt incondicional. El salto interior es el que
#: produce la plantilla de Qwen al renderizar un razonamiento vacio; upstream lo
#: documenta explicitamente y no es `<think>\n</think>`.
_COT_VACIO = "<think>\n\n</think>"

_PATRON_CODIGO = re.compile(r"<\|audio_code_(\d+)\|>")


def hay_prompt_negativo(prompt_negativo: Optional[str]) -> bool:
    """True si el prompt negativo tiene contenido real (no el marcador)."""
    return bool(
        prompt_negativo
        and prompt_negativo.strip()
        and prompt_negativo.strip() != SIN_ENTRADA_USUARIO
    )


def _envolver(tokenizer, contenido_usuario: str) -> str:
    """Aplica la plantilla de chat con el turno de asistente abierto."""
    return tokenizer.apply_chat_template(
        [
            {"role": "system", "content": f"# Instruction\n{DEFAULT_LM_INSTRUCTION}\n\n"},
            {"role": "user", "content": contenido_usuario},
        ],
        tokenize=False,
        add_generation_prompt=True,
    )


def prompt_cot(tokenizer, estilo: str, letra: str = "") -> str:
    """Prompt de la fase 1: generar los metadatos del razonamiento."""
    return _envolver(tokenizer, f"# Caption\n{estilo}\n\n# Lyric\n{letra}\n")


def prompt_cot_uncond(tokenizer, letra: str, prompt_negativo: str = SIN_ENTRADA_USUARIO) -> str:
    """Prompt incondicional de la fase 1 (solo si se usa CFG en el razonamiento).

    Upstream NO aplica CFG en la fase de razonamiento —`cfg_scale` se fuerza a
    1,0— porque escalar logits de texto provoca saltos de linea prematuros y
    captions truncados. Se mantiene la funcion porque es barata y deja el
    experimento disponible, pero el planificador no la usa.
    """
    if hay_prompt_negativo(prompt_negativo):
        return _envolver(tokenizer, f"# Caption\n{prompt_negativo}\n\n# Lyric\n{letra}\n")
    return _envolver(tokenizer, f"# Lyric\n{letra}\n")


def prompt_codigos(tokenizer, estilo: str, letra: str, cot: str) -> str:
    """Prompt de la fase 2: el razonamiento ya hecho, faltan los codigos."""
    return _envolver(tokenizer, f"# Caption\n{estilo}\n\n# Lyric\n{letra}\n") + cot + "\n\n"


def prompt_codigos_uncond(tokenizer, prompt_negativo: str = SIN_ENTRADA_USUARIO) -> str:
    """Prompt incondicional de la fase 2 para el CFG.

    El mensaje de usuario es el prompt negativo **crudo** (o el literal
    `"NO USER INPUT"`), sin el envoltorio `# Caption / # Lyric`, y el
    razonamiento va vacio. Asi se reproduce el dropout de condicion del
    entrenamiento; envolverlo dejaria el estilo y la letra identicos en las dos
    ramas y el CFG solo amplificaria la direccion de los metadatos.
    """
    usuario = prompt_negativo if hay_prompt_negativo(prompt_negativo) else SIN_ENTRADA_USUARIO
    return _envolver(tokenizer, usuario) + _COT_VACIO + "\n\n"


def metadatos_a_cot(metadatos: Dict[str, Any]) -> str:
    """Reserializa los metadatos como bloque `<think>` en YAML.

    El orden de los campos lo fija `sort_keys=True`, que resulta ser el mismo
    orden en que los genera el automata (bpm, caption, duration, keyscale,
    language, timesignature son alfabeticos). Coincidencia comprobada, no
    supuesta.
    """
    elementos: Dict[str, Any] = {}
    for campo in CAMPOS_COT:
        valor = metadatos.get(campo)
        if valor is None:
            continue
        # MODIFICADO respecto a upstream: upstream hace `value.endswith("/4")`
        # sobre el valor tal cual, que revienta con `AttributeError` si el compas
        # llega como entero (que es justo como sale de un `--compas 4` en la
        # linea de ordenes). Aqui se normaliza a texto antes de mirar el sufijo.
        if campo == "timesignature":
            valor = str(valor)
            if valor.endswith("/4"):
                valor = valor.split("/")[0]
        if isinstance(valor, str) and valor.isdigit():
            valor = int(valor)
        elementos[campo] = valor

    cuerpo = yaml.dump(elementos, allow_unicode=True, sort_keys=True).strip() if elementos else ""
    return f"<think>\n{cuerpo}\n</think>"


def parsear_salida(texto: str) -> Tuple[Dict[str, Any], str]:
    """Extrae `(metadatos, cadena_de_codigos)` del texto que genero el LM.

    Los codigos se devuelven como la cadena concatenada de tokens
    `<|audio_code_N|>` porque es la forma en la que upstream los pasa por su API
    (`audio_code_hints`). Para obtener la lista de enteros, usar
    `planificador.codigos_de_texto`.
    """
    metadatos: Dict[str, Any] = {}

    codigos = "".join(re.findall(r"<\|audio_code_\d+\|>", texto))

    razonamiento = None
    for patron in (r"<think>(.*?)</think>", r"<reasoning>(.*?)</reasoning>"):
        emparejado = re.search(patron, texto, re.DOTALL)
        if emparejado:
            razonamiento = emparejado.group(1).strip()
            break
    if not razonamiento:
        razonamiento = (
            texto.split("<|audio_code_")[0] if "<|audio_code_" in texto else texto
        ).strip()

    if razonamiento:
        clave: Optional[str] = None
        acumulado: List[str] = []

        def guardar() -> None:
            nonlocal clave, acumulado
            if clave and acumulado:
                valor = "\n".join(acumulado)
                if clave in ("bpm", "duration"):
                    try:
                        metadatos[clave] = int(valor.strip())
                    except ValueError:
                        metadatos[clave] = valor.strip()
                elif clave == "caption":
                    metadatos[clave] = limpiar_caption(valor)
                elif clave in ("keyscale", "language", "timesignature", "genres"):
                    metadatos[clave] = valor.strip()
            clave = None
            acumulado = []

        for linea in razonamiento.split("\n"):
            if linea.strip().startswith("<"):
                continue
            if linea and not linea[0].isspace() and ":" in linea:
                guardar()
                nombre, _, resto = linea.partition(":")
                clave = nombre.strip().lower()
                if resto.strip():
                    acumulado.append(resto)
            elif linea.startswith((" ", "\t")) and clave:
                acumulado.append(linea)
        guardar()

    return metadatos, codigos
