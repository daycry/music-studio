#!/usr/bin/env python3
"""Medicion del A/B del planificador de 5 Hz — analisis de senal, sin GPU.

Que hace
--------
Toma las pistas que produjo `generate_smoke.py --matriz`, mide sobre cada una un
juego de descriptores y —esto es lo importante— **compara contrastes, no pistas
sueltas**. Una tabla de ocho numeros por pista no responde a la pregunta; lo que
la responde es si la distancia CON-planificador vs SIN-planificador es mayor que
la distancia que produce cambiar la semilla.

Por que el contraste de semilla es la vara de medir
---------------------------------------------------
Ya esta medido en este proyecto que cambiar la semilla mueve mucho el audio. Si
el planificador mueve el audio MENOS que un cambio de semilla, entonces su efecto
no se distingue del ruido de muestreo: no es una mejora, es otra tirada de dados.
Por eso cada metrica se reporta tres veces:

* `d_lm`     — |m(con) - m(sin)| a **igual semilla**. Es el efecto del planificador.
* `d_semilla`— |m(s1) - m(s2)| dentro de **la misma rama**. Es el ruido de referencia.
* `ratio`    — `d_lm / d_semilla`. **Menor que 1 = el planificador mueve menos que
  el azar.** Mayor que 1 (y bastante) es lo unico que justificaria seguir.

Se anade un contraste **cruzado** (distinta rama y distinta semilla) como cota
superior: si `d_lm` se parece a `d_cruzado`, el planificador cambia tanto como
cambiarlo todo; si se parece a cero, no cambia nada.

Distancias de audio directas
----------------------------
Ademas de los descriptores escalares se calculan dos distancias entre pistas:

* `dist_logmel` — L1 media entre log-mel-espectrogramas. Es la que mejor captura
  «suenan distinto» sin castigar desfases de fase.
* `corr_onda`   — correlacion de Pearson entre formas de onda.

`corr_onda` merece un aviso: la rama CON y la rama SIN comparten **exactamente el
mismo ruido de difusion** (verificado en el codigo: `prepare_noise` usa un
`torch.Generator` propio sembrado con la semilla, y el bucle ODE vendorizado no
vuelve a sortear nada). Asi que una correlacion alta entre CON y SIN significa
«el plan casi no desvio la trayectoria», y una baja significa que si.

Uso::

    python spikes/medir_ab.py --directorio D:/srv/ace-step/out \\
        --salida D:/srv/ace-step/out/ab-medidas.json
"""

from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import find_peaks

# --- Parametros de analisis ------------------------------------------------- #
#: Ventana de la STFT. 2048 a 48 kHz son 42,7 ms: resolucion suficiente para el
#: centroide y el rolloff sin emborronar los transitorios de la percusion.
N_FFT = 2048
SALTO = 512
#: Frontera de «brillo» que pide el encargo.
CORTE_AGUDOS_HZ = 4000.0
#: Rolloff al 95 % de la energia acumulada.
FRACCION_ROLLOFF = 0.95
#: Bandas mel para el log-mel y para la matriz de autosimilitud.
N_MEL = 64
#: Rango dinamico del log-mel, en dB por debajo del maximo de la pista.
#:
#: NO es cosmetico, y lo cazo un test: con un suelo ABSOLUTO (`+1e-10`) la
#: distancia log-mel queda dominada por las bandas casi mudas, donde el logaritmo
#: se dispara. Medido: anadir ruido inaudible a un seno de 440 Hz daba distancia
#: 13,2, mientras que mover ese mismo seno de 440 Hz a 3.000 Hz —un cambio
#: musicalmente enorme— daba 7,4. O sea, el orden INVERTIDO. Recortar a 80 dB por
#: debajo del maximo es lo que hace `power_to_db(ref=max, top_db=80)` de librosa,
#: y deja la metrica mirando lo que se oye en vez del suelo de ruido.
#:
#: 60 y no 80: es el valor MEDIDO que arregla ese orden invertido (con 80 el
#: ruido seguia mandando: 17,2 contra 10,1). Sobre material con el espectro lleno
#: —que es el caso real: dos pistas del mismo modelo— la distancia es identica de
#: 100 dB a 40 dB de recorte (0,605 frente a 2,097), o sea que el valor no
#: inclina la comparacion; solo quita el suelo inaudible. 60 dB por debajo del
#: pico de la pista no se oye en una escucha normal.
TOP_DB = 60.0


