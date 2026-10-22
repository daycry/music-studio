import array
import ctypes
import json
import os
import socket
import stat
import sys
from types import SimpleNamespace
from uuid import UUID

import pytest
from studio_storage_guard import helper, protocol
from studio_storage_guard.preflight import StorageGuardError

UUID_TEXT = "bda4915f-04df-4e3c-94d6-39817d60185e"
REQUEST = {"version": 1, "role": "server", "challenge": "ab" * 32}


def test_main_requires_deployment_uuid(monkeypatch):
    monkeypatch.delenv("STUDIO_STORAGE_UUID", raising=False)
    assert helper.main() == 1


def test_main_runs_serially_and_releases_owned_resources(monkeypatch):
    monkeypatch.setenv("STUDIO_STORAGE_UUID", UUID_TEXT)
    events = []

    class Authority:
        def __init__(self, uuid):
            events.append(("authority", uuid))

        def close(self):
            events.append(("authority-close",))

    class Server:
        def __init__(self, authority):
            events.append(("server",))

        def serve_once(self):
            events.append(("serve",))
            raise KeyboardInterrupt()

        def close(self):
            events.append(("server-close",))

    monkeypatch.setattr(helper, "Authority", Authority)
    monkeypatch.setattr(helper, "Server", Server)
    assert helper.main() == 0
    assert events == [
        ("authority", UUID_TEXT),
        ("server",),
        ("serve",),
        ("server-close",),
        ("authority-close",),
    ]


def authority(monkeypatch):
    value = helper.Authority.__new__(helper.Authority)
    value.uuid = UUID(UUID_TEXT)
    value.roots = {"server": 10, "raw": 20}
    infos = {
        10: SimpleNamespace(st_dev=3, st_ino=1, st_mode=stat.S_IFDIR | 0o1770),
        20: SimpleNamespace(st_dev=3, st_ino=2, st_mode=stat.S_IFDIR | 0o1770),
        30: SimpleNamespace(st_dev=3, st_ino=1, st_mode=stat.S_IFDIR | 0o1770),
    }
    monkeypatch.setattr(helper.os, "fstat", infos.__getitem__)
    monkeypatch.setattr(helper, "filesystem_uuid", lambda fd: value.uuid)
    monkeypatch.setattr(helper, "_runtime", lambda: None)
    value.seals = {
        role: (infos[fd].st_dev, infos[fd].st_ino, infos[fd].st_mode)
        for role, fd in value.roots.items()
    }
    value.paths = {"server": "/data", "raw": "/data/tmp"}

    class Backend:
        def open_root(self, path):
            return 10 if path == "/data" else 20

    monkeypatch.setattr(helper, "LinuxBackend", Backend)
    monkeypatch.setattr(helper.os, "close", lambda fd: None)
    monkeypatch.setattr(
        helper,
        "_directory",
        lambda fd, uid, mode: (infos[fd].st_dev, infos[fd].st_ino, infos[fd].st_mode),
    )
    return value, infos


@pytest.mark.parametrize("variant", ["inode", "device", "file", "uuid"])
def test_wrong_received_root_rejected_before_probe(monkeypatch, variant):
    value, infos = authority(monkeypatch)
    if variant == "uuid":
        monkeypatch.setattr(
            helper,
            "filesystem_uuid",
            lambda fd: UUID(int=1) if fd == 30 else value.uuid,
        )
    else:
        setattr(
            infos[30],
            {"inode": "st_ino", "device": "st_dev", "file": "st_mode"}[variant],
            {"inode": 99, "device": 99, "file": stat.S_IFREG}[variant],
        )
    with pytest.raises(StorageGuardError):
        value.perform(30, REQUEST)


def test_received_descriptor_drives_fresh_domain_and_cleanup(monkeypatch):
    value, _ = authority(monkeypatch)
    events = []

    class Domain:
        @classmethod
        def open(cls, fd):
            events.append(("open", fd))
            return cls()

        def __enter__(self):
            return self

        def probe(self):
            events.append(("probe",))

        def __exit__(self, *args):
            events.append(("close",))

    monkeypatch.setattr(helper, "CustodiedProbeDomain", Domain)
    result = value.perform(30, REQUEST)
    assert events == [("open", 30), ("probe",), ("close",)]
    assert result == REQUEST | {"uuid": UUID_TEXT, "device": 3, "inode": 1}


