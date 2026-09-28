from weights.hashing import sha256_file
from weights.verify import verify_file, verify_remote_code


def test_verify_file_ok_when_hash_matches(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"contenido correcto")
    digest = sha256_file(p)

    result = verify_file(p, digest, expected_bytes=p.stat().st_size)
    assert result.ok
    assert result.reason == ""


def test_verify_file_rejects_wrong_hash(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"contenido")
    result = verify_file(p, "0" * 64)
    assert not result.ok
    assert "sha256" in result.reason


def test_verify_file_rejects_wrong_size(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"contenido")
    digest = sha256_file(p)
    result = verify_file(p, digest, expected_bytes=999999)
    assert not result.ok
    assert "tamaño" in result.reason


def test_verify_file_missing(tmp_path):
    result = verify_file(tmp_path / "no-existe.bin", "0" * 64)
    assert not result.ok
    assert "no existe" in result.reason


def test_verify_uses_seal_after_first_check(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"contenido")
    digest = sha256_file(p)

    first = verify_file(p, digest)
    assert first.ok
    from weights.seal import seal_path

    assert seal_path(p).exists()

    second = verify_file(p, digest)
    assert second.ok


def test_verify_remote_code_rejects_hash_mismatch(tmp_path):
    py_file = tmp_path / "modeling_acestep_v15_turbo.py"
    py_file.write_text("# codigo remoto original\n", encoding="utf-8")
    original_hash = sha256_file(py_file)

    ok_result = verify_remote_code(py_file, original_hash)
    assert ok_result.ok

    # El repo remoto cambia el fichero sin avisar (o alguien lo modifica en disco):
    py_file.write_text("# codigo remoto MODIFICADO\n", encoding="utf-8")
    tampered_result = verify_remote_code(py_file, original_hash)
    assert not tampered_result.ok
    assert "sha256" in tampered_result.reason
