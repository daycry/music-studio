"""Composición confiada sintética; descriptor real, SQLite y transporte de fixture."""

import asyncio
import json
import os
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from app.models import JobAttempt
from app.queue.runtime import QueueRuntime
from app.settings import ContractSettings
from app.worker.contracts import canonical_sha256
from engine_contract import Health
from engine_mock import descriptor as real_mock_descriptor
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_dispatcher_admission import add
from test_dispatcher_recovery import engine as engine  # noqa: PLC0414


def test_real_cpu_mock_owned_runtime_captures_before_fixture_submit(
    engine, monkeypatch
):
    native = real_mock_descriptor()
    assert native.weights == []
    posts = []
    submitted = asyncio.Event()
    client = httpx.AsyncClient

    def wire(request):
        if request.url.path == "/v1/health":
            return httpx.Response(
                200,
                json={
                    "engine_id": "mock",
                    "engine_version": "0.1.0",
                    "image_digest": "unknown",
                    "state": "idle",
                    "loaded": None,
                    "gpu": {"total_mb": 0, "free_mb": 0, "cap_mb": 0},
                },
            )
        if request.url.path == "/v1/models":
            return httpx.Response(200, json=[native.model_dump(mode="json")])
        if request.url.path == "/v1/jobs":
            body = json.loads(request.content)
            with Session(engine) as session:
                attempt = session.get(JobAttempt, body["job_id"])
                assert attempt.provenance is not None
                assert attempt.engine_request.model_dump(mode="json") == body
                value = attempt.provenance.model_dump(mode="json")
                assert value["evidence_kind"] == "synthetic"
                assert value["descriptor"]["weights"] == []
                assert value["observed_model"] is None
                assert value["expected_image_digest"] is None
                assert value["reported_image_digest"] is None
                assert attempt.provenance_sha256 == canonical_sha256(value)
            posts.append(body)
            submitted.set()
            return httpx.Response(202, json={"job_id": body["job_id"]})
        if request.url.path.endswith("/events"):
            return httpx.Response(
                200, content=b"", headers={"content-type": "application/x-ndjson"}
            )
        return httpx.Response(
            200,
            json={
                "job_id": request.url.path.rsplit("/", 1)[-1],
                "state": "busy",
                "seq": 0,
            },
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: client(**dict(kwargs, transport=httpx.MockTransport(wire))),
    )
    jid, _ = add(
        engine,
        lane="cpu",
        request={
            "params": {"duration_s": 1, "style": "  literal [Verse]  "},
            "mode": "cpu",
            "seed": 17,
            "n_outputs": 2,
            "timeout_s": 60,
        },
    )
    settings = ContractSettings(
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        engine_token="private-test-only",
        engines={"mock": "http://engine-mock:8199"},
    )

    async def run():
        runtime = QueueRuntime(engine, settings, poll_s=0.01)
        await runtime.start()
        try:
            await asyncio.wait_for(submitted.wait(), runtime.control_s)
            assert len(posts) == 1, (
                "Configured real CPU mock never reached durable submit"
            )
            assert posts[0]["seed"] == 17 and posts[0]["n_outputs"] == 2
            assert posts[0]["params"]["style"] == "  literal [Verse]  "
            with Session(engine) as session:
                row = session.scalar(select(JobAttempt).where(JobAttempt.job_id == jid))
                assert row.provenance.synthetic_binding.scope == "product"
        finally:
            await runtime.close()
        assert runtime.executor._shutdown and not runtime.native and not runtime.workers

    asyncio.run(run())


