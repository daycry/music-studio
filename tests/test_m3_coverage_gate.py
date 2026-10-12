"""Fixtures CPU sintéticas: nunca acreditan autoridad ROOT o producto."""

import copy
import hashlib
import json

import pytest

from scripts import m3_coverage_gate as gate


def test_path_namespace_and_strict_json():
    assert gate.validate_path("src/.hidden.py") == "src/.hidden.py"
    for path in (
        "../escape",
        "/absolute",
        "a//b",
        "a/./b",
        "C:/x",
        "a\\b",
        "CON.py",
        "a. ",
        "e\u0301.py",
        "x\n.py",
    ):
        with pytest.raises(ValueError):
            gate.validate_path(path)
    assert gate.load_json(b'{"count":1}') == {"count": 1}
    for data in (b'{"count":1,"count":2}', b'{"count":NaN}', b"\xef\xbb\xbf{}"):
        with pytest.raises(ValueError):
            gate.load_json(data)


UID = "00000000000000000000000001"
SHA = "a" * 64
REF = {"path": "proof.json", "sha256": SHA, "bytes": 1}


def test_closed_schemas_reject_types_missing_and_future_refs():
    tree = {
        "schema_version": 1,
        "root_id": UID,
        "files": [{"path": "src.py", "sha256": SHA, "bytes": 0, "kind": "regular"}],
    }
    assert gate.validate_schema("tree", tree) == tree
    for mutation in ("extra", "bool", "negative", "missing"):
        bad = copy.deepcopy(tree)
        if mutation == "extra":
            bad["root_receipt_ref"] = REF
        if mutation == "bool":
            bad["schema_version"] = True
        if mutation == "negative":
            bad["files"][0]["bytes"] = -1
        if mutation == "missing":
            del bad["root_id"]
        with pytest.raises(ValueError):
            gate.validate_schema("tree", bad)
    policy = {
        "line_min": 80,
        "branch_required": True,
        "branch_min": 80,
        "scope": "whole_changed_current",
        "rounding": "none",
        "exceptions": [],
    }
    assert gate.validate_schema("policy", policy) == policy
    for field, value in [
        ("line_min", 79),
        ("branch_required", 1),
        ("branch_min", None),
    ]:
        bad = dict(policy, **{field: value})
        with pytest.raises(ValueError):
            gate.validate_schema("policy", bad)
    counter = {
        "covered": 79999,
        "total": 100000,
        "percent": {"numerator": 7999900, "denominator": 100000},
        "minimum": 80,
    }
    assert gate.validate_schema("counter", counter) == counter
    for field, value in [("covered", True), ("total", 0), ("covered", 100001)]:
        with pytest.raises(ValueError):
            gate.validate_schema("counter", dict(counter, **{field: value}))


def emit(root, path, value, raw=False):
    data = (
        value
        if raw
        else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def test_full_tree_hidden_collisions_and_artifact_closure(tmp_path):
    emit(tmp_path, "candidate/src.py", b"x=1\n", True)
    emit(tmp_path, "candidate/.hidden", b"x", True)
    assert [x["path"] for x in gate.scan_tree(tmp_path / "candidate")] == [
        ".hidden",
        "src.py",
    ]
    leaf = emit(tmp_path, "leaf.txt", b"FULLBYTES\r\n", True)
    parent = emit(tmp_path, "parent.json", {"nested": [leaf]})
    evidence = gate.Evidence(tmp_path)
    assert evidence.artifact(parent) == (tmp_path / "parent.json").read_bytes()
    (tmp_path / "leaf.txt").write_bytes(b"FULLBYTES\n")
    with pytest.raises(ValueError, match="SOURCE_MISMATCH"):
        evidence.artifact(parent)
    collision = {
        "schema_version": 1,
        "root_id": UID,
        "files": [
            {"path": p, "sha256": SHA, "bytes": 1, "kind": "regular"}
            for p in ("SRC.py", "src.py")
        ],
    }
    with pytest.raises(ValueError, match="COLLISION"):
        gate.validate_schema("tree", collision)
    with pytest.raises(ValueError):
        evidence.artifact(dict(leaf, path="../outside"))


def test_dag_rejects_cycle_before_hash_and_hardlinks(tmp_path):
    a = {"path": "a.json", "sha256": SHA, "bytes": 1}
    b = {"path": "b.json", "sha256": SHA, "bytes": 1}
    emit(tmp_path, "a.json", {"ref": b})
    emit(tmp_path, "b.json", {"ref": a})
    with pytest.raises(ValueError, match="CYCLE"):
        gate.Evidence(tmp_path).artifact(a)
    import os

    emit(tmp_path, "source.py", b"x", True)
    os.link(tmp_path / "source.py", tmp_path / "alias.py")
    with pytest.raises(ValueError, match="HARDLINK"):
        gate.scan_tree(tmp_path)


def python_raw(covered=80, total=100, branches=100, branch_covered=80):
    return {
        "meta": {
            "format": 3,
            "version": "7.13.1",
            "timestamp": "2026-10-12T13:00:00",
            "branch_coverage": True,
        },
        "files": {
            "src.py": {
                "executed_lines": list(range(1, covered + 1)),
                "missing_lines": list(range(covered + 1, total + 1)),
                "excluded_lines": [],
                "summary": {
                    "num_statements": total,
                    "covered_lines": covered,
                    "missing_lines": total - covered,
                    "num_branches": branches,
                    "covered_branches": branch_covered,
                    "missing_branches": branches - branch_covered,
                    "percent_covered": 80,
                },
                "executed_branches": [[i, i + 1] for i in range(1, branch_covered + 1)],
                "missing_branches": [
                    [i, i + 1] for i in range(branch_covered + 1, branches + 1)
                ],
            }
        },
    }


@pytest.mark.parametrize(
    "covered,total,passed",
    [(70, 100, False), (100, 100, True), (79999, 100000, False), (80, 100, True)],
)
def test_python_whole_threshold_no_mean_or_rounding(covered, total, passed):
    result = gate.python_counts(python_raw(covered, total), "src.py", True)
    assert result["lines"]["covered"] == covered
    assert result["lines"]["total"] == total
    assert (100 * covered >= 80 * total) == passed
    assert result["statements"] == result["lines"]


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "empty",
        "excluded",
        "bool",
        "negative",
        "zero",
        "duplicate",
        "branch_off",
        "branch_low",
    ],
)
def test_python_invalid_or_missing_and_branches(mutation):
    raw = python_raw()
    f = raw["files"]["src.py"]
    if mutation == "missing":
        raw["files"] = {"other.py": f}
    if mutation == "empty":
        raw["files"] = {}
    if mutation == "excluded":
        f["excluded_lines"] = [101]
    if mutation == "bool":
        f["executed_lines"][0] = True
    if mutation == "negative":
        f["summary"]["num_statements"] = -1
    if mutation == "zero":
        raw = python_raw(0, 0)
    if mutation == "duplicate":
        f["executed_lines"].append(1)
    if mutation == "branch_off":
        raw["meta"]["branch_coverage"] = False
    if mutation == "branch_low":
        raw = python_raw(100, 100, 100, 70)
    if mutation == "branch_low":
        r = gate.python_counts(raw, "src.py", True)
        assert 100 * r["branches"]["covered"] < 80 * r["branches"]["total"]
    else:
        with pytest.raises(ValueError):
            gate.python_counts(raw, "src.py", True)


def js_raw():
    loc = lambda line: {
        "start": {"line": line, "column": 0},
        "end": {"line": line, "column": 1},
    }
    return {
        "src.ts": {
            "path": "src.ts",
            "statementMap": {str(i): loc(1) for i in range(100)},
            "s": {str(i): int(i < 70) for i in range(100)},
            "fnMap": {},
            "f": {},
            "branchMap": {
                "0": {"type": "if", "loc": loc(1), "locations": [loc(1), loc(1)]}
            },
            "b": {"0": [1, 1]},
        }
    }


