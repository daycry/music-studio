"""T-04 I2: reanudar con intents ya empaquetadas (``prepared``) y otras ``reserved``.

Dos takes: la A quedó ``prepared`` (paquete y staging conservados por T-05) y la B
``reserved``. La reanudación debe republicar la A desde su staging, excluirla del
hijo con ``resume-skip.json`` y reprocesar solo la B. El hijo valida ese fichero.
Todo con el código real (hash y escritura reales); solo se sustituyen el
``fsync`` de directorio (inexistente en Windows), el lanzamiento del hijo Linux y
la lectura del manifiesto/recibo histórico, que pertenecen al Linux real.
"""

import json
import queue
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import models
from app.db import create_db_engine, migrate
from app.migrations.cpu_publication_invariants import cas
from app.publication import PublicationCoordinator
from app.worker import execution as execution_module
from app.worker import packages
from app.worker.contracts import PostPlan, TakeFailure, TakeSuccess, canonical_sha256
from app.worker.execution import CpuAudioService
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_worker_publication_invariants import (
    ATTEMPT,
    EXECUTION,
    INTENT,
    JOB,
    OWNER,
    POST,
    REVISION,
    SONG,
    TAKE,
    attach_provenance,
    common,
    execution,
    insert_raw,
    plan,
    post_request,
    row,
)
from test_worker_publication_invariants import (
    authority as base_authority,
)

TAKE_B = "01K70000000000000000000020"
INTENT_B = "01K70000000000000000000021"
REVISION_B = "01K70000000000000000000022"
WAV = {0: b"A" * 64, 1: b"B" * 64}
DEAD = {"leader": 4242, "birth": 7}


def _sha(payload):
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def _terminal():
    from app.migrations.job_attempt_invariants import validate_contract

    artifacts = [
        {
            "output_index": index,
            "path": f"tmp/{ATTEMPT}/{index}.wav",
            "media_type": "audio/wav",
            "sha256": _sha(WAV[index]),
            "meta": {"seed": 17},
        }
        for index in (0, 1)
    ]
    value = {
        "seq": 1,
        "ts": "2026-10-07T00:00:00.000000Z",
        "job_id": ATTEMPT,
        "type": "done",
        "data": {
            "artifacts": artifacts,
            "telemetry": {
                "load_s": 0.0,
                "run_s": 1.0,
                "vram_peak_mb": 0,
                "vram_cap_mb": 0,
                "spilled": False,
                "mode": "bf16",
                "model_revision": "pinned",
            },
        },
    }
    return validate_contract(value, "event").model_dump(mode="json")


def _authority(take_id, index, terminal):
    return dict(
        base_authority(),
        take_id=take_id,
        output_index=index,
        terminal_sha256=canonical_sha256(terminal),
    )


def _plan(terminal):
    value = plan()
    entries = []
    for index, take_id in ((0, TAKE), (1, TAKE_B)):
        source = {
            "path": f"data/tmp/{ATTEMPT}/{index}.wav",
            "sha256": _sha(WAV[index]),
            "media_type": "audio/wav",
            "bytes": len(WAV[index]),
            "duration_s": 1.0,
        }
        entries.append(
            {
                "authority": _authority(take_id, index, terminal),
                "source": source,
                "copy": {
                    **source,
                    "path": f"data/tmp/_server_inputs/{EXECUTION}/{index}.wav",
                },
            }
        )
    value["takes"] = entries
    return PostPlan.model_validate(value).model_dump(mode="json")


def _package(take_id, index, terminal):
    value = {"authority": _authority(take_id, index, terminal)}
    for role, name, media in (
        ("master", "master.flac", "audio/flac"),
        ("listen", "listen.mp3", "audio/mpeg"),
        ("peaks", "peaks.json", "application/json"),
        ("manifest", "manifest.json", "application/json"),
    ):
        value[role] = {
            "path": f"data/songs/{SONG}/takes/{take_id}/{name}",
            "sha256": "c" * 64,
            "bytes": 100,
            "media_type": media,
        }
    return value


