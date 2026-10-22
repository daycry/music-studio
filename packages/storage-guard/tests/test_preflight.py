from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from studio_storage_guard.preflight import verify_root

IDENTITY = UUID("12345678-1234-4234-8234-123456789abc")


class Backend:
    def __init__(self):
        self.closed = []
        self.probes = []
        self.opened = 0
        self.info = SimpleNamespace(
            device=12,
            inode=34,
            mount_id=7,
            fs_uuid=IDENTITY,
            fs_type="ext4",
            mount_root="/",
            writable=True,
        )

    def open_root(self, root):
        fd = 8 + self.opened
        self.opened += 1
        return fd

    def inspect(self, fd):
        return self.info

    def probe(self, fd):
        self.probes.append(fd)

    def close(self, fd):
        self.closed.append(fd)


def assert_all_descriptors_closed(backend):
    assert backend.closed == list(range(9, 8 + backend.opened)) + [8]


def test_valid_server_retains_fd_until_close():
    backend = Backend()
    lease = verify_root(Path("/data"), str(IDENTITY), "server", _backend=backend)
    assert lease.fd == 8
    assert backend.closed == [9]
    assert backend.probes == [8]
    lease.revalidate()
    lease.close()
    assert_all_descriptors_closed(backend)


@pytest.mark.parametrize(
    "field,value",
    [
        ("fs_uuid", UUID(int=0)),
        ("fs_type", "9p"),
        ("mount_root", "/other"),
        ("writable", False),
    ],
)
def test_wrong_server_mount_rejected_before_write(field, value):
    backend = Backend()
    setattr(backend.info, field, value)
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        verify_root(Path("/data"), str(IDENTITY), "server", _backend=backend)
    assert backend.probes == []
    assert_all_descriptors_closed(backend)


def test_engine_library_readonly_and_raw_same_uuid():
    from studio_storage_guard import preflight

    library = Backend()
    library.info.writable = False
    raw = Backend()
    raw.info.mount_root = "/tmp"
    with preflight.verify_engine_roots(
        "/data", "/data/tmp", str(IDENTITY), _backends=(library, raw)
    ) as pair:
        pair.revalidate()
        assert library.probes == []
        assert raw.probes == [8]
    assert_all_descriptors_closed(library)
    assert_all_descriptors_closed(raw)


def test_lease_revalidation_detects_changed_identity():
    backend = Backend()
    lease = verify_root("/data", str(IDENTITY), "server", _backend=backend)
    backend.info.inode += 1
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        lease.revalidate()
    lease.close()


def test_mountinfo_exact_id_and_escaped_root():
    from studio_storage_guard.preflight import _mount_record

    text = "6 1 8:1 /other /data rw - ext4 /dev/x rw\n7 1 8:2 /a\\040b /data\\134x ro,nosuid shared:2 - ext4 /dev/y rw\n"
    record = _mount_record(text, 7)
    assert record == ("/a b", "/data\\x", "ext4", False, "8:2")


@pytest.mark.parametrize(
    "text",
    [
        "7 1 8:2 / /data rw - ext4 /dev/x rw\n" * 2,
        "garbage",
        "7 1 8:2 / /data rx - ext4 /dev/x rw",
    ],
)
def test_mountinfo_rejects_ambiguous_or_malformed(text):
    from studio_storage_guard.preflight import _mount_record

    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        _mount_record(text, 7)


def test_native_open_uses_directory_nofollow_per_component(monkeypatch):
    import os

    from studio_storage_guard import preflight

    calls = []
    monkeypatch.setattr(os, "O_DIRECTORY", 65536, raising=False)
    monkeypatch.setattr(os, "O_NOFOLLOW", 131072, raising=False)
    monkeypatch.setattr(os, "O_CLOEXEC", 524288, raising=False)
    monkeypatch.setattr(
        os,
        "open",
        lambda path, flags, **kw: calls.append((path, flags, kw)) or len(calls) + 10,
    )
    monkeypatch.setattr(os, "close", lambda fd: None)
    backend = preflight.LinuxBackend()
    fd = backend.open_root("/data/tmp")
    assert fd == 13
    assert [c[0] for c in calls] == ["/", "data", "tmp"]
    assert all(c[1] & os.O_NOFOLLOW and c[1] & os.O_DIRECTORY for c in calls)
    assert calls[1][2]["dir_fd"] == 11
    assert calls[2][2]["dir_fd"] == 12


