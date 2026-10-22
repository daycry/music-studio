"""Referencias U3: terminal aceptado real; completion CPU inyectada T05."""

import asyncio
import hashlib

import pytest
from app.models import Asset, Job, Take
from app.queue.admission import Admission
from app.queue.events import EventBus, EventConsumer
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_queue_chains import create, services
from test_queue_chains import engine as _chain_engine

engine = _chain_engine


def accepted(database, chain, resolver, owner, *, artifact_mutator=None):
    with Session(database) as s:
        job = s.get(Job, chain.generation_job_id)
        s.expunge(job)
    resolved = asyncio.run(resolver.resolve(job, engine=database))
    from synthetic_composition import capture

    admission = Admission(
        database, owner, synthetic_registry=resolver.synthetic_registry
    )
    claim = admission.reserve(resolved)
    capture(admission, claim, resolved.backend)
    artifacts = []
    root = resolver.data_dir
    for i in range(3):
        path = root / "tmp" / claim.attempt_id / f"{i}.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"synthetic-{i}".encode())
        artifacts.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "media_type": "audio/wav",
                "output_index": i,
            }
        )
    if artifact_mutator is not None:
        artifact_mutator(artifacts)
    EventConsumer(database, owner, EventBus()).accept(
        claim.attempt_id,
        "mock",
        {
            "job_id": claim.attempt_id,
            "seq": 1,
            "ts": "2026-10-08T07:00:00Z",
            "type": "done",
            "data": {
                "artifacts": artifacts,
                "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
            },
        },
    )
    return claim, artifacts


