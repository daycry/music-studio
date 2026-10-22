"""Binding Windows AMD64 tardío; únicamente memoria propia invocable en K1."""

import os
import platform
import sys
from typing import ClassVar


def _build_acquisition_abi(c):
    abi = _build_abi(c)
    u8, u16, u32, pointer = c.c_uint8, c.c_uint16, c.c_uint32, c.c_void_p

    class SECURITY_DESCRIPTOR(c.Structure):
        _fields_: ClassVar[list] = [
            ("Revision", u8),
            ("Sbz1", u8),
            ("Control", u16),
            ("Owner", pointer),
            ("Group", pointer),
            ("Sacl", pointer),
            ("Dacl", pointer),
        ]

    class ACL(c.Structure):
        _fields_: ClassVar[list] = [
            ("AclRevision", u8),
            ("Sbz1", u8),
            ("AclSize", u16),
            ("AceCount", u16),
            ("Sbz2", u16),
        ]

    class ACE_HEADER(c.Structure):
        _fields_: ClassVar[list] = [("AceType", u8), ("AceFlags", u8), ("AceSize", u16)]

    class ACCESS_ALLOWED_ACE(c.Structure):
        _fields_: ClassVar[list] = [
            ("Header", ACE_HEADER),
            ("Mask", u32),
            ("SidStart", u32),
        ]

    abi.update(
        {
            "SECURITY_DESCRIPTOR": SECURITY_DESCRIPTOR,
            "ACL": ACL,
            "ACE_HEADER": ACE_HEADER,
            "ACCESS_ALLOWED_ACE": ACCESS_ALLOWED_ACE,
        }
    )
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
    if any(
        c.sizeof(abi[name]) != size
        or c.alignment(abi[name]) != alignment
        or any(
            getattr(abi[name], field).offset != offset
            for field, offset in fields.items()
        )
        for name, (size, alignment, fields) in expected.items()
    ):
        raise RuntimeError("ABI_UNACCREDITED") from None
    return abi


def _bind_acquisition_functions(c, abi, dlls):
    p, u, i, w, s = c.c_void_p, c.c_uint32, c.c_int32, c.POINTER(c.c_uint16), c.c_uint16
    definitions = {
        "ntdll": {
            "NtCreateFile": (
                (
                    c.POINTER(p),
                    u,
                    c.POINTER(abi["OBJECT_ATTRIBUTES"]),
                    c.POINTER(abi["IO_STATUS_BLOCK"]),
                    c.POINTER(c.c_int64),
                    u,
                    u,
                    u,
                    u,
                    p,
                    u,
                ),
                i,
            )
        },
        "kernel32": {
            "CloseHandle": ((p,), i),
            "GetVolumePathNameW": ((w, w, u), i),
            "GetVolumeNameForVolumeMountPointW": ((w, w, u), i),
            "QueryDosDeviceW": ((w, w, u), u),
            "GetDriveTypeW": ((w,), u),
        },
        "advapi32": {
            "CreateWellKnownSid": ((i, p, p, c.POINTER(u)), i),
            "IsValidSid": ((p,), i),
            "GetLengthSid": ((p,), u),
            "InitializeSecurityDescriptor": ((p, u), i),
            "InitializeAcl": ((p, u, u), i),
            "AddAccessAllowedAce": ((p, u, u, p), i),
            "SetSecurityDescriptorOwner": ((p, p, i), i),
            "SetSecurityDescriptorGroup": ((p, p, i), i),
            "SetSecurityDescriptorDacl": ((p, i, p, i), i),
            "SetSecurityDescriptorControl": ((p, s, s), i),
            "IsValidSecurityDescriptor": ((p,), i),
            "GetSecurityDescriptorControl": ((p, c.POINTER(s), c.POINTER(u)), i),
            "GetSecurityDescriptorOwner": ((p, c.POINTER(p), c.POINTER(i)), i),
            "GetSecurityDescriptorGroup": ((p, c.POINTER(p), c.POINTER(i)), i),
            "GetSecurityDescriptorDacl": (
                (p, c.POINTER(i), c.POINTER(p), c.POINTER(i)),
                i,
            ),
        },
    }
    return {
        name: _bind_function(dlls[dll], name, args, result)
        for dll, symbols in definitions.items()
        for name, (args, result) in symbols.items()
    }


