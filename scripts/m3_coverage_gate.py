"""Gate estricto de cobertura M3; no concede autoridad por JSON autoemitido."""

import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def validate_path(value):
    if (
        type(value) is not str
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise ValueError("PATH_INVALID")
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or any(
        c in value for c in ":\\"
    ):
        raise ValueError("PATH_INVALID")
    for part in value.split("/"):
        if (
            not part
            or part in (".", "..")
            or part.endswith((".", " "))
            or re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)
        ):
            raise ValueError("PATH_INVALID")
    return value


def load_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("DUPLICATE_KEY")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("NONFINITE_JSON")

    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("BOM")

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("NONFINITE_JSON")
        return result

    result = json.loads(
        data.decode("utf-8"),
        object_pairs_hook=pairs,
        parse_constant=constant,
        parse_float=number,
    )

    def unicode_check(value):
        if isinstance(value, str):
            value.encode("utf-8")
        elif isinstance(value, dict):
            for key, child in value.items():
                unicode_check(key)
                unicode_check(child)
        elif isinstance(value, list):
            for child in value:
                unicode_check(child)

    unicode_check(result)
    return result


SCHEMAS = {
    "artifact": "path:Path sha256:S bytes:N",
    "tree": "schema_version:=1 root_id:U files:[tree_file]",
    "tree_file": "path:Path sha256:S bytes:N kind:=regular",
    "root": "root_id:U path:Path tree_sha256:S inventory_ref:artifact",
    "policy": "line_min:=80 branch_required:B branch_min:N? scope:=whole_changed_current rounding:=none exceptions:[exception]",
    "exception": "path:Path classification:test|config|prose|deleted_production reason:L proof_ref:artifact root_approval_ref:artifact",
    "file": "path:Path base_sha256:S? candidate_sha256:S? base_bytes:N? candidate_bytes:N? stack:python|istanbul|none package:Path? classification:production|test|config|prose runner_id:U? exception_ref:artifact?",
    "change": "kind:added|modified|deleted|renamed old_path:Path? new_path:Path? old_sha256:S? new_sha256:S?",
    "inventory": "schema_version:=1 phase_id:U created_at:UTC base_root_ref:root candidate_root_ref:root source_freeze_ref:artifact policy:policy files:[file] changes:[change]",
    "freeze": "schema_version:=1 phase_id:U created_at:UTC contract_ref:artifact base_inventory_ref:artifact candidate_inventory_ref:artifact classification_ref:artifact runner_config_refs:[artifact] tool_lock_refs:[artifact] root_ratification_ref:artifact",
    "classification": "schema_version:=1 phase_id:U base_inventory_ref:artifact candidate_inventory_ref:artifact entries:[classification_entry]",
    "classification_entry": "path:Path classification:production|test|config|prose|deleted_production reason:L proof_refs:[artifact]",
    "approval": "schema_version:=1 approval_id:U phase_id:U created_at:UTC contract_ref:artifact base_inventory_ref:artifact candidate_inventory_ref:artifact classification_ref:artifact runner_plan_ref:artifact policy:policy runner_config_refs:[artifact] tool_lock_refs:[artifact] root_authorization_ref:artifact",
    "plan": "schema_version:=1 phase_id:U entries:[plan_entry]",
    "plan_entry": "runner_id:U kind:runner|combine stack:python|istanbul package:Path tool_ref:artifact input_runner_ids:[U]",
    "execution": "schema_version:=1 execution_id:U phase_id:U kind:root_inventory|runner|combine runner_id:U? upstream_refs:[artifact] argv:[Text] cwd:Path environment:[env] started_at:UTC finished_at:UTC exit_code:N stdout_ref:artifact stderr_ref:artifact tool_ref:artifact observed_source_inventory_refs:[artifact] output_refs:[artifact] custody_ref:artifact",
    "env": "name:L value:Text",
    "root_receipt": "schema_version:=1 phase_id:U created_at:UTC base_root_id:U candidate_root_id:U base_tree_sha256:S candidate_tree_sha256:S inventory_sha256:S source_freeze_sha256:S approved_classification_ref:artifact namespace:Path runner_ids:[U] root_execution_ref:artifact",
    "reports": "schema_version:=1 phase_id:U inventory_sha256:S source_freeze_sha256:S root_receipt_ref:artifact runner_records:[runner] combined_records:[combined]",
    "runner": "runner_id:U stack:python|istanbul package:Path platform:L tool:tool receipt_ref:artifact raw_report_ref:artifact summary_ref:artifact? config_refs:[artifact] effective_config_ref:artifact source_manifest_ref:artifact source_maps:[map] test_result_refs:[artifact]",
    "tool": "name:coverage.py|jest|vitest version:L executable_ref:artifact lock_refs:[artifact]",
    "map": "generated_ref:artifact original_ref:artifact map_ref:artifact mapper_ref:artifact raw_key:Text",
    "combined": "combined_id:U stack:python|istanbul input_runner_ids:[U] tool_ref:artifact receipt_ref:artifact raw_report_ref:artifact source_manifest_ref:artifact",
    "receipt": "schema_version:=1 runner_id:U phase_id:U argv:[Text] cwd:Path environment:[env] started_at:UTC finished_at:UTC exit_code:N stdout_ref:artifact stderr_ref:artifact tool_ref:artifact config_sha256:S inventory_sha256:S source_manifest_sha256:S report_sha256:S root_execution_receipt_ref:artifact",
    "config": "schema_version:=1 runner_id:U source_roots:[Path] branch:B include_patterns:[Text] omit_patterns:[Text] exclude_lines:[Text] ignore_patterns:[Text] test_nodes:[Text] config_refs:[artifact] raw_effective_ref:artifact",
    "source": "schema_version:=1 runner_id:U files:[source_file]",
    "source_file": "path:Path sha256:S bytes:N raw_key:Text",
    "percent": "numerator:Q denominator:P",
    "counter": "covered:N total:P percent:percent minimum:=80",
    "file_verdict": "path:Path change:added|modified|deleted|renamed classification:production|test|config|prose source_sha256:S? runner_id:U? raw_key:Text? lines:counter? statements:counter? branches:counter? branch_state:measured|not_required|not_applicable|pending branch_na_proof_ref:artifact? status:pass|fail|pending|excepted reason:L?",
    "stack_verdict": "stack:python|istanbul package:Path runner_ids:[U] status:pass|fail|pending",
    "exclusion": "path:Path reason:L",
    "error": "code:L path:Path? proof_ref:artifact?",
    "verdict": "schema_version:=1 phase_id:U? inventory_sha256:S? reports_sha256:S? helper_sha256:S? helper_exit:0|1|2 applies:B verdict:pass|fail|pending exit_code:0|1|2 files:[file_verdict] exceptions:[exception] missing:[Path] ambiguous:[Path] exclusions:[exclusion] stacks:[stack_verdict] errors:[error]",
}


