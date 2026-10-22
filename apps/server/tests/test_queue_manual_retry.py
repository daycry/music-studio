"""Reintento lógico sistema §3 con índices globales y concurrencia SQLite real."""

import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor

import pytest
from app.models import Job, Take, new_id
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_queue_chains import create, request, services
from test_queue_chains import engine as _chain_engine

engine = _chain_engine


def failed(database, chain):
    with Session(database) as s:
        job = s.get(Job, chain.generation_job_id)
        job.status = "failed"
        job.error_code = "ORIGINAL_FAILURE"
        for i, tid in enumerate(chain.take_ids):
            s.get(Take, tid).status = (
                "failed" if i == 2 else "ready" if i == 0 else "cancelled"
            )
        s.commit()


def retry(database, owner, resolver, jid, **kwargs):
    from app.queue.manual_retry import ManualRetry

    return asyncio.run(ManualRetry(database, owner, resolver).retry(jid, **kwargs))


def test_queue_manual_retry_new_job_only_failed_original_index(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    failed(engine, chain)
    with Session(engine) as s:
        before = {
            t.id: copy.deepcopy(
                {c.name: getattr(t, c.name) for c in Take.__table__.columns}
            )
            for t in s.scalars(select(Take))
        }
    new = retry(engine, owner, resolver, chain.generation_job_id)
    assert new.take_ids == (chain.take_ids[2],)
    with Session(engine) as s:
        old = s.get(Job, chain.generation_job_id)
        job = s.get(Job, new.generation_job_id)
        assert old.status == "failed" and old.error_code == "ORIGINAL_FAILURE"
        assert job.id != old.id and job.request == old.request == request()
        assert (job.status, job.attempt, job.max_attempts) == ("queued", 0, 3)
        take = s.get(Take, new.take_ids[0])
        prior = before[take.id]
        assert (take.variant_index, take.seed, take.batch_id, take.root_id) == (
            2,
            19,
            prior["batch_id"],
            prior["root_id"],
        )
        assert take.status == "queued" and take.job_id == job.id
        post = s.get(Job, new.post_job_id)
        assert [x["output_index"] for x in post.request["inputs"]] == [2]
        assert len(new.beat_job_ids) == 1
        for tid in chain.take_ids[:2]:
            current = {
                c.name: getattr(s.get(Take, tid), c.name)
                for c in Take.__table__.columns
            }
            assert current == before[tid]
    assert retry(engine, owner, resolver, chain.generation_job_id) is None


def test_queue_manual_retry_two_connections_one_claim(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    failed(engine, chain)
    from app.db import create_db_engine

    other = create_db_engine(engine.url.database)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(retry, db, owner, resolver, chain.generation_job_id)
                for db in (engine, other)
            ]
            results = [f.result() for f in futures]
        assert sum(x is not None for x in results) == 1
        with Session(engine) as s:
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(Job.task == "music.instrumental")
                )
                == 2
            )
    finally:
        other.dispose()


@pytest.mark.parametrize(
    "bad",
    [
        "ready",
        "cancelled",
        "unrelated",
        "duplicate",
        "foreign_owner",
        "active_job",
        "mismatch_seed",
        "mismatch_index",
    ],
)
def test_queue_manual_retry_reject_selection_atomic(engine, bad):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    failed(engine, chain)
    ids = [chain.take_ids[2]]
    if bad == "ready":
        ids.append(chain.take_ids[0])
    if bad == "cancelled":
        ids.append(chain.take_ids[1])
    if bad == "unrelated":
        ids.append("01K70000000000000000000000")
    if bad == "duplicate":
        ids *= 2
    if bad == "foreign_owner":
        owner = new_id()
    with Session(engine) as s:
        if bad == "active_job":
            s.get(Job, chain.generation_job_id).status = "interrupted"
        if bad == "mismatch_seed":
            s.get(Take, ids[0]).seed = 55
        if bad == "mismatch_index":
            s.get(Take, ids[0]).variant_index = 9
        s.commit()
    with pytest.raises(ValueError):
        retry(engine, owner, resolver, chain.generation_job_id, take_ids=ids)
    with Session(engine) as s:
        assert s.get(Take, chain.take_ids[2]).job_id == chain.generation_job_id
        assert (
            s.scalar(
                select(func.count())
                .select_from(Job)
                .where(Job.task == "music.instrumental")
            )
            == 1
        )


