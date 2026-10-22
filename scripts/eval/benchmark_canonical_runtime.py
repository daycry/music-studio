"""Autoridad aislada opt-in: bootstrap privado, dos carriles y scheduler único.

Confía en código supervisor y en el SO; no aísla a usuarios con acceso a memoria.
No integra EpisodeAcquirer, runtime, rows, packs ni FINAL. Ningún dict del caller
crea autoridad: el canal congela exclusivamente una respuesta real del sensor.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.machinery
import importlib.util
import os
import queue
import secrets
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from benchmark_clock import utc_now
from benchmark_process import (
    MAX_PROGRESS,
    MAX_REQUEST,
    RESERVE_NS,
    OwnedProcess,
    WorkerDeadline,
    WorkerFailure,
    decode,
    encode,
    kernel,
)

MODE = "canonical_mux_v1"
MAX_CHARACTERS = 64 * 1024 * 1024
FRAGMENT = 1200
INGEST = {"challenge", "ingest", "begin", "fragment", "end", "publish", "confirm"}
READ = {"status", "base"}


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _factory_hash(reference):
    name = reference.rsplit(":", 1)[0]
    path = (
        Path(name)
        if name.endswith(".py")
        else Path(importlib.util.find_spec(name).origin)
    )
    path = path.resolve()
    if not path.is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("handler_outside_repository")
    return _hash(path.read_bytes())


def _sealed_factory(reference, seal):
    module_name, attribute = reference.rsplit(":", 1)
    path = (
        Path(module_name)
        if module_name.endswith(".py")
        else Path(importlib.util.find_spec(module_name).origin)
    )
    path = path.resolve()
    if not path.is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("handler_outside_repository")
    source = path.read_bytes()
    if _hash(source) != seal:
        raise ValueError("canonical_factory_source_changed")
    name = "trusted_mux_" + seal

    class SealedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            return compile(source, str(path), "exec")

    spec = importlib.util.spec_from_file_location(
        name, path, loader=SealedLoader(name, str(path))
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Execute precisely the source bytes hashed above, never cached bytecode.
    spec.loader.exec_module(module)
    return getattr(module, attribute)


def _signed(value, key):
    return {**value, "mac": hmac.new(key, encode(value), hashlib.sha256).hexdigest()}


def _verified(frame, key, epoch, binding, *, reply=False):
    names = {"epoch", "binding", "lane", "seq", "index", "payload"}
    names |= {"type"} if reply else {"deadline_ns"}
    if not isinstance(frame, dict) or set(frame) != names | {"mac"}:
        raise ValueError("closed_authenticated_frame_required")
    value = {k: v for k, v in frame.items() if k != "mac"}
    if not isinstance(frame["mac"], str) or not hmac.compare_digest(
        frame["mac"], _signed(value, key)["mac"]
    ):
        raise ValueError("frame_authentication_failed")
    if (
        value["epoch"] != epoch
        or value["binding"] != binding
        or value["lane"] not in {"ingest", "read"}
        or type(value["seq"]) is not int
        or value["seq"] <= 0
        or type(value["index"]) is not int
        or value["index"] < 0
    ):
        raise ValueError("frame_session_binding_invalid")
    if not reply and type(value["deadline_ns"]) is not int:
        raise ValueError("deadline_invalid")
    return value


class ReplySlot(queue.Queue):
    """64 progresos por secuencia, terminal y aviso de fallo reservados."""

    def __init__(self):
        super().__init__(maxsize=MAX_PROGRESS + 2)
        self.next_index = 0
        self.terminal = False
        self.wire_progress = []

    def admit(self, value, *, before_error=None):
        if self.terminal or value["index"] != self.next_index:
            raise ValueError("stale_or_reordered_reply")
        kind = value["type"]
        if not isinstance(kind, str) or kind not in {"progress", "result", "error"}:
            raise ValueError("invalid_reply_type")
        if kind == "progress":
            if value["lane"] != "read":
                raise ValueError("ingest_progress_forbidden")
            if len(self.wire_progress) >= MAX_PROGRESS:
                raise ValueError("progress_limit")
            self.wire_progress.append(value)
        else:
            self.terminal = True
        self.next_index += 1
        if kind == "error" and before_error is not None:
            before_error(value)
        self.put_nowait(value)


def _mux_failure(error, progress, evidence):
    # The legacy exception constructor consumes value. Keep authenticated wire
    # metadata separate from this explicitly labelled internal adapter.
    normalized = [{"value": frame["payload"]} for frame in progress]
    cls = WorkerDeadline if isinstance(error, WorkerDeadline) else WorkerFailure
    failure = cls(
        str(error),
        progress=normalized,
        evidence={
            **evidence,
            "progress_protocol": MODE,
            "normalized_progress": normalized,
            "normalized_progress_semantics": "internal payload-to-value adapter; not wire",
        },
    )
    failure.progress = list(progress)
    return failure


class ParentMux:
    """Writer de un frame y waiters independientes; nunca adquiere el lock RPC."""

    def __init__(self, owned):
        self.owned = owned
        self.key = secrets.token_bytes(32)
        self.epoch = secrets.token_hex(16)
        self.binding = ""
        self.control = threading.Lock()
        self.slots = {}
        self.sequences = {"ingest": 0, "read": 0}
        self.outgoing = queue.Queue(maxsize=2)
        self.failure = None
        self.live = False
        self._remote_error = None
        self._drain_deadline_ns = 0

    def gate(self, config, reference):
        self.binding = _hash(encode(config, MAX_REQUEST))
        if "bootstrap_path" in config:
            data = Path(config["bootstrap_path"]).read_bytes()
            if _hash(data) != config["bootstrap_sha256"]:
                raise ValueError("canonical_prebound_file_changed")
            self.epoch = decode(data)["epoch"]
        return encode(
            {
                "gate": True,
                "mode": MODE,
                "handler": reference,
                "source_sha256": _factory_hash(reference),
                "config": config,
                "binding": self.binding,
                "epoch": self.epoch,
                "key": self.key.hex(),
            },
            MAX_REQUEST,
        )

    def activate(self, deadline):
        writer = threading.Thread(target=self._write, name="canonical-frame-writer")
        self.owned._writers.append(writer)
        writer.start()
        challenge = secrets.token_hex(32)
        value = self.call(
            {
                "operation": "challenge",
                "arguments": {
                    "challenge": challenge,
                    "ownership": self.owned.ownership,
                },
            },
            deadline_ns=deadline,
        )["value"]
        if value != {"challenge": challenge, "ownership": self.owned.ownership}:
            raise WorkerFailure("canonical_birth_challenge_invalid")
        self.live = True

    def _write(self):
        while not self.owned.closed and self.failure is None:
            try:
                frame = self.outgoing.get(timeout=0.01)
            except queue.Empty:
                continue
            try:
                written = self.owned.process.stdin.write(frame)
                if written != len(frame):
                    raise OSError("partial_pipe_write")
            except (OSError, ValueError) as error:
                self.fail(error)
                return

    def fail(self, error):
        with self.control:
            if self.failure is not None:
                return
            self.failure = error
            self.live = False
            for slot in self.slots.values():
                try:
                    slot.put_nowait(self.failure)
                except queue.Full:
                    pass  # Existing reply is checked against failure before return.

    def deliver(self, frame):
        encode(frame)  # Independent receiver byte quota, including envelope/MAC.
        value = _verified(frame, self.key, self.epoch, self.binding, reply=True)
        with self.control:
            if self.failure is not None:
                if (
                    self._remote_error
                    and (value["lane"], value["seq"]) == self._remote_error[:2]
                ):
                    raise ValueError("stale_or_reordered_reply")
                raise ValueError("epoch_revoked")
            slot = self.slots.get((value["lane"], value["seq"]))
            if slot is None:
                raise ValueError("foreign_or_replayed_reply")

            # Authentication, sequence/type/quota admission precede revocation.
            # Commit under control BEFORE queue publication wakes any caller.
            def revoke(error_frame):
                self._remote_error = (value["lane"], value["seq"], encode(error_frame))
                self._drain_deadline_ns = min(
                    slot.deadline_ns, time.perf_counter_ns() + 220_000_000
                )
                self.failure = WorkerFailure(str(error_frame["payload"]))
                self.live = False
                for other in self.slots.values():
                    if other is not slot:
                        try:
                            other.put_nowait(self.failure)
                        except queue.Full:
                            pass

            slot.admit(value, before_error=revoke)

    def call(self, payload, *, deadline_ns):
        if type(deadline_ns) is not int:
            raise ValueError("deadline_invalid")
        if not isinstance(payload, dict) or set(payload) - {"operation", "arguments"}:
            raise ValueError("closed_operation_payload_required")
        operation = payload.get("operation")
        if not isinstance(operation, str) or operation not in INGEST | READ:
            raise ValueError("unknown_canonical_operation")
        if not self.live and operation != "challenge":
            raise WorkerFailure("canonical_not_live")
        lane = "ingest" if operation in INGEST else "read"
        started, started_utc = time.perf_counter_ns(), utc_now()
        cutoff = deadline_ns - RESERVE_NS
        waiter = ReplySlot()
        waiter.deadline_ns = deadline_ns
        with self.control:
            if self.failure or self.owned.closed:
                raise WorkerFailure("epoch_revoked")
            if any(k[0] == lane for k in self.slots):
                raise WorkerFailure("canonical_lane_full")
            self.sequences[lane] += 1
            seq = self.sequences[lane]
            self.slots[lane, seq] = waiter
        stop = threading.Event()

        def watchdog():
            if not stop.wait(max(0, (cutoff - time.perf_counter_ns()) / 1e9)):
                self.fail(WorkerDeadline("original_deadline_expired"))
                try:
                    self.owned.abort_owned("canonical_deadline")
                except WorkerFailure as error:
                    self.fail(error)

        watch = threading.Thread(target=watchdog, name="canonical-deadline")
        watch.start()  # Armed BEFORE encoding, admission or any pipe write.
        progress = []
        try:
            if started >= cutoff:
                raise WorkerDeadline("insufficient_original_budget")
            frame = _signed(
                {
                    "epoch": self.epoch,
                    "binding": self.binding,
                    "lane": lane,
                    "seq": seq,
                    "index": 0,
                    "deadline_ns": deadline_ns,
                    "payload": payload,
                },
                self.key,
            )
            self.outgoing.put_nowait(encode(frame, MAX_REQUEST))
            index = 0
            while True:
                remaining = (cutoff - time.perf_counter_ns()) / 1e9
                if remaining <= 0:
                    raise WorkerDeadline("original_deadline_expired")
                try:
                    message = waiter.get(timeout=remaining)
                except queue.Empty as error:
                    raise WorkerDeadline("worker_deadline") from error
                if isinstance(message, Exception):
                    raise message
                if self.failure:
                    raise self.failure
                if message["index"] != index:
                    raise WorkerFailure("stale_or_reordered_reply")
                index += 1
                if message["type"] == "error":
                    raise WorkerFailure(str(message["payload"]))
                if message["type"] == "progress":
                    if len(progress) >= MAX_PROGRESS:
                        raise WorkerFailure("progress_limit")
                    progress.append(message)
                    continue
                if message["type"] != "result":
                    raise WorkerFailure("invalid_result")
                if self.owned.job.evidence(self.owned.process) != self.owned.ownership:
                    raise WorkerFailure("worker_identity_changed")
                finished = time.perf_counter_ns()
                if finished >= cutoff:
                    raise WorkerDeadline("completion_late")
                return {
                    "value": message["payload"],
                    "progress": progress,
                    "ownership": dict(self.owned.ownership),
                    "parent_started_monotonic_ns": started,
                    "parent_finished_monotonic_ns": finished,
                    "parent_started_utc": started_utc,
                    "parent_finished_utc": utc_now(),
                    "parent_completion_verified": True,
                }
        except Exception as error:
            self.fail(error)
            cleanup_error = None
            try:
                self.owned.abort_owned("canonical_call_failure")
            except Exception as cleanup:  # noqa: BLE001 - preserve the primary error
                cleanup_error = str(cleanup)
            raise _mux_failure(
                error,
                waiter.wire_progress,
                {
                    "cleanup": self.owned.close_evidence,
                    "cleanup_error": cleanup_error,
                },
            ) from error
        finally:
            stop.set()
            watch.join(timeout=0.22)
            with self.control:
                self.slots.pop((lane, seq), None)


def _own_birth():
    dll = kernel()
    # Pseudo-handle of this process; ownership remains checked by the parent Job.
    import ctypes
    from ctypes import wintypes

    times = [wintypes.FILETIME() for _ in range(4)]
    if not dll.GetProcessTimes(-1, *[ctypes.byref(t) for t in times]):
        raise ctypes.WinError(ctypes.get_last_error())
    member = wintypes.BOOL()
    if not dll.IsProcessInJob(-1, None, ctypes.byref(member)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        "pid": os.getpid(),
        "creation_time": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
        "job_member": bool(member.value),
    }


def serve_mux(gate, incoming, outgoing):
    """Input nativo independiente; toda API canónica corre en este scheduler."""
    if set(gate) != {
        "gate",
        "mode",
        "handler",
        "source_sha256",
        "config",
        "binding",
        "epoch",
        "key",
    }:
        raise ValueError("canonical_gate_invalid")
    if (
        _factory_hash(gate["handler"]) != gate["source_sha256"]
        or _hash(encode(gate["config"], MAX_REQUEST)) != gate["binding"]
    ):
        raise ValueError("canonical_bootstrap_source_changed")
    key = bytes.fromhex(gate["key"])
    lanes = {name: queue.Queue(maxsize=1) for name in ("ingest", "read")}
    responses = queue.Queue(maxsize=2)
    failed, wake, halted = [], threading.Event(), threading.Event()
    active = {"ingest": False, "read": False}
    admission = threading.Lock()

    def input_loop():
        expected = {"ingest": 1, "read": 1}
        try:
            while not halted.is_set():
                data = incoming.readline(MAX_REQUEST + 1)
                if not data:
                    raise ValueError("canonical_input_eof")
                value = _verified(
                    decode(data, MAX_REQUEST), key, gate["epoch"], gate["binding"]
                )
                lane = value["lane"]
                if value["seq"] != expected[lane] or value["index"] != 0:
                    raise ValueError("replayed_or_out_of_order_request")
                payload = value["payload"]
                if not isinstance(payload, dict) or set(payload) - {
                    "operation",
                    "arguments",
                }:
                    raise ValueError("closed_operation_payload_required")
                operation = payload.get("operation")
                if operation not in (INGEST if lane == "ingest" else READ):
                    raise ValueError("canonical_lane_operation_invalid")
                with admission:
                    if active[lane]:
                        raise ValueError("canonical_lane_full")
                    active[lane] = True
                    lanes[lane].put_nowait(value)
                expected[lane] += 1
                wake.set()
        except (
            OSError,
            ValueError,
            TypeError,
            RecursionError,
            KeyError,
            queue.Full,
        ) as error:
            failed.append(error)
            wake.set()

    def output_loop():
        try:
            while not halted.is_set():
                try:
                    value = responses.get(timeout=0.01)
                except queue.Empty:
                    continue
                outgoing.write(encode(_signed(value, key)))
                outgoing.flush()
        except (OSError, ValueError, TypeError, RuntimeError, queue.Full) as error:
            failed.append(error)
            wake.set()

    def reply(request, kind, payload, index=0):
        value = {k: request[k] for k in ("epoch", "binding", "lane", "seq")}
        value.update(type=kind, payload=payload, index=index)
        encode(_signed(value, key))
        responses.put(
            value,
            timeout=max(
                0, (request["deadline_ns"] - RESERVE_NS - time.perf_counter_ns()) / 1e9
            ),
        )

    handler = None
    threads = []
    live, reading = False, None
    try:
        outgoing.write(encode({"type": "ready", "pid": os.getpid()}))
        outgoing.flush()
        threads = [
            threading.Thread(target=input_loop),
            threading.Thread(target=output_loop),
        ]
        for thread in threads:
            thread.daemon = (
                True  # Parent kills own Job, then joins its own pipe threads.
            )
            thread.start()
        while not failed:
            wake.clear()
            try:
                request = lanes["ingest"].get_nowait()
            except queue.Empty:
                request = None
            if request:
                if time.perf_counter_ns() >= request["deadline_ns"] - RESERVE_NS:
                    raise ValueError("original_deadline_expired")
                payload = request["payload"]
                if payload["operation"] == "challenge":
                    if (
                        live
                        or payload.get("arguments", {}).get("ownership") != _own_birth()
                    ):
                        raise ValueError("canonical_birth_binding_invalid")
                    handler = _sealed_factory(gate["handler"], gate["source_sha256"])(
                        gate["config"]
                    )
                    live = True
                    value = payload["arguments"]
                else:
                    if not live:
                        raise ValueError("canonical_not_live")
                    if hasattr(handler, "handle_ingest"):
                        value = handler.handle_ingest(payload, request["deadline_ns"])
                    else:
                        value = handler(
                            payload,
                            lambda _: (_ for _ in ()).throw(
                                ValueError("ingest_progress_forbidden")
                            ),
                        )
                with admission:
                    active["ingest"] = False
                reply(request, "result", value)
                continue  # Priority re-check BEFORE each next witness.
            if reading is None:
                try:
                    request = lanes["read"].get_nowait()
                except queue.Empty:
                    wake.wait(timeout=0.01)
                    continue
                if not live:
                    raise ValueError("canonical_not_live")
                reading = (
                    request,
                    handler.read_steps(request["payload"], request["deadline_ns"]),
                    0,
                )
            request, iterator, index = reading
            if time.perf_counter_ns() >= request["deadline_ns"] - RESERVE_NS:
                raise ValueError("original_deadline_expired")
            try:
                value = next(iterator)
                if value is None:
                    continue  # One native witness; no prefix/payload on the wire.
                if index >= MAX_PROGRESS:
                    raise ValueError("progress_limit")
                reply(request, "progress", value, index)
                reading = request, iterator, index + 1
            except StopIteration as result:
                reading = None
                with admission:
                    active["read"] = False
                reply(request, "result", result.value, index)
        if failed:
            raise failed[0]
    finally:
        halted.set()
        if reading:
            reading[1].close()
        if handler:
            handler.close()


def _closed(value, names):
    if type(value) is not dict or set(value) != set(names.split()):
        raise ValueError("closed_canonical_arguments_required")


def _remaining(deadline):
    if type(deadline) is not int or time.perf_counter_ns() >= deadline - RESERVE_NS:
        raise WorkerDeadline("original_deadline_expired")


def _attempt(observation, context, ownership):
    """El ancla procede del registro auténtico, no de attempt+trusted_attempt RPC."""
    from benchmark_episode import SCHEMA, VERSION, validate_receipt
    from benchmark_observation import acquisition_context
    from benchmark_plan import digest

    _closed(observation, "request completion observed")
    request, completion = observation["request"], observation["completion"]
    if request.get("operation") != "episode_v3":
        raise ValueError("canonical_sensor_operation_invalid")
    args = request["arguments"]
    observed = observation["observed"]
    value = completion["value"]
    if (
        completion["ownership"] != ownership
        or value.get("episode_id", value.get("proof", {}).get("episode_id"))
        != args["episode_id"]
        or not isinstance(args["stream"], str)
        or not args["stream"]
        or args["deadline_ns"] != args["start"]["monotonic_ns"] + 2_000_000_000
        or completion["parent_started_monotonic_ns"] < args["start"]["monotonic_ns"]
        or observed["monotonic_ns"] < completion["parent_finished_monotonic_ns"]
    ):
        raise ValueError("canonical_sensor_observation_invalid")
    if "rejected" in value:
        _closed(
            value,
            "rejected episode_id ordinal request_sha256 rejection_sha256 raw_refs progress_refs",
        )
        if type(value["ordinal"]) is not int or value["ordinal"] < 1:
            raise ValueError("canonical_rejection_ordinal_invalid")
        _remaining(args["deadline_ns"])
        return {
            "status": "rejected",
            "episode_id": args["episode_id"],
            "result": value,
            "request": args,
            "ownership": ownership,
            "observed": observed,
        }
    _closed(value, "proof summary")
    proof = value["proof"]
    receipt = {
        "schema": SCHEMA,
        "episode_id": args["episode_id"],
        "ordinal": proof["ordinal"],
        "start": args["start"],
        "deadline_ns": args["deadline_ns"],
        "observed_utc": observed["utc"],
        "observed_monotonic_ns": observed["monotonic_ns"],
        "proof": proof,
        "previous_receipt_sha256": None
        if args["confirm"] is None
        else digest(args["confirm"]),
        "context_sha256": digest(acquisition_context(context, VERSION)),
        "ownership": ownership,
    }
    validate_receipt(receipt, context)
    _remaining(receipt["deadline_ns"])
    return {"status": "accepted", "receipt": receipt}


def _attempt_clock(attempt):
    """Original budget of either authentic outcome; never a positive reject receipt."""
    if attempt["status"] == "accepted":
        return attempt["receipt"]
    return {
        "episode_id": attempt["request"]["episode_id"],
        "deadline_ns": attempt["request"]["deadline_ns"],
        "observed_monotonic_ns": attempt["observed"]["monotonic_ns"],
    }


@dataclass(frozen=True, eq=False)
class CanonicalPosition:
    """Capability por identidad en el registro padre; sus campos no son autoridad."""

    token: str
    epoch: str
    context_sha256: str
    cursor: int
    prefix: str
    kind: str
    stream: str
    worker: str


class CanonicalProvider:
    """Store, State y todas sus capabilities viven en el scheduler de este hijo."""

    def __init__(self, config):
        from benchmark_canonical import CanonicalState
        from benchmark_custody import CustodyStore
        from benchmark_episode import confined

        _closed(config, "canonical_mux_v1 bootstrap_path bootstrap_sha256")
        data = Path(config["bootstrap_path"]).read_bytes()
        if _hash(data) != config["bootstrap_sha256"]:
            raise ValueError("canonical_prebound_file_changed")
        binding = decode(data)
        _closed(binding, "root context stream epoch supervisor sensor")
        if binding["supervisor"]["pid"] != os.getppid():
            raise ValueError("canonical_supervisor_binding_invalid")
        dll = kernel()
        handle = dll.OpenProcess(0x1000, False, os.getppid())
        if not handle:
            raise ValueError("canonical_supervisor_unobservable")
        try:
            import ctypes
            from ctypes import wintypes

            times = [wintypes.FILETIME() for _ in range(4)]
            if not dll.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
                raise ValueError("canonical_supervisor_birth_unobservable")
            if (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime != binding[
                "supervisor"
            ]["creation_time"]:
                raise ValueError("canonical_supervisor_birth_changed")
        finally:
            dll.CloseHandle(handle)
        self.binding = binding
        self.root = confined(binding["root"])
        self.context = binding["context"]
        private = self.root / ("canonical-" + binding["epoch"])
        private.mkdir(parents=True)
        self.store = CustodyStore(private)
        self.state = CanonicalState(self.root, self.context, self.store)
        self.owner = threading.current_thread()
        self.transfer = self.tentative = None
        self.published = None
        self.anchors = {}
        self.views = {}

    def _check(self):
        if threading.current_thread() is not self.owner:
            raise ValueError("canonical_scheduler_owner_required")
        if self.state.disposition != "protected":
            raise ValueError("unknown_quarantined")

    def handle_ingest(self, payload, deadline_ns):
        _remaining(deadline_ns)
        expected = (
            self.transfer["deadline_ns"]
            if self.transfer
            else self.tentative["clock"]["deadline_ns"]
            if self.tentative
            else payload.get("arguments", {}).get("deadline_ns")
        )
        if deadline_ns != expected:
            raise ValueError("canonical_original_budget_changed")
        return self(payload, None)

    def __call__(self, payload, emit):
        self._check()
        operation, args = payload["operation"], payload.get("arguments")
        if operation == "begin":
            _closed(args, "transfer characters sha256 deadline_ns")
            _remaining(args["deadline_ns"])
            if self.transfer or self.tentative:
                raise ValueError("canonical_ingest_busy")
            if (
                type(args["characters"]) is not int
                or not 0 < args["characters"] <= MAX_CHARACTERS
            ):
                raise ValueError("canonical_transfer_size_invalid")
            self.transfer = {**args, "next": 0, "text": [], "length": 0}
            return {"transfer": args["transfer"], "index": 0}
        if operation == "fragment":
            _closed(args, "transfer index text")
            transfer = self.transfer
            if (
                not transfer
                or args["transfer"] != transfer["transfer"]
                or type(args["index"]) is not int
                or args["index"] != transfer["next"]
            ):
                raise ValueError("canonical_fragment_order_invalid")
            _remaining(transfer["deadline_ns"])
            if (
                not isinstance(args["text"], str)
                or not 0 < len(args["text"]) <= FRAGMENT
            ):
                raise ValueError("canonical_fragment_size_invalid")
            transfer["length"] += len(args["text"])
            if transfer["length"] > transfer["characters"]:
                raise ValueError("canonical_transfer_excess")
            transfer["text"].append(args["text"])
            transfer["next"] += 1
            return {"transfer": args["transfer"], "index": transfer["next"]}
        if operation == "end":
            _closed(args, "transfer")
            transfer = self.transfer
            if not transfer or args["transfer"] != transfer["transfer"]:
                raise ValueError("canonical_unknown_transfer")
            _remaining(transfer["deadline_ns"])
            data = "".join(transfer["text"]).encode()
            if (
                transfer["length"] != transfer["characters"]
                or _hash(data) != transfer["sha256"]
            ):
                raise ValueError("canonical_transfer_seal_invalid")
            observation = decode(data, MAX_CHARACTERS * 4)
            attempt = _attempt(observation, self.context, self.binding["sensor"])
            receipt = _attempt_clock(attempt)
            if receipt["deadline_ns"] != transfer["deadline_ns"]:
                raise ValueError("canonical_ingest_context_invalid")
            # Independent authenticated registry BEFORE any episode filesystem I/O.
            if receipt["episode_id"] in self.anchors:
                raise ValueError("canonical_attempt_replay")
            anchor_bytes = encode(attempt)
            self.anchors[receipt["episode_id"]] = anchor_bytes
            entries = self._stage(attempt)
            trusted_attempt = decode(self.anchors[receipt["episode_id"]])
            token = self.state.capture(
                entries, attempt, trusted_attempt=trusted_attempt, context=self.context
            )
            candidate = self.state.propose(
                token, attempt, trusted_attempt=trusted_attempt, context=self.context
            )
            snapshot = self.state.commit(candidate)
            self.views.clear()
            _remaining(receipt["deadline_ns"])
            commit = {
                "cursor": snapshot.cursor,
                "prefix": snapshot.rolling_hash,
                "receipt_sha256": _hash(anchor_bytes),
                "transfer": args["transfer"],
            }
            self.tentative = {
                "commit": commit,
                "clock": receipt,
                "stage": "committed",
            }
            self.transfer = None
            return commit
        if operation == "publish":
            _closed(args, "commit observed")
            tentative = self.tentative
            if (
                not tentative
                or tentative["stage"] != "committed"
                or args["commit"] != tentative["commit"]
            ):
                raise ValueError("canonical_publication_binding_invalid")
            receipt = tentative["clock"]
            _remaining(receipt["deadline_ns"])
            if (
                type(args["observed"]) is not int
                or not receipt["observed_monotonic_ns"]
                <= args["observed"]
                < receipt["deadline_ns"]
            ):
                raise ValueError("canonical_publication_clock_invalid")
            data = encode(args)
            self._write(
                receipt["episode_id"],
                "external-publish.json",
                data,
                receipt["deadline_ns"],
            )
            tentative["stage"] = "persisted"
            tentative["anchor_sha256"] = _hash(data)
            tentative["observed"] = args["observed"]
            return {"commit": args["commit"], "anchor_sha256": _hash(data)}
        if operation == "confirm":
            _closed(args, "commit anchor_sha256 completed")
            tentative = self.tentative
            if (
                not tentative
                or tentative["stage"] != "persisted"
                or args["commit"] != tentative["commit"]
                or args["anchor_sha256"] != tentative["anchor_sha256"]
            ):
                raise ValueError("canonical_publication_confirmation_invalid")
            deadline = tentative["clock"]["deadline_ns"]
            _remaining(deadline)
            if (
                type(args["completed"]) is not int
                or not tentative["observed"] <= args["completed"] < deadline
            ):
                raise ValueError("canonical_publication_completion_late")
            self.published = dict(tentative["commit"])
            self.tentative = None
            return self.published
        raise ValueError("unknown_canonical_ingest_operation")

    def _write(self, episode, name, data, deadline):
        _remaining(deadline)
        path = self.root / episode / name
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _remaining(deadline)

    def _stage(self, attempt):
        import re

        from benchmark_custody import MAX_ENTRIES, SourceEntry
        from benchmark_episode import confined

        receipt = _attempt_clock(attempt)
        deadline = receipt["deadline_ns"]
        directory = self.root / receipt["episode_id"]
        if confined(directory, self.root) != directory:
            raise ValueError("canonical_original_namespace_changed")
        original = []
        # Closed native EpisodeProvider namespace; consumer cannot supply paths.
        for path in sorted(directory.iterdir()):
            _remaining(deadline)
            if path.name == "rejected.json" and attempt["status"] != "rejected":
                raise ValueError("canonical_unknown_original_name")
            if path.name not in {
                "request.json",
                "prepared.json",
                "commit.json",
                "rejected.json",
            } and not re.fullmatch(r"(?:raw|progress)-[1-9][0-9]*\.json", path.name):
                raise ValueError("canonical_unknown_original_name")
            if path.is_symlink() or not path.is_file():
                raise ValueError("canonical_original_type_invalid")
            if path.stat().st_size > MAX_CHARACTERS:
                raise ValueError("canonical_original_oversized")
            with path.open("rb") as original_file:
                data = original_file.read(MAX_CHARACTERS + 1)
            if len(data) > MAX_CHARACTERS:
                raise ValueError("canonical_original_oversized")
            original.append(SourceEntry(path.name, path, len(data), _hash(data)))
            if len(original) > MAX_ENTRIES - 2:
                raise ValueError("canonical_original_inventory_full")
        receipt_bytes = encode(attempt)
        inventory_bytes = encode(
            {
                "entries": [
                    {"name": e.name, "length": e.length, "sha256": e.seal}
                    for e in original
                ],
                "receipt_sha256": _hash(receipt_bytes),
            }
        )
        for name, data in (
            ("supervisor-receipt.json", receipt_bytes),
            ("supervisor-inventory.json", inventory_bytes),
        ):
            self._write(receipt["episode_id"], name, data, deadline)
            original.append(SourceEntry(name, directory / name, len(data), _hash(data)))
        return original

    def read_steps(self, payload, deadline_ns):
        self._check()
        if self.tentative or self.transfer or self.published is None:
            raise ValueError("canonical_head_unpublished")
        _closed(payload.get("arguments", {}), "")
        published = self.published
        lease = self.state.checkout(deadline=(deadline_ns - RESERVE_NS) / 1e9)
        try:
            while True:
                finished = self.state.witness_step(lease)
                yield None
                if finished:
                    break
            position = self.state.finish_accredit(lease)
            if position != {k: published[k] for k in ("cursor", "prefix")}:
                raise ValueError("canonical_watermark_changed")
            token = secrets.token_hex(32)
            value = {
                **position,
                "token": token,
                "epoch": self.binding["epoch"],
                "context_sha256": _hash(encode(self.context)),
                "kind": payload["operation"],
                "stream": self.binding["stream"],
                "worker": self._worker_identity(),
            }
            self.views[token] = value
            # Only one base/status capability remains active; no history registry.
            self.views = {token: value}
            return value
        finally:
            self.state.release(lease)

    def _worker_identity(self):
        birth = _own_birth()
        return f"{birth['pid']}:{birth['creation_time']}"

    def close(self):
        self.state.lose_authority()
        self.store.close()


class CanonicalChannel:
    """Factory del supervisor: root/context se derivan del sensor propio real."""

    def __init__(
        self,
        sensor,
        *,
        private_root,
        stream,
        trusted_handler="benchmark_canonical_runtime:CanonicalProvider",
    ):
        from benchmark_episode import confined, read_json

        if type(sensor) is not OwnedProcess or sensor.closed or sensor._mux:
            raise ValueError("canonical_original_sensor_required")
        if sensor.job.evidence(sensor.process) != sensor.ownership:
            raise ValueError("canonical_sensor_ownership_changed")
        sensor_config = decode(sensor._trusted_config_bytes, MAX_REQUEST)
        self.sensor = sensor
        self.context = read_json(confined(sensor_config["context_path"]))
        root = confined(sensor_config["root"])
        private = confined(private_root)
        private.mkdir(parents=True, exist_ok=True)
        binding = {
            "root": str(root),
            "context": self.context,
            "stream": stream,
            "epoch": secrets.token_hex(16),
            "supervisor": _own_birth(),
            "sensor": dict(sensor.ownership),
        }
        data = encode(binding)
        path = private / ("bootstrap-" + binding["epoch"] + ".json")
        with path.open("xb") as output:
            output.write(data)
        self.worker = OwnedProcess(
            {
                "canonical_mux_v1": True,
                "bootstrap_path": str(path),
                "bootstrap_sha256": _hash(data),
            },
            trusted_handler,
        )
        self.binding = binding
        self._context_sha256 = _hash(encode(self.context))
        self.positions = {}
        self.last_receipt = None
        self.last_attempt = None
        self.cleanup_errors = []
        self.publication = None
        self.consumed = None

    def ingest_latest(self):
        self.positions.clear()
        self.last_receipt = self.last_attempt = None
        try:
            return self._ingest_latest()
        except BaseException:
            self.publication = None
            try:
                self.worker.abort_owned("canonical_ingest_incomplete")
            except BaseException as cleanup:  # noqa: BLE001 - preserve primary ingest failure
                try:
                    from benchmark_coordinator import safe_cleanup_error_record

                    record = {
                        "type": type(cleanup).__name__[:128],
                        "message_sha256": None,
                        "observed": None,
                    }
                    self.cleanup_errors.append(record)
                    self.cleanup_errors[-1] = safe_cleanup_error_record(cleanup)
                except BaseException:  # noqa: BLE001,S110 - ni registro ni metadata sustituyen la causa primaria
                    pass
            raise

    def _ingest_latest(self):
        if _hash(encode(self.context)) != self._context_sha256:
            raise ValueError("canonical_context_binding_changed")
        # Only a private completion record generated by actual OwnedProcess.call.
        completion = self.sensor._last_completion
        if completion is None or completion is self.consumed:
            raise ValueError("canonical_missing_or_replayed_sensor_completion")
        if self.sensor.job.evidence(self.sensor.process) != self.sensor.ownership:
            raise ValueError("canonical_sensor_ownership_changed")
        self.consumed = completion
        request = decode(completion[0], MAX_REQUEST)
        observed = {"utc": utc_now(), "monotonic_ns": time.perf_counter_ns()}
        observation = {
            "request": request,
            "completion": completion[1],
            "observed": observed,
        }
        attempt = _attempt(observation, self.context, self.sensor.ownership)
        deadline = _attempt_clock(attempt)["deadline_ns"]
        data = encode(observation, MAX_CHARACTERS * 4)
        text = data.decode()
        transfer = secrets.token_hex(16)

        def call(operation, args):
            return self.worker.call(
                {"operation": operation, "arguments": args}, deadline_ns=deadline
            )

        try:
            call(
                "begin",
                {
                    "transfer": transfer,
                    "characters": len(text),
                    "sha256": _hash(data),
                    "deadline_ns": deadline,
                },
            )
            for index, offset in enumerate(range(0, len(text), FRAGMENT)):
                call(
                    "fragment",
                    {
                        "transfer": transfer,
                        "index": index,
                        "text": text[offset : offset + FRAGMENT],
                    },
                )
            committed = call("end", {"transfer": transfer})
            commit = committed["value"]
            anchor = call(
                "publish",
                {
                    "commit": commit,
                    "observed": committed["parent_finished_monotonic_ns"],
                },
            )
            final = anchor["parent_finished_monotonic_ns"]
            _remaining(deadline)
            # External completion anchor lives in supervisor memory; no self-hash.
            publication = {
                "commit": commit,
                "anchor_sha256": anchor["value"]["anchor_sha256"],
                "completed": final,
            }
            confirmed = call("confirm", publication)
            _remaining(deadline)
            if confirmed["value"] != commit:
                raise WorkerFailure("canonical_final_confirmation_changed")
            publication["confirmed"] = confirmed["parent_finished_monotonic_ns"]
            self.publication = publication
            self.last_attempt = attempt
            self.last_receipt = attempt.get("receipt")
            return dict(commit)
        except BaseException:
            self.publication = None
            try:
                self.worker.abort_owned("canonical_publication_incomplete")
            except BaseException as cleanup:  # noqa: BLE001 - preserve primary publication failure
                try:
                    from benchmark_coordinator import safe_cleanup_error_record

                    record = {
                        "type": type(cleanup).__name__[:128],
                        "message_sha256": None,
                        "observed": None,
                    }
                    self.cleanup_errors.append(record)
                    self.cleanup_errors[-1] = safe_cleanup_error_record(cleanup)
                except BaseException:  # noqa: BLE001,S110 - ni registro ni metadata sustituyen la causa primaria
                    pass
            raise

    def request_view(self, *, kind="status", deadline_ns):
        if kind not in READ:
            raise ValueError("canonical_view_kind_invalid")
        result = self.worker.call(
            {"operation": kind, "arguments": {}}, deadline_ns=deadline_ns
        )
        value = result["value"]
        position = CanonicalPosition(**value)
        birth = self.worker.ownership
        if (
            position.epoch != self.binding["epoch"]
            or position.context_sha256 != _hash(encode(self.context))
            or position.worker != f"{birth['pid']}:{birth['creation_time']}"
            or position.stream != self.binding["stream"]
            or position.kind != kind
        ):
            self.worker.abort_owned("canonical_foreign_position")
            raise WorkerFailure("canonical_position_binding_invalid")
        self.positions = {position.token: position}
        return position

    def _resolve_position(self, position):
        """Sólo busca identidad; cualquier acreditación fresca usa request_view."""
        if (
            type(position) is not CanonicalPosition
            or self.positions.get(position.token) is not position
            or self.worker.closed
        ):
            raise ValueError("canonical_unknown_or_foreign_position")
        return position

    def close(self):
        self.positions.clear()
        self.publication = self.last_receipt = None
        self.worker.close(graceful=False)
