"""Unidad canónica CPU sintética; procesos, archivos y relojes Windows reales."""

import ast
import copy
import importlib
import importlib.util
import json
import os
import time
import uuid
from pathlib import Path

import pytest


def _private_root():
    cache = (Path.cwd() / ".cache").resolve()
    supplied = os.environ.get("STUDIO_CANONICAL_TEST_ROOT")
    base = Path(supplied).resolve() if supplied else cache / "pytest/canonical-active"
    if not base.is_relative_to(cache):
        raise ValueError("canonical_test_root_outside_repo_cache")
    private = base / ("run-" + uuid.uuid4().hex)
    private.mkdir(parents=True)
    return private


PRIVATE = _private_root()


def _native_fixture():
    """Clon privado; conserva AST de tests y confina toda escritura de fixture."""
    path = PRIVATE / "fixtures/canonical_native_fixture.py"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        source = (
            Path.cwd() / "scripts/eval/tests/test_benchmark_episode_v3.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignment = next(
            n
            for n in tree.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "PHASE" for t in n.targets)
        )
        lines = source.splitlines(keepends=True)
        lines[assignment.lineno - 1 : assignment.end_lineno] = [
            "PHASE = Path(" + repr(str(PRIVATE / "fixtures/native")) + ")\n"
        ]
        source = "".join(lines)
        if os.environ.get("STUDIO_CANONICAL_FIXTURE_INSTRUMENTATION") == "1":
            source = source.replace(
                "from benchmark_episode import EpisodeAcquirer, read_publications",
                "from benchmark_episode import read_publications\n"
                "from native_measurement import MeasuredAcquirer as EpisodeAcquirer",
            )
            source = source.replace(
                "def close(self):pass",
                'def close(self):save_native_coverage("sensor-close")',
            )
            source = (
                source.replace(
                    "from benchmark_episode import EpisodeProvider",
                    "from benchmark_episode import EpisodeProvider\n"
                    "from native_measurement import save_native_coverage\n"
                    'save_native_coverage("provider-import")',
                    1,
                )
                .replace(
                    'emit({"source":"synthetic_partial","actual_count":self.count})',
                    'emit({"source":"synthetic_partial","actual_count":self.count});'
                    'save_native_coverage("before-sampling")',
                )
                .replace(
                    "super().checkpoint(stage,emit)",
                    "super().checkpoint(stage,emit);save_native_coverage(stage)",
                )
            )
        original_tree = ast.parse(
            (Path.cwd() / "scripts/eval/tests/test_benchmark_episode_v3.py").read_text(
                encoding="utf-8"
            )
        )
        retained = lambda tree: [
            ast.dump(n, include_attributes=False)
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name != "episode_factory"
        ]
        # Fixture plumbing is the only function changed; all test/helper AST stay exact.
        assert retained(ast.parse(source)) == retained(original_tree)
        path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("canonical_private_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


episode_factory = _native_fixture().episode_factory


@pytest.mark.parametrize("target", ["attempt", "anchor", "both", "transition"])
def test_caller_identity_is_frozen_before_request_io(
    episode_factory, monkeypatch, target
):
    c = canonical()
    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        attempts = copy.deepcopy(observer.attempts)
        anchors = copy.deepcopy(attempts)
        original_attempt = copy.deepcopy(attempts[0])
        directory = observer.root / original_attempt["receipt"]["episode_id"]
        baseline = c.fold_originals(
            observer.root,
            attempts,
            context,
            trusted_attempts=anchors,
            historical=True,
        )
        original_read = c.read_json
        interleavings = []

        def mutate_at_request(path):
            if path == directory / "request.json":
                interleavings.append(str(path))
                if target in {"attempt", "both", "transition"}:
                    attempts[0]["receipt"]["ownership"]["pid"] = 0
                if target in {"anchor", "both"}:
                    anchors[0]["receipt"]["ownership"]["pid"] = 0
            return original_read(path)

        monkeypatch.setattr(c, "read_json", mutate_at_request)
        try:
            result = (
                c.transition(
                    c.Snapshot(), directory, attempts[0], context, historical=True
                )
                if target == "transition"
                else c.fold_originals(
                    observer.root,
                    attempts,
                    context,
                    trusted_attempts=anchors,
                    historical=True,
                )
            )
        except ValueError:
            assert interleavings == [str(directory / "request.json")]
            return
        assert interleavings == [str(directory / "request.json")]
        assert c._thaw(result.last_receipt) == original_attempt["receipt"]
        assert c._thaw(result.history.attempt) == original_attempt
        assert result.samples() == baseline.samples()
        # Caller mutation after return and edits to decoded exports have no alias.
        attempts[0]["receipt"]["ownership"]["pid"] = -1
        anchors[0]["receipt"]["ownership"]["pid"] = -2
        exported = c._thaw(result.history.attempt)
        exported["receipt"]["ownership"]["pid"] = -3
        exported_samples = result.samples()
        exported_samples[0]["nvml"]["used_mb"] = 0
        assert c._thaw(result.history.attempt) == original_attempt
        assert c._thaw(result.last_receipt) == original_attempt["receipt"]
        assert result.samples() == baseline.samples()
    finally:
        cleanup(observer, "caller-identity-" + target)


def canonical():
    return importlib.import_module("benchmark_canonical")


@pytest.mark.parametrize("status", ["rejected", "interrupted"])
def test_direct_transition_nonaccepted_inputs_and_exports_do_not_alias(
    episode_factory, status
):
    c = canonical()
    from benchmark_process import WorkerFailure

    observer, context = episode_factory(
        **(
            {"invalid": True}
            if status == "rejected"
            else {"block_stage": "commit_fsync"}
        )
    )
    try:
        with pytest.raises(ValueError if status == "rejected" else WorkerFailure):
            observer.acquire("phase")
        attempt = copy.deepcopy(observer.attempts[-1])
        original = copy.deepcopy(attempt)
        empty = c.Snapshot()
        result = c.transition(
            empty,
            observer.root / attempt["request"]["episode_id"],
            attempt,
            context,
            historical=True,
        )
        assert result.history.previous is empty.history
        assert c._thaw(result.history.attempt) == original
        assert c._thaw(result.prior_start) == original["request"]["start"]
        attempt["request"]["start"]["monotonic_ns"] = 0
        context.clear()
        exported = c._thaw(result.history.attempt)
        exported["request"]["start"]["monotonic_ns"] = -1
        assert c._thaw(result.history.attempt) == original
        assert c._thaw(result.prior_start) == original["request"]["start"]
        assert result.last_receipt is None and result.samples() == []
        assert empty == c.Snapshot()
    finally:
        cleanup(observer, "direct-alias-" + status)


def entries(observer, attempt):
    from hashlib import sha256

    from benchmark_custody import SourceEntry

    episode_id = (
        attempt["receipt"]["episode_id"]
        if attempt["status"] == "accepted"
        else attempt["request"]["episode_id"]
    )
    directory = observer.root / episode_id
    return [
        SourceEntry(p.name, p, len(p.read_bytes()), sha256(p.read_bytes()).hexdigest())
        for p in sorted(directory.glob("*.json"))
    ]


def cleanup(observer, name):
    from benchmark_process import process_alive

    observer.close()
    assert not observer.worker.reader.is_alive()
    assert not process_alive(observer.worker.pid)
    assert observer.worker.close_evidence["job_empty"]
    assert observer.worker.close_evidence["errors"] == []
    (PRIVATE / (name + "-cleanup.json")).write_text(
        json.dumps(
            {
                "native_argv": observer.worker.process.args,
                "native_cwd": str(Path.cwd()),
                "ownership": observer.worker.ownership,
                "attempts": observer.attempts,
                "receipts": observer.receipts,
                "context": observer.observation_context,
                "cleanup": observer.worker.close_evidence,
                "reader_alive": observer.worker.reader.is_alive(),
                "old_cleanup": "UNKNOWN",
            },
            indent=2,
        )
    )


def test_native_incremental_equals_independent_original_fold(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore
    from benchmark_episode import read_publications, summary

    observer, context = episode_factory()
    profiles = []
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            native_read = store.read
            actual_reads = []

            def measured_read(ref, name, *, offset, length, deadline):
                result = native_read(
                    ref, name, offset=offset, length=length, deadline=deadline
                )
                actual_reads.append(
                    {
                        "capsule": ref.capsule_id,
                        "entry": name,
                        "offset": offset,
                        "requested": length,
                        "received": len(result),
                    }
                )
                return result

            store.read = measured_read
            for _ in range(3):
                observer.acquire("phase")
                attempt = copy.deepcopy(observer.attempts[-1])
                token = state.capture(
                    entries(observer, attempt),
                    attempt,
                    trusted_attempt=observer.attempts[-1],
                    context=context,
                )
                candidate = state.propose(
                    token,
                    attempt,
                    trusted_attempt=observer.attempts[-1],
                    record=observer.last_record,
                    context=context,
                )
                before = state.snapshot
                state.commit(candidate)
                assert state.snapshot.cursor == before.cursor + 1
                profile = state.read_profile
                current = actual_reads
                actual_reads = []
                assert len({r["capsule"] for r in current}) == 1
                assert sum(r["received"] for r in current) == profile["bytes"]
                assert sum(r["requested"] > 0 for r in current) == profile["reads"]
                profile["native_pass_through"] = current
                profile["provider_owned_files"] = len(entries(observer, attempt))
                profiles.append(profile)
            originals = c.fold_originals(
                observer.root,
                observer.attempts,
                context,
                trusted_attempts=observer.attempts,
                historical=True,
            )
            legacy = read_publications(
                observer.root,
                observer.receipts,
                context,
                trusted_receipts=observer.receipts,
                attempts=observer.attempts,
                trusted_attempts=observer.attempts,
                historical=True,
            )
            assert originals.samples() == legacy == state.offline_samples()
            assert [summary(s) for s in legacy] == [
                summary(s) for s in state.offline_samples()
            ]
            assert all(p["old_entry_reads"] == 0 and p["bytes"] > 0 for p in profiles)
            assert state.snapshot.accepted_count == 3
            (PRIVATE / "read-profile.json").write_text(json.dumps(profiles, indent=2))
    finally:
        cleanup(observer, "equivalence")


@pytest.mark.parametrize(
    "attack",
    ["unknown", "foreign", "fabricated", "context", "anchor", "skip", "summary"],
)
def test_binding_and_atomic_rollback(episode_factory, attack):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            observer.acquire("phase")
            attempt = copy.deepcopy(observer.attempts[-1])
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=observer.attempts[-1],
                context=context,
            )
            original = state.snapshot
            supplied = copy.deepcopy(context)
            trusted = observer.attempts[-1]
            record = copy.deepcopy(observer.last_record)
            if attack == "unknown":
                token = object()
            elif attack == "foreign":
                other = c.CanonicalState(observer.root, context, store)
                token = other.capture(
                    entries(observer, attempt),
                    attempt,
                    trusted_attempt=trusted,
                    context=context,
                )
            elif attack == "fabricated":
                token = copy.copy(token)
            elif attack == "context":
                supplied["session_id"] = "foreign"
            elif attack == "anchor":
                trusted = copy.deepcopy(trusted)
                trusted["receipt"]["ownership"]["pid"] += 1
            elif attack == "skip":
                attempt["receipt"]["ordinal"] = 2
                trusted = attempt
            else:
                record["sample"]["nvml"]["used_mb"] += 1
            reads = state.read_profile["reads"]
            with pytest.raises(ValueError):
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=trusted,
                    record=record,
                    context=supplied,
                )
            assert state.snapshot is original
            if attack != "summary":
                assert state.read_profile["reads"] == reads
    finally:
        cleanup(observer, "rollback-" + attack)


