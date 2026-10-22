import asyncio
from pathlib import Path
from types import SimpleNamespace

import app.queue.runtime as runtime_module
from app import models
from app.db import create_db_engine, migrate
from app.publication import PublicationCoordinator
from app.queue.runtime import QueueRuntime
from app.worker.execution import CpuAudioService
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def test_default_cpu_service_resolves_ffmpeg_from_repository_root(monkeypatch):
    runtime = object.__new__(QueueRuntime)
    runtime.engine = object()
    runtime.owner_id = "owner"
    runtime.bus = None
    runtime.publication_coordinator = object()
    runtime.settings = SimpleNamespace(data_dir=Path("C:/workspace/data"))
    captured = {}

    def fake_service(*args, **kwargs):
        captured["root"] = args[1]
        captured["ffmpeg"] = kwargs["ffmpeg"]
        captured["coordinator"] = kwargs["coordinator"]
        return "cpu-service"

    monkeypatch.setattr(runtime_module, "CpuAudioService", fake_service)
    assert runtime._default_cpu_service() == "cpu-service"
    assert captured["root"] == Path("C:/workspace")
    assert (
        captured["ffmpeg"]
        .as_posix()
        .endswith("tools/ffmpeg-linux/n9.0.2-17-g2a571b6068/bin/ffmpeg")
    )
    assert captured["coordinator"] is runtime.publication_coordinator


def test_default_cpu_service_uses_data_mount_as_worker_root(monkeypatch, tmp_path):
    runtime = object.__new__(QueueRuntime)
    runtime.engine = object()
    runtime.owner_id = "owner"
    runtime.bus = None
    runtime.publication_coordinator = object()
    runtime.settings = SimpleNamespace(data_dir=tmp_path / "data")
    captured = {}

    def fake_service(*args, **kwargs):
        captured["root"] = args[1]
        captured["coordinator"] = kwargs["coordinator"]
        return "cpu-service"

    monkeypatch.setattr(runtime_module, "CpuAudioService", fake_service)
    assert runtime._default_cpu_service() == "cpu-service"
    assert captured["root"] == tmp_path
    assert captured["coordinator"] is runtime.publication_coordinator


def test_runtime_dispatches_post_audio_to_cpu_service_with_two_slots():
    async def run():
        runtime = object.__new__(QueueRuntime)
        runtime.cpu_service = SimpleNamespace(calls=[])
        runtime.cpu_workers = {}

        class Admission:
            def candidates(self):
                return [
                    SimpleNamespace(id="post-1", task="post.audio"),
                    SimpleNamespace(id="beats-1", task="audio.beats"),
                    SimpleNamespace(id="post-2", task="post.audio"),
                    SimpleNamespace(id="post-3", task="post.audio"),
                ]

        def execute(job_id):
            runtime.cpu_service.calls.append(job_id)

        runtime.cpu_service.execute_job = execute
        runtime.admission = Admission()

        async def dbcall(function, *args):
            return function(*args)

        runtime.dbcall = dbcall
        await runtime._dispatch_cpu()
        await asyncio.gather(*runtime.cpu_workers.values())

        assert runtime.cpu_service.calls == ["post-1", "post-2"]
        assert "beats-1" not in runtime.cpu_service.calls
        assert "post-3" not in runtime.cpu_service.calls

    asyncio.run(run())


def test_runtime_arbitrates_engine_jobs_before_cpu_post_workers():
    async def run():
        runtime = object.__new__(QueueRuntime)
        runtime.stop = asyncio.Event()
        runtime.poll_s = 0.01
        runtime.cpu_workers = {}
        runtime.workers = {}
        runtime.backends = {"mock": object()}
        runtime.logger = SimpleNamespace(warning=lambda *args, **kwargs: None)
        order = []

        async def cancel_cpu():
            order.append("cancel_cpu")

        async def arbitrate():
            order.append("arbitrate")

        async def dispatch_cpu():
            order.append("dispatch_cpu")
            runtime.stop.set()

        runtime._cancel_cpu = cancel_cpu
        runtime._cancel = lambda: asyncio.sleep(0)
        runtime._active = list

        async def dbcall(function, *args):
            return function(*args)

        runtime.dbcall = dbcall
        runtime._arbitrate = arbitrate
        runtime._dispatch_cpu = dispatch_cpu
        await runtime._run()
        assert order == ["cancel_cpu", "arbitrate", "dispatch_cpu"]

    asyncio.run(run())


