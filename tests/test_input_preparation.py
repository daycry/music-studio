"""Preparación fiel con textos sintéticos."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def preparation():
    path = ROOT / "scripts/input_preparation.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("input_preparation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_identity_and_explicit_tags():
    m = preparation()
    raw = b"\xef\xbb\xbf**[Verse: soft]**\r\n*literal verse*\r\n"
    request = {
        "task": "music.song",
        "params": {"lyrics": raw.decode("utf-8-sig"), "style": "synthetic"},
        "lyrics_declaration": "own",
    }
    result = getattr(m, "prepare", lambda *a, **k: {})(request, sources={"lyrics": raw})
    assert result.get("effective") == request
    assert (
        result["fields"]["lyrics"]["original_bytes_sha256"]
        != result["fields"]["lyrics"]["effective_sha256"]
    )
    changed = m.prepare(request, sources={"lyrics": raw}, strip_tag_markdown=True)
    assert (
        changed["effective"]["params"]["lyrics"]
        == "[Verse: soft]\r\n*literal verse*\r\n"
    )
    assert changed["fields"]["lyrics"]["diff"]
    assert changed["transformations"] == ["strip_tag_markdown"]
    assert request["params"]["lyrics"].startswith("**[")


def test_receipt_integrity_and_immutable_publication(tmp_path):
    import json

    import pytest

    m = preparation()
    request = {
        "task": "music.instrumental",
        "params": {"style": "private"},
        "lyrics_declaration": None,
    }
    receipt = m.prepare(request)
    ref = getattr(m, "publish", lambda *a: None)(receipt, tmp_path)
    assert isinstance(ref, dict) and len(ref["sha256"]) == 64
    assert m.publish(receipt, tmp_path) == ref
    assert m.verify(ref, request, tmp_path) == receipt
    changed = dict(request, params={"style": "other"})
    with pytest.raises(ValueError, match="PREPARATION_REQUEST_MISMATCH"):
        m.verify(ref, changed, tmp_path)
    path = tmp_path / "preparations" / (ref["sha256"] + ".json")
    path.write_text(json.dumps(dict(receipt, engine_budget="invented")))
    with pytest.raises(ValueError, match="PREPARATION_HASH_MISMATCH"):
        m.verify(ref, request, tmp_path)
    with pytest.raises(ValueError, match="PREPARATION_HASH_MISMATCH"):
        m.publish(receipt, tmp_path)


def test_atomic_failure_and_paths(tmp_path, monkeypatch):
    import pytest

    m = preparation()
    receipt = m.prepare({"task": "music.instrumental", "params": {"style": "private"}})

    def fail(*a):
        raise OSError("synthetic failure")

    monkeypatch.setattr(m.os, "link", fail)
    with pytest.raises(OSError):
        m.publish(receipt, tmp_path)
    assert list((tmp_path / "preparations").iterdir()) == []
    for value in ["../outside", "A" * 64, None]:
        with pytest.raises(ValueError, match="PREPARATION_INVALID"):
            m.verify({"sha256": value}, receipt["effective"], tmp_path)
    altered = dict(receipt, fields={})
    with pytest.raises(ValueError, match="PREPARATION_INVALID"):
        m.publish(altered, tmp_path)


def test_lyrics_source_disagreement_rejected():
    import pytest

    m = preparation()
    with pytest.raises(ValueError, match="PREPARATION_SOURCE_MISMATCH"):
        m.prepare(
            {"task": "music.song", "params": {"lyrics": "verse", "style": "caption"}},
            sources={"lyrics": b"different verse"},
        )


def test_effective_request_hash():
    m = preparation()
    request = {"task": "music.instrumental", "params": {"style": "caption"}}
    receipt = m.prepare(request)
    assert receipt.get("effective_request_sha256") == m.digest(m.encode(request))


def test_declared_lyrics_hash_matches_source_bytes():
    import pytest

    m = preparation()
    raw = b"\xef\xbb\xbf**[Verse]**\r\nsynthetic verse\r\n"
    request = {
        "task": "music.song",
        "params": {"lyrics": raw.decode("utf-8-sig"), "style": "caption"},
        "lyrics_sha256": "0" * 64,
    }
    with pytest.raises(ValueError, match="PREPARATION_SOURCE_MISMATCH"):
        m.prepare(request, sources={"lyrics": raw}, strip_tag_markdown=True)
    request["lyrics_sha256"] = m.digest(raw)
    receipt = m.prepare(request, sources={"lyrics": raw}, strip_tag_markdown=True)
    assert receipt["effective"]["lyrics_sha256"] == m.digest(raw)
    assert receipt["fields"]["lyrics"]["effective_sha256"] != m.digest(raw)


def test_execution_binding_preserves_requested_seed():
    import pytest

    m = preparation()
    request = {
        "task": "music.instrumental",
        "params": {"style": "caption"},
        "seed": None,
        "n_outputs": 2,
    }
    receipt = m.prepare(request)
    bound = getattr(m, "bind_execution", lambda *a, **k: {})(
        receipt, seed=1234, n_outputs=2
    )
    assert bound.get("execution") == {"seed": 1234, "n_outputs": 2}
    assert bound["original"]["seed"] is None and bound["effective"]["seed"] is None
    assert "execution" not in receipt
    m.validate_receipt(bound)
    for kwargs in (
        {"seed": True, "n_outputs": 2},
        {"seed": -1, "n_outputs": 2},
        {"seed": 1234, "n_outputs": 1},
        {"seed": 2**64 - 1, "n_outputs": 2},
    ):
        with pytest.raises(ValueError, match="PREPARATION_EXECUTION_MISMATCH"):
            m.bind_execution(receipt, **kwargs)
    declared = m.prepare(dict(request, seed=1))
    with pytest.raises(ValueError, match="PREPARATION_EXECUTION_MISMATCH"):
        m.bind_execution(declared, seed=1234, n_outputs=2)


def test_malformed_receipt_fields_has_typed_error():
    import pytest

    m = preparation()
    receipt = m.prepare({"task": "music.instrumental", "params": {"style": "caption"}})
    receipt["fields"] = []
    with pytest.raises(ValueError, match="PREPARATION_INVALID"):
        m.validate_receipt(receipt)
