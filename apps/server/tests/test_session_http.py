"""HTTP real sobre ASGI, SQLite/User y registro protegido; cola ajena aislada."""

import asyncio
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from app.event_dtos import SessionCredentialDTO
from app.local_sessions import LocalSessionRegistry, SessionError
from app.main import create_app
from app.models import User
from app.settings import ContractSettings
from fastapi.testclient import TestClient
from sqlalchemy import select, update

UNIT = Path.cwd() / ".cache/dev-cycle/m1/t06-session-http-review1-fix1"
ORIGIN = "http://127.0.0.1:3000"
BOOT = {"Origin": ORIGIN, "X-Studio-Session-Bootstrap": "1"}


@pytest.fixture
def tmp_path():
    directory = UNIT / "fixtures" / uuid4().hex
    directory.mkdir(parents=True)
    return directory


class UnrelatedQueue:
    """Sin GPU/jobs: sólo el protocolo de lifecycle ajeno a autenticación."""

    def __init__(self, engine, settings):
        self.closed = False

    async def start(self):
        pass

    async def close(self):
        self.closed = True


def config(tmp_path, **changes):
    return ContractSettings(
        engine_token="internal-engine-private", data_dir=tmp_path, **changes
    )


@contextmanager
def connection(tmp_path, **kwargs):
    app = create_app(config(tmp_path), queue_runtime_factory=UnrelatedQueue, **kwargs)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        yield client


def issue(client):
    response = client.post("/api/session/bootstrap", headers=BOOT)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    dto = SessionCredentialDTO.model_validate(response.json())
    assert dto.expires_in_s == 28800
    assert set(response.json()) == {"session_token", "expires_in_s"}
    return dto.session_token


def test_issue_validate_revoke(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        with client.app.state.db.connect() as database:
            owner = database.scalar(
                select(User.id).where(User.name == "local", User.deleted_at.is_(None))
            )
        registry = client.app.state.session_registry
        assert registry.validate(token).owner_id == owner
        assert token != "internal-engine-private"
        headers = {"Origin": ORIGIN, "X-Studio-Session-Token": token}
        response = client.delete("/api/session", headers=headers)
        assert response.status_code == 204
        assert response.content == b""
        assert response.headers["cache-control"] == "no-store"
        assert client.delete("/api/session", headers=headers).status_code == 401
        with pytest.raises(SessionError, match="SESSION_REQUIRED"):
            registry.validate(token)
    assert registry.active_count == 0
    assert client.app.state.queue.closed
    logs = "".join(p.read_text() for p in tmp_path.rglob("*.log"))
    assert token not in logs


@pytest.mark.parametrize(
    "headers,status",
    [
        ({"Origin": ORIGIN}, 401),
        ({**BOOT, "X-Studio-Session-Bootstrap": "0"}, 401),
        ({"X-Studio-Session-Bootstrap": "1"}, 403),
        ({**BOOT, "Origin": "http://evil.test"}, 403),
        ({**BOOT, "Host": "server"}, 403),
        ({**BOOT, "Host": "server:8000"}, 403),
        ({**BOOT, "Host": "localhost"}, 403),
        ({**BOOT, "Host": "127.0.0.1:8000.evil.test"}, 403),
        ({**BOOT, "Host": "localhost:8001"}, 403),
        ({**BOOT, "Origin": "null"}, 403),
        ({**BOOT, "X-Forwarded-Host": "localhost:8000", "Host": "server"}, 403),
    ],
)
def test_bootstrap_security(tmp_path, headers, status):
    with connection(tmp_path) as client:
        response = client.post("/api/session/bootstrap", headers=headers)
        assert response.status_code == status
        assert response.headers["cache-control"] == "no-store"
        assert client.app.state.session_registry.active_count == 0


@pytest.mark.parametrize(
    "body,query,extra",
    [
        (b"{}", "", {}),
        (b"x", "", {}),
        (b"", "?owner_id=private", {}),
        (b"", "?token=private", {}),
        (b"", "", {"Content-Length": "1"}),
        (b"", "", {"Content-Length": "-1"}),
        (b"", "", {"Content-Length": "x"}),
        (b"", "", {"Content-Length": "00"}),
        (b"", "", {"Transfer-Encoding": "chunked"}),
        (b"", "", {"Authorization": "private"}),
        (b"", "", {"X-Studio-Engine-Token": "private"}),
        (b"", "", {"X-Studio-Session-Token": "private"}),
    ],
)
def test_reject_payload_before_issue(tmp_path, body, query, extra):
    with connection(tmp_path) as client:
        response = client.post(
            "/api/session/bootstrap" + query, headers={**BOOT, **extra}, content=body
        )
        assert response.status_code == 422
        assert "private" not in response.text
        assert client.app.state.session_registry.active_count == 0


@pytest.mark.parametrize(
    "name,value,status",
    [
        ("Host", "127.0.0.1:8000", 403),
        ("Origin", ORIGIN, 403),
        ("X-Studio-Session-Bootstrap", "1", 401),
        ("Content-Length", "0", 422),
    ],
)
def test_asgi_injected_duplicate_headers(tmp_path, name, value, status):
    with connection(tmp_path) as client:
        headers = [
            ("Host", "127.0.0.1:8000"),
            *BOOT.items(),
            ("Content-Length", "0"),
            (name, value),
        ]
        response = client.post("/api/session/bootstrap", headers=headers)
        assert response.status_code == status


@pytest.mark.parametrize(
    "token", [None, "wrong", "internal-engine-private", "x" * 65, "a,b"]
)
def test_delete_invalid_credentials(tmp_path, token):
    with connection(tmp_path) as client:
        headers = {"Origin": ORIGIN}
        if token is not None:
            headers["X-Studio-Session-Token"] = token
        response = client.delete("/api/session", headers=headers)
        assert response.status_code == 401
        assert response.json()["code"] == "SESSION_REQUIRED"
        assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "query,body,extra",
    [
        ("?owner=private", b"", {}),
        ("", b"{}", {}),
        ("", b"", {"X-Studio-Session-Bootstrap": "1"}),
    ],
)
def test_delete_rejects_input_without_revocation(tmp_path, query, body, extra):
    with connection(tmp_path) as client:
        token = issue(client)
        headers = {"Origin": ORIGIN, "X-Studio-Session-Token": token, **extra}
        assert (
            client.request(
                "DELETE", "/api/session" + query, headers=headers, content=body
            ).status_code
            == 422
        )
        assert client.app.state.session_registry.validate(token)


