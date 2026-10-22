import copy
import hashlib
from types import SimpleNamespace

import pytest
from app.worker.contracts import CapturedProvenance, PostPlan
from app.worker.planning import compose_post_plan
from test_worker_contracts import provenance as contract_provenance

OWNER = "01K70000000000000000000000"
SONG = "01K70000000000000000000001"
POST = "01K70000000000000000000002"
GEN = "01K70000000000000000000003"
ATTEMPT = "01K70000000000000000000004"
TAKE = "01K70000000000000000000005"


def _provenance():
    value = copy.deepcopy(contract_provenance())
    value["task"] = "music.instrumental"
    value["load"] = {"model_id": "model", "mode": "cpu"}
    value["observed_model"] = {"model_id": "model", "mode": "cpu"}
    value["descriptor"]["tasks"] = {
        "music.instrumental": {"verified": True, "device": "cpu", "params_schema": {}}
    }
    value["descriptor"]["modes"] = [{"id": "cpu", "notes": "default"}]
    return CapturedProvenance.model_validate(value)


def _inputs():
    return [{"role": "source", "ref": {"type": "job", "id": GEN}, "output_index": 0}]


def _fixture(tmp_path):
    source = tmp_path / "data" / "tmp" / ATTEMPT / "0.wav"
    source.parent.mkdir(parents=True)
    payload = b"wav bytes"
    source.write_bytes(payload)
    artifact = {
        "output_index": 0,
        "path": f"tmp/{ATTEMPT}/0.wav",
        "media_type": "audio/wav",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "meta": {"seed": 17},
    }
    post = SimpleNamespace(
        id=POST,
        owner_id=OWNER,
        song_id=SONG,
        status="queued",
        request={"inputs": _inputs()},
    )
    generation = SimpleNamespace(
        id=GEN, status="succeeded", request={"params": {"duration_s": 2}}
    )
    attempt = SimpleNamespace(
        id=ATTEMPT,
        ordinal=1,
        status="succeeded",
        terminal=SimpleNamespace(
            seq=1,
            job_id=ATTEMPT,
            type="done",
            data=SimpleNamespace(artifacts=[artifact]),
            model_dump=lambda mode=None: {
                "seq": 1,
                "job_id": ATTEMPT,
                "type": "done",
                "data": {"artifacts": [artifact]},
            },
        ),
        provenance=_provenance(),
    )
    take = SimpleNamespace(
        id=TAKE,
        owner_id=OWNER,
        song_id=SONG,
        job_id=GEN,
        variant_index=0,
        seed=17,
        duration_s=None,
        params={},
    )
    return post, generation, attempt, [take], [artifact]


def test_compose_post_plan_binds_durable_chain_and_source(tmp_path):
    post, generation, attempt, takes, artifacts = _fixture(tmp_path)
    plan = compose_post_plan(
        post=post,
        generation=generation,
        attempt=attempt,
        takes=takes,
        artifacts=artifacts,
        root=tmp_path,
        execution_id="01K70000000000000000000006",
        tool_pin={"schema_version": 1, "tool_id": "ffmpeg"},
    )

    assert isinstance(plan, PostPlan)
    assert plan.post_job_id == POST
    assert plan.takes[0].authority.take_id == TAKE
    assert plan.takes[0].source.path == f"data/tmp/{ATTEMPT}/0.wav"
    assert plan.takes[0].copied_source.path.endswith("/0.wav")


def test_compose_post_plan_rejects_missing_winning_provenance(tmp_path):
    post, generation, attempt, takes, artifacts = _fixture(tmp_path)
    attempt.provenance = None
    with pytest.raises(ValueError, match="PROVENANCE_MISSING"):
        compose_post_plan(
            post=post,
            generation=generation,
            attempt=attempt,
            takes=takes,
            artifacts=artifacts,
            root=tmp_path,
            execution_id="01K70000000000000000000006",
            tool_pin={"schema_version": 1, "tool_id": "ffmpeg"},
        )
