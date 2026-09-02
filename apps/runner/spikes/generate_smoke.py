#!/usr/bin/env python3
"""Spike de humo de generacion real — `T-03` (Fase 0, GPU local).

Que hace
--------
Lleva un prompt de estilo y una letra en castellano hasta un **fichero WAV en
disco**, por el camino real del runner: `adapters/ace_step/adapter.py`
(`AceStepAdapter.load()` + `AceStepAdapter.generate()`), que a su vez resuelve el
shim (`ace_step_shim:build_pipeline`) y ejecuta el pipeline vendorizado. Aqui no
se reimplementa ni una linea del camino de inferencia: si el adapter, el shim o
`vendor/` estan mal, este spike falla, que es justo lo que se le pide.

Que mide
--------
* **Cronometraje por etapas**: carga (con su desglose `weights_download` /
  `vram_load` / `warmup`), condicionamiento, difusion, decode y escritura.
* **VRAM por etapa**. El contador de pico de `torch.cuda` es global al proceso y
  no se puede reiniciar por etapa sin instrumentar el shim, y el shim no se toca
  para esto. Asi que la VRAM se **muestrea** en un hilo aparte (40 ms por
  defecto) y cada etapa se queda con el maximo de las muestras que caen en su
  ventana. Es un pico **muestreado**: un transitorio mas corto que el periodo
  puede escaparse. El pico de la generacion entera si es exacto y sale de la
  telemetria del adapter (contador de `torch.cuda`, reiniciado por generacion).
* **Verificacion del artefacto**: existencia y tamano, cabecera (tasa, canales,
  ancho de muestra), duracion real frente a la pedida con la tolerancia de ±5 %
  del contrato observable (C-01), finitud de la senal, y comprobacion de que
  **no es silencio** (RMS y pico), que es el modo de fallo silencioso mas
  probable de un pipeline de difusion mal condicionado.

Las fronteras de etapa no se estiman: se leen de los hitos que el propio shim y
el adapter registran por `logging` (`Condicionamiento listo en...`, `Difusion
completada en...`, `Decode en...`, `Audio escrito en...`), anotando el instante
monotono de cada registro. Por eso el informe lleva, para cada etapa, la duracion
de la **ventana** medida aqui y la **declarada** por el shim: si divergen, se ve.

Que NO hace
-----------
* No juzga la calidad musical: eso es escucha humana (gate **G1**, `T-09`).
* No normaliza loudness ni transcodifica (`T-19`/`T-45`). El WAV sale a la tasa
  nativa del VAE, que ya son 48 kHz estereo: no hay remuestreo ni ffmpeg.
* No emite manifiesto de procedencia (`T-27`, F5). Como sustituto minimo, el
  informe JSON registra la ruta y el SHA-256 de **cada** modulo del runner que se
  ejecuto —incluido el vendorizado— y, si se pide, el de los pesos.

Guardarrail G-01
----------------
Exige `ACE_STEP_REQUIRE_GPU=1` y aborta si el adapter no resuelve el backend
`gpu`. Una corrida real no puede degradar al mock en silencio: un WAV simulado
colado como medicion es peor que no tener WAV.

Uso (dentro del contenedor, con pesos y salida montados)::

    MSYS_NO_PATHCONV=1 docker run --rm --gpus all \
      -e ACE_STEP_REQUIRE_GPU=1 \
      -v "D:\\srv\\ace-step\\weights:/weights:ro" \
      -v "D:\\srv\\ace-step\\out:/outputs" \
      -v "C:\\...\\apps\\runner:/work:ro" \
      --entrypoint python ace-step-runner:t05 \
      /work/spikes/generate_smoke.py --duraciones 30,180

El A/B del planificador de 5 Hz
------------------------------
`--sin-lm` desactiva el planificador (`usar_lm=False`) y devuelve `src_latents` al
latente de silencio, que es como generaba este pipeline antes de conectarlo. Las
dos pistas se producen con **la misma semilla, la misma letra, el mismo prompt y
los mismos metadatos**; lo unico que cambia es si hubo plan. Dos contenedores, uno
cada vez (el artefacto ocupa 7,0 GiB y cargarlo dos veces en el mismo proceso no
cabe en 8 GB de VRAM)::

    # A — con planificador
    ... generate_smoke.py --duraciones 25 --semilla 20260902 \
        --fichero-pesos ace_step_1_5_lm.safetensors --etiqueta lm-on

    # B — control, sin planificador
    ... generate_smoke.py --duraciones 25 --semilla 20260902 \
        --fichero-pesos ace_step_1_5_lm.safetensors --etiqueta lm-off --sin-lm

Cualquier otra diferencia entre las dos ordenes invalida la comparacion. El
informe JSON registra `peticion_base.model_params` completo, asi que siempre se
puede comprobar cual de las dos es cada fichero.

Codigo de salida: `0` si todas las comprobaciones bloqueantes pasan en todas las
duraciones, `1` si alguna falla, `2` si la ejecucion revienta antes de poder
comprobar nada.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import os
import sys
import threading
import time
import traceback
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AQUI = Path(__file__).resolve()

#: Periodo del muestreador de VRAM. 40 ms es un compromiso: fino para no perderse
#: el pico del condicionamiento (que dura ~1 s) y grueso para que el hilo no
#: compita por el GIL con el bucle de difusion.
PERIODO_MUESTREO_S = 0.04

#: Tolerancia de duracion del contrato observable (C-01): ±5 %.
TOLERANCIA_DURACION = 0.05

#: Umbrales de «esto no es silencio». Un RMS por debajo de -60 dBFS o un pico por
#: debajo de -26 dBFS en una pista de pop no es una pista floja: es un fallo.
RMS_MINIMO = 10 ** (-60.0 / 20.0)
PICO_MINIMO = 10 ** (-26.0 / 20.0)

# OJO A LAS TILDES Y A LA EÑE. La primera version de estas constantes iba sin
# ellas, y no era un detalle cosmetico: el normalizador es NFC y no elimina
# acentos, asi que "sonar" y "sonar" son secuencias de tokens DISTINTAS y
# palabras distintas. Le estabamos pidiendo al modelo que cantara "sonar" (emitir
# sonido) cuando la letra dice "sonar". Con `vocal_language="es"` esto degrada la
# pronunciacion y la prosodia, y hundiria el WER del gate G1 por un motivo que no
# es del modelo sino nuestro. Cualquier letra que se escriba aqui va acentuada.
PROMPT_POR_DEFECTO = (
    "pop electrónico nocturno en castellano, voz femenina cálida, sintetizadores "
    "analógicos, guitarra con delay, bajo profundo, batería suave, 92 BPM, "
    "melancólico, producción limpia"
)

# Metadatos musicales. Hasta el 2026-09-02 se enviaban SIEMPRE como `N/A`, y el
# bloque de metas del prompt viajaba en blanco en cada generacion. Upstream los
# rellena con la cadena de pensamiento de su planificador de 5 Hz; como aqui ese
# planificador esta desconectado, si no los ponemos a mano no los pone nadie.
# El BPM por defecto concuerda con el que ya dice el prompt de estilo (92): un
# prompt que pide 92 BPM y un bloque de metas que dice "no aplica" es una
# contradiccion que el modelo tiene que resolver adivinando.
BPM_POR_DEFECTO = 92
TONALIDAD_POR_DEFECTO = "A minor"
COMPAS_POR_DEFECTO = "4/4"


def _construir_model_params(args, usar_lm: bool | None = None) -> dict:
    """Arma `model_params` omitiendo lo que se pida dejar sin especificar.

    Pasar `--bpm 0`, `--tonalidad ""` o `--compas ""` deja ese metadato fuera,
    que es como reproducir el comportamiento anterior para comparar A/B.
    """
    params: dict = {"vocal_language": args.idioma_voz}
    if args.bpm:
        params["bpm"] = int(args.bpm)
    if args.tonalidad:
        params["keyscale"] = args.tonalidad
    if args.compas:
        params["timesignature"] = args.compas
    # El A/B del planificador de 5 Hz. `--sin-lm` es la rama de control: mismo
    # artefacto, misma semilla, misma letra, mismo prompt y mismos metadatos; lo
    # unico que cambia es si `src_latents` es el plan del LM o el latente de
    # silencio. Cualquier otra diferencia entre las dos corridas invalida la
    # comparacion, asi que no se toca nada mas.
    # `usar_lm` puede venir forzado por la celda de la matriz A/B; si no viene,
    # manda `--sin-lm`, que es el comportamiento de siempre.
    params["usar_lm"] = (not args.sin_lm) if usar_lm is None else bool(usar_lm)
    params["lm_cfg"] = args.lm_cfg
    params["lm_temperatura"] = args.lm_temperatura
    return params



@dataclass(frozen=True)
class CasoAB:
    """Una celda de la matriz A/B: todo lo que puede variar entre pistas.

    El A/B del planificador solo significa algo si entre la rama CON y la rama
    SIN no cambia nada mas que `usar_lm`. Pero para saber si la diferencia
    CON-vs-SIN es mayor que el ruido, hace falta ademas variar la semilla, y eso
    obliga a cruzar dos ejes. Esta estructura es ese cruce, y existe para que la
    matriz se ejecute tras UNA sola carga: el arranque en frio son ~643 s y seis
    contenedores serian ~64 min de puro cargar el mismo artefacto seis veces.

    Que la matriz corra en un unico proceso NO contamina la comparacion, y esto
    esta verificado en el codigo, no supuesto:

    * El ruido de difusion sale de `prepare_noise`, que construye un
      `torch.Generator` propio sembrado con `seed` (`modeling_acestep_v15_turbo.py`).
      No lee el RNG global, asi que no le afecta lo que haya corrido antes.
    * El bucle ODE vendorizado (`vendor/pipeline/diffusion.py`) no vuelve a
      sortear nada: solo llama a `prepare_noise` una vez.
    * El planificador siembra el RNG global el mismo (`torch.manual_seed`) al
      entrar, asi que su plan tampoco depende del estado que dejo la pista
      anterior.

    Consecuencia que es justo lo que se quiere medir: a igual semilla, la rama
    CON y la rama SIN reciben EXACTAMENTE el mismo ruido inicial. Lo unico que
    difiere entre las dos es `src_latents` (el plan del LM o el latente de
    silencio).
    """

    etiqueta: str
    duracion_s: int
    semilla: int
    usar_lm: bool


def _parsear_matriz(texto: str) -> list[CasoAB]:
    """Convierte "etiqueta:duracion:semilla:si|no,..." en celdas de la matriz."""
    casos: list[CasoAB] = []
    for crudo in str(texto).split(","):
        crudo = crudo.strip()
        if not crudo:
            continue
        partes = crudo.split(":")
        if len(partes) != 4:
            raise SystemExit(
                f"--matriz: celda invalida {crudo!r}. Formato: "
                "etiqueta:duracion_s:semilla:si|no"
            )
        etiqueta, duracion, semilla, lm = (p.strip() for p in partes)
        if lm not in ("si", "no"):
            raise SystemExit(f"--matriz: en {crudo!r} el 4.o campo debe ser 'si' o 'no'.")
        casos.append(
            CasoAB(
                etiqueta=etiqueta,
                duracion_s=int(duracion),
                semilla=int(semilla),
                usar_lm=(lm == "si"),
            )
        )
    if not casos:
        raise SystemExit("--matriz vacia.")
    return casos


LETRA_POR_DEFECTO = """[verse]
Se apaga la ciudad y enciendo la consola,
la noche me sostiene, la memoria se desborda.
Un cable, dos acordes, la lluvia en el cristal,
y un coro de neones que no sabe terminar.

