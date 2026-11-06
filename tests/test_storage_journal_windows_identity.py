"""Identidad CPU: parsing acotado y autoridad nominal separada."""

import importlib
import pathlib
import struct
import sys
import types
import uuid

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
SID = bytes([1, 1, 0, 0, 0, 0, 0, 5]) + struct.pack("<I", 21)


def load():
    key = "k4a_" + uuid.uuid4().hex
    package = types.ModuleType(key)
    package.__path__ = [str(SCRIPTS)]
    sys.modules[key] = package
    if not (SCRIPTS / "storage_journal_windows_identity.py").exists():
        # Un baseline ausente no produce ImportError: el assert funcional
        # expone el parser que aún no rechaza el dato no acreditado.
        return types.SimpleNamespace(_parse_sid=lambda *a, **k: SID)
    return importlib.import_module(key + ".storage_journal_windows_identity")


def test_sid_output_only_current_returnlength():
    m = load()
    base = 4096
    data = struct.pack("<QI", base + 16, 0) + bytes(4) + SID
    assert m._parse_sid(data, base=base, header=16, user=True) == SID
    for pointer in (base + 12, base + 17, base + 28, base + 65536, 131328):
        bad = struct.pack("<QI", pointer, 0) + data[12:]
        with pytest.raises(Exception, match="PRINCIPAL_UNACCREDITED"):
            m._parse_sid(bad, base=base, header=16, user=True)


@pytest.mark.parametrize(
    "sid",
    [
        bytes(12),
        bytes([1, 0]) + bytes(10),
        bytes([2, 1]) + bytes(10),
        bytes([1, 16]) + bytes(70),
    ],
)
def test_sid_revision_count_and_attributes(sid):
    m = load()
    bad = struct.pack("<QI", 4112, 0) + bytes(4) + sid
    with pytest.raises(Exception, match="PRINCIPAL_UNACCREDITED"):
        m._parse_sid(bad, base=4096, header=16, user=True)


def test_cpu_authority_is_separate_and_native_precheck_denies():
    m = load()
    factory = getattr(m, "_assemble_cpu_identity_session", lambda *a, **k: None)
    ops_type = getattr(m, "_CpuIdentityOps", lambda f: f)
    authority = factory(
        ops_type(lambda call: None), principal_sid=SID, primary_group_sid=SID
    )
    assert type(authority).__name__ == "_CpuDeployerAuthority"
    check = getattr(m, "_validate_current_admission", lambda a: None)
    with pytest.raises(Exception, match="ADMISSION_REQUIRED"):
        check(authority)


def test_native_bootstrap_platform_gate_before_loader(monkeypatch):
    m = load()
    monkeypatch.setattr(sys, "platform", "linux")
    bootstrap = getattr(m, "_bootstrap_current_deployer", lambda: None)
    with pytest.raises(Exception, match="PLATFORM_UNSUPPORTED"):
        bootstrap()


def test_k2_future_owner_seams_fail_closed():
    m = load()
    for name in (
        "_bind_acquisition_owner",
        "_pin_current_acquisition_admission",
        "_complete_acquisition_admission_pin",
        "_abort_acquisition_admission_pin",
        "_pin_cpu_acquisition_admission",
    ):
        seam = getattr(m, name, lambda *a, **k: None)
        with pytest.raises(Exception, match="ADMISSION_REQUIRED"):
            seam({}, owner={})


class TokenSdk:
    def __init__(self, module):
        self.m = module
        self.calls = []
        self.fail = None
        self.stamp = (1, 2, 3)
        self.next_handle = 101

    def execute(self, call):
        self.calls.append(call.function)
        step = call.frame_ref.plan[call.ordinal]
        storage = call.frame_ref.storage
        if call.function.startswith("GetCurrent"):
            return self.m._ContextPseudoResult(
                2**64 - (1 if call.function.endswith("Process") else 2)
            )
        if call.function == "OpenThreadToken":
            return self.m._TokenBoolResult(False, 1008)
        if call.function == "OpenProcessToken":
            struct.pack_into("<Q", storage, step.offset, self.next_handle)
            self.next_handle += 1
        elif call.function == "GetTokenInformation":
            size = {1: 28, 5: 20, 8: 4, 10: 56}[step.info_class]
            struct.pack_into("<I", storage, step.return_offset, size)
            if step.sizing:
                return self.m._TokenBoolResult(False, 122)
            if step.info_class == 8:
                struct.pack_into("<i", storage, step.offset, 1)
            elif step.info_class == 10:
                raw = bytearray(56)
                for off, value in zip((0, 8, 48), self.stamp, strict=True):
                    struct.pack_into("<Ii", raw, off, value, 0)
                struct.pack_into("<i", raw, 24, 1)
                storage[step.offset : step.offset + 56] = raw
            else:
                header = 16 if step.info_class == 1 else 8
                struct.pack_into(
                    "<Q",
                    storage,
                    step.offset,
                    step.offset + header + call.frame_ref.base,
                )
                if step.info_class == 1:
                    struct.pack_into("<I", storage, step.offset + 8, 0)
                storage[step.offset + header : step.offset + header + len(SID)] = SID
        if self.fail == call.function:
            return self.m._TokenBoolResult(False, 5)
        return self.m._TokenBoolResult(True, None)


def test_cpu_issue_requires_fresh_observation_and_scope():
    m = load()
    sdk = TokenSdk(m)
    authority = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    issue = getattr(m, "_issue_cpu_acquisition_admission", lambda *a, **k: None)
    admission = issue(authority, scope=m._AdmissionScope.CANDIDATE_READ_ONLY)
    assert type(admission).__name__ == "_CpuAdmission"
    assert sdk.calls.count("GetTokenInformation") == 12
    assert sdk.calls.count("CloseHandle") == 2
    with pytest.raises(Exception, match="ADMISSION_REQUIRED"):
        m._validate_current_admission(admission)
    calls = len(sdk.calls)
    with pytest.raises(Exception, match="ADMISSION_REQUIRED"):
        issue(authority, scope=m._AdmissionScope.OWNED_PROBE_CANDIDATE)
    assert len(sdk.calls) == calls


@pytest.mark.parametrize(
    "fault",
    [
        "thread_denied",
        "thread_false_output",
        "thread_true",
        "stats_drift",
        "stats_type",
        "fixed_length",
        "variable_capacity",
        "bad_result",
        "close_unknown",
    ],
)
def test_cpu_observation_causal_rejection(fault):
    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        storage = call.frame_ref.storage
        if call.function == "OpenThreadToken":
            if fault == "thread_denied":
                return m._TokenBoolResult(False, 5)
            if fault == "thread_false_output":
                struct.pack_into("<Q", storage, step.offset, 123)
            if fault == "thread_true":
                struct.pack_into("<Q", storage, step.offset, 123)
                return m._TokenBoolResult(True)
        if call.function == "GetTokenInformation":
            if fault == "fixed_length" and step.info_class == 10:
                struct.pack_into("<I", storage, step.return_offset, 57)
            if fault == "variable_capacity" and step.info_class == 1:
                struct.pack_into("<I", storage, step.return_offset, 65537)
            if not step.sizing and step.info_class == 10:
                if fault == "stats_drift" and step.offset == 120:
                    struct.pack_into("<I", storage, step.offset + 48, 99)
                if fault == "stats_type":
                    struct.pack_into("<i", storage, step.offset + 24, 2)
        if fault == "bad_result" and call.function == "OpenProcessToken":
            return object()
        if fault == "close_unknown" and call.function == "CloseHandle":
            raise KeyboardInterrupt("private-sentinel")
        return result

    authority = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(execute), principal_sid=SID, primary_group_sid=SID
    )
    issue = getattr(m, "_issue_cpu_acquisition_admission", lambda *a, **k: None)
    code = (
        "RESOURCE_UNKNOWN"
        if fault in {"thread_false_output", "bad_result", "close_unknown"}
        else "PRINCIPAL_UNACCREDITED"
    )
    with pytest.raises(Exception, match=code):
        issue(authority, scope=m._AdmissionScope.CANDIDATE_READ_ONLY)


