"""T-04 CA-4: un job de engine dudoso pasa a reintento acotado."""
# ruff: noqa: F811  (los fixtures se importan de otro test)

import asyncio

import pytest
from app.models import Job, JobAttempt
from app.queue.runtime import QueueRuntime
from sqlalchemy.orm import Session
from test_dispatcher_recovery import (  # noqa: F401  (fixture `engine`)
    RecordedBackend,
    engine,
    prepared,
    settings,
)


def _run(engine, backend, *, settle=0.6):
    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.sleep(settle)
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize("scenario", ["cursor", "partial"])
def test_ca4_absent_engine_makes_doubtful_job_failed_retryable_then_retried(
    engine, scenario
):
    jid, _, claim = prepared(engine)
    backend = RecordedBackend()
    if scenario == "cursor":
        with Session(engine) as session, session.begin():
            session.get(JobAttempt, claim.attempt_id).last_seq = 1
    else:
        output = settings().data_dir / "tmp" / claim.attempt_id
        output.mkdir(parents=True)
        (output / "partial.bin").write_bytes(b"preserve")
    _run(engine, backend)
    with Session(engine) as session:
        first = session.get(JobAttempt, claim.attempt_id)
        assert first.status == "failed"
        assert first.terminal.type == "error"
        assert first.terminal.data["retryable"] is True
        job = session.get(Job, jid)
        # Lo recoge el retry x2 existente: attempt nuevo con la misma semilla.
        assert job.attempt == 2
        assert len(backend.posts) == 1
        assert backend.posts[0].job_id != claim.attempt_id
        assert backend.posts[0].seed == claim.request.seed
    if scenario == "partial":
        assert (output / "partial.bin").read_bytes() == b"preserve"


def test_ca4_respects_max_attempts(engine):
    jid, _, claim = prepared(engine)
    with Session(engine) as session, session.begin():
        session.get(JobAttempt, claim.attempt_id).last_seq = 1
        session.get(Job, jid).max_attempts = 1
    backend = RecordedBackend()
    _run(engine, backend)
    with Session(engine) as session:
        job = session.get(Job, jid)
        assert job.status == "failed"
        assert job.attempt == 1
        assert session.get(JobAttempt, claim.attempt_id).terminal.type == "error"
    assert not backend.posts


def test_ca4_unresponsive_engine_keeps_waiting(engine):
    from app.queue.backends.protocol import BackendFailure

    jid, _, claim = prepared(engine)
    backend = RecordedBackend()

    async def failed(aid):
        raise BackendFailure("AUTH")

    backend.status = failed
    _run(engine, backend, settle=0.35)
    with Session(engine) as session:
        assert session.get(Job, jid).status == "interrupted"
        assert session.get(JobAttempt, claim.attempt_id).terminal is None
    assert not backend.posts
