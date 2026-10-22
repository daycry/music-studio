"""Bytes fuera del writer; mapping privado cerrado para paquetes inmutables."""

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from audio_post.manifest import _validate, safe_path, verify_manifest
from audio_post.private_context import (
    PreparedContext,
    prepare_context,
    project_request,
    verify_private_context,
)

from .contracts import FileReference, PreparedPackage, canonical_sha256

FILES = (
    ("master", "master.flac", "audio/flac"),
    ("listen", "listen.mp3", "audio/mpeg"),
    ("peaks", "peaks.json", "application/json"),
    ("manifest", "manifest.json", "application/json"),
)
MAX_PLAN_BYTES = 16 * 1024 * 1024
TOOL_PIN = Path("/studio/tools/ffmpeg-linux.lock.json")


def _context_material(context, prepared_context):
    """Return authenticated context bytes without repeating serialization."""
    if prepared_context is None:
        return prepare_context(context)
    if prepared_context.value is not context:
        raise ValueError("PROVENANCE_MISMATCH")
    return prepared_context.payload, prepared_context.digest


def canonical_bytes(value):
    value = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def identity(path):
    info = path.lstat()
    if path.is_symlink() or path.is_junction():
        raise ValueError("UNSAFE_PATH")
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def read_file(path, *, limit=None):
    before = identity(path)
    if (
        not stat.S_ISREG(before[2])
        or before[3] != 1
        or (limit is not None and before[4] > limit)
    ):
        raise ValueError("UNSAFE_PATH")
    fd = os.open(
        path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            (info.st_dev, info.st_ino) != before[:2]
            or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
        ):
            raise ValueError("UNSAFE_PATH")
        payload = stream.read() if limit is None else stream.read(limit + 1)
    if (
        identity(path) != before
        or len(payload) != before[4]
        or (limit is not None and len(payload) > limit)
    ):
        raise ValueError("UNSAFE_PATH")
    return payload