def test_cpu_admissions_lifetime_quota_before_calls():
    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    for scope in (
        m._AdmissionScope.CANDIDATE_READ_ONLY,
        m._AdmissionScope.PRODUCT_CHAIN_CANDIDATE,
    ):
        for _ in range(2):
            m._issue_cpu_acquisition_admission(a, scope=scope)
    before = len(sdk.calls)
    with pytest.raises(Exception, match="OWNER_RETIRE_REQUIRED"):
        m._issue_cpu_acquisition_admission(
            a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
        )
    assert len(sdk.calls) == before


def test_diagnostic_dto_sanitizes_rejects_unbounded_data():
    m = load()
    info = getattr(m, "IdentityInfo", lambda **kw: kw)
    result = info(
        state="live",
        source="cpu_double",
        admissions=0,
        threads=0,
        pins=0,
        observations=0,
        scopes=(),
    )
    assert type(result).__name__ == "IdentityInfo"
    assert "SID" not in repr(result)
    with pytest.raises(ValueError, match="DIAGNOSTIC_INVALID"):
        info(
            state="private-path-sentinel",
            source="cpu_double",
            admissions=0,
            threads=0,
            pins=0,
            observations=0,
            scopes=(),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("observations", 8192),
        ("subcalls", 229376),
        ("observations", True),
        ("subcalls", -1),
    ],
)
def test_cpu_observation_quota_reserves_before_sdk(field, value):
    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    r = m._CPU_AUTHORITIES[a]
    r.counters = {"observations": 0, "subcalls": 0}
    r.counters[field] = value
    with pytest.raises(Exception, match="OWNER_RETIRE_REQUIRED"):
        m._cpu_observe(r)
    assert sdk.calls == []


def test_cpu_known_frame_discards_raw_but_unknown_keeps_it():
    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    m._issue_cpu_acquisition_admission(a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY)
    r = m._CPU_AUTHORITIES[a]
    assert all(
        len(call.frame_ref.storage) == 0 and call.preimage == b"" for call in r.calls
    )


def test_cpu_records_have_nominal_issuer_policy_epoch():
    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    admission = m._issue_cpu_acquisition_admission(
        a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
    )
    r = m._CPU_AUTHORITIES[a].admissions[admission]
    assert type(r).__name__ == "_AdmissionRecord"
    assert r.capability is admission and r.principal_ratification_ref is a
    assert type(r.issuer_ref).__name__ == "_CpuIssuer"
    assert type(r.policy_ref).__name__ == "_CpuSecurityPolicy"
    assert type(r.epoch_ref).__name__ == "_CpuPolicyEpoch"
    assert r.source == "cpu_double" and r.state == "live"
    with pytest.raises(m.IdentityError) as error:
        m._validate_current_admission(admission)
    assert error.value.diagnostic.code == "ADMISSION_REQUIRED"


def test_future_native_seams_emit_typed_sanitized_diagnostic():
    m = load()
    with pytest.raises(Exception) as error:
        m._bind_acquisition_owner({"sid": "secret-sentinel"}, owner={})
    assert (
        getattr(getattr(error.value, "diagnostic", None), "code", None)
        == "ADMISSION_REQUIRED"
    )
    assert "secret-sentinel" not in repr(error.value)


def test_call_registry_uses_reference_not_dataclass_equality():
    from dataclasses import replace

    m = load()
    call = m._CpuTokenCallRecord(
        0, "CloseHandle", "entered", object(), m._CpuFrame(), (), (), b""
    )
    clone = replace(call)
    assert call == clone and call is not clone
    check = getattr(m, "_registered_call_reference", lambda refs, item: item in refs)
    assert check([call], call)
    assert not check([call], clone)


def test_cpu_post_true_before_ownership_cut_retains_preimage():
    import inspect

    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    r = m._CPU_AUTHORITIES[a]
    lines, start = inspect.getsourcelines(m._cpu_open)
    line_number = start + next(
        i for i, text in enumerate(lines) if "handle = struct.unpack" in text
    )

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is m._cpu_open.__code__
            and frame.f_lineno == line_number
            and frame.f_locals["thread"] is False
        ):
            raise RuntimeError("secret-cut-sentinel")
        return cut

    try:
        previous_trace = sys.gettrace()
        sys.settrace(cut)
        with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
            m._issue_cpu_acquisition_admission(
                a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
            )
    finally:
        sys.settrace(previous_trace)
    assert r.state == "unknown" and sdk.calls.count("CloseHandle") == 0
    assert len(r.calls[-1].preimage) == 131328
    assert len(r.frame.storage) == 131328


@pytest.mark.parametrize("fault", ["source", "issuer", "policy", "epoch"])
def test_cpu_source_and_epoch_reject_before_callbacks(fault):
    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    r = m._CPU_AUTHORITIES[a]
    if fault == "source":
        r.source = "native_windows_x64"
    elif fault == "issuer":
        r.issuer_ref = object()
    elif fault == "policy":
        m._CPU_CAPABILITIES[r.policy_ref].doctrine = "caller-policy"
    else:
        m._CPU_CAPABILITIES[r.epoch_ref].state = "revoked"
    with pytest.raises(Exception, match="CAPABILITY_INVALID|CAPABILITY_REVOKED"):
        m._issue_cpu_acquisition_admission(
            a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
        )
    assert sdk.calls == []


def test_cpu_raw_frame_already_active_rejects_before_calls():
    m = load()
    sdk = TokenSdk(m)
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    r = m._CPU_AUTHORITIES[a]
    r.frame = object()
    with pytest.raises(Exception, match="OWNER_RETIRE_REQUIRED"):
        m._cpu_observe(r)
    assert sdk.calls == []


def test_sdk_ranges_do_not_expand_into_other_buffer_or_tail():
    m = load()
    valid = getattr(m, "_sdk_step_ranges_valid", lambda step, ranges: True)
    step = m._QueryStep(
        "GetTokenInformation",
        offset=256,
        return_offset=40,
        info_class=1,
        capacity=65536,
        token=101,
    )
    nominal = ((40, 4), (256, 65536))
    assert valid(step, nominal)
    for bad in (
        ((40, 4), (256, 65537)),
        ((40, 4), (65792, 65536)),
        ((40, 4), (131328, 256)),
        ((40, True), (256, 65536)),
    ):
        assert not valid(step, bad)
    step.capacity = True
    assert not valid(step, ((40, 4), (256, 1)))


@pytest.mark.parametrize("user", [True, False])
def test_sid_last_byte_of_capacity_65536_is_allowed(user):
    m = load()
    sid = bytes([1, 15, 0, 0, 0, 0, 0, 5]) + bytes(60)
    base = 4096 + (256 if user else 65792)
    data = bytearray(65536)
    struct.pack_into("<Q", data, 0, base + len(data) - len(sid))
    data[-len(sid) :] = sid
    assert (
        m._parse_sid(bytes(data), base=base, header=16 if user else 8, user=user) == sid
    )
    for pointer in (
        base + len(data) - len(sid) + 4,
        base + len(data),
        4096 + 131328,
        4096 + 131584,
    ):
        struct.pack_into("<Q", data, 0, pointer)
        with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
            m._parse_sid(bytes(data), base=base, header=16 if user else 8, user=user)


