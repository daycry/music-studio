"""Letra propia capturada de SQLite y cómputo WAV/FFmpeg real en Linux."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import models
from app.db import create_db_engine, migrate
from app.publication import PublicationCoordinator
from app.queue.chains import validate_lyrics
from app.queue.synthetic_registry import MOCK_ORIGIN, packaged_mock_registry
from app.worker.contracts import CapturedProvenance, PostPlan, canonical_sha256
from app.worker.execution import CpuAudioService
from audio_post.manifest import verify_manifest
from audio_post.private_context import verify_private_context
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_job_attempt_schema import ATTEMPT, JOB, OWNER, SONG, row
from test_worker_actual_execution import RecordingBus, physical_wav
from test_worker_publication_invariants import (
    EXECUTION,
    POST,
    TAKE,
    common,
    post_request,
    terminal,
)

LYRICS = "01K70000000000000000000012"
TEXT = "Texto ficticio privado de prueba\nSegunda línea sin normalizar."


@pytest.fixture
def song_actual(tmp_path, request):
    import os
    import sys

    assert sys.platform == "linux"
    options = getattr(request, "param", 0)
    output_index = (
        options if isinstance(options, int) else options.get("output_index", 0)
    )
    n_outputs = output_index + 1
    root = tmp_path / "song_actual"
    root.mkdir()
    source = root / f"data/tmp/{ATTEMPT}/{output_index}.wav"
    physical_wav(source)
    if isinstance(options, dict) and options.get("invalid_audio"):
        source.write_bytes(b"Authorized artifact bytes that are not audio")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    ffmpeg = Path(os.environ["STUDIO_ACTUAL_FFMPEG"])
    assert (
        hashlib.sha256(ffmpeg.read_bytes()).hexdigest()
        == os.environ["STUDIO_ACTUAL_FFMPEG_SHA"]
    )
    pin = json.loads(Path("/studio/tools/ffmpeg-linux.lock.json").read_text())
    backend = SimpleNamespace(origin=MOCK_ORIGIN)
    registry = packaged_mock_registry({"mock": backend}, {"mock": MOCK_ORIGIN})
    entry = registry.entries[0]
    provenance = CapturedProvenance(
        descriptor=entry.descriptor,
        engine_id="mock",
        engine_version="0.1.0",
        contract_version="1",
        task="music.song",
        load={"model_id": "mock", "mode": "cpu"},
        observed_model={"model_id": "mock", "mode": "cpu"},
        expected_image_digest=None,
        reported_image_digest=None,
        evidence_kind="synthetic",
        synthetic_binding=entry.binding,
    )
    registry.rebind(provenance, backend=backend)
    event = terminal()
    event["data"]["artifacts"][0].update(
        output_index=output_index, path=f"tmp/{ATTEMPT}/{output_index}.wav"
    )
    event["data"]["artifacts"][0]["meta"]["seed"] = 17 + output_index
    event["data"]["artifacts"][0]["sha256"] = source_sha
    event["data"]["telemetry"].update(mode="cpu", model_revision="synthetic-v1")
    params = {
        "duration_s": 2,
        "lyrics": TEXT,
        "style": "Estilo ficticio privado",
        "lyrics_declaration": "licensed",
        "lyrics_sha256": "b" * 64,
        "lyrics_version_id": "01K70000000000000000000013",
    }
    actual_post_request = post_request()
    actual_post_request["inputs"][0]["output_index"] = output_index
    database = root / "data/studio.sqlite"
    migrate(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.add(models.Song(**common(SONG), title="Canción sintética de prueba"))
        session.flush()
        session.add(
            models.LyricsVersion(
                **common(LYRICS),
                song_id=SONG,
                text=TEXT,
                source="manual",
                declaration="own",
                sha256=hashlib.sha256(TEXT.encode()).hexdigest(),
            )
        )
        session.add(
            models.Job(
                **common(JOB),
                song_id=SONG,
                task="music.song",
                lane="cpu",
                status="succeeded",
                attempt=1,
                request={"seed": 17, "n_outputs": n_outputs, "params": dict(params)},
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
                request=actual_post_request,
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
        session.add(
            models.Take(
                **common(TAKE),
                song_id=SONG,
                job_id=JOB,
                status="queued",
                batch_id=JOB,
                variant_index=output_index,
                root_id=TAKE,
                derivation="original",
                task="music.song",
                model_id="mock",
                model_version="1",
                seed=17 + output_index,
                params=dict(params),
                commercial_use=True,
                lyrics_version_id=LYRICS,
            )
        )
        session.flush()
        attempt = row()
        attempt.update(
            status="succeeded",
            last_seq=1,
            terminal=event,
            mode="cpu",
            load_options={"model_id": "mock", "mode": "cpu"},
            provenance=provenance,
            provenance_sha256=canonical_sha256(provenance),
        )
        attempt["engine_request"].update(
            task="music.song",
            mode="cpu",
            inputs=[],
            params=dict(params),
            n_outputs=n_outputs,
        )
        session.add(models.JobAttempt(**attempt))
        validate_lyrics(session, session.get(models.Job, JOB), LYRICS)
        session.commit()
    a = {
        "owner_id": OWNER,
        "song_id": SONG,
        "post_job_id": POST,
        "generation_job_id": JOB,
        "winning_attempt_id": ATTEMPT,
        "winning_ordinal": 1,
        "terminal_seq": 1,
        "terminal_sha256": canonical_sha256(event),
        "take_id": TAKE,
        "output_index": output_index,
        "seed": 17 + output_index,
        "provenance_sha256": canonical_sha256(provenance),
    }
    reference = {
        "path": f"data/tmp/{ATTEMPT}/{output_index}.wav",
        "sha256": source_sha,
        "media_type": "audio/wav",
        "bytes": source.stat().st_size,
        "duration_s": 2.0,
    }
    plan = PostPlan(
        version=1,
        handler="post.audio",
        handler_version=1,
        owner_id=OWNER,
        song_id=SONG,
        post_job_id=POST,
        generation_job_id=JOB,
        request_sha256=canonical_sha256(actual_post_request),
        tool_pin_sha256=canonical_sha256(pin),
        provenance=provenance,
        takes=[
            {
                "authority": a,
                "source": reference,
                "copy": {
                    **reference,
                    "path": f"data/tmp/_server_inputs/{EXECUTION}/{output_index}.wav",
                },
            }
        ],
    )
    service = CpuAudioService(
        engine,
        root,
        coordinator=PublicationCoordinator(),
        bus=RecordingBus(),
        ffmpeg=ffmpeg,
    )
    try:
        yield SimpleNamespace(
            root=root, engine=engine, plan=plan, service=service, params=params
        )
    finally:
        engine.dispose()


def test_song_private_receipt_uses_sql_author_not_param_claim(song_actual):
    actual = song_actual
    results = actual.service.execute(actual.plan, execution_id=EXECUTION)
    with Session(actual.engine) as session:
        assert session.get(models.Take, TAKE).status == "ready", (
            "La letra declarada real debe producir una toma Ready"
        )
        assert (
            len(
                session.scalars(
                    select(models.Asset).where(models.Asset.subject_id == TAKE)
                ).all()
            )
            == 4
        )
        request = session.get(models.JobAttempt, ATTEMPT).engine_request.model_dump(
            mode="json"
        )
    final = actual.root / f"data/songs/{SONG}/takes/{TAKE}"
    manifest = json.loads((final / "manifest.json").read_bytes())
    assert "manifest_context_sha256" not in manifest and "root_take_id" not in manifest
    digest = manifest["private_context"]["sha256"]
    payload = (actual.root / f"data/private-contexts/{digest}.json").read_bytes()
    assert hashlib.sha256(payload).hexdigest() == digest
    receipt = json.loads(payload)
    assert receipt["captured_request"] == request
    assert receipt["takes"][TAKE]["output_index"] == 0
    assert receipt["takes"][TAKE]["lyrics"] == {
        "lyrics_version_id": LYRICS,
        "sha256": hashlib.sha256(TEXT.encode()).hexdigest(),
        "declaration": "own",
    }
    assert manifest["request"] == {
        "task": "music.song",
        "params": {"duration_s": 2},
        "seed": 17,
        "variant_index": 0,
        "lyrics_sha256": hashlib.sha256(TEXT.encode()).hexdigest(),
        "lyrics_declaration": "own",
    }
    assert TEXT not in json.dumps(manifest, ensure_ascii=False)
    assert actual.params["style"] not in json.dumps(manifest, ensure_ascii=False)
    assert verify_private_context(manifest, actual.root / "data") == {"valid": True}
    assert (
        verify_manifest(
            manifest, actual.root, private_context_root=actual.root / "data"
        )["valid"]
        is True
    )
    assert (actual.root / f"data/songs/{SONG}/song.json").is_file()
    assert not (actual.root / f"data/tmp/{ATTEMPT}").exists()
    before = {path.name: path.read_bytes() for path in final.iterdir()}
    assert len(results) == 1 and results[0].status == "success"
    actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert {path.name: path.read_bytes() for path in final.iterdir()} == before
    assert (
        actual.root / f"data/private-contexts/{digest}.json"
    ).read_bytes() == payload
    with Session(actual.engine) as session:
        assert len(session.scalars(select(models.Asset)).all()) == 4


@pytest.mark.parametrize(
    "change,code",
    [
        ("UPDATE take SET lyrics_version_id=NULL", "PROVENANCE_MISSING"),
        (
            "UPDATE lyrics_version SET deleted_at='2026-10-09T00:00:00Z'",
            "PROVENANCE_MISSING",
        ),
        ("UPDATE lyrics_version SET text='Different text'", "PROVENANCE_MISMATCH"),
        ("UPDATE lyrics_version SET sha256='" + "a" * 64 + "'", "PROVENANCE_MISMATCH"),
        ("UPDATE take SET seed='18'", "PROVENANCE_MISMATCH"),
    ],
)
def test_sql_lyrics_proof_is_checked_before_copy_or_spawn(song_actual, change, code):
    actual = song_actual
    with actual.engine.begin() as connection:
        connection.execute(text(change))
    with pytest.raises(ValueError, match="^" + code + "$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert not (actual.root / "data/tmp/_server_inputs").exists()

    assert not (actual.root / "data/tmp/_server_cpu").exists()
    assert not actual.service.owners
    with Session(actual.engine) as session:
        assert not session.scalars(select(models.CpuExecution)).all()
        assert not session.scalars(select(models.Asset)).all()


@pytest.mark.parametrize(
    "change,reason",
    [
        ("UPDATE lyrics_version SET declaration='unknown'", "ck_declaration"),
        ("UPDATE lyrics_version SET owner_id='foreign'", "Immutable identity"),
    ],
)
def test_existing_sql_guards_reject_invalid_proof_changes(song_actual, change, reason):
    with (
        pytest.raises(IntegrityError, match=reason),
        song_actual.engine.begin() as connection,
    ):
        connection.execute(text(change))


def test_total_plan_and_private_context_budget_precedes_copy(song_actual, monkeypatch):
    from app.worker import execution
    from app.worker.packages import canonical_bytes
    from audio_post.private_context import prepare_context

    actual = song_actual
    with actual.engine.connect() as connection:
        context, _ = actual.service.publisher.capture_context(connection, actual.plan)
    plan_size = len(canonical_bytes(actual.plan))
    context_size = len(prepare_context(context)[0])
    limit = plan_size + context_size - 1
    assert plan_size <= limit and context_size <= limit
    monkeypatch.setattr(execution, "MAX_PLAN_BYTES", limit)
    with pytest.raises(ValueError, match="^PLAN_TOO_LARGE$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert not (actual.root / "data/private-contexts").exists()
    assert not (actual.root / "data/tmp/_server_inputs").exists()
    assert not actual.service.owners


def test_lyrics_authority_drift_before_commit_cannot_publish(song_actual, monkeypatch):
    actual = song_actual
    publish = actual.service.publisher.publish

    def drift_then_publish(*args, **kwargs):
        with actual.engine.begin() as connection:
            connection.execute(text("UPDATE lyrics_version SET declaration='licensed'"))
        return publish(*args, **kwargs)

    monkeypatch.setattr(actual.service.publisher, "publish", drift_then_publish)
    with pytest.raises(ValueError, match="^PROVENANCE_MISMATCH$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    with Session(actual.engine) as session:
        assert session.get(models.Take, TAKE).status != "ready"
        assert not session.scalars(select(models.Asset)).all()
    assert not actual.service.owners


def test_replay_uses_historical_receipt_and_rejects_new_declaration(song_actual):
    actual = song_actual
    actual.service.execute(actual.plan, execution_id=EXECUTION)
    final = actual.root / f"data/songs/{SONG}/takes/{TAKE}"
    before = {path.name: path.read_bytes() for path in final.iterdir()}
    receipts = actual.root / "data/private-contexts"
    before_receipts = {path.name: path.read_bytes() for path in receipts.iterdir()}
    with actual.engine.begin() as connection:
        connection.execute(text("UPDATE lyrics_version SET declaration='licensed'"))
    with pytest.raises(ValueError, match="^PROVENANCE_MISMATCH$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert {path.name: path.read_bytes() for path in final.iterdir()} == before
    assert {
        path.name: path.read_bytes() for path in receipts.iterdir()
    } == before_receipts
    with Session(actual.engine) as session:
        assert len(session.scalars(select(models.Asset)).all()) == 4
    # A new valid version with identical text cannot replace the historical
    # Take binding and authorize a freshly captured receipt on replay.
    replacement = "01K70000000000000000000014"
    with Session(actual.engine) as session:
        session.get(models.LyricsVersion, LYRICS).declaration = "own"
        session.add(
            models.LyricsVersion(
                **common(replacement),
                song_id=SONG,
                text=TEXT,
                sha256=hashlib.sha256(TEXT.encode()).hexdigest(),
                source="manual",
                declaration="own",
            )
        )
        session.commit()
    with actual.engine.begin() as connection:
        connection.execute(
            text("UPDATE take SET lyrics_version_id=:id WHERE id=:take"),
            {"id": replacement, "take": TAKE},
        )
    with pytest.raises(ValueError, match="^PROVENANCE_MISMATCH$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert {path.name: path.read_bytes() for path in final.iterdir()} == before
    assert {
        path.name: path.read_bytes() for path in receipts.iterdir()
    } == before_receipts


@pytest.mark.parametrize("song_actual", [3], indirect=True)
def test_real_sparse_output_keeps_engine_index_and_seed(song_actual):
    actual = song_actual
    actual.service.execute(actual.plan, execution_id=EXECUTION)
    manifest = json.loads(
        (actual.root / f"data/songs/{SONG}/takes/{TAKE}/manifest.json").read_bytes()
    )
    assert manifest["request"]["variant_index"] == 3
    assert manifest["request"]["seed"] == 20
    digest = manifest["private_context"]["sha256"]
    receipt = json.loads(
        (actual.root / f"data/private-contexts/{digest}.json").read_bytes()
    )
    assert receipt["captured_request"]["n_outputs"] == 4
    assert receipt["takes"][TAKE]["output_index"] == 3
    with Session(actual.engine) as session:
        assert session.get(models.Take, TAKE).status == "ready"
        assert len(session.scalars(select(models.Asset)).all()) == 4


def test_content_addressed_receipt_reuses_only_identical_single_link_file(song_actual):
    import os

    from audio_post.private_context import prepare_context

    actual = song_actual
    with actual.engine.connect() as connection:
        context, _ = actual.service.publisher.capture_context(connection, actual.plan)
    payload, digest = prepare_context(context)
    actual.service._put_receipt(payload, digest)
    path = actual.root / f"data/private-contexts/{digest}.json"
    inode = path.stat().st_ino
    actual.service._put_receipt(payload, digest)
    assert path.stat().st_ino == inode and path.read_bytes() == payload
    os.link(path, path.with_suffix(".foreign"))
    with pytest.raises(ValueError, match="^UNSAFE_PATH$"):
        actual.service._put_receipt(payload, digest)
    path.with_suffix(".foreign").unlink()
    path.write_bytes(b"foreign receipt")
    with pytest.raises(ValueError, match="^PROVENANCE_MISMATCH$"):
        actual.service._put_receipt(payload, digest)
    assert path.read_bytes() == b"foreign receipt"


@pytest.mark.parametrize("kind", ["hardlink", "symlink", "fifo", "tamper"])
def test_raw_source_custody_rejects_aliases_and_changed_bytes(song_actual, kind):
    import os

    actual = song_actual
    source = actual.root / actual.plan.takes[0].source.path
    if kind == "hardlink":
        os.link(source, source.with_suffix(".foreign"))
    elif kind == "symlink":
        saved = source.with_suffix(".foreign")
        source.rename(saved)
        source.symlink_to(saved)
    elif kind == "fifo":
        source.unlink()
        os.mkfifo(source)
    else:
        source.write_bytes(b"changed raw output")
    code = "PROVENANCE_MISMATCH" if kind == "tamper" else "UNSAFE_PATH"
    with pytest.raises(ValueError, match="^" + code + "$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert not actual.service.owners
    assert not (actual.root / "data/tmp/_server_inputs").exists()
    if kind == "fifo":
        source.unlink()  # The own test FIFO cannot be copied into host evidence.


@pytest.mark.parametrize("song_actual", [{"invalid_audio": True}], indirect=True)
def test_actual_ffmpeg_failure_is_durable_and_has_no_assets(song_actual):
    actual = song_actual
    try:
        results = actual.service.execute(actual.plan, execution_id=EXECUTION)
    except BaseException:
        owner = actual.service.owners.get(EXECUTION)
        if owner is not None:
            (actual.root / "native-child-stderr.txt").write_bytes(owner.stderr)
        raise
    assert len(results) == 1 and results[0].status == "failure"
    with Session(actual.engine) as session:
        take = session.get(models.Take, TAKE)
        assert take.status == "failed" and take.error_code == results[0].code
        assert not session.scalars(select(models.Asset)).all()
        cpu = session.get(models.CpuExecution, EXECUTION)
        assert cpu.state == "finished" and cpu.cleanup_state == "confirmed"
        assert cpu.outcome["kind"] == "all_failed"
    assert not actual.service.owners
    assert not (actual.root / f"data/songs/{SONG}/takes/{TAKE}").exists()


def test_cancel_at_publication_barrier_preserves_no_assets_and_joins(
    song_actual, monkeypatch
):
    actual = song_actual
    publish = actual.service.publisher.publish

    def cancel_then_publish(*args, **kwargs):
        with actual.engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE job SET cancel_requested_at='2026-10-09T00:00:00Z' WHERE id=:id"
                ),
                {"id": POST},
            )
        return publish(*args, **kwargs)

    monkeypatch.setattr(actual.service.publisher, "publish", cancel_then_publish)
    with pytest.raises(ValueError, match="^CANCELLED$"):
        actual.service.execute(actual.plan, execution_id=EXECUTION)
    with Session(actual.engine) as session:
        assert session.get(models.Take, TAKE).status != "ready"
        assert not session.scalars(select(models.Asset)).all()
        assert session.get(models.CpuExecution, EXECUTION).cleanup_state == "confirmed"
    assert not actual.service.owners


@pytest.mark.parametrize("foreign_kind", ["empty_directory", "directory", "file"])
def test_native_noreplace_preserves_foreign_destination(tmp_path, foreign_kind):
    import errno

    from app.worker.publications import rename_noreplace

    source = tmp_path / "owned-source"
    source.mkdir()
    (source / "owned").write_bytes(b"own bytes")
    destination = tmp_path / "foreign-destination"
    if foreign_kind == "file":
        destination.write_bytes(b"foreign bytes")
    else:
        destination.mkdir()
        if foreign_kind == "directory":
            (destination / "witness").write_bytes(b"foreign bytes")
    before = destination.stat().st_ino
    with pytest.raises(OSError) as caught:
        rename_noreplace(source, destination)
    assert caught.value.errno == errno.EEXIST
    assert destination.stat().st_ino == before
    assert (source / "owned").read_bytes() == b"own bytes"
    if foreign_kind == "file":
        assert destination.read_bytes() == b"foreign bytes"
    elif foreign_kind == "directory":
        assert (destination / "witness").read_bytes() == b"foreign bytes"
    else:
        assert list(destination.iterdir()) == []


@pytest.mark.linux_real
def test_native_publication_rejects_cross_device_before_rename(tmp_path):
    from app.worker.publications import rename_noreplace

    source = tmp_path / "owned-source"
    source.mkdir()
    destination = Path("/proof/tmp") / ("cross-device-" + tmp_path.name)
    destination.parent.mkdir(exist_ok=True)
    assert source.parent.stat().st_dev != destination.parent.stat().st_dev
    with pytest.raises(ValueError, match="^UNSAFE_PATH$"):
        rename_noreplace(source, destination)
    assert source.is_dir() and not destination.exists()
