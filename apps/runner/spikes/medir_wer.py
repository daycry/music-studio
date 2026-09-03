#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Instrumento de PUNTUACION de G1: el WER del criterio 4, y la puerta que lo custodia.

Que es esto y que NO es
=======================
`g1_generar.py` produce el material; esto **mide una de las dos cifras
objetivas** del gate: el WER de la letra cantada (`g1-protocolo.md` §6.2), que
el §2 somete a dos umbrales — **media <= 15 %** sobre las 10 pistas propias
**y** **peor caso <= 25 %**.

**No puntua** las cinco dimensiones de la rubrica (§3) — eso es escucha
humana —, ni calcula CLAP (§6.1), ni emite veredicto.

Las tres capas, y por que estan separadas
=========================================
**Capa 1 — la aritmetica.** Distancia de edicion sobre palabras, biblioteca
estandar pura, sin dependencias y sin modelos. Es la parte que se puede probar
con verdad conocida ("10 palabras, una mal, 10 %") y que por tanto **se puede
creer**. Corre en cualquier interprete, hoy, sin GPU y sin descargar nada.

**Capa 2 — la puerta.** CLAUDE.md exige **licencia comercial verificada ANTES
de integrar** cualquier herramienta del pipeline, y §9.1 precondicion 9 pone esa
verificacion del lado del propietario. Sin una ficha comprobada que llegue **de
fuera**, este modulo se niega a medir y dice exactamente que le falta.

**Capa 3 — el transcriptor real** (`TranscriptorLocal`). Carga con
`transformers` unos pesos que **ya estan en disco**, puestos ahi por quien
verifico su licencia. Se cargo `HeartMuLa/HeartTranscriptor-oss` (Apache-2.0,
Whisper medium ajustado a musica), pero la clase no lo nombra ni lo presupone:
lo que sabe es cargar un directorio local de la familia Whisper.

Lo que la capa 3 **no** hace, y son invariantes, no preferencias:

* **no descarga nada** — `local_files_only=True` en cada `from_pretrained`, y la
  ruta es un directorio de disco, jamas un identificador de hub;
* **no ejecuta codigo de terceros** — `trust_remote_code=False` explicito, y
  antes de cargar nada `auditar_directorio_modelo()` rechaza el directorio si
  trae un `.py`, un `auto_map` o un `custom_pipelines`;
* **no toca un pickle** — `use_safetensors=True`, y la misma auditoria rechaza el
  directorio si convive un `.bin`/`.pt`/`.ckpt` con los pesos buenos, porque un
  formato alternativo al lado es un cargador esperando equivocarse (D-14);
* **no se importa sola** — `torch` y `transformers` se importan **dentro** del
  metodo de carga. Importar este modulo sigue costando lo que costaba: la capa 1
  y la puerta siguen siendo biblioteca estandar y siguen corriendo sin modelo.

Separar las capas es lo que permite que la 1 y la 2 esten probadas sin pesos, y
que la suite siga verde en una maquina que no los tenga (los tests que los
necesitan se saltan con `skipif`).

La decision de las TILDES, que este proyecto ya pago cara
========================================================
`medir_wer()` **conserva tildes y enye por defecto**, y esa es la decision.

1. **La manda el protocolo.** §6.2, fila de normalizacion, es literal: «se
   conservan las tildes y la "n" con virgulilla». No es una preferencia de este
   fichero; es el criterio fijado **antes** de escuchar, y el §2 lo blinda con
   su regla de inmutabilidad. Cambiarlo ahora seria mover la definicion del
   numero despues de fijar el umbral.
2. **Quitarlas regala aciertos que no existen.** «sonar» y «soñar» son palabras
   distintas: si el transcriptor escribe una donde la letra dice la otra, el
   oyente tampoco entendio lo que se canto — que es exactamente lo que D4 y el
   WER miden. Igualarlas convertiria un error de inteligibilidad real en un cero.
   El proyecto ya se quemo con esto en el otro extremo del pipeline
   (`g1_generar.py`, cabecera, punto 2): una letra sin tildes se canta distinto.
3. **El sesgo que introduce se ve, y se mide.** El riesgo contrario es real: un
   transcriptor que sistematicamente no acentua inflaria el WER por un defecto
   suyo, no del cantante. Ese sesgo **no se disimula relajando la norma**: se
   mide, y aparece en el **suelo** (`medir_suelo()`), que se calcula con esta
   misma normalizacion. Un suelo alto por tildes es informacion util; una norma
   laxa solo esconde el problema.

Por eso hay un segundo modo, `NORMALIZACION_SIN_TILDES`, **de diagnostico**:
sirve para responder «¿cuanto de mi WER es solo acentos?» y su respuesta se
escribe como observacion. Lleva `apta_para_acta=False` y `medir_pista()` la
rechaza si la medida va al acta.

El suelo del transcriptor: sin ese numero, el 15 % no significa nada
====================================================================
§6.2 lo advierte por escrito antes de que haya cifras: «un WER medido con un
transcriptor sobre **voz cantada** no es un WER de voz hablada; el transcriptor
**tambien se equivoca**».

Un 12 % puede ser un modelo musical excelente medido con un transcriptor malo, o
uno mediocre medido con uno impecable, y **la cifra sola no distingue los dos
casos**. Por eso `medir_suelo()` mide el WER del transcriptor sobre **audio de
voz clara de referencia** cuya transcripcion se conoce, con la misma
normalizacion y el mismo idioma forzado, y `resumir()` **se declara
`interpretable=False` mientras no se le pase ese suelo**.

Tres avisos sobre el suelo, para que no se use de mas:

* **No se resta al numero del gate.** §2 es inequivoco: los umbrales «se aplican
  tal cual». `media_menos_suelo` es **informativo** y no toca `cumple_media`.
  Restarlo para pasar seria degradar un umbral con aritmetica.
* **Es un suelo de voz HABLADA clara, y por tanto una COTA INFERIOR del suelo
  que el mismo transcriptor tendria sobre CANTO**, que es mas dificil: melodia,
  vocales alargadas, notas sostenidas, instrumentos de fondo. Es la limitacion
  que hay que decir en voz alta, y tiene dos consecuencias de signo contrario
  que conviene no confundir:

  1. **Presentado como «el error del transcriptor», FAVORECE AL TRANSCRIPTOR.**
     El numero que sale aqui es el que comete en su caso facil, no en el del
     gate. Publicarlo sin la etiqueta lo hace parecer mas fiable de lo que es
     sobre el material que de verdad se mide.
  2. **Restado de la media, PERJUDICA AL GENERADOR.** `media - suelo_habla` deja
     un residuo mayor que `media - suelo_canto`, asi que atribuye al modelo
     musical mas error del que le toca. Por eso `media_menos_suelo` **no es «el
     error del generador»** y no se puede leer asi.

  La trampa que esto impide es la tercera lectura, la que si haria pasar un gate
  que no pasa: **estimar** un suelo de canto (mayor) y restarlo. Ese numero no
  esta medido, §2 no lo admite y este modulo no lo calcula.
* **Es del transcriptor concreto que lo midio.** Un suelo no viaja: cambiar de
  transcriptor obliga a medirlo otra vez, como obliga a repetir G1-bis.

Uso
===
La capa 1 no necesita nada instalado::

    python apps/runner/spikes/medir_wer.py comparar letra.txt transcripcion.txt

Comprobar que una ficha de transcriptor pasa la puerta (sin medir nada)::

    python apps/runner/spikes/medir_wer.py ficha D:/srv/transcriptor/ficha.json

Transcribir de verdad una pista, con su cronometro (necesita torch y
transformers, y los pesos que declare la ficha)::

    python apps/runner/spikes/medir_wer.py transcribir D:/srv/whisper/ficha.json pista.wav --idioma es

Medir el SUELO del transcriptor sobre un corpus de voz clara con licencia
declarada::

    python apps/runner/spikes/medir_wer.py suelo D:/srv/whisper/ficha.json D:/srv/whisper/suelo/corpus.json

Comprobar que los umbrales de aqui siguen siendo los del protocolo::

    python apps/runner/spikes/medir_wer.py umbrales
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Protocol, Sequence, runtime_checkable

# --------------------------------------------------------------------------- #
# Arranque de sys.path (los spikes son scripts sueltos hasta T-10, tras el gate)
# --------------------------------------------------------------------------- #
_AQUI = Path(__file__).resolve()
_RUNNER_ROOT = _AQUI.parents[1]  # apps/runner
if str(_RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNNER_ROOT))

from contracts import (  # noqa: E402  (tras el arranque de sys.path)
    UnsafeWeightsFormat,
    assert_safetensors,
    assert_safetensors_header,
)

__all__ = [
    # Capa 1
    "Normalizacion",
    "NORMALIZACION_PROTOCOLO",
    "NORMALIZACION_SIN_TILDES",
    "IGUAL",
    "SUSTITUCION",
    "INSERCION",
    "BORRADO",
    "Operacion",
    "ResultadoWer",
    "ReferenciaVacia",
    "normalizar",
    "medir_wer",
    "formatear_alineacion",
    # Capa 2
    "SCHEMA_FICHA",
    "LICENCIAS_COMERCIALES",
    "FichaTranscriptor",
    "Transcriptor",
    "TranscriptorDePrueba",
    "ErrorDePuerta",
    "FichaAusente",
    "FichaInvalida",
    "LicenciaNoPermitida",
    "TranscriptorNoAptoParaActa",
    "cargar_ficha",
    "exigir_apto_para_acta",
    "MedicionPista",
    "medir_pista",
    # Capa 3 — el transcriptor real
    "SR_TRANSCRIPTOR",
    "SUFIJOS_PESOS_NO_SAFETENSORS",
    "SUFIJOS_CODIGO",
    "CLAVES_CODIGO_REMOTO",
    "AudioNoSoportado",
    "DependenciaAusente",
    "ModeloNoAuditable",
    "ModeloConCodigoRemoto",
    "ModeloConPesosInseguros",
    "AuditoriaModelo",
    "auditar_directorio_modelo",
    "leer_wav_mono_16k",
    "TranscriptorLocal",
    "transcriptor_desde_ficha",
    # Suelo y resumen
    "AVISO_SUELO_ES_COTA_INFERIOR",
    "SCHEMA_CORPUS_SUELO",
    "LICENCIAS_CORPUS_SUELO",
    "CorpusInvalido",
    "MuestraSuelo",
    "CorpusSuelo",
    "cargar_corpus_suelo",
    "Suelo",
    "medir_suelo",
    "ResumenG1",
    "resumir",
    # Umbrales
    "UMBRAL_WER_MEDIA",
    "UMBRAL_WER_PEOR",
    "UmbralesDerivados",
    "verificar_umbrales",
]


# =========================================================================== #
# CAPA 1 — normalizacion
# =========================================================================== #

@dataclass(frozen=True)
class Normalizacion:
    """Que se le hace al texto antes de comparar. Se declara con el resultado.

    Es un objeto y no una pila de argumentos sueltos justamente para que viaje
    **pegado a la cifra**: un WER sin decir como se normalizo no es reproducible
    en G1-bis, y §6.2 exige archivar «el texto normalizado de ambos».
    """

    nombre: str
    """Como se cita en el acta. `medir_wer` lo copia al resultado."""

    apta_para_acta: bool
    """Si `False`, la cifra que produce es de diagnostico y no cierra el gate."""

    minusculas: bool = True
    quitar_puntuacion: bool = True
    quitar_corchetes: bool = True
    conservar_tildes: bool = True
    """Ver la cabecera del modulo. `False` solo en el modo de diagnostico."""


