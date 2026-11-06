"""ADR-0069: política offline y planes sin ejecución de almacenamiento.

No realiza provisión ni acredita custodia nativa/UUID/NOREPLACE.
El CLI siempre termina bloqueado (exit 2), incluidos planes bien formados.
"""

import argparse
import json
import re
import stat
from pathlib import Path
from uuid import UUID

OPERATIONS = {
    "create": (
        "CreateVirtualDisk CREATE_NEW dinámico, file ID/ACL y handle retenido",
        "Acreditar vacío y asociación propia device; fijar UUID ext4 nuevo",
    ),
    "attach": (
        "Abrir sólo VHDX del proyecto por receipt/file ID/ACL",
        "Correlacionar handle propio con device WSL, sin índice de lista",
    ),
    "mount": (
        "Correlacionar device del VHDX propio y UUID ext4 retenidos",
        "Acreditar mount exacto rw y prueba nativa NOREPLACE bajo custodia",
    ),
    "detach": (
        "Validar handle propio, device, UUID y receipt vigente",
        "Quiesce, flush y detach propio; preservar VHDX/receipt y servicios ajenos",
    ),
}


def disk_path(project: Path) -> Path:
    """Auditoría readonly: no sustituye custodia por handles para mutaciones."""
    root = Path(project).absolute()
    disk = root / "data" / "_storage" / "studio-data.vhdx"
    candidates = list(disk.parents)
    candidates.reverse()
    candidates.append(disk)
    for candidate in candidates:
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        attributes = getattr(metadata, "st_file_attributes", 0)
        if attributes & 0x400 or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("alias/reparse en ruta del disco")
        if candidate != disk:
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError("padre del disco no es directorio")
        elif not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("hardlink/alias o archivo de disco no regular")
    resolved = disk.resolve(strict=False)
    if resolved != disk or not resolved.is_relative_to(root.resolve(strict=True)):
        raise ValueError("alias o escape del proyecto")
    return resolved


def plan(project: Path, operation: str, *, admin: bool = False, size_gib: int = 64):
    if operation not in OPERATIONS:
        raise ValueError("operación de almacenamiento desconocida")
    if type(size_gib) is not int or size_gib < 8 or size_gib > 1024:
        raise ValueError("presupuesto fuera de 8..1024 GiB")
    disk = disk_path(project)
    result = {
        "disk": str(disk),
        "operation": operation,
        "size_bytes": size_gib * (1024**3),
        "commands": [],
    }
    if admin is not True:
        status, gap = "NEEDS_ADMIN", "Token administrador no acreditado"
    elif operation == "create" and disk.exists():
        status, gap = "CONFLICT", "Disco existente preservado: no adoptar/formatear"
    else:
        status = "NEEDS_CONTEXT"
        gap = "Custodia nativa handle VHDX/device no implementada; no executor"
        result["requirements"] = list(OPERATIONS[operation])
    result.update(status=status, gap=gap)
    return result


def _canonical_root(root: str) -> None:
    if not re.fullmatch(r"/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", root):
        raise ValueError("vista virtual no canónica")
    if re.match(r"^/mnt/[a-z](?:/|$)", root):
        raise ValueError("vista de unidad Windows rechazada")


def _canonical_uuid(value: str) -> None:
    if str(UUID(value)) != value:
        raise ValueError("UUID no canónico")


def validate_evidence(item: dict, root: str, expected_uuid: str) -> None:
    """Política simulable: fixtures booleanas no son garantía del kernel."""
    _canonical_root(root)
    _canonical_uuid(expected_uuid)
    if item.get("disk_bound") is not True:
        raise ValueError("disk identity pendiente de custodia nativa")
    required = {
        "root": root,
        "mountpoint": root,
        "mount_root": "/",
        "fs_type": "ext4",
        "uuid": expected_uuid,
    }
    for key, expected in required.items():
        if item.get(key) != expected:
            raise ValueError(f"evidencia de {key} incorrecta")
    if item.get("read_only") is not False:
        raise ValueError("montaje readonly o no acreditado")
    if not re.fullmatch(r"/dev/[A-Za-z0-9_-]+", item.get("source", "")):
        raise ValueError("device no canónico")
    if item.get("noreplace") is not True:
        raise ValueError("NOREPLACE pendiente de prueba nativa")


def parse_mountinfo(text: str, root: str) -> dict:
    _canonical_root(root)
    found = []
    for row in text.splitlines():
        sections = row.split(" - ")
        if len(sections) != 2:
            raise ValueError("mountinfo malformado")
        mount, filesystem = (section.split() for section in sections)
        if len(mount) < 6 or len(filesystem) < 3:
            raise ValueError("mountinfo malformado")
        if mount[4] != root:
            continue
        options = set(mount[5].split(",")) | set(filesystem[2].split(","))
        found.append(
            {
                "root": root,
                "mountpoint": mount[4],
                "mount_root": mount[3],
                "source": filesystem[1],
                "fs_type": filesystem[0],
                "read_only": "ro" in options,
            }
        )
    if len(found) != 1:
        raise ValueError("montaje exacto ausente o ambiguo")
    return found[0]


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("operation", choices=[*OPERATIONS, "preflight"])
    cli.add_argument(
        "--project", type=Path, default=Path(__file__).resolve().parents[1]
    )
    cli.add_argument("--size-gib", type=int, default=64)
    cli.add_argument(
        "--admin-observed",
        action="store_true",
        help="Observación para plan: nunca autorización de ejecución",
    )
    cli.add_argument("--root")
    cli.add_argument("--uuid")
    args = cli.parse_args(argv)
    try:
        if args.operation != "preflight":
            output = plan(
                args.project,
                args.operation,
                admin=args.admin_observed,
                size_gib=args.size_gib,
            )
        else:
            if not args.root or not args.uuid:
                raise ValueError("preflight requiere --root y --uuid")
            _canonical_root(args.root)
            _canonical_uuid(args.uuid)
            output = {
                "status": "NEEDS_CONTEXT",
                "commands": [],
                "gap": "Custodia VHDX/device y UUID/NOREPLACE nativos pendientes; startup bloqueado",
            }
    except (OSError, ValueError) as error:
        output = {"status": "REJECTED", "commands": [], "gap": str(error)}
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
