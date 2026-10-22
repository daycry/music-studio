"""API M1 de canciones y entrada de generaciones."""

import json
from contextlib import contextmanager
from types import SimpleNamespace

from app import models
from app.event_dtos import SessionCredentialDTO
from app.main import create_app
from app.queue.events import EventBus
from app.queue.inputs import ResolutionError
from app.settings import ContractSettings
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

ORIGIN = "http://127.0.0.1:3000"
BOOT = {"Origin": ORIGIN, "X-Studio-Session-Bootstrap": "1"}


class QueueWithoutEngines:
    def __init__(self, engine, settings, resolver=None):
        self.bus = EventBus()
        self.resolver = resolver

    async def start(self):
        pass

    async def close(self):
        self.bus.shutdown()


def config(tmp_path):
    return ContractSettings(engine_token="internal-engine-private", data_dir=tmp_path)


@contextmanager
def connection(tmp_path):
    app = create_app(config(tmp_path), queue_runtime_factory=QueueWithoutEngines)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        yield client


def issue(client):
    response = client.post("/api/session/bootstrap", headers=BOOT)
    assert response.status_code == 200, response.text
    return SessionCredentialDTO.model_validate(response.json()).session_token


def headers(token):
    return {"Origin": ORIGIN, "X-Studio-Session-Token": token}


def ready_take(client, token, tmp_path):
    response = client.post("/api/songs", headers=headers(token), json={"title": "Take"})
    song_id = response.json()["id"]
    engine = client.app.state.db
    with Session(engine) as session, session.begin():
        owner_id = client.app.state.session_owner_id
        job = models.Job(
            owner_id=owner_id,
            song_id=song_id,
            task="music.instrumental",
            lane="gpu",
            request={
                "task": "music.instrumental",
                "params": {},
                "seed": 17,
                "n_outputs": 1,
            },
            status="queued",
        )
        session.add(job)
        session.flush()
        take_id = models.new_id()
        take = models.Take(
            id=take_id,
            owner_id=owner_id,
            song_id=song_id,
            job_id=job.id,
            status="ready",
            batch_id=job.id,
            variant_index=0,
            root_id=take_id,
            derivation="original",
            task="music.instrumental",
            model_id="mock",
            model_version="1.0",
            seed=17,
            params={},
            duration_s=1.0,
            sample_rate=48000,
            commercial_use=True,
        )
        session.add(take)
        session.flush()
        root = tmp_path / "songs" / song_id / "takes" / take.id
        root.mkdir(parents=True)
        audio = root / "listen.mp3"
        audio.write_bytes(b"0123456789")
        master = root / "master.flac"
        master.write_bytes(b"master-flac")
        peaks = root / "peaks.json"
        peaks.write_text(json.dumps({"data": [[[0, 1]]]}), encoding="utf-8")
        for role, name, media in (
            ("listen", "listen.mp3", "audio/mpeg"),
            ("master", "master.flac", "audio/flac"),
            ("peaks", "peaks.json", "application/json"),
        ):
            payload = (root / name).read_bytes()
            session.add(
                models.Asset(
                    owner_id=owner_id,
                    subject_type="take",
                    subject_id=take.id,
                    role=role,
                    path=f"songs/{song_id}/takes/{take.id}/{name}",
                    media_type=media,
                    sha256=__import__("hashlib").sha256(payload).hexdigest(),
                    bytes=len(payload),
                    meta={},
                )
            )
        job_id = job.id
    return song_id, take_id, job_id


