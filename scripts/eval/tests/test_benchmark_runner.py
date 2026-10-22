"""OrquestaciÃ³n con APIs/sensores inyectados; no validaciÃ³n GPU real."""

import pytest


def test_runner_timeout_preserves_existing_job_and_does_not_duplicate(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")
    assert callable(getattr(runner, "observe_job", None)), "Falta runner de job vivo"

    class Api:
        def __init__(self):
            self.calls = []

        def events(self, job, after=0, **kwargs):
            self.calls.append((job, after))
            return []

        def request(self, *args):
            return {"job_id": "j", "state": "busy"}

    class Sensor:
        def sample(self):
            return {"browser": {"visible": True}}

    api = Api()
    with pytest.raises(runner.ObservationTimeout):
        runner.observe_job(api, Sensor(), "j", tmp_path, observation_s=0, interval_s=0)
    assert (tmp_path / "observation-timeout.json").exists()
    assert api.calls == []


def test_manual_prerequisites_require_real_taskmanager_browser_and_sha(harness_module):
    runner = harness_module("benchmark_runner")
    assert callable(getattr(runner, "validate_prerequisites", None)), (
        "Falta preflight WDDM manual"
    )
    with pytest.raises(ValueError, match="task_manager"):
        runner.validate_prerequisites({"browser": {"hwnd": 1, "pid": 2}})


def test_row_rejects_fake_timing_or_missing_sensor(harness_module):
    runner = harness_module("benchmark_runner")
    assert callable(getattr(runner, "summarize_run", None)), "Falta row validity"
    run = {
        "run_id": "r",
        "job_id": "j",
        "config_id": "base",
        "duration_s": 30,
        "phase": "warm",
        "storage": "bind",
    }
    terminal = {
        "type": "done",
        "data": {
            "telemetry": {
                "run_s": 50,
                "load_s": 30,
                "vram_peak_mb": 10,
                "vram_cap_mb": 20,
                "spilled": False,
            },
            "result": {},
        },
    }
    row = runner.summarize_run(
        run, terminal, [], [], output_valid=True, fidelity_valid=True
    )
    assert row["valid"] is False and row["inference_s"] is None and row["rtf"] is None
    assert row["shared_gpu_observed"] is None


def test_session_runner_submits_once_after_estimate_and_resume_uses_receipt(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")
    assert callable(getattr(runner, "execute_run", None)), (
        "Falta ejecuciÃ³n/reanudaciÃ³n idempotente"
    )

    class Api:
        def __init__(self):
            self.calls = []

        def request(self, method, path, body=None):
            self.calls.append((method, path))
            if path == "/v1/estimate":
                return {"input_budget": {"effective_sha256": "hash"}}
            return {"job_id": "J", "state": "done"}

        def events(self, job, after, **kwargs):
            return [
                {
                    "seq": 1,
                    "job_id": "J",
                    "type": "error",
                    "data": {"code": "VRAM_EXCEEDED"},
                }
            ]

    class Sensors:
        observation_method = "task_manager_v1"

        def sample(self):
            return {}

    plan = {"timeouts": {"observation_s": 1}, "observer_policy": {"interval_s": 0}}
    run = {"run_id": "R", "job_id": "J"}
    api = Api()
    receipt = runner.execute_run(plan, run, api, Sensors(), tmp_path, {"job_id": "J"})
    assert receipt["type"] == "error"
    assert api.calls[:2] == [("POST", "/v1/estimate"), ("POST", "/v1/jobs")]
    api.calls.clear()
    runner.execute_run(plan, run, api, Sensors(), tmp_path, {"job_id": "J"})
    assert ("POST", "/v1/jobs") not in api.calls


def valid_output_bundle(harness_module, tmp_path, monkeypatch, *, frames=30 * 48000):
    import json
    from pathlib import Path

    import numpy as np
    import soundfile as sf

    planner = harness_module("benchmark_plan")
    monkeypatch.syspath_prepend(
        str(Path(__file__).resolve().parents[3] / "apps/engines/acestep")
    )
    from input_profile import SOURCE_HASHES

    request = {
        "job_id": "J",
        "model_id": "ace-step-1.5-base",
        "task": "music.song",
        "seed": 1,
        "n_outputs": 1,
        "params": {
            "style": "test",
            "lyrics": "CPU fixture",
            "language": "es",
            "duration_s": 30,
            "inference_steps": 32,
            "guidance_scale": 7,
            "shift": 1,
        },
    }
    flags = {
        "thinking": True,
        "shift": 1,
        "inference_steps": 32,
        "guidance_scale": 7,
        "lm_cfg_scale": 2,
        "audio_cover_strength": 1,
        "use_cot_caption": False,
        "use_cot_language": False,
        "use_cot_metas": False,
    }
    effective = {
        **flags,
        "params": {
            "caption": "test",
            "lyrics": "CPU fixture",
            "vocal_language": "es",
            "duration": 30,
            "seed": 1,
            "bpm": None,
            "keyscale": "",
            "enable_normalization": False,
            "lm_negative_prompt": "NO USER INPUT",
            **flags,
        },
        "config": {
            "batch_size": 1,
            "use_random_seed": False,
            "seeds": [1],
            "allow_lm_batch": False,
        },
        "lm_metadata": {"duration": 30, "language": "es"},
    }
    tokens = {"count": 3, "tokens_sha256": "0" * 64, "input_sha256": "1" * 64}
    lm = {
        "conditional": tokens,
        "unconditional": tokens,
        "context_policy": 4096,
        "reserve_tokens": 160,
    }
    branch = {
        "initial_task": "text2music",
        "resolved_task": "cover",
        "has_audio_codes": True,
        "instruction_sha256": "f295493a5987057e7eda95c4f8e5c268d35e6df991591905247bda2d04db4bac",
        "text": tokens,
        "lyrics": tokens,
    }
    planned = {
        "receipt_version": 2,
        "profile_revision": "dce621408bee8c31b4fc4811682eb9359e1bc94",
        "profile_sha256": planner.digest(SOURCE_HASHES),
        "source_hashes": SOURCE_HASHES,
        "request": request,
        "request_sha256": planner.digest(request),
        "effective": effective,
        "effective_sha256": planner.digest(effective),
        "checkpoint": {"id": "acestep-v15-base"},
        "lm": lm,
        "dit": {"candidates": {"cover": branch}},
    }
    planned["profile_revision"] = "dce621408bee8c31b4fcf4811682eb9359e1bc94"
    captured = {
        "output_index": 0,
        "planned_sha256": planner.digest(planned),
        "generation_params_sha256": planner.digest(effective["params"]),
        "generation_config_sha256": planner.digest(effective["config"]),
        "flags": flags,
        "boundaries": [
            {
                "stage": "lm_arguments",
                "metadata": effective["lm_metadata"],
                "arguments_sha256": planner.digest(
                    {"metadata": effective["lm_metadata"]}
                ),
            },
            {"stage": "lm_formatted_prompt", **lm, "cfg_sha256": planner.digest(lm)},
            {
                "stage": "dit_arguments",
                "arguments_sha256": planner.digest({"cpu_fixture": True}),
            },
            {
                "stage": "dit_resolution",
                **{
                    k: branch[k]
                    for k in (
                        "initial_task",
                        "resolved_task",
                        "has_audio_codes",
                        "instruction_sha256",
                    )
                },
            },
            {
                "stage": "dit_tokens",
                "text": {k: tokens[k] for k in ("count", "tokens_sha256")},
                "lyrics": {k: tokens[k] for k in ("count", "tokens_sha256")},
            },
        ],
    }
    folder = tmp_path / "data/tmp/J"
    folder.mkdir(parents=True)
    with sf.SoundFile(
        folder / "output-0.wav", mode="w", samplerate=48000, channels=2, subtype="FLOAT"
    ) as wav:
        wav.seek(frames - 1)
        wav.write(np.zeros((1, 2)))
    receipt_path = folder / "input-receipt-0.json"
    receipt_path.write_text(json.dumps({"planned": planned, "captured": captured}))
    terminal = {
        "type": "done",
        "data": {
            "artifacts": [
                {
                    "path": "tmp/J/output-0.wav",
                    "output_index": 0,
                    "sha256": planner.file_hash(folder / "output-0.wav"),
                }
            ],
            "telemetry": {
                "extra": {"inference_timings": [{"audio_duration_s": frames / 48000}]}
            },
            "result": {
                "input_receipts": [
                    {
                        "filename": "input-receipt-0.json",
                        "output_index": 0,
                        "sha256": planner.file_hash(receipt_path),
                    }
                ],
                "runtime_effective": {
                    "checkpoint": "acestep-v15-base",
                    "lm": "acestep-5Hz-lm-0.6B",
                    "mode": "bf16",
                    "resource_root": "/models",
                    "lm_backend": "pt",
                },
            },
        },
    }
    config = {
        "checkpoint": "acestep-v15-base",
        "lm": "acestep-5Hz-lm-0.6B",
        "mode": "bf16",
        "params": {"inference_steps": 32, "guidance_scale": 7, "shift": 1},
    }
    estimate = {"input_budget": {"effective_sha256": planned["effective_sha256"]}}
    return request, terminal, config, estimate, receipt_path


def test_fidelity_uses_actual_wav_duration_and_rejects_rehashed_wrong_seed(
    harness_module, tmp_path, monkeypatch
):
    import json

    runner = harness_module("benchmark_runner")
    planner = harness_module("benchmark_plan")
    request, terminal, config, estimate, receipt_path = valid_output_bundle(
        harness_module, tmp_path, monkeypatch
    )
    output_valid, fidelity_valid, proof = runner.verify_outputs(
        tmp_path,
        request,
        terminal,
        config=config,
        resource_root="/models",
        estimate=estimate,
    )
    assert output_valid and fidelity_valid and proof["frames"] == 30 * 48000
    receipt = json.loads(receipt_path.read_text())
    receipt["planned"]["effective"]["params"]["seed"] = 2
    receipt["planned"]["effective_sha256"] = planner.digest(
        receipt["planned"]["effective"]
    )
    receipt["captured"]["planned_sha256"] = planner.digest(receipt["planned"])
    estimate["input_budget"]["effective_sha256"] = receipt["planned"][
        "effective_sha256"
    ]
    receipt_path.write_text(json.dumps(receipt))
    terminal["data"]["result"]["input_receipts"][0]["sha256"] = planner.file_hash(
        receipt_path
    )
    with pytest.raises(ValueError, match="effective_input_mismatch"):
        runner.verify_outputs(
            tmp_path,
            request,
            terminal,
            config=config,
            resource_root="/models",
            estimate=estimate,
        )


def test_requested_duration_rejects_tiny_wav_even_with_matching_telemetry(
    harness_module, tmp_path, monkeypatch
):
    runner = harness_module("benchmark_runner")
    request, terminal, config, estimate, _ = valid_output_bundle(
        harness_module, tmp_path, monkeypatch, frames=8
    )
    with pytest.raises(ValueError, match="wav_requested_duration_mismatch"):
        runner.verify_outputs(
            tmp_path,
            request,
            terminal,
            config=config,
            resource_root="/models",
            estimate=estimate,
        )


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("cfg", "effective_controls_mismatch"),
        ("lm_duration", "effective_lm_metadata_mismatch"),
        ("dit_hash", "capture_hash_invalid"),
    ],
)
def test_rehashed_capture_rejects_verifiable_contradictions(
    harness_module, tmp_path, monkeypatch, mutation, error
):
    import json

    runner = harness_module("benchmark_runner")
    planner = harness_module("benchmark_plan")
    request, terminal, config, estimate, path = valid_output_bundle(
        harness_module, tmp_path, monkeypatch
    )
    receipt = json.loads(path.read_text())
    if mutation == "cfg":
        receipt["captured"]["flags"]["guidance_scale"] = 1
    elif mutation == "lm_duration":
        receipt["captured"]["boundaries"][0]["metadata"]["duration"] = 300
    else:
        receipt["captured"]["boundaries"][2]["arguments_sha256"] = "not-a-hash"
    path.write_text(json.dumps(receipt))
    terminal["data"]["result"]["input_receipts"][0]["sha256"] = planner.file_hash(path)
    with pytest.raises(ValueError, match=error):
        runner.verify_outputs(
            tmp_path,
            request,
            terminal,
            config=config,
            resource_root="/models",
            estimate=estimate,
        )


