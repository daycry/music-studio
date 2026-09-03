#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ciego ENTRE SERIES para la sesion de escucha de G1 (`g1-protocolo.md` §5.4).

Que ciego es este, y por que hacia falta otro
=============================================
`g1_generar.py` ya ciega las **tomas** dentro de la serie propia: el operador
elige cual de las tres manda (§5.2) sin saber si esta oyendo la primera o la
ultima. Ese es un ciego para una decision previa.

El de §5.4 es distinto y es **el que decide el gate**: el evaluador **debe**
saber a que brief responde cada pista (sin eso D1 no es puntuable) y **no puede
saber de que serie viene** — propia, libreria o Suno. Ese script no existia.
Este es.

Lo que hace, en el orden en que lo hace
=======================================
1. Recoge las series de sus directorios y comprueba la rejilla: **una pista por
   serie y brief**, ni mas ni menos. Un hueco o un duplicado aborta, porque una
   celda vacia identifica la serie ausente sin escuchar nada.
2. **Normaliza al nivel de sesion** con `g1_sonoridad`: -16 LUFS integrados,
   pico real <= -1 dBTP, **solo ganancia** (§5.5). La libreria viene masterizada
   a nivel comercial y sin igualar aplastaria a cualquier salida de modelo por
   sonar mas fuerte, no por sonar mejor.
3. **Recodifica uniforme** (§5.4.2): misma tasa, mismos canales, misma
   profundidad para las 30 pistas. Una cabecera a 44,1 kHz frente a otra a
   48 kHz delata la pista de libreria en el explorador de archivos.
4. **Escribe WAV limpios sin metadatos.** No hace falta `ffmpeg -map_metadata
   -1`: el modulo `wave` de la biblioteca estandar solo sabe escribir `fmt ` y
   `data`, asi que reescribir las muestras basta. Hay un test que abre el
   fichero resultante y comprueba que no se ha colado un `LIST`.
5. **Baraja por brief**, no globalmente. Es la parte que mas importa: con una
   baraja global, `x1` seria siempre la misma serie y reconocer **una** pista
   revelaria las treinta. Barajando por brief, descubrir B03 no dice nada de
   B04.
6. **Sella el mapa** serie<->etiqueta con SHA-256 y su `LEEME`, igual que
   `sellar_mapa()` en `g1_generar.py`. El sello no impide abrir el fichero
   —nada puede impedirlo—: hace que una modificacion posterior sea evidente.

La semilla del barajado **se sortea** (no hay `--semilla` en el CLI: seria una
puerta trasera al ciego) y **solo se escribe dentro del sellado**, junto al mapa
que ya revela todo. Fuera de `05-ciego/` no aparece: hay un test que rastrea
todos los ficheros producidos buscandola.

Que NO hace este script
=======================
No genera pistas, no elige tomas, no puntua, no compara y no abre el mapa. Y no
descarga nada: las series llegan de fuera, ya elegidas.

Riesgos residuales, declarados
==============================
* **Timbre.** §5.4.5 ya lo dice: el propietario puede reconocer su propio
  modelo. Ningun script arregla eso.
* **Duracion y tamano.** Si las pistas propias duran exactamente lo pedido por
  el brief y las de libreria duran tres minutos, la duracion agrupa por serie.
  Es una propiedad del material, no del cegado; se anota aqui para que quien
  prepare la sesion lo tenga en cuenta al elegir las lineas base.
* **`04-sesion/loudness.csv`.** §5.5 pide anotar el valor medido de cada pista.
  El nivel de **origen** es un delator directo (un master a -9 LUFS solo puede
  ser la libreria), asi que en `04-sesion/` va el valor **final** —el que
  demuestra que la sesion esta igualada— y el de origen, la ganancia aplicada y
  la serie viven dentro del sellado. Aun asi, una pista capada por el techo de
  pico acaba por debajo de -16 y eso se ve en el fichero: por eso lleva al lado
  un `LEEME.txt` que pide no abrirlo antes de puntuar.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_AQUI = Path(__file__).resolve().parent
if str(_AQUI) not in sys.path:  # el runner aun no es paquete instalable (T-10)
    sys.path.insert(0, str(_AQUI))

import g1_sonoridad  # noqa: E402

# --------------------------------------------------------------------------- #
# Nombres y formato de la sesion
# --------------------------------------------------------------------------- #

