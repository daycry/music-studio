"""Publicación v3 bajo un único deadline, con recibos externos del supervisor.

EpisodeAcquirer es persistente y sólo lo conduce UN sampler. acquire(stream)
no toca disco ni ejecuta sensores en el padre. Startup lee el contexto sellado
en el hijo (presupuesto separado). El hijo conserva RAW/progreso, valida,
prepara, hace flush/fsync del commit, relee y verifica todos sus bytes.
El padre comprueba el pequeño resultado confiable y observa su finalización.
Sólo entonces emite un recibo en memoria; el coordinador debe custodiarlo.

read_publications exige esos recibos anclados externamente: bytes preparados,
commit o un JSON autodeclarado no prueban aceptación. El audit del recibo se
persiste en el hijo en la siguiente petición; es posterior al commit, jamás
se presenta como reloj del último write. Sin una nueva petición puede no existir.
La publicación aceptada se valida offline con el recibo externo original.
Un ack perdido/tardío no avanza estado: el hijo sólo confirma el candidato
pendiente al recibir el recibo oportuno en la SIGUIENTE llamada. Los rechazos
rompen la adyacencia compartida. No ofrece garantías de disco físico ni RT.
"""

import os
import re
import threading
import time
import uuid
from itertools import pairwise
from pathlib import Path

from benchmark_clock import utc_now
from benchmark_observation import (
    acquisition_context,
    episode_decision,
    observation_policy,
    policy_hash,
    stamp,
)
from benchmark_plan import digest
from benchmark_process import (
    OwnedProcess,
    WorkerDeadline,
    WorkerFailure,
    decode,
    encode,
)
from benchmark_provider import NativeProvider
from benchmark_startup import StartupBudget

VERSION = "wddm_auto_v3"
SCHEMA = "owned_episode_v3"
MAX_FILE = 262144
REPO = Path(__file__).resolve().parents[2]


def confined(path, root=REPO):
    path = Path(path).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("v3_path_outside_root")
    return path


def read_json(path):
    from benchmark_canonical import _BytePath

    if type(path) is _BytePath:
        data = path.read_bytes()
    else:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_FILE + 1)
    try:
        return decode(data if data.endswith(b"\n") else data + b"\n", MAX_FILE)
    except (ValueError, TypeError) as error:
        raise ValueError("v3_invalid_or_partial_json") from error


def sealed_read(path, expected):
    value = read_json(path)
    if digest(value) != expected:
        raise ValueError("v3_file_seal_mismatch")
    return value


def clock():
    return {"utc": utc_now(), "monotonic_ns": time.perf_counter_ns()}


def check_clock(value, start, deadline, *, now=None):
    mono = value["monotonic_ns"]
    if (
        type(mono) is not int
        or not start["monotonic_ns"] <= mono < deadline
        or stamp(value["utc"]) < stamp(start["utc"])
        or abs(
            (mono - start["monotonic_ns"]) / 1e9
            - (stamp(value["utc"]) - stamp(start["utc"]))
        )
        > 0.1
        or (now is not None and stamp(value["utc"]) > stamp(now))
    ):
        raise ValueError("v3_completion_clock_invalid")


def summary(sample):
    return {
        "timestamp": sample["timestamp"],
        "monotonic_ns": sample["monotonic_ns"],
        "nvml": sample["nvml"],
        "windows": {k: sample["windows"][k] for k in ("shared_mb", "dedicated_mb")},
        "wsl": sample["wsl"],
        "schema": "validated_v3_summary",
    }