def test_native_inspect_uses_uuid_ioctl_and_exact_fd_mount(monkeypatch):
    import io
    import os
    import stat
    import sys

    from studio_storage_guard import preflight

    fake = SimpleNamespace(
        ioctl=lambda fd, request, data, mutate: data.__setitem__(
            slice(None), bytes([16]) + IDENTITY.bytes
        )
    )
    monkeypatch.setitem(sys.modules, "fcntl", fake)
    monkeypatch.setattr(
        os,
        "fstat",
        lambda fd: SimpleNamespace(st_dev=2050, st_ino=34, st_mode=stat.S_IFDIR),
    )
    monkeypatch.setattr(os, "major", lambda dev: 8, raising=False)
    monkeypatch.setattr(os, "minor", lambda dev: 2, raising=False)
    monkeypatch.setattr(os, "readlink", lambda path: "/data")
    monkeypatch.setattr(os, "close", lambda fd: None)
    monkeypatch.setattr(preflight.LinuxBackend, "open_root", lambda self, path: 9)
    monkeypatch.setattr(
        "builtins.open",
        lambda path, **kw: io.StringIO(
            "mnt_id:\t7\n"
            if "fdinfo" in str(path)
            else "7 1 8:2 / /data rw - ext4 /dev/x rw\n"
        ),
    )
    info = preflight.LinuxBackend().inspect(8)
    assert info.fs_uuid == IDENTITY
    assert info.mount_id == 7
    assert info.fs_type == "ext4" and info.writable
    assert info.device == 2050 and info.inode == 34


def test_revalidate_masks_private_os_error_and_enter_releases():
    backend = Backend()
    lease = verify_root("/data", str(IDENTITY), "server", _backend=backend)
    backend.inspect = lambda fd: (_ for _ in ()).throw(OSError("private path"))
    with pytest.raises(Exception, match="^STORAGE_ROOT_INVALID$"):
        lease.__enter__()
    assert_all_descriptors_closed(backend)


def test_pair_enter_failure_releases_both():
    from studio_storage_guard.preflight import verify_engine_roots

    library, raw = Backend(), Backend()
    library.info.writable = False
    raw.info.mount_root = "/tmp"
    pair = verify_engine_roots(
        "/data", "/data/tmp", str(IDENTITY), _backends=(library, raw)
    )
    raw.info.inode += 1
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        pair.__enter__()
    assert_all_descriptors_closed(library)
    assert_all_descriptors_closed(raw)


def test_native_inspect_rejects_rebound_path(monkeypatch):
    import io
    import os
    import stat
    import sys

    from studio_storage_guard import preflight

    monkeypatch.setitem(
        sys.modules,
        "fcntl",
        SimpleNamespace(
            ioctl=lambda fd, req, buf, mut: buf.__setitem__(
                slice(None), bytes([16]) + IDENTITY.bytes
            )
        ),
    )
    monkeypatch.setattr(
        os,
        "fstat",
        lambda fd: SimpleNamespace(
            st_dev=2050, st_ino=34 if fd == 8 else 99, st_mode=stat.S_IFDIR
        ),
    )
    monkeypatch.setattr(os, "major", lambda dev: 8, raising=False)
    monkeypatch.setattr(os, "minor", lambda dev: 2, raising=False)
    monkeypatch.setattr(os, "readlink", lambda path: "/data")
    monkeypatch.setattr(os, "close", lambda fd: None)
    monkeypatch.setattr(
        "builtins.open",
        lambda path, **kw: io.StringIO(
            "mnt_id:\t7\n"
            if "fdinfo" in str(path)
            else "7 1 8:2 / /data rw - ext4 /dev/x rw\n"
        ),
    )
    monkeypatch.setattr(preflight.LinuxBackend, "open_root", lambda self, path: 9)
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        preflight.LinuxBackend().inspect(8)


@pytest.mark.parametrize("root", ["relative", "/data/../tmp"])
def test_native_open_rejects_noncanonical_root(root):
    from studio_storage_guard.preflight import LinuxBackend

    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        LinuxBackend().open_root(root)


def test_native_open_failure_releases_ancestor(monkeypatch):
    import os

    from studio_storage_guard.preflight import LinuxBackend

    monkeypatch.setattr(os, "O_DIRECTORY", 65536, raising=False)
    monkeypatch.setattr(os, "O_NOFOLLOW", 131072, raising=False)
    monkeypatch.setattr(os, "O_CLOEXEC", 524288, raising=False)
    calls = []

    def open_part(path, flags, **kw):
        if path == "/":
            return 8
        raise OSError("alias")

    monkeypatch.setattr(os, "open", open_part)
    monkeypatch.setattr(os, "close", calls.append)
    with pytest.raises(OSError):
        LinuxBackend().open_root("/alias")
    assert calls == [8]


def test_pair_raw_uuid_mismatch_releases_library():
    from studio_storage_guard.preflight import verify_engine_roots

    library, raw = Backend(), Backend()
    library.info.writable = False
    raw.info.mount_root = "/tmp"
    raw.info.fs_uuid = UUID(int=0)
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        verify_engine_roots(
            "/data", "/data/tmp", str(IDENTITY), _backends=(library, raw)
        )
    assert_all_descriptors_closed(library)
    assert_all_descriptors_closed(raw)


