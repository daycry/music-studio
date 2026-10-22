"""Transición común y consumidor canónico bajo custodia individual.

El fold reconstruye originales desde vacío; no es FINAL con packs ni integra
runtime/coordinador. Las referencias sólo tienen autoridad en su instancia.
"""

from __future__ import annotations

import copy
import fnmatch
import hashlib
import math
import threading
import time
from dataclasses import dataclass
from functools import wraps
from itertools import pairwise
from types import MappingProxyType

from benchmark_custody import (
    MAX_ENTRIES,
    MAX_READ,
    CustodyError,
    CustodyStore,
    SourceEntry,
)
from benchmark_episode import (
    MAX_FILE,
    SCHEMA,
    VERSION,
    check_clock,
    confined,
    read_json,
    sealed_read,
    summary,
    validate_receipt,
    verify_ownership,
    verify_prepared,
    verify_progress,
)
from benchmark_observation import (
    acquisition_context,
    acquisition_end,
    episode_decision,
    stamp,
    validate_samples,
)
from benchmark_plan import digest
from benchmark_process import decode, encode


def validate_accepted(
    directory,
    receipt,
    context,
    previous=None,
    *,
    historical=False,
    now=None,
    idle=False,
):
    """Único cuerpo semántico aceptado, para originales y cápsula protegida."""
    validate_receipt(receipt, context)
    if receipt["previous_receipt_sha256"] != (
        None if previous is None else digest(previous["receipt"])
    ):
        raise ValueError("v3_missing_predecessor_or_rejection_inventory")
    request = read_json(directory / "request.json")
    proof = receipt["proof"]
    commit = sealed_read(directory / "commit.json", proof["commit_sha256"])
    prepared = sealed_read(directory / "prepared.json", proof["prepared_sha256"])
    if (
        set(commit) != {"schema", "episode_id", "prepared_sha256", "write_started"}
        or commit["schema"] != SCHEMA
        or commit["episode_id"] != receipt["episode_id"]
        or commit["prepared_sha256"] != digest(prepared)
    ):
        raise ValueError("v3_commit_reference_invalid")
    if request != {
        "schema": SCHEMA,
        "ordinal": receipt["ordinal"],
        "episode_id": receipt["episode_id"],
        "request": {
            "episode_id": receipt["episode_id"],
            "stream": prepared["stream"],
            "start": receipt["start"],
            "deadline_ns": receipt["deadline_ns"],
            "phase_started_utc": prepared["phase_started_utc"],
            "idle": prepared["idle"],
            "confirm": None if previous is None else previous["receipt"],
            "enforce": True,
        },
        "context": acquisition_context(context, VERSION),
    }:
        raise ValueError("v3_request_context_or_phase_invalid")
    if (
        prepared["episode_id"],
        prepared["ordinal"],
        prepared["start"],
        prepared["deadline_ns"],
    ) != (
        receipt["episode_id"],
        receipt["ordinal"],
        receipt["start"],
        receipt["deadline_ns"],
    ):
        raise ValueError("v3_prepared_receipt_mismatch")
    originals = []
    for i, ref in enumerate(prepared["raw_refs"], 1):
        if ref["path"] != f"raw-{i}.json":
            raise ValueError("v3_raw_order_invalid")
        originals.append(sealed_read(directory / ref["path"], ref["sha256"]))
    if sorted(p.name for p in directory.glob("raw-*.json")) != [
        f"raw-{i}.json" for i in range(1, len(originals) + 1)
    ]:
        raise ValueError("v3_omitted_raw")
    sample = verify_prepared(
        prepared, originals, context, previous, historical=historical, now=now
    )
    if idle and sample["nvml"]["used_mb"] > 1600:
        raise ValueError("auto_nvml_invalid_or_idle")
    verify_progress(directory, prepared, originals)
    if proof["sample_sha256"] != digest(sample):
        raise ValueError("v3_sample_seal_invalid")
    if proof["summary_sha256"] != digest(summary(sample)):
        raise ValueError("v3_summary_seal_invalid")
    check_clock(commit["write_started"], receipt["start"], receipt["deadline_ns"])
    sequence = [
        prepared["validation_finished"],
        commit["write_started"],
        proof["commit_finished"],
        proof["verification_finished"],
    ]
    if any(
        a["monotonic_ns"] > b["monotonic_ns"] or stamp(a["utc"]) > stamp(b["utc"])
        for a, b in pairwise(sequence)
    ):
        raise ValueError("v3_commit_completion_order_invalid")
    episode_decision(
        originals,
        context,
        previous=prepared["predecessor"],
        historical=historical,
        now=now,
        idle=prepared["idle"],
        completion=(receipt["observed_utc"], receipt["observed_monotonic_ns"]),
        phase_started_utc=prepared["phase_started_utc"],
        method=VERSION,
    )
    if proof["commit_finished"]["monotonic_ns"] < max(
        op["finished_monotonic_ns"] for op in sample["operations"].values()
    ) or stamp(proof["commit_finished"]["utc"]) < acquisition_end(sample):
        raise ValueError("v3_commit_before_acquisition")
    return sample


