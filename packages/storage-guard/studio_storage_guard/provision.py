"""Provisión exclusiva de dominios ADR-0071 por el controlador Linux root.

La configuración UUID pertenece al controlador confiable. La inspección del
kernel y un árbol virgen no acreditan por sí solos la custodia del VHDX:
el operador debe vincularlos al disco propio y al recibo attached antes de
invocar esta primitiva. No se lee, escribe ni avanza el recibo histórico.
Un error preserva residuos y bloquea el reintento; nunca repara una biblioteca.
"""

import argparse
import json
import os
import re
import stat
import sys
from pathlib import PurePosixPath
from uuid import UUID

from .custody import _DIR_FLAGS
from .preflight import LinuxBackend, StorageGuardError, _mount_record, _seal


def _controller():
    if (
        sys.platform != "linux"
        or os.getresuid() != (0, 0, 0)
        or os.getresgid() != (0, 0, 0)
        or any(group != 0 for group in os.getgroups())
    ):
        raise StorageGuardError()


def _mountinfo():
    with open("/proc/self/mountinfo", encoding="utf-8") as stream:
        return stream.read()


def _exact_mount(info, path):
    text = _mountinfo()
    root, point, kind, writable, _ = _mount_record(text, info.mount_id)
    if (root, point, kind, writable) != ("/", path, "ext4", True):
        raise StorageGuardError()
    # Reject nested/stacked mounts, including ones on the same device. st_dev
    # alone cannot identify a bind mount. Parse every record fail-closed.
    for line in text.splitlines():
        fields = line.split(" - ")[0].split()
        record = _mount_record(line, int(fields[0]))
        candidate = PurePosixPath(record[1])
        if int(fields[0]) != info.mount_id and candidate.is_relative_to(path):
            raise StorageGuardError()


def _directory(fd, uid, gid, modes, device):
    info = os.fstat(fd)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_dev != device
        or (info.st_uid, info.st_gid) != (uid, gid)
        or stat.S_IMODE(info.st_mode) not in modes
        or any(
            name in {"system.posix_acl_access", "system.posix_acl_default"}
            for name in os.listxattr(fd)
        )
    ):
        raise StorageGuardError()
    return info.st_dev, info.st_ino


