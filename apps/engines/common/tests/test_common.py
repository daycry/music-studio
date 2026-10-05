import engine_common as common
import pytest


@pytest.mark.parametrize("endpoint", ["/v1/estimate", "/v1/jobs"])
def test_native_preflight_rejection_precedes_loading_and_queue(
    tmp_path, endpoint, monkeypatch
):
    from engine_contract import ModelDescriptor
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    with TestClient(create_mock_app(token="secret")) as old:
        old.headers["X-Studio-Engine-Token"] = "secret"
        descriptor = ModelDescriptor.model_validate(old.get("/v1/models").json()[0])
    called = []

    def reject(request):
        called.append(request["params"])
        raise common.EngineError("INVALID_PARAMS", "Entrada excede presupuesto nativo")

    app = common.create_app(
        [descriptor],
        "engine_common.mock:MockAdapter",
        token="secret",
        data_dir=tmp_path,
        gpu=common.CpuGpu(),
        preflight=reject,
    )
    monkeypatch.setattr(
        app.state.supervisor,
        "load",
        lambda *a, **k: pytest.fail("load after rejection"),
    )
    with TestClient(app) as client:
        client.headers["X-Studio-Engine-Token"] = "secret"
        response = client.post(endpoint, json=payload())
        assert response.status_code == 422
        assert called == [payload()["params"]]
        assert client.get("/v1/health").json()["loaded"] is None
        assert client.get("/v1/jobs/" + payload()["job_id"]).status_code == 404


def test_endpoints():
    assert hasattr(common, "create_app"), "Servidor /v1 todavía no implementado"
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    with TestClient(create_mock_app(token="secret")) as client:
        assert client.get("/v1/health").status_code == 401
        client.headers["X-Studio-Engine-Token"] = "secret"
        assert client.get("/v1/health").json()["contract_version"] == "1"
        assert client.get("/v1/models").json()[0]["id"] == "mock"
        assert (
            client.post(
                "/v1/load", json={"model_id": "mock", "mode": "cpu"}
            ).status_code
            == 200
        )
        assert client.post("/v1/unload").status_code == 200


def test_child_process():
    assert hasattr(common, "ProcessSupervisor"), (
        "Supervisor hijo todavía no implementado"
    )
    supervisor = common.ProcessSupervisor()
    supervisor.load("mock", "cpu", 1024, 4096)
    assert supervisor.pid and supervisor.pid != __import__("os").getpid()
    assert supervisor.alive
    supervisor.unload()
    assert not supervisor.alive


def test_vram_guard():
    assert hasattr(common, "VramGuard"), "VramGuard todavía no implementado"
    guard = common.VramGuard(total_mb=12000, free_mb=3000, margin_mb=512)
    assert guard.cap_mb == 2488
    guard.observe(2450)
    assert guard.spilled and guard.peak_mb == 2450
    with pytest.raises(common.EngineError, match="VRAM_EXCEEDED"):
        guard.observe(2500)


def test_cancel_and_terminal(tmp_path):
    assert hasattr(common, "CancelToken"), (
        "Cancelación cooperativa todavía no implementada"
    )

    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    payload = {
        "job_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "task": "music.song",
        "model_id": "mock",
        "inputs": [],
        "params": {"duration_s": 0.1},
        "output_dir": "tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV/",
        "timeout_s": 30,
    }
    with TestClient(
        create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=100)
    ) as client:
        client.headers["X-Studio-Engine-Token"] = "secret"
        assert client.post("/v1/jobs", json=payload).status_code == 202
        assert client.delete("/v1/jobs/" + payload["job_id"]).status_code == 200
        events = [
            __import__("json").loads(line)
            for line in client.get(
                "/v1/jobs/" + payload["job_id"] + "/events"
            ).text.splitlines()
        ]
        assert (
            len([e for e in events if e["type"] in {"done", "error", "cancelled"}]) == 1
        )
        assert events[-1]["type"] == "cancelled"
        assert not (tmp_path / payload["output_dir"]).exists()


