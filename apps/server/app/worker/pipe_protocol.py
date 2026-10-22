"""IPC privado JSON puro (ADR-0057), sin I/O ni autoridad de publicación.

encode/decode validan un frame. Decoder.feed es un iterador: cada frame aceptado
se entrega antes de examinar el siguiente. Un fallo posterior conserva entregas
y cuentas anteriores. Consumir el iterador antes de otro feed/finish.
EOF sólo prueba frontera de bytes, nunca custodia ni recursos devueltos.

El payload es JSON opaco. El padre debe validar PerTakeResult y PostPlan, incluido
validate_result, por separado. El transporte no concede confianza ni publicación.
El epoch privado correlaciona, no autentica; no se exporta en snapshots públicos.
No se serializan objetos Python ni callbacks.
"""

from __future__ import annotations

import json
import math
import re
import struct
from enum import StrEnum

# ADR-0057: frame limita el cuerpo, total incluye prefijos, 64 tomas independientes.
MAX_FRAME_BYTES = 262144
MAX_TOTAL_BYTES = 4194304
MAX_FRAMES = 132
MAX_PROGRESS = 64
MAX_TAKE_RESULTS = 64
MAX_DEPTH = 20
MAX_COLLECTION = 256
MAX_STRING = 8192
MAX_EPOCH = 128  # Correlación ASCII pequeña del supervisor privado.
_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}\Z")
_EPOCH = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_FIELDS = {"version", "execution_id", "epoch", "seq", "kind", "payload"}
_FORBIDDEN = (
    "secret",
    "token",
    "password",
    "credential",
    "ciphertext",
    "authorization",
    "header",
    "apikey",
    "privatekey",
    "modelcode",
    "dynamicimport",
    "entrypoint",
)


class ProtocolError(ValueError):
    """Entrada privada inválida; el mensaje nunca incluye contenido recibido."""


class Kind(StrEnum):
    READY = "ready"
    REQUEST = "request"
    PROGRESS = "progress"
    TAKE_RESULT = "take_result"
    RESULT = "result"
    STOP = "stop"
    CLOSED = "closed"


def _string(value):
    if type(value) is not str or len(value) > MAX_STRING:
        raise ProtocolError("Cadena JSON inválida")
    if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise ProtocolError("Surrogate Unicode inválido")


def _json_value(value, depth=0, ancestors=None):
    """Acota cada valor antes de iterencode, sin subclases ejecutables."""
    if depth > MAX_DEPTH:
        raise ProtocolError("Profundidad JSON excedida")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        # Derivado del presupuesto wire, no del dominio (p.ej. seed).
        if value.bit_length() > MAX_FRAME_BYTES * 4:
            raise ProtocolError("Entero excede el presupuesto del frame")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ProtocolError("Número no finito")
        return
    if type(value) is str:
        _string(value)
        return
    if type(value) not in (dict, list) or len(value) > MAX_COLLECTION:
        raise ProtocolError("Colección JSON inválida")
    ancestors = set() if ancestors is None else ancestors
    identity = id(value)
    if identity in ancestors:
        raise ProtocolError("Ciclo JSON")
    ancestors.add(identity)
    if type(value) is dict:
        for key, item in value.items():
            _string(key)
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            if any(word in normalized for word in _FORBIDDEN):
                raise ProtocolError("Campo privado prohibido")
            _json_value(item, depth + 1, ancestors)
    else:
        for item in value:
            _json_value(item, depth + 1, ancestors)
    ancestors.remove(identity)


def _identity(execution_id, epoch):
    if type(execution_id) is not str or not _ULID.fullmatch(execution_id):
        raise ProtocolError("ULID de ejecución inválido")
    if type(epoch) is not str or not _EPOCH.fullmatch(epoch):
        raise ProtocolError("Epoch de correlación inválido")


