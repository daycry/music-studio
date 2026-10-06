"""Preflight nativo en hijo CPU; el padre HTTP no importa torch/transformers."""

import ast
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from engine_common import EngineError
from input_profile import (
    DIT_LYRICS_LIMIT,
    DIT_TEXT_LIMIT,
    LM_CONTEXT,
    MAX_DURATION,
    SOURCE_HASHES,
    UPSTREAM_REVISION,
)


def digest(value):
    raw = (
        value.encode("utf-8")
        if isinstance(value, str)
        else json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )
    return hashlib.sha256(raw).hexdigest()


def native_templates(source):
    """Ejecuta solo métodos puros del código fijado, sin copiar plantillas."""
    import yaml

    source = Path(source)
    for path, expected in SOURCE_HASHES.items():
        if digest((source / path).read_bytes().decode("utf-8")) != expected:
            raise EngineError("WEIGHTS_MISMATCH", "Fuente del perfil no coincide")
    constants = runpy.run_path(str(source / "constants.py"))
    namespace = dict(constants, yaml=yaml)
    # get_global_gpu_config solo aporta el límite explícito del tier elegido.
    tree = ast.parse((source / "gpu_config.py").read_text(encoding="utf-8"))
    tiers = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "GPU_TIER_CONFIGS" for t in n.targets
        )
    )
    assert tiers["tier4"]["max_duration_with_lm"] == MAX_DURATION
    namespace["get_global_gpu_config"] = lambda: SimpleNamespace(
        max_duration_with_lm=MAX_DURATION
    )
    selected = {
        "llm_inference.py": (
            "LLMHandler",
            {
                "_format_metadata_as_cot",
                "build_formatted_prompt_with_cot",
                "_has_meaningful_negative_prompt",
                "_compute_max_new_tokens",
            },
        ),
        "core/generation/handler/metadata_utils.py": ("MetadataMixin", None),
        "core/generation/handler/prompt_utils.py": (
            "PromptMixin",
            {
                "_format_instruction",
                "_format_lyrics",
                "build_dit_inputs",
            },
        ),
    }
    for filename, (classname, names) in selected.items():
        tree = ast.parse((source / filename).read_text(encoding="utf-8"))
        original = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == classname
        )
        cls = ast.ClassDef(
            name=classname,
            bases=[],
            keywords=[],
            decorator_list=[],
            body=[
                n
                for n in original.body
                if isinstance(n, ast.FunctionDef) and (names is None or n.name in names)
            ],
        )
        module = ast.Module(
            body=[
                ast.ImportFrom(
                    module="__future__", names=[ast.alias(name="annotations")], level=0
                ),
                cls,
            ],
            type_ignores=[],
        )
        exec(compile(ast.fix_missing_locations(module), filename, "exec"), namespace)  # noqa: S102 - método puro de fuente SHA-256 fijada
    lm = namespace["LLMHandler"]()
    lm.max_model_len = LM_CONTEXT
    lm.use_legacy_cfg_prompt = False
    conditioning = type(
        "Conditioning", (namespace["PromptMixin"], namespace["MetadataMixin"]), {}
    )()
    return lm, conditioning


def token_record(tokenizer, text):
    ids = tokenizer(text, truncation=False)["input_ids"]
    return {
        "count": len(ids),
        "input_sha256": digest(text),
        "tokens_sha256": digest(ids),
    }


def enforce_budget(lm, dit, reserve):
    if any(branch["count"] + reserve > LM_CONTEXT for branch in lm.values()):
        raise EngineError(
            "INVALID_PARAMS", "Entrada y salida exceden el presupuesto LM"
        )
    if (
        dit["text"]["count"] > DIT_TEXT_LIMIT
        or dit["lyrics"]["count"] > DIT_LYRICS_LIMIT
    ):
        raise EngineError("INVALID_PARAMS", "Entrada excede el presupuesto DiT")


