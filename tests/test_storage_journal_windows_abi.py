"""ABI nativa sin apertura de objetos; gates CPU separados."""

import importlib.util
import os
import pathlib
import platform
import sys
import types
import uuid

import pytest

WINDOWS_X64 = (
    os.name == "nt"
    and sys.platform == "win32"
    and sys.maxsize == 2**63 - 1
    and platform.machine().casefold() in {"amd64", "x86_64"}
)
native_windows = pytest.mark.skipif(
    not WINDOWS_X64, reason="Windows AMD64 real requerido; no positivo fingido"
)


def load():
    path = (
        pathlib.Path(__file__).resolve().parents[1]
        / "scripts/storage_journal_windows_abi.py"
    )
    key = "abi_" + uuid.uuid4().hex
    package = types.ModuleType(key)
    package.__path__ = [str(path.parent)]
    sys.modules[key] = package
    spec = importlib.util.spec_from_file_location(
        key + ".storage_journal_windows_abi", path
    )
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def test_unsupported_abi_gate(monkeypatch):
    m = load()
    monkeypatch.setattr(m.platform, "machine", lambda: "arm64")
    with pytest.raises(Exception, match="PLATFORM_UNSUPPORTED"):
        m._new_native_memory_backend()


@native_windows
def test_native_backend_complete_abi():
    m = load()
    backend = m._new_native_memory_backend()
    assert backend is not None
    assert all(
        callable(getattr(backend, field, None))
        for field in ("allocate", "release", "copy_in", "copy_out")
    )


def test_abi_widths_and_struct_offsets():
    import ctypes as c

    m = load()
    abi = m._build_abi(c)
    actual = (
        None
        if abi is None
        else {
            name: (
                c.sizeof(abi[name]),
                c.alignment(abi[name]),
                tuple(getattr(abi[name], field).offset for field in fields),
            )
            for name, fields in {
                "UNICODE_STRING": ("Length", "MaximumLength", "Buffer"),
                "OBJECT_ATTRIBUTES": (
                    "Length",
                    "RootDirectory",
                    "ObjectName",
                    "Attributes",
                    "SecurityDescriptor",
                    "SecurityQualityOfService",
                ),
                "IO_STATUS_BLOCK": ("u", "Information"),
            }.items()
        }
    )
    assert actual == {
        "UNICODE_STRING": (16, 8, (0, 2, 8)),
        "OBJECT_ATTRIBUTES": (48, 8, (0, 8, 16, 24, 32, 40)),
        "IO_STATUS_BLOCK": (16, 8, (0, 8)),
    }
    assert {
        name: c.sizeof(abi[name])
        for name in (
            "PVOID",
            "LONG",
            "ULONG",
            "USHORT",
            "WCHAR",
            "SIZE_T",
            "LARGE_INTEGER",
        )
    } == {
        "PVOID": 8,
        "LONG": 4,
        "ULONG": 4,
        "USHORT": 2,
        "WCHAR": 2,
        "SIZE_T": 8,
        "LARGE_INTEGER": 8,
    }


def test_binding_explicit_signature_and_missing():
    import ctypes as c

    m = load()
    function = types.SimpleNamespace()
    dll = types.SimpleNamespace(VirtualAlloc=function)
    result = m._bind_function(
        dll,
        "VirtualAlloc",
        (c.c_void_p, c.c_size_t, c.c_uint32, c.c_uint32),
        c.c_void_p,
    )
    assert result is function and getattr(function, "argtypes", None) == (
        c.c_void_p,
        c.c_size_t,
        c.c_uint32,
        c.c_uint32,
    )
    assert function.restype is c.c_void_p
    with pytest.raises(RuntimeError, match="ABI_UNACCREDITED"):
        m._bind_function(dll, "Missing", (), c.c_int32)


@native_windows
def test_invalid_width_rejects_before_dll(monkeypatch):
    import ctypes as c

    m = load()
    seen = []
    sizeof = c.sizeof
    monkeypatch.setattr(
        c, "sizeof", lambda typ: 4 if typ is c.c_void_p else sizeof(typ)
    )
    monkeypatch.setattr(c, "WinDLL", lambda *args, **kwargs: seen.append(args))
    with pytest.raises(RuntimeError, match="ABI_UNACCREDITED"):
        m._new_native_memory_backend()
    assert seen == []


