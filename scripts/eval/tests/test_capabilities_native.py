import importlib
import importlib.util
import inspect

import pytest


@pytest.mark.parametrize("exceptional_exit", [False, True])
def test_capture_preserves_signature_filtered_captions_and_restores(
    tmp_path, monkeypatch, exceptional_exit
):
    import sys
    import types

    from scripts.eval.capabilities_native import capture_boundaries

    fake = types.ModuleType("acestep.core.generation.handler.generate_music")

    def splice(pred_wavs, src_wavs, crossfade_duration=0.0):
        return pred_wavs

    fake.apply_repaint_waveform_splice = splice
    monkeypatch.setitem(sys.modules, fake.__name__, fake)

    class DIT:
        def generate_music(self, captions: str, lyrics: str = "", seed: int = -1):
            """Generador con parámetros explícitos, como la interfaz instalada."""
            return {"captions": captions, "lyrics": lyrics, "seed": seed}

        def _decode_generate_music_pred_latents(self, latents):
            return None

        def process_src_audio(self, src_audio):
            return None

        def process_reference_audio(self, reference_audio):
            return None

    class LM:
        def generate_with_stop_condition(self, caption, user_metadata=None):
            return caption

        def generate_from_formatted_prompt(self, formatted_prompt, cfg):
            return formatted_prompt

    runtime = types.SimpleNamespace(dit=DIT(), lm=LM())
    targets = [
        (runtime.dit, "generate_music"),
        (runtime.dit, "_decode_generate_music_pred_latents"),
        (runtime.dit, "process_src_audio"),
        (runtime.dit, "process_reference_audio"),
        (runtime.lm, "generate_with_stop_condition"),
        (runtime.lm, "generate_from_formatted_prompt"),
        (fake, "apply_repaint_waveform_splice"),
    ]
    originals = [getattr(obj, name) for obj, name in targets]
    dit_generate_kwargs = {
        "captions": "own caption",
        "lyrics": "[Verse]\nown lyrics",
        "seed": 101,
        "unsupported": "discard me",
    }
    receipt = None
    try:
        with capture_boundaries(runtime, tmp_path, {}, 501) as receipt:
            # Filtro de generate_music instalado, fijado por revisión upstream:
            # conserva únicamente los nombres declarados en la firma del DiT.
            supported_generate_keys = set(
                inspect.signature(runtime.dit.generate_music).parameters.keys()
            )
            filtered_generate_kwargs = {
                key: value
                for key, value in dit_generate_kwargs.items()
                if key in supported_generate_keys
            }
            result = runtime.dit.generate_music(**filtered_generate_kwargs)
            assert result == {
                "captions": "own caption",
                "lyrics": "[Verse]\nown lyrics",
                "seed": 101,
            }
            assert receipt["boundaries"][0]["arguments"] == result
            for (obj, name), original in zip(targets, originals, strict=True):
                wrapped = getattr(obj, name)
                assert inspect.signature(wrapped) == inspect.signature(original)
                assert wrapped.__name__ == original.__name__
                assert wrapped.__doc__ == original.__doc__
                assert wrapped.__annotations__ == original.__annotations__
                assert wrapped.__wrapped__ == original
            if exceptional_exit:
                raise RuntimeError("private capture failure")
    except RuntimeError as exc:
        assert exceptional_exit and str(exc) == "private capture failure"
    finally:
        for (obj, name), original in zip(targets, originals, strict=True):
            assert getattr(obj, name) == original
            assert inspect.signature(getattr(obj, name)) == inspect.signature(original)


def module():
    name = "scripts.eval.capabilities_native"
    if importlib.util.find_spec(name) is None:
        return type(
            "Missing",
            (),
            {
                "native_values": staticmethod(
                    lambda row, request, fixture: {"task_type": "text2music"}
                ),
                "validate_lora": staticmethod(lambda *a: {}),
            },
        )()
    return importlib.import_module(name)


def test_retake_is_cover_with_source_overlay():
    result = module().native_values(
        {
            "case": "music.retake",
            "control": {"retake_seed": 201, "retake_variance": 0.2},
        },
        {"params": {"style": "own", "lyrics": "own", "duration_s": 60}, "seed": 101},
        {"source": "own.wav"},
    )
    assert result["task_type"] == "cover"
    assert result["src_audio"] == "own.wav"
    assert result["retake_seed"] == 201


def test_lora_absence_is_prerequisite_not_mock_success(tmp_path):
    with pytest.raises(ValueError, match="lora_prerequisite"):
        module().validate_lora({}, tmp_path)


