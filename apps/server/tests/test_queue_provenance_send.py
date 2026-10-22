"""Frontera real SQLite/Dispatcher; EngineBackend ajeno y sintético declarado."""

import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest
from app.db import create_db_engine, migrate
from app.models import Job, JobAttempt, Song, User
from app.queue.admission import Admission
from app.queue.backends.protocol import CancelAck, ConfirmedAbsent, Submission
from app.queue.dispatcher import Dispatcher
from app.queue.resolver import Resolver
from app.worker.contracts import CapturedProvenance, canonical_sha256
from engine_contract import Event, Health, JobStatus, LoadedModel, ModelDescriptor
from sqlalchemy import select
from sqlalchemy.orm import Session

PHASE = Path(os.environ["STUDIO_PROVENANCE_TEST_ROOT"]).resolve()
assert PHASE.is_relative_to(
    Path.cwd().resolve() / ".cache/dev-cycle/m1/t05-provenance-capture-unit1"
)


def descriptor(device="gpu", task="music.instrumental"):
    return ModelDescriptor.model_validate(
        {
            "id": "fixture-model",
            "family": "fixture",
            "version": "1",
            "revision": "synthetic-immutable",
            "license": "MIT",
            "commercial_use": True,
            "training_data": "synthetic fixture only",
            "provider": {"type": "local"},
            "weights": [
                {
                    "path": "fixture/model.safetensors",
                    "sha256": "a" * 64,
                    "bytes": 1,
                    "format": "safetensors",
                }
            ],
            "modes": [
                {"id": m, "vram_mb": 1000, "notes": "synthetic"}
                for m in ("bf16", "offload", "cpu")
            ],
            "tasks": {
                task: {
                    "verified": True,
                    "device": device,
                    "params_schema": {"type": "object"},
                }
            },
        }
    )


class SyntheticBackend:
    """Único doble: protocolo EngineBackend, sin engine, pesos ni GPU reales."""

    origin = "http://synthetic-provenance:8199"

    def __init__(self, engine, *, device="gpu", task="music.instrumental"):
        self.engine = engine
        self.model = descriptor(device, task)
        self.loaded = None
        self.posts, self.loads = [], []
        self.after_health = None
        self.after_load = None
        self.health_update = {}
        self.boundary = None
        self.require_capture = task.startswith("music.")
        self.record = None
        self.events_value = []
        self.cancels = []

    async def models(self):
        return [self.model]

    async def health(self):
        value = Health(
            engine_id="fixture-engine",
            engine_version="1",
            image_digest="unknown",
            state="idle",
            loaded=self.loaded,
            gpu={"total_mb": 12000, "free_mb": 10000, "cap_mb": 9488},
        ).model_copy(update=self.health_update)
        if self.after_health and self.loads:
            self.after_health()
        return value

    async def load(self, request):
        self.loads.append(request)
        self.loaded = LoadedModel(model_id=request.model_id, mode=request.mode)
        if self.after_load:
            return self.after_load(self.loaded)
        return self.loaded

    async def unload(self):
        self.loaded = None

    async def submit(self, request):
        with Session(self.engine) as session:
            attempt = session.get(JobAttempt, request.job_id)
            if self.require_capture:
                assert attempt.provenance is not None, (
                    "missing durable provenance at submit"
                )
                evidence = CapturedProvenance.model_validate(attempt.provenance)
                assert attempt.provenance_sha256 == canonical_sha256(evidence)
                assert evidence.descriptor.value.revision == "synthetic-immutable"
                assert evidence.load.model_id == request.model_id
                assert evidence.load.mode == request.mode
                assert evidence.expected_image_digest is None
                assert evidence.reported_image_digest is None
            else:
                assert attempt.provenance is None and attempt.provenance_sha256 is None
            if self.boundary:
                self.boundary(attempt)
        self.posts.append(request)
        return Submission(job_id=request.job_id)

    async def status(self, aid):
        return self.record if self.record is not None else ConfirmedAbsent(aid)

    async def cancel(self, aid):
        self.cancels.append(aid)
        return CancelAck(job_id=aid)

    async def events(self, aid, after=0):
        for value in self.events_value:
            if value.seq > after:
                yield value