def validate_inventory_attempt(directory, attempt, ordinal, context):
    status = attempt["status"]
    if status == "accepted":
        receipt = attempt["receipt"]
        validate_receipt(receipt, context)
        if receipt["ordinal"] != ordinal:
            raise ValueError("v3_attempt_order_invalid")
        start = receipt["start"]
    elif status in {"rejected", "interrupted"}:
        request = attempt["request"]
        start = request["start"]
        if status == "rejected":
            result = attempt["result"]
            if (
                result["ordinal"] != ordinal
                or result["episode_id"] != request["episode_id"]
            ):
                raise ValueError("v3_rejected_order_invalid")
            manifest = sealed_read(directory / "request.json", result["request_sha256"])
            if manifest != {
                "schema": SCHEMA,
                "ordinal": ordinal,
                "episode_id": request["episode_id"],
                "request": request,
                "context": acquisition_context(context, VERSION),
            }:
                raise ValueError("v3_rejected_context_invalid")
            rejection = sealed_read(
                directory / "rejected.json", result["rejection_sha256"]
            )
            if (
                rejection["status"] != "rejected"
                or rejection["error"] != result["rejected"]
            ):
                raise ValueError("v3_rejection_reference_invalid")
            for kind in ("raw_refs", "progress_refs"):
                refs = result[kind]
                prefix = "raw" if kind == "raw_refs" else "progress"
                for i, ref in enumerate(refs, 1):
                    if ref["path"] != f"{prefix}-{i}.json":
                        raise ValueError("v3_rejected_raw_order_invalid")
                    sealed_read(directory / ref["path"], ref["sha256"])
                if {p.name for p in directory.glob(f"{prefix}-*.json")} != {
                    r["path"] for r in refs
                }:
                    raise ValueError("v3_rejected_raw_omitted")
        else:
            if (
                attempt["ordinal"] != ordinal
                or attempt["interrupted"]["status"] != "incomplete_invalid"
            ):
                raise ValueError("v3_interrupted_order_invalid")
            # Inspect available bytes; an unreturned value has no fabricated
            # completion. Parent progress remains the external partial anchor.
            if (directory / "request.json").exists():
                manifest = read_json(directory / "request.json")
                if (
                    manifest["request"] != request
                    or manifest["ordinal"] != ordinal
                    or manifest["context"] != acquisition_context(context, VERSION)
                ):
                    raise ValueError("v3_interrupted_context_invalid")
            last_progress = start
            for frame in attempt["interrupted"]["progress"]:
                if frame["monotonic_ns"] < last_progress["monotonic_ns"] or stamp(
                    frame["utc"]
                ) < stamp(last_progress["utc"]):
                    raise ValueError("v3_interrupted_progress_clock_invalid")
                last_progress = frame
    else:
        raise ValueError("v3_attempt_status_invalid")
    return start


