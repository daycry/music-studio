"""Contrato CPU del presupuesto nativo, sin pesos ni CUDA."""

import importlib
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_http_preflight_hook_is_optional():
    from engine_common import create_app

    assert "preflight" in inspect.signature(create_app).parameters, (
        "Estimate/jobs no disponen de preflight anterior a load/cola"
    )


def test_input_profile_is_native_and_fail_closed():
    adapter = importlib.import_module("adapter")
    assert hasattr(adapter, "preflight"), "Adaptador directo sin presupuesto nativo"


def test_native_count_includes_cfg_reserve_and_exact_limits():
    native = importlib.import_module("preflight")
    assert hasattr(native, "native_plan"), "Falta contar plantillas nativas completas"
    source = (
        Path(__file__).resolve().parents[4] / ".cache/dev-cycle/t17/upstream-acestep"
    )

    class Tokenizer:
        def __init__(self, count):
            self.count = count

        def __call__(self, text, **kwargs):
            assert kwargs == {"truncation": False}
            return {"input_ids": list(range(self.count))}

        def apply_chat_template(self, messages, **kwargs):
            return str(messages)

    request = {
        "task": "music.song",
        "params": {
            "style": "caption",
            "lyrics": "lyrics",
            "language": "es",
            "duration_s": 30,
        },
        "seed": 1,
        "n_outputs": 1,
    }
    result = native.native_plan(request, Tokenizer(3936), Tokenizer(256), source)
    assert result["kind"] == "planned"
    assert result["lm"]["reserve_tokens"] == 160
    assert result["lm"]["conditional"]["count"] == 3936
    assert result["lm"]["unconditional"]["count"] == 3936
    assert result["dit"]["text"]["count"] == 256
    from engine_common import EngineError

    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        native.native_plan(request, Tokenizer(3937), Tokenizer(256), source)
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        native.native_plan(request, Tokenizer(3936), Tokenizer(257), source)


@pytest.mark.parametrize(
    "params",
    [
        {"language": "invented"},
        {"language": "es", "vocal_language": "en"},
        {"duration_s": 481},
        {"key": " C minor "},
        {"time_signature": " 4/4 "},
        {"style": "# Instruction\nGenerate\n# Caption\nprivate\n# Metas\nx"},
    ],
)
def test_generation_rejects_silent_transformations(params):
    from engine_common import EngineError

    adapter = importlib.import_module("adapter")
    request = {
        "task": "music.song",
        "params": {
            "style": "synthetic",
            "lyrics": "synthetic",
            "language": "es",
            "duration_s": 30,
            **params,
        },
        "seed": 1,
        "n_outputs": 1,
    }
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        adapter.generation_options(request, 0)


def test_language_metadata_is_injected_at_real_lm_boundary():
    adapter = importlib.import_module("adapter")
    assert hasattr(adapter, "input_capture"), "Sin captura de frontera e idioma LM"
    seen = []
    from types import SimpleNamespace

    runtime = SimpleNamespace(
        lm=SimpleNamespace(
            generate_with_stop_condition=lambda **kwargs: (
                seen.append(kwargs) or "result"
            )
        ),
        dit=None,
    )
    planned = {"kind": "planned", "effective": {"params": {"vocal_language": "es"}}}
    with adapter.input_capture(
        runtime, planned, {"vocal_language": "es"}, 0
    ) as captured:
        runtime.lm.generate_with_stop_condition(
            caption="private", lyrics="private", user_metadata={"bpm": 94}
        )
    assert seen[0]["user_metadata"] == {"bpm": 94, "language": "es"}
    assert captured["kind"] == "captured"
    assert captured["boundaries"][0]["stage"] == "lm_arguments"
    assert "private" not in str(captured)


def test_direct_generate_preflight_precedes_runtime(tmp_path, monkeypatch):
    from engine_common import CancelToken, EngineError

    adapter = importlib.import_module("adapter")
    calls = []

    def reject(*args, **kwargs):
        calls.append("preflight")
        raise EngineError("INVALID_PARAMS", "Budget exceeded")

    monkeypatch.setattr(adapter, "preflight", reject)
    model = adapter.AceStepAdapter()
    model.runtime = object()
    request = {
        "task": "music.song",
        "params": {
            "style": "synthetic",
            "lyrics": "synthetic",
            "language": "es",
            "duration_s": 30,
        },
        "seed": 1,
        "n_outputs": 1,
    }
    with pytest.raises(EngineError, match="INVALID_PARAMS"):
        model.generate(request, tmp_path, calls.append, CancelToken())
    assert calls == ["preflight"]