def _new_native_acquisition_backend():
    if (
        os.name != "nt"
        or sys.platform != "win32"
        or sys.maxsize != 2**63 - 1
        or platform.machine().casefold() not in {"amd64", "x86_64"}
    ):
        raise RuntimeError("PLATFORM_UNSUPPORTED") from None
    import ctypes as c

    from . import storage_journal_windows_acquisition as acquisition

    abi = _build_acquisition_abi(c)
    functions = _bind_acquisition_functions(
        c,
        abi,
        {
            name: c.WinDLL(name, use_last_error=True)
            for name in ("ntdll", "kernel32", "advapi32")
        },
    )

    def checked(frame, operation):
        if type(frame) is not acquisition._AcquisitionCallFrame:
            raise RuntimeError("CAPABILITY_INVALID") from None
        owner = acquisition._owner_record(frame.owner_ref, frame.operation)
        if owner.source != "native_windows_x64" or owner.ops is not backend:
            raise RuntimeError("CAPABILITY_INVALID") from None
        if not _sdk_frame_owned(frame, operation, backend):
            raise RuntimeError("CAPABILITY_INVALID") from None
        acquisition._identity._validate_acquisition_backend_pin(
            frame.admission_pin, owner=frame.owner_ref, frame=frame
        )

    def open_owned(frame):
        checked(frame, "open")
        return _execute_acquisition_open(c, abi, functions, frame)

    def close_owned(frame):
        checked(frame, "close")
        return _execute_acquisition_close(c, functions, frame)

    def locate_owned(frame):
        checked(frame, "locate")
        return _execute_acquisition_locator(c, functions, frame)

    def descriptor_owned(frame):
        checked(frame, "descriptor")
        return _execute_acquisition_descriptor(c, functions, frame)

    backend = acquisition._AcquisitionOps(
        open_owned, close_owned, locate_owned, descriptor_owned
    )
    return backend


def _execute_acquisition_open(c, abi, functions, frame):
    import struct

    from . import storage_journal_windows_acquisition as acquisition

    record = acquisition._owner_record(frame.owner_ref, frame.operation)
    control = record.control
    _arena_view(c, control)
    name_arena = frame.arena_refs[-1]
    _arena_view(c, name_arena)
    segments = {segment[0]: segment for segment in name_arena.segments}
    name_offset = segments[acquisition._SegmentName.UNICODE_NAME][1]
    us_offset = segments[acquisition._SegmentName.UNICODE_STRING][1]
    oa_offset = segments[acquisition._SegmentName.OBJECT_ATTRIBUTES][1]
    name_length = segments[acquisition._SegmentName.UNICODE_NAME][2] - 2
    unicode = abi["UNICODE_STRING"].from_buffer(
        name_arena.storage, name_arena.aligned_offset + us_offset
    )
    unicode.Length = name_length
    unicode.MaximumLength = name_length + 2
    unicode.Buffer = name_arena.native_base + name_offset
    oa = abi["OBJECT_ATTRIBUTES"].from_buffer(
        name_arena.storage, name_arena.aligned_offset + oa_offset
    )
    oa.Length = 48
    oa.RootDirectory = (
        None
        if frame.parent_ref is None
        else struct.unpack_from(
            "<Q",
            control.storage,
            control.aligned_offset
            + record.acquisitions[frame.parent_ref].slot_index * 8,
        )[0]
    )
    oa.ObjectName = name_arena.native_base + us_offset
    oa.Attributes = 0x40
    oa.SecurityDescriptor = None
    oa.SecurityQualityOfService = None
    if frame.descriptor_ref is not None:
        descriptor = record.descriptors[frame.descriptor_ref].arena
        _arena_view(c, descriptor)
        oa.SecurityDescriptor = descriptor.native_base
    slot = frame.slot_index
    output = c.cast(c.c_void_p(control.native_base + slot * 8), c.POINTER(c.c_void_p))
    iosb = c.cast(
        c.c_void_p(control.native_base + 2048 + slot * 16),
        c.POINTER(abi["IO_STATUS_BLOCK"]),
    )
    preimage = bytes(
        control.storage[
            control.aligned_offset + 2048 + slot * 16 : control.aligned_offset
            + 2064
            + slot * 16
        ]
    )
    returned = _sdk_call(
        c,
        functions["NtCreateFile"],
        frame,
        acquisition._SdkFunction.NT_CREATE_FILE,
        (
            output,
            frame.access,
            c.pointer(oa),
            iosb,
            None,
            frame.file_attributes,
            frame.share,
            frame.nt_disposition,
            frame.options,
            None,
            0,
        ),
        ((control, slot * 8, 8), (control, 2048 + slot * 16, 16)),
        capture_error=False,
    )
    status = returned & 0xFFFFFFFF
    struct.pack_into(
        "<I", control.storage, control.aligned_offset + 6144 + slot * 4, status
    )
    iosb_status = iosb.contents.u.Status & 0xFFFFFFFF
    information = int(iosb.contents.Information)
    unchanged = (
        bytes(
            control.storage[
                control.aligned_offset + 2048 + slot * 16 : control.aligned_offset
                + 2064
                + slot * 16
            ]
        )
        == preimage
    )
    return acquisition._NativeCreateCompletion(
        status, iosb_status, information, unchanged
    )


