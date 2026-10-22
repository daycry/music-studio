"""Cliente fresco del helper; no concede una lease ni cachea resultados."""

import array
import os
import secrets
import socket
import stat
from uuid import UUID

from . import protocol
from .custody import _DIR_FLAGS, _directory
from .preflight import LinuxBackend, RootLease, StorageGuardError, _seal


def _consumer_runtime():
    try:
        if os.getresuid() != (10001,) * 3 or os.getresgid() != (10001,) * 3:
            raise StorageGuardError()
        with open("/proc/self/status", encoding="ascii") as stream:
            fields = dict(line.split(":", 1) for line in stream if ":" in line)
        if (
            any(
                int(fields[key].strip(), 16)
                for key in ("CapEff", "CapPrm", "CapInh", "CapAmb")
            )
            or int(fields["NoNewPrivs"].strip()) != 1
        ):
            raise StorageGuardError()
    except (OSError, ValueError, KeyError, AttributeError):
        raise StorageGuardError() from None


def _socket_address(data_root):
    root = control = None
    try:
        root = LinuxBackend().open_root(data_root)
        _directory(root, 0, 0o1770)
        control = os.open(".storage-control", _DIR_FLAGS, dir_fd=root)
        _directory(control, 19000, 0o750)
        value = os.stat("guard.sock", dir_fd=control, follow_symlinks=False)
        path = data_root + "/.storage-control/guard.sock"
        if (
            not stat.S_ISSOCK(value.st_mode)
            or (value.st_uid, value.st_gid, stat.S_IMODE(value.st_mode))
            != (19000, 10001, 0o660)
            or any(
                name in {"system.posix_acl_access", "system.posix_acl_default"}
                for name in os.listxattr(path, follow_symlinks=False)
            )
        ):
            raise StorageGuardError()
        return path
    except (OSError, ValueError, AttributeError):
        raise StorageGuardError() from None
    finally:
        for fd in (control, root):
            if fd is not None:
                os.close(fd)


class Client:
    def __init__(self, data_root="/data"):
        self.data_root = data_root

    def perform(self, root_fd, role, expected_uuid):
        try:
            _consumer_runtime()
            request = {"version": 1, "role": role, "challenge": secrets.token_hex(32)}
            protocol.decode(protocol.encode(request))
            backend = LinuxBackend()
            info = backend.inspect(root_fd)
            if (
                info.fs_uuid != UUID(expected_uuid)
                or info.fs_type != "ext4"
                or info.mount_root != ("/tmp" if role == "raw" else "/")
                or not info.writable
            ):
                raise StorageGuardError()
            lease = RootLease(
                root_fd,
                backend,
                _seal(info),
                self.data_root + ("/tmp" if role == "raw" else ""),
            )
            lease.revalidate()
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as connection:
                connection = protocol.Deadline(connection)
                connection.connect(_socket_address(self.data_root))
                protocol.authenticate(connection, 19000)
                connection.sendmsg(
                    [protocol.encode(request)],
                    [
                        (
                            socket.SOL_SOCKET,
                            socket.SCM_RIGHTS,
                            array.array("i", [root_fd]),
                        )
                    ],
                )
                connection.shutdown(socket.SHUT_WR)
                result, _ = protocol.receive(connection, response=True)
                if result != request | {
                    "uuid": str(UUID(expected_uuid)),
                    "device": info.device,
                    "inode": info.inode,
                }:
                    raise StorageGuardError()
            lease.revalidate()
            _consumer_runtime()
            return result
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError):
            raise StorageGuardError() from None
