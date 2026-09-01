#!/usr/bin/env python3
"""Arnes de medicion de T-03 — tiempos de inferencia, perfil de VRAM y arranque en frio.

Tarea
-----
`T-03` (F2, Fase 0 — spikes de viabilidad). Cierra S-01, S-02 e I-07 de
`spec.md` §11. Este fichero es **el arnes**: instrumenta, mide, agrega y emite el
informe. **Los numeros los rellena la ejecucion, no el codigo**; la plantilla de
resultados es `apps/runner/spikes/inference_timing.md` (otro entregable).

Criterios de aceptacion de T-03 que este script habilita
--------------------------------------------------------
1. Tiempo de inferencia por pista en GPU de >= 24 GB (referencia S-02: 150 s
   totales, ~90 s de inferencia pura).
2. VRAM pico **con y sin offloading**, contra el suelo de 8 GB y el confort de
   24 GB (`spec.md` §11.1, D-06).
3. Arranque en frio con imagen cacheada (2-6 min esperado) y sin cachear (5-12 min).
4. Instrumentacion por etapas: `scheduling`, `image_pull`, `weights_download`,
   `vram_load`, `warmup`, `inference` (las seis de `_timing.STAGES`).
5. 10 inferencias con offloading y 10 sin offloading, con el VRAM pico de cada una.
6. Factor de conversion entre la GPU local usada y la L40S objetivo, si difieren.

Lo que este script NO puede medir, y por que
--------------------------------------------
`scheduling` e `image_pull` **no son medibles desde dentro del proceso en GPU
local**: el primero lo consume el proveedor asignando maquina y el segundo el
`docker pull` del host, ambos antes de que este proceso exista. Solo son reales
contra el **pod de RunPod** (unico consumo de GPU cloud autorizado de T-03,
decision del 2026-08-18). El informe JSON los emite como `null` **con motivo**;
no se inventan. Si el adapter reporta un valor para esas etapas, se conserva
aparte (`adapter_reported_s`) y marcado, nunca como medicion del arnes.

En modo `--mock` **nada de lo que sale de aqui es una medicion**: el adapter mock
simula tiempos deterministas y la cabecera del informe lleva
`adapter.source == "mock"` con su aviso. El modo mock existe para verificar el
arnes en una maquina sin GPU (aqui `nvidia-smi` no existe y `torch` no esta
instalado), no para rellenar T-03.

Invariantes respetados
----------------------
* **D-14**: la ruta de pesos la valida el adapter con `assert_safetensors()`.
  Este script no abre ningun checkpoint.
* **D-15**: `RunnerContext` no transporta credenciales y aqui no se lee ni se
  escribe ningun secreto. `--weights-dir` es una **ruta**, no una credencial.
* **D-17**: cada run lleva `max_gpu_seconds` y el arnes **revalida** los
  `gpu_seconds` reportados con `assert_within_gpu_budget()`; un run que agote el
  presupuesto se registra como abortado y no contamina las estadisticas.
* Imports de acelerador **perezosos** (dentro de la funcion). El camino `--mock`
  usa solo la biblioteca estandar.
* La semilla se registra por trazabilidad; **no** garantiza salida identica
  (driver, cuDNN, kernels de atencion, orden de reduccion en coma flotante). Este
  arnes nunca compara audio.

Ejecucion
---------
Verificacion del arnes sin GPU (lo que se puede correr en la maquina de desarrollo)::

    python apps/runner/spikes/vram_profile.py --mock --runs 2 --both

Medicion real de T-03 en GPU local (necesita el adapter de T-05)::

    python apps/runner/spikes/vram_profile.py --runs 10 --both \
        --gpu-label "RTX 4090" --weights-dir /workspace/weights

Solo un escenario, saltando el arranque en frio::

    python apps/runner/spikes/vram_profile.py --runs 10 --no-offload --skip-cold-start

Codigos de salida
-----------------
* `0` — ejecucion completa (o completa con avisos).
* `1` — error de configuracion o de entorno (adapter real ausente, VRAM por
  debajo del suelo de 8 GB, argumentos invalidos).
* `2` — no se obtuvo ninguna medicion usable en ningun escenario.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Sequence

# Los spikes se ejecutan como scripts sueltos, sin paquete instalable (el
# empaquetado del monorepo es T-10, detras del gate G1): se anade
# `apps/runner/` y `apps/runner/spikes/` a sys.path de forma robusta al cwd.
_SPIKES_DIR = os.path.dirname(os.path.abspath(__file__))
_RUNNER_ROOT = os.path.dirname(_SPIKES_DIR)
for _ruta in (_RUNNER_ROOT, _SPIKES_DIR):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import _timing  # noqa: E402  (tras el arranque de sys.path)
from _mock import MockMusicModelAdapter, make_request  # noqa: E402
from contracts import (  # noqa: E402
    GenerationRequest,
    GpuBudgetExceeded,
    MusicModelAdapter,
    RunnerContext,
    assert_within_gpu_budget,
)

TASK = "T-03"
SPIKE = "vram_profile"

#: Nombres de escenario del informe. Son claves estables: el documento de
#: resultados y cualquier reanalisis posterior las citan.
SCENARIO_NO_OFFLOAD = "no_offload"
SCENARIO_OFFLOAD = "offload"

#: Referencia S-02 de `spec.md` §11 — **hipotesis de la spec, no medicion**.
S02_TOTAL_S = 150.0
S02_INFERENCE_S = 90.0

#: Rangos esperados de arranque en frio (S-01 / S-01b). Igual: expectativa, no dato.
S01_RANGE_IMAGE_CACHED_S = (120.0, 360.0)
S01_RANGE_IMAGE_NOT_CACHED_S = (300.0, 720.0)

#: Etapas que este arnes NO puede medir en GPU local (ver docstring del modulo).
STAGES_ONLY_RUNPOD = ("scheduling", "image_pull")
REASON_ONLY_RUNPOD = (
    "No medible desde este proceso en GPU local: 'scheduling' lo consume el "
    "proveedor asignando maquina y 'image_pull' el docker pull del host, ambos "
    "antes de que exista este proceso. Solo es real contra el pod de RunPod "
    "(unico consumo de GPU cloud autorizado de T-03, decision 2026-08-18)."
)

#: Duracion de la pista de sonda que cierra cada escenario de arranque en frio.
#: Corta a proposito: el objeto de la medicion es el arranque, no la pista.
COLD_START_PROBE_DURATION_S = 30

#: Ruta relativa del adapter real que crea T-05 (contenerizacion minima).
REAL_ADAPTER_REL_PATH = os.path.join("adapters", "ace_step", "adapter.py")
REAL_ADAPTER_CLASS = "AceStepAdapter"

EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_NO_MEASUREMENT = 2


class SpikeError(RuntimeError):
    """Error de configuracion o de entorno del spike, con mensaje para el operador."""


# --------------------------------------------------------------------------- #
# Utilidades de entorno (todo import de acelerador es perezoso)
# --------------------------------------------------------------------------- #

def _utc_now_iso() -> str:
    """Marca de tiempo UTC en ISO-8601 con segundos."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _nvidia_smi(query: str) -> str | None:
    """Primera linea de `nvidia-smi --query-gpu=<query>`, o `None` si no se puede.

    Defensiva a proposito: en la maquina de desarrollo `nvidia-smi` no existe y
    eso **no es un fallo del spike**, es el motivo por el que existe `--mock`.
    """
    try:
        proceso = subprocess.run(
            [
                "nvidia-smi",
                f"--query-gpu={query}",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    if proceso.returncode != 0:
        return None
    primera = proceso.stdout.strip().splitlines()
    return primera[0].strip() if primera else None


def _driver_info() -> dict[str, Any]:
    """Version de driver y nombre de GPU segun `nvidia-smi`, o nulos con motivo."""
    driver = _nvidia_smi("driver_version")
    if driver is None:
        return {
            "driver_version": None,
            "gpu_name_smi": None,
            "reason": (
                "nvidia-smi no disponible en esta maquina. Sin GPU no hay medicion "
                "valida de T-03: solo el modo --mock."
            ),
        }
    return {"driver_version": driver, "gpu_name_smi": _nvidia_smi("name"), "reason": None}


def _torch_info() -> dict[str, Any]:
    """Estado de torch/CUDA con **import perezoso**; nunca lanza."""
    info: dict[str, Any] = {
        "installed": False,
        "version": None,
        "cuda_version": None,
        "cuda_available": None,
        "reason": None,
    }
    try:
        import torch  # noqa: PLC0415  (perezoso: no hay torch en desarrollo)
    except Exception as exc:
        info["reason"] = (
            f"torch no importable ({type(exc).__name__}). Esperado en la maquina de "
            "desarrollo: el camino --mock usa solo biblioteca estandar."
        )
        return info
    info["installed"] = True
    try:
        info["version"] = str(torch.__version__)
        info["cuda_version"] = str(getattr(torch.version, "cuda", None))
        info["cuda_available"] = bool(torch.cuda.is_available())
    except Exception as exc:  # torch presente pero roto: dato, no excepcion
        info["reason"] = f"torch importable pero la consulta fallo: {type(exc).__name__}."
    return info


def _reset_peak_vram(device: int = 0) -> bool:
    """Reinicia el pico de VRAM del proceso (`torch.cuda`), si se puede.

    Import perezoso y defensivo. Devuelve `True` solo si el reinicio se ejecuto:
    sin eso, el pico de un run arrastraria el del anterior y las 10 mediciones de
    VRAM del criterio 5 no serian independientes.
    """
    try:
        import torch  # noqa: PLC0415  (perezoso)

        if not torch.cuda.is_available():
            return False
        torch.cuda.reset_peak_memory_stats(device)
    except Exception:
        return False
    return True


# --------------------------------------------------------------------------- #
# Formato de consola
# --------------------------------------------------------------------------- #

def _fmt(valor: Any, ndigits: int = 1, sufijo: str = "") -> str:
    """Numero formateado, o `n/d` cuando el dato no existe (nunca un cero falso)."""
    if valor is None:
        return "n/d"
    if isinstance(valor, bool):
        return "si" if valor else "no"
    if isinstance(valor, (int, float)):
        return f"{valor:.{ndigits}f}{sufijo}"
    return str(valor)


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Tabla Markdown alineada, lista para pegar en `inference_timing.md`."""
    anchos = [len(h) for h in headers]
    for fila in rows:
        for i, celda in enumerate(fila):
            if i < len(anchos):
                anchos[i] = max(anchos[i], len(celda))

    def linea(celdas: Sequence[str]) -> str:
        rellenas = [
            (celdas[i] if i < len(celdas) else "").ljust(anchos[i]) for i in range(len(anchos))
        ]
        return "| " + " | ".join(rellenas) + " |"

    separador = "|" + "|".join("-" * (a + 2) for a in anchos) + "|"
    return "\n".join([linea(headers), separador, *(linea(f) for f in rows)])


def _stats_dict(valores: Sequence[float]) -> dict[str, Any] | None:
    """`Stats.as_dict()` de la serie, o `None` si no hay ni una medida."""
    if not valores:
        return None
    return _timing.summarize(valores).as_dict()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vram_profile.py",
        description=(
            "T-03: mide tiempos de inferencia, VRAM pico con y sin offloading y "
            "arranque en frio de ACE-Step 1.5, y emite informe JSON + tablas."
        ),
        epilog=(
            "Ejemplo de verificacion sin GPU: "
            "python apps/runner/spikes/vram_profile.py --mock --runs 2 --both"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Inferencias por escenario (T-03 pide 10 con y 10 sin offloading).",
    )
    escenarios = parser.add_mutually_exclusive_group()
    escenarios.add_argument(
        "--both",
        dest="scenarios",
        action="store_const",
        const="both",
        help="Mide los dos escenarios: sin offloading y con offloading (por defecto).",
    )
    escenarios.add_argument(
        "--offload",
        dest="scenarios",
        action="store_const",
        const=SCENARIO_OFFLOAD,
        help="Mide solo con offloading (suelo de 8 GB, tiempos degradados).",
    )
    escenarios.add_argument(
        "--no-offload",
        dest="scenarios",
        action="store_const",
        const=SCENARIO_NO_OFFLOAD,
        help="Mide solo sin offloading (linea base comparable con S-02).",
    )
    parser.set_defaults(scenarios="both")
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Usa el adapter mock de _mock.py (solo biblioteca estandar). Verifica el "
            "arnes sin GPU; NO produce mediciones validas para T-03."
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Ruta del informe JSON. Si termina en .json se usa tal cual; si es un "
            "directorio se genera el nombre dentro. Por defecto: "
            "apps/runner/spikes/results/ (relativo a este script, no al cwd)."
        ),
    )
    parser.add_argument(
        "--duration-s",
        type=int,
        default=180,
        help="Duracion de la pista a generar en cada run, en segundos.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help=(
            "Semilla base; cada run usa seed+indice. Se registra por TRAZABILIDAD: "
            "no garantiza salida identica (D-13)."
        ),
    )
    parser.add_argument(
        "--max-gpu-seconds",
        type=int,
        default=600,
        help="Presupuesto de segundos de GPU por run y del runner (D-17).",
    )
    parser.add_argument(
        "--gpu-label",
        default=None,
        help=(
            "Etiqueta de la GPU real usada (p. ej. 'RTX 4090'), para el factor de "
            "conversion a la L40S objetivo. Si contiene 'L40S' el factor es 1,0."
        ),
    )
    parser.add_argument(
        "--l40s-inference-s",
        type=float,
        default=S02_INFERENCE_S,
        help=(
            "Inferencia pura de referencia en la L40S, en segundos. El valor por "
            "defecto es la HIPOTESIS S-02 de la spec; sustituyelo por la medicion "
            "real del pod cuando exista."
        ),
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Dispositivo del RunnerContext. Por defecto 'mock' con --mock, 'cuda:0' si no.",
    )
    parser.add_argument(
        "--dtype",
        default="bfloat16",
        help="Precision de computo declarada al adapter.",
    )
    parser.add_argument(
        "--weights-dir",
        default=os.environ.get("WEIGHTS_DIR", "/workspace/weights"),
        help=(
            "Directorio de la cache de pesos safetensors (D-14 lo valida el adapter). "
            "Es una RUTA, nunca una credencial (D-15)."
        ),
    )
    parser.add_argument(
        "--skip-cold-start",
        action="store_true",
        help="Omite el bloque de arranque en frio (criterio 3 quedara sin medir).",
    )
    return parser


def _resolve_out_path(raw: str | None, *, mode: str) -> Path:
    """Ruta final del informe: fichero explicito o nombre generado en un directorio."""
    if raw is not None:
        candidato = Path(raw)
        if candidato.suffix.lower() == ".json":
            return candidato
        directorio = candidato
    else:
        directorio = Path(_SPIKES_DIR) / "results"
    marca = datetime.now().strftime("%Y%m%d-%H%M%S")
    return directorio / f"t03-vram-profile-{mode}-{marca}.json"


# --------------------------------------------------------------------------- #
# Adapters
# --------------------------------------------------------------------------- #

def _load_real_adapter_class() -> type:
    """Import **perezoso** de `AceStepAdapter` desde `adapters/ace_step/adapter.py`.

    Se carga por ruta con `importlib` porque en la Fase 0 no hay paquete
    instalable (eso es T-10, detras de G1). Si el fichero no existe todavia el
    mensaje lo dice: lo crea T-05, y hasta entonces solo hay `--mock`.
    """
    import importlib.util  # noqa: PLC0415  (perezoso, solo en el camino real)

    ruta = Path(_RUNNER_ROOT) / REAL_ADAPTER_REL_PATH
    if not ruta.is_file():
        raise SpikeError(
            f"No existe {ruta}. El adapter real de ACE-Step lo crea T-05 "
            "(contenerizacion minima), que aun no esta implementada. Para verificar "
            "este arnes usa --mock; para medir T-03 de verdad, espera a T-05."
        )
    spec = importlib.util.spec_from_file_location("ace_step_adapter_t05", ruta)
    if spec is None or spec.loader is None:
        raise SpikeError(f"No se pudo preparar el import de {ruta}.")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    try:
        spec.loader.exec_module(modulo)
    except Exception as exc:
        raise SpikeError(
            f"Fallo al importar {ruta}: {type(exc).__name__}: {exc}. Si el fallo es un "
            "import de torch/CUDA, esta maquina no tiene GPU: usa --mock."
        ) from exc
    clase = getattr(modulo, REAL_ADAPTER_CLASS, None)
    if clase is None:
        raise SpikeError(
            f"{ruta} no expone '{REAL_ADAPTER_CLASS}'. El arnes de T-03 espera esa "
            "clase implementando contracts.MusicModelAdapter."
        )
    return clase


def _adapter_factory(args: argparse.Namespace) -> Callable[..., MusicModelAdapter]:
    """Devuelve la fabrica de adapters del modo elegido.

    Los flags `image_cached` / `weights_cached` solo tienen sentido en el mock: en
    el camino real el estado de la cache lo fija el host (docker / volumen del
    pod), no el arnes, y por eso se ignoran de forma explicita.
    """
    if args.mock:

        def crear_mock(*, image_cached: bool = True, weights_cached: bool = True) -> MusicModelAdapter:
            return MockMusicModelAdapter(
                image_cached=image_cached,
                weights_cached=weights_cached,
                output_dir=None,  # 10 runs x ~32 MB de WAV no aportan nada a T-03
                time_scale=0.0,   # los tiempos del mock son simulados, no vividos
            )

        return crear_mock

    clase = _load_real_adapter_class()

    def crear_real(*, image_cached: bool = True, weights_cached: bool = True) -> MusicModelAdapter:
        del image_cached, weights_cached  # los fija el host, no este script
        try:
            return clase()
        except TypeError as exc:
            raise SpikeError(
                f"{REAL_ADAPTER_CLASS}() no se puede construir sin argumentos "
                f"({exc}). T-03 invoca el adapter directo (sin la abstraccion de "
                "proveedor de T-85): dale valores por defecto o adapta el arnes."
            ) from exc

    return crear_real


def _meta_backend_adapter(adapter: Any) -> dict[str, Any]:
    """Backend y fuente que declara un adapter, leyendo `backend` y `describe()`.

    Es la materia prima de `es_adapter_degradado_a_mock()`: no carga pesos ni
    toca la GPU, solo lee lo que el adapter dice de si mismo.
    """
    meta: dict[str, Any] = {
        "backend": getattr(adapter, "backend", None),
        "backend_reason": str(getattr(adapter, "backend_reason", "") or ""),
        "source": None,
    }
    describe = getattr(adapter, "describe", None)
    if callable(describe):
        try:
            meta["source"] = dict(describe()).get("source")
        except Exception:  # noqa: BLE001  (un describe() roto no decide nada)
            pass
    return meta


def es_adapter_degradado_a_mock(meta: dict[str, Any]) -> bool:
    """Decide si un adapter 'real' esta de hecho degradado al mock (defecto C1).

    Mismo criterio que `capability_probe` (T-07): un `backend` `"mock"` o
    `"unavailable"`, o una cabecera con `source == "mock"`, delatan que las
    cifras NO son mediciones. El llamante debe degradar el informe ENTERO a modo
    mock (source, avisos, criterios en `simulado`), nunca etiquetarlo como GPU.
    """
    backend = str(meta.get("backend", "") or "")
    fuente = str(meta.get("source", "") or "")
    return backend in ("mock", "unavailable") or fuente == "mock"


def _load_stage_timings_adapter(adapter: Any) -> dict[str, float]:
    """Etapas de carga que reporta el adapter (contrato M-3).

    Desde M-3 los `stage_timings` de una generacion cubren SOLO esa generacion;
    las etapas del arranque (`weights_download`, `vram_load`, `warmup`...) las
    reporta el adapter aparte, en `load_stage_timings_s` de `describe()`
    (adapter real) o `report_metadata()` (mock). Nunca lanza: un adapter sin
    cabecera legible simplemente no aporta etapas de carga.
    """
    for nombre in ("describe", "report_metadata"):
        metodo = getattr(adapter, nombre, None)
        if callable(metodo):
            try:
                crudo = dict(metodo()).get("load_stage_timings_s") or {}
                return {str(k): float(v) for k, v in dict(crudo).items()}
            except Exception:  # noqa: BLE001
                return {}
    return {}


def _make_context(args: argparse.Namespace, *, offload: bool) -> RunnerContext:
    """`RunnerContext` del escenario. **Sin credenciales, a proposito (D-15).**"""
    device = args.device or ("mock" if args.mock else "cuda:0")
    return RunnerContext(
        device=device,
        dtype=args.dtype,
        offload=offload,
        weights_dir=args.weights_dir,
        max_gpu_seconds=args.max_gpu_seconds,
    )


def _make_run_request(args: argparse.Namespace, *, scenario: str, index: int) -> GenerationRequest:
    """Peticion del run `index`. La `idempotency_key` distingue trabajos logicos.

    La semilla varia por run (`seed + index - 1`): medir diez veces exactamente la
    misma trayectoria de difusion no da diez medidas, da una repetida.
    """
    return make_request(
        duration_s=args.duration_s,
        max_gpu_seconds=args.max_gpu_seconds,
        idempotency_key=f"t03-{scenario}-{index:03d}",
        seed=None if args.seed is None else args.seed + index - 1,
    )


# --------------------------------------------------------------------------- #
# Medicion: arranque en frio
# --------------------------------------------------------------------------- #

def _normalize_cold_stages(etapas: dict[str, float], *, mock: bool) -> dict[str, Any]:
    """Etapas de arranque en frio, con `null` **y motivo** en lo no medible.

    `scheduling` e `image_pull` salen siempre a `null`: aqui no se miden. Lo que el
    adapter haya reportado para ellas se conserva aparte y marcado, para que quede
    trazable sin colarse como medicion (en modo mock es una simulacion).
    """
    salida: dict[str, Any] = {}
    for etapa in _timing.COLD_START_STAGES:
        valor = etapas.get(etapa)
        if etapa in STAGES_ONLY_RUNPOD:
            salida[etapa] = {
                "s": None,
                "reason": REASON_ONLY_RUNPOD,
                "adapter_reported_s": None if valor is None else round(float(valor), 3),
                "adapter_reported_is_simulation": mock,
            }
        else:
            salida[etapa] = {
                "s": None if valor is None else round(float(valor), 3),
                "reason": None
                if valor is not None
                else "el adapter no reporto esta etapa en stage_timings.",
            }
    return salida


async def _measure_cold_start(
    args: argparse.Namespace,
    *,
    offload: bool,
    factory: Callable[..., MusicModelAdapter],
    warnings: list[str],
) -> dict[str, Any]:
    """Mide el arranque en frio en los escenarios que el modo permite.

    En `--mock` se recorren los tres escenarios de T-03 (imagen cacheada, imagen no
    cacheada, pesos no cacheados) porque el mock los sabe simular. En el camino
    real solo hay **un** escenario observable: el estado de cache que tenga el host
    en ese momento. Los otros dos exigen el pod de RunPod (o un `docker pull` en
    frio) y se declaran no medidos, no se estiman.
    """
    if args.mock:
        plan = [
            (
                "image_cached",
                True,
                True,
                "Imagen y pesos en cache del host.",
                S01_RANGE_IMAGE_CACHED_S,
            ),
            (
                "image_not_cached",
                False,
                True,
                "Imagen de contenedor sin cache (termino dominante, S-01b).",
                S01_RANGE_IMAGE_NOT_CACHED_S,
            ),
            (
                "weights_not_cached",
                True,
                False,
                "Pesos safetensors sin cache en el volumen persistente.",
                S01_RANGE_IMAGE_NOT_CACHED_S,
            ),
        ]
    else:
        plan = [
            (
                "host_state_as_is",
                True,
                True,
                (
                    "Unico escenario observable desde este script: el estado real de la "
                    "cache de imagen y de pesos lo fija el host (docker / volumen del "
                    "pod). Los escenarios 'imagen no cacheada' y 'pesos no cacheados' "
                    "exigen el pod de RunPod o un docker pull en frio."
                ),
                None,
            )
        ]

    escenarios: dict[str, Any] = {}
    for nombre, image_cached, weights_cached, descripcion, rango in plan:
        adapter = factory(image_cached=image_cached, weights_cached=weights_cached)
        ctx = _make_context(args, offload=offload)
        bloque: dict[str, Any] = {
            "description": descripcion,
            "image_cached": image_cached if args.mock else None,
            "weights_cached": weights_cached if args.mock else None,
            "expected_range_s": list(rango) if rango else None,
            "expected_range_source": (
                "S-01/S-01b de spec.md §11: EXPECTATIVA de la spec, no medicion."
                if rango
                else None
            ),
        }
        t0 = perf_counter()
        try:
            await adapter.load(ctx)
        except Exception as exc:
            bloque["status"] = "error"
            bloque["detail"] = f"{type(exc).__name__}: {exc}"
            bloque["load_wall_s"] = round(perf_counter() - t0, 3)
            warnings.append(
                f"Arranque en frio '{nombre}': load() fallo ({type(exc).__name__}). "
                "El escenario queda sin medir."
            )
            escenarios[nombre] = bloque
            await adapter.unload()
            continue
        bloque["load_wall_s"] = round(perf_counter() - t0, 3)

        salud = await adapter.health()
        bloque["health"] = {
            "ready": salud.ready,
            "detail": salud.detail,
            "vram_total_mb": salud.vram_total_mb,
            "vram_free_mb": salud.vram_free_mb,
        }

        # Contrato M-3: las etapas del arranque las reporta el propio adapter
        # (load_stage_timings_s); la telemetria de la sonda ya cubre SOLO su
        # inferencia y no las repite.
        etapas: dict[str, float] = _load_stage_timings_adapter(adapter)
        try:
            sonda = make_request(
                duration_s=COLD_START_PROBE_DURATION_S,
                max_gpu_seconds=args.max_gpu_seconds,
                idempotency_key=f"t03-cold-{nombre}",
                seed=args.seed,
            )
            resultado = await adapter.generate(sonda)
            bloque["probe"] = {
                "duration_s": COLD_START_PROBE_DURATION_S,
                "gpu_seconds": resultado.telemetry.gpu_seconds,
                "vram_peak_mb": resultado.telemetry.vram_peak_mb,
                "note": (
                    "Pista corta de sonda: cierra el arranque en frio con la primera "
                    "generacion real, que es lo que paga un usuario al despertar el pod."
                ),
            }
        except GpuBudgetExceeded as exc:
            bloque["probe"] = {
                "status": "aborted_gpu_budget",
                "elapsed_s": exc.elapsed_s,
                "max_gpu_seconds": exc.max_gpu_seconds,
                "note": "D-17 aplicado: el presupuesto se agoto durante el arranque en frio.",
            }
            warnings.append(
                f"Arranque en frio '{nombre}': la sonda agoto max_gpu_seconds "
                f"({exc.elapsed_s:.1f} s > {exc.max_gpu_seconds} s)."
            )
        except Exception as exc:
            bloque["probe"] = {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}
            warnings.append(f"Arranque en frio '{nombre}': la sonda fallo ({type(exc).__name__}).")
        finally:
            await adapter.unload()

        bloque["stages"] = _normalize_cold_stages(etapas, mock=args.mock)
        medibles = {
            k: v
            for k, v in etapas.items()
            if k in _timing.COLD_START_STAGES and k not in STAGES_ONLY_RUNPOD
        }
        temporizador = _timing.StageTimer()
        temporizador.merge(medibles)
        bloque["measurable_timer_report"] = temporizador.as_report()
        bloque["cold_start_measurable_s"] = round(temporizador.total_s(), 3)
        bloque["cold_start_total_s"] = None
        bloque["cold_start_total_reason"] = REASON_ONLY_RUNPOD
        bloque.setdefault("status", "ok")
        escenarios[nombre] = bloque

    return {
        "offload": offload,
        "scenarios": escenarios,
        "notice": (
            "El arranque en frio COMPLETO (con scheduling e image_pull) solo es medible "
            "contra el pod de RunPod. Este bloque mide lo local (weights_download, "
            "vram_load, warmup) y deja el resto en null con motivo."
        ),
    }


# --------------------------------------------------------------------------- #
# Medicion: escenarios de inferencia
# --------------------------------------------------------------------------- #

async def _measure_scenario(
    args: argparse.Namespace,
    *,
    offload: bool,
    factory: Callable[..., MusicModelAdapter],
    warnings: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Ejecuta `--runs` inferencias en un escenario y devuelve (agregado, runs).

    El modelo se carga **una vez** y se mantiene cargado durante los N runs: es el
    escenario real de un pod caliente (keep-warm 10 min), y recargar antes de cada
    run mediria N arranques en frio, no N inferencias. Para que los N picos de VRAM
    sean independientes se reinicia el contador de pico entre runs cuando torch lo
    permite.
    """
    nombre = SCENARIO_OFFLOAD if offload else SCENARIO_NO_OFFLOAD
    ctx = _make_context(args, offload=offload)
    adapter = factory()
    if not isinstance(adapter, MusicModelAdapter):
        warnings.append(
            f"El adapter de '{nombre}' no satisface contracts.MusicModelAdapter "
            "(faltan metodos del Protocol). Se continua, pero el resultado es sospechoso."
        )

    agregado: dict[str, Any] = {
        "scenario": nombre,
        "offload": offload,
        "requested_runs": args.runs,
        "device": ctx.device,
        "dtype": ctx.dtype,
        "max_gpu_seconds": args.max_gpu_seconds,
        "duration_s": args.duration_s,
    }
    runs: list[dict[str, Any]] = []

    with _timing.StageTimer() as temporizador:
        t0 = perf_counter()
        try:
            await adapter.load(ctx)
        except Exception as exc:
            agregado["status"] = "error"
            agregado["detail"] = f"load() fallo: {type(exc).__name__}: {exc}"
            warnings.append(f"Escenario '{nombre}': load() fallo ({type(exc).__name__}: {exc}).")
            await adapter.unload()
            return agregado, runs
        agregado["load_wall_s"] = round(perf_counter() - t0, 3)

        # M-3: coste del arranque, pagado UNA vez por carga y reportado aparte por
        # el adapter. Se refleja aqui para que el informe conserve el termino de
        # arranque del presupuesto de D-17 sin multiplicarlo por N runs (las
        # telemetrias de cada run ya no lo arrastran).
        etapas_carga = _load_stage_timings_adapter(adapter)
        agregado["load_stage_timings_s"] = {
            k: round(v, 3) for k, v in etapas_carga.items()
        }
        agregado["load_gpu_seconds"] = round(
            sum(
                v
                for k, v in etapas_carga.items()
                if k in _timing.GPU_STAGES and k != "inference"
            ),
            3,
        )
        agregado["load_gpu_seconds_note"] = (
            "Coste de GPU del arranque (vram_load + warmup), pagado UNA vez por "
            "escenario (M-3): no esta incluido en los gpu_seconds de cada run."
        )

        salud = await adapter.health()
        agregado["health_after_load"] = {
            "ready": salud.ready,
            "detail": salud.detail,
            "vram_total_mb": salud.vram_total_mb,
            "vram_free_mb": salud.vram_free_mb,
        }

        inferencias: list[float] = []
        gpu_segundos: list[float] = []
        picos: list[float] = []

        for indice in range(1, args.runs + 1):
            peticion = _make_run_request(args, scenario=nombre, index=indice)
            registro: dict[str, Any] = {
                "scenario": nombre,
                "run": indice,
                "offload": offload,
                "idempotency_key": peticion.idempotency_key,
                "seed": peticion.seed,
                "duration_s": peticion.duration_s,
                "max_gpu_seconds": peticion.max_gpu_seconds,
            }
            registro["peak_counter_reset"] = _reset_peak_vram()
            antes = _timing.vram_snapshot_mb()
            reloj = perf_counter()
            try:
                with temporizador.stage("inference"):
                    resultado = await adapter.generate(peticion)
            except GpuBudgetExceeded as exc:
                registro["status"] = "aborted_gpu_budget"
                registro["harness_wall_s"] = round(perf_counter() - reloj, 3)
                registro["elapsed_s"] = exc.elapsed_s
                registro["detail"] = str(exc)
                runs.append(registro)
                warnings.append(
                    f"Escenario '{nombre}' run {indice}: abortado por D-17 "
                    f"({exc.elapsed_s:.1f} s > {exc.max_gpu_seconds} s). No entra en las "
                    "estadisticas."
                )
                continue
            except Exception as exc:
                registro["status"] = "error"
                registro["harness_wall_s"] = round(perf_counter() - reloj, 3)
                registro["detail"] = f"{type(exc).__name__}: {exc}"
                runs.append(registro)
                warnings.append(f"Escenario '{nombre}' run {indice}: {type(exc).__name__}: {exc}.")
                continue

            wall = perf_counter() - reloj
            telemetria = resultado.telemetry
            registro["harness_wall_s"] = round(wall, 3)
            registro["gpu_seconds"] = telemetria.gpu_seconds
            registro["offloading_enabled_reported"] = telemetria.offloading_enabled
            registro["retries"] = telemetria.retries
            registro["stage_timings_s"] = {
                k: round(float(v), 3) for k, v in telemetria.stage_timings.items()
            }

            inferencia = telemetria.stage_timings.get("inference")
            if inferencia is None:
                inferencia = wall
                registro["inference_source"] = (
                    "reloj del arnes: el adapter no reporto stage_timings['inference']."
                )
                warnings.append(
                    f"Escenario '{nombre}' run {indice}: sin stage_timings['inference']; "
                    "se usa el reloj del arnes, que incluye sobrecarga del proceso."
                )
            else:
                registro["inference_source"] = "telemetria del adapter"
            registro["inference_s"] = round(float(inferencia), 3)
            inferencias.append(float(inferencia))
            gpu_segundos.append(float(telemetria.gpu_seconds))

            # D-17 revalidado por el arnes: el adapter es quien debe abortar, pero si
            # devuelve un resultado fuera de presupuesto hay que verlo en el informe.
            try:
                assert_within_gpu_budget(
                    telemetria.gpu_seconds,
                    min(peticion.max_gpu_seconds, ctx.max_gpu_seconds),
                    detail=f"Revalidacion del arnes de T-03, escenario '{nombre}' run {indice}.",
                )
                registro["status"] = "ok"
            except GpuBudgetExceeded as exc:
                registro["status"] = "budget_violation_reported"
                registro["detail"] = str(exc)
                warnings.append(
                    f"Escenario '{nombre}' run {indice}: el adapter devolvio "
                    f"{telemetria.gpu_seconds:.1f} gpu_seconds con presupuesto "
                    f"{exc.max_gpu_seconds} s. Deberia haber abortado (D-17)."
                )

            pico_telemetria = telemetria.vram_peak_mb
            despues = _timing.vram_snapshot_mb()
            registro["vram_peak_mb_telemetry"] = pico_telemetria
            registro["vram_snapshot_before_mb"] = list(antes) if antes else None
            registro["vram_snapshot_after_mb"] = list(despues) if despues else None
            pico_proceso = despues[2] if despues else None
            registro["vram_peak_mb_process"] = pico_proceso
            pico_efectivo = pico_telemetria if pico_telemetria is not None else pico_proceso
            registro["vram_peak_mb"] = pico_efectivo
            if pico_efectivo is None:
                warnings.append(
                    f"Escenario '{nombre}' run {indice}: sin pico de VRAM (ni telemetria "
                    "ni torch.cuda). El criterio 2 de T-03 no se puede cerrar asi."
                )
            else:
                picos.append(float(pico_efectivo))

            artefactos = resultado.artifacts
            registro["artifacts"] = [
                {
                    "format": a.format,
                    "sample_rate": a.sample_rate,
                    "channels": a.channels,
                    "duration_s": a.duration_s,
                    "size_bytes": a.size_bytes,
                    "on_disk": a.path is not None,
                }
                for a in artefactos
            ]
            runs.append(registro)

        await adapter.unload()

    ok = [r for r in runs if r.get("status") in ("ok", "budget_violation_reported")]
    agregado["completed_runs"] = len(ok)
    agregado["status"] = "ok" if ok else "no_measurement"
    agregado["inference_s"] = _stats_dict(inferencias)
    agregado["gpu_seconds"] = _stats_dict(gpu_segundos)
    agregado["vram_peak_mb"] = _stats_dict(picos)
    agregado["harness_clock"] = temporizador.as_report()
    agregado["harness_clock_note"] = (
        "Reloj real del arnes por etapa. En --mock no dice nada (los tiempos del mock "
        "son simulados, no vividos); en GPU real es el contraste externo de la telemetria."
    )

    pico_max = max(picos) if picos else None
    agregado["vram_thresholds"] = {
        "floor_mb": _timing.VRAM_FLOOR_MB,
        "comfort_mb": _timing.VRAM_COMFORT_MB,
        "l40s_reference_mb": _timing.VRAM_REFERENCE_L40S_MB,
        "peak_max_mb": pico_max,
        "fits_floor_8gb": None if pico_max is None else pico_max <= _timing.VRAM_FLOOR_MB,
        "fits_comfort_24gb": None if pico_max is None else pico_max <= _timing.VRAM_COMFORT_MB,
        "fits_l40s_48gb": None
        if pico_max is None
        else pico_max <= _timing.VRAM_REFERENCE_L40S_MB,
    }
    return agregado, runs


# --------------------------------------------------------------------------- #
# Derivados: factor de conversion y comparacion con S-02
# --------------------------------------------------------------------------- #

def _l40s_conversion(
    args: argparse.Namespace, *, baseline_median_s: float | None, mode: str
) -> dict[str, Any]:
    """Factor de conversion de la GPU local a la L40S objetivo.

    Es un **ratio explicito de tiempos**, no una equivalencia de hardware: se
    obtiene dividiendo la referencia de inferencia de la L40S por la mediana
    medida en local. Multiplicar los tiempos locales por el factor da una
    estimacion para la L40S, y esa estimacion es una **extrapolacion lineal a
    validar**, nunca una medida: memoria, kernels de atencion y reloj no escalan
    linealmente entre arquitecturas.
    """
    etiqueta = args.gpu_label
    es_l40s = bool(etiqueta) and "l40s" in etiqueta.lower()
    bloque: dict[str, Any] = {
        "gpu_label": etiqueta,
        "is_l40s": es_l40s,
        "l40s_reference_inference_s": args.l40s_inference_s,
        "l40s_reference_source": (
            "Hipotesis S-02 de spec.md §11 (~90 s de inferencia pura) mientras no exista "
            "medicion real en el pod. Sustituible con --l40s-inference-s."
            if args.l40s_inference_s == S02_INFERENCE_S
            else "Valor aportado por el operador con --l40s-inference-s."
        ),
        "local_inference_median_s": baseline_median_s,
        "factor_local_to_l40s": None,
        "warning": (
            "EXTRAPOLACION LINEAL A VALIDAR, NO UNA MEDIDA. El factor traslada tiempos "
            "medidos en la GPU local a una estimacion para la L40S; solo una medicion en "
            "la L40S lo confirma. No usar para recalibrar evaluation.md §6 sin decir que "
            "es una extrapolacion."
        ),
    }
    if es_l40s:
        bloque["factor_local_to_l40s"] = 1.0
        bloque["note"] = (
            "La medicion ya es en la GPU objetivo (L40S): no hay conversion que aplicar."
        )
        return bloque
    if etiqueta is None:
        bloque["note"] = (
            "Sin --gpu-label no se puede documentar el factor de conversion (criterio 6 "
            "de T-03). Pasa la etiqueta de la GPU usada."
        )
        return bloque
    if baseline_median_s is None or baseline_median_s <= 0:
        bloque["note"] = (
            "Sin mediana de inferencia sin offloading no hay ratio: el escenario "
            "comparable con S-02 es el de 24 GB o mas sin offloading."
        )
        return bloque
    bloque["factor_local_to_l40s"] = round(args.l40s_inference_s / baseline_median_s, 4)
    bloque["note"] = (
        f"Estimacion para la L40S = tiempo local x {bloque['factor_local_to_l40s']}. "
        f"Ratio derivado de {baseline_median_s:.1f} s medidos en '{etiqueta}' frente a "
        f"{args.l40s_inference_s:.1f} s de referencia en L40S."
    )
    if mode == "mock":
        bloque["note"] += " Modo --mock: el numerador y el denominador no son mediciones."
    return bloque


def _s02_comparison(baseline: dict[str, Any] | None, *, mode: str) -> dict[str, Any]:
    """Contraste de lo medido sin offloading contra la linea base S-02."""
    bloque: dict[str, Any] = {
        "reference_total_s": S02_TOTAL_S,
        "reference_inference_s": S02_INFERENCE_S,
        "reference_source": (
            "S-02 de spec.md §11: 150 s totales por pista con ~90 s de inferencia pura en "
            "GPU de >= 24 GB. Es la hipotesis que T-03 tiene que confirmar o corregir."
        ),
        "measured_inference_median_s": None,
        "delta_inference_pct": None,
        "measured_gpu_seconds_median_s": None,
        "recommendation": None,
    }
    if not baseline or not baseline.get("inference_s"):
        bloque["recommendation"] = (
            "Sin escenario sin offloading medido no se puede recomendar ajuste de "
            "S-02/S-02b: la referencia se define en GPU de >= 24 GB sin offloading."
        )
        return bloque
    mediana = float(baseline["inference_s"]["median"])
    bloque["measured_inference_median_s"] = mediana
    bloque["delta_inference_pct"] = round((mediana - S02_INFERENCE_S) / S02_INFERENCE_S * 100.0, 1)
    if baseline.get("gpu_seconds"):
        bloque["measured_gpu_seconds_median_s"] = float(baseline["gpu_seconds"]["median"])
    if mode == "mock":
        bloque["recommendation"] = (
            "Modo --mock: NO se recomienda ningun ajuste de S-02/S-02b. Los tiempos son "
            "simulados y recalibrar evaluation.md §6 con ellos seria un error material."
        )
    else:
        delta = bloque["delta_inference_pct"]
        if abs(delta) <= 15.0:
            bloque["recommendation"] = (
                f"Desvio del {delta:+.1f} % frente a S-02: dentro de ruido razonable. "
                "Mantener S-02 y anotar el valor medido en inference_timing.md."
            )
        else:
            bloque["recommendation"] = (
                f"Desvio del {delta:+.1f} % frente a S-02. Documentar en "
                "inference_timing.md como entrada para revisar S-02/S-02b y el §6 de "
                "evaluation.md (coste de GPU escala linealmente con este numero). No "
                "corregir la evaluacion desde esta tarea."
            )
    return bloque


def _acceptance_criteria(
    args: argparse.Namespace,
    *,
    mode: str,
    environment: dict[str, Any],
    cold_start: dict[str, Any] | None,
    scenarios: dict[str, dict[str, Any]],
    conversion: dict[str, Any],
) -> list[dict[str, Any]]:
    """Estado de los seis criterios de T-03 segun lo que esta ejecucion ha medido.

    En modo `--mock` **ningun** criterio se marca como medido: el estado es
    `simulado`, que es justo lo que impide que un informe de verificacion del arnes
    se lea como el cierre de la tarea.
    """
    simulado = mode == "mock"
    sin_offload = scenarios.get(SCENARIO_NO_OFFLOAD)
    con_offload = scenarios.get(SCENARIO_OFFLOAD)
    vram_total = environment.get("vram_total_mb")
    nota_mock = (
        "Modo --mock: valor SIMULADO de forma determinista por el adapter mock. No "
        "satisface el criterio; T-03 exige GPU real."
    )

    def estado(cumple: bool | None) -> str:
        if simulado:
            return "simulado"
        if cumple is None:
            return "parcial"
        return "medido" if cumple else "no medido"

    criterios: list[dict[str, Any]] = []

    tiene_base = bool(sin_offload and sin_offload.get("inference_s"))
    gpu_suficiente = None if vram_total is None else vram_total >= _timing.VRAM_COMFORT_MB
    criterios.append(
        {
            "id": 1,
            "criterion": (
                "Tiempo de inferencia por pista medido en GPU >= 24 GB (S-02: 150 s "
                "totales, ~90 s de inferencia pura)."
            ),
            "status": estado(bool(tiene_base and gpu_suficiente)),
            "value": (sin_offload or {}).get("inference_s"),
            "note": nota_mock
            if simulado
            else (
                "VRAM total no detectada: no se puede afirmar que la medicion sea en "
                ">= 24 GB."
                if vram_total is None
                else (
                    f"VRAM detectada {vram_total} MB frente al confort de "
                    f"{_timing.VRAM_COMFORT_MB} MB."
                )
            ),
        }
    )

    picos_ambos = bool(
        sin_offload
        and sin_offload.get("vram_peak_mb")
        and con_offload
        and con_offload.get("vram_peak_mb")
    )
    criterios.append(
        {
            "id": 2,
            "criterion": (
                "VRAM pico con y sin offloading, frente al suelo de 8 GB y el confort "
                "de 24 GB (spec §11.1)."
            ),
            "status": estado(picos_ambos),
            "value": {
                SCENARIO_NO_OFFLOAD: (sin_offload or {}).get("vram_thresholds"),
                SCENARIO_OFFLOAD: (con_offload or {}).get("vram_thresholds"),
            },
            "note": nota_mock
            if simulado
            else (
                "Los dos escenarios medidos."
                if picos_ambos
                else "Falta uno de los dos escenarios: ejecutar con --both."
            ),
        }
    )

    criterios.append(
        {
            "id": 3,
            "criterion": (
                "Arranque en frio medido con imagen cacheada (2-6 min) y sin cachear "
                "(5-12 min)."
            ),
            "status": "simulado" if simulado else "parcial" if cold_start else "no medido",
            "value": None
            if cold_start is None
            else {
                nombre: bloque.get("cold_start_measurable_s")
                for nombre, bloque in cold_start["scenarios"].items()
            },
            "note": nota_mock
            if simulado
            else (
                REASON_ONLY_RUNPOD
                if cold_start
                else "Ejecutado con --skip-cold-start: el criterio queda sin abordar."
            ),
        }
    )

    etapas_vistas = sorted(
        {
            etapa
            for escenario in scenarios.values()
            for etapa in (escenario.get("harness_clock", {}).get("stage_timings_s", {}) or {})
        }
        | {
            etapa
            for escenario in scenarios.values()
            for run in escenario.get("_stage_keys", [])
            for etapa in run
        }
    )
    criterios.append(
        {
            "id": 4,
            "criterion": (
                "Instrumentacion por etapas: scheduling, image_pull, weights_download, "
                "vram_load, warmup, inference."
            ),
            "status": "simulado" if simulado else "parcial",
            "value": {
                "canonical_stages": list(_timing.STAGES),
                "stages_not_measurable_locally": list(STAGES_ONLY_RUNPOD),
                "harness_measured_stages": etapas_vistas,
            },
            "note": nota_mock if simulado else REASON_ONLY_RUNPOD,
        }
    )

    diez_y_diez = bool(
        sin_offload
        and con_offload
        and sin_offload.get("completed_runs", 0) >= 10
        and con_offload.get("completed_runs", 0) >= 10
    )
    criterios.append(
        {
            "id": 5,
            "criterion": "10 inferencias con offloading y 10 sin offloading, con VRAM pico de cada una.",
            "status": estado(diez_y_diez),
            "value": {
                SCENARIO_NO_OFFLOAD: (sin_offload or {}).get("completed_runs", 0),
                SCENARIO_OFFLOAD: (con_offload or {}).get("completed_runs", 0),
            },
            "note": nota_mock
            if simulado
            else (
                "Cumplido."
                if diez_y_diez
                else "Se necesitan >= 10 runs completados en cada escenario (--runs 10 --both)."
            ),
        }
    )

    criterios.append(
        {
            "id": 6,
            "criterion": "Factor de conversion entre la GPU local usada y la L40S objetivo, si difieren.",
            "status": estado(conversion.get("factor_local_to_l40s") is not None),
            "value": conversion.get("factor_local_to_l40s"),
            "note": nota_mock if simulado else conversion.get("note"),
        }
    )
    return criterios


# --------------------------------------------------------------------------- #
# Consola
# --------------------------------------------------------------------------- #

def _print_report(payload: dict[str, Any], destino: Path) -> None:
    """Imprime las tablas en castellano listas para copiar a `inference_timing.md`."""
    entorno = payload["environment"]
    modo = payload["mode"]

    print()
    print(f"# {TASK} — tiempos de inferencia, VRAM y arranque en frio ({modo.upper()})")
    print()
    if modo == "mock":
        print(
            "> AVISO: ejecucion en modo --mock. Tiempos y VRAM **simulados** de forma\n"
            "> determinista. NO son una medicion y NO cierran ningun criterio de T-03,\n"
            "> que exige GPU real (local para inferencia/VRAM, pod de RunPod para el\n"
            "> arranque en frio)."
        )
        print()

    print("## Entorno")
    print()
    print(
        _md_table(
            ["Dato", "Valor"],
            [
                ["Generado", payload["generated_at"]],
                ["Modo", modo],
                ["Fuente de los tiempos", str(payload["adapter"].get("source"))],
                ["Etiqueta de GPU (operador)", str(entorno.get("gpu_label") or "n/d")],
                ["GPU detectada", str((entorno.get("gpu") or {}).get("name") or "n/d")],
                ["VRAM total (MB)", _fmt(entorno.get("vram_total_mb"), 0)],
                ["Driver", str(entorno["driver"].get("driver_version") or "n/d")],
                ["torch / CUDA", f"{entorno['torch'].get('version')} / {entorno['torch'].get('cuda_version')}"],
                ["Offloading decidido", _fmt(entorno["offloading_decision"]["offload"])],
                ["Plataforma", entorno["platform"]["system"] + " " + entorno["platform"]["release"]],
            ],
        )
    )
    print()
    print(f"Motivo de la decision de offloading: {entorno['offloading_decision']['reason']}")
    print()

    print("## Inferencia por escenario")
    print()
    filas = []
    for nombre in (SCENARIO_NO_OFFLOAD, SCENARIO_OFFLOAD):
        escenario = payload["scenarios"].get(nombre)
        if not escenario:
            continue
        inf = escenario.get("inference_s") or {}
        filas.append(
            [
                "sin offloading" if nombre == SCENARIO_NO_OFFLOAD else "con offloading",
                str(escenario.get("completed_runs", 0)),
                _fmt(inf.get("mean")),
                _fmt(inf.get("median")),
                _fmt(inf.get("p95")),
                _fmt(inf.get("min")),
                _fmt(inf.get("max")),
            ]
        )
    if filas:
        print(
            _md_table(
                ["Escenario", "n", "Media (s)", "Mediana (s)", "p95 (s)", "Min (s)", "Max (s)"],
                filas,
            )
        )
        print()
        print(
            "Con n=10 el p95 interpola entre las dos ultimas muestras: no es un p95 "
            "robusto y conviene decirlo asi en el informe."
        )
    else:
        print("Sin escenarios medidos.")
    print()

    print("## VRAM pico frente a los umbrales de D-06")
    print()
    filas = []
    for nombre in (SCENARIO_NO_OFFLOAD, SCENARIO_OFFLOAD):
        escenario = payload["scenarios"].get(nombre)
        if not escenario:
            continue
        vram = escenario.get("vram_peak_mb") or {}
        umbrales = escenario.get("vram_thresholds") or {}
        filas.append(
            [
                "sin offloading" if nombre == SCENARIO_NO_OFFLOAD else "con offloading",
                _fmt(vram.get("median"), 0),
                _fmt(vram.get("max"), 0),
                _fmt(umbrales.get("fits_floor_8gb")),
                _fmt(umbrales.get("fits_comfort_24gb")),
                _fmt(umbrales.get("fits_l40s_48gb")),
            ]
        )
    if filas:
        print(
            _md_table(
                [
                    "Escenario",
                    "Pico mediana (MB)",
                    "Pico max (MB)",
                    "Cabe en 8 GB",
                    "Cabe en 24 GB",
                    "Cabe en 48 GB",
                ],
                filas,
            )
        )
    else:
        print("Sin picos de VRAM registrados.")
    print()

    frio = payload.get("cold_start")
    print("## Arranque en frio")
    print()
    if not frio:
        print("No medido en esta ejecucion (--skip-cold-start).")
    else:
        filas = []
        for nombre, bloque in frio["scenarios"].items():
            etapas = bloque.get("stages", {})
            filas.append(
                [
                    nombre,
                    "no medido (RunPod)",
                    "no medido (RunPod)",
                    _fmt(etapas.get("weights_download", {}).get("s")),
                    _fmt(etapas.get("vram_load", {}).get("s")),
                    _fmt(etapas.get("warmup", {}).get("s")),
                    _fmt(bloque.get("cold_start_measurable_s")),
                ]
            )
        print(
            _md_table(
                [
                    "Escenario",
                    "scheduling",
                    "image_pull",
                    "weights_download (s)",
                    "vram_load (s)",
                    "warmup (s)",
                    "Total medible (s)",
                ],
                filas,
            )
        )
        print()
        print(frio["notice"])
    print()

    conversion = payload["l40s_conversion"]
    print("## Factor de conversion a la L40S")
    print()
    print(
        _md_table(
            ["Dato", "Valor"],
            [
                ["GPU local (etiqueta)", str(conversion.get("gpu_label") or "n/d")],
                ["Es L40S", _fmt(conversion.get("is_l40s"))],
                ["Mediana local de inferencia (s)", _fmt(conversion.get("local_inference_median_s"))],
                ["Referencia L40S (s)", _fmt(conversion.get("l40s_reference_inference_s"))],
                ["Factor local -> L40S", _fmt(conversion.get("factor_local_to_l40s"), 4)],
            ],
        )
    )
    print()
    print(conversion["warning"])
    if conversion.get("note"):
        print(conversion["note"])
    print()

    s02 = payload["s02_comparison"]
    print("## Contraste con S-02")
    print()
    print(
        _md_table(
            ["Dato", "Valor"],
            [
                ["Referencia S-02 total (s)", _fmt(s02["reference_total_s"])],
                ["Referencia S-02 inferencia (s)", _fmt(s02["reference_inference_s"])],
                ["Mediana medida sin offloading (s)", _fmt(s02.get("measured_inference_median_s"))],
                ["Desvio (%)", _fmt(s02.get("delta_inference_pct"))],
                ["gpu_seconds mediana (s)", _fmt(s02.get("measured_gpu_seconds_median_s"))],
            ],
        )
    )
    print()
    print(f"Recomendacion: {s02.get('recommendation')}")
    print()

    print("## Criterios de aceptacion de T-03")
    print()
    print(
        _md_table(
            ["#", "Estado", "Criterio"],
            [
                [str(c["id"]), c["status"], c["criterion"]]
                for c in payload["acceptance_criteria"]
            ],
        )
    )
    print()

    avisos = payload.get("warnings") or []
    if avisos:
        print("## Avisos")
        print()
        for aviso in avisos:
            print(f"- {aviso}")
        print()

    print(f"Informe JSON: {destino}")
    print()


# --------------------------------------------------------------------------- #
# Orquestacion
# --------------------------------------------------------------------------- #

async def _amain(args: argparse.Namespace) -> int:
    if args.runs < 1:
        raise SpikeError("--runs debe ser >= 1.")
    if args.duration_s < 1:
        raise SpikeError("--duration-s debe ser >= 1.")
    if args.max_gpu_seconds < 1:
        raise SpikeError("--max-gpu-seconds debe ser >= 1 (D-17).")
    if args.l40s_inference_s <= 0:
        raise SpikeError("--l40s-inference-s debe ser > 0.")

    modo = "mock" if args.mock else "gpu"
    avisos: list[str] = []

    informacion_gpu = _timing.gpu_info()
    vram_total = informacion_gpu["vram_total_mb"] if informacion_gpu else None
    offload_auto, motivo_offload = _timing.decide_offloading(vram_total)
    if motivo_offload.startswith(_timing.NOT_VIABLE_PREFIX) and not args.mock:
        raise SpikeError(
            f"{motivo_offload} (VRAM detectada: {vram_total} MB). T-03 no se mide a "
            "ciegas: aborta aqui."
        )
    if not args.mock and informacion_gpu is None:
        avisos.append(
            "Sin GPU detectada por torch.cuda y sin --mock: la ejecucion continuara "
            "pero los criterios de T-03 no se podran cerrar."
        )

    entorno: dict[str, Any] = {
        "gpu_label": args.gpu_label,
        "gpu": informacion_gpu,
        "vram_total_mb": vram_total,
        "driver": _driver_info(),
        "torch": _torch_info(),
        "offloading_decision": {"offload": offload_auto, "reason": motivo_offload},
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "weights_dir": args.weights_dir,
        "credentials_note": (
            "D-15: el runner corre sin credenciales persistentes. RunnerContext no "
            "transporta secretos y este arnes no lee ni escribe ninguno."
        ),
    }

    fabrica = _adapter_factory(args)

    # C1: el adapter de T-05 cae al mock EN SILENCIO cuando no ve CUDA (si
    # ACE_STEP_REQUIRE_GPU no esta puesto). Si eso pasa, este informe no puede
    # salir etiquetado como medicion: se degrada TODO a modo mock (source,
    # criterios en 'simulado', aviso visible), igual que hace capability_probe.
    aviso_degradado: str | None = None
    if not args.mock:
        meta_backend = _meta_backend_adapter(fabrica())
        if es_adapter_degradado_a_mock(meta_backend):
            modo = "mock"
            aviso_degradado = (
                "El adapter de T-05 NO esta corriendo sobre GPU real (backend="
                f"{meta_backend.get('backend')!r}, source={meta_backend.get('source')!r}): "
                f"{meta_backend.get('backend_reason', '')} El modo se degrada a 'mock' "
                "y ningun criterio de T-03 podra marcarse como medido. Para una "
                "medicion valida: GPU visible en el contenedor (docker run --gpus "
                "all), ACE_STEP_MOCK sin poner y ACE_STEP_REQUIRE_GPU=1."
            )
            print(f"[{TASK}] AVISO GRAVE: {aviso_degradado}", file=sys.stderr)
            avisos.append(aviso_degradado)

    if args.scenarios == "both":
        pedidos = [False, True]
    elif args.scenarios == SCENARIO_OFFLOAD:
        pedidos = [True]
    else:
        pedidos = [False]

    for offload in pedidos:
        if not args.mock and not offload and offload_auto and vram_total is not None:
            avisos.append(
                "Se ha pedido el escenario SIN offloading pero la VRAM detectada esta por "
                f"debajo del confort de {_timing.VRAM_COMFORT_MB} MB: si el adapter "
                "activa offloading por su cuenta, el escenario no sera comparable con S-02."
            )

    frio: dict[str, Any] | None = None
    if not args.skip_cold_start:
        # El arranque en frio se mide UNA vez, con el primer escenario pedido
        # (`pedidos[0]`): con --both eso es el escenario SIN offloading. Es una
        # decision de coste (cada arranque en frio son 2-6 min), no un olvido, y
        # el informe lo declara en 'offload_scenario_note'.
        frio = await _measure_cold_start(
            args, offload=pedidos[0], factory=fabrica, warnings=avisos
        )
        frio["offload_scenario_note"] = (
            f"Medido con offload={pedidos[0]} (el PRIMER escenario pedido; con "
            "--both es el escenario sin offloading). El arranque en frio no se "
            "repite por escenario para no pagar dos veces los 2-6 min de carga."
        )

    escenarios: dict[str, dict[str, Any]] = {}
    todos_los_runs: list[dict[str, Any]] = []
    metadatos_adapter: dict[str, Any] = {"source": modo}
    for offload in pedidos:
        agregado, runs = await _measure_scenario(
            args, offload=offload, factory=fabrica, warnings=avisos
        )
        agregado["_stage_keys"] = [list(r.get("stage_timings_s", {}) or {}) for r in runs]
        escenarios[agregado["scenario"]] = agregado
        todos_los_runs.extend(runs)

    if args.mock:
        sonda = MockMusicModelAdapter()
        metadatos_adapter = sonda.report_metadata()
        metadatos_adapter["generations"] = len(
            [r for r in todos_los_runs if r.get("status") == "ok"]
        )
    else:
        # C1: `source` NUNCA se hardcodea a "gpu"; refleja el modo efectivo, que
        # puede haberse degradado a mock si el adapter no vio CUDA.
        metadatos_adapter = {
            "source": modo,
            "module": str(Path(_RUNNER_ROOT) / REAL_ADAPTER_REL_PATH),
            "class": REAL_ADAPTER_CLASS,
            "backend": meta_backend.get("backend"),
            "backend_reason": meta_backend.get("backend_reason"),
            "degradado_a_mock": aviso_degradado,
            "aviso": (
                aviso_degradado
                if aviso_degradado
                else (
                    "Medicion en GPU real. El manifiesto de procedencia NO se emite en "
                    "Fase 0: lo aporta T-27 en F5 sobre el esquema firmado por legal "
                    "(D-20)."
                )
            ),
        }

    base = escenarios.get(SCENARIO_NO_OFFLOAD)
    mediana_base = (
        float(base["inference_s"]["median"]) if base and base.get("inference_s") else None
    )
    conversion = _l40s_conversion(args, baseline_median_s=mediana_base, mode=modo)
    s02 = _s02_comparison(base, mode=modo)

    criterios = _acceptance_criteria(
        args,
        mode=modo,
        environment=entorno,
        cold_start=frio,
        scenarios=escenarios,
        conversion=conversion,
    )
    for escenario in escenarios.values():
        escenario.pop("_stage_keys", None)

    payload: dict[str, Any] = {
        "task": TASK,
        "spike": SPIKE,
        "generated_at": _utc_now_iso(),
        "mode": modo,
        "adapter": metadatos_adapter,
        "cli": {
            "runs": args.runs,
            "scenarios": args.scenarios,
            "mock": args.mock,
            "duration_s": args.duration_s,
            "seed": args.seed,
            "max_gpu_seconds": args.max_gpu_seconds,
            "gpu_label": args.gpu_label,
            "l40s_inference_s": args.l40s_inference_s,
            "device": args.device,
            "dtype": args.dtype,
            "weights_dir": args.weights_dir,
            "skip_cold_start": args.skip_cold_start,
            "out": args.out,
        },
        "environment": entorno,
        "cold_start": frio,
        "scenarios": escenarios,
        "runs": todos_los_runs,
        "l40s_conversion": conversion,
        "s02_comparison": s02,
        "acceptance_criteria": criterios,
        "warnings": avisos,
        "notes": [
            "La semilla se registra por trazabilidad: no garantiza salida identica "
            "(driver, cuDNN, kernels de atencion, orden de reduccion en coma flotante).",
            "Este arnes no evalua calidad musical: eso es escucha humana (gate G1, T-09).",
            "Sin manifiesto de procedencia en Fase 0: lo aporta T-27 en F5 (D-20).",
        ],
    }

    destino = _resolve_out_path(args.out, mode=modo)
    _timing.write_json_report(destino, payload)
    _print_report(payload, destino)

    usables = sum(1 for e in escenarios.values() if e.get("completed_runs", 0) > 0)
    if usables == 0:
        print(
            "[T-03] Ninguna medicion usable: revisa los avisos del informe.",
            file=sys.stderr,
        )
        return EXIT_NO_MEASUREMENT
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return asyncio.run(_amain(args))
    except SpikeError as exc:
        print(f"\n[{TASK}] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except KeyboardInterrupt:
        print(f"\n[{TASK}] Interrumpido por el usuario.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
