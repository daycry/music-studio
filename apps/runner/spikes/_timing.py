"""Medicion por etapas, VRAM y estadisticas — utilidades comunes de los spikes.

Modulo compartido por los tres spikes de la Fase 0: `T-03` (tiempos de
inferencia, perfil de VRAM y arranque en frio), `T-04` (dos inferencias
concurrentes) y `T-05` (contenerizacion minima de ACE-Step 1.5).

Reglas de diseno
----------------
* **Todo el camino mock funciona con la biblioteca estandar.** `torch` no esta
  instalado en la maquina de desarrollo y `nvidia-smi` no existe ahi, asi que
  todos los imports de acelerador son **perezosos** (dentro de la funcion que
  los necesita) y toda funcion que consulte la GPU devuelve `None` en lugar de
  reventar. Esto es lo que permite verificar los spikes de principio a fin sin
  GPU, con `--mock`.
* **Nada de numpy.** El agregador de estadisticas usa `statistics` y `math`, que
  son estandar. numpy es dependencia del monorepo (`T-10`), detras del gate G1.
* Los umbrales de VRAM son los de D-06 / `spec.md` §11.1: **8 GB es el suelo con
  offloading** (mas lento), **24 GB la cifra de confort** (RTX 4090/5090), y la
  referencia cloud es la L40S de 48 GB. El suelo se compara con una **banda de
  tolerancia** de `VRAM_FLOOR_TOLERANCE_MB` porque la VRAM que reporta el driver
  no es la VRAM del envase: ver la nota de `VRAM_FLOOR_TOLERANCE_MB` (CS-51).

Aviso sobre lo que mide `StageTimer`
-----------------------------------
`StageTimer` mide **reloj real** (`time.perf_counter`). En modo `--mock` los
tiempos que interesan son los **simulados** por el adapter mock, que llegan en
`RunTelemetry.stage_timings`; el reloj real ahi es de milisegundos y no dice
nada. Un informe de spike en modo mock debe etiquetar la fuente de los tiempos
(`"mock"` frente a `"gpu"`) para que nadie confunda una simulacion con una
medicion — los valores de `T-03` recalibran el §6 de `evaluation.md`.
"""

from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from types import TracebackType
from typing import Any, Sequence

__all__ = [
    "STAGES",
    "COLD_START_STAGES",
    "GPU_STAGES",
    "VRAM_FLOOR_MB",
    "VRAM_FLOOR_TOLERANCE_MB",
    "VRAM_COMFORT_MB",
    "VRAM_REFERENCE_L40S_MB",
    "NOT_VIABLE_PREFIX",
    "StageTimer",
    "Stats",
    "summarize",
    "vram_snapshot_mb",
    "gpu_info",
    "decide_offloading",
    "write_json_report",
]


# --------------------------------------------------------------------------- #
# Etapas canonicas
# --------------------------------------------------------------------------- #

#: Etapas del arranque en frio y de la ejecucion, en el orden en que ocurren.
#: Son literalmente las seis que `T-03` exige instrumentar: scheduling, pull de
#: imagen, descarga de pesos, carga a VRAM, warm-up e inferencia.
STAGES: tuple[str, ...] = (
    "scheduling",         # el proveedor asigna la maquina (RunPod); ~0 en GPU local
    "image_pull",         # descarga de la imagen de contenedor; termino dominante (S-01b)
    "weights_download",   # descarga de los pesos safetensors a la cache del host
    "vram_load",          # carga de pesos a VRAM (se alarga con offloading)
    "warmup",             # primera pasada en vacio, compilacion de kernels
    "inference",          # generacion propiamente dicha
)

#: Subconjunto que compone el **arranque en frio** (S-01: 2-6 min con imagen
#: cacheada, 5-12 min sin cachear). `inference` queda fuera a proposito: el
#: arranque en frio es lo que se paga *antes* de generar.
COLD_START_STAGES: tuple[str, ...] = (
    "scheduling",
    "image_pull",
    "weights_download",
    "vram_load",
    "warmup",
)