def verify_prepared(
    prepared, originals, context, previous=None, *, historical=False, now=None
):
    if set(prepared) != {
        "schema",
        "episode_id",
        "ordinal",
        "stream",
        "context",
        "policy_sha256",
        "start",
        "deadline_ns",
        "phase_started_utc",
        "idle",
        "raw_refs",
        "progress_refs",
        "sample_sha256",
        "previous_receipt_sha256",
        "predecessor",
        "validation_finished",
    }:
        raise ValueError("v3_prepared_schema_invalid")
    if (
        prepared["schema"] != SCHEMA
        or prepared["context"] != acquisition_context(context, VERSION)
        or prepared["policy_sha256"] != policy_hash(observation_policy(VERSION))
    ):
        raise ValueError("v3_context_or_policy_invalid")
    start = prepared["start"]
    if (
        type(prepared["deadline_ns"]) is not int
        or prepared["deadline_ns"] != start["monotonic_ns"] + 2_000_000_000
    ):
        raise ValueError("v3_original_deadline_invalid")
    if (
        type(prepared["ordinal"]) is not int
        or prepared["ordinal"] < 1
        or type(prepared["idle"]) is not bool
    ):
        raise ValueError("v3_ordinal_or_idle_invalid")
    if not isinstance(prepared["stream"], str) or not prepared["stream"]:
        raise ValueError("v3_stream_invalid")
    if prepared["previous_receipt_sha256"] != (
        None if previous is None else digest(previous["receipt"])
    ) or prepared["predecessor"] != (None if previous is None else previous["sample"]):
        raise ValueError("v3_predecessor_invalid")
    refs = prepared["raw_refs"]
    if not 1 <= len(refs) <= 3 or len(refs) != len(originals):
        raise ValueError("v3_raw_count_invalid")
    for i, (ref, raw) in enumerate(zip(refs, originals), 1):
        if ref != {"path": f"raw-{i}.json", "ordinal": i, "sha256": digest(raw)}:
            raise ValueError("v3_raw_order_or_seal_invalid")
        if (
            stamp(raw["timestamp"]) < stamp(start["utc"])
            or raw["monotonic_ns"] < start["monotonic_ns"]
        ):
            raise ValueError("v3_raw_before_parent_start")
    completion = prepared["validation_finished"]
    check_clock(completion, start, prepared["deadline_ns"])
    accepted = episode_decision(
        originals,
        context,
        previous=prepared["predecessor"],
        historical=historical,
        now=now,
        idle=prepared["idle"],
        completion=(completion["utc"], completion["monotonic_ns"]),
        phase_started_utc=prepared["phase_started_utc"],
        method=VERSION,
    )
    if accepted is None or digest(accepted) != prepared["sample_sha256"]:
        raise ValueError("v3_acceptance_invalid")
    return accepted


def verify_progress(directory, prepared, originals):
    refs = prepared["progress_refs"]
    if not isinstance(refs, list) or not 1 <= len(refs) <= 64:
        raise ValueError("v3_progress_count_invalid")
    full = []
    last = prepared["start"]
    for i, ref in enumerate(refs, 1):
        if set(ref) != {"path", "sha256"} or ref["path"] != f"progress-{i}.json":
            raise ValueError("v3_progress_order_invalid")
        event = sealed_read(directory / ref["path"], ref["sha256"])
        if set(event) != {"clock", "value"}:
            raise ValueError("v3_progress_schema_invalid")
        check_clock(event["clock"], prepared["start"], prepared["deadline_ns"])
        if event["clock"]["monotonic_ns"] < last["monotonic_ns"] or stamp(
            event["clock"]["utc"]
        ) < stamp(last["utc"]):
            raise ValueError("v3_progress_clock_order_invalid")
        last = event["clock"]
        if event["value"].get("source") == "full_raw":
            if event["value"].get("attempt") != len(full) + 1:
                raise ValueError("v3_progress_raw_order_invalid")
            full.append(event["value"].get("raw"))
    if (
        full != originals
        or last["monotonic_ns"] > prepared["validation_finished"]["monotonic_ns"]
    ):
        raise ValueError("v3_partial_or_omitted_progress")
    if {p.name for p in directory.glob("progress-*.json")} != {
        ref["path"] for ref in refs
    }:
        raise ValueError("v3_omitted_progress_file")