@pytest.mark.parametrize("variant", ["root-drift", "uuid-drift", "extra-field"])
def test_authority_rechecks_after_probe(monkeypatch, variant):
    value, infos = authority(monkeypatch)

    class Domain:
        @classmethod
        def open(cls, fd):
            return cls()

        def __enter__(self):
            return self

        def probe(self):
            if variant == "root-drift":
                infos[30].st_ino = 90
            elif variant == "uuid-drift":
                monkeypatch.setattr(helper, "filesystem_uuid", lambda fd: UUID(int=1))

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(helper, "CustodiedProbeDomain", Domain)
    with pytest.raises(StorageGuardError):
        value.perform(
            30, REQUEST | ({"path": "/other"} if variant == "extra-field" else {})
        )


def _credentials(uid):
    os.setgroups([])
    os.setresgid(10001, 10001, 10001)
    os.setresuid(uid, uid, uid)
    assert ctypes.CDLL(None).prctl(38, 1, 0, 0, 0) == 0
    with open("/proc/self/status") as stream:
        status = dict(line.split(":", 1) for line in stream if ":" in line)
    assert all(
        int(status[key], 16) == 0 for key in ("CapEff", "CapPrm", "CapInh", "CapAmb")
    )
    assert status["NoNewPrivs"].strip() == "1"


def _native_exchange(uid=10001, variant="success", use_client=False):
    # TMPFS UUID ioctl is the only seam; sockets, IDs, FDs and domain syscalls are real.
    ready_r, ready_w = os.pipe()
    report_r, report_w = os.pipe()
    consumer_r, consumer_w = os.pipe()
    path = "/scratch/data/.storage-control/guard.sock"
    server = os.fork()
    if server == 0:
        try:
            os.close(ready_r)
            os.close(report_r)
            _credentials(19000)
            helper.filesystem_uuid = lambda fd: UUID(UUID_TEXT)
            authority = helper.Authority(UUID_TEXT, "/scratch/data")
            endpoint = helper.Server(authority, "/scratch/data")
            listener = endpoint.listener
            listener.settimeout(2)
            os.write(ready_w, b"1")
            before = len(os.listdir("/proc/self/fd"))
            try:
                endpoint.serve_once()
                outcome = "success"
            except (StorageGuardError, OSError):
                outcome = "rejected"
            after = len(os.listdir("/proc/self/fd"))
            endpoint.close()
            authority.close()
            os.write(
                report_w,
                json.dumps(
                    {
                        "outcome": outcome,
                        "leak": after - before,
                        "clean": os.listdir("/scratch/data/.storage-probes")
                        == [".lock"],
                    }
                ).encode(),
            )
            os._exit(0)
        except (
            OSError,
            ValueError,
            RuntimeError,
            AssertionError,
            AttributeError,
        ) as error:
            os.write(report_w, repr(error).encode())
            os._exit(1)
    os.close(ready_w)
    os.close(report_w)
    assert os.read(ready_r, 1) == b"1"
    os.close(ready_r)
    consumer = os.fork()
    if consumer == 0:
        try:
            if uid != 0:
                _credentials(uid)
            if use_client:
                from studio_storage_guard import client

                # Only ext4 inspection/UUID are seams on this owned TMPFS fixture.
                original_backend = client.LinuxBackend

                class Backend(original_backend):
                    def inspect(self, fd):
                        info = os.fstat(fd)
                        from types import SimpleNamespace

                        return SimpleNamespace(
                            device=info.st_dev,
                            inode=info.st_ino,
                            mount_id=1,
                            fs_uuid=UUID(UUID_TEXT),
                            fs_type="ext4",
                            mount_root="/",
                            writable=True,
                        )

                client.LinuxBackend = Backend
                root = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
                try:
                    result = client.Client("/scratch/data").perform(
                        root, "server", UUID_TEXT
                    )
                    assert result["inode"] == os.fstat(root).st_ino
                    assert result["uuid"] == UUID_TEXT
                    os.write(consumer_w, b"success")
                except StorageGuardError:
                    os.write(consumer_w, b"rejected")
                finally:
                    os.close(root)
                os._exit(0)
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            connection.settimeout(1)
            connection.connect(path)
            fd = os.open(
                "/scratch/data" if variant != "wrong-root" else "/scratch/data/tmp",
                os.O_RDONLY | os.O_DIRECTORY,
            )
            ancillary = [
                (
                    socket.SOL_SOCKET,
                    socket.SCM_RIGHTS,
                    array.array("i", [fd, fd] if variant == "extra-fd" else [fd]),
                )
            ]
            connection.sendmsg([protocol.encode(REQUEST)], ancillary)
            if variant != "deadline":
                connection.shutdown(socket.SHUT_WR)
            if variant == "disconnect":
                connection.close()
            else:
                try:
                    protocol.receive(connection, response=True)
                except StorageGuardError:
                    pass
            os.close(fd)
            os.write(consumer_w, b"done")
            os._exit(0)
        except (OSError, ValueError, RuntimeError, AssertionError, AttributeError):
            os._exit(1)
    os.waitpid(consumer, 0)
    os.close(consumer_w)
    consumer_report = os.read(consumer_r, 4096)
    os.close(consumer_r)
    _, status = os.waitpid(server, 0)
    report = os.read(report_r, 4096)
    os.close(report_r)
    assert status == 0, report
    result = json.loads(report)
    result["consumer"] = consumer_report.decode()
    return result