def test_queue_admission_unblocks_only_available_dependencies(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    admission = Admission(engine, owner)
    assert admission.select(chain.post_job_id).id == chain.post_job_id
    assert admission.select(chain.beat_job_ids[0]) is None
    with Session(engine) as s:
        assert (
            s.get(Job, chain.post_job_id).request["inputs"][0]["ref"]["type"] == "job"
        )


def test_queue_references_winning_attempt_delegate_bytes(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, artifacts = accepted(engine, chain, resolver, owner)
    from app.queue.references import resolve_references

    with Session(engine) as s:
        post = s.get(Job, chain.post_job_id)
        wires = resolve_references(post, s, resolver.data_dir)
        assert [w["path"] for w in wires] == [a["path"] for a in artifacts]
        assert all(claim.attempt_id in w["path"] for w in wires)
        assert post.request["inputs"][0]["ref"]["id"] == chain.generation_job_id


@pytest.mark.parametrize(
    "bad",
    [
        "changed_bytes",
        "missing",
        "duplicate_index",
        "wrong_index",
        "wrong_path",
        "missing_edge",
        "wrong_song",
        "unknown_attempt",
        "hardlink",
    ],
)
def test_queue_references_reject_before_reserve(engine, bad):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)

    def mutate(artifacts):
        if bad == "duplicate_index":
            artifacts.append(dict(artifacts[0]))
        if bad == "wrong_index":
            artifacts[0]["output_index"] = 9
        if bad == "wrong_path":
            artifacts[0]["path"] = "tmp/01K70000000000000000000000/0.wav"

    _claim, artifacts = accepted(
        engine, chain, resolver, owner, artifact_mutator=mutate
    )
    import os

    from app.models import JobDependency
    from app.queue.references import resolve_references

    path = resolver.data_dir / artifacts[0]["path"]
    if bad == "changed_bytes":
        path.write_bytes(b"changed")
    if bad == "missing":
        path.unlink()
    if bad == "hardlink":
        os.link(path, path.with_suffix(".alias"))
    with Session(engine) as s:
        post = s.get(Job, chain.post_job_id)
        if bad == "missing_edge":
            edge = s.scalar(
                select(JobDependency).where(JobDependency.job_id == post.id)
            )
            edge.deleted_at = "2026-10-08T07:01:00Z"
            s.flush()
        if bad == "wrong_song":
            post.song_id = "01K70000000000000000000000"
        if bad == "unknown_attempt":
            s.get(Job, chain.generation_job_id).attempt = 2
        with s.no_autoflush, pytest.raises(ValueError):
            resolve_references(post, s, resolver.data_dir)


def test_queue_t05_completion_injection_beats_cpu_no_gpu_unload(engine):
    """T05 injection: own ready assets only; no real FFmpeg/manifest evidence."""
    owner, song, catalog, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    # Reinicio declarado del backend al preparar la completion CPU inyectada.
    catalog.loaded = None
    with Session(engine) as s:
        s.get(Job, chain.post_job_id).status = "succeeded"
        for tid in chain.take_ids:
            take = s.get(Take, tid)
            take.status = "ready"
            path = resolver.data_dir / "masters" / f"{tid}.flac"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"T05 injection synthetic")
            s.add(
                Asset(
                    owner_id=owner,
                    subject_type="take",
                    subject_id=tid,
                    role="master",
                    path=path.relative_to(resolver.data_dir).as_posix(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    media_type="audio/flac",
                    bytes=path.stat().st_size,
                )
            )
        s.commit()
    from app.queue.backends.protocol import Submission
    from app.queue.dispatcher import Dispatcher

    calls = []

    async def submit(body):
        calls.append(("submit", body))
        return Submission(job_id=body.job_id)

    async def unload():
        raise AssertionError("CPU must not unload GPU")

    catalog.submit = submit
    catalog.unload = unload
    dispatcher = Dispatcher(Admission(engine, owner), resolver)

    async def run():
        try:
            return await dispatcher.dispatch(chain.beat_job_ids[0])
        finally:
            await dispatcher.close()

    claim = asyncio.run(run())
    assert claim is not None and claim.request.task == "audio.beats"
    assert claim.request.inputs[0].role == "master" and calls[0][0] == "submit"


@pytest.mark.parametrize("terminal", ["failed", "cancelled"])
def test_queue_failed_parent_propagates_chain(engine, terminal):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    with Session(engine) as s:
        s.get(Job, chain.generation_job_id).status = terminal
        s.commit()
    admission = Admission(engine, owner)
    assert admission.select(chain.post_job_id) is None
    assert admission.select(chain.beat_job_ids[0]) is None
    with Session(engine) as s:
        assert s.get(Job, chain.post_job_id).error_code == "DEPENDENCY_FAILED"
        assert s.get(Job, chain.beat_job_ids[0]).error_code == "DEPENDENCY_FAILED"


def ready_beats(database, chain, resolver, owner, count):
    """Estado CPU sintético propio, relaciones y consultas SQLite reales."""
    from app.models import JobDependency

    with Session(database) as s:
        s.get(Job, chain.post_job_id).status = "succeeded"
        for tid in chain.take_ids:
            take = s.get(Take, tid)
            take.status = "ready"
            path = resolver.data_dir / "masters" / f"{tid}.flac"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"own synthetic master")
            s.add(
                Asset(
                    owner_id=owner,
                    subject_type="take",
                    subject_id=tid,
                    role="master",
                    path=path.relative_to(resolver.data_dir).as_posix(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    media_type="audio/flac",
                    bytes=path.stat().st_size,
                )
            )
        # Repeated analyses of existing ready takes are independent logical jobs.
        for i in range(count - len(chain.beat_job_ids)):
            beat = Job(
                owner_id=owner,
                song_id=s.get(Job, chain.post_job_id).song_id,
                task="audio.beats",
                lane="cpu",
                status="blocked",
                request={
                    "params": {},
                    "inputs": [
                        {
                            "role": "master",
                            "ref": {
                                "type": "take",
                                "id": chain.take_ids[i % len(chain.take_ids)],
                            },
                        }
                    ],
                },
            )
            s.add(beat)
            s.flush()
            s.add(
                JobDependency(
                    owner_id=owner, job_id=beat.id, depends_on_job_id=chain.post_job_id
                )
            )
        s.commit()


def count_sql(database, call, label):
    """Native cursor witness, retained outside product code; no timing claim."""
    import json
    import os
    from datetime import datetime, timezone
    from pathlib import Path

    from sqlalchemy import event

    queries = []

    def observe(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(database, "before_cursor_execute", observe)
    try:
        result = call()
    finally:
        event.remove(database, "before_cursor_execute", observe)
        phase = Path(os.environ["STUDIO_TEST_ROOT"]).parent
        record = {
            "label": label,
            "utc": datetime.now(timezone.utc).isoformat(),
            "select_count": len(queries),
            "statements": queries,
            "sources": {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (
                    Path("apps/server/app/queue/references.py"),
                    Path("apps/server/app/queue/admission.py"),
                )
            },
        }
        with (phase / "native-query-counts.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps(record) + "\n")
    return result, queries


def test_queue_references_400_ready_beats_native_query_bound(engine):
    from sqlalchemy import inspect

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    ready_beats(engine, chain, resolver, owner, 400)
    pages, queries = count_sql(
        engine,
        lambda: list(Admission(engine, owner).candidate_batches()),
        "400-ready-beats",
    )
    assert [len(page) for page in pages] == [400]
    assert all(
        j.task == "audio.beats" and j.status == "queued" and inspect(j).detached
        for j in pages[0]
    )
    assert len(queries) <= 16, len(queries)


def test_queue_references_shared_64_post_inputs_native_query_bound(engine):
    from app.queue.references import validate_references
    from test_queue_chains import request

    owner, song, catalog, resolver = services(engine)
    catalog.value["tasks"]["music.instrumental"]["limits"]["n_outputs"] = 64
    chain = create(engine, owner, song, resolver, request=request(64))

    def extra_outputs(artifacts):
        for i in range(3, 64):
            artifacts.append({**artifacts[0], "output_index": i})

    accepted(engine, chain, resolver, owner, artifact_mutator=extra_outputs)

    def validate():
        with Session(engine) as s, s.begin():
            from app.queue.admission import writer

            writer(s)
            post = s.get(Job, chain.post_job_id)
            validate_references(post, s)
            return len(post.request["inputs"])

    size, queries = count_sql(engine, validate, "64-shared-post-inputs")
    assert size == 64
    assert len(queries) <= 8, len(queries)


def test_queue_references_finite_801_ready_beats_detached(engine):
    from sqlalchemy import inspect

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    ready_beats(engine, chain, resolver, owner, 801)
    pages = Admission(engine, owner).candidate_batches()
    try:
        first = next(pages)
        with Session(engine) as s:
            late = Job(
                owner_id=owner,
                song_id=song,
                task="audio.beats",
                lane="cpu",
                request={},
                created_at="2020-01-01T00:00:00Z",
            )
            s.add(late)
            s.commit()
            late_id = late.id
        remaining = list(pages)
        all_pages = [first, *remaining]
        assert [len(page) for page in all_pages] == [400, 400, 1]
        jobs = [job for page in all_pages for job in page]
        assert len({j.id for j in jobs}) == 801 and late_id not in {j.id for j in jobs}
        assert all(inspect(j).detached for j in jobs)
    finally:
        pages.close()


@pytest.mark.parametrize(
    "bad",
    [
        "asset_ref",
        "duplicate_asset",
        "deleted_take",
        "deleted_asset",
        "wrong_role",
        "duplicate_ref",
        "bad_item",
        "bad_identity",
        "bad_type",
        "unknown_kind",
        "missing_post_binding",
    ],
)
def test_queue_references_preloaded_native_identities_remain_authoritative(engine, bad):
    from app.queue.references import preload_references, validate_references

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    ready_beats(engine, chain, resolver, owner, 3)
    with Session(engine) as s:
        beat = s.get(Job, chain.beat_job_ids[0])
        asset = s.scalar(select(Asset).where(Asset.subject_id == chain.take_ids[0]))
        if bad == "asset_ref":
            beat.request = {
                "inputs": [{"role": "master", "ref": {"type": "asset", "id": asset.id}}]
            }
        if bad == "duplicate_asset":
            s.add(
                Asset(
                    owner_id=owner,
                    subject_type="take",
                    subject_id=asset.subject_id,
                    role=asset.role,
                    path=asset.path,
                    sha256=asset.sha256,
                    media_type=asset.media_type,
                    bytes=asset.bytes,
                )
            )
        if bad == "deleted_take":
            s.get(Take, chain.take_ids[0]).deleted_at = "2026-10-08T07:02:00Z"
        if bad == "deleted_asset":
            asset.deleted_at = "2026-10-08T07:02:00Z"
        if bad == "wrong_role":
            asset.role = "other"
        if bad == "duplicate_ref":
            beat.request = {"inputs": [beat.request["inputs"][0]] * 2}
        if bad == "bad_item":
            beat.request = {"inputs": ["invalid"]}
        if bad == "bad_identity":
            beat.request = {"inputs": [{"role": "master", "ref": {"type": "take"}}]}
        if bad == "bad_type":
            beat.request = {
                "inputs": [{"role": "master", "ref": {"type": "take", "id": 7}}]
            }
        if bad == "unknown_kind":
            beat.request = {
                "inputs": [
                    {
                        "role": "master",
                        "ref": {"type": "other", "id": chain.take_ids[0]},
                    }
                ]
            }
        if bad == "missing_post_binding":
            s.get(Job, chain.post_job_id).request = {"inputs": []}
        s.commit()
    with Session(engine) as s, s.begin():
        beat = s.get(Job, chain.beat_job_ids[0])
        window = preload_references(s, [beat])
        if bad == "asset_ref":
            validate_references(beat, s, window=window)
        else:
            with pytest.raises(ValueError):
                validate_references(beat, s, window=window)


def test_queue_references_window_never_trusted_across_transactions_or_polls(engine):
    from app.queue.references import preload_references, validate_references

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    ready_beats(engine, chain, resolver, owner, 3)
    with Session(engine) as s:
        beat = s.get(Job, chain.beat_job_ids[0])
        window = preload_references(s, [beat])
        validate_references(beat, s, window=window)
        s.commit()
        with pytest.raises(ValueError):
            validate_references(beat, s, window=window)
    with Session(engine) as other:
        beat = other.get(Job, chain.beat_job_ids[0])
        with pytest.raises(ValueError):
            validate_references(beat, other, window=window)
        other.get(Take, chain.take_ids[0]).status = "failed"
        other.commit()
    assert Admission(engine, owner).candidates(chain.beat_job_ids[0]) == []
    with Session(engine) as s:
        beat = s.get(Job, chain.beat_job_ids[0])
        with pytest.raises(ValueError):
            validate_references(beat, s)
