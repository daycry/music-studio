"""Factoría privada T-10. Sólo importación de torch dentro del hijo GPU."""

import hashlib
import json
import os
import random
import re
import sys
from contextlib import contextmanager
from functools import wraps
from inspect import isfunction
from pathlib import Path

from scripts.eval.capabilities_evidence import (
    compare_pcm,
    exclusive_json,
    file_record,
    pcm_record,
)


def native_values(row, request, fixture):
    p = request["params"]
    values = {
        "task_type": "text2music",
        "caption": p["style"],
        "lyrics": p["lyrics"],
        "duration": p["duration_s"],
        "seed": request["seed"],
        "inference_steps": p.get("inference_steps", 8),
        "guidance_scale": p.get("guidance_scale", 7.0),
        "shift": p.get("shift", 1.0),
        "thinking": True,
        "lm_cfg_scale": 2.0,
        "vocal_language": "es",
        "enable_normalization": False,
        "use_cot_metas": False,
        "use_cot_caption": False,
        "use_cot_language": False,
        "lm_negative_prompt": p.get("negative_prompt", "NO USER INPUT"),
        "bpm": p.get("bpm"),
        "keyscale": p.get("key", ""),
    }
    case, control = row["case"], row["control"]
    if case == "music.instrumental":
        values.update(instrumental=True, lyrics="[Instrumental]")
    if case in (
        "music.retake",
        "music.cover",
        "music.repaint",
        "music.extend",
        "music.complete",
        "audio.stems",
    ):
        values["src_audio"] = (
            fixture["padded_source"]
            if case == "music.extend"
            else fixture["vocals"]
            if case == "music.complete"
            else fixture["source"]
        )
        values["task_type"] = {
            "music.retake": "cover",
            "music.cover": "cover",
            "music.repaint": "repaint",
            "music.extend": "repaint",
            "music.complete": "complete",
            "audio.stems": "extract",
        }[case]
        if case == "music.complete":
            # Upstream complete is not a skip-LM task. Codes replace source audio.
            values["thinking"] = False
            values["audio_codes"] = ""
        values.update(
            {
                k: v
                for k, v in control.items()
                if k not in ("pad_s", "complete_track_classes", "track_name")
            }
        )
    if case == "timbre_ref" and control["reference"]:
        values["reference_audio"] = fixture["references"][control["reference"]]["path"]
    return values


def contained(root, value):
    path = (Path(root) / value).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("outside_project")
    return path


def validate_audio_resources(fixture, root):
    paths = [fixture[k] for k in ("source", "vocals") if fixture.get(k)]
    paths.extend(r["path"] for r in fixture.get("references", {}).values())
    paths.extend(fixture.get("ground_truth", {}).get("tracks", {}).values())
    for value in paths:
        rights = fixture.get("rights", {}).get(value, {})
        seal = fixture.get("input_seals", {}).get(value)
        if (
            not seal
            or rights.get("authorized") is not True
            or not rights.get("provenance")
            or (rights.get("real_voice") and rights.get("consent") is not True)
        ):
            raise ValueError("audio_rights_prerequisite")
        if file_record(contained(root, value)) != seal:
            raise ValueError("audio_input_changed")


