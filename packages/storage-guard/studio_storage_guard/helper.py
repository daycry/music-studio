"""Helper secuencial; sólo raíces propias de configuración de despliegue."""

import os
import socket
import stat
from uuid import UUID

from . import protocol
from .custody import _DIR_FLAGS, CustodiedProbeDomain, _directory, _runtime
from .preflight import LinuxBackend, StorageGuardError, _identity


def filesystem_uuid(fd):
    import fcntl

    value = bytearray(17)
    fcntl.ioctl(fd, 0x80111500, value, True)
    if value[0] != 16:
        raise StorageGuardError()
    return UUID(bytes=bytes(value[1:]))


class Authority:
    def __init__(self, expected_uuid, data_root="/data"):
        self.uuid = UUID(expected_uuid)
        self.roots = {}
        self.seals = {}
        self.paths = {"server": data_root, "raw": data_root + "/tmp"}
        try:
            _runtime()
            for role, path in self.paths.items():
                fd = LinuxBackend().open_root(path)
                self.roots[role] = fd
                self.seals[role] = _directory(fd, 0, 0o1770)
                if filesystem_uuid(fd) != self.uuid:
                    raise StorageGuardError()
        except BaseException:
            self.close()
            raise

    def close(self):
        for fd in self.roots.values():
            os.close(fd)
        self.roots.clear()

    def _validate_own(self, role):
        fd = self.roots[role]
        if (
            _directory(fd, 0, 0o1770) != self.seals[role]
            or filesystem_uuid(fd) != self.uuid
        ):
            raise StorageGuardError()
        fresh = LinuxBackend().open_root(self.paths[role])
        try:
            if (
                _directory(fresh, 0, 0o1770) != self.seals[role]
                or filesystem_uuid(fresh) != self.uuid
            ):
                raise StorageGuardError()
        finally:
            os.close(fresh)

    def perform(self, root_fd, request):
        _runtime()
        protocol.decode(protocol.encode(request))
        self._validate_own(request["role"])
        own_fd = self.roots[request["role"]]
        info = os.fstat(root_fd)
        own = os.fstat(own_fd)
        seal = (info.st_dev, info.st_ino, info.st_mode)
        if (
            not stat.S_ISDIR(info.st_mode)
            or seal != (own.st_dev, own.st_ino, own.st_mode)
            or filesystem_uuid(root_fd) != self.uuid
            or filesystem_uuid(own_fd) != self.uuid
        ):
            raise StorageGuardError()
        with CustodiedProbeDomain.open(root_fd) as domain:
            domain.probe()
        current = os.fstat(root_fd)
        self._validate_own(request["role"])
        if (
            (current.st_dev, current.st_ino, current.st_mode) != seal
            or filesystem_uuid(root_fd) != self.uuid
            or filesystem_uuid(own_fd) != self.uuid
        ):
            raise StorageGuardError()
        return request | {
            "uuid": str(self.uuid),
            "device": info.st_dev,
            "inode": info.st_ino,
        }

    def handle(self, connection):
        connection = protocol.Deadline(connection)
        fd = None
        try:
            protocol.authenticate(connection, 10001)
            request, fd = protocol.receive(connection)
            result = self.perform(fd, request)
            connection.sendall(protocol.encode(result, response=True))
            connection.shutdown(socket.SHUT_WR)
        finally:
            if fd is not None:
                os.close(fd)


class Server:
    def __init__(self, authority, data_root="/data"):
        import fcntl

        self.authority = authority
        self.path = data_root + "/.storage-control/guard.sock"
        self.listener = None
        self.control = self.lock = None
        try:
            _runtime()
            self.control = os.open(
                ".storage-control", _DIR_FLAGS, dir_fd=authority.roots["server"]
            )
            _directory(self.control, 19000, 0o750)
            self.lock = os.open(
                ".lock",
                os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                0o600,
                dir_fd=self.control,
            )
            value = os.fstat(self.lock)
            if (
                not stat.S_ISREG(value.st_mode)
                or (
                    value.st_uid,
                    value.st_gid,
                    stat.S_IMODE(value.st_mode),
                    value.st_nlink,
                    value.st_size,
                )
                != (19000, 10001, 0o600, 1, 0)
                or os.listxattr(self.lock)
            ):
                raise StorageGuardError()
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if os.listdir(self.control) != [".lock"]:
                raise StorageGuardError()
            self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            self.listener.bind(f"/proc/self/fd/{self.control}/guard.sock")
            os.chmod("guard.sock", 0o660, dir_fd=self.control, follow_symlinks=False)
            self.socket_seal = _identity(
                os.stat("guard.sock", dir_fd=self.control, follow_symlinks=False)
            )
            self.listener.listen(1)
        except (OSError, ValueError, AttributeError, RuntimeError):
            if self.listener is not None:
                self.listener.close()
            for fd in (self.lock, self.control):
                if fd is not None:
                    os.close(fd)
            raise StorageGuardError() from None

    def close(self):
        listener, lock, control = self.listener, self.lock, self.control
        self.listener = self.lock = self.control = None
        if listener is None and lock is None and control is None:
            return
        error = None
        try:
            listener.close()
            if (
                _identity(os.stat("guard.sock", dir_fd=control, follow_symlinks=False))
                != self.socket_seal
            ):
                raise StorageGuardError()
            os.unlink("guard.sock", dir_fd=control)
        except BaseException as cause:  # noqa: BLE001 - release handles before re-raising
            error = cause
        finally:
            for fd in (lock, control):
                if fd is not None:
                    try:
                        os.close(fd)
                    except BaseException as cause:  # noqa: BLE001 - preserve first failure
                        if error is None:
                            error = cause
        if isinstance(error, (OSError, ValueError, AttributeError)):
            raise StorageGuardError() from None
        if error is not None:
            raise error

    def serve_once(self):
        connection, _ = self.listener.accept()
        with connection:
            self.authority.handle(connection)


def main():
    authority = server = None
    try:
        authority = Authority(os.environ["STUDIO_STORAGE_UUID"])
        server = Server(authority)
        while True:
            try:
                server.serve_once()
            except (StorageGuardError, OSError):
                continue
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, KeyError, AttributeError, RuntimeError):
        return 1
    finally:
        try:
            if server is not None:
                server.close()
        finally:
            if authority is not None:
                authority.close()


if __name__ == "__main__":
    raise SystemExit(main())