def test_cpu_fetch_capacity_65536_without_retry_regression():
    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if call.function == "GetTokenInformation" and step.info_class in (1, 5):
            struct.pack_into("<I", call.frame_ref.storage, step.return_offset, 65536)
        return result

    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(execute), principal_sid=SID, primary_group_sid=SID
    )
    admission = m._issue_cpu_acquisition_admission(
        a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
    )
    assert type(admission) is m._CpuAdmission
    assert sdk.calls.count("GetTokenInformation") == 12
    assert sdk.calls.count("CloseHandle") == 2


def test_identity_reload_cannot_reset_kernel_bootstrap_latch(monkeypatch):
    m = load()
    m._io._kernel_identity_bootstrap_claim()
    io = m._io
    m = importlib.reload(m)
    assert m._io is io and io._IDENTITY_BOOTSTRAP_CONSUMED
    monkeypatch.setattr(m.platform, "machine", lambda: "amd64")
    monkeypatch.setattr(m.os, "name", "nt")
    monkeypatch.setattr(m.sys, "platform", "win32")
    with pytest.raises(m.IdentityError, match="OWNER_RETIRE_REQUIRED"):
        m._bootstrap_current_deployer()


def test_fake_native_caps_and_cpu_authority_never_bind(monkeypatch):
    import copy
    import pickle

    m = load()
    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(lambda call: None), principal_sid=SID, primary_group_sid=SID
    )
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
            operation(a)
    with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
        m._DeployerAuthority()
    for candidate in (
        {"trusted": True},
        object.__new__(m._DeployerAuthority),
        a,
        m.IdentityInfo("live", "cpu_double", 0, 0, 0, 0, ()),
    ):
        with pytest.raises(m.IdentityError, match="CAPABILITY_INVALID"):
            m._issue_acquisition_admission(
                candidate, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
            )
    for candidate in ({}, object.__new__(m._AcquisitionAdmission), a):
        with pytest.raises(m.IdentityError, match="ADMISSION_REQUIRED"):
            m._validate_current_admission(candidate)


@pytest.mark.parametrize(
    "field,value",
    [
        ("win32_error", True),
        ("win32_error", 2**32),
        ("ntstatus", 0),
        ("operation", "private-sentinel"),
        ("code", "private-sentinel"),
    ],
)
def test_identity_diagnostic_exact_types(field, value):
    m = load()
    data = {
        "code": "RESOURCE_UNKNOWN",
        "operation": "query",
        "win32_error": None,
        "ntstatus": None,
    }
    data[field] = value
    with pytest.raises(ValueError, match="DIAGNOSTIC_INVALID"):
        m.IdentityDiagnostic(**data)


@pytest.mark.parametrize(
    "name",
    [
        "_issue_acquisition_admission",
        "_revoke_deployer_authority",
        "_close_deployer_authority",
        "_identity_info",
    ],
)
def test_root_seams_accept_deployer_authority_keyword(name):
    m = load()
    kwargs = {"deployer_authority": object()}
    if name == "_issue_acquisition_admission":
        kwargs["scope"] = m._AdmissionScope.CANDIDATE_READ_ONLY
    with pytest.raises(m.IdentityError, match="CAPABILITY_INVALID"):
        getattr(m, name)(**kwargs)


def test_alias_cannot_enter_another_native_domain(monkeypatch):
    m = load()
    entered = []

    def entered_root():
        entered.append("root")
        raise RuntimeError("alias-entered-root")

    monkeypatch.setattr(m, "os", types.SimpleNamespace(name="nt"))
    monkeypatch.setattr(m, "platform", types.SimpleNamespace(machine=lambda: "amd64"))
    monkeypatch.setattr(
        m,
        "sys",
        types.SimpleNamespace(platform="win32", maxsize=2**63 - 1, modules=sys.modules),
    )
    monkeypatch.setattr(m, "_bootstrap_native", entered_root)
    with pytest.raises(m.IdentityError, match="OWNER_RETIRE_REQUIRED"):
        m._bootstrap_current_deployer()
    assert entered == []


@pytest.mark.parametrize("close_fault", ["false", "cut"])
def test_primary_principal_rejection_survives_unknown_cleanup(close_fault):
    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            call.function == "GetTokenInformation"
            and step.info_class == 8
            and not step.sizing
        ):
            struct.pack_into("<i", call.frame_ref.storage, step.offset, 2)
        if call.function == "CloseHandle":
            if close_fault == "cut":
                raise RuntimeError("private-close-sentinel")
            return m._TokenBoolResult(False, 5)
        return result

    a = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(execute), principal_sid=SID, primary_group_sid=SID
    )
    with pytest.raises(m.IdentityError) as error:
        m._issue_cpu_acquisition_admission(
            a, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
        )
    assert error.value.diagnostic.code == "PRINCIPAL_UNACCREDITED"
    assert error.value.cleanup.state == "unknown"
    assert error.value.cleanup.diagnostics[0].code == "RESOURCE_UNKNOWN"
    assert m._CPU_AUTHORITIES[a].state == "unknown"
    assert sdk.calls.count("CloseHandle") == 1
    assert "private-close-sentinel" not in repr(error.value)


@pytest.mark.parametrize(
    "exception_type",
    [ValueError, RuntimeError, KeyboardInterrupt, "identity", "private"],
)
@pytest.mark.parametrize("message", ["PRINCIPAL_UNACCREDITED", "private-cut-sentinel"])
def test_fix1_post_true_cut_preserves_actual_output(exception_type, message):
    import inspect

    m = load()
    sdk = TokenSdk(m)
    authority = m._assemble_cpu_identity_session(
        m._CpuIdentityOps(sdk.execute), principal_sid=SID, primary_group_sid=SID
    )
    record = m._CPU_AUTHORITIES[authority]
    lines, start = inspect.getsourcelines(m._cpu_open)
    target = start + next(
        i for i, text in enumerate(lines) if "handle = struct.unpack" in text
    )
    if exception_type == "identity":
        cut_error = m.IdentityError(
            m.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query")
        )
    elif exception_type == "private":

        class PrivateCut(ValueError):
            pass

        cut_error = PrivateCut(message)
    else:
        cut_error = exception_type(message)

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is m._cpu_open.__code__
            and frame.f_lineno == target
            and not frame.f_locals["thread"]
        ):
            raise cut_error
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
            m._issue_cpu_acquisition_admission(
                authority, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
            )
    finally:
        sys.settrace(previous)
    assert record.state == "unknown"
    assert sdk.calls.count("CloseHandle") == 0
    assert len(record.frame.storage) == 131328
    call = record.calls[-1]
    assert len(call.preimage) == 131328
    assert struct.unpack_from("<Q", call.preimage, 8)[0] == 0
    assert struct.unpack_from("<Q", record.frame.storage, 8)[0] == 101
    assert call.raw_result.success is True and call.error is cut_error
    assert record.frame.handles == {}
    calls = tuple(sdk.calls)
    with pytest.raises(ValueError, match="CAPABILITY_REVOKED"):
        m._issue_cpu_acquisition_admission(
            authority, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
        )
    assert tuple(sdk.calls) == calls


def test_fix1_poisoned_boundary_is_typed_before_query():
    import ast
    import inspect
    import threading

    m = load()
    tree = ast.parse(inspect.getsource(m._issue_acquisition_admission))
    # CPU control-flow proof: no native capability or admission is manufactured.
    row = types.SimpleNamespace(state="live")
    session = types.SimpleNamespace(lock=threading.RLock())
    called = []
    namespace = dict(m.__dict__)
    namespace["_authority_record"] = lambda authority, operation: (row, session)
    namespace["_native_live"] = lambda *args: called.append("query")
    exec(compile(tree, "<CPU-AST-boundary-poison>", "exec"), namespace)  # noqa: S102 - AST CPU no coverage original
    m._io._KERNEL_POISONED = True
    with pytest.raises(m.IdentityError) as error:
        namespace["_issue_acquisition_admission"](
            object(), scope=m._AdmissionScope.CANDIDATE_READ_ONLY
        )
    assert error.value.diagnostic.code == "OWNER_RETIRE_REQUIRED"
    assert error.value.diagnostic.operation == "issue"
    assert m._io._KERNEL_POISONED and called == []


