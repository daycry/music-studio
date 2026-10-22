"""M1/T-07: duración por defecto, descargas, URLs de assets y contrato tipado."""

import os
from types import SimpleNamespace

import pytest
from app import models
from app.domain_routes import _take_dict
from app.main import create_app
from app.queue.resolver import Resolver
from app.queue.synthetic_registry import packaged_mock_descriptor
from engine_contract import Health, ModelDescriptor
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from synthetic_composition import composition, declared_entries
from test_domain_routes import QueueWithoutEngines, config, connection, headers, issue
from test_domain_routes import ready_take as _ready_take

SONG = {
    "task": "music.song",
    "lyrics": "[Verse]\nHola",
    "lyrics_declaration": "own",
}


def mock_app(tmp_path, *, duration_limits=None):
    recipe = packaged_mock_descriptor().model_dump(mode="json")
    if duration_limits is not None:
        recipe["tasks"]["music.song"]["params_schema"]["properties"]["duration_s"] = {
            "type": "number",
            **duration_limits,
        }

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


def counts(client):
    with Session(client.app.state.db) as session:
        return tuple(
            len(session.scalars(select(model)).all())
            for model in (models.Song, models.Job, models.Take, models.LyricsVersion)
        )


# ---- CA-1 -------------------------------------------------------------------


