"""Regresiones de revisión 1; fixtures CPU, sin inferencia musical."""

import ast
import json
import types
from pathlib import Path

import pytest

from scripts.eval import capabilities as cli
from scripts.eval import capabilities_native as native
from scripts.eval import capabilities_runtime as runtime
from scripts.eval.capabilities_evidence import file_record
from scripts.eval.capabilities_plan import matrix, request_for
from scripts.eval.tests.test_capabilities_checks import text_bundle

ROOT = Path(__file__).resolve().parents[3]
UPSTREAM = ROOT / ".cache/dev-cycle/t17/upstream-acestep"


def row_for(case, surface="native_lab"):
    return next(r for r in matrix() if r["case"] == case and r["surface"] == surface)


def upstream_instruction():
    """Execute only inspected pure AST helper, never imports upstream/torch."""
    tree = ast.parse((UPSTREAM / "constants.py").read_text(encoding="utf-8"))
    templates = next(
        n.value
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "TASK_INSTRUCTIONS" for t in n.targets
        )
    )
    tree = ast.parse((UPSTREAM / "core/generation/handler/task_utils.py").read_text())
    fn = next(
        n
        for c in tree.body
        if isinstance(c, ast.ClassDef)
        for n in c.body
        if isinstance(n, ast.FunctionDef) and n.name == "generate_instruction"
    )
    fn.returns = None
    for a in fn.args.args:
        a.annotation = None
    scope = {"TASK_INSTRUCTIONS": ast.literal_eval(templates)}
    exec(  # noqa: S102 — inspected pure AST helper, no upstream module imports
        compile(
            ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
            "sealed-task-utils",
            "exec",
        ),
        scope,
    )
    return types.MethodType(scope["generate_instruction"], object())


def capture_params(tmp_path, monkeypatch, case):
    import numpy as np
    import soundfile as sf

    row = row_for(case)
    source = tmp_path / "voice.wav"
    sf.write(source, np.ones((48, 2), dtype=np.float32) * 0.1, 48000, subtype="FLOAT")
    fixture = {
        "style": "original",
        "instrumental_style": "Instrumental pop. No vocals, speech or humming.",
        "lyrics": "[Verse]\noriginal",
        "source": "voice.wav",
        "vocals": "voice.wav",
        "padded_source": "voice.wav",
        "input_seals": {"voice.wav": file_record(source)},
        "rights": {"voice.wav": {"authorized": True, "provenance": "CPU fixture"}},
    }
    captured = {}

    class Stop(Exception):
        pass

    def params(**values):
        # Real upstream default is nonempty; dispatcher will not replace it.
        captured.update(
            instruction="Fill the audio semantic mask based on the given conditions:"
        )
        captured.update(values)
        raise Stop

    model = types.SimpleNamespace(
        dit=types.SimpleNamespace(generate_instruction=upstream_instruction()),
        GenerationParams=params,
        lm=types.SimpleNamespace(llm_initialized=True),
    )
    adapter = types.ModuleType("adapter")
    adapter.AceStepAdapter = lambda **k: types.SimpleNamespace(runtime=model)
    for name in (
        "private_upstream_output",
        "step_hooks",
        "timed_generation",
        "upstream_call",
        "write_wav",
    ):
        setattr(adapter, name, lambda *a, **k: None)
    monkeypatch.setitem(__import__("sys").modules, "adapter", adapter)
    lab = native.NativeLabAdapter(row["checkpoint"], row["lm"], "models", tmp_path, {})
    request = request_for(row, fixture)
    request.update(capability_row=row, fixture=fixture)
    folder = tmp_path / "data/tmp" / row["job_id"]
    folder.mkdir(parents=True)
    with pytest.raises(Stop):
        lab.generate(
            request, folder, lambda e: None, types.SimpleNamespace(check=lambda: None)
        )
    return captured, row


@pytest.mark.parametrize(
    "case",
    [
        "music.retake",
        "music.cover",
        "music.repaint",
        "music.extend",
        "music.song",
        "music.instrumental",
        "music.complete",
        "audio.stems",
    ],
)
def test_r01_effective_generation_params_instruction(tmp_path, monkeypatch, case):
    params, _row = capture_params(tmp_path, monkeypatch, case)
    assert params["instruction"] == upstream_instruction()(
        params["task_type"],
        **{
            k: v
            for k, v in _row["control"].items()
            if k in ("track_name", "complete_track_classes")
        },
    )
    if params["task_type"] != "text2music":
        assert (
            params["instruction"]
            != "Fill the audio semantic mask based on the given conditions:"
        )