class EpisodeProvider:
    """Factory confiable: make_sensor/checkpoint son seams locales para tests."""

    def __init__(self, config):
        if set(config) != {"root", "context_path", "sensor_config"}:
            raise ValueError("v3_provider_config_invalid")
        self.root = confined(config["root"])
        self.root.mkdir(parents=True, exist_ok=True)
        self.context = read_json(confined(config["context_path"]))
        self.fixture_config = config["sensor_config"]
        self.sensor = self.make_sensor(self.fixture_config)
        self.ordinal = 0
        self.pending = self.previous = None
        self.directory = None
        self.progress_lock = threading.Lock()

    def make_sensor(self, config):
        return NativeProvider(config)

    def checkpoint(self, stage, emit):
        emit({"stage": stage})

    def write(self, name, value, *, commit=False, durable=True):
        path = confined(self.directory / name, self.root)
        data = encode(value, MAX_FILE)
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            if commit:
                self.checkpoint("commit_fsync", self.emit)
            if durable:
                os.fsync(stream.fileno())
        return clock()

    def __call__(self, payload, emit):
        if (
            set(payload) != {"operation", "arguments"}
            or payload["operation"] != "episode_v3"
        ):
            raise ValueError("v3_closed_operation_required")
        args = payload["arguments"]
        if set(args) != {
            "episode_id",
            "stream",
            "start",
            "deadline_ns",
            "phase_started_utc",
            "idle",
            "confirm",
            "enforce",
        }:
            raise ValueError("v3_arguments_invalid")
        if not re.fullmatch(r"[0-9a-f]{32}", args["episode_id"]):
            raise ValueError("v3_episode_id_invalid")
        if args["deadline_ns"] != args["start"]["monotonic_ns"] + 2_000_000_000:
            raise ValueError("v3_original_deadline_invalid")
        # Confirmation is supplied ONLY by the supervisor after its previous
        # timely return. A candidate's files or child completion never suffice.
        confirm = args["confirm"]
        if confirm is not None:
            if self.pending is None or confirm["proof"] != self.pending["proof"]:
                raise ValueError("v3_confirmation_invalid")
            validate_receipt(confirm, self.context)
            self.previous = {"receipt": confirm, "sample": self.pending["sample"]}
            self.directory = self.root / confirm["episode_id"]
            self.emit = emit
            self.write(
                "supervisor-audit.json",
                {
                    "kind": "audit_of_completed_commit",
                    "receipt": confirm,
                    "audit_started": clock(),
                },
                durable=False,
            )
        else:
            self.previous = None
        self.pending = None
        self.ordinal += 1
        self.directory = self.root / args["episode_id"]
        self.directory.mkdir()
        self.emit = emit
        self.progress_index = 0
        self.progress_refs = []
        manifest = {
            "schema": SCHEMA,
            "ordinal": self.ordinal,
            "episode_id": args["episode_id"],
            "request": args,
            "context": acquisition_context(self.context, VERSION),
        }
        self.write("request.json", manifest)

        def progress(value):
            # Keep the genuine frame in parent memory BEFORE potentially slow
            # persistence. Already written bytes remain invalid after interruption.
            # NativeProvider may call this callback concurrently: the Windows
            # sampler emits intermediate PDH frames from its worker thread while
            # the parallel observer publishes completed operations.
            with self.progress_lock:
                emit(value)
                self.progress_index += 1
                name = f"progress-{self.progress_index}.json"
                event = {"clock": clock(), "value": value}
                self.write(name, event)
                self.progress_refs.append({"path": name, "sha256": digest(event)})

        originals = []
        accepted = None
        try:
            for attempt in range(1, 4):
                raw = self.sensor(
                    {
                        "operation": "sample",
                        "arguments": {
                            "observation_context": self.context,
                            "observation_method": VERSION,
                        },
                    },
                    progress,
                )
                progress({"source": "full_raw", "attempt": attempt, "raw": raw})
                self.checkpoint("raw_write", emit)
                self.write(f"raw-{attempt}.json", raw)
                originals.append(raw)
                if not args["enforce"]:
                    raise ValueError("v3_raw_only_not_accepted")
                self.checkpoint("validation", emit)
                try:
                    accepted = episode_decision(
                        originals,
                        self.context,
                        previous=None
                        if self.previous is None
                        else self.previous["sample"],
                        idle=args["idle"],
                        phase_started_utc=args["phase_started_utc"],
                        method=VERSION,
                    )
                except ValueError as error:
                    if (
                        str(error) == "auto_dedicated_disagreement"
                        and attempt < 3
                    ):
                        continue
                    raise
                if accepted is not None:
                    break
            if accepted is None:
                raise ValueError("v3_dedicated_disagreement")
            prepared = {
                "schema": SCHEMA,
                "episode_id": args["episode_id"],
                "ordinal": self.ordinal,
                "stream": args["stream"],
                "context": acquisition_context(self.context, VERSION),
                "policy_sha256": policy_hash(observation_policy(VERSION)),
                "start": args["start"],
                "deadline_ns": args["deadline_ns"],
                "phase_started_utc": args["phase_started_utc"],
                "idle": args["idle"],
                "raw_refs": [
                    {"path": f"raw-{i}.json", "ordinal": i, "sha256": digest(v)}
                    for i, v in enumerate(originals, 1)
                ],
                "progress_refs": self.progress_refs,
                "sample_sha256": digest(accepted),
                "previous_receipt_sha256": None
                if self.previous is None
                else digest(self.previous["receipt"]),
                "predecessor": None
                if self.previous is None
                else self.previous["sample"],
                "validation_finished": clock(),
            }
            verify_prepared(prepared, originals, self.context, self.previous)
            verify_progress(self.directory, prepared, originals)
            self.checkpoint("prepared_write", emit)
            self.write("prepared.json", prepared)
            commit = {
                "schema": SCHEMA,
                "episode_id": args["episode_id"],
                "prepared_sha256": digest(prepared),
                "write_started": clock(),
            }
            self.checkpoint("commit_write", emit)
            commit_finished = self.write("commit.json", commit, commit=True)
            self.checkpoint("verification", emit)
            reread = sealed_read(self.directory / "prepared.json", digest(prepared))
            sealed_read(self.directory / "commit.json", digest(commit))
            raws = [
                sealed_read(self.directory / ref["path"], ref["sha256"])
                for ref in reread["raw_refs"]
            ]
            verify_prepared(reread, raws, self.context, self.previous)
            verify_progress(self.directory, reread, raws)
            proof = {
                "schema": SCHEMA,
                "episode_id": args["episode_id"],
                "ordinal": self.ordinal,
                "prepared_sha256": digest(prepared),
                "commit_sha256": digest(commit),
                "sample_sha256": digest(accepted),
                "summary_sha256": digest(summary(accepted)),
                "commit_finished": commit_finished,
                "verification_finished": clock(),
            }
            check_clock(
                proof["verification_finished"], args["start"], args["deadline_ns"]
            )
            self.pending = {"proof": proof, "sample": accepted}
            return {"proof": proof, "summary": summary(accepted)}
        except ValueError as error:
            self.previous = self.pending = None
            rejection = {"status": "rejected", "error": str(error), "clock": clock()}
            self.write("rejected.json", rejection)
            return {
                "rejected": str(error),
                "episode_id": args["episode_id"],
                "ordinal": self.ordinal,
                "request_sha256": digest(manifest),
                "rejection_sha256": digest(rejection),
                "raw_refs": [
                    {"path": f"raw-{i}.json", "sha256": digest(v)}
                    for i, v in enumerate(originals, 1)
                ],
                "progress_refs": self.progress_refs,
            }

    def close(self):
        self.sensor.close()


