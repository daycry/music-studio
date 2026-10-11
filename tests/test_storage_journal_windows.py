"""Sintéticos explícitos y testigos nativos separados, sin admisión de cadena."""

import ctypes
import importlib.util
import json
import os
import struct
import sys
import uuid
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/storage_journal_windows.py"
SPEC = importlib.util.spec_from_file_location("candidate_windows_security", SOURCE)
security = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = security
SPEC.loader.exec_module(security)


def sid(authority=5, *parts):
    return (
        bytes([1, len(parts)])
        + authority.to_bytes(6, "big")
        + struct.pack("<" + "I" * len(parts), *parts)
    )


USER = sid(5, 21, 7, 8, 9, 1001)
SYSTEM = sid(5, 18)
ADMINS = sid(5, 32, 544)
OUTSIDER = sid(5, 21, 7, 8, 9, 1002)


def ace(trustee=USER, mask=0x1F01FF, kind=0, flags=0):
    return struct.pack("<BBHI", kind, flags, 8 + len(trustee), mask) + trustee


def descriptor(aces=None, owner=USER, group=SYSTEM, control=0x9004):
    if aces is None:
        aces = [ace(USER), ace(SYSTEM), ace(ADMINS)]
    acl_data = b"".join(aces)
    acl = struct.pack("<BBHHH", 2, 0, len(acl_data) + 8, len(aces), 0) + acl_data
    return (
        struct.pack(
            "<BBHIIII",
            1,
            0,
            control,
            20,
            20 + len(owner),
            0,
            20 + len(owner) + len(group),
        )
        + owner
        + group
        + acl
    )


def test_synthetic_closed_descriptor_is_local_diagnostic():
    result = security.evaluate_security(descriptor(), USER, "journal")
    assert result.local_sufficient is True
    assert result.native_observed is False
    assert not hasattr(result, "handle")
    assert not hasattr(result, "token")
    with pytest.raises((AttributeError, TypeError)):
        result.local_sufficient = False


def test_descriptor_sid_acl_bounds_fail_closed():
    assert security.evaluate_security(descriptor(), USER, "journal").local_sufficient
    malformed = [
        b"",
        descriptor()[:19],
        descriptor()[:-1],
        descriptor(control=0x1004),
        descriptor(control=0x9000),
        descriptor(aces=[]),
        descriptor(owner=USER[:-1]),
        descriptor(group=SYSTEM[:-1]),
    ]
    original = descriptor()
    for offset, replacement in [
        (0, b"\x02"),
        (1, b"\x01"),
        (4, struct.pack("<I", 1)),
        (8, struct.pack("<I", 20)),
        (12, struct.pack("<I", 20)),
        (16, struct.pack("<I", 0)),
        (20, b"\x02"),
        (21, b"\x10"),
    ]:
        malformed.append(
            original[:offset] + replacement + original[offset + len(replacement) :]
        )
    acl_offset = 20 + len(USER) + len(SYSTEM)
    for delta, replacement in [
        (0, b"\x03"),
        (1, b"\x01"),
        (2, b"\xff\xff"),
        (4, b"\xff\xff"),
        (6, b"\x01\x00"),
        (10, b"\x07\x00"),
    ]:
        at = acl_offset + delta
        malformed.append(
            original[:at] + replacement + original[at + len(replacement) :]
        )
    for raw in malformed:
        result = security.evaluate_security(raw, USER, "journal")
        assert not result.local_sufficient, raw.hex()
        assert result.reasons
    for invalid_principal in [b"", USER[:-1], USER + b"\0", "S-1-5-18", None]:
        assert not security.evaluate_security(
            descriptor(), invalid_principal, "journal"
        ).local_sufficient
    assert not security.evaluate_security(
        descriptor(), USER, "root_system"
    ).local_sufficient


