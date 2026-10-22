"""Regresión real de la caché Triton con la configuración de la imagen."""

import os
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.mark.skipif(
    os.environ.get("STUDIO_ENGINE_CONTAINER") != "1",
    reason="requiere el usuario y la configuración de la imagen del engine",
)
def test_triton_default_cache_is_writable_by_runtime_user():
    from triton.runtime.cache import FileCacheManager

    assert os.getuid() == 10001
    manager = FileCacheManager(uuid4().hex)
    payload = b"analysis-runtime-cache-regression"
    written = manager.put(payload, "runtime-probe.bin", binary=True)
    cached = manager.get_file("runtime-probe.bin")
    assert cached == written
    assert Path(cached).read_bytes() == payload
    assert os.environ["TRITON_CACHE_DIR"] == "/studio/.cache/triton"
    assert Path(cached).is_relative_to(Path("/studio/.cache/triton"))
    assert os.stat("/studio/.cache/triton").st_uid == 10001
    assert os.stat("/studio/.cache/triton").st_mode & 0o777 == 0o755
