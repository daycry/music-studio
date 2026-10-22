"""Storage startup leases; the descriptor remains owned until close."""

import ctypes
import os
import re
import stat
from pathlib import PurePosixPath
from types import SimpleNamespace
from uuid import UUID


def _mount_record(text, mount_id):
    records = []
    try:
        for line in text.splitlines():
            left, right = line.split(" - ")
            fields, extra = left.split(), right.split()
            if int(fields[0]) != mount_id:
                continue
            options = set(fields[5].split(","))
            if len(extra) != 3 or len(options & {"ro", "rw"}) != 1:
                raise ValueError()

            def decode(value):
                return re.sub(
                    r"\\(040|011|012|134)", lambda match: chr(int(match[1], 8)), value
                )

            records.append(
                (
                    decode(fields[3]),
                    decode(fields[4]),
                    extra[0],
                    "rw" in options and "ro" not in extra[2].split(","),
                    fields[2],
                )
            )
        if len(records) != 1:
            raise ValueError()
        return records[0]
    except (ValueError, IndexError):
        raise StorageGuardError() from None


class LinuxBackend:
    def open_root(self, root):
        path = PurePosixPath(os.fspath(root))
        if not path.is_absolute() or ".." in path.parts:
            raise StorageGuardError()
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        fd = os.open("/", flags)
        try:
            for part in path.parts[1:]:
                child = os.open(part, flags, dir_fd=fd)
                os.close(fd)
                fd = child
            return fd
        except BaseException:
            os.close(fd)
            raise

    def close(self, fd):
        os.close(fd)

    def inspect(self, fd):
        import fcntl

        identity = os.fstat(fd)
        if not stat.S_ISDIR(identity.st_mode):
            raise StorageGuardError()
        with open(f"/proc/self/fdinfo/{fd}", encoding="ascii") as stream:
            ids = re.findall(r"^mnt_id:\s*(\d+)$", stream.read(), re.MULTILINE)
        if len(ids) != 1:
            raise StorageGuardError()
        mount_id = int(ids[0])
        with open("/proc/self/mountinfo", encoding="utf-8") as stream:
            root, point, fs_type, writable, device = _mount_record(
                stream.read(), mount_id
            )
        if (
            device != f"{os.major(identity.st_dev)}:{os.minor(identity.st_dev)}"
            or os.readlink(f"/proc/self/fd/{fd}") != point
        ):
            raise StorageGuardError()
        fresh = self.open_root(point)
        try:
            if _identity(os.fstat(fresh)) != _identity(identity):
                raise StorageGuardError()
            with open(f"/proc/self/fdinfo/{fresh}", encoding="ascii") as stream:
                fresh_ids = re.findall(
                    r"^mnt_id:\s*(\d+)$", stream.read(), re.MULTILINE
                )
            if fresh_ids != ids:
                raise StorageGuardError()
        finally:
            os.close(fresh)
        data = bytearray(17)
        fcntl.ioctl(fd, 0x80111500, data, True)  # FS_IOC_GETFSUUID, struct fsuuid2.
        if data[0] != 16 or len(data) != 17:
            raise StorageGuardError()
        return SimpleNamespace(
            device=identity.st_dev,
            inode=identity.st_ino,
            mount_id=mount_id,
            fs_uuid=UUID(bytes=bytes(data[1:])),
            fs_type=fs_type,
            mount_root=root,
            writable=writable,
        )

    def probe(self, fd, *, lease=None, role=None, expected_uuid=None, data_root=None):
        if (
            lease is None
            or lease.fd != fd
            or role not in {"server", "raw"}
            or expected_uuid is None
            or data_root is None
        ):
            raise StorageGuardError()
        # Lazy imports keep inspection usable by Client without probe recursion.
        from .client import Client
        from .custody import anonymous_rw_probe

        lease.revalidate()
        Client(data_root).perform(fd, role, expected_uuid)
        lease.revalidate()
        anonymous_rw_probe(fd)
        lease.revalidate()


