"""Contrato causal CPU de adquisición; nunca ejecuta DLL o archivos nativos."""

import gc
import importlib
import pathlib
import struct
import sys
import types
import uuid

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
SID = bytes([1, 1, 0, 0, 0, 0, 0, 5]) + struct.pack("<I", 21)


@pytest.mark.parametrize("bound", [False, True])
@pytest.mark.parametrize("unchanged", [False, True])
def test_fix2_known_failure_traceback_releases_original_sdk_buffer(bound, unchanged):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    source = None
    if bound:
        _, authority, admission = cpu_identity_fixture(m)
        source = m._identity._CPU_AUTHORITIES[authority]
        with m._owner_pin_boundary(owner):
            m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    baseline = tuple(record.backings)
    # La observación conserva sólo identidad/tamaño del SDK buffer; nunca sus bytes.
    original_buffers = {}
    callbacks = []

    def missing(frame):
        sdk.calls.append("open")
        callbacks.append(frame)
        original_buffers[id(frame.arena_refs[-1].storage)] = len(
            frame.arena_refs[-1].storage
        )
        status = 0xC0000034
        base = record.control.aligned_offset
        struct.pack_into(
            "<I", record.control.storage, base + 6144 + frame.slot_index * 4, status
        )
        if not unchanged:
            struct.pack_into(
                "<QQ",
                record.control.storage,
                base + 2048 + frame.slot_index * 16,
                status,
                0,
            )
        return m._NativeCreateCompletion(
            status,
            0x7FFFFFFF if unchanged else status,
            2**64 - 1 if unchanged else 0,
            unchanged,
        )

    def retained_originals(value):
        # Devuelve escalares; los temporales de la inspección mueren al retornar.
        if type(value) is bytearray:
            return {id(value): len(value)} if id(value) in original_buffers else {}
        found = {}
        if type(value) in {tuple, list, dict}:
            for item in value.values() if type(value) is dict else value:
                found.update(retained_originals(item))
        return found

    record.ops = m._AcquisitionOps(missing, sdk.close, sdk.locate, sdk.descriptor)
    for _ in range(7):
        with pytest.raises(m.AcquisitionError, match="NOT_FOUND/open_anchor"):
            m._open_owned_anchor(owner, locator)
    gc.collect()
    retained = {}
    frames = (
        [
            pin.target_frame_ref
            for pin in source.pins.values()
            if pin.target_frame_ref.operation == "open_anchor"
        ]
        if bound
        else callbacks
    )
    assert len(frames) == 7
    for frame in frames:
        call = frame.call_record_ref
        assert frame.phase is m._CallPhase.ACKNOWLEDGED
        assert call.recognized_error.diagnostic.code == "NOT_FOUND"
        traceback = call.recognized_error.__traceback__
        while traceback is not None:
            if traceback.tb_frame.f_code.co_name == "_create_completion":
                retained.update(retained_originals(traceback.tb_frame.f_locals))
            traceback = traceback.tb_next
    assert retained == {}, (
        f"unaccounted_original_buffers={len(retained)}, "
        f"unaccounted_bytes={sum(retained.values())}, charged={len(record.backings)}"
    )
    assert tuple(record.backings) == baseline and record.handles == 0
    assert record.inflight == [] and record.next_slot == 7
    assert all(
        row.state is m._AcquisitionState.FAILED for row in record.acquisitions.values()
    )
    assert not m._io._KERNEL_POISONED
    if bound:
        assert len(source.pins) == 8 and all(
            pin.state == "completed" for pin in source.pins.values()
        )


@pytest.mark.parametrize("bound", [False, True])
@pytest.mark.parametrize("unchanged", [False, True])
def test_fix1_known_failure_returns_name_backing_after_full_recognition(
    bound, unchanged
):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    source = None
    if bound:
        _, authority, admission = cpu_identity_fixture(m)
        source = m._identity._CPU_AUTHORITIES[authority]
        with m._owner_pin_boundary(owner):
            m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    baseline = tuple(record.backings)
    captured = []

    def missing(frame):
        sdk.calls.append("open")
        captured.append((frame, frame.arena_refs[-1]))
        assert frame.phase is m._CallPhase.ENTERED
        assert frame.arena_refs[-1] in record.backings
        if bound:
            assert source.pins[frame.admission_pin].state == "active"
        status = 0xC0000034
        base = record.control.aligned_offset
        struct.pack_into(
            "<I", record.control.storage, base + 6144 + frame.slot_index * 4, status
        )
        if not unchanged:
            struct.pack_into(
                "<QQ",
                record.control.storage,
                base + 2048 + frame.slot_index * 16,
                status,
                0,
            )
        return m._NativeCreateCompletion(
            status,
            0x7FFFFFFF if unchanged else status,
            2**64 - 1 if unchanged else 0,
            unchanged,
        )

    record.ops = m._AcquisitionOps(missing, sdk.close, sdk.locate, sdk.descriptor)
    for index in range(7):
        with pytest.raises(m.AcquisitionError, match="NOT_FOUND/open_anchor"):
            m._open_owned_anchor(owner, locator)
        assert tuple(record.backings) == baseline
        frame, released = captured[-1]
        assert frame.phase is m._CallPhase.ACKNOWLEDGED
        assert released.state is m._AuxiliaryState.CLOSED
        assert released.storage == bytearray() and released.overlay is None
        assert released.native_base == 0
        assert frame.arena_refs == (record.control,)
        assert frame.call_record_ref.preimage == b""
        assert frame.call_record_ref.return_value is None
        assert record.next_slot == index + 1 and len(record.acquisitions) == index + 1
        assert record.handles == 0 and record.inflight == []
        assert all(
            row.state is m._AcquisitionState.FAILED
            for row in record.acquisitions.values()
        )
        assert not m._io._KERNEL_POISONED
    assert sdk.calls == ["locate"] + ["open"] * 7
    if bound:
        assert len(source.pins) == 8 and all(
            pin.state == "completed" for pin in source.pins.values()
        )


