"""CLI de preparación offline y metadata opcional."""

import pytest
from test_generate import module

DIRECT = ["--task", "music.instrumental", "--style", "synthetic", "--duration", "30"]


def test_native_receipt_publication_rejects_forgery(tmp_path):
    m = module()
    assert hasattr(m, "publish_input_receipts"), (
        "CLI pierde captura efectiva del engine"
    )
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        m.publish_input_receipts(
            {
                "input_receipts": [
                    {
                        "filename": "../private.json",
                        "sha256": "a" * 64,
                        "output_index": 0,
                    }
                ]
            },
            tmp_path,
            "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            {},
            1,
        )


def _native_receipt_fixture():
    """Recibo sintético consistente para comprobar integridad, sin afirmar inferencia."""
    import hashlib
    import json

    def sha(value):
        return hashlib.sha256(
            json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()

    request = {
        "task": "music.song",
        "seed": 1,
        "n_outputs": 1,
        "params": {
            "style": "synthetic",
            "lyrics": "synthetic",
            "duration_s": 30,
            "language": "es",
        },
    }
    effective = {
        "params": {
            "caption": "synthetic",
            "lyrics": "synthetic",
            "duration": 30,
            "seed": 1,
            "vocal_language": "es",
            "instrumental": False,
            "bpm": None,
            "keyscale": "",
            "enable_normalization": False,
            "lm_negative_prompt": "NO USER INPUT",
            "use_cot_caption": False,
            "use_cot_language": False,
            "use_cot_metas": False,
        },
        "thinking": True,
        "shift": 1.0,
        "guidance_scale": 7.0,
        "inference_steps": 8,
        "lm_cfg_scale": 2.0,
        "audio_cover_strength": 1.0,
        "legacy_cfg_prompt": False,
        "lm_metadata": {"duration": 30, "language": "es"},
    }
    text = {"count": 100, "tokens_sha256": "a" * 64, "input_sha256": "b" * 64}
    lyric = {"count": 10, "tokens_sha256": "c" * 64, "input_sha256": "d" * 64}
    lm = {
        "conditional": text,
        "unconditional": lyric,
        "reserve_tokens": 160,
        "context_policy": 4096,
    }
    planned = {
        "receipt_version": 1,
        "kind": "planned",
        "request": request,
        "request_sha256": sha(request),
        "effective": effective,
        "effective_sha256": sha(effective),
        "lm": lm,
        "dit": {"text": text, "lyrics": lyric},
    }
    captured = {
        "receipt_version": 1,
        "kind": "captured",
        "output_index": 0,
        "planned_sha256": sha(planned),
        "flags": {
            "thinking": True,
            "shift": 1.0,
            "guidance_scale": 7.0,
            "inference_steps": 8,
            "lm_cfg_scale": 2.0,
            "audio_cover_strength": 1.0,
            "use_cot_caption": False,
            "use_cot_language": False,
            "use_cot_metas": False,
        },
        "boundaries": [
            {"stage": "lm_arguments", "metadata": {"duration": 30, "language": "es"}},
            {
                "stage": "lm_formatted_prompt",
                "conditional": text,
                "unconditional": lyric,
                "reserve_tokens": 160,
            },
            {"stage": "dit_arguments", "arguments_sha256": sha(effective)},
            {
                "stage": "dit_tokens",
                "text": {k: text[k] for k in ("count", "tokens_sha256")},
                "lyrics": {k: lyric[k] for k in ("count", "tokens_sha256")},
            },
        ],
    }
    return {"planned": planned, "captured": captured}, request


def _rehash_native_receipt(receipt):
    """Recalcula toda la integridad interna tras una alteración semántica."""
    import hashlib
    import json

    def sha(value):
        return hashlib.sha256(
            json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()

    planned, captured = receipt["planned"], receipt["captured"]
    planned["request_sha256"] = sha(planned["request"])
    planned["effective_sha256"] = sha(planned["effective"])
    captured["planned_sha256"] = sha(planned)
    captured["generation_params_sha256"] = sha(planned["effective"]["params"])
    captured["boundaries"][2]["arguments_sha256"] = sha(planned["effective"])


@pytest.mark.parametrize(
    "checkpoint,params,steps,cfg",
    [
        ("acestep-v15-sft", {}, 50, 7),
        ("acestep-v15-sft", {"inference_steps": 41, "guidance_scale": 3}, 41, 3),
        ("acestep-v15-turbo", {"inference_steps": 4}, 4, 7),
    ],
)
def test_native_receipt_checkpoint_controls(checkpoint, params, steps, cfg):
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    request["params"].update(params)
    request["model_id"] = (
        "ace-step-1.5-sft" if checkpoint.endswith("sft") else "ace-step-1.5-turbo"
    )
    receipt["planned"]["checkpoint"] = {"id": checkpoint}
    effective = receipt["planned"]["effective"]
    effective.update(inference_steps=steps, guidance_scale=cfg)
    effective["params"].update(inference_steps=steps, guidance_scale=cfg)
    receipt["captured"]["flags"].update(inference_steps=steps, guidance_scale=cfg)
    _rehash_native_receipt(receipt)
    assert (
        validate_input_receipt(json.dumps(receipt), request, 0, private_params=True)
        == receipt
    )
    # Integridad recalculada no legitima parámetros/capturas incoherentes.
    effective["params"]["inference_steps"] += 1
    _rehash_native_receipt(receipt)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0, private_params=True)


@pytest.mark.parametrize(
    "mismatch", ["checkpoint", "native_identity", "published_identity"]
)
def test_native_receipt_checkpoint_identity_mismatch(mismatch):
    import copy
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    request["model_id"] = "ace-step-1.5-turbo"
    receipt["planned"]["checkpoint"] = {"id": "acestep-v15-turbo"}
    expected = copy.deepcopy(request)
    if mismatch == "checkpoint":
        receipt["planned"]["checkpoint"]["id"] = "acestep-v15-sft"
    elif mismatch == "native_identity":
        request["model_id"] = "ace-step-1.5-sft"
    else:
        expected["model_id"] = "ace-step-1.5-sft"
    _rehash_native_receipt(receipt)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), expected, 0, private_params=True)


