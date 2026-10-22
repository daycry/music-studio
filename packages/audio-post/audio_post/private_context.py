"""Recibo de solicitud y linaje; integridad privada, sin autoridad SQL."""

import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

MAX_CONTEXT_BYTES = 16 * 1024 * 1024
_ID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}")
_HASH = re.compile(r"[0-9a-f]{64}")
_SECRET = (
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "apikey",
    "privatekey",
    "ciphertext",
    "header",
)
_PHOTO = {"photo", "photos", "photopath", "photodata", "photourl"}
_PRIVATE = {"lyrics", "lyricstext", "style", "styleprompt", "tags"}


@dataclass(frozen=True)
class PreparedContext:
    """Validated immutable material reused by one worker execution.

    ``value`` remains available for projections while ``payload`` and
    ``digest`` are the authenticated representation.  File custody is still
    checked by callers that read the durable receipt; this object only avoids
    reserialising the same already validated context for every output.
    """

    value: dict
    payload: bytes
    digest: str


def _fail():
    raise ValueError("PRIVATE_CONTEXT_INVALID")


def _name(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _json(value, depth=0, *, public=False):
    if depth > 20:
        _fail()
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is str:
        if len(value) > MAX_CONTEXT_BYTES:
            _fail()
        return
    if type(value) not in (dict, list) or len(value) > 256:
        _fail()
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                _fail()
            name = _name(key)
            if (
                any(word in name for word in _SECRET)
                or name in _PHOTO
                or (public and name in _PRIVATE)
            ):
                _fail()
        value = value.values()
    for item in value:
        _json(item, depth + 1, public=public)


def _closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        _fail()


def _id(value):
    if type(value) is not str or not _ID.fullmatch(value):
        _fail()


def _hash(value):
    if type(value) is not str or not _HASH.fullmatch(value):
        _fail()


def _text(value):
    if type(value) is not str or not value:
        _fail()


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        _fail()


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _validate(value):
    _json(value)
    _closed(
        value,
        {"version", "winning_request_sha256", "captured_request", "song_id", "takes"},
    )
    if type(value["version"]) is not int or value["version"] != 1:
        _fail()
    _id(value["song_id"])
    _hash(value["winning_request_sha256"])
    request = value["captured_request"]
    _closed(
        request,
        {
            "job_id",
            "task",
            "model_id",
            "mode",
            "inputs",
            "params",
            "seed",
            "n_outputs",
            "output_dir",
            "timeout_s",
        },
    )
    _id(request["job_id"])
    for key in ("task", "model_id"):
        _text(request[key])
    if request["mode"] is not None:
        _text(request["mode"])
    if request["output_dir"] != f"tmp/{request['job_id']}":
        _fail()
    _integer(request["seed"], 0, 2**64 - 1)
    _integer(request["n_outputs"], 1, 64)
    _integer(request["timeout_s"], 1, 2**63 - 1)
    if (
        request["seed"] + request["n_outputs"] > 2**64
        or type(request["params"]) is not dict
        or type(request["inputs"]) is not list
    ):
        _fail()
    for item in request["inputs"]:
        _closed(item, {"role", "path", "sha256", "media_type"})
        _text(item["role"])
        _text(item["media_type"])
        _hash(item["sha256"])
        # Pure lexical confinement; this validates no input file or authority.
        path = item["path"]
        if (
            type(path) is not str
            or not path
            or "\\" in path
            or ":" in path
            or path.startswith("/")
            or any(p in {"", ".", ".."} for p in path.split("/"))
        ):
            _fail()
    if (
        hashlib.sha256(_canonical(request)).hexdigest()
        != value["winning_request_sha256"]
    ):
        _fail()
    takes = value["takes"]
    if type(takes) is not dict or not 1 <= len(takes) <= request["n_outputs"]:
        _fail()
    indices = set()
    for take_id, take in takes.items():
        _id(take_id)
        _closed(
            take,
            {
                "output_index",
                "root_id",
                "params",
                "model_id",
                "model_version",
                "commercial_use",
                "lineage",
                "lyrics",
            },
        )
        _integer(take["output_index"], 0, request["n_outputs"] - 1)
        if take["output_index"] in indices:
            _fail()
        indices.add(take["output_index"])
        _id(take["root_id"])
        _text(take["model_version"])
        if (
            take["model_id"] != request["model_id"]
            or type(take["commercial_use"]) is not bool
            or type(take["params"]) is not dict
        ):
            _fail()
        lineage = take["lineage"]
        _closed(lineage, {"parents", "derivation", "section_map"})
        if (
            type(lineage["parents"]) is not list
            or lineage["derivation"]
            not in {
                "original",
                "variant",
                "extend",
                "repaint",
                "cover",
                "complete",
                "remaster",
                "edit",
            }
            or (
                lineage["section_map"] is not None
                and type(lineage["section_map"]) is not dict
            )
        ):
            _fail()
        for parent in lineage["parents"]:
            _closed(parent, {"type", "id", "role"})
            _id(parent["id"])
            _text(parent["type"])
            _text(parent["role"])
        if lineage["derivation"] == "original" and (
            take["root_id"] != take_id or lineage["parents"]
        ):
            _fail()
        proof = take["lyrics"]
        lyrics = request["params"].get("lyrics", "")
        if type(lyrics) is not str:
            _fail()
        if proof is None:
            if lyrics:
                _fail()
        else:
            _closed(proof, {"lyrics_version_id", "sha256", "declaration"})
            _id(proof["lyrics_version_id"])
            _hash(proof["sha256"])
            if (
                proof["declaration"]
                not in {"own", "assistant", "public_domain", "licensed"}
                or hashlib.sha256(lyrics.encode("utf-8")).hexdigest() != proof["sha256"]
            ):
                _fail()
        if "lyrics" in take["params"] and take["params"]["lyrics"] != lyrics:
            _fail()


def prepare_context(value):
    """Valida y devuelve bytes canónicos y SHA; no escribe ni concede autoridad."""
    try:
        _validate(value)
        payload = _canonical(value)
        if len(payload) > MAX_CONTEXT_BYTES:
            _fail()
        return payload, hashlib.sha256(payload).hexdigest()
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise ValueError("PRIVATE_CONTEXT_INVALID") from None


def prepare_context_once(value):
    """Validate and canonicalise a context once for a bounded execution."""
    payload, digest = prepare_context(value)
    return PreparedContext(value=value, payload=payload, digest=digest)


def project_request(value, take_id):
    """Proyecta lo solicitado, sin simular parámetros efectivos del engine."""
    prepare_context(value)
    try:
        take = value["takes"][take_id]
        request = value["captured_request"]
        params = {
            k: v
            for k, v in request["params"].items()
            if k
            not in {
                "lyrics",
                "style",
                "lyrics_sha256",
                "lyrics_declaration",
                "lyrics_version_id",
            }
        }
        _json(params, public=True)
        result = {
            "task": request["task"],
            "params": params,
            "seed": request["seed"] + take["output_index"],
            "variant_index": take["output_index"],
        }
        if take["lyrics"] is not None:
            result.update(
                lyrics_sha256=take["lyrics"]["sha256"],
                lyrics_declaration=take["lyrics"]["declaration"],
            )
        # Return a detached JSON view, never mutable references into the receipt.
        return json.loads(_canonical(result))
    except (KeyError, ValueError, TypeError):
        raise ValueError("PRIVATE_CONTEXT_INVALID") from None


def _identity(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _read(data_root, digest):
    from .manifest import safe_path

    path = safe_path(data_root, f"private-contexts/{digest}.json")
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or not 0 < before.st_size <= MAX_CONTEXT_BYTES
        or (hasattr(os, "getuid") and before.st_uid != os.getuid())
    ):
        _fail()
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    with os.fdopen(descriptor, "rb") as stream:
        opened = _identity(os.fstat(stream.fileno()))
        pathname = _identity(before)
        # Windows 3.12 reports different ctime domains through path and FD
        # APIs. Keep full ctime checks within each domain on both platforms.
        if (opened[:-1] != pathname[:-1]) if os.name == "nt" else (opened != pathname):
            _fail()
        payload = stream.read(MAX_CONTEXT_BYTES + 1)
        if (
            len(payload) != before.st_size
            or _identity(os.fstat(stream.fileno())) != opened
        ):
            _fail()
    # Revalidate the fixed ancestors and pathname after reading the same FD.
    safe_path(data_root, f"private-contexts/{digest}.json")
    if (
        _identity(path.lstat()) != _identity(before)
        or hashlib.sha256(payload).hexdigest() != digest
    ):
        _fail()
    return payload


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            _fail()
        result[key] = value
    return result


def context_root(manifest, base_dir):
    """Sólo la disposición durable fijada permite inferir la raíz de datos."""
    base = Path(base_dir).absolute()
    parts = base.parts
    if len(parts) < 5 or parts[-4:] != (
        "songs",
        manifest["song_id"],
        "takes",
        manifest["subject"]["id"],
    ):
        _fail()
    return base.parents[3]


def verify_private_context(manifest, data_root):
    """Verifica correspondencia privada; devuelve sólo el resultado público."""
    try:
        reference = manifest["private_context"]
        _closed(reference, {"sha256"})
        _hash(reference["sha256"])
        payload = _read(data_root, reference["sha256"])
        value = json.loads(payload, object_pairs_hook=_pairs)
        canonical, digest = prepare_context(value)
        if canonical != payload or digest != reference["sha256"]:
            _fail()
        subject = manifest["subject"]
        _closed(subject, {"type", "id"})
        take = value["takes"][subject["id"]]
        if (
            manifest["kind"] != "audio_take"
            or subject["type"] != "take"
            or manifest["song_id"] != value["song_id"]
            or _canonical(manifest["request"])
            != _canonical(project_request(value, subject["id"]))
            or _canonical(manifest["lineage"]) != _canonical(take["lineage"])
        ):
            _fail()
        _json(manifest, public=True)
        generators = [m for m in manifest["models"] if m.get("role") == "generator"]
        if (
            len(generators) != 1
            or generators[0]["id"] != take["model_id"]
            or type(generators[0].get("commercial_use")) is not bool
            or generators[0].get("commercial_use") != take["commercial_use"]
        ):
            _fail()
        return {"valid": True}
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise ValueError("PRIVATE_CONTEXT_INVALID") from None
