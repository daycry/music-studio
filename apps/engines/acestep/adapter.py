"""ACE-Step Python; se importa en el hijo, nunca CUDA en la factoría HTTP."""

import io
import json
import math
import os
import re
import secrets
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from functools import wraps
from types import SimpleNamespace

from descriptor import (
    CHECKPOINT,
    LM,
    locked_model,
    model_root,
)
from descriptor import (
    model_id as checkpoint_model_id,
)
from engine_common import EngineError
from input_profile import MAX_DURATION, VALID_LANGUAGES, inference_controls
from patches import enforce_safe_pretrained, install_safe_loader, verify_components
from preflight import digest, preflight, token_record

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
def input_capture(runtime, planned, values, index):
    """Envolturas temporales: solo se acredita una frontera cuando se ejecuta."""
    captured = {
        "receipt_version": 1,
        "kind": "captured",
        "output_index": index,
        "boundaries": [],
        "planned_sha256": digest(planned),
    }
    originals = []

    def wrap(obj, name, callback):
        original = getattr(obj, name, None)
        if callable(original):
            originals.append((obj, name, original))
            setattr(obj, name, wraps(original)(callback(original)))

    def arguments(original):
        def call(*args, **kwargs):
            metadata = dict(kwargs.get("user_metadata") or {})
            metadata["language"] = values["vocal_language"]
            kwargs["user_metadata"] = metadata
            captured["boundaries"].append(
                {
                    "stage": "lm_arguments",
                    "arguments_sha256": digest(
                        {k: v for k, v in kwargs.items() if k != "progress"}
                    ),
                    "metadata": metadata,
                }
            )
            return original(*args, **kwargs)

        return call

    def formatted(original):
        def call(formatted_prompt, cfg, **kwargs):
            lm = runtime.lm
            conditional = token_record(lm.llm_tokenizer, formatted_prompt)
            unconditional_prompt = lm._build_unconditional_prompt(
                caption=cfg["caption"],
                lyrics=cfg["lyrics"],
                cot_text=cfg["cot_text"],
                negative_prompt=cfg["negative_prompt"],
                generation_phase=cfg["generation_phase"],
                is_batch=False,
            )
            unconditional = token_record(lm.llm_tokenizer, unconditional_prompt)
            if (
                conditional != planned["lm"]["conditional"]
                or unconditional != planned["lm"]["unconditional"]
            ):
                raise EngineError(
                    "INVALID_PARAMS", "Entrada LM cambió tras el preflight"
                )
            reserve = lm._compute_max_new_tokens(
                cfg["target_duration"], cfg["generation_phase"]
            )
            if reserve != planned["lm"]["reserve_tokens"]:
                raise EngineError(
                    "INVALID_PARAMS", "Reserva LM cambió tras el preflight"
                )
            captured["boundaries"].append(
                {
                    "stage": "lm_formatted_prompt",
                    "conditional": conditional,
                    "unconditional": unconditional,
                    "reserve_tokens": reserve,
                    "cfg_sha256": digest(cfg),
                }
            )
            return original(formatted_prompt=formatted_prompt, cfg=cfg, **kwargs)

        return call

    def dit_arguments(original):
        def call(*args, **kwargs):
            for key, expected in (
                ("captions", values["caption"]),
                ("lyrics", values["lyrics"]),
                ("vocal_language", values["vocal_language"]),
                ("audio_duration", values["duration"]),
                ("bpm", values["bpm"]),
                ("key_scale", values["keyscale"]),
                ("time_signature", values.get("timesignature", "")),
            ) + tuple(
                (key, values[key])
                for key in ("inference_steps", "guidance_scale")
                if key in values
            ):
                if kwargs.get(key) != expected:
                    raise EngineError(
                        "INVALID_PARAMS", "Entrada DiT cambió tras el preflight"
                    )
            captured["boundaries"].append(
                {
                    "stage": "dit_arguments",
                    "arguments_sha256": digest(
                        {k: v for k, v in kwargs.items() if k != "progress"}
                    ),
                }
            )
            return original(*args, **kwargs)

        return call

    def dit_tokens(original):
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            records = {}
            for name, ids, mask in (
                ("text", result[1], result[2]),
                ("lyrics", result[3], result[4]),
            ):
                tokens = ids[0][mask[0].bool()].tolist()
                expected = planned["dit"][name]
                if (
                    len(tokens) != expected["count"]
                    or digest(tokens) != expected["tokens_sha256"]
                ):
                    raise EngineError(
                        "INVALID_PARAMS", "Tokens DiT cambiaron tras el preflight"
                    )
                records[name] = {"count": len(tokens), "tokens_sha256": digest(tokens)}
            captured["boundaries"].append({"stage": "dit_tokens", **records})
            return result

        return call

    try:
        wrap(runtime.lm, "generate_with_stop_condition", arguments)
        wrap(runtime.lm, "generate_from_formatted_prompt", formatted)
        wrap(runtime.dit, "generate_music", dit_arguments)
        wrap(runtime.dit, "_prepare_text_conditioning_inputs", dit_tokens)
        yield captured
    finally:
        for obj, name, original in reversed(originals):
            setattr(obj, name, original)


