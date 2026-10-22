"""Pruebas de custodia de temporales; ninguna raíz externa autoriza escritura."""

import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts import test_workspace as ws


@pytest.mark.parametrize("timing", ["entry", "collected", "between"])
def test_cleanup_revalidates_owner_before_each_delete(tmp_path, monkeypatch, timing):
    """Intercalación controlada sobre filesystem real; sólo cambia marcador propio."""
    from contextlib import contextmanager

    owned = ws.create_workspace(tmp_path / "owned")
    marker = owned.path / ws.MARKER
    payloads = [owned.path / name for name in ("first", "second")]
    for payload in payloads:
        payload.write_bytes(b"owned-payload")
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    control = foreign / "control"
    control.write_bytes(b"foreign-control")
    before = (control.stat().st_mode, foreign.stat().st_mode)
    scandir = os.scandir
    unlink = Path.unlink
    removed = []

    @contextmanager
    def tamper(directory):
        with scandir(directory) as iterator:
            if Path(directory) == owned.path and timing == "entry":
                marker.write_text("tampered", encoding="ascii")
            yield iterator
        if Path(directory) == owned.path and timing == "collected":
            marker.write_text("tampered", encoding="ascii")

    def tamper_between(path, *args, **kwargs):
        result = unlink(path, *args, **kwargs)
        if path in payloads:
            removed.append(path)
            if timing == "between":
                marker.write_text("tampered", encoding="ascii")
        return result

    try:
        with monkeypatch.context() as patch:
            patch.setattr(ws.os, "scandir", tamper)
            patch.setattr(Path, "unlink", tamper_between)
            with pytest.raises(ValueError, match="Marcador alterado"):
                owned.cleanup()
        expected = 1 if timing == "between" else 0
        retained = [
            payload for payload in payloads if payload not in removed[:expected]
        ]
        assert all(payload.is_file() for payload in retained), (
            "Payload borrado después de perder custodia"
        )
        assert len(removed) == expected
        for payload in payloads:
            if payload not in removed:
                assert payload.is_file(), "Payload borrado después de perder custodia"
                assert payload.read_bytes() == b"owned-payload"
        assert control.read_bytes() == b"foreign-control"
        assert (control.stat().st_mode, foreign.stat().st_mode) == before
        assert list(foreign.iterdir()) == [control]
        assert marker.read_text() == "tampered"
        assert ws._OWNED[owned.path] == owned.token
    finally:
        # Sólo el test propietario restaura su token tras la limpieza fallida.
        marker.write_text(owned.token, encoding="ascii")
        owned.cleanup()


def _native_junction(link, target):
    """Guarda la creación nativa fuera del UUID que se va a limpiar."""
    proof = (
        ws.workspace_base(
            os.environ.get("STUDIO_TEST_PROOF_ROOT", ".cache/pytest-proofs")
        )
        / uuid.uuid4().hex
    )
    proof.mkdir(parents=True)
    (proof / "test-source.py").write_bytes(Path(__file__).read_bytes())
    (proof / "helper-source.py").write_bytes(Path(ws.__file__).read_bytes())
    argv = ["cmd", "/d", "/c", "mklink", "/J", str(link), str(target)]
    receipt = {
        "argv": argv,
        "parent_pid": os.getpid(),
        "utc_start": datetime.now(UTC).isoformat(),
    }
    (proof / "command.json").write_text(json.dumps(receipt))
    child = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    receipt.update(child_pid=child.pid, child_created_utc=datetime.now(UTC).isoformat())
    (proof / "command.json").write_text(json.dumps(receipt))
    stdout, stderr = child.communicate()
    receipt.update(exit=child.returncode, utc_end=datetime.now(UTC).isoformat())
    (proof / "command.json").write_text(json.dumps(receipt))
    (proof / "stdout.txt").write_text(stdout)
    (proof / "stderr.txt").write_text(stderr)
    assert child.returncode == 0, stderr
    return subprocess.CompletedProcess(argv, child.returncode, stdout, stderr)


