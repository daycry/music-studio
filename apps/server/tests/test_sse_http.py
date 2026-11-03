"""Contrato HTTP mínimo del stream SSE autenticado por sesión local."""

import asyncio
import json
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from app import event_routes, models
from app.event_dtos import SessionCredentialDTO
from app.main import create_app
from app.queue.events import EventBus, EventConsumer
from app.settings import ContractSettings
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_dispatcher_recovery import event as engine_event
from test_dispatcher_recovery import prepared

ORIGIN = "http://127.0.0.1:3000"
BOOT = {"Origin": ORIGIN, "X-Studio-Session-Bootstrap": "1"}
UNIT = Path.cwd() / ".cache/dev-cycle/m1/t06-session-http"


@pytest.fixture
def tmp_path():
    path = Path.cwd() / ".cache/dev-cycle/20261103-cpu-m1/t06/fixtures" / uuid4().hex
    path.mkdir(parents=True)
    return path


class QueueWithBus:
    def __init__(self, engine, settings):
        self.bus = EventBus()
        self.closed = False

    async def start(self):
        pass

    async def close(self):
        self.closed = True
        self.bus.shutdown()


def config(tmp_path):
    return ContractSettings(engine_token="internal-engine-private", data_dir=tmp_path)


@contextmanager
def connection(tmp_path):
    app = create_app(config(tmp_path), queue_runtime_factory=QueueWithBus)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        yield client


def issue(client):
    response = client.post("/api/session/bootstrap", headers=BOOT)
    assert response.status_code == 200, response.text
    return SessionCredentialDTO.model_validate(response.json()).session_token


def test_events_requires_public_session(tmp_path):
    with connection(tmp_path) as client:
        response = client.get("/api/events", headers={"Origin": ORIGIN})
        assert response.status_code == 401
        assert response.json()["code"] == "SESSION_REQUIRED"


def test_events_rejects_untrusted_query_ids_before_stream(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        base = {
            "Origin": ORIGIN,
            "X-Studio-Session-Token": token,
        }
        invalid = client.get("/api/events?known_job_id=not-an-ulid", headers=base)
        assert invalid.status_code == 422
        unknown = client.get(
            "/api/events?known_job_id=01K70000000000000000000001", headers=base
        )
        assert unknown.status_code == 403
        extra = client.get("/api/events?owner_id=private", headers=base)
        assert extra.status_code == 422


def test_events_bootstrap_emits_bounded_snapshot(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        status, body = asyncio.run(
            read_stream(
                client, token, "", stop=lambda c: b'"phase":"end"' in b"".join(c)
            )
        )
        assert status == 200
        assert b"event: system.status" in body
        assert b'"phase":"begin"' in body


def test_events_replays_last_event_id_for_owner(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        with Session(client.app.state.db) as session, session.begin():
            owner = session.scalar(
                select(models.User.id).where(models.User.name == "local")
            )
            song_id = "01K70000000000000000000001"
            job_id = "01K70000000000000000000002"
            session.add(models.Song(id=song_id, owner_id=owner, title="SSE"))
            session.add(
                models.Job(
                    id=job_id,
                    owner_id=owner,
                    song_id=song_id,
                    task="music.instrumental",
                    lane="gpu",
                    status="running",
                    request={"seed": 17},
                )
            )
        bus = client.app.state.queue.bus
        bus.publish(
            {
                "job_id": job_id,
                "song_id": song_id,
                "owner_id": owner,
                "type": "job.progress",
                "ts": "2026-10-09T00:00:00.123Z",
                "data": {"status": "running", "fraction": 0.5},
            }
        )
        status, body = asyncio.run(
            read_stream(
                client,
                token,
                "",
                extra_headers={"last-event-id": f"{bus.epoch}:1"},
                stop=lambda c: b"event: job.progress" in b"".join(c),
            )
        )
        assert status == 200
        assert b"event: job.progress" in body
        assert b'"fraction":0.5' in body


# --- T-06: productor real, heartbeat que no cierra y ámbito de jobs terminales ---


async def read_stream(client, token, query, *, stop, extra_headers=None, timeout=5.0):
    """Ejecuta GET /api/events directo sobre ASGI y devuelve los chunks del cuerpo."""
    disconnect = asyncio.Event()
    chunks, start = [], {}
    headers = [
        (b"host", b"127.0.0.1:8000"),
        (b"origin", ORIGIN.encode()),
        (b"accept", b"text/event-stream"),
        (b"x-studio-session-token", token.encode()),
    ] + [(k.lower().encode(), v.encode()) for k, v in (extra_headers or {}).items()]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/events",
        "raw_path": b"/api/events",
        "query_string": query.encode(),
        "headers": headers,
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8000),
    }
    done = asyncio.Event()

    async def receive():
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            start["status"] = message["status"]
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))
            if stop(chunks):
                done.set()

    task = asyncio.create_task(client.app(scope, receive, send))
    try:
        await asyncio.wait_for(done.wait(), timeout)
    except asyncio.TimeoutError:
        pass
    finally:
        disconnect.set()
        await asyncio.wait_for(task, 5)
    return start.get("status"), b"".join(chunks)


