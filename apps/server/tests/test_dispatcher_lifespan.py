"""Runtime del producto con HTTP sintético y SQLite nativo, sin GPU."""

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from app.main import create_app
from app.models import Job, JobAttempt
from app.settings import ContractSettings
from sqlalchemy import select
from sqlalchemy.orm import Session
from synthetic_composition import http_runtime
from test_dispatcher_admission import add
from test_queue_backend import health
from test_queue_resolver import descriptor


def test_configured_lifespan_consumes_real_terminal(monkeypatch):
    posts = []
    original = httpx.AsyncClient
    resident = [None]

    def wire(request):
        assert request.headers.get("X-Studio-Engine-Token") == "private-test-only"
        if request.url.path == "/v1/health":
            return httpx.Response(200, json=dict(health(), loaded=resident[0]))
        if request.url.path == "/v1/models":
            return httpx.Response(200, json=[descriptor()])
        if request.url.path == "/v1/load":
            resident[0] = {"model_id": "mock", "mode": "bf16"}
            return httpx.Response(200, json={"model_id": "mock", "mode": "bf16"})
        if request.url.path == "/v1/jobs":
            body = json.loads(request.content)
            posts.append(body)
            return httpx.Response(202, json={"job_id": body["job_id"]})
        aid = request.url.path.split("/")[-1]
        if request.url.path.endswith("/events"):
            aid = request.url.path.split("/")[-2]
            terminal = {
                "job_id": aid,
                "seq": 1,
                "ts": "2026-10-08T02:00:00Z",
                "type": "done",
                "data": {
                    "artifacts": [],
                    "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
                },
            }
            return httpx.Response(
                200,
                text=json.dumps(terminal) + "\n",
                headers={"content-type": "application/x-ndjson"},
            )
        return httpx.Response(200, json={"job_id": aid, "state": "done", "seq": 1})

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(**dict(kw, transport=httpx.MockTransport(wire))),
    )
    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    settings = ContractSettings(
        data_dir=root,
        engine_token="private-test-only",
        engines={"mock": "http://engine-mock:8199"},
    )

    async def run():
        app = create_app(settings, queue_runtime_factory=http_runtime)
        async with app.router.lifespan_context(app):
            jid, _ = await asyncio.to_thread(add, app.state.db)
            for _ in range(40):
                await asyncio.sleep(0.05)
                with Session(app.state.db) as session:
                    job = session.get(Job, jid)
                    if job.status == "succeeded":
                        attempt = session.scalar(
                            select(JobAttempt).where(JobAttempt.job_id == jid)
                        )
                        assert attempt.last_seq == 1
                        assert attempt.terminal.type == "done"
                        assert len(posts) == 1
                        return
            with Session(app.state.db) as session:
                runtime = getattr(app.state, "queue", None)
                if runtime:
                    errors = [
                        repr(t.exception())
                        for t in runtime.workers.values()
                        if t.done() and not t.cancelled()
                    ]
                    assert not errors, errors
                assert session.get(Job, jid).status == "succeeded", (
                    "Configured lifespan left durable job unconsumed"
                )

    asyncio.run(run())


def test_cancellation_during_cleanup_awaits_resources_and_keeps_cancel_identity():
    from app.queue.runtime import QueueRuntime

    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    config = ContractSettings(data_dir=root, engine_token="private-test-only")
    entered, release = None, None

    class Closing(QueueRuntime):
        async def close(self):
            entered.set()
            await release.wait()
            await super().close()
            raise RuntimeError("synthetic secondary close")

    async def run():
        nonlocal entered, release
        entered, release = asyncio.Event(), asyncio.Event()
        app = create_app(config, queue_runtime_factory=Closing)

        async def lifetime():
            async with app.router.lifespan_context(app):
                pass

        task = asyncio.create_task(lifetime())
        await asyncio.wait_for(entered.wait(), 2)
        task.cancel("synthetic cancel during close")
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError) as caught:
            await asyncio.wait_for(task, 2)
        assert caught.value.args == ("synthetic cancel during close",)
        assert app.state.backup.task.done()
        assert app.state.queue.executor._shutdown
        assert not app.state.queue.native and not app.state.queue.workers

    asyncio.run(run())