@pytest.mark.skipif(os.name != "nt", reason="Junction nativa Windows")
@pytest.mark.parametrize("target_kind", ["foreign", "cycle", "broken"])
def test_context_cleanup_native_child_junction(tmp_path, target_kind):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    control = foreign / "control"
    control.write_bytes(b"foreign-control")
    before = (control.stat().st_mode, foreign.stat().st_mode)
    owned = None
    link = None
    try:
        with control.open("rb") as handle:
            with ws.workspace(tmp_path / "owned") as path:
                owned = path
                link = path / "link"
                target = {
                    "foreign": foreign,
                    "cycle": path,
                    "broken": tmp_path / "missing",
                }[target_kind]
                _native_junction(link, target)
                with pytest.raises(ValueError):
                    ws.checked_path(link)
                assert handle.read() == b"foreign-control"
            assert not owned.exists()
            handle.seek(0)
            assert handle.read() == b"foreign-control"
        assert control.read_bytes() == b"foreign-control"
        assert (control.stat().st_mode, foreign.stat().st_mode) == before
        assert list(foreign.iterdir()) == [control]
    finally:
        if link is not None and link.is_junction():
            os.rmdir(link)
        if owned is not None and owned.exists():
            ws.Workspace(owned, owned.parent, ws._OWNED[owned]).cleanup()


def test_context_cleanup_native_child_hardlink(tmp_path):
    control = tmp_path / "foreign-file"
    control.write_bytes(b"foreign-control")
    before = control.stat().st_mode
    owned = None
    link = None
    try:
        with control.open("rb") as handle:
            with ws.workspace(tmp_path / "owned") as path:
                owned = path
                link = path / "link"
                os.link(control, link)
                assert link.lstat().st_nlink == 2
                assert handle.read() == b"foreign-control"
            assert not owned.exists()
            handle.seek(0)
            assert handle.read() == b"foreign-control"
        assert control.read_bytes() == b"foreign-control"
        assert control.stat().st_mode == before
        assert control.stat().st_nlink == 1
    finally:
        if link is not None and link.exists():
            link.unlink()
        if owned is not None and owned.exists():
            ws.Workspace(owned, owned.parent, ws._OWNED[owned]).cleanup()


@pytest.mark.skipif(os.name != "nt", reason="Handle nativo Windows")
def test_cleanup_open_directory_preserves_marker(tmp_path):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    owned = ws.create_workspace(tmp_path / "owned")
    marker = owned.path / ws.MARKER
    handle = kernel.CreateFileW(
        str(owned.path), 0x80000000, 3, None, 3, 0x02000000, None
    )
    assert handle != wintypes.HANDLE(-1).value, ctypes.get_last_error()
    try:
        with pytest.raises(PermissionError):
            owned.cleanup()
        assert marker.read_text() == owned.token
        assert ws._OWNED[owned.path] == owned.token
    finally:
        assert kernel.CloseHandle(handle)
        # Recuperación explícita del RED anterior, sólo UUID/registro propios.
        if not marker.exists():
            marker.write_text(owned.token)
        owned.cleanup()


@pytest.mark.parametrize("kind", ["file", "directory", "broken", "cycle"])
def test_context_cleanup_native_child_symlink(tmp_path, kind):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    control = foreign / "control"
    control.write_bytes(b"foreign-control")
    before = (control.stat().st_mode, foreign.stat().st_mode)
    with control.open("rb") as handle:
        with ws.workspace(tmp_path / "owned") as path:
            target = {
                "file": control,
                "directory": foreign,
                "broken": tmp_path / "missing",
                "cycle": path,
            }[kind]
            try:
                (path / "link").symlink_to(target, target_is_directory=kind != "file")
            except OSError as exc:
                if os.name == "nt" and exc.winerror == 1314:
                    pytest.skip("Windows sin privilegio de symlink nativo")
                raise
            with pytest.raises(ValueError):
                ws.checked_path(path / "link")
        assert not path.exists()
        assert handle.read() == b"foreign-control"
    assert (control.stat().st_mode, foreign.stat().st_mode) == before
    assert list(foreign.iterdir()) == [control]