def verify_ownership(ownership):
    if (
        not isinstance(ownership, dict)
        or set(ownership) != {"pid", "creation_time", "job_member"}
        or type(ownership["pid"]) is not int
        or ownership["pid"] <= 0
        or type(ownership["creation_time"]) is not int
        or ownership["creation_time"] <= 0
        or ownership["job_member"] is not True
    ):
        raise ValueError("v3_supervisor_identity_invalid")


def validate_receipt(receipt, context):
    """Comprobación estructural y temporal; autenticidad requiere ancla externa."""
    if (
        set(receipt)
        != {
            "schema",
            "episode_id",
            "ordinal",
            "start",
            "deadline_ns",
            "observed_utc",
            "observed_monotonic_ns",
            "proof",
            "previous_receipt_sha256",
            "context_sha256",
            "ownership",
        }
        or receipt["schema"] != SCHEMA
    ):
        raise ValueError("v3_supervisor_schema_invalid")
    if receipt["context_sha256"] != digest(acquisition_context(context, VERSION)):
        raise ValueError("v3_supervisor_context_invalid")
    proof = receipt["proof"]
    if (
        set(proof)
        != {
            "schema",
            "episode_id",
            "ordinal",
            "prepared_sha256",
            "commit_sha256",
            "sample_sha256",
            "summary_sha256",
            "commit_finished",
            "verification_finished",
        }
        or proof["schema"] != SCHEMA
        or (proof["episode_id"], proof["ordinal"])
        != (receipt["episode_id"], receipt["ordinal"])
    ):
        raise ValueError("v3_supervisor_proof_invalid")
    start, deadline = receipt["start"], receipt["deadline_ns"]
    if type(deadline) is not int or deadline != start["monotonic_ns"] + 2_000_000_000:
        raise ValueError("v3_original_deadline_invalid")
    times = [
        proof["commit_finished"],
        proof["verification_finished"],
        {
            "utc": receipt["observed_utc"],
            "monotonic_ns": receipt["observed_monotonic_ns"],
        },
    ]
    for point in times:
        check_clock(point, start, deadline)
    if any(
        a["monotonic_ns"] > b["monotonic_ns"] or stamp(a["utc"]) > stamp(b["utc"])
        for a, b in pairwise(times)
    ):
        raise ValueError("v3_completion_order_invalid")
    verify_ownership(receipt["ownership"])
    if not re.fullmatch(r"[0-9a-f]{32}", receipt["episode_id"]):
        raise ValueError("v3_supervisor_identity_invalid")