def cpu_record(module, execute):
    authority = module._assemble_cpu_identity_session(
        module._CpuIdentityOps(execute), principal_sid=SID, primary_group_sid=SID
    )
    return module._CPU_AUTHORITIES[authority]


def test_cpu_factory_invalid_callback_never_registers_authority():
    m = load()
    with pytest.raises(ValueError, match="CAPABILITY_INVALID"):
        m._assemble_cpu_identity_session(
            m._CpuIdentityOps(None), principal_sid=SID, primary_group_sid=SID
        )
    assert m._CPU_AUTHORITIES == {} and m._CPU_CAPABILITIES == {}
    assert m._io._LIVE_IDENTITY_SESSIONS == {}


@pytest.mark.parametrize(
    "operation", ["alias_bootstrap", "source_gate", "unknown_gate", "authority_info"]
)
def test_principal_protection_guards_refuse_registered_cpu_before_resource_loader(
    operation,
):
    import inspect

    m = load()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    callbacks = []
    record = cpu_record(m, callbacks.append)
    loaders = []
    loader_codes = {
        inspect.unwrap(m._bootstrap_native).__code__,
        inspect.unwrap(abi._new_native_identity_backend).__code__,
    }
    prior = sys.getprofile()

    def observe(python_frame, event, arg):
        if event == "call" and python_frame.f_code in loader_codes:
            loaders.append(python_frame.f_code.co_name)

    expected = (
        "OWNER_RETIRE_REQUIRED"
        if operation in {"alias_bootstrap", "unknown_gate"}
        else "CAPABILITY_INVALID"
    )
    if operation == "unknown_gate":
        record.state = "unknown"
    try:
        sys.setprofile(observe)
        with pytest.raises(m.IdentityError, match=expected):
            if operation == "alias_bootstrap":
                m._require_canonical_identity_instance()
            elif operation == "authority_info":
                m._identity_info(record.capability)
            else:
                m._native_live(record, "query")
    finally:
        sys.setprofile(prior)
    assert callbacks == loaders == [] and record.source == "cpu_double"
    assert m._io._LIVE_IDENTITY_SESSIONS == {} and record.admissions == {}


@pytest.mark.parametrize("operation", ["complete", "abort"])
def test_cpu_pin_terminal_unknown_reference_stops_before_target_or_queries(operation):
    m = load()
    sdk = TokenSdk(m)
    record = cpu_record(m, sdk.execute)
    admission = m._issue_cpu_acquisition_admission(
        record.capability, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
    )
    acquisition = importlib.import_module(
        m.__package__ + ".storage_journal_windows_acquisition"
    )
    owner_callbacks = []
    owner = acquisition._assemble_cpu_acquisition_owner(
        acquisition._AcquisitionOps(*((owner_callbacks.append,) * 4)),
        principal_sid=SID,
        primary_group_sid=SID,
    )
    before = tuple(record.calls)
    function = (
        m._complete_cpu_acquisition_admission_pin
        if operation == "complete"
        else m._abort_cpu_acquisition_admission_pin
    )
    with pytest.raises(m.IdentityError, match="ADMISSION_REQUIRED"):
        function(object(), owner=owner)
    assert tuple(record.calls) == before and record.pins == {}
    assert (
        record.admissions[admission].state == "live" and record.source == "cpu_double"
    )
    assert (
        owner_callbacks == []
        and acquisition._LIVE_ACQUISITION_OWNERS[owner].source == "cpu_double"
    )


def test_cpu_unknown_sdk_query_does_not_invoke_any_callback():
    m = load()
    callbacks = []
    record = cpu_record(m, callbacks.append)
    frame = m._CpuFrame()
    step = m._QueryStep("ReadFile")
    with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
        m._cpu_call(record, frame, step)
    assert callbacks == [] and record.calls == [] and frame.plan == [step]
    assert record.source == "cpu_double" and not m._io._KERNEL_POISONED


def test_cpu_second_close_keeps_first_true_and_never_retries_sdk_callback():
    m = load()
    sdk = TokenSdk(m)
    record = cpu_record(m, sdk.execute)
    frame = m._CpuFrame()
    handle = m._cpu_open(record, frame, thread=False, offset=8)
    result, known_call = m._cpu_call(
        record, frame, m._QueryStep("CloseHandle", token=handle)
    )
    assert result.success is True and known_call.close_attempted
    before = tuple(sdk.calls)
    with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
        m._cpu_call(record, frame, m._QueryStep("CloseHandle", token=handle))
    assert tuple(sdk.calls) == before and sdk.calls.count("CloseHandle") == 1
    failed_call = record.calls[-1]
    assert failed_call.raw_result is None and not failed_call.close_attempted
    assert known_call.raw_result is result and frame.handles[handle] is True
    assert record.state == "unknown" and m._io._KERNEL_POISONED


@pytest.mark.parametrize(
    "cut", ["user_attributes", "postcleanup_thread", "postquery_unknown"]
)
def test_cpu_query_semantic_or_custody_cut_uses_actual_callback_and_retained_frame(cut):
    import threading

    m = load()
    sdk = TokenSdk(m)
    reached = []
    record = None

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            cut == "user_attributes"
            and step.function == "GetTokenInformation"
            and step.info_class == 1
            and not step.sizing
        ):
            struct.pack_into("<I", call.frame_ref.storage, step.offset + 8, 2)
            reached.append(call)
        elif (
            cut == "postcleanup_thread"
            and step.function == "CloseHandle"
            and sdk.calls.count("CloseHandle") == 2
        ):
            call.frame_ref.thread_id = threading.get_native_id() + 1
            reached.append(call)
        elif (
            cut == "postquery_unknown"
            and step.function == "OpenThreadToken"
            and sdk.calls.count("OpenThreadToken") == 2
        ):
            record.state = "unknown"
            reached.append(call)
        return result

    record = cpu_record(m, execute)
    with pytest.raises(
        ValueError,
        match="PRINCIPAL_UNACCREDITED"
        if cut == "user_attributes"
        else "RESOURCE_UNKNOWN",
    ):
        m._issue_cpu_acquisition_admission(
            record.capability, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
        )
    assert (
        len(reached) == 1 and record.admissions == {} and record.source == "cpu_double"
    )
    assert record.frame is not None and len(record.frame.storage) == 131328
    if cut == "user_attributes":
        assert record.state == "revoked" and record.frame.cleanup_complete
        assert sdk.calls.count("CloseHandle") == 1 and not m._io._KERNEL_POISONED
    else:
        assert record.state == "unknown" and m._io._KERNEL_POISONED
        assert sdk.calls.count("CloseHandle") == (
            2 if cut == "postcleanup_thread" else 0
        )
        assert reached[0].raw_result is not None


@pytest.mark.parametrize(
    "sid", [None, bytearray(SID), b"", bytes(69), bytes(12), bytes([1, 2]) + bytes(10)]
)
def test_cpu_session_rejects_unaccredited_binary_sid_before_callbacks(sid):
    m = load()
    callbacks = []
    with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
        m._assemble_cpu_identity_session(
            m._CpuIdentityOps(callbacks.append),
            principal_sid=sid,
            primary_group_sid=SID,
        )
    assert callbacks == [] and m._CPU_AUTHORITIES == {}
    assert m._io._LIVE_IDENTITY_SESSIONS == {}


