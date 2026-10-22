"""Pruebas aisladas: relojes/kernel Windows reales; contenido CPU sintético."""

import ast
import importlib.util
import json
import os
import threading
import time
import uuid
from pathlib import Path

import benchmark_process as process_api
import pytest

PRIVATE = Path(os.environ["STUDIO_CANONICAL_TEST_ROOT"])


TRANSPORT_FIXTURE = """import ctypes
import benchmark_canonical_runtime as runtime
from benchmark_canonical_runtime import CanonicalProvider
class Provider(CanonicalProvider):
    def read_steps(self, payload, deadline_ns):
        # Trusted constructor-selected transport fixture, not semantic approval.
        if MODE == "quota65": runtime.MAX_PROGRESS = 65
        original = runtime._signed
        def signed(value, key):
            if value.get("lane") == "read" and value.get("index") == 1:
                value = dict(value)
                if MODE == "replay": value["index"] = 0
                if MODE == "binding": value["binding"] = "foreign"
                if MODE == "lane": value["lane"] = "ingest"
                if MODE == "malformed": value["type"] = "unknown"
                if MODE == "error": value.update(type="error", payload="native_protocol_error")
                frame = original(value, key)
                if MODE == "mac": frame["mac"] = "0" * 64
                return frame
            return original(value, key)
        if MODE in {"replay", "binding", "lane", "malformed", "error", "mac"}:
            runtime._signed = signed
        for index in range(COUNT):
            if index == 1 and NATIVE_EVENT:
                dll = ctypes.WinDLL("kernel32", use_last_error=True)
                dll.OpenEventW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
                dll.OpenEventW.restype = ctypes.c_void_p
                dll.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
                dll.CloseHandle.argtypes = [ctypes.c_void_p]
                event = dll.OpenEventW(0x100000, False, NATIVE_EVENT)
                if not event: raise ctypes.WinError(ctypes.get_last_error())
                try:
                    while dll.WaitForSingleObject(event, 0) == 258: yield None
                finally: dll.CloseHandle(event)
            yield {"step": index, "chunk": "x" * 1200}
        if MODE == "failure": raise ValueError("native_explicit_failure")
        if MODE == "deadline":
            dll = ctypes.WinDLL("kernel32", use_last_error=True)
            dll.CreateEventW.restype = ctypes.c_void_p
            dll.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            event = dll.CreateEventW(None, True, False, None)
            if not event: raise ctypes.WinError(ctypes.get_last_error())
            dll.WaitForSingleObject(event, 0xffffffff)
        return {"transport_complete": True}
"""


def transport_channel(episode_sensor, count, mode, native_event=None):
    import benchmark_canonical_runtime as runtime

    observer, _, root = episode_sensor
    fixture = root / "transport_fixture.py"
    fixture.write_text(
        f"COUNT = {count!r}\nMODE = {mode!r}\nNATIVE_EVENT = {native_event!r}\n"
        + TRANSPORT_FIXTURE,
        encoding="utf-8",
    )
    return runtime.CanonicalChannel(
        observer.worker,
        private_root=root / "binding",
        stream="phase",
        trusted_handler=f"{fixture}:Provider",
    )


def test_native_64_progress_before_collector_resumes(episode_sensor, monkeypatch):
    import benchmark_canonical_runtime as runtime

    channel = transport_channel(episode_sensor, 64, "complete")
    mux = channel.worker._mux
    released = threading.Event()
    drain = threading.Event()
    delivered = []
    original_get = runtime.queue.Queue.get
    original_deliver = mux.deliver
    errors, results = [], []

    def get(queue, *args, **kwargs):
        if any(
            lane == "read" and slot is queue for (lane, _), slot in mux.slots.items()
        ):
            assert drain.wait(1), "collector barrier was not released"
        return original_get(queue, *args, **kwargs)

    def deliver(frame):
        try:
            original_deliver(frame)
            if frame["lane"] == "read":
                delivered.append({k: v for k, v in frame.items() if k != "mac"})
                if frame["type"] == "result":
                    released.set()
        except Exception:
            released.set()
            drain.set()
            raise

    monkeypatch.setattr(runtime.queue.Queue, "get", get)
    monkeypatch.setattr(mux, "deliver", deliver)
    deadline = time.perf_counter_ns() + 2_000_000_000

    def read():
        try:
            results.append(
                channel.worker.call({"operation": "status"}, deadline_ns=deadline)
            )
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            errors.append(error)

    reader = threading.Thread(target=read)
    reader.start()
    try:
        assert released.wait(1)
        assert mux.failure is None, repr(mux.failure)
        # Legitimate ingest still traverses the native scheduler and reader while
        # the read collector is pending. Real validators are exercised elsewhere.
        value = channel.worker.call(
            {
                "operation": "begin",
                "arguments": {
                    "transfer": "burst",
                    "characters": 1,
                    "sha256": "0" * 64,
                    "deadline_ns": deadline,
                },
            },
            deadline_ns=deadline,
        )
        assert value["value"] is not None
        assert reader.is_alive()
        drain.set()
        reader.join(timeout=1)
        assert not errors, repr(errors)
        assert len(results[0]["progress"]) == 64
        assert len(delivered) == 65 and delivered[-1]["type"] == "result"
        assert results[0]["value"] == {"transport_complete": True}
        assert not channel.worker.closed
    finally:
        released.set()
        drain.set()
        channel.close()
        reader.join(timeout=2)


