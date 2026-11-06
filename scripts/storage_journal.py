"""Codec puro de journal v1: datos lógicos sin autoridad ni efectos nativos.

Wire W1–W6: LE explícito, 64 slots fijos, SHA256 separado por dominio,
schemas cerrados, snapshots bytes inmutables y scan completo fail-closed.
Un head lógico no es JournalToken, ACK durable, flush ni permiso de despliegue.
"""

import base64
import binascii
import hashlib
import json
import re
import struct
import unicodedata
from dataclasses import dataclass, field
from pathlib import PureWindowsPath
from uuid import UUID

MAX_PAYLOAD = 1048576
SLOT_COUNT = 64
PHASES = (
    "reserved",
    "raw_verified",
    "vhdx_verified",
    "published",
    "attached",
    "validated",
)
STATES = (
    "inactive",
    "attach_intent",
    "attached",
    "validate_intent",
    "validated",
    "quiesce_intent",
    "detach_intent",
    "detached",
    "unknown",
)
ROLES = ("journal", "raw", "incoming", "published")
ACTIONS = (
    "reserve",
    "raw_verify",
    "vhdx_verify",
    "publish",
    "attach",
    "validate",
    "quiesce",
    "detach",
    "reconcile",
)
ENVELOPE_KEYS = frozenset(
    (
        "journal_version",
        "generation",
        "slot_index",
        "journal_id",
        "operation_id",
        "request_id",
        "request_payload_b64",
        "request_sha256",
        "previous_commit_sha256",
        "receipt_payload_b64",
        "receipt_sha256",
        "published_receipt_payload_b64",
        "journal_identity",
        "project_identity",
        "parent_chain",
        "owned_objects",
        "intent",
        "session",
        "result",
    )
)


class JournalError(ValueError):
    """Entrada wire inválida; nunca concede capacidad de almacenamiento."""