@pytest.mark.parametrize(
    "fault", ["pid", "frame_thread", "revoked", "plan_limit", "poison"]
)
def test_cpu_query_invalid_lease_stops_second_callback_after_actual_first(fault):
    import threading

    m = load()
    callbacks = []

    def execute(call):
        callbacks.append(call.function)
        return m._ContextPseudoResult(2**64 - 1)

    record = cpu_record(m, execute)
    frame = m._CpuFrame()
    first, first_call = m._cpu_call(record, frame, m._QueryStep("GetCurrentProcess"))
    assert first.value == 2**64 - 1 and first_call.phase == "recognized"
    if fault == "pid":
        record.pid += 1
    elif fault == "frame_thread":
        frame.thread_id = threading.get_native_id() + 1
    elif fault == "revoked":
        record.state = "revoked"
    elif fault == "plan_limit":
        frame.plan.extend(m._QueryStep("GetCurrentProcess") for _ in range(27))
    else:
        m._io._KERNEL_POISONED = True
    expected = (
        "OWNER_MISMATCH"
        if fault in {"pid", "frame_thread"}
        else "OWNER_RETIRE_REQUIRED"
    )
    with pytest.raises(ValueError, match=expected):
        m._cpu_call(record, frame, m._QueryStep("GetCurrentProcess"))
    assert callbacks == ["GetCurrentProcess"] and record.calls == [first_call]
    assert first_call.raw_result is first and record.source == "cpu_double"


@pytest.mark.parametrize(
    "fault",
    [
        "pid",
        "root_authority",
        "root_revoked",
        "authority_revoked",
        "probe_scope",
        "principal",
    ],
)
def test_cpu_admission_issuance_provenance_and_scope_stay_cpu_only(fault):
    m = load()
    sdk = TokenSdk(m)
    callbacks = []

    def execute(call):
        callbacks.append(call.function)
        return sdk.execute(call)

    record = cpu_record(m, execute)
    scope = m._AdmissionScope.CANDIDATE_READ_ONLY
    if fault == "pid":
        record.pid += 1
    elif fault == "root_authority":
        m._CPU_CAPABILITIES[record.policy_ref].authority_ref = object()
    elif fault == "root_revoked":
        m._CPU_CAPABILITIES[record.policy_ref].state = "revoked"
    elif fault == "authority_revoked":
        record.state = "revoked"
    elif fault == "probe_scope":
        scope = m._AdmissionScope.OWNED_PROBE_CANDIDATE
    else:
        record.principal_sid = SID[:-4] + struct.pack("<I", 22)
    expected = {
        "pid": "CAPABILITY_INVALID",
        "root_authority": "CAPABILITY_INVALID",
        "root_revoked": "CAPABILITY_REVOKED",
        "authority_revoked": "CAPABILITY_REVOKED",
        "probe_scope": "ADMISSION_REQUIRED",
        "principal": "PRINCIPAL_UNACCREDITED",
    }[fault]
    with pytest.raises(ValueError, match=expected):
        m._issue_cpu_acquisition_admission(record.capability, scope=scope)
    assert record.admissions == {} and record.source == "cpu_double"
    assert bool(callbacks) is (fault == "principal")
    assert m._io._LIVE_IDENTITY_SESSIONS == {}


@pytest.mark.parametrize("fault", ["thread_limit", "thread_epoch", "buffer_pending"])
def test_cpu_observation_preflight_retains_history_without_callback(fault):
    import threading

    m = load()
    callbacks = []
    record = cpu_record(m, callbacks.append)
    if fault == "thread_limit":
        record.threads = {threading.Thread(): index for index in range(8)}
    elif fault == "thread_epoch":
        record.threads[threading.current_thread()] = threading.get_native_id() + 1
    else:
        record.frame = m._CpuFrame()
    threads_before = dict(record.threads)
    frame_before = record.frame
    with pytest.raises(
        ValueError,
        match="OWNER_MISMATCH" if fault == "thread_epoch" else "OWNER_RETIRE_REQUIRED",
    ):
        m._cpu_observe(record)
    assert callbacks == [] and record.state == "revoked"
    assert record.threads == threads_before and record.frame is frame_before
    assert record.counters == {"observations": 0, "subcalls": 0}


@pytest.mark.parametrize(
    "fault", ["pid", "admission_revoked", "authority_revoked", "policy", "unregistered"]
)
def test_cpu_admission_current_rejects_stale_reference_without_new_queries(fault):
    m = load()
    sdk = TokenSdk(m)
    record = cpu_record(m, sdk.execute)
    admission = m._issue_cpu_acquisition_admission(
        record.capability, scope=m._AdmissionScope.CANDIDATE_READ_ONLY
    )
    calls_before = tuple(record.calls)
    row = record.admissions[admission]
    if fault == "pid":
        record.pid += 1
    elif fault == "admission_revoked":
        row.state = "revoked"
    elif fault == "authority_revoked":
        record.state = "revoked"
    elif fault == "policy":
        row.policy_ref = object()
    else:
        record.admissions.pop(admission)
    expected = (
        "ADMISSION_REQUIRED"
        if fault in {"pid", "unregistered"}
        else "CAPABILITY_REVOKED"
    )
    with pytest.raises(m.IdentityError, match=expected):
        m._cpu_admission_current(record, admission, "complete")
    assert tuple(record.calls) == calls_before and len(calls_before) > 0
    assert type(admission) is m._CpuAdmission and record.source == "cpu_double"


@pytest.mark.parametrize(
    "fault",
    ["dto", "boolean", "error_type", "error_bound", "true_error", "false_missing"],
)
def test_fix1_call_result_guard(fault):
    m = load()
    sdk = TokenSdk(m)
    reached = []

    def execute(call):
        sdk.execute(call)
        reached.append(call.function)
        if fault == "dto":
            return types.SimpleNamespace(success=True, error=None)
        if fault == "boolean":
            return m._TokenBoolResult(1)
        if fault == "error_type":
            return m._TokenBoolResult(False, True)
        if fault == "error_bound":
            return m._TokenBoolResult(False, 2**32)
        if fault == "true_error":
            return m._TokenBoolResult(True, 5)
        return m._TokenBoolResult(False)

    record = cpu_record(m, execute)
    frame = m._CpuFrame()
    with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
        m._cpu_call(record, frame, m._QueryStep("OpenProcessToken", offset=8))
    assert reached == ["OpenProcessToken"]
    assert record.state == "unknown" and len(frame.storage) == 131328
    assert record.calls[-1].raw_result is not None


@pytest.mark.parametrize("fault", ["dto", "exact_int", "lower", "upper"])
def test_fix1_pseudo_result_guard(fault):
    m = load()
    reached = []
    value = {"exact_int": True, "lower": 1, "upper": 2**64}.get(fault, 2**64 - 1)

    def execute(call):
        reached.append(call.function)
        return (
            types.SimpleNamespace(value=value)
            if fault == "dto"
            else m._ContextPseudoResult(value)
        )

    record = cpu_record(m, execute)
    frame = m._CpuFrame()
    with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
        m._cpu_call(record, frame, m._QueryStep("GetCurrentProcess"))
    assert reached == ["GetCurrentProcess"] and record.state == "unknown"