@pytest.fixture
def engine():
    directory = PHASE / uuid4().hex
    directory.mkdir(parents=True)
    path = directory / "studio.sqlite"
    migrate(path)
    db = create_db_engine(path)
    try:
        yield db
    finally:
        db.dispose()


def add(engine, *, device="gpu", task="music.instrumental"):
    with Session(engine) as session, session.begin():
        owner = session.scalar(select(User.id))
        song = Song(owner_id=owner, title="Fixture de procedencia")
        session.add(song)
        session.flush()
        job = Job(
            owner_id=owner,
            song_id=song.id,
            task=task,
            lane=device,
            request={
                "params": {"style": "  literal  "},
                "seed": 17,
                "mode": "cpu" if device == "cpu" else "bf16",
                "n_outputs": 2,
                "timeout_s": 60,
            },
        )
        session.add(job)
        session.flush()
        return job.id, owner


def pipeline(engine, *, device="gpu", task="music.instrumental"):
    jid, owner = add(engine, device=device, task=task)
    backend = SyntheticBackend(engine, device=device, task=task)
    admission = Admission(engine, owner)
    resolver = Resolver({"fixture": backend}, data_dir=PHASE)
    return jid, admission, resolver, backend, Dispatcher(admission, resolver)


def test_durable_capture_exists_at_real_submit_and_catalog_cannot_replace_it(engine):
    jid, admission, _resolver, backend, dispatcher = pipeline(engine)
    reserve = admission.reserve

    def mutate_after_selection(resolved):
        backend.model.revision = "later-catalog-mutation"
        return reserve(resolved)

    admission.reserve = mutate_after_selection
    claim = asyncio.run(dispatcher.dispatch(jid))
    assert claim is not None and len(backend.posts) == 1
    assert claim.request.seed == 17 and claim.request.n_outputs == 2
    assert claim.request.params == {"style": "  literal  "}


@pytest.mark.parametrize(
    "change",
    ["other", "unloaded", "ack", "version", "engine", "contract", "digest", "invalid"],
)
def test_post_load_drift_never_sends(engine, change):
    jid, _admission, _resolver, backend, dispatcher = pipeline(engine)

    def drift(loaded):
        if change == "other":
            backend.loaded = LoadedModel(model_id="OTHER", mode="bf16")
        elif change == "unloaded":
            backend.loaded = None
        elif change == "ack":
            return LoadedModel(model_id="OTHER", mode="bf16")
        else:
            field = {
                "version": "engine_version",
                "engine": "engine_id",
                "contract": "contract_version",
                "digest": "image_digest",
                "invalid": "image_digest",
            }[change]
            backend.health_update[field] = (
                "sha256:" + "b" * 64 if change == "digest" else "wrong"
            )
        return loaded

    backend.after_load = drift
    claim = asyncio.run(dispatcher.dispatch(jid))
    assert claim is not None and not backend.posts
    with Session(engine) as session:
        assert session.get(JobAttempt, claim.attempt_id).provenance is None


@pytest.mark.parametrize("task", ["music.instrumental", "audio.beats"])
def test_cpu_unloaded_is_honest_and_nonmusic_has_no_musical_evidence(engine, task):
    jid, _admission, _resolver, backend, dispatcher = pipeline(
        engine, device="cpu", task=task
    )
    if task.startswith("music."):
        backend.boundary = lambda attempt: (
            pytest.fail("CPU unloaded became observed")
            if attempt.provenance.observed_model is not None
            else None
        )
    claim = asyncio.run(dispatcher.dispatch(jid))
    assert claim is not None and len(backend.posts) == 1 and not backend.loads