def test_r02_input_contract_data_relative():
    row = row_for("timbre_ref", "v1")
    row["control"]["reference"] = "A"
    fixture = {
        "style": "own",
        "lyrics": "own",
        "references": {
            "A": {
                "path": "data/inputs/ref.wav",
                "role": "reference_audio",
                "sha256": "a" * 64,
                "media_type": "audio/wav",
            }
        },
    }
    request = request_for(row, fixture)
    assert request["inputs"][0] == {
        **fixture["references"]["A"],
        "path": "inputs/ref.wav",
    }


def test_r03_unregistered_marker_is_not_audited_lora(tmp_path):
    folder = tmp_path / "adapter"
    folder.mkdir()
    (folder / "adapter_config.json").write_text('{"peft_type":"LORA"}')
    (folder / "adapter_model.safetensors").write_bytes(b"CPU fixture")
    marker = tmp_path / "marker"
    marker.write_text("unrelated")
    resource = {
        "path": "adapter",
        "checkpoint": "acestep-v15-turbo",
        "license": "",
        "commercial_use": None,
        "dataset_provenance": "CPU",
        "consent": True,
        "files": {p.name: file_record(p) for p in folder.iterdir()},
        "loader_audit": {
            "approved": True,
            "peft_version": "0.18.1",
            "sources": {"marker": file_record(marker)},
        },
    }
    with pytest.raises(ValueError, match="lora_prerequisite"):
        native.validate_lora(resource, tmp_path)


def test_r04_cli_resources_cannot_override_original_text(tmp_path):
    text_bundle(tmp_path)
    assert (
        cli.main(["plan", "--session", "r04", "--text-bundle", "text"], root=tmp_path)
        == 0
    )
    plan = json.loads((tmp_path / "eval/capabilities/r04/plan.json").read_text())
    resources = tmp_path / "resources.json"
    resources.write_text(json.dumps({"style": "tampered", "lyrics": "tampered"}))

    class API:
        def __init__(self):
            self.calls = []

        def request(self, *args, **kwargs):
            self.calls.append(args)
            raise ValueError("CPU probe reached POST")

    api = API()
    result = cli.main(
        [
            "execute",
            "--session",
            "r04",
            "--case-id",
            plan["rows"][0]["job_id"],
            "--resources",
            "resources.json",
        ],
        root=tmp_path,
        api=api,
    )
    assert result == 2 and api.calls == []


def test_r05_contract_output_is_relative_to_data(tmp_path):
    row = row_for("music.song", "v1")
    raw = tmp_path / "data/tmp" / row["job_id"] / "output.wav"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"CPU output, not musical evidence")
    folder = tmp_path / "evaluation"
    folder.mkdir()
    runtime.copy_outputs(
        row,
        [
            {
                "path": f"tmp/{row['job_id']}/output.wav",
                "sha256": file_record(raw)["sha256"],
            }
        ],
        tmp_path,
        folder,
    )
    assert (folder / "output.wav").read_bytes() == raw.read_bytes()


