#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kit de ejecucion del gate G1: genera la SERIE PROPIA de las 10 pistas.

Que es esto y que NO es
=======================
Esto **prepara** el gate G1; **no lo ejecuta**. Genera la serie propia (ACE-Step
1.5) de los 10 briefs de `gates/g1-protocolo.md` §4, la deja anonimizada con su
mapa sellado y escribe el registro tecnico que el acta necesita. **Lo que decide
el gate — escuchar y puntuar — lo hace el propietario**, y este script no lo
toca: no puntua, no compara, no abre el mapa y no escribe veredicto alguno.

Tampoco genera las lineas base (Suno, libreria). Esas son §5.1 y salen de fuera.

Fuente de verdad: el protocolo, no este fichero
-----------------------------------------------
Los 10 briefs **se leen del propio `g1-protocolo.md` §4** en cada arranque, no
estan copiados aqui. Es deliberado: §4 los declara «PROPUESTOS — pendientes de
ratificacion del propietario», que puede sustituir cualquiera **antes de
generar** (§9). Si estuvieran duplicados en el codigo, una sustitucion en el
protocolo no llegaria al audio y el gate mediria otra cosa que la ratificada.
El SHA-256 del protocolo leido queda en el informe: si alguien edita §4 despues,
se ve.

Los cinco umbrales del §2 **no aparecen en este fichero**, ni siquiera como
comentario. Este script no comprueba umbrales; solo produce material.

Las cuatro cosas que el 2026-09-02 se aprendieron a la fuerza
=============================================================
Van cableadas aqui porque cada una costo una tanda de GPU:

1. **Etiquetas de seccion canonicas.** ACE-Step espera `[intro]`, `[verse]`,
   `[chorus]`, `[bridge]`, `[outro]`. Las de estilo Suno
   (`[VERSO 1 - HOMBRE, entra el beat]`) **viajan verbatim al modelo** y
   empeoran el resultado; con las canonicas el pulso salio un 47 % mas marcado.
   `validar_letra()` **rechaza** cualquier otra etiqueta: es un fallo bloqueante,
   no un aviso, porque una pista generada con etiquetas malas no se puede
   distinguir por el nombre del fichero y contaminaria la sesion entera.
2. **Tildes y enyes.** El normalizador es NFC y no elimina acentos: «sonar» y
   «sonar» son palabras distintas y secuencias de tokens distintas. Una letra
   castellana sin una sola tilde casi siempre es una letra a la que se le han
   caido, asi que se bloquea (escape consciente: `--permitir-sin-tildes`).
3. **Metadatos poblados.** `bpm`, `keyscale` y `timesignature` iban en `N/A` por
   defecto. El BPM sale de la columna «Tempo» del §4; el modo, del caracter
   declarado; el compas es 4/4. Ver `derivar_tonalidad()` para lo que es
   derivacion y lo que es convencion.
4. **Planificador de 5 Hz siempre puesto.** Su efecto medido es del 60,7 %
   frente al 1-7 % del ruido de semilla. `usar_lm=True` no es opcional aqui:
   `--sin-lm` **no existe** en este script a proposito.

El limitador de picos (techo -1 dBFS) no es una opcion del shim: es
incondicional. Aun asi se **verifica** antes de cargar (`_verificar_limitador`),
porque el motivo por el que existe es justamente G1: un recorte duro nuestro se
oiria en la dimension 2 de la rubrica y penalizaria a ACE-Step por un fallo de
exportacion que es nuestro.

Ciego, y por que la ceguera empieza aqui
========================================
§5.4 anonimiza **series** (propia / Suno / libreria) y eso ocurre despues, con
las tres series sobre la mesa. Pero hay un ciego ANTES, y este script es el
unico sitio donde se puede montar: §5.2 obliga al propietario a elegir **una
toma de tres** por brief, comparando solo dentro de la serie propia. Si los
ficheros se llamaran `B01-toma1/2/3`, esa eleccion estaria anclada por el orden
(«la primera» o «la ultima» siempre pesan). Por eso:

* el nombre es opaco y **no ordenado**: `B01-3f9a2c.wav`, donde el testigo es
  `sha256(semilla_maestra|brief|toma)[:6]`;
* el **orden de generacion se baraja** dentro de cada brief, para que la fecha
  de modificacion del fichero tampoco reconstruya el indice de toma;
* el registro tecnico (`02-generado/propio/registro-tecnico.json`) se puede
  abrir sin romper nada: lleva tiempos, VRAM y nivel de GPU, pero **no lleva ni
  la semilla ni el indice de toma**;
* la semilla y el indice viven **solo** en `05-ciego/mapa-tomas.csv`, que se
  sella con SHA-256 (§5.6) y no se abre hasta despues de elegir.

**Riesgo residual, declarado** (como manda §5.4.5): el `mtime` sigue existiendo
y el propietario podria ordenar por fecha para reconstruir el orden de
generacion — pero ese orden ya esta barajado, asi que no da el indice de toma.
Lo que no se puede evitar es que quien ejecuta el script vea la consola mientras
corre. Si eso importa, se redirige la salida a fichero y no se mira.

Lo que este script NO decide y deja abierto
===========================================
* **Las letras las escribe el propietario** (§4.1, precondicion 7 de §9.1). No
  se inventan aqui. Sin la letra de un brief, ese brief **no se genera**.
* La **tonica** de `keyscale` es una convencion, no una decision musical: ver
  `derivar_tonalidad()`.
* El **numero de tomas por brief es 3** (§5.2). `--tomas 1` existe para un
  ensayo, y el informe queda marcado como `sesion_no_conforme_5_2`.

Uso
===
Ensayo en seco (no toca la GPU, no escribe audio, no necesita contenedor)::

    python apps/runner/spikes/g1_generar.py --dry-run \\
        --letras D:/srv/ace-step/letras/g1

Generacion real: ver `spikes/README.md`, seccion «Kit de ejecucion de G1».
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.util
import json
import logging
import os
import random
import re
import sys
import time
import traceback
import unicodedata
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AQUI = Path(__file__).resolve()

# --------------------------------------------------------------------------- #
# Constantes del protocolo que este script APLICA (no las decide)
# --------------------------------------------------------------------------- #

#: Ruta por defecto del protocolo, relativa a la raiz del repositorio. Se puede
#: sobreescribir con --protocolo (en el contenedor el repo no esta montado
#: entero, asi que ahi se pasa la ruta del bind mount).
PROTOCOLO_REL = Path("docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md")

#: Etiquetas de seccion que ACE-Step entiende. Cualquier otra se rechaza.
#: Medido el 2026-09-02: las etiquetas descriptivas de estilo Suno no se
#: interpretan, se cantan.
ETIQUETAS_CANONICAS = frozenset({"intro", "verse", "chorus", "bridge", "outro"})

#: Tomas por brief y por serie que exige §5.2. No es un valor por defecto
#: comodo: es el numero del protocolo.
TOMAS_PROTOCOLO = 3

#: Compas por defecto. Ninguno de los 10 briefs de §4 pide metrica impar, asi
#: que 4/4 para los diez y se congela (§5.2, «el resto de parametros ... es
#: identico para los 10 briefs»).
COMPAS_POR_DEFECTO = "4/4"

#: Tonica de cada modo. NO es una decision musical: ver derivar_tonalidad().
TONICA_MENOR = "A minor"
TONICA_MAYOR = "C major"

#: Palabras del caracter declarado que empujan a modo menor. La lista sale de
#: leer la columna «Genero / caracter» del §4, no de teoria musical general.
_PALABRAS_MENOR = (
    "melancolico", "melancolica", "oscuro", "oscura", "solemne", "fragil",
    "contenida", "contenido", "nocturno", "nocturna", "triste", "epico", "epica",
)

#: Mediciones reales del 2026-09-02 en la GTX 1070 (tier3), con el artefacto CON
#: planificador, `usar_lm=True` y `lm_cfg=2.0`. De aqui sale la estimacion, y
#: por eso se archiva la procedencia: para poder recalibrarla en otra maquina
#: sustituyendo la tabla, no adivinando un factor.
#:
#: (duracion_pedida_s, total_s, fichero de informe del que sale)
MEDICIONES_TIER3: tuple[tuple[int, float, str], ...] = (
    (25, 42.532, "ab-planificador-informe.json"),
    (25, 46.838, "ab-planificador-informe.json"),
    (25, 49.350, "lm-on-informe.json"),
    (25, 110.634, "t05-carga-contigua2-informe.json"),
    (25, 113.056, "t05-final-informe.json"),
    (60, 86.999, "ab-planificador-informe.json"),
    (60, 119.530, "con-limitador-informe.json"),
    (240, 622.857, "libre-canonica-informe.json"),
    (240, 690.348, "libre-informe.json"),
)

#: Arranque en frio medido (carga total: weights_download + vram_load + warmup)
#: con lectura contigua de pesos. 109,70 s y 116,37 s en dos corridas.
CARGA_EN_FRIO_S = (109.70, 116.37)


# --------------------------------------------------------------------------- #
# Briefs: se LEEN del protocolo
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Brief:
    """Un brief de §4 con sus seis ejes verificables mas el destino."""

    id: str                 # "B-01"
    uso_final: str
    genero: str
    bpm: int
    instrumentacion: str
    voz: str
    idioma: str             # "es" | "en"
    duracion_s: int
    destino: str            # "streaming" | "broadcast"
    exigencia: str

    @property
    def clave(self) -> str:
        """Identificador sin guion, para nombres de fichero: `B01`."""
        return self.id.replace("-", "")


def _limpiar_markdown(texto: str) -> str:
    """Quita el marcado de la celda y deja el texto que va al modelo.

    Es literal a proposito: `**castellano**` -> `castellano`, `*chorus*` ->
    `chorus`, `«Cuaderno de ruido»` se conserva. Lo que llega al prompt tiene que
    ser lo que dice la tabla, no una reescritura.
    """
    texto = texto.replace("**", "").replace("`", "")
    texto = re.sub(r"\*(?=\S)(.+?)(?<=\S)\*", r"\1", texto)
    return " ".join(texto.split()).strip()