def test_closed_lease_cannot_be_reused():
    backend = Backend()
    lease = verify_root("/data", str(IDENTITY), "server", _backend=backend)
    lease.close()
    lease.close()
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        lease.revalidate()
    assert_all_descriptors_closed(backend)


def test_verify_rejects_inspection_drift_after_probe():
    backend = Backend()
    backend.probe = lambda fd: setattr(backend.info, "mount_id", 999)
    # The receipt must snapshot fields, not retain a mutable syscall object.
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        verify_root("/data", str(IDENTITY), "server", _backend=backend)
    assert_all_descriptors_closed(backend)


def test_engine_pair_rejects_distinct_device_with_copied_uuid():
    from studio_storage_guard.preflight import verify_engine_roots

    library, raw = Backend(), Backend()
    library.info.writable = False
    raw.info.mount_root = "/tmp"
    raw.info.device = 99
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        verify_engine_roots(
            "/data", "/data/tmp", str(IDENTITY), _backends=(library, raw)
        )
    assert_all_descriptors_closed(library)
    assert_all_descriptors_closed(raw)


def test_revalidate_reopens_original_requested_root():
    backend = Backend()
    paths = []
    moved = []

    def open_root(path):
        paths.append(path)
        if path == "/data" and moved:
            raise OSError("original mount moved")
        return 8 if len(paths) == 1 else 9

    backend.open_root = open_root
    lease = verify_root("/data", str(IDENTITY), "server", _backend=backend)
    moved.append(True)
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        lease.revalidate()
    lease.close()
    assert paths[-1] == "/data"


def test_raw_acquisition_revalidates_library_and_closes_pair_on_drift():
    from studio_storage_guard.preflight import verify_engine_roots

    library, raw = Backend(), Backend()
    library.info.writable = False
    raw.info.mount_root = "/tmp"
    raw.probe = lambda fd: setattr(library.info, "writable", True)
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        verify_engine_roots(
            "/data", "/data/tmp", str(IDENTITY), _backends=(library, raw)
        )
    assert_all_descriptors_closed(library)
    assert_all_descriptors_closed(raw)


def test_acquisition_rejects_original_path_moved_during_probe():
    backend = Backend()
    moved = []
    opener = backend.open_root

    def open_root(root):
        if moved:
            raise OSError("mount moved off original requested path")
        return opener(root)

    backend.open_root = open_root
    backend.probe = lambda fd: moved.append(True)
    with pytest.raises(Exception, match="STORAGE_ROOT_INVALID"):
        verify_root("/data", str(IDENTITY), "server", _backend=backend)
    assert_all_descriptors_closed(backend)


@pytest.fixture
def default_backend_seams(monkeypatch):
    from studio_storage_guard import client, custody, preflight

    backend = Backend()
    paths, events = [], []

    def open_root(self, root):
        paths.append(root)
        return backend.open_root(root)

    monkeypatch.setattr(preflight.LinuxBackend, "open_root", open_root)
    monkeypatch.setattr(
        preflight.LinuxBackend, "inspect", lambda self, fd: backend.inspect(fd)
    )
    monkeypatch.setattr(
        preflight.LinuxBackend, "close", lambda self, fd: backend.close(fd)
    )
    monkeypatch.setattr(
        client.Client,
        "perform",
        lambda self, fd, role, uuid: events.append(
            ("ipc", self.data_root, fd, role, uuid)
        ),
    )
    monkeypatch.setattr(
        custody, "anonymous_rw_probe", lambda fd: events.append(("rw", fd))
    )
    return backend, paths, events


def test_default_server_wires_fresh_ipc_and_anonymous_probe(default_backend_seams):
    backend, paths, events = default_backend_seams
    with verify_root("/studio/data", str(IDENTITY), "server") as lease:
        assert events == [
            ("ipc", "/studio/data", lease.fd, "server", str(IDENTITY)),
            ("rw", lease.fd),
        ]
        assert set(paths) == {"/studio/data"}
    assert_all_descriptors_closed(backend)


def test_default_library_never_calls_ipc_or_writes(default_backend_seams):
    backend, paths, events = default_backend_seams
    backend.info.writable = False
    with verify_root("/studio/data", str(IDENTITY), "library"):
        assert events == []
        assert set(paths) == {"/studio/data"}
    assert_all_descriptors_closed(backend)