def write_once(path, payload):
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    fsync_directory(path.parent)


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def tool(ffmpeg, plan):
    pin = json.loads(read_file(TOOL_PIN, limit=65536))
    expected = TOOL_PIN.parent.parent / pin["dest"] / "bin/ffmpeg"
    if Path(ffmpeg) != expected or canonical_sha256(pin) != plan.tool_pin_sha256:
        raise ValueError("PROVENANCE_MISMATCH")
    # SHA is derived from the archive authenticated during image build.
    installed = json.loads(
        read_file(expected.parent.parent / ".installed.json", limit=65536)
    )
    if (
        installed["archive_sha256"] != pin["candidate"]["sha256"]
        or hashlib.sha256(read_file(expected)).hexdigest() != installed["ffmpeg_sha256"]
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    return pin


def read_resume_skip(directory, plan):
    """Takes que el server ya empaquetó en un intento anterior (reanudación).

    El hijo no las reprocesa. Fichero ausente: ninguna. Forma, duplicados o ids
    ajenos al plan → ``PROVENANCE_MISMATCH``.
    """
    marker = Path(directory) / "resume-skip.json"
    if not marker.exists():
        return set()

    def pairs(items):
        keys = [key for key, _ in items]
        if len(set(keys)) != len(keys):
            raise ValueError("PROVENANCE_MISMATCH")
        return dict(items)

    value = json.loads(read_file(marker, limit=65536), object_pairs_hook=pairs)
    ids = {entry.authority.take_id for entry in plan.takes}
    skip = value.get("skip") if isinstance(value, dict) else None
    if (
        set(value) != {"skip"}
        or not isinstance(skip, list)
        or len(set(skip)) != len(skip)
        or not set(skip) <= ids
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    return set(skip)


def stage(root, execution_id, entry):
    a = entry.authority
    return safe_path(
        root, f"data/songs/{a.song_id}/takes/.pending-{execution_id}/{a.take_id}"
    )


def create_package(
    plan,
    entry,
    directory,
    processed,
    pin,
    context,
    *,
    data_root,
    prepared_context: PreparedContext | None = None,
):
    _, receipt_sha = _context_material(context, prepared_context)
    a = entry.authority
    base = f"data/songs/{a.song_id}/takes/{a.take_id}/"
    descriptor = plan.provenance.descriptor.value
    take = context["takes"][a.take_id]
    outputs = [
        {**output, "path": base + output["path"]} for output in processed["outputs"]
    ]
    manifest = {
        "manifest_version": 1,
        "kind": "audio_take",
        "subject": {"type": "take", "id": a.take_id},
        "song_id": a.song_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "commercial_use": descriptor.commercial_use,
        "provider": {"type": "local"},
        "models": [
            {
                "role": "generator",
                "id": descriptor.id,
                "revision": descriptor.revision,
                "license": descriptor.license,
                "weights": [w.model_dump(mode="json") for w in descriptor.weights],
                "commercial_use": descriptor.commercial_use,
            }
        ],
        "pipeline": {
            "engine_id": plan.provenance.engine_id,
            "engine_version": plan.provenance.engine_version,
            "image_digest": plan.provenance.reported_image_digest,
            "workflow_id": None,
            "workflow_sha256": None,
            "custom_nodes": [],
            "remote_code": [],
        },
        "request": project_request(context, a.take_id),
        "inputs": [],
        "lineage": take["lineage"],
        "private_context": {"sha256": receipt_sha},
        "post": processed["post"],
        "outputs": outputs,
        "run": {"mode": plan.provenance.load.mode or "unknown"},
        "tools": [
            {
                "name": pin["tool_id"],
                "version": pin["candidate"]["ffmpeg_commit"],
                "license": "LGPLv3",
                "commercial_use": True,
                "build": pin["candidate"]["recipe_commit"],
            }
        ],
    }
    if plan.provenance.evidence_kind == "synthetic":
        manifest["evidence_kind"] = "synthetic"
        manifest["synthetic_binding"] = plan.provenance.synthetic_binding.model_dump(
            mode="json"
        )
    _validate(manifest)
    # A private validation view resolves only the fixed basenames; emitted
    # manifest keeps final paths and is never rewritten during publication.
    view = {
        **manifest,
        "outputs": [{**o, "path": FILES[i][1]} for i, o in enumerate(outputs)],
    }
    verify_manifest(view, directory, private_context_root=data_root)
    write_once(directory / "manifest.json", canonical_bytes(manifest) + b"\n")
    refs = {}
    for role, basename, media in FILES:
        payload = read_file(directory / basename)
        with (directory / basename).open("rb") as stream:
            os.fsync(stream.fileno())
        refs[role] = FileReference(
            path=base + basename,
            media_type=media,
            sha256=hashlib.sha256(payload).hexdigest(),
            bytes=len(payload),
        )
    fsync_directory(directory)
    return PreparedPackage(authority=a, **refs)


def verify_package(
    plan,
    entry,
    package,
    directory,
    context,
    *,
    data_root,
    prepared_context: PreparedContext | None = None,
):
    if package.authority != entry.authority:
        raise ValueError("PROVENANCE_MISMATCH")
    metadata = {}
    for role, basename, _ in FILES:
        payload = read_file(directory / basename)
        reference = getattr(package, role)
        if (
            hashlib.sha256(payload).hexdigest() != reference.sha256
            or len(payload) != reference.bytes
        ):
            raise ValueError("PROVENANCE_MISMATCH")
        metadata[basename] = identity(directory / basename)
    manifest = json.loads(read_file(directory / "manifest.json", limit=MAX_PLAN_BYTES))
    _validate(manifest)
    a = entry.authority
    take = context["takes"][a.take_id]
    _, receipt_sha = _context_material(context, prepared_context)
    if (
        manifest["subject"] != {"type": "take", "id": a.take_id}
        or manifest["song_id"] != a.song_id
        or manifest["kind"] != "audio_take"
        or manifest["request"]["seed"] != a.seed
        or manifest["request"]["variant_index"] != a.output_index
        or manifest["request"] != project_request(context, a.take_id)
        or manifest["request"]["task"] != plan.provenance.task
        or manifest["lineage"] != take["lineage"]
        or manifest.get("private_context") != {"sha256": receipt_sha}
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    verify_private_context(manifest, data_root)
    if plan.provenance.evidence_kind == "synthetic" and manifest.get(
        "synthetic_binding"
    ) != plan.provenance.synthetic_binding.model_dump(mode="json"):
        raise ValueError("PROVENANCE_MISMATCH")
    for role, basename, media in FILES[:3]:
        reference = getattr(package, role)
        matches = [o for o in manifest["outputs"] if o["role"] == role]
        if len(matches) != 1 or any(
            matches[0][k] != v for k, v in reference.model_dump().items()
        ):
            raise ValueError("PROVENANCE_MISMATCH")
    return metadata