@pytest.mark.parametrize("mode", ["deadline", "failure"])
def test_native_primary_error_after_mux_progress(episode_sensor, mode):
    channel = transport_channel(episode_sensor, 1, mode)
    deadline = time.perf_counter_ns() + 2_000_000_000
    expected = (
        process_api.WorkerDeadline if mode == "deadline" else process_api.WorkerFailure
    )
    try:
        with pytest.raises(expected) as caught:
            channel.worker.call({"operation": "status"}, deadline_ns=deadline)
        error = caught.value
        assert len(error.progress) == 1
        assert error.partial_raw == {"step": 0, "chunk": "x" * 1200}
        assert error.progress[0]["payload"] == error.partial_raw
        assert "value" not in error.progress[0]
        assert error.evidence["normalized_progress"] == [{"value": error.partial_raw}]
        assert "not wire" in error.evidence["normalized_progress_semantics"]
        assert (
            "deadline" in str(error)
            if mode == "deadline"
            else "worker_pipe_eof" in str(error)
        )
        assert error.evidence["cleanup"] is channel.worker.close_evidence
        assert channel.worker.process.poll() is not None
        assert channel.worker.close_evidence["job_empty"]
        assert time.perf_counter_ns() < deadline
    finally:
        channel.close()


def test_native_cleanup_error_does_not_replace_primary(episode_sensor, monkeypatch):
    channel = transport_channel(episode_sensor, 1, "failure")
    abort = channel.worker.abort_owned

    def cleanup(reason):
        abort(reason)
        raise process_api.WorkerFailure("private_cleanup_control")

    monkeypatch.setattr(channel.worker, "abort_owned", cleanup)
    try:
        with pytest.raises(
            process_api.WorkerFailure, match="worker_pipe_eof"
        ) as caught:
            channel.worker.call(
                {"operation": "status"},
                deadline_ns=time.perf_counter_ns() + 2_000_000_000,
            )
        assert caught.value.evidence["cleanup_error"] == "private_cleanup_control"
        assert caught.value.evidence["cleanup"] is channel.worker.close_evidence
        assert caught.value.partial_raw == {"step": 0, "chunk": "x" * 1200}
        assert channel.worker.process.poll() is not None
        assert channel.worker.close_evidence["job_empty"]
    finally:
        channel.close()


def test_receiver_frame_byte_quota_precedes_admission(episode_sensor):
    import benchmark_canonical_runtime as runtime

    channel = transport_channel(episode_sensor, 1, "complete")
    mux = channel.worker._mux
    slot = runtime.ReplySlot()
    mux.slots["read", 1] = slot
    try:
        frame = runtime._signed(
            {
                "epoch": mux.epoch,
                "binding": mux.binding,
                "lane": "read",
                "seq": 1,
                "index": 0,
                "type": "progress",
                "payload": "small",
            },
            mux.key,
        )
        # Negative receiver probe: bytes must fail before MAC validation.
        frame["payload"] = "x" * process_api.MAX_FRAME
        with pytest.raises(ValueError, match="frame"):
            mux.deliver(frame)
        assert slot.empty() and not slot.wire_progress and slot.next_index == 0
        assert slot.maxsize == process_api.MAX_PROGRESS + 2
    finally:
        mux.slots.pop(("read", 1))
        channel.close()


