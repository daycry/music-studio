"""Idioma opcional en la API, validado por el resolver real del mock."""

import json

import pytest
from app import models
from app.main import create_app
from app.queue.resolver import Resolver
from app.queue.synthetic_registry import packaged_mock_descriptor
from engine_contract import Health, ModelDescriptor
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from synthetic_composition import composition, declared_entries
from test_domain_routes import QueueWithoutEngines, config, headers, issue


def application(tmp_path, *, required=False):
    recipe = packaged_mock_descriptor().model_dump(mode="json")
    if required:
        recipe["tasks"]["music.song"]["params_schema"]["required"] = ["language"]

    class Catalog:
        origin = "http://engine-mock:8199"

        async def health(self):
            return Health(
                engine_id="mock",
                engine_version="1",
                image_digest="unknown",
                state="idle",
                gpu={"total_mb": 0, "free_mb": 0, "cap_mb": 0},
            )

        async def models(self):
            return [ModelDescriptor.model_validate(recipe)]

    backend = Catalog()
    backend.trusted_entries = declared_entries(backend, [recipe])

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(
                engine,
                settings,
                Resolver(
                    {"mock": backend},
                    data_dir=settings.data_dir,
                    synthetic_registry=composition({"mock": backend}),
                ),
            )

    return create_app(config(tmp_path), queue_runtime_factory=Queue)


@pytest.mark.parametrize("language", [{}, {"language": None}], ids=["omitted", "null"])
def test_generation_accepts_optional_language(tmp_path, language):
    with TestClient(application(tmp_path), base_url="http://127.0.0.1:8000") as client:
        response = client.post(
            "/api/generations",
            headers=headers(issue(client)),
            json={
                "task": "music.song",
                "lyrics": "[Verse]\nHola",
                "lyrics_declaration": "own",
                **language,
            },
        )
        assert response.status_code == 202, response.text
        assert_generation(client, response, None)


@pytest.mark.parametrize(
    "language,expected,required",
    [
        ({"language": "es"}, "es", False),
        ({"params": {"language": "fr"}}, "fr", False),
        ({"language": None, "params": {"language": "fr"}}, "fr", False),
        ({"language": "es", "params": {"language": "fr"}}, "es", False),
        ({"language": "es"}, "es", True),
    ],
)
def test_generation_preserves_explicit_language(tmp_path, language, expected, required):
    with TestClient(
        application(tmp_path, required=required), base_url="http://127.0.0.1:8000"
    ) as client:
        response = client.post(
            "/api/generations",
            headers=headers(issue(client)),
            json={
                "task": "music.song",
                "lyrics": "[Verse]\nHola",
                "lyrics_declaration": "own",
                **language,
            },
        )
        assert response.status_code == 202, response.text
        assert_generation(client, response, expected)


def assert_generation(client, response, language):
    with Session(client.app.state.db) as session:
        job = session.get(models.Job, response.json()["generation_job_id"])
        params = job.request["params"]
        if language is None:
            assert "language" not in params
        else:
            assert params["language"] == language
        take = session.get(models.Take, response.json()["take_ids"][0])
        lyrics = session.get(models.LyricsVersion, take.lyrics_version_id)
        assert lyrics.declaration == "own"
        assert lyrics.text == params["lyrics"] == "[Verse]\nHola"
        assert lyrics.owner_id == job.owner_id == take.owner_id
        assert lyrics.song_id == job.song_id == take.song_id
        # Comprobar la petición efectiva que el resolver entrega al engine.
        import asyncio

        resolved = asyncio.run(
            client.app.state.queue.resolver.resolve(
                job,
                engine=client.app.state.db,
            )
        )
        assert json.loads(resolved.payload)["params"] == params


@pytest.mark.parametrize(
    "required,declaration,language",
    [
        (True, "own", {}),
        (True, "own", {"language": None}),
        (False, None, {}),
        (False, None, {"language": "es"}),
    ],
)
def test_generation_retains_required_language_and_authorship_gates(
    tmp_path,
    required,
    declaration,
    language,
):
    with TestClient(
        application(tmp_path, required=required), base_url="http://127.0.0.1:8000"
    ) as client:
        response = client.post(
            "/api/generations",
            headers=headers(issue(client)),
            json={
                "task": "music.song",
                "lyrics": "[Verse]\nHola",
                **({"lyrics_declaration": declaration} if declaration else {}),
                **language,
            },
        )
        assert response.status_code == 422
        assert response.json()["code"] == (
            "INVALID_PARAMS" if declaration else "LYRICS_DECLARATION_REQUIRED"
        )
