import os
import sys

import pytest


@pytest.mark.skipif(sys.platform != "linux", reason="Linux syscall test")
def test_native_noreplace_preserves_all_witnesses_and_cleans(tmp_path):
    from studio_storage_guard.custody import CustodiedProbeDomain

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/scratch/data", flags)
    try:
        with CustodiedProbeDomain.open(fd) as domain:
            domain.probe()
        assert os.listdir("/scratch/data/.storage-probes") == [".lock"]
    finally:
        os.close(fd)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux syscall test")
def test_probe_does_not_remove_substituted_marker(tmp_path, monkeypatch):
    from pathlib import Path

    from studio_storage_guard import custody

    rename = custody._rename_noreplace

    def substitute(fd, source, target):
        if target == "target-link":
            parent = os.open("target-nonempty", os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
            try:
                os.unlink("marker", dir_fd=parent)
                foreign = os.open(
                    "marker", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=parent
                )
                os.write(foreign, b"foreign")
                os.close(foreign)
            finally:
                os.close(parent)
        return rename(fd, source, target)

    monkeypatch.setattr(custody, "_rename_noreplace", substitute)
    tmp_path = Path("/scratch/marker-substitution/.storage-probes")
    fd = os.open("/scratch/marker-substitution", os.O_RDONLY | os.O_DIRECTORY)
    try:
        with (
            custody.CustodiedProbeDomain.open(fd) as domain,
            pytest.raises(Exception, match="STORAGE_ROOT_INVALID"),
        ):
            domain.probe()
        marker = next(tmp_path.glob("*/target-nonempty/marker"))
        assert marker.read_bytes() == b"foreign"
    finally:
        os.close(fd)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux syscall test")
def test_probe_preserves_file_modified_in_place(tmp_path, monkeypatch):
    from pathlib import Path

    from studio_storage_guard import custody

    rename = custody._rename_noreplace

    def mutate(fd, source, target):
        if target == "target-link":
            foreign = os.open("target-file", os.O_WRONLY, dir_fd=fd)
            os.write(foreign, b"foreign")
            os.close(foreign)
        return rename(fd, source, target)

    monkeypatch.setattr(custody, "_rename_noreplace", mutate)
    tmp_path = Path("/scratch/file-mutation/.storage-probes")
    fd = os.open("/scratch/file-mutation", os.O_RDONLY | os.O_DIRECTORY)
    try:
        with (
            custody.CustodiedProbeDomain.open(fd) as domain,
            pytest.raises(Exception, match="STORAGE_ROOT_INVALID"),
        ):
            domain.probe()
        assert next(tmp_path.glob("*/target-file")).read_bytes() == b"foreign"
    finally:
        os.close(fd)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux syscall test")
def test_native_tmpfs_root_rejected_before_probe(monkeypatch):
    from studio_storage_guard import preflight

    probes = []
    monkeypatch.setattr(
        preflight.LinuxBackend, "probe", lambda self, fd: probes.append(fd)
    )
    with pytest.raises(preflight.StorageGuardError, match="^STORAGE_ROOT_INVALID$"):
        preflight.verify_root(
            "/scratch", "12345678-1234-4234-8234-123456789abc", "server"
        )
    assert probes == []


@pytest.mark.skipif(sys.platform != "linux", reason="Linux syscall test")
def test_native_symlink_ancestor_rejected_without_writes(tmp_path):
    from studio_storage_guard import preflight

    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(preflight.StorageGuardError, match="^STORAGE_ROOT_INVALID$"):
        preflight.verify_root(
            str(alias), "12345678-1234-4234-8234-123456789abc", "server"
        )
    assert list(target.iterdir()) == []