def test_delete_duplicate_token(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        response = client.delete(
            "/api/session",
            headers=[("Origin", ORIGIN), ("X-Studio-Session-Token", token)]
            + [("X-Studio-Session-Token", token)],
        )
        assert response.status_code == 401
        assert client.app.state.session_registry.validate(token)


@pytest.mark.parametrize(
    "path,method,header,expected",
    [
        ("/api/session/bootstrap", "POST", "x-studio-session-bootstrap", 200),
        ("/api/session", "DELETE", "x-studio-session-token", 200),
        ("/api/session/bootstrap", "DELETE", "x-studio-session-bootstrap", 400),
        ("/api/session", "POST", "x-studio-session-token", 400),
        ("/api/session", "GET", "x-studio-session-token", 400),
        ("/api/events", "GET", "x-studio-session-token", 200),
        ("/api/songs", "POST", "x-studio-session-bootstrap", 400),
        ("/api/session/bootstrap", "POST", "authorization", 400),
        ("/api/session/bootstrap", "POST", "x-studio-engine-token", 400),
        (
            "/api/session/bootstrap",
            "POST",
            "x-studio-session-bootstrap, content-type",
            400,
        ),
        (
            "/api/session/bootstrap",
            "POST",
            "x-studio-session-bootstrap,x-studio-session-bootstrap",
            400,
        ),
        ("/api/session/bootstrap", "POST", "x-studio-session-bootstrap,", 400),
        ("/api/session/bootstrap", "POST", "", 400),
        ("/api/session/", "DELETE", "x-studio-session-token", 400),
    ],
)
def test_preflight_path_permission(tmp_path, path, method, header, expected):
    with connection(tmp_path) as client:
        response = client.options(
            path,
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": header,
            },
        )
        assert response.status_code == expected
        assert response.headers["access-control-allow-origin"] == ORIGIN
        assert "access-control-allow-credentials" not in response.headers
        if expected == 200:
            assert response.headers["access-control-allow-methods"] == method
            assert response.headers["access-control-allow-headers"] == header
            assert {
                part.strip().lower() for part in response.headers["vary"].split(",")
            } == {
                "origin",
                "access-control-request-method",
                "access-control-request-headers",
            }


