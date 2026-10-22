"""Identidad nativa y rechazo de sustituciones en directorios de audio."""

import ctypes
import os
import subprocess
import uuid
from ctypes import wintypes
from pathlib import Path

import pytest
from audio_post import pipeline

ROOT = Path(__file__).resolve().parents[3]


def _native_id(path):
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
    kernel.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    class FileId(ctypes.Structure):
        _fields_ = [("volume", ctypes.c_ulonglong), ("value", ctypes.c_ubyte * 16)]

    handle = kernel.CreateFileW(str(path), 0, 7, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        value = FileId()
        if not kernel.GetFileInformationByHandleEx(
            handle, 18, ctypes.byref(value), ctypes.sizeof(value)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return value.volume, bytes(value.value)
    finally:
        assert kernel.CloseHandle(handle)


@pytest.mark.skipif(os.name != "nt", reason="FileId128 nativo Windows")
def test_native_child_creation_preserves_directory_identity():
    directory = ROOT / ".cache" / ("directory-identity-" + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    original = pipeline._directory_identity(directory)
    native = _native_id(directory)
    before = directory.lstat()
    child = directory / "child"
    try:
        child.mkdir()
        after = directory.lstat()
        assert _native_id(directory) == native
        assert (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_reparse_tag,
        ) == (after.st_dev, after.st_ino, after.st_mode, after.st_reparse_tag)
        assert before.st_file_attributes ^ after.st_file_attributes in (0, 0x10000000)
        assert pipeline._directory_identity(directory) == original
    finally:
        child.rmdir()
        directory.rmdir()


def test_native_directory_replacement_changes_identity(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()
    original = pipeline._directory_identity(directory)
    backup = tmp_path / "backup"
    directory.rename(backup)
    directory.mkdir()
    (directory / "foreign").write_bytes(b"preserve")
    assert pipeline._directory_identity(directory) != original
    assert (directory / "foreign").read_bytes() == b"preserve"
    assert backup.is_dir()


def test_directory_identity_rejects_regular_file(tmp_path):
    regular = tmp_path / "regular"
    regular.write_bytes(b"preserve")
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        pipeline._directory_identity(regular)
    assert regular.read_bytes() == b"preserve"


@pytest.mark.skipif(os.name != "nt", reason="Junction nativa Windows")
def test_directory_identity_rejects_native_junction(tmp_path):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "control").write_bytes(b"preserve")
    alias = tmp_path / "alias"
    result = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(alias), str(foreign)],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    try:
        assert alias.is_junction()
        with pytest.raises(ValueError, match="UNSAFE_PATH"):
            pipeline._directory_identity(alias)
        assert (foreign / "control").read_bytes() == b"preserve"
        assert list(foreign.iterdir()) == [foreign / "control"]
    finally:
        os.rmdir(alias)


@pytest.mark.skipif(os.name != "nt", reason="FileId128 nativo Windows")
def test_native_empty_enumeration_preserves_directory_identity():
    directory = ROOT / ".cache" / ("directory-enumeration-" + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    before = pipeline._directory_identity(directory)
    native = _native_id(directory)
    try:
        with os.scandir(directory) as entries:
            assert list(entries) == []
        assert _native_id(directory) == native
        assert pipeline._directory_identity(directory) == before
    finally:
        directory.rmdir()


@pytest.mark.parametrize(
    "field,value",
    [
        ("st_file_attributes", 0x410),
        ("st_reparse_tag", 0x12345678),
        ("st_mode", 0o100600),
    ],
)
def test_identity_rejects_security_signal(tmp_path, monkeypatch, field, value):
    """Señales suplementarias: la identidad y sus positivas son nativas arriba."""
    from types import SimpleNamespace

    directory = tmp_path / "directory"
    directory.mkdir()
    actual = directory.lstat()
    fields = {
        name: getattr(actual, name, 0)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_file_attributes",
            "st_reparse_tag",
        )
    }
    fields[field] = value
    native_lstat = Path.lstat

    def altered(path, *args, **kwargs):
        return (
            SimpleNamespace(**fields)
            if path == directory
            else native_lstat(path, *args, **kwargs)
        )

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", altered)
        with pytest.raises(ValueError, match="UNSAFE_PATH"):
            pipeline._directory_identity(directory)


def test_identity_preserves_other_attribute_bits(tmp_path, monkeypatch):
    from types import SimpleNamespace

    directory = tmp_path / "directory"
    directory.mkdir()
    original = pipeline._directory_identity(directory)
    actual = directory.lstat()
    fields = {
        name: getattr(actual, name, 0)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_file_attributes",
            "st_reparse_tag",
        )
    }
    fields["st_file_attributes"] ^= 0x2
    native_lstat = Path.lstat

    def altered(path, *args, **kwargs):
        return (
            SimpleNamespace(**fields)
            if path == directory
            else native_lstat(path, *args, **kwargs)
        )

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", altered)
        assert pipeline._directory_identity(directory) != original
