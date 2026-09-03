#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sonoridad EBU R128 y normalizacion de nivel para la sesion de escucha de G1.

Que resuelve
============
`gates/g1-protocolo.md` §5.5 lo dice sin rodeos: **comparar sin igualar el
loudness mide sonoridad, no calidad**. La linea base de libreria viene
masterizada a nivel comercial y aplastaria cualquier salida de modelo por el
mero hecho de sonar mas fuerte. Antes de la escucha, las 30 pistas (o 20 en la
variante B) se llevan todas al mismo nivel: **-16 LUFS integrados con pico real
<= -1 dBTP**, medicion EBU R128.

Por que aqui no hay `ffmpeg`
============================
§5.5 propone `ffmpeg loudnorm` en dos pasadas. Este modulo lo implementa en
numpy/scipy. Dos motivos, y el segundo es el que manda:

1. `ffmpeg` no esta instalado ni en el host ni en la imagen del runner, y no se
   va a instalar. Meter un binario externo en la cadena que prepara el material
   del gate es dependencia nueva sin ficha de licencia comprobada.
2. **`loudnorm` no garantiza aplicar solo ganancia.** Incluso en dos pasadas
   puede revertir a modo dinamico y **comprimir**. Comprimir alteraria la
   **dimension 2 de la rubrica** (§3.2, «calidad de mezcla y ausencia de
   artefactos»), que es una de las cinco que se puntuan. Normalizar la muestra
   alterando justo lo que se mide invalida la medida.

Lo que se hace en su lugar es lo que §5.5 pide literalmente —«la normalizacion
es **solo ganancia**; nada de limitar ni comprimir»—: se mide, se calcula **un
escalar**, y se multiplica. `normalizar()` devuelve exactamente
`senal * 10**(g/20)`, y hay un test que lo comprueba con igualdad estricta.

Que se implementa, y contra que verdad se valida
================================================
* **Sonoridad integrada segun ITU-R BS.1770-4**: ponderacion K en dos etapas
  (estanteria de agudos + paso alto RLB), media cuadratica por bloques de 400 ms
  con 75 % de solape, y las **dos puertas** — absoluta a -70 LUFS y relativa a
  -10 LU sobre la media de los bloques que pasan la absoluta.
* **Pico real** por sobremuestreo x4: el pico entre muestras es mayor que el de
  las muestras, y esa diferencia llega a 3 dB en el peor caso (un seno a fs/4
  desfasado 45 grados). Medir solo las muestras deja pasar recortes reales.
* **Ganancia acotada**: si la ganancia que pide -16 LUFS hiciera pasar el pico
  real de -1 dBTP, se aplica **la menor de las dos**. El protocolo prefiere una
  pista mas baja a una recortada — un recorte nuestro se oiria en D2 y
  penalizaria al modelo por un fallo de exportacion que es nuestro. Cuando eso
  pasa, `Ajuste.objetivo_alcanzado` es `False` y `Ajuste.motivo` lo explica:
  **quien lea el acta tiene que saber que esa pista no llego al objetivo.**

Coeficientes: la ITU tabula la ponderacion K **solo a 48 kHz**. A 48 kHz este
modulo usa esos numeros literales, sin derivar nada. A otras tasas obtiene el
prototipo analogico por transformada bilineal inversa y lo vuelve a discretizar;
el viaje de ida y vuelta a 48 kHz es exacto (2e-16) y a 44,1 / 96 kHz la
calibracion del estandar a 997 Hz se conserva dentro de 0,004 dB. Toda la cadena
del runner es 48 kHz de todos modos, y `g1_anonimizar.py` remuestrea cualquier
entrada a la tasa de sesion antes de medir.

