import hashlib
import io
import json
import os
import stat
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest


def api():
    return __import__("scripts.fetch_web_tools", fromlist=["*"])


def archive(tmp_path, names, kind="zip", special=None):
    path = tmp_path / ("input.zip" if kind == "zip" else "input.tgz")
    if kind == "zip":
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
            for name, data in names:
                item = zipfile.ZipInfo(name)
                if special:
                    item.create_system = 3
                    item.external_attr = special
                out.writestr(item, data)
    else:
        with tarfile.open(path, "w:gz") as out:
            for name, data in names:
                item = tarfile.TarInfo(name)
                item.size = len(data)
                if special:
                    item.type = special
                    item.linkname = "outside"
                    item.size = 0
                out.addfile(item, io.BytesIO(data) if not special else None)
    return path


@pytest.mark.parametrize("kind", ["zip", "tar"])
@pytest.mark.parametrize(
    "name",
    [
        "../evil",
        "/evil",
        "C:/evil",
        "//server/evil",
        "package/../evil",
        "package/..\\evil",
        "package/file:stream",
        "other/file",
        "package/CON",
        "package/a.",
        "package/a /b",
    ],
)
def test_reject_paths_before_writes(tmp_path, kind, name):
    path = archive(tmp_path, [("package/good", b"ok"), (name, b"bad")], kind)
    before = set(tmp_path.rglob("*"))
    with pytest.raises(ValueError):
        api().inspect_archive(path, kind, "package")
    assert set(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("kind", ["zip", "tar"])
@pytest.mark.parametrize(
    "names",
    [
        [("package/a", b"a"), ("package/a", b"b")],
        [("package/A", b"a"), ("package/a", b"b")],
        [("package/a", b"a"), ("package/a/b", b"b")],
    ],
)
def test_duplicate_collision(tmp_path, kind, names):
    path = archive(tmp_path, names, kind)
    with pytest.raises(ValueError):
        api().inspect_archive(path, kind, "package")


@pytest.mark.parametrize(
    "special",
    [
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
        tarfile.FIFOTYPE,
    ],
)
def test_tar_special_rejected(tmp_path, special):
    path = archive(tmp_path, [("package/link", b"")], "tar", special)
    with pytest.raises(ValueError):
        api().inspect_archive(path, "tar", "package")


@pytest.mark.parametrize("special", [(stat.S_IFLNK | 0o777) << 16, 0x400])
def test_zip_links_reparse(tmp_path, special):
    path = archive(tmp_path, [("package/link", b"target")], special=special)
    with pytest.raises(ValueError):
        api().inspect_archive(path, "zip", "package")


@pytest.mark.parametrize(
    "limit", [{"files": 1}, {"file_bytes": 1}, {"total_bytes": 3}, {"ratio": 0.01}]
)
def test_bombs(tmp_path, limit):
    path = archive(tmp_path, [("package/a", b"aa"), ("package/b", b"bb")])
    with pytest.raises(ValueError):
        api().inspect_archive(path, "zip", "package", **limit)


@pytest.mark.parametrize(
    "field,value",
    [
        ("bytes", 1),
        ("sha256", "0" * 64),
        ("shasum", "0" * 40),
        ("integrity", "sha512-AAAA"),
    ],
)
def test_pins(tmp_path, field, value):
    path = tmp_path / "archive"
    path.write_bytes(b"known bytes")
    pin = {
        "bytes": 11,
        "sha256": "7811f41783c32477db669f4b802ea960501ce4882bfe4e032945a05ec393bede",
    }
    pin[field] = value
    with pytest.raises(ValueError):
        api().verify_archive(path, pin)


@pytest.mark.parametrize(
    "package",
    [{"name": "other", "version": "9.12.0"}, {"name": "pnpm", "version": "1"}],
)
def test_wrong_package(tmp_path, package):
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package))
    with pytest.raises(ValueError):
        api().verify_identity(tmp_path, "pnpm")


def test_private_environment(tmp_path):
    env = api().build_environment(
        tmp_path,
        {
            "SYSTEMROOT": "C:/Windows",
            "SECRET": "private",
            "npm_config_use_node_version": "99",
            "PNPM_HOME": "outside",
        },
    )
    assert "SECRET" not in env
    assert "npm_config_use_node_version" not in env
    assert env["SYSTEMROOT"] == "C:/Windows"
    for key in [
        "PNPM_HOME",
        "npm_config_store_dir",
        "npm_config_cache",
        "npm_config_state_dir",
        "npm_config_userconfig",
        "npm_config_globalconfig",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
        "TEMP",
        "TMP",
    ]:
        assert Path(env[key]).is_relative_to(tmp_path)
    assert env["npm_config_manage_package_manager_versions"] == "false"
    assert env["npm_config_package_manager_strict"] == "true"
    assert env["npm_config_engine_strict"] == "true"


