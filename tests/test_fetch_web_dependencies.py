"""Importación opaca real, finita y local (sin extracción ni instalador)."""

import base64
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from scripts import fetch_web_dependencies as deps

PROJECT = Path(__file__).resolve().parents[1]
ARCHIVES = PROJECT / deps.ARCHIVE_ROOT


@pytest.fixture(scope="session", autouse=True)
def prepared_archives():
    try:
        deps.check(PROJECT)
    except (deps.InputError, OSError) as exc:
        pytest.fail(
            "Prerrequisito: preparar los 609 tgz oficiales con "
            "scripts/fetch_web_dependencies.py --import-local <directorio-local> "
            "y verificar con --check; no se descargan ni se buscan cachés. "
            f"Detalle: {exc}",
            pytrace=False,
        )


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    (root / "tools").mkdir(parents=True)
    for name in ("tools/web-dependencies.lock.json", "pnpm-lock.yaml"):
        target = root / name
        target.write_bytes(deps.read_file(PROJECT, PROJECT / name))
    return root


@pytest.mark.parametrize("integrity", [None, 1])
@pytest.mark.parametrize("operation", ["library", "cli"])
def test_non_string_integrity_typed_before_writes(
    repository, capsys, integrity, operation
):
    path = repository / deps.LOCK
    lock = json.loads(path.read_text())
    lock["artifacts"][0]["integrity"] = integrity
    path.write_text(json.dumps(lock))
    before = {
        p.relative_to(repository): p.read_bytes()
        for p in repository.rglob("*")
        if p.is_file()
    }
    if operation == "library":
        with pytest.raises(deps.InputError, match="INVALID_LOCK"):
            deps.import_local(repository, repository / "absent-input")
    else:
        assert (
            deps.main(
                [
                    "--root",
                    str(repository),
                    "--import-local",
                    str(repository / "absent-input"),
                ]
            )
            == 2
        )
        assert "INVALID_LOCK" in capsys.readouterr().err
    after = {
        p.relative_to(repository): p.read_bytes()
        for p in repository.rglob("*")
        if p.is_file()
    }
    assert after == before
    assert not (repository / deps.ARCHIVE_ROOT).exists()
    assert not list(repository.rglob(".web-input-*"))


def test_repository_without_historical_cache(tmp_path, monkeypatch):
    monkeypatch.setitem(
        repository.__wrapped__.__globals__, "COPIES", tmp_path / "absent-history"
    )
    root = repository.__wrapped__(tmp_path)
    for name in (deps.LOCK, "pnpm-lock.yaml"):
        assert (root / name).read_bytes() == (PROJECT / name).read_bytes()
    assert deps.load_lock(root)[0]["artifact_count"] == 609


def test_import_native609(repository):
    rows = json.loads((repository / "tools/web-dependencies.lock.json").read_text())[
        "artifacts"
    ]
    source = repository / "input"
    shutil.copytree(ARCHIVES, source)
    result = deps.import_local(repository, source)
    assert result == {"verified": 609, "published": True}
    for row in rows:
        data = (repository / row["archive_path"]).read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
        assert (
            "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()
            == row["integrity"]
        )
    assert deps.import_local(repository, source) == {
        "verified": 609,
        "published": False,
    }
    assert deps.check(repository) == {"verified": 609, "published": False}
    assert deps.main(["--root", str(repository), "--check"]) == 0
    target = repository / rows[0]["archive_path"]
    target.write_bytes(b"corrupt existing publication")
    with pytest.raises(deps.InputError, match="INTEGRITY"):
        deps.import_local(repository, source)
    assert target.read_bytes() == b"corrupt existing publication"


def test_missing_before_partial(repository, tmp_path):
    source = repository / "empty"
    source.mkdir()
    with pytest.raises(deps.InputError, match="MISSING_ARCHIVES"):
        deps.import_local(repository, source)
    assert not (repository / "tools/web-dependencies/archives").exists()


def test_unknown_preserves_foreign(repository, tmp_path):
    source = repository / "source"
    source.mkdir()
    foreign = source / "foreign.tgz"
    foreign.write_bytes(b"foreign opaque input")
    with pytest.raises(deps.InputError, match="UNKNOWN_ARCHIVE"):
        deps.import_local(repository, source)
    assert foreign.read_bytes() == b"foreign opaque input"
    assert not (repository / "tools/web-dependencies/archives").exists()


