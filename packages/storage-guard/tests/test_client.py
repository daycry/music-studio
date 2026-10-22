import io
import socket
import stat
import sys
from types import SimpleNamespace
from uuid import UUID

import pytest
from studio_storage_guard import client
from studio_storage_guard.preflight import StorageGuardError

UUID_TEXT = "bda4915f-04df-4e3c-94d6-39817d60185e"


@pytest.mark.parametrize("variant", ["uid", "gid", "caps", "nnp"])
def test_consumer_runtime_blocks_wrong_authority(monkeypatch, variant):
    monkeypatch.setattr(
        client.os,
        "getresuid",
        lambda: (10001, 10001, 10001) if variant != "uid" else (0, 10001, 10001),
        raising=False,
    )
    monkeypatch.setattr(
        client.os,
        "getresgid",
        lambda: (10001, 10001, 10001) if variant != "gid" else (10001, 0, 10001),
        raising=False,
    )
    status = (
        "CapEff: 0\nCapPrm: 0\nCapInh: 0\nCapAmb: "
        + ("1" if variant == "caps" else "0")
        + "\nNoNewPrivs: "
        + ("0" if variant == "nnp" else "1")
        + "\n"
    )
    monkeypatch.setattr(
        client, "open", lambda *args, **kwargs: io.StringIO(status), raising=False
    )
    with pytest.raises(StorageGuardError):
        client._consumer_runtime()


@pytest.mark.parametrize(
    "variant", ["socket-mode", "socket-owner", "socket-link", "control-policy"]
)
def test_socket_address_checks_protected_endpoint(monkeypatch, variant):
    class Backend:
        def open_root(self, path):
            return 10

    monkeypatch.setattr(client, "LinuxBackend", Backend)
    monkeypatch.setattr(client.os, "open", lambda *args, **kwargs: 20)
    monkeypatch.setattr(client.os, "close", lambda fd: None)

    def directory(fd, uid, mode):
        if variant == "control-policy" and fd == 20:
            raise StorageGuardError()

    # This is an explicit policy seam, not POSIX mode evidence.
    monkeypatch.setattr(client, "_directory", directory, raising=False)
    info = SimpleNamespace(
        st_mode=stat.S_IFSOCK | (0o666 if variant == "socket-mode" else 0o660),
        st_uid=10001 if variant == "socket-owner" else 19000,
        st_gid=10001,
    )
    if variant == "socket-link":
        info.st_mode = stat.S_IFLNK | 0o660
    monkeypatch.setattr(client.os, "stat", lambda *args, **kwargs: info)
    monkeypatch.setattr(
        client.os, "listxattr", lambda *args, **kwargs: [], raising=False
    )
    with pytest.raises(StorageGuardError):
        client._socket_address("/data")


class Connection:
    def settimeout(self, value):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def connect(self, *args):
        pass

    def sendmsg(self, *args):
        return len(args[0][0])

    def shutdown(self, *args):
        pass


@pytest.fixture
def valid_client(monkeypatch):
    monkeypatch.setattr(socket, "AF_UNIX", 1, raising=False)
    monkeypatch.setattr(socket, "SOCK_SEQPACKET", 5, raising=False)
    monkeypatch.setattr(socket, "SCM_RIGHTS", 1, raising=False)
    monkeypatch.setattr(client.socket, "socket", lambda *args: Connection())
    monkeypatch.setattr(client, "_consumer_runtime", lambda: None)
    monkeypatch.setattr(
        client, "_socket_address", lambda path: path + "/.storage-control/guard.sock"
    )
    monkeypatch.setattr(
        client.protocol, "authenticate", lambda *args: (0, 19000, 10001)
    )

    class Backend:
        def inspect(self, fd):
            return SimpleNamespace(
                device=3,
                inode=1,
                mount_id=1,
                fs_uuid=UUID(UUID_TEXT),
                fs_type="ext4",
                mount_root="/",
                writable=True,
            )

        def open_root(self, path):
            return 20

        def close(self, fd):
            pass

    monkeypatch.setattr(client, "LinuxBackend", Backend)

    def receive(*args, **kwargs):
        return {
            "version": 1,
            "role": "server",
            "challenge": "ab" * 32,
            "uuid": UUID_TEXT,
            "device": 3,
            "inode": 1,
        }, None

    monkeypatch.setattr(client.protocol, "receive", receive)
    monkeypatch.setattr(client.secrets, "token_hex", lambda n: "ab" * n)
    return Backend


