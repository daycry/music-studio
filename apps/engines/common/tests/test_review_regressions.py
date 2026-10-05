import json
import os
import threading
import time
from pathlib import Path

import pytest
from engine_common import server
from engine_mock import create_mock_app, descriptor
from fastapi.testclient import TestClient
from test_common import payload

HEADERS = {"X-Studio-Engine-Token": "secret"}


@pytest.fixture
def tmp_path():
    import shutil
    import uuid

    path = server.PROJECT_ROOT / ".cache/dev-cycle/fix03" / uuid.uuid4().hex
    path.mkdir(parents=True)
    yield path
    shutil.rmtree(path)


def terminal(client, request):
    return [
        json.loads(line)
        for line in client.get(f"/v1/jobs/{request['job_id']}/events").text.splitlines()
    ][-1]


def test_timeout_includes_child_model_load(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "PYTHONPATH",
        str(Path(__file__).parent) + os.pathsep + os.environ.get("PYTHONPATH", ""),
    )
    app = server.create_app(
        [descriptor()],
        "regression_adapter:SlowLoadAdapter",
        token="secret",
        data_dir=tmp_path,
        gpu=server.NvmlGpu(),
    )
    monkeypatch.setattr(server.NvmlGpu, "snapshot", lambda self: (12000, 11000))
    with TestClient(app, headers=HEADERS) as client:
        request = {**payload(), "timeout_s": 1}
        started = time.monotonic()
        assert client.post("/v1/jobs", json=request).status_code == 202
        event = terminal(client, request)
        assert event["data"]["code"] == "TIMEOUT"
        assert time.monotonic() - started < 1.8
        assert not app.state.supervisor.alive


def test_health_during_cancel_cleanup_stays_busy(tmp_path, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    original = server.shutil.rmtree

    def cleanup(path):
        entered.set()
        assert release.wait(3)
        original(path)

    app = create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=100)
    with TestClient(app, headers=HEADERS, raise_server_exceptions=False) as client:
        request = payload()
        client.post("/v1/jobs", json=request)
        deadline = time.monotonic() + 3
        while not (tmp_path / request["output_dir"]).exists():
            assert time.monotonic() < deadline
            time.sleep(0.01)
        monkeypatch.setattr(server.shutil, "rmtree", cleanup)
        client.delete(f"/v1/jobs/{request['job_id']}")
        assert entered.wait(3)
        try:
            response = client.get("/v1/health")
            assert response.status_code == 200
            assert response.json()["state"] == "busy"
            assert (
                client.post(
                    "/v1/jobs", json=payload("01ARZ3NDEKTSV4RRFFQ69G5FAW")
                ).status_code
                == 409
            )
        finally:
            release.set()
        assert terminal(client, request)["type"] == "cancelled"


def test_vram_telemetry_is_per_job(tmp_path):
    class Gpu:
        def snapshot(self):
            return 12000, 3000

    app = create_mock_app(
        token="secret", data_dir=tmp_path, stage_delay_ms=0, gpu=Gpu()
    )
    with TestClient(app, headers=HEADERS) as client:
        for index, peak in enumerate((2450, 100)):
            request = payload(
                "01ARZ3NDEKTSV4RRFFQ69G5FA" + str(index), _mock={"vram_peak_mb": peak}
            )
            client.post("/v1/jobs", json=request)
            data = terminal(client, request)["data"]["telemetry"]
            assert data["vram_peak_mb"] == peak
            assert data["spilled"] == (index == 0)
            if index:
                assert data["load_s"] == 0


def test_container_data_mount_is_accepted_without_allowing_host_paths(
    tmp_path, monkeypatch
):
    mount = tmp_path / "container-data"
    outside = tmp_path / "host-private"
    monkeypatch.setattr(server, "PROJECT_ROOT", tmp_path / "installation")
    monkeypatch.setattr(server, "CONTAINER_DATA_ROOT", mount, raising=False)
    monkeypatch.setattr(server, "in_container", lambda: True, raising=False)
    app = create_mock_app(token="secret", data_dir=mount)
    with TestClient(app, headers=HEADERS) as client:
        request = payload()
        client.post("/v1/jobs", json=request)
        assert terminal(client, request)["type"] == "done"
        assert (mount / request["output_dir"]).is_dir()
    with pytest.raises(ValueError, match="dentro del proyecto"):
        create_mock_app(token="secret", data_dir=outside)
    monkeypatch.setenv("STUDIO_DATA_DIR", str(outside))
    with pytest.raises(ValueError, match="dentro del proyecto"):
        create_mock_app(token="secret")
    monkeypatch.delenv("STUDIO_DATA_DIR")
    monkeypatch.setattr(server, "in_container", lambda: False)
    with pytest.raises(ValueError, match="dentro del proyecto"):
        create_mock_app(token="secret", data_dir=mount)