@pytest.mark.parametrize("secondary", ["runtime", "backup", "dispose"])
@pytest.mark.parametrize("cancelled", [False, True])
def test_startup_original_identity_survives_secondary_cleanup_with_resources(
    monkeypatch, secondary, cancelled
):
    import pytest
    from app import main
    from app.queue.runtime import QueueRuntime

    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    config = ContractSettings(data_dir=root, engine_token="private-test-only")
    original = (
        asyncio.CancelledError("synthetic cancellation")
        if cancelled
        else RuntimeError("synthetic original startup")
    )
    sentinels = []
    real_engine = main.create_db_engine

    def create_engine(*args, **kwargs):
        db = real_engine(*args, **kwargs)
        dispose = db.dispose

        def closed():
            dispose()
            sentinels.append("engine disposed")
            if secondary == "dispose":
                raise RuntimeError("synthetic disposal failure")

        db.dispose = closed
        return db

    monkeypatch.setattr(main, "create_db_engine", create_engine)
    backup_close = main.DailyBackup.close

    async def closed_backup(self):
        await backup_close(self)
        if secondary == "backup":
            raise RuntimeError("synthetic backup failure")

    monkeypatch.setattr(main.DailyBackup, "close", closed_backup)

    class Failing(QueueRuntime):
        async def start(self):
            await self.dbcall(lambda: sentinels.append("native acquired"))
            self.workers["sentinel"] = asyncio.create_task(asyncio.Event().wait())
            raise original

        async def close(self):
            await super().close()
            sentinels.append("runtime closed")
            if secondary == "runtime":
                raise RuntimeError("synthetic secondary cleanup")

    async def run():
        app = create_app(config, queue_runtime_factory=Failing)
        with pytest.raises(type(original)) as caught:
            async with app.router.lifespan_context(app):
                pytest.fail("startup must fail")
        assert app.state.backup.task.done()
        assert app.state.backup.stop.is_set() and app.state.backup.cancel.is_set()
        assert not app.state.queue.native and not app.state.queue.workers
        assert app.state.queue.executor._shutdown
        assert sentinels == ["native acquired", "runtime closed", "engine disposed"]
        assert caught.value is original, (
            "Secondary cleanup replaced original startup exception"
        )
        assert caught.value.__notes__ == ["server.cleanup_failed"]

    asyncio.run(run())


@pytest.mark.parametrize("secondary", ["backup", "dispose"])
def test_standalone_cleanup_failure_remains_failure(monkeypatch, secondary):
    from app import main

    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    config = ContractSettings(data_dir=root, engine_token="private-test-only")
    failure = RuntimeError("synthetic standalone cleanup")
    real_close = main.DailyBackup.close
    real_engine = main.create_db_engine
    disposed = []

    async def close(self):
        await real_close(self)
        if secondary == "backup":
            raise failure

    def create_engine(*args, **kwargs):
        engine = real_engine(*args, **kwargs)
        dispose = engine.dispose

        def final():
            dispose()
            disposed.append(True)
            if secondary == "dispose":
                raise failure

        engine.dispose = final
        return engine

    monkeypatch.setattr(main.DailyBackup, "close", close)
    monkeypatch.setattr(main, "create_db_engine", create_engine)

    async def run():
        app = create_app(config)
        with pytest.raises(RuntimeError) as caught:
            async with app.router.lifespan_context(app):
                pass
        assert caught.value is failure
        assert app.state.backup.task.done()
        assert app.state.queue.task.done() and app.state.queue.executor._shutdown
        assert disposed == [True]

    asyncio.run(run())


def test_empty_engines_lifespan_preserves_health_security_and_backup():
    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    settings = ContractSettings(data_dir=root, engine_token="private-test-only")

    async def run():
        app = create_app(settings)
        async with app.router.lifespan_context(app):
            runtime = app.state.queue
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000"
            ) as client:
                assert (await client.get("/health")).json() == {
                    "status": "running",
                    "process": "server",
                }
                assert (
                    await client.get("/health", headers={"host": "foreign.test"})
                ).status_code == 403
                assert (await client.get("/missing")).status_code == 404
            assert list((root / "backups").iterdir())
            assert not runtime.backends and not runtime.workers
        assert runtime.task.done()
        assert not runtime.native and not runtime.workers

    asyncio.run(run())


