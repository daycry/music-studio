"""Presupuesto de copia sobre bytes reales y reloj monotónico controlado."""

import hashlib
import json
from itertools import pairwise
from pathlib import Path

import pytest

RATE = 128 * 1024**2
CHUNK = 8 * 1024**2


class Clock:
    def __init__(self, early_returns=False):
        self.ns = 0
        self.sleeps = []
        self.early_returns = early_returns
        self.events = []
        self.failure = None
        self.slow_sync_ns = 0

    def monotonic_ns(self):
        return self.ns

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        elapsed = round(seconds * 1e9)
        if self.early_returns and len(self.sleeps) == 1:
            elapsed = 0
        elif self.early_returns and len(self.sleeps) == 2:
            elapsed //= 2
        self.ns += elapsed


@pytest.fixture
def paced_storage(harness_module, tmp_path, monkeypatch):
    storage = harness_module("benchmark_storage")
    clock = Clock()
    source = tmp_path / "source"
    target = tmp_path / ".cache/copy"
    components = []
    # Dos archivos con bloque completo y cola: el presupuesto incluye el lock.
    for index in range(2):
        blob = bytes([index + 1]) * (CHUNK + 123)
        directory = source / f"ace-step-1.5/checkpoints/dit{index}"
        directory.mkdir(parents=True)
        (directory / "safe.safetensors").write_bytes(blob)
        components.append(
            {
                "id": f"dit{index}",
                "dest_subdir": f"dit{index}",
                "files": [
                    {
                        "path": "safe.safetensors",
                        "format": "safetensors",
                        "bytes": len(blob),
                        "sha256": hashlib.sha256(blob).hexdigest(),
                    }
                ],
            }
        )
    (source / "models.lock.json").write_text(
        json.dumps({"models": {"ace-step-1.5": {"components": components}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    monkeypatch.setattr(storage.time, "monotonic_ns", clock.monotonic_ns)
    monkeypatch.setattr(storage.time, "perf_counter_ns", clock.monotonic_ns)
    monkeypatch.setattr(storage.time, "sleep", clock.sleep)
    original_open = Path.open
    original_fsync = storage.os.fsync
    writes = []
    pauses = {}
    slow_writes = {}
    descriptors = {}

    def sync_event(operation, path):
        if clock.failure == (operation, len(writes) - 1):
            raise OSError(f"injected_{operation}_failure")
        clock.events.append((operation, path))

    class Writer:
        def __init__(self, stream, path):
            self.stream = stream
            self.path = path

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, chunk):
            start = clock.ns
            result = self.stream.write(chunk)
            clock.ns += slow_writes.get(len(writes), 0)
            writes.append((self.path, len(chunk), start, clock.ns))
            clock.events.append(("write", self.path))
            return result

        def flush(self):
            sync_event("flush", self.path)
            return self.stream.flush()

        def fileno(self):
            descriptor = self.stream.fileno()
            descriptors[descriptor] = self.path
            return descriptor

    def fsync(descriptor):
        sync_event("fsync", descriptors[descriptor])
        result = original_fsync(descriptor)
        clock.ns += clock.slow_sync_ns
        return result

    def open_file(path, mode="r", *args, **kwargs):
        stream = original_open(path, mode, *args, **kwargs)
        if mode == "xb" and path.is_relative_to(target):
            relative = path.relative_to(target).as_posix()
            clock.ns += pauses.get(relative, 0)
            return Writer(stream, relative)
        return stream

    monkeypatch.setattr(Path, "open", open_file)
    monkeypatch.setattr(storage.os, "fsync", fsync)
    return storage, clock, source, target, writes, pauses, slow_writes


def prepare(fixture):
    storage, _, source, target, *_ = fixture
    return storage.prepare_storage(source, target, ["dit0", "dit1"])


def assert_paced(writes, finished_ns):
    for current, following in pairwise(writes):
        required_ns = (current[1] * 10**9 + RATE - 1) // RATE
        assert following[2] - current[2] >= required_ns, (
            "La siguiente escritura empieza antes de consumir su presupuesto"
        )
    assert finished_ns - writes[-1][2] >= (writes[-1][1] * 10**9 + RATE - 1) // RATE


def test_copy_paces_every_chunk_across_files_and_preserves_hashes(paced_storage):
    storage, clock, source, target, writes, *_ = paced_storage
    hashes = []
    original_hash = storage.file_hash

    def record_hash(path):
        hashes.append(path)
        return original_hash(path)

    storage.file_hash = record_hash
    try:
        receipt = prepare(paced_storage)
    finally:
        storage.file_hash = original_hash
    assert_paced(writes, clock.ns)
    assert len(writes) == 5 and max(write[1] for write in writes) == CHUNK
    for record in receipt["files"]:
        relative = record["relative"]
        assert (source / relative).read_bytes() == (target / relative).read_bytes()
        assert source / relative in hashes and target / relative in hashes
    assert receipt["source_lock_sha256"] == receipt["destination_lock_sha256"]
    assert receipt["copy_s"] == clock.ns / 1e9
    assert receipt["copy_s"] >= sum(write[1] for write in writes) / RATE


def test_receipt_declares_copy_policy_rate_and_chunk(paced_storage):
    receipt = prepare(paced_storage)
    assert receipt.get("copy_policy") == "monotonic_bounded_sync_v2"
    assert receipt["copy_rate_bytes_per_s"] == RATE
    assert receipt["copy_chunk_bytes"] == CHUNK


def test_prior_and_between_file_pauses_do_not_credit_later_writes(paced_storage):
    _, clock, _, _, writes, pauses, _ = paced_storage
    clock.ns = 20 * 10**9
    pauses["ace-step-1.5/checkpoints/dit1/safe.safetensors"] = 7 * 10**9
    prepare(paced_storage)
    assert_paced(writes, clock.ns)
    assert writes[3][2] - writes[2][2] >= 7 * 10**9
    assert writes[4][2] - writes[3][2] >= CHUNK * 10**9 // RATE


def test_short_and_spurious_sleep_returns_recheck_deadline(paced_storage):
    _, clock, _, _, writes, *_ = paced_storage
    clock.early_returns = True
    prepare(paced_storage)
    assert_paced(writes, clock.ns)
    assert len(clock.sleeps) >= len(writes) + 2


def test_slow_write_does_not_credit_the_following_chunk(paced_storage):
    _, clock, _, _, writes, _, slow_writes = paced_storage
    slow_writes[0] = 3 * 10**9
    prepare(paced_storage)
    assert_paced(writes, clock.ns)
    assert writes[1][2] == writes[0][3]
    assert writes[2][2] - writes[1][2] >= CHUNK * 10**9 // RATE


def test_bind_does_not_copy_or_sleep_and_declares_no_copy_policy(paced_storage):
    storage, clock, source, _, writes, *_ = paced_storage
    receipt = storage.prepare_storage(source, source, ["dit0", "dit1"])
    assert clock.sleeps == [] and writes == []
    assert clock.events == []
    assert receipt["storage"] == "bind" and receipt["copy_s"] == 0
    for field in ("copy_policy", "copy_rate_bytes_per_s", "copy_chunk_bytes"):
        assert field in receipt and receipt[field] is None


def test_destination_verification_still_rejects_corrupt_copied_bytes(
    paced_storage, monkeypatch
):
    storage, _, _, target, *_ = paced_storage
    original_verify = storage.verify_selected

    def corrupt_destination(path, components):
        if path == target:
            (target / "ace-step-1.5/checkpoints/dit0/safe.safetensors").write_bytes(
                b"corrupt"
            )
        return original_verify(path, components)

    monkeypatch.setattr(storage, "verify_selected", corrupt_destination)
    with pytest.raises(ValueError, match="weights_mismatch"):
        prepare(paced_storage)


def test_copy_syncs_each_block_before_next_write_including_lock_and_tail(paced_storage):
    _, clock, source, target, writes, *_ = paced_storage
    receipt = prepare(paced_storage)
    expected = [
        (operation, path)
        for path, *_ in writes
        for operation in ("write", "flush", "fsync")
    ]
    assert clock.events == expected
    assert writes[0][0] == "models.lock.json"
    assert [write[1] for write in writes[1:]] == [CHUNK, 123, CHUNK, 123]
    assert (source / "models.lock.json").read_bytes() == (
        target / "models.lock.json"
    ).read_bytes()
    assert receipt["source_lock_sha256"] == receipt["destination_lock_sha256"]


@pytest.mark.parametrize("operation", ["flush", "fsync"])
@pytest.mark.parametrize("write_index", [0, 2, 4])
def test_sync_failure_propagates_without_valid_receipt(
    paced_storage, operation, write_index
):
    _, clock, _, _, writes, *_ = paced_storage
    clock.failure = (operation, write_index)
    receipt = None
    with pytest.raises(OSError, match=f"injected_{operation}_failure"):
        receipt = prepare(paced_storage)
    assert receipt is None
    assert len(writes) == write_index + 1
    assert clock.events[-1][0] == ("write" if operation == "flush" else "flush")


def test_slow_sync_is_in_copy_time_without_credit_for_following_chunks(paced_storage):
    _, clock, _, _, writes, *_ = paced_storage
    clock.slow_sync_ns = 3 * 10**9
    receipt = prepare(paced_storage)
    assert receipt["copy_s"] == clock.ns / 1e9
    assert receipt["copy_s"] >= len(writes) * 3
    assert_paced(writes, clock.ns)
    for current, following in pairwise(writes):
        assert following[2] - current[3] >= clock.slow_sync_ns
