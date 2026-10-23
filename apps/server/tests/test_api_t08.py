"""M1/T-08 CA-2: las respuestas 202/unload declaran su modelo en el OpenAPI."""

import pytest
from app.main import create_app
from test_domain_routes import config

CASES = [
    ("/api/generations", "post", "202", "GenerationQueuedDTO"),
    ("/api/jobs/{job_id}/cancel", "post", "202", "JobCancelDTO"),
    ("/api/jobs/{job_id}/retry", "post", "202", "JobRetryDTO"),
    ("/api/system/unload", "post", "200", "UnloadResultDTO"),
]


@pytest.mark.parametrize("path,method,status,name", CASES)
def test_openapi_declares_response_model(tmp_path, path, method, status, name):
    spec = create_app(config(tmp_path)).openapi()
    content = spec["paths"][path][method]["responses"][status]["content"]
    schema = content["application/json"]["schema"]
    assert schema == {"$ref": f"#/components/schemas/{name}"}


def test_declared_fields_match_what_handlers_return(tmp_path):
    schemas = create_app(config(tmp_path)).openapi()["components"]["schemas"]
    assert set(schemas["GenerationQueuedDTO"]["properties"]) == {
        "song_id",
        "generation_job_id",
        "post_job_id",
        "take_ids",
        "beat_job_ids",
    }
    assert set(schemas["JobRetryDTO"]["properties"]) == {
        "generation_job_id",
        "post_job_id",
        "take_ids",
        "beat_job_ids",
    }
    assert set(schemas["JobCancelDTO"]["properties"]) == {"job_id", "cancel_requested"}
    assert set(schemas["UnloadResultDTO"]["properties"]) == {"freed_mb"}