def test_generation_without_duration_persists_30s_in_job_and_takes(tmp_path):
    with TestClient(mock_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        response = client.post(
            "/api/generations",
            headers=headers(issue(client)),
            json={**SONG, "n_outputs": 2},
        )
        assert response.status_code == 202, response.text
        body = response.json()
        with Session(client.app.state.db) as session:
            job = session.get(models.Job, body["generation_job_id"])
            assert job.request["params"]["duration_s"] == 30
            for take_id in body["take_ids"]:
                assert session.get(models.Take, take_id).params["duration_s"] == 30


def test_generation_keeps_explicit_duration(tmp_path):
    with TestClient(mock_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        response = client.post(
            "/api/generations",
            headers=headers(issue(client)),
            json={**SONG, "params": {"duration_s": 45.5}},
        )
        assert response.status_code == 202, response.text
        with Session(client.app.state.db) as session:
            job = session.get(models.Job, response.json()["generation_job_id"])
            assert job.request["params"]["duration_s"] == 45.5


@pytest.mark.parametrize("value", ["30", "abc", None, True, [30], 0, -5, 600.5, 601])
def test_generation_rejects_invalid_duration_before_creating_anything(tmp_path, value):
    with TestClient(mock_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        before = counts(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={**SONG, "params": {"duration_s": value}},
        )
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "INVALID_PARAMS"
        assert counts(client) == before


def test_generation_accepts_duration_upper_bound(tmp_path):
    with TestClient(mock_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        response = client.post(
            "/api/generations",
            headers=headers(issue(client)),
            json={**SONG, "params": {"duration_s": 600}},
        )
        assert response.status_code == 202, response.text


def test_descriptor_limits_still_apply_over_the_default(tmp_path):
    app = mock_app(tmp_path, duration_limits={"minimum": 10, "maximum": 600})
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        ok = client.post("/api/generations", headers=headers(token), json=SONG)
        assert ok.status_code == 202, ok.text
        before = counts(client)
        low = client.post(
            "/api/generations",
            headers=headers(token),
            json={**SONG, "params": {"duration_s": 5}},
        )
        assert low.status_code == 422, low.text
        assert counts(client) == before


def test_estimate_without_duration_uses_30s_and_rejects_invalid(tmp_path):
    captured = []

    class Backend:
        async def estimate(self, request):
            captured.append(request)
            return SimpleNamespace(model_dump=lambda mode="json": {"eta_s": 1})

    class FakeResolver:
        def __init__(self):
            self.backends = {"mock": Backend()}

        async def _catalog(self, _backend):
            return SimpleNamespace(engine_id="mock", engine_version="1"), [
                SimpleNamespace(id="mock")
            ]

    class Queue(QueueWithoutEngines):
        def __init__(self, engine, settings):
            super().__init__(engine, settings, FakeResolver())

    app = create_app(config(tmp_path), queue_runtime_factory=Queue)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        body = {"task": "music.song", "model_id": "mock"}
        ok = client.post("/api/generations/estimate", headers=headers(token), json=body)
        assert ok.status_code == 200, ok.text
        assert captured[-1].params["duration_s"] == 30
        bad = client.post(
            "/api/generations/estimate",
            headers=headers(token),
            json={**body, "params": {"duration_s": 0}},
        )
        assert bad.status_code == 422, bad.text
        assert bad.json()["code"] == "INVALID_PARAMS"
        assert len(captured) == 1


# ---- CA-2 -------------------------------------------------------------------


def disposition(response):
    return response.headers["content-disposition"]


def test_download_flag_serves_attachment_with_safe_filename(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_id, _ = _ready_take(client, token, tmp_path)
        client.patch(
            f"/api/songs/{song_id}",
            headers=headers(token),
            json={"title": 'Canción: "Ñandú"/..\\x?*'},
        )
        for route, ext in (("audio", "mp3"), ("master", "flac")):
            plain = client.get(f"/api/takes/{take_id}/{route}", headers=headers(token))
            assert disposition(plain).startswith("inline;")
            got = client.get(
                f"/api/takes/{take_id}/{route}?download=1", headers=headers(token)
            )
            assert got.status_code == 200
            value = disposition(got)
            assert value.startswith("attachment;"), value
            assert f'.{ext}"' in value
            filename = value.split('filename="', 1)[1].split('"', 1)[0]
            assert filename.isascii()
            assert not any(c in filename for c in '/\\:*?"<>|')
            assert ".." not in filename
            assert take_id in filename
            assert "filename*=UTF-8''" in value
            assert got.content == plain.content
        partial = client.get(
            f"/api/takes/{take_id}/audio?download=1",
            headers={**headers(token), "Range": "bytes=0-1"},
        )
        assert partial.status_code == 206
        assert disposition(partial).startswith("attachment;")
        zero = client.get(
            f"/api/takes/{take_id}/audio?download=0", headers=headers(token)
        )
        assert disposition(zero).startswith("inline;")


@pytest.mark.parametrize(
    "value",
    ["bytes=5-2", "bytes=0-1,3-4", "bytes=99-", "items=0-1", "bytes=-0", "bytes=a-b"],
)
@pytest.mark.parametrize("route", ["audio", "master"])
def test_invalid_or_multiple_range_is_416(tmp_path, route, value):
    with connection(tmp_path) as client:
        token = issue(client)
        _, take_id, _ = _ready_take(client, token, tmp_path)
        response = client.get(
            f"/api/takes/{take_id}/{route}",
            headers={**headers(token), "Range": value},
        )
        assert response.status_code == 416, response.text
        assert response.headers["content-range"].startswith("bytes */")


def test_asset_of_another_take_or_unknown_take_is_404(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_a, _ = _ready_take(client, token, tmp_path)
        with Session(client.app.state.db) as session, session.begin():
            owner_id = client.app.state.session_owner_id
            job_id = session.get(models.Take, take_a).job_id
            take_b = models.new_id()
            session.add(
                models.Take(
                    id=take_b,
                    owner_id=owner_id,
                    song_id=song_id,
                    job_id=job_id,
                    status="ready",
                    batch_id=job_id,
                    variant_index=1,
                    root_id=take_b,
                    derivation="original",
                    task="music.instrumental",
                    model_id="mock",
                    model_version="1.0",
                    seed=18,
                    params={},
                    commercial_use=True,
                )
            )
        for route in ("audio", "master", "peaks"):
            response = client.get(
                f"/api/takes/{take_b}/{route}", headers=headers(token)
            )
            assert response.status_code == 404, response.text
            assert b"0123456789" not in response.content
        ghost = client.get(f"/api/takes/{'0' * 26}/audio", headers=headers(token))
        # Un take ajeno o inexistente responde 403 FORBIDDEN_SCOPE (convención
        # vigente: no revela si el id existe para otro owner).
        assert ghost.status_code == 403
        assert ghost.json()["code"] == "FORBIDDEN_SCOPE"


def set_asset_path(client, take_id, role, path):
    # El CHECK de la BD ya rechaza estas rutas; se desactiva para probar que la
    # API también las rechaza si alguien manipula la fila.
    with client.app.state.db.connect() as conn:
        conn.exec_driver_sql("PRAGMA ignore_check_constraints=ON")
        conn.exec_driver_sql(
            "UPDATE asset SET path=? WHERE subject_id=? AND role=?",
            (path, take_id, role),
        )
        conn.commit()
        conn.exec_driver_sql("PRAGMA ignore_check_constraints=OFF")


@pytest.mark.parametrize(
    "tampered",
    [
        "../secret.mp3",
        "songs/../../secret.mp3",
        "/etc/passwd",
        "C:/Windows/win.ini",
        "songs\\x\\listen.mp3",
        "",
    ],
)
def test_tampered_asset_path_is_never_served(tmp_path, tampered):
    with connection(tmp_path / "data") as client:
        (tmp_path / "secret.mp3").write_bytes(b"0123456789")
        token = issue(client)
        _, take_id, _ = _ready_take(client, token, tmp_path / "data")
        set_asset_path(client, take_id, "listen", tampered)
        response = client.get(f"/api/takes/{take_id}/audio", headers=headers(token))
        assert response.status_code == 404, response.text
        assert response.json()["code"] == "NOT_FOUND"
        assert response.content != b"0123456789"


def test_symlinked_asset_is_never_served(tmp_path):
    with connection(tmp_path / "data") as client:
        token = issue(client)
        song_id, take_id, _ = _ready_take(client, token, tmp_path / "data")
        outside = tmp_path / "outside.mp3"
        outside.write_bytes(b"0123456789")
        listen = (
            tmp_path / "data" / "songs" / song_id / "takes" / take_id / "listen.mp3"
        )
        listen.unlink()
        try:
            os.symlink(outside, listen)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks no disponibles en este entorno")
        response = client.get(f"/api/takes/{take_id}/audio", headers=headers(token))
        assert response.status_code == 404, response.text
        assert response.content != b"0123456789"


# ---- CA-3 -------------------------------------------------------------------


def test_take_dict_only_publishes_urls_for_routed_roles():
    take = SimpleNamespace(
        **{
            key: None
            for key in [
                "song_id",
                "job_id",
                "lyrics_version_id",
                "batch_id",
                "root_id",
                "model_version",
                "seed",
                "params",
                "duration_s",
                "sample_rate",
                "rating",
                "label",
                "error_code",
                "created_at",
                "updated_at",
            ]
        },
        id="T1",
        status="ready",
        variant_index=0,
        derivation="original",
        task="music.song",
        model_id="mock",
        favorite=False,
        commercial_use=True,
    )

    def asset(role):
        return SimpleNamespace(role=role, media_type="x/y", bytes=1, sha256="a" * 64)

    result = _take_dict(
        take,
        assets=[asset(r) for r in ("listen", "master", "peaks", "manifest", "cover")],
    )
    assert set(result["assets"]) == {"listen", "master", "peaks", "manifest", "cover"}
    assert result["assets"]["manifest"]["sha256"] == "a" * 64
    assert result["assets"]["manifest"]["bytes"] == 1
    urls = {
        role: value["url"] for role, value in result["assets"].items() if "url" in value
    }
    assert urls == {
        "listen": "/api/takes/T1/audio",
        "master": "/api/takes/T1/master",
        "peaks": "/api/takes/T1/peaks",
    }


# ---- CA-4 -------------------------------------------------------------------

REFS = [
    ("/api/system", "get"),
    ("/api/models", "get"),
    ("/api/generations/estimate", "post"),
    ("/api/takes/{take_id}/peaks", "get"),
    ("/api/songs/{song_id}", "patch"),
    ("/api/takes/{take_id}", "patch"),
]


@pytest.mark.parametrize("key", REFS)
def test_openapi_declares_response_model(tmp_path, key):
    spec = create_app(config(tmp_path)).openapi()
    path, method = key
    content = spec["paths"][path][method]["responses"]["200"]["content"]
    schema = content["application/json"]["schema"]
    assert "$ref" in schema or "properties" in schema, key


def test_system_queue_is_filtered_by_owner(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        _ready_take(client, token, tmp_path)
        engine = client.app.state.db
        # Motor sin el PRAGMA foreign_keys de la app: inserta un job de otro owner.
        raw = create_engine(engine.url)
        with Session(raw) as session, session.begin():
            session.add(
                models.Job(
                    owner_id="7" + "0" * 25,
                    task="music.instrumental",
                    lane="gpu",
                    request={"params": {}},
                    status="running",
                )
            )
        raw.dispose()
        with Session(engine) as session:
            assert session.scalar(
                select(models.Job.id).where(models.Job.status == "running")
            )
        system = client.get("/api/system", headers=headers(token)).json()
        assert system["queue"] == {"queued": True, "blocked": False, "running": False}


@pytest.mark.parametrize("literal", ["Infinity", "-Infinity", "NaN"])
def test_generation_rejects_non_finite_duration(tmp_path, literal):
    with TestClient(mock_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        raw = (
            '{"task":"music.song","lyrics":"[Verse]\nHola","lyrics_declaration":"own",'
            f'"params":{{"duration_s":{literal}}}}}'
        )
        response = client.post(
            "/api/generations",
            headers={**headers(token), "Content-Type": "application/json"},
            content=raw,
        )
        assert response.status_code == 422, response.text


HUGE = int("9" * 400)


def test_huge_integer_duration_is_422_not_500(tmp_path):
    with TestClient(mock_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        raw = (
            '{"task":"music.song","lyrics":"[Verse]\nHola","lyrics_declaration":"own",'
            '"params":{"duration_s":' + "9" * 400 + "}}"
        )
        response = client.post(
            "/api/generations",
            headers={**headers(token), "Content-Type": "application/json"},
            content=raw,
        )
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "INVALID_PARAMS"
        estimate = client.post(
            "/api/generations/estimate",
            headers={**headers(token), "Content-Type": "application/json"},
            content='{"task":"music.song","model_id":"mock","params":{"duration_s":'
            + "9" * 400
            + "}}",
        )
        assert estimate.status_code == 422, estimate.text
        assert estimate.json()["code"] == "INVALID_PARAMS"