def test_cpu_service_claim_is_bounded_to_two_slots(tmp_path):
    owner = "01K70000000000000000000000"
    song = "01K70000000000000000000001"
    jobs = [f"01K7000000000000000000000{index}" for index in range(2, 5)]
    database = Path(tmp_path) / "data" / "studio.sqlite"
    database.parent.mkdir(parents=True)
    migrate(database)
    engine = create_db_engine(database)
    with Session(engine) as session, session.begin():
        local = session.scalar(select(models.User).where(models.User.name == "local"))
        owner = local.id
        session.add(models.Song(id=song, owner_id=owner, title="CPU"))
        for job_id in jobs:
            session.add(
                models.Job(
                    id=job_id,
                    owner_id=owner,
                    song_id=song,
                    task="post.audio",
                    lane="cpu",
                    status="queued",
                    request={"inputs": []},
                )
            )
    service = CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=tmp_path / "ffmpeg",
        owner_id=owner,
    )
    try:
        assert [service.claim_job(job_id) for job_id in jobs] == [True, True, False]
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(models.Job)
                    .where(models.Job.status == "running")
                )
                == 2
            )
            session.get(
                models.Job, jobs[0]
            ).cancel_requested_at = "2026-10-09T00:00:00Z"
            session.commit()
        assert service.pending_cancellations() == [jobs[0]]
        assert service.reconcile_startup() == 0
    finally:
        engine.dispose()


def test_cpu_service_reconciles_active_execution_after_restart(tmp_path):
    """A restart must leave an owned non-terminal execution explicitly unknown."""
    from test_worker_publication_invariants import (
        JOB,
        POST,
        SONG,
        TAKE,
        attach_provenance,
        common,
        execution,
        insert_raw,
        post_request,
        row,
        terminal,
    )

    database = Path(tmp_path) / "data" / "studio.sqlite"
    database.parent.mkdir(parents=True)
    migrate(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.add(models.Song(**common(SONG), title="reconcile"))
        session.flush()
        session.add(
            models.Job(
                **common(JOB),
                song_id=SONG,
                task="music.instrumental",
                lane="gpu",
                status="succeeded",
                attempt=1,
                request={"seed": 17},
            )
        )
        session.add(
            models.Job(
                **common(POST),
                song_id=SONG,
                task="post.audio",
                lane="cpu",
                status="running",
                attempt=1,
                request=post_request(),
            )
        )
        session.add(
            models.JobDependency(
                **common("01K70000000000000000000009"),
                job_id=POST,
                depends_on_job_id=JOB,
            )
        )
        session.add(
            models.Take(
                **common(TAKE),
                song_id=SONG,
                job_id=JOB,
                status="queued",
                batch_id=JOB,
                variant_index=0,
                root_id=TAKE,
                derivation="original",
                task="music.instrumental",
                model_id="mock",
                model_version="1.5",
                seed=17,
                commercial_use=True,
            )
        )
        attempt = row()
        attempt.update(status="succeeded", last_seq=1, terminal=terminal())
        session.add(models.JobAttempt(**attempt))
        session.commit()
    attach_provenance(engine)
    insert_raw(engine, "cpu_execution", execution())

    service = CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=tmp_path / "ffmpeg",
        owner_id=common(SONG)["owner_id"],
    )
    try:
        assert service.reconcile_startup() == 1
        with Session(engine) as session:
            job = session.get(models.Job, POST)
            cpu = session.get(models.CpuExecution, execution()["id"])
            assert (job.status, job.error_code) == (
                "interrupted",
                "CPU_CUSTODY_UNKNOWN",
            )
            assert (cpu.state, cpu.cleanup_state, cpu.error_code) == (
                "interrupted",
                "unknown",
                "CPU_CUSTODY_UNKNOWN",
            )
    finally:
        engine.dispose()