def payload(job_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", **params):
    return {
        "job_id": job_id,
        "task": "music.song",
        "model_id": "mock",
        "params": {"duration_s": 0.01, **params},
        "output_dir": f"tmp/{job_id}/",
        "timeout_s": 30,
    }


def test_job_replay_busy_and_validation(tmp_path):
    import json

    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    with TestClient(
        create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=100)
    ) as client:
        client.headers["X-Studio-Engine-Token"] = "secret"
        invalid = payload(duration_s=-1)
        assert client.post("/v1/jobs", json=invalid).json()["code"] == "INVALID_PARAMS"
        invalid["model_id"] = "missing"
        assert (
            client.post("/v1/estimate", json=invalid).json()["code"]
            == "MODEL_NOT_FOUND"
        )
        request = payload()
        assert client.post("/v1/estimate", json=request).status_code == 200
        assert client.post("/v1/jobs", json=request).status_code == 202
        assert client.post("/v1/jobs", json=request).status_code == 202
        assert (
            client.post("/v1/jobs", json=payload("01ARZ3NDEKTSV4RRFFQ69G5FAW")).json()[
                "code"
            ]
            == "BUSY"
        )
        assert client.post("/v1/unload").status_code == 409
        url = f"/v1/jobs/{request['job_id']}"
        events = [
            json.loads(line) for line in client.get(url + "/events").text.splitlines()
        ]
        assert events[-1]["type"] == "done"
        assert events[0]["data"]["stage"] == "loading_model"
        assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
        replay = [
            json.loads(line)
            for line in client.get(url + "/events?after=2").text.splitlines()
        ]
        assert replay == events[2:]
        assert client.get(url).json()["state"] == "done"
        assert client.get("/v1/jobs/missing").status_code == 404


def test_gpu_simulated_error_and_telemetry(tmp_path):
    import json

    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    class SimulatedGpu:
        def snapshot(self):
            return 12000, 3000

    with TestClient(
        create_mock_app(
            token="secret", data_dir=tmp_path, stage_delay_ms=0, gpu=SimulatedGpu()
        )
    ) as client:
        client.headers["X-Studio-Engine-Token"] = "secret"
        for index, peak in enumerate((2450, 2500)):
            request = payload(
                "01ARZ3NDEKTSV4RRFFQ69G5FA" + str(index), _mock={"vram_peak_mb": peak}
            )
            assert client.post("/v1/jobs", json=request).status_code == 202
            events = [
                json.loads(line)
                for line in client.get(
                    f"/v1/jobs/{request['job_id']}/events"
                ).text.splitlines()
            ]
            terminal = events[-1]
            assert (
                len([e for e in events if e["type"] in {"done", "error", "cancelled"}])
                == 1
            )
            if index == 0:
                telemetry = terminal["data"]["telemetry"]
                assert telemetry["vram_peak_mb"] == 2450
                assert telemetry["vram_cap_mb"] == 2488 and telemetry["spilled"]
            else:
                assert terminal["data"]["code"] == "VRAM_EXCEEDED"
                assert not (tmp_path / request["output_dir"]).exists()


def test_nvml_reads_memory_and_shuts_down(monkeypatch):
    import sys
    from types import SimpleNamespace

    calls = []
    fake = SimpleNamespace(
        nvmlInit=lambda: calls.append("init"),
        nvmlShutdown=lambda: calls.append("shutdown"),
        nvmlDeviceGetHandleByIndex=lambda index: index,
        nvmlDeviceGetMemoryInfo=lambda handle: SimpleNamespace(
            total=12000 * 1024**2, free=3000 * 1024**2
        ),
        NVMLError=RuntimeError,
    )
    monkeypatch.setitem(sys.modules, "pynvml", fake)
    assert common.NvmlGpu().snapshot() == (12000, 3000)
    assert calls == ["init", "shutdown"]


