"""Autoridad DB de referencias; bytes y staging delegados a inputs de U1."""

from sqlalchemy import func, select, tuple_

from app.models import Asset, Job, JobAttempt, JobDependency, Song, Take, User

from .inputs import ResolutionError, owned_inputs


def _rows(session, model, column, ids):
    ids = list(ids)
    rows = []
    for start in range(0, len(ids), 400):
        rows.extend(
            session.scalars(select(model).where(column.in_(ids[start : start + 400])))
        )
    return rows


class _ReferenceWindow:
    """Sólo identidades de esta ventana y esta transacción; nunca entre polls."""

    def __init__(self, session, jobs):
        self.session = session
        self.job_ids = {job.id for job in jobs}
        self.roots = {
            Song: {
                row.id: row
                for row in _rows(session, Song, Song.id, {j.song_id for j in jobs})
            },
            User: {
                row.id: row
                for row in _rows(session, User, User.id, {j.owner_id for j in jobs})
            },
        }
        refs = []
        for job in jobs:
            items = job.request.get("inputs", [])
            if isinstance(items, list):
                refs.extend(
                    (item["ref"], item.get("role"))
                    for item in items
                    if isinstance(item, dict)
                    and isinstance(item.get("ref"), dict)
                    and isinstance(item["ref"].get("id"), str)
                )
        self.edges = {jid: [] for jid in self.job_ids}
        for edge in _rows(session, JobDependency, JobDependency.job_id, self.job_ids):
            if not edge.deleted_at:
                self.edges[edge.job_id].append(edge)
        parent_ids = {ref["id"] for ref, _ in refs if ref.get("type") == "job"}
        parent_ids.update(
            edge.depends_on_job_id for edges in self.edges.values() for edge in edges
        )
        self.parents = {row.id: row for row in _rows(session, Job, Job.id, parent_ids)}
        winning = {(p.id, p.attempt) for p in self.parents.values()}
        self.attempts = {}
        winning = list(winning)
        for start in range(0, len(winning), 400):
            for row in session.scalars(
                select(JobAttempt).where(
                    tuple_(JobAttempt.job_id, JobAttempt.ordinal).in_(
                        winning[start : start + 400]
                    ),
                    JobAttempt.deleted_at.is_(None),
                )
            ):
                self.attempts[(row.job_id, row.ordinal)] = row
        asset_ids = {ref["id"] for ref, _ in refs if ref.get("type") == "asset"}
        self.assets = {
            row.id: row for row in _rows(session, Asset, Asset.id, asset_ids)
        }
        take_ids = {ref["id"] for ref, _ in refs if ref.get("type") == "take"}
        take_ids.update(
            a.subject_id for a in self.assets.values() if a.subject_type == "take"
        )
        self.takes = {row.id: row for row in _rows(session, Take, Take.id, take_ids)}
        pairs = list(
            {
                (ref["id"], role)
                for ref, role in refs
                if ref.get("type") == "take" and isinstance(role, str)
            }
        )
        self.take_assets = {}
        for start in range(0, len(pairs), 400):
            # Dos filas bastan para detectar ambigüedad; memoria acotada por identidad.
            ranked = (
                select(
                    Asset.id,
                    func.row_number()
                    .over(
                        partition_by=(Asset.subject_id, Asset.role), order_by=Asset.id
                    )
                    .label("position"),
                )
                .where(
                    Asset.subject_type == "take",
                    Asset.deleted_at.is_(None),
                    tuple_(Asset.subject_id, Asset.role).in_(
                        pairs[start : start + 400]
                    ),
                )
                .subquery()
            )
            for asset in session.scalars(
                select(Asset)
                .join(ranked, ranked.c.id == Asset.id)
                .where(ranked.c.position <= 2)
            ):
                self.take_assets.setdefault((asset.subject_id, asset.role), []).append(
                    asset
                )
        self.transaction = session.get_transaction()

    def check(self, session, job):
        if (
            session is not self.session
            or session.get_transaction() is not self.transaction
            or job.id not in self.job_ids
        ):
            raise ResolutionError("Reference window transaction mismatch")


def preload_references(session, jobs):
    jobs = [job for job in jobs if job.request.get("inputs")]
    return _ReferenceWindow(session, jobs) if jobs else None


