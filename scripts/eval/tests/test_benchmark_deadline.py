"""HTTPResponse real sobre lecturas socket simuladas: sin red ni threads."""

import http.client
import io
import json

import pytest


def wire_transport(
    runtime, monkeypatch, *, payload, phase, delay, chunked=True, status=200
):
    clock = [0.0]
    header = f"HTTP/1.1 {status} OK\r\nConnection: close\r\n".encode()
    if chunked:
        header += b"Transfer-Encoding: chunked\r\n"
    header += b"\r\n"
    extension = b";foo=bar" if phase == "extension" else b""
    chunk_header = format(len(payload), "x").encode() + extension + b"\r\n"
    body = chunk_header + payload + b"\r\n0\r\n\r\n" if chunked else payload
    wire = header + body
    sockets = []

    class Raw(io.RawIOBase):
        def __init__(self, sock):
            super().__init__()
            self._sock = sock

        def readable(self):
            return True

        def readinto(self, target):
            sock = self._sock
            position = sock.position
            slow = (
                phase == "headers"
                and position < len(header)
                or phase in {"chunk", "extension"}
                and len(header) <= position < len(header) + len(chunk_header)
                or phase == "body"
                and position >= len(header)
                or phase == "all"
            )
            cost = delay if slow else 0
            if sock.timeout is not None and cost > sock.timeout:
                clock[0] += sock.timeout
                raise TimeoutError("CPU timeout")
            clock[0] += cost
            if position == len(wire):
                return 0
            target[0] = wire[position]
            sock.position += 1
            return 1

        def close(self):
            self._sock.raw_closed = True
            super().close()

    class Sock:
        def __init__(self):
            self.position = 0
            self.timeout = 0.04
            self.closed = self.raw_closed = False
            sockets.append(self)

        def makefile(self, *args, buffering=None, **kwargs):
            raw = Raw(self)
            return raw if buffering == 0 else io.BufferedReader(raw)

        def settimeout(self, value):
            self.timeout = value

        def setsockopt(self, *args):
            pass

        def sendall(self, data):
            self.sent = data
            if phase == "send":
                clock[0] += self.timeout
                raise TimeoutError("CPU send timeout")

        def close(self):
            self.closed = True

    def create(*args, **kwargs):
        if phase == "open":
            clock[0] += 0.04
            raise TimeoutError("CPU connect timeout")
        return Sock()

    def old_open(*args, **kwargs):
        response = http.client.HTTPResponse(create())
        response.begin()
        return response

    monkeypatch.setattr(runtime.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(runtime.socket, "create_connection", create)
    # Reproduce baseline urllib and also exercise replacement HTTPConnection.
    if hasattr(runtime, "urllib"):
        monkeypatch.setattr(runtime.urllib.request, "urlopen", old_open)
    return clock, sockets


@pytest.mark.parametrize(
    "phase", ["headers", "chunk", "extension", "body", "open", "send"]
)
@pytest.mark.parametrize("kind", ["events", "json"])
def test_deadline_bounds_real_http_parser(harness_module, monkeypatch, phase, kind):
    runtime = harness_module("benchmark_runtime")
    payload = (
        json.dumps({"seq": 1, "job_id": "J", "type": "done", "data": {}}).encode()
        + b"\n"
    )
    clock, sockets = wire_transport(
        runtime, monkeypatch, payload=payload, phase=phase, delay=0.025
    )
    api = runtime.EngineApi(1, "private-CPU", timeout=0.04)
    if kind == "events":
        assert api.events("J", after=7, timeout=0.04) == []
    else:
        with pytest.raises(runtime.ApiError):
            api.request("GET", "/v1/jobs/J")
    assert clock[0] <= 0.040001, (phase, kind, clock[0])
    assert all(sock.closed and (sock.raw_closed or phase == "send") for sock in sockets)
    if sockets and hasattr(sockets[0], "sent"):
        assert (
            b"after=7" in sockets[0].sent
            if kind == "events"
            else b"/v1/jobs/J" in sockets[0].sent
        )


@pytest.mark.parametrize("kind,status", [("events", 200), ("json", 200), ("json", 400)])
def test_real_http_success_error_and_close(harness_module, monkeypatch, kind, status):
    runtime = harness_module("benchmark_runtime")
    payload = (
        json.dumps(
            {
                "seq": 8,
                "job_id": "J",
                "type": "done",
                "code": "INVALID_PARAMS",
                "data": {},
            }
        ).encode()
        + b"\n"
    )
    clock, sockets = wire_transport(
        runtime, monkeypatch, payload=payload, phase="all", delay=0.00001, status=status
    )
    api = runtime.EngineApi(1, "private-CPU", timeout=0.04)
    if status == 400:
        with pytest.raises(runtime.ApiError, match="INVALID_PARAMS"):
            api.request("GET", "/v1/jobs/J")
    elif kind == "events":
        assert api.events("J", after=7, timeout=0.04)[0]["seq"] == 8
    else:
        assert api.request("GET", "/v1/jobs/J")["job_id"] == "J"
    assert clock[0] < 0.04 and all(sock.raw_closed for sock in sockets)


def test_status_query_keeps_original_global_deadline(harness_module, monkeypatch):
    runtime = harness_module("benchmark_runtime")
    api = runtime.EngineApi(1, "CPU")
    monkeypatch.setattr(runtime.time, "monotonic", lambda: 2.0)
    seen = {}

    def request(*args, **kwargs):
        seen.update(kwargs)
        return {}

    monkeypatch.setattr(api, "request", request)
    api.request_before("GET", "/v1/jobs/J", deadline=3.0)
    assert seen.get("deadline") == 3.0


def test_plain_body_also_uses_absolute_deadline(harness_module, monkeypatch):
    runtime = harness_module("benchmark_runtime")
    clock, sockets = wire_transport(
        runtime,
        monkeypatch,
        payload=b'{"job_id":"J"}',
        phase="body",
        delay=0.025,
        chunked=False,
    )
    with pytest.raises(runtime.ApiError, match="TRANSPORT_DEADLINE"):
        runtime.EngineApi(1, "CPU", timeout=0.04).request("GET", "/v1/jobs/J")
    assert clock[0] <= 0.040001 and all(
        sock.raw_closed and sock.closed for sock in sockets
    )


def test_event_line_limit_applies_before_json_decode(harness_module, monkeypatch):
    runtime = harness_module("benchmark_runtime")
    payload = (
        json.dumps(
            {
                "seq": 1,
                "job_id": "J",
                "type": "done",
                "data": {"padding": "x" * (4 * 1024 * 1024)},
            }
        ).encode()
        + b"\n"
    )

    class Response(io.BytesIO):
        status = 200

        def read1(self, size):
            return self.read(size)

    response = Response(payload)
    monkeypatch.setattr(runtime.EngineApi, "open_response", lambda *args: response)
    assert runtime.EngineApi(1, "CPU").events("J", timeout=1) == []
    assert response.closed


@pytest.mark.parametrize("kind", ["events", "json"])
def test_json_decoded_after_deadline_is_rejected(harness_module, monkeypatch, kind):
    runtime = harness_module("benchmark_runtime")
    payload = b'{"seq":1,"job_id":"J","type":"done","data":{}}\n'
    clock, sockets = wire_transport(
        runtime, monkeypatch, payload=payload, phase="all", delay=0
    )
    loads = runtime.json.loads

    def late(value):
        result = loads(value)
        clock[0] = 0.05
        return result

    monkeypatch.setattr(runtime.json, "loads", late)
    api = runtime.EngineApi(1, "CPU", timeout=0.04)
    if kind == "events":
        assert not api.events("J", timeout=0.04)
    else:
        with pytest.raises(runtime.ApiError, match="TRANSPORT_DEADLINE"):
            api.request("GET", "/v1/jobs/J")
    assert all(sock.raw_closed and sock.closed for sock in sockets)


@pytest.mark.parametrize("sensor_cost", [0.5, 1.5, 4.0])
def test_sampling_budget_includes_sensor_and_global_deadline(
    harness_module, tmp_path, sensor_cost
):
    runner = harness_module("benchmark_runner")
    clock = [0.0]
    samples, budgets = [], []

    class Sensor:
        def sample(self):
            samples.append(clock[0])
            clock[0] += sensor_cost
            return {}

    class Api:
        def events(self, job_id, after, timeout):
            budgets.append(timeout)
            clock[0] += timeout
            return []

        def request_before(self, *args, **kwargs):
            return {"job_id": "J", "state": "busy"}

    with pytest.raises(runner.ObservationTimeout):
        runner.observe_job(
            Api(),
            Sensor(),
            "J",
            tmp_path,
            observation_s=4,
            interval_s=1,
            clock=lambda: clock[0],
            sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
        )
    if sensor_cost == 0.5:
        assert samples == [0, 1, 2, 3]
        assert budgets == [0.5] * 4
    elif sensor_cost == 1.5:
        assert samples == [0, 2.5]
        assert budgets == [1]
    else:
        assert not budgets
    assert clock[0] <= 4 if sensor_cost == 4 else clock[0] <= 4.5


def test_terminal_received_after_global_deadline_is_not_accepted(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")
    clock = [0.0]

    class Sensor:
        def sample(self):
            return {}

    class Api:
        def events(self, *args, **kwargs):
            clock[0] = 1.1
            return [{"job_id": "J", "seq": 1, "type": "done", "data": {}}]

        def request_before(self, *args, **kwargs):
            raise AssertionError("no query after deadline")

    with pytest.raises(runner.ObservationTimeout):
        runner.observe_job(
            Api(),
            Sensor(),
            "J",
            tmp_path,
            observation_s=1,
            interval_s=1,
            clock=lambda: clock[0],
        )
    assert not runner.read_records(tmp_path / "events.ndjson")


@pytest.mark.parametrize("sensor_cost", [1.0, 1.5])
def test_slow_sensor_still_observes_ready_done(harness_module, tmp_path, sensor_cost):
    runner = harness_module("benchmark_runner")
    clock = [0.0]
    queries = []

    class Sensor:
        def sample(self):
            clock[0] += sensor_cost
            return {}

    class Api:
        def events(self, job_id, after, timeout):
            queries.append((job_id, after, timeout))
            clock[0] += 0.01
            return [{"job_id": "J", "seq": 1, "type": "done", "data": {}}]

        def request_before(self, *args, **kwargs):
            raise AssertionError("terminal needs no status query")

    terminal, _ = runner.observe_job(
        Api(),
        Sensor(),
        "J",
        tmp_path,
        observation_s=4,
        interval_s=1,
        clock=lambda: clock[0],
        sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    assert terminal["type"] == "done"
    assert queries == [("J", 0, 1)]
    assert clock[0] == sensor_cost + 0.01
    assert runner.read_records(tmp_path / "events.ndjson") == [terminal]


def test_slow_sensor_progress_and_status_keep_job_and_resume_sequence(
    harness_module, tmp_path
):
    runner = harness_module("benchmark_runner")
    clock = [0.0]
    queries, statuses = [], []

    class Sensor:
        def sample(self):
            clock[0] += 1.5
            return {}

    class Api:
        def events(self, job_id, after, timeout):
            queries.append((job_id, after, timeout))
            clock[0] += 0.01
            return [
                {"job_id": job_id, "seq": after + 1, "type": "progress", "data": {}}
            ]

        def request_before(self, method, path, deadline):
            statuses.append((method, path, deadline, clock[0]))
            return {"job_id": "J", "state": "busy"}

    with pytest.raises(runner.ObservationTimeout):
        runner.observe_job(
            Api(),
            Sensor(),
            "J",
            tmp_path,
            observation_s=4,
            interval_s=1,
            clock=lambda: clock[0],
            sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
        )
    assert [(job, after) for job, after, _ in queries] == [("J", 0), ("J", 1)]
    assert [entry[2] for entry in statuses] == [2.5, 4]
    assert all(
        method == "GET" and path == "/v1/jobs/J" and now < deadline
        for method, path, deadline, now in statuses
    )
    assert [
        event["seq"] for event in runner.read_records(tmp_path / "events.ndjson")
    ] == [1, 2]
    assert (
        json.loads((tmp_path / "observation-timeout.json").read_text())[
            "observed_status"
        ]["job_id"]
        == "J"
    )

    class ResumeApi(Api):
        def events(self, job_id, after, timeout):
            assert (job_id, after) == ("J", 2)
            return [{"job_id": job_id, "seq": 3, "type": "done", "data": {}}]

    terminal, _ = runner.observe_job(
        ResumeApi(),
        Sensor(),
        "J",
        tmp_path,
        observation_s=4,
        interval_s=1,
        clock=lambda: clock[0],
        sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    assert terminal["seq"] == 3
    assert [
        event["seq"] for event in runner.read_records(tmp_path / "events.ndjson")
    ] == [1, 2, 3]


@pytest.mark.parametrize("sensor_cost", [1.5, 5.0])
def test_slow_sensor_cannot_accept_terminal_outside_horizon(
    harness_module, tmp_path, sensor_cost
):
    runner = harness_module("benchmark_runner")
    clock = [0.0]
    queries = []

    class Sensor:
        def sample(self):
            clock[0] += sensor_cost
            return {}

    class Api:
        def events(self, job_id, after, timeout):
            queries.append((job_id, after, timeout))
            clock[0] = 4.01
            return [{"job_id": "J", "seq": 1, "type": "done", "data": {}}]

        def request_before(self, *args, **kwargs):
            raise AssertionError("no query after global deadline")

    with pytest.raises(runner.ObservationTimeout):
        runner.observe_job(
            Api(),
            Sensor(),
            "J",
            tmp_path,
            observation_s=4,
            interval_s=1,
            clock=lambda: clock[0],
            sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
        )
    assert queries == ([("J", 0, 1)] if sensor_cost == 1.5 else [])
    assert not runner.read_records(tmp_path / "events.ndjson")
    assert clock[0] == (4.01 if sensor_cost == 1.5 else 5)
