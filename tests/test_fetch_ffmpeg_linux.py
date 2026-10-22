"""Synthetic real TAR test double: these pins do NOT prove the official release."""

import hashlib
import io
import json
import os
import tarfile
import uuid
from pathlib import Path

import pytest

from scripts import fetch_ffmpeg_linux as fetch


@pytest.fixture
def sample(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    archive = root / "source.tar.xz"

    def make(members=None):
        with tarfile.open(archive, "w:xz") as tar:
            for name, data, kind in members or [
                ("release/bin/ffmpeg", b"synthetic ELF", tarfile.REGTYPE),
                ("release/bin/ffprobe", b"synthetic probe", tarfile.REGTYPE),
                ("release/LICENSE.txt", b"synthetic LGPL notice", tarfile.REGTYPE),
            ]:
                entry = tarfile.TarInfo(name)
                entry.type = kind
                entry.mode = 0o6755
                entry.size = len(data) if kind == tarfile.REGTYPE else 0
                entry.linkname = "outside"
                tar.addfile(entry, io.BytesIO(data) if entry.size else None)
        pin = {
            "candidate": {
                "bytes": archive.stat().st_size,
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "asset": "release.tar.xz",
                "url": "https://example.invalid/TESTDOUBLE",
            },
            "dest": "tools/ffmpeg-linux/TESTDOUBLE",
        }
        monkeypatch.setattr(fetch, "ROOT", root)
        monkeypatch.setattr(fetch, "_load_pin", lambda: pin)
        capture_root = os.environ.get("STUDIO_FFMPEG_TEST_FIXTURES")
        if capture_root:
            capture = Path(capture_root) / uuid.uuid4().hex
            capture.mkdir(parents=True)
            (capture / "fixture.tar.xz").write_bytes(archive.read_bytes())
            (capture / "TESTDOUBLE-pin.json").write_text(json.dumps(pin), "utf-8")
        return pin

    pin = make()
    return root, archive, pin, make


def test_import_preserves_source_and_notices(sample):
    root, source, pin, _ = sample
    before = source.read_bytes()
    assert fetch.main(["--import-local", str(source)]) == 0
    dest = root / pin["dest"]
    assert (dest / "bin/ffmpeg").read_bytes() == b"synthetic ELF"
    assert (dest / "LICENSE.txt").read_bytes() == b"synthetic LGPL notice"
    assert source.read_bytes() == before
    assert fetch.main(["--check"]) == 0


@pytest.mark.parametrize(
    "name",
    [
        "/outside",
        "release/../escape",
        "release/bin/NUL",
        "release/bin/a:b",
        "release//a",
        "release/./a",
        "release/bin/a.",
        "other/bin/a",
        "release/bin/a\\b",
    ],
)
def test_reject_unsafe_names(sample, name):
    root, source, pin, make = sample
    make(
        [
            ("release/bin/ffmpeg", b"ok", tarfile.REGTYPE),
            (name, b"bad", tarfile.REGTYPE),
        ]
    )
    before = source.read_bytes()
    assert fetch.main(["--import-local", str(source)]) == 2
    assert not (root / pin["dest"]).exists()
    assert source.read_bytes() == before


@pytest.mark.parametrize(
    "kind",
    [
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
        tarfile.FIFOTYPE,
        b"X",
    ],
)
def test_reject_special_members(sample, kind):
    root, source, pin, make = sample
    make([("release/bin/ffmpeg", b"ok", tarfile.REGTYPE), ("release/bad", b"", kind)])
    assert fetch.main(["--import-local", str(source)]) == 2
    assert not (root / pin["dest"]).exists()


def test_duplicate_casefold(sample):
    _, source, _, make = sample
    make(
        [
            ("release/bin/ffmpeg", b"a", tarfile.REGTYPE),
            ("release/bin/FFMPEG", b"b", tarfile.REGTYPE),
        ]
    )
    assert fetch.main(["--import-local", str(source)]) == 2


def test_tampered_archive_rejected_before_extraction(sample):
    root, source, pin, _ = sample
    source.write_bytes(source.read_bytes() + b"tamper")
    assert fetch.main(["--import-local", str(source)]) == 2
    assert not (root / pin["dest"]).exists()


@pytest.mark.parametrize(
    "target", ["bin/ffmpeg", ".archive.tar.xz", ".provenance.json"]
)
def test_check_rejects_tampering(sample, target):
    root, source, pin, _ = sample
    assert fetch.main(["--import-local", str(source)]) == 0
    (root / pin["dest"] / target).write_bytes(b"tampered")
    assert fetch.main(["--check"]) == 2


def test_foreign_publication_preserved(sample):
    root, source, pin, _ = sample
    dest = root / pin["dest"]
    dest.mkdir(parents=True)
    (dest / "foreign").write_bytes(b"mine")
    assert fetch.main(["--import-local", str(source)]) == 2
    assert (dest / "foreign").read_bytes() == b"mine"


def test_concurrent_lock_preserved(sample):
    root, source, pin, _ = sample
    parent = (root / pin["dest"]).parent
    parent.mkdir(parents=True)
    lock = parent / ".acquisition-lock"
    lock.mkdir()
    (lock / "foreign").write_bytes(b"mine")
    assert fetch.main(["--import-local", str(source)]) == 2
    assert (lock / "foreign").read_bytes() == b"mine"


@pytest.mark.parametrize("failure", [OSError("disk"), KeyboardInterrupt()])
def test_rollback_cancel_own_cleanup(sample, monkeypatch, failure):
    root, source, pin, _ = sample
    before = source.read_bytes()

    def fail(*args):
        raise failure

    monkeypatch.setattr(fetch, "_publish", fail)
    assert fetch.main(["--import-local", str(source)]) == 2
    assert not (root / pin["dest"]).exists()
    assert not list((root / pin["dest"]).parent.glob(".stage-*"))
    assert source.read_bytes() == before


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--check", "--download"],
        ["--import-local", "missing"],
        ["--root", "..", "--check"],
    ],
)
def test_invalid_cli_controlled(sample, args):
    assert fetch.main(args) == 2


