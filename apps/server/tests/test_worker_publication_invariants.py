"""U2b1: SQLite real; procedencia y terminal sintéticos explícitos, sin runtime."""

import json
import sqlite3
from pathlib import Path

import pytest
from app import models
from app.db import create_db_engine, migrate
from app.worker.contracts import (
    CapturedProvenance,
    PostPlan,
    TakeFailure,
    canonical_sha256,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session
from test_job_attempt_schema import ATTEMPT, JOB, OWNER, SONG, UTC, row
from test_worker_contracts import provenance as synthetic_provenance

POST = "01K70000000000000000000004"
TAKE = "01K70000000000000000000005"
EXECUTION = "01K70000000000000000000006"
INTENT = "01K70000000000000000000007"
REVISION = "01K70000000000000000000008"
OTHER = "01K70000000000000000000009"


def provenance():
    value = synthetic_provenance()
    value.update(
        engine_id="mock",
        task="music.instrumental",
        load={"model_id": "mock", "mode": "bf16"},
    )
    value["descriptor"]["id"] = "mock"
    value["descriptor"]["tasks"]["music.instrumental"] = value["descriptor"][
        "tasks"
    ].pop("music.song")
    value["observed_model"]["model_id"] = "mock"
    return CapturedProvenance.model_validate(value).model_dump(mode="json")


def terminal():
    from app.migrations.job_attempt_invariants import validate_contract

    value = {
        "seq": 1,
        "ts": UTC,
        "job_id": ATTEMPT,
        "type": "done",
        "data": {
            "artifacts": [
                {
                    "output_index": 0,
                    "path": f"tmp/{ATTEMPT}/0.wav",
                    "media_type": "audio/wav",
                    "sha256": "a" * 64,
                    "meta": {"seed": 17},
                }
            ],
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


def authority():
    return {
        "owner_id": OWNER,
        "song_id": SONG,
        "post_job_id": POST,
        "generation_job_id": JOB,
        "winning_attempt_id": ATTEMPT,
        "winning_ordinal": 1,
        "terminal_seq": 1,
        "terminal_sha256": canonical_sha256(terminal()),
        "take_id": TAKE,
        "output_index": 0,
        "seed": 17,
        "provenance_sha256": canonical_sha256(provenance()),
    }


def common(identifier):
    return {
        "id": identifier,
        "owner_id": OWNER,
        "created_at": UTC,
        "updated_at": UTC,
        "deleted_at": None,
    }


def plan():
    source = {
        "path": f"data/tmp/{ATTEMPT}/0.wav",
        "sha256": "a" * 64,
        "media_type": "audio/wav",
        "bytes": 100,
        "duration_s": 1.0,
    }
    return PostPlan.model_validate(
        {
            "version": 1,
            "handler": "post.audio",
            "handler_version": 1,
            "owner_id": OWNER,
            "song_id": SONG,
            "post_job_id": POST,
            "generation_job_id": JOB,
            "request_sha256": canonical_sha256(post_request()),
            "tool_pin_sha256": "b" * 64,
            "provenance": provenance(),
            "takes": [
                {
                    "authority": authority(),
                    "source": source,
                    "copy": {**source, "path": "data/tmp/_server_inputs/unit/0.wav"},
                }
            ],
        }
    ).model_dump(mode="json")


def post_request():
    return {
        "inputs": [
            {"role": "source", "ref": {"type": "job", "id": JOB}, "output_index": 0}
        ]
    }


def execution():
    value = plan()
    return dict(
        **common(EXECUTION),
        job_id=POST,
        ordinal=1,
        handler="post.audio",
        handler_version=1,
        contract_version=1,
        state="prepared",
        revision=1,
        plan=value,
        plan_sha256=canonical_sha256(value),
        outcome=None,
        error_code=None,
        finished_at=None,
        supervisor_epoch="private-epoch",
        lease_token="private-lease",
        process_identity={"pid": 123, "birth": "private"},
        cleanup_state="unknown",
    )


def intent():
    return dict(
        **common(INTENT),
        song_id=SONG,
        take_id=TAKE,
        output_index=0,
        seed=17,
        state="reserved",
        revision=1,
        active_revision_id=None,
        error_code=None,
        committed_at=None,
    )


def content():
    return dict(
        **common(REVISION),
        **{k: v for k, v in authority().items() if k != "owner_id"},
        intent_id=INTENT,
        cpu_execution_id=EXECUTION,
        source_sha256="a" * 64,
        stage_path=f"songs/{SONG}/takes/.pending-{EXECUTION}/{TAKE}",
        final_path=f"songs/{SONG}/takes/{TAKE}",
        package=None,
        package_sha256=None,
        error_code=None,
    )


def package():
    value = {"authority": authority()}
    for role, name, media in (
        ("master", "master.flac", "audio/flac"),
        ("listen", "listen.mp3", "audio/mpeg"),
        ("peaks", "peaks.json", "application/json"),
        ("manifest", "manifest.json", "application/json"),
    ):
        value[role] = {
            "path": f"data/songs/{SONG}/takes/{TAKE}/{name}",
            "sha256": "c" * 64,
            "bytes": 100,
            "media_type": media,
        }
    return value


def insert_raw(engine, table, value):
    encoded = {
        k: json.dumps(v, allow_nan=True)
        if isinstance(v, (dict, list))
        else str(v)
        if k == "seed"
        else v
        for k, v in value.items()
    }
    with sqlite3.connect(engine.url.database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            f'INSERT INTO "{table}" ({",".join(encoded)}) VALUES ({",".join("?" for _ in encoded)})',
            tuple(encoded.values()),
        )


@pytest.fixture
def engine(tmp_path):
    database = tmp_path / "publication.sqlite"
    migrate(database)
    database_engine = create_db_engine(database)
    with Session(database_engine) as session:
        session.add(models.Song(**common(SONG), title="Native SQL synthetic evidence"))
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
            models.JobDependency(**common(OTHER), job_id=POST, depends_on_job_id=JOB)
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
        session.flush()
        value = row()
        value.update(status="succeeded", last_seq=1, terminal=terminal())
        session.add(models.JobAttempt(**value))
        session.commit()
    try:
        yield database_engine
    finally:
        database_engine.dispose()


def attach_provenance(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job_attempt SET provenance=?,provenance_sha256=? WHERE id=?",
            (json.dumps(provenance()), canonical_sha256(provenance()), ATTEMPT),
        )


def test_post_completion_marks_job_and_failed_beat_durable(engine):
    from app.worker.publications import Publisher

    beat = "01K70000000000000000000010"
    with Session(engine) as session:
        session.add(
            models.Job(
                **common(beat),
                song_id=SONG,
                task="audio.beats",
                lane="cpu",
                status="blocked",
                request={
                    "params": {},
                    "inputs": [{"role": "master", "ref": {"type": "take", "id": TAKE}}],
                },
            )
        )
        session.add(
            models.JobDependency(
                **common("01K70000000000000000000011"),
                job_id=beat,
                depends_on_job_id=POST,
            )
        )
        session.commit()

    publisher = Publisher(engine, Path("."), None, None)
    failure = TakeFailure(
        status="failure", take_id=TAKE, output_index=0, code="AUDIO_INVALID"
    )
    with engine.begin() as connection:
        publisher._complete_post(
            connection, PostPlan.model_validate(plan()), (failure,)
        )

    with Session(engine) as session:
        assert session.get(models.Job, POST).status == "succeeded"
        beat_row = session.get(models.Job, beat)
        assert (beat_row.status, beat_row.error_code) == (
            "failed",
            "DEPENDENCY_FAILED",
        )


def reserve(engine):
    attach_provenance(engine)
    insert_raw(engine, "cpu_execution", execution())
    insert_raw(engine, "publication_intent", intent())
    insert_raw(engine, "publication_intent_revision", content())
    from app.migrations.cpu_publication_invariants import cas

    with engine.begin() as connection:
        cas(
            connection,
            "publication_intent",
            INTENT,
            1,
            "reserved",
            active_revision_id=REVISION,
        )


def test_cpu_rejects_engine_lane_sql(engine):
    value = execution()
    value["job_id"] = JOB
    with pytest.raises(sqlite3.IntegrityError, match="CPU|authority"):
        insert_raw(engine, "cpu_execution", value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision", 0),
        ("ordinal", 1.5),
        ("state", "fake"),
        ("plan_sha256", "X" * 64),
        ("plan", {"token": "secret"}),
    ],
)
def test_cpu_sql_contract_invalid(engine, field, value):
    attach_provenance(engine)
    value_row = execution()
    value_row[field] = value
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, "cpu_execution", value_row)


@pytest.mark.parametrize("mutation", ["finite", "secret", "authority", "digest"])
def test_cpu_orm_contract_invalid(engine, mutation):
    value = execution()
    if mutation == "finite":
        value["plan"]["takes"][0]["source"]["duration_s"] = float("inf")
    if mutation == "secret":
        value["plan"]["lease_token"] = "private"
    if mutation == "authority":
        value["plan"]["post_job_id"] = JOB
    if mutation == "digest":
        value["plan_sha256"] = "f" * 64
    with (
        pytest.raises((ValueError, StatementError, IntegrityError)),
        Session(engine) as session,
    ):
        session.add(models.CpuExecution(**value))
        session.flush()


@pytest.mark.parametrize(
    "field,value",
    [
        ("song_id", JOB),
        ("post_job_id", JOB),
        ("generation_job_id", POST),
        ("winning_attempt_id", JOB),
        ("winning_ordinal", 2),
        ("terminal_seq", 2),
        ("terminal_sha256", "f" * 64),
        ("output_index", 1),
        ("seed", 18),
        ("provenance_sha256", "f" * 64),
        ("source_sha256", "f" * 64),
    ],
)
def test_revision_crossrow_fraud_sql(engine, field, value):
    attach_provenance(engine)
    insert_raw(engine, "cpu_execution", execution())
    insert_raw(engine, "publication_intent", intent())
    current = content()
    current[field] = value
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, "publication_intent_revision", current)


