import app
import pytest
from pydantic import ValidationError


def settings(**kwargs):
    factory = getattr(app, "Settings", None)
    assert callable(factory), "Server configuration behavior is absent"
    return factory(_env_file=None, engine_token="synthetic-token", **kwargs)


def test_settings_engines_environment(monkeypatch):
    monkeypatch.setenv(
        "STUDIO_ENGINES", "mock=http://engine-mock:8199,acestep=http://127.0.0.1:8101"
    )
    config = settings()
    assert config.engines == {
        "mock": "http://engine-mock:8199",
        "acestep": "http://127.0.0.1:8101",
    }
    assert config.vram_margin_mb == 512
    assert config.nightly_window == "01:00-07:00"


@pytest.mark.parametrize(
    "value",
    [
        "mock=https://evil.test",
        "mock=http://user:secret@engine-mock:8199",
        "mock=http://engine-mock:8199/path",
        "mock=http://engine-mock:8199,mock=http://localhost:8199",
        "broken",
    ],
)
def test_settings_reject_invalid_engines(value):
    with pytest.raises(ValidationError):
        settings(engines=value)


def test_settings_confines_paths(tmp_path):
    with pytest.raises(ValidationError):
        settings(data_dir=tmp_path.parent.parent.parent.parent.parent.parent.parent)


def test_settings_secret_required(monkeypatch):
    monkeypatch.delenv("STUDIO_ENGINE_TOKEN", raising=False)
    factory = getattr(app, "Settings", None)
    assert callable(factory), "Persistent engine token configuration is absent"
    with pytest.raises(ValidationError):
        factory(_env_file=None)


@pytest.mark.parametrize(
    "field,value",
    [
        ("web_origin", "http://evil.test:3000"),
        ("web_origin", "http://127.0.0.1:3000/path"),
        ("allowed_hosts", "*"),
        ("allowed_hosts", "server:99999"),
        ("engine_token", "invalid\nsecret"),
        ("engine_token", ""),
        ("nightly_window", "25:00-01:00"),
        ("vram_margin_mb", -1),
        ("engines", "mock=http://engine-mock:8199/?private=secret"),
    ],
)
def test_settings_invalid_fields(field, value):
    with pytest.raises(ValidationError):
        app.Settings(
            _env_file=None, **{"engine_token": "synthetic-token", field: value}
        )


def test_settings_reads_local_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("STUDIO_ENGINE_TOKEN", raising=False)
    env = tmp_path / "fixture.env"
    env.write_text(
        "STUDIO_ENGINE_TOKEN=synthetic-persistent\nSTUDIO_ALLOWED_HOSTS=localhost:8000,server:8000\n",
        encoding="utf-8",
    )
    before = env.read_bytes()
    first = app.Settings(_env_file=env)
    second = app.Settings(_env_file=env)
    assert (
        first.engine_token.get_secret_value()
        == second.engine_token.get_secret_value()
        == "synthetic-persistent"
    )
    assert env.read_bytes() == before
    assert first.allowed_hosts == ["localhost:8000", "server:8000"]
    assert "synthetic-persistent" not in repr(first)


def test_settings_duplicate_family_whitespace():
    with pytest.raises(ValidationError):
        settings(engines="mock=http://engine-mock:8199, mock=http://localhost:8199")