@pytest.mark.parametrize("failure", ["cancel", "write"])
def test_no_send_when_health_to_capture_authority_or_commit_fails(engine, failure):
    from sqlalchemy.exc import OperationalError

    jid, admission, _resolver, backend, dispatcher = pipeline(engine)
    if failure == "cancel":

        def cancel():
            with Session(engine) as session, session.begin():
                session.get(Job, jid).cancel_requested_at = "2026-10-09T00:00:00Z"

        backend.after_health = cancel
    else:

        def failed_capture(*args):
            raise OperationalError("synthetic writer failure", {}, Exception("fixture"))

        admission.capture_provenance = failed_capture
    if failure == "write":
        with pytest.raises(OperationalError):
            asyncio.run(dispatcher.dispatch(jid))
    else:
        asyncio.run(dispatcher.dispatch(jid))
    assert not backend.posts
    with Session(engine) as session:
        attempt = session.scalar(select(JobAttempt).where(JobAttempt.job_id == jid))
        assert attempt.provenance is None


async def paused_runtime(engine, owner, backend):
    from app.queue.cancellation import Cancellation
    from app.queue.events import EventConsumer
    from app.queue.recovery import Recovery
    from app.queue.retry import Retry
    from app.queue.runtime import QueueRuntime
    from app.settings import ContractSettings

    runtime = QueueRuntime(
        engine,
        ContractSettings(data_dir=PHASE, engine_token="synthetic-private-fixture"),
        backends={"fixture": backend},
    )
    runtime.owner_id = owner
    runtime.admission = Admission(engine, owner)
    runtime.resolver = Resolver(runtime.backends, data_dir=PHASE)
    runtime.dispatcher = Dispatcher(runtime.admission, runtime.resolver)
    runtime.consumer = EventConsumer(engine, owner, runtime.bus)
    runtime.recovery = Recovery(engine, owner, PHASE)
    runtime.retry = Retry(engine, owner)
    runtime.cancellation = Cancellation(engine, owner)
    return runtime


def fail_attempt(engine, claim, *, code="VRAM_EXCEEDED"):
    from app.queue.events import EventBus, EventConsumer

    with Session(engine) as session:
        owner = session.get(JobAttempt, claim.attempt_id).owner_id
    terminal = Event(
        job_id=claim.attempt_id,
        seq=1,
        ts="2026-10-09T00:00:00Z",
        type="error",
        data={"code": code, "message": "synthetic", "retryable": True},
    )
    assert EventConsumer(engine, owner, EventBus()).accept(
        claim.attempt_id, "fixture-engine", terminal
    )