@pytest.mark.parametrize(
    "name,value",
    [
        ("Access-Control-Request-Method", "POST"),
        ("Access-Control-Request-Headers", "x-studio-session-bootstrap"),
    ],
)
def test_preflight_duplicate(tmp_path, name, value):
    with connection(tmp_path) as client:
        response = client.options(
            "/api/session/bootstrap",
            headers=[
                ("Origin", ORIGIN),
                ("Access-Control-Request-Method", "POST"),
                ("Access-Control-Request-Headers", "x-studio-session-bootstrap"),
                (name, value),
            ],
        )
        assert response.status_code == 400


def test_expiry_capacity_and_production_random(tmp_path):
    with connection(tmp_path) as client:
        tokens = {issue(client) for _ in range(32)}
        assert len(tokens) == 32
        assert all(len(token) == 43 for token in tokens)
        response = client.post("/api/session/bootstrap", headers=BOOT)
        assert response.status_code == 503
        assert response.json()["code"] == "SESSION_LIMIT"
    clock = [100.0]

    def factory(owner):
        return LocalSessionRegistry._for_tests(owner, clock=lambda: clock[0])

    with connection(tmp_path / "expiry", session_registry_factory=factory) as client:
        token = issue(client)
        clock[0] += 28800
        assert (
            client.delete(
                "/api/session",
                headers={"Origin": ORIGIN, "X-Studio-Session-Token": token},
            ).status_code
            == 401
        )
        assert issue(client) != token


def test_deleted_owner_rechecked(tmp_path):
    with connection(tmp_path) as client:
        issue(client)
        with client.app.state.db.begin() as database:
            database.execute(update(User).values(deleted_at="2026-10-09T00:00:00Z"))
        response = client.post("/api/session/bootstrap", headers=BOOT)
        assert response.status_code == 503
        assert response.json()["code"] == "SERVICE_UNAVAILABLE"


def test_owner_lookup_unavailable(tmp_path):
    with connection(tmp_path) as client:
        with client.app.state.db.begin() as database:
            database.exec_driver_sql("DROP TABLE user")
        response = client.post("/api/session/bootstrap", headers=BOOT)
        assert response.status_code == 503
        assert response.json()["code"] == "SERVICE_UNAVAILABLE"


def test_factory_and_export_no_runtime_effects(tmp_path, monkeypatch):
    import secrets

    from app import main

    def forbidden(*args, **kwargs):
        pytest.fail("runtime side effect before lifespan")

    monkeypatch.setattr(main, "migrate", forbidden)
    monkeypatch.setattr(main, "create_db_engine", forbidden)
    monkeypatch.setattr(main, "configure_logging", forbidden)
    monkeypatch.setattr(secrets, "token_urlsafe", forbidden)
    settings = config(tmp_path)
    application = create_app(
        settings, queue_runtime_factory=forbidden, session_registry_factory=forbidden
    )
    assert application.state.settings is settings
    schema = application.openapi()
    assert (
        schema["paths"]["/api/session/bootstrap"]["post"]["operationId"]
        == "bootstrap_local_session"
    )
    assert not list(tmp_path.iterdir())


def test_registry_close_on_start_failure(tmp_path):
    records = []

    class FailingQueue(UnrelatedQueue):
        async def start(self):
            raise ValueError("primary")

    def registry_factory(owner):
        registry = LocalSessionRegistry(owner)
        records.append(registry)
        return registry

    application = create_app(
        config(tmp_path),
        queue_runtime_factory=FailingQueue,
        session_registry_factory=registry_factory,
    )
    with pytest.raises(ValueError, match="primary"), TestClient(application):
        pass
    assert len(records) == 1
    assert records[0].active_count == 0
    with pytest.raises(SessionError, match="SERVICE_UNAVAILABLE"):
        records[0].issue(records[0]._owner_id)