def test_r06_complete_initialized_lm_keeps_source(tmp_path, monkeypatch):
    params, _ = capture_params(tmp_path, monkeypatch, "music.complete")
    # Pinned upstream decision with an initialized LM: thinking produces codes.
    tree = ast.parse((UPSTREAM / "inference.py").read_text(encoding="utf-8"))
    assigns = {
        n.targets[0].id: n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
    }
    scope = {
        "params": types.SimpleNamespace(**params),
        "llm_handler": types.SimpleNamespace(llm_initialized=True),
        "need_lm_for_cot": False,
        "morph_on_text2music": False,
        "skip_lm_tasks": ast.literal_eval(assigns["skip_lm_tasks"]),
    }
    for name in ("skip_lm", "use_lm"):
        scope[name] = eval(
            compile(ast.Expression(assigns[name]), "pinned-lm-decision", "eval"), scope
        )
    assert scope["use_lm"] is False, "LM codes would bypass vocals source"
    assert params["src_audio"].endswith("voice.wav")
    assert params["lm_cfg_scale"] == 2.0
    source_tree = ast.parse(
        (UPSTREAM / "core/generation/handler/generate_music_request.py").read_text()
    )
    branch = next(
        n
        for n in ast.walk(source_tree)
        if isinstance(n, ast.If)
        and ast.unparse(n.test) == "src_audio is not None"
        and any(
            isinstance(c, ast.Call)
            and isinstance(c.func, ast.Attribute)
            and c.func.attr == "process_src_audio"
            for c in ast.walk(n)
        )
    )
    calls = []
    dit = types.SimpleNamespace(
        _has_non_empty_audio_codes=lambda v: bool(v.strip()),
        process_src_audio=lambda source: calls.append(source) or "consumed vocals",
    )
    scope = {
        "self": dit,
        "src_audio": params["src_audio"],
        "audio_code_string": params["audio_codes"],
        "logger": types.SimpleNamespace(info=lambda *a: None, error=lambda *a: None),
    }
    # Only the valid-source branch; return statements belong to upstream function.
    body = ast.Module(body=branch.body, type_ignores=[])
    fn = ast.FunctionDef(
        name="source_branch",
        args=ast.arguments(
            posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
        ),
        body=body.body + [ast.Return(ast.Name("processed_src_audio", ast.Load()))],
        decorator_list=[],
    )
    exec(  # noqa: S102 — inspected source-routing branch with CPU doubles
        compile(
            ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
            "pinned-source-decision",
            "exec",
        ),
        scope,
    )
    assert scope["source_branch"]() == "consumed vocals"
    assert calls == [params["src_audio"]]


@pytest.mark.parametrize(
    "path", ["../escape.wav", "data/data/ref.wav", "C:/outside.wav", "/outside.wav"]
)
def test_r02_input_escapes_rejected(path):
    row = row_for("timbre_ref", "v1")
    row["control"]["reference"] = "A"
    with pytest.raises(ValueError, match="data_path"):
        request_for(
            row, {"style": "own", "lyrics": "own", "references": {"A": {"path": path}}}
        )


@pytest.mark.parametrize(
    "path",
    [
        "../tmp/x.wav",
        "data/tmp/x.wav",
        "/absolute.wav",
        "C:/absolute.wav",
        "tmp/other/output.wav",
    ],
)
def test_r05_output_escape_and_other_jobs_rejected(tmp_path, path):
    with pytest.raises(ValueError):
        runtime.copy_outputs(
            row_for("music.song", "v1"), [{"path": path}], tmp_path, tmp_path
        )


def test_r02_real_server_estimate_contract_without_child(tmp_path, monkeypatch):
    from engine_common.server import create_app
    from fastapi.testclient import TestClient

    monkeypatch.syspath_prepend(str(ROOT / "apps/engines/acestep"))
    from descriptor import descriptor

    raw = tmp_path / "data/inputs/ref.wav"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"CPU contract fixture; not music")
    row = row_for("timbre_ref", "v1")
    row["control"]["reference"] = "A"
    fixture = {
        "style": "own",
        "lyrics": "own",
        "references": {
            "A": {
                "path": "data/inputs/ref.wav",
                "role": "reference_audio",
                "media_type": "audio/wav",
                "sha256": file_record(raw)["sha256"],
            }
        },
    }
    app = create_app(
        [descriptor()],
        "must.not.start:Factory",
        token="CPU-test-token",
        data_dir=tmp_path / "data",
        gpu=types.SimpleNamespace(snapshot=lambda: (12000, 10000)),
    )
    with TestClient(app) as client:
        request = request_for(row, fixture)
        response = client.post(
            "/v1/estimate",
            json=request,
            headers={"X-Studio-Engine-Token": "CPU-test-token"},
        )
        assert response.status_code == 200, response.text
        request["inputs"][0]["path"] = "data/inputs/ref.wav"
        assert (
            client.post(
                "/v1/estimate",
                json=request,
                headers={"X-Studio-Engine-Token": "CPU-test-token"},
            ).status_code
            == 422
        )


