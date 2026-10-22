"""El mecanismo existente conserva el token: no se crea otro generador."""

import re
import runpy
from pathlib import Path


def test_existing_init_env_generates_once(tmp_path, monkeypatch, capsys):
    source = Path(__file__).resolve().parents[3] / "scripts/init_env.py"
    main = runpy.run_path(str(source))["main"]
    template = tmp_path / "fixture.example"
    target = tmp_path / "fixture.env"
    template.write_text(
        "STUDIO_ENGINE_TOKEN=\nSTUDIO_DATA_DIR=./data\n", encoding="utf-8"
    )
    monkeypatch.setitem(main.__globals__, "ENV_EXAMPLE", template)
    monkeypatch.setitem(main.__globals__, "ENV_FILE", target)
    main()
    original = target.read_bytes()
    main()
    assert target.read_bytes() == original
    token = target.read_text().splitlines()[0].partition("=")[2]
    assert re.fullmatch(r"[0-9a-f]{64}", token)
    assert token not in capsys.readouterr().out