@pytest.mark.parametrize("bound", [False, True])
def test_fix1_pinned_ancestor_close_revokes_descendant_future_authority(bound):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    if bound:
        _, _authority, admission = cpu_identity_fixture(m)
        with m._owner_pin_boundary(owner):
            m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    anchor = m._open_owned_anchor(owner, locator)
    directory = m._open_owned_component(
        owner,
        anchor,
        "dir",
        m._AcquireProfile.PARENT_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    leaf = m._open_owned_component(
        owner,
        directory,
        "file",
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    with pytest.raises(m.AcquisitionError, match="CAPABILITY_IN_USE/close"):
        m._close_acquisition(owner, anchor)
    before = tuple(sdk.calls), tuple(record.backings), record.handles, record.next_slot
    with pytest.raises(m.AcquisitionError, match="CAPABILITY_REVOKED/open_component"):
        m._open_owned_component(
            owner,
            directory,
            "another",
            m._AcquireProfile.READ_EXISTING,
            m._Disposition.OPEN_EXISTING,
        )
    assert (
        tuple(sdk.calls),
        tuple(record.backings),
        record.handles,
        record.next_slot,
    ) == before
    assert all(
        record.acquisitions[item].state is m._AcquisitionState.REVOKED
        for item in (anchor, directory, leaf)
    )
    for item in (leaf, directory, anchor):
        assert m._close_acquisition(owner, item).state == "closed"
    assert record.handles == 0 and not m._io._KERNEL_POISONED


@pytest.mark.parametrize("cut", ["remove_backing", "empty_storage"])
def test_fix1_known_failure_cleanup_cut_retains_exact_custody(monkeypatch, cut):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    captured = []
    cause = KeyboardInterrupt("private-known-failure-cleanup-cut")

    class CutList(list):
        def remove(self, item):
            super().remove(item)
            raise cause

    def missing(frame):
        captured.append(
            (frame, frame.arena_refs[-1], bytes(frame.arena_refs[-1].storage))
        )
        if cut == "remove_backing":
            record.backings = CutList(record.backings)
        else:
            original = bytearray

            def empty_cut(*args, **kwargs):
                if not args:
                    raise cause
                return original(*args, **kwargs)

            monkeypatch.setattr(m, "bytearray", empty_cut, raising=False)
        struct.pack_into(
            "<I", record.control.storage, 6144 + frame.slot_index * 4, 0xC0000034
        )
        return m._NativeCreateCompletion(0xC0000034, 0x7FFFFFFF, 2**64 - 1, True)

    record.ops = m._AcquisitionOps(missing, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(m.AcquisitionError, match="RESOURCE_UNKNOWN/open_anchor"):
        m._open_owned_anchor(owner, locator)
    frame, arena, before = captured[0]
    assert m._io._KERNEL_POISONED and record.handles == 1
    assert (
        frame.phase is m._CallPhase.UNKNOWN
        and frame.record_ref.state is m._AcquisitionState.UNKNOWN
    )
    assert any(backing is arena for backing in record.backings)
    assert arena.state is m._AuxiliaryState.LIVE and bytes(arena.storage) == before
    assert frame.arena_refs[-1] is arena and frame.call_record_ref in record.inflight
    assert frame.call_record_ref.error is cause and frame.call_record_ref.preimage


@pytest.mark.parametrize("name", ["a" * 255, "\U0001f600" * 127 + "a"])
def test_fix1_component_utf16_510_accepts_512_rejects_before_entry(name):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    item = m._open_owned_component(
        owner,
        parent,
        name,
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    assert len(name.encode("utf-16-le")) == 510
    assert m._acquisition_info(owner, item).state == "candidate"
    before = tuple(sdk.calls)
    with pytest.raises(m.AcquisitionError, match="COMPONENT_INVALID"):
        m._open_owned_component(
            owner,
            parent,
            name + "a",
            m._AcquireProfile.READ_EXISTING,
            m._Disposition.OPEN_EXISTING,
        )
    assert sdk.calls == list(before)


def test_fix1_locator_total_utf16_limit_uses_valid_components():
    m, sdk, owner = assembly()
    prefix = "C:\\" + ("a" * 255 + "\\") * 63
    path = prefix + "b" * (16383 - len(prefix))
    assert len(path.encode("utf-16-le")) == 32766
    assert all(
        0 < len(part.encode("utf-16-le")) <= 510 for part in path[3:].split("\\")
    )
    m._locate_anchor(owner, project_location=path)
    before = tuple(sdk.calls)
    with pytest.raises(m.AcquisitionError, match="COMPONENT_INVALID/locate"):
        m._locate_anchor(owner, project_location=path + "b")
    assert tuple(sdk.calls) == before


def test_fix1_requested_backing_boundary_accounts_padding_before_reservation():
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    plans = (((m._SegmentName.UNICODE_NAME, 131064, 8),),)
    (arena,) = m._reserve_layouts(record, "locate", plans)
    assert arena.logical_length == 131064 and arena.requested_bytes == 131071
    assert len(arena.storage) == 131071
    before = (
        tuple(record.backings),
        record.handles,
        record.next_slot,
        tuple(record.inflight),
    )
    with pytest.raises(m.AcquisitionError, match="ACQUISITION_LIMIT/locate"):
        m._reserve_layouts(
            record, "locate", (((m._SegmentName.UNICODE_NAME, 131072, 8),),)
        )
    assert (
        tuple(record.backings),
        record.handles,
        record.next_slot,
        tuple(record.inflight),
    ) == before
    assert sdk.calls == []


def load():
    key = "k2_" + uuid.uuid4().hex
    package = types.ModuleType(key)
    package.__path__ = [str(SCRIPTS)]
    sys.modules[key] = package
    return importlib.import_module(key + ".storage_journal_windows_acquisition")


def test_bound_cpu_complete_rejects_callback_reentry_before_return_without_queries():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    reached = []

    def entered(frame):
        returned = sdk.locate(frame)
        reached.append(frame)
        print(
            "Actual CPU locator callback reached; facade frame ENTRY before callback return"
        )
        assert frame.phase is m._CallPhase.ENTERED and record.admission_ref is admission
        before = tuple(token_sdk.calls)
        with pytest.raises(identity.IdentityError, match="CAPABILITY_INVALID"):
            identity._complete_cpu_acquisition_admission_pin(
                frame.admission_pin, owner=owner
            )
        assert (
            tuple(token_sdk.calls) == before
            and source.pins[frame.admission_pin].state == "active"
        )
        return returned

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    assert sdk.calls == ["locate"] and len(reached) == 1
    assert record.locators[locator].state is m._AuxiliaryState.LIVE
    assert all(pin.state == "completed" for pin in source.pins.values())


def test_bound_cpu_complete_rejects_reserved_frame_without_post_queries():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    with m._owner_pin_boundary(owner) as frame:
        pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        assert frame.phase is m._CallPhase.RESERVED
        before = tuple(token_sdk.calls)
        with pytest.raises(identity.IdentityError, match="CAPABILITY_INVALID"):
            identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
        assert tuple(token_sdk.calls) == before and source.pins[pin].state == "active"
        identity._abort_cpu_acquisition_admission_pin(pin, owner=owner)
    assert source.pins[pin].state == "aborted" and sdk.calls == []


def test_bound_cpu_complete_observes_returned_after_actual_callback():
    m, sdk, owner = assembly()
    _token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    witnessed = []
    previous = sys.getprofile()

    def observe(python_frame, event, arg):
        if (
            event == "call"
            and python_frame.f_code
            is identity._complete_cpu_acquisition_admission_pin.__code__
        ):
            pin = source.pins[python_frame.f_locals["pin"]]
            witnessed.append((pin.target_frame_ref.phase, tuple(sdk.calls), pin.state))

    try:
        sys.setprofile(observe)
        m._locate_anchor(owner, project_location="C:\\studio")
    finally:
        sys.setprofile(previous)
    assert witnessed == [(m._CallPhase.RETURNED, ("locate",), "active")]
    assert all(pin.state == "completed" for pin in source.pins.values())


def test_bound_cpu_reserved_probe_scope_cannot_expand_current_readonly_pin():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    reached = []

    def entered(frame):
        completion = sdk.locate(frame)
        reached.append(frame)
        before = (tuple(token_sdk.calls), tuple(source.pins), source.pin_slots_reserved)
        pin = source.pins[frame.admission_pin]
        assert pin.state == "active" and record.admission_ref is admission
        with pytest.raises(identity.IdentityError, match="ADMISSION_REQUIRED"):
            identity._pin_scope(
                identity._AdmissionScope.OWNED_PROBE_CANDIDATE, frame, m, "pin"
            )
        assert (
            tuple(token_sdk.calls),
            tuple(source.pins),
            source.pin_slots_reserved,
        ) == before
        assert (
            source.admissions[admission].scope
            is identity._AdmissionScope.CANDIDATE_READ_ONLY
        )
        assert pin.state == "active" and record.source == "cpu_double"
        return completion

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    assert len(reached) == 1 and sdk.calls == ["locate"]
    assert record.locators[locator].state is m._AuxiliaryState.LIVE
    assert len(source.pins) == 1 and all(
        pin.state == "completed" for pin in source.pins.values()
    )
    assert not m._io._KERNEL_POISONED


@pytest.mark.parametrize(
    "fault",
    [
        "arity",
        "wrong_function",
        "range_shape",
        "foreign_buffer",
        "range_bool",
        "range_tail",
        "range_overlap",
        "extra_ordinal",
        "result_bool",
        "result_high",
        "last_error_bool",
        "last_error_overflow",
    ],
)
def test_cpu_original_sdk_transport_rejects_invalid_entry_and_retains_outputs(fault):
    """Original ABI helper + nominal CPU owner; no factory/issuer/DLL nativo."""
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    entered_frames = []
    callbacks = []

    def entered(frame):
        sdk.open(frame)
        entered_frames.append(frame)
        assert record.source == "cpu_double" and frame.owner_ref is owner
        assert frame.phase is m._CallPhase.ENTERED
        args = tuple(range(11))
        ranges = ((record.control, 0, 8),)
        name = m._SdkFunction.NT_CREATE_FILE
        scalar = (
            True if fault == "result_bool" else 2**31 if fault == "result_high" else 0
        )
        capture_error = fault.startswith("last_error")
        last_error = True if fault == "last_error_bool" else 2**32

        def closed_cpu_callback(*values):
            callbacks.append(values)
            return scalar

        if fault == "arity":
            args = args[:-1]
        elif fault == "wrong_function":
            name = m._SdkFunction.CLOSE_HANDLE
            args = (1,)
        elif fault == "range_shape":
            ranges = ((record.control, 0),)
        elif fault == "foreign_buffer":
            ranges = ((object(), 0, 8),)
        elif fault == "range_bool":
            ranges = ((record.control, True, 8),)
        elif fault == "range_tail":
            ranges = ((record.control, record.control.logical_length, 1),)
        elif fault == "range_overlap":
            ranges = ((record.control, 0, 8), (record.control, 4, 8))
        elif fault == "extra_ordinal":
            abi._sdk_call(
                None,
                closed_cpu_callback,
                frame,
                name,
                args,
                ranges,
                capture_error=False,
            )
            callbacks.clear()
        return abi._sdk_call(
            types.SimpleNamespace(get_last_error=lambda: last_error),
            closed_cpu_callback,
            frame,
            name,
            args,
            ranges,
            capture_error=capture_error,
        )

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(m.AcquisitionError, match="RESOURCE_UNKNOWN"):
        m._open_owned_anchor(owner, locator)
    assert len(entered_frames) == 1 and len(record.inflight) == 1
    call = record.inflight[0]
    assert call.frame is entered_frames[0] and call.frame.phase is m._CallPhase.UNKNOWN
    assert record.handles == 1 and record.next_slot == 1
    assert struct.unpack_from("<Q", record.control.storage, 0)[0] == 101
    assert record.state is m._OwnerState.UNKNOWN and m._io._KERNEL_POISONED
    if fault.startswith(("result", "last_error")):
        assert len(callbacks) == 1 and len(call.subcalls) == 1
        step = call.subcalls[0]
        assert step.phase is m._CallPhase.UNKNOWN and type(step.error) is RuntimeError
        expected_scalar = (
            True if fault == "result_bool" else 2**31 if fault == "result_high" else 0
        )
        assert step.return_scalar == expected_scalar and type(
            step.return_scalar
        ) is type(expected_scalar)
        if fault.startswith("last_error"):
            assert step.win32_error == (True if fault == "last_error_bool" else 2**32)
    else:
        assert callbacks == []
        assert len(call.subcalls) == (1 if fault == "extra_ordinal" else 0)


def test_cpu_owner_owns_control_backing_without_sdk_entry():
    m = load()
    calls = []
    owner = m._assemble_cpu_acquisition_owner(
        m._AcquisitionOps(*((lambda frame: calls.append(frame),) * 4)),
        principal_sid=SID,
        primary_group_sid=SID,
    )
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    assert record.source == "cpu_double"
    assert record.pid > 0 and record.state.value == "live"
    assert record.control.logical_length == 10240
    assert record.control.requested_bytes == 10247
    assert record.backings == [record.control]
    assert record.handles == 0 and record.next_slot == 0 and record.inflight == []
    assert len(record.control.storage) == 10247 and calls == []


class AcquisitionSdk:
    def __init__(self, module):
        self.m = module
        self.calls = []
        self.frames = []
        self.next_handle = 101

    def locate(self, frame):
        self.calls.append("locate")
        self.frames.append(frame)
        frame.locator_record.root_dos = "C:\\"
        frame.locator_record.guid = "Volume{01234567-89ab-cdef-0123-456789abcdef}"
        frame.locator_record.target = "\\Device\\HarddiskVolume3"
        frame.locator_record.nt_name = "\\??\\" + frame.locator_record.guid + "\\"
        return self.m._LocatorCompletion(True)

    def open(self, frame):
        self.calls.append("open")
        self.frames.append(frame)
        record = self.m._LIVE_ACQUISITION_OWNERS[frame.owner_ref]
        assert frame in [call.frame for call in record.inflight]
        assert record.handles > 0
        assert frame.phase.value == "entered"
        assert (
            struct.unpack_from("<Q", record.control.storage, frame.slot_index * 8)[0]
            == 0
        )
        assert struct.unpack_from(
            "<QQ", record.control.storage, 2048 + frame.slot_index * 16
        ) == (0x7FFFFFFF, 2**64 - 1)
        struct.pack_into(
            "<Q", record.control.storage, frame.slot_index * 8, self.next_handle
        )
        self.next_handle += 1
        information = 2 if frame.nt_disposition == 2 else 1
        struct.pack_into(
            "<QQ", record.control.storage, 2048 + frame.slot_index * 16, 0, information
        )
        struct.pack_into("<I", record.control.storage, 6144 + frame.slot_index * 4, 0)
        return self.m._NativeCreateCompletion(0, 0, information, False)

    def close(self, frame):
        self.calls.append("close")
        self.frames.append(frame)
        record = self.m._LIVE_ACQUISITION_OWNERS[frame.owner_ref]
        struct.pack_into("<i", record.control.storage, 7168 + frame.slot_index * 4, 1)
        return self.m._NativeCloseCompletion(True)

    def descriptor(self, frame):
        self.calls.append("descriptor")
        self.frames.append(frame)
        row = frame.descriptor_record
        storage = row.arena.storage
        # CPU pointer values are offsets only; no address is dereferenced.
        struct.pack_into("<BBH4xQQQQ", storage, 0, 1, 0, 0x1004, 9216, 9284, 0, 40)
        struct.pack_into(
            "<BBHHH", storage, 40, 2, 0, row.acl_length, len(row.trustees), 0
        )
        offset = 48
        for sid in row.trustees:
            struct.pack_into("<BBHI", storage, offset, 0, 0, 8 + len(sid), row.mask)
            storage[offset + 8 : offset + 8 + len(sid)] = sid
            offset += 8 + len(sid)
        row.getter_outputs = (0x1004, 1, 9216, False, 9284, False, True, 40, False)
        return self.m._DescriptorCompletion(True)


def assembly():
    m = load()
    sdk = AcquisitionSdk(m)
    owner = m._assemble_cpu_acquisition_owner(
        m._AcquisitionOps(sdk.open, sdk.close, sdk.locate, sdk.descriptor),
        principal_sid=SID,
        primary_group_sid=SID,
    )
    return m, sdk, owner


def test_locator_registered_navigation_from_own_callback():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    row = record.locators[locator]
    assert row.capability is locator and row.owner_ref is owner
    assert row.root_dos == "C:\\" and row.nt_name.startswith("\\??\\Volume{")
    assert row.source == "cpu_double" and row.state.value == "live"
    assert sdk.calls == ["locate"] and record.inflight == []


def test_anchor_reserves_slot_outputs_frame_and_charge_before_dispatch():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    acquisition = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    row = record.acquisitions[acquisition]
    assert row.capability is acquisition and row.parent_ref is None
    assert row.profile is m._AcquireProfile.ANCHOR_CANDIDATE
    assert row.disposition is m._Disposition.OPEN_EXISTING
    assert row.state.value == "candidate" and row.slot_index == 0
    assert row.completion == m._NativeCreateCompletion(0, 0, 1, False)
    assert record.handles == 1 and record.next_slot == 1 and record.inflight == []
    frame = sdk.frames[-1]
    assert frame.access == 0x001200A0 and frame.share == 3
    assert frame.options == 0x00200021 and frame.nt_disposition == 1
    assert frame.file_attributes == 0 and frame.descriptor_ref is None
    assert frame.parent_ref is None and frame.object_attributes == 0x40
    assert sdk.calls == ["locate", "open"]


@pytest.mark.parametrize(
    "fault",
    [
        "pending",
        "informational",
        "warning",
        "missing",
        "invalid",
        "pseudo",
        "iosb_sentinel",
        "iosb_status",
        "information",
        "wrapper",
        "bool_status",
        "mismatch",
        "error_output",
        "error_partial",
        "exception",
        "interrupt",
    ],
)
def test_uncertain_open_retains_outputs_and_poison_without_close(fault):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.open(frame)
        storage = record.control.storage
        slot = frame.slot_index
        handle, status, info = 101, 0, 1
        returned = 0
        if fault == "pending":
            returned = status = 0x103
        elif fault == "informational":
            returned = status = 1
        elif fault == "warning":
            returned = status = 0x80000005
        elif fault == "missing":
            handle = 0
        elif fault == "invalid":
            handle = 2**64 - 1
        elif fault == "pseudo":
            handle = 2**64 - 6
        elif fault == "iosb_sentinel":
            status, info = 0x7FFFFFFF, 2**64 - 1
        elif fault == "iosb_status":
            status = 0xC0000022
        elif fault == "information":
            info = 2
        elif fault == "mismatch":
            info = 7
        elif fault.startswith("error"):
            returned = status = 0xC0000022
            info = 0
            if fault == "error_partial":
                handle, status = 0, 0
        struct.pack_into("<Q", storage, slot * 8, handle)
        struct.pack_into("<QQ", storage, 2048 + slot * 16, status, info)
        struct.pack_into("<I", storage, 6144 + slot * 4, returned)
        if fault == "exception":
            raise RuntimeError("private-error-sentinel")
        if fault == "interrupt":
            raise KeyboardInterrupt("private-interrupt-sentinel")
        if fault == "wrapper":
            return None
        if fault == "bool_status":
            return m._NativeCreateCompletion(False, 0, 1, False)
        if fault == "mismatch":
            return result
        return m._NativeCreateCompletion(returned, status, info, False)

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(Exception, match="RESOURCE_UNKNOWN") as error:
        m._open_owned_anchor(owner, locator)
    assert sdk.calls == ["locate", "open"]
    assert m._io._KERNEL_POISONED is True
    assert record.state.value == "unknown" and record.handles == 1
    assert len(record.inflight) == 1 and len(record.control.storage) == 10247
    call = record.inflight[0]
    assert call.frame.phase.value == "unknown" and len(call.preimage) == 10247
    assert "private-" not in str(error.value)


@pytest.mark.parametrize(
    "status,expected",
    [
        (0xC0000034, "NOT_FOUND"),
        (0xC000003A, "NOT_FOUND"),
        (0xC0000043, "SHARING_CONFLICT"),
        (0xC0000022, "ACCESS_DENIED"),
        (0xC0000001, "OPEN_FAILED"),
    ],
)
@pytest.mark.parametrize("unchanged", [True, False])
def test_known_error_preserves_tombstone_and_returns_handle_charge(
    status, expected, unchanged
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.calls.append("open")
        assert frame.phase.value == "entered" and record.handles == 1
        slot = frame.slot_index
        struct.pack_into("<I", record.control.storage, 6144 + slot * 4, status)
        if not unchanged:
            struct.pack_into("<QQ", record.control.storage, 2048 + slot * 16, status, 0)
        return m._NativeCreateCompletion(
            status,
            0x7FFFFFFF if unchanged else status,
            2**64 - 1 if unchanged else 0,
            unchanged,
        )

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(Exception, match=expected):
        m._open_owned_anchor(owner, locator)
    assert sdk.calls == ["locate", "open"] and record.handles == 0
    assert record.next_slot == 1 and len(record.acquisitions) == 1
    assert next(iter(record.acquisitions.values())).state.value == "failed"
    assert record.inflight == [] and m._io._KERNEL_POISONED is False


@pytest.mark.parametrize(
    "profile,access,share,options",
    [
        ("PARENT_EXISTING", 0x001200A0, 3, 0x00200021),
        ("PARENT_CREATE_FILE", 0x001200A2, 3, 0x00200021),
        ("PARENT_CREATE_DOMAIN", 0x001200A6, 3, 0x00200021),
        ("READ_EXISTING", 0x00120081, 1, 0x00200068),
        ("WRITER_EXISTING", 0x00120083, 0, 0x0020006A),
    ],
)
def test_relative_component_exact_recipe_and_parent_pin(
    profile, access, share, options
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    acquisition = m._open_owned_component(
        owner,
        parent,
        "journal",
        m._AcquireProfile[profile],
        m._Disposition.OPEN_EXISTING,
        None,
    )
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    row = record.acquisitions[acquisition]
    assert row.parent_ref is parent and row.slot_index == 1
    assert record.acquisitions[parent].child_pins == 1
    frame = sdk.frames[-1]
    assert (frame.access, frame.share, frame.options) == (access, share, options)
    assert frame.name_bytes == "journal".encode("utf-16-le")
    assert frame.parent_ref is parent and frame.nt_disposition == 1
    assert frame.file_attributes == 0 and frame.descriptor_ref is None
    assert row.state.value == "candidate" and record.handles == 2


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "a/b",
        "a\\b",
        "a:b",
        "a*b",
        "a?b",
        'a"b',
        "a<b",
        "a>b",
        "a|b",
        "a\0b",
        "a\x1fb",
        "a.",
        "a ",
        "CON.txt",
        "prn",
        "AUX",
        "NUL",
        "CONIN$",
        "CONOUT$",
        "COM1",
        "LPT9",
        "COM¹",
        "LPT².txt",
        "COM³",
        "a" * 256,
        "\ud800",
        7,
        True,
    ],
)
def test_component_rejection_preentry_after_positive_dispatch(name):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    m._open_owned_component(
        owner,
        parent,
        "ok",
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    calls = tuple(sdk.calls)
    row = m._LIVE_ACQUISITION_OWNERS[owner]
    previous = (row.next_slot, row.handles, row.acquisitions[parent].child_pins)
    with pytest.raises(Exception, match="COMPONENT_INVALID"):
        m._open_owned_component(
            owner,
            parent,
            name,
            m._AcquireProfile.READ_EXISTING,
            m._Disposition.OPEN_EXISTING,
        )
    assert tuple(sdk.calls) == calls
    assert (row.next_slot, row.handles, row.acquisitions[parent].child_pins) == previous


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("owner_forged", "CAPABILITY_INVALID"),
        ("owner_subclass", "CAPABILITY_INVALID"),
        ("owner_pid", "CAPABILITY_INVALID"),
        ("parent_forged", "CAPABILITY_INVALID"),
        ("parent_cross", "OWNER_MISMATCH"),
        ("parent_file", "CAPABILITY_INVALID"),
        ("locator_forged", "CAPABILITY_INVALID"),
        ("profile", "PROFILE_INVALID"),
        ("anchor_profile", "PROFILE_INVALID"),
        ("disposition", "DISPOSITION_INVALID"),
        ("descriptor", "DESCRIPTOR_INVALID"),
        ("handles", "ACQUISITION_LIMIT"),
        ("slots", "ACQUISITION_LIMIT"),
        ("poison", "OWNER_RETIRE_REQUIRED"),
    ],
)
def test_nominal_owner_parent_profile_quota_guards(mutation, code):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    profile, disposition, descriptor = (
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
        None,
    )
    if mutation == "parent_cross":
        other = m._assemble_cpu_acquisition_owner(
            record.ops, principal_sid=SID, primary_group_sid=SID
        )
        other_locator = m._locate_anchor(other, project_location="C:\\studio")
        parent = m._open_owned_anchor(other, other_locator)
    elif mutation == "parent_file":
        parent = m._open_owned_component(owner, parent, "file", profile, disposition)
    elif mutation == "owner_forged":
        owner = object.__new__(m._AcquisitionOwner)
    elif mutation == "owner_subclass":

        class Subclass(m._AcquisitionOwner):
            pass

        owner = object.__new__(Subclass)
    elif mutation == "owner_pid":
        record.pid += 1
    elif mutation == "parent_forged":
        parent = object.__new__(m._OwnedAcquisition)
    elif mutation == "locator_forged":
        locator = object.__new__(m._AnchorLocator)
    elif mutation == "profile":
        profile = "READ_EXISTING"
    elif mutation == "anchor_profile":
        profile = m._AcquireProfile.ANCHOR_CANDIDATE
    elif mutation == "disposition":
        disposition = "OPEN_EXISTING"
    elif mutation == "descriptor":
        descriptor = object()
    elif mutation == "handles":
        record.handles = 64
    elif mutation == "slots":
        record.next_slot = 256
    elif mutation == "poison":
        m._io._KERNEL_POISONED = True
    calls = tuple(sdk.calls)
    with pytest.raises(Exception, match=code):
        if mutation == "locator_forged":
            m._open_owned_anchor(owner, locator)
        else:
            m._open_owned_component(
                owner, parent, "journal", profile, disposition, descriptor
            )
    assert tuple(sdk.calls) == calls


@pytest.mark.parametrize(
    "path",
    [
        "studio",
        "C:",
        "\\\\server\\share",
        "\\??\\C:\\studio",
        "\\\\?\\C:\\studio",
        "C:/studio",
        "C:\\..\\studio",
        "C:\\a.\\b",
        "C:\\CON\\b",
        "C:\\a\0b",
        "C:\\" + "a" * 16381,
        7,
    ],
)
def test_locator_input_guards_after_positive_sdk(path):
    m, sdk, owner = assembly()
    m._locate_anchor(owner, project_location="C:\\studio")
    with pytest.raises(Exception, match="COMPONENT_INVALID"):
        m._locate_anchor(owner, project_location=path)
    assert sdk.calls == ["locate"]


def test_explicit_close_once_releases_child_charge_and_parent_pin():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    child = m._open_owned_component(
        owner,
        parent,
        "file",
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    outcome = m._close_acquisition(owner, child)
    assert outcome.state == "closed" and outcome.causes == ()
    assert m._close_acquisition(owner, child) is outcome
    assert sdk.calls == ["locate", "open", "open", "close"]
    assert record.handles == 1 and record.acquisitions[parent].child_pins == 0
    assert record.acquisitions[child].state.value == "closed"
    assert record.acquisitions[child].native_close_attempted is True
    assert record.inflight == [] and record.next_slot == 2


@pytest.mark.parametrize(
    "fault",
    [
        "false",
        "pending",
        "invalid",
        "bool",
        "missing_error",
        "mismatch",
        "exception",
        "interrupt",
    ],
)
def test_close_unknown_retains_charge_and_never_retries(fault):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    acquisition = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.close(frame)
        if fault == "exception":
            raise RuntimeError("private-close-cut")
        if fault == "interrupt":
            raise KeyboardInterrupt("private-close-cut")
        if fault == "invalid":
            return None
        if fault == "bool":
            return m._NativeCloseCompletion(1, None)
        if fault in {"false", "pending", "missing_error"}:
            error = {"false": 5, "pending": 997, "missing_error": None}[fault]
            struct.pack_into(
                "<i", record.control.storage, 7168 + frame.slot_index * 4, 0
            )
            struct.pack_into(
                "<I", record.control.storage, 8192 + frame.slot_index * 4, error or 0
            )
            return m._NativeCloseCompletion(False, error)
        return m._NativeCloseCompletion(True, 5)

    record.ops = m._AcquisitionOps(sdk.open, entered, sdk.locate, sdk.descriptor)
    outcome = m._close_acquisition(owner, acquisition)
    assert outcome.state == "unknown" and record.handles == 1
    assert m._close_acquisition(owner, acquisition) is outcome
    assert sdk.calls.count("close") == 1 and m._io._KERNEL_POISONED is True
    assert record.state.value == "unknown" and len(record.inflight) == 1


@pytest.mark.parametrize(
    "target_text",
    [
        "frame.phase = _CallPhase.COMPLETED",
        'outcome = AcquisitionCloseOutcome("closed")',
        "record.handles -= 1",
        "record.inflight.remove(call)",
        "frame.phase = _CallPhase.ACKNOWLEDGED",
        "row.state = _AcquisitionState.CLOSED",
        "row.outcome = outcome",
    ],
)
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_close_true_cut_before_full_recognition_unknown(target_text, error_type):
    import inspect

    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    acquisition = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    lines, start = inspect.getsourcelines(m._close_registered_acquisition)
    target = start + next(i for i, text in enumerate(lines) if target_text in text)
    cut_error = error_type("private-recognition-cut")

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is m._close_registered_acquisition.__code__
            and frame.f_lineno == target
        ):
            assert sdk.calls.count("close") == 1
            raise cut_error
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        outcome = m._close_acquisition(owner, acquisition)
    finally:
        sys.settrace(previous)
    assert outcome.state == "unknown" and record.handles == 1
    assert m._close_acquisition(owner, acquisition) is outcome
    assert sdk.calls.count("close") == 1 and len(record.inflight) == 1
    assert record.inflight[0].error is cut_error
    assert struct.unpack_from("<i", record.control.storage, 7168)[0] == 1


def test_pinned_parent_close_rejects_preentry_then_children_close():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    child = m._open_owned_component(
        owner,
        parent,
        "file",
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    with pytest.raises(Exception, match="CAPABILITY_IN_USE"):
        m._close_acquisition(owner, parent)
    assert sdk.calls.count("close") == 0
    with pytest.raises(Exception, match="CAPABILITY_REVOKED"):
        m._open_owned_component(
            owner,
            parent,
            "new",
            m._AcquireProfile.READ_EXISTING,
            m._Disposition.OPEN_EXISTING,
        )
    assert m._close_acquisition(owner, child).state == "closed"
    assert m._close_acquisition(owner, parent).state == "closed"


def test_owner_close_postorder_and_all_backings_terminal():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    child = m._open_owned_component(
        owner,
        parent,
        "file",
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    outcome = m._close_acquisition_owner(owner)
    assert outcome.state == "closed" and m._close_acquisition_owner(owner) is outcome
    assert [
        frame.record_ref.capability
        for frame in sdk.frames
        if frame.operation == "close"
    ] == [child, parent]
    record = m._CLOSED_ACQUISITION_OWNERS[owner]
    assert record.handles == 0 and record.backings == []
    assert record.control is None and record.ops is None
    assert record.locators[locator].state.value == "closed"


def test_owner_close_stops_first_unknown_and_keeps_closed_prior():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    child = m._open_owned_component(
        owner,
        parent,
        "file",
        m._AcquireProfile.READ_EXISTING,
        m._Disposition.OPEN_EXISTING,
    )
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.close(frame)
        return m._NativeCloseCompletion(False, 5)

    record.ops = m._AcquisitionOps(sdk.open, entered, sdk.locate, sdk.descriptor)
    outcome = m._close_acquisition_owner(owner)
    assert outcome.state == "unknown" and sdk.calls.count("close") == 1
    assert m._close_acquisition_owner(owner) is outcome
    assert record.acquisitions[child].state.value == "unknown"
    assert record.acquisitions[parent].state.value == "revoked"
    assert record.handles == 2 and record.control is not None


@pytest.mark.parametrize("fault", ["fifth", "ops", "sid", "group", "poison"])
def test_owner_factory_exact_quota_sid_and_domain_precheck(fault):
    m, sdk, owner = assembly()
    m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    ops, sid, group = record.ops, SID, SID
    if fault == "fifth":
        for _ in range(3):
            m._assemble_cpu_acquisition_owner(
                ops, principal_sid=SID, primary_group_sid=SID
            )
    elif fault == "ops":
        ops = (sdk.open, sdk.close, sdk.locate, sdk.descriptor)
    elif fault == "sid":
        sid = b"invalid-private-sid"
    elif fault == "group":
        group = b"invalid-private-group"
    else:
        m._io._KERNEL_POISONED = True
    code = {
        "fifth": "ACQUISITION_LIMIT",
        "ops": "CAPABILITY_INVALID",
        "sid": "PRINCIPAL_UNACCREDITED",
        "group": "PRINCIPAL_UNACCREDITED",
        "poison": "OWNER_RETIRE_REQUIRED",
    }[fault]
    with pytest.raises(Exception, match=code):
        m._assemble_cpu_acquisition_owner(
            ops, principal_sid=sid, primary_group_sid=group
        )
    assert sdk.calls == ["locate"]


def test_control_sid_offsets_and_lengths_are_own_charged_storage():
    m, sdk, owner = assembly()
    control = m._LIVE_ACQUISITION_OWNERS[owner].control
    assert control.storage[9216:9228] == SID
    assert control.storage[9284:9296] == SID
    assert struct.unpack_from("<II", control.storage, 9488) == (12, 12)
    assert control.storage[9576:10240] == bytes(664)
    assert sdk.calls == []


@pytest.mark.parametrize(
    "name",
    [
        "_AcquisitionOwner",
        "_AnchorLocator",
        "_OwnedAcquisition",
        "_ClosedDescriptor",
        "_CpuAdmissionPin",
    ],
)
@pytest.mark.parametrize("operation", ["copy", "deepcopy", "repr"])
def test_opaque_acquisition_operations_have_no_authority_or_address(name, operation):
    import copy

    m, sdk, _owner = assembly()
    candidate = object.__new__(getattr(m, name))
    if operation == "repr":
        assert repr(candidate) == "<" + name + ">"
    else:
        with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
            getattr(copy, operation)(candidate)
    assert sdk.calls == []


@pytest.mark.parametrize(
    "role,mask", [("FILE_JOURNAL", 0x00120083), ("DIRECTORY_DOMAIN", 0x001200A6)]
)
def test_closed_descriptor_own_group_dacl_masks_and_charged_backing(role, mask):
    m, sdk, owner = assembly()
    descriptor = m._new_closed_descriptor(owner, role=m._NewObjectRole[role])
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    row = record.descriptors[descriptor]
    assert row.capability is descriptor and row.owner_ref is owner
    assert row.mask == mask and row.trustees[0] == SID
    assert row.trustees[1] == bytes.fromhex("010100000000000512000000")
    assert row.trustees[2] == bytes.fromhex("01020000000000052000000020020000")
    assert row.arena in record.backings and row.arena.requested_bytes <= 4096
    assert row.acl_length == 8 + sum(8 + len(sid) for sid in row.trustees)
    assert row.state.value == "live" and sdk.calls == ["descriptor"]
    assert record.inflight == [] and record.handles == 0


@pytest.mark.parametrize(
    "fault",
    [
        "control",
        "revision",
        "sacl",
        "owner",
        "group",
        "dacl",
        "ace_flags",
        "ace_mask",
        "ace_sid",
        "acl_size",
        "getter",
        "wrapper",
        "number",
        "exception",
        "interrupt",
    ],
)
def test_descriptor_incongruence_is_uncertain_and_retained(fault):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.descriptor(frame)
        row = frame.descriptor_record
        data = row.arena.storage
        changes = {
            "control": (2, "<H", 4),
            "revision": (0, "<B", 2),
            "sacl": (24, "<Q", 5),
            "owner": (8, "<Q", 9217),
            "group": (16, "<Q", 9285),
            "dacl": (32, "<Q", 41),
            "ace_flags": (49, "<B", 1),
            "ace_mask": (52, "<I", 0x10000000),
            "ace_sid": (56, "<B", 2),
            "acl_size": (42, "<H", 8),
        }
        if fault in changes:
            offset, fmt, value = changes[fault]
            struct.pack_into(fmt, data, offset, value)
        elif fault == "getter":
            row.getter_outputs = (0x1004, 1, 9217, False, 9284, False, True, 40, False)
        elif fault == "wrapper":
            return None
        elif fault == "number":
            return m._DescriptorCompletion(1)
        elif fault == "exception":
            raise RuntimeError("private-SD-cut")
        elif fault == "interrupt":
            raise KeyboardInterrupt("private-SD-cut")
        return result

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, sdk.locate, entered)
    with pytest.raises(Exception, match="RESOURCE_UNKNOWN"):
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    assert sdk.calls == ["descriptor"] and m._io._KERNEL_POISONED is True
    assert record.state.value == "unknown" and len(record.inflight) == 1
    assert record.inflight[0].frame.descriptor_record.arena in record.backings


@pytest.mark.parametrize("fault", ["known", "pending"])
def test_descriptor_bool_failure_known_vs_pending(fault):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.descriptor(frame)
        return m._DescriptorCompletion(
            False,
            m.AcquisitionDiagnostic(
                "DESCRIPTOR_INVALID", "descriptor", 997 if fault == "pending" else 5
            ),
        )

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, sdk.locate, entered)
    with pytest.raises(
        Exception,
        match="RESOURCE_UNKNOWN" if fault == "pending" else "DESCRIPTOR_INVALID",
    ):
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    assert sdk.calls == ["descriptor"]
    if fault == "known":
        assert record.inflight == [] and len(record.backings) == 1
        assert m._io._KERNEL_POISONED is False
    else:
        assert len(record.inflight) == 1 and len(record.backings) == 2
        assert m._io._KERNEL_POISONED is True


@pytest.mark.parametrize(
    "target_text",
    [
        "frame.phase = _CallPhase.RETURNED",
        "row.completion = _create_completion",
        "frame.phase = _CallPhase.COMPLETED",
        "frame.phase = _CallPhase.ACKNOWLEDGING",
        "record.inflight.remove(call)",
        "frame.phase = _CallPhase.ACKNOWLEDGED",
        "row.state = _AcquisitionState.CANDIDATE",
        "return acquisition",
    ],
)
@pytest.mark.parametrize("kind", ["ordinary", "interrupt", "typed"])
def test_open_post_success_cut_retains_actual_slot_and_call(target_text, kind):
    import inspect

    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    lines, start = inspect.getsourcelines(m._open)
    target = start + next(i for i, text in enumerate(lines) if target_text in text)
    errors = {
        "ordinary": RuntimeError("private-open-cut"),
        "interrupt": KeyboardInterrupt("private-open-cut"),
        "typed": m.AcquisitionError(
            m.AcquisitionDiagnostic("OPEN_FAILED", "open_anchor")
        ),
    }
    cut_error = errors[kind]

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is m._open.__code__
            and frame.f_lineno == target
        ):
            assert sdk.calls.count("open") == 1
            raise cut_error
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(Exception, match="RESOURCE_UNKNOWN"):
            m._open_owned_anchor(owner, locator)
    finally:
        sys.settrace(previous)
    assert record.handles == 1 and record.state.value == "unknown"
    assert sdk.calls.count("close") == 0 and len(record.inflight) == 1
    assert record.inflight[0].error is cut_error
    assert struct.unpack_from("<Q", record.control.storage, 0)[0] == 101


def test_unknown_process_blocks_new_backend_operations_with_zero_additional_calls():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.open(frame)
        raise RuntimeError("private-entered-error")

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(Exception, match="RESOURCE_UNKNOWN"):
        m._open_owned_anchor(owner, locator)
    calls = tuple(sdk.calls)
    with pytest.raises(Exception, match="OWNER_RETIRE_REQUIRED"):
        m._locate_anchor(owner, project_location="C:\\studio")
    outcome = m._close_acquisition_owner(owner)
    assert outcome.state == "unknown" and tuple(sdk.calls) == calls


def test_locator_call_charges_all_sdk_buffers_before_entry_and_returns_transients():
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.locate(frame)
        assert len(frame.arena_refs) == 3
        assert [arena.requested_bytes for arena in frame.arena_refs] == [
            10247,
            32775,
            65543,
        ]
        assert sum(arena.requested_bytes for arena in frame.arena_refs) == 108565
        assert all(arena in record.backings for arena in frame.arena_refs)
        assert record.inflight[0].charge == (3, 108565, 0)
        assert frame.arena_refs[1].segments[0][0] is m._SegmentName.PROJECT_INPUT
        return result

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    assert len(record.backings) == 2
    assert record.locators[locator].arena_refs[0] in record.backings
    assert record.inflight == []


def test_open_call_name_oa_unicode_backing_charged_before_entry():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.open(frame)
        assert len(frame.arena_refs) == 3
        names = [segment[0] for segment in frame.arena_refs[-1].segments]
        assert names == [
            m._SegmentName.UNICODE_NAME,
            m._SegmentName.UNICODE_STRING,
            m._SegmentName.OBJECT_ATTRIBUTES,
        ]
        assert frame.arena_refs[-1] in record.backings
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)
    assert len(record.backings) == 2 and record.inflight == []


@pytest.mark.parametrize("operation", ["locator", "descriptor", "nested"])
def test_shared_pool_locator_descriptor_and_frame_limits_preentry(operation):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    if operation == "locator":
        for _ in range(4):
            m._locate_anchor(owner, project_location="C:\\studio")
        calls = tuple(sdk.calls)
        with pytest.raises(Exception, match="ACQUISITION_LIMIT"):
            m._locate_anchor(owner, project_location="C:\\studio")
        assert tuple(sdk.calls) == calls
    elif operation == "descriptor":
        for _ in range(7):
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        calls = tuple(sdk.calls)
        with pytest.raises(Exception, match="ACQUISITION_LIMIT"):
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        assert len(record.backings) == 8 and tuple(sdk.calls) == calls
    else:
        locator = m._locate_anchor(owner, project_location="C:\\studio")

        def entered(frame):
            result = sdk.open(frame)
            with pytest.raises(Exception, match="ACQUISITION_LIMIT"):
                m._locate_anchor(owner, project_location="C:\\studio")
            return result

        record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
        m._open_owned_anchor(owner, locator)
        assert sdk.calls == ["locate", "open"]


def test_native_factory_requires_actual_nominal_k4a_before_loader(monkeypatch):
    m, sdk, owner = assembly()
    calls = []
    monkeypatch.setattr(importlib, "import_module", lambda *args: calls.append(args))
    with pytest.raises(m.AcquisitionError, match="ADMISSION_REQUIRED"):
        m._new_native_acquisition_owner(owner)
    with pytest.raises(m.AcquisitionError, match="ADMISSION_REQUIRED"):
        m._new_native_acquisition_owner(
            {"source": "native_windows_x64", "trusted": True}
        )
    assert calls == [] and sdk.calls == []


def test_info_pure_observes_candidate_closed_and_unknown_without_sdk():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    acquisition = m._open_owned_anchor(owner, locator)
    info = m._acquisition_info(owner, acquisition)
    assert (info.profile, info.disposition, info.state, info.provenance) == (
        "ANCHOR_CANDIDATE",
        "OPEN_EXISTING",
        "candidate",
        "cpu_double",
    )
    assert set(vars(info)) == {"profile", "disposition", "state", "provenance"}
    m._close_acquisition(owner, acquisition)
    assert m._acquisition_info(owner, acquisition).state == "closed"
    calls = tuple(sdk.calls)
    m._io._KERNEL_POISONED = True
    assert m._acquisition_info(owner, acquisition).state == "closed"
    assert tuple(sdk.calls) == calls


@pytest.mark.parametrize(
    "args",
    [
        ("UNKNOWN", "owner", None, None),
        ("CONFLICT", "locate", None, None),
        ("NOT_FOUND", "descriptor", None, None),
        ("RESOURCE_UNKNOWN", "info", None, None),
        ("OPEN_FAILED", "open_anchor", True, None),
        ("OPEN_FAILED", "open_anchor", -1, None),
        ("OPEN_FAILED", "open_anchor", None, True),
        ("OPEN_FAILED", "open_anchor", None, 2**32),
    ],
)
def test_diagnostic_closed_codes_operations_and_u32_types(args):
    m = load()
    with pytest.raises(ValueError, match="DIAGNOSTIC_INVALID"):
        m.AcquisitionDiagnostic(*args)


@pytest.mark.parametrize(
    "args", [("candidate", ()), ("closed", []), ("unknown", (object(),))]
)
def test_outcome_exact_immutable_causes(args):
    m = load()
    with pytest.raises(ValueError, match="DIAGNOSTIC_INVALID"):
        m.AcquisitionCloseOutcome(*args)


@pytest.mark.parametrize(
    "role,profile,parent_profile,access,share,options,attributes",
    [
        (
            "FILE_JOURNAL",
            "CREATE_FILE",
            "PARENT_CREATE_FILE",
            0x00120083,
            0,
            0x0020006A,
            0x80,
        ),
        (
            "DIRECTORY_DOMAIN",
            "CREATE_DIRECTORY",
            "PARENT_CREATE_DOMAIN",
            0x001200A6,
            3,
            0x00200021,
            0x10,
        ),
    ],
)
def test_cpu_create_noreplace_exact_descriptor_role_and_current_parent_guard(
    role, profile, parent_profile, access, share, options, attributes
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    anchor = m._open_owned_anchor(owner, locator)
    parent = m._open_owned_component(
        owner,
        anchor,
        "parent",
        m._AcquireProfile[parent_profile],
        m._Disposition.OPEN_EXISTING,
    )
    descriptor = m._new_closed_descriptor(owner, role=m._NewObjectRole[role])
    m._seed_cpu_parent_admission(owner, parent, role=m._NewObjectRole[role])
    acquisition = m._open_owned_component(
        owner,
        parent,
        "new",
        m._AcquireProfile[profile],
        m._Disposition.CREATE_NEW,
        descriptor,
    )
    frame = sdk.frames[-1]
    assert (frame.access, frame.share, frame.options, frame.file_attributes) == (
        access,
        share,
        options,
        attributes,
    )
    assert frame.nt_disposition == 2 and frame.descriptor_ref is descriptor
    assert (
        m._LIVE_ACQUISITION_OWNERS[owner]
        .acquisitions[acquisition]
        .completion.information
        == 2
    )


@pytest.mark.parametrize(
    "fault,code",
    [
        ("missing_guard", "SECURITY_UNACCREDITED"),
        ("wrong_guard", "SECURITY_UNACCREDITED"),
        ("missing_descriptor", "DESCRIPTOR_INVALID"),
        ("wrong_descriptor", "DESCRIPTOR_INVALID"),
        ("forged_descriptor", "DESCRIPTOR_INVALID"),
    ],
)
def test_create_guards_preentry_with_positive_read_callback(fault, code):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    anchor = m._open_owned_anchor(owner, locator)
    parent = m._open_owned_component(
        owner,
        anchor,
        "parent",
        m._AcquireProfile.PARENT_CREATE_FILE,
        m._Disposition.OPEN_EXISTING,
    )
    descriptor = m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    if fault != "missing_guard":
        m._seed_cpu_parent_admission(
            owner,
            parent,
            role=m._NewObjectRole.DIRECTORY_DOMAIN
            if fault == "wrong_guard"
            else m._NewObjectRole.FILE_JOURNAL,
        )
    if fault == "missing_descriptor":
        descriptor = None
    elif fault == "wrong_descriptor":
        descriptor = m._new_closed_descriptor(
            owner, role=m._NewObjectRole.DIRECTORY_DOMAIN
        )
    elif fault == "forged_descriptor":
        descriptor = object.__new__(m._ClosedDescriptor)
    calls = tuple(sdk.calls)
    with pytest.raises(m.AcquisitionError, match=code):
        m._open_owned_component(
            owner,
            parent,
            "new",
            m._AcquireProfile.CREATE_FILE,
            m._Disposition.CREATE_NEW,
            descriptor,
        )
    assert tuple(sdk.calls) == calls


def test_descriptor_role_enum_and_cpu_parent_role_exact():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    with pytest.raises(m.AcquisitionError, match="DESCRIPTOR_INVALID"):
        m._new_closed_descriptor(owner, role="FILE_JOURNAL")
    with pytest.raises(m.AcquisitionError, match="SECURITY_UNACCREDITED"):
        m._seed_cpu_parent_admission(owner, parent, role="FILE_JOURNAL")
    assert sdk.calls == ["locate", "open"]


def test_sdk_utf16_strict_termination_and_multisz_single_target():
    m = load()
    root = "C:\\".encode("utf-16-le") + b"\0\0"
    assert m._decode_utf16z(root, 4) == "C:\\"
    target = "\\Device\\HarddiskVolume3"
    data = (target + "\0\0").encode("utf-16-le")
    assert m._decode_device_multisz(data, len(data) // 2) == target


@pytest.mark.parametrize(
    "data,count",
    [
        (b"\0\0", 1),
        ("\\Device\\HarddiskVolume3\0".encode("utf-16-le"), 24),
        (
            "\\Device\\HarddiskVolume3\0\\Device\\HarddiskVolume4\0\0".encode(
                "utf-16-le"
            ),
            47,
        ),
        ("\\Device\\HarddiskVolumeX\0\0".encode("utf-16-le"), 25),
        ("\\Device\\HarddiskVolume3\0\0".encode("utf-16-le"), True),
        ("\\Device\\HarddiskVolume3\0\0".encode("utf-16-le"), 32769),
    ],
)
def test_sdk_device_count_bound_and_ambiguous_outputs(data, count):
    m = load()
    with pytest.raises(m.AcquisitionError, match="ANCHOR_UNACCREDITED"):
        m._decode_device_multisz(data, count)


@pytest.mark.parametrize(
    "field,value",
    [
        ("root_dos", "C:\\mount\\"),
        ("guid", "Volume{invalid}"),
        ("target", "\\Device\\Other3"),
        ("nt_name", "\\??\\C:\\"),
        ("root_dos", None),
    ],
)
def test_locator_success_incongruence_unknown_keeps_all_sdk_backings(field, value):
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.locate(frame)
        setattr(frame.locator_record, field, value)
        return result

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    with pytest.raises(m.AcquisitionError, match="RESOURCE_UNKNOWN"):
        m._locate_anchor(owner, project_location="C:\\studio")
    assert sdk.calls == ["locate"] and len(record.inflight) == 1
    assert len(record.backings) == 3 and m._io._KERNEL_POISONED is True


def cpu_handler(module, name):
    """Cuerpo actual extraído sin cambiar un nodo; no emite autoridad nativa."""
    import ast
    import hashlib

    path = SCRIPTS / "storage_journal_windows_abi.py"
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    digest = hashlib.sha256(
        ast.dump(node, include_attributes=True).encode()
    ).hexdigest()
    namespace = dict(vars(module))
    namespace["__name__"] = "cpu_ast_" + digest
    exec(  # noqa: S102 - AST exacto autorizado ROOT; no autoridad ni cobertura nativa
        compile(
            ast.Module(body=[node], type_ignores=[]), "<CPU-AST-" + digest + ">", "exec"
        ),
        namespace,
    )
    return namespace[name], hashlib.sha256(raw).hexdigest(), digest


def test_ast_cpu_actual_open_handler_dispatches_exact_sdk_arguments():
    import ctypes as c

    m, sdk, owner = assembly()
    abi_module = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, _, _ = cpu_handler(abi_module, "_execute_acquisition_open")
    abi = abi_module._build_acquisition_abi(c)
    captured = []
    steps = []
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def create(
        output,
        access,
        oa,
        iosb,
        allocation,
        attributes,
        share,
        disposition,
        options,
        ea,
        ea_length,
    ):
        captured.append(
            (access, attributes, share, disposition, options, allocation, ea, ea_length)
        )
        assert oa.contents.Length == 48 and oa.contents.RootDirectory is None
        assert (
            oa.contents.Attributes == 0x40
            and oa.contents.SecurityQualityOfService is None
        )
        output[0] = 101
        iosb.contents.u.Status = 0
        iosb.contents.Information = 1
        return 0

    def entered(frame):
        sdk.calls.append("open")
        result = handler(c, abi, {"NtCreateFile": create}, frame)
        steps.extend(call.function.value for call in record.inflight[0].subcalls)
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    acquisition = m._open_owned_anchor(owner, locator)
    assert m._acquisition_info(owner, acquisition).provenance == "cpu_double"
    assert captured == [(0x001200A0, 0, 3, 1, 0x00200021, None, None, 0)]
    assert sdk.calls == ["locate", "open"]
    assert steps == ["NtCreateFile"]


@pytest.mark.parametrize(
    "returned,error", [(1, None), (-1, None), (0, 0), (0, 5), (0, 997)]
)
def test_ast_cpu_actual_close_handler_immediate_bool_error_and_slot(returned, error):
    import ctypes as c

    m, sdk, owner = assembly()
    abi_module = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, _, _ = cpu_handler(abi_module, "_execute_acquisition_close")
    sequence = []
    ctypes_fixture = types.SimpleNamespace(
        **{name: getattr(c, name) for name in dir(c) if not name.startswith("__")}
    )
    ctypes_fixture.get_last_error = lambda: sequence.append("last_error") or error
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    acquisition = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def close(handle):
        sequence.append("CloseHandle")
        assert handle == 101
        return returned

    def entered(frame):
        sdk.calls.append("close")
        return handler(ctypes_fixture, {"CloseHandle": close}, frame)

    record.ops = m._AcquisitionOps(sdk.open, entered, sdk.locate, sdk.descriptor)
    outcome = m._close_acquisition(owner, acquisition)
    assert outcome.state == ("closed" if returned != 0 else "unknown")
    assert sequence == (
        ["CloseHandle"] if returned != 0 else ["CloseHandle", "last_error"]
    )
    assert sdk.calls.count("close") == 1
    assert struct.unpack_from("<i", record.control.storage, 7168)[0] == returned


class LocatorSdk:
    def __init__(self, c, fault=None):
        self.c, self.fault = c, fault
        self.calls = []
        self.guid = "\\\\?\\Volume{01234567-89ab-cdef-0123-456789abcdef}\\"
        self.target = "\\Device\\HarddiskVolume3"

    def text(self, pointer):
        words = self.c.cast(pointer, self.c.POINTER(self.c.c_uint16))
        values = []
        for offset in range(32768):
            if words[offset] == 0:
                return bytes(values).decode("utf-16-le")
            values.extend(int(words[offset]).to_bytes(2, "little"))
        raise AssertionError("input own no terminado")

    def write(self, pointer, text):
        words = self.c.cast(pointer, self.c.POINTER(self.c.c_uint16))
        data = text.encode("utf-16-le")
        for offset in range(len(data) // 2):
            words[offset] = int.from_bytes(data[offset * 2 : offset * 2 + 2], "little")

    def path(self, input_pointer, output, capacity):
        self.calls.append("GetVolumePathNameW")
        assert self.text(input_pointer) == "C:\\studio" and capacity == 32768
        self.write(output, ("C:\\mount\\" if self.fault == "mount" else "C:\\") + "\0")
        return 1

    def drive(self, root):
        self.calls.append("GetDriveTypeW")
        assert self.text(root) == "C:\\"
        return 4 if self.fault == "drive" else 3

    def name(self, root, output, capacity):
        self.calls.append("GetVolumeNameForVolumeMountPointW")
        assert self.text(root) == "C:\\" and capacity == 50
        self.write(
            output,
            ("\\\\?\\Volume{invalid}\\" if self.fault == "guid" else self.guid) + "\0",
        )
        return 1

    def query(self, name, output, capacity):
        self.calls.append("QueryDosDeviceW")
        assert capacity == 32768
        key = self.text(name)
        assert key in {"C:", self.guid[4:-1]}
        target = self.target
        count = self.calls.count("QueryDosDeviceW")
        if self.fault == "pair" and key != "C:":
            target += "4"
        if self.fault == "changed" and count >= 3:
            target += "4"
        if self.fault == "ambiguous":
            target += "\0\\Device\\HarddiskVolume4"
        if self.fault == "failed":
            return 0
        data = target + "\0\0"
        self.write(output, data)
        return 32769 if self.fault == "count" else len(data)

    def functions(self):
        return {
            "GetVolumePathNameW": self.path,
            "GetDriveTypeW": self.drive,
            "GetVolumeNameForVolumeMountPointW": self.name,
            "QueryDosDeviceW": self.query,
        }


@pytest.mark.parametrize(
    "fault",
    [None, "mount", "drive", "guid", "pair", "changed", "ambiguous", "count", "failed"],
)
def test_ast_cpu_locator_closed_sdk_sequence_without_retry(fault):
    import ctypes as c

    m, sdk, owner = assembly()
    abi_module = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, _, _ = cpu_handler(abi_module, "_execute_acquisition_locator")
    ctypes_fixture = types.SimpleNamespace(
        **{name: getattr(c, name) for name in dir(c) if not name.startswith("__")}
    )
    ctypes_fixture.get_last_error = lambda: 5
    locator_sdk = LocatorSdk(c, fault)
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.calls.append("locate")
        return handler(ctypes_fixture, locator_sdk.functions(), frame)

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    if fault is None:
        locator = m._locate_anchor(owner, project_location="C:\\studio")
        assert record.locators[locator].target == locator_sdk.target
        assert (
            locator_sdk.calls
            == [
                "GetVolumePathNameW",
                "GetDriveTypeW",
                "GetVolumeNameForVolumeMountPointW",
            ]
            + ["QueryDosDeviceW"] * 4
        )
    else:
        with pytest.raises(m.AcquisitionError, match="ANCHOR_UNACCREDITED"):
            m._locate_anchor(owner, project_location="C:\\studio")
        assert m._io._KERNEL_POISONED is False
        assert record.inflight == [] and len(record.backings) == 1
        assert locator_sdk.calls.count("QueryDosDeviceW") <= 4
    assert sdk.calls == ["locate"]


class DescriptorSdk:
    def __init__(self, c, abi, fault=None):
        self.c, self.abi, self.fault = c, abi, fault
        self.calls = []
        self.acl_offset = 8

    def bytes_at(self, pointer, count):
        array = self.c.cast(pointer, self.c.POINTER(self.c.c_uint8))
        return bytes(array[i] for i in range(count))

    def write(self, pointer, data):
        array = self.c.cast(pointer, self.c.POINTER(self.c.c_uint8))
        for i, value in enumerate(data):
            array[i] = value

    def execute(self, name, *args):
        self.calls.append(name)
        if self.fault == name:
            return 0
        c = self.c
        if name == "CreateWellKnownSid":
            kind, domain, output, length = args
            assert domain is None and length[0] == 68 and kind in {22, 26}
            data = bytes.fromhex(
                "010100000000000512000000"
                if kind == 22
                else "01020000000000052000000020020000"
            )
            self.write(output, data)
            length[0] = len(data)
        elif name == "IsValidSid":
            return 1
        elif name == "GetLengthSid":
            return 8 + 4 * self.bytes_at(args[0], 2)[1]
        elif name == "InitializeSecurityDescriptor":
            assert args[1] == 1
            self.write(args[0], bytes([1]) + bytes(39))
        elif name == "InitializeAcl":
            pointer, length, revision = args
            assert revision == 2
            self.write(pointer, struct.pack("<BBHHH", 2, 0, length, 0, 0))
        elif name == "AddAccessAllowedAce":
            pointer, revision, mask, sid_pointer = args
            sid = self.bytes_at(sid_pointer, 8 + 4 * self.bytes_at(sid_pointer, 2)[1])
            self.write(
                pointer + self.acl_offset,
                struct.pack("<BBHI", 0, 0, 8 + len(sid), mask) + sid,
            )
            self.acl_offset += 8 + len(sid)
            acl = c.cast(pointer, c.POINTER(self.abi["ACL"])).contents
            acl.AceCount += 1
        else:
            sd = c.cast(args[0], c.POINTER(self.abi["SECURITY_DESCRIPTOR"])).contents
            if name == "SetSecurityDescriptorOwner":
                assert args[2] == 0
                sd.Owner = args[1]
            elif name == "SetSecurityDescriptorGroup":
                assert args[2] == 0
                sd.Group = args[1]
            elif name == "SetSecurityDescriptorDacl":
                assert args[1] == 1 and args[3] == 0
                sd.Dacl = args[2]
                sd.Control |= 4
            elif name == "SetSecurityDescriptorControl":
                assert args[1:] == (0x1000, 0x1000)
                sd.Control |= 0x1000
            elif name == "IsValidSecurityDescriptor":
                return 1
            elif name == "GetSecurityDescriptorControl":
                args[1][0], args[2][0] = sd.Control, sd.Revision
            elif name == "GetSecurityDescriptorOwner":
                args[1][0], args[2][0] = sd.Owner, 0
            elif name == "GetSecurityDescriptorGroup":
                args[1][0], args[2][0] = sd.Group, 0
            elif name == "GetSecurityDescriptorDacl":
                args[1][0], args[2][0], args[3][0] = 1, sd.Dacl, 0
            else:
                raise AssertionError(name)
        return 1

    def functions(self):
        names = [
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
        return {
            name: (lambda *args, function=name: self.execute(function, *args))
            for name in names
        }


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "InitializeAcl",
        "IsValidSecurityDescriptor",
        "CreateWellKnownSid",
        "GetSecurityDescriptorGroup",
    ],
)
def test_ast_cpu_descriptor_full_sdk_constructor_and_getters(fault):
    import ctypes as c

    m, sdk, owner = assembly()
    abi_module = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, _, _ = cpu_handler(abi_module, "_execute_acquisition_descriptor")
    abi = abi_module._build_acquisition_abi(c)
    ctypes_fixture = types.SimpleNamespace(
        **{name: getattr(c, name) for name in dir(c) if not name.startswith("__")}
    )
    ctypes_fixture.get_last_error = lambda: 5
    descriptor_sdk = DescriptorSdk(c, abi, fault)
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.calls.append("descriptor")
        return handler(ctypes_fixture, descriptor_sdk.functions(), frame)

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, sdk.locate, entered)
    if fault is None:
        descriptor = m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        assert record.descriptors[descriptor].getter_outputs[0:2] == (0x1004, 1)
        assert descriptor_sdk.calls.count("AddAccessAllowedAce") == 3
        assert (
            descriptor_sdk.calls[:6]
            == ["CreateWellKnownSid", "IsValidSid", "GetLengthSid"] * 2
        )
        assert descriptor_sdk.calls[-4:] == [
            "GetSecurityDescriptorControl",
            "GetSecurityDescriptorOwner",
            "GetSecurityDescriptorGroup",
            "GetSecurityDescriptorDacl",
        ]
    else:
        with pytest.raises(m.AcquisitionError, match="DESCRIPTOR_INVALID"):
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        assert descriptor_sdk.calls[-1] == fault
        assert record.inflight == [] and len(record.backings) == 1
        assert m._io._KERNEL_POISONED is False
    assert sdk.calls == ["descriptor"]


def test_cpu_original_descriptor_known_failure_keeps_owner_usable_without_retry():
    import ctypes as c

    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    descriptor_sdk = DescriptorSdk(c, abi._build_acquisition_abi(c), "InitializeAcl")
    fixture = types.SimpleNamespace(
        **{name: getattr(c, name) for name in dir(c) if not name.startswith("__")}
    )
    last_errors = []
    fixture.get_last_error = lambda: last_errors.append(5) or 5
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.calls.append("descriptor")
        assert record.source == "cpu_double" and frame.owner_ref is owner
        return abi._execute_acquisition_descriptor(
            fixture, descriptor_sdk.functions(), frame
        )

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, sdk.locate, entered)
    with pytest.raises(m.AcquisitionError, match="DESCRIPTOR_INVALID"):
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    assert descriptor_sdk.calls[-1] == "InitializeAcl"
    assert descriptor_sdk.calls.count("InitializeAcl") == 1 and last_errors == [5]
    assert sdk.calls == ["descriptor"] and record.inflight == []
    assert record.backings == [record.control] and record.state is m._OwnerState.LIVE
    assert not m._io._KERNEL_POISONED and record.handles == record.next_slot == 0
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    assert record.locators[locator].state is m._AuxiliaryState.LIVE


def test_owner_reload_cannot_reset_lifetime_quota_or_drop_strong_custody():
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    for _ in range(3):
        m._assemble_cpu_acquisition_owner(
            record.ops, principal_sid=SID, primary_group_sid=SID
        )
    before = tuple(m._LIVE_ACQUISITION_OWNERS.values())
    reloaded = importlib.reload(m)
    ops = reloaded._AcquisitionOps(sdk.open, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(
        reloaded.AcquisitionError, match="ACQUISITION_LIMIT|OWNER_RETIRE_REQUIRED"
    ):
        reloaded._assemble_cpu_acquisition_owner(
            ops, principal_sid=SID, primary_group_sid=SID
        )
    assert tuple(reloaded._LIVE_ACQUISITION_OWNERS.values()) == before
    assert record.control is not None and sdk.calls == []


def cpu_identity_fixture(m):
    path = SCRIPTS.parent / "tests" / "test_storage_journal_windows_identity.py"
    name = "cpu_identity_fixture_" + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(name, path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    sdk = helper.TokenSdk(m._identity)
    authority = m._identity._assemble_cpu_identity_session(
        m._identity._CpuIdentityOps(sdk.execute),
        principal_sid=SID,
        primary_group_sid=SID,
    )
    admission = m._identity._issue_cpu_acquisition_admission(
        authority, scope=m._identity._AdmissionScope.CANDIDATE_READ_ONLY
    )
    return sdk, authority, admission


def test_cpu_pin_new_pre_post_effective_observation_one_time_same_thread():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._io._kernel_domain() as boundary, record.lock:
        frame = m._AcquisitionCallFrame(
            owner, "locate", arena_refs=(record.control,), boundary_lease_ref=boundary
        )
        call = m._AcquisitionCallRecord(frame, bytes(record.control.storage))
        record.inflight.append(call)
        pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        assert (
            type(pin) is m._CpuAdmissionPin and type(pin) is not identity._AdmissionPin
        )
        assert source.counters["observations"] == 2
        assert frame.admission_pin is pin
        identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
        assert source.counters["observations"] == 3
        calls = tuple(token_sdk.calls)
        identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
        assert tuple(token_sdk.calls) == calls
        assert source.pins[pin].state == "completed"
    assert sdk.calls == []


def test_closed_backend_rejects_actual_cpu_frame_before_sdk(monkeypatch):
    import ctypes as c

    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    calls = []

    class Function:
        def __call__(self, *args):
            calls.append(args)
            raise AssertionError("no SDK entry permitido")

    functions = {member.value: Function() for member in m._SdkFunction}
    monkeypatch.setattr(c, "WinDLL", lambda *a, **k: types.SimpleNamespace(**functions))
    backend = abi._new_native_acquisition_backend()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    errors = []

    def entered(frame):
        result = sdk.open(frame)
        try:
            backend.open(frame)
        except Exception as error:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
            errors.append(error)
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)
    assert calls == [] and sdk.calls == ["locate", "open"]
    assert len(errors) == 1 and str(errors[0]) == "CAPABILITY_INVALID"


def test_owner_guard_preregisters_authentic_boundary_lease_in_frame():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.open(frame)
        assert type(frame.boundary_lease_ref) is m._io._KernelBoundaryLease
        assert m._io._BOUNDARY_LEASES[frame.boundary_lease_ref][0] == record.pid
        assert record.lock._is_owned() and m._io._NATIVE_BOUNDARY_LOCK._is_owned()
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)


def test_sdk_ownership_predicate_on_actual_cpu_frame_has_no_native_authority():
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        result = sdk.open(frame)
        assert abi._sdk_frame_owned(frame, "open", record.ops) is True
        assert record.source == "cpu_double"
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)