@pytest.mark.parametrize(
    "mode, reason",
    [
        ("quota65", "progress_limit"),
        ("replay", "stale_or_reordered_reply"),
        ("binding", "frame_session_binding_invalid"),
        ("lane", "foreign_or_replayed_reply"),
        ("malformed", "invalid_reply_type"),
        ("error", "native_protocol_error"),
        ("mac", "frame_authentication_failed"),
    ],
)
def test_native_receiver_controls_with_concurrent_ingest(
    episode_sensor, monkeypatch, mode, reason
):
    import ctypes

    dll = ctypes.WinDLL("kernel32", use_last_error=True)
    dll.CreateEventW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_wchar_p,
    ]
    dll.CreateEventW.restype = ctypes.c_void_p
    dll.SetEvent.argtypes = [ctypes.c_void_p]
    dll.CloseHandle.argtypes = [ctypes.c_void_p]
    name = "Local\\music-studio-transport-" + uuid.uuid4().hex
    event = dll.CreateEventW(None, True, False, name)
    assert event
    channel = transport_channel(
        episode_sensor, 65 if mode == "quota65" else 2, mode, name
    )
    first = threading.Event()
    original = channel.worker._mux.deliver
    errors = []

    def deliver(frame):
        original(frame)
        if frame["lane"] == "read" and frame["index"] == 0:
            first.set()

    monkeypatch.setattr(channel.worker._mux, "deliver", deliver)
    deadline = time.perf_counter_ns() + 2_000_000_000

    def read():
        try:
            channel.worker.call({"operation": "status"}, deadline_ns=deadline)
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            errors.append(error)

    reader = threading.Thread(target=read)
    reader.start()
    try:
        assert first.wait(1)
        result = channel.worker.call(
            {
                "operation": "begin",
                "arguments": {
                    "transfer": "control",
                    "characters": 1,
                    "sha256": "0" * 64,
                    "deadline_ns": deadline,
                },
            },
            deadline_ns=deadline,
        )
        assert result["value"] is not None and reader.is_alive()
        assert dll.SetEvent(event)
        reader.join(timeout=2)
        assert len(errors) == 1 and isinstance(errors[0], process_api.WorkerFailure)
        assert reason in str(errors[0])
        assert len(errors[0].progress) == (64 if mode == "quota65" else 1)
        receipt = channel.worker.close_evidence
        assert receipt["job_empty"]
        # Reader rejection before EOF keeps the existing unknown quarantine;
        # empty Job alone never certifies returned resources.
        if mode == "error":
            assert receipt["resources_returned"]
        else:
            assert receipt["disposition"] == "UNKNOWN_QUARANTINED"
            assert not receipt["resources_returned"] and not receipt["reader_eof"]
        assert channel.worker.process.poll() is not None
        channel.worker.close(graceful=False)
        assert channel.worker.close_evidence is receipt
    finally:
        dll.SetEvent(event)
        channel.close()
        reader.join(timeout=2)
        dll.CloseHandle(event)


@pytest.fixture
def native_handler():
    root = PRIVATE / uuid.uuid4().hex
    root.mkdir(parents=True)
    path = root / "native_handler.py"
    path.write_text(
        """import ctypes, os, time
from pathlib import Path
class Handler:
    def __init__(self, config):
        self.config = config
        self.dll = ctypes.WinDLL("kernel32", use_last_error=True)
        self.dll.CreateEventW.restype = ctypes.c_void_p
        self.dll.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.dll.CloseHandle.argtypes = [ctypes.c_void_p]
        self.event = self.dll.CreateEventW(None, True, False, None)
        if not self.event: raise ctypes.WinError(ctypes.get_last_error())
    def steps(self):
        Path(self.config["entered"]).write_text("own event kernel wait")
        for index in range(8):
            self.dll.WaitForSingleObject(self.event, 80)
            yield index
    def read_steps(self, payload, deadline_ns):
        for index in self.steps(): yield {"step": index}
        return {"read_complete": True}
    def __call__(self, payload, emit):
        if self.config.get("block_ingest") and payload["operation"] == "ingest":
            Path(self.config["entered"]).write_text("own event infinite kernel wait")
            self.dll.WaitForSingleObject(self.event, 0xffffffff)
        if payload["operation"] == "status":
            for index in self.steps(): emit({"step": index})
            return {"read_complete": True}
        if payload["operation"] == "block":
            Path(self.config["entered"]).write_text("own event infinite kernel wait")
            self.dll.WaitForSingleObject(self.event, 0xffffffff)
        return {"ingested": True}
    def close(self):
        self.dll.CloseHandle(self.event)
""",
        encoding="utf-8",
    )
    return root, path


def wait_file(path, deadline):
    while not path.exists() and time.perf_counter_ns() < deadline:
        time.sleep(0.001)
    assert path.exists(), "native handler never reached kernel wait"


