"""Shift CLI con entradas sintéticas; no usa secretos ni audio privado."""

import pytest
from test_generate import ROOT, module, publication_setup

DIRECT = ["--task", "music.instrumental", "--style", "synthetic", "--duration", "30"]


@pytest.mark.parametrize("value", ["1", "3", "5", "2.5"])
def test_direct_shift(value):
    result = module().read_request(DIRECT + ["--shift", value])
    assert result["params"]["shift"] == float(value)


@pytest.mark.parametrize("value", ["0", "6", "nan", "inf", "-inf"])
def test_invalid_direct_shift(value):
    with pytest.raises(ValueError, match="INVALID_PARAMS"):
        module().read_request(DIRECT + ["--shift=" + value])


def test_omitted_shift_unchanged():
    assert "shift" not in module().read_request(DIRECT)["params"]


def test_brief_shift_override(tmp_path):
    directory = tmp_path / "eval/briefs"
    directory.mkdir(parents=True)
    (directory / "briefs.yaml").write_text(
        "version: 1\nbriefs:\n  SYNTH:\n    style: synthetic\n"
        "    duration_s: 30\n    language: es\n    task: music.instrumental\n",
        encoding="utf-8",
    )
    result = module().read_request(["--brief", "SYNTH", "--shift", "3"], root=tmp_path)
    assert result["params"]["shift"] == 3
    assert (
        "shift"
        not in module().read_request(["--brief", "SYNTH"], root=tmp_path)["params"]
    )


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        0,
        6,
        True,
        "3",
        None,
        10**400,
        -(10**400),
    ],
    ids=[
        "nan",
        "inf",
        "negative-inf",
        "zero",
        "six",
        "bool",
        "string",
        "null",
        "huge-positive",
        "huge-negative",
    ],
)
def test_invalid_shift_rejected_before_enqueue(tmp_path, monkeypatch, value):
    import httpx

    m, request, config, transport, _ = publication_setup(tmp_path, monkeypatch)
    request["params"]["shift"] = value
    calls = []
    original = transport.handle_request

    def tracked(req):
        calls.append((req.method, req.url.path))
        return original(req)

    monkeypatch.setattr(transport, "handle_request", tracked)
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match="^INVALID_PARAMS$"),
    ):
        m.generate(request, config=config, root=ROOT, client=client)
    assert ("POST", "/v1/jobs") not in calls


def test_explicit_shift_preserved_in_manifest(tmp_path, monkeypatch):
    import json

    import httpx

    m, request, config, transport, _ = publication_setup(tmp_path, monkeypatch)
    request["params"]["shift"] = 3
    original = transport.handle_request
    jobs = []

    def with_shift(req):
        response = original(req)
        if req.url.path == "/v1/models":
            models = response.json()
            models[0]["tasks"][request["task"]]["params_schema"]["properties"][
                "shift"
            ] = {"type": "number", "minimum": 1, "maximum": 5}
            return httpx.Response(200, json=models)
        if req.method == "POST" and req.url.path == "/v1/jobs":
            jobs.append(json.loads(req.content))
        return response

    monkeypatch.setattr(transport, "handle_request", with_shift)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, root=ROOT, client=client)
    assert jobs[0]["params"]["shift"] == 3
    manifest = json.loads(
        (destinations[0] / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["request"]["params"]["shift"] == 3
