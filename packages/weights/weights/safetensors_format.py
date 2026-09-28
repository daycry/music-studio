"""Escritor de `.safetensors` propio, a mano (ADR-0006 §3).

`safetensors.numpy.save_file` no admite BF16 (numpy no tiene ese dtype), y los
storages de ACE-Step (`silence_latent.pt`) pueden venir en BF16. En vez de tener
dos caminos (uno con `safetensors.numpy` para los dtypes "normales" y otro a
mano para BF16), este módulo escribe siempre el formato a mano: es un formato
simple y documentado (https://github.com/huggingface/safetensors#format) y así
un mismo fichero puede mezclar tensores BF16 con otros dtypes sin depender de
qué acepte la API de turno.

Formato: 8 bytes little-endian con el tamaño N de la cabecera, N bytes de JSON
UTF-8 (`{nombre: {"dtype", "shape", "data_offsets": [inicio, fin]}, ...}`, con
`"__metadata__"` opcional), y a continuación los bytes crudos de cada tensor en
el orden de sus `data_offsets`.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path

# Nombre de dtype de safetensors -> bytes por elemento.
DTYPE_ITEMSIZE: dict[str, int] = {
    "F64": 8,
    "F32": 4,
    "F16": 2,
    "BF16": 2,
    "I64": 8,
    "I32": 4,
    "I16": 2,
    "I8": 1,
    "U8": 1,
    "BOOL": 1,
}


@dataclass(frozen=True)
class TensorEntry:
    dtype: str  # clave de DTYPE_ITEMSIZE
    shape: tuple[int, ...]
    data: bytes  # bytes crudos, C-contiguos, en el dtype declarado


def write_safetensors(
    tensors: dict[str, TensorEntry], path: str | Path, metadata: dict[str, str] | None = None
) -> None:
    if tensors:
        for name, entry in tensors.items():
            if entry.dtype not in DTYPE_ITEMSIZE:
                raise ValueError(f"dtype no soportado en {name!r}: {entry.dtype}")
            expected = DTYPE_ITEMSIZE[entry.dtype]
            for dim in entry.shape:
                expected *= dim
            if len(entry.data) != expected:
                raise ValueError(
                    f"tamaño de datos inconsistente en {name!r}: "
                    f"{len(entry.data)} bytes, esperados {expected}"
                )

    header: dict[str, object] = {}
    if metadata:
        header["__metadata__"] = metadata

    offset = 0
    blobs: list[bytes] = []
    for name in sorted(tensors):  # orden determinista
        entry = tensors[name]
        start = offset
        end = offset + len(entry.data)
        header[name] = {
            "dtype": entry.dtype,
            "shape": list(entry.shape),
            "data_offsets": [start, end],
        }
        blobs.append(entry.data)
        offset = end

    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    # El propio formato pide alinear el inicio de datos: se rellena con espacios
    # ASCII (válidos en JSON entre tokens) hasta múltiplo de 8 si hace falta.
    pad = (-len(header_json)) % 8
    header_json += b" " * pad

    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(header_json)))
        f.write(header_json)
        f.writelines(blobs)


def read_safetensors_header(path: str | Path) -> dict:
    """Lee solo la cabecera (para tests/verificación), sin depender de la
    librería `safetensors`.
    """
    with open(path, "rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        header = json.loads(f.read(n).decode("utf-8"))
    return header