def test_retry_offload_captures_own_actual_load_preserves_previous_attempt(engine):
    jid, admission, _resolver, backend, dispatcher = pipeline(engine)
    previous = asyncio.run(dispatcher.dispatch(jid))
    with Session(engine) as session:
        row = session.get(JobAttempt, previous.attempt_id)
        old_sha = row.provenance_sha256
    fail_attempt(engine, previous)
    backend.loaded = None
    backend.posts.clear()

    async def run():
        runtime = await paused_runtime(engine, admission.owner_id, backend)
        try:
            await runtime._retry()
        finally:
            await runtime.close()

    asyncio.run(run())
    assert len(backend.posts) == 1
    new = backend.posts[0]
    assert new.job_id != previous.attempt_id and new.mode == "offload"
    assert (new.seed, new.n_outputs, new.params, new.inputs) == (
        previous.request.seed,
        previous.request.n_outputs,
        previous.request.params,
        previous.request.inputs,
    )
    with Session(engine) as session:
        old = session.get(JobAttempt, previous.attempt_id)
        current = session.get(JobAttempt, new.job_id)
        assert old.provenance_sha256 == old_sha and old.terminal.type == "error"
        assert current.ordinal == 2 and current.provenance.load.mode == "offload"
        assert current.provenance_sha256 != old_sha


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("interrupted", [False, True])
def test_confirmed_absent_submitted_resend_preserves_capture_and_denies_legacy_null(
    engine, legacy, interrupted
):
    jid, admission, resolver, backend, dispatcher = pipeline(engine)
    if legacy:
        resolved = asyncio.run(resolver.resolve(admission.select(jid), engine=engine))
        claim = admission.reserve(resolved)
        assert admission.acknowledge(claim)
    else:
        claim = asyncio.run(dispatcher.dispatch(jid))
    backend.loaded = None
    backend.posts.clear()
    if interrupted:
        with Session(engine) as session, session.begin():
            session.get(Job, jid).status = "interrupted"
    with Session(engine) as session:
        row = session.get(JobAttempt, claim.attempt_id)
        prior = row.provenance
        prior_sha = row.provenance_sha256

    async def run():
        runtime = await paused_runtime(engine, admission.owner_id, backend)
        try:
            attempt = runtime.recovery.current(claim.attempt_id)[0]
            task = asyncio.create_task(runtime._consume(attempt))
            # Stop only after one complete operational observation, not a performance gate.
            for _ in range(100):
                with Session(engine) as session:
                    job = session.get(Job, jid)
                    if backend.posts or (
                        job.status == "interrupted" and (legacy or job.error)
                    ):
                        break
                await asyncio.sleep(0.01)
            runtime.stop.set()
            await task
        finally:
            await runtime.close()

    asyncio.run(run())
    assert len(backend.posts) == (0 if legacy else 1)
    with Session(engine) as session:
        row = session.get(JobAttempt, claim.attempt_id)
        assert row.provenance == prior and row.provenance_sha256 == prior_sha


@pytest.mark.parametrize("drift", ["catalog", "other", "version", "digest", "cancel"])
def test_recovery_fresh_drift_or_cancel_denies_send_without_rewriting_history(
    engine, drift
):
    jid, admission, _resolver, backend, dispatcher = pipeline(engine)
    claim = asyncio.run(dispatcher.dispatch(jid))
    backend.posts.clear()
    backend.loaded = None
    if drift == "catalog":
        backend.model.revision = "changed-after-original-send"
    else:

        def changed(loaded):
            if drift == "other":
                backend.loaded = LoadedModel(model_id="OTHER", mode="bf16")
            elif drift in {"version", "digest"}:
                backend.health_update[
                    "engine_version" if drift == "version" else "image_digest"
                ] = "changed"
            else:
                with Session(engine) as session, session.begin():
                    session.get(Job, jid).cancel_requested_at = "2026-10-09T00:00:00Z"
            return loaded

        backend.after_load = changed
    with Session(engine) as session:
        original = session.get(JobAttempt, claim.attempt_id).provenance

    async def run():
        runtime = await paused_runtime(engine, admission.owner_id, backend)
        try:
            task = asyncio.create_task(
                runtime._consume(runtime.recovery.current(claim.attempt_id)[0])
            )
            for _ in range(100):
                with Session(engine) as session:
                    if session.get(Job, jid).status == "interrupted":
                        break
                await asyncio.sleep(0.01)
            runtime.stop.set()
            await task
        finally:
            await runtime.close()

    asyncio.run(run())
    assert not backend.posts
    with Session(engine) as session:
        assert session.get(JobAttempt, claim.attempt_id).provenance == original


def test_cpu_resend_loaded_matching_keeps_original_unobserved_capture(engine):
    jid, admission, _resolver, backend, dispatcher = pipeline(engine, device="cpu")
    claim = asyncio.run(dispatcher.dispatch(jid))
    backend.posts.clear()
    backend.loaded = LoadedModel(model_id=claim.load_options.model_id, mode="cpu")

    async def run():
        runtime = await paused_runtime(engine, admission.owner_id, backend)
        try:
            task = asyncio.create_task(
                runtime._consume(runtime.recovery.current(claim.attempt_id)[0])
            )
            for _ in range(100):
                if backend.posts:
                    break
                await asyncio.sleep(0.01)
            runtime.stop.set()
            await task
        finally:
            await runtime.close()

    asyncio.run(run())
    assert len(backend.posts) == 1 and not backend.loads
    with Session(engine) as session:
        row = session.get(JobAttempt, claim.attempt_id)
        assert row.provenance.observed_model is None


