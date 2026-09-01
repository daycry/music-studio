"""Contrato minimo del adapter de modelo musical — Fase 0 (spikes de viabilidad).

Este modulo es la superficie compartida por los tres spikes de la Fase 0 (`T-03`
tiempos/VRAM/arranque en frio, `T-04` concurrencia, `T-05` contenerizacion minima
de ACE-Step 1.5). Es una **version reducida a proposito** del contrato de la
`spec.md` §3.3.

Que NO esta aqui, y quien lo aporta
-----------------------------------
* `ModelDescriptor` completo (`id`, `version`, `weights_uri`, `weights_format`,
  `weights_sha256`, `license`, `commercial_use`, `training_data_declaration`,
  `capabilities`, `params_schema`, `limits`, `hardware`, `status`) — lo construye
  **T-30 en la Fase 5**, junto con el registry y la suite de conformidad. En la
  Fase 0 el adapter no se registra: se invoca directo.
* `ProvenanceRecord` / manifiesto de procedencia v1 (`manifest_schema_version`,
  `lyrics_declaration` D-21, `source_generation` D-22, cadena de hashes del
  ledger) — lo aporta **T-27 en la Fase 5 (C-10a)**, y su esquema **lo firma
  legal antes de implementarse** (D-20). Por eso `GenerationResult` de este
  modulo **no** lleva `provenance`: emitir un formato que legal no ha firmado
  seria peor que no emitirlo. La regla 4 del contrato (`provenance` obligatorio)
  entra en vigor con T-27, no aqui.
* Capacidades diferidas de la peticion: `voice: VoiceSpec` (condicionamiento de
  timbre), `source_audio: AudioRef` (cover / remezcla / continuacion) y
  `section_edit: SectionEdit` (inpaint de un tramo). Son alcance de las Fases 2-3
  (C-07/C-08, bloqueadas por gate) y de la Fase 4 (no-go vigente para clonacion
  de voz). `T-07` solo **mide** si ACE-Step las soporta; no las implementa.
* La **declaracion de derechos de la letra** (D-21) es un bloqueo duro de la API
  (`POST /generations`, T-11), no del adapter: sin ella no se encola nada. Aqui
  no aparece porque en la Fase 0 no hay API.

Dependencias
------------
Solo biblioteca estandar (`dataclasses`, `enum`, `typing`). **Nada de pydantic**:
la `spec.md` §3.3 lo usa porque describe el contrato definitivo, que vive dentro
del monorepo; el monorepo y sus dependencias son `T-10` en adelante, detras del
gate **G1**. Los spikes tienen que poder ejecutarse con un Python limpio.

Invariantes de seguridad que este modulo si hace cumplir
--------------------------------------------------------
* **D-14 — solo `safetensors`**: `assert_safetensors()` valida la ruta de pesos y
  levanta `UnsafeWeightsFormat` en cualquier otro caso. Jamas `pickle`,
  `torch.load`, `joblib`, `dill`, `np.load(allow_pickle=True)` ni `yaml.load`
  sin `SafeLoader` sobre checkpoints no confiables: es ejecucion remota de
  codigo. `weights_sha256` verifica **integridad, no inocuidad**.
* **D-15 — aislamiento de credenciales**: `RunnerContext` no tiene ni un campo
  de credencial, a proposito. El runner recibe URLs firmadas de alcance por
  trabajo y caducidad corta por entorno de vida corta, nunca ficheros de
  secretos, y no persiste nada.
* **D-17 — presupuesto de GPU**: `GenerationRequest.max_gpu_seconds` es
  obligatorio y `assert_within_gpu_budget()` aborta con `GpuBudgetExceeded`.

Nota sobre la semilla
---------------------
`GenerationRequest.seed` se registra **por trazabilidad**, no como garantia de
salida identica: la difusion en GPU depende del driver, cuDNN, los kernels de
atencion y el orden de reduccion en coma flotante. Ninguna prueba debe comparar
audio bit a bit (D-13: la conformidad es por tolerancia perceptual).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Protocol, runtime_checkable

__all__ = [
    "SAFETENSORS_SUFFIX",
    "AudioFormat",
    "ModelCapability",
    "AudioArtifact",
    "GenerationRequest",
    "RunTelemetry",
    "GenerationResult",
    "HealthStatus",
    "RunnerContext",
    "MusicModelAdapter",
    "GpuBudgetExceeded",
    "UnsafeWeightsFormat",
    "assert_safetensors",
    "assert_within_gpu_budget",
]

#: Unica extension de pesos aceptada (D-14).
SAFETENSORS_SUFFIX = ".safetensors"

#: Formatos de artefacto de audio del contrato. FLAC es el formato de almacen y
#: MP3 320 la copia de escucha (D-09); WAV es **exportacion a demanda** y siempre
#: a 48 kHz con resample soxr (D-23).
AudioFormat = Literal["flac", "mp3", "wav"]


# --------------------------------------------------------------------------- #
# Excepciones
# --------------------------------------------------------------------------- #

class UnsafeWeightsFormat(Exception):
    """Se intento cargar pesos en un formato que no es `safetensors` (D-14)."""


class GpuBudgetExceeded(Exception):
    """El trabajo agoto su presupuesto de segundos de GPU (D-17).

    Lleva las dos cifras como atributos para que el runner las registre en
    telemetria sin volver a calcularlas.
    """

    def __init__(self, elapsed_s: float, max_gpu_seconds: int, detail: str = "") -> None:
        self.elapsed_s = float(elapsed_s)
        self.max_gpu_seconds = int(max_gpu_seconds)
        mensaje = (
            f"Presupuesto de GPU excedido (D-17): {self.elapsed_s:.1f} s consumidos "
            f"frente a max_gpu_seconds={self.max_gpu_seconds}. El trabajo se aborta."
        )
        if detail:
            mensaje = f"{mensaje} {detail}"
        super().__init__(mensaje)


# --------------------------------------------------------------------------- #
# Validadores de invariantes
# --------------------------------------------------------------------------- #

def assert_safetensors(path: str | os.PathLike[str]) -> str:
    """Valida que `path` apunta a un fichero `.safetensors` (D-14).

    Es la unica puerta de entrada de pesos del runner. No comprueba que el
    fichero exista ni que su hash cuadre —eso es `weights_sha256`, integridad—:
    comprueba el **formato**, que es lo que decide si cargarlo puede ejecutar
    codigo arbitrario.

    Devuelve la ruta tal cual se recibio (normalizada a `str`) para poder
    encadenar la llamada en el punto de carga.

    Levanta:
        UnsafeWeightsFormat: si la ruta no termina en `.safetensors`, si esta
            vacia, si el nombre de fichero es solo la extension, o si termina en
            separador de directorio (un directorio no es un fichero de pesos, y
            aceptar `pesos.safetensors/` abriria la puerta a que dentro haya
            cualquier cosa).
    """
    raw = os.fspath(path)
    if raw.endswith(("/", "\\")):
        raise UnsafeWeightsFormat(
            f"Ruta de pesos con separador final: {raw!r}. Se espera un FICHERO "
            f"'{SAFETENSORS_SUFFIX}', no un directorio: el formato de lo que hay "
            "dentro de un directorio no se puede validar por el nombre, y cargar un "
            "pickle desde ahi seria ejecucion remota de codigo (RCE) igualmente (D-14)."
        )
    if not raw or not raw.strip():
        raise UnsafeWeightsFormat(
            "Ruta de pesos vacia. Solo se aceptan ficheros '.safetensors' (D-14): "
            "cargar un checkpoint en pickle (torch.load, joblib, dill, "
            "np.load(allow_pickle=True)) ejecuta codigo arbitrario contenido en el "
            "fichero; es ejecucion remota de codigo (RCE), no un riesgo teorico."
        )

    # Normalizacion minima para que la comprobacion valga igual en Windows y POSIX:
    # se mira solo el nombre de fichero, no el resto de la ruta.
    nombre = os.path.basename(raw.replace("\\", "/"))
    if not nombre.lower().endswith(SAFETENSORS_SUFFIX) or nombre.lower() == SAFETENSORS_SUFFIX:
        raise UnsafeWeightsFormat(
            f"Formato de pesos rechazado: {raw!r}. Solo se aceptan ficheros "
            f"'{SAFETENSORS_SUFFIX}' (D-14). Los formatos basados en pickle "
            "(.bin, .pt, .pth, .ckpt, .pkl, .joblib) deserializan objetos "
            "arbitrarios: cargarlos con torch.load/joblib/dill ejecuta el codigo "
            "que lleve el fichero, es ejecucion remota de codigo (RCE). "
            "'weights_sha256' verifica integridad, NO inocuidad: un pickle "
            "malicioso con hash correcto sigue siendo un pickle malicioso."
        )
    return raw


def assert_within_gpu_budget(elapsed_s: float, max_gpu_seconds: int, detail: str = "") -> None:
    """Aborta el trabajo si ya consumio mas GPU de la presupuestada (D-17).

    Se llama en los puntos de control del bucle de inferencia (por etapa, o cada
    N pasos de difusion), no una sola vez al final: el objetivo de D-17 es cortar
    un trabajo desbocado, no contabilizarlo a posteriori.

    Levanta:
        ValueError: si `max_gpu_seconds` no es positivo.
        GpuBudgetExceeded: si `elapsed_s > max_gpu_seconds`.
    """
    if max_gpu_seconds <= 0:
        raise ValueError("max_gpu_seconds debe ser > 0 (D-17: todo trabajo lleva presupuesto).")
    if elapsed_s > max_gpu_seconds:
        raise GpuBudgetExceeded(elapsed_s, max_gpu_seconds, detail)


# --------------------------------------------------------------------------- #
# Capacidades declaradas
# --------------------------------------------------------------------------- #

class ModelCapability(StrEnum):
    """Capacidades que un modelo puede declarar (`spec.md` §3.3).

    En la Fase 0 este enum es solo vocabulario: sirve para que `T-07` (matriz de
    capacidades verificadas) registre por escrito que soporta ACE-Step de verdad,
    frente a lo que promete su README. La resolucion de modelo por capacidades
    —y el registry que la consulta— es T-30 en la Fase 5; el router con
    preferencias y fallback no se construye hasta que haya un tercer modelo que
    lo justifique (D-16).
    """

    TEXT_TO_MUSIC = "text_to_music"            # prompt de estilo -> musica
    LYRICS_TO_SONG = "lyrics_to_song"          # letra + estilo -> cancion cantada
    INSTRUMENTAL = "instrumental"              # generacion sin voz
    VOICE_CONDITIONING = "voice_conditioning"  # condicionar timbre/registro vocal
    STEM_OUTPUT = "stem_output"                # entrega stems nativos
    SECTION_INPAINT = "section_inpaint"        # regenerar un tramo concreto
    CONTINUATION = "continuation"              # extender una pista existente
    AUDIO_TO_AUDIO = "audio_to_audio"          # cover / remezcla sobre audio de entrada
    FINE_TUNABLE = "fine_tunable"              # admite pesos derivados propios


# --------------------------------------------------------------------------- #
# Datos del contrato
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True, kw_only=True)
class AudioArtifact:
    """Un fichero de audio producido por el adapter.

    El contenido viaja **o** como ruta en disco (`path`, lo normal: el runner
    escribe y luego sube con URL firmada de alcance por trabajo, D-15) **o** como
    bytes en memoria (`data`, util en los spikes y en el mock). Exactamente uno
    de los dos.

    `size_bytes` y `duration_s` describen el artefacto **real**, no el pedido: la
    tolerancia de duracion (±5 %, C-01) la comprueba quien consuma esto, no este
    contenedor de datos.
    """

    format: AudioFormat
    sample_rate: int
    channels: int
    duration_s: float
    size_bytes: int
    path: str | None = None
    data: bytes | None = None

    def __post_init__(self) -> None:
        if (self.path is None) == (self.data is None):
            raise ValueError(
                "AudioArtifact necesita exactamente uno de 'path' o 'data' "
                "(se recibieron ambos, o ninguno)."
            )
        if self.format not in ("flac", "mp3", "wav"):
            raise ValueError(f"Formato de audio no soportado: {self.format!r}.")
        if self.sample_rate <= 0 or self.channels <= 0:
            raise ValueError("sample_rate y channels deben ser > 0.")
        if self.duration_s <= 0:
            raise ValueError("duration_s debe ser > 0.")
        if self.size_bytes < 0:
            raise ValueError("size_bytes no puede ser negativo.")


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationRequest:
    """Peticion de generacion — version minima de Fase 0.

    Construccion solo por palabra clave: son ocho campos y confundir dos
    posicionales (por ejemplo `duration_s` con `max_gpu_seconds`) seria un fallo
    silencioso y caro.

    Diferido a fases posteriores (ver el docstring del modulo): `voice`,
    `source_audio`, `section_edit`.
    """

    style_prompt: str
    duration_s: int
    max_gpu_seconds: int
    idempotency_key: str
    lyrics: str | None = None
    instrumental: bool = False
    seed: int | None = None
    model_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.style_prompt.strip():
            raise ValueError("style_prompt no puede estar vacio.")
        if self.duration_s <= 0:
            raise ValueError("duration_s debe ser > 0.")
        if self.max_gpu_seconds <= 0:
            raise ValueError(
                "max_gpu_seconds debe ser > 0: todo trabajo lleva presupuesto de GPU (D-17)."
            )
        if not self.idempotency_key.strip():
            raise ValueError(
                "idempotency_key es obligatoria: reintentar un trabajo no debe "
                "duplicar artefactos."
            )
        if self.instrumental and self.lyrics is not None:
            raise ValueError(
                "Peticion contradictoria: instrumental=True junto con 'lyrics'. Una "
                "pista instrumental no canta letra; deja lyrics=None o pon "
                "instrumental=False."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class RunTelemetry:
    """Telemetria de una ejecucion, en las unidades que consumen T-03 y T-04.

    `stage_timings` usa las etapas canonicas de `spikes._timing.STAGES`
    (`scheduling`, `image_pull`, `weights_download`, `vram_load`, `warmup`,
    `inference`), que son exactamente las que `T-03` exige medir.

    **Contrato de `gpu_seconds` y `stage_timings` (cambio M-3):** cubren SOLO la
    generacion a la que pertenece esta telemetria (en la practica, la etapa
    `inference`). El coste del arranque (`weights_download`, `vram_load`,
    `warmup`) se paga **una vez** por carga del modelo y el adapter lo reporta
    **aparte** —`load_gpu_seconds` y `load_stage_timings_s` en su cabecera
    (`describe()` / `report_metadata()`)—, nunca repetido en la telemetria de
    cada una de las N generaciones: sumarlo N veces inflaria el presupuesto de
    D-17 y cualquier agregado de coste.

    `vram_peak_mb` es `None` cuando no hay CUDA (maquina sin GPU, o modo mock sin
    medicion real) **o cuando el pico no es fiable** (otra generacion concurrente
    en el mismo proceso lo contamina): ausencia de dato, no cero.

    El **coste** por generacion, que la `spec.md` §12.3 pide visible desde el dia
    uno, no esta aqui: se deriva de `gpu_seconds` por el precio/hora del
    proveedor, y ese calculo vive en la observabilidad (F7), no en el runner.
    """

    gpu_seconds: float
    vram_peak_mb: int | None = None
    retries: int = 0
    offloading_enabled: bool = False
    stage_timings: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationResult:
    """Resultado de una generacion — version minima de Fase 0.

    FALTA A PROPOSITO: `provenance: ProvenanceRecord`.
    El manifiesto de procedencia v1 (con `manifest_schema_version`,
    `lyrics_declaration` D-21 y `source_generation` D-22) y su encadenado al
    ledger append-only los aporta **T-27 en la Fase 5 (C-10a)**, sobre el esquema
    **firmado por legal** (D-20). Ningun adapter de la Fase 0 emite procedencia:
    inventar aqui un formato provisional obligaria a un backfill de la cadena de
    hashes, y una cadena WORM no admite backfill. Las ~20 pistas propias de
    spikes y G1 se cubren con manifiesto retroactivo simplificado (S-11).
    """

    artifacts: list[AudioArtifact]
    telemetry: RunTelemetry


@dataclass(frozen=True, slots=True, kw_only=True)
class HealthStatus:
    """Respuesta de `health()`.

    `detail` es obligatorio y debe ser legible: cuando `ready` es `False` es lo
    unico que el operador va a leer. En el modo GPU local, un arranque con VRAM
    insuficiente tiene que decir la VRAM detectada y el minimo exigido, y nunca
    fallar en silencio (`spec.md` §6, D-29).
    """

    ready: bool
    detail: str
    vram_total_mb: int | None = None
    vram_free_mb: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RunnerContext:
    """Contexto de ejecucion que recibe `load()`.

    **Sin credenciales, a proposito (D-15).** No hay aqui claves de S3, tokens de
    RunPod ni rutas a ficheros de secretos, y no debe haberlas nunca: el runner
    opera sin credenciales persistentes y recibe URLs firmadas de alcance por
    trabajo y caducidad corta a traves de variables de entorno de vida corta.
    Ningun adapter puede alcanzar los artefactos de otro trabajo.

    Campos:
        device: identificador de dispositivo (`"cuda:0"`, `"cpu"`, `"mock"`).
        dtype: precision de computo (`"bfloat16"`, `"float16"`, `"float32"`).
        offload: si se activa offloading de pesos. Se decide por la VRAM
            detectada —automatico por debajo de los 24 GB de confort (D-06/D-29)—
            con `spikes._timing.decide_offloading()`, y degrada los tiempos de
            forma material (S-02).
        weights_dir: directorio de la cache de pesos en el host o volumen
            persistente. Todo fichero que se lea de ahi pasa por
            `assert_safetensors()` (D-14).
        max_gpu_seconds: techo por defecto de segundos de GPU del runner (D-17).
            Una peticion puede traer el suyo; el efectivo es el menor de los dos.
    """

    device: str
    dtype: str
    offload: bool
    weights_dir: str
    max_gpu_seconds: int

    def __post_init__(self) -> None:
        if self.max_gpu_seconds <= 0:
            raise ValueError("max_gpu_seconds debe ser > 0 (D-17).")


# --------------------------------------------------------------------------- #
# Interfaz del adapter
# --------------------------------------------------------------------------- #

@runtime_checkable
class MusicModelAdapter(Protocol):
    """Interfaz de comportamiento de un modelo musical (`spec.md` §3.3).

    Los cuatro metodos son `async`: el runner atiende salud y cancelacion
    mientras una inferencia esta en vuelo. Un adapter que bloquee el bucle de
    eventos con computo sincrono debe delegarlo a un executor.

    En la Fase 5, `T-30` anade a este Protocol el atributo
    `descriptor: ModelDescriptor` y la suite de conformidad que lo verifica
    (D-13, por tolerancia perceptual: nunca comparacion bit a bit).
    """

    async def load(self, ctx: RunnerContext) -> None:
        """Carga los pesos y deja el modelo listo para generar.

        Contrato:
        * Todo fichero de pesos pasa por `assert_safetensors()` antes de abrirse
          (D-14). Cualquier otro formato aborta la carga.
        * Idempotente: llamarlo dos veces no recarga ni duplica memoria.
        * Cubre las etapas `weights_download`, `vram_load` y `warmup` de la
          medicion de arranque en frio de `T-03` (`scheduling` e `image_pull`
          ocurren antes de que exista el proceso: las mide el orquestador).
        * No lee credenciales de disco (D-15).
        """
        ...

    async def generate(self, req: GenerationRequest) -> GenerationResult:
        """Genera audio a partir de la peticion.

        Contrato:
        * Exige `load()` previo; si no, levanta `RuntimeError`.
        * Respeta `req.max_gpu_seconds` con puntos de control durante la
          inferencia y aborta con `GpuBudgetExceeded` al excederlo (D-17).
        * Devuelve al menos un `AudioArtifact` y una `RunTelemetry` con
          `gpu_seconds` y `stage_timings` rellenos. Ambos cubren SOLO esta
          generacion (M-3): el coste de carga se reporta una vez, aparte
          (`load_gpu_seconds` en la cabecera del adapter), no en cada run.
        * `req.seed` se registra por trazabilidad; **no** se promete salida
          identica entre ejecuciones (driver, cuDNN, kernels de atencion, orden
          de reduccion en coma flotante).
        * `req.idempotency_key` identifica el trabajo logico: un reintento con la
          misma clave no debe producir artefactos duplicados.
        * En la Fase 5 este metodo empieza a devolver tambien `provenance`
          (T-27, sobre el esquema firmado por legal).
        """
        ...

    async def health(self) -> HealthStatus:
        """Estado del adapter, sin efectos secundarios ni consumo de GPU.

        Debe responder tambien —y sobre todo— cuando el modelo **no** esta listo:
        es la sonda con la que `T-03` cierra la medicion de arranque en frio, y
        la que decide si un pod acepta trabajo. Nunca lanza excepcion: un fallo
        se reporta como `ready=False` con `detail` explicativo.
        """
        ...

    async def unload(self) -> None:
        """Libera pesos y memoria de GPU.

        Idempotente y seguro incluso tras un fallo de `load()`. Despues de
        `unload()`, `health()` reporta `ready=False` y `generate()` vuelve a
        exigir `load()`. Es lo que permite medir el pico de VRAM de ejecuciones
        sucesivas sin contaminacion entre ellas (`T-03`) y liberar la GPU al
        vencer el keep-warm.
        """
        ...
