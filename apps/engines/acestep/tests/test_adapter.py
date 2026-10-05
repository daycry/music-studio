"""Pruebas CPU del borde real del adapter; no acreditan generación GPU."""

import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_pretrained_always_safe_and_local(monkeypatch):
    import sys

    patches = module("patches")
    calls = []

    class Loader:
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            calls.append(kwargs)

    # No finge la API upstream: prueba el filtro de kwargs de bibliotecas reales.
    class Causal(Loader):
        pass

    class Vae(Loader):
        pass

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoModel=Loader, AutoModelForCausalLM=Causal),
    )
    monkeypatch.setitem(
        sys.modules, "diffusers.models", SimpleNamespace(AutoencoderOobleck=Vae)
    )
    patches.enforce_safe_pretrained()
    for cls in (Loader, Causal, Vae):
        cls.from_pretrained("local", use_safetensors=False, local_files_only=False)
    assert all(
        call == {"use_safetensors": True, "local_files_only": True} for call in calls
    )


def test_pretrained_loads_bf16_before_cuda_transfer(monkeypatch):
    import inspect
    import sys

    patches = module("patches")
    assert "dtype" in inspect.signature(patches.enforce_safe_pretrained).parameters, (
        "Falta forzar BF16 al deserializar, antes de transferir a CUDA"
    )
    calls = []

    def make_loader(name):
        return type(
            name,
            (),
            {
                "from_pretrained": staticmethod(
                    lambda *args, **kwargs: calls.append((name, kwargs))
                )
            },
        )

    auto, causal, vae = [make_loader(name) for name in ("auto", "causal", "vae")]
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoModel=auto, AutoModelForCausalLM=causal),
    )
    monkeypatch.setitem(
        sys.modules, "diffusers.models", SimpleNamespace(AutoencoderOobleck=vae)
    )
    patches.enforce_safe_pretrained("bf16")
    for cls in (auto, causal, vae):
        cls.from_pretrained("local", dtype="fp32", torch_dtype="fp32")
    assert calls == [
        ("auto", {"dtype": "bf16", "use_safetensors": True, "local_files_only": True}),
        (
            "causal",
            {"dtype": "bf16", "use_safetensors": True, "local_files_only": True},
        ),
        (
            "vae",
            {"torch_dtype": "bf16", "use_safetensors": True, "local_files_only": True},
        ),
    ]


def test_prepare_unknown_checkpoint_fails_before_import(monkeypatch, tmp_path):
    adapter = module("adapter")
    monkeypatch.setattr(adapter, "locked_model", lambda *args: {"components": []})
    with pytest.raises(Exception, match="MODEL_NOT_FOUND"):
        adapter.prepare_runtime(tmp_path, "unknown", "lm")


@pytest.mark.skipif(
    os.getenv("STUDIO_ENGINE_CONTAINER") != "1",
    reason="La fuente auditada está en la imagen fijada",
)
def test_install_patch_on_actual_upstream_without_models():
    import dis

    patches = module("patches")
    patches.install_safe_loader()
    from acestep.core.generation.handler.init_service_loader import (
        InitServiceLoaderMixin,
    )

    instructions = list(
        dis.get_instructions(InitServiceLoaderMixin._load_main_model_from_checkpoint)
    )
    assert any(i.argval == "safe_load_file" for i in instructions)
    assert not any(i.opname == "LOAD_ATTR" and i.argval == "load" for i in instructions)


def test_converted_file_is_verified_instead_of_pickle(tmp_path):
    patches = module("patches")
    root = tmp_path / "dit"
    root.mkdir()
    blob = b"safe tensor fixture"
    (root / "silence_latent.safetensors").write_bytes(blob)
    component = {
        "id": "dit",
        "dest_subdir": "dit",
        "files": [
            {
                "path": "silence_latent.pt",
                "format": "pickle",
                "converted": {
                    "dest": "silence_latent.safetensors",
                    "bytes": len(blob),
                    "sha256": hashlib.sha256(blob).hexdigest(),
                },
            }
        ],
    }
    patches.verify_components(tmp_path, [component])
    (root / "silence_latent.safetensors").write_bytes(b"a" * len(blob))
    with pytest.raises(Exception, match="WEIGHTS_MISMATCH"):
        patches.verify_components(tmp_path, [component])


