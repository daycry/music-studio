from weights.hashing import sha256_bytes, sha256_file


def test_sha256_file_matches_known_vector(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hola mundo")
    # sha256("hola mundo") calculado independientemente
    assert sha256_file(p) == sha256_bytes(b"hola mundo")
    import hashlib

    assert sha256_file(p) == hashlib.sha256(b"hola mundo").hexdigest()


def test_sha256_file_streams_large_content(tmp_path):
    p = tmp_path / "big.bin"
    chunk = b"x" * 1024
    with open(p, "wb") as f:
        f.writelines(chunk for _ in range(20000))  # ~20 MB, fuerza streaming
    import hashlib

    h = hashlib.sha256()
    h.update(chunk * 20000)
    assert sha256_file(p, chunk_size=8192) == h.hexdigest()
