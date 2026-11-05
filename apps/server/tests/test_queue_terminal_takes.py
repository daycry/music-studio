"""Terminales reales de la cola sobre placeholders creados por GenerationChains."""

import asyncio
import copy

import pytest
from app.models import Asset, Job, JobAttempt, PublicationIntent, Song, Take, new_id
from app.publication import PublicationCoordinator
from app.queue.admission import Admission
from app.queue.cancellation import Cancellation
from app.queue.events import EventBus, EventConsumer
from app.queue.retry import Retry
from sqlalchemy.orm import Session
from test_dispatcher_recovery import event
from test_queue_chains import create, request, services
from test_queue_chains import engine as engine  # noqa: PLC0414
from test_queue_manual_retry import retry as manual_retry


@pytest.mark.parametrize(
    "scenario",
    [
        "no_offload",
        "already_offload",
        "offload",
        "provider",
        "busy",
        "low_vram",
        "backoff",
        "exhausted",
        "removed_model",
        "changed_identity",
    ],
)
@pytest.mark.parametrize("captured", [False, True])
def test_runtime_and_admission_finish_impossible_vram_retry(engine, scenario, captured):
    from app.queue.resolver import Resolver
    from app.queue.runtime import QueueRuntime
    from synthetic_composition import capture, chain_recipes
    from test_dispatcher_recovery import RecordedBackend, settings

    owner, song, _, _ = services(engine)
    recipe = chain_recipes()[0]
    if scenario != "no_offload":
        recipe["modes"].append({"id": "offload", "vram_mb": 500, "notes": "synthetic"})

    class Backend(RecordedBackend):
        retry_state = None
        observations = 0

        async def health(self):
            health = await super().health()
            self.observations += 1
            if self.retry_state == "busy":
                return health.model_copy(update={"state": "busy"})
            if self.retry_state == "low_vram":
                return health.model_copy(
                    update={"gpu": health.gpu.model_copy(update={"free_mb": 1})}
                )
            if self.retry_state == "changed_identity" and self.observations % 2 == 0:
                return health.model_copy(update={"image_digest": "changed"})
            return health

    backend = Backend(recipes=[recipe])
    backend.value = recipe
    resolver = Resolver(
        {"mock": backend},
        data_dir=settings().data_dir,
        synthetic_registry=backend.synthetic_registry,
    )
    body = request(n=2)
    if scenario == "already_offload":
        body["mode"] = "offload"
    chain = create(engine, owner, song, resolver, request=body)
    admission = Admission(engine, owner, synthetic_registry=backend.synthetic_registry)
    claim = admission.reserve(
        asyncio.run(resolver.resolve(admission.select(chain.generation_job_id)))
    )
    if captured:
        capture(admission, claim, backend)
    before_request = claim.request.model_dump(mode="json")
    code = "INTERNAL" if scenario == "provider" else "VRAM_EXCEEDED"
    if scenario in {"backoff", "exhausted"}:
        with Session(engine) as session, session.begin():
            job = session.get(Job, chain.generation_job_id)
            if scenario == "backoff":
                job.not_before = "2099-01-01T00:00:00Z"
            else:
                job.max_attempts = 1
    consumer = EventConsumer(engine, owner, EventBus())
    assert consumer.accept(
        claim.attempt_id,
        "mock",
        event(
            claim.attempt_id,
            "error",
            {
                "code": code,
                "message": "synthetic",
                "retryable": True,
            },
        ),
    )
    backend.loaded = None
    backend.retry_state = scenario
    backend.observations = 0
    if scenario == "removed_model":
        backend.value = {**recipe, "id": "removed"}
    with Session(engine) as session:
        old = session.get(JobAttempt, claim.attempt_id)
        before_attempt = {
            c.name: getattr(old, c.name) for c in JobAttempt.__table__.columns
        }
        before_takes = {
            tid: {
                c.name: getattr(session.get(Take, tid), c.name)
                for c in Take.__table__.columns
            }
            for tid in chain.take_ids
        }

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
            cpu_service=object(),
        )
        await runtime.start()
        runtime.task.cancel()
        await asyncio.gather(runtime.task, return_exceptions=True)
        old_epoch = runtime.bus.epoch
        try:
            for _ in range(3):
                await runtime.dbcall(runtime.admission.candidates)
                await runtime._retry()
            with Session(engine) as session:
                job = session.get(Job, chain.generation_job_id)
                old = session.get(JobAttempt, claim.attempt_id)
                assert old.engine_request.model_dump(mode="json") == before_request
                assert {
                    c.name: getattr(old, c.name) for c in JobAttempt.__table__.columns
                } == before_attempt
                assert job.request == body
                definitive = scenario in {"no_offload", "already_offload", "exhausted"}
                submitted = scenario in {"offload", "provider"}
                assert (
                    (job.status, job.attempt) == ("running", 2)
                    if submitted
                    else (job.status, job.attempt) == ("failed", 1)
                )
                assert job.max_attempts == (1 if definitive else 3)
                assert session.get(Job, chain.post_job_id).status == (
                    "failed" if definitive else "blocked"
                )
                assert [
                    (
                        session.get(Take, tid).status,
                        session.get(Take, tid).seed,
                        session.get(Take, tid).variant_index,
                    )
                    for tid in chain.take_ids
                ] == [
                    ("failed" if definitive else "queued", 17, 0),
                    ("failed" if definitive else "queued", 18, 1),
                ]
                for tid in chain.take_ids:
                    take = session.get(Take, tid)
                    for key, value in before_takes[tid].items():
                        if key not in {"status", "updated_at", "error_code"}:
                            assert getattr(take, key) == value
                assert len(backend.posts) == (1 if submitted else 0)
                if submitted:
                    sent = backend.posts[0]
                    assert (sent.seed, sent.params, sent.n_outputs) == (
                        17,
                        body["params"],
                        2,
                    )
                    assert sent.mode == (
                        "bf16" if scenario == "provider" else "offload"
                    )
                if scenario in {"no_offload", "already_offload"}:
                    assert runtime.bus.epoch != old_epoch
                else:
                    assert runtime.bus.epoch == old_epoch
        finally:
            await runtime.close()

    asyncio.run(run())
    if scenario in {"no_offload", "already_offload", "exhausted"}:
        retried = manual_retry(engine, owner, resolver, chain.generation_job_id)
        assert retried.take_ids == chain.take_ids
        with Session(engine) as session:
            child = session.get(Job, retried.generation_job_id)
            assert (child.status, child.attempt, child.max_attempts) == ("queued", 0, 3)
            assert all(
                session.get(Take, tid).status == "queued" for tid in chain.take_ids
            )


