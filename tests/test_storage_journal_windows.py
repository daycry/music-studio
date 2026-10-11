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


def test_observation_component_closed_validation():
    assert security._validate_component("canción-𝄞.bin") == "canción-𝄞.bin"
    for name in [
        None,
        True,
        1,
        "",
        ".",
        "..",
        "a/b",
        "a\\b",
        "a:b",
        "a\0b",
        "CON",
        "nul.txt",
        "COM1.bin",
        "LPT9",
        "COM¹",
        "a.",
        "a ",
        "\\??\\C:",
        "*",
        "?",
        "<",
        ">",
        '"',
        "|",
        "\ud800",
        "x" * 256,
    ]:
        with pytest.raises(security.NativeObservationError):
            security._validate_component(name)


class ObservationDouble:
    """Doble causal; no testigo de kernel ni contrato público."""

    def __init__(self):
        self.calls, self.closed = [], []
        self.status, self.information, self.iosb_status = 0, 1, 0
        self.query_error = 0
        self.file_type = 1
        self.path = "\\\\?\\C:\\private\\child"
        self.attributes, self.tag, self.links = 0x20, 0, 1
        self.delete_pending = 0
        self.directory = 0
        self.eof, self.allocation = 17, 4096
        self.close_result = 1
        self.close_fault = None
        self.hook = None

    def NtCreateFile(
        self,
        out,
        access,
        attributes,
        iosb,
        allocation,
        flags,
        share,
        disposition,
        options,
        ea,
        length,
    ):
        obj = attributes._obj
        name = obj.ObjectName.contents
        self.calls.append(
            (
                "open",
                access,
                share,
                disposition,
                options,
                obj.Attributes,
                obj.RootDirectory,
                ctypes.string_at(name.Buffer, name.Length),
            )
        )
        out._obj.value = 202
        iosb._obj.Status = self.iosb_status
        iosb._obj.Information = self.information
        if self.hook:
            self.hook()
        return self.status

    def GetFileType(self, handle):
        self.calls.append(("type", handle))
        return self.file_type

    def GetFileInformationByHandleEx(self, handle, kind, buffer, size):
        self.calls.append(("query", handle, kind, size))
        value = buffer._obj
        if kind == 18:
            value.VolumeSerialNumber = 73
            value.FileId.Identifier[:] = bytes(range(16))
        elif kind == 9:
            value.FileAttributes = 0x10 if handle == 101 else self.attributes
            value.ReparseTag = 0 if handle == 101 else self.tag
        elif kind == 1:
            value.AllocationSize = self.allocation
            value.EndOfFile = self.eof
            value.NumberOfLinks = self.links
            value.DeletePending = self.delete_pending
            value.Directory = 1 if handle == 101 else self.directory
        if self.query_error and handle != 101:
            ctypes.set_last_error(self.query_error)
            return 0
        return 1

    def GetFinalPathNameByHandleW(self, handle, buffer, capacity, flags):
        self.calls.append(("path", handle))
        buffer.value = self.path
        return len(self.path)

    def CloseHandle(self, handle):
        self.closed.append(handle)
        if self.close_fault:
            raise self.close_fault
        return self.close_result


class ObservationOwner:
    def __init__(self):
        self.handle = 101


def observation_parent(fake=None):
    fake = fake or ObservationDouble()
    context = security._ObservationContext(fake)
    owner = ObservationOwner()
    return security._BorrowedDirectory(owner, context), fake


def test_observation_abi_and_profiles():
    assert hasattr(security, "_UnicodeString"), "ABI aún no implementada"
    assert ctypes.sizeof(security._UnicodeString) == 16
    assert security._UnicodeString.Buffer.offset == 8
    assert ctypes.sizeof(security._ObjectAttributes) == 48
    assert security._ObjectAttributes.RootDirectory.offset == 8
    assert security._ObjectAttributes.ObjectName.offset == 16
    assert ctypes.sizeof(security._IoStatusBlock) == 16
    assert security._IoStatusBlock.Information.offset == 8
    assert ctypes.sizeof(security._FileIdInfo) == 24
    assert ctypes.sizeof(security._FileStandardInfo) == 24
    assert security._FileStandardInfo.DeletePending.offset == 20
    assert security._FileStandardInfo.Directory.offset == 21
    assert ctypes.sizeof(security._FileAttributeTagInfo) == 8
    parent, fake = observation_parent()
    child = security._open_relative_existing(parent, "child", "file")
    assert any(c[0] == "open" for c in fake.calls)
    opened = next(c for c in fake.calls if c[0] == "open")
    assert opened == (
        "open",
        0x120081,
        1,
        1,
        0x200060,
        0x1000,
        101,
        b"c\x00h\x00i\x00l\x00d\x00",
    )
    child.close()
    fake.directory, fake.attributes = 1, 0x10
    child = security._open_relative_existing(parent, "sub", "directory")
    opened = [c for c in fake.calls if c[0] == "open"][-1]
    assert opened[1:7] == (0x1200A0, 3, 1, 0x200021, 0x1000, 101)
    child.close()