def seed_job(client):
    """Job running con intento real en la BD de la app; devuelve el productor."""
    jid, owner, claim = prepared(client.app.state.db)
    bus = client.app.state.queue.bus
    consumer = EventConsumer(client.app.state.db, owner, bus)
    with Session(client.app.state.db) as session:
        song_id = session.get(models.Job, jid).song_id
    return jid, song_id, claim, consumer


@pytest.mark.parametrize("replay", [False, True])
def test_events_song_filter_all_real_producer_events(tmp_path, replay):
    with connection(tmp_path) as client:
        token = issue(client)
        _, song_id, claim, consumer = seed_job(client)
        bus = client.app.state.queue.bus
        cursor = bus.cursor

        def produce():
            for seq, (kind, data) in enumerate(
                [
                    ("stage", {"stage": "sampling"}),
                    ("progress", {"fraction": 0.5}),
                    (
                        "done",
                        {
                            "artifacts": [],
                            "telemetry": {
                                "mode": "bf16",
                                "model_revision": "synthetic",
                            },
                        },
                    ),
                ],
                1,
            ):
                assert consumer.accept(
                    claim.attempt_id,
                    "mock",
                    engine_event(claim.attempt_id, kind, data, seq),
                )

        async def scenario():
            if replay:
                await asyncio.to_thread(produce)

            async def live_producer():
                while bus.subscriber_count == 0:
                    await asyncio.sleep(0.01)
                await asyncio.to_thread(produce)

            producer = None if replay else asyncio.create_task(live_producer())
            try:
                return await read_stream(
                    client,
                    token,
                    f"song_id={song_id}",
                    extra_headers={"last-event-id": cursor},
                    stop=lambda c: b"event: job.done" in b"".join(c),
                    timeout=1.0,
                )
            finally:
                if producer is not None:
                    if not producer.done():
                        producer.cancel()
                    results = await asyncio.gather(producer, return_exceptions=True)
                    for result in results:
                        if isinstance(result, Exception):
                            raise result

        status, body = asyncio.run(scenario())
        assert status == 200
        for kind in ("stage", "progress", "done"):
            assert f"event: job.{kind}".encode() in body
        assert body.count(f'"song_id":"{song_id}"'.encode()) == 3