def _envelope(message):
    if type(message) is not dict or message.keys() != _FIELDS:
        raise ProtocolError("Campos del sobre inválidos")
    if type(message["version"]) is not int or message["version"] != 1:
        raise ProtocolError("Versión inválida")
    _identity(message["execution_id"], message["epoch"])
    if type(message["seq"]) is not int or message["seq"] <= 0:
        raise ProtocolError("Secuencia inválida")
    _json_value(message["seq"])
    if type(message["kind"]) not in (str, Kind):
        raise ProtocolError("Tipo de mensaje inválido")
    try:
        Kind(message["kind"])
    except ValueError:
        raise ProtocolError("Tipo de mensaje desconocido") from None
    if type(message["payload"]) is not dict:
        raise ProtocolError("Payload debe ser objeto JSON")
    _json_value(message["payload"])


def encode(message: dict) -> bytes:
    """Prefijo uint32 network + UTF-8, valores acotados antes de codificar."""
    _envelope(message)
    body = bytearray()
    encoder = json.JSONEncoder(
        ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )
    try:
        for part in encoder.iterencode(message):
            if len(part) > MAX_FRAME_BYTES - len(body):
                raise ProtocolError("Frame demasiado grande")
            encoded = part.encode("utf-8", errors="strict")
            if len(encoded) > MAX_FRAME_BYTES - len(body):
                raise ProtocolError("Frame demasiado grande")
            body.extend(encoded)
    except (ValueError, OverflowError, RecursionError, UnicodeError):
        raise ProtocolError("JSON no codificable dentro del límite") from None
    return struct.pack("!I", len(body)) + body


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("Clave JSON duplicada")
        result[key] = value
    return result


def _constant(_value):
    raise ProtocolError("Constante JSON no finita")


