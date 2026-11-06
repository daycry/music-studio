"""Fixtures sintéticas de CPU: ninguna identidad concede autoridad nativa."""

import base64
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "storage_journal.py"
spec = importlib.util.spec_from_file_location("storage_journal", SOURCE)
j = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = j
spec.loader.exec_module(j)

JID = "12345678-1234-4123-8123-123456789abc"
OP = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
RID = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
ROOT = "C:/SyntheticStudio"
ZERO = "0" * 64


def canonical(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def identity(path, index, kind="directory"):
    return {"path": path, "file_id": f"{index:032x}", "volume_serial": 17, "kind": kind}


def request(action="reserve", **arguments):
    if not arguments:
        arguments = {"size_bytes": 67108864, "project_path": ROOT}
    return canonical({"action": action, "operation_id": OP, "arguments": arguments})


def request_digest(raw):
    return hashlib.sha256(
        b"MSJNL/REQUEST/v1" + struct.pack("<I", len(raw)) + raw
    ).hexdigest()


def envelope(generation=1, previous=ZERO, request_id=RID):
    receipt = canonical(
        {
            "schema_version": 1,
            "operation_id": OP,
            "phase": "reserved",
            "disk_path": ROOT + "/data/_storage/studio-data.vhdx",
            "size_bytes": 67108864,
            "history": [{"phase": "reserved", "evidence": {}}],
        }
    )
    req = request()
    chain = [
        identity("C:/", 1),
        identity(ROOT, 2),
        identity(ROOT + "/data", 3),
        identity(ROOT + "/data/_storage", 4),
    ]
    ji = identity(ROOT + "/data/_storage/storage-control.journal", 5, "file")
    return {
        "journal_version": 1,
        "generation": generation,
        "slot_index": generation - 1,
        "journal_id": JID,
        "operation_id": OP,
        "request_id": request_id,
        "request_payload_b64": base64.b64encode(req).decode(),
        "request_sha256": request_digest(req),
        "previous_commit_sha256": previous,
        "receipt_payload_b64": base64.b64encode(receipt).decode(),
        "receipt_sha256": hashlib.sha256(receipt).hexdigest(),
        "published_receipt_payload_b64": None,
        "journal_identity": ji,
        "project_identity": dict(chain[1]),
        "parent_chain": chain,
        "owned_objects": [
            {
                "role": "journal",
                "identity": dict(ji),
                "parent_identity": dict(chain[-1]),
                "name": "storage-control.journal",
                "origin": "created",
            }
        ],
        "intent": None,
        "session": {
            "epoch": 0,
            "state": "inactive",
            "admission": "closed",
            "distro": None,
            "mountpoint": None,
        },
        "result": None,
    }


def test_snapshot_exact_fresh_projection():
    value = envelope()
    raw = canonical(value)
    snapshot = j.validate_snapshot(raw)
    assert snapshot.payload == raw
    projection = snapshot.projection
    projection["parent_chain"][0]["path"] = "D:/"
    value["session"]["state"] = "unknown"
    assert snapshot.payload == raw
    assert snapshot.projection == envelope()
    with pytest.raises((AttributeError, TypeError)):
        snapshot.payload = b"changed"


def mutate(value, route, replacement):
    parent = value
    for part in route[:-1]:
        parent = parent[part]
    parent[route[-1]] = replacement
    return value


@pytest.mark.parametrize(
    "route,replacement",
    [
        (("journal_version",), True),
        (("journal_version",), 2),
        (("generation",), 0),
        (("generation",), 1.0),
        (("slot_index",), 64),
        (("slot_index",), True),
        (("generation",), 2),
        (("operation_id",), "8" + OP[1:]),
        (("request_id",), "I" + RID[1:]),
        (("journal_id",), JID.upper()),
        (("journal_id",), "12345678-1234-1123-8123-123456789abc"),
        (("request_sha256",), "f" * 64),
        (("receipt_sha256",), "f" * 64),
        (("previous_commit_sha256",), "A" * 64),
        (("request_payload_b64",), "YQ==\n"),
        (("receipt_payload_b64",), "Zh=="),
        (("journal_identity", "kind"), "directory"),
        (("project_identity", "volume_serial"), True),
        (("project_identity", "file_id"), "A" * 32),
        (("parent_chain", 0, "path"), "C:/foreign"),
        (("parent_chain", 2, "path"), ROOT + "/data/intermediate"),
        (("parent_chain", 2, "volume_serial"), 18),
        (("parent_chain", 2, "file_id"), "0" * 31 + "2"),
        (("owned_objects", 0, "name"), "wrong"),
        (("owned_objects", 0, "origin"), "adopted"),
        (("owned_objects", 0, "role"), "foreign"),
        (("owned_objects", 0, "parent_identity", "file_id"), "f" * 32),
        (
            ("intent",),
            {
                "action": "future",
                "request_id": RID,
                "previous_state": "inactive",
                "object_roles": [],
            },
        ),
        (("session", "state"), "future"),
        (("session", "epoch"), -1),
        (("session", "admission"), "open"),
        (("session", "mountpoint"), "/x/../y"),
        (("result",), {"state": "future", "code": "X", "causes": []}),
        (("unknown",), 1),
    ],
)
def test_envelope_schema_rejection(route, replacement):
    good = canonical(envelope())
    assert j.validate_snapshot(good).payload == good
    bad = canonical(mutate(envelope(), route, replacement))
    with pytest.raises(ValueError):
        j.validate_snapshot(bad)


@pytest.mark.parametrize(
    "bad",
    [
        lambda raw: raw[:-1],
        lambda raw: b"\xef\xbb\xbf" + raw,
        lambda raw: raw + b" ",
        lambda raw: raw.replace(b'"generation":1', b'"generation":NaN'),
        lambda raw: raw.replace(b'"epoch":0', b'"epoch":0,"epoch":0'),
        lambda raw: raw.replace(b'"epoch":0', b'"epoch":Infinity'),
        lambda raw: raw.replace(b'"epoch":0', b'"epoch":18446744073709551616'),
        lambda raw: raw.replace(b'"code"', b'"\\ud800"'),
        lambda raw: canonical({**envelope(), "x": [[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]}),
        lambda raw: canonical({**envelope(), "x": list(range(65))}),
        lambda raw: canonical({**envelope(), "x": "a" * 32769}),
    ],
)
def test_canonical_bounds_rejection(bad):
    good = canonical(envelope())
    assert j.validate_snapshot(good).payload == good
    value = bad(good)
    # Surrogate mutation uses a guaranteed existing key, not a no-op.
    if value == good:
        value = good.replace(b'"distro":null', b'"distro":"\\ud800"')
    with pytest.raises(ValueError):
        j.validate_snapshot(value)


@pytest.mark.parametrize(
    "path",
    [
        "C:\\x",
        "c:/x",
        "//host/share/x",
        "C:x",
        "/x",
        "C:/x//y",
        "C:/x/./y",
        "C:/x/../y",
        "C:/x/CON",
        "C:/x/NUL.txt",
        "C:/x/LPT1",
        "C:/x/foo.",
        "C:/x/foo ",
        "C:/x/ads:stream",
        "C:/x/\x00",
        "C:/x/\x1f",
        "C:/x/a?b",
        "C:/x/a*b",
        "C:/x/a|b",
        "C:/x/a<b",
    ],
)
def test_windows_path_rejection(path):
    good = canonical(envelope())
    assert j.validate_snapshot(good).payload == good
    bad = mutate(envelope(), ("journal_identity", "path"), path)
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(bad))


@pytest.mark.parametrize(
    "target",
    [
        "phase",
        "operation",
        "path",
        "history",
        "evidence",
        "size_bool",
        "version",
        "duplicate",
        "noncanonical",
    ],
)
def test_receipt_rejection(target):
    value = envelope()
    raw = base64.b64decode(value["receipt_payload_b64"])
    assert j.validate_snapshot(canonical(value)).payload == canonical(value)
    receipt = json.loads(raw)
    changes = {
        "phase": ("phase", "published"),
        "operation": ("operation_id", RID),
        "path": ("disk_path", ROOT + "/wrong.vhdx"),
        "history": ("history", []),
        "evidence": ("history", [{"phase": "reserved", "evidence": {"unexpected": 1}}]),
        "size_bool": ("size_bytes", True),
        "version": ("schema_version", 2),
    }
    if target in changes:
        key, replacement = changes[target]
        receipt[key] = replacement
        raw = canonical(receipt)
    elif target == "duplicate":
        raw = raw.replace(
            b'"schema_version":1', b'"schema_version":1,"schema_version":1'
        )
    else:
        raw = raw[:-1]
    value["receipt_payload_b64"] = base64.b64encode(raw).decode()
    value["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))


@pytest.mark.parametrize(
    "action,arguments",
    [
        ("attach", {}),
        ("record", {"phase": "future", "receipt_sha256": ZERO}),
        ("record", {"phase": "reserved", "receipt_sha256": "x"}),
        ("reserve", {"size_bytes": True, "project_path": ROOT}),
        ("reserve", {"size_bytes": 0, "project_path": ROOT}),
        ("reserve", {"size_bytes": 1, "project_path": ROOT, "extra": 0}),
        ("reserve", {"size_bytes": 1, "project_path": "D:/foreign"}),
    ],
)
def test_request_schema_rejection(action, arguments):
    value = envelope()
    assert j.validate_snapshot(canonical(value)).payload == canonical(value)
    raw = canonical({"action": action, "operation_id": OP, "arguments": arguments})
    value["request_payload_b64"] = base64.b64encode(raw).decode()
    value["request_sha256"] = request_digest(raw)
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))