# --- Utilidades ------------------------------------------------------------- #
def leer_wav(ruta: Path) -> tuple[np.ndarray, np.ndarray, int]:
    """Devuelve `(mono, estereo, tasa)` en float64 normalizado a [-1, 1)."""
    with wave.open(str(ruta), "rb") as w:
        canales, ancho, tasa, n_tramas = (
            w.getnchannels(),
            w.getsampwidth(),
            w.getframerate(),
            w.getnframes(),
        )
        crudo = w.readframes(n_tramas)
    if ancho != 2:
        raise ValueError(f"{ruta.name}: se esperaba PCM de 16 bits, hay {ancho * 8}.")
    datos = np.frombuffer(crudo, dtype="<i2").astype(np.float64) / 32768.0
    estereo = datos.reshape(-1, canales)
    return estereo.mean(axis=1), estereo, tasa


def _dbfs(v: float) -> float:
    return 20.0 * math.log10(v) if v > 1e-12 else -np.inf


def banco_mel(tasa: int, n_fft: int, n_mel: int) -> np.ndarray:
    """Banco de filtros mel triangulares (implementacion propia, sin librosa)."""

    def a_mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def a_hz(m):
        return 700.0 * (10.0 ** (m / 2595.0) - 1.0)

    bordes = a_hz(np.linspace(a_mel(20.0), a_mel(tasa / 2), n_mel + 2))
    frecs = np.fft.rfftfreq(n_fft, 1.0 / tasa)
    banco = np.zeros((n_mel, len(frecs)))
    for i in range(n_mel):
        izq, cen, der = bordes[i], bordes[i + 1], bordes[i + 2]
        subida = (frecs - izq) / max(cen - izq, 1e-9)
        bajada = (der - frecs) / max(der - cen, 1e-9)
        banco[i] = np.clip(np.minimum(subida, bajada), 0.0, None)
    return banco


def log_mel(mag: np.ndarray, tasa: int, top_db: float = TOP_DB) -> np.ndarray:
    """Log-mel-espectrograma en dB, recortado a `top_db` por debajo del maximo.

    El recorte es lo que impide que las bandas casi mudas manden en la distancia
    (ver `TOP_DB`).
    """
    banco = banco_mel(tasa, N_FFT, N_MEL)
    pot = banco @ (mag**2)
    db = 10.0 * np.log10(np.maximum(pot, 1e-20))
    return np.maximum(db, db.max() - top_db)


def stft_magnitud(x: np.ndarray, n_fft: int = N_FFT, salto: int = SALTO) -> np.ndarray:
    """Magnitud de la STFT, `[n_frecuencias, n_tramas]`, ventana de Hann."""
    # `as_strided` exige memoria contigua: una vista rebanada la rompe en silencio
    # y devolveria basura sin levantar ningun error.
    x = np.ascontiguousarray(x, dtype=np.float64)
    if len(x) < n_fft:
        x = np.pad(x, (0, n_fft - len(x)))
    ventana = np.hanning(n_fft)
    n_tramas = 1 + (len(x) - n_fft) // salto
    tramas = np.lib.stride_tricks.as_strided(
        x,
        shape=(n_tramas, n_fft),
        strides=(x.strides[0] * salto, x.strides[0]),
    ).copy()
    return np.abs(np.fft.rfft(tramas * ventana, axis=1)).T


