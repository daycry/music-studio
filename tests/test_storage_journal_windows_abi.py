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


def test_acquisition_sdk_layouts_sizes_alignment_and_offsets():
    import ctypes as c

    m = load()
    abi = m._build_acquisition_abi(c)
    expected = {
        "SECURITY_DESCRIPTOR": (
            40,
            8,
            {
                "Revision": 0,
                "Sbz1": 1,
                "Control": 2,
                "Owner": 8,
                "Group": 16,
                "Sacl": 24,
                "Dacl": 32,
            },
        ),
        "ACL": (
            8,
            2,
            {"AclRevision": 0, "Sbz1": 1, "AclSize": 2, "AceCount": 4, "Sbz2": 6},
        ),
        "ACE_HEADER": (4, 2, {"AceType": 0, "AceFlags": 1, "AceSize": 2}),
        "ACCESS_ALLOWED_ACE": (12, 4, {"Header": 0, "Mask": 4, "SidStart": 8}),
    }
    for name, (size, alignment, fields) in expected.items():
        assert c.sizeof(abi[name]) == size and c.alignment(abi[name]) == alignment
        assert {field: getattr(abi[name], field).offset for field in fields} == fields


def test_acquisition_all_closed_sdk_signatures_bind_before_calls():
    import ctypes as c

    m = load()
    abi = m._build_acquisition_abi(c)
    calls = []

    class Function:
        def __call__(self, *args):
            calls.append(args)
            raise AssertionError("binding no ejecuta SDK")

    names = {
        "ntdll": ["NtCreateFile"],
        "kernel32": [
            "CloseHandle",
            "GetVolumePathNameW",
            "GetVolumeNameForVolumeMountPointW",
            "QueryDosDeviceW",
            "GetDriveTypeW",
        ],
        "advapi32": [
            "CreateWellKnownSid",
            "IsValidSid",
            "GetLengthSid",
            "InitializeSecurityDescriptor",
            "InitializeAcl",
            "AddAccessAllowedAce",
            "SetSecurityDescriptorOwner",
            "SetSecurityDescriptorGroup",
            "SetSecurityDescriptorDacl",
            "SetSecurityDescriptorControl",
            "IsValidSecurityDescriptor",
            "GetSecurityDescriptorControl",
            "GetSecurityDescriptorOwner",
            "GetSecurityDescriptorGroup",
            "GetSecurityDescriptorDacl",
        ],
    }
    dlls = {
        dll: types.SimpleNamespace(**{name: Function() for name in symbols})
        for dll, symbols in names.items()
    }
    functions = m._bind_acquisition_functions(c, abi, dlls)
    assert set(functions) == {name for symbols in names.values() for name in symbols}
    assert len(functions["NtCreateFile"].argtypes) == 11
    assert functions["NtCreateFile"].restype is c.c_int32
    assert functions["CloseHandle"].argtypes == (c.c_void_p,)
    assert functions["QueryDosDeviceW"].restype is c.c_uint32
    assert functions["SetSecurityDescriptorControl"].argtypes == (
        c.c_void_p,
        c.c_uint16,
        c.c_uint16,
    )
    assert calls == []


@pytest.mark.parametrize(
    "name", ["SECURITY_DESCRIPTOR", "ACL", "ACE_HEADER", "ACCESS_ALLOWED_ACE"]
)
def test_acquisition_layout_mismatch_rejects_before_resources(monkeypatch, name):
    import ctypes as c

    m = load()
    sizeof = c.sizeof
    monkeypatch.setattr(
        c,
        "sizeof",
        lambda typ: sizeof(typ) + 1 if typ.__name__ == name else sizeof(typ),
    )
    with pytest.raises(RuntimeError, match="ABI_UNACCREDITED"):
        m._build_acquisition_abi(c)


def acquisition_fake_dlls():
    calls = []

    class Function:
        def __call__(self, *args):
            calls.append(args)
            raise AssertionError("CPU binding no ejecuta SDK real")

    names = [
        "NtCreateFile",
        "CloseHandle",
        "GetVolumePathNameW",
        "GetVolumeNameForVolumeMountPointW",
        "QueryDosDeviceW",
        "GetDriveTypeW",
        "CreateWellKnownSid",
        "IsValidSid",
        "GetLengthSid",
        "InitializeSecurityDescriptor",
        "InitializeAcl",
        "AddAccessAllowedAce",
        "SetSecurityDescriptorOwner",
        "SetSecurityDescriptorGroup",
        "SetSecurityDescriptorDacl",
        "SetSecurityDescriptorControl",
        "IsValidSecurityDescriptor",
        "GetSecurityDescriptorControl",
        "GetSecurityDescriptorOwner",
        "GetSecurityDescriptorGroup",
        "GetSecurityDescriptorDacl",
    ]
    return types.SimpleNamespace(**{name: Function() for name in names}), calls