def _sdk_frame_owned(frame, operation, ops):
    import threading

    from . import storage_journal_windows_acquisition as acquisition

    if type(frame) is not acquisition._AcquisitionCallFrame:
        return False
    try:
        owner = acquisition._owner_record(frame.owner_ref, frame.operation)
    except acquisition.AcquisitionError:
        return False
    if (
        owner.ops is not ops
        or not owner.lock._is_owned()
        or not acquisition._io._NATIVE_BOUNDARY_LOCK._is_owned()
    ):
        return False
    with acquisition._io._REGISTRY_LOCK:
        lease = acquisition._io._BOUNDARY_LEASES.get(frame.boundary_lease_ref)
    if type(
        frame.boundary_lease_ref
    ) is not acquisition._io._KernelBoundaryLease or lease != (
        os.getpid(),
        threading.current_thread(),
        threading.get_native_id(),
    ):
        return False
    operations = {
        "open": {"open_anchor", "open_component"},
        "close": {"close"},
        "locate": {"locate"},
        "descriptor": {"descriptor"},
    }
    if (
        frame.operation not in operations.get(operation, set())
        or frame.phase is not acquisition._CallPhase.ENTERED
    ):
        return False
    if not any(
        type(call) is acquisition._AcquisitionCallRecord and call.frame is frame
        for call in owner.inflight
    ):
        return False
    if (
        type(frame.arena_refs) is not tuple
        or not frame.arena_refs
        or frame.arena_refs[0] is not owner.control
    ):
        return False
    if owner.control.logical_length != 10240 or owner.control.requested_bytes != 10247:
        return False
    for arena in frame.arena_refs:
        if (
            type(arena) is not acquisition._CallArena
            or arena.owner_ref is not owner.capability
            or not any(backing is arena for backing in owner.backings)
            or type(arena.storage) is not bytearray
        ):
            return False
        if (
            any(
                type(v) is not int
                for v in (
                    arena.logical_length,
                    arena.requested_bytes,
                    arena.aligned_offset,
                )
            )
            or not 0 < arena.logical_length <= 131065
            or arena.requested_bytes != arena.logical_length + 7
            or len(arena.storage) != arena.requested_bytes
            or not 0 <= arena.aligned_offset <= 7
            or arena.state is not acquisition._AuxiliaryState.LIVE
        ):
            return False
    if operation in {"open", "close"}:
        slot = frame.slot_index
        if (
            type(slot) is not int
            or not 0 <= slot < 256
            or frame.record_ref is None
            or frame.record_ref.slot_index != slot
            or owner.acquisitions.get(frame.record_ref.capability)
            is not frame.record_ref
        ):
            return False
    if operation == "open":
        row = frame.record_ref
        recipe = acquisition._RECIPES.get(row.profile)
        if (
            recipe is None
            or any(
                type(v) is not int for v in (frame.access, frame.share, frame.options)
            )
            or (frame.access, frame.share, frame.options) != recipe
        ):
            return False
    return True


def _arena_view(c, arena):
    if arena.overlay is None:
        arena.overlay = (c.c_uint8 * arena.requested_bytes).from_buffer(arena.storage)
        base = c.addressof(arena.overlay)
        arena.aligned_offset = (-base) & 7
        if arena.aligned_offset:
            arena.storage[
                arena.aligned_offset : arena.aligned_offset + arena.logical_length
            ] = arena.storage[: arena.logical_length]
        arena.native_base = base + arena.aligned_offset
    return arena.overlay


