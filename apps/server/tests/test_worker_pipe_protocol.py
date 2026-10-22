"""IPC privado puro: límites, entrega parcial y estado transaccional."""

import json
import struct

import pytest
from app.worker.pipe_protocol import (
    MAX_FRAME_BYTES,
    MAX_TOTAL_BYTES,
    Decoder,
    Kind,
    ProtocolError,
    Session,
    decode,
    encode,
)

ID = "01M49HZQ7K5WFE9PA1N3WDN92K"
EPOCH = "private-epoch_1"


def message(kind="ready", seq=1, payload=None, **changes):
    result = {
        "version": 1,
        "execution_id": ID,
        "epoch": EPOCH,
        "seq": seq,
        "kind": kind,
        "payload": {} if payload is None else payload,
    }
    result.update(changes)
    return result


def wire(value):
    body = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode()
    return struct.pack("!I", len(body)) + body


def raw(body):
    return struct.pack("!I", len(body)) + body


def test_nonfinite_encoder_red():
    with pytest.raises(ProtocolError):
        encode(message(payload={"x": float("nan")}))


def test_duplicates_red():
    body = json.dumps(message()).replace('"payload": {}', '"payload": {"x":1,"x":2}')
    with pytest.raises(ProtocolError):
        decode(raw(body.encode()))


def test_sequence_red():
    session = Session(ID, EPOCH, "child")
    with pytest.raises(ProtocolError):
        session.accept(message(seq=2), 100)
    assert session.frames == session.total_bytes == 0


def test_oversize_before_copy_red():
    decoder = Decoder(Session(ID, EPOCH, "child"))
    with pytest.raises(ProtocolError):
        list(decoder.feed(struct.pack("!I", MAX_FRAME_BYTES + 1) + b"x" * 1000000))
    assert decoder.retained_bytes <= 4
    assert decoder.session.frames == 0


def test_fragment_eof_red():
    decoder = Decoder(Session(ID, EPOCH, "child"))
    list(decoder.feed(b"\x00"))
    with pytest.raises(ProtocolError):
        decoder.finish()


def test_terminal_repetition_red():
    session = Session(ID, EPOCH, "child")
    session.accept(message(), 100)
    session.accept(message("result", 2), 100)
    with pytest.raises(ProtocolError):
        session.accept(message("result", 3), 100)
    assert session.frames == 2


@pytest.mark.parametrize("step", [1, 2, 3, 4, 5, 7, 1000000])
def test_fragmented_multiple_frames(step):
    messages = [
        message(),
        message("take_result", 2),
        message("result", 3),
        message("closed", 4),
    ]
    stream = b"".join(encode(m) for m in messages)
    decoder = Decoder(Session(ID, EPOCH, "child"))
    actual = []
    for i in range(0, len(stream), step):
        actual.extend(decoder.feed(stream[i : i + step]))
        assert decoder.retained_bytes <= MAX_FRAME_BYTES + 4
    decoder.end_of_input()
    assert actual == messages
    assert decoder.session.frames == 4
    assert decoder.session.total_bytes == len(stream)


@pytest.mark.parametrize("split", [1, 2, 3, 4])
def test_prefix_split(split):
    data = encode(message())
    d = Decoder(Session(ID, EPOCH, "child"))
    assert list(d.feed(data[:split])) == []
    assert list(d.feed(data[split:])) == [message()]
    d.finish()


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", True),
        ("version", 1.0),
        ("version", 2),
        ("seq", True),
        ("seq", 1.0),
        ("seq", 0),
        ("seq", -1),
        ("execution_id", "8" + ID[1:]),
        ("execution_id", ID.lower()),
        ("execution_id", ID[:-1]),
        ("execution_id", 1),
        ("epoch", ""),
        ("epoch", "x" * 129),
        ("epoch", "a\n"),
        ("epoch", 1),
        ("kind", "unknown"),
        ("kind", 1),
        ("payload", []),
        ("payload", None),
        ("payload", "text"),
    ],
)
def test_strict_envelope(field, value):
    m = message()
    m[field] = value
    with pytest.raises(ProtocolError):
        encode(m)
    with pytest.raises(ProtocolError):
        decode(wire(m))


def test_exact_fields_and_kind_enum():
    assert encode(message(kind=Kind.READY)) == encode(message())
    for m in [
        dict(message(), extra=1),
        {k: v for k, v in message().items() if k != "seq"},
        [],
        object(),
    ]:
        with pytest.raises(ProtocolError):
            encode(m)


