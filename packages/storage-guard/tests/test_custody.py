import json
import os
import sys

import pytest
from studio_storage_guard.preflight import LinuxBackend, StorageGuardError


def test_unprotected_backend_refuses_before_any_write(monkeypatch):
    calls = []

    def would_write(*args, **kwargs):
        calls.append(args)
        raise StorageGuardError()

    monkeypatch.setattr(os, "mkdir", would_write)
    with pytest.raises(StorageGuardError):
        LinuxBackend().probe(999)
    assert calls == []


@pytest.mark.skipif(sys.platform != "linux", reason="real Linux credentials")
def test_protected_domain_runs_noreplace_and_cleans():
    from studio_storage_guard.custody import CustodiedProbeDomain

    root = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with CustodiedProbeDomain.open(root) as domain:
            domain.probe()
        assert os.listdir("/scratch/data/.storage-probes") == [".lock"]
    finally:
        os.close(root)


@pytest.mark.skipif(sys.platform != "linux", reason="real anonymous Linux inode")
def test_anonymous_consumer_rw_has_no_named_witness():
    from studio_storage_guard.custody import anonymous_rw_probe

    root = os.open("/scratch/consumer", os.O_RDONLY | os.O_DIRECTORY)
    try:
        anonymous_rw_probe(root)
        assert os.listdir(root) == []
    finally:
        os.close(root)