def _attempt_header(attempt, context, ordinal):
    """Sólo memoria: binding/orden antes de tocar cualquier artefacto."""
    status = attempt["status"]
    if status == "accepted":
        receipt = attempt["receipt"]
        validate_receipt(receipt, context)
        start, deadline, episode_id = (
            receipt["start"],
            receipt["deadline_ns"],
            receipt["episode_id"],
        )
        number = receipt["ordinal"]
    elif status in {"rejected", "interrupted"}:
        request = attempt["request"]
        start, deadline, episode_id = (
            request["start"],
            request["deadline_ns"],
            request["episode_id"],
        )
        number = (
            attempt["result"]["ordinal"] if status == "rejected" else attempt["ordinal"]
        )
        if deadline != start["monotonic_ns"] + 2_000_000_000:
            raise ValueError("v3_original_deadline_invalid")
        verify_ownership(
            attempt["ownership"]
            if status == "rejected"
            else attempt["interrupted"]["evidence"]["ownership"]
        )
    else:
        raise ValueError("v3_attempt_status_invalid")
    if type(number) is not int or number != ordinal:
        raise ValueError("v3_attempt_order_invalid")
    if (
        not isinstance(episode_id, str)
        or len(episode_id) != 32
        or any(c not in "0123456789abcdef" for c in episode_id)
    ):
        raise ValueError("v3_supervisor_identity_invalid")
    return start, deadline / 1e9, episode_id


@dataclass(frozen=True, slots=True)
class _History:
    previous: _History | None
    attempt: bytes
    sample: bytes | None
    witness: object = None


class _BytePath:
    """Vista de una entrada de índice cerrado; SHA de bytes, no de JSON."""

    def __init__(self, directory, name):
        self.directory = directory
        self.name = name

    def exists(self):
        return self.name in self.directory.entries

    def read_bytes(self):
        directory = self.directory
        if self.name not in directory.entries:
            raise ValueError("canonical_closed_entry_missing")
        length, seal = directory.entries[self.name]
        if length > MAX_FILE:
            raise ValueError("v3_invalid_or_partial_json")
        payload = bytearray()
        for position in range(0, max(length, 1), MAX_READ):
            amount = min(MAX_READ, length - position)
            chunk = directory.store.read(
                directory.ref,
                self.name,
                offset=position,
                length=amount,
                deadline=directory.deadline,
            )
            directory.profile["reads"] += 1
            directory.profile["bytes"] += len(chunk)
            directory.profile["entries"].append(self.name)
            if len(chunk) != amount:
                raise ValueError("canonical_short_read")
            payload.extend(chunk)
        if hashlib.sha256(payload).hexdigest() != seal:
            raise ValueError("canonical_source_byte_seal_mismatch")
        return bytes(payload)


class _ClosedDirectory:
    def __init__(self, store, ref, entries, deadline, profile):
        self.store, self.ref, self.entries = store, ref, entries
        self.deadline, self.profile = deadline, profile

    def __truediv__(self, name):
        return _BytePath(self, name)

    def glob(self, pattern):
        return (
            _BytePath(self, name)
            for name in self.entries
            if fnmatch.fnmatchcase(name, pattern)
        )


class _Token:
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class _Registration:
    ref: object
    entries: object
    attempt: bytes
    deadline: float


@dataclass(frozen=True, slots=True)
class _Candidate:
    head: Snapshot
    proposed: Snapshot
    registration: _Registration


@dataclass(frozen=True, slots=True)
class Snapshot:
    cursor: int = 0
    accepted_count: int = 0
    prior_start: bytes | None = None
    last_receipt: bytes | None = None
    last_sample: bytes | None = None
    last_accepted_receipt: bytes | None = None
    last_accepted_sample: bytes | None = None
    rejection_adjacency: bool = False
    interrupted: bool = False
    rolling_hash: str = ""
    history: _History | None = None

    def samples(self):
        samples = []
        link = self.history
        while link is not None:
            if link.sample is not None:
                samples.append(_thaw(link.sample))
            link = link.previous
        return samples[::-1]


def _freeze(value):
    return encode(value, MAX_FILE)


def _thaw(value):
    return decode(value, MAX_FILE)


def _deadline(deadline):
    if time.perf_counter() >= deadline:
        raise ValueError("canonical_original_deadline_exhausted")


def _publication_errors(function):
    """Misma normalización de errores que el wrapper offline ya cubierto."""

    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (KeyError, TypeError, AttributeError, IndexError, OSError) as error:
            raise ValueError("v3_incomplete_publication") from error

    return checked