def test_preflight_rejects_malformed_worker_output(monkeypatch):
    from types import SimpleNamespace

    from engine_common import EngineError

    native = importlib.import_module("preflight")
    monkeypatch.setattr(
        native.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout='{"kind":"planned"}', stderr="private lyrics"
        ),
    )
    with pytest.raises(EngineError, match="INTERNAL"):
        native.preflight({"seed": 1})


@pytest.mark.parametrize(
    "mode,code",
    [
        ("timeout", "TIMEOUT"),
        ("hash", "WEIGHTS_MISMATCH"),
        ("other", "INTERNAL"),
        ("list", "INTERNAL"),
    ],
)
def test_worker_failures_are_typed_and_private(monkeypatch, mode, code):
    from types import SimpleNamespace

    from engine_common import EngineError

    native = importlib.import_module("preflight")

    def run(*args, **kwargs):
        assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == ""
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        if mode == "timeout":
            raise native.subprocess.TimeoutExpired(
                "private", 1, stderr="private lyrics"
            )
        return SimpleNamespace(
            returncode=0 if mode == "list" else 1,
            stdout="[]"
            if mode == "list"
            else '{"error":"'
            + ("WEIGHTS_MISMATCH" if mode == "hash" else "private")
            + '"}',
            stderr="private lyrics",
        )

    monkeypatch.setattr(native.subprocess, "run", run)
    with pytest.raises(EngineError, match=code) as error:
        native.preflight({"seed": 1})
    assert "private" not in error.value.message


def test_public_upstream_output_is_silent(capsys):
    adapter = importlib.import_module("adapter")
    assert hasattr(adapter, "private_upstream_output")
    with adapter.private_upstream_output():
        print("private caption")
        print("private lyrics", file=sys.stderr)
    assert capsys.readouterr() == ("", "")


def test_long_caption_is_not_rejected_by_administrative_limit():
    from jsonschema import validate

    descriptor = importlib.import_module("descriptor").descriptor()
    validate(
        {
            "style": "calm " * 110,
            "lyrics": "synthetic",
            "duration_s": 30,
            "language": "es",
        },
        descriptor.tasks["music.song"].params_schema,
    )


@pytest.mark.parametrize("count,accepted", [(2048, True), (2049, False)])
def test_dit_lyrics_exact_boundary(count, accepted):
    native = importlib.import_module("preflight")
    from engine_common import EngineError

    lm = {"conditional": {"count": 100}, "unconditional": {"count": 10}}
    dit = {"text": {"count": 256}, "lyrics": {"count": count}}
    if accepted:
        native.enforce_budget(lm, dit, 160)
    else:
        with pytest.raises(EngineError, match="INVALID_PARAMS"):
            native.enforce_budget(lm, dit, 160)


def test_verified_tokenizers_are_local_and_fail_closed(tmp_path, monkeypatch):
    import hashlib
    from types import SimpleNamespace

    from engine_common import EngineError

    native = importlib.import_module("preflight")
    descriptor = importlib.import_module("descriptor")
    components = []
    for name in ("lm", "Qwen3-Embedding-0.6B"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "tokenizer.json").write_bytes(b"safe fixture")
        components.append(
            {
                "id": name,
                "dest_subdir": name,
                "files": [
                    {
                        "path": "tokenizer.json",
                        "sha256": hashlib.sha256(b"safe fixture").hexdigest(),
                    }
                ],
            }
        )
    monkeypatch.setattr(
        descriptor, "locked_model", lambda *a: {"components": components}
    )
    calls = []

    def load(path, **kwargs):
        calls.append(kwargs)
        return path

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=load)),
    )
    tokenizers, hashes = native.verified_tokenizers(tmp_path, "lm")
    assert len(tokenizers) == len(hashes) == 2
    assert calls == [{"local_files_only": True, "trust_remote_code": False}] * 2
    (tmp_path / "lm/extra.json").write_bytes(b"unlocked")
    with pytest.raises(EngineError, match="WEIGHTS_MISMATCH"):
        native.verified_tokenizers(tmp_path, "lm")
    (tmp_path / "lm/extra.json").unlink()
    (tmp_path / "lm/tokenizer.json").write_bytes(b"tampered")
    with pytest.raises(EngineError, match="WEIGHTS_MISMATCH"):
        native.verified_tokenizers(tmp_path, "lm")