Este modulo **no puntua, no compara series y no escribe veredicto**. Solo mide y
aplica ganancia.
"""

from __future__ import annotations

import argparse
import math
import sys
import wave
from dataclasses import dataclass, asdict
from math import gcd
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from scipy import signal as _signal

# --------------------------------------------------------------------------- #
# Constantes del estandar y del protocolo
# --------------------------------------------------------------------------- #

#: Tasa a la que la ITU tabula los coeficientes de la ponderacion K.
TASA_TABLA = 48000

#: Termino de calibracion de `L_K` (BS.1770-4). No es un ajuste libre: cancela
#: exactamente la ganancia de la ponderacion K a 997 Hz (+0,691014 dB).
OFFSET_LK_DB = -0.691

#: Bloque de la medida integrada y solape, en las unidades del estandar.
BLOQUE_S = 0.400
SOLAPE = 0.75

#: Las dos puertas. La absoluta es un umbral fijo; la relativa se calcula sobre
#: la media de los bloques que pasan la absoluta.
PUERTA_ABSOLUTA_LUFS = -70.0
PUERTA_RELATIVA_LU = -10.0

#: Pesos de canal de BS.1770-4 (L, R, C, Ls, Rs). Mono y estereo van todos a 1.
PESOS_CANAL = (1.0, 1.0, 1.0, 1.41, 1.41)

#: Objetivo de la SESION de escucha (§5.5). No es el objetivo de producto: ese
#: es por destino (D-23: broadcast -23, streaming -14, stems sin normalizar).
#: Este es un nivel unico para las 30 pistas precisamente porque su funcion es
#: ELIMINAR la variable, no fijar un estandar de entrega.
OBJETIVO_LUFS_SESION = -16.0
TECHO_DBTP_SESION = -1.0

#: Factor de sobremuestreo del medidor de pico real. BS.1770-4 Anexo 2 usa x4.
SOBREMUESTREO_PICO = 4

#: Ventana del interpolador polifasico del pico real. Un Kaiser con beta alto da
#: banda de rechazo suficiente para que el pico interpolado no venga de rizado.
_VENTANA_PICO = ("kaiser", 12.0)

#: Tabla 1 de BS.1770-4 — estanteria de agudos, a 48 kHz.
_TABLA_SHELF = (
    (1.53512485958697, -2.69169618940638, 1.19839281085285),
    (1.0, -1.69065929318241, 0.73248077421585),
)

#: Tabla 2 de BS.1770-4 — paso alto RLB, a 48 kHz.
_TABLA_PASO_ALTO = (
    (1.0, -2.0, 1.0),
    (1.0, -1.99004745483398, 0.99007225036621),
)

Biquad = tuple[np.ndarray, np.ndarray]


# --------------------------------------------------------------------------- #
# Utilidades de senal
# --------------------------------------------------------------------------- #

def como_matriz(senal: Any) -> np.ndarray:
    """Devuelve la senal como matriz `(muestras, canales)` de `float64`.

    Acepta mono en 1-D. Rechaza `nan` e `inf`: un `nan` propagado acaba dando
    `-inf` en la medida, que es indistinguible de un silencio legitimo, y
    entonces una pista rota entraria en la sesion como si fuera correcta.
    """
    matriz = np.asarray(senal, dtype=np.float64)
    if matriz.ndim == 1:
        matriz = matriz[:, np.newaxis]
    if matriz.ndim != 2:
        raise ValueError(
            f"La senal debe ser (muestras,) o (muestras, canales); llego {matriz.shape}."
        )
    if matriz.shape[1] > len(PESOS_CANAL):
        raise ValueError(
            f"BS.1770-4 define pesos para {len(PESOS_CANAL)} canales; llegaron "
            f"{matriz.shape[1]}."
        )
    if not np.isfinite(matriz).all():
        raise ValueError(
            "La senal contiene valores no finitos (nan o inf). Se aborta en vez de "
            "medir: un nan da -inf y se confundiria con silencio."
        )
    return matriz


def _a_db(amplitud: float) -> float:
    """dB de una amplitud lineal, con `-inf` para el cero (sin avisos)."""
    return 20.0 * math.log10(amplitud) if amplitud > 0.0 else -math.inf


# --------------------------------------------------------------------------- #
# Ponderacion K
# --------------------------------------------------------------------------- #

def _a_analogico(b: Sequence[float], a: Sequence[float], tasa: int
                 ) -> tuple[np.ndarray, np.ndarray]:
    """Transformada bilineal INVERSA de un biquad digital a su prototipo en `s`.

    Con `z = (k + s) / (k - s)` y `k = 2 * tasa`, sustituir y multiplicar por
    `(k + s)^2` deja, para cada trio `(c0, c1, c2)`:

        s^2 * (c0 - c1 + c2) + s * 2k * (c0 - c2) + k^2 * (c0 + c1 + c2)
    """
    k = 2.0 * tasa

    def convertir(c: Sequence[float]) -> np.ndarray:
        c0, c1, c2 = (float(v) for v in c)
        return np.array([c0 - c1 + c2, 2.0 * k * (c0 - c2), k * k * (c0 + c1 + c2)])

    return convertir(b), convertir(a)


def _redisctretizar(b: Sequence[float], a: Sequence[float], tasa: int) -> Biquad:
    """Lleva un biquad tabulado a 48 kHz hasta otra tasa de muestreo."""
    if tasa == TASA_TABLA:
        return np.asarray(b, dtype=np.float64), np.asarray(a, dtype=np.float64)
    b_s, a_s = _a_analogico(b, a, TASA_TABLA)
    b_z, a_z = _signal.bilinear(b_s, a_s, fs=tasa)
    return np.asarray(b_z, dtype=np.float64), np.asarray(a_z, dtype=np.float64)


def coeficientes_ponderacion_k(tasa: int) -> list[Biquad]:
    """Las dos etapas de la ponderacion K a la tasa pedida.

    A 48 kHz devuelve la tabla de la ITU sin tocar. A otras tasas, el prototipo
    analogico redisctretizado (ver la cabecera del modulo).
    """
    if tasa <= 0:
        raise ValueError(f"Tasa de muestreo invalida: {tasa}.")
    return [
        _redisctretizar(_TABLA_SHELF[0], _TABLA_SHELF[1], tasa),
        _redisctretizar(_TABLA_PASO_ALTO[0], _TABLA_PASO_ALTO[1], tasa),
    ]


def aplicar_ponderacion_k(senal: Any, tasa: int) -> np.ndarray:
    """Filtra la senal con la cascada de la ponderacion K, canal a canal."""
    matriz = como_matriz(senal)
    salida = matriz
    for b, a in coeficientes_ponderacion_k(tasa):
        salida = _signal.lfilter(b, a, salida, axis=0)
    return salida


# --------------------------------------------------------------------------- #
# Sonoridad integrada (BS.1770-4 con las dos puertas)
# --------------------------------------------------------------------------- #

def _medias_cuadraticas_por_bloque(ponderada: np.ndarray, tasa: int) -> np.ndarray:
    """`z[j, c]`: media cuadratica del canal `c` en el bloque `j`.

    Bloques de 400 ms con 75 % de solape, o sea un paso de 100 ms. Se calcula
    con suma acumulada para que el coste sea lineal en las muestras y no
    cuadratico en el solape.
    """
    largo_bloque = int(round(BLOQUE_S * tasa))
    paso = int(round(largo_bloque * (1.0 - SOLAPE)))
    if largo_bloque <= 0 or paso <= 0:
        raise ValueError(f"Tasa demasiado baja para bloques de {BLOQUE_S} s: {tasa}.")

    n = ponderada.shape[0]
    if n < largo_bloque:
        return np.empty((0, ponderada.shape[1]), dtype=np.float64)

    acumulada = np.concatenate(
        [np.zeros((1, ponderada.shape[1])), np.cumsum(np.square(ponderada), axis=0)],
        axis=0,
    )
    inicios = np.arange(0, n - largo_bloque + 1, paso)
    return (acumulada[inicios + largo_bloque] - acumulada[inicios]) / float(largo_bloque)


def _sonoridad_de(z: np.ndarray, pesos: np.ndarray) -> np.ndarray:
    """`l_j = -0,691 + 10 log10(sum_c G_c z_jc)`, con `-inf` donde la suma es 0."""
    suma = z @ pesos
    salida = np.full(suma.shape, -math.inf, dtype=np.float64)
    positivos = suma > 0.0
    salida[positivos] = OFFSET_LK_DB + 10.0 * np.log10(suma[positivos])
    return salida


def sonoridad_integrada(senal: Any, tasa: int) -> float:
    """Sonoridad integrada en LUFS, o `-inf` si no queda ni un bloque.

    `-inf` es la respuesta honesta para el silencio, para una pista por debajo
    de la puerta absoluta y para un fragmento mas corto que un bloque: en los
    tres casos no hay nada que medir, y devolver un numero seria inventarlo.
    """
    matriz = como_matriz(senal)
    ponderada = aplicar_ponderacion_k(matriz, tasa)
    z = _medias_cuadraticas_por_bloque(ponderada, tasa)
    if z.shape[0] == 0:
        return -math.inf

    pesos = np.asarray(PESOS_CANAL[: z.shape[1]], dtype=np.float64)

    # Puerta absoluta: -70 LUFS, umbral fijo.
    pasan_absoluta = _sonoridad_de(z, pesos) > PUERTA_ABSOLUTA_LUFS
    if not pasan_absoluta.any():
        return -math.inf

    # Puerta relativa: -10 LU respecto de la media de los que pasaron la absoluta.
    media_absoluta = z[pasan_absoluta].mean(axis=0)
    suma_absoluta = float(media_absoluta @ pesos)
    if suma_absoluta <= 0.0:
        return -math.inf
    umbral_relativo = OFFSET_LK_DB + 10.0 * np.log10(suma_absoluta) + PUERTA_RELATIVA_LU

    pasan = pasan_absoluta & (_sonoridad_de(z, pesos) > umbral_relativo)
    if not pasan.any():
        return -math.inf

    suma_final = float(z[pasan].mean(axis=0) @ pesos)
    if suma_final <= 0.0:
        return -math.inf
    return float(OFFSET_LK_DB + 10.0 * np.log10(suma_final))


# --------------------------------------------------------------------------- #
# Picos
# --------------------------------------------------------------------------- #

def pico_de_muestra_dbfs(senal: Any) -> float:
    """Pico de las muestras, en dBFS. No es el pico real: ver abajo."""
    matriz = como_matriz(senal)
    if matriz.size == 0:
        return -math.inf
    return _a_db(float(np.max(np.abs(matriz))))


def pico_real_dbtp(senal: Any, tasa: int, factor: int = SOBREMUESTREO_PICO) -> float:
    """Pico real (true peak) en dBTP, por sobremuestreo x`factor`.

    La forma de onda entre dos muestras puede superar a las dos, y en el peor
    caso —un seno a fs/4 desfasado 45 grados— lo hace por 3,01 dB enteros. Un
    medidor que solo mire las muestras da por bueno un nivel que al convertir a
    analogico o al recodificar recorta de verdad.

    El resultado nunca baja del pico de muestra: el interpolador puede quedarse
    corto en los extremos del fragmento, pero el pico real es, por definicion,
    al menos el mayor de las muestras.
    """
    matriz = como_matriz(senal)
    if matriz.size == 0:
        return -math.inf
    pico_muestras = float(np.max(np.abs(matriz)))
    if pico_muestras == 0.0:
        return -math.inf
    if factor <= 1:
        return _a_db(pico_muestras)

    sobremuestreada = _signal.resample_poly(matriz, factor, 1, axis=0, window=_VENTANA_PICO)
    return _a_db(max(pico_muestras, float(np.max(np.abs(sobremuestreada)))))


# --------------------------------------------------------------------------- #
# Ganancia hacia el objetivo de la sesion
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Ajuste:
    """Lo que se decidio hacer con una pista, y por que.

    `lufs_final` y `dbtp_final` solo los rellena `normalizar()`, que vuelve a
    MEDIR despues de aplicar la ganancia en vez de sumarla sobre el papel. La
    diferencia importa: la puerta absoluta de -70 LUFS es un umbral fijo, asi
    que en pistas muy flojas la medida no es exactamente equivariante a la
    ganancia. Lo que va al acta es lo medido.
    """

    lufs_medido: float
    dbtp_medido: float
    objetivo_lufs: float
    techo_dbtp: float
    ganancia_db: float
    ganancia_pedida_db: float
    limitado_por_pico: bool
    objetivo_alcanzado: bool
    motivo: str
    lufs_final: float | None = None
    dbtp_final: float | None = None

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


#: Umbral de decision para «la ganancia se quedo corta por culpa del pico».
#: Milesimas de dB son ruido de coma flotante, no una pista que no llego.
_TOLERANCIA_DB = 1e-6


def ganancia_para_objetivo(senal: Any, tasa: int,
                           objetivo_lufs: float = OBJETIVO_LUFS_SESION,
                           techo_dbtp: float = TECHO_DBTP_SESION) -> Ajuste:
    """Calcula la ganancia constante a aplicar. No toca la senal.

    Regla de §5.5, sin margen de interpretacion: si la ganancia que pide el
    objetivo de sonoridad hiciera pasar el pico real del techo, se aplica **la
    menor de las dos** y se registra que la pista se quedo por debajo.
    """
    matriz = como_matriz(senal)
    lufs = sonoridad_integrada(matriz, tasa)
    dbtp = pico_real_dbtp(matriz, tasa)

    if not math.isfinite(lufs):
        return Ajuste(
            lufs_medido=lufs, dbtp_medido=dbtp, objetivo_lufs=objetivo_lufs,
            techo_dbtp=techo_dbtp, ganancia_db=0.0, ganancia_pedida_db=math.inf,
            limitado_por_pico=False, objetivo_alcanzado=False,
            motivo=(
                "Silencio o pista entera por debajo de la puerta absoluta de "
                f"{PUERTA_ABSOLUTA_LUFS:g} LUFS: no hay sonoridad que igualar y no se "
                "aplica ganancia. Revisar la pista antes de meterla en la sesion."
            ),
        )

    pedida = objetivo_lufs - lufs
    margen_pico = math.inf if not math.isfinite(dbtp) else techo_dbtp - dbtp
    ganancia = min(pedida, margen_pico)
    limitado = ganancia < pedida - _TOLERANCIA_DB

    if limitado:
        motivo = (
            f"Techo de pico real: llegar a {objetivo_lufs:g} LUFS pedia "
            f"{pedida:+.2f} dB, pero el pico real esta en {dbtp:.2f} dBTP y solo "
            f"caben {margen_pico:+.2f} dB bajo {techo_dbtp:g} dBTP. Se aplica la "
            f"menor: la pista queda en {lufs + ganancia:.2f} LUFS, "
            f"{objetivo_lufs - (lufs + ganancia):.2f} LU por debajo del objetivo. "
            "Se prefiere una pista mas baja a una recortada (§5.5)."
        )
    else:
        motivo = f"Ganancia de {ganancia:+.2f} dB hasta {objetivo_lufs:g} LUFS."

    return Ajuste(
        lufs_medido=lufs, dbtp_medido=dbtp, objetivo_lufs=objetivo_lufs,
        techo_dbtp=techo_dbtp, ganancia_db=ganancia, ganancia_pedida_db=pedida,
        limitado_por_pico=limitado, objetivo_alcanzado=not limitado, motivo=motivo,
    )


def normalizar(senal: Any, tasa: int,
               objetivo_lufs: float = OBJETIVO_LUFS_SESION,
               techo_dbtp: float = TECHO_DBTP_SESION) -> tuple[np.ndarray, Ajuste]:
    """Aplica SOLO la ganancia constante calculada, y vuelve a medir.

    La salida es exactamente `senal * 10**(g/20)`. Nada de limitador, nada de
    compresion, nada de recorte: §5.5 lo prohibe porque alteraria la dimension 2
    de la rubrica, que es una de las cinco que se puntuan.
    """
    matriz = como_matriz(senal)
    ajuste = ganancia_para_objetivo(matriz, tasa, objetivo_lufs, techo_dbtp)
    salida = matriz * (10.0 ** (ajuste.ganancia_db / 20.0))
    return salida, Ajuste(
        **{
            **ajuste.como_dict(),
            "lufs_final": sonoridad_integrada(salida, tasa),
            "dbtp_final": pico_real_dbtp(salida, tasa),
        }
    )


# --------------------------------------------------------------------------- #
# Entrada/salida de WAV — sin metadatos, por diseno
# --------------------------------------------------------------------------- #

#: Anchos de muestra PCM entera admitidos, en bytes.
_ANCHOS = (1, 2, 3, 4)


def leer_wav(ruta: Path) -> tuple[np.ndarray, int, int]:
    """Lee un WAV PCM a `(matriz float64 en [-1, 1), tasa, ancho en bytes)`.

    Solo PCM entero. El modulo `wave` de la biblioteca estandar rechaza por si
    solo cualquier cosa que no sea `WAVE_FORMAT_PCM`, lo que de paso descarta
    formatos comprimidos que traerian su propia coloracion al material del gate.
    """
    with wave.open(str(ruta), "rb") as entrada:
        canales = entrada.getnchannels()
        ancho = entrada.getsampwidth()
        tasa = entrada.getframerate()
        marcos = entrada.getnframes()
        crudo = entrada.readframes(marcos)

    if ancho not in _ANCHOS:
        raise ValueError(f"{ruta.name}: ancho de muestra no admitido ({ancho} bytes).")
    if canales < 1:
        raise ValueError(f"{ruta.name}: WAV sin canales.")

    bruto = np.frombuffer(crudo, dtype=np.uint8)
    if ancho == 1:
        # PCM de 8 bit es SIN signo con punto medio en 128 (formato WAV).
        muestras = bruto.astype(np.float64) - 128.0
        escala = 128.0
    elif ancho == 3:
        # 24 bit no tiene dtype propio: se rellena a 32 bit por la izquierda para
        # conservar el signo y luego se divide por el desplazamiento.
        bloques = bruto.reshape(-1, 3)
        relleno = np.zeros((bloques.shape[0], 4), dtype=np.uint8)
        relleno[:, 1:] = bloques
        muestras = relleno.view("<i4").reshape(-1).astype(np.float64)
        escala = float(1 << 31)
    else:
        tipo = "<i2" if ancho == 2 else "<i4"
        muestras = bruto.view(tipo).astype(np.float64)
        escala = float(1 << (8 * ancho - 1))

    matriz = (muestras / escala).reshape(-1, canales)
    return matriz, tasa, ancho


def escribir_wav(ruta: Path, senal: Any, tasa: int, ancho: int = 2) -> None:
    """Escribe un WAV PCM **sin una sola etiqueta**.

    El modulo `wave` escribe `RIFF`/`WAVE` con `fmt ` y `data` y nada mas: no
    tiene manera de emitir un `LIST`/`INFO`, un `ID3` ni un `TSSE`. Por eso
    reescribir las muestras basta para cumplir §5.4.2 sin `ffmpeg
    -map_metadata -1`. Hay un test que abre el fichero resultante y comprueba
    que los unicos trozos presentes son esos dos: un tag delataria el origen de
    la pista sin necesidad de escucharla.
    """
    matriz = como_matriz(senal)
    if ancho not in (2, 3, 4):
        raise ValueError(f"Ancho de salida no admitido: {ancho} bytes.")

    escala = float(1 << (8 * ancho - 1))
    limite = escala - 1.0
    enteros = np.clip(np.rint(matriz * escala), -escala, limite)

    if ancho == 3:
        de_32 = enteros.astype("<i4").reshape(-1)
        crudo = de_32.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    else:
        crudo = enteros.astype("<i2" if ancho == 2 else "<i4").tobytes()

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(ruta), "wb") as salida:
        salida.setnchannels(matriz.shape[1])
        salida.setsampwidth(ancho)
        salida.setframerate(tasa)
        salida.writeframes(crudo)


def remuestrear(senal: Any, tasa_origen: int, tasa_destino: int) -> np.ndarray:
    """Remuestreo racional. Necesario para que el WAV no delate la serie.

    §5.4.2 exige que las 30 pistas salgan con la **misma frecuencia de
    muestreo**: una cabecera a 44,1 kHz frente a otra a 48 kHz identifica la
    pista de libreria sin escuchar nada.
    """
    matriz = como_matriz(senal)
    if tasa_origen == tasa_destino:
        return matriz
    divisor = gcd(int(tasa_origen), int(tasa_destino))
    return np.asarray(
        _signal.resample_poly(matriz, tasa_destino // divisor, tasa_origen // divisor, axis=0),
        dtype=np.float64,
    )


def ajustar_canales(senal: Any, canales: int) -> np.ndarray:
    """Iguala el numero de canales. Solo sube de mono; nunca mezcla a la baja.

    Una mezcla a la baja de material que no conocemos (que hacer con un centro,
    con que ganancia) es una decision de mezcla, y este modulo no toma
    decisiones de mezcla: alterar la mezcla es alterar D2. Si llega material con
    mas canales de los pedidos, se aborta y lo resuelve el propietario.
    """
    matriz = como_matriz(senal)
    if matriz.shape[1] == canales:
        return matriz
    if matriz.shape[1] == 1:
        return np.repeat(matriz, canales, axis=1)
    raise ValueError(
        f"No se sabe pasar de {matriz.shape[1]} a {canales} canales sin tomar una "
        "decision de mezcla, y mezclar alteraria la dimension 2 de la rubrica. "
        "Convertir la pista antes de traerla."
    )


# --------------------------------------------------------------------------- #
# CLI: medir ficheros sueltos (util para rellenar y verificar `loudness.csv`)
# --------------------------------------------------------------------------- #

def _texto_medida(ruta: Path) -> str:
    matriz, tasa, ancho = leer_wav(ruta)
    lufs = sonoridad_integrada(matriz, tasa)
    dbtp = pico_real_dbtp(matriz, tasa)
    muestra = pico_de_muestra_dbfs(matriz)
    duracion = matriz.shape[0] / float(tasa) if tasa else 0.0
    return (
        f"{ruta.name}\n"
        f"    {tasa} Hz - {matriz.shape[1]} canales - {ancho * 8} bit - {duracion:.2f} s\n"
        f"    sonoridad integrada : {lufs:8.2f} LUFS\n"
        f"    pico real           : {dbtp:8.2f} dBTP\n"
        f"    pico de muestra     : {muestra:8.2f} dBFS\n"
    )


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Mide sonoridad integrada (EBU R128) y pico real de ficheros WAV. "
            "Solo mide: para normalizar la sesion de G1, usar g1_anonimizar.py."
        )
    )
    parser.add_argument("ficheros", nargs="+", type=Path, help="WAV PCM a medir.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = construir_parser().parse_args(list(argv) if argv is not None else None)
    fallos = 0
    for ruta in args.ficheros:
        try:
            sys.stdout.write(_texto_medida(ruta))
        except Exception as error:  # noqa: BLE001 - se informa y se sigue con el resto
            fallos += 1
            sys.stderr.write(f"{ruta}: {error}\n")
    return 1 if fallos else 0


if __name__ == "__main__":  # pragma: no cover - envoltorio de linea de comandos
    raise SystemExit(main())