def _domain(token, value):
    if token.endswith("?"):
        if value is None:
            return
        return _domain(token[:-1], value)
    if token.startswith("["):
        if type(value) is not list or len(value) > 100000:
            raise ValueError("ARRAY_INVALID")
        for item in value:
            _domain(token[1:-1], item)
        return
    if token in SCHEMAS:
        validate_schema(token, value)
        return
    if token.startswith("=") or "|" in token:
        options = token[1:].split("|") if token.startswith("=") else token.split("|")
        literals = [int(x) if x.isdigit() else x for x in options]
        if not any(type(value) is type(x) and value == x for x in literals):
            raise ValueError("LITERAL_INVALID")
        return
    if token in ("N", "P", "Q"):
        maximum = (2**63 - 1) * (100 if token == "Q" else 1)
        if (
            type(value) is not int
            or value < (1 if token == "P" else 0)
            or value > maximum
        ):
            raise ValueError("INTEGER_INVALID")
    elif token == "B":
        if type(value) is not bool:
            raise ValueError("BOOL_INVALID")
    elif token == "Path":
        validate_path(value)
    elif token in ("S", "U", "L", "UTC", "Text"):
        patterns = {
            "S": r"[0-9a-f]{64}",
            "U": r"[0-7][0-9A-HJKMNP-TV-Z]{25}",
            "L": r"[a-zA-Z0-9_.:-]{1,128}",
            "UTC": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
        }
        if (
            type(value) is not str
            or (token == "Text" and len(value) > 32768)
            or (token != "Text" and not re.fullmatch(patterns[token], value))
        ):
            raise ValueError("STRING_INVALID")
        if token == "UTC":
            from datetime import datetime

            datetime.fromisoformat(value)
    else:
        raise ValueError("SCHEMA_UNKNOWN")


def validate_schema(name, value):
    fields = dict(field.split(":", 1) for field in SCHEMAS[name].split())
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError("CLOSED_SCHEMA")
    for field, token in fields.items():
        _domain(token, value[field])
    if name == "policy" and value["branch_min"] != (
        80 if value["branch_required"] else None
    ):
        raise ValueError("BRANCH_POLICY")
    if name == "counter" and (
        value["covered"] > value["total"]
        or value["percent"]
        != {"numerator": 100 * value["covered"], "denominator": value["total"]}
    ):
        raise ValueError("COUNTER_INVALID")
    if name in ("tree", "source"):
        paths = [row["path"] for row in value["files"]]
        if len({p.casefold() for p in paths}) != len(paths):
            raise ValueError("PATH_COLLISION")
        if paths != sorted(paths, key=lambda p: p.encode("utf-8")):
            raise ValueError("PATH_ORDER")
    return value


def scan_tree(root):
    root = Path(root)
    _safe_components(root)
    result = []

    def visit(directory):
        for child in directory.iterdir():
            info = _safe_components(child)
            relative = validate_path(child.relative_to(root).as_posix())
            if stat.S_ISDIR(info.st_mode):
                visit(child)
            elif stat.S_ISREG(info.st_mode):
                data = _read_stable(child)
                result.append(
                    {
                        "path": relative,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "bytes": len(data),
                        "kind": "regular",
                    }
                )
            else:
                raise ValueError("FILE_KIND")

    visit(root)
    result.sort(key=lambda row: row["path"].encode("utf-8"))
    if len({r["path"].casefold() for r in result}) != len(result):
        raise ValueError("PATH_COLLISION")
    return result


def _safe_components(path):
    path = Path(path).absolute()
    for component in [*reversed(path.parents), path]:
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("REPARSE")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("HARDLINK_UNPROVEN")
    return info


def _read_stable(path):
    before = _safe_components(path)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("FILE_KIND")
    with open(path, "rb") as handle:
        opened = os.fstat(handle.fileno())
        data = handle.read()
        closed = os.fstat(handle.fileno())
    after = _safe_components(path)
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
    if len({signature(s) for s in (before, opened, closed, after)}) != 1:
        raise ValueError("SOURCE_MISMATCH")
    return data


def artifact_refs(value):
    if isinstance(value, dict):
        if set(value) == {"path", "sha256", "bytes"}:
            yield value
        else:
            for child in value.values():
                yield from artifact_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifact_refs(child)


class Evidence:
    def __init__(self, root):
        self.root = Path(root).absolute()
        _safe_components(self.root)

    def path(self, relative):
        validate_path(relative)
        path = self.root / relative
        _safe_components(path)
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("PATH_ESCAPE")
        return path

    def artifact(self, ref, active=()):
        validate_schema("artifact", ref)
        path = ref["path"]
        if path in active:
            raise ValueError("DAG_CYCLE")
        data = _read_stable(self.path(path))
        if path.endswith(".json"):
            document = load_json(data)
            for dependency in artifact_refs(document):
                self.artifact(dependency, active + (path,))
        if (
            len(data) != ref["bytes"]
            or hashlib.sha256(data).hexdigest() != ref["sha256"]
        ):
            raise ValueError("SOURCE_MISMATCH")
        return data

    def document(self, ref, schema):
        data = self.artifact(ref)
        try:
            return validate_schema(schema, load_json(data))
        except ValueError as exc:
            if schema in ("receipt", "root_receipt", "execution"):
                raise LookupError("RECEIPT_INVALID") from exc
            raise


COVERAGE_READERS = {"7.13.1": 3, "7.16.2": 3}
ISTANBUL_READERS = {("vitest", "3.0.0")}


def python_counts(raw, key, branch_required):
    if (
        type(raw) is not dict
        or type(raw.get("meta")) is not dict
        or type(raw.get("files")) is not dict
    ):
        raise ValueError("RAW_INVALID")
    meta = raw["meta"]
    if type(meta.get("version")) is not str or meta["version"] not in COVERAGE_READERS:
        raise LookupError("TOOL_FORMAT_UNKNOWN")
    if (
        type(meta.get("format")) is not int
        or meta["format"] != COVERAGE_READERS[meta["version"]]
    ):
        raise ValueError("RAW_HEADER_INVALID")
    if (
        type(meta.get("branch_coverage")) is not bool
        or type(meta.get("timestamp")) is not str
    ):
        raise ValueError("RAW_HEADER_INVALID")
    if key not in raw["files"]:
        raise ValueError("PRODUCTION_MISSING")
    f = raw["files"][key]

    def line_set(field):
        values = f[field]
        if type(values) is not list:
            raise ValueError("LINES_INVALID")
        for value in values:
            _domain("P", value)
        if len(set(values)) != len(values):
            raise ValueError("LINES_DUPLICATE")
        return set(values)

    covered, missing = line_set("executed_lines"), line_set("missing_lines")
    if covered & missing or f.get("excluded_lines") != []:
        raise ValueError("EXCLUSION_OR_OVERLAP")
    s = f["summary"]
    for field, expected in [
        ("num_statements", len(covered | missing)),
        ("covered_lines", len(covered)),
        ("missing_lines", len(missing)),
    ]:
        _domain("N", s[field])
        if s[field] != expected:
            raise ValueError("COUNTER_INVALID")
    lines = counter(len(covered), len(covered | missing))
    branches = None
    if branch_required:
        if not meta["branch_coverage"]:
            raise ValueError("BRANCH_DISABLED")
        sets = []
        for field in ("executed_branches", "missing_branches"):
            values = f[field]
            if type(values) is not list:
                raise ValueError("BRANCH_INVALID")
            for arc in values:
                if (
                    type(arc) is not list
                    or len(arc) != 2
                    or any(
                        type(x) is not int or abs(x) > 2**63 - 1 or x == 0 for x in arc
                    )
                ):
                    raise ValueError("BRANCH_INVALID")
            arcs = {tuple(x) for x in values}
            if len(arcs) != len(values):
                raise ValueError("BRANCH_DUPLICATE")
            sets.append(arcs)
        executed, absent = sets
        if executed & absent:
            raise ValueError("BRANCH_OVERLAP")
        for field, expected in [
            ("num_branches", len(executed | absent)),
            ("covered_branches", len(executed)),
            ("missing_branches", len(absent)),
        ]:
            _domain("N", s[field])
            if s[field] != expected:
                raise ValueError("BRANCH_COUNTER_INVALID")
        if executed or absent:
            branches = counter(len(executed), len(executed | absent))
    return {"lines": lines, "statements": lines, "branches": branches}