def _sin_acentos_min(texto: str) -> str:
    """Minusculas y sin diacriticos. **Solo para comparar palabras clave.**

    Nunca se aplica a nada que viaje al modelo: ahi las tildes son
    imprescindibles (ver cabecera, punto 2).
    """
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def _parsear_duracion(celda: str) -> int:
    """«**3:00**» -> 180 · «**45 s** con final resuelto» -> 45 · «30 s exactos» -> 30."""
    limpio = _limpiar_markdown(celda)
    m = re.search(r"(\d+)\s*:\s*(\d{2})", limpio)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r"(\d+)\s*s\b", limpio)
    if m:
        return int(m.group(1))
    raise ValueError(f"No se pudo leer la duracion de la celda {celda!r}.")


def _parsear_bpm(celda: str) -> int:
    m = re.search(r"(\d+)", _limpiar_markdown(celda))
    if not m:
        raise ValueError(f"No se pudo leer el tempo de la celda {celda!r}.")
    return int(m.group(1))


def _parsear_idioma(celda_voz: str) -> str:
    """Devuelve el codigo de `vocal_language` a partir de la columna «Voz / idioma»."""
    plano = _sin_acentos_min(celda_voz)
    if "castellano" in plano or "espanol" in plano:
        return "es"
    if "ingles" in plano or "english" in plano:
        return "en"
    raise ValueError(f"No se pudo leer el idioma del canto de la celda {celda_voz!r}.")


def leer_briefs(ruta_protocolo: Path) -> list[Brief]:
    """Extrae los 10 briefs de la tabla de §4 del protocolo.

    Se buscan las filas cuya primera celda sea `**B-NN**`. No se busca por numero
    de linea ni por indice de tabla: si alguien reordena el documento, esto sigue
    encontrandolas, y si desaparecen, falla en vez de generar de menos.
    """
    if not ruta_protocolo.is_file():
        raise SystemExit(
            f"No se encontro el protocolo en {ruta_protocolo}. Indicalo con "
            "--protocolo (dentro del contenedor hay que montar la carpeta gates/)."
        )
    texto = ruta_protocolo.read_text(encoding="utf-8")
    briefs: list[Brief] = []
    for linea in texto.splitlines():
        if not linea.lstrip().startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) < 9:
            continue
        m = re.fullmatch(r"\*\*(B-\d{2})\*\*", celdas[0])
        if not m:
            continue
        try:
            briefs.append(
                Brief(
                    id=m.group(1),
                    uso_final=_limpiar_markdown(celdas[1]),
                    genero=_limpiar_markdown(celdas[2]),
                    bpm=_parsear_bpm(celdas[3]),
                    instrumentacion=_limpiar_markdown(celdas[4]),
                    voz=_limpiar_markdown(celdas[5]),
                    idioma=_parsear_idioma(celdas[5]),
                    duracion_s=_parsear_duracion(celdas[6]),
                    destino=_limpiar_markdown(celdas[7]).lower(),
                    exigencia=_limpiar_markdown(celdas[8]),
                )
            )
        except ValueError as exc:
            raise SystemExit(f"Fila de brief ilegible en §4 ({celdas[0]}): {exc}") from exc

    if len(briefs) != 10:
        raise SystemExit(
            f"§4 del protocolo declara 10 briefs y se leyeron {len(briefs)} "
            f"({[b.id for b in briefs]}). No se genera una serie incompleta: el "
            "gate se calcula sobre 10 y una muestra corta cambia todas las medias."
        )
    ids = [b.id for b in briefs]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"Briefs repetidos en §4: {ids}.")
    return briefs


# --------------------------------------------------------------------------- #
# Derivaciones mecanicas (§4.2)
# --------------------------------------------------------------------------- #

def _minuscula_inicial(texto: str) -> str:
    """Baja la inicial salvo si la palabra parece un nombre propio o una sigla.

    «Batería acústica» -> «batería acústica», pero «Rhodes» y «BPM» se quedan.
    Regla: solo se baja si la palabra tiene alguna minuscula despues de la
    primera letra Y no esta en la lista de nombres propios de instrumentos que
    aparecen en §4.
    """
    if not texto:
        return texto
    primera = texto.split()[0].strip(",")
    propios = {"Rhodes", "Hammond"}
    if primera in propios or primera.isupper():
        return texto
    return texto[0].lower() + texto[1:]


def derivar_prompt_estilo(brief: Brief) -> str:
    """Prompt de estilo unico del brief, derivado **mecanicamente** de la tabla.

    §4.2 exige exactamente esto: un unico prompt por brief, derivado de las
    columnas, usado **literal** en ACE-Step, en Suno, como consulta de libreria y
    como texto de referencia de CLAP. «No se reescribe el prompt entre modelos,
    ni se afina buscando un resultado mejor», porque un prompt distinto por
    modelo mide al que escribe prompts, no al modelo.

    De ahi que esto sea una plantilla fija y no una redaccion: si se pudiera
    ajustar por brief, alguien lo ajustaria — y al primer resultado flojo se
    ajustaria.

    Orden: genero/caracter, instrumentacion, voz, tempo, idioma del canto.

    De la columna «Voz / idioma» se separa el idioma, que va en el punto «·» y
    que ya se enuncia al final del prompt. Sin esa separacion el prompt decia
    «voz masculina media · castellano, 112 BPM, cantado en castellano»: el punto
    medio y el idioma repetido son ruido que el modelo tokeniza igual que el
    resto.
    """
    idioma_largo = "castellano" if brief.idioma == "es" else "ingles"
    voz = _limpiar_markdown(brief.voz.split("·")[0])
    return (
        f"{brief.genero}, {_minuscula_inicial(brief.instrumentacion)}, "
        f"voz {_minuscula_inicial(voz)}, {brief.bpm} BPM, cantado en {idioma_largo}"
    )


def derivar_tonalidad(brief: Brief) -> tuple[str, str]:
    """Devuelve `(keyscale, motivo)`.

    Que es derivacion y que es convencion — la distincion importa
    --------------------------------------------------------------
    El **modo** (mayor/menor) SI se deriva de un dato declarado por el brief: la
    columna «Genero / caracter» de §4. «melancolico», «oscuro», «solemne» o
    «fragil» piden menor; «luminoso», «optimista» o «calido», mayor.

    La **tonica** (la `A` de «A minor») **no la declara ningun brief**, asi que
    aqui no se deriva de nada: es una **convencion fija**, A para menor y C para
    mayor, la misma para los diez. Se elige constante en vez de variada por dos
    razones: §5.2 manda congelar lo que no sea un eje del brief, y una tonica
    distinta por pista seria una variable que nadie ha declarado y que ensuciaria
    la comparacion.

    Si el propietario quiere otra tonalidad en algun brief, la pone en el fichero
    de `--extra` y el informe registra que vino de ahi. Lo que no se hace es
    fingir que la tonica sale del brief.
    """
    plano = _sin_acentos_min(f"{brief.genero} {brief.uso_final}")
    for palabra in _PALABRAS_MENOR:
        if palabra in plano:
            return TONICA_MENOR, f"modo menor por «{palabra}» en el caracter declarado; tonica convencional"
    return TONICA_MAYOR, "modo mayor por defecto (sin palabras de caracter menor); tonica convencional"


# --------------------------------------------------------------------------- #
# Letras: las escribe el propietario, aqui solo se validan
# --------------------------------------------------------------------------- #

_RE_ETIQUETA = re.compile(r"\[([^\]]*)\]")
_ACENTOS_ES = set("áéíóúüñÁÉÍÓÚÜÑ")


@dataclass
class Letra:
    ruta: Path
    texto: str
    referencia_wer: str
    etiquetas: list[str]
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def valida(self) -> bool:
        return not self.errores


def _referencia_wer(texto: str) -> str:
    """Letra sin marcas de seccion: la referencia contra la que se calcula el WER.

    §4.1: «Si la letra que se envia al modelo lleva marcas de seccion
    (`[verse]`, `[chorus]`), la referencia de WER es la version **sin marcas**».
    Se archiva ya hecha para que en §6.2 nadie tenga que rehacerla a mano y
    meter una diferencia que no es del modelo.
    """
    sin_marcas = _RE_ETIQUETA.sub("", texto)
    lineas = [l.strip() for l in sin_marcas.splitlines()]
    return "\n".join(l for l in lineas if l).strip() + "\n"


def cargar_letra(directorio: Path, brief: Brief, permitir_sin_tildes: bool) -> Letra:
    """Lee y valida la letra del brief. **No la escribe ni la corrige.**"""
    candidatas = [directorio / f"{brief.id}.txt", directorio / f"{brief.clave}.txt"]
    ruta = next((c for c in candidatas if c.is_file()), None)
    if ruta is None:
        vacia = Letra(ruta=candidatas[0], texto="", referencia_wer="", etiquetas=[])
        vacia.errores.append(
            f"falta la letra: se busco {', '.join(str(c) for c in candidatas)}. "
            "§4.1 y §9.1 (precondicion 7) la ponen del lado del propietario; este "
            "script no inventa letras."
        )
        return vacia

    texto = ruta.read_text(encoding="utf-8")
    letra = Letra(
        ruta=ruta,
        texto=texto,
        referencia_wer=_referencia_wer(texto),
        etiquetas=[e.strip() for e in _RE_ETIQUETA.findall(texto)],
    )
    validar_letra(letra, brief, permitir_sin_tildes)
    return letra