def test_handler_disables_download_autosync_and_estimates():
    adapter = module("adapter")
    assert hasattr(adapter, "configure_handler"), (
        "Falta desactivar progreso estimado y persistencia upstream"
    )
    handler = SimpleNamespace()
    adapter.configure_handler(handler)
    assert handler._ensure_models_present(config_path="missing") is None
    assert handler._sync_model_code_if_needed("model", Path("/models")) is None
    assert handler._start_diffusion_progress_estimator(progress=lambda: None) == (
        None,
        None,
    )
    assert handler._save_progress_estimates() is None


def test_decoder_step_hooks_are_real_and_removed():
    from engine_common.runtime import CancelToken, EngineError

    adapter = module("adapter")
    assert hasattr(adapter, "step_hooks"), "Falta cancelación y progreso por paso real"

    class Layer:
        def __init__(self):
            self.pre, self.post = [], []

        def register_forward_pre_hook(self, callback):
            self.pre.append(callback)
            return SimpleNamespace(remove=lambda: self.pre.remove(callback))

        def register_forward_hook(self, callback):
            self.post.append(callback)
            return SimpleNamespace(remove=lambda: self.post.remove(callback))

        def step(self):
            for hook in self.pre:
                hook(self, ())
            for hook in self.post:
                hook(self, (), None)

    layer, lm = Layer(), Layer()
    runtime = SimpleNamespace(
        dit=SimpleNamespace(model=SimpleNamespace(decoder=layer)),
        lm=SimpleNamespace(llm=lm),
    )
    token, events = CancelToken(), []
    with adapter.step_hooks(
        runtime, token, lambda value, **kwargs: events.append(value), 8
    ):
        layer.step()
        assert events == [pytest.approx(0.52 + 0.27 / 8)]
        token.cancel()
        with pytest.raises(EngineError, match="CANCELLED"):
            lm.step()
    assert layer.pre == layer.post == lm.pre == []


def test_verified_components_fail_closed(tmp_path):
    patches = module("patches")
    assert hasattr(patches, "verify_components"), (
        "Falta verificación de pesos antes de runtime"
    )
    blob = b"safe fixture"
    component = {
        "id": "dit",
        "dest_subdir": "dit",
        "files": [
            {
                "path": "model.safetensors",
                "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
                "format": "safetensors",
            }
        ],
    }
    (tmp_path / "dit").mkdir()
    target = tmp_path / "dit/model.safetensors"
    target.write_bytes(blob)
    patches.verify_components(tmp_path, [component])
    target.write_bytes(b"corrupted")
    with pytest.raises(Exception, match="WEIGHTS_MISMATCH"):
        patches.verify_components(tmp_path, [component])


def test_weights_missing_extra_pickle_and_escape(tmp_path):
    patches = module("patches")
    (tmp_path / "dit").mkdir()
    component = {"id": "dit", "dest_subdir": "dit", "files": []}
    (tmp_path / "dit/rogue.bin").write_bytes(b"pickle")
    with pytest.raises(Exception, match="WEIGHTS_MISMATCH"):
        patches.verify_components(tmp_path, [component])
    for entry in (
        {
            "path": "missing.safetensors",
            "bytes": 1,
            "sha256": "a" * 64,
            "format": "safetensors",
        },
        {"path": "unsafe.pt", "bytes": 1, "sha256": "a" * 64, "format": "pickle"},
        {"path": "../../outside", "bytes": 1, "sha256": "a" * 64, "format": "metadata"},
    ):
        component["files"] = [entry]
        with pytest.raises(Exception, match="WEIGHTS_MISMATCH"):
            patches.verify_components(tmp_path, [component])


def test_patch_changed_loader_is_rejected():
    patches = module("patches")
    with pytest.raises(ValueError, match="ha cambiado"):
        patches.patch_loader_source("new upstream implementation")
    source = '"silence_latent.pt"\ntorch.load(silence_latent_path, weights_only=True)\ntorch.load(other)'
    with pytest.raises(ValueError, match="adicional"):
        patches.patch_loader_source(source)