#: La del §6.2, palabra por palabra. Es la unica con la que se cierra el gate.
NORMALIZACION_PROTOCOLO = Normalizacion(
    nombre="protocolo-g1-6.2",
    apta_para_acta=True,
)

#: Diagnostico: responde «¿cuanto de este WER son solo acentos?». Su cifra se
#: escribe como observacion en `g1-resultado.md`, nunca como el numero del gate.
NORMALIZACION_SIN_TILDES = Normalizacion(
    nombre="diagnostico-sin-tildes",
    apta_para_acta=False,
    conservar_tildes=False,
)

_RE_CORCHETES = re.compile(r"\[[^\]]*\]")

#: Apostrofos que unen una contraccion. Se **borran** en vez de separar, para que
#: «don't» sea un token y no dos: partirla inventaria una insercion que nadie
#: canto. §6.2: «las contracciones se dejan tal cual».
_APOSTROFOS = frozenset("'\u2018\u2019\u02bc\u00b4")

_RE_DIGITO = re.compile(r"\d")


def _escrituras(palabra: str) -> frozenset[str]:
    """Las escrituras (latina, cirilica, han...) que aparecen en una palabra.

    Se saca del nombre Unicode de cada letra («CYRILLIC SMALL LETTER IE» ->
    CYRILLIC), que es la forma barata de hacerlo sin tabla propia. Los
    diacriticos latinos no cuentan como otra escritura: «á» sigue siendo LATIN.
    """
    nombres = set()
    for caracter in palabra:
        if caracter.isalpha():
            try:
                nombres.add(unicodedata.name(caracter).split()[0])
            except ValueError:  # sin nombre en la base de datos Unicode
                nombres.add("DESCONOCIDA")
    return frozenset(nombres)


