"""Publish a verified offline VHDX through Windows handle custody.

The publisher copies only a receipt-backed staged file into a newly-created
owned file in ``data/_storage``. The final name is installed with the native
no-replace operation; existing objects are never adopted or overwritten.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from studio_storage_guard.receipt import ReceiptError, StorageReceipt

from scripts.storage_windows import WindowsCustody

_CHUNK = 1024 * 1024
_MAX_PUBLISH_BYTES = 64 * 1024**3


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _plain_file(path: Path, root: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError("fuente VHDX no es un archivo propio")
    root = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("fuente VHDX fuera del proyecto")
    current = path
    while True:
        metadata = current.lstat()
        if current.is_symlink() or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise ValueError("alias/reparse en ruta de reserva")
        if current == root:
            break
        if current.parent == current:
            raise ValueError("ra?z de reserva no coincide")
        current = current.parent
    return resolved


def _identity_text(identity: object) -> str:
    if isinstance(identity, tuple) and len(identity) == 2:
        volume, file_id = identity
        if isinstance(volume, int) and isinstance(file_id, bytes):
            return f"{volume}:{file_id.hex()}"
    raise ValueError("identidad de archivo publicada no acreditada")


def publish_verified_vhdx(
    project_root: str | Path,
    receipt_path: str | Path,
    *,
    custody_factory: Callable[..., WindowsCustody] = WindowsCustody,
) -> StorageReceipt:
    """Copy and atomically publish the VHDX described by a verified receipt."""
    root = Path(project_root).absolute()
    receipt_file = Path(receipt_path).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("ra?z de proyecto inv?lida")
    if receipt_file.is_symlink() or not receipt_file.is_file():
        raise ValueError("recibo ausente o no regular")
    receipt = StorageReceipt.from_bytes(receipt_file.read_bytes())
    if receipt.phase != "vhdx_verified":
        raise ReceiptError("recibo no est? en vhdx_verified")
    expected_size = receipt.history[-1]["evidence"]["vhdx_size"]
    expected_hash = receipt.history[-1]["evidence"]["vhdx_sha256"]
    if (
        type(expected_size) is not int
        or expected_size <= 0
        or expected_size > _MAX_PUBLISH_BYTES
    ):
        raise ValueError("tama?o VHDX no publicable")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ValueError("hash VHDX ausente")
    source = _plain_file(receipt_file.parent / "studio-data.vhdx", root)
    before = source.stat()
    if before.st_size != expected_size or _sha256(source) != expected_hash:
        raise ValueError("hash o tama?o de fuente VHDX no coincide")
    final = root / "data" / "_storage" / "studio-data.vhdx"
    if final.exists() or final.is_symlink():
        raise OSError(183, "destino publicado ya existe")
    final.parent.mkdir(parents=True, exist_ok=True)

    with custody_factory(root, "data/_storage") as custody:
        owned = custody.create_sparse_file("studio-data.vhdx.incoming", expected_size)
        offset = 0
        with source.open("rb") as stream:
            while chunk := stream.read(_CHUNK):
                owned.write(chunk, offset=offset)
                offset += len(chunk)
        after = source.stat()
        if after.st_size != before.st_size or _sha256(source) != expected_hash:
            raise ValueError("fuente VHDX cambi? durante la publicaci?n")
        seal = owned.seal(expected_hash)
        owned.promote_no_replace("studio-data.vhdx", seal)
        metadata = owned.inspect()
        file_id = _identity_text(metadata.identity)

    published = receipt.advance(
        "published",
        {"final_path": final.absolute().as_posix(), "file_id": file_id},
    )
    receipt_file.write_bytes(published.to_bytes())
    return published