@pytest.mark.parametrize(
    "extra",
    [
        ace(kind=2),
        ace(kind=5),
        ace(kind=9),
        ace(kind=11, flags=8),
        ace(flags=0x20),
        ace(flags=4),
        ace(flags=8),
        ace(mask=0x200),
        ace(mask=0x200000),
        ace(mask=0x02000000),
        ace(sid(3, 0)),
        ace(sid(3, 4)),
        ace(kind=1),
    ],
    ids=[
        "audit",
        "object",
        "callback",
        "callback-io",
        "unknown-flag",
        "np-alone",
        "io-alone",
        "unknown-low",
        "unknown-standard",
        "maximum-allowed",
        "creator-owner",
        "owner-rights",
        "noncanonical",
    ],
)
def test_uninterpretable_ace_fail_closed(extra):
    assert security.evaluate_security(
        descriptor(), USER, "existing_parent"
    ).local_sufficient
    result = security.evaluate_security(
        descriptor([ace(), extra]), USER, "existing_parent"
    )
    assert not result.local_sufficient


@pytest.mark.parametrize("role", ["journal", "protected_domain", "existing_parent"])
def test_outsider_owner_and_ti_cannot_self_accredit(role):
    assert security.evaluate_security(descriptor(), USER, role).local_sufficient
    for owner in [OUTSIDER, sid(5, 80, 1, 2, 3, 4, 5)]:
        assert not security.evaluate_security(
            descriptor(owner=owner), USER, role
        ).local_sufficient
    if role != "existing_parent":
        for owner in [SYSTEM, ADMINS]:
            assert not security.evaluate_security(
                descriptor(owner=owner), USER, role
            ).local_sufficient


@pytest.mark.parametrize(
    "role,dangerous",
    [("journal", 0xD0116), ("protected_domain", 0xD0156), ("existing_parent", 0xD0150)],
)
def test_dangerous_outsider_allow_deny_generic_and_io(role, dangerous):
    assert security.evaluate_security(descriptor(), USER, role).local_sufficient
    for bit in [1 << n for n in range(32) if dangerous & (1 << n)]:
        for trustee in [OUTSIDER, sid(5, 32, 545), sid(5, 987654)]:
            for flags in [0, 0x10, 0x0B, 0x03, 0x07]:
                raw = descriptor(
                    [ace(trustee, bit, kind=1), ace(), ace(trustee, bit, flags=flags)]
                )
                assert not security.evaluate_security(raw, USER, role).local_sufficient
    for generic in [0x10000000, 0x40000000]:
        assert not security.evaluate_security(
            descriptor([ace(), ace(OUTSIDER, generic)]), USER, role
        ).local_sufficient


def test_closed_new_roles_and_parent_read_creation_grants():
    for role in ["journal", "protected_domain"]:
        for flags, control, kind in [(0x10, 0x9004, 0), (0, 0x8004, 0), (0, 0x9004, 1)]:
            assert not security.evaluate_security(
                descriptor([ace(flags=flags, kind=kind)], control=control), USER, role
            ).local_sufficient
        assert not security.evaluate_security(
            descriptor([ace(), ace(OUTSIDER, 1)]), USER, role
        ).local_sufficient
    for mask in [0x1200A9, 0x80000000, 0x20000000, 2, 4, 6]:
        raw = descriptor([ace(), ace(OUTSIDER, mask)])
        assert security.evaluate_security(raw, USER, "existing_parent").local_sufficient
    for owner in [SYSTEM, ADMINS]:
        assert security.evaluate_security(
            descriptor(owner=owner), USER, "existing_parent"
        ).local_sufficient