#: Etapas en las que el trabajo **retiene la GPU** y por tanto cuentan para el
#: presupuesto de D-17. `scheduling`, `image_pull` y `weights_download` consumen
#: reloj (y el pod se factura), pero no son computo de GPU del trabajo. Ojo al
#: contrato M-3: `RunTelemetry.gpu_seconds` de una generacion cubre SOLO
#: `inference`; `vram_load` y `warmup` se pagan una vez por carga y el adapter
#: los reporta aparte (`load_gpu_seconds` / `load_stage_timings_s`).
GPU_STAGES: tuple[str, ...] = ("vram_load", "warmup", "inference")


# --------------------------------------------------------------------------- #
# Umbrales de VRAM (D-06, spec.md §11.1)
# --------------------------------------------------------------------------- #

#: Suelo nominal de D-06 / `spec.md` §11.1: **8 GB**. Es la cifra *de catalogo*
#: —la que trae escrita la caja de la tarjeta—, no la que reporta el driver. Su
#: valor NO se toca: hay dos consumidores que dependen de esta semantica exacta
#: (`vram_profile.py` lo usa como techo de PICO en `fits_floor_8gb`, y `_mock.py`
#: lo usa como VRAM total simulada); cambiar el numero les cambiaria el
#: significado por debajo. La correccion del suelo se hace con la tolerancia de
#: abajo, no aqui.
VRAM_FLOOR_MB = 8 * 1024

#: Banda de tolerancia del suelo, en MB. **Este es el arreglo de CS-51.**
#:
#: El problema, medido y reproducido (pre-dev-checklist.md §A, item 7-ter):
#: `torch.cuda.get_device_properties().total_memory` NO informa de la VRAM
#: nominal de la tarjeta, sino de la memoria **utilizable** tras la reserva del
#: driver, y ademas `vram_snapshot_mb()` / `gpu_info()` la truncan con division
#: entera a MB. En la GTX 1070 de la maquina local:
#:
#:   * `cuDeviceTotalMem_v2` = 8.589.672.448 B = **8191,75 MiB** -> truncado a
#:     **8191** MB (frente a los 8192 MB del envase: faltan 294.912 B).
#:   * `nvidia-smi` sobre la misma tarjeta: `Total` 8192 MiB, **`Reserved` 132
#:     MiB**, libre ~6988 MiB con el escritorio de Windows arrancado.
#:
#: Es decir: **cualquier** tarjeta vendida como 8 GB reporta 8191 MB o menos, y
#: con la comparacion estricta contra 8192 el suelo rechazaba por construccion
#: exactamente la clase de tarjeta que D-06 queria admitir. Un off-by-one de 1
#: MiB dejaba `decide_offloading()` devolviendo NO VIABLE y `adapter._load_sync()`
#: abortando antes de tocar los pesos.
#:
#: Por que 64 MiB y no un numero magico: la intencion de D-06 es *"una tarjeta de
#: 8 GB debe pasar"*. 64 MiB cubre con holgura el truncamiento (< 1 MiB) y la
#: reserva del driver observada (132 MiB de `Reserved` ya estan *fuera* de
#: `total_memory`; el margen es para variaciones de driver/plataforma), y no abre
#: la puerta a ninguna otra clase de tarjeta: el siguiente escalon comercial por
#: debajo son 6 GB, y 6144 + 64 = 6208 sigue muy por debajo de 8192. La banda es
#: una correccion de unidad de medida, no una rampa hacia abajo.
#:
#: !!! AVISO DE ALCANCE — REQUIERE RATIFICACION DEL PROPIETARIO !!!
#: Aunque `VRAM_FLOOR_MB` no cambia de valor, el suelo **efectivo** pasa de 8192
#: a 8128 MB, y 8192 es un numero **aprobado en la spec** (D-06 / `spec.md`
#: §11.1, reforzado por D-29). Esto es la modificacion de un umbral de spec:
#: necesita el visto bueno explicito del propietario y una linea en `spec.md`.
#: Esta registrado como **CS-51** (item 7-ter) en `pre-dev-checklist.md`, que ya
#: lo marca como "decision sobre un umbral de la spec, no un parche". Mientras no
#: este ratificado, este codigo desbloquea la Fase 0 en la maquina local pero la
#: cifra sigue siendo provisional.
#:
#: ARRASTRE CONOCIDO, anotado como seguimiento y NO corregido aqui por alcance:
#: hay dos sitios que imprimen "Minimo exigido: {VRAM_FLOOR_MB} MB" y a partir de
#: este cambio diran 8192 cuando el minimo aplicado es 8128 —
#: `capability_probe.py` (resumen del probe) y `adapters/ace_step/adapter.py` (el
#: RuntimeError de arranque). En el segundo el operador ve igualmente la cifra
#: correcta, porque el `motivo` que devuelve esta funcion se imprime delante.
VRAM_FLOOR_TOLERANCE_MB = 64

