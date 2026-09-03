#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arnes de medicion de CLAP para el gate G1: criterio 3 del `g1-protocolo.md` §2.

Que es esto
===========
Mide la **similitud audio-texto** entre cada pista y el prompt de estilo literal
de su brief, y publica los pares `(propia, libreria)` de los 10 briefs. Es el
criterio 3 de G1.

* **la mecanica de la medida es nuestra y esta probada** — troceado en ventanas,
  coseno y media;
* **el modelo llega inyectado** (`ModeloClap`), de modo que la mecanica se prueba
  con un modelo de juguete determinista, sin descargar nada y sin GPU;
* **la puerta de licencia esta puesta** — sin ficha valida no se mide, y el
  mensaje dice exactamente que falta;
* **el backend real esta cableado** (`transformers-clap`), y carga los pesos
  **de disco**, sin red y sin codigo remoto.

El modelo, y lo que costo elegirlo (2026-09-03)
===============================================
El protocolo (§6.1) nombraba **HeartCLAP** como candidato principal y **no esta
publicado**: es el hallazgo A-3 de `T-06`, reconfirmado el 2026-09-03 contra la
API del hub (la organizacion tiene seis repos y ninguno es ese; el mas reciente
es de hace casi siete meses). Se pasa a la alternativa que el propio §6.1 preve
—«un modelo CLAP de la familia LAION»— y de los cinco candidatos queda uno::

    laion/clap-htsat-fused @ 365dea6ef167def6676140ed93bbc43f84dabb28

**Lo eligio el invariante de `safetensors`, no su calidad musical**: los otros
cuatro publican unicamente `pytorch_model.bin`, que es un pickle, y cargarlo
ejecuta el codigo que lleve dentro (D-14). El precio hay que leerlo, porque
viaja con el numero: **los dos LAION entrenados especificamente con musica estan
entre los descartados**. El que queda es el generalista con fusion
(LAION-Audio-630K: lleva musica, pero no esta especializado en ella), asi que el
criterio 3 se mide con **menos poder discriminante sobre canciones** del que
tendria con los otros. Es una perdida real, no un tecnicismo.

**La licencia esta verificada contra fuente primaria y NO ratificada.** El repo
de pesos declara `apache-2.0` solo como **metadato** —no publica fichero de
licencia—, mientras que el repositorio de codigo del proveedor
(`github.com/LAION-AI/CLAP`) publica un LICENSE **CC0-1.0** con texto integro.
Las dos lecturas permiten uso comercial; la ficha declara **Apache-2.0 por ser la
mas restrictiva de las dos**. La evidencia completa —textos integros de las dos
licencias, respuestas crudas de las APIs, hashes de cada fichero— esta archivada
en `D:/srv/clap/provenance/`. Quien cierra una ficha de licencia es el
propietario (regla 5 del registry, I-13b): mientras no lo haga, la ficha lo dice
en `licencia.verificada_por`, y ese texto **sale impreso en el informe** junto al
numero.

Como se carga, y las tres cosas que este backend no hace
=======================================================
`ClapDeTransformers` carga el modelo con `transformers` **desde el directorio
local que nombra la ficha**, y por ese orden: primero se audita el directorio
(un solo fichero de pesos, que es el que la ficha hasheo; nada en formato pickle
al lado; ninguna configuracion que pida codigo remoto) y solo despues se importa
`transformers` y se carga.

1. **No descarga nada.** `local_files_only=True` en las dos cargas. Si algo
   falta, falla; no sale a la red a buscarlo.
2. **No ejecuta codigo del repositorio de pesos.** `trust_remote_code=False`
   explicito, y ademas se rechaza el directorio si `config.json`,
   `preprocessor_config.json` o `tokenizer_config.json` traen `auto_map` o
   `custom_pipelines`, que son las dos llaves con las que un repo de pesos pide
   que se ejecute codigo suyo.
3. **No carga nada que no sea `safetensors`.** `use_safetensors=True` en la
   carga del modelo, y la auditoria previa del directorio.

Lo que este script NO hace
--------------------------
* **No decide el gate.** Publica el recuento y los valores brutos; los cinco
  umbrales del §2 **no aparecen aqui**, ni siquiera como comentario, por el
  mismo motivo por el que no aparecen en `g1_generar.py`: un script que conoce
  el liston acaba, antes o despues, opinando sobre el.
* **No descarga pesos** ni toca la red: los pesos tienen que estar ya en disco,
  puestos ahi por quien verifico su procedencia.
* **No remuestrea en silencio.** Si la tasa del WAV no es la que declara la
  ficha, para. Remuestrear cambia la medida, y §6.1 exige que la politica sea
  identica para las tres series: esa decision se declara antes de calcular, no
  se improvisa dentro de un bucle.

La advertencia que viaja con el numero (A-14)
=============================================
Va en el informe que emite el script, no solo en el acta, y esa es la parte
importante. El criterio 3 **favorece estructuralmente a la serie propia**: la
pista propia se genero **condicionada al mismo texto** contra el que luego se
mide la similitud (ACE-Step 1.5 condiciona con un text encoder), mientras que la
de libreria solo tuvo que sobrevivir a una busqueda por palabras clave en un
catalogo. No es optimizacion directa de la metrica —el modelo no condiciona con
CLAP—, pero **si es la misma tarea para una serie y no para la otra**.

Consecuencia practica: **un 10 de 10 aqui no es prueba de calidad musical.** Es
una comprobacion de sanidad («la pista responde al prompt»). Si el numero
viajara solo, en modo solo no hay nadie que corrija esa lectura. Por eso se
publican tambien **el tamano del efecto** (diferencia media y mediana) y los
valores en bruto: un 7 de 10 con diferencias de 0,001 y otro con diferencias de
0,15 son resultados distintos.

Invariantes que aplican aqui igual que a los generadores
========================================================
* **Solo `safetensors`** (D-14). La puerta es la del runner (`contracts`), no una
  copia: nombre primero, cabecera real despues. Nunca `torch.load` ni nada que
  deserialice objetos.
* **SHA-256 comprobado** al cargar la ficha. Verifica **integridad**, no
  inocuidad; lo segundo lo da la licencia y la procedencia, no un hash.
* **Nada se resuelve por nombre.** La ficha *nombra* el backend; no lo importa.
  Una ficha hostil solo consigue que el script se niegue.

Uso::

    python spikes/medir_clap.py --ficha D:/srv/clap/clap.model.json \\
        --directorio D:/srv/g1/07-metricas --salida clap.json

Ese comando carga el modelo y **para en el material**: `--directorio` no se lee
todavia, porque el emparejado de los 10 briefs (que par de ficheros y que prompt
literal va con cada uno) lo fija `T-09` y se archiva en `07-metricas/README.md`
(§6.1). Leerlo «a ojo» seria inventarse la mitad del procedimiento.