@pytest.mark.parametrize("variant,steps", [("turbo", 8), ("sft", 50), ("base", 32)])
def test_verifier_accepts_native_plan_and_capture_branches(
    harness_module, tmp_path, monkeypatch, variant, steps
):
    import json
    from pathlib import Path
    from types import SimpleNamespace

    import numpy as np

    runner = harness_module("benchmark_runner")
    planner = harness_module("benchmark_plan")
    request, terminal, config, estimate, path = valid_output_bundle(
        harness_module, tmp_path, monkeypatch
    )
    import adapter
    import preflight

    source = (
        Path(__file__).resolve().parents[3] / ".cache/dev-cycle/t17/upstream-acestep"
    )
    request["model_id"] = f"ace-step-1.5-{variant}"
    request["params"]["inference_steps"] = steps
    if variant == "turbo":
        request["params"].pop("guidance_scale")
    config["checkpoint"] = f"acestep-v15-{variant}"
    config["params"] = {
        k: v
        for k, v in request["params"].items()
        if k in {"shift", "inference_steps", "guidance_scale"}
    }

    class Tokenizer:
        def __call__(self, text, **kwargs):
            return {"input_ids": list(range(10))}

        def apply_chat_template(self, messages, **kwargs):
            return str(messages)

    planned = preflight.native_plan(
        request, Tokenizer(), Tokenizer(), source, config["checkpoint"]
    )
    planned["checkpoint"] = {"id": config["checkpoint"]}
    lm, dit = preflight.native_templates(source)
    lm.llm_tokenizer = Tokenizer()
    lm.generate_with_stop_condition = lambda **kwargs: None
    lm.generate_from_formatted_prompt = lambda **kwargs: None
    lm._build_unconditional_prompt = lambda **kw: lm.build_formatted_prompt_with_cot(
        kw["caption"],
        kw["lyrics"],
        kw["cot_text"],
        is_negative_prompt=True,
        negative_prompt=kw["negative_prompt"],
    )
    dit.generate_music = lambda **kwargs: None
    masks = [SimpleNamespace(bool=lambda: np.ones(10, dtype=bool))]
    dit._prepare_text_conditioning_inputs = lambda *a, **kw: (
        None,
        np.array([list(range(10))]),
        masks,
        np.array([list(range(10))]),
        masks,
    )
    values = planned["effective"]["params"]
    metadata = planned["effective"]["lm_metadata"]
    cot = lm._format_metadata_as_cot(metadata)
    cfg = {
        "caption": values["caption"],
        "lyrics": values["lyrics"],
        "cot_text": cot,
        "negative_prompt": values["lm_negative_prompt"],
        "generation_phase": "codes",
        "target_duration": 30,
    }
    formatted = lm.build_formatted_prompt_with_cot(
        values["caption"], values["lyrics"], cot
    )
    with adapter.input_capture(
        SimpleNamespace(lm=lm, dit=dit), planned, values, 0
    ) as captured:
        lm.generate_with_stop_condition(
            caption=values["caption"],
            lyrics=values["lyrics"],
            user_metadata=metadata,
            target_duration=30,
        )
        lm.generate_from_formatted_prompt(formatted_prompt=formatted, cfg=cfg)
        dit.generate_music(
            captions=values["caption"],
            lyrics=values["lyrics"],
            vocal_language=values["vocal_language"],
            audio_duration=30,
            bpm=values["bpm"],
            key_scale=values["keyscale"],
            time_signature="",
            inference_steps=steps,
            guidance_scale=7,
            audio_code_string="CPU-synthetic",
        )
        task, instruction = dit._resolve_generate_music_task(
            "text2music", "CPU-synthetic", dit.default_instruction
        )
        dit._prepare_text_conditioning_inputs(1, [instruction])
    captured["flags"] = {
        "thinking": True,
        "lm_cfg_scale": 2,
        "audio_cover_strength": 1,
        **{
            k: values[k]
            for k in (
                "use_cot_caption",
                "use_cot_language",
                "use_cot_metas",
                "shift",
                "inference_steps",
                "guidance_scale",
            )
        },
    }
    captured["generation_params_sha256"] = preflight.digest(values)
    captured["generation_config_sha256"] = preflight.digest(
        planned["effective"]["config"]
    )
    path.write_text(json.dumps({"planned": planned, "captured": captured}))
    terminal["data"]["result"]["input_receipts"][0]["sha256"] = planner.file_hash(path)
    terminal["data"]["result"]["runtime_effective"]["checkpoint"] = config["checkpoint"]
    estimate["input_budget"]["effective_sha256"] = planned["effective_sha256"]
    output, fidelity, proof = runner.verify_outputs(
        tmp_path,
        request,
        terminal,
        config=config,
        resource_root="/models",
        estimate=estimate,
    )
    assert output and fidelity and task == "cover"
    assert (
        planned["lm"]["conditional"]["input_sha256"]
        != planned["dit"]["candidates"]["cover"]["text"]["input_sha256"]
    )
    assert (
        proof["dynamic_arguments_hash_validation"]
        == "format_and_receipt_provenance_only"
    )