class EpisodeAcquirer:
    """Un solo sampler; receipts son aceptaciones supervisadas en memoria.

    root/context_path deben pertenecer al repositorio. La lectura de contexto se
    realiza en startup fuera del plazo del episodio. El coordinador puede persistir
    receipts posteriormente como audit, sin atribuirle el reloj del commit previo.
    Tras un timeout el proceso queda cerrado; crear sustituto requiere startup nuevo.
    """

    observation_method = VERSION

    def __init__(
        self,
        *,
        root,
        context_path,
        sensor_config=None,
        trusted_handler="benchmark_episode:EpisodeProvider",
        startup_timeout_s=5,
        startup_deadline_ns=None,
    ):
        budget = StartupBudget.from_timeout(
            startup_timeout_s, deadline_ns=startup_deadline_ns
        )
        if not budget.remaining_ns():
            raise WorkerDeadline("episode_startup_deadline")
        self.root = confined(root)
        self.observation_context = read_json(confined(context_path))
        self.context_sha256 = digest(
            acquisition_context(self.observation_context, VERSION)
        )
        self.phase_started_utc = None
        self.previous_receipt = None
        self.receipts = []
        self.attempts = []
        self.ordinal = 0
        self.last_interrupted = None
        self.last_record = None
        if not budget.remaining_ns():
            raise WorkerDeadline("episode_startup_deadline")
        self.worker = OwnedProcess(
            {
                "root": str(self.root),
                "context_path": str(confined(context_path)),
                "sensor_config": sensor_config or {},
            },
            trusted_handler,
            startup_timeout_s=startup_timeout_s,
            startup_deadline_ns=budget.deadline_ns,
        )

    def acquire(self, stream, *, idle=False, enforce=True):
        from benchmark_canonical_integration import canonical_for_acquirer

        canonical = canonical_for_acquirer(self)
        started = clock()
        deadline = started["monotonic_ns"] + 2_000_000_000
        episode_id = uuid.uuid4().hex
        self.ordinal += 1
        previous = self.previous_receipt
        args = {
            "episode_id": episode_id,
            "stream": str(stream),
            "start": started,
            "deadline_ns": deadline,
            "phase_started_utc": self.phase_started_utc,
            "idle": idle,
            "confirm": previous,
            "enforce": enforce,
        }
        self.last_record = self.last_interrupted = None
        result = None
        recorded_rejection = False
        try:
            result = self.worker.call(
                {"operation": "episode_v3", "arguments": args}, deadline_ns=deadline
            )
            value = result["value"]
            if "rejected" in value:
                self.previous_receipt = None
                if canonical is not None:
                    canonical.ingest_latest()
                    attempt = canonical.last_attempt
                    if attempt["status"] != "rejected" or attempt["request"] != args:
                        raise WorkerFailure("canonical_rejected_attempt_changed")
                    self.attempts.append(attempt)
                    recorded_rejection = True
                    raise ValueError("observability_lost_" + value["rejected"])
                self.attempts.append(
                    {
                        "status": "rejected",
                        "episode_id": episode_id,
                        "result": value,
                        "request": args,
                        "ownership": result["ownership"],
                        "observed": clock(),
                    }
                )
                recorded_rejection = True
                raise ValueError("observability_lost_" + value["rejected"])
            if (
                set(value) != {"proof", "summary"}
                or value["proof"]["episode_id"] != episode_id
            ):
                raise WorkerFailure("v3_publication_result_invalid")
            encode(value, 4096)
            if (
                value["proof"]["ordinal"] != self.ordinal
                or digest(value["summary"]) != value["proof"]["summary_sha256"]
            ):
                raise WorkerFailure("v3_summary_or_ordinal_invalid")
            if canonical is not None:
                canonical.ingest_latest()
                receipt = canonical.last_receipt
                if (
                    canonical.last_attempt["status"] != "accepted"
                    or receipt["proof"] != value["proof"]
                    or receipt["start"] != started
                    or receipt["deadline_ns"] != deadline
                    or receipt["ownership"] != result["ownership"]
                    or canonical.publication["confirmed"] > deadline
                ):
                    raise WorkerFailure("canonical_accepted_attempt_changed")
                validate_receipt(receipt, self.observation_context)
                if time.perf_counter_ns() >= deadline - 100_000_000:
                    raise WorkerDeadline("v3_parent_acceptance_late")
                self.last_record = {
                    "supervisor_receipt": receipt,
                    "sample": value["summary"],
                }
                self.receipts.append(receipt)
                self.previous_receipt = receipt
                self.attempts.append(canonical.last_attempt)
                return value["summary"]
            observed = clock()
            receipt = {
                "schema": SCHEMA,
                "episode_id": episode_id,
                "ordinal": value["proof"]["ordinal"],
                "start": started,
                "deadline_ns": deadline,
                "observed_utc": observed["utc"],
                "observed_monotonic_ns": observed["monotonic_ns"],
                "proof": value["proof"],
                "previous_receipt_sha256": None
                if previous is None
                else digest(previous),
                "context_sha256": self.context_sha256,
                "ownership": result["ownership"],
            }
            validate_receipt(receipt, self.observation_context)
            observed = clock()
            receipt["observed_utc"] = observed["utc"]
            receipt["observed_monotonic_ns"] = observed["monotonic_ns"]
            # Pure, finite in-memory verification only; no parent filesystem or
            # arbitrary source callable. Check again after constructing receipt.
            if time.perf_counter_ns() >= deadline - 100_000_000:
                raise WorkerDeadline("v3_parent_acceptance_late")
            self.last_record = {
                "supervisor_receipt": receipt,
                "sample": value["summary"],
            }
            self.receipts.append(receipt)
            self.previous_receipt = receipt
            self.attempts.append({"status": "accepted", "receipt": receipt})
            return value["summary"]
        except (
            WorkerFailure,
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
        ) as caught:
            if recorded_rejection:
                raise
            failure = (
                caught
                if isinstance(caught, WorkerFailure)
                else WorkerFailure("v3_parent_verification_invalid_" + str(caught))
            )
            if result is not None:
                failure.progress = result["progress"]
                failure.evidence = {
                    "ownership": result["ownership"],
                    "parent_result_observed": result.get(
                        "parent_finished_monotonic_ns"
                    ),
                    "verification_failure": str(failure),
                }
            self.previous_receipt = None
            if canonical is not None:
                try:
                    canonical.close()
                except BaseException as cleanup:  # noqa: BLE001 - preserve interruption and its original native evidence
                    try:
                        from benchmark_coordinator import safe_cleanup_error_record

                        failure.evidence["canonical_cleanup_error"] = {
                            "type": type(cleanup).__name__[:128],
                            "message_sha256": None,
                            "observed": None,
                        }
                        failure.evidence["canonical_cleanup_error"] = (
                            safe_cleanup_error_record(cleanup)
                        )
                    except BaseException:  # noqa: BLE001,S110 - la custodia secundaria tampoco sustituye la primera causa
                        pass
            self.last_interrupted = {
                "status": "incomplete_invalid",
                "episode_id": episode_id,
                "progress": failure.progress,
                "evidence": failure.evidence,
            }
            self.attempts.append(
                {
                    "status": "interrupted",
                    "episode_id": episode_id,
                    "ordinal": self.ordinal,
                    "request": args,
                    "interrupted": self.last_interrupted,
                }
            )
            try:
                self.worker.close(graceful=False)
            except BaseException as cleanup:  # noqa: BLE001 - preservar la primera causa de proof/canónico
                try:
                    from benchmark_coordinator import safe_cleanup_error_record

                    failure.evidence["cleanup_error"] = safe_cleanup_error_record(
                        cleanup
                    )
                except BaseException:  # noqa: BLE001,S110 - ni la custodia secundaria sustituye la primera causa
                    pass
            if failure is caught:
                raise
            raise failure

    def close(self):
        from benchmark_canonical_integration import canonical_for_acquirer

        canonical = canonical_for_acquirer(self)
        try:
            if canonical is not None:
                canonical.close()
        finally:
            self.worker.close()