@pytest.mark.parametrize("case", ["scalar", "closed", "kind", "name", "parent-type"])
def test_observation_rejects_inputs_before_open(case):
    parent, fake = observation_parent()
    name, kind = "child", "file"
    if case == "scalar":
        parent = 101
    elif case == "closed":
        parent.owner.handle = None
    elif case == "kind":
        kind = "journal"
    elif case == "name":
        name = "a:b"
    elif case == "parent-type":
        fake.file_type = 3
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, name, kind)
    assert not any(c[0] == "open" for c in fake.calls)
    assert not fake.closed


def test_observation_status_error_never_closes_outslot():
    parent, fake = observation_parent()
    fake.status = -1073741790
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "child", "file")
    assert not fake.closed
    assert not any(c[0] == "query" and c[1] == 202 for c in fake.calls)


def test_observation_return_governs_not_iosb():
    parent, fake = observation_parent()
    fake.iosb_status = -1073741790
    child = security._open_relative_existing(parent, "child", "file")
    assert isinstance(child, security._ObservedHandle)
    child.close()
    assert fake.closed == [202]


def test_observation_wrong_information_closes_acquisition_once():
    parent, fake = observation_parent()
    fake.information = 2
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "child", "file")
    assert fake.closed == [202]


def test_observation_metadata_frozen_copy():
    parent, fake = observation_parent()
    child = security._open_relative_existing(parent, "child", "file")
    assert child is not None, "Falta apertura propia"
    observed = security.read_handle_metadata(child)
    assert observed.volume_serial == 73 and observed.file_id == bytes(range(16))
    assert observed.final_path == fake.path and observed.kind == "file"
    assert (observed.links, observed.eof, observed.allocation) == (1, 17, 4096)
    assert (observed.attributes, observed.reparse_tag, observed.delete_pending) == (
        0x20,
        0,
        False,
    )
    assert tuple(map(len, observed.raw)) == (24, 8, 24)
    assert not hasattr(observed, "handle")
    with pytest.raises((AttributeError, TypeError)):
        observed.links = 2
    child.close()


@pytest.mark.parametrize(
    "field,value",
    [
        ("attributes", 0x420),
        ("tag", 0xA0000003),
        ("links", 0),
        ("links", 2),
        ("delete_pending", 1),
        ("directory", 1),
        ("file_type", 3),
        ("eof", -1),
        ("allocation", -1),
        ("allocation", 1),
        ("path", "\\\\?\\UNC\\host\\share\\f"),
        ("path", "C:\\x"),
        ("path", "\\\\?\\C:\\a\\..\\b"),
        ("path", "\\\\?\\C:\\a:stream"),
    ],
)
def test_observation_metadata_fail_closed(field, value):
    parent, fake = observation_parent()
    setattr(fake, field, value)
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "child", "file")
    # Parent metadata rejection occurs before acquisition for shared invalid fields.
    assert fake.closed in ([], [202])


def test_observation_false_query_never_parses_plausible_buffer(monkeypatch):
    if sys.platform == "linux":
        last_error = ctypes.c_ulong(0)
        monkeypatch.setattr(
            ctypes,
            "set_last_error",
            lambda value: setattr(last_error, "value", value),
            raising=False,
        )
        monkeypatch.setattr(
            ctypes, "get_last_error", lambda: last_error.value, raising=False
        )
    parent, fake = observation_parent()
    fake.query_error = 5
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "child", "file")
    assert fake.closed == [202]
    assert ctypes.get_last_error() == 5
    assert security._RETAINED is None


