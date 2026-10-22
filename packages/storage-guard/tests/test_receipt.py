import json
from pathlib import Path

import pytest
from studio_storage_guard.receipt import (
    PHASES,
    ReceiptError,
    StorageReceipt,
)


def make_receipt(tmp_path: Path) -> StorageReceipt:
    return StorageReceipt.reserve(
        project_root=tmp_path,
        operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        size_bytes=64 * 1024 * 1024,
    )


def test_reserve_uses_project_paths_and_first_phase(tmp_path):
    receipt = make_receipt(tmp_path)

    assert PHASES == (
        "reserved",
        "raw_verified",
        "vhdx_verified",
        "published",
        "attached",
        "validated",
    )
    assert receipt.phase == "reserved"
    assert receipt.disk_path == (tmp_path / "data/_storage/studio-data.vhdx").as_posix()
    assert receipt.size_bytes == 64 * 1024 * 1024
    assert receipt.history == ({"phase": "reserved", "evidence": {}},)


def test_phase_transitions_are_monotonic_and_require_evidence(tmp_path):
    receipt = make_receipt(tmp_path)

    with pytest.raises(ReceiptError, match="transicion de fase"):
        receipt.advance("vhdx_verified", {"vhdx_sha256": "a" * 64})

    receipt = receipt.advance(
        "raw_verified",
        {
            "raw_sha256": "b" * 64,
            "raw_size": 64 * 1024 * 1024,
            "uuid": "12345678-1234-5678-1234-567812345678",
        },
    )
    with pytest.raises(ReceiptError, match="evidencia"):
        receipt.advance("vhdx_verified", {})
    receipt = receipt.advance(
        "vhdx_verified", {"vhdx_sha256": "c" * 64, "vhdx_size": 1024}
    )
    receipt = receipt.advance(
        "published", {"final_path": receipt.disk_path, "file_id": "file-1"}
    )
    receipt = receipt.advance(
        "attached", {"device": "/dev/loop0", "mountpoint": "/mnt/studio-data"}
    )
    receipt = receipt.advance("validated", {"noreplace": True, "fs_type": "ext4"})
    assert receipt.phase == "validated"
    assert [item["phase"] for item in receipt.history] == list(PHASES)

    with pytest.raises(ReceiptError, match="terminal"):
        receipt.advance("validated", {})


def test_serialization_is_canonical_and_rejects_tampering(tmp_path):
    receipt = make_receipt(tmp_path).advance(
        "raw_verified",
        {
            "raw_sha256": "b" * 64,
            "raw_size": 1,
            "uuid": "12345678-1234-5678-1234-567812345678",
        },
    )
    encoded = receipt.to_bytes()
    assert encoded == receipt.to_bytes()
    assert json.loads(encoded) == receipt.to_dict()
    assert StorageReceipt.from_bytes(encoded) == receipt

    tampered = receipt.to_dict()
    tampered["phase"] = "published"
    with pytest.raises(ReceiptError, match="historial"):
        StorageReceipt.from_dict(tampered)