@pytest.mark.parametrize(
    "frames,accepted",
    [
        (30 * 48000 - 1920, True),
        (30 * 48000 - 1922, False),
        (30 * 48000 + 1920, True),
        (30 * 48000 + 1922, False),
    ],
)
def test_wav_tolerance_is_one_native_latent_frame(
    harness_module, tmp_path, monkeypatch, frames, accepted
):
    runner = harness_module("benchmark_runner")
    req, terminal, config, estimate, _ = valid_output_bundle(
        harness_module, tmp_path, monkeypatch, frames=frames
    )
    if accepted:
        assert runner.verify_outputs(
            tmp_path,
            req,
            terminal,
            config=config,
            resource_root="/models",
            estimate=estimate,
        )[:2] == (True, True)
    else:
        with pytest.raises(ValueError, match="wav_requested_duration_mismatch"):
            runner.verify_outputs(
                tmp_path,
                req,
                terminal,
                config=config,
                resource_root="/models",
                estimate=estimate,
            )


def test_v3_estimate_and_submit_allow_real_engine_preflight(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")

    class Api:
        def __init__(self):
            self.calls = []

        def operation(self, name, arguments):
            assert name == "exists"
            return False

        def request(self, method, path, body=None, **kwargs):
            self.calls.append((method, path, kwargs))
            if path == "/v1/estimate":
                return {"eta_s": 30}
            raise runner.ApiError("PRECHECK_STOP")

        def write_json(self, path, value):
            self.calls.append(("WRITE", str(path), {}))

    class Coordinator:
        def check(self):
            return None

    api = Api()
    plan = {"observation_method": "wddm_auto_v3", "timeouts": {"observation_s": 1}}
    run = {"job_id": "J"}
    request = {"job_id": "J", "timeout_s": 3600}

    with pytest.raises(runner.ApiError, match="PRECHECK_STOP"):
        runner.execute_run_v3(plan, run, api, Coordinator(), tmp_path, request)

    assert api.calls == [
        ("WRITE", str(tmp_path / "request.json"), {}),
        ("POST", "/v1/estimate", {"timeout": 120}),
        ("WRITE", str(tmp_path / "estimate.json"), {}),
        ("WRITE", str(tmp_path / "submission-intent.json"), {}),
        ("POST", "/v1/jobs", {"timeout": 120}),
    ]