def read_attempt_inventory(root, attempts, context, *, trusted_attempts):
    """Audit de rechazos/RAW parciales anclado en resultados del supervisor.

    Una interrupción puede dejar el último archivo truncado. Se conserva como tal;
    el lector no lo convierte en RAW completo ni lo usa como muestra/predecesor.
    """
    if trusted_attempts is None or [digest(a) for a in attempts] != [
        digest(a) for a in trusted_attempts
    ]:
        raise ValueError("v3_supervisor_attempt_anchor_mismatch")
    root = confined(root)
    previous_start = None
    accepted = []
    breaks = set()
    last_rejected = False
    for ordinal, attempt in enumerate(attempts, 1):
        from benchmark_canonical import validate_inventory_attempt

        status = attempt["status"]
        if status not in {"accepted", "rejected", "interrupted"}:
            raise ValueError("v3_attempt_status_invalid")
        episode_id = (
            attempt["receipt"]["episode_id"]
            if status == "accepted"
            else attempt["request"]["episode_id"]
        )
        directory = confined(root / episode_id, root)
        start = validate_inventory_attempt(directory, attempt, ordinal, context)
        if status == "accepted":
            receipt = attempt["receipt"]
            accepted.append(receipt)
            if last_rejected:
                breaks.add(receipt["episode_id"])
            last_rejected = False
        else:
            last_rejected = True
        if previous_start is not None and (
            start["monotonic_ns"] <= previous_start["monotonic_ns"]
            or stamp(start["utc"]) <= stamp(previous_start["utc"])
        ):
            raise ValueError("v3_attempt_replayed")
        previous_start = start
    return accepted, breaks