@contextmanager
def private_upstream_output():
    """Ámbito hijo: evita letras/prompts en stdout IPC y stderr de Docker."""
    logger = getattr(sys.modules.get("loguru"), "logger", None)
    if logger is not None:
        logger.disable("acestep")
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            yield
    finally:
        if logger is not None:
            logger.enable("acestep")


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


def generation_options(request, index, checkpoint=None):
    values = request["params"]
    identity = (
        checkpoint_model_id(checkpoint)
        if checkpoint
        else request.get("model_id", checkpoint_model_id(CHECKPOINT))
    )
    if request.get("model_id", identity) != identity or identity not in {
        "ace-step-1.5-turbo",
        "ace-step-1.5-sft",
    }:
        raise EngineError("MODEL_NOT_FOUND")
    try:
        controls = inference_controls(values, sft=identity == "ace-step-1.5-sft")
    except ValueError:
        raise EngineError(
            "INVALID_PARAMS", "Controles de inferencia no admitidos"
        ) from None
    language = values.get("vocal_language", values.get("language", "unknown"))
    if language not in VALID_LANGUAGES or (
        "language" in values
        and "vocal_language" in values
        and values["language"] != values["vocal_language"]
    ):
        raise EngineError("INVALID_PARAMS", "Idioma no admitido o contradictorio")
    if not 10 <= values["duration_s"] <= MAX_DURATION:
        raise EngineError("INVALID_PARAMS", "Duración fuera del presupuesto LM tier4")
    if "# Instruction" in values["style"] and "# Caption" in values["style"]:
        raise EngineError("INVALID_PARAMS", "Caption con extracción SFT no explícita")
    for name in ("key", "time_signature"):
        if name in values and values[name] != values[name].strip():
            raise EngineError("INVALID_PARAMS", "Metadata con limpieza no explícita")
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
        **controls,
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
    if "time_signature" in values:
        params["timesignature"] = values["time_signature"]
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
        if model_id != checkpoint_model_id(self.checkpoint):
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
        receipts = []
        for index in range(request["n_outputs"]):
            token.check()
            values, config = generation_options(request, index, self.checkpoint)
            variant_request = {**request, "seed": values["seed"], "n_outputs": 1}
            planned = preflight(
                variant_request,
                checkpoints=self.checkpoints,
                lm=self.lm,
                checkpoint=self.checkpoint,
            )

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

            params = runtime.GenerationParams(**values)
            generation_config = runtime.GenerationConfig(**config)
            with (
                private_upstream_output(),
                step_hooks(runtime, token, progress, values["inference_steps"]),
                input_capture(runtime, planned, values, index) as captured,
            ):
                actual_params = params if isinstance(params, dict) else vars(params)
                actual_config = (
                    generation_config
                    if isinstance(generation_config, dict)
                    else vars(generation_config)
                )
                captured["generation_params_sha256"] = digest(actual_params)
                captured["generation_config_sha256"] = digest(actual_config)
                captured["flags"] = {
                    k: actual_params[k]
                    for k in (
                        "thinking",
                        "use_cot_caption",
                        "use_cot_language",
                        "use_cot_metas",
                        "shift",
                        "guidance_scale",
                        "inference_steps",
                        "lm_cfg_scale",
                        "audio_cover_strength",
                    )
                    if k in actual_params
                }
                result = upstream_call(
                    "generación",
                    runtime.generate_music,
                    runtime.dit,
                    runtime.lm,
                    params,
                    generation_config,
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
            private = {"planned": planned, "captured": captured}
            filename_receipt = f"input-receipt-{index}.json"
            with (output_dir / filename_receipt).open("x", encoding="utf-8") as stream:
                json.dump(private, stream, ensure_ascii=False, sort_keys=True)
            receipts.append(
                {
                    "filename": filename_receipt,
                    "sha256": digest(
                        (output_dir / filename_receipt).read_text(encoding="utf-8")
                    ),
                    "output_index": index,
                }
            )
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
            "result": {"input_receipts": receipts},
            "vram_peak_mb": runtime.torch.cuda.max_memory_allocated() / 1024**2,
        }