def test_r04_lawful_resources_preserve_sealed_text(tmp_path):
    text_bundle(tmp_path)
    assert (
        cli.main(
            ["plan", "--session", "lawful", "--text-bundle", "text"], root=tmp_path
        )
        == 0
    )
    folder = tmp_path / "eval/capabilities/lawful"
    plan = json.loads((folder / "plan.json").read_text())
    (tmp_path / "resources.json").write_text(json.dumps({"prerequisites": {}}))

    class API:
        def request(self, method, path, body=None, **kwargs):
            if path == "/v1/jobs":
                assert body["params"]["style"] == plan["fixture"]["style"]
                assert body["params"]["lyrics"] == plan["fixture"]["lyrics"]
                assert (folder / body["job_id"] / "resources-receipt.json").exists()
                from scripts.eval.benchmark_runtime import ApiError

                raise ApiError("INVALID_PARAMS", 422)
            return {"ok": True}

    row = plan["rows"][0]
    assert (
        cli.main(
            [
                "execute",
                "--session",
                "lawful",
                "--case-id",
                row["job_id"],
                "--resources",
                "resources.json",
            ],
            root=tmp_path,
            api=API(),
        )
        == 0
    )
    receipt = json.loads(
        (folder / row["job_id"] / "resources-receipt.json").read_text()
    )
    assert receipt["text_fixture"] == plan["fixture"]


def lora_fixture(root):
    import shutil

    import numpy as np
    from safetensors.numpy import save_file

    folder = root / "models/cpu-lora"
    folder.mkdir(parents=True)
    (folder / "adapter_config.json").write_text('{"peft_type":"LORA"}')
    save_file(
        {"cpu_fixture": np.zeros((1,), dtype=np.float32)},
        str(folder / "adapter_model.safetensors"),
    )
    source_files = {}
    for relative in (
        "peft_model.py",
        "config.py",
        "utils/other.py",
        "utils/save_and_load.py",
    ):
        path = root / "peft" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            ROOT / ".cache/dev-cycle/t10/loader-audit/sources/peft" / relative, path
        )
        source_files[f"peft/{relative}"] = file_record(path)
    loader = root / "scripts/eval/capabilities_native.py"
    loader.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/eval/capabilities_native.py", loader)
    audit = {
        "status": "approved",
        "peft_version": "0.18.1",
        "reviewer": "CPU fixture only",
        "reviewed_at": "2026-10-06",
        "source_files": source_files,
        "safe_loader": {
            "path": "scripts/eval/capabilities_native.py",
            "seal": file_record(loader),
            "local_safetensors_only": True,
            "alias_loader_no_fallback": True,
        },
    }
    receipt = root / "audit.json"
    receipt.write_text(json.dumps(audit))
    audit_ref = {
        "receipt": "audit.json",
        "seal": file_record(receipt),
        "approved": True,
        "peft_version": "0.18.1",
        "sources": source_files,
    }
    resource = {
        "id": "cpu-lora",
        "revision": "a" * 40,
        "path": "models/cpu-lora",
        "checkpoint": "acestep-v15-turbo",
        "license": "CC-BY-NC-4.0",
        "commercial_use": False,
        "dataset_provenance": "synthetic private CPU fixture",
        "consent": True,
        "files": {p.name: file_record(p) for p in folder.iterdir()},
        "loader_audit": audit_ref,
        "laboratory_only": True,
    }
    entry = {
        **resource,
        "kind": "lora",
        "dest": resource["path"],
        "files": [
            {
                "path": k,
                **v,
                "format": "safetensors" if k.endswith("safetensors") else "metadata",
            }
            for k, v in resource["files"].items()
        ],
    }
    (root / "models/models.lock.json").write_text(
        json.dumps({"models": {"cpu-lora": entry}})
    )
    return resource, audit


@pytest.mark.parametrize(
    "field,value",
    [("license", ""), ("commercial_use", None), ("revision", "main"), ("consent", 1)],
)
def test_r03_registered_metadata_rejected(tmp_path, field, value):
    resource, _ = lora_fixture(tmp_path)
    resource[field] = value
    with pytest.raises(ValueError, match="lora_prerequisite"):
        native.validate_lora(resource, tmp_path)


def test_r03_positive_registered_private_resource(tmp_path):
    resource, _ = lora_fixture(tmp_path)
    assert native.validate_lora(resource, tmp_path) == tmp_path / "models/cpu-lora"


