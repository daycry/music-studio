"""Casos de custodia CPU con instancias privadas por caso."""

import importlib.util
import os
import pathlib
import platform
import sys
import threading
import types
import uuid

import pytest

WINDOWS_X64 = (
    os.name == "nt"
    and sys.platform == "win32"
    and sys.maxsize == 2**63 - 1
    and platform.machine().casefold() in {"amd64", "x86_64"}
)
native_windows = pytest.mark.skipif(
    not WINDOWS_X64, reason="Windows AMD64 real requerido; no positivo fingido"
)

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"


def load(name="io"):
    key = "k1_" + name + "_" + uuid.uuid4().hex
    package = types.ModuleType(key)
    package.__path__ = [str(SCRIPTS)]
    sys.modules[key] = package
    spec = importlib.util.spec_from_file_location(
        key + ".storage_journal_windows_" + name,
        SCRIPTS / ("storage_journal_windows_" + name + ".py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Blocks:
    def __init__(self, m):
        self.m = m
        self.blocks = {}
        self.calls = []
        self.next = 65539

    def allocate(self, size):
        base = self.next
        self.next += size + 65536
        self.blocks[base] = bytearray(size)
        self.calls.append(("allocate", base, size))
        return self.m._AllocResult(base)

    def release(self, base):
        self.calls.append(("release", base))
        del self.blocks[base]
        return self.m._BoolResult(True)

    def locate(self, address):
        for base, block in self.blocks.items():
            if base <= address <= base + len(block):
                return block, address - base
        raise AssertionError("double: address fuera de bloque propio")

    def copy_in(self, address, data):
        self.calls.append(("copy_in", len(data)))
        block, offset = self.locate(address)
        block[offset : offset + len(data)] = data

    def copy_out(self, address, length):
        self.calls.append(("copy_out", length))
        block, offset = self.locate(address)
        return bytes(block[offset : offset + length])

    def ops(self):
        return self.m._MemoryOps(
            self.allocate, self.release, self.copy_in, self.copy_out
        )


def setup():
    m = load()
    b = Blocks(m)
    c = m._assemble_memory_context(b.ops(), provenance="cpu_double")
    return m, b, c


@pytest.mark.parametrize("machine", ["arm64", "x86", "unknown"])
def test_unsupported_gate_before_loader(monkeypatch, machine):
    m = load()
    monkeypatch.setattr(m.platform, "machine", lambda: machine)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._new_memory_context()
    assert caught.value.diagnostic.code == "PLATFORM_UNSUPPORTED"


def test_requested_alignment_and_quota():
    m, b, c = setup()
    a = m._allocate_aligned(c, length=131072, alignment=65536)
    assert m._arena_info(c, a) == m.ArenaInfo(131072, 65536, "live", "cpu_double")
    assert b.calls == [("allocate", 65539, 196607)]
    for _ in range(7):
        m._allocate_aligned(c, length=512, alignment=512)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic.code == "ARENA_LIMIT"
    assert sum(call[0] == "allocate" for call in b.calls) == 8


@pytest.mark.parametrize(
    "length,alignment,code",
    [
        (True, 512, "INTEGER_INVALID"),
        (513, 512, "ALIGNMENT_INVALID"),
        (512, 513, "ALIGNMENT_INVALID"),
        (0, 512, "RANGE_INVALID"),
        (1179648, 65536, "ARENA_LIMIT"),
    ],
)
def test_allocate_rejected_before_entry(length, alignment, code):
    m, b, c = setup()
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=length, alignment=alignment)
    assert caught.value.diagnostic.code == code
    assert b.calls == []


def test_overflow_helper():
    m = load()
    assert m._checked_reservation_size(512, 512, 1024) == 1023
    with pytest.raises(m.KernelMemoryError) as caught:
        m._checked_reservation_size(1024, 512, 1024)
    assert caught.value.diagnostic.code == "OVERFLOW"


@pytest.mark.parametrize("fake", [None, {}, True, 0, -1])
def test_capability_identity(fake):
    m, b, c = setup()
    with pytest.raises(m.KernelMemoryError) as caught:
        m._arena_info(c, fake)
    assert caught.value.diagnostic.code == "CAPABILITY_INVALID"
    assert b.calls == []


def test_alloc_null_rolls_back_then_succeeds():
    m = load()
    b = Blocks(m)

    def alloc(size):
        b.calls.append(("null", size))
        return m._AllocResult(None, 8)

    c = m._assemble_memory_context(
        m._MemoryOps(alloc, b.release, b.copy_in, b.copy_out), provenance="cpu_double"
    )
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic == m.FailureDiagnostic(
        "ALLOCATION_FAILED", "allocate", 8
    )
    assert m._LIVE_MEMORY_CONTEXTS[c].charge == (0, 0, 0)
    m._LIVE_MEMORY_CONTEXTS[c].ops = b.ops()
    a = m._allocate_aligned(c, length=512, alignment=512)
    assert m._arena_info(c, a).state == "live"


@pytest.mark.parametrize("result", [None, True, 0, -1, 2**64])
def test_alloc_invalid_completion_quarantined(result):
    m = load()
    b = Blocks(m)

    def alloc(size):
        return result if result is None else m._AllocResult(result)

    c = m._assemble_memory_context(
        m._MemoryOps(alloc, b.release, b.copy_in, b.copy_out), provenance="cpu_double"
    )
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    assert m._KERNEL_POISONED
    assert c in m._QUARANTINED_MEMORY_CONTEXTS
    assert m._LIVE_MEMORY_CONTEXTS[c].charge == (1, 512, 1023)
    assert not any(call[0] == "release" for call in b.calls)


@pytest.mark.parametrize("seam", ["_acknowledge_result", "_register_allocation"])
def test_return_registration_interruption(monkeypatch, seam):
    m, b, c = setup()

    def cut(*args):
        raise KeyboardInterrupt("SECRET-PATH-ADDRESS")

    monkeypatch.setattr(m, seam, cut)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    record = m._LIVE_MEMORY_CONTEXTS[c]
    assert record.inflight and record.charge == (1, 512, 1023)
    assert c in m._QUARANTINED_MEMORY_CONTEXTS
    assert [x[0] for x in b.calls] == ["allocate"]
    assert "SECRET" not in str(caught.value)


def test_alloc_entered_before_backend():
    m = load()
    holder = {}

    def allocate(size):
        record = m._LIVE_MEMORY_CONTEXTS[holder["context"]]
        assert record.inflight[-1].operation == "allocate"
        assert record.charge == (1, 512, 1023)
        raise RuntimeError("SECRET")

    b = Blocks(m)
    c = m._assemble_memory_context(
        m._MemoryOps(allocate, b.release, b.copy_in, b.copy_out),
        provenance="cpu_double",
    )
    holder["context"] = c
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    assert len(m._LIVE_MEMORY_CONTEXTS[c].inflight) == 1


def test_copy_exact_independent_and_zero_boundary():
    m, _b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    data = bytes(range(256)) * 2
    m._arena_copy_in(c, a, offset=0, data=data)
    copied = m._arena_copy_out(c, a, offset=0, length=512)
    assert type(copied) is bytes and copied == data and copied is not data
    m._arena_copy_in(c, a, offset=0, data=b"x")
    assert copied == data
    m._arena_copy_in(c, a, offset=512, data=b"")
    assert m._arena_copy_out(c, a, offset=512, length=0) == b""


@pytest.mark.parametrize(
    "offset,data,code",
    [
        (-1, b"a", "RANGE_INVALID"),
        (513, b"", "RANGE_INVALID"),
        (511, b"ab", "RANGE_INVALID"),
        (True, b"a", "INTEGER_INVALID"),
        (0, bytearray(b"a"), "INTEGER_INVALID"),
        (0, memoryview(b"a"), "INTEGER_INVALID"),
    ],
)
def test_copy_in_rejects_without_backend(offset, data, code):
    m, b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    before = list(b.calls)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._arena_copy_in(c, a, offset=offset, data=data)
    assert caught.value.diagnostic.code == code
    assert b.calls == before


def test_copy_unknown_retains_and_retires():
    m = load()
    b = Blocks(m)

    def copy_out(address, length):
        return bytearray(length)

    c = m._assemble_memory_context(
        m._MemoryOps(b.allocate, b.release, b.copy_in, copy_out),
        provenance="cpu_double",
    )
    a = m._allocate_aligned(c, length=512, alignment=512)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._arena_copy_out(c, a, offset=0, length=1)
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    assert m._arena_info(c, a).state == "unknown"
    with pytest.raises(m.KernelMemoryError, match="OWNER_RETIRE_REQUIRED"):
        m._allocate_aligned(c, length=512, alignment=512)


def test_close_revoke_original_base_stable():
    m, b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    original = b.calls[0][1]
    outcome = m._close_arena(c, a)
    assert outcome == m.CloseOutcome("closed")
    assert m._close_arena(c, a) is outcome
    assert b.calls == [("allocate", original, 1023), ("release", original)]
    assert m._arena_info(c, a).state == "closed"
    assert m._LIVE_MEMORY_CONTEXTS[c].charge == (0, 0, 0)
    with pytest.raises(m.KernelMemoryError, match="CAPABILITY_REVOKED"):
        m._arena_copy_out(c, a, offset=0, length=0)


@pytest.mark.parametrize("mode", ["false", "none", "raise", "interrupt", "after_true"])
def test_close_uncertainty_never_retry(monkeypatch, mode):
    m = load()
    b = Blocks(m)
    holder = {}
    calls = []

    def release(base):
        calls.append(base)
        assert m._arena_info(holder["c"], holder["a"]).state == "revoked"
        if mode == "false":
            return m._BoolResult(False, 5)
        if mode == "none":
            return None
        if mode == "interrupt":
            raise KeyboardInterrupt("SECRET")
        if mode == "raise":
            raise RuntimeError("SECRET")
        return m._BoolResult(True)

    c = m._assemble_memory_context(
        m._MemoryOps(b.allocate, release, b.copy_in, b.copy_out),
        provenance="cpu_double",
    )
    a = m._allocate_aligned(c, length=512, alignment=512)
    sibling = m._allocate_aligned(c, length=512, alignment=512)
    holder.update(c=c, a=a)
    if mode == "after_true":
        old = m._acknowledge_result

        def cut(call, result):
            if call.operation == "close":
                raise KeyboardInterrupt("SECRET")
            old(call, result)

        monkeypatch.setattr(m, "_acknowledge_result", cut)
    outcome = m._close_arena(c, a)
    assert outcome.state == "unknown" and outcome.causes[0].code == "RESOURCE_UNKNOWN"
    assert m._close_arena(c, a) is outcome
    assert len(calls) == 1
    assert m._arena_info(c, sibling).state == "unknown"
    assert m._close_arena(c, sibling).state == "unknown" and len(calls) == 1
    assert "SECRET" not in repr(outcome)


def test_context_close_reverse_and_stable():
    m, b, c = setup()
    arenas = [m._allocate_aligned(c, length=512, alignment=512) for _ in range(3)]
    bases = [call[1] for call in b.calls]
    outcome = m._close_memory_context(c)
    assert outcome == m.CloseOutcome("closed")
    assert [call[1] for call in b.calls if call[0] == "release"] == bases[::-1]
    assert all(m._arena_info(c, a).state == "closed" for a in arenas)
    assert m._close_memory_context(c) is outcome


def test_context_close_stops_on_failure():
    m = load()
    b = Blocks(m)
    calls = []

    def release(base):
        calls.append(base)
        return m._BoolResult(len(calls) == 1, None if len(calls) == 1 else 5)

    c = m._assemble_memory_context(
        m._MemoryOps(b.allocate, release, b.copy_in, b.copy_out),
        provenance="cpu_double",
    )
    arenas = [m._allocate_aligned(c, length=512, alignment=512) for _ in range(3)]
    bases = [call[1] for call in b.calls]
    outcome = m._close_memory_context(c)
    assert outcome.state == "unknown"
    assert calls == bases[:0:-1]
    assert m._arena_info(c, arenas[2]).state == "closed"
    assert m._arena_info(c, arenas[0]).state == "unknown"
    assert m._close_memory_context(c) is outcome


@pytest.mark.parametrize("cleanup_good", [True, False])
def test_register_ordinary_rollback_primary_separate(monkeypatch, cleanup_good):
    m = load()
    b = Blocks(m)
    calls = []

    def release(base):
        calls.append(base)
        return m._BoolResult(cleanup_good, None if cleanup_good else 5)

    c = m._assemble_memory_context(
        m._MemoryOps(b.allocate, release, b.copy_in, b.copy_out),
        provenance="cpu_double",
    )

    def broken(*args):
        raise MemoryError("SECRET")

    monkeypatch.setattr(m, "_register_allocation", broken)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    assert caught.value.cleanup.state == ("closed" if cleanup_good else "unknown")
    assert calls == [b.calls[0][1]]
    assert m._LIVE_MEMORY_CONTEXTS[c].charge == (
        (0, 0, 0) if cleanup_good else (1, 512, 1023)
    )


def test_copy_close_serialized_and_close_rivals():
    m = load()
    b = Blocks(m)
    entered = threading.Event()
    proceed = threading.Event()
    close_started = threading.Event()
    finished = []
    errors = []

    def copying(address, data):
        entered.set()
        assert proceed.wait(5)
        b.copy_in(address, data)

    c = m._assemble_memory_context(
        m._MemoryOps(b.allocate, b.release, copying, b.copy_out),
        provenance="cpu_double",
    )
    a = m._allocate_aligned(c, length=512, alignment=512)

    def copy():
        try:
            m._arena_copy_in(c, a, offset=0, data=b"x")
        except BaseException as e:  # noqa: BLE001 - capturar fallo de thread para el supervisor
            errors.append(e)

    def close():
        close_started.set()
        try:
            finished.append(m._close_arena(c, a))
        except BaseException as e:  # noqa: BLE001 - capturar fallo de thread para el supervisor
            errors.append(e)

    t = threading.Thread(target=copy)
    t.start()
    assert entered.wait(5)
    u = threading.Thread(target=close)
    u.start()
    assert close_started.wait(5)
    # El lock es real: la llamada bloqueada retiene autoridad hasta terminar.
    lock = m._LIVE_MEMORY_CONTEXTS[c].lock
    assert not lock.acquire(blocking=False)
    proceed.set()
    t.join(5)
    u.join(5)
    assert not t.is_alive() and not u.is_alive() and not errors
    assert finished == [m.CloseOutcome("closed")]
    assert [call[0] for call in b.calls] == ["allocate", "copy_in", "release"]
    rivals = [threading.Thread(target=close) for _ in range(2)]
    for thread in rivals:
        thread.start()
    for thread in rivals:
        thread.join(5)
    assert len(finished) == 3 and all(x is finished[0] for x in finished)
    assert sum(call[0] == "release" for call in b.calls) == 1


def test_pid_and_owner_mismatch_before_backend(monkeypatch):
    m, b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    other = m._assemble_memory_context(b.ops(), provenance="cpu_double")
    before = list(b.calls)
    with pytest.raises(m.KernelMemoryError, match="OWNER_MISMATCH"):
        m._arena_copy_out(other, a, offset=0, length=1)
    monkeypatch.setattr(m.os, "getpid", lambda: -1)
    with pytest.raises(m.KernelMemoryError, match="OWNER_MISMATCH"):
        m._arena_copy_out(c, a, offset=0, length=1)
    assert b.calls == before


@pytest.mark.parametrize(
    "args",
    [
        ("SECRET", "close", None, None),
        ("RESOURCE_UNKNOWN", "SECRET", None, None),
        ("RESOURCE_UNKNOWN", "close", True, None),
        ("RESOURCE_UNKNOWN", "close", 2**32, None),
        ("RESOURCE_UNKNOWN", "close", None, 1),
    ],
)
def test_diagnostic_enums_closed(args):
    m = load()
    with pytest.raises((ValueError, TypeError), match="DIAGNOSTIC_INVALID"):
        m.FailureDiagnostic(*args)


@pytest.mark.parametrize("alignment", [512, 4096, 65536])
@native_windows
def test_native_own_memory_positive(alignment, record_property):
    m = load()
    c = m._new_memory_context()
    assert type(c) is m._MemoryContext
    a = m._allocate_aligned(c, length=alignment * 2, alignment=alignment)
    data = bytes(range(256)) * (alignment * 2 // 256)
    m._arena_copy_in(c, a, offset=0, data=data)
    assert m._arena_copy_out(c, a, offset=0, length=len(data)) == data
    record = m._LIVE_MEMORY_CONTEXTS[c]
    allocation = record.allocations[a]
    native_ops = record.ops
    releases = []

    def release(base):
        releases.append(base == allocation.base)
        return native_ops.release(base)

    record.ops = m._MemoryOps(
        native_ops.allocate, release, native_ops.copy_in, native_ops.copy_out
    )
    assert allocation.address % alignment == 0
    assert allocation.base <= allocation.address < allocation.base + alignment
    assert allocation.requested == len(data) + alignment - 1
    assert m._arena_info(c, a).provenance == "native_windows_x64"
    assert m._close_arena(c, a) == m.CloseOutcome("closed")
    assert m._close_arena(c, a) == m.CloseOutcome("closed")
    assert m._close_memory_context(c) == m.CloseOutcome("closed")
    assert record.charge == (0, 0, 0) and not record.inflight
    assert releases == [True]
    record_property("alignment", alignment)
    record_property("requested_bytes", len(data) + alignment - 1)
    record_property("release_calls", len(releases))
    record_property("free_original_base", all(releases))
    record_property("native_memory_only", True)


def test_backend_kernel_error_still_uncertain():
    m = load()
    b = Blocks(m)

    def allocate(size):
        raise m.KernelMemoryError(
            m.FailureDiagnostic("ALLOCATION_FAILED", "allocate", 8)
        )

    c = m._assemble_memory_context(
        m._MemoryOps(allocate, b.release, b.copy_in, b.copy_out),
        provenance="cpu_double",
    )
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    assert c in m._QUARANTINED_MEMORY_CONTEXTS and m._KERNEL_POISONED


def test_global_poison_invalidates_other_contexts():
    m = load()
    b = Blocks(m)
    good = m._assemble_memory_context(b.ops(), provenance="cpu_double")
    empty = m._assemble_memory_context(b.ops(), provenance="cpu_double")
    a = m._allocate_aligned(good, length=512, alignment=512)

    def allocate(size):
        raise KeyboardInterrupt("SECRET")

    bad = m._assemble_memory_context(
        m._MemoryOps(allocate, b.release, b.copy_in, b.copy_out),
        provenance="cpu_double",
    )
    with pytest.raises(m.KernelMemoryError, match="RESOURCE_UNKNOWN"):
        m._allocate_aligned(bad, length=512, alignment=512)
    before = list(b.calls)
    assert m._arena_info(good, a).state == "unknown"
    assert m._close_memory_context(empty).state == "unknown"
    assert m._close_arena(good, a).state == "unknown"
    assert b.calls == before
    with pytest.raises(m.KernelMemoryError, match="OWNER_RETIRE_REQUIRED"):
        m._assemble_memory_context(b.ops(), provenance="cpu_double")


@pytest.mark.parametrize("kind", ["info", "outcome", "error", "provenance"])
def test_dto_invalid_inputs_sanitized(kind):
    m = load()
    b = Blocks(m)
    with pytest.raises((ValueError, TypeError, m.KernelMemoryError)) as caught:
        if kind == "info":
            m.ArenaInfo(512, 512, "SECRET", "cpu_double")
        elif kind == "outcome":
            m.CloseOutcome("closed", ("SECRET",))
        elif kind == "error":
            m.KernelMemoryError("SECRET")
        else:
            m._assemble_memory_context(b.ops(), provenance={"SECRET": 1})
    assert "SECRET" not in str(caught.value)


def test_forged_exact_subclass_copy_and_frozen():
    import copy
    from dataclasses import FrozenInstanceError

    m, _b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)

    class SubArena(m.AlignedArena):
        pass

    for fake in (object.__new__(m.AlignedArena), object.__new__(SubArena)):
        with pytest.raises(m.KernelMemoryError, match="CAPABILITY_INVALID"):
            m._arena_info(c, fake)
    with pytest.raises(m.KernelMemoryError, match="CAPABILITY_INVALID"):
        m._arena_info(object.__new__(m._MemoryContext), a)
    for cap in (a, c):
        with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
            type(cap)()
        with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
            copy.copy(cap)
        with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
            copy.deepcopy(cap)
        with pytest.raises(TypeError):
            int(cap)
        assert "65539" not in repr(cap)
    info = m._arena_info(c, a)
    with pytest.raises(FrozenInstanceError):
        info.state = "closed"
    assert m._arena_copy_out(c, a, offset=0, length=0) == b""


def test_eight_max_arenas_exact_requested_quota():
    m, b, c = setup()
    for _ in range(8):
        m._allocate_aligned(c, length=1114112, alignment=65536)
    assert m._LIVE_MEMORY_CONTEXTS[c].charge == (8, 8912896, 9437176)
    assert all(call[2] == 1179647 for call in b.calls)
    with pytest.raises(m.KernelMemoryError, match="ARENA_LIMIT"):
        m._allocate_aligned(c, length=512, alignment=512)
    assert len(b.calls) == 8
    assert m._close_memory_context(c).state == "closed"
    assert m._LIVE_MEMORY_CONTEXTS[c].charge == (0, 0, 0)


@pytest.mark.parametrize(
    "offset,length,code",
    [
        (True, 1, "INTEGER_INVALID"),
        (0, True, "INTEGER_INVALID"),
        (-1, 0, "RANGE_INVALID"),
        (513, 0, "RANGE_INVALID"),
        (511, 2, "RANGE_INVALID"),
        (0, -1, "RANGE_INVALID"),
    ],
)
def test_copy_out_invalid_range_controls(offset, length, code):
    m, b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    before = list(b.calls)
    with pytest.raises(m.KernelMemoryError, match=code):
        m._arena_copy_out(c, a, offset=offset, length=length)
    assert b.calls == before


@pytest.mark.parametrize(
    "op,mode",
    [
        ("copy_in", "raise"),
        ("copy_in", "bad_result"),
        ("copy_out", "raise"),
        ("copy_out", "short"),
        ("copy_out", "after_return"),
    ],
)
def test_copy_cut_custody(monkeypatch, op, mode):
    m = load()
    b = Blocks(m)

    def copy(*args):
        if mode == "raise":
            raise RuntimeError("SECRET")
        if op == "copy_in":
            return True
        return b"" if mode == "short" else b"x"

    ops = m._MemoryOps(
        b.allocate,
        b.release,
        copy if op == "copy_in" else b.copy_in,
        copy if op == "copy_out" else b.copy_out,
    )
    c = m._assemble_memory_context(ops, provenance="cpu_double")
    a = m._allocate_aligned(c, length=512, alignment=512)
    if mode == "after_return":
        old = m._acknowledge_result

        def ack(call, result):
            if call.operation == "copy_out":
                raise KeyboardInterrupt("SECRET")
            old(call, result)

        monkeypatch.setattr(m, "_acknowledge_result", ack)
    with pytest.raises(m.KernelMemoryError, match="RESOURCE_UNKNOWN") as caught:
        if op == "copy_in":
            m._arena_copy_in(c, a, offset=0, data=b"x")
        else:
            m._arena_copy_out(c, a, offset=0, length=1)
    assert caught.value.__suppress_context__
    assert m._LIVE_MEMORY_CONTEXTS[c].inflight[-1].operation == op
    assert m._close_arena(c, a).state == "unknown"
    assert not any(call[0] == "release" for call in b.calls)


@pytest.mark.parametrize(
    "failure", ["invalid_error", "missing_error", "range_overflow"]
)
def test_allocation_completion_controls(failure):
    m = load()
    b = Blocks(m)

    def alloc(size):
        if failure == "invalid_error":
            return m._AllocResult(None, True)
        if failure == "missing_error":
            return m._AllocResult(None, None)
        return m._AllocResult(2**64 - 512)

    c = m._assemble_memory_context(
        m._MemoryOps(alloc, b.release, b.copy_in, b.copy_out), provenance="cpu_double"
    )
    with pytest.raises(m.KernelMemoryError, match="RESOURCE_UNKNOWN"):
        m._allocate_aligned(c, length=512, alignment=512)
    assert m._KERNEL_POISONED and c in m._QUARANTINED_MEMORY_CONTEXTS
    assert b.calls == []


@pytest.mark.parametrize(
    "part,value",
    [
        ("os", "posix"),
        ("platform", "linux"),
        ("maxsize", 2**31 - 1),
        ("machine", "arm64"),
    ],
)
def test_factory_unsupported_blocks_ctypes_import(monkeypatch, part, value):
    import builtins

    for name in ("io", "abi"):
        m = load(name)
        m.os = types.SimpleNamespace(
            name=value if part == "os" else "nt", getpid=lambda: 1
        )
        m.sys = types.SimpleNamespace(
            platform=value if part == "platform" else "win32",
            maxsize=value if part == "maxsize" else 2**63 - 1,
        )
        m.platform = types.SimpleNamespace(
            machine=lambda: value if part == "machine" else "AMD64"
        )
        calls = []
        original = builtins.__import__

        def guarded(name, *args, _calls=calls, _original=original, **kwargs):
            if name == "ctypes":
                _calls.append(name)
                raise AssertionError("loader prohibido")
            return _original(name, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(builtins, "__import__", guarded)
            with pytest.raises(Exception, match="PLATFORM_UNSUPPORTED"):
                (
                    m._new_memory_context
                    if name == "io"
                    else m._new_native_memory_backend
                )()
        assert calls == []


def test_module_imports_are_pure(monkeypatch):
    import builtins

    seen = []
    original = builtins.__import__

    def guard(name, *args, **kwargs):
        if name == "ctypes":
            seen.append(name)
            raise AssertionError("ctypes al importar")
        return original(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", guard)
        load("io")
        load("abi")
    assert seen == []


@native_windows
def test_factory_abi_error_sanitized_before_resources():
    m = load()

    def failed(*args):
        raise OSError("SECRET")

    m.importlib = types.SimpleNamespace(import_module=failed)
    with pytest.raises(m.KernelMemoryError, match="ABI_UNACCREDITED") as caught:
        m._new_memory_context()
    assert caught.value.__suppress_context__ and "SECRET" not in str(caught.value)
    assert not m._LIVE_MEMORY_CONTEXTS


@native_windows
def test_poison_blocks_native_factory_before_binder():
    m = load()
    b = Blocks(m)

    def failed(size):
        raise RuntimeError("SECRET")

    c = m._assemble_memory_context(
        m._MemoryOps(failed, b.release, b.copy_in, b.copy_out), provenance="cpu_double"
    )
    with pytest.raises(m.KernelMemoryError, match="RESOURCE_UNKNOWN"):
        m._allocate_aligned(c, length=512, alignment=512)
    seen = []
    m.importlib = types.SimpleNamespace(import_module=lambda *args: seen.append(args))
    with pytest.raises(m.KernelMemoryError, match="OWNER_RETIRE_REQUIRED"):
        m._new_memory_context()
    assert seen == []


def test_context_close_interruption_retained(monkeypatch):
    m, b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    before = list(b.calls)

    def cut(*args):
        raise KeyboardInterrupt("SECRET")

    monkeypatch.setattr(m, "_close_owned", cut)
    result = m._close_memory_context(c)
    assert result.state == "unknown" and result.causes[0].operation == "context_close"
    assert m._LIVE_MEMORY_CONTEXTS[c].inflight[-1].operation == "context_close"
    assert m._close_memory_context(c) is result
    assert m._arena_info(c, a).state == "unknown" and b.calls == before


@pytest.mark.parametrize("path", ["arena", "context", "rollback"])
@pytest.mark.parametrize(
    "cut",
    ["constructor", "charge_before", "charge_after", "remove_before", "remove_after"],
)
def test_fix1_release_finalization_cut(monkeypatch, path, cut):
    m, b, c = setup()
    record = m._LIVE_MEMORY_CONTEXTS[c]
    if path != "rollback":
        a = m._allocate_aligned(c, length=512, alignment=512)
    old_charge = m._charge
    old_post = m.CloseOutcome.__post_init__
    triggered = []

    def interrupt():
        triggered.append(True)
        raise KeyboardInterrupt("FIX1_SECRET")

    def charge(r, count, logical, requested):
        if count == -1 and cut == "charge_before":
            interrupt()
        old_charge(r, count, logical, requested)
        if count == -1 and cut == "charge_after":
            interrupt()

    def post(outcome):
        old_post(outcome)
        if outcome.state == "closed" and cut == "constructor":
            interrupt()

    class CutList(list):
        def remove(self, call):
            if call.operation == "close" and cut == "remove_before":
                interrupt()
            super().remove(call)
            if call.operation == "close" and cut == "remove_after":
                interrupt()

    monkeypatch.setattr(m, "_charge", charge)
    monkeypatch.setattr(m.CloseOutcome, "__post_init__", post)
    record.inflight = CutList(record.inflight)
    if path == "rollback":

        def broken(*args):
            raise MemoryError("FIX1_PRIMARY")

        monkeypatch.setattr(m, "_register_allocation", broken)
        with pytest.raises(m.KernelMemoryError) as caught:
            m._allocate_aligned(c, length=512, alignment=512)
        assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
        outcome = caught.value.cleanup
        a = next(iter(record.allocations))
    else:
        result = m._close_arena(c, a) if path == "arena" else m._close_memory_context(c)
        outcome = record.allocations[a].outcome
        assert result.state == "unknown"
    assert triggered == [True]
    assert outcome.state == "unknown"
    assert m._close_arena(c, a) is outcome
    assert m._arena_info(c, a).state == "unknown"
    assert record.state == "unknown" and m._KERNEL_POISONED
    assert m._QUARANTINED_MEMORY_CONTEXTS[c] is record
    assert record.charge == (1, 512, 1023)
    assert any(call.operation == "close" for call in record.inflight)
    assert sum(call[0] == "release" for call in b.calls) == 1
    assert m._close_memory_context(c).state == "unknown"
    assert sum(call[0] == "release" for call in b.calls) == 1
    assert "FIX1_SECRET" not in repr(outcome)


@pytest.mark.parametrize(
    "cut", ["state_before", "state_after", "outcome_before", "outcome_after"]
)
@pytest.mark.parametrize("target", ["arena", "context"])
def test_fix1_publication_cut(monkeypatch, target, cut):
    m, b, c = setup()
    a = m._allocate_aligned(c, length=512, alignment=512)
    record = m._LIVE_MEMORY_CONTEXTS[c]
    allocation = record.allocations[a]
    victim = allocation if target == "arena" else record
    original = type(victim)
    triggered = []

    class CutRecord(original):
        def __setattr__(self, name, value):
            chosen = (
                name == "state" and value == "closed" and cut.startswith("state")
            ) or (
                name == "outcome"
                and value is not None
                and value.state == "closed"
                and cut.startswith("outcome")
            )
            if chosen and not triggered and cut.endswith("before"):
                triggered.append(True)
                raise KeyboardInterrupt("FIX1_SECRET")
            super().__setattr__(name, value)
            if chosen and not triggered and cut.endswith("after"):
                triggered.append(True)
                raise KeyboardInterrupt("FIX1_SECRET")

    victim.__class__ = CutRecord
    outcome = m._close_arena(c, a) if target == "arena" else m._close_memory_context(c)
    assert triggered == [True]
    assert outcome.state == "unknown"
    assert victim.state == "unknown"
    assert victim.outcome is outcome
    assert record.state == "unknown" and m._KERNEL_POISONED
    assert m._QUARANTINED_MEMORY_CONTEXTS[c] is record
    if target == "arena":
        assert record.charge == (1, 512, 1023)
        assert m._arena_info(c, a).state == "unknown"
        assert m._close_arena(c, a) is outcome
    else:
        assert record.charge == (0, 0, 0)
        assert m._arena_info(c, a).state == "closed"
        assert m._close_memory_context(c) is outcome
    assert sum(call[0] == "release" for call in b.calls) == 1


@pytest.mark.parametrize("after", [False, True])
def test_fix1_rollback_acquisition_removal_cut(monkeypatch, after):
    m, b, c = setup()
    record = m._LIVE_MEMORY_CONTEXTS[c]
    triggered = []

    class CutList(list):
        def remove(self, call):
            if call.operation == "allocate":
                if after:
                    super().remove(call)
                triggered.append(True)
                raise KeyboardInterrupt("FIX1_SECRET")
            super().remove(call)

    record.inflight = CutList()

    def broken(*args):
        raise MemoryError("FIX1_PRIMARY")

    monkeypatch.setattr(m, "_register_allocation", broken)
    with pytest.raises(m.KernelMemoryError) as caught:
        m._allocate_aligned(c, length=512, alignment=512)
    assert triggered == [True]
    assert caught.value.diagnostic.code == "RESOURCE_UNKNOWN"
    assert caught.value.cleanup is not None
    assert caught.value.cleanup.state == "unknown"
    a = next(iter(record.allocations))
    assert m._arena_info(c, a).state == "unknown"
    assert m._close_arena(c, a) is caught.value.cleanup
    assert record.charge == (1, 512, 1023)
    assert {call.operation for call in record.inflight} == {"allocate", "close"}
    assert any(isinstance(call.error, MemoryError) for call in record.inflight)
    assert m._QUARANTINED_MEMORY_CONTEXTS[c] is record
    assert sum(call[0] == "release" for call in b.calls) == 1