def test_registry_close_on_cancellation(tmp_path):
    async def exercise():
        application = create_app(config(tmp_path), queue_runtime_factory=UnrelatedQueue)
        with pytest.raises(asyncio.CancelledError):
            async with application.router.lifespan_context(application):
                registry = application.state.session_registry
                raise asyncio.CancelledError()
        with pytest.raises(SessionError, match="SERVICE_UNAVAILABLE"):
            registry.issue(registry._owner_id)

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "header",
    [
        "\rx-studio-session-bootstrap",
        "x-studio-session-bootstrap\n",
        "\u00a0x-studio-session-bootstrap",
    ],
)
def test_preflight_invalid_syntax(tmp_path, header):
    async def exercise():
        application = create_app(config(tmp_path), queue_runtime_factory=UnrelatedQueue)
        messages = []
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "scheme": "http",
            "method": "OPTIONS",
            "path": "/api/session/bootstrap",
            "raw_path": b"/api/session/bootstrap",
            "query_string": b"",
            "headers": [
                (b"host", b"127.0.0.1:8000"),
                (b"origin", ORIGIN.encode()),
                (b"access-control-request-method", b"POST"),
                (b"access-control-request-headers", header.encode("latin1")),
            ],
            "server": ("127.0.0.1", 8000),
            "client": ("172.18.0.5", 321),
        }

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            messages.append(message)

        await application(scope, receive, send)
        assert messages[0]["status"] == 400

    asyncio.run(exercise())


@pytest.mark.parametrize("state", ["missing", "deleted", "nonunique", "invalid"])
def test_lifespan_binds_only_real_unique_active_user(tmp_path, monkeypatch, state):
    from app import main

    original = main.create_db_engine

    def database_factory(*args, **kwargs):
        engine = original(*args, **kwargs)
        with engine.begin() as database:
            if state == "missing":
                database.exec_driver_sql("DELETE FROM user")
            elif state == "deleted":
                database.exec_driver_sql(
                    "UPDATE user SET deleted_at='2026-10-09T00:00:00Z'"
                )
            elif state == "invalid":
                database.exec_driver_sql("DROP TABLE user")
                database.exec_driver_sql(
                    "CREATE TABLE user (id TEXT PRIMARY KEY, name TEXT, deleted_at TEXT)"
                )
                database.exec_driver_sql(
                    "INSERT INTO user VALUES ('local','local',NULL)"
                )
            else:
                database.exec_driver_sql("DROP TABLE user")
                database.exec_driver_sql(
                    "CREATE TABLE user (id TEXT PRIMARY KEY, name TEXT, deleted_at TEXT)"
                )
                database.exec_driver_sql(
                    "INSERT INTO user VALUES ('01ARZ3NDEKTSV4RRFFQ69G5FAV','local',NULL),('01ARZ3NDEKTSV4RRFFQ69G5FAW','local',NULL)"
                )
        return engine

    monkeypatch.setattr(main, "create_db_engine", database_factory)
    with connection(tmp_path) as client:
        response = client.post("/api/session/bootstrap", headers=BOOT)
        assert response.status_code == 503
        assert response.json()["code"] == "SERVICE_UNAVAILABLE"
        assert client.app.state.session_owner_id is None