def test_events_song_filter_delivers_real_producer_envelope(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        _, song_id, claim, consumer = seed_job(client)
        bus = client.app.state.queue.bus
        epoch = bus.epoch
        consumer.accept(
            claim.attempt_id,
            "mock",
            engine_event(claim.attempt_id, "progress", {"fraction": 0.5}),
        )
        status, body = asyncio.run(
            read_stream(
                client,
                token,
                f"song_id={song_id}",
                extra_headers={"Last-Event-ID": f"{epoch}:1"},
                stop=lambda c: b"job.progress" in b"".join(c),
                timeout=2.0,
            )
        )
        assert status == 200
        assert b"event: job.progress" in body
        assert f'"song_id":"{song_id}"'.encode() in body


def test_events_live_real_producer_with_song_filter(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        _, song_id, claim, consumer = seed_job(client)

        async def scenario():
            async def produce():
                await asyncio.sleep(0.3)
                await asyncio.to_thread(
                    consumer.accept,
                    claim.attempt_id,
                    "mock",
                    engine_event(claim.attempt_id, "progress", {"fraction": 0.25}),
                )

            producer = asyncio.create_task(produce())
            result = await read_stream(
                client,
                token,
                f"song_id={song_id}",
                stop=lambda c: b"job.progress" in b"".join(c),
                timeout=3.0,
            )
            await producer
            return result

        status, body = asyncio.run(scenario())
        assert status == 200
        assert b"event: job.progress" in body
        assert b'"fraction":0.25' in body


def test_events_heartbeat_does_not_close_the_stream(tmp_path, monkeypatch):
    monkeypatch.setattr(event_routes, "HEARTBEAT_SECONDS", 0.05)
    with connection(tmp_path) as client:
        token = issue(client)
        _, song_id, claim, consumer = seed_job(client)

        async def scenario():
            async def produce():
                await asyncio.sleep(0.4)
                await asyncio.to_thread(
                    consumer.accept,
                    claim.attempt_id,
                    "mock",
                    engine_event(claim.attempt_id, "progress", {"fraction": 0.75}),
                )

            producer = asyncio.create_task(produce())
            result = await read_stream(
                client,
                token,
                f"song_id={song_id}",
                stop=lambda c: b"job.progress" in b"".join(c),
                timeout=3.0,
            )
            await producer
            return result

        status, body = asyncio.run(scenario())
        assert status == 200
        assert body.count(b": keep-alive") >= 2
        assert b"event: job.progress" in body
        assert b'"fraction":0.75' in body
        assert body.rindex(b": keep-alive") < body.index(b"event: job.progress")


@pytest.mark.parametrize("song_filter", [False, True])
def test_events_scope_ignores_terminal_jobs(tmp_path, song_filter):
    with connection(tmp_path) as client:
        token = issue(client)
        jid, song_id, claim, consumer = seed_job(client)
        with Session(client.app.state.db) as session, session.begin():
            owner = session.get(models.Job, jid).owner_id
            for index in range(68):
                session.add(
                    models.Job(
                        id=f"01K7{index:022d}",
                        owner_id=owner,
                        song_id=song_id,
                        task="music.instrumental",
                        lane="gpu",
                        status="succeeded",
                        request={"seed": index},
                    )
                )

        async def scenario():
            async def produce():
                await asyncio.sleep(0.3)
                await asyncio.to_thread(
                    consumer.accept,
                    claim.attempt_id,
                    "mock",
                    engine_event(claim.attempt_id, "progress", {"fraction": 0.5}),
                )

            producer = asyncio.create_task(produce())
            result = await read_stream(
                client,
                token,
                f"song_id={song_id}" if song_filter else "",
                stop=lambda c: b"job.progress" in b"".join(c),
                timeout=3.0,
            )
            await producer
            return result

        status, body = asyncio.run(scenario())
        assert status == 200
        assert b"event: job.progress" in body
        snapshots = [
            json.loads(line[6:])
            for line in body.splitlines()
            if line.startswith(b"data: ") and b'"system.status"' in line
        ]
        # Los 68 terminales no agrandan el snapshot inicial de jobs activos.
        assert all(len(frame["data"].get("jobs", [])) <= 64 for frame in snapshots)


def test_events_large_scope_never_authorizes_another_owner(tmp_path, monkeypatch):
    monkeypatch.setattr(event_routes, "HEARTBEAT_SECONDS", 0.01)
    with connection(tmp_path) as client:
        token = issue(client)
        _, song_id, _, _ = seed_job(client)
        foreign_owner, foreign_song, foreign_job = [models.new_id() for _ in range(3)]
        # La BD M1 sólo admite el usuario local. Un sobre con otro owner
        # no obtiene autoridad por declarar IDs ajenos en el bus.
        bus = client.app.state.queue.bus
        cursor = bus.cursor
        bus.publish(
            {
                "job_id": foreign_job,
                "song_id": foreign_song,
                "owner_id": foreign_owner,
                "type": "job.progress",
                "ts": "2026-10-09T00:00:00Z",
                "data": {"status": "running", "fraction": 0.5},
            }
        )
        status, body = asyncio.run(
            read_stream(
                client,
                token,
                "",
                extra_headers={"last-event-id": cursor},
                stop=lambda c: b": keep-alive" in b"".join(c),
            )
        )
        assert status == 200
        assert foreign_job.encode() not in body
        for query in (
            f"known_job_id={foreign_job}",
            f"song_id={foreign_song}",
            f"song_id={song_id}&known_job_id={foreign_job}",
        ):
            response = client.get(
                f"/api/events?{query}",
                headers={
                    "Origin": ORIGIN,
                    "X-Studio-Session-Token": token,
                },
            )
            assert response.status_code == 403
