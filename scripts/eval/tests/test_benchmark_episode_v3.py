"""CPU explícitamente sintética, procesos Windows reales, relojes reales.

No es calibración GPU. Las demoras se inyectan en operaciones verdaderas
del hijo, nunca mediante timestamps ficticios o booleanos de finalización.
"""

import ast
import copy
import json
import time
import uuid
from pathlib import Path

import pytest
from benchmark_episode import EpisodeAcquirer, read_publications
from benchmark_process import WorkerFailure, process_alive

PHASE = Path.cwd() / ".cache/dev-cycle/t09/publication-v3-implementation"


@pytest.mark.parametrize("recording_fault", [False, True])
def test_firstcause_proof_keeps_original_after_native_sensor_cleanup_fault(
    episode_factory, monkeypatch, recording_fault
):
    """Controlled parent proof/Job termination faults after real native response."""
    import benchmark_coordinator as coordinator
    import benchmark_episode as episode

    observer, _ = episode_factory()
    primary = WorkerFailure("controlled_parent_proof_firstcause")
    proof_seen = []

    def proof_failure(receipt, context):
        assert observer.worker._last_completion is not None
        assert observer.worker.ownership["job_member"] is True
        assert observer.worker.reader.is_alive()
        proof_seen.append(receipt)
        raise primary

    def terminate_fault():
        raise OSError("controlled_owned_sensor_job_termination_fault")

    def recording_error(error):
        raise RuntimeError("controlled_secondary_recording_fault")

    monkeypatch.setattr(episode, "validate_receipt", proof_failure)
    monkeypatch.setattr(observer.worker.job, "terminate", terminate_fault)
    if recording_fault:
        monkeypatch.setattr(coordinator, "cleanup_error_record", recording_error)
    try:
        with pytest.raises(BaseException) as caught:
            observer.acquire("controlled-firstcause")
        assert proof_seen
        assert caught.value is primary
        assert type(caught.value) is WorkerFailure
        assert primary.evidence["cleanup_error"]["type"] == "WorkerFailure"
        assert observer.previous_receipt is None
        assert observer.receipts == []
        assert observer.attempts[-1]["status"] == "interrupted"
        assert observer.worker.close_evidence["resources_returned"] is False
        assert observer.worker.close_evidence["disposition"] == "UNKNOWN_QUARANTINED"
    finally:
        observer.close()
        assert observer.worker.process.poll() is not None
        assert not observer.worker.reader.is_alive()


def test_firstcause_successful_episode_does_not_swallow_native_cleanup_fault(
    episode_factory, monkeypatch
):
    """No primary proof error: actual sensor cleanup fault must propagate."""
    observer, _ = episode_factory()
    observer.acquire("controlled-success-before-cleanup")

    def terminate_fault():
        raise OSError("controlled_cleanup_without_primary")

    monkeypatch.setattr(observer.worker.job, "terminate", terminate_fault)
    try:
        with pytest.raises(WorkerFailure, match="controlled_cleanup_without_primary"):
            observer.close()
        assert observer.worker.close_evidence["resources_returned"] is False
    finally:
        observer.close()
        assert observer.worker.process.poll() is not None
        assert not observer.worker.reader.is_alive()