@pytest.mark.parametrize(
    "payload",
    [
        {"x": float("inf")},
        {"x": -float("inf")},
        {"x": (1, 2)},
        {"x": object()},
        {1: "bad"},
        {"x": "x" * 8193},
        {"x": "\ud800"},
        {"\udfff": 1},
        {"x": list(range(257))},
        {str(i): i for i in range(257)},
        {"x": lambda: 1},
    ],
)
def test_bounded_json_encoder(payload):
    with pytest.raises(ProtocolError):
        encode(message(payload=payload))


@pytest.mark.parametrize(
    "key",
    [
        "engine_token",
        "password",
        "Authorization",
        "api-key",
        "private_key",
        "credential",
        "ciphertext",
        "secret",
        "headers",
        "entrypoint",
        "dynamic_import",
        "model_code",
        "raw_model_code",
    ],
)
def test_recursive_forbidden_keys(key):
    with pytest.raises(ProtocolError):
        encode(message(payload={"nested": [{key: "value"}]}))
    with pytest.raises(ProtocolError):
        decode(wire(message(payload={"nested": [{key: "value"}]})))


def test_cycles_depth_and_giant_integer_typed():
    cycle = []
    cycle.append(cycle)
    deep = {}
    for _ in range(1000):
        deep = {"x": deep}
    for value in [cycle, deep, 1 << 1000000]:
        with pytest.raises(ProtocolError):
            encode(message(payload={"x": value}))


def test_valid_json_boundaries_and_seed():
    value = {
        "s": "😀" * 8192,
        "items": list(range(256)),
        "seed": 2**80,
        "values": [None, True, False, 1, -2, 1.5, "\n"],
    }
    assert decode(encode(message(payload=value))) == message(payload=value)
    deep = 1
    for _ in range(19):
        deep = [deep]
    assert decode(encode(message(payload={"x": deep}))) == message(payload={"x": deep})
    with pytest.raises(ProtocolError):
        encode(message(payload={"x": [deep]}))


@pytest.mark.parametrize(
    "text",
    [
        '{"x":1,"x":2}',
        '{"x":[{"a":1,"a":2}]}',
        '{"x":NaN}',
        '{"x":Infinity}',
        '{"x":-Infinity}',
        '{"x":1e999}',
        '{"x":"\\ud800"}',
        '{"\\udfff":1}',
    ],
)
def test_malicious_json_parse(text):
    body = json.dumps(message()).replace('"payload": {}', '"payload": ' + text)
    with pytest.raises(ProtocolError):
        decode(raw(body.encode()))


def test_duplicate_envelope_and_deep_parser():
    body = json.dumps(message()).replace('"version": 1', '"version":1,"version":1')
    for data in [
        body.encode(),
        b"[" * 2000 + b"0" + b"]" * 2000,
        b"{} garbage",
        b"",
        b"\xff",
    ]:
        with pytest.raises(ProtocolError):
            decode(raw(data))


@pytest.mark.parametrize("cut", [1, 2, 3, 4, 5, -1])
def test_truncated_eof(cut):
    data = encode(message())[:cut]
    d = Decoder(Session(ID, EPOCH, "child"))
    assert list(d.feed(data)) == []
    with pytest.raises(ProtocolError):
        d.finish()
    with pytest.raises(ProtocolError):
        decode(data)


def sized_message(size, kind="progress", seq=2):
    m = message(kind, seq, {str(i): "x" * 8000 for i in range(32)})
    base = len(encode(m)) - 4
    m["payload"]["padding"] = "x" * (size - base - len(',"padding":""'))
    assert len(encode(m)) == size + 4
    return m


def test_exact_max_frame_and_oversize_encoder_decoder():
    m = sized_message(MAX_FRAME_BYTES)
    assert decode(encode(m)) == m
    m["payload"]["padding"] += "x"
    with pytest.raises(ProtocolError):
        encode(m)
    with pytest.raises(ProtocolError):
        decode(wire(m))
    with pytest.raises(ProtocolError):
        decode(encode(message()) + encode(message()))


@pytest.mark.parametrize(
    "changes",
    [
        {"execution_id": "01M49HZQ7K5WFE9PA1N3WDN92M"},
        {"epoch": "other"},
        {"seq": 2},
        {"seq": True},
    ],
)
def test_correlation_rejection_atomic(changes):
    s = Session(ID, EPOCH, "child")
    with pytest.raises(ProtocolError):
        s.accept(message(**changes), 100)
    assert s.frames == s.total_bytes == s.progress_count == s.take_result_count == 0
    s.accept(message(), 100)
    assert s.frames == 1