# --- Descriptores por pista ------------------------------------------------- #
def descriptores(x: np.ndarray, estereo: np.ndarray, tasa: int) -> dict[str, float]:
    """Los ocho descriptores del encargo, mas los estructurales."""
    mag = stft_magnitud(x, N_FFT, SALTO)
    pot = mag**2
    frecs = np.fft.rfftfreq(N_FFT, 1.0 / tasa)
    energia_trama = pot.sum(axis=0)
    # Solo tramas con energia: en las de silencio el centroide es indefinido y
    # promediarlo como cero sesga la media hacia abajo.
    vivas = energia_trama > (energia_trama.max() * 1e-6)

    rms = float(np.sqrt(np.mean(x**2)))
    pico = float(np.max(np.abs(x)))

    centroide = (frecs[:, None] * mag).sum(axis=0) / np.maximum(mag.sum(axis=0), 1e-12)

    acum = np.cumsum(pot, axis=0)
    total = np.maximum(acum[-1], 1e-20)
    idx_rolloff = (acum < FRACCION_ROLLOFF * total).sum(axis=0)
    rolloff = frecs[np.clip(idx_rolloff, 0, len(frecs) - 1)]

    agudos = pot[frecs >= CORTE_AGUDOS_HZ].sum(axis=0) / np.maximum(pot.sum(axis=0), 1e-20)

    # Planitud: media geometrica / media aritmetica de la potencia por trama.
    pot_s = pot + 1e-20
    planitud = np.exp(np.mean(np.log(pot_s), axis=0)) / np.mean(pot_s, axis=0)

    # Flujo: L2 de la diferencia positiva de magnitudes normalizadas por trama.
    mag_n = mag / np.maximum(np.linalg.norm(mag, axis=0, keepdims=True), 1e-12)
    flujo = np.linalg.norm(np.maximum(np.diff(mag_n, axis=1), 0.0), axis=0)

    d: dict[str, float] = {
        "rms": rms,
        "rms_dbfs": _dbfs(rms),
        "pico": pico,
        "pico_dbfs": _dbfs(pico),
        "factor_cresta_db": _dbfs(pico) - _dbfs(rms),
        "centroide_hz": float(np.mean(centroide[vivas])),
        "rolloff95_hz": float(np.mean(rolloff[vivas])),
        "energia_sobre_4k_pct": float(np.mean(agudos[vivas]) * 100.0),
        "planitud_espectral": float(np.mean(planitud[vivas])),
        "flujo_espectral": float(np.mean(flujo)),
        "correlacion_lr": float(
            np.corrcoef(estereo[:, 0], estereo[:, 1])[0, 1] if estereo.shape[1] > 1 else 1.0
        ),
    }
    d.update(estructura(x, mag, tasa))
    d.update(pulso(mag, tasa))
    return d


