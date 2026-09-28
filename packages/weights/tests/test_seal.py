import time

from weights.seal import read_seal, seal_path, verified_sha256


def test_write_and_read_seal_roundtrip(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"contenido")
    digest = verified_sha256(p)
    assert seal_path(p).exists()
    seal = read_seal(p)
    assert seal is not None
    assert seal.sha256 == digest
    assert seal.size == p.stat().st_size


def test_verified_sha256_reuses_seal_without_recomputing(tmp_path, monkeypatch):
    p = tmp_path / "f.bin"
    p.write_bytes(b"contenido")
    first = verified_sha256(p)

    calls = {"n": 0}
    import weights.seal as seal_mod

    real_sha256_file = seal_mod.sha256_file

    def counting_sha256_file(path, *a, **k):
        calls["n"] += 1
        return real_sha256_file(path, *a, **k)

    monkeypatch.setattr(seal_mod, "sha256_file", counting_sha256_file)

    second = verified_sha256(p)
    assert second == first
    assert calls["n"] == 0  # el sello coincide: no se recalcula


def test_verified_sha256_recomputes_when_seal_stale(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"v1")
    digest_v1 = verified_sha256(p)

    time.sleep(0.01)
    p.write_bytes(b"v2 con contenido distinto")
    digest_v2 = verified_sha256(p)

    assert digest_v1 != digest_v2
    seal = read_seal(p)
    assert seal.sha256 == digest_v2


def test_read_seal_missing_returns_none(tmp_path):
    p = tmp_path / "no-existe.bin"
    assert read_seal(p) is None
