"""Controles CLI explícitos, preparación y manifiestos sin GPU."""

import json

import httpx
import pytest
from test_generate import module, publication_setup

DIRECT = ["--task", "music.instrumental", "--style", "synthetic", "--duration", "30"]


def test_cli_inference_options_and_preparation():
    result = module().read_request(
        DIRECT + ["--inference-steps", "50", "--guidance-scale", "7"]
    )
    assert result["params"]["inference_steps"] == 50
    assert result["params"]["guidance_scale"] == 7
    assert result["_preparation"]["effective"]["params"] == result["params"]


@pytest.mark.parametrize(
    "args",
    [
        ["--inference-steps", "0"],
        ["--inference-steps", "201"],
        ["--guidance-scale", "nan"],
        ["--guidance-scale", "inf"],
        ["--guidance-scale", "0"],
        ["--guidance-scale", "21"],
    ],
)
def test_cli_rejects_invalid_controls(args):
    with pytest.raises(ValueError, match="INVALID_PARAMS"):
        module().read_request(DIRECT + args)


def test_brief_accepts_inference_overrides(tmp_path):
    folder = tmp_path / "eval/briefs"
    folder.mkdir(parents=True)
    (folder / "briefs.yaml").write_text(
        "version: 1\nbriefs:\n  S:\n    task: music.instrumental\n    style: synthetic\n    duration_s: 30\n    language: es\n",
        encoding="utf-8",
    )
    result = module().read_request(
        ["--brief", "S", "--inference-steps", "60", "--guidance-scale", "4"],
        root=tmp_path,
    )
    assert result["params"]["inference_steps"] == 60
    assert result["params"]["guidance_scale"] == 4


def test_explicit_controls_manifest(tmp_path, monkeypatch):
    m, request, config, transport, _ = publication_setup(tmp_path, monkeypatch)
    request["params"].update(inference_steps=50, guidance_scale=7)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    manifest = json.loads((destinations[0] / "manifest.json").read_text())
    assert manifest["request"]["params"]["inference_steps"] == 50
    assert manifest["request"]["params"]["guidance_scale"] == 7


@pytest.mark.parametrize(
    "params",
    [
        {"inference_steps": True},
        {"inference_steps": 0},
        {"inference_steps": 2.5},
        {"inference_steps": 201},
        {"guidance_scale": float("nan")},
        {"guidance_scale": True},
        {"guidance_scale": 21},
        {"guidance_scale": 10**400},
    ],
)
def test_programmatic_invalid_before_http(tmp_path, monkeypatch, params):
    m, request, config, _, _ = publication_setup(tmp_path, monkeypatch)
    request["params"].update(params)

    class Offline:
        def request(self, *args, **kwargs):
            raise ValueError("HTTP_BEFORE_VALIDATION")

    with pytest.raises(ValueError, match="INVALID_PARAMS"):
        m.generate(request, config=config, client=Offline())


def test_legacy_cli_omits_controls():
    assert "inference_steps" not in module().read_request(DIRECT)["params"]
    assert "guidance_scale" not in module().read_request(DIRECT)["params"]