def _identity(value):
    return value.st_dev, value.st_ino, value.st_mode


def _file_identity(value):
    return _identity(value) + (
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _witness_identity(value):
    return _identity(value) if stat.S_ISDIR(value.st_mode) else _file_identity(value)


def _rename_noreplace(fd, source, target):
    library = ctypes.CDLL(None, use_errno=True)
    rename = library.renameat2
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(fd, os.fsencode(source), fd, os.fsencode(target), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, "STORAGE_ROOT_INVALID")


class StorageGuardError(RuntimeError):
    code = "STORAGE_ROOT_INVALID"

    def __init__(self):
        super().__init__(self.code)


class RootLease:
    def __init__(self, fd, backend, seal, root):
        self.fd = fd
        self._backend = backend
        self._closed = False
        self._seal = seal
        self._root = os.fspath(root)

    def revalidate(self):
        try:
            if self._closed or _seal(self._backend.inspect(self.fd)) != self._seal:
                raise StorageGuardError()
            fresh = self._backend.open_root(self._root)
            try:
                if _seal(self._backend.inspect(fresh)) != self._seal:
                    raise StorageGuardError()
            finally:
                self._backend.close(fresh)
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
            raise StorageGuardError() from None

    def __enter__(self):
        try:
            self.revalidate()
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if not self._closed:
            self._closed = True
            self._backend.close(self.fd)


def _seal(info):
    return tuple(vars(info).items())


def verify_engine_roots(library_root, raw_root, expected_uuid, *, _backends=None):
    backends = _backends or (None, None)
    library = verify_root(library_root, expected_uuid, "library", _backend=backends[0])
    raw = None
    try:
        raw = verify_root(
            raw_root,
            expected_uuid,
            "raw",
            _backend=backends[1],
            _data_root=library_root,
        )
        if dict(library._seal)["device"] != dict(raw._seal)["device"]:
            raise StorageGuardError()
        library.revalidate()
        raw.revalidate()
        return EngineLease(library, raw)
    except Exception:
        try:
            if raw is not None:
                raw.close()
        finally:
            library.close()
        raise


class EngineLease:
    def __init__(self, library, raw):
        self.library, self.raw = library, raw

    def revalidate(self):
        self.library.revalidate()
        self.raw.revalidate()

    def close(self):
        try:
            self.raw.close()
        finally:
            self.library.close()

    def __enter__(self):
        try:
            self.revalidate()
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, *args):
        self.close()


def verify_root(root, expected_uuid, role, *, _backend=None, _data_root=None):
    backend = _backend or LinuxBackend()
    fd = None
    try:
        fd = backend.open_root(root)
        info = backend.inspect(fd)
        seal = _seal(info)
        mount_root, writable = {
            "server": ("/", True),
            "library": ("/", False),
            "raw": ("/tmp", True),
        }[role]
        if (
            info.fs_uuid != UUID(expected_uuid)
            or info.fs_type != "ext4"
            or info.mount_root != mount_root
            or info.writable != writable
        ):
            raise StorageGuardError()
        lease = RootLease(fd, backend, seal, root)
        if writable:
            if isinstance(backend, LinuxBackend):
                data_root = os.fspath(_data_root if _data_root is not None else root)
                if role == "raw" and _data_root is None:
                    data_root = str(PurePosixPath(os.fspath(root)).parent)
                backend.probe(
                    fd,
                    lease=lease,
                    role=role,
                    expected_uuid=expected_uuid,
                    data_root=data_root,
                )
            else:
                backend.probe(fd)
        if _seal(backend.inspect(fd)) != seal:
            raise StorageGuardError()
        lease.revalidate()
        return lease
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        ImportError,
        RuntimeError,
    ):
        if fd is not None:
            backend.close(fd)
        raise StorageGuardError() from None
