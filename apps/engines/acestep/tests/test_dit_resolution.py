"""Resolución nativa pura fijada; sin modelos ni inferencia."""

from pathlib import Path

import adapter
import preflight
import pytest

SOURCE = Path(__file__).resolve().parents[4] / ".cache/dev-cycle/t17/upstream-acestep"


def test_real_http_estimate_transports_both_candidates(tmp_path):
    from descriptor import descriptor
    from engine_common import CpuGpu, create_app
    from fastapi.testclient import TestClient

    class Count(Tokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

    def native(req):
        return preflight.native_plan(req, Count(), Count(), SOURCE)

    app = create_app(
        [descriptor()],
        "adapter:AceStepAdapter",
        token="secret",
        data_dir=tmp_path,
        gpu=CpuGpu(),
        preflight=native,
    )
    body = {
        **request(),
        "job_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "output_dir": "tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV/",
        "inputs": [],
        "timeout_s": 60,
    }
    with TestClient(app) as client:
        response = client.post(
            "/v1/estimate", json=body, headers={"X-Studio-Engine-Token": "secret"}
        )
        assert response.status_code == 200
        budget = response.json()["input_budget"]["dit"]
        assert budget["receipt_version"] == 2
        assert set(budget["candidates"]) == {"text2music", "cover"}


class Tokenizer:
    def __call__(self, text, **kwargs):
        assert kwargs == {"truncation": False}
        return {"input_ids": list(text.encode())}

    def apply_chat_template(self, messages, **kwargs):
        return str(messages)


def request(sft=False):
    return {
        "task": "music.song",
        "model_id": "ace-step-1.5-sft" if sft else "ace-step-1.5-turbo",
        "params": {
            "style": "synthetic",
            "lyrics": "synthetic",
            "duration_s": 30,
            "language": "es",
        },
        "seed": 1,
        "n_outputs": 1,
    }


@pytest.mark.parametrize("sft", [False, True])
def test_plan_accounts_for_both_native_resolutions(sft):
    # Count double only: instruction input hashes must still be distinct.
    class Count(Tokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

    plan = preflight.native_plan(request(sft), Count(), Count(), SOURCE)
    assert plan["receipt_version"] == 2
    assert set(plan["dit"]["candidates"]) == {"text2music", "cover"}
    assert (
        plan["dit"]["candidates"]["text2music"]["instruction_sha256"]
        != plan["dit"]["candidates"]["cover"]["instruction_sha256"]
    )


@pytest.mark.parametrize(
    "codes", ["", "  ", [], ["", "  "], "synthetic", ["", "synthetic"]]
)
@pytest.mark.parametrize("sft", [False, True])
def test_capture_binds_native_resolution_and_instructions(codes, sft):
    from types import SimpleNamespace

    import numpy as np

    class Count(Tokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

    plan = preflight.native_plan(request(sft), Count(), Count(), SOURCE)
    _, dit = preflight.native_templates(SOURCE)
    mask = [SimpleNamespace(bool=lambda: np.ones(10, dtype=bool))]
    dit._prepare_text_conditioning_inputs = lambda *a, **k: (
        None,
        np.array([list(range(10))]),
        mask,
        np.array([list(range(10))]),
        mask,
    )
    runtime = SimpleNamespace(lm=None, dit=dit)
    values, _ = adapter.generation_options(request(sft), 0)
    with adapter.input_capture(runtime, plan, values, 0) as captured:
        task, instruction = dit._resolve_generate_music_task(
            "text2music", codes, dit.default_instruction
        )
        dit._prepare_text_conditioning_inputs(1, [instruction])
    resolution = next(
        b for b in captured["boundaries"] if b["stage"] == "dit_resolution"
    )
    assert resolution["resolved_task"] == task
    assert type(resolution["has_audio_codes"]) is bool
    assert resolution["instruction_sha256"] == preflight.digest(instruction)
    assert captured["receipt_version"] == 2


@pytest.mark.parametrize("keyword", [False, True])
def test_instruction_mutation_is_rejected_even_with_identical_token_ids(keyword):
    from types import SimpleNamespace

    import numpy as np
    from engine_common import EngineError

    class Count(Tokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

    plan = preflight.native_plan(request(), Count(), Count(), SOURCE)
    _, dit = preflight.native_templates(SOURCE)
    mask = [SimpleNamespace(bool=lambda: np.ones(10, dtype=bool))]
    dit._prepare_text_conditioning_inputs = lambda *a, **k: (
        None,
        np.array([list(range(10))]),
        mask,
        np.array([list(range(10))]),
        mask,
    )
    with adapter.input_capture(SimpleNamespace(lm=None, dit=dit), plan, {}, 0):
        dit._resolve_generate_music_task(
            "text2music", "synthetic", dit.default_instruction
        )
        with pytest.raises(EngineError, match="INVALID_PARAMS"):
            if keyword:
                dit._prepare_text_conditioning_inputs(instructions=["altered"])
            else:
                dit._prepare_text_conditioning_inputs(1, ["altered"])


def test_resolver_rejects_unknown_initial_instruction():
    from types import SimpleNamespace

    from engine_common import EngineError

    class Count(Tokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

    plan = preflight.native_plan(request(), Count(), Count(), SOURCE)
    _, dit = preflight.native_templates(SOURCE)
    with (
        adapter.input_capture(SimpleNamespace(lm=None, dit=dit), plan, {}, 0),
        pytest.raises(EngineError, match="INVALID_PARAMS"),
    ):
        dit._resolve_generate_music_task(
            task_type="text2music",
            audio_code_string="synthetic",
            instruction="unknown",
        )


@pytest.mark.parametrize("branch", ["text2music", "cover"])
@pytest.mark.parametrize("field,limit", [("text", 256), ("lyrics", 2048)])
@pytest.mark.parametrize("extra", [0, 1])
def test_both_native_candidates_enforce_exact_budget(branch, field, limit, extra):
    from engine_common import EngineError

    class Count(Tokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

    baseline = preflight.native_plan(request(), Count(), Count(), SOURCE)
    target = baseline["dit"]["candidates"][branch][field]["input_sha256"]

    class Budget(Count):
        def __call__(self, text, **kwargs):
            count = limit + extra if preflight.digest(text) == target else 10
            return {"input_ids": list(range(count))}

    if extra:
        with pytest.raises(EngineError, match="INVALID_PARAMS"):
            preflight.native_plan(request(), Count(), Budget(), SOURCE)
    else:
        result = preflight.native_plan(request(), Count(), Budget(), SOURCE)
        assert result["dit"]["candidates"][branch][field]["count"] == limit
