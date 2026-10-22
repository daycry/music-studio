"""Lease nativa de recibos temporales, sin provisión ni datos del estudio."""
# ruff: noqa: SIM117 - los contextos distinguen operación y fallo esperado

import ctypes
import hashlib
import importlib.util
import os
import subprocess
import sys
from builtins import BaseExceptionGroup
from dataclasses import replace
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread, current_thread
from uuid import uuid4

import pytest
from studio_storage_guard.receipt import StorageReceipt

from scripts.storage_windows import CustodyError

PRIVATE = Path(__file__).resolve().parents[1]
SOURCE = PRIVATE / "scripts/storage_receipt_store.py"
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows nativo")


def module():
    assert SOURCE.is_file(), "ReceiptLease ausente: falta exclusión nativa del recibo"
    spec = importlib.util.spec_from_file_location("receipt_lease_candidate", SOURCE)
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


@pytest.fixture
def receipt():
    tmp_path = PRIVATE / ".cache/dev-cycle/m1/receipt-lease-tests" / uuid4().hex
    tmp_path.mkdir(parents=True)
    path = tmp_path / "nested/receipt.json"
    path.parent.mkdir()
    payload = StorageReceipt.reserve(
        project_root=tmp_path, operation_id="0" * 26, size_bytes=4096
    ).to_bytes()
    path.write_bytes(payload)
    return tmp_path, path, payload


def test_snapshot_same_handle(receipt, monkeypatch):
    root, path, payload = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    try:
        monkeypatch.setattr(
            Path, "read_bytes", lambda _: pytest.fail("pathname reopen")
        )
        snapshot = lease.read_snapshot()
        assert snapshot.payload == payload
        assert snapshot.receipt.to_bytes() == payload
        assert snapshot.identity == lease.revalidate().identity
        lease.assert_expected(payload)
    finally:
        lease.close()


@pytest.mark.parametrize(
    "action", ["write", "truncate", "replace", "rename", "delete", "parent"]
)
def test_native_rival_mutation_denied(receipt, action):
    root, path, payload = receipt
    code = """import os,sys
from pathlib import Path
p=Path(sys.argv[1]); action=sys.argv[2]
try:
 if action=='write': p.write_bytes(b'FOREIGN')
 elif action=='truncate': open(p,'wb').close()
 elif action=='replace':
  other=p.with_name('foreign');other.write_bytes(b'FOREIGN');os.replace(other,p)
 elif action=='rename': p.rename(p.with_name('renamed'))
 elif action=='delete': p.unlink()
 elif action=='parent': p.parent.rename(p.parent.with_name('moved'))
except OSError: sys.exit(0)
sys.exit(42)
"""
    with module().ReceiptLease.open_existing(root, path) as lease:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path), action], check=False
        )
        assert result.returncode == 0
        assert lease.read_snapshot().payload == payload
        assert path.read_bytes() == payload
    path.rename(path.with_name("after-close"))


def test_previous_writer_denies_acquisition(receipt):
    root, path, payload = receipt
    with path.open("r+b"):
        with pytest.raises(OSError):
            module().ReceiptLease.open_existing(root, path)
    assert path.read_bytes() == payload


def test_expected_stale_preserves_foreign(receipt):
    root, path, payload = receipt
    changed = payload.replace(b"4096", b"8192")
    path.write_bytes(changed)
    with module().ReceiptLease.open_existing(root, path) as lease:
        with pytest.raises(CustodyError):
            lease.assert_expected(payload)
        assert lease.read_snapshot().payload == changed
    assert path.read_bytes() == changed


def test_replacement_before_binding_rejected_by_expected(receipt):
    root, path, payload = receipt
    replacement = path.with_name("replacement")
    foreign = payload.replace(b"4096", b"8192")
    replacement.write_bytes(foreign)
    os.replace(replacement, path)
    with module().ReceiptLease.open_existing(root, path) as lease:
        with pytest.raises(CustodyError):
            lease.assert_expected(payload)
    assert path.read_bytes() == foreign