def test_istanbul_statements_whole_lines_and_map_ids():
    raw = js_raw()
    result = gate.istanbul_counts(raw, "src.ts", True)
    assert result["lines"]["covered"] == result["lines"]["total"] == 1
    assert (
        result["statements"]["covered"] == 70 and result["statements"]["total"] == 100
    )
    for mutation in ("id", "bool", "branch_size", "range"):
        bad = copy.deepcopy(raw)
        f = bad["src.ts"]
        if mutation == "id":
            del f["s"]["1"]
        if mutation == "bool":
            f["s"]["1"] = True
        if mutation == "branch_size":
            f["b"]["0"] = [1]
        if mutation == "range":
            f["statementMap"]["1"]["start"]["line"] = 0
        with pytest.raises(ValueError):
            gate.istanbul_counts(bad, "src.ts", True)


def synthetic_case(
    root,
    files=None,
    production=True,
    combine=False,
    stack="python",
    exception_class="prose",
):
    """Fixtures sintéticas: ninguna autorización ni ejecución oficial."""
    uid = lambda n: str(n).zfill(26)
    phase, base_id, candidate_id, runner_id = map(uid, (1, 2, 3, 4))
    files = files or {"src.py": (b"x=0\n", b"x=1\n" * 200)}
    refs = {}
    put = lambda name, value, raw=False: refs.setdefault(
        name, emit(root, name, value, raw)
    )
    for path, (old, new) in files.items():
        if old is not None:
            put("base/" + path, old, True)
        if new is not None:
            put("candidate/" + path, new, True)
    for tree in ("base", "candidate"):
        (root / tree).mkdir(exist_ok=True)
    tree_rows = lambda tree: [
        {
            "path": p,
            "sha256": refs[tree + "/" + p]["sha256"],
            "bytes": refs[tree + "/" + p]["bytes"],
            "kind": "regular",
        }
        for p in sorted(files)
        if tree + "/" + p in refs
    ]
    for name, rid in [("base", base_id), ("candidate", candidate_id)]:
        put(
            name + "-tree.json",
            {"schema_version": 1, "root_id": rid, "files": tree_rows(name)},
        )
    put("contract.txt", b"SYNTHETIC CONTRACT", True)
    put("delegation.txt", b"SYNTHETIC NOT ROOT AUTHORITY", True)
    put("tool.bin", b"SYNTHETIC TOOL", True)
    put("lock.json", {"synthetic": True})
    put("proof.txt", b"SYNTHETIC CLASSIFICATION", True)
    entries = [
        {
            "path": p,
            "classification": (
                "deleted_production"
                if pair[1] is None and production
                else "production"
                if production
                else exception_class
            ),
            "reason": "SYNTHETIC",
            "proof_refs": [refs["proof.txt"]],
        }
        for p, pair in files.items()
    ]
    put(
        "K.json",
        {
            "schema_version": 1,
            "phase_id": phase,
            "base_inventory_ref": refs["base-tree.json"],
            "candidate_inventory_ref": refs["candidate-tree.json"],
            "entries": entries,
        },
    )
    plan_entries = (
        [
            {
                "runner_id": runner_id,
                "kind": "runner",
                "stack": stack,
                "package": "pkg",
                "tool_ref": refs["tool.bin"],
                "input_runner_ids": [],
            }
        ]
        if production and any(pair[1] is not None for pair in files.values())
        else []
    )
    if combine:
        plan_entries.append(
            {
                "runner_id": uid(9),
                "kind": "combine",
                "stack": "python",
                "package": "pkg",
                "tool_ref": refs["tool.bin"],
                "input_runner_ids": [runner_id],
            }
        )
    put("Plan.json", {"schema_version": 1, "phase_id": phase, "entries": plan_entries})
    policy = {
        "line_min": 80,
        "branch_required": True,
        "branch_min": 80,
        "scope": "whole_changed_current",
        "rounding": "none",
        "exceptions": [],
    }
    put("config.txt", b"[coverage:run]\nbranch=True\n", True)
    put(
        "A.json",
        {
            "schema_version": 1,
            "approval_id": uid(5),
            "phase_id": phase,
            "created_at": "2026-10-12T13:00:00Z",
            "contract_ref": refs["contract.txt"],
            "base_inventory_ref": refs["base-tree.json"],
            "candidate_inventory_ref": refs["candidate-tree.json"],
            "classification_ref": refs["K.json"],
            "runner_plan_ref": refs["Plan.json"],
            "policy": policy,
            "runner_config_refs": [refs["config.txt"]],
            "tool_lock_refs": [refs["lock.json"]],
            "root_authorization_ref": refs["delegation.txt"],
        },
    )
    put(
        "F.json",
        {
            "schema_version": 1,
            "phase_id": phase,
            "created_at": "2026-10-12T13:00:00Z",
            "contract_ref": refs["contract.txt"],
            "base_inventory_ref": refs["base-tree.json"],
            "candidate_inventory_ref": refs["candidate-tree.json"],
            "classification_ref": refs["K.json"],
            "runner_config_refs": [refs["config.txt"]],
            "tool_lock_refs": [refs["lock.json"]],
            "root_ratification_ref": refs["A.json"],
        },
    )
    rows = []
    changes = []
    exceptions = []
    for p, (old, new) in files.items():
        get = lambda tree, key, p=p: refs.get(tree + "/" + p, {}).get(key)
        classification = "production" if production else exception_class
        exception = None
        if new is None or not production:
            exc = {
                "path": p,
                "classification": "deleted_production"
                if production
                else exception_class,
                "reason": "SYNTHETIC",
                "proof_ref": refs["proof.txt"],
                "root_approval_ref": refs["A.json"],
            }
            exception = put("exception-" + str(len(exceptions)) + ".json", exc)
            exceptions.append(exc)
        rows.append(
            {
                "path": p,
                "base_sha256": get("base", "sha256"),
                "candidate_sha256": get("candidate", "sha256"),
                "base_bytes": get("base", "bytes"),
                "candidate_bytes": get("candidate", "bytes"),
                "stack": stack if production and new is not None else "none",
                "package": "pkg" if production and new is not None else None,
                "classification": classification,
                "runner_id": runner_id if production and new is not None else None,
                "exception_ref": exception,
            }
        )
        kind = "added" if old is None else "deleted" if new is None else "modified"
        changes.append(
            {
                "kind": kind,
                "old_path": p if old is not None else None,
                "new_path": p if new is not None else None,
                "old_sha256": get("base", "sha256"),
                "new_sha256": get("candidate", "sha256"),
            }
        )
    root_ref = lambda tree, rid: {
        "root_id": rid,
        "path": tree,
        "tree_sha256": refs[tree + "-tree.json"]["sha256"],
        "inventory_ref": refs[tree + "-tree.json"],
    }
    inventory = {
        "schema_version": 1,
        "phase_id": phase,
        "created_at": "2026-10-12T13:00:00Z",
        "base_root_ref": root_ref("base", base_id),
        "candidate_root_ref": root_ref("candidate", candidate_id),
        "source_freeze_ref": refs["F.json"],
        "policy": dict(policy, exceptions=exceptions),
        "files": rows,
        "changes": changes,
    }
    put("I.json", inventory)
    return inventory, refs