@pytest.mark.skipif(sys.platform != "linux", reason="real POSIX policy")
@pytest.mark.parametrize("variant", ["nosticky", "wrongowner", "privatewide", "acl"])
def test_domain_rejects_unaccredited_policy(variant):
    from studio_storage_guard.custody import CustodiedProbeDomain

    root = os.open("/scratch/" + variant, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(StorageGuardError):
            CustodiedProbeDomain.open(root)
    finally:
        os.close(root)


def _ask_rival(op, path):
    request = int(os.environ["RIVAL_REQUEST_FD"])
    response = int(os.environ["RIVAL_RESPONSE_FD"])
    os.write(request, (json.dumps({"op": op, "path": path}) + "\n").encode())
    data = bytearray()
    while not data.endswith(b"\n"):
        data.extend(os.read(response, 1))
    result = json.loads(data)
    credentials = result.pop("credentials")
    assert credentials["Uid"].split() == ["10001"] * 4
    assert credentials["Gid"].split() == ["10001"] * 4
    assert all(
        int(credentials[key], 16) == 0
        for key in ("CapEff", "CapPrm", "CapInh", "CapAmb")
    )
    assert credentials["NoNewPrivs"] == "1"
    return result


def _rival(op, path):
    result = _ask_rival(op, path)
    assert result == {"success": False, "errno": 13} or result == {
        "success": False,
        "errno": 1,
    }


@pytest.mark.skipif(sys.platform != "linux", reason="real competing UID10001")
@pytest.mark.parametrize(
    "boundary", ["delete-file", "delete-directory", "creator-close", "mkdir-open"]
)
def test_rival_cannot_reach_protected_names_at_boundaries(boundary, monkeypatch):
    from studio_storage_guard.custody import CustodiedProbeDomain

    root = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
    events = []
    operation = {
        "delete-file": "unlink",
        "delete-directory": "rmdir",
        "creator-close": "close",
        "mkdir-open": "open",
    }[boundary]
    original = getattr(os, operation)

    def schedule(*args, **kwargs):
        name = args[0]
        if operation == "close":
            try:
                path = os.readlink("/proc/self/fd/" + str(name))
            except OSError:
                path = ""
            if path.endswith("/target-file (deleted)"):
                assert os.fstat(name).st_nlink == 0
                assert os.fstat(name).st_size == 0
                path = path.removesuffix(" (deleted)")
            selected = path.endswith("/target-file")
        else:
            parent = kwargs.get("dir_fd")
            path = (
                os.readlink("/proc/self/fd/" + str(parent)) + "/" + str(name)
                if parent is not None
                else ""
            )
            selected = (
                name == "target-file"
                if operation == "unlink"
                else name == "target-empty"
                if operation == "rmdir"
                else str(name).startswith("probe-")
            )
        if selected and not events:
            _rival("write" if boundary == "creator-close" else "rename", path)
            _rival("rename", "/scratch/data/.storage-probes")
            events.append(path)
        return original(*args, **kwargs)

    try:
        with CustodiedProbeDomain.open(root) as domain:
            monkeypatch.setattr(os, operation, schedule)
            domain.probe()
            assert len(events) == 1
        assert os.listdir("/scratch/data/.storage-probes") == [".lock"]
    finally:
        os.close(root)


@pytest.mark.skipif(sys.platform != "linux", reason="real unknown preservation")
def test_unknown_residue_is_preserved_and_blocks_reopen(monkeypatch):
    from studio_storage_guard import custody

    original = custody._rename_noreplace
    path = []

    def introduce(fd, source, target):
        if not path:
            name = os.readlink("/proc/self/fd/" + str(fd)) + "/unknown"
            with open(name, "wb") as stream:
                stream.write(b"foreign-retained")
            path.append(name)
        return original(fd, source, target)

    monkeypatch.setattr(custody, "_rename_noreplace", introduce)
    root = os.open("/scratch/unknown", os.O_RDONLY | os.O_DIRECTORY)
    try:
        with (
            custody.CustodiedProbeDomain.open(root) as domain,
            pytest.raises(StorageGuardError),
        ):
            domain.probe()
        with open(path[0], "rb") as stream:
            assert stream.read() == b"foreign-retained"
        with pytest.raises(StorageGuardError):
            custody.CustodiedProbeDomain.open(root)
    finally:
        os.close(root)


@pytest.mark.skipif(sys.platform != "linux", reason="real descriptor lifetime")
def test_constructor_duplicate_failure_closes_already_owned_fd(monkeypatch):
    from studio_storage_guard.custody import CustodiedProbeDomain

    duplicate = os.dup
    captured = []

    def second_fails(fd):
        if captured:
            raise OSError("fd limit")
        value = duplicate(fd)
        captured.append(value)
        return value

    root = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
    try:
        monkeypatch.setattr(os, "dup", second_fails)
        with pytest.raises(StorageGuardError):
            CustodiedProbeDomain.open(root)
        with pytest.raises(OSError):
            os.fstat(captured[0])
        assert os.fstat(root)
    finally:
        os.close(root)


@pytest.mark.skipif(sys.platform != "linux", reason="actual consumer UID10001")
def test_consumer_uid10001_anonymous_rw_and_helper_runtime_rejection():
    assert _ask_rival("consumer", "") == {"success": True}
    assert _ask_rival("runtime", "") == {"runtime_rejected": True}


@pytest.mark.skipif(sys.platform != "linux", reason="unknown ACL query fail closed")
def test_acl_query_error_fails_closed(monkeypatch):
    from studio_storage_guard.custody import CustodiedProbeDomain

    observed = []

    def unknown(fd):
        observed.append(os.fstat(fd).st_ino)
        raise OSError("ACL query unavailable")

    root = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
    try:
        monkeypatch.setattr(os, "listxattr", unknown)
        with pytest.raises(StorageGuardError, match="^STORAGE_ROOT_INVALID$"):
            CustodiedProbeDomain.open(root)
        assert observed == [os.fstat(root).st_ino]
    finally:
        os.close(root)


@pytest.mark.skipif(sys.platform != "linux", reason="real source directory contents")
def test_source_modified_after_creation_is_preserved(monkeypatch):
    from studio_storage_guard import custody

    rename = custody._rename_noreplace
    created = []

    def modify(fd, source, target):
        if target == "target-absent":
            name = os.readlink("/proc/self/fd/" + str(fd)) + "/" + source + "/foreign"
            with open(name, "wb") as stream:
                stream.write(b"foreign-source")
            created.append(name.replace(source, target))
        return rename(fd, source, target)

    monkeypatch.setattr(custody, "_rename_noreplace", modify)
    root = os.open("/scratch/source-mutation", os.O_RDONLY | os.O_DIRECTORY)
    try:
        with (
            custody.CustodiedProbeDomain.open(root) as domain,
            pytest.raises(StorageGuardError),
        ):
            domain.probe()
        with open(created[0], "rb") as stream:
            assert stream.read() == b"foreign-source"
    finally:
        os.close(root)