@pytest.fixture
def episode_factory():
    folder = PHASE / "v3-fixtures" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    fixture = folder / "sensor_fixture.py"
    original = ast.parse(
        (Path.cwd() / "scripts/eval/tests/test_benchmark_observation.py").read_text(
            encoding="utf-8"
        )
    )
    names = {
        "NOW",
        "BROWSER",
        "CONTEXT",
        "INSTANCE",
        "UTC_ZONE",
        "utc",
        "bracket",
        "sample",
    }
    nodes = [
        n
        for n in original.body
        if (
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)
        )
        or (isinstance(n, ast.FunctionDef) and n.name in names)
    ]
    (folder / "sensor_values.py").write_text(
        "import copy\nfrom datetime import datetime,timedelta,timezone\n"
        + "\n".join(ast.unparse(n) for n in nodes),
        encoding="utf-8",
    )
    # Trusted CPU sensor fixture reuses the historic values, replacing EVERY
    # acquisition/operation/FILETIME clock with actual calls around its work.
    fixture.write_text(
        """import copy, importlib.util, time, subprocess, sys, threading
from pathlib import Path
from benchmark_episode import EpisodeProvider
from benchmark_clock import utc_now
from benchmark_observation import acquisition_context, stamp
spec=importlib.util.spec_from_file_location("historical_sensor_values",Path(__file__).with_name("sensor_values.py"))
values=importlib.util.module_from_spec(spec);spec.loader.exec_module(values)
class Sensor:
    def __init__(self,config):
        self.config=config;self.count=0
    def __call__(self,payload,emit):
        self.count+=1
        if self.config.get("concurrent_progress"):
            barrier=threading.Barrier(8)
            def publish(index):
                barrier.wait()
                emit({"source":"synthetic_concurrent", "index":index})
            threads=[threading.Thread(target=publish,args=(index,)) for index in range(32)]
            for thread in threads:thread.start()
            for thread in threads:thread.join()
        emit({"source":"synthetic_partial","actual_count":self.count})
        if self.config.get("block_stage")=="sampling":
            child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"])
            emit({"source":"synthetic_descendant","pid":child.pid});time.sleep(3)
        if self.config.get("delay_each_s"):time.sleep(self.config["delay_each_s"])
        raw=values.sample(0)
        raw["acquisition_context"]=acquisition_context(payload["arguments"]["observation_context"],"wddm_auto_v3")
        raw["timestamp"]=utc_now();raw["monotonic_ns"]=time.perf_counter_ns()
        a=utc_now();ma=time.perf_counter_ns()
        q=utc_now();ft=int(stamp(q)*10000000)+116444736000000000
        time.sleep(.001)
        b=utc_now();mb=time.perf_counter_ns()
        bracket={"started_utc":a,"finished_utc":b,"started_monotonic_ns":ma,"finished_monotonic_ns":mb}
        raw["operations"]={k:copy.deepcopy(bracket) for k in raw["operations"]}
        raw["windows"]["collection"]=copy.deepcopy(bracket)
        raw["windows"]["query_filetime"]=raw["windows"]["query_utc_filetime"]=ft
        for counter in raw["windows"]["counters"].values():
            counter["raw_filetime"]=counter["raw_utc_filetime"]=ft
        if self.config.get("mismatch") and self.count <= self.config["mismatch"]:
            raw["windows"]["dedicated_mb"]+=200
            c=raw["windows"]["counters"]["dedicated_mb"]
            c["raw_value"]=c["formatted_value"]=raw["windows"]["dedicated_mb"]*2**20
        if self.config.get("invalid"):
            raw["browser"]["visible"]=False
        emit({"source":"synthetic_full","raw":raw})
        return raw
    def close(self):pass
class Fixture(EpisodeProvider):
    def make_sensor(self,config):return Sensor(config)
    def checkpoint(self,stage,emit):
        super().checkpoint(stage,emit)
        if self.fixture_config.get("block_stage")==stage:time.sleep(3)
""",
        encoding="utf-8",
    )
    from test_benchmark_observation import CONTEXT

    context = copy.deepcopy(CONTEXT)
    context_path = folder / "context.json"
    context_path.write_text(json.dumps(context), encoding="utf-8")

    def make(**config):
        return EpisodeAcquirer(
            root=folder / uuid.uuid4().hex / "publications",
            context_path=context_path,
            trusted_handler=f"{fixture}:Fixture",
            sensor_config=config,
        ), context

    return make


def test_concurrent_sensor_progress_keeps_episode_refs_in_wire_order(episode_factory):
    observer, _ = episode_factory(concurrent_progress=True)
    try:
        receipt = observer.acquire("concurrent-progress")
        assert receipt["schema"] == "validated_v3_summary"
        assert observer.receipts[-1]["episode_id"]
    finally:
        observer.close()