def prepare_golden(value, b=512):
    """LE152 PREPARE: digest120; payload from B, all zero padding included."""
    import uuid

    payload = canonical(value)
    p = ((1048576 + b - 1) // b) * b
    raw = struct.pack(
        "<8s4IQ2I16s32s32s",
        b"MSPREP01",
        1,
        b + p,
        value["slot_index"],
        0,
        value["generation"],
        len(payload),
        0,
        uuid.UUID(JID).bytes,
        bytes.fromhex(value["previous_commit_sha256"]),
        bytes.fromhex(value["request_sha256"]),
    )
    raw += bytes(b - len(raw)) + payload + bytes(p - len(payload))
    digest = hashlib.sha256(b"MSJNL/PREPARE/v1" + raw).digest()
    return raw[:120] + digest + raw[152:]


def commit_golden(value, prepare, b=512):
    """LE176 COMMIT: digest144; separate block with linked PREPARE hash."""
    import uuid

    raw = struct.pack(
        "<8s4IQ16s32s32s32s",
        b"MSCMIT01",
        1,
        b,
        value["slot_index"],
        0,
        value["generation"],
        uuid.UUID(JID).bytes,
        bytes.fromhex(value["previous_commit_sha256"]),
        prepare[120:152],
        bytes.fromhex(value["request_sha256"]),
    )
    raw += bytes(b - len(raw))
    digest = hashlib.sha256(b"MSJNL/COMMIT/v1" + raw).digest()
    return raw[:144] + digest + raw[176:]


def test_frame_golden_domain_separation():
    value = envelope()
    snapshot = j.validate_snapshot(canonical(value))
    header = j.decode_header(header_golden())
    golden = prepare_golden(value)
    assert j.encode_prepare(header, snapshot) == golden
    assert j.encode_commit(header, snapshot, golden) == commit_golden(value, golden)
    assert golden[120:152] != commit_golden(value, golden)[144:176]
    wrong = envelope()
    wrong["journal_id"] = "22345678-1234-4123-8123-123456789abc"
    with pytest.raises(ValueError):
        j.encode_prepare(header, j.validate_snapshot(canonical(wrong)))
    damaged = bytearray(golden)
    damaged[512] ^= 1
    with pytest.raises(ValueError):
        j.encode_commit(header, snapshot, bytes(damaged))


def journal_wire(values, incomplete=False, b=512):
    """Construye bytes sólo con el golden independiente, nunca con el codec."""
    raw = header_golden(b)
    p = ((1048576 + b - 1) // b) * b
    for index, value in enumerate(values):
        prep = prepare_golden(value, b)
        commit = (
            bytes(b)
            if incomplete and index == len(values) - 1
            else commit_golden(value, prep, b)
        )
        raw += prep + commit
    return raw + bytes((64 - len(values)) * (p + 2 * b))


def two_values():
    first = envelope()
    commit = commit_golden(first, prepare_golden(first))
    second = envelope(2, commit[144:176].hex(), "01ARZ3NDEKTSV4RRFFQ69G5FAX")
    return [first, second]


def test_inspect_clean_incomplete_fullscan():
    wire = journal_wire(two_values())
    inspection = j.inspect_journal(wire)
    assert inspection.status == "clean"
    assert inspection.consumed_slots == 2
    assert inspection.head.generation == 2
    assert len(inspection.heads) == 2
    empty = j.inspect_journal(journal_wire([]))
    assert empty.status == "clean" and empty.head is None
    pending = j.inspect_journal(journal_wire(two_values(), incomplete=True))
    assert pending.status == "incomplete_tail"
    assert pending.head is None
    assert pending.consumed_slots == 2
    assert pending.incomplete_payload == canonical(two_values()[1])


@pytest.mark.parametrize(
    "target",
    [
        "gap",
        "tail",
        "prepare",
        "commit",
        "predecessor",
        "duplicate_request",
        "operation",
        "truncated",
        "extra",
        "header",
        "padding",
        "incomplete_gap",
    ],
)
def test_inspect_corruption_is_closed(target):
    values = two_values()
    good = journal_wire(values)
    assert j.inspect_journal(good).status == "clean"
    b, s = 512, 1048576 + 1024
    if target == "predecessor":
        values[1]["previous_commit_sha256"] = "f" * 64
        bad = journal_wire(values)
    elif target == "duplicate_request":
        values[1]["request_id"] = RID
        bad = journal_wire(values)
    elif target == "operation":
        values[1]["operation_id"] = values[1]["request_id"]
        receipt = json.loads(base64.b64decode(values[1]["receipt_payload_b64"]))
        receipt["operation_id"] = values[1]["operation_id"]
        rr = canonical(receipt)
        req = json.loads(base64.b64decode(values[1]["request_payload_b64"]))
        req["operation_id"] = values[1]["operation_id"]
        rq = canonical(req)
        values[1].update(
            receipt_payload_b64=base64.b64encode(rr).decode(),
            receipt_sha256=hashlib.sha256(rr).hexdigest(),
            request_payload_b64=base64.b64encode(rq).decode(),
            request_sha256=request_digest(rq),
        )
        assert j.validate_snapshot(canonical(values[1])).payload == canonical(values[1])
        bad = journal_wire(values)
    elif target == "truncated":
        bad = good[:-1]
    elif target == "extra":
        bad = good + b"\x00"
    elif target == "incomplete_gap":
        bad = journal_wire(values, incomplete=True)
        bad = bad[: b + s] + bytes(s) + bad[b + 2 * s :]
        bad = bad[:-1] + b"\x01"
    else:
        damage = bytearray(good)
        if target == "gap":
            damage[b : b + s] = bytes(s)
        else:
            offset = {
                "tail": b + 63 * s,
                "prepare": b,
                "commit": b + s - b,
                "header": 64,
                "padding": b + 152,
            }[target]
            damage[offset] ^= 1
        bad = bytes(damage)
    result = j.inspect_journal(bad)
    assert result.status in ("JOURNAL_CORRUPT", "JOURNAL_CORRUPT_OR_UNKNOWN")
    assert result.head is None and result.heads == ()


@pytest.mark.parametrize(
    "section,offset",
    [
        ("prepare", i)
        for i in (0, 8, 12, 16, 20, 24, 32, 36, 40, 56, 88, 120, 152, 511, 512, 1049087)
    ]
    + [("commit", i) for i in (0, 8, 12, 16, 20, 24, 32, 48, 80, 112, 144, 176, 511)],
)
def test_frame_offset_damage_no_prefix_head(section, offset):
    good = journal_wire([envelope()])
    assert j.inspect_journal(good).status == "clean"
    raw = bytearray(good)
    position = 512 + (1048576 + 512 if section == "commit" else 0) + offset
    raw[position] ^= 1
    result = j.inspect_journal(bytes(raw))
    assert result.status == "JOURNAL_CORRUPT"
    assert result.head is None


def test_requests_replay_conflict_stale_and_append():
    inspection = j.inspect_journal(journal_wire(two_values()))
    head = inspection.head
    first = inspection.heads[0]
    replay = j.decide_request(inspection, RID, request(), None)
    assert replay.status == "replay"
    assert replay.head == first and replay.next_slot is None
    changed = request(size_bytes=1, project_path=ROOT)
    assert j.decide_request(inspection, RID, changed, head).status == "REQUEST_CONFLICT"
    fresh_id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
    assert (
        j.decide_request(inspection, fresh_id, request(), first).status
        == "STALE_GENERATION"
    )
    decision = j.decide_request(inspection, fresh_id, request(), head)
    assert decision.status == "append" and decision.next_slot == 2
    assert decision.head == head
    empty = j.inspect_journal(journal_wire([]))
    assert j.decide_request(empty, fresh_id, request(), None).next_slot == 0
    pending = j.inspect_journal(journal_wire(two_values(), incomplete=True))
    assert j.decide_request(pending, RID, request(), head).status == "JOURNAL_BLOCKED"


def test_full_64_replay_before_full():
    values = []
    previous = ZERO
    for index in range(64):
        value = envelope(index + 1, previous, OP[:20] + f"{index:06d}")
        previous = commit_golden(value, prepare_golden(value))[144:176].hex()
        values.append(value)
    inspection = j.inspect_journal(journal_wire(values))
    assert inspection.status == "clean" and inspection.consumed_slots == 64
    replay = j.decide_request(inspection, values[0]["request_id"], request(), None)
    assert replay.status == "replay" and replay.head == inspection.heads[0]
    assert (
        j.decide_request(inspection, RID, request(), inspection.head).status
        == "JOURNAL_FULL"
    )
    assert (
        j.decide_request(inspection, RID, request(), None).status == "STALE_GENERATION"
    )


def lifecycle_receipt(phase="published"):
    receipt = json.loads(base64.b64decode(envelope()["receipt_payload_b64"]))
    evidence = [
        {
            "phase": "raw_verified",
            "evidence": {
                "raw_sha256": "b" * 64,
                "raw_size": 67108864,
                "uuid": "22345678-1234-4123-8123-123456789abc",
            },
        },
        {
            "phase": "vhdx_verified",
            "evidence": {"vhdx_sha256": "c" * 64, "vhdx_size": 1024},
        },
        {
            "phase": "published",
            "evidence": {"final_path": receipt["disk_path"], "file_id": "file-1"},
        },
        {
            "phase": "attached",
            "evidence": {"device": "/dev/loop0", "mountpoint": "/mnt/studio-data"},
        },
        {"phase": "validated", "evidence": {"noreplace": True, "fs_type": "ext4"}},
    ]
    phases = [
        "reserved",
        "raw_verified",
        "vhdx_verified",
        "published",
        "attached",
        "validated",
    ]
    receipt["phase"] = phase
    receipt["history"].extend(evidence[: phases.index(phase)])
    return receipt


def with_receipt(value, receipt, published=None):
    raw = canonical(receipt)
    value["receipt_payload_b64"] = base64.b64encode(raw).decode()
    value["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    requested = json.loads(base64.b64decode(value["request_payload_b64"]))
    if requested["action"] == "reserve":
        requested["arguments"]["size_bytes"] = receipt["size_bytes"]
        request_raw = canonical(requested)
        value["request_payload_b64"] = base64.b64encode(request_raw).decode()
        value["request_sha256"] = request_digest(request_raw)
    value["published_receipt_payload_b64"] = (
        None if published is None else base64.b64encode(canonical(published)).decode()
    )
    return value


@pytest.mark.parametrize("damage", ["missing", "wrongphase", "size", "prefix"])
def test_published_snapshot_prefix_rejection(damage):
    pub = lifecycle_receipt()
    current = lifecycle_receipt("validated")
    good = canonical(with_receipt(envelope(), current, pub))
    assert j.validate_snapshot(good).payload == good
    if damage == "missing":
        pub = None
    elif damage == "wrongphase":
        pub = lifecycle_receipt("attached")
    elif damage == "size":
        pub["size_bytes"] += 1
    else:
        pub["history"][1]["evidence"]["raw_sha256"] = "f" * 64
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(with_receipt(envelope(), current, pub)))


@pytest.mark.parametrize(
    "damage", ["history", "size", "publishedbytes", "phase_regression"]
)
def test_chain_receipt_and_published_bytes_immutable(damage):
    first = with_receipt(envelope(), lifecycle_receipt(), lifecycle_receipt())
    prep = prepare_golden(first)
    second = with_receipt(
        envelope(
            2, commit_golden(first, prep)[144:176].hex(), "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        ),
        lifecycle_receipt("validated"),
        lifecycle_receipt(),
    )
    good = journal_wire([first, second])
    assert j.inspect_journal(good).status == "clean"
    current = lifecycle_receipt("validated")
    pub = lifecycle_receipt()
    if damage == "size":
        current["size_bytes"] += 1
        pub["size_bytes"] += 1
    elif damage == "history":
        current["history"][1]["evidence"]["raw_sha256"] = "f" * 64
        pub["history"][1]["evidence"]["raw_sha256"] = "f" * 64
    elif damage == "publishedbytes":
        pub["history"][3]["evidence"]["synthetic_extension"] = "changed"
        current["history"][3]["evidence"]["synthetic_extension"] = "changed"
    else:
        current = lifecycle_receipt("reserved")
        pub = None
    with_receipt(second, current, pub)
    # Each mutated snapshot remains internally valid; the chain is what rejects.
    assert j.validate_snapshot(canonical(second)).payload == canonical(second)
    result = j.inspect_journal(journal_wire([first, second]))
    assert result.status == "JOURNAL_CORRUPT" and result.head is None


@pytest.mark.parametrize(
    "phase",
    ["reserved", "raw_verified", "vhdx_verified", "published", "attached", "validated"],
)
def test_receipt_existing_phases_portable(phase, record_property):
    receipt = lifecycle_receipt(phase)
    pub = (
        lifecycle_receipt() if phase in ("published", "attached", "validated") else None
    )
    raw = canonical(with_receipt(envelope(), receipt, pub))
    snapshot = j.validate_snapshot(raw)
    assert snapshot.payload == raw
    assert base64.b64decode(snapshot.projection["receipt_payload_b64"]) == canonical(
        receipt
    )
    # Existing parser compatibility is only characterized on its Windows host.
    if sys.platform == "win32":
        spec = importlib.util.spec_from_file_location(
            "accepted_receipt",
            SOURCE.parents[1]
            / "packages/storage-guard/studio_storage_guard/receipt.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        record_property("accepted_receipt_import", module.__file__)
        record_property(
            "accepted_receipt_sha256",
            hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        )
        assert module.StorageReceipt.from_bytes(
            canonical(receipt)
        ).to_bytes() == canonical(receipt)


@pytest.mark.parametrize(
    "path", ["/x//y", "/x/./y", "/x/../y", "relative", "/x\\y", "/x/\x00"]
)
def test_session_posix_rejected(path):
    value = envelope()
    value["session"]["mountpoint"] = "/mnt/synthetic"
    assert j.validate_snapshot(canonical(value)).payload == canonical(value)
    value["session"]["mountpoint"] = path
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))


@pytest.mark.parametrize("cause", ["intent", "result"])
def test_open_session_consistency_only(cause):
    value = envelope()
    value["session"] = {
        "epoch": 1,
        "state": "validated",
        "admission": "open",
        "distro": "SyntheticDistro",
        "mountpoint": "/mnt/synthetic",
    }
    assert j.validate_snapshot(canonical(value)).payload == canonical(value)
    if cause == "intent":
        value["intent"] = {
            "action": "validate",
            "request_id": RID,
            "previous_state": "attached",
            "object_roles": ["published"],
        }
    else:
        value["result"] = {
            "state": "unknown",
            "code": "SYNTHETIC",
            "causes": ["synthetic-only"],
        }
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))
    value["session"]["admission"] = "closed"
    assert j.validate_snapshot(canonical(value)).payload == canonical(value)


