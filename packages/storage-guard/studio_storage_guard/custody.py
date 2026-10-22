"""Primitivas del helper exclusivo; aún no conectadas al gate consumidor."""

import errno
import os
import secrets
import stat

from .preflight import StorageGuardError, _file_identity, _identity, _rename_noreplace


def _runtime():
    if os.getresuid() != (19000, 19000, 19000) or os.getresgid() != (10001,) * 3:
        raise StorageGuardError()
    with open("/proc/self/status", encoding="ascii") as stream:
        fields = dict(line.split(":", 1) for line in stream if ":" in line)
    if any(
        int(fields[key].strip(), 16) for key in ("CapEff", "CapPrm", "CapInh", "CapAmb")
    ):
        raise StorageGuardError()
    if int(fields["NoNewPrivs"].strip()) != 1:
        raise StorageGuardError()


def _directory(fd, uid, mode):
    value = os.fstat(fd)
    if not stat.S_ISDIR(value.st_mode) or (
        value.st_uid,
        value.st_gid,
        stat.S_IMODE(value.st_mode),
    ) != (uid, 10001, mode):
        raise StorageGuardError()
    # An unsupported or failed query is not evidence that ACLs are absent.
    if any(
        name in {"system.posix_acl_access", "system.posix_acl_default"}
        for name in os.listxattr(fd)
    ):
        raise StorageGuardError()
    return _identity(value)


_DIR_FLAGS = (
    getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | os.O_RDONLY
)


