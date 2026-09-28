import struct

import numpy as np
import pytest
from safetensors.numpy import load_file as safetensors_load_file
from weights.convert import ConversionError, convert_torch_pickle_zip
from weights.safetensors_format import read_safetensors_header

from .pickle_fixtures import (
    build_single_tensor_pickle,
    build_state_dict_pickle,
    write_torch_zip,
)


def test_convert_single_tensor_pickle_roundtrip(tmp_path):
    values = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype="float32")
    data_pkl = build_single_tensor_pickle("0", "cpu", numel=values.size, size=values.shape, stride=(3, 1))
    src = tmp_path / "silence_latent.pt"
    write_torch_zip(src, "silence_latent", data_pkl, {"0": values.tobytes()})

    dest = tmp_path / "silence_latent.safetensors"
    result = convert_torch_pickle_zip(src, dest)

    assert result.tensor_count == 1
    assert dest.exists()
    assert result.sha256_converted != result.sha256_original

    loaded = safetensors_load_file(str(dest))
    assert set(loaded.keys()) == {"tensor"}
    np.testing.assert_array_equal(loaded["tensor"], values)


def test_convert_state_dict_pickle_with_multiple_tensors(tmp_path):
    values = np.arange(6, dtype="float32")
    data_pkl = build_state_dict_pickle(
        ["layer.weight", "layer.bias"], storage_key="0", numel=6, size=(6,), stride=(1,)
    )
    src = tmp_path / "pytorch_model.bin"
    write_torch_zip(src, "pytorch_model", data_pkl, {"0": values.tobytes()})

    dest = tmp_path / "pytorch_model.safetensors"
    result = convert_torch_pickle_zip(src, dest)

    assert result.tensor_count == 2
    header = read_safetensors_header(dest)
    assert "layer.weight" in header and "layer.bias" in header

    loaded = safetensors_load_file(str(dest))
    np.testing.assert_array_equal(loaded["layer.weight"], values)
    np.testing.assert_array_equal(loaded["layer.bias"], values)


def test_convert_rejects_truncated_storage(tmp_path):
    data_pkl = build_single_tensor_pickle("0", "cpu", numel=6, size=(2, 3), stride=(3, 1))
    src = tmp_path / "bad.pt"
    # Solo 3 floats en vez de los 6 que numel/size anuncian.
    write_torch_zip(src, "bad", data_pkl, {"0": struct.pack("<3f", 1.0, 2.0, 3.0)})

    with pytest.raises(ConversionError, match="truncado"):
        convert_torch_pickle_zip(src, tmp_path / "bad.safetensors")


def test_convert_hashes_match_recomputation(tmp_path):
    import hashlib

    values = np.array([1.0, 2.0], dtype="float32")
    data_pkl = build_single_tensor_pickle("0", "cpu", numel=2, size=(2,), stride=(1,))
    src = tmp_path / "t.pt"
    write_torch_zip(src, "t", data_pkl, {"0": values.tobytes()})
    dest = tmp_path / "t.safetensors"

    result = convert_torch_pickle_zip(src, dest)

    assert result.sha256_original == hashlib.sha256(src.read_bytes()).hexdigest()
    assert result.sha256_converted == hashlib.sha256(dest.read_bytes()).hexdigest()
    assert result.bytes_original == src.stat().st_size
    assert result.bytes_converted == dest.stat().st_size