@pytest.mark.parametrize("operation", ["ipc", "rw"])
def test_default_operation_failure_closes_root(
    default_backend_seams, monkeypatch, operation
):
    from studio_storage_guard import client, custody

    backend, _, events = default_backend_seams

    def fail(*args):
        raise OSError("private details")

    if operation == "ipc":
        monkeypatch.setattr(client.Client, "perform", fail)
    else:
        monkeypatch.setattr(custody, "anonymous_rw_probe", fail)
    with pytest.raises(Exception, match="^STORAGE_ROOT_INVALID$"):
        verify_root("/studio/data", str(IDENTITY), "server")
    assert not any(event[0] == "rw" for event in events)
    assert_all_descriptors_closed(backend)


@pytest.mark.parametrize("operation", ["ipc", "rw"])
@pytest.mark.parametrize("drift", ["identity", "original_path"])
def test_default_revalidates_between_operations_and_before_lease(
    default_backend_seams, monkeypatch, operation, drift
):
    from studio_storage_guard import client, custody, preflight

    backend, paths, events = default_backend_seams

    def mutate(*args):
        events.append((operation,))
        if drift == "identity":
            backend.info.inode += 1
        else:

            def moved(self, root):
                paths.append(root)
                raise OSError("original path moved")

            monkeypatch.setattr(preflight.LinuxBackend, "open_root", moved)

    if operation == "ipc":
        monkeypatch.setattr(client.Client, "perform", mutate)
    else:
        monkeypatch.setattr(custody, "anonymous_rw_probe", mutate)
    with pytest.raises(Exception, match="^STORAGE_ROOT_INVALID$"):
        verify_root("/studio/data", str(IDENTITY), "server")
    assert [event[0] for event in events] == (
        ["ipc"] if operation == "ipc" else ["ipc", "rw"]
    )
    assert set(paths) == {"/studio/data"}
    assert_all_descriptors_closed(backend)


@pytest.mark.parametrize("field,value", [("fs_uuid", UUID(int=0)), ("writable", False)])
def test_default_rejects_before_any_operation(default_backend_seams, field, value):
    backend, _, events = default_backend_seams
    setattr(backend.info, field, value)
    with pytest.raises(Exception, match="^STORAGE_ROOT_INVALID$"):
        verify_root("/studio/data", str(IDENTITY), "server")
    assert events == []
    assert_all_descriptors_closed(backend)


@pytest.mark.parametrize("failure", [None, "ipc", "rw", "library_drift"])
def test_default_engine_roots_use_library_control_and_raw_fd(
    default_backend_seams, monkeypatch, failure
):
    from studio_storage_guard import client, custody, preflight

    backend, paths, events = default_backend_seams
    raw_fd = []
    library_rw = []

    def inspect(self, fd):
        path = paths[fd - 8]
        raw = path == "/studio/data/tmp"
        if raw:
            raw_fd.append(fd)
        return SimpleNamespace(
            **(
                vars(backend.info)
                | {
                    "mount_root": "/tmp" if raw else "/",
                    "writable": raw or bool(library_rw),
                }
            )
        )

    monkeypatch.setattr(preflight.LinuxBackend, "inspect", inspect)
    if failure:

        def fail(*args):
            raise OSError("helper or anonymous write failed")

        if failure == "ipc":
            monkeypatch.setattr(client.Client, "perform", fail)
        elif failure == "rw":
            monkeypatch.setattr(custody, "anonymous_rw_probe", fail)
        else:
            monkeypatch.setattr(
                custody, "anonymous_rw_probe", lambda fd: library_rw.append(True)
            )
        with pytest.raises(Exception, match="^STORAGE_ROOT_INVALID$"):
            preflight.verify_engine_roots(
                "/studio/data", "/studio/data/tmp", str(IDENTITY)
            )
        assert sorted(backend.closed) == list(range(8, 8 + backend.opened))
        return
    with preflight.verify_engine_roots(
        "/studio/data", "/studio/data/tmp", str(IDENTITY)
    ) as pair:
        assert events == [
            ("ipc", "/studio/data", pair.raw.fd, "raw", str(IDENTITY)),
            ("rw", pair.raw.fd),
        ]
        assert pair.library.fd != pair.raw.fd
        assert pair.raw.fd in raw_fd
    assert sorted(backend.closed) == list(range(8, 8 + backend.opened))


def test_default_each_acquisition_performs_new_operations(default_backend_seams):
    _, _, events = default_backend_seams
    for _ in range(2):
        with verify_root("/studio/data", str(IDENTITY), "server"):
            pass
    assert [event[0] for event in events] == ["ipc", "rw", "ipc", "rw"]


def test_default_standalone_raw_uses_parent_control_root(default_backend_seams):
    backend, paths, events = default_backend_seams
    backend.info.mount_root = "/tmp"
    with verify_root("/studio/data/tmp", str(IDENTITY), "raw") as lease:
        assert events == [
            ("ipc", "/studio/data", lease.fd, "raw", str(IDENTITY)),
            ("rw", lease.fd),
        ]
        assert set(paths) == {"/studio/data/tmp"}
    assert_all_descriptors_closed(backend)
