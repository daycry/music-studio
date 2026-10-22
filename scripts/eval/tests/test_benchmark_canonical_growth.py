"""Pruebas canónicas CPU: procesos y relojes reales, sin sensores GPU.

El pacing acelerado pertenece sólo a esta definición de prueba. No acredita
cadencia de producción, ni horas GPU. Ningún validador se reemplaza.
"""

import copy
import json
import time
from pathlib import Path

import pytest
from benchmark_clock import utc_now
from benchmark_episode import read_publications
from benchmark_plan import digest, file_hash, source_hashes
from benchmark_runtime import BenchmarkOperationProvider

PRIVATE = Path.cwd() / ".cache/dev-cycle/t09/canonical-growth-unit"


@pytest.fixture(scope="module")
def canonical_history():
    import benchmark_observation as observation
    import test_benchmark_episode_v3 as fixture_module

    previous_phase = fixture_module.PHASE
    fixture_module.PHASE = PRIVATE / "native-history"
    try:
        make = fixture_module.episode_factory.__wrapped__()
    finally:
        fixture_module.PHASE = previous_phase
    initial, context = make()
    initial.close()
    cleanups = [initial.worker.close_evidence]
    context["source_hashes"] = source_hashes(Path.cwd())
    context["lock_sha256"] = file_hash(Path.cwd() / "models/models.lock.json")
    folder = initial.root.parents[1]
    (folder / "context.json").write_text(json.dumps(context), encoding="utf-8")
    sensor = folder / "sensor_fixture.py"
    sensor.write_text(
        sensor.read_text(encoding="utf-8").replace(
            "raw=values.sample(0)",
            'raw=values.sample(0, 8000 if Path(__file__).with_name("phase.txt").read_text()=="loaded" else 1200)',
        ),
        encoding="utf-8",
    )
    sensor.with_name("phase.txt").write_text("baseline", encoding="utf-8")
    observer, context = make()
    lifecycle, proofs, phases, records = {}, {}, {}, []
    viewport_at = utc_now()
    started = time.perf_counter_ns()
    try:
        for phase in ("baseline", "loaded", "unloaded"):
            sensor.with_name("phase.txt").write_text(phase, encoding="utf-8")
            if phase != "baseline":
                observed = utc_now()
                proofs[phase] = {
                    "started_utc": observed,
                    "finished_utc": observed,
                    "response": {"loaded": {"model_id": "CPU", "mode": "bf16"}}
                    if phase == "loaded"
                    else {"loaded": None, "state": "idle"},
                    "acquisition_context": observation.acquisition_context(
                        context, "wddm_auto_v3"
                    ),
                    "test_scope": "CPU synthetic lifecycle; no engine/GPU",
                }
                lifecycle[phase] = {
                    "event": "health_loaded"
                    if phase == "loaded"
                    else "health_unloaded",
                    "job_id": "CPU",
                    "observed_at": observed,
                    **({"loaded": None} if phase == "unloaded" else {}),
                }
                observer.phase_started_utc = observed
            refs = []
            for _ in range(10):
                sample = observer.acquire(phase, idle=phase != "loaded")
                records.append(copy.deepcopy(observer.last_record))
                assert sample == records[-1]["sample"]
                receipt = observer.receipts[-1]
                refs.append(
                    {
                        "episode_id": receipt["episode_id"],
                        "receipt_sha256": digest(receipt),
                    }
                )
            phases[phase] = refs
        for phase, proof in proofs.items():
            path = folder / (phase + "-proof.json")
            path.write_text(json.dumps(proof), encoding="utf-8")
            lifecycle[phase]["proof"] = {
                "path": path.relative_to(Path.cwd()).as_posix(),
                "sha256": file_hash(path),
                "bytes": path.stat().st_size,
            }
            lifecycle[phase]["acquisition_context"] = observation.acquisition_context(
                context, "wddm_auto_v3"
            )
        # 130 auténticos intentos, sin duplicar recibos ni inventar timestamps.
        for _ in range(100):
            observer.acquire("unloaded", idle=True)
            records.append(copy.deepcopy(observer.last_record))
        samples = read_publications(
            observer.root,
            observer.receipts,
            context,
            trusted_receipts=observer.receipts,
            attempts=observer.attempts,
            trusted_attempts=observer.attempts,
            historical=True,
        )
        assert len(samples) == len(records) == 130
        case = {
            "root": observer.root,
            "receipts": copy.deepcopy(observer.receipts),
            "attempts": copy.deepcopy(observer.attempts),
            "phases": phases,
        }
        yield case, lifecycle, context, proofs, viewport_at, records
    finally:
        observer.close()
        cleanups.append(observer.worker.close_evidence)
        (PRIVATE / "native-cleanup.json").write_text(
            json.dumps(
                {
                    "cleanup": cleanups,
                    "elapsed_s": (time.perf_counter_ns() - started) / 1e9,
                    "accepted": len(observer.receipts),
                    "attempts": len(observer.attempts),
                    "ownership": observer.worker.ownership,
                    "reader_alive": observer.worker.reader.is_alive(),
                    "historical_cleanup": "UNKNOWN; not recertified",
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def runtime_for(case, context, records):
    from benchmark_audit import AuditPrefix

    runtime = object.__new__(BenchmarkOperationProvider)
    runtime.root = Path.cwd()
    binding = {"root": str(case["root"]), "context": context, "stream": "CPU"}
    runtime.audit_prefix = AuditPrefix(binding, runtime.validate_delta)
    runtime.audit_value = {
        "root": str(case["root"]),
        "context": context,
        "receipts": case["receipts"],
        "attempts": case["attempts"],
        "records": records,
    }
    return runtime


def test_repeated_refresh_large_canonical_history_stays_bounded(canonical_history):
    """Criterio funcional: ambas renovaciones y prerequisites <=256 KiB."""
    import test_benchmark_calibration_v3 as calibration_module
    from benchmark_episode import read_json
    from benchmark_process import encode

    case, lifecycle, context, proofs, viewport_at, records = canonical_history
    observation, plan, case = calibration_module.auto_case.__wrapped__(
        (case, lifecycle, context, proofs, viewport_at)
    )
    runtime = runtime_for(case, context, records)
    runtime.plan = plan
    publication_path = Path(observation["evidence"]["publications"]["path"])
    assert publication_path.stat().st_size > 262144
    prerequisite_path = case["root"].parent / "growth-prerequisites-0.json"
    prerequisite_path.write_text(
        json.dumps({"observation": observation}), encoding="utf-8"
    )
    sizes = []
    for ordinal in range(1, 3):
        result = runtime(
            {
                "operation": "refresh_accreditation",
                "arguments": {
                    "observation_path": str(prerequisite_path),
                    "path": str(
                        case["root"].parent / f"growth-publications-{ordinal}.json"
                    ),
                },
            },
            lambda event: None,
        )
        frame = encode(result)
        prerequisite_path = case["root"].parent / f"growth-prerequisites-{ordinal}.json"
        prerequisite_path.write_text(json.dumps(result), encoding="utf-8")
        assert read_json(prerequisite_path) == result
        sizes.append(
            {
                "frame_bytes": len(frame),
                "prerequisites_bytes": prerequisite_path.stat().st_size,
            }
        )
    (PRIVATE / "refresh-sizes.json").write_text(
        json.dumps(
            {
                "history_bytes": publication_path.stat().st_size,
                "sizes": sizes,
                "canonical_episodes": len(case["receipts"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("prefix_size", [10, 20])
def test_new_delta_does_not_reopen_canonical_prefix(
    canonical_history, monkeypatch, prefix_size
):
    case, _, context, _, _, records = canonical_history
    runtime = runtime_for(case, context, records)
    first = {
        **runtime.audit_value,
        **{
            k: runtime.audit_value[k][:prefix_size]
            for k in ("receipts", "attempts", "records")
        },
    }
    runtime.validate_delta(
        first, {k: first[k] for k in ("receipts", "attempts", "records")}
    )
    observed = []
    original_open = Path.open

    class Reading:
        def __init__(self, stream, path):
            self.stream, self.path = stream, path

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def read(self, *args):
            begin = time.perf_counter_ns()
            result = self.stream.read(*args)
            observed.append(
                {
                    "path": str(self.path),
                    "start_ns": begin,
                    "end_ns": time.perf_counter_ns(),
                    "returned_bytes": len(result),
                }
            )
            return result

    def capture(path, *args, **kwargs):
        stream = original_open(path, *args, **kwargs)
        if path.is_relative_to(case["root"]):
            return Reading(stream, path)
        return stream

    monkeypatch.setattr(Path, "open", capture)
    next_snapshot = {
        **runtime.audit_value,
        **{
            k: runtime.audit_value[k][: prefix_size + 1]
            for k in ("receipts", "attempts", "records")
        },
    }
    begin = time.perf_counter_ns()
    runtime.validate_delta(
        next_snapshot,
        {
            k: runtime.audit_value[k][prefix_size : prefix_size + 1]
            for k in ("receipts", "attempts", "records")
        },
    )
    online_elapsed = (time.perf_counter_ns() - begin) / 1e9
    online_reads = list(observed)
    old_ids = {r["episode_id"] for r in first["receipts"]}
    old_reads = [
        entry for entry in observed if Path(entry["path"]).parent.name in old_ids
    ]
    observed.clear()
    begin = time.perf_counter_ns()
    independent = read_publications(
        case["root"],
        next_snapshot["receipts"],
        context,
        trusted_receipts=case["receipts"][: prefix_size + 1],
        attempts=case["attempts"][: prefix_size + 1],
        trusted_attempts=case["attempts"][: prefix_size + 1],
        historical=True,
    )
    final_elapsed = (time.perf_counter_ns() - begin) / 1e9
    assert len(independent) == prefix_size + 1
    assert {Path(entry["path"]).parent.name for entry in observed} == {
        r["episode_id"] for r in next_snapshot["receipts"]
    }
    (PRIVATE / f"prefix-io-profile-{prefix_size}.json").write_text(
        json.dumps(
            {
                "prefix_episodes": prefix_size,
                "new_episodes": 1,
                "online_reads": online_reads,
                "old_reads": old_reads,
                "independent_original_reads": observed,
                "online_elapsed_s": online_elapsed,
                "independent_elapsed_s": final_elapsed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    assert old_reads == [], "nuevo delta reabre los originales del prefijo"


def test_delta_foreign_root_rejected_before_canonical_io(canonical_history):
    case, _, context, _, _, records = canonical_history
    runtime = runtime_for(case, context, records)
    runtime.audit_prefix.binding["root"] = str(
        case["root"].parent / "different-owned-root"
    )
    snapshot = {
        **runtime.audit_value,
        **{k: runtime.audit_value[k][:1] for k in ("receipts", "attempts", "records")},
    }
    with pytest.raises(ValueError, match="binding"):
        runtime.validate_delta(
            snapshot, {k: snapshot[k] for k in ("receipts", "attempts", "records")}
        )


@pytest.mark.parametrize("damage", ["missing_binding", "owned_root", "owned_context"])
def test_delta_internal_binding_damage_rejected_without_io(
    canonical_history, monkeypatch, damage
):
    """La validación interna exige el binding y el estado de su propio store."""
    case, _, context, _, _, records = canonical_history
    runtime = runtime_for(case, context, records)
    snapshot = {
        **runtime.audit_value,
        **{k: runtime.audit_value[k][:1] for k in ("receipts", "attempts", "records")},
    }
    if damage == "missing_binding":
        runtime.audit_prefix = None
    elif damage == "owned_root":
        runtime.audit_prefix.value["root"] = str(case["root"].parent / "foreign")
    else:
        runtime.audit_prefix.value["context"] = {**context, "session_id": "foreign"}
    opened = []
    original_open = Path.open

    def capture(path, *args, **kwargs):
        stream = original_open(path, *args, **kwargs)
        if path.is_relative_to(case["root"]):
            opened.append(str(path))
        return stream

    monkeypatch.setattr(Path, "open", capture)
    before = copy.deepcopy(runtime.audit_value)
    with pytest.raises(ValueError, match="binding"):
        runtime.validate_delta(
            snapshot, {k: snapshot[k] for k in ("receipts", "attempts", "records")}
        )
    assert opened == []
    assert runtime.audit_value == before