@_publication_errors
def transition(
    head,
    directory,
    attempt,
    context,
    *,
    historical=False,
    now=None,
    record=None,
    witness=None,
):
    # Sólo el delta; el prefijo inmutable sigue compartido por identidad.
    attempt = copy.deepcopy(attempt)
    context = copy.deepcopy(context)
    record = copy.deepcopy(record)
    start, _, _ = _attempt_header(attempt, context, head.cursor + 1)
    if head.prior_start is not None:
        prior = _thaw(head.prior_start)
        if start["monotonic_ns"] <= prior["monotonic_ns"] or stamp(
            start["utc"]
        ) <= stamp(prior["utc"]):
            raise ValueError("v3_attempt_replayed")
    if attempt["status"] in {"rejected", "interrupted"}:
        validate_inventory_attempt(directory, attempt, head.cursor + 1, context)
        return Snapshot(
            cursor=head.cursor + 1,
            accepted_count=head.accepted_count,
            prior_start=_freeze(start),
            last_accepted_receipt=head.last_accepted_receipt,
            last_accepted_sample=head.last_accepted_sample,
            rejection_adjacency=True,
            interrupted=True,
            rolling_hash=digest(
                {
                    "previous": head.rolling_hash,
                    "cursor": head.cursor + 1,
                    "attempt": digest(attempt),
                    "sample": None,
                }
            ),
            history=_History(head.history, _freeze(attempt), None, witness),
        )
    receipt = attempt["receipt"]
    previous = (
        None
        if head.last_receipt is None
        else {"receipt": _thaw(head.last_receipt), "sample": _thaw(head.last_sample)}
    )
    sample = validate_accepted(
        directory, receipt, context, previous, historical=historical, now=now
    )
    if record is not None and record != {
        "supervisor_receipt": receipt,
        "sample": summary(sample),
    }:
        raise ValueError("v3_audit_summary_mismatch")
    return Snapshot(
        cursor=head.cursor + 1,
        accepted_count=head.accepted_count + 1,
        prior_start=_freeze(receipt["start"]),
        last_receipt=_freeze(receipt),
        last_sample=_freeze(sample),
        last_accepted_receipt=_freeze(receipt),
        last_accepted_sample=_freeze(sample),
        interrupted=head.interrupted,
        rolling_hash=digest(
            {
                "previous": head.rolling_hash,
                "cursor": head.cursor + 1,
                "attempt": digest(attempt),
                "sample": digest(sample),
            }
        ),
        history=_History(head.history, _freeze(attempt), _freeze(sample), witness),
    )


def fold_originals(
    root, attempts, context, *, trusted_attempts, historical=False, now=None
):
    # Las dos fuentes quedan separadas del llamador antes de comparar o hacer I/O.
    attempts = copy.deepcopy(attempts)
    trusted_attempts = copy.deepcopy(trusted_attempts)
    context = _thaw(_freeze(context))
    root = confined(root)
    if trusted_attempts is None or [digest(a) for a in attempts] != [
        digest(a) for a in trusted_attempts
    ]:
        raise ValueError("v3_supervisor_attempt_anchor_mismatch")
    head = Snapshot(rolling_hash=digest({"root": str(root), "context": context}))
    for attempt in attempts:
        _, _, episode_id = _attempt_header(attempt, context, head.cursor + 1)
        head = transition(
            head,
            confined(root / episode_id, root),
            attempt,
            context,
            historical=historical,
            now=now,
        )
    return head