def native_plan(request, lm_tokenizer, dit_tokenizer, source, checkpoint=None):
    from adapter import generation_options

    values, config = generation_options(
        {**request, "seed": request.get("seed") or 0}, 0, checkpoint
    )
    lm, dit = native_templates(source)
    lm.llm_tokenizer = lm_tokenizer
    metadata = {
        "duration": int(values["duration"]),
        "language": values["vocal_language"],
    }
    for key in ("bpm", "keyscale", "timesignature"):
        if (
            values.get(key) is not None
            and values.get(key) != ""
            and (key == "bpm" or values[key].lower() != "n/a")
        ):
            metadata[key] = values[key]
    cot = lm._format_metadata_as_cot(metadata)
    conditional = lm.build_formatted_prompt_with_cot(
        values["caption"], values["lyrics"], cot
    )
    unconditional = lm.build_formatted_prompt_with_cot(
        values["caption"],
        values["lyrics"],
        cot,
        is_negative_prompt=True,
        negative_prompt=values["lm_negative_prompt"],
    )
    reserve = lm._compute_max_new_tokens(values["duration"], "codes")
    if reserve != int(values["duration"] * 5) + 10:
        raise EngineError("INVALID_PARAMS", "Reserva LM limitada por el perfil")
    metas = dit._build_metadata_dict(
        values["bpm"],
        values["keyscale"],
        values.get("timesignature", ""),
        values["duration"],
    )
    text, lyrics = dit.build_dit_inputs(
        "text2music",
        None,
        values["caption"],
        values["lyrics"],
        metas,
        values["vocal_language"],
    )
    lm_branches = {
        "conditional": token_record(lm_tokenizer, conditional),
        "unconditional": token_record(lm_tokenizer, unconditional),
    }
    dit_branches = {
        "text": token_record(dit_tokenizer, text),
        "lyrics": token_record(dit_tokenizer, lyrics),
    }
    enforce_budget(lm_branches, dit_branches, reserve)
    effective = {
        "params": values,
        "config": config,
        "lm_metadata": metadata,
        "lm_cfg_scale": 2.0,
        "thinking": True,
        "inference_steps": values["inference_steps"],
        "guidance_scale": values["guidance_scale"],
        "shift": values.get("shift", 1.0),
        "audio_cover_strength": 1.0,
        "legacy_cfg_prompt": False,
    }
    if request.get("seed") is None:
        effective["params"]["seed"] = None
        effective["config"]["seeds"] = None
    return {
        "receipt_version": 1,
        "kind": "planned",
        "profile_revision": UPSTREAM_REVISION,
        "profile_sha256": digest(SOURCE_HASHES),
        "source_hashes": SOURCE_HASHES,
        "request_sha256": digest(request),
        "request": request,
        "effective_sha256": digest(effective),
        "effective": effective,
        "lm": {**lm_branches, "reserve_tokens": reserve, "context_policy": LM_CONTEXT},
        "dit": dit_branches,
    }


def verified_tokenizers(checkpoints, lm):
    from descriptor import locked_model
    from transformers import AutoTokenizer

    hashes = []
    components = {
        c["id"]: c
        for c in locked_model(checkpoints.parents[1] / "models.lock.json")["components"]
    }
    paths = []
    for name in (lm, "Qwen3-Embedding-0.6B"):
        component = components[name]
        folder = checkpoints / component["dest_subdir"]
        expected_paths = set()
        for entry in component["files"]:
            if entry["path"].endswith((".json", ".jinja", ".txt")):
                expected_paths.add(entry["path"])
                path = folder / entry["path"]
                if (
                    not path.is_file()
                    or path.is_symlink()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]
                ):
                    raise EngineError(
                        "WEIGHTS_MISMATCH", "Tokenizador/configuración no coincide"
                    )
                hashes.append(
                    {
                        "component": name,
                        "path": entry["path"],
                        "sha256": entry["sha256"],
                    }
                )
        actual = {
            p.relative_to(folder).as_posix()
            for p in folder.rglob("*")
            if p.is_file() and p.suffix in {".json", ".jinja", ".txt"}
        }
        if actual != expected_paths:
            raise EngineError("WEIGHTS_MISMATCH", "Configuración adicional no fijada")
        paths.append(folder)
    return [
        AutoTokenizer.from_pretrained(
            str(p), local_files_only=True, trust_remote_code=False
        )
        for p in paths
    ], hashes


