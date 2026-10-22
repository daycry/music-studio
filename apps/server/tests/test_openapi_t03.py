"""Regresiones de contrato y ciclo de vida T03 sin datos reales."""

import importlib.util
import json
from uuid import uuid4

import pytest
from app.main import create_app
from app.settings import ROOT, Settings
from fastapi.testclient import TestClient
from pydantic import ValidationError

PRIVATE = ROOT / ".cache/dev-cycle/m1/t03-api-implementation"


@pytest.fixture
def workspace():
    path = PRIVATE / "fixtures" / uuid4().hex
    path.mkdir(parents=True)
    return path


@pytest.fixture
def exporter():
    spec = importlib.util.spec_from_file_location(
        "export_t03", ROOT / "scripts/export_contracts.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config(path):
    return Settings(
        _env_file=None,
        engine_token="test-neutral",
        data_dir=path / "data",
        models_dir=path / "models",
    )


def test_factory_has_no_runtime_side_effects(workspace, monkeypatch):
    from app import main

    def forbidden(*args, **kwargs):
        pytest.fail("Runtime initialization before lifespan")

    for name in [
        "configure_logging",
        "migrate",
        "create_db_engine",
        "DailyBackup",
        "reconcile",
    ]:
        monkeypatch.setattr(main, name, forbidden)
    app = create_app(config(workspace))
    assert "/health" in app.openapi()["paths"]
    assert not list(workspace.iterdir())
    assert not hasattr(app.state, "db")


def test_export_ignores_all_environment_sources(exporter, workspace, monkeypatch):
    before = exporter.server_schema()
    poison = {
        "DATA_DIR": "Z:/outside",
        "MODELS_DIR": "Z:/outside",
        "ENGINE_TOKEN": " invalid secret ",
        "ENGINES": "broken",
        "VRAM_MARGIN_MB": "-1",
        "NIGHTLY_WINDOW": "invalid",
        "WEB_ORIGIN": "https://evil.test",
        "ALLOWED_HOSTS": "evil.test",
    }
    for key, value in poison.items():
        monkeypatch.setenv("STUDIO_" + key, value)
    dotenv = workspace / ".env"
    dotenv.write_text("\n".join("STUDIO_" + k + "=" + v for k, v in poison.items()))
    monkeypatch.setitem(Settings.model_config, "env_file", dotenv)
    assert exporter.server_schema() == before
    with pytest.raises(ValidationError):
        create_app()
    from app.settings import ContractSettings

    with pytest.raises(ValidationError):
        ContractSettings(engine_token=" bad ")
    assert not (workspace / "data").exists()


@pytest.mark.parametrize("stale", ["engine-v1.json", "openapi.json", "both", "missing"])
def test_export_checks_every_contract(exporter, workspace, capsys, stale):
    assert exporter.main([], output_dir=workspace) == 0
    baseline = {p.name: p.read_bytes() for p in workspace.iterdir()}
    for name in baseline:
        if stale in [name, "both"]:
            (workspace / name).write_text("{}")
        if stale == "missing":
            (workspace / name).unlink()
    assert exporter.main(["--check"], output_dir=workspace) == 1
    output = capsys.readouterr().out
    assert "engine-v1.json" in output and "openapi.json" in output
    assert exporter.main([], output_dir=workspace) == 0
    assert {p.name: p.read_bytes() for p in workspace.iterdir()} == baseline
    assert exporter.main(["--check"], output_dir=workspace) == 0


def test_published_contract_matches_real_factory(exporter):
    expected = (
        json.dumps(
            exporter.server_schema(), indent=2, sort_keys=True, ensure_ascii=False
        )
        + "\n"
    )
    assert (ROOT / "packages/contracts/openapi.json").read_text(
        encoding="utf-8"
    ) == expected


def test_health_and_actual_problem_responses(workspace, monkeypatch):
    app = create_app(config(workspace))
    schema = app.openapi()
    operation = schema["paths"]["/health"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/HealthDTO")
    for status in ["403", "500"]:
        from app.api_models import ProblemDTO

        assert (
            operation["responses"][status]["content"]["application/problem+json"][
                "schema"
            ]
            == ProblemDTO.model_json_schema()
        )
    with TestClient(
        app, base_url="http://127.0.0.1:8000", raise_server_exceptions=False
    ) as client:
        assert client.get("/health").json() == {
            "status": "running",
            "process": "server",
        }
        assert client.get("/health", headers={"Host": "evil.test"}).status_code == 403
        assert (
            client.get("/health", headers={"Origin": "http://evil.test"}).status_code
            == 403
        )
        for route in app.routes:
            if route.path == "/health":

                async def broken():
                    raise RuntimeError("private secret")

                monkeypatch.setattr(route.dependant, "call", broken)
        response = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})
        assert response.status_code == 500
        assert response.headers["content-type"] == "application/problem+json"
        assert (
            response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
        )
        assert response.json() == {
            "type": "about:blank",
            "title": "Internal server error",
            "status": 500,
            "detail": "Internal server error",
            "code": "INTERNAL",
        }
    assert "private secret" not in (workspace / "data/logs/server.log").read_text()