def test_hardlink_rejected(receipt):
    root, path, payload = receipt
    os.link(path, path.with_name("alias"))
    with pytest.raises(CustodyError):
        module().ReceiptLease.open_existing(root, path)
    assert path.read_bytes() == payload


def test_missing_rejected(receipt):
    root, path, payload = receipt
    with pytest.raises(OSError):
        module().ReceiptLease.open_existing(root, path.with_name("missing"))
    assert path.read_bytes() == payload


@pytest.mark.parametrize("kind", ["outside", "dot", "unc", "relative", "duplicate"])
def test_noncanonical_rejected(receipt, kind):
    root, path, payload = receipt
    candidate = {
        "outside": str(root.parent / "receipt.json"),
        "dot": str(path.parent) + "\\.\\receipt.json",
        "unc": "\\\\localhost\\c$\\receipt.json",
        "relative": "receipt.json",
        "duplicate": str(path.parent) + "\\\\receipt.json",
    }[kind]
    with pytest.raises(ValueError):
        module().ReceiptLease.open_existing(root, candidate)
    assert path.read_bytes() == payload


def test_closed_idempotent_and_read_rejected(receipt):
    root, path, _ = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    lease.close()
    lease.close()
    with pytest.raises(CustodyError):
        lease.read_snapshot()
    path.unlink()


def test_invalid_receipt_preserved(receipt):
    root, path, _ = receipt
    path.write_bytes(b"FOREIGN")
    with module().ReceiptLease.open_existing(root, path) as lease:
        with pytest.raises(ValueError):
            lease.read_snapshot()
    assert path.read_bytes() == b"FOREIGN"


def test_native_junction_rejected(receipt):
    root, path, payload = receipt
    junction = root / "junction"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(path.parent)],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    try:
        with pytest.raises(CustodyError):
            module().ReceiptLease.open_existing(root, junction / path.name)
        assert path.read_bytes() == payload
    finally:
        os.rmdir(junction)


def test_partial_open_failure_releases_handles(receipt, monkeypatch):
    root, path, payload = receipt
    api = module()
    original = api._ReceiptNative.inspect

    def fail(self, handle):
        metadata = original(self, handle)
        if metadata.final_path.endswith("receipt.json"):
            raise RuntimeError("injected inspect")
        return metadata

    monkeypatch.setattr(api._ReceiptNative, "inspect", fail)
    with pytest.raises(RuntimeError, match="injected inspect"):
        api.ReceiptLease.open_existing(root, path)
    path.rename(path.with_name("released"))
    assert path.with_name("released").read_bytes() == payload


def test_revalidate_detects_identity_change_mock(receipt, monkeypatch):
    root, path, _ = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    original = lease._native.inspect
    monkeypatch.setattr(
        lease._native,
        "inspect",
        lambda handle: replace(original(handle), volume_serial=123),
    )
    try:
        with pytest.raises(CustodyError):
            lease.revalidate()
    finally:
        lease.close()


def test_entry_failure_releases_handles(receipt, monkeypatch):
    root, path, _ = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    monkeypatch.setattr(
        lease, "revalidate", lambda: (_ for _ in ()).throw(RuntimeError("entry"))
    )
    with pytest.raises(RuntimeError, match="entry"):
        with lease:
            pytest.fail("entered after failure")
    path.unlink()


def test_cleanup_failure_preserves_primary_and_uncertainty(receipt, monkeypatch):
    root, path, _ = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    original = lease._native.close
    failed = lease._handles[-1][0]

    def fail(handle):
        if handle == failed:
            raise OSError("injected close uncertainty")
        return original(handle)

    monkeypatch.setattr(lease._native, "close", fail)
    with pytest.raises(BaseExceptionGroup) as error:
        with lease:
            raise RuntimeError("primary")
    assert "primary" in str(error.value.exceptions[0])
    assert "uncertain" in str(error.value.exceptions[1])
    assert lease._handles == []
    assert len(lease.close_uncertainties) == 1
    assert lease.close_uncertainties[0].path.endswith("receipt.json")
    with pytest.raises(BaseExceptionGroup):
        lease.close()
    # Sólo el test sabe que la inyección ocurrió ANTES del CloseHandle real.
    # El producto no recupera autoridad ni vuelve a usar un escalar incierto.
    original(failed)
    path.unlink()