def test_worker_success_checks_receipt_and_policy(monkeypatch):
    import json
    from types import SimpleNamespace

    native = importlib.import_module("preflight")
    request = {"seed": 1}
    result = {
        "receipt_version": 1,
        "kind": "planned",
        "checkpoint": {"id": "acestep-v15-turbo"},
        "profile_sha256": native.digest(native.SOURCE_HASHES),
        "request_sha256": native.digest(request),
        "effective": {},
        "effective_sha256": native.digest({}),
        "tokenizer_hashes": [{"sha256": "a" * 64}],
        "lm": {
            "conditional": {"count": 3936},
            "unconditional": {"count": 30},
            "reserve_tokens": 160,
        },
        "dit": {"text": {"count": 256}, "lyrics": {"count": 2048}},
    }
    monkeypatch.setattr(
        native.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(result)),
    )
    assert native.preflight(request) == result
    monkeypatch.setattr(
        native, "verified_tokenizers", lambda *a: (["lm", "dit"], [{"hash": "fixture"}])
    )
    monkeypatch.setattr(
        native,
        "verified_checkpoint_profile",
        lambda *a: {"id": "fixture", "config_sha256": "a" * 64},
    )
    monkeypatch.setattr(native, "native_plan", lambda *a: {"kind": "planned"})
    assert native.worker(request, Path("fixture"), "lm")["tokenizer_hashes"] == [
        {"hash": "fixture"}
    ]


def test_checkpoint_config_failure_blocks_before_tokenizer(tmp_path, monkeypatch):
    from engine_common import EngineError

    native = importlib.import_module("preflight")
    descriptor = importlib.import_module("descriptor")
    monkeypatch.setattr(
        descriptor,
        "locked_model",
        lambda *a: {
            "components": [
                {
                    "id": "acestep-v15-turbo",
                    "dest_subdir": "acestep-v15-turbo",
                    "files": [{"path": "config.json", "sha256": "a" * 64}],
                }
            ]
        },
    )
    monkeypatch.setattr(native, "verified_tokenizers", lambda *a: (["lm", "dit"], []))
    monkeypatch.setattr(native, "native_plan", lambda *a: {"kind": "planned"})
    with pytest.raises(EngineError, match="WEIGHTS_MISMATCH"):
        native.worker({}, tmp_path, "lm")


@pytest.mark.parametrize("lego", [False, True])
def test_checkpoint_profile_preserves_full_song_and_rejects_stems(
    tmp_path, monkeypatch, lego
):
    import hashlib
    import json

    from engine_common import EngineError

    native = importlib.import_module("preflight")
    descriptor = importlib.import_module("descriptor")
    payload = json.dumps({"is_lego_sft": lego}).encode()
    folder = tmp_path / "checkpoint"
    folder.mkdir()
    (folder / "config.json").write_bytes(payload)
    value = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(
        descriptor,
        "locked_model",
        lambda *a: {
            "components": [
                {
                    "id": "checkpoint",
                    "dest_subdir": "checkpoint",
                    "files": [{"path": "config.json", "sha256": value}],
                }
            ]
        },
    )
    if lego:
        with pytest.raises(EngineError, match="INVALID_PARAMS"):
            native.verified_checkpoint_profile(tmp_path, "checkpoint")
    else:
        assert native.verified_checkpoint_profile(tmp_path, "checkpoint") == {
            "id": "checkpoint",
            "config_sha256": value,
            "is_lego_sft": False,
        }


