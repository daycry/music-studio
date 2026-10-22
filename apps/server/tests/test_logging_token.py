import json

import app
import httpx
import pytest
from test_settings import settings


def test_logging_redaction(tmp_path):
    factory = getattr(app, "configure_logging", None)
    assert callable(factory), "Safe JSON logging behavior is absent"
    logger = factory(settings(data_dir=tmp_path))
    logger.info(
        "synthetic-token lyrics-private\nforged log",
        extra={"job_id": "01JTEST", "song_id": "01STEST", "lyrics": "lyrics-private"},
    )
    handler = logger.handlers[0]
    handler.flush()
    lines = (tmp_path / "logs/server.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert set(data) == {"ts", "level", "proc", "job_id", "song_id", "msg"}
    assert data["job_id"] == "01JTEST"
    assert "synthetic-token" not in lines[0] and "lyrics-private" not in lines[0]
    assert handler.when == "MIDNIGHT" and handler.backupCount == 14 and handler.utc
    handler.close()


def test_engine_token_header(tmp_path):
    factory = getattr(app, "engine_client", None)
    assert callable(factory), "Authenticated local engine client behavior is absent"
    seen = []

    def receive(request):
        seen.append(request)
        return httpx.Response(200, json={"state": "idle"})

    config = settings(data_dir=tmp_path, engines={"mock": "http://engine-mock:8199"})
    with factory(config, "mock", transport=httpx.MockTransport(receive)) as connection:
        assert connection.get("/v1/health").json()["state"] == "idle"
    assert seen[0].headers["X-Studio-Engine-Token"] == "synthetic-token"
    assert str(seen[0].url) == "http://engine-mock:8199/v1/health"


def test_engine_token_never_leaves_origin(tmp_path):
    seen = []
    config = settings(data_dir=tmp_path, engines={"mock": "http://engine-mock:8199"})
    with (
        app.engine_client(
            config,
            "mock",
            transport=httpx.MockTransport(lambda request: seen.append(request)),
        ) as connection,
        pytest.raises(ValueError, match="configured local origin"),
    ):
        connection.get("http://evil.test/token")
    assert seen == []


def test_engine_does_not_follow_redirect(tmp_path):
    seen = []

    def receive(request):
        seen.append(request)
        return httpx.Response(302, headers={"Location": "http://evil.test/"})

    config = settings(data_dir=tmp_path, engines={"mock": "http://engine-mock:8199"})
    with app.engine_client(
        config, "mock", transport=httpx.MockTransport(receive)
    ) as connection:
        assert connection.get("/v1/health").status_code == 302
    assert len(seen) == 1


def test_logging_event_and_exception_redaction(tmp_path):
    logger = app.configure_logging(settings(data_dir=tmp_path))
    assert logger is app.configure_logging(settings(data_dir=tmp_path))
    try:
        raise RuntimeError("synthetic-secret lyrics-private")
    except RuntimeError:
        logger.exception(
            "request.failed",
            extra={"job_id": "forged\nsecret", "song_id": "/private/path"},
        )
    logger.info("server.started")
    logger.info("request.completed %s", "synthetic-token")
    logger.handlers[0].flush()
    lines = (tmp_path / "logs/server.log").read_text().splitlines()
    assert [json.loads(line)["msg"] for line in lines] == [
        "request.failed",
        "server.started",
        "[redacted]",
    ]
    assert "synthetic" not in "\n".join(lines) and "private" not in "\n".join(lines)
    assert all("job_id" not in json.loads(line) for line in lines)
    logger.handlers[0].close()
