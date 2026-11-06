"""Pruebas nativas Windows; no acreditan montaje ni conversión Linux."""

import os
import hashlib
import ctypes
from ctypes import wintypes
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest

from scripts.storage_windows import CustodyError, OwnedFile, WindowsCustody

pytestmark = pytest.mark.skipif(os.name != "nt", reason="API nativa Windows")


@pytest.fixture
def tmp_path():
    path = Path(__file__).resolve().parents[1] / ".cache/dev-cycle/m1/t05-storage-windows-primitives1" / ("fixture-" + uuid4().hex)
    path.mkdir()
    return path


def test_atomic_directory_creation_and_live_identity(tmp_path):
    scope = tmp_path / ".cache" / "dev-cycle" / "test"
    scope.mkdir(parents=True)
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        directory = custody.create_directory("own")
        metadata = directory.inspect()
        assert metadata.directory
        assert metadata.links == 1
        assert len(metadata.file_id) == 16
        assert metadata.final_path == "\\\\?\\" + str(scope / "own")
        with pytest.raises(OSError):
            os.rename(scope / "own", scope / "rival")
        assert directory.inspect().identity == metadata.identity
        directory.discard()
        assert not (scope / "own").exists()


def test_sparse_file_is_new_guarded_low_allocation(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        file = custody.create_sparse_file("raw.img", 1024**3)
        before = file.inspect()
        assert before.size == 1024**3
        assert before.allocated < 1024**2
        assert before.attributes & 0x200
        file.write(b"abc", offset=1024**3 - 3)
        assert file.read(offset=1024**3 - 4, size=4) == b"\x00abc"
        assert file.inspect().allocated < 1024**2
        assert file.inspect().identity == before.identity
        with pytest.raises(OSError):
            os.rename(scope / "raw.img", scope / "rival.img")
        with pytest.raises(OSError):
            (scope / "raw.img").unlink()
        assert file.inspect().identity == before.identity


def test_seal_requires_expected_bytes_and_blocks_future_writes(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        file = custody.create_sparse_file("raw.img", 0)
        file.write(b"owned")
        identity = file.inspect().identity
        with pytest.raises(CustodyError, match="hash"):
            file.seal(hashlib.sha256(b"unexpected").hexdigest())
        assert file.read(size=16) == b"owned"
        seal = file.seal(hashlib.sha256(b"owned").hexdigest())
        assert seal.identity == identity
        assert seal.sha256 == hashlib.sha256(b"owned").hexdigest()
        with pytest.raises(CustodyError, match="sellad"):
            file.write(b"bad")


@pytest.mark.parametrize("foreign", [None, "empty", "nonempty", "file", "hardlink"])
def test_promotion_by_handle_never_replaces_foreign_destination(tmp_path, foreign):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    destination = scope / "studio-data.vhdx"
    if foreign in {"empty", "nonempty"}:
        destination.mkdir()
        if foreign == "nonempty":
            (destination / "witness").write_bytes(b"FOREIGN")
    elif foreign == "file":
        destination.write_bytes(b"FOREIGN")
    elif foreign == "hardlink":
        (scope / "witness").write_bytes(b"FOREIGN")
        os.link(scope / "witness", destination)
    identity = destination.stat().st_ino if foreign else None
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        file = custody.create_sparse_file("output.vhdx", 0)
        file.write(b"OWNED")
        before = file.inspect()
        seal = file.seal(hashlib.sha256(b"OWNED").hexdigest())
        if foreign:
            for _ in range(2):
                with pytest.raises(OSError) as error:
                    file.promote_no_replace("studio-data.vhdx", seal)
                assert error.value.winerror in {5, 80, 183}
            assert destination.stat().st_ino == identity
            assert file.inspect() == before
            if foreign in {"file", "hardlink"}:
                assert destination.read_bytes() == b"FOREIGN"
            elif foreign == "nonempty":
                assert (destination / "witness").read_bytes() == b"FOREIGN"
            else:
                assert list(destination.iterdir()) == []
        else:
            file.promote_no_replace("studio-data.vhdx", seal)
            assert file.inspect().identity == before.identity
            assert file.inspect().final_path == "\\\\?\\" + str(destination)
            assert file.read(size=16) == b"OWNED"
            assert not (scope / "output.vhdx").exists()
            with pytest.raises(OSError):
                destination.unlink()


def test_disposition_uses_same_owned_handle_and_preserves_published_file(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        file = custody.create_sparse_file("raw.img", 0)
        file.write(b"OWNED")
        seal = file.seal(hashlib.sha256(b"OWNED").hexdigest())
        file.discard(seal)
        assert not (scope / "raw.img").exists()
        with pytest.raises(CustodyError, match="cerrad"):
            file.inspect()
        final = custody.create_sparse_file("output.vhdx", 0)
        final.write(b"OWNED")
        seal = final.seal(hashlib.sha256(b"OWNED").hexdigest())
        final.promote_no_replace("studio-data.vhdx", seal)
        with pytest.raises(CustodyError, match="publicad"):
            final.discard(seal)
        assert final.read(size=16) == b"OWNED"


def test_live_producer_must_be_reaped_before_seal_or_close(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    custody = WindowsCustody(tmp_path, ".cache/dev-cycle/test")
    file = custody.create_sparse_file("raw.img", 0)
    producer = custody.start_producer([sys.executable, "-B", "-c", "import time; time.sleep(0.3)"], [file])
    try:
        with pytest.raises(CustodyError, match="productor"):
            file.write(b"BAD")
        with pytest.raises(CustodyError, match="productor"):
            custody.start_producer([sys.executable, "-B", "-c", "pass"], [file])
        with pytest.raises(CustodyError, match="productor"):
            file.seal(hashlib.sha256(b"").hexdigest())
        with pytest.raises(CustodyError, match="productor"):
            custody.close()
        with pytest.raises(subprocess.TimeoutExpired):
            producer.wait(timeout=0)
        assert file.inspect().size == 0
        assert producer.wait(timeout=10) == 0
        seal = file.seal(hashlib.sha256(b"").hexdigest())
        file.discard(seal)
    finally:
        producer.wait(timeout=10)
        custody.close()


def test_child_files_require_live_owned_parent_and_cleanup_by_handle(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        directory = custody.create_directory("reservation")
        file = custody.create_sparse_file("raw.img", 0, parent=directory)
        assert file.inspect().final_path == "\\\\?\\" + str(scope / "reservation/raw.img")
        with pytest.raises(OSError):
            directory.discard()
        seal = file.seal(hashlib.sha256(b"").hexdigest())
        file.discard(seal)
        directory.discard()
        with pytest.raises(CustodyError):
            custody.create_sparse_file("bad", 0, parent=directory)


def test_existing_handle_cannot_reconstruct_creation_authority(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    foreign = scope / "foreign"
    foreign.write_bytes(b"FOREIGN")
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        handle = custody._native.child(custody._scope._handle, "foreign", False, False)
        try:
            with pytest.raises(CustodyError, match="creación"):
                OwnedFile(custody, handle, "\\\\?\\" + str(foreign), False)
        finally:
            custody._native.kernel.CloseHandle(handle)
        assert foreign.read_bytes() == b"FOREIGN"


def test_unknown_bytes_between_kernel_creation_and_inspection_are_preserved(tmp_path, monkeypatch):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    with WindowsCustody(tmp_path, ".cache/dev-cycle/test") as custody:
        original = custody._native.child

        def injected_write(parent, name, directory, create):
            handle = original(parent, name, directory, create)
            if create and not directory:
                amount = wintypes.DWORD()
                custody._native.checked(custody._native.kernel.WriteFile(handle, b"UNKNOWN", 7, ctypes.byref(amount), None))
                assert amount.value == 7
            return handle

        monkeypatch.setattr(custody._native, "child", injected_write)
        with pytest.raises(CustodyError, match="vacío"):
            custody.create_sparse_file("raw.img", 0)
        assert (scope / "raw.img").read_bytes() == b"UNKNOWN"


def test_parent_exit_does_not_release_live_descendant_writer(tmp_path):
    scope = tmp_path / ".cache/dev-cycle/test"
    scope.mkdir(parents=True)
    custody = WindowsCustody(tmp_path, ".cache/dev-cycle/test")
    file = custody.create_sparse_file("raw.img", 0)
    command = "import subprocess,sys; subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(0.8)'])"
    producer = custody.start_producer([sys.executable, "-B", "-c", command], [file])
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            producer.wait(timeout=0.2)
        with pytest.raises(CustodyError, match="productor"):
            file.seal(hashlib.sha256(b"").hexdigest())
        assert producer.wait(timeout=10) == 0
        file.discard(file.seal(hashlib.sha256(b"").hexdigest()))
    finally:
        producer.wait(timeout=10)
        # En el RED previo al job, el PID principal termina antes que su hijo.
        time.sleep(1)
        custody.close()