@pytest.mark.parametrize(
    "mutation",
    [
        "lock_absent",
        "unregistered",
        "revision",
        "artifact_hash",
        "receipt_hash",
        "receipt_unapproved",
        "mirror_changed",
        "unsafe_loader",
        "noncommercial_default",
        "config",
        "extra_file",
    ],
)
def test_r03_registered_audit_and_weights_fail_closed(tmp_path, mutation):
    resource, audit = lora_fixture(tmp_path)
    lockpath = tmp_path / "models/models.lock.json"
    lock = json.loads(lockpath.read_text())
    if mutation == "lock_absent":
        lockpath.unlink()
    elif mutation == "unregistered":
        lock["models"] = {}
        lockpath.write_text(json.dumps(lock))
    elif mutation == "revision":
        lock["models"]["cpu-lora"]["revision"] = "b" * 40
        lockpath.write_text(json.dumps(lock))
    elif mutation in ("artifact_hash", "mirror_changed", "config", "extra_file"):
        path = {
            "artifact_hash": "models/cpu-lora/adapter_model.safetensors",
            "mirror_changed": "peft/utils/other.py",
            "config": "models/cpu-lora/adapter_config.json",
            "extra_file": "models/cpu-lora/adapter_model.bin",
        }[mutation]
        (tmp_path / path).write_text("changed")
    elif mutation == "receipt_hash":
        (tmp_path / "audit.json").write_text("changed")
    elif mutation == "noncommercial_default":
        resource.pop("laboratory_only")
    else:
        if mutation == "receipt_unapproved":
            audit["status"] = "pending"
        else:
            audit["safe_loader"]["alias_loader_no_fallback"] = False
        (tmp_path / "audit.json").write_text(json.dumps(audit))
        resource["loader_audit"]["seal"] = file_record(tmp_path / "audit.json")
        lock["models"]["cpu-lora"]["loader_audit"] = resource["loader_audit"]
        lockpath.write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="lora_prerequisite"):
        native.validate_lora(resource, tmp_path)


def test_r03_runtime_identity_and_alias_safe_loading(tmp_path, monkeypatch):
    import sys

    resource, audit = lora_fixture(tmp_path)
    peft = types.ModuleType("peft")
    peft.__version__ = "0.18.1"
    peft.__file__ = str(tmp_path / "peft/__init__.py")
    monkeypatch.setitem(sys.modules, "peft", peft)
    utils = types.ModuleType("peft.utils")
    peft.utils = utils
    monkeypatch.setitem(sys.modules, "peft.utils", utils)
    original = lambda *a, **k: pytest.fail("unsafe fallback called")
    modules = {}
    for name in (
        "peft.peft_model",
        "peft.config",
        "peft.utils.other",
        "peft.utils.save_and_load",
    ):
        module = types.ModuleType(name)
        module.__file__ = str(tmp_path / (name.replace(".", "/") + ".py"))
        module.load_peft_weights = original
        monkeypatch.setitem(sys.modules, name, module)
        modules[name] = module
    utils.save_and_load = modules["peft.utils.save_and_load"]
    weights = types.ModuleType("safetensors.torch")
    weights.load_file = lambda path, device: {"safe": Path(path).name, "device": device}
    monkeypatch.setitem(sys.modules, "safetensors.torch", weights)
    folder = tmp_path / resource["path"]
    with native.safe_lora_weights(folder, audit):
        for module in modules.values():
            assert module.load_peft_weights(str(folder)) == {
                "safe": "adapter_model.safetensors",
                "device": "cpu",
            }
        with pytest.raises(ValueError, match="lora_loader_nonlocal"):
            modules["peft.peft_model"].load_peft_weights("https://forbidden.invalid")
    assert all(module.load_peft_weights is original for module in modules.values())
    modules["peft.config"].__file__ = str(tmp_path / "foreign.py")
    with (
        pytest.raises(ValueError, match="peft_runtime_module_changed"),
        native.safe_lora_weights(folder, audit),
    ):
        pytest.fail("must reject arbitrary mirror module")
    modules["peft.config"].__file__ = str(tmp_path / "peft/config.py")
    (tmp_path / "peft/config.py").write_text("changed")
    with (
        pytest.raises(ValueError, match="peft_runtime_source_changed"),
        native.safe_lora_weights(folder, audit),
    ):
        pytest.fail("must reject changed runtime")