@pytest.mark.parametrize(
    "direction,kinds",
    [
        ("parent", ["ready", "progress", "take_result", "result", "closed"]),
        ("child", ["request", "stop"]),
    ],
)
def test_direction_enforced(direction, kinds):
    for kind in kinds:
        s = Session(ID, EPOCH, direction)
        with pytest.raises(ProtocolError):
            s.accept(message(kind), 100)
        assert s.frames == 0


def test_parent_request_stop_order():
    s = Session(ID, EPOCH, "parent")
    s.accept(message("request"), 100)
    with pytest.raises(ProtocolError):
        s.accept(message("request", 2), 100)
    s.accept(message("stop", 2), 100)
    with pytest.raises(ProtocolError):
        s.accept(message("stop", 3), 100)
    s = Session(ID, EPOCH, "parent")
    s.accept(message("stop"), 100)
    with pytest.raises(ProtocolError):
        s.accept(message("request", 2), 100)


def test_child_order_and_explicit_stopping():
    for kind in ["progress", "take_result", "result", "closed"]:
        with pytest.raises(ProtocolError):
            Session(ID, EPOCH, "child").accept(message(kind), 100)
    s = Session(ID, EPOCH, "child")
    s.accept(message(), 100)
    for kind in ["ready", "closed"]:
        with pytest.raises(ProtocolError):
            s.accept(message(kind, 2), 100)
    s.mark_stopping()
    s.accept(message("closed", 2), 100)
    with pytest.raises(ProtocolError):
        s.accept(message("closed", 3), 100)
    s = Session(ID, EPOCH, "child")
    s.mark_stopping()
    s.accept(message("closed"), 100)
    for reason in ["stop", "liveness"]:
        s = Session(ID, EPOCH, "child")
        s.mark_stopping(reason)
        s.accept(message("closed"), 100)
    with pytest.raises(ProtocolError):
        Session(ID, EPOCH, "child").mark_stopping("guess")


def test_64_siblings_then_one_global_result():
    s = Session(ID, EPOCH, "child")
    s.accept(message(), 100)
    for seq in range(2, 66):
        s.accept(message("take_result", seq, {"output_index": seq - 2}), 100)
    assert s.take_result_count == 64
    with pytest.raises(ProtocolError):
        s.accept(message("take_result", 66), 100)
    for seq in range(66, 130):
        s.accept(message("progress", seq), 100)
    with pytest.raises(ProtocolError):
        s.accept(message("progress", 130), 100)
    s.accept(message("result", 130), 100)
    for kind in ["progress", "take_result", "ready", "result"]:
        with pytest.raises(ProtocolError):
            s.accept(message(kind, 131), 100)
    s.accept(message("closed", 131), 100)
    assert s.frames == 131
    with pytest.raises(ProtocolError):
        s.accept(message("closed", 132), 100)


def test_frame_and_total_budget_atomic():
    s = Session(ID, EPOCH, "child")
    # Las cuentas recibidas son tamaños wire, incluyendo prefijo.
    s.accept(message(), MAX_FRAME_BYTES + 4)
    for seq in range(2, 16):
        s.accept(message("progress", seq), MAX_FRAME_BYTES + 4)
    remaining = MAX_TOTAL_BYTES - s.total_bytes
    s.accept(message("progress", 16), remaining)
    before = (s.frames, s.total_bytes, s.progress_count)
    with pytest.raises(ProtocolError):
        s.accept(message("result", 17), 1)
    assert (s.frames, s.total_bytes, s.progress_count) == before
    # Límite global independiente: estado ya al tope simula límite de recepción.
    s = Session(ID, EPOCH, "child")
    s.frames = 132
    with pytest.raises(ProtocolError):
        s.accept(message(seq=133), 100)


def test_decoder_total_budget_before_body_copy():
    s = Session(ID, EPOCH, "child")
    d = Decoder(s)
    data = encode(message())
    assert list(d.feed(data)) == [message()]
    s.total_bytes = MAX_TOTAL_BYTES - 4
    with pytest.raises(ProtocolError):
        list(d.feed(encode(message("progress", 2))))
    assert d.retained_bytes <= 4
    assert s.frames == 1


def test_valid_before_invalid_delivery_retained():
    s = Session(ID, EPOCH, "child")
    d = Decoder(s)
    iterator = d.feed(encode(message()) + wire(message("progress", 3)))
    assert next(iterator) == message()
    with pytest.raises(ProtocolError):
        next(iterator)
    assert s.frames == 1
    assert s.total_bytes == len(encode(message()))
    with pytest.raises(ProtocolError):
        list(d.feed(b""))
    with pytest.raises(ProtocolError):
        d.finish()