def prepared_chain(database, lane="gpu"):
    owner, song, catalog, resolver = services(database)
    if lane == "cpu":
        catalog.value["tasks"]["music.instrumental"]["lane"] = "cpu"
    chain = create(database, owner, song, resolver, request=request(n=2))
    admission = Admission(
        database, owner, synthetic_registry=catalog.synthetic_registry
    )
    resolved = asyncio.run(resolver.resolve(admission.select(chain.generation_job_id)))
    claim = admission.reserve(resolved)
    assert claim is not None
    return owner, resolver, chain, admission, claim


def fail(database, owner, claim, *, retryable=False, code="INTERNAL"):
    consumer = EventConsumer(database, owner, EventBus())
    assert consumer.accept(
        claim.attempt_id,
        "mock",
        event(
            claim.attempt_id,
            "error",
            {
                "code": code,
                "message": "fallo controlado",
                "retryable": retryable,
            },
        ),
    )


@pytest.mark.parametrize(
    "change",
    ["cancel", "budget", "request", "deleted_song", "engine", "model", "ordinal"],
)
def test_impossible_vram_close_cas_preserves_changed_authority(engine, change):
    from app.publication import PublicationCoordinator

    owner, _, chain, _, claim = prepared_chain(engine)
    fail(engine, owner, claim, retryable=True, code="VRAM_EXCEEDED")
    bus = EventBus()
    service = Retry(engine, owner, coordinator=PublicationCoordinator(), bus=bus)
    source, previous = next(service.candidates())
    if change in {"engine", "model"}:
        setattr(previous, change + "_id", "changed")
    elif change == "ordinal":
        source.attempt = 2
    else:
        with Session(engine) as session, session.begin():
            job = session.get(Job, chain.generation_job_id)
            if change == "cancel":
                job.cancel_requested_at = "2026-11-05T00:00:00Z"
            elif change == "budget":
                job.max_attempts = 1
            elif change == "request":
                job.request = {**job.request, "seed": 99}
            else:
                session.get(Song, job.song_id).deleted_at = "2026-11-05T00:00:00Z"
    with Session(engine) as session:
        before = {
            c.name: getattr(session.get(Job, chain.generation_job_id), c.name)
            for c in Job.__table__.columns
        }
    epoch = bus.epoch
    assert not service.close_impossible_vram(source, previous)
    assert bus.epoch == epoch
    with Session(engine) as session:
        assert {
            c.name: getattr(session.get(Job, chain.generation_job_id), c.name)
            for c in Job.__table__.columns
        } == before
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)