@pytest.mark.parametrize(
    "shape,rate,value",
    [
        ((1, 8), 48000, 0.1),
        ((2, 8), 44100, 0.1),
        ((2, 0), 48000, 0.1),
        ((2, 8), 48000, float("nan")),
    ],
)
def test_wav_rejects_incompatible_audio(tmp_path, shape, rate, value):
    import numpy as np

    adapter = module("adapter")
    with pytest.raises(Exception, match="INTERNAL"):
        adapter.write_wav(tmp_path / "bad.wav", np.full(shape, value), rate)
    assert not (tmp_path / "bad.wav").exists()


def test_load_rejects_invalid_mode_model_and_budget():
    adapter = module("adapter")
    model = adapter.AceStepAdapter()
    for model_id, mode, cap, total, code in [
        ("missing", "bf16", 1, 2, "MODEL_NOT_FOUND"),
        ("ace-step-1.5-turbo", "int8", 1, 2, "INVALID_PARAMS"),
        ("ace-step-1.5-turbo", "bf16", 0, 2, "VRAM_EXCEEDED"),
        ("ace-step-1.5-turbo", "bf16", 3, 2, "VRAM_EXCEEDED"),
    ]:
        with pytest.raises(Exception, match=code):
            model.load(model_id, mode, cap, total)


@pytest.mark.parametrize("failure", ["cuda", "bf16", "dit", "dtype", "device", "lm"])
def test_failed_runtime_load_is_not_published(monkeypatch, failure):
    adapter = module("adapter")
    cuda = SimpleNamespace(
        is_available=lambda: failure != "cuda",
        is_bf16_supported=lambda: failure != "bf16",
        set_per_process_memory_fraction=lambda f: None,
        reset_peak_memory_stats=lambda: None,
    )
    runtime = SimpleNamespace(
        torch=SimpleNamespace(cuda=cuda, bfloat16="bf16"),
        dit=SimpleNamespace(
            dtype="fp32" if failure == "dtype" else "bf16",
            device="cpu" if failure == "device" else "cuda",
            initialize_service=lambda **kw: ("status", failure != "dit"),
        ),
        lm=SimpleNamespace(initialize=lambda **kw: ("status", failure != "lm")),
    )
    monkeypatch.setattr(adapter, "prepare_runtime", lambda *args: runtime)
    model = adapter.AceStepAdapter()
    with pytest.raises(Exception, match="INTERNAL"):
        model.load("ace-step-1.5-turbo", "offload", 100, 200)
    assert model.runtime is None


def test_instrumental_language_and_random_seed():
    adapter = module("adapter")
    params, config = adapter.generation_options(
        {"task": "music.instrumental", "params": {"style": "jazz", "duration_s": 30}}, 0
    )
    assert params["lyrics"] == "[Instrumental]" and params["instrumental"]
    assert params["vocal_language"] == "unknown" and config["seeds"] == [params["seed"]]


def test_upstream_error_and_swallowed_cancel(tmp_path, monkeypatch):
    from engine_common.runtime import CancelToken, EngineError

    adapter = module("adapter")
    monkeypatch.setattr(adapter, "preflight", lambda *a, **k: {"kind": "planned"})
    model = adapter.AceStepAdapter()
    token = CancelToken()
    request = {
        "task": "music.instrumental",
        "params": {"style": "jazz", "duration_s": 30},
        "n_outputs": 1,
    }
    with pytest.raises(Exception, match="INTERNAL"):
        model.generate(request, tmp_path, lambda event: None, token)

    def swallowed(*args, **kwargs):
        token.cancel()
        try:
            kwargs["progress"](0.5)
        except EngineError as error:
            return SimpleNamespace(success=False, audios=[], error=error.code)
        raise AssertionError("La cancelación debe llegar al callback")

    model.runtime = SimpleNamespace(
        dit=None,
        lm=None,
        GenerationParams=lambda **kw: kw,
        GenerationConfig=lambda **kw: kw,
        generate_music=swallowed,
    )
    with pytest.raises(Exception, match="CANCELLED"):
        model.generate(request, tmp_path, lambda event: None, token)
    token = CancelToken()
    model.runtime.generate_music = lambda *args, **kw: SimpleNamespace(
        success=False, audios=[]
    )
    with pytest.raises(Exception, match="INTERNAL"):
        model.generate(request, tmp_path, lambda event: None, token)