def test_client_authenticates_before_transferring_fd(monkeypatch, valid_client):
    def reject(*args):
        raise StorageGuardError()

    monkeypatch.setattr(client.protocol, "authenticate", reject)
    with pytest.raises(StorageGuardError):
        client.Client().perform(10, "server", UUID_TEXT)


@pytest.mark.parametrize(
    "variant",
    ["ro", "filesystem", "uuid", "mount-root", "path-drift", "after-drift", "library"],
)
def test_client_requires_original_root_before_and_after(
    monkeypatch, valid_client, variant
):
    class Backend(valid_client):
        def __init__(self):
            self.count = 0

        def inspect(self, fd):
            self.count += 1
            value = super().inspect(fd)
            if variant == "ro":
                value.writable = False
            if variant == "filesystem":
                value.fs_type = "tmpfs"
            if variant == "uuid":
                value.fs_uuid = UUID(int=1)
            if variant == "mount-root":
                value.mount_root = "/else"
            if variant == "path-drift" and fd == 20:
                value.inode = 40
            if variant == "after-drift" and self.count > 3:
                value.inode = 40
            return value

    monkeypatch.setattr(client, "LinuxBackend", Backend)
    with pytest.raises(StorageGuardError):
        client.Client().perform(
            10, "library" if variant == "library" else "server", UUID_TEXT
        )


@pytest.mark.parametrize("variant", ["challenge", "uuid", "role", "device", "inode"])
def test_client_rejects_response_mismatch(monkeypatch, valid_client, variant):
    monkeypatch.setattr(socket, "AF_UNIX", 1, raising=False)
    monkeypatch.setattr(socket, "SOCK_SEQPACKET", 5, raising=False)
    monkeypatch.setattr(socket, "SCM_RIGHTS", 1, raising=False)
    monkeypatch.setattr(client.socket, "socket", lambda *args: Connection())
    monkeypatch.setattr(client.secrets, "token_hex", lambda n: "ab" * n)

    def receive(*args, **kwargs):
        result = {
            "version": 1,
            "role": "server",
            "challenge": "ab" * 32,
            "uuid": UUID_TEXT,
            "device": 3,
            "inode": 1,
        }
        result[variant] = {
            "challenge": "cd" * 32,
            "uuid": str(UUID(int=1)),
            "role": "raw",
            "device": 4,
            "inode": 2,
        }[variant]
        return result, None

    monkeypatch.setattr(client.protocol, "receive", receive)

    class Backend:
        def inspect(self, fd):
            return SimpleNamespace(
                device=3,
                inode=1,
                mount_id=1,
                fs_uuid=UUID(UUID_TEXT),
                fs_type="ext4",
                mount_root="/",
                writable=True,
            )

        def open_root(self, path):
            return 20

        def close(self, fd):
            pass

    monkeypatch.setattr(client, "LinuxBackend", Backend)
    with pytest.raises(StorageGuardError):
        client.Client().perform(10, "server", UUID_TEXT)


@pytest.mark.skipif(
    sys.platform != "linux", reason="native authenticated Client with TMPFS UUID seam"
)
def test_native_client_real_credentials_and_domain_cleanup():
    from test_helper import _native_exchange

    result = _native_exchange(use_client=True)
    assert result == {
        "outcome": "success",
        "leak": 0,
        "clean": True,
        "consumer": "success",
    }