def validate_lora(resource, root):
    required = (
        "path",
        "checkpoint",
        "license",
        "commercial_use",
        "dataset_provenance",
        "consent",
        "files",
        "loader_audit",
    )
    if (
        not all(k in resource for k in required)
        or resource["consent"] is not True
        or not isinstance(resource["dataset_provenance"], str)
        or not resource["dataset_provenance"].strip()
        or not isinstance(resource["license"], str)
        or not resource["license"].strip()
        or type(resource["commercial_use"]) is not bool
    ):
        raise ValueError("lora_prerequisite")
    revision = resource.get("revision", "")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("lora_prerequisite_revision")
    if (
        resource["commercial_use"] is False
        and resource.get("laboratory_only") is not True
    ):
        raise ValueError("lora_prerequisite_laboratory_only")
    try:
        lock = json.loads((Path(root) / "models/models.lock.json").read_text())
        entry = lock["models"][resource["id"]]
        if entry["kind"] != "lora" or entry["dest"] != resource["path"]:
            raise ValueError
        for name in (
            "revision",
            "checkpoint",
            "license",
            "commercial_use",
            "dataset_provenance",
            "consent",
            "loader_audit",
        ):
            if entry[name] != resource[name]:
                raise ValueError
        registered = {
            f["path"]: {"sha256": f["sha256"], "bytes": f["bytes"]}
            for f in entry["files"]
        }
        if registered != resource["files"]:
            raise ValueError
    except (KeyError, OSError, ValueError, TypeError) as error:
        raise ValueError("lora_prerequisite_registration") from error
    if "newyear" in resource["path"].lower():
        raise ValueError("lora_prerequisite_rejected_provenance")
    folder = contained(root, resource["path"])
    expected = {"adapter_config.json", "adapter_model.safetensors"}
    if (
        set(resource["files"]) != expected
        or {p.name for p in folder.iterdir()} != expected
    ):
        raise ValueError("lora_prerequisite_safe_files")
    for name, seal in resource["files"].items():
        if file_record(folder / name) != seal:
            raise ValueError("lora_prerequisite_hash")
    config = json.loads((folder / "adapter_config.json").read_text())
    if config.get("peft_type") != "LORA" or config.get("auto_mapping"):
        raise ValueError("lora_prerequisite_config")
    lora_audit(resource, root)
    return folder


PEFT_SOURCES = {
    "peft/peft_model.py",
    "peft/config.py",
    "peft/utils/other.py",
    "peft/utils/save_and_load.py",
}


def lora_audit(resource, root):
    """Recibo aprobado fijado por el registro, ligado al loader y fuentes PEFT."""
    try:
        ref = resource["loader_audit"]
        receipt = contained(root, ref["receipt"])
        if file_record(receipt) != ref["seal"]:
            raise ValueError
        audit = json.loads(receipt.read_text())
        loader = audit["safe_loader"]
        if (
            audit["status"] != "approved"
            or audit["peft_version"] != "0.18.1"
            or not audit["reviewer"]
            or not audit["reviewed_at"]
            or set(audit["source_files"]) != PEFT_SOURCES
            or loader["path"] != "scripts/eval/capabilities_native.py"
            or loader["local_safetensors_only"] is not True
            or loader["alias_loader_no_fallback"] is not True
            or file_record(contained(root, loader["path"])) != loader["seal"]
        ):
            raise ValueError
        for path, seal in audit["source_files"].items():
            if file_record(contained(root, path)) != seal:
                raise ValueError
        return audit
    except (KeyError, OSError, ValueError, TypeError) as error:
        raise ValueError("lora_prerequisite_loader_audit") from error


@contextmanager
def safe_lora_weights(folder, audit):
    """Sustituye todos los alias PEFT por carga local safetensors, sin fallback."""
    import peft
    import peft.utils.save_and_load as loading
    from safetensors.torch import load_file

    if peft.__version__ != "0.18.1":
        raise ValueError("peft_version_changed")
    if file_record(Path(__file__)) != audit["safe_loader"]["seal"]:
        raise ValueError("lora_runtime_loader_changed")
    package = Path(peft.__file__).resolve().parent
    for path, seal in audit["source_files"].items():
        if file_record(contained(package.parent, path)) != seal:
            raise ValueError("peft_runtime_source_changed")
    for name in (
        "peft.peft_model",
        "peft.config",
        "peft.utils.other",
        "peft.utils.save_and_load",
    ):
        from importlib import import_module

        module = import_module(name)
        expected = package.parent / (name.replace(".", "/") + ".py")
        if Path(module.__file__).resolve() != expected.resolve():
            raise ValueError("peft_runtime_module_changed")
    original = loading.load_peft_weights
    replacements = []

    def local_weights(model_id, device=None, **kwargs):
        if Path(model_id).resolve() != folder.resolve():
            raise ValueError("lora_loader_nonlocal")
        return load_file(str(folder / "adapter_model.safetensors"), device="cpu")

    for module in tuple(sys.modules.values()):
        if module and getattr(module, "__name__", "").startswith("peft"):
            for name, value in tuple(vars(module).items()):
                if value is original:
                    replacements.append((module, name, value))
                    setattr(module, name, local_weights)
    try:
        yield
    finally:
        for module, name, value in reversed(replacements):
            setattr(module, name, value)