def counter(covered, total):
    value = {
        "covered": covered,
        "total": total,
        "percent": {"numerator": 100 * covered, "denominator": total},
        "minimum": 80,
    }
    return validate_schema("counter", value)


def _location(value):
    if type(value) is not dict or set(value) != {"start", "end"}:
        raise ValueError("MAP_RANGE")
    for point in value.values():
        if type(point) is not dict or set(point) != {"line", "column"}:
            raise ValueError("MAP_RANGE")
        _domain("P", point["line"])
        _domain("N", point["column"])
    start, end = value["start"], value["end"]
    if (start["line"], start["column"]) > (end["line"], end["column"]):
        raise ValueError("MAP_RANGE")


def istanbul_counts(raw, key, branch_required):
    if type(raw) is not dict or key not in raw:
        raise ValueError("PRODUCTION_MISSING")
    f = raw[key]
    required = {"path", "statementMap", "fnMap", "branchMap", "s", "f", "b"}
    if (
        type(f) is not dict
        or not required <= set(f)
        or set(f) - required - {"inputSourceMap", "_coverageSchema", "hash", "all"}
        or f["path"] != key
    ):
        raise ValueError("ISTANBUL_FORMAT")
    for maps, counts in [("statementMap", "s"), ("fnMap", "f"), ("branchMap", "b")]:
        if (
            type(f[maps]) is not dict
            or type(f[counts]) is not dict
            or set(f[maps]) != set(f[counts])
        ):
            raise ValueError("MAP_IDS")
        for identity in f[maps]:
            if not re.fullmatch(r"0|[1-9][0-9]*", identity):
                raise ValueError("MAP_IDS")
    lines = {}
    for identity, location in f["statementMap"].items():
        _location(location)
        count = f["s"][identity]
        _domain("N", count)
        line = location["start"]["line"]
        lines[line] = max(lines.get(line, 0), count)
    for identity, fn in f["fnMap"].items():
        if type(fn) is not dict or not {"name", "decl", "loc", "line"} <= set(fn):
            raise ValueError("FUNCTION_MAP")
        _location(fn["decl"])
        _location(fn["loc"])
        _domain("P", fn["line"])
        _domain("N", f["f"][identity])
    branch_counts = []
    for identity, branch in f["branchMap"].items():
        if type(branch) is not dict or not {"type", "locations"} <= set(branch):
            raise ValueError("BRANCH_MAP")
        if "loc" in branch:
            _location(branch["loc"])
        locations = branch["locations"]
        counts = f["b"][identity]
        if (
            type(locations) is not list
            or type(counts) is not list
            or len(locations) != len(counts)
            or not counts
        ):
            raise ValueError("BRANCH_MAP")
        for location, count in zip(locations, counts):
            _location(location)
            _domain("N", count)
            branch_counts.append(count)
    return {
        "lines": counter(sum(x > 0 for x in lines.values()), len(lines)),
        "statements": counter(sum(x > 0 for x in f["s"].values()), len(f["s"])),
        "branches": counter(sum(x > 0 for x in branch_counts), len(branch_counts))
        if branch_required and branch_counts
        else None,
    }


