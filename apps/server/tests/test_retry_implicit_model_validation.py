"""API/SQLite reales: el modelo original se conserva al reintentar."""

import asyncio
from copy import deepcopy

import pytest
from app import models
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_domain_routes import headers, issue
from test_generation_language_optional import application


@pytest.mark.parametrize("explicit", [False, True], ids=["implicit", "explicit"])
@pytest.mark.parametrize("task", ["music.instrumental", "music.song"])
def test_retry_keeps_selected_model_and_original_take(tmp_path, explicit, task):
    with TestClient(application(tmp_path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        payload = {"task": task, "seed": 17, "params": {"duration_s": 2}}
        if explicit:
            payload["model_id"] = "mock"
        if task == "music.song":
            payload.update(lyrics="[Verse]\nHola", lyrics_declaration="own")
        created = client.post("/api/generations", headers=headers(token), json=payload)
        assert created.status_code == 202, created.text
        jid, tid = created.json()["generation_job_id"], created.json()["take_ids"][0]
        with Session(client.app.state.db) as session, session.begin():
            job, take = session.get(models.Job, jid), session.get(models.Take, tid)
            before = deepcopy(job.request)
            identity = (
                take.model_id,
                take.model_version,
                take.seed,
                take.params,
                take.root_id,
                take.derivation,
                take.lyrics_version_id,
            )
            job.status = take.status = "failed"
            job.error_code = take.error_code = "INTERNAL"
        retried = client.post(f"/api/jobs/{jid}/retry", headers=headers(token))
        assert retried.status_code == 202, retried.text
        assert retried.json()["take_ids"] == [tid]
        with Session(client.app.state.db) as session:
            old = session.get(models.Job, jid)
            new = session.get(models.Job, retried.json()["generation_job_id"])
            take = session.get(models.Take, tid)
            assert old.request == new.request == before
            assert old.model_id == new.model_id == take.model_id == "mock"
            assert old.engine_id == new.engine_id == "mock"
            assert (
                take.model_id,
                take.model_version,
                take.seed,
                take.params,
                take.root_id,
                take.derivation,
                take.lyrics_version_id,
            ) == identity
            assert take.job_id == new.id and take.status == "queued"
            for child_id in [
                created.json()["post_job_id"],
                *created.json()["beat_job_ids"],
            ]:
                assert session.get(models.Job, child_id).model_id is None
            if task == "music.song":
                lyrics = session.get(models.LyricsVersion, take.lyrics_version_id)
                assert (
                    lyrics.declaration == "own"
                    and lyrics.text == before["params"]["lyrics"]
                )
        repeated = client.post(f"/api/jobs/{jid}/retry", headers=headers(token))
        assert repeated.status_code == 409 and repeated.json()["code"] == "CONFLICT"


@pytest.mark.parametrize(
    "available", [True, False], ids=["new-default", "original-unavailable"]
)
def test_retry_never_switches_to_new_default(tmp_path, available):
    from app.main import create_app
    from app.queue.resolver import Resolver
    from app.queue.synthetic_registry import packaged_mock_descriptor
    from engine_contract import Health, ModelDescriptor
    from synthetic_composition import composition, declared_entries
    from test_domain_routes import QueueWithoutEngines, config

    original = packaged_mock_descriptor().model_dump(mode="json")
    alternate = deepcopy(original)
    alternate["id"] = "mock-alternate"

    class Catalog:
        origin = "http://engine-mock:8199"
        def __init__(self):
            self.recipes = [original]

        async def health(self):
            return Health(
                engine_id="mock",
                engine_version="1",
                image_digest="unknown",
                state="idle",
                gpu={"total_mb": 0, "free_mb": 0, "cap_mb": 0},
            )

        async def models(self):
            return [ModelDescriptor.model_validate(recipe) for recipe in self.recipes]

    catalog = Catalog()
    catalog.trusted_entries = declared_entries(catalog, [original, alternate])

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(
                engine,
                settings,
                Resolver(
                    {"mock": catalog},
                    data_dir=settings.data_dir,
                    synthetic_registry=composition({"mock": catalog}),
                ),
            )

    with TestClient(
        create_app(config(tmp_path), queue_runtime_factory=Queue),
        base_url="http://127.0.0.1:8000",
    ) as client:
        token = issue(client)
        created = client.post(
            "/api/generations",
            headers=headers(token),
            json={"task": "music.instrumental", "seed": 19},
        )
        assert created.status_code == 202, created.text
        jid, tid = created.json()["generation_job_id"], created.json()["take_ids"][0]
        with Session(client.app.state.db) as session, session.begin():
            job, take = session.get(models.Job, jid), session.get(models.Take, tid)
            job.status = take.status = "failed"
            original_request = deepcopy(job.request)
        # Una nueva preferencia real del cat?logo, acreditada antes de observaci?n.
        catalog.recipes = [alternate, original] if available else [alternate]
        resolver = client.app.state.queue.resolver
        resolver.invalidate(catalog.origin)
        retried = client.post(f"/api/jobs/{jid}/retry", headers=headers(token))
        if not available:
            assert retried.status_code == 409, retried.text
            with Session(client.app.state.db) as session:
                assert session.get(models.Take, tid).job_id == jid
                assert session.get(models.Job, jid).request == original_request
            return
        assert retried.status_code == 202, retried.text
        with Session(client.app.state.db) as session:
            replacement = session.get(models.Job, retried.json()["generation_job_id"])
            assert replacement.model_id == "mock" and replacement.engine_id == "mock"
            assert replacement.request == original_request
            resolved = asyncio.run(
                resolver.resolve(replacement, engine=client.app.state.db)
            )
            assert resolved.model_id == "mock"
            # Primera admisi?n real: identidad l?gica y petici?n durable concordantes.
            from app.queue.admission import Admission

            admission = Admission(
                client.app.state.db,
                replacement.owner_id,
                synthetic_registry=resolver.synthetic_registry,
            )
            claim = admission.reserve(resolved)
            assert claim is not None
        with Session(client.app.state.db) as session:
            attempt = session.get(models.JobAttempt, claim.attempt_id)
            assert attempt.model_id == attempt.engine_request.model_id == "mock"
            assert attempt.engine_id == "mock"
            assert attempt.engine_request.seed == 19
            assert attempt.engine_request.params == original_request["params"]
            assert session.get(models.Job, jid).request == original_request


@pytest.mark.parametrize(
    "conflict", ["legacy-null", "take-model", "take-seed", "take-params"]
)
def test_retry_capture_conflicts_fail_closed_without_rewriting_original(
    tmp_path, conflict
):
    with TestClient(application(tmp_path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        created = client.post(
            "/api/generations",
            headers=headers(token),
            json={"task": "music.instrumental", "seed": 17},
        )
        assert created.status_code == 202, created.text
        jid, tid = created.json()["generation_job_id"], created.json()["take_ids"][0]
        with Session(client.app.state.db) as session, session.begin():
            job, take = session.get(models.Job, jid), session.get(models.Take, tid)
            job.status = take.status = "failed"
            if conflict == "legacy-null":
                job.model_id = None
            elif conflict == "take-model":
                take.model_id = "different"
            elif conflict == "take-seed":
                take.seed = 18
            else:
                take.params = {"style": "changed"}
            before_job = deepcopy(
                {c.name: getattr(job, c.name) for c in models.Job.__table__.columns}
            )
            before_take = deepcopy(
                {c.name: getattr(take, c.name) for c in models.Take.__table__.columns}
            )
        # updated_at refleja el commit del escenario antes de medir no-escritura.
        with Session(client.app.state.db) as session:
            before_job = deepcopy(
                {
                    c.name: getattr(session.get(models.Job, jid), c.name)
                    for c in models.Job.__table__.columns
                }
            )
            before_take = deepcopy(
                {
                    c.name: getattr(session.get(models.Take, tid), c.name)
                    for c in models.Take.__table__.columns
                }
            )
        retried = client.post(f"/api/jobs/{jid}/retry", headers=headers(token))
        assert retried.status_code == 409, retried.text
        assert retried.json()["code"] == "CONFLICT"
        with Session(client.app.state.db) as session:
            assert {
                c.name: getattr(session.get(models.Job, jid), c.name)
                for c in models.Job.__table__.columns
            } == before_job
            assert {
                c.name: getattr(session.get(models.Take, tid), c.name)
                for c in models.Take.__table__.columns
            } == before_take
            assert session.query(models.Job).count() == 3