def test_runtime_close_failure_still_awaits_backup_shutdown():
    import pytest
    from app.queue.runtime import QueueRuntime

    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    settings = ContractSettings(data_dir=root, engine_token="private-test-only")

    class FailingClose(QueueRuntime):
        async def close(self):
            await super().close()
            raise RuntimeError("synthetic close failure")

    async def run():
        app = create_app(settings, queue_runtime_factory=FailingClose)
        with pytest.raises(RuntimeError, match="synthetic close failure"):
            async with app.router.lifespan_context(app):
                backup = app.state.backup
        assert backup.task.done(), "Queue close failure orphaned backup task"

    asyncio.run(run())


def test_startup_recovery_failure_closes_runtime_without_masking_cause(monkeypatch):
    import pytest
    from app.queue.recovery import Recovery
    from app.queue.runtime import QueueRuntime
    from test_dispatcher_recovery import RecordedBackend

    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    settings = ContractSettings(data_dir=root, engine_token="private-test-only")

    def broken(self):
        raise RuntimeError("synthetic startup cause")

    monkeypatch.setattr(Recovery, "startup", broken)
    created = []

    def factory(db, config):
        backend = RecordedBackend()
        runtime = QueueRuntime(
            db,
            config,
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        created.append(runtime)
        return runtime

    async def run():
        app = create_app(settings, queue_runtime_factory=factory)
        with pytest.raises(RuntimeError, match="synthetic startup cause"):
            async with app.router.lifespan_context(app):
                raise AssertionError("Unreachable failed startup")
        assert not created[0].native
        assert app.state.backup.task.done()

    asyncio.run(run())


def test_shutdown_awaits_native_writer_and_cancels_slow_stream():
    import threading

    from app.queue.runtime import QueueRuntime
    from engine_contract import JobStatus
    from test_dispatcher_recovery import RecordedBackend
    from test_dispatcher_recovery import settings as config

    # Standalone native file to exercise the actual application lifecycle.
    root = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex
    root.mkdir()
    (root / ".u2-owner").write_text(root.name, encoding="utf-8")
    backend = RecordedBackend()
    entered, release, stream_closed = threading.Event(), threading.Event(), []

    async def status(aid):
        return JobStatus(job_id=aid, state="busy", seq=0)

    async def slow(aid, after=0):
        try:
            await asyncio.Event().wait()
            yield None
        finally:
            stream_closed.append(aid)

    backend.status, backend.events = status, slow

    async def run():
        settings = config().model_copy(update={"data_dir": root})
        app = create_app(
            settings,
            queue_runtime_factory=lambda db, st: QueueRuntime(
                db,
                st,
                backends={"mock": backend},
                stream_s=0.2,
                synthetic_registry=backend.synthetic_registry,
            ),
        )
        async with app.router.lifespan_context(app):
            runtime = app.state.queue
            jid, _ = await asyncio.to_thread(add, app.state.db)
            for _ in range(40):
                if runtime.workers:
                    break
                await asyncio.sleep(0.025)
            original = runtime._active

            def paused():
                entered.set()
                release.wait(2)
                return original()

            runtime._active = paused
            for _ in range(40):
                if entered.is_set():
                    break
                await asyncio.sleep(0.025)
            assert entered.is_set()
            close = asyncio.create_task(runtime.close())
            await asyncio.sleep(0.04)
            assert not close.done(), "Native SQLite work was orphaned at shutdown"
            release.set()
            await close
            with Session(app.state.db) as session:
                assert session.get(Job, jid).status in {"running", "interrupted"}
            assert stream_closed
            assert not runtime.workers and not runtime.native
        assert not backend.cancels

    try:
        asyncio.run(run())
    finally:
        release.set()