@pytest.mark.parametrize(
    "fault",
    ["false_output", "thread_denied", "thread_true", "null", "pseudo", "duplicate"],
)
def test_fix1_open_guard(fault):
    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if call.function.startswith("Open"):
            if fault == "false_output":
                struct.pack_into("<Q", call.frame_ref.storage, step.offset, 123)
            elif fault == "thread_denied":
                return m._TokenBoolResult(False, 5)
            elif fault == "thread_true":
                struct.pack_into("<Q", call.frame_ref.storage, step.offset, 123)
                return m._TokenBoolResult(True)
            elif fault in {"null", "pseudo"}:
                struct.pack_into(
                    "<Q",
                    call.frame_ref.storage,
                    step.offset,
                    0 if fault == "null" else 2**64 - 1,
                )
        return result

    record = cpu_record(m, execute)
    frame = m._CpuFrame()
    if fault == "duplicate":
        frame.handles[101] = False
    thread = fault in {"false_output", "thread_denied", "thread_true"}
    code = (
        "PRINCIPAL_UNACCREDITED"
        if fault in {"thread_denied", "thread_true"}
        else "RESOURCE_UNKNOWN"
    )
    with pytest.raises(ValueError, match=code):
        m._cpu_open(record, frame, thread=thread, offset=0 if thread else 8)
    assert len(sdk.calls) == 2 and sdk.calls[-1].startswith("Open")
    if fault == "thread_true":
        assert frame.handles == {123: False}


@pytest.mark.parametrize(
    "fault",
    [
        "sizing_success",
        "sizing_error",
        "capacity_low",
        "capacity_high",
        "fill_failure",
        "length_low",
        "length_high",
    ],
)
def test_fix1_fetch_guard(fault):
    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if step.sizing:
            if fault == "sizing_success":
                return m._TokenBoolResult(True)
            if fault == "sizing_error":
                return m._TokenBoolResult(False, 5)
            if fault.startswith("capacity_"):
                struct.pack_into(
                    "<I",
                    call.frame_ref.storage,
                    step.return_offset,
                    27 if fault == "capacity_low" else 65537,
                )
        else:
            if fault == "fill_failure":
                return m._TokenBoolResult(False, 5)
            if fault.startswith("length_"):
                struct.pack_into(
                    "<I",
                    call.frame_ref.storage,
                    step.return_offset,
                    27 if fault == "length_low" else 29,
                )
        return result

    record = cpu_record(m, execute)
    frame = m._CpuFrame()
    with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
        m._cpu_fetch(
            record, frame, token=101, info_class=1, offset=256, return_offset=40
        )
    assert sdk.calls == ["GetTokenInformation"] * (
        2 if fault.startswith("length_") or fault == "fill_failure" else 1
    )
    assert len(frame.plan) == len(sdk.calls)


@pytest.mark.parametrize(
    "fault",
    ["step_type", "open_slot", "query_offset", "query_return", "query_capacity"],
)
def test_fix1_sdk_range_guard_reaches_boundary(fault):
    m = load()
    sdk = TokenSdk(m)
    record = cpu_record(m, sdk.execute)
    frame = m._CpuFrame()
    step = m._QueryStep("OpenProcessToken", offset=8)
    if fault == "step_type":
        step = types.SimpleNamespace(**step.__dict__)
    elif fault == "open_slot":
        step.offset = 40
    else:
        step = m._QueryStep("GetTokenInformation", 256, 40, 1, False, 28, 101)
        if fault == "query_offset":
            step.offset = 65792
        elif fault == "query_return":
            step.return_offset = 32
        else:
            step.capacity = 65537
    with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
        m._cpu_call(record, frame, step)
    assert sdk.calls == []


@pytest.mark.parametrize(
    "fault", ["stats_type", "stats_drift", "current_drift", "token_type"]
)
def test_fix1_observation_stamp_guard(fault):
    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if call.function == "GetTokenInformation" and not step.sizing:
            if step.info_class == 10:
                if fault == "stats_type":
                    struct.pack_into("<i", call.frame_ref.storage, step.offset + 24, 2)
                if (
                    fault == "stats_drift"
                    and step.offset == 120
                    or fault == "current_drift"
                    and step.offset == 176
                ):
                    struct.pack_into("<I", call.frame_ref.storage, step.offset + 48, 99)
            if fault == "token_type" and step.info_class == 8:
                struct.pack_into("<i", call.frame_ref.storage, step.offset, 2)
        return result

    record = cpu_record(m, execute)
    with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
        m._cpu_observe(record)
    assert "GetTokenInformation" in sdk.calls and "CloseHandle" in sdk.calls
    assert record.state == "revoked"


@pytest.mark.parametrize(
    "criterion",
    [
        "diagnostic_code_type",
        "diagnostic_code_enum",
        "diagnostic_operation_type",
        "diagnostic_operation_enum",
        "diagnostic_uint_type",
        "diagnostic_uint_bounds",
        "diagnostic_ntstatus",
        "close_state_type",
        "close_state_enum",
        "close_tuple",
        "close_item",
        "info_state_type",
        "info_state_enum",
        "info_source_type",
        "info_source_enum",
        "info_count_type",
        "info_count_bounds",
        "info_scope_tuple",
        "info_scope_count",
        "info_scope_type",
        "info_scope_enum",
        "error_diagnostic",
        "error_cleanup",
    ],
)
def test_fix1_dto_guard(criterion):
    m = load()

    class String(str):
        pass

    diagnostic = {
        "code": "RESOURCE_UNKNOWN",
        "operation": "query",
        "win32_error": None,
        "ntstatus": None,
    }
    close = {"state": "closed", "diagnostics": ()}
    info = {
        "state": "live",
        "source": "cpu_double",
        "admissions": 0,
        "threads": 0,
        "pins": 0,
        "observations": 0,
        "scopes": (),
    }
    factory = m.IdentityDiagnostic
    data = diagnostic
    if criterion.startswith("diagnostic_"):
        field, value = {
            "diagnostic_code_type": ("code", String("RESOURCE_UNKNOWN")),
            "diagnostic_code_enum": ("code", "private-code-sentinel"),
            "diagnostic_operation_type": ("operation", String("query")),
            "diagnostic_operation_enum": ("operation", "private-operation-sentinel"),
            "diagnostic_uint_type": ("win32_error", True),
            "diagnostic_uint_bounds": ("win32_error", 2**32),
            "diagnostic_ntstatus": ("ntstatus", 0),
        }[criterion]
        data[field] = value
    elif criterion.startswith("close_"):
        factory, data = m.IdentityCloseOutcome, close
        field, value = {
            "close_state_type": ("state", String("closed")),
            "close_state_enum": ("state", "private-state-sentinel"),
            "close_tuple": ("diagnostics", []),
            "close_item": (
                "diagnostics",
                (types.SimpleNamespace(code="RESOURCE_UNKNOWN", operation="query"),),
            ),
        }[criterion]
        data[field] = value
    elif criterion.startswith("info_"):
        factory, data = m.IdentityInfo, info
        field, value = {
            "info_state_type": ("state", String("live")),
            "info_state_enum": ("state", "private-state-sentinel"),
            "info_source_type": ("source", String("cpu_double")),
            "info_source_enum": ("source", "private-source-sentinel"),
            "info_count_type": ("admissions", True),
            "info_count_bounds": ("observations", 8193),
            "info_scope_tuple": ("scopes", []),
            "info_scope_count": ("scopes", ("CANDIDATE_READ_ONLY",) * 3),
            "info_scope_type": ("scopes", (String("CANDIDATE_READ_ONLY"),)),
            "info_scope_enum": ("scopes", ("private-scope-sentinel",)),
        }[criterion]
        data[field] = value
    else:
        factory = m.IdentityError
        data = {"diagnostic": m.IdentityDiagnostic(**diagnostic)}
        if criterion == "error_diagnostic":
            data["diagnostic"] = types.SimpleNamespace(**diagnostic)
        else:
            data["cleanup"] = types.SimpleNamespace(state="closed", diagnostics=())
    with pytest.raises(ValueError, match="DIAGNOSTIC_INVALID"):
        factory(**data)


