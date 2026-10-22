"""Recibo privado causal: privacidad, confinamiento y compatibilidad v1."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from audio_post import verify_manifest

ROOT = Path(__file__).resolve().parents[3]
TAKE = "01K6Q000000000000000000001"
SONG = "01K6Q000000000000000000002"


@pytest.fixture
def package(tmp_path):
    data = tmp_path / "data"
    directory = data / "songs" / SONG / "takes" / TAKE
    directory.mkdir(parents=True)
    (directory / "fixture.txt").write_bytes(b"music-studio fixture\n")
    manifest = json.loads(
        (ROOT / "packages/contracts/examples/audio_take.json").read_text()
    )
    manifest["request"].pop("style_prompt")
    manifest["private_context"] = {"sha256": "a" * 64}
    return data, directory, manifest


def test_missing_private_context_is_rejected(package):
    _, directory, manifest = package
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(manifest, directory)


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


@pytest.fixture
def context():
    lyrics = "[Verso]\nLetra privada única"
    request = {
        "job_id": "01K6Q000000000000000000003",
        "task": "music.song",
        "model_id": "fixture-generator",
        "mode": "bf16",
        "inputs": [],
        "params": {
            "lyrics": lyrics,
            "style": "estilo privado único",
            "duration_s": 3,
            "vocal_language": "es",
        },
        "seed": 40,
        "n_outputs": 3,
        "output_dir": "tmp/01K6Q000000000000000000003",
        "timeout_s": 600,
    }
    proof = {
        "lyrics_version_id": "01K6Q000000000000000000004",
        "sha256": hashlib.sha256(lyrics.encode()).hexdigest(),
        "declaration": "licensed",
    }
    return {
        "version": 1,
        "winning_request_sha256": hashlib.sha256(canonical(request)).hexdigest(),
        "captured_request": request,
        "song_id": SONG,
        "takes": {
            TAKE: {
                "output_index": 2,
                "root_id": "01K6Q000000000000000000005",
                "params": copy.deepcopy(request["params"]),
                "model_id": "fixture-generator",
                "model_version": "1.0",
                "commercial_use": True,
                "lineage": {
                    "parents": [
                        {
                            "type": "take",
                            "id": "01K6Q000000000000000000005",
                            "role": "source",
                        }
                    ],
                    "derivation": "variant",
                    "section_map": {"from_s": 0, "to_s": 3},
                },
                "lyrics": proof,
            }
        },
    }


def install(package, value, payload=None):
    data, _, manifest = package
    payload = canonical(value) if payload is None else payload
    digest = hashlib.sha256(payload).hexdigest()
    receipts = data / "private-contexts"
    receipts.mkdir(exist_ok=True)
    path = receipts / f"{digest}.json"
    path.write_bytes(payload)
    manifest["private_context"] = {"sha256": digest}
    manifest["request"] = {
        "task": "music.song",
        "params": {"duration_s": 3, "vocal_language": "es"},
        "seed": 42,
        "variant_index": 2,
        "lyrics_sha256": value["takes"][TAKE]["lyrics"]["sha256"],
        "lyrics_declaration": "licensed",
    }
    manifest["lineage"] = copy.deepcopy(value["takes"][TAKE]["lineage"])
    manifest["models"][0].update(role="generator", id="fixture-generator")
    return path


def test_exact_private_context_safe_public_request_and_lineage(package, context):
    from audio_post.private_context import (
        prepare_context,
        project_request,
        verify_private_context,
    )

    path = install(package, context)
    data, directory, manifest = package
    payload, digest = prepare_context(context)
    assert payload == path.read_bytes() == canonical(context)
    assert digest == path.stem
    assert json.loads(payload)["captured_request"] == context["captured_request"]
    public = project_request(context, TAKE)
    assert public == manifest["request"]
    public["params"]["duration_s"] = 99
    assert context["captured_request"]["params"]["duration_s"] == 3
    assert verify_private_context(manifest, data) == {"valid": True}
    assert verify_manifest(manifest, directory) == {"valid": True, "outputs": 1}
    encoded = json.dumps(manifest)
    assert "Letra privada" not in encoded and "estilo privado" not in encoded
    assert "manifest_context_sha256" not in manifest and "preparation" not in manifest


@pytest.mark.parametrize(
    "field",
    [
        "song",
        "subject",
        "kind",
        "seed",
        "index",
        "task",
        "params",
        "lineage",
        "model",
        "commercial",
        "declaration",
        "lyrics_hash",
    ],
)
def test_manifest_context_disagreement(package, context, field):
    install(package, context)
    _, directory, manifest = package
    if field == "song":
        manifest["song_id"] = "01K6Q000000000000000000009"
    elif field == "subject":
        manifest["subject"]["id"] = "01K6Q000000000000000000009"
    elif field == "kind":
        manifest["kind"] = "cli_run"
    elif field in {"seed", "task"}:
        manifest["request"][field] = 99 if field == "seed" else "music.instrumental"
    elif field == "index":
        manifest["request"]["variant_index"] = 1
    elif field == "params":
        manifest["request"]["params"]["duration_s"] = 9
    elif field == "lineage":
        manifest["lineage"]["derivation"] = "original"
    elif field == "model":
        manifest["models"][0]["id"] = "other"
    elif field == "commercial":
        manifest["models"][0]["commercial_use"] = False
    elif field == "declaration":
        manifest["request"]["lyrics_declaration"] = "own"
    else:
        manifest["request"]["lyrics_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(manifest, directory, private_context_root=package[0])


@pytest.mark.parametrize(
    "key",
    [
        "style",
        "style_prompt",
        "api-key",
        "Access_Token",
        "photos",
        "photo_data",
        "lyrics_text",
    ],
)
def test_public_private_alias_never_accepted_or_printed(package, context, key, capsys):
    install(package, context)
    package[2]["future"] = {key: "DO-NOT-PRINT-PRIVATE-CONTENT"}
    with pytest.raises(ValueError) as caught:
        verify_manifest(package[2], package[1])
    assert "DO-NOT-PRINT" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert not capsys.readouterr().out and not capsys.readouterr().err


@pytest.mark.parametrize(
    "mutation", ["content", "hardlink", "symlink", "directory", "size", "rename"]
)
def test_file_mutation_and_aliases(package, context, mutation, monkeypatch):
    from audio_post import private_context as module

    path = install(package, context)
    if mutation == "content":
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "hardlink":
        import os

        os.link(path, path.parent / "alias.json")
    elif mutation == "symlink":
        original = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda p: p == path or original(p))
    elif mutation == "directory":
        path.unlink()
        path.mkdir()
    elif mutation == "size":
        monkeypatch.setattr(module, "MAX_CONTEXT_BYTES", 100)
    else:
        real_fstat = module.os.fstat
        calls = 0

        def replace(descriptor):
            nonlocal calls
            calls += 1
            result = real_fstat(descriptor)
            if calls == 2:
                payload = path.read_bytes()
                path.unlink()
                path.write_bytes(payload)
            return result

        monkeypatch.setattr(module.os, "fstat", replace)
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(package[2], package[1])


def test_explicit_root_required_for_other_layouts(package, context):
    install(package, context)
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(package[2], package[0])
    assert verify_manifest(package[2], package[1], private_context_root=package[0])[
        "valid"
    ]


@pytest.mark.parametrize(
    "payload_change", ["noncanonical", "duplicate", "nan", "extra", "request_hash"]
)
def test_closed_finite_canonical_receipt(package, context, payload_change):
    payload = canonical(context)
    if payload_change == "noncanonical":
        payload += b"\n"
    elif payload_change == "duplicate":
        payload = payload.replace(
            b'{"captured_request":', b'{"version":1,"captured_request":', 1
        )
    elif payload_change == "nan":
        payload = payload.replace(b'"duration_s":3', b'"duration_s":NaN')
    elif payload_change == "extra":
        context["extra"] = "forbidden"
        payload = canonical(context)
    else:
        context["winning_request_sha256"] = "0" * 64
        payload = canonical(context)
    install(package, context, payload)
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(package[2], package[1])


@pytest.mark.parametrize(
    "mutation",
    [
        "proof_missing",
        "proof_hash",
        "proof_declaration",
        "take_lyrics",
        "take_extra",
        "request_extra",
        "input_extra",
        "secret",
        "photo",
        "nested_style",
        "index_bool",
        "index_range",
        "duplicate_index",
        "model",
        "original_root",
        "nonfinite",
        "depth",
    ],
)
def test_invalid_private_evidence_rejected(context, mutation):
    from audio_post.private_context import prepare_context, project_request

    request, take = context["captured_request"], context["takes"][TAKE]
    if mutation == "proof_missing":
        take["lyrics"] = None
    elif mutation == "proof_hash":
        take["lyrics"]["sha256"] = "0" * 64
    elif mutation == "proof_declaration":
        take["lyrics"]["declaration"] = "invented"
    elif mutation == "take_lyrics":
        take["params"]["lyrics"] = "different"
    elif mutation == "take_extra":
        take["extra"] = 1
    elif mutation == "request_extra":
        request["extra"] = 1
    elif mutation == "input_extra":
        request["inputs"] = [
            {
                "role": "source",
                "path": "uploads/x.wav",
                "media_type": "audio/wav",
                "sha256": "a" * 64,
                "extra": 1,
            }
        ]
    elif mutation in {"secret", "photo", "nested_style"}:
        request["params"]["nested"] = {
            "api_key"
            if mutation == "secret"
            else "photos"
            if mutation == "photo"
            else "style": "private"
        }
    elif mutation == "index_bool":
        take["output_index"] = True
    elif mutation == "index_range":
        take["output_index"] = 3
    elif mutation == "duplicate_index":
        context["takes"]["01K6Q000000000000000000006"] = copy.deepcopy(take)
    elif mutation == "model":
        take["model_id"] = "other"
    elif mutation == "original_root":
        take["lineage"]["derivation"] = "original"
    elif mutation == "nonfinite":
        request["params"]["duration_s"] = float("inf")
    else:
        nested = request["params"]
        for _ in range(22):
            nested["nested"] = {}
            nested = nested["nested"]
    if mutation != "nonfinite":
        context["winning_request_sha256"] = hashlib.sha256(
            canonical(request)
        ).hexdigest()
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        project_request(
            context, TAKE
        ) if mutation == "nested_style" else prepare_context(context)


def test_instrumental_null_proof_and_legacy(package, context):
    from audio_post.private_context import prepare_context, project_request

    request = context["captured_request"]
    request["task"] = "music.instrumental"
    request["params"].pop("lyrics")
    take = context["takes"][TAKE]
    take["params"].pop("lyrics")
    take["lyrics"] = None
    context["winning_request_sha256"] = hashlib.sha256(canonical(request)).hexdigest()
    assert prepare_context(context)[0] == canonical(context)
    public = project_request(context, TAKE)
    assert "lyrics_sha256" not in public and "lyrics_declaration" not in public
    manifest = package[2]
    manifest.pop("private_context")
    assert verify_manifest(manifest, package[1])["valid"]


def test_windows_stat_ctime_domains_preserve_each_api_identity(
    package, context, monkeypatch
):
    import os
    from types import SimpleNamespace

    from audio_post import private_context as module

    if os.name != "nt":
        pytest.skip("Windows stat API domains")
    install(package, context)
    original = module.os.fstat

    def fd_metadata(descriptor):
        actual = original(descriptor)
        values = {
            name: getattr(actual, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        }
        values["st_ctime_ns"] += 1
        return SimpleNamespace(**values)

    monkeypatch.setattr(module.os, "fstat", fd_metadata)
    assert verify_manifest(package[2], package[1])["valid"]


def test_fd_ctime_change_is_rejected(package, context, monkeypatch):
    from types import SimpleNamespace

    from audio_post import private_context as module

    path = install(package, context)
    initial_ctime = path.lstat().st_ctime_ns
    original = module.os.fstat
    calls = 0

    def fd_metadata(descriptor):
        nonlocal calls
        calls += 1
        actual = original(descriptor)
        values = {
            name: getattr(actual, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        }
        values["st_ctime_ns"] = initial_ctime + (calls > 1)
        return SimpleNamespace(**values)

    monkeypatch.setattr(module.os, "fstat", fd_metadata)
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(package[2], package[1])


def test_schema_errors_do_not_echo_content(package):
    package[2]["private_context"]["sha256"] = "DO-NOT-PRINT-PRIVATE-CONTENT"
    with pytest.raises(ValueError) as caught:
        verify_manifest(package[2], package[1])
    assert str(caught.value) == "MANIFEST_SCHEMA"


def test_public_json_types_must_match_private_request(package, context):
    context["captured_request"]["params"]["guidance"] = 1
    context["winning_request_sha256"] = hashlib.sha256(
        canonical(context["captured_request"])
    ).hexdigest()
    install(package, context)
    package[2]["request"]["params"]["guidance"] = True
    with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
        verify_manifest(package[2], package[1])


@pytest.mark.parametrize(
    "recorded,public,valid",
    [
        (True, True, True),
        (False, False, True),
        (True, 1, False),
        (True, 1.0, False),
        (False, 0, False),
        (False, 0.0, False),
    ],
)
def test_direct_verifier_commercial_correspondence_is_typed(
    package, context, recorded, public, valid
):
    from audio_post.private_context import verify_private_context

    context["takes"][TAKE]["commercial_use"] = recorded
    install(package, context)
    package[2]["models"][0]["commercial_use"] = public
    if valid:
        assert verify_private_context(package[2], package[0]) == {"valid": True}
    else:
        with pytest.raises(ValueError, match="PRIVATE_CONTEXT"):
            verify_private_context(package[2], package[0])


def _remove_owned_fifo(path, directory_fd, owned_identity):
    import os
    import stat

    info = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
    identity = [info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_ctime_ns]
    if not stat.S_ISFIFO(info.st_mode) or identity != owned_identity:
        raise ValueError("FIFO fixture identity changed; no cleanup")
    os.unlink(path.name, dir_fd=directory_fd)


def test_raced_fifo_cannot_block_private_context_read(package, context):
    import os
    import subprocess
    import sys
    import time
    from datetime import datetime, timezone

    if not hasattr(os, "mkfifo"):
        pytest.skip("Native FIFO requires POSIX; Windows simulation is separate")
    path = install(package, context)
    code = r"""