@pytest.mark.parametrize(
    "case", ["depth", "list", "string", "nodes", "float", "duplicate"]
)
def test_receipt_extension_limits_causal(case):
    receipt = lifecycle_receipt("raw_verified")
    extension = receipt["history"][1]["evidence"]
    extension["synthetic_extension"] = ["x"] * 64
    good = with_receipt(envelope(), receipt)
    assert j.validate_snapshot(canonical(good)).payload == canonical(good)
    raw = None
    if case == "depth":
        nested = 0
        for _ in range(17):
            nested = [nested]
        extension["synthetic_extension"] = nested
    elif case == "list":
        extension["synthetic_extension"] = ["x"] * 65
    elif case == "string":
        extension["synthetic_extension"] = "x" * 32769
    elif case == "nodes":
        extension["synthetic_extension"] = [["x"] * 64 for _ in range(64)]
    elif case == "float":
        extension["synthetic_extension"] = 1.0
    else:
        raw = canonical(receipt).replace(
            b'"raw_size":67108864', b'"raw_size":67108864,"raw_size":67108864'
        )
    if raw is None:
        raw = canonical(receipt)
    good["receipt_payload_b64"] = base64.b64encode(raw).decode()
    good["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(good))


@pytest.mark.parametrize("b", [512, 1024, 4096, 65536])
def test_layout_boundaries_and_header_dataclass(b):
    layout = j.JournalLayout(b)
    header = j.JournalHeader(layout, JID)
    assert j.encode_header(header) == header_golden(b)
    assert j.decode_header(header_golden(b)) == header
    assert layout.slot_offset(63) == b + 63 * layout.slot_bytes
    for index in (True, -1, 64, 1.0):
        with pytest.raises(ValueError):
            layout.slot_offset(index)


def test_public_bytes_inputs_and_limit():
    raw = canonical(envelope())
    for value in (bytearray(raw), memoryview(raw), raw.decode(), None, bytes(1048577)):
        with pytest.raises(ValueError):
            j.validate_snapshot(value)
    for value in (bytearray(), memoryview(b""), "", None):
        with pytest.raises(ValueError):
            j.inspect_journal(value)
    assert j.inspect_journal(b"").status == "JOURNAL_CORRUPT_OR_UNKNOWN"


def test_no_external_effects_guard_has_positive_control(monkeypatch):
    import builtins
    import ctypes
    import os
    import subprocess
    import time
    import uuid

    wire = journal_wire([envelope()])
    snapshot = j.validate_snapshot(canonical(envelope()))
    header = j.decode_header(header_golden())
    observed = []

    def forbidden(*args, **kwargs):
        observed.append("blocked")
        raise AssertionError("external effect blocked")

    with monkeypatch.context() as patch:
        for owner, name in (
            (builtins, "open"),
            (os, "open"),
            (os, "stat"),
            (subprocess, "run"),
            (subprocess, "Popen"),
            (ctypes, "CDLL"),
            (ctypes, "WinDLL" if sys.platform == "win32" else "PyDLL"),
            (time, "time"),
            (uuid, "uuid4"),
        ):
            patch.setattr(owner, name, forbidden)
        with (
            pytest.raises(AssertionError, match="external effect"),
            builtins.open("synthetic-forbidden-control"),
        ):
            pytest.fail("el guard debe interceptar antes de crear el archivo")
        observed.clear()
        assert j.encode_header(header) == header_golden()
        prepare = j.encode_prepare(header, snapshot)
        assert j.encode_commit(header, snapshot, prepare) == commit_golden(
            envelope(), prepare
        )
        inspection = j.inspect_journal(wire)
        assert j.decide_request(inspection, RID, request(), None).status == "replay"
        assert observed == []


def test_same_request_id_different_malformed_bytes_is_conflict():
    inspection = j.inspect_journal(journal_wire([envelope()]))
    assert j.decide_request(inspection, RID, request(), None).status == "replay"
    assert (
        j.decide_request(inspection, RID, b"different bytes", None).status
        == "REQUEST_CONFLICT"
    )


def test_nested_base64_named_extension_has_ordinary_string_limit():
    receipt = lifecycle_receipt("raw_verified")
    evidence = receipt["history"][1]["evidence"]
    evidence["receipt_payload_b64"] = "x" * 32768
    good = canonical(with_receipt(envelope(), receipt))
    assert j.validate_snapshot(good).payload == good
    evidence["receipt_payload_b64"] = "x" * 32769
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(with_receipt(envelope(), receipt)))