def _uint(value, maximum=(1 << 64) - 1, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise JournalError("INTEGER_INVALID")
    return value


@dataclass(frozen=True)
class JournalLayout:
    alignment: int
    payload_bytes: int = field(init=False)
    slot_bytes: int = field(init=False)
    capacity_bytes: int = field(init=False)

    def __post_init__(self):
        b = _uint(self.alignment, 65536, 512)
        if b & (b - 1):
            raise JournalError("ALIGNMENT_INVALID")
        p = ((MAX_PAYLOAD + b - 1) // b) * b
        object.__setattr__(self, "payload_bytes", p)
        object.__setattr__(self, "slot_bytes", p + 2 * b)
        object.__setattr__(self, "capacity_bytes", b + SLOT_COUNT * (p + 2 * b))

    def slot_offset(self, index):
        return self.alignment + _uint(index, SLOT_COUNT - 1) * self.slot_bytes


def _bytes(value, maximum=None):
    if type(value) is not bytes:
        raise JournalError("BYTES_REQUIRED")
    if maximum is not None and len(value) > maximum:
        raise JournalError("PAYLOAD_TOO_LARGE")
    return value


def _uuid(value):
    if type(value) is not str:
        raise JournalError("UUID_INVALID")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise JournalError("UUID_INVALID") from exc
    if (
        str(parsed) != value
        or parsed.version != 4
        or parsed.variant != "specified in RFC 4122"
    ):
        raise JournalError("UUID_INVALID")
    return parsed.bytes


@dataclass(frozen=True)
class JournalHeader:
    layout: JournalLayout
    journal_id: str

    def __post_init__(self):
        if type(self.layout) is not JournalLayout:
            raise JournalError("LAYOUT_INVALID")
        _uuid(self.journal_id)


def _seal(domain, raw, offset):
    digest = hashlib.sha256(domain + raw).digest()
    return raw[:offset] + digest + raw[offset + 32 :]


def _verify(domain, raw, offset):
    expected = hashlib.sha256(
        domain + raw[:offset] + bytes(32) + raw[offset + 32 :]
    ).digest()
    if raw[offset : offset + 32] != expected:
        raise JournalError("DIGEST_INVALID")


def encode_header(header):
    if type(header) is tuple and len(header) == 2:
        header = JournalHeader(JournalLayout(header[0]), header[1])
    if type(header) is not JournalHeader:
        raise JournalError("HEADER_INVALID")
    layout = header.layout
    b = layout.alignment
    raw = struct.pack(
        "<8s6I2Q16s",
        b"MSJNL001",
        1,
        b,
        b,
        SLOT_COUNT,
        MAX_PAYLOAD,
        0,
        layout.slot_bytes,
        layout.capacity_bytes,
        _uuid(header.journal_id),
    ) + bytes(b - 64)
    return _seal(b"MSJNL/HEADER/v1", raw, 64)


def decode_header(raw):
    _bytes(raw, 65536)
    if len(raw) < 96:
        raise JournalError("HEADER_TRUNCATED")
    fields = struct.unpack("<8s6I2Q16s", raw[:64])
    magic, version, size, alignment, count, maximum, reserved, slot, capacity, jid = (
        fields
    )
    layout = JournalLayout(alignment)
    if (
        magic != b"MSJNL001"
        or version != 1
        or size != alignment
        or len(raw) != alignment
        or count != SLOT_COUNT
        or maximum != MAX_PAYLOAD
        or reserved
        or slot != layout.slot_bytes
        or capacity != layout.capacity_bytes
        or any(raw[96:])
    ):
        raise JournalError("HEADER_INVALID")
    _verify(b"MSJNL/HEADER/v1", raw, 64)
    return JournalHeader(layout, str(UUID(bytes=jid)))


@dataclass(frozen=True)
class JournalSnapshot:
    payload: bytes

    def __post_init__(self):
        _validate_envelope(self.payload)

    @property
    def projection(self):
        return json.loads(self.payload)


def validate_snapshot(raw):
    return JournalSnapshot(raw)


def _closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise JournalError("SCHEMA_INVALID")


def _text(value, nonempty=True):
    if (
        type(value) is not str
        or (nonempty and not value)
        or any(
            unicodedata.category(c) == "Cc" or 0xD800 <= ord(c) <= 0xDFFF for c in value
        )
    ):
        raise JournalError("STRING_INVALID")
    return value


def _hex(value, length=64):
    if type(value) is not str or not re.fullmatch(
        r"[0-9a-f]{" + str(length) + r"}", value
    ):
        raise JournalError("HEX_INVALID")
    return value


def _ulid(value):
    if type(value) is not str or not re.fullmatch(
        r"[0-7][0-9A-HJKMNP-TV-Z]{25}", value
    ):
        raise JournalError("ULID_INVALID")
    return value


def _winpath(value, ancestor=False):
    _text(value)
    if not re.match(r"^[A-Z]:/", value) or "\\" in value:
        raise JournalError("WINDOWS_PATH_INVALID")
    path = PureWindowsPath(value)
    if not path.is_absolute() or path.as_posix() != value:
        raise JournalError("WINDOWS_PATH_INVALID")
    components = value[3:].split("/")
    if value.endswith(":/") and ancestor:
        return path
    for part in components:
        stem = part.split(".", 1)[0].upper()
        if (
            not part
            or part in (".", "..")
            or part.endswith((" ", "."))
            or any(c in part for c in ':<>"|?*')
            or stem in ("CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$")
            or re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", stem)
        ):
            raise JournalError("WINDOWS_PATH_INVALID")
    return path


def _posix(value):
    _text(value)
    if value == "/":
        return
    if (
        not value.startswith("/")
        or "\\" in value
        or any(p in ("", ".", "..") for p in value[1:].split("/"))
    ):
        raise JournalError("POSIX_PATH_INVALID")


def _canonical(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf8")


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise JournalError("DUPLICATE_KEY")
        value[key] = item
    return value


def _reject_constant(value):
    raise JournalError("NONFINITE_JSON")


def _preflight_json(raw):
    _bytes(raw, MAX_PAYLOAD)
    # Token budgets precede recursive parsing or materializing caller containers.
    # This is a bounds pass; stdlib still validates the actual JSON grammar.
    tokens = re.finditer(rb'"(?:[^"\\]|\\.)*"|[{}\[\],:]|[^\s{}\[\],:"]+', raw)
    containers = []
    nodes = 0
    for match in tokens:
        lead = match.group()[0]
        if lead in (44, 58):
            continue
        if lead in (93, 125):
            if containers:
                containers.pop()
            continue
        nodes += 1
        if nodes > 4096:
            raise JournalError("JSON_NODES")
        if containers and containers[-1][0] == 91:
            containers[-1][1] += 1
            if containers[-1][1] > 64:
                raise JournalError("JSON_LIST_LIMIT")
        if lead in (91, 123):
            containers.append([lead, 0])
            if len(containers) > 16:
                raise JournalError("JSON_DEPTH")


def _json(raw, envelope=False):
    _bytes(raw, MAX_PAYLOAD)
    _preflight_json(raw)
    try:
        value = json.loads(
            raw.decode("utf8"),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except JournalError:
        raise
    except (ValueError, RecursionError) as exc:
        raise JournalError("JSON_INVALID") from exc
    stack = [(value, None, False)]
    nodes = 0
    while stack:
        item, key, top_field = stack.pop()
        nodes += 1
        if nodes > 4096:
            raise JournalError("JSON_NODES")
        if type(item) is dict:
            stack.extend((k, None, False) for k in item)
            stack.extend((v, k, item is value) for k, v in item.items())
        elif type(item) is list:
            if len(item) > 64:
                raise JournalError("JSON_LIST_LIMIT")
            stack.extend((v, None, False) for v in item)
        elif type(item) is str:
            limit = (
                ((MAX_PAYLOAD + 2) // 3) * 4
                if envelope
                and top_field
                and key
                in (
                    "request_payload_b64",
                    "receipt_payload_b64",
                    "published_receipt_payload_b64",
                )
                else 32768
            )
            if len(item) > limit or any(0xD800 <= ord(c) <= 0xDFFF for c in item):
                raise JournalError("JSON_STRING_LIMIT")
        elif type(item) is int:
            _uint(item)
        elif item is not None and type(item) is not bool:
            raise JournalError("JSON_TYPE_INVALID")
    if _canonical(value) != raw:
        raise JournalError("JSON_NONCANONICAL")
    return value


def _b64(value):
    if type(value) is not str:
        raise JournalError("BASE64_INVALID")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise JournalError("BASE64_INVALID") from exc
    if base64.b64encode(raw).decode("ascii") != value:
        raise JournalError("BASE64_NONCANONICAL")
    return _bytes(raw, MAX_PAYLOAD)


def _identity(value, kind, ancestor=False):
    _closed(value, ("volume_serial", "file_id", "path", "kind"))
    _uint(value["volume_serial"])
    _hex(value["file_id"], 32)
    _winpath(value["path"], ancestor)
    if value["kind"] != kind:
        raise JournalError("IDENTITY_KIND_INVALID")


def _receipt(raw, project, operation, journal_id):
    value = _json(raw)
    _closed(
        value,
        (
            "schema_version",
            "operation_id",
            "phase",
            "disk_path",
            "size_bytes",
            "history",
        ),
    )
    if _uint(value["schema_version"]) != 1 or value["operation_id"] != operation:
        raise JournalError("RECEIPT_IDENTITY_INVALID")
    _ulid(value["operation_id"])
    _uint(value["size_bytes"], minimum=1)
    _winpath(value["disk_path"])
    if value["disk_path"] != project + "/data/_storage/studio-data.vhdx":
        raise JournalError("RECEIPT_PATH_INVALID")
    phase = value["phase"]
    if type(phase) is not str or phase not in PHASES:
        raise JournalError("RECEIPT_PHASE_INVALID")
    history = value["history"]
    if type(history) is not list or len(history) != PHASES.index(phase) + 1:
        raise JournalError("RECEIPT_HISTORY_INVALID")
    required = (
        (),
        ("raw_sha256", "raw_size", "uuid"),
        ("vhdx_sha256", "vhdx_size"),
        ("final_path", "file_id"),
        ("device", "mountpoint"),
        ("noreplace", "fs_type"),
    )
    for index, item in enumerate(history):
        _closed(item, ("phase", "evidence"))
        evidence = item["evidence"]
        if item["phase"] != PHASES[index] or type(evidence) is not dict:
            raise JournalError("RECEIPT_HISTORY_INVALID")
        if not set(required[index]).issubset(evidence) or (index == 0 and evidence):
            raise JournalError("RECEIPT_EVIDENCE_INVALID")
        if index == 1:
            _hex(evidence["raw_sha256"])
            _uint(evidence["raw_size"], minimum=1)
            try:
                uid = str(UUID(evidence["uuid"]))
            except (ValueError, TypeError, AttributeError) as exc:
                raise JournalError("EXT4_UUID_INVALID") from exc
            if uid != evidence["uuid"] or uid == journal_id:
                raise JournalError("EXT4_UUID_INVALID")
        elif index == 2:
            _hex(evidence["vhdx_sha256"])
            _uint(evidence["vhdx_size"], minimum=1)
        elif index == 3:
            _winpath(evidence["final_path"])
            _text(evidence["file_id"])
            if evidence["final_path"] != value["disk_path"]:
                raise JournalError("RECEIPT_PUBLISHED_PATH_INVALID")
        elif index == 4:
            _posix(evidence["device"])
            _posix(evidence["mountpoint"])
            if not evidence["device"].startswith("/dev/"):
                raise JournalError("RECEIPT_DEVICE_INVALID")
        elif index == 5:
            if evidence["noreplace"] is not True or evidence["fs_type"] != "ext4":
                raise JournalError("RECEIPT_VALIDATION_INVALID")
    return value


def _request(raw, operation, project):
    value = _json(raw)
    _closed(value, ("action", "operation_id", "arguments"))
    _ulid(value["operation_id"])
    if value["operation_id"] != operation:
        raise JournalError("REQUEST_OPERATION_INVALID")
    arguments = value["arguments"]
    if value["action"] == "reserve":
        _closed(arguments, ("size_bytes", "project_path"))
        _uint(arguments["size_bytes"], minimum=1)
        _winpath(arguments["project_path"])
        if arguments["project_path"] != project:
            raise JournalError("REQUEST_PROJECT_INVALID")
    elif value["action"] == "record":
        _closed(arguments, ("phase", "receipt_sha256"))
        if type(arguments["phase"]) is not str or arguments["phase"] not in PHASES:
            raise JournalError("REQUEST_PHASE_INVALID")
        _hex(arguments["receipt_sha256"])
    else:
        raise JournalError("REQUEST_ACTION_NOT_RELEASED")
    return value


def request_sha256(raw):
    _bytes(raw, MAX_PAYLOAD)
    return hashlib.sha256(
        b"MSJNL/REQUEST/v1" + struct.pack("<I", len(raw)) + raw
    ).hexdigest()


def _validate_envelope(raw):
    value = _json(raw, envelope=True)
    _closed(value, ENVELOPE_KEYS)
    if _uint(value["journal_version"]) != 1:
        raise JournalError("JOURNAL_VERSION_INVALID")
    generation = _uint(value["generation"], SLOT_COUNT, 1)
    if _uint(value["slot_index"], SLOT_COUNT - 1) != generation - 1:
        raise JournalError("GENERATION_INVALID")
    _uuid(value["journal_id"])
    _ulid(value["operation_id"])
    _ulid(value["request_id"])
    for key in ("request_sha256", "receipt_sha256", "previous_commit_sha256"):
        _hex(value[key])
    project = value["project_identity"]
    journal = value["journal_identity"]
    _identity(project, "directory")
    _identity(journal, "file")
    root = project["path"]
    if journal["path"] != root + "/data/_storage/storage-control.journal":
        raise JournalError("JOURNAL_PATH_INVALID")
    chain = value["parent_chain"]
    if type(chain) is not list or not chain:
        raise JournalError("PARENT_CHAIN_INVALID")
    paths = set()
    ids = set()
    for index, parent in enumerate(chain):
        _identity(parent, "directory", ancestor=True)
        path = parent["path"]
        fid = parent["file_id"]
        if (
            parent["volume_serial"] != project["volume_serial"]
            or path.casefold() in paths
            or fid in ids
        ):
            raise JournalError("PARENT_CHAIN_ALIAS")
        paths.add(path.casefold())
        ids.add(fid)
        if index == 0:
            if path != root[:3]:
                raise JournalError("PARENT_CHAIN_ROOT_INVALID")
        elif str(PureWindowsPath(path).parent.as_posix()) != chain[index - 1]["path"]:
            raise JournalError("PARENT_CHAIN_GAP")
    if (
        chain.count(project) != 1
        or chain[-1]["path"] != PureWindowsPath(journal["path"]).parent.as_posix()
    ):
        raise JournalError("PARENT_CHAIN_PROJECT_INVALID")
    if (
        journal["volume_serial"] != project["volume_serial"]
        or journal["file_id"] in ids
    ):
        raise JournalError("JOURNAL_IDENTITY_ALIAS")
    objects = value["owned_objects"]
    if type(objects) is not list:
        raise JournalError("OWNED_OBJECTS_INVALID")
    roles = set()
    object_ids = set()
    object_paths = set()
    for obj in objects:
        _closed(obj, ("role", "identity", "parent_identity", "name", "origin"))
        role = obj["role"]
        if (
            type(role) is not str
            or role not in ROLES
            or role in roles
            or obj["origin"] not in ("created", "reserved")
        ):
            raise JournalError("OWNED_ROLE_INVALID")
        roles.add(role)
        child, parent = obj["identity"], obj["parent_identity"]
        _identity(child, "file")
        _identity(parent, "directory")
        _text(obj["name"])
        if (
            child["volume_serial"] != project["volume_serial"]
            or parent["volume_serial"] != project["volume_serial"]
            or parent not in chain
            or child["file_id"] in ids
            or child["file_id"] in object_ids
            or child["path"].casefold() in object_paths
            or not child["path"].startswith(root + "/")
            or child["path"] != parent["path"] + "/" + obj["name"]
            or PureWindowsPath(child["path"]).name != obj["name"]
        ):
            raise JournalError("OWNED_IDENTITY_INVALID")
        if role == "journal" and child != journal:
            raise JournalError("OWNED_JOURNAL_INVALID")
        if (
            role == "published"
            and child["path"] != root + "/data/_storage/studio-data.vhdx"
        ):
            raise JournalError("OWNED_PUBLISHED_INVALID")
        if role != "journal" and (
            child["file_id"] == journal["file_id"]
            or child["path"].casefold() == journal["path"].casefold()
        ):
            raise JournalError("OWNED_ALIAS")
        object_ids.add(child["file_id"])
        object_paths.add(child["path"].casefold())
    receipt_raw = _b64(value["receipt_payload_b64"])
    if hashlib.sha256(receipt_raw).hexdigest() != value["receipt_sha256"]:
        raise JournalError("RECEIPT_DIGEST_INVALID")
    receipt = _receipt(receipt_raw, root, value["operation_id"], value["journal_id"])
    published = value["published_receipt_payload_b64"]
    if published is not None:
        pub = _receipt(
            _b64(published), root, value["operation_id"], value["journal_id"]
        )
        if (
            pub["phase"] != "published"
            or pub["size_bytes"] != receipt["size_bytes"]
            or _canonical(receipt["history"][: len(pub["history"])])
            != _canonical(pub["history"])
        ):
            raise JournalError("PUBLISHED_PREFIX_INVALID")
    elif PHASES.index(receipt["phase"]) >= PHASES.index("published"):
        raise JournalError("PUBLISHED_SNAPSHOT_REQUIRED")
    request_raw = _b64(value["request_payload_b64"])
    if request_sha256(request_raw) != value["request_sha256"]:
        raise JournalError("REQUEST_DIGEST_INVALID")
    request = _request(request_raw, value["operation_id"], root)
    arguments = request["arguments"]
    if request["action"] == "reserve":
        if arguments["size_bytes"] != receipt["size_bytes"]:
            raise JournalError("REQUEST_RECEIPT_SIZE_MISMATCH")
    elif (
        arguments["phase"] != receipt["phase"]
        or arguments["receipt_sha256"] != value["receipt_sha256"]
    ):
        raise JournalError("REQUEST_RECEIPT_RECORD_MISMATCH")
    intent = value["intent"]
    if intent is not None:
        _closed(intent, ("action", "request_id", "previous_state", "object_roles"))
        if (
            type(intent["action"]) is not str
            or intent["action"] not in ACTIONS
            or intent["previous_state"] not in STATES
        ):
            raise JournalError("INTENT_INVALID")
        _ulid(intent["request_id"])
        r = intent["object_roles"]
        if (
            type(r) is not list
            or any(type(x) is not str or x not in ROLES for x in r)
            or len(set(r)) != len(r)
        ):
            raise JournalError("INTENT_ROLES_INVALID")
    session = value["session"]
    _closed(session, ("epoch", "state", "admission", "distro", "mountpoint"))
    _uint(session["epoch"])
    if (
        type(session["state"]) is not str
        or session["state"] not in STATES
        or session["admission"] not in ("closed", "open")
    ):
        raise JournalError("SESSION_INVALID")
    if session["distro"] is not None:
        _text(session["distro"])
    if session["mountpoint"] is not None:
        _posix(session["mountpoint"])
    result = value["result"]
    if result is not None:
        _closed(result, ("state", "code", "causes"))
        if (
            result["state"] not in ("observed", "unknown")
            or type(result["causes"]) is not list
        ):
            raise JournalError("RESULT_INVALID")
        _text(result["code"])
        for cause in result["causes"]:
            _text(cause)
    if session["admission"] == "open" and (
        session["state"] != "validated"
        or intent is not None
        or (result is not None and result["state"] == "unknown")
    ):
        raise JournalError("ADMISSION_INCONSISTENT")
    return value


def encode_prepare(header, snapshot):
    if type(header) is not JournalHeader or type(snapshot) is not JournalSnapshot:
        raise JournalError("FRAME_INPUT_INVALID")
    value = snapshot.projection
    if value["journal_id"] != header.journal_id:
        raise JournalError("FRAME_JOURNAL_INVALID")
    layout = header.layout
    b, p = layout.alignment, layout.payload_bytes
    raw = struct.pack(
        "<8s4IQ2I16s32s32s",
        b"MSPREP01",
        1,
        b + p,
        value["slot_index"],
        0,
        value["generation"],
        len(snapshot.payload),
        0,
        _uuid(header.journal_id),
        bytes.fromhex(value["previous_commit_sha256"]),
        bytes.fromhex(value["request_sha256"]),
    )
    raw += bytes(b - len(raw)) + snapshot.payload + bytes(p - len(snapshot.payload))
    return _seal(b"MSJNL/PREPARE/v1", raw, 120)


def encode_commit(header, snapshot, prepare):
    _bytes(prepare)
    if prepare != encode_prepare(header, snapshot):
        raise JournalError("PREPARE_INVALID")
    value = snapshot.projection
    b = header.layout.alignment
    raw = struct.pack(
        "<8s4IQ16s32s32s32s",
        b"MSCMIT01",
        1,
        b,
        value["slot_index"],
        0,
        value["generation"],
        _uuid(header.journal_id),
        bytes.fromhex(value["previous_commit_sha256"]),
        prepare[120:152],
        bytes.fromhex(value["request_sha256"]),
    )
    raw += bytes(b - len(raw))
    return _seal(b"MSJNL/COMMIT/v1", raw, 144)


@dataclass(frozen=True)
class JournalHead:
    generation: int
    slot_index: int
    journal_id: str
    operation_id: str
    request_id: str
    request_payload: bytes
    commit_sha256: bytes
    snapshot: JournalSnapshot

    def __post_init__(self):
        if (
            _uint(self.generation, SLOT_COUNT, 1)
            != _uint(self.slot_index, SLOT_COUNT - 1) + 1
        ):
            raise JournalError("HEAD_GENERATION_INVALID")
        _uuid(self.journal_id)
        _ulid(self.operation_id)
        _ulid(self.request_id)
        _bytes(self.request_payload, MAX_PAYLOAD)
        if (
            len(_bytes(self.commit_sha256)) != 32
            or type(self.snapshot) is not JournalSnapshot
        ):
            raise JournalError("HEAD_INVALID")


@dataclass(frozen=True)
class JournalInspection:
    status: str
    head: JournalHead | None = None
    heads: tuple[JournalHead, ...] = ()
    consumed_slots: int = 0
    incomplete_payload: bytes | None = None

    def __post_init__(self):
        if type(self.status) is not str or self.status not in (
            "clean",
            "incomplete_tail",
            "JOURNAL_CORRUPT",
            "JOURNAL_CORRUPT_OR_UNKNOWN",
        ):
            raise JournalError("INSPECTION_STATUS_INVALID")
        if type(self.heads) is not tuple or any(
            type(h) is not JournalHead for h in self.heads
        ):
            raise JournalError("INSPECTION_HEADS_INVALID")
        if self.head is not None and type(self.head) is not JournalHead:
            raise JournalError("INSPECTION_HEAD_INVALID")
        _uint(self.consumed_slots, SLOT_COUNT)
        if self.incomplete_payload is not None:
            _bytes(self.incomplete_payload, MAX_PAYLOAD)


def _decode_prepare(header, raw):
    b = header.layout.alignment
    if len(raw) != b + header.layout.payload_bytes:
        raise JournalError("PREPARE_LENGTH_INVALID")
    length = struct.unpack_from("<I", raw, 32)[0]
    _uint(length, MAX_PAYLOAD, 1)
    snapshot = JournalSnapshot(raw[b : b + length])
    if raw != encode_prepare(header, snapshot):
        raise JournalError("PREPARE_INVALID")
    return snapshot


def _continuity(previous, current):
    old, new = previous.projection, current.projection
    for key in (
        "journal_id",
        "operation_id",
        "journal_identity",
        "project_identity",
        "parent_chain",
    ):
        if old[key] != new[key]:
            raise JournalError("CHAIN_IDENTITY_CHANGED")
    old_receipt = _json(_b64(old["receipt_payload_b64"]))
    new_receipt = _json(_b64(new["receipt_payload_b64"]))
    if old_receipt["size_bytes"] != new_receipt["size_bytes"]:
        raise JournalError("CHAIN_RECEIPT_IDENTITY_CHANGED")
    history = old_receipt["history"]
    if _canonical(new_receipt["history"][: len(history)]) != _canonical(history):
        raise JournalError("CHAIN_RECEIPT_HISTORY_CHANGED")
    published = old["published_receipt_payload_b64"]
    if published is not None and published != new["published_receipt_payload_b64"]:
        raise JournalError("CHAIN_PUBLISHED_BYTES_CHANGED")


def inspect_journal(raw):
    _bytes(raw)
    try:
        if len(raw) < 96:
            raise JournalError("JOURNAL_TRUNCATED")
        b = struct.unpack_from("<I", raw, 16)[0]
        layout = JournalLayout(b)
        if len(raw) != layout.capacity_bytes:
            raise JournalError("JOURNAL_CAPACITY_INVALID")
        header = decode_header(raw[:b])
    except JournalError:
        return JournalInspection("JOURNAL_CORRUPT_OR_UNKNOWN")
    heads = []
    seen_requests = set()
    previous_hash = bytes(32)
    unused = corrupt = False
    incomplete = None
    consumed = 0
    # Inspect every fixed slot. A damaged later slot can never leave a prefix head.
    for index in range(SLOT_COUNT):
        offset = layout.slot_offset(index)
        slot = raw[offset : offset + layout.slot_bytes]
        if not slot.strip(b"\x00"):
            unused = True
            continue
        consumed = index + 1
        if unused or incomplete is not None:
            corrupt = True
        prepare, commit = slot[:-b], slot[-b:]
        try:
            snapshot = _decode_prepare(header, prepare)
            value = snapshot.projection
            if (
                value["slot_index"] != index
                or value["generation"] != index + 1
                or bytes.fromhex(value["previous_commit_sha256"]) != previous_hash
                or value["request_id"] in seen_requests
            ):
                raise JournalError("CHAIN_INVALID")
            if heads:
                _continuity(heads[-1].snapshot, snapshot)
            if commit == bytes(b):
                incomplete = snapshot.payload
                continue
            if commit != encode_commit(header, snapshot, prepare):
                raise JournalError("COMMIT_INVALID")
            previous_hash = commit[144:176]
            seen_requests.add(value["request_id"])
            heads.append(
                JournalHead(
                    index + 1,
                    index,
                    header.journal_id,
                    value["operation_id"],
                    value["request_id"],
                    _b64(value["request_payload_b64"]),
                    previous_hash,
                    snapshot,
                )
            )
        except JournalError:
            corrupt = True
    if corrupt:
        return JournalInspection("JOURNAL_CORRUPT", consumed_slots=consumed)
    if incomplete is not None:
        return JournalInspection(
            "incomplete_tail", consumed_slots=consumed, incomplete_payload=incomplete
        )
    return JournalInspection(
        "clean", heads[-1] if heads else None, tuple(heads), consumed
    )


@dataclass(frozen=True)
class RequestDecision:
    status: str
    head: JournalHead | None = None
    next_slot: int | None = None

    def __post_init__(self):
        if type(self.status) is not str or self.status not in (
            "replay",
            "append",
            "REQUEST_CONFLICT",
            "STALE_GENERATION",
            "JOURNAL_FULL",
            "JOURNAL_BLOCKED",
        ):
            raise JournalError("DECISION_STATUS_INVALID")
        if self.head is not None and type(self.head) is not JournalHead:
            raise JournalError("DECISION_HEAD_INVALID")
        if self.next_slot is not None:
            _uint(self.next_slot, SLOT_COUNT - 1)


def decide_request(inspection, request_id, request_payload, expected_head):
    if type(inspection) is not JournalInspection or (
        expected_head is not None and type(expected_head) is not JournalHead
    ):
        raise JournalError("DECISION_INPUT_INVALID")
    _ulid(request_id)
    _bytes(request_payload, MAX_PAYLOAD)
    if inspection.status != "clean":
        return RequestDecision("JOURNAL_BLOCKED")
    for head in inspection.heads:
        if head.request_id == request_id:
            if head.request_payload != request_payload or request_sha256(
                head.request_payload
            ) != request_sha256(request_payload):
                return RequestDecision("REQUEST_CONFLICT")
            return RequestDecision("replay", head)
    value = _json(request_payload)
    _closed(value, ("action", "operation_id", "arguments"))
    operation = (
        inspection.head.operation_id if inspection.head else value["operation_id"]
    )
    project = (
        inspection.head.snapshot.projection["project_identity"]["path"]
        if inspection.head
        else None
    )
    if project is None and value["action"] == "reserve":
        _closed(value["arguments"], ("size_bytes", "project_path"))
        project = value["arguments"]["project_path"]
    _request(request_payload, operation, project)
    if expected_head != inspection.head:
        return RequestDecision("STALE_GENERATION")
    if inspection.consumed_slots >= SLOT_COUNT:
        return RequestDecision("JOURNAL_FULL")
    return RequestDecision("append", inspection.head, inspection.consumed_slots)