@pytest.mark.parametrize("control", ["inference_steps", "guidance_scale"])
def test_native_receipt_rejects_boolean_control_capture(control):
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    request["model_id"] = "ace-step-1.5-sft"
    request["params"].update(inference_steps=1, guidance_scale=1)
    receipt["planned"]["checkpoint"] = {"id": "acestep-v15-sft"}
    effective = receipt["planned"]["effective"]
    effective.update(inference_steps=1, guidance_scale=1)
    effective["params"].update(inference_steps=1, guidance_scale=1)
    receipt["captured"]["flags"].update(inference_steps=1, guidance_scale=1)
    effective[control] = receipt["captured"]["flags"][control] = True
    _rehash_native_receipt(receipt)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0, private_params=True)


SEMANTIC_MUTATIONS = [
    "language",
    "language_alias",
    "language_conflict",
    "shift",
    "bpm",
    "key",
    "time_signature",
    "invented_metadata",
    "cot_flags",
    "thinking",
    "guidance_scale",
    "inference_steps",
    "lm_cfg_scale",
    "audio_cover_strength",
    "context_policy",
    "reserve_tokens",
    "captured_metadata",
    "legacy_cfg_prompt",
]


def _mutate_native_semantics(receipt, mutation):
    planned, captured = receipt["planned"], receipt["captured"]
    effective = planned["effective"]
    params = effective["params"]
    requested = planned["request"]["params"]
    if mutation in {"language", "language_alias", "language_conflict"}:
        if mutation == "language_alias":
            requested["vocal_language"] = requested.pop("language")
        elif mutation == "language_conflict":
            requested["vocal_language"] = "en"
        params["vocal_language"] = "en"
        effective["lm_metadata"]["language"] = "en"
        captured["boundaries"][0]["metadata"]["language"] = "en"
    elif mutation == "shift":
        requested["shift"] = 3
    elif mutation in {"bpm", "key", "time_signature", "invented_metadata"}:
        key = {
            "bpm": "bpm",
            "key": "keyscale",
            "time_signature": "timesignature",
            "invented_metadata": "bpm",
        }[mutation]
        if mutation != "invented_metadata":
            requested[mutation] = {
                "bpm": 120,
                "key": "C minor",
                "time_signature": "3/4",
            }[mutation]
        params[key] = {"bpm": 90, "keyscale": "D minor", "timesignature": "4/4"}[key]
        effective["lm_metadata"][key] = params[key]
        captured["boundaries"][0]["metadata"][key] = params[key]
    elif mutation == "cot_flags":
        for key in ("use_cot_caption", "use_cot_language", "use_cot_metas"):
            params[key] = captured["flags"][key] = True
    elif mutation in {"context_policy", "reserve_tokens"}:
        planned["lm"][mutation] += 1
        if mutation == "reserve_tokens":
            captured["boundaries"][1][mutation] += 1
    elif mutation == "captured_metadata":
        captured["boundaries"][0]["metadata"]["bpm"] = 90
    elif mutation == "legacy_cfg_prompt":
        effective["legacy_cfg_prompt"] = True
    else:
        effective[mutation] = captured["flags"][mutation] = (
            False if mutation == "thinking" else effective[mutation] + 1
        )
    _rehash_native_receipt(receipt)