def test_package_manager_mismatch(tmp_path):
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@10.0.0"}')
    with pytest.raises(ValueError):
        api().verify_project(tmp_path)


def test_missing_check_and_foreign_preserved(tmp_path):
    module = api()
    with pytest.raises(ValueError):
        module.check_disk(tmp_path, {"file": {"sha256": "0" * 64, "bytes": 1}}, {})
    sentinel = tmp_path / "foreign"
    sentinel.write_bytes(b"preserve")
    with pytest.raises(ValueError):
        module.check_disk(tmp_path, {}, {})
    assert sentinel.read_bytes() == b"preserve"


def test_disk_tamper_extra_missing(tmp_path):
    module = api()
    path = archive(tmp_path, [("package/a", b"original")])
    manifest = module.inspect_archive(path, "zip", "package")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a").write_bytes(b"changed")
    with pytest.raises(ValueError):
        module.check_disk(dest, manifest, {})
    (dest / "a").write_bytes(b"original")
    (dest / "extra.cjs").write_bytes(b"extra")
    with pytest.raises(ValueError):
        module.check_disk(dest, manifest, {})
    (dest / "extra.cjs").unlink()
    (dest / "a").unlink()
    with pytest.raises(ValueError):
        module.check_disk(dest, manifest, {})


def test_archive_stream_hash_known(tmp_path):
    path = archive(tmp_path, [("package/a", b"abc")])
    assert (
        api().inspect_archive(path, "zip", "package")["a"]["sha256"]
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_hash_checks_all_algorithms(tmp_path):
    import base64
    import hashlib

    data = b"known bytes"
    path = tmp_path / "archive"
    path.write_bytes(data)
    pin = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "shasum": hashlib.sha1(data).hexdigest(),
        "integrity": "sha512-"
        + base64.b64encode(hashlib.sha512(data).digest()).decode(),
    }
    api().verify_archive(path, pin)
    pin["shasum"] = "0" * 40
    with pytest.raises(ValueError, match="shasum"):
        api().verify_archive(path, pin)
    pin["shasum"] = hashlib.sha1(data).hexdigest()
    pin["integrity"] = "sha512-AAAA"
    with pytest.raises(ValueError, match="integrity"):
        api().verify_archive(path, pin)


def fixture_install(tmp_path, kind="tar"):
    module = api()
    contents = [
        ("package/package.json", b'{"name":"pnpm","version":"9.12.0"}'),
        ("package/bin/pnpm.cjs", b"code"),
        ("package/dist/pnpm.cjs", b"code"),
        ("package/LICENSE", b"license"),
    ]
    path = archive(tmp_path, contents, kind)
    pin = {
        "kind": kind,
        "prefix": "package",
        "dest": "tools/pnpm/9.12.0",
        "bytes": path.stat().st_size,
        "sha256": module.digest(path),
    }
    manifest = module.inspect_archive(path, kind, "package")
    return module, path, pin, manifest


@pytest.mark.parametrize("kind", ["tar", "zip"])
def test_install_atomic_idempotent_and_manifest_tamper(tmp_path, kind):
    module, path, pin, manifest = fixture_install(tmp_path, kind)
    dest = module.extract(tmp_path, path, "pnpm", pin, manifest)
    assert (dest / "LICENSE").read_bytes() == b"license"
    assert (dest / "bin/pnpm.cjs").read_bytes() == b"code"
    assert module.extract(tmp_path, path, "pnpm", pin, manifest) == dest
    metadata = dest / module.MANIFEST
    changed = json.loads(metadata.read_text())
    (dest / "bin/pnpm.cjs").write_bytes(b"evil")
    changed["files"]["bin/pnpm.cjs"]["sha256"] = module.digest(dest / "bin/pnpm.cjs")
    metadata.write_text(json.dumps(changed))
    with pytest.raises(ValueError):
        module.extract(tmp_path, path, "pnpm", pin, manifest)
    assert (dest / "bin/pnpm.cjs").read_bytes() == b"evil"


def test_failure_cleanup_only_own_stage(tmp_path):
    module, path, pin, manifest = fixture_install(tmp_path)
    foreign = tmp_path / ".cache/fetch/foreign"
    foreign.mkdir(parents=True)
    (foreign / "sentinel").write_bytes(b"preserve")
    with pytest.raises(ValueError):
        module.extract(tmp_path, path, "node", pin, manifest)
    assert (foreign / "sentinel").read_bytes() == b"preserve"
    assert list(foreign.parent.glob("web-stage-*")) == []
    assert not (tmp_path / pin["dest"]).exists()