def test_owned_object_cannot_alias_omitted_journal_role():
    value = envelope()
    value["owned_objects"] = [
        {
            "role": "raw",
            "identity": identity(ROOT + "/data/_storage/raw.img", 6, "file"),
            "parent_identity": dict(value["parent_chain"][-1]),
            "name": "raw.img",
            "origin": "created",
        }
    ]
    good = canonical(value)
    assert j.validate_snapshot(good).payload == good
    value["owned_objects"][0]["identity"]["file_id"] = value["journal_identity"][
        "file_id"
    ]
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))


@pytest.mark.parametrize(
    "action,field",
    [("reserve", "size_bytes"), ("record", "phase"), ("record", "receipt_sha256")],
)
def test_request_arguments_match_current_receipt(action, field):
    value = envelope()
    args = (
        {"size_bytes": 67108864, "project_path": ROOT}
        if action == "reserve"
        else {"phase": "reserved", "receipt_sha256": value["receipt_sha256"]}
    )
    raw = canonical({"action": action, "operation_id": OP, "arguments": args})
    value["request_payload_b64"] = base64.b64encode(raw).decode()
    value["request_sha256"] = request_digest(raw)
    good = canonical(value)
    assert j.validate_snapshot(good).payload == good
    args[field] = {
        "size_bytes": 67108865,
        "phase": "raw_verified",
        "receipt_sha256": "f" * 64,
    }[field]
    changed = canonical({"action": action, "operation_id": OP, "arguments": args})
    value["request_payload_b64"] = base64.b64encode(changed).decode()
    value["request_sha256"] = request_digest(changed)
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))