def test_registry_issues_only_exact_bound_identity_lease():
    from app.queue.synthetic_registry import SyntheticRegistry, TrustedSyntheticEntry

    class Backend:
        origin = "http://engine-mock:8199"

    backend = Backend()
    descriptor = real_mock_descriptor()
    health = Health(
        engine_id="mock",
        engine_version="0.1.0",
        image_digest="unknown",
        state="idle",
        gpu={"total_mb": 0, "free_mb": 0, "cap_mb": 0},
    )
    entry = TrustedSyntheticEntry.from_descriptor(
        backend,
        descriptor,
        recipe_id="declared-test-cpu",
        scope="test",
        engine_id="mock",
        engine_version="0.1.0",
        implementation={
            "name": "declared-fixture",
            "revision": "v1",
            "source_sha256": "a" * 64,
            "common_source_sha256": "b" * 64,
        },
    )
    registry = SyntheticRegistry((entry,))
    lease = registry.select(backend, descriptor, health)
    assert lease is not None, "Trusted recipe did not issue an authority lease"
    assert registry.check(lease, lease.binding)
    assert not registry.check(replace(lease), lease.binding)
    assert not SyntheticRegistry((entry,)).check(lease, lease.binding)
    assert registry.select(Backend(), descriptor, health) is None
    backend.origin = "http://another-origin:8199"
    assert not registry.check(lease, lease.binding)


def test_selected_lease_cannot_authorize_a_different_snapshot():
    from app.queue.provenance import SelectedProvenance
    from app.queue.synthetic_registry import SyntheticRegistry, TrustedSyntheticEntry
    from app.worker.contracts import SyntheticCapturedDescriptor
    from engine_contract import JobRequest, LoadRequest

    class Backend:
        origin = "http://engine-mock:8199"

    backend = Backend()
    descriptor = real_mock_descriptor()
    health = Health(
        engine_id="mock",
        engine_version="0.1.0",
        image_digest="unknown",
        state="idle",
        gpu={"total_mb": 0, "free_mb": 0, "cap_mb": 0},
    )
    entry = TrustedSyntheticEntry.from_descriptor(
        backend,
        descriptor,
        recipe_id="test-frozen",
        scope="test",
        engine_id="mock",
        engine_version="0.1.0",
        implementation={
            "name": "fixture",
            "revision": "1",
            "source_sha256": "a" * 64,
            "common_source_sha256": "b" * 64,
        },
    )
    registry = SyntheticRegistry((entry,))
    selected = SelectedProvenance.select(
        descriptor,
        health,
        "music.instrumental",
        "mock",
        "cpu",
        backend=backend,
        registry=registry,
    )
    request = JobRequest(
        job_id="01K70000000000000000000003",
        task="music.instrumental",
        model_id="mock",
        mode="cpu",
        output_dir="tmp/01K70000000000000000000003",
        timeout_s=60,
    )
    load = LoadRequest(model_id="mock", mode="cpu")
    assert selected.binds(request, load)
    changed = descriptor.model_dump(mode="json")
    changed["revision"] = "unadmitted"
    forged = replace(selected, descriptor=SyntheticCapturedDescriptor(changed))
    assert not forged.binds(request, load), (
        "Lease leaked authority to a substituted descriptor"
    )


def test_learned_serialization_remains_historical_in_nested_worker_json():
    from app.models import WorkerJSON
    from app.worker.contracts import CapturedProvenance, PostPlan
    from test_worker_contracts import plan, provenance

    value = CapturedProvenance.model_validate(provenance())
    nested = PostPlan.model_validate(plan())
    assert value.evidence_kind == "learned" and value.synthetic_binding is None
    assert "evidence_kind" not in value.model_dump(mode="json")
    assert "synthetic_binding" not in nested.model_dump(mode="json")["provenance"]
    assert (
        canonical_sha256(value)
        == "8fa06a6649e672e4fba9bf75c49a141037339f83b9de0c48031b9d4eb8346e65"
    )
    assert (
        canonical_sha256(nested)
        == "d15eb15db03be986d34a4e6b71a8412f1526f8a07ac4825aa01fcbadfc431b76"
    )
    serialized = WorkerJSON(PostPlan).process_bind_param(nested, None)
    assert canonical_sha256(serialized) == canonical_sha256(nested)