@pytest.mark.parametrize("fault", ["exact_bytes", "length"])
def test_fix1_stamp_shape_from_actual_query(fault):
    m = load()
    sdk = TokenSdk(m)
    record = cpu_record(m, sdk.execute)
    frame = m._CpuFrame()
    data = m._cpu_fetch(
        record, frame, token=101, info_class=10, offset=64, return_offset=32
    )
    data = bytearray(data) if fault == "exact_bytes" else data + b"\0"
    with pytest.raises(ValueError, match="PRINCIPAL_UNACCREDITED"):
        m._stamp(data, frame=frame)
    assert sdk.calls == ["GetTokenInformation", "GetTokenInformation"]


def test_fix1_close_false_preserves_unknown_frame():
    m = load()
    sdk = TokenSdk(m)
    sdk.fail = "CloseHandle"
    record = cpu_record(m, sdk.execute)
    with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
        m._cpu_observe(record)
    assert record.state == "unknown" and sdk.calls.count("CloseHandle") == 1
    assert len(record.frame.storage) == 131328


def test_fix1_unknown_blocks_sibling_cpu_boundary():
    m = load()
    bad = cpu_record(m, lambda call: object())
    healthy = TokenSdk(m)
    sibling = cpu_record(m, healthy.execute)
    with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
        m._cpu_observe(bad)
    assert m._io._KERNEL_POISONED
    with pytest.raises(ValueError, match="OWNER_RETIRE_REQUIRED"):
        m._cpu_observe(sibling)
    assert healthy.calls == [] and bad.state == "unknown"


def test_fix1_boundary_poison_between_lookup_and_entry():
    import ast
    import inspect
    import threading

    m = load()
    tree = ast.parse(inspect.getsource(m._issue_acquisition_admission))
    lookup = threading.Event()
    resume = threading.Event()
    row = types.SimpleNamespace(state="live")
    session = types.SimpleNamespace(lock=threading.RLock())
    errors = []
    calls = []

    def authority_record(authority, operation):
        lookup.set()
        assert resume.wait(5)
        return row, session

    namespace = dict(m.__dict__)
    namespace["_authority_record"] = authority_record
    namespace["_native_live"] = lambda *args: calls.append("query")
    exec(compile(tree, "<CPU-AST-lookup-poison>", "exec"), namespace)  # noqa: S102 - AST CPU no coverage original

    def issue():
        try:
            namespace["_issue_acquisition_admission"](
                object(), scope=m._AdmissionScope.CANDIDATE_READ_ONLY
            )
        except Exception as error:  # noqa: BLE001 - devolver el fallo del hilo al assert principal
            errors.append(error)

    thread = threading.Thread(target=issue)
    thread.start()
    try:
        assert lookup.wait(5)
        with m._io._NATIVE_BOUNDARY_LOCK:
            m._io._KERNEL_POISONED = True
        resume.set()
        thread.join(5)
    finally:
        resume.set()
        thread.join(5)
    assert not thread.is_alive() and calls == []
    assert len(errors) == 1 and type(errors[0]) is m.IdentityError
    assert errors[0].diagnostic.code == "OWNER_RETIRE_REQUIRED"
    assert errors[0].diagnostic.operation == "issue" and m._io._KERNEL_POISONED


@pytest.mark.parametrize(
    "stage",
    ["returned", "own_register", "recognized_handle", "before_close", "semantic_raise"],
)
@pytest.mark.parametrize("kind", ["value", "private", "identity", "interrupt"])
def test_fix1_cuts_preserve_custody_at_each_handoff(stage, kind):
    import inspect

    m = load()
    sdk = TokenSdk(m)
    if stage == "semantic_raise":
        sdk.fail = "GetTokenInformation"
    record = cpu_record(m, sdk.execute)
    function, marker = {
        "returned": (inspect.unwrap(m._cpu_call), "call.raw_result = result"),
        "own_register": (m._cpu_open, "frame.handles[handle] = False"),
        "recognized_handle": (m._cpu_open, "call.recognized_handle = handle"),
        "before_close": (m._cpu_observe_impl, "for handle in reversed"),
        "semantic_raise": (m._reject_principal, "raise error from None"),
    }[stage]
    lines, start = inspect.getsourcelines(function)
    target = start + next(i for i, text in enumerate(lines) if marker in text)
    if kind == "identity":
        cut_error = m.IdentityError(
            m.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query")
        )
    elif kind == "private":
        cut_error = m._SemanticRejection("PRINCIPAL_UNACCREDITED")
    else:
        cut_error = (ValueError if kind == "value" else KeyboardInterrupt)(
            "PRINCIPAL_UNACCREDITED"
        )
    hit = []

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is function.__code__
            and frame.f_lineno == target
        ):
            if (
                stage == "returned"
                and frame.f_locals["step"].function != "OpenProcessToken"
            ):
                return cut
            if (
                stage in {"own_register", "recognized_handle"}
                and frame.f_locals["thread"]
            ):
                return cut
            hit.append(stage)
            raise cut_error
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(ValueError, match="RESOURCE_UNKNOWN"):
            m._cpu_observe(record)
    finally:
        sys.settrace(previous)
    assert hit == [stage] and record.state == "unknown" and m._io._KERNEL_POISONED
    assert sdk.calls.count("CloseHandle") == 0
    assert len(record.frame.storage) == 131328
    call = record.calls[-1]
    assert len(call.preimage) == 131328 and call.error is cut_error
    assert call.raw_result is not None
    if stage in {"returned", "own_register", "recognized_handle"}:
        assert call.raw_result.success is True
        assert struct.unpack_from("<Q", record.frame.storage, 8)[0] == 101


@pytest.mark.parametrize(
    "field,limit",
    [("admissions", 4), ("threads", 8), ("pins", 2048), ("observations", 8192)],
)
@pytest.mark.parametrize("fault", ["exact", "lower", "upper"])
def test_fix1_info_count_each_field(field, limit, fault):
    m = load()
    data = {
        "state": "live",
        "source": "cpu_double",
        "admissions": 0,
        "threads": 0,
        "pins": 0,
        "observations": 0,
        "scopes": (),
    }
    data[field] = {"exact": True, "lower": -1, "upper": limit + 1}[fault]
    with pytest.raises(ValueError, match="DIAGNOSTIC_INVALID"):
        m.IdentityInfo(**data)


@pytest.mark.parametrize("kind", ["same_semantic", "value", "interrupt", "public"])
@pytest.mark.parametrize(
    "stage", ["before_close", "after_close", "before_revoke", "at_revoke"]
)
def test_fix2_cleanup_cut_keeps_primary_and_shared_unknown(stage, kind):
    import inspect

    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            call.function == "GetTokenInformation"
            and step.info_class == 8
            and not step.sizing
        ):
            struct.pack_into("<i", call.frame_ref.storage, step.offset, 2)
        return result

    record = cpu_record(m, execute)
    sibling_sdk = TokenSdk(m)
    sibling = cpu_record(m, sibling_sdk.execute)
    function = m._cpu_observe_impl
    markers = {
        "before_close": "for handle in reversed",
        "after_close": "if not result.success:",
        "before_revoke": "if primary:",
        "at_revoke": 'record.state = "revoked"',
    }
    lines, start = inspect.getsourcelines(function)
    candidates = [start + i for i, line in enumerate(lines) if markers[stage] in line]
    target = candidates[-1] if stage == "before_revoke" else candidates[0]
    hit = []

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is function.__code__
            and frame.f_lineno == target
        ):
            owned = record.frame
            assert (
                owned.semantic_known
                and frame.f_locals["primary"] == "PRINCIPAL_UNACCREDITED"
            )
            error = (
                owned.semantic_rejection
                if kind == "same_semantic"
                else (ValueError if kind == "value" else KeyboardInterrupt)(
                    "private-cleanup-cut"
                )
            )
            if kind == "public":
                error = m.IdentityError(
                    m.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query")
                )
                owned.public_error = error
            hit.append(
                (
                    error,
                    bytes(owned.storage),
                    record.calls[-1].raw_result,
                    record.calls[-1].preimage,
                )
            )
            raise error
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(m.IdentityError) as raised:
            m._cpu_observe(record)
    finally:
        sys.settrace(previous)
    assert len(hit) == 1
    assert raised.value.diagnostic.code == "PRINCIPAL_UNACCREDITED"
    assert raised.value.cleanup.state == "unknown"
    assert raised.value.cleanup.diagnostics[0].code == "RESOURCE_UNKNOWN"
    assert record.state == "unknown" and m._io._KERNEL_POISONED
    assert (
        bytes(record.frame.storage) == hit[0][1] and len(record.frame.storage) == 131328
    )
    assert record.calls[-1].raw_result is hit[0][2]
    assert record.calls[-1].preimage == hit[0][3] and len(hit[0][3]) == 131328
    assert record.calls[-1].error is hit[0][0]
    assert not record.admissions and record.source == "cpu_double"
    assert sdk.calls.count("CloseHandle") == (0 if stage == "before_close" else 1)
    before = list(sdk.calls)
    with pytest.raises(ValueError, match="OWNER_RETIRE_REQUIRED"):
        m._cpu_observe(record)
    with pytest.raises(ValueError, match="OWNER_RETIRE_REQUIRED"):
        m._cpu_observe(sibling)
    assert sdk.calls == before and sibling_sdk.calls == []
    assert "private-cleanup-cut" not in repr(raised.value)