def read_publications(
    root,
    receipts,
    context,
    *,
    trusted_receipts,
    attempts=None,
    trusted_attempts=None,
    now=None,
    historical=False,
    idle=False,
):
    """Recomputación offline anclada en los recibos originales del supervisor.

    El llamador custodia trusted_receipts de forma independiente o en su ledger
    sellado. Usar los propios ficheros no confiables como ancla no autentica nada.
    Los directorios sin ack siguen rechazados. attempts/trusted_attempts acreditan
    los rechazos entre segmentos; no se deben emparejar muestras a través de ellos.
    historical=True permite auditar registros antiguos sin fingir frescura actual.
    """
    root = confined(root)
    if [digest(r) for r in receipts] != [digest(r) for r in trusted_receipts]:
        raise ValueError("v3_supervisor_anchor_mismatch")
    breaks = set()
    if attempts is not None:
        inventory, breaks = read_attempt_inventory(
            root, attempts, context, trusted_attempts=trusted_attempts
        )
        if inventory != receipts:
            raise ValueError("v3_omitted_attempt_acceptance")
    accepted = []
    previous = None
    ordinal = 0
    try:
        for receipt in receipts:
            validate_receipt(receipt, context)
            if receipt["ordinal"] <= ordinal:
                raise ValueError("v3_replayed_or_reordered_receipt")
            if receipt["episode_id"] in breaks:
                previous = None
            if receipt["previous_receipt_sha256"] != (
                None if previous is None else digest(previous["receipt"])
            ):
                # A rejection breaks adjacency; a later coordinator must include
                # its rejected attempt inventory when validating such restarts.
                raise ValueError("v3_missing_predecessor_or_rejection_inventory")
            if (
                ordinal == 0
                and receipt["ordinal"] != 1
                and receipt["episode_id"] not in breaks
            ):
                raise ValueError("v3_missing_origin")
            directory = confined(root / receipt["episode_id"], root)
            from benchmark_canonical import validate_accepted

            sample = validate_accepted(
                directory,
                receipt,
                context,
                previous,
                historical=historical,
                now=now,
                idle=idle,
            )
            accepted.append(sample)
            previous = {"receipt": receipt, "sample": sample}
            ordinal = receipt["ordinal"]
        return accepted
    except (KeyError, TypeError, AttributeError, IndexError, OSError) as error:
        raise ValueError("v3_incomplete_publication") from error


