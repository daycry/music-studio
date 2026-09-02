# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original.
#
# Obra derivada de `acestep/constrained_logits_processor.py`.
#
#   Origen          : github.com/ace-step/ACE-Step-1.5
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866  (2026-08-29)
#   Bytes origen    : 114461
#   SHA-256 origen  : 84cf84ad894130397ba53a4cbd8666961bf578c77295b79599b288a3825faa32
#   blob SHA-1      : 69eeffb56ebb4c1e54b106f25f237ba0fbf6b2ae  (verificado contra
#                     la atestacion del arbol de la API de GitHub)
#   Copiado el      : 2026-09-02
#   Licencia        : MIT (LICENSE de la raiz del repositorio, blob SHA-1
#                     600451d484a555c1273baa2602f32a37fdd0d0ab)
#
# Cada cambio va marcado con "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Decodificacion restringida del planificador de 5 Hz: automata + lista blanca.

Esto NO es un extra
-------------------
Sin este fichero el LM decide **cuantos** codigos emite, y un codigo son 0,2 s
de audio. La duracion pedida deja de ser un contrato y pasa a ser una sugerencia:
se rompe el "+-5 %" de la spec de raiz, no por deriva numerica sino porque nadie
esta pidiendo esa longitud. Con este fichero, el numero de codigos es
**exactamente** `int(duracion * 5)`, forzado token a token.

Que restringe, exactamente
--------------------------
Un automata finito recorre dos regiones del texto que genera el LM:

1. **Razonamiento** (`<think> ... </think>`), campo a campo, en este orden::

       <think>
       bpm: <entero 30..300>
       caption: <texto libre sin acentos graves ni codigos de audio, <=512 tokens>
       duration: <entero 10..DURATION_MAX>
       keyscale: <una de las 70 tonalidades validas>
       language: <uno de los 51 codigos de idioma>
       timesignature: <2 | 3 | 4 | 6>
       </think>

   Los nombres de campo se fuerzan token a token contra la cadena literal. Los
   valores se fuerzan con arboles de prefijos construidos con la tokenizacion
   REAL (no con caracteres: el tokenizador fusiona el espacio del ": " con la
   primera letra del valor, y un arbol construido sobre caracteres se
   desincroniza en el primer paso).

2. **Codigos** (despues de `</think>`), y aqui estan las dos restricciones que
   importan:

   - **Lista blanca de vocabulario.** Solo se permiten los 64.000 tokens
     `<|audio_code_N|>` con `N <= 63999`, mas el EOS. El vocabulario del
     tokenizador tiene 65.535 de esos tokens: los 1.535 sobrantes existen y el
     modelo puede emitirlos, y `quantizer.get_output_from_indices` los indexa
     fuera del libro de codigos. Tambien se bloquea todo el texto, que si no
     compite por la masa de probabilidad.
   - **Contador de duracion.** Mientras `codigos_emitidos < objetivo` el EOS
     esta a `-inf`; en cuanto se alcanza el objetivo, el EOS es el UNICO token
     permitido. No es una parada blanda: es una igualdad.

Que se ha quitado y por que
---------------------------
- **El campo `genres` entero** (vocabulario, trie, coincidencia con el caption,
  recarga en caliente del fichero). Upstream lo pasa siempre a `skip_genres=True`
  desde `generate_with_stop_condition`, y ademas su `genres_vocab.txt` no esta
  vendorizado: la rama de "vocabulario no cargado" degrada a generacion de texto
  SIN restringir, que es exactamente lo que este fichero existe para impedir.
  Son ~500 lineas y una lectura de disco en tiempo de construccion.
- **La fase `understand`** (audio -> metadatos + letra). No la usamos.
- `diagnose_keyscale_prefix_tree`, `_should_end_numeric_field`,
  `_get_allowed_digit_tokens` y `_should_end_text_field`: los dos primeros solo
  se llaman entre si, los otros dos solo desde la rama de `genres`. Codigo
  muerto una vez quitado `genres`.
- **La herencia de `transformers.generation.logits_process.LogitsProcessor`.**
  El bucle de generacion es nuestro (`generacion.py`) y llama al procesador
  directamente, asi que la clase base solo aportaba acoplamiento a la API
  interna de `transformers`, que es justo lo que rompe entre versiones mayores.