@pytest.mark.parametrize("kind", ["same_semantic", "value", "interrupt", "public"])
def test_fix2_actual_handler_ast_keeps_primary_without_grants(kind):
    """Ejecuta sólo el handler AST real con custodia CPU; no crea sesión nativa."""
    import ast
    import inspect

    m = load()
    record = cpu_record(m, TokenSdk(m).execute)
    frame = m._CpuFrame()
    frame.semantic_known = True
    frame.semantic_rejection = m._SemanticRejection("PRINCIPAL_UNACCREDITED")
    record.frame = frame
    if kind == "same_semantic":
        error = frame.semantic_rejection
    elif kind == "public":
        error = m.IdentityError(m.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query"))
        frame.public_error = error
    else:
        error = (ValueError if kind == "value" else KeyboardInterrupt)(
            "private-native-cleanup-cut"
        )
    tree = ast.parse(inspect.getsource(m._observe_current_effective_principal))
    outer = next(node for node in tree.body[0].body if isinstance(node, ast.Try))
    handler = outer.handlers[-1]
    # Sustituye exclusivamente el transporte de poison, no la política del handler.
    namespace = dict(m.__dict__)
    namespace.update(
        record=record, frame=frame, error=error, _native_poison=m._poison_cpu
    )
    wrapper = ast.Try(
        body=[ast.Raise(exc=ast.Name(id="error", ctx=ast.Load()), cause=None)],
        handlers=[
            ast.ExceptHandler(
                type=ast.Name(id="BaseException", ctx=ast.Load()),
                name="error",
                body=handler.body,
            )
        ],
        orelse=[],
        finalbody=[],
    )
    with pytest.raises(m.IdentityError) as raised:
        exec(  # noqa: S102 - AST del handler propio; sin entrada ni grants externos
            compile(
                ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[])),
                "<actual-native-handler-policy-no-grants>",
                "exec",
            ),
            namespace,
        )
    assert raised.value.diagnostic.code == "PRINCIPAL_UNACCREDITED"
    assert raised.value.cleanup.state == "unknown"
    assert raised.value.cleanup.diagnostics[0].code == "RESOURCE_UNKNOWN"
    assert record.state == "unknown" and m._io._KERNEL_POISONED
    assert len(frame.storage) == 131328 and not record.admissions


def test_fix2_known_rejection_marks_final_phase_after_actual_close_and_revoke():
    m = load()
    sdk = TokenSdk(m)
    sdk.fail = "GetTokenInformation"
    record = cpu_record(m, sdk.execute)
    with pytest.raises(m._SemanticRejection, match="PRINCIPAL_UNACCREDITED"):
        m._cpu_observe(record)
    assert sdk.calls.count("CloseHandle") == 1 and record.state == "revoked"
    assert not m._io._KERNEL_POISONED
    assert vars(record.frame).get("cleanup_complete") is True


@pytest.mark.parametrize("kind", ["same_semantic", "value", "interrupt", "public"])
def test_fix2_between_two_closes_stops_and_keeps_first_primary(kind):
    import inspect

    m = load()
    sdk = TokenSdk(m)

    def execute(call):
        result = sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            call.function == "GetTokenInformation"
            and step.info_class == 10
            and step.offset == 176
            and not step.sizing
        ):
            struct.pack_into("<I", call.frame_ref.storage, step.offset + 48, 9)
        return result

    record = cpu_record(m, execute)
    function = m._cpu_observe_impl
    lines, start = inspect.getsourcelines(function)
    target = start + next(
        i for i, line in enumerate(lines) if "result, _ = _cpu_call(" in line
    )
    hits = []

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is function.__code__
            and frame.f_lineno == target
            and sdk.calls.count("CloseHandle") == 1
        ):
            owned = record.frame
            error = (
                owned.semantic_rejection
                if kind == "same_semantic"
                else (ValueError if kind == "value" else KeyboardInterrupt)(
                    "private-between-closes"
                )
            )
            if kind == "public":
                error = m.IdentityError(
                    m.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query")
                )
                owned.public_error = error
            hits.append((error, bytes(owned.storage), record.calls[-1].preimage))
            raise error
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(m.IdentityError) as raised:
            m._cpu_observe(record)
    finally:
        sys.settrace(previous)
    assert len(hits) == 1 and sdk.calls.count("CloseHandle") == 1
    assert record.frame.handles == {101: False, 102: True}
    assert record.state == "unknown" and m._io._KERNEL_POISONED
    assert raised.value.diagnostic.code == "PRINCIPAL_UNACCREDITED"
    assert raised.value.cleanup.state == "unknown"
    assert raised.value.cleanup.diagnostics[0].code == "RESOURCE_UNKNOWN"
    assert (
        bytes(record.frame.storage) == hits[0][1]
        and len(record.frame.storage) == 131328
    )
    assert record.calls[-1].preimage == hits[0][2] and len(hits[0][2]) == 131328
    assert record.calls[-1].error is hits[0][0] and record.calls[-1].raw_result.success


def test_fix1_bootstrap_claim_to_entry_poison_is_typed():
    import ast
    import inspect

    m = load()
    tree = ast.parse(inspect.getsource(m._bootstrap_native))
    namespace = dict(m.__dict__)
    namespace["_require_canonical_identity_instance"] = lambda: None

    def claim_then_poison():
        m._io._kernel_identity_bootstrap_claim()
        m._io._KERNEL_POISONED = True

    # No native session is constructed: the actual domain rejects before its body.
    namespace["_io"] = types.SimpleNamespace(
        _kernel_identity_bootstrap_claim=claim_then_poison,
        _kernel_domain=m._io._kernel_domain,
        KernelMemoryError=m._io.KernelMemoryError,
    )
    exec(compile(tree, "<CPU-AST-bootstrap-entry-poison>", "exec"), namespace)  # noqa: S102 - AST CPU no coverage original
    with pytest.raises(m.IdentityError) as error:
        namespace["_bootstrap_native"]()
    assert error.value.diagnostic.code == "OWNER_RETIRE_REQUIRED"
    assert error.value.diagnostic.operation == "bootstrap"
    assert m._io._KERNEL_POISONED and m._io._IDENTITY_BOOTSTRAP_CONSUMED
    assert m._io._LIVE_IDENTITY_SESSIONS == {} and m._io._LIVE_MEMORY_CONTEXTS == {}