def estructura(x: np.ndarray, mag: np.ndarray, tasa: int) -> dict[str, float]:
    """Descriptores ESTRUCTURALES: es lo que el planificador deberia aportar.

    Un planificador de 5 Hz que funciona no tiene por que cambiar el brillo ni el
    nivel: tiene que cambiar como se ORGANIZA la pista en el tiempo. Tres formas
    complementarias de mirarlo:

    * `acf_env_pico` — autocorrelacion de la envolvente de energia. Mide cuanto se
      repite la pista a si misma (pulso, compas, frase). Se busca el maximo entre
      0,5 s y un tercio de la duracion, evitando el lag 0.
    * `std_rms_1s`  — desviacion tipica del RMS por segundo, en dB. Una pista con
      secciones sube y baja; una textura plana no.
    * `novedad_*`   — curva de novedad sobre la matriz de autosimilitud log-mel
      con nucleo de tablero de ajedrez. Los picos son fronteras de seccion.
    """
    salida: dict[str, float] = {}

    # --- Envolvente de energia a 100 Hz (salto de 10 ms) -------------------- #
    salto_env = int(tasa * 0.01)
    n = len(x) // salto_env
    env = np.sqrt(np.array([np.mean(x[i * salto_env : (i + 1) * salto_env] ** 2) for i in range(n)]))
    env = env - env.mean()
    if np.std(env) > 1e-12:
        acf = np.correlate(env, env, mode="full")[len(env) - 1 :]
        acf /= acf[0]
        lag_min, lag_max = int(0.5 * 100), min(int(len(env) / 3), len(acf) - 1)
        if lag_max > lag_min:
            tramo = acf[lag_min:lag_max]
            salida["acf_env_pico"] = float(np.max(tramo))
            salida["acf_env_lag_s"] = float((lag_min + int(np.argmax(tramo))) / 100.0)
        else:
            salida["acf_env_pico"] = float("nan")
            salida["acf_env_lag_s"] = float("nan")
    else:
        salida["acf_env_pico"] = float("nan")
        salida["acf_env_lag_s"] = float("nan")

    # --- Varianza de energia entre tramos de 1 s ---------------------------- #
    n_seg = len(x) // tasa
    if n_seg >= 2:
        rms_seg = np.array(
            [np.sqrt(np.mean(x[i * tasa : (i + 1) * tasa] ** 2)) for i in range(n_seg)]
        )
        db_seg = 20.0 * np.log10(np.maximum(rms_seg, 1e-12))
        salida["std_rms_1s_db"] = float(np.std(db_seg))
        salida["rango_rms_1s_db"] = float(np.max(db_seg) - np.min(db_seg))
    else:
        salida["std_rms_1s_db"] = float("nan")
        salida["rango_rms_1s_db"] = float("nan")

    # --- Novedad sobre la matriz de autosimilitud --------------------------- #
    logmel = log_mel(mag, tasa)
    # Normalizar cada trama: la similitud debe ser de TIMBRE, no de nivel.
    v = logmel - logmel.mean(axis=0, keepdims=True)
    v /= np.maximum(np.linalg.norm(v, axis=0, keepdims=True), 1e-12)
    ssm = v.T @ v

    # Nucleo de tablero de ajedrez con ventana gaussiana. 1,5 s de medio ancho:
    # busca fronteras de seccion, no cambios de golpe.
    medio = max(int(1.5 * tasa / SALTO), 4)
    if ssm.shape[0] > 2 * medio + 2:
        ejes = np.arange(-medio, medio)
        gx, gy = np.meshgrid(ejes, ejes)
        signo = np.sign(gx) * np.sign(gy)
        nucleo = signo * np.exp(-(gx**2 + gy**2) / (2 * (medio / 2.0) ** 2))
        novedad = np.zeros(ssm.shape[0])
        for i in range(medio, ssm.shape[0] - medio):
            novedad[i] = np.sum(ssm[i - medio : i + medio, i - medio : i + medio] * nucleo)
        util = novedad[medio : ssm.shape[0] - medio]
        if util.size and np.ptp(util) > 0:
            util_n = (util - util.min()) / np.ptp(util)
            picos, _ = find_peaks(util_n, prominence=0.25, distance=medio)
            salida["novedad_media"] = float(np.mean(util_n))
            salida["novedad_std"] = float(np.std(util_n))
            salida["cambios_seccion"] = float(len(picos))
            salida["cambios_por_minuto"] = float(len(picos) / (len(x) / tasa) * 60.0)
        else:
            salida.update(
                {"novedad_media": float("nan"), "novedad_std": float("nan"),
                 "cambios_seccion": float("nan"), "cambios_por_minuto": float("nan")}
            )
    else:
        salida.update(
            {"novedad_media": float("nan"), "novedad_std": float("nan"),
             "cambios_seccion": float("nan"), "cambios_por_minuto": float("nan")}
        )
    return salida


# --- Ritmo: envolvente de ATAQUES, tempo y fuerza del pulso ----------------- #
#
# Por que un bloque aparte y no reusar `acf_env_pico`: aquel mide la envolvente de
# ENERGIA (RMS por trama). Sirve para ver si la pista se repite a si misma, pero
# un pad que sube y baja le da tanta autocorrelacion como un bombo. Lo que aqui se
# quiere medir es el ENCAJE RITMICO —la queja del propietario es que las voces no
# siguen el ritmo de la base—, y para eso hay que mirar los ATAQUES: saltos
# positivos del espectro, no el nivel.
#
# Todo lo de este bloque es un PROXY instrumental. Mide la mezcla, no la voz
# aislada, y no dictamina calidad musical: eso es escucha humana (G1). Sirve para
# decir si hay o no una diferencia MEDIBLE entre dos ramas.