def two_take_world(tmp_path):
    database = Path(tmp_path) / "data" / "studio.sqlite"
    database.parent.mkdir(parents=True)
    migrate(database)
    engine = create_db_engine(database)
    terminal = _terminal()
    with Session(engine) as session:
        session.add(models.Song(**common(SONG), title="two takes"))
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
        session.flush()
        session.add(
            models.JobDependency(
                **common("01K70000000000000000000009"),
                job_id=POST,
                depends_on_job_id=JOB,
            )
        )
        for index, take_id in ((0, TAKE), (1, TAKE_B)):
            session.add(
                models.Take(
                    **common(take_id),
                    song_id=SONG,
                    job_id=JOB,
                    status="queued",
                    batch_id=JOB,
                    variant_index=index,
                    root_id=take_id,
                    derivation="original",
                    task="music.instrumental",
                    model_id="mock",
                    model_version="1.5",
                    seed=17,
                    commercial_use=True,
                )
            )
        session.flush()
        attempt = row()
        attempt.update(status="succeeded", last_seq=1, terminal=terminal)
        session.add(models.JobAttempt(**attempt))
        session.commit()
    attach_provenance(engine)
    value = _plan(terminal)
    insert_raw(
        engine,
        "cpu_execution",
        dict(
            execution(),
            plan=value,
            plan_sha256=canonical_sha256(value),
            process_identity=None,
        ),
    )
    for index, take_id, intent_id, revision_id in (
        (0, TAKE, INTENT, REVISION),
        (1, TAKE_B, INTENT_B, REVISION_B),
    ):
        auth = _authority(take_id, index, terminal)
        insert_raw(
            engine,
            "publication_intent",
            dict(
                **common(intent_id),
                song_id=SONG,
                take_id=take_id,
                output_index=index,
                seed=17,
                state="reserved",
                revision=1,
                active_revision_id=None,
                error_code=None,
                committed_at=None,
            ),
        )
        insert_raw(
            engine,
            "publication_intent_revision",
            dict(
                **common(revision_id),
                **{k: v for k, v in auth.items() if k != "owner_id"},
                intent_id=intent_id,
                cpu_execution_id=EXECUTION,
                source_sha256=_sha(WAV[index]),
                stage_path=f"songs/{SONG}/takes/.pending-{EXECUTION}/{take_id}",
                final_path=f"songs/{SONG}/takes/{take_id}",
                package=None,
                package_sha256=None,
                error_code=None,
            ),
        )
        with engine.begin() as connection:
            cas(
                connection,
                "publication_intent",
                intent_id,
                1,
                "reserved",
                active_revision_id=revision_id,
            )
    # La A queda empaquetada (prepared); la B sigue reserved.
    package = _package(TAKE, 0, terminal)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET package=?,package_sha256=? WHERE id=?",
            (json.dumps(package), canonical_sha256(package), REVISION),
        )
        cas(connection, "publication_intent", INTENT, 2, "prepared")
    service = CpuAudioService(
        engine,
        tmp_path,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=Path(tmp_path) / "ffmpeg",
        owner_id=OWNER,
    )
    service._birth_probe = lambda pid: None
    service._group_probe = lambda leader: False
    assert service.reconcile_startup() == 1
    return engine, service


@pytest.fixture
def world(tmp_path, monkeypatch):
    # El fsync de un directorio no existe en Windows; el resto de write_once es real.
    monkeypatch.setattr(packages, "fsync_directory", lambda path: None)
    monkeypatch.setattr(execution_module, "tool", lambda *args: None)
    engine, service = two_take_world(tmp_path)
    root = Path(tmp_path) / "data"
    for index, payload in WAV.items():
        path = root / "tmp" / ATTEMPT / f"{index}.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    takes = root / "songs" / SONG / "takes" / f".pending-{EXECUTION}"
    (takes / TAKE).mkdir(parents=True)
    (takes / TAKE / "master.flac").write_bytes(b"packaged by the dead child")
    (takes / TAKE_B).mkdir()
    (takes / TAKE_B / "master.flac").write_bytes(b"half written")
    run = root / "tmp" / "_server_cpu" / EXECUTION
    run.mkdir(parents=True)
    try:
        yield SimpleNamespace(
            engine=engine, service=service, root=root, takes=takes, run=run
        )
    finally:
        engine.dispose()


def _history(service):
    """El recibo histórico y el manifiesto viven en Linux real: aquí se aceptan."""
    service.publisher.receipt_from_history = (
        lambda plan, execution_id, raw, entries=None: (
            {},
            "d" * 64,
        )
    )