def test_inventory_union_added_deleted_hidden_rename_stale(tmp_path):
    files = {
        "src.py": (b"x=0\n", b"x=1\n"),
        ".hidden.py": (None, b"y=1\n"),
        "old.py": (b"z=0\n", None),
        "new.py": (None, b"z=0\n"),
    }
    inventory, refs = synthetic_case(tmp_path, files)
    inventory["changes"] = [
        c
        for c in inventory["changes"]
        if c["old_path"] != "old.py" and c["new_path"] != "new.py"
    ] + [
        {
            "kind": "renamed",
            "old_path": "old.py",
            "new_path": "new.py",
            "old_sha256": refs["base/old.py"]["sha256"],
            "new_sha256": refs["candidate/new.py"]["sha256"],
        }
    ]
    evidence = gate.Evidence(tmp_path)
    result = gate.inspect_inventory(evidence, inventory)
    assert result["current"] == {".hidden.py", "src.py", "new.py"}
    bad = copy.deepcopy(inventory)
    bad["files"] = bad["files"][1:]
    with pytest.raises(ValueError):
        gate.inspect_inventory(evidence, bad)
    emit(tmp_path, "candidate/untracked.py", b"new=1\n", True)
    with pytest.raises(ValueError, match="SOURCE_MISMATCH"):
        gate.inspect_inventory(evidence, inventory)


def test_inventory_disguised_production_and_duplicate_runner_plan(tmp_path):
    inventory, _refs = synthetic_case(tmp_path)
    inventory["files"][0]["classification"] = "prose"
    with pytest.raises(ValueError):
        gate.inspect_inventory(gate.Evidence(tmp_path), inventory)


def synthetic_reports(root, inventory, refs, raw=None):
    raw = raw or python_raw(100, 100)
    put = lambda name, value, raw=False: refs.setdefault(
        name, emit(root, name, value, raw)
    )
    uid = lambda n: str(n).zfill(26)
    phase = inventory["phase_id"]
    rid = uid(4)
    for name in ("stdout.txt", "stderr.txt", "custody.txt"):
        put(name, b"SYNTHETIC NOT ROOT OBSERVATION\n", True)

    def execution(name, kind, upstream, outputs):
        return put(
            name,
            {
                "schema_version": 1,
                "execution_id": uid(100 + len(refs)),
                "phase_id": phase,
                "kind": kind,
                "runner_id": None if kind == "root_inventory" else rid,
                "upstream_refs": upstream,
                "argv": ["SYNTHETIC", kind],
                "cwd": "candidate",
                "environment": [],
                "started_at": "2026-10-12T13:00:00Z",
                "finished_at": "2026-10-12T13:00:01Z",
                "exit_code": 0,
                "stdout_ref": refs["stdout.txt"],
                "stderr_ref": refs["stderr.txt"],
                "tool_ref": refs["tool.bin"],
                "observed_source_inventory_refs": [
                    refs["base-tree.json"],
                    refs["candidate-tree.json"],
                ],
                "output_refs": outputs,
                "custody_ref": refs["custody.txt"],
            },
        )

    execution(
        "E0.json",
        "root_inventory",
        [refs["I.json"], refs["F.json"], refs["A.json"]],
        [],
    )
    plan = json.loads((root / "Plan.json").read_bytes())
    put(
        "R.json",
        {
            "schema_version": 1,
            "phase_id": phase,
            "created_at": "2026-10-12T13:00:01Z",
            "base_root_id": inventory["base_root_ref"]["root_id"],
            "candidate_root_id": inventory["candidate_root_ref"]["root_id"],
            "base_tree_sha256": inventory["base_root_ref"]["tree_sha256"],
            "candidate_tree_sha256": inventory["candidate_root_ref"]["tree_sha256"],
            "inventory_sha256": refs["I.json"]["sha256"],
            "source_freeze_sha256": refs["F.json"]["sha256"],
            "approved_classification_ref": refs["K.json"],
            "namespace": "case",
            "runner_ids": [r["runner_id"] for r in plan["entries"]],
            "root_execution_ref": refs["E0.json"],
        },
    )
    put("raw.json", raw)
    put("effective-raw.txt", b"SYNTHETIC OFFICIAL CONFIG\n", True)
    config = {
        "schema_version": 1,
        "runner_id": rid,
        "source_roots": [".root"],
        "branch": True,
        "include_patterns": [],
        "omit_patterns": [],
        "exclude_lines": [],
        "ignore_patterns": [],
        "test_nodes": ["test_synthetic"],
        "config_refs": [refs["config.txt"]],
        "raw_effective_ref": refs["effective-raw.txt"],
    }
    source_paths = [
        r["path"] for r in inventory["files"] if r["candidate_sha256"] is not None
    ]
    config["source_roots"] = source_paths or ["empty"]
    put("effective.json", config)
    put(
        "source.json",
        {
            "schema_version": 1,
            "runner_id": rid,
            "files": [
                {
                    "path": path,
                    "sha256": refs["candidate/" + path]["sha256"],
                    "bytes": refs["candidate/" + path]["bytes"],
                    "raw_key": path,
                }
                for path in sorted(source_paths)
            ],
        },
    )
    execution(
        "Ej.json",
        "runner",
        [refs["R.json"], refs["I.json"], refs["F.json"]],
        [refs["raw.json"], refs["effective.json"], refs["source.json"]],
    )
    e = json.loads((root / "Ej.json").read_bytes())
    put(
        "Cj.json",
        {
            "schema_version": 1,
            "runner_id": rid,
            "phase_id": phase,
            "argv": e["argv"],
            "cwd": e["cwd"],
            "environment": e["environment"],
            "started_at": e["started_at"],
            "finished_at": e["finished_at"],
            "exit_code": 0,
            "stdout_ref": e["stdout_ref"],
            "stderr_ref": e["stderr_ref"],
            "tool_ref": refs["tool.bin"],
            "config_sha256": refs["effective.json"]["sha256"],
            "inventory_sha256": refs["I.json"]["sha256"],
            "source_manifest_sha256": refs["source.json"]["sha256"],
            "report_sha256": refs["raw.json"]["sha256"],
            "root_execution_receipt_ref": refs["Ej.json"],
        },
    )
    runner = {
        "runner_id": rid,
        "stack": inventory["files"][0]["stack"] if source_paths else "python",
        "package": "pkg",
        "platform": "synthetic_cpu",
        "tool": {
            "name": "coverage.py"
            if inventory["files"][0]["stack"] == "python"
            else "vitest",
            "version": "7.13.1"
            if inventory["files"][0]["stack"] == "python"
            else "3.0.0",
            "executable_ref": refs["tool.bin"],
            "lock_refs": [refs["lock.json"]],
        },
        "receipt_ref": refs["Cj.json"],
        "raw_report_ref": refs["raw.json"],
        "summary_ref": None
        if inventory["files"][0]["stack"] == "python"
        else put("summary.json", {"synthetic": True}),
        "config_refs": [refs["config.txt"]],
        "effective_config_ref": refs["effective.json"],
        "source_manifest_ref": refs["source.json"],
        "source_maps": [],
        "test_result_refs": [],
    }
    reports = {
        "schema_version": 1,
        "phase_id": phase,
        "inventory_sha256": refs["I.json"]["sha256"],
        "source_freeze_sha256": refs["F.json"]["sha256"],
        "root_receipt_ref": refs["R.json"],
        "runner_records": [runner] if plan["entries"] else [],
        "combined_records": [],
    }
    put("P.json", reports)
    put("helper.json", {"synthetic": True, "average": 85})
    return reports


def run_gate(root, helper_exit=0, observation=None):
    return gate.evaluate(
        root / "I.json",
        root / "P.json",
        root / "helper.json",
        helper_exit,
        observation=observation,
    )


def test_perfect_synthetic_never_grants_root_authority(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)
    result = run_gate(tmp_path)
    assert result["exit_code"] == 2 and result["verdict"] == "pending"
    assert "ROOT_CUSTODY_MISSING" in [e["code"] for e in result["errors"]]