def _sdk_call(c, function, frame, name, args, ranges, *, capture_error):
    from . import storage_journal_windows_acquisition as acquisition

    owner = acquisition._owner_record(frame.owner_ref, frame.operation)
    call = next(call for call in owner.inflight if call.frame is frame)
    arities = {
        acquisition._SdkFunction.NT_CREATE_FILE: 11,
        acquisition._SdkFunction.CLOSE_HANDLE: 1,
        acquisition._SdkFunction.VOLUME_PATH: 3,
        acquisition._SdkFunction.VOLUME_NAME: 3,
        acquisition._SdkFunction.DOS_DEVICE: 3,
        acquisition._SdkFunction.DRIVE_TYPE: 1,
        acquisition._SdkFunction.WELL_KNOWN_SID: 4,
        acquisition._SdkFunction.VALID_SID: 1,
        acquisition._SdkFunction.SID_LENGTH: 1,
        acquisition._SdkFunction.INITIALIZE_SD: 2,
        acquisition._SdkFunction.INITIALIZE_ACL: 3,
        acquisition._SdkFunction.ADD_ACE: 4,
        acquisition._SdkFunction.SET_OWNER: 3,
        acquisition._SdkFunction.SET_GROUP: 3,
        acquisition._SdkFunction.SET_DACL: 4,
        acquisition._SdkFunction.SET_CONTROL: 3,
        acquisition._SdkFunction.VALID_SD: 1,
        acquisition._SdkFunction.GET_CONTROL: 3,
        acquisition._SdkFunction.GET_OWNER: 3,
        acquisition._SdkFunction.GET_GROUP: 3,
        acquisition._SdkFunction.GET_DACL: 4,
    }
    permitted = {
        "open_anchor": {acquisition._SdkFunction.NT_CREATE_FILE},
        "open_component": {acquisition._SdkFunction.NT_CREATE_FILE},
        "close": {acquisition._SdkFunction.CLOSE_HANDLE},
        "locate": {
            acquisition._SdkFunction.VOLUME_PATH,
            acquisition._SdkFunction.DRIVE_TYPE,
            acquisition._SdkFunction.VOLUME_NAME,
            acquisition._SdkFunction.DOS_DEVICE,
        },
        "descriptor": set(acquisition._SdkFunction)
        - {
            acquisition._SdkFunction.NT_CREATE_FILE,
            acquisition._SdkFunction.CLOSE_HANDLE,
            acquisition._SdkFunction.VOLUME_PATH,
            acquisition._SdkFunction.DRIVE_TYPE,
            acquisition._SdkFunction.VOLUME_NAME,
            acquisition._SdkFunction.DOS_DEVICE,
        },
    }
    if (
        type(name) is not acquisition._SdkFunction
        or name not in permitted.get(frame.operation, set())
        or type(args) is not tuple
        or len(args) != arities[name]
        or type(ranges) is not tuple
        or type(capture_error) is not bool
    ):
        raise RuntimeError("CAPABILITY_INVALID")
    function_kind = acquisition._SdkFunction
    plans = {
        "open_anchor": (function_kind.NT_CREATE_FILE,),
        "open_component": (function_kind.NT_CREATE_FILE,),
        "close": (function_kind.CLOSE_HANDLE,),
        "locate": (
            function_kind.VOLUME_PATH,
            function_kind.DRIVE_TYPE,
            function_kind.VOLUME_NAME,
        )
        + (function_kind.DOS_DEVICE,) * 4,
    }
    if frame.operation == "descriptor":
        plans["descriptor"] = (
            (
                function_kind.WELL_KNOWN_SID,
                function_kind.VALID_SID,
                function_kind.SID_LENGTH,
            )
            * 2
            + (function_kind.INITIALIZE_SD, function_kind.INITIALIZE_ACL)
            + (function_kind.ADD_ACE,) * len(frame.descriptor_record.trustees)
            + (
                function_kind.SET_OWNER,
                function_kind.SET_GROUP,
                function_kind.SET_DACL,
                function_kind.SET_CONTROL,
                function_kind.VALID_SD,
                function_kind.GET_CONTROL,
                function_kind.GET_OWNER,
                function_kind.GET_GROUP,
                function_kind.GET_DACL,
            )
        )
    plan = plans[frame.operation]
    ordinal = len(call.subcalls)
    if (
        ordinal >= len(plan)
        or plan[ordinal] is not name
        or any(
            previous.phase is not acquisition._CallPhase.ACKNOWLEDGED
            or type(previous.ordinal) is not int
            or previous.ordinal != index
            or previous.function is not plan[index]
            or previous.error is not None
            for index, previous in enumerate(call.subcalls)
        )
    ):
        raise RuntimeError("CAPABILITY_INVALID")
    validated = []
    for item in ranges:
        if type(item) is not tuple or len(item) != 3:
            raise RuntimeError("CAPABILITY_INVALID")
        arena, offset, length = item
        if (
            not any(owned is arena for owned in frame.arena_refs)
            or type(arena) is not acquisition._CallArena
            or type(offset) is not int
            or type(length) is not int
            or not 0 <= offset <= arena.logical_length
            or not 0 < length <= arena.logical_length - offset
        ):
            raise RuntimeError("CAPABILITY_INVALID")
        if any(
            previous is arena
            and offset < previous_offset + previous_length
            and previous_offset < offset + length
            for previous, previous_offset, previous_length in validated
        ):
            raise RuntimeError("CAPABILITY_INVALID")
        validated.append(item)
    step = acquisition._SdkCallRecord(
        name,
        len(call.subcalls),
        acquisition._CallPhase.RESERVED,
        frame.arena_refs,
        ranges,
        tuple(
            bytes(
                arena.storage[
                    arena.aligned_offset + offset : arena.aligned_offset
                    + offset
                    + length
                ]
            )
            for arena, offset, length in ranges
        ),
        args,
    )
    call.subcalls.append(step)
    step.phase = acquisition._CallPhase.ENTERED
    try:
        result = function(*args)
        step.return_scalar = result
        if type(result) is not int:
            raise RuntimeError("RESOURCE_UNKNOWN")
        unsigned = name in {
            acquisition._SdkFunction.DRIVE_TYPE,
            acquisition._SdkFunction.DOS_DEVICE,
            acquisition._SdkFunction.SID_LENGTH,
        }
        if not (
            0 <= result <= 2**32 - 1 if unsigned else -(2**31) <= result <= 2**31 - 1
        ):
            raise RuntimeError("RESOURCE_UNKNOWN")
        if capture_error and result == 0:
            step.win32_error = c.get_last_error()
            if (
                type(step.win32_error) is not int
                or not 0 <= step.win32_error <= 2**32 - 1
            ):
                raise RuntimeError("RESOURCE_UNKNOWN")
        step.phase = acquisition._CallPhase.ACKNOWLEDGED
        return result
    except BaseException as error:
        step.error = error
        step.phase = acquisition._CallPhase.UNKNOWN
        raise


