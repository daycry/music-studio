"""Cancelación HTTP y listener SSE reales; catálogo sintético sin workers."""

import asyncio
import os
import threading
from pathlib import Path
from uuid import uuid4

import pytest
from app.models import Job, Take
from app.publication import PublicationCoordinator
from app.queue.cancellation import Cancellation
from app.queue.events import EventBus
from app.sse import StreamClosed, TrustedFeedScope
from fastapi.testclient import TestClient
from sqlalchemy import event as sql_event
from sqlalchemy.orm import Session
from test_api_t07 import SONG, mock_app
from test_domain_routes import headers, issue
from test_queue_chains import create, services
from test_queue_chains import engine as engine  # noqa: PLC0414
from test_queue_terminal_takes import prepared_chain


def test_cancel_barrier_timeout_returns_503_without_rows_or_feed_changes(tmp_path):
    with TestClient(
        mock_app(tmp_path),
        base_url="http://127.0.0.1:8000",
        raise_server_exceptions=False,
    ) as client:
        token = issue(client)
        created = client.post("/api/generations", headers=headers(token), json=SONG)
        assert created.status_code == 202, created.text
        chain = created.json()
        runtime = client.app.state.queue
        coordinator = PublicationCoordinator(acquisition_timeout=0.01)
        runtime.publication_coordinator = coordinator
        bus = runtime.bus

        async def subscribe():
            return bus.subscribe(
                TrustedFeedScope(client.app.state.session_owner_id), bus.cursor
            )

        subscriber = client.portal.call(subscribe)
        old_epoch, old_cursor = bus.epoch, bus.cursor
        held, release = threading.Event(), threading.Event()

        def hold():
            with coordinator.barrier():
                held.set()
                assert release.wait(5)

        thread = threading.Thread(target=hold)
        thread.start()
        assert held.wait(2)
        try:
            response = client.post(
                f"/api/jobs/{chain['generation_job_id']}/cancel", headers=headers(token)
            )
            assert response.status_code == 503, response.text
            assert response.json()["code"] == "SERVICE_UNAVAILABLE"
            assert (bus.epoch, bus.cursor) == (old_epoch, old_cursor)
            with Session(client.app.state.db) as session:
                job = session.get(Job, chain["generation_job_id"])
                assert job.status == "queued" and job.cancel_requested_at is None
                assert all(
                    session.get(Take, tid).status == "queued"
                    for tid in chain["take_ids"]
                )

            async def no_event():
                with pytest.raises(TimeoutError):
                    await asyncio.wait_for(subscriber.next(), 0.02)

            client.portal.call(no_event)
        finally:
            release.set()
            thread.join(2)
            subscriber.close()
        assert not thread.is_alive()