@native_windows
def test_missing_symbol_rejects_before_allocate(monkeypatch):
    import ctypes as c

    m = load()
    calls = []

    def allocate(*args):
        calls.append(args)

    dll = types.SimpleNamespace(VirtualAlloc=allocate)
    monkeypatch.setattr(c, "WinDLL", lambda *args, **kwargs: dll)
    with pytest.raises(RuntimeError, match="ABI_UNACCREDITED"):
        m._new_native_memory_backend()
    assert calls == []


@pytest.mark.parametrize(
    "base,success,expected_error", [(65536, 2, None), (None, 0, 8)]
)
@native_windows
def test_closed_native_arguments_normalization(
    monkeypatch, base, success, expected_error
):
    import ctypes as c

    m = load()
    calls = []
    signatures = {}

    def alloc(*args):
        calls.append(("allocate", args))
        return base

    def free(*args):
        calls.append(("release", args))
        return success

    def future(*args):
        raise AssertionError("K1 nunca invoca NTIO")

    dll = types.SimpleNamespace(
        VirtualAlloc=alloc,
        VirtualFree=free,
        CloseHandle=future,
        FlushFileBuffers=future,
        NtCreateFile=future,
        NtReadFile=future,
        NtWriteFile=future,
    )
    monkeypatch.setattr(c, "WinDLL", lambda *args, **kwargs: dll)
    monkeypatch.setattr(
        c, "get_last_error", lambda: calls.append(("last_error", ())) or 8
    )
    old = m._bind_function

    def bind(dll, name, args, result):
        signatures[name] = (args, result)
        return old(dll, name, args, result)

    monkeypatch.setattr(m, "_bind_function", bind)
    backend = m._new_native_memory_backend()
    result = None if backend is None else backend.allocate(1023)
    observed = None if result is None else (result.base, result.win32_error)
    assert observed == (base, expected_error)
    released = backend.release(65536)
    assert (released.success, released.win32_error) == (bool(success), expected_error)
    assert calls == (
        [("allocate", (None, 1023, 0x3000, 4)), ("release", (65536, 0, 0x8000))]
        if base
        else [
            ("allocate", (None, 1023, 0x3000, 4)),
            ("last_error", ()),
            ("release", (65536, 0, 0x8000)),
            ("last_error", ()),
        ]
    )
    assert set(signatures) == {
        "VirtualAlloc",
        "VirtualFree",
        "CloseHandle",
        "FlushFileBuffers",
        "NtCreateFile",
        "NtReadFile",
        "NtWriteFile",
    }
    assert [
        len(signatures[name][0])
        for name in ("NtCreateFile", "NtReadFile", "NtWriteFile")
    ] == [11, 9, 9]
    assert signatures["VirtualAlloc"] == (
        (c.c_void_p, c.c_size_t, c.c_uint32, c.c_uint32),
        c.c_void_p,
    )
    assert signatures["VirtualFree"] == (
        (c.c_void_p, c.c_size_t, c.c_uint32),
        c.c_int32,
    )
    abi = m._build_abi(c)
    p = c.c_void_p
    u = c.c_uint32
    iosb = c.POINTER(abi["IO_STATUS_BLOCK"])
    large = c.POINTER(c.c_int64)
    # Clases ABI distintas por build; inspeccionar tipos apuntados por layout.
    create = signatures["NtCreateFile"][0]
    assert create[0] == c.POINTER(p) and create[1] == u
    assert c.sizeof(create[2]._type_) == 48 and c.sizeof(create[3]._type_) == 16
    assert create[4:] == (large, u, u, u, u, p, u)
    for name in ("NtReadFile", "NtWriteFile"):
        args, restype = signatures[name]
        assert args[:4] == (p, p, p, p) and c.sizeof(args[4]._type_) == 16
        assert args[5:] == (p, u, large, c.POINTER(u)) and restype is c.c_int32
    assert c.sizeof(iosb._type_) == 16


def test_binding_ignores_signature_rejected():
    import ctypes as c

    m = load()

    class Broken:
        @property
        def argtypes(self):
            return ()

        @argtypes.setter
        def argtypes(self, value):
            pass

    with pytest.raises(RuntimeError, match="ABI_UNACCREDITED"):
        m._bind_function(
            types.SimpleNamespace(VirtualFree=Broken()),
            "VirtualFree",
            (c.c_void_p, c.c_size_t, c.c_uint32),
            c.c_int32,
        )