La API de Python si mide hoy, con el modelo real o con uno propio::

    ficha = cargar_ficha("D:/srv/clap/clap.model.json")
    par = medir_brief("B-01", prompt, propia, libreria, construir_modelo(ficha), ficha)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, Protocol

import numpy as np

# --------------------------------------------------------------------------- #
# Arranque de sys.path
# --------------------------------------------------------------------------- #
# Los spikes se ejecutan como scripts sueltos: no hay paquete instalable, porque
# el empaquetado del monorepo es T-10 y esta detras de este mismo gate. Se anade
# `apps/runner/` para poder reutilizar las puertas de pesos de `contracts`, que
# es preferible a copiarlas: una regla de seguridad duplicada se desincroniza.
_AQUI = Path(__file__).resolve()
_RUNNER_ROOT = _AQUI.parents[1]                 # apps/runner
if str(_RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNNER_ROOT))

from contracts import (  # noqa: E402  (tras el arranque de sys.path)
    UnsafeWeightsFormat,
    assert_safetensors,
    assert_safetensors_header,
)

__all__ = [
    "ADVERTENCIA_CRITERIO_3",
    "BACKENDS_CLAP",
    "BACKEND_TRANSFORMERS",
    "LICENCIAS_ACEPTADAS",
    "LICENCIAS_NO_COMERCIALES",
    "SCHEMA_FICHA",
    "VENTANA_S",
    "Audio",
    "BackendNoDisponible",
    "ClapDeTransformers",
    "FichaClap",
    "FichaInvalida",
    "MedidaPista",
    "ModeloClap",
    "ParBrief",
    "cargar_ficha",
    "construir_modelo",
    "formatear",
    "informe",
    "leer_wav",
    "medir_brief",
    "medir_pista",
    "similitud_coseno",
    "ventanas",
]


# --------------------------------------------------------------------------- #
# La advertencia que acompana al numero (A-14)
# --------------------------------------------------------------------------- #
#: Redactada a partir de la recomendacion (c) de A-14 en `decisiones-2026-09-01.md`.
#: Va en el informe, en el texto de consola y, de ahi, al acta. Si alguien la
#: quita, hay un test que lo caza.
ADVERTENCIA_CRITERIO_3 = (
    "AVISO (A-14): este criterio favorece estructuralmente a la serie propia. La "
    "pista propia se genero condicionada al MISMO texto contra el que aqui se mide "
    "la similitud; la de libreria solo tuvo que aparecer en una busqueda por "
    "palabras clave. Cumplirlo NO es evidencia de calidad musical: es una "
    "comprobacion de sanidad de que la pista responde al prompt. Leer un resultado "
    "alto como validacion es exactamente el error que esta nota existe para evitar."
)

#: Duracion de ventana por defecto (§6.1: los modelos CLAP consumen fragmentos de
#: longitud fija). La ficha puede declarar otra si el modelo elegido la impone;
#: entonces se aplica IDENTICA a las tres series y queda anotada en el informe.
#: Cola minima que se acepta como ventana. Por debajo se descarta: ver `ventanas`.
MIN_VENTANA_S = 1.0

VENTANA_S = 10.0

#: Politica declarada, tal cual viaja al informe. Es lo que §6.1 exige anotar
#: para que la cifra sea reproducible en G1-bis.
POLITICA_VENTANAS = (
    "ventanas no solapadas que cubren la pista entera; la ultima se incluye "
    "aunque sea mas corta, salvo si no llega al minimo declarado, en cuyo caso "
    "se descarta (ver 'desviacion_declarada' del informe)"
)
POLITICA_AGREGACION = (
    "media aritmetica de las similitudes coseno de las ventanas, sin ponderar por "
    "duracion: la ultima ventana corta pesa lo mismo que una completa"
)


# --------------------------------------------------------------------------- #
# Ficha del modelo: la puerta de licencia
# --------------------------------------------------------------------------- #
#: Version del esquema de la ficha. Una ficha de un esquema desconocido se
#: RECHAZA en vez de interpretarse a medias.
SCHEMA_FICHA = 1

#: Nombre del unico backend que este repositorio sabe ejecutar. La ficha lo
#: **nombra**; quien decide es el `if` explicito de `construir_modelo()`.
BACKEND_TRANSFORMERS = "transformers-clap"

#: Backends de CLAP que este repositorio sabe ejecutar. Anadir uno exige (1)
#: escribirlo aqui **y** escribir su constructor, las dos cosas en un commit, y
#: (2) archivar su ficha de licencia verificada (I-13b). Ninguna de las dos cosas
#: la puede hacer un dato que aparezca en disco.
BACKENDS_CLAP: frozenset[str] = frozenset({BACKEND_TRANSFORMERS})

#: Licencias con uso comercial permitido **verificadas para este proyecto**.
#: Lista CERRADA: lo que no esta aqui no se usa, aunque sea permisiva de fama.
#: Anadir una entrada es una decision documentada, no una conveniencia del dia.
LICENCIAS_ACEPTADAS = frozenset({
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC0-1.0",
    "CC-BY-4.0",
})

#: Rechazadas EXPLICITAMENTE, no simplemente ausentes, para que el motivo quede
#: escrito donde se lee. Es lo que descarto MusicGen y lo que dejo los pesos de
#: Demucs en revision: la regla vale para las herramientas de medicion igual que
#: para los generadores.
LICENCIAS_NO_COMERCIALES = frozenset({
    "CC-BY-NC-4.0",
    "CC-BY-NC-SA-4.0",
    "CC-BY-NC-ND-4.0",
    "CC-BY-NC-3.0",
    "CC-BY-NC-SA-3.0",
})


class FichaInvalida(Exception):
    """La ficha del modelo de medicion no vale, con el motivo dentro."""


class BackendNoDisponible(Exception):
    """La ficha nombra un backend que este repositorio no sabe ejecutar."""


class FichaClap(NamedTuple):
    """Identidad comprobada del modelo con el que se mide. Solo se obtiene a
    traves de `cargar_ficha()`, que es la puerta: quien tiene una de estas ya
    paso la validacion de licencia, de formato y de integridad."""

    id: str
    version: str
    backend: str
    ruta_pesos: Path
    sha256: str
    licencia_spdx: str
    licencia_verificada_por: str
    licencia_verificada_el: str
    licencia_fuente: str | None
    tasa_entrada_hz: int
    ventana_s: float
    ruta_ficha: Path


def _texto(documento: dict[str, Any], campo: str) -> str:
    valor = documento.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise FichaInvalida(
            f"falta el campo {campo!r} o no es una cadena no vacia. "
            "Sin el, la ficha no identifica nada."
        )
    return valor.strip()


def _sha256_de(ruta: Path) -> str:
    digestor = hashlib.sha256()
    with open(ruta, "rb") as fichero:
        for bloque in iter(lambda: fichero.read(1024 * 1024), b""):
            digestor.update(bloque)
    return digestor.hexdigest()


