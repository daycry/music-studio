"""Transporte aditivo de prefijos; la política y el auditor v3 son independientes.

El binding procede del bootstrap propio, nunca de una ruta de RPC. Una sola
transacción publica posiciones/hash después de validar bytes y anclas nuevas.
"""

import json
from collections.abc import Sequence
from itertools import chain

from benchmark_plan import digest

TRANSPORT = "wddm_audit_delta_v1"
COLLECTIONS = ("receipts", "attempts", "records")
LIMIT = 64 * 1024**2


class ExtendedPrefix(Sequence):
    """Vista de validación sin copiar el historial ni publicarlo antes del commit."""

    def __init__(self, prefix, suffix):
        self.prefix, self.suffix = prefix, suffix

    def __len__(self):
        return len(self.prefix) + len(self.suffix)

    def __iter__(self):
        return chain(self.prefix, self.suffix)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return (
            self.prefix[index]
            if index < len(self.prefix)
            else self.suffix[index - len(self.prefix)]
        )

    def __eq__(self, other):
        return (
            isinstance(other, Sequence)
            and len(self) == len(other)
            and all(a == b for a, b in zip(self, other, strict=True))
        )


def positions(value):
    return {name: len(value[name]) for name in COLLECTIONS}


def prefix_hash(previous, stream, sequence, first, last, segment_hash):
    return digest(
        {
            "transport": TRANSPORT,
            "stream": stream,
            "sequence": sequence,
            "previous": previous,
            "first": first,
            "last": last,
            "segment_sha256": segment_hash,
        }
    )


class AuditPrefix:
    def __init__(self, binding, validate):
        self.binding = binding
        self.validate = validate
        self.value = {
            "root": binding["root"],
            "context": binding["context"],
            **{name: [] for name in COLLECTIONS},
        }
        self.sequence = 0
        self.prefix = digest({"transport": TRANSPORT, "binding": binding})
        self.pending = None
        self.anchor = None

    def status(self):
        return {
            "transport": TRANSPORT,
            "stream": self.binding["stream"],
            "sequence": self.sequence,
            "prefix": self.prefix,
            "positions": positions(self.value),
            "validated": len(self.value["receipts"]),
            "supervisor_anchor_sha256": self.anchor,
            "audit_only": True,
        }

    def begin(self, header):
        if self.pending is not None:
            raise ValueError("delta_incomplete_segment_pending")
        self.pending = None
        if (
            header.get("transport") != TRANSPORT
            or header.get("stream") != self.binding["stream"]
            or header.get("sequence") != self.sequence + 1
            or type(header.get("sequence")) is not int
            or header.get("previous") != self.prefix
            or header.get("first") != positions(self.value)
        ):
            raise ValueError("delta_prefix_identity_invalid")
        first, last = header["first"], header["last"]
        if set(last) != set(COLLECTIONS) or any(
            type(first[n]) is not int or type(last[n]) is not int or last[n] < first[n]
            for n in COLLECTIONS
        ):
            raise ValueError("delta_positions_invalid")
        if (
            first == last
            or type(header.get("characters")) is not int
            or not 0 < header["characters"] <= LIMIT
        ):
            raise ValueError("delta_bound_or_empty_invalid")
        if header.get("prefix") != prefix_hash(
            self.prefix,
            self.binding["stream"],
            header["sequence"],
            first,
            last,
            header["sha256"],
        ):
            raise ValueError("delta_chain_invalid")
        self.pending = {"header": dict(header), "fragments": [], "length": 0}
        return {"started": True}

    def fragment(self, args):
        pending = self.pending
        if pending is None:
            raise ValueError("delta_segment_not_started")
        text = args.get("text")
        if (
            type(args.get("index")) is not int
            or args["index"] != len(pending["fragments"])
            or not isinstance(text, str)
            or len(text) > 1200
        ):
            self.pending = None
            raise ValueError("delta_fragment_order_invalid")
        if pending["length"] + len(text) > pending["header"]["characters"]:
            self.pending = None
            raise ValueError("delta_fragment_overflow")
        pending["fragments"].append(text)
        pending["length"] += len(text)
        return {"received": args["index"]}

    def commit(self):
        pending, self.pending = self.pending, None
        if pending is None or pending["length"] != pending["header"]["characters"]:
            raise ValueError("delta_segment_incomplete")
        header = pending["header"]
        segment = json.loads("".join(pending["fragments"]))
        if digest(segment) != header["sha256"] or set(segment) != set(COLLECTIONS):
            raise ValueError("delta_segment_seal_invalid")
        if any(
            not isinstance(segment[n], list)
            or len(segment[n]) != header["last"][n] - header["first"][n]
            for n in COLLECTIONS
        ):
            raise ValueError("delta_segment_positions_invalid")
        staged = {
            **self.value,
            **{
                name: ExtendedPrefix(self.value[name], segment[name])
                for name in COLLECTIONS
            },
        }
        self.validate(staged, segment)
        # El worker sólo despacha una llamada a la vez; tras validar se publica
        # el segmento completo y su identidad, sin exponer una vista preparada.
        for name in COLLECTIONS:
            self.value[name].extend(segment[name])
        self.sequence = header["sequence"]
        self.prefix = header["prefix"]
        self.anchor = header["prefix"]
        return self.status()


def segment_header(status, segment):
    serialized = json.dumps(
        segment, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    )
    first = status["positions"]
    last = {name: first[name] + len(segment[name]) for name in COLLECTIONS}
    sequence = status["sequence"] + 1
    seal = digest(segment)
    header = {
        "transport": TRANSPORT,
        "stream": status["stream"],
        "sequence": sequence,
        "previous": status["prefix"],
        "first": first,
        "last": last,
        "sha256": seal,
        "characters": len(serialized),
        "prefix": prefix_hash(
            status["prefix"], status["stream"], sequence, first, last, seal
        ),
    }
    return header, serialized