#: Nombres propios, distintos de los de `g1_generar.py` (`mapa-tomas.*`), para
#: que los dos sellos convivan en `05-ciego/` sin pisarse. Son dos ciegos
#: distintos y cada uno se rompe en su momento.
NOMBRE_MAPA = "mapa-series.csv"
NOMBRE_SELLO = "sello-series.json"
NOMBRE_LEEME = "LEEME-NO-ABRIR-series.txt"

DIR_SESION = "04-sesion"
DIR_CIEGO = "05-ciego"

#: Formato uniforme de salida (§5.4.2). 48 kHz / estereo / 16 bit es lo que
#: produce el runner y lo que verifica `generate_smoke.verificar_wav`.
TASA_SESION = 48000
CANALES_SESION = 2
ANCHO_SESION = 2

#: Un nombre de pista solo puede decir el brief y una etiqueta opaca.
PATRON_ETIQUETA = re.compile(r"B\d{2,}-x\d+")

#: De donde se saca el brief del nombre de fichero de entrada: `B03-9f2a1c.wav`,
#: `B03.wav` o `B03_toma2.wav` valen; cualquier otra cosa aborta.
_PATRON_BRIEF = re.compile(r"^(B\d{2,})(?:[-_.].*)?$", re.IGNORECASE)

_CABECERA_MAPA = (
    "brief", "etiqueta_ciega", "serie",
    "fichero_origen", "sha256_origen", "fichero_sesion", "sha256_sesion",
    "tasa_origen", "canales_origen", "bits_origen", "duracion_s",
    "lufs_origen", "dbtp_origen", "ganancia_db",
    "lufs_final", "dbtp_final", "objetivo_alcanzado", "motivo",
)

#: Columnas de `04-sesion/loudness.csv`, que se puede abrir antes de puntuar.
#:
#: NO lleva el pico real por pista, y es deliberado (revision 2026-09-03): con la
#: normalizacion por ganancia pura `lufs` queda clavado en el objetivo para todas,
#: asi que `dbtp` seria exactamente el FACTOR DE CRESTA de cada pista — y la
#: cresta es justo lo que una ganancia constante NO altera. Un master de libreria
#: comprimido y una pista propia sin comprimir tienen crestas muy distintas y
#: agrupan por serie a simple vista. El techo si se publica: es un parametro de la
#: sesion, igual para todas, y no distingue nada. El pico medido de cada pista
#: vive en el sellado, junto al resto de lo que delata.
_CABECERA_LOUDNESS = ("etiqueta", "brief", "lufs", "objetivo_lufs", "techo_dbtp")


# --------------------------------------------------------------------------- #
# Recogida de material
# --------------------------------------------------------------------------- #

def _brief_de(ruta: Path) -> str:
    coincidencia = _PATRON_BRIEF.match(ruta.stem)
    if not coincidencia:
        raise ValueError(
            f"{ruta.name}: no se sabe a que brief pertenece. El nombre tiene que "
            "empezar por el identificador del brief (B01, B02...)."
        )
    return coincidencia.group(1).upper()


def recoger_series(directorios: Mapping[str, Path]) -> dict[str, dict[str, Path]]:
    """Indexa cada serie por brief y comprueba que no hay dos pistas por celda.

    La eleccion de toma (§5.2) ocurre **antes** y la hace el propietario. Aqui
    tiene que llegar ya elegida: si quedan dos candidatas, no es este script
    quien decide.
    """
    if len(directorios) < 2:
        raise ValueError(
            "Hacen falta al menos dos series para que haya algo que cegar "
            f"(llegaron {len(directorios)}). La variante B de §5.6 son dos: "
            "propia y libreria."
        )

    recogidas: dict[str, dict[str, Path]] = {}
    for serie, directorio in sorted(directorios.items()):
        carpeta = Path(directorio)
        if not carpeta.is_dir():
            raise ValueError(f"Serie '{serie}': {carpeta} no es un directorio.")
        por_brief: dict[str, Path] = {}
        for fichero in sorted(carpeta.glob("*.wav")):
            brief = _brief_de(fichero)
            if brief in por_brief:
                raise ValueError(
                    f"Serie '{serie}': {brief} tiene dos pistas "
                    f"({por_brief[brief].name} y {fichero.name}). La eleccion de toma "
                    "(§5.2) va antes que el cegado: dejar una sola."
                )
            por_brief[brief] = fichero
        if not por_brief:
            raise ValueError(f"Serie '{serie}': no hay ningun WAV en {carpeta}.")
        recogidas[serie] = por_brief
    return recogidas