def _validar_licencia(documento: dict[str, Any]) -> dict[str, str]:
    """Comprueba la ficha de licencia. Es la regla 5 del registry (I-13b)."""
    licencia = documento.get("licencia")
    if not isinstance(licencia, dict):
        raise FichaInvalida(
            "falta el bloque 'licencia'. Un modelo sin ficha de licencia verificada "
            "no se integra en el pipeline, tampoco para medir (I-13b)."
        )

    spdx = _texto(licencia, "spdx")
    if spdx in LICENCIAS_NO_COMERCIALES:
        raise FichaInvalida(
            f"licencia {spdx!r}: prohibe el uso comercial. El proyecto solo integra "
            "herramientas con uso comercial permitido, y la regla vale para las de "
            "medicion igual que para los generadores (fue lo que descarto MusicGen)."
        )
    if spdx not in LICENCIAS_ACEPTADAS:
        raise FichaInvalida(
            f"licencia {spdx!r}: no esta en la lista verificada de este repositorio "
            f"({sorted(LICENCIAS_ACEPTADAS)}). La lista es cerrada a proposito: "
            "anadir una licencia exige comprobarla y escribirla en un commit."
        )

    uso_comercial = licencia.get("uso_comercial")
    if uso_comercial is not True:
        raise FichaInvalida(
            f"licencia {spdx!r} declara uso_comercial={uso_comercial!r}. O el SPDX o "
            "la declaracion estan mal, y ante una contradiccion no se elige la "
            "lectura conveniente: se para y se comprueba."
        )

    return {
        "spdx": spdx,
        "verificada_por": _texto(licencia, "verificada_por"),
        "verificada_el": _texto(licencia, "verificada_el"),
        "fuente": licencia.get("fuente") if isinstance(licencia.get("fuente"), str) else None,
    }


def _validar_pesos(documento: dict[str, Any], ruta_ficha: Path) -> tuple[Path, str]:
    """Puerta de pesos: formato (D-14) primero, integridad despues."""
    declarado = _texto(documento, "pesos")
    ruta = Path(declarado)
    if not ruta.is_absolute():
        ruta = (ruta_ficha.parent / ruta).resolve()

    # 1) El NOMBRE, antes de abrir nada. Es lo que decide si cargarlo podria
    #    ejecutar codigo (D-14).
    try:
        assert_safetensors(ruta)
    except UnsafeWeightsFormat as exc:
        raise FichaInvalida(f"pesos rechazados: {exc}") from exc

    if not ruta.is_file():
        raise FichaInvalida(
            f"los pesos declarados no existen en disco: {ruta}. La ficha describe algo "
            "que tiene que estar aqui; no se descarga nada en tiempo de ejecucion."
        )

    # 2) La CABECERA real, al abrirlo. Defensa en profundidad: un pickle
    #    renombrado pasa el filtro del nombre y muere aqui.
    try:
        assert_safetensors_header(ruta)
    except UnsafeWeightsFormat as exc:
        raise FichaInvalida(f"pesos rechazados: {exc}") from exc
    except OSError as exc:
        raise FichaInvalida(f"los pesos no se pueden leer: {exc}") from exc

    # 3) La INTEGRIDAD. No es inocuidad, y por eso no sustituye a la licencia.
    esperado = _texto(documento, "sha256").lower()
    if len(esperado) != 64 or any(c not in "0123456789abcdef" for c in esperado):
        raise FichaInvalida(
            f"el campo 'sha256' no es un digest hexadecimal de 64 caracteres: {esperado!r}"
        )
    obtenido = _sha256_de(ruta)
    if obtenido != esperado:
        raise FichaInvalida(
            f"el sha256 de {ruta.name} no cuadra con la ficha (integridad).\n"
            f"  declarado: {esperado}\n  en disco:  {obtenido}\n"
            "Los pesos no son los que se verificaron; la medida no seria reproducible."
        )
    return ruta, obtenido


def exigir_ficha_valida(ficha: FichaClap) -> FichaClap:
    """Revalida la ficha EN EL PUNTO DE USO. Devuelve la misma o levanta.

    Por que existe, y por que no basta con `cargar_ficha()`
    ------------------------------------------------------
    `cargar_ficha()` era la unica puerta, y su docstring decia que la unica forma
    de tener un `FichaClap` es pasar por ella. **Era falso**: `FichaClap` es un
    `NamedTuple` publico y exportado, asi que cualquiera lo construye a mano con
    una licencia propietaria y una ruta a un `.bin`, y se salta la validacion
    entera. Comprobado ejecutandolo (revision 2026-09-03).

    Una puerta que se puede rodear no es una puerta. Asi que los invariantes que
    de verdad importan se vuelven a comprobar aqui, y esta funcion se llama desde
    cada camino que MIDE. Es barato —son comprobaciones sobre campos ya en
    memoria— y es lo unico que no se puede rodear construyendo la tupla a mano.

    Lo que se revalida es lo que sostiene un invariante del proyecto, no la ficha
    entera: la licencia (uso comercial verificado, I-13b), el formato de los
    pesos (D-14, solo safetensors) y la forma del hash.
    """
    if ficha.licencia_spdx in LICENCIAS_NO_COMERCIALES:
        raise ValueError(
            f"licencia {ficha.licencia_spdx!r}: prohibe el uso comercial. No se mide con "
            "ella, y da igual como se haya construido la ficha."
        )
    if ficha.licencia_spdx not in LICENCIAS_ACEPTADAS:
        raise ValueError(
            f"licencia {ficha.licencia_spdx!r}: fuera de la lista verificada de este "
            f"repositorio ({sorted(LICENCIAS_ACEPTADAS)}). Anadir una exige comprobarla "
            "y escribirla en un commit, no construir la ficha a mano."
        )
    nombre = ficha.ruta_pesos.name.lower()
    if not nombre.endswith(".safetensors"):
        raise ValueError(
            f"pesos {ficha.ruta_pesos.name!r}: solo se aceptan '.safetensors' (D-14). "
            "Los formatos basados en pickle ejecutan codigo al deserializar."
        )
    sha = str(ficha.sha256).strip().lower()
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError(
            f"sha256 {ficha.sha256!r} no es un SHA-256 hexadecimal de 64 caracteres."
        )
    return ficha