def test_native_boundary_records_formatted_lm_and_language(tmp_path, monkeypatch):
    import sys
    import types

    from scripts.eval.capabilities_native import capture_boundaries

    module_name = "acestep.core.generation.handler.generate_music"
    fake = types.ModuleType(module_name)
    fake.apply_repaint_waveform_splice = lambda **k: k["pred_wavs"]
    monkeypatch.setitem(sys.modules, module_name, fake)

    class LM:
        def generate_with_stop_condition(self, **kwargs):
            return kwargs

        def generate_from_formatted_prompt(self, formatted_prompt, cfg, **kwargs):
            return formatted_prompt

    class DIT:
        def _decode_generate_music_pred_latents(self, **kwargs):
            return None

        def process_src_audio(self, *a):
            return None

        def process_reference_audio(self, *a):
            return None

        def generate_music(self, **kwargs):
            return kwargs

    runtime = types.SimpleNamespace(lm=LM(), dit=DIT())
    with capture_boundaries(runtime, tmp_path, {}, 501) as receipt:
        result = runtime.lm.generate_with_stop_condition(
            caption="own", lyrics="[Verse]\nown", user_metadata={}
        )
        runtime.lm.generate_from_formatted_prompt(
            "# Instruction\n# Caption own", {"caption": "own", "lyrics": "[Verse]\nown"}
        )
        runtime.dit.generate_music(captions="own", lyrics="[Verse]\nown")
    assert result["user_metadata"]["language"] == "es"
    assert receipt["boundaries"][1]["prompt"] == "# Instruction\n# Caption own"
    assert receipt["boundaries"][2]["arguments"]["lyrics"] == "[Verse]\nown"


def test_unsealed_upstream_cannot_load(tmp_path, monkeypatch):
    import sys
    import types
    from pathlib import Path

    from scripts.eval.capabilities_native import NativeLabAdapter

    adapter = types.ModuleType("adapter")
    adapter.AceStepAdapter = lambda **k: types.SimpleNamespace(load=lambda *a: None)
    monkeypatch.setitem(sys.modules, "adapter", adapter)
    lab = NativeLabAdapter(
        "checkpoint",
        "lm",
        "models",
        tmp_path,
        {"seal.txt": {"sha256": "x", "bytes": 0}},
    )
    monkeypatch.setattr(
        module(), "file_record", lambda path: {"sha256": "x", "bytes": 0}
    )
    original = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: (
            True if str(self) in ("/.dockerenv", "\\.dockerenv") else original(self)
        ),
    )
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    with pytest.raises(ValueError, match="upstream_seal_required"):
        lab.load("checkpoint", "bf16", 9000, 12000)


def test_dit_tokenizer_rejects_truncation_before_generation(tmp_path, monkeypatch):
    import sys
    import types

    import numpy as np

    from scripts.eval.capabilities_native import capture_boundaries

    fake = types.ModuleType("acestep.core.generation.handler.generate_music")
    fake.apply_repaint_waveform_splice = lambda **k: k["pred_wavs"]
    monkeypatch.setitem(sys.modules, fake.__name__, fake)

    class Tokenizer:
        def __call__(self, text, **kwargs):
            return types.SimpleNamespace(input_ids=np.arange(300)[None, :])

    dit = types.SimpleNamespace(
        text_tokenizer=Tokenizer(),
        _decode_generate_music_pred_latents=lambda: None,
        process_src_audio=lambda: None,
        process_reference_audio=lambda: None,
        generate_music=lambda: None,
    )
    lm = types.SimpleNamespace(
        generate_with_stop_condition=lambda **k: k,
        generate_from_formatted_prompt=lambda *a, **k: None,
    )
    with (
        capture_boundaries(types.SimpleNamespace(dit=dit, lm=lm), tmp_path, {}, 501),
        pytest.raises(ValueError, match="native_dit_budget_exceeded"),
    ):
        dit.text_tokenizer(
            "# Instruction\n# Caption",
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )


def test_audio_requires_seal_rights_and_voice_consent(tmp_path):
    validator = getattr(module(), "validate_audio_resources", lambda *a: None)
    (tmp_path / "voice.wav").write_bytes(b"CPU test resource")
    with pytest.raises(ValueError, match="audio_rights_prerequisite"):
        validator({"source": "voice.wav"}, tmp_path)


def test_capture_keeps_callable_tokenizer_probe_and_delegation(tmp_path, monkeypatch):
    import sys
    import types

    import numpy as np

    from scripts.eval.capabilities_native import capture_boundaries

    fake = types.ModuleType("acestep.core.generation.handler.generate_music")
    fake.apply_repaint_waveform_splice = lambda **k: k["pred_wavs"]
    monkeypatch.setitem(sys.modules, fake.__name__, fake)

    class Tokenizer:
        model_max_length = 256

        def __init__(self):
            self.calls = []

        def __call__(self, text, **kwargs):
            self.calls.append((text, kwargs))
            return types.SimpleNamespace(input_ids=np.arange(3)[None, :])

    tokenizer = Tokenizer()
    dit = types.SimpleNamespace(
        text_tokenizer=tokenizer,
        _decode_generate_music_pred_latents=lambda: None,
        process_src_audio=lambda: None,
        process_reference_audio=lambda: None,
        generate_music=lambda: None,
    )
    lm = types.SimpleNamespace(
        generate_with_stop_condition=lambda **k: k,
        generate_from_formatted_prompt=lambda *a, **k: None,
    )
    with capture_boundaries(
        types.SimpleNamespace(dit=dit, lm=lm), tmp_path, {}, 501
    ) as receipt:
        assert dit.text_tokenizer.model_max_length == 256
        result = dit.text_tokenizer("own", truncation=True, max_length=256)
        assert result.input_ids.tolist() == [[0, 1, 2]]
        assert tokenizer.calls == [
            ("own", {"truncation": False, "max_length": 256}),
            ("own", {"truncation": True, "max_length": 256}),
        ]
        assert receipt["boundaries"][0]["tokens"] == [0, 1, 2]
    assert dit.text_tokenizer is tokenizer