class CustodiedProbeDomain:
    def __init__(self, root_fd, private_fd):
        # No externally supplied proof/token: every construction checks authority.
        _runtime()
        self._root = None
        self._private = None
        self._lock = None
        self._closed = False
        try:
            self._root = os.dup(root_fd)
            self._private = os.dup(private_fd)
            self._root_seal = _directory(self._root, 0, 0o1770)
            self._private_seal = _directory(self._private, 19000, 0o700)
            self._validate()
            import fcntl

            self._lock = os.open(
                ".lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                0o600,
                dir_fd=self._private,
            )
            info = os.fstat(self._lock)
            if (
                not stat.S_ISREG(info.st_mode)
                or (
                    info.st_uid,
                    info.st_gid,
                    stat.S_IMODE(info.st_mode),
                    info.st_size,
                    info.st_nlink,
                )
                != (19000, 10001, 0o600, 0, 1)
                or os.listxattr(self._lock)
            ):
                raise StorageGuardError()
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._validate()
            if set(os.listdir(self._private)) != {".lock"}:
                raise StorageGuardError()
        except (OSError, ValueError, KeyError, AttributeError, RuntimeError):
            self.close()
            raise StorageGuardError() from None
        except BaseException:
            self.close()
            raise

    @classmethod
    def open(cls, root_fd):
        private = None
        try:
            _runtime()
            _directory(root_fd, 0, 0o1770)
            private = os.open(".storage-probes", _DIR_FLAGS, dir_fd=root_fd)
            return cls(root_fd, private)
        except (OSError, ValueError, KeyError, AttributeError, RuntimeError):
            raise StorageGuardError() from None
        finally:
            if private is not None:
                os.close(private)

    def _validate(self):
        _runtime()
        if (
            self._closed
            or _directory(self._root, 0, 0o1770) != self._root_seal
            or _directory(self._private, 19000, 0o700) != self._private_seal
        ):
            raise StorageGuardError()
        current = os.open(".storage-probes", _DIR_FLAGS, dir_fd=self._root)
        try:
            if (
                _directory(current, 19000, 0o700) != self._private_seal
                or os.fstat(current).st_dev != os.fstat(self._root).st_dev
            ):
                raise StorageGuardError()
        finally:
            os.close(current)

    def close(self):
        if not self._closed:
            self._closed = True
            for fd in (self._lock, self._private, self._root):
                if fd is not None:
                    os.close(fd)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def probe(self):
        # Creator descriptors remain live through validation and cleanup.
        self._validate()
        if set(os.listdir(self._private)) != {".lock"}:
            raise StorageGuardError()
        run_name = "probe-" + secrets.token_hex(16)
        descriptors = []
        records = {}
        try:
            os.mkdir(run_name, 0o700, dir_fd=self._private)
            run = os.open(run_name, _DIR_FLAGS, dir_fd=self._private)
            descriptors.append(run)
            run_seal = _directory(run, 19000, 0o700)
            if os.listdir(run):
                raise StorageGuardError()

            def new_directory(name):
                self._validate()
                os.mkdir(name, 0o700, dir_fd=run)
                creator = os.open(name, _DIR_FLAGS, dir_fd=run)
                descriptors.append(creator)
                seal = _directory(creator, 19000, 0o700)
                if os.listdir(creator):
                    raise StorageGuardError()
                records[name] = {
                    "fd": creator,
                    "seal": seal,
                    "kind": "directory",
                    "children": {},
                }

            def new_file(parent, name, expected):
                self._validate()
                creator = os.open(
                    name,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=parent,
                )
                descriptors.append(creator)
                if os.write(creator, expected) != len(expected):
                    raise StorageGuardError()
                os.fsync(creator)
                created = os.fstat(creator)
                if (
                    not stat.S_ISREG(created.st_mode)
                    or created.st_nlink != 1
                    or created.st_size != len(expected)
                    or os.pread(creator, len(expected) + 1, 0) != expected
                ):
                    raise StorageGuardError()
                return {
                    "fd": creator,
                    "seal": _file_identity(created),
                    "kind": "file",
                    "content": expected,
                }

            for kind in ("absent", "empty", "nonempty", "file", "link"):
                source, target = "source-" + kind, "target-" + kind
                new_directory(source)
                if kind in ("empty", "nonempty"):
                    new_directory(target)
                    if kind == "nonempty":
                        records[target]["children"]["marker"] = new_file(
                            records[target]["fd"], "marker", b"own-marker"
                        )
                elif kind == "file":
                    records[target] = new_file(run, target, b"")
                elif kind == "link":
                    self._validate()
                    os.symlink("own-unresolved", target, dir_fd=run)
                    records[target] = {
                        "kind": "link",
                        "seal": _file_identity(
                            os.stat(target, dir_fd=run, follow_symlinks=False)
                        ),
                        "content": "own-unresolved",
                    }
                self._validate()
                try:
                    _rename_noreplace(run, source, target)
                except OSError as error:
                    if kind == "absent" or error.errno != errno.EEXIST:
                        raise StorageGuardError() from None
                else:
                    if kind != "absent":
                        raise StorageGuardError()
                    records[target] = records.pop(source)

            def verify_file(parent, name, record):
                actual = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if (
                    _file_identity(actual) != record["seal"]
                    or _file_identity(os.fstat(record["fd"])) != record["seal"]
                    or os.pread(record["fd"], len(record["content"]) + 1, 0)
                    != record["content"]
                ):
                    raise StorageGuardError()

            # All membership/content checks precede the first deletion.
            self._validate()
            if set(os.listdir(run)) != set(records):
                raise StorageGuardError()
            for name, record in records.items():
                kind = record["kind"]
                if kind == "file":
                    verify_file(run, name, record)
                elif kind == "link":
                    if (
                        _file_identity(os.stat(name, dir_fd=run, follow_symlinks=False))
                        != record["seal"]
                        or os.readlink(name, dir_fd=run) != record["content"]
                    ):
                        raise StorageGuardError()
                else:
                    if (
                        _identity(os.stat(name, dir_fd=run, follow_symlinks=False))
                        != record["seal"]
                        or _directory(record["fd"], 19000, 0o700) != record["seal"]
                        or set(os.listdir(record["fd"])) != set(record["children"])
                    ):
                        raise StorageGuardError()
                    for entry, nested in record["children"].items():
                        verify_file(record["fd"], entry, nested)

            # Authority is the domain, never a fictional stat/delete CAS.
            for name, record in records.items():
                self._validate()
                if record["kind"] == "directory":
                    for entry in record["children"]:
                        self._validate()
                        os.unlink(entry, dir_fd=record["fd"])
                    os.rmdir(name, dir_fd=run)
                else:
                    os.unlink(name, dir_fd=run)
            self._validate()
            if (
                os.listdir(run)
                or _identity(
                    os.stat(run_name, dir_fd=self._private, follow_symlinks=False)
                )
                != run_seal
            ):
                raise StorageGuardError()
            os.rmdir(run_name, dir_fd=self._private)
            self._validate()
        except (OSError, ValueError, KeyError, AttributeError, RuntimeError):
            # Unexpected contents/crash residues are retained, never recursively reclaimed.
            raise StorageGuardError() from None
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)


def anonymous_rw_probe(root_fd):
    fd = None
    try:
        fd = os.open(
            ".",
            os.O_TMPFILE | os.O_EXCL | os.O_RDWR | os.O_CLOEXEC,
            0o600,
            dir_fd=root_fd,
        )
        pattern = b"studio-storage-rw\x00" + secrets.token_bytes(32)
        if os.write(fd, pattern) != len(pattern):
            raise StorageGuardError()
        os.fsync(fd)
        if os.pread(fd, len(pattern) + 1, 0) != pattern or os.fstat(fd).st_nlink != 0:
            raise StorageGuardError()
    except (OSError, ValueError, AttributeError, RuntimeError):
        raise StorageGuardError() from None
    finally:
        if fd is not None:
            os.close(fd)