def _serialized(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return guarded


@dataclass(frozen=True, slots=True, eq=False)
class _ReadLease:
    """Capability interna; sólo el registro concede autoridad para leer."""

    state: object
    owner: object
    seal: object
    identity: object = None

    def __post_init__(self):
        object.__setattr__(self, "identity", self)


@dataclass(slots=True)
class _LeaseProgress:
    snapshot: Snapshot
    link: _History | None
    context: bytes
    deadline: float
    epoch: int
    busy: bool = False
    finished: bool = False


class CanonicalState:
    """Estado interno con autoridad por instancia y publicación atómica."""

    def __init__(self, root, context, store):
        if type(store) is not CustodyStore:
            raise ValueError("canonical_owned_store_required")
        self._root = confined(root)
        self._context = _freeze(context)
        self._store = store
        self._head = Snapshot(
            rolling_hash=digest(
                {"root": str(self._root), "context": _thaw(self._context)}
            )
        )
        self._profile = {"reads": 0, "bytes": 0, "entries": [], "old_entry_reads": 0}
        self._registry = {}
        self._candidates = {}
        self._quarantined = False
        self._lock = threading.RLock()
        self._accreditation_lock = threading.Lock()
        self._lease_seal = object()
        self._leases = {}
        self._epoch = 0

    @property
    def snapshot(self):
        return self._head

    @property
    def read_profile(self):
        return _thaw(_freeze(self._profile))

    @property
    def disposition(self):
        return "unknown_quarantined" if self._quarantined else "protected"

    @_serialized
    def lose_authority(self):
        self._quarantined = True
        self._epoch += 1
        self._leases.clear()

    @_serialized
    def capture(self, entries, attempt, *, trusted_attempt, context):
        if self._quarantined:
            raise ValueError("unknown_quarantined")
        if _freeze(context) != self._context:
            raise ValueError("canonical_context_binding_mismatch")
        if trusted_attempt is None or _freeze(attempt) != _freeze(trusted_attempt):
            raise ValueError("v3_supervisor_attempt_anchor_mismatch")
        _, deadline, episode_id = _attempt_header(
            attempt, _thaw(self._context), self._head.cursor + 1
        )
        if type(entries) not in (list, tuple) or not 1 <= len(entries) <= MAX_ENTRIES:
            raise ValueError("canonical_closed_entries_invalid")
        names = set()
        for entry in entries:
            if (
                type(entry) is not SourceEntry
                or entry.name in names
                or confined(entry.path, self._root)
                != self._root / episode_id / entry.name
            ):
                raise ValueError("canonical_source_binding_mismatch")
            names.add(entry.name)
        frozen = _freeze(attempt)
        metadata = MappingProxyType({e.name: (e.length, e.seal) for e in entries})
        _deadline(deadline)
        try:
            ref = self._store.capture(tuple(entries), deadline=deadline)
        except CustodyError as error:
            self.lose_authority()
            raise ValueError("unknown_quarantined") from error
        _deadline(deadline)
        token = _Token()
        self._registry[token] = _Registration(ref, metadata, frozen, deadline)
        return token

    @_serialized
    def propose(self, token, attempt, *, trusted_attempt, context, record=None):
        if self._quarantined:
            raise ValueError("unknown_quarantined")
        if _freeze(context) != self._context:
            raise ValueError("canonical_context_binding_mismatch")
        if trusted_attempt is None or _freeze(attempt) != _freeze(trusted_attempt):
            raise ValueError("v3_supervisor_attempt_anchor_mismatch")
        registration = self._registry.get(token) if type(token) is _Token else None
        if registration is None or registration.attempt != _freeze(attempt):
            raise ValueError("canonical_unknown_or_foreign_reference")
        _deadline(registration.deadline)
        profile = {"reads": 0, "bytes": 0, "entries": [], "old_entry_reads": 0}
        directory = _ClosedDirectory(
            self._store,
            registration.ref,
            registration.entries,
            registration.deadline,
            profile,
        )
        try:
            proposed = transition(
                self._head,
                directory,
                _thaw(registration.attempt),
                _thaw(self._context),
                record=record,
                witness=token,
            )
            _deadline(registration.deadline)
        except CustodyError as error:
            self.lose_authority()
            raise ValueError("unknown_quarantined") from error
        finally:
            self._profile = profile
        candidate = _Candidate(self._head, proposed, registration)
        self._candidates[id(candidate)] = candidate
        return candidate

    @_serialized
    def commit(self, candidate):
        if self._quarantined:
            raise ValueError("unknown_quarantined")
        if (
            self._candidates.get(id(candidate)) is not candidate
            or candidate.head is not self._head
        ):
            raise ValueError("canonical_stale_or_foreign_candidate")
        _deadline(candidate.registration.deadline)
        self._witness(candidate.registration, candidate.registration.deadline)
        if candidate.proposed.last_sample is not None:
            validate_samples(
                [_thaw(candidate.proposed.last_sample)],
                _thaw(self._context),
                historical=False,
                method=VERSION,
            )
        _deadline(candidate.registration.deadline)
        self._head = candidate.proposed
        self._candidates.clear()
        if self._head.interrupted or self._head.last_sample is None:
            self._epoch += 1
            self._leases.clear()
        return self._head

    def _witness(self, registration, deadline):
        try:
            self._store.read(
                registration.ref,
                next(iter(registration.entries)),
                offset=0,
                length=0,
                deadline=deadline,
            )
        except CustodyError as error:
            self.lose_authority()
            raise ValueError("unknown_quarantined") from error

    @_serialized
    def checkout(self, *, deadline: float) -> _ReadLease:
        """O(1): fija head/contexto/epoch y un plazo absoluto, sin copiar historia."""
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError("canonical_read_deadline_invalid")
        _deadline(deadline)
        if self._quarantined or self._head.history is None:
            raise ValueError("unknown_quarantined")
        if self._head.interrupted or self._head.last_sample is None:
            raise ValueError("v3_accreditation_observation_interrupted")
        if self._leases:
            raise ValueError("canonical_read_lease_busy")
        lease = _ReadLease(self, threading.current_thread(), self._lease_seal)
        self._leases[lease] = _LeaseProgress(
            self._head, self._head.history, self._context, deadline, self._epoch
        )
        return lease

    def _lease_progress(self, lease) -> _LeaseProgress:
        # Called only while holding the brief state lock. No supplied owner/epoch.
        if (
            type(lease) is not _ReadLease
            or lease.state is not self
            or lease.identity is not lease
            or lease.seal is not self._lease_seal
            or lease.owner is not threading.current_thread()
        ):
            raise ValueError("canonical_unknown_or_foreign_lease")
        if self._quarantined:
            raise ValueError("unknown_quarantined")
        if self._head.interrupted or self._head.last_sample is None:
            raise ValueError("v3_accreditation_observation_interrupted")
        progress = self._leases.get(lease)
        if progress is None or progress.epoch != self._epoch or progress.finished:
            raise ValueError("canonical_unknown_or_finished_lease")
        if progress.context is not self._context:
            raise ValueError("canonical_context_binding_mismatch")
        _deadline(progress.deadline)
        return progress

    def witness_step(self, lease: _ReadLease) -> bool:
        """Un witness nativo de cero bytes fuera del lock; True al acabar prefijo."""
        with self._lock:
            progress = self._lease_progress(lease)
            if progress.busy:
                raise ValueError("canonical_read_lease_busy")
            if progress.link is None:
                return True
            registration = self._registry.get(progress.link.witness)
            if registration is None:
                self.lose_authority()
                raise ValueError("unknown_quarantined")
            link = progress.link
            progress.busy = True
        try:
            _deadline(progress.deadline)
            self._witness(registration, progress.deadline)
            with self._lock:
                self._lease_progress(lease)
                progress.link = link.previous
                return progress.link is None
        finally:
            with self._lock:
                progress.busy = False

    def finish_accredit(self, lease: _ReadLease) -> dict:
        """Valida frescura actual del snapshot seleccionado y vuelve a comprobar autoridad."""
        with self._lock:
            progress = self._lease_progress(lease)
            if progress.busy or progress.link is not None:
                raise ValueError("canonical_read_lease_unfinished")
            progress.busy = True
        try:
            validate_samples(
                [_thaw(progress.snapshot.last_sample)],
                _thaw(progress.context),
                historical=False,
                method=VERSION,
            )
            with self._lock:
                self._lease_progress(lease)
                result = {
                    "cursor": progress.snapshot.cursor,
                    "prefix": progress.snapshot.rolling_hash,
                }
                _deadline(progress.deadline)
                progress.finished = True
                return result
        finally:
            with self._lock:
                progress.busy = False

    @_serialized
    def release(self, lease: _ReadLease) -> None:
        """Idempotente para capability original/dueño exacto, aun tras revocación."""
        if (
            type(lease) is not _ReadLease
            or lease.state is not self
            or lease.identity is not lease
            or lease.seal is not self._lease_seal
            or lease.owner is not threading.current_thread()
        ):
            raise ValueError("canonical_unknown_or_foreign_lease")
        self._leases.pop(lease, None)

    def accredit(self):
        # Serializa sólo compatibilidad; ingreso/revocación nunca toman este lock.
        deadline = time.perf_counter() + 2
        with self._accreditation_lock:
            lease = self.checkout(deadline=deadline)
            try:
                while not self.witness_step(lease):
                    pass
                return self.finish_accredit(lease)
            finally:
                self.release(lease)

    def offline_samples(self):
        return self._head.samples()