#: Cifra de confort para canciones completas (RTX 4090 / 5090).
VRAM_COMFORT_MB = 24 * 1024
#: Referencia cloud del plan (RunPod L40S), a efectos de comparar mediciones.
VRAM_REFERENCE_L40S_MB = 48 * 1024

#: Prefijo con el que `decide_offloading()` marca una configuracion **no
#: ejecutable**. El llamante debe abortar con mensaje claro, nunca en silencio
#: (`spec.md` §6, fila de GPU local sin VRAM suficiente).
NOT_VIABLE_PREFIX = "NO VIABLE"


# --------------------------------------------------------------------------- #
# Temporizacion por etapas
# --------------------------------------------------------------------------- #

class _StageScope:
    """Gestor de contexto interno de una sola etapa. Lo crea `StageTimer.stage()`."""

    __slots__ = ("_timer", "_stage", "_t0")

    def __init__(self, timer: StageTimer, stage: str) -> None:
        self._timer = timer
        self._stage = stage
        self._t0 = 0.0

    def __enter__(self) -> _StageScope:
        self._t0 = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        # Se contabiliza tambien cuando la etapa falla: un arranque en frio que
        # revienta a los 4 min ha consumido esos 4 min y el informe debe verlos.
        self._timer.add(self._stage, perf_counter() - self._t0)
        return False  # nunca se traga la excepcion


