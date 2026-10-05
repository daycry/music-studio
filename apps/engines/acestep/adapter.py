"""ACE-Step Python; se importa en el hijo, nunca CUDA en la factoría HTTP."""

import math
import os
import re
import secrets
import sys
from contextlib import contextmanager, redirect_stdout
from types import SimpleNamespace

from descriptor import CHECKPOINT, LM, MODEL_ID, locked_model, model_root
from engine_common import EngineError
from patches import enforce_safe_pretrained, install_safe_loader, verify_components

MAX_SEED = 2**64 - 1


def exact_prepare_seeds(actual_batch_size, seed, use_random_seed):
    """Sustituye TaskUtilsMixin.prepare_seeds (upstream task_utils.py:19).

    Inference convierte config.seeds a CSV y el upstream aplica int(float(s)),
    que redondea enteros >2**53. Aquí los enteros llegan intactos al LM/DiT;
    no hay fallback aleatorio para semillas explícitas inválidas.
    """
    if use_random_seed:
        values = [secrets.randbelow(2**32) for _ in range(actual_batch_size)]
    else:
        tokens = seed.split(",") if isinstance(seed, str) else [seed]
        try:
            if any(
                not (
                    (isinstance(value, int) and not isinstance(value, bool))
                    or (
                        isinstance(value, str)
                        and re.fullmatch(r"[0-9]+", value.strip())
                    )
                )
                for value in tokens
            ):
                raise ValueError("Semilla no entera")
            values = [int(value) for value in tokens]
        except (TypeError, ValueError, OverflowError):
            raise EngineError("INVALID_PARAMS", "Semillas enteras requeridas") from None
        if len(values) != actual_batch_size or any(
            not 0 <= value <= MAX_SEED for value in values
        ):
            raise EngineError("INVALID_PARAMS", "Semillas fuera del rango de 64 bits")
    return values, ", ".join(str(value) for value in values)


def upstream_error(phase, detail):
    """Clasifica la causa sin publicar status/tracebacks/rutas del proveedor."""
    text = str(detail).casefold()
    oom = type(detail).__name__ == "OutOfMemoryError" or (
        any(device in text for device in ("cuda", "gpu", "vram"))
        and any(
            reason in text
            for reason in (
                "out of memory",
                "outofmemoryerror",
                "budget exceeded",
                "memory allocation failed",
                "insufficient free vram",
            )
        )
    )
    if oom:
        return EngineError("VRAM_EXCEEDED", f"VRAM insuficiente durante {phase}")
    return EngineError("INTERNAL", f"Fallo interno durante {phase}")


