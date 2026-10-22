"""Recuperación sintética sobre intentos nativos persistentes."""

import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest
from app.db import create_db_engine, migrate
from app.models import Job, JobAttempt
from app.queue.backends.protocol import CancelAck, ConfirmedAbsent, Submission
from app.queue.runtime import QueueRuntime
from app.settings import ContractSettings
from engine_contract import Event, JobStatus, LoadedModel
from sqlalchemy.orm import Session
from synthetic_composition import capture
from test_dispatcher_admission import add, admission, resolve
from test_queue_resolver import Catalog


@pytest.fixture
def engine():
    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    path = root / "studio.sqlite"
    migrate(path)
    db = create_db_engine(path)
    try:
        yield db
    finally:
        db.dispose()


class RecordedBackend(Catalog):
    """Backend protocol synthetic; records every side effect."""

    def __init__(self, **composition_options):
        super().__init__(**composition_options)
        self.posts, self.cancels, self.cursors = [], [], []
        self.record = None
        self.events_value = []

    async def load(self, request):
        self.loaded = LoadedModel(model_id=request.model_id, mode=request.mode)
        return self.loaded

    async def submit(self, request):
        self.posts.append(request)
        self.record = JobStatus(job_id=request.job_id, state="busy", seq=0)
        return Submission(job_id=request.job_id)

    async def status(self, aid):
        return self.record if self.record is not None else ConfirmedAbsent(aid)

    async def cancel(self, aid):
        self.cancels.append(aid)
        return CancelAck(job_id=aid)

    async def events(self, aid, after=0):
        self.cursors.append((aid, after))
        for value in self.events_value:
            yield value


class _SubmitObservedBackend(RecordedBackend):
    def __init__(self):
        super().__init__()
        self.submitted = asyncio.Event()

    async def submit(self, request):
        response = await super().submit(request)
        self.submitted.set()
        return response


def prepared(engine, *, backend=None):
    jid, owner = add(engine)
    from test_dispatcher_admission import DEFAULT_CATALOG

    if backend is None:
        adm = admission(engine, owner)
        claim = adm.reserve(resolve(adm.select(jid)))
        capture(adm, claim, DEFAULT_CATALOG)
    else:
        from app.queue.resolver import Resolver

        adm = admission(engine, owner, synthetic_registry=backend.synthetic_registry)
        resolver = Resolver(
            {"mock": backend},
            data_dir=settings().data_dir,
            synthetic_registry=backend.synthetic_registry,
        )
        claim = adm.reserve(asyncio.run(resolver.resolve(adm.select(jid))))
        capture(adm, claim, backend)
        # Proceso remoto reiniciado antes de inyectar el escenario de recuperación.
        backend.loaded = None
    return jid, owner, claim


def settings():
    return ContractSettings(
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        engine_token="private-test-only",
    )


def event(aid, kind, data, seq=1):
    return Event.model_validate(
        {
            "job_id": aid,
            "seq": seq,
            "ts": "2026-10-08T02:00:00Z",
            "type": kind,
            "data": data,
        }
    )


def test_absent_zero_cursor_resubmits_same_frozen_id(engine):
    jid, _owner, claim = prepared(engine)
    backend = _SubmitObservedBackend()

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.wait_for(backend.submitted.wait(), runtime.control_s)
            assert len(backend.posts) == 1, "Lost ACK did not reconcile frozen attempt"
            assert backend.posts[0] == claim.request
            with Session(engine) as session:
                assert session.get(Job, jid).attempt == 1
                assert session.get(JobAttempt, claim.attempt_id).id == claim.attempt_id
        finally:
            await runtime.close()

    asyncio.run(run())


def test_other_active_ignores_orphan_or_deleted_interrupted_jobs(engine):
    from app.queue.recovery import Recovery

    current, owner = add(engine, status="running", lane="cpu", engine_id="mock")
    _orphan, _ = add(engine, status="interrupted", lane="cpu", engine_id="mock")
    deleted, _ = add(engine, status="interrupted", lane="cpu", engine_id="mock")
    with Session(engine) as session, session.begin():
        session.get(Job, deleted).deleted_at = "2026-10-10T00:00:00Z"

    recovery = Recovery(engine, owner, settings().data_dir)
    assert not recovery.other_active(current, "cpu", "mock")


def test_absent_zero_cursor_waits_for_real_submit_with_delayed_status(
    engine, monkeypatch
):
    original_status = RecordedBackend.status
    observations = {"entered": 0, "returned": 0}

    async def delayed_status(self, aid):
        result = await original_status(self, aid)
        if isinstance(result, ConfirmedAbsent):
            observations["entered"] += 1
            await asyncio.sleep(0.45)
            observations["returned"] += 1
        return result

    monkeypatch.setattr(RecordedBackend, "status", delayed_status)
    test_absent_zero_cursor_resubmits_same_frozen_id(engine)
    assert observations == {"entered": 1, "returned": 1}


def test_configured_family_alias_reconnects_only_matching_engine(engine):
    jid, _, claim = prepared(engine)
    backend = RecordedBackend()
    backend.record = JobStatus(job_id=claim.attempt_id, state="done", seq=1)
    backend.events_value = [
        event(
            claim.attempt_id,
            "done",
            {
                "artifacts": [],
                "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
            },
        )
    ]

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"family_alias": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.sleep(0.35)
            with Session(engine) as session:
                assert session.get(Job, jid).status == "succeeded", (
                    "Configured family name hid matching engine identity"
                )
            assert not backend.posts
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "scenario",
    [
        # "cursor" y "partial" (el engine confirma ausencia) pasan a reintento
        # acotado en T-04/CA-4: ver test_queue_recovery_gpu_doubt.py.
        "rollback",
        "status_failure",
        "foreign",
        "wrong_identity",
        "unverified",
        "noncommercial",
        "vram",
    ],
)
def test_uncertain_recovery_retains_capacity_and_cursor(engine, scenario):
    from app.queue.backends.protocol import BackendFailure

    jid, _, claim = prepared(engine)
    backend = RecordedBackend()
    if scenario == "unverified":
        backend.value["tasks"]["music.instrumental"]["verified"] = False
    if scenario == "noncommercial":
        backend.value["commercial_use"] = False
    if scenario == "vram":
        original = backend.health

        async def constrained():
            return (await original()).model_copy(
                update={
                    "gpu": (await original()).gpu.model_copy(update={"free_mb": 600})
                }
            )

        backend.health = constrained
    if scenario == "rollback":
        with Session(engine) as session, session.begin():
            session.get(JobAttempt, claim.attempt_id).last_seq = 1
        backend.record = JobStatus(job_id=claim.attempt_id, state="done", seq=0)
    if scenario == "status_failure":

        async def failed(aid):
            raise BackendFailure("AUTH")

        backend.status = failed
    if scenario == "foreign":
        original = backend.health

        async def occupied():
            value = await original()
            return value.model_copy(
                update={"state": "busy", "job_id": "01K70000000000000000000003"}
            )

        backend.health = occupied
    if scenario == "wrong_identity":
        original = backend.health

        async def wrong():
            return (await original()).model_copy(update={"engine_id": "foreign"})

        backend.health = wrong

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.sleep(0.35)
            with Session(engine) as session:
                assert session.get(Job, jid).status == "interrupted", (
                    "Startup did not retain uncertain occupancy"
                )
                assert session.get(JobAttempt, claim.attempt_id).last_seq == (
                    1 if scenario == "rollback" else 0
                )
            assert not backend.posts
            assert not backend.cancels
        finally:
            await runtime.close()

    asyncio.run(run())
