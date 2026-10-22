import app
import pytest
from fastapi.testclient import TestClient
from test_settings import settings


def client(tmp_path):
    factory = getattr(app, "create_app", None)
    assert callable(factory), "HTTP server security behavior is absent"
    config = settings(data_dir=tmp_path)
    return TestClient(
        factory(config), base_url="http://127.0.0.1:8000", raise_server_exceptions=False
    )


def test_security_host_rebinding(tmp_path):
    response = client(tmp_path).get("/health", headers={"Host": "evil.test:8000"})
    assert response.status_code == 403
    assert response.json()["code"] == "INVALID_HOST"


def test_security_origin_before_routing(tmp_path):
    response = client(tmp_path).post(
        "/api/songs", headers={"Origin": "http://evil.test"}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN_ORIGIN"


def test_security_sse_cross_site(tmp_path):
    response = client(tmp_path).get(
        "/api/events", headers={"Origin": "http://evil.test"}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN_ORIGIN"


def test_security_cors_preflight(tmp_path):
    response = client(tmp_path).options(
        "/api/songs",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_security_cors_preflight_allows_session_token_for_api(tmp_path):
    response = client(tmp_path).options(
        "/api/system/unload",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-studio-session-token",
        },
    )
    assert response.status_code == 200
    assert "x-studio-session-token" in {
        part.strip().lower()
        for part in response.headers["access-control-allow-headers"].split(",")
    }


def test_errors_not_found(tmp_path):
    response = client(tmp_path).get("/missing?secret=synthetic-private")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "NOT_FOUND"
    assert "synthetic-private" not in response.text


def test_errors_validation_redaction(tmp_path):
    test_client = client(tmp_path)

    @test_client.app.get("/test-validation")
    def validation(number: int):
        return {"number": number}

    response = test_client.get("/test-validation?number=synthetic-private")
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "INVALID_PARAMS"
    assert "synthetic-private" not in response.text


def test_errors_internal_redaction(tmp_path):
    test_client = client(tmp_path)

    @test_client.app.get("/test-error")
    def failure():
        raise RuntimeError("synthetic-secret /private/path lyrics-private")

    response = test_client.get("/test-error")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL"
    assert "synthetic-secret" not in response.text


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_security_missing_origin(tmp_path, method):
    assert client(tmp_path).request(method, "/missing").status_code == 403


@pytest.mark.parametrize(
    "host", ["127.0.0.1:8000", "localhost:8000", "server:8000", "server"]
)
def test_security_allowed_hosts(tmp_path, host):
    response = client(tmp_path).get("/health", headers={"Host": host})
    assert response.status_code == 200
    assert response.json() == {"status": "running", "process": "server"}


@pytest.mark.parametrize(
    "host",
    [
        "localhost:8001",
        "127.0.0.1:8000.evil.test",
        "127.0.0.1",
        "localhost",
        "server.evil.test:8000",
        "192.168.1.5:8000",
        "127.0.0.1:8000@evil.test",
    ],
)
def test_security_reject_other_authorities(tmp_path, host):
    assert client(tmp_path).get("/health", headers={"Host": host}).status_code == 403


@pytest.mark.parametrize(
    "origin",
    [
        "null",
        "http://127.0.0.1:3000.evil.test",
        "http://127.0.0.1:3001",
        "http://localhost:3000",
        "http://127.0.0.1:3000/",
    ],
)
def test_security_origin_exact(tmp_path, origin):
    assert (
        client(tmp_path).post("/api/songs", headers={"Origin": origin}).status_code
        == 403
    )


def test_security_duplicate_headers(tmp_path):
    connection = client(tmp_path)
    assert (
        connection.get(
            "/health", headers=[("Host", "127.0.0.1:8000"), ("Host", "evil.test")]
        ).status_code
        == 403
    )
    assert (
        connection.post(
            "/api/songs",
            headers=[
                ("Origin", "http://127.0.0.1:3000"),
                ("Origin", "http://evil.test"),
            ],
        ).status_code
        == 403
    )


@pytest.mark.parametrize("route", ["/api/events/", "/api/%65vents", "/missing"])
def test_security_sse_path_and_accept(tmp_path, route):
    assert (
        client(tmp_path).get(route, headers={"Accept": "text/event-stream"}).status_code
        == 403
    )


def test_security_sse_allowed_origin_without_fake_endpoint(tmp_path):
    response = client(tmp_path).get(
        "/api/events", headers={"Origin": "http://127.0.0.1:3000"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "SESSION_REQUIRED"


@pytest.mark.parametrize(
    "method,headers",
    [
        ("TRACE", "content-type"),
        ("POST", "x-studio-engine-token"),
        ("POST", "authorization"),
    ],
)
def test_security_preflight_closed(tmp_path, method, headers):
    response = client(tmp_path).options(
        "/api/songs",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"


def test_security_preflight_evil(tmp_path):
    response = client(tmp_path).options(
        "/api/songs",
        headers={"Origin": "http://evil.test", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_security_lifespan(tmp_path):
    with client(tmp_path) as connection:
        assert connection.get("/health").status_code == 200
        assert connection.head("/missing").status_code == 404
        assert (
            connection.get(
                "/health", headers={"Origin": "http://evil.test"}
            ).status_code
            == 403
        )


def test_errors_internal_has_cors(tmp_path):
    connection = client(tmp_path)

    @connection.app.get("/test-error")
    def failure():
        raise ValueError("synthetic-private")

    response = connection.get(
        "/test-error", headers={"Origin": "http://127.0.0.1:3000"}
    )
    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_errors_method_not_allowed(tmp_path):
    response = client(tmp_path).post(
        "/health", headers={"Origin": "http://127.0.0.1:3000"}
    )
    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"
    assert response.headers["allow"] == "GET"


@pytest.mark.parametrize("method", ["GET", "HEAD"])
@pytest.mark.parametrize(
    "origin", ["http://evil.test", "null", "", "http://127.0.0.1:3000/"]
)
def test_security_explicit_invalid_read_origin(tmp_path, method, origin):
    response = client(tmp_path).request(method, "/health", headers={"Origin": origin})
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_security_duplicate_read_origins(tmp_path, method):
    response = client(tmp_path).request(
        method, "/health", headers=[("Origin", "http://127.0.0.1:3000")] * 2
    )
    assert response.status_code == 403


@pytest.mark.parametrize("method", ["GET", "HEAD"])
@pytest.mark.parametrize("headers", [{}, {"Origin": "http://127.0.0.1:3000"}])
def test_security_ordinary_reads(tmp_path, method, headers):
    response = client(tmp_path).request(method, "/missing", headers=headers)
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert ("access-control-allow-origin" in response.headers) == bool(headers)


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_security_sse_requires_origin_on_reads(tmp_path, method):
    response = client(tmp_path).request(
        method, "/health", headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "bad_value", ["Basic secret\r\nX-Injected: yes", "secret\x00", "secret\u2603", 123]
)
def test_errors_safe_protocol_headers(tmp_path, bad_value):
    from starlette.exceptions import HTTPException

    connection = client(tmp_path)

    @connection.app.get("/protocol-error")
    def failure():
        raise HTTPException(
            401,
            detail="synthetic-private",
            headers={
                "WWW-Authenticate": bad_value,
                "Content-Type": "text/html",
                "X-Private": "synthetic-private",
            },
        )

    response = connection.get("/protocol-error")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert "www-authenticate" not in response.headers
    assert "x-private" not in response.headers
    assert "synthetic-private" not in response.text


def test_errors_preserve_authenticate(tmp_path):
    from starlette.exceptions import HTTPException

    connection = client(tmp_path)

    @connection.app.get("/protocol-error")
    def failure():
        raise HTTPException(
            401,
            headers={
                "wWw-AuThEnTiCaTe": 'Basic realm="studio"',
                "Content-Type": "text/html",
            },
        )

    response = connection.get("/protocol-error")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="studio"'
    assert response.headers["content-type"] == "application/problem+json"