#: Rango de tempo donde se busca el pulso. Fuera de el, lo que se encuentra son
#: armonicos del compas o de la frase, no el pulso.
BPM_MIN, BPM_MAX = 50.0, 200.0
#: Banda del bombo y del sub 808: es la que lleva la rejilla.
BANDA_GRAVE_HZ = (30.0, 200.0)
#: Banda telefonica. La voz cantada vive aqui casi entera, y la percusion grave
#: casi nada, que es justo lo que hace util comparar las dos.
BANDA_VOZ_HZ = (300.0, 3400.0)


def envolvente_ataques(
    mag: np.ndarray,
    tasa: int,
    banda: tuple[float, float] | None = None,
    ref: float | None = None,
) -> np.ndarray:
    """Envolvente de ataques (flujo espectral rectificado) de una banda.

    En dB y no en lineal a proposito: un ataque es un salto MULTIPLICATIVO, y en
    lineal el instrumento mas fuerte de la mezcla se come los ataques de todos los
    demas —que es exactamente el error que haria invisible el problema de la voz
    contra un bombo alto—. El suelo a `TOP_DB` por debajo de `ref` evita que el
    silencio entre golpes genere saltos enormes al volver a entrar.

    `ref` es la potencia de referencia de los dB y NO es un detalle. MEDIDO: con
    una referencia POR BANDA (el maximo de cada banda), un tren de golpes de 60 Hz
    daba en la banda de voz una envolvente de ataques casi tan grande como en la
    banda grave (ratio 1,63) pese a no haber nada de voz. La causa es que
    normalizar cada banda contra su propio maximo sube el suelo de la banda vacia
    hasta la escala completa, y entonces la fuga del transitorio —que en energia
    es despreciable— se convierte en un ataque de libro. Con una referencia COMUN
    a todo el espectro, una banda 40 dB por debajo se queda pegada al suelo y su
    flujo es el que le corresponde: casi cero.

    Esto importa porque la comparacion voz-contra-grave se apoya en que las dos
    bandas sean comparables en magnitud. Para el TEMPO daba igual (la
    autocorrelacion es invariante a escala); para el ENCAJE, no.
    """
    frecs = np.fft.rfftfreq(N_FFT, d=1.0 / tasa)
    m = mag
    if banda is not None:
        sel = (frecs >= banda[0]) & (frecs < banda[1])
        if not sel.any():
            return np.zeros(max(mag.shape[1] - 1, 0))
        m = mag[sel]
    pot = m**2
    if ref is None:
        ref = float(np.max(mag**2))
    ref = float(ref) + 1e-20
    db = 10.0 * np.log10(np.maximum(pot / ref, 10.0 ** (-TOP_DB / 10.0)))
    return np.maximum(np.diff(db, axis=1), 0.0).mean(axis=0)


def tempo_por_autocorrelacion(
    env: np.ndarray, tasa_env: float, bpm_min: float = BPM_MIN, bpm_max: float = BPM_MAX
) -> tuple[float, float]:
    """Devuelve `(bpm, fuerza_del_pulso)` por autocorrelacion de la envolvente.

    `fuerza_del_pulso` es la altura del pico de la autocorrelacion NORMALIZADA por
    el lag 0, con la envolvente centrada: 0 es «no hay periodicidad a ese tempo» y
    1 es «la envolvente se repite identica». Es la medida que discrimina un pulso
    marcado de uno emborronado, y por eso es la que mas importa aqui.
    """
    e = np.asarray(env, dtype=np.float64)
    if e.size < 4 or not np.isfinite(e).all() or np.std(e) < 1e-12:
        return float("nan"), float("nan")
    e = e - e.mean()
    acf = np.correlate(e, e, mode="full")[e.size - 1 :]
    if acf[0] <= 0:
        return float("nan"), float("nan")
    acf = acf / acf[0]
    lag_min = max(int(round(60.0 / bpm_max * tasa_env)), 1)
    lag_max = min(int(round(60.0 / bpm_min * tasa_env)), acf.size - 1)
    if lag_max <= lag_min:
        return float("nan"), float("nan")
    tramo = acf[lag_min : lag_max + 1]
    i = int(np.argmax(tramo))
    lag = lag_min + i
    fuerza = float(tramo[i])
    # Interpolacion parabolica sobre los tres puntos del pico: a 93,75 tramas/s un
    # lag entero son ~1,5 BPM de resolucion a 94 BPM, que es mas error del que
    # tiene sentido reportar cuando se compara contra un objetivo exacto.
    if 0 < lag < acf.size - 1:
        y0, y1, y2 = acf[lag - 1], acf[lag], acf[lag + 1]
        denom = y0 - 2.0 * y1 + y2
        if abs(denom) > 1e-12:
            lag = lag + 0.5 * (y0 - y2) / denom
    if lag <= 0:
        return float("nan"), float("nan")
    return float(60.0 * tasa_env / lag), fuerza