def test_optin_ingest_does_not_wait_for_whole_read(native_handler):
    root, handler = native_handler
    entered = root / "entered"
    owned = process_api.OwnedProcess(
        {"canonical_mux_v1": True, "entered": str(entered)}, f"{handler}:Handler"
    )
    results, errors = [], []
    deadline = time.perf_counter_ns() + 2_000_000_000

    def read():
        try:
            results.append(owned.call({"operation": "status"}, deadline_ns=deadline))
        except (OSError, ValueError, RuntimeError) as error:
            errors.append(error)

    reader = threading.Thread(target=read)
    reader.start()
    try:
        wait_file(entered, deadline - 250_000_000)
        started = time.perf_counter_ns()
        ingested = owned.call({"operation": "ingest"}, deadline_ns=deadline)
        finished = time.perf_counter_ns()
        assert ingested["value"]["ingested"] is True
        assert finished - started < 250_000_000
        assert reader.is_alive(), "ingest waited for the complete audit"
        reader.join(timeout=2)
        assert not errors
        assert results[0]["value"]["read_complete"] is True
    finally:
        owned.close(graceful=False)
        reader.join(timeout=2)


def test_forced_close_revokes_while_graceful_stdin_write_blocked(native_handler):
    root, handler = native_handler
    entered = root / "entered"
    owned = process_api.OwnedProcess({"entered": str(entered)}, f"{handler}:Handler")
    stop = threading.Event()
    failures = []
    frame = process_api.encode(
        {"seq": 1, "payload": {"operation": "block", "arguments": "x" * 3000}},
        process_api.MAX_REQUEST,
    )
    deadline = time.perf_counter_ns() + 2_000_000_000

    def fill():
        try:
            while not stop.is_set():
                owned.process.stdin.write(frame)
        except (OSError, ValueError) as error:
            failures.append(str(error))

    def graceful():
        try:
            owned.close()
        except (OSError, ValueError, RuntimeError) as error:
            failures.append(str(error))

    writer = threading.Thread(target=fill)
    closer = threading.Thread(target=graceful)
    writer.start()
    try:
        wait_file(entered, deadline - 250_000_000)
        time.sleep(0.025)
        closer.start()
        time.sleep(0.025)
        assert owned.closed and closer.is_alive()
        owned.close(graceful=False)
        assert owned.process.poll() is not None, "original owned Job remains alive"
        assert time.perf_counter_ns() < deadline
        writer.join(timeout=0.22)
        closer.join(timeout=0.22)
        assert not writer.is_alive() and not closer.is_alive()
        assert owned.close_evidence["job_empty"] is True
    finally:
        stop.set()
        # Baseline rescue uses the original Job, never a PID/name lookup.
        if owned.process.poll() is None:
            owned.job.terminate()
        writer.join(timeout=2)
        if closer.ident is not None:
            closer.join(timeout=2)
        if not owned.closed:
            owned.close(graceful=False)