def test_cleanup_marker_hardlink_stays_failclosed(tmp_path):
    owned = ws.create_workspace(tmp_path / "owned")
    marker = owned.path / ws.MARKER
    foreign = tmp_path / "marker-control"
    os.link(marker, foreign)
    before = foreign.stat().st_mode
    try:
        with pytest.raises(ValueError, match="Marcador alterado"):
            owned.cleanup()
        assert marker.read_text() == owned.token
        assert foreign.read_text() == owned.token
        assert foreign.stat().st_mode == before
        assert ws._OWNED[owned.path] == owned.token
    finally:
        foreign.unlink()
        owned.cleanup()


@pytest.mark.skipif(os.name != "nt", reason="Junction nativa Windows")
def test_cleanup_owned_root_reparse_stays_failclosed(tmp_path):
    owned = ws.create_workspace(tmp_path / "owned")
    backup = tmp_path / "original"
    owned.path.rename(backup)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    control = foreign / "control"
    control.write_bytes(b"preserve")
    _native_junction(owned.path, foreign)
    try:
        with pytest.raises(ValueError, match="Enlace/reparse"):
            owned.cleanup()
        assert control.read_bytes() == b"preserve"
        assert list(foreign.iterdir()) == [control]
        assert (backup / ws.MARKER).read_text() == owned.token
    finally:
        os.rmdir(owned.path)
        backup.rename(owned.path)
        owned.cleanup()


@pytest.mark.skipif(os.name != "nt", reason="Junction nativa Windows")
@pytest.mark.parametrize("replacement", ["junction", "directory"])
def test_cleanup_preinspected_directory_swap_rejected(
    tmp_path, monkeypatch, replacement
):
    from contextlib import contextmanager

    owned = ws.create_workspace(tmp_path / "owned")
    child = owned.path / "directory"
    child.mkdir()
    (child / "payload").write_bytes(b"owned")
    backup = tmp_path / "backup"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    control = foreign / "control"
    control.write_bytes(b"preserve")
    before = control.stat().st_mode
    scandir = os.scandir

    @contextmanager
    def swap_after_inspection(directory):
        with scandir(directory) as iterator:
            yield iterator
        if Path(directory) == child:
            child.rename(backup)
            if replacement == "junction":
                _native_junction(child, foreign)
            else:
                child.mkdir()
                (child / "control").write_bytes(b"replacement")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(ws.os, "scandir", swap_after_inspection)
            with pytest.raises(ValueError, match="Enlace/reparse|Directorio cambiado"):
                owned.cleanup()
        assert control.read_bytes() == b"preserve"
        assert control.stat().st_mode == before
        assert list(foreign.iterdir()) == [control]
        assert (owned.path / ws.MARKER).read_text() == owned.token
    finally:
        if child.is_junction():
            os.rmdir(child)
        elif child.exists():
            assert (child / "control").read_bytes() == b"replacement"
            (child / "control").unlink()
            child.rmdir()
        if backup.exists():
            backup.rename(child)
        owned.cleanup()


def test_namespace_default_no_historical_phase(monkeypatch):
    monkeypatch.delenv("STUDIO_TEST_ROOT", raising=False)
    assert ws.workspace_base() == ws.ROOT / ".cache/pytest-tmp"


@pytest.mark.parametrize(
    "namespace", ["../escape", "C:/foreign", ".cache/../escape", "tools/private"]
)
def test_namespace_escape_rejected(namespace):
    with pytest.raises(ValueError):
        ws.workspace_base(namespace)


def test_caller_cannot_redefine_repository(tmp_path):
    with pytest.raises(ValueError):
        ws.workspace_base(".cache/private", root=tmp_path)


def test_create_owned_uuid_and_control(tmp_path, monkeypatch):
    base = tmp_path / "workspaces"
    base.mkdir()
    (base / "control").write_bytes(b"preserve")
    monkeypatch.setenv("STUDIO_TEST_ROOT", str(base))
    owned = ws.create_workspace()
    assert owned.path.parent == base
    assert len(owned.path.name) == 32
    assert (owned.path / ws.MARKER).read_text() == owned.token
    assert (base / "control").read_bytes() == b"preserve"
    owned.cleanup()


