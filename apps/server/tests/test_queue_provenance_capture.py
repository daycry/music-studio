"""Captura write-once contra las autoridades y triggers SQLite reales."""

import asyncio
from dataclasses import replace

import pytest
from app.models import Job, JobAttempt, new_id
from app.worker.contracts import canonical_sha256
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_queue_provenance_send import engine as engine  # noqa: PLC0414
from test_queue_provenance_send import pipeline


def reserved(engine):
    jid, admission, resolver, backend, _dispatcher = pipeline(engine)
    selected = asyncio.run(resolver.resolve(admission.select(jid), engine=engine))
    claim = admission.reserve(selected)
    asyncio.run(backend.load(claim.load_options))
    return admission, claim, backend


def evidence(claim, backend):
    from app.queue.provenance import capture_before_send

    return capture_before_send(
        claim.selected_provenance,
        claim.request,
        claim.load_options,
        asyncio.run(backend.health()),
        require_loaded=True,
    )


def test_identical_competing_capture_idempotent_different_capture_rejected(engine):
    from concurrent.futures import ThreadPoolExecutor

    admission, claim, backend = reserved(engine)
    value = evidence(claim, backend)
    digest = canonical_sha256(value)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: admission.capture_provenance(claim, value, digest), range(2)
            )
        )
    assert results == [True, True]
    changed = value.model_copy(update={"observed_model": None})
    assert not admission.capture_provenance(claim, changed, canonical_sha256(changed))
    with Session(engine) as session:
        attempt = session.get(JobAttempt, claim.attempt_id)
        assert attempt.provenance == value and attempt.provenance_sha256 == digest
    assert admission.may_send(claim)


@pytest.mark.parametrize(
    "sql",
    [
        "provenance=NULL, provenance_sha256=NULL",
        "provenance_sha256=:sha",
        "provenance='{}'",
    ],
)
def test_direct_sql_final_guard_never_rewrites_capture(engine, sql):
    admission, claim, backend = reserved(engine)
    value = evidence(claim, backend)
    assert admission.capture_provenance(claim, value, canonical_sha256(value))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text("UPDATE job_attempt SET " + sql + " WHERE id=:id"),
            {"id": claim.attempt_id, "sha": "b" * 64},
        )


def test_nullable_pair_and_hash_request_claim_guards(engine):
    admission, claim, backend = reserved(engine)
    value = evidence(claim, backend)
    assert not admission.may_send(claim)
    assert admission.may_prepare_send(claim)
    assert not admission.capture_provenance(claim, value, "b" * 64)
    bad = replace(claim, request=claim.request.model_copy(update={"seed": 99}))
    assert not admission.capture_provenance(bad, value, canonical_sha256(value))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text("UPDATE job_attempt SET provenance_sha256=:sha WHERE id=:id"),
            {"id": claim.attempt_id, "sha": "b" * 64},
        )


@pytest.mark.parametrize(
    "field", ["cancel", "deleted", "owner", "job", "load", "selected"]
)
def test_capture_requires_live_exact_authority(engine, field):
    admission, claim, backend = reserved(engine)
    value = evidence(claim, backend)
    if field in {"cancel", "deleted"}:
        with Session(engine) as session, session.begin():
            job = session.get(Job, claim.job_id)
            setattr(
                job,
                "cancel_requested_at" if field == "cancel" else "deleted_at",
                "2026-10-09T00:00:00Z",
            )
    elif field == "owner":
        admission.owner_id = new_id()
    elif field == "job":
        claim = replace(claim, job_id="01K70000000000000000000000")
    elif field == "load":
        claim = replace(
            claim,
            load_options=claim.load_options.model_copy(update={"mode": "offload"}),
        )
    else:
        claim = replace(claim, selected_provenance=None)
    assert not admission.capture_provenance(claim, value, canonical_sha256(value))