def inspect_inventory(evidence, inventory):
    validate_schema("inventory", inventory)
    phase = inventory["phase_id"]
    trees = []
    for key in ("base_root_ref", "candidate_root_ref"):
        root = inventory[key]
        tree = evidence.document(root["inventory_ref"], "tree")
        canonical = json.dumps(
            tree,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
        if (
            tree["root_id"] != root["root_id"]
            or hashlib.sha256(canonical).hexdigest() != root["tree_sha256"]
        ):
            raise ValueError("TREE_BINDING")
        if tree["files"] != scan_tree(evidence.path(root["path"])):
            raise ValueError("SOURCE_MISMATCH")
        trees.append({r["path"]: r for r in tree["files"]})
    base, candidate = trees
    paths = {p for p in set(base) | set(candidate) if base.get(p) != candidate.get(p)}
    files = unique_rows(inventory["files"], "path")
    if set(files) != paths:
        raise ValueError("INVENTORY_DIFF")
    if len({p.casefold() for p in set(base) | set(candidate)}) != len(
        set(base) | set(candidate)
    ):
        raise ValueError("PATH_COLLISION")
    freeze = evidence.document(inventory["source_freeze_ref"], "freeze")
    approval = evidence.document(freeze["root_ratification_ref"], "approval")
    classification = evidence.document(freeze["classification_ref"], "classification")
    plan = evidence.document(approval["runner_plan_ref"], "plan")
    for doc in (freeze, approval, classification, plan):
        if doc["phase_id"] != phase:
            raise ValueError("PHASE_MISMATCH")
    for key, source in [
        ("base_inventory_ref", "base_root_ref"),
        ("candidate_inventory_ref", "candidate_root_ref"),
    ]:
        expected = inventory[source]["inventory_ref"]
        if any(d[key] != expected for d in (freeze, approval, classification)):
            raise ValueError("TREE_BINDING")
    for key in (
        "contract_ref",
        "classification_ref",
        "runner_config_refs",
        "tool_lock_refs",
    ):
        if freeze[key] != approval[key]:
            raise ValueError("FREEZE_BINDING")
    approved_policy = dict(inventory["policy"], exceptions=[])
    if approval["policy"] != approved_policy:
        raise ValueError("POLICY_BINDING")
    classifications = unique_rows(classification["entries"], "path")
    if set(classifications) != paths:
        raise ValueError("CLASSIFICATION_DIFF")
    runners = unique_rows(plan["entries"], "runner_id")
    seen = set()
    for entry in plan["entries"]:
        inputs = entry["input_runner_ids"]
        if (
            len(set(inputs)) != len(inputs)
            or (entry["kind"] == "runner" and inputs)
            or (entry["kind"] == "combine" and (not inputs or not set(inputs) <= seen))
        ):
            raise ValueError("PLAN_DAG")
        seen.add(entry["runner_id"])
    touched = set()
    kinds = {}
    for change in inventory["changes"]:
        old, new = change["old_path"], change["new_path"]
        kind = change["kind"]
        if kind == "added" and (old is not None or new is None or new in base):
            raise ValueError("CHANGE_INVALID")
        if kind == "deleted" and (new is not None or old is None or old in candidate):
            raise ValueError("CHANGE_INVALID")
        if kind == "modified" and (old is None or old != new):
            raise ValueError("CHANGE_INVALID")
        if kind == "renamed" and (
            old is None or new is None or old == new or old in candidate or new in base
        ):
            raise ValueError("CHANGE_INVALID")
        members = {p for p in (old, new) if p is not None}
        if touched & members or not members <= paths:
            raise ValueError("CHANGE_DUPLICATE")
        touched |= members
        for p in members:
            kinds[p] = kind
        if change["old_sha256"] != (base.get(old) or {}).get("sha256") or change[
            "new_sha256"
        ] != (candidate.get(new) or {}).get("sha256"):
            raise ValueError("CHANGE_SHA")
    if touched != paths:
        raise ValueError("CHANGE_MISSING")
    exceptions = unique_rows(inventory["policy"]["exceptions"], "path")
    required_exceptions = set()
    current = set()
    for path, row in files.items():
        for prefix, tree in [("base", base), ("candidate", candidate)]:
            observed = tree.get(path, {})
            if row[prefix + "_sha256"] != observed.get("sha256") or row[
                prefix + "_bytes"
            ] != observed.get("bytes"):
                raise ValueError("SOURCE_MISMATCH")
        cls = classifications[path]
        deleted = path not in candidate
        expected_cls = (
            "deleted_production"
            if deleted and row["classification"] == "production"
            else row["classification"]
        )
        if cls["classification"] != expected_cls or not cls["proof_refs"]:
            raise ValueError("CLASSIFICATION_MISMATCH")
        if row["classification"] == "production" and not deleted:
            current.add(path)
            if (
                row["exception_ref"] is not None
                or row["stack"] == "none"
                or row["package"] is None
                or row["runner_id"] not in runners
            ):
                raise ValueError("PRODUCTION_DISGUISED")
            planned = runners[row["runner_id"]]
            if planned["kind"] != "runner" or (
                planned["stack"],
                planned["package"],
            ) != (row["stack"], row["package"]):
                raise ValueError("RUNNER_BINDING")
        else:
            required_exceptions.add(path)
            if row["exception_ref"] is None or path not in exceptions:
                raise ValueError("EXCEPTION_MISSING")
            exc = evidence.document(row["exception_ref"], "exception")
            if (
                exc != exceptions[path]
                or exc["classification"] != expected_cls
                or exc["root_approval_ref"] != freeze["root_ratification_ref"]
                or exc["proof_ref"] not in cls["proof_refs"]
            ):
                raise ValueError("EXCEPTION_BINDING")
    if set(exceptions) != required_exceptions:
        raise ValueError("EXCEPTION_EXTRA")
    return {
        "current": current,
        "base": base,
        "candidate": candidate,
        "freeze": freeze,
        "approval": approval,
        "classification": classification,
        "plan": plan,
        "kinds": kinds,
        "runners": runners,
    }


def unique_rows(rows, key):
    result = {r[key]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("DUPLICATE_ID")
    return result


def evaluate(
    inventory_path, reports_path, helper_path, helper_exit, minimum=80, observation=None
):
    result = {
        "schema_version": 1,
        "phase_id": None,
        "inventory_sha256": None,
        "reports_sha256": None,
        "helper_sha256": None,
        "helper_exit": helper_exit
        if type(helper_exit) is int and helper_exit in (0, 1, 2)
        else 2,
        "applies": True,
        "verdict": "pending",
        "exit_code": 2,
        "files": [],
        "exceptions": [],
        "missing": [],
        "ambiguous": [],
        "exclusions": [],
        "stacks": [],
        "errors": [],
    }
    faults = []

    def error(code, pending=False, path=None):
        if not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,128}", code):
            code = "INPUT_INVALID"
        result["errors"].append({"code": code, "path": path, "proof_ref": None})
        faults.append(2 if pending else 1)

    def caught(exc, invalid_pending=False, path=None):
        pending = (
            isinstance(exc, (OSError, json.JSONDecodeError, UnicodeError))
            or type(exc) is LookupError
            or invalid_pending
        )
        error(
            str(exc)
            if isinstance(exc, ValueError)
            and not isinstance(exc, json.JSONDecodeError)
            or type(exc) is LookupError
            else "EVIDENCE_MISSING_OR_INVALID",
            pending,
            path,
        )

    def finish():
        exit_code = 1 if 1 in faults else 2 if 2 in faults else 0
        if exit_code:
            for row in result["files"]:
                if row["status"] == "pass":
                    row.update(
                        status="fail" if exit_code == 1 else "pending",
                        reason="PHASE_EVIDENCE_INVALID"
                        if exit_code == 1
                        else "PHASE_EVIDENCE_PENDING",
                    )
        result.update(
            exit_code=exit_code, verdict={0: "pass", 1: "fail", 2: "pending"}[exit_code]
        )
        return validate_schema("verdict", result)

    try:
        if (
            type(minimum) is not int
            or minimum != 80
            or type(helper_exit) is not int
            or helper_exit not in (0, 1, 2)
        ):
            raise ValueError("CLI_POLICY_INVALID")
        inventory_path = Path(inventory_path).absolute()
        evidence = Evidence(inventory_path.parent)
        inventory_bytes = _read_stable(evidence.path(inventory_path.name))
        inventory = validate_schema("inventory", load_json(inventory_bytes))
        inventory_ref = {
            "path": inventory_path.name,
            "sha256": hashlib.sha256(inventory_bytes).hexdigest(),
            "bytes": len(inventory_bytes),
        }
        result.update(
            phase_id=inventory["phase_id"], inventory_sha256=inventory_ref["sha256"]
        )
        state = inspect_inventory(evidence, inventory)
        result["applies"] = bool(state["current"])
        result["exceptions"] = inventory["policy"]["exceptions"]
        for row in inventory["files"]:
            current = row["path"] in state["current"]
            result["files"].append(
                {
                    "path": row["path"],
                    "change": state["kinds"][row["path"]],
                    "classification": row["classification"],
                    "source_sha256": row["candidate_sha256"],
                    "runner_id": row["runner_id"],
                    "raw_key": None,
                    "lines": None,
                    "statements": None,
                    "branches": None,
                    "branch_state": "pending" if current else "not_required",
                    "branch_na_proof_ref": None,
                    "status": "pending" if current else "excepted",
                    "reason": None if current else "ROOT_APPROVED_EXCEPTION",
                }
            )
    except (ValueError, OSError, KeyError, TypeError, RecursionError):
        error("INVENTORY_INVALID")
        return finish()
    try:
        reports_path = Path(reports_path).absolute()
        helper_path = Path(helper_path).absolute()
        if reports_path.parent != evidence.root or helper_path.parent != evidence.root:
            raise ValueError("INPUT_NAMESPACE")
        reports_bytes = _read_stable(evidence.path(reports_path.name))
        try:
            reports = validate_schema("reports", load_json(reports_bytes))
        except (ValueError, KeyError, TypeError) as exc:
            caught(exc, invalid_pending=True)
            if observation is None:
                error("ROOT_CUSTODY_MISSING", True)
            return finish()
        result["reports_sha256"] = hashlib.sha256(reports_bytes).hexdigest()
        if (
            reports["phase_id"] != inventory["phase_id"]
            or reports["inventory_sha256"] != inventory_ref["sha256"]
            or reports["source_freeze_sha256"]
            != inventory["source_freeze_ref"]["sha256"]
        ):
            raise ValueError("REPORT_BINDING")
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as exc:
        caught(
            exc,
            invalid_pending=isinstance(
                exc, (json.JSONDecodeError, KeyError, TypeError)
            ),
        )
        if observation is None:
            error("ROOT_CUSTODY_MISSING", True)
        return finish()
    try:
        helper_bytes = _read_stable(evidence.path(helper_path.name))
        load_json(helper_bytes)
        result["helper_sha256"] = hashlib.sha256(helper_bytes).hexdigest()
    except (ValueError, OSError) as exc:
        if result["applies"]:
            caught(exc, True)
    if result["applies"] and helper_exit:
        error(
            "HELPER_FAILED" if helper_exit == 1 else "HELPER_UNAVAILABLE",
            helper_exit == 2,
        )
    rows = {r["path"]: r for r in result["files"]}
    root_receipt = None
    try:
        root_receipt = evidence.document(reports["root_receipt_ref"], "root_receipt")
        inspect_root_receipt(evidence, inventory, inventory_ref, state, root_receipt)
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as exc:
        caught(exc)
    try:
        runners = unique_rows(reports["runner_records"], "runner_id")
        combined = unique_rows(reports["combined_records"], "combined_id")
        if set(runners) & set(combined):
            raise ValueError("DUPLICATE_ID")
        if set(runners) | set(combined) != set(state["runners"]):
            raise ValueError("RUNNER_MISSING")
    except ValueError as exc:
        caught(exc)
        runners = {r["runner_id"]: r for r in reports["runner_records"]}
        combined = {r["combined_id"]: r for r in reports["combined_records"]}
    for rid, record in runners.items():
        requires_union = any(rid in r["input_runner_ids"] for r in combined.values())
        matched = [
            r
            for r in inventory["files"]
            if r["runner_id"] == rid and r["path"] in state["current"]
        ]
        stack_result = {
            "stack": record["stack"],
            "package": record["package"],
            "runner_ids": [rid],
            "status": "pass",
        }
        result["stacks"].append(stack_result)
        before = len(faults)
        raw = None
        try:
            raw = load_json(evidence.artifact(record["raw_report_ref"]))
            source = evidence.document(record["source_manifest_ref"], "source")
            config = evidence.document(record["effective_config_ref"], "config")
            inspect_runner_inputs(evidence, inventory, state, record, source, config)
            source_files = unique_rows(source["files"], "path")
            if type(raw) is not dict or (
                record["stack"] == "python" and type(raw.get("meta")) is not dict
            ):
                raise LookupError("RAW_INVALID")
            if (
                record["stack"] == "python"
                and raw.get("meta", {}).get("version") != record["tool"]["version"]
            ):
                raise ValueError("RAW_TOOL_VERSION_MISMATCH")
            for source_row in source_files.values():
                (python_counts if record["stack"] == "python" else istanbul_counts)(
                    raw, source_row["raw_key"], inventory["policy"]["branch_required"]
                )
                inspect_raw_source_range(
                    evidence, inventory, record["stack"], raw, source_row
                )
            for row in matched:
                verdict = rows[row["path"]]
                if row["path"] not in source_files:
                    raise ValueError("PRODUCTION_MISSING")
                source_row = source_files[row["path"]]
                verdict["raw_key"] = source_row["raw_key"]
                try:
                    counts = (
                        python_counts
                        if record["stack"] == "python"
                        else istanbul_counts
                    )(
                        raw,
                        source_row["raw_key"],
                        inventory["policy"]["branch_required"],
                    )
                    inspect_raw_source_range(
                        evidence, inventory, record["stack"], raw, source_row
                    )
                    verdict.update(counts)
                    verdict["branch_state"] = (
                        "measured"
                        if counts["branches"] is not None
                        else "not_required"
                        if not inventory["policy"]["branch_required"]
                        else "pending"
                    )
                    if (
                        inventory["policy"]["branch_required"]
                        and counts["branches"] is None
                    ):
                        try:
                            proof = inspect_branch_proof(
                                evidence,
                                record,
                                source_row,
                                config,
                                inventory,
                                observation,
                            )
                            verdict.update(
                                branch_state="not_applicable", branch_na_proof_ref=proof
                            )
                        except (
                            ValueError,
                            OSError,
                            LookupError,
                            AttributeError,
                        ) as exc:
                            if isinstance(exc, (LookupError, AttributeError)):
                                error("BRANCH_PROOF_MISSING", True, row["path"])
                            else:
                                caught(exc, path=row["path"])
                    low = any(
                        c is not None and 100 * c["covered"] < 80 * c["total"]
                        for c in counts.values()
                    )
                    verdict["status"] = (
                        "fail"
                        if low
                        else "pending"
                        if verdict["branch_state"] == "pending"
                        else "pass"
                    )
                    if low and not requires_union:
                        error("BELOW_MINIMUM", False, row["path"])
                    if requires_union:
                        verdict.update(
                            status="pending", reason="OFFICIAL_COMBINATION_REQUIRED"
                        )
                except (ValueError, LookupError, KeyError, TypeError) as exc:
                    caught(exc, path=row["path"])
                    verdict["status"] = (
                        "pending" if isinstance(exc, LookupError) else "fail"
                    )
                    verdict["reason"] = (
                        str(exc) if isinstance(exc, ValueError) else "RAW_INVALID"
                    )
                    if isinstance(exc, ValueError) and str(exc) == "PRODUCTION_MISSING":
                        result["missing"].append(row["path"])
            inspect_runner_receipt(
                evidence,
                inventory,
                inventory_ref,
                state,
                record,
                source,
                config,
                observation,
            )
        except (
            ValueError,
            OSError,
            LookupError,
            KeyError,
            TypeError,
            RecursionError,
        ) as exc:
            caught(exc)
            if isinstance(exc, ValueError) and str(exc) == "PRODUCTION_MISSING":
                result["missing"].extend(
                    row["path"]
                    for row in matched
                    if row["path"] not in result["missing"]
                )
        new = faults[before:]
        stack_result["status"] = (
            "fail" if 1 in new else "pending" if 2 in new else "pass"
        )
        for row in matched:
            verdict = rows[row["path"]]
            if stack_result["status"] == "fail" and verdict["status"] != "fail":
                verdict.update(status="fail", reason="RUNNER_INVALID")
            elif stack_result["status"] == "pending" and verdict["status"] == "pass":
                verdict.update(status="pending", reason="RUNNER_PENDING")
    for row in inventory["files"]:
        if row["path"] in state["current"] and row["runner_id"] not in runners:
            result["missing"].append(row["path"])
            error("RUNNER_MISSING", False, row["path"])
    for cid, record in combined.items():
        try:
            counts_by_path = inspect_combined(
                evidence, inventory, inventory_ref, state, record, runners, observation
            )
            for path, counts in counts_by_path.items():
                if path not in rows or path not in state["current"]:
                    continue
                verdict = rows[path]
                verdict.update(
                    counts,
                    runner_id=cid,
                    branch_state="measured"
                    if counts["branches"] is not None
                    else "not_required"
                    if not inventory["policy"]["branch_required"]
                    else "not_applicable"
                    if counts.get("branch_na_proof_ref") is not None
                    else "pending",
                    reason=None,
                )
                low = any(
                    c is not None and 100 * c["covered"] < 80 * c["total"]
                    for c in (counts[k] for k in ("lines", "statements", "branches"))
                )
                verdict["status"] = (
                    "fail"
                    if low
                    else "pending"
                    if verdict["branch_state"] == "pending"
                    else "pass"
                )
                if low:
                    error("BELOW_MINIMUM", False, path)
                if verdict["branch_state"] == "pending":
                    error("BRANCH_PROOF_MISSING", True, path)
        except (
            ValueError,
            OSError,
            LookupError,
            KeyError,
            TypeError,
            RecursionError,
        ) as exc:
            caught(exc)
    try:
        if observation is None:
            raise LookupError("ROOT_CUSTODY_MISSING")
        expected = {
            "kind": "preapproval",
            "inventory_ref": inventory_ref,
            "inventory": inventory,
            "freeze": state["freeze"],
            "approval": state["approval"],
            "classification": state["classification"],
            "plan": state["plan"],
        }
        verify_observation(
            evidence, observation.observe_preapproval(expected), expected
        )
        if root_receipt is not None:
            execution = evidence.document(
                root_receipt["root_execution_ref"], "execution"
            )
            expected = {
                "kind": "root_inventory",
                "inventory_ref": inventory_ref,
                "root_receipt": root_receipt,
                "execution": execution,
            }
            verify_observation(
                evidence, observation.observe_execution(expected), expected
            )
        else:
            raise LookupError("ROOT_CUSTODY_MISSING")
    except (ValueError, OSError, LookupError, AttributeError, TypeError) as exc:
        if isinstance(exc, (LookupError, AttributeError)):
            error("ROOT_CUSTODY_MISSING", True)
        else:
            caught(exc)
    try:
        inspect_inventory(evidence, inventory)
        evidence.artifact(inventory_ref)
        evidence.artifact(
            {
                "path": reports_path.name,
                "sha256": result["reports_sha256"],
                "bytes": len(reports_bytes),
            }
        )
        if result["helper_sha256"] is not None and (
            hashlib.sha256(_read_stable(evidence.path(helper_path.name))).hexdigest()
            != result["helper_sha256"]
        ):
            raise ValueError("SOURCE_MISMATCH")
        if _read_stable(evidence.path(reports_path.name)) != reports_bytes:
            raise ValueError("SOURCE_MISMATCH")
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as exc:
        caught(exc)
    return finish()


def inspect_root_receipt(evidence, inventory, inventory_ref, state, receipt):
    expected = {
        "phase_id": inventory["phase_id"],
        "base_root_id": inventory["base_root_ref"]["root_id"],
        "candidate_root_id": inventory["candidate_root_ref"]["root_id"],
        "base_tree_sha256": inventory["base_root_ref"]["tree_sha256"],
        "candidate_tree_sha256": inventory["candidate_root_ref"]["tree_sha256"],
        "inventory_sha256": inventory_ref["sha256"],
        "source_freeze_sha256": inventory["source_freeze_ref"]["sha256"],
        "approved_classification_ref": state["freeze"]["classification_ref"],
    }
    if (
        any(receipt[k] != v for k, v in expected.items())
        or len(set(receipt["runner_ids"])) != len(receipt["runner_ids"])
        or set(receipt["runner_ids"]) != set(state["runners"])
    ):
        raise ValueError("ROOT_RECEIPT_BINDING")
    execution = evidence.document(receipt["root_execution_ref"], "execution")
    inspect_execution(execution, "root_inventory", None, inventory, evidence)
    if (
        inventory_ref not in execution["upstream_refs"]
        or inventory["source_freeze_ref"] not in execution["upstream_refs"]
    ):
        raise ValueError("ROOT_EXECUTION_BINDING")


def _utc_instant(value):
    # UTC schema permits arbitrary fractions; datetime alone truncates at 6 digits.
    whole, separator, fraction = value[:-1].partition(".")
    return datetime.fromisoformat(whole + "Z"), (
        Decimal("0." + fraction) if separator else Decimal(0)
    )


def inspect_execution(execution, kind, rid, inventory, evidence):
    if (
        execution["phase_id"],
        execution["kind"],
        execution["runner_id"],
        execution["exit_code"],
    ) != (inventory["phase_id"], kind, rid, 0):
        raise ValueError("EXECUTION_BINDING")
    if (
        _utc_instant(execution["finished_at"]) < _utc_instant(execution["started_at"])
        or not execution["argv"]
    ):
        raise ValueError("EXECUTION_TIMES")
    expected = [
        inventory[k]["inventory_ref"] for k in ("base_root_ref", "candidate_root_ref")
    ]
    if execution["observed_source_inventory_refs"] != expected:
        raise ValueError("OBSERVED_SOURCE_BINDING")
    unique_rows(execution["environment"], "name")
    for ref in artifact_refs(execution):
        evidence.artifact(ref)


def inspect_runner_inputs(evidence, inventory, state, record, source, config):
    rid = record["runner_id"]
    planned = state["runners"].get(rid)
    if (
        planned is None
        or (planned["stack"], planned["package"], planned["kind"])
        != (record["stack"], record["package"], "runner")
        or planned["tool_ref"] != record["tool"]["executable_ref"]
    ):
        raise ValueError("RUNNER_BINDING")
    if source["runner_id"] != rid or config["runner_id"] != rid:
        raise ValueError("RUNNER_BINDING")
    if (
        record["tool"]["lock_refs"] != state["freeze"]["tool_lock_refs"]
        or record["config_refs"] != config["config_refs"]
        or any(
            r not in state["freeze"]["runner_config_refs"]
            for r in config["config_refs"]
        )
    ):
        raise ValueError("CONFIG_BINDING")
    if (
        any(config[k] for k in ("omit_patterns", "exclude_lines", "ignore_patterns"))
        or config["include_patterns"]
    ):
        raise ValueError("EXCLUSIONS")
    if inventory["policy"]["branch_required"] and not config["branch"]:
        raise ValueError("BRANCH_DISABLED")
    if not config["source_roots"] or not config["test_nodes"]:
        raise ValueError("CONFIG_SCOPE")
    sources = unique_rows(source["files"], "path")
    if len({r["raw_key"] for r in sources.values()}) != len(sources):
        raise ValueError("RAW_ALIAS_AMBIGUOUS")
    in_roots = lambda p: any(
        p == r or p.startswith(r + "/") for r in config["source_roots"]
    )
    approved_exceptions = {r["path"] for r in inventory["policy"]["exceptions"]}
    expected = {
        p
        for p in state["candidate"]
        if in_roots(p)
        and p not in approved_exceptions
        and Path(p).suffix.lower()
        in (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
    }
    if set(sources) != expected:
        raise ValueError("SOURCE_SCOPE")
    for path, row in sources.items():
        if (
            path not in state["candidate"]
            or row["sha256"] != state["candidate"][path]["sha256"]
            or row["bytes"] != state["candidate"][path]["bytes"]
        ):
            raise ValueError("SOURCE_MISMATCH")
        data = _read_stable(
            evidence.path(inventory["candidate_root_ref"]["path"] + "/" + path)
        )
        if re.search(
            rb"(?i)(pragma\s*:\s*no\s*(?:cover|branch)|istanbul\s+ignore|v8\s+ignore|c8\s+ignore)",
            data,
        ):
            raise ValueError("SOURCE_PRAGMA")
    if record["stack"] == "python" and record["tool"]["name"] != "coverage.py":
        raise LookupError("TOOL_FORMAT_UNKNOWN")
    if (
        record["stack"] == "python"
        and record["tool"]["version"] not in COVERAGE_READERS
    ):
        raise LookupError("TOOL_FORMAT_UNKNOWN")
    if (
        record["stack"] == "istanbul"
        and (record["tool"]["name"], record["tool"]["version"]) not in ISTANBUL_READERS
    ):
        raise LookupError("TOOL_FORMAT_UNKNOWN")
    if record["stack"] == "istanbul" and record["summary_ref"] is None:
        raise LookupError("SUMMARY_MISSING")
    maps = unique_rows(record["source_maps"], "raw_key")
    if not set(maps) <= {r["raw_key"] for r in sources.values()}:
        raise ValueError("SOURCE_MAP_MISMATCH")
    for mapping in maps.values():
        for ref in artifact_refs(mapping):
            evidence.artifact(ref)
        source_map = load_json(evidence.artifact(mapping["map_ref"]))
        if (
            type(source_map) is not dict
            or source_map.get("version") != 3
            or type(source_map.get("sources")) is not list
            or len(source_map["sources"]) != 1
            or type(source_map.get("sourcesContent")) is not list
            or len(source_map["sourcesContent"]) != 1
            or type(source_map["sourcesContent"][0]) is not str
            or not source_map.get("mappings")
        ):
            raise ValueError("SOURCE_MAP_INVALID")
        if (
            hashlib.sha256(source_map["sourcesContent"][0].encode()).hexdigest()
            != mapping["original_ref"]["sha256"]
        ):
            raise ValueError("SOURCE_MAP_MISMATCH")
    for path, row in sources.items():
        if record["stack"] == "python":
            prefix = inventory["candidate_root_ref"]["path"]
            physical = evidence.path(prefix + "/" + path)
            allowed = {
                path,
                str(Path(path)),
                prefix + "/" + path,
                str(physical),
                physical.as_posix(),
            }
            if row["raw_key"] not in allowed:
                raise ValueError("RAW_ALIAS_AMBIGUOUS")
            if row["raw_key"] != path:
                receipt = evidence.document(record["receipt_ref"], "receipt")
                if receipt["cwd"] != prefix:
                    raise ValueError("RAW_ROOT_PREFIX_BINDING")
            continue
        if row["raw_key"] != path:
            mapping = maps.get(row["raw_key"])
            if mapping is None:
                raise LookupError("SOURCE_MAP_MISSING")
            if mapping["original_ref"]["sha256"] != row["sha256"]:
                raise ValueError("SOURCE_MAP_MISMATCH")


def inspect_runner_receipt(
    evidence, inventory, inventory_ref, state, record, source, config, observation
):
    receipt = evidence.document(record["receipt_ref"], "receipt")
    rid = record["runner_id"]
    if (
        receipt["runner_id"] != rid
        or receipt["phase_id"] != inventory["phase_id"]
        or receipt["exit_code"] != 0
        or receipt["inventory_sha256"] != inventory_ref["sha256"]
        or receipt["report_sha256"] != record["raw_report_ref"]["sha256"]
        or receipt["config_sha256"] != record["effective_config_ref"]["sha256"]
        or receipt["source_manifest_sha256"] != record["source_manifest_ref"]["sha256"]
        or receipt["tool_ref"] != record["tool"]["executable_ref"]
    ):
        raise ValueError("RUNNER_RECEIPT_BINDING")
    execution = evidence.document(receipt["root_execution_receipt_ref"], "execution")
    inspect_execution(execution, "runner", rid, inventory, evidence)
    for field in (
        "argv",
        "cwd",
        "environment",
        "started_at",
        "finished_at",
        "exit_code",
        "stdout_ref",
        "stderr_ref",
        "tool_ref",
    ):
        if receipt[field] != execution[field]:
            raise ValueError("RUNNER_EXECUTION_BINDING")
    outputs = [
        record[k]
        for k in ("raw_report_ref", "effective_config_ref", "source_manifest_ref")
    ]
    if (
        any(ref not in execution["output_refs"] for ref in outputs)
        or inventory_ref not in execution["upstream_refs"]
    ):
        raise ValueError("RUNNER_OUTPUT_BINDING")
    if observation is None:
        raise LookupError("ROOT_CUSTODY_MISSING")
    for mapping in record["source_maps"]:
        if (
            mapping["map_ref"] not in execution["output_refs"]
            or mapping["generated_ref"] not in execution["output_refs"]
        ):
            raise ValueError("SOURCE_MAP_OUTPUT_BINDING")
        matching = [
            r
            for r in source["files"]
            if r["raw_key"] == mapping["raw_key"]
            and r["sha256"] == mapping["original_ref"]["sha256"]
        ]
        if len(matching) != 1:
            raise ValueError("SOURCE_MAP_MISMATCH")
        mapping_expected = {
            "kind": "source_mapping",
            "mapping": mapping,
            "source": matching[0],
            "raw_report_ref": record["raw_report_ref"],
            "effective_config_ref": record["effective_config_ref"],
            "tool": record["tool"],
            "execution": execution,
            "source_freeze": state["freeze"],
        }
        try:
            mapped = observation.observe_mapping(mapping_expected)
        except AttributeError as exc:
            raise LookupError("MAPPING_OBSERVATION_MISSING") from exc
        verify_observation(evidence, mapped, mapping_expected)
    expected = {
        "kind": "runner",
        "inventory_ref": inventory_ref,
        "record": record,
        "receipt": receipt,
        "execution": execution,
        "source_manifest": source,
        "effective_config": config,
    }
    verify_observation(evidence, observation.observe_execution(expected), expected)


def verify_observation(evidence, observed, expected):
    if not isinstance(observed, ObservedEvidence) or observed.bindings != expected:
        raise ValueError("ROOT_OBSERVATION_MISMATCH")
    refs = list(artifact_refs(expected))
    if not refs or any(
        ref["path"] not in observed.artifact_bytes
        or observed.artifact_bytes[ref["path"]] != evidence.artifact(ref)
        for ref in refs
    ):
        raise ValueError("ROOT_OBSERVATION_BYTES")


@dataclass(frozen=True)
class ObservedEvidence:
    """Evidencia CPU del collector ROOT inyectado; nunca se carga desde JSON."""

    bindings: dict
    artifact_bytes: dict


def inspect_combined(
    evidence, inventory, inventory_ref, state, record, runners, observation
):
    planned = state["runners"].get(record["combined_id"])
    if (
        planned is None
        or planned["kind"] != "combine"
        or record["input_runner_ids"] != planned["input_runner_ids"]
        or not set(record["input_runner_ids"]) <= set(runners)
    ):
        raise ValueError("COMBINE_BINDING")
    cid = record["combined_id"]
    if record["stack"] != planned["stack"] or record["tool_ref"] != planned["tool_ref"]:
        raise ValueError("COMBINE_BINDING")
    receipt = evidence.document(record["receipt_ref"], "receipt")
    execution = evidence.document(receipt["root_execution_receipt_ref"], "execution")
    inspect_execution(execution, "combine", cid, inventory, evidence)
    source = evidence.document(record["source_manifest_ref"], "source")
    raw = load_json(evidence.artifact(record["raw_report_ref"]))
    if (
        source["runner_id"] != cid
        or receipt["runner_id"] != cid
        or receipt["inventory_sha256"] != inventory_ref["sha256"]
        or receipt["report_sha256"] != record["raw_report_ref"]["sha256"]
        or receipt["source_manifest_sha256"] != record["source_manifest_ref"]["sha256"]
        or receipt["tool_ref"] != record["tool_ref"]
    ):
        raise ValueError("COMBINE_RECEIPT_BINDING")
    config_refs = [
        r for r in execution["output_refs"] if r["sha256"] == receipt["config_sha256"]
    ]
    if len(config_refs) != 1:
        raise ValueError("COMBINE_CONFIG_BINDING")
    config = evidence.document(config_refs[0], "config")
    for field in (
        "argv",
        "cwd",
        "environment",
        "started_at",
        "finished_at",
        "exit_code",
        "stdout_ref",
        "stderr_ref",
        "tool_ref",
    ):
        if receipt[field] != execution[field]:
            raise ValueError("COMBINE_EXECUTION_BINDING")
    if inventory_ref not in execution["upstream_refs"] or any(
        ref not in execution["output_refs"]
        for ref in (record["raw_report_ref"], record["source_manifest_ref"])
    ):
        raise ValueError("COMBINE_OUTPUT_BINDING")
    for rid in record["input_runner_ids"]:
        runner = runners[rid]
        if (
            runner["stack"] != record["stack"]
            or runner["package"] != planned["package"]
            or runner["receipt_ref"] not in execution["upstream_refs"]
            or runner["raw_report_ref"] not in execution["upstream_refs"]
        ):
            raise ValueError("COMBINE_INPUT_BINDING")
        source_input = evidence.document(runner["source_manifest_ref"], "source")
        config_input = evidence.document(runner["effective_config_ref"], "config")
        if source_input["files"] != source["files"] or {
            k: v for k, v in config_input.items() if k != "runner_id"
        } != {k: v for k, v in config.items() if k != "runner_id"}:
            raise ValueError("COMBINE_SOURCE_CONFIG_MISMATCH")
    if observation is None:
        raise LookupError("ROOT_CUSTODY_MISSING")
    expected = {
        "kind": "combine",
        "inventory_ref": inventory_ref,
        "record": record,
        "receipt": receipt,
        "execution": execution,
        "source_manifest": source,
        "effective_config": config,
        "input_records": [runners[r] for r in record["input_runner_ids"]],
    }
    verify_observation(evidence, observation.observe_execution(expected), expected)
    result = {}
    input_tool = runners[record["input_runner_ids"][0]]["tool"]
    if type(raw) is not dict or (
        record["stack"] == "python" and type(raw.get("meta")) is not dict
    ):
        raise LookupError("RAW_INVALID")
    if (
        record["stack"] == "python"
        and raw.get("meta", {}).get("version") != input_tool["version"]
    ):
        raise ValueError("RAW_TOOL_VERSION_MISMATCH")
    for source_row in source["files"]:
        counts = (python_counts if record["stack"] == "python" else istanbul_counts)(
            raw, source_row["raw_key"], inventory["policy"]["branch_required"]
        )
        inspect_raw_source_range(evidence, inventory, record["stack"], raw, source_row)
        if counts["branches"] is None and inventory["policy"]["branch_required"]:
            adapter = {
                "receipt_ref": record["receipt_ref"],
                "raw_report_ref": record["raw_report_ref"],
                "effective_config_ref": config_refs[0],
                "source_manifest_ref": record["source_manifest_ref"],
                "tool": input_tool,
            }
            counts["branch_na_proof_ref"] = inspect_branch_proof(
                evidence, adapter, source_row, config, inventory, observation
            )
        result[source_row["path"]] = counts
    return result


def inspect_raw_source_range(evidence, inventory, stack, raw, source):
    import io
    import tokenize

    data = _read_stable(
        evidence.path(inventory["candidate_root_ref"]["path"] + "/" + source["path"])
    )
    encoding, _ = (
        tokenize.detect_encoding(io.BytesIO(data).readline)
        if stack == "python"
        else ("utf-8", None)
    )
    lines = data.decode(encoding).splitlines()
    f = raw["files"][source["raw_key"]] if stack == "python" else raw[source["raw_key"]]
    if stack == "python":
        numbers = f["executed_lines"] + f["missing_lines"]
        if any(number > len(lines) for number in numbers):
            raise ValueError("RAW_SOURCE_RANGE")
        if any(
            abs(number) > len(lines) + 1
            for pair in f.get("executed_branches", []) + f.get("missing_branches", [])
            for number in pair
        ):
            raise ValueError("RAW_SOURCE_RANGE")
    else:
        locations = (
            list(f["statementMap"].values())
            + [x[key] for x in f["fnMap"].values() for key in ("decl", "loc")]
            + [loc for x in f["branchMap"].values() for loc in x["locations"]]
        )
        for location in locations:
            for point in location.values():
                if (
                    point["line"] > len(lines)
                    or point["column"]
                    > len(lines[point["line"] - 1].encode("utf-16-le")) // 2
                ):
                    raise ValueError("RAW_SOURCE_RANGE")


def inspect_branch_proof(evidence, record, source_row, config, inventory, observation):
    if observation is None or not config["branch"]:
        raise LookupError("BRANCH_PROOF_MISSING")
    receipt = evidence.document(record["receipt_ref"], "receipt")
    execution = evidence.document(receipt["root_execution_receipt_ref"], "execution")
    expected = {
        "kind": "branch_not_applicable",
        "source": source_row,
        "raw_report_ref": record["raw_report_ref"],
        "effective_config_ref": record["effective_config_ref"],
        "tool": record["tool"],
        "execution": execution,
    }
    observed = observation.branch_proof(expected)
    if not isinstance(observed, ObservedEvidence) or set(observed.bindings) != set(
        expected
    ) | {"proof_ref"}:
        raise ValueError("BRANCH_OBSERVATION_MISMATCH")
    proof = observed.bindings["proof_ref"]
    validate_schema("artifact", proof)
    if proof not in execution["output_refs"] or proof in [
        record["raw_report_ref"],
        record["effective_config_ref"],
        record["source_manifest_ref"],
    ]:
        raise ValueError("BRANCH_PROOF_BINDING")
    expected = dict(expected, proof_ref=proof)
    verify_observation(evidence, observed, expected)
    evidence.artifact(proof).decode("utf-8")
    return proof


def main(argv=None, observation=None):
    import argparse

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise ValueError("CLI_ARGUMENTS_INVALID")

    parser = Parser(
        description="Cobertura whole M3 con evidencia ROOT independiente.",
        allow_abbrev=False,
    )
    for flag in ("inventory", "reports", "helper"):
        parser.add_argument("--" + flag, required=True)
    parser.add_argument("--helper-exit", type=int, required=True)
    parser.add_argument("--min", type=int, required=True)
    parser.add_argument("--json", action="store_true", required=True)
    try:
        args = parser.parse_args(argv)
        result = evaluate(
            args.inventory,
            args.reports,
            args.helper,
            args.helper_exit,
            args.min,
            observation,
        )
    except ValueError:
        result = {
            "schema_version": 1,
            "phase_id": None,
            "inventory_sha256": None,
            "reports_sha256": None,
            "helper_sha256": None,
            "helper_exit": 2,
            "applies": True,
            "verdict": "fail",
            "exit_code": 1,
            "files": [],
            "exceptions": [],
            "missing": [],
            "ambiguous": [],
            "exclusions": [],
            "stacks": [],
            "errors": [
                {"code": "CLI_ARGUMENTS_INVALID", "path": None, "proof_ref": None}
            ],
        }
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return result["exit_code"]


if __name__ == "__main__":
    # Caller-owned embedding seam: no persisted data grants custody.
    factory = globals().get("_root_observer_factory")
    observation = factory(ObservedEvidence) if callable(factory) else None
    raise SystemExit(main(observation=observation))