@pytest.mark.parametrize(
    "kind",
    [
        "nonempty",
        "continuation",
        "disconnect",
        "timeout",
        "nonascii-token",
        "many-headers",
    ],
)
def test_raw_asgi_bounded_body_and_disconnect(tmp_path, kind):
    async def exercise():
        application = create_app(config(tmp_path), queue_runtime_factory=UnrelatedQueue)
        messages, calls = [], []
        headers = [
            (b"host", b"127.0.0.1:8000"),
            (b"origin", ORIGIN.encode()),
            (b"x-studio-session-bootstrap", b"1"),
        ]
        if kind == "nonascii-token":
            headers[-1] = (b"x-studio-session-bootstrap", b"\xff")
        if kind == "many-headers":
            headers.extend([(b"x-extra", b"x")] * 128)
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "scheme": "http",
            "method": "POST",
            "path": "/api/session/bootstrap",
            "raw_path": b"/api/session/bootstrap",
            "query_string": b"",
            "headers": headers,
            "server": ("127.0.0.1", 8000),
            "client": ("172.18.0.5", 321),
        }

        async def receive():
            calls.append(1)
            if kind == "timeout":
                await asyncio.sleep(10)
            if kind == "disconnect":
                return {"type": "http.disconnect"}
            return {
                "type": "http.request",
                "body": b"x" * 1000000 if kind == "nonempty" else b"",
                "more_body": kind == "continuation",
            }

        async def send(message):
            messages.append(message)

        async with application.router.lifespan_context(application):
            await asyncio.wait_for(application(scope, receive, send), timeout=3)
            assert messages[0]["status"] == (
                401
                if kind == "nonascii-token"
                else 403
                if kind == "many-headers"
                else 422
            )
            assert len(calls) <= 1
            assert application.state.session_registry.active_count == 0

    asyncio.run(exercise())


def test_bootstrap_before_lifespan_is_unavailable(tmp_path):
    application = create_app(config(tmp_path), queue_runtime_factory=UnrelatedQueue)
    client = TestClient(
        application, base_url="http://127.0.0.1:8000", raise_server_exceptions=False
    )
    response = client.post("/api/session/bootstrap", headers=BOOT)
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert response.headers["cache-control"] == "no-store"


def test_native_http_parser_duplicate_host_is_distinct_from_asgi():
    import h11

    parser = h11.Connection(h11.SERVER)
    with pytest.raises(h11.RemoteProtocolError) as error:
        parser.receive_data(
            b"POST /api/session/bootstrap HTTP/1.1\r\nHost: localhost:8000\r\nHost: localhost:8000\r\nContent-Length: 0\r\n\r\n"
        )
        parser.next_event()
    assert error.value.error_status_hint == 400
    parser = h11.Connection(h11.SERVER)
    parser.receive_data(
        b"POST /api/session/bootstrap HTTP/1.1\r\nHost: localhost:8000\r\nOrigin: http://127.0.0.1:3000\r\nOrigin: http://127.0.0.1:3000\r\nContent-Length: 0\r\n\r\n"
    )
    request = parser.next_event()
    assert len([v for k, v in request.headers if k == b"origin"]) == 2


@pytest.mark.parametrize("registry_state", ["missing", "none", "unstarted", "stopped"])
@pytest.mark.parametrize("token", ["wrong", None])
def test_delete_unavailable_registry_before_lifespan(tmp_path, registry_state, token):
    import json

    async def exercise():
        application = create_app(config(tmp_path), queue_runtime_factory=UnrelatedQueue)
        if registry_state == "none":
            application.state.session_registry = None
        elif registry_state == "unstarted":
            application.state.session_registry = LocalSessionRegistry(None)
        elif registry_state == "stopped":
            registry = LocalSessionRegistry("01ARZ3NDEKTSV4RRFFQ69G5FAV")
            registry.close()
            application.state.session_registry = registry
        headers = [
            (b"host", b"127.0.0.1:8000"),
            (b"origin", ORIGIN.encode()),
            (b"content-length", b"0"),
        ]
        if token is not None:
            headers.append((b"x-studio-session-token", token.encode()))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "scheme": "http",
            "method": "DELETE",
            "path": "/api/session",
            "raw_path": b"/api/session",
            "query_string": b"",
            "headers": headers,
            "server": ("127.0.0.1", 8000),
            "client": ("172.18.0.5", 321),
        }
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        error = None
        try:
            await asyncio.wait_for(application(scope, receive, send), timeout=3)
        except AttributeError as caught:
            # ASGI error middleware sends its 500 before rethrowing the cause.
            error = caught
        assert messages[0]["status"] == (503 if token is not None else 401)
        body = b"".join(message.get("body", b"") for message in messages[1:])
        assert json.loads(body)["code"] == (
            "SERVICE_UNAVAILABLE" if token is not None else "SESSION_REQUIRED"
        )
        assert dict(messages[0]["headers"])[b"cache-control"] == b"no-store"
        assert error is None
        assert not list(tmp_path.iterdir())

    asyncio.run(exercise())