def test_runtime_load_forces_pt_bf16_and_budget(monkeypatch):
    adapter = module("adapter")
    assert hasattr(adapter, "AceStepAdapter"), "Falta carga real del adapter en hijo"
    calls = []
    dit = SimpleNamespace(
        dtype="bf16",
        device="cuda",
        initialize_service=lambda **kwargs: (
            calls.append(("dit", kwargs)) or ("ok", True)
        ),
    )
    lm = SimpleNamespace(
        initialize=lambda **kwargs: calls.append(("lm", kwargs)) or ("ok", True)
    )
    cuda = SimpleNamespace(
        is_available=lambda: True,
        is_bf16_supported=lambda: True,
        set_per_process_memory_fraction=lambda fraction: calls.append(
            ("budget", fraction)
        ),
        reset_peak_memory_stats=lambda: None,
    )
    runtime = SimpleNamespace(
        torch=SimpleNamespace(cuda=cuda, bfloat16="bf16"), dit=dit, lm=lm
    )
    monkeypatch.setattr(adapter, "prepare_runtime", lambda *args: runtime)
    model = adapter.AceStepAdapter()
    model.load("ace-step-1.5-turbo", "bf16", 8192, 12288)
    assert calls[0] == ("budget", 8192 / 12288)
    assert calls[1][1]["compile_model"] is False and calls[1][1]["quantization"] is None
    assert calls[2][1]["backend"] == "pt" and calls[2][1]["dtype"] == "bf16"
    assert calls[2][1]["lm_model_path"] == "acestep-5Hz-lm-0.6B"


def test_generate_real_callback_and_cancellation(tmp_path, monkeypatch):
    import numpy as np
    from engine_common.runtime import CancelToken, EngineError

    adapter = module("adapter")
    monkeypatch.setattr(adapter, "preflight", lambda *a, **k: {"kind": "planned"})
    assert hasattr(adapter, "AceStepAdapter"), "Falta generación adapter"
    model = adapter.AceStepAdapter()
    events, seen = [], []
    token = CancelToken()

    def run(dit, lm, params, config, save_dir, progress):
        seen.append((params, config, save_dir))
        progress(0.52, desc="Diffusion")
        progress(0.8, desc="Decoding audio...")
        return SimpleNamespace(
            success=True,
            audios=[
                {"tensor": np.full((2, 8), 0.1, dtype="float32"), "sample_rate": 48000}
            ],
        )

    model.runtime = SimpleNamespace(
        generate_music=run,
        GenerationParams=lambda **kwargs: SimpleNamespace(**kwargs),
        GenerationConfig=lambda **kwargs: kwargs,
        dit=None,
        lm=None,
        torch=SimpleNamespace(
            cuda=SimpleNamespace(max_memory_allocated=lambda: 1024**2)
        ),
    )
    req = {
        "task": "music.song",
        "params": {
            "style": "pop",
            "lyrics": "[Verse]\nHola",
            "language": "es",
            "duration_s": 30,
        },
        "seed": 42,
        "n_outputs": 2,
    }
    result = model.generate(req, tmp_path, events.append, token)
    assert len(result["artifacts"]) == 2
    assert [a["meta"]["seed"] for a in result["artifacts"]] == [42, 43]
    assert seen[0][2] is None
    assert any(kind == "progress" and data["fraction"] == 0.52 for kind, data in events)
    assert any(kind == "stage" and data["stage"] == "decoding" for kind, data in events)
    token.cancel()
    with pytest.raises(EngineError, match="CANCELLED"):
        model.generate(req, tmp_path, events.append, token)


def test_http_factory_parent_without_torch(tmp_path):
    from engine_common import CpuGpu
    from fastapi.testclient import TestClient

    factory = module("engine_acestep")
    client = TestClient(
        factory.create_app(token="test", data_dir=tmp_path, gpu=CpuGpu())
    )
    assert (
        client.get("/v1/models", headers={"X-Studio-Engine-Token": "test"}).status_code
        == 200
    )
    assert client.get("/v1/models").status_code == 401


def module(name):
    assert importlib.util.find_spec(name), f"Falta implementación {name}"
    return importlib.import_module(name)