@pytest.mark.parametrize("coordinated", [False, True])
def test_impossible_vram_close_rollback_preserves_budget_placeholders_and_feed(
    engine, monkeypatch, coordinated
):
    from app.publication import PublicationCoordinator
    from app.queue import retry

    owner, _, chain, _, claim = prepared_chain(engine)
    fail(engine, owner, claim, retryable=True, code="VRAM_EXCEEDED")
    bus = EventBus()
    service = Retry(
        engine,
        owner,
        coordinator=PublicationCoordinator() if coordinated else None,
        bus=bus if coordinated else None,
    )
    source, previous = next(service.candidates())
    original = retry.terminalize_placeholders

    def reject(*args):
        original(*args)
        raise RuntimeError("injected after terminalization before commit")

    monkeypatch.setattr(retry, "terminalize_placeholders", reject)
    epoch = bus.epoch
    with pytest.raises(RuntimeError, match="injected after terminalization"):
        service.close_impossible_vram(source, previous)
    assert bus.epoch == epoch
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).max_attempts == 3
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)


def test_impossible_vram_legacy_close_and_replay_are_durable(engine):
    owner, _, chain, _, claim = prepared_chain(engine)
    fail(engine, owner, claim, retryable=True, code="VRAM_EXCEEDED")
    service = Retry(engine, owner)
    source, previous = next(service.candidates())
    assert service.close_impossible_vram(source, previous)
    assert not service.close_impossible_vram(source, previous)
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).max_attempts == 1
        assert all(session.get(Take, tid).status == "failed" for tid in chain.take_ids)


def test_impossible_vram_uncertain_commit_keeps_durable_rows_and_invalidates(engine):
    from app.publication import PublicationCoordinator
    from sqlalchemy import event as sql_event

    owner, _, chain, _, claim = prepared_chain(engine)
    fail(engine, owner, claim, retryable=True, code="VRAM_EXCEEDED")
    bus = EventBus()
    service = Retry(engine, owner, coordinator=PublicationCoordinator(), bus=bus)
    source, previous = next(service.candidates())
    primary = RuntimeError("injected after actual commit")

    def committed(session):
        if session.bind is engine:
            raise primary

    sql_event.listen(Session, "after_commit", committed)
    epoch = bus.epoch
    try:
        with pytest.raises(RuntimeError) as caught:
            service.close_impossible_vram(source, previous)
        assert caught.value is primary
    finally:
        sql_event.remove(Session, "after_commit", committed)
    assert bus.epoch != epoch
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).max_attempts == 1
        assert all(session.get(Take, tid).status == "failed" for tid in chain.take_ids)


@pytest.mark.parametrize(
    "coordinator,bus",
    [
        (object(), EventBus()),
        (None, EventBus()),
        (PublicationCoordinator(), None),
    ],
)
def test_retry_rejects_partial_publication_composition(engine, coordinator, bus):
    with pytest.raises(TypeError, match="shared coordinator"):
        Retry(engine, "owner", coordinator=coordinator, bus=bus)