class StageTimer:
    """Acumulador de segundos por etapa, usable como gestor de contexto.

    Uso tipico en un spike::

        with StageTimer() as timer:
            with timer.stage("weights_download"):
                descargar_pesos()
            with timer.stage("vram_load"):
                cargar_a_vram()
            for _ in range(10):
                with timer.stage("inference"):   # se acumula, no se sobrescribe
                    generar()
        print(timer.timings, timer.wall_s)

    Entrar en el propio `StageTimer` es opcional y solo sirve para medir el
    **reloj total** del bloque (`wall_s`), que puede ser mayor que la suma de
    etapas: la diferencia es tiempo no instrumentado, y verlo es util.

    Args:
        strict_stages: si es `True` (por defecto) rechaza nombres de etapa que no
            esten en `STAGES`, para que las claves del informe sean comparables
            entre ejecuciones y entre maquinas. Ponlo en `False` solo para
            mediciones exploratorias.
    """

    __slots__ = ("_strict", "_acc", "_counts", "_t0", "wall_s")

    def __init__(self, *, strict_stages: bool = True) -> None:
        self._strict = strict_stages
        self._acc: dict[str, float] = {}
        self._counts: dict[str, int] = {}
        self._t0: float | None = None
        #: Reloj total del bloque `with`, o 0.0 si no se uso como contexto.
        self.wall_s: float = 0.0

    # -- contexto global (opcional) ----------------------------------------- #

    def __enter__(self) -> StageTimer:
        self._t0 = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if self._t0 is not None:
            self.wall_s = perf_counter() - self._t0
        return False

    # -- API ---------------------------------------------------------------- #

    def stage(self, name: str) -> _StageScope:
        """Devuelve el gestor de contexto que cronometra la etapa `name`."""
        self._check(name)
        return _StageScope(self, name)

    def add(self, name: str, seconds: float) -> None:
        """Suma `seconds` a una etapa sin cronometrarla.

        Es la via por la que un spike incorpora tiempos medidos **fuera** del
        proceso (el `scheduling` y el `image_pull` de RunPod, que ocurren antes
        de que exista este proceso) o simulados por el adapter mock.
        """
        self._check(name)
        if seconds < 0:
            raise ValueError(f"Tiempo negativo para la etapa {name!r}: {seconds}.")
        self._acc[name] = self._acc.get(name, 0.0) + float(seconds)
        self._counts[name] = self._counts.get(name, 0) + 1

    def merge(self, timings: dict[str, float]) -> None:
        """Incorpora un diccionario de etapa -> segundos (p. ej. de `RunTelemetry`)."""
        for name, seconds in timings.items():
            self.add(name, seconds)

    @property
    def timings(self) -> dict[str, float]:
        """Copia de los acumulados, ordenada segun `STAGES` (extras al final)."""
        conocidas = [s for s in STAGES if s in self._acc]
        extras = sorted(k for k in self._acc if k not in STAGES)
        return {name: self._acc[name] for name in (*conocidas, *extras)}

    @property
    def counts(self) -> dict[str, int]:
        """Numero de veces que se ha cronometrado cada etapa."""
        return dict(self._counts)

    def total_s(self, stages: Sequence[str] | None = None) -> float:
        """Suma de segundos de las etapas indicadas (por defecto, todas).

        Con `stages=COLD_START_STAGES` da el arranque en frio; con
        `stages=GPU_STAGES`, los segundos de GPU que cuentan para D-17.
        """
        claves = self._acc.keys() if stages is None else stages
        return sum(self._acc.get(name, 0.0) for name in claves)

    def as_report(self) -> dict[str, Any]:
        """Bloque listo para volcar en el informe JSON del spike."""
        return {
            "stage_timings_s": {k: round(v, 3) for k, v in self.timings.items()},
            "stage_counts": self.counts,
            "cold_start_s": round(self.total_s(COLD_START_STAGES), 3),
            "gpu_seconds": round(self.total_s(GPU_STAGES), 3),
            "total_measured_s": round(self.total_s(), 3),
            "wall_s": round(self.wall_s, 3),
        }

    def _check(self, name: str) -> None:
        if self._strict and name not in STAGES:
            raise ValueError(
                f"Etapa desconocida: {name!r}. Las etapas canonicas de T-03 son "
                f"{', '.join(STAGES)}. Usa StageTimer(strict_stages=False) para "
                "mediciones exploratorias."
            )


# --------------------------------------------------------------------------- #
# Consulta de GPU (imports perezosos, nunca revientan)
# --------------------------------------------------------------------------- #

def _torch_cuda() -> Any | None:
    """Devuelve el modulo `torch` si esta importable y con CUDA disponible.

    Import **perezoso** y defensivo: en la maquina de desarrollo no hay torch, y
    en un contenedor mal construido torch puede existir sin CUDA utilizable.
    Cualquier fallo devuelve `None`.
    """
    try:
        import torch  # noqa: PLC0415  (perezoso a proposito: no hay GPU en desarrollo)
    except Exception:
        return None
    try:
        if not torch.cuda.is_available():
            return None
    except Exception:
        return None
    return torch