@pytest.mark.parametrize("mutation", SEMANTIC_MUTATIONS)
def test_native_receipt_rejects_rehashed_semantic_contradiction(mutation):
    import copy
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    assert validate_input_receipt(json.dumps(receipt), request, 0) == receipt
    _mutate_native_semantics(receipt, mutation)
    request = copy.deepcopy(receipt["planned"]["request"])
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0, private_params=True)


@pytest.mark.parametrize("case", ["alias", "metadata", "omitted", "instrumental"])
def test_native_receipt_preserves_requested_metadata_and_defaults(case):
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    effective = receipt["planned"]["effective"]
    values = effective["params"]
    metadata = effective["lm_metadata"]
    if case == "alias":
        request["params"]["vocal_language"] = request["params"].pop("language")
    elif case == "metadata":
        request["params"].update(bpm=120, key="C minor", time_signature="3/4", shift=3)
        values.update(bpm=120, keyscale="C minor", timesignature="3/4", shift=3)
        metadata.update(bpm=120, keyscale="C minor", timesignature="3/4")
        effective["shift"] = receipt["captured"]["flags"]["shift"] = 3
    elif case == "omitted":
        request["params"].pop("language")
        values["vocal_language"] = metadata["language"] = "unknown"
    else:
        request["task"] = "music.instrumental"
        request["params"].pop("lyrics")
        values.update(instrumental=True, lyrics="[Instrumental]")
    receipt["captured"]["boundaries"][0]["metadata"] = dict(metadata)
    _rehash_native_receipt(receipt)
    assert validate_input_receipt(json.dumps(receipt), request, 0) == receipt


@pytest.mark.parametrize("mutation", [None, "language", "shift", "cot_flags"])
def test_generation_native_semantics_before_cas(tmp_path, monkeypatch, mutation):
    import copy
    import hashlib
    import json

    import httpx
    from audio_post import verify_manifest
    from test_generate import ROOT, publication_setup

    monkeypatch.syspath_prepend(str(ROOT / "apps/engines/acestep"))
    from descriptor import descriptor

    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    receipt, native_request = _native_receipt_fixture()
    if mutation:
        _mutate_native_semantics(receipt, mutation)
    request.update(copy.deepcopy(native_request))
    request.update(
        lyrics_declaration="own", lyrics_sha256=hashlib.sha256(b"synthetic").hexdigest()
    )
    payload = json.dumps(receipt).encode()
    digest = hashlib.sha256(payload).hexdigest()
    original = transport.handle_request

    def with_receipt(req):
        response = original(req)
        if req.url.path == "/v1/models":
            models = response.json()
            models[0]["tasks"]["music.song"] = {
                **models[0]["tasks"]["music.instrumental"],
                "params_schema": descriptor().tasks["music.song"].params_schema,
            }
            return httpx.Response(200, json=models)
        if req.url.path.endswith("/events"):
            event = json.loads(response.content)
            job_id = event["job_id"]
            (data / f"tmp/{job_id}/input-receipt-0.json").write_bytes(payload)
            event["data"]["result"] = {
                "input_receipts": [
                    {
                        "filename": "input-receipt-0.json",
                        "sha256": digest,
                        "output_index": 0,
                    }
                ]
            }
            return httpx.Response(200, content=json.dumps(event))
        return response

    monkeypatch.setattr(transport, "handle_request", with_receipt)
    with httpx.Client(transport=transport) as client:
        if mutation:
            with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
                m.generate(request, config=config, client=client)
            assert not (data / f"preparations/native-{digest}.json").exists()
            assert not list(data.glob("cli/*/*/manifest.json"))
        else:
            destinations = m.generate(request, config=config, client=client)
            path = destinations[0] / "manifest.json"
            assert verify_manifest(path, path.parent)["valid"]
            # A hostile CAS entry with all hashes refreshed must also fail verification.
            changed = copy.deepcopy(receipt)
            _mutate_native_semantics(changed, "language")
            changed_payload = json.dumps(changed).encode()
            changed_digest = hashlib.sha256(changed_payload).hexdigest()
            (data / f"preparations/native-{changed_digest}.json").write_bytes(
                changed_payload
            )
            manifest = json.loads(path.read_text())
            manifest["input_receipts"][0]["sha256"] = changed_digest
            with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
                verify_manifest(manifest, path.parent)