def cargar_ficha(ruta: str | Path) -> FichaClap:
    """Lee y valida la ficha del modelo de medicion. **Es la puerta.**

    Valida el documento entero: licencia, pesos, integridad y parametros. Los
    invariantes que sostienen una regla del proyecto se vuelven a comprobar en
    `exigir_ficha_valida()`, en el punto de uso, porque `FichaClap` es un
    NamedTuple publico y esta puerta se puede rodear construyendolo a mano.

    Comprueba, en este orden: que el fichero exista y sea JSON; el esquema; los
    campos de identidad; la **licencia** (SPDX en lista cerrada de uso comercial
    verificado, mas quien la comprobo y cuando); y los **pesos** (solo
    `safetensors` por nombre y por cabecera, presentes en disco, con SHA-256 que
    cuadra).

    Levanta:
        FichaInvalida: siempre con el motivo concreto dentro. Nunca devuelve una
            ficha a medias.
    """
    ruta_ficha = Path(ruta)
    if not ruta_ficha.is_file():
        raise FichaInvalida(
            f"no existe la ficha del modelo de CLAP en {ruta_ficha}.\n"
            "El modelo tiene que llegar de fuera declarado: ruta local de los pesos, "
            "identificador, version, licencia SPDX con uso comercial verificado y "
            "SHA-256. Hoy el candidato del protocolo (HeartCLAP) no esta publicado "
            "y no hay suplente designado (A-3), asi que esa decision sigue abierta."
        )
    try:
        documento = json.loads(ruta_ficha.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FichaInvalida(f"ficha ilegible ({ruta_ficha}): {exc}") from exc

    if not isinstance(documento, dict):
        raise FichaInvalida("la ficha no es un objeto JSON")

    schema = documento.get("schema")
    if schema != SCHEMA_FICHA:
        raise FichaInvalida(
            f"schema {schema!r}: este arnes entiende el {SCHEMA_FICHA}. Una ficha de "
            "un esquema desconocido no se interpreta a medias."
        )

    licencia = _validar_licencia(documento)
    ruta_pesos, sha256 = _validar_pesos(documento, ruta_ficha)

    tasa = documento.get("tasa_entrada_hz")
    if not isinstance(tasa, int) or tasa <= 0:
        raise FichaInvalida(
            "falta 'tasa_entrada_hz' o no es un entero positivo. §6.1 obliga a anotar "
            "la frecuencia de muestreo de entrada: sin ella la medida no es repetible."
        )

    ventana = documento.get("ventana_s", VENTANA_S)
    if not isinstance(ventana, (int, float)) or ventana <= 0:
        raise FichaInvalida("'ventana_s' tiene que ser un numero de segundos positivo")

    return FichaClap(
        id=_texto(documento, "id"),
        version=_texto(documento, "version"),
        backend=_texto(documento, "backend"),
        ruta_pesos=ruta_pesos,
        sha256=sha256,
        licencia_spdx=licencia["spdx"],
        licencia_verificada_por=licencia["verificada_por"],
        licencia_verificada_el=licencia["verificada_el"],
        licencia_fuente=licencia["fuente"],
        tasa_entrada_hz=tasa,
        ventana_s=float(ventana),
        ruta_ficha=ruta_ficha,
    )


# --------------------------------------------------------------------------- #
# El modelo, inyectado
# --------------------------------------------------------------------------- #

class ModeloClap(Protocol):
    """Lo unico que este arnes necesita de un modelo CLAP.

    Deliberadamente minimo: dos metodos que devuelven vectores. Lo que haya
    detras —HeartCLAP el dia que se publique, un LAION `clap-htsat-*`, o el
    modelo de juguete de los tests— no le importa a la mecanica de la medida, y
    esa es justo la razon de que la mecanica se pueda probar hoy.

    Los vectores no tienen por que venir normalizados: `similitud_coseno()`
    normaliza, porque asumirlo seria confiar en una promesa del modelo.
    """

    def embed_texto(self, texto: str) -> np.ndarray:
        """Vector del prompt de estilo literal del brief (§4.2)."""

    def embed_audio(self, ventana: np.ndarray, tasa: int) -> np.ndarray:
        """Vector de una ventana de audio mono en float, a `tasa` Hz."""


# --------------------------------------------------------------------------- #
# El backend real: CLAP de LAION cargado con transformers, desde disco
# --------------------------------------------------------------------------- #
#: Extensiones de ficheros de pesos basadas en `pickle`. Si una aparece en el
#: directorio del modelo, el directorio no es el que se verifico y se rechaza:
#: `use_safetensors=True` impide cargarlo, pero un pickle al lado de los pesos es
#: una invitacion a que el siguiente cargador —o el siguiente que edite esto— lo
#: coja (D-14).
_EXTENSIONES_DE_PESOS_PROHIBIDAS = frozenset({
    ".bin", ".pt", ".pth", ".ckpt", ".pkl", ".joblib",
})

#: Las dos llaves con las que un repositorio de pesos pide que se ejecute codigo
#: suyo. `trust_remote_code=False` ya las desactiva; encontrarlas significa que el
#: modelo NO es utilizable bajo el invariante del proyecto, y eso se dice al
#: cargar y no cuando falle a medias.
_CLAVES_DE_CODIGO_REMOTO = ("auto_map", "custom_pipelines")

#: Configuraciones donde puede aparecer `auto_map`: la del modelo, la del
#: extractor de caracteristicas, la del tokenizador y la del procesador.
_CONFIGS_QUE_SE_AUDITAN = (
    "config.json",
    "preprocessor_config.json",
    "tokenizer_config.json",
    "processor_config.json",
)


def _auditar_directorio_de_pesos(ficha: FichaClap) -> Path:
    """Comprueba el **directorio** del modelo antes de cargar nada de el.

    `cargar_ficha()` valida un fichero: el que lleva el SHA-256. Pero
    `from_pretrained` no carga un fichero, carga un **directorio** entero
    —configuracion, tokenizador, extractor—, y de eso la ficha no dice nada. Asi
    que aqui se mira lo que el hash no cubre:

    1. que haya **un solo** fichero de pesos y sea exactamente el que la ficha
       hasheo (si hubiera varios, el numero saldria de pesos sin verificar);
    2. que no haya ningun fichero de pesos en formato pickle al lado (D-14);
    3. que ninguna configuracion pida **codigo remoto**.

    Es barato —cuatro `read_text` de ficheros pequenos— y ocurre **antes** de
    importar `transformers`, para que el fallo llegue antes de leer 600 MB.
    """
    directorio = ficha.ruta_pesos.parent
    if not directorio.is_dir():
        raise FichaInvalida(
            f"los pesos declarados no viven en un directorio legible: {directorio}"
        )

    pesos = sorted(p.name for p in directorio.glob("*.safetensors"))
    if pesos != [ficha.ruta_pesos.name]:
        raise FichaInvalida(
            f"el directorio {directorio} contiene {pesos} y la ficha solo verifica "
            f"{ficha.ruta_pesos.name!r}. Con varios ficheros de pesos, parte de lo que "
            "se cargaria no esta cubierto por el SHA-256 de la ficha, y la medida "
            "dejaria de ser reproducible."
        )

    pickles = sorted(
        p.name for p in directorio.iterdir()
        if p.is_file() and p.suffix.lower() in _EXTENSIONES_DE_PESOS_PROHIBIDAS
    )
    if pickles:
        raise FichaInvalida(
            f"hay ficheros de pesos en formato pickle junto a los verificados: {pickles} "
            f"(en {directorio}). Deserializar uno ejecuta el codigo que lleve dentro "
            "(D-14). Este backend no los carga, pero un directorio que los contiene no "
            "es el que se verifico: borralos o apunta la ficha a uno limpio."
        )

    for nombre in _CONFIGS_QUE_SE_AUDITAN:
        ruta = directorio / nombre
        if not ruta.is_file():
            continue
        try:
            documento = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise FichaInvalida(f"configuracion ilegible ({ruta}): {exc}") from exc
        if not isinstance(documento, dict):
            continue
        for clave in _CLAVES_DE_CODIGO_REMOTO:
            if clave in documento:
                raise FichaInvalida(
                    f"{nombre} declara {clave!r}: este modelo pide ejecutar codigo de su "
                    "propio repositorio de pesos para cargarse. No se usa, y no se "
                    "arregla poniendo trust_remote_code: el invariante es que el codigo "
                    "que corre aqui sea el que esta en este repositorio."
                )
    return directorio


def _a_vector(salida: Any, dimension: int, que: str) -> np.ndarray:
    """Saca el embedding de lo que devuelve `transformers`, sin adivinar.

    En `transformers` 5.x, `get_audio_features()` y `get_text_features()`
    devuelven `BaseModelOutputWithPooling`, y el embedding proyectado es
    `pooler_output`; con la API anterior devolvian el tensor pelado. Coger el
    objeto entero **no da un error**: da un vector inventado, y de ahi sale un
    coseno plausible. Por eso se comprueba tambien la dimension contra la que
    declara el modelo.
    """
    tensor = getattr(salida, "pooler_output", None)
    if tensor is None and hasattr(salida, "detach"):
        tensor = salida
    if tensor is None:
        raise TypeError(
            f"el modelo devolvio {type(salida).__name__} como embedding de {que}: ni es "
            "un tensor ni trae 'pooler_output'. La API de transformers ha cambiado y "
            "seguir adelante daria un vector que no es el embedding."
        )
    vector = np.asarray(tensor.detach().to("cpu").numpy(), dtype=np.float64).reshape(-1)
    if vector.shape != (dimension,):
        raise ValueError(
            f"el embedding de {que} tiene dimension {vector.shape[0]} y el modelo declara "
            f"{dimension}. No se compara lo que no vive en el mismo espacio."
        )
    return vector


class ClapDeTransformers:
    """CLAP real (`laion/clap-htsat-*`) cargado con `transformers` desde disco.

    Cumple `ModeloClap` y nada mas: dos metodos que devuelven vectores. Se
    construye **solo** desde `construir_modelo()`, que revalida la ficha antes.

    Tres decisiones que cambian el numero, escritas donde se toman:

    * **CPU.** No se pide dispositivo, asi que `transformers` carga en CPU y ahi
      se queda. §6.1 dice que la CPU es aceptable, y ademas deja libres los 8 GB
      de la GPU local para generar. Sin GPU por medio no hay diferencias por
      kernels de atencion ni por orden de reduccion. El audio entra en `float32`,
      que es el dtype de los pesos.
    * **No se remuestrea.** `embed_audio()` exige la tasa que declara el extractor
      del propio modelo; si no cuadra, para. Es la misma regla que aplica
      `medir_brief()` a los WAV.
    * **No se trunca el texto.** Recortar un prompt de estilo largo cambiaria el
      texto de referencia del §4.2 sin decirlo. Si un prompt no cabe en el
      codificador, es mejor que reviente a que mida otra cosa.

    La ultima ventana de una pista puede ser mas corta que la ventana declarada;
    el extractor la rellena repitiendola (`padding="repeatpad"`, de la propia
    configuracion del modelo). Es inherente a un modelo de entrada fija, y se
    aplica **igual a las tres series**, que es lo que §6.1 exige.
    """

    def __init__(self, ficha: FichaClap) -> None:
        directorio = _auditar_directorio_de_pesos(ficha)

        try:
            import torch  # noqa: PLC0415  (diferido: la mecanica no necesita torch)
            from transformers import ClapModel, ClapProcessor  # noqa: PLC0415
        except ImportError as exc:
            raise BackendNoDisponible(
                f"el backend {ficha.backend!r} necesita 'transformers' y 'torch' "
                f"instalados, y falta alguno: {exc}. La CPU basta; no hace falta GPU."
            ) from exc

        self._torch = torch
        self.ficha = ficha
        # `local_files_only`: nada de red en tiempo de ejecucion, ni un HEAD para
        # comprobar si hay revision mas nueva. La negativa a ejecutar codigo
        # remoto va explicita en las dos cargas aunque ya sea el valor por
        # defecto: es un invariante, no una preferencia, y un valor por defecto
        # puede cambiar de version.
        self._procesador = ClapProcessor.from_pretrained(
            str(directorio), local_files_only=True, trust_remote_code=False,
        )
        self._modelo = ClapModel.from_pretrained(
            str(directorio),
            local_files_only=True,
            use_safetensors=True,
            trust_remote_code=False,
        )
        # Modo de inferencia. Se usa `train(False)` y no su alias corto porque el
        # test que veta la resolucion dinamica de codigo busca esa subcadena en el
        # fuente; son la misma llamada.
        self._modelo.train(False)

        extractor = self._procesador.feature_extractor
        self.dimension = int(self._modelo.config.projection_dim)
        self.tasa_entrada_hz = int(extractor.sampling_rate)
        self.ventana_s = float(extractor.nb_max_samples) / self.tasa_entrada_hz

        # La ficha describe el modelo; si lo que hay en disco no coincide, es la
        # ficha la que miente sobre la medida que se va a publicar. §6.1 obliga a
        # anotar tasa y ventana: anotar unas y usar otras seria peor que no
        # anotarlas.
        if self.tasa_entrada_hz != ficha.tasa_entrada_hz:
            raise FichaInvalida(
                f"la ficha declara {ficha.tasa_entrada_hz} Hz de entrada y el extractor "
                f"del modelo consume {self.tasa_entrada_hz} Hz. El informe anotaria una "
                "tasa que no es la que se uso."
            )
        if abs(self.ventana_s - ficha.ventana_s) > 1e-6:
            raise FichaInvalida(
                f"la ficha declara ventanas de {ficha.ventana_s} s y el modelo consume "
                f"{self.ventana_s} s ({extractor.nb_max_samples} muestras). Con una "
                "ventana mas larga el modelo comprimiria lo que sobra, y con una mas "
                "corta rellenaria repitiendo: en los dos casos se mediria otra cosa."
            )

    def embed_texto(self, texto: str) -> np.ndarray:
        """Vector del prompt de estilo literal del brief (§4.2), sin reescribir."""
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError(
                "el texto de referencia esta vacio: no hay prompt contra el que medir."
            )
        entradas = self._procesador(text=[texto], return_tensors="pt", padding=True)
        with self._torch.inference_mode():
            salida = self._modelo.get_text_features(**entradas)
        return _a_vector(salida, self.dimension, "texto")

    def embed_audio(self, ventana: np.ndarray, tasa: int) -> np.ndarray:
        """Vector de una ventana de audio mono, a la tasa que exige el modelo."""
        if int(tasa) != self.tasa_entrada_hz:
            raise ValueError(
                f"ventana a {tasa} Hz y el modelo consume {self.tasa_entrada_hz} Hz. "
                "Aqui no se remuestrea: cambiaria la medida sin dejar rastro."
            )
        muestras = np.asarray(ventana, dtype=np.float32).reshape(-1)
        if muestras.size == 0:
            raise ValueError("ventana vacia: no hay audio que embeber")
        entradas = self._procesador(
            audio=muestras, sampling_rate=self.tasa_entrada_hz, return_tensors="pt",
        )
        with self._torch.inference_mode():
            salida = self._modelo.get_audio_features(**entradas)
        return _a_vector(salida, self.dimension, "audio")


def construir_modelo(ficha: FichaClap) -> ModeloClap:
    """Resuelve el backend que **nombra** la ficha, con un `if` explicito.

    La ficha es un dato del disco: nombra, no importa. La correspondencia entre
    el nombre y el codigo que se ejecuta vive aqui, en este fichero, y cambiarla
    exige un commit — que es justo el punto de control que se busca (I-13b).

    Levanta:
        BackendNoDisponible: si la ficha nombra un backend que este repositorio
            no sabe ejecutar, o si le faltan las dependencias al que si sabe.
        FichaInvalida: si el directorio de pesos contradice la ficha o rompe un
            invariante (varios ficheros de pesos, un pickle al lado, codigo
            remoto declarado).
        ValueError: desde `exigir_ficha_valida()`, si la ficha se construyo a
            mano saltandose `cargar_ficha()`.
    """
    exigir_ficha_valida(ficha)
    if ficha.backend not in BACKENDS_CLAP:
        raise BackendNoDisponible(
            f"la ficha nombra el backend {ficha.backend!r} y este repositorio solo sabe "
            f"ejecutar {sorted(BACKENDS_CLAP)}.\n"
            "Anadir uno exige escribir su constructor aqui, en un commit, y archivar "
            "antes su ficha de licencia verificada contra fuente primaria (I-13b). "
            "Nada se resuelve por nombre."
        )
    if ficha.backend == BACKEND_TRANSFORMERS:
        return ClapDeTransformers(ficha)
    raise BackendNoDisponible(
        f"{ficha.backend!r} figura en BACKENDS_CLAP pero no tiene constructor escrito. "
        "Es un fallo de este fichero, no de la ficha: la lista y los constructores se "
        "escriben juntos."
    )


# --------------------------------------------------------------------------- #
# Mecanica de la medida: ventanas, coseno, media
# --------------------------------------------------------------------------- #

class Audio(NamedTuple):
    """Audio mono en float, con su tasa de muestreo."""

    muestras: np.ndarray
    tasa: int


class MedidaPista(NamedTuple):
    """Lo medido en una pista: la media y las similitudes que la componen."""

    media: float
    similitudes: list[float]
    n_ventanas: int
    duracion_s: float


def similitud_coseno(a: np.ndarray, b: np.ndarray) -> float:
    """Coseno entre dos vectores, normalizando aqui y no confiando en el modelo.

    Levanta:
        ValueError: si las dimensiones no coinciden o si algun vector es nulo.
            Un vector nulo no tiene direccion: devolver 0 se leeria como «no se
            parece» y devolver `nan` se colaria en la media. Las dos son
            mentiras distintas, y las dos ensucian un numero que decide un gate.
    """
    va = np.asarray(a, dtype=np.float64).reshape(-1)
    vb = np.asarray(b, dtype=np.float64).reshape(-1)
    if va.shape != vb.shape:
        raise ValueError(
            f"dimension distinta entre los vectores: {va.shape} y {vb.shape}. "
            "El de audio y el de texto tienen que vivir en el mismo espacio."
        )
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        raise ValueError(
            "vector nulo: no tiene direccion, asi que no hay coseno que calcular."
        )
    return float(np.dot(va, vb) / (na * nb))


def ventanas(muestras: np.ndarray, tasa: int, ventana_s: float = VENTANA_S) -> list[np.ndarray]:
    """Trocea el audio en ventanas **no solapadas** que cubren la pista entera.

    La ultima ventana se devuelve aunque sea mas corta (§6.1: cubrir la pista
    entera). Descartarla seria ignorar el final de cada pista sin decirlo, y el
    final es justo donde el protocolo mira el cierre (D3) en varios briefs.

    Con UN limite: una cola por debajo de `MIN_VENTANA_S` se descarta. Sin el, la
    cifra dependia de la duracion modulo 10 s con un salto enorme —una pista de
    40,00 s daba 4 ventanas y la misma con 0,02 s mas daba 5, y esa quinta de 960
    muestras pesaba igual que las otras cuatro (revision 2026-09-03)—. Un
    fragmento de 20 ms no lleva contenido musical que ningun modelo pueda juzgar:
    lo que aporta es ruido con voto. La cola descartada nunca pasa de
    `MIN_VENTANA_S`, asi que «cubrir la pista entera» se sigue cumpliendo salvo
    por menos de un segundo, y eso se declara en la politica del informe.

    Levanta:
        ValueError: si el audio esta vacio, si la ventana no es positiva o si la
            pista entera es mas corta que `MIN_VENTANA_S`. Un audio vacio no vale
            0,0 de similitud: vale «aqui no hay pista».
    """
    if ventana_s <= 0:
        raise ValueError(f"ventana_s tiene que ser positiva, y es {ventana_s!r}")
    if tasa <= 0:
        raise ValueError(f"tasa de muestreo no valida: {tasa!r}")
    x = np.asarray(muestras).reshape(-1)
    if x.size == 0:
        raise ValueError("audio vacio: no hay nada que medir")

    paso = max(1, int(round(ventana_s * tasa)))
    minimo = max(1, int(round(MIN_VENTANA_S * tasa)))
    if x.size < minimo:
        raise ValueError(
            f"pista de {x.size / tasa:.3f} s: mas corta que el minimo de "
            f"{MIN_VENTANA_S} s. No hay contenido que medir."
        )
    trozos = [x[i:i + paso] for i in range(0, x.size, paso)]
    # La cola corta se descarta; nunca llega a MIN_VENTANA_S y siempre queda al
    # menos una ventana, porque arriba se exigio que la pista la alcance.
    return [t for t in trozos if t.size >= minimo]


def medir_pista(
    audio: Audio,
    texto: str,
    modelo: ModeloClap,
    ventana_s: float = VENTANA_S,
) -> MedidaPista:
    """Similitud media de una pista contra su prompt de estilo literal.

    El texto se embebe **una vez** por pista: no cambia entre ventanas, y
    re-embeberlo abriria la puerta a que un modelo con aleatoriedad interna
    devolviera vectores distintos dentro de la misma pista.
    """
    trozos = ventanas(audio.muestras, audio.tasa, ventana_s)
    vector_texto = modelo.embed_texto(texto)
    similitudes = [
        similitud_coseno(modelo.embed_audio(trozo, audio.tasa), vector_texto)
        for trozo in trozos
    ]
    # Media SIMPLE, una por ventana, porque es lo que §6.1 prescribe literalmente
    # («ventanas no solapadas que cubren la pista entera, y **media** de las
    # similitudes»). Ponderar por duracion seria mas defendible en abstracto —una
    # ventana de media pesaria la mitad— pero cambiar como se agrega es cambiar
    # la aritmetica de un criterio del gate, y eso lo firma el propietario, no lo
    # decide este script. El artefacto que la media simple tenia con colas
    # diminutas se resuelve en `ventanas()`, descartandolas, que no toca la
    # formula.
    return MedidaPista(
        media=float(statistics.fmean(similitudes)),
        similitudes=similitudes,
        n_ventanas=len(trozos),
        duracion_s=audio.muestras.size / audio.tasa,
    )


# --------------------------------------------------------------------------- #
# El par de un brief: propia contra libreria
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ParBrief:
    """Lo medido en un brief. Se publica entero, no solo si gana."""

    brief: str
    texto: str
    propia: MedidaPista
    libreria: MedidaPista | None
    nota: str = ""

    @property
    def clap_propia(self) -> float:
        return self.propia.media

    @property
    def clap_libreria(self) -> float | None:
        return None if self.libreria is None else self.libreria.media

    @property
    def diferencia(self) -> float | None:
        """`propia - libreria`, el tamano del efecto que pide A-14."""
        return None if self.libreria is None else self.propia.media - self.libreria.media

    @property
    def propia_gana_o_empata(self) -> bool:
        """`propia >= libreria` (§2, criterio 3: el empate cuenta como cumplido).

        Un brief **sin linea base** cuenta como **no cumplido**, por §2.1: «un
        brief sin linea base es un brief sin evidencia, y la carga de la prueba
        la tiene el modelo propio, no la libreria».
        """
        if self.libreria is None:
            return False
        return self.propia.media >= self.libreria.media

    def a_dict(self) -> dict[str, Any]:
        return {
            "brief": self.brief,
            "texto": self.texto,
            "clap_propia": self.clap_propia,
            "clap_libreria": self.clap_libreria,
            "diferencia": self.diferencia,
            "propia_gana_o_empata": self.propia_gana_o_empata,
            "similitudes_propia": self.propia.similitudes,
            "similitudes_libreria": None if self.libreria is None else self.libreria.similitudes,
            "ventanas_propia": self.propia.n_ventanas,
            "ventanas_libreria": None if self.libreria is None else self.libreria.n_ventanas,
            "duracion_propia_s": self.propia.duracion_s,
            "duracion_libreria_s": None if self.libreria is None else self.libreria.duracion_s,
            "nota": self.nota,
        }


def _comprobar_tasa(audio: Audio, ficha: FichaClap, que: str) -> None:
    if audio.tasa != ficha.tasa_entrada_hz:
        raise ValueError(
            f"{que}: la tasa de muestreo es {audio.tasa} Hz y la ficha declara "
            f"{ficha.tasa_entrada_hz} Hz. Aqui no se remuestrea en silencio: cambiaria "
            "la medida sin dejar rastro, y §6.1 exige que la politica sea identica "
            "para las tres series. Remuestrea fuera, declaralo, y vuelve a pasar."
        )


def medir_brief(
    brief: str,
    texto: str,
    propia: Audio,
    libreria: Audio | None,
    modelo: ModeloClap,
    ficha: FichaClap,
) -> ParBrief:
    """Mide el par `(propia, libreria)` de un brief con la misma politica.

    `ficha` no es decorativo: pide un `FichaClap` —que solo sale de
    `cargar_ficha()`— para que no se pueda medir con un modelo sin licencia
    comprobada, y de el sale la ventana y la tasa esperada.

    `libreria=None` es un caso legitimo y previsto: se registra con su nota y
    cuenta como **no cumplido** (§2.1).
    """
    exigir_ficha_valida(ficha)
    _comprobar_tasa(propia, ficha, f"{brief}/propia")
    medida_propia = medir_pista(propia, texto, modelo, ficha.ventana_s)

    if libreria is None:
        return ParBrief(
            brief=brief,
            texto=texto,
            propia=medida_propia,
            libreria=None,
            nota=(
                "sin linea base de libreria utilizable: cuenta como NO cumplido "
                "(g1-protocolo.md §2.1)"
            ),
        )

    _comprobar_tasa(libreria, ficha, f"{brief}/libreria")
    return ParBrief(
        brief=brief,
        texto=texto,
        propia=medida_propia,
        libreria=medir_pista(libreria, texto, modelo, ficha.ventana_s),
    )


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #

def informe(pares: list[ParBrief], ficha: FichaClap) -> dict[str, Any]:
    """Arma el informe: identidad del modelo, pares en bruto, resumen y aviso.

    Lo que **no** lleva: ningun umbral, ninguna comparacion contra un liston y
    ninguna palabra que se parezca a un veredicto. Este script mide; el gate lo
    cierra el acta con la aritmetica de §8.
    """
    exigir_ficha_valida(ficha)
    diferencias = [p.diferencia for p in pares if p.diferencia is not None]
    resumen = {
        "briefs_medidos": len(pares),
        "propia_gana_o_empata": sum(1 for p in pares if p.propia_gana_o_empata),
        "sin_linea_base": sum(1 for p in pares if p.libreria is None),
        "diferencia_media": float(statistics.fmean(diferencias)) if diferencias else None,
        "diferencia_mediana": float(statistics.median(diferencias)) if diferencias else None,
    }

    return {
        "medida": "clap-audio-texto",
        "referencia": "g1-protocolo.md §6.1 (criterio 3 de §2)",
        "advertencia": ADVERTENCIA_CRITERIO_3,
        "modelo": {
            "id": ficha.id,
            "version": ficha.version,
            "backend": ficha.backend,
            "sha256": ficha.sha256,
            "pesos": str(ficha.ruta_pesos),
            "licencia_spdx": ficha.licencia_spdx,
            "licencia_verificada_por": ficha.licencia_verificada_por,
            "licencia_verificada_el": ficha.licencia_verificada_el,
            "licencia_fuente": ficha.licencia_fuente,
            "tasa_entrada_hz": ficha.tasa_entrada_hz,
        },
        "politica": {
            "ventana_s": ficha.ventana_s,
            "ventanas": POLITICA_VENTANAS,
            "agregacion": POLITICA_AGREGACION,
            # §6.1 exige anotar la politica para que G1-bis la repita igual. Esta
            # DESVIACION va escrita en el informe, no solo en el codigo: es lo
            # unico que separa este calculo de la letra del protocolo.
            "cola_minima_s": MIN_VENTANA_S,
            "desviacion_declarada": (
                f"Una cola final por debajo de {MIN_VENTANA_S} s se DESCARTA en vez de "
                "contar como una ventana mas. §6.1 dice «cubren la pista entera», asi que "
                "esto se aparta de su letra en menos de un segundo por pista. El motivo: "
                "con media simple —que es la que §6.1 prescribe— una cola de 0,02 s pesaba "
                "igual que una ventana de 10 s, y la cifra saltaba segun la duracion modulo "
                "la ventana. La agregacion NO se ha tocado: sigue siendo la media simple."
            ),
            "texto_de_referencia": "prompt de estilo literal del brief (§4.2), sin reescribir",
        },
        "briefs": [p.a_dict() for p in pares],
        "resumen": resumen,
    }


def _fmt(valor: float | None, ancho: int = 7) -> str:
    """Numero a tres decimales, o un guion si no lo hay. Ancho fijo: estas
    columnas se leen comparando de un vistazo, y una tabla descuadrada se lee
    mal justo donde importa."""
    return f"{'-':>{ancho}}" if valor is None else f"{valor:{ancho}.3f}"


def formatear(inf: dict[str, Any]) -> str:
    """Version legible del informe, con la advertencia delante y detras.

    Delante porque se lee antes que los numeros; detras porque, cuando alguien
    copia la ultima parte de la salida al acta, la advertencia va con ella.
    """
    m = inf["modelo"]
    lineas = [
        ADVERTENCIA_CRITERIO_3,
        "",
        f"CLAP audio-texto · {inf['referencia']}",
        f"modelo: {m['id']} @ {m['version']} · backend {m['backend']}",
        f"pesos:  {m['sha256'][:16]}... · {m['licencia_spdx']} "
        f"(verificada por {m['licencia_verificada_por']} el {m['licencia_verificada_el']})",
        f"entrada: {m['tasa_entrada_hz']} Hz · ventana {inf['politica']['ventana_s']} s",
        f"ventanas: {inf['politica']['ventanas']}",
        f"agregacion: {inf['politica']['agregacion']}",
        "",
        f"{'brief':8} {'propia':>7} {'libreria':>9} {'dif.':>7}  propia >= libreria",
    ]
    for fila in inf["briefs"]:
        marca = "si" if fila["propia_gana_o_empata"] else "no"
        nota = f"   ({fila['nota']})" if fila["nota"] else ""
        lineas.append(
            f"{fila['brief']:8} {_fmt(fila['clap_propia'])} {_fmt(fila['clap_libreria'], 9)} "
            f"{_fmt(fila['diferencia'])}  {marca}{nota}"
        )

    r = inf["resumen"]
    lineas += [
        "",
        f"briefs medidos: {r['briefs_medidos']} · con propia >= libreria: "
        f"{r['propia_gana_o_empata']} · sin linea base: {r['sin_linea_base']}",
        f"tamano del efecto (propia - libreria): media {_fmt(r['diferencia_media'])} · "
        f"mediana {_fmt(r['diferencia_mediana'])}",
        "",
        ADVERTENCIA_CRITERIO_3,
    ]
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Entrada/salida de audio
# --------------------------------------------------------------------------- #

def leer_wav(ruta: str | Path) -> Audio:
    """Lee un WAV PCM de 16 bits y devuelve mono en float64 [-1, 1).

    Solo WAV, y a proposito: **no hay ffmpeg en esta maquina** y no se va a
    instalar, asi que cualquier conversion ocurre fuera y queda declarada. Es la
    misma lectura que usa `medir_ab.py`, para que las dos mediciones vean
    exactamente el mismo audio.
    """
    ruta = Path(ruta)
    with wave.open(str(ruta), "rb") as w:
        canales, ancho, tasa, n_tramas = (
            w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes(),
        )
        crudo = w.readframes(n_tramas)
    if ancho != 2:
        raise ValueError(f"{ruta.name}: se esperaba PCM de 16 bits, hay {ancho * 8}.")
    datos = np.frombuffer(crudo, dtype="<i2").astype(np.float64) / 32768.0
    return Audio(datos.reshape(-1, canales).mean(axis=1), tasa)


# --------------------------------------------------------------------------- #
# Linea de comandos
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    """Puerta de licencia primero, backend despues, material al final.

    Codigos de salida: `2` ficha invalida · `3` backend no disponible o
    directorio de pesos rechazado · `4` modelo listo pero el material del gate no
    se lee todavia (ver el final de la funcion). Nunca devuelve `0` sin medir:
    un cero silencioso se leeria como «medido y sin novedad».
    """
    p = argparse.ArgumentParser(
        description=(
            "Mide el criterio 3 de G1 (CLAP audio-texto). Requiere ficha de modelo "
            "con licencia verificada; el modelo NO se descarga aqui."
        )
    )
    p.add_argument("--ficha", required=True, help="ruta de la ficha <modelo>.model.json")
    p.add_argument("--directorio", required=True, help="directorio con el material del gate")
    p.add_argument("--salida", default=None, help="fichero JSON del informe")
    args = p.parse_args(argv)

    try:
        ficha = cargar_ficha(args.ficha)
    except FichaInvalida as exc:
        print(f"[ficha] no se puede medir: {exc}")
        return 2

    print(
        f"[ficha] {ficha.id} @ {ficha.version} · {ficha.licencia_spdx} "
        f"(verificada por {ficha.licencia_verificada_por} el {ficha.licencia_verificada_el})"
    )
    print(f"[ficha] pesos {ficha.ruta_pesos.name} · sha256 {ficha.sha256[:16]}...")

    try:
        modelo = construir_modelo(ficha)
    except (BackendNoDisponible, FichaInvalida) as exc:
        print(f"[backend] {exc}")
        return 3

    print(
        f"[modelo] backend {ficha.backend} cargado de {ficha.ruta_pesos.parent} "
        f"(sin red, sin codigo remoto) · embeddings de "
        f"{getattr(modelo, 'dimension', '?')}-d"
    )

    # Lo que falta ya no es el modelo: es el material. El emparejado de los 10
    # briefs (que par de ficheros y que prompt literal va con cada uno) lo fija
    # T-09 y se archiva en `07-metricas/README.md` (§6.1). Leer un directorio a
    # ojo seria inventarse la mitad del procedimiento del gate, asi que esto para
    # aqui y lo dice, en vez de devolver 0 como si hubiera medido algo.
    print(
        f"[material] no se ha leido {args.directorio}: el emparejado de los briefs "
        "(§6.1, lo fija T-09 y se archiva en 07-metricas/README.md) no esta definido. "
        "La API de Python si mide: medir_brief(...) con este modelo."
    )
    if args.salida:
        print(f"[material] tampoco se ha escrito {args.salida}: no hay nada que escribir.")
    print(f"[aviso] {ADVERTENCIA_CRITERIO_3}")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