def vram_snapshot_mb(device: int = 0) -> tuple[int, int, int] | None:
    """Devuelve `(total_mb, used_mb, peak_mb)` de la GPU, o `None` si no hay CUDA.

    * `total_mb`: VRAM total del dispositivo.
    * `used_mb`: memoria reservada ahora por el proceso (`memory_reserved`, que es
      lo que el proceso le ha quitado al sistema, no solo lo que tiene ocupado
      con tensores).
    * `peak_mb`: pico historico reservado desde el ultimo
      `torch.cuda.reset_peak_memory_stats()`. Es la cifra que `T-03` compara
      contra el suelo de 8 GB y el confort de 24 GB.

    Las tres son del **proceso actual**: no ve el consumo de un segundo proceso
    de inferencia. Para `T-04` (dos inferencias concurrentes) el pico simultaneo
    hay que leerlo del sistema (`nvidia-smi --query-gpu=memory.used`), no de aqui.

    Nunca lanza excepcion: sin torch, sin CUDA o con un dispositivo invalido
    devuelve `None`.
    """
    torch = _torch_cuda()
    if torch is None:
        return None
    try:
        total = int(torch.cuda.get_device_properties(device).total_memory) // (1024 * 1024)
        used = int(torch.cuda.memory_reserved(device)) // (1024 * 1024)
        peak = int(torch.cuda.max_memory_reserved(device)) // (1024 * 1024)
    except Exception:
        return None
    return (total, used, peak)


def gpu_info(device: int = 0) -> dict[str, Any] | None:
    """Nombre de la GPU y VRAM total, o `None` si no hay CUDA disponible.

    Incluye `device_count` porque `T-04` necesita saber si la maquina tiene una o
    varias GPU antes de interpretar una medicion de concurrencia.
    """
    torch = _torch_cuda()
    if torch is None:
        return None
    try:
        props = torch.cuda.get_device_properties(device)
        return {
            "name": str(props.name),
            "vram_total_mb": int(props.total_memory) // (1024 * 1024),
            "device_count": int(torch.cuda.device_count()),
        }
    except Exception:
        return None


