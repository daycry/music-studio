"""Preflight real fijado por hash: sin imports de modelos ni trabajo GPU."""

import ast
import hashlib
import typing
from pathlib import Path
from types import SimpleNamespace

import adapter
import pytest
from engine_common.runtime import CancelToken, EngineError


def real_preflight(free_gb, cuda=True, offload=False):
    root = Path("/opt/acestep/acestep")
    if not root.exists():
        root = (
            Path(__file__).resolve().parents[4]
            / ".cache/dev-cycle/t06/upstream/acestep"
        )
    source = root / "core/generation/handler/generate_music.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        "4126b89bea9032d5ad1a5d9f906410ef4ede79a1d2328635aa365010473ee086"
    )
    method = next(
        node
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name == "_vram_preflight_check"
    )
    constants = {}
    for node in ast.parse((root / "gpu_config.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"DIT_INFERENCE_VRAM_PER_BATCH", "VRAM_SAFETY_MARGIN_GB"}:
                constants[name] = ast.literal_eval(node.value)
    namespace = {
        **constants,
        "Optional": typing.Optional,
        "Dict": dict,
        "Any": typing.Any,
        "torch": SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: cuda)),
        "logger": SimpleNamespace(
            debug=lambda *a: None, info=lambda *a: None, warning=lambda *a: None
        ),
        "get_dit_type_from_path": lambda path: "turbo",
        "get_effective_free_vram_gb": lambda: free_gb,
    }
    exec(  # noqa: S102 - método upstream hash-verificado extraído por AST, sin imports GPU
        compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    handler = SimpleNamespace(offload_to_cpu=offload)
    return lambda batch, duration: namespace["_vram_preflight_check"](
        handler, batch, duration, 1.0
    )


@pytest.mark.parametrize("batch,duration", [(1, 30), (2, 120)])
def test_real_preflight_failure_classified_vram(tmp_path, monkeypatch, batch, duration):
    native_calls = []

    def token_preflight(request, **kwargs):
        # Este doble aísla el presupuesto de tokens del preflight VRAM real probado.
        native_calls.append((request, kwargs))
        return {"kind": "planned", "request_sha256": adapter.digest(request)}

    monkeypatch.setattr(adapter, "preflight", token_preflight)
    result = real_preflight(0.1)(batch, duration)
    assert result["success"] is False and result["error"].startswith(
        "Insufficient free VRAM:"
    )
    model = adapter.AceStepAdapter()
    model.runtime = SimpleNamespace(
        dit=SimpleNamespace(),
        lm=None,
        generate_music=lambda *a, **kw: SimpleNamespace(**result),
        GenerationParams=lambda **kw: kw,
        GenerationConfig=lambda **kw: kw,
    )
    with pytest.raises(EngineError) as caught:
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
    assert caught.value.message == "VRAM insuficiente durante generación"
    assert list(tmp_path.iterdir()) == []
    assert len(native_calls) == 1
    assert native_calls[0][0]["seed"] == 42
    assert native_calls[0][0]["n_outputs"] == 1
    assert native_calls[0][1]["checkpoint"] == model.checkpoint


def test_preflight_isolation_and_equivalent_statuses():
    result = real_preflight(0.1)(1, 30)
    assert real_preflight(8)(1, 30) is None
    assert real_preflight(0.1, cuda=False)(1, 30) is None
    assert real_preflight(0.1, offload=True)(1, 30) is None
    text = result["error"].casefold()
    assert "vram" in text and "insufficient free vram" in text
    assert not any(
        reason in text
        for reason in (
            "out of memory",
            "outofmemoryerror",
            "budget exceeded",
            "memory allocation failed",
        )
    )
    for detail in (result["error"], result["status_message"]):
        error = adapter.upstream_error("generación", detail + " token=private /private")
        assert error.code == "VRAM_EXCEEDED"
        assert error.message == "VRAM insuficiente durante generación"
    error = adapter.upstream_error(
        "generación", "Insufficient free CPU memory: /private token=secret"
    )
    assert (
        error.code == "INTERNAL" and error.message == "Fallo interno durante generación"
    )