def _plegar_bpm(bpm: float, minimo: float = 70.0, maximo: float = 140.0) -> float:
    """Lleva el tempo a una octava comparable, doblando o partiendo por dos.

    La autocorrelacion no distingue 94 de 47 ni de 188: los tres explican la misma
    envolvente. Para comparar dos ramas hace falta mirarlas en la misma octava.
    """
    if not math.isfinite(bpm) or bpm <= 0:
        return float("nan")
    for _ in range(8):
        if bpm < minimo:
            bpm *= 2.0
        elif bpm > maximo:
            bpm /= 2.0
        else:
            break
    return float(bpm)


def desfase_voz_beat(
    env_voz: np.ndarray, env_grave: np.ndarray, tasa_env: float, bpm: float
) -> tuple[float, float]:
    """`(desfase_ms, coherencia)` entre los ataques de la voz y los del grave.

    Se busca el maximo de la correlacion cruzada normalizada dentro de MEDIO pulso
    a cada lado: mas alla, el que se encontraria es el golpe siguiente, no el
    mismo desplazado.

    Signo: **positivo = la voz llega TARDE** respecto al grave.
    `np.correlate(a, b, "full")[centro + k] = sum_t a[t+k]*b[t]`, que es maximo
    cuando `a[s] ~ b[s-k]`, o sea cuando `a` es `b` retrasada `k` tramas.

    `coherencia` es esa correlacion en su maximo (-1..1): si es baja, no es que la
    voz vaya adelantada o atrasada de forma consistente, es que NO SIGUE una
    rejilla comun con el grave. Para la queja del propietario, una coherencia baja
    dice mas que un desfase grande.
    """
    a = np.asarray(env_voz, dtype=np.float64)
    b = np.asarray(env_grave, dtype=np.float64)
    n = min(a.size, b.size)
    if n < 8 or not math.isfinite(bpm) or bpm <= 0:
        return float("nan"), float("nan")
    a, b = a[:n], b[:n]
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return float("nan"), float("nan")
    a = (a - a.mean()) / np.std(a)
    b = (b - b.mean()) / np.std(b)
    cc = np.correlate(a, b, mode="full") / n
    centro = n - 1
    max_lag = max(int(round(60.0 / bpm / 2.0 * tasa_env)), 1)
    inicio, fin = max(centro - max_lag, 0), min(centro + max_lag, cc.size - 1)
    tramo = cc[inicio : fin + 1]
    i = int(np.argmax(tramo))
    lag = (inicio + i) - centro
    return float(lag / tasa_env * 1000.0), float(tramo[i])