def test_source_escape(repository):
    with pytest.raises(deps.InputError, match="OUTSIDE_ROOT"):
        deps.import_local(repository, repository.parent.parent)


def test_source_hardlink(repository, tmp_path):
    source = repository / "source"
    source.mkdir()
    origin = repository / "original.tgz"
    shutil.copyfile(next(ARCHIVES.iterdir()), origin)
    os.link(origin, source / "linked.tgz")
    try:
        with pytest.raises(deps.InputError, match="UNSAFE_FILE"):
            deps.import_local(repository, source)
    finally:
        (source / "linked.tgz").unlink()


def test_changed_lock(repository):
    path = repository / "pnpm-lock.yaml"
    path.write_bytes(path.read_bytes() + b"\n# changed\n")
    with pytest.raises(deps.InputError, match="LOCK_MISMATCH"):
        deps.import_local(repository, ARCHIVES)


@pytest.mark.parametrize(
    "field,value",
    [
        ("archive_path", "../../escape.tgz"),
        ("integrity", "sha512-invalid"),
        ("sha256", "invalid"),
        ("bytes", -1),
    ],
)
def test_bad_lock(repository, field, value):
    path = repository / "tools/web-dependencies.lock.json"
    lock = json.loads(path.read_text())
    lock["artifacts"][0][field] = value
    path.write_text(json.dumps(lock))
    with pytest.raises(deps.InputError, match="INVALID_LOCK"):
        deps.import_local(repository, ARCHIVES)


def test_incomplete_existing_never_overwritten(repository):
    target = repository / "tools/web-dependencies/archives"
    target.mkdir(parents=True)
    sentinel = target / "foreign.txt"
    sentinel.write_bytes(b"keep")
    with pytest.raises(deps.InputError, match="ARCHIVE_SET"):
        deps.import_local(repository, ARCHIVES)
    assert sentinel.read_bytes() == b"keep"


def test_reserved_path(repository):
    with pytest.raises(deps.InputError, match="UNSAFE_PATH"):
        deps.import_local(repository, repository / "NUL")


def test_native_executable_identity(repository):
    file = repository / "opaque.exe"
    file.write_bytes(b"ordinary opaque bytes")
    assert deps.read_file(repository, file) == b"ordinary opaque bytes"


def test_direct_archive_selection_matches_requested_version():
    package = json.loads(deps.read_file(PROJECT, PROJECT / "apps/web/package.json"))
    direct = package["dependencies"] | package["devDependencies"]
    lock, _ = deps.load_lock(PROJECT)
    omitted = direct_archive_names(lock["artifacts"], direct)
    expected = {
        row["sha256"] + ".tgz"
        for row in lock["artifacts"]
        if direct.get(row["name"]) == row["version"]
    }
    alternatives = {
        row["sha256"] + ".tgz"
        for row in lock["artifacts"]
        if row["name"] in direct and row["version"] != direct[row["name"]]
    }
    assert alternatives
    assert len(expected) == 23
    assert omitted == expected
    assert not omitted & alternatives


def direct_archive_names(artifacts, direct):
    return {
        row["sha256"] + ".tgz"
        for row in artifacts
        if direct.get(row["name"]) == row["version"]
    }


def test_original586_missing23(repository):
    source = repository / "input"
    package = json.loads(deps.read_file(PROJECT, PROJECT / "apps/web/package.json"))
    direct = package["dependencies"] | package["devDependencies"]
    lock, _ = deps.load_lock(PROJECT)
    omitted = direct_archive_names(lock["artifacts"], direct)
    assert len(omitted) == 23
    shutil.copytree(
        ARCHIVES, source, ignore=lambda directory, names: set(names) & omitted
    )
    copied = {path.name for path in source.iterdir()}
    assert len(copied) == 586
    assert copied == {row["sha256"] + ".tgz" for row in lock["artifacts"]} - omitted
    assert all(
        (source / (row["sha256"] + ".tgz")).is_file()
        for row in lock["artifacts"]
        if row["name"] in direct and row["version"] != direct[row["name"]]
    )
    with pytest.raises(deps.InputError, match="MISSING_ARCHIVES: faltan 23"):
        deps.import_local(repository, source)
    assert not (repository / deps.ARCHIVE_ROOT).exists()