def test_foreign_destination_fail_closed(tmp_path):
    module, path, pin, manifest = fixture_install(tmp_path)
    dest = tmp_path / pin["dest"]
    dest.mkdir(parents=True)
    (dest / "sentinel").write_bytes(b"foreign")
    with pytest.raises(ValueError):
        module.extract(tmp_path, path, "pnpm", pin, manifest)
    assert (dest / "sentinel").read_bytes() == b"foreign"


def test_environment_foreign_config_preserved(tmp_path):
    module = api()
    config = tmp_path / ".cache/dev-cycle/m1/t08-web-portable-tools/runtime/user.npmrc"
    config.parent.mkdir(parents=True)
    config.write_text("use-node-version=99\n")
    with pytest.raises(ValueError):
        module.build_environment(tmp_path)
    assert config.read_text() == "use-node-version=99\n"


def test_symlink_ancestor_native(tmp_path):
    module = api()
    outside = tmp_path / "foreign"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Windows privilege unavailable: {exc}")
    with pytest.raises(ValueError):
        module.safe_path(link / "new", tmp_path)
    assert list(outside.iterdir()) == []


def test_outside_path_rejected(tmp_path):
    with pytest.raises(ValueError):
        api().safe_path(tmp_path.parent / "outside", tmp_path)


def test_lock_and_archive_confinement(tmp_path):
    module = api()
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    (tmp_path / "tools").mkdir()
    lock = {"schema_version": 1, "tools": module.PINS}
    (tmp_path / "tools/tools.lock.json").write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="fuera"):
        module.prepare(tmp_path, tmp_path.parent, True)
    with pytest.raises(ValueError, match="Falta archivo"):
        module.prepare(tmp_path, tmp_path, True)
    lock["tools"] = {"node": dict(module.PINS["node"], dest="outside")}
    (tmp_path / "tools/tools.lock.json").write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="pins"):
        module.prepare(tmp_path, tmp_path, True)


def test_main_missing_check_does_not_download(tmp_path, monkeypatch, capsys):
    module = api()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module, "download", lambda *a: pytest.fail("NO download on check")
    )
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/tools.lock.json").write_text(
        json.dumps({"schema_version": 1, "tools": module.PINS})
    )
    assert module.main(["--check"]) == 1
    assert "NO LISTO" in capsys.readouterr().out


def test_download_offline_bounded_and_reused(tmp_path, monkeypatch):
    module = api()

    class Response(io.BytesIO):
        pass

    monkeypatch.setattr(
        module.urllib.request, "urlopen", lambda url, timeout: Response(b"abc")
    )
    pin = {
        "url": "https://official.invalid/fixed",
        "asset": "fixture.zip",
        "bytes": 3,
        "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    }
    path = module.download(tmp_path, pin)
    assert path.read_bytes() == b"abc"
    pin["bytes"] = 1
    with pytest.raises(ValueError):
        module.download(tmp_path, pin)
    assert len(list((tmp_path / ".cache/fetch").iterdir())) == 1


def test_generated_manifest_not_trusted(tmp_path):
    module, path, pin, manifest = fixture_install(tmp_path)
    dest = module.extract(tmp_path, path, "pnpm", pin, manifest)
    (dest / module.MANIFEST).write_text("{}")
    with pytest.raises(ValueError, match="Procedencia"):
        module.check_disk(dest, manifest, pin)


def test_default_download_cache_reused(tmp_path, monkeypatch):
    module, path, pin, _manifest = fixture_install(tmp_path)
    node_path = archive(tmp_path, [("package/node.exe", b"node")], "zip")
    node_pin = dict(
        pin,
        kind="zip",
        asset="node.zip",
        dest="tools/node/22.23.2/win-x64",
        bytes=node_path.stat().st_size,
        sha256=module.digest(node_path),
    )
    pnpm_pin = dict(pin, asset="pnpm.tgz", version="9.12.0")
    monkeypatch.setattr(module, "PINS", {"node": node_pin, "pnpm": pnpm_pin})
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/tools.lock.json").write_text(
        json.dumps({"schema_version": 1, "tools": module.PINS})
    )
    calls = []

    def offline_download(root, selected):
        calls.append(selected["asset"])
        destination = (
            root / ".cache/fetch" / ("web-archive-fixture-" + selected["asset"])
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            (node_path if selected is node_pin else path).read_bytes()
        )
        return destination

    monkeypatch.setattr(module, "download", offline_download)
    module.prepare(tmp_path, None, False)
    module.prepare(tmp_path, None, False)
    assert calls == ["node.zip", "pnpm.tgz"], (
        "Debe reutilizar archivo verificado, sin descargar otra vez"
    )