def test_song_and_lyrics_belong_to_local_session(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        response = client.post(
            "/api/songs",
            headers=headers(token),
            json={"title": "Libre", "style_prompt": "hip hop luminoso"},
        )
        assert response.status_code == 201, response.text
        song = response.json()
        assert song["title"] == "Libre"
        song_id = song["id"]

        lyrics = client.post(
            f"/api/songs/{song_id}/lyrics",
            headers=headers(token),
            json={
                "text": "[Verse]\nCamino\n[Chorus]\nLibre",
                "declaration": "own",
            },
        )
        assert lyrics.status_code == 201, lyrics.text
        assert lyrics.json()["song_id"] == song_id
        listed = client.get("/api/songs", headers=headers(token))
        assert listed.status_code == 200
        assert listed.json()["items"][0]["id"] == song_id


def test_song_takes_list_is_owner_scoped(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_id, _job_id = ready_take(client, token, tmp_path)
        response = client.get(f"/api/songs/{song_id}/takes", headers=headers(token))
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["id"] == take_id


def test_generation_with_lyrics_requires_declaration(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={"task": "music.song", "lyrics": "[Verse]\nHola"},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "LYRICS_DECLARATION_REQUIRED"


def test_generation_does_not_accept_lyrics_for_instrumental(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={
                "task": "music.instrumental",
                "lyrics": "[Verse]\nNo se usa",
            },
        )
        assert response.status_code == 422


def test_generation_forwards_style_and_defaults_seed(tmp_path):
    class Resolver:
        async def resolve(self, job, engine=None):
            return SimpleNamespace(
                lane="gpu", backend=self, model_id="mock", engine_id="mock"
            )

        async def _catalog(self, _backend):
            return SimpleNamespace(engine_id="mock", engine_version="1"), [
                SimpleNamespace(id="mock", version="1.0", commercial_use=True)
            ]

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, Resolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={
                "task": "music.song",
                "lyrics": "[Verse]\nHola",
                "lyrics_declaration": "own",
                "style_prompt": "hip hop luminoso",
            },
        )
        assert response.status_code == 202, response.text
        with Session(client.app.state.db) as session:
            job = session.get(models.Job, response.json()["generation_job_id"])
            assert job.request["params"]["style"] == "hip hop luminoso"
            assert job.request["seed"] == 0


def test_generation_estimate_receives_song_lyrics_and_language(tmp_path):
    captured = {}

    class Backend:
        async def estimate(self, request):
            captured["request"] = request
            return SimpleNamespace(model_dump=lambda mode="json": {"eta_s": 12})

    class Resolver:
        def __init__(self):
            self.backends = {"mock": Backend()}

        async def _catalog(self, _backend):
            return SimpleNamespace(engine_id="mock", engine_version="1"), [
                SimpleNamespace(id="ace-step-1.5-turbo")
            ]

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, Resolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post(
            "/api/generations/estimate",
            headers=headers(token),
            json={
                "task": "music.song",
                "model_id": "ace-step-1.5-turbo",
                "params": {
                    "style": "hip hop luminoso",
                    "lyrics": "[Verse]\nHola",
                    "language": "es",
                    "duration_s": 180,
                },
            },
        )
        assert response.status_code == 200, response.text
        assert captured["request"].params["lyrics"] == "[Verse]\nHola"
        assert captured["request"].params["language"] == "es"


def test_generation_rejects_invalid_lyrics_tags_before_queue(tmp_path):
    class Resolver:
        async def resolve(self, job, engine=None):
            raise AssertionError("invalid lyrics must not reach resolver")

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, Resolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={
                "task": "music.song",
                "lyrics": "[chrous]\nHola",
                "lyrics_declaration": "own",
                "style_prompt": "hip hop",
            },
        )
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_PARAMS"


def test_generation_creates_song_chain_after_authority_checks(tmp_path):
    class Resolver:
        async def resolve(self, job, *, engine=None):
            return SimpleNamespace(
                lane="gpu", model_id="mock", backend=object(), engine_id="mock"
            )

        async def _catalog(self, backend):
            return None, [
                SimpleNamespace(id="mock", version="1.0", commercial_use=True)
            ]

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, Resolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={
                "task": "music.song",
                "lyrics": "[Verse]\nHola",
                "lyrics_declaration": "own",
                "seed": 17,
                "n_outputs": 2,
            },
        )
        assert response.status_code == 202, response.text
        body = response.json()
        assert len(body["take_ids"]) == 2
        with Session(client.app.state.db) as session:
            generation = session.get(models.Job, body["generation_job_id"])
            post = session.get(models.Job, body["post_job_id"])
            assert (generation.task, generation.lane, generation.status) == (
                "music.song",
                "gpu",
                "queued",
            )
            assert (post.task, post.lane, post.status) == (
                "post.audio",
                "cpu",
                "blocked",
            )