@pytest.mark.parametrize("lane", ["gpu", "cpu"])
def test_definitive_error_terminalizes_created_placeholders_and_manual_retry(
    engine, lane
):
    owner, resolver, chain, admission, claim = prepared_chain(engine, lane)
    with Session(engine) as session:
        before = {
            tid: copy.deepcopy(
                {
                    c.name: getattr(session.get(Take, tid), c.name)
                    for c in Take.__table__.columns
                }
            )
            for tid in chain.take_ids
        }
    fail(engine, owner, claim)
    admission.candidates()
    with Session(engine) as session:
        assert session.get(Job, chain.post_job_id).error_code == "DEPENDENCY_FAILED"
        for tid in chain.take_ids:
            take = session.get(Take, tid)
            assert (take.status, take.error_code) == ("failed", "INTERNAL")
            for key in (
                "params",
                "seed",
                "variant_index",
                "batch_id",
                "job_id",
                "root_id",
            ):
                assert getattr(take, key) == before[tid][key]
    retried = manual_retry(engine, owner, resolver, chain.generation_job_id)
    assert retried.take_ids == chain.take_ids
    with Session(engine) as session:
        assert all(
            session.get(Take, tid).job_id == retried.generation_job_id
            for tid in chain.take_ids
        )


@pytest.mark.parametrize("claimed", [False, True])
def test_confirmed_cancellation_terminalizes_created_placeholders(engine, claimed):
    owner, song, catalog, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    admission = Admission(engine, owner, synthetic_registry=catalog.synthetic_registry)
    claim = None
    if claimed:
        claim = admission.reserve(
            asyncio.run(resolver.resolve(admission.select(chain.generation_job_id)))
        )
    assert Cancellation(engine, owner).request(chain.generation_job_id)
    if claimed:
        with Session(engine) as session:
            assert all(
                session.get(Take, tid).status == "queued" for tid in chain.take_ids
            )
        consumer = EventConsumer(engine, owner, EventBus())
        assert consumer.accept(
            claim.attempt_id,
            "mock",
            event(
                claim.attempt_id,
                "cancelled",
                {"telemetry": {"mode": "bf16", "model_revision": "synthetic"}},
            ),
        )
    admission.candidates()
    with Session(engine) as session:
        assert all(
            session.get(Take, tid).status == "cancelled" for tid in chain.take_ids
        )


@pytest.mark.parametrize("lane", ["gpu", "cpu"])
def test_retry_interleaved_with_admission_preserves_placeholders_until_exhaustion(
    engine, lane
):
    owner, resolver, chain, admission, claim = prepared_chain(engine, lane)
    retry = Retry(engine, owner)
    for ordinal in (1, 2, 3):
        fail(engine, owner, claim, retryable=True)
        # Admission corre ANTES de Retry.reserve: no puede matar el post transitorio.
        admission.candidates()
        with Session(engine) as session:
            job = session.get(Job, chain.generation_job_id)
            previous = session.get(JobAttempt, claim.attempt_id)
            assert previous.ordinal == ordinal
            if ordinal == 3:
                assert session.get(Job, chain.post_job_id).status == "failed"
                assert all(
                    (session.get(Take, tid).status, session.get(Take, tid).error_code)
                    == ("failed", "INTERNAL")
                    for tid in chain.take_ids
                )
                break
            assert session.get(Job, chain.post_job_id).status == "blocked"
            assert all(
                session.get(Take, tid).status == "queued" for tid in chain.take_ids
            )
            frozen = retry.frozen_job(job, previous, previous.mode)
        resolved = asyncio.run(resolver.resolve(frozen))
        claim = retry.reserve(chain.generation_job_id, previous.id, resolved)
        assert claim is not None and claim.request.seed == 17
        admission.candidates()
        with Session(engine) as session:
            assert session.get(Job, chain.post_job_id).status == "blocked"