def test_cleanup_only_owned_uuid(tmp_path, monkeypatch):
    base = tmp_path / "owned"
    monkeypatch.setenv("STUDIO_TEST_ROOT", str(base))
    owned = ws.create_workspace()
    foreign = base / "foreign"
    foreign.mkdir()
    (foreign / "control").write_bytes(b"preserve")
    (owned.path / "payload").write_bytes(b"owned")
    owned.cleanup()
    assert not owned.path.exists()
    assert (foreign / "control").read_bytes() == b"preserve"


def test_cleanup_marker_tamper_failclosed(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDIO_TEST_ROOT", str(tmp_path / "owned"))
    owned = ws.create_workspace()
    marker = owned.path / ws.MARKER
    marker.write_text("foreign")
    try:
        with pytest.raises(ValueError):
            owned.cleanup()
        assert marker.read_text() == "foreign"
    finally:
        marker.write_text(owned.token)
        owned.cleanup()


@pytest.mark.skipif(os.name != "nt", reason="mklink /J nativo Windows")
def test_namespace_native_junction_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "control").write_bytes(b"preserve")
    link = tmp_path / "link"
    assert link.parent.resolve() == tmp_path.resolve()
    command = _native_junction(link, target)
    assert command.returncode == 0, command.stderr
    try:
        with pytest.raises(ValueError):
            ws.create_workspace(str(link / "new"))
        assert (target / "control").read_bytes() == b"preserve"
        assert list(target.iterdir()) == [target / "control"]
    finally:
        assert link.resolve() == target.resolve()
        os.rmdir(link)


