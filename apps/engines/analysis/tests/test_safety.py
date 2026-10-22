import hashlib
import json
from pathlib import Path

import engine_analysis
import pytest
from engine_common import EngineError


def locked_fixture(tmp_path):
    folder = tmp_path / "clap-larger-music"
    folder.mkdir()
    payload = b"safe fixture"
    (folder / "model.safetensors").write_bytes(payload)
    (folder / "config.json").write_bytes(b"{}")
    entry = {
        "files": [
            {
                "path": filename,
                "format": fmt,
                "sha256": hashlib.sha256((folder / filename).read_bytes()).hexdigest(),
                "bytes": (folder / filename).stat().st_size,
            }
            for filename, fmt in [
                ("model.safetensors", "safetensors"),
                ("config.json", "metadata"),
            ]
        ]
    }
    (tmp_path / "models.lock.json").write_text(
        json.dumps({"models": {"clap-larger-music": entry}})
    )
    return folder


def verifier():
    function = getattr(engine_analysis, "verify_model", None)
    assert callable(function), "Falta verificación estricta de recursos locales"
    return function


def test_locked_resources_reject_modified_configuration(tmp_path):
    folder = locked_fixture(tmp_path)
    (folder / "config.json").write_text('{"modified": true}')
    with pytest.raises(EngineError) as error:
        verifier()(tmp_path, "clap-larger-music")
    assert error.value.code == "WEIGHTS_MISMATCH"


def test_locked_resources_reject_unlisted_loader_files(tmp_path):
    folder = locked_fixture(tmp_path)
    (folder / "tokenizer_config.json").write_text("{}")
    with pytest.raises(EngineError) as error:
        verifier()(tmp_path, "clap-larger-music")
    assert error.value.code == "WEIGHTS_MISMATCH"


def test_locked_resources_returns_only_safe_converted_checkpoint(tmp_path):
    folder = locked_fixture(tmp_path)
    _, files = verifier()(tmp_path, "clap-larger-music")
    assert files == [folder / "model.safetensors"]


def test_http_factory_stays_free_of_torch():
    import subprocess
    import sys

    code = "import sys; import engine_analysis; from engine_common.runtime import CpuGpu; factory=getattr(engine_analysis, 'create_app', None); assert callable(factory), 'Falta factoría HTTP'; app=factory(token='test', gpu=CpuGpu()); assert 'torch' not in sys.modules; assert app.state.supervisor.factory == 'engine_analysis:AnalysisAdapter'"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