def test_embedded_main_uses_only_caller_memory_factory(tmp_path, monkeypatch, capsys):
    import runpy
    import sys

    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(gate.__file__),
            "--inventory",
            str(tmp_path / "I.json"),
            "--reports",
            str(tmp_path / "P.json"),
            "--helper",
            str(tmp_path / "helper.json"),
            "--helper-exit",
            "0",
            "--min",
            "80",
            "--json",
        ],
    )
    received = []

    def factory(constructor):
        received.append(constructor)

        class EmbeddedSyntheticObserver(SyntheticObserver):
            def capture(self, expected):
                captured = super().capture(expected)
                return constructor(captured.bindings, captured.artifact_bytes)

        return EmbeddedSyntheticObserver(tmp_path)

    with pytest.raises(SystemExit) as embedded:
        runpy.run_path(
            gate.__file__,
            run_name="__main__",
            init_globals={"_root_observer_factory": factory},
        )
    result = json.loads(capsys.readouterr().out)
    assert embedded.value.code == result["exit_code"] == 0
    assert len(received) == 1 and received[0] is not gate.ObservedEvidence
    with pytest.raises(SystemExit) as standalone:
        runpy.run_path(gate.__file__, run_name="__main__")
    result = json.loads(capsys.readouterr().out)
    assert standalone.value.code == result["exit_code"] == 2
    assert "ROOT_CUSTODY_MISSING" in [e["code"] for e in result["errors"]]


def test_invalid_report_schema_pending_but_binding_mismatch_fail(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    reports = synthetic_reports(tmp_path, inventory, refs)
    emit(tmp_path, "P.json", {"schema_version": 1})
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 2
    assert "CLOSED_SCHEMA" in [e["code"] for e in result["errors"]]
    reports["phase_id"] = "00000000000000000000000002"
    emit(tmp_path, "P.json", reports)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 1
    assert "REPORT_BINDING" in [e["code"] for e in result["errors"]]


def replace_synthetic_raw(root, refs, reports, raw):
    """Rebind synthetic DAG so malformed input, rather than stale SHA, is tested."""
    raw_ref = emit(root, "raw.json", raw)
    execution = json.loads((root / "Ej.json").read_bytes())
    execution["output_refs"][0] = raw_ref
    execution_ref = emit(root, "Ej.json", execution)
    receipt = json.loads((root / "Cj.json").read_bytes())
    receipt.update(
        report_sha256=raw_ref["sha256"], root_execution_receipt_ref=execution_ref
    )
    receipt_ref = emit(root, "Cj.json", receipt)
    reports["runner_records"][0].update(raw_report_ref=raw_ref, receipt_ref=receipt_ref)
    emit(root, "P.json", reports)


@pytest.mark.parametrize("malformation", ["raw_array", "meta_array"])
def test_raw_header_malformed_emits_pending_json(tmp_path, capsys, malformation):
    inventory, refs = synthetic_case(tmp_path)
    reports = synthetic_reports(tmp_path, inventory, refs)
    raw = [] if malformation == "raw_array" else dict(python_raw(), meta=[])
    replace_synthetic_raw(tmp_path, refs, reports, raw)
    code = gate.main(
        [
            "--inventory",
            str(tmp_path / "I.json"),
            "--reports",
            str(tmp_path / "P.json"),
            "--helper",
            str(tmp_path / "helper.json"),
            "--helper-exit",
            "0",
            "--min",
            "80",
            "--json",
        ],
        observation=SyntheticObserver(tmp_path),
    )
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert code == result["exit_code"] == 2
    assert "RAW_INVALID" in [e["code"] for e in result["errors"]]
    assert "Traceback" not in output.err


def test_map_nonstring_content_emits_fail_json(tmp_path, capsys):
    _inventory, _refs, reports = mapped_synthetic_case(tmp_path)
    mapping = reports["runner_records"][0]["source_maps"][0]
    source_map = json.loads((tmp_path / "source-map.json").read_bytes())
    source_map["sourcesContent"] = [1]
    mapping["map_ref"] = emit(tmp_path, "source-map.json", source_map)
    emit(tmp_path, "P.json", reports)
    code = gate.main(
        [
            "--inventory",
            str(tmp_path / "I.json"),
            "--reports",
            str(tmp_path / "P.json"),
            "--helper",
            str(tmp_path / "helper.json"),
            "--helper-exit",
            "0",
            "--min",
            "80",
            "--json",
        ],
        observation=SyntheticObserver(tmp_path),
    )
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert code == result["exit_code"] == 1
    assert "SOURCE_MAP_INVALID" in [e["code"] for e in result["errors"]]
    assert "Traceback" not in output.err


@pytest.mark.parametrize("reverse", [False, True])
def test_execution_fractional_utc_order(tmp_path, reverse):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)
    execution = json.loads((tmp_path / "Ej.json").read_bytes())
    first, last = "2026-10-12T13:00:00Z", "2026-10-12T13:00:00.500Z"
    execution.update(
        started_at=last if reverse else first, finished_at=first if reverse else last
    )
    gate.validate_schema("execution", execution)
    if reverse:
        with pytest.raises(ValueError, match="EXECUTION_TIMES"):
            gate.inspect_execution(
                execution,
                "runner",
                execution["runner_id"],
                inventory,
                gate.Evidence(tmp_path),
            )
    else:
        gate.inspect_execution(
            execution,
            "runner",
            execution["runner_id"],
            inventory,
            gate.Evidence(tmp_path),
        )


def test_unknown_istanbul_reader_is_pending(tmp_path):
    _inventory, _refs, reports = mapped_synthetic_case(tmp_path)
    record = reports["runner_records"][0]
    record["tool"]["version"] = "9999.0.0"
    emit(tmp_path, "P.json", reports)
    observer = SyntheticObserver(tmp_path)
    observer.observe_mapping = observer.capture
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == 2
    assert "TOOL_FORMAT_UNKNOWN" in [e["code"] for e in result["errors"]]


def test_execution_submicrosecond_reversal_rejected(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)
    execution = json.loads((tmp_path / "Ej.json").read_bytes())
    execution.update(
        started_at="2026-10-12T13:00:00.0000001Z",
        finished_at="2026-10-12T13:00:00Z",
    )
    gate.validate_schema("execution", execution)
    with pytest.raises(ValueError, match="EXECUTION_TIMES"):
        gate.inspect_execution(
            execution,
            "runner",
            execution["runner_id"],
            inventory,
            gate.Evidence(tmp_path),
        )


@pytest.mark.parametrize("reverse", [False, True])
def test_execution_exact_fraction_order_and_equivalent_precision(tmp_path, reverse):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)
    execution = json.loads((tmp_path / "Ej.json").read_bytes())
    execution.update(
        started_at="2026-10-12T13:00:00.1234567Z"
        if reverse
        else "2026-10-12T13:00:00.5Z",
        finished_at="2026-10-12T13:00:00.1234566Z"
        if reverse
        else "2026-10-12T13:00:00.500Z",
    )
    gate.validate_schema("execution", execution)
    if reverse:
        with pytest.raises(ValueError, match="EXECUTION_TIMES"):
            gate.inspect_execution(
                execution,
                "runner",
                execution["runner_id"],
                inventory,
                gate.Evidence(tmp_path),
            )
    else:
        gate.inspect_execution(
            execution,
            "runner",
            execution["runner_id"],
            inventory,
            gate.Evidence(tmp_path),
        )


