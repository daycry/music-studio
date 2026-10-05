"""Regresiones B1/B2: parser upstream real y errores CPU tipados."""

import ast
import hashlib
import random
from pathlib import Path
from types import SimpleNamespace

import adapter
import numpy as np
import pytest
from engine_common.runtime import CancelToken, EngineError


@pytest.fixture
def isolated_token_preflight(monkeypatch):
    """Aísla conteo CPU; estos dobles prueban parser de semillas/errores VRAM."""
    calls = []

    def token_preflight(request, **kwargs):
        calls.append((request, kwargs))
        return {"kind": "planned", "request_sha256": adapter.digest(request)}

    monkeypatch.setattr(adapter, "preflight", token_preflight)
    return calls


def real_seed_parser():
    root = Path("/opt/acestep/acestep")
    if not root.exists():
        root = (
            Path(__file__).resolve().parents[4]
            / ".cache/dev-cycle/t06/upstream/acestep"
        )
    source = root / "core/generation/handler/task_utils.py"
    assert (
        hashlib.sha256(source.read_bytes()).hexdigest()
        == "a5c90c6af54d1eb207cbf79db39535e115361542cb37735ed4359287bd257a66"
    )
    tree = ast.parse(source.read_text(encoding="utf-8"))
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "prepare_seeds"
    )
    namespace = {
        "random": random,
        "List": list,
        "Tuple": tuple,
        "logger": SimpleNamespace(
            debug=lambda *args: None, exception=lambda *args: None
        ),
    }
    exec(  # noqa: S102 - sólo el método upstream fijado por hash, extracción AST sin importar torch
        compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    return namespace["prepare_seeds"]


def test_large_seeds_exact_distinct_after_real_parser(
    tmp_path, isolated_token_preflight
):
    from types import MethodType

    parser = real_seed_parser()
    base = 9007199254740992
    assert parser(None, 1, str(base + 1), False)[0] == [base], (
        "Reproducción del redondeo upstream fijado"
    )
    handler = SimpleNamespace()
    handler.prepare_seeds = MethodType(parser, handler)
    adapter.configure_handler(handler)
    used = []

    def generate(dit, lm, params, config, **kwargs):
        seed = dit.prepare_seeds(1, ",".join(str(s) for s in config["seeds"]), False)[
            0
        ][0]
        used.append(seed)
        return SimpleNamespace(
            success=True,
            audios=[
                {"tensor": np.full((2, 8), 0.1, dtype="float32"), "sample_rate": 48000}
            ],
        )

    model = adapter.AceStepAdapter()
    model.runtime = SimpleNamespace(
        dit=handler,
        lm=None,
        generate_music=generate,
        GenerationParams=lambda **kw: kw,
        GenerationConfig=lambda **kw: kw,
        torch=SimpleNamespace(cuda=SimpleNamespace(max_memory_allocated=lambda: 0)),
    )
    request = {
        "task": "music.instrumental",
        "params": {"style": "jazz", "duration_s": 30},
        "seed": base,
        "n_outputs": 2,
    }
    result = model.generate(request, tmp_path, lambda event: None, CancelToken())
    assert used == [base, base + 1]
    assert [item["meta"]["seed"] for item in result["artifacts"]] == used
    assert [call[0]["seed"] for call in isolated_token_preflight] == used
    assert all(call[0]["n_outputs"] == 1 for call in isolated_token_preflight)
    assert all(
        call[1]["checkpoint"] == model.checkpoint for call in isolated_token_preflight
    )


@pytest.mark.parametrize("phase", ["dit", "lm", "generate"])
def test_cuda_oom_status_becomes_vram_exceeded(
    monkeypatch, tmp_path, phase, isolated_token_preflight
):
    private = "CUDA out of memory. token=do-not-expose /private/model"
    cuda = SimpleNamespace(
        is_available=lambda: True,
        is_bf16_supported=lambda: True,
        set_per_process_memory_fraction=lambda f: None,
        reset_peak_memory_stats=lambda: None,
    )
    runtime = SimpleNamespace(
        torch=SimpleNamespace(cuda=cuda, bfloat16="bf16"),
        dit=SimpleNamespace(
            dtype="bf16",
            device="cuda",
            initialize_service=lambda **kw: (
                private if phase == "dit" else "ok",
                phase != "dit",
            ),
        ),
        lm=SimpleNamespace(
            initialize=lambda **kw: (private if phase == "lm" else "ok", phase != "lm")
        ),
        generate_music=lambda *args, **kwargs: SimpleNamespace(
            success=False, audios=[], error=private, status_message=private
        ),
        GenerationParams=lambda **kw: kw,
        GenerationConfig=lambda **kw: kw,
    )
    monkeypatch.setattr(adapter, "prepare_runtime", lambda *args: runtime)
    model = adapter.AceStepAdapter()
    with pytest.raises(EngineError) as caught:
        model.load("ace-step-1.5-turbo", "bf16", 100, 200)
        model.generate(
            {
                "task": "music.instrumental",
                "params": {"style": "jazz", "duration_s": 30},
                "n_outputs": 1,
                "seed": 42,
            },
            tmp_path,
            lambda event: None,
            CancelToken(),
        )
    assert caught.value.code == "VRAM_EXCEEDED"
    assert (
        "do-not-expose" not in caught.value.message
        and "/private" not in caught.value.message
    )
    assert [call[0]["seed"] for call in isolated_token_preflight] == (
        [42] if phase == "generate" else []
    )
    assert all(call[0]["n_outputs"] == 1 for call in isolated_token_preflight)


@pytest.mark.parametrize("phase", ["dit", "lm", "generate"])
def test_cuda_oom_exception_becomes_vram_exceeded(
    monkeypatch, tmp_path, phase, isolated_token_preflight
):
    def fail(**kwargs):
        raise RuntimeError("CUDA out of memory. token=do-not-expose /private/model")

    cuda = SimpleNamespace(
        is_available=lambda: True,
        is_bf16_supported=lambda: True,
        set_per_process_memory_fraction=lambda f: None,
        reset_peak_memory_stats=lambda: None,
    )
    runtime = SimpleNamespace(
        torch=SimpleNamespace(cuda=cuda, bfloat16="bf16"),
        dit=SimpleNamespace(
            dtype="bf16",
            device="cuda",
            initialize_service=fail if phase == "dit" else lambda **kw: ("ok", True),
        ),
        lm=SimpleNamespace(
            initialize=fail if phase == "lm" else lambda **kw: ("ok", True)
        ),
        generate_music=lambda *args, **kwargs: fail(),
        GenerationParams=lambda **kw: kw,
        GenerationConfig=lambda **kw: kw,
    )
    monkeypatch.setattr(adapter, "prepare_runtime", lambda *args: runtime)
    model = adapter.AceStepAdapter()
    with pytest.raises(EngineError) as caught:
        model.load("ace-step-1.5-turbo", "bf16", 100, 200)
        model.generate(
            {
                "task": "music.instrumental",
                "params": {"style": "jazz", "duration_s": 30},
                "n_outputs": 1,
                "seed": 42,
            },
            tmp_path,
            lambda event: None,
            CancelToken(),
        )
    assert caught.value.code == "VRAM_EXCEEDED"
    assert (
        "do-not-expose" not in caught.value.message
        and "/private" not in caught.value.message
    )
    assert [call[0]["seed"] for call in isolated_token_preflight] == (
        [42] if phase == "generate" else []
    )
    assert all(call[0]["n_outputs"] == 1 for call in isolated_token_preflight)


def test_seed_overflow_rejected_before_any_generation(tmp_path):
    calls = []
    model = adapter.AceStepAdapter()
    model.runtime = SimpleNamespace(
        generate_music=lambda *args, **kwargs: calls.append(1)
    )
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        model.generate(
            {
                "task": "music.instrumental",
                "params": {"style": "jazz", "duration_s": 30},
                "seed": 2**64 - 1,
                "n_outputs": 2,
            },
            tmp_path,
            lambda event: None,
            CancelToken(),
        )
    assert calls == [] and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "value", ["", "-1", "1.5", "nan", "1e3", "1_2", None, 1.5, True, str(2**64)]
)
def test_explicit_invalid_seeds_never_fall_back_random(value):
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        adapter.exact_prepare_seeds(1, value, False)


def test_exact_seed_parser_boundaries_and_no_padding():
    assert adapter.exact_prepare_seeds(2, f"0,{2**64 - 1}", False)[0] == [0, 2**64 - 1]
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        adapter.exact_prepare_seeds(2, "42", False)
    assert len(adapter.exact_prepare_seeds(2, None, True)[0]) == 2


def test_error_classifier_safe_categories_and_engine_error_preservation():
    assert (
        adapter.upstream_error("generación", "VRAM budget exceeded /private").code
        == "VRAM_EXCEEDED"
    )
    assert (
        adapter.upstream_error("generación", "CPU out of memory /private").code
        == "INTERNAL"
    )
    assert (
        adapter.upstream_error("generación", "provider failure token=private").message
        == "Fallo interno durante generación"
    )
    Oom = type("OutOfMemoryError", (RuntimeError,), {})
    assert adapter.upstream_error("carga", Oom("opaque")).code == "VRAM_EXCEEDED"

    def typed():
        raise EngineError("CANCELLED")

    with pytest.raises(EngineError, match="CANCELLED"):
        adapter.upstream_call("generación", typed)
