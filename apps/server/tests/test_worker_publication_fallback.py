"""Publicación sencilla (ADR-0089 §2): renameat2 si existe, si no ausencia + rename."""

import errno
import os

import pytest
from app.worker import publications


def _tree(tmp_path):
    source = tmp_path / "owned-source"
    source.mkdir()
    (source / "owned").write_bytes(b"own bytes")
    return source, tmp_path / "final"


@pytest.mark.parametrize("code", [errno.EINVAL, errno.ENOSYS])
def test_rename_noreplace_falls_back_when_native_is_unsupported(
    tmp_path, monkeypatch, code
):
    source, destination = _tree(tmp_path)

    def unsupported(*_args):
        raise OSError(code, os.strerror(code))

    monkeypatch.setattr(publications, "_native_noreplace", unsupported)
    publications.rename_noreplace(source, destination)
    assert (destination / "owned").read_bytes() == b"own bytes"
    assert not source.exists()


@pytest.mark.parametrize("foreign_kind", ["empty_directory", "directory", "file"])
def test_fallback_preserves_foreign_destination(tmp_path, monkeypatch, foreign_kind):
    source, destination = _tree(tmp_path)
    if foreign_kind == "file":
        destination.write_bytes(b"foreign bytes")
    else:
        destination.mkdir()
        if foreign_kind == "directory":
            (destination / "witness").write_bytes(b"foreign bytes")

    def unsupported(*_args):
        raise OSError(errno.EINVAL, "EINVAL")

    monkeypatch.setattr(publications, "_native_noreplace", unsupported)
    before = destination.stat().st_ino
    with pytest.raises(OSError) as caught:
        publications.rename_noreplace(source, destination)
    assert caught.value.errno == errno.EEXIST
    assert destination.stat().st_ino == before
    assert (source / "owned").read_bytes() == b"own bytes"
    if foreign_kind == "directory":
        assert (destination / "witness").read_bytes() == b"foreign bytes"
    elif foreign_kind == "empty_directory":
        assert list(destination.iterdir()) == []


def test_native_eexist_is_not_retried_with_fallback(tmp_path, monkeypatch):
    source, destination = _tree(tmp_path)

    def exists(*_args):
        raise OSError(errno.EEXIST, "EEXIST")

    def boom(*_args):
        raise AssertionError("fallback must not run")

    monkeypatch.setattr(publications, "_native_noreplace", exists)
    monkeypatch.setattr(os, "rename", boom)
    with pytest.raises(OSError) as caught:
        publications.rename_noreplace(source, destination)
    assert caught.value.errno == errno.EEXIST
