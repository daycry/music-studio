"""Wire /v1 CPU sintético, sin sockets ni secretos del host."""

import asyncio
import hashlib
import importlib.util
import json

import httpx
import pytest
from app.settings import ContractSettings
from engine_contract import JobRequest, LoadRequest

ID = "01K70000000000000000000003"


@pytest.mark.parametrize(
    "operation",
    [
        "health",
        "models",
        "load",
        "unload",
        "estimate",
        "submit",
        "status",
        "events",
        "cancel",
    ],
)
def test_queue_backend_semantic_transport_baseline(operation):
    seen = []

    def handler(req):
        seen.append(
            (req.method, req.url.path, req.headers.get("X-Studio-Engine-Token"))
        )
        if operation == "events":
            return httpx.Response(
                200, headers={"content-type": "application/x-ndjson"}, content=b""
            )
        values = {
            "health": health(),
            "models": [],
            "load": {"model_id": "mock", "mode": "bf16"},
            "unload": {"freed_mb": 0},
            "estimate": {"eta_s": 0, "vram_mb": 0},
            "submit": {"job_id": ID},
            "status": {"job_id": ID, "state": "busy", "seq": 0},
            "cancel": {"job_id": ID},
        }
        return httpx.Response(
            202 if operation == "submit" else 200, json=values[operation]
        )

    async def run():
        async with backend(handler) as client:
            if operation == "events":
                _ = [event async for event in client.events(ID)]
            else:
                args = (
                    [LoadRequest(model_id="mock", mode="bf16")]
                    if operation == "load"
                    else [request()]
                    if operation in {"estimate", "submit"}
                    else [ID]
                    if operation in {"status", "cancel"}
                    else []
                )
                await getattr(client, operation)(*args)

    asyncio.run(run())
    paths = {
        "health": ("GET", "/v1/health"),
        "models": ("GET", "/v1/models"),
        "load": ("POST", "/v1/load"),
        "unload": ("POST", "/v1/unload"),
        "estimate": ("POST", "/v1/estimate"),
        "submit": ("POST", "/v1/jobs"),
        "status": ("GET", "/v1/jobs/" + ID),
        "events": ("GET", "/v1/jobs/" + ID + "/events"),
        "cancel": ("DELETE", "/v1/jobs/" + ID),
    }
    assert seen == [(*paths[operation], "private-test-only")]


def backend(handler, **options):
    assert importlib.util.find_spec("app.queue") is not None, (
        "Falta backend /v1 funcional"
    )
    from app.queue.backends.http import HttpEngineBackend

    settings = ContractSettings(
        engine_token="private-test-only", engines={"mock": "http://engine-mock:8199"}
    )
    return HttpEngineBackend(
        settings, "mock", transport=httpx.MockTransport(handler), **options
    )


def request():
    return JobRequest(
        job_id=ID,
        task="music.instrumental",
        model_id="mock",
        mode="bf16",
        seed=17,
        output_dir="tmp/" + ID,
        timeout_s=60,
    )


def health():
    return {
        "engine_id": "mock",
        "engine_version": "1",
        "image_digest": "unknown",
        "state": "idle",
        "loaded": None,
        "gpu": {"total_mb": 12000, "free_mb": 10000, "cap_mb": 9488},
    }


