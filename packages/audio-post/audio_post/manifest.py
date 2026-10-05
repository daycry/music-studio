"""Validación y escritura inmutable de procedencia v1."""

import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = (
    Path(__file__).resolve().parents[3] / "packages/contracts/manifest-v1.schema.json"
)


def safe_path(root, relative):
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
        or relative.startswith("/")
        or PureWindowsPath(relative).drive
        or any(p in ("", ".", "..") for p in relative.split("/"))
    ):
        raise ValueError("UNSAFE_PATH")
    for part in relative.split("/"):
        if (
            part.rstrip(" .") != part
            or any(ord(c) < 32 or c in '<>"|?*' for c in part)
            or PureWindowsPath(part).is_reserved()
        ):
            raise ValueError("UNSAFE_PATH")
    root = Path(root).absolute()
    if any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
        raise ValueError("UNSAFE_PATH")
    root = root.resolve()
    target = root.joinpath(*relative.split("/"))
    if not target.resolve().is_relative_to(root):
        raise ValueError("UNSAFE_PATH")
    current = root
    for part in relative.split("/"):
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise ValueError("UNSAFE_PATH")
    return target


def _privacy(value):
    if isinstance(value, dict):
        if {
            "lyrics",
            "lyrics_text",
            "photo",
            "photo_path",
            "photo_data",
            "photos",
        } & value.keys():
            raise ValueError("MANIFEST_PRIVATE_CONTENT")
        for item in value.values():
            _privacy(item)
    elif isinstance(value, list):
        for item in value:
            _privacy(item)


def _validate(manifest):
    _privacy(manifest)
    if isinstance(manifest, dict) and isinstance(manifest.get("inputs"), list):
        for item in manifest.get("inputs", []):
            if isinstance(item, dict) and {"path", "url", "data"} & item.keys():
                raise ValueError("MANIFEST_PRIVATE_CONTENT")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            manifest
        )
    )
    if errors:
        raise ValueError("MANIFEST_SCHEMA: " + errors[0].message)


def verify_manifest(manifest, base_dir):
    if isinstance(manifest, (str, Path)):
        manifest = json.loads(Path(manifest).read_text(encoding="utf-8"))
    _validate(manifest)
    permissions = [
        item.get("commercial_use")
        for key in ("models", "tools", "inputs")
        for item in manifest[key]
    ]
    # v1 permits legacy dependencies without this optional declaration. Only
    # reject contradictions proved by the available declarations.
    if (manifest["commercial_use"] and False in permissions) or (
        permissions
        and all(permission is True for permission in permissions)
        and not manifest["commercial_use"]
    ):
        raise ValueError("COMMERCIAL_USE_MISMATCH")
    for output in manifest["outputs"]:
        path = safe_path(base_dir, output["path"])
        if not path.is_file():
            raise ValueError("OUTPUT_MISSING: " + output["path"])
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != output["sha256"]:
            raise ValueError("HASH_MISMATCH: " + output["path"])
        if "bytes" in output and path.stat().st_size != output["bytes"]:
            raise ValueError("SIZE_MISMATCH: " + output["path"])
    return {"valid": True, "outputs": len(manifest["outputs"])}


def write_manifest(path, manifest):
    result = copy.deepcopy(manifest)
    dependencies = [
        item for key in ("models", "tools", "inputs") for item in result.get(key, [])
    ]
    result["commercial_use"] = all(
        item.get("commercial_use") is True for item in dependencies
    )
    _validate(result)
    path = Path(path)
    verify_manifest(result, path.parent)
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
    return result
