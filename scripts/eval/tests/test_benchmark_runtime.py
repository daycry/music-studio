"""Reanudar sin duplicar trabajos y limpiar exclusivamente dueÃ±o exacto."""

import pytest


def test_resume_queries_existing_job_without_resubmitting(harness_module):
    runtime = harness_module("benchmark_runtime")
    assert callable(getattr(runtime, "resume_action", None)), "Falta recuperaciÃ³n real"
    for state in ("loading", "busy", "done", "error", "cancelled"):
        assert runtime.resume_action(
            {"job_id": "j"}, {"job_id": "j", "state": state}
        ) in {"observe", "terminal"}
    with pytest.raises(ValueError):
        runtime.resume_action({"job_id": "j"}, {"job_id": "other", "state": "busy"})
    assert runtime.resume_action(None, None) == "submit_new"
    assert runtime.resume_action({"job_id": "j"}, None) == "missing_existing"


def test_container_cleanup_requires_id_and_all_labels(harness_module):
    runtime = harness_module("benchmark_runtime")
    assert callable(getattr(runtime, "assert_owner", None)), "Falta ownership exacto"
    receipt = {
        "container_id": "exact",
        "session_id": "s",
        "plan_sha256": "p",
        "owner": "o",
    }
    inspection = {
        "Id": "exact",
        "Config": {
            "Labels": {
                "studio.t09.session": "s",
                "studio.t09.plan": "p",
                "studio.t09.owner": "o",
            }
        },
    }
    runtime.assert_owner(receipt, inspection)
    with pytest.raises(ValueError):
        runtime.assert_owner(receipt, {**inspection, "Id": "other"})
    with pytest.raises(ValueError):
        runtime.assert_owner(receipt, {"Id": "exact", "Config": {"Labels": {}}})


def test_runtime_uses_loopback_no_global_teardown_and_secret_env(harness_module):
    runtime = harness_module("benchmark_runtime")
    assert callable(getattr(runtime, "container_command", None)), "Falta backend propio"
    plan = {"session_id": "S", "plan_sha256": "p", "image_id": "sha256:image"}
    config = {"checkpoint": "acestep-v15-base", "lm": "acestep-5Hz-lm-0.6B"}
    command, env = runtime.container_command(
        plan, config, "container_copy", owner="o", port=8149
    )
    assert "127.0.0.1:8149:8101" in command
    assert "--env" in command and "STUDIO_ENGINE_TOKEN" in command
    assert env["STUDIO_ENGINE_TOKEN"] not in " ".join(command)
    assert not any(
        v in command for v in ("--privileged", "--network=host", "8101:8101", "prune")
    )
    assert "/studio/.cache/benchmark/S/models" in command


def test_storage_copies_locked_safe_files_and_preserves_layout(
    harness_module, tmp_path
):
    storage = harness_module("benchmark_storage")
    assert callable(getattr(storage, "prepare_storage", None)), "Falta copia verificada"
    import hashlib
    import json

    source = tmp_path / "source"
    target = tmp_path / "target"
    blob = b"safetensor fixture"
    directory = source / "ace-step-1.5/checkpoints/dit"
    directory.mkdir(parents=True)
    (directory / "safe.safetensors").write_bytes(blob)
    component = {
        "id": "dit",
        "dest_subdir": "dit",
        "files": [
            {
                "path": "old.pt",
                "format": "pickle",
                "converted": {
                    "dest": "safe.safetensors",
                    "bytes": len(blob),
                    "sha256": hashlib.sha256(blob).hexdigest(),
                },
            }
        ],
    }
    (source / "models.lock.json").write_text(
        json.dumps({"models": {"ace-step-1.5": {"components": [component]}}})
    )
    receipt = storage.prepare_storage(source, target, ["dit"])
    assert (
        target / "ace-step-1.5/checkpoints/dit/safe.safetensors"
    ).read_bytes() == blob
    assert not (target / "ace-step-1.5/checkpoints/dit/old.pt").exists()
    assert receipt["source_lock_sha256"] == receipt["destination_lock_sha256"]
    (directory / "safe.safetensors").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="mismatch"):
        storage.prepare_storage(source, tmp_path / "other", ["dit"])