def validar_letra(letra: Letra, brief: Brief, permitir_sin_tildes: bool) -> None:
    """Rellena `errores` (bloquean) y `avisos` (no bloquean) de una letra."""
    if not letra.texto.strip():
        letra.errores.append("la letra esta vacia.")
        return

    # (1) Etiquetas canonicas. Bloqueante, no aviso: una pista generada con
    #     etiquetas de estilo Suno no se distingue por el nombre del fichero y
    #     contaminaria la sesion. Medido el 2026-09-02.
    if not letra.etiquetas:
        letra.errores.append(
            "sin ninguna etiqueta de seccion. ACE-Step espera al menos "
            f"una de {sorted(ETIQUETAS_CANONICAS)}."
        )
    malas = sorted({e for e in letra.etiquetas if e.strip().lower() not in ETIQUETAS_CANONICAS})
    if malas:
        letra.errores.append(
            f"etiquetas no canonicas {malas}. ACE-Step solo interpreta "
            f"{sorted(ETIQUETAS_CANONICAS)}; el resto lo CANTA literalmente. "
            "Ejemplo real: «[VERSO 1 - HOMBRE, entra el beat]» acaba en el audio."
        )
    # Mayusculas: [VERSE] no es [verse] para un tokenizador.
    mal_caja = sorted({e for e in letra.etiquetas if e != e.lower() and e.lower() in ETIQUETAS_CANONICAS})
    if mal_caja:
        letra.errores.append(f"etiquetas en mayusculas {mal_caja}: se escriben en minusculas.")

    # (2) Tildes y enyes en las letras en castellano.
    if brief.idioma == "es" and not (set(letra.texto) & _ACENTOS_ES):
        mensaje = (
            "letra en castellano sin una sola tilde ni enye. Casi siempre "
            "significa que se han perdido al copiar. «sonar» y «sonar» son "
            "palabras distintas para el modelo y hundirian el WER por un fallo "
            "nuestro, no suyo."
        )
        if permitir_sin_tildes:
            letra.avisos.append(mensaje + " Aceptada por --permitir-sin-tildes.")
        else:
            letra.errores.append(mensaje + " Usa --permitir-sin-tildes si es intencionado.")

    # (3) Extension minima de §4.1.
    etiquetas_min = [e.strip().lower() for e in letra.etiquetas]
    estrofas = etiquetas_min.count("verse")
    estribillos = etiquetas_min.count("chorus")
    if brief.duracion_s >= 90:
        if estrofas < 2 or estribillos < 1:
            letra.errores.append(
                f"§4.1 pide para un brief de {brief.duracion_s} s (>= 1:30) "
                f"«dos estrofas y un estribillo»; hay {estrofas} [verse] y "
                f"{estribillos} [chorus]."
            )
    else:
        frases = [l for l in _referencia_wer(letra.texto).splitlines() if l.strip()]
        if len(frases) < 2:
            letra.errores.append(
                f"§4.1 pide para un brief corto ({brief.duracion_s} s) «un bloque "
                f"cantado completo con al menos dos frases»; hay {len(frases)}."
            )

    # (4) Densidad de letra frente a la duracion. Solo aviso: no hay regla
    #     numerica en el protocolo y el modelo estira o comprime.
    palabras = len(letra.referencia_wer.split())
    if palabras and brief.duracion_s:
        por_segundo = palabras / brief.duracion_s
        if por_segundo > 1.6:
            letra.avisos.append(
                f"{palabras} palabras para {brief.duracion_s} s ({por_segundo:.2f} "
                "palabras/s): mucha letra para el tiempo, riesgo de atropello."
            )
        elif por_segundo < 0.15:
            letra.avisos.append(
                f"{palabras} palabras para {brief.duracion_s} s ({por_segundo:.2f} "
                "palabras/s): poca letra, riesgo de tramos instrumentales largos."
            )


# --------------------------------------------------------------------------- #
# Plan de generacion
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Toma:
    """Una toma concreta: el brief, su indice y su etiqueta ciega."""

    brief_id: str
    indice: int              # 1..N; NO aparece en el nombre del fichero
    etiqueta_ciega: str      # "B01-3f9a2c"
    semilla: int
    duracion_s: int


def _testigo(semilla_maestra: int, brief_id: str, indice: int) -> str:
    """Testigo opaco y estable de una toma. No ordenado: no dice si es la 1 o la 3."""
    material = f"{semilla_maestra}|{brief_id}|{indice}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:6]


def _semilla_toma(semilla_maestra: int, brief_id: str, indice: int) -> int:
    """Semilla derivada: reproducible y distinta por (brief, toma).

    Derivada en vez de aleatoria para que una repeticion de §8.5 con la misma
    `--semilla-maestra` reproduzca exactamente la misma serie. Se acota a 31 bits
    porque el `torch.Generator` de `prepare_noise` toma un entero con signo.
    """
    material = f"semilla|{semilla_maestra}|{brief_id}|{indice}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big") & 0x7FFFFFFF


def construir_plan(briefs: list[Brief], tomas: int, semilla_maestra: int) -> list[Toma]:
    """Lista de tomas en el orden EN QUE SE VAN A GENERAR, ya barajado.

    El barajado es del ciego, no un capricho: sin el, el `mtime` de los ficheros
    reconstruye el indice de toma y la eleccion de §5.2 queda anclada por el
    orden. Se baraja con un `Random` propio sembrado con la semilla maestra, de
    modo que el orden es reproducible pero no adivinable a ojo, y **no** toca el
    RNG global (que es el que usa el modelo).
    """
    plan: list[Toma] = []
    for brief in briefs:
        for i in range(1, tomas + 1):
            plan.append(
                Toma(
                    brief_id=brief.id,
                    indice=i,
                    etiqueta_ciega=f"{brief.clave}-{_testigo(semilla_maestra, brief.id, i)}",
                    semilla=_semilla_toma(semilla_maestra, brief.id, i),
                    duracion_s=brief.duracion_s,
                )
            )
    # Se baraja SOLO dentro de cada brief: los briefs se generan en orden para
    # que un corte a media tanda deje briefs enteros y `--desde` sea util.
    barajador = random.Random(semilla_maestra ^ 0x6731)
    resultado: list[Toma] = []
    for brief in briefs:
        del_brief = [t for t in plan if t.brief_id == brief.id]
        barajador.shuffle(del_brief)
        resultado.extend(del_brief)
    return resultado


# --------------------------------------------------------------------------- #
# Estimacion de tiempo (§ «avisa antes de empezar»)
# --------------------------------------------------------------------------- #

