"""Preparación offline de un ext4 temporal y conversión VHDX.

El comando trabaja sólo en ``.cache/dev-cycle``. Nunca adopta ni reemplaza
``data/_storage/studio-data.vhdx`` y no intenta attach, mount o publicación.
La promoción final y la infraestructura WSL siguen siendo pasos separados.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from studio_storage_guard.receipt import StorageReceipt

TOOL_ROOT = (
    "/studio/tools/storage-linux/debian-bookworm-amd64/bundle-2026-10-09/sysroot"
)
TOOLS = {
    "mke2fs": f"{TOOL_ROOT}/sbin/mke2fs",
    "e2fsck": f"{TOOL_ROOT}/sbin/e2fsck",
    "qemu-img": f"{TOOL_ROOT}/usr/bin/qemu-img",
}
LIBRARY_PATH = f"{TOOL_ROOT}/usr/lib/x86_64-linux-gnu:{TOOL_ROOT}/lib/x86_64-linux-gnu"
_OPERATION_ID_LENGTH = 26


def _operation_id() -> str:
    return uuid4().hex.upper()[:_OPERATION_ID_LENGTH]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _plain_directory(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise ValueError("ruta de reserva no es un directorio propio")


@dataclass(frozen=True)
class StorageOfflinePlan:
    project_root: Path
    operation_id: str
    filesystem_uuid: str
    size_bytes: int
    image: str
    workspace: Path
    raw_path: Path
    vhdx_path: Path
    final_path: Path
    commands: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "operation_id": self.operation_id,
            "filesystem_uuid": self.filesystem_uuid,
            "size_bytes": self.size_bytes,
            "image": self.image,
            "workspace": self.workspace.as_posix(),
            "raw_path": self.raw_path.as_posix(),
            "vhdx_path": self.vhdx_path.as_posix(),
            "final_path": self.final_path.as_posix(),
            "commands": [list(command) for command in self.commands],
        }


def _command(workspace: Path, image: str, tool: str, *args: object) -> tuple[str, ...]:
    return (
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--mount",
        f"type=bind,source={workspace},target=/work",
        image,
        "env",
        f"LD_LIBRARY_PATH={LIBRARY_PATH}",
        TOOLS[tool],
        *(str(value) for value in args),
    )


def plan(
    project_root: str | Path,
    *,
    size_bytes: int,
    operation_id: str | None = None,
    filesystem_uuid: str | None = None,
    image: str,
) -> StorageOfflinePlan:
    root = Path(project_root).absolute()
    if not root.is_absolute() or root.is_symlink():
        raise ValueError("raiz de proyecto invalida")
    if type(size_bytes) is not int or size_bytes <= 0:
        raise ValueError("size_bytes invalido")
    operation_id = operation_id or _operation_id()
    if (
        type(operation_id) is not str
        or len(operation_id) != _OPERATION_ID_LENGTH
        or not operation_id.isalnum()
        or operation_id.upper() != operation_id
    ):
        raise ValueError("operation_id invalido")
    filesystem_uuid = filesystem_uuid or str(uuid4())
    if (
        not isinstance(filesystem_uuid, str)
        or str(UUID(filesystem_uuid)) != filesystem_uuid
    ):
        raise ValueError("filesystem_uuid invalido")
    if (
        not isinstance(image, str)
        or not image.strip()
        or any(value in image for value in "\r\n")
    ):
        raise ValueError("imagen de herramientas invalida")
    final_path = root / "data" / "_storage" / "studio-data.vhdx"
    if final_path.exists() or final_path.is_symlink():
        raise ValueError("final existente preservado")
    workspace = root / ".cache" / "dev-cycle" / f"storage-{operation_id}"
    if workspace.exists() or workspace.is_symlink():
        raise ValueError("reserva existente preservada")
    raw_path = workspace / "raw.ext4"
    vhdx_path = workspace / "studio-data.vhdx"
    commands = (
        _command(
            workspace,
            image,
            "mke2fs",
            "-t",
            "ext4",
            "-F",
            "-U",
            filesystem_uuid,
            "/work/raw.ext4",
        ),
        _command(workspace, image, "e2fsck", "-fn", "/work/raw.ext4"),
        _command(
            workspace,
            image,
            "qemu-img",
            "create",
            "-f",
            "vhdx",
            "/work/studio-data.vhdx",
            size_bytes,
        ),
        _command(
            workspace,
            image,
            "qemu-img",
            "convert",
            "-f",
            "raw",
            "-O",
            "vhdx",
            "-n",
            "/work/raw.ext4",
            "/work/studio-data.vhdx",
        ),
        _command(
            workspace,
            image,
            "qemu-img",
            "info",
            "--output=json",
            "/work/studio-data.vhdx",
        ),
    )
    return StorageOfflinePlan(
        root,
        operation_id,
        filesystem_uuid,
        size_bytes,
        image,
        workspace,
        raw_path,
        vhdx_path,
        final_path,
        commands,
    )


def execute(plan: StorageOfflinePlan, *, runner=subprocess.run) -> StorageReceipt:
    """Run the fixed CPU tools and leave a reviewable, unpromoted receipt."""
    _plain_directory(plan.project_root)
    _plain_directory(plan.project_root / ".cache")
    plan.workspace.parent.mkdir(parents=True, exist_ok=True)
    plan.workspace.mkdir()
    with plan.raw_path.open("xb") as stream:
        stream.truncate(plan.size_bytes)
    for command in plan.commands:
        runner(command, check=True, capture_output=True, text=True)
    if (
        plan.raw_path.is_symlink()
        or plan.vhdx_path.is_symlink()
        or not plan.raw_path.is_file()
        or not plan.vhdx_path.is_file()
    ):
        raise ValueError("salida de herramienta no es un archivo propio")
    receipt = StorageReceipt.reserve(
        project_root=plan.project_root,
        operation_id=plan.operation_id,
        size_bytes=plan.size_bytes,
    )
    receipt = receipt.advance(
        "raw_verified",
        {
            "raw_sha256": _sha256(plan.raw_path),
            "raw_size": plan.raw_path.stat().st_size,
            "uuid": plan.filesystem_uuid,
        },
    )
    receipt = receipt.advance(
        "vhdx_verified",
        {
            "vhdx_sha256": _sha256(plan.vhdx_path),
            "vhdx_size": plan.vhdx_path.stat().st_size,
        },
    )
    (plan.workspace / "receipt.json").write_bytes(receipt.to_bytes())
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--size-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--uuid", dest="filesystem_uuid")
    parser.add_argument("--operation-id")
    parser.add_argument("--image", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        prepared = plan(
            args.project,
            size_bytes=args.size_bytes,
            operation_id=args.operation_id,
            filesystem_uuid=args.filesystem_uuid,
            image=args.image,
        )
        if not args.execute:
            print(json.dumps(prepared.to_dict(), ensure_ascii=False, indent=2))
            return 0
        receipt = execute(prepared)
        print(receipt.to_bytes().decode("utf-8"), end="")
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(
            json.dumps({"status": "NOT_READY", "error": str(error)}, ensure_ascii=False)
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