def test_portable_platform_rejects_without_loading_dll(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")

    def forbidden(*args, **kwargs):
        pytest.fail("No se debe cargar DLL en plataforma no soportada")

    monkeypatch.setattr(ctypes, "WinDLL", forbidden, raising=False)
    for call in [
        security.current_security_principal,
        lambda: security.read_handle_security(123),
    ]:
        with pytest.raises(Exception) as caught:
            call()
        assert getattr(caught.value, "code", None) == "PLATFORM_UNSUPPORTED"


def native_api():
    """Harness independiente, sólo fixtures; no usa el binding del candidato."""
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    pointer, dword, boolean = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32
    signatures = [
        (kernel, "GetCurrentProcess", [], pointer),
        (kernel, "CloseHandle", [pointer], boolean),
        (
            kernel,
            "CreateFileW",
            [ctypes.c_wchar_p, dword, dword, pointer, dword, dword, pointer],
            pointer,
        ),
        (kernel, "CreateDirectoryW", [ctypes.c_wchar_p, pointer], boolean),
        (adv, "OpenProcessToken", [pointer, dword, ctypes.POINTER(pointer)], boolean),
        (
            adv,
            "GetTokenInformation",
            [pointer, dword, pointer, dword, ctypes.POINTER(dword)],
            boolean,
        ),
        (adv, "GetLengthSid", [pointer], dword),
        (adv, "IsValidSid", [pointer], boolean),
        (adv, "IsWellKnownSid", [pointer, ctypes.c_int32], boolean),
    ]
    for lib, name, args, result in signatures:
        function = getattr(lib, name)
        function.argtypes, function.restype = args, result
    return adv, kernel


def independent_principal():
    adv, kernel = native_api()
    token = ctypes.c_void_p()
    assert adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token))
    try:
        needed = ctypes.c_uint32()
        assert not adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        assert ctypes.get_last_error() == 122 and 16 <= needed.value <= 65536
        buffer = ctypes.create_string_buffer(needed.value)
        assert adv.GetTokenInformation(
            token, 1, buffer, len(buffer), ctypes.byref(needed)
        )
        sid_pointer = ctypes.c_void_p.from_buffer(buffer).value
        assert adv.IsValidSid(sid_pointer)
        return ctypes.string_at(sid_pointer, adv.GetLengthSid(sid_pointer))
    finally:
        value, token.value = token.value, None
        assert kernel.CloseHandle(value)


@pytest.mark.skipif(sys.platform != "win32", reason="Testigo nativo Windows")
def test_native_principal_matches_independent_token_user():
    assert security.current_security_principal() == independent_principal()
    adv, _ = native_api()
    assert adv.IsWellKnownSid(ctypes.create_string_buffer(security.SYSTEM_SID), 22)
    assert adv.IsWellKnownSid(
        ctypes.create_string_buffer(security.ADMINISTRATORS_SID), 26
    )


@pytest.fixture
def native_fixture():
    if sys.platform != "win32":
        pytest.skip("Fixture nativa Windows")
    _, kernel = native_api()
    principal = independent_principal()
    namespace = SOURCE.parents[2]
    own = namespace / ("native-own-" + uuid.uuid4().hex)

    class Attributes(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_uint32),
            ("descriptor", ctypes.c_void_p),
            ("inherit", ctypes.c_int32),
        ]

    buffers = []
    handles = []

    def attributes(raw):
        buffer = ctypes.create_string_buffer(raw)
        buffers.append(buffer)
        return Attributes(ctypes.sizeof(Attributes), ctypes.addressof(buffer), 0)

    closed = descriptor(
        owner=principal,
        group=principal,
        aces=[ace(principal), ace(SYSTEM), ace(ADMINS)],
    )
    sa = attributes(closed)
    assert kernel.CreateDirectoryW(str(own), ctypes.byref(sa)), ctypes.get_last_error()

    def create(name, extra=()):
        raw = descriptor(
            owner=principal,
            group=principal,
            aces=[ace(principal), ace(SYSTEM), ace(ADMINS), *extra],
        )
        sa = attributes(raw)
        handle = kernel.CreateFileW(
            str(own / name), 0x120089, 1, ctypes.byref(sa), 1, 0, None
        )
        assert handle not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
        handles.append(handle)
        return handle

    try:
        yield principal, create, own
    finally:
        while handles:
            handle = handles.pop()
            assert kernel.CloseHandle(handle)
        # Objetos propios preservados; ninguna eliminación ni ACL post-creación.


def save_native_witness(own, name, observation, result):
    (own / (name + ".rawsd")).write_bytes(observation.raw)
    (own / (name + ".json")).write_text(
        json.dumps(
            {
                "source": str(SOURCE),
                "native_observed": result.native_observed,
                "local_sufficient": result.local_sufficient,
                "reasons": result.reasons,
                "owner_hex": observation.owner.hex(),
                "group_hex": observation.group.hex(),
                "control": observation.control,
                "scope": "S2 leaf únicamente; no cadena G2",
            },
            indent=2,
        )
    )


