"""El server no arranca sobre una raÃ­z declarada sin acreditar."""

from uuid import UUID

import pytest
from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient
from studio_storage_guard.preflight import StorageGuardError


def test_storage_uuid_is_optional_but_typed():
    value = UUID("12345678-1234-4234-8234-123456789abc")
    settings = Settings(_env_file=None, engine_token="test-neutral", storage_uuid=value)
    assert settings.storage_uuid == value


def test_storage_gate_rejects_before_logging_or_migration(tmp_path, monkeypatch):
    from app import main
    from studio_storage_guard import preflight

    events = []

    def reject(*args, **kwargs):
        events.append("storage")
        raise StorageGuardError()

    monkeypatch.setattr(preflight, "verify_root", reject)
    monkeypatch.setattr(
        main, "configure_logging", lambda settings: events.append("log")
    )
    monkeypatch.setattr(main, "migrate", lambda path: events.append("migrate"))
    settings = Settings(
        _env_file=None,
        engine_token="test-neutral",
        data_dir=tmp_path / "data",
        models_dir=tmp_path / "models",
        storage_uuid="12345678-1234-4234-8234-123456789abc",
    )

    with pytest.raises(StorageGuardError), TestClient(create_app(settings)):
        pass

    assert events == ["storage"]