def test_atomic_publication_and_no_clobber(repository):
    destination = repository / "own/output"
    with deps.Publication(repository, destination) as publication:
        publication.write("opaque.tgz", b"opaque bytes")
        publication.publish()
    assert (destination / "opaque.tgz").read_bytes() == b"opaque bytes"
    with (
        pytest.raises(deps.InputError, match="DESTINATION_EXISTS"),
        deps.Publication(repository, destination),
    ):
        pytest.fail("clobbered existing publication")


def test_concurrent_publication_lease(repository):
    from concurrent.futures import ThreadPoolExecutor

    destination = repository / "own/output"
    with deps.Publication(repository, destination) as first:
        first.write("first", b"owner")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                lambda: deps.Publication(repository, destination).__enter__()
            )
            with pytest.raises(FileExistsError):
                future.result()
        first.publish()
    assert (destination / "first").read_bytes() == b"owner"


def test_rollback_exact_owned_files(repository):
    destination = repository / "own/output"
    with (
        pytest.raises(RuntimeError, match="abort"),
        deps.Publication(repository, destination) as publication,
    ):
        stage = publication.stage
        publication.write("nested/opaque.tgz", b"unchanged")
        raise RuntimeError("abort")
    assert not destination.exists()
    assert not stage.exists()
    assert not list(destination.parent.glob("*.lock"))


def test_stage_foreign_preserved_fail_closed(repository):
    destination = repository / "own/output"
    with (
        pytest.raises(deps.InputError, match="STAGE_CHANGED"),
        deps.Publication(repository, destination) as publication,
    ):
        publication.write("own", b"own")
        sentinel = publication.stage / "foreign"
        sentinel.write_bytes(b"foreign")
        publication.publish()
    assert sentinel.read_bytes() == b"foreign"
    assert not destination.exists()


def test_stage_integrity_tamper(repository):
    destination = repository / "own/output"
    with (
        pytest.raises(deps.InputError, match="INTEGRITY"),
        deps.Publication(repository, destination) as publication,
    ):
        publication.write("own", b"own")
        (publication.stage / "own").write_bytes(b"tamper")
        publication.publish()
    assert not destination.exists()


def test_ancestor_native_rename_denied(repository):
    ancestor = repository / "input"
    ancestor.mkdir()
    file = ancestor / "file"
    file.write_bytes(b"safe")
    with deps.ancestors(repository, file), pytest.raises(OSError):
        ancestor.rename(repository / "swapped")
    assert file.read_bytes() == b"safe"


def test_junction_before_stage_rejected(repository):
    import _winapi

    foreign = repository / "foreign"
    foreign.mkdir()
    sentinel = foreign / "sentinel"
    sentinel.write_bytes(b"foreign")
    junction = repository / "input"
    _winapi.CreateJunction(str(foreign), str(junction))
    try:
        with pytest.raises(deps.InputError, match="UNSAFE_PATH"):
            deps.import_local(repository, junction)
        assert sentinel.read_bytes() == b"foreign"
        assert not (repository / deps.ARCHIVE_ROOT).exists()
    finally:
        junction.rmdir()


@pytest.mark.parametrize(
    "name", ["a/../b", "a//b", "CON.txt", "a:stream", "a.", "a ", "/a", "a\\b"]
)
def test_portable_reserved_names(name):
    with pytest.raises(deps.InputError, match="UNSAFE_PATH"):
        deps.relative_name(name)


def test_unknown_and_duplicate_opaque_archive(repository):
    source = repository / "input"
    source.mkdir()
    origin = next(ARCHIVES.iterdir())
    shutil.copyfile(origin, source / "one.tgz")
    shutil.copyfile(origin, source / "two.tgz")
    with pytest.raises(deps.InputError, match="AMBIGUOUS_ARCHIVE"):
        deps.import_local(repository, source)
    (source / "two.tgz").rename(source / "two.txt")
    with pytest.raises(deps.InputError, match="UNKNOWN_ARCHIVE"):
        deps.import_local(repository, source)