def test_trusted_entry_revalidates_a_model_copy_before_authority():
    import pytest
    from app.queue.synthetic_registry import SyntheticRegistry, TrustedSyntheticEntry

    class Backend:
        origin = "http://engine-mock:8199"

    backend = Backend()
    descriptor = real_mock_descriptor()
    entry = TrustedSyntheticEntry.from_descriptor(
        backend,
        descriptor,
        recipe_id="declared",
        scope="test",
        engine_id="mock",
        engine_version="0.1.0",
        implementation={
            "name": "fixture",
            "revision": "1",
            "source_sha256": "a" * 64,
            "common_source_sha256": "b" * 64,
        },
    )
    forged = entry.binding.model_copy(update={"implementation_sha256": "c" * 64})
    with pytest.raises(ValueError):
        SyntheticRegistry((replace(entry, binding=forged),))


def declared_cpu(*, expected_image_digest=None):
    from app.queue.synthetic_registry import SyntheticRegistry, TrustedSyntheticEntry

    class Backend:
        origin = "http://engine-mock:8199"

    backend = Backend()
    descriptor = real_mock_descriptor()
    health = Health(
        engine_id="mock",
        engine_version="0.1.0",
        image_digest="unknown",
        state="idle",
        gpu={"total_mb": 0, "free_mb": 0, "cap_mb": 0},
    )
    entry = TrustedSyntheticEntry.from_descriptor(
        backend,
        descriptor,
        recipe_id="explicit-cpu",
        scope="test",
        engine_id="mock",
        engine_version="0.1.0",
        expected_image_digest=expected_image_digest,
        implementation={
            "name": "fixture",
            "revision": "v1",
            "source_sha256": "a" * 64,
            "common_source_sha256": "b" * 64,
        },
    )
    return backend, descriptor, health, entry, SyntheticRegistry((entry,))


@pytest.mark.parametrize(
    "drift",
    [
        "descriptor",
        "origin",
        "identity",
        "version",
        "contract",
        "bad_digest",
        "backend",
    ],
)
def test_unregistered_or_drifted_recipe_does_not_select(drift):
    from app.queue.synthetic_registry import SyntheticRegistry

    backend, descriptor, health, _entry, registry = declared_cpu()
    assert SyntheticRegistry().select(backend, descriptor, health) is None
    if drift == "descriptor":
        descriptor.revision = "changed"
    elif drift == "origin":
        backend.origin = "http://another:8199"
    elif drift == "identity":
        health.engine_id = "other"
    elif drift == "version":
        health.engine_version = "other"
    elif drift == "contract":
        health = health.model_copy(update={"contract_version": "2"})
    elif drift == "bad_digest":
        health.image_digest = "synthetic"
    else:
        backend = type(backend)()
    assert registry.select(backend, descriptor, health) is None


@pytest.mark.parametrize(
    "invalid",
    [
        "bool_version",
        "recipe",
        "origin",
        "unknown_field",
        "implementation_sha",
        "implementation_extra",
        "image",
    ],
)
def test_binding_is_closed_bounded_and_typed(invalid):
    from app.worker.contracts import SyntheticBinding

    _, _, _, entry, _ = declared_cpu()
    value = entry.binding.model_dump(mode="json")
    if invalid == "bool_version":
        value["version"] = True
    elif invalid == "recipe":
        value["recipe_id"] = "x" * 129
    elif invalid == "origin":
        value["origin"] = "http://user:password@engine-mock:8199/path"
    elif invalid == "unknown_field":
        value["caller_authority"] = True
    elif invalid == "implementation_sha":
        value["implementation_sha256"] = "c" * 64
    elif invalid == "implementation_extra":
        value["implementation"]["extra"] = True
    else:
        value["expected_image_digest"] = "synthetic"
    with pytest.raises(ValueError):
        SyntheticBinding.model_validate(value)