def test_invalid_api_type(sample):
    with pytest.raises(fetch.InputError):
        fetch.acquire(123)


def test_check_detects_added_empty_directory(sample):
    root, source, pin, _ = sample
    assert fetch.main(["--import-local", str(source)]) == 0
    (root / pin["dest"] / "foreign-empty").mkdir()
    assert fetch.main(["--check"]) == 2


def test_check_rejects_privileged_mode(sample):
    _, source, _, _ = sample
    assert fetch.main(["--import-local", str(source)]) == 0
    # Windows chmod cannot represent setuid: use a labelled stat TESTDOUBLE.
    original = fetch._plain

    def privileged(path, directory=False):
        info = original(path, directory)
        if path.name == "ffmpeg":
            import os

            fields = list(info)
            fields[0] |= 0o4000
            return os.stat_result(fields)
        return info

    from unittest.mock import patch

    with patch.object(fetch, "_plain", privileged):
        assert fetch.main(["--check"]) == 2


@pytest.mark.parametrize(
    "limit", ["MAX_ENTRIES", "MAX_FILE_BYTES", "MAX_EXPANDED_BYTES"]
)
def test_bounded_extraction(sample, monkeypatch, limit):
    root, source, pin, _ = sample
    monkeypatch.setattr(fetch, limit, 1)
    assert fetch.main(["--import-local", str(source)]) == 2
    assert not (root / pin["dest"]).exists()


def test_download_and_reuse_verified_cache(sample, monkeypatch):
    root, source, pin, _ = sample
    # Transport TESTDOUBLE only: production receives no caller URL/pin config.
    calls = []

    class Response(io.BytesIO):
        pass

    class Opener:
        def open(self, url, timeout):
            calls.append((url, timeout))
            return Response(source.read_bytes())

    monkeypatch.setattr(fetch.urllib.request, "build_opener", lambda *a: Opener())
    assert fetch.main(["--download"]) == 0
    assert calls == [(pin["candidate"]["url"], 30)]
    assert fetch.main(["--check"]) == 0
    alternate = root / "alternate"
    alternate.mkdir()
    # cache belongs to repository root, even with a confined output root.
    assert fetch.main(["--download", "--root", str(alternate)]) == 0
    assert len(calls) == 1


def test_local_directory_input(sample):
    root, _, _, _ = sample
    assert fetch.main(["--import-local", str(root)]) == 2


def test_missing_check(sample):
    assert fetch.main(["--check"]) == 2


def test_file_directory_collision(sample):
    _, source, _, make = sample
    make(
        [
            ("release/bin", b"a", tarfile.REGTYPE),
            ("release/bin/ffmpeg", b"b", tarfile.REGTYPE),
        ]
    )
    assert fetch.main(["--import-local", str(source)]) == 2