def test_missing_provenance_is_typed_and_legacy_allowed(engine):
    from app.migrations.cpu_publication_invariants import (
        PublicationError,
        require_provenance,
    )

    with engine.connect() as connection:
        attempt = dict(
            connection.execute(select(models.JobAttempt.__table__)).mappings().one()
        )
        with pytest.raises(PublicationError) as failure:
            require_provenance(attempt)
        assert failure.value.code == "PROVENANCE_MISSING"


def test_sql_cas_stale_illegal_and_immutable(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import PublicationError, cas

    with engine.begin() as connection:
        assert cas(connection, "cpu_execution", EXECUTION, 1, "running") == 2
        assert cas(connection, "cpu_execution", EXECUTION, 1, "running") == 2
        with pytest.raises(PublicationError, match="CAS"):
            cas(connection, "cpu_execution", EXECUTION, 1, "draining")
        with pytest.raises((PublicationError, IntegrityError)):
            cas(connection, "publication_intent", INTENT, 2, "committed")
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE cpu_execution SET plan_sha256=? WHERE id=?", ("f" * 64, EXECUTION)
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET terminal_seq=2 WHERE id=?",
            (REVISION,),
        )


def test_package_write_once_and_cancel_guard(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import cas

    p = package()
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET package=?,package_sha256=? WHERE id=?",
            (json.dumps(p), canonical_sha256(p), REVISION),
        )
        cas(connection, "publication_intent", INTENT, 2, "prepared")
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET package_sha256=? WHERE id=?",
            ("f" * 64, REVISION),
        )
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE job SET cancel_requested_at=? WHERE id=?", (UTC, POST)
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        cas(connection, "publication_intent", INTENT, 3, "renamed")