def test_candidate_stale_parallel_and_caller_immutability(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            original_context = copy.deepcopy(context)
            state = c.CanonicalState(observer.root, context, store)
            context["session_id"] = "mutated"
            observer.acquire("phase")
            attempt = copy.deepcopy(observer.attempts[-1])
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=observer.attempts[-1],
                context=original_context,
            )
            one = state.propose(
                token,
                attempt,
                trusted_attempt=observer.attempts[-1],
                record=observer.last_record,
                context=original_context,
            )
            two = state.propose(
                token,
                attempt,
                trusted_attempt=observer.attempts[-1],
                record=observer.last_record,
                context=original_context,
            )
            attempt["receipt"]["ownership"]["pid"] = 0
            state.commit(one)
            saved = state.snapshot
            with pytest.raises(ValueError, match="stale"):
                state.commit(two)
            assert state.snapshot is saved
            exported = state.offline_samples()
            exported[0]["nvml"]["used_mb"] = 0
            assert state.offline_samples()[0]["nvml"]["used_mb"] == 1200
    finally:
        cleanup(observer, "parallel")


def test_original_deadline_no_live_historical_escape(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            candidate = state.propose(
                token,
                attempt,
                trusted_attempt=attempt,
                record=observer.last_record,
                context=context,
            )
            saved = state.snapshot
            remaining = attempt["receipt"]["deadline_ns"] / 1e9 - time.perf_counter()
            time.sleep(max(0, remaining) + 0.02)
            with pytest.raises(ValueError, match="deadline"):
                state.commit(candidate)
            assert state.snapshot is saved
            with pytest.raises(TypeError):
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    historical=True,
                )
    finally:
        cleanup(observer, "deadline")


@pytest.mark.parametrize(
    "attack",
    [
        "begin",
        "middle",
        "end",
        "missing_raw",
        "missing_progress",
        "commit",
        "partial",
        "extra_raw",
        "extra_progress",
    ],
)
def test_independent_fold_rejects_original_tampering(episode_factory, attack):
    c = canonical()
    observer, context = episode_factory()
    try:
        for _ in range(3):
            observer.acquire("phase")
        index = {"begin": 0, "middle": 1, "end": 2}.get(attack, 1)
        directory = observer.root / observer.receipts[index]["episode_id"]
        if attack in {"begin", "middle", "end", "partial"}:
            (directory / "raw-1.json").write_bytes(b'{"truncated":')
        elif attack == "missing_raw":
            (directory / "raw-1.json").unlink()
        elif attack == "missing_progress":
            (directory / "progress-1.json").unlink()
        elif attack == "commit":
            (directory / "commit.json").write_bytes(b"{}\n")
        elif attack == "extra_raw":
            (directory / "raw-2.json").write_bytes(
                (directory / "raw-1.json").read_bytes()
            )
        else:
            (directory / "progress-99.json").write_bytes(b"{}\n")
        with pytest.raises(ValueError):
            c.fold_originals(
                observer.root,
                observer.attempts,
                context,
                trusted_attempts=observer.attempts,
                historical=True,
            )
    finally:
        cleanup(observer, "tamper-" + attack)