@pytest.mark.parametrize(
    "phase,index,key,bad",
    [
        ("raw_verified", 1, "raw_sha256", "A" * 64),
        ("raw_verified", 1, "raw_size", True),
        ("raw_verified", 1, "uuid", JID),
        ("raw_verified", 1, "uuid", "not-a-uuid"),
        ("vhdx_verified", 2, "vhdx_sha256", "z" * 64),
        ("vhdx_verified", 2, "vhdx_size", 0),
        ("published", 3, "final_path", ROOT + "/elsewhere.vhdx"),
        ("published", 3, "file_id", ""),
        ("attached", 4, "device", "/not-dev/loop0"),
        ("attached", 4, "mountpoint", "/mnt/../x"),
        ("validated", 5, "noreplace", 1),
        ("validated", 5, "fs_type", "ntfs"),
    ],
)
def test_receipt_phase_evidence_negative_controls(phase, index, key, bad):
    current = lifecycle_receipt(phase)
    pub = lifecycle_receipt() if index >= 3 else None
    good = canonical(with_receipt(envelope(), current, pub))
    assert j.validate_snapshot(good).payload == good
    current["history"][index]["evidence"][key] = bad
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(with_receipt(envelope(), current, pub)))


@pytest.mark.parametrize(
    "section,offset",
    [
        ("prepare", 0),
        ("prepare", 8),
        ("prepare", 12),
        ("prepare", 16),
        ("prepare", 20),
        ("prepare", 32),
        ("prepare", 36),
        ("prepare", 152),
        ("commit", 0),
        ("commit", 8),
        ("commit", 12),
        ("commit", 16),
        ("commit", 20),
        ("commit", 176),
    ],
)
def test_rehashed_semantic_frame_damage_still_rejected(section, offset):
    value = envelope()
    prep = prepare_golden(value)
    commit = commit_golden(value, prep)
    good = journal_wire([value])
    assert j.inspect_journal(good).status == "clean"
    raw = bytearray(prep if section == "prepare" else commit)
    raw[offset] ^= 1
    digest_offset = 120 if section == "prepare" else 144
    raw[digest_offset : digest_offset + 32] = bytes(32)
    domain = b"MSJNL/PREPARE/v1" if section == "prepare" else b"MSJNL/COMMIT/v1"
    raw[digest_offset : digest_offset + 32] = hashlib.sha256(domain + raw).digest()
    start = 512 if section == "prepare" else 512 + len(prep)
    bad = good[:start] + bytes(raw) + good[start + len(raw) :]
    assert j.inspect_journal(bad).status == "JOURNAL_CORRUPT"