def test_load_does_not_block_async_events_loop(tmp_path, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    app = create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=0)
    with TestClient(app, headers=HEADERS) as client:
        request = payload()
        client.post("/v1/jobs", json=request)
        terminal(client, request)
        original = app.state.supervisor.load

        def slow_load(*args, **kwargs):
            entered.set()
            release.wait(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(app.state.supervisor, "load", slow_load)
        client.post("/v1/unload")
        loader = threading.Thread(
            target=lambda: client.post("/v1/load", json={"model_id": "mock"})
        )
        loader.start()
        assert entered.wait(3)

        async def heartbeat_during_events():
            import asyncio

            response = next(
                route.endpoint for route in app.routes if route.path.endswith("/events")
            )
            heartbeat = asyncio.create_task(asyncio.sleep(0.01))
            started = time.monotonic()
            await response(request["job_id"], after=0)
            await heartbeat
            return time.monotonic() - started

        try:
            elapsed = client.portal.call(heartbeat_during_events)
            assert elapsed < 0.2
            health = client.get("/v1/health")
            assert health.status_code == 200
            assert health.json()["state"] == "loading"
            assert client.post("/v1/load", json={"model_id": "mock"}).status_code == 409
            assert client.post("/v1/unload").status_code == 409
            assert (
                client.post(
                    "/v1/jobs", json=payload("01ARZ3NDEKTSV4RRFFQ69G5FAW")
                ).status_code
                == 409
            )
        finally:
            release.set()
            loader.join(3)


def test_health_reads_loaded_snapshot_once(tmp_path, monkeypatch):
    class ChangingSupervisor:
        reads = 0

        def __init__(self, *args):
            pass

        @property
        def loaded(self):
            self.reads += 1
            return ("mock", "cpu") if self.reads == 1 else None

        def unload(self):
            pass

    monkeypatch.setattr(server, "ProcessSupervisor", ChangingSupervisor)
    app = create_mock_app(token="secret", data_dir=tmp_path)
    with TestClient(app, headers=HEADERS, raise_server_exceptions=False) as client:
        response = client.get("/v1/health")
        assert response.status_code == 200
        assert response.json()["loaded"] == {"model_id": "mock", "mode": "cpu"}


def test_cancel_during_implicit_load_has_one_terminal(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "PYTHONPATH",
        str(Path(__file__).parent) + os.pathsep + os.environ.get("PYTHONPATH", ""),
    )
    from engine_common import CpuGpu

    app = server.create_app(
        [descriptor()],
        "regression_adapter:SlowLoadAdapter",
        token="secret",
        data_dir=tmp_path,
        gpu=CpuGpu(),
    )
    with TestClient(app, headers=HEADERS) as client:
        request = payload()
        assert client.post("/v1/jobs", json=request).status_code == 202
        assert client.delete(f"/v1/jobs/{request['job_id']}").status_code == 200
        events = [
            json.loads(line)
            for line in client.get(
                f"/v1/jobs/{request['job_id']}/events"
            ).text.splitlines()
        ]
        assert [
            event["type"] for event in events if event["type"] in server.TERMINALS
        ] == ["cancelled"]
        assert not (tmp_path / request["output_dir"]).exists()
        assert client.get("/v1/health").json()["state"] == "idle"


def test_submit_input_validation_does_not_block_async_events_loop(
    tmp_path, monkeypatch
):
    import asyncio
    import hashlib

    source = tmp_path / "slow-input.wav"
    source.write_bytes(b"pcm")
    entered = threading.Event()
    original_open = Path.open

    def slow_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path == source and mode == "rb":
            entered.set()
            time.sleep(0.3)
        return original_open(path, *args, **kwargs)

    app = create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=0)
    with TestClient(app, headers=HEADERS) as client:
        previous = {**payload(), "task": "text.generate"}
        assert client.post("/v1/jobs", json=previous).status_code == 202
        assert terminal(client, previous)["type"] == "done"
        incoming = {
            **payload("01ARZ3NDEKTSV4RRFFQ69G5FAW"),
            "task": "text.generate",
            "inputs": [
                {
                    "role": "source",
                    "path": source.name,
                    "sha256": hashlib.sha256(b"pcm").hexdigest(),
                    "media_type": "audio/wav",
                }
            ],
        }
        monkeypatch.setattr(Path, "open", slow_open)
        responses = []
        submitter = threading.Thread(
            target=lambda: responses.append(
                client.post("/v1/jobs", json=incoming).status_code
            )
        )
        submitter.start()

        async def heartbeat_during_events():
            endpoint = next(
                route.endpoint for route in app.routes if route.path.endswith("/events")
            )
            heartbeat = asyncio.create_task(asyncio.sleep(0.01))
            started = time.monotonic()
            await endpoint(previous["job_id"], after=0)
            await heartbeat
            return time.monotonic() - started

        try:
            assert entered.wait(3)
            elapsed = client.portal.call(heartbeat_during_events)
            assert elapsed < 0.2, f"heartbeat {elapsed:.3f} s >= 0.2 s"
        finally:
            submitter.join(3)
        assert responses == [202]
        assert terminal(client, incoming)["type"] == "done"