def test_replacement_releases_before_vram_measurement(monkeypatch):
    from engine_common import server
    from engine_mock import descriptor
    from fastapi.testclient import TestClient

    calls = []

    class Supervisor:
        alive = True
        loaded = ("old", "cpu")

        def __init__(self, *args):
            pass

        def unload(self):
            calls.append("unload")
            self.alive = False
            self.loaded = None

        def load(self, model_id, mode, cap_mb, total_mb):
            calls.append("load")
            self.alive = True
            self.loaded = (model_id, mode)

    class Gpu:
        def snapshot(self):
            calls.append("snapshot")
            return 12000, 11000

    monkeypatch.setattr(server, "ProcessSupervisor", Supervisor)
    app = server.create_app([descriptor()], "unused", token="secret", gpu=Gpu())
    with TestClient(app) as client:
        client.headers["X-Studio-Engine-Token"] = "secret"
        assert client.post("/v1/load", json={"model_id": "mock"}).status_code == 200
        assert calls[:3] == ["unload", "snapshot", "load"]


def test_worker_result_errors_and_cancel(tmp_path, monkeypatch):
    from engine_common import worker
    from engine_mock import MockAdapter

    messages = []
    monkeypatch.setattr(worker, "send", messages.append)
    token = common.CancelToken()
    worker.run(MockAdapter(stage_delay_ms=0), payload(), tmp_path, token)
    assert messages[-1]["kind"] == "result"
    worker.run(
        MockAdapter(stage_delay_ms=0),
        payload(style="@mock:fail=PROVIDER_ERROR @mock:retryable"),
        tmp_path,
        token,
    )
    assert messages[-1]["code"] == "PROVIDER_ERROR" and messages[-1]["retryable"]
    token.cancel()
    worker.run(MockAdapter(stage_delay_ms=0), payload(), tmp_path, token)
    assert messages[-1]["code"] == "CANCELLED"

    class Broken:
        def generate(self, *args):
            raise RuntimeError("private information")

    worker.run(Broken(), payload(), tmp_path, common.CancelToken())
    assert messages[-1]["code"] == "INTERNAL"
    assert "private" not in messages[-1]["message"]


def test_worker_load_ipc(monkeypatch):
    import io
    import json

    from engine_common import worker

    messages = []
    commands = [
        {
            "command": "load",
            "factory": "engine_mock:MockAdapter",
            "options": {"stage_delay_ms": 0},
            "model_id": model,
            "mode": "cpu",
            "cap_mb": 0,
            "total_mb": 0,
        }
        for model in ("mock", "missing")
    ]
    commands.append({**commands[0], "factory": "engine_mock:MissingAdapter"})
    monkeypatch.setattr(
        worker.sys, "stdin", io.StringIO("\n".join(json.dumps(c) for c in commands))
    )
    monkeypatch.setattr(worker, "send", messages.append)
    worker.main()
    assert messages[0] == {"kind": "loaded"}
    assert messages[1]["code"] == "MODEL_NOT_FOUND"
    assert messages[2]["code"] == "INTERNAL"


def test_http_fail_once_is_retryable_and_recovers(tmp_path):
    import json

    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    with TestClient(
        create_mock_app(token="secret", data_dir=tmp_path, stage_delay_ms=0)
    ) as client:
        client.headers["X-Studio-Engine-Token"] = "secret"
        for index in (0, 1):
            request = payload(
                "01ARZ3NDEKTSV4RRFFQ69G5FA" + str(index),
                style="same prompt @mock:fail_once=PROVIDER_ERROR @mock:retryable",
            )
            assert client.post("/v1/jobs", json=request).status_code == 202
            events = [
                json.loads(line)
                for line in client.get(
                    f"/v1/jobs/{request['job_id']}/events"
                ).text.splitlines()
            ]
            if index == 0:
                assert events[-1]["type"] == "error"
                assert events[-1]["data"]["retryable"]
            else:
                assert events[-1]["type"] == "done"
