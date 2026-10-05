import json
from pathlib import Path

import engine_contract as contract
import pytest


def test_remote_code_descriptor_compatible_and_preserved():
    payload = {
        "id": "test",
        "family": "test",
        "version": "1",
        "revision": "fixed",
        "license": "MIT",
        "commercial_use": True,
        "training_data": "literal",
        "provider": {"type": "local"},
        "weights": [],
        "modes": [],
        "tasks": {},
    }
    legacy = contract.ModelDescriptor(**payload)
    assert "remote_code" in contract.ModelDescriptor.model_fields, (
        "Falta hashes de código remoto opcionales"
    )
    assert legacy.remote_code == []
    entry = {"path": "model/modeling.py", "sha256": "a" * 64}
    assert contract.ModelDescriptor(**payload, remote_code=[entry]).model_dump()[
        "remote_code"
    ] == [entry]
    for invalid in (
        {"path": "../evil.py", "sha256": "a" * 64},
        {"path": "safe.py", "sha256": "bad"},
        {"path": "/outside.py", "sha256": "a" * 64},
    ):
        with pytest.raises(ValueError):
            contract.ModelDescriptor(**payload, remote_code=[invalid])


def test_models_and_schema():
    assert hasattr(contract, "JobRequest"), (
        "JobRequest y esquema todavía no implementados"
    )
    request = contract.JobRequest(
        job_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        task="music.song",
        model_id="mock",
        inputs=[],
        params={},
        output_dir="tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV/",
        timeout_s=30,
    )
    assert request.n_outputs == 1
    with pytest.raises(ValueError):
        contract.JobRequest(**{**request.model_dump(), "output_dir": "../escape"})
    versioned = Path("packages/contracts/engine-v1.json")
    assert json.loads(versioned.read_text()) == contract.contract_schema()


def test_forward_compatibility_and_event_validation():
    from pydantic import ValidationError

    request = contract.JobRequest(
        job_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        task="music.song",
        model_id="mock",
        output_dir="tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV/",
        timeout_s=30,
        future_optional={"value": 1},
    )
    assert "future_optional" not in request.model_dump()
    event = contract.Event(
        seq=1,
        job_id=request.job_id,
        type="progress",
        data={"fraction": 0.5, "future_optional": True},
    )
    assert event.data["fraction"] == 0.5 and event.ts.tzinfo is not None
    with pytest.raises(ValidationError):
        contract.Event(
            seq=2, job_id=request.job_id, type="progress", data={"fraction": 2}
        )
    with pytest.raises(ValidationError):
        contract.Event(
            seq=2,
            job_id=request.job_id,
            type="error",
            data={"code": "unknown", "message": "x", "retryable": False},
        )


def test_python_311_syntax_and_no_torch_parent():
    import ast

    paths = [
        Path("packages/engine-contract/engine_contract"),
        Path("apps/engines/common/engine_common"),
    ]
    for folder in paths:
        for path in folder.glob("*.py"):
            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"), feature_version=(3, 11)
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    assert all(
                        not alias.name.startswith("torch") for alias in node.names
                    )
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or "").startswith("torch")


@pytest.mark.parametrize(
    "event_type,data",
    [
        ("stage", {}),
        ("progress", {"fraction": 2}),
        ("progress", {"fraction": -0.1}),
        ("delta", {}),
        ("artifact", {"output_index": 0}),
        ("log", {"level": "info"}),
        ("done", {"artifacts": []}),
        ("error", {"code": "UNKNOWN", "message": "x", "retryable": False}),
        ("cancelled", {}),
    ],
)
def test_exported_event_schema_rejects_invalid_payload(event_type, data):
    from jsonschema import Draft202012Validator

    event = {
        "seq": 1,
        "job_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "type": event_type,
        "data": data,
    }
    with pytest.raises(ValueError):
        contract.Event.model_validate(event)
    schema = contract.contract_schema()
    event_schema = {"$defs": schema["$defs"], "$ref": "#/$defs/Event"}
    assert list(Draft202012Validator(event_schema).iter_errors(event)), (
        "El esquema exportado debe rechazar el mismo payload que Pydantic"
    )


def test_standalone_event_schema_resolves_payload_refs_and_optional_fields():
    from jsonschema import Draft202012Validator

    event = contract.Event(
        seq=1,
        job_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        type="progress",
        data={"fraction": 0.5, "future_optional": True},
    ).model_dump(mode="json")
    event["data"]["future_optional"] = True
    Draft202012Validator(contract.Event.model_json_schema()).validate(event)


def test_export_cli_generates_and_detects_stale_contract(tmp_path, monkeypatch, capsys):
    import importlib.util

    source = Path("scripts/export_contracts.py").resolve()
    spec = importlib.util.spec_from_file_location("export_contract_cli", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        module, "__file__", str(tmp_path / "scripts/export_contracts.py")
    )
    monkeypatch.setattr("sys.argv", ["export_contracts.py", "--check"])
    assert module.main() == 1
    assert "out of date" in capsys.readouterr().out
    monkeypatch.setattr("sys.argv", ["export_contracts.py"])
    assert module.main() == 0
    monkeypatch.setattr("sys.argv", ["export_contracts.py", "--check"])
    assert module.main() == 0
    assert "up to date" in capsys.readouterr().out
    (tmp_path / "packages/contracts/engine-v1.json").write_text("{}")
    assert module.main() == 1