def test_production_lock_is_authoritative(sample, monkeypatch):
    root, _, _, _ = sample
    monkeypatch.undo()
    pin = fetch._load_pin()
    assert (
        pin["candidate"]["sha256"]
        == "2d41cbea0ca1a15029b638330740f78d6f5aeb062355bf425433fc938705350a"
    )
    assert pin["candidate"]["bytes"] == 137863452
    assert fetch.main(["--check", "--root", str(root)]) == 2


def test_implicit_directory_case_ambiguity(sample):
    _, source, _, make = sample
    make(
        [
            ("release/bin/ffmpeg", b"a", tarfile.REGTYPE),
            ("release/BIN/ffprobe", b"b", tarfile.REGTYPE),
            ("release/LICENSE.txt", b"notice", tarfile.REGTYPE),
        ]
    )
    with pytest.raises(fetch.InputError, match="ambigu"):
        fetch._payload(source)


def test_foreign_stage_preserved_lock_cleaned(sample, monkeypatch):
    root, source, pin, _ = sample

    def replace_marker(stage, dest):
        (stage / ".owner").write_text("foreign")
        raise OSError("publication interrupted")

    monkeypatch.setattr(fetch, "_publish", replace_marker)
    assert fetch.main(["--import-local", str(source)]) == 2
    parent = (root / pin["dest"]).parent
    stages = list(parent.glob(".stage-*"))
    assert len(stages) == 1
    assert (stages[0] / ".owner").read_text() == "foreign"
    assert not (parent / ".acquisition-lock").exists()


def test_concurrent_acquisition_no_replace(sample, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    root, source, pin, _ = sample
    entered, proceed = Event(), Event()
    original = fetch._publish

    def delayed(stage, dest):
        entered.set()
        assert proceed.wait(10)
        original(stage, dest)

    monkeypatch.setattr(fetch, "_publish", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fetch.main, ["--import-local", str(source)])
        assert entered.wait(10)
        try:
            assert fetch.main(["--import-local", str(source)]) == 2
        finally:
            proceed.set()
        assert future.result(timeout=10) == 0
    assert fetch.main(["--check"]) == 0
    assert (root / pin["dest"] / "bin/ffmpeg").read_bytes() == b"synthetic ELF"


def test_download_total_deadline(sample, monkeypatch):
    import time

    root, source, pin, _ = sample
    ticks = iter([0, 601, 602, 603])
    monkeypatch.setattr(time, "monotonic", lambda: next(ticks))

    class Opener:
        def open(self, url, timeout):
            return io.BytesIO(source.read_bytes())

    monkeypatch.setattr(fetch.urllib.request, "build_opener", lambda *a: Opener())
    assert fetch.main(["--download"]) == 2
    assert not (root / pin["dest"]).exists()


def test_check_bounded_provenance(sample, monkeypatch):
    root, source, pin, _ = sample
    assert fetch.main(["--import-local", str(source)]) == 0
    path = root / pin["dest"] / ".provenance.json"
    original = fetch._plain

    def oversized(candidate, directory=False):
        info = original(candidate, directory)
        if candidate == path:
            fields = list(info)
            fields[6] = 16 * 1024 * 1024
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(fetch, "_plain", oversized)
    assert fetch.main(["--check"]) == 2
@pytest.mark.parametrize("failure", [OSError("disk full TESTDOUBLE"), KeyboardInterrupt()])
def test_lock_owner_write_failure_cleans_owned_empty_lock(sample, monkeypatch, failure):
    root, source, pin, _ = sample
    original = Path.write_text
    before = source.read_bytes()

    def fail(path, *args, **kwargs):
        if path.name == ".owner" and path.parent.name == ".acquisition-lock":
            raise failure
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail)
    assert fetch.main(["--import-local", str(source)]) == 2
    assert not ((root / pin["dest"]).parent / ".acquisition-lock").exists()
    assert source.read_bytes() == before