def test_lifecycle_preserves_migration_backup_and_closes_handlers(workspace):
    app = create_app(config(workspace))
    assert not (workspace / "data").exists()
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        assert client.get("/health").status_code == 200
        assert (workspace / "data/db/studio.sqlite").is_file()
        assert list((workspace / "data/backups").glob("*.sqlite"))
        task = app.state.backup.task
        assert not task.done()
    assert task.done()
    log = (workspace / "data/logs/server.log").read_text()
    assert "server.started" in log and "server.stopped" in log
    # Restart uses a fresh handler after shutdown.
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "stage",
    ["migrate", "create_db_engine", "DailyBackup", "reconcile", "initial", "start"],
)
def test_failed_startup_releases_acquired_resources(workspace, monkeypatch, stage):
    from unittest.mock import AsyncMock, MagicMock

    from app import main

    logger = MagicMock()
    handler = MagicMock()
    logger.handlers = [handler]
    monkeypatch.setattr(main, "configure_logging", lambda settings: logger)
    engine = MagicMock()
    scheduler = MagicMock()
    scheduler.initial = AsyncMock()
    scheduler.close = AsyncMock()
    scheduler.__dict__.pop("task", None)

    def fail(*args, **kwargs):
        raise RuntimeError("startup failure")

    monkeypatch.setattr(
        main, "migrate", fail if stage == "migrate" else lambda path: None
    )
    monkeypatch.setattr(
        main,
        "create_db_engine",
        fail if stage == "create_db_engine" else lambda *a, **k: engine,
    )
    monkeypatch.setattr(
        main, "DailyBackup", fail if stage == "DailyBackup" else lambda *a: scheduler
    )
    monkeypatch.setattr(
        main, "reconcile", fail if stage == "reconcile" else lambda *a, **k: None
    )
    if stage == "initial":
        scheduler.initial.side_effect = RuntimeError("startup failure")
    if stage == "start":
        scheduler.start.side_effect = RuntimeError("startup failure")
    with (
        pytest.raises(RuntimeError, match="startup failure"),
        TestClient(create_app(config(workspace))),
    ):
        pass
    handler.close.assert_called_once()
    if stage not in ["migrate", "create_db_engine"]:
        engine.dispose.assert_called_once()


def test_error_before_startup_is_safe_and_disk_free(workspace, monkeypatch):
    app = create_app(config(workspace))
    for route in app.routes:
        if route.path == "/health":

            async def broken():
                raise RuntimeError("private secret")

            monkeypatch.setattr(route.dependant, "call", broken)
    client = TestClient(
        app, base_url="http://127.0.0.1:8000", raise_server_exceptions=False
    )
    assert client.get("/health").status_code == 500
    assert not list(workspace.iterdir())


def test_exporter_never_reads_dotenv(exporter, monkeypatch):
    from pydantic_settings.sources import DotEnvSettingsSource

    original = DotEnvSettingsSource._read_env_files
    loaded = []

    def observe(source):
        if source.env_file is not None:
            loaded.append(True)
        return original(source)

    monkeypatch.setattr(DotEnvSettingsSource, "_read_env_files", observe)
    exporter.server_schema()
    assert not loaded


def test_cancelled_shutdown_finishes_cleanup(workspace, monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from app import main

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        engine, logger, handler = MagicMock(), MagicMock(), MagicMock()
        logger.handlers = [handler]

        async def initial():
            pass

        async def close():
            entered.set()
            await release.wait()

        scheduler = SimpleNamespace(
            initial=initial,
            start=lambda: None,
            close=close,
            task=None,
            stop=asyncio.Event(),
            cancel=MagicMock(),
        )
        monkeypatch.setattr(main, "configure_logging", lambda settings: logger)
        monkeypatch.setattr(main, "migrate", lambda path: None)
        monkeypatch.setattr(main, "create_db_engine", lambda *a, **k: engine)
        monkeypatch.setattr(main, "DailyBackup", lambda *a: scheduler)
        monkeypatch.setattr(main, "reconcile", lambda *a, **k: None)
        app = create_app(config(workspace))
        context = app.router.lifespan_context(app)
        await context.__aenter__()
        shutdown = asyncio.create_task(context.__aexit__(None, None, None))
        await entered.wait()
        shutdown.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await shutdown
        engine.dispose.assert_called_once()
        handler.close.assert_called_once()
        scheduler.cancel.set.assert_called_once()

    asyncio.run(scenario())


def test_export_preserves_existing_engine_bytes(exporter, workspace):
    assert exporter.main([], output_dir=workspace) == 0
    engine = workspace / "engine-v1.json"
    original = engine.read_bytes().replace(b"\n", b"\r\n")
    engine.write_bytes(original)
    assert exporter.main([], output_dir=workspace) == 0
    assert engine.read_bytes() == original
    assert exporter.main(["--check"], output_dir=workspace) == 0