def upstream_call(phase, operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except EngineError:
        raise
    except Exception as error:  # noqa: BLE001 - frontera upstream; código tipado y mensaje público constante
        raise upstream_error(phase, error) from None


def configure_handler(dit):
    # Sin descargas, autosync de código ni estimaciones por cronómetro/persistidas.
    dit._ensure_models_present = lambda **kwargs: None
    dit._sync_model_code_if_needed = lambda *args: None
    dit._start_diffusion_progress_estimator = lambda **kwargs: (None, None)
    dit._save_progress_estimates = lambda: None
    dit.prepare_seeds = exact_prepare_seeds


@contextmanager
def step_hooks(runtime, token, progress, total):
    """El decoder fijado se llama una vez por paso Euler; hook real, no timer.

    El LM PT comprueba cancelación en cada forward. Los hooks se retiran también
    cuando el upstream captura un error/cancelación y devuelve un resultado fallido.
    """
    handles = []
    completed = 0

    def check(*args):
        token.check()

    def step(*args):
        nonlocal completed
        completed += 1
        progress(0.52 + 0.27 * min(completed / total, 1), desc="Diffusion step")

    try:
        decoder = getattr(getattr(runtime.dit, "model", None), "decoder", None)
        if decoder is not None:
            handles.append(decoder.register_forward_pre_hook(check))
            handles.append(decoder.register_forward_hook(step))
        lm = getattr(runtime.lm, "llm", None)
        if lm is not None:
            handles.append(lm.register_forward_pre_hook(check))
        yield
    finally:
        for handle in handles:
            handle.remove()


def load_options(mode, checkpoint):
    if mode not in {"bf16", "offload"}:
        raise EngineError("INVALID_PARAMS", "Modo ACE-Step no admitido")
    return {
        "config_path": checkpoint,
        "device": "cuda",
        "use_flash_attention": False,
        "compile_model": False,
        "offload_to_cpu": mode == "offload",
        "offload_dit_to_cpu": mode == "offload",
        "quantization": None,
        "use_mlx_dit": False,
        "vae_checkpoint": "official",
    }


def generation_options(request, index):
    values = request["params"]
    if "shift" in values and (
        type(values["shift"]) not in {int, float}
        or not 1 <= values["shift"] <= 5
        or not math.isfinite(values["shift"])
    ):
        raise EngineError(
            "INVALID_PARAMS", "Shift requiere un número finito entre 1 y 5"
        )
    seed = request.get("seed")
    if seed is not None and (
        seed < 0 or seed + max(index, request.get("n_outputs", 1) - 1) > MAX_SEED
    ):
        raise EngineError(
            "INVALID_PARAMS", "Semilla base y variantes exceden el rango de 64 bits"
        )
    seed = secrets.randbelow(2**31) if seed is None else seed + index
    instrumental = request["task"] == "music.instrumental"
    params = {
        "caption": values["style"],
        "lyrics": "[Instrumental]" if instrumental else values["lyrics"],
        "instrumental": instrumental,
        "duration": values["duration_s"],
        "seed": seed,
        "vocal_language": values.get(
            "vocal_language", values.get("language", "unknown")
        ),
        "bpm": values.get("bpm"),
        "keyscale": values.get("key", ""),
        "enable_normalization": False,
        "use_cot_language": False,
        "use_cot_caption": False,
        "use_cot_metas": False,
        "lm_negative_prompt": values.get("negative_prompt", "NO USER INPUT"),
    }
    if "shift" in values:
        params["shift"] = values["shift"]
    return params, {
        "batch_size": 1,
        "use_random_seed": False,
        "seeds": [seed],
        "allow_lm_batch": False,
    }


def write_wav(path, samples, sample_rate):
    import numpy as np
    import soundfile as sf

    if hasattr(samples, "detach"):
        samples = samples.detach().cpu().float().numpy()
    samples = np.asarray(samples, dtype=np.float32)
    if samples.ndim != 2 or samples.shape[0] != 2 or sample_rate != 48000:
        raise EngineError(
            "INTERNAL", "Audio upstream incompatible: requiere 48 kHz estéreo"
        )
    if not samples.shape[1] or not np.isfinite(samples).all():
        raise EngineError("INTERNAL", "Audio upstream vacío o no finito")
    sf.write(str(path), samples.T, sample_rate, subtype="FLOAT", format="WAV")


def prepare_runtime(checkpoints, checkpoint, lm):
    lock = locked_model(checkpoints.parents[1] / "models.lock.json")
    by_id = {component["id"]: component for component in lock["components"]}
    try:
        selected = [
            by_id[name] for name in (checkpoint, lm, "vae", "Qwen3-Embedding-0.6B")
        ]
    except KeyError:
        raise EngineError(
            "MODEL_NOT_FOUND", "Checkpoint o LM no fijado en el lock"
        ) from None
    verify_components(checkpoints, selected)
    os.environ["ACESTEP_CHECKPOINTS_DIR"] = str(checkpoints)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from acestep import gpu_config

    gpu_config.set_global_gpu_config(gpu_config.get_gpu_config_for_tier("tier4"))
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler

    install_safe_loader()
    enforce_safe_pretrained(torch.bfloat16)
    dit = AceStepHandler()
    # Los componentes ya están completos y verificados. Evita descarga automática
    # y autosync de .py remotos que invalidaría el hash del descriptor/lock.
    configure_handler(dit)
    return SimpleNamespace(
        torch=torch,
        dit=dit,
        lm=LLMHandler(),
        generate_music=generate_music,
        GenerationParams=GenerationParams,
        GenerationConfig=GenerationConfig,
    )


class AceStepAdapter:
    def __init__(self, checkpoint=CHECKPOINT, lm=LM):
        self.checkpoint = checkpoint
        self.lm = lm
        self.checkpoints = model_root() / "ace-step-1.5/checkpoints"
        self.runtime = None

    def load(self, model_id, mode, cap_mb, total_mb):
        if model_id != MODEL_ID:
            raise EngineError("MODEL_NOT_FOUND")
        options = load_options(mode, self.checkpoint)
        if total_mb <= 0 or not 0 < cap_mb <= total_mb:
            raise EngineError("VRAM_EXCEEDED", "Presupuesto VRAM insuficiente")
        with redirect_stdout(sys.stderr):
            runtime = upstream_call(
                "preparación del modelo",
                prepare_runtime,
                self.checkpoints,
                self.checkpoint,
                self.lm,
            )
            torch = runtime.torch
            if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
                raise EngineError("INTERNAL", "CUDA BF16 requerida")
            torch.cuda.set_per_process_memory_fraction(cap_mb / total_mb)
            torch.cuda.reset_peak_memory_stats()
            status, success = upstream_call(
                "carga de DiT/VAE/text encoder",
                runtime.dit.initialize_service,
                project_root=str(self.checkpoints.parent),
                **options,
            )
            if not success:
                raise upstream_error("carga de DiT/VAE/text encoder", status)
            if runtime.dit.dtype != torch.bfloat16 or runtime.dit.device != "cuda":
                raise EngineError(
                    "INTERNAL", "No se pudo cargar DiT/VAE/text encoder en BF16 CUDA"
                )
            status, success = upstream_call(
                "carga de LM",
                runtime.lm.initialize,
                checkpoint_dir=str(self.checkpoints),
                lm_model_path=self.lm,
                backend="pt",
                device="cuda",
                offload_to_cpu=mode == "offload",
                dtype=torch.bfloat16,
            )
            if not success:
                raise upstream_error("carga de LM", status)
        self.runtime = runtime

    def generate(self, request, output_dir, emit, token):
        if self.runtime is None:
            raise EngineError("INTERNAL", "Modelo no cargado")
        token.check()
        runtime = self.runtime
        ipc_stdout = sys.stdout
        artifacts = []
        for index in range(request["n_outputs"]):
            token.check()
            values, config = generation_options(request, index)

            def progress(value, desc=None, _index=index, **kwargs):
                token.check()
                # Sólo eventos provenientes del callback real, sin cronómetro.
                if not isinstance(value, (int, float)):
                    return
                with redirect_stdout(ipc_stdout):
                    stage = (
                        "decoding" if "decod" in (desc or "").lower() else "generating"
                    )
                    emit(("stage", {"stage": stage}))
                    emit(
                        (
                            "progress",
                            {
                                "fraction": max(0.0, min(1.0, float(value))),
                                "output_index": _index,
                            },
                        )
                    )

            with redirect_stdout(sys.stderr), step_hooks(runtime, token, progress, 8):
                result = upstream_call(
                    "generación",
                    runtime.generate_music,
                    runtime.dit,
                    runtime.lm,
                    runtime.GenerationParams(**values),
                    runtime.GenerationConfig(**config),
                    save_dir=None,
                    progress=progress,
                )
            # Upstream captura excepciones de callback: restituye CANCELLED antes
            # de traducir su GenerationResult fallido a error interno.
            token.check()
            if not result.success:
                detail = f"{getattr(result, 'error', '')} {getattr(result, 'status_message', '')}"
                raise upstream_error("generación", detail)
            if len(result.audios) != 1:
                raise EngineError("INTERNAL", "ACE-Step no produjo el audio solicitado")
            filename = f"output-{index}.wav"
            audio = result.audios[0]
            write_wav(output_dir / filename, audio["tensor"], audio["sample_rate"])
            token.check()
            artifacts.append(
                {
                    "filename": filename,
                    "output_index": index,
                    "media_type": "audio/wav",
                    "meta": {
                        "seed": values["seed"],
                        "sample_rate": audio["sample_rate"],
                        "channels": 2,
                    },
                }
            )
        return {
            "artifacts": artifacts,
            "vram_peak_mb": runtime.torch.cuda.max_memory_allocated() / 1024**2,
        }