@pytest.mark.parametrize("binary", ["ffmpeg", "ffprobe"])
def test_check_rejects_missing_execute_linux_stat_TESTDOUBLE(sample, monkeypatch, binary):
    _, source, _, _ = sample
    assert fetch.main(["--import-local", str(source)]) == 0
    original = fetch._plain

    def mode_model(path, directory=False):
        info = original(path, directory)
        fields = list(info)
        if path.parent.name == "bin" and path.name in ("ffmpeg", "ffprobe"):
            fields[0] = (fields[0] & ~0o777) | (0o644 if path.name == binary else 0o755)
        return os.stat_result(fields)

    # Platform policy TESTDOUBLE only; no native Linux or binary execution.
    monkeypatch.setattr(fetch.sys, "platform", "linux")
    monkeypatch.setattr(fetch, "_plain", mode_model)
    assert fetch.main(["--check"]) == 2

@pytest.mark.parametrize("mutation", ["entry", "marker", "identity", "unknown"])
def test_lock_write_failure_preserves_unknown_custody(sample, monkeypatch, mutation, capsys):
    root, source, pin, _ = sample
    original_write = Path.write_text
    original_plain = fetch._plain
    lock = (root / pin["dest"]).parent / ".acquisition-lock"
    changed = False

    def plain(path, directory=False):
        info = original_plain(path, directory)
        if path == lock:
            if mutation == "unknown":
                raise OSError("identity unavailable TESTDOUBLE")
            if mutation == "identity" and changed:
                # Identity TESTDOUBLE avoids relying on Windows inode reuse.
                fields = list(info)
                fields[1] += 1
                return os.stat_result(fields)
        return info

    def fail(path, *args, **kwargs):
        nonlocal changed
        if path == lock / ".owner":
            if mutation == "entry":
                (lock / "foreign").write_bytes(b"foreign")
            elif mutation == "marker":
                original_write(path, "foreign")
            changed = True
            raise OSError("owner write failure TESTDOUBLE")
        return original_write(path, *args, **kwargs)

    monkeypatch.setattr(fetch, "_plain", plain)
    monkeypatch.setattr(Path, "write_text", fail)
    assert fetch.main(["--import-local", str(source)]) == 2
    assert lock.is_dir()
    assert "UNKNOWN" in capsys.readouterr().err
    if mutation == "entry":
        assert (lock / "foreign").read_bytes() == b"foreign"
    elif mutation == "marker":
        assert (lock / ".owner").read_text() == "foreign"


@pytest.mark.parametrize("mutation", ["entry", "marker", "identity"])
def test_marked_lock_preserves_foreign_custody(sample, monkeypatch, mutation, capsys):
    root, source, pin, _ = sample
    lock = (root / pin["dest"]).parent / ".acquisition-lock"
    original_plain = fetch._plain
    changed = False

    def plain(path, directory=False):
        info = original_plain(path, directory)
        if path == lock and changed and mutation == "identity":
            fields = list(info)
            fields[1] += 1  # Explicit identity TESTDOUBLE.
            return os.stat_result(fields)
        return info

    def fail(stage, dest):
        nonlocal changed
        if mutation == "entry":
            (lock / "foreign").write_bytes(b"foreign")
        elif mutation == "marker":
            (lock / ".owner").write_text("foreign")
        changed = True
        raise OSError("publication interrupted TESTDOUBLE")

    monkeypatch.setattr(fetch, "_plain", plain)
    monkeypatch.setattr(fetch, "_publish", fail)
    assert fetch.main(["--import-local", str(source)]) == 2
    assert lock.is_dir()
    assert (lock / ".owner").exists()
    assert "UNKNOWN" in capsys.readouterr().err
    if mutation == "entry":
        assert (lock / "foreign").read_bytes() == b"foreign"
    elif mutation == "marker":
        assert (lock / ".owner").read_text() == "foreign"


@pytest.mark.parametrize("platform,mode", [("linux", 0o755), ("win32", 0o644)])
def test_check_accepts_platform_mode_stat_TESTDOUBLE(sample, monkeypatch, platform, mode):
    root, source, pin, _ = sample
    assert fetch.main(["--import-local", str(source)]) == 0
    dest = root / pin["dest"]
    before = {p: p.read_bytes() for p in dest.rglob("*") if p.is_file()}
    original = fetch._plain

    def model(path, directory=False):
        info = original(path, directory)
        if path.parent.name == "bin" and path.name in ("ffmpeg", "ffprobe"):
            fields = list(info)
            fields[0] = (fields[0] & ~0o777) | mode
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(fetch.sys, "platform", platform)
    monkeypatch.setattr(fetch, "_plain", model)
    assert fetch.main(["--check"]) == 0
    assert {p: p.read_bytes() for p in before} == before