def test_native_closed_descriptor_read_borrowed_handle(native_fixture):
    principal, create, own = native_fixture
    handle = create("closed")
    observation = security.read_handle_security(handle)
    assert observation.owner == principal
    assert observation.group == principal
    assert observation.control & 0x1004 == 0x1004
    assert observation.raw
    result = security.evaluate_security(observation, principal, "journal")
    assert result.local_sufficient and result.native_observed
    assert not hasattr(observation, "handle")
    # El handle prestado sigue válido: segunda consulta por el mismo handle.
    assert security.read_handle_security(handle).raw == observation.raw
    assert not security.evaluate_security(
        observation.raw, principal, "journal"
    ).native_observed
    save_native_witness(own, "closed", observation, result)


@pytest.mark.parametrize("mask", [2, 0x40000], ids=["write-data", "write-dac"])
def test_native_outsider_effective_grant_rejected(native_fixture, mask):
    principal, create, own = native_fixture
    handle = create("outsider", [ace(sid(5, 32, 545), mask)])
    observation = security.read_handle_security(handle)
    assert observation.owner == principal and observation.control & 0x1000
    result = security.evaluate_security(observation, principal, "journal")
    assert result.native_observed and not result.local_sufficient
    save_native_witness(own, "negative", observation, result)


@pytest.mark.skipif(sys.platform != "win32", reason="Padre existente Windows readonly")
def test_native_existing_host_parent_rejects_without_mutation():
    _, kernel = native_api()
    parent = SOURCE.parents[2]
    handle = kernel.CreateFileW(str(parent), 0x20000, 7, None, 3, 0x02000000, None)
    assert handle not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
    try:
        principal = independent_principal()
        before = security.read_handle_security(handle)
        result = security.evaluate_security(before, principal, "existing_parent")
        assert result.native_observed and not result.local_sufficient
        after = security.read_handle_security(handle)
        assert before.raw == after.raw  # Comparación local, no prueba ABA ni cadena.
        (parent / "host-parent.rawsd").write_bytes(before.raw)
        (parent / "host-parent-witness.json").write_text(
            json.dumps(
                {
                    "owner_hex": before.owner.hex(),
                    "control": before.control,
                    "raw_hex": before.raw.hex(),
                    "reasons": result.reasons,
                    "local_sufficient": False,
                    "native_observed": True,
                    "mutation": False,
                },
                indent=2,
            )
        )
    finally:
        value, handle = handle, None
        assert kernel.CloseHandle(value)


class SecurityApiDouble:
    """Doble causal etiquetado; no constituye evidencia nativa."""

    def __init__(self, mode="ok"):
        self.mode = mode
        self.raw = descriptor()
        self.buffer = ctypes.create_string_buffer(self.raw)
        self.freed = []
        self.closed = []
        self.calls = []

    def GetSecurityInfo(self, handle, kind, info, owner, group, dacl, sacl, out):
        self.calls.append((handle, kind, info, owner, group, dacl, sacl))
        if self.mode != "missing":
            out._obj.value = ctypes.addressof(self.buffer)
        if self.mode == "interrupt":
            raise KeyboardInterrupt("consulta interrumpida")
        return 5 if self.mode == "status" else 0

    def IsValidSecurityDescriptor(self, pointer):
        return self.mode != "invalid"

    def GetSecurityDescriptorLength(self, pointer):
        return security.MAX_DESCRIPTOR + 1 if self.mode == "oversize" else len(self.raw)

    def GetSecurityDescriptorControl(self, pointer, control, revision):
        control._obj.value = 0x8004 if self.mode == "inconsistent" else 0x9004
        revision._obj.value = 1
        return self.mode != "control"

    def LocalFree(self, pointer):
        self.freed.append(pointer)
        if self.mode in ("cleanup", "interrupt-cleanup"):
            return pointer
        return None