def test_queued_cancel_http_invalidates_live_feed_after_committed_take_terminal():
    path = (
        Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]).parent / "cancel-api" / uuid4().hex
    )
    path.mkdir(parents=True)
    with TestClient(mock_app(path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post("/api/generations", headers=headers(token), json=SONG)
        assert response.status_code == 202, response.text
        chain = response.json()
        runtime = client.app.state.queue
        runtime.publication_coordinator = PublicationCoordinator()
        bus = runtime.bus

        async def subscribe():
            return bus.subscribe(
                TrustedFeedScope(client.app.state.session_owner_id), bus.cursor
            )

        subscriber = client.portal.call(subscribe)
        old_epoch = bus.epoch
        commit_epochs = []

        def committed(session):
            if session.bind is client.app.state.db:
                commit_epochs.append(bus.epoch)

        sql_event.listen(Session, "after_commit", committed)
        try:
            response = client.post(
                f"/api/jobs/{chain['generation_job_id']}/cancel", headers=headers(token)
            )
            assert response.status_code == 202, response.text
            with Session(client.app.state.db) as session:
                assert (
                    session.get(Job, chain["generation_job_id"]).status == "cancelled"
                )
                assert all(
                    session.get(Take, tid).status == "cancelled"
                    for tid in chain["take_ids"]
                )

            async def read():
                return await asyncio.wait_for(subscriber.next(), 0.3)

            with pytest.raises(StreamClosed, match="gap"):
                client.portal.call(read)
            assert bus.epoch != old_epoch
            assert commit_epochs == [old_epoch]
            stable = bus.epoch
            repeated = client.post(
                f"/api/jobs/{chain['generation_job_id']}/cancel", headers=headers(token)
            )
            assert repeated.status_code == 202
            assert repeated.json()["cancel_requested"] is False
            forbidden = client.post(
                f"/api/jobs/{'0' * 26}/cancel", headers=headers(token)
            )
            assert forbidden.status_code == 403
            assert bus.epoch == stable
        finally:
            sql_event.remove(Session, "after_commit", committed)
            subscriber.close()


def test_cancellation_nochange_and_scope_rejection_preserve_epoch(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    bus, coordinator = EventBus(), PublicationCoordinator()
    service = Cancellation(engine, owner, coordinator=coordinator, bus=bus)
    old = bus.epoch
    with pytest.raises(ValueError, match="Local job absent"):
        service.request("0" * 26)
    assert bus.epoch == old
    assert service.pending() == [] and bus.epoch == old
    assert service.request(chain.generation_job_id)
    changed = bus.epoch
    assert changed != old
    assert not service.request(chain.generation_job_id)
    assert service.pending() == [] and bus.epoch == changed


def test_pending_only_invalidates_when_it_terminalizes_a_queued_job(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    with Session(engine) as session, session.begin():
        session.get(
            Job, chain.generation_job_id
        ).cancel_requested_at = "2026-11-05T00:00:00Z"
    bus = EventBus()
    service = Cancellation(engine, owner, coordinator=PublicationCoordinator(), bus=bus)
    old = bus.epoch
    assert service.pending() == []
    assert old != bus.epoch
    with Session(engine) as session:
        assert all(
            session.get(Take, tid).status == "cancelled" for tid in chain.take_ids
        )
    old = bus.epoch
    assert service.pending() == [] and old == bus.epoch


def test_repeated_running_cancel_and_pending_observation_do_not_invalidate(engine):
    owner, _, chain, _, claim = prepared_chain(engine)
    bus = EventBus()
    service = Cancellation(engine, owner, coordinator=PublicationCoordinator(), bus=bus)
    assert service.request(chain.generation_job_id)
    old = bus.epoch
    assert service.request(chain.generation_job_id)
    assert bus.epoch == old
    assert service.pending() == [(claim.attempt_id, "mock")]
    assert bus.epoch == old
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).status == "running"
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)


def test_precommit_failure_rolls_back_real_rows_and_preserves_feed(engine, monkeypatch):
    from app.queue import cancellation

    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    bus = EventBus()
    service = Cancellation(engine, owner, coordinator=PublicationCoordinator(), bus=bus)
    original = cancellation.terminalize_placeholders
    primary = RuntimeError("injected before commit")

    def reject(*args):
        original(*args)
        raise primary

    monkeypatch.setattr(cancellation, "terminalize_placeholders", reject)
    old = bus.epoch
    with pytest.raises(RuntimeError) as caught:
        service.request(chain.generation_job_id)
    assert caught.value is primary and bus.epoch == old
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).status == "queued"
        assert all(session.get(Take, tid).status == "queued" for tid in chain.take_ids)


def test_commit_uncertainty_preserves_durable_terminal_and_invalidates(engine):
    owner, song, _, resolver = services(engine)
    chain = create(engine, owner, song, resolver)
    bus = EventBus()
    service = Cancellation(engine, owner, coordinator=PublicationCoordinator(), bus=bus)
    primary = RuntimeError("injected after actual commit")

    def committed(session):
        if session.bind is engine:
            raise primary

    sql_event.listen(Session, "after_commit", committed)
    old = bus.epoch
    try:
        with pytest.raises(RuntimeError) as caught:
            service.request(chain.generation_job_id)
        assert caught.value is primary
    finally:
        sql_event.remove(Session, "after_commit", committed)
    assert bus.epoch != old
    with Session(engine) as session:
        assert session.get(Job, chain.generation_job_id).status == "cancelled"
        assert all(
            session.get(Take, tid).status == "cancelled" for tid in chain.take_ids
        )


@pytest.mark.parametrize(
    "coordinator,bus",
    [(PublicationCoordinator(), None), (None, EventBus()), (object(), EventBus())],
)
def test_cancellation_rejects_partial_or_untrusted_composition(
    engine, coordinator, bus
):
    with pytest.raises(TypeError):
        Cancellation(engine, "owner", coordinator=coordinator, bus=bus)
