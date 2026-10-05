"""Preparación local fiel: sin engines, tokens ni modificación de originales."""

import base64
import copy
import difflib
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


def safe_path(root, relative):
    root = Path(root).absolute()
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()) or any(
        p.is_symlink() or p.is_junction() for p in (target, *target.parents)
    ):
        raise ValueError("UNSAFE_PATH")
    return target


def encode(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def prepare(request, *, sources=None, strip_tag_markdown=False):
    original = copy.deepcopy(request)
    effective = copy.deepcopy(request)
    transformations = []
    if strip_tag_markdown and "lyrics" in effective["params"]:
        text = effective["params"]["lyrics"]
        effective["params"]["lyrics"] = re.sub(
            r"(?m)^(\s*)\*\*(\[[^\]\r\n]+\])\*\*([ \t]*)(?=\r?$)", r"\1\2\3", text
        )
        transformations.append("strip_tag_markdown")
    fields = {}
    for name in ("lyrics", "style"):
        if name not in original["params"]:
            continue
        before, after = original["params"][name], effective["params"][name]
        raw = (sources or {}).get(name, before.encode("utf-8"))
        if name == "lyrics" and raw.decode("utf-8-sig") != before:
            raise ValueError("PREPARATION_SOURCE_MISMATCH")
        if (
            name == "lyrics"
            and original.get("lyrics_sha256") is not None
            and original["lyrics_sha256"] != digest(raw)
        ):
            raise ValueError("PREPARATION_SOURCE_MISMATCH")
        if name == "style" and raw.decode("utf-8-sig") != before:
            transformations.append("explicit_style")
        fields[name] = {
            "original": raw.decode("utf-8-sig"),
            "original_bytes_base64": base64.b64encode(raw).decode("ascii"),
            "original_bytes_sha256": digest(raw),
            "effective_sha256": digest(after.encode("utf-8")),
            "diff": "".join(
                difflib.unified_diff(
                    raw.decode("utf-8-sig").splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile="original",
                    tofile="effective",
                )
            ),
        }
    return {
        "version": 1,
        "original": original,
        "effective": effective,
        "effective_request_sha256": digest(encode(effective)),
        "fields": fields,
        "transformations": transformations,
        "engine_budget": "pending",
    }


def validate_receipt(receipt):
    try:
        base = dict(receipt)
        if "execution" in base:
            _validate_execution(base.pop("execution"), receipt["effective"])
        sources = {
            name: base64.b64decode(field["original_bytes_base64"], validate=True)
            for name, field in receipt["fields"].items()
        }
        if base != prepare(
            receipt["original"],
            sources=sources,
            strip_tag_markdown="strip_tag_markdown" in receipt["transformations"],
        ):
            raise ValueError("PREPARATION_INVALID")
    except (KeyError, TypeError, AttributeError, UnicodeError, ValueError) as error:
        raise ValueError("PREPARATION_INVALID") from error


def _validate_execution(execution, request):
    if (
        not isinstance(execution, dict)
        or set(execution) != {"seed", "n_outputs"}
        or type(execution["seed"]) is not int
        or type(execution["n_outputs"]) is not int
        or not 1 <= execution["n_outputs"] <= 64
        or not 0 <= execution["seed"] <= 2**64 - execution["n_outputs"]
        or execution["n_outputs"] != request.get("n_outputs")
        or (request.get("seed") is not None and execution["seed"] != request["seed"])
    ):
        raise ValueError("PREPARATION_EXECUTION_MISMATCH")


def bind_execution(receipt, *, seed, n_outputs):
    validate_receipt(receipt)
    execution = {"seed": seed, "n_outputs": n_outputs}
    _validate_execution(execution, receipt["effective"])
    bound = copy.deepcopy(receipt)
    bound["execution"] = execution
    return bound


def publish(receipt, data):
    validate_receipt(receipt)
    payload = encode(receipt)
    sha = digest(payload)
    directory = safe_path(data, "preparations")
    directory.mkdir(parents=True, exist_ok=True)
    target = safe_path(data, f"preparations/{sha}.json")
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if digest(target.read_bytes()) != sha:
                raise ValueError("PREPARATION_HASH_MISMATCH")
    finally:
        Path(temporary).unlink()
    return {"sha256": sha}


def verify(reference, request, data):
    if (
        not isinstance(reference, dict)
        or set(reference) != {"sha256"}
        or not isinstance(reference["sha256"], str)
        or not re.fullmatch("[0-9a-f]{64}", reference["sha256"])
    ):
        raise ValueError("PREPARATION_INVALID")
    payload = safe_path(data, f"preparations/{reference['sha256']}.json").read_bytes()
    if digest(payload) != reference["sha256"]:
        raise ValueError("PREPARATION_HASH_MISMATCH")
    try:
        receipt = json.loads(payload)
    except ValueError as error:
        raise ValueError("PREPARATION_INVALID") from error
    validate_receipt(receipt)
    if receipt["effective"] != request:
        raise ValueError("PREPARATION_REQUEST_MISMATCH")
    return receipt