def test_synthetic_expected_digest_is_only_fixture_authority(engine):
    from app.queue.provenance import capture_before_send

    _admission, claim, backend = reserved(engine)
    selected = replace(
        claim.selected_provenance, expected_image_digest="sha256:" + "a" * 64
    )
    assert claim.selected_provenance.expected_image_digest is None
    health = asyncio.run(backend.health())
    # Both the selected and fresh reported identities are this explicit synthetic fixture.
    selected = replace(
        selected,
        resolve_health_json=health.model_copy(
            update={"image_digest": "sha256:" + "b" * 64}
        ).model_dump_json(),
    )
    with pytest.raises(ValueError):
        capture_before_send(
            selected,
            claim.request,
            claim.load_options,
            health.model_copy(update={"image_digest": "sha256:" + "b" * 64}),
            require_loaded=True,
        )


@pytest.mark.parametrize(
    "mutation", ["task", "mode", "model", "busy", "job", "image-invalid"]
)
def test_pure_capture_rejects_unbound_request_or_health(engine, mutation):
    from app.queue.provenance import capture_before_send

    _admission, claim, backend = reserved(engine)
    request, load = claim.request, claim.load_options
    health = asyncio.run(backend.health())
    if mutation in {"task", "mode", "model"}:
        field = "model_id" if mutation == "model" else mutation
        request = request.model_copy(update={field: "OTHER"})
    else:
        updates = {
            "busy": {"state": "busy"},
            "job": {"job_id": claim.attempt_id},
            "image-invalid": {"image_digest": "UNKNOWN"},
        }[mutation]
        health = health.model_copy(update=updates)
    with pytest.raises(ValueError):
        capture_before_send(
            claim.selected_provenance, request, load, health, require_loaded=True
        )


def test_known_digest_valid_snapshot_and_selection_deeply_immutable(engine):
    from dataclasses import FrozenInstanceError

    from app.queue.provenance import SelectedProvenance, capture_before_send

    _admission, claim, backend = reserved(engine)
    backend.health_update["image_digest"] = "sha256:" + "a" * 64
    health = asyncio.run(backend.health())
    selected = SelectedProvenance.select(
        backend.model,
        health,
        claim.request.task,
        claim.load_options.model_id,
        claim.load_options.mode,
    )
    captured = capture_before_send(
        selected, claim.request, claim.load_options, health, require_loaded=True
    )
    assert captured.reported_image_digest == "sha256:" + "a" * 64
    assert captured.expected_image_digest is None
    with pytest.raises(FrozenInstanceError):
        selected.task = "music.song"
    copied = selected.descriptor.value
    copied.revision = "later"
    assert selected.descriptor.value.revision == "synthetic-immutable"


def test_started_attempt_cannot_gain_or_rewrite_capture(engine):
    from app.queue.events import EventBus, EventConsumer
    from engine_contract import Event

    admission, claim, backend = reserved(engine)
    value = evidence(claim, backend)
    assert EventConsumer(engine, admission.owner_id, EventBus()).accept(
        claim.attempt_id,
        "fixture-engine",
        Event(
            job_id=claim.attempt_id,
            seq=1,
            ts="2026-10-09T00:00:00Z",
            type="stage",
            data={"stage": "loading_model"},
        ),
    )
    assert not admission.capture_provenance(claim, value, canonical_sha256(value))
    assert not admission.may_send(claim)
    with Session(engine) as session:
        assert session.get(JobAttempt, claim.attempt_id).provenance is None