def test_decoder_types_finish_and_failure_latch():
    for value in ["bytes", None, [1]]:
        d = Decoder(Session(ID, EPOCH, "child"))
        with pytest.raises(ProtocolError):
            list(d.feed(value))
    for value in [bytearray(encode(message())), memoryview(encode(message()))]:
        d = Decoder(Session(ID, EPOCH, "child"))
        assert list(d.feed(value)) == [message()]
        d.finish()
        with pytest.raises(ProtocolError):
            list(d.feed(b""))
    d = Decoder(Session(ID, EPOCH, "child"))
    d.finish()  # EOF sólo afirma frontera de bytes, no custodia ni result obligatorio.
    d.finish()


@pytest.mark.parametrize(
    "args", [("bad", EPOCH, "child"), (ID, "", "child"), (ID, EPOCH, "both")]
)
def test_invalid_session_configuration(args):
    with pytest.raises(ProtocolError):
        Session(*args)


@pytest.mark.parametrize("size", [True, -1, 0, MAX_FRAME_BYTES + 5, 1.5])
def test_invalid_accounting_size(size):
    s = Session(ID, EPOCH, "child")
    with pytest.raises(ProtocolError):
        s.accept(message(), size)
    assert s.frames == s.total_bytes == 0


def test_payload_is_json_not_domain_authority():
    # Finite JSON mal formado para PerTakeResult se entrega: el padre lo valida aparte.
    m = message("take_result", 2, {"status": "invented", "seed": 2**80})
    d = Decoder(Session(ID, EPOCH, "child"))
    assert list(d.feed(encode(message()) + encode(m))) == [message(), m]


def test_decode_noncontiguous_view_is_typed():
    value = memoryview(b"abcdefgh")[::2]
    with pytest.raises(ProtocolError):
        decode(value)


def test_actual_four_mib_wire_success_then_reject_before_copy():
    s = Session(ID, EPOCH, "child")
    d = Decoder(s)
    first = encode(message())
    assert list(d.feed(first)) == [message()]
    for seq in range(2, 17):
        m = sized_message(MAX_FRAME_BYTES, seq=seq)
        assert list(d.feed(encode(m))) == [m]
    remaining_body = MAX_TOTAL_BYTES - s.total_bytes - 4
    last = sized_message(remaining_body, seq=17)
    assert list(d.feed(encode(last))) == [last]
    assert s.total_bytes == MAX_TOTAL_BYTES
    assert s.frames == 17
    with pytest.raises(ProtocolError):
        list(d.feed(encode(message("result", 18))))
    assert s.total_bytes == MAX_TOTAL_BYTES
    assert s.frames == 17
    assert d.retained_bytes <= 4


def test_131_actual_frames_with_64_progress_and_64_siblings():
    messages = [message()]
    messages += [message("progress", i) for i in range(2, 66)]
    messages += [message("take_result", i) for i in range(66, 130)]
    messages += [message("result", 130), message("closed", 131)]
    d = Decoder(Session(ID, EPOCH, "child"))
    assert list(d.feed(b"".join(encode(m) for m in messages))) == messages
    assert d.session.frames == 131
    assert d.session.progress_count == d.session.take_result_count == 64
    d.finish()


def test_multibyte_byte_budget_and_native_integer_encoding_error():
    for m in [
        message(payload={str(i): "😀" * 8192 for i in range(9)}),
        message(payload={"seed": 1 << 20000}),
        message(seq=1 << 1000000),
    ]:
        with pytest.raises(ProtocolError):
            encode(m)


def test_invalid_utf8_in_incremental_body():
    d = Decoder(Session(ID, EPOCH, "child"))
    with pytest.raises(ProtocolError):
        list(d.feed(raw(b"\xff")))
    assert d.session.frames == d.session.total_bytes == 0


def test_concurrent_iteration_and_pending_finish_rejected():
    d = Decoder(Session(ID, EPOCH, "child"))
    iterator = d.feed(encode(message()) + encode(message("result", 2)))
    assert next(iterator) == message()
    with pytest.raises(ProtocolError):
        list(d.feed(b""))
    with pytest.raises(ProtocolError):
        d.finish()
    assert list(iterator) == [message("result", 2)]
    d.finish()


def test_noncontiguous_feed_latched_without_acceptance():
    d = Decoder(Session(ID, EPOCH, "child"))
    with pytest.raises(ProtocolError):
        list(d.feed(memoryview(b"abcdefgh")[::2]))
    assert d.session.frames == d.session.total_bytes == 0


def test_decoder_prefix_zero_rejected_before_large_body():
    d = Decoder(Session(ID, EPOCH, "child"))
    with pytest.raises(ProtocolError):
        list(d.feed(b"\0" * 1000000))
    assert d.retained_bytes <= 4
    assert d.session.frames == 0
