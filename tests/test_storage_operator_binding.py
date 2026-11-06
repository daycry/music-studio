"""Binding nativo de archivos testigo; no acredita VHDX, attach ni ext4."""

import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from studio_storage_guard.receipt import ReceiptError, StorageReceipt

from scripts.storage_windows import CustodyError, WindowsCustody

_PRIVATE = Path(__file__).resolve().parents[1]
_SOURCE = _PRIVATE / "scripts/storage_operator.py"
if _SOURCE.is_file():
    spec = importlib.util.spec_from_file_location("storage_operator_candidate", _SOURCE)
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
else:
    operator = None

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows nativo requerido")


def binding():
    assert operator is not None, (
        "falta PublishedDiskBinding: no existe lease de consulta publicada"
    )
    return operator.PublishedDiskBinding


@pytest.fixture
def published():
    root = _PRIVATE / ".cache/dev-cycle/m1/storage-binding-tests" / uuid4().hex
    scope = root / "data/_storage"
    scope.mkdir(parents=True)
    disk = scope / "studio-data.vhdx"
    with WindowsCustody(root, "data/_storage") as custody:
        owned = custody.create_sparse_file("studio-data.vhdx", 0)
        owned.write(b"OWNED")
        identity = owned.inspect().identity
    receipt = StorageReceipt.reserve(
        project_root=root, operation_id="0" * 26, size_bytes=5
    )
    receipt = receipt.advance(
        "raw_verified",
        {
            "raw_sha256": hashlib.sha256(b"OWNED").hexdigest(),
            "raw_size": 5,
            "uuid": "00000000-0000-0000-0000-000000000001",
        },
    )
    receipt = receipt.advance(
        "vhdx_verified",
        {"vhdx_sha256": hashlib.sha256(b"OWNED").hexdigest(), "vhdx_size": 5},
    )
    receipt = receipt.advance(
        "published",
        {
            "final_path": disk.as_posix(),
            "file_id": f"{identity[0]}:{identity[1].hex()}",
        },
    )
    return root, disk, receipt, identity


def handles():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetProcessHandleCount.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ulong),
    ]
    count = ctypes.c_ulong()
    assert kernel.GetProcessHandleCount(kernel.GetCurrentProcess(), ctypes.byref(count))
    return count.value


def test_live_query_identity_and_runtime_writes(published):
    root, disk, receipt, identity = published
    before = receipt.to_bytes()
    with binding().open(root, receipt) as lease:
        assert lease.revalidate().identity == identity
        assert not any(
            hasattr(lease, method)
            for method in ("write", "discard", "adopt", "promote_no_replace")
        )
        disk.write_bytes(b"RUNTIME WRITES CHANGE SIZE AND HASH")
        assert lease.revalidate().identity == identity
    assert receipt.to_bytes() == before
    assert disk.read_bytes() == b"RUNTIME WRITES CHANGE SIZE AND HASH"


def test_replacement_before_open_preserves_foreign(published):
    root, disk, receipt, _ = published
    disk.rename(disk.with_suffix(".old"))
    disk.write_bytes(b"FOREIGN")
    with pytest.raises(CustodyError, match="identidad"):
        binding().open(root, receipt)
    assert disk.read_bytes() == b"FOREIGN"


def test_lease_blocks_real_rename_delete_and_releases_exactly(published):
    root, disk, receipt, _ = published
    cls = binding()
    baseline = handles()
    lease = cls.open(root, receipt)
    retained = handles()
    assert retained > baseline
    for path in (disk, disk.parent, root):
        with pytest.raises(OSError) as denied:
            path.rename(path.with_name(path.name + "-renamed"))
        assert denied.value.winerror == 32
    with pytest.raises(OSError) as denied:
        disk.unlink()
    assert denied.value.winerror == 32
    lease.close()
    assert handles() == baseline
    lease.close()
    assert handles() == baseline
    with pytest.raises(CustodyError, match="cerrad"):
        lease.revalidate()
    released = disk.with_suffix(".released")
    disk.rename(released)
    assert released.read_bytes() == b"OWNED"
    released.unlink()
    assert not released.exists()
    (root / "native-binding-receipt.json").write_text(
        json.dumps(
            {
                "baseline_handles": baseline,
                "retained_handles": retained,
                "closed_handles": handles(),
                "rename_delete_winerror": 32,
                "rename_delete_after_close": "permitted",
                "phase": receipt.phase,
                "file_id": receipt.history[-1]["evidence"]["file_id"],
            }
        ),
        encoding="utf8",
    )


def test_hardlink_rejected_without_leak_or_writes(published):
    root, disk, receipt, _ = published
    os.link(disk, disk.with_suffix(".alias"))
    cls = binding()
    baseline = handles()
    with pytest.raises(CustodyError, match="hardlink"):
        cls.open(root, receipt)
    assert handles() == baseline
    assert disk.read_bytes() == b"OWNED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("file_id", "0:" + "00" * 16),
        ("file_id", "invalid"),
        ("final_path", "C:/foreign.vhdx"),
    ],
)
def test_bad_receipt_evidence_rejected_without_leak(published, field, value):
    root, disk, receipt, _ = published
    receipt.history[-1]["evidence"][field] = value
    cls = binding()
    baseline = handles()
    with pytest.raises((CustodyError, ReceiptError)):
        cls.open(root, receipt)
    assert handles() == baseline
    assert disk.read_bytes() == b"OWNED"