def _execute_acquisition_close(c, functions, frame):
    import struct

    from . import storage_journal_windows_acquisition as acquisition

    owner = acquisition._owner_record(frame.owner_ref, frame.operation)
    control = owner.control
    _arena_view(c, control)
    slot = frame.slot_index
    handle = struct.unpack_from(
        "<Q", control.storage, control.aligned_offset + slot * 8
    )[0]
    result = _sdk_call(
        c,
        functions["CloseHandle"],
        frame,
        acquisition._SdkFunction.CLOSE_HANDLE,
        (handle,),
        ((control, 7168 + slot * 4, 4), (control, 8192 + slot * 4, 4)),
        capture_error=True,
    )
    call = next(call for call in owner.inflight if call.frame is frame)
    error = call.subcalls[-1].win32_error
    struct.pack_into(
        "<i", control.storage, control.aligned_offset + 7168 + slot * 4, result
    )
    if error is not None:
        struct.pack_into(
            "<I", control.storage, control.aligned_offset + 8192 + slot * 4, error
        )
    return acquisition._NativeCloseCompletion(result != 0, error)


def _execute_acquisition_locator(c, functions, frame):
    import re

    from . import storage_journal_windows_acquisition as acquisition

    owner = acquisition._owner_record(frame.owner_ref, frame.operation)
    control, inputs, outputs = frame.arena_refs
    for arena in frame.arena_refs:
        _arena_view(c, arena)
    input_pointer = c.cast(c.c_void_p(inputs.native_base), c.POINTER(c.c_uint16))
    output_pointer = c.cast(c.c_void_p(outputs.native_base), c.POINTER(c.c_uint16))

    def input_text(text):
        data = text.encode("utf-16-le", "strict") + b"\0\0"
        if len(data) > inputs.logical_length:
            raise RuntimeError("RESOURCE_UNKNOWN")
        inputs.storage[inputs.aligned_offset : inputs.aligned_offset + len(data)] = data

    def output_sentinel(capacity):
        outputs.storage[
            outputs.aligned_offset : outputs.aligned_offset + capacity * 2
        ] = b"\xff" * (capacity * 2)

    def output_bytes(capacity):
        return bytes(
            outputs.storage[
                outputs.aligned_offset : outputs.aligned_offset + capacity * 2
            ]
        )

    def failure(error=None):
        return acquisition._LocatorCompletion(
            False,
            acquisition.AcquisitionDiagnostic("ANCHOR_UNACCREDITED", "locate", error),
        )

    def current_error():
        call = next(call for call in owner.inflight if call.frame is frame)
        return call.subcalls[-1].win32_error

    input_text(frame.project_location)
    output_sentinel(32768)
    returned = _sdk_call(
        c,
        functions["GetVolumePathNameW"],
        frame,
        acquisition._SdkFunction.VOLUME_PATH,
        (input_pointer, output_pointer, 32768),
        ((outputs, 0, 65536),),
        capture_error=True,
    )
    if returned == 0:
        return failure(current_error())
    try:
        root = acquisition._decode_utf16z(output_bytes(32768), 32768)
    except acquisition.AcquisitionError:
        return failure()
    if root.casefold() != frame.project_location[:3].casefold():
        return failure()
    input_text(root)
    drive = _sdk_call(
        c,
        functions["GetDriveTypeW"],
        frame,
        acquisition._SdkFunction.DRIVE_TYPE,
        (input_pointer,),
        ((control, 9572, 4),),
        capture_error=False,
    )
    if drive != 3:
        return failure()
    output_sentinel(50)
    returned = _sdk_call(
        c,
        functions["GetVolumeNameForVolumeMountPointW"],
        frame,
        acquisition._SdkFunction.VOLUME_NAME,
        (input_pointer, output_pointer, 50),
        ((outputs, 0, 100),),
        capture_error=True,
    )
    if returned == 0:
        return failure(current_error())
    try:
        guid_path = acquisition._decode_utf16z(output_bytes(50), 50)
    except acquisition.AcquisitionError:
        return failure()
    if not re.fullmatch(
        r"\\\\\?\\Volume\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}\\",
        guid_path,
    ):
        return failure()
    guid = guid_path[4:-1]
    targets = []
    for name in (root[:2], guid, root[:2], guid):
        input_text(name)
        output_sentinel(32768)
        count = _sdk_call(
            c,
            functions["QueryDosDeviceW"],
            frame,
            acquisition._SdkFunction.DOS_DEVICE,
            (input_pointer, output_pointer, 32768),
            ((outputs, 0, 65536),),
            capture_error=True,
        )
        if count == 0:
            return failure(current_error())
        try:
            target = acquisition._decode_device_multisz(output_bytes(32768), count)
        except acquisition.AcquisitionError:
            return failure()
        targets.append(target)
        if target != targets[0]:
            return failure()
    row = frame.locator_record
    row.root_dos, row.guid, row.target, row.nt_name = (
        root,
        guid,
        targets[0],
        "\\??\\" + guid + "\\",
    )
    return acquisition._LocatorCompletion(True)