def test_native_receipt_publishes_privately_and_is_bound_to_request(tmp_path):
    import hashlib
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    payload = json.dumps(receipt).encode()
    value = hashlib.sha256(payload).hexdigest()
    job_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    source = tmp_path / f"tmp/{job_id}"
    source.mkdir(parents=True)
    (source / "input-receipt-0.json").write_bytes(payload)
    result = {
        "input_receipts": [
            {"filename": "input-receipt-0.json", "sha256": value, "output_index": 0}
        ]
    }
    references = module().publish_input_receipts(result, tmp_path, job_id, request, 1)
    assert references == [{"sha256": value, "output_index": 0}]
    assert (tmp_path / f"preparations/native-{value}.json").read_bytes() == payload
    assert "synthetic" not in json.dumps(references)
    assert (
        module().publish_input_receipts(result, tmp_path, job_id, request, 1)
        == references
    )
    assert validate_input_receipt(payload, request, 0) == receipt
    for changed in (
        {**request, "seed": 2},
        {**request, "params": {**request["params"], "style": "different"}},
        {**request, "variant_index": 1},
    ):
        with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
            validate_input_receipt(payload, changed, 0)
    (source / "input-receipt-0.json").write_bytes(payload + b" ")
    with pytest.raises(ValueError, match="INPUT_RECEIPT_HASH_MISMATCH"):
        module().publish_input_receipts(result, tmp_path, job_id, request, 1)


@pytest.mark.parametrize(
    "mutation", ["planned", "missing_boundary", "tokens", "reserve", "language"]
)
def test_native_receipt_rejects_internal_inconsistency(mutation):
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    if mutation == "planned":
        receipt["planned"]["effective"]["params"]["caption"] = "changed"
    elif mutation == "missing_boundary":
        receipt["captured"]["boundaries"].pop()
    elif mutation == "tokens":
        receipt["captured"]["boundaries"][3]["text"]["tokens_sha256"] = "0" * 64
    elif mutation == "reserve":
        receipt["captured"]["boundaries"][1]["reserve_tokens"] -= 1
    else:
        receipt["captured"]["boundaries"][0]["metadata"]["language"] = "en"
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0)


def test_native_receipt_requires_captured_effective_defaults():
    import json

    from audio_post.manifest import validate_input_receipt

    receipt, request = _native_receipt_fixture()
    receipt["captured"].pop("flags", None)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0)


