"""Construye pickle de prueba a mano, opcode a opcode, replicando exactamente
la estructura que usa `torch.save` (protocolo 2), verificada contra los tres
pickle reales de la tarea (ver `audit_pickle.py`). No depende de torch ni de
red: es pura construcción de bytes.
"""

from __future__ import annotations

import io
import zipfile


def _proto(n: int) -> bytes:
    return b"\x80" + bytes([n])


def _mark() -> bytes:
    return b"("


def _global(module: str, name: str) -> bytes:
    return b"c" + module.encode() + b"\n" + name.encode() + b"\n"


def _binunicode(s: str) -> bytes:
    b = s.encode("utf-8")
    return b"X" + len(b).to_bytes(4, "little") + b


def _binint(n: int) -> bytes:
    if 0 <= n < 256:
        return b"K" + bytes([n])
    if 0 <= n < 65536:
        return b"M" + n.to_bytes(2, "little")
    return b"J" + n.to_bytes(4, "little", signed=True)


def _tuple() -> bytes:
    return b"t"


def _tuple1() -> bytes:
    return b"\x85"


def _tuple3() -> bytes:
    return b"\x87"


def _empty_tuple() -> bytes:
    return b")"


def _empty_dict() -> bytes:
    return b"}"


def _reduce() -> bytes:
    return b"R"


def _binpersid() -> bytes:
    return b"Q"


def _newfalse() -> bytes:
    return b"\x89"


def _binput(n: int) -> bytes:
    return b"q" + bytes([n])


def _setitems() -> bytes:
    return b"u"


def _stop() -> bytes:
    return b"."


def build_single_tensor_pickle(storage_key: str, location: str, numel: int, size, stride) -> bytes:
    """Un único tensor de nivel superior, como `silence_latent.pt`."""
    out = io.BytesIO()
    out.write(_proto(2))
    out.write(_global("torch._utils", "_rebuild_tensor_v2"))
    out.write(_binput(0))
    out.write(_mark())
    out.write(_mark())
    out.write(_binunicode("storage"))
    out.write(_binput(1))
    out.write(_global("torch", "FloatStorage"))
    out.write(_binput(2))
    out.write(_binunicode(storage_key))
    out.write(_binput(3))
    out.write(_binunicode(location))
    out.write(_binput(4))
    out.write(_binint(numel))
    out.write(_tuple())
    out.write(_binput(5))
    out.write(_binpersid())
    out.write(_binint(0))  # storage_offset
    if len(size) == 1:
        out.write(_binint(size[0]))
        out.write(_tuple1())
    elif len(size) == 3:
        for dim in size:
            out.write(_binint(dim))
        out.write(_tuple3())
    else:
        out.write(_mark())
        for dim in size:
            out.write(_binint(dim))
        out.write(_tuple())
    out.write(_binput(6))
    if len(stride) == 1:
        out.write(_binint(stride[0]))
        out.write(_tuple1())
    elif len(stride) == 3:
        for dim in stride:
            out.write(_binint(dim))
        out.write(_tuple3())
    else:
        out.write(_mark())
        for dim in stride:
            out.write(_binint(dim))
        out.write(_tuple())
    out.write(_binput(7))
    out.write(_newfalse())
    out.write(_global("collections", "OrderedDict"))
    out.write(_binput(8))
    out.write(_empty_tuple())
    out.write(_reduce())
    out.write(_binput(9))
    out.write(_tuple())
    out.write(_binput(10))
    out.write(_reduce())
    out.write(_binput(11))
    out.write(_stop())
    return out.getvalue()


def build_state_dict_pickle(tensor_names: list[str], storage_key: str, numel: int, size, stride) -> bytes:
    """Un `OrderedDict` de nivel superior con varios tensores que comparten un
    mismo storage sintético, como `pytorch_model.bin`/`final0.ckpt`.
    """
    out = io.BytesIO()
    out.write(_proto(2))
    out.write(_global("collections", "OrderedDict"))
    out.write(_binput(0))
    out.write(_empty_tuple())
    out.write(_reduce())
    out.write(_binput(1))
    out.write(_mark())
    put_n = 2
    for name in tensor_names:
        out.write(_binunicode(name))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_global("torch._utils", "_rebuild_tensor_v2"))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_mark())
        out.write(_mark())
        out.write(_binunicode("storage"))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_global("torch", "FloatStorage"))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_binunicode(storage_key))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_binunicode("cpu"))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_binint(numel))
        out.write(_tuple())
        out.write(_binput(put_n))
        put_n += 1
        out.write(_binpersid())
        out.write(_binint(0))
        for dim in size:
            out.write(_binint(dim))
        out.write(_tuple1() if len(size) == 1 else _tuple3())
        out.write(_binput(put_n))
        put_n += 1
        for dim in stride:
            out.write(_binint(dim))
        out.write(_tuple1() if len(stride) == 1 else _tuple3())
        out.write(_binput(put_n))
        put_n += 1
        out.write(_newfalse())
        out.write(_global("collections", "OrderedDict"))
        out.write(_binput(put_n))
        put_n += 1
        out.write(_empty_tuple())
        out.write(_reduce())
        out.write(_binput(put_n))
        put_n += 1
        out.write(_tuple())
        out.write(_binput(put_n))
        put_n += 1
        out.write(_reduce())
        out.write(_binput(put_n))
        put_n += 1
    out.write(_setitems())
    out.write(_stop())
    return out.getvalue()


def build_malicious_pickle() -> bytes:
    """`os.system('...')` vía REDUCE. El auditor debe rechazarlo por el GLOBAL
    `os system`, sin llegar nunca a ejecutar nada (ni en la pasada estática ni
    en la reconstrucción).
    """
    out = io.BytesIO()
    out.write(_proto(2))
    out.write(_global("os", "system"))
    out.write(_binunicode("echo pwned"))
    out.write(_tuple1())
    out.write(_reduce())
    out.write(_stop())
    return out.getvalue()


def build_malicious_builtins_eval_pickle() -> bytes:
    out = io.BytesIO()
    out.write(_proto(2))
    out.write(_global("builtins", "eval"))
    out.write(_binunicode("__import__('os').system('echo pwned')"))
    out.write(_tuple1())
    out.write(_reduce())
    out.write(_stop())
    return out.getvalue()


def write_torch_zip(path, prefix: str, data_pkl: bytes, storages: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(f"{prefix}/data.pkl", data_pkl)
        zf.writestr(f"{prefix}/byteorder", b"little")
        zf.writestr(f"{prefix}/version", b"3\n")
        for key, raw in storages.items():
            zf.writestr(f"{prefix}/data/{key}", raw)
