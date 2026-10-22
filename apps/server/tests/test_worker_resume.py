"""T-04: carril CPU, idempotencia del arranque y reanudación de post.audio."""

import time
from pathlib import Path

from app import models
from app.db import create_db_engine, migrate
from app.publication import PublicationCoordinator
from app.worker.execution import CpuAudioService
from sqlalchemy import select
from sqlalchemy.orm import Session


def _lane_world(tmp_path, statuses):
    """Un song local y un job ``post.audio`` por cada estado dado."""
    song = "01K70000000000000000000001"
    database = Path(tmp_path) / "data" / "studio.sqlite"
    database.parent.mkdir(parents=True)
    migrate(database)
    engine = create_db_engine(database)
    ids = [f"01K7000000000000000000010{index}" for index in range(len(statuses))]
    with Session(engine) as session, session.begin():
        owner = session.scalar(
            select(models.User).where(models.User.name == "local")
        ).id
        session.add(models.Song(id=song, owner_id=owner, title="CPU"))
        for job_id, status in zip(ids, statuses, strict=True):
            deleted = status.endswith("+deleted")
            session.add(
                models.Job(
                    id=job_id,
                    owner_id=owner,
                    song_id=song,
                    task="post.audio",
                    lane="cpu",
                    status=status.split("+")[0],
                    attempt=0 if status == "queued" else 1,
                    request={"inputs": []},
                    deleted_at="2026-10-22T00:00:00Z" if deleted else None,
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
    return engine, service, ids


def test_ca2_interrupted_posts_do_not_block_the_cpu_lane(tmp_path):
    engine, service, ids = _lane_world(
        tmp_path, ["interrupted", "interrupted", "queued"]
    )
    try:
        assert service.claim_job(ids[2]) is True
    finally:
        engine.dispose()


def test_ca2_deleted_running_job_is_not_occupying_a_slot(tmp_path):
    engine, service, ids = _lane_world(
        tmp_path, ["running+deleted", "running", "queued"]
    )
    try:
        assert service.claim_job(ids[2]) is True
    finally:
        engine.dispose()


def test_ca2_two_live_running_jobs_still_fill_the_lane(tmp_path):
    engine, service, ids = _lane_world(tmp_path, ["running", "running", "queued"])
    try:
        assert service.claim_job(ids[2]) is False
    finally:
        engine.dispose()


def test_ca2_interrupted_job_with_live_owner_in_this_process_occupies_a_slot(tmp_path):
    engine, service, ids = _lane_world(
        tmp_path, ["interrupted", "interrupted", "queued"]
    )
    service.job_executions[ids[0]] = "exec-a"
    service.job_executions[ids[1]] = "exec-b"
    try:
        assert service.claim_job(ids[2]) is False
    finally:
        engine.dispose()


def _snapshot(engine):
    from test_worker_publication_invariants import EXECUTION, POST

    with Session(engine) as session:
        job = session.get(models.Job, POST)
        cpu = session.get(models.CpuExecution, EXECUTION)
        return (
            job.status,
            job.error_code,
            job.error,
            job.updated_at,
            cpu.state,
            cpu.revision,
            cpu.cleanup_state,
            cpu.updated_at,
        )


def test_ca5_reconcile_startup_is_idempotent(tmp_path):
    from test_worker_startup_staging import _interrupted_world, _service

    engine, _ = _interrupted_world(tmp_path)
    service = _service(engine, tmp_path)
    try:
        assert service.reconcile_startup() == 1
        first = _snapshot(engine)
        time.sleep(0.01)
        assert service.reconcile_startup() == 0
        assert _snapshot(engine) == first
        assert first[5] == 2  # una sola subida de revision
    finally:
        engine.dispose()


# --- mundo interrumpido con intent reservada ---------------------------------

DEAD = {"leader": 4242, "birth": 7}


def _reserved_world(tmp_path, *, identity=DEAD):
    """post.audio ``running`` con cpu_execution + intent ``reserved`` tras un reinicio."""
    from app.migrations.cpu_publication_invariants import cas
    from test_worker_publication_invariants import (
        EXECUTION,
        INTENT,
        REVISION,
        content,
        insert_raw,
        intent,
    )
    from test_worker_startup_staging import _interrupted_world, _service

    engine, _ = _interrupted_world(tmp_path)
    insert_raw(engine, "publication_intent", intent())
    insert_raw(engine, "publication_intent_revision", content())
    with engine.begin() as connection:
        cas(
            connection,
            "publication_intent",
            INTENT,
            1,
            "reserved",
            active_revision_id=REVISION,
        )
        cas(
            connection,
            "cpu_execution",
            EXECUTION,
            1,
            "prepared",
            process_identity=identity,
        )
    service = _service(engine, tmp_path)
    service._birth_probe = lambda pid: None  # el proceso anterior ya no existe
    assert service.reconcile_startup() == 1
    return engine, service


def _request_cancel(engine):
    from test_worker_publication_invariants import POST

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job SET cancel_requested_at='2026-10-22T00:00:00Z' WHERE id=?",
            (POST,),
        )


def _tmp_dirs(tmp_path):
    from test_worker_publication_invariants import ATTEMPT, EXECUTION, SONG

    root = Path(tmp_path) / "data"
    dirs = {
        "raw": root / "tmp" / ATTEMPT,
        "run": root / "tmp" / "_server_cpu" / EXECUTION,
        "inputs": root / "tmp" / "_server_inputs" / EXECUTION,
        "stage": root / "songs" / SONG / "takes" / f".pending-{EXECUTION}",
    }
    for path in dirs.values():
        path.mkdir(parents=True)
        (path / "x.bin").write_bytes(b"x")
    return dirs


def test_ca3_interrupted_post_can_be_cancelled(tmp_path):
    from test_worker_publication_invariants import EXECUTION, INTENT, POST, TAKE

    engine, service = _reserved_world(tmp_path)
    dirs = _tmp_dirs(tmp_path)
    _request_cancel(engine)
    try:
        assert service.cancel_job(POST) is True
        with Session(engine) as session:
            job = session.get(models.Job, POST)
            cpu = session.get(models.CpuExecution, EXECUTION)
            assert job.status == "cancelled"
            assert (cpu.state, cpu.cleanup_state) == ("cancelled", "confirmed")
            assert session.get(models.PublicationIntent, INTENT).state == "cancelled"
            assert session.get(models.Take, TAKE).status == "cancelled"
        assert not any(path.exists() for path in dirs.values())
    finally:
        engine.dispose()


def test_ca3_cancel_without_proof_of_death_changes_nothing(tmp_path):
    from test_worker_publication_invariants import EXECUTION, POST

    engine, service = _reserved_world(tmp_path)
    service._birth_probe = lambda pid: DEAD["birth"]  # el líder sigue vivo
    dirs = _tmp_dirs(tmp_path)
    _request_cancel(engine)
    try:
        assert service.cancel_job(POST) is False
        with Session(engine) as session:
            assert session.get(models.Job, POST).status == "interrupted"
            assert session.get(models.CpuExecution, EXECUTION).state == "interrupted"
        assert all(path.exists() for path in dirs.values())
    finally:
        engine.dispose()


def test_ca3_cancel_leaves_already_final_intents_alone(tmp_path):
    """Una intent ya final (``failed``) no se reescribe al cancelar."""
    from app.migrations.cpu_publication_invariants import cas
    from test_worker_publication_invariants import INTENT, POST

    engine, service = _reserved_world(tmp_path)
    with engine.begin() as connection:
        cas(
            connection,
            "publication_intent",
            INTENT,
            2,
            "failed",
            error_code="AUDIO_INVALID",
        )
    _request_cancel(engine)
    try:
        assert service.cancel_job(POST) is True
        with Session(engine) as session:
            assert session.get(models.PublicationIntent, INTENT).state == "failed"
            assert session.get(models.Job, POST).status == "cancelled"
    finally:
        engine.dispose()


# --- CA-1: reanudar sobre la misma cpu_execution ------------------------------


def test_ca1_resumable_only_with_proof_of_death(tmp_path):
    from test_worker_publication_invariants import EXECUTION, POST

    engine, service = _reserved_world(tmp_path)
    try:
        assert service.resumable_jobs() == [POST]
        service._birth_probe = lambda pid: DEAD["birth"]  # el líder sigue vivo
        assert service.resumable_jobs() == []
        service._birth_probe = lambda pid: None
        service.owners[EXECUTION] = object()  # dueño vivo en este proceso
        assert service.resumable_jobs() == []
    finally:
        engine.dispose()


def test_ca1_unreadable_identity_or_missing_proc_is_not_a_proof(tmp_path):
    engine, service = _reserved_world(tmp_path, identity={"pid": 1, "birth": "x"})
    try:
        assert service.resumable_jobs() == []

        def no_proc(pid):
            raise OSError("PROC_UNAVAILABLE")

        service._birth_probe = no_proc
        assert service.resumable_jobs() == []
    finally:
        engine.dispose()


def test_ca1_pid_reused_with_other_birth_proves_death(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    service._birth_probe = lambda pid: DEAD["birth"] + 1  # mismo pid, otro proceso
    try:
        assert service.resumable_jobs() == [POST]
    finally:
        engine.dispose()


def test_ca1_never_launched_workload_is_dead_by_definition(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path, identity=None)
    try:
        assert service.resumable_jobs() == [POST]
    finally:
        engine.dispose()


def test_ca1_claim_resume_confirms_custody_and_leases_anew(tmp_path):
    from test_worker_publication_invariants import EXECUTION, POST

    engine, service = _reserved_world(tmp_path)
    with Session(engine) as session:
        before = session.get(models.CpuExecution, EXECUTION)
        old = (before.lease_token, before.supervisor_epoch)
    try:
        assert service.claim_resume(POST) == EXECUTION
        with Session(engine) as session:
            job = session.get(models.Job, POST)
            cpu = session.get(models.CpuExecution, EXECUTION)
            assert (job.status, job.error_code, job.attempt) == ("running", None, 1)
            assert (cpu.state, cpu.cleanup_state) == ("prepared", "confirmed")
            assert cpu.process_identity is None and cpu.error_code is None
            assert (cpu.lease_token, cpu.supervisor_epoch) != old
        # solo una reanudación por job y proceso
        assert service.claim_resume(POST) is None
    finally:
        engine.dispose()


def test_ca1_claim_resume_without_proof_confirms_nothing(tmp_path):
    from test_worker_publication_invariants import EXECUTION, POST

    engine, service = _reserved_world(tmp_path)
    service._birth_probe = lambda pid: DEAD["birth"]
    try:
        assert service.claim_resume(POST) is None
        with Session(engine) as session:
            assert session.get(models.Job, POST).status == "interrupted"
            cpu = session.get(models.CpuExecution, EXECUTION)
            assert (cpu.state, cpu.cleanup_state) == ("interrupted", "unknown")
    finally:
        engine.dispose()


def test_ca1_claim_resume_respects_cancel_and_lane_capacity(tmp_path):
    from test_worker_publication_invariants import POST

    engine, service = _reserved_world(tmp_path)
    _request_cancel(engine)
    try:
        assert service.claim_resume(POST) is None
    finally:
        engine.dispose()


def test_ca1_resume_with_only_final_intents_finishes_the_execution(
    tmp_path, monkeypatch
):
    """Si ninguna intent sigue ``reserved`` no hay nada que reprocesar: se cierra."""
    from app.worker import execution as execution_module

    monkeypatch.setattr(execution_module, "tool", lambda *args: None)

    def write_once(path, payload):  # fsync de directorio no existe en Windows
        with path.open("xb") as stream:
            stream.write(payload)

    monkeypatch.setattr(execution_module, "write_once", write_once)
    from app.migrations.cpu_publication_invariants import cas
    from test_worker_publication_invariants import EXECUTION, INTENT, POST, TAKE

    engine, service = _reserved_world(tmp_path)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE take SET status='failed', error_code='AUDIO_INVALID' WHERE id=?",
            (TAKE,),
        )
        cas(
            connection,
            "publication_intent",
            INTENT,
            2,
            "failed",
            error_code="AUDIO_INVALID",
        )
    try:
        assert service.claim_resume(POST) == EXECUTION
        plan = _plan_from_row(engine)
        results = service.execute(plan, execution_id=EXECUTION, resume=True)
        assert [r.status for r in results] == ["failure"]
        with Session(engine) as session:
            cpu = session.get(models.CpuExecution, EXECUTION)
            assert (cpu.state, cpu.cleanup_state) == ("finished", "confirmed")
            assert cpu.outcome["kind"] == "all_failed"
            assert session.get(models.Job, POST).status == "succeeded"
    finally:
        engine.dispose()


def _plan_from_row(engine):
    from app.worker.contracts import PostPlan
    from test_worker_publication_invariants import EXECUTION

    with Session(engine) as session:
        return PostPlan.model_validate(session.get(models.CpuExecution, EXECUTION).plan)


def test_ca1_runtime_dispatches_resumable_posts_first():
    import asyncio
    from types import SimpleNamespace

    from app.queue.runtime import QueueRuntime

    async def run():
        runtime = object.__new__(QueueRuntime)
        runtime.cpu_workers = {}
        calls = []
        runtime.cpu_service = SimpleNamespace(
            resumable_jobs=lambda: ["resume-1"],
            execute_job=lambda job_id: calls.append(job_id),
        )
        runtime.admission = SimpleNamespace(
            candidates=lambda: [
                SimpleNamespace(id="post-1", task="post.audio"),
                SimpleNamespace(id="post-2", task="post.audio"),
            ]
        )

        async def dbcall(function, *args):
            return function(*args)

        runtime.dbcall = dbcall
        await runtime._dispatch_cpu()
        await asyncio.gather(*runtime.cpu_workers.values())
        assert calls == ["resume-1", "post-1"]  # dos carriles en total

    asyncio.run(run())


def test_ca1_prepare_resume_reuses_run_dir_and_discards_dead_childs_stage(
    tmp_path, monkeypatch
):
    """Las reservadas se reprocesan desde el WAV crudo; el staging a medias se descarta."""
    import json
    from types import SimpleNamespace

    from app.worker import execution as execution_module
    from test_worker_publication_invariants import (
        ATTEMPT,
        EXECUTION,
        POST,
        SONG,
        TAKE,
    )

    engine, service = _reserved_world(tmp_path)
    assert service.claim_resume(POST) == EXECUTION
    from app.worker.contracts import PostPlan

    value = _plan_from_row(engine).model_dump(mode="json")
    # el fixture congela la copia bajo «unit»; un plan real usa el id de ejecución
    value["takes"][0]["copy"]["path"] = f"data/tmp/_server_inputs/{EXECUTION}/0.wav"
    plan = PostPlan.model_validate(value)
    with engine.connect() as connection:
        previous = (
            connection.execute(
                select(models.CpuExecution.__table__).where(
                    models.CpuExecution.id == EXECUTION
                )
            )
            .mappings()
            .one()
        )
    root = Path(tmp_path) / "data"
    raw_wav = root / "tmp" / ATTEMPT / "0.wav"
    raw_wav.parent.mkdir(parents=True)
    raw_wav.write_bytes(b"w" * 100)
    stage_dir = root / "songs" / SONG / "takes" / f".pending-{EXECUTION}" / TAKE
    stage_dir.mkdir(parents=True)
    (stage_dir / "master.flac").write_bytes(b"half written")
    run = root / "tmp" / "_server_cpu" / EXECUTION
    run.mkdir(parents=True)
    (run / "post-plan.json").write_bytes(b"{}")

    fake_hash = SimpleNamespace(
        sha256=lambda payload: SimpleNamespace(hexdigest=lambda: "a" * 64)
    )
    monkeypatch.setattr(execution_module, "hashlib", fake_hash)
    monkeypatch.setattr(service, "_put_receipt", lambda *args: None)
    monkeypatch.setattr(
        execution_module, "canonical_sha256", lambda value: previous["plan_sha256"]
    )
    monkeypatch.setattr(
        execution_module, "canonical_bytes", lambda value: b'{"skip":[]}'
    )
    monkeypatch.setattr(
        execution_module,
        "write_once",
        lambda path, payload: path.write_bytes(payload),
    )
    # el plan en disco difiere del recompuesto: misma identidad, otros bytes
    (run / "post-plan.json").write_bytes(b'{"skip":[]}')
    try:
        _, returned = service._prepare_resume(
            plan,
            EXECUTION,
            dict(previous),
            b'{"skip":[]}',
            {},
            SimpleNamespace(payload=b"{}", digest="d" * 64),
            {},
        )
        assert returned == run
        assert not stage_dir.exists()
        assert (root / "tmp" / "_server_inputs" / EXECUTION / "0.wav").read_bytes() == (
            b"w" * 100
        )
        assert json.loads((run / "resume-skip.json").read_bytes()) == {"skip": []}
        assert service._skipped[EXECUTION] == set()
    finally:
        engine.dispose()