def test_submit_reserves_engine_while_validating_inputs(tmp_path, monkeypatch):
    import hashlib

    source = tmp_path / "slow-input.wav"
    source.write_bytes(b"pcm")
    entered = threading.Event()
    release = threading.Event()
    original_open = Path.open

    def blocked_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path == source and mode == "rb":
            entered.set()
            assert release.wait(5)
        return original_open(path, *args, **kwargs)

    app = create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=0)
    with TestClient(app, headers=HEADERS) as client:
        previous = {**payload(), "task": "text.generate"}
        assert client.post("/v1/jobs", json=previous).status_code == 202
        assert terminal(client, previous)["type"] == "done"
        incoming = {
            **payload("01ARZ3NDEKTSV4RRFFQ69G5FAW"),
            "task": "text.generate",
            "inputs": [
                {
                    "role": "source",
                    "path": source.name,
                    "sha256": hashlib.sha256(b"pcm").hexdigest(),
                    "media_type": "audio/wav",
                }
            ],
        }
        monkeypatch.setattr(Path, "open", blocked_open)
        responses = []
        submitter = threading.Thread(
            target=lambda: responses.append(
                client.post("/v1/jobs", json=incoming).status_code
            )
        )
        submitter.start()
        try:
            assert entered.wait(3)
            assert client.get("/v1/health").json()["state"] == "loading"
            assert terminal(client, previous)["type"] == "done"
            assert client.post("/v1/load", json={"model_id": "mock"}).status_code == 409
            assert client.post("/v1/unload").status_code == 409
            assert client.post("/v1/jobs", json=incoming).status_code == 409
            assert client.post("/v1/jobs", json=payload()).status_code == 202
            assert (
                client.post(
                    "/v1/jobs", json=payload("01ARZ3NDEKTSV4RRFFQ69G5FAX")
                ).status_code
                == 409
            )
        finally:
            release.set()
            submitter.join(3)
        assert responses == [202]
        assert terminal(client, incoming)["type"] == "done"
        assert client.post("/v1/jobs", json=incoming).status_code == 202


@pytest.mark.parametrize("failure", ["hash", "missing", "io"])
def test_submit_validation_failure_releases_reservation(tmp_path, monkeypatch, failure):
    import hashlib

    source = tmp_path / "input.wav"
    if failure != "missing":
        source.write_bytes(b"pcm")
    original_open = Path.open

    def failed_open(path, *args, **kwargs):
        if path == source:
            raise OSError("Fallo de E/S simulado")
        return original_open(path, *args, **kwargs)

    app = create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=0)
    with TestClient(app, headers=HEADERS, raise_server_exceptions=False) as client:
        request = {
            **payload(),
            "task": "text.generate",
            "inputs": [
                {
                    "role": "source",
                    "path": source.name,
                    "sha256": "0" * 64
                    if failure == "hash"
                    else hashlib.sha256(b"pcm").hexdigest(),
                    "media_type": "audio/wav",
                }
            ],
        }
        if failure == "io":
            monkeypatch.setattr(Path, "open", failed_open)
        assert client.post("/v1/jobs", json=request).status_code == (
            500 if failure == "io" else 422
        )
        assert client.get("/v1/health").json()["state"] == "idle"
        assert client.get(f"/v1/jobs/{request['job_id']}").status_code == 404
        monkeypatch.setattr(Path, "open", original_open)
        source.write_bytes(b"pcm")
        request["inputs"][0]["sha256"] = hashlib.sha256(b"pcm").hexdigest()
        assert client.post("/v1/load", json={"model_id": "mock"}).status_code == 200
        assert client.post("/v1/jobs", json=request).status_code == 202
        assert terminal(client, request)["type"] == "done"
