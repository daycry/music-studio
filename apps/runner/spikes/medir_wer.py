#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Instrumento de PUNTUACION de G1: el WER del criterio 4, y la puerta que lo custodia.

Que es esto y que NO es
=======================
`g1_generar.py` produce el material; esto **mide una de las dos cifras
objetivas** del gate: el WER de la letra cantada (`g1-protocolo.md` §6.2), que
el §2 somete a dos umbrales — **media <= 15 %** sobre las 10 pistas propias
**y** **peor caso <= 25 %**.

**No transcribe.** No trae ningun modelo, no descarga nada y no sabe leer audio.
Eso es deliberado y es la mitad del encargo: ver la capa 2, abajo.

Tampoco puntua las cinco dimensiones de la rubrica (§3) — eso es escucha
humana —, ni calcula CLAP (§6.1), ni emite veredicto.

Las dos capas, y por que estan separadas
========================================
**Capa 1 — la aritmetica.** Distancia de edicion sobre palabras, biblioteca
estandar pura, sin dependencias y sin modelos. Es la parte que se puede probar
con verdad conocida ("10 palabras, una mal, 10 %") y que por tanto **se puede
creer**. Corre en cualquier interprete, hoy, sin GPU y sin descargar nada.

**Capa 2 — el transcriptor, que aqui NO se integra.** El protocolo propone
`HeartTranscriptor-oss` (§6.2), pero CLAUDE.md exige **licencia comercial
verificada ANTES de integrar** cualquier herramienta del pipeline, y esa
verificacion es la precondicion 9 de §9.1, abierta y del propietario. Asi que
este modulo define **la interfaz** (ruta de audio + idioma -> texto) y **la
puerta**: sin una ficha de licencia comprobada que llegue **de fuera**, se niega
a medir y dice exactamente que le falta.

Separar las dos capas es lo que permite que la capa 1 este terminada y probada
hoy, con el gate aun bloqueado por una verificacion legal que no depende de
ningun programa.

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

Dos avisos sobre el suelo, para que no se use de mas:

* **No se resta al numero del gate.** §2 es inequivoco: los umbrales «se aplican
  tal cual». `media_menos_suelo` es **informativo** y no toca `cumple_media`.
  Restarlo para pasar seria degradar un umbral con aritmetica.
* **Es un suelo de voz hablada clara**, no de canto. Acota por abajo, no explica
  la diferencia entera. Un WER de canto siempre tendra una parte que no es ni
  del generador ni del transcriptor, sino del hecho de cantar.

Uso
===
La capa 1 no necesita nada instalado::

    python apps/runner/spikes/medir_wer.py comparar letra.txt transcripcion.txt

Comprobar que una ficha de transcriptor pasa la puerta (sin medir nada)::

    python apps/runner/spikes/medir_wer.py ficha D:/srv/transcriptor/ficha.json

Comprobar que los umbrales de aqui siguen siendo los del protocolo::

    python apps/runner/spikes/medir_wer.py umbrales
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
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
    # Suelo y resumen
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
# La interfaz minima. Aqui NO se implementa ningun transcriptor real.
# --------------------------------------------------------------------------- #

@runtime_checkable
class Transcriptor(Protocol):
    """Lo minimo que tiene que ofrecer un transcriptor para servir a §6.2.

    Deliberadamente diminuto — ruta de audio e idioma, devuelve texto — porque
    **el modulo no integra ninguno**. Cuando el propietario cierre la
    precondicion 9 de §9.1 (ficha de licencia de HeartTranscriptor-oss
    verificada), la implementacion real vivira **fuera de aqui**, cargara sus
    pesos con `safetensors` y satisfara este protocolo. Este fichero no la
    importa, no la nombra y no la descarga.

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

class Suelo(NamedTuple):
    """WER del transcriptor sobre voz clara de referencia. Ver cabecera del modulo."""

    wer_medio: float
    n_muestras: int
    detalle: tuple[MedicionPista, ...]


def medir_suelo(
    transcriptor: Any,
    muestras: Iterable[tuple[str | os.PathLike[str], str, str]],
    *,
    para_acta: bool = True,
    norma: Normalizacion = NORMALIZACION_PROTOCOLO,
) -> Suelo:
    """Mide el WER del transcriptor sobre audio de **voz clara** ya conocida.

    Args:
        muestras: tuplas `(ruta_audio, idioma, texto_esperado)`. El audio debe
            ser **voz hablada clara** con transcripcion conocida y verificada, en
            los mismos idiomas de los briefs (castellano e ingles, §4). No sirve
            audio del propio gate: eso es lo que se quiere medir.
        norma: la misma que se use con las pistas, o el suelo no es restable.

    El numero que sale es el **error que el transcriptor comete solo**. Se
    publica junto al WER de las pistas para poder leerlo (§6.2), y **no se resta
    del numero del gate** (§2, regla de inmutabilidad).
    """
    detalle = [
        medir_pista(
            transcriptor, ruta, idioma, esperado,
            brief=f"suelo:{os.path.basename(os.fspath(ruta))}",
            para_acta=para_acta,
            norma=norma,
        )
        for ruta, idioma, esperado in muestras
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
    """**Informativo.** No entra en `cumple`. Ver la cabecera del modulo."""

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
            "de voz clara. Es INFORMATIVO: §2 aplica el 15 %/25 % tal cual y restar el suelo "
            "para pasar seria degradar un umbral con aritmetica. Ademas es un suelo de voz "
            "HABLADA: acota por abajo, no explica la diferencia entera con el canto."
        )
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
    print("\nOjo: esto acredita LICENCIA e INTEGRIDAD. No hay transcriptor integrado en "
          "este modulo; la implementacion real vive fuera y satisface el protocolo "
          "`Transcriptor`.")
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
            "WER del criterio 4 de G1 (§6.2). NO transcribe: la capa 1 mide y la capa 2 "
            "exige que el transcriptor llegue de fuera con su ficha de licencia verificada."
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