@pytest.mark.parametrize(
    "kind",
    [
        "low",
        "rounded",
        "missing",
        "empty",
        "helper1",
        "helper2",
        "raw_absent",
        "receipt_absent",
        "stale_raw",
        "omit",
    ],
)
def test_phase_fail_pending_precedence_and_explicit_rows(tmp_path, kind):
    inventory, refs = synthetic_case(
        tmp_path,
        files={"src.py": (b"x=0\n", b"x=1\n" * 100001)} if kind == "rounded" else None,
    )
    raw = (
        python_raw(70, 100)
        if kind == "low"
        else python_raw(79999, 100000)
        if kind == "rounded"
        else python_raw(100, 100)
    )
    if kind == "missing":
        raw["files"] = {"other.py": raw["files"]["src.py"]}
    if kind == "empty":
        raw["files"] = {}
    synthetic_reports(tmp_path, inventory, refs, raw)
    if kind in ("raw_absent", "receipt_absent"):
        (tmp_path / ("raw.json" if kind == "raw_absent" else "Cj.json")).unlink()
    if kind == "stale_raw":
        (tmp_path / "raw.json").write_text("{}")
    if kind == "omit":
        cfg = json.loads((tmp_path / "effective.json").read_bytes())
        cfg["omit_patterns"] = ["src.py"]
        (tmp_path / "effective.json").write_text(json.dumps(cfg))
    result = run_gate(
        tmp_path, 1 if kind == "helper1" else 2 if kind == "helper2" else 0
    )
    expected = 2 if kind in ("helper2", "raw_absent", "receipt_absent") else 1
    assert result["exit_code"] == expected
    assert len(result["files"]) == 1
    if kind == "rounded":
        assert "BELOW_MINIMUM" in [e["code"] for e in result["errors"]]
        assert result["files"][0]["lines"]["covered"] == 79999
        assert result["files"][0]["lines"]["total"] == 100000
    if kind in ("missing", "empty"):
        assert result["missing"] == ["src.py"]


def test_phase_exact_eighty_boundary_passes(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs, python_raw(80, 100, 100, 80))
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 0 and result["verdict"] == "pass"
    assert result["files"][0]["status"] == "pass"
    assert result["files"][0]["lines"] == {
        "covered": 80,
        "total": 100,
        "percent": {"numerator": 8000, "denominator": 100},
        "minimum": 80,
    }
    assert not result["errors"]


class SyntheticObserver:
    """Seam UNIT/SYNTHETIC: no receipt real, nunca usado por CLI productivo."""

    def __init__(self, root):
        self.evidence = gate.Evidence(root)

    def observe_preapproval(self, expected):
        return self.capture(expected)

    def observe_execution(self, expected):
        return self.capture(expected)

    def capture(self, expected):
        return gate.ObservedEvidence(
            copy.deepcopy(expected),
            {
                r["path"]: self.evidence.artifact(r)
                for r in gate.artifact_refs(expected)
            },
        )


def test_cli_literal_flags_json_exit_and_nonproduction_exception(tmp_path, capsys):
    inventory, refs = synthetic_case(tmp_path, production=False)
    synthetic_reports(tmp_path, inventory, refs)
    (tmp_path / "helper.json").unlink()
    argv = [
        "--inventory",
        str(tmp_path / "I.json"),
        "--reports",
        str(tmp_path / "P.json"),
        "--helper",
        str(tmp_path / "helper.json"),
        "--helper-exit",
        "2",
        "--min",
        "80",
        "--json",
    ]
    code = gate.main(argv, observation=SyntheticObserver(tmp_path))
    result = json.loads(capsys.readouterr().out)
    assert code == result["exit_code"] == 0 and result["applies"] is False
    assert (
        result["files"][0]["status"] == "excepted"
        and result["files"][0]["lines"] is None
    )
    code = gate.main(argv[:-3] + ["--min", "79", "--json"])
    result = json.loads(capsys.readouterr().out)
    assert code == result["exit_code"] == 1