def test_wrong_project_receipt_rejected_without_mutation(receipt):
    root, path, payload = receipt
    foreign = payload.replace(b"studio-data.vhdx", b"foreign.vhdx")
    path.write_bytes(foreign)
    with module().ReceiptLease.open_existing(root, path) as lease:
        with pytest.raises(CustodyError):
            lease.read_snapshot()
    assert path.read_bytes() == foreign


def test_read_failure_releases_on_context_exit(receipt, monkeypatch):
    root, path, _ = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    monkeypatch.setattr(
        lease._native,
        "read",
        lambda handle, size: (_ for _ in ()).throw(OSError("injected ReadFile")),
    )
    with pytest.raises(OSError, match="ReadFile"):
        with lease:
            lease.read_snapshot()
    path.unlink()


def test_uncertain_close_disables_lease(receipt, monkeypatch):
    root, path, _ = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    original = lease._native.close
    failed = lease._handles[-1][0]
    monkeypatch.setattr(
        lease._native,
        "close",
        lambda handle: (
            (_ for _ in ()).throw(OSError("uncertain"))
            if handle == failed
            else original(handle)
        ),
    )
    with pytest.raises(BaseExceptionGroup):
        lease.close()
    try:
        with pytest.raises(CustodyError, match="incierta"):
            lease.revalidate()
    finally:
        with pytest.raises(BaseExceptionGroup):
            lease.close()
        assert lease._handles == []
        # Witness propio cuya inyección no llamó al kernel; cleanup de test.
        original(failed)


def test_subprocess_previous_writer_denies_lease(receipt):
    root, path, payload = receipt
    code = "import sys; f=open(sys.argv[1], 'r+b'); print('ready',flush=True); sys.stdin.readline(); f.close()"
    rival = subprocess.Popen(
        [sys.executable, "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        output = Queue()
        Thread(target=lambda: output.put(rival.stdout.readline()), daemon=True).start()
        try:
            assert output.get(timeout=10).strip() == "ready"
        except Empty:
            pytest.fail("el escritor rival no acreditó arranque en 10 s")
        with pytest.raises(OSError):
            module().ReceiptLease.open_existing(root, path)
    finally:
        try:
            rival.communicate("close\n", timeout=10)
        except subprocess.TimeoutExpired:
            rival.kill()
            rival.communicate(timeout=10)
    assert rival.returncode == 0
    assert path.read_bytes() == payload


def test_reader_subprocess_allowed(receipt):
    root, path, payload = receipt
    with module().ReceiptLease.open_existing(root, path):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; from pathlib import Path; sys.stdout.buffer.write(Path(sys.argv[1]).read_bytes())",
                str(path),
            ],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout == payload


@pytest.mark.parametrize(
    "payload", [b"", b"x" * (1024 * 1024 + 1)], ids=["empty", "oversize"]
)
def test_snapshot_size_bound(receipt, payload):
    root, path, _ = receipt
    path.write_bytes(payload)
    with module().ReceiptLease.open_existing(root, path) as lease:
        with pytest.raises(CustodyError, match="tamaño"):
            lease.read_snapshot()
    assert path.read_bytes() == payload


def test_expected_requires_bytes(receipt):
    root, path, _ = receipt
    with module().ReceiptLease.open_existing(root, path) as lease:
        with pytest.raises(TypeError):
            lease.assert_expected("not bytes")


def test_direct_constructor_rejected():
    with pytest.raises(TypeError):
        module().ReceiptLease()


def test_native_handle_count_restored(receipt):
    import ctypes

    root, path, _ = receipt
    api = module()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetProcessHandleCount.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ulong),
    ]

    def count():
        value = ctypes.c_ulong()
        assert kernel.GetProcessHandleCount(
            kernel.GetCurrentProcess(), ctypes.byref(value)
        )
        return value.value

    before = count()
    for _ in range(10):
        with api.ReceiptLease.open_existing(root, path) as lease:
            lease.read_snapshot()
            assert count() > before
    # El RLock nativo también ocupa un HANDLE mientras la lease viva exista.
    # Al destruir el objeto cerrado no queda ningún handle propio: control
    # nativo independiente conservado en evidence/probe-lock-count.log.
    del lease
    assert count() == before