def test_queue_manual_retry_rollback_midchain(engine, monkeypatch):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    failed(engine, chain)
    from app.queue import manual_retry

    real = manual_retry.add_dependents

    def fail(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError("own injected retry chain failure")

    monkeypatch.setattr(manual_retry, "add_dependents", fail)
    with pytest.raises(RuntimeError):
        retry(engine, owner, resolver, chain.generation_job_id)
    with Session(engine) as s:
        assert s.get(Take, chain.take_ids[2]).status == "failed"
        assert s.get(Take, chain.take_ids[2]).job_id == chain.generation_job_id
        assert s.scalar(select(func.count()).select_from(Job)) == 5


def test_queue_manual_retry_historical_attempt_and_extra_outputs_not_ready_assets(
    engine,
):
    from app.models import Asset, JobAttempt
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, _ = accepted(engine, chain, resolver, owner)
    # Legacy synthetic logical failure: failed() also marks the generator failed.
    # This proves attempt preservation, not a causal downstream T05 failure.
    # Authenticate the CPU failure explicitly; all historical assertions remain.
    own_post_failure(engine, chain)
    failed(engine, chain)
    with Session(engine) as s:
        old_attempt = s.get(JobAttempt, claim.attempt_id)
        before = old_attempt.terminal.model_dump(mode="json")
        body = old_attempt.engine_request.model_dump(mode="json")
        old_take = s.get(Take, chain.take_ids[0])
        master = old_take.id
        s.get(
            __import__("app.models", fromlist=["Song"]).Song, song
        ).master_take_id = master
        s.commit()
    new = retry(engine, owner, resolver, chain.generation_job_id)
    with Session(engine) as s:
        assert (
            s.get(JobAttempt, claim.attempt_id).terminal.model_dump(mode="json")
            == before
        )
        assert (
            s.get(JobAttempt, claim.attempt_id).engine_request.model_dump(mode="json")
            == body
        )
        assert s.scalar(select(func.count()).select_from(JobAttempt)) == 1
        assert s.get(Job, new.generation_job_id).request["n_outputs"] == 3
        assert (
            len(new.take_ids) == 1 and s.get(Take, new.take_ids[0]).variant_index == 2
        )
        assert s.get(Take, master).status == "ready"
        assert s.scalar(select(func.count()).select_from(Asset)) == 0


def test_queue_manual_retry_never_replaces_uncertain_prepared_attempt(engine):
    from app.models import JobAttempt
    from app.queue.admission import Admission

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    with Session(engine) as s:
        job = s.get(Job, chain.generation_job_id)
        s.expunge(job)
    resolved = asyncio.run(resolver.resolve(job, engine=engine))
    claim = Admission(
        engine, owner, synthetic_registry=resolver.synthetic_registry
    ).reserve(resolved)
    failed(engine, chain)
    # Fallo lógico inyectado no aporta un terminal durable al intento possibly-sent.
    with pytest.raises(ValueError):
        retry(engine, owner, resolver, chain.generation_job_id)
    with Session(engine) as s:
        assert s.get(JobAttempt, claim.attempt_id).status == "prepared"
        assert s.get(JobAttempt, claim.attempt_id).terminal is None
        assert s.get(Take, chain.take_ids[2]).job_id == chain.generation_job_id
        assert s.scalar(select(func.count()).select_from(Job)) == 5


def own_post_failure(database, chain):
    """Fallo durable del server CPU inyectado; no ejecuta producción T05."""
    with Session(database) as s:
        post = s.get(Job, chain.post_job_id)
        post.status = "failed"
        post.error_code = "POST_AUDIO_FAILURE"
        post.error = "synthetic own CPU failure"
        post.finished_at = "2026-10-08T07:01:00Z"
        for i, tid in enumerate(chain.take_ids):
            s.get(Take, tid).status = (
                "ready" if i == 0 else "cancelled" if i == 1 else "failed"
            )
        s.commit()


def test_queue_manual_retry_succeeded_generation_own_post_failure_native(engine):
    from app.models import JobAttempt, Song
    from sqlalchemy import text
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, _ = accepted(engine, chain, resolver, owner)
    own_post_failure(engine, chain)
    # Another generation's failed binding must remain untouched by this retry.
    foreign = create(engine, owner, song, resolver)
    failed(engine, foreign)
    with Session(engine) as s:
        assert s.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert (
            s.execute(text("SELECT version_num FROM alembic_version")).scalar()
            == "0007"
        )
        s.get(Song, song).master_take_id = chain.take_ids[0]
        s.commit()
        before_job = copy.deepcopy(
            {
                c.name: getattr(s.get(Job, chain.generation_job_id), c.name)
                for c in Job.__table__.columns
            }
        )
        before_attempt = {
            c.name: (
                getattr(s.get(JobAttempt, claim.attempt_id), c.name).model_dump(
                    mode="json"
                )
                if c.name in {"terminal", "engine_request", "load_options"}
                else getattr(s.get(JobAttempt, claim.attempt_id), c.name)
            )
            for c in JobAttempt.__table__.columns
        }
        untouched = {
            tid: copy.deepcopy(
                {
                    c.name: getattr(s.get(Take, tid), c.name)
                    for c in Take.__table__.columns
                }
            )
            for tid in (*chain.take_ids[:2], *foreign.take_ids)
        }
        assert before_job["status"] == "succeeded"
        assert before_attempt["terminal"]["type"] == "done"
    new = retry(engine, owner, resolver, chain.generation_job_id)
    assert new.take_ids == (chain.take_ids[2],)
    with Session(engine) as s:
        old = s.get(Job, chain.generation_job_id)
        assert {
            c.name: getattr(old, c.name) for c in Job.__table__.columns
        } == before_job
        assert {
            c.name: (
                getattr(s.get(JobAttempt, claim.attempt_id), c.name).model_dump(
                    mode="json"
                )
                if c.name in {"terminal", "engine_request", "load_options"}
                else getattr(s.get(JobAttempt, claim.attempt_id), c.name)
            )
            for c in JobAttempt.__table__.columns
        } == before_attempt
        job = s.get(Job, new.generation_job_id)
        assert job.id != old.id and job.request == old.request == request()
        assert (job.status, job.attempt, job.request["seed"]) == ("queued", 0, 17)
        take = s.get(Take, chain.take_ids[2])
        assert (take.status, take.job_id, take.variant_index, take.seed) == (
            "queued",
            job.id,
            2,
            19,
        )
        assert [
            x["output_index"] for x in s.get(Job, new.post_job_id).request["inputs"]
        ] == [2]
        for tid, original in untouched.items():
            assert {
                c.name: getattr(s.get(Take, tid), c.name)
                for c in Take.__table__.columns
            } == original
        assert s.get(Song, song).master_take_id == chain.take_ids[0]
    assert retry(engine, owner, resolver, chain.generation_job_id) is None


@pytest.mark.parametrize(
    "bad",
    [
        "no_post_failure",
        "missing_edge",
        "cancelled_post",
        "deleted_post",
        "wrong_post_task",
        "wrong_post_song",
        "missing_failure_code",
        "missing_finished",
        "wrong_bound_index",
        "duplicate_bound_index",
        "wrong_role",
        "wrong_parent",
        "extra_dependency",
        "unknown_ack",
        "deleted_attempt",
        "unknown_ordinal",
    ],
)
def test_queue_manual_retry_requires_authenticated_own_post_failure(engine, bad):
    from app.models import JobAttempt, JobDependency, Song
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, _ = accepted(engine, chain, resolver, owner)
    own_post_failure(engine, chain)
    with Session(engine) as s:
        post = s.get(Job, chain.post_job_id)
        if bad == "no_post_failure":
            post.status = "succeeded"
        if bad == "missing_edge":
            s.scalar(
                select(JobDependency).where(JobDependency.job_id == post.id)
            ).deleted_at = "2026-10-08T07:02:00Z"
        if bad == "cancelled_post":
            post.cancel_requested_at = "2026-10-08T07:02:00Z"
        if bad == "deleted_post":
            post.deleted_at = "2026-10-08T07:02:00Z"
        if bad == "wrong_post_task":
            post.task = "audio.beats"
        if bad == "wrong_post_song":
            other_song = Song(owner_id=owner, title="Other own song")
            s.add(other_song)
            s.flush()
            # Cross-song edges are forbidden even when tombstoned. Store a real
            # unrelated failure instead; it must not authorize these bindings.
            post.status = "succeeded"
            s.add(
                Job(
                    owner_id=owner,
                    song_id=other_song.id,
                    task="post.audio",
                    lane="cpu",
                    request={"inputs": []},
                    status="failed",
                    error_code="POST_AUDIO_FAILURE",
                    finished_at="2026-10-08T07:02:00Z",
                )
            )
        if bad == "missing_failure_code":
            post.error_code = None
        if bad == "missing_finished":
            post.finished_at = None
        if bad in {
            "wrong_bound_index",
            "duplicate_bound_index",
            "wrong_role",
            "wrong_parent",
        }:
            items = copy.deepcopy(post.request["inputs"])
            if bad == "wrong_bound_index":
                items = items[:2]
            if bad == "duplicate_bound_index":
                items.append(copy.deepcopy(items[2]))
            if bad == "wrong_role":
                items[2]["role"] = "other"
            if bad == "wrong_parent":
                items[2]["ref"]["id"] = post.id
            post.request = {"inputs": items}
        if bad == "extra_dependency":
            unrelated = Job(
                owner_id=owner,
                song_id=song,
                task="audio.beats",
                lane="cpu",
                request={},
                status="succeeded",
            )
            s.add(unrelated)
            s.flush()
            s.add(
                JobDependency(
                    owner_id=owner,
                    job_id=post.id,
                    depends_on_job_id=unrelated.id,
                )
            )
        if bad in {"unknown_ack", "deleted_attempt"}:
            s.get(JobAttempt, claim.attempt_id).deleted_at = "2026-10-08T07:02:00Z"
            if bad == "unknown_ack":
                # Reserve an actually uncertain successor, do not mutate frozen terminal.
                old = s.get(Job, chain.generation_job_id)
                old.attempt = 2
                previous = s.get(JobAttempt, claim.attempt_id)
                aid = new_id()
                body = previous.engine_request.model_dump(mode="json")
                body.update(job_id=aid, output_dir="tmp/" + aid)
                s.add(
                    JobAttempt(
                        id=aid,
                        owner_id=owner,
                        job_id=old.id,
                        ordinal=2,
                        engine_id=previous.engine_id,
                        model_id=previous.model_id,
                        mode=previous.mode,
                        engine_request=body,
                        load_options=previous.load_options.model_dump(mode="json"),
                    )
                )
        if bad == "unknown_ordinal":
            s.get(Job, chain.generation_job_id).attempt = 0
        s.commit()
    with pytest.raises(ValueError):
        retry(
            engine,
            owner,
            resolver,
            chain.generation_job_id,
            take_ids=[chain.take_ids[2]],
        )
    with Session(engine) as s:
        assert s.get(Job, chain.generation_job_id).status == "succeeded"
        assert s.get(Take, chain.take_ids[2]).job_id == chain.generation_job_id
        assert s.get(Take, chain.take_ids[2]).status == "failed"
        assert s.scalar(select(func.count()).select_from(Job)) == (
            6 if bad in {"extra_dependency", "wrong_post_song"} else 5
        )


def test_queue_manual_retry_filters_only_authenticated_failed_bindings(engine):
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    own_post_failure(engine, chain)
    with Session(engine) as s:
        s.get(Take, chain.take_ids[1]).status = "failed"
        post = s.get(Job, chain.post_job_id)
        post.request = {"inputs": [post.request["inputs"][2]]}
        s.commit()
    new = retry(engine, owner, resolver, chain.generation_job_id)
    assert new.take_ids == (chain.take_ids[2],)
    with Session(engine) as s:
        assert s.get(Take, chain.take_ids[1]).status == "failed"
        assert s.get(Take, chain.take_ids[1]).job_id == chain.generation_job_id
    with pytest.raises(ValueError):
        retry(
            engine,
            owner,
            resolver,
            chain.generation_job_id,
            take_ids=[chain.take_ids[1]],
        )


def test_queue_manual_retry_revalidates_post_failure_under_writer(engine):
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    accepted(engine, chain, resolver, owner)
    own_post_failure(engine, chain)
    real = resolver.resolve

    async def revoke(*args, **kwargs):
        result = await real(*args, **kwargs)
        with Session(engine) as s:
            s.get(Job, chain.post_job_id).cancel_requested_at = "2026-10-08T07:03:00Z"
            s.commit()
        return result

    resolver.resolve = revoke
    with pytest.raises(ValueError):
        retry(engine, owner, resolver, chain.generation_job_id)
    with Session(engine) as s:
        assert s.get(Take, chain.take_ids[2]).job_id == chain.generation_job_id
        assert s.get(Job, chain.generation_job_id).status == "succeeded"
        assert s.scalar(select(func.count()).select_from(Job)) == 5


def test_queue_manual_retry_failed_logical_done_cannot_skip_post_authentication(engine):
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    claim, _ = accepted(engine, chain, resolver, owner)
    failed(engine, chain)
    # Caller-marked logical/take status does not authenticate a CPU failure.
    with pytest.raises(ValueError, match="downstream failure"):
        retry(engine, owner, resolver, chain.generation_job_id)
    with Session(engine) as s:
        from app.models import JobAttempt

        assert s.get(JobAttempt, claim.attempt_id).terminal.type == "done"
        assert s.get(Take, chain.take_ids[2]).job_id == chain.generation_job_id
        assert s.scalar(select(func.count()).select_from(Job)) == 5