@pytest.mark.parametrize(
    "invalid", ["weights", "remote_code", "external", "extra", "mode", "token", "huge"]
)
def test_synthetic_descriptor_remains_closed_and_deeply_immutable(invalid):
    from app.worker.contracts import SyntheticCapturedDescriptor

    value = real_mock_descriptor().model_dump(mode="json")
    snapshot = SyntheticCapturedDescriptor(value)
    exposed = snapshot.value
    exposed.revision = "mutated-copy"
    assert snapshot.value.revision == "synthetic-v1"
    if invalid == "weights":
        value["weights"] = [{"path": "mock.safetensors", "sha256": "a" * 64}]
    elif invalid == "remote_code":
        value["remote_code"] = [{"path": "adapter.py", "sha256": "a" * 64}]
    elif invalid == "external":
        value["provider"] = {"type": "external"}
    elif invalid == "extra":
        value["extra"] = True
    elif invalid == "mode":
        value["modes"] = []
    elif invalid == "token":
        value["tasks"]["music.song"]["params_schema"]["token"] = "secret"
    else:
        value["revision"] = "x" * 513
    with pytest.raises(ValueError):
        SyntheticCapturedDescriptor(value)


def selected_capture(registry, backend, descriptor, health):
    from app.queue.provenance import SelectedProvenance, capture_before_send
    from engine_contract import JobRequest, LoadRequest

    selected = SelectedProvenance.select(
        descriptor,
        health,
        "music.instrumental",
        "mock",
        "cpu",
        backend=backend,
        registry=registry,
    )
    request = JobRequest(
        job_id="01K70000000000000000000003",
        task="music.instrumental",
        model_id="mock",
        mode="cpu",
        output_dir="tmp/01K70000000000000000000003",
        timeout_s=60,
    )
    load = LoadRequest(model_id="mock", mode="cpu")
    captured = capture_before_send(
        selected, request, load, health, require_loaded=False
    )
    return selected, request, load, captured


def test_durable_capture_requires_fresh_exact_composition_to_rebind():
    from app.queue.provenance import SelectedProvenance
    from app.queue.synthetic_registry import SyntheticRegistry
    from app.worker.contracts import CapturedProvenance

    backend, descriptor, health, _entry, registry = declared_cpu()
    _, request, load, captured = selected_capture(registry, backend, descriptor, health)
    durable = CapturedProvenance.model_validate_json(captured.model_dump_json())
    with pytest.raises(ValueError):
        SelectedProvenance.from_captured(durable)
    with pytest.raises(ValueError):
        SelectedProvenance.from_captured(
            durable, backend=backend, registry=SyntheticRegistry()
        )
    new_backend, _, _, new_entry, new_registry = declared_cpu()
    selected = SelectedProvenance.from_captured(
        durable, backend=new_backend, registry=new_registry
    )
    assert selected.binds(request, load) and selected.registry is new_registry
    assert not selected.authorized(registry)
    changed = replace(
        new_entry,
        binding=new_entry.binding.model_copy(update={"recipe_id": "different"}),
    )
    with pytest.raises(ValueError):
        SelectedProvenance.from_captured(
            durable, backend=new_backend, registry=SyntheticRegistry((changed,))
        )
    assert durable.model_dump(mode="json")["evidence_kind"] == "synthetic"
    assert canonical_sha256(durable) != canonical_sha256(
        {
            k: v
            for k, v in durable.model_dump(mode="json").items()
            if k != "synthetic_binding"
        }
    )


def test_cpu_capture_unknown_and_later_observed_resident_are_distinct_evidence():
    from app.queue.provenance import capture_before_send
    from engine_contract import LoadedModel

    backend, descriptor, health, _, registry = declared_cpu()
    selected, request, load, first = selected_capture(
        registry, backend, descriptor, health
    )
    assert first.observed_model is None and first.reported_image_digest is None
    health.loaded = LoadedModel(model_id="mock", mode="cpu")
    second = capture_before_send(selected, request, load, health, require_loaded=False)
    assert second.observed_model.model_id == "mock"
    assert canonical_sha256(second) != canonical_sha256(first)
    health.loaded = LoadedModel(model_id="foreign", mode="cpu")
    with pytest.raises(ValueError):
        capture_before_send(selected, request, load, health, require_loaded=False)