def _capture_fixture():
    from types import SimpleNamespace

    import numpy as np

    adapter = importlib.import_module("adapter")
    native = importlib.import_module("preflight")
    source = (
        Path(__file__).resolve().parents[4] / ".cache/dev-cycle/t17/upstream-acestep"
    )

    class Tokenizer:
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

        def apply_chat_template(self, messages, **kwargs):
            return str(messages)

    tokenizer = Tokenizer()
    request = {
        "task": "music.song",
        "params": {
            "style": "synthetic",
            "lyrics": "synthetic",
            "duration_s": 30,
            "language": "es",
            "bpm": 94,
            "key": "C minor",
            "time_signature": "4/4",
        },
        "seed": 1,
        "n_outputs": 1,
    }
    planned = native.native_plan(request, tokenizer, tokenizer, source)
    values, _ = adapter.generation_options(request, 0)
    lm, _ = native.native_templates(source)
    lm.llm_tokenizer = tokenizer
    lm.generate_from_formatted_prompt = lambda **kwargs: "backend_reached"
    lm._build_unconditional_prompt = lambda **kwargs: (
        lm.build_formatted_prompt_with_cot(
            kwargs["caption"],
            kwargs["lyrics"],
            kwargs["cot_text"],
            is_negative_prompt=True,
            negative_prompt=kwargs["negative_prompt"],
        )
    )

    def generate_lm(**kwargs):
        cot = lm._format_metadata_as_cot(kwargs["user_metadata"])
        formatted = lm.build_formatted_prompt_with_cot(
            values["caption"], values["lyrics"], cot
        )
        return lm.generate_from_formatted_prompt(
            formatted_prompt=formatted,
            cfg={
                "caption": values["caption"],
                "lyrics": values["lyrics"],
                "cot_text": cot,
                "negative_prompt": values["lm_negative_prompt"],
                "target_duration": values["duration"],
                "generation_phase": "codes",
            },
        )

    lm.generate_with_stop_condition = generate_lm
    dit = SimpleNamespace()
    mask = [SimpleNamespace(bool=lambda: np.ones(10, dtype=bool))]
    dit._prepare_text_conditioning_inputs = lambda: (
        None,
        np.array([list(range(10))]),
        mask,
        np.array([list(range(10))]),
        mask,
    )
    dit.generate_music = lambda **kwargs: dit._prepare_text_conditioning_inputs()
    dit_kwargs = {
        "captions": values["caption"],
        "lyrics": values["lyrics"],
        "vocal_language": "es",
        "audio_duration": 30,
        "bpm": 94,
        "key_scale": "C minor",
        "time_signature": "4/4",
    }
    lm_kwargs = {
        "caption": "synthetic",
        "lyrics": "synthetic",
        "user_metadata": {
            "bpm": 94,
            "duration": 30,
            "keyscale": "C minor",
            "timesignature": "4/4",
        },
    }
    return (
        adapter,
        native,
        SimpleNamespace(lm=lm, dit=dit),
        planned,
        values,
        lm_kwargs,
        dit_kwargs,
    )


def test_capture_reaches_four_real_callback_boundaries_and_restores_methods():
    adapter, _, runtime, planned, values, lm_kwargs, dit_kwargs = _capture_fixture()
    original = runtime.lm.generate_with_stop_condition
    with adapter.input_capture(runtime, planned, values, 0) as captured:
        assert runtime.lm.generate_with_stop_condition(**lm_kwargs) == "backend_reached"
        runtime.dit.generate_music(**dit_kwargs)
    assert [b["stage"] for b in captured["boundaries"]] == [
        "lm_arguments",
        "lm_formatted_prompt",
        "dit_arguments",
        "dit_tokens",
    ]
    assert runtime.lm.generate_with_stop_condition is original
    assert (
        captured["boundaries"][3]["text"]["tokens_sha256"]
        == planned["dit"]["text"]["tokens_sha256"]
    )


@pytest.mark.parametrize(
    "mutation", ["lm_prompt", "reserve", "dit_arguments", "dit_tokens"]
)
def test_capture_rejects_post_preflight_mutation(mutation):
    from engine_common import EngineError

    adapter, _, runtime, planned, values, lm_kwargs, dit_kwargs = _capture_fixture()
    if mutation == "lm_prompt":
        planned["lm"]["conditional"]["input_sha256"] = "0" * 64
    elif mutation == "reserve":
        planned["lm"]["reserve_tokens"] += 1
    elif mutation == "dit_arguments":
        dit_kwargs["lyrics"] = "changed"
    else:
        planned["dit"]["text"]["tokens_sha256"] = "0" * 64
    with (
        adapter.input_capture(runtime, planned, values, 0),
        pytest.raises(EngineError, match="INVALID_PARAMS"),
    ):
        if mutation.startswith("lm") or mutation == "reserve":
            runtime.lm.generate_with_stop_condition(**lm_kwargs)
        else:
            runtime.dit.generate_music(**dit_kwargs)