def decide_offloading(vram_total_mb: int | None) -> tuple[bool, str]:
    """Decide si activar offloading de pesos y explica por que.

    Aplica los umbrales de D-06 / `spec.md` §11.1: **24 GB de confort**, **8 GB
    de suelo**, este ultimo con la **banda de tolerancia** de
    `VRAM_FLOOR_TOLERANCE_MB`.

    La banda existe porque el argumento que llega aqui es la VRAM que **reporta
    el driver** (`total_memory`, truncada a MB), no la VRAM nominal de la
    tarjeta: una 8 GB reporta 8191 MB o menos. La comparacion real es, por tanto,
    `vram_total_mb + VRAM_FLOOR_TOLERANCE_MB < VRAM_FLOOR_MB`, lo que equivale a
    un **suelo efectivo de 8128 MB**. Ver la nota larga de
    `VRAM_FLOOR_TOLERANCE_MB` (CS-51) para la evidencia medida y para el aviso de
    que ese suelo efectivo necesita ratificacion del propietario.

    Devuelve `(offload, motivo)`:
    * `>= 24 GB` -> `(False, ...)`: cabe entero, sin degradacion.
    * `8128 MB <= VRAM < 24 GB` -> `(True, ...)`: offloading automatico y **aviso
      explicito de tiempos degradados** (D-29). S-02 (150 s por pista) se mide en
      GPU de >= 24 GB; con offloading sube de forma material. Aqui caen tanto una
      8 GB real (8191 MB reportados) como el suelo nominal exacto (8192).
    * `< 8128 MB` -> `(True, "NO VIABLE: ...")`: el motivo empieza por
      `NOT_VIABLE_PREFIX` y el llamante **debe abortar** con mensaje claro
      —VRAM detectada y minimo exigido—, ofreciendo enviar el trabajo a
      `GPU_PROVIDER=runpod` si esta configurado (`spec.md` §6). El `True` que se
      devuelve es solo el valor conservador; no significa que se pueda ejecutar.
    * `None` (VRAM desconocida: sin torch, sin CUDA o deteccion fallida) ->
      `(True, ...)`: conservador. Es el caso de la maquina de desarrollo, donde
      solo se ejecuta el modo `--mock`.
    """
    if vram_total_mb is None:
        return (
            True,
            "VRAM desconocida (sin torch/CUDA o deteccion fallida): se asume "
            "offloading por prudencia. En este estado solo es valido el modo "
            "--mock; una medicion real necesita GPU detectada.",
        )
    # Comparacion CON tolerancia (CS-51): el argumento es VRAM reportada por el
    # driver, no VRAM de catalogo. Sin el sumando, una 8 GB de verdad —que
    # reporta 8191— caia en esta rama y abortaba la carga por 1 MiB.
    #
    # El texto del motivo corrige ademas dos afirmaciones que la version anterior
    # daba por buenas y que las mediciones de las cabeceras upstream han
    # desmentido: (a) el modelo no son "3,5B" parametros —el checkpoint de
    # ACE-Step tiene 2,394 G y el conjunto con text encoder y VAE, 3,158 G—, y
    # (b) no es cierto que "no arranca ni con offloading": el offloading no llega
    # ni a evaluarse, porque `load_file()` deposita el artefacto entero en VRAM
    # antes de que exista el pipeline que decidiria offloadear.
    if vram_total_mb + VRAM_FLOOR_TOLERANCE_MB < VRAM_FLOOR_MB:
        return (
            True,
            f"{NOT_VIABLE_PREFIX}: {vram_total_mb} MB de VRAM por debajo del suelo "
            f"efectivo de {VRAM_FLOOR_MB - VRAM_FLOOR_TOLERANCE_MB} MB (suelo "
            f"nominal {VRAM_FLOOR_MB} MB de D-06, menos {VRAM_FLOOR_TOLERANCE_MB} MB "
            "de tolerancia por la reserva del driver y el truncamiento a MB). "
            "Con esta VRAM no hay offloading que valga: el artefacto fusionado de "
            "ACE-Step 1.5 en fp16 son ~5.878 MiB que `load_file()` deposita en VRAM "
            "ANTES de construir el pipeline, y es el pipeline quien decide el "
            "offloading. (Parametros reales: 2,394 G en el checkpoint de ACE-Step; "
            "3,158 G contando el text encoder Qwen3-Embedding-0.6B y el VAE Oobleck.) "
            "Abortar con mensaje claro indicando VRAM detectada y minimo exigido; si "
            "hay proveedor cloud configurado (GPU_PROVIDER=runpod), ofrecer enviar el "
            "trabajo alli.",
        )
    if vram_total_mb < VRAM_COMFORT_MB:
        return (
            True,
            f"{vram_total_mb} MB de VRAM: por encima del suelo efectivo de "
            f"{VRAM_FLOOR_MB - VRAM_FLOOR_TOLERANCE_MB} MB (nominal {VRAM_FLOOR_MB} MB, "
            f"D-06) pero por debajo del confort de {VRAM_COMFORT_MB} MB (24 GB, D-06). "
            "Offloading automatico activado: la generacion funciona con TIEMPOS "
            "DEGRADADOS respecto a S-02 (150 s/pista medidos en >= 24 GB). "
            "Documentar la degradacion medida en el informe de T-03.",
        )
    return (
        False,
        f"{vram_total_mb} MB de VRAM: alcanza la cifra de confort de "
        f"{VRAM_COMFORT_MB} MB (24 GB, D-06). Sin offloading; los tiempos son "
        "comparables con la linea base de S-02.",
    )


