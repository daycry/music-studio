"""Identidad fresca restrictiva antes de conceder procedencia (ADR-0068)."""

import asyncio
import os
from pathlib import Path

import pytest
from app.models import Job, JobAttempt
from app.queue.dispatcher import Dispatcher
from app.queue.resolver import ResolutionError, Resolver
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_dispatcher_admission import add, admission
from test_dispatcher_admission import engine as native_engine
from test_queue_resolver import Catalog, descriptor


@pytest.fixture(name="engine")
def drift_engine():
    yield from native_engine.__wrapped__()


def composition(engine, owner):
    # Declaración previa al catálogo; no se acredita la identidad cambiada.
    backend = Catalog(recipes=[descriptor()])
    resolver = Resolver(
        {"mock": backend},
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        synthetic_registry=backend.synthetic_registry,
    )
    return Dispatcher(
        admission(engine, owner, synthetic_registry=resolver.synthetic_registry),
        resolver,
    ), backend


@pytest.mark.parametrize("explicit", [True, False])
def test_identity_drift_before_selected_provenance(engine, monkeypatch, explicit):
    jid, owner = add(engine)
    dispatcher, backend = composition(engine, owner)
    versions, effects = [], []
    original_health = backend.health

    async def health():
        backend.version = "1" if not versions else "changed"
        value = await original_health()
        versions.append(value.engine_version)
        return value

    async def forbidden(request):
        effects.append(request)
        raise AssertionError("Drift must not load or submit")

    def reserve(resolved):
        effects.append(resolved)
        raise AssertionError("Drift must not reserve")

    def lease(registry, entry):
        effects.append(entry)
        raise AssertionError("Drift must not grant a lease")

    backend.health = health
    backend.load = backend.submit = forbidden
    dispatcher.admission.reserve = reserve
    monkeypatch.setattr(type(backend.synthetic_registry), "_lease", lease)
    assert asyncio.run(dispatcher.dispatch(jid if explicit else None)) is None
    assert versions == ["1", "changed"]
    assert effects == []
    assert backend.origin not in dispatcher.resolver._cache
    with Session(engine) as session:
        assert (session.get(Job, jid).status, session.get(Job, jid).attempt) == (
            "queued",
            0,
        )
        assert not session.scalars(select(JobAttempt)).all()


def test_stable_identity_preserves_resolve_wrapper_and_provenance(engine):
    from app.queue.backends.protocol import Submission

    jid, owner = add(engine)
    dispatcher, backend = composition(engine, owner)
    original = dispatcher.resolver.resolve
    observed, sends = [], []

    async def wrapped(job, **kwargs):
        observed.append(kwargs["expected_route"])
        return await original(job, **kwargs)

    async def submit(request):
        sends.append(request.job_id)
        return Submission(job_id=request.job_id)

    dispatcher.resolver.resolve = wrapped
    backend.submit = submit
    claim = asyncio.run(dispatcher.dispatch(jid))
    assert claim is not None and claim.job_id == jid
    assert len(observed) == 1 and observed[0].identity == ("mock", "1", "unknown")
    assert observed[0].backend is backend
    assert sends == [claim.attempt_id]
    with Session(engine) as session:
        attempt = session.get(JobAttempt, claim.attempt_id)
        assert attempt.provenance is not None
        assert session.get(Job, jid).attempt == 1


@pytest.mark.parametrize("invalid", ["params", "binding"])
def test_initial_invalid_explicit_request_still_raises(engine, invalid):
    from app.queue.synthetic_registry import SyntheticRegistry

    jid, owner = add(engine)
    dispatcher, _backend = composition(engine, owner)
    if invalid == "binding":
        dispatcher.resolver.synthetic_registry = SyntheticRegistry()
    else:
        with Session(engine) as session:
            session.get(Job, jid).request = {"params": {"duration_s": -1}}
            session.commit()
    with pytest.raises(ResolutionError):
        asyncio.run(dispatcher.dispatch(jid))
    with Session(engine) as session:
        assert session.get(Job, jid).attempt == 0
        assert not session.scalars(select(JobAttempt)).all()