@pytest.mark.skipif(
    sys.platform != "linux", reason="native distinct UID and SCM_RIGHTS"
)
def test_native_wrong_peer_fails_before_probe():
    result = _native_exchange(uid=10002)
    assert result["outcome"] == "rejected"
    assert result["leak"] == 0


@pytest.mark.skipif(
    sys.platform != "linux", reason="native distinct UID and SCM_RIGHTS"
)
@pytest.mark.parametrize(
    "variant", ["success", "extra-fd", "wrong-root", "deadline", "disconnect"]
)
def test_native_helper_authenticated_exchange(variant):
    result = _native_exchange(variant=variant)
    assert result["outcome"] == ("success" if variant == "success" else "rejected")
    assert result["leak"] == 0
    if variant == "success":
        assert result["clean"]


@pytest.mark.skipif(
    sys.platform != "linux", reason="native protected control and instance lock"
)
@pytest.mark.parametrize("variant", ["busy-lock", "wide-control"])
def test_native_endpoint_rejects_before_socket_creation(variant):
    incoming, outgoing = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            _credentials(19000)
            helper.filesystem_uuid = lambda fd: UUID(UUID_TEXT)
            authority = helper.Authority(UUID_TEXT, "/scratch/data")
            if variant == "busy-lock":
                import fcntl

                lock = os.open(
                    "/scratch/data/.storage-control/.lock",
                    os.O_CREAT | os.O_RDWR,
                    0o600,
                )
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                os.chmod("/scratch/data/.storage-control", 0o770)
            try:
                server = helper.Server(authority, "/scratch/data")
            except StorageGuardError:
                result = "rejected"
            else:
                server.close()
                result = "allowed"
            authority.close()
            if variant == "wide-control":
                os.chmod("/scratch/data/.storage-control", 0o750)
            os.write(outgoing, result.encode())
            os._exit(0)
        except (
            OSError,
            ValueError,
            RuntimeError,
            AssertionError,
            AttributeError,
        ) as error:
            os.write(outgoing, repr(error).encode())
            os._exit(1)
    os.close(outgoing)
    _, status = os.waitpid(pid, 0)
    report = os.read(incoming, 4096)
    os.close(incoming)
    assert status == 0, report
    assert report == b"rejected"


@pytest.mark.skipif(
    sys.platform != "linux", reason="native helper authority configuration"
)
@pytest.mark.parametrize("variant", ["wrong-uid", "uuid-authority"])
def test_native_authority_constructor_rejects_invalid_config(variant):
    incoming, outgoing = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            _credentials(10001 if variant == "wrong-uid" else 19000)
            helper.filesystem_uuid = lambda fd: (
                UUID(int=1) if variant == "uuid-authority" else UUID(UUID_TEXT)
            )
            try:
                authority = helper.Authority(UUID_TEXT, "/scratch/data")
            except StorageGuardError:
                result = "rejected"
            else:
                authority.close()
                result = "allowed"
            os.write(outgoing, result.encode())
            os._exit(0)
        except (
            OSError,
            ValueError,
            RuntimeError,
            AssertionError,
            AttributeError,
        ) as error:
            os.write(outgoing, repr(error).encode())
            os._exit(1)
    os.close(outgoing)
    _, status = os.waitpid(pid, 0)
    report = os.read(incoming, 4096)
    os.close(incoming)
    assert status == 0, report
    assert report == b"rejected"


@pytest.mark.skipif(
    sys.platform != "linux", reason="native conservative socket cleanup"
)
def test_native_endpoint_preserves_unknown_replacement():
    incoming, outgoing = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            _credentials(19000)
            helper.filesystem_uuid = lambda fd: UUID(UUID_TEXT)
            authority = helper.Authority(UUID_TEXT, "/scratch/data")
            endpoint = helper.Server(authority, "/scratch/data")
            path = "/scratch/data/.storage-control/guard.sock"
            os.unlink(path)
            with open(path, "wb") as stream:
                stream.write(b"foreign")
            try:
                endpoint.close()
            except StorageGuardError:
                pass
            preserved = os.path.exists(path)
            if preserved:
                with open(path, "rb") as stream:
                    assert stream.read() == b"foreign"
                os.unlink(path)  # fixture created it, not product recovery.
            authority.close()
            os.write(outgoing, str(preserved).encode())
            os._exit(0)
        except (
            OSError,
            ValueError,
            RuntimeError,
            AssertionError,
            AttributeError,
        ) as error:
            os.write(outgoing, repr(error).encode())
            os._exit(1)
    os.close(outgoing)
    _, status = os.waitpid(pid, 0)
    report = os.read(incoming, 4096)
    os.close(incoming)
    assert status == 0, report
    assert report == b"True"


