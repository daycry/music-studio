"""Unit tests for verified VHDX publication."""

import hashlib
import json
from pathlib import Path

import pytest
from studio_storage_guard.receipt import StorageReceipt

from scripts.storage_publish import publish_verified_vhdx


class FakeFile:
    def __init__(self, path: Path, size: int):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(b"\x00" * size)
        self.sealed = None
        self.published = False

    def write(self, payload: bytes, *, offset: int = 0):
        with self.path.open("r+b") as stream:
            stream.seek(offset)
            stream.write(payload)

    def seal(self, digest: str):
        actual = hashlib.sha256(self.path.read_bytes()).hexdigest()
        assert actual == digest
        self.sealed = digest
        return object()

    def inspect(self):
        return type("Metadata", (), {"identity": (1, b"owned-file-id")})()

    def promote_no_replace(self, name: str, seal):
        assert self.sealed
        destination = self.path.parent / name
        if destination.exists():
            raise OSError(183, "already exists")
        self.path.replace(destination)
        self.published = True


class FakeCustody:
    def __init__(self, project_root, scope):
        self.scope = Path(project_root) / "data" / "_storage"

    def __enter__(self):
        self.scope.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *_):
        return False

    def create_sparse_file(self, name, size_bytes):
        return FakeFile(self.scope / name, size_bytes)


def _receipt(tmp_path: Path, payload: bytes) -> Path:
    workspace = tmp_path / ".cache" / "dev-cycle" / "storage-01ARZ3NDEKTSV4RRFFQ69G5FAV"
    workspace.mkdir(parents=True)
    source = workspace / "studio-data.vhdx"
    source.write_bytes(payload)
    receipt = (
        StorageReceipt.reserve(
            project_root=tmp_path,
            operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            size_bytes=len(payload),
        )
        .advance(
            "raw_verified",
            {
                "raw_sha256": hashlib.sha256(b"raw").hexdigest(),
                "raw_size": 3,
                "uuid": "12345678-1234-5678-1234-567812345678",
            },
        )
        .advance(
            "vhdx_verified",
            {
                "vhdx_sha256": hashlib.sha256(payload).hexdigest(),
                "vhdx_size": len(payload),
            },
        )
    )
    receipt_path = workspace / "receipt.json"
    receipt_path.write_bytes(receipt.to_bytes())
    return receipt_path


def test_publish_verified_vhdx_copies_and_advances_receipt(tmp_path):
    receipt_path = _receipt(tmp_path, b"verified-vhdx")
    result = publish_verified_vhdx(tmp_path, receipt_path, custody_factory=FakeCustody)
    final = tmp_path / "data" / "_storage" / "studio-data.vhdx"
    assert final.read_bytes() == b"verified-vhdx"
    assert result.phase == "published"
    assert result.history[-1]["evidence"]["final_path"] == final.absolute().as_posix()
    assert result.history[-1]["evidence"]["file_id"]
    assert json.loads(receipt_path.read_text())["phase"] == "published"


def test_publish_refuses_existing_destination_and_preserves_source(tmp_path):
    receipt_path = _receipt(tmp_path, b"verified-vhdx")
    final = tmp_path / "data" / "_storage" / "studio-data.vhdx"
    final.parent.mkdir(parents=True)
    final.write_bytes(b"FOREIGN")
    with pytest.raises(OSError):
        publish_verified_vhdx(tmp_path, receipt_path, custody_factory=FakeCustody)
    assert final.read_bytes() == b"FOREIGN"
    assert (receipt_path.parent / "studio-data.vhdx").read_bytes() == b"verified-vhdx"


def test_publish_refuses_tampered_source(tmp_path):
    receipt_path = _receipt(tmp_path, b"verified-vhdx")
    source = receipt_path.parent / "studio-data.vhdx"
    source.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash"):
        publish_verified_vhdx(tmp_path, receipt_path, custody_factory=FakeCustody)
    assert not (tmp_path / "data" / "_storage" / "studio-data.vhdx").exists()