def test_retry_same_output_preserves_history(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import cas

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET error_code='AUDIO_INVALID' WHERE id=?",
            (REVISION,),
        )
        connection.exec_driver_sql(
            "UPDATE take SET status='failed',error_code='AUDIO_INVALID' WHERE id=?",
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
        # Une nouvelle identité de contenu doit avoir une autre génération/attempt;
        # la même sortie échouée ne rencontre aucune unicité globale winner/index.
        connection.exec_driver_sql(
            "UPDATE cpu_execution SET state='interrupted',revision=2 WHERE id=?",
            (EXECUTION,),
        )
    # A distinct intent cannot claim the same take, even after failure.
    current = intent()
    current["id"] = OTHER
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, "publication_intent", current)
    with engine.connect() as connection:
        assert (
            connection.exec_driver_sql(
                "SELECT error_code FROM publication_intent_revision WHERE id=?",
                (REVISION,),
            ).scalar_one()
            == "AUDIO_INVALID"
        )


def test_parent_mutation_cannot_invalidate_frozen_authority(engine):
    reserve(engine)
    for statement, params in [
        ("UPDATE take SET seed='18' WHERE id=?", (TAKE,)),
        ("UPDATE job SET task='audio.beats' WHERE id=?", (POST,)),
        ("UPDATE job_attempt SET last_seq=2 WHERE id=?", (ATTEMPT,)),
    ]:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.exec_driver_sql(statement, params)