def test_gpu_lease_refuses_live_or_other_owner_and_ollama_restores_identity(
    harness_module, tmp_path, monkeypatch
):
    runtime = harness_module("benchmark_runtime")
    assert callable(getattr(runtime, "GpuLease", None)), (
        "Falta lease GPU de dueÃ±o exacto"
    )
    owner = {"owner": "o", "session_id": "s", "plan_sha256": "p"}
    path = tmp_path / "gpu.lock"
    lease = runtime.GpuLease(path, owner)
    lease.acquire()
    with pytest.raises(ValueError):
        runtime.GpuLease(path, {**owner, "owner": "other"}).acquire(resume=True)
    monkeypatch.setattr(runtime, "pid_alive", lambda pid: True)
    with pytest.raises(ValueError):
        lease.acquire(resume=True)
    monkeypatch.setattr(runtime, "pid_alive", lambda pid: False)
    lease.acquire(resume=True)
    lease.release()
    assert not path.exists()
    calls = []
    state = [
        "NAME ID SIZE\nmimo:9b-q5 x 8GB",
        "NAME ID SIZE",
        "NAME ID SIZE",
        "NAME ID SIZE\nmimo:9b-q5 x 8GB",
    ]
    from types import SimpleNamespace

    def command(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(
            returncode=0, stdout=state.pop(0) if "ps" in args else ""
        )

    ollama = runtime.OllamaState(execute=command)
    before = ollama.snapshot()
    ollama.discharge(before)
    assert ollama.restore(before)["models"] == ["mimo:9b-q5"]
    assert any(args[-2:] == ["stop", "mimo:9b-q5"] for args in calls)
    assert not any("rm" in args or "kill" in args for args in calls)


def test_resume_lease_can_resume_again_after_dead_owner_preserving_old_claim(
    harness_module, tmp_path, monkeypatch
):
    runtime = harness_module("benchmark_runtime")
    owner = {"owner": "o", "session_id": "s", "plan_sha256": "p"}
    lease = runtime.GpuLease(tmp_path / "gpu.lock", owner)
    lease.acquire()
    monkeypatch.setattr(runtime, "pid_alive", lambda pid: False)
    lease.acquire(resume=True)
    lease.acquire(resume=True)
    assert list(tmp_path.glob("gpu.resume-claim.previous-*"))
    lease.release()


def test_copy_refuses_low_space_instead_of_partial_or_external_storage(
    harness_module, tmp_path, monkeypatch
):
    storage = harness_module("benchmark_storage")
    from types import SimpleNamespace

    assert callable(getattr(storage, "storage_capacity", None)), (
        "Falta puerta de espacio de copia"
    )
    monkeypatch.setattr(
        storage.shutil, "disk_usage", lambda path: SimpleNamespace(free=10)
    )
    with pytest.raises(ValueError, match="insufficient_container_storage"):
        storage.storage_capacity(tmp_path / "new/models", 100)


@pytest.mark.parametrize("complete", [True, False])
def test_real_http_response_continuous_events_keep_sampling_and_deadline(
    harness_module, tmp_path, monkeypatch, complete
):
    import http.client
    import io
    import itertools
    import json
    import time
    import urllib.parse

    runtime = harness_module("benchmark_runtime")
    runner = harness_module("benchmark_runner")
    afters = []
    responses = []
    sampled = []
    last = 13 if complete else 100

    class Body(io.BytesIO):
        def readline(self, size=-1):
            if self.tell() >= self.body_start:
                time.sleep(0.012)
            return super().readline(size)

        def read1(self, size=-1):
            time.sleep(0.012)
            return super().readline(size)

    class Sock:
        def __init__(self, content):
            self.content = content

        def makefile(self, *args, **kwargs):
            return self.content

    def transport(request, **kwargs):
        after = int(
            urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)[
                "after"
            ][0]
        )
        afters.append(after)
        headers = b"HTTP/1.1 200 OK\r\nContent-Type: application/x-ndjson\r\nConnection: close\r\n\r\n"
        records = [
            {
                "seq": i,
                "job_id": "J",
                "type": "done" if i == last else "stage",
                "data": {},
            }
            for i in range(after + 1, last + 1)
        ]
        body = Body(headers + b"".join(json.dumps(e).encode() + b"\n" for e in records))
        body.body_start = len(headers)
        response = http.client.HTTPResponse(Sock(body))
        response.begin()
        responses.append(response)
        return response

    from types import SimpleNamespace

    monkeypatch.setattr(
        runtime.EngineApi,
        "open_response",
        lambda self, method, path, body, deadline: transport(
            SimpleNamespace(full_url=self.base + path)
        ),
    )
    api = runtime.EngineApi(1, "CPU")
    monkeypatch.setattr(
        api, "request", lambda *args, **kwargs: {"job_id": "J", "state": "busy"}
    )

    class Sensor:
        def sample(self):
            sampled.append(time.monotonic())
            return {}

    start = time.monotonic()
    if complete:
        terminal, _ = runner.observe_job(
            api, Sensor(), "J", tmp_path, observation_s=0.5, interval_s=0.035
        )
        assert terminal["type"] == "done"
    else:
        with pytest.raises(runner.ObservationTimeout):
            runner.observe_job(
                api, Sensor(), "J", tmp_path, observation_s=0.13, interval_s=0.035
            )
        assert time.monotonic() - start < 0.25
    assert len(sampled) >= 3
    assert max(b - a for a, b in itertools.pairwise(sampled)) < 0.09
    assert afters[0] == 0 and afters == sorted(set(afters))
    events = runner.read_records(tmp_path / "events.ndjson")
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert all(response.isclosed() for response in responses)


def test_json_status_transport_has_deadline_even_with_continuous_bytes(
    harness_module, monkeypatch
):
    import http.client
    import io
    import time

    runtime = harness_module("benchmark_runtime")

    class Body(io.BytesIO):
        def read(self, size=-1):
            if size < 0:
                result = b""
                while chunk := self.read(1):
                    result += chunk
                return result
            time.sleep(0.012)
            return super().read(size)

        def read1(self, size=-1):
            return self.read(1)

    class Sock:
        def makefile(self, *args, **kwargs):
            return Body(
                b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n{"job_id":"J","state":"busy"}'
            )

    responses = []

    def transport(*args, **kwargs):
        response = http.client.HTTPResponse(Sock())
        response.begin()
        responses.append(response)
        return response

    monkeypatch.setattr(runtime.EngineApi, "open_response", lambda *args: transport())
    api = runtime.EngineApi(1, "CPU", timeout=0.04)
    start = time.monotonic()
    with pytest.raises(runtime.ApiError, match="TRANSPORT_DEADLINE"):
        api.request("GET", "/v1/jobs/J")
    assert time.monotonic() - start < 0.12
    assert responses[0].isclosed()
