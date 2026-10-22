"""Adquisicion confinada del sysroot Linux de almacenamiento."""

import hashlib
import importlib.util
import io
import json
import lzma
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def storage_fetch():
    path = ROOT / "scripts/fetch_storage_linux.py"
    spec = importlib.util.spec_from_file_location("studio_fetch_storage_linux", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tar(entries):
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w") as archive:
        for name, content, kind in entries:
            info = tarfile.TarInfo(name)
            if kind == "dir":
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                archive.addfile(info)
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = content
                archive.addfile(info)
            else:
                raw = content.encode()
                info.size = len(raw)
                info.mode = 0o755 if name.endswith("/qemu-img") else 0o644
                archive.addfile(info, io.BytesIO(raw))
    return lzma.compress(payload.getvalue())


def _deb(entries):
    control = _tar([("control", "Package: fixture\n", "file")])
    data = _tar(entries)
    members = [
        ("debian-binary", b"2.0\n"),
        ("control.tar.xz", control),
        ("data.tar.xz", data),
    ]
    output = io.BytesIO(b"!<arch>\n")
    output.seek(0, io.SEEK_END)
    for name, content in members:
        encoded = name.encode().ljust(16, b" ")
        header = encoded + b"0           " + b"0     " + b"0     " + b"100644  "
        header += str(len(content)).encode().ljust(10, b" ") + b"`\n"
        output.write(header)
        output.write(content)
        if len(content) % 2:
            output.write(b"\n")
    return output.getvalue()


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    fetch = storage_fetch()
    package_bytes = _deb(
        [
            ("usr/bin/qemu-img", "fixture qemu", "file"),
            ("usr/share/doc/qemu-utils/copyright", "license", "file"),
            ("lib/fixture.so", "library", "file"),
            ("usr/lib/libfixture.so.1", "library", "file"),
            ("usr/lib/libfixture.so", "libfixture.so.1", "symlink"),
        ]
    )
    source = tmp_path / "packages"
    source.mkdir()
    (source / "qemu-utils.deb").write_bytes(package_bytes)
    pin = {
        "schema_version": 1,
        "tool_id": "fixture",
        "dest": "tools/storage-linux/test-bundle",
        "packages": [
            {
                "package": "qemu-utils",
                "version": "1.0",
                "architecture": "amd64",
                "url": "https://deb.debian.org/debian/qemu-utils.deb",
                "sha256": hashlib.sha256(package_bytes).hexdigest(),
                "bytes": len(package_bytes),
            }
        ],
        "executables": ["usr/bin/qemu-img"],
    }
    monkeypatch.setattr(fetch, "_load_pin", lambda: pin)
    return fetch, tmp_path, source, pin


def test_import_local_extracts_verified_private_sysroot(fixture):
    fetch, root, source, pin = fixture

    assert fetch.main(["--import-local", str(source), "--root", str(root)]) == 0
    dest = root / pin["dest"]
    assert (dest / "usr/bin/qemu-img").read_text() == "fixture qemu"
    assert (dest / "usr/lib/libfixture.so").read_text() == "library"
    provenance = json.loads((dest / ".provenance.json").read_text())
    assert provenance["pin"]["packages"][0]["package"] == "qemu-utils"
    assert (
        provenance["materialized_aliases"]["symlinks"]["usr/lib/libfixture.so"]
        == "usr/lib/libfixture.so.1"
    )
    assert fetch.main(["--check", "--root", str(root)]) == 0


def test_existing_destination_is_preserved(fixture):
    fetch, root, source, pin = fixture
    dest = root / pin["dest"]
    dest.mkdir(parents=True)
    (dest / "foreign").write_bytes(b"foreign")

    assert fetch.main(["--import-local", str(source), "--root", str(root)]) == 2
    assert (dest / "foreign").read_bytes() == b"foreign"


@pytest.mark.parametrize(
    "entries",
    [
        [("../escape", "bad", "file")],
        [("usr/bin/qemu-img", "bad", "symlink")],
    ],
)
def test_unsafe_payload_is_rejected_without_publication(fixture, entries):
    fetch, root, source, pin = fixture
    package = _deb(entries)
    (source / "qemu-utils.deb").write_bytes(package)
    pin["packages"][0]["sha256"] = hashlib.sha256(package).hexdigest()
    pin["packages"][0]["bytes"] = len(package)

    assert fetch.main(["--import-local", str(source), "--root", str(root)]) == 2
    assert not (root / pin["dest"]).exists()


def test_tampered_package_is_rejected(fixture):
    fetch, root, source, _ = fixture
    (source / "qemu-utils.deb").write_bytes(b"tampered")

    assert fetch.main(["--import-local", str(source), "--root", str(root)]) == 2
    assert not (root / "tools/storage-linux/test-bundle").exists()


def test_invalid_cli_has_no_effect(fixture):
    fetch, root, _, _ = fixture

    assert fetch.main(["--check", "--download", "--root", str(root)]) == 2
    assert not (root / "tools/storage-linux").exists()