def _quitar_diacriticos(texto: str) -> str:
    """Descompone y tira las marcas combinantes: «cantará» -> «cantara», «ñ» -> «n»."""
    descompuesto = unicodedata.normalize("NFD", texto)
    return unicodedata.normalize(
        "NFC", "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    )


def _es_alfanumerico(caracter: str) -> bool:
    return caracter.isalnum()


def normalizar(texto: str, norma: Normalizacion = NORMALIZACION_PROTOCOLO) -> tuple[str, ...]:
    """Aplica `norma` y devuelve las palabras. La MISMA se aplica a los dos textos.

    Que hace, en orden, y por que ese orden:

    1. **NFC.** Dos formas de escribir «á» (precompuesta y descompuesta) tienen
       que ser la misma palabra. Sin esto, la referencia y la transcripcion
       podrian diferir en bytes siendo identicas a la vista.
    2. **Marcas de seccion** `[verse]`, `[chorus]`: fuera. No se cantan (§4.1).
    3. **Minusculas.**
    4. **Diacriticos**, solo si la norma lo pide. Ver la cabecera del modulo.
    5. **Puntuacion**: el apostrofo interior se borra (contracciones); el resto
       de puntuacion y simbolos se sustituye por espacio, para que «hola,adios»
       no acabe siendo una sola palabra inventada.
    6. **Espacios colapsados** y partido en palabras.

    Lo que **no** hace, a proposito: **no convierte digitos a palabras**. §6.2
    pide que los numeros vengan ya escritos en palabras, y deletrearlos en dos
    idiomas es un subsistema con sus propios errores que se colarian en la cifra
    del gate en silencio. Si sobrevive un digito, `medir_wer()` **avisa** y la
    resolucion es a mano.
    """
    texto = unicodedata.normalize("NFC", texto)
    if norma.quitar_corchetes:
        texto = _RE_CORCHETES.sub(" ", texto)
    if norma.minusculas:
        texto = texto.lower()
    if not norma.conservar_tildes:
        texto = _quitar_diacriticos(texto)

    if norma.quitar_puntuacion:
        salida: list[str] = []
        for i, caracter in enumerate(texto):
            if caracter in _APOSTROFOS:
                anterior = texto[i - 1] if i else ""
                siguiente = texto[i + 1] if i + 1 < len(texto) else ""
                # Interior de palabra -> se borra; en cualquier otro sitio, separa.
                salida.append("" if _es_alfanumerico(anterior) and _es_alfanumerico(siguiente) else " ")
            elif unicodedata.category(caracter)[0] in ("P", "S"):
                salida.append(" ")
            else:
                salida.append(caracter)
        texto = "".join(salida)

    return tuple(texto.split())


# =========================================================================== #
# CAPA 1 — la aritmetica del WER
# =========================================================================== #

IGUAL = "igual"
SUSTITUCION = "sustitucion"
INSERCION = "insercion"
BORRADO = "borrado"


class Operacion(NamedTuple):
    """Un paso de la alineacion. El acta necesita ver QUE fallo, no solo cuanto."""

    tipo: str
    referencia: str | None
    hipotesis: str | None
    posicion: int
    """Indice de la palabra en la REFERENCIA (para una insercion, donde cae)."""


class ResultadoWer(NamedTuple):
    wer: float
    """Fraccion `(S + D + I) / N`. **No se recorta a 1,0**: con mas inserciones
    que palabras de referencia, un WER > 100 % es la verdad y esconderla
    convertiria una alucinacion del transcriptor en un aprobado."""

    wer_pct: float
    sustituciones: int
    inserciones: int
    borrados: int
    aciertos: int
    n_referencia: int
    alineacion: tuple[Operacion, ...]
    normalizacion: Normalizacion
    referencia_normalizada: tuple[str, ...]
    hipotesis_normalizada: tuple[str, ...]
    avisos: tuple[str, ...]


class ReferenciaVacia(ValueError):
    """La referencia no tiene ni una palabra: `N = 0` y el WER no existe."""


def _alinear(ref: Sequence[str], hip: Sequence[str]) -> tuple[Operacion, ...]:
    """Levenshtein sobre palabras con reconstruccion del camino.

    Coste 1 para sustitucion, insercion y borrado — la definicion estandar del
    WER, la misma que usa `jiwer` (§6.2, «con la definicion estandar»). La
    matriz completa se guarda porque el camino es parte del entregable: una
    cifra sin alineacion no deja mirar el error.

    Coste O(N*M) en tiempo y memoria. Sobra para letras de cancion (cientos de
    palabras); si algun dia se midiera un audiolibro, habria que trocear.
    """
    n, m = len(ref), len(hip)
    dist = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dist[i][0] = i
    for j in range(1, m + 1):
        dist[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hip[j - 1]:
                dist[i][j] = dist[i - 1][j - 1]
            else:
                dist[i][j] = 1 + min(
                    dist[i - 1][j - 1],  # sustitucion
                    dist[i][j - 1],      # insercion
                    dist[i - 1][j],      # borrado
                )

    pasos: list[Operacion] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hip[j - 1] and dist[i][j] == dist[i - 1][j - 1]:
            pasos.append(Operacion(IGUAL, ref[i - 1], hip[j - 1], i - 1))
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dist[i][j] == dist[i - 1][j - 1] + 1:
            pasos.append(Operacion(SUSTITUCION, ref[i - 1], hip[j - 1], i - 1))
            i, j = i - 1, j - 1
        elif j > 0 and dist[i][j] == dist[i][j - 1] + 1:
            pasos.append(Operacion(INSERCION, None, hip[j - 1], i))
            j -= 1
        else:
            pasos.append(Operacion(BORRADO, ref[i - 1], None, i - 1))
            i -= 1
    pasos.reverse()
    return tuple(pasos)


def medir_wer(
    referencia: str,
    hipotesis: str,
    norma: Normalizacion = NORMALIZACION_PROTOCOLO,
) -> ResultadoWer:
    """`WER = (S + D + I) / N` sobre palabras, con desglose y alineacion (§6.2).

    Args:
        referencia: la letra literal enviada al modelo, sin marcas de seccion.
        hipotesis: lo que el transcriptor entendio.
        norma: como se normalizan **los dos** textos. Por defecto, la del §6.2.

    Levanta:
        ReferenciaVacia: si tras normalizar la referencia no queda ni una
            palabra. Es un error y no un `0 %` ni un `100 %`: el denominador del
            WER es `N`, y con `N = 0` no hay cifra que dar. Devolver cualquier
            numero aqui meteria en el acta una media calculada sobre una pista
            que en realidad no se midio.
    """
    ref = normalizar(referencia, norma)
    hip = normalizar(hipotesis, norma)
    if not ref:
        raise ReferenciaVacia(
            "La referencia se queda sin palabras al normalizarla, asi que N = 0 y el "
            "WER no esta definido (su denominador es N). Comprueba que la letra del "
            "brief no esta vacia y que no es solo marcas de seccion: §4.1 archiva la "
            "referencia YA sin marcas, y es esa la que hay que pasar aqui."
        )

    alineacion = _alinear(ref, hip)
    tipos = [op.tipo for op in alineacion]
    sustituciones = tipos.count(SUSTITUCION)
    inserciones = tipos.count(INSERCION)
    borrados = tipos.count(BORRADO)
    aciertos = tipos.count(IGUAL)

    n = len(ref)
    wer = (sustituciones + borrados + inserciones) / n

    avisos: list[str] = []
    digitos_ref = [p for p in ref if _RE_DIGITO.search(p)]
    digitos_hip = [p for p in hip if _RE_DIGITO.search(p)]
    if digitos_ref or digitos_hip:
        avisos.append(
            "Sobreviven digitos tras normalizar "
            f"(referencia: {digitos_ref or 'ninguno'}; transcripcion: {digitos_hip or 'ninguno'}). "
            "§6.2 pide los numeros ESCRITOS EN PALABRAS y este modulo no los deletrea a "
            "proposito: hacerlo en dos idiomas es una fuente de error propia que se colaria "
            "en la cifra del gate. Reescribelos a mano en los dos textos, o el «3» frente a "
            "«tres» contara como sustitucion sin que el cantante se haya equivocado."
        )

    # Escrituras mezcladas. Esto no es teorico: medido el 2026-09-03 sobre el
    # corpus del suelo, el transcriptor escribio «conflatеd» con una «е» CIRILICA
    # dentro de una palabra por lo demas latina. A la vista es la misma palabra;
    # para el WER es una sustitucion, y quien mire la alineacion no vera por que.
    # Se AVISA y no se arregla, por lo mismo que con los digitos: normalizar
    # homoglifos aqui cambiaria la definicion del numero despues de fijar el
    # umbral (§2). La resolucion es a mano, en la transcripcion.
    escrituras_ref = frozenset().union(*(_escrituras(p) for p in ref)) if ref else frozenset()
    mezcladas = [p for p in hip if len(_escrituras(p)) > 1]
    ajenas = sorted(
        (frozenset().union(*(_escrituras(p) for p in hip)) if hip else frozenset())
        - escrituras_ref
    )
    if mezcladas:
        avisos.append(
            f"Palabras con escrituras MEZCLADAS en la transcripcion: {mezcladas}. Un "
            "homoglifo (una «е» cirilica dentro de una palabra latina, por ejemplo) se ve "
            "igual pero no es la misma letra, y cuenta como sustitucion sin que se pueda "
            "ver por que en la alineacion. Corrigelo a mano en la transcripcion."
        )
    elif ajenas:
        avisos.append(
            f"La transcripcion trae letras de escrituras que la referencia no usa: {ajenas}. "
            "Suele ser el transcriptor derivando de idioma en un tramo (§6.2 fuerza el "
            "idioma justamente para evitarlo). Mira ese tramo antes de dar la cifra por buena."
        )

    if not norma.apta_para_acta:
        avisos.append(
            f"Normalizacion {norma.nombre!r}: cifra de DIAGNOSTICO. No es la del §6.2 y no "
            "puede ir al acta como el WER del criterio 4."
        )

    return ResultadoWer(
        wer=wer,
        wer_pct=wer * 100.0,
        sustituciones=sustituciones,
        inserciones=inserciones,
        borrados=borrados,
        aciertos=aciertos,
        n_referencia=n,
        alineacion=alineacion,
        normalizacion=norma,
        referencia_normalizada=ref,
        hipotesis_normalizada=hip,
        avisos=tuple(avisos),
    )


def formatear_alineacion(resultado: ResultadoWer, solo_fallos: bool = True) -> str:
    """La alineacion en texto, para pegarla en `07-metricas/` y poder mirarla."""
    lineas = []
    for op in resultado.alineacion:
        if solo_fallos and op.tipo == IGUAL:
            continue
        ref = op.referencia if op.referencia is not None else "-"
        hip = op.hipotesis if op.hipotesis is not None else "-"
        lineas.append(f"  [{op.posicion:>4}] {op.tipo:<12} ref={ref!r:<20} oido={hip!r}")
    if not lineas:
        return "  (sin diferencias)"
    return "\n".join(lineas)


# =========================================================================== #
# CAPA 2 — la ficha del transcriptor y su puerta
# =========================================================================== #

#: Version del esquema de la ficha. Igual que en `model_cards.py`: una ficha de
#: un esquema desconocido se RECHAZA, no se interpreta a medias.
SCHEMA_FICHA = 1

#: Lista BLANCA de licencias con uso comercial verificado para este proyecto.
#: Blanca y no negra a proposito: lo que nadie ha comprobado no pasa. Anadir una
#: exige un commit, que es justo el punto de control que CLAUDE.md pide
#: («licencias comerciales verificadas ANTES de integrar»). El caso que costo
#: dinero real aqui fue Demucs, con pesos CC-BY-NC descubiertos tarde.
LICENCIAS_COMERCIALES = frozenset({
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "CC0-1.0",
    "CC-BY-4.0",
    "Unlicense",
})

_CAMPOS_OBLIGATORIOS = (
    "identificador",
    "version",
    "ruta_pesos",
    "licencia_spdx",
    "sha256_pesos",
    "licencia_verificada_por",
    "licencia_verificada_el",
    "fuente_licencia",
)

_RE_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ErrorDePuerta(RuntimeError):
    """Base de todo lo que impide medir. Se sale por arriba, nunca se ignora."""


class FichaAusente(ErrorDePuerta):
    """No hay ficha donde se dijo que estaria."""


class FichaInvalida(ErrorDePuerta):
    """La ficha existe pero no acredita lo que tiene que acreditar."""


class LicenciaNoPermitida(FichaInvalida):
    """La licencia declarada no esta en la lista de uso comercial verificado."""


class TranscriptorNoAptoParaActa(ErrorDePuerta):
    """Se pidio una cifra para el acta con algo que no puede producirla."""


class FichaTranscriptor(NamedTuple):
    """Lo que hay que saber de unos pesos ANTES de dejarles tocar el gate.

    Los cuatro datos que exige el encargo — **ruta local, identificador,
    licencia SPDX y hash** — mas quien verifico la licencia, cuando y contra que
    fuente. Sin los tres ultimos, «licencia verificada» es una palabra: §6.2
    exige archivar «modelo, version, SHA-256 de pesos y parametros», y §9.1
    ítem 9 pone la verificacion del lado del propietario.
    """

    identificador: str
    version: str
    ruta_pesos: Path
    licencia_spdx: str
    sha256_pesos: str
    licencia_verificada_por: str
    licencia_verificada_el: str
    fuente_licencia: str
    ruta_ficha: Path

    def para_acta(self) -> dict[str, str]:
        """Las lineas que se copian a `07-metricas/README.md` (§6.2)."""
        return {
            "modelo": f"{self.identificador}@{self.version}",
            "pesos": str(self.ruta_pesos),
            "sha256_pesos": self.sha256_pesos,
            "licencia_spdx": self.licencia_spdx,
            "licencia_verificada_por": self.licencia_verificada_por,
            "licencia_verificada_el": self.licencia_verificada_el,
            "fuente_licencia": self.fuente_licencia,
        }


def _sha256_fichero(ruta: Path) -> str:
    digest = hashlib.sha256()
    with open(ruta, "rb") as fichero:
        for bloque in iter(lambda: fichero.read(1 << 20), b""):
            digest.update(bloque)
    return digest.hexdigest()


def cargar_ficha(ruta: str | os.PathLike[str], verificar_hash: bool = True) -> FichaTranscriptor:
    """Lee la ficha del transcriptor y comprueba que acredita lo que dice.

    **Este modulo no descarga ni instala nada.** La ficha y los pesos llegan de
    fuera, puestos por el propietario, que es quien puede verificar una licencia
    (§9.1, precondicion 9). Aqui solo se comprueba, en este orden:

    1. que la ficha exista y sea JSON de un esquema conocido;
    2. que **no falte ningun campo** — y se enumeran todos los que faltan de una
       vez, no el primero, para no obligar a descubrirlos de uno en uno;
    3. que la licencia este en `LICENCIAS_COMERCIALES` (lista blanca);
    4. que los pesos sean `.safetensors` **por nombre y por cabecera** — se
       reutilizan las dos puertas de D-14 de `contracts.py` en vez de escribir
       una tercera version del mismo criterio;
    5. que el SHA-256 cuadre con el fichero que hay en disco.

    El paso 5 verifica **integridad, no inocuidad** (D-14): un safetensors con
    hash correcto puede traer pesos manipulados. Lo que hace que cargarlo no sea
    ejecucion remota de codigo es el paso 4, no este.
    """
    ruta_ficha = Path(ruta)
    if not ruta_ficha.is_file():
        raise FichaAusente(
            f"No hay ficha de transcriptor en {ruta_ficha}. Sin ella este modulo NO mide: "
            "el transcriptor es una herramienta de terceros y CLAUDE.md exige licencia "
            "comercial verificada ANTES de integrarla. La ficha la escribe el propietario "
            f"y debe declarar: {', '.join(_CAMPOS_OBLIGATORIOS)}."
        )

    try:
        documento = json.loads(ruta_ficha.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FichaInvalida(f"Ficha ilegible ({ruta_ficha}): {exc}") from exc

    if not isinstance(documento, dict):
        raise FichaInvalida(f"La ficha {ruta_ficha} no es un objeto JSON.")

    schema = documento.get("schema")
    if schema != SCHEMA_FICHA:
        raise FichaInvalida(
            f"schema {schema!r}: este modulo entiende el {SCHEMA_FICHA}. Una ficha de un "
            "esquema desconocido no se interpreta a medias."
        )

    faltan = [c for c in _CAMPOS_OBLIGATORIOS
              if not isinstance(documento.get(c), str) or not documento[c].strip()]
    if faltan:
        raise FichaInvalida(
            f"A la ficha {ruta_ficha} le faltan campos obligatorios (o los trae vacios): "
            f"{', '.join(faltan)}. Se enumeran todos de una vez a proposito. "
            "Los tres de verificacion (licencia_verificada_por / _el / fuente_licencia) no "
            "son burocracia: sin ellos «licencia verificada» no es comprobable por nadie."
        )

    licencia = documento["licencia_spdx"].strip()
    if licencia not in LICENCIAS_COMERCIALES:
        raise LicenciaNoPermitida(
            f"Licencia {licencia!r} no esta en la lista de uso comercial verificado "
            f"{sorted(LICENCIAS_COMERCIALES)}. La lista es BLANCA: lo que nadie ha "
            "comprobado no pasa. Si esta licencia si permite uso comercial, se verifica "
            "contra la fuente primaria y se anade con un commit — que es el punto de "
            "control, no un tramite."
        )

    ruta_pesos = Path(documento["ruta_pesos"].strip())
    try:
        assert_safetensors(ruta_pesos)
    except UnsafeWeightsFormat as exc:
        raise FichaInvalida(f"Pesos declarados en {ruta_ficha}: {exc}") from exc

    if not ruta_pesos.is_file():
        raise FichaInvalida(
            f"Los pesos declarados no existen: {ruta_pesos}. Este modulo NO los descarga; "
            "llegan de fuera con su ficha (§9.1, precondicion 9)."
        )

    try:
        assert_safetensors_header(ruta_pesos)
    except UnsafeWeightsFormat as exc:
        raise FichaInvalida(f"Pesos declarados en {ruta_ficha}: {exc}") from exc

    sha_declarado = documento["sha256_pesos"].strip().lower()
    if not _RE_SHA256.match(sha_declarado):
        raise FichaInvalida(
            f"sha256_pesos {sha_declarado!r} no son 64 caracteres hexadecimales."
        )
    if verificar_hash:
        sha_real = _sha256_fichero(ruta_pesos)
        if sha_real != sha_declarado:
            raise FichaInvalida(
                f"El sha256 no cuadra para {ruta_pesos}: la ficha dice {sha_declarado} y el "
                f"fichero es {sha_real}. Verifica INTEGRIDAD, no inocuidad (D-14): lo que "
                "impide que cargarlo sea RCE es que sea un safetensors, no este hash."
            )

    return FichaTranscriptor(
        identificador=documento["identificador"].strip(),
        version=documento["version"].strip(),
        ruta_pesos=ruta_pesos,
        licencia_spdx=licencia,
        sha256_pesos=sha_declarado,
        licencia_verificada_por=documento["licencia_verificada_por"].strip(),
        licencia_verificada_el=documento["licencia_verificada_el"].strip(),
        fuente_licencia=documento["fuente_licencia"].strip(),
        ruta_ficha=ruta_ficha,
    )


# --------------------------------------------------------------------------- #
# La interfaz minima que cumplen el doble de pruebas y el transcriptor real
# --------------------------------------------------------------------------- #

@runtime_checkable
class Transcriptor(Protocol):
    """Lo minimo que tiene que ofrecer un transcriptor para servir a §6.2.

    Deliberadamente diminuto — ruta de audio e idioma, devuelve texto — para que
    la aritmetica del WER no dependa de con que se transcribio. Lo cumplen el
    doble de pruebas (`TranscriptorDePrueba`, que no escucha nada) y el real
    (`TranscriptorLocal`, capa 3), y **la puerta los distingue por la marca
    `es_de_prueba`, no por el tipo**.

    `idioma` es obligatorio y no opcional: §6.2 exige **forzar** el idioma
    declarado del brief, porque dejar que el modelo lo detecte «introduce una
    fuente de error que no es del generador musical».
    """

    #: Ficha de licencia verificada, o `None` si no la hay (y entonces no mide).
    ficha: FichaTranscriptor | None

    #: `True` en los dobles de prueba. La puerta lo mira antes que nada.
    es_de_prueba: bool

    def transcribir(self, ruta_audio: str | os.PathLike[str], idioma: str) -> str:
        ...


class TranscriptorDePrueba:
    """DOBLE DE PRUEBAS. Devuelve un texto fijo y no abre el audio.

    ⚠️ **No transcribe nada.** Existe para que los tests de la capa 1 y del
    resumen puedan correr sin modelo, y esta marcado con `es_de_prueba = True`
    precisamente para que la puerta lo rechace: una cifra del acta salida de
    aqui seria **inventarse el numero del gate**, que es lo unico que §8.1
    castiga con anular la sesion entera.

    Acepta una `ficha` solo para poder probar que **ni con ficha** pasa la
    puerta: la marca de doble manda sobre cualquier declaracion.
    """

    es_de_prueba = True

    def __init__(self, texto_fijo: str, ficha: FichaTranscriptor | None = None) -> None:
        self.texto_fijo = texto_fijo
        self.ficha = ficha
        self.llamadas: list[tuple[str, str]] = []

    def transcribir(self, ruta_audio: str | os.PathLike[str], idioma: str) -> str:
        self.llamadas.append((os.fspath(ruta_audio), idioma))
        return self.texto_fijo


def exigir_apto_para_acta(transcriptor: Any) -> FichaTranscriptor:
    """La puerta. Devuelve la ficha si el transcriptor puede cerrar el criterio 4.

    Levanta `TranscriptorNoAptoParaActa` si es un doble de pruebas o si no trae
    ficha de licencia verificada. El orden importa: la marca de doble se mira
    **antes** que la ficha, para que adjuntarle una no lo blanquee.
    """
    if getattr(transcriptor, "es_de_prueba", False):
        raise TranscriptorNoAptoParaActa(
            f"{type(transcriptor).__name__} es un transcriptor de PRUEBA: devuelve un texto "
            "fijo y no escucha el audio. Una cifra suya en el acta seria inventarse el WER "
            "del gate. Tampoco lo salva adjuntarle una ficha: la marca de doble manda. "
            "Para medir de verdad hace falta un transcriptor real con su ficha de licencia "
            "verificada (§9.1, precondicion 9)."
        )
    ficha = getattr(transcriptor, "ficha", None)
    if ficha is None:
        raise TranscriptorNoAptoParaActa(
            f"{type(transcriptor).__name__} no trae ficha de licencia verificada. CLAUDE.md "
            "exige licencia comercial comprobada ANTES de integrar cualquier herramienta del "
            "pipeline, y §6.2 exige archivar modelo, version y SHA-256 de los pesos. "
            f"Carga la ficha con cargar_ficha() y asignala. Campos: {', '.join(_CAMPOS_OBLIGATORIOS)}."
        )
    if not isinstance(ficha, FichaTranscriptor):
        raise TranscriptorNoAptoParaActa(
            f"La ficha de {type(transcriptor).__name__} no salio de cargar_ficha(): "
            f"es un {type(ficha).__name__}. Solo cuenta una ficha validada por la puerta."
        )

    # Y ahora el CONTENIDO, no solo el tipo. `FichaTranscriptor` es un NamedTuple
    # publico: se construye a mano con una licencia propietaria y una ruta a un
    # `.bin`, pasa el `isinstance` de arriba y cruza la puerta. Comprobado
    # ejecutandolo (revision 2026-09-03). Una puerta que se rodea construyendo
    # una tupla no es una puerta, asi que los invariantes que sostienen una regla
    # del proyecto se revalidan aqui, que es donde no se pueden rodear.
    # La lista es CERRADA a proposito: no hay lista negra de licencias prohibidas,
    # porque eso invierte la carga —lo no enumerado pasaria— y este invariante no
    # admite esa lectura. Lo que no esta comprobado y escrito, no entra.
    if ficha.licencia_spdx not in LICENCIAS_COMERCIALES:
        raise TranscriptorNoAptoParaActa(
            f"licencia {ficha.licencia_spdx!r}: fuera de la lista verificada de este "
            f"repositorio ({sorted(LICENCIAS_COMERCIALES)}). Anadir una exige comprobarla "
            "y escribirla en un commit."
        )
    if not ficha.ruta_pesos.name.lower().endswith(".safetensors"):
        raise TranscriptorNoAptoParaActa(
            f"pesos {ficha.ruta_pesos.name!r}: solo se aceptan '.safetensors' (D-14). Los "
            "formatos basados en pickle ejecutan codigo al deserializar, y eso no cambia "
            "porque el modelo sea de medida y no de generacion."
        )
    sha = str(ficha.sha256_pesos).strip().lower()
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise TranscriptorNoAptoParaActa(
            f"sha256_pesos {ficha.sha256_pesos!r} no es un SHA-256 hexadecimal de 64 "
            "caracteres: §6.2 exige archivarlo para que la medida sea reproducible."
        )
    return ficha


# =========================================================================== #
# CAPA 3 — el transcriptor real: pesos de disco, sin red y sin codigo ajeno
# =========================================================================== #

#: Whisper trabaja a 16 kHz. No es un parametro: es la tasa a la que se entreno
#: su extractor de rasgos, y darle otra no falla, deforma.
SR_TRANSCRIPTOR = 16000

#: Formatos de pesos que NO son safetensors. Si uno de estos convive con los
#: buenos, el directorio se rechaza entero. `use_safetensors=True` protege la
#: carga de HOY; un fichero asi al lado es un cargador futuro esperando
#: equivocarse, y los cinco primeros son pickle — ejecucion de codigo (D-14).
SUFIJOS_PESOS_NO_SAFETENSORS = frozenset({
    ".bin", ".pt", ".pth", ".ckpt", ".pkl", ".pickle", ".msgpack", ".h5",
})

#: Sufijos de codigo ejecutable. Un modelo son datos; si trae programa, el
#: programa viaja con el, y eso es exactamente lo que CLAUDE.md prohibe.
SUFIJOS_CODIGO = frozenset({".py", ".pyc", ".pyd", ".pyo", ".so", ".dll", ".dylib"})

#: Claves con las que una ficha de modelo pide que se ejecute codigo suyo.
#: Encontrarlas es motivo de RECHAZO, no de aviso: `auto_map` existe justamente
#: para que `Auto*.from_pretrained` importe un `.py` del repositorio del modelo.
CLAVES_CODIGO_REMOTO = ("auto_map", "custom_pipelines", "custom_code", "trust_remote_code")


class AudioNoSoportado(ValueError):
    """El audio no es un WAV PCM de 16 bits, que es lo unico que se lee aqui."""


class DependenciaAusente(ErrorDePuerta):
    """Falta `torch`, `transformers`, `numpy` o `scipy`: no se puede transcribir."""


class ModeloNoAuditable(ErrorDePuerta):
    """El directorio de pesos no esta donde se dijo, o no contiene safetensors."""


class ModeloConCodigoRemoto(ErrorDePuerta):
    """El directorio trae codigo, o pide que se ejecute codigo suyo. No se carga."""


class ModeloConPesosInseguros(ErrorDePuerta):
    """Junto a los safetensors hay pesos en un formato basado en pickle (D-14)."""


class AuditoriaModelo(NamedTuple):
    """Lo que se comprobo del directorio ANTES de dejar que transformers lo abra."""

    directorio: Path
    pesos: tuple[Path, ...]
    configuraciones: tuple[Path, ...]
    n_ficheros: int


def _claves_en_json(documento: Any, claves: Sequence[str]) -> list[str]:
    """Busca `claves` en un JSON ya parseado, a cualquier profundidad.

    Iterativo y no recursivo a proposito: `tokenizer.json` anida mucho, y un
    error de recursion aqui se leeria como «este modelo es raro» cuando en
    realidad seria un limite del interprete.

    `trust_remote_code: false` NO cuenta: declararlo apagado es lo correcto. Lo
    que se rechaza es pedirlo encendido, y la mera presencia de las otras tres.
    """
    encontradas: list[str] = []
    pila = [documento]
    while pila:
        nodo = pila.pop()
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                if clave in claves and not (clave == "trust_remote_code" and not valor):
                    encontradas.append(clave)
                pila.append(valor)
        elif isinstance(nodo, list):
            pila.extend(nodo)
    return sorted(set(encontradas))


def auditar_directorio_modelo(directorio: str | os.PathLike[str]) -> AuditoriaModelo:
    """Mira el directorio de pesos ANTES de cargarlo y lo rechaza si trae sorpresas.

    Tres invariantes de CLAUDE.md, comprobados aqui porque es el ultimo sitio
    donde comprobarlos sirve de algo — despues ya se ha cargado:

    1. **Nada de codigo.** Ningun `.py`, `.so`, `.dll`... en el arbol.
    2. **Nada de codigo remoto pedido por configuracion.** Ningun `auto_map`,
       `custom_pipelines`, `custom_code` ni `trust_remote_code: true` en los JSON.
    3. **Solo safetensors.** Ni un `.bin`/`.pt`/`.ckpt` conviviendo con ellos, y
       al menos un `.safetensors` de verdad.

    Lo que **no** comprueba: que los pesos sean inocuos. Eso no lo comprueba
    nadie (D-14). Comprueba que cargarlos no ejecute codigo elegido por otro.

    Los JSON se leen con `json.loads` sobre texto: aqui no se deserializa nada.
    """
    d = Path(directorio)
    if not d.is_dir():
        raise ModeloNoAuditable(
            f"No hay directorio de modelo en {d}. Este modulo NO descarga pesos: llegan "
            "de fuera, puestos por quien verifico su licencia (§9.1, precondicion 9)."
        )

    ficheros = sorted(p for p in d.rglob("*") if p.is_file())
    codigo = [p for p in ficheros if p.suffix.lower() in SUFIJOS_CODIGO]
    if codigo:
        raise ModeloConCodigoRemoto(
            f"El directorio {d} trae codigo ejecutable: {[p.name for p in codigo]}. Un "
            "modelo son datos; si trae programa, cargarlo puede ejecutarlo. CLAUDE.md no "
            "admite `trust_remote_code` ni codigo de terceros en el pipeline."
        )

    inseguros = [p for p in ficheros if p.suffix.lower() in SUFIJOS_PESOS_NO_SAFETENSORS]
    if inseguros:
        raise ModeloConPesosInseguros(
            f"Junto a los pesos de {d} hay ficheros en formatos que no son safetensors: "
            f"{[p.name for p in inseguros]}. Se rechaza el directorio ENTERO aunque hoy se "
            "cargue con use_safetensors=True: un formato alternativo al lado es un cargador "
            "esperando equivocarse, y .bin/.pt/.pth/.ckpt/.pkl son pickle, es decir "
            "ejecucion de codigo al deserializar (D-14). Quita el fichero o usa otro directorio."
        )

    configuraciones = tuple(p for p in ficheros if p.suffix.lower() == ".json")
    for config in configuraciones:
        try:
            documento = json.loads(config.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ModeloNoAuditable(f"No se puede auditar {config}: {exc}") from exc
        claves = _claves_en_json(documento, CLAVES_CODIGO_REMOTO)
        if claves:
            raise ModeloConCodigoRemoto(
                f"{config.name} pide codigo remoto: {claves}. `auto_map` es justo el "
                "mecanismo por el que Auto*.from_pretrained importa un .py del repositorio "
                "del modelo. No se carga."
            )

    pesos = tuple(p for p in ficheros if p.suffix.lower() == ".safetensors")
    if not pesos:
        raise ModeloNoAuditable(
            f"En {d} no hay ni un .safetensors. Sin pesos no hay transcriptor, y no se "
            "buscan en otro formato a proposito (D-14)."
        )

    return AuditoriaModelo(
        directorio=d,
        pesos=pesos,
        configuraciones=configuraciones,
        n_ficheros=len(ficheros),
    )


def leer_wav_mono_16k(ruta: str | os.PathLike[str]) -> tuple[Any, float, int]:
    """WAV PCM de 16 bits -> `(muestras float32 mono a 16 kHz, duracion_s, sr_original)`.

    Solo WAV, y a proposito: es lo que produce `g1_generar.py` y lo que trae el
    corpus del suelo. Aceptar formatos comprimidos meteria un decodificador de
    terceros en el camino de una cifra del gate, y esa es justo la clase de
    dependencia que este proyecto exige justificar ANTES de tenerla.

    La duracion que devuelve es la del audio **original**, no la del remuestreo:
    es el denominador del RTF y tiene que ser la de verdad.
    """
    ruta = Path(ruta)
    if ruta.suffix.lower() != ".wav":
        raise AudioNoSoportado(
            f"{ruta.name}: aqui solo se lee WAV PCM. Convierte el audio fuera, con la "
            "herramienta que ya use el pipeline, y pasa el WAV."
        )
    if not ruta.is_file():
        raise AudioNoSoportado(f"No existe el audio {ruta}.")

    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise DependenciaAusente(f"Leer audio necesita numpy: {exc}") from exc

    with wave.open(str(ruta), "rb") as w:
        canales = w.getnchannels()
        ancho = w.getsampwidth()
        sr = w.getframerate()
        n = w.getnframes()
        if ancho != 2:
            raise AudioNoSoportado(
                f"{ruta.name}: se esperaban 16 bits por muestra y hay {ancho * 8}. No se "
                "convierte por las bravas: interpretar mal la profundidad mete ruido en la "
                "entrada del transcriptor, y ese ruido acabaria contado como error del cantante."
            )
        if n == 0:
            raise AudioNoSoportado(f"{ruta.name}: no tiene ni una muestra.")
        crudo = w.readframes(n)

    x = np.frombuffer(crudo, dtype="<i2").astype(np.float32) / 32768.0
    if canales > 1:
        x = x.reshape(-1, canales).mean(axis=1)
    duracion = len(x) / sr

    if sr != SR_TRANSCRIPTOR:
        try:
            from scipy.signal import resample_poly
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise DependenciaAusente(
                f"Remuestrear de {sr} Hz a {SR_TRANSCRIPTOR} Hz necesita scipy: {exc}"
            ) from exc
        g = math.gcd(sr, SR_TRANSCRIPTOR)
        x = resample_poly(x, SR_TRANSCRIPTOR // g, sr // g).astype(np.float32)

    return x, duracion, sr


class TranscriptorLocal:
    """Transcriptor de VERDAD: pesos locales, `transformers`, sin red ni codigo ajeno.

    Satisface el protocolo `Transcriptor` y **no** lleva `es_de_prueba`, asi que
    cruza `exigir_apto_para_acta()` si —y solo si— su ficha lo merece. De hecho la
    puerta se cruza en el propio constructor: un transcriptor real que no pudiera
    producir una cifra del acta no deberia ni llegar a existir.

    Por que las clases concretas y no `AutoModel`
    ---------------------------------------------
    `WhisperForConditionalGeneration` y `WhisperProcessor` son clases concretas.
    `Auto*` es lo que consulta `auto_map` para importar codigo del repositorio del
    modelo; usar la concreta cierra esa via **por construccion**, no por bandera.
    Aun asi se pasa `trust_remote_code=False` explicito y se audita el directorio
    antes: tres cierres para el mismo agujero, porque el agujero es ejecucion
    remota de codigo.

    Por que `local_files_only=True`
    -------------------------------
    Sin esa bandera, un identificador mal escrito o un fichero que falte hacen que
    `transformers` se vaya al hub a buscarlo. Eso traeria pesos que **nadie ha
    verificado**, por un camino que no pasa por `cargar_ficha()`, y ademas
    convertiria una cifra del gate en algo que depende de la red.

    Los pesos se cargan en la PRIMERA transcripcion, no al construir: la puerta,
    la auditoria y los tests de contrato tienen que poder correr sin gastar 3 GB de
    RAM ni el segundo de carga.
    """

    #: Lo mira la puerta antes que nada. Aqui es `False` porque este si escucha.
    es_de_prueba = False

    def __init__(
        self,
        ficha: FichaTranscriptor,
        *,
        directorio: str | os.PathLike[str] | None = None,
        hilos: int | None = None,
    ) -> None:
        if not isinstance(ficha, FichaTranscriptor):
            raise TypeError(
                "TranscriptorLocal exige una ficha salida de cargar_ficha(): es lo que "
                f"acredita licencia e integridad, y ha llegado un {type(ficha).__name__}."
            )
        self.ficha = ficha
        # La puerta, en el constructor: revalida el CONTENIDO de la ficha
        # (licencia en la lista blanca, pesos .safetensors, sha256 bien formado).
        exigir_apto_para_acta(self)

        self.directorio = (
            Path(directorio) if directorio is not None else Path(ficha.ruta_pesos).parent
        )
        self.auditoria = auditar_directorio_modelo(self.directorio)

        declarados = Path(ficha.ruta_pesos).resolve()
        if declarados not in {p.resolve() for p in self.auditoria.pesos}:
            raise ModeloNoAuditable(
                f"Los pesos que declara la ficha ({declarados}) no estan entre los "
                f"safetensors auditados de {self.directorio}: "
                f"{[p.name for p in self.auditoria.pesos]}. La ficha acredita UN fichero "
                "concreto por su sha256; cargar otro dejaria el acta declarando un hash que "
                "no es el de los pesos que midieron."
            )

        self.hilos = hilos
        self.segundos_carga: float | None = None
        self.segundos_inferencia = 0.0
        self.segundos_audio = 0.0
        self.historial: list[dict[str, Any]] = []
        """Una entrada por transcripcion. El cronometro no es curiosidad: el RTF
        de este modelo depende de la LONGITUD de la pista (Whisper rellena hasta
        30 s, asi que un enunciado de 4 s cuesta casi lo mismo que uno de 30), y
        sin el detalle por pista esa dependencia no se ve en la media."""
        self._modelo: Any = None
        self._procesador: Any = None

    # -- carga --------------------------------------------------------------- #

    def cargar(self) -> float:
        """Carga pesos y procesador (idempotente). Devuelve los segundos que tardo.

        `torch` y `transformers` se importan **aqui dentro**, no arriba: la capa 1
        y la puerta tienen que seguir siendo biblioteca estandar, y buena parte de
        la suite corre en maquinas donde no hay nada de esto instalado.
        """
        if self._modelo is not None:
            return self.segundos_carga or 0.0

        try:
            import torch
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
        except ImportError as exc:
            raise DependenciaAusente(
                "Transcribir de verdad necesita torch y transformers instalados "
                f"({exc}). La capa 1 (la aritmetica del WER) y la puerta de licencia no "
                "los necesitan y siguen funcionando sin ellos."
            ) from exc

        if self.hilos:
            torch.set_num_threads(self.hilos)

        t0 = time.perf_counter()
        self._procesador = WhisperProcessor.from_pretrained(
            str(self.directorio),
            local_files_only=True,
            trust_remote_code=False,
        )
        self._modelo = WhisperForConditionalGeneration.from_pretrained(
            str(self.directorio),
            dtype=torch.float32,
            low_cpu_mem_usage=True,
            use_safetensors=True,   # explicito aunque no haya .bin: es el invariante D-14
            local_files_only=True,  # que un fichero que falte NO se busque en la red
            trust_remote_code=False,
        )
        self._modelo.eval()
        self.segundos_carga = time.perf_counter() - t0
        return self.segundos_carga

    # -- transcripcion ------------------------------------------------------- #

    def transcribir(self, ruta_audio: str | os.PathLike[str], idioma: str) -> str:
        """Transcribe un WAV con el idioma FORZADO (§6.2) y cronometra la pasada.

        El idioma no tiene valor por defecto: §6.2 exige forzar el del brief
        porque dejar que el modelo lo detecte «introduce una fuente de error que
        no es del generador musical».
        """
        if not isinstance(idioma, str) or not idioma.strip():
            raise ValueError(
                "El idioma es obligatorio y se FUERZA (§6.2). Dejar que el modelo lo "
                "detecte mete en la cifra del gate un error que no es del generador: una "
                "pista en castellano detectada como portugues se transcribe entera mal."
            )
        self.cargar()
        import torch

        audio, duracion, sr_original = leer_wav_mono_16k(ruta_audio)
        entradas = self._procesador(
            audio,
            sampling_rate=SR_TRANSCRIPTOR,
            return_tensors="pt",
            truncation=False,
            padding="longest",
            return_attention_mask=True,
        )
        # Whisper solo mira 30 s de golpe (3000 tramas de mel). Por encima de eso
        # transformers decodifica en tramos encadenados, y ese camino exige las
        # marcas de tiempo. Pedirlas siempre no vale: en la ventana corta cambian
        # el texto que sale, y el WER no puede depender de un detalle asi.
        largo = entradas.input_features.shape[-1] > 3000

        t0 = time.perf_counter()
        with torch.no_grad():
            ids = self._modelo.generate(
                entradas.input_features,
                attention_mask=entradas.get("attention_mask"),
                language=idioma.strip(),
                task="transcribe",
                num_beams=1,                     # voraz: barato y sin aleatoriedad
                condition_on_prev_tokens=False,  # que un tramo no arrastre al siguiente
                return_timestamps=largo,
            )
        segundos = time.perf_counter() - t0
        # `clean_up_tokenization_spaces=False` explicito: esa limpieza esta pensada
        # para tokenizadores WordPiece y sobre BPE es destructiva (se come espacios
        # antes de la puntuacion). Hoy transformers ya la ignora para Whisper, pero
        # una limpieza que cambia el texto segun la version de la libreria no puede
        # quedar implicita en el camino de una cifra del gate.
        texto = self._procesador.batch_decode(
            ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0].strip()

        self.segundos_inferencia += segundos
        self.segundos_audio += duracion
        self.historial.append({
            "audio": os.fspath(ruta_audio),
            "idioma": idioma.strip(),
            "sr_original": sr_original,
            "duracion_s": duracion,
            "segundos": segundos,
            "rtf": segundos / duracion if duracion else float("nan"),
            "ventanas_de_30s": int(entradas.input_features.shape[-1] // 3000) or 1,
        })
        return texto

    @property
    def llamadas(self) -> int:
        return len(self.historial)

    @property
    def ultima(self) -> dict[str, Any] | None:
        """La ultima medida, o `None` si todavia no ha transcrito nada."""
        return self.historial[-1] if self.historial else None

    @property
    def rtf_medio(self) -> float | None:
        """Segundos de CPU por segundo de audio, sobre todo lo transcrito.

        **No es una constante del modelo, y extrapolarlo sale mal.** Depende de
        dos cosas ajenas al modelo, medidas las dos en esta maquina el 2026-09-03:

        1. **La longitud de la pista.** Whisper mira ventanas de 30 s y rellena
           las que no llegan: un enunciado de 4 s cuesta casi lo mismo que uno de
           30, asi que su RTF sale disparado. Sobre las 80 frases sueltas del
           corpus del suelo el RTF medio salio **1,60**; sobre una pista de 180 s,
           **0,355**. Mismo modelo, misma maquina.
        2. **Cuanto se canta dentro.** La decodificacion es autorregresiva, asi
           que una ventana con letra densa cuesta mas que una con instrumental.
           Pista de 180 s poco densa: **0,355**. Pista de 240 s con letra
           continua: **0,907**.

        Para presupuestar la tanda de §4 hay que quedarse con el PEOR caso medido
        sobre material parecido, no con la media: 0,907 sobre pistas largas y
        densas, que son las diez del gate.
        """
        if not self.segundos_audio:
            return None
        return self.segundos_inferencia / self.segundos_audio

    @property
    def segundos_por_ventana(self) -> float | None:
        """Coste medio por ventana de 30 s: quita el efecto del relleno, no el otro.

        Es mejor base que el RTF para comparar pistas de longitudes distintas,
        porque descuenta el relleno hasta 30 s. Pero **sigue sin ser constante**:
        lo medido va de 9,7 s por ventana (frases sueltas) a 10,7 s (pista de
        180 s) y 27,2 s (pista de 240 s con letra densa), porque lo que domina es
        cuantos tokens tiene que emitir el decodificador. Sirve para acotar, no
        para predecir.
        """
        ventanas = sum(m["ventanas_de_30s"] for m in self.historial)
        return self.segundos_inferencia / ventanas if ventanas else None


def transcriptor_desde_ficha(
    ruta_ficha: str | os.PathLike[str],
    *,
    hilos: int | None = None,
    verificar_hash: bool = True,
) -> TranscriptorLocal:
    """`ficha.json` -> transcriptor listo (todavia sin cargar los pesos).

    Es el camino corto y el unico recomendado: pasa por `cargar_ficha()`, asi que
    licencia, formato y sha256 quedan comprobados antes de que el objeto exista.
    """
    return TranscriptorLocal(
        cargar_ficha(ruta_ficha, verificar_hash=verificar_hash), hilos=hilos
    )


# =========================================================================== #
# Medida de una pista
# =========================================================================== #

class MedicionPista(NamedTuple):
    brief: str
    ruta_audio: str
    idioma: str
    transcripcion: str
    resultado: ResultadoWer
    apta_para_acta: bool
    ficha: FichaTranscriptor | None


def medir_pista(
    transcriptor: Any,
    ruta_audio: str | os.PathLike[str],
    idioma: str,
    referencia: str,
    *,
    brief: str,
    para_acta: bool = True,
    norma: Normalizacion = NORMALIZACION_PROTOCOLO,
) -> MedicionPista:
    """Transcribe una pista y mide su WER contra la letra de referencia.

    `para_acta` es `True` **por defecto** a proposito: el modo estricto es el que
    se usa de verdad, y quien quiera una cifra de juguete tiene que pedirla. Un
    valor por defecto laxo acabaria colandose en el acta por olvido.

    Con `para_acta=True` se cruzan dos puertas antes de tocar nada: la del
    transcriptor (`exigir_apto_para_acta`) y la de la normalizacion (tiene que
    ser la del §6.2).
    """
    ficha: FichaTranscriptor | None = None
    if para_acta:
        ficha = exigir_apto_para_acta(transcriptor)
        if not norma.apta_para_acta:
            raise TranscriptorNoAptoParaActa(
                f"Normalizacion {norma.nombre!r} es de diagnostico y no la del §6.2. El "
                "criterio 4 se mide con la normalizacion fijada ANTES de escuchar; "
                "cambiarla ahora seria mover la definicion del numero (§2, inmutabilidad)."
            )
    else:
        ficha = getattr(transcriptor, "ficha", None)
        if not isinstance(ficha, FichaTranscriptor):
            ficha = None

    transcripcion = transcriptor.transcribir(ruta_audio, idioma)
    resultado = medir_wer(referencia, transcripcion, norma)
    return MedicionPista(
        brief=brief,
        ruta_audio=os.fspath(ruta_audio),
        idioma=idioma,
        transcripcion=transcripcion,
        resultado=resultado,
        apta_para_acta=para_acta,
        ficha=ficha,
    )


# =========================================================================== #
# El suelo del transcriptor (§6.2): sin el, el 15 % no significa nada
# =========================================================================== #

#: La limitacion del suelo, escrita una sola vez y citada en todas partes: en las
#: notas del resumen, en la salida de la linea de ordenes y en el JSON que se
#: archiva. Escribirla en un sitio solo garantizaria que se cae del otro.
AVISO_SUELO_ES_COTA_INFERIOR = (
    "El suelo esta medido sobre VOZ HABLADA clara, no sobre canto, asi que es una COTA "
    "INFERIOR del suelo que este mismo transcriptor tendria sobre las pistas del gate: "
    "cantar es mas dificil de transcribir (melodia, vocales alargadas, notas sostenidas, "
    "instrumentos de fondo). Dos consecuencias, de signo contrario: (1) presentado como "
    "«lo que se equivoca el transcriptor» FAVORECE AL TRANSCRIPTOR, porque es su caso "
    "facil y no el del gate; (2) restado de la media, PERJUDICA AL GENERADOR, porque deja "
    "un residuo mayor del que le toca — «media menos suelo» no es «el error del generador» "
    "y no se puede leer asi. Lo que esto impide es la tercera lectura, la unica que haria "
    "pasar un gate que no pasa: ESTIMAR un suelo de canto, mayor, y restarlo. Ese numero no "
    "esta medido y §2 aplica los umbrales tal cual."
)

#: Version del esquema del manifiesto del corpus del suelo. Igual que la ficha:
#: un esquema desconocido se rechaza, no se interpreta a medias.
SCHEMA_CORPUS_SUELO = 1

#: Licencias admitidas para el AUDIO DE REFERENCIA del suelo. Es una lista propia
#: y NO `LICENCIAS_COMERCIALES`, y la diferencia es deliberada:
#:
#: * `LICENCIAS_COMERCIALES` gobierna las **herramientas del pipeline** (pesos,
#:   separadores, marcadores de agua). Ahi una clausula de ShareAlike es veneno:
#:   se contagia a lo que se derive de ella, y unos pesos CC-BY-SA podrian
#:   arrastrar a lo generado con ellos. Por eso esa lista no la admite.
#: * El corpus del suelo no se integra en nada, no se redistribuye y no toca
#:   ninguna pista: es material de MEDIDA que se escucha una vez para cronometrar
#:   el error del transcriptor. Ahi ShareAlike no contagia nada, porque no hay
#:   obra derivada que distribuir.
#:
#: La lista sigue siendo blanca, y anadir una entrada sigue exigiendo verificar la
#: licencia contra la fuente primaria y dejarlo en un commit.
LICENCIAS_CORPUS_SUELO = LICENCIAS_COMERCIALES | frozenset({"CC-BY-SA-4.0"})

_CAMPOS_CORPUS = ("descripcion", "licencia_spdx", "fuente_licencia", "licencia_verificada_el")


class CorpusInvalido(ErrorDePuerta):
    """El manifiesto del corpus del suelo no acredita lo que tiene que acreditar."""


class MuestraSuelo(NamedTuple):
    """Un trozo de voz clara con su transcripcion conocida."""

    ruta: Path
    idioma: str
    texto: str
    fuente: str
    duracion_s: float | None


class CorpusSuelo(NamedTuple):
    """El corpus de voz de referencia, con la licencia de su AUDIO declarada.

    El manifiesto exige licencia y fuente por el mismo motivo que la ficha del
    transcriptor: una cifra que se archiva en el acta arrastra consigo el material
    con el que se obtuvo, y «lo baje de internet» no es una procedencia.
    """

    ruta_manifiesto: Path
    descripcion: str
    licencia_spdx: str
    fuente_licencia: str
    licencia_verificada_el: str
    muestras: tuple[MuestraSuelo, ...]

    def triples(self) -> tuple[tuple[Path, str, str], ...]:
        """Lo que `medir_suelo()` espera: `(ruta, idioma, texto)`."""
        return tuple((m.ruta, m.idioma, m.texto) for m in self.muestras)

    def por_idioma(self) -> dict[str, int]:
        recuento: dict[str, int] = {}
        for m in self.muestras:
            recuento[m.idioma] = recuento.get(m.idioma, 0) + 1
        return recuento


def cargar_corpus_suelo(
    ruta: str | os.PathLike[str],
    *,
    verificar_audio: bool = True,
) -> CorpusSuelo:
    """Lee el manifiesto del corpus del suelo y comprueba que se puede usar.

    Comprueba, en este orden: esquema conocido; campos de licencia presentes;
    licencia en `LICENCIAS_CORPUS_SUELO`; al menos una muestra; y que cada muestra
    trae ruta, idioma y texto no vacios, con el audio en su sitio.

    Las rutas relativas se resuelven **contra el directorio del manifiesto**, para
    que el corpus se pueda mover entero sin reescribirlo.
    """
    ruta_manifiesto = Path(ruta)
    if not ruta_manifiesto.is_file():
        raise CorpusInvalido(
            f"No hay manifiesto de corpus en {ruta_manifiesto}. Sin suelo medido, "
            "`resumir()` se declara interpretable=False y la cifra del gate no se lee "
            "(§6.2)."
        )
    try:
        documento = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CorpusInvalido(f"Manifiesto ilegible ({ruta_manifiesto}): {exc}") from exc
    if not isinstance(documento, dict):
        raise CorpusInvalido(f"El manifiesto {ruta_manifiesto} no es un objeto JSON.")

    schema = documento.get("schema")
    if schema != SCHEMA_CORPUS_SUELO:
        raise CorpusInvalido(
            f"schema {schema!r}: este modulo entiende el {SCHEMA_CORPUS_SUELO}."
        )

    faltan = [c for c in _CAMPOS_CORPUS
              if not isinstance(documento.get(c), str) or not documento[c].strip()]
    if faltan:
        raise CorpusInvalido(
            f"Al manifiesto {ruta_manifiesto} le faltan campos: {', '.join(faltan)}. La "
            "licencia del AUDIO de referencia se declara igual que la de los pesos: una "
            "cifra del acta arrastra el material con el que se obtuvo."
        )

    licencia = documento["licencia_spdx"].strip()
    if licencia not in LICENCIAS_CORPUS_SUELO:
        raise CorpusInvalido(
            f"Licencia {licencia!r} del corpus: fuera de la lista verificada "
            f"{sorted(LICENCIAS_CORPUS_SUELO)}. Lista BLANCA: lo que nadie ha comprobado no "
            "pasa. Si de verdad permite el uso, se verifica contra la fuente primaria y se "
            "anade con un commit."
        )

    crudas = documento.get("muestras")
    if not isinstance(crudas, list) or not crudas:
        raise CorpusInvalido(
            f"El manifiesto {ruta_manifiesto} no trae muestras. Un suelo de cero muestras "
            "no es un cero: es un suelo sin medir."
        )

    base = ruta_manifiesto.parent
    muestras: list[MuestraSuelo] = []
    for i, cruda in enumerate(crudas):
        if not isinstance(cruda, dict):
            raise CorpusInvalido(f"La muestra {i} del corpus no es un objeto JSON.")
        for campo in ("ruta", "idioma", "texto"):
            if not isinstance(cruda.get(campo), str) or not cruda[campo].strip():
                raise CorpusInvalido(
                    f"A la muestra {i} ({cruda.get('ruta', '?')}) le falta {campo!r}."
                )
        destino = Path(cruda["ruta"].strip())
        if not destino.is_absolute():
            destino = (base / destino).resolve()
        if verificar_audio and not destino.is_file():
            raise CorpusInvalido(
                f"La muestra {i} apunta a un audio que no existe: {destino}."
            )
        duracion = cruda.get("duracion_s")
        muestras.append(MuestraSuelo(
            ruta=destino,
            idioma=cruda["idioma"].strip(),
            texto=cruda["texto"].strip(),
            fuente=str(cruda.get("fuente", "")).strip(),
            duracion_s=float(duracion) if isinstance(duracion, (int, float)) else None,
        ))

    return CorpusSuelo(
        ruta_manifiesto=ruta_manifiesto,
        descripcion=documento["descripcion"].strip(),
        licencia_spdx=licencia,
        fuente_licencia=documento["fuente_licencia"].strip(),
        licencia_verificada_el=documento["licencia_verificada_el"].strip(),
        muestras=tuple(muestras),
    )


class Suelo(NamedTuple):
    """WER del transcriptor sobre voz clara de referencia. Ver cabecera del modulo."""

    wer_medio: float
    n_muestras: int
    detalle: tuple[MedicionPista, ...]

    dominio: str = "habla-leida-clara"
    """Sobre QUE se midio. No es adorno: un suelo de habla y uno de canto no son
    el mismo numero, y el campo obliga a decir cual es este."""

    es_cota_inferior_del_suelo_de_canto: bool = True
    """Siempre `True` mientras `dominio` sea habla. Ver `AVISO_SUELO_ES_COTA_INFERIOR`."""

    corpus: str = ""
    """De donde salio el audio de referencia, para poder repetirlo."""

    licencia_corpus: str = ""
    """Licencia SPDX del audio de referencia, verificada al cargar el manifiesto."""

    def por_idioma(self) -> dict[str, float]:
        """WER medio por idioma. Un suelo global esconde que un idioma va peor."""
        suma: dict[str, list[float]] = {}
        for m in self.detalle:
            suma.setdefault(m.idioma, []).append(m.resultado.wer)
        return {idioma: sum(v) / len(v) for idioma, v in sorted(suma.items())}


def medir_suelo(
    transcriptor: Any,
    muestras: CorpusSuelo | Iterable[tuple[str | os.PathLike[str], str, str]],
    *,
    para_acta: bool = True,
    norma: Normalizacion = NORMALIZACION_PROTOCOLO,
) -> Suelo:
    """Mide el WER del transcriptor sobre audio de **voz clara** ya conocida.

    Args:
        muestras: un `CorpusSuelo` cargado con `cargar_corpus_suelo()` —que ademas
            acredita la licencia del audio— o, para pruebas, tuplas sueltas
            `(ruta_audio, idioma, texto_esperado)`. El audio debe ser **voz
            hablada clara** con transcripcion conocida y verificada, en los mismos
            idiomas de los briefs (castellano e ingles, §4). No sirve audio del
            propio gate: eso es justo lo que se quiere medir.
        norma: la misma que se use con las pistas, o el suelo no es restable.

    El numero que sale es el **error que el transcriptor comete solo**, sobre
    habla. Se publica junto al WER de las pistas para poder leerlo (§6.2), **no se
    resta del numero del gate** (§2, regla de inmutabilidad) y arrastra siempre la
    limitacion de `AVISO_SUELO_ES_COTA_INFERIOR`.
    """
    corpus = muestras if isinstance(muestras, CorpusSuelo) else None
    triples = corpus.triples() if corpus is not None else muestras

    detalle = [
        medir_pista(
            transcriptor, ruta, idioma, esperado,
            brief=f"suelo:{os.path.basename(os.fspath(ruta))}",
            para_acta=para_acta,
            norma=norma,
        )
        for ruta, idioma, esperado in triples
    ]
    if not detalle:
        raise ValueError(
            "No hay muestras de voz clara. Un suelo de cero muestras no es un cero: es un "
            "suelo que no se ha medido, y §6.2 avisa de que sin el la cifra no se interpreta."
        )
    return Suelo(
        wer_medio=sum(m.resultado.wer for m in detalle) / len(detalle),
        n_muestras=len(detalle),
        detalle=tuple(detalle),
        corpus="" if corpus is None else str(corpus.ruta_manifiesto),
        licencia_corpus="" if corpus is None else corpus.licencia_spdx,
    )


# =========================================================================== #
# Criterio 4: los umbrales son del protocolo, no de este fichero
# =========================================================================== #

#: §2, criterio 4: «WER de la letra cantada: <= 15 % de media sobre las 10 pistas
#: propias y <= 25 % en el peor caso individual». Estan aqui como constantes para
#: no parsear markdown en cada medida, y `verificar_umbrales()` comprueba contra
#: el protocolo que no han derivado. Ninguno de los dos se toca tras escuchar.
UMBRAL_WER_MEDIA = 0.15
UMBRAL_WER_PEOR = 0.25

_RE_UMBRAL_MEDIA = re.compile(r"≤\s*(\d+)\s*%\s*de media")
_RE_UMBRAL_PEOR = re.compile(r"≤\s*(\d+)\s*%\s*en el peor caso")


class UmbralesDerivados(RuntimeError):
    """Las constantes de aqui ya no dicen lo que dice el §2 del protocolo."""


def verificar_umbrales(ruta_protocolo: str | os.PathLike[str]) -> tuple[float, float]:
    """Comprueba que `UMBRAL_WER_*` siguen siendo los del §2. Devuelve los dos.

    El protocolo es la fuente de verdad y este fichero, una copia. Una copia sin
    comprobar acaba divergiendo en silencio, y aqui divergir significa medir el
    gate contra un umbral que nadie ratifico.
    """
    texto = Path(ruta_protocolo).read_text(encoding="utf-8")
    media = _RE_UMBRAL_MEDIA.search(texto)
    peor = _RE_UMBRAL_PEOR.search(texto)
    if not media or not peor:
        raise UmbralesDerivados(
            f"No se encuentran los umbrales de WER en {ruta_protocolo}. O el §2 cambio de "
            "redaccion o no es el protocolo. No se mide a ciegas."
        )
    leidos = (int(media.group(1)) / 100, int(peor.group(1)) / 100)
    if leidos != (UMBRAL_WER_MEDIA, UMBRAL_WER_PEOR):
        raise UmbralesDerivados(
            f"El protocolo dice media <= {leidos[0]:.0%} y peor <= {leidos[1]:.0%}, pero este "
            f"modulo lleva {UMBRAL_WER_MEDIA:.0%} y {UMBRAL_WER_PEOR:.0%}. Manda el protocolo: "
            "si el cambio es legitimo, se ratifica por escrito y solo rige desde la SIGUIENTE "
            "ejecucion del gate (§2, regla de inmutabilidad)."
        )
    return (UMBRAL_WER_MEDIA, UMBRAL_WER_PEOR)


class ResumenG1(NamedTuple):
    """El criterio 4 resuelto sobre un conjunto de pistas."""

    n_pistas: int
    media: float
    peor: float
    brief_peor: str
    cumple_media: bool
    cumple_peor: bool
    cumple: bool
    suelo: Suelo | None
    media_menos_suelo: float | None
    """**Informativo, y no es «el error del generador».** No entra en `cumple`.
    Con un suelo de habla el residuo sale mayor del que le tocaria al modelo
    musical (`AVISO_SUELO_ES_COTA_INFERIOR`). Ver la cabecera del modulo."""

    interpretable: bool
    para_acta: bool
    notas: tuple[str, ...]
    mediciones: tuple[MedicionPista, ...]


def resumir(
    mediciones: Sequence[MedicionPista],
    suelo: Suelo | None,
    *,
    para_acta: bool = False,
) -> ResumenG1:
    """Media, peor caso y veredicto del criterio 4 (§2 y §8.3).

    Los dos umbrales son un **AND**, no un promedio que se compense: una media
    impecable con una sola pista al 30 % **no cumple**. Asi lo dice §8.3 y asi se
    calcula.
    """
    if not mediciones:
        raise ValueError(
            "No hay mediciones que resumir. Una media de cero pistas no es un 0 %: es que no "
            "se midio nada, y §8.1 anula la sesion a la que le falte una pista."
        )
    if para_acta:
        impropias = [m.brief for m in mediciones if not m.apta_para_acta]
        if impropias:
            raise TranscriptorNoAptoParaActa(
                f"Estas mediciones no son aptas para el acta: {impropias}. Un resumen del "
                "criterio 4 no puede mezclar cifras reales con cifras de prueba."
            )

    media = sum(m.resultado.wer for m in mediciones) / len(mediciones)
    peor_medicion = max(mediciones, key=lambda m: m.resultado.wer)
    peor = peor_medicion.resultado.wer

    notas: list[str] = []
    if len(mediciones) != 10:
        notas.append(
            f"Son {len(mediciones)} pistas y §2 mide el criterio 4 sobre las 10 propias. "
            "Con menos, el mismo umbral se aplica sobre menos evidencia (§3.4, regla de "
            "aplicabilidad): se documenta como debilidad de la sesion, nunca como "
            "flexibilizacion del umbral."
        )
    if suelo is None:
        notas.append(
            "SIN SUELO DEL TRANSCRIPTOR: la cifra no es interpretable. §6.2 lo advierte antes "
            "de que haya numeros — el transcriptor tambien se equivoca, y un 12 % puede ser un "
            "modelo excelente medido con un transcriptor malo o al reves. Mide el suelo con "
            "medir_suelo() sobre voz clara de referencia y publicalo junto a esta cifra."
        )
    else:
        notas.append(
            f"Suelo del transcriptor: {suelo.wer_medio:.2%} sobre {suelo.n_muestras} muestras "
            f"de {suelo.dominio}. Es INFORMATIVO: §2 aplica el 15 %/25 % tal cual y restar el "
            "suelo para pasar seria degradar un umbral con aritmetica."
        )
        if suelo.es_cota_inferior_del_suelo_de_canto:
            notas.append(AVISO_SUELO_ES_COTA_INFERIOR)
    if any(m.resultado.avisos for m in mediciones):
        notas.append(
            "Alguna medicion trae avisos (mira `resultado.avisos` pista a pista): resuelvelos "
            "antes de llevar la cifra al acta."
        )

    cumple_media = media <= UMBRAL_WER_MEDIA
    cumple_peor = peor <= UMBRAL_WER_PEOR
    return ResumenG1(
        n_pistas=len(mediciones),
        media=media,
        peor=peor,
        brief_peor=peor_medicion.brief,
        cumple_media=cumple_media,
        cumple_peor=cumple_peor,
        cumple=cumple_media and cumple_peor,
        suelo=suelo,
        media_menos_suelo=None if suelo is None else media - suelo.wer_medio,
        interpretable=suelo is not None,
        para_acta=para_acta,
        notas=tuple(notas),
        mediciones=tuple(mediciones),
    )


# =========================================================================== #
# Linea de comandos
# =========================================================================== #

_PROTOCOLO_REL = Path("docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md")


def _cmd_comparar(args: argparse.Namespace) -> int:
    norma = NORMALIZACION_SIN_TILDES if args.sin_tildes else NORMALIZACION_PROTOCOLO
    referencia = Path(args.referencia).read_text(encoding="utf-8")
    hipotesis = Path(args.hipotesis).read_text(encoding="utf-8")
    r = medir_wer(referencia, hipotesis, norma)
    print(f"Normalizacion : {r.normalizacion.nombre} "
          f"(apta para el acta: {'si' if r.normalizacion.apta_para_acta else 'NO'})")
    print(f"N (referencia): {r.n_referencia} palabras")
    print(f"S / I / D     : {r.sustituciones} / {r.inserciones} / {r.borrados}")
    print(f"WER           : {r.wer_pct:.2f} %")
    print("Alineacion (solo fallos):")
    print(formatear_alineacion(r))
    for aviso in r.avisos:
        print(f"\n[AVISO] {aviso}")
    print("\n[RECORDATORIO] Esta cifra no se interpreta sin el SUELO del transcriptor "
          "(§6.2). Mide tambien su WER sobre voz clara conocida.")
    return 0


def _cmd_ficha(args: argparse.Namespace) -> int:
    try:
        ficha = cargar_ficha(args.ruta)
    except ErrorDePuerta as exc:
        print(f"PUERTA CERRADA: {exc}")
        return 2
    print("PUERTA ABIERTA. Lo que se archiva en 07-metricas/ (§6.2):")
    for clave, valor in ficha.para_acta().items():
        print(f"  {clave:<26} {valor}")
    print("\nOjo: esto acredita LICENCIA e INTEGRIDAD, no inocuidad (D-14). Lo que impide "
          "que cargar estos pesos sea ejecucion remota de codigo es que sean safetensors y "
          "que el directorio pase `auditar_directorio_modelo()`, no este hash.")
    return 0


def _cmd_transcribir(args: argparse.Namespace) -> int:
    """Transcribe UNA pista de verdad y cronometra. No mide WER: para eso hace
    falta la letra de referencia, y esa la aporta `comparar` o `medir_pista()`."""
    try:
        transcriptor = transcriptor_desde_ficha(args.ficha, hilos=args.hilos)
    except ErrorDePuerta as exc:
        print(f"PUERTA CERRADA: {exc}")
        return 2

    print(f"Modelo   : {transcriptor.ficha.identificador}@{transcriptor.ficha.version}")
    print(f"Directorio: {transcriptor.directorio} "
          f"({transcriptor.auditoria.n_ficheros} ficheros auditados, "
          f"{len(transcriptor.auditoria.pesos)} safetensors, 0 pickles, 0 codigo)")

    try:
        texto = transcriptor.transcribir(args.audio, args.idioma)
    except (ErrorDePuerta, AudioNoSoportado, ValueError) as exc:
        print(f"NO SE PUDO TRANSCRIBIR: {exc}")
        return 2

    ultima = transcriptor.ultima or {}
    print(f"Carga    : {transcriptor.segundos_carga:.2f} s")
    print(f"Audio    : {ultima.get('duracion_s', 0):.1f} s a {ultima.get('sr_original')} Hz "
          f"({ultima.get('ventanas_de_30s')} ventanas de 30 s)")
    print(f"Inferencia: {ultima.get('segundos', 0):.2f} s · RTF {ultima.get('rtf', 0):.3f} · "
          f"{transcriptor.segundos_por_ventana:.1f} s por ventana")
    print(f"\nTranscripcion ({args.idioma}):\n{texto}")
    print("\n[RECORDATORIO] Esto es texto, no una cifra del gate. El WER sale de compararlo "
          "con la letra de referencia, y no se interpreta sin el SUELO del transcriptor "
          "(§6.2).")

    if args.salida:
        Path(args.salida).write_text(json.dumps({
            "modelo": transcriptor.ficha.para_acta(),
            "audio": os.fspath(args.audio),
            "idioma": args.idioma,
            "texto": texto,
            "carga_s": transcriptor.segundos_carga,
            "medida": ultima,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\ninforme -> {args.salida}")
    return 0


def _cmd_suelo(args: argparse.Namespace) -> int:
    """Mide el SUELO del transcriptor sobre el corpus de voz clara del manifiesto."""
    try:
        transcriptor = transcriptor_desde_ficha(args.ficha, hilos=args.hilos)
        corpus = cargar_corpus_suelo(args.corpus)
    except ErrorDePuerta as exc:
        print(f"PUERTA CERRADA: {exc}")
        return 2

    if args.limite:
        corpus = corpus._replace(muestras=corpus.muestras[: args.limite])

    print(f"Corpus   : {corpus.descripcion}")
    print(f"Licencia : {corpus.licencia_spdx} (verificada {corpus.licencia_verificada_el})")
    print(f"Fuente   : {corpus.fuente_licencia}")
    print(f"Muestras : {len(corpus.muestras)} {corpus.por_idioma()}")

    suelo = medir_suelo(transcriptor, corpus, para_acta=not args.sin_puerta)

    print(f"\nSUELO    : {suelo.wer_medio:.2%} sobre {suelo.n_muestras} muestras")
    for idioma, wer in suelo.por_idioma().items():
        print(f"  {idioma}: {wer:.2%}")
    if transcriptor.rtf_medio is not None:
        print(f"RTF medio: {transcriptor.rtf_medio:.3f} "
              f"({transcriptor.segundos_inferencia:.0f} s de CPU sobre "
              f"{transcriptor.segundos_audio:.0f} s de audio) · "
              f"{transcriptor.segundos_por_ventana:.1f} s por ventana de 30 s")
        print("[OJO] Este RTF es de FRASES SUELTAS y no se extrapola a las pistas del "
              "gate: Whisper rellena cada frase hasta 30 s, asi que su RTF sale inflado. "
              "Para presupuestar la tanda de §4 hay que cronometrar pistas largas.")
    print(f"\n[LIMITACION] {AVISO_SUELO_ES_COTA_INFERIOR}")

    if args.salida:
        Path(args.salida).write_text(json.dumps({
            "modelo": transcriptor.ficha.para_acta(),
            "corpus": {
                "manifiesto": str(corpus.ruta_manifiesto),
                "descripcion": corpus.descripcion,
                "licencia_spdx": corpus.licencia_spdx,
                "fuente_licencia": corpus.fuente_licencia,
                "licencia_verificada_el": corpus.licencia_verificada_el,
            },
            "normalizacion": NORMALIZACION_PROTOCOLO.nombre,
            "suelo_wer": suelo.wer_medio,
            "suelo_wer_por_idioma": suelo.por_idioma(),
            "n_muestras": suelo.n_muestras,
            "dominio": suelo.dominio,
            "es_cota_inferior_del_suelo_de_canto": suelo.es_cota_inferior_del_suelo_de_canto,
            "limitacion": AVISO_SUELO_ES_COTA_INFERIOR,
            "rtf_medio": transcriptor.rtf_medio,
            "rtf_medio_no_extrapolable_porque": (
                "son frases sueltas y Whisper rellena cada una hasta 30 s; usa "
                "segundos_por_ventana_de_30s para presupuestar pistas largas"
            ),
            "segundos_por_ventana_de_30s": transcriptor.segundos_por_ventana,
            "segundos_carga": transcriptor.segundos_carga,
            "detalle": [
                {
                    "audio": m.ruta_audio,
                    "idioma": m.idioma,
                    "referencia": m.resultado.referencia_normalizada,
                    "transcripcion": m.transcripcion,
                    "wer": m.resultado.wer,
                    "n": m.resultado.n_referencia,
                    "s_i_d": [m.resultado.sustituciones, m.resultado.inserciones,
                              m.resultado.borrados],
                    "avisos": m.resultado.avisos,
                    "cronometro": cronometro,
                }
                for m, cronometro in zip(suelo.detalle, transcriptor.historial)
            ],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\ninforme -> {args.salida}")
    return 0


def _cmd_umbrales(args: argparse.Namespace) -> int:
    ruta = Path(args.protocolo) if args.protocolo else _AQUI.parents[3] / _PROTOCOLO_REL
    try:
        media, peor = verificar_umbrales(ruta)
    except (UmbralesDerivados, OSError) as exc:
        print(f"NO VERIFICADO: {exc}")
        return 2
    print(f"Umbrales del criterio 4 verificados contra {ruta}:")
    print(f"  media <= {media:.0%} · peor caso <= {peor:.0%}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "WER del criterio 4 de G1 (§6.2), y el suelo sin el cual no se interpreta. "
            "`comparar` y `umbrales` no necesitan nada instalado; `transcribir` y `suelo` "
            "cargan los pesos que declare la ficha, de disco y sin red."
        )
    )
    sub = p.add_subparsers(dest="orden", required=True)

    c = sub.add_parser("comparar", help="WER entre dos ficheros de texto (sin modelo).")
    c.add_argument("referencia", help="Letra literal, sin marcas de seccion (§4.1).")
    c.add_argument("hipotesis", help="Transcripcion.")
    c.add_argument("--sin-tildes", action="store_true",
                   help="Modo DIAGNOSTICO: iguala tildes y enye. Su cifra no va al acta.")
    c.set_defaults(func=_cmd_comparar)

    f = sub.add_parser("ficha", help="Comprueba una ficha de transcriptor contra la puerta.")
    f.add_argument("ruta")
    f.set_defaults(func=_cmd_ficha)

    t = sub.add_parser("transcribir", help="Transcribe un WAV con los pesos de la ficha.")
    t.add_argument("ficha")
    t.add_argument("audio")
    t.add_argument("--idioma", required=True,
                   help="Se FUERZA, no se detecta (§6.2). Ej.: es, en.")
    t.add_argument("--hilos", type=int, default=None, help="Hilos de CPU para torch.")
    t.add_argument("--salida", default=None, help="Fichero JSON con el informe.")
    t.set_defaults(func=_cmd_transcribir)

    s = sub.add_parser("suelo", help="Mide el suelo del transcriptor sobre voz clara (§6.2).")
    s.add_argument("ficha")
    s.add_argument("corpus", help="Manifiesto JSON del corpus de voz de referencia.")
    s.add_argument("--limite", type=int, default=None, help="Usa solo las N primeras muestras.")
    s.add_argument("--hilos", type=int, default=None)
    s.add_argument("--salida", default=None)
    s.add_argument("--sin-puerta", action="store_true",
                   help="Mide sin exigir que el transcriptor sea apto para el acta. "
                        "Solo para probar el arnes; su cifra no vale para nada mas.")
    s.set_defaults(func=_cmd_suelo)

    u = sub.add_parser("umbrales", help="Comprueba que los umbrales siguen siendo los del §2.")
    u.add_argument("protocolo", nargs="?", default=None)
    u.set_defaults(func=_cmd_umbrales)
    return p


def _forzar_utf8_en_consola() -> None:
    """La consola de Windows es cp1252 y se come «§», tildes y la enye.

    Aqui no es cosmetico: la alineacion que imprime `comparar` **se archiva en
    `07-metricas/`** (§6.2), y una «ñ» convertida en «?» al copiarla convertiria
    justo la sustitucion que se quiere mirar en un error ilegible. Misma cura
    que en `g1_generar.py`; dentro del contenedor no hace nada, ya es UTF-8.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError, OSError):
            pass


def main(argv: list[str] | None = None) -> int:
    _forzar_utf8_en_consola()
    args = construir_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