@pytest.mark.parametrize(
    "fault,code",
    [
        ("lock", "CAPABILITY_INVALID"),
        ("boundary", "CAPABILITY_INVALID"),
        ("frame", "CAPABILITY_INVALID"),
        ("frame_owner", "OWNER_MISMATCH"),
        ("pid", "CAPABILITY_INVALID"),
        ("revoked", "CAPABILITY_REVOKED"),
        ("scope", "ADMISSION_REQUIRED"),
        ("pin_limit", "OWNER_RETIRE_REQUIRED"),
        ("observation_limit", "OWNER_RETIRE_REQUIRED"),
    ],
)
def test_cpu_pin_guard_held_owner_domain_frame_scope_and_quotas(fault, code):
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    frame = m._AcquisitionCallFrame(owner, "locate", arena_refs=(record.control,))
    record.inflight.append(
        m._AcquisitionCallRecord(frame, bytes(record.control.storage))
    )
    before = tuple(token_sdk.calls)
    if fault == "pid":
        record.pid += 1
    elif fault == "frame":
        record.inflight.clear()
    elif fault == "frame_owner":
        frame.owner_ref = object()
    elif fault == "revoked":
        source.admissions[admission].state = "revoked"
    elif fault == "scope":
        frame.operation = "open_component"
        frame.record_ref = types.SimpleNamespace(
            profile=m._AcquireProfile.WRITER_EXISTING
        )
    elif fault == "pin_limit":
        source.pin_slots_reserved = 2048
    elif fault == "observation_limit":
        source.counters["observations"] = 8191

    def attempt():
        with pytest.raises(identity.IdentityError, match=code):
            identity._pin_cpu_acquisition_admission(admission, owner=owner)

    if fault == "lock":
        with m._io._kernel_domain() as boundary:
            frame.boundary_lease_ref = boundary
            attempt()
    elif fault == "boundary":
        with record.lock:
            attempt()
    else:
        with m._io._kernel_domain() as boundary, record.lock:
            frame.boundary_lease_ref = boundary
            attempt()
    assert tuple(token_sdk.calls) == before and sdk.calls == []


