"""Binding Windows AMD64 tardío; únicamente memoria propia invocable en K1."""

import os
import platform
import sys
from typing import ClassVar


def _new_native_memory_backend():
    if not (
        os.name == "nt"
        and sys.platform == "win32"
        and sys.maxsize == 2**63 - 1
        and platform.machine().casefold() in {"amd64", "x86_64"}
    ):
        raise RuntimeError("PLATFORM_UNSUPPORTED") from None
    import ctypes as c

    from .storage_journal_windows_io import _AllocResult, _BoolResult, _MemoryOps

    try:
        abi = _build_abi(c)
        kernel = c.WinDLL("kernel32", use_last_error=True)
        nt = c.WinDLL("ntdll", use_last_error=True)
        pointer = abi["PVOID"]
        size = abi["SIZE_T"]
        ulong = abi["ULONG"]
        long = abi["LONG"]
        handle_pointer = c.POINTER(pointer)
        iosb_pointer = c.POINTER(abi["IO_STATUS_BLOCK"])
        offset_pointer = c.POINTER(abi["LARGE_INTEGER"])
        bindings = {
            "VirtualAlloc": _bind_function(
                kernel, "VirtualAlloc", (pointer, size, ulong, ulong), pointer
            ),
            "VirtualFree": _bind_function(
                kernel, "VirtualFree", (pointer, size, ulong), long
            ),
            "CloseHandle": _bind_function(kernel, "CloseHandle", (pointer,), long),
            "FlushFileBuffers": _bind_function(
                kernel, "FlushFileBuffers", (pointer,), long
            ),
            "NtCreateFile": _bind_function(
                nt,
                "NtCreateFile",
                (
                    handle_pointer,
                    ulong,
                    c.POINTER(abi["OBJECT_ATTRIBUTES"]),
                    iosb_pointer,
                    offset_pointer,
                    ulong,
                    ulong,
                    ulong,
                    ulong,
                    pointer,
                    ulong,
                ),
                long,
            ),
            "NtReadFile": _bind_function(
                nt,
                "NtReadFile",
                (
                    pointer,
                    pointer,
                    pointer,
                    pointer,
                    iosb_pointer,
                    pointer,
                    ulong,
                    offset_pointer,
                    c.POINTER(ulong),
                ),
                long,
            ),
            "NtWriteFile": _bind_function(
                nt,
                "NtWriteFile",
                (
                    pointer,
                    pointer,
                    pointer,
                    pointer,
                    iosb_pointer,
                    pointer,
                    ulong,
                    offset_pointer,
                    c.POINTER(ulong),
                ),
                long,
            ),
        }
    except Exception:  # noqa: BLE001 - diagnostico cerrado sin chaining
        raise RuntimeError("ABI_UNACCREDITED") from None

    def allocate(size_bytes):
        base = bindings["VirtualAlloc"](None, size_bytes, 0x3000, 0x4)
        if not base:
            error = c.get_last_error()
            return _AllocResult(None, error)
        return _AllocResult(base, None)

    def release(base):
        success = bindings["VirtualFree"](base, 0, 0x8000)
        if not success:
            error = c.get_last_error()
            return _BoolResult(False, error)
        return _BoolResult(True, None)

    def copy_in(address, data):
        c.memmove(address, data, len(data))

    def copy_out(address, length):
        return c.string_at(address, length)

    return _MemoryOps(allocate, release, copy_in, copy_out)


def _build_abi(c):
    pointer = c.c_void_p
    long = c.c_int32
    ulong = c.c_uint32
    ushort = c.c_uint16
    size = c.c_size_t

    class UNICODE_STRING(c.Structure):
        _fields_: ClassVar[list] = [
            ("Length", ushort),
            ("MaximumLength", ushort),
            ("Buffer", pointer),
        ]

    class OBJECT_ATTRIBUTES(c.Structure):
        _fields_: ClassVar[list] = [
            ("Length", ulong),
            ("RootDirectory", pointer),
            ("ObjectName", pointer),
            ("Attributes", ulong),
            ("SecurityDescriptor", pointer),
            ("SecurityQualityOfService", pointer),
        ]

    class STATUS_UNION(c.Union):
        _fields_: ClassVar[list] = [("Status", long), ("Pointer", pointer)]

    class IO_STATUS_BLOCK(c.Structure):
        _fields_: ClassVar[list] = [("u", STATUS_UNION), ("Information", size)]

    abi = {
        "PVOID": pointer,
        "LONG": long,
        "ULONG": ulong,
        "USHORT": ushort,
        "WCHAR": ushort,
        "SIZE_T": size,
        "LARGE_INTEGER": c.c_int64,
        "UNICODE_STRING": UNICODE_STRING,
        "OBJECT_ATTRIBUTES": OBJECT_ATTRIBUTES,
        "STATUS_UNION": STATUS_UNION,
        "IO_STATUS_BLOCK": IO_STATUS_BLOCK,
    }
    widths = {
        "PVOID": 8,
        "LONG": 4,
        "ULONG": 4,
        "USHORT": 2,
        "WCHAR": 2,
        "SIZE_T": 8,
        "LARGE_INTEGER": 8,
        "UNICODE_STRING": 16,
        "OBJECT_ATTRIBUTES": 48,
        "STATUS_UNION": 8,
        "IO_STATUS_BLOCK": 16,
    }
    offsets = {
        "UNICODE_STRING": {"Length": 0, "MaximumLength": 2, "Buffer": 8},
        "OBJECT_ATTRIBUTES": {
            "Length": 0,
            "RootDirectory": 8,
            "ObjectName": 16,
            "Attributes": 24,
            "SecurityDescriptor": 32,
            "SecurityQualityOfService": 40,
        },
        "STATUS_UNION": {"Status": 0, "Pointer": 0},
        "IO_STATUS_BLOCK": {"u": 0, "Information": 8},
    }
    if (
        any(c.sizeof(abi[name]) != width for name, width in widths.items())
        or any(c.alignment(abi[name]) != 8 for name in offsets)
        or any(
            getattr(abi[name], field).offset != offset
            for name, fields in offsets.items()
            for field, offset in fields.items()
        )
    ):
        raise RuntimeError("ABI_UNACCREDITED") from None
    return abi


def _bind_function(dll, name, args, result):
    try:
        function = getattr(dll, name)
        function.argtypes = args
        function.restype = result
        if function.argtypes != args or function.restype is not result:
            raise ValueError()
        return function
    except Exception:  # noqa: BLE001 - diagnostico cerrado sin chaining
        raise RuntimeError("ABI_UNACCREDITED") from None