def test_retry_adopts_new_content_without_erasing_old_failure(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import cas

    ids = ["01K700" + str(i).zfill(20) for i in range(10, 15)]
    gen, post, winner, cpu, revision = ids
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET error_code='AUDIO_INVALID' WHERE id=?",
            (REVISION,),
        )
        connection.exec_driver_sql(
            "UPDATE take SET status='failed',error_code='AUDIO_INVALID' WHERE id=?",
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
    with Session(engine) as session:
        session.add(
            models.Job(
                **common(gen),
                song_id=SONG,
                task="music.instrumental",
                lane="gpu",
                status="succeeded",
                attempt=1,
                request={"seed": 17},
            )
        )
        req = post_request()
        req["inputs"][0]["ref"]["id"] = gen
        session.add(
            models.Job(
                **common(post),
                song_id=SONG,
                task="post.audio",
                lane="cpu",
                status="running",
                attempt=1,
                request=req,
            )
        )
        session.flush()
        session.add(
            models.JobDependency(
                **common(models.new_id()), job_id=post, depends_on_job_id=gen
            )
        )
        session.get(models.Take, TAKE).job_id = gen
        value = row()
        value.update(
            id=winner,
            job_id=gen,
            status="succeeded",
            last_seq=1,
            terminal=terminal(),
            provenance=provenance(),
            provenance_sha256=canonical_sha256(provenance()),
        )
        value["engine_request"]["job_id"] = winner
        value["engine_request"]["output_dir"] = "tmp/" + winner
        value["terminal"]["job_id"] = winner
        value["terminal"]["data"]["artifacts"][0]["path"] = f"tmp/{winner}/0.wav"
        session.add(models.JobAttempt(**value))
        session.commit()
    p = plan()
    p.update(
        post_job_id=post, generation_job_id=gen, request_sha256=canonical_sha256(req)
    )
    a = p["takes"][0]["authority"]
    a.update(
        post_job_id=post,
        generation_job_id=gen,
        winning_attempt_id=winner,
        terminal_sha256=canonical_sha256(value["terminal"]),
    )
    p["takes"][0]["source"]["path"] = f"data/tmp/{winner}/0.wav"
    ex = execution()
    ex.update(id=cpu, job_id=post, plan=p, plan_sha256=canonical_sha256(p))
    insert_raw(engine, "cpu_execution", ex)
    c = content()
    c.update(
        id=revision,
        cpu_execution_id=cpu,
        post_job_id=post,
        generation_job_id=gen,
        winning_attempt_id=winner,
        terminal_sha256=a["terminal_sha256"],
        stage_path=f"songs/{SONG}/takes/.pending-{cpu}/{TAKE}",
    )
    insert_raw(engine, "publication_intent_revision", c)
    with engine.begin() as connection:
        assert (
            cas(
                connection,
                "publication_intent",
                INTENT,
                3,
                "reserved",
                active_revision_id=revision,
                error_code=None,
            )
            == 4
        )
        assert connection.exec_driver_sql(
            "SELECT id,error_code FROM publication_intent_revision ORDER BY id"
        ).all() == [(REVISION, "AUDIO_INVALID"), (revision, None)]
    from app import snapshots

    document = snapshots.project(engine, SONG)
    snapshots.validate(document, Path(engine.url.database).parent)
    destination = Path(engine.url.database).parent / "retry-restored.sqlite"
    snapshots.restore_new(destination, document, destination.parent)
    restored = create_db_engine(destination)
    try:
        assert (
            snapshots.project(restored, SONG)["rows"]["publication_intent_revision"]
            == document["rows"]["publication_intent_revision"]
        )
    finally:
        restored.dispose()


def test_cpu_unknown_custody_cannot_finish_or_resume(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import cas

    with engine.begin() as connection:
        cas(connection, "cpu_execution", EXECUTION, 1, "running")
        cas(connection, "cpu_execution", EXECUTION, 2, "draining")
    with pytest.raises(IntegrityError), engine.begin() as connection:
        cas(
            connection,
            "cpu_execution",
            EXECUTION,
            3,
            "finished",
            outcome={
                "kind": "all_failed",
                "ready_take_ids": [],
                "failed_take_ids": [TAKE],
            },
        )
    with engine.begin() as connection:
        cas(connection, "cpu_execution", EXECUTION, 3, "interrupted")
    with pytest.raises(IntegrityError), engine.begin() as connection:
        cas(connection, "cpu_execution", EXECUTION, 4, "prepared")


def test_legacy_ready_take_cannot_acquire_new_intent(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE take SET status='ready' WHERE id=?", (TAKE,))
    with pytest.raises(sqlite3.IntegrityError):
        insert_raw(engine, "publication_intent", intent())


@pytest.mark.parametrize(
    "fraud",
    ["foreign_owner", "foreign_seed", "foreign_ordinal", "unsafe_path", "finite"],
)
def test_prepared_package_sql_rejects_contradictions(engine, fraud):
    reserve(engine)
    p = package()
    if fraud == "foreign_owner":
        p["authority"]["owner_id"] = JOB
    if fraud == "foreign_seed":
        p["authority"]["seed"] = 18
    if fraud == "foreign_ordinal":
        p["authority"]["winning_ordinal"] = 2
    if fraud == "unsafe_path":
        p["master"]["path"] = "../outside.flac"
    if fraud == "finite":
        p["master"]["bytes"] = float("inf")
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET package=?,package_sha256=? WHERE id=?",
            (json.dumps(p), "c" * 64, REVISION),
        )


def test_sql_outcome_is_closed_and_finite(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import cas

    with pytest.raises(IntegrityError), engine.begin() as connection:
        cas(
            connection,
            "cpu_execution",
            EXECUTION,
            1,
            "prepared",
            outcome={"kind": "wrong", "ready_take_ids": [], "failed_take_ids": [TAKE]},
        )


def prepared(engine):
    reserve(engine)
    from app.migrations.cpu_publication_invariants import cas

    p = package()
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE publication_intent_revision SET package=?,package_sha256=? WHERE id=?",
            (json.dumps(p), canonical_sha256(p), REVISION),
        )
        cas(connection, "publication_intent", INTENT, 2, "prepared")
        cas(connection, "publication_intent", INTENT, 3, "renamed")


def test_committed_requires_exact_assets(engine):
    prepared(engine)
    from app.migrations.cpu_publication_invariants import cas

    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE take SET status='ready' WHERE id=?", (TAKE,))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        cas(connection, "publication_intent", INTENT, 4, "committed", committed_at=UTC)


def test_orm_plan_rechecks_real_winner_terminal_digest(engine):
    attach_provenance(engine)
    value = execution()
    value["plan"]["takes"][0]["authority"]["terminal_sha256"] = "f" * 64
    value["plan_sha256"] = canonical_sha256(value["plan"])
    with (
        pytest.raises((ValueError, StatementError, IntegrityError)),
        Session(engine) as session,
    ):
        session.add(models.CpuExecution(**value))
        session.flush()


def test_cpu_orm_roundtrip_uses_accepted_immutable_plan(engine):
    attach_provenance(engine)
    with Session(engine) as session:
        session.add(models.CpuExecution(**execution()))
        session.commit()
        session.expire_all()
        stored = session.get(models.CpuExecution, EXECUTION)
        assert isinstance(stored.plan, PostPlan)
        assert stored.plan.takes[0].authority.take_id == TAKE
        assert stored.plan.provenance.reported_image_digest is None
        assert stored.plan.provenance.expected_image_digest is None
        with pytest.raises(ValueError):
            stored.plan.handler_version = 2


def test_ready_assets_history_and_terminal_outcome_are_preserved(engine):
    prepared(engine)
    from app.migrations.cpu_publication_invariants import cas

    p = package()
    with Session(engine) as session:
        for role in ("master", "listen", "peaks", "manifest"):
            f = p[role]
            session.add(
                models.Asset(
                    **common(models.new_id()),
                    subject_type="take",
                    subject_id=TAKE,
                    role=role,
                    path=f["path"][5:],
                    sha256=f["sha256"],
                    media_type=f["media_type"],
                    bytes=f["bytes"],
                    meta={},
                )
            )
        session.get(models.Take, TAKE).status = "ready"
        session.commit()
    with engine.begin() as connection:
        cas(connection, "publication_intent", INTENT, 4, "committed", committed_at=UTC)
        cas(connection, "cpu_execution", EXECUTION, 1, "running")
        cas(
            connection,
            "cpu_execution",
            EXECUTION,
            2,
            "draining",
            cleanup_state="confirmed",
            lease_token=None,
            process_identity=None,
        )
        cas(
            connection,
            "cpu_execution",
            EXECUTION,
            3,
            "finished",
            outcome={
                "kind": "all_ready",
                "ready_take_ids": [TAKE],
                "failed_take_ids": [],
            },
            finished_at=UTC,
        )
    for statement in (
        "UPDATE take SET status='failed'",
        "UPDATE asset SET bytes=101",
        "DELETE FROM publication_intent_revision",
    ):
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.exec_driver_sql(statement)
    from app import snapshots

    document = snapshots.project(engine, SONG)
    destination = Path(engine.url.database).parent / "ready-restored.sqlite"
    snapshots.restore_new(destination, document, destination.parent)
    restored = create_db_engine(destination)
    try:
        assert snapshots.project(restored, SONG) == document
    finally:
        restored.dispose()