def pulso(mag: np.ndarray, tasa: int) -> dict[str, float]:
    """Bloque de ritmo completo: tempo, fuerza del pulso y encaje voz-base."""
    tasa_env = tasa / SALTO
    # UNA referencia para las tres envolventes: ver `envolvente_ataques`. Con una
    # por banda, la fuga de los transitorios del bombo en la banda de voz sale del
    # mismo tamano que la voz y el encaje medido es un espejismo.
    ref = float(np.max(mag**2))
    env_total = envolvente_ataques(mag, tasa, None, ref)
    env_grave = envolvente_ataques(mag, tasa, BANDA_GRAVE_HZ, ref)
    env_voz = envolvente_ataques(mag, tasa, BANDA_VOZ_HZ, ref)

    bpm, fuerza = tempo_por_autocorrelacion(env_total, tasa_env)
    bpm_g, fuerza_g = tempo_por_autocorrelacion(env_grave, tasa_env)
    bpm_v, fuerza_v = tempo_por_autocorrelacion(env_voz, tasa_env)
    desfase_ms, coherencia = desfase_voz_beat(env_voz, env_grave, tasa_env, bpm_g)

    return {
        "bpm_acf": bpm,
        "bpm_acf_plegado": _plegar_bpm(bpm),
        "pulso_fuerza": fuerza,
        "bpm_grave": bpm_g,
        "bpm_grave_plegado": _plegar_bpm(bpm_g),
        "pulso_fuerza_grave": fuerza_g,
        "bpm_voz": bpm_v,
        "bpm_voz_plegado": _plegar_bpm(bpm_v),
        "pulso_fuerza_voz": fuerza_v,
        "desfase_voz_beat_ms": desfase_ms,
        "coherencia_voz_beat": coherencia,
    }