def test_real_arbitration_preserves_cpu_two_capacity_and_nonmusic_null(engine):
    pipelines = [pipeline(engine, device="cpu", task="audio.beats") for _ in range(3)]
    owner = pipelines[0][1].owner_id
    backends = {}
    for index, (jid, admission, resolver, backend, dispatcher) in enumerate(pipelines):
        identity = "synthetic-cpu-" + str(index)
        backend.origin = "http://" + identity + ":8199"
        backend.health_update["engine_id"] = identity
        backends[identity] = backend
        with Session(engine) as session, session.begin():
            session.get(Job, jid).engine_id = identity

    async def run():
        runtime = await paused_runtime(engine, owner, pipelines[0][3])
        runtime.backends = backends
        runtime.resolver = Resolver(backends, data_dir=PHASE)
        runtime.dispatcher = Dispatcher(runtime.admission, runtime.resolver)
        try:
            await runtime._arbitrate()
            assert sum(len(backend.posts) for backend in backends.values()) == 2
            assert (
                sum(
                    count
                    for lane, _, count in runtime._retry_occupancy()
                    if lane == "cpu"
                )
                == 2
            )
        finally:
            await runtime.close()

    asyncio.run(run())


def test_orphan_interrupted_job_without_attempt_does_not_consume_capacity(engine):
    jid, owner = add(engine, device="cpu", task="audio.beats")
    with Session(engine) as session, session.begin():
        job = session.get(Job, jid)
        job.status = "interrupted"
        job.attempt = 1

    backend = SyntheticBackend(engine, device="cpu", task="audio.beats")

    async def run():
        runtime = await paused_runtime(engine, owner, backend)
        try:
            assert runtime._retry_occupancy() == []
        finally:
            await runtime.close()

    asyncio.run(run())


def test_orphan_interrupted_jobs_do_not_block_cpu_dispatch(engine):
    orphans = [add(engine, device="cpu", task="audio.beats")[0] for _ in range(2)]
    with Session(engine) as session, session.begin():
        for orphan in orphans:
            job = session.get(Job, orphan)
            job.status = "interrupted"
            job.attempt = 1

    jid, _admission, _resolver, backend, dispatcher = pipeline(
        engine, device="cpu", task="audio.beats"
    )
    claim = asyncio.run(dispatcher.dispatch(jid))
    assert claim is not None
    assert len(backend.posts) == 1


def test_switching_owned_gpu_resident_captures_new_target_after_load(engine):
    jid, _admission, resolver, backend, dispatcher = pipeline(engine)
    claim = asyncio.run(dispatcher.dispatch(jid))
    fail_attempt(engine, claim, code="INTERNAL")
    next_id, _ = add(engine)
    target = SyntheticBackend(engine)
    target.origin = "http://synthetic-second:8199"
    target.health_update["engine_id"] = "synthetic-second"
    with Session(engine) as session, session.begin():
        session.get(Job, next_id).engine_id = "synthetic-second"
    resolver.backends["second"] = target
    next_claim = asyncio.run(dispatcher.dispatch(next_id))
    assert next_claim is not None and len(target.posts) == 1
    assert backend.loaded is None
    with Session(engine) as session:
        captured = session.get(JobAttempt, next_claim.attempt_id).provenance
        assert captured.engine_id == "synthetic-second"
        assert captured.observed_model.model_id == target.model.id