@pytest.mark.parametrize("phase", ["pre", "post"])
def test_cpu_pin_principal_stamp_change_revokes_and_never_promotes(phase):
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._io._kernel_domain() as boundary, record.lock:
        frame = m._AcquisitionCallFrame(
            owner, "locate", arena_refs=(record.control,), boundary_lease_ref=boundary
        )
        record.inflight.append(
            m._AcquisitionCallRecord(frame, bytes(record.control.storage))
        )
        if phase == "pre":
            token_sdk.stamp = (1, 2, 9)
            with pytest.raises(identity.IdentityError, match="PRINCIPAL_UNACCREDITED"):
                identity._pin_cpu_acquisition_admission(admission, owner=owner)
        else:
            pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
            token_sdk.stamp = (1, 2, 9)
            with pytest.raises(identity.IdentityError, match="PRINCIPAL_UNACCREDITED"):
                identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
            assert source.pins[pin].state == "revoked"
    assert source.state == "revoked" and sdk.calls == []
    assert not source.lock._is_owned()


def test_cpu_pin_wrong_thread_rejects_without_wait_or_query():
    import threading

    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    errors = []
    with m._io._kernel_domain() as boundary, record.lock:
        frame = m._AcquisitionCallFrame(
            owner, "locate", arena_refs=(record.control,), boundary_lease_ref=boundary
        )
        record.inflight.append(
            m._AcquisitionCallRecord(frame, bytes(record.control.storage))
        )
        pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        before = tuple(token_sdk.calls)

        def foreign():
            try:
                identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
            except Exception as error:  # noqa: BLE001 - custodia fuerte ante cortes; sin retry ni cleanup especulativo
                errors.append(error)

        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(timeout=1)
        assert not thread.is_alive() and tuple(token_sdk.calls) == before
        assert len(errors) == 1 and str(errors[0]) == "OWNER_MISMATCH/complete"
        assert source.pins[pin].state == "active"
        identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
    assert sdk.calls == []