def test_publication_revision_binds_actual_durable_capture_sha_and_terminal_seed(
    engine,
):
    from app.models import (
        CpuExecution,
        JobDependency,
        PublicationIntent,
        PublicationIntentRevision,
        Take,
    )
    from app.queue.events import EventBus, EventConsumer
    from app.worker.contracts import PostPlan
    from engine_contract import Event

    admission, claim, backend = reserved(engine)
    value = evidence(claim, backend)
    digest = canonical_sha256(value)
    assert admission.capture_provenance(claim, value, digest)
    terminal = Event(
        job_id=claim.attempt_id,
        seq=1,
        ts="2026-10-09T00:00:00Z",
        type="done",
        data={
            "artifacts": [
                {
                    "output_index": 0,
                    "path": f"tmp/{claim.attempt_id}/0.wav",
                    "media_type": "audio/wav",
                    "sha256": "a" * 64,
                    "meta": {"seed": 17},
                }
            ],
            "telemetry": {"mode": "bf16", "model_revision": "synthetic"},
        },
    )
    assert EventConsumer(engine, admission.owner_id, EventBus()).accept(
        claim.attempt_id, "fixture-engine", terminal
    )
    with Session(engine) as session, session.begin():
        job = session.get(Job, claim.job_id)
        owner, song = job.owner_id, job.song_id
        post = Job(
            owner_id=owner,
            song_id=song,
            task="post.audio",
            lane="cpu",
            status="running",
            attempt=1,
            request={
                "inputs": [
                    {
                        "role": "source",
                        "ref": {"type": "job", "id": job.id},
                        "output_index": 0,
                    }
                ]
            },
        )
        session.add(post)
        session.flush()
        session.add(
            JobDependency(owner_id=owner, job_id=post.id, depends_on_job_id=job.id)
        )
        tid = new_id()
        take = Take(
            id=tid,
            owner_id=owner,
            song_id=song,
            job_id=job.id,
            status="queued",
            batch_id=job.id,
            variant_index=0,
            root_id=tid,
            derivation="original",
            task=job.task,
            model_id=claim.request.model_id,
            model_version="1",
            seed=17,
            commercial_use=True,
        )
        session.add(take)
        session.flush()
        authority = {
            "owner_id": owner,
            "song_id": song,
            "post_job_id": post.id,
            "generation_job_id": job.id,
            "winning_attempt_id": claim.attempt_id,
            "winning_ordinal": 1,
            "terminal_seq": 1,
            "terminal_sha256": canonical_sha256(
                session.get(JobAttempt, claim.attempt_id).terminal
            ),
            "take_id": tid,
            "output_index": 0,
            "seed": 17,
            "provenance_sha256": digest,
        }
        source = {
            "path": f"data/tmp/{claim.attempt_id}/0.wav",
            "sha256": "a" * 64,
            "media_type": "audio/wav",
            "bytes": 100,
            "duration_s": 1.0,
        }
        plan = PostPlan.model_validate(
            {
                "version": 1,
                "handler": "post.audio",
                "handler_version": 1,
                "owner_id": owner,
                "song_id": song,
                "post_job_id": post.id,
                "generation_job_id": job.id,
                "request_sha256": canonical_sha256(post.request),
                "tool_pin_sha256": "b" * 64,
                "provenance": value,
                "takes": [
                    {
                        "authority": authority,
                        "source": source,
                        "copy": {
                            **source,
                            "path": "data/tmp/_server_inputs/fixture/0.wav",
                        },
                    }
                ],
            }
        )
        execution = CpuExecution(
            owner_id=owner,
            job_id=post.id,
            ordinal=1,
            handler="post.audio",
            handler_version=1,
            contract_version=1,
            state="prepared",
            revision=1,
            plan=plan,
            plan_sha256=canonical_sha256(plan),
            cleanup_state="unknown",
        )
        session.add(execution)
        session.flush()
        intent = PublicationIntent(
            owner_id=owner, song_id=song, take_id=tid, output_index=0, seed=17
        )
        session.add(intent)
        session.flush()
        revision = PublicationIntentRevision(
            owner_id=owner,
            intent_id=intent.id,
            cpu_execution_id=execution.id,
            **{k: v for k, v in authority.items() if k != "owner_id"},
            source_sha256="a" * 64,
            stage_path=f"songs/{song}/takes/.pending-{execution.id}/{tid}",
            final_path=f"songs/{song}/takes/{tid}",
        )
        session.add(revision)
        session.flush()
        rid = revision.id
    with Session(engine) as session:
        assert session.get(PublicationIntentRevision, rid).provenance_sha256 == digest
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE publication_intent_revision SET provenance_sha256=:sha WHERE id=:id"
            ),
            {"id": rid, "sha": "b" * 64},
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text("UPDATE job_attempt SET provenance_sha256=:sha WHERE id=:id"),
            {"id": claim.attempt_id, "sha": "b" * 64},
        )