def test_native_rejection_break_and_fold_equivalence(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    sensor = observer.root.parents[1] / "sensor_fixture.py"
    # Private fixture configuration only: the native child rechecks a local
    # switch; sensors are synthetic, validator/kernel/clocks are untouched.
    cleanup(observer, "rejection-bootstrap")
    sensor.write_text(
        sensor.read_text(encoding="utf-8").replace(
            'if self.config.get("invalid"):',
            'if self.config.get("invalid") or Path(__file__).with_name("invalid.flag").exists():',
        ),
        encoding="utf-8",
    )
    from benchmark_episode import EpisodeAcquirer, read_publications

    observer = EpisodeAcquirer(
        root=observer.root.parent / "sequence",
        context_path=sensor.with_name("context.json"),
        trusted_handler=f"{sensor}:Fixture",
    )
    switch = sensor.with_name("invalid.flag")
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            for rejected in (False, True, False):
                if rejected:
                    switch.write_text("synthetic invalid sensor", encoding="utf-8")
                    with pytest.raises(ValueError):
                        observer.acquire("phase")
                else:
                    switch.unlink(missing_ok=True)
                    observer.acquire("phase")
                attempt = observer.attempts[-1]
                token = state.capture(
                    entries(observer, attempt),
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                )
                state.commit(
                    state.propose(
                        token,
                        attempt,
                        trusted_attempt=attempt,
                        context=context,
                        record=observer.last_record,
                    )
                )
                if rejected:
                    assert state.snapshot.last_receipt is None
                    assert state.snapshot.rejection_adjacency
                    assert state.snapshot.last_accepted_receipt is not None
                    assert state.snapshot.last_accepted_sample is not None
                with (
                    pytest.raises(ValueError, match="interrupted")
                    if state.snapshot.interrupted
                    else __import__("contextlib").nullcontext()
                ):
                    state.accredit()
            assert observer.receipts[-1]["previous_receipt_sha256"] is None
            full = c.fold_originals(
                observer.root,
                observer.attempts,
                context,
                trusted_attempts=observer.attempts,
                historical=True,
            )
            old = read_publications(
                observer.root,
                observer.receipts,
                context,
                trusted_receipts=observer.receipts,
                attempts=observer.attempts,
                trusted_attempts=observer.attempts,
                historical=True,
            )
            assert full.samples() == old == state.offline_samples()
            assert full.rolling_hash == state.snapshot.rolling_hash
            assert state.snapshot.cursor == 3 and state.snapshot.accepted_count == 2
    finally:
        cleanup(observer, "rejection")


def test_native_interrupted_partial_bytes_are_not_accreditation(episode_factory):
    c = canonical()
    from benchmark_process import WorkerFailure

    observer, context = episode_factory(block_stage="commit_fsync")
    try:
        with pytest.raises(WorkerFailure):
            observer.acquire("phase")
        assert list(observer.root.rglob("commit.json"))
        head = c.fold_originals(
            observer.root,
            observer.attempts,
            context,
            trusted_attempts=observer.attempts,
            historical=True,
        )
        assert head.cursor == 1 and head.accepted_count == 0
        assert head.last_sample is None and head.interrupted
        attempt = copy.deepcopy(observer.attempts[0])
        attempt["interrupted"]["progress"][-1]["monotonic_ns"] = (
            attempt["request"]["start"]["monotonic_ns"] - 1
        )
        with pytest.raises(ValueError, match="progress_clock"):
            c.fold_originals(
                observer.root,
                [attempt],
                context,
                trusted_attempts=[attempt],
                historical=True,
            )
    finally:
        cleanup(observer, "interrupted")


def test_native_lost_old_witness_unknown_quarantined(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    store = CustodyStore(PRIVATE / "fixtures")
    try:
        state = c.CanonicalState(observer.root, context, store)
        for _ in range(2):
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            state.commit(
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    record=observer.last_record,
                )
            )
        assert state.accredit()["cursor"] == 2
        saved = state.snapshot
        store.close()
        with pytest.raises(ValueError, match="unknown_quarantined"):
            state.accredit()
        assert state.snapshot is saved
        assert state.disposition == "unknown_quarantined"
        with pytest.raises(ValueError, match="unknown_quarantined"):
            state.accredit()
    finally:
        store.close()
        cleanup(observer, "lost")


def test_no_unissued_candidate_or_lost_cursor_authority(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            with pytest.raises(ValueError):
                state.commit(object())
            with pytest.raises(ValueError, match="unknown_quarantined"):
                state.accredit()
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            state.commit(
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    record=observer.last_record,
                )
            )
            state.lose_authority()
            with pytest.raises(ValueError, match="unknown_quarantined"):
                state.accredit()
            assert state.disposition == "unknown_quarantined"
    finally:
        cleanup(observer, "cursor")


def test_live_read_late_atomic_failure(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            original_read = store.read

            def delayed_read(ref, name, *, offset, length, deadline):
                time.sleep(max(0, deadline - time.perf_counter()) + 0.02)
                return original_read(
                    ref, name, offset=offset, length=length, deadline=deadline
                )

            store.read = delayed_read
            saved = state.snapshot
            with pytest.raises(ValueError, match="unknown_quarantined"):
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    record=observer.last_record,
                )
            assert (
                state.snapshot is saved and state.disposition == "unknown_quarantined"
            )
    finally:
        cleanup(observer, "late-read")


def test_offline_freshness_900s_preserved_live_has_no_clock_override(episode_factory):
    c = canonical()
    from datetime import datetime, timedelta, timezone

    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            state.commit(
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    record=observer.last_record,
                )
            )
            assert state.accredit()["cursor"] == 1
            time.sleep(0.02)
            assert state.accredit()["cursor"] == 1
            # Explicit offline policy boundary; no claim of 900s wall/native run.
            future = datetime.now(timezone.utc) + timedelta(seconds=901)
            with pytest.raises(ValueError, match="expired"):
                c.fold_originals(
                    observer.root,
                    observer.attempts,
                    context,
                    trusted_attempts=observer.attempts,
                    now=future,
                )
            assert (
                c.fold_originals(
                    observer.root,
                    observer.attempts,
                    context,
                    trusted_attempts=observer.attempts,
                    now=future,
                    historical=True,
                ).accepted_count
                == 1
            )
            with pytest.raises(TypeError):
                state.accredit(now=future)
            with pytest.raises(TypeError):
                state.accredit(historical=True)
    finally:
        cleanup(observer, "freshness")