def test_acquisition_factory_fake_binding_is_pure_closed_ops(monkeypatch):
    import ctypes as c

    m = load()
    dll, calls = acquisition_fake_dlls()
    loads = []

    def loader(name, *, use_last_error):
        assert use_last_error is True
        loads.append(name)
        return dll

    monkeypatch.setattr(c, "WinDLL", loader, raising=False)
    backend = m._new_native_acquisition_backend()
    assert loads == ["ntdll", "kernel32", "advapi32"] and calls == []
    assert set(vars(backend)) == {"open", "close", "locate", "descriptor"}
    assert all(callable(value) for value in vars(backend).values())
    for operation in vars(backend).values():
        with pytest.raises(RuntimeError, match="CAPABILITY_INVALID"):
            operation({"source": "native_windows_x64", "trusted": True})
    assert calls == []


@pytest.mark.parametrize("fault", ["os", "platform", "machine", "python32"])
def test_acquisition_platform_gate_before_any_fake_loader(monkeypatch, fault):
    import ctypes as c

    m = load()
    calls = []
    monkeypatch.setattr(c, "WinDLL", lambda *a, **k: calls.append(a), raising=False)
    if fault == "os":
        monkeypatch.setattr(m, "os", types.SimpleNamespace(name="posix"))
    elif fault == "platform":
        monkeypatch.setattr(
            m, "sys", types.SimpleNamespace(platform="linux", maxsize=2**63 - 1)
        )
    elif fault == "python32":
        monkeypatch.setattr(
            m, "sys", types.SimpleNamespace(platform="win32", maxsize=2**31 - 1)
        )
    else:
        monkeypatch.setattr(
            m, "platform", types.SimpleNamespace(machine=lambda: "arm64")
        )
    with pytest.raises(RuntimeError, match="PLATFORM_UNSUPPORTED"):
        m._new_native_acquisition_backend()
    assert calls == []


def test_identity_sdk_layouts_exact():
    import ctypes as c

    m = load()
    builder = getattr(m, "_build_identity_abi", m._build_abi)
    abi = builder(c)
    expected = {
        "LUID": (8, 4, {"LowPart": 0, "HighPart": 4}),
        "TOKEN_USER": (16, 8, {"Sid": 0, "Attributes": 8}),
        "TOKEN_PRIMARY_GROUP": (8, 8, {"PrimaryGroup": 0}),
        "TOKEN_STATISTICS": (
            56,
            8,
            {
                "TokenId": 0,
                "AuthenticationId": 8,
                "ExpirationTime": 16,
                "TokenType": 24,
                "ImpersonationLevel": 28,
                "DynamicCharged": 32,
                "DynamicAvailable": 36,
                "GroupCount": 40,
                "PrivilegeCount": 44,
                "ModifiedId": 48,
            },
        ),
    }
    actual = {
        name: None
        if name not in abi
        else (
            c.sizeof(abi[name]),
            c.alignment(abi[name]),
            {field: getattr(abi[name], field).offset for field in fields},
        )
        for name, (_, _, fields) in expected.items()
    }
    assert actual == expected


def test_identity_bindings_fake_sdk_and_call_wall(monkeypatch):
    import ctypes as c

    m = load()
    calls = []
    # Gate y DLL simulados sólo para fijar firmas: ningún issuer ni query real.
    monkeypatch.setattr(m, "os", types.SimpleNamespace(name="nt"))
    monkeypatch.setattr(
        m, "sys", types.SimpleNamespace(platform="win32", maxsize=2**63 - 1)
    )
    monkeypatch.setattr(m, "platform", types.SimpleNamespace(machine=lambda: "amd64"))

    class Function:
        def __call__(self, *args):
            calls.append(args)
            return 1

    functions = {
        name: Function()
        for name in (
            "GetCurrentProcess",
            "GetCurrentThread",
            "OpenThreadToken",
            "OpenProcessToken",
            "GetTokenInformation",
            "CloseHandle",
        )
    }
    dll = types.SimpleNamespace(**functions)
    monkeypatch.setattr(c, "WinDLL", lambda *a, **k: dll, raising=False)
    factory = getattr(m, "_new_native_identity_backend", lambda: None)
    backend = factory()
    assert type(backend).__name__ == "_IdentityOps"
    assert calls == []
    assert functions["OpenThreadToken"].argtypes == (
        c.c_void_p,
        c.c_uint32,
        c.c_int32,
        c.POINTER(c.c_void_p),
    )
    assert functions["GetTokenInformation"].argtypes == (
        c.c_void_p,
        c.c_int32,
        c.c_void_p,
        c.c_uint32,
        c.POINTER(c.c_uint32),
    )
    assert all(
        f.restype is (c.c_void_p if n.startswith("GetCurrent") else c.c_int32)
        for n, f in functions.items()
    )
    with pytest.raises(Exception, match="CAPABILITY_INVALID"):
        backend.execute({"trusted": True})
    assert calls == []


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