def test_transient_dedicated_mismatch_gets_one_bounded_extra_sample(episode_factory):
    observer, _ = episode_factory(mismatch=2)
    try:
        summary = observer.acquire("transient-dedicated-mismatch")
        assert summary["schema"] == "validated_v3_summary"
    finally:
        observer.close()


@pytest.mark.parametrize(
    "stage",
    [
        "sampling",
        "validation",
        "raw_write",
        "prepared_write",
        "commit_write",
        "commit_fsync",
        "verification",
    ],
    ids=str,
)
def test_blocked_episode_is_bounded_and_never_advances(episode_factory, stage):
    observer, _ = episode_factory(block_stage=stage)
    pid = observer.worker.pid
    started = time.perf_counter_ns()
    from benchmark_clock import utc_now

    started_utc = utc_now()
    with pytest.raises(WorkerFailure):
        observer.acquire("phase")
    returned = time.perf_counter_ns()
    returned_utc = utc_now()
    elapsed = (returned - started) / 1e9
    assert elapsed < 2.05
    assert observer.previous_receipt is None
    assert observer.receipts == []
    assert observer.last_interrupted["status"] == "incomplete_invalid"
    assert observer.last_interrupted["progress"]
    assert not process_alive(pid)
    assert not observer.worker.reader.is_alive()
    assert observer.worker.close_evidence["job_empty"]
    assert observer.worker.close_evidence["errors"] == []
    for event in observer.last_interrupted["progress"]:
        v = event["value"]
        if v.get("source") == "synthetic_descendant":
            assert not process_alive(v["pid"])
    assert list(observer.root.rglob("*.json"))
    assert (
        read_publications(
            observer.root, [], observer.observation_context, trusted_receipts=[]
        )
        == []
    )
    audit = PHASE / "measurements-v3"
    audit.mkdir(exist_ok=True)
    (audit / f"blocked-{stage}-{uuid.uuid4().hex}.json").write_text(
        json.dumps(
            {
                "kind": "audit_after_interrupted_return",
                "stage": stage,
                "started_utc": started_utc,
                "returned_utc": returned_utc,
                "started_monotonic_ns": started,
                "returned_monotonic_ns": returned,
                "elapsed_s": elapsed,
                "interrupted": observer.last_interrupted,
                "cleanup": observer.worker.close_evidence,
                "audit_written_utc": utc_now(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_valid_publication_requires_supervisor_receipt_and_full_recomputation(
    episode_factory,
):
    observer, context = episode_factory()
    try:
        first = observer.acquire("phase")
        second = observer.acquire("phase")
        assert first["nvml"]["used_mb"] == second["nvml"]["used_mb"] == 1200
        assert len(observer.receipts) == 2
        assert observer.receipts[1]["previous_receipt_sha256"]
        accepted = read_publications(
            observer.root,
            observer.receipts,
            context,
            trusted_receipts=observer.receipts,
        )
        assert len(accepted) == 2
        assert all(x["acquisition_context"]["policy_sha256"] for x in accepted)
        with pytest.raises(ValueError, match="supervisor"):
            read_publications(
                observer.root, observer.receipts, context, trusted_receipts=[]
            )
        from benchmark_clock import utc_now

        audit = PHASE / "measurements-v3"
        audit.mkdir(exist_ok=True)
        (audit / f"cpu-success-{uuid.uuid4().hex}.json").write_text(
            json.dumps(
                {
                    "kind": "audit_of_completed_cpu_synthetic_publications",
                    "root": str(observer.root.relative_to(Path.cwd())),
                    "context": context,
                    "receipts": observer.receipts,
                    "attempts": observer.attempts,
                    "audit_written_utc": utc_now(),
                    "gpu_calibration": False,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        observer.close()


@pytest.mark.parametrize(
    "attack",
    [
        "omit",
        "reorder",
        "replay",
        "context",
        "late",
        "partial",
        "forged_commit",
        "phase",
        "retry",
        "predecessor",
    ],
)
def test_offline_rejects_modified_or_incomplete_evidence(episode_factory, attack):
    observer, context = episode_factory(mismatch=1)
    try:
        observer.acquire("phase")
        observer.acquire("phase")
        records = copy.deepcopy(observer.receipts)
        if attack == "omit":
            records.pop(0)
        elif attack == "reorder":
            records.reverse()
        elif attack == "replay":
            records[1] = copy.deepcopy(records[0])
        elif attack == "context":
            context["session_id"] = "swapped"
        elif attack == "late":
            records[0]["observed_monotonic_ns"] = records[0]["deadline_ns"] + 1
        elif attack == "predecessor":
            records[1]["previous_receipt_sha256"] = None
        else:
            directory = observer.root / records[0]["episode_id"]
            if attack == "partial":
                (directory / "raw-1.json").write_bytes(b'{"partial":')
            elif attack == "forged_commit":
                commit = json.loads(
                    (directory / "commit.json").read_text(encoding="utf-8")
                )
                commit["prepared_sha256"] = "0" * 64
                (directory / "commit.json").write_text(
                    json.dumps(commit), encoding="utf-8"
                )
            else:
                prepared = json.loads(
                    (directory / "prepared.json").read_text(encoding="utf-8")
                )
                if attack == "phase":
                    prepared["phase_started_utc"] = "2099-01-01T00:00:00+00:00"
                if attack == "retry":
                    prepared["raw_refs"].reverse()
                (directory / "prepared.json").write_text(
                    json.dumps(prepared), encoding="utf-8"
                )
        with pytest.raises(ValueError):
            read_publications(
                observer.root, records, context, trusted_receipts=observer.receipts
            )
    finally:
        observer.close()


def test_only_isolated_mismatch_gets_bounded_fresh_retries(episode_factory):
    observer, context = episode_factory(mismatch=1)
    try:
        observer.acquire("phase")
        receipt = observer.receipts[0]
        prepared = json.loads(
            (observer.root / receipt["episode_id"] / "prepared.json").read_text(
                encoding="utf-8"
            )
        )
        assert len(prepared["raw_refs"]) == 2
        assert (
            len(
                read_publications(
                    observer.root,
                    observer.receipts,
                    context,
                    trusted_receipts=observer.receipts,
                )
            )
            == 1
        )
    finally:
        observer.close()
    observer, _ = episode_factory(mismatch=2)
    try:
        observer.acquire("phase")
        receipt = observer.receipts[0]
        prepared = json.loads(
            (observer.root / receipt["episode_id"] / "prepared.json").read_text(
                encoding="utf-8"
            )
        )
        assert len(prepared["raw_refs"]) == 3
    finally:
        observer.close()
    observer, _ = episode_factory(mismatch=1, invalid=True)
    try:
        with pytest.raises(ValueError):
            observer.acquire("phase")
        assert observer.previous_receipt is None
        assert observer.receipts == []
        assert list(observer.root.rglob("raw-1.json"))
        assert not list(observer.root.rglob("raw-2.json"))
    finally:
        observer.close()


def test_observation_reader_requires_explicit_v3_and_supervised_evidence(
    episode_factory,
):
    from benchmark_observation import (
        accepted_samples,
        acquire_sample,
        read_acquisitions,
    )

    observer, context = episode_factory()
    try:
        value = acquire_sample(observer, "phase")
        assert value["schema"] == "validated_v3_summary"
        records = read_acquisitions(
            observer.root,
            context,
            method="wddm_auto_v3",
            supervisor_receipts=observer.receipts,
            trusted_receipts=observer.receipts,
        )
        assert records == [observer.last_record]
        samples = accepted_samples(
            records,
            context,
            publication_root=observer.root,
            trusted_receipts=observer.receipts,
        )
        assert samples[0]["windows"]["dedicated_mb"] == 1200
    finally:
        observer.close()


def test_offline_validates_progress_and_recomputed_order_after_resealing(
    episode_factory,
):
    from benchmark_plan import digest
    from benchmark_process import encode

    observer, context = episode_factory(mismatch=1)
    try:
        observer.acquire("phase")
        receipt = copy.deepcopy(observer.receipts[0])
        directory = observer.root / receipt["episode_id"]
        prepared = json.loads((directory / "prepared.json").read_text(encoding="utf-8"))
        assert prepared["progress_refs"]
        raw = prepared["raw_refs"][1]
        original = json.loads((directory / raw["path"]).read_text(encoding="utf-8"))
        # Reseal altered bytes and a fixture custody receipt to reach the
        # semantic validator, rather than only testing hash mismatch.
        original["operations"]["browser"] = json.loads(
            (directory / "raw-1.json").read_text(encoding="utf-8")
        )["operations"]["browser"]
        (directory / raw["path"]).write_bytes(encode(original))
        raw["sha256"] = digest(original)
        prepared["sample_sha256"] = digest(original)
        (directory / "prepared.json").write_bytes(encode(prepared))
        commit = json.loads((directory / "commit.json").read_text(encoding="utf-8"))
        commit["prepared_sha256"] = digest(prepared)
        (directory / "commit.json").write_bytes(encode(commit))
        receipt["proof"]["prepared_sha256"] = digest(prepared)
        receipt["proof"]["commit_sha256"] = digest(commit)
        receipt["proof"]["sample_sha256"] = digest(original)
        with pytest.raises(ValueError):
            read_publications(
                observer.root, [receipt], context, trusted_receipts=[receipt]
            )
    finally:
        observer.close()


def test_rejection_breaks_shared_adjacency_and_is_required_offline(episode_factory):
    observer, _ = episode_factory(mismatch=1, invalid=True)
    try:
        with pytest.raises(ValueError):
            observer.acquire("phase")
        assert observer.attempts[0]["status"] == "rejected"
        # Fixture invalidity is a sensor-local switch, not RPC executable input.
        # Use an in-process trusted adapter below to change the fixture state.
        assert observer.attempts[0]["episode_id"]
        assert observer.previous_receipt is None
    finally:
        observer.close()


@pytest.fixture
def inprocess(episode_factory, monkeypatch):
    """Instrument child production code in-process for official coverage.

    Actual process isolation/deadlines are proven by separate native tests above.
    This trusted adapter performs real disk writes/reads and real sensor clocks.
    """
    import importlib.util

    import benchmark_episode

    native_verify = benchmark_episode.verify_ownership

    def synthetic_coverage_ownership(value):
        # This adapter is explicitly NOT a native publication receipt. All real
        # ownership/deadline cases above run through the unpatched native path.
        if value != {"synthetic_inprocess": True}:
            native_verify(value)

    monkeypatch.setattr(
        benchmark_episode, "verify_ownership", synthetic_coverage_ownership
    )

    class Adapter:
        def __init__(self, config, handler, **kwargs):
            path, name = handler.rsplit(":", 1)
            spec = importlib.util.spec_from_file_location(
                "trusted_coverage_fixture", path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.handler = getattr(module, name)(config)
            self.ownership = {"synthetic_inprocess": True}
            self.closed = False

        def call(self, payload, *, deadline_ns):
            events = []
            value = self.handler(
                payload,
                lambda v: events.append(
                    {
                        "value": copy.deepcopy(v),
                        "utc": benchmark_episode.utc_now(),
                        "monotonic_ns": time.perf_counter_ns(),
                    }
                ),
            )
            return {"value": value, "progress": events, "ownership": self.ownership}

        def close(self, **kwargs):
            if not self.closed:
                self.handler.close()
                self.closed = True

    monkeypatch.setattr(benchmark_episode, "OwnedProcess", Adapter)
    return episode_factory


def test_rejected_inventory_allows_fresh_segment_without_partial_reuse(inprocess):
    observer, context = inprocess()
    try:
        observer.acquire("phase")
        observer.worker.handler.sensor.config["invalid"] = True
        with pytest.raises(ValueError):
            observer.acquire("phase")
        observer.worker.handler.sensor.config["invalid"] = False
        observer.acquire("phase")
        assert observer.receipts[1]["previous_receipt_sha256"] is None
        assert len(observer.attempts) == 3
        accepted = read_publications(
            observer.root,
            observer.receipts,
            context,
            trusted_receipts=observer.receipts,
            attempts=observer.attempts,
            trusted_attempts=observer.attempts,
        )
        assert len(accepted) == 2
        with pytest.raises(ValueError):
            read_publications(
                observer.root,
                observer.receipts,
                context,
                trusted_receipts=observer.receipts,
            )
    finally:
        observer.close()


@pytest.mark.parametrize(
    "attack",
    [
        "raw_omit",
        "progress_omit",
        "progress_swap",
        "partial_reuse",
        "policy",
        "phase",
        "context",
        "ordinal",
        "deadline",
        "sample",
        "commit_started_late",
        "completion_order",
        "originals_extra",
        "request",
        "receipt_clock",
        "no_ownership",
        "late_ack",
    ],
)
def test_semantic_recomputation_with_fixture_resealed_bytes(inprocess, attack):
    from benchmark_plan import digest
    from benchmark_process import encode

    observer, context = inprocess(mismatch=1)
    try:
        observer.acquire("phase")
        receipt = copy.deepcopy(observer.receipts[0])
        directory = observer.root / receipt["episode_id"]
        prepared = json.loads((directory / "prepared.json").read_text(encoding="utf-8"))
        commit = json.loads((directory / "commit.json").read_text(encoding="utf-8"))
        request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
        if attack == "raw_omit":
            prepared["raw_refs"].pop(0)
        elif attack == "progress_omit":
            prepared["progress_refs"].pop()
        elif attack == "progress_swap":
            prepared["progress_refs"].reverse()
        elif attack == "partial_reuse":
            raw = json.loads((directory / "raw-2.json").read_text(encoding="utf-8"))
            before = json.loads((directory / "raw-1.json").read_text(encoding="utf-8"))
            raw["operations"]["wsl"] = before["operations"]["wsl"]
            (directory / "raw-2.json").write_bytes(encode(raw))
            prepared["raw_refs"][1]["sha256"] = digest(raw)
            prepared["sample_sha256"] = digest(raw)
        elif attack == "policy":
            prepared["policy_sha256"] = "0" * 64
        elif attack == "phase":
            prepared["phase_started_utc"] = "2099-01-01T00:00:00+00:00"
            request["request"]["phase_started_utc"] = prepared["phase_started_utc"]
        elif attack == "context":
            prepared["context"]["session_id"] = "other"
        elif attack == "ordinal":
            prepared["ordinal"] = 9
        elif attack == "deadline":
            prepared["deadline_ns"] += 1
        elif attack == "sample":
            prepared["sample_sha256"] = "0" * 64
        elif attack == "commit_started_late":
            commit["write_started"]["monotonic_ns"] = receipt["deadline_ns"] + 1
        elif attack == "completion_order":
            receipt["proof"]["commit_finished"]["monotonic_ns"] = (
                receipt["proof"]["verification_finished"]["monotonic_ns"] + 1
            )
        elif attack == "originals_extra":
            (directory / "raw-3.json").write_bytes(
                (directory / "raw-2.json").read_bytes()
            )
        elif attack == "request":
            request["context"]["image_id"] = "swapped"
        elif attack == "receipt_clock":
            receipt["observed_utc"] = "2000-01-01T00:00:00+00:00"
        elif attack == "no_ownership":
            receipt["ownership"] = {}
        elif attack == "late_ack":
            receipt["observed_monotonic_ns"] = receipt["deadline_ns"] + 1
        (directory / "request.json").write_bytes(encode(request))
        (directory / "prepared.json").write_bytes(encode(prepared))
        commit["prepared_sha256"] = digest(prepared)
        (directory / "commit.json").write_bytes(encode(commit))
        receipt["proof"]["prepared_sha256"] = digest(prepared)
        receipt["proof"]["commit_sha256"] = digest(commit)
        receipt["proof"]["sample_sha256"] = prepared["sample_sha256"]
        with pytest.raises(ValueError):
            read_publications(
                observer.root, [receipt], context, trusted_receipts=[receipt]
            )
    finally:
        observer.close()


def test_child_pending_state_is_only_confirmed_by_next_timely_receipt(inprocess):
    observer, context = inprocess()
    try:
        observer.acquire("phase")
        handler = observer.worker.handler
        assert handler.previous is None
        assert handler.pending is not None
        observer.acquire("phase")
        assert handler.previous["receipt"] == observer.receipts[0]
        assert handler.pending["proof"] == observer.receipts[1]["proof"]
        assert (
            observer.root / observer.receipts[0]["episode_id"] / "supervisor-audit.json"
        ).is_file()
        assert (
            len(
                read_publications(
                    observer.root,
                    observer.receipts,
                    context,
                    trusted_receipts=observer.receipts,
                    attempts=observer.attempts,
                    trusted_attempts=observer.attempts,
                )
            )
            == 2
        )
    finally:
        observer.close()


def test_supervisor_audit_metadata_does_not_add_a_durable_sync_to_next_episode(
    inprocess, monkeypatch
):
    """The already durable commit is the authority; its follow-up audit is metadata."""
    import benchmark_episode

    calls = []
    original = benchmark_episode.EpisodeProvider.write

    def capture(self, name, value, **kwargs):
        if name == "supervisor-audit.json":
            calls.append(dict(kwargs))
        return original(self, name, value, **kwargs)

    monkeypatch.setattr(benchmark_episode.EpisodeProvider, "write", capture)
    observer, _ = inprocess()
    try:
        observer.acquire("phase")
        observer.acquire("phase")
        assert calls == [{"durable": False}]
    finally:
        observer.close()


def test_runtime_raw_only_and_closed_operations_cannot_accept(inprocess):
    observer, _ = inprocess()
    try:
        with pytest.raises(ValueError, match="raw_only"):
            observer.acquire("phase", enforce=False)
        assert not observer.receipts
        handler = observer.worker.handler
        with pytest.raises(ValueError, match="closed_operation"):
            handler({"operation": "sample", "arguments": {}}, lambda _: None)
        with pytest.raises(ValueError, match="arguments"):
            handler({"operation": "episode_v3", "arguments": {}}, lambda _: None)
    finally:
        observer.close()


def test_parent_malformed_proof_is_interrupted_and_cleaned_without_advancing(inprocess):
    observer, _ = inprocess()
    call = observer.worker.call

    def corrupt(payload, *, deadline_ns):
        result = call(payload, deadline_ns=deadline_ns)
        result["value"]["proof"]["commit_finished"]["monotonic_ns"] = deadline_ns + 1
        return result

    observer.worker.call = corrupt
    with pytest.raises(WorkerFailure):
        observer.acquire("phase")
    assert observer.worker.closed
    assert observer.previous_receipt is None
    assert not observer.receipts
    assert observer.last_interrupted["progress"]


def test_retry_uses_original_total_deadline_with_real_cpu_delay(episode_factory):
    observer, context = episode_factory(mismatch=1, delay_each_s=1.02)
    started = time.perf_counter_ns()
    with pytest.raises(WorkerFailure):
        observer.acquire("phase")
    assert (time.perf_counter_ns() - started) / 1e9 < 2.05
    assert observer.receipts == [] and observer.previous_receipt is None
    assert list(observer.root.rglob("raw-1.json"))
    assert not list(observer.root.rglob("raw-2.json"))
    values = [frame["value"] for frame in observer.last_interrupted["progress"]]
    assert any(v.get("actual_count") == 2 for v in values)
    assert (
        read_publications(
            observer.root,
            [],
            context,
            trusted_receipts=[],
            attempts=observer.attempts,
            trusted_attempts=observer.attempts,
        )
        == []
    )


def test_native_interrupted_commit_bytes_never_count_as_ack(episode_factory):
    observer, context = episode_factory(block_stage="commit_fsync")
    with pytest.raises(WorkerFailure):
        observer.acquire("phase")
    assert list(observer.root.rglob("commit.json"))
    assert not observer.receipts
    assert (
        read_publications(
            observer.root,
            [],
            context,
            trusted_receipts=[],
            attempts=observer.attempts,
            trusted_attempts=observer.attempts,
        )
        == []
    )


def test_closed_trusted_factory_requests_and_context_custody(inprocess):
    from benchmark_episode import EpisodeProvider, confined, read_json

    observer, _ = inprocess()
    try:
        handler = observer.worker.handler
        for args, match in [
            ({}, "arguments"),
            (
                {
                    "episode_id": "../../x",
                    "stream": "p",
                    "start": {"utc": "2026-10-07T00:00:00+00:00", "monotonic_ns": 1},
                    "deadline_ns": 2000000001,
                    "phase_started_utc": None,
                    "idle": False,
                    "confirm": None,
                    "enforce": True,
                },
                "episode_id",
            ),
        ]:
            with pytest.raises(ValueError, match=match):
                handler({"operation": "episode_v3", "arguments": args}, lambda _: None)
        with pytest.raises(ValueError, match="config"):
            EpisodeProvider({"execute": "bad"})
        with pytest.raises(ValueError, match="outside"):
            confined(Path.cwd().parent / "foreign")
        path = observer.root / "partial.json"
        path.write_bytes(b'{"x":')
        with pytest.raises(ValueError, match="partial"):
            read_json(path)
        path.write_bytes(b'{"x":1,"x":2}\n')
        with pytest.raises(ValueError, match="partial"):
            read_json(path)
    finally:
        observer.close()


def test_v3_raw_cannot_bypass_publication_readers_or_old_calibration(inprocess):
    from benchmark_observation import accepted_samples, validate_calibration

    observer, context = inprocess()
    try:
        observer.acquire("phase")
        raw = read_publications(
            observer.root,
            observer.receipts,
            context,
            trusted_receipts=observer.receipts,
        )[0]
        with pytest.raises(ValueError, match="supervis"):
            accepted_samples([raw], context)
        with pytest.raises(ValueError, match="supervis"):
            accepted_samples([observer.last_record["sample"]], context)
        with pytest.raises(ValueError, match="supervis"):
            validate_calibration({}, {}, context, method="wddm_auto_v3")
    finally:
        observer.close()


def test_v3_reader_retains_freshness_and_routes_rejection_inventory(inprocess):
    from datetime import datetime, timedelta, timezone

    from benchmark_observation import accepted_samples, read_acquisitions

    observer, context = inprocess()
    try:
        observer.acquire("phase")
        future = datetime.now(timezone.utc) + timedelta(seconds=1000)
        with pytest.raises(ValueError, match="expired"):
            read_acquisitions(
                observer.root,
                context,
                method="wddm_auto_v3",
                supervisor_receipts=observer.receipts,
                trusted_receipts=observer.receipts,
                now=future,
            )
        observer.worker.handler.sensor.config["invalid"] = True
        with pytest.raises(ValueError):
            observer.acquire("phase")
        observer.worker.handler.sensor.config["invalid"] = False
        observer.acquire("phase")
        records = read_acquisitions(
            observer.root,
            context,
            method="wddm_auto_v3",
            supervisor_receipts=observer.receipts,
            trusted_receipts=observer.receipts,
            attempts=observer.attempts,
            trusted_attempts=observer.attempts,
            historical=True,
            now=future,
        )
        assert (
            len(
                accepted_samples(
                    records,
                    context,
                    publication_root=observer.root,
                    trusted_receipts=observer.receipts,
                    attempts=observer.attempts,
                    trusted_attempts=observer.attempts,
                    historical=True,
                    now=future,
                )
            )
            == 2
        )
    finally:
        observer.close()


def test_supervisor_ownership_has_strict_native_identity(episode_factory):
    from benchmark_episode import validate_receipt

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        forged = copy.deepcopy(observer.receipts[0])
        forged["ownership"] = {"pid": "foreign", "creation_time": 0, "job_member": True}
        with pytest.raises(ValueError, match="identity"):
            validate_receipt(forged, context)
    finally:
        observer.close()
