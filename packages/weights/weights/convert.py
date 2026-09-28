"""Conversor de pickle de PyTorch (formato zip de `torch.save`) a `.safetensors`
(ADR-0006 §3). Sin torch, sin `pickle.load` directo: usa `audit_pickle` para las
dos pasadas y `numpy` solo para el reshape/stride de los storages (nunca para
interpretar el pickle).

Formato zip de `torch.save` (versión >= 1.6, la que usan todos los repos de
esta tarea): un `.pt`/`.bin`/`.ckpt` es un zip con un prefijo (el nombre del
fichero sin extensión, p.ej. `silence_latent/`, `pytorch_model/`, `final0/`):
  `<prefijo>/data.pkl`      — el pickle con el grafo de objetos
  `<prefijo>/data/<key>`    — bytes crudos de cada storage, referenciados desde
                               `data.pkl` vía `persistent_id`
  `<prefijo>/byteorder`     — "little" o "big" (verificado contra el propio
                               `sys.byteorder`; si no coincide, no convertimos:
                               no hay ningún fichero real de esta tarea en big
                               endian y no merece la pena arriesgar una
                               conversión silenciosa mal hecha)
  `<prefijo>/version`       — versión del formato de serialización (informativa)

Verificado con los tres pickle reales de T-02 (ver notas en `audit_pickle.py`).
"""

from __future__ import annotations

import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .audit_pickle import _STORAGE_DTYPES, _StorageRef, _TensorRef, load_restricted
from .hashing import sha256_file
from .safetensors_format import TensorEntry, write_safetensors

# numpy no tiene bfloat16: para el resize/stride lo tratamos como uint16 (mismo
# tamaño en memoria) y solo al final se etiqueta como "BF16" en la cabecera de
# safetensors (ver safetensors_format.py).
_STORAGE_NUMPY_DTYPE: dict[str, str] = {
    "FloatStorage": "float32",
    "HalfStorage": "float16",
    "BFloat16Storage": "uint16",
    "DoubleStorage": "float64",
    "LongStorage": "int64",
    "IntStorage": "int32",
    "ShortStorage": "int16",
    "ByteStorage": "uint8",
    "BoolStorage": "bool",
}

_STORAGE_SAFETENSORS_DTYPE: dict[str, str] = {
    "FloatStorage": "F32",
    "HalfStorage": "F16",
    "BFloat16Storage": "BF16",
    "DoubleStorage": "F64",
    "LongStorage": "I64",
    "IntStorage": "I32",
    "ShortStorage": "I16",
    "ByteStorage": "U8",
    "BoolStorage": "BOOL",
}


class ConversionError(ValueError):
    pass


@dataclass(frozen=True)
class ConversionResult:
    sha256_original: str
    bytes_original: int
    sha256_converted: str
    bytes_converted: int
    tensor_count: int


def _find_prefix(zf: zipfile.ZipFile) -> str:
    for name in zf.namelist():
        if name.endswith("/data.pkl"):
            return name[: -len("/data.pkl")]
    raise ConversionError("no se encontró <prefijo>/data.pkl en el zip")


def _materialize_tensor(ref: _TensorRef) -> TensorEntry:
    storage = ref.storage
    np_dtype = _STORAGE_NUMPY_DTYPE.get(storage.dtype_name)
    st_dtype = _STORAGE_SAFETENSORS_DTYPE.get(storage.dtype_name)
    if np_dtype is None or st_dtype is None:
        raise ConversionError(f"storage sin dtype mapeado: {storage.dtype_name}")

    itemsize = np.dtype(np_dtype).itemsize
    flat = np.frombuffer(storage.data, dtype=np_dtype)
    if flat.size < storage.numel:
        raise ConversionError(
            f"storage truncado: {flat.size} elementos, se esperaban {storage.numel}"
        )

    n_elements = 1
    for dim in ref.size:
        n_elements *= dim

    if n_elements == 0:
        contiguous = np.empty((0,), dtype=np_dtype)
    else:
        byte_strides = tuple(s * itemsize for s in ref.stride)
        windowed = np.lib.stride_tricks.as_strided(
            flat[ref.storage_offset :],
            shape=ref.size,
            strides=byte_strides,
            writeable=False,
        )
        contiguous = np.ascontiguousarray(windowed)

    return TensorEntry(dtype=st_dtype, shape=tuple(ref.size), data=contiguous.tobytes())


def _walk_state_dict(obj: Any, prefix: str = "") -> dict[str, _TensorRef]:
    """El objeto de nivel superior puede ser: un `_TensorRef` suelto (p.ej.
    `silence_latent.pt`, un único tensor), un dict de tensores (state_dict), o
    un dict con metadatos de Lightning donde `state_dict` es, a su vez, ese
    dict de tensores (extraemos SOLO esa clave, ADR-0006 §3).
    """
    if isinstance(obj, _TensorRef):
        return {"tensor" if not prefix else prefix: obj}
    if isinstance(obj, dict):
        if all(isinstance(v, _TensorRef) for v in obj.values()) and obj:
            return dict(obj)
        if "state_dict" in obj and isinstance(obj["state_dict"], dict):
            return _walk_state_dict(obj["state_dict"])
        raise ConversionError(
            "no se encontró un state_dict de tensores en el pickle "
            "(ni el objeto raíz ni obj['state_dict'] lo son)"
        )
    raise ConversionError(f"estructura de pickle no soportada: {type(obj)!r}")


def convert_torch_pickle_zip(src_path: str | Path, dest_path: str | Path) -> ConversionResult:
    """Convierte un `.pt`/`.bin`/`.ckpt` (zip de `torch.save`) a `.safetensors`.
    Devuelve los hashes de origen y destino para el lock (ADR-0006 §3, §6).
    """
    src_path = Path(src_path)
    dest_path = Path(dest_path)
    sha256_original = sha256_file(src_path)
    bytes_original = src_path.stat().st_size

    with zipfile.ZipFile(src_path) as zf:
        prefix = _find_prefix(zf)
        try:
            byteorder = zf.read(f"{prefix}/byteorder").decode("ascii").strip()
        except KeyError:
            byteorder = sys.byteorder
        if byteorder != sys.byteorder:
            raise ConversionError(
                f"byteorder del pickle ({byteorder}) distinto del de esta máquina "
                f"({sys.byteorder}); conversión no soportada"
            )

        def storage_reader(dtype_name: str, key: str, numel: int, location: str) -> _StorageRef:
            if dtype_name not in _STORAGE_DTYPES:
                raise ConversionError(f"storage no soportado: {dtype_name}")
            raw = zf.read(f"{prefix}/data/{key}")
            return _StorageRef(key=key, location=location, numel=numel, dtype_name=dtype_name, data=raw)

        data_pkl = zf.read(f"{prefix}/data.pkl")
        top_obj = load_restricted(data_pkl, storage_reader)

    tensor_refs = _walk_state_dict(top_obj)
    tensors = {name: _materialize_tensor(ref) for name, ref in tensor_refs.items()}

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    write_safetensors(tensors, dest_path, metadata={"converted_from": src_path.name})

    sha256_converted = sha256_file(dest_path)
    bytes_converted = dest_path.stat().st_size

    return ConversionResult(
        sha256_original=sha256_original,
        bytes_original=bytes_original,
        sha256_converted=sha256_converted,
        bytes_converted=bytes_converted,
        tensor_count=len(tensors),
    )