"""

from __future__ import annotations

import re
from enum import Enum, auto
from typing import Dict, List, Optional, Sequence, Set, Tuple

import torch

from .constants import (
    BPM_MAX,
    BPM_MIN,
    DURATION_MAX,
    DURATION_MIN,
    MAX_AUDIO_CODE,
    MAX_TOKENS_CAPTION,
    TAMANO_LIBRO_CODIGOS,
    VALID_KEYSCALES,
    VALID_LANGUAGES,
    VALID_TIME_SIGNATURES,
    codigos_para_duracion,
)

__all__ = ["CAMPOS", "EstadoFSM", "ProcesadorRestringido", "limpiar_caption"]


#: Patron de los tokens de codigo de audio del vocabulario del LM.
_PATRON_CODIGO = re.compile(r"^<\|audio_code_(\d+)\|>$")

#: Campos del razonamiento, en el orden en que los genera el automata.
#: MODIFICADO respecto a upstream: sin "genres" (ver docstring del modulo).
CAMPOS = ("bpm", "caption", "duration", "keyscale", "language", "timesignature")


class EstadoFSM(Enum):
    """Estados del automata que guia la generacion de metadatos."""

    THINK_TAG = auto()            # generando "<think>"
    NEWLINE_AFTER_THINK = auto()  # generando el "\n" de despues
    BPM_NAME = auto()             # generando "bpm:"
    BPM_VALUE = auto()            # generando el entero 30..300
    CAPTION_NAME = auto()         # generando "caption:"
    CAPTION_VALUE = auto()        # generando el texto del caption
    DURATION_NAME = auto()        # generando "duration:"
    DURATION_VALUE = auto()       # generando el entero 10..max
    KEYSCALE_NAME = auto()        # generando "keyscale:"
    KEYSCALE_VALUE = auto()       # generando la tonalidad
    LANGUAGE_NAME = auto()        # generando "language:"
    LANGUAGE_VALUE = auto()       # generando el codigo de idioma
    TIMESIG_NAME = auto()         # generando "timesignature:"
    TIMESIG_VALUE = auto()        # generando 2, 3, 4 o 6
    THINK_END_TAG = auto()        # generando "</think>"
    CODES_GENERATION = auto()     # generando codigos de audio
    COMPLETED = auto()            # terminado


def limpiar_caption(caption: str) -> str:
    """Aplana un caption con formato multilinea de YAML a una sola linea.

    Copia literal de `MetadataConstrainedLogitsProcessor.postprocess_caption`.
    Entra ``"Una balada.\\n  Abre con piano.\\n  Y sigue."`` y sale
    ``"Una balada. Abre con piano. Y sigue."``.
    """
    if not caption:
        return caption
    lineas = [linea.strip() for linea in caption.split("\n")]
    return " ".join(linea for linea in lineas if linea)


class ProcesadorRestringido:
    """Automata que enmascara logits para que la salida del LM sea valida.

    Se construye **una vez** por proceso (construye cinco arboles de prefijos y
    dos mascaras de 217.204 elementos) y se reutiliza llamando a
    :meth:`reiniciar` antes de cada generacion.

    El contrato con el bucle de generacion es de dos llamadas por paso:

    1. ``logits = procesador(input_ids, logits)`` antes de muestrear.
    2. ``procesador.actualizar_estado(token)`` despues de muestrear.

    Saltarse la segunda deja el automata congelado en `THINK_TAG` y el
    contador de codigos a cero: el EOS no se forzaria nunca.
    """

    def __init__(
        self,
        tokenizer,
        habilitado: bool = True,
        duracion_maxima: Optional[int] = None,
    ) -> None:
        self.tokenizer = tokenizer
        self.habilitado = habilitado

        # MODIFICADO respecto a upstream: se quita el parametro `debug` y las
        # ~60 llamadas a `logger.debug` que colgaban de el. Upstream usa
        # `loguru`, que NO esta en la imagen; y un log por token en un bucle de
        # 900 pasos no es depuracion, es ruido. Los puntos de observacion que si
        # hacen falta salen por el callback `on_token` de `generacion.py`.

        self.duracion_maxima = duracion_maxima if duracion_maxima is not None else DURATION_MAX

        # Campos que se omiten. `genres` no existe en esta copia.
        self.omitir_caption = False
        self.omitir_idioma = False

        # Valores impuestos por el usuario. Los que no sean None se inyectan
        # token a token en vez de generarse.
        self.metadatos_usuario: Dict[str, Optional[str]] = {campo: None for campo in CAMPOS}

        # Temperaturas por fase (opcionales). Si se usan, el muestreador debe ir
        # a temperatura 1,0 para no aplicarla dos veces.
        self.temperatura_metadatos: Optional[float] = None
        self.temperatura_codigos: Optional[float] = None

        # Restriccion de duracion de la fase de codigos.
        self.duracion_objetivo: Optional[float] = None
        self.codigos_objetivo: Optional[int] = None
        self.codigos_emitidos: int = 0

        # Parar en cuanto se cierre `</think>` (fase 1).
        self.parar_en_razonamiento: bool = False

        # "cot" o "codes".
        self.fase: str = "cot"

        # Estado del automata.
        self.estado = EstadoFSM.THINK_TAG
        self.posicion_en_estado = 0
        self.valor_acumulado = ""
        self.tokens_acumulados: List[int] = []

        # Seguimiento del caption.
        self.caption_tras_salto = False
        self.caption_tokens = 0
        self.caption_terminando = False
        self.nombre_campo_pendiente = ""

        # Cola de inyeccion de campos del usuario.
        self.cola_campo_usuario: List[int] = []
        self.campo_usuario_actual: Optional[str] = None

        self._precalcular_tokens()

        self.especificaciones = {
            "bpm": {"min": BPM_MIN, "max": BPM_MAX},
            "duration": {"min": DURATION_MIN, "max": self.duracion_maxima},
            "timesignature": {"valores": VALID_TIME_SIGNATURES},
        }
        self.valores_bpm = [str(v) for v in range(BPM_MIN, BPM_MAX + 1)]
        self.valores_duracion = [str(v) for v in range(DURATION_MIN, self.duracion_maxima + 1)]
        self.valores_compas = [str(v) for v in VALID_TIME_SIGNATURES]

        self.arbol_tonalidad = self._construir_arbol_tonalidad()
        self.arbol_bpm = self._construir_arbol_numerico(self.valores_bpm, "bpm:", "bpm: ")
        self.arbol_duracion = self._construir_arbol_numerico(
            self.valores_duracion, "duration:", "duration: "
        )
        self.arbol_compas = self._construir_arbol_numerico(
            self.valores_compas, "timesignature:", "timesignature: "
        )
        self.arbol_idioma = self._construir_arbol_idioma()

        # MODIFICADO respecto a upstream: aqui iba `self._load_genres_vocab()`,
        # que abre `genres_vocab.txt` del directorio del modulo. Se ha quitado:
        # este paquete NO lee del disco al construirse.

        self.cadenas_fijas = {
            EstadoFSM.THINK_TAG: "<think>",
            EstadoFSM.NEWLINE_AFTER_THINK: "\n",
            EstadoFSM.BPM_NAME: "bpm:",
            EstadoFSM.CAPTION_NAME: "caption:",
            EstadoFSM.DURATION_NAME: "duration:",
            EstadoFSM.KEYSCALE_NAME: "keyscale:",
            EstadoFSM.LANGUAGE_NAME: "language:",
            EstadoFSM.TIMESIG_NAME: "timesignature:",
            EstadoFSM.THINK_END_TAG: "</think>",
        }

        # MODIFICADO respecto a upstream: memo de `_tokens_de_cadena_fija`. Es
        # funcion pura de (cadena, posicion) y upstream la recalcula en cada
        # paso con hasta 20 llamadas a `tokenizer.encode`.
        self._memo_cadena_fija: Dict[Tuple[str, int], List[int]] = {}

        self._construir_transiciones()

    # ------------------------------------------------------------------ #
    # Precalculo
    # ------------------------------------------------------------------ #

    def _precalcular_tokens(self) -> None:
        """Resuelve los identificadores de token que usa el automata."""
        cod = self.tokenizer.encode

        self.tokens_digito = {}
        for d in range(10):
            tokens = cod(str(d), add_special_tokens=False)
            if tokens:
                self.tokens_digito[d] = tokens[-1]

        saltos = cod("\n", add_special_tokens=False)
        self.token_salto = saltos[-1] if saltos else None

        espacios = cod(" ", add_special_tokens=False)
        self.token_espacio = espacios[-1] if espacios else None

        self.token_eos = self.tokenizer.eos_token_id

        puntos = cod(".", add_special_tokens=False)
        self.token_punto = puntos[-1] if puntos else None

        acentos = cod("`", add_special_tokens=False)
        self.token_acento_grave = acentos[-1] if acentos else None

        self.tamano_vocabulario = len(self.tokenizer)
        self.tonalidades_validas = set(VALID_KEYSCALES)
        self.idiomas_validos = list(VALID_LANGUAGES)

        # MODIFICADO respecto a upstream: upstream descubre los tokens de codigo
        # recorriendo los 217.204 identificadores y llamando a
        # `tokenizer.decode([id])` en cada uno — 217.204 llamadas a la libreria
        # de tokenizacion en cada construccion. Aqui se lee `get_vocab()` una
        # vez (es un dict token->id que ya incluye los anadidos) y se filtra con
        # el mismo patron. Mismo resultado, dos ordenes de magnitud mas rapido,
        # y de paso queda construida la biyeccion codigo <-> token, que upstream
        # rehace mas tarde a base de expresiones regulares sobre el texto
        # decodificado.
        self.token_por_codigo: Dict[int, int] = {}
        self.codigo_por_token: Dict[int, int] = {}
        fuera_de_rango = 0
        for texto, ident in self.tokenizer.get_vocab().items():
            emparejado = _PATRON_CODIGO.match(texto)
            if emparejado is None:
                continue
            valor = int(emparejado.group(1))
            if 0 <= valor <= MAX_AUDIO_CODE:
                self.token_por_codigo[valor] = ident
                self.codigo_por_token[ident] = valor
            else:
                fuera_de_rango += 1
        self.tokens_codigo: Set[int] = set(self.codigo_por_token)
        self.codigos_fuera_de_rango = fuera_de_rango

        # MODIFICADO respecto a upstream: upstream solo emite un `logger.warning`
        # si no encuentra ningun token de codigo. Aqui se rompe: un vocabulario
        # con un numero de codigos distinto de 64.000 significa que el
        # tokenizador no es el del checkpoint, y seguir adelante produciria
        # audio silenciosamente mal condicionado.
        if len(self.tokens_codigo) != TAMANO_LIBRO_CODIGOS:
            raise ValueError(
                f"El vocabulario del tokenizador tiene {len(self.tokens_codigo)} tokens "
                f"<|audio_code_N|> validos y el libro de codigos FSQ del DiT tiene "
                f"{TAMANO_LIBRO_CODIGOS}. Tokenizador y checkpoint no se corresponden."
            )

        self._construir_mascaras_codigos()

    def _construir_mascaras_codigos(self) -> None:
        """Construye las dos mascaras de vocabulario, en CPU y float32."""
        indices = list(self.tokens_codigo)

        # Bloquea los codigos de audio (se usa durante el caption).
        mascara = torch.zeros(1, self.tamano_vocabulario, dtype=torch.float32)
        mascara[0, indices] = float("-inf")
        self.mascara_bloquea_codigos = mascara

        # Bloquea TODO menos los codigos de audio y el EOS (fase de codigos).
        inversa = torch.full((1, self.tamano_vocabulario), float("-inf"), dtype=torch.float32)
        inversa[0, indices] = 0.0
        if self.token_eos is not None:
            inversa[0, self.token_eos] = 0.0
        self.mascara_solo_codigos = inversa

    # ------------------------------------------------------------------ #
    # Arboles de prefijos
    # ------------------------------------------------------------------ #

    def _extraer_tokens_de_valor(
        self, valor: str, prefijo_para_emparejar: str, prefijo_para_tokenizar: str
    ) -> Optional[List[int]]:
        """Tokeniza `prefijo + valor` y devuelve solo los tokens del valor.

        El truco de upstream, y hay que entenderlo o el arbol sale mal: el
        automata emite ``"keyscale:"`` SIN espacio, pero el tokenizador, al ver
        ``"keyscale: G major"``, fusiona el espacio con la G y produce ``" G"``.
        Por eso hay dos prefijos: uno para emparejar lo que el automata ya ha
        emitido y otro para tokenizar como lo vera el modelo.
        """
        tokens_prefijo = (
            self.tokenizer.encode(prefijo_para_emparejar, add_special_tokens=False)
            if prefijo_para_emparejar
            else []
        )
        completos = self.tokenizer.encode(prefijo_para_tokenizar + valor, add_special_tokens=False)
        if len(completos) < len(tokens_prefijo):
            return None
        if completos[: len(tokens_prefijo)] != tokens_prefijo:
            return None
        return completos[len(tokens_prefijo) :]

    def _sembrar_arbol(
        self, arbol: Dict[Tuple[int, ...], Set[int]], tokens_valor: Sequence[int]
    ) -> None:
        """Anade una secuencia completa al arbol de prefijos."""
        for i in range(len(tokens_valor) + 1):
            prefijo = tuple(tokens_valor[:i])
            destino = arbol.setdefault(prefijo, set())
            if i < len(tokens_valor):
                destino.add(tokens_valor[i])
            elif self.token_salto is not None:
                # Valor completo: a partir de aqui solo cabe el salto de linea.
                destino.add(self.token_salto)

    def _construir_arbol_tonalidad(self) -> Dict[Tuple[int, ...], Set[int]]:
        arbol: Dict[Tuple[int, ...], Set[int]] = {}
        for tonalidad in self.tonalidades_validas:
            tokens = self._extraer_tokens_de_valor(tonalidad, "keyscale:", "keyscale: ")
            if not tokens:
                continue
            # El primer token tiene que ser una nota A-G; si no, esa combinacion
            # se descarta (upstream hace la misma comprobacion).
            primero = self.tokenizer.decode([tokens[0]]).lstrip()
            if not primero or primero[0].upper() not in "ABCDEFG":
                continue
            self._sembrar_arbol(arbol, tokens)
        return arbol

    def _construir_arbol_numerico(
        self, valores: Sequence[str], prefijo_emparejar: str, prefijo_tokenizar: str
    ) -> Dict[Tuple[int, ...], Set[int]]:
        arbol: Dict[Tuple[int, ...], Set[int]] = {}
        for valor in valores:
            tokens = self._extraer_tokens_de_valor(valor, prefijo_emparejar, prefijo_tokenizar)
            if tokens is None:
                continue
            self._sembrar_arbol(arbol, tokens)
        return arbol

    def _construir_arbol_idioma(self) -> Dict[Tuple[int, ...], Set[int]]:
        arbol: Dict[Tuple[int, ...], Set[int]] = {}
        for idioma in self.idiomas_validos:
            tokens = self._extraer_tokens_de_valor(idioma, "language:", "language: ")
            if not tokens:
                continue
            self._sembrar_arbol(arbol, tokens)
        return arbol

    # ------------------------------------------------------------------ #
    # Transiciones
    # ------------------------------------------------------------------ #

    def _siguiente_campo(self, campo: str) -> EstadoFSM:
        """Estado NAME del campo siguiente, saltando los omitidos."""
        campo_a_estado = {
            "bpm": EstadoFSM.BPM_NAME,
            "caption": EstadoFSM.CAPTION_NAME,
            "duration": EstadoFSM.DURATION_NAME,
            "keyscale": EstadoFSM.KEYSCALE_NAME,
            "language": EstadoFSM.LANGUAGE_NAME,
            "timesignature": EstadoFSM.TIMESIG_NAME,
        }
        try:
            indice = CAMPOS.index(campo)
        except ValueError:
            return EstadoFSM.THINK_END_TAG
        for siguiente in CAMPOS[indice + 1 :]:
            if siguiente == "caption" and self.omitir_caption:
                continue
            if siguiente == "language" and self.omitir_idioma:
                continue
            return campo_a_estado[siguiente]
        return EstadoFSM.THINK_END_TAG

    def _construir_transiciones(self) -> None:
        self.siguiente_estado = {
            EstadoFSM.THINK_TAG: EstadoFSM.NEWLINE_AFTER_THINK,
            EstadoFSM.NEWLINE_AFTER_THINK: EstadoFSM.BPM_NAME,
            EstadoFSM.THINK_END_TAG: EstadoFSM.CODES_GENERATION,
            EstadoFSM.CODES_GENERATION: EstadoFSM.COMPLETED,
        }
        self.siguiente_estado[EstadoFSM.BPM_NAME] = EstadoFSM.BPM_VALUE
        self.siguiente_estado[EstadoFSM.BPM_VALUE] = self._siguiente_campo("bpm")
        if not self.omitir_caption:
            self.siguiente_estado[EstadoFSM.CAPTION_NAME] = EstadoFSM.CAPTION_VALUE
            self.siguiente_estado[EstadoFSM.CAPTION_VALUE] = self._siguiente_campo("caption")
        self.siguiente_estado[EstadoFSM.DURATION_NAME] = EstadoFSM.DURATION_VALUE
        self.siguiente_estado[EstadoFSM.DURATION_VALUE] = self._siguiente_campo("duration")
        self.siguiente_estado[EstadoFSM.KEYSCALE_NAME] = EstadoFSM.KEYSCALE_VALUE
        self.siguiente_estado[EstadoFSM.KEYSCALE_VALUE] = self._siguiente_campo("keyscale")
        if not self.omitir_idioma:
            self.siguiente_estado[EstadoFSM.LANGUAGE_NAME] = EstadoFSM.LANGUAGE_VALUE
            self.siguiente_estado[EstadoFSM.LANGUAGE_VALUE] = self._siguiente_campo("language")
        self.siguiente_estado[EstadoFSM.TIMESIG_NAME] = EstadoFSM.TIMESIG_VALUE
        self.siguiente_estado[EstadoFSM.TIMESIG_VALUE] = EstadoFSM.THINK_END_TAG

    # ------------------------------------------------------------------ #
    # Configuracion por generacion
    # ------------------------------------------------------------------ #

    def reiniciar(self) -> None:
        """Deja el automata listo para otra generacion. Llamar SIEMPRE antes."""
        self.estado = EstadoFSM.THINK_TAG
        self.posicion_en_estado = 0
        self.valor_acumulado = ""
        self.tokens_acumulados = []
        self.codigos_emitidos = 0
        self.cola_campo_usuario = []
        self.campo_usuario_actual = None
        self.caption_tras_salto = False
        self.caption_tokens = 0
        self.caption_terminando = False
        self.nombre_campo_pendiente = ""

    def fijar_duracion_objetivo(self, duracion: Optional[float]) -> None:
        """Fija la longitud EXACTA en codigos. `None` = sin restriccion.

        Esta es la funcion que hace que la duracion sea un contrato. Con
        `duracion = 30` el automata bloquea el EOS durante 150 codigos y lo
        fuerza en el 151.
        """
        self.duracion_objetivo = duracion
        if duracion is not None and duracion > 0:
            self.codigos_objetivo = codigos_para_duracion(duracion)
        else:
            self.codigos_objetivo = None

    def fijar_duracion_maxima(self, duracion_maxima: int) -> None:
        """Cambia el tope del campo `duration` y reconstruye su arbol."""
        if duracion_maxima == self.duracion_maxima:
            return
        self.duracion_maxima = duracion_maxima
        self.especificaciones["duration"]["max"] = duracion_maxima
        self.valores_duracion = [str(v) for v in range(DURATION_MIN, duracion_maxima + 1)]
        self.arbol_duracion = self._construir_arbol_numerico(
            self.valores_duracion, "duration:", "duration: "
        )

    def fijar_metadatos_usuario(self, metadatos: Optional[Dict[str, Optional[str]]] = None) -> None:
        """Impone valores de campos. Los que valgan None los genera el modelo."""
        metadatos = metadatos or {}
        for campo in CAMPOS:
            self.metadatos_usuario[campo] = metadatos.get(campo)
        self._construir_transiciones()

    def fijar_parar_en_razonamiento(self, parar: bool) -> None:
        """Si es True, fuerza EOS en cuanto se cierra `</think>` (fase 1)."""
        self.parar_en_razonamiento = parar

    def fijar_fase(self, fase: str) -> None:
        """Fase de generacion: "cot" (metadatos) o "codes" (codigos de audio)."""
        # MODIFICADO respecto a upstream: se elimina la fase "understand".
        if fase not in ("cot", "codes"):
            raise ValueError(f"Fase invalida: {fase!r}. Debe ser 'cot' o 'codes'.")
        self.fase = fase

    def fijar_omitir_caption(self, omitir: bool) -> None:
        self.omitir_caption = omitir
        self._construir_transiciones()

    def fijar_omitir_idioma(self, omitir: bool) -> None:
        self.omitir_idioma = omitir
        self._construir_transiciones()

    # ------------------------------------------------------------------ #
    # Utilidades de enmascarado
    # ------------------------------------------------------------------ #

    def _lista_blanca(self, logits: torch.Tensor, permitidos: Sequence[int]) -> None:
        """Deja pasar solo `permitidos`; el resto a -inf. En sitio."""
        if not permitidos:
            logits.fill_(float("-inf"))
            return
        indices = torch.tensor(list(permitidos), device=logits.device, dtype=torch.long)
        guardados = logits[0, indices].clone()
        logits.fill_(float("-inf"))
        logits[0, indices] = guardados

    def _mascara_en(self, mascara: torch.Tensor, logits: torch.Tensor) -> torch.Tensor:
        """Devuelve `mascara` en el dispositivo y dtype de `logits` (con cache)."""
        if mascara.device != logits.device or mascara.dtype != logits.dtype:
            return mascara.to(device=logits.device, dtype=logits.dtype)
        return mascara

    def _escalar_temperatura(self, logits: torch.Tensor) -> torch.Tensor:
        if self.estado in (EstadoFSM.CODES_GENERATION, EstadoFSM.COMPLETED):
            temperatura = self.temperatura_codigos
        else:
            temperatura = self.temperatura_metadatos
        if temperatura is None:
            return logits
        if temperatura <= 0:
            temperatura = 1e-6
        return logits / temperatura

    def _tokens_de_cadena_fija(self, cadena: str) -> List[int]:
        """Tokens que pueden continuar `cadena` desde `posicion_en_estado`.

        Estrategia de upstream: buscar el prefijo MAS LARGO que se codifique en
        un unico token y devolver ese token. Si no hay ninguno, recopilar los
        primeros tokens de los prefijos crecientes y verificar que el texto
        decodificado casa con el prefijo.
        """
        clave = (cadena, self.posicion_en_estado)
        memo = self._memo_cadena_fija.get(clave)
        if memo is not None:
            return memo

        resto = cadena[self.posicion_en_estado :]
        if not resto:
            self._memo_cadena_fija[clave] = []
            return []

        for fin in range(len(resto), 0, -1):
            tokens = self.tokenizer.encode(resto[:fin], add_special_tokens=False)
            if tokens and len(tokens) == 1:
                self._memo_cadena_fija[clave] = [tokens[0]]
                return [tokens[0]]

        candidatos: Dict[int, int] = {}
        for fin in range(1, min(len(resto) + 1, 20)):
            prefijo = resto[:fin]
            tokens = self.tokenizer.encode(prefijo, add_special_tokens=False)
            if not tokens:
                continue
            primero = tokens[0]
            decodificado = self.tokenizer.decode([primero]).lstrip().lower()
            normalizado = prefijo.lstrip().lower()
            if decodificado.startswith(normalizado) or normalizado.startswith(decodificado):
                if primero not in candidatos or fin > candidatos[primero]:
                    candidatos[primero] = fin

        resultado = [t for t, _ in sorted(candidatos.items(), key=lambda par: par[1], reverse=True)]
        self._memo_cadena_fija[clave] = resultado
        return resultado

    def _tokens_campo_usuario(self, campo: str) -> Optional[List[int]]:
        """Tokens de `nombre: valor\\n` para un campo impuesto por el usuario."""
        valor = self.metadatos_usuario.get(campo)
        if valor is None:
            return None
        completos = self.tokenizer.encode(f"{campo}: {valor}\n", add_special_tokens=False)
        prefijo = self.tokenizer.encode(f"{campo}:", add_special_tokens=False)
        if len(completos) >= len(prefijo) and completos[: len(prefijo)] == prefijo:
            return completos[len(prefijo) :]
        return completos

    # ------------------------------------------------------------------ #
    # Punto de entrada del bucle de generacion
    # ------------------------------------------------------------------ #

    def __call__(self, input_ids: torch.Tensor, logits: torch.Tensor) -> torch.Tensor:
        """Enmascara `logits` [B, V] segun el estado del automata."""
        if not self.habilitado:
            return self._escalar_temperatura(logits)

        if self.estado == EstadoFSM.COMPLETED:
            return self._escalar_temperatura(logits)

        # En la fase de codigos el `</think>` ya viene en el prompt: hay que
        # detectarlo y saltar directamente a la generacion de codigos.
        if self.fase == "codes" and self.estado == EstadoFSM.THINK_TAG:
            if self._prompt_cierra_razonamiento(input_ids):
                self.estado = EstadoFSM.CODES_GENERATION
                self.codigos_emitidos = 0

        if self.estado == EstadoFSM.CODES_GENERATION:
            # (1) Lista blanca de vocabulario: solo codigos validos y EOS.
            logits = logits + self._mascara_en(self.mascara_solo_codigos, logits)

            # (2) Contrato de duracion.
            if self.codigos_objetivo is not None and self.token_eos is not None:
                if self.codigos_emitidos < self.codigos_objetivo:
                    logits[:, self.token_eos] = float("-inf")
                else:
                    solo_eos = logits[:, self.token_eos].clone()
                    logits.fill_(float("-inf"))
                    logits[:, self.token_eos] = solo_eos
            return self._escalar_temperatura(logits)

        for b in range(logits.shape[0]):
            logits[b] = self._procesar_secuencia(input_ids[b], logits[b : b + 1])[0]
        return self._escalar_temperatura(logits)

    def _prompt_cierra_razonamiento(self, input_ids: torch.Tensor) -> bool:
        """True si `</think>` aparece ya en la entrada."""
        cierre = self.tokenizer.encode("</think>", add_special_tokens=False)
        if not cierre:
            return False
        n = len(cierre)
        for b in range(input_ids.shape[0]):
            secuencia = input_ids[b].tolist()
            for i in range(len(secuencia) - n + 1):
                if secuencia[i : i + n] == cierre:
                    return True
        return False

    # ------------------------------------------------------------------ #
    # Estados de metadatos
    # ------------------------------------------------------------------ #

    def _intentar_inyectar_campo(self, campo: str, logits: torch.Tensor, vacio: bool) -> bool:
        """Arranca la inyeccion de un campo impuesto por el usuario."""
        if self.metadatos_usuario[campo] is None or self.cola_campo_usuario or not vacio:
            return False
        tokens = self.tokenizer.encode(f" {self.metadatos_usuario[campo]}\n", add_special_tokens=False)
        if not tokens:
            return False
        self.cola_campo_usuario = list(tokens)
        self.campo_usuario_actual = campo
        self._lista_blanca(logits, [tokens[0]])
        return True

    def _permitir_desde_arbol(
        self,
        arbol: Dict[Tuple[int, ...], Set[int]],
        logits: torch.Tensor,
        cerrar_si_completo: bool,
    ) -> None:
        """Aplica el arbol de prefijos al estado actual.

        `cerrar_si_completo` reproduce la asimetria de upstream: en tonalidad,
        idioma y compas, en cuanto el prefijo admite salto de linea se fuerza el
        salto (el valor esta completo y no se permite alargarlo); en BPM y
        duracion se deja el conjunto entero, que ya incluye el salto.
        """
        prefijo = tuple(self.tokens_acumulados)
        permitidos = arbol.get(prefijo)

        if (
            cerrar_si_completo
            and permitidos is not None
            and self.token_salto is not None
            and self.token_salto in permitidos
        ):
            self._lista_blanca(logits, [self.token_salto])
            return

        if permitidos:
            self._lista_blanca(logits, list(permitidos))
            return

        # MODIFICADO respecto a upstream: cuando el arbol no ofrece continuacion,
        # upstream llama a `_apply_whitelist_inplace(scores, [])` para BPM,
        # duracion y compas, que pone TODO el vocabulario a -inf. Lo que sale de
        # ahi es un `multinomial` sobre una distribucion vacia (o un `argmax` que
        # devuelve el token 0): un fallo tardio y sin mensaje. Aqui se cierra el
        # campo con un salto de linea, que es lo que upstream ya hace en
        # tonalidad e idioma. Con los arboles bien construidos esta rama no
        # deberia alcanzarse nunca.
        if self.token_salto is not None:
            self._lista_blanca(logits, [self.token_salto])

    def _procesar_secuencia(self, input_ids: torch.Tensor, logits: torch.Tensor) -> torch.Tensor:
        """Enmascara una sola secuencia [1, V] segun el estado del automata."""
        if self.cola_campo_usuario:
            self._lista_blanca(logits, [self.cola_campo_usuario[0]])
            return logits

        if self.estado in self.cadenas_fijas:
            cadena = self.cadenas_fijas[self.estado]
            permitidos = self._tokens_de_cadena_fija(cadena)

            if permitidos:
                if self.estado == EstadoFSM.THINK_END_TAG and self.parar_en_razonamiento:
                    restantes = len(cadena) - self.posicion_en_estado
                    if restantes <= 10 and self.token_eos is not None:
                        self._lista_blanca(logits, [self.token_eos])
                        return logits
                self._lista_blanca(logits, permitidos)
                return logits

            # La cadena esta completa: transitar.
            if self.estado == EstadoFSM.THINK_END_TAG and self.parar_en_razonamiento:
                if self.token_eos is not None:
                    self._lista_blanca(logits, [self.token_eos])
                    return logits
            self._transitar()
            if self.estado in self.cadenas_fijas:
                # No deberia ocurrir; se evita la recursion infinita.
                return logits
            logits.zero_()
            return self._procesar_secuencia(input_ids, logits)

        if self.estado == EstadoFSM.BPM_VALUE:
            if self._intentar_inyectar_campo("bpm", logits, not self.tokens_acumulados):
                return logits
            self._permitir_desde_arbol(self.arbol_bpm, logits, cerrar_si_completo=False)
            return logits

        if self.estado == EstadoFSM.CAPTION_VALUE:
            return self._procesar_caption(logits)

        if self.estado == EstadoFSM.DURATION_VALUE:
            if self._intentar_inyectar_campo("duration", logits, not self.tokens_acumulados):
                return logits
            if self.duracion_objetivo is not None:
                # Con duracion objetivo se fuerza digito a digito el valor exacto.
                objetivo = str(int(self.duracion_objetivo))
                posicion = len(self.valor_acumulado)
                if posicion < len(objetivo):
                    digito = int(objetivo[posicion])
                    if digito in self.tokens_digito:
                        self._lista_blanca(logits, [self.tokens_digito[digito]])
                elif self.token_salto is not None:
                    self._lista_blanca(logits, [self.token_salto])
                return logits
            self._permitir_desde_arbol(self.arbol_duracion, logits, cerrar_si_completo=False)
            return logits

        if self.estado == EstadoFSM.KEYSCALE_VALUE:
            if self._intentar_inyectar_campo("keyscale", logits, not self.tokens_acumulados):
                return logits
            self._permitir_desde_arbol(self.arbol_tonalidad, logits, cerrar_si_completo=True)
            return logits

        if self.estado == EstadoFSM.LANGUAGE_VALUE:
            return self._procesar_idioma(logits)

        if self.estado == EstadoFSM.TIMESIG_VALUE:
            if self._intentar_inyectar_campo("timesignature", logits, not self.tokens_acumulados):
                return logits
            self._permitir_desde_arbol(self.arbol_compas, logits, cerrar_si_completo=True)
            return logits

        return logits

    def _procesar_caption(self, logits: torch.Tensor) -> torch.Tensor:
        """Caption: texto libre con tres barreras y un final por indentacion."""
        if self._intentar_inyectar_campo("caption", logits, not self.valor_acumulado):
            return logits

        if self.caption_tras_salto:
            # Tras un salto de linea: si el token mas probable NO empieza por
            # espacio o tabulador, el modelo esta empezando el campo siguiente.
            token_cima = int(torch.argmax(logits[0]).item())
            texto_cima = self.tokenizer.decode([token_cima])
            if texto_cima and texto_cima[0] not in " \t":
                self.caption_tras_salto = False
                self.caption_terminando = True
                self.nombre_campo_pendiente = ""
                return logits
            self.caption_tras_salto = False

        if self.caption_terminando:
            # El modelo esta escribiendo el nombre del campo siguiente: se deja
            # libre y `actualizar_estado` detecta los dos puntos.
            return logits

        if self.token_acento_grave is not None:
            logits[0, self.token_acento_grave] = float("-inf")

        logits = logits + self._mascara_en(self.mascara_bloquea_codigos, logits)

        if self.caption_tokens >= MAX_TOKENS_CAPTION and self.token_salto is not None:
            self._lista_blanca(logits, [self.token_salto])

        return logits

    def _procesar_idioma(self, logits: torch.Tensor) -> torch.Tensor:
        """Idioma: se elige el mas probable en el primer token y se fuerza el resto."""
        if self._intentar_inyectar_campo("language", logits, not self.tokens_acumulados):
            return logits

        if not self.tokens_acumulados:
            candidatos = list(self.arbol_idioma.get((), ()))
            if candidatos:
                indices = torch.tensor(candidatos, device=logits.device, dtype=torch.long)
                mejor = int(torch.argmax(logits[0, indices]).item())
                self._lista_blanca(logits, [candidatos[mejor]])
            elif self.token_salto is not None:
                self._lista_blanca(logits, [self.token_salto])
            return logits

        self._permitir_desde_arbol(self.arbol_idioma, logits, cerrar_si_completo=True)
        return logits

    # ------------------------------------------------------------------ #
    # Avance del automata
    # ------------------------------------------------------------------ #

    def _transitar(self) -> None:
        if self.estado not in self.siguiente_estado:
            return
        self.estado = self.siguiente_estado[self.estado]
        self.posicion_en_estado = 0
        self.valor_acumulado = ""
        self.tokens_acumulados = []
        self.caption_tras_salto = False
        self.caption_tokens = 0
        self.caption_terminando = False
        self.nombre_campo_pendiente = ""

    def actualizar_estado(self, token_generado: int) -> None:
        """Avanza el automata con el token que se acaba de muestrear.

        Es la mitad del contrato. En `CODES_GENERATION` esta llamada es la que
        incrementa el contador de codigos; sin ella el EOS jamas se forzaria y
        la duracion volveria a ser libre.
        """
        if not self.habilitado or self.estado == EstadoFSM.COMPLETED:
            return

        if self.estado == EstadoFSM.CODES_GENERATION:
            self.codigos_emitidos += 1
            return

        if self.cola_campo_usuario:
            self.cola_campo_usuario.pop(0)
            if not self.cola_campo_usuario:
                campo = self.campo_usuario_actual
                self.campo_usuario_actual = None
                siguiente = self._siguiente_campo(campo) if campo else None
                if siguiente is not None:
                    self.estado = siguiente
                    self.posicion_en_estado = 0
                    self.valor_acumulado = ""
                    self.tokens_acumulados = []
                else:
                    self._transitar()
            return

        texto = self.tokenizer.decode([token_generado])

        if self.estado in self.cadenas_fijas:
            cadena = self.cadenas_fijas[self.estado]
            self.posicion_en_estado += len(texto)
            if self.posicion_en_estado >= len(cadena):
                if self.estado == EstadoFSM.THINK_END_TAG and self.parar_en_razonamiento:
                    self.estado = EstadoFSM.COMPLETED
                    self.posicion_en_estado = 0
                    self.valor_acumulado = ""
                    self.tokens_acumulados = []
                else:
                    self._transitar()
            return

        if self.estado in (EstadoFSM.BPM_VALUE, EstadoFSM.DURATION_VALUE, EstadoFSM.TIMESIG_VALUE):
            if token_generado == self.token_salto:
                self._transitar()
                return
            self.tokens_acumulados.append(token_generado)
            if texto.strip().isdigit():
                self.valor_acumulado += texto.strip()
            return

        if self.estado in (EstadoFSM.KEYSCALE_VALUE, EstadoFSM.LANGUAGE_VALUE):
            if token_generado == self.token_salto:
                self._transitar()
                return
            self.tokens_acumulados.append(token_generado)
            self.valor_acumulado += texto
            return

        if self.estado == EstadoFSM.CAPTION_VALUE:
            self.caption_tokens += 1
            self.valor_acumulado += texto
            self.caption_tras_salto = "\n" in texto

            if self.caption_terminando:
                self.nombre_campo_pendiente += texto
                if ":" in texto:
                    nombre = self.nombre_campo_pendiente.strip().rstrip(":").strip().lower()
                    campo_a_valor = {
                        "duration": EstadoFSM.DURATION_VALUE,
                        "keyscale": EstadoFSM.KEYSCALE_VALUE,
                        "language": EstadoFSM.LANGUAGE_VALUE,
                        "timesignature": EstadoFSM.TIMESIG_VALUE,
                    }
                    self.caption_terminando = False
                    self.nombre_campo_pendiente = ""
                    if nombre in campo_a_valor:
                        self.estado = campo_a_valor[nombre]
                        self.posicion_en_estado = 0
                        self.valor_acumulado = ""
                        self.tokens_acumulados = []
                    else:
                        self._transitar()
            return