def _process_handle_count():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetProcessHandleCount.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ulong),
    ]
    value = ctypes.c_ulong()
    assert kernel.GetProcessHandleCount(kernel.GetCurrentProcess(), ctypes.byref(value))
    return value.value


def test_interrupted_successful_close_never_retries_uncertain_scalar(
    receipt, monkeypatch
):
    root, path, payload = receipt
    api = module()
    count_before = _process_handle_count()
    lease = api.ReceiptLease.open_existing(root, path)
    native = lease._native
    original = native.close
    target = lease._handles[-1][0]
    foreign = root / "foreign-witness"
    foreign_payload = b"FOREIGN-WITNESS-UNCHANGED"
    foreign.write_bytes(foreign_payload)
    owned_foreign = []
    actual_close_calls = []
    interrupted_once = False

    def interrupted(handle):
        nonlocal interrupted_once
        actual_close_calls.append(handle)
        original(handle)  # CloseHandle realmente SUCCESS; interrupción sólo después.
        if handle == target and not interrupted_once:
            interrupted_once = True
            raise KeyboardInterrupt("injected after actual CloseHandle SUCCESS")

    monkeypatch.setattr(native, "close", interrupted)
    try:
        with pytest.raises(BaseExceptionGroup) as first_error:
            lease.close()
        assert any(
            isinstance(error, KeyboardInterrupt)
            for error in first_error.value.exceptions
        )
        first_close_calls = tuple(actual_close_calls)
        assert first_close_calls.count(target) == 1
        # Ocho testigos reales, sin exigir ningún comportamiento del allocator.
        # La seguridad exige no reintentar aunque NO se observe reutilización.
        for _ in range(8):
            handle = native.open(str(foreign), directory=False)
            identity = native.inspect(handle).identity
            assert native.read(handle, len(foreign_payload)) == foreign_payload
            owned_foreign.append((handle, identity))
        repeated_error = None
        try:
            lease.close()
        except BaseExceptionGroup as error:
            repeated_error = error
        foreign_results = []
        for handle, identity in owned_foreign:
            try:
                actual = native.inspect(handle)
                preserved = (
                    actual.identity == identity
                    and native.read(handle, len(foreign_payload)) == foreign_payload
                )
                foreign_results.append((handle, preserved, None))
            except OSError as error:
                foreign_results.append((handle, False, str(error)))
        print(
            f"actual CloseHandle SUCCESS; uncertain={target}; target calls before=1/after={actual_close_calls.count(target)}; "
            f"reuse_observed={any(handle == target for handle, _ in owned_foreign)}; foreign_results={foreign_results}"
        )
        assert tuple(actual_close_calls) == first_close_calls, (
            "second lease.close retried an uncertain scalar in actual CloseHandle"
        )
        assert foreign.read_bytes() == foreign_payload
        assert (
            hashlib.sha256(path.read_bytes()).digest()
            == hashlib.sha256(payload).digest()
        )
        assert all(preserved for _, preserved, _ in foreign_results), foreign_results
        assert repeated_error is not None, "uncertainty cannot become silent success"
    finally:
        monkeypatch.setattr(native, "close", original)
        for handle, identity in reversed(owned_foreign):
            try:
                if native.inspect(handle).identity == identity:
                    original(handle)
            except OSError:
                # Witness known to have been destroyed by the failing original; no retries/reopens.
                pass
        count_after = _process_handle_count()
        print(
            f"handles before={count_before}; after owned foreign cleanup={count_after}"
        )