def test_resolver_without_routing_context_keeps_binding_error(engine):
    jid, owner = add(engine)
    dispatcher, backend = composition(engine, owner)
    backend.version = "changed"
    with Session(engine) as session:
        job = session.get(Job, jid)
        session.expunge(job)
    with pytest.raises(ResolutionError):
        asyncio.run(dispatcher.resolver.resolve(job, engine=engine))


@pytest.mark.parametrize("change", ["backend", "origin"])
def test_selected_backend_binding_drift_discards_before_lease(
    engine, monkeypatch, change
):
    jid, owner = add(engine)
    dispatcher, backend = composition(engine, owner)
    replacement = Catalog(recipes=[descriptor()])
    original_screen = dispatcher._screen
    origin = backend.origin
    effects = []

    async def screen(routed, observations, occupancy):
        allowed = await original_screen(routed, observations, occupancy)
        if change == "backend":
            dispatcher.resolver.backends["mock"] = replacement
        else:
            backend.origin = "http://engine-analysis:8199"
        return allowed

    def forbidden(*args):
        effects.append(args)
        raise AssertionError("Stale binding cannot grant authority")

    dispatcher._screen = screen
    dispatcher.admission.reserve = forbidden
    monkeypatch.setattr(type(backend.synthetic_registry), "_lease", forbidden)
    assert asyncio.run(dispatcher.dispatch(jid)) is None
    assert effects == []
    assert origin not in dispatcher.resolver._cache
    with Session(engine) as session:
        assert session.get(Job, jid).attempt == 0
        assert not session.scalars(select(JobAttempt)).all()


@pytest.mark.parametrize("explicit", [True, False])
def test_selected_backend_replaced_during_prior_catalog(engine, monkeypatch, explicit):
    from synthetic_composition import composition as declared_composition

    jid, owner = add(engine, engine_id="mock")
    recipe = descriptor()
    other = Catalog(
        origin="http://engine-analysis:8199", engine_id="other", recipes=[recipe]
    )
    selected = Catalog(recipes=[recipe])
    replacement = Catalog(recipes=[recipe])
    backends = {"other": other, "selected": selected}
    registry = declared_composition(backends)
    resolver = Resolver(
        backends,
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        synthetic_registry=registry,
    )
    dispatcher = Dispatcher(
        admission(engine, owner, synthetic_registry=registry), resolver
    )
    observed, effects = [], []

    def health_callback(backend, name):
        original = backend.health

        async def health():
            value = await original()
            observed.append(name)
            if name == "other":
                value = value.model_copy(update={"engine_id": "other"})
                if observed.count("other") == 2:
                    resolver.backends["selected"] = replacement
            return value

        return health

    async def forbidden_request(request=None):
        effects.append(request)
        raise AssertionError("Replacement must not load, unload or submit")

    def forbidden_authority(*args):
        effects.append(args)
        raise AssertionError("Replacement must not grant a lease or reserve")

    for backend, name in [
        (other, "other"),
        (selected, "selected"),
        (replacement, "replacement"),
    ]:
        backend.health = health_callback(backend, name)
        backend.load = backend.unload = backend.submit = forbidden_request
    dispatcher.admission.reserve = forbidden_authority
    monkeypatch.setattr(type(registry), "_lease", forbidden_authority)
    assert asyncio.run(dispatcher.dispatch(jid if explicit else None)) is None
    assert selected.origin not in resolver._cache
    assert effects == []
    assert observed == ["other", "selected", "other"]
    assert (other.calls, selected.calls, replacement.calls) == (1, 1, 0)
    with Session(engine) as session:
        assert (session.get(Job, jid).status, session.get(Job, jid).attempt) == (
            "queued",
            0,
        )
        assert not session.scalars(select(JobAttempt)).all()