def test_explicit_image_authority_is_not_inferred_from_reported_digest():
    backend, descriptor, health, _, registry = declared_cpu(
        expected_image_digest="sha256:" + "a" * 64
    )
    assert registry.select(backend, descriptor, health) is None
    health.image_digest = "sha256:" + "b" * 64
    assert registry.select(backend, descriptor, health) is None
    health.image_digest = "sha256:" + "a" * 64
    _, _, _, value = selected_capture(registry, backend, descriptor, health)
    assert (
        value.expected_image_digest
        == value.reported_image_digest
        == health.image_digest
    )


def test_packaged_cpu_recipe_matches_real_function_but_overrides_need_explicit_authority(
    engine,
):
    from app.queue.synthetic_registry import (
        packaged_mock_descriptor,
        packaged_mock_registry,
    )

    assert packaged_mock_descriptor() == real_mock_descriptor()
    backend, _, _, _, _ = declared_cpu()
    assert (
        len(
            packaged_mock_registry(
                {"mock": backend}, {"mock": backend.origin + "/"}
            ).entries
        )
        == 1
    )
    assert not packaged_mock_registry({}, {}).entries
    assert not packaged_mock_registry(
        {"mock": backend}, {"mock": "http://other:8199"}
    ).entries
    runtime = QueueRuntime(
        engine,
        ContractSettings(
            data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
            engine_token="private-test-only",
        ),
        backends={"mock": backend},
    )
    assert not runtime.synthetic_registry.entries
    asyncio.run(runtime.close())


def test_synthetic_capture_sql_cas_is_write_once_and_checks_same_registry(
    engine, monkeypatch
):
    from app.queue.admission import Admission, PreclaimResolutionError
    from app.queue.provenance import capture_before_send
    from app.queue.resolver import Resolver
    from app.queue.synthetic_registry import SyntheticRegistry
    from engine_contract import LoadedModel

    backend, descriptor, health, entry, registry = declared_cpu()

    async def models():
        return [descriptor]

    async def current_health():
        return health

    backend.models, backend.health = models, current_health
    jid, owner = add(
        engine,
        lane="cpu",
        request={"params": {}, "mode": "cpu", "seed": 7, "timeout_s": 60},
    )
    admission = Admission(engine, owner, synthetic_registry=registry)
    resolver = Resolver(
        {"mock": backend},
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        synthetic_registry=registry,
    )
    resolved = asyncio.run(resolver.resolve(admission.select(jid)))
    with pytest.raises(PreclaimResolutionError):
        Admission(
            engine, owner, synthetic_registry=SyntheticRegistry((entry,))
        ).reserve(resolved)
    claim = admission.reserve(resolved)
    value = capture_before_send(
        claim.selected_provenance,
        claim.request,
        claim.load_options,
        health,
        require_loaded=False,
    )
    sha = canonical_sha256(value)
    assert admission.capture_provenance(claim, value, sha)
    assert admission.capture_provenance(claim, value, sha)
    assert admission.may_send(claim)
    health.loaded = LoadedModel(model_id="mock", mode="cpu")
    observed = capture_before_send(
        claim.selected_provenance,
        claim.request,
        claim.load_options,
        health,
        require_loaded=False,
    )
    assert not admission.capture_provenance(claim, observed, canonical_sha256(observed))
    admission.synthetic_registry = SyntheticRegistry((entry,))
    assert not admission.may_send(claim)
    assert not admission.capture_provenance(claim, value, sha)
    admission.synthetic_registry = registry
    backend.origin = "http://changed:8199"
    assert not admission.may_send(claim)
    backend.origin = entry.binding.origin
    with Session(engine) as session:
        row = session.get(JobAttempt, claim.attempt_id)
        assert row.provenance == value and row.provenance_sha256 == sha
        assert row.provenance.observed_model is None
    # Un segundo claim ejercita la comprobación dentro de writer, tras el precheck.
    other, _ = add(
        engine,
        lane="cpu",
        request={"params": {}, "mode": "cpu", "seed": 8, "timeout_s": 60},
    )
    second = admission.reserve(asyncio.run(resolver.resolve(admission.select(other))))
    health.loaded = None
    fresh = capture_before_send(
        second.selected_provenance,
        second.request,
        second.load_options,
        health,
        require_loaded=False,
    )
    import app.queue.admission as module

    original = module.writer

    def changed_writer(session):
        original(session)
        backend.origin = "http://changed:8199"

    monkeypatch.setattr(module, "writer", changed_writer)
    assert not admission.capture_provenance(second, fresh, canonical_sha256(fresh))
    with Session(engine) as session:
        row = session.get(JobAttempt, second.attempt_id)
        assert row.provenance is None and row.provenance_sha256 is None