@pytest.mark.parametrize("kind", ["done", "error", "cancelled"])
def test_live_runtime_consumer_keeps_capture_through_real_terminal(engine, kind):
    from app.queue.runtime import QueueRuntime
    from app.settings import ContractSettings

    jid, _admission, _resolver, backend, dispatcher = pipeline(engine)
    claim = asyncio.run(dispatcher.dispatch(jid))
    data = {
        "done": {
            "artifacts": [],
            "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
        },
        "error": {
            "code": "INTERNAL",
            "message": "synthetic terminal",
            "retryable": False,
        },
        "cancelled": {"telemetry": {"mode": "bf16", "model_revision": "synthetic"}},
    }[kind]
    backend.record = JobStatus(job_id=claim.attempt_id, state=kind, seq=1)
    backend.events_value = [
        Event(
            job_id=claim.attempt_id,
            seq=1,
            ts="2026-10-09T00:00:00Z",
            type=kind,
            data=data,
        )
    ]
    if kind == "cancelled":
        with Session(engine) as session, session.begin():
            session.get(Job, jid).cancel_requested_at = "2026-10-09T00:00:00Z"

    async def run():
        runtime = QueueRuntime(
            engine,
            ContractSettings(data_dir=PHASE, engine_token="synthetic"),
            backends={"fixture": backend},
            poll_s=0.01,
        )
        await runtime.start()
        try:
            for _ in range(100):
                with Session(engine) as session:
                    row = session.get(JobAttempt, claim.attempt_id)
                    if row.terminal is not None:
                        break
                await asyncio.sleep(0.01)
            with Session(engine) as session:
                row = session.get(JobAttempt, claim.attempt_id)
                assert row.terminal is not None and row.terminal.type == kind
                assert row.provenance_sha256 == canonical_sha256(row.provenance)
            if kind == "cancelled":
                assert backend.cancels == [claim.attempt_id]
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "observation", ["foreign_status", "rollback", "lost_health", "foreign_absence"]
)
def test_recovery_uncertainty_retains_capture_and_capacity(engine, observation):
    from app.queue.backends.protocol import BackendFailure
    from app.queue.events import EventBus, EventConsumer

    jid, admission, _resolver, backend, dispatcher = pipeline(engine)
    claim = asyncio.run(dispatcher.dispatch(jid))
    if observation == "rollback":
        assert EventConsumer(engine, admission.owner_id, EventBus()).accept(
            claim.attempt_id,
            "fixture-engine",
            Event(
                job_id=claim.attempt_id,
                seq=1,
                ts="2026-10-09T00:00:00Z",
                type="stage",
                data={"stage": "generating"},
            ),
        )
        backend.record = JobStatus(job_id=claim.attempt_id, state="busy", seq=0)
    elif observation == "foreign_status":
        backend.record = JobStatus(
            job_id="01K70000000000000000000009", state="busy", seq=0
        )
    elif observation == "foreign_absence":
        backend.record = ConfirmedAbsent("01K70000000000000000000009")
    else:

        async def lost():
            raise BackendFailure("SYNTHETIC_DOWN")

        backend.health = lost
    backend.posts.clear()

    async def run():
        runtime = await paused_runtime(engine, admission.owner_id, backend)
        try:
            if observation == "lost_health":
                assert await runtime._backend_for("fixture-engine") is None
                return
            task = asyncio.create_task(
                runtime._consume(runtime.recovery.current(claim.attempt_id)[0])
            )
            for _ in range(100):
                with Session(engine) as session:
                    if session.get(Job, jid).status == "interrupted":
                        break
                await asyncio.sleep(0.01)
            runtime.stop.set()
            await task
            assert runtime._retry_occupancy() == [("gpu", "fixture-engine", 1)]
        finally:
            await runtime.close()

    asyncio.run(run())
    assert not backend.posts
    with Session(engine) as session:
        assert session.get(JobAttempt, claim.attempt_id).provenance is not None