def test_owner_metadata_boundary_closed_api_builds_registered_frame_and_lease():
    m, sdk, owner = assembly()
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner) as frame:
        assert frame.owner_ref is owner and frame.operation == "owner"
        assert frame.phase is m._CallPhase.RESERVED and frame.arena_refs == (
            record.control,
        )
        assert record.inflight[0].frame is frame
        assert frame.boundary_lease_ref in m._io._BOUNDARY_LEASES
        assert record.lock._is_owned() and m._io._NATIVE_BOUNDARY_LOCK._is_owned()
        assert record.handles == 0 and record.next_slot == 0
    assert record.inflight == [] and sdk.calls == []


def test_cpu_abort_unentered_pin_releases_only_session_lease_without_query():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner) as _frame:
        pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        before = tuple(token_sdk.calls)
        identity._abort_cpu_acquisition_admission_pin(pin, owner=owner)
        assert source.pins[pin].state == "aborted"
        assert not source.lock._is_owned() and tuple(token_sdk.calls) == before
        identity._abort_cpu_acquisition_admission_pin(pin, owner=owner)
        assert tuple(token_sdk.calls) == before
    assert record.inflight == [] and sdk.calls == []


@pytest.mark.parametrize("phase", ["pre", "post"])
def test_cpu_query_uncertainty_retains_pin_owner_and_poison(phase):
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def interrupted(call):
        result = token_sdk.execute(call)
        if call.function == "OpenProcessToken":
            raise KeyboardInterrupt("private-pin-query-cut")
        return result

    with m._owner_pin_boundary(owner) as _frame:
        if phase == "post":
            pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        source.ops = identity._CpuIdentityOps(interrupted)
        with pytest.raises(identity.IdentityError, match="RESOURCE_UNKNOWN"):
            if phase == "pre":
                identity._pin_cpu_acquisition_admission(admission, owner=owner)
            else:
                identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
        assert m._io._KERNEL_POISONED is True
        assert any(pin_record.state == "unknown" for pin_record in source.pins.values())
        assert source.owner_refs[owner] is record and source.frame is not None
    assert record.inflight and sdk.calls == []


@pytest.mark.parametrize(
    "fault",
    [
        "slot_bool",
        "slot_oob",
        "logical_bool",
        "requested_mismatch",
        "foreign_arena",
        "missing_backing",
        "storage_bytes",
        "aligned_bool",
        "arena_tuple",
        "control_shape",
        "access_bool",
        "recipe_access",
    ],
)
def test_sdk_frame_metadata_guard_rejects_before_dispatch_on_actual_cpu_frame(fault):
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    reached = []

    def entered(frame):
        result = sdk.open(frame)
        reached.append(frame)
        control = record.control
        target, attribute, changed = {
            "slot_bool": (frame, "slot_index", True),
            "slot_oob": (frame, "slot_index", 256),
            "logical_bool": (control, "logical_length", True),
            "requested_mismatch": (control, "requested_bytes", 10240),
            "foreign_arena": (control, "owner_ref", object()),
            "missing_backing": (record, "backings", []),
            "storage_bytes": (control, "storage", bytes(control.storage)),
            "aligned_bool": (control, "aligned_offset", True),
            "arena_tuple": (frame, "arena_refs", list(frame.arena_refs)),
            "control_shape": (control, "logical_length", 10232),
            "access_bool": (frame, "access", True),
            "recipe_access": (frame, "access", 0xFFFFFFFF),
        }[fault]
        before = getattr(target, attribute)
        setattr(target, attribute, changed)
        try:
            assert abi._sdk_frame_owned(frame, "open", record.ops) is False
        finally:
            setattr(target, attribute, before)
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)
    assert reached and sdk.calls == ["locate", "open"]


def test_owner_close_with_active_registered_pin_retains_control_and_frame():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner) as frame:
        pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        before = tuple(token_sdk.calls)
        control, operations = record.control, record.ops
        outcome = m._close_acquisition_owner(owner)
        assert outcome.state == "unknown"
        assert record.control is control and record.ops is operations
        assert record.inflight[0].frame is frame and source.pins[pin].state == "active"
        assert tuple(token_sdk.calls) == before and sdk.calls == []


@pytest.mark.parametrize("phase", ["pre", "post"])
def test_cpu_pin_callback_typed_error_is_unknown_without_recognized_cleanup(phase):
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    cause = identity.IdentityError(
        identity.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query")
    )
    reached = []

    def interrupted(call):
        result = token_sdk.execute(call)
        if call.function == "OpenProcessToken":
            reached.append(call)
            raise cause
        return result

    with m._owner_pin_boundary(owner):
        if phase == "post":
            pin = identity._pin_cpu_acquisition_admission(admission, owner=owner)
        source.ops = identity._CpuIdentityOps(interrupted)
        with pytest.raises(identity.IdentityError, match="RESOURCE_UNKNOWN"):
            if phase == "pre":
                identity._pin_cpu_acquisition_admission(admission, owner=owner)
            else:
                identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
        assert reached and source.state == "unknown" and m._io._KERNEL_POISONED
        assert any(row.state == "unknown" for row in source.pins.values())
    assert record.inflight and sdk.calls == []


@pytest.mark.parametrize(
    "name",
    [
        "_AcquisitionOwner",
        "_AnchorLocator",
        "_OwnedAcquisition",
        "_ClosedDescriptor",
        "_CpuAdmissionPin",
    ],
)
def test_acquisition_capability_construction_and_copy_are_not_authority(name):
    import copy

    m, sdk, _owner = assembly()
    cls = getattr(m, name)
    with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
        cls()
    candidate = object.__new__(cls)
    for operation in (copy.copy, copy.deepcopy):
        with pytest.raises(TypeError, match="CAPABILITY_INVALID"):
            operation(candidate)
    assert repr(candidate) == "<" + name + ">"
    assert sdk.calls == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("profile", "private-secret-path"),
        ("profile", 1),
        ("disposition", "private-secret-sid"),
        ("state", "reserved"),
        ("provenance", "private-backend-address"),
        ("provenance", True),
    ],
)
def test_acquisition_info_rejects_arbitrary_payloads(field, value):
    m, _, _ = assembly()
    values = {
        "profile": "READ_EXISTING",
        "disposition": "OPEN_EXISTING",
        "state": "candidate",
        "provenance": "cpu_double",
    }
    values[field] = value
    with pytest.raises(ValueError, match="INFO_INVALID"):
        m.AcquisitionInfo(**values)


def test_close_frame_retains_actual_boundary_and_control_before_cpu_callback():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    reached = []

    def entered(frame):
        result = sdk.close(frame)
        reached.append(frame)
        assert frame.arena_refs == (record.control,)
        assert type(frame.boundary_lease_ref) is m._io._KernelBoundaryLease
        assert frame.boundary_lease_ref in m._io._BOUNDARY_LEASES
        assert record.inflight[0].frame is frame
        return result

    record.ops = m._AcquisitionOps(sdk.open, entered, sdk.locate, sdk.descriptor)
    assert m._close_acquisition(owner, item).state == "closed"
    assert reached


def test_cpu_owner_binding_retains_nominal_admission_principal_policy_and_epoch():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    row = m._LIVE_ACQUISITION_OWNERS[owner]
    before = tuple(token_sdk.calls)
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    assert row.source == "cpu_double" and row.admission_ref is admission
    assert (
        row.principal_sid == source.principal_sid
        and row.primary_group_sid == source.primary_group_sid
    )
    assert row.policy_ref is source.policy_ref and row.epoch_ref is source.epoch_ref
    assert source.owner_refs[owner] is row and tuple(token_sdk.calls) == before
    assert sdk.calls == []


def test_cpu_bound_owner_pipeline_pins_each_actual_backend_and_postobserves():
    m, sdk, owner = assembly()
    _token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    observations_before = source.counters["observations"]
    reached = []

    def wrapper(function):
        def entered(frame):
            reached.append(frame.operation)
            assert type(frame.admission_pin) is m._CpuAdmissionPin
            pin_row = source.pins[frame.admission_pin]
            assert pin_row.state == "active" and pin_row.target_frame_ref is frame
            assert source.lock._is_owned() and record.lock._is_owned()
            return function(frame)

        return entered

    record.ops = m._AcquisitionOps(
        *(
            wrapper(function)
            for function in (sdk.open, sdk.close, sdk.locate, sdk.descriptor)
        )
    )
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    descriptor = m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    assert m._close_acquisition(owner, item).state == "closed"
    assert reached == ["locate", "open_anchor", "descriptor", "close"]
    assert source.pin_slots_reserved == 4 and len(source.pins) == 4
    assert all(row.state == "completed" for row in source.pins.values())
    assert source.counters["observations"] == observations_before + 8
    assert not source.lock._is_owned() and record.inflight == []
    assert record.descriptors[descriptor].state is m._AuxiliaryState.LIVE


@pytest.mark.parametrize("operation", ["locate", "open", "descriptor", "close"])
def test_cpu_pin_pipeline_single_boundary_is_causal(operation):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    _token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    observed_before = source.counters["observations"]
    reached = []

    def entered(frame):
        reached.append(frame)
        assert type(frame.admission_pin) is m._CpuAdmissionPin
        assert (
            source.pins[frame.admission_pin].state == "active"
            and source.lock._is_owned()
        )
        return getattr(sdk, operation)(frame)

    values = {
        name: getattr(sdk, name) for name in ("open", "close", "locate", "descriptor")
    }
    values[operation] = entered
    record.ops = m._AcquisitionOps(**values)
    try:
        if operation == "locate":
            m._locate_anchor(owner, project_location="C:\\studio")
        elif operation == "open":
            m._open_owned_anchor(owner, locator)
        elif operation == "descriptor":
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        else:
            assert m._close_acquisition(owner, item).state == "closed"
    except m.AcquisitionError:
        print(
            "CPU callback reached:",
            bool(reached),
            "custody error:",
            repr(record.inflight[-1].error),
        )
        raise
    assert (
        reached
        and source.pin_slots_reserved == 1
        and source.counters["observations"] == observed_before + 2
    )
    assert (
        all(row.state == "completed" for row in source.pins.values())
        and not source.lock._is_owned()
    )