@pytest.mark.parametrize(
    "mode",
    ["status", "missing", "invalid", "oversize", "control", "inconsistent", "cleanup"],
)
def test_double_reader_faults_are_closed_and_cleanup_once(monkeypatch, mode):
    valid = SecurityApiDouble()
    monkeypatch.setattr(security, "_windows_api", lambda: valid)
    observation = security.read_handle_security(71)
    assert observation.raw == descriptor()
    assert not security.evaluate_security(observation, USER, "journal").native_observed
    assert valid.calls == [(71, 1, 7, None, None, None, None)]
    assert len(valid.freed) == 1 and not valid.closed
    faulty = SecurityApiDouble(mode)
    monkeypatch.setattr(security, "_windows_api", lambda: faulty)
    with pytest.raises(security.SecurityInspectionError) as caught:
        security.read_handle_security(71)
    assert caught.value.code == "SECURITY_UNACCREDITED"
    assert len(faulty.freed) == (0 if mode == "missing" else 1)
    assert not faulty.closed


def test_double_reader_baseexception_and_cleanup_primary_preserved(monkeypatch):
    fake = SecurityApiDouble("interrupt")
    monkeypatch.setattr(security, "_windows_api", lambda: fake)

    def cleanup(pointer):
        fake.freed.append(pointer)
        raise RuntimeError("cleanup injected")

    fake.LocalFree = cleanup
    with pytest.raises(KeyboardInterrupt) as caught:
        security.read_handle_security(71)
    assert str(caught.value) == "consulta interrumpida"
    assert caught.value.__notes__ == ["Cleanup separado: RuntimeError"]
    assert len(fake.freed) == 1


class PrincipalApiDouble:
    """TokenUser sintético con buffer real de ctypes; ninguna autoridad nativa."""

    def __init__(self, mode="ok"):
        self.mode = mode
        self.closed = []
        self.queries = 0

    def GetCurrentThread(self):
        return -2

    def GetCurrentProcess(self):
        return -1

    def OpenThreadToken(self, thread, access, as_self, out):
        assert (thread, access, as_self) == (-2, 8, 1)
        if self.mode == "impersonation":
            out._obj.value = 201
            return 1
        ctypes.set_last_error(5 if self.mode == "thread-denied" else 1008)
        return 0

    def OpenProcessToken(self, process, access, out):
        assert (process, access) == (-1, 8)
        if self.mode != "process-missing":
            out._obj.value = (
                ctypes.c_void_p(-1).value if self.mode == "pseudo-handle" else 202
            )
        return self.mode != "process-failed"

    def GetTokenInformation(self, token, kind, buffer, size, needed):
        assert token.value == 202 and kind == 1
        self.queries += 1
        if buffer is None:
            needed._obj.value = 70000 if self.mode == "size-large" else 16 + len(USER)
            ctypes.set_last_error(5 if self.mode == "size-error" else 122)
            return self.mode == "size-success"
        if self.mode == "interrupt":
            raise KeyboardInterrupt("token interrupted")
        if self.mode == "query-failed":
            return 0
        needed._obj.value = size + 1 if self.mode == "query-size" else size
        address = ctypes.addressof(buffer)
        pointer = address + 16
        if self.mode == "pointer-outside":
            pointer = address + size
        elif self.mode == "pointer-prefix":
            pointer = address
        ctypes.c_void_p.from_buffer(buffer).value = pointer
        raw = USER
        if self.mode == "truncated":
            raw = bytes([1, 15]) + USER[2:]
        if self.mode == "invalid-sid":
            raw = bytes([2]) + USER[1:]
        ctypes.memmove(address + 16, raw, len(raw))
        return 1

    def IsValidSid(self, pointer):
        return self.mode != "native-invalid-sid"

    def GetLengthSid(self, pointer):
        return 12 if self.mode == "native-length" else len(USER)

    def CloseHandle(self, handle):
        self.closed.append(handle)
        return self.mode != "cleanup"


@pytest.mark.skipif(
    sys.platform != "win32", reason="ctypes last_error Win32; doble causal"
)
@pytest.mark.parametrize(
    "mode",
    [
        "impersonation",
        "thread-denied",
        "process-missing",
        "process-failed",
        "size-large",
        "size-error",
        "size-success",
        "query-failed",
        "query-size",
        "pointer-outside",
        "pointer-prefix",
        "truncated",
        "invalid-sid",
        "native-invalid-sid",
        "native-length",
        "cleanup",
    ],
)
def test_double_principal_error_contract_and_close_once(monkeypatch, mode):
    valid = PrincipalApiDouble()
    monkeypatch.setattr(security, "_windows_api", lambda: valid)
    assert security.current_security_principal() == USER
    assert valid.closed == [202]
    fake = PrincipalApiDouble(mode)
    monkeypatch.setattr(security, "_windows_api", lambda: fake)
    with pytest.raises(security.SecurityInspectionError):
        security.current_security_principal()
    assert fake.closed == (
        [201]
        if mode == "impersonation"
        else []
        if mode in ["thread-denied", "process-missing"]
        else [202]
    )


