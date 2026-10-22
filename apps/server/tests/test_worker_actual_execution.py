"""WAV físico, SQLite y FFmpeg Linux reales; no sustitutos del cómputo."""

import hashlib
import importlib.util
import json
import math
import os
import struct
import subprocess
import sys
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import models
from app.db import create_db_engine, migrate
from app.publication import PublicationCoordinator
from app.queue.synthetic_registry import MOCK_ORIGIN, packaged_mock_registry
from app.worker.contracts import CapturedProvenance, PostPlan, canonical_sha256
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_job_attempt_schema import ATTEMPT, JOB, OWNER, SONG, row
from test_worker_publication_invariants import (
    EXECUTION,
    POST,
    TAKE,
    common,
    post_request,
    terminal,
)


class RecordingBus:
    def __init__(self):
        self.confirmed = []
        self.gaps = 0

    def publish_confirmed(self, value):
        self.confirmed.append(value)
        return True

    def mark_gap(self):
        self.gaps += 1


def physical_wav(path):
    path.parent.mkdir(parents=True)
    frames = bytearray()
    for index in range(96000):
        value = int(12000 * math.sin(index * 2 * math.pi * 440 / 48000))
        frames.extend(struct.pack("<hh", value, value))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(frames)


@pytest.fixture
def actual(tmp_path, request):
    assert sys.platform == "linux", "Este gate exige Linux real; no sustitución host"
    root = tmp_path / "actual"
    root.mkdir()
    source = root / f"data/tmp/{ATTEMPT}/0.wav"
    physical_wav(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    ffmpeg = Path(os.environ["STUDIO_ACTUAL_FFMPEG"])
    pin = json.loads(Path("/studio/tools/ffmpeg-linux.lock.json").read_text())
    assert ffmpeg.is_file()
    assert (
        hashlib.sha256(ffmpeg.read_bytes()).hexdigest()
        == os.environ["STUDIO_ACTUAL_FFMPEG_SHA"]
    )
    probe = subprocess.run([str(ffmpeg), "-version"], capture_output=True, check=True)
    assert b"--enable-gpl" not in probe.stdout
    assert b"--enable-libmp3lame" in probe.stdout
    import audio_post.pipeline
    import pyloudnorm
    import soundfile

    assert audio_post.pipeline.process_audio and soundfile.read and pyloudnorm.Meter

    backend = SimpleNamespace(origin=MOCK_ORIGIN)
    registry = packaged_mock_registry({"mock": backend}, {"mock": MOCK_ORIGIN})
    entry = registry.entries[0]
    provenance = CapturedProvenance(
        descriptor=entry.descriptor,
        engine_id="mock",
        engine_version="0.1.0",
        contract_version="1",
        task="music.instrumental",
        load={"model_id": "mock", "mode": "cpu"},
        observed_model={"model_id": "mock", "mode": "cpu"},
        expected_image_digest=None,
        reported_image_digest=None,
        evidence_kind="synthetic",
        synthetic_binding=entry.binding,
    )
    registry.rebind(provenance, backend=backend)
    event = terminal()
    event["data"]["artifacts"][0]["sha256"] = digest
    event["data"]["telemetry"]["mode"] = "cpu"
    event["data"]["telemetry"]["model_revision"] = "synthetic-v1"
    database = root / "data/studio.sqlite"
    migrate(database)
    engine = create_db_engine(database)
    with Session(engine) as session:
        session.add(models.Song(**common(SONG), title="WAV real sintético"))
        session.flush()
        session.add(
            models.Job(
                **common(JOB),
                song_id=SONG,
                task="music.instrumental",
                lane="cpu",
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
                model_version="1",
                seed=17,
                commercial_use=True,
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
        attempt["engine_request"]["mode"] = "cpu"
        attempt["engine_request"]["params"]["duration_s"] = 2
        attempt["engine_request"]["params"].update(getattr(request, "param", {}))
        session.add(models.JobAttempt(**attempt))
        session.commit()
    authority = {
        "owner_id": OWNER,
        "song_id": SONG,
        "post_job_id": POST,
        "generation_job_id": JOB,
        "winning_attempt_id": ATTEMPT,
        "winning_ordinal": 1,
        "terminal_seq": 1,
        "terminal_sha256": canonical_sha256(event),
        "take_id": TAKE,
        "output_index": 0,
        "seed": 17,
        "provenance_sha256": canonical_sha256(provenance),
    }
    reference = {
        "path": f"data/tmp/{ATTEMPT}/0.wav",
        "sha256": digest,
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
        request_sha256=canonical_sha256(post_request()),
        tool_pin_sha256=canonical_sha256(pin),
        provenance=provenance,
        takes=[
            {
                "authority": authority,
                "source": reference,
                "copy": {
                    **reference,
                    "path": f"data/tmp/_server_inputs/{EXECUTION}/0.wav",
                },
            }
        ],
    )
    bus = RecordingBus()
    service = None
    if importlib.util.find_spec("app.worker.execution") is not None:
        from app.worker.execution import CpuAudioService

        service = CpuAudioService(
            engine, root, coordinator=PublicationCoordinator(), bus=bus, ffmpeg=ffmpeg
        )
    try:
        yield SimpleNamespace(
            root=root, engine=engine, plan=plan, service=service, bus=bus
        )
    finally:
        engine.dispose()


def test_real_wav_is_transcoded_and_published_once(actual):
    # El producto actual no contiene handler CPU real. El driver conserva ese
    # comportamiento sin fabricar paquetes ni provocar un ImportError.
    results = (
        ()
        if actual.service is None
        else actual.service.execute(actual.plan, execution_id=EXECUTION)
    )
    with Session(actual.engine) as session:
        assets = session.scalars(
            select(models.Asset).where(models.Asset.subject_id == TAKE)
        ).all()
        assert {asset.role for asset in assets} == {
            "master",
            "listen",
            "peaks",
            "manifest",
        }, "El WAV autorizado debe producir los cuatro assets durables"
        assert session.get(models.Take, TAKE).status == "ready"
        assert session.scalar(select(models.PublicationIntent)).state == "committed"
        for asset in assets:
            path = actual.root / "data" / asset.path
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == asset.sha256
            assert path.stat().st_size == asset.bytes
    assert len(results) == 1 and results[0].status == "success"
    assert math.isfinite(results[0].integrated_lufs)
    assert abs(results[0].integrated_lufs + 14) <= 0.5
    assert results[0].true_peak_dbtp <= -1.0
    final = actual.root / f"data/songs/{SONG}/takes/{TAKE}"
    before = {path.name: path.read_bytes() for path in final.iterdir()}
    manifest = json.loads(before["manifest.json"])
    assert manifest["kind"] == "audio_take"
    assert manifest["subject"] == {"type": "take", "id": TAKE}
    assert manifest["models"][0]["weights"] == []
    assert manifest[
        "synthetic_binding"
    ] == actual.plan.provenance.synthetic_binding.model_dump(mode="json")
    assert (actual.root / f"data/songs/{SONG}/song.json").is_file()
    actual.service.execute(actual.plan, execution_id=EXECUTION)
    assert {path.name: path.read_bytes() for path in final.iterdir()} == before
    with Session(actual.engine) as session:
        assert len(session.scalars(select(models.Asset)).all()) == 4


def test_manifest_keeps_winning_params_and_actual_take_lineage(actual):
    parent = "01K70000000000000000000010"
    with Session(actual.engine) as session:
        session.add(
            models.Take(
                **common(parent),
                song_id=SONG,
                job_id=JOB,
                status="queued",
                batch_id=JOB,
                variant_index=1,
                root_id=parent,
                derivation="original",
                task="music.instrumental",
                model_id="mock",
                model_version="1",
                seed=18,
                commercial_use=True,
            )
        )
        session.flush()
        take = session.get(models.Take, TAKE)
        take.root_id = parent
        take.derivation = "variant"
        session.add(
            models.LineageEdge(
                **common("01K70000000000000000000011"),
                child_type="take",
                child_id=TAKE,
                parent_type="take",
                parent_id=parent,
                role="source",
                section_map=None,
            )
        )
        request = session.get(models.JobAttempt, ATTEMPT).engine_request
        expected = {
            "params": request.model_dump(mode="json")["params"],
            "lineage": {
                "parents": [{"type": "take", "id": parent, "role": "source"}],
                "derivation": "variant",
                "section_map": None,
            },
        }
        assert expected["params"] == {"duration_s": 2}
        session.commit()
    actual.service.execute(actual.plan, execution_id=EXECUTION)
    manifest_path = actual.root / f"data/songs/{SONG}/takes/{TAKE}/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    assert {
        "params": manifest["request"]["params"],
        "lineage": manifest["lineage"],
    } == expected


@pytest.mark.parametrize(
    "actual", [{"style": "Estilo privado del propietario"}], indirect=True
)
def test_private_params_require_generic_receipt_before_manifest_publication(actual):
    actual.service.execute(actual.plan, execution_id=EXECUTION)
    with Session(actual.engine) as session:
        take = session.get(models.Take, TAKE)
        assert take.status == "ready"
        assert take.error_code is None
        assert len(session.scalars(select(models.Asset)).all()) == 4
    manifest = json.loads(
        (actual.root / f"data/songs/{SONG}/takes/{TAKE}/manifest.json").read_bytes()
    )
    assert "style" not in manifest["request"]["params"]
    digest = manifest["private_context"]["sha256"]
    payload = (actual.root / f"data/private-contexts/{digest}.json").read_bytes()
    assert hashlib.sha256(payload).hexdigest() == digest
    receipt = json.loads(payload)
    assert receipt["captured_request"]["params"]["style"] == (
        "Estilo privado del propietario"
    )
    assert "Estilo privado del propietario" not in json.dumps(manifest)
