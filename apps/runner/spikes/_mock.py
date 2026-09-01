"""Adapter mock determinista para los spikes de la Fase 0 (modo `--mock`).

Para que existe
---------------
La maquina de desarrollo no tiene GPU: `nvidia-smi` no existe y `torch` no esta
instalado. Sin este mock, los tres spikes de la Fase 0 (`T-03`, `T-04`, `T-05`)
no se podrian ni ejecutar ni revisar hasta tener la GPU delante. Con `--mock` se
recorre el camino completo —carga, generacion, telemetria, informe JSON— usando
**solo la biblioteca estandar**, y lo que se verifica es la **forma del
contrato**, no el audio.

Lo que este mock NO es
----------------------
* **No es el mock canonico de la suite E2E.** El mock de `MOCK_GPU=1` que usan
  las pruebas de extremo a extremo lo define el `test-plan.md` mas adelante,
  junto con el resto del monorepo (`T-10` y siguientes, detras del gate **G1**).
  Este vive dentro de `spikes/`, se llama `_mock` con guion bajo porque es
  privado de los spikes, y **no lo sustituye**.
* **No es una estimacion.** Los tiempos que simula son plausibles y coherentes
  con S-01/S-02 (`spec.md` §11), pero **no miden nada**. Ningun informe puede
  presentarlos como resultado de `T-03`: el criterio de aceptacion exige medicion
  en GPU real (local para inferencia/VRAM, pod de RunPod para el arranque en
  frio). Todo informe generado en este modo debe llevar la marca
  `"source": "mock"` que devuelve `MockMusicModelAdapter.report_metadata()`.
* **No emite procedencia.** Igual que el adapter real de la Fase 0: el manifiesto
  v1 lo aporta `T-27` en la F5, sobre el esquema firmado por legal (D-20).

Determinismo
------------
Todo valor simulado sale de un `hashlib.sha256` sobre los campos de la peticion
(semilla, prompt de estilo, letra, duracion, instrumental, `idempotency_key`).
**No se usa `random` ni el estado global de nadie**: la misma peticion da los
mismos numeros en cualquier maquina y en cualquier orden de ejecucion, que es lo
que hace revisable un informe de spike. Ojo con la ironia: este mock si es
reproducible bit a bit, el modelo real **no** —la semilla se registra por
trazabilidad, no como garantia (D-13).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import wave
from pathlib import Path
from typing import Any

# Los spikes se ejecutan como scripts sueltos, sin paquete instalable: el
# empaquetado del monorepo es T-10, detras del gate G1. Por eso se anade
# `apps/runner/` a sys.path a mano en lugar de importar con ruta de paquete.
_RUNNER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RUNNER_ROOT not in sys.path:
    sys.path.insert(0, _RUNNER_ROOT)

_SPIKES_DIR = os.path.dirname(os.path.abspath(__file__))
if _SPIKES_DIR not in sys.path:
    sys.path.insert(0, _SPIKES_DIR)

import _timing  # noqa: E402  (tras el arranque de sys.path)
from contracts import (  # noqa: E402
    AudioArtifact,
    GenerationRequest,
    GenerationResult,
    HealthStatus,
    ModelCapability,
    RunnerContext,
    RunTelemetry,
    assert_safetensors,
    assert_within_gpu_budget,
)

__all__ = ["MockMusicModelAdapter", "make_request"]

#: ACE-Step genera a 44,1 kHz estereo; el WAV a 48 kHz es exportacion a demanda
#: con resample soxr (D-09/D-23). El mock respeta la tasa nativa.
_SAMPLE_RATE = 44_100
_CHANNELS = 2
_SAMPLE_WIDTH = 2  # 16 bit


def _digest(*parts: object) -> bytes:
    """SHA-256 de las partes dadas, unidas con un separador que no aparece en texto."""
    material = "\x1f".join(repr(p) for p in parts).encode("utf-8")
    return hashlib.sha256(material).digest()


def _unit(digest: bytes, offset: int) -> float:
    """Extrae un float determinista en [0, 1) de 4 bytes del digest.

    `offset` se toma modulo el tamano del digest, asi que cualquier indice vale y
    no hay que contar bytes al anadir una magnitud nueva.
    """
    i = (offset * 4) % (len(digest) - 4)
    return int.from_bytes(digest[i : i + 4], "big") / 2**32


def _entre(digest: bytes, offset: int, bajo: float, alto: float) -> float:
    """Valor determinista en [bajo, alto) derivado del digest."""
    return bajo + (alto - bajo) * _unit(digest, offset)


def make_request(
    *,
    style_prompt: str = "pop electronico melancolico, tempo medio, voz femenina",
    duration_s: int = 180,
    max_gpu_seconds: int = 600,
    idempotency_key: str = "spike-mock-0001",
    lyrics: str | None = "[verso]\nletra de prueba del spike\n[estribillo]\nsegunda linea",
    instrumental: bool = False,
    seed: int | None = 1234,
    model_params: dict[str, Any] | None = None,
) -> GenerationRequest:
    """Peticion de ejemplo con valores por defecto sensatos, para los spikes.

    Ahorra repetir los ocho campos obligatorios en cada script. `max_gpu_seconds`
    por defecto es 600 s: holgado frente a los 150 s de S-02 y suficiente para que
    un caso con offloading no salte el presupuesto por accidente (D-17).
    """
    return GenerationRequest(
        style_prompt=style_prompt,
        duration_s=duration_s,
        max_gpu_seconds=max_gpu_seconds,
        idempotency_key=idempotency_key,
        lyrics=None if instrumental else lyrics,
        instrumental=instrumental,
        seed=seed,
        model_params=dict(model_params or {}),
    )


class MockMusicModelAdapter:
    """Implementacion mock y determinista de `contracts.MusicModelAdapter`.

    Simula las seis etapas de `_timing.STAGES` con tiempos derivados de la
    semilla y el prompt (nunca aleatorios) y un pico de VRAM que **reacciona al
    flag de offloading**: con offloading el pico cae por debajo del suelo de 8 GB
    a costa de multiplicar el tiempo de inferencia, que es exactamente el
    compromiso que `T-03` va a medir de verdad.

    Args:
        image_cached: si la imagen de contenedor ya esta en cache del host. Con
            `False` se simula el escenario sin cachear de `T-03` (5-12 min).
        weights_cached: si los pesos ya estan en la cache del host o volumen
            persistente. Con `False` se simula la descarga.
        output_dir: si se indica, `generate()` **escribe un WAV silencioso valido**
            de la duracion pedida en ese directorio y el artefacto apunta ahi.
            Cuidado con el tamano: 44,1 kHz estereo de 16 bit son ~10,6 MB por
            minuto, o ~32 MB por pista de 3 min. Si es `None` (por defecto) no se
            toca el disco y el artefacto viaja como `data` con una carga
            **marcador**, no audio decodificable.
        time_scale: factor de espera real. `0.0` (por defecto) no duerme: los
            tiempos son simulados, no vividos, y un spike no puede tardar 90 s de
            reloj por inferencia falsa. Subelo solo para probar cancelaciones o
            barras de progreso.
        weights_name: nombre del fichero de pesos simulado. Pasa por
            `assert_safetensors()` en `load()`, igual que el adapter real (D-14):
            ponle una extension de pickle y el mock **falla a proposito**.
    """

    MODEL_ID = "mock-ace-step"
    MODEL_VERSION = "0.0.0-spike"
    #: Solo las capacidades que la Fase 0 necesita. Lo que ACE-Step soporte de
    #: verdad en `SECTION_INPAINT`, `AUDIO_TO_AUDIO`, `VOICE_CONDITIONING` y
    #: `CONTINUATION` lo determina `T-07` empiricamente, no este mock.
    CAPABILITIES = frozenset(
        {
            ModelCapability.TEXT_TO_MUSIC,
            ModelCapability.LYRICS_TO_SONG,
            ModelCapability.INSTRUMENTAL,
        }
    )

    def __init__(
        self,
        *,
        image_cached: bool = True,
        weights_cached: bool = True,
        output_dir: str | Path | None = None,
        time_scale: float = 0.0,
        weights_name: str = "ace_step_1_5.safetensors",
    ) -> None:
        self.image_cached = image_cached
        self.weights_cached = weights_cached
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.time_scale = float(time_scale)
        self.weights_name = weights_name

        self._ctx: RunnerContext | None = None
        self._loaded = False
        self._load_timings: dict[str, float] = {}
        self._generations = 0

    # -- ciclo de vida ------------------------------------------------------ #

    async def load(self, ctx: RunnerContext) -> None:
        """Simula el arranque: scheduling, pull de imagen, pesos, VRAM y warm-up.

        Idempotente, como exige el contrato: una segunda llamada no vuelve a
        simular nada y conserva los tiempos de la primera (el keep-warm de 10 min
        significa justo eso: no se paga dos veces).

        Valida la ruta de pesos con `assert_safetensors()` **antes** de simular la
        carga (D-14), y no lee ninguna credencial (D-15): `RunnerContext` no
        transporta ninguna.
        """
        if self._loaded:
            return

        ruta_pesos = os.path.join(ctx.weights_dir, self.weights_name)
        assert_safetensors(ruta_pesos)  # D-14: unica puerta de entrada de pesos

        d = _digest("load", ctx.device, ctx.dtype, ctx.offload, self.weights_name)
        timings: dict[str, float] = {}

        # scheduling: en cloud el proveedor tiene que asignar una maquina. En GPU
        # local es ~0, pero el mock no sabe donde corre (RunnerContext no lleva
        # proveedor: eso es T-85 en F6), asi que simula el caso cloud. Un spike en
        # local puede sobrescribirlo con StageTimer.add("scheduling", 0.0).
        timings["scheduling"] = _entre(d, 0, 4.0, 20.0)
        # image_pull: termino dominante del arranque en frio sin cache (S-01b).
        timings["image_pull"] = _entre(d, 2, 3.0, 12.0) if self.image_cached else _entre(d, 3, 90.0, 300.0)
        # weights_download: 3,5B en safetensors; cacheados, casi nada.
        timings["weights_download"] = (
            _entre(d, 4, 1.0, 5.0) if self.weights_cached else _entre(d, 5, 60.0, 240.0)
        )
        # vram_load y warmup: se alargan con offloading, que trocea la carga.
        factor_offload = 2.2 if ctx.offload else 1.0
        timings["vram_load"] = _entre(d, 6, 12.0, 40.0) * factor_offload
        timings["warmup"] = _entre(d, 7, 6.0, 18.0) * factor_offload

        for etapa, segundos in timings.items():
            await self._sleep(segundos)
            self._load_timings[etapa] = round(segundos, 3)

        self._ctx = ctx
        self._loaded = True

    async def unload(self) -> None:
        """Libera el estado simulado. Idempotente y segura tras un `load()` fallido."""
        self._loaded = False
        self._ctx = None
        self._load_timings = {}

    # -- generacion --------------------------------------------------------- #

    async def generate(self, req: GenerationRequest) -> GenerationResult:
        """Simula una generacion y devuelve artefacto + telemetria deterministas.

        Los tiempos de `inference` escalan con `req.duration_s` en torno a la
        linea base de S-02 (~90 s de inferencia pura para una pista de 3 min en
        GPU de >= 24 GB) y se multiplican por 2,5 con offloading.

        Contrato de telemetria (M-3), el mismo que el adapter real:
        `gpu_seconds` y `stage_timings` cubren SOLO esta generacion (la etapa
        `inference`). El coste simulado del arranque se reporta una vez, aparte
        (`load_stage_timings()` / `load_gpu_seconds()`, y en `report_metadata()`).

        Aplica D-17 de verdad, sobre el coste TOTAL del trabajo (arranque mas
        inferencia, que es lo que retiene la tarjeta): si supera el presupuesto,
        levanta `GpuBudgetExceeded` en lugar de devolver un resultado. Es la
        unica forma de que los spikes ejerciten esa rama sin GPU.

        Levanta:
            RuntimeError: si no se llamo a `load()` antes (contrato del adapter).
            GpuBudgetExceeded: si el presupuesto de GPU se agota (D-17).
        """
        if not self._loaded or self._ctx is None:
            raise RuntimeError(
                "generate() sin load() previo: el contrato de MusicModelAdapter exige "
                "cargar el modelo antes de generar."
            )

        ctx = self._ctx
        offload = ctx.offload
        d = _digest(
            "generate",
            req.seed,
            req.style_prompt,
            req.lyrics,
            req.duration_s,
            req.instrumental,
            req.idempotency_key,
            offload,
        )

        # Inferencia: base S-02 escalada por duracion, degradada por offloading.
        base_por_180s = _entre(d, 0, 75.0, 110.0)
        inferencia_s = base_por_180s * (req.duration_s / 180.0)
        if req.instrumental:
            inferencia_s *= 0.85  # sin sintesis vocal, algo mas rapido
        if offload:
            inferencia_s *= 2.5  # tiempos degradados (D-29): el coste del suelo de 8 GB

        # Para el PRESUPUESTO (D-17) cuentan las etapas en que el trabajo retiene
        # la tarjeta: carga a VRAM y warm-up del arranque, mas la inferencia. Para
        # la TELEMETRIA (M-3), en cambio, solo la inferencia de esta generacion.
        gpu_total_trabajo = inferencia_s + self.load_gpu_seconds()

        presupuesto = min(req.max_gpu_seconds, ctx.max_gpu_seconds)
        assert_within_gpu_budget(
            gpu_total_trabajo,
            presupuesto,
            detail=(
                f"Simulacion del mock de spikes (offloading={offload}, "
                f"duracion pedida={req.duration_s} s)."
            ),
        )

        await self._sleep(inferencia_s)
        self._generations += 1

        # Pico de VRAM: reacciona al offloading. Sin offloading cabe holgado en la
        # cifra de confort de 24 GB; con offloading baja del suelo de 8 GB a costa
        # del 2,5x de tiempo aplicado arriba.
        if offload:
            vram_peak_mb = int(_entre(d, 1, 6_200.0, 7_600.0))
        else:
            vram_peak_mb = int(_entre(d, 2, 16_800.0, 21_500.0))

        telemetry = RunTelemetry(
            # SOLO esta generacion (M-3): el coste de carga se reporta una vez,
            # aparte, en load_gpu_seconds()/report_metadata().
            gpu_seconds=round(inferencia_s, 3),
            vram_peak_mb=vram_peak_mb,
            retries=0,
            offloading_enabled=offload,
            stage_timings={"inference": round(inferencia_s, 3)},
        )
        return GenerationResult(artifacts=[self._make_artifact(req, d)], telemetry=telemetry)

    # -- salud -------------------------------------------------------------- #

    async def health(self) -> HealthStatus:
        """Estado del mock. Nunca lanza excepcion, como exige el contrato.

        Si la maquina resulta tener CUDA, reporta la VRAM **real** leida con
        `_timing.vram_snapshot_mb()`; si no la hay (el caso normal en desarrollo),
        reporta valores **simulados** y lo dice en `detail`, para que nadie los
        confunda con una medicion.
        """
        if not self._loaded or self._ctx is None:
            return HealthStatus(
                ready=False,
                detail=(
                    f"Mock '{self.MODEL_ID}@{self.MODEL_VERSION}' sin cargar: "
                    "llama a load(ctx) antes de generar."
                ),
            )

        real = _timing.vram_snapshot_mb()
        if real is not None:
            total, usado, _pico = real
            return HealthStatus(
                ready=True,
                detail=(
                    f"Mock '{self.MODEL_ID}@{self.MODEL_VERSION}' listo en "
                    f"{self._ctx.device} (offloading={self._ctx.offload}); VRAM REAL "
                    f"leida de torch.cuda. Los tiempos siguen siendo simulados."
                ),
                vram_total_mb=total,
                vram_free_mb=max(total - usado, 0),
            )

        d = _digest("health", self.MODEL_ID, self._ctx.device, self._ctx.offload)
        total_sim = _timing.VRAM_FLOOR_MB if self._ctx.offload else _timing.VRAM_COMFORT_MB
        ocupado_sim = int(_entre(d, 0, 0.55, 0.85) * total_sim)
        return HealthStatus(
            ready=True,
            detail=(
                f"Mock '{self.MODEL_ID}@{self.MODEL_VERSION}' listo en "
                f"{self._ctx.device} (offloading={self._ctx.offload}). Sin CUDA en esta "
                "maquina: VRAM y tiempos SIMULADOS, no medidos."
            ),
            vram_total_mb=total_sim,
            vram_free_mb=total_sim - ocupado_sim,
        )

    # -- utilidades para los informes de spike ------------------------------ #

    def load_stage_timings(self) -> dict[str, float]:
        """Etapas simuladas del arranque (contrato M-3, como el adapter real).

        Este coste se paga **una vez** por carga y se reporta aqui, aparte: los
        `stage_timings` de cada generacion ya no lo repiten.
        """
        return dict(self._load_timings)

    def load_gpu_seconds(self) -> float:
        """Segundos simulados de GPU del arranque (vram_load + warmup), pagados una vez."""
        return sum(
            v
            for k, v in self._load_timings.items()
            if k in _timing.GPU_STAGES and k != "inference"
        )

    def report_metadata(self) -> dict[str, Any]:
        """Bloque de cabecera para el informe JSON del spike.

        Lleva `source: "mock"` de forma explicita: es la marca que impide que un
        informe simulado se lea como una medicion real de `T-03`. Desde M-3
        lleva tambien el coste del arranque (`load_stage_timings_s` /
        `load_gpu_seconds`), que ya no viaja en la telemetria de cada generacion.
        """
        return {
            "source": "mock",
            "model_id": self.MODEL_ID,
            "model_version": self.MODEL_VERSION,
            "capabilities": sorted(str(c) for c in self.CAPABILITIES),
            "image_cached": self.image_cached,
            "weights_cached": self.weights_cached,
            "generations": self._generations,
            "writes_audio": self.output_dir is not None,
            # Coste del arranque, pagado UNA vez por carga (contrato M-3).
            "load_stage_timings_s": {
                k: round(v, 3) for k, v in self.load_stage_timings().items()
            },
            "load_gpu_seconds": round(self.load_gpu_seconds(), 3),
            "aviso": (
                "Tiempos y VRAM SIMULADOS de forma determinista a partir de la semilla "
                "y el prompt. No son una medicion: los criterios de aceptacion de T-03 "
                "exigen GPU real (local para inferencia/VRAM, pod de RunPod para el "
                "arranque en frio)."
            ),
        }

    # -- internos ----------------------------------------------------------- #

    async def _sleep(self, seconds: float) -> None:
        """Espera `seconds * time_scale`. Con `time_scale=0` solo cede el control."""
        await asyncio.sleep(seconds * self.time_scale if self.time_scale > 0 else 0)

    def _make_artifact(self, req: GenerationRequest, d: bytes) -> AudioArtifact:
        """Construye el artefacto: WAV silencioso en disco, o carga marcador.

        El formato declarado es siempre `wav` porque es lo unico que la biblioteca
        estandar puede producir de verdad (modulo `wave`). El adapter real de la
        Fase 1 entrega **FLAC + MP3 320** (D-09) y WAV a 48 kHz solo como
        exportacion a demanda (D-23); ese pipeline de codificacion es post-proceso
        (`T-45`), no alcance de este mock.
        """
        duracion = float(req.duration_s)
        if self.output_dir is None:
            # Carga marcador: NO es audio decodificable. Se declara el tamano real
            # de los bytes que se devuelven, no una estimacion de FLAC inventada.
            cuerpo = b"MOCK-AUDIO-FASE0\x00" + d + d[::-1]
            return AudioArtifact(
                format="wav",
                sample_rate=_SAMPLE_RATE,
                channels=_CHANNELS,
                duration_s=duracion,
                size_bytes=len(cuerpo),
                data=cuerpo,
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        nombre = f"{req.idempotency_key}-{d[:4].hex()}.wav"
        destino = self.output_dir / nombre
        marcos = int(duracion * _SAMPLE_RATE)
        with wave.open(str(destino), "wb") as wav:
            wav.setnchannels(_CHANNELS)
            wav.setsampwidth(_SAMPLE_WIDTH)
            wav.setframerate(_SAMPLE_RATE)
            # Silencio escrito por bloques de 1 s para no construir en memoria los
            # ~32 MB de una pista de 3 min.
            bloque = b"\x00" * (_SAMPLE_RATE * _CHANNELS * _SAMPLE_WIDTH)
            restantes = marcos
            while restantes > 0:
                if restantes >= _SAMPLE_RATE:
                    wav.writeframes(bloque)
                    restantes -= _SAMPLE_RATE
                else:
                    wav.writeframes(b"\x00" * (restantes * _CHANNELS * _SAMPLE_WIDTH))
                    restantes = 0
        return AudioArtifact(
            format="wav",
            sample_rate=_SAMPLE_RATE,
            channels=_CHANNELS,
            duration_s=duracion,
            size_bytes=destino.stat().st_size,
            path=str(destino),
        )