def verified_checkpoint_profile(checkpoints, checkpoint):
    from descriptor import locked_model

    try:
        component = next(
            c
            for c in locked_model(checkpoints.parents[1] / "models.lock.json")[
                "components"
            ]
            if c["id"] == checkpoint
        )
        entry = next(f for f in component["files"] if f["path"] == "config.json")
        path = checkpoints / component["dest_subdir"] / entry["path"]
        payload = path.read_bytes()
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(checkpoints.resolve())
            or hashlib.sha256(payload).hexdigest() != entry["sha256"]
        ):
            raise ValueError()
        config = json.loads(payload)
        if not isinstance(config, dict):
            raise TypeError()
    except (StopIteration, OSError, ValueError, KeyError, TypeError):
        raise EngineError(
            "WEIGHTS_MISMATCH", "Configuración DiT no fijada o alterada"
        ) from None
    if config.get("is_lego_sft", False):
        # conditioning_text.py:72/104: plantilla de pista Global/Local;
        # music.song/instrumental M0 solo exponen text2music de canción completa.
        raise EngineError(
            "INVALID_PARAMS", "Perfil SFT-stems requiere una capacidad no expuesta"
        )
    return {"id": checkpoint, "config_sha256": entry["sha256"], "is_lego_sft": False}


def worker(
    request,
    checkpoints,
    lm,
    source=Path("/opt/acestep/acestep"),
    checkpoint="acestep-v15-turbo",
):
    checkpoint_profile = verified_checkpoint_profile(Path(checkpoints), checkpoint)
    tokenizers, hashes = verified_tokenizers(Path(checkpoints), lm)
    result = native_plan(request, *tokenizers, source, checkpoint)
    result["tokenizer_hashes"] = hashes
    result["checkpoint"] = checkpoint_profile
    return result


def preflight(request, *, checkpoints=None, lm=None, checkpoint=None, timeout=60):
    from descriptor import CHECKPOINT, LM, model_root

    checkpoints = checkpoints or model_root() / "ace-step-1.5/checkpoints"
    environment = dict(
        os.environ,
        CUDA_VISIBLE_DEVICES="",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker"],
            input=json.dumps(
                {
                    "request": request,
                    "checkpoints": str(checkpoints),
                    "lm": lm or LM,
                    "checkpoint": checkpoint or CHECKPOINT,
                }
            ),
            text=True,
            capture_output=True,
            timeout=timeout,
            env=environment,
            check=False,
        )
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise EngineError("INTERNAL", "Respuesta de preflight no válida")
        if result.returncode or "error" in payload:
            code = payload.get("error", "INTERNAL")
            if code not in {
                "INVALID_PARAMS",
                "WEIGHTS_MISMATCH",
                "TIMEOUT",
                "INTERNAL",
            }:
                code = "INTERNAL"
            raise EngineError(code, "Preflight nativo rechazado")
        if (
            payload.get("kind") != "planned"
            or payload.get("receipt_version") != 1
            or payload.get("profile_sha256") != digest(SOURCE_HASHES)
            or payload.get("request_sha256") != digest(request)
            or payload.get("effective_sha256") != digest(payload.get("effective"))
            or not payload.get("tokenizer_hashes")
            or payload.get("checkpoint", {}).get("id") != (checkpoint or CHECKPOINT)
        ):
            raise EngineError("INTERNAL", "Respuesta de preflight no válida")
        enforce_budget(
            {k: payload["lm"][k] for k in ("conditional", "unconditional")},
            payload["dit"],
            payload["lm"]["reserve_tokens"],
        )
        return payload
    except subprocess.TimeoutExpired:
        raise EngineError("TIMEOUT", "Preflight nativo agotó el plazo") from None
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        raise EngineError("INTERNAL", "Preflight nativo no disponible") from None


if __name__ == "__main__":
    try:
        args = json.load(sys.stdin)
        payload = worker(**args)
        print(json.dumps(payload))
    except Exception as error:  # noqa: BLE001 - frontera privada; nunca stderr/texto upstream
        print(
            json.dumps(
                {"error": error.code if isinstance(error, EngineError) else "INTERNAL"}
            )
        )
        sys.exit(1)