def test_observation_close_revokes_once():
    parent, fake = observation_parent()
    child = security._open_relative_existing(parent, "child", "file")
    assert child is not None, "Falta adquisición propia"
    original = fake.CloseHandle

    def close(handle):
        assert child._handle is None
        return original(handle)

    fake.CloseHandle = close
    assert child.close().state == "closed"
    assert child.close().state == "closed"
    with pytest.raises(security.NativeObservationError):
        security.read_handle_metadata(child)
    assert fake.closed == [202] and parent.owner.handle == 101


def test_observation_context_preserves_baseexception_and_cleanup():
    parent, fake = observation_parent()
    child = security._open_relative_existing(parent, "child", "file")
    assert child is not None, "Falta adquisición propia"
    with pytest.raises(KeyboardInterrupt) as caught, child:
        raise KeyboardInterrupt("primary")
    assert str(caught.value) == "primary" and fake.closed == [202]


def test_observation_nonwindows_without_dll(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")

    def forbidden(*args, **kwargs):
        pytest.fail("DLL no permitida")

    monkeypatch.setattr(ctypes, "WinDLL", forbidden, raising=False)
    with pytest.raises(security.PlatformUnsupportedError):
        security._ObservationContext()


def observation_child(body):
    import queue
    import subprocess
    import threading

    bootstrap = (
        "import runpy, json, gc, weakref, threading, time\n"
        f"globals().update(runpy.run_path({str(Path(__file__).resolve())!r}))\n"
        + body
        + "\nsys.stdout.flush()\nthreading.Event().wait(60)\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-X", "utf8", "-B", "-c", bootstrap],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = queue.Queue()
    reader = threading.Thread(target=lambda: lines.put(process.stdout.readline()))
    reader.start()
    line = b""
    try:
        line = lines.get(timeout=10)
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=30)
        reader.join(5)
    out, err = process.communicate(timeout=5)
    assert line, err.decode("utf-8", errors="replace")
    record = json.loads(line.decode("utf-8"))
    assert record["scope"] == "double-own-child-reaped"
    assert process.poll() is not None and not err
    (SOURCE.parents[2] / ("child-reap-" + uuid.uuid4().hex + ".json")).write_text(
        json.dumps(
            {
                "witness": record,
                "pid": process.pid,
                "reaped": True,
                "terminated_by_parent": True,
                "exit_code": process.returncode,
                "remaining_stdout": out.decode("utf-8"),
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("mode", ["pending-open", "entered-exception", "pending-query"])
def test_observation_unresolved_retains_and_poison_child(mode):
    observation_child(f"""
parent, fake = observation_parent()
owner_ref = weakref.ref(parent.owner)
if {mode!r} == "pending-open":
    fake.status = 0x103
elif {mode!r} == "entered-exception":
    def interrupt():
        raise KeyboardInterrupt("in-flight")
    fake.hook = interrupt
else:
    fake.query_error = 997
try:
    security._open_relative_existing(parent, "child", "file")
except security.IOCompletionUnaccreditedError as error:
    assert error.code == "IO_COMPLETION_UNACCREDITED"
else:
    raise AssertionError("Completion no acreditada debe rechazar")
assert security._RETAINED is not None
arena_ref = weakref.ref(security._RETAINED[1])
count = len(fake.calls)
try:
    security._open_relative_existing(parent, "second", "file")
except security.IOCompletionUnaccreditedError:
    pass
else:
    raise AssertionError("Poison debe bloquear segunda operación")
assert len(fake.calls) == count and not fake.closed
del parent
gc.collect()
assert arena_ref() is not None and owner_ref() is not None
print(json.dumps({{"scope": "double-own-child-reaped", "retained": True}}))
""")


@pytest.mark.parametrize("mode", ["false", "exception", "cleanup-primary"])
def test_observation_unknown_close_retains_without_retry_child(mode):
    observation_child(f"""
parent, fake = observation_parent()
child = security._open_relative_existing(parent, "child", "file")
assert child is not None, "Falta adquisición propia"
if {mode!r} == "false":
    fake.close_result = 0
else:
    fake.close_fault = KeyboardInterrupt("cleanup")
if {mode!r} == "cleanup-primary":
    try:
        with child:
            raise ValueError("primary")
    except ValueError as error:
        assert str(error) == "primary" and error.__notes__
    else:
        raise AssertionError("Primaria debe conservarse")
else:
    result = child.close()
    assert result.state == "unknown" and result.causes
assert child._handle is None
assert child.close().state == "unknown" and fake.closed == [202]
try:
    security._open_relative_existing(parent, "second", "file")
except security.IOCompletionUnaccreditedError:
    pass
else:
    raise AssertionError("Reap obligatorio antes de nuevas operaciones")
print(json.dumps({{"scope": "double-own-child-reaped", "close": "unknown"}}))
""")


def test_observation_concurrent_query_close_serialized():
    import threading

    parent, fake = observation_parent()
    child = security._open_relative_existing(parent, "child", "file")
    assert child is not None, "Falta adquisición propia"
    entered, release, closed = threading.Event(), threading.Event(), threading.Event()
    original = fake.GetFileType

    def paused(handle):
        entered.set()
        assert release.wait(5)
        assert not fake.closed
        return original(handle)

    fake.GetFileType = paused
    failures = []

    def query():
        try:
            security.read_handle_metadata(child)
        except BaseException as error:  # noqa: BLE001 - evidencia del thread, no se pierde la causa
            failures.append(error)

    def close():
        child.close()
        closed.set()

    reader = threading.Thread(target=query)
    closer = threading.Thread(target=close)
    reader.start()
    try:
        assert entered.wait(5)
        closer.start()
        assert not closed.wait(0.05)
    finally:
        release.set()
        reader.join(5)
        if closer.ident:
            closer.join(5)
    assert not failures and closed.is_set() and fake.closed == [202]


@pytest.fixture
def observation_native_fixture():
    if sys.platform != "win32":
        pytest.skip("Testigo Windows nativo")
    _, kernel = native_api()
    principal = independent_principal()
    own = SOURCE.parents[2] / ("u2b1-native-own-" + uuid.uuid4().hex)
    raw = descriptor(
        owner=principal,
        group=principal,
        aces=[ace(principal), ace(SYSTEM), ace(ADMINS)],
    )
    buffer = ctypes.create_string_buffer(raw)

    class Attributes(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_uint32),
            ("descriptor", ctypes.c_void_p),
            ("inherit", ctypes.c_int32),
        ]

    sa = Attributes(ctypes.sizeof(Attributes), ctypes.addressof(buffer), 0)
    assert kernel.CreateDirectoryW(str(own), ctypes.byref(sa)), ctypes.get_last_error()
    assert kernel.CreateDirectoryW(str(own / "sub"), ctypes.byref(sa)), (
        ctypes.get_last_error()
    )
    for name in ["file", "other"]:
        value = kernel.CreateFileW(
            str(own / name), 0x120089, 7, ctypes.byref(sa), 1, 0, None
        )
        assert value not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
        assert kernel.CloseHandle(value)
    owner = ObservationOwner()
    owner.handle = kernel.CreateFileW(str(own), 0x1200A0, 3, None, 3, 0x2200000, None)
    assert owner.handle not in (None, ctypes.c_void_p(-1).value), (
        ctypes.get_last_error()
    )
    parent = security._BorrowedDirectory(owner, security._ObservationContext())
    try:
        yield parent, own, kernel
    finally:
        assert kernel.CloseHandle(owner.handle)
        owner.handle = None


def test_observation_native_ordinary_missing_and_borrow(observation_native_fixture):
    parent, own, _kernel = observation_native_fixture
    parent_sd = security.read_handle_security(parent.owner.handle).raw
    child = security._open_relative_existing(parent, "file", "file")
    assert child is not None, "FILE_OPEN aún no implementado"
    before = security.read_handle_metadata(child)
    before_sd = security.read_handle_security(child._handle).raw
    after = security.read_handle_metadata(child)
    assert before == after and before.kind == "file" and before.links == 1
    assert before.final_path == "\\\\?\\" + str(own / "file")
    assert security.read_handle_security(child._handle).raw == before_sd
    assert child.close().state == "closed"
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "absent", "file")
    assert not (own / "absent").exists()
    directory = security._open_relative_existing(parent, "sub", "directory")
    assert security.read_handle_metadata(directory).kind == "directory"
    directory.close()
    assert security.read_handle_security(parent.owner.handle).raw == parent_sd
    (own / "ordinary.json").write_text(
        json.dumps(
            {
                "scope": "native-observation-no-chain",
                "file_id": before.file_id.hex(),
                "volume_serial": before.volume_serial,
                "path": before.final_path,
                "security_sha256": __import__("hashlib").sha256(before_sd).hexdigest(),
                "parent_not_closed": True,
                "missing_not_created": True,
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("access", [2, 0x10000])
def test_observation_native_sharing_bilateral(access, observation_native_fixture):
    parent, own, kernel = observation_native_fixture
    invalid = ctypes.c_void_p(-1).value
    rival = kernel.CreateFileW(str(own / "file"), access, 7, None, 3, 0, None)
    assert rival not in (None, invalid), ctypes.get_last_error()
    try:
        with pytest.raises(security.NativeObservationError):
            security._open_relative_existing(parent, "file", "file")
    finally:
        assert kernel.CloseHandle(rival)
    first = security._open_relative_existing(parent, "file", "file")
    second = security._open_relative_existing(parent, "file", "file")
    try:
        rival = kernel.CreateFileW(str(own / "file"), access, 7, None, 3, 0, None)
        assert rival == invalid and ctypes.get_last_error() == 32
        assert (
            security.read_handle_metadata(first).file_id
            == security.read_handle_metadata(second).file_id
        )
    finally:
        if second is not None:
            second.close()
        if first is not None:
            first.close()
    rival = kernel.CreateFileW(str(own / "file"), access, 7, None, 3, 0, None)
    assert rival not in (None, invalid), ctypes.get_last_error()
    assert kernel.CloseHandle(rival)


def test_observation_native_directory_denies_delete(observation_native_fixture):
    parent, own, kernel = observation_native_fixture
    directory = security._open_relative_existing(parent, "sub", "directory")
    assert directory is not None, "FILE_OPEN directorio aún no implementado"
    invalid = ctypes.c_void_p(-1).value
    try:
        rival = kernel.CreateFileW(
            str(own / "sub"), 0x10000, 7, None, 3, 0x2200000, None
        )
        assert rival == invalid and ctypes.get_last_error() == 32
        with pytest.raises(OSError):
            os.rename(own / "sub", own / "renamed")
    finally:
        directory.close()
    rival = kernel.CreateFileW(str(own / "sub"), 0x10000, 7, None, 3, 0x2200000, None)
    assert rival not in (None, invalid), ctypes.get_last_error()
    assert kernel.CloseHandle(rival)


def test_observation_native_hardlink_and_wrong_kind(observation_native_fixture):
    parent, own, _kernel = observation_native_fixture
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "file", "directory")
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "sub", "file")
    os.link(own / "file", own / "alias-file")
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "file", "file")
    assert os.lstat(own / "alias-file").st_nlink == 2


def test_observation_native_new_junction_no_traversal(observation_native_fixture):
    import subprocess

    parent, own, _kernel = observation_native_fixture
    sentinel = own / "sub" / "sentinel"
    sentinel.write_bytes(b"private-target-intact")
    target_sd = security.read_handle_security(parent.owner.handle).raw
    result = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            "mklink",
            "/J",
            str(own / "alias-dir"),
            str(own / "sub"),
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert os.lstat(own / "alias-dir").st_file_attributes & 0x400
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "alias-dir", "directory")
    assert sentinel.read_bytes() == b"private-target-intact"
    assert security.read_handle_security(parent.owner.handle).raw == target_sd
    (own / "junction-witness.json").write_text(
        json.dumps(
            {
                "scope": "new-native-junction-rejected-no-traversal",
                "alias": str(own / "alias-dir"),
                "target": str(own / "sub"),
                "objects_preserved": True,
                "sentinel_intact": True,
                "stdout": result.stdout.decode(errors="replace"),
            }
        ),
        encoding="utf-8",
    )