def test_native_receipt_negative_prompt_matches_effective_input():
    import hashlib
    import json

    from audio_post.manifest import validate_input_receipt

    def digest(value):
        return hashlib.sha256(
            json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()

    receipt, request = _native_receipt_fixture()
    request["params"]["negative_prompt"] = "private original"
    planned = receipt["planned"]
    planned["effective"]["params"]["lm_negative_prompt"] = "private substituted"
    planned["request_sha256"] = digest(planned["request"])
    planned["effective_sha256"] = digest(planned["effective"])
    receipt["captured"]["planned_sha256"] = digest(planned)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        validate_input_receipt(json.dumps(receipt), request, 0, private_params=True)


def test_native_receipt_interrupted_write_cannot_leave_partial_cas(
    tmp_path, monkeypatch
):
    import hashlib
    import json
    from pathlib import Path

    receipt, request = _native_receipt_fixture()
    payload = json.dumps(receipt).encode()
    value = hashlib.sha256(payload).hexdigest()
    job_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    source = tmp_path / f"tmp/{job_id}"
    source.mkdir(parents=True)
    (source / "input-receipt-0.json").write_bytes(payload)
    result = {
        "input_receipts": [
            {"filename": "input-receipt-0.json", "sha256": value, "output_index": 0}
        ]
    }
    original = Path.open

    class InterruptingFile:
        def __init__(self, path, *args, **kwargs):
            self.stream = original(path, *args, **kwargs)

        def __enter__(self):
            return self

        def write(self, content):
            self.stream.write(content[:20])
            self.stream.flush()
            raise OSError("interrupted fixture")

        def __exit__(self, *args):
            self.stream.close()

    def open_file(path, *args, **kwargs):
        if path.name.endswith(".json") and args and args[0] == "xb":
            return InterruptingFile(path, *args, **kwargs)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_file)
    with pytest.raises(OSError, match="interrupted fixture"):
        module().publish_input_receipts(result, tmp_path, job_id, request, 1)
    assert not (tmp_path / f"preparations/native-{value}.json").exists()
    assert list((tmp_path / "preparations").iterdir()) == []
    monkeypatch.setattr(Path, "open", original)
    assert module().publish_input_receipts(result, tmp_path, job_id, request, 1) == [
        {"sha256": value, "output_index": 0}
    ]


def test_native_receipt_malformed_reference_is_typed(tmp_path):
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        module().publish_input_receipts(
            {"input_receipts": [None]}, tmp_path, "01ARZ3NDEKTSV4RRFFQ69G5FAV", {}, 1
        )


def test_manifest_checks_the_same_native_bytes_it_hashes(tmp_path, monkeypatch):
    import hashlib
    import json
    from pathlib import Path

    import audio_post.manifest as manifest_module

    receipt, request = _native_receipt_fixture()
    payload = json.dumps(receipt).encode()
    value = hashlib.sha256(payload).hexdigest()
    folder = tmp_path / "preparations"
    folder.mkdir()
    path = folder / f"native-{value}.json"
    path.write_bytes(payload)
    # Unidad de frontera IO; el schema público se comprueba en las pruebas de publicación.
    manifest = {
        "input_receipts": [{"sha256": value, "output_index": 0}],
        "request": {
            **request,
            "params": {
                k: v
                for k, v in request["params"].items()
                if k not in {"style", "lyrics"}
            },
        },
        "models": [],
        "tools": [],
        "inputs": [],
        "commercial_use": True,
        "outputs": [],
    }
    monkeypatch.setattr(manifest_module, "_validate", lambda *a: None)
    original = Path.read_bytes
    reads = []

    def read(path_to_read):
        if path_to_read == path:
            reads.append(path_to_read)
        return original(path_to_read)

    monkeypatch.setattr(Path, "read_bytes", read)
    assert manifest_module.verify_manifest(manifest, tmp_path)["valid"]
    assert reads == [path]


def test_manifest_native_receipt_is_bound_to_private_preparation(tmp_path, monkeypatch):
    import hashlib
    import json

    import audio_post.manifest as manifest_module

    m = module()
    native, request = _native_receipt_fixture()
    # Preparación real alternativa; el recibo nativo sigue siendo internamente válido.
    changed = {
        **request,
        "params": {**request["params"], "style": "different private caption"},
    }
    preparation = m.preparation.prepare(changed)
    preparation["execution"] = {"seed": 1, "n_outputs": 1}
    folder = tmp_path / "preparations"
    folder.mkdir()
    refs = {}
    for name, value in (("native", native), ("preparation", preparation)):
        payload = json.dumps(value).encode()
        digest = hashlib.sha256(payload).hexdigest()
        (
            folder / (("native-" if name == "native" else "") + digest + ".json")
        ).write_bytes(payload)
        refs[name] = digest
    manifest = {
        "input_receipts": [{"sha256": refs["native"], "output_index": 0}],
        "preparation": {"sha256": refs["preparation"]},
        "request": {
            **request,
            "variant_index": 0,
            "params": {
                k: v
                for k, v in request["params"].items()
                if k not in {"style", "lyrics"}
            },
        },
        "models": [],
        "tools": [],
        "inputs": [],
        "commercial_use": True,
        "outputs": [],
    }
    monkeypatch.setattr(manifest_module, "_validate", lambda *a: None)
    with pytest.raises(ValueError, match="INPUT_RECEIPT_INVALID"):
        manifest_module.verify_manifest(manifest, tmp_path)