import json,os,sys
from pathlib import Path
from audio_post import private_context as module
root,digest=Path(sys.argv[1]),sys.argv[2]
target=root/'private-contexts'/f'{digest}.json'
real_open=module.os.open
def swapped_open(path,flags,*args,**kwargs):
    assert Path(path)==target
    target.unlink()
    os.mkfifo(target,0o600)
    info=target.lstat()
    print('FIFO_IDENTITY='+json.dumps([info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_ctime_ns]),flush=True)
    print('FIFO_SWAPPED',flush=True)
    return real_open(path,flags,*args,**kwargs)
module.os.open=swapped_open
try:
    module._read(root,digest)
except ValueError:
    print('REJECTED',flush=True)
    sys.exit(0)
sys.exit(8)
"""
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat()
    argv = [sys.executable, "-B", "-c", code, str(package[0]), path.stem]
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    output = errors = ""
    child = None
    blocked = False
    try:
        child = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        try:
            output, errors = child.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            blocked = True
            child.kill()
            output, errors = child.communicate(timeout=2)
    finally:
        try:
            if child is not None:
                if child.poll() is None:
                    child.kill()
                    output, errors = child.communicate(timeout=2)
                identities = [
                    line.removeprefix("FIFO_IDENTITY=")
                    for line in output.splitlines()
                    if line.startswith("FIFO_IDENTITY=")
                ]
                if identities:
                    assert len(identities) == 1, "Ambiguous owned FIFO identity"
                    _remove_owned_fifo(path, directory_fd, json.loads(identities[0]))
        finally:
            os.close(directory_fd)
    elapsed = time.monotonic() - started
    if os.environ.get("STUDIO_FIFO_EVIDENCE"):
        Path(os.environ["STUDIO_FIFO_EVIDENCE"]).write_text(
            json.dumps(
                {
                    "argv": argv,
                    "pid": child.pid,
                    "started_utc": started_utc,
                    "finished_utc": datetime.now(timezone.utc).isoformat(),
                    "elapsed_s": elapsed,
                    "deadline_s": 3,
                    "blocked": blocked,
                    "killed_after_deadline": blocked,
                    "reaped": child.poll() is not None,
                    "exit_code": child.returncode,
                    "stdout": output,
                    "stderr": errors,
                },
                indent=2,
            )
        )
    assert "FIFO_SWAPPED" in output, errors
    assert not blocked, (
        f"owned FIFO child {child.pid} blocked for {elapsed:.3f}s; killed and reaped"
    )
    assert child.returncode == 0 and "REJECTED" in output, errors


def test_windows_simulated_raced_fifo_open_is_bounded(package, context, monkeypatch):
    import threading

    from audio_post import private_context as module

    path = install(package, context)
    release = threading.Event()
    reached = threading.Event()
    original = module.os.open
    results = []
    nonblocking = getattr(module.os, "O_NONBLOCK", 2048)
    monkeypatch.setattr(module.os, "O_NONBLOCK", nonblocking, raising=False)

    def fifo_open(name, flags, *args, **kwargs):
        if Path(name) == path:
            reached.set()
            if not flags & nonblocking:
                assert release.wait(3), "simulation cleanup deadline"
            raise OSError("simulated FIFO open")
        return original(name, flags, *args, **kwargs)

    def verify():
        try:
            module.verify_private_context(package[2], package[0])
        except ValueError:
            results.append("rejected")

    monkeypatch.setattr(module.os, "open", fifo_open)
    child = threading.Thread(target=verify)
    child.start()
    try:
        assert reached.wait(1), "simulation did not reach open"
        child.join(timeout=0.25)
        blocked = child.is_alive()
    finally:
        release.set()
        child.join(timeout=2)
    assert not child.is_alive(), "owned simulation thread cleanup failed"
    assert not blocked, "simulated FIFO open blocked before regular-file validation"
    assert results == ["rejected"]


@pytest.mark.parametrize("replacement", ["owned", "identity", "regular", "symlink"])
def test_fifo_fixture_cleanup_preserves_foreign_entries(tmp_path, replacement):
    import os

    if not hasattr(os, "mkfifo"):
        pytest.skip("Native FIFO requires POSIX")
    path = tmp_path / "owned.fifo"
    os.mkfifo(path, 0o600)
    info = path.lstat()
    identity = [info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_ctime_ns]
    directory_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if replacement == "identity":
            identity[1] += 1
        elif replacement in ("regular", "symlink"):
            path.unlink()
            if replacement == "regular":
                path.write_text("foreign witness", encoding="utf-8")
            else:
                path.symlink_to("absent-foreign-witness")
        before = path.lstat()
        if replacement == "owned":
            _remove_owned_fifo(path, directory_fd, identity)
            assert not path.exists()
        else:
            with pytest.raises(ValueError, match="FIFO fixture identity changed"):
                _remove_owned_fifo(path, directory_fd, identity)
            after = path.lstat()
            assert (after.st_dev, after.st_ino, after.st_mode, after.st_ctime_ns) == (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_ctime_ns,
            )
            if replacement == "regular":
                assert path.read_text(encoding="utf-8") == "foreign witness"
            elif replacement == "symlink":
                assert path.readlink() == Path("absent-foreign-witness")
    finally:
        os.close(directory_fd)
        # Only this test creates/replaces the witness; release its own fixture.
        path.unlink(missing_ok=True)