def test_probe_failure_reports_actual_exit(tmp_path, monkeypatch):
    import subprocess

    module = api()
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    node = tmp_path / "tools/node/22.23.2/win-x64"
    pnpm = tmp_path / "tools/pnpm/9.12.0"
    node.mkdir(parents=True)
    (pnpm / "bin").mkdir(parents=True)
    (node / "node.exe").write_bytes(b"never execute fixture")
    (pnpm / "bin/pnpm.cjs").write_bytes(b"never execute fixture")
    prepared = {
        name: {"dest": dest, "archive": tmp_path / "not-executed", "manifest": {}}
        for name, dest in [("node", node), ("pnpm", pnpm)]
    }
    monkeypatch.setattr(module, "verify_archive", lambda *a: None)
    monkeypatch.setattr(module, "inspect_archive", lambda *a: {})
    monkeypatch.setattr(module, "check_disk", lambda *a: None)
    monkeypatch.setattr(module, "verify_identity", lambda *a: None)
    calls = []

    def failed(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 7, "wrong", "native failure")

    monkeypatch.setattr(module.subprocess, "run", failed)
    with pytest.raises(ValueError, match='"exit": 7'):
        module.probe(tmp_path, prepared)
    assert calls[0][0] == [str(node / "node.exe"), "--version"]
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["cwd"] == tmp_path


def test_probe_portable_argv_and_postcheck(tmp_path, monkeypatch):
    import subprocess

    module = api()
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    node = tmp_path / "node"
    pnpm = tmp_path / "pnpm"
    node.mkdir()
    (pnpm / "bin").mkdir(parents=True)
    (node / "node.exe").write_bytes(b"fixture")
    (pnpm / "bin/pnpm.cjs").write_bytes(b"fixture")
    prepared = {
        name: {"dest": dest, "archive": tmp_path / "archive", "manifest": {}}
        for name, dest in [("node", node), ("pnpm", pnpm)]
    }
    monkeypatch.setattr(module, "verify_archive", lambda *a: None)
    monkeypatch.setattr(module, "inspect_archive", lambda *a: {})
    checked = []
    monkeypatch.setattr(module, "check_disk", lambda *a: checked.append(a[0]))
    monkeypatch.setattr(module, "verify_identity", lambda *a: None)
    calls = []

    def version(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(
            argv, 0, "v22.23.2\n" if len(argv) == 2 else "9.12.0\n", ""
        )

    monkeypatch.setattr(module.subprocess, "run", version)
    records = module.probe(tmp_path, prepared)
    assert calls == [
        [str(node / "node.exe"), "--version"],
        [str(node / "node.exe"), str(pnpm / "bin/pnpm.cjs"), "--version"],
    ]
    assert len(checked) == 6
    assert records[1]["exit"] == 0


def test_manifest_missing_identity_and_format(tmp_path):
    module = api()
    path = archive(tmp_path, [("package/a", b"abc")])
    manifest = module.inspect_archive(path, "zip", "package")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a").write_bytes(b"abc")
    with pytest.raises(ValueError, match="Procedencia"):
        module.check_disk(dest, manifest, {"pin": "present"})
    with pytest.raises(ValueError, match="Runtime"):
        module.verify_identity(dest, "node")
    with pytest.raises(ValueError, match="Formato"):
        module.open_archive(path, "unknown")


def test_prepared_check_only_offline(tmp_path, monkeypatch):
    module, path, pin, _manifest = fixture_install(tmp_path)
    pin = dict(pin, version="9.12.0", asset="pnpm.tgz")
    monkeypatch.setattr(module, "PINS", {"pnpm": pin})
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    (archive_dir / pin["asset"]).write_bytes(path.read_bytes())
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/tools.lock.json").write_text(
        json.dumps({"schema_version": 1, "tools": module.PINS})
    )
    module.prepare(tmp_path, archive_dir, False)
    monkeypatch.setattr(
        module, "extract", lambda *a: pytest.fail("No extraction on check")
    )
    monkeypatch.setattr(
        module, "download", lambda *a: pytest.fail("No download on check")
    )
    assert (
        module.prepare(tmp_path, archive_dir, True)["pnpm"]["dest"]
        == tmp_path / pin["dest"]
    )