def test_negative_prompt_is_accepted_and_published_only_privately(
    tmp_path, monkeypatch
):
    import json

    import httpx
    from audio_post import verify_manifest
    from test_generate import ROOT

    monkeypatch.syspath_prepend(str(ROOT / "apps/engines/acestep"))
    from descriptor import descriptor
    from engine_contract import JobRequest
    from test_generate import publication_setup

    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    request["params"].update(
        duration_s=30, negative_prompt="private excluded instruments"
    )
    JobRequest.model_validate(
        {
            **request,
            "job_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "model_id": "mock",
            "mode": "cpu",
            "timeout_s": 60,
            "output_dir": "tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV",
        }
    )
    original = transport.handle_request

    def ace_schema(req):
        response = original(req)
        if req.url.path == "/v1/models":
            models = response.json()
            models[0]["tasks"]["music.instrumental"]["params_schema"] = (
                descriptor().tasks["music.instrumental"].params_schema
            )
            return httpx.Response(200, json=models)
        return response

    monkeypatch.setattr(transport, "handle_request", ace_schema)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    manifest = json.loads((destinations[0] / "manifest.json").read_text())
    assert "negative_prompt" not in manifest["request"]["params"]
    assert "private excluded instruments" not in json.dumps(manifest)
    private = json.loads(
        (
            data / "preparations" / (manifest["preparation"]["sha256"] + ".json")
        ).read_text()
    )
    assert (
        private["effective"]["params"]["negative_prompt"]
        == request["params"]["negative_prompt"]
    )
    assert verify_manifest(manifest, destinations[0])["valid"]
    # Los recibos públicos antiguos se leen sin reescribirlos.
    manifest["request"]["params"]["negative_prompt"] = request["params"][
        "negative_prompt"
    ]
    assert verify_manifest(manifest, destinations[0])["valid"]


def test_offline_prepare_and_metadata(tmp_path, monkeypatch, capsys):
    m = module()
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "generate", lambda *a, **k: pytest.fail("engine contacted"))
    monkeypatch.setattr(m, "environment", lambda: pytest.fail("environment contacted"))
    assert (
        m.main(
            DIRECT + ["--prepare-only", "--key", "C minor", "--time-signature", "4/4"]
        )
        == 0
    )
    assert "pending" in capsys.readouterr().out
    paths = list((tmp_path / "data/preparations").glob("*.json"))
    assert len(paths) == 1
    import json

    receipt = json.loads(paths[0].read_text(encoding="utf-8"))
    assert receipt["effective"]["params"]["key"] == "C minor"
    assert receipt["effective"]["params"]["time_signature"] == "4/4"


def test_source_style_and_tag_opt_in(tmp_path):
    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_bytes(b"\xef\xbb\xbf**[Verse: exact]**\r\n*literal*\r\n")
    source = tmp_path / "style.txt"
    source.write_text("long private source", encoding="utf-8")
    args = [
        "--lyrics",
        str(lyrics),
        "--style",
        "explicit caption",
        "--source-style-file",
        str(source),
        "--duration",
        "30",
        "--language",
        "es",
        "--lyrics-declaration",
        "own",
    ]
    result = module().read_request(args, root=tmp_path)
    assert result["params"]["lyrics"] == lyrics.read_bytes().decode("utf-8-sig")
    assert (
        result["_preparation"]["fields"]["style"]["original"] == "long private source"
    )
    assert result["_preparation"]["transformations"] == ["explicit_style"]
    changed = module().read_request(args + ["--strip-tag-markdown"], root=tmp_path)
    assert changed["params"]["lyrics"] == "[Verse: exact]\r\n*literal*\r\n"
    assert changed["lyrics_sha256"] == result["lyrics_sha256"]