# --- Distancias entre pistas ------------------------------------------------ #
def distancias(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    """Distancias de audio directas entre dos pistas de la misma duracion."""
    n = min(len(a["mono"]), len(b["mono"]))
    xa, xb = a["mono"][:n], b["mono"][:n]
    corr = float(np.corrcoef(xa, xb)[0, 1]) if np.std(xa) > 0 and np.std(xb) > 0 else float("nan")

    ma, mb = stft_magnitud(xa), stft_magnitud(xb)
    k = min(ma.shape[1], mb.shape[1])
    # Cada pista se recorta contra SU propio maximo: la distancia mide diferencia
    # de contenido audible, no de ganancia global.
    la = log_mel(ma[:, :k], a["tasa"])
    lb = log_mel(mb[:, :k], b["tasa"])
    return {
        "corr_onda": corr,
        "dist_logmel": float(np.mean(np.abs(la - lb))),
        "dist_logmel_norm": float(np.mean(np.abs(la - lb)) / (np.std(np.concatenate([la, lb])) + 1e-12)),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Mide y compara el A/B del planificador de 5 Hz.")
    p.add_argument("--directorio", default="D:/srv/ace-step/out")
    p.add_argument("--salida", default="D:/srv/ace-step/out/ab-medidas.json")
    args = p.parse_args()

    raiz = Path(args.directorio)
    etiquetas = ["lm-si-s1", "lm-no-s1", "lm-si-s2", "lm-no-s2", "lm-si-60", "lm-no-60"]
    pistas: dict[str, dict[str, Any]] = {}
    for et in etiquetas:
        # El nombre real lleva duracion, timestamp y hash: se busca por prefijo.
        candidatos = sorted(raiz.glob(f"{et}-*.wav"), key=lambda q: q.stat().st_mtime)
        if not candidatos:
            print(f"[falta] no hay WAV para {et}")
            continue
        ruta = candidatos[-1]
        mono, estereo, tasa = leer_wav(ruta)
        d = descriptores(mono, estereo, tasa)
        d["fichero"] = ruta.name
        d["duracion_s"] = round(len(mono) / tasa, 3)
        pistas[et] = {**d, "mono": mono, "tasa": tasa}
        print(f"[medido] {et:10s} {ruta.name}  {d['duracion_s']} s")

    metricas = [
        "rms_dbfs", "pico_dbfs", "factor_cresta_db", "centroide_hz", "rolloff95_hz",
        "energia_sobre_4k_pct", "planitud_espectral", "flujo_espectral",
        "acf_env_pico", "std_rms_1s_db", "rango_rms_1s_db",
        "novedad_media", "novedad_std", "cambios_seccion",
    ]

    informe: dict[str, Any] = {
        "pistas": {
            k: {m: v[m] for m in [*metricas, "fichero", "duracion_s", "acf_env_lag_s", "correlacion_lr"]}
            for k, v in pistas.items()
        },
        "contrastes": {},
        "distancias_audio": {},
    }

    # --- Contrastes escalares (solo el bloque de 25 s, que tiene los dos ejes) #
    cuatro = ["lm-si-s1", "lm-no-s1", "lm-si-s2", "lm-no-s2"]
    if all(k in pistas for k in cuatro):
        filas = {}
        for m in metricas:
            v = {k: pistas[k][m] for k in cuatro}
            d_lm = np.mean([abs(v["lm-si-s1"] - v["lm-no-s1"]), abs(v["lm-si-s2"] - v["lm-no-s2"])])
            d_se = np.mean([abs(v["lm-si-s1"] - v["lm-si-s2"]), abs(v["lm-no-s1"] - v["lm-no-s2"])])
            d_cr = np.mean([abs(v["lm-si-s1"] - v["lm-no-s2"]), abs(v["lm-no-s1"] - v["lm-si-s2"])])
            filas[m] = {
                "con_s1": v["lm-si-s1"], "sin_s1": v["lm-no-s1"],
                "con_s2": v["lm-si-s2"], "sin_s2": v["lm-no-s2"],
                "d_lm": float(d_lm), "d_semilla": float(d_se), "d_cruzado": float(d_cr),
                "ratio_lm_semilla": float(d_lm / d_se) if d_se > 1e-12 else float("nan"),
            }
        informe["contrastes"]["25s"] = filas

    # --- Distancias de audio ------------------------------------------------- #
    pares = [
        ("LM  (misma semilla s1)", "lm-si-s1", "lm-no-s1"),
        ("LM  (misma semilla s2)", "lm-si-s2", "lm-no-s2"),
        ("semilla (rama CON)", "lm-si-s1", "lm-si-s2"),
        ("semilla (rama SIN)", "lm-no-s1", "lm-no-s2"),
        ("cruzado (todo distinto)", "lm-si-s1", "lm-no-s2"),
        ("cruzado (todo distinto)", "lm-no-s1", "lm-si-s2"),
        ("LM  (60 s)", "lm-si-60", "lm-no-60"),
    ]
    for nombre, a, b in pares:
        if a in pistas and b in pistas:
            informe["distancias_audio"].setdefault(nombre, []).append(
                {"a": a, "b": b, **distancias(pistas[a], pistas[b])}
            )

    if "lm-si-60" in pistas and "lm-no-60" in pistas:
        informe["contrastes"]["60s"] = {
            m: {
                "con": pistas["lm-si-60"][m],
                "sin": pistas["lm-no-60"][m],
                "d_lm": float(abs(pistas["lm-si-60"][m] - pistas["lm-no-60"][m])),
            }
            for m in metricas
        }

    # `json.dumps` escribe `NaN`/`Infinity`, que NO son JSON valido y revientan a
    # cualquier lector estricto. Se convierten a `null` antes de escribir.
    def _limpiar(o):
        if isinstance(o, dict):
            return {k: _limpiar(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_limpiar(v) for v in o]
        if isinstance(o, float) and not math.isfinite(o):
            return None
        return o

    Path(args.salida).write_text(
        json.dumps(_limpiar(informe), indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print(f"\n[informe] {args.salida}")

    # --- Impresion legible --------------------------------------------------- #
    if "25s" in informe["contrastes"]:
        print("\n=== 25 s: efecto del planificador frente al efecto de la semilla ===")
        cab = f"{'metrica':22s} {'CON s1':>10s} {'SIN s1':>10s} {'CON s2':>10s} {'SIN s2':>10s} {'d_LM':>9s} {'d_semilla':>9s} {'ratio':>7s}"
        print(cab)
        print("-" * len(cab))
        for m, f in informe["contrastes"]["25s"].items():
            print(
                f"{m:22s} {f['con_s1']:10.4g} {f['sin_s1']:10.4g} {f['con_s2']:10.4g} "
                f"{f['sin_s2']:10.4g} {f['d_lm']:9.4g} {f['d_semilla']:9.4g} {f['ratio_lm_semilla']:7.2f}"
            )
    print("\n=== Distancias de audio directas ===")
    for nombre, lista in informe["distancias_audio"].items():
        for e in lista:
            print(
                f"{nombre:26s} {e['a']:9s} vs {e['b']:9s}  "
                f"corr_onda {e['corr_onda']:+.4f}  dist_logmel {e['dist_logmel']:.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