def test_load_configuration():
    adapter = module("adapter")
    assert adapter.load_options("bf16", "acestep-v15-turbo") == {
        "config_path": "acestep-v15-turbo",
        "device": "cuda",
        "use_flash_attention": False,
        "compile_model": False,
        "offload_to_cpu": False,
        "offload_dit_to_cpu": False,
        "quantization": None,
        "use_mlx_dit": False,
        "vae_checkpoint": "official",
    }
    assert adapter.load_options("offload", "acestep-v15-turbo")["offload_dit_to_cpu"]


def test_safe_loading_patch():
    patches = module("patches")
    upstream = Path("/opt/acestep/acestep")
    if not upstream.exists():
        upstream = (
            Path(__file__).resolve().parents[4]
            / ".cache/dev-cycle/t06/upstream/acestep"
        )
    source = (upstream / "core/generation/handler/init_service_loader.py").read_text()
    transformed = patches.patch_loader_source(source)
    assert "torch.load(" not in transformed
    assert "silence_latent.safetensors" in transformed
    assert (
        'safe_load_file(silence_latent_path)["tensor"].transpose(1, 2)' in transformed
    )


def test_generation_parameters():
    adapter = module("adapter")
    params, config = adapter.generation_options(
        {
            "task": "music.song",
            "params": {
                "lyrics": "[Verse]\nHola",
                "style": "pop",
                "duration_s": 30,
                "language": "es",
                "bpm": 94,
                "key": "C major",
            },
            "seed": 42,
        },
        1,
    )
    assert params["vocal_language"] == "es"
    assert params["lyrics"] == "[Verse]\nHola"
    assert params["caption"] == "pop"
    assert params["duration"] == 30 and params["seed"] == 43
    assert params["bpm"] == 94 and params["keyscale"] == "C major"
    assert not params["enable_normalization"] and not params["use_cot_language"]
    assert config == {
        "batch_size": 1,
        "use_random_seed": False,
        "seeds": [43],
        "allow_lm_batch": False,
    }


def test_float32_wav(tmp_path):
    import numpy as np
    import soundfile as sf

    adapter = module("adapter")
    samples = np.array([[0.1, -0.2, 0.3], [-0.4, 0.5, -0.6]], dtype="float32")
    adapter.write_wav(tmp_path / "raw.wav", samples, 48000)
    info = sf.info(tmp_path / "raw.wav")
    assert (info.subtype, info.channels, info.samplerate) == ("FLOAT", 2, 48000)
    actual, _ = sf.read(tmp_path / "raw.wav", dtype="float32")
    np.testing.assert_array_equal(actual, samples.T)


def test_descriptor_unverified():
    desc = module("descriptor").descriptor()
    assert desc.license == "MIT" and desc.commercial_use
    assert (
        desc.training_data
        == "Professionally licensed music tracks.\nA vast collection of public domain and royalty-free music.\nHigh-quality audio generated via advanced MIDI-to-Audio conversion."
    )
    assert len(desc.remote_code) == 2
    assert set(desc.tasks) == {"music.song", "music.instrumental"}
    assert all(not task.verified for task in desc.tasks.values())
    assert all(
        not feature.verified
        for task in desc.tasks.values()
        for feature in task.features.values()
    )
    assert {mode.id for mode in desc.modes} == {"bf16", "offload"}


def test_time_signature_metadata_optional():
    adapter = module("adapter")
    request = {
        "task": "music.instrumental",
        "params": {
            "style": "synthetic",
            "duration_s": 30,
            "key": "C minor",
            "time_signature": "4/4",
        },
        "seed": 1,
        "n_outputs": 1,
    }
    values, _ = adapter.generation_options(request, 0)
    assert values.get("timesignature") == "4/4"
    assert values["keyscale"] == "C minor"
    del request["params"]["time_signature"]
    assert "timesignature" not in adapter.generation_options(request, 0)[0]
    desc = module("descriptor").descriptor()
    assert "time_signature" in desc.tasks["music.song"].params_schema["properties"]


@pytest.mark.parametrize("key", ["", "x" * 33])
def test_key_descriptor_preserves_legacy_strings(key):
    from jsonschema import validate

    desc = module("descriptor").descriptor()
    for task in ("music.song", "music.instrumental"):
        schema = desc.tasks[task].params_schema["properties"]["key"]
        validate(key, schema)
