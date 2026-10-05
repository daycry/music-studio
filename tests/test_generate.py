"""CLI M0 con entradas sintéticas, sin GPU ni material privado."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest
from engine_mock import descriptor

ROOT = Path(__file__).resolve().parents[1]


def module():
    path = ROOT / "scripts/generate.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("generate_cli", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def invoke(name, *args, **kwargs):
    return getattr(module(), name, lambda *a, **kw: None)(*args, **kwargs)


def test_direct_request_and_rights(tmp_path):
    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_text("[Verse]\nUna prueba sintética\n", encoding="utf-8")
    args = [
        "--lyrics",
        str(lyrics),
        "--style",
        "hip hop",
        "--duration",
        "30",
        "--language",
        "es",
        "--seed",
        "1",
        "--variants",
        "2",
        "--lyrics-declaration",
        "own",
    ]
    result = invoke("read_request", args, root=ROOT)
    assert result is not None
    assert result["params"] == {
        "lyrics": lyrics.read_bytes().decode("utf-8"),
        "style": "hip hop",
        "duration_s": 30.0,
        "language": "es",
    }
    assert result["seed"] == 1 and result["n_outputs"] == 2
    assert result["lyrics_declaration"] == "own"
    with pytest.raises(ValueError, match="LYRICS_DECLARATION_REQUIRED"):
        invoke("read_request", args[:-2], root=ROOT)


def test_mock_post_and_manifest(tmp_path, capsys):
    import json

    from audio_post import verify_manifest
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    data = tmp_path / "data"
    data.mkdir()
    config = {
        "STUDIO_ENGINE_TOKEN": "synthetic-token",
        "STUDIO_DATA_DIR": str(data),
        "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
    }
    request = {
        "task": "music.instrumental",
        "params": {"style": "synthetic", "duration_s": 3},
        "seed": 7,
        "n_outputs": 2,
        "engine": "mock",
        "lyrics_declaration": None,
        "lyrics_sha256": None,
    }
    with TestClient(
        create_mock_app(token="synthetic-token", data_dir=data, stage_delay_ms=0)
    ) as client:
        result = invoke("generate", request, config=config, root=ROOT, client=client)
        assert result is not None
        assert len(result) == 2
        assert (
            client.get(
                "/v1/health", headers={"X-Studio-Engine-Token": "synthetic-token"}
            ).json()["loaded"]
            is None
        )
    for index, dest in enumerate(result):
        assert {p.name for p in dest.iterdir()} == {
            "master.flac",
            "listen.mp3",
            "peaks.json",
            "manifest.json",
        }
        manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["kind"] == "cli_run"
        assert manifest["request"]["seed"] == 7 + index
        assert manifest["models"][0]["revision"] == "synthetic-v1"
        assert verify_manifest(dest / "manifest.json", dest)["valid"]
    spec = importlib.util.spec_from_file_location(
        "verify_cli", ROOT / "scripts/verify_manifest.py"
    )
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    assert verifier.main([str(data / "cli")]) == 0
    output = capsys.readouterr().out
    assert "generating" in output
    assert "all valid" in output


def test_brief_catalog(tmp_path):
    directory = tmp_path / "eval/briefs"
    directory.mkdir(parents=True)
    (directory / "briefs.yaml").write_text(
        "version: 1\nbriefs:\n  B-99:\n    style: synthetic folk\n    duration_s: 30\n"
        "    language: es\n    bpm: 84\n    lyrics_declaration: null\n",
        encoding="utf-8",
    )
    (directory / "B-99.txt").write_text("[Verse]\nPrueba\n", encoding="utf-8")
    result = invoke(
        "read_request",
        ["--brief", "B-99", "--lyrics-declaration", "own"],
        root=tmp_path,
    )
    assert result["params"]["bpm"] == 84
    assert result["params"]["duration_s"] == 30
    assert result["lyrics_declaration"] == "own"
    with pytest.raises(ValueError, match="LYRICS_DECLARATION_REQUIRED"):
        invoke("read_request", ["--brief", "B-99"], root=tmp_path)
    with pytest.raises(ValueError, match="BRIEF_NOT_FOUND"):
        invoke("read_request", ["--brief", "B-00"], root=tmp_path)


def test_direct_bpm():
    result = invoke(
        "read_request",
        [
            "--task",
            "music.instrumental",
            "--style",
            "synthetic",
            "--duration",
            "30",
            "--bpm",
            "94",
        ],
    )
    assert result["params"]["bpm"] == 94
    with pytest.raises(ValueError, match="INVALID_PARAMS"):
        invoke(
            "read_request",
            [
                "--task",
                "music.instrumental",
                "--style",
                "synthetic",
                "--duration",
                "30",
                "--bpm",
                "301",
            ],
        )


def test_long_stage_stream_timeout(tmp_path, monkeypatch):
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    data = tmp_path / "data"
    request = {
        "task": "music.instrumental",
        "params": {"style": "@mock:fail=INTERNAL", "duration_s": 3},
        "seed": 1,
        "n_outputs": 1,
        "engine": "mock",
        "lyrics_declaration": None,
        "lyrics_sha256": None,
    }
    timeouts = []
    with TestClient(
        create_mock_app(token="synthetic", data_dir=data, stage_delay_ms=0)
    ) as client:
        stream = client.stream

        def capture(*args, **kwargs):
            timeouts.append(kwargs["timeout"])
            return stream(*args, **kwargs)

        monkeypatch.setattr(client, "stream", capture)
        with pytest.raises(ValueError, match="INTERNAL"):
            invoke(
                "generate",
                request,
                config={
                    "STUDIO_ENGINE_TOKEN": "synthetic",
                    "STUDIO_DATA_DIR": str(data),
                    "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
                },
                root=ROOT,
                client=client,
            )
        assert (
            client.get(
                "/v1/health", headers={"X-Studio-Engine-Token": "synthetic"}
            ).json()["loaded"]
            is None
        )
    assert timeouts[0] > 300


def test_song_manifest_privacy_and_rights(tmp_path, monkeypatch):
    from audio_post import verify_manifest
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_text("[Verse]\nTexto sintético privado\n", encoding="utf-8")
    data = tmp_path / "data"
    m = module()
    config = {
        "STUDIO_ENGINE_TOKEN": "synthetic",
        "STUDIO_DATA_DIR": str(data),
        "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
    }
    with TestClient(
        create_mock_app(token="synthetic", data_dir=data, stage_delay_ms=0)
    ) as client:
        request = m.read_request(
            [
                "--lyrics",
                str(lyrics),
                "--style",
                "synthetic",
                "--duration",
                "3",
                "--language",
                "es",
                "--lyrics-declaration",
                "licensed",
            ]
        )
        m.generate(request, config=config, client=client)
    manifest_path = next(data.glob("cli/*/*/manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["commercial_use"] is False
    assert manifest["inputs"][0]["rights"] == "licensed"
    assert "Texto sintético privado" not in json.dumps(manifest)
    assert manifest["request"]["lyrics_declaration"] == "licensed"
    assert verify_manifest(manifest_path, manifest_path.parent)["valid"]


@pytest.mark.parametrize(
    "argv,code",
    [
        (["--duration", "nan"], "INVALID_PARAMS"),
        (["--duration", "601"], "INVALID_PARAMS"),
        (["--duration", "0"], "INVALID_PARAMS"),
        (["--duration", "30", "--variants", "0"], "INVALID_PARAMS"),
        (["--duration", "30", "--seed", "-1"], "INVALID_PARAMS"),
        (["--duration", "30", "--lyrics", "ignored.txt"], "INSTRUMENTAL_HAS_LYRICS"),
    ],
)
def test_invalid_direct(argv, code):
    with pytest.raises(ValueError, match=code):
        invoke(
            "read_request",
            ["--task", "music.instrumental", "--style", "synthetic", *argv],
        )


@pytest.mark.parametrize(
    "catalog",
    [
        "[]",
        "version: 2\nbriefs: {}",
        "version: true\nbriefs: {}",
        "version: 1\nbriefs:\n  X:\n    style: a\n    duration_s: 3\n    language: es\n    task: []",
        "version: 1\nbriefs:\n  X:\n    style: a\n    duration_s: 3\n    language: es\n    bpm: true",
        "version: 1\nbriefs:\n  X:\n    style: a\n    duration_s: 3\n    language: es\n    lyrics_declaration: []",
        "version: [broken",
        "version: 1\nbriefs:\n  X: 3",
    ],
)
def test_invalid_catalog(tmp_path, catalog):
    folder = tmp_path / "eval/briefs"
    folder.mkdir(parents=True)
    (folder / "briefs.yaml").write_text(catalog, encoding="utf-8")
    with pytest.raises(ValueError, match="BRIEF_CATALOG_INVALID"):
        invoke("read_request", ["--brief", "X"], root=tmp_path)


def test_missing_brief_inputs(tmp_path):
    with pytest.raises(ValueError, match="BRIEF_CATALOG_INVALID"):
        invoke("read_request", ["--brief", "X"], root=tmp_path)
    folder = tmp_path / "eval/briefs"
    folder.mkdir(parents=True)
    (folder / "briefs.yaml").write_text(
        "version: 1\nbriefs:\n  X:\n    style: a\n    duration_s: 3\n    language: es\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="BRIEF_LYRICS_MISSING"):
        invoke(
            "read_request",
            ["--brief", "X", "--lyrics-declaration", "own"],
            root=tmp_path,
        )
    with pytest.raises(ValueError, match="BRIEF_ARGUMENT_CONFLICT"):
        invoke("read_request", ["--brief", "X", "--style", "changed"], root=tmp_path)
    with pytest.raises(ValueError, match="BRIEF_NOT_FOUND"):
        invoke("read_request", ["--brief", "../X"], root=tmp_path)


def test_config_and_local_paths(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "# synthetic\nSTUDIO_ENGINE_TOKEN=file-value\nIGNORED\n", encoding="utf-8"
    )
    monkeypatch.setenv("STUDIO_ENGINE_TOKEN", "environment-value")
    assert invoke("environment", tmp_path)["STUDIO_ENGINE_TOKEN"] == "environment-value"
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        invoke("confined", tmp_path.parent, tmp_path)
    config = {"STUDIO_ENGINES": "mock=http://127.0.0.1:8199"}
    assert invoke("engine_url", {}, config) == "http://127.0.0.1:8199"
    assert invoke("engine_url", {"engine": "mock"}, config) == "http://127.0.0.1:8199"
    for url in [
        "http://example.org",
        "https://localhost",
        "http://secret@localhost",
        "http://localhost/?token=secret",
    ]:
        with pytest.raises(ValueError, match="LOCAL_ENGINE_REQUIRED"):
            invoke("engine_url", {"engine": url}, config)


def synthetic_request():
    return {
        "task": "music.instrumental",
        "params": {"style": "synthetic", "duration_s": 3},
        "seed": 1,
        "n_outputs": 1,
        "engine": "mock",
        "lyrics_declaration": None,
        "lyrics_sha256": None,
    }


def fake_transport(data, case):
    calls = []
    state = "idle"
    loaded = False

    def handle(req):
        nonlocal state, loaded
        calls.append((req.method, req.url.path))
        assert req.headers["X-Studio-Engine-Token"] == "synthetic"
        if req.url.path == "/v1/health":
            return httpx.Response(
                200,
                json={
                    "engine_id": "mock",
                    "engine_version": "1",
                    "image_digest": "synthetic",
                    "state": "busy"
                    if case == "busy"
                    else (state if state in {"loading", "busy"} else "idle"),
                    "loaded": {"model_id": "mock", "mode": "cpu"} if loaded else None,
                    "gpu": {"total_mb": 0, "free_mb": 0, "cap_mb": 0},
                },
            )
        if req.url.path == "/v1/models":
            model = descriptor().model_dump(mode="json")
            if case == "unverified":
                model["tasks"]["music.instrumental"]["verified"] = False
            if case == "no_modes":
                model["modes"] = []
            return httpx.Response(200, json=[model])
        if req.url.path == "/v1/jobs":
            job = json.loads(req.content)
            if case != "reject":
                state, loaded = "loading", True
            return httpx.Response(
                409 if case == "reject" else 202,
                json={
                    "job_id": "different" if case == "job_mismatch" else job["job_id"]
                },
            )
        if req.url.path.endswith("/events"):
            job_id = req.url.path.split("/")[-2]
            source = data / f"tmp/{job_id}/output.wav"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"synthetic")
            import hashlib

            artifact = {
                "output_index": 0,
                "path": f"tmp/{job_id}/output.wav",
                "media_type": "audio/wav",
                "sha256": hashlib.sha256(b"synthetic").hexdigest(),
                "meta": {"seed": 1},
            }
            if case == "hash":
                artifact["sha256"] = "0" * 64
            if case == "seed":
                artifact["meta"]["seed"] = 2
            if case == "path":
                artifact["path"] = "tmp/other/output.wav"
            event = {
                "seq": 1,
                "job_id": job_id,
                "type": "done",
                "data": {
                    "artifacts": [] if case == "outputs" else [artifact],
                    "telemetry": {"mode": "cpu", "model_revision": "synthetic-v1"},
                },
            }
            if case == "cancelled":
                event["type"] = "cancelled"
            if case == "event_job":
                event["job_id"] = "00000000000000000000000000"
            if case == "interrupt":
                raise KeyboardInterrupt
            state = event["type"]
            return httpx.Response(
                401 if case == "events_http" else 200, content=json.dumps(event)
            )
        if req.method == "DELETE":
            state = "cancelled"
            return httpx.Response(200, json={"job_id": req.url.path.split("/")[-1]})
        if req.url.path.startswith("/v1/jobs/"):
            return httpx.Response(
                200,
                json={"job_id": req.url.path.split("/")[-1], "state": state, "seq": 1},
            )
        if req.url.path == "/v1/unload":
            loaded = False
        return httpx.Response(200, json={"freed_mb": 0})

    return httpx.MockTransport(handle), calls


@pytest.mark.parametrize(
    "case,code",
    [
        ("busy", "ENGINE_BUSY"),
        ("reject", "ENGINE_HTTP_409"),
        ("unverified", "CAPABILITY_UNAVAILABLE"),
        ("no_modes", "CAPABILITY_UNAVAILABLE"),
        ("job_mismatch", "ENGINE_JOB_MISMATCH"),
        ("hash", "HASH_MISMATCH"),
        ("seed", "ENGINE_SEED_MISMATCH"),
        ("path", "ENGINE_ARTIFACT_INVALID"),
        ("outputs", "ENGINE_OUTPUTS_INVALID"),
        ("cancelled", "CANCELLED"),
        ("event_job", "ENGINE_EVENT_INVALID"),
        ("events_http", "ENGINE_HTTP_401"),
    ],
)
def test_engine_errors(tmp_path, case, code):
    data = tmp_path / "data"
    transport, calls = fake_transport(data, case)
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match=code),
    ):
        invoke(
            "generate",
            synthetic_request(),
            config={
                "STUDIO_ENGINE_TOKEN": "synthetic",
                "STUDIO_DATA_DIR": str(data),
                "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
            },
            client=client,
        )
    if case in {"busy", "reject", "unverified", "no_modes"}:
        assert ("POST", "/v1/unload") not in calls
    else:
        assert ("POST", "/v1/unload") in calls
    assert not list(data.glob("cli/*/*/manifest.json"))


def test_main_errors_are_private(tmp_path, monkeypatch, capsys):
    m = module()
    monkeypatch.setattr(m, "read_request", lambda argv: synthetic_request())
    monkeypatch.setattr(m, "environment", dict)
    assert m.main([]) == 1
    assert "ENGINE_TOKEN_REQUIRED" in capsys.readouterr().err

    def fail(*a, **kw):
        raise OSError("private-file-path and secret")

    monkeypatch.setattr(m, "generate", fail)
    assert m.main([]) == 1
    assert "private-file-path" not in capsys.readouterr().err

    def interrupt(*a, **kw):
        raise KeyboardInterrupt

    monkeypatch.setattr(m, "generate", interrupt)
    assert m.main([]) == 130


def test_interrupt_cancels_and_unloads(tmp_path):
    data = tmp_path / "data"
    transport, calls = fake_transport(data, "interrupt")
    with httpx.Client(transport=transport) as client, pytest.raises(KeyboardInterrupt):
        invoke(
            "generate",
            synthetic_request(),
            config={
                "STUDIO_ENGINE_TOKEN": "synthetic",
                "STUDIO_DATA_DIR": str(data),
                "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
            },
            client=client,
        )
    assert any(method == "DELETE" for method, path in calls)
    assert ("POST", "/v1/unload") in calls


def test_post_failure_does_not_publish_partial(tmp_path, monkeypatch):
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    data = tmp_path / "data"
    m = module()
    request = synthetic_request()
    request["n_outputs"] = 2
    real_process = m.process_audio
    count = 0

    def fail_second(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            raise ValueError("AUDIO_TARGET_UNREACHABLE")
        return real_process(*args, **kwargs)

    monkeypatch.setattr(m, "process_audio", fail_second)
    with (
        TestClient(
            create_mock_app(token="synthetic", data_dir=data, stage_delay_ms=0)
        ) as client,
        pytest.raises(ValueError, match="AUDIO_TARGET_UNREACHABLE"),
    ):
        m.generate(
            request,
            config={
                "STUDIO_ENGINE_TOKEN": "synthetic",
                "STUDIO_DATA_DIR": str(data),
                "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
            },
            client=client,
        )
    assert not list(data.glob("cli/*/*"))


def test_main_result_output(tmp_path, monkeypatch, capsys):
    m = module()
    monkeypatch.setattr(m, "read_request", lambda argv: synthetic_request())
    monkeypatch.setattr(m, "environment", dict)
    monkeypatch.setattr(m, "generate", lambda *a, **kw: [ROOT / "data/cli/synthetic"])
    assert m.main([]) == 0
    assert "data/cli/synthetic" in capsys.readouterr().out


def publication_setup(tmp_path, monkeypatch, variants=1):
    """Aísla publicación: contrato y manifiesto reales, audio sintético mínimo."""
    import hashlib

    m = module()
    data = tmp_path / "data"
    request = synthetic_request()
    request["n_outputs"] = variants
    transport, _calls = fake_transport(data, "success")
    if variants != 1:
        # Keep the protocol fixture's output count independent of audio encoding.
        original = transport.handle_request

        def outputs(req):
            response = original(req)
            if req.url.path.endswith("/events"):
                event = json.loads(response.content)
                artifact = event["data"]["artifacts"][0]
                event["data"]["artifacts"] = [
                    {**artifact, "output_index": i, "meta": {"seed": 1 + i}}
                    for i in range(variants)
                ]
                return httpx.Response(200, content=json.dumps(event))
            return response

        monkeypatch.setattr(transport, "handle_request", outputs)

    def post(source, destination, **kwargs):
        destination.mkdir()
        payload = b"synthetic publication fixture"
        (destination / "master.flac").write_bytes(payload)
        return {
            "post": {},
            "outputs": [
                {
                    "role": "master",
                    "path": "master.flac",
                    "media_type": "audio/flac",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                    "meta": {},
                }
            ],
        }

    monkeypatch.setattr(m, "process_audio", post)
    config = {
        "STUDIO_ENGINE_TOKEN": "synthetic",
        "STUDIO_DATA_DIR": str(data),
        "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
    }
    return m, request, config, transport, data


@pytest.mark.parametrize("winerror", [5, 32])
def test_publication_transient_windows_lock(tmp_path, monkeypatch, winerror):
    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    rename = Path.rename
    calls = []

    def transient(source, target):
        calls.append((source, target))
        if len(calls) == 1:
            raise OSError(13, "synthetic transient publication lock", None, winerror)
        return rename(source, target)

    monkeypatch.setattr(Path, "rename", transient)
    with httpx.Client(transport=transport) as client:
        destinations = m.generate(request, config=config, client=client)
    assert len(calls) == 2
    assert len(destinations) == 1
    assert (destinations[0] / "manifest.json").is_file()
    assert not list(data.glob("cli/*/.pending-*"))


@pytest.mark.parametrize("winerror", [5, 32])
def test_publication_persistent_lock_rolls_back_variants(
    tmp_path, monkeypatch, winerror
):
    m, request, config, transport, data = publication_setup(
        tmp_path, monkeypatch, variants=2
    )
    rename = Path.rename
    calls = []
    sleeps = []
    failure = OSError(13, "synthetic persistent publication lock", None, winerror)

    def blocked_second(source, target):
        calls.append((source, target))
        if len(calls) == 1:
            return rename(source, target)
        raise failure

    monkeypatch.setattr(Path, "rename", blocked_second)
    monkeypatch.setattr(m.time, "sleep", sleeps.append)
    with httpx.Client(transport=transport) as client, pytest.raises(OSError) as raised:
        m.generate(request, config=config, client=client)
    assert raised.value is failure
    assert len(calls) == 6
    assert sleeps == [0.1, 0.2, 0.4, 0.8]
    assert not list(data.glob("cli/*/*"))


def test_publication_cleanup_keeps_original_error(tmp_path, monkeypatch):
    m, request, config, transport, data = publication_setup(tmp_path, monkeypatch)
    failure = OSError(13, "synthetic persistent publication lock", None, 5)
    cleanup = m.shutil.rmtree

    def denied(*args):
        raise failure

    def cleanup_denied(path):
        if path.name.startswith(".pending-"):
            raise OSError("synthetic staging cleanup denial")
        return cleanup(path)

    monkeypatch.setattr(Path, "rename", denied)
    monkeypatch.setattr(m.time, "sleep", lambda delay: None)
    monkeypatch.setattr(m.shutil, "rmtree", cleanup_denied)
    with httpx.Client(transport=transport) as client, pytest.raises(OSError) as raised:
        m.generate(request, config=config, client=client)
    assert raised.value is failure
    assert "PUBLICATION_CLEANUP_FAILED" in failure.__notes__
    monkeypatch.setattr(m.shutil, "rmtree", cleanup)
    cleanup(data)


@pytest.mark.parametrize("winerror", [None, 2, 3, 80])
def test_publication_other_errors_not_retried(tmp_path, monkeypatch, winerror):
    m = module()
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    calls = []
    failure = OSError(13, "synthetic non-transient failure", None, winerror)

    def fail(*args):
        calls.append(args)
        raise failure

    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(OSError) as raised:
        m.publish_directory(source, destination)
    assert raised.value is failure
    assert len(calls) == 1


def test_publication_unix_not_retried(tmp_path, monkeypatch):
    from types import SimpleNamespace

    m = module()
    source = tmp_path / "source"
    source.mkdir()
    calls = []

    def fail(*args):
        calls.append(args)
        raise OSError(13, "synthetic denied", None, 5)

    monkeypatch.setattr(m, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(OSError):
        m.publish_directory(source, tmp_path / "destination")
    assert len(calls) == 1


@pytest.mark.parametrize("appears_on_retry", [False, True])
def test_publication_never_overwrites_existing(tmp_path, monkeypatch, appears_on_retry):
    m = module()
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    sentinel = destination / "existing.txt"
    calls = []

    def create_destination():
        destination.mkdir()
        sentinel.write_bytes(b"existing data")

    def denied(*args):
        calls.append(args)
        raise OSError(13, "synthetic lock", None, 32)

    if appears_on_retry:
        monkeypatch.setattr(m.time, "sleep", lambda delay: create_destination())
    else:
        create_destination()
    monkeypatch.setattr(Path, "rename", denied)
    with pytest.raises(FileExistsError, match="PUBLICATION_DESTINATION_EXISTS"):
        m.publish_directory(source, destination)
    assert sentinel.read_bytes() == b"existing data"
    assert len(calls) == int(appears_on_retry)


def test_ctrl_c_during_loading_waits_for_unload(tmp_path, monkeypatch, capsys):
    from engine_mock import create_mock_app
    from fastapi.testclient import TestClient

    m = module()
    data = tmp_path / "data"
    config = {
        "STUDIO_ENGINE_TOKEN": "synthetic",
        "STUDIO_DATA_DIR": str(data),
        "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
    }
    monkeypatch.setattr(m, "read_request", lambda argv: synthetic_request())
    monkeypatch.setattr(m, "environment", lambda: config)
    original_generate = m.generate
    with TestClient(
        create_mock_app(token="synthetic", data_dir=data, stage_delay_ms=1000)
    ) as client:

        def interrupt(*args, **kwargs):
            raise KeyboardInterrupt("synthetic private interruption")

        monkeypatch.setattr(client, "stream", interrupt)
        monkeypatch.setattr(
            m, "generate", lambda req, **kw: original_generate(req, **kw, client=client)
        )
        assert m.main([]) == 130
        health = client.get(
            "/v1/health", headers={"X-Studio-Engine-Token": "synthetic"}
        ).json()
        assert health["state"] == "idle" and health["loaded"] is None
    stderr = capsys.readouterr().err
    assert "Generación cancelada" in stderr
    assert "synthetic private interruption" not in stderr


@pytest.mark.parametrize("case", ["cancel_transport", "unload_http", "missing_job"])
@pytest.mark.parametrize("primary_type", [KeyboardInterrupt, ValueError])
def test_cleanup_failure_preserves_primary(
    tmp_path, monkeypatch, capsys, case, primary_type
):
    m = module()
    data = tmp_path / "data"
    transport, calls = fake_transport(data, "interrupt")
    base = transport.handle_request
    primary = primary_type("private primary detail")

    def responses(req):
        if req.url.path.endswith("/events"):
            # Let the original fixture establish its accepted job state.
            raise primary
        if case == "cancel_transport" and req.method == "DELETE":
            raise httpx.ReadTimeout("private token and path", request=req)
        if case == "unload_http" and req.url.path == "/v1/unload":
            return httpx.Response(500, json={"private": "token"})
        if case == "missing_job" and req.url.path.startswith("/v1/jobs/"):
            return httpx.Response(404)
        return base(req)

    monkeypatch.setattr(transport, "handle_request", responses)
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(primary_type) as raised,
    ):
        m.generate(
            synthetic_request(),
            config={
                "STUDIO_ENGINE_TOKEN": "synthetic",
                "STUDIO_DATA_DIR": str(data),
                "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
            },
            client=client,
        )
    assert raised.value is primary
    assert "ENGINE_CLEANUP_UNCONFIRMED" in primary.__notes__
    stderr = capsys.readouterr().err
    assert "ENGINE_CLEANUP_UNCONFIRMED" in stderr
    assert "private" not in stderr and "token" not in stderr
    if case == "missing_job":
        assert not any(
            method in {"DELETE", "POST"} and path != "/v1/jobs"
            for method, path in calls
        )


def cleanup_clock_fixture(
    monkeypatch,
    *,
    finish_after,
    foreign_job=False,
    foreign_model=False,
    conflict_once=False,
    stale_unload=False,
):
    from types import SimpleNamespace

    m = module()
    clock = [0.0]
    calls = []
    unloaded = False
    conflict = conflict_once

    def sleep(seconds):
        clock[0] += seconds

    monkeypatch.setattr(
        m, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep)
    )
    job_id = "00000000000000000000000001"

    def request(method, path, **kwargs):
        nonlocal unloaded, conflict
        calls.append((method, path, kwargs.get("timeout")))
        if path.startswith("/v1/jobs/"):
            if method == "DELETE":
                return {"job_id": job_id}
            return {
                "job_id": job_id,
                "state": "cancelled" if clock[0] >= finish_after else "loading",
                "seq": 1,
            }
        if path == "/v1/health":
            return {
                "engine_id": "mock",
                "engine_version": "1",
                "image_digest": "synthetic",
                "state": "idle" if clock[0] >= finish_after else "loading",
                "job_id": "00000000000000000000000002"
                if foreign_job
                else (None if clock[0] >= finish_after else job_id),
                "loaded": None
                if unloaded and not stale_unload
                else {"model_id": "other" if foreign_model else "mock", "mode": "cpu"},
                "gpu": {"total_mb": 0, "free_mb": 0, "cap_mb": 0},
            }
        if path == "/v1/unload":
            if conflict:
                conflict = False
                raise ValueError("ENGINE_HTTP_409")
            unloaded = True
            return {"freed_mb": 0}
        raise AssertionError("unexpected request")

    return m, job_id, request, clock, calls


def test_cleanup_waits_beyond_ten_seconds(monkeypatch):
    m, job_id, request, clock, calls = cleanup_clock_fixture(
        monkeypatch, finish_after=20
    )
    m.finish_job(request, job_id, "mock", "cpu", cancel=True)
    assert 20 <= clock[0] < 21
    assert sum(method == "DELETE" for method, path, timeout in calls) == 1
    assert sum(path == "/v1/unload" for method, path, timeout in calls) == 1
    assert all(0 < timeout <= 5 for method, path, timeout in calls)


def test_cleanup_timeout_is_bounded(monkeypatch):
    m, job_id, request, clock, calls = cleanup_clock_fixture(
        monkeypatch, finish_after=1000
    )
    with pytest.raises(ValueError, match="ENGINE_CLEANUP_TIMEOUT"):
        m.finish_job(request, job_id, "mock", "cpu", cancel=True)
    assert clock[0] == pytest.approx(300)
    assert not any(path == "/v1/unload" for method, path, timeout in calls)


@pytest.mark.parametrize("foreign_model", [False, True])
def test_cleanup_never_unloads_foreign_work(monkeypatch, foreign_model):
    m, job_id, request, _clock, calls = cleanup_clock_fixture(
        monkeypatch,
        finish_after=0,
        foreign_job=not foreign_model,
        foreign_model=foreign_model,
    )
    with pytest.raises(ValueError, match="ENGINE_CLEANUP_FOREIGN"):
        m.finish_job(request, job_id, "mock", "cpu", cancel=True)
    assert not any(method in {"POST", "DELETE"} for method, path, timeout in calls)


def test_cleanup_rechecks_after_unload_busy(monkeypatch):
    m, job_id, request, clock, calls = cleanup_clock_fixture(
        monkeypatch, finish_after=0, conflict_once=True
    )
    m.finish_job(request, job_id, "mock", "cpu", cancel=False)
    assert sum(path == "/v1/unload" for method, path, timeout in calls) == 2
    assert clock[0] == pytest.approx(0.1)


def test_cleanup_requires_loaded_none(monkeypatch):
    m, job_id, request, _clock, calls = cleanup_clock_fixture(
        monkeypatch, finish_after=0, stale_unload=True
    )
    with pytest.raises(ValueError, match="ENGINE_UNLOAD_UNCONFIRMED"):
        m.finish_job(request, job_id, "mock", "cpu", cancel=False)
    assert sum(path == "/v1/unload" for method, path, timeout in calls) == 1


def test_generate_has_one_cleanup_budget(tmp_path, monkeypatch, capsys):
    import time
    from types import SimpleNamespace

    m = module()
    data = tmp_path / "data"
    sentinel = data / "cli/existing/keep.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"preexisting output")
    transport, _calls = fake_transport(data, "success")
    base = transport.handle_request
    unloads = []
    clock = [0.0]
    windows = []
    original_finish = m.finish_job

    def sleep(seconds):
        clock[0] += seconds

    monkeypatch.setattr(
        m,
        "time",
        SimpleNamespace(time=time.time, monotonic=lambda: clock[0], sleep=sleep),
    )

    def responses(req):
        if req.url.path == "/v1/unload":
            unloads.append(clock[0])
            return httpx.Response(409)
        return base(req)

    def finish(*args, **kwargs):
        windows.append(clock[0])
        return original_finish(*args, **kwargs)

    monkeypatch.setattr(transport, "handle_request", responses)
    monkeypatch.setattr(m, "finish_job", finish)
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match="ENGINE_CLEANUP_TIMEOUT") as raised,
    ):
        m.generate(
            synthetic_request(),
            config={
                "STUDIO_ENGINE_TOKEN": "synthetic",
                "STUDIO_DATA_DIR": str(data),
                "STUDIO_ENGINES": "mock=http://127.0.0.1:8199",
            },
            client=client,
        )
    assert clock[0] <= 300 + 1e-9
    assert windows == [0.0]
    assert unloads and max(unloads) < 300
    assert "ENGINE_CLEANUP_UNCONFIRMED" in raised.value.__notes__
    assert "ENGINE_CLEANUP_UNCONFIRMED" in capsys.readouterr().err
    assert not list(data.glob("cli/*/*/manifest.json"))
    assert sentinel.read_bytes() == b"preexisting output"