def read_publications_delta(
    root,
    receipts,
    context,
    *,
    trusted_receipts,
    prefix_receipts,
    prefix_attempts,
    prefix_records,
    attempts,
    trusted_attempts,
    now=None,
    historical=False,
    idle=False,
):
    """Audita sólo un segmento nuevo sobre un prefijo ya validado.

    El prefijo llega de la custodia del supervisor y no se vuelve a abrir. La
    primera muestra nueva transporta su predecesora completa en ``prepared``;
    se contrasta contra el resumen sellado del prefijo antes de validar el
    directorio nuevo. Así el delta conserva la misma semántica de
    ``read_publications`` sin convertir cada tick en un escaneo histórico.
    """
    root = confined(root)
    if [digest(r) for r in receipts] != [digest(r) for r in trusted_receipts]:
        raise ValueError("v3_supervisor_anchor_mismatch")
    if len(prefix_receipts) != len(prefix_records):
        raise ValueError("v3_delta_prefix_shape_invalid")
    prefix_attempts = list(prefix_attempts)
    attempts = list(attempts)
    if len(attempts) < len(prefix_attempts):
        raise ValueError("v3_delta_attempt_prefix_shorter")
    if [digest(a) for a in attempts[: len(prefix_attempts)]] != [
        digest(a) for a in prefix_attempts
    ]:
        raise ValueError("v3_delta_attempt_prefix_mismatch")
    if [digest(a) for a in attempts] != [digest(a) for a in trusted_attempts]:
        raise ValueError("v3_supervisor_attempt_anchor_mismatch")

    suffix_attempts = attempts[len(prefix_attempts) :]
    suffix_receipts, breaks = read_attempt_inventory_delta(
        root,
        suffix_attempts,
        context,
        trusted_attempts=suffix_attempts,
        ordinal=len(prefix_attempts) + 1,
        previous_attempt=None if not prefix_attempts else prefix_attempts[-1],
    )
    if suffix_receipts != list(receipts):
        raise ValueError("v3_omitted_attempt_acceptance")

    accepted = []
    previous_receipt = prefix_receipts[-1] if prefix_receipts else None
    previous_summary = prefix_records[-1]["sample"] if prefix_records else None
    ordinal = prefix_receipts[-1]["ordinal"] if prefix_receipts else 0
    for receipt in receipts:
        validate_receipt(receipt, context)
        if receipt["ordinal"] <= ordinal:
            raise ValueError("v3_replayed_or_reordered_receipt")
        if receipt["episode_id"] in breaks or previous_receipt is None:
            previous = None
        else:
            directory = confined(root / receipt["episode_id"], root)
            from benchmark_canonical import validate_accepted

            prepared = sealed_read(directory / "prepared.json", receipt["proof"]["prepared_sha256"])
            predecessor = prepared.get("predecessor")
            if summary(predecessor) != previous_summary:
                raise ValueError("v3_delta_predecessor_anchor_mismatch")
            previous = {"receipt": previous_receipt, "sample": predecessor}
        directory = confined(root / receipt["episode_id"], root)
        from benchmark_canonical import validate_accepted

        sample = validate_accepted(
            directory,
            receipt,
            context,
            previous,
            historical=historical,
            now=now,
            idle=idle,
        )
        accepted.append(sample)
        previous_receipt = receipt
        previous_summary = summary(sample)
        ordinal = receipt["ordinal"]
    return accepted


def read_attempt_inventory_delta(
    root,
    attempts,
    context,
    *,
    trusted_attempts,
    ordinal,
    previous_attempt=None,
):
    """Valida únicamente intentos nuevos, usando el último encabezado en RAM."""
    if [digest(a) for a in attempts] != [digest(a) for a in trusted_attempts]:
        raise ValueError("v3_supervisor_attempt_anchor_mismatch")
    root = confined(root)
    previous_start = None
    last_rejected = False
    if previous_attempt is not None:
        status = previous_attempt["status"]
        previous_start = (
            previous_attempt["receipt"]["start"]
            if status == "accepted"
            else previous_attempt["request"]["start"]
        )
        last_rejected = status != "accepted"
    accepted = []
    breaks = set()
    for attempt in attempts:
        from benchmark_canonical import validate_inventory_attempt

        status = attempt["status"]
        if status not in {"accepted", "rejected", "interrupted"}:
            raise ValueError("v3_attempt_status_invalid")
        episode_id = (
            attempt["receipt"]["episode_id"]
            if status == "accepted"
            else attempt["request"]["episode_id"]
        )
        directory = confined(root / episode_id, root)
        start = validate_inventory_attempt(directory, attempt, ordinal, context)
        if previous_start is not None and (
            start["monotonic_ns"] <= previous_start["monotonic_ns"]
            or stamp(start["utc"]) <= stamp(previous_start["utc"])
        ):
            raise ValueError("v3_attempt_replayed")
        if status == "accepted":
            receipt = attempt["receipt"]
            accepted.append(receipt)
            if last_rejected:
                breaks.add(receipt["episode_id"])
            last_rejected = False
        else:
            last_rejected = True
        previous_start = start
        ordinal += 1
    return accepted, breaks
