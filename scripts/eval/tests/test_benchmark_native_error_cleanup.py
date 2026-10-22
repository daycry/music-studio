"""Regresión nativa: revocación lógica y EOF físico conservan hechos distintos."""

import ctypes
import threading
import time
import uuid

import benchmark_canonical_runtime as runtime
import benchmark_process as process
import pytest
import test_benchmark_canonical_runtime as original_runtime

transport_channel = original_runtime.transport_channel


@pytest.fixture
def episode_sensor():
    yield from original_runtime.episode_sensor.__wrapped__()


class ReadObserver:
    """Observa el retorno real de readline; nunca sustituye bytes ni fabrica EOF."""

    def __init__(self, pipe):
        self.pipe = pipe
        self.reads = []

    def readline(self, limit):
        data = self.pipe.readline(limit)
        self.reads.append((threading.current_thread().name, bytes(data)))
        return data

    def __getattr__(self, name):
        return getattr(self.pipe, name)


def native_event():
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
    name = "Local\\music-studio-error-cleanup-" + uuid.uuid4().hex
    handle = dll.CreateEventW(None, True, False, name)
    assert handle
    return dll, handle, name


@pytest.mark.parametrize("count", [2, 3])
@pytest.mark.parametrize("concurrent_close", [False, True])
def test_authenticated_error_rejects_tail_and_reads_real_eof(
    episode_sensor, monkeypatch, count, concurrent_close
):
    dll, event, name = native_event()
    channel = transport_channel(episode_sensor, count, "error", name)
    worker, mux = channel.worker, channel.worker._mux
    pipe = ReadObserver(worker.process.stdout)
    worker.process.stdout = pipe
    first, tail = threading.Event(), threading.Event()
    admitted, rejected, wake_states, errors, results, close_errors = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    original_deliver, original_get, original_put = (
        mux.deliver,
        runtime.queue.Queue.get,
        runtime.queue.Queue.put,
    )

    def deliver(frame):
        try:
            original_deliver(frame)
            admitted.append(dict(frame))
            if frame["lane"] == "read" and frame["index"] == 0:
                first.set()
        except ValueError as error:
            rejected.append((dict(frame), str(error)))
            if frame.get("lane") == "read" and frame.get("type") == "result":
                tail.set()
            raise

    def get(slot, *args, **kwargs):
        if any(lane == "read" and s is slot for (lane, _), s in mux.slots.items()):
            assert tail.wait(1), "native tail was never logically rejected"
        return original_get(slot, *args, **kwargs)

    def put(slot, value, *args, **kwargs):
        if isinstance(value, dict) and value.get("type") == "error":
            wake_states.append((mux.live, str(mux.failure)))
        return original_put(slot, value, *args, **kwargs)

    monkeypatch.setattr(mux, "deliver", deliver)
    monkeypatch.setattr(runtime.queue.Queue, "get", get)
    monkeypatch.setattr(runtime.queue.Queue, "put", put)
    deadline = time.perf_counter_ns() + 2_000_000_000

    def read():
        try:
            results.append(worker.call({"operation": "status"}, deadline_ns=deadline))
        except process.WorkerFailure as error:
            errors.append(error)

    def close():
        if tail.wait(1):
            try:
                worker.close(graceful=False)
            except process.WorkerFailure as error:
                close_errors.append(error)

    reader = threading.Thread(target=read)
    closer = threading.Thread(target=close) if concurrent_close else None
    reader.start()
    if closer:
        closer.start()
    try:
        assert first.wait(1)
        assert dll.SetEvent(event)
        reader.join(timeout=2)
        if closer:
            closer.join(timeout=1)
        assert not reader.is_alive() and not results and not close_errors
        assert len(errors) == 1 and str(errors[0]) == "native_protocol_error"
        failure = errors[0]
        assert len(failure.progress) == 1
        assert failure.progress[0]["payload"] == {"step": 0, "chunk": "x" * 1200}
        assert failure.partial_raw == failure.progress[0]["payload"]
        assert [f["type"] for f in admitted if f["lane"] == "read"] == [
            "progress",
            "error",
        ]
        assert rejected[-1][0]["type"] == "result"
        assert all(
            "reordered" in reason or "revoked" in reason for _, reason in rejected
        )
        receipt = worker.close_evidence
        assert receipt["resources_returned"]
        assert receipt["reader_eof"] and receipt["reader_joined"]
        assert receipt["original_ownership_verified"] and receipt["job_empty"]
        assert receipt["ownership"]["pid"] == worker.pid
        assert receipt["ownership"]["creation_time"] > 0
        assert receipt["ownership"]["job_member"]
        assert pipe.reads[-1] == (worker.reader.name, b"")
        assert any(
            process.decode(data).get("type") == "result"
            for _, data in pipe.reads
            if data
        )
        assert wake_states == [(False, "native_protocol_error")]
        assert failure.evidence["cleanup"] is receipt
        assert time.perf_counter_ns() < deadline
        snapshot = process.encode(failure.progress)
        worker.close(graceful=False)
        assert worker.close_evidence is receipt
        assert process.encode(failure.progress) == snapshot
        assert str(failure) == "native_protocol_error"
    finally:
        dll.SetEvent(event)
        channel.close()
        reader.join(timeout=2)
        if closer:
            closer.join(timeout=1)
        assert dll.CloseHandle(event)


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("malformed", "invalid_reply_type"),
        ("mac", "frame_authentication_failed"),
        ("replay", "stale_or_reordered_reply"),
        ("quota65", "progress_limit"),
        ("binding", "frame_session_binding_invalid"),
        ("lane", "foreign_or_replayed_reply"),
    ],
)
def test_preterminal_rejection_keeps_unknown_quarantine(episode_sensor, mode, reason):
    dll, event, name = native_event()
    channel = transport_channel(
        episode_sensor, 65 if mode == "quota65" else 2, mode, name
    )
    worker = channel.worker
    pipe = ReadObserver(worker.process.stdout)
    worker.process.stdout = pipe
    try:
        assert dll.SetEvent(event)
        with pytest.raises(process.WorkerFailure, match=reason) as caught:
            worker.call(
                {"operation": "status"},
                deadline_ns=time.perf_counter_ns() + 2_000_000_000,
            )
        receipt = worker.close_evidence
        assert receipt["job_empty"]
        assert receipt["disposition"] == "UNKNOWN_QUARANTINED"
        assert not receipt["resources_returned"] and not receipt["reader_eof"]
        assert not any(data == b"" for _, data in pipe.reads)
        assert len(caught.value.progress) == (64 if mode == "quota65" else 1)
        assert caught.value.evidence["cleanup"] is receipt
        worker.close(graceful=False)
        assert worker.close_evidence is receipt
    finally:
        channel.close()
        assert dll.CloseHandle(event)