def test_known_owner_close_compacts_metadata_backings_without_retaining_buffers():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    descriptor = m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    retained_arenas = tuple(record.backings)
    assert sdk.calls == ["locate", "descriptor"]
    assert m._close_acquisition_owner(owner).state == "closed"
    assert record.locators[locator].arena_refs == ()
    assert (
        record.locators[locator].root_dos
        == record.locators[locator].guid
        == record.locators[locator].target
        == record.locators[locator].nt_name
        == ""
    )
    assert (
        record.descriptors[descriptor].arena is None
        and record.descriptors[descriptor].getter_outputs == ()
    )
    assert record.backings == [] and record.ops is None and record.control is None
    assert all(
        arena.state is m._AuxiliaryState.CLOSED
        and arena.storage == bytearray()
        and arena.overlay is None
        and arena.native_base == 0
        for arena in retained_arenas
    )


@pytest.mark.parametrize(
    "fault,code",
    [
        ("nominal", "ADMISSION_REQUIRED"),
        ("unregistered", "ADMISSION_REQUIRED"),
        ("owner_source", "CAPABILITY_INVALID"),
        ("owner_state", "CAPABILITY_INVALID"),
        ("rebind", "CAPABILITY_INVALID"),
        ("principal", "PRINCIPAL_UNACCREDITED"),
        ("primary_group", "PRINCIPAL_UNACCREDITED"),
    ],
)
def test_cpu_binding_guard_is_causal_with_live_cpu_registry(fault, code):
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    _source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    assert token_sdk.calls
    with m._owner_pin_boundary(owner):
        if fault == "nominal":
            admission = object()
        elif fault == "unregistered":
            admission = object.__new__(identity._CpuAdmission)
        elif fault == "owner_source":
            record.source = "unknown"
        elif fault == "owner_state":
            record.state = m._OwnerState.REVOKED
        elif fault == "rebind":
            identity._bind_cpu_acquisition_owner(admission, owner=owner)
        elif fault == "principal":
            record.principal_sid = bytes.fromhex("010100000000000512000000")
        else:
            record.primary_group_sid = bytes.fromhex("010100000000000512000000")
        calls_before = tuple(token_sdk.calls)
        with pytest.raises(identity.IdentityError, match=code):
            identity._bind_cpu_acquisition_owner(admission, owner=owner)
        assert tuple(token_sdk.calls) == calls_before and sdk.calls == []


@pytest.mark.parametrize("operation", ["locate", "open", "descriptor", "writer_scope"])
def test_bound_admission_precheck_is_public_and_before_reservation(operation):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    _token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    calls_before = tuple(sdk.calls)
    accounting_before = (
        record.handles,
        record.next_slot,
        tuple(record.backings),
        source.pin_slots_reserved,
    )
    if operation != "writer_scope":
        source.state = "revoked"
    with pytest.raises(
        m.AcquisitionError,
        match="ADMISSION_REQUIRED"
        if operation == "writer_scope"
        else "CAPABILITY_REVOKED",
    ):
        if operation == "locate":
            m._locate_anchor(owner, project_location="C:\\studio")
        elif operation == "descriptor":
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        elif operation == "open":
            m._open_owned_anchor(owner, locator)
        else:
            m._open_owned_component(
                owner,
                parent,
                "child",
                m._AcquireProfile.WRITER_EXISTING,
                m._Disposition.OPEN_EXISTING,
            )
    assert tuple(sdk.calls) == calls_before
    assert accounting_before == (
        record.handles,
        record.next_slot,
        tuple(record.backings),
        source.pin_slots_reserved,
    )
    assert record.inflight == [] and not m._io._KERNEL_POISONED


@pytest.mark.parametrize(
    "fault,code",
    [
        ("pins", "OWNER_RETIRE_REQUIRED"),
        ("observations", "OWNER_RETIRE_REQUIRED"),
        ("subcalls", "OWNER_RETIRE_REQUIRED"),
        ("pins_bool", "OWNER_RETIRE_REQUIRED"),
        ("observations_bool", "OWNER_RETIRE_REQUIRED"),
        ("owner_binding", "CAPABILITY_INVALID"),
        ("policy", "CAPABILITY_INVALID"),
        ("epoch", "CAPABILITY_INVALID"),
    ],
)
def test_bound_owner_pin_quota_and_binding_fail_before_metadata_reservation(
    fault, code
):
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    if fault == "pins":
        source.pin_slots_reserved = 2048
    elif fault == "observations":
        source.counters["observations"] = 8191
    elif fault == "subcalls":
        source.counters["subcalls"] = 229376 - 55
    elif fault == "pins_bool":
        source.pin_slots_reserved = True
    elif fault == "observations_bool":
        source.counters["observations"] = True
    elif fault == "owner_binding":
        source.owner_refs.pop(owner)
    elif fault == "policy":
        record.policy_ref = object()
    else:
        record.epoch_ref = object()
    accounting_before = tuple(record.backings), record.handles, record.next_slot
    before = tuple(token_sdk.calls)
    with pytest.raises(m.AcquisitionError, match=code):
        m._locate_anchor(owner, project_location="C:\\studio")
    assert (
        tuple(record.backings),
        record.handles,
        record.next_slot,
    ) == accounting_before
    assert (
        record.inflight == [] and sdk.calls == [] and tuple(token_sdk.calls) == before
    )


@pytest.mark.parametrize(
    "fault",
    [
        "offset_bool",
        "length_bool",
        "negative",
        "tail",
        "overflow",
        "empty_length",
        "ranges_list",
        "args_list",
        "function_string",
        "function_other_operation",
        "overlap",
        "capture_error_flag",
    ],
)
def test_ast_sdk_subcall_guard_limits_own_ranges_before_cpu_sdk_callback(fault):
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, source_sha, node_sha = cpu_handler(abi, "_sdk_call")
    print("CPU-AST source/node SHA:", source_sha, node_sha)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    sdk_callbacks = []
    reached = []

    def entered(frame):
        result = sdk.open(frame)
        reached.append(frame)
        print("CPU ownership callback reached before SDK range predicate")
        control = record.control
        ranges = (
            (control, frame.slot_index * 8, 8),
            (control, 2048 + frame.slot_index * 16, 16),
        )
        args = tuple(range(11))
        name = m._SdkFunction.NT_CREATE_FILE
        if fault == "offset_bool":
            ranges = ((control, True, 8),)
        elif fault == "length_bool":
            ranges = ((control, 0, True),)
        elif fault == "negative":
            ranges = ((control, -1, 8),)
        elif fault == "tail":
            ranges = ((control, control.logical_length, 1),)
        elif fault == "overflow":
            ranges = ((control, 2**64, 8),)
        elif fault == "empty_length":
            ranges = ((control, 0, 0),)
        elif fault == "ranges_list":
            ranges = list(ranges)
        elif fault == "args_list":
            args = list(args)
        elif fault == "function_string":
            name = "NtCreateFile"
        elif fault == "function_other_operation":
            name = m._SdkFunction.CLOSE_HANDLE
        elif fault == "overlap":
            ranges = ((control, 0, 8), (control, 4, 8))

        def closed_cpu_sdk(*values):
            sdk_callbacks.append(values)
            return 0

        with pytest.raises(RuntimeError, match="CAPABILITY_INVALID"):
            handler(
                types.SimpleNamespace(get_last_error=lambda: 5),
                closed_cpu_sdk,
                frame,
                name,
                args,
                ranges,
                capture_error=1 if fault == "capture_error_flag" else False,
            )
        assert sdk_callbacks == []
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)
    assert (
        reached
        and len(source_sha) == len(node_sha) == 64
        and sdk.calls == ["locate", "open"]
    )


@pytest.mark.parametrize("operation", ["locate", "open", "descriptor"])
@pytest.mark.parametrize("cut", ["principal_change", "query_unknown"])
def test_bound_prequery_failure_maps_public_error_and_preserves_exact_custody(
    operation, cut
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    before_backings = tuple(record.backings)
    before_calls = tuple(sdk.calls)
    reached = []
    if cut == "principal_change":
        token_sdk.stamp = (4, 5, 6)
    else:

        def interrupted(call):
            result = token_sdk.execute(call)
            if call.function == "OpenProcessToken":
                reached.append(call)
                raise KeyboardInterrupt("private-prequery-cut")
            return result

        source.ops = identity._CpuIdentityOps(interrupted)
    with pytest.raises(
        m.AcquisitionError,
        match="PRINCIPAL_UNACCREDITED"
        if cut == "principal_change"
        else "RESOURCE_UNKNOWN",
    ):
        if operation == "locate":
            m._locate_anchor(owner, project_location="C:\\studio")
        elif operation == "open":
            m._open_owned_anchor(owner, locator)
        else:
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    assert tuple(sdk.calls) == before_calls
    if cut == "principal_change":
        assert tuple(record.backings) == before_backings and record.inflight == []
        assert (
            record.handles == 0
            and not source.lock._is_owned()
            and not m._io._KERNEL_POISONED
        )
        assert all(pin.state == "revoked" for pin in source.pins.values())
    else:
        assert reached and record.inflight and record.state is m._OwnerState.UNKNOWN
        assert (
            source.state == "unknown"
            and m._io._KERNEL_POISONED
            and source.lock._is_owned()
        )
        assert record.inflight[0].frame.admission_pin in source.pins
        assert len(record.backings) > len(before_backings)


def test_known_principal_rejection_before_close_retains_known_handle_without_sdk_or_poison():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    control = record.control
    raw_before = bytes(control.storage)
    token_sdk.stamp = (4, 5, 6)
    outcome = m._close_acquisition(owner, item)
    assert outcome.state == "unknown" and sdk.calls.count("close") == 0
    assert (
        record.handles == 1
        and record.control is control
        and bytes(control.storage) == raw_before
    )
    assert record.state is m._OwnerState.REVOKED and not m._io._KERNEL_POISONED
    assert record.inflight[0].frame.phase is m._CallPhase.RESERVED
    assert record.acquisitions[item].native_close_attempted is False
    assert not source.lock._is_owned() and all(
        pin.state == "revoked" for pin in source.pins.values()
    )
    assert m._close_acquisition(owner, item) is outcome


def test_known_postquery_principal_change_retains_returned_output_without_trust_or_retry():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    reached = []

    def entered(frame):
        result = sdk.open(frame)
        reached.append(frame)
        token_sdk.stamp = (4, 5, 6)
        return result

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(m.AcquisitionError, match="PRINCIPAL_UNACCREDITED"):
        m._open_owned_anchor(owner, locator)
    assert (
        reached and record.state is m._OwnerState.REVOKED and not m._io._KERNEL_POISONED
    )
    call = record.inflight[0]
    assert (
        type(call.return_value) is m._NativeCreateCompletion
        and call.return_value.return_status == 0
    )
    assert call.frame.phase is m._CallPhase.RETURNED and record.handles == 1
    assert (
        struct.unpack_from("<Q", record.control.storage, call.frame.slot_index * 8)[0]
        != 0
    )
    assert (
        all(pin.state == "revoked" for pin in source.pins.values())
        and not source.lock._is_owned()
    )
    assert sdk.calls == ["locate", "open"]


@pytest.mark.parametrize(
    "target_text",
    [
        "record.next_slot += 1",
        "record.handles += 1",
        "record.acquisitions[acquisition] = row",
        'struct.pack_into("<Q", record.control.storage',
        "frame = _AcquisitionCallFrame(",
    ],
    ids=["slot", "handle", "registry", "output", "frame"],
)
def test_acquisition_a1_a2_cut_has_preregistered_frame_before_entry(target_text):
    import inspect

    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    function = getattr(m, "_open_registered", m._open)
    lines, start = inspect.getsourcelines(function)
    if target_text == "frame = _AcquisitionCallFrame(" and any(
        "frame.slot_index = slot" in line for line in lines
    ):
        target_text = "frame.slot_index = slot"
    target = start + next(i for i, text in enumerate(lines) if target_text in text)
    cause = KeyboardInterrupt("private-reservation-cut")
    reached = []

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is function.__code__
            and frame.f_lineno == target
        ):
            reached.append(frame)
            raise cause
        return cut

    prior = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(BaseException) as caught:
            m._open_owned_anchor(owner, locator)
    finally:
        sys.settrace(prior)
    assert reached and sdk.calls == ["locate"]
    assert (
        type(caught.value) is m.AcquisitionError
        and str(caught.value) == "RESOURCE_UNKNOWN/open_anchor"
    )
    assert record.state is m._OwnerState.UNKNOWN and m._io._KERNEL_POISONED
    assert len(record.inflight) == 1 and record.inflight[0].error is cause
    assert type(record.inflight[0].frame) is m._AcquisitionCallFrame
    assert (
        record.inflight[0].frame.owner_ref is owner
        and record.inflight[0].frame.phase is m._CallPhase.UNKNOWN
    )


def test_a6_recognition_builds_frozen_info_before_candidate_publication():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    snapshot = record.acquisitions[item].info_snapshot
    assert type(snapshot) is m.AcquisitionInfo and snapshot.state == "candidate"
    assert m._acquisition_info(owner, item) is snapshot and sdk.calls == [
        "locate",
        "open",
    ]


@pytest.mark.parametrize(
    "cut,cleanup",
    [
        ("memory", "known"),
        ("memory", "unknown"),
        ("runtime", "known"),
        ("runtime", "unknown"),
        ("interrupt", "unused"),
    ],
)
def test_a6_owned_registration_failure_rolls_back_only_accredited_completion(
    monkeypatch, cut, cleanup
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    cause = {
        "memory": MemoryError,
        "runtime": RuntimeError,
        "interrupt": KeyboardInterrupt,
    }[cut]("private-registration-error")
    reached = []

    def allocation(*args, **kwargs):
        reached.append(args)
        assert sdk.calls == ["locate", "open"]
        assert record.inflight[0].frame.phase is m._CallPhase.COMPLETED
        raise cause

    monkeypatch.setattr(m, "AcquisitionInfo", allocation)
    if cleanup == "unknown":

        def close_failure(frame):
            sdk.calls.append("close")
            struct.pack_into(
                "<i", record.control.storage, 7168 + frame.slot_index * 4, 0
            )
            struct.pack_into(
                "<I", record.control.storage, 8192 + frame.slot_index * 4, 5
            )
            return m._NativeCloseCompletion(False, 5)

        record.ops = m._AcquisitionOps(
            sdk.open, close_failure, sdk.locate, sdk.descriptor
        )
    with pytest.raises(
        m.AcquisitionError,
        match="OPEN_FAILED" if cut in {"memory", "runtime"} else "RESOURCE_UNKNOWN",
    ) as captured:
        m._open_owned_anchor(owner, locator)
    assert reached and sdk.calls.count("close") == (
        1 if cut in {"memory", "runtime"} else 0
    )
    if cleanup == "known":
        assert (
            captured.value.cleanup is None
            and record.handles == 0
            and record.inflight == []
        )
        assert record.state is m._OwnerState.LIVE and not m._io._KERNEL_POISONED
        assert (
            len(record.backings) == 2
            and next(iter(record.acquisitions.values())).state
            is m._AcquisitionState.CLOSED
        )
    elif cleanup == "unknown":
        assert captured.value.cleanup.state == "unknown" and m._io._KERNEL_POISONED
        assert record.handles == 1 and record.inflight and len(record.backings) == 3
    else:
        assert (
            record.handles == 1
            and record.inflight[0].error is cause
            and m._io._KERNEL_POISONED
        )


def test_ast_descriptor_sdk_foreign_typed_failure_cannot_claim_known_cleanup():
    import ctypes as c

    m, sdk, owner = assembly()
    abi_module = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, source_sha, node_sha = cpu_handler(
        abi_module, "_execute_acquisition_descriptor"
    )
    print("CPU-AST source/node SHA:", source_sha, node_sha)
    abi = abi_module._build_acquisition_abi(c)
    ctypes_fixture = types.SimpleNamespace(
        **{name: getattr(c, name) for name in dir(c) if not name.startswith("__")}
    )
    ctypes_fixture.get_last_error = lambda: 5
    descriptor_sdk = DescriptorSdk(c, abi, None)
    functions = descriptor_sdk.functions()
    cause = abi_module._SdkKnownFailure(5)
    reached = []

    def foreign(*args):
        functions_original(*args)
        reached.append(args)
        raise cause

    functions_original = functions["InitializeAcl"]
    functions["InitializeAcl"] = foreign
    record = m._LIVE_ACQUISITION_OWNERS[owner]

    def entered(frame):
        sdk.calls.append("descriptor")
        return handler(ctypes_fixture, functions, frame)

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, sdk.locate, entered)
    with pytest.raises(m.AcquisitionError, match="RESOURCE_UNKNOWN"):
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    assert reached and record.inflight[0].error is cause and m._io._KERNEL_POISONED
    assert record.inflight[0].subcalls[-1].error is cause and len(record.backings) == 2


@pytest.mark.parametrize(
    "fault",
    [
        "signed_high",
        "signed_low",
        "last_error_bool",
        "last_error_negative",
        "last_error_overflow",
    ],
)
def test_ast_sdk_scalar_width_and_last_error_types_retain_raw_on_unknown(fault):
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, source_sha, node_sha = cpu_handler(abi, "_sdk_call")
    print("CPU-AST source/node SHA:", source_sha, node_sha)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    reached = []

    def entered(frame):
        original = sdk.open(frame)
        scalar = {"signed_high": 2**31, "signed_low": -(2**31) - 1}.get(fault, 0)
        error = {
            "last_error_bool": True,
            "last_error_negative": -1,
            "last_error_overflow": 2**32,
        }.get(fault, 5)

        def closed_cpu_sdk(*values):
            reached.append(values)
            return scalar

        fixture = types.SimpleNamespace(get_last_error=lambda: error)
        with pytest.raises(RuntimeError, match="RESOURCE_UNKNOWN"):
            handler(
                fixture,
                closed_cpu_sdk,
                frame,
                m._SdkFunction.NT_CREATE_FILE,
                tuple(range(11)),
                ((record.control, 0, 8),),
                capture_error=fault.startswith("last_error"),
            )
        step = record.inflight[0].subcalls[-1]
        assert (
            reached
            and step.return_scalar == scalar
            and step.phase is m._CallPhase.UNKNOWN
        )
        assert type(step.error) is RuntimeError
        if fault.startswith("last_error"):
            assert step.win32_error is error
        return original

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    m._open_owned_anchor(owner, locator)


