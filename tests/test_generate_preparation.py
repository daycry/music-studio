"""CLI de preparación offline y metadata opcional."""

import pytest
from test_generate import module

DIRECT = ["--task", "music.instrumental", "--style", "synthetic", "--duration", "30"]


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
