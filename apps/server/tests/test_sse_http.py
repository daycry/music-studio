"""Contrato HTTP mínimo del stream SSE autenticado por sesión local."""

from contextlib import contextmanager
from pathlib import Path

from app import models
from app.event_dtos import SessionCredentialDTO
from app.main import create_app
from app.queue.events import EventBus
from app.settings import ContractSettings
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

ORIGIN = "http://127.0.0.1:3000"
BOOT = {"Origin": ORIGIN, "X-Studio-Session-Bootstrap": "1"}
UNIT = Path.cwd() / ".cache/dev-cycle/m1/t06-session-http"


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
        with client.stream(
            "GET",
            "/api/events",
            headers={
                "Origin": ORIGIN,
                "Accept": "text/event-stream",
                "X-Studio-Session-Token": token,
            },
        ) as response:
            assert response.status_code == 200, response.text
            assert response.headers["content-type"].startswith("text/event-stream")
            body = next(response.iter_bytes())
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
        with client.stream(
            "GET",
            "/api/events",
            headers={
                "Origin": ORIGIN,
                "Accept": "text/event-stream",
                "X-Studio-Session-Token": token,
                "Last-Event-ID": f"{bus.epoch}:1",
            },
        ) as response:
            assert response.status_code == 200, response.text
            body = next(response.iter_bytes())
            assert b"event: job.progress" in body
            assert b'"fraction":0.5' in body