@pytest.mark.parametrize(
    "change",
    [
        "implicit",
        "wrong_branch",
        "learned_binding",
        "unknown_kind",
        "descriptor_sha",
        "identity",
        "unverified",
        "bad_mode",
    ],
)
def test_captured_evidence_branch_is_explicit_and_consistent(change):
    from app.worker.contracts import CapturedDescriptor, CapturedProvenance
    from test_worker_contracts import provenance

    backend, descriptor, health, _, registry = declared_cpu()
    _, _, _, value = selected_capture(registry, backend, descriptor, health)
    body = value.model_dump(mode="json")
    if change == "implicit":
        body.pop("evidence_kind")
        body.pop("synthetic_binding")
    elif change == "wrong_branch":
        body["descriptor"] = CapturedDescriptor(provenance()["descriptor"])
    elif change == "learned_binding":
        body["evidence_kind"] = "learned"
    elif change == "unknown_kind":
        body["evidence_kind"] = "caller"
    elif change == "descriptor_sha":
        body["synthetic_binding"]["descriptor_sha256"] = "c" * 64
    elif change == "identity":
        body["engine_id"] = "other"
    elif change == "unverified":
        body["descriptor"]["tasks"]["music.instrumental"]["verified"] = False
        body["synthetic_binding"]["descriptor_sha256"] = canonical_sha256(
            body["descriptor"]
        )
    else:
        body["load"]["mode"] = "offload"
    with pytest.raises(ValueError):
        CapturedProvenance.model_validate(body)