def test_cleanup_invalidates_owned_pointer_before_callback():
    observed = []

    def cleanup(value):
        observed.append((value, resource.value))
        return 1

    with security._owned_resource(cleanup) as resource:
        resource.value = 99
    assert observed == [(99, None)]


def test_synthetic_observation_cannot_claim_native():
    observed = security.SecurityObservation(descriptor())
    assert not security.evaluate_security(observed, USER, "journal").native_observed
    assert observed.owner == USER and observed.group == SYSTEM
    with pytest.raises((AttributeError, TypeError)):
        observed._origin = True


@pytest.mark.skipif(
    sys.platform != "win32", reason="ctypes last_error Win32; doble causal"
)
def test_principal_rejects_pseudo_handle_without_closing_it(monkeypatch):
    valid = PrincipalApiDouble()
    monkeypatch.setattr(security, "_windows_api", lambda: valid)
    assert security.current_security_principal() == USER
    fake = PrincipalApiDouble("pseudo-handle")
    monkeypatch.setattr(security, "_windows_api", lambda: fake)
    with pytest.raises(security.SecurityInspectionError):
        security.current_security_principal()
    assert fake.closed == []


@pytest.mark.parametrize(
    "handle", [None, True, 0, -1, (1 << 64) - 1, 1 << 64, ctypes.c_void_p(71)]
)
def test_borrowed_scalar_validation_never_closes_it(monkeypatch, handle):
    fake = SecurityApiDouble()
    monkeypatch.setattr(security, "_windows_api", lambda: fake)
    with pytest.raises(security.SecurityInspectionError):
        security.read_handle_security(handle)
    assert not fake.calls and not fake.closed and not fake.freed


@pytest.mark.skipif(
    sys.platform != "win32", reason="ctypes last_error Win32; doble causal"
)
def test_principal_baseexception_primary_and_cleanup_separated(monkeypatch):
    fake = PrincipalApiDouble("interrupt")

    def cleanup(handle):
        fake.closed.append(handle)
        raise RuntimeError("close fault")

    fake.CloseHandle = cleanup
    monkeypatch.setattr(security, "_windows_api", lambda: fake)
    with pytest.raises(KeyboardInterrupt) as caught:
        security.current_security_principal()
    assert str(caught.value) == "token interrupted"
    assert caught.value.__notes__ == ["Cleanup separado: RuntimeError"]
    assert fake.closed == [202]


def test_native_load_error_is_typed(monkeypatch):
    def missing_dll(*args, **kwargs):
        raise OSError("injected loader error")

    monkeypatch.setattr(ctypes, "WinDLL", missing_dll, raising=False)
    monkeypatch.setattr(os, "name", "nt")
    with pytest.raises(security.SecurityInspectionError) as caught:
        security.current_security_principal()
    assert caught.value.code == "SECURITY_UNACCREDITED"


def test_cleanup_without_primary_exception_is_typed(monkeypatch):
    fake = SecurityApiDouble()

    def failing_free(pointer):
        fake.freed.append(pointer)
        raise OSError("injected cleanup error")

    fake.LocalFree = failing_free
    monkeypatch.setattr(security, "_windows_api", lambda: fake)
    with pytest.raises(security.SecurityInspectionError) as caught:
        security.read_handle_security(71)
    assert caught.value.code == "SECURITY_UNACCREDITED"
    assert len(fake.freed) == 1


def test_principal_self_generic_trustee_is_not_substituted():
    assert security.evaluate_security(
        descriptor(), USER, "existing_parent"
    ).local_sufficient
    raw = descriptor([ace(), ace(sid(5, 10), 0x120089)])
    assert not security.evaluate_security(raw, USER, "existing_parent").local_sufficient