def test_concurrent_same_handle_reads_return_both_exact_snapshots(receipt, monkeypatch):
    root, path, payload = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    kernel = lease._native.kernel
    original = kernel.SetFilePointerEx
    paused, second_started, second_done, release = Event(), Event(), Event(), Event()
    outcomes = Queue()

    def pause_after_real_seek(*args):
        result = original(*args)  # Real native pointer position at zero.
        if current_thread().name == "first-receipt-reader":
            paused.set()
            if not release.wait(5):
                raise RuntimeError("test scheduling deadline exceeded")
        return result

    def read(label):
        if label == "second":
            second_started.set()
        try:
            outcomes.put((label, lease.read_snapshot(), None))
        except BaseException as error:  # noqa: BLE001 - evidencia del resultado, incluidas interrupciones
            outcomes.put((label, None, error))
        finally:
            if label == "second":
                second_done.set()

    monkeypatch.setattr(kernel, "SetFilePointerEx", pause_after_real_seek)
    first = Thread(
        target=read, args=("first",), name="first-receipt-reader", daemon=True
    )
    second = Thread(
        target=read, args=("second",), name="second-receipt-reader", daemon=True
    )
    try:
        first.start()
        assert paused.wait(5), "first native seek did not execute"
        second.start()
        assert second_started.wait(5), "second reader did not start"
        # Before serialization the second completes while the first is paused.
        # With correct serialization it waits; either schedule must yield exact bytes.
        second_done.wait(0.2)
        release.set()
        first.join(5)
        second.join(5)
        assert not first.is_alive() and not second.is_alive(), (
            "reader deadline exceeded"
        )
        results = [outcomes.get(timeout=1), outcomes.get(timeout=1)]
        print(
            [
                (label, str(error) if error else "exact snapshot")
                for label, _, error in results
            ]
        )
        assert all(error is None for _, _, error in results), results
        assert all(
            snapshot.payload == payload and snapshot.receipt.to_bytes() == payload
            for _, snapshot, _ in results
        )
        assert path.read_bytes() == payload
    finally:
        release.set()
        if first.ident is not None:
            first.join(5)
        if second.ident is not None:
            second.join(5)
        lease.close()


def test_close_waits_for_native_snapshot_then_rejects_new_reads(receipt, monkeypatch):
    root, path, payload = receipt
    lease = module().ReceiptLease.open_existing(root, path)
    native_read = lease._native.read
    paused, release, close_started, close_done = Event(), Event(), Event(), Event()
    outcomes = Queue()

    def pause_read(*args):
        paused.set()
        if not release.wait(5):
            raise RuntimeError("read scheduling deadline")
        return native_read(*args)

    def read():
        try:
            outcomes.put(("read", lease.read_snapshot(), None))
        except BaseException as error:  # noqa: BLE001 - resultado completo del hilo
            outcomes.put(("read", None, error))

    def close():
        close_started.set()
        try:
            lease.close()
            outcomes.put(("close", None, None))
        except BaseException as error:  # noqa: BLE001 - resultado completo del hilo
            outcomes.put(("close", None, error))
        finally:
            close_done.set()

    monkeypatch.setattr(lease._native, "read", pause_read)
    reader = Thread(target=read, daemon=True)
    closer = Thread(target=close, daemon=True)
    try:
        reader.start()
        assert paused.wait(5)
        closer.start()
        assert close_started.wait(5)
        assert not close_done.wait(0.2), "close interfered with an active native read"
        release.set()
        reader.join(5)
        closer.join(5)
        assert not reader.is_alive() and not closer.is_alive()
        results = [outcomes.get(timeout=1), outcomes.get(timeout=1)]
        assert all(error is None for _, _, error in results), results
        snapshot = next(snapshot for label, snapshot, _ in results if label == "read")
        assert snapshot.payload == payload
        assert path.read_bytes() == payload
        with pytest.raises(CustodyError):
            lease.read_snapshot()
    finally:
        release.set()
        reader.join(5)
        if closer.ident is not None:
            closer.join(5)
        lease.close()


def test_context_body_does_not_serialize_unrelated_thread_read(receipt):
    root, path, payload = receipt
    outcomes = Queue()
    with module().ReceiptLease.open_existing(root, path) as lease:

        def read():
            try:
                outcomes.put(lease.read_snapshot().payload)
            except BaseException as error:  # noqa: BLE001 - traza causal del hilo
                outcomes.put(error)

        reader = Thread(target=read, daemon=True)
        reader.start()
        reader.join(5)
        assert not reader.is_alive(), "context body held the operation lock"
        assert outcomes.get(timeout=1) == payload