def _plan_row(engine):
    with Session(engine) as session:
        return PostPlan.model_validate(session.get(models.CpuExecution, EXECUTION).plan)


def test_i2_claim_resume_keeps_the_packaged_intent_and_marks_it_for_skip(world):
    assert world.service.claim_resume(POST) == EXECUTION
    with Session(world.engine) as session:
        assert session.get(models.PublicationIntent, INTENT).state == "prepared"
        assert session.get(models.PublicationIntent, INTENT_B).state == "reserved"
        assert session.get(models.CpuExecution, EXECUTION).state == "prepared"


def test_i2_prepare_resume_skips_the_packaged_take_and_cleans_only_the_pending(world):
    _history(world.service)
    assert world.service.claim_resume(POST) == EXECUTION
    plan = _plan_row(world.engine)
    with world.engine.connect() as connection:
        previous = (
            connection.execute(
                select(models.CpuExecution.__table__).where(
                    models.CpuExecution.id == EXECUTION
                )
            )
            .mappings()
            .one()
        )
    from audio_post.private_context import PreparedContext

    ctx = PreparedContext(value={}, payload=b"{}", digest="d" * 64)
    _, run = world.service._prepare_resume(
        plan, EXECUTION, dict(previous), packages.canonical_bytes(plan), {}, ctx, {}
    )
    assert run == world.run
    marker = json.loads((run / "resume-skip.json").read_bytes())
    assert marker == {"skip": [TAKE]}
    assert (world.takes / TAKE / "master.flac").read_bytes() == (
        b"packaged by the dead child"
    )  # el staging empaquetado lo conserva T-05
    assert not (world.takes / TAKE_B).exists()  # la salida a medias se descarta
    copies = world.root / "tmp" / "_server_inputs" / EXECUTION
    assert sorted(p.name for p in copies.iterdir()) == ["1.wav"]  # solo la pendiente
    assert (copies / "1.wav").read_bytes() == WAV[1]
    assert world.service._skipped[EXECUTION] == {TAKE}


class FakeGroup:
    launched = []  # noqa: RUF012

    def __init__(self, mode, run, execution_id, epoch, **kwargs):
        FakeGroup.launched.append(
            {
                "run": Path(run),
                "skip": json.loads((Path(run) / "resume-skip.json").read_bytes()),
                "pending_stage_exists": (
                    Path(run).parents[2]
                    / "songs"
                    / SONG
                    / "takes"
                    / f".pending-{execution_id}"
                    / TAKE_B
                ).exists(),
            }
        )
        self.disposition = {"leader": 999, "birth": 1}

    def contain_unknown(self):
        pass


def _fake_owner(messages):
    class FakeOwner:
        def __init__(self, group, execution_id, epoch, deadline):
            self.done, self.messages = threading.Event(), queue.Queue()
            self.finalizer = SimpleNamespace(ident=None)
            self.receipt = SimpleNamespace(release_gate=True)

        def start(self):
            for message in messages:
                self.messages.put(message)
            self.done.set()

        def receive(self, timeout):
            return self.messages.get(timeout=timeout)

        def join(self, timeout):
            return self.receipt

        def cancel(self):
            pass

    return FakeOwner


def _failure_message():
    return {
        "kind": "take_result",
        "payload": TakeFailure(
            status="failure", take_id=TAKE_B, output_index=1, code="AUDIO_INVALID"
        ).model_dump(mode="json"),
    }


def _install(world, monkeypatch, messages):
    FakeGroup.launched = []
    monkeypatch.setattr(execution_module, "LinuxGroup", FakeGroup)
    monkeypatch.setattr(execution_module, "Owner", _fake_owner(messages))
    _history(world.service)
    # La captura del contexto privado (letra, autoría) es ajena a esta reanudación.
    from audio_post.private_context import PreparedContext

    world.service.publisher.capture_context = lambda connection, plan: ({}, {})
    world.service.publisher.revalidate_context = lambda *args: None
    monkeypatch.setattr(
        execution_module,
        "prepare_context_once",
        lambda context: PreparedContext(value={}, payload=b"{}", digest="d" * 64),
    )
    world.service._put_receipt = lambda *args: None
    republished = []
    world.service.publisher.reconcile = lambda plan, execution_id: republished.append(
        execution_id
    )

    def stored(plan, execution_id):
        with Session(world.engine) as session:
            package = session.get(models.PublicationIntentRevision, REVISION).package
        results = [
            TakeSuccess(
                status="success",
                take_id=TAKE,
                output_index=0,
                package=package,
                duration_s=1.0,
                integrated_lufs=-14.0,
                true_peak_dbtp=-1.5,
            )
        ]
        return tuple(results)

    world.service._stored_results = stored
    return republished


