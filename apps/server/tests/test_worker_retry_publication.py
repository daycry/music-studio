"""Reintento con linaje e intent nueva: CPU/SQLite real, sin ejecutar FFmpeg."""

import json
import os
import sys
from pathlib import Path

import pytest
from app.models import Job, JobAttempt, PublicationIntent, Take, new_id
from app.publication import PublicationCoordinator
from app.worker.execution import CpuAudioService
from app.worker.planning import compose_post_plan
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_queue_chains import create, services
from test_queue_manual_retry import completed_post_with_take_failures, retry
from test_queue_manual_retry import engine as _retry_engine
from test_queue_references import accepted

engine = _retry_engine


def retry_plan(engine, resolver, owner, chain, execution_id):
    def seeds(artifacts):
        for artifact in artifacts:
            artifact["meta"] = {"seed": 17 + artifact["output_index"]}

    claim, artifacts = accepted(engine, chain, resolver, owner, artifact_mutator=seeds)
    with Session(engine) as session:
        post = session.get(Job, chain.post_job_id)
        post.status = "running"
        plan = compose_post_plan(
            post=post,
            generation=session.get(Job, chain.generation_job_id),
            attempt=session.get(JobAttempt, claim.attempt_id),
            takes=[session.get(Take, tid) for tid in chain.take_ids],
            artifacts=artifacts,
            root=resolver.data_dir.parent,
            execution_id=execution_id,
            tool_pin=json.loads(
                (
                    Path(__file__).resolve().parents[3] / "tools/ffmpeg-linux.lock.json"
                ).read_text()
            ),
        )
        session.commit()
    return plan


@pytest.mark.parametrize("detached_worker_namespace", [False, True])
def test_retry_sparse_index_reserves_new_publication_without_overwriting_history(
    engine, monkeypatch, detached_worker_namespace
):
    owner, song, _, resolver = services(engine)
    original = create(engine, owner, song, resolver)
    completed_post_with_take_failures(engine, original, resolver, owner)
    new = retry(
        engine,
        owner,
        resolver,
        original.generation_job_id,
        take_ids=[original.take_ids[2]],
    )
    execution_id = new_id()
    plan = retry_plan(engine, resolver, owner, new, execution_id)
    assert [entry.authority.output_index for entry in plan.takes] == [2]
    assert plan.takes[0].authority.seed == 19
    service = CpuAudioService(
        engine,
        resolver.data_dir.parent,
        coordinator=PublicationCoordinator(),
        bus=None,
        ffmpeg=resolver.data_dir / "synthetic-ffmpeg",
        owner_id=owner,
    )
    if detached_worker_namespace:
        # Other tests can replace the parent package without evicting its modules.
        monkeypatch.delattr(sys.modules["app"], "worker", raising=False)
    # Explicit seam: no executable runs. Real pin, context, SQL, CAS and
    # Publisher.authority remain active; only binary verification is replaced.
    execution_globals = CpuAudioService._prepare.__globals__
    monkeypatch.setitem(execution_globals, "tool", lambda *_: None)
    # Windows cannot open directories for fsync. This test proves logical
    # identity/reservation, not Linux filesystem durability or audio completion.
    flushes = []
    if os.name == "nt":
        monkeypatch.setitem(
            execution_globals["write_once"].__globals__,
            "fsync_directory",
            lambda path: flushes.append(path),
        )
    stored, run = service._prepare(plan, execution_id)
    assert stored["state"] == "prepared" and run.is_dir()
    if os.name == "nt":
        assert resolver.data_dir / "private-contexts" in flushes
        assert resolver.data_dir / "tmp/_server_inputs" / execution_id in flushes
        assert run in flushes
    with Session(engine) as session:
        old = session.scalar(
            select(PublicationIntent).where(
                PublicationIntent.take_id == original.take_ids[2]
            )
        )
        new_intent = session.scalar(
            select(PublicationIntent).where(
                PublicationIntent.take_id == new.take_ids[0]
            )
        )
        assert old.state == "failed" and old.error_code == "AUDIO_INVALID"
        assert new_intent.id != old.id and new_intent.state == "reserved"
        assert (
            session.get(Take, original.take_ids[2]).job_id == original.generation_job_id
        )
    context = service.publisher.contexts[execution_id]["takes"][new.take_ids[0]]
    assert context["lineage"] == {
        "parents": [{"type": "take", "id": original.take_ids[2], "role": "retry"}],
        "derivation": "variant",
        "section_map": None,
    }


@pytest.mark.parametrize(
    "bad",
    [
        "negative",
        "bool",
        "duplicate_input",
        "duplicate_take",
        "foreign_owner",
        "foreign_song",
        "negative_artifact",
        "duplicate_artifact",
        "wrong_ref",
        "wrong_role",
        "wrong_digest",
        "wrong_media",
        "missing_take",
        "wrong_path",
        "duration",
        "wrong_task",
        "live_generation",
        "live_attempt",
        "input_type",
    ],
)
def test_retry_plan_rejects_invalid_original_bindings(tmp_path, bad):
    from test_worker_planning import _fixture

    post, generation, attempt, takes, artifacts = _fixture(tmp_path)
    item = post.request["inputs"][0]
    if bad == "negative":
        item["output_index"] = -1
    if bad == "bool":
        item["output_index"] = False
    if bad == "duplicate_input":
        post.request["inputs"].append(dict(item))
    if bad == "duplicate_take":
        takes.append(takes[0])
    if bad == "foreign_owner":
        takes[0].owner_id = new_id()
    if bad == "foreign_song":
        takes[0].song_id = new_id()
    if bad == "negative_artifact":
        artifacts[0]["output_index"] = -1
    if bad == "duplicate_artifact":
        # The accepted terminal and resolved artifacts share this fixture list.
        original_dump = attempt.terminal.model_dump
        attempt.terminal.model_dump = lambda **kw: {
            **original_dump(**kw),
            "data": {"artifacts": artifacts * 2},
        }
    if bad == "wrong_ref":
        item["ref"]["id"] = post.id
    if bad == "wrong_role":
        item["role"] = "other"
    if bad == "wrong_digest":
        artifacts[0]["sha256"] = "0" * 64
    if bad == "wrong_media":
        artifacts[0]["media_type"] = "text/plain"
    if bad == "missing_take":
        takes.clear()
    if bad == "wrong_path":
        artifacts[0]["path"] = "tmp/foreign/0.wav"
    if bad == "duration":
        generation.request = {"params": {"duration_s": 0}}
    if bad == "wrong_task":
        post.task = "audio.beats"
    if bad == "live_generation":
        generation.status = "running"
    if bad == "live_attempt":
        attempt.status = "running"
    if bad == "input_type":
        post.request["inputs"] = [1]
    with pytest.raises((ValueError, TypeError)):
        compose_post_plan(
            post=post,
            generation=generation,
            attempt=attempt,
            takes=takes,
            artifacts=artifacts,
            root=tmp_path,
            execution_id=new_id(),
            tool_pin={},
        )