def _body(body):
    try:
        message = json.loads(
            bytes(body).decode("utf-8", errors="strict"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise ProtocolError("JSON UTF-8 inválido") from None
    _envelope(message)
    return message


def decode(frame: bytes) -> dict:
    """Un único frame completo, sin estado de sesión ni aceptación implícita."""
    if type(frame) not in (bytes, bytearray, memoryview):
        raise ProtocolError("Frame debe contener bytes")
    try:
        frame = memoryview(frame).cast("B")
    except (TypeError, ValueError):
        raise ProtocolError("Vista de bytes inválida") from None
    if len(frame) < 4:
        raise ProtocolError("Prefijo truncado")
    size = struct.unpack("!I", frame[:4])[0]
    if not 0 < size <= MAX_FRAME_BYTES:
        raise ProtocolError("Longitud de frame inválida")
    if len(frame) != size + 4:
        raise ProtocolError("Frame truncado o bytes sobrantes")
    return _body(frame[4:])


class Session:
    """Validador por dirección emisora parent/child; commit después de validar.

    accept recibe el tamaño wire real, prefijo incluido, del decoder/encoder.
    mark_stopping exige un hecho explícito del supervisor: stop o liveness.
    No comprueba ese hecho físico; closed no acredita recursos devueltos.
    """

    def __init__(self, execution_id: str, epoch: str, direction: str):
        _identity(execution_id, epoch)
        if type(direction) is not str or direction not in ("parent", "child"):
            raise ProtocolError("Dirección inválida")
        self.execution_id, self.epoch, self.direction = execution_id, epoch, direction
        self.frames = self.total_bytes = self.progress_count = (
            self.take_result_count
        ) = 0
        self._ready = self._request = self._stopping = self._result = self._closed = (
            False
        )

    def mark_stopping(self, reason="stop") -> None:
        if reason not in ("stop", "liveness"):
            raise ProtocolError("Contexto de parada inválido")
        self._stopping = True

    def check_size(self, wire_bytes: int) -> None:
        if type(wire_bytes) is not int or not 4 < wire_bytes <= MAX_FRAME_BYTES + 4:
            raise ProtocolError("Tamaño wire inválido")
        if self.frames >= MAX_FRAMES or self.total_bytes + wire_bytes > MAX_TOTAL_BYTES:
            raise ProtocolError("Presupuesto de dirección excedido")

    def accept(self, message: dict, wire_bytes: int) -> dict:
        _envelope(message)
        if (
            message["execution_id"] != self.execution_id
            or message["epoch"] != self.epoch
        ):
            raise ProtocolError("Correlación de ejecución distinta")
        if message["seq"] != self.frames + 1:
            raise ProtocolError("Secuencia no contigua")
        self.check_size(wire_bytes)
        kind = Kind(message["kind"])
        if self.direction == "parent":
            if kind not in (Kind.REQUEST, Kind.STOP):
                raise ProtocolError("Mensaje ajeno a dirección parent")
            if self._stopping or (kind == Kind.REQUEST and self._request):
                raise ProtocolError("Orden parent inválido")
        else:
            if kind not in (
                Kind.READY,
                Kind.PROGRESS,
                Kind.TAKE_RESULT,
                Kind.RESULT,
                Kind.CLOSED,
            ):
                raise ProtocolError("Mensaje ajeno a dirección child")
            if self._closed or (self._result and kind != Kind.CLOSED):
                raise ProtocolError("Mensaje después de terminal global")
            if kind == Kind.READY and self._ready:
                raise ProtocolError("Ready repetido")
            if (
                kind != Kind.READY
                and not self._ready
                and not (kind == Kind.CLOSED and self._stopping)
            ):
                raise ProtocolError("Ready requerido")
            if kind == Kind.CLOSED and not (self._result or self._stopping):
                raise ProtocolError("Closed sin result o parada explícita")
            if kind == Kind.PROGRESS and self.progress_count >= MAX_PROGRESS:
                raise ProtocolError("Demasiados progress")
            if kind == Kind.TAKE_RESULT and self.take_result_count >= MAX_TAKE_RESULTS:
                raise ProtocolError("Demasiados take_result")
        self.frames += 1
        self.total_bytes += wire_bytes
        self.progress_count += kind == Kind.PROGRESS
        self.take_result_count += kind == Kind.TAKE_RESULT
        self._ready |= kind == Kind.READY
        self._request |= kind == Kind.REQUEST
        self._stopping |= kind == Kind.STOP
        self._result |= kind == Kind.RESULT
        self._closed |= kind == Kind.CLOSED
        return message


class Decoder:
    """Incremental: retiene como máximo un cuerpo + prefijo (262148 bytes).

    memoryview no copia el chunk: el prefijo se inspecciona antes del cuerpo.
    El total por dirección es independiente. Tras error queda inutilizable,
    conservando cuentas aceptadas. El llamador posee el chunk y mensajes
    entregados; no se encolan aquí. No prueba ReadFile ni pipes físicos.
    """

    def __init__(self, session: Session):
        self.session = session
        self._buffer = bytearray()
        self._size = None
        self._failed = self._finished = self._feeding = False

    @property
    def retained_bytes(self):
        return len(self._buffer)

    def feed(self, chunk):
        """Iterar hasta terminar: yields preceden a fallos de frames siguientes."""
        if self._failed or self._finished or self._feeding:
            raise ProtocolError("Decoder no disponible")
        self._feeding = True
        try:
            if type(chunk) not in (bytes, bytearray, memoryview):
                raise ProtocolError("Chunk debe contener bytes")
            try:
                data = memoryview(chunk).cast("B")
            except (TypeError, ValueError):
                raise ProtocolError("Vista de bytes inválida") from None
            offset = 0
            while offset < len(data):
                target = 4 if self._size is None else self._size + 4
                count = min(target - len(self._buffer), len(data) - offset)
                self._buffer.extend(data[offset : offset + count])
                offset += count
                if self._size is None and len(self._buffer) == 4:
                    size = struct.unpack("!I", self._buffer)[0]
                    if not 0 < size <= MAX_FRAME_BYTES:
                        raise ProtocolError("Longitud de frame inválida")
                    self.session.check_size(size + 4)
                    self._size = size
                if self._size is not None and len(self._buffer) == self._size + 4:
                    message = _body(memoryview(self._buffer)[4:])
                    self.session.accept(message, self._size + 4)
                    self._buffer = bytearray()
                    self._size = None
                    yield message
        except ProtocolError:
            self._failed = True
            self._buffer = bytearray()
            raise
        finally:
            self._feeding = False

    def finish(self) -> None:
        """EOF explícito: prefijo/cuerpo parcial es error, incluso tras reader=0."""
        if self._failed or self._feeding:
            raise ProtocolError("Decoder no disponible al terminar")
        if self._buffer:
            self._failed = True
            raise ProtocolError("EOF con frame incompleto")
        self._finished = True

    end_of_input = finish