def test_queue_backend_nine_methods_exact_wire():
    seen = []

    def handle(req):
        assert req.headers["X-Studio-Engine-Token"] == "private-test-only"
        seen.append((req.method, req.url.path))
        bodies = {
            "/v1/health": health(),
            "/v1/models": [],
            "/v1/load": {"model_id": "mock", "mode": "bf16"},
            "/v1/unload": {"freed_mb": 100},
            "/v1/estimate": {"eta_s": 2, "vram_mb": 1000},
            "/v1/jobs": {"job_id": ID},
            "/v1/jobs/" + ID: {"job_id": ID, "state": "busy", "seq": 0},
        }
        if req.method == "DELETE":
            return httpx.Response(200, json={"job_id": ID})
        if req.url.path.endswith("events"):
            assert req.url.params["after"] == "2"
            return httpx.Response(
                200,
                headers={"content-type": "application/x-ndjson"},
                content=json.dumps(
                    {
                        "seq": 3,
                        "ts": "2026-10-07T00:00:00Z",
                        "job_id": ID,
                        "type": "delta",
                        "data": {"text": "canción"},
                    }
                ).encode()
                + b"\n",
            )
        return httpx.Response(
            202 if req.url.path == "/v1/jobs" else 200, json=bodies[req.url.path]
        )

    async def run():
        async with backend(handle) as client:
            assert (await client.health()).engine_id == "mock"
            assert await client.models() == []
            assert (
                await client.load(LoadRequest(model_id="mock", mode="bf16"))
            ).mode == "bf16"
            assert (await client.unload()).freed_mb == 100
            assert (await client.estimate(request())).eta_s == 2
            assert (await client.submit(request())).job_id == ID
            assert (await client.status(ID)).state == "busy"
            assert [e.data["text"] async for e in client.events(ID, 2)] == ["canción"]
            assert (await client.cancel(ID)).job_id == ID

    asyncio.run(run())
    assert len(seen) == 9


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, json={}),
        httpx.Response(404, json={"code": "NOT_FOUND"}),
        httpx.Response(200, json={"job_id": "wrong", "state": "done", "seq": 1}),
        httpx.Response(200, headers={"content-type": "text/plain"}, content=b"{}"),
    ],
)
def test_queue_backend_unknown_is_never_absent(response):
    async def run():
        async with backend(lambda req: response) as client:
            from app.queue.backends.protocol import BackendFailure

            with pytest.raises(BackendFailure):
                await client.status(ID)

    asyncio.run(run())


def test_queue_backend_confirmed_absent_only_native_problem():
    async def run():
        response = httpx.Response(
            404,
            headers={"content-type": "application/problem+json"},
            json={
                "type": "about:blank",
                "title": "NOT_FOUND",
                "status": 404,
                "detail": "Trabajo no encontrado",
                "code": "NOT_FOUND",
                "retryable": False,
            },
        )
        async with backend(lambda req: response) as client:
            from app.queue.backends.protocol import ConfirmedAbsent

            assert isinstance(await client.status(ID), ConfirmedAbsent)

    asyncio.run(run())