#: Los diez briefs que fija §4 del protocolo. La rejilla se mide contra ESTO y no
#: contra lo que haya en disco: un brief ausente en TODAS las series no deja
#: hueco en la union, y sin este listado pasaba en silencio (revision 2026-09-03).
BRIEFS_DEL_PROTOCOLO = tuple(f"B{i:02d}" for i in range(1, 11))


def comprobar_rejilla(
    recogidas: Mapping[str, dict[str, Path]],
    briefs_esperados: Sequence[str] | None = BRIEFS_DEL_PROTOCOLO,
) -> list[str]:
    """Devuelve los briefs, tras exigir que TODAS las series los tengan todos.

    Un hueco no es un detalle de inventario: si B02 tiene dos pistas en vez de
    tres, el evaluador sabe que falta una serie, y con dos pistas y una ausencia
    el ciego de ese brief ya esta medio roto.

    Y se comprueba contra `briefs_esperados` —los diez de §4— y no contra la
    union de lo encontrado, porque un brief que falte en TODAS las series no deja
    hueco: la rejilla saldria «completa» con nueve. Eso invalida el gate por
    §8.1, porque los umbrales de §2 se calculan sobre las **10** pistas propias
    («7 de las 10», «media sobre las 10»): una sesion de nueve mide otra cosa con
    el mismo nombre.

    `briefs_esperados=None` relaja la comprobacion a la union, que es lo legitimo
    para un ENSAYO del circuito con tres briefs. Se pide explicitamente para que
    nunca ocurra por descuido en la tanda de verdad.
    """
    completo = sorted({b for por_brief in recogidas.values() for b in por_brief})
    faltas: list[str] = []
    if briefs_esperados is not None:
        ausentes = [b for b in briefs_esperados if b not in completo]
        if ausentes:
            raise ValueError(
                f"Faltan briefs en TODAS las series: {', '.join(ausentes)}. El gate se "
                f"calcula sobre los {len(briefs_esperados)} briefs de §4 («7 de las 10», "
                "«media sobre las 10»), asi que una sesion con menos mide otra cosa con el "
                "mismo nombre y §8.1 la invalida. Para un ensayo del circuito, pasa "
                "briefs_esperados=None a proposito."
            )
        sobrantes = [b for b in completo if b not in briefs_esperados]
        if sobrantes:
            raise ValueError(
                f"Briefs que no son de §4: {', '.join(sobrantes)}. Revisa los nombres de "
                "fichero antes de sellar nada."
            )
        completo = list(briefs_esperados)
    for serie, por_brief in sorted(recogidas.items()):
        for brief in completo:
            if brief not in por_brief:
                faltas.append(f"{brief} falta en la serie '{serie}'")
    if faltas:
        raise ValueError(
            "La rejilla serie x brief tiene huecos y un hueco delata la serie "
            "ausente: " + "; ".join(faltas)
        )
    return completo


# --------------------------------------------------------------------------- #
# Barajado por brief
# --------------------------------------------------------------------------- #

def nueva_semilla() -> int:
    """Semilla del barajado. Se sortea: nadie la elige, ni el operador."""
    return secrets.randbits(63)


def reparto_de_brief(semilla: int, brief: str, series: list[str]) -> dict[str, str]:
    """`{serie: etiqueta}` para un brief. Independiente brief a brief.

    La semilla de cada brief sale de `SHA-256(semilla | brief)`, no de un
    contador: asi el reparto de B04 no se puede deducir del de B03 aunque este
    se descubra, que es justo lo que pide «por brief y no globalmente».
    """
    digest = hashlib.sha256(f"{semilla}|{brief}".encode("utf-8")).digest()
    baraja = list(series)
    random.Random(int.from_bytes(digest[:8], "big")).shuffle(baraja)
    return {serie: f"x{indice + 1}" for indice, serie in enumerate(baraja)}


# --------------------------------------------------------------------------- #
# Sellado
# --------------------------------------------------------------------------- #

