"""Entradas propias: bytes verificados, staging y writer independientes."""

import asyncio
import hashlib
import json
import os
from pathlib import Path

import pytest
from app.models import Job, Upload, new_id
from app.queue.resolver import Resolver
from sqlalchemy.orm import Session
from test_dispatcher_admission import add, admission
from test_dispatcher_admission import engine as native_engine
from test_queue_resolver import Catalog


@pytest.fixture(name="engine")
def queue_input_engine():
    yield from native_engine.__wrapped__()


def test_queue_inputs_hash_outside_writer_and_eventloop(engine, monkeypatch):
    import sqlite3
    import time

    from app.queue.backends.protocol import Submission
    from app.queue.dispatcher import Dispatcher

    job, owner, _root, _source, _digest, resolver = source_job(engine)
    observations = []
    original = hashlib.file_digest

    def observed_hash(stream, algorithm):
        on_loop = False
        try:
            asyncio.get_running_loop()
            on_loop = True
        except RuntimeError:
            pass
        writable = True
        with sqlite3.connect(engine.url.database, timeout=0) as other:
            try:
                other.execute(
                    "UPDATE snapshot_clock SET revision=revision+1 WHERE id=1"
                )
            except sqlite3.OperationalError:
                writable = False
        time.sleep(0.05)
        observations.append((on_loop, writable))
        return original(stream, algorithm)

    monkeypatch.setattr(hashlib, "file_digest", observed_hash)
    backend = next(iter(resolver.backends.values()))

    async def submit(request):
        return Submission(job_id=request.job_id)

    backend.submit = submit

    async def run():
        await Dispatcher(admission(engine, owner), resolver).dispatch(job.id)

    asyncio.run(run())
    assert observations and all(
        not loop and writable for loop, writable in observations
    ), observations
    (Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / "hash-io-profile.json").write_text(
        json.dumps(observations), encoding="utf-8"
    )


def source_job(engine):
    jid, owner = add(
        engine,
        task="audio.beats",
        request={"params": {}, "mode": "bf16", "seed": 1, "timeout_s": 60},
    )
    root = Path(engine.url.database).parent
    (root / "uploads").mkdir()
    source = root / "uploads/owned.wav"
    source.write_bytes(b"owned input\x00" * 8192)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with Session(engine) as session:
        upload = Upload(
            owner_id=owner,
            kind="audio",
            path="uploads/owned.wav",
            sha256=digest,
            media_type="audio/wav",
            rights="own",
            consent="n_a",
        )
        session.add(upload)
        session.flush()
        job = session.get(Job, jid)
        job.request = dict(
            job.request,
            inputs=[{"role": "master", "ref": {"type": "upload", "id": upload.id}}],
        )
        session.commit()
        session.refresh(job)
        session.expunge(job)
    catalog = Catalog()
    catalog.value["tasks"]["audio.beats"]["inputs"] = [
        {"role": "master", "required": True, "media_types": ["audio/wav"]}
    ]
    return job, owner, root, source, digest, Resolver({"mock": catalog}, data_dir=root)


def test_queue_inputs_actual_owned_wire(engine):
    job, _owner, _root, _source, digest, resolver = source_job(engine)
    resolved = asyncio.run(resolver.resolve(job, engine=engine))
    request, _ = resolved.freeze(new_id())
    assert [i.model_dump(mode="json") for i in request.inputs] == [
        {
            "role": "master",
            "path": "uploads/owned.wav",
            "sha256": digest,
            "media_type": "audio/wav",
        }
    ]


def test_queue_inputs_claim_snapshot_survives_original_mutation(engine):
    job, owner, root, source, digest, resolver = source_job(engine)
    resolved = asyncio.run(resolver.resolve(job, engine=engine))
    claim = admission(engine, owner).reserve(resolved)
    source.write_bytes(b"changed after preparation")
    wire = claim.request.inputs[0] if claim else None
    assert wire is not None and wire.path.startswith("tmp/_server_inputs/")
    assert hashlib.sha256((root / wire.path).read_bytes()).hexdigest() == digest
    assert (root / wire.path).read_bytes() != source.read_bytes()


def test_queue_inputs_staging_real_mutation_before_writer(engine):
    import stat

    import pytest
    from app.queue.resolver import ResolutionError
    from sqlalchemy import event

    job, owner, root, _source, _digest, resolver = source_job(engine)
    resolved = asyncio.run(resolver.resolve(job, engine=engine))
    mutated = []

    def mutate(connection, cursor, statement, params, context, many):
        if statement.startswith("UPDATE snapshot_clock") and not mutated:
            staged = next((root / "tmp/_server_inputs").glob("*/0"))
            staged.chmod(stat.S_IWRITE | stat.S_IREAD)
            staged.write_bytes(b"real mutation before writer")
            mutated.append(staged)

    event.listen(engine, "before_cursor_execute", mutate)
    try:
        with pytest.raises(ResolutionError, match="staging changed"):
            admission(engine, owner).reserve(resolved)
    finally:
        event.remove(engine, "before_cursor_execute", mutate)
    assert mutated and not mutated[0].exists()
    with Session(engine) as session:
        assert session.get(Job, job.id).attempt == 0


def test_queue_inputs_lost_claim_cleans_only_owned_stage(engine):
    job, owner, root, source, digest, resolver = source_job(engine)
    resolved = asyncio.run(resolver.resolve(job, engine=engine))
    with Session(engine) as session:
        session.get(Job, job.id).cancel_requested_at = "2026-10-08T02:00:00Z"
        session.commit()
    assert admission(engine, owner).reserve(resolved) is None
    assert list((root / "tmp/_server_inputs").iterdir()) == []
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


def test_queue_inputs_commit_observation_failure_keeps_durable_inputs(engine):
    from app.models import JobAttempt
    from sqlalchemy import event, select

    job, owner, root, _source, _digest, resolver = source_job(engine)
    resolved = asyncio.run(resolver.resolve(job, engine=engine))

    def failed_observation(session):
        raise RuntimeError("Commit observation interrupted after native commit")

    event.listen(Session, "after_commit", failed_observation)
    try:
        with pytest.raises(RuntimeError, match="Commit observation interrupted"):
            admission(engine, owner).reserve(resolved)
    finally:
        event.remove(Session, "after_commit", failed_observation)
    with Session(engine) as session:
        attempt = session.scalar(select(JobAttempt).where(JobAttempt.job_id == job.id))
        assert attempt is not None and attempt.status == "prepared"
        assert all(
            (root / wire.path).is_file() for wire in attempt.engine_request.inputs
        )