def _execute_acquisition_descriptor(c, functions, frame):
    import struct

    from . import storage_journal_windows_acquisition as acquisition

    owner = acquisition._owner_record(frame.owner_ref, frame.operation)
    control, arena = frame.arena_refs
    for backing in frame.arena_refs:
        _arena_view(c, backing)
    row = frame.descriptor_record
    sd, acl = arena.native_base, arena.native_base + 40
    known_failure = None

    def pointer(offset, typ):
        return c.cast(c.c_void_p(control.native_base + offset), c.POINTER(typ))

    def failure(error=None):
        return acquisition._DescriptorCompletion(
            False,
            acquisition.AcquisitionDiagnostic(
                "DESCRIPTOR_INVALID", "descriptor", error
            ),
        )

    def step(name, args, ranges, *, predicate=False):
        nonlocal known_failure
        returned = _sdk_call(
            c,
            functions[name.value],
            frame,
            name,
            args,
            ranges,
            capture_error=not predicate,
        )
        if returned == 0:
            call = next(call for call in owner.inflight if call.frame is frame)
            error = _SdkKnownFailure(call.subcalls[-1].win32_error)
            known_failure = (error, call.subcalls[-1])
            raise error
        return returned

    try:
        well_known = (
            (22, 9352, 9496, bytes.fromhex("010100000000000512000000")),
            (26, 9420, 9500, bytes.fromhex("01020000000000052000000020020000")),
        )
        for kind, offset, length_offset, expected in well_known:
            struct.pack_into(
                "<I", control.storage, control.aligned_offset + length_offset, 68
            )
            step(
                acquisition._SdkFunction.WELL_KNOWN_SID,
                (
                    kind,
                    None,
                    control.native_base + offset,
                    pointer(length_offset, c.c_uint32),
                ),
                ((control, offset, 68), (control, length_offset, 4)),
            )
            length = struct.unpack_from(
                "<I", control.storage, control.aligned_offset + length_offset
            )[0]
            if (
                length != len(expected)
                or bytes(
                    control.storage[
                        control.aligned_offset + offset : control.aligned_offset
                        + offset
                        + length
                    ]
                )
                != expected
            ):
                raise RuntimeError("RESOURCE_UNKNOWN")
            sid_pointer = control.native_base + offset
            step(acquisition._SdkFunction.VALID_SID, (sid_pointer,), (), predicate=True)
            returned = _sdk_call(
                c,
                functions["GetLengthSid"],
                frame,
                acquisition._SdkFunction.SID_LENGTH,
                (sid_pointer,),
                ((control, 9572, 4),),
                capture_error=False,
            )
            if returned != length:
                raise RuntimeError("RESOURCE_UNKNOWN")
        step(acquisition._SdkFunction.INITIALIZE_SD, (sd, 1), ((arena, 0, 40),))
        step(
            acquisition._SdkFunction.INITIALIZE_ACL,
            (acl, row.acl_length, 2),
            ((arena, 40, row.acl_length),),
        )
        sid_offsets = {owner.principal_sid: 9216}
        for _, offset, _, sid in well_known:
            sid_offsets.setdefault(sid, offset)
        for sid in row.trustees:
            step(
                acquisition._SdkFunction.ADD_ACE,
                (acl, 2, row.mask, control.native_base + sid_offsets[sid]),
                ((arena, 40, row.acl_length),),
            )
        step(
            acquisition._SdkFunction.SET_OWNER,
            (sd, control.native_base + 9216, 0),
            ((arena, 0, 40),),
        )
        step(
            acquisition._SdkFunction.SET_GROUP,
            (sd, control.native_base + 9284, 0),
            ((arena, 0, 40),),
        )
        step(acquisition._SdkFunction.SET_DACL, (sd, 1, acl, 0), ((arena, 0, 40),))
        step(
            acquisition._SdkFunction.SET_CONTROL,
            (sd, 0x1000, 0x1000),
            ((arena, 0, 40),),
        )
        step(acquisition._SdkFunction.VALID_SD, (sd,), (), predicate=True)
        step(
            acquisition._SdkFunction.GET_CONTROL,
            (sd, pointer(9556, c.c_uint16), pointer(9560, c.c_uint32)),
            ((control, 9556, 2), (control, 9560, 4)),
        )
        step(
            acquisition._SdkFunction.GET_OWNER,
            (sd, pointer(9528, c.c_void_p), pointer(9536, c.c_int32)),
            ((control, 9528, 8), (control, 9536, 4)),
        )
        step(
            acquisition._SdkFunction.GET_GROUP,
            (sd, pointer(9544, c.c_void_p), pointer(9552, c.c_int32)),
            ((control, 9544, 8), (control, 9552, 4)),
        )
        step(
            acquisition._SdkFunction.GET_DACL,
            (
                sd,
                pointer(9504, c.c_int32),
                pointer(9512, c.c_void_p),
                pointer(9520, c.c_int32),
            ),
            ((control, 9504, 4), (control, 9512, 8), (control, 9520, 4)),
        )
    except _SdkKnownFailure as error:
        if (
            known_failure is None
            or error is not known_failure[0]
            or known_failure[1].phase is not acquisition._CallPhase.ACKNOWLEDGED
            or known_failure[1].return_scalar != 0
        ):
            raise
        return failure(error.win32_error)
    base = control.aligned_offset
    read = lambda fmt, offset: struct.unpack_from(fmt, control.storage, base + offset)[
        0
    ]
    row.getter_outputs = (
        read("<H", 9556),
        read("<I", 9560),
        read("<Q", 9528),
        read("<i", 9536) != 0,
        read("<Q", 9544),
        read("<i", 9552) != 0,
        read("<i", 9504) != 0,
        read("<Q", 9512),
        read("<i", 9520) != 0,
    )
    return acquisition._DescriptorCompletion(True)