def test_native_junction_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    marker = target / "control"
    marker.write_bytes(b"preserve")
    link = tmp_path / "link"
    assert link.parent.resolve() == tmp_path.resolve()
    command = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert command.returncode == 0, command.stderr
    try:
        with pytest.raises(ValueError):
            api().safe_path(link / "new", tmp_path)
        assert marker.read_bytes() == b"preserve"
    finally:
        assert link.resolve() == target.resolve()
        os.rmdir(link)


def test_member_path_budget(tmp_path):
    path = archive(tmp_path, [("package/" + "a" * 256, b"payload")])
    before = set(tmp_path.rglob("*"))
    with pytest.raises(ValueError, match="Ruta|longitud"):
        api().inspect_archive(path, "zip", "package")
    assert set(tmp_path.rglob("*")) == before


def test_digest_exact_bytes(tmp_path):
    path = tmp_path / "payload"
    path.write_bytes(b"abc")
    assert api().digest(path) == hashlib.sha256(b"abc").hexdigest()


@pytest.mark.parametrize("kind", ["zip", "tar"])
def test_exact_manifest(tmp_path, kind):
    path = archive(tmp_path, [("package/a", b"abc")], kind)
    assert api().inspect_archive(path, kind, "package") == {
        "a": {
            "bytes": 3,
            "sha256": hashlib.sha256(b"abc").hexdigest(),
            "executable": False,
        }
    }


def test_extract_payload_effect(tmp_path):
    module, path, pin, manifest = fixture_install(tmp_path)
    dest = module.extract(tmp_path, path, "pnpm", pin, manifest)
    payload = dest / "LICENSE"
    assert (payload.read_bytes() if payload.is_file() else None) == b"license"


def test_disk_source_metadata(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a").write_bytes(b"abc")
    manifest = {
        "a": {
            "bytes": 3,
            "sha256": hashlib.sha256(b"abc").hexdigest(),
            "executable": False,
        }
    }
    (dest / api().MANIFEST).write_text("{}")
    with pytest.raises(ValueError, match="Procedencia"):
        api().check_disk(dest, manifest, {"source": "fixed"})


def test_environment_exact_config(tmp_path):
    env = api().build_environment(
        tmp_path, {"SYSTEMROOT": "C:/Windows", "SECRET": "discard"}
    )
    assert env.get("npm_config_manage_package_manager_versions") == "false"
    assert "SECRET" not in env


def test_download_payload_effect(tmp_path, monkeypatch):
    import io

    module = api()
    monkeypatch.setattr(
        module.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"abc")
    )
    pin = {
        "url": "https://fixture.invalid",
        "asset": "fixture.zip",
        "bytes": 3,
        "sha256": hashlib.sha256(b"abc").hexdigest(),
    }
    path = module.download(tmp_path, pin)
    assert (path.read_bytes() if path.is_file() else None) == b"abc"


def test_prepare_real_transport_cached(tmp_path, monkeypatch):
    import io

    module, path, pin, manifest = fixture_install(tmp_path)
    pin = dict(
        pin, asset="fixture.tgz", url="https://fixture.invalid", version="9.12.0"
    )
    monkeypatch.setattr(module, "PINS", {"pnpm": pin})
    (tmp_path / "tools").mkdir()
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@9.12.0"}')
    (tmp_path / "tools/tools.lock.json").write_text(
        json.dumps({"schema_version": 1, "tools": module.PINS})
    )
    calls = []

    def transport(*args, **kwargs):
        calls.append(args)
        return io.BytesIO(path.read_bytes())

    monkeypatch.setattr(module.urllib.request, "urlopen", transport)
    try:
        first = module.prepare(tmp_path, None, False)
        second = module.prepare(tmp_path, None, False)
    except ValueError:
        first = second = {}
    assert len(calls) == 1
    assert first == second
    assert first["pnpm"]["manifest"] == manifest
    assert (first["pnpm"]["dest"] / "LICENSE").read_bytes() == b"license"


def test_probe_package_pin_before_execution(tmp_path):
    (tmp_path / "package.json").write_text('{"packageManager":"pnpm@10.0.0"}')
    with pytest.raises(ValueError, match="packageManager"):
        api().probe(tmp_path, {})


def test_direct_extract_rejects_before_any_writes(tmp_path):
    module = api()
    path = archive(tmp_path, [("package/../escape", b"bad")])
    pin = {
        "kind": "zip",
        "prefix": "package",
        "dest": "tools/private",
        "bytes": path.stat().st_size,
        "sha256": module.digest(path),
    }
    before = set(tmp_path.rglob("*"))
    with pytest.raises(ValueError):
        module.extract(tmp_path, path, "pnpm", pin, {})
    assert set(tmp_path.rglob("*")) == before
