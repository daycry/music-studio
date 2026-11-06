"""Política de almacenamiento; no aprovisiona discos ni acredita un despliegue."""

import importlib.util
import json
from pathlib import Path

import pytest


def storage():
    path = Path(__file__).parents[1] / "scripts/storage.py"
    if not path.exists():
        pytest.fail("Falta la política de almacenamiento confinado")
    spec = importlib.util.spec_from_file_location("studio_storage_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_requires_admin_without_side_effects(tmp_path):
    before = list(tmp_path.iterdir())
    result = storage().plan(tmp_path, "create", admin=False)
    assert result["status"] == "NEEDS_ADMIN"
    assert result["commands"] == []
    assert list(tmp_path.iterdir()) == before


def test_plan_never_formats_or_adopts_existing_disk(tmp_path):
    folder = tmp_path / "data/_storage"
    folder.mkdir(parents=True)
    disk = folder / "studio-data.vhdx"
    disk.write_bytes(b"foreign disk")
    result = storage().plan(tmp_path, "create", admin=True)
    assert result["status"] == "CONFLICT"
    assert result["commands"] == []
    assert disk.read_bytes() == b"foreign disk"


def test_plan_new_disk_is_exact_and_unexecutable(tmp_path):
    result = storage().plan(tmp_path, "create", admin=True)
    assert result["status"] == "NEEDS_CONTEXT"
    assert result["disk"] == str(tmp_path / "data/_storage/studio-data.vhdx")
    assert result["size_bytes"] == 64 * 1024**3
    assert result["commands"] == []
    assert "device" in result["gap"]


def test_alias_rejected(tmp_path, monkeypatch):
    import stat
    from types import SimpleNamespace

    (tmp_path / "data").mkdir()
    original = Path.lstat

    def aliased(path):
        if path == tmp_path / "data":
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original(path)

    monkeypatch.setattr(Path, "lstat", aliased)
    with pytest.raises(ValueError, match="alias"):
        storage().disk_path(tmp_path)


def evidence():
    return {
        "root": "/mnt/studio-data",
        "mountpoint": "/mnt/studio-data",
        "fs_type": "ext4",
        "uuid": "12345678-1234-1234-1234-123456789abc",
        "read_only": False,
        "source": "/dev/sdz1",
        "mount_root": "/",
        "disk_bound": False,
        "noreplace": False,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("mountpoint", "/"),
        ("fs_type", "9p"),
        ("fs_type", "tmpfs"),
        ("uuid", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        ("read_only", True),
        ("mount_root", "/subdir"),
        ("disk_bound", False),
        ("noreplace", False),
    ],
)
def test_preflight_rejects_inadequate_evidence(field, value):
    item = evidence() | {"disk_bound": True, "noreplace": True, field: value}
    with pytest.raises(ValueError):
        storage().validate_evidence(item, "/mnt/studio-data", evidence()["uuid"])


def test_unresolved_mount_identity_is_not_green():
    with pytest.raises(ValueError, match="disk"):
        storage().validate_evidence(evidence(), "/mnt/studio-data", evidence()["uuid"])


@pytest.mark.parametrize("operation", ["attach", "mount", "detach"])
def test_operations_need_native_identity_without_commands(tmp_path, operation):
    result = storage().plan(tmp_path, operation, admin=True)
    assert result["status"] == "NEEDS_CONTEXT"
    assert result["commands"] == []


def test_uuid_and_virtual_mount_are_strict():
    for root in ["/", "/mnt/../data", "/mnt/a b", "relative", "/mnt/c/data"]:
        with pytest.raises(ValueError):
            storage().validate_evidence(evidence(), root, evidence()["uuid"])
    with pytest.raises(ValueError):
        storage().validate_evidence(evidence(), "/mnt/studio-data", "not-a-uuid")


def test_mountinfo_requires_exact_unique_mount():
    line = "44 22 8:1 / /mnt/studio-data rw,relatime - ext4 /dev/sdz1 rw\n"
    item = storage().parse_mountinfo(line, "/mnt/studio-data")
    assert item["fs_type"] == "ext4"
    assert item["source"] == "/dev/sdz1"
    assert item["read_only"] is False
    for text in ["", line + line]:
        with pytest.raises(ValueError):
            storage().parse_mountinfo(text, "/mnt/studio-data")


@pytest.mark.parametrize(
    "args,status",
    [
        (["create"], "NEEDS_ADMIN"),
        (["attach", "--admin-observed"], "NEEDS_CONTEXT"),
        (["create", "--size-gib", "1"], "REJECTED"),
        (["preflight"], "REJECTED"),
        (["preflight", "--root", "/mnt/studio-data", "--uuid", "bad"], "REJECTED"),
        (
            [
                "preflight",
                "--root",
                "/mnt/studio-data",
                "--uuid",
                "12345678-1234-1234-1234-123456789abc",
            ],
            "NEEDS_CONTEXT",
        ),
    ],
)
def test_cli_never_authorizes_storage(args, status, tmp_path, capsys):
    before = list(tmp_path.iterdir())
    assert storage().main([*args, "--project", str(tmp_path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == status
    assert result["commands"] == []
    assert list(tmp_path.iterdir()) == before


def test_disk_rejects_non_directory_parent(tmp_path):
    (tmp_path / "data").write_bytes(b"preserve")
    with pytest.raises(ValueError, match="padre"):
        storage().disk_path(tmp_path)
    assert (tmp_path / "data").read_bytes() == b"preserve"


def test_disk_rejects_real_hardlink(tmp_path):
    import os

    (tmp_path / "data/_storage").mkdir(parents=True)
    disk = tmp_path / "data/_storage/studio-data.vhdx"
    disk.write_bytes(b"preserve")
    os.link(disk, tmp_path / "another-name")
    with pytest.raises(ValueError, match="hardlink"):
        storage().disk_path(tmp_path)
    assert disk.read_bytes() == b"preserve"
    assert (tmp_path / "another-name").read_bytes() == b"preserve"


def test_invalid_operation_and_budget_do_not_inspect_disk(tmp_path):
    for operation, budget in [("format", 64), ("create", True), ("create", 1025)]:
        with pytest.raises(ValueError):
            storage().plan(tmp_path, operation, size_gib=budget)


def test_malformed_mountinfo_and_wrong_device_rejected():
    with pytest.raises(ValueError, match="malformado"):
        storage().parse_mountinfo("bad mount row", "/mnt/studio-data")
    item = evidence() | {"disk_bound": True, "noreplace": True, "source": "not-device"}
    with pytest.raises(ValueError, match="device"):
        storage().validate_evidence(item, "/mnt/studio-data", evidence()["uuid"])
