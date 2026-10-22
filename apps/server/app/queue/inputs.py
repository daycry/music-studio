"""Referencias propias y verificación de bytes fuera del writer."""

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from engine_contract import Input
from sqlalchemy import select

from app.models import Asset, Job, JobAttempt, JobDependency, Song, Take, Upload


class ResolutionError(ValueError):
    """Petición no admisible antes de reservar."""


def confined_path(root, relative):
    root = Path(root)
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ResolutionError("Input file absent or outside data")
    cursor = path
    while True:
        if cursor.is_symlink() or (
            hasattr(cursor, "is_junction") and cursor.is_junction()
        ):
            raise ResolutionError("Input link")
        if cursor == root:
            break
        if cursor.parent == cursor:
            raise ResolutionError("Input outside data")
        cursor = cursor.parent
    if path.stat().st_nlink != 1:
        raise ResolutionError("Input alias")
    return path


def verified_file(root, wire):
    path = confined_path(root, wire["path"])
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != wire["sha256"]:
            raise ResolutionError("Input hash mismatch")


def owned_inputs(job, session, data_dir, *, verify=True):
    wires = []
    for item in job.request.get("inputs", []):
        if (
            not isinstance(item, dict)
            or set(item) - {"role", "ref", "output_index"}
            or "ref" not in item
            or session is None
        ):
            raise ResolutionError("Owned DB input reference required")
        ref = item["ref"]
        if not isinstance(ref, dict) or set(ref) != {"type", "id"}:
            raise ResolutionError("Invalid input reference")
        kind, rid = ref["type"], ref["id"]
        row = None
        if kind == "upload":
            row = session.get(Upload, rid)
        elif kind in {"take", "asset"}:
            row = (
                session.get(Asset, rid)
                if kind == "asset"
                else session.scalar(
                    select(Asset).where(
                        Asset.subject_type == "take",
                        Asset.subject_id == rid,
                        Asset.role == item["role"],
                        Asset.deleted_at.is_(None),
                    )
                )
            )
            take = (
                session.get(Take, row.subject_id)
                if row and row.subject_type == "take"
                else None
            )
            song = session.get(Song, take.song_id) if take else None
            if (
                not take
                or take.owner_id != job.owner_id
                or take.status != "ready"
                or take.deleted_at
                or not song
                or (
                    song.id != job.song_id
                    or song.owner_id != job.owner_id
                    or song.deleted_at
                    or song.is_dependency_only
                )
            ):
                raise ResolutionError("Input take not ready or owned live root")
        elif kind == "job":
            parent = session.get(Job, rid)
            edge = session.scalar(
                select(JobDependency.id).where(
                    JobDependency.job_id == job.id,
                    JobDependency.depends_on_job_id == rid,
                    JobDependency.owner_id == job.owner_id,
                    JobDependency.deleted_at.is_(None),
                )
            )
            if (
                not parent
                or not edge
                or parent.owner_id != job.owner_id
                or parent.song_id != job.song_id
                or parent.status != "succeeded"
                or parent.deleted_at
            ):
                raise ResolutionError("Output parent unavailable")
            attempt = session.scalar(
                select(JobAttempt)
                .where(
                    JobAttempt.job_id == rid,
                    JobAttempt.status == "succeeded",
                    JobAttempt.deleted_at.is_(None),
                )
                .order_by(JobAttempt.ordinal.desc())
            )
            artifacts = (
                attempt.terminal.data["artifacts"]
                if attempt and attempt.terminal
                else []
            )
            matches = [
                a for a in artifacts if a["output_index"] == item.get("output_index", 0)
            ]
            if len(matches) != 1 or not matches[0]["path"].startswith(
                "tmp/" + attempt.id + "/"
            ):
                raise ResolutionError("Output identity unavailable")
            media = matches[0]
        else:
            raise ResolutionError("Unsupported input reference")
        if kind != "job":
            if not row or row.owner_id != job.owner_id or row.deleted_at:
                raise ResolutionError("Input not owned")
            media = {key: getattr(row, key) for key in ("path", "sha256", "media_type")}
        wire = Input(
            role=item["role"],
            **{key: media[key] for key in ("path", "sha256", "media_type")},
        ).model_dump(mode="json")
        if verify:
            verified_file(data_dir, wire)
        else:
            confined_path(data_dir, wire["path"])
        wires.append(wire)
    return wires


def file_identity(path):
    info = path.stat()
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


@dataclass(frozen=True)
class StagedInputs:
    root: Path
    directory: Path | None
    wires: list
    identities: tuple

    def check(self):
        for wire, identity in zip(self.wires, self.identities, strict=True):
            path = confined_path(self.root, wire["path"])
            if file_identity(path) != identity:
                raise ResolutionError("Owned input staging changed")

    def cleanup(self):
        if self.directory is None:
            return
        # Sólo nombres creados por esta copia, nunca borrado recursivo de contenido desconocido.
        for wire in self.wires:
            path = confined_path(self.root, wire["path"])
            if path.parent != self.directory or path.is_symlink():
                raise ResolutionError("Staging cleanup ownership changed")
            path.chmod(stat.S_IWRITE | stat.S_IREAD)
            path.unlink()
        self.directory.rmdir()


def stage_inputs(root, wires):
    root = Path(root)
    if not wires:
        return StagedInputs(root, None, [], ())
    parent = root / "tmp/_server_inputs"
    for path in (root, root / "tmp", parent):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ResolutionError("Staging parent link")
        path.mkdir(exist_ok=True)
    directory = parent / uuid4().hex
    directory.mkdir(mode=0o700)
    copied, identities = [], []
    try:
        for index, wire in enumerate(wires):
            source = confined_path(root, wire["path"])
            destination = directory / str(index)
            copied_wire = dict(wire, path=destination.relative_to(root).as_posix())
            digest = hashlib.sha256()
            try:
                incoming = source.open("rb")
            except FileNotFoundError as exc:
                raise ResolutionError("Input disappeared before staging") from exc
            with incoming, destination.open("xb") as outgoing:
                copied.append(copied_wire)
                while chunk := incoming.read(1024 * 1024):
                    outgoing.write(chunk)
                    digest.update(chunk)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            if digest.hexdigest() != wire["sha256"]:
                raise ResolutionError("Input changed during staging")
            # SHA fresco de la copia fuera del writer; no usa un manifiesto como autoridad.
            verified_file(root, copied_wire)
            destination.chmod(stat.S_IREAD)
            identities.append(file_identity(destination))
        return StagedInputs(root, directory, copied, tuple(identities))
    except BaseException:
        StagedInputs(root, directory, copied, ()).cleanup()
        raise