def array(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu().float().numpy()
    import numpy as np

    result = np.asarray(value, dtype=np.float32)
    return result[0] if result.ndim == 3 and result.shape[0] == 1 else result


@contextmanager
def capture_boundaries(runtime, folder, control, python_seed):
    """Wrappers temporales: no modifican retornos ni fuentes upstream."""
    import importlib

    module = importlib.import_module("acestep.core.generation.handler.generate_music")
    saved = []
    captured = {
        "python_seed": python_seed,
        "reference_offsets": [],
        "states": {},
        "boundaries": [],
    }
    state = random.getstate()
    random.seed(python_seed)

    def save(name, value):
        import numpy as np

        samples = array(value)
        pcm_record(samples)
        path = folder / f"{name}.npy"
        with path.open("xb") as stream:
            np.save(stream, samples, allow_pickle=False)
        captured["states"][name] = {
            **pcm_record(samples),
            "file": path.name,
            **file_record(path),
        }

    def wrap(obj, name, build):
        original = getattr(obj, name)
        saved.append((obj, name, original))
        wrapped = build(original)
        if isfunction(wrapped):
            wrapped = wraps(original)(wrapped)
        setattr(obj, name, wrapped)

    def decode(original):
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            save("pre_splice", result[0])
            return result

        return call

    def source(original):
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            if result is not None:
                save("processed_source", result)
            return result

        return call

    def splice(original):
        def call(*args, **kwargs):
            save("splice_source", kwargs["src_wavs"])
            captured["crossfade_duration_effective"] = kwargs["crossfade_duration"]
            result = original(*args, **kwargs)
            save("post_splice", result)
            return result

        return call

    def reference(original):
        def call(*args, **kwargs):
            offsets = []
            old = random.randint

            def randint(a, b):
                result = old(a, b)
                offsets.append({"low": a, "high": b, "draw": result})
                return result

            random.randint = randint
            try:
                result = original(*args, **kwargs)
            finally:
                random.randint = old
            captured["reference_offsets"] = offsets
            if result is not None:
                samples = array(result)
                save("reference_segments", samples)
                captured["reference_segment_sha256"] = [
                    pcm_record(samples[:, i * 480000 : (i + 1) * 480000])["sha256"]
                    for i in range(3)
                ]
            return result

        return call

    def lm_arguments(original):
        def call(*args, **kwargs):
            kwargs["user_metadata"] = {
                **(kwargs.get("user_metadata") or {}),
                "language": "es",
            }
            clean = {k: v for k, v in kwargs.items() if k != "progress"}
            captured["boundaries"].append({"stage": "lm_arguments", "arguments": clean})
            return original(*args, **kwargs)

        return call

    def formatted(original):
        def call(formatted_prompt, cfg, **kwargs):
            captured["boundaries"].append(
                {
                    "stage": "lm_formatted_prompt",
                    "prompt": formatted_prompt,
                    "cfg": cfg,
                    "prompt_sha256": hashlib.sha256(
                        formatted_prompt.encode()
                    ).hexdigest(),
                }
            )
            tokenizer = getattr(runtime.lm, "llm_tokenizer", None)
            if tokenizer is not None:
                from preflight import token_record

                tokens = token_record(tokenizer, formatted_prompt)
                reserve = runtime.lm._compute_max_new_tokens(
                    cfg["target_duration"], cfg["generation_phase"]
                )
                captured["boundaries"][-1].update(tokens=tokens, reserve_tokens=reserve)
                if tokens["count"] + reserve > 4096:
                    raise ValueError("native_lm_budget_exceeded")
            return original(formatted_prompt, cfg, **kwargs)

        return call

    def dit_arguments(original):
        def call(*args, **kwargs):
            clean = {
                k: v
                for k, v in kwargs.items()
                if k != "progress"
                and isinstance(v, (str, int, float, bool, list, dict, type(None)))
            }
            captured["boundaries"].append(
                {
                    "stage": "dit_arguments",
                    "arguments": clean,
                    "arguments_sha256": hashlib.sha256(
                        json.dumps(clean, sort_keys=True).encode()
                    ).hexdigest(),
                }
            )
            return original(*args, **kwargs)

        return call

    class TokenizerCapture:
        def __init__(self, original):
            self.original = original

        def __getattr__(self, name):
            return getattr(self.original, name)

        def __call__(self, text, **kwargs):
            probe = self.original(text, **{**kwargs, "truncation": False})
            ids = probe.input_ids[0]
            if hasattr(ids, "detach"):
                ids = ids.detach().cpu()
            tokens = ids.tolist()
            limit = kwargs.get("max_length")
            record = {
                "stage": "dit_tokenizer",
                "text": text,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "tokens": tokens,
                "token_count": len(tokens),
                "max_length": limit,
                "truncation_requested": kwargs.get("truncation", False),
            }
            captured["boundaries"].append(record)
            if limit and len(tokens) > limit:
                raise ValueError("native_dit_budget_exceeded")
            return self.original(text, **kwargs)

    try:
        wrap(runtime.dit, "_decode_generate_music_pred_latents", decode)
        wrap(runtime.dit, "process_src_audio", source)
        wrap(runtime.dit, "process_reference_audio", reference)
        wrap(module, "apply_repaint_waveform_splice", splice)
        wrap(runtime.lm, "generate_with_stop_condition", lm_arguments)
        wrap(runtime.lm, "generate_from_formatted_prompt", formatted)
        wrap(runtime.dit, "generate_music", dit_arguments)
        if hasattr(runtime.dit, "text_tokenizer"):
            wrap(runtime.dit, "text_tokenizer", TokenizerCapture)
        yield captured
    finally:
        random.setstate(state)
        for obj, name, original in reversed(saved):
            setattr(obj, name, original)


class NativeLabAdapter:
    """Reutiliza carga BF16/guardas del adapter congelado, factoría no pública."""

    def __init__(
        self, checkpoint, lm, resource_root, root, source_seal, upstream_seal=None
    ):
        self.root = Path(root).resolve()
        self.source_seal = source_seal
        self.upstream_seal = upstream_seal
        self.checkpoint = checkpoint
        from adapter import AceStepAdapter

        self.base = AceStepAdapter(
            checkpoint=checkpoint, lm=lm, resource_root=resource_root
        )

    def load(self, model_id, mode, cap_mb, total_mb):
        if (
            not Path("/.dockerenv").exists()
            or os.environ.get("HF_HUB_OFFLINE") != "1"
            or os.environ.get("TRANSFORMERS_OFFLINE") != "1"
        ):
            raise ValueError("container_offline_required")
        if not self.source_seal:
            raise ValueError("sealed_factory_required")
        for path, seal in self.source_seal.items():
            if file_record(contained(self.root, path)) != seal:
                raise ValueError("sealed_factory_changed")
        if not self.upstream_seal:
            raise ValueError("upstream_seal_required")
        from importlib.util import find_spec

        source = Path(find_spec("acestep").origin).parent
        for path, seal in self.upstream_seal.items():
            if file_record(contained(source, path)) != seal:
                raise ValueError("pinned_upstream_changed")
        self.base.load(model_id, mode, cap_mb, total_mb)

    def generate(self, request, output_dir, emit, token):
        import soundfile as sf
        from adapter import (
            private_upstream_output,
            step_hooks,
            timed_generation,
            upstream_call,
            write_wav,
        )

        row, fixture = request["capability_row"], request["fixture"]
        validate_audio_resources(fixture, self.root)
        expected = self.root / "data" / "tmp" / request["job_id"]
        if Path(output_dir).resolve() != expected.resolve():
            raise ValueError("raw_output_only")
        runtime = self.base.runtime
        values = native_values(row, request, fixture)
        values["instruction"] = runtime.dit.generate_instruction(
            values["task_type"],
            **{
                k: v
                for k, v in row["control"].items()
                if k in ("track_name", "complete_track_classes")
            },
        )
        for name in ("src_audio", "reference_audio"):
            if values.get(name):
                path = contained(self.root, values[name])
                values[name] = str(path)
                samples, rate = sf.read(path, dtype="float32", always_2d=True)
                if rate != 48000 or samples.shape[1] != 2:
                    raise ValueError("source_48k_stereo_required")
                if name == "src_audio":
                    import numpy as np

                    if np.max(np.abs(samples)) > 0.8:
                        raise ValueError("source_amplitude")
                    with (output_dir / "original_source.npy").open("xb") as stream:
                        np.save(stream, samples.T, allow_pickle=False)
        if row["case"] == "lora":
            resource = fixture["lora"]
            if resource["checkpoint"] != self.checkpoint:
                raise ValueError("lora_checkpoint_mismatch")
            folder = validate_lora(resource, self.root)
            with (
                private_upstream_output(),
                safe_lora_weights(folder, lora_audit(resource, self.root)),
            ):
                runtime.dit.load_lora(str(folder))
                if not runtime.dit.lora_loaded:
                    raise ValueError("lora_load_failed")
                runtime.dit.set_lora_scale(row["control"]["lora_scale"])
                runtime.dit.use_lora = row["control"]["lora_scale"] != 0
        token.check()

        def progress(value, desc=None, **kwargs):
            token.check()
            emit(("progress", {"fraction": float(value), "description": desc}))

        params = runtime.GenerationParams(**values)
        config = runtime.GenerationConfig(
            batch_size=1,
            use_random_seed=False,
            seeds=[row["seed"]],
            allow_lm_batch=False,
        )
        with (
            private_upstream_output(),
            step_hooks(runtime, token, progress, values["inference_steps"]),
            capture_boundaries(
                runtime,
                output_dir,
                row["control"],
                row["control"].get("python_seed", 501),
            ) as captured,
        ):
            result, timing = timed_generation(
                runtime,
                lambda: upstream_call(
                    "laboratorio nativo",
                    runtime.generate_music,
                    runtime.dit,
                    runtime.lm,
                    params,
                    config,
                    save_dir=None,
                    progress=progress,
                ),
            )
        token.check()
        if not result.success or len(result.audios) != 1:
            raise ValueError("native_generation_failed")
        audio = result.audios[0]
        path = output_dir / "output-0.wav"
        if path.exists():
            raise FileExistsError(path)
        write_wav(path, audio["tensor"], audio["sample_rate"])
        comparisons = {}
        if row["case"] in ("music.repaint", "music.extend"):
            import numpy as np

            for name in ("original_source", "processed_source", "splice_source"):
                source = output_dir / f"{name}.npy"
                if source.exists():
                    original = np.load(source, allow_pickle=False)
                    for state in ("pre_splice", "post_splice"):
                        target = output_dir / f"{state}.npy"
                        if target.exists():
                            comparisons[f"{name}:{state}"] = compare_pcm(
                                original,
                                np.load(target, allow_pickle=False),
                                int(row["control"]["repainting_start"] * 48000),
                                int(row["control"]["repainting_end"] * 48000),
                                crossfade_frames=int(
                                    captured.get("crossfade_duration_effective", 0)
                                    * 48000
                                ),
                            )
        receipt = {
            "surface": "native_lab",
            "params_effective": vars(params),
            "config_effective": vars(config),
            "captured": captured,
            "comparisons": comparisons,
            "runtime_effective": self.base.effective,
            "timing": timing,
            "audio_params_effective": audio.get("params"),
            "lm_policy": {
                "thinking_effective": values["thinking"],
                "reason": "complete_consumes_vocals_without_lm_codes"
                if row["case"] == "music.complete"
                else "upstream_task_skips_lm"
                if values["task_type"] in ("cover", "repaint", "extract")
                else "text2music_uses_lm_codes_cfg2",
            },
            "verified": False,
        }
        exclusive_json(output_dir / "native-receipt.json", receipt)
        return {
            "artifacts": [
                {
                    "filename": "output-0.wav",
                    "output_index": 0,
                    "media_type": "audio/wav",
                    "meta": {"seed": row["seed"], "sample_rate": 48000, "channels": 2},
                }
            ],
            "result": receipt,
            "vram_peak_mb": runtime.torch.cuda.max_memory_allocated() / 1024**2,
        }
