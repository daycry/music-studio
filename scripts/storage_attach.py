"""Fail-closed attach/mount operator for the project's published VHDX.

The operator never chooses a block device by position. It attaches the exact
VHDX, compares ``lsblk`` before/after, selects the single new ext4 device with
the receipt UUID, mounts it as root, validates ``findmnt`` and ``blkid``, then
advances the receipt to ``attached``. Any failure attempts a private unmount
and WSL detach; it never stops WSL, Docker or Ollama globally.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from studio_storage_guard.receipt import ReceiptError, StorageReceipt

from scripts.storage_operator import PublishedDiskBinding
from scripts.storage_windows import CustodyError

_DEVICE = re.compile(r"/dev/[A-Za-z0-9._-]+\Z")
_MOUNTPOINT = re.compile(r"/[A-Za-z0-9._/-]*\Z")
_PLACEHOLDER = "<device-from-lsblk>"


class AttachError(RuntimeError):
    """The exact VHDX/device/mount contract could not be accredited."""


@dataclass(frozen=True)
class BlockRecord:
    fstype: str
    uuid: str
    mountpoint: str


@dataclass(frozen=True)
class AttachPlan:
    project_root: Path
    receipt_path: Path
    final_path: Path
    filesystem_uuid: str
    distro: str
    mountpoint: str
    status: str
    commands: tuple[tuple[str, ...], ...]


def _canonical_mountpoint(value: str) -> str:
    if (
        not isinstance(value, str)
        or not _MOUNTPOINT.fullmatch(value)
        or ".." in Path(value).parts
        or "//" in value
    ):
        raise ValueError("mountpoint no can?nico")
    return value.rstrip("/") or "/"


def _read_receipt(root: Path, receipt_path: Path) -> StorageReceipt:
    root = root.resolve(strict=True)
    resolved = receipt_path.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError("recibo fuera del proyecto")
    current = receipt_path
    while True:
        metadata = current.lstat()
        if current.is_symlink() or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise ValueError("alias/reparse en ruta del recibo")
        if current == root:
            break
        if current.parent == current:
            raise ValueError("ra?z del recibo no coincide")
        current = current.parent
    if not receipt_path.is_file():
        raise ValueError("recibo ausente o no regular")
    receipt = StorageReceipt.from_bytes(receipt_path.read_bytes())
    if receipt.phase != "published":
        raise ReceiptError("recibo debe estar en published")
    final = root / "data" / "_storage" / "studio-data.vhdx"
    if receipt.disk_path != final.absolute().as_posix():
        raise ReceiptError("ruta publicada no coincide")
    if final.is_symlink() or not final.is_file():
        raise ValueError("VHDX publicado ausente o no regular")
    return receipt


def _uuid_from_receipt(receipt: StorageReceipt) -> str:
    for item in receipt.history:
        if item["phase"] == "raw_verified":
            value = item["evidence"].get("uuid")
            if isinstance(value, str):
                return value
    raise ReceiptError("UUID ext4 ausente en recibo")


def plan(
    project_root: str | Path,
    receipt_path: str | Path,
    *,
    distro: str = "Ubuntu",
    mountpoint: str = "/mnt/studio-data",
    admin: bool = False,
) -> AttachPlan:
    root = Path(project_root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("ra?z de proyecto inv?lida")
    if not isinstance(distro, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", distro):
        raise ValueError("distro no can?nica")
    mountpoint = _canonical_mountpoint(mountpoint)
    receipt_file = Path(receipt_path).absolute()
    receipt = _read_receipt(root, receipt_file)
    final = root / "data" / "_storage" / "studio-data.vhdx"
    uuid = _uuid_from_receipt(receipt)
    if admin is not True:
        return AttachPlan(
            root, receipt_file, final, uuid, distro, mountpoint, "NEEDS_ADMIN", ()
        )
    base = ("wsl.exe", "-d", distro, "-u", "root", "--")
    commands = (
        ("wsl.exe", "--mount", str(final), "--vhd", "--bare"),
        base
        + ("lsblk", "--json", "--paths", "--output", "NAME,FSTYPE,UUID,MOUNTPOINT"),
        base + ("mkdir", "-p", mountpoint),
        base + ("mount", "-t", "ext4", _PLACEHOLDER, mountpoint),
        base
        + (
            "findmnt",
            "-n",
            "-o",
            "SOURCE,FSTYPE,OPTIONS,FSROOT",
            "--target",
            mountpoint,
        ),
        base + ("blkid", "-s", "UUID", "-o", "value", _PLACEHOLDER),
    )
    return AttachPlan(
        root, receipt_file, final, uuid, distro, mountpoint, "READY_TO_ATTACH", commands
    )


def parse_lsblk(text: str) -> dict[str, BlockRecord]:
    """Read lsblk's JSON tree, retaining every device for the before/after diff.

    A null field means lsblk observed no value; an absent field means the
    requested protocol was not delivered and must fail closed.
    """

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AttachError("clave lsblk duplicada")
            result[key] = value
        return result

    try:
        payload = json.loads(text, object_pairs_hook=unique_object)
    except (TypeError, ValueError, RecursionError) as exc:
        raise AttachError("JSON lsblk no canónico") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"blockdevices"}
        or not isinstance(payload["blockdevices"], list)
    ):
        raise AttachError("árbol lsblk no canónico")
    records: dict[str, BlockRecord] = {}
    pending = list(payload["blockdevices"])
    while pending:
        item = pending.pop()
        required = {"name", "fstype", "uuid", "mountpoint"}
        if (
            not isinstance(item, dict)
            or not required <= set(item)
            or set(item) - required - {"children"}
        ):
            raise AttachError("lsblk no can?nico")
        device = item["name"]
        if not isinstance(device, str) or not _DEVICE.fullmatch(device):
            raise AttachError("dispositivo lsblk no canónico")
        values = [item[key] for key in ("fstype", "uuid", "mountpoint")]
        if any(value is not None and not isinstance(value, str) for value in values):
            raise AttachError("campos lsblk no canónicos")
        fstype, uuid, mountpoint = [value or "" for value in values]
        if any(
            value and not re.fullmatch(r"[A-Za-z0-9._:+-]+", value)
            for value in (fstype, uuid)
        ):
            raise AttachError("campos lsblk no canónicos")
        if mountpoint == "[SWAP]" and fstype == "swap":
            pass
        elif mountpoint:
            try:
                _canonical_mountpoint(mountpoint)
            except ValueError as exc:
                raise AttachError("mountpoint de lsblk no canónico") from exc
        if "children" in item:
            if not isinstance(item["children"], list):
                raise AttachError("hijos lsblk no canónicos")
            pending.extend(item["children"])
        if device in records:
            raise AttachError("dispositivo lsblk duplicado")
        records[device] = BlockRecord(fstype, uuid, mountpoint)
    return records


def _select_device(
    before: dict[str, BlockRecord], after: dict[str, BlockRecord], expected_uuid: str
) -> str:
    candidates = [
        device
        for device, record in after.items()
        if device not in before
        and record.fstype == "ext4"
        and record.uuid == expected_uuid
        and not record.mountpoint
    ]
    if len(candidates) != 1:
        raise AttachError("dispositivo ext4 nuevo ambiguo o ausente")
    return candidates[0]


def _run(runner, argv: tuple[str, ...], *, check: bool = True):
    return runner(argv, check=check, capture_output=True, text=True)


def _findmnt(stdout: str, device: str, mountpoint: str) -> None:
    fields = stdout.strip().split()
    if len(fields) != 4 or fields[0] != device or fields[1] != "ext4":
        raise AttachError("findmnt no acredita dispositivo/ext4")
    options = set(fields[2].split(","))
    if "rw" not in options or "ro" in options or fields[3] != "/":
        raise AttachError("montaje no acredita rw y ra?z ext4")
    if not mountpoint.startswith("/"):
        raise AttachError("mountpoint no can?nico")


def execute(
    plan: AttachPlan, *, runner: Callable = subprocess.run, binding_factory=None
) -> StorageReceipt:
    if plan.status != "READY_TO_ATTACH":
        raise AttachError("plan no listo para attach")
    if not _is_admin():
        raise AttachError("NEEDS_ADMIN")
    attached = mounted = False
    device = None
    binding = None
    identity_lost = False
    receipt_write_attempted = False
    primary = None
    error = None
    cleanup_errors = []

    def validate():
        nonlocal identity_lost
        try:
            binding.revalidate()
        except BaseException:
            identity_lost = True
            raise

    def checked(argv):
        nonlocal attached, mounted
        validate()
        result = _run(runner, argv)
        # Record successful effects before the post-command identity check.
        if argv == plan.commands[0]:
            attached = True
        elif "mount" in argv:
            mounted = True
        validate()
        return result

    try:
        snapshot = plan.receipt_path.read_bytes()
        receipt = _read_receipt(plan.project_root, plan.receipt_path)
        if (
            StorageReceipt.from_bytes(snapshot).to_bytes() != receipt.to_bytes()
            or plan.receipt_path.read_bytes() != snapshot
            or receipt.disk_path != plan.final_path.absolute().as_posix()
            or _uuid_from_receipt(receipt) != plan.filesystem_uuid
        ):
            raise ReceiptError("recibo no coincide con plan/snapshot")
        factory = (
            PublishedDiskBinding.open if binding_factory is None else binding_factory
        )
        binding = factory(plan.project_root, receipt)
        before = parse_lsblk(checked(plan.commands[1]).stdout or "")
        checked(plan.commands[0])
        after = parse_lsblk(checked(plan.commands[1]).stdout or "")
        device = _select_device(before, after, plan.filesystem_uuid)
        checked(plan.commands[2])
        mount = tuple(device if v == _PLACEHOLDER else v for v in plan.commands[3])
        checked(mount)
        _findmnt(checked(plan.commands[4]).stdout or "", device, plan.mountpoint)
        uuid_command = tuple(
            device if v == _PLACEHOLDER else v for v in plan.commands[5]
        )
        if checked(uuid_command).stdout.strip() != plan.filesystem_uuid:
            raise AttachError("UUID del dispositivo no coincide")
        validate()
        if plan.receipt_path.read_bytes() != snapshot:
            raise ReceiptError("recibo cambió durante attach")
        advanced = receipt.advance(
            "attached", {"device": device, "mountpoint": plan.mountpoint}
        )
        validate()
        if plan.receipt_path.read_bytes() != snapshot:
            raise ReceiptError("recibo cambió antes de commit")
        receipt_write_attempted = True
        plan.receipt_path.write_bytes(advanced.to_bytes())
        validate()
        return advanced
    except BaseException as exc:
        primary = exc
        if binding is not None and attached:
            try:
                if identity_lost:
                    raise CustodyError("identidad perdida; rollback por ruta prohibido")
                validate()
                if mounted and device:
                    mount_probe = tuple(
                        "--mountpoint" if value == "--target" else value
                        for value in plan.commands[4]
                    )
                    fields = (checked(mount_probe).stdout or "").strip().split()
                    uuid_command = tuple(
                        device if v == _PLACEHOLDER else v for v in plan.commands[5]
                    )
                    if (
                        len(fields) != 4
                        or fields[0] != device
                        or fields[1] != "ext4"
                        or fields[3] != "/"
                        or checked(uuid_command).stdout.strip() != plan.filesystem_uuid
                    ):
                        raise AttachError(
                            "rollback no acredita montaje/dispositivo/UUID"
                        )
                    checked(
                        (
                            "wsl.exe",
                            "-d",
                            plan.distro,
                            "-u",
                            "root",
                            "--",
                            "umount",
                            plan.mountpoint,
                        )
                    )
                checked(("wsl.exe", "--unmount", str(plan.final_path)))
            except BaseException as cleanup_error:  # noqa: BLE001 - retain cleanup beside primary
                cleanup_errors.append(cleanup_error)
        message = str(exc)
        if attached and cleanup_errors:
            message += (
                f"; incertidumbre cleanup (attached={attached}, mounted={mounted}): "
            )
            message += "; ".join(str(error) for error in cleanup_errors)
        if receipt_write_attempted:
            message += "; incertidumbre commit: recibo puede haber avanzado"
        error = AttachError(message)
        error.receipt_write_attempted = receipt_write_attempted
        error.primary = exc
        error.cleanup_errors = tuple(cleanup_errors)
        raise error from exc
    finally:
        if binding is not None:
            try:
                binding.close()
            except BaseException as close_error:
                if primary is not None:
                    # Preserve the primary cause while exposing failed lease cleanup.
                    error.cleanup_errors += (close_error,)
                    error.args = (
                        (
                            f"{error}; incertidumbre cleanup: BINDING_CLOSE_FAILED "
                            f"(attached={attached}, mounted={mounted}; "
                            "handles pueden seguir retenidos)"
                        ),
                    )
                    error.add_note(f"binding close: {close_error}")
                else:
                    raise AttachError(
                        f"binding close: {close_error}; incertidumbre commit: recibo puede haber avanzado"
                    ) from close_error


def _is_admin() -> bool:
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--distro", default="Ubuntu")
    parser.add_argument("--mountpoint", default="/mnt/studio-data")
    parser.add_argument(
        "--admin-observed",
        action="store_true",
        help="s?lo prepara el plan; nunca autoriza ejecuci?n",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        admin = _is_admin() if args.execute else args.admin_observed
        prepared = plan(
            args.project,
            args.receipt,
            distro=args.distro,
            mountpoint=args.mountpoint,
            admin=admin,
        )
        if not args.execute:
            print(
                {
                    "status": prepared.status,
                    "commands": [list(c) for c in prepared.commands],
                }
            )
            return 2 if prepared.status != "READY_TO_ATTACH" else 0
        if prepared.status != "READY_TO_ATTACH":
            print({"status": prepared.status, "commands": []})
            return 2
        receipt = execute(prepared)
        print(receipt.to_bytes().decode("utf-8"), end="")
        return 0
    except (
        OSError,
        ValueError,
        ReceiptError,
        AttachError,
        CustodyError,
        subprocess.SubprocessError,
    ) as exc:
        print({"status": "NOT_READY", "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