class _SdkKnownFailure(Exception):
    def __init__(self, win32_error):
        self.win32_error = win32_error


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


def _build_identity_abi(c):
    pointer, uint, sint = c.c_void_p, c.c_uint32, c.c_int32

    class LUID(c.Structure):
        _fields_: ClassVar[list] = [("LowPart", uint), ("HighPart", sint)]

    class TOKEN_USER(c.Structure):
        _fields_: ClassVar[list] = [("Sid", pointer), ("Attributes", uint)]

    class TOKEN_PRIMARY_GROUP(c.Structure):
        _fields_: ClassVar[list] = [("PrimaryGroup", pointer)]

    class TOKEN_STATISTICS(c.Structure):
        _fields_: ClassVar[list] = [
            ("TokenId", LUID),
            ("AuthenticationId", LUID),
            ("ExpirationTime", c.c_int64),
            ("TokenType", sint),
            ("ImpersonationLevel", sint),
            ("DynamicCharged", uint),
            ("DynamicAvailable", uint),
            ("GroupCount", uint),
            ("PrivilegeCount", uint),
            ("ModifiedId", LUID),
        ]

    abi = {
        "HANDLE": pointer,
        "PVOID": pointer,
        "DWORD": uint,
        "BOOL": sint,
        "TOKEN_TYPE": sint,
        "LUID": LUID,
        "TOKEN_USER": TOKEN_USER,
        "SID_AND_ATTRIBUTES": TOKEN_USER,
        "TOKEN_PRIMARY_GROUP": TOKEN_PRIMARY_GROUP,
        "TOKEN_STATISTICS": TOKEN_STATISTICS,
    }
    layouts = {
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
    if (
        c.sizeof(pointer) != 8
        or c.sizeof(uint) != 4
        or c.sizeof(sint) != 4
        or any(
            c.sizeof(abi[n]) != size
            or c.alignment(abi[n]) != align
            or any(getattr(abi[n], f).offset != offset for f, offset in fields.items())
            for n, (size, align, fields) in layouts.items()
        )
    ):
        raise RuntimeError("ABI_UNACCREDITED") from None
    return abi


def _new_native_identity_backend():
    if not (
        os.name == "nt"
        and sys.platform == "win32"
        and sys.maxsize == 2**63 - 1
        and platform.machine().casefold() in {"amd64", "x86_64"}
    ):
        raise RuntimeError("PLATFORM_UNSUPPORTED") from None
    import ctypes as c

    from . import storage_journal_windows_identity as identity

    try:
        abi = _build_identity_abi(c)
        kernel = c.WinDLL("kernel32", use_last_error=True)
        advapi = c.WinDLL("advapi32", use_last_error=True)
        handle, uint, sint = abi["HANDLE"], abi["DWORD"], abi["BOOL"]
        signatures = {
            "GetCurrentProcess": (kernel, (), handle),
            "GetCurrentThread": (kernel, (), handle),
            "OpenThreadToken": (advapi, (handle, uint, sint, c.POINTER(handle)), sint),
            "OpenProcessToken": (advapi, (handle, uint, c.POINTER(handle)), sint),
            "GetTokenInformation": (
                advapi,
                (handle, sint, handle, uint, c.POINTER(uint)),
                sint,
            ),
            "CloseHandle": (kernel, (handle,), sint),
        }
        bindings = {
            name: _bind_function(dll, name, args, restype)
            for name, (dll, args, restype) in signatures.items()
        }
    except Exception:  # noqa: BLE001 - ninguna query antes de binding cerrado
        raise RuntimeError("ABI_UNACCREDITED") from None

    def execute(call):
        _, frame, step, address = identity._validate_native_call(call, ops)
        function = bindings[step.function]
        if step.function in {"GetCurrentProcess", "GetCurrentThread"}:
            return identity._ContextPseudoResult(function())
        if step.function == "OpenThreadToken":
            output = handle.from_address(address + step.offset)
            raw = function(frame.current_pseudo, 8, 1, c.byref(output))
        elif step.function == "OpenProcessToken":
            output = handle.from_address(address + step.offset)
            raw = function(frame.current_pseudo, 8, c.byref(output))
        elif step.function == "GetTokenInformation":
            length = uint.from_address(address + step.return_offset)
            raw = function(
                step.token,
                step.info_class,
                None if step.sizing else address + step.offset,
                step.capacity,
                c.byref(length),
            )
        else:
            raw = function(step.token)
        error = c.get_last_error() if not raw else None
        return identity._TokenBoolResult(bool(raw), error)

    ops = identity._IdentityOps(execute)
    return ops
