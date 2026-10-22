"""Transporte incremental CPU: publicaciones canónicas y procesos propios."""

import copy
import importlib.util
import json
import uuid
from pathlib import Path

import pytest
from benchmark_audit import AuditPrefix, segment_header
from benchmark_coordinator import ContinuousCoordinator, RuntimeChannel
from benchmark_evidence import exclusive_json
from benchmark_plan import digest
from benchmark_process import OwnedProcess


def fixture_module():
    path = (
        Path.cwd()
        / ".cache/dev-cycle/t09/transition-review2-adjudicated-fix/fixtures2/test_benchmark_coordinator_v3.py"
    )
    spec = importlib.util.spec_from_file_location("delta_native_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_unchanged_prefix_uses_bounded_delta_header():
    module = fixture_module()
    observer, context = module.episode_factory.__wrapped__()()
    native = module.fake_runtime.__wrapped__()
    plan = {
        **native[1],
        **{
            k: context[k]
            for k in ("session_id", "plan_sha256", "image_id", "lock_sha256")
        },
    }
    Path(native[2]["plan_path"]).write_text(json.dumps(plan), encoding="utf-8")
    owner_path = Path(native[2]["owner_path"])
    owner = json.loads(owner_path.read_text())
    owner.update({k: plan[k] for k in ("session_id", "plan_sha256")})
    owner_path.write_text(json.dumps(owner), encoding="utf-8")
    binding = {
        "root": str(observer.root),
        "context": context,
        "stream": "CPU-DELTA-OWN",
    }
    binding_path = native[0] / "audit-binding.json"
    exclusive_json(binding_path, binding)
    config = {
        **native[2],
        "audit_binding_path": str(binding_path),
        "audit_binding_sha256": digest(binding),
    }
    with ContinuousCoordinator(observer, interval_s=2.5) as coordinator:
        worker = OwnedProcess(config, native[3])
        calls = []
        original = worker.call

        def counted(payload, **kwargs):
            calls.append(payload)
            return original(payload, **kwargs)

        worker.call = counted
        channel = RuntimeChannel(coordinator, worker, audit_binding=binding)
        try:
            first = channel.audit_publications()
            calls.clear()
            second = channel.audit_publications()
            assert second["transport"] == "wddm_audit_delta_v1"
            assert second["validated"] == first["validated"]
            assert len(calls) <= 2
            assert sum(len(str(call)) for call in calls) < 3500
        finally:
            channel.close()
    assert worker.close_evidence["job_empty"] is True
    assert worker.close_evidence["reader_joined"] is True


def send(prefix, segment):
    header, text = segment_header(prefix.status(), segment)
    prefix.begin(header)
    for index, offset in enumerate(range(0, len(text), 1200)):
        prefix.fragment({"index": index, "text": text[offset : offset + 1200]})
    return prefix.commit(), header, text


def test_delta_validation_cannot_observe_uncommitted_prefix():
    seen = []

    def validate(value, segment):
        seen.append(prefix.status()["positions"])
        assert len(value["receipts"]) == 1
        return digest(segment)

    prefix = AuditPrefix({"root": "owned", "context": {}, "stream": "atomic"}, validate)
    send(prefix, {"receipts": [{}], "attempts": [{}], "records": [{}]})
    assert seen == [{"receipts": 0, "attempts": 0, "records": 0}]


def test_delta_anchor_authenticates_entire_chained_prefix():
    prefix = AuditPrefix(
        {"root": "owned", "context": {}, "stream": "anchor"},
        lambda value, segment: digest(segment),
    )
    segment = {"receipts": [{}], "attempts": [{}], "records": [{}]}
    first, _, _ = send(prefix, segment)
    second, _, _ = send(prefix, segment)
    assert first["supervisor_anchor_sha256"] == first["prefix"]
    assert second["supervisor_anchor_sha256"] == second["prefix"]
    assert first["supervisor_anchor_sha256"] != second["supervisor_anchor_sha256"]


def test_delta_positions_require_integers_and_pending_segment_cannot_be_replaced():
    from benchmark_audit import prefix_hash

    prefix = AuditPrefix(
        {"root": "owned", "context": {}, "stream": "typed"},
        lambda value, segment: digest(segment),
    )
    segment = {"receipts": [{}], "attempts": [{}], "records": [{}]}
    header, _ = segment_header(prefix.status(), segment)
    forged = copy.deepcopy(header)
    forged["first"]["receipts"] = 0.0
    forged["prefix"] = prefix_hash(
        forged["previous"],
        forged["stream"],
        forged["sequence"],
        forged["first"],
        forged["last"],
        forged["sha256"],
    )
    with pytest.raises(ValueError):
        prefix.begin(forged)
    prefix.begin(header)
    with pytest.raises(ValueError, match="pending"):
        prefix.begin(header)


def test_delta_incomplete_pending_segment_cannot_be_silently_replaced():
    prefix = AuditPrefix(
        {"root": "owned", "context": {}, "stream": "pending"},
        lambda value, segment: digest(segment),
    )
    header, _ = segment_header(
        prefix.status(), {"receipts": [{}], "attempts": [{}], "records": [{}]}
    )
    prefix.begin(header)
    with pytest.raises(ValueError, match="pending"):
        prefix.begin(header)


def test_bound_runtime_complete_protocol_cannot_select_foreign_trusted_root(tmp_path):
    from benchmark_runtime import BenchmarkOperationProvider

    provider = BenchmarkOperationProvider.__new__(BenchmarkOperationProvider)
    provider.root = Path.cwd()
    provider.audit_prefix = AuditPrefix(
        {"root": str(tmp_path / "owned"), "context": {}, "stream": "bound"},
        lambda *args: None,
    )
    foreign = {
        "root": str(tmp_path / "foreign"),
        "context": {},
        "receipts": [],
        "attempts": [],
        "records": [],
    }
    text = json.dumps(foreign, separators=(",", ":"))
    provider(
        {
            "operation": "audit_begin",
            "arguments": {"characters": len(text), "sha256": digest(foreign)},
        },
        lambda value: None,
    )
    for index, offset in enumerate(range(0, len(text), 1200)):
        provider(
            {
                "operation": "audit_fragment",
                "arguments": {"index": index, "text": text[offset : offset + 1200]},
            },
            lambda value: None,
        )
    with pytest.raises(ValueError, match="binding"):
        provider({"operation": "audit_validate", "arguments": {}}, lambda value: None)
    assert provider.audit_prefix.status()["positions"] == {
        "receipts": 0,
        "attempts": 0,
        "records": 0,
    }


def test_extended_prefix_preserves_sequence_without_history_copy():
    from benchmark_audit import ExtendedPrefix

    original = [1, 2]
    view = ExtendedPrefix(original, [3, 4])
    assert view.prefix is original
    assert list(view) == [1, 2, 3, 4]
    assert view[-1] == 4 and view[0] == 1
    assert view[1:3] == [2, 3]
    assert view == [1, 2, 3, 4]
    assert view != [1] and view != object()
    with pytest.raises(IndexError):
        _ = view[4]
    with pytest.raises(IndexError):
        _ = view[-5]


def test_delta_bound_fragment_and_incomplete_fail_without_pending_publication():
    prefix = AuditPrefix(
        {"root": "own", "context": {}, "stream": "bounded"}, lambda *a: None
    )
    segment = {"receipts": [{}], "attempts": [{}], "records": [{}]}
    header, text = segment_header(prefix.status(), segment)
    before = prefix.status()
    for characters in (0, 64 * 1024**2 + 1):
        with pytest.raises(ValueError, match="bound"):
            prefix.begin({**header, "characters": characters})
    with pytest.raises(ValueError, match="not_started"):
        prefix.fragment({"index": 0, "text": text})
    prefix.begin(header)
    with pytest.raises(ValueError, match="overflow"):
        prefix.fragment({"index": 0, "text": text + "x"})
    with pytest.raises(ValueError, match="incomplete"):
        prefix.commit()
    assert prefix.status() == before


@pytest.mark.parametrize(
    "mutation",
    [
        "stream",
        "sequence",
        "previous",
        "first",
        "last",
        "prefix",
        "seal",
        "incomplete",
        "fragment",
        "replay",
        "authority",
    ],
)
def test_delta_rejects_invalid_segment_without_advancing_verified_prefix(mutation):
    def validate(value, segment):
        if any(r.get("authoritative") is not True for r in segment["receipts"]):
            raise ValueError("external_anchor_invalid")
        return digest(segment)

    prefix = AuditPrefix({"root": "owned", "context": {}, "stream": "unique"}, validate)
    segment = {
        "receipts": [{"authoritative": True}],
        "attempts": [{"status": "accepted"}],
        "records": [{}],
    }
    _, old_header, _old_text = send(prefix, segment)
    before = copy.deepcopy(prefix.status())
    old_value = copy.deepcopy(prefix.value)
    header, text = segment_header(before, segment)
    with pytest.raises((ValueError, KeyError)):
        if mutation == "replay":
            prefix.begin(old_header)
        elif mutation in {"stream", "sequence", "previous", "first", "last", "prefix"}:
            header[mutation] = (
                {"receipts": -1} if mutation in {"first", "last"} else "false"
            )
            prefix.begin(header)
        else:
            if mutation == "authority":
                segment["receipts"][0]["authoritative"] = False
                header, text = segment_header(before, segment)
            prefix.begin(header)
            if mutation == "fragment":
                prefix.fragment({"index": 1, "text": text[:1200]})
            elif mutation == "incomplete":
                prefix.fragment({"index": 0, "text": text[:1]})
                prefix.commit()
            else:
                if mutation == "seal":
                    text = text.replace("true", "null")
                for index, offset in enumerate(range(0, len(text), 1200)):
                    prefix.fragment(
                        {"index": index, "text": text[offset : offset + 1200]}
                    )
                prefix.commit()
    assert prefix.status() == before
    assert prefix.value == old_value


def test_delta_native_volume_48000_logical_cpu_episodes():
    """Duración sintética declarada; ninguna sesión real de 13h ni sensor real."""
    import math
    import time

    phase = Path.cwd() / ".cache/dev-cycle/t09/transition-review2-adjudicated-fix"
    folder = phase / "volume" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    handler = folder / "volume_provider.py"
    handler.write_text(
        """import os,site,uuid,json
from pathlib import Path
from benchmark_audit import AuditPrefix
from benchmark_plan import digest
class Volume:
    def __init__(self,config):
        self.folder=Path(config["folder"])
        self.coverage=None
        if os.environ.get("T09_NATIVE_COVERAGE_CONFIG"):
            site.addsitedir(str(Path.cwd()/".venv/Lib/site-packages"))
            import coverage
            self.coverage=coverage.Coverage(config_file=os.environ["T09_NATIVE_COVERAGE_CONFIG"],data_file=os.environ["T09_NATIVE_COVERAGE_PREFIX"]+"."+str(os.getpid())+"."+uuid.uuid4().hex)
            self.coverage.start()
        self.prefix=AuditPrefix({"root":str(self.folder),"context":{"synthetic_cpu":True},"stream":config["stream"]},self.validate)
    def validate(self,value,segment):
        first=len(value["receipts"])-len(segment["receipts"])
        for i,(r,a,s) in enumerate(zip(segment["receipts"],segment["attempts"],segment["records"],strict=True),first+1):
            if r["ordinal"]!=i or r["episode_id"]!="CPU-%06d"%i or a!={"status":"accepted","receipt":r} or s["supervisor_receipt"]!=r or s["sample_sha256"]!=digest(s["sample"]):raise ValueError("synthetic_authoritative_schema_invalid")
        with (self.folder/"segments-original.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(segment,separators=(",",":"))+"\\n")
        return digest(segment)
    def __call__(self,payload,emit):
        action,args=payload["operation"],payload["arguments"]
        if action=="status":return self.prefix.status()
        if action=="begin":return self.prefix.begin(args)
        if action=="fragment":return self.prefix.fragment(args)
        if action=="commit":return self.prefix.commit()
        raise ValueError("unknown_cpu_action")
    def close(self):
        if self.coverage:self.coverage.stop();self.coverage.save()
""",
        encoding="utf-8",
    )
    worker = OwnedProcess(
        {"folder": str(folder), "stream": uuid.uuid4().hex}, f"{handler}:Volume"
    )
    calls = 0
    sizes = 0
    fragments = 0
    started = time.monotonic()

    def rpc(action, args):
        nonlocal calls
        calls += 1
        return worker.call(
            {"operation": action, "arguments": args},
            deadline_ns=time.perf_counter_ns() + 30_000_000_000,
        )["value"]

    try:
        status = rpc("status", {})
        for start in range(0, 48000, 32):
            segment = {name: [] for name in ("receipts", "attempts", "records")}
            for ordinal in range(start + 1, start + 33):
                receipt = {
                    "ordinal": ordinal,
                    "episode_id": f"CPU-{ordinal:06d}",
                    "synthetic_cpu": True,
                    "start": {
                        "utc": "2026-10-07T00:00:00Z",
                        "monotonic_ns": ordinal * 1_000_000_000,
                    },
                    "deadline_ns": ordinal * 1_000_000_000 + 2_000_000_000,
                    "proof": {
                        "commit_sha256": "a" * 64,
                        "prepared_sha256": "b" * 64,
                        "sample_sha256": "c" * 64,
                    },
                    "previous_receipt_sha256": "d" * 64,
                }
                sample = {
                    "synthetic_cpu": True,
                    "nvml": {"used_mb": 1200},
                    "windows": {"dedicated_mb": 1200, "shared_mb": 0},
                    "operations": {
                        name: {
                            "started_monotonic_ns": ordinal * 1_000_000_000,
                            "finished_monotonic_ns": ordinal * 1_000_000_000 + 1000,
                            "provider": "CPU-SYNTHETIC",
                        }
                        for name in ("nvml", "pdh", "dxgi", "wsl", "browser")
                    },
                }
                segment["receipts"].append(receipt)
                segment["attempts"].append({"status": "accepted", "receipt": receipt})
                segment["records"].append(
                    {
                        "supervisor_receipt": receipt,
                        "sample": sample,
                        "sample_sha256": digest(sample),
                    }
                )
            header, text = segment_header(status, segment)
            sizes += len(text)
            rpc("begin", header)
            for index, offset in enumerate(range(0, len(text), 1200)):
                rpc("fragment", {"index": index, "text": text[offset : offset + 1200]})
            fragments += math.ceil(len(text) / 1200)
            status = rpc("commit", {})
            assert (
                status["positions"] == header["last"]
                and status["prefix"] == header["prefix"]
            )
        assert sizes > 64 * 1024**2
        assert status["validated"] == 48000
        assert calls == 1 + 1500 * 2 + fragments
        assert rpc("status", {}) == status
        # Relectura independiente del journal realmente serializado.
        originals = folder / "segments-original.jsonl"
        count = 0
        for line in originals.open(encoding="utf-8"):
            segment = json.loads(line)
            for record in segment["records"]:
                count += 1
                assert record["supervisor_receipt"]["ordinal"] == count
                assert record["sample_sha256"] == digest(record["sample"])
        assert count == 48000
        exclusive_json(
            folder / "result.json",
            {
                "synthetic_cpu": True,
                "logical_episodes": count,
                "serialized_characters": sizes,
                "actual_rpc_calls": calls,
                "fragments": fragments,
                "duration_wall_s": time.monotonic() - started,
                "synthetic_duration_s": 48000,
                "canonical_gpu_chain": False,
                "final_prefix": status,
            },
        )
    finally:
        worker.close()
    assert worker.close_evidence["job_empty"] and worker.close_evidence["reader_joined"]
