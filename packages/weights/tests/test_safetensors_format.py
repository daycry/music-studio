import numpy as np
from safetensors.numpy import load_file as safetensors_load_file
from weights.safetensors_format import (
    TensorEntry,
    read_safetensors_header,
    write_safetensors,
)


def test_write_safetensors_readable_by_real_library(tmp_path):
    a = np.array([1.0, 2.0, 3.0], dtype="float32")
    b = np.array([[1, 2], [3, 4]], dtype="int64")
    tensors = {
        "a": TensorEntry(dtype="F32", shape=a.shape, data=a.tobytes()),
        "b": TensorEntry(dtype="I64", shape=b.shape, data=b.tobytes()),
    }
    dest = tmp_path / "out.safetensors"
    write_safetensors(tensors, dest)

    loaded = safetensors_load_file(str(dest))
    np.testing.assert_array_equal(loaded["a"], a)
    np.testing.assert_array_equal(loaded["b"], b)


def test_write_safetensors_bf16_header_roundtrip(tmp_path):
    # numpy no tiene bfloat16: guardamos 4 valores como bytes crudos uint16 y
    # verificamos que la cabecera declara BF16 con el shape correcto (no
    # podemos usar safetensors.numpy para leer BF16, así que comprobamos la
    # cabecera a mano, que es justo lo que escribe nuestro writer).
    raw = (0x3F80).to_bytes(2, "little") * 4  # 4 elementos "bf16" cualquiera
    tensors = {"w": TensorEntry(dtype="BF16", shape=(4,), data=raw)}
    dest = tmp_path / "bf16.safetensors"
    write_safetensors(tensors, dest)

    header = read_safetensors_header(dest)
    assert header["w"]["dtype"] == "BF16"
    assert header["w"]["shape"] == [4]

    with open(dest, "rb") as f:
        import struct

        (n,) = struct.unpack("<Q", f.read(8))
        f.seek(8 + n + header["w"]["data_offsets"][0])
        assert f.read(len(raw)) == raw


def test_write_safetensors_rejects_size_mismatch(tmp_path):
    import pytest

    tensors = {"a": TensorEntry(dtype="F32", shape=(3,), data=b"\x00" * 4)}  # faltan bytes
    with pytest.raises(ValueError, match="inconsistente"):
        write_safetensors(tensors, tmp_path / "bad.safetensors")