# --------------------------------------------------------------------------- #
# Estadisticas sin numpy
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class Stats:
    """Resumen estadistico de una serie de medidas (segundos, MB, lo que sea)."""

    n: int
    mean: float
    median: float
    p95: float
    min: float
    max: float

    def as_dict(self, ndigits: int = 3) -> dict[str, Any]:
        """Version redondeada y serializable para el informe JSON."""
        return {
            "n": self.n,
            "mean": round(self.mean, ndigits),
            "median": round(self.median, ndigits),
            "p95": round(self.p95, ndigits),
            "min": round(self.min, ndigits),
            "max": round(self.max, ndigits),
        }


def _percentile(ordenados: list[float], q: float) -> float:
    """Percentil `q` (0..1) por interpolacion lineal sobre una lista ya ordenada.

    Metodo de rango lineal, el mismo que usa `numpy.percentile` por defecto, para
    que las cifras del spike sean comparables con cualquier reanalisis posterior.
    Con 10 muestras (las 10 inferencias que pide `T-03`) el p95 interpola entre
    las dos ultimas: conviene decirlo en el informe en lugar de presentarlo como
    un p95 robusto.
    """
    if len(ordenados) == 1:
        return ordenados[0]
    pos = (len(ordenados) - 1) * q
    bajo = math.floor(pos)
    alto = math.ceil(pos)
    if bajo == alto:
        return ordenados[bajo]
    return ordenados[bajo] + (ordenados[alto] - ordenados[bajo]) * (pos - bajo)


def summarize(values: Sequence[float], *, percentile: float = 0.95) -> Stats:
    """Media, mediana, p95, minimo y maximo de `values`, sin numpy.

    Args:
        values: serie de medidas. No puede estar vacia.
        percentile: percentil alto a calcular, en 0..1 (por defecto 0,95).

    Levanta:
        ValueError: si `values` esta vacia o `percentile` esta fuera de 0..1.
            Una serie vacia es un fallo del spike (no se midio nada), no un
            resultado: devolver ceros lo enmascararia en el informe.
    """
    if not values:
        raise ValueError("summarize() necesita al menos una medida; la serie esta vacia.")
    if not 0.0 <= percentile <= 1.0:
        raise ValueError(f"percentile debe estar en 0..1; recibido {percentile}.")
    datos = sorted(float(v) for v in values)
    return Stats(
        n=len(datos),
        mean=statistics.fmean(datos),
        median=statistics.median(datos),
        p95=_percentile(datos, percentile),
        min=datos[0],
        max=datos[-1],
    )


# --------------------------------------------------------------------------- #
# Informes
# --------------------------------------------------------------------------- #

def write_json_report(path: str | Path, payload: dict[str, Any]) -> Path:
    """Escribe `payload` como JSON indentado en `path` y devuelve la ruta.

    Crea los directorios que falten, escribe en **UTF-8** con `ensure_ascii=False`
    (los informes van en castellano y llevan acentos) y termina en salto de
    linea. No sobrescribe con silencio: si `path` existe, se reemplaza —el
    llamante es quien decide el nombre, y los informes de spike se versionan por
    escenario y fecha, no por acumulacion.

    No serializa objetos arbitrarios a proposito: si el payload lleva algo que no
    es JSON nativo, `TypeError` es la respuesta correcta. Convierte antes
    (`Stats.as_dict()`, `StageTimer.as_report()`).

    La escritura es **atomica**: se serializa primero (un `TypeError` no toca el
    fichero existente), se vuelca a un temporal en el **mismo directorio** y se
    renombra con `os.replace()`. Un proceso que muera a mitad de escritura no
    puede dejar un informe truncado con nombre valido.
    """
    destino = Path(path)
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)
    temporal = destino.with_name(f"{destino.name}.tmp-{os.getpid()}")
    try:
        temporal.write_text(texto + "\n", encoding="utf-8")
        os.replace(temporal, destino)
    finally:
        # Si el replace no llego a ejecutarse, no se deja basura junto al informe.
        temporal.unlink(missing_ok=True)
    return destino