@pytest.mark.parametrize(
    "args", [["--key", ""], ["--time-signature", "0/4"], ["--time-signature", "4/3"]]
)
def test_metadata_invalid(args):
    with pytest.raises(ValueError, match="INVALID_PARAMS"):
        module().read_request(DIRECT + args)


def test_brief_metadata_conflict_and_omission(tmp_path):
    directory = tmp_path / "eval/briefs"
    directory.mkdir(parents=True)
    (directory / "briefs.yaml").write_text(
        "version: 1\nbriefs:\n  S:\n    task: music.instrumental\n    style: synthetic\n    duration_s: 30\n    language: es\n    key: D minor\n    time_signature: 3/4\n",
        encoding="utf-8",
    )
    m = module()
    result = m.read_request(["--brief", "S"], root=tmp_path)
    assert result["params"]["key"] == "D minor"
    assert result["params"]["time_signature"] == "3/4"
    for args in [["--key", "C"], ["--time-signature", "4/4"]]:
        with pytest.raises(ValueError, match="BRIEF_ARGUMENT_CONFLICT"):
            m.read_request(["--brief", "S", *args], root=tmp_path)
    assert "key" not in m.read_request(DIRECT)["params"]
    assert "time_signature" not in m.read_request(DIRECT)["params"]


def test_generation_receipt_and_disagreement_before_http(tmp_path, monkeypatch):
    import json

    import httpx
    from test_generate import publication_setup

    m, request, config, transport, _data = publication_setup(tmp_path, monkeypatch)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    manifest = json.loads((destinations[0] / "manifest.json").read_text())
    assert "preparation" in manifest
    assert "synthetic" not in json.dumps(manifest["request"])
    request["preparation"] = manifest["preparation"]
    request["params"]["style"] = "changed"

    class Offline:
        def request(self, *a, **kw):
            pytest.fail("HTTP before integrity check")

    with pytest.raises(ValueError, match="PREPARATION_REQUEST_MISMATCH"):
        m.generate(request, config=config, client=Offline())


def test_real_cli_entrypoint(tmp_path):
    import subprocess
    import sys

    from test_generate import ROOT

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--prepare-only" in result.stdout


def test_manifest_receipt_tampering_and_privacy(tmp_path, monkeypatch):
    import json

    import httpx
    from audio_post import verify_manifest
    from test_generate import publication_setup

    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    path = destinations[0] / "manifest.json"
    manifest = json.loads(path.read_text())
    ref = manifest["preparation"]
    receipt_path = data / "preparations" / (ref["sha256"] + ".json")
    original = receipt_path.read_bytes()
    receipt_path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="PREPARATION_HASH_MISMATCH"):
        verify_manifest(path, path.parent)
    receipt_path.write_bytes(original)
    manifest["request"]["params"]["duration_s"] = 20
    with pytest.raises(ValueError, match="PREPARATION_REQUEST_MISMATCH"):
        verify_manifest(manifest, path.parent)
    manifest["preparation"]["lyrics"] = "private"
    with pytest.raises(ValueError, match="MANIFEST_PRIVATE_CONTENT"):
        verify_manifest(manifest, path.parent)


def test_preparation_requires_authorship(tmp_path):
    path = tmp_path / "lyrics.txt"
    path.write_text("synthetic", encoding="utf-8")
    with pytest.raises(ValueError, match="LYRICS_DECLARATION_REQUIRED"):
        module().read_request(
            [
                "--prepare-only",
                "--lyrics",
                str(path),
                "--style",
                "caption",
                "--duration",
                "30",
                "--language",
                "es",
            ],
            root=tmp_path,
        )