@pytest.fixture
def episode_sensor():
    source = Path("scripts/eval/tests/test_benchmark_episode_v3.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    assignment = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "PHASE" for t in n.targets)
    )
    lines = source.splitlines(keepends=True)
    root = PRIVATE / ("sensor-" + uuid.uuid4().hex)
    root.mkdir()
    lines[assignment.lineno - 1 : assignment.end_lineno] = [
        f"PHASE = Path({str(root)!r})\n"
    ]
    path = root / "native_factory.py"
    path.write_text("".join(lines), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("unit1_native_factory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    factory = module.episode_factory.__wrapped__()
    observer, context = factory()
    try:
        yield observer, context, root
    finally:
        observer.close()


def acquire_original(sensor, channel):
    from benchmark_episode import clock

    started = clock()
    args = {
        "episode_id": uuid.uuid4().hex,
        "stream": "phase",
        "start": started,
        "deadline_ns": started["monotonic_ns"] + 2_000_000_000,
        "phase_started_utc": None,
        "idle": False,
        "confirm": channel.last_receipt,
        "enforce": True,
    }
    sensor.call(
        {"operation": "episode_v3", "arguments": args}, deadline_ns=args["deadline_ns"]
    )
    return channel.ingest_latest()


def test_real_canonical_ingest_publish_status_and_opaque_position(episode_sensor):
    import benchmark_canonical_runtime as runtime

    observer, _context, root = episode_sensor
    channel = runtime.CanonicalChannel(
        observer.worker, private_root=root / "binding", stream="phase"
    )
    try:
        commit = acquire_original(observer.worker, channel)
        assert commit["cursor"] == 1
        position = channel.request_view(
            deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
        assert position.cursor == 1 and position.prefix == commit["prefix"]
        assert channel._resolve_position(position) is position
        counterfeit = runtime.CanonicalPosition(**position.__dict__)
        with pytest.raises(ValueError, match="foreign_position"):
            channel._resolve_position(counterfeit)
        second = acquire_original(observer.worker, channel)
        assert second["cursor"] == 2
        fresh = channel.request_view(
            kind="base", deadline_ns=time.perf_counter_ns() + 2_000_000_000
        )
        assert fresh.cursor == 2
        with pytest.raises(ValueError, match="foreign_position"):
            channel._resolve_position(position)
        with pytest.raises(ValueError, match="replayed_sensor"):
            channel.ingest_latest()
    finally:
        channel.close()
    assert channel.worker.close_evidence["resources_returned"] is True
    (root / "canonical-receipt.json").write_text(
        json.dumps(
            {
                "sensor_birth": observer.worker.ownership,
                "canonical_birth": channel.worker.ownership,
                "canonical_cleanup": channel.worker.close_evidence,
                "canonical_argv": channel.worker.process.args,
                "scope": "CPU synthetic values; actual native processes/store/state/validators",
            }
        ),
        encoding="utf-8",
    )


def test_real_store_witness_steps_yield_to_native_ingest(episode_sensor):
    import benchmark_canonical_runtime as runtime

    observer, _, root = episode_sensor
    fixture = root / "slow_witness.py"
    fixture.write_text(
        """import ctypes
from pathlib import Path
from benchmark_canonical_runtime import CanonicalProvider
class SlowProvider(CanonicalProvider):
    def __init__(self, config):
        super().__init__(config)
        self.reading = False
        self.dll = ctypes.WinDLL("kernel32", use_last_error=True)
        self.dll.CreateEventW.restype = ctypes.c_void_p
        self.dll.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.dll.CloseHandle.argtypes = [ctypes.c_void_p]
        self.event = self.dll.CreateEventW(None, True, False, None)
        original = self.state._witness
        def witness(registration, deadline):
            original(registration, deadline)
            if self.reading:
                Path(__file__).with_name("witness-entered").write_text("actual witness then own event wait")
                self.dll.WaitForSingleObject(self.event, 90)
        self.state._witness = witness
    def read_steps(self, payload, deadline):
        iterator = super().read_steps(payload, deadline)
        try:
            while True:
                self.reading = True
                try: value = next(iterator)
                except StopIteration as result: return result.value
                finally: self.reading = False
                yield value
        finally: iterator.close()
    def close(self):
        super().close()
        self.dll.CloseHandle(self.event)
""",
        encoding="utf-8",
    )
    channel = runtime.CanonicalChannel(
        observer.worker,
        private_root=root / "binding",
        stream="phase",
        trusted_handler=f"{fixture}:SlowProvider",
    )
    values, errors = [], []
    try:
        for _ in range(8):
            acquire_original(observer.worker, channel)
        deadline = time.perf_counter_ns() + 2_000_000_000

        def read():
            try:
                values.append(channel.request_view(deadline_ns=deadline))
            except (OSError, ValueError, RuntimeError) as error:
                errors.append(error)

        reader = threading.Thread(target=read)
        reader.start()
        wait_file(root / "witness-entered", deadline - 250_000_000)
        started = time.perf_counter_ns()
        committed = acquire_original(observer.worker, channel)
        finished = time.perf_counter_ns()
        assert committed["cursor"] == 9
        assert reader.is_alive(), (
            "real custody ingest waited for the complete prefix audit"
        )
        reader.join(timeout=2)
        assert not errors
        assert values[0].cursor == 8
        (root / "priority-wall.json").write_text(
            json.dumps(
                {
                    "started": started,
                    "ingest_finished": finished,
                    "read_finished": time.perf_counter_ns(),
                    "read_deadline": deadline,
                    "witnesses": 8,
                    "native_primitive": "own event after pass-through real custody witness; not blocked custody ReadFile",
                    "synthetic_cpu_values": True,
                }
            ),
            encoding="utf-8",
        )
    finally:
        channel.close()


@pytest.mark.parametrize(
    "attack",
    [
        "mac",
        "epoch",
        "binding",
        "sequence",
        "bool_seq",
        "index",
        "lane",
        "extra",
        "payload",
        "oversize",
    ],
)
def test_native_wire_attack_fails_before_handler_io(native_handler, attack):
    import benchmark_canonical_runtime as runtime

    root, handler = native_handler
    entered = root / "entered"
    owned = process_api.OwnedProcess(
        {"canonical_mux_v1": True, "entered": str(entered)}, f"{handler}:Handler"
    )
    mux = owned._mux
    request = {
        "epoch": mux.epoch,
        "binding": mux.binding,
        "lane": "read",
        "seq": 1,
        "index": 0,
        "deadline_ns": time.perf_counter_ns() + 2_000_000_000,
        "payload": {"operation": "status"},
    }
    if attack in {"epoch", "binding"}:
        request[attack] = "foreign"
    elif attack == "sequence":
        request["seq"] = 0
    elif attack == "bool_seq":
        request["seq"] = True
    elif attack == "index":
        request["index"] = 1
    elif attack == "lane":
        request["lane"] = "foreign"
    elif attack == "extra":
        request["untrusted_root"] = str(root)
    elif attack == "payload":
        request["payload"]["operation"] = "unknown"
    frame = runtime._signed(request, mux.key)
    if attack == "mac":
        frame["mac"] = "0" * 64
    data = process_api.encode(frame) if attack != "oversize" else b"x" * 4097 + b"\n"
    try:
        owned.process.stdin.write(data)
        with pytest.raises(process_api.WorkerFailure):
            owned.call(
                {"operation": "ingest"},
                deadline_ns=time.perf_counter_ns() + 2_000_000_000,
            )
        assert not entered.exists()
        assert owned.process.poll() is not None
    finally:
        owned.close(graceful=False)
    assert owned.close_evidence["job_empty"]


def test_watchdog_kills_original_job_with_native_input_and_writer_blocked(
    native_handler,
):
    root, handler = native_handler
    entered = root / "entered"
    owned = process_api.OwnedProcess(
        {"canonical_mux_v1": True, "entered": str(entered), "block_ingest": True},
        f"{handler}:Handler",
    )
    errors = []
    deadline = time.perf_counter_ns() + 2_000_000_000
    stop = threading.Event()

    def ingest():
        try:
            owned.call({"operation": "ingest"}, deadline_ns=deadline)
        except (OSError, ValueError, RuntimeError) as error:
            errors.append(error)

    def fill():
        try:
            while not stop.is_set():
                owned.process.stdin.write(b"x" * 4096)
        except (OSError, ValueError):
            pass

    ingester = threading.Thread(target=ingest)
    writer = threading.Thread(target=fill)
    ingester.start()
    try:
        wait_file(entered, deadline - 250_000_000)
        writer.start()
        time.sleep(0.04)
        with pytest.raises(process_api.WorkerFailure):
            owned.call({"operation": "status"}, deadline_ns=deadline)
        ingester.join(timeout=0.22)
        writer.join(timeout=0.22)
        assert errors and not ingester.is_alive() and not writer.is_alive()
        assert time.perf_counter_ns() < deadline + 50_000_000
        assert owned.process.poll() is not None
        assert owned.close_evidence["resources_returned"]
    finally:
        stop.set()
        owned.close(graceful=False)
        ingester.join(timeout=2)
        if writer.ident:
            writer.join(timeout=2)


@pytest.mark.parametrize(
    "attack",
    ["request_mutation", "context", "parent_publish_failure", "late", "unknown_name"],
)
def test_real_ingest_negative_controls_revoke_and_preserve_raw(
    episode_sensor, monkeypatch, attack
):
    import benchmark_canonical_runtime as runtime
    from benchmark_episode import clock

    observer, _, root = episode_sensor
    channel = runtime.CanonicalChannel(
        observer.worker, private_root=root / "binding", stream="phase"
    )
    started = clock()
    args = {
        "episode_id": uuid.uuid4().hex,
        "stream": "phase",
        "start": started,
        "deadline_ns": started["monotonic_ns"] + 2_000_000_000,
        "phase_started_utc": None,
        "idle": False,
        "confirm": None,
        "enforce": True,
    }
    observer.worker.call(
        {"operation": "episode_v3", "arguments": args}, deadline_ns=args["deadline_ns"]
    )
    directory = observer.root / args["episode_id"]
    if attack == "request_mutation":
        (directory / "request.json").write_text("{}", encoding="utf-8")
    elif attack == "unknown_name":
        (directory / "foreign.json").write_text("{}", encoding="utf-8")
    elif attack == "context":
        channel.context["session_id"] = "foreign"
    elif attack == "late":
        remaining = (args["deadline_ns"] - time.perf_counter_ns()) / 1e9
        time.sleep(max(0, remaining + 0.005))
    elif attack == "parent_publish_failure":
        original = channel.worker.call

        def refuse(payload, **kwargs):
            if payload["operation"] == "publish":
                raise RuntimeError("controlled parent publication failure")
            return original(payload, **kwargs)

        monkeypatch.setattr(channel.worker, "call", refuse)
    try:
        with pytest.raises((ValueError, RuntimeError)):
            channel.ingest_latest()
        assert channel.last_receipt is None and channel.publication is None
        assert channel.worker.closed
        assert list(directory.glob("raw-*.json"))
        assert channel.worker.close_evidence["job_empty"]
        assert list(observer.root.glob("canonical-*/custody-*/*.cap")) or attack in {
            "context",
            "late",
            "unknown_name",
        }
    finally:
        channel.close()


def test_independent_read_lane_is_bounded_without_revoking_healthy_read(native_handler):
    root, handler = native_handler
    entered = root / "entered"
    owned = process_api.OwnedProcess(
        {"canonical_mux_v1": True, "entered": str(entered)}, f"{handler}:Handler"
    )
    errors = []
    deadline = time.perf_counter_ns() + 2_000_000_000

    def read():
        try:
            owned.call({"operation": "status"}, deadline_ns=deadline)
        except (ValueError, RuntimeError) as error:
            errors.append(error)

    reader = threading.Thread(target=read)
    reader.start()
    try:
        wait_file(entered, deadline - 250_000_000)
        started = time.perf_counter_ns()
        with pytest.raises(process_api.WorkerFailure, match="lane_full"):
            owned.call({"operation": "status"}, deadline_ns=deadline)
        assert time.perf_counter_ns() - started < 50_000_000
        reader.join(timeout=2)
        assert not errors and not owned.closed
    finally:
        owned.close(graceful=False)
        reader.join(timeout=2)


@pytest.mark.parametrize(
    "attack", ["source", "challenge", "binding_file", "supervisor_birth"]
)
def test_bootstrap_attack_precedes_factory_filesystem_effects(
    episode_sensor, native_handler, monkeypatch, attack
):
    import benchmark_canonical_runtime as runtime

    observer, _, root = episode_sensor
    original_activate = runtime.ParentMux.activate
    original_birth = runtime._own_birth
    if attack == "supervisor_birth":
        monkeypatch.setattr(
            runtime, "_own_birth", lambda: {**original_birth(), "creation_time": 1}
        )

    def activate(mux, deadline):
        if attack == "challenge":
            mux.owned.ownership["creation_time"] += 1
        if attack == "binding_file":
            config = process_api.decode(mux.owned._trusted_config_bytes)
            Path(config["bootstrap_path"]).write_bytes(b"{}\n")
        return original_activate(mux, deadline)

    if attack in {"challenge", "binding_file"}:
        monkeypatch.setattr(runtime.ParentMux, "activate", activate)
    if attack == "source":
        ownroot, handler = native_handler
        original_assign = process_api.WindowsJob.assign

        def assign(job, process):
            handler.write_text(
                handler.read_text(encoding="utf-8") + "\n# changed after parent seal\n",
                encoding="utf-8",
            )
            return original_assign(job, process)

        monkeypatch.setattr(process_api.WindowsJob, "assign", assign)
        with pytest.raises((ValueError, RuntimeError)):
            process_api.OwnedProcess(
                {"canonical_mux_v1": True, "entered": str(ownroot / "entered")},
                f"{handler}:Handler",
            )
        assert not (ownroot / "entered").exists()
    else:
        with pytest.raises((ValueError, RuntimeError)):
            runtime.CanonicalChannel(
                observer.worker, private_root=root / "binding", stream="phase"
            )
        assert not list(observer.root.glob("canonical-*")), (
            "forged bootstrap reached custody filesystem"
        )


@pytest.mark.parametrize(
    "attack",
    [
        "size",
        "wrong_deadline",
        "foreign_transfer",
        "bool_index",
        "fragment_size",
        "excess",
        "end_digest",
        "fake_publish",
        "fake_confirm",
    ],
)
def test_closed_ingest_transport_controls_before_capture(episode_sensor, attack):
    import benchmark_canonical_runtime as runtime

    observer, _, root = episode_sensor
    channel = runtime.CanonicalChannel(
        observer.worker, private_root=root / "binding", stream="phase"
    )
    deadline = time.perf_counter_ns() + 2_000_000_000

    def call(operation, arguments):
        return channel.worker.call(
            {"operation": operation, "arguments": arguments}, deadline_ns=deadline
        )

    try:
        if attack in {"size", "wrong_deadline"}:
            args = {
                "transfer": "control",
                "characters": 10,
                "sha256": "0" * 64,
                "deadline_ns": deadline,
            }
            if attack == "size":
                args["characters"] = runtime.MAX_CHARACTERS + 1
            else:
                args["deadline_ns"] += 1
            with pytest.raises(process_api.WorkerFailure):
                call("begin", args)
        elif attack in {"fake_publish", "fake_confirm"}:
            operation = "publish" if attack == "fake_publish" else "confirm"
            args = (
                {"commit": {}, "observed": 0}
                if operation == "publish"
                else {"commit": {}, "anchor_sha256": "0" * 64, "completed": 0}
            )
            with pytest.raises(process_api.WorkerFailure):
                call(operation, args)
        else:
            call(
                "begin",
                {
                    "transfer": "control",
                    "characters": 1,
                    "sha256": "0" * 64,
                    "deadline_ns": deadline,
                },
            )
            args = {"transfer": "control", "index": 0, "text": "x"}
            if attack == "foreign_transfer":
                args["transfer"] = "foreign"
            elif attack == "bool_index":
                args["index"] = True
            elif attack == "fragment_size":
                args["text"] = "x" * 1201
            elif attack == "excess":
                args["text"] = "xx"
            if attack == "end_digest":
                call("fragment", args)
                with pytest.raises(process_api.WorkerFailure):
                    call("end", {"transfer": "control"})
            else:
                with pytest.raises(process_api.WorkerFailure):
                    call("fragment", args)
        assert channel.worker.closed
        assert not list(observer.root.glob("canonical-*/custody-*/*.cap"))
    finally:
        channel.close()


def test_cleanup_error_keeps_unknown_quarantine_and_shared_receipt(
    native_handler, monkeypatch
):
    import ctypes

    root, handler = native_handler
    owned = process_api.OwnedProcess(
        {"entered": str(root / "entered")}, f"{handler}:Handler"
    )

    def refuse():
        buffer = ctypes.create_string_buffer(32)
        if not owned.job.dll.QueryInformationJobObject(
            owned.job.handle, 0x7FFF, buffer, len(buffer), None
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        raise AssertionError("invalid information class unexpectedly accepted")

    monkeypatch.setattr(owned.job, "member_handles", refuse)
    with pytest.raises(process_api.WorkerFailure, match="WinError"):
        owned.abort_owned("control")
    receipt = owned.close_evidence
    assert receipt["disposition"] == "UNKNOWN_QUARANTINED"
    assert not receipt["resources_returned"]
    assert receipt["job_empty"] and receipt["reader_eof"]
    owned.close(graceful=False)
    assert owned.close_evidence is receipt


@pytest.mark.parametrize("control", ["fresh_clock_900", "custody_lost_after_checkout"])
def test_actual_canonical_validator_and_custody_failure_controls(
    episode_sensor, control
):
    import benchmark_canonical_runtime as runtime

    observer, _, root = episode_sensor
    fixture = root / "authority_fault.py"
    fixture.write_text(
        """from benchmark_canonical_runtime import CanonicalProvider
import benchmark_canonical as canonical
from benchmark_clock import utc_now
from benchmark_observation import stamp
from datetime import datetime, timezone
class Provider(CanonicalProvider):
    def read_steps(self, payload, deadline):
        iterator = super().read_steps(payload, deadline)
        original = canonical.validate_samples
        CONTROL = """
        + repr(control)
        + """
        try:
            if CONTROL == "fresh_clock_900":
                def actual_validator(samples, context, **kwargs):
                    future = datetime.fromtimestamp(stamp(utc_now()) + 901, timezone.utc).isoformat()
                    return original(samples, context, now=future, **kwargs)
                canonical.validate_samples = actual_validator
            first = next(iterator)
            if CONTROL == "custody_lost_after_checkout": self.store.close()
            yield first
            return (yield from iterator)
        finally:
            canonical.validate_samples = original
            iterator.close()
""",
        encoding="utf-8",
    )
    channel = runtime.CanonicalChannel(
        observer.worker,
        private_root=root / "binding",
        stream="phase",
        trusted_handler=f"{fixture}:Provider",
    )
    try:
        acquire_original(observer.worker, channel)
        acquire_original(observer.worker, channel)
        with pytest.raises(process_api.WorkerFailure):
            channel.request_view(deadline_ns=time.perf_counter_ns() + 2_000_000_000)
        assert channel.worker.closed
        assert list(observer.root.glob("canonical-*/custody-*/*.cap"))
        assert channel.worker.close_evidence["job_empty"]
        assert not channel.positions
    finally:
        channel.close()