_TEXTO_LEEME = """NO ABRIR {mapa} todavia.

Este fichero dice de que SERIE viene cada pista de 04-sesion/ — propia,
libreria o Suno. Abrirlo antes de tiempo no invalida una puntuacion: la
contamina, que es peor, porque no se nota.

Se abre en el momento exacto que fija g1-protocolo.md §5.6, y no antes:

  1. Estan rellenadas TODAS las hojas de los 10 briefs, con sus notas.
  2. Las hojas estan exportadas a fichero y su SHA-256 anotado en
     06-hojas/hashes.txt y en la cabecera de la sesion.
  3. Solo ENTONCES se abre este mapa.
  4. Ninguna puntuacion se toca despues. Si al ver el mapa uno cambia de
     opinion sobre una pista, eso no se corrige: se anota como observacion,
     y es en si mismo un dato sobre la fiabilidad de la sesion.

La semilla del barajado esta en {sello} y en ningun otro sitio. Con ella y
con este script el reparto se puede reconstruir entero, o sea que el sello
vale tanto como el mapa: no sacarlo de esta carpeta.

Comprobar que nada se ha tocado:
    sha256sum -c {hashes}
Si no cuadra, el mapa se ha modificado despues de generarlo y hay que
decirlo en el acta.

Ojo: en esta misma carpeta puede haber un mapa-tomas.csv de g1_generar.py.
Es OTRO ciego, el de §5.2 (que toma de la serie propia manda), y se rompe
en otro momento. Este de aqui es el de §5.4.

Lo que SI se puede abrir sin romper nada:
    04-sesion/loudness.csv  (nivel final de cada pista; ver su LEEME.txt)
"""

_TEXTO_LEEME_SESION = """Estas son las pistas de la sesion de escucha (§5.4).

El nombre dice el brief —eso es deliberado, sin el la dimension D1 no es
puntuable— y nada mas. La etiqueta xN es opaca y esta barajada por brief:
descubrir de que serie es una pista de B03 no dice nada de B04.

loudness.csv guarda el nivel FINAL de cada pista, que es lo que demuestra
que la sesion esta igualada (§5.5). Conviene no abrirlo antes de puntuar:
una pista cuyo pico real impidio llegar a {objetivo:g} LUFS queda algo por
debajo, y eso es una pista sobre su origen. El nivel de origen, la ganancia
aplicada y la serie no estan aqui: viven en 05-ciego/, sellados.

Las fechas de modificacion se han igualado a proposito. Ordenar la carpeta
por fecha no dice nada.
"""