@pytest.mark.parametrize("name", ["DRIVE_TYPE", "DOS_DEVICE", "SID_LENGTH"])
@pytest.mark.parametrize("scalar", [-1, 2**32 - 1])
def test_ast_unsigned_sdk_result_uses_uint32_width(name, scalar):
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    handler, source_sha, node_sha = cpu_handler(abi, "_sdk_call")
    print("CPU-AST source/node SHA:", source_sha, node_sha)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    reached = []
    operation = "descriptor" if name == "SID_LENGTH" else "locate"

    def entered(frame):
        original = getattr(sdk, operation)(frame)

        def closed_cpu_sdk(*args):
            reached.append(args)
            return scalar

        # Prefijo CPU real a través del mismo helper: registros/ACK emitidos
        # por callbacks doubles, nunca se fabrican fases o subrecords nativos.
        prefixes = {
            "DRIVE_TYPE": ((m._SdkFunction.VOLUME_PATH, (0, 0, 32768)),),
            "DOS_DEVICE": (
                (m._SdkFunction.VOLUME_PATH, (0, 0, 32768)),
                (m._SdkFunction.DRIVE_TYPE, (0,)),
                (m._SdkFunction.VOLUME_NAME, (0, 0, 50)),
            ),
            "SID_LENGTH": (
                (m._SdkFunction.WELL_KNOWN_SID, (22, None, 0, 0)),
                (m._SdkFunction.VALID_SID, (0,)),
            ),
        }
        for prefix, prefix_args in prefixes[name]:
            assert (
                handler(
                    None,
                    lambda *args: 1,
                    frame,
                    prefix,
                    prefix_args,
                    (),
                    capture_error=False,
                )
                == 1
            )
        arguments = (0,) if name != "DOS_DEVICE" else (0, 0, 32768)
        if scalar < 0:
            with pytest.raises(RuntimeError, match="RESOURCE_UNKNOWN"):
                handler(
                    None,
                    closed_cpu_sdk,
                    frame,
                    getattr(m._SdkFunction, name),
                    arguments,
                    (),
                    capture_error=False,
                )
        else:
            assert (
                handler(
                    None,
                    closed_cpu_sdk,
                    frame,
                    getattr(m._SdkFunction, name),
                    arguments,
                    (),
                    capture_error=False,
                )
                == scalar
            )
        assert reached
        return original

    functions = {
        key: getattr(sdk, key) for key in ("open", "close", "locate", "descriptor")
    }
    functions[operation] = entered
    record.ops = m._AcquisitionOps(**functions)
    if operation == "locate":
        m._locate_anchor(owner, project_location="C:\\studio")
    else:
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)


@pytest.mark.parametrize("operation", ["locate", "open", "descriptor", "close"])
def test_known_terminal_pin_frame_releases_transient_refs_after_full_ack(operation):
    m, _sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    if operation == "locate":
        m._locate_anchor(owner, project_location="C:\\studio")
    elif operation == "open":
        m._open_owned_anchor(owner, locator)
    elif operation == "descriptor":
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    else:
        assert m._close_acquisition(owner, item).state == "closed"
    pin = next(iter(source.pins))
    frame = source.pins[pin].target_frame_ref
    assert (
        source.pins[pin].state == "completed"
        and frame.phase is m._CallPhase.ACKNOWLEDGED
    )
    assert frame.arena_refs == (record.control,)
    assert frame.project_location == "" and frame.name_bytes == b""
    assert (
        frame.locator_record is None
        and frame.descriptor_record is None
        and frame.record_ref is None
    )
    assert frame.parent_ref is None and frame.descriptor_ref is None
    before = tuple(token_sdk.calls)
    identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
    assert tuple(token_sdk.calls) == before


@pytest.mark.parametrize("fault", ["diagnostic", "cleanup"])
def test_acquisition_error_rejects_untyped_secret_payload_without_exposing_it(fault):
    m, _, _ = assembly()
    diagnostic = m.AcquisitionDiagnostic("RESOURCE_UNKNOWN", "open_anchor")
    cleanup = None
    if fault == "diagnostic":
        diagnostic = types.SimpleNamespace(
            code="private-secret-handle", operation="private-secret-path"
        )
    else:
        cleanup = types.SimpleNamespace(state="private-secret-sid")
    with pytest.raises(ValueError, match="ERROR_INVALID") as caught:
        m.AcquisitionError(diagnostic, cleanup)
    assert "private-secret" not in str(caught.value)


@pytest.mark.parametrize("stage", ["after_swap", "before_save", "before_select"])
def test_compaction_cut_restores_original_frame_graph_and_exact_backing_references(
    stage,
):
    import inspect

    m, sdk, owner = assembly()
    _token_sdk, authority, admission = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        identity._bind_cpu_acquisition_owner(admission, owner=owner)
    original_frames = []

    def entered(frame):
        result = sdk.locate(frame)
        original_frames.append(
            (
                frame,
                frame.__dict__,
                frame.arena_refs,
                tuple(bytes(arena.storage) for arena in frame.arena_refs),
            )
        )
        return result

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    lines, start = inspect.getsourcelines(m._compact_completed_pin_frames)
    target_text = (
        "for pin in source.pins.values()"
        if stage in {"after_swap", "before_select"}
        else "originals.append((frame, original))"
    )
    loop_line = start + next(
        index for index, line in enumerate(lines) if target_text in line
    )
    cause = KeyboardInterrupt("private-compaction-cut")
    visits = []

    def cut(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is m._compact_completed_pin_frames.__code__
            and frame.f_lineno == loop_line
        ):
            visits.append(frame)
            if len(visits) == (2 if stage == "after_swap" else 1):
                raise cause
        return cut

    previous = sys.gettrace()
    try:
        sys.settrace(cut)
        with pytest.raises(BaseException) as caught:
            m._locate_anchor(owner, project_location="C:\\studio")
    finally:
        sys.settrace(previous)
    actual, original, arenas, raw = original_frames[0]
    assert (
        type(caught.value) is m.AcquisitionError
        and str(caught.value) == "RESOURCE_UNKNOWN/locate"
    )
    assert actual.__dict__ is original and actual.arena_refs is arenas
    assert tuple(bytes(arena.storage) for arena in arenas) == raw
    assert record.inflight[0].frame is actual and record.inflight[0].error is cause
    assert all(any(backing is arena for backing in record.backings) for arena in arenas)
    assert record.state is m._OwnerState.UNKNOWN and m._io._KERNEL_POISONED
    assert source.pin_slots_reserved == 1 and sdk.calls == ["locate"]


def test_terminal_compaction_repetition_keeps_lifetime_charge_and_shared_control_until_owner_close():
    m, sdk, owner = assembly()
    token_sdk, authority, admission = cpu_identity_fixture(m)
    source = m._identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    control = record.control
    snapshot = bytes(control.storage)
    charge = (
        record.handles,
        record.next_slot,
        len(record.backings),
        source.pin_slots_reserved,
        source.counters["observations"],
    )
    pin = next(iter(source.pins))
    frame = source.pins[pin].target_frame_ref
    terminal_dict = frame.__dict__
    calls = tuple(token_sdk.calls)
    for _ in range(3):
        with m._owner_domain(owner, "locate"):
            pass
        m._identity._complete_cpu_acquisition_admission_pin(pin, owner=owner)
    assert frame.__dict__ is terminal_dict and frame.arena_refs == (control,)
    assert (
        bytes(control.storage) == snapshot
        and record.locators[locator].state is m._AuxiliaryState.LIVE
    )
    assert charge == (
        record.handles,
        record.next_slot,
        len(record.backings),
        source.pin_slots_reserved,
        source.counters["observations"],
    )
    assert (
        tuple(token_sdk.calls) == calls
        and len(source.pins) == 1
        and sdk.calls == ["locate"]
    )
    assert m._close_acquisition_owner(owner).state == "closed"
    assert (
        record.control is None
        and frame.arena_refs[0] is control
        and control.storage == bytearray()
    )
    assert source.pin_slots_reserved == 1 and source.pins[pin].state == "completed"


@pytest.mark.parametrize("operation", ["open", "descriptor", "close", "second_open"])
def test_cpu_sdk_outputs_at_nonzero_owned_alignment_are_recognized(operation):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    item = (
        m._open_owned_anchor(owner, locator)
        if operation in {"close", "second_open"}
        else None
    )
    reached = []

    def shift(arena, offset=3):
        logical = bytes(arena.storage[: arena.logical_length])
        arena.aligned_offset = offset
        arena.storage[offset : offset + arena.logical_length] = logical

    def opened(frame):
        print(
            "CPU registered open callback reached; writes only actual own shifted slot"
        )
        reached.append(frame)
        if operation != "second_open":
            shift(record.control)
        offset = record.control.aligned_offset
        assert (
            struct.unpack_from(
                "<Q", record.control.storage, offset + frame.slot_index * 8
            )[0]
            == 0
        )
        assert struct.unpack_from(
            "<QQ", record.control.storage, offset + 2048 + frame.slot_index * 16
        ) == (0x7FFFFFFF, 2**64 - 1)
        sdk.calls.append("open")
        struct.pack_into(
            "<Q", record.control.storage, offset + frame.slot_index * 8, sdk.next_handle
        )
        sdk.next_handle += 1
        struct.pack_into(
            "<QQ", record.control.storage, offset + 2048 + frame.slot_index * 16, 0, 1
        )
        struct.pack_into(
            "<I", record.control.storage, offset + 6144 + frame.slot_index * 4, 0
        )
        return m._NativeCreateCompletion(0, 0, 1, False)

    def descriptor(frame):
        result = sdk.descriptor(frame)
        print(
            "CPU registered descriptor callback reached; shifts actual own SD/ACL bytes"
        )
        reached.append(frame)
        shift(frame.descriptor_record.arena)
        return result

    def closed(frame):
        print(
            "CPU registered close callback reached; writes actual own shifted BOOL slot"
        )
        reached.append(frame)
        shift(record.control, 7)
        sdk.calls.append("close")
        struct.pack_into(
            "<i", record.control.storage, 7 + 7168 + frame.slot_index * 4, 1
        )
        return m._NativeCloseCompletion(True)

    if operation == "second_open":
        shift(record.control)
    record.ops = m._AcquisitionOps(opened, closed, sdk.locate, descriptor)
    if operation in {"open", "second_open"}:
        returned = m._open_owned_anchor(owner, locator)
        assert record.acquisitions[returned].state is m._AcquisitionState.CANDIDATE
        if operation == "second_open":
            assert (
                record.handles == 2
                and struct.unpack_from("<Q", record.control.storage, 3)[0] == 101
            )
    elif operation == "descriptor":
        returned = m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        assert record.descriptors[returned].state is m._AuxiliaryState.LIVE
    else:
        assert m._close_acquisition(owner, item).state == "closed"
    assert reached and record.inflight == [] and not m._io._KERNEL_POISONED