@pytest.mark.parametrize(
    "attack",
    [
        "partial",
        "nul",
        "empty",
        "missing_raw",
        "missing_progress",
        "extra_raw",
        "extra_progress",
        "commit",
    ],
)
def test_protected_bytes_fail_before_acceptance(episode_factory, attack):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            directory = observer.root / attempt["receipt"]["episode_id"]
            if attack in {"partial", "nul", "empty"}:
                (directory / "raw-1.json").write_bytes(
                    {"partial": b'{"a":', "nul": b"{}\x00", "empty": b""}[attack]
                )
            elif attack.startswith("missing"):
                (
                    directory
                    / ("raw-1.json" if attack == "missing_raw" else "progress-1.json")
                ).unlink()
            elif attack.startswith("extra"):
                (
                    directory
                    / ("raw-9.json" if attack == "extra_raw" else "progress-99.json")
                ).write_bytes(b"{}\n")
            else:
                (directory / "commit.json").write_bytes(b"{}\n")
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            saved = state.snapshot
            with pytest.raises(ValueError):
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    record=observer.last_record,
                )
            assert state.snapshot is saved
    finally:
        cleanup(observer, "protected-" + attack)


def test_exact_crlf_bytes_authority_separate_from_semantic_digest(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            observer.acquire("phase")
            attempt = observer.attempts[-1]
            directory = observer.root / attempt["receipt"]["episode_id"]
            for p in directory.glob("*.json"):
                p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            state.commit(
                state.propose(
                    token,
                    attempt,
                    trusted_attempt=attempt,
                    context=context,
                    record=observer.last_record,
                )
            )
            full = c.fold_originals(
                observer.root,
                observer.attempts,
                context,
                trusted_attempts=observer.attempts,
                historical=True,
            )
            assert state.offline_samples() == full.samples()
    finally:
        cleanup(observer, "crlf")


def test_no_linear_history_copy_in_transition_or_receipt_lookup():
    c = canonical()
    source = ast.parse(Path(c.__file__).read_text(encoding="utf-8"))
    transition = next(
        n
        for n in source.body
        if isinstance(n, ast.FunctionDef) and n.name == "transition"
    )
    # Structural guard supplements the actual native I/O profile/equivalence.
    assert not any(
        isinstance(n, (ast.For, ast.While, ast.ListComp, ast.SetComp))
        for n in ast.walk(transition)
    )


def test_interrupted_progress_must_remain_monotonic(episode_factory):
    c = canonical()
    from benchmark_process import WorkerFailure

    observer, context = episode_factory(block_stage="commit_fsync")
    try:
        with pytest.raises(WorkerFailure):
            observer.acquire("phase")
        attempt = copy.deepcopy(observer.attempts[-1])
        frames = attempt["interrupted"]["progress"]
        assert len(frames) > 2
        frames[-1]["monotonic_ns"] = attempt["request"]["start"]["monotonic_ns"] + 1
        with pytest.raises(ValueError, match="progress_clock"):
            c.fold_originals(
                observer.root,
                [attempt],
                context,
                trusted_attempts=[attempt],
                historical=True,
            )
    finally:
        cleanup(observer, "interrupted-monotonic")


@pytest.mark.parametrize("status", ["rejected", "interrupted"])
def test_nonaccepted_transition_requires_external_native_ownership(
    episode_factory, status
):
    c = canonical()
    from benchmark_process import WorkerFailure

    observer, context = episode_factory(
        **(
            {"invalid": True}
            if status == "rejected"
            else {"block_stage": "commit_fsync"}
        )
    )
    try:
        with pytest.raises(ValueError if status == "rejected" else WorkerFailure):
            observer.acquire("phase")
        attempt = copy.deepcopy(observer.attempts[-1])
        assert attempt["status"] == status
        if status == "rejected":
            attempt["ownership"] = {}
        else:
            attempt["interrupted"]["evidence"]["ownership"] = {}
        with pytest.raises(ValueError, match="identity"):
            c.fold_originals(
                observer.root,
                [attempt],
                context,
                trusted_attempts=[attempt],
                historical=True,
            )
    finally:
        cleanup(observer, "nonaccepted-ownership-" + status)


def test_transition_accepted_effects_and_immutable_link(episode_factory):
    c = canonical()
    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        empty = c.Snapshot()
        attempt = observer.attempts[-1]
        head = c.transition(
            empty,
            observer.root / attempt["receipt"]["episode_id"],
            attempt,
            context,
            historical=True,
        )
        assert (head.cursor, head.accepted_count) == (1, 1)
        assert empty.cursor == 0
        assert head.history.previous is empty.history
        assert head.samples()[0]["nvml"]["used_mb"] == 1200
        exported = head.samples()
        exported[0]["nvml"]["used_mb"] = 0
        assert head.samples()[0]["nvml"]["used_mb"] == 1200
    finally:
        cleanup(observer, "transition-accepted")


@pytest.mark.parametrize("status", ["rejected", "interrupted"])
def test_transition_nonaccepted_effects(episode_factory, status):
    c = canonical()
    from benchmark_process import WorkerFailure

    observer, context = episode_factory(
        **(
            {"invalid": True}
            if status == "rejected"
            else {"block_stage": "commit_fsync"}
        )
    )
    try:
        with pytest.raises(ValueError if status == "rejected" else WorkerFailure):
            observer.acquire("phase")
        attempt = observer.attempts[-1]
        empty = c.Snapshot()
        head = c.transition(
            empty,
            observer.root / attempt["request"]["episode_id"],
            attempt,
            context,
            historical=True,
        )
        assert (
            head.cursor,
            head.accepted_count,
            head.interrupted,
            head.rejection_adjacency,
            head.last_receipt,
        ) == (1, 0, True, True, None)
        assert head.samples() == [] and empty.cursor == 0
    finally:
        cleanup(observer, "transition-" + status)


def test_independent_fold_effects_and_same_transition(episode_factory, monkeypatch):
    c = canonical()
    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        original = c.transition
        visits = []

        def measured(head, *args, **kwargs):
            visits.append(head.cursor)
            return original(head, *args, **kwargs)

        monkeypatch.setattr(c, "transition", measured)
        result = c.fold_originals(
            observer.root,
            observer.attempts,
            context,
            trusted_attempts=observer.attempts,
            historical=True,
        )
        assert (result.cursor, result.accepted_count, visits) == (1, 1, [0])
    finally:
        cleanup(observer, "fold-effects")


def test_capture_context_binding_before_source_io(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            source_entries = entries(observer, observer.attempts[-1])
            reads = []
            original = store.capture

            def measured(*args, **kwargs):
                reads.append(True)
                return original(*args, **kwargs)

            store.capture = measured
            foreign = copy.deepcopy(context)
            foreign["session_id"] = "foreign"
            with pytest.raises(ValueError, match="context"):
                state.capture(
                    source_entries,
                    observer.attempts[-1],
                    trusted_attempt=observer.attempts[-1],
                    context=foreign,
                )
            assert reads == [] and state.snapshot.cursor == 0
    finally:
        cleanup(observer, "capture-binding")


def test_capture_closed_path_binding_before_source_io(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore, SourceEntry

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            source_entries = entries(observer, observer.attempts[-1])
            entry = source_entries[0]
            source_entries[0] = SourceEntry(
                entry.name, observer.root / entry.name, entry.length, entry.seal
            )
            with pytest.raises(ValueError, match="source_binding"):
                state.capture(
                    source_entries,
                    observer.attempts[-1],
                    trusted_attempt=observer.attempts[-1],
                    context=context,
                )
            assert state.snapshot.cursor == 0
    finally:
        cleanup(observer, "capture-path")


def test_capsule_prepare_reads_payload_and_freezes_report(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        attempt = copy.deepcopy(observer.attempts[-1])
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=observer.attempts[-1],
                context=context,
            )
            record = copy.deepcopy(observer.last_record)
            candidate = state.propose(
                token,
                attempt,
                trusted_attempt=observer.attempts[-1],
                context=context,
                record=record,
            )
            assert state.read_profile["bytes"] > 0
            assert state.snapshot.cursor == 0
            record["sample"]["nvml"]["used_mb"] = 0
            attempt["receipt"]["ownership"]["pid"] = 0
            assert candidate.proposed.samples()[0]["nvml"]["used_mb"] == 1200
    finally:
        cleanup(observer, "prepare-effects")


def test_original_fold_requires_independent_supervisor_anchor(episode_factory):
    c = canonical()
    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        trusted = copy.deepcopy(observer.attempts)
        trusted[0]["receipt"]["ownership"]["pid"] += 1
        with pytest.raises(ValueError, match="anchor"):
            c.fold_originals(
                observer.root,
                observer.attempts,
                context,
                trusted_attempts=trusted,
                historical=True,
            )
    finally:
        cleanup(observer, "fold-anchor")


def test_transition_rejects_nonmonotonic_prior_start(episode_factory):
    c = canonical()
    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        attempt = observer.attempts[-1]
        # An existing trusted cursor's prior start must be obeyed independently
        # of predecessor sample availability (rejections break that adjacency).
        head = c.Snapshot(prior_start=c.encode(attempt["receipt"]["start"], c.MAX_FILE))
        with pytest.raises(ValueError, match="replayed"):
            c.transition(
                head,
                observer.root / attempt["receipt"]["episode_id"],
                attempt,
                context,
                historical=True,
            )
        assert head.cursor == 0
    finally:
        cleanup(observer, "transition-replay")


def test_commit_publishes_frozen_effects(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = copy.deepcopy(observer.attempts[-1])
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=observer.attempts[-1],
                context=context,
            )
            candidate = state.propose(
                token,
                attempt,
                trusted_attempt=observer.attempts[-1],
                context=context,
                record=observer.last_record,
            )
            assert state.snapshot.cursor == 0
            state.commit(candidate)
            assert (state.snapshot.cursor, state.snapshot.accepted_count) == (1, 1)
            assert state.offline_samples()[0]["nvml"]["used_mb"] == 1200
    finally:
        cleanup(observer, "commit-effects")


def test_copied_candidate_cannot_publish(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            candidate = state.propose(
                token,
                attempt,
                trusted_attempt=attempt,
                context=context,
                record=observer.last_record,
            )
            saved = state.snapshot
            with pytest.raises(ValueError, match="foreign"):
                state.commit(copy.copy(candidate))
            assert state.snapshot is saved
    finally:
        cleanup(observer, "candidate-copy")


def test_capture_requires_external_anchor(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            source_entries = entries(observer, attempt)
            with pytest.raises(ValueError, match="anchor"):
                state.capture(
                    source_entries, attempt, trusted_attempt=None, context=context
                )
            assert state.snapshot.cursor == 0
    finally:
        cleanup(observer, "capture-anchor")


def test_commit_requires_live_native_pin(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    store = CustodyStore(PRIVATE / "fixtures")
    try:
        observer.acquire("phase")
        state = c.CanonicalState(observer.root, context, store)
        attempt = observer.attempts[-1]
        token = state.capture(
            entries(observer, attempt),
            attempt,
            trusted_attempt=attempt,
            context=context,
        )
        candidate = state.propose(
            token,
            attempt,
            trusted_attempt=attempt,
            context=context,
            record=observer.last_record,
        )
        saved = state.snapshot
        store.close()
        with pytest.raises(ValueError, match="unknown_quarantined"):
            state.commit(candidate)
        assert state.snapshot is saved
        assert state.disposition == "unknown_quarantined"
    finally:
        store.close()
        cleanup(observer, "commit-pin")


def test_revoked_authority_preserves_cursor_and_blocks_commit(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            candidate = state.propose(
                token,
                attempt,
                trusted_attempt=attempt,
                context=context,
                record=observer.last_record,
            )
            saved = state.snapshot
            state.lose_authority()
            with pytest.raises(ValueError, match="unknown_quarantined"):
                state.commit(candidate)
            assert (
                state.snapshot is saved and state.disposition == "unknown_quarantined"
            )
    finally:
        cleanup(observer, "revoked-effects")


def test_empty_cursor_cannot_accredit():
    c = canonical()
    from benchmark_custody import CustodyStore
    from test_benchmark_observation import CONTEXT

    with CustodyStore(PRIVATE / "fixtures") as store:
        state = c.CanonicalState(PRIVATE / "empty", CONTEXT, store)
        with pytest.raises(ValueError, match="unknown_quarantined"):
            state.accredit()
        assert state.snapshot.cursor == 0


def test_late_read_quarantines_without_cursor_publish(episode_factory):
    c = canonical()
    from benchmark_custody import CustodyError, CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            native_read = store.read

            def delayed(*args, **kwargs):
                time.sleep(max(0, kwargs["deadline"] - time.perf_counter()) + 0.02)
                return native_read(*args, **kwargs)

            store.read = delayed
            saved = state.snapshot
            try:
                state.propose(token, attempt, trusted_attempt=attempt, context=context)
            except (ValueError, CustodyError):
                pass
            assert (state.disposition, state.snapshot is saved) == (
                "unknown_quarantined",
                True,
            )
    finally:
        cleanup(observer, "late-quarantine-effects")


@pytest.mark.parametrize("operation", ["capture", "commit"])
def test_late_native_completion_never_exposes_acceptance(episode_factory, operation):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            source_entries = entries(observer, attempt)
            native = store.capture if operation == "capture" else store.read

            def returned_late(*args, **kwargs):
                result = native(*args, **kwargs)
                time.sleep(max(0, kwargs["deadline"] - time.perf_counter()) + 0.02)
                return result

            if operation == "capture":
                store.capture = returned_late
                action = lambda: state.capture(
                    source_entries, attempt, trusted_attempt=attempt, context=context
                )
            else:
                token = state.capture(
                    source_entries, attempt, trusted_attempt=attempt, context=context
                )
                candidate = state.propose(
                    token, attempt, trusted_attempt=attempt, context=context
                )
                store.read = returned_late
                action = lambda: state.commit(candidate)
            saved = state.snapshot
            with pytest.raises(ValueError, match="deadline"):
                action()
            assert state.snapshot is saved
    finally:
        cleanup(observer, "late-completion-" + operation)


@pytest.mark.parametrize("operation", ["accredit", "commit"])
def test_external_clock_freshness_rechecked_at_exposure(
    episode_factory, monkeypatch, operation
):
    c = canonical()
    from datetime import datetime, timedelta, timezone

    import benchmark_observation as observation
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            candidate = state.propose(
                token, attempt, trusted_attempt=attempt, context=context
            )
            if operation == "accredit":
                state.commit(candidate)
                assert state.accredit()["cursor"] == 1
            saved = state.snapshot
            future = datetime.now(timezone.utc) + timedelta(seconds=901)
            # Policy clock probe only: no claim of 901s elapsed native wall time.
            monkeypatch.setattr(observation, "utc_now", lambda: future.isoformat())
            with pytest.raises(ValueError, match="expired"):
                state.accredit() if operation == "accredit" else state.commit(candidate)
            assert state.snapshot is saved
    finally:
        cleanup(observer, "external-freshness-" + operation)


@pytest.mark.parametrize("operation", ["capture", "propose"])
def test_revocation_blocks_payload_io(episode_factory, operation):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            source_entries = entries(observer, attempt)
            token = state.capture(
                source_entries, attempt, trusted_attempt=attempt, context=context
            )
            state.lose_authority()
            calls = []
            native_capture, native_read = store.capture, store.read

            def measured_capture(*args, **kwargs):
                calls.append("capture")
                return native_capture(*args, **kwargs)

            def measured_read(*args, **kwargs):
                calls.append("read")
                return native_read(*args, **kwargs)

            store.capture, store.read = measured_capture, measured_read
            with pytest.raises(ValueError, match="unknown_quarantined"):
                if operation == "capture":
                    state.capture(
                        source_entries,
                        attempt,
                        trusted_attempt=attempt,
                        context=context,
                    )
                else:
                    state.propose(
                        token, attempt, trusted_attempt=attempt, context=context
                    )
            assert calls == [] and state.snapshot.cursor == 0
    finally:
        cleanup(observer, "revocation-io-" + operation)


def test_store_authority_cannot_be_minted_by_caller():
    c = canonical()
    from test_benchmark_observation import CONTEXT

    with pytest.raises(ValueError, match="owned_store"):
        c.CanonicalState(PRIVATE / "empty", CONTEXT, object())


def test_late_semantic_prepare_never_exposes_candidate(episode_factory, monkeypatch):
    c = canonical()
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            native_transition = c.transition

            def returned_late(*args, **kwargs):
                result = native_transition(*args, **kwargs)
                time.sleep(
                    max(
                        0, attempt["receipt"]["deadline_ns"] / 1e9 - time.perf_counter()
                    )
                    + 0.02
                )
                return result

            monkeypatch.setattr(c, "transition", returned_late)
            saved = state.snapshot
            with pytest.raises(ValueError, match="deadline"):
                state.propose(token, attempt, trusted_attempt=attempt, context=context)
            assert state.snapshot is saved
    finally:
        cleanup(observer, "late-prepare")


def test_concurrent_candidates_only_one_publishes(episode_factory):
    c = canonical()
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        observer.acquire("phase")
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            attempt = observer.attempts[-1]
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            candidates = [
                state.propose(token, attempt, trusted_attempt=attempt, context=context)
                for _ in range(2)
            ]
            native_read = store.read

            def slower_native(*args, **kwargs):
                result = native_read(*args, **kwargs)
                time.sleep(0.05)
                return result

            store.read = slower_native
            started = threading.Barrier(2)

            def publish(candidate):
                started.wait(timeout=1)
                try:
                    state.commit(candidate)
                    return "published"
                except ValueError as error:
                    assert "stale" in str(error)
                    return "stale"

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(publish, candidates))
            assert sorted(results) == ["published", "stale"]
            assert (state.snapshot.cursor, state.snapshot.accepted_count) == (1, 1)
    finally:
        cleanup(observer, "concurrent-candidates")


def _lease_publish(state, observer, context):
    """Adquisición y transición nativas existentes; ningún validador sustituido."""
    observer.acquire("phase")
    attempt = observer.attempts[-1]
    token = state.capture(
        entries(observer, attempt), attempt, trusted_attempt=attempt, context=context
    )
    return state.commit(
        state.propose(token, attempt, trusted_attempt=attempt, context=context)
    )


@pytest.mark.parametrize("ingress", ["healthy", "revoke"])
def test_accredit_yields_state_after_actual_native_witness(episode_factory, ingress):
    """Gate Event de scheduling sintético DESPUÉS de witness nativo real."""
    import threading

    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    gate, release, completed = threading.Event(), threading.Event(), threading.Event()
    workers, outcomes = [], {}
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            checkout_head = _lease_publish(state, observer, context)
            native = state._witness

            def paused_after_native(registration, deadline):
                native(registration, deadline)
                if threading.current_thread().name == "lease-read":
                    gate.set()
                    if not release.wait(1.5):
                        raise AssertionError("own synthetic scheduling gate timed out")

            state._witness = paused_after_native

            def read():
                try:
                    outcomes["read"] = state.accredit()
                except (ValueError, AssertionError, RuntimeError, OSError) as error:
                    outcomes["read"] = error

            def ingest():
                try:
                    if ingress == "healthy":
                        outcomes["ingest"] = _lease_publish(state, observer, context)
                    else:
                        state.lose_authority()
                        outcomes["ingest"] = "revoked"
                except (ValueError, AssertionError, RuntimeError, OSError) as error:
                    outcomes["ingest"] = error
                finally:
                    completed.set()

            reader = threading.Thread(target=read, name="lease-read")
            workers.append(reader)
            reader.start()
            assert gate.wait(1), "actual native witness did not return"
            writer = threading.Thread(target=ingest, name="lease-ingest")
            workers.append(writer)
            writer.start()
            try:
                assert completed.wait(0.8), "accredit blocked own ingress on state lock"
            finally:
                # Own gate always released, including RED; bounded join, never orphan.
                release.set()
                for worker in workers:
                    worker.join(3)
                    assert not worker.is_alive()
            assert not isinstance(outcomes["ingest"], Exception)
            if ingress == "healthy":
                assert outcomes["read"] == {
                    "cursor": checkout_head.cursor,
                    "prefix": checkout_head.rolling_hash,
                }
                assert state.snapshot.cursor == checkout_head.cursor + 1
            else:
                assert isinstance(outcomes["read"], ValueError)
                assert "quarantined" in str(outcomes["read"])
    finally:
        release.set()
        for worker in workers:
            worker.join(3)
            assert not worker.is_alive()
        cleanup(observer, "lease-state-gate-" + ingress)


def test_accredit_budget_is_absolute_across_actual_witnesses(
    episode_factory, monkeypatch
):
    """Reloj de política controlado, witnesses nativos reales; NO prueba cadencia."""
    from types import SimpleNamespace

    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            for _ in range(2):
                _lease_publish(state, observer, context)
            native = state._witness
            clock = [time.perf_counter()]
            calls = []
            # Replace only canonical's policy clock, not the real store/process clocks.
            monkeypatch.setattr(
                c, "time", SimpleNamespace(perf_counter=lambda: clock[0])
            )

            def elapsed_after_actual_witness(registration, deadline):
                native(registration, deadline)
                calls.append(deadline)
                clock[0] += 1.1

            state._witness = elapsed_after_actual_witness
            with pytest.raises(ValueError, match="deadline"):
                state.accredit()
            assert len(calls) == 2
            assert calls[0] == calls[1]
    finally:
        cleanup(observer, "lease-absolute-policy")


def test_lease_exact_snapshot_progress_and_zero_prefix_payload(episode_factory):
    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            for _ in range(3):
                selected = _lease_publish(state, observer, context)
            native, calls = store.read, []

            def measured(*args, **kwargs):
                value = native(*args, **kwargs)
                calls.append((args[0], kwargs["length"], len(value)))
                return value

            store.read = measured
            lease = state.checkout(deadline=time.perf_counter() + 2)
            assert calls == []  # checkout does no native IO or prefix material read.
            assert state._leases[lease].snapshot is selected
            assert state._leases[lease].link is selected.history
            with pytest.raises(ValueError, match="busy"):
                state.checkout(deadline=time.perf_counter() + 2)
            with pytest.raises(ValueError, match="unfinished"):
                state.finish_accredit(lease)
            assert state.witness_step(lease) is False
            later = _lease_publish(state, observer, context)
            calls.clear()  # New delta payload IO is independent of prefix witnesses.
            assert state.witness_step(lease) is False
            assert state.witness_step(lease) is True
            assert state.witness_step(lease) is True  # Completed step does not reread.
            assert len(calls) == 2
            assert all(length == received == 0 for _, length, received in calls)
            assert state.finish_accredit(lease) == {
                "cursor": selected.cursor,
                "prefix": selected.rolling_hash,
            }
            assert (
                state.snapshot is later and later.history.previous is selected.history
            )
            with pytest.raises(ValueError, match="finished"):
                state.finish_accredit(lease)
            state.release(lease)
            state.release(lease)
            assert state._leases == {}
            with pytest.raises(ValueError, match="finished"):
                state.finish_accredit(lease)
            assert state.accredit()["cursor"] == 4
    finally:
        cleanup(observer, "lease-exact-prefix")


@pytest.mark.parametrize(
    "attack", ["json", "unknown", "copy", "forged", "state", "caller"]
)
def test_lease_capability_and_foreign_release_do_not_clobber_owner(
    episode_factory, attack
):
    import threading

    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            selected = _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            foreign = (
                c.CanonicalState(observer.root, context, store)
                if attack == "state"
                else state
            )
            token = {
                "json": {"cursor": selected.cursor, "prefix": selected.rolling_hash},
                "unknown": object(),
                "copy": copy.copy(lease),
                "forged": c._ReadLease(state, threading.current_thread(), object()),
            }.get(attack, lease)
            errors = []

            def probe():
                for action in (
                    foreign.witness_step,
                    foreign.finish_accredit,
                    foreign.release,
                ):
                    with pytest.raises(ValueError, match="foreign") as caught:
                        action(token)
                    errors.append(str(caught.value))

            if attack == "caller":
                worker = threading.Thread(target=probe, name="foreign-lease-caller")
                worker.start()
                worker.join(2)
                assert not worker.is_alive()
            else:
                probe()
            assert len(errors) == 3
            assert len(state._leases) == 1 and lease in state._leases
            assert state.witness_step(lease) is True
            assert state.finish_accredit(lease)["cursor"] == selected.cursor
            state.release(lease)
    finally:
        cleanup(observer, "lease-capability-" + attack)


@pytest.mark.parametrize("position", [0, 1, 2])
def test_lease_actual_pin_loss_at_start_middle_end_quarantines(
    episode_factory, position
):
    from benchmark_custody import CustodyError, CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            for _ in range(3):
                selected = _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            for _ in range(position):
                assert state.witness_step(lease) is False
            link = state._leases[lease].link
            registration = state._registry[link.witness]
            refs = dict(state._registry)
            # Actual own pinned handle closure, no fake positive/validator override.
            store._capsules[registration.ref.capsule_id].pin.close()
            with pytest.raises(ValueError, match="quarantined") as caught:
                state.witness_step(lease)
            assert isinstance(caught.value.__cause__, CustodyError)
            assert state._registry == refs and state.snapshot is selected
            assert state.disposition == "unknown_quarantined" and not state._leases
            with pytest.raises(ValueError, match="quarantined"):
                state.finish_accredit(lease)
            state.release(lease)
            state.release(lease)
    finally:
        cleanup(observer, "lease-pin-loss-" + str(position))


@pytest.mark.parametrize(
    "where", ["before_step", "after_step", "finish", "after_validation"]
)
def test_lease_absolute_deadline_includes_waits_and_finish(
    episode_factory, monkeypatch, where
):
    from types import SimpleNamespace

    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            _lease_publish(state, observer, context)
            clock = [time.perf_counter()]
            deadline = clock[0] + 2
            lease = state.checkout(deadline=deadline)
            monkeypatch.setattr(
                c, "time", SimpleNamespace(perf_counter=lambda: clock[0])
            )
            if where == "before_step":
                clock[0] = deadline
                action = lambda: state.witness_step(lease)
            elif where == "after_step":
                native = state._witness

                def elapsed(registration, bound):
                    native(registration, bound)
                    assert bound == deadline
                    clock[0] = deadline

                state._witness = elapsed
                action = lambda: state.witness_step(lease)
            else:
                assert state.witness_step(lease) is True
                if where == "finish":
                    clock[0] = deadline
                else:
                    native_validation = c.validate_samples

                    def elapsed_validation(*args, **kwargs):
                        result = native_validation(*args, **kwargs)
                        clock[0] = deadline
                        return result

                    monkeypatch.setattr(c, "validate_samples", elapsed_validation)
                action = lambda: state.finish_accredit(lease)
            with pytest.raises(ValueError, match="deadline"):
                action()
            state.release(lease)
            assert not state._leases
    finally:
        cleanup(observer, "lease-deadline-" + where)


@pytest.mark.parametrize("deadline", [True, "2", float("nan"), float("inf"), -1])
def test_lease_deadline_requires_finite_absolute_budget(episode_factory, deadline):
    from benchmark_custody import CustodyStore

    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = canonical().CanonicalState(observer.root, context, store)
            _lease_publish(state, observer, context)
            with pytest.raises(ValueError, match="deadline"):
                state.checkout(deadline=deadline)
            assert not state._leases
    finally:
        cleanup(observer, "lease-invalid-deadline-" + repr(deadline))


@pytest.mark.parametrize("age", [900, 901])
def test_lease_finish_uses_actual_sensor_snapshot_and_fresh_policy_clock(
    episode_factory, monkeypatch, age
):
    """Reloj de política acelerado; no acredita cadencia, GPU ni 901s de pared."""
    from datetime import datetime, timedelta

    import benchmark_observation as observation
    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            selected = _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            assert state.witness_step(lease) is True
            timestamp = c._thaw(selected.last_sample)["timestamp"]
            future = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            ) + timedelta(seconds=age)
            monkeypatch.setattr(observation, "utc_now", lambda: future.isoformat())
            if age == 901:
                with pytest.raises(ValueError, match="expired"):
                    state.finish_accredit(lease)
            else:
                assert state.finish_accredit(lease) == {
                    "cursor": selected.cursor,
                    "prefix": selected.rolling_hash,
                }
            state.release(lease)
    finally:
        cleanup(observer, "lease-fresh-policy-" + str(age))


@pytest.mark.parametrize("during", ["step", "finish"])
def test_lease_revocation_epoch_rechecked_before_return(
    episode_factory, monkeypatch, during
):
    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            selected = _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            epoch = state._epoch
            if during == "step":
                native = state._witness

                def revoked(registration, deadline):
                    native(registration, deadline)
                    state.lose_authority()

                state._witness = revoked
                action = lambda: state.witness_step(lease)
            else:
                assert state.witness_step(lease) is True
                native_validation = c.validate_samples

                def revoked(*args, **kwargs):
                    result = native_validation(*args, **kwargs)
                    state.lose_authority()
                    return result

                monkeypatch.setattr(c, "validate_samples", revoked)
                action = lambda: state.finish_accredit(lease)
            with pytest.raises(ValueError, match="quarantined"):
                action()
            assert state._epoch == epoch + 1 and not state._leases
            assert state.snapshot is selected
            state.release(lease)
    finally:
        cleanup(observer, "lease-revoke-return-" + during)


@pytest.mark.parametrize("status", ["rejected", "interrupted"])
def test_lease_nonaccepted_native_newhead_invalidates_selected_prefix(
    episode_factory, status
):
    from benchmark_custody import CustodyStore
    from benchmark_episode import EpisodeAcquirer
    from benchmark_process import WorkerFailure

    c = canonical()
    bootstrap, context = episode_factory()
    sensor = bootstrap.root.parents[1] / "sensor_fixture.py"
    cleanup(bootstrap, "lease-break-bootstrap-" + status)
    text = sensor.read_text(encoding="utf-8")
    text = text.replace(
        'if self.config.get("invalid"):',
        'if self.config.get("invalid") or Path(__file__).with_name("reject.flag").exists():',
    ).replace(
        "super().checkpoint(stage,emit)",
        "super().checkpoint(stage,emit)\n"
        '        if stage=="raw_write" and Path(__file__).with_name("interrupt.flag").exists():raise RuntimeError("own synthetic interrupted native checkpoint")',
    )
    sensor.write_text(text, encoding="utf-8")
    observer = EpisodeAcquirer(
        root=bootstrap.root.parent / "lease-sequence",
        context_path=sensor.with_name("context.json"),
        trusted_handler=f"{sensor}:Fixture",
    )
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            selected = _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            assert state.witness_step(lease) is True
            sensor.with_name(
                "reject.flag" if status == "rejected" else "interrupt.flag"
            ).write_text("own synthetic scheduling/sensor switch")
            with pytest.raises(ValueError if status == "rejected" else WorkerFailure):
                observer.acquire("phase")
            attempt = observer.attempts[-1]
            assert attempt["status"] == status
            token = state.capture(
                entries(observer, attempt),
                attempt,
                trusted_attempt=attempt,
                context=context,
            )
            state.commit(
                state.propose(token, attempt, trusted_attempt=attempt, context=context)
            )
            assert state.snapshot.cursor == selected.cursor + 1
            assert state.snapshot.interrupted and state.snapshot.last_sample is None
            assert state._leases == {}
            with pytest.raises(ValueError, match="interrupted"):
                state.finish_accredit(lease)
            state.release(lease)
            with pytest.raises(ValueError, match="interrupted"):
                state.checkout(deadline=time.perf_counter() + 2)
    finally:
        cleanup(observer, "lease-native-break-" + status)


def test_lease_missing_prefix_registration_fails_closed(episode_factory):
    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            del state._registry[state.snapshot.history.witness]
            with pytest.raises(ValueError, match="quarantined"):
                state.witness_step(lease)
            assert state.disposition == "unknown_quarantined" and not state._leases
            state.release(lease)
    finally:
        cleanup(observer, "lease-missing-registration")


@pytest.mark.parametrize("effect", ["epoch", "release", "recursive"])
def test_lease_progress_cannot_complete_after_own_invalidating_effect(
    episode_factory, effect
):
    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            _lease_publish(state, observer, context)
            lease = state.checkout(deadline=time.perf_counter() + 2)
            native = state._witness

            def interleaved(registration, deadline):
                native(registration, deadline)
                if effect == "epoch":
                    state._epoch += (
                        1  # Synthetic internal epoch change, not wire authority.
                    )
                elif effect == "release":
                    state.release(lease)
                else:
                    with pytest.raises(ValueError, match="busy"):
                        state.witness_step(lease)
                    with pytest.raises(ValueError, match="unfinished"):
                        state.finish_accredit(lease)

            state._witness = interleaved
            if effect == "recursive":
                assert state.witness_step(lease) is True
                assert state.finish_accredit(lease)["cursor"] == 1
            else:
                with pytest.raises(ValueError, match="lease"):
                    state.witness_step(lease)
                with pytest.raises(ValueError, match="lease"):
                    state.finish_accredit(lease)
            state.release(lease)
            state.release(lease)
    finally:
        cleanup(observer, "lease-progress-effect-" + effect)


def test_lease_checkout_is_constant_work_and_registry_bounded(
    episode_factory, monkeypatch
):
    from benchmark_custody import CustodyStore

    c = canonical()
    observer, context = episode_factory()
    try:
        with CustodyStore(PRIVATE / "fixtures") as store:
            state = c.CanonicalState(observer.root, context, store)
            selected = _lease_publish(state, observer, context)
            native_copy = c.copy.deepcopy

            def forbid_history_copy(value, *args, **kwargs):
                assert value is not selected and value is not selected.history
                return native_copy(value, *args, **kwargs)

            monkeypatch.setattr(c.copy, "deepcopy", forbid_history_copy)
            native = store.read
            reads = []

            def measured(*args, **kwargs):
                value = native(*args, **kwargs)
                reads.append(kwargs["length"])
                return value

            store.read = measured
            first = None
            for _ in range(100):
                lease = state.checkout(deadline=time.perf_counter() + 2)
                first = first or lease
                assert len(state._leases) == 1
                assert state._leases[lease].snapshot is selected
                assert state._leases[lease].link is selected.history
                state.release(lease)
                assert not state._leases
            state.release(
                first
            )  # Old issued capability remains idempotent, no tombstones.
            assert reads == []
            lease = state.checkout(deadline=time.perf_counter() + 2)
            state._context = c._freeze({"foreign": "internal context change"})
            with pytest.raises(ValueError, match="context_binding"):
                state.witness_step(lease)
            with pytest.raises(ValueError, match="context_binding"):
                state.finish_accredit(lease)
            state.release(lease)
    finally:
        cleanup(observer, "lease-bounded-checkout")