def test_actual_private_import(record_property):
    assert Path(j.__file__).resolve() == SOURCE.resolve()
    record_property("actual_import", str(SOURCE.resolve()))
    record_property("source_sha256", hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    record_property("platform", sys.platform)


def test_root_posix_is_canonical_metadata_not_permission():
    value = envelope()
    value["session"]["mountpoint"] = "/"
    assert j.validate_snapshot(canonical(value)).payload == canonical(value)


def test_unicode_control_character_in_metadata_rejected():
    value = envelope()
    value["session"]["distro"] = "SyntheticDistro"
    good = canonical(value)
    assert j.validate_snapshot(good).payload == good
    value["session"]["distro"] = "Synthetic\u0085Distro"
    with pytest.raises(ValueError):
        j.validate_snapshot(canonical(value))


@pytest.mark.parametrize("value", [[0] * 65, [[0] * 64 for _ in range(64)]])
def test_container_limits_precede_json_parser_allocation(value):
    good = canonical({"synthetic_extension": [0] * 64})
    assert j._preflight_json(good) is None
    with pytest.raises(ValueError):
        j._preflight_json(canonical({"synthetic_extension": value}))


class MutableStatus(list):
    """Reproducción A01: igualdad personalizada sobre estado mutable de caller."""

    def __eq__(self, other):
        return self[0] == other

    def __ne__(self, other):
        return not self == other


@pytest.mark.parametrize(
    "constructor,status",
    [
        (j.JournalInspection, "JOURNAL_CORRUPT"),
        (j.RequestDecision, "append"),
    ],
)
def test_a01_public_status_rejects_mutable_scalar(constructor, status):
    control = constructor(status)
    assert type(control.status) is str and control.status == status
    if constructor is j.JournalInspection:
        assert (
            j.decide_request(control, RID, request(), None).status == "JOURNAL_BLOCKED"
        )
    caller = MutableStatus([status])
    with pytest.raises(j.JournalError):
        constructor(caller)
    caller[0] = "clean" if constructor is j.JournalInspection else "replay"
    assert control.status == status


def record_receipt(value, receipt, published=None):
    with_receipt(value, receipt, published)
    raw = canonical(
        {
            "action": "record",
            "operation_id": OP,
            "arguments": {
                "phase": receipt["phase"],
                "receipt_sha256": value["receipt_sha256"],
            },
        }
    )
    value["request_payload_b64"] = base64.b64encode(raw).decode()
    value["request_sha256"] = request_digest(raw)
    return value


def test_b01_chain_history_bool_to_int_changes_exact_bytes():
    import copy

    receipt = lifecycle_receipt("raw_verified")
    receipt["history"][1]["evidence"]["synthetic_extension"] = True
    first = record_receipt(envelope(), receipt)
    prev = commit_golden(first, prepare_golden(first))[144:176].hex()
    second_receipt = copy.deepcopy(receipt)
    second = record_receipt(
        envelope(2, prev, "01ARZ3NDEKTSV4RRFFQ69G5FAX"), second_receipt
    )
    assert j.inspect_journal(journal_wire([first, second])).status == "clean"
    second_receipt["history"][1]["evidence"]["synthetic_extension"] = 1
    assert receipt["history"] == second_receipt["history"]
    assert canonical(receipt["history"]) != canonical(second_receipt["history"])
    record_receipt(second, second_receipt)
    assert j.validate_snapshot(canonical(second)).payload == canonical(second)
    rejected = j.inspect_journal(journal_wire([first, second]))
    assert rejected.status == "JOURNAL_CORRUPT" and rejected.head is None


def test_b01_published_prefix_bool_to_int_changes_exact_bytes():
    pub = lifecycle_receipt("published")
    current = lifecycle_receipt("validated")
    pub["history"][1]["evidence"]["synthetic_extension"] = True
    current["history"][1]["evidence"]["synthetic_extension"] = True
    control = canonical(record_receipt(envelope(), current, pub))
    assert j.validate_snapshot(control).payload == control
    current["history"][1]["evidence"]["synthetic_extension"] = 1
    assert current["history"][: len(pub["history"])] == pub["history"]
    assert canonical(current["history"][: len(pub["history"])]) != canonical(
        pub["history"]
    )
    mutated = canonical(record_receipt(envelope(), current, pub))
    with pytest.raises(j.JournalError):
        j.validate_snapshot(mutated)


def enormous_integer_payload(field):
    good = canonical(envelope())
    original = b'"generation":1' if field == "generation" else b'"epoch":0'
    key = b'"generation":' if field == "generation" else b'"epoch":'
    bad = good.replace(original, key + b"9" * 5000, 1)
    assert len(bad) < 1048576 and bad != good
    return good, bad


@pytest.mark.parametrize("field", ["generation", "epoch"])
def test_b02_large_integer_has_typed_error_without_global_limit_change(field):
    good, bad = enormous_integer_payload(field)
    limit = sys.get_int_max_str_digits()
    assert limit == 4300
    assert j.validate_snapshot(good).payload == good
    with pytest.raises(j.JournalError):
        j.validate_snapshot(bad)
    assert sys.get_int_max_str_digits() == limit


@pytest.mark.parametrize("field", ["generation", "epoch"])
def test_b02_large_integer_correctly_hashed_wire_is_closed(field):
    import uuid

    good, bad = enormous_integer_payload(field)
    value = envelope()
    assert good == canonical(value)
    assert j.inspect_journal(journal_wire([value])).status == "clean"
    b, p = 512, 1048576
    raw = struct.pack(
        "<8s4IQ2I16s32s32s",
        b"MSPREP01",
        1,
        b + p,
        0,
        0,
        1,
        len(bad),
        0,
        uuid.UUID(JID).bytes,
        bytes(32),
        bytes.fromhex(value["request_sha256"]),
    )
    raw += bytes(b - len(raw)) + bad + bytes(p - len(bad))
    digest = hashlib.sha256(b"MSJNL/PREPARE/v1" + raw).digest()
    prep = raw[:120] + digest + raw[152:]
    commit = commit_golden(value, prep)
    wire = header_golden() + prep + commit + bytes(63 * (p + 2 * b))
    assert len(wire) == len(journal_wire([value]))
    limit = sys.get_int_max_str_digits()
    rejected = j.inspect_journal(wire)
    assert rejected.status in ("JOURNAL_CORRUPT", "JOURNAL_CORRUPT_OR_UNKNOWN")
    assert rejected.head is None and rejected.heads == ()
    assert sys.get_int_max_str_digits() == limit == 4300


def header_golden(b=512):
    """Wire independiente: LE96; digest en offset64 y ceros hasta B."""
    import uuid

    p = ((1048576 + b - 1) // b) * b
    s = p + b * 2
    raw = struct.pack(
        "<8s6I2Q16s",
        b"MSJNL001",
        1,
        b,
        b,
        64,
        1048576,
        0,
        s,
        b + 64 * s,
        uuid.UUID(JID).bytes,
    )
    raw += bytes(b - len(raw))
    digest = hashlib.sha256(b"MSJNL/HEADER/v1" + raw).digest()
    return raw[:64] + digest + raw[96:]


def test_header_golden_and_mutations():
    wire = header_golden()
    assert j.encode_header((512, JID)) == wire
    header = j.decode_header(wire)
    assert header.journal_id == JID
    assert header.layout.alignment == 512
    for offset in (0, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 96, 511):
        damage = bytearray(wire)
        damage[offset] ^= 1
        with pytest.raises(ValueError):
            j.decode_header(bytes(damage))
    for value in (wire[:-1], wire + b"\x00", bytearray(wire), memoryview(wire)):
        with pytest.raises(ValueError):
            j.decode_header(value)


def test_layout_exact_and_strict():
    layout = j.JournalLayout(4096)
    assert layout.payload_bytes == 1048576
    assert layout.slot_bytes == 1056768
    assert layout.capacity_bytes == 67637248
    for value in (True, 511, 513, 131072, 4096.0):
        with pytest.raises(ValueError):
            j.JournalLayout(value)