def test_observation_poison_retains_other_live_acquisitions_child():
    observation_child("""
parent, fake = observation_parent()
other, other_fake = observation_parent()
first = security._open_relative_existing(parent, "first", "file")
second = security._open_relative_existing(other, "second", "file")
first_ref, second_ref = weakref.ref(first), weakref.ref(second)
fake.status = 0x103
try:
    security._open_relative_existing(parent, "pending", "file")
except security.IOCompletionUnaccreditedError:
    pass
del first, second, parent, other
gc.collect()
assert first_ref() is not None and second_ref() is not None, "Owners de adquisiciones reales deben retenerse"
assert first_ref().close().state == "unknown"
assert second_ref().close().state == "unknown"
assert not fake.closed and not other_fake.closed
print(json.dumps({"scope": "double-own-child-reaped", "all_owners_retained": True}))
""")


def test_observation_independent_contexts_serialize_native_calls():
    import threading

    parent, fake = observation_parent()
    other, other_fake = observation_parent()
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    original = fake.NtCreateFile

    def paused(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    fake.NtCreateFile = paused
    failures = []

    def observe(parent):
        try:
            child = security._open_relative_existing(parent, "file", "file")
            child.close()
        except BaseException as error:  # noqa: BLE001 - evidencia del thread, no se pierde la causa
            failures.append(error)

    def second():
        observe(other)
        finished.set()

    one = threading.Thread(target=observe, args=(parent,))
    two = threading.Thread(target=second)
    one.start()
    try:
        assert entered.wait(5)
        two.start()
        assert not finished.wait(0.05), (
            "Segundo contexto no debe entrar en vuelo simultáneo"
        )
        assert not other_fake.calls
    finally:
        release.set()
        one.join(5)
        if two.ident:
            two.join(5)
    assert not failures and finished.is_set()


def test_observation_kind_requires_exact_closed_string():
    class EqualFile:
        def __eq__(self, other):
            return other == "file"

    parent, fake = observation_parent()
    with pytest.raises(security.NativeObservationError):
        security._open_relative_existing(parent, "file", EqualFile())
    assert not fake.calls


def test_observation_close_beforecall_fault_is_unknown_child():
    observation_child("""
parent, fake = observation_parent()
child = security._open_relative_existing(parent, "file", "file")
attempts = []
def before(handle):
    attempts.append(handle)
    assert child._handle is None
    raise KeyboardInterrupt("before-call")
fake.CloseHandle = before
result = child.close()
assert result is not None, "Close observation ausente"
assert result.state == "unknown" and result.causes == ("KeyboardInterrupt",)
assert child.close() == result and attempts == [202] and not fake.closed
print(json.dumps({"scope": "double-own-child-reaped", "before_call_unknown": True}))
""")


def fix1_child(body):
    """Child propio: streams y diagnóstico sólo se sellan después de wait/reap."""
    import hashlib
    import subprocess
    from datetime import datetime, timezone

    namespace = SOURCE.parents[2] / ("fix1-child-" + uuid.uuid4().hex)
    namespace.mkdir()
    script = namespace / "child.py"
    bootstrap = (
        "import runpy, json, gc, weakref, ast, traceback\n"
        f"globals().update(runpy.run_path({str(Path(__file__).resolve())!r}))\n"
        "try:\n"
        + "\n".join("    " + line for line in body.splitlines())
        + "\nexcept BaseException:\n"
        "    traceback.print_exc()\n"
        "    raise SystemExit(1)\n"
    )
    script.write_text(bootstrap, encoding="utf-8")
    argv = [sys.executable, "-X", "utf8", "-B", str(script)]
    started = datetime.now(timezone.utc).isoformat()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate(timeout=30)
    (namespace / "stdout.txt").write_bytes(out)
    (namespace / "stderr.txt").write_bytes(err)
    (namespace / "receipt.json").write_text(
        json.dumps(
            {
                "utc_start": started,
                "utc_end": datetime.now(timezone.utc).isoformat(),
                "argv": argv,
                "pid": process.pid,
                "exit_code": process.returncode,
                "reaped": process.poll() is not None,
                "source": str(SOURCE),
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "stdout_sha256": hashlib.sha256(out).hexdigest(),
                "stderr_sha256": hashlib.sha256(err).hexdigest(),
                "scope": "single-fault-double-own-process-not-native-pending",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    assert process.poll() is not None
    assert process.returncode == 0, err.decode("utf-8", errors="replace")
    assert not err
    return json.loads(out)


def fix1_transition_body(mode, fault):
    return f"""
mode, fault = {mode!r}, {fault!r}
parent, fake = observation_parent()
owner_ref = weakref.ref(parent.owner)
injected, witnessed = [], []
arena_ref = [None]
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
function_name = {{"b01": "call", "b02": "close", "b03": "_open_relative_existing"}}[mode]
target = {{"b01": "pending", "b02": "result", "b03": "value"}}[mode]
function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function_name)
if mode == "b01":
    node = next(n for n in ast.walk(function) if isinstance(n, ast.If) and "pending" in ast.unparse(n.test))
elif mode == "b02":
    node = next(n for n in ast.walk(function) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == target for t in n.targets) and isinstance(n.value, ast.Call) and isinstance(n.value.args[0], ast.IfExp))
else:
    node = next(n for n in ast.walk(function) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == target for t in n.targets))
if mode == "b01":
    fake.status = security.STATUS_PENDING
if mode == "b02":
    child = security._open_relative_existing(parent, "child", "file")
def trace(frame, event, arg):
    if event == "line" and frame.f_code.co_filename == str(SOURCE) and frame.f_code.co_name == function_name and frame.f_lineno == node.lineno:
        relevant = (frame.f_locals.get("returned") == security.STATUS_PENDING if mode == "b01" else bool(fake.closed) if mode == "b02" else frame.f_locals.get("status") == security.STATUS_SUCCESS)
        if relevant:
            witnessed.append({{"line": frame.f_lineno, "role": target, "native_calls": len(fake.calls), "closes": list(fake.closed)}})
            arena_ref[0] = weakref.ref(frame.f_locals["arena"])
            if fault and not injected:
                injected.append(True)
                sys.settrace(None)
                raise KeyboardInterrupt("FIX1 single post-return fault")
    return trace
sys.settrace(trace)
try:
    if mode == "b02":
        child.close()
    else:
        acquired = security._open_relative_existing(parent, "child", "file")
        acquired.close()
except BaseException as error:
    error_name = type(error).__name__
finally:
    sys.settrace(None)
assert witnessed, "La transición no fue observada"
assert len(injected) == int(fault), "La inyección causal debe ocurrir exactamente una vez"
if mode == "b02":
    result = child.close()
    assert fake.closed == [202], "CloseHandle no puede repetirse con None"
    assert result.state == ("unknown" if fault else "closed")
    assert child._handle is None
if fault or mode == "b01":
    gc.collect()
    assert arena_ref[0]() is not None, "Arena nativa liberada sin completion acreditada"
    assert security._RETAINED is not None, "Falta poison global"
    retained_arena = security._RETAINED[1]
    assert retained_arena is arena_ref[0]()
    count = len(fake.calls)
    try:
        security._open_relative_existing(parent, "next", "file")
    except security.IOCompletionUnaccreditedError:
        pass
    else:
        raise AssertionError("Segunda operación no bloqueada")
    other, other_fake = observation_parent()
    try:
        security.read_handle_metadata(other)
    except security.IOCompletionUnaccreditedError:
        pass
    else:
        raise AssertionError("Poison debe bloquear también otro contexto")
    assert len(fake.calls) == count and not other_fake.calls
    assert fake.closed == ([202] if mode == "b02" else [])
    del parent
    gc.collect()
    assert owner_ref() is not None
else:
    assert security._RETAINED is None and fake.closed == [202]
    assert not parent.context.owned
print(json.dumps({{"mode": mode, "fault": fault, "witnessed": witnessed, "injected": len(injected), "retained": security._RETAINED is not None, "closes": fake.closed, "owner_alive": owner_ref() is not None}}))
"""


@pytest.mark.parametrize("fault", [True, False], ids=["fault", "control"])
def test_fix1_postpending_retains_arena_owner_global_poison(fault):
    fix1_child(fix1_transition_body("b01", fault))


@pytest.mark.parametrize("fault", [True, False], ids=["fault", "control"])
def test_fix1_postclose_reserves_idempotence_without_none_retry(fault):
    fix1_child(fix1_transition_body("b02", fault))


@pytest.mark.parametrize("fault", [True, False], ids=["fault", "control"])
def test_fix1_postsuccess_open_keeps_acquisition_arena_owner(fault):
    fix1_child(fix1_transition_body("b03", fault))


def test_fix1_context_without_primary_unknown_close_is_typed():
    fix1_child("""
parent, fake = observation_parent()
child = security._open_relative_existing(parent, "child", "file")
assert child._handle == 202 and child in parent.context.owned
fake.close_result = 0
try:
    with child:
        pass
except security.NativeObservationError:
    pass
else:
    raise AssertionError("Cleanup no acreditado sin primaria debe generar error tipado")
assert child._handle is None and fake.closed == [202]
assert child.close().state == "unknown" and fake.closed == [202]
assert security._RETAINED is not None
print(json.dumps({"mode": "a01", "typed": True, "closes": fake.closed, "retained": True}))
""")


def test_fix1_entered_typed_exception_still_retains():
    fix1_child("""
parent, fake = observation_parent()
def typed_failure():
    raise security.IOCompletionUnaccreditedError("native double entered")
fake.hook = typed_failure
try:
    security._open_relative_existing(parent, "child", "file")
except security.IOCompletionUnaccreditedError:
    pass
else:
    raise AssertionError("La llamada debe fallar")
assert security._RETAINED is not None, "Tipo del error no acredita completion"
assert security._RETAINED[1].owner is parent and not fake.closed
print(json.dumps({"typed_error_retained": True}))
""")


@pytest.mark.parametrize(
    "stage",
    [
        "reserve",
        "revoke",
        "before-native",
        "post-native",
        "publish",
        "remove-owner",
        "discard-context",
        "return-close",
        "open-status",
        "open-value",
        "open-register",
        "init-authority",
        "init-parent",
        "init-observation",
        "init-register",
        "init-live",
        "open-info",
        "open-metadata",
        "return-open",
    ],
)
def test_fix1_adjacent_transition_single_fault(stage):
    fix1_child(f"""
stage = {stage!r}
close_stages = {{"reserve", "revoke", "before-native", "post-native", "publish", "remove-owner", "discard-context", "return-close"}}
roles = {{
    "reserve": ("close", "self._close_observation = unknown"),
    "revoke": ("close", "self._handle = None"),
    "before-native": ("close", "accepted = bool("),
    "post-native": ("close", "reasons ="),
    "publish": ("close", "self._close_observation = result"),
    "remove-owner": ("close", "self.context.owned.remove("),
    "discard-context": ("close", "_LIVE_CONTEXTS.discard("),
    "return-close": ("close", "return result"),
    "open-status": ("_open_relative_existing", "if status != STATUS_SUCCESS:"),
    "open-value": ("_open_relative_existing", "value = arena.output.value"),
    "open-register": ("_open_relative_existing", "child = _ObservedHandle("),
    "init-authority": ("__init__", "self._handle, self.kind ="),
    "init-parent": ("__init__", "self.parent, self.context ="),
    "init-observation": ("__init__", "self._close_observation = None"),
    "init-register": ("__init__", "self.context.owned.add("),
    "init-live": ("__init__", "_LIVE_CONTEXTS.add("),
    "open-info": ("_open_relative_existing", "if arena.iosb.Information != FILE_OPENED:"),
    "open-metadata": ("_open_relative_existing", "read_handle_metadata(child)"),
    "return-open": ("_open_relative_existing", "return child"),
}}
function_name, prefix = roles[stage]
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
if function_name == "__init__":
    scope = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "_ObservedHandle")
else:
    scope = tree
function = next(n for n in ast.walk(scope) if isinstance(n, ast.FunctionDef) and n.name == function_name)
node = next(n for n in ast.walk(function) if isinstance(n, ast.stmt) and ast.unparse(n).startswith(prefix))
parent, fake = observation_parent()
owner_ref = weakref.ref(parent.owner)
if stage in close_stages:
    child = security._open_relative_existing(parent, "child", "file")
injected, evidence, arena_ref = [], [], [None]
def trace(frame, event, arg):
    if event == "line" and frame.f_code.co_filename == str(SOURCE) and frame.f_code.co_name == function_name and frame.f_lineno == node.lineno and not injected:
        holder = frame if "arena" in frame.f_locals else frame.f_back
        arena_ref[0] = weakref.ref(holder.f_locals["arena"])
        evidence.append({{"stage": stage, "line": frame.f_lineno, "opens": sum(c[0] == "open" for c in fake.calls), "closes": list(fake.closed)}})
        injected.append(True)
        sys.settrace(None)
        raise KeyboardInterrupt("FIX1 adjacent single fault")
    return trace
sys.settrace(trace)
try:
    if stage in close_stages:
        child.close()
    else:
        security._open_relative_existing(parent, "child", "file")
except security.IOCompletionUnaccreditedError:
    pass
finally:
    sys.settrace(None)
assert len(injected) == 1, "La transición semántica debe inyectarse"
assert security._RETAINED is not None and security._RETAINED[1] is arena_ref[0]()
assert arena_ref[0]() is not None and owner_ref() is not None
if stage in close_stages:
    assert child._handle is None and child.close().state == "unknown"
    assert child in parent.context.owned and parent.context in security._LIVE_CONTEXTS
    assert fake.closed in ([], [202]) and None not in fake.closed
else:
    assert not fake.closed
count = len(fake.calls)
try:
    security._open_relative_existing(parent, "other", "file")
except security.IOCompletionUnaccreditedError:
    pass
else:
    raise AssertionError("Poison global ausente")
assert len(fake.calls) == count
del parent
gc.collect()
assert arena_ref[0]() is not None and owner_ref() is not None
print(json.dumps({{"stage": stage, "injected": len(injected), "evidence": evidence, "retained": True, "closes": fake.closed}}))
""")