@pytest.mark.skipif(os.name != "nt", reason="mklink /J nativo Windows")
def test_cleanup_native_junction_unlinks_child(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDIO_TEST_ROOT", str(tmp_path / "owned"))
    owned = ws.create_workspace()
    target = tmp_path / "foreign"
    target.mkdir()
    marker = target / "control"
    marker.write_bytes(b"preserve")
    link = owned.path / "link"
    assert link.parent.resolve() == owned.path.resolve()
    out = _native_junction(link, target)
    assert out.returncode == 0, out.stderr
    try:
        assert (owned.path / ws.MARKER).read_text() == owned.token
        owned.cleanup()
        assert marker.read_bytes() == b"preserve"
        assert not owned.path.exists()
    finally:
        if link.is_junction():
            assert link.resolve() == target.resolve()
            os.rmdir(link)
        if owned.path.exists():
            owned.cleanup()


def test_cannot_cleanup_forged_owner(tmp_path):
    forged = ws.Workspace(tmp_path, tmp_path.parent, "forged")
    with pytest.raises(ValueError):
        forged.cleanup()


@pytest.mark.parametrize("fixture_source", ["conftest.py", "tests/conftest.py"])
def test_actual_pytest_fixture_namespace_and_release(tmp_path, fixture_source):
    source_root = Path(os.environ.get("STUDIO_FIXTURE_PROBE_SOURCES", str(ws.ROOT)))
    probe = tmp_path / "probe"
    probe.mkdir()
    namespace = tmp_path / "namespace"
    namespace.mkdir()
    control = namespace / "control"
    control.write_bytes(b"preserve")
    result = probe / "result.json"
    source = source_root / fixture_source
    (probe / "conftest.py").write_text(
        "import importlib.util\n"
        f'spec=importlib.util.spec_from_file_location("actual_fixture", {str(source)!r})\n'
        "module=importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\n"
        "tmp_path=module.tmp_path\n",
        encoding="utf-8",
    )
    (probe / "test_probe.py").write_text(
        "import json\nfrom pathlib import Path\n"
        "def test_effect(tmp_path):\n"
        '    (tmp_path/"payload").write_bytes(b"owned")\n'
        f'    Path({str(result)!r}).write_text(json.dumps({{"path":str(tmp_path)}}))\n',
        encoding="utf-8",
    )
    env = dict(os.environ, STUDIO_TEST_ROOT=str(namespace))
    instrumentation = (
        [
            "-m",
            "coverage",
            "run",
            "--parallel-mode",
            "--rcfile=" + os.environ["STUDIO_FIXTURE_CHILD_COVERAGE"],
            "-m",
            "pytest",
        ]
        if "STUDIO_FIXTURE_CHILD_COVERAGE" in os.environ
        else ["-m", "pytest"]
    )
    argv = [
        sys.executable,
        "-B",
        *instrumentation,
        str(probe / "test_probe.py"),
        "--confcutdir=" + str(probe),
        "-p",
        "no:cacheprovider",
        "-q",
        "--junitxml=" + str(probe / "pytest.xml"),
    ]
    proof = (
        ws.workspace_base(
            os.environ.get("STUDIO_TEST_PROOF_ROOT", ".cache/pytest-proofs")
        )
        / uuid.uuid4().hex
    )
    proof.mkdir(parents=True)
    for item in probe.iterdir():
        if item.is_file():
            (proof / item.name).write_bytes(item.read_bytes())
    (proof / "fixture-source.py").write_bytes(source.read_bytes())
    (proof / "helper-source.py").write_bytes(Path(ws.__file__).read_bytes())
    (proof / "parent-test-source.py").write_bytes(Path(__file__).read_bytes())
    argv[-1] = "--junitxml=" + str(proof / "pytest.xml")
    started = datetime.now(UTC).isoformat()
    receipt = {
        "utc_start": started,
        "argv": argv,
        "cwd": str(ws.ROOT),
        "source": str(source),
        "parent_pid": os.getpid(),
    }
    (proof / "command.json").write_text(json.dumps(receipt))
    child = subprocess.Popen(
        argv,
        cwd=ws.ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    receipt.update(child_pid=child.pid, child_created_utc=datetime.now(UTC).isoformat())
    (proof / "command.json").write_text(json.dumps(receipt))
    stdout, stderr = child.communicate()
    receipt.update(exit=child.returncode, utc_end=datetime.now(UTC).isoformat())
    (proof / "command.json").write_text(json.dumps(receipt))
    (proof / "stdout.txt").write_text(stdout, encoding="utf-8")
    (proof / "stderr.txt").write_text(stderr, encoding="utf-8")
    out = subprocess.CompletedProcess(
        argv, child.returncode, stdout=stdout, stderr=stderr
    )
    for item in probe.iterdir():
        if item.is_file():
            (proof / item.name).write_bytes(item.read_bytes())
    assert out.returncode == 0, out.stdout + out.stderr
    allocated = Path(json.loads(result.read_text())["path"])
    assert allocated.parent == namespace
    assert not allocated.exists()
    assert control.read_bytes() == b"preserve"
    assert list(namespace.iterdir()) == [control]


@pytest.mark.skipif(
    os.name != "nt", reason="Share-deny de archivo abierto nativo Windows"
)
def test_cleanup_error_preserves_owner_marker(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDIO_TEST_ROOT", str(tmp_path / "owned"))
    owned = ws.create_workspace()
    payload = owned.path / "payload"
    payload.write_bytes(b"locked")
    marker = owned.path / ws.MARKER
    try:
        with payload.open("rb"):
            with pytest.raises(PermissionError):
                owned.cleanup()
            assert marker.is_file()
            assert marker.read_text() == owned.token
    finally:
        if not marker.exists():
            marker.write_text(owned.token)
        owned.cleanup()


@pytest.mark.skipif(os.name != "nt", reason="Enumeración nativa Windows")
def test_cleanup_native_empty_directory_without_identity_change():
    """La enumeración puede cambiar un bit incidental sin sustituir el objeto."""
    owned = ws.create_workspace(ws.ROOT / ".cache" / "empty-directory-regression")
    child = owned.path / "empty"
    child.mkdir()
    before = child.lstat()
    with os.scandir(child) as entries:
        assert list(entries) == []
    after = child.lstat()
    assert (before.st_dev, before.st_ino, before.st_mode, before.st_reparse_tag) == (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_reparse_tag,
    )
    # Use a fresh directory: collect must perform the first enumeration itself.
    child.rmdir()
    child.mkdir()
    owned.cleanup()
    assert not owned.path.exists()
    assert owned.path not in ws._OWNED