def test_synthetic_captured_before_terminal_binds_real_sql_publication_revision(engine):
    """SQL estructural real; artifacts/timing/tool pin son fixtures, no WAV generado."""
    from app.models import (
        CpuExecution,
        Job,
        PublicationIntent,
        PublicationIntentRevision,
        Take,
        new_id,
    )
    from app.worker.contracts import PostPlan, PublicationAuthority
    from sqlalchemy import text
    from test_queue_chains import create, services
    from test_queue_references import accepted

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)

    def declared_seed_metadata(artifacts):
        for index, artifact in enumerate(artifacts):
            artifact["meta"] = {"seed": 17 + index}

    claim, artifacts = accepted(
        engine, chain, resolver, owner, artifact_mutator=declared_seed_metadata
    )
    execution_id, intent_id, revision_id = new_id(), new_id(), new_id()
    with Session(engine) as session:
        attempt = session.get(JobAttempt, claim.attempt_id)
        provenance = attempt.provenance
        capture_sha = attempt.provenance_sha256
        terminal_sha = canonical_sha256(attempt.terminal)
        assert (
            provenance.evidence_kind == "synthetic"
            and provenance.descriptor.value.weights == []
        )
        post = session.get(Job, chain.post_job_id)
        post.status, post.attempt = "running", 1
        take = session.get(Take, chain.take_ids[0])
        authority = PublicationAuthority(
            owner_id=owner,
            song_id=song,
            post_job_id=post.id,
            generation_job_id=claim.job_id,
            winning_attempt_id=attempt.id,
            winning_ordinal=attempt.ordinal,
            terminal_seq=attempt.last_seq,
            terminal_sha256=terminal_sha,
            take_id=take.id,
            output_index=0,
            seed=take.seed,
            provenance_sha256=capture_sha,
        )
        source_path = resolver.data_dir / artifacts[0]["path"]
        source = {
            "path": "data/" + artifacts[0]["path"],
            "sha256": artifacts[0]["sha256"],
            "media_type": "audio/wav",
            "bytes": source_path.stat().st_size,
            "duration_s": 1.0,
        }
        plan = PostPlan(
            version=1,
            handler="post.audio",
            handler_version=1,
            owner_id=owner,
            song_id=song,
            post_job_id=post.id,
            generation_job_id=claim.job_id,
            request_sha256=canonical_sha256(post.request),
            tool_pin_sha256="b" * 64,
            provenance=provenance,
            takes=[
                {
                    "authority": authority,
                    "source": source,
                    "copy": {
                        **source,
                        "path": f"data/tmp/_server_inputs/{execution_id}/0.wav",
                    },
                }
            ],
        )
        session.flush()
        session.add(
            CpuExecution(
                id=execution_id,
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
                supervisor_epoch="fixture-epoch",
                lease_token="fixture-lease",
                process_identity={"pid": 123, "birth": "declared-fixture"},
                cleanup_state="unknown",
            )
        )
        session.flush()
        session.add(
            PublicationIntent(
                id=intent_id,
                owner_id=owner,
                song_id=song,
                take_id=take.id,
                output_index=0,
                seed=take.seed,
                state="reserved",
                revision=1,
            )
        )
        session.flush()
        session.add(
            PublicationIntentRevision(
                id=revision_id,
                **authority.model_dump(exclude={"owner_id"}),
                owner_id=owner,
                intent_id=intent_id,
                cpu_execution_id=execution_id,
                source_sha256=source["sha256"],
                stage_path=f"songs/{song}/takes/.pending-{execution_id}/{take.id}",
                final_path=f"songs/{song}/takes/{take.id}",
            )
        )
        session.commit()
    with Session(engine) as session:
        stored = session.get(CpuExecution, execution_id)
        revision = session.get(PublicationIntentRevision, revision_id)
        assert stored.plan.provenance.evidence_kind == "synthetic"
        assert stored.plan.provenance.synthetic_binding == provenance.synthetic_binding
        assert stored.plan_sha256 == canonical_sha256(stored.plan)
        assert revision.provenance_sha256 == capture_sha
        assert (
            session.execute(
                text(
                    "SELECT json_extract(plan,'$.provenance.evidence_kind') FROM cpu_execution WHERE id=:id"
                ),
                {"id": execution_id},
            ).scalar_one()
            == "synthetic"
        )


def test_busy_routing_does_not_issue_selection_but_full_resolution_captures():
    from app.queue.provenance import capture_before_send
    from test_queue_resolver import Catalog, job, resolver

    async def run():
        backend = Catalog()
        original_health = backend.health

        async def busy():
            return (await original_health()).model_copy(
                update={"state": "busy", "job_id": "01K70000000000000000000003"}
            )

        backend.health = busy
        selected_job = job()
        service = resolver(backend)
        routed = await service.route(selected_job, {})
        assert routed.lane == "gpu" and routed.mode == "bf16"
        assert routed.selected_provenance is None, (
            "Routing emitted selection authority before busy rejection"
        )
        assert not service.synthetic_registry._issued
        backend.health = original_health
        resolved = await service.resolve(selected_job)
        assert resolved.selected_provenance.evidence_kind == "synthetic"
        assert resolved.selected_provenance.authorized(service.synthetic_registry)
        request, load = resolved.freeze(selected_job.id)
        await backend.load(load)
        captured = capture_before_send(
            resolved.selected_provenance,
            request,
            load,
            await backend.health(),
            require_loaded=True,
        )
        assert (
            captured.synthetic_binding == resolved.selected_provenance.synthetic_binding
        )
        assert captured.observed_model.mode == "bf16"

    asyncio.run(run())
