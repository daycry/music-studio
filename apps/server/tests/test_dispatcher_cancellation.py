"""Un acuse de cancelación no libera ocupación."""

import asyncio

from app.models import Job, JobAttempt
from app.queue.runtime import QueueRuntime
from engine_contract import JobStatus
from sqlalchemy.orm import Session
from test_dispatcher_recovery import RecordedBackend, prepared, settings
from test_dispatcher_recovery import engine as engine  # noqa: PLC0414


def test_durable_cancel_propagated_without_fabricating_terminal(engine):
    jid, _, claim = prepared(engine)
    with Session(engine) as session, session.begin():
        session.get(Job, jid).cancel_requested_at = "2026-10-08T02:00:00Z"
    backend = RecordedBackend()
    backend.record = JobStatus(job_id=claim.attempt_id, state="busy", seq=0)

    async def run():
        runtime = QueueRuntime(engine, settings(), backends={"mock": backend})
        await runtime.start()
        try:
            await asyncio.sleep(0.35)
            assert backend.cancels == [claim.attempt_id], (
                "Durable cancellation never reached engine"
            )
            with Session(engine) as session:
                assert session.get(Job, jid).status in {"running", "interrupted"}
                assert session.get(JobAttempt, claim.attempt_id).terminal is None
            assert not backend.posts
        finally:
            await runtime.close()

    asyncio.run(run())


def test_queued_cancel_terminalizes_without_inventing_engine_event(engine):
    from test_dispatcher_admission import add

    jid, _ = add(engine)
    with Session(engine) as session, session.begin():
        session.get(Job, jid).cancel_requested_at = "2026-10-08T02:00:00Z"
    backend = RecordedBackend()

    async def run():
        runtime = QueueRuntime(engine, settings(), backends={"mock": backend})
        await runtime.start()
        try:
            await asyncio.sleep(0.25)
            with Session(engine) as session:
                assert session.get(Job, jid).status == "cancelled"
                assert session.get(Job, jid).attempt == 0
            assert not backend.cancels and not backend.posts
        finally:
            await runtime.close()

    asyncio.run(run())