def test_branch_zero_requires_official_observed_proof(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    reports = synthetic_reports(tmp_path, inventory, refs, python_raw(100, 100, 0, 0))
    observer = SyntheticObserver(tmp_path)
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == 2 and result["files"][0]["branches"] is None
    proof = emit(
        tmp_path, "branch-proof.txt", b"SYNTHETIC exit_counts={} whole source\n", True
    )
    e = json.loads((tmp_path / "Ej.json").read_bytes())
    e["output_refs"].append(proof)
    refs["Ej.json"] = emit(tmp_path, "Ej.json", e)
    c = json.loads((tmp_path / "Cj.json").read_bytes())
    c["root_execution_receipt_ref"] = refs["Ej.json"]
    refs["Cj.json"] = emit(tmp_path, "Cj.json", c)
    reports["runner_records"][0]["receipt_ref"] = refs["Cj.json"]
    emit(tmp_path, "P.json", reports)
    observer.branch_proof = lambda expected: gate.ObservedEvidence(
        dict(expected, proof_ref=proof),
        dict(
            observer.capture(expected).artifact_bytes,
            **{"branch-proof.txt": (tmp_path / "branch-proof.txt").read_bytes()},
        ),
    )
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == 0
    assert (
        result["files"][0]["branch_state"] == "not_applicable"
        and result["files"][0]["branches"] is None
        and result["files"][0]["branch_na_proof_ref"] == proof
    )


@pytest.mark.parametrize("prefix", ["candidate", "absolute", "outside"])
def test_python_raw_pairing_exact_declared_root_prefix(tmp_path, prefix):
    inventory, refs = synthetic_case(tmp_path)
    reports = synthetic_reports(tmp_path, inventory, refs)
    key = (
        str(tmp_path / "candidate/src.py")
        if prefix == "absolute"
        else prefix + "/src.py"
    )
    raw = python_raw(100, 100)
    raw["files"][key] = raw["files"].pop("src.py")
    rawref = emit(tmp_path, "raw.json", raw)
    source = json.loads((tmp_path / "source.json").read_bytes())
    source["files"][0]["raw_key"] = key
    srcref = emit(tmp_path, "source.json", source)
    e = json.loads((tmp_path / "Ej.json").read_bytes())
    e["output_refs"] = [rawref, refs["effective.json"], srcref]
    eref = emit(tmp_path, "Ej.json", e)
    c = json.loads((tmp_path / "Cj.json").read_bytes())
    c.update(
        report_sha256=rawref["sha256"],
        source_manifest_sha256=srcref["sha256"],
        root_execution_receipt_ref=eref,
    )
    cref = emit(tmp_path, "Cj.json", c)
    reports["runner_records"][0].update(
        raw_report_ref=rawref, source_manifest_ref=srcref, receipt_ref=cref
    )
    emit(tmp_path, "P.json", reports)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == (1 if prefix == "outside" else 0)


@pytest.mark.parametrize("mutation", ["unknown_minor", "float_format"])
def test_python_versioned_reader_never_guesses_formats(mutation):
    raw = python_raw()
    if mutation == "unknown_minor":
        raw["meta"]["version"] = "7.999.0"
    else:
        raw["meta"]["format"] = 3.0
    with pytest.raises((ValueError, LookupError)):
        gate.python_counts(raw, "src.py", True)


def test_python_native_separator_pairing_is_exact_and_cwd_bound(tmp_path):
    from pathlib import Path

    path = "src/fixture.py"
    key = str(Path(path))
    inventory, refs = synthetic_case(tmp_path, files={path: (b"x=0\n", b"x=1\n" * 200)})
    raw = python_raw(100, 100)
    raw["files"][key] = raw["files"].pop("src.py")
    reports = synthetic_reports(tmp_path, inventory, refs, raw)
    source = json.loads((tmp_path / "source.json").read_bytes())
    source["files"][0]["raw_key"] = key
    srcref = emit(tmp_path, "source.json", source)
    e = json.loads((tmp_path / "Ej.json").read_bytes())
    e["output_refs"] = [refs["raw.json"], refs["effective.json"], srcref]
    eref = emit(tmp_path, "Ej.json", e)
    c = json.loads((tmp_path / "Cj.json").read_bytes())
    c.update(source_manifest_sha256=srcref["sha256"], root_execution_receipt_ref=eref)
    cref = emit(tmp_path, "Cj.json", c)
    reports["runner_records"][0].update(source_manifest_ref=srcref, receipt_ref=cref)
    emit(tmp_path, "P.json", reports)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 0
    assert result["files"][0]["path"] == path and result["files"][0]["raw_key"] == key
    if key != path:
        e["cwd"] = "elsewhere"
        eref = emit(tmp_path, "Ej.json", e)
        c.update(cwd="elsewhere", root_execution_receipt_ref=eref)
        cref = emit(tmp_path, "Cj.json", c)
        reports["runner_records"][0]["receipt_ref"] = cref
        emit(tmp_path, "P.json", reports)
        result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
        assert result["exit_code"] == 1
        assert "RAW_ROOT_PREFIX_BINDING" in {x["code"] for x in result["errors"]}


def test_official_combination_observed_not_local_average(tmp_path):
    inventory, refs = synthetic_case(tmp_path, combine=True)
    reports = synthetic_reports(tmp_path, inventory, refs, python_raw(70, 100))
    rid = "00000000000000000000000009"
    raw = emit(tmp_path, "combined-raw.json", python_raw(100, 100))
    cfg = json.loads((tmp_path / "effective.json").read_bytes())
    cfg["runner_id"] = rid
    cfgref = emit(tmp_path, "combined-config.json", cfg)
    source = json.loads((tmp_path / "source.json").read_bytes())
    source["runner_id"] = rid
    srcref = emit(tmp_path, "combined-source.json", source)
    e = json.loads((tmp_path / "Ej.json").read_bytes())
    e.update(
        execution_id="00000000000000000000000199",
        runner_id=rid,
        kind="combine",
        upstream_refs=[
            refs["R.json"],
            refs["I.json"],
            refs["F.json"],
            refs["Cj.json"],
            refs["raw.json"],
        ],
        output_refs=[raw, cfgref, srcref],
    )
    eref = emit(tmp_path, "Ec.json", e)
    c = json.loads((tmp_path / "Cj.json").read_bytes())
    c.update(
        runner_id=rid,
        report_sha256=raw["sha256"],
        config_sha256=cfgref["sha256"],
        source_manifest_sha256=srcref["sha256"],
        root_execution_receipt_ref=eref,
    )
    cref = emit(tmp_path, "Cc.json", c)
    reports["combined_records"] = [
        {
            "combined_id": rid,
            "stack": "python",
            "input_runner_ids": ["00000000000000000000000004"],
            "tool_ref": refs["tool.bin"],
            "receipt_ref": cref,
            "raw_report_ref": raw,
            "source_manifest_ref": srcref,
        }
    ]
    emit(tmp_path, "P.json", reports)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 0
    assert result["files"][0]["lines"]["covered"] == 100
    assert result["files"][0]["runner_id"] == rid


@pytest.mark.parametrize("malformation", ["raw_array", "meta_array"])
def test_combined_raw_header_malformed_emits_pending_json(
    tmp_path, monkeypatch, capsys, malformation
):
    import runpy
    import sys

    # This baseline also proves the DAG reaches Combined before its only mutation.
    test_official_combination_observed_not_local_average(tmp_path)
    reports = json.loads((tmp_path / "P.json").read_bytes())
    raw = [] if malformation == "raw_array" else dict(python_raw(), meta=[])
    raw_ref = emit(tmp_path, "combined-raw.json", raw)
    execution = json.loads((tmp_path / "Ec.json").read_bytes())
    execution["output_refs"][0] = raw_ref
    execution_ref = emit(tmp_path, "Ec.json", execution)
    receipt = json.loads((tmp_path / "Cc.json").read_bytes())
    receipt.update(
        report_sha256=raw_ref["sha256"], root_execution_receipt_ref=execution_ref
    )
    receipt_ref = emit(tmp_path, "Cc.json", receipt)
    reports["combined_records"][0].update(
        raw_report_ref=raw_ref, receipt_ref=receipt_ref
    )
    emit(tmp_path, "P.json", reports)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(gate.__file__),
            "--inventory",
            str(tmp_path / "I.json"),
            "--reports",
            str(tmp_path / "P.json"),
            "--helper",
            str(tmp_path / "helper.json"),
            "--helper-exit",
            "0",
            "--min",
            "80",
            "--json",
        ],
    )

    def factory(constructor):
        class EmbeddedSyntheticObserver(SyntheticObserver):
            def capture(self, expected):
                captured = super().capture(expected)
                return constructor(captured.bindings, captured.artifact_bytes)

        return EmbeddedSyntheticObserver(tmp_path)

    with pytest.raises(SystemExit) as embedded:
        runpy.run_path(
            gate.__file__,
            run_name="__main__",
            init_globals={"_root_observer_factory": factory},
        )
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert embedded.value.code == result["exit_code"] == 2
    assert result["verdict"] == "pending"
    assert "RAW_INVALID" in [e["code"] for e in result["errors"]]
    assert output.err == ""


def test_raw_ranges_and_unrelated_map_cannot_cover_source(tmp_path):
    inventory, refs = synthetic_case(tmp_path, files={"src.py": (b"x=0\n", b"x=1\n")})
    synthetic_reports(tmp_path, inventory, refs)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 1
    assert "RAW_SOURCE_RANGE" in [e["code"] for e in result["errors"]]


@pytest.mark.parametrize(
    "mutation",
    ["version", "receipt_invalid", "raw_version_mismatch", "full_source_missing"],
)
def test_unknown_tool_invalid_receipt_and_full_source_scope(tmp_path, mutation):
    inventory, refs = synthetic_case(tmp_path)
    reports = synthetic_reports(tmp_path, inventory, refs)
    if mutation == "version":
        reports["runner_records"][0]["tool"]["version"] = "unknown"
        emit(tmp_path, "P.json", reports)
    elif mutation == "receipt_invalid":
        cref = emit(tmp_path, "Cj.json", {"schema_version": 1})
        reports["runner_records"][0]["receipt_ref"] = cref
        emit(tmp_path, "P.json", reports)
    elif mutation == "raw_version_mismatch":
        raw = python_raw(100, 100)
        raw["meta"]["version"] = "7.12.0"
        # rebind raw and receipt/observation outputs; association is valid, version is not
        new = emit(tmp_path, "raw.json", raw)
        e = json.loads((tmp_path / "Ej.json").read_bytes())
        e["output_refs"][0] = new
        eref = emit(tmp_path, "Ej.json", e)
        c = json.loads((tmp_path / "Cj.json").read_bytes())
        c.update(report_sha256=new["sha256"], root_execution_receipt_ref=eref)
        cref = emit(tmp_path, "Cj.json", c)
        reports["runner_records"][0].update(raw_report_ref=new, receipt_ref=cref)
        emit(tmp_path, "P.json", reports)
    else:
        source = json.loads((tmp_path / "source.json").read_bytes())
        source["files"] = []
        sref = emit(tmp_path, "source.json", source)
        reports["runner_records"][0]["source_manifest_ref"] = sref
        emit(tmp_path, "P.json", reports)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == (
        2 if mutation in ("version", "receipt_invalid") else 1
    )


