"""Adapter minimo de ACE-Step 1.5 — `T-05` (Fase 0, contenerizacion minima).

Que es esto
-----------
La implementacion de `contracts.MusicModelAdapter` que corre **dentro del
contenedor** de `Dockerfile` (misma carpeta). Es el adapter que usan, en este
orden: `T-03` (tiempos, VRAM y arranque en frio), `T-04` (dos inferencias
concurrentes), `T-09` (las 10 pistas del gate **G1**) y, mucho mas adelante,
`T-85` (proveedor GPU local de produccion con la abstraccion
`GPU_PROVIDER=local|runpod|mock`, F6).

En la Fase 0 el contenedor se invoca **directo** con `docker run --gpus all`:
no existe la capa de abstraccion de proveedor (es `T-85`), ni API HTTP de
plataforma (es `T-11`), ni registry (es `T-30`). Decision del 2026-08-18
(D-29, `spec.md` confirmacion 13).

Lo que este fichero NO hace, y quien lo hace
--------------------------------------------
* **No emite manifiesto de procedencia.** `GenerationResult` no lleva
  `provenance` a proposito: el manifiesto v1 —con `manifest_schema_version`,
  `lyrics_declaration` (D-21) y el encadenado al ledger append-only— lo aporta
  **T-27 en la Fase 5 (C-10a)**, sobre el **esquema firmado por legal** (D-20).
  Emitir aqui un formato provisional obligaria a un backfill de la cadena de
  hashes, y una cadena WORM no admite backfill. Las pistas de spikes y de G1 se
  cubren con manifiesto retroactivo simplificado (S-11).
* **No normaliza loudness ni transcodifica.** El artefacto que sale de aqui es
  WAV crudo a la tasa nativa del modelo. El post-proceso —FLAC de almacen + MP3
  320 de escucha (D-09), exportacion a 48 kHz con resample soxr y objetivo de
  loudness EBU R128 por destino (D-23)— es **T-19/T-45**, no esta tarea.
* **No se registra en ningun registry ni persiste `ModelDescriptor`.** El
  descriptor completo (`weights_sha256`, `license`, `commercial_use`,
  `training_data_declaration`, `params_schema`, `limits`, `hardware`) y la suite
  de conformidad son **T-30, F5**. Aqui el modelo se invoca por nombre de
  fichero.
* **No implementa `voice`, `source_audio` ni `section_edit`.** No estan en el
  `GenerationRequest` de la Fase 0 (fases 2-4, con gate o con no-go vigente).
  `T-07` solo **mide** si ACE-Step las soporta.

Invariantes que si hace cumplir
-------------------------------
* **D-14 — solo `safetensors`**: la puerta de entrada de pesos son dos
  comprobaciones de `contracts`, en dos momentos distintos:
  `assert_safetensors()` sobre el **nombre**, **antes** de abrir el fichero, y
  `assert_safetensors_header()` sobre la **cabecera real**, **al abrirlo** en
  `load()`. La segunda es defensa en profundidad y un error temprano y claro
  (los cargadores ya rechazan un pickle renombrado), no un agujero que se cierre.
  Ningun cargador que deserialice objetos de Python (la familia `.pt`, `.bin`,
  `.ckpt`, `.pkl`, `.joblib`) toca un checkpoint: deserializar uno **ejecuta**
  el codigo que lleve dentro, es ejecucion remota de codigo (RCE). El hash de
  los pesos verifica **integridad, no inocuidad**.
* **D-15 — aislamiento de credenciales**: este proceso no lee ningun fichero de
  secretos, no escribe credenciales y no las acepta por argumento.
  `RunnerContext` no tiene campo de credencial. Toda configuracion llega por
  variables de entorno de vida corta o por argumento de linea de comandos, y las
  URLs firmadas (cuando existan, F5+) son de alcance por trabajo. El contenedor
  **no necesita red de salida** para generar: los pesos se montan como volumen.
* **D-17 — presupuesto de GPU**: el presupuesto efectivo es
  `min(req.max_gpu_seconds, ctx.max_gpu_seconds)` y se comprueba en tres puntos
  —antes de empezar, en cada paso de difusion via `on_step`, y al cerrar la
  inferencia— abortando con `GpuBudgetExceeded`.
* **D-06 / D-29 — hardware**: la VRAM se detecta al arrancar. Por debajo de los
  24 GB de confort se activa **offloading automatico** con aviso explicito de
  tiempos degradados; por debajo del suelo de 8 GB se **aborta con mensaje
  claro** (VRAM detectada y minimo exigido), nunca en silencio (`spec.md` §6).

Sobre la semilla
----------------
`req.seed` se propaga y se registra **por trazabilidad**, no como garantia de
salida identica: la difusion en GPU depende del driver, cuDNN, los kernels de
atencion y el orden de reduccion en coma flotante. Ninguna prueba debe comparar
audio bit a bit (D-13: conformidad por tolerancia perceptual).

Modo mock
---------
Con `ACE_STEP_MOCK=1` (o `--mock`), o cuando **no hay CUDA disponible**, el
adapter delega en `spikes/_mock.py`. Es lo que permite ejecutar y revisar este
fichero de punta a punta en una maquina sin GPU y **solo con la biblioteca
estandar**: todos los imports de `torch` y `safetensors` son **perezosos**,
dentro de la funcion que los necesita. Cualquier salida de este modo va marcada
con `source: "mock"` para que no se lea como una medicion.

El punto de integracion con el codigo del modelo
------------------------------------------------
La construccion del grafo del modelo y el bucle de muestreo de ACE-Step viven en
el paquete del proyecto upstream, cuya API exacta **no se ha verificado en esta
maquina** (aqui no hay ni GPU ni release descargada). En lugar de inventarla,
este adapter la aisla en **un solo punto de integracion** (`_resolve_pipeline_factory`,
configurable con `ACE_STEP_PIPELINE_FACTORY`) con un contrato de shim documentado
mas abajo. Si el shim no esta, el modo real falla con un mensaje explicito en vez
de fingir. Ese shim se cierra en la maquina con GPU, como parte de `T-03`.
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import hashlib
import importlib
import json
import logging
import os
import signal
import sys
import threading
import time
import uuid
import wave
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol

# --------------------------------------------------------------------------- #
# Arranque de sys.path
# --------------------------------------------------------------------------- #
# No hay paquete instalable ni `__init__.py`: el empaquetado del monorepo es
# `T-10`, detras del gate G1. Los modulos del cimiento (`contracts.py`,
# `spikes/_timing.py`, `spikes/_mock.py`) son modulos de nivel superior, asi que
# se anaden sus directorios a sys.path a mano y de forma robusta al cwd (el
# contenedor arranca en /app, pero un desarrollador puede lanzarlo desde
# cualquier sitio).
_HERE = Path(__file__).resolve()
_ADAPTER_DIR = _HERE.parent                 # .../adapters/ace_step
_RUNNER_ROOT = _HERE.parents[2]             # .../apps/runner
_SPIKES_DIR = _RUNNER_ROOT / "spikes"
for _ruta in (str(_ADAPTER_DIR), str(_SPIKES_DIR), str(_RUNNER_ROOT)):
    # El propio directorio del adapter entra en sys.path para que el shim del
    # modelo (`ace_step_shim.py`, que escribe T-03 con la release delante) sea
    # importable como modulo hermano sin tocar PYTHONPATH.
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import _timing  # noqa: E402  (tras el arranque de sys.path)
from contracts import (  # noqa: E402
    AudioArtifact,
    GenerationRequest,
    GenerationResult,
    GpuBudgetExceeded,
    HealthStatus,
    RunnerContext,
    RunTelemetry,
    assert_safetensors,
    assert_safetensors_header,
    assert_within_gpu_budget,
)

__all__ = [
    "AceStepAdapter",
    "RenderedAudio",
    "build_context",
    "main",
]

_LOG = logging.getLogger("ace_step.adapter")


# --------------------------------------------------------------------------- #
# Valores por defecto (todos sobreescribibles por entorno o argumento)
# --------------------------------------------------------------------------- #

#: Los pesos se **montan** como volumen, nunca viajan en la imagen (ver el
#: comentario correspondiente del `Dockerfile`): es lo que hace medible el
#: arranque en frio de `T-03` y lo que mide `T-36` mas adelante.
DEFAULT_WEIGHTS_DIR = "/weights"
DEFAULT_WEIGHTS_FILE = "ace_step_1_5.safetensors"
DEFAULT_OUTPUT_DIR = "/outputs"
#: 600 s: holgado frente a los 150 s por pista de S-02, y suficiente para que un
#: caso con offloading (que degrada de forma material) no salte el presupuesto
#: por accidente. Es un techo de seguridad (D-17), no un objetivo.
DEFAULT_MAX_GPU_SECONDS = 600
#: La superficie HTTP de `serve` es una **consola de control de la Fase 0**, no
#: la API de plataforma (`T-11`): no tiene autenticacion. Por eso escucha en
#: loopback por defecto y el `Dockerfile` documenta publicar el puerto solo en
#: `127.0.0.1`.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
#: Tope del cuerpo de una peticion HTTP. Una letra de cancion no llega ni de
#: lejos; el limite existe para no aceptar una lectura no acotada.
_MAX_BODY_BYTES = 1 << 20

#: Punto de integracion con el codigo del modelo upstream. Formato
#: `"modulo:atributo"`. El modulo por defecto es un **hermano de este fichero**
#: que aun no existe: lo escribe `T-03` en la maquina con GPU, cuando la release
#: real de ACE-Step 1.5 esta en disco y su API se puede verificar en lugar de
#: suponerla.
_PIPELINE_FACTORY_ENV = "ACE_STEP_PIPELINE_FACTORY"
_PIPELINE_FACTORY_DEFAULT = "ace_step_shim:build_pipeline"

#: Interruptor de emergencia de la lectura contigua de pesos. Existe para poder
#: reproducir el comportamiento anterior (`load_file`, ~11 MiB/s sobre el bind
#: mount) si algun dia un artefacto raro se atraganta, no porque se espere usarlo.
_CARGA_CONTIGUA_ENV = "ACE_STEP_CARGA_CONTIGUA"

#: Campos aceptados en el cuerpo JSON de `POST /generate`. Lista blanca: un
#: campo desconocido se rechaza con 400 en lugar de reventar al construir la
#: dataclass, y evita que un cliente cuele parametros no contemplados.
_CAMPOS_PETICION = frozenset(
    {
        "style_prompt",
        "duration_s",
        "max_gpu_seconds",
        "idempotency_key",
        "lyrics",
        "instrumental",
        "seed",
        "model_params",
    }
)


# --------------------------------------------------------------------------- #
# Contrato del shim del modelo (local a T-05, NO es el contrato de la spec)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class RenderedAudio:
    """Audio devuelto por el shim del modelo.

    El shim entrega **una** de las dos formas:

    * `pcm16`: PCM entrelazado de 16 bit con signo, little-endian, que este
      adapter escribe a WAV con el modulo `wave` de la biblioteca estandar.
      La conversion desde los tensores en coma flotante del modelo es
      responsabilidad del shim, que es quien tiene `torch` a mano; asi este
      fichero no necesita ni torch ni numpy para materializar el artefacto.
    * `path`: ruta a un fichero de audio que el shim ya escribio.

    `duration_s` es la duracion **real** del audio producido, no la pedida. Si el
    shim no la sabe, puede dejarla en `None` y este adapter la deduce (del PCM, o
    leyendo la cabecera del WAV). La tolerancia de ±5 % frente a la duracion
    pedida (C-01) la comprueba quien consuma el artefacto, no este adapter.
    """

    sample_rate: int
    channels: int
    duration_s: float | None = None
    pcm16: bytes | None = None
    path: str | None = None


class _AceStepPipeline(Protocol):
    """Forma que debe tener el objeto que devuelve la factoria del shim.

    Solo `render()` es obligatorio. `warmup()` y `release()` son opcionales y se
    invocan con `getattr` si existen.

    Contrato de `render()`:

    * Recibe todo por palabra clave.
    * Debe llamar a `on_step(paso, total)` en cada paso de muestreo: es el punto
      de control de **D-17**. `on_step` levanta `GpuBudgetExceeded` cuando el
      trabajo agota su presupuesto, y el shim **debe dejar propagar** esa
      excepcion (no atraparla). Un shim que ignore `on_step` degrada D-17 a una
      comprobacion al final: el trabajo desbocado se detecta, pero tarde.
    * `params` son los `model_params` de la peticion, sin interpretar por este
      adapter (no hay `params_schema` hasta `T-30`).
    """

    def render(
        self,
        *,
        style_prompt: str,
        lyrics: str | None,
        duration_s: int,
        instrumental: bool,
        seed: int | None,
        params: dict[str, Any],
        on_step: Callable[[int, int], None],
    ) -> RenderedAudio:
        ...


def _resolve_pipeline_factory() -> Callable[..., Any]:
    """Importa la factoria del shim del modelo y la devuelve.

    La factoria se invoca como
    `factory(state_dict=..., device=..., dtype=..., offload=...)` y devuelve un
    objeto conforme a `_AceStepPipeline`.

    Levanta `RuntimeError` con instrucciones si el shim no esta importable: es
    preferible un fallo explicito a inventar la API del proyecto upstream.
    """
    especificacion = os.environ.get(_PIPELINE_FACTORY_ENV, _PIPELINE_FACTORY_DEFAULT).strip()
    if ":" not in especificacion:
        raise RuntimeError(
            f"{_PIPELINE_FACTORY_ENV}={especificacion!r} mal formado. Formato esperado: "
            "'modulo:atributo' (por ejemplo 'ace_step_shim:build_pipeline')."
        )
    nombre_modulo, _, atributo = especificacion.partition(":")
    try:
        modulo = importlib.import_module(nombre_modulo)
    except ImportError as exc:
        raise RuntimeError(
            f"No se pudo importar el shim del modelo ({especificacion!r}): {exc}.\n"
            "Este adapter aisla a proposito la construccion del grafo de ACE-Step y su "
            "bucle de muestreo en un unico punto de integracion, porque la API exacta de "
            "la release upstream no se ha verificado todavia (T-05 se escribio en una "
            "maquina sin GPU y sin la release en disco). Para cerrar el modo real:\n"
            f"  1. Escribe '{nombre_modulo}.py' junto a este adapter con una funcion "
            f"'{atributo}(*, state_dict, device, dtype, offload)' que devuelva un objeto "
            "con el metodo render() documentado en _AceStepPipeline.\n"
            "  2. Fija en requirements.txt la version exacta del paquete de ACE-Step que "
            "ese shim importa.\n"
            "  3. Eso es una subtarea de T-03 (instrumentar el runner en la GPU objetivo), "
            "no de este fichero.\n"
            "Mientras tanto, el camino verificable es el modo mock: ACE_STEP_MOCK=1."
        ) from exc
    factoria = getattr(modulo, atributo, None)
    if not callable(factoria):
        raise RuntimeError(
            f"El shim {nombre_modulo!r} no expone un invocable {atributo!r}. "
            "Revisa ACE_STEP_PIPELINE_FACTORY."
        )
    return factoria


def _prefijos_residentes_gpu(factoria: Callable[..., Any]) -> tuple[str, ...]:
    """Prefijos que el shim deja residentes en VRAM, preguntandoselo AL SHIM.

    El reparto por componente es decision del shim y este adapter no la duplica:
    solo la consulta para poder leer esos bytes **directos a la tarjeta** en vez
    de darles la vuelta por RAM (3.005 MiB de pico que no caben con holgura en un
    contenedor de 7,9 GiB). Si el shim no lo declara se devuelve la tupla vacia:
    todo va a RAM y el shim lo sube como siempre; se pierde el ahorro de pico,
    no la correccion.
    """
    modulo = sys.modules.get(getattr(factoria, "__module__", "") or "")
    prefijos = getattr(modulo, "PREFIJOS_RESIDENTES_GPU", ())
    if not isinstance(prefijos, (tuple, list)) or not all(isinstance(p, str) for p in prefijos):
        _LOG.warning(
            "El shim declara PREFIJOS_RESIDENTES_GPU=%r, que no es una tupla de cadenas. "
            "Se ignora y se carga todo a RAM.",
            prefijos,
        )
        return ()
    return tuple(prefijos)


def _cargar_state_dict(
    ruta: str, factoria: Callable[..., Any], device: str, digestor: Any = None
) -> Any:
    """Lee el artefacto por tramos contiguos; cae a `load_file` SOLO si no sabe leerlo.

    La lectura contigua es la que baja `vram_load` de 709 s a ~70 s (ver el bloque
    de comentario de `_load_sync`, etapa 3). El respaldo NO es silencioso: sale
    por WARNING diciendo cuanto va a costar, porque un arranque de 12 minutos que
    nadie ha visto venir es peor que un fallo.

    El respaldo se toma unicamente ante `ArtefactoIlegible` (una disposicion del
    fichero que la lectura por tramos no contempla, o un fichero truncado: en ese
    caso `load_file` lo rechazara al instante y el aviso de «12 minutos» sera
    pesimista). Cualquier otro fallo se propaga: en particular el de «VRAM
    insuficiente», que el cargador lanza ANTES de asignar. Caer entonces a
    `load_file` y subir tensor a tensor seria ir al OOM de driver que el diseno
    prohibe, y esconder la causa real tras 12 minutos (revision 2026-09-03).
    Cambio de comportamiento respecto a la version anterior, dicho sin rodeos:
    un fallo de RAM al reservar un tramo (`torch.empty`) o un `OSError` de E/S
    tambien se propagan ahora; antes caian a `load_file`, que mapea el fichero
    sin reservar RAM por adelantado. Se acepta porque el shim materializa cada
    componente igualmente y habria reventado en el mismo sitio unos minutos mas
    tarde.

    Ninguna de las dos rutas deserializa objetos: `carga_contigua` lee la cabecera
    JSON y bytes crudos, y `load_file` es el cargador de `safetensors`. La puerta
    de entrada sigue siendo `assert_safetensors()`, ya ejecutada (D-14).
    """
    if _env_flag(_CARGA_CONTIGUA_ENV, True):
        import carga_contigua  # noqa: PLC0415  (perezoso: necesita torch)

        destinos = {}
        if str(device).startswith("cuda"):
            destinos = {p: str(device) for p in _prefijos_residentes_gpu(factoria)}
        try:
            # `digestor` (hashlib) recibe todos los bytes de paso: la integridad
            # sale gratis de la misma lectura en vez de costar un segundo recorrido.
            return carga_contigua.cargar_contiguo(ruta, destinos=destinos, digestor=digestor)
        except carga_contigua.ArtefactoIlegible as exc:
            _LOG.warning(
                "La lectura contigua de %r no sabe leer este artefacto (%r). Se vuelve a "
                "load_file(), que sobre un bind mount ha medido ~11 MiB/s: espera unos "
                "12 minutos de carga.",
                ruta,
                exc,
            )
    else:
        _LOG.warning(
            "%s desactivada por entorno: se usa load_file(), ~11 MiB/s sobre bind mount.",
            _CARGA_CONTIGUA_ENV,
        )
    from safetensors.torch import load_file  # noqa: PLC0415

    return load_file(ruta, device="cpu")


# --------------------------------------------------------------------------- #
# Utilidades de entorno (D-15: nada de ficheros de secretos)
# --------------------------------------------------------------------------- #

def _sha256_de_procedencia(ruta_pesos: str) -> tuple[str, str]:
    """(sha256 esperado, origen) leidos del `.provenance.json` hermano del artefacto.

    El fusor (`tools/build_artifact.py`) deja junto a `X.safetensors` un
    `X.provenance.json` con `artifact.sha256`. Si no existe, devuelve ("", ruta)
    para que quien llame avise. Si existe pero no se puede leer o no trae un
    SHA-256 valido, es un error: un fichero de procedencia roto no es lo mismo
    que no tener ninguno, y confundirlos dejaria pasar un artefacto sin
    verificar con aspecto de verificado.
    """
    ruta_prov = Path(ruta_pesos).with_suffix(".provenance.json")
    if not ruta_prov.is_file():
        return "", str(ruta_prov)
    try:
        documento = json.loads(ruta_prov.read_text(encoding="utf-8"))
        esperado = str(documento["artifact"]["sha256"]).strip().lower()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"El fichero de provenance {str(ruta_prov)!r} existe pero no se puede leer "
            f"o no trae artifact.sha256 ({exc!r}). No se carga un artefacto cuya "
            "procedencia esta rota."
        ) from exc
    if len(esperado) != 64 or any(c not in "0123456789abcdef" for c in esperado):
        raise RuntimeError(
            f"artifact.sha256 en {str(ruta_prov)!r} no es un SHA-256 hexadecimal: "
            f"{esperado!r}. Fichero de provenance roto."
        )
    return esperado, str(ruta_prov)


def _env_flag(nombre: str, defecto: bool = False) -> bool:
    """Lee una variable de entorno booleana ('1', 'true', 'yes', 'on')."""
    valor = os.environ.get(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in ("1", "true", "yes", "on", "si")


def _env_int(nombre: str, defecto: int) -> int:
    """Lee un entero de entorno; si no es un entero valido, avisa y usa el defecto."""
    valor = os.environ.get(nombre)
    if valor is None or not valor.strip():
        return defecto
    try:
        return int(valor.strip())
    except ValueError:
        _LOG.warning("%s=%r no es un entero; se usa %d.", nombre, valor, defecto)
        return defecto


def _env_str(nombre: str, defecto: str) -> str:
    valor = os.environ.get(nombre)
    return valor.strip() if valor and valor.strip() else defecto


def _resolver_offload_forzado() -> bool | None:
    """Lee `ACE_STEP_OFFLOAD`: `auto` (defecto) -> None, `1`/`0` -> True/False.

    `auto` deja la decision a `_timing.decide_offloading()` sobre la VRAM medida.
    Forzarlo a `0` en una GPU por debajo de 24 GB **no desactiva** el offloading
    automatico: bajar de la cifra de confort sin offloading acaba en fallo de
    memoria, y un fallo de memoria a los 4 minutos de arranque en frio es el peor
    modo de fallo posible. Solo se respeta para **activarlo** en una GPU grande
    (util para medir la degradacion de S-02 en `T-03`).
    """
    valor = os.environ.get("ACE_STEP_OFFLOAD", "auto").strip().lower()
    if valor in ("auto", ""):
        return None
    return valor in ("1", "true", "yes", "on", "si")


def build_context(
    *,
    device: str | None = None,
    dtype: str | None = None,
    weights_dir: str | None = None,
    max_gpu_seconds: int | None = None,
    offload: bool | None = None,
    backend: str = "gpu",
) -> RunnerContext:
    """Construye el `RunnerContext` desde argumentos y entorno.

    Sin credenciales, por contrato (D-15): `RunnerContext` no tiene donde
    ponerlas y este constructor no las busca en ningun sitio.
    """
    dispositivo = device or _env_str("ACE_STEP_DEVICE", "mock" if backend == "mock" else "cuda:0")
    # bfloat16 por defecto: es lo habitual para difusion en Ada/Hopper y evita el
    # escalado de perdida de fp16. La eleccion definitiva se cierra al medir en
    # T-03 (puede haber kernels que solo esten optimizados para fp16).
    precision = dtype or _env_str("ACE_STEP_DTYPE", "bfloat16")
    return RunnerContext(
        device=dispositivo,
        dtype=precision,
        offload=bool(offload) if offload is not None else bool(_resolver_offload_forzado()),
        weights_dir=weights_dir or _env_str("ACE_STEP_WEIGHTS_DIR", DEFAULT_WEIGHTS_DIR),
        max_gpu_seconds=max_gpu_seconds
        if max_gpu_seconds is not None
        else _env_int("ACE_STEP_MAX_GPU_SECONDS", DEFAULT_MAX_GPU_SECONDS),
    )


# --------------------------------------------------------------------------- #
# El adapter
# --------------------------------------------------------------------------- #

class AceStepAdapter:
    """Implementacion minima de `contracts.MusicModelAdapter` para ACE-Step 1.5.

    Args:
        weights_name: nombre del fichero de pesos dentro de `ctx.weights_dir`.
            Pasa por `assert_safetensors()` antes de abrirse (D-14).
        output_dir: directorio donde escribir el audio. Si es `None`, el
            artefacto viaja en memoria (`AudioArtifact.data`), util en spikes.
        mock: fuerza el modo mock. Si es `None`, se decide por
            `ACE_STEP_MOCK` y por la presencia de CUDA.
        require_gpu: si es `True`, la ausencia de CUDA es un **error**, no una
            excusa para caer al mock. Es lo que impide que `T-09` genere las
            pistas de G1 con audio simulado. El `Dockerfile` lo activa: un
            contenedor CUDA sin GPU es una configuracion mal hecha.
        mock_image_cached / mock_weights_cached / mock_time_scale: perillas que
            **solo** afectan al modo mock (escenarios de arranque en frio de
            `T-03`).
    """

    MODEL_ID = "ace-step"
    #: Version del modelo, no de este adapter. El descriptor completo (con
    #: `weights_sha256`, licencia **MIT** —no Apache 2.0, como decia la
    #: planificacion; corregido en T-06— y la declaracion de datos de
    #: entrenamiento de la model card) lo construye `T-30` en la F5.
    MODEL_VERSION = "1.5"

    def __init__(
        self,
        *,
        weights_name: str | None = None,
        output_dir: str | Path | None = None,
        mock: bool | None = None,
        require_gpu: bool | None = None,
        mock_image_cached: bool = True,
        mock_weights_cached: bool = True,
        mock_time_scale: float = 0.0,
    ) -> None:
        self._weights_name = weights_name or _env_str("ACE_STEP_WEIGHTS_FILE", DEFAULT_WEIGHTS_FILE)
        self._output_dir = Path(output_dir) if output_dir is not None else None
        self._require_gpu = _env_flag("ACE_STEP_REQUIRE_GPU") if require_gpu is None else require_gpu
        self._mock_image_cached = mock_image_cached
        self._mock_weights_cached = mock_weights_cached
        self._mock_time_scale = mock_time_scale

        mock_pedido = _env_flag("ACE_STEP_MOCK") if mock is None else bool(mock)
        self.backend, self.backend_reason = self._resolver_backend(mock_pedido)

        self._ctx: RunnerContext | None = None
        self._delegate: Any | None = None          # MockMusicModelAdapter en modo mock
        self._pipeline: Any | None = None          # shim del modelo en modo gpu
        self._loaded = False
        self._loading_since: float | None = None
        self._load_timings: dict[str, float] = {}
        self._offload = False
        self._offload_reason = ""
        self._gpu: dict[str, Any] | None = None
        self._generations = 0
        self._weights_path: str | None = None
        #: SHA-256 del artefacto **efectivamente contrastado** y de donde salio el
        #: valor esperado (`ACE_STEP_WEIGHTS_SHA256` o el `.provenance.json`
        #: hermano). Los rellena `_verificar_integridad()` solo cuando la
        #: comparacion cuadra; mientras valgan `None`, la identidad de los pesos
        #: NO esta verificada y `describe()` lo dice tal cual. Es lo que permite
        #: saber con que pesos exactos se genero una pista: `weights_file` es un
        #: nombre, y un nombre se renombra.
        self._weights_sha256: str | None = None
        self._weights_sha256_origen: str | None = None
        #: Motivo del ultimo `--preload` fallido en modo serve, consultable por
        #: `health()`. Lo rellena el callback del Future de `_servir()` y se
        #: limpia cuando un `load()` posterior termina bien.
        self.preload_error: str | None = None

        # -- coordinacion de ciclo de vida (M-1) ---------------------------- #
        # `load()`/`unload()` son ESCRITORES y las generaciones LECTORES: un
        # rwlock casero con un lock asyncio (escritor) mas un contador de
        # generaciones en vuelo protegido por una condicion. Garantiza que
        # unload() espera a los trabajos en vuelo, que dos load() concurrentes
        # no cargan dos veces y que ninguna generacion EMPIEZA durante un
        # load()/unload(). Las primitivas asyncio se ligan al bucle en su primer
        # await (Python >= 3.10), asi que crearlas aqui es seguro aunque el
        # bucle viva en otro hilo (modo serve).
        self._lock_ciclo = asyncio.Lock()
        self._cond_vuelo = asyncio.Condition()
        self._en_vuelo = 0
        # Contadores del lado sincrono (hilos de asyncio.to_thread): protegen
        # `self._generations` y la decision de M-4 sobre el pico de VRAM.
        self._vuelo_lock = threading.Lock()
        self._vuelo_sync = 0
        self._arranques_sync = 0

    # -- eleccion de backend ------------------------------------------------ #

    def _resolver_backend(self, mock_pedido: bool) -> tuple[str, str]:
        """Decide entre `"mock"`, `"gpu"` y `"unavailable"`, y explica por que.

        `"unavailable"` es el estado honesto de un contenedor con `require_gpu`
        que no ve CUDA: no se cae al mock en silencio (eso convertiria una
        simulacion en «resultado»), pero tampoco se revienta en el constructor,
        para que `health()` y `probe` puedan **decir** lo que pasa. `load()` es
        quien aborta (`spec.md` §6: nunca fallo silencioso).
        """
        if mock_pedido:
            return "mock", "solicitado explicitamente (--mock / ACE_STEP_MOCK=1)."
        info = _timing.gpu_info()
        if info is not None:
            self._gpu = info
            return "gpu", (
                f"CUDA detectada: {info['name']}, {info['vram_total_mb']} MB de VRAM, "
                f"{info['device_count']} dispositivo(s)."
            )
        if self._require_gpu:
            return "unavailable", (
                "No hay CUDA disponible (torch ausente, sin driver o sin GPU visible) y "
                "ACE_STEP_REQUIRE_GPU esta activo: no se cae al mock. Comprueba que el "
                "contenedor se lanzo con 'docker run --gpus all' y que el NVIDIA Container "
                "Toolkit esta instalado en el host."
            )
        return "mock", (
            "No hay CUDA disponible: se delega en el mock de spikes/_mock.py. "
            "TIEMPOS Y VRAM SIMULADOS, no medidos."
        )

    # -- ciclo de vida ------------------------------------------------------ #

    async def load(self, ctx: RunnerContext) -> None:
        """Carga los pesos y deja el modelo listo. Idempotente.

        Cubre las etapas `weights_download`, `vram_load` y `warmup` de la
        medicion de arranque en frio de `T-03`. `scheduling` e `image_pull`
        ocurren **antes** de que exista este proceso: las mide el orquestador
        desde fuera (por eso `_timing.StageTimer.add()` existe).

        El trabajo pesado se delega a un hilo con `asyncio.to_thread`, para que
        el bucle de eventos siga atendiendo `health()` durante los 2-6 minutos
        del arranque en frio. Eso es exactamente el criterio de aceptacion (c)
        de `T-05`.

        Ciclo de vida (M-1): toma el lock de escritor, asi que dos `load()`
        concurrentes se **serializan** (el segundo ve el modelo ya cargado y no
        recarga: nada de doble VRAM), y un `load()` tras `unload()` espera a que
        no quede ninguna generacion en vuelo antes de tocar el estado.
        """
        async with self._lock_ciclo:
            await self._esperar_sin_generaciones()
            if self._loaded:
                return
            if self.backend == "unavailable":
                raise RuntimeError(f"Arranque abortado. {self.backend_reason}")

            self._loading_since = time.monotonic()
            try:
                if self.backend == "mock":
                    self._delegate = self._construir_mock()
                    _LOG.warning(
                        "MODO MOCK: %s Ninguna cifra de esta ejecucion es una medicion.",
                        self.backend_reason,
                    )
                    await self._delegate.load(ctx)
                else:
                    await asyncio.to_thread(self._load_sync, ctx)
                self._ctx = ctx
                self._loaded = True
                # Un load() que termina bien invalida el motivo del preload
                # fallido anterior: health() debe dejar de reportarlo.
                self.preload_error = None
            finally:
                self._loading_since = None

    async def _esperar_sin_generaciones(self) -> None:
        """Bloquea hasta que no quede ninguna generacion en vuelo (M-1).

        Solo se llama con `_lock_ciclo` en la mano: las generaciones nuevas no
        pueden empezar (el lock las frena) y las que estan en vuelo notifican la
        condicion al terminar, asi que la espera siempre progresa.
        """
        async with self._cond_vuelo:
            await self._cond_vuelo.wait_for(lambda: self._en_vuelo == 0)

    def _construir_mock(self) -> Any:
        """Instancia el adapter mock de los spikes (import perezoso y explicito)."""
        from _mock import MockMusicModelAdapter  # noqa: PLC0415

        return MockMusicModelAdapter(
            image_cached=self._mock_image_cached,
            weights_cached=self._mock_weights_cached,
            output_dir=self._output_dir,
            time_scale=self._mock_time_scale,
            weights_name=self._weights_name,
        )

    def _load_sync(self, ctx: RunnerContext) -> None:
        """Parte sincrona y bloqueante de `load()`: GPU, pesos y warm-up."""
        timer = _timing.StageTimer()

        # 1) Hardware: detectar VRAM y decidir offloading (D-06 / D-29).
        info = self._gpu or _timing.gpu_info()
        self._gpu = info
        vram_total = info.get("vram_total_mb") if info else None
        offload_auto, motivo = _timing.decide_offloading(vram_total)
        if motivo.startswith(_timing.NOT_VIABLE_PREFIX):
            # `spec.md` §6, fila «GPU local sin VRAM suficiente»: arranque fallido
            # con mensaje claro —VRAM detectada y minimo exigido—, nunca silencioso.
            raise RuntimeError(
                f"{motivo}\nVRAM detectada: {vram_total} MB. Minimo exigido: "
                f"{_timing.VRAM_FLOOR_MB} MB (8 GB, suelo con offloading). "
                f"Cifra de confort: {_timing.VRAM_COMFORT_MB} MB (24 GB)."
            )
        forzado = _resolver_offload_forzado()
        # El offloading automatico no se puede desactivar: se puede activar de mas
        # (para medir su coste en T-03), nunca de menos.
        self._offload = bool(offload_auto or ctx.offload or forzado)
        self._offload_reason = motivo
        if self._offload:
            _LOG.warning(
                "Offloading ACTIVADO: %s Los tiempos de esta ejecucion son "
                "DEGRADADOS respecto a S-02 (150 s/pista en GPU de >= 24 GB) y no "
                "sirven como linea base sin decirlo en el informe.",
                motivo,
            )
        else:
            _LOG.info("Offloading desactivado: %s", motivo)

        # 2) Pesos: D-14 antes de tocar el fichero.
        ruta = os.path.join(ctx.weights_dir, self._weights_name)
        ruta = assert_safetensors(ruta)   # unica puerta de entrada de pesos
        # El nombre de pesos (ACE_STEP_WEIGHTS_FILE / --weights-file) no puede
        # escapar de ctx.weights_dir por path traversal ('../../...'): tras
        # resolver symlinks, el fichero tiene que seguir DENTRO del directorio.
        base_pesos = os.path.realpath(ctx.weights_dir)
        ruta_real = os.path.realpath(ruta)
        try:
            fuera = os.path.commonpath([base_pesos, ruta_real]) != base_pesos
        except ValueError:  # unidades distintas (Windows) o rutas incomparables
            fuera = True
        if fuera:
            raise RuntimeError(
                f"Ruta de pesos fuera del directorio permitido: {self._weights_name!r} "
                f"resuelve a {ruta_real!r}, fuera de {base_pesos!r}. El nombre de "
                "pesos (ACE_STEP_WEIGHTS_FILE / --weights-file) debe apuntar a un "
                "fichero DENTRO de ctx.weights_dir."
            )
        self._weights_path = ruta
        # Una carga nueva parte sin identidad verificada: si esta apunta a otro
        # fichero (o a uno que no se llega a contrastar), heredar el hash de la
        # carga anterior publicaria una identidad que no corresponde a
        # `weights_path`.
        self._weights_sha256 = None
        self._weights_sha256_origen = None
        with timer.stage("weights_download"):
            # En este contenedor los pesos llegan **montados** como volumen, asi que
            # esta etapa mide la comprobacion local (y el hash, si se pide), no una
            # descarga. En el pod de RunPod sin volumen caliente si es una descarga
            # real de ~7 GB: ese es el termino que `T-03` mide contra S-01 y el que
            # `T-36` optimiza mas adelante.
            if not os.path.isfile(ruta):
                raise FileNotFoundError(
                    f"No existe el fichero de pesos {ruta!r}. Se esperan los pesos "
                    f"montados en {ctx.weights_dir!r} (por ejemplo "
                    f"'-v /ruta/host/pesos:{DEFAULT_WEIGHTS_DIR}:ro'): la imagen no los "
                    "incluye a proposito."
                )
            # Primera vez que se ABRE el fichero: aqui se comprueba la cabecera
            # real, ya que el nombre se valido antes (`assert_safetensors`, con
            # el fichero aun sin tocar). Cuesta 8 bytes mas la cabecera JSON y
            # convierte un artefacto que no es lo que dice su extension en un
            # error inmediato y legible, en vez de un fallo mas oscuro dentro
            # del cargador varios minutos despues (D-14, defensa en profundidad:
            # ni la lectura contigua ni `load_file` deserializan objetos).
            assert_safetensors_header(ruta)
            # Solo se RESUELVE que hash se espera; el calculo va de paso en la
            # lectura contigua de la etapa 3 y se compara alli.
            hash_esperado = self._hash_esperado(ruta)

        # 3) Carga del artefacto. Imports perezosos: en la maquina de desarrollo
        #    no hay torch, y este fichero tiene que poder importarse igualmente.
        #    M-5: si cualquiera de las etapas 3-4 falla, se limpia el estado
        #    parcial (pipeline con pesos en VRAM, state_dict huerfano) y se
        #    relanza la excepcion original: un load() fallido deja el adapter
        #    descargado, consistente y reintentable.
        #
        # POR QUE EL ARTEFACTO SE LEE POR TRAMOS CONTIGUOS (2026-09-02, segunda vuelta)
        # -----------------------------------------------------------------------
        # Historia corta de esta linea, que ha cambiado dos veces el mismo dia:
        #
        #   1. `load_file(ruta, device=ctx.device)` — el artefacto ENTERO aterrizaba
        #      en VRAM antes de que el shim pudiera opinar. Con el planificador de
        #      5 Hz dentro (7.180 MiB) ya NO CABE en 8 GB: reventaba antes de
        #      ejecutar una linea del shim.
        #   2. `load_file(ruta, device="cpu")` — arreglaba el pico de VRAM (el shim
        #      pasa a decidir componente a componente) pero **no** el tiempo:
        #      `load_file` mapea el fichero y el coste real se paga despues, cuando
        #      el shim toca cada tensor. Sobre el bind mount de Docker eso son
        #      fallos de pagina de 4 KiB a 11 MiB/s MEDIDOS, o sea 709,08 s de
        #      `vram_load`: 12 minutos que rompen la promesa de arranque en frio de
        #      2-6 min de `ui-design.md` antes de escribirla en codigo.
        #   3. Lo de ahora: `carga_contigua.cargar_contiguo()`. Los tensores de un
        #      safetensors estan uno detras de otro, asi que se lee el rango entero
        #      de cada tramo de una vez (`readinto`) y los tensores son vistas de
        #      ese buffer. MEDIDO en el mismo contenedor: 118,8 MiB/s de media, once
        #      veces la tasa por tensor y ya al nivel del disco fisico (141-144 MiB/s
        #      leyendo desde Windows fuera de Docker).
        #
        # A/B completo, misma orden y misma pista de 25 s (2026-09-02, GTX 1070):
        #
        #                        load_file    contigua
        #     vram_load            642,0 s      72,9 s
        #     warm-up               39,1 s      36,8 s
        #     ARRANQUE EN FRIO     681,1 s     109,7 s
        #     generacion 25 s      127,8 s     110,6 s
        #
        # La generacion sale mas rapida, y no por casualidad: los buffers de la
        # lectura contigua los reserva el asignador de PyTorch, alineados a 64
        # bytes. Con `bytearray` (que devuelve pagina+16) la misma carga daba
        # 86,7 MiB/s y el warm-up subia a 80,0 s, porque el planificador de 5 Hz
        # corre en CPU y sus kernels vectorizados pagan la desalineacion.
        #
        # Lo que NO cambia, y es deliberado:
        #   * El reparto por componente lo sigue decidiendo EL SHIM. Aqui solo se
        #     le dice al cargador que `dit.decoder` acabara en VRAM para leerlo
        #     directo a la tarjeta y ahorrarse 3.005 MiB de pico en RAM; ese dato
        #     se toma del propio shim (`PREFIJOS_RESIDENTES_GPU`), no se duplica.
        #   * El pico de VRAM durante la construccion sigue siendo lo que el shim
        #     residencia (`dit.decoder`, 3.005 MiB), y el pico de una GENERACION
        #     sigue siendo el condicionamiento (6.190 MiB medidos).
        #   * Los tensores llegan MATERIALIZADOS en memoria anonima, que es lo que
        #     el shim conseguia clonando: un tensor respaldado por el mapeo del
        #     fichero se relee pagina a pagina en cada subida a VRAM (42,91 s
        #     frente a 0,43 s). Ahora el shim ve `tensores_materializados` y se
        #     ahorra tambien esos clones.
        #
        # M-5: si cualquiera de las etapas 3-4 falla, se limpia el estado parcial
        # (pipeline con pesos en VRAM, state_dict huerfano) y se relanza la
        # excepcion original: un load() fallido deja el adapter descargado,
        # consistente y reintentable.
        state_dict: Any = None
        try:
            with timer.stage("vram_load"):
                import torch  # noqa: PLC0415  (perezoso a proposito)

                try:
                    torch.cuda.reset_peak_memory_stats()
                except Exception:  # noqa: BLE001  (una GPU rara no debe tumbar la carga)
                    _LOG.debug("No se pudo reiniciar el contador de pico de VRAM.")
                # La factoria se resuelve ANTES de leer ~7 GB de pesos: el fallo
                # tipico (shim ausente) no debe dejar un state_dict huerfano.
                factoria = _resolve_pipeline_factory()
                digestor = hashlib.sha256() if hash_esperado else None
                state_dict = _cargar_state_dict(ruta, factoria, ctx.device, digestor=digestor)
                if hash_esperado:
                    # Si la carga fue por el respaldo (`load_file`), no hay hash de
                    # paso y `_verificar_integridad` recorre el fichero.
                    self._verificar_integridad(
                        ruta,
                        obtenido=getattr(state_dict, "sha256", None),
                        esperado=hash_esperado,
                    )
                self._pipeline = factoria(
                    state_dict=state_dict,
                    device=ctx.device,
                    dtype=ctx.dtype,
                    offload=self._offload,
                )
                # El diccionario de pesos ya vive dentro del pipeline: soltar la
                # referencia local evita mantener viva una copia (y, con el mapeo
                # en CPU, el propio mapeo del fichero).
                state_dict = None

            # 4) Warm-up: primera pasada en vacio y compilacion de kernels. Es un
            #    termino de 30-120 s del arranque en frio (S-01), no un detalle.
            with timer.stage("warmup"):
                calentar = getattr(self._pipeline, "warmup", None)
                if callable(calentar):
                    calentar()
                else:
                    _LOG.info(
                        "El shim no expone warmup(): el coste de compilacion de kernels se "
                        "pagara en la primera inferencia y contaminara su medicion."
                    )
        except BaseException:
            state_dict = None
            self._limpiar_carga_fallida()
            raise

        self._load_timings = timer.timings
        _LOG.info(
            "Modelo listo. Etapas de carga (s): %s",
            {k: round(v, 2) for k, v in self._load_timings.items()},
        )

    def _hash_esperado(self, ruta: str) -> tuple[str, str] | None:
        """(sha256 esperado, origen), o `None` si no hay nada que comparar.

        Cuando devuelve `None` ya ha avisado por el log del motivo (salto
        explicito o ausencia de fuente). De donde sale el hash esperado, por orden:

        1. `ACE_STEP_WEIGHTS_SHA256`, si esta definida (manda siempre).
        2. El `<artefacto>.provenance.json` hermano que escribe el fusor
           (`artifact.sha256`). Es el caso normal: el lanzador no tiene que
           acordarse de nada (revision 2026-09-03, hallazgo I-1: `generar.cmd`
           no exportaba la variable y las pistas salian sin verificar).
        3. Ninguno: se AVISA de que la integridad no se ha verificado.

        `ACE_STEP_SKIP_INTEGRITY=1` salta la comprobacion avisando; existe solo
        para la medicion de arranque en frio de `T-03`, a la que recorrer ~7 GB
        le contaminaria el numero.

        Verifica **integridad, no inocuidad**: un fichero manipulado con hash
        correcto sigue siendo el fichero que alguien puso ahi. Lo que hace segura
        la carga es el formato (`safetensors`, D-14), no el hash.
        """
        if _env_flag("ACE_STEP_SKIP_INTEGRITY"):
            _LOG.warning(
                "Integridad de pesos NO verificada: ACE_STEP_SKIP_INTEGRITY esta activo. "
                "Solo es legitimo para medir el arranque en frio (T-03)."
            )
            return None
        esperado = os.environ.get("ACE_STEP_WEIGHTS_SHA256", "").strip().lower()
        origen = "ACE_STEP_WEIGHTS_SHA256"
        if not esperado:
            esperado, origen = _sha256_de_procedencia(ruta)
        if not esperado:
            _LOG.warning(
                "Integridad de pesos NO verificada: ni ACE_STEP_WEIGHTS_SHA256 ni %s. "
                "El artefacto se carga tal cual esta en disco.",
                origen,
            )
            return None
        return esperado, origen

    def _verificar_integridad(
        self,
        ruta: str,
        obtenido: str | None = None,
        esperado: tuple[str, str] | None = None,
    ) -> None:
        """Compara el SHA-256 de los pesos con el esperado y aborta si difieren.

        `obtenido`: hash ya calculado (normalmente de paso en la lectura contigua,
        `EstadoDelArtefacto.sha256`). Si es `None`, se recorre el fichero entero,
        que sobre el bind mount son ~217 s por 7,5 GB: es el camino de respaldo,
        no el normal. `esperado`: lo que devolvio `_hash_esperado`; si es `None`
        se resuelve aqui, y si no hay nada que comparar se sale sin error.
        """
        if esperado is None:
            esperado = self._hash_esperado(ruta)
            if esperado is None:
                return
        valor, origen = esperado
        inicio = time.perf_counter()
        if obtenido is None:
            digestor = hashlib.sha256()
            with open(ruta, "rb") as fichero:
                for bloque in iter(lambda: fichero.read(8 * 1024 * 1024), b""):
                    digestor.update(bloque)
            obtenido = digestor.hexdigest()
            como = "recorriendo el fichero"
        else:
            como = "calculado de paso en la carga"
        if obtenido != valor:
            raise RuntimeError(
                f"Integridad de pesos fallida en {ruta!r}: SHA-256 {obtenido} frente al "
                f"esperado {valor} (segun {origen}). El arranque se aborta."
            )
        # Identidad real del artefacto, para que `describe()` la publique. Se
        # guarda SOLO aqui, en el unico camino en que la comparacion ha cuadrado:
        # si se salto la comprobacion o no habia con que comparar, se sale antes
        # y el campo sigue en `None` —ausencia de dato, no cadena vacia.
        self._weights_sha256 = obtenido
        self._weights_sha256_origen = origen
        _LOG.info(
            "Integridad de pesos verificada (SHA-256 %s..., segun %s, %s, %.1f s).",
            obtenido[:16],
            origen,
            como,
            time.perf_counter() - inicio,
        )

    def _limpiar_carga_fallida(self) -> None:
        """Deja el adapter descargado y sin VRAM retenida tras un `load()` fallido (M-5).

        Libera el pipeline a medio construir (via `release()` del shim, si lo
        expone), suelta las referencias, vacia la cache de CUDA y reinicia el
        contador de pico. Se llama desde el hilo de `_load_sync`, con el lock de
        ciclo de vida ya en la mano (lo tiene `load()`).
        """
        pipeline, self._pipeline = self._pipeline, None
        if pipeline is not None:
            liberar = getattr(pipeline, "release", None)
            if callable(liberar):
                try:
                    liberar()
                except Exception as exc:  # noqa: BLE001
                    _LOG.warning(
                        "El shim fallo al liberar recursos tras un load() fallido "
                        "(se ignora): %r",
                        exc,
                    )
            del pipeline
        self._loaded = False
        self._ctx = None
        self._load_timings = {}
        # Sin carga vigente no hay identidad de pesos que publicar: un load()
        # fallido no puede dejar en `describe()` un hash con aspecto de bueno.
        self._weights_sha256 = None
        self._weights_sha256_origen = None
        gc.collect()
        torch = sys.modules.get("torch")
        if torch is not None:
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    _LOG.info("VRAM liberada tras load() fallido: el adapter queda reintentable.")
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("No se pudo vaciar la cache de CUDA (se ignora): %r", exc)

    async def unload(self) -> None:
        """Libera pesos y VRAM. Idempotente y segura tras un `load()` fallido.

        Vacia de verdad la cache de CUDA y reinicia el contador de pico, que es
        lo que permite a `T-03` medir el pico de ejecuciones sucesivas sin
        contaminacion entre ellas. Deja el adapter **reutilizable**: tras
        `unload()`, `load()` vuelve a funcionar.

        Ciclo de vida (M-1): toma el lock de escritor y **espera a que terminen
        las generaciones en vuelo** antes de liberar nada. Ninguna generacion
        nueva puede empezar mientras tanto.
        """
        async with self._lock_ciclo:
            await self._esperar_sin_generaciones()
            await self._unload_interno()

    async def _unload_interno(self) -> None:
        """Cuerpo de `unload()`, ya con el lock de ciclo de vida en la mano."""
        if self._delegate is not None:
            try:
                await self._delegate.unload()
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("Fallo al descargar el mock (se ignora): %r", exc)
            self._delegate = None

        pipeline, self._pipeline = self._pipeline, None
        self._loaded = False
        self._ctx = None
        self._load_timings = {}
        self._loading_since = None

        if pipeline is not None:
            liberar = getattr(pipeline, "release", None)
            if callable(liberar):
                try:
                    liberar()
                except Exception as exc:  # noqa: BLE001
                    _LOG.warning("El shim fallo al liberar recursos (se ignora): %r", exc)
            del pipeline

        gc.collect()
        # Se consulta `sys.modules` en lugar de importar torch: en una maquina sin
        # torch, `unload()` no debe fallar ni intentar importarlo solo para vaciar
        # una cache que no existe.
        torch = sys.modules.get("torch")
        if torch is not None:
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    _LOG.info("Cache de CUDA vaciada y contador de pico reiniciado.")
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("No se pudo vaciar la cache de CUDA (se ignora): %r", exc)

    # -- generacion --------------------------------------------------------- #

    async def generate(self, req: GenerationRequest) -> GenerationResult:
        """Genera audio a partir de la peticion.

        `req` ya viene validada por `GenerationRequest.__post_init__` (prompt no
        vacio, duracion y presupuesto positivos, clave de idempotencia presente,
        y la contradiccion `instrumental=True` con letra rechazada).

        El resultado **no** lleva `provenance`: lo completa `T-27` en la F5, con
        el esquema de manifiesto firmado por legal (D-20).

        Ciclo de vida (M-1): se registra como "lector" bajo el lock de ciclo de
        vida antes de empezar, asi que una generacion no puede arrancar mientras
        un `load()`/`unload()` esta en curso, y `unload()` espera a que las que
        estan en vuelo terminen.
        """
        # Fallo rapido sin esperar al lock: durante un arranque en frio de 2-6
        # min la respuesta correcta es "sin load() previo", no un bloqueo mudo.
        if self._delegate is None and (
            not self._loaded or self._ctx is None or self._pipeline is None
        ):
            raise RuntimeError(
                "generate() sin load() previo: el contrato de MusicModelAdapter exige "
                "cargar el modelo antes de generar."
            )
        async with self._lock_ciclo:
            # Revalidacion bajo el lock: un unload() concurrente pudo colarse
            # entre el fallo rapido de arriba y la toma del lock.
            delegado = self._delegate
            if delegado is None and (
                not self._loaded or self._ctx is None or self._pipeline is None
            ):
                raise RuntimeError(
                    "generate() sin load() previo: el contrato de MusicModelAdapter "
                    "exige cargar el modelo antes de generar."
                )
            async with self._cond_vuelo:
                self._en_vuelo += 1
        try:
            if delegado is not None:
                return await delegado.generate(req)
            return await asyncio.to_thread(self._generate_sync, req)
        finally:
            async with self._cond_vuelo:
                self._en_vuelo -= 1
                self._cond_vuelo.notify_all()

    def _generate_sync(self, req: GenerationRequest) -> GenerationResult:
        """Parte sincrona y bloqueante de `generate()`.

        Contrato de telemetria (M-3): `gpu_seconds` y `stage_timings` del
        resultado cubren SOLO esta generacion (la etapa `inference`). El coste
        del arranque (`weights_download`, `vram_load`, `warmup`) se paga una vez
        por carga y se reporta aparte (`load_gpu_seconds` /
        `load_stage_timings_s` en `describe()`), nunca repetido en cada run.
        Para el presupuesto de D-17 el arranque SI se sigue sumando: el trabajo
        retuvo la tarjeta durante esas etapas.
        """
        assert self._ctx is not None and self._pipeline is not None  # garantizado arriba
        ctx = self._ctx

        # D-17: el presupuesto efectivo es el MENOR de los dos techos. Una peticion
        # no puede pedir mas GPU de la que el runner concede.
        presupuesto = min(req.max_gpu_seconds, ctx.max_gpu_seconds)

        # Los segundos de GPU ya consumidos por el arranque (carga a VRAM y
        # warm-up) cuentan para el PRESUPUESTO: son etapas en las que el trabajo
        # retiene la tarjeta (`_timing.GPU_STAGES`). No cuentan, en cambio, para
        # los `gpu_seconds` reportados de esta generacion (M-3).
        gpu_previo = self.load_gpu_seconds()
        assert_within_gpu_budget(
            gpu_previo,
            presupuesto,
            detail="Consumido en carga a VRAM y warm-up, antes de empezar la inferencia.",
        )

        # M-4: el contador de pico de torch.cuda es GLOBAL al proceso.
        # Reiniciarlo con otra generacion en vuelo invalidaria el pico de la
        # concurrente, asi que solo se reinicia cuando esta generacion esta
        # sola; si hubo concurrencia en cualquier momento del run, el pico no es
        # atribuible a esta inferencia y `vram_peak_mb` sale como None (dato
        # ausente, nunca un numero falso). El pico simultaneo real de T-04 se
        # lee del sistema (`nvidia-smi --query-gpu=memory.used`), no de aqui.
        with self._vuelo_lock:
            self._vuelo_sync += 1
            self._arranques_sync += 1
            sin_concurrencia = self._vuelo_sync == 1
            marca_arranques = self._arranques_sync
        try:
            torch = sys.modules.get("torch")
            if torch is not None and sin_concurrencia:
                try:
                    # Pico por generacion: se reinicia aqui para que `vram_peak_mb`
                    # sea el de ESTA inferencia y no arrastre el de la carga ni el
                    # de la anterior.
                    torch.cuda.reset_peak_memory_stats()
                except Exception:  # noqa: BLE001
                    _LOG.debug("No se pudo reiniciar el contador de pico de VRAM.")

            timer = _timing.StageTimer()
            inicio = time.perf_counter()

            def on_step(paso: int, total: int) -> None:
                """Punto de control de D-17 dentro del bucle de muestreo."""
                assert_within_gpu_budget(
                    gpu_previo + (time.perf_counter() - inicio),
                    presupuesto,
                    detail=f"Abortado en el paso de muestreo {paso}/{total}.",
                )

            _LOG.info(
                "Generando: %d s pedidos, semilla=%s, instrumental=%s, presupuesto=%d s de GPU.",
                req.duration_s,
                req.seed,
                req.instrumental,
                presupuesto,
            )
            with timer.stage("inference"):
                rendered = self._pipeline.render(
                    style_prompt=req.style_prompt,
                    lyrics=req.lyrics,
                    duration_s=req.duration_s,
                    instrumental=req.instrumental,
                    # Se propaga por TRAZABILIDAD: no promete salida identica (D-13).
                    seed=req.seed,
                    params=dict(req.model_params),
                    on_step=on_step,
                )

            gpu_inferencia = timer.total_s(("inference",))
            # Ultima red de seguridad: si el shim ignoro `on_step`, este es el unico
            # punto donde D-17 se aplica. Se valida ANTES de materializar: un trabajo
            # fuera de presupuesto **no** se entrega y no debe dejar un WAV huerfano
            # en disco.
            assert_within_gpu_budget(
                gpu_previo + gpu_inferencia,
                presupuesto,
                detail="Detectado al cerrar la inferencia (el shim no llamo a on_step, o lo ignoro).",
            )
            artefacto = self._materializar(req, rendered)

            with self._vuelo_lock:
                # M-4: el pico solo es fiable si esta generacion estuvo SOLA de
                # principio a fin (nadie en vuelo al empezar y ningun arranque
                # nuevo mientras corria).
                pico_fiable = sin_concurrencia and self._arranques_sync == marca_arranques
                self._generations += 1
            pico = _timing.vram_snapshot_mb() if pico_fiable else None
            vram_peak_mb = pico[2] if pico is not None else None
            if not pico_fiable:
                _LOG.warning(
                    "vram_peak_mb=None: hubo generaciones concurrentes en este proceso "
                    "y el contador de pico de torch.cuda no distingue cual reservo que. "
                    "El pico simultaneo se mide desde el sistema (T-04)."
                )

            telemetria = RunTelemetry(
                # SOLO esta generacion (M-3): el coste de carga va aparte, en
                # `load_gpu_seconds`, pagado una vez.
                gpu_seconds=round(gpu_inferencia, 3),
                vram_peak_mb=vram_peak_mb,
                # Los reintentos los cuenta el orquestador de la cola (F5), no el adapter:
                # aqui una ejecucion es una ejecucion.
                retries=0,
                offloading_enabled=self._offload,
                stage_timings={k: round(v, 3) for k, v in timer.timings.items()},
            )
            # GenerationResult sin `provenance`: lo completa T-27 en F5 (D-20).
            return GenerationResult(artifacts=[artefacto], telemetry=telemetria)
        finally:
            with self._vuelo_lock:
                self._vuelo_sync -= 1

    def _materializar(self, req: GenerationRequest, rendered: Any) -> AudioArtifact:
        """Convierte lo que devuelve el shim en un `AudioArtifact`.

        El formato es **WAV** porque es lo unico que se puede escribir con la
        biblioteca estandar (modulo `wave`) y porque en la Fase 0 el consumidor es
        una escucha humana (G1), no el almacen. FLAC de almacen + MP3 320 de
        escucha (D-09) y la exportacion a 48 kHz con loudness por destino (D-23)
        son post-proceso: `T-19`/`T-45`.
        """
        sample_rate = int(getattr(rendered, "sample_rate", 0) or 0)
        channels = int(getattr(rendered, "channels", 0) or 0)
        pcm16 = getattr(rendered, "pcm16", None)
        ruta_shim = getattr(rendered, "path", None)
        if sample_rate <= 0 or channels <= 0:
            raise RuntimeError(
                "El shim devolvio 'sample_rate' o 'channels' invalidos: "
                f"sample_rate={sample_rate!r}, channels={channels!r}. Revisa el contrato "
                "de RenderedAudio."
            )
        if (pcm16 is None) == (ruta_shim is None):
            raise RuntimeError(
                "El shim debe devolver exactamente uno de 'pcm16' o 'path' "
                "(se recibieron ambos, o ninguno)."
            )

        duracion = getattr(rendered, "duration_s", None)

        if ruta_shim is not None:
            destino = Path(ruta_shim)
            if duracion is None:
                duracion = self._duracion_de_wav(destino) or float(req.duration_s)
            return AudioArtifact(
                format="wav",
                sample_rate=sample_rate,
                channels=channels,
                duration_s=float(duracion),
                size_bytes=destino.stat().st_size,
                path=str(destino),
            )

        if len(pcm16) == 0:
            # Se comprueba sobre los BYTES, no sobre la duracion declarada: un shim
            # que declare duration_s > 0 con un buffer vacio no debe colar un WAV
            # sin audio como entregable.
            raise RuntimeError(
                "El shim devolvio audio vacio: 'pcm16' no contiene ni una muestra "
                "pese al contrato de RenderedAudio. No hay audio que entregar."
            )
        marcos = len(pcm16) // (channels * 2)  # 2 bytes por muestra (16 bit)
        if duracion is None:
            duracion = marcos / float(sample_rate)
        if duracion <= 0:
            raise RuntimeError(
                "El shim devolvio un PCM vacio: no hay audio que entregar "
                f"({len(pcm16)} bytes)."
            )

        if self._output_dir is None:
            # Sin directorio de salida el artefacto viaja en memoria. Comodo para
            # los spikes; para las pistas de G1 (`T-09`) hay que escribir a disco.
            return AudioArtifact(
                format="wav",
                sample_rate=sample_rate,
                channels=channels,
                duration_s=float(duracion),
                size_bytes=len(pcm16),
                data=pcm16,
            )

        self._output_dir.mkdir(parents=True, exist_ok=True)
        etiqueta = _slug(req.idempotency_key)
        destino = self._output_dir / f"{etiqueta}.wav"
        with wave.open(str(destino), "wb") as salida:
            salida.setnchannels(channels)
            salida.setsampwidth(2)
            salida.setframerate(sample_rate)
            salida.writeframes(pcm16)
        _LOG.info("Audio escrito en %s (%.1f s).", destino, duracion)
        return AudioArtifact(
            format="wav",
            sample_rate=sample_rate,
            channels=channels,
            duration_s=float(duracion),
            size_bytes=destino.stat().st_size,
            path=str(destino),
        )

    @staticmethod
    def _duracion_de_wav(ruta: Path) -> float | None:
        """Duracion real leida de la cabecera del WAV, o `None` si no se puede."""
        try:
            with wave.open(str(ruta), "rb") as entrada:
                marcos = entrada.getnframes()
                tasa = entrada.getframerate()
            return marcos / float(tasa) if tasa else None
        except Exception:  # noqa: BLE001  (no es un WAV, o esta truncado)
            return None

    # -- salud -------------------------------------------------------------- #

    async def health(self) -> HealthStatus:
        """Estado del adapter. **Nunca lanza excepcion** (contrato).

        Responde tambien —y sobre todo— mientras el modelo **no** esta listo: es
        la sonda con la que `T-03` cierra la medicion de arranque en frio y la que
        decide si el contenedor acepta trabajo. Como `load()` corre en un hilo,
        esta corrutina contesta durante los 2-6 minutos del arranque en frio, e
        indica cuantos segundos lleva.
        """
        try:
            if self._delegate is not None:
                return await self._delegate.health()

            if self.backend == "unavailable":
                return HealthStatus(ready=False, detail=self.backend_reason)

            if self._loading_since is not None:
                transcurrido = time.monotonic() - self._loading_since
                return HealthStatus(
                    ready=False,
                    detail=(
                        f"Arranque en frio en curso: {transcurrido:.0f} s. Rango esperado "
                        "2-6 min con imagen de contenedor cacheada, 5-12 min sin cachear "
                        "(S-01). No es un fallo: no hay barra de progreso porque no hay "
                        "progreso real que reportar todavia."
                    ),
                    **self._vram_para_health(),
                )

            if not self._loaded or self._ctx is None:
                # M-2: un --preload fallido no puede desaparecer sin rastro; su
                # motivo queda consultable aqui hasta que un load() termine bien.
                preload = (
                    f" PRELOAD FALLIDO: {self.preload_error}." if self.preload_error else ""
                )
                return HealthStatus(
                    ready=False,
                    detail=(
                        f"'{self.MODEL_ID}@{self.MODEL_VERSION}' sin cargar: llama a "
                        f"load(ctx) (o POST /load) antes de generar. Backend: "
                        f"{self.backend} — {self.backend_reason}{preload}"
                    ),
                    **self._vram_para_health(),
                )

            return HealthStatus(
                ready=True,
                detail=(
                    f"'{self.MODEL_ID}@{self.MODEL_VERSION}' listo en {self._ctx.device} "
                    f"(dtype={self._ctx.dtype}, offloading={self._offload}, "
                    f"generaciones={self._generations}). "
                    f"{'TIEMPOS DEGRADADOS por offloading. ' if self._offload else ''}"
                    f"Pesos: {self._weights_path}"
                ),
                **self._vram_para_health(),
            )
        except Exception as exc:  # noqa: BLE001  (health() no puede lanzar)
            return HealthStatus(
                ready=False,
                detail=f"health() capturo un fallo inesperado: {exc!r}",
            )

    def _vram_para_health(self) -> dict[str, int | None]:
        """VRAM total y libre para `HealthStatus`, o `None` si no hay CUDA."""
        pico = _timing.vram_snapshot_mb()
        if pico is None:
            return {"vram_total_mb": None, "vram_free_mb": None}
        total, usado, _ = pico
        return {"vram_total_mb": total, "vram_free_mb": max(total - usado, 0)}

    # -- utilidades de informe --------------------------------------------- #

    def load_stage_timings(self) -> dict[str, float]:
        """Etapas del arranque (`weights_download`, `vram_load`, `warmup`...).

        Contrato M-3: este coste se paga **una vez** por carga del modelo y se
        reporta aqui, aparte; los `stage_timings` de cada generacion ya no lo
        repiten. En modo mock delega en los tiempos simulados del mock.
        """
        if self._delegate is not None:
            metodo = getattr(self._delegate, "load_stage_timings", None)
            if callable(metodo):
                return dict(metodo())
            return {}
        return dict(self._load_timings)

    def load_gpu_seconds(self) -> float:
        """Segundos de GPU del arranque (vram_load + warmup), pagados UNA vez.

        Es el termino de arranque del presupuesto de D-17: visible en informes y
        salud, pero fuera de los `gpu_seconds` de cada generacion (M-3).
        """
        return sum(
            v
            for k, v in self.load_stage_timings().items()
            if k in _timing.GPU_STAGES and k != "inference"
        )

    def describe(self) -> dict[str, Any]:
        """Cabecera para el informe JSON de un spike.

        Lleva `source` de forma explicita (`"gpu"` o `"mock"`): es la marca que
        impide que una simulacion se lea como medicion de `T-03`. En modo mock
        incorpora tambien `report_metadata()` del mock.

        Desde M-3 lleva tambien el coste del arranque (`load_stage_timings_s` y
        `load_gpu_seconds`), que se paga una vez por carga y ya no viaja en la
        telemetria de cada generacion.

        Identidad de los pesos
        ----------------------
        `weights_sha256` es el hash **contrastado** en la ultima carga que lo
        verifico, y `weights_sha256_origen` dice quien aporto el valor esperado
        (`ACE_STEP_WEIGHTS_SHA256` o el `.provenance.json` hermano). Ambos son
        `None` —nunca cadena vacia ni un hash calculado aqui por compromiso—
        cuando no hubo verificacion: sin fuente con que comparar, con
        `ACE_STEP_SKIP_INTEGRITY=1`, o antes del primer `load()`. Que sean `None`
        significa exactamente eso: *nadie ha contrastado este artefacto*.
        Sobreviven a `unload()`, igual que `weights_path`, porque un informe se
        escribe a menudo con el modelo ya descargado. Verifican **integridad, no
        inocuidad**: lo que hace segura la carga es el formato (D-14).

        NO se publica la variante de pesos (`turbo` / `sft`), y no por olvido: el
        adapter no puede saberla sin inventarsela. Los dos checkpoints tienen las
        mismas claves con las mismas formas, asi que no se deduce del artefacto;
        `ACE_STEP_VARIANTE` solo fija la que usa el **warm-up** del shim; y cada
        peticion trae la suya en `model_params["variante"]`, asi que ni siquiera
        hay una unica variante por carga. Publicar aqui un valor por defecto
        seria una etiqueta que un informe leeria como hecho medido.
        """
        info: dict[str, Any] = {
            "tarea": "T-05",
            "source": "mock" if self.backend == "mock" else self.backend,
            "backend_reason": self.backend_reason,
            "model_id": self.MODEL_ID,
            "model_version": self.MODEL_VERSION,
            "weights_file": self._weights_name,
            "weights_path": self._weights_path,
            # Identidad real del artefacto: `None` mientras nadie la haya
            # contrastado (ver el docstring). El nombre de fichero no identifica
            # nada, se renombra; el hash verificado si.
            "weights_sha256": self._weights_sha256,
            "weights_sha256_origen": self._weights_sha256_origen,
            "offloading_enabled": self._offload,
            "offloading_reason": self._offload_reason,
            "gpu": self._gpu,
            "generations": self._generations,
            # Coste del arranque, pagado UNA vez por carga (contrato M-3): no se
            # repite en gpu_seconds ni en stage_timings de cada generacion.
            "load_stage_timings_s": {
                k: round(v, 3) for k, v in self.load_stage_timings().items()
            },
            "load_gpu_seconds": round(self.load_gpu_seconds(), 3),
            "writes_audio": self._output_dir is not None,
            "no_incluye": [
                "variante de pesos (turbo/sft): no se deduce del artefacto (mismas "
                "claves y formas) y cada peticion trae la suya en model_params",
                "provenance / manifiesto (T-27, F5, esquema firmado por legal — D-20)",
                "loudness y transcode FLAC/MP3/48 kHz (T-19 / T-45)",
                "registry y ModelDescriptor persistido (T-30, F5)",
                "abstraccion GPU_PROVIDER local|runpod|mock (T-85, F6)",
            ],
        }
        if self._delegate is not None:
            info["mock"] = self._delegate.report_metadata()
        return info

    def probe(self) -> dict[str, Any]:
        """Diagnostico de hardware sin cargar pesos. Util al arrancar y en `T-03`."""
        gpu = self._gpu or _timing.gpu_info()
        vram_total = gpu.get("vram_total_mb") if gpu else None
        offload, motivo = _timing.decide_offloading(vram_total)
        pico = _timing.vram_snapshot_mb()
        return {
            "backend": self.backend,
            "backend_reason": self.backend_reason,
            "gpu": gpu,
            "vram_snapshot_mb": (
                {"total": pico[0], "used": pico[1], "peak": pico[2]} if pico else None
            ),
            "offloading_recomendado": offload,
            "offloading_motivo": motivo,
            "viable": not motivo.startswith(_timing.NOT_VIABLE_PREFIX),
            "umbrales_mb": {
                "suelo": _timing.VRAM_FLOOR_MB,
                "confort": _timing.VRAM_COMFORT_MB,
                "referencia_l40s": _timing.VRAM_REFERENCE_L40S_MB,
            },
        }


def _slug(texto: str, limite: int = 64) -> str:
    """Nombre de fichero seguro y **sin colisiones** a partir de una cadena arbitraria.

    Ademas de sanear caracteres, incorpora un hash corto (8 hex de SHA-256) del
    texto ORIGINAL: dos claves de idempotencia distintas que saneen o trunquen
    igual (`"a b"` y `"a-b"`, claves largas con el mismo prefijo) no deben acabar
    sobrescribiendose el WAV en silencio.
    """
    limpio = "".join(c if c.isalnum() or c in "-_" else "-" for c in texto).strip("-")
    marca = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:8]
    return f"{(limpio or 'generacion')[:limite]}-{marca}"


# --------------------------------------------------------------------------- #
# Superficie HTTP de control (modo `serve`)
# --------------------------------------------------------------------------- #
# ATENCION: esta NO es la API de la plataforma (`T-11`, POST /generations con
# autenticacion, declaracion de derechos de la letra y cola). Es una consola de
# control minima de la Fase 0, **sin autenticacion**, cuyo unico proposito es
# mantener los pesos cargados entre generaciones: sin ella, `T-09` pagaria 2-6
# min de arranque en frio por cada una de las 10 pistas de G1. Por eso escucha en
# loopback por defecto y el `Dockerfile` documenta publicar el puerto solo en
# `127.0.0.1`. No exponerla a una red no confiable.

class _ControlServer(ThreadingHTTPServer):
    """Servidor con las referencias que necesita el handler."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        direccion: tuple[str, int],
        adapter: AceStepAdapter,
        loop: asyncio.AbstractEventLoop,
        ctx: RunnerContext,
        ranuras: threading.BoundedSemaphore,
    ) -> None:
        super().__init__(direccion, _ControlHandler)
        self.adapter = adapter
        self.loop = loop
        self.ctx = ctx
        self.ranuras = ranuras