@pytest.mark.skipif(sys.platform != "linux", reason="ioctl ABI")
def test_filesystem_uuid_ioctl_shape(monkeypatch):
    import fcntl

    def ioctl(fd, code, data, mutate):
        assert code == 0x80111500 and len(data) == 17 and mutate
        data[:] = bytes([16]) + UUID(UUID_TEXT).bytes

    monkeypatch.setattr(fcntl, "ioctl", ioctl)
    assert helper.filesystem_uuid(10) == UUID(UUID_TEXT)

    def bad(fd, code, data, mutate):
        data[0] = 15

    monkeypatch.setattr(fcntl, "ioctl", bad)
    with pytest.raises(StorageGuardError):
        helper.filesystem_uuid(10)


@pytest.mark.skipif(
    sys.platform != "linux", reason="native instance exclusion and close ownership"
)
def test_native_second_instance_and_idempotent_close():
    incoming, outgoing = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            _credentials(19000)
            helper.filesystem_uuid = lambda fd: UUID(UUID_TEXT)
            authority = helper.Authority(UUID_TEXT, "/scratch/data")
            endpoint = helper.Server(authority, "/scratch/data")
            original = os.stat("/scratch/data/.storage-control/guard.sock")
            with pytest.raises(StorageGuardError):
                helper.Server(authority, "/scratch/data")
            assert (
                os.stat("/scratch/data/.storage-control/guard.sock").st_ino
                == original.st_ino
            )
            endpoint.close()
            retained = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
            endpoint.close()
            os.fstat(retained)
            os.close(retained)
            authority.close()
            os.write(outgoing, b"passed")
            os._exit(0)
        except (
            OSError,
            ValueError,
            RuntimeError,
            AssertionError,
            AttributeError,
        ) as error:
            os.write(outgoing, repr(error).encode())
            os._exit(1)
    os.close(outgoing)
    _, status = os.waitpid(pid, 0)
    report = os.read(incoming, 4096)
    os.close(incoming)
    assert status == 0, report
    assert report == b"passed"


@pytest.mark.parametrize(
    "failure", ["listener", "lock", "control", "seal", "interrupt"]
)
def test_close_releases_every_owned_handle_without_retry(monkeypatch, failure):
    endpoint = helper.Server.__new__(helper.Server)
    endpoint.control, endpoint.lock = 20, 10
    endpoint.socket_seal = (1, 2, 3)
    primary = (
        RuntimeError("listener failed")
        if failure == "listener"
        else OSError(5, "close failed")
    )
    if failure == "interrupt":
        primary = KeyboardInterrupt()
    if failure == "seal":
        primary = StorageGuardError()
    events = []

    class Listener:
        def close(self):
            events.append("listener")
            if failure == "listener":
                raise primary

    endpoint.listener = Listener()
    monkeypatch.setattr(
        helper,
        "_identity",
        lambda info: (9, 9, 9) if failure == "seal" else endpoint.socket_seal,
    )

    def close(fd):
        events.append(fd)
        if fd == 10 and failure in {"listener", "lock", "interrupt"}:
            raise OSError(9, "secondary") if failure == "listener" else primary
        if fd == 20 and failure == "control":
            raise primary

    monkeypatch.setattr(
        helper,
        "os",
        SimpleNamespace(
            close=close,
            stat=lambda *args, **kwargs: None,
            unlink=lambda *args, **kwargs: events.append("unlink"),
        ),
    )
    expected = (
        type(primary)
        if failure in {"listener", "seal", "interrupt"}
        else StorageGuardError
    )
    with pytest.raises(expected) as caught:
        endpoint.close()
    if failure in {"listener", "seal", "interrupt"}:
        assert (
            caught.value is primary
            if failure != "seal"
            else isinstance(caught.value, StorageGuardError)
        )
    assert events[-2:] == [10, 20]
    assert (endpoint.listener, endpoint.lock, endpoint.control) == (None, None, None)
    previous = list(events)
    endpoint.close()
    assert events == previous