@pytest.mark.parametrize(
    "ref",
    [
        dict(REF, path=""),
        dict(REF, path="a/../b"),
        dict(REF, bytes=True),
        dict(REF, bytes=2**63),
        dict(REF, sha256="A" * 64),
        dict(REF, sha256=3),
        dict(REF, extra=1),
    ],
)
def test_artifact_schema_boundaries(ref):
    with pytest.raises(ValueError):
        gate.validate_schema("artifact", ref)


def test_schema_collection_nullable_and_exact_large_counter():
    assert gate.counter(2**63 - 1, 2**63 - 1)["percent"]["numerator"] == 100 * (
        2**63 - 1
    )
    tree = {"schema_version": 1, "root_id": UID, "files": []}
    for field, value in [
        ("files", {}),
        ("files", [0]),
        ("root_id", "Z" * 26),
        ("root_id", False),
        ("schema_version", 1.0),
    ]:
        with pytest.raises(ValueError):
            gate.validate_schema("tree", dict(tree, **{field: value}))
    with pytest.raises(ValueError):
        gate.validate_schema(
            "plan", {"schema_version": 1, "phase_id": UID, "entries": [{}] * 100001}
        )
    with pytest.raises(ValueError, match="PATH_ORDER"):
        gate.validate_schema(
            "tree",
            dict(
                tree,
                files=[
                    {"path": p, "sha256": SHA, "bytes": 1, "kind": "regular"}
                    for p in ("z", "a")
                ],
            ),
        )
    policy = {
        "line_min": 80,
        "branch_required": False,
        "branch_min": None,
        "scope": "whole_changed_current",
        "rounding": "none",
        "exceptions": [],
    }
    assert gate.validate_schema("policy", policy) == policy
    assert gate.python_counts(python_raw(80, 100), "src.py", False)["branches"] is None
    assert gate.istanbul_counts(js_raw(), "src.ts", False)["branches"] is None


@pytest.mark.parametrize(
    "mutation",
    [
        "format",
        "header",
        "raw_shape",
        "line_shape",
        "overlap",
        "summary",
        "branch_shape",
        "branch_bool",
        "branch_duplicate",
        "branch_overlap",
        "branch_summary",
    ],
)
def test_official_python_corruption_never_credits(mutation):
    raw = python_raw()
    f = raw["files"]["src.py"]
    if mutation == "format":
        raw["meta"]["format"] = 99
    if mutation == "header":
        raw["meta"]["branch_coverage"] = 1
    if mutation == "raw_shape":
        raw["files"] = []
    if mutation == "line_shape":
        f["executed_lines"] = {}
    if mutation == "overlap":
        f["missing_lines"].append(1)
    if mutation == "summary":
        f["summary"]["covered_lines"] = 79
    if mutation == "branch_shape":
        f["executed_branches"] = {}
    if mutation == "branch_bool":
        f["executed_branches"][0] = [True, 2]
    if mutation == "branch_duplicate":
        f["executed_branches"].append([1, 2])
    if mutation == "branch_overlap":
        f["missing_branches"].append([1, 2])
    if mutation == "branch_summary":
        f["summary"]["covered_branches"] = 79
    with pytest.raises((ValueError, LookupError)):
        gate.python_counts(raw, "src.py", True)


@pytest.mark.parametrize(
    "mutation",
    [
        "format",
        "ids",
        "identity",
        "location_fields",
        "location_order",
        "function",
        "branch_locations",
        "negative",
        "empty_statements",
    ],
)
def test_official_istanbul_corruption_never_credits(mutation):
    raw = js_raw()
    f = raw["src.ts"]
    if mutation == "format":
        f["unknown"] = True
    if mutation == "ids":
        f["s"] = {}
    if mutation == "identity":
        f["s"]["A"] = f["s"].pop("0")
        f["statementMap"]["A"] = f["statementMap"].pop("0")
    if mutation == "location_fields":
        f["statementMap"]["0"]["start"]["unknown"] = 0
    if mutation == "location_order":
        f["statementMap"]["0"]["start"]["line"] = 2
    if mutation == "function":
        f["fnMap"] = {"0": {}}
        f["f"] = {"0": 0}
    if mutation == "branch_locations":
        f["branchMap"]["0"]["locations"] = []
    if mutation == "negative":
        f["s"]["0"] = -1
    if mutation == "empty_statements":
        f["s"] = {}
        f["statementMap"] = {}
    with pytest.raises(ValueError):
        gate.istanbul_counts(raw, "src.ts", True)


def test_root_observation_is_not_a_json_or_bool(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)

    class NoAuthority:
        def observe_preapproval(self, expected):
            return True

        def observe_execution(self, expected):
            return {"bindings": expected}

    result = run_gate(tmp_path, observation=NoAuthority())
    assert result["exit_code"] == 1
    assert "ROOT_OBSERVATION_MISMATCH" in [e["code"] for e in result["errors"]]

    class StaleObserver(SyntheticObserver):
        def capture(self, expected):
            observed = super().capture(expected)
            return gate.ObservedEvidence(
                observed.bindings, {p: b"FAKE" for p in observed.artifact_bytes}
            )

    result = run_gate(tmp_path, observation=StaleObserver(tmp_path))
    assert result["exit_code"] == 1
    assert "ROOT_OBSERVATION_BYTES" in [e["code"] for e in result["errors"]]


@pytest.mark.parametrize(
    "mutation",
    [
        "helper_corrupt",
        "reports_corrupt",
        "inventory_corrupt",
        "runner_missing",
        "path_traversal",
        "policy_min",
        "stale_source",
    ],
)
def test_cli_failure_shapes_namespace_missing_and_concurrent_source(tmp_path, mutation):
    inventory, refs = synthetic_case(tmp_path)
    reports = synthetic_reports(tmp_path, inventory, refs)
    observer = SyntheticObserver(tmp_path)
    if mutation in ("helper_corrupt", "reports_corrupt", "inventory_corrupt"):
        (
            tmp_path
            / {
                "helper_corrupt": "helper.json",
                "reports_corrupt": "P.json",
                "inventory_corrupt": "I.json",
            }[mutation]
        ).write_bytes(b"{")
    elif mutation == "runner_missing":
        reports["runner_records"] = []
        emit(tmp_path, "P.json", reports)
    elif mutation == "path_traversal":
        inventory["candidate_root_ref"]["path"] = "../outside"
        emit(tmp_path, "I.json", inventory)
    elif mutation == "policy_min":
        inventory["policy"]["line_min"] = 79
        emit(tmp_path, "I.json", inventory)
    else:

        class Concurrent(SyntheticObserver):
            def observe_preapproval(self, expected):
                observed = super().observe_preapproval(expected)
                (tmp_path / "candidate/src.py").write_bytes(b"x=2\n" * 200)
                return observed

        observer = Concurrent(tmp_path)
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == (
        2 if mutation in ("helper_corrupt", "reports_corrupt") else 1
    )
    assert gate.validate_schema("verdict", result) == result


def test_reparse_links_are_rejected_within_own_namespace(tmp_path):
    import os

    emit(tmp_path, "source.txt", b"only owned fixture", True)
    try:
        os.symlink(tmp_path / "source.txt", tmp_path / "link.txt")
    except OSError as exc:
        pytest.skip("Windows no concede symlink propio: " + str(exc.winerror))
    with pytest.raises(ValueError, match="REPARSE"):
        gate.scan_tree(tmp_path)


