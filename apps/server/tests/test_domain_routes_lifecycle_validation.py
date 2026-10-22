"""Validación API de ciclo de vida, biblioteca y fronteras de sesión de M1."""

import hashlib

import pytest
from app import models
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_domain_routes import connection, headers, issue, ready_take
from test_generation_language_optional import application


def create_song(client, token, title):
    response = client.post("/api/songs", headers=headers(token), json={"title": title})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def assert_problem(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["code"] == code


def test_take_trash_restore_preserves_master_assets_and_lineage(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_id, job_id = ready_take(client, token, tmp_path)
        with Session(client.app.state.db) as session, session.begin():
            owner_id = client.app.state.session_owner_id
            parent_id = models.new_id()
            session.add(
                models.Take(
                    id=parent_id,
                    owner_id=owner_id,
                    song_id=song_id,
                    job_id=job_id,
                    status="ready",
                    batch_id=job_id,
                    variant_index=1,
                    root_id=parent_id,
                    derivation="original",
                    task="music.instrumental",
                    model_id="mock",
                    model_version="1.0",
                    seed=18,
                    params={},
                    commercial_use=True,
                )
            )
            session.flush()
            take = session.get(models.Take, take_id)
            take.root_id = parent_id
            take.derivation = "variant"
            edge = models.LineageEdge(
                owner_id=owner_id,
                child_type="take",
                child_id=take_id,
                parent_type="take",
                parent_id=parent_id,
                role="source",
            )
            session.add(edge)
            session.flush()
            edge_id = edge.id
        master = client.post(
            f"/api/songs/{song_id}/master",
            headers=headers(token),
            json={"take_id": take_id},
        )
        assert master.status_code == 200, master.text
        before = client.get(f"/api/takes/{take_id}", headers=headers(token)).json()
        assert before["lineage"] == [
            {
                "parent_type": "take",
                "parent_id": parent_id,
                "role": "source",
                "section_map": None,
            }
        ]
        assert (
            client.delete(f"/api/takes/{take_id}", headers=headers(token)).status_code
            == 204
        )
        assert_problem(
            client.get(f"/api/takes/{take_id}", headers=headers(token)),
            403,
            "FORBIDDEN_SCOPE",
        )
        assert take_id not in {
            row["id"]
            for row in client.get(
                f"/api/songs/{song_id}/takes", headers=headers(token)
            ).json()["items"]
        }
        with Session(client.app.state.db) as session:
            assert session.get(models.Take, take_id).deleted_at is not None
            assert session.get(models.Song, song_id).master_take_id == take_id
            assert session.get(models.LineageEdge, edge_id).deleted_at is None
        restored = client.post(f"/api/takes/{take_id}/restore", headers=headers(token))
        assert restored.status_code == 200, restored.text
        assert restored.json()["status"] == "ready"
        after = client.get(f"/api/takes/{take_id}", headers=headers(token)).json()
        for key in ("id", "job_id", "root_id", "derivation", "lineage", "assets"):
            assert after[key] == before[key]
        assert (
            client.get(f"/api/takes/{take_id}/audio", headers=headers(token)).content
            == b"0123456789"
        )
        # La segunda restauración es idempotente: no crea otro take.
        assert (
            client.post(f"/api/takes/{take_id}/restore", headers=headers(token)).json()[
                "id"
            ]
            == take_id
        )
        with Session(client.app.state.db) as session:
            assert session.query(models.Take).filter_by(song_id=song_id).count() == 2


@pytest.mark.parametrize(
    "status,error_code", [("failed", "INTERNAL"), ("cancelled", "CANCELLED")]
)
def test_take_restore_retains_terminal_error(tmp_path, status, error_code):
    with connection(tmp_path) as client:
        token = issue(client)
        _, take_id, _ = ready_take(client, token, tmp_path)
        with Session(client.app.state.db) as session, session.begin():
            take = session.get(models.Take, take_id)
            take.status = status
            take.error_code = error_code
        assert (
            client.delete(f"/api/takes/{take_id}", headers=headers(token)).status_code
            == 204
        )
        restored = client.post(f"/api/takes/{take_id}/restore", headers=headers(token))
        assert restored.status_code == 200, restored.text
        assert restored.json()["status"] == status
        with Session(client.app.state.db) as session:
            assert session.get(models.Take, take_id).error_code == error_code
            assert session.get(models.Take, take_id).deleted_at is None


def test_take_mutations_reject_ids_and_credentials_from_another_studio(tmp_path):
    with (
        connection(tmp_path / "own") as client,
        connection(tmp_path / "other") as other,
    ):
        token, other_token = issue(client), issue(other)
        _, take_id, _ = ready_take(client, token, tmp_path / "own")
        _, other_id, _ = ready_take(other, other_token, tmp_path / "other")
        for method, suffix in (("DELETE", ""), ("POST", "/restore")):
            assert_problem(
                client.request(
                    method, f"/api/takes/{other_id}{suffix}", headers=headers(token)
                ),
                403,
                "FORBIDDEN_SCOPE",
            )
            assert_problem(
                client.request(
                    method,
                    f"/api/takes/{take_id}{suffix}",
                    headers=headers(other_token),
                ),
                401,
                "SESSION_REQUIRED",
            )
        assert (
            other.get(f"/api/takes/{other_id}", headers=headers(other_token)).json()[
                "status"
            ]
            == "ready"
        )
        assert (
            client.get(f"/api/takes/{take_id}", headers=headers(token)).json()["status"]
            == "ready"
        )


def test_lyrics_history_preserves_versions_and_declarations(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id = create_song(client, token, "Versiones")
        versions = []
        for text, declaration in (
            ("[Verse]\nPrimera", "own"),
            ("[Verse]\nSegunda", "licensed"),
        ):
            response = client.post(
                f"/api/songs/{song_id}/lyrics",
                headers=headers(token),
                json={"text": text, "declaration": declaration},
            )
            assert response.status_code == 201, response.text
            versions.append(response.json())
        response = client.get(f"/api/songs/{song_id}/lyrics", headers=headers(token))
        assert response.status_code == 200, response.text
        assert [row["id"] for row in response.json()["items"]] == [
            row["id"] for row in reversed(versions)
        ]
        for actual, original in zip(
            response.json()["items"], reversed(versions), strict=True
        ):
            assert actual == original
            assert (
                actual["sha256"] == hashlib.sha256(actual["text"].encode()).hexdigest()
            )
        assert (
            client.get(f"/api/songs/{song_id}", headers=headers(token)).json()[
                "current_lyrics_version_id"
            ]
            == versions[-1]["id"]
        )
        assert_problem(
            client.get(f"/api/songs/{models.new_id()}/lyrics", headers=headers(token)),
            403,
            "FORBIDDEN_SCOPE",
        )


def test_collection_listing_excludes_trash_and_keeps_contract(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        visible = client.post(
            "/api/collections", headers=headers(token), json={"name": "Conservar"}
        ).json()
        deleted = client.post(
            "/api/collections", headers=headers(token), json={"name": "Oculta"}
        ).json()
        with Session(client.app.state.db) as session, session.begin():
            session.get(models.Collection, deleted["id"]).deleted_at = models.utc_now()
        response = client.get("/api/collections", headers=headers(token))
        assert response.status_code == 200, response.text
        assert response.json() == {"items": [visible]}
        assert_problem(
            client.patch(
                f"/api/collections/{visible['id']}", headers=headers(token), json={}
            ),
            422,
            "INVALID_PARAMS",
        )
        assert_problem(
            client.patch(
                f"/api/collections/{deleted['id']}",
                headers=headers(token),
                json={"name": "Intrusión"},
            ),
            403,
            "FORBIDDEN_SCOPE",
        )
        assert_problem(
            client.post(
                "/api/songs",
                headers=headers(token),
                json={"title": "Inválida", "collection_id": deleted["id"]},
            ),
            403,
            "FORBIDDEN_SCOPE",
        )


def test_analysis_listing_preserves_analyzer_and_hides_deleted_results(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        _, take_id, _ = ready_take(client, token, tmp_path)
        with Session(client.app.state.db) as session, session.begin():
            visible = models.Analysis(
                owner_id=client.app.state.session_owner_id,
                take_id=take_id,
                kind="key",
                analyzer_id="synthetic-key",
                analyzer_version="1",
                data={"key": "C", "confidence": 0.7},
            )
            session.add(visible)
            session.add(
                models.Analysis(
                    owner_id=client.app.state.session_owner_id,
                    take_id=take_id,
                    kind="beats",
                    analyzer_id="synthetic-beats",
                    analyzer_version="2",
                    data={"beats": [0.0]},
                    deleted_at=models.utc_now(),
                )
            )
            session.flush()
            identifier = visible.id
        response = client.get(f"/api/takes/{take_id}/analysis", headers=headers(token))
        assert response.status_code == 200, response.text
        assert response.json() == {
            "items": [
                {
                    "id": identifier,
                    "kind": "key",
                    "analyzer_id": "synthetic-key",
                    "analyzer_version": "1",
                    "lyrics_version_id": None,
                    "data": {"key": "C", "confidence": 0.7},
                }
            ]
        }
        assert_problem(
            client.get(
                f"/api/takes/{models.new_id()}/analysis", headers=headers(token)
            ),
            403,
            "FORBIDDEN_SCOPE",
        )


def test_library_cursor_and_filters_return_stable_disjoint_pages(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        song_id, take_id, _ = ready_take(client, token, tmp_path)
        second = create_song(client, token, "Segundo")
        first_page = client.get(
            "/api/songs", params={"limit": 1}, headers=headers(token)
        ).json()
        assert first_page["next"]
        second_page = client.get(
            "/api/songs",
            params={"limit": 1, "cursor": first_page["next"]},
            headers=headers(token),
        ).json()
        assert second_page["next"] is None
        assert {row["id"] for row in first_page["items"] + second_page["items"]} == {
            song_id,
            second,
        }
        assert (
            client.patch(
                f"/api/takes/{take_id}", headers=headers(token), json={"favorite": True}
            ).status_code
            == 200
        )
        for query, expected in (
            ({"model_id": "mock"}, [song_id]),
            ({"model_id": "missing"}, []),
            ({"favorite": "true"}, [song_id]),
            ({"favorite": "false"}, []),
            (
                {
                    "updated_after": "2000-01-01T00:00:00Z",
                    "updated_before": "2099-01-01T00:00:00Z",
                },
                [song_id, second],
            ),
        ):
            response = client.get("/api/songs", params=query, headers=headers(token))
            assert response.status_code == 200, response.text
            assert {row["id"] for row in response.json()["items"]} == set(expected)
        for identifier in (song_id, second):
            assert (
                client.delete(
                    f"/api/songs/{identifier}", headers=headers(token)
                ).status_code
                == 204
            )
        trash1 = client.get(
            "/api/songs/trash", params={"limit": 1}, headers=headers(token)
        ).json()
        trash2 = client.get(
            "/api/songs/trash",
            params={"limit": 1, "cursor": trash1["next"]},
            headers=headers(token),
        ).json()
        assert trash2["next"] is None
        assert {row["id"] for row in trash1["items"] + trash2["items"]} == {
            song_id,
            second,
        }


def test_library_rejects_invalid_filters_without_mutating_data(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        identifier = create_song(client, token, "Intacta")
        for route in ("/api/songs", "/api/songs/trash"):
            for params in (
                {"limit": "abc"},
                {"limit": "0"},
                {"limit": "101"},
                {"cursor": "missing-separator"},
                {"cursor": "stamp|short"},
            ):
                assert_problem(
                    client.get(route, params=params, headers=headers(token)),
                    422,
                    "INVALID_PARAMS",
                )
        for params in ({"favorite": "yes"}, {"status": "unknown"}, {"q": '"'}):
            assert_problem(
                client.get("/api/songs", params=params, headers=headers(token)),
                422,
                "INVALID_PARAMS",
            )
        assert (
            client.get(f"/api/songs/{identifier}", headers=headers(token)).json()[
                "title"
            ]
            == "Intacta"
        )
        assert_problem(
            client.patch(f"/api/songs/{identifier}", headers=headers(token), json={}),
            422,
            "INVALID_PARAMS",
        )


def test_retry_api_reuses_failed_take_and_preserves_original_request(tmp_path):
    with TestClient(application(tmp_path), base_url="http://127.0.0.1:8000") as client:
        token = issue(client)
        response = client.post(
            "/api/generations",
            headers=headers(token),
            json={
                "task": "music.instrumental",
                "model_id": "mock",
                "seed": 17,
                "params": {"duration_s": 2},
            },
        )
        assert response.status_code == 202, response.text
        original = response.json()
        job_id, take_id = original["generation_job_id"], original["take_ids"][0]
        assert_problem(
            client.post(f"/api/jobs/{job_id}/retry", headers=headers(token)),
            409,
            "CONFLICT",
        )
        with Session(client.app.state.db) as session, session.begin():
            job, take = (
                session.get(models.Job, job_id),
                session.get(models.Take, take_id),
            )
            job.status, take.status = "failed", "failed"
            job.error_code = take.error_code = "INTERNAL"
            original_request = job.request
        retried = client.post(f"/api/jobs/{job_id}/retry", headers=headers(token))
        assert retried.status_code == 202, retried.text
        assert retried.json()["take_ids"] == [take_id]
        assert retried.json()["generation_job_id"] != job_id
        with Session(client.app.state.db) as session:
            assert session.get(models.Job, job_id).request == original_request
            replacement = session.get(models.Job, retried.json()["generation_job_id"])
            assert replacement.request == original_request
            take = session.get(models.Take, take_id)
            assert take.job_id == replacement.id
            assert take.status == "queued"
            assert take.seed == 17
            assert take.root_id == take_id
        assert_problem(
            client.post(f"/api/jobs/{job_id}/retry", headers=headers(token)),
            409,
            "CONFLICT",
        )
        assert_problem(
            client.post(f"/api/jobs/{models.new_id()}/retry", headers=headers(token)),
            409,
            "CONFLICT",
        )
        assert_problem(
            client.post(
                f"/api/jobs/{job_id}/retry", headers={"Origin": "http://127.0.0.1:3000"}
            ),
            401,
            "SESSION_REQUIRED",
        )


def test_retry_without_engine_is_unavailable(tmp_path):
    with connection(tmp_path) as client:
        token = issue(client)
        _, _, job_id = ready_take(client, token, tmp_path)
        assert_problem(
            client.post(f"/api/jobs/{job_id}/retry", headers=headers(token)),
            503,
            "SERVICE_UNAVAILABLE",
        )