def test_i2_resume_reprocesses_only_the_reserved_take_and_merges_results(
    world, monkeypatch
):
    republished = _install(world, monkeypatch, [_failure_message()])
    assert world.service.claim_resume(POST) == EXECUTION
    results = world.service.execute(
        _plan_row(world.engine), execution_id=EXECUTION, resume=True
    )
    assert len(FakeGroup.launched) == 1
    launched = FakeGroup.launched[0]
    assert launched["skip"] == {"skip": [TAKE]}
    assert launched["pending_stage_exists"] is False
    assert republished == [EXECUTION]  # la A se republica desde su staging
    assert {r.take_id: r.status for r in results} == {
        TAKE_B: "failure",
        TAKE: "success",
    }
    with Session(world.engine) as session:
        cpu = session.get(models.CpuExecution, EXECUTION)
        assert (cpu.state, cpu.cleanup_state) == ("finished", "confirmed")
        assert cpu.outcome["kind"] == "mixed"
        assert session.get(models.PublicationIntent, INTENT_B).state == "failed"
        assert session.get(models.Job, POST).status == "succeeded"


def test_i2_missing_result_for_the_pending_take_keeps_the_execution_interrupted(
    world, monkeypatch
):
    _install(world, monkeypatch, [])
    assert world.service.claim_resume(POST) == EXECUTION
    with pytest.raises(ValueError, match="CPU_CUSTODY_UNKNOWN"):
        world.service.execute(
            _plan_row(world.engine), execution_id=EXECUTION, resume=True
        )
    with Session(world.engine) as session:
        assert session.get(models.CpuExecution, EXECUTION).state == "interrupted"
        assert session.get(models.PublicationIntent, INTENT).state == "prepared"


def test_i2_stored_results_short_of_the_skipped_takes_require_recovery(
    world, monkeypatch
):
    _install(world, monkeypatch, [_failure_message()])
    world.service._stored_results = lambda plan, execution_id: ()
    assert world.service.claim_resume(POST) == EXECUTION
    with pytest.raises(ValueError, match="CPU_EXECUTION_REQUIRES_RECOVERY"):
        world.service.execute(
            _plan_row(world.engine), execution_id=EXECUTION, resume=True
        )


# --- el hijo valida el fichero de exclusión -----------------------------------


def _marker(tmp_path, text):
    path = Path(tmp_path) / "resume-skip.json"
    path.write_text(text, encoding="utf-8")
    return Path(tmp_path)


def test_i2_child_reads_a_valid_skip_file(tmp_path):
    plan = PostPlan.model_validate(_plan(_terminal()))
    folder = _marker(tmp_path, json.dumps({"skip": [TAKE]}))
    assert packages.read_resume_skip(folder, plan) == {TAKE}


def test_i2_child_without_skip_file_skips_nothing(tmp_path):
    plan = PostPlan.model_validate(_plan(_terminal()))
    assert packages.read_resume_skip(Path(tmp_path), plan) == set()


@pytest.mark.parametrize(
    "text",
    [
        json.dumps({"skip": ["01K7FOREIGN0000000000000A"]}),
        json.dumps({"skip": [TAKE], "extra": 1}),
        json.dumps({"skip": [TAKE, TAKE]}),
        json.dumps({"skip": TAKE}),
        json.dumps([TAKE]),
        '{"skip": [], "skip": []}',
    ],
)
def test_i2_child_rejects_a_forged_skip_file(tmp_path, text):
    plan = PostPlan.model_validate(_plan(_terminal()))
    folder = _marker(tmp_path, text)
    with pytest.raises(ValueError, match="PROVENANCE_MISMATCH"):
        packages.read_resume_skip(folder, plan)