def _recta_por_minimos_cuadrados(puntos: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(puntos)
    sx = sum(x for x, _ in puntos)
    sy = sum(y for _, y in puntos)
    sxx = sum(x * x for x, _ in puntos)
    sxy = sum(x * y for x, y in puntos)
    denominador = n * sxx - sx * sx
    if denominador == 0:
        raise ValueError("mediciones degeneradas: todas con la misma duracion.")
    b = (n * sxy - sx * sy) / denominador
    a = (sy - b * sx) / n
    return a, b


def modelo_de_tiempo() -> dict[str, tuple[float, float]]:
    """Tres rectas `total_s = a + b * duracion_s` a partir de MEDICIONES_TIER3.

    Por que un rango y no un numero
    -------------------------------
    El planificador de 5 Hz es autorregresivo y se para en EOS: su coste varia
    entre corridas de la MISMA duracion. Medido: cinco pistas de 25 s costaron
    entre 42,5 y 113,1 s. Un unico numero seria una estimacion falsamente
    precisa, asi que se dan tres:

    * `optimista`: recta por los dos puntos mas rapidos de cada extremo.
    * `central`: minimos cuadrados sobre las nueve mediciones.
    * `pesimista`: recta por los dos puntos mas lentos de cada extremo.

    Las tres coinciden en la pendiente (~2,7 s de computo por segundo de audio),
    que es el dato robusto; lo que varia es el termino fijo.
    """
    puntos = [(float(d), float(t)) for d, t, _ in MEDICIONES_TIER3]
    central = _recta_por_minimos_cuadrados(puntos)

    corta = min(d for d, _ in puntos)
    larga = max(d for d, _ in puntos)
    rapido_corto = min(t for d, t in puntos if d == corta)
    rapido_largo = min(t for d, t in puntos if d == larga)
    lento_corto = max(t for d, t in puntos if d == corta)
    lento_largo = max(t for d, t in puntos if d == larga)

    def recta(x0: float, y0: float, x1: float, y1: float) -> tuple[float, float]:
        b = (y1 - y0) / (x1 - x0)
        return y0 - b * x0, b

    return {
        "optimista": recta(corta, rapido_corto, larga, rapido_largo),
        "central": central,
        "pesimista": recta(corta, lento_corto, larga, lento_largo),
    }


def estimar(briefs: list[Brief], tomas: int) -> dict[str, Any]:
    """Estimacion de la tanda completa, con carga en frio incluida."""
    modelo = modelo_de_tiempo()
    audio_total = sum(b.duracion_s for b in briefs) * tomas

    def total_escenario(nombre: str) -> float:
        a, b = modelo[nombre]
        return sum(max(0.0, a + b * br.duracion_s) for br in briefs) * tomas

    carga = sum(CARGA_EN_FRIO_S) / len(CARGA_EN_FRIO_S)
    escenarios = {}
    for nombre in ("optimista", "central", "pesimista"):
        computo = total_escenario(nombre)
        escenarios[nombre] = {
            "computo_s": round(computo, 1),
            "carga_s": round(carga, 1),
            "total_s": round(computo + carga, 1),
            "total_min": round((computo + carga) / 60.0, 1),
        }

    a_c, b_c = modelo["central"]
    a_p, b_p = modelo["pesimista"]
    por_brief = [
        {
            "brief": br.id,
            "duracion_s": br.duracion_s,
            "tomas": tomas,
            "central_s": round(max(0.0, a_c + b_c * br.duracion_s) * tomas, 1),
            "pesimista_s": round(max(0.0, a_p + b_p * br.duracion_s) * tomas, 1),
        }
        for br in briefs
    ]
    return {
        "modelo": {k: {"a_s": round(v[0], 2), "b_s_por_s": round(v[1], 4)} for k, v in modelo.items()},
        "procedencia": "mediciones del 2026-09-02 en GTX 1070 (tier3), planificador ON, lm_cfg=2.0",
        "mediciones_usadas": [
            {"duracion_s": d, "total_s": t, "informe": f} for d, t, f in MEDICIONES_TIER3
        ],
        "audio_total_s": audio_total,
        "pistas": len(briefs) * tomas,
        "escenarios": escenarios,
        "por_brief": por_brief,
    }


def texto_estimacion(est: dict[str, Any], tomas: int) -> str:
    lineas = [
        "",
        "=" * 78,
        f"  ESTIMACION DE LA TANDA — {est['pistas']} pistas "
        f"({len(est['por_brief'])} briefs x {tomas} tomas), "
        f"{est['audio_total_s']} s de audio",
        "=" * 78,
        "  Calibrado con 9 mediciones reales en esta misma maquina (tier3, GTX 1070,",
        "  planificador ON). El planificador de 5 Hz es autorregresivo y su coste",
        "  varia entre corridas, de ahi el rango.",
        "",
        "    escenario     computo      carga    TOTAL",
    ]
    for nombre in ("optimista", "central", "pesimista"):
        e = est["escenarios"][nombre]
        lineas.append(
            f"    {nombre:<12} {e['computo_s']:8.0f} s {e['carga_s']:8.0f} s "
            f"{e['total_s']:8.0f} s  ({e['total_min']:.0f} min)"
        )
    lineas += [
        "",
        "    Reparto por brief (central / pesimista, todas sus tomas):",
    ]
    for fila in est["por_brief"]:
        lineas.append(
            f"      {fila['brief']}  {fila['duracion_s']:>3} s x{fila['tomas']}  "
            f"{fila['central_s']:7.0f} s / {fila['pesimista_s']:7.0f} s"
        )
    lineas += [
        "",
        "  La carga del artefacto se paga UNA sola vez: las pistas se generan de una",
        "  en una en el mismo proceso. Bajarse a mitad de tanda y volver a empezar",
        "  cuesta otra carga en frio.",
        "=" * 78,
        "",
    ]
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Nivel de GPU (dato critico del acta)
# --------------------------------------------------------------------------- #

def detectar_gpu(forzar_nivel: str | None = None) -> dict[str, Any]:
    """Nivel de GPU segun `adapters/ace_step/gpu_tiers.py`.

    Por que esto es critico y no decorativo
    ---------------------------------------
    `gpu_tiers.py` define OCHO niveles. La GTX 1070 de desarrollo es **tier3**,
    el tercero por abajo: sin BF16, sin INT8, atencion `eager`, planificador de
    0,6B en vez del de 1,7B que usa el hardware de referencia de la spec
    (RTX 4090/5090, tier6b). **No es el mismo modelo corriendo mas despacio: es
    una configuracion distinta.**

    Consecuencia para el acta de G1: un `NO-GO` medido en tier3 no dice que
    ACE-Step 1.5 no sirva; dice que no sirve **en tier3**. Si el nivel no queda
    escrito encima del veredicto, esa distincion se pierde y una decision sobre
    589 h se toma sobre una medicion mal atribuida.

    Se llama antes de cargar nada, y sin torch devuelve el motivo en vez de
    fallar: el ensayo en seco tiene que poder correr en el portatil.
    """
    datos: dict[str, Any] = {
        "detectado": False,
        "nivel": None,
        "motivo": None,
        "forzado": bool(forzar_nivel or os.environ.get("ACE_STEP_TIER")),
    }
    try:
        import torch  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        datos["motivo"] = f"torch no importable ({exc!r}): fuera del contenedor esto es normal."
        return datos
    try:
        import gpu_tiers  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        datos["motivo"] = f"gpu_tiers no importable ({exc!r}): revisa --raiz-app."
        return datos

    if not torch.cuda.is_available():
        datos["motivo"] = (
            "CUDA no disponible en este entorno. En el contenedor con --gpus all "
            "deberia detectarse tier3 (GTX 1070, 8191 MiB)."
        )
        return datos

    indice = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(indice)
    vram_mb = int(props.total_memory // (1024 * 1024))
    capacidad = torch.cuda.get_device_capability(indice)
    config = gpu_tiers.resolver_configuracion(
        vram_mb, capacidad, forzar_nivel=forzar_nivel or None
    )
    datos.update(
        {
            "detectado": True,
            "nivel": config.nivel,
            "nivel_sin_forzar": gpu_tiers.detectar_nivel(vram_mb),
            "gpu": props.name,
            "vram_mb": vram_mb,
            "capacidad": f"sm_{capacidad[0]}{capacidad[1]}",
            "niveles_totales": len(gpu_tiers.TIER_THRESHOLDS_GB) + 1,
            "resumen": config.resumen(),
            "configuracion": {
                "dtype": config.dtype,
                "atencion": config.atencion,
                "planificador": config.planificador,
                "lm_recomendado": config.lm_recomendado,
                "duracion_max_s": config.duracion_max_s,
                "lote_max": config.lote_max,
                "offload_dit": config.offload_dit,
                "offload_todo": config.offload_todo,
                "cuantizar": config.cuantizar,
            },
            "avisos": list(config.avisos),
        }
    )
    return datos


# --------------------------------------------------------------------------- #
# Carga de generate_smoke por ruta explicita
# --------------------------------------------------------------------------- #

def cargar_generate_smoke() -> Any:
    """Importa el `generate_smoke.py` **hermano** por ruta, sin tocar `sys.path`.

    No se hace `import generate_smoke` a secas por dos motivos:

    * La imagen NO lleva `spikes/generate_smoke.py` (el Dockerfile solo copia
      `_timing.py` y `_mock.py`), asi que el modulo tiene que salir del bind
      mount `/work`.
    * Meter `/work/spikes` en `sys.path` adelantaria TODO el arbol del bind mount
      por delante de `/app`, y la politica de estos spikes es la contraria: el
      codigo que se ejercita es el que viaja en la imagen. Cargarlo por ruta
      resuelve solo este modulo y deja la politica intacta.
    """
    ruta = _AQUI.parent / "generate_smoke.py"
    if not ruta.is_file():
        raise SystemExit(
            f"No se encontro {ruta}. g1_generar.py reutiliza su verificacion de "
            "WAV, su muestreador de VRAM y su escucha de etapas; tienen que estar "
            "juntos en el mismo directorio."
        )
    nombre = "g1_generate_smoke"
    if nombre in sys.modules:
        return sys.modules[nombre]
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    if spec is None or spec.loader is None:
        raise SystemExit(f"No se pudo preparar la carga de {ruta}.")
    modulo = importlib.util.module_from_spec(spec)
    # Registrar ANTES de ejecutar, y no despues. `@dataclass` resuelve sus
    # anotaciones con `sys.modules[cls.__module__].__dict__`; si el modulo aun no
    # esta ahi, eso es `None.__dict__` y el import revienta con un
    # `AttributeError` que no dice nada de la causa real. Pasa con `CasoAB` y con
    # `MuestraVram`, que son dataclasses de nivel superior de generate_smoke.
    sys.modules[nombre] = modulo
    try:
        spec.loader.exec_module(modulo)
    except BaseException:
        del sys.modules[nombre]
        raise
    return modulo


def _verificar_limitador() -> dict[str, Any]:
    """Comprueba que el shim que se va a usar lleva el limitador de picos.

    Es incondicional en el codigo, pero se verifica en vez de suponerse: si
    alguien despachara una imagen antigua, las pistas saldrian con recorte duro y
    la dimension 2 de la rubrica penalizaria a ACE-Step por un fallo nuestro.
    Mas vale abortar aqui que descubrirlo escuchando.
    """
    import ace_step_shim  # noqa: PLC0415

    techo = getattr(ace_step_shim, "TECHO_LIMITADOR_DB", None)
    tiene = callable(getattr(ace_step_shim, "_limitar_picos", None))
    if not tiene or techo is None:
        raise SystemExit(
            "El shim cargado no tiene limitador de picos (`_limitar_picos`). "
            "Reconstruye la imagen: sin el, las pistas salen con recorte duro y "
            "eso se oye en la dimension 2 de la rubrica de G1."
        )
    return {"presente": True, "techo_dbfs": float(techo), "fichero": ace_step_shim.__file__}


# --------------------------------------------------------------------------- #
# Escritura de los artefactos de §10.2
# --------------------------------------------------------------------------- #

def escribir_briefs(raiz: Path, briefs: list[Brief], prompts: dict[str, str],
                    letras: dict[str, Letra], metas: dict[str, dict]) -> None:
    """Archiva `01-briefs/` tal y como lo describe §10.2.

    Se escribe ANTES de generar, no despues: §4.2 exige que el prompt este
    escrito antes, y §4.1 que la letra quede archivada literal como referencia
    del WER. Un archivo generado a posteriori no demuestra nada.
    """
    destino = raiz / "01-briefs"
    destino.mkdir(parents=True, exist_ok=True)
    for brief in briefs:
        letra = letras[brief.id]
        (destino / f"{brief.id}.prompt.txt").write_text(prompts[brief.id] + "\n", encoding="utf-8", newline="\n")
        (destino / f"{brief.id}.letra.txt").write_text(letra.texto, encoding="utf-8", newline="\n")
        (destino / f"{brief.id}.letra-referencia-wer.txt").write_text(
            letra.referencia_wer, encoding="utf-8", newline="\n"
        )
        ficha = asdict(brief)
        ficha["prompt_estilo"] = prompts[brief.id]
        ficha["metadatos_musicales"] = metas[brief.id]
        ficha["letra_origen"] = str(letra.ruta)
        ficha["letra_sha256"] = hashlib.sha256(letra.texto.encode("utf-8")).hexdigest()
        ficha["avisos_letra"] = letra.avisos
        (destino / f"{brief.id}.brief.json").write_text(
            json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
        )


_CABECERA_MAPA = (
    "brief", "etiqueta_ciega", "indice_toma", "orden_generacion", "semilla",
    "fichero", "duracion_pedida_s", "duracion_real_s", "generada",
)


def sellar_mapa(raiz: Path, filas: list[dict[str, Any]], semilla_maestra: int) -> dict[str, str]:
    """Escribe `05-ciego/mapa-tomas.csv` y lo sella con SHA-256 (§5.6).

    El sello no impide abrir el fichero — nada puede impedirlo. Lo que hace es
    que **una modificacion posterior sea evidente**, que es exactamente el
    mecanismo que §5.6 pide para las hojas de puntuacion y el mismo principio de
    la cadena de hashes del ledger de la plataforma: barato, verificable y
    suficiente.
    """
    destino = raiz / "05-ciego"
    destino.mkdir(parents=True, exist_ok=True)
    csv_ruta = destino / "mapa-tomas.csv"
    with csv_ruta.open("w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(_CABECERA_MAPA))
        escritor.writeheader()
        for fila in sorted(filas, key=lambda f: f["etiqueta_ciega"]):
            escritor.writerow({k: fila.get(k, "") for k in _CABECERA_MAPA})

    digest = hashlib.sha256(csv_ruta.read_bytes()).hexdigest()
    sello = {
        "fichero": csv_ruta.name,
        "sha256": digest,
        "sellado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "semilla_maestra": semilla_maestra,
        "filas": len(filas),
    }
    (destino / "mapa-tomas.sha256").write_text(
        f"{digest}  {csv_ruta.name}\n", encoding="utf-8", newline="\n"
    )
    (destino / "sello.json").write_text(
        json.dumps(sello, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    (destino / "LEEME-NO-ABRIR.txt").write_text(
        "NO ABRIR mapa-tomas.csv todavia.\n"
        "\n"
        "Este fichero dice que semilla y que numero de toma hay detras de cada\n"
        "etiqueta ciega. Se abre DESPUES de haber elegido, brief a brief, cual de\n"
        "las tomas manda (protocolo g1-protocolo.md §5.2), y no antes.\n"
        "\n"
        "Conocer el indice de toma mientras se elige ancla la eleccion: «la\n"
        "primera» y «la ultima» pesan aunque uno no quiera. Por eso el nombre del\n"
        "fichero de audio no lo dice y por eso el orden de generacion esta\n"
        "barajado.\n"
        "\n"
        "El sello SHA-256 esta en mapa-tomas.sha256 y en sello.json. Comprobarlo:\n"
        "    sha256sum -c mapa-tomas.sha256\n"
        "Si no cuadra, el mapa se ha tocado despues de generarlo y hay que decirlo\n"
        "en el acta.\n"
        "\n"
        "Lo que SI se puede abrir sin romper nada:\n"
        "    02-generado/propio/registro-tecnico.json  (tiempos, VRAM, nivel de GPU;\n"
        "    no lleva ni semillas ni indices de toma)\n",
        encoding="utf-8", newline="\n",
    )
    return sello


# --------------------------------------------------------------------------- #
# Ejecucion
# --------------------------------------------------------------------------- #

async def generar(args: argparse.Namespace, briefs: list[Brief], plan: list[Toma],
                  prompts: dict[str, str], letras: dict[str, Letra],
                  metas: dict[str, dict], informe: dict[str, Any]) -> int:
    """Genera la serie propia, de una en una, tras UNA sola carga."""
    gs = cargar_generate_smoke()
    raiz_app = gs.resolver_raiz_app(args.raiz_app)
    gs.preparar_sys_path(raiz_app)

    import adapter as modulo_adapter  # noqa: PLC0415
    from contracts import GenerationRequest  # noqa: PLC0415

    # --- Guardarrail G-01: identico al de generate_smoke, y por lo mismo ----- #
    if not modulo_adapter._env_flag("ACE_STEP_REQUIRE_GPU"):  # noqa: SLF001
        raise SystemExit(
            "G-01 (pre-dev-checklist §A): sin ACE_STEP_REQUIRE_GPU=1 el adapter "
            "puede caer al mock si CUDA no esta visible. Diez WAV simulados "
            "colados en un gate de calidad serian peor que no tener gate."
        )
    if modulo_adapter._env_flag("ACE_STEP_MOCK"):  # noqa: SLF001
        raise SystemExit("ACE_STEP_MOCK activo: esto no serian generaciones reales.")

    informe["limitador"] = _verificar_limitador()

    raiz_eval = Path(args.raiz_evaluacion)
    dir_audio = raiz_eval / "02-generado" / "propio"
    dir_manifiestos = raiz_eval / "08-manifiestos"
    dir_staging = raiz_eval / "02-generado" / ".staging"
    for carpeta in (dir_audio, dir_manifiestos, dir_staging):
        carpeta.mkdir(parents=True, exist_ok=True)

    escribir_briefs(raiz_eval, briefs, prompts, letras, metas)

    escucha = gs.EscuchaEtapas()
    logging.getLogger().addHandler(escucha)

    adaptador = modulo_adapter.AceStepAdapter(
        weights_name=args.fichero_pesos, output_dir=dir_staging, require_gpu=True
    )
    if adaptador.backend != "gpu":
        raise SystemExit(
            f"Backend resuelto '{adaptador.backend}', no 'gpu'. {adaptador.backend_reason}"
        )
    ctx = modulo_adapter.build_context(
        device=args.dispositivo,
        dtype=args.dtype,
        weights_dir=args.pesos,
        max_gpu_seconds=args.max_gpu_seconds,
    )
    informe["contexto"] = {
        "device": ctx.device,
        "dtype": ctx.dtype,
        "weights_dir": ctx.weights_dir,
        "weights_file": args.fichero_pesos,
        "max_gpu_seconds": ctx.max_gpu_seconds,
        "offload_solicitado": ctx.offload,
    }

    # El SHA-256 de los pesos es la casilla «SHA-256 de los pesos» de la cabecera
    # de la hoja (§7.1) y la precondicion 2 de §9.1. Se calcula una vez.
    ruta_pesos = Path(ctx.weights_dir) / args.fichero_pesos
    if args.hash_pesos and ruta_pesos.is_file():
        print(f"[pesos] SHA-256 de {ruta_pesos} (7,5 GB, ~1 min)...")
        t0 = time.perf_counter()
        informe["pesos_sha256"] = gs.sha256_fichero(ruta_pesos)
        print(f"[pesos] {informe['pesos_sha256']}  ({time.perf_counter() - t0:.1f} s)")
    else:
        informe["pesos_sha256"] = None
        informe.setdefault("avisos", []).append(
            "SHA-256 de los pesos NO calculado (--sin-hash-pesos). La cabecera de "
            "la hoja de §7.1 lo pide y §9.1 lo hace precondicion."
        )

    muestreador = gs.MuestreadorVram(periodo_s=args.periodo_muestreo)
    muestreador.start()
    registro: dict[str, Any] = {}
    filas_mapa: list[dict[str, Any]] = []
    codigo = 0
    por_id = {b.id: b for b in briefs}

    def volcar_parcial() -> None:
        """Persiste lo que haya tras CADA pista.

        Una tanda de tres tomas son ~2,5 h. Si se corta en la pista 27 y solo se
        escribiera al final, se perderian 27 pistas de GPU por nada.
        """
        (dir_audio / "registro-tecnico.json").write_text(
            json.dumps(
                {
                    "aviso": (
                        "Se puede abrir sin romper el ciego: aqui NO hay semillas "
                        "ni indices de toma. Esos estan en 05-ciego/mapa-tomas.csv."
                    ),
                    "nivel_gpu": informe.get("gpu"),
                    "pistas": dict(sorted(registro.items())),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8", newline="\n",
        )

    try:
        print(f"[carga] {ruta_pesos} en {ctx.device}... (una sola vez para toda la tanda)")
        t_ini = time.perf_counter()
        await adaptador.load(ctx)
        t_fin = time.perf_counter()
        etapas_carga = adaptador.load_stage_timings()
        informe["carga"] = {
            "total_s": round(t_fin - t_ini, 3),
            "gpu_seconds_de_carga": round(adaptador.load_gpu_seconds(), 3),
            "etapas_s": {k: round(v, 3) for k, v in etapas_carga.items()},
        }
        print(f"[carga] lista en {t_fin - t_ini:.1f} s {informe['carga']['etapas_s']}")

        # El nivel de GPU se vuelve a resolver con CUDA ya inicializado: antes de
        # cargar puede no haber contexto y `get_device_properties` mentiria.
        informe["gpu"] = detectar_gpu(args.forzar_nivel)
        print(f"[gpu] {informe['gpu'].get('resumen') or informe['gpu'].get('motivo')}")

        t_tanda = time.perf_counter()
        for orden, toma in enumerate(plan, start=1):
            brief = por_id[toma.brief_id]
            meta = metas[brief.id]
            params = {
                "vocal_language": brief.idioma,
                # Los tres metadatos salen de `metas`, no del brief crudo: es la
                # unica estructura que ya lleva aplicadas las sobreescrituras de
                # --extra, y es la que se archiva en 01-briefs/. Leer el bpm de
                # un sitio y la tonalidad de otro es como se desincronizan.
                "bpm": meta["bpm"],
                "keyscale": meta["keyscale"],
                "timesignature": meta["timesignature"],
                # Innegociable: efecto medido del 60,7 % frente al 1-7 % del ruido
                # de semilla. Este script no expone forma de apagarlo.
                "usar_lm": True,
                "lm_cfg": args.lm_cfg,
                "lm_temperatura": args.lm_temperatura,
            }
            peticion = GenerationRequest(
                style_prompt=prompts[brief.id],
                duration_s=toma.duracion_s,
                max_gpu_seconds=args.max_gpu_seconds,
                idempotency_key=f"g1-{toma.etiqueta_ciega}",
                lyrics=letras[brief.id].texto,
                instrumental=False,
                seed=toma.semilla,
                model_params=params,
            )
            restantes = len(plan) - orden
            print(
                f"\n[{orden}/{len(plan)}] {toma.etiqueta_ciega} — {brief.id}, "
                f"{toma.duracion_s} s, {brief.idioma}, {brief.bpm} BPM, "
                f"{meta['keyscale']} (quedan {restantes})"
            )
            t_gen_ini = time.perf_counter()
            resultado = await adaptador.generate(peticion)
            t_gen_fin = time.perf_counter()

            hitos = escucha.en_ventana(t_gen_ini, t_gen_fin)
            ventanas, cola = gs.ventanas_de_etapa(hitos, t_gen_ini, t_gen_fin)
            for datos in ventanas.values():
                datos["vram"] = muestreador.pico(datos.pop("_t0"), datos.pop("_t1"))

            artefacto = resultado.artifacts[0]
            if not artefacto.path:
                raise RuntimeError("El adapter devolvio el audio en memoria; se exige fichero.")
            # Renombrado al nombre ciego: el que pone el adapter lleva marca de
            # tiempo, y una marca de tiempo reconstruye el orden de generacion.
            destino_audio = dir_audio / f"{toma.etiqueta_ciega}.wav"
            os.replace(artefacto.path, destino_audio)

            verificacion = gs.verificar_wav(destino_audio, float(toma.duracion_s))
            bloqueantes = verificacion.get("comprobaciones", {})
            todo_ok = bool(bloqueantes) and all(bloqueantes.values())
            if not todo_ok:
                codigo = 1

            pico_vram = max(
                [d["vram"]["usado_pico_mb"] for d in ventanas.values()
                 if d.get("vram", {}).get("usado_pico_mb") is not None] or [0]
            )
            registro[toma.etiqueta_ciega] = {
                "brief": brief.id,
                "duracion_pedida_s": toma.duracion_s,
                "duracion_real_s": verificacion.get("cabecera", {}).get("duracion_real_s"),
                "desviacion_pct": verificacion.get("cabecera", {}).get("desviacion_pct"),
                "fichero": destino_audio.name,
                "total_s": round(t_gen_fin - t_gen_ini, 3),
                "etapas": ventanas,
                "segundos_no_atribuidos": cola,
                "vram_pico_muestreado_mb": pico_vram,
                "vram_pico_torch_mb": resultado.telemetry.vram_peak_mb,
                "gpu_seconds": resultado.telemetry.gpu_seconds,
                "nivel_gpu": informe["gpu"].get("nivel"),
                "model_params_sin_semilla": params,
                "verificacion": verificacion,
                "veredicto": "OK" if todo_ok else "FALLO",
            }
            filas_mapa.append(
                {
                    "brief": brief.id,
                    "etiqueta_ciega": toma.etiqueta_ciega,
                    "indice_toma": toma.indice,
                    "orden_generacion": orden,
                    "semilla": toma.semilla,
                    "fichero": destino_audio.name,
                    "duracion_pedida_s": toma.duracion_s,
                    "duracion_real_s": verificacion.get("cabecera", {}).get("duracion_real_s"),
                    "generada": "si",
                }
            )
            # Manifiesto retroactivo simplificado de §10.2. Retroactivo porque el
            # manifiesto v1 real llega con C-10a (T-26, F5) y estas pistas nacen
            # antes de que exista el ledger; una cadena WORM no admite backfill
            # (D-20), asi que la trazabilidad de G1 es documental y no pretende
            # otra cosa. Va en 08-manifiestos/ y contiene la semilla: es el
            # SEGUNDO fichero que rompe el ciego, y por eso se avisa aqui.
            (dir_manifiestos / f"{toma.etiqueta_ciega}.manifiesto.json").write_text(
                json.dumps(
                    {
                        "aviso_ciego": (
                            "contiene la semilla: no abrir antes de elegir la toma (§5.2)"
                        ),
                        "modelo": "ACE-Step 1.5 (turbo, artefacto con planificador de 5 Hz)",
                        "pesos_fichero": args.fichero_pesos,
                        "pesos_sha256": informe.get("pesos_sha256"),
                        "semilla": toma.semilla,
                        "prompt_estilo": prompts[brief.id],
                        "letra": letras[brief.id].texto,
                        "brief": brief.id,
                        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "hardware": informe["gpu"].get("resumen") or informe["gpu"].get("motivo"),
                        "nivel_gpu": informe["gpu"].get("nivel"),
                        "parametros_inferencia": params,
                        "max_gpu_seconds": args.max_gpu_seconds,
                        "duracion_pedida_s": toma.duracion_s,
                        "fichero_audio": destino_audio.name,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8", newline="\n",
            )
            volcar_parcial()

            transcurrido = time.perf_counter() - t_tanda
            print(
                f"    {t_gen_fin - t_gen_ini:.1f} s · pico VRAM {pico_vram} MiB · "
                f"{verificacion.get('cabecera', {}).get('duracion_real_s')} s reales "
                f"({verificacion.get('cabecera', {}).get('desviacion_pct')} %) · "
                f"{'OK' if todo_ok else 'FALLO'}"
            )
            print(f"    tanda: {transcurrido / 60:.1f} min consumidos, {restantes} pistas por delante")
            if not todo_ok:
                for nombre, valor in bloqueantes.items():
                    if not valor:
                        print(f"    [MAL] {nombre}")
                if not args.seguir_tras_fallo:
                    print(
                        "[abortado] comprobaciones bloqueantes fallidas. La carga ya "
                        "esta pagada; usa --seguir-tras-fallo si prefieres terminar la "
                        "tanda y revisar despues."
                    )
                    break

    except BaseException as exc:  # noqa: BLE001
        informe["fallo"] = {
            "tipo": type(exc).__name__,
            "mensaje": str(exc),
            "traceback": traceback.format_exc(),
        }
        codigo = 2
        traceback.print_exc()
    finally:
        muestreador.detener()
        informe["muestreo_vram"] = {
            "periodo_ms": round(args.periodo_muestreo * 1000, 1),
            "vram_total_mb": muestreador.total_mb,
            "error": muestreador.error,
        }
        try:
            await adaptador.unload()
        except Exception as exc:  # noqa: BLE001
            informe.setdefault("avisos", []).append(f"unload() fallo: {exc!r}")
        logging.getLogger().removeHandler(escucha)
        informe["adapter"] = adaptador.describe()
        informe["procedencia_codigo"] = gs.procedencia_modulos(raiz_app)
        volcar_parcial()

        # Las tomas que no llegaron a generarse constan en el mapa como tales: un
        # mapa que solo lista lo que salio bien no permite auditar la tanda.
        generadas = {f["etiqueta_ciega"] for f in filas_mapa}
        for toma in plan:
            if toma.etiqueta_ciega not in generadas:
                filas_mapa.append(
                    {
                        "brief": toma.brief_id,
                        "etiqueta_ciega": toma.etiqueta_ciega,
                        "indice_toma": toma.indice,
                        "orden_generacion": "",
                        "semilla": toma.semilla,
                        "fichero": "",
                        "duracion_pedida_s": toma.duracion_s,
                        "duracion_real_s": "",
                        "generada": "no",
                    }
                )
        informe["sello_mapa"] = sellar_mapa(raiz_eval, filas_mapa, args.semilla_maestra)
        informe["pistas_generadas"] = len(generadas)
        informe["pistas_planificadas"] = len(plan)
        informe["codigo_salida"] = codigo
        destino = raiz_eval / "g1-generacion-informe.json"
        destino.write_text(
            json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
        )
        print(f"\n[informe] {destino}")
        print(f"[mapa]    {raiz_eval / '05-ciego' / 'mapa-tomas.csv'}")
        print(f"[sello]   SHA-256 {informe['sello_mapa']['sha256']}")
        print(f"[pistas]  {len(generadas)} de {len(plan)} generadas")
        print(f"[nivel]   GPU: {informe.get('gpu', {}).get('nivel')}  <-- va en el acta de G1")
    return codigo


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera la serie propia de las 10 pistas del gate G1 leyendo los briefs "
            "del protocolo. NO ejecuta el gate: no puntua ni decide."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true", dest="dry_run",
        help=(
            "Ensayo en seco: lee los briefs, deriva prompts y metadatos, valida las "
            "letras, estima el tiempo y detecta el nivel de GPU. NO carga el modelo, "
            "NO toca la GPU y NO escribe nada salvo --plan-json."
        ),
    )
    parser.add_argument(
        "--protocolo", default=None,
        help="Ruta de g1-protocolo.md. Por defecto se busca desde la raiz del repo.",
    )
    parser.add_argument(
        "--letras", default=None,
        help=(
            "Directorio con las 10 letras del propietario (B-01.txt ... B-10.txt). "
            "Obligatorio: §4.1 y §9.1 las ponen de su lado y este script no las inventa."
        ),
    )
    parser.add_argument(
        "--extra", default=None,
        help=(
            'JSON de sobreescrituras por brief, p. ej. '
            '{"B-01": {"keyscale": "E major", "prompt": "..."}}. Lo que venga de '
            "aqui queda marcado como tal en el informe."
        ),
    )
    parser.add_argument(
        "--raiz-evaluacion", default="/outputs/g1-2026", dest="raiz_evaluacion",
        help=(
            "Carpeta de evaluacion de §10.2. Fuera del repo y fuera de la biblioteca "
            "de trabajo (S-11): en el repo no va audio."
        ),
    )
    parser.add_argument(
        "--tomas", type=int, default=TOMAS_PROTOCOLO,
        help=(
            "Tomas por brief. §5.2 fija 3 (semillas distintas, todas registradas) y "
            "el propietario elige una comparando solo dentro de la serie. Con otro "
            "valor el informe queda marcado como no conforme a §5.2."
        ),
    )
    parser.add_argument(
        "--semilla-maestra", type=int, default=20260902, dest="semilla_maestra",
        help=(
            "De ella salen, de forma reproducible, las semillas de cada toma, los "
            "testigos ciegos y el barajado del orden. La misma semilla maestra "
            "reproduce la serie entera (util para las repeticiones de §8.5)."
        ),
    )
    parser.add_argument(
        "--solo", default=None,
        help="Genera solo estos briefs, separados por comas: B-03,B-07.",
    )
    parser.add_argument(
        "--desde", default=None,
        help="Reanuda desde este brief inclusive (B-05). Util tras un corte.",
    )
    parser.add_argument(
        "--escribir-plantillas", default=None, dest="escribir_plantillas",
        help=(
            "Escribe en este directorio B-01.txt ... B-10.txt con las etiquetas "
            "canonicas puestas y VACIAS, mas una ficha B-NN.BRIEF.txt con el brief "
            "delante. No escribe ni un verso: las letras son del propietario (§4.1). "
            "No pisa ficheros existentes. Termina sin generar nada."
        ),
    )
    parser.add_argument(
        "--permitir-sin-tildes", action="store_true", dest="permitir_sin_tildes",
        help=(
            "Acepta letras en castellano sin ninguna tilde ni enye. Casi siempre es "
            "una letra a la que se le han caido al copiar; por eso hay que pedirlo."
        ),
    )
    parser.add_argument(
        "--si", action="store_true", dest="confirmado",
        help="Salta la confirmacion interactiva tras leer la estimacion de tiempo.",
    )
    parser.add_argument(
        "--seguir-tras-fallo", action="store_true", dest="seguir_tras_fallo",
        help="No aborta la tanda si una pista falla sus comprobaciones. Salida sigue en 1.",
    )
    parser.add_argument(
        "--plan-json", default=None, dest="plan_json",
        help="Vuelca el plan y la estimacion a este JSON (funciona tambien en --dry-run).",
    )
    parser.add_argument(
        "--forzar-nivel", default=None, dest="forzar_nivel",
        help=(
            "Fuerza el nivel de gpu_tiers (tier1..unlimited). Si se usa, el informe "
            "lo grita: el acta de G1 no puede decir que se genero en un nivel que no era."
        ),
    )
    parser.add_argument("--lm-cfg", type=float, default=2.0, dest="lm_cfg",
                        help="CFG del planificador de 5 Hz (2,0 es el de upstream).")
    parser.add_argument("--lm-temperatura", type=float, default=0.85, dest="lm_temperatura",
                        help="Temperatura del planificador (0,85 es el de upstream).")
    parser.add_argument("--pesos", default=None, help="Directorio de pesos (por defecto, entorno).")
    parser.add_argument(
        "--fichero-pesos",
        default=os.environ.get("ACE_STEP_WEIGHTS_FILE", "ace_step_1_5_lm.safetensors"),
        help="Artefacto CON planificador. El de 6,16 GB no lo lleva.",
    )
    parser.add_argument("--dispositivo", default=None, help="Por defecto, ACE_STEP_DEVICE.")
    parser.add_argument("--dtype", default=None, help="Por defecto, ACE_STEP_DTYPE.")
    parser.add_argument(
        "--max-gpu-seconds", type=int, default=1800,
        help=(
            "Techo de D-17 por peticion, CARGA INCLUIDA (el adapter suma "
            "load_gpu_seconds a cada generacion). El brief mas largo son 180 s de "
            "audio, ~500 s de computo, mas ~110 s de carga."
        ),
    )
    parser.add_argument("--periodo-muestreo", type=float, default=0.04,
                        dest="periodo_muestreo", help="Periodo del muestreador de VRAM, en s.")
    parser.add_argument("--raiz-app", default=None, dest="raiz_app",
                        help="Raiz del runner (por defecto /app dentro del contenedor).")
    parser.add_argument(
        "--sin-hash-pesos", action="store_false", dest="hash_pesos",
        help=(
            "No calcula el SHA-256 de los pesos (~1 min sobre 7,5 GB). La cabecera "
            "de la hoja de §7.1 lo pide, asi que por defecto SI se calcula."
        ),
    )
    return parser


def resolver_protocolo(indicada: str | None) -> Path:
    """Localiza `g1-protocolo.md`, dentro y fuera del contenedor.

    Fuera, el fichero cuelga de la raiz del repo, cuatro niveles por encima de
    este script. Dentro, el repo no esta montado entero: solo la carpeta
    `gates/`, en `/protocolo`. Ojo con subir cuatro niveles a ciegas: en el
    contenedor este fichero es `/work/spikes/g1_generar.py` y solo tiene tres
    ancestros, asi que `parents[3]` es un IndexError, no una ruta que no existe.
    """
    if indicada:
        ruta = Path(indicada).resolve()
        if not ruta.is_file():
            raise SystemExit(f"--protocolo: {ruta} no existe.")
        return ruta
    bases: list[Path] = []
    if len(_AQUI.parents) > 3:
        bases.append(_AQUI.parents[3])   # raiz del repo, fuera del contenedor
    bases += [Path.cwd(), Path("/protocolo")]
    for base in bases:
        for candidata in (base / PROTOCOLO_REL, base / "g1-protocolo.md"):
            if candidata.is_file():
                return candidata.resolve()
    raise SystemExit(
        "No se encontro g1-protocolo.md. Se busco en "
        f"{[str(b) for b in bases]}. Indicalo con --protocolo; dentro del "
        "contenedor hay que montar la carpeta gates/ en /protocolo "
        "(ver spikes/README.md)."
    )


def _forzar_utf8_en_consola() -> None:
    """La consola de Windows es cp1252 y se come «§», tildes y flechas.

    El ensayo en seco esta pensado para correrse en el portatil, fuera del
    contenedor, asi que tiene que poder imprimir el texto del protocolo sin
    romperse. Dentro del contenedor esto no hace nada: ya es UTF-8.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError, OSError):
            pass


def escribir_plantillas(destino: Path, briefs: list[Brief], prompts: dict[str, str],
                        metas: dict[str, dict]) -> None:
    """Esqueletos de letra con las etiquetas canonicas ya puestas. Sin una palabra dentro.

    Las letras las escribe el propietario (§4.1). Lo unico que se le da hecho es
    la estructura de etiquetas —que es justo donde se metio la pata el
    2026-09-02— y una ficha con el brief delante para no tener que ir al
    protocolo a mirarlo. Ni un verso: eso seria escribirle la letra y falsearia
    la dimension 4 y el WER.
    """
    destino.mkdir(parents=True, exist_ok=True)
    for brief in briefs:
        if brief.duracion_s >= 90:
            # §4.1: dos estrofas y un estribillo como minimo.
            secciones = ["verse", "chorus", "verse", "chorus"]
        else:
            secciones = ["verse", "chorus"]
        cuerpo = "\n\n".join(f"[{s}]\n" for s in secciones)
        ruta = destino / f"{brief.id}.txt"
        if ruta.exists():
            print(f"  (ya existe, no se toca) {ruta}")
        else:
            ruta.write_text(cuerpo, encoding="utf-8", newline="\n")
            print(f"  {ruta}")
        (destino / f"{brief.id}.BRIEF.txt").write_text(
            f"{brief.id} — {brief.uso_final}\n"
            f"  genero/caracter : {brief.genero}\n"
            f"  tempo           : {brief.bpm} BPM\n"
            f"  instrumentacion : {brief.instrumentacion}\n"
            f"  voz / idioma    : {brief.voz}  ({brief.idioma})\n"
            f"  duracion        : {brief.duracion_s} s\n"
            f"  destino loudness: {brief.destino}\n"
            f"  exige (D1)      : {brief.exigencia}\n"
            f"  prompt de estilo: {prompts[brief.id]}\n"
            f"  metadatos       : bpm={metas[brief.id]['bpm']} "
            f"keyscale={metas[brief.id]['keyscale']} "
            f"compas={metas[brief.id]['timesignature']}\n"
            "\n"
            f"Escribe la letra en {brief.id}.txt. Reglas que el script comprueba:\n"
            "  - solo etiquetas [intro] [verse] [chorus] [bridge] [outro], en minusculas\n"
            "  - con tildes y enyes si el canto es en castellano\n"
            "  - >= 1:30 -> dos [verse] y un [chorus]; mas corto -> dos frases minimo\n"
            "Este fichero .BRIEF.txt es para leerlo tu; el script no lo envia al modelo.\n",
            encoding="utf-8", newline="\n",
        )


def main(argv: list[str] | None = None) -> int:
    _forzar_utf8_en_consola()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        stream=sys.stdout,
    )
    args = construir_parser().parse_args(argv)

    if args.tomas < 1:
        raise SystemExit("--tomas tiene que ser >= 1.")

    ruta_protocolo = resolver_protocolo(args.protocolo)
    briefs = leer_briefs(ruta_protocolo)
    sha_protocolo = hashlib.sha256(ruta_protocolo.read_bytes()).hexdigest()
    print(f"[protocolo] {ruta_protocolo}")
    print(f"[protocolo] SHA-256 {sha_protocolo}")
    print(f"[protocolo] 10 briefs leidos de §4: {', '.join(b.id for b in briefs)}")

    # --- Filtros de reanudacion ------------------------------------------- #
    if args.solo:
        pedidos = {p.strip().upper() for p in args.solo.split(",") if p.strip()}
        conocidos = {b.id for b in briefs}
        if not pedidos <= conocidos:
            raise SystemExit(f"--solo: briefs desconocidos {sorted(pedidos - conocidos)}.")
        briefs = [b for b in briefs if b.id in pedidos]
    if args.desde:
        desde = args.desde.strip().upper()
        ids = [b.id for b in briefs]
        if desde not in ids:
            raise SystemExit(f"--desde: {desde} no esta entre {ids}.")
        briefs = briefs[ids.index(desde):]
    parcial = len(briefs) != 10

    # --- Derivaciones y sobreescrituras ------------------------------------ #
    extra: dict[str, dict] = {}
    if args.extra:
        extra = json.loads(Path(args.extra).read_text(encoding="utf-8"))
    prompts: dict[str, str] = {}
    metas: dict[str, dict] = {}
    briefs_efectivos: list[Brief] = []
    for brief in briefs:
        sobre = extra.get(brief.id, {})
        # Un `bpm` sobreescrito tiene que entrar en el brief ANTES de derivar el
        # prompt. Si no, el prompt sigue diciendo el tempo de §4 y el bloque de
        # metas dice otro: exactamente la contradiccion que el modelo tiene que
        # resolver adivinando, y que el 2026-09-02 se arreglo poblando las metas.
        if "bpm" in sobre:
            brief = replace(brief, bpm=int(sobre["bpm"]))
        briefs_efectivos.append(brief)
        prompts[brief.id] = sobre.get("prompt") or derivar_prompt_estilo(brief)
        keyscale, motivo = derivar_tonalidad(brief)
        if sobre.get("keyscale"):
            keyscale, motivo = sobre["keyscale"], "sobreescrito en --extra por el propietario"
        metas[brief.id] = {
            "bpm": brief.bpm,
            "bpm_origen": "--extra" if "bpm" in sobre else "columna «Tempo» de §4",
            "keyscale": keyscale,
            "keyscale_motivo": motivo,
            "timesignature": sobre.get("timesignature", COMPAS_POR_DEFECTO),
            "prompt_origen": "--extra" if sobre.get("prompt") else "derivado de §4 (§4.2)",
        }
    briefs = briefs_efectivos

    if args.escribir_plantillas:
        print(f"\n[plantillas] esqueletos de letra en {args.escribir_plantillas}")
        escribir_plantillas(Path(args.escribir_plantillas), briefs, prompts, metas)
        print(
            "[plantillas] escritas. Escribe las letras y vuelve con "
            "--dry-run --letras <ese directorio>."
        )
        return 0

    # --- Letras: del propietario, aqui solo se validan --------------------- #
    if not args.letras:
        raise SystemExit(
            "Falta --letras. Las 10 letras las escribe el propietario (§4.1, "
            "precondicion 7 de §9.1) y este script no las inventa: una letra "
            "inventada haria que la dimension 4 y el WER midieran otra cosa."
        )
    dir_letras = Path(args.letras)
    if not dir_letras.is_dir():
        raise SystemExit(f"--letras: {dir_letras} no es un directorio.")
    letras = {b.id: cargar_letra(dir_letras, b, args.permitir_sin_tildes) for b in briefs}

    print("\n[letras]")
    for brief in briefs:
        letra = letras[brief.id]
        estado = "OK " if letra.valida else "MAL"
        palabras = len(letra.referencia_wer.split())
        print(
            f"  [{estado}] {brief.id}  {brief.duracion_s:>3} s  {brief.idioma}  "
            f"{palabras:>4} palabras  etiquetas={letra.etiquetas}"
        )
        for error in letra.errores:
            print(f"         ERROR: {error}")
        for aviso in letra.avisos:
            print(f"         aviso: {aviso}")

    invalidas = [b.id for b in briefs if not letras[b.id].valida]

    print("\n[prompts de estilo derivados de §4.2 — literales, tambien para Suno, libreria y CLAP]")
    for brief in briefs:
        m = metas[brief.id]
        print(f"  {brief.id}  bpm={m['bpm']}  keyscale={m['keyscale']}  compas={m['timesignature']}")
        print(f"        {prompts[brief.id]}")
        print(f"        (tonalidad: {m['keyscale_motivo']})")

    # --- Nivel de GPU ------------------------------------------------------- #
    # En --dry-run puede fallar (no hay torch fuera del contenedor) y eso no es
    # un error: se dice y se sigue.
    try:
        gs = cargar_generate_smoke()
        gs.preparar_sys_path(gs.resolver_raiz_app(args.raiz_app))
    except SystemExit as exc:
        print(f"\n[gpu] no se pudo preparar sys.path: {exc}")
    gpu = detectar_gpu(args.forzar_nivel)
    print("\n[gpu]")
    if gpu["detectado"]:
        print(f"  nivel detectado: {gpu['nivel']} de {gpu['niveles_totales']} niveles")
        print(f"  {gpu['resumen']}")
        for aviso in gpu.get("avisos", []):
            print(f"  aviso: {aviso}")
        if gpu["nivel"] == "tier3":
            print(
                "  ATENCION para el acta: tier3 es el tercer nivel por abajo de ocho.\n"
                "  Sin BF16, sin INT8, atencion eager y planificador de 0,6B. El\n"
                "  hardware de referencia de la spec (RTX 4090/5090) es tier6b y corre\n"
                "  otra configuracion. Un NO-GO medido aqui dice «no sirve en tier3»,\n"
                "  no «no sirve». Escribe el nivel encima del veredicto."
            )
    else:
        print(f"  no detectado: {gpu['motivo']}")

    # --- Estimacion --------------------------------------------------------- #
    est = estimar(briefs, args.tomas)
    print(texto_estimacion(est, args.tomas))

    plan = construir_plan(briefs, args.tomas, args.semilla_maestra)

    informe: dict[str, Any] = {
        "spike": "g1_generar",
        "tarea": "T-09 (preparacion; el gate lo ejecuta el propietario)",
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocolo": {"ruta": str(ruta_protocolo), "sha256": sha_protocolo},
        "briefs": [asdict(b) for b in briefs],
        "prompts_estilo": prompts,
        "metadatos_musicales": metas,
        "letras": {
            b.id: {
                "ruta": str(letras[b.id].ruta),
                "sha256": hashlib.sha256(letras[b.id].texto.encode("utf-8")).hexdigest(),
                "palabras_referencia_wer": len(letras[b.id].referencia_wer.split()),
                "etiquetas": letras[b.id].etiquetas,
                "avisos": letras[b.id].avisos,
            }
            for b in briefs
        },
        "tomas_por_brief": args.tomas,
        "semilla_maestra": args.semilla_maestra,
        "estimacion": est,
        "gpu": gpu,
        "planificador_5hz": {"usar_lm": True, "lm_cfg": args.lm_cfg,
                             "lm_temperatura": args.lm_temperatura},
        "conformidad": {
            "briefs_completos": not parcial,
            "tomas_conforme_5_2": args.tomas == TOMAS_PROTOCOLO,
            "nivel_forzado": bool(args.forzar_nivel or os.environ.get("ACE_STEP_TIER")),
        },
    }
    avisos: list[str] = []
    if parcial:
        avisos.append(
            f"SERIE PARCIAL: {len(briefs)} de 10 briefs (--solo/--desde). El gate se "
            "calcula sobre 10; esta tanda no cierra la serie por si sola."
        )
    if args.tomas != TOMAS_PROTOCOLO:
        avisos.append(
            f"sesion_no_conforme_5_2: {args.tomas} tomas por brief en vez de las "
            f"{TOMAS_PROTOCOLO} que fija §5.2. Con una sola toma no hay eleccion que "
            "hacer y el material no cumple el protocolo tal como esta escrito."
        )
    if args.forzar_nivel or os.environ.get("ACE_STEP_TIER"):
        avisos.append(
            "NIVEL DE GPU FORZADO: el informe no representa a esta maquina y no "
            "puede sostener el acta de G1."
        )
    if avisos:
        informe["avisos_conformidad"] = avisos

    if args.plan_json:
        plan_ruta = Path(args.plan_json)
        plan_ruta.parent.mkdir(parents=True, exist_ok=True)
        volcado = dict(informe)
        volcado["plan_orden_generacion"] = [
            {"orden": i, "brief": t.brief_id, "etiqueta_ciega": t.etiqueta_ciega,
             "duracion_s": t.duracion_s}
            for i, t in enumerate(plan, start=1)
        ]
        plan_ruta.write_text(json.dumps(volcado, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print(f"[plan] {plan_ruta}")

    for aviso in avisos:
        print(f"[AVISO] {aviso}")

    if invalidas:
        print(
            "\n[bloqueado] Letras invalidas o ausentes en: " + ", ".join(invalidas) +
            "\nNo se genera nada. Corrige las letras y vuelve a ejecutar el ensayo en seco."
        )
        return 3

    if args.dry_run:
        # Precision deliberada: SI se ha tocado la GPU, para leer su nivel. Lo
        # que no se ha hecho es cargar los 7,5 GB de pesos ni generar audio.
        # Decir «no se ha tocado la GPU» seria mas comodo y seria falso.
        print(
            "\n[dry-run] Ensayo en seco terminado. NO se han cargado los pesos y NO "
            "se ha generado audio. Lo unico que se ha pedido a la GPU es su nombre "
            "y su VRAM, para detectar el nivel."
        )
        print(f"[dry-run] Plan: {len(plan)} pistas, de una en una, tras UNA sola carga.")
        print("[dry-run] Quita --dry-run y anade --si cuando quieras generar de verdad.")
        return 0

    # --- Confirmacion antes de gastar GPU ---------------------------------- #
    if not args.confirmado:
        # `isatty()` no es de fiar en todas partes: bajo MSYS/Git Bash devuelve
        # True con la entrada redirigida a /dev/null, y entonces `input()` revienta
        # con EOFError en vez de preguntar. Se trata igual que «no hay terminal»:
        # lo que no puede pasar es que una tanda de horas arranque sin que nadie
        # haya visto la estimacion, ni que se caiga con un traceback en su lugar.
        respuesta = None
        if sys.stdin is not None and sys.stdin.isatty():
            try:
                respuesta = input("Has leido la estimacion. Generar ahora? [s/N] ").strip().lower()
            except (EOFError, OSError):
                respuesta = None
        if respuesta is None:
            raise SystemExit(
                "Sin terminal interactiva no se arranca una tanda de horas por "
                "accidente. La estimacion esta arriba; si te cuadra, repite el "
                "comando con --si."
            )
        if respuesta not in ("s", "si", "sí"):
            print("Cancelado. No se ha tocado la GPU.")
            return 0

    return asyncio.run(generar(args, briefs, plan, prompts, letras, metas, informe))


if __name__ == "__main__":
    raise SystemExit(main())