def test_strict_cli_argument_errors_keep_json(capsys):
    assert gate.main([]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["errors"][0]["code"] == "CLI_ARGUMENTS_INVALID"
    assert gate.validate_schema("verdict", result) == result


@pytest.mark.parametrize(
    "classification", ["test", "config", "prose", "deleted_production"]
)
def test_all_nonproduction_exceptions_keep_null_percentages(tmp_path, classification):
    deleted = classification == "deleted_production"
    inventory, refs = synthetic_case(
        tmp_path,
        files={"src.py": (b"x=0\n", None)} if deleted else None,
        production=deleted,
        exception_class=classification if not deleted else "prose",
    )
    synthetic_reports(tmp_path, inventory, refs)
    (tmp_path / "helper.json").unlink()
    result = run_gate(tmp_path, 2, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 0 and result["applies"] is False
    assert (
        result["files"][0]["status"] == "excepted"
        and result["files"][0]["lines"] is None
    )


def test_istanbul_statement_failure_is_phase_exit_one(tmp_path):
    inventory, refs = synthetic_case(
        tmp_path, files={"src.ts": (b"x=0\n", b"x=1\n" * 200)}, stack="istanbul"
    )
    synthetic_reports(tmp_path, inventory, refs, js_raw())
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 1
    assert result["files"][0]["lines"]["covered"] == 1
    assert result["files"][0]["statements"]["covered"] == 70


@pytest.mark.parametrize(
    "data", [b'{"value":1e400}', b'{"value":"\\ud800"}', b'{"\\udfff":1}']
)
def test_json_overflow_and_lone_surrogates_are_invalid(data):
    with pytest.raises(ValueError):
        gate.load_json(data)


def mapped_synthetic_case(root, corrupt=False):
    inventory, refs = synthetic_case(
        root, files={"src.ts": (b"x=0\n", b"x=1\n" * 200)}, stack="istanbul"
    )
    raw = js_raw()
    raw["src.ts"]["s"] = {str(i): 1 for i in range(100)}
    reports = synthetic_reports(root, inventory, refs, raw)
    generated = emit(root, "generated.js", b"x=1;\n" * 200, True)
    mapper = refs["tool.bin"]
    content = (root / "candidate/src.ts").read_text()
    mapping = emit(
        root,
        "source-map.json",
        {
            "version": 3,
            "sources": ["src.ts"],
            "sourcesContent": [content if not corrupt else "FAKE"],
            "mappings": "AAAA",
        },
    )
    raw["generated.js"] = raw.pop("src.ts")
    raw["generated.js"]["path"] = "generated.js"
    rawref = emit(root, "raw.json", raw)
    source = json.loads((root / "source.json").read_bytes())
    source["files"][0]["raw_key"] = "generated.js"
    sourceref = emit(root, "source.json", source)
    e = json.loads((root / "Ej.json").read_bytes())
    e["output_refs"] = [rawref, refs["effective.json"], sourceref, generated, mapping]
    eref = emit(root, "Ej.json", e)
    c = json.loads((root / "Cj.json").read_bytes())
    c.update(
        report_sha256=rawref["sha256"],
        source_manifest_sha256=sourceref["sha256"],
        root_execution_receipt_ref=eref,
    )
    cref = emit(root, "Cj.json", c)
    record = reports["runner_records"][0]
    record.update(
        raw_report_ref=rawref,
        source_manifest_ref=sourceref,
        receipt_ref=cref,
        source_maps=[
            {
                "generated_ref": generated,
                "original_ref": refs["candidate/src.ts"],
                "map_ref": mapping,
                "mapper_ref": mapper,
                "raw_key": "generated.js",
            }
        ],
    )
    emit(root, "P.json", reports)
    return inventory, refs, reports


def test_json_map_requires_independent_official_mapping_observation(tmp_path):
    mapped_synthetic_case(tmp_path)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 2
    assert "MAPPING_OBSERVATION_MISSING" in [e["code"] for e in result["errors"]]


def test_existing_corrupt_source_map_is_fail(tmp_path):
    mapped_synthetic_case(tmp_path, True)
    result = run_gate(tmp_path, observation=SyntheticObserver(tmp_path))
    assert result["exit_code"] == 1
    assert "SOURCE_MAP_MISMATCH" in [e["code"] for e in result["errors"]]


def test_mapping_pairing_positive_only_synthetic_seam(tmp_path):
    mapped_synthetic_case(tmp_path)
    observer = SyntheticObserver(tmp_path)
    observer.observe_mapping = observer.capture
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == 0
    assert result["files"][0]["raw_key"] == "generated.js"
    assert result["files"][0]["statements"]["covered"] == 100


@pytest.mark.parametrize(
    "mutation",
    ["invalid", "absent", "version", "sources", "content", "mappings", "pairing"],
)
def test_mapping_existing_defects_and_required_absence(tmp_path, mutation):
    _inventory, _refs, reports = mapped_synthetic_case(tmp_path)
    record = reports["runner_records"][0]
    observer = SyntheticObserver(tmp_path)
    observer.observe_mapping = observer.capture
    if mutation == "absent":
        record["source_maps"] = []
        emit(tmp_path, "P.json", reports)
    elif mutation == "invalid":
        (tmp_path / "source-map.json").write_bytes(b"{}")
    else:
        source_map = json.loads((tmp_path / "source-map.json").read_bytes())
        if mutation == "version":
            source_map["version"] = 2
        if mutation == "sources":
            source_map["sources"] = ["src.ts", "second.ts"]
        if mutation == "content":
            source_map["sourcesContent"] = []
        if mutation == "mappings":
            source_map["mappings"] = ""
        if mutation == "pairing":
            record["source_maps"][0]["raw_key"] = "unrelated.js"
        if mutation != "pairing":
            mref = emit(tmp_path, "source-map.json", source_map)
            record["source_maps"][0]["map_ref"] = mref
        emit(tmp_path, "P.json", reports)
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == (2 if mutation == "absent" else 1)


def test_concurrent_raw_after_runner_observation_is_fail(tmp_path):
    inventory, refs = synthetic_case(tmp_path)
    synthetic_reports(tmp_path, inventory, refs)

    class ConcurrentRaw(SyntheticObserver):
        def observe_preapproval(self, expected):
            observed = super().observe_preapproval(expected)
            (tmp_path / "raw.json").write_bytes(b"{}")
            return observed

    result = run_gate(tmp_path, observation=ConcurrentRaw(tmp_path))
    assert result["exit_code"] == 1
    assert result["files"][0]["status"] == "fail"


def test_official_combination_zero_branches_requires_observed_proof(tmp_path):
    test_official_combination_observed_not_local_average(tmp_path)
    rawref = emit(tmp_path, "combined-raw.json", python_raw(100, 100, 0, 0))
    proof = emit(
        tmp_path,
        "combined-branch-proof.txt",
        b"SYNTHETIC official exit_counts={}\n",
        True,
    )
    e = json.loads((tmp_path / "Ec.json").read_bytes())
    e["output_refs"][0] = rawref
    e["output_refs"].append(proof)
    eref = emit(tmp_path, "Ec.json", e)
    c = json.loads((tmp_path / "Cc.json").read_bytes())
    c.update(report_sha256=rawref["sha256"], root_execution_receipt_ref=eref)
    cref = emit(tmp_path, "Cc.json", c)
    reports = json.loads((tmp_path / "P.json").read_bytes())
    reports["combined_records"][0].update(raw_report_ref=rawref, receipt_ref=cref)
    emit(tmp_path, "P.json", reports)
    observer = SyntheticObserver(tmp_path)
    observer.branch_proof = lambda expected: gate.ObservedEvidence(
        dict(expected, proof_ref=proof),
        dict(
            observer.capture(expected).artifact_bytes,
            **{
                "combined-branch-proof.txt": (
                    tmp_path / "combined-branch-proof.txt"
                ).read_bytes()
            },
        ),
    )
    result = run_gate(tmp_path, observation=observer)
    assert result["exit_code"] == 0
    assert (
        result["files"][0]["branch_state"] == "not_applicable"
        and result["files"][0]["branch_na_proof_ref"] == proof
    )