def sellar_mapa_series(raiz: Path, filas: list[dict[str, Any]], semilla: int,
                       objetivo_lufs: float, techo_dbtp: float) -> dict[str, Any]:
    """Escribe `05-ciego/mapa-series.csv` y lo sella (§5.4.4 y §5.6).

    Coherente con `sellar_mapa()` de `g1_generar.py`: mismo CSV + `.sha256` +
    `sello.json` + `LEEME`, y por el mismo motivo — el sello no cierra el
    fichero con llave, hace que tocarlo se note.

    Devuelve el sello **sin la semilla**: lo que devuelve esta funcion acaba en
    el informe y el informe se imprime.
    """
    destino = raiz / DIR_CIEGO
    destino.mkdir(parents=True, exist_ok=True)
    csv_ruta = destino / NOMBRE_MAPA

    with csv_ruta.open("w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(_CABECERA_MAPA))
        escritor.writeheader()
        for fila in sorted(filas, key=lambda f: (f["brief"], f["etiqueta_ciega"])):
            escritor.writerow({k: fila.get(k, "") for k in _CABECERA_MAPA})

    digest = hashlib.sha256(csv_ruta.read_bytes()).hexdigest()
    hashes = csv_ruta.with_suffix(".sha256")
    hashes.write_text(f"{digest}  {csv_ruta.name}\n", encoding="utf-8", newline="\n")

    sello_publico = {
        "fichero": csv_ruta.name,
        "sha256": digest,
        "sellado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filas": len(filas),
        "objetivo_lufs": objetivo_lufs,
        "techo_dbtp": techo_dbtp,
    }
    (destino / NOMBRE_SELLO).write_text(
        json.dumps({**sello_publico, "semilla": semilla}, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
    )
    (destino / NOMBRE_LEEME).write_text(
        _TEXTO_LEEME.format(mapa=csv_ruta.name, sello=NOMBRE_SELLO, hashes=hashes.name),
        encoding="utf-8", newline="\n",
    )
    return sello_publico


# --------------------------------------------------------------------------- #
# Anonimizacion
# --------------------------------------------------------------------------- #

def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def anonimizar(directorios: Mapping[str, Path], raiz: Path, *,
               semilla: int | None = None,
               objetivo_lufs: float = g1_sonoridad.OBJETIVO_LUFS_SESION,
               techo_dbtp: float = g1_sonoridad.TECHO_DBTP_SESION,
               tasa: int = TASA_SESION, canales: int = CANALES_SESION,
               ancho: int = ANCHO_SESION,
               briefs_esperados: Sequence[str] | None = BRIEFS_DEL_PROTOCOLO,
               ) -> dict[str, Any]:
    """Prepara `04-sesion/` y sella `05-ciego/`. Devuelve un informe sin semilla.

    El informe se imprime y se puede pegar en el acta: por eso no lleva ni la
    semilla ni el reparto. Todo lo que rompe el ciego esta dentro del sello.
    """
    recogidas = recoger_series(directorios)
    briefs = comprobar_rejilla(recogidas, briefs_esperados)
    series = sorted(recogidas)
    if semilla is None:
        semilla = nueva_semilla()

    sesion = raiz / DIR_SESION
    sesion.mkdir(parents=True, exist_ok=True)

    filas: list[dict[str, Any]] = []
    loudness: list[dict[str, Any]] = []
    escritos: list[Path] = []
    bajo_objetivo = 0

    for brief in briefs:
        reparto = reparto_de_brief(semilla, brief, series)
        # Se escribe en orden de ETIQUETA, no de serie: asi ni el orden de
        # creacion en el sistema de ficheros sigue al de las series.
        for serie in sorted(series, key=lambda s: reparto[s]):
            etiqueta = reparto[serie]
            origen = recogidas[serie][brief]

            matriz, tasa_origen, ancho_origen = g1_sonoridad.leer_wav(origen)
            canales_origen = matriz.shape[1]
            duracion = matriz.shape[0] / float(tasa_origen) if tasa_origen else 0.0

            uniforme = g1_sonoridad.ajustar_canales(
                g1_sonoridad.remuestrear(matriz, tasa_origen, tasa), canales
            )
            normalizada, ajuste = g1_sonoridad.normalizar(
                uniforme, tasa, objetivo_lufs, techo_dbtp
            )

            destino = sesion / f"{brief}-{etiqueta}.wav"
            g1_sonoridad.escribir_wav(destino, normalizada, tasa, ancho)
            escritos.append(destino)
            if not ajuste.objetivo_alcanzado:
                bajo_objetivo += 1

            filas.append({
                "brief": brief,
                "etiqueta_ciega": etiqueta,
                "serie": serie,
                "fichero_origen": str(origen),
                "sha256_origen": _sha256(origen),
                "fichero_sesion": destino.name,
                "sha256_sesion": _sha256(destino),
                "tasa_origen": tasa_origen,
                "canales_origen": canales_origen,
                "bits_origen": ancho_origen * 8,
                "duracion_s": round(duracion, 3),
                "lufs_origen": round(ajuste.lufs_medido, 2),
                "dbtp_origen": round(ajuste.dbtp_medido, 2),
                "ganancia_db": round(ajuste.ganancia_db, 3),
                "lufs_final": round(ajuste.lufs_final, 2),
                "dbtp_final": round(ajuste.dbtp_final, 2),
                "objetivo_alcanzado": "si" if ajuste.objetivo_alcanzado else "no",
                "motivo": ajuste.motivo,
            })
            loudness.append({
                "etiqueta": f"{brief}-{etiqueta}",
                "brief": brief,
                "lufs": round(ajuste.lufs_final, 2),
                "objetivo_lufs": objetivo_lufs,
                "techo_dbtp": techo_dbtp,
            })

    # Una sola marca de tiempo para todas: ordenar la carpeta por fecha no puede
    # ser una via de escape del ciego.
    marca = time.time_ns()
    for ruta in escritos:
        os.utime(ruta, ns=(marca, marca))

    with (sesion / "loudness.csv").open("w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(_CABECERA_LOUDNESS))
        escritor.writeheader()
        escritor.writerows(sorted(loudness, key=lambda f: f["etiqueta"]))
    (sesion / "LEEME.txt").write_text(
        _TEXTO_LEEME_SESION.format(objetivo=objetivo_lufs), encoding="utf-8", newline="\n"
    )

    sello = sellar_mapa_series(raiz, filas, semilla, objetivo_lufs, techo_dbtp)
    return {
        "raiz": str(raiz),
        "series": series,
        "briefs": len(briefs),
        "pistas": len(filas),
        "pistas_bajo_objetivo": bajo_objetivo,
        "formato_sesion": {
            "tasa_hz": tasa, "canales": canales, "bits": ancho * 8,
            "objetivo_lufs": objetivo_lufs, "techo_dbtp": techo_dbtp,
        },
        "sello_mapa": sello,
    }


# --------------------------------------------------------------------------- #
# Linea de comandos
# --------------------------------------------------------------------------- #

def _par_serie(texto: str) -> tuple[str, Path]:
    if "=" not in texto:
        raise argparse.ArgumentTypeError(
            f"'{texto}' no tiene la forma nombre=ruta (por ejemplo propia=./propio)."
        )
    nombre, _, ruta = texto.partition("=")
    nombre = nombre.strip()
    if not nombre:
        raise argparse.ArgumentTypeError(f"'{texto}': falta el nombre de la serie.")
    return nombre, Path(ruta.strip())


def construir_parser() -> argparse.ArgumentParser:
    """Parser del CLI. **No hay `--semilla`, y es a proposito.**

    Fijar la semilla desde fuera equivale a conocer el reparto sin abrir el
    sello: seria una puerta trasera al ciego con aspecto de opcion comoda. Los
    tests pasan la semilla llamando a `anonimizar()` directamente.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Ciega las series de G1 entre si (g1-protocolo.md §5.4): normaliza al "
            "nivel de sesion, recodifica uniforme y sin metadatos, baraja por brief "
            "y sella el mapa. La semilla se sortea y solo queda dentro del sellado."
        )
    )
    parser.add_argument(
        "--serie", action="append", required=True, type=_par_serie, metavar="NOMBRE=RUTA",
        help="Serie a cegar; repetir una vez por serie (propia, libreria, suno).",
    )
    parser.add_argument(
        "--salida", required=True, type=Path, metavar="RAIZ",
        help="Raiz de evaluacion (§10.2); se escriben 04-sesion/ y 05-ciego/.",
    )
    parser.add_argument("--objetivo-lufs", type=float,
                        default=g1_sonoridad.OBJETIVO_LUFS_SESION)
    parser.add_argument("--techo-dbtp", type=float,
                        default=g1_sonoridad.TECHO_DBTP_SESION)
    parser.add_argument("--tasa", type=int, default=TASA_SESION)
    parser.add_argument("--canales", type=int, default=CANALES_SESION)
    parser.add_argument(
        "--ensayo", action="store_true",
        help=(
            "Relaja la rejilla a los briefs encontrados en vez de exigir los 10 de §4. "
            "Es para PROBAR el circuito con menos material. Una tanda de verdad con menos "
            "de 10 briefs mide otra cosa que el gate y §8.1 la invalida, asi que esto se "
            "pide a proposito y nunca deberia aparecer en la ejecucion real."
        ),
    )
    return parser


def _forzar_utf8_en_consola() -> None:
    """La consola de Windows es cp1252 y se come «§» y las flechas.

    Mismo apano que `g1_generar.py`: este script se corre en el portatil, fuera
    del contenedor, y cita el protocolo por seccion. Dentro del contenedor no
    hace nada porque ya es UTF-8.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError, OSError):
            pass


def main(argv: Iterable[str] | None = None) -> int:
    _forzar_utf8_en_consola()
    args = construir_parser().parse_args(list(argv) if argv is not None else None)
    directorios = dict(args.serie)
    if len(directorios) != len(args.serie):
        sys.stderr.write("Hay dos series con el mismo nombre.\n")
        return 2

    try:
        informe = anonimizar(
            directorios, args.salida,
            objetivo_lufs=args.objetivo_lufs, techo_dbtp=args.techo_dbtp,
            tasa=args.tasa, canales=args.canales,
            briefs_esperados=None if args.ensayo else BRIEFS_DEL_PROTOCOLO,
        )
    except ValueError as error:
        sys.stderr.write(f"{error}\n")
        return 1

    formato = informe["formato_sesion"]
    sys.stdout.write(
        f"{informe['pistas']} pistas de {len(informe['series'])} series "
        f"({', '.join(informe['series'])}) sobre {informe['briefs']} briefs.\n"
        f"Formato de sesion: {formato['tasa_hz']} Hz / {formato['canales']} canales / "
        f"{formato['bits']} bit, {formato['objetivo_lufs']:g} LUFS con techo "
        f"{formato['techo_dbtp']:g} dBTP.\n"
        f"Bajo objetivo por techo de pico: {informe['pistas_bajo_objetivo']} "
        f"(el detalle esta en el sellado).\n"
        f"Pistas en {args.salida / DIR_SESION}\n"
        f"Mapa sellado en {args.salida / DIR_CIEGO / NOMBRE_MAPA} "
        f"(sha256 {informe['sello_mapa']['sha256'][:16]}...). NO ABRIR hasta §5.6.\n"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - envoltorio de linea de comandos
    raise SystemExit(main())