def test_receipt_mutation_during_acquisition_is_rejected(published, monkeypatch):
    root, disk, receipt, _ = published
    cls = binding()
    original = operator._QueryNative.open

    def racing(native, path):
        handle = original(native, path)
        if path.endswith("studio-data.vhdx"):
            receipt.history[-1]["evidence"]["file_id"] = "0:" + "00" * 16
        return handle

    monkeypatch.setattr(operator._QueryNative, "open", racing)
    baseline = handles()
    with pytest.raises(CustodyError, match="recibo"):
        cls.open(root, receipt)
    assert handles() == baseline
    assert disk.read_bytes() == b"OWNED"


def test_reparse_ancestor_rejected(published):
    root, disk, receipt, _ = published
    cls = binding()
    # Junction nativa mediante API Python, sin shell/admin/servicios.
    import _winapi

    target = root / "foreign-data"
    (root / "data").rename(target)
    _winapi.CreateJunction(str(target), str(root / "data"))
    baseline = handles()
    with pytest.raises(CustodyError, match="reparse"):
        cls.open(root, receipt)
    assert handles() == baseline
    assert disk.read_bytes() == b"OWNED"


def test_path_replacement_during_acquisition_rejected(published, monkeypatch):
    root, disk, receipt, _ = published
    cls = binding()
    original = operator._QueryNative.open

    def racing(native, path):
        if path.endswith("studio-data.vhdx"):
            disk.rename(disk.with_suffix(".old"))
            disk.write_bytes(b"FOREIGN")
        return original(native, path)

    monkeypatch.setattr(operator._QueryNative, "open", racing)
    baseline = handles()
    with pytest.raises(CustodyError, match="identidad"):
        cls.open(root, receipt)
    assert handles() == baseline
    assert disk.read_bytes() == b"FOREIGN"


def test_disk_reparse_rejected_without_writes(published):
    root, disk, receipt, _ = published
    cls = binding()
    import _winapi

    disk.rename(disk.with_suffix(".old"))
    target = root / "foreign-directory"
    target.mkdir()
    witness = target / "witness"
    witness.write_bytes(b"FOREIGN")
    _winapi.CreateJunction(str(target), str(disk))
    baseline = handles()
    with pytest.raises(CustodyError, match="reparse"):
        cls.open(root, receipt)
    assert handles() == baseline
    assert witness.read_bytes() == b"FOREIGN"


@pytest.mark.parametrize(
    "root", ["relative", "C:/with/../escape", "//server/share/project", "C:/bad."]
)
def test_unc_relative_and_noncanonical_roots_rejected(published, root):
    _, disk, receipt, _ = published
    with pytest.raises(ValueError):
        binding().open(root, receipt)
    assert disk.read_bytes() == b"OWNED"


def test_public_constructor_wrong_receipt_phase_and_type_rejected(published):
    root, _, receipt, _ = published
    cls = binding()
    with pytest.raises(TypeError):
        cls()
    with pytest.raises(ReceiptError):
        cls.open(root, receipt.to_dict())
    reserved = StorageReceipt.reserve(
        project_root=root, operation_id="0" * 26, size_bytes=5
    )
    with pytest.raises(ReceiptError, match="published"):
        cls.open(root, reserved)


def test_missing_disk_releases_every_retained_handle(published):
    root, disk, receipt, _ = published
    cls = binding()
    disk.rename(disk.with_suffix(".old"))
    baseline = handles()
    with pytest.raises(OSError):
        cls.open(root, receipt)
    assert handles() == baseline


def test_receipt_mutation_after_open_rejected(published):
    root, _, receipt, _ = published
    with binding().open(root, receipt) as lease:
        receipt.history[-1]["evidence"]["file_id"] = "0:" + "00" * 16
        with pytest.raises(CustodyError, match="recibo"):
            lease.revalidate()


def test_entry_failure_releases_native_handles_and_preserves_foreign(
    published, monkeypatch
):
    root, disk, receipt, _ = published
    cls = binding()
    original_open = cls.open
    tracked = []
    witness = root / "foreign"
    witness.write_bytes(b"FOREIGN")
    baseline = handles()

    def mutate_after_successful_open(project, supplied):
        lease = original_open(project, supplied)
        tracked.append(lease)
        # La adquisición y su último revalidate ya terminaron correctamente.
        supplied.history[-1]["evidence"]["file_id"] = "0:" + "00" * 16
        return lease

    monkeypatch.setattr(cls, "open", staticmethod(mutate_after_successful_open))
    body_entered = False
    try:
        with pytest.raises(CustodyError, match="recibo alterado"), cls.open(root, receipt):
            body_entered = True
        after_failure = handles()
        try:
            disk.rename(disk.with_suffix(".released"))
            rename_error = None
        except OSError as error:
            rename_error = error.winerror
        (root / "native-entry-failure-receipt.json").write_text(
            json.dumps(
                {
                    "baseline_handles": baseline,
                    "after_entry_failure": after_failure,
                    "rename_winerror": rename_error,
                    "body_entered": body_entered,
                    "foreign_sha256": hashlib.sha256(witness.read_bytes()).hexdigest(),
                }
            ),
            encoding="utf8",
        )
        assert not body_entered
        assert witness.read_bytes() == b"FOREIGN"
        assert after_failure == baseline, (
            "__enter__ fallido debe liberar todos sus handles"
        )
        assert rename_error is None
        assert disk.with_suffix(".released").read_bytes() == b"OWNED"
    finally:
        # Conserva una reproducción RED limpia sin esconder el fallo observado.
        for lease in tracked:
            lease.close()