def test_generation_resolution_failure_does_not_leave_draft_or_lyrics(tmp_path):
    class Resolver:
        async def resolve(self, job, *, engine=None):
            raise ResolutionError("no compatible engine")

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, Resolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={
                "task": "music.song",
                "lyrics": "[Verse]\nNo debe quedar",
                "lyrics_declaration": "own",
                "style_prompt": "hip hop",
            },
        )
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_PARAMS"
        with Session(client.app.state.db) as session:
            owner = client.app.state.session_owner_id
            assert session.query(models.Song).filter_by(owner_id=owner).count() == 0
            assert (
                session.query(models.LyricsVersion).filter_by(owner_id=owner).count()
                == 0
            )


def test_take_detail_patch_audio_range_peaks_and_master(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_id, _ = ready_take(client, token, tmp_path)
        detail = client.get(f"/api/takes/{take_id}", headers=headers(token))
        assert detail.status_code == 200, detail.text
        assert detail.json()["status"] == "ready"
        patched = client.patch(
            f"/api/takes/{take_id}",
            headers=headers(token),
            json={"favorite": True, "rating": 5, "label": "mejor"},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["favorite"] is True
        audio = client.get(
            f"/api/takes/{take_id}/audio",
            headers={**headers(token), "Range": "bytes=2-5"},
        )
        assert audio.status_code == 206
        assert audio.content == b"2345"
        assert audio.headers["content-range"] == "bytes 2-5/10"
        master_audio = client.get(
            f"/api/takes/{take_id}/master", headers=headers(token)
        )
        assert master_audio.status_code == 200
        assert master_audio.content == b"master-flac"
        assert master_audio.headers["content-type"] == "audio/flac"
        assert master_audio.headers["content-disposition"].endswith('.flac"')
        peaks = client.get(f"/api/takes/{take_id}/peaks", headers=headers(token))
        assert peaks.status_code == 200
        assert peaks.json()["data"] == [[[0, 1]]]
        master = client.post(
            f"/api/songs/{song_id}/master",
            headers=headers(token),
            json={"take_id": take_id},
        )
        assert master.status_code == 200, master.text
        assert master.json()["master_take_id"] == take_id


def test_job_cancel_is_owner_bound_and_durable(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        _, _, job_id = ready_take(client, token, tmp_path)
        response = client.post(f"/api/jobs/{job_id}/cancel", headers=headers(token))
        assert response.status_code == 202, response.text
        with Session(client.app.state.db) as session:
            assert session.get(models.Job, job_id).cancel_requested_at is not None


def test_models_estimate_unload_and_system_use_local_backend(tmp_path):
    class Backend:
        origin = "http://engine-mock:8199"

        async def estimate(self, request):
            assert request.model_id == "mock"
            return SimpleNamespace(
                model_dump=lambda mode=None: {
                    "eta_s": 3.0,
                    "vram_mb": 512.0,
                    "cost_eur": None,
                }
            )

        async def unload(self):
            return SimpleNamespace(freed_mb=128.0)

        async def health(self):
            return SimpleNamespace(
                model_dump=lambda mode=None: {"state": "idle", "engine_id": "mock"}
            )

    class Resolver:
        def __init__(self):
            self.backends = {"mock": Backend()}

        async def _catalog(self, backend):
            return SimpleNamespace(engine_id="mock", engine_version="1"), [
                SimpleNamespace(
                    id="mock",
                    model_dump=lambda mode=None: {
                        "id": "mock",
                        "family": "mock",
                        "version": "1",
                        "commercial_use": True,
                        "tasks": {
                            "music.song": {
                                "verified": True,
                                "params_schema": {"properties": {"duration_s": {}}},
                                "features": {"bpm": {"verified": False}},
                            }
                        },
                    },
                )
            ]

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, Resolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        model = client.get("/api/models", headers=headers(token))
        assert model.status_code == 200, model.text
        assert model.json()["items"][0]["id"] == "mock"
        estimate = client.post(
            "/api/generations/estimate",
            headers=headers(token),
            json={"task": "music.instrumental", "model_id": "mock"},
        )
        assert estimate.status_code == 200, estimate.text
        assert estimate.json()["eta_s"] == 3.0
        unload = client.post("/api/system/unload", headers=headers(token))
        assert unload.status_code == 200, unload.text
        assert unload.json()["freed_mb"] == 128.0
        system = client.get("/api/system", headers=headers(token))
        assert system.status_code == 200, system.text
        assert system.json()["engines"][0]["state"] == "idle"
        assert system.json()["models"][0]["id"] == "mock"
        assert (
            "duration_s"
            in system.json()["models"][0]["tasks"]["music.song"]["params_schema"][
                "properties"
            ]
        )
        assert system.json()["models"][0]["tasks"]["music.song"]["features"]
        assert "total_bytes" in system.json()["ram"]


def test_song_cursor_search_and_collections(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        collection = client.post(
            "/api/collections",
            headers=headers(token),
            json={"name": "Cierres"},
        )
        assert collection.status_code == 201, collection.text
        collection_id = collection.json()["id"]
        first = client.post(
            "/api/songs",
            headers=headers(token),
            json={"title": "Libre", "style_prompt": "amanecer"},
        )
        second = client.post(
            "/api/songs",
            headers=headers(token),
            json={"title": "Otra", "style_prompt": "noche"},
        )
        assert first.status_code == second.status_code == 201
        song_id = first.json()["id"]
        patched = client.patch(
            f"/api/songs/{song_id}",
            headers=headers(token),
            json={"collection_id": collection_id},
        )
        assert patched.status_code == 200, patched.text
        found = client.get("/api/songs?q=amanecer", headers=headers(token))
        assert found.status_code == 200, found.text
        assert [row["id"] for row in found.json()["items"]] == [song_id]
        filtered = client.get(
            f"/api/songs?collection_id={collection_id}", headers=headers(token)
        )
        assert filtered.status_code == 200
        assert filtered.json()["items"][0]["collection_id"] == collection_id
        renamed = client.patch(
            f"/api/collections/{collection_id}",
            headers=headers(token),
            json={"name": "Cierres finales"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["name"] == "Cierres finales"


def test_song_library_filters_status_and_tag(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        first = client.post(
            "/api/songs",
            headers=headers(token),
            json={"title": "Luz", "tags": ["cierre", "luminoso"]},
        )
        second = client.post(
            "/api/songs",
            headers=headers(token),
            json={"title": "Borrador", "tags": ["borrador"]},
        )
        assert first.status_code == second.status_code == 201
        first_id = first.json()["id"]
        changed = client.patch(
            f"/api/songs/{first_id}", headers=headers(token), json={"status": "final"}
        )
        assert changed.status_code == 200, changed.text
        by_status = client.get("/api/songs?status=final", headers=headers(token))
        assert [row["id"] for row in by_status.json()["items"]] == [first_id]
        by_tag = client.get("/api/songs?tag=cierre", headers=headers(token))
        assert [row["id"] for row in by_tag.json()["items"]] == [first_id]
        invalid = client.get("/api/songs?status=unknown", headers=headers(token))
        assert invalid.status_code == 422


def test_song_trash_restore_and_retention_purge(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        created = client.post(
            "/api/songs",
            headers=headers(token),
            json={"title": "Papelera", "style_prompt": "amanecer"},
        )
        assert created.status_code == 201, created.text
        song_id = created.json()["id"]

        deleted = client.delete(f"/api/songs/{song_id}", headers=headers(token))
        assert deleted.status_code == 204, deleted.text
        assert (
            client.get(f"/api/songs/{song_id}", headers=headers(token)).status_code
            == 403
        )
        assert (
            client.get("/api/songs?q=amanecer", headers=headers(token)).json()["items"]
            == []
        )

        trash = client.get("/api/songs/trash", headers=headers(token))
        assert trash.status_code == 200, trash.text
        item = next(row for row in trash.json()["items"] if row["id"] == song_id)
        assert item["deleted_at"]
        assert item["purge_after"]

        too_soon = client.post(f"/api/songs/{song_id}/purge", headers=headers(token))
        assert too_soon.status_code == 409
        assert too_soon.json()["code"] == "PURGE_RETENTION"

        restored = client.post(f"/api/songs/{song_id}/restore", headers=headers(token))
        assert restored.status_code == 200, restored.text
        assert restored.json()["id"] == song_id
        assert (
            client.get("/api/songs/trash", headers=headers(token)).json()["items"] == []
        )
        assert [
            row["id"]
            for row in client.get(
                "/api/songs?q=amanecer", headers=headers(token)
            ).json()["items"]
        ] == [song_id]

        client.delete(f"/api/songs/{song_id}", headers=headers(token))
        with Session(client.app.state.db) as session, session.begin():
            song = session.get(models.Song, song_id)
            song.deleted_at = "2026-08-01T00:00:00.000000Z"

        purged = client.post(f"/api/songs/{song_id}/purge", headers=headers(token))
        assert purged.status_code == 204, purged.text
        assert (
            client.get("/api/songs/trash", headers=headers(token)).json()["items"] == []
        )


def test_song_restore_keeps_existing_takes(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_id, _ = ready_take(client, token, tmp_path)
        assert (
            client.delete(f"/api/songs/{song_id}", headers=headers(token)).status_code
            == 204
        )
        restored = client.post(f"/api/songs/{song_id}/restore", headers=headers(token))
        assert restored.status_code == 200, restored.text
        takes = client.get(f"/api/songs/{song_id}/takes", headers=headers(token))
        assert takes.status_code == 200
        assert [take["id"] for take in takes.json()["items"]] == [take_id]


def test_song_purge_preserves_durable_history(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, _take_id, _job_id = ready_take(client, token, tmp_path)
        assert (
            client.delete(f"/api/songs/{song_id}", headers=headers(token)).status_code
            == 204
        )
        with Session(client.app.state.db) as session, session.begin():
            song = session.get(models.Song, song_id)
            song.deleted_at = "2026-08-01T00:00:00.000000Z"
        purged = client.post(f"/api/songs/{song_id}/purge", headers=headers(token))
        assert purged.status_code == 409
        assert purged.json()["code"] == "PURGE_PROTECTED"


def test_openapi_audio_and_take_shapes(tmp_path):
    with connection(tmp_path) as client:
        spec = client.get("/openapi.json").json()
        take = spec["paths"]["/api/songs/{song_id}/takes"]["get"]["responses"]["200"]
        assert take["content"]["application/json"]["schema"]["type"] == "object"
        assert (
            take["content"]["application/json"]["schema"]["properties"]["items"][
                "items"
            ]["type"]
            == "object"
        )
        restore_song = spec["paths"]["/api/songs/{song_id}/restore"]["post"][
            "responses"
        ]["200"]
        assert (
            restore_song["content"]["application/json"]["schema"]["properties"]["id"][
                "type"
            ]
            == "string"
        )
        restore_take = spec["paths"]["/api/takes/{take_id}/restore"]["post"][
            "responses"
        ]["200"]
        assert (
            restore_take["content"]["application/json"]["schema"]["properties"]["id"][
                "type"
            ]
            == "string"
        )
        collections = spec["paths"]["/api/collections"]["get"]["responses"]["200"]
        assert (
            collections["content"]["application/json"]["schema"]["properties"]["items"][
                "items"
            ]["properties"]["name"]["type"]
            == "string"
        )
        audio = spec["paths"]["/api/takes/{take_id}/master"]["get"]["responses"]["200"]
        assert set(audio["content"]) == {"audio/flac"}
        assert audio["content"]["audio/flac"]["schema"]["format"] == "binary"
        takes_list = spec["paths"]["/api/songs/{song_id}/takes"]["get"]["responses"][
            "200"
        ]
        assert set(
            takes_list["content"]["application/json"]["schema"]["properties"]
        ) == {"items"}
        song_properties = spec["paths"]["/api/songs/{song_id}"]["get"]["responses"][
            "200"
        ]["content"]["application/json"]["schema"]["properties"]
        assert {
            "negative_prompt",
            "language",
            "tags",
            "notes",
            "current_lyrics_version_id",
        } <= set(song_properties)
        take_properties = spec["paths"]["/api/takes/{take_id}"]["get"]["responses"][
            "200"
        ]["content"]["application/json"]["schema"]["properties"]
        assert {"created_at", "updated_at"} <= set(take_properties)
        assert {"role", "bytes"} <= set(
            take_properties["assets"]["additionalProperties"]["properties"]
        )
        collection_post = spec["paths"]["/api/collections"]["post"]["responses"]
        assert "201" in collection_post and "200" not in collection_post