def test_queue_backend_stream_incremental_utf8_and_quiet_eof():
    class Chunks(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            value = (
                json.dumps(
                    {
                        "seq": 1,
                        "ts": "2026-10-07T00:00:00Z",
                        "job_id": ID,
                        "type": "delta",
                        "data": {"text": "á"},
                    },
                    ensure_ascii=False,
                ).encode()
                + b"\n"
            )
            for byte in value:
                yield bytes([byte])

        async def aclose(self):
            self.closed = True

    chunks = Chunks()

    async def run():
        async with backend(
            lambda req: httpx.Response(
                200, headers={"content-type": "application/x-ndjson"}, stream=chunks
            )
        ) as client:
            events = [e async for e in client.events(ID)]
            assert [e.type for e in events] == ["delta"]
            assert events[0].data == {"text": "á"}

    asyncio.run(run())
    assert chunks.closed


@pytest.mark.parametrize("content", [b"x" * 513, b"\xff\n", b"{}\n", b"{}"])
def test_queue_backend_bad_stream_is_bounded(content):
    async def run():
        async with backend(
            lambda req: httpx.Response(
                200, headers={"content-type": "application/x-ndjson"}, content=content
            ),
            max_line_bytes=512,
        ) as client:
            from app.queue.backends.protocol import BackendFailure

            with pytest.raises(BackendFailure):
                _ = [e async for e in client.events(ID)]

    asyncio.run(run())


def test_queue_backend_native_mock_asgi_all_nine(tmp_path_factory):

    from app.queue.backends.http import HttpEngineBackend
    from app.queue.backends.protocol import ConfirmedAbsent
    from engine_mock import create_mock_app

    data = tmp_path_factory.mktemp("native")
    settings = ContractSettings(
        engine_token="private-test-only", engines={"mock": "http://engine-mock:8199"}
    )
    app = create_mock_app(token="private-test-only", data_dir=data, stage_delay_ms=0)
    source = data / "tmp" / "input.wav"
    source.parent.mkdir(parents=True, exist_ok=True)
    payload = b"synthetic master"
    source.write_bytes(payload)

    async def run():
        async with (
            app.router.lifespan_context(app),
            HttpEngineBackend(
                settings, "mock", transport=httpx.ASGITransport(app=app)
            ) as client,
        ):
            assert (await client.health()).engine_id == "mock"
            assert (await client.models())[0].provider.type == "local"
            assert isinstance(await client.status(ID), ConfirmedAbsent)
            wire = request().model_copy(
                update={
                    "task": "audio.beats",
                    "mode": "cpu",
                    "params": {"duration_s": 0.01},
                    "inputs": [
                        {
                            "role": "master",
                            "path": "tmp/input.wav",
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "media_type": "audio/wav",
                        }
                    ],
                }
            )
            assert (await client.estimate(wire)).vram_mb == 0
            assert (
                await client.load(LoadRequest(model_id="mock", mode="cpu"))
            ).mode == "cpu"
            assert (await client.submit(wire)).job_id == ID
            events = [e async for e in client.events(ID)]
            assert events[-1].type == "done"
            assert (await client.status(ID)).state == "done"
            assert (await client.cancel(ID)).job_id == ID
            assert (await client.unload()).freed_mb == 0
            assert (await client.health()).loaded is None

    asyncio.run(run())


@pytest.mark.parametrize(
    "method", ["health", "models", "load", "unload", "estimate", "submit", "cancel"]
)
def test_queue_backend_malformed_each_control(method):
    async def run():
        from app.queue.backends.protocol import BackendFailure

        async with backend(
            lambda req: httpx.Response(
                200 if method != "submit" else 202, json={"garbage": 1}
            )
        ) as c:
            args = (
                [LoadRequest(model_id="mock", mode="bf16")]
                if method == "load"
                else [request()]
                if method in {"estimate", "submit"}
                else [ID]
                if method == "cancel"
                else []
            )
            with pytest.raises(BackendFailure):
                await getattr(c, method)(*args)

    asyncio.run(run())


@pytest.mark.parametrize(
    "kind",
    ["redirect", "busy", "model_missing", "timeout", "bad_json", "identity", "auth404"],
)
def test_queue_backend_error_observations(kind):
    async def handler(req):
        if kind == "timeout":
            raise httpx.ReadTimeout("synthetic", request=req)
        if kind == "redirect":
            return httpx.Response(302, headers={"location": "http://external.invalid/"})
        if kind in {"busy", "model_missing", "auth404"}:
            return httpx.Response(
                404 if kind != "busy" else 409,
                headers={"content-type": "application/problem+json"},
                json={
                    "code": {
                        "busy": "BUSY",
                        "model_missing": "MODEL_NOT_FOUND",
                        "auth404": "UNAUTHORIZED",
                    }[kind]
                },
            )
        if kind == "identity":
            return httpx.Response(200, json={"model_id": "other", "mode": "bf16"})
        return httpx.Response(
            200, headers={"content-type": "application/json"}, content=b"not json"
        )

    async def run():
        from app.queue.backends.protocol import BackendFailure

        async with backend(handler) as c:
            with pytest.raises(BackendFailure):
                await c.load(LoadRequest(model_id="mock", mode="bf16"))

    asyncio.run(run())


def test_queue_backend_deadlines_and_id_reject_before_http():
    calls = []

    async def slow(req):
        calls.append(req)
        await asyncio.sleep(1)
        return httpx.Response(200, json=health())

    async def run():
        from app.queue.backends.protocol import BackendFailure

        async with backend(slow, control_s=0.01) as c:
            with pytest.raises(ValueError):
                await c.status("http://other/")
            with pytest.raises(ValueError):
                _ = [e async for e in c.events(ID, -1)]
            assert calls == []
            with pytest.raises(BackendFailure):
                await c.health()
        with pytest.raises(ValueError):
            backend(slow, control_s=0)

    asyncio.run(run())
