"""Contexto web selectivo con herramientas y archivos oficiales reales."""

import json
import shutil
from pathlib import Path

import pytest

from scripts import fetch_web_dependencies as deps
from scripts import web_build_inputs as inputs

PROJECT = Path(__file__).resolve().parents[1]
ARCHIVES = PROJECT / deps.ARCHIVE_ROOT


@pytest.fixture(scope="session", autouse=True)
def prepared_inputs():
    try:
        deps.check(PROJECT)
        linux = json.loads(
            deps.read_file(PROJECT, PROJECT / "tools/web-linux.lock.json")
        )
        tools = json.loads(deps.read_file(PROJECT, PROJECT / "tools/tools.lock.json"))
        inputs.tool_files(PROJECT, linux, tools)
    except (deps.InputError, OSError) as exc:
        pytest.fail(
            "Prerrequisito: preparar y verificar los 609 tgz con "
            "scripts/fetch_web_dependencies.py --import-local <directorio-local> / --check "
            "y pnpm 9.12.0 con scripts/fetch_web_tools.py --check. "
            "Sin búsqueda de cachés ni adquisición automática. "
            f"Detalle: {exc}",
            pytrace=False,
        )


@pytest.fixture
def web_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    for name in inputs.REQUIRED:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(deps.read_file(PROJECT, PROJECT / name))
    for name in inputs.WEB_DIRS:
        directory = PROJECT / "apps/web" / name
        if name == "public" and not directory.exists():
            continue
        (root / "apps/web" / name).mkdir(parents=True, exist_ok=True)
        allowed = (
            inputs.PUBLIC_EXTENSIONS if name == "public" else inputs.SOURCE_EXTENSIONS
        )
        for source in inputs.walk(PROJECT, directory):
            if source.suffix in allowed:
                target = root / source.relative_to(PROJECT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(deps.read_file(PROJECT, source))
    for source in inputs.walk(PROJECT, PROJECT / "packages/contracts"):
        if source.suffix == ".json":
            target = root / source.relative_to(PROJECT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(deps.read_file(PROJECT, source))
    linux = json.loads(deps.read_file(PROJECT, PROJECT / "tools/web-linux.lock.json"))
    tools = json.loads(deps.read_file(PROJECT, PROJECT / "tools/tools.lock.json"))
    files, _ = inputs.tool_files(PROJECT, linux, tools)
    for source, pin in files.items():
        data = deps.read_file(PROJECT, source)
        deps.verified(data, pin)
        target = root / source.relative_to(PROJECT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return root


def test_web_repo_without_historical_cache(tmp_path, monkeypatch):
    monkeypatch.setitem(
        web_repo.__wrapped__.__globals__, "COPIES", tmp_path / "absent-history"
    )
    root = web_repo.__wrapped__(tmp_path)
    for name in inputs.REQUIRED:
        assert (root / name).read_bytes() == (PROJECT / name).read_bytes()
    for name in inputs.WEB_DIRS:
        if name == "public" and not (PROJECT / "apps/web" / name).exists():
            assert not (root / "apps/web" / name).exists()
            continue
        for source in inputs.walk(PROJECT, PROJECT / "apps/web" / name):
            allowed = (
                inputs.PUBLIC_EXTENSIONS
                if name == "public"
                else inputs.SOURCE_EXTENSIONS
            )
            if source.suffix in allowed:
                assert (
                    root / source.relative_to(PROJECT)
                ).read_bytes() == source.read_bytes()
    linux = json.loads((root / "tools/web-linux.lock.json").read_text())
    tools = json.loads((root / "tools/tools.lock.json").read_text())
    assert len(inputs.tool_files(root, linux, tools)[0]) == 902


def test_context_native609_pnpm901(web_repo):
    source = web_repo / "input"
    shutil.copytree(ARCHIVES, source)
    deps.import_local(web_repo, source)
    for name in (
        ".env",
        "data/secret.wav",
        "models/weights.py",
        "node_modules/secret.js",
        "apps/web/.next/secret.js",
        "apps/web/.cache/secret.js",
        "apps/web/next.config.compiled.js",
        "apps/web/public/secret.py",
    ):
        target = web_repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"must not copy")
    destination = web_repo / ".cache/output/context"
    result = inputs.build_context(web_repo, destination)
    assert (destination / "apps/web/package.json").is_file()
    assert result["ready"] is True
    assert result["archive_count"] == 609
    assert result["pnpm_file_count"] == 901
    assert (destination / "tools/pnpm/9.12.0/dist/node_modules/.modules.yaml").is_file()
    assert (destination / "apps/web/lib/generated/api.d.ts").is_file()
    assert (destination / "packages/contracts/openapi.json").is_file()
    assert len(list((destination / "inputs/archives").glob("*.tgz"))) == 609
    manifest = json.loads((destination / "build-inputs.json").read_text())
    assert manifest == result
    assert all(
        ".env" not in name and not name.startswith(("data/", "models/", "tools/node/"))
        for name in manifest["files"]
    )
    assert not (destination / "apps/web/next.config.compiled.js").exists()
    assert not (destination / "apps/web/public/secret.py").exists()
    assert not (destination / "apps/web/.next").exists()


def test_missing_context_input_no_publication(web_repo):
    destination = web_repo / ".cache/context"
    (web_repo / "apps/web/next.config.ts").unlink()
    with pytest.raises(deps.InputError, match="MISSING_INPUT"):
        inputs.build_context(web_repo, destination)
    assert not destination.exists()


def test_existing_foreign_destination(web_repo):
    destination = web_repo / ".cache/context"
    destination.mkdir(parents=True)
    sentinel = destination / "foreign"
    sentinel.write_bytes(b"keep")
    (destination / "build-inputs.json").write_text('{"ready":true,"archive_count":609}')
    with pytest.raises(deps.InputError, match="DESTINATION_EXISTS"):
        inputs.build_context(web_repo, destination)
    assert sentinel.read_bytes() == b"keep"
    assert (
        destination / "build-inputs.json"
    ).read_text() == '{"ready":true,"archive_count":609}'


def test_pnpm_tamper_no_publication(web_repo):
    path = web_repo / "tools/pnpm/9.12.0/dist/node_modules/.modules.yaml"
    path.write_bytes(b"tampered")
    destination = web_repo / ".cache/context"
    with pytest.raises(deps.InputError, match="INTEGRITY"):
        inputs.build_context(web_repo, destination)
    assert not destination.exists()


def test_base_tools_pin_mismatch(web_repo):
    path = web_repo / "tools/web-linux.lock.json"
    lock = json.loads(path.read_text())
    lock["tools_lock_sha256"] = "0" * 64
    path.write_text(json.dumps(lock))
    with pytest.raises(deps.InputError, match="LOCK_MISMATCH"):
        inputs.build_context(web_repo, web_repo / ".cache/context")


def test_context_destination_escape(web_repo):
    with pytest.raises(deps.InputError, match="OUTSIDE_ROOT"):
        inputs.build_context(web_repo, web_repo.parent / "escape")


def test_destination_junction_before_stage(web_repo):
    import _winapi

    foreign = web_repo / "foreign"
    foreign.mkdir()
    sentinel = foreign / "sentinel"
    sentinel.write_bytes(b"keep")
    (web_repo / ".cache").mkdir()
    link = web_repo / ".cache/link"
    _winapi.CreateJunction(str(foreign), str(link))
    try:
        with pytest.raises(deps.InputError, match="UNSAFE_PATH"):
            inputs.build_context(web_repo, link / "context")
        assert sentinel.read_bytes() == b"keep"
        assert not (foreign / "context").exists()
    finally:
        link.rmdir()


def test_context_cannot_write_sources(web_repo):
    with pytest.raises(deps.InputError, match="UNSAFE_DESTINATION"):
        inputs.build_context(web_repo, web_repo / "apps/new-output")


def test_pnpm_unknown_foreign_file(web_repo):
    file = web_repo / "tools/pnpm/9.12.0/dist/foreign.js"
    file.write_bytes(b"foreign")
    with pytest.raises(deps.InputError, match="INVALID_TOOL_RECEIPT"):
        inputs.build_context(web_repo, web_repo / ".cache/context")
    assert file.read_bytes() == b"foreign"


@pytest.mark.parametrize(
    "field,value",
    [
        ("image_id", "node:latest"),
        ("platform", "windows/amd64"),
        ("pnpm_version", "9.0.0"),
    ],
)
def test_changed_linux_identity(web_repo, field, value):
    path = web_repo / "tools/web-linux.lock.json"
    lock = json.loads(path.read_text())
    lock[field] = value
    path.write_text(json.dumps(lock))
    with pytest.raises(deps.InputError, match="INVALID_"):
        inputs.build_context(web_repo, web_repo / ".cache/context")


def test_web_manifest_changed_pin(web_repo):
    path = web_repo / "apps/web/package.json"
    package = json.loads(path.read_text())
    package["dependencies"]["next"] = "latest"
    path.write_text(json.dumps(package))
    with pytest.raises(deps.InputError, match="LOCK_MISMATCH"):
        inputs.build_context(web_repo, web_repo / ".cache/context")


def test_caller_linux_identity_not_authoritative(web_repo):
    path = web_repo / "tools/web-linux.lock.json"
    lock = json.loads(path.read_text())
    lock["image_id"] = "sha256:" + "1" * 64
    lock["observed_immutable_reference"] = "node@" + lock["image_id"]
    path.write_text(json.dumps(lock))
    with pytest.raises(deps.InputError, match="LOCK_MISMATCH"):
        inputs.collect_inputs(web_repo)


def test_context_cli_finite_error(web_repo, capsys):
    assert (
        inputs.main(
            ["--root", str(web_repo), "--output", str(web_repo / ".cache/context")]
        )
        == 2
    )
    assert "MISSING_INPUT" in capsys.readouterr().err
    with pytest.raises(SystemExit) as result:
        inputs.main(
            ["--output", str(web_repo / ".cache/context"), "--execute", "docker"]
        )
    assert result.value.code == 2


def test_native_changed_input_rollback(web_repo):
    import threading
    import time

    source = web_repo / "input"
    shutil.copytree(ARCHIVES, source)
    deps.import_local(web_repo, source)
    parent = web_repo / ".cache/output"
    parent.mkdir(parents=True)
    destination = parent / "context"
    stop = threading.Event()
    changed = threading.Event()
    failure = []

    def mutate_after_birth():
        try:
            deadline = time.monotonic() + 600
            while not stop.is_set() and time.monotonic() < deadline:
                if list(parent.glob(".web-input-????????????????????????????????")):
                    try:
                        (web_repo / "package.json").write_bytes(b"changed during copy")
                    except PermissionError:
                        stop.wait(0.005)
                        continue
                    changed.set()
                    return
                stop.wait(0.005)
            failure.append("stage birth not observed")
        except OSError as exc:
            failure.append(repr(exc))

    thread = threading.Thread(target=mutate_after_birth)
    thread.start()
    try:
        with pytest.raises(deps.InputError, match="INTEGRITY"):
            inputs.build_context(web_repo, destination)
    finally:
        stop.set()
        thread.join(timeout=5)
    assert changed.is_set() and not failure and not thread.is_alive()
    assert not destination.exists()
    assert not list(parent.glob(".web-input-*"))