class _ControlHandler(BaseHTTPRequestHandler):
    """Rutas: `GET /health`, `GET /describe`, `GET /probe`,
    `POST /load`, `POST /generate`, `POST /unload`."""

    server_version = "AceStepRunner/0.1"
    protocol_version = "HTTP/1.1"

    # -- infraestructura ---------------------------------------------------- #

    def log_message(self, formato: str, *args: Any) -> None:  # noqa: D102
        _LOG.info("http %s - %s", self.address_string(), formato % args)

    def _responder(self, codigo: int, cuerpo: dict[str, Any]) -> None:
        datos = json.dumps(cuerpo, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _leer_json(self) -> dict[str, Any]:
        longitud = int(self.headers.get("Content-Length") or 0)
        if longitud > _MAX_BODY_BYTES:
            raise ValueError(
                f"Cuerpo demasiado grande ({longitud} bytes); el tope es {_MAX_BODY_BYTES}."
            )
        if longitud <= 0:
            return {}
        crudo = self.rfile.read(longitud)
        datos = json.loads(crudo.decode("utf-8"))
        if not isinstance(datos, dict):
            raise ValueError("Se esperaba un objeto JSON en el cuerpo de la peticion.")
        return datos

    def _esperar(self, corrutina: Any, timeout: float | None = None) -> Any:
        """Ejecuta una corrutina del adapter en el bucle de eventos del proceso."""
        servidor: _ControlServer = self.server  # type: ignore[assignment]
        futuro = asyncio.run_coroutine_threadsafe(corrutina, servidor.loop)
        return futuro.result(timeout)

    # -- rutas -------------------------------------------------------------- #

    def do_GET(self) -> None:  # noqa: N802  (nombre impuesto por http.server)
        servidor: _ControlServer = self.server  # type: ignore[assignment]
        ruta = self.path.split("?", 1)[0].rstrip("/") or "/"
        try:
            if ruta in ("/", "/health"):
                estado = self._esperar(servidor.adapter.health(), timeout=30)
                # Siempre 200: el codigo de salida de `healthcheck` es quien decide
                # si el contenedor esta sano, leyendo el campo `ready`. Un 503
                # durante el arranque en frio ensuciaria los logs sin aportar nada.
                self._responder(
                    200,
                    {
                        "ready": estado.ready,
                        "detail": estado.detail,
                        "vram_total_mb": estado.vram_total_mb,
                        "vram_free_mb": estado.vram_free_mb,
                    },
                )
            elif ruta == "/describe":
                self._responder(200, servidor.adapter.describe())
            elif ruta == "/probe":
                self._responder(200, servidor.adapter.probe())
            else:
                self._responder(404, {"error": "ruta_desconocida", "path": ruta})
        except Exception as exc:  # noqa: BLE001
            _LOG.exception("Fallo atendiendo GET %s", ruta)
            self._responder(500, {"error": "fallo_interno", "detail": repr(exc)})

    def do_POST(self) -> None:  # noqa: N802
        """`POST /load`, `POST /unload` y `POST /generate`.

        Ciclo de vida (M-1): `load()` y `unload()` toman el lock de escritor del
        adapter, asi que **`/unload` espera a que terminen las generaciones en
        vuelo** antes de liberar nada, `/load` es idempotente y serializado (dos
        `/load` concurrentes no cargan el modelo dos veces ni duplican VRAM), y
        ninguna generacion puede empezar mientras un load/unload esta en curso.
        Un `/load` fallido devuelve 500 con el motivo y deja el adapter limpio y
        reintentable (M-5).
        """
        servidor: _ControlServer = self.server  # type: ignore[assignment]
        ruta = self.path.split("?", 1)[0].rstrip("/") or "/"
        try:
            if ruta == "/load":
                try:
                    self._esperar(servidor.adapter.load(servidor.ctx), timeout=None)
                except Exception as exc:  # noqa: BLE001
                    # M-5: el propio load() ya limpio el estado parcial; aqui solo
                    # se devuelve el motivo para que el operador reintente.
                    _LOG.exception("POST /load fallo")
                    self._responder(
                        500,
                        {
                            "error": "load_fallido",
                            "detail": (
                                f"{exc} El adapter queda descargado y limpio: "
                                "corrige la causa y reintenta POST /load."
                            ),
                        },
                    )
                    return
                self._responder(200, {"ok": True, "detail": "load() completado."})
            elif ruta == "/unload":
                self._esperar(servidor.adapter.unload(), timeout=None)
                self._responder(
                    200,
                    {
                        "ok": True,
                        "detail": (
                            "unload() completado (espero a las generaciones en vuelo)."
                        ),
                    },
                )
            elif ruta == "/generate":
                self._generar(servidor)
            else:
                self._responder(404, {"error": "ruta_desconocida", "path": ruta})
        except ValueError as exc:
            self._responder(400, {"error": "peticion_invalida", "detail": str(exc)})
        except GpuBudgetExceeded as exc:
            self._responder(
                422,
                {
                    "error": "gpu_budget_exceeded",
                    "detail": str(exc),
                    "elapsed_s": exc.elapsed_s,
                    "max_gpu_seconds": exc.max_gpu_seconds,
                },
            )
        except RuntimeError as exc:
            self._responder(409, {"error": "estado_invalido", "detail": str(exc)})
        except Exception as exc:  # noqa: BLE001
            _LOG.exception("Fallo atendiendo POST %s", ruta)
            self._responder(500, {"error": "fallo_interno", "detail": repr(exc)})

    def _generar(self, servidor: _ControlServer) -> None:
        cuerpo = self._leer_json()
        req = _peticion_desde_json(cuerpo, servidor.ctx)
        # Una GPU, un trabajo, salvo que se suba `--max-concurrency` a proposito
        # (eso es justamente lo que mide `T-04`).
        if not servidor.ranuras.acquire(blocking=False):
            self._responder(
                503,
                {
                    "error": "ocupado",
                    "detail": "No hay ranura de inferencia libre. Reintenta o sube "
                    "--max-concurrency (T-04 mide si la GPU aguanta dos a la vez).",
                },
            )
            return
        try:
            resultado = self._esperar(servidor.adapter.generate(req), timeout=None)
        finally:
            servidor.ranuras.release()
        self._responder(200, _informe(servidor.adapter, servidor.ctx, req, resultado))


def _peticion_desde_json(cuerpo: dict[str, Any], ctx: RunnerContext) -> GenerationRequest:
    """Construye un `GenerationRequest` desde JSON con lista blanca de campos."""
    desconocidos = sorted(set(cuerpo) - _CAMPOS_PETICION)
    if desconocidos:
        raise ValueError(
            f"Campos no reconocidos: {', '.join(desconocidos)}. Aceptados: "
            f"{', '.join(sorted(_CAMPOS_PETICION))}. Los campos 'voice', 'source_audio' y "
            "'section_edit' son de fases posteriores y no existen en la Fase 0."
        )
    datos = dict(cuerpo)
    datos.setdefault("duration_s", 180)
    datos.setdefault("max_gpu_seconds", ctx.max_gpu_seconds)
    # Sufijo aleatorio corto: dos peticiones sin clave en el mismo segundo no
    # deben compartir clave de idempotencia (colisionarian en el nombre del WAV).
    datos.setdefault(
        "idempotency_key", f"t05-http-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    )
    if "style_prompt" not in datos:
        raise ValueError("'style_prompt' es obligatorio.")
    try:
        return GenerationRequest(**datos)  # su __post_init__ valida el resto
    except TypeError as exc:
        raise ValueError(f"Peticion mal formada: {exc}") from exc


def _informe(
    adapter: AceStepAdapter,
    ctx: RunnerContext,
    req: GenerationRequest,
    resultado: GenerationResult,
) -> dict[str, Any]:
    """Informe JSON de una generacion, listo para volcar o devolver por HTTP."""
    return {
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "adapter": adapter.describe(),
        "contexto": {
            "device": ctx.device,
            "dtype": ctx.dtype,
            "offload_solicitado": ctx.offload,
            "weights_dir": ctx.weights_dir,
            "max_gpu_seconds": ctx.max_gpu_seconds,
        },
        "peticion": {
            "style_prompt": req.style_prompt,
            "duration_s": req.duration_s,
            "max_gpu_seconds": req.max_gpu_seconds,
            "idempotency_key": req.idempotency_key,
            "instrumental": req.instrumental,
            "tiene_letra": req.lyrics is not None,
            # La semilla se registra por TRAZABILIDAD; no garantiza salida identica.
            "seed": req.seed,
            "model_params": req.model_params,
        },
        "telemetria": {
            # Contrato M-3: cubre SOLO esta generacion; el arranque va aparte.
            "gpu_seconds": resultado.telemetry.gpu_seconds,
            "vram_peak_mb": resultado.telemetry.vram_peak_mb,
            "retries": resultado.telemetry.retries,
            "offloading_enabled": resultado.telemetry.offloading_enabled,
            "stage_timings_s": resultado.telemetry.stage_timings,
        },
        "arranque": {
            "load_stage_timings_s": {
                k: round(v, 3) for k, v in adapter.load_stage_timings().items()
            },
            "load_gpu_seconds": round(adapter.load_gpu_seconds(), 3),
            "nota": (
                "Coste del arranque (carga a VRAM y warm-up), pagado UNA vez por "
                "carga del modelo (M-3): cuenta para el presupuesto de D-17 pero "
                "no se repite en la telemetria de cada generacion."
            ),
        },
        "artefactos": [
            {
                "format": a.format,
                "sample_rate": a.sample_rate,
                "channels": a.channels,
                "duration_s": a.duration_s,
                "size_bytes": a.size_bytes,
                "path": a.path,
                "en_memoria": a.data is not None,
            }
            for a in resultado.artifacts
        ],
        "provenance": None,
        "provenance_nota": (
            "Ausente a proposito: el manifiesto de procedencia v1 lo aporta T-27 en la "
            "Fase 5 (C-10a), sobre el esquema firmado por legal (D-20). Las pistas de "
            "spikes y de G1 se cubren con manifiesto retroactivo simplificado (S-11)."
        ),
    }


def _servir(args: argparse.Namespace) -> int:
    """Modo `serve`: mantiene el modelo cargado y atiende la consola de control."""
    adapter = _adapter_desde_args(args)
    ctx = _contexto_desde_args(args, adapter)

    # El adapter es async; el servidor HTTP de la biblioteca estandar es de hilos.
    # Un unico bucle de eventos en su propio hilo une las dos mitades y, sobre
    # todo, permite que `GET /health` conteste mientras `load()` esta en vuelo.
    loop = asyncio.new_event_loop()
    hilo_loop = threading.Thread(target=loop.run_forever, name="ace-step-loop", daemon=True)
    hilo_loop.start()

    ranuras = threading.BoundedSemaphore(max(1, args.max_concurrency))
    servidor = _ControlServer((args.host, args.port), adapter, loop, ctx, ranuras)
    _LOG.info(
        "Consola de control en http://%s:%d (backend=%s, concurrencia=%d). "
        "Sin autenticacion: no exponer fuera de loopback (la API de plataforma es T-11).",
        args.host,
        args.port,
        adapter.backend,
        args.max_concurrency,
    )

    def apagar(signum: int, _marco: Any) -> None:
        # SIGTERM de `docker stop`: hay que liberar la VRAM antes de morir, o el
        # siguiente contenedor arranca sobre una tarjeta ocupada.
        _LOG.info("Senal %s recibida: apagando.", signum)
        threading.Thread(target=servidor.shutdown, daemon=True).start()

    for senal in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(senal, apagar)
        except (ValueError, OSError):  # pragma: no cover  (hilo secundario o Windows)
            _LOG.debug("No se pudo instalar el manejador de %s.", senal)

    try:
        if args.preload:
            # Se lanza sin esperar: el servidor debe atender `/health` durante el
            # arranque en frio (2-6 min cacheado, 5-12 min sin cachear — S-01).
            futuro_preload = asyncio.run_coroutine_threadsafe(adapter.load(ctx), loop)

            def _al_terminar_preload(futuro: Any) -> None:
                # M-2: un fallo de --preload (pesos ausentes, VRAM insuficiente,
                # hash incorrecto) no puede desaparecer en silencio: se loguea por
                # stderr con el mensaje completo y queda consultable en /health.
                try:
                    exc = futuro.exception()
                except Exception as raro:  # noqa: BLE001  (p. ej. CancelledError)
                    exc = raro
                if exc is None:
                    return
                mensaje = f"{type(exc).__name__}: {exc}"
                adapter.preload_error = mensaje
                _LOG.error(
                    "--preload fallo: %s. El servidor sigue vivo; corrige la causa "
                    "y reintenta con POST /load (el motivo queda en GET /health).",
                    mensaje,
                )

            futuro_preload.add_done_callback(_al_terminar_preload)
        servidor.serve_forever(poll_interval=0.5)
    finally:
        servidor.server_close()
        try:
            asyncio.run_coroutine_threadsafe(adapter.unload(), loop).result(timeout=60)
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("unload() al apagar no termino limpio: %r", exc)
        loop.call_soon_threadsafe(loop.stop)
        hilo_loop.join(timeout=10)
    return 0


def _healthcheck(args: argparse.Namespace) -> int:
    """Modo `healthcheck`: sonda HTTP local para el `HEALTHCHECK` del Dockerfile.

    Sale con 0 solo si el adapter reporta `ready=True`. Usa `urllib` de la
    biblioteca estandar para no meter `curl` en la imagen (menos superficie y
    menos bytes que descargar en el arranque en frio).
    """
    import urllib.error  # noqa: PLC0415
    import urllib.request  # noqa: PLC0415

    url = args.url or f"http://127.0.0.1:{args.port}/health"
    try:
        with urllib.request.urlopen(url, timeout=args.timeout) as respuesta:  # noqa: S310
            datos = json.loads(respuesta.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"no-listo: la sonda {url} fallo: {exc!r}", file=sys.stderr)
        return 1
    listo = bool(datos.get("ready"))
    print(f"{'listo' if listo else 'no-listo'}: {datos.get('detail', '')}")
    return 0 if listo else 1


def _probe(args: argparse.Namespace) -> int:
    """Modo `probe`: diagnostico de GPU/VRAM sin cargar pesos."""
    adapter = _adapter_desde_args(args)
    diagnostico = adapter.probe()  # una sola sonda: imprimir y decidir sobre lo mismo
    print(json.dumps(diagnostico, ensure_ascii=False, indent=2))
    return 0 if diagnostico["viable"] or adapter.backend == "mock" else 1


def _generar_una(args: argparse.Namespace) -> int:
    """Modo `generate`: one-shot para los spikes (`T-03`, `T-04`, `T-09`).

    Carga, genera una pista, descarga y vuelca el informe JSON. Es el modo que
    usan los spikes cuando quieren un proceso por generacion (que es lo que
    `T-04` necesita para medir dos inferencias en paralelo de verdad).
    """
    adapter = _adapter_desde_args(args)
    ctx = _contexto_desde_args(args, adapter)

    letra: str | None = args.lyrics
    if args.lyrics_file:
        letra = Path(args.lyrics_file).read_text(encoding="utf-8")
    if args.instrumental:
        # `GenerationRequest` rechaza instrumental con letra; se avisa en lugar de
        # dejar que la peticion falle por un flag olvidado.
        if letra:
            _LOG.warning("--instrumental ignora la letra proporcionada.")
        letra = None

    req = GenerationRequest(
        style_prompt=args.style,
        duration_s=args.duration,
        max_gpu_seconds=args.max_gpu_seconds or ctx.max_gpu_seconds,
        idempotency_key=args.idempotency_key
        or f"t05-oneshot-{int(time.time())}-{uuid.uuid4().hex[:8]}",
        lyrics=letra,
        instrumental=args.instrumental,
        seed=args.seed,
        model_params=_parsear_params(args.param),
    )

    async def ejecutar() -> dict[str, Any]:
        await adapter.load(ctx)
        estado = await adapter.health()
        _LOG.info("health() tras la carga: ready=%s — %s", estado.ready, estado.detail)
        try:
            resultado = await adapter.generate(req)
            # El informe se arma ANTES de descargar: unload() borra los tiempos de
            # carga y el bloque `arranque` del informe (M-3) los necesita.
            return _informe(adapter, ctx, req, resultado)
        finally:
            await adapter.unload()

    try:
        informe = asyncio.run(ejecutar())
    except GpuBudgetExceeded as exc:
        # D-17 funcionando: no es un error del programa, es el tope actuando.
        print(json.dumps({"error": "gpu_budget_exceeded", "detail": str(exc)}, indent=2))
        return 2
    informe["health_final"] = "unload() ejecutado; el adapter queda reutilizable."
    salida = json.dumps(informe, ensure_ascii=False, indent=2)
    print(salida)
    if args.report:
        destino = _timing.write_json_report(args.report, informe)
        _LOG.info("Informe escrito en %s", destino)
    return 0


def _parsear_params(pares: list[str] | None) -> dict[str, Any]:
    """Convierte `--param clave=valor` en `model_params`.

    El valor se interpreta como JSON si se puede (`8`, `true`, `[1,2]`) y como
    cadena si no. No se valida contra ningun esquema: `params_schema` llega con
    el `ModelDescriptor` de `T-30`.
    """
    resultado: dict[str, Any] = {}
    for par in pares or []:
        if "=" not in par:
            raise ValueError(f"--param espera 'clave=valor'; recibido {par!r}.")
        clave, _, valor = par.partition("=")
        try:
            resultado[clave.strip()] = json.loads(valor)
        except json.JSONDecodeError:
            resultado[clave.strip()] = valor
    return resultado


# --------------------------------------------------------------------------- #
# Linea de comandos
# --------------------------------------------------------------------------- #

def _adapter_desde_args(args: argparse.Namespace) -> AceStepAdapter:
    salida = None if getattr(args, "no_write", False) else getattr(args, "output_dir", None)
    return AceStepAdapter(
        weights_name=args.weights_file,
        output_dir=salida,
        mock=True if args.mock else None,
        require_gpu=True if args.require_gpu else None,
        mock_image_cached=not getattr(args, "mock_no_image_cache", False),
        mock_weights_cached=not getattr(args, "mock_no_weights_cache", False),
        mock_time_scale=getattr(args, "mock_time_scale", 0.0),
    )


def _contexto_desde_args(args: argparse.Namespace, adapter: AceStepAdapter) -> RunnerContext:
    offload = {"auto": None, "on": True, "off": False}[args.offload]
    return build_context(
        device=args.device,
        dtype=args.dtype,
        weights_dir=args.weights_dir,
        max_gpu_seconds=getattr(args, "max_gpu_seconds", None) or None,
        offload=offload,
        backend=adapter.backend,
    )


def _parser() -> argparse.ArgumentParser:
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--mock", action="store_true", help="Fuerza el modo mock (= ACE_STEP_MOCK=1).")
    comun.add_argument(
        "--require-gpu",
        action="store_true",
        help="La ausencia de CUDA es un error, no una caida al mock (usalo en T-09).",
    )
    comun.add_argument("--weights-dir", default=None, help=f"Defecto: {DEFAULT_WEIGHTS_DIR}")
    comun.add_argument("--weights-file", default=None, help=f"Defecto: {DEFAULT_WEIGHTS_FILE}")
    comun.add_argument("--device", default=None, help="Defecto: cuda:0 (mock: 'mock').")
    comun.add_argument("--dtype", default=None, help="Defecto: bfloat16.")
    comun.add_argument(
        "--offload",
        choices=("auto", "on", "off"),
        default="auto",
        help="auto decide por VRAM (D-06). 'off' NO desactiva el offloading automatico.",
    )
    comun.add_argument(
        "--max-gpu-seconds",
        type=int,
        default=None,
        help=f"Techo de segundos de GPU del runner (D-17). Defecto: {DEFAULT_MAX_GPU_SECONDS}.",
    )
    comun.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING, ERROR.")
    mock = comun.add_argument_group("modo mock (sin efecto con GPU real)")
    mock.add_argument("--mock-no-image-cache", action="store_true",
                      help="Simula el arranque en frio sin imagen cacheada (S-01b).")
    mock.add_argument("--mock-no-weights-cache", action="store_true",
                      help="Simula la descarga de pesos.")
    mock.add_argument("--mock-time-scale", type=float, default=0.0,
                      help="Fraccion de los tiempos simulados que se espera de verdad.")

    parser = argparse.ArgumentParser(
        prog="adapter.py",
        description=(
            "Adapter minimo de ACE-Step 1.5 (T-05, Fase 0). Dos modos utiles: 'serve' "
            "mantiene el modelo cargado y atiende una consola de control local; "
            "'generate' hace un one-shot para los spikes. Sin manifiesto de procedencia "
            "(T-27, F5), sin loudness ni transcode (T-19/T-45), sin registry (T-30) y sin "
            "la abstraccion GPU_PROVIDER (T-85)."
        ),
        epilog=(
            "Invariantes: solo safetensors (D-14), sin credenciales persistentes (D-15), "
            "presupuesto de GPU por trabajo (D-17), offloading automatico por debajo de "
            "24 GB con aviso de tiempos degradados (D-06/D-29)."
        ),
    )
    sub = parser.add_subparsers(dest="modo", required=True)

    p_serve = sub.add_parser("serve", parents=[comun], help="Sirve el adapter (modo por defecto del contenedor).")
    p_serve.add_argument("--host", default=_env_str("ACE_STEP_HOST", DEFAULT_HOST))
    p_serve.add_argument("--port", type=int, default=_env_int("ACE_STEP_PORT", DEFAULT_PORT))
    p_serve.add_argument("--preload", action="store_true", default=True,
                         help="Carga el modelo al arrancar (por defecto).")
    p_serve.add_argument("--no-preload", dest="preload", action="store_false",
                         help="Espera un POST /load explicito.")
    p_serve.add_argument("--max-concurrency", type=int, default=1,
                         help="Inferencias simultaneas permitidas (T-04 mide si >1 es viable).")
    p_serve.add_argument("--output-dir", default=_env_str("ACE_STEP_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
    p_serve.set_defaults(func=_servir)

    p_gen = sub.add_parser("generate", parents=[comun], help="One-shot de generacion para los spikes.")
    p_gen.add_argument("--style", default="pop electronico melancolico, tempo medio, voz femenina",
                       help="Prompt de estilo.")
    p_gen.add_argument("--lyrics", default=None, help="Letra en linea.")
    p_gen.add_argument("--lyrics-file", default=None, help="Fichero UTF-8 con la letra.")
    p_gen.add_argument("--duration", type=int, default=180, help="Duracion pedida en segundos.")
    p_gen.add_argument("--instrumental", action="store_true", help="Sin voz (ignora la letra).")
    p_gen.add_argument("--seed", type=int, default=None,
                       help="Se registra por trazabilidad; NO garantiza salida identica (D-13).")
    p_gen.add_argument("--idempotency-key", default=None)
    p_gen.add_argument("--output-dir", default=_env_str("ACE_STEP_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
    p_gen.add_argument("--no-write", action="store_true",
                       help="No escribe audio en disco; el artefacto viaja en memoria.")
    p_gen.add_argument("--report", default=None, help="Ruta del informe JSON a escribir.")
    p_gen.add_argument("--param", action="append", default=None, metavar="CLAVE=VALOR",
                       help="model_params sin interpretar (params_schema es T-30).")
    p_gen.set_defaults(func=_generar_una)

    p_probe = sub.add_parser("probe", parents=[comun], help="Diagnostico de GPU/VRAM sin cargar pesos.")
    p_probe.set_defaults(func=_probe)

    p_hc = sub.add_parser("healthcheck", help="Sonda del HEALTHCHECK del contenedor.")
    p_hc.add_argument("--url", default=None, help="Defecto: http://127.0.0.1:<port>/health")
    p_hc.add_argument("--port", type=int, default=_env_int("ACE_STEP_PORT", DEFAULT_PORT))
    p_hc.add_argument("--timeout", type=float, default=10.0)
    p_hc.add_argument("--log-level", default="WARNING")
    p_hc.set_defaults(func=_healthcheck)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del `ENTRYPOINT` del contenedor."""
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        # A stderr y sin secretos: los logs del runner acaban en el recolector del
        # host y no deben llevar nada sensible (D-15).
        stream=sys.stderr,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        # Puerto ocupado o sin permisos en `serve` (y resto de fallos de E/S,
        # FileNotFoundError incluido): mensaje claro y el mismo codigo de salida
        # que los demas fallos esperables, nunca traza cruda.
        _LOG.error(
            "Fallo de E/S: %s. Si es 'Address already in use', hay otro proceso "
            "escuchando en ese puerto: cambia --port o para el otro runner.",
            exc,
        )
        return 1
    except (GpuBudgetExceeded, RuntimeError, ValueError) as exc:
        # Fallos esperables (presupuesto, VRAM insuficiente, pesos ausentes, formato
        # de pesos rechazado): mensaje claro y codigo de salida, nunca traza cruda.
        _LOG.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