def validate_references(job, session, *, window=None):
    """Sólo las referencias de esta fila, sin inventarios ni lectura de bytes."""
    items = job.request.get("inputs", [])
    if not items:
        return
    if session is None or not isinstance(items, list):
        raise ResolutionError("Database bound inputs required")
    window = window or preload_references(session, [job])
    window.check(session, job)
    song, user = (
        window.roots[Song].get(job.song_id),
        window.roots[User].get(job.owner_id),
    )
    if not (
        song
        and user
        and user.name == "local"
        and not user.deleted_at
        and song.owner_id == job.owner_id
        and not song.deleted_at
        and not song.is_dependency_only
    ):
        raise ResolutionError("Reference root unavailable")
    identities = set()
    for item in items:
        if (
            not isinstance(item, dict)
            or "ref" not in item
            or set(item) - {"ref", "role", "output_index"}
        ):
            raise ResolutionError("Stable reference required")
        ref = item["ref"]
        if not isinstance(ref, dict) or set(ref) != {"type", "id"}:
            raise ResolutionError("Reference identity required")
        kind, rid = ref["type"], ref["id"]
        index = item.get("output_index", 0)
        if (
            not isinstance(rid, str)
            or not isinstance(item.get("role"), str)
            or type(index) is not int
            or index < 0
        ):
            raise ResolutionError("Typed reference required")
        identity = (kind, rid, index, item["role"])
        if identity in identities:
            raise ResolutionError("Duplicate reference")
        identities.add(identity)
        if kind == "job":
            parent = window.parents.get(rid)
            edge = next(
                (e for e in window.edges[job.id] if e.depends_on_job_id == rid), None
            )
            if not (
                parent
                and edge
                and edge.owner_id == job.owner_id
                and parent.owner_id == job.owner_id
                and parent.song_id == job.song_id
                and parent.status == "succeeded"
                and not parent.deleted_at
                and not parent.cancel_requested_at
            ):
                raise ResolutionError("Owned successful dependency required")
            attempt = window.attempts.get((rid, parent.attempt))
            if not (
                attempt
                and attempt.owner_id == job.owner_id
                and attempt.status == "succeeded"
                and attempt.engine_id == parent.engine_id
                and attempt.terminal
                and attempt.terminal.type == "done"
                and attempt.terminal.job_id == attempt.id
                and attempt.terminal.seq == attempt.last_seq
            ):
                raise ResolutionError("Exact accepted winning attempt required")
            artifacts = attempt.terminal.data["artifacts"]
            indices = [a["output_index"] for a in artifacts]
            if len(set(indices)) != len(indices):
                raise ResolutionError("Duplicate artifact output index")
            matches = [a for a in artifacts if a["output_index"] == index]
            if len(matches) != 1 or not matches[0]["path"].startswith(
                "tmp/" + attempt.id + "/"
            ):
                raise ResolutionError("Winning output identity unavailable")
        elif kind in {"take", "asset"}:
            asset = window.assets.get(rid) if kind == "asset" else None
            take = window.takes.get(
                asset.subject_id if asset and asset.subject_type == "take" else rid
            )
            if not (
                take
                and take.owner_id == job.owner_id
                and take.song_id == job.song_id
                and not take.deleted_at
                and take.status == "ready"
            ):
                raise ResolutionError("Owned ready take required")
            if kind == "take":
                assets = window.take_assets.get((take.id, item["role"]), [])
                if len(assets) != 1:
                    raise ResolutionError("Unique ready asset required")
                asset = assets[0]
            if not (
                asset
                and asset.owner_id == job.owner_id
                and not asset.deleted_at
                and asset.subject_type == "take"
                and asset.role == item["role"]
            ):
                raise ResolutionError("Owned asset role required")
            if job.task == "audio.beats" and window.edges[job.id]:
                parent = next(
                    (
                        p
                        for e in window.edges[job.id]
                        if e.owner_id == job.owner_id
                        and (p := window.parents.get(e.depends_on_job_id)) is not None
                        and p.task == "post.audio"
                        and p.owner_id == job.owner_id
                        and p.song_id == job.song_id
                        and p.status == "succeeded"
                        and not p.deleted_at
                    ),
                    None,
                )
                if parent is None or not any(
                    x.get("ref") == {"type": "job", "id": take.job_id}
                    and x.get("output_index") == take.variant_index
                    for x in parent.request.get("inputs", [])
                ):
                    raise ResolutionError("Take must belong to successful post chain")
        elif kind != "upload":
            raise ResolutionError("Unsupported reference")


def references_available(job, session, *, window=None):
    try:
        validate_references(job, session, window=window)
        return True
    except ResolutionError:
        return False


def resolve_references(job, session, data_dir, *, verify=True):
    validate_references(job, session)
    return owned_inputs(job, session, data_dir, verify=verify)


def check_job_references(engine, job, data_dir):
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        # Resolver y stage_inputs verifican SHA antes del writer; no releer aquí.
        return resolve_references(job, session, data_dir, verify=False)