@pytest.mark.parametrize(
    "guard",
    [
        "ready",
        "failed",
        "cancelled",
        "asset",
        "intent",
        "deleted",
        "song",
        "job",
        "index",
        "seed",
        "params",
        "model",
        "task",
    ],
)
def test_terminal_does_not_change_other_or_published_variants(engine, guard):
    owner, resolver, chain, _, claim = prepared_chain(engine)
    protected = chain.take_ids[1]
    if guard == "song":
        with Session(engine) as session, session.begin():
            song = Song(id=new_id(), owner_id=owner, title="Otra canción")
            session.add(song)
            other_song = song.id
        protected = create(engine, owner, other_song, resolver).take_ids[0]
    with Session(engine) as session, session.begin():
        take = session.get(Take, protected)
        if guard in {"ready", "failed", "cancelled"}:
            take.status = guard
        elif guard == "asset":
            session.add(
                Asset(
                    owner_id=owner,
                    subject_type="take",
                    subject_id=take.id,
                    role="audio_master",
                    path="songs/test/takes/test/master.wav",
                    media_type="audio/wav",
                    sha256="a" * 64,
                    bytes=1,
                )
            )
        elif guard == "intent":
            session.add(
                PublicationIntent(
                    owner_id=owner,
                    song_id=take.song_id,
                    take_id=take.id,
                    output_index=take.variant_index,
                    seed=take.seed,
                )
            )
        elif guard == "deleted":
            take.deleted_at = "2026-10-08T00:00:00Z"
        elif guard == "job":
            take.job_id = chain.post_job_id
        elif guard == "index":
            take.variant_index = 9
        elif guard == "seed":
            take.seed = 800
        elif guard == "params":
            take.params = {"style": "different"}
        elif guard == "model":
            take.model_id = "another-model"
        elif guard == "task":
            take.task = "music.song"
    with Session(engine) as session:
        before = copy.deepcopy(
            {
                c.name: getattr(session.get(Take, protected), c.name)
                for c in Take.__table__.columns
            }
        )
    fail(engine, owner, claim)
    with Session(engine) as session:
        assert session.get(Take, chain.take_ids[0]).status == "failed"
        assert {
            c.name: getattr(session.get(Take, protected), c.name)
            for c in Take.__table__.columns
        } == before


def test_retry_backoff_is_not_definitive(engine):
    owner, _, chain, admission, claim = prepared_chain(engine)
    fail(engine, owner, claim, retryable=True)
    with Session(engine) as session, session.begin():
        session.get(Job, chain.generation_job_id).not_before = "2099-01-01T00:00:00Z"
    admission.candidates()
    with Session(engine) as session:
        assert session.get(Job, chain.post_job_id).status == "blocked"
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)


def test_successful_generation_waits_for_post_without_terminalizing_take(engine):
    owner, _, chain, _, claim = prepared_chain(engine)
    consumer = EventConsumer(engine, owner, EventBus())
    assert consumer.accept(
        claim.attempt_id,
        "mock",
        event(
            claim.attempt_id,
            "done",
            {
                "artifacts": [],
                "result": {},
                "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
            },
        ),
    )
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).status == "succeeded"
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)


def test_terminal_generation_preserves_uint64_variant_seeds(engine):
    owner, song, catalog, resolver = services(engine)
    chain = create(engine, owner, song, resolver, request=request(n=2, seed=2**64 - 2))
    admission = Admission(engine, owner, synthetic_registry=catalog.synthetic_registry)
    claim = admission.reserve(
        asyncio.run(resolver.resolve(admission.select(chain.generation_job_id)))
    )
    fail(engine, owner, claim)
    with Session(engine) as session:
        assert [
            (session.get(Take, tid).status, session.get(Take, tid).seed)
            for tid in chain.take_ids
        ] == [("failed", 2**64 - 2), ("failed", 2**64 - 1)]


def test_terminal_cannot_authorize_placeholders_with_invalid_generation_request(engine):
    owner, _, chain, _, claim = prepared_chain(engine)
    with Session(engine) as session, session.begin():
        job = session.get(Job, chain.generation_job_id)
        job.request = {**job.request, "n_outputs": 65}
    fail(engine, owner, claim)
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).status == "failed"
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)