@pytest.mark.parametrize("case", ["structure", "field_hash"])
def test_malformed_receipt_with_matching_reference(tmp_path, monkeypatch, case):
    import hashlib
    import json

    import httpx
    from audio_post import verify_manifest
    from test_generate import publication_setup

    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    manifest = json.loads((destinations[0] / "manifest.json").read_text())
    receipt = json.loads(
        (
            data / "preparations" / (manifest["preparation"]["sha256"] + ".json")
        ).read_text()
    )
    if case == "structure":
        receipt["effective"] = {}
    else:
        receipt["fields"]["style"]["effective_sha256"] = "a" * 64
    payload = json.dumps(receipt).encode()
    sha = hashlib.sha256(payload).hexdigest()
    (data / "preparations" / (sha + ".json")).write_bytes(payload)
    manifest["preparation"] = {"sha256": sha}
    with pytest.raises(ValueError, match="PREPARATION_INVALID"):
        verify_manifest(manifest, destinations[0])


def test_manifest_rejects_false_lyrics_source_hash(tmp_path, monkeypatch):
    import copy
    import hashlib
    import json

    import httpx
    from audio_post import verify_manifest
    from test_generate import publication_setup

    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    manifest = json.loads((destinations[0] / "manifest.json").read_text())
    original = copy.deepcopy(request)
    original.update(
        task="music.song",
        lyrics_declaration="own",
        lyrics_sha256=hashlib.sha256(b"synthetic verse").hexdigest(),
    )
    original["params"].update(lyrics="synthetic verse", language="es")
    receipt = m.preparation.prepare(original)
    for kind in ("original", "effective"):
        receipt[kind]["lyrics_sha256"] = "0" * 64
    receipt["effective_request_sha256"] = m.preparation.digest(
        m.preparation.encode(receipt["effective"])
    )
    receipt["execution"] = {
        "seed": original["seed"],
        "n_outputs": original["n_outputs"],
    }
    payload = m.preparation.encode(receipt)
    digest = hashlib.sha256(payload).hexdigest()
    (data / "preparations" / (digest + ".json")).write_bytes(payload)
    manifest["preparation"] = {"sha256": digest}
    manifest["request"].update(
        task="music.song",
        lyrics_declaration="own",
        lyrics_sha256="0" * 64,
        variant_index=0,
    )
    manifest["request"]["params"]["language"] = "es"
    with pytest.raises(ValueError, match="PREPARATION_INVALID"):
        verify_manifest(manifest, destinations[0])


@pytest.mark.parametrize("requested_seed", [1, None])
def test_manifest_variant_seed_binding(tmp_path, monkeypatch, requested_seed):
    import copy
    import json

    import httpx
    from audio_post import verify_manifest
    from test_generate import publication_setup

    m, request, config, transport, data = publication_setup(
        tmp_path, monkeypatch, variants=2
    )
    request["seed"] = requested_seed
    monkeypatch.setattr(m.secrets, "randbits", lambda bits: 1234)
    base_seed = 1 if requested_seed is not None else 1234
    handler = transport.handle_request

    def actual_seeds(req):
        response = handler(req)
        if req.url.path.endswith("/events"):
            event = json.loads(response.content)
            for artifact in event["data"]["artifacts"]:
                artifact["meta"]["seed"] = base_seed + artifact["output_index"]
            return httpx.Response(200, content=json.dumps(event))
        return response

    monkeypatch.setattr(transport, "handle_request", actual_seeds)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    for index, destination in enumerate(destinations):
        manifest = json.loads((destination / "manifest.json").read_text())
        assert verify_manifest(manifest, destination)["valid"]
        for wrong_seed in (99999, base_seed + (1 - index)):
            changed = copy.deepcopy(manifest)
            changed["request"]["seed"] = wrong_seed
            with pytest.raises(ValueError, match="PREPARATION_REQUEST_MISMATCH"):
                verify_manifest(changed, destination)
        assert manifest["request"]["variant_index"] == index
        receipt = json.loads(
            (
                data / "preparations" / (manifest["preparation"]["sha256"] + ".json")
            ).read_text()
        )
        assert receipt["execution"] == {"seed": base_seed, "n_outputs": 2}
        assert receipt["original"]["seed"] == requested_seed
        for invalid_index in (None, True, -1, 2, 0.5):
            changed = copy.deepcopy(manifest)
            changed["request"]["variant_index"] = invalid_index
            with pytest.raises(
                ValueError, match="MANIFEST_SCHEMA|PREPARATION_REQUEST_MISMATCH"
            ):
                verify_manifest(changed, destination)