def test_nonzero_alignment_duplicate_handle_retains_actual_slots_without_second_authority():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    first = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    control = record.control
    control.storage[3 : 3 + control.logical_length] = bytes(
        control.storage[: control.logical_length]
    )
    control.aligned_offset = 3
    reached = []

    def duplicate(frame):
        print("CPU duplicate-output callback reached in actual shifted registered slot")
        reached.append(frame)
        struct.pack_into("<Q", control.storage, 3 + frame.slot_index * 8, 101)
        struct.pack_into("<QQ", control.storage, 3 + 2048 + frame.slot_index * 16, 0, 1)
        struct.pack_into("<I", control.storage, 3 + 6144 + frame.slot_index * 4, 0)
        return m._NativeCreateCompletion(0, 0, 1, False)

    record.ops = m._AcquisitionOps(duplicate, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(m.AcquisitionError, match="RESOURCE_UNKNOWN/open_anchor"):
        m._open_owned_anchor(owner, locator)
    assert reached and record.acquisitions[first].state is m._AcquisitionState.CANDIDATE
    assert record.handles == 2 and record.inflight[0].frame is reached[0]
    assert (
        struct.unpack_from("<Q", control.storage, 3)[0]
        == struct.unpack_from("<Q", control.storage, 11)[0]
        == 101
    )
    assert m._io._KERNEL_POISONED and sdk.calls == ["locate", "open"]


@pytest.mark.parametrize(
    "fault", ["known_unchanged", "known_written", "partial", "pending", "exception"]
)
def test_aligned_control_known_vs_unknown_completion_keeps_exact_original_custody(
    fault,
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    control = record.control
    control.storage[7 : 7 + control.logical_length] = bytes(
        control.storage[: control.logical_length]
    )
    control.aligned_offset = 7
    reached = []
    cause = KeyboardInterrupt("private-aligned-sdk-interruption")

    def entered(frame):
        print(
            "CPU original registered callback reached; aligned control and IOSB retained"
        )
        reached.append(frame)
        status = 0x103 if fault == "pending" else 0xC0000034
        struct.pack_into("<I", control.storage, 7 + 6144 + frame.slot_index * 4, status)
        if fault in {"known_written", "partial", "pending"}:
            struct.pack_into(
                "<QQ",
                control.storage,
                7 + 2048 + frame.slot_index * 16,
                status,
                1 if fault == "partial" else 0,
            )
        reached.append(bytes(control.storage))
        if fault == "exception":
            raise cause
        unchanged = fault == "known_unchanged"
        return m._NativeCreateCompletion(
            status,
            0x7FFFFFFF if unchanged else status,
            2**64 - 1 if unchanged else (1 if fault == "partial" else 0),
            unchanged,
        )

    record.ops = m._AcquisitionOps(entered, sdk.close, sdk.locate, sdk.descriptor)
    known = fault.startswith("known")
    with pytest.raises(
        m.AcquisitionError,
        match="NOT_FOUND/open_anchor" if known else "RESOURCE_UNKNOWN/open_anchor",
    ):
        m._open_owned_anchor(owner, locator)
    assert reached and control.storage == reached[1] and record.control is control
    if known:
        assert (
            record.handles == 0 and record.inflight == [] and not m._io._KERNEL_POISONED
        )
    else:
        call = record.inflight[0]
        assert call.frame is reached[0] and any(
            arena is control for arena in record.backings
        )
        assert (
            record.handles == 1
            and call.frame.phase is m._CallPhase.UNKNOWN
            and m._io._KERNEL_POISONED
        )
        if fault == "exception":
            assert call.error is cause


def test_cpu_parent_close_rival_waits_for_actual_child_owner_boundary_and_then_rejects_pin():
    import threading

    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    parent = m._open_owned_anchor(owner, locator)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    entered = threading.Event()
    release = threading.Event()
    rival_attempt = threading.Event()
    rival_done = threading.Event()
    results = {}

    def held_child(frame):
        assert record.lock._is_owned() and m._io._NATIVE_BOUNDARY_LOCK._is_owned()
        assert (
            record.acquisitions[parent].child_pins == 1
            and record.inflight[0].frame is frame
        )
        result = sdk.open(frame)
        print(
            "CPU child backend reached while actual owner/boundary locks held; parent pin visible"
        )
        entered.set()
        assert release.wait(5)
        return result

    record.ops = m._AcquisitionOps(held_child, sdk.close, sdk.locate, sdk.descriptor)

    def open_child():
        try:
            results["child"] = m._open_owned_component(
                owner,
                parent,
                "journal",
                m._AcquireProfile.READ_EXISTING,
                m._Disposition.OPEN_EXISTING,
                None,
            )
        except BaseException as error:  # noqa: BLE001 - preserva causa fuerte del thread CPU
            results["open_error"] = error

    def rival_close():
        rival_attempt.set()
        try:
            results["close"] = m._close_acquisition(owner, parent)
        except BaseException as error:  # noqa: BLE001 - preserva causa fuerte del thread CPU
            results["close_error"] = error
        finally:
            rival_done.set()

    opener = threading.Thread(target=open_child)
    rival = threading.Thread(target=rival_close)
    opener.start()
    try:
        assert entered.wait(5)
        rival.start()
        assert rival_attempt.wait(5) and not rival_done.wait(0.05)
        assert sdk.calls == ["locate", "open", "open"]
    finally:
        release.set()
        opener.join(5)
        if rival.ident is not None:
            rival.join(5)
    assert (
        not opener.is_alive() and not rival.is_alive() and "open_error" not in results
    )
    error = results["close_error"]
    assert type(error) is m.AcquisitionError and str(error) == "CAPABILITY_IN_USE/close"
    assert (
        record.acquisitions[parent].child_pins == 1
        and not record.acquisitions[parent].native_close_attempted
    )
    assert m._close_acquisition(owner, results["child"]).state == "closed"
    assert m._close_acquisition(owner, parent).state == "closed"
    assert (
        sdk.calls == ["locate", "open", "open", "close", "close"]
        and not m._io._KERNEL_POISONED
    )


def test_cpu_close_post_principal_change_retains_true_output_unknown_charge_and_never_retries():
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator)
    token_sdk, authority, admission = cpu_identity_fixture(m)
    source = m._identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    reached = []

    def closed(frame):
        result = sdk.close(frame)
        print(
            "CPU CloseTRUE callback reached before genuine CPU post-observation principal change"
        )
        reached.append(frame)
        token_sdk.stamp = (4, 5, 6)
        return result

    record.ops = m._AcquisitionOps(sdk.open, closed, sdk.locate, sdk.descriptor)
    outcome = m._close_acquisition(owner, item)
    call = record.inflight[0]
    assert (
        reached and outcome.state == "unknown" and record.state is m._OwnerState.UNKNOWN
    )
    assert call.frame is reached[0] and call.frame.phase is m._CallPhase.UNKNOWN
    assert (
        type(call.return_value) is m._NativeCloseCompletion
        and call.return_value.success is True
    )
    assert struct.unpack_from("<i", record.control.storage, 7168)[0] == 1
    assert (
        record.handles == 1
        and record.acquisitions[item].native_close_attempted
        and m._io._KERNEL_POISONED
    )
    assert (
        call.error is call.recognized_error
        and type(call.error.__context__) is m._identity.IdentityError
    )
    assert (
        source.pin_slots_reserved == 1
        and all(pin.state == "revoked" for pin in source.pins.values())
        and not source.lock._is_owned()
    )
    calls_before = tuple(token_sdk.calls)
    assert m._close_acquisition(owner, item) is outcome
    assert (
        m._close_acquisition_owner(owner).state == "unknown"
        and record.control is not None
    )
    assert (
        sdk.calls == ["locate", "open", "close"]
        and tuple(token_sdk.calls) == calls_before
    )


@pytest.mark.parametrize(
    "name,arity",
    [
        ("NT_CREATE_FILE", 11),
        ("CLOSE_HANDLE", 1),
        ("VOLUME_PATH", 3),
        ("VOLUME_NAME", 3),
        ("DOS_DEVICE", 3),
        ("DRIVE_TYPE", 1),
        ("WELL_KNOWN_SID", 4),
        ("VALID_SID", 1),
        ("SID_LENGTH", 1),
        ("INITIALIZE_SD", 2),
        ("INITIALIZE_ACL", 3),
        ("ADD_ACE", 4),
        ("SET_OWNER", 3),
        ("SET_GROUP", 3),
        ("SET_DACL", 4),
        ("SET_CONTROL", 3),
        ("VALID_SD", 1),
        ("GET_CONTROL", 3),
        ("GET_OWNER", 3),
        ("GET_GROUP", 3),
        ("GET_DACL", 4),
    ],
)
def test_ast_sdk_closed_signature_arity_rejects_before_any_sdk_callback(name, arity):
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    helper, source_sha, node_sha = cpu_handler(abi, "_sdk_call")
    print("CPU-AST source/node SHA:", source_sha, node_sha)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    entered = []
    callbacks = []
    operation = (
        "open"
        if name == "NT_CREATE_FILE"
        else "close"
        if name == "CLOSE_HANDLE"
        else "locate"
        if name in {"VOLUME_PATH", "VOLUME_NAME", "DOS_DEVICE", "DRIVE_TYPE"}
        else "descriptor"
    )
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    item = m._open_owned_anchor(owner, locator) if operation == "close" else None

    def reached(frame):
        completion = getattr(sdk, operation)(frame)
        print(
            "Actual CPU ownership dispatch reached before closed arity predicate:", name
        )
        entered.append(frame)

        def cpu_sdk(*args):
            callbacks.append(args)
            return 1

        with pytest.raises(RuntimeError, match="CAPABILITY_INVALID"):
            helper(
                None,
                cpu_sdk,
                frame,
                getattr(m._SdkFunction, name),
                (0,) * (arity - 1),
                (),
                capture_error=False,
            )
        assert callbacks == []
        return completion

    functions = {
        key: getattr(sdk, key) for key in ("open", "close", "locate", "descriptor")
    }
    functions[operation] = reached
    record.ops = m._AcquisitionOps(**functions)
    if operation == "locate":
        m._locate_anchor(owner, project_location="C:\\studio")
    elif operation == "descriptor":
        m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
    elif operation == "open":
        m._open_owned_anchor(owner, locator)
    else:
        assert m._close_acquisition(owner, item).state == "closed"
    assert entered and callbacks == []


@pytest.mark.parametrize(
    "fault",
    [
        "locator_first",
        "descriptor_first",
        "extra_open",
        "prior_unknown",
        "ordinal_bool",
        "ordinal_index",
        "prior_function",
        "prior_error",
    ],
)
def test_ast_sdk_closed_ordinal_plan_rejects_next_entry_causally(fault):
    m, sdk, owner = assembly()
    abi = importlib.import_module(m.__package__ + ".storage_journal_windows_abi")
    helper, source_sha, node_sha = cpu_handler(abi, "_sdk_call")
    print("CPU-AST source/node SHA:", source_sha, node_sha)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    history_fault = fault in {
        "prior_unknown",
        "ordinal_bool",
        "ordinal_index",
        "prior_function",
        "prior_error",
    }
    operation = (
        "locate"
        if fault == "locator_first" or history_fault
        else "descriptor"
        if fault == "descriptor_first"
        else "open"
    )
    observed = []
    sdk_callbacks = []
    cause = KeyboardInterrupt("private-original-sdk-step-cut")

    def entered(frame):
        original = getattr(sdk, operation)(frame)
        observed.append(frame)
        print("Actual CPU dispatch reached before SDK ordinal plan:", fault)
        name, args = (
            (m._SdkFunction.DRIVE_TYPE, (0,))
            if operation == "locate"
            else (m._SdkFunction.GET_DACL, (0, 0, 0, 0))
            if operation == "descriptor"
            else (m._SdkFunction.NT_CREATE_FILE, (0,) * 11)
        )
        if operation == "open" or history_fault:

            def first(*values):
                if fault == "prior_unknown":
                    raise cause
                return 0

            try:
                helper(
                    None,
                    first,
                    frame,
                    m._SdkFunction.VOLUME_PATH if history_fault else name,
                    (0, 0, 32768) if history_fault else args,
                    (),
                    capture_error=False,
                )
            except KeyboardInterrupt as error:
                assert error is cause
            if fault == "ordinal_bool":
                record.inflight[0].subcalls[0].ordinal = False
            elif fault == "ordinal_index":
                record.inflight[0].subcalls[0].ordinal = 4
            elif fault == "prior_function":
                record.inflight[0].subcalls[0].function = m._SdkFunction.DRIVE_TYPE
            elif fault == "prior_error":
                record.inflight[0].subcalls[0].error = cause

        def next_sdk(*values):
            sdk_callbacks.append(values)
            return 1

        with pytest.raises(RuntimeError, match="CAPABILITY_INVALID"):
            helper(None, next_sdk, frame, name, args, (), capture_error=False)
        assert sdk_callbacks == []
        if fault == "prior_unknown":
            raise cause
        return original

    functions = {
        key: getattr(sdk, key) for key in ("open", "close", "locate", "descriptor")
    }
    functions[operation] = entered
    record.ops = m._AcquisitionOps(**functions)
    try:
        if operation == "locate":
            m._locate_anchor(owner, project_location="C:\\studio")
        elif operation == "descriptor":
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        else:
            m._open_owned_anchor(owner, locator)
    except m.AcquisitionError:
        pass
    assert observed and sdk_callbacks == []


@pytest.mark.parametrize("phase", ["pre", "post"])
def test_cpu_registered_primary_and_token_cleanup_unknown_stay_separate_in_acquisition_error(
    phase,
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    token_sdk, authority, admission = cpu_identity_fixture(m)
    source = m._identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    enabled = [phase == "pre"]
    callbacks = []

    def token_call(call):
        result = token_sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            enabled[0]
            and call.function == "GetTokenInformation"
            and step.info_class == 8
            and not step.sizing
        ):
            print(
                "Actual CPU token observation callback reached known principal rejection"
            )
            callbacks.append(call)
            struct.pack_into("<i", call.frame_ref.storage, step.offset, 2)
            token_sdk.fail = "CloseHandle"
        return result

    source.ops = m._identity._CpuIdentityOps(token_call)

    def opened(frame):
        result = sdk.open(frame)
        enabled[0] = True
        return result

    record.ops = m._AcquisitionOps(opened, sdk.close, sdk.locate, sdk.descriptor)
    with pytest.raises(m.AcquisitionError) as raised:
        m._open_owned_anchor(owner, locator)
    assert callbacks and raised.value.diagnostic.code == "PRINCIPAL_UNACCREDITED"
    assert (
        type(raised.value.cleanup) is m.AcquisitionCloseOutcome
        and raised.value.cleanup.state == "unknown"
    )
    assert raised.value.cleanup.causes[0].code == "RESOURCE_UNKNOWN"
    call = record.inflight[0]
    assert (
        call.error is source.frame.public_error
        and call.error.cleanup.state == "unknown"
    )
    assert (
        source.state == "unknown"
        and record.state is m._OwnerState.UNKNOWN
        and m._io._KERNEL_POISONED
    )
    assert (
        record.handles == 1
        and record.control is not None
        and call.frame.call_record_ref is call
    )
    assert sdk.calls == (["locate"] if phase == "pre" else ["locate", "open"])
    if phase == "post":
        assert (
            type(call.return_value) is m._NativeCreateCompletion
            and call.return_value.return_status == 0
        )


@pytest.mark.parametrize("fault", ["registered", "foreign"])
def test_ast_native_pin_except_pure_transport_uses_exact_cpu_custody_provenance(fault):
    import ast
    import copy
    import hashlib

    m, _, _ = assembly()
    token_sdk, authority, _ = cpu_identity_fixture(m)
    identity = m._identity
    source = identity._CPU_AUTHORITIES[authority]

    def rejected(call):
        result = token_sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            call.function == "GetTokenInformation"
            and step.info_class == 8
            and not step.sizing
        ):
            print(
                "Actual CPU principal observation reached before exact AST normalization"
            )
            struct.pack_into("<i", call.frame_ref.storage, step.offset, 2)
            token_sdk.fail = "CloseHandle"
        return result

    source.ops = identity._CpuIdentityOps(rejected)
    with pytest.raises(identity.IdentityError) as caught:
        identity._cpu_observe(source)
    original = caught.value
    assert source.frame.public_error is original and original.cleanup.state == "unknown"
    source_bytes = pathlib.Path(identity.__file__).read_bytes()
    tree = ast.parse(source_bytes)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_pin_current_acquisition_admission"
    )
    outer = next(node for node in function.body if isinstance(node, ast.Try))
    body = outer.handlers[0].body
    poison_index = next(
        index
        for index, node in enumerate(body)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_native_poison"
    )
    pure_tail = copy.deepcopy(body[poison_index + 1 :])
    node_sha = hashlib.sha256(
        ast.dump(ast.Module(body=pure_tail, type_ignores=[])).encode()
    ).hexdigest()
    print(
        "AST SYNTHETIC normalization only; exact source/node SHA:",
        hashlib.sha256(source_bytes).hexdigest(),
        node_sha,
    )
    wrapper = ast.parse("def pure_normalization(error, session, observed):\n    pass\n")
    wrapper.body[0].body = pure_tail
    namespace = dict(vars(identity))
    exec(  # noqa: S102 - ROOT autoriza tail puro; sin Native grants/frames/SDK/cobertura original
        compile(
            ast.fix_missing_locations(wrapper),
            "<CPU-SYNTHETIC-native-except-" + node_sha + ">",
            "exec",
        ),
        namespace,
    )
    error = (
        original
        if fault == "registered"
        else identity.IdentityError(
            identity.IdentityDiagnostic("PRINCIPAL_UNACCREDITED", "query"),
            original.cleanup,
        )
    )
    with pytest.raises(identity.IdentityError) as normalized:
        namespace["pure_normalization"](
            error, source, types.SimpleNamespace(frame_ref=source.frame)
        )
    if fault == "registered":
        assert (
            normalized.value.diagnostic.code == "PRINCIPAL_UNACCREDITED"
            and normalized.value.cleanup is original.cleanup
        )
    else:
        assert (
            normalized.value.diagnostic.code == "RESOURCE_UNKNOWN"
            and normalized.value.cleanup is None
        )
    assert (
        source.frame.public_error is original
        and source.state == "unknown"
        and m._io._KERNEL_POISONED
    )


def test_cpu_synthetic_wrapped_transport_keeps_original_registered_primary_and_cleanup():
    m, sdk, owner = assembly()
    token_sdk, authority, _ = cpu_identity_fixture(m)
    source = m._identity._CPU_AUTHORITIES[authority]
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    reached = []

    def rejected(call):
        result = token_sdk.execute(call)
        step = call.frame_ref.plan[call.ordinal]
        if (
            call.function == "GetTokenInformation"
            and step.info_class == 8
            and not step.sizing
        ):
            struct.pack_into("<i", call.frame_ref.storage, step.offset, 2)
            token_sdk.fail = "CloseHandle"
        return result

    source.ops = m._identity._CpuIdentityOps(rejected)

    def entered(frame):
        sdk.locate(frame)
        reached.append(frame)
        print(
            "CPU registered dispatch reached; synthetic diagnostic-only wrapped transport"
        )
        try:
            m._identity._cpu_observe(source)
        except m._identity.IdentityError as original:
            assert (
                source.frame.public_error is original
                and original.cleanup.state == "unknown"
            )
            try:
                m._identity._fail(
                    original.diagnostic.code, "pin", cleanup=original.cleanup
                )
            except m._identity.IdentityError as wrapped:
                assert wrapped.__context__ is original
                call = record.inflight[0]
                with pytest.raises(
                    m.AcquisitionError, match="PRINCIPAL_UNACCREDITED"
                ) as mapped:
                    m._preserve_admission_cleanup_failure(record, call, source, wrapped)
                assert (
                    call.error is original and mapped.value.cleanup.state == "unknown"
                )
                raise mapped.value
        raise AssertionError("CPU_PRIMARY_NOT_REJECTED")

    record.ops = m._AcquisitionOps(sdk.open, sdk.close, entered, sdk.descriptor)
    with pytest.raises(m.AcquisitionError, match="PRINCIPAL_UNACCREDITED"):
        m._locate_anchor(owner, project_location="C:\\studio")
    assert reached and record.state is m._OwnerState.UNKNOWN and m._io._KERNEL_POISONED


@pytest.mark.parametrize("operation", ["locate", "descriptor"])
@pytest.mark.parametrize("phase", ["entry", "rejected_post"])
def test_auxiliary_record_is_unpublished_building_then_live_or_revoked(
    operation, phase
):
    m, sdk, owner = assembly()
    token_sdk, _authority, admission = cpu_identity_fixture(m)
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    with m._owner_pin_boundary(owner):
        m._identity._bind_cpu_acquisition_owner(admission, owner=owner)
    reached = []

    def entered(frame):
        row = frame.locator_record if operation == "locate" else frame.descriptor_record
        reached.append(row)
        print(
            "Actual CPU metadata callback reached with preregistered unpublished record:",
            operation,
        )
        if phase == "entry":
            assert row.state.value == "building"
        completion = getattr(sdk, operation)(frame)
        if phase == "rejected_post":
            token_sdk.stamp = (4, 5, 6)
        return completion

    functions = {
        key: getattr(sdk, key) for key in ("open", "close", "locate", "descriptor")
    }
    functions[operation] = entered
    record.ops = m._AcquisitionOps(**functions)
    if phase == "entry":
        if operation == "locate":
            m._locate_anchor(owner, project_location="C:\\studio")
        else:
            m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        assert reached[0].state.value == "live"
    else:
        with pytest.raises(m.AcquisitionError, match="PRINCIPAL_UNACCREDITED"):
            if operation == "locate":
                m._locate_anchor(owner, project_location="C:\\studio")
            else:
                m._new_closed_descriptor(owner, role=m._NewObjectRole.FILE_JOURNAL)
        assert (
            reached[0].state.value == "revoked"
            and record.inflight
            and not m._io._KERNEL_POISONED
        )


@pytest.mark.parametrize(
    "member", ["profile", "disposition", "locator_ref", "primary", "cleanup"]
)
def test_call_schema_derived_accessors_read_actual_registered_references_without_authority(
    member,
):
    m, sdk, owner = assembly()
    locator = m._locate_anchor(owner, project_location="C:\\studio")
    record = m._LIVE_ACQUISITION_OWNERS[owner]
    captured = []

    def entered(frame):
        call = record.inflight[0]
        print(
            "Actual CPU registered callback reached before derived schema accessor:",
            member,
        )
        captured.append(call)
        if member == "profile":
            assert frame.profile is frame.record_ref.profile
        elif member == "disposition":
            assert frame.disposition is frame.record_ref.disposition
        elif member == "locator_ref":
            assert frame.locator_ref is frame.locator_record.capability
            return sdk.locate(frame)
        if member in {"primary", "cleanup"}:
            status = 0xC0000034
            struct.pack_into(
                "<I", record.control.storage, 6144 + frame.slot_index * 4, status
            )
            return m._NativeCreateCompletion(status, 0x7FFFFFFF, 2**64 - 1, True)
        return sdk.open(frame)

    record.ops = m._AcquisitionOps(
        entered,
        sdk.close,
        entered if member == "locator_ref" else sdk.locate,
        sdk.descriptor,
    )
    if member in {"primary", "cleanup"}:
        with pytest.raises(m.AcquisitionError, match="NOT_FOUND") as raised:
            m._open_owned_anchor(owner, locator)
        call = captured[0]
        if member == "primary":
            assert call.primary is raised.value.diagnostic
        else:
            assert call.cleanup is raised.value.cleanup is None
    elif member == "locator_ref":
        m._locate_anchor(owner, project_location="C:\\studio")
    else:
        m._open_owned_anchor(owner, locator)
    assert captured and record.inflight == [] and not m._io._KERNEL_POISONED
