"""Validación y escritura inmutable de procedencia v1."""

import base64
import copy
import difflib
import hashlib
import json
import re
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
    if "preparation" in manifest:
        reference = manifest["preparation"]
        base = Path(base_dir).absolute()
        data = next(
            (p for p in (base, *base.parents) if (p / "preparations").is_dir()), base
        )
        path = safe_path(data, f"preparations/{reference['sha256']}.json")
        if not path.is_file():
            raise ValueError("PREPARATION_MISSING")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != reference["sha256"]:
            raise ValueError("PREPARATION_HASH_MISMATCH")
        effective = _preparation_effective(payload)
        receipt = json.loads(payload)
        request = manifest["request"]
        execution = receipt.get("execution")
        index = request.get("variant_index")
        if (
            not isinstance(execution, dict)
            or set(execution) != {"seed", "n_outputs"}
            or type(execution["seed"]) is not int
            or type(execution["n_outputs"]) is not int
            or not 1 <= execution["n_outputs"] <= 64
            or not 0 <= execution["seed"] <= 2**64 - execution["n_outputs"]
            or execution["n_outputs"] != effective.get("n_outputs")
            or (
                effective.get("seed") is not None
                and effective["seed"] != execution["seed"]
            )
            or type(index) is not int
            or not 0 <= index < execution["n_outputs"]
            or request["seed"] != execution["seed"] + index
        ):
            raise ValueError("PREPARATION_REQUEST_MISMATCH")
        if (
            effective["task"] != request["task"]
            or {
                k: v
                for k, v in effective["params"].items()
                if k not in {"lyrics", "style"}
            }
            != request["params"]
            or effective.get("lyrics_declaration") != request.get("lyrics_declaration")
            or effective.get("lyrics_sha256") != request.get("lyrics_sha256")
        ):
            raise ValueError("PREPARATION_REQUEST_MISMATCH")
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


def _preparation_effective(payload):
    """Comprueba la evidencia privada sin importar CLI, engines ni modelos."""
    try:
        receipt = json.loads(payload)
        effective = receipt["effective"]
        original = receipt["original"]
        canonical = (
            json.dumps(
                effective,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        if (
            receipt["version"] != 1
            or receipt["engine_budget"] != "pending"
            or hashlib.sha256(canonical).hexdigest()
            != receipt["effective_request_sha256"]
        ):
            raise ValueError()
        expected = copy.deepcopy(original)
        transformations = []
        if "strip_tag_markdown" in receipt["transformations"]:
            transformations.append("strip_tag_markdown")
            expected["params"]["lyrics"] = re.sub(
                r"(?m)^(\s*)\*\*(\[[^\]\r\n]+\])\*\*([ \t]*)(?=\r?$)",
                r"\1\2\3",
                original["params"]["lyrics"],
            )
        if expected != effective or not isinstance(effective["task"], str):
            raise ValueError()
        names = {name for name in ("lyrics", "style") if name in effective["params"]}
        if names != set(receipt["fields"]):
            raise ValueError()
        for name in names:
            field = receipt["fields"][name]
            raw = base64.b64decode(field["original_bytes_base64"], validate=True)
            before = raw.decode("utf-8-sig")
            after = effective["params"][name]
            if name == "lyrics" and before != original["params"][name]:
                raise ValueError()
            if (
                name == "lyrics"
                and original.get("lyrics_sha256") is not None
                and original["lyrics_sha256"] != hashlib.sha256(raw).hexdigest()
            ):
                raise ValueError()
            if name == "style" and before != original["params"][name]:
                transformations.append("explicit_style")
            diff = "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile="original",
                    tofile="effective",
                )
            )
            if (
                before != field["original"]
                or hashlib.sha256(raw).hexdigest() != field["original_bytes_sha256"]
                or hashlib.sha256(after.encode("utf-8")).hexdigest()
                != field["effective_sha256"]
                or diff != field["diff"]
            ):
                raise ValueError()
        if transformations != receipt["transformations"]:
            raise ValueError()
        return effective
    except (KeyError, TypeError, AttributeError, ValueError, UnicodeError) as error:
        raise ValueError("PREPARATION_INVALID") from error


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