[chorus]
Canta, que la máquina aprendió a soñar,
canta, que la noche no se va a acabar.
Deja que la onda se condense al respirar,
y guarda cada huella, que la vamos a firmar.

[verse]
No pido una estrella ni un truco de cristal,
me basta con la traza de lo que fue real."""


# --------------------------------------------------------------------------- #
# Localizacion del codigo del runner
# --------------------------------------------------------------------------- #
# Este fichero se ejecuta desde el bind mount de solo lectura (`/work`), pero el
# codigo que debe ejercitarse es el que **viaja en la imagen** (`/app`): es el
# que corre en produccion y el que tiene hash conocido. Se antepone esa raiz a
# `sys.path` para que gane sobre el directorio del propio script, y el informe
# deja constancia de que fichero se cargo realmente.

def resolver_raiz_app(indicada: str | None = None) -> Path:
    """Devuelve la raiz del runner (la que contiene `adapters/` y `spikes/`)."""
    candidatas: list[Path] = []
    if indicada:
        candidatas.append(Path(indicada))
    del_entorno = os.environ.get("ACE_STEP_APP_ROOT", "").strip()
    if del_entorno:
        candidatas.append(Path(del_entorno))
    candidatas.append(Path("/app"))
    candidatas.append(_AQUI.parents[1])
    for candidata in candidatas:
        if (candidata / "adapters" / "ace_step" / "adapter.py").is_file():
            return candidata.resolve()
    raise SystemExit(
        "No se encontro el codigo del runner. Se buscaron "
        f"{[str(c) for c in candidatas]}. Indica la raiz con --raiz-app o "
        "ACE_STEP_APP_ROOT (debe contener adapters/ace_step/adapter.py)."
    )


def preparar_sys_path(raiz_app: Path) -> None:
    """Antepone las tres carpetas del runner a `sys.path`, en orden."""
    for ruta in (raiz_app / "spikes", raiz_app / "adapters" / "ace_step", raiz_app):
        texto = str(ruta)
        while texto in sys.path:
            sys.path.remove(texto)
        sys.path.insert(0, texto)


def sha256_fichero(ruta: str | Path) -> str:
    digestor = hashlib.sha256()
    with open(ruta, "rb") as fichero:
        for bloque in iter(lambda: fichero.read(8 * 1024 * 1024), b""):
            digestor.update(bloque)
    return digestor.hexdigest()


def procedencia_modulos(raiz_app: Path) -> dict[str, dict[str, str]]:
    """Ruta y SHA-256 de cada modulo del runner que se ha llegado a importar.

    Sustituto minimo del manifiesto de procedencia (`T-27`, F5) para un spike:
    deja escrito **que codigo exacto** produjo el audio, incluido el vendorizado.
    """
    raiz = str(raiz_app)
    salida: dict[str, dict[str, str]] = {}
    for nombre, modulo in list(sys.modules.items()):
        fichero = getattr(modulo, "__file__", None)
        if not fichero:
            continue
        try:
            absoluto = os.path.realpath(fichero)
        except OSError:
            continue
        if not absoluto.startswith(raiz) or not os.path.isfile(absoluto):
            continue
        salida[nombre] = {"fichero": absoluto, "sha256": sha256_fichero(absoluto)}
    return dict(sorted(salida.items()))


# --------------------------------------------------------------------------- #
# Muestreador de VRAM
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class MuestraVram:
    """Una lectura de VRAM con su instante monotono."""

    t: float
    #: `total - libre` segun el driver: incluye el contexto de CUDA y la cache del
    #: asignador de PyTorch. Es lo que ve `nvidia-smi`, y lo que decide si cabe.
    usado_mb: int
    #: Solo tensores vivos (`torch.cuda.memory_allocated`).
    asignado_mb: int
    #: Lo que el asignador le ha quitado al sistema (`torch.cuda.memory_reserved`).
    reservado_mb: int


class MuestreadorVram(threading.Thread):
    """Muestrea la VRAM en un hilo aparte mientras corre la generacion.

    Existe porque el pico por etapa no se puede sacar de `torch.cuda` sin
    reiniciar su contador dentro del shim. Un fallo del muestreador (una GPU que
    deja de responder a `mem_get_info`) no puede tumbar la generacion: se anota y
    se deja de muestrear.
    """

    def __init__(self, indice: int = 0, periodo_s: float = PERIODO_MUESTREO_S) -> None:
        super().__init__(name="muestreador-vram", daemon=True)
        self._indice = indice
        self._periodo = periodo_s
        self._parar = threading.Event()
        self._lock = threading.Lock()
        self._muestras: list[MuestraVram] = []
        self.error: str | None = None
        self.total_mb: int | None = None

    def run(self) -> None:  # noqa: D102
        import torch  # noqa: PLC0415  (perezoso: este fichero se revisa sin torch)

        while True:
            try:
                libre, total = torch.cuda.mem_get_info(self._indice)
                muestra = MuestraVram(
                    t=time.perf_counter(),
                    usado_mb=int((total - libre) // (1024 * 1024)),
                    asignado_mb=int(torch.cuda.memory_allocated(self._indice) // (1024 * 1024)),
                    reservado_mb=int(torch.cuda.memory_reserved(self._indice) // (1024 * 1024)),
                )
                self.total_mb = int(total // (1024 * 1024))
            except Exception as exc:  # noqa: BLE001  (el muestreo nunca tumba la corrida)
                self.error = f"{type(exc).__name__}: {exc}"
                return
            with self._lock:
                self._muestras.append(muestra)
            if self._parar.wait(self._periodo):
                return

    def detener(self) -> None:
        self._parar.set()
        self.join(timeout=5.0)

    def pico(self, t0: float, t1: float) -> dict[str, Any]:
        """Maximos de las muestras dentro de `[t0, t1]`."""
        with self._lock:
            dentro = [m for m in self._muestras if t0 <= m.t <= t1]
        if not dentro:
            return {
                "muestras": 0,
                "detalle": (
                    "ventana mas corta que el periodo de muestreo "
                    f"({self._periodo * 1000:.0f} ms): sin lecturas atribuibles"
                ),
            }
        return {
            "muestras": len(dentro),
            "usado_pico_mb": max(m.usado_mb for m in dentro),
            "asignado_pico_mb": max(m.asignado_mb for m in dentro),
            "reservado_pico_mb": max(m.reservado_mb for m in dentro),
            "usado_final_mb": dentro[-1].usado_mb,
        }


# --------------------------------------------------------------------------- #
# Fronteras de etapa leidas del log del shim
# --------------------------------------------------------------------------- #

class EscuchaEtapas(logging.Handler):
    """Anota el instante monotono de los hitos de etapa del shim y del adapter.

    Se engancha al logger raiz y no formatea nada: mira el `msg` sin interpolar
    (que es una constante del codigo) y se queda con `args[0]` cuando es la
    duracion que el propio shim declara.
    """

    HITOS: tuple[tuple[str, str], ...] = (
        # El planificador de 5 Hz va PRIMERO en la generacion (produce los
        # `src_latents` que consume el condicionamiento) y solo aparece con
        # usar_lm=True. En esta tarjeta corre en CPU y es la etapa mas cara de la
        # pista, asi que sin ella el reparto de tiempos no dice nada.
        ("Planificador listo en", "planificacion"),
        ("Condicionamiento listo en", "condicionamiento"),
        ("Difusion completada en", "difusion"),
        ("Decode en", "decode"),
        ("Audio escrito en", "escritura"),
    )

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self._lock_eventos = threading.Lock()
        self.eventos: list[tuple[str, float, float | None]] = []

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D102
        mensaje = record.msg
        if not isinstance(mensaje, str):
            return
        for prefijo, etapa in self.HITOS:
            if not mensaje.startswith(prefijo):
                continue
            declarado: float | None = None
            argumentos = record.args
            if isinstance(argumentos, tuple) and argumentos:
                primero = argumentos[0]
                if isinstance(primero, (int, float)) and not isinstance(primero, bool):
                    declarado = float(primero)
            with self._lock_eventos:
                self.eventos.append((etapa, time.perf_counter(), declarado))
            return

    def en_ventana(self, t0: float, t1: float) -> list[tuple[str, float, float | None]]:
        """Hitos registrados dentro de `[t0, t1]`, en orden de llegada.

        El filtro por ventana es lo que separa los hitos de una generacion de los
        del `warmup()`, que ejecuta el mismo camino y emite los mismos mensajes
        durante la carga.
        """
        with self._lock_eventos:
            return [e for e in self.eventos if t0 <= e[1] <= t1]


def ventanas_de_etapa(
    hitos: list[tuple[str, float, float | None]], t_inicio: float, t_fin: float
) -> tuple[dict[str, dict[str, Any]], float]:
    """Convierte hitos (marcas de FIN de etapa) en ventanas consecutivas.

    Devuelve las ventanas y los segundos no atribuidos a ninguna (la cola entre el
    ultimo hito y el final real de la llamada).
    """
    ventanas: dict[str, dict[str, Any]] = {}
    cursor = t_inicio
    for etapa, instante, declarado in hitos:
        ventanas[etapa] = {
            "inicio_rel_s": round(cursor - t_inicio, 4),
            "fin_rel_s": round(instante - t_inicio, 4),
            "ventana_s": round(instante - cursor, 4),
            "declarado_por_el_shim_s": None if declarado is None else round(declarado, 4),
            "_t0": cursor,
            "_t1": instante,
        }
        cursor = instante
    return ventanas, round(t_fin - cursor, 4)


# --------------------------------------------------------------------------- #
# Verificacion del WAV
# --------------------------------------------------------------------------- #

def _dbfs(valor: float) -> float | None:
    """dBFS de una amplitud lineal, o `None` si es cero (evita `-inf` en JSON)."""
    return round(20.0 * math.log10(valor), 2) if valor > 0.0 else None


def verificar_wav(ruta: Path, duracion_pedida: float) -> dict[str, Any]:
    """Abre el WAV, mide la senal y evalua las comprobaciones bloqueantes.

    Son las del contrato observable de la spec —formato, duracion ±5 %— mas las
    minimas de sanidad de senal. Ninguna juzga calidad musical: eso es G1.
    """
    import numpy as np  # noqa: PLC0415  (perezoso, igual que torch)

    informe: dict[str, Any] = {"ruta": str(ruta)}
    comprobaciones: dict[str, bool] = {}
    informe["comprobaciones"] = comprobaciones

    comprobaciones["fichero_existe"] = ruta.is_file()
    if not comprobaciones["fichero_existe"]:
        informe["error"] = "El fichero no existe en disco al terminar la generacion."
        return informe
    tamano = ruta.stat().st_size
    informe["tamano_bytes"] = tamano
    comprobaciones["tamano_no_trivial"] = tamano > 44  # 44 B es la cabecera pelada

    with wave.open(str(ruta), "rb") as entrada:
        canales = entrada.getnchannels()
        ancho = entrada.getsampwidth()
        tasa = entrada.getframerate()
        marcos = entrada.getnframes()
        crudo = entrada.readframes(marcos)

    duracion_real = marcos / float(tasa) if tasa else 0.0
    desviacion = (duracion_real - duracion_pedida) / duracion_pedida if duracion_pedida else 0.0
    informe["cabecera"] = {
        "sample_rate": tasa,
        "canales": canales,
        "ancho_muestra_bytes": ancho,
        "marcos": marcos,
        "duracion_real_s": round(duracion_real, 4),
        "duracion_pedida_s": duracion_pedida,
        "desviacion_pct": round(desviacion * 100.0, 3),
    }
    comprobaciones["sample_rate_48k"] = tasa == 48000
    comprobaciones["estereo"] = canales == 2
    comprobaciones["pcm_16_bit"] = ancho == 2
    comprobaciones["duracion_en_tolerancia_5pct"] = abs(desviacion) <= TOLERANCIA_DURACION
    comprobaciones["bytes_coinciden_con_cabecera"] = len(crudo) == marcos * canales * ancho

    if ancho != 2 or marcos == 0:
        informe["error"] = "Sin PCM de 16 bit que analizar."
        return informe

    muestras = np.frombuffer(crudo, dtype="<i2").reshape(-1, canales)
    flotante = muestras.astype(np.float64) / 32768.0

    # El PCM entero no puede contener NaN por construccion; la finitud del tensor
    # en coma flotante la comprueba el shim (`_a_pcm16` aborta si el decode
    # devuelve NaN o inf). Lo que si delata a un NaN convertido a entero es una
    # avalancha de ceros o de saturaciones, y eso se mide abajo.
    comprobaciones["sin_valores_no_finitos"] = bool(np.isfinite(flotante).all())

    rms = float(np.sqrt(np.mean(np.square(flotante))))
    pico = float(np.max(np.abs(flotante)))
    ceros = float(np.mean(muestras == 0))
    saturados = float(np.mean(np.abs(muestras.astype(np.int32)) >= 32767))
    continua = float(np.mean(flotante))

    por_canal = [
        {
            "rms": round(float(np.sqrt(np.mean(np.square(flotante[:, c])))), 6),
            "pico": round(float(np.max(np.abs(flotante[:, c]))), 6),
        }
        for c in range(canales)
    ]

    segundos = marcos // tasa
    rms_por_segundo: list[float] = []
    if segundos:
        bloques = flotante[: segundos * tasa].reshape(segundos, tasa, canales)
        rms_por_segundo = [float(v) for v in np.sqrt(np.mean(np.square(bloques), axis=(1, 2)))]
    mudos = sum(1 for v in rms_por_segundo if v < RMS_MINIMO)

    correlacion = None
    if canales == 2:
        matriz = np.corrcoef(flotante[:, 0], flotante[:, 1])
        if np.isfinite(matriz[0, 1]):
            correlacion = round(float(matriz[0, 1]), 4)

    informe["senal"] = {
        "rms": round(rms, 6),
        "rms_dbfs": _dbfs(rms),
        "pico": round(pico, 6),
        "pico_dbfs": _dbfs(pico),
        "offset_continua": round(continua, 6),
        "muestras_a_cero_pct": round(ceros * 100.0, 3),
        "muestras_saturadas_pct": round(saturados * 100.0, 4),
        "por_canal": por_canal,
        "correlacion_canales": correlacion,
        "rms_por_segundo": {
            "n": len(rms_por_segundo),
            "min": round(min(rms_por_segundo), 6) if rms_por_segundo else None,
            "mediana": (
                round(sorted(rms_por_segundo)[len(rms_por_segundo) // 2], 6)
                if rms_por_segundo
                else None
            ),
            "max": round(max(rms_por_segundo), 6) if rms_por_segundo else None,
            "segundos_por_debajo_de_menos_60_dbfs": mudos,
        },
    }

    comprobaciones["no_es_silencio"] = rms > RMS_MINIMO and pico >= PICO_MINIMO
    comprobaciones["pico_dentro_de_escala"] = 0.0 < pico <= 1.0
    # Informativos: no bloquean, pero se miran. `no_es_silencio` ya cazaria una
    # pista muda entera; esto detecta la pista medio vacia y el falso estereo.
    informe["indicadores"] = {
        "menos_del_10pct_de_segundos_mudos": bool(
            not rms_por_segundo or mudos <= max(1, len(rms_por_segundo) // 10)
        ),
        "recorte_por_debajo_del_1pct": saturados < 0.01,
        "estereo_no_es_mono_duplicado": correlacion is None or correlacion < 0.9999,
    }
    return informe


# --------------------------------------------------------------------------- #
# Ejecucion
# --------------------------------------------------------------------------- #

def _texto_etapas(bloque: dict[str, dict[str, Any]]) -> str:
    lineas = []
    for etapa, datos in bloque.items():
        pico = datos.get("vram", {}).get("usado_pico_mb")
        declarado = datos.get("declarado_por_el_shim_s")
        sufijo = f"  (shim: {declarado:.3f} s)" if declarado is not None else " " * 18
        lineas.append(
            f"    {etapa:<18} {datos['ventana_s']:8.3f} s{sufijo}"
            + (f"  pico VRAM {pico} MiB" if pico is not None else "  pico VRAM n/d")
        )
    return "\n".join(lineas)


async def ejecutar(args: argparse.Namespace) -> int:
    raiz_app = resolver_raiz_app(args.raiz_app)
    preparar_sys_path(raiz_app)

    import adapter as modulo_adapter  # noqa: PLC0415  (tras preparar sys.path)
    from contracts import GenerationRequest  # noqa: PLC0415

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    escucha = EscuchaEtapas()
    logging.getLogger().addHandler(escucha)

    # --- Guardarrail G-01: nada de mock en una corrida real ----------------- #
    if not modulo_adapter._env_flag("ACE_STEP_REQUIRE_GPU"):  # noqa: SLF001
        raise SystemExit(
            "G-01 (pre-dev-checklist §A): este spike solo se ejecuta con "
            "ACE_STEP_REQUIRE_GPU=1. Sin ese guardarrail el adapter puede caer al "
            "mock si CUDA no esta visible, y un WAV simulado colado como medicion es "
            "peor que no tener WAV. Anade '-e ACE_STEP_REQUIRE_GPU=1' al docker run."
        )
    if modulo_adapter._env_flag("ACE_STEP_MOCK"):  # noqa: SLF001
        raise SystemExit("ACE_STEP_MOCK esta activo: esto no seria una generacion real.")

    adaptador = modulo_adapter.AceStepAdapter(
        weights_name=args.fichero_pesos,
        output_dir=salida,
        require_gpu=True,
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

    # La matriz A/B, si se pidio; si no, una celda por duracion con la semilla y
    # la rama globales, que es exactamente el comportamiento anterior.
    if args.matriz:
        casos = _parsear_matriz(args.matriz)
    else:
        casos = [
            CasoAB(
                etiqueta=args.etiqueta,
                duracion_s=d,
                semilla=args.semilla,
                usar_lm=not args.sin_lm,
            )
            for d in args.duraciones
        ]

    informe: dict[str, Any] = {
        "spike": "generate_smoke",
        "tarea": "T-03",
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "gpu",
        "raiz_app": str(raiz_app),
        "guardarrail_g01": "ACE_STEP_REQUIRE_GPU=1 verificado; backend='gpu'",
        "contexto": {
            "device": ctx.device,
            "dtype": ctx.dtype,
            "weights_dir": ctx.weights_dir,
            "weights_file": args.fichero_pesos,
            "max_gpu_seconds": ctx.max_gpu_seconds,
            "offload_solicitado": ctx.offload,
        },
        "peticion_base": {
            "style_prompt": args.prompt,
            "letra": args.letra,
            "semilla": args.semilla,
            "duraciones_s": args.duraciones,
            # Se registra el `model_params` COMPLETO, no solo el prompt: la rama
            # del A/B (`usar_lm`) vive ahi y sin ella el informe no dice cual de
            # las dos versiones es.
            "model_params": _construir_model_params(args),
        },
        # La matriz A/B efectiva. `peticion_base` describe lo COMUN a todas las
        # pistas (prompt, letra, metadatos); aqui esta lo que varia entre ellas,
        # que son los dos unicos ejes del experimento: `usar_lm` y `semilla`.
        "matriz": [
            {
                "etiqueta": c.etiqueta,
                "duracion_s": c.duracion_s,
                "semilla": c.semilla,
                "usar_lm": c.usar_lm,
            }
            for c in casos
        ],
        "muestreo_vram": {
            "periodo_ms": round(args.periodo_muestreo * 1000, 1),
            "nota": (
                "pico MUESTREADO por etapa (maximo de las lecturas de la ventana), no "
                "exacto; el pico exacto de la generacion completa es "
                "telemetria_adapter.vram_peak_mb, del contador de torch.cuda"
            ),
        },
        "generaciones": [],
    }

    muestreador = MuestreadorVram(periodo_s=args.periodo_muestreo)
    muestreador.start()
    codigo = 0
    try:
        # --- Carga (arranque en frio) --------------------------------------- #
        print(f"[carga] pesos {ctx.weights_dir}/{args.fichero_pesos} en {ctx.device}...")
        t_carga_ini = time.perf_counter()
        await adaptador.load(ctx)
        t_carga_fin = time.perf_counter()

        etapas_carga = adaptador.load_stage_timings()
        # Las ventanas de las subetapas de carga se reconstruyen hacia atras desde
        # el final, con las duraciones que midio el `StageTimer` del adapter.
        bloque_carga: dict[str, dict[str, Any]] = {}
        cursor = t_carga_fin
        for etapa in ("warmup", "vram_load", "weights_download"):
            duracion = etapas_carga.get(etapa)
            if duracion is None:
                continue
            t0, t1 = cursor - duracion, cursor
            bloque_carga[etapa] = {
                "ventana_s": round(duracion, 4),
                "vram": muestreador.pico(t0, t1),
            }
            cursor = t0
        informe["carga"] = {
            "total_s": round(t_carga_fin - t_carga_ini, 3),
            "gpu_seconds_de_carga": round(adaptador.load_gpu_seconds(), 3),
            "etapas": dict(reversed(list(bloque_carga.items()))),
            "vram_al_terminar": muestreador.pico(t_carga_fin - 0.2, t_carga_fin),
        }
        resumen_carga = {k: round(v, 2) for k, v in etapas_carga.items()}
        print(f"[carga] lista en {t_carga_fin - t_carga_ini:.2f} s {resumen_carga}")

        # --- Generaciones ---------------------------------------------------- #
        for caso in casos:
            duracion_pedida = caso.duracion_s
            clave = f"{caso.etiqueta}-{duracion_pedida}s-{int(time.time())}"
            params_caso = _construir_model_params(args, usar_lm=caso.usar_lm)
            peticion = GenerationRequest(
                style_prompt=args.prompt,
                duration_s=duracion_pedida,
                max_gpu_seconds=args.max_gpu_seconds,
                idempotency_key=clave,
                lyrics=args.letra,
                instrumental=False,
                seed=caso.semilla,
                model_params=params_caso,
            )
            print(
                f"\n[generacion] {duracion_pedida} s, semilla {caso.semilla}, "
                f"planificador {'SI' if caso.usar_lm else 'NO'}, clave {clave}"
            )
            t_gen_ini = time.perf_counter()
            resultado = await adaptador.generate(peticion)
            t_gen_fin = time.perf_counter()

            hitos = escucha.en_ventana(t_gen_ini, t_gen_fin)
            ventanas, cola = ventanas_de_etapa(hitos, t_gen_ini, t_gen_fin)
            for datos in ventanas.values():
                datos["vram"] = muestreador.pico(datos.pop("_t0"), datos.pop("_t1"))

            artefacto = resultado.artifacts[0]
            if not artefacto.path:
                raise RuntimeError(
                    "El adapter devolvio el audio en memoria: este spike exige fichero en "
                    "disco (revisa --salida)."
                )
            verificacion = verificar_wav(Path(artefacto.path), float(duracion_pedida))

            bloqueantes = verificacion.get("comprobaciones", {})
            todo_ok = bool(bloqueantes) and all(bloqueantes.values())
            if not todo_ok:
                codigo = 1

            informe["generaciones"].append(
                {
                    "duracion_pedida_s": duracion_pedida,
                    "idempotency_key": clave,
                    # Los tres ejes del A/B, explicitos en cada fila: sin esto el
                    # informe no permite reconstruir que pista es cual.
                    "etiqueta": caso.etiqueta,
                    "semilla": caso.semilla,
                    "usar_lm": caso.usar_lm,
                    "model_params": params_caso,
                    "total_s": round(t_gen_fin - t_gen_ini, 3),
                    "etapas": ventanas,
                    "segundos_no_atribuidos_a_ninguna_etapa": cola,
                    "telemetria_adapter": {
                        "gpu_seconds": resultado.telemetry.gpu_seconds,
                        "vram_peak_mb": resultado.telemetry.vram_peak_mb,
                        "offloading_enabled": resultado.telemetry.offloading_enabled,
                        "stage_timings": resultado.telemetry.stage_timings,
                    },
                    "artefacto": {
                        "format": artefacto.format,
                        "sample_rate": artefacto.sample_rate,
                        "channels": artefacto.channels,
                        "duration_s": artefacto.duration_s,
                        "size_bytes": artefacto.size_bytes,
                        "path": artefacto.path,
                    },
                    "verificacion": verificacion,
                    "veredicto": "OK" if todo_ok else "FALLO",
                }
            )

            print(f"[etapas] total {t_gen_fin - t_gen_ini:.2f} s")
            print(_texto_etapas(ventanas))
            senal = verificacion.get("senal", {})
            cabecera = verificacion.get("cabecera", {})
            print(
                f"[fichero] {artefacto.path} — {verificacion.get('tamano_bytes')} B, "
                f"{cabecera.get('sample_rate')} Hz, {cabecera.get('canales')} canales, "
                f"{cabecera.get('duracion_real_s')} s "
                f"({cabecera.get('desviacion_pct')} % frente a lo pedido)"
            )
            print(
                f"[senal] RMS {senal.get('rms')} ({senal.get('rms_dbfs')} dBFS), "
                f"pico {senal.get('pico')} ({senal.get('pico_dbfs')} dBFS), "
                f"ceros {senal.get('muestras_a_cero_pct')} %, "
                f"correlacion L/R {senal.get('correlacion_canales')}"
            )
            for nombre, valor in bloqueantes.items():
                print(f"    [{'OK ' if valor else 'MAL'}] {nombre}")
            for nombre, valor in verificacion.get("indicadores", {}).items():
                print(f"    [{'ok ' if valor else '  !'}] {nombre} (informativo)")
            if not todo_ok:
                if args.seguir_tras_fallo:
                    # En la matriz A/B una celda mala no invalida las demas, y la
                    # carga (~643 s) ya esta pagada: se sigue y el codigo de
                    # salida se queda en 1.
                    print("[aviso] comprobaciones bloqueantes fallidas: se sigue con la matriz.")
                else:
                    print("[abortado] comprobaciones bloqueantes fallidas: no se sigue.")
                    break

    except BaseException as exc:  # noqa: BLE001  (el informe se escribe pase lo que pase)
        informe["fallo"] = {
            "tipo": type(exc).__name__,
            "mensaje": str(exc),
            "traceback": traceback.format_exc(),
        }
        codigo = 2
        traceback.print_exc()
    finally:
        muestreador.detener()
        if muestreador.error:
            informe["muestreo_vram"]["error"] = muestreador.error
        informe["muestreo_vram"]["vram_total_mb"] = muestreador.total_mb
        try:
            await adaptador.unload()
        except Exception as exc:  # noqa: BLE001
            informe.setdefault("avisos", []).append(f"unload() fallo: {exc!r}")
        logging.getLogger().removeHandler(escucha)
        informe["adapter"] = adaptador.describe()
        informe["procedencia_codigo"] = procedencia_modulos(raiz_app)
        if args.hash_pesos:
            ruta_pesos = Path(ctx.weights_dir) / args.fichero_pesos
            if ruta_pesos.is_file():
                informe["pesos_sha256"] = sha256_fichero(ruta_pesos)
        informe["codigo_salida"] = codigo
        destino = salida / f"{args.etiqueta}-informe.json"
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[informe] {destino}")
        print(f"[veredicto] codigo de salida {codigo}")
    return codigo


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genera audio real con el adapter de ACE-Step y verifica el WAV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--duraciones",
        default="30",
        help="Duraciones en segundos separadas por comas. Se ejecutan en orden y se para "
        "en la primera que falle (la corta primero, para cerrar el ciclo antes de "
        "gastar tiempo).",
    )
    parser.add_argument(
        "--matriz",
        default=None,
        help=(
            "Matriz A/B ejecutada tras UNA sola carga: celdas "
            "'etiqueta:duracion_s:semilla:si|no' separadas por comas, donde el ultimo "
            "campo es el planificador. Gana sobre --duraciones/--semilla/--sin-lm. "
            "Existe porque el arranque en frio son ~643 s: seis pistas en seis "
            "contenedores serian ~64 min de cargar seis veces el mismo artefacto. "
            "No contamina la comparacion (ver CasoAB)."
        ),
    )
    parser.add_argument(
        "--seguir-tras-fallo",
        action="store_true",
        dest="seguir_tras_fallo",
        help=(
            "No aborta la matriz cuando una celda falla sus comprobaciones "
            "bloqueantes. El codigo de salida sigue siendo 1."
        ),
    )
    parser.add_argument("--prompt", default=PROMPT_POR_DEFECTO, help="Prompt de estilo.")
    parser.add_argument("--letra", default=LETRA_POR_DEFECTO, help="Letra en castellano.")
    parser.add_argument(
        "--letra-fichero", default=None, help="Fichero UTF-8 con la letra (gana sobre --letra)."
    )
    parser.add_argument("--semilla", type=int, default=20260902, help="Semilla (trazabilidad).")
    parser.add_argument("--bpm", type=int, default=BPM_POR_DEFECTO,
                        help="Tempo en el bloque de metas. 0 lo omite (comportamiento anterior).")
    parser.add_argument("--tonalidad", default=TONALIDAD_POR_DEFECTO,
                        help='Tonalidad, p.ej. "A minor". Cadena vacia para omitirla.')
    parser.add_argument("--compas", default=COMPAS_POR_DEFECTO,
                        help='Compas, p.ej. "4/4". Cadena vacia para omitirlo.')
    parser.add_argument("--idioma-voz", default="es", dest="idioma_voz",
                        help="Idioma del canto (vocal_language).")
    parser.add_argument(
        "--sin-lm",
        action="store_true",
        dest="sin_lm",
        help=(
            "Desactiva el planificador de 5 Hz (usar_lm=False): `src_latents` vuelve a ser "
            "el latente de silencio. Es la rama de CONTROL del A/B. Ejecuta la misma orden "
            "dos veces, una con esta bandera y otra sin ella, manteniendo --semilla, "
            "--letra, --prompt, --bpm, --tonalidad y --compas, y cambiando solo --etiqueta."
        ),
    )
    parser.add_argument(
        "--lm-cfg", type=float, default=2.0, dest="lm_cfg",
        help=("Escala de CFG del planificador (defecto 2,0, el de upstream). 1,0 lo "
              "desactiva y divide por dos su coste: una pasada por codigo en vez de dos."),
    )
    parser.add_argument(
        "--lm-temperatura", type=float, default=0.85, dest="lm_temperatura",
        help="Temperatura de muestreo del planificador (defecto 0,85, el de upstream).",
    )
    parser.add_argument("--salida", default=os.environ.get("ACE_STEP_OUTPUT_DIR", "/outputs"))
    parser.add_argument("--pesos", default=None, help="Directorio de pesos (por defecto, entorno).")
    parser.add_argument(
        "--fichero-pesos",
        default=os.environ.get("ACE_STEP_WEIGHTS_FILE", "ace_step_1_5.safetensors"),
    )
    parser.add_argument("--dispositivo", default=None, help="Por defecto, ACE_STEP_DEVICE.")
    parser.add_argument("--dtype", default=None, help="Por defecto, ACE_STEP_DTYPE.")
    parser.add_argument(
        # Sube de 600 a 1800 el 2026-09-02, y no es un aflojamiento gratuito.
        # D-17 cuenta la CARGA dentro del presupuesto (`gpu_previo`), y el
        # arranque en frio del artefacto con planificador son 614,1 s MEDIDOS
        # (vram_load 571,4 + warm-up 42,7, este ultimo con el planificador ya
        # dentro): con 600 el trabajo se abortaba ANTES de generar nada, con el
        # mensaje correcto pero inutilizando el spike. Los 600 estaban calibrados
        # contra el artefacto anterior (394-463 s). El techo sigue existiendo y
        # sigue siendo un techo: 1800 deja sitio a una pista larga tras un
        # arranque en frio y aborta igual si algo se queda colgado.
        "--max-gpu-seconds", type=int, default=1800,
        help=("Techo de D-17 en segundos, CARGA INCLUIDA. Arranque en frio medido con "
              "el artefacto con planificador: 614 s."),
    )
    parser.add_argument("--periodo-muestreo", type=float, default=PERIODO_MUESTREO_S)
    parser.add_argument("--etiqueta", default="t03-smoke", help="Prefijo de los ficheros.")
    parser.add_argument("--raiz-app", default=None, help="Raiz del runner (por defecto /app).")
    parser.add_argument(
        "--hash-pesos",
        action="store_true",
        help="Calcula el SHA-256 de los pesos al terminar (recorre ~6 GB).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        stream=sys.stdout,
    )
    args = construir_parser().parse_args(argv)
    args.duraciones = [int(v) for v in str(args.duraciones).split(",") if v.strip()]
    if not args.duraciones:
        raise SystemExit("--duraciones vacio.")
    if args.letra_fichero:
        args.letra = Path(args.letra_fichero).read_text(encoding="utf-8")
    return asyncio.run(ejecutar(args))


if __name__ == "__main__":
    raise SystemExit(main())