def test_local_cli_error_and_finite_operations(repository, capsys):
    assert deps.main(["--root", str(repository), "--check"]) == 2
    assert "MISSING_INPUT" in capsys.readouterr().err
    with pytest.raises(SystemExit) as result:
        deps.main(["--root", str(repository), "--execute", "node"])
    assert result.value.code == 2


def test_sri_mismatch_even_with_correct_sha256():
    data = b"actual opaque bytes"
    row = deps.metadata(data) | {
        "integrity": "sha512-" + base64.b64encode(bytes(64)).decode()
    }
    with pytest.raises(deps.InputError, match="INTEGRITY: SRI"):
        deps.verified(data, row)


def test_source_special_directory_rejected(repository):
    source = repository / "input"
    (source / "foreign-directory").mkdir(parents=True)
    with pytest.raises(deps.InputError, match="UNSAFE_FILE"):
        deps.import_local(repository, source)


def test_root_cannot_authorize_escape():
    with pytest.raises(deps.InputError, match="OUTSIDE_ROOT"):
        deps.check(PROJECT.parent)


def test_caller_lock_cannot_mint_official_metadata(repository):
    path = repository / "tools/web-dependencies.lock.json"
    lock = json.loads(path.read_text())
    lock["artifacts"][0]["url"] = "https://caller.invalid/pretend-official.tgz"
    path.write_text(json.dumps(lock))
    with pytest.raises(deps.InputError, match="LOCK_MISMATCH"):
        deps.load_lock(repository)


def test_library_boundary_cannot_expand_repo():
    with pytest.raises(deps.InputError, match="OUTSIDE_ROOT"):
        deps.safe_path(PROJECT.parent, PROJECT.parent / "unowned-output")


def test_publication_race_preserves_new_foreign_output(repository):
    destination = repository / "own/output"
    with (
        pytest.raises(deps.InputError, match="DESTINATION_EXISTS"),
        deps.Publication(repository, destination) as publication,
    ):
        publication.write("own", b"own")
        destination.mkdir()
        sentinel = destination / "foreign"
        sentinel.write_bytes(b"keep")
        publication.publish()
    assert sentinel.read_bytes() == b"keep"
    assert not publication.stage.exists()


def test_stage_native_directory_swap_preserves_foreign(repository):
    destination = repository / "own/output"
    with (
        pytest.raises(deps.InputError, match="STAGE_CHANGED"),
        deps.Publication(repository, destination) as publication,
    ):
        publication.write("own", b"own")
        stage = publication.stage
        stage.rename(destination.parent / "saved-own-stage")
        stage.mkdir()
        sentinel = stage / "foreign"
        sentinel.write_bytes(b"keep")
        publication.publish()
    assert sentinel.read_bytes() == b"keep"
    assert not destination.exists()


def test_native_read_handle_blocks_file_write(repository):
    path = repository / "input.tgz"
    path.write_bytes(b"opaque")
    handle, close = deps._windows_handle(path, False)
    try:
        with pytest.raises(PermissionError):
            path.write_bytes(b"tampered")
    finally:
        close(handle)
    assert path.read_bytes() == b"opaque"


def test_read_limits_and_missing_input(repository):
    file = repository / "opaque"
    file.write_bytes(b"too big")
    with pytest.raises(deps.InputError, match="INPUT_LIMIT"):
        deps.read_file(repository, file, limit=1)
    with pytest.raises(deps.InputError, match="MISSING_INPUT"):
        deps.read_file(repository, repository / "missing")
    with pytest.raises(deps.InputError, match="UNSAFE_FILE"):
        deps.read_file(repository, repository)
    with pytest.raises(deps.InputError, match="UNSAFE_IO"):
        deps._windows_handle(repository / "missing", False)


@pytest.mark.parametrize("fault", ["count", "duplicate", "batch_limit"])
def test_lock_batch_bounds(repository, fault):
    path = repository / "tools/web-dependencies.lock.json"
    lock = json.loads(path.read_text())
    if fault == "count":
        lock["artifact_count"] = 610
    elif fault == "duplicate":
        lock["artifacts"][1] = lock["artifacts"][0]
    else:
        for row in lock["artifacts"]:
            row["bytes"] = deps.MAX_ARCHIVE_BYTES
    path.write_text(json.dumps(lock))
    with pytest.raises(deps.InputError, match="INVALID_LOCK"):
        deps.load_lock(repository)