def provision_domains(mountpoint, expected_uuid):
    """Create new domains, retaining root/path/creator FDs until revalidated.

    Only trusted root platform code may call this API. No descriptor or
    caller-provided proof/backend is accepted. Success means provisioned;
    live consumer/helper probes and lifecycle validation remain separate.
    """
    descriptors = []
    try:
        _controller()
        path = os.fspath(mountpoint)
        if (
            not isinstance(path, str)
            or path == "/"
            or not re.fullmatch(r"/[A-Za-z0-9._/-]+", path)
            or str(PurePosixPath(path)) != path
            or ".." in PurePosixPath(path).parts
        ):
            raise StorageGuardError()
        uuid = UUID(expected_uuid)
        if str(uuid) != expected_uuid or uuid.int == 0:
            raise StorageGuardError()
        backend = LinuxBackend()
        ancestors = []
        for ancestor in reversed(PurePosixPath(path).parents):
            ancestor_path = str(ancestor)
            fd = backend.open_root(ancestor_path)
            descriptors.append(fd)
            value = os.fstat(fd)
            if stat.S_IMODE(value.st_mode) & 0o022:
                raise StorageGuardError()
            policy = stat.S_IMODE(value.st_mode)
            identity = _directory(fd, 0, 0, {policy}, value.st_dev)
            ancestors.append((ancestor_path, fd, identity, policy))
        root = backend.open_root(path)
        descriptors.append(root)
        info = backend.inspect(root)
        if (
            info.fs_uuid != uuid
            or info.fs_type != "ext4"
            or info.mount_root != "/"
            or info.writable is not True
        ):
            raise StorageGuardError()
        mount_seal = _seal(info)
        device = info.device
        root_identity = _directory(root, 0, 0, {0o700, 0o755}, device)
        if root_identity != (info.device, info.inode):
            raise StorageGuardError()
        _exact_mount(info, path)
        initial = set(os.listdir(root))
        if initial not in (set(), {"lost+found"}):
            raise StorageGuardError()
        records = []
        if initial:
            lost = os.open("lost+found", _DIR_FLAGS, dir_fd=root)
            descriptors.append(lost)
            seal = _directory(lost, 0, 0, {0o700}, device)
            if os.listdir(lost):
                raise StorageGuardError()
            records.append([root, "lost+found", lost, seal, 0, 0, 0o700, set()])

        root_policy = [0, 0, stat.S_IMODE(os.fstat(root).st_mode)]
        root_members = set(initial)

        def validate():
            _controller()
            for ancestor_path, retained, identity, policy in ancestors:
                if _directory(retained, 0, 0, {policy}, identity[0]) != identity:
                    raise StorageGuardError()
                fresh_ancestor = backend.open_root(ancestor_path)
                try:
                    if (
                        _directory(fresh_ancestor, 0, 0, {policy}, identity[0])
                        != identity
                    ):
                        raise StorageGuardError()
                finally:
                    os.close(fresh_ancestor)
            if (
                _seal(backend.inspect(root)) != mount_seal
                or _directory(root, *root_policy[:2], {root_policy[2]}, device)
                != root_identity
                or set(os.listdir(root)) != root_members
            ):
                raise StorageGuardError()
            _exact_mount(info, path)
            fresh = backend.open_root(path)
            try:
                if (
                    _seal(backend.inspect(fresh)) != mount_seal
                    or _directory(fresh, *root_policy[:2], {root_policy[2]}, device)
                    != root_identity
                ):
                    raise StorageGuardError()
            finally:
                os.close(fresh)
            for parent, name, fd, seal, uid, gid, mode, children in records:
                if (
                    _directory(fd, uid, gid, {mode}, device) != seal
                    or set(os.listdir(fd)) != children
                ):
                    raise StorageGuardError()
                current = os.open(name, _DIR_FLAGS, dir_fd=parent)
                try:
                    if _directory(current, uid, gid, {mode}, device) != seal:
                        raise StorageGuardError()
                finally:
                    os.close(current)

        validate()
        # Before creating anything traversable, close the parent to consumers.
        os.fchmod(root, 0o700)
        root_policy[2] = 0o700
        os.fsync(root)
        validate()

        def create(parent, name):
            validate()
            # mkdir has exclusive creation semantics; EEXIST is never adopted.
            os.mkdir(name, 0o700, dir_fd=parent)
            if parent == root:
                root_members.add(name)
            else:
                next(record for record in records if record[2] == parent)[7].add(name)
            fd = os.open(name, _DIR_FLAGS, dir_fd=parent)
            descriptors.append(fd)
            # umask may remove permissions; it cannot grant write to consumers.
            value = os.fstat(fd)
            if stat.S_IMODE(value.st_mode) & 0o077:
                raise StorageGuardError()
            os.fchmod(fd, 0o700)
            seal = _directory(fd, 0, 0, {0o700}, device)
            if os.listdir(fd):
                raise StorageGuardError()
            record = [parent, name, fd, seal, 0, 0, 0o700, set()]
            records.append(record)
            os.fsync(fd)
            os.fsync(parent)
            validate()
            return record

        temporary = create(root, "tmp")
        data_probes = create(root, ".storage-probes")
        raw_probes = create(temporary[2], ".storage-probes")
        control = create(root, ".storage-control")
        for record, uid, mode in (
            (data_probes, 19000, 0o700),
            (raw_probes, 19000, 0o700),
            (control, 19000, 0o750),
            (temporary, 0, 0o1770),
        ):
            validate()
            os.fchown(record[2], uid, 10001)
            record[4:6] = [uid, 10001]
            os.fchmod(record[2], mode)
            record[6] = mode
            os.fsync(record[2])
            os.fsync(record[0])
            validate()
        validate()
        os.fchown(root, 0, 10001)
        root_policy[1] = 10001
        os.fsync(root)
        validate()
        # Commit exposure last; nothing below root remains consumer-mutable
        # until all protected domains and durable parent entries are verified.
        os.fchmod(root, 0o1770)
        root_policy[2] = 0o1770
        os.fsync(root)
        validate()
        return {
            "status": "provisioned",
            "uuid": str(uuid),
            "device": info.device,
            "inode": info.inode,
            "mount_id": info.mount_id,
        }
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        ImportError,
        RuntimeError,
    ):
        # No recursive deletion, ownership repair, or fresh receipt promotion.
        raise StorageGuardError() from None
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Provisionar dominios ext4 nuevos ADR-0071"
    )
    parser.add_argument("--mountpoint", required=True)
    parser.add_argument("--uuid", required=True)
    args = parser.parse_args(argv)
    try:
        result = provision_domains(args.mountpoint, args.uuid)
    except StorageGuardError as error:
        print(error.code, file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
