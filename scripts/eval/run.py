"""Batería CPU de M0: plan reproducible, transporte /v1 y custodia ciega."""

import argparse
import copy
import json
import re
import secrets
import shutil
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx
import yaml
from engine_contract import Event, Health, JobRequest, ModelDescriptor
from jsonschema import validate

from scripts import generate
from scripts import input_preparation as preparation
from scripts.eval import metrics
from scripts.eval.metrics import confined, exclusive_json, file_hash

ROOT = Path(__file__).resolve().parents[2]
SEEDS = (101, 202, 303)
VERSION = "evaluation-plan-v1"
KNOWN_CANDIDATES = {"ace-step-1.5-turbo", "ace-step-1.5-base", "ace-step-1.5-sft"}
CANONICAL = (
    (45, 112, "es"),
    (180, 84, "es"),
    (30, 96, "es"),
    (120, 92, "en"),
    (150, 68, "es"),
    (30, 124, "es"),
    (150, 140, "en"),
    (40, 100, "es"),
    (165, 76, "en"),
    (90, 110, "en"),
)


def seal_plan(plan):
    value = copy.deepcopy(plan)
    value.pop("hash", None)
    value["hash"] = preparation.digest(preparation.encode(value))
    return value


def literal_briefs():
    document = confined(ROOT / "docs/calidad/evaluacion-escucha.md", ROOT)
    text = document.read_text(encoding="utf-8-sig")
    rows = [line for line in text.splitlines() if line.startswith("| B-")]
    if len(rows) != 10:
        raise ValueError("CANONICAL_BRIEFS_INVALID")
    return {line.split("|")[1].strip(): line for line in rows}, file_hash(document)


def resolve_descriptor(descriptors, candidate, task):
    parsed = [
        ModelDescriptor.model_validate(d).model_dump(mode="json") for d in descriptors
    ]
    matches = [
        d
        for d in parsed
        if d["id"] == candidate
        and d["provider"]["type"] == "local"
        and task in d["tasks"]
    ]
    if len(matches) != 1:
        raise ValueError("CANDIDATE_UNAVAILABLE")
    model = matches[0]
    if not model["tasks"][task]["verified"]:
        raise ValueError("CAPABILITY_UNVERIFIED")
    if not model["modes"]:
        raise ValueError("MODE_UNAVAILABLE")
    return model


def build_plan(candidate, *, root=ROOT, known_candidates=None, descriptors=None):
    root = Path(root).absolute()
    known = KNOWN_CANDIDATES if known_candidates is None else known_candidates
    if candidate not in known and descriptors is None:
        raise ValueError("UNKNOWN_CANDIDATE")
    model = (
        resolve_descriptor(descriptors, candidate, "music.song")
        if descriptors is not None
        else None
    )
    path = confined(root / "eval/briefs/briefs.yaml", root)
    raw = path.read_bytes()
    catalog = yaml.safe_load(raw)
    if (
        not isinstance(catalog, dict)
        or catalog.get("version") != 1
        or not isinstance(catalog.get("briefs"), dict)
    ):
        raise ValueError("CATALOG_SCHEMA_INVALID")
    if set(catalog["briefs"]) - {f"B-{i:02}" for i in range(1, 11)}:
        raise ValueError("CATALOG_SCHEMA_INVALID")
    literal, document_hash = literal_briefs()
    rows = []
    for i, (duration, bpm, language) in enumerate(CANONICAL, 1):
        code = f"B-{i:02}"
        entry = catalog["briefs"].get(code)
        diagnostics, request, receipt = [], None, None
        lyrics_path = confined(root / f"eval/briefs/{code}.txt", root)
        if entry is None:
            diagnostics.append("MISSING_INPUT")
        else:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("style"), str)
                or not entry["style"].strip()
                or entry.get("task", "music.song") != "music.song"
                or (entry.get("duration_s"), entry.get("bpm"), entry.get("language"))
                != (duration, bpm, language)
            ):
                raise ValueError("CATALOG_SCHEMA_INVALID")
            if entry.get("lyrics_declaration") not in {
                None,
                "own",
                "assistant",
                "public_domain",
                "licensed",
            }:
                raise ValueError("CATALOG_SCHEMA_INVALID")
            if entry.get("lyrics_declaration") is None:
                diagnostics.append("MISSING_DECLARATION")
        if not lyrics_path.is_file():
            diagnostics.append("MISSING_LYRICS")
        if not diagnostics:
            request = generate.read_request(
                ["--brief", code, "--seed", "101"], root=root
            )
            receipt = request.pop("_preparation")
            request.pop("_prepare_only")
            if model:
                validate(
                    request["params"], model["tasks"]["music.song"]["params_schema"]
                )
        for seed in SEEDS:
            effective = copy.deepcopy(request)
            bound = None
            if effective:
                effective["seed"] = seed
                # Reuse original bytes preserved by read_request; never re-prepare a transformed input.
                bound = copy.deepcopy(receipt)
                bound["original"]["seed"] = seed
                bound["effective"]["seed"] = seed
                bound["effective_request_sha256"] = preparation.digest(
                    preparation.encode(bound["effective"])
                )
                preparation.validate_receipt(bound)
            rows.append(
                {
                    "brief_id": code,
                    "seed": seed,
                    "literal_brief": literal[code],
                    "catalog_style": entry["style"] if entry else None,
                    "request": effective,
                    "preparation": bound,
                    "diagnostics": diagnostics.copy(),
                    "status": "PLANNED_NOT_READY"
                    if diagnostics or model is None
                    else "PLANNED",
                }
            )
    sources = {
        "catalog": {"sha256": preparation.digest(raw), "bytes": len(raw)},
        "brief_document_sha256": document_hash,
    }
    return seal_plan(
        {
            "version": VERSION,
            "candidate": candidate,
            "descriptor": model,
            "sources": sources,
            "seeds": list(SEEDS),
            "rows": rows,
            "floor_status": "PENDING",
            "acceptance": None,
        }
    )


class V1Transport:
    """Controlador M0 sin BD: modelo explícito, no retries de submit ni post limiter."""

    def __init__(self, *, root, config, url, client):
        self.root = Path(root).absolute()
        self.data = confined(
            self.root / config.get("STUDIO_DATA_DIR", "data"), self.root
        )
        self.url = generate.engine_url({"engine": url}, config)
        token = config.get("STUDIO_ENGINE_TOKEN")
        if not token:
            raise ValueError("ENGINE_TOKEN_REQUIRED")
        self.headers = {"X-Studio-Engine-Token": token}
        self.client = client

    @staticmethod
    def remaining(deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("TIMEOUT")
        return remaining

    def chunks(self, response, deadline):
        # iter_lines buffers incomplete lines indefinitely. Each native network
        # read instead has a finite timeout; every returned byte block checks the
        # absolute deadline, including keepalive/partial-line traffic.
        try:
            for chunk in response.iter_bytes():
                self.remaining(deadline)
                yield chunk
            self.remaining(deadline)
        except httpx.TimeoutException:
            raise ValueError("TIMEOUT") from None

    def call(self, method, path, *, deadline=None, **kwargs):
        if deadline is None:
            deadline = time.monotonic() + kwargs.pop("timeout", 10)
        timeout = min(1, self.remaining(deadline))
        with self.client.stream(
            method, self.url + path, headers=self.headers, timeout=timeout, **kwargs
        ) as response:
            if response.status_code >= 400:
                raise ValueError("ENGINE_HTTP_" + str(response.status_code))
            body = bytearray()
            for chunk in self.chunks(response, deadline):
                body.extend(chunk)
                if len(body) > 8 * 1024 * 1024:
                    raise ValueError("ENGINE_RESPONSE_TOO_LARGE")
            return json.loads(body)

    def event_batches(self, response, deadline):
        pending = bytearray()
        for chunk in self.chunks(response, deadline):
            pending.extend(chunk)
            if len(pending) > 1024 * 1024:
                raise ValueError("ENGINE_EVENT_TOO_LARGE")
            lines = []
            while b"\n" in pending:
                line, _, rest = pending.partition(b"\n")
                pending = bytearray(rest)
                self.remaining(deadline)
                if line.strip():
                    lines.append(line)
            if lines:
                yield lines, bool(pending.strip())
        if pending.strip():
            self.remaining(deadline)
            yield [bytes(pending)], False

    def __call__(self, request, *, job_id, descriptor, inputs=None):
        model = resolve_descriptor([descriptor], descriptor["id"], request["task"])
        validate(request["params"], model["tasks"][request["task"]]["params_schema"])
        if model["tasks"][request["task"]]["device"] != "cpu":
            raise ValueError("REAL_GPU_PREFLIGHT_DEFERRED")
        started = time.monotonic()
        deadline = started + 60
        health = Health.model_validate(
            self.call("GET", "/v1/health", deadline=deadline)
        )
        if (
            health.state != "idle"
            or health.loaded is not None
            or health.job_id is not None
        ):
            raise ValueError("ENGINE_NOT_UNLOADED_IDLE")
        actual = resolve_descriptor(
            self.call("GET", "/v1/models", deadline=deadline),
            model["id"],
            request["task"],
        )
        if actual != model:
            raise ValueError("DESCRIPTOR_MISMATCH")
        mode = "cpu" if any(m["id"] == "cpu" for m in model["modes"]) else "bf16"
        job = JobRequest(
            job_id=job_id,
            task=request["task"],
            model_id=model["id"],
            mode=mode,
            inputs=inputs or [],
            params=request["params"],
            seed=request.get("seed"),
            output_dir=f"tmp/{job_id}/",
            timeout_s=60,
        )
        estimate = self.call(
            "POST", "/v1/estimate", deadline=deadline, json=job.model_dump(mode="json")
        )
        intent = confined(self.data / f"tmp/{job_id}/controller-intent.json", self.root)
        exclusive_json(
            intent,
            {
                "job": job.model_dump(mode="json"),
                "descriptor": model,
                "estimate": estimate,
                "status": "SUBMIT_INTENT_NO_RETRY",
            },
        )
        submitted = False
        ack_received = False
        failure = None
        events = []
        try:
            # Intent durable avant submit: timeout/unknown ACK retains same job identity.
            submitted = True
            try:
                ack = self.call(
                    "POST",
                    "/v1/jobs",
                    deadline=deadline,
                    json=job.model_dump(mode="json"),
                )
            except (httpx.HTTPError, ValueError) as error:
                if isinstance(error, ValueError) and str(error) != "TIMEOUT":
                    raise
                raise ValueError("SUBMIT_ACK_UNKNOWN") from None
            if ack.get("job_id") != job_id:
                raise ValueError("ENGINE_JOB_MISMATCH")
            ack_received = True
            terminal = None
            last = 0
            while terminal is None:
                if time.monotonic() >= deadline:
                    raise ValueError("TIMEOUT")
                try:
                    with self.client.stream(
                        "GET",
                        self.url + f"/v1/jobs/{job_id}/events",
                        params={"after": last},
                        headers=self.headers,
                        timeout=min(1, self.remaining(deadline)),
                    ) as response:
                        if response.status_code >= 400:
                            raise ValueError("ENGINE_HTTP_" + str(response.status_code))
                        for lines, partial in self.event_batches(response, deadline):
                            for line in lines:
                                self.remaining(deadline)
                                event = Event.model_validate_json(line)
                                if (
                                    event.job_id != job_id
                                    or event.seq != last + 1
                                    or terminal is not None
                                ):
                                    raise ValueError("ENGINE_EVENT_INVALID")
                                last = event.seq
                                events.append(event.model_dump(mode="json"))
                                if event.type in {"done", "error", "cancelled"}:
                                    terminal = event
                            if terminal is not None:
                                if partial:
                                    raise ValueError("ENGINE_EVENT_INVALID")
                                break  # Terminal does not require peer EOF/keepalive closure.
                except (ValueError, httpx.TimeoutException) as error:
                    if isinstance(error, ValueError) and str(error) != "TIMEOUT":
                        raise
                    # A quiet stream may reconnect at the last validated sequence.
                    # Discard incomplete bytes; the provider replays that event.
                    self.remaining(deadline)
                if terminal is None:
                    time.sleep(0.01)
            exclusive_json(intent.parent / "controller-events.json", events)
            if terminal.type != "done":
                raise ValueError(terminal.data.get("code", "CANCELLED"))
            done = terminal.data
            if len(done["artifacts"]) != 1 or done["artifacts"][0]["output_index"] != 0:
                raise ValueError("ENGINE_OUTPUTS_INVALID")
            artifact = done["artifacts"][0]
            if not artifact["path"].startswith(f"tmp/{job_id}/"):
                raise ValueError("ENGINE_ARTIFACT_INVALID")
            source = confined(self.data / artifact["path"], self.root)
            if file_hash(source) != artifact["sha256"]:
                raise ValueError("HASH_MISMATCH")
            receipts = generate.publish_input_receipts(
                done.get("result"), self.data, job_id, job.model_dump(mode="json"), 1
            )
            if request["task"] == "music.song":
                if (
                    artifact["media_type"] != "audio/wav"
                    or artifact["meta"].get("seed") != job.seed
                ):
                    raise ValueError("ENGINE_ARTIFACT_INVALID")
                metrics.audio_record(
                    source, expected_duration=request["params"]["duration_s"]
                )
            return {
                "source": str(source),
                "sha256": artifact["sha256"],
                "job_id": job_id,
                "model_id": model["id"],
                "descriptor": model,
                "planned_estimate": estimate,
                "captured_receipts": receipts,
                "telemetry": done["telemetry"],
                "run_s": time.monotonic() - started,
                "synthetic": model["family"] == "mock",
            }
        except BaseException as error:
            failure = error
            if not (intent.parent / "controller-events.json").exists():
                exclusive_json(intent.parent / "controller-events.json", events)
            exclusive_json(
                intent.parent / "controller-outcome.json",
                {
                    "job_id": job_id,
                    "status": "TERMINAL_FAILURE"
                    if ack_received
                    else "SUBMIT_ACK_UNKNOWN",
                    "error_type": type(error).__name__,
                    "retry_submit": False,
                },
            )
            raise
        finally:
            if submitted:
                try:
                    generate.finish_job(
                        self.call, job_id, model["id"], mode, cancel=True, timeout_s=10
                    )
                except (
                    ValueError,
                    OSError,
                    RuntimeError,
                    httpx.HTTPError,
                    KeyboardInterrupt,
                ):
                    exclusive_json(
                        intent.parent / "controller-cleanup-unconfirmed.json",
                        {
                            "job_id": job_id,
                            "status": "CLEANUP_UNCONFIRMED",
                            "retry_submit": False,
                        },
                    )
                    if failure is None:
                        raise ValueError("ENGINE_CLEANUP_UNCONFIRMED") from None
                    failure.add_note("ENGINE_CLEANUP_UNCONFIRMED")


def measure_take(
    source, request, *, root, transport, descriptors, bindings, floor=None
):
    """Tres jobs seriales con bindings explícitos; errores observables por métrica."""
    result = {}
    tasks = ("audio.transcribe", "audio.clap", "audio.aesthetics")
    if set(bindings) != set(tasks):
        raise ValueError("METRIC_BINDINGS_REQUIRED")
    params = request["params"]
    for task in tasks:
        job_id = generate.ulid()
        try:
            model = resolve_descriptor(descriptors, bindings[task], task)
            values = metrics.metric_request(
                task, language=params["language"], style=params["style"]
            )
            validate(values, model["tasks"][task]["params_schema"])
            staged = metrics.stage_audio(source, Path(root) / "data", job_id, root=root)
            captured = transport(
                {"task": task, "params": values, "seed": None},
                job_id=job_id,
                descriptor=model,
                inputs=[staged],
            )
            if captured["job_id"] != job_id or captured["model_id"] != model["id"]:
                raise ValueError("METRIC_BINDING_MISMATCH")
            output = confined(captured["source"], root)
            if file_hash(output) != captured["sha256"] or not output.is_relative_to(
                Path(root).absolute() / f"data/tmp/{job_id}"
            ):
                raise ValueError("HASH_MISMATCH")
            payload = json.loads(output.read_text(encoding="utf-8"))
            if (
                not isinstance(payload, dict)
                or not isinstance(payload.get("stages"), list)
                or not payload["stages"]
                or not all(isinstance(stage, dict) for stage in payload["stages"])
            ):
                raise ValueError("METRIC_OUTPUT_INVALID")
            if (
                payload.get("task") != task
                or not payload.get("stages")
                or payload["stages"][0].get("model_id") != model["id"]
                or payload["stages"][0].get("revision") != model["revision"]
                or payload["stages"][0].get("task") != task
            ):
                raise ValueError("METRIC_PROVENANCE_MISMATCH")
            adjusted_floor = None
            profile = preparation.digest(
                preparation.encode(
                    {
                        "descriptor": model,
                        "stages": payload["stages"],
                        "coverage": "whole_recording",
                        "normalization": metrics.NORMALIZATION,
                    }
                )
            )
            if floor is not None and task == "audio.transcribe":
                if (
                    floor.get("model_id") != model["id"]
                    or floor.get("status") != "MEASURED"
                    or floor.get("normalization") != metrics.NORMALIZATION
                    or not floor.get("bindings")
                    or floor.get("profile") != profile
                ):
                    raise ValueError("FLOOR_PROFILE_MISMATCH")
                # No trusted, controlled real-corpus execution currently exists.
                # A caller-supplied MEASURED dictionary cannot authorize a rebate.
                raise ValueError("FLOOR_CONTROLLED_EXECUTION_PENDING")
            value = metrics.native_metric(
                task,
                payload,
                reference=params["lyrics"],
                language=params["language"],
                floor=adjusted_floor,
            )
            result[task] = {
                "status": "MEASURED",
                "value": value,
                "job_id": job_id,
                "descriptor": model,
                "input": staged,
                "output_sha256": captured["sha256"],
                "synthetic": captured.get("synthetic", False),
                "acceptance": None,
                "profile": profile,
            }
        except (ValueError, OSError, KeyError, httpx.HTTPError) as error:
            result[task] = {
                "status": "ERROR",
                "job_id": job_id,
                "error": str(error)
                if isinstance(error, ValueError)
                else type(error).__name__,
            }
    return result


def execute(
    plan,
    *,
    root=ROOT,
    transport=None,
    allow_synthetic=False,
    normalization=None,
    metric_runner=None,
):
    root = Path(root).absolute()
    if (
        plan.get("version") != VERSION
        or plan.get("seeds") != list(SEEDS)
        or not isinstance(plan.get("rows"), list)
    ):
        raise ValueError("PLAN_SCHEMA_INVALID")
    if seal_plan(plan)["hash"] != plan.get("hash"):
        raise ValueError("PLAN_HASH_MISMATCH")
    if any(row["diagnostics"] for row in plan["rows"]):
        raise ValueError("PREREQUISITES_PENDING")
    if (
        file_hash(confined(root / "eval/briefs/briefs.yaml", root))
        != plan["sources"]["catalog"]["sha256"]
    ):
        raise ValueError("SOURCE_CATALOG_MISMATCH")
    for row in plan["rows"]:
        lyrics = confined(root / f"eval/briefs/{row['brief_id']}.txt", root)
        if (
            file_hash(lyrics)
            != row["preparation"]["fields"]["lyrics"]["original_bytes_sha256"]
        ):
            raise ValueError("SOURCE_LYRICS_MISMATCH")
    model = plan["descriptor"]
    if not allow_synthetic:
        if plan["floor_status"] != "MEASURED" or model is None:
            raise ValueError("PREREQUISITES_PENDING_FLOOR_DESCRIPTOR")
        raise ValueError("REAL_GPU_PREFLIGHT_DEFERRED")
    if model is None:
        from engine_mock import descriptor

        model = resolve_descriptor(
            [descriptor().model_dump(mode="json")], plan["candidate"], "music.song"
        )
    if model["family"] != "mock" or transport is None:
        raise ValueError("SYNTHETIC_BINDING_REQUIRED")
    if len(plan["rows"]) != 30 or [
        (r["brief_id"], r["seed"]) for r in plan["rows"]
    ] != [(f"B-{i:02}", s) for i in range(1, 11) for s in SEEDS]:
        raise ValueError("PLAN_SLOTS_INVALID")
    session_id = generate.ulid()
    folder = confined(root / f"eval/takes/{session_id}", root)
    folder.mkdir(parents=True)
    exclusive_json(folder / "plan.json", plan)
    takes = []
    for index, row in enumerate(plan["rows"]):
        job_id = generate.ulid()
        identity = f"{session_id}:{index}"
        request = row["request"]
        preparation.validate_receipt(row["preparation"])
        if row["preparation"]["effective"] != request or request["seed"] != row["seed"]:
            raise ValueError("PREPARATION_REQUEST_MISMATCH")
        take = {
            "identity": identity,
            "brief_id": row["brief_id"],
            "candidate": plan["candidate"],
            "seed": row["seed"],
            "job_id": job_id,
            "synthetic": True,
            "status": "PENDING",
            "metrics": None,
            "blind_ready": False,
        }
        # No resume API: cada ejecución crea IDs nuevos; un intento incierto no se reenvía.
        exclusive_json(
            folder / f"intent-{index:02}.json", {"row": row, "job_id": job_id}
        )
        try:
            result = transport(request, job_id=job_id, descriptor=model)
            if (
                result["job_id"] != job_id
                or result["model_id"] != plan["candidate"]
                or result.get("synthetic") is not True
            ):
                raise ValueError("CAPTURED_BINDING_MISMATCH")
            source = confined(result["source"], root)
            if file_hash(source) != result["sha256"]:
                raise ValueError("HASH_MISMATCH")
            audio = metrics.audio_record(
                source, expected_duration=request["params"]["duration_s"]
            )
            raw = folder / f"raw-{index:02}.wav"
            with source.open("rb") as original, raw.open("xb") as copied:
                shutil.copyfileobj(original, copied)
            if file_hash(raw) != result["sha256"]:
                raise ValueError("HASH_MISMATCH")
            take.update(
                source=str(raw),
                sha256=file_hash(raw),
                provenance=result,
                audio=audio,
                status="RAW_ONLY_PENDING_LOUDNESS_METRICS",
            )
            if normalization:
                scaled = folder / f"scaled-{index:02}.wav"
                measured = normalization(raw, scaled, root=root)
                take["loudness"] = measured
                if (
                    measured["blind_ready"]
                    and not audio["silent"]
                    and not audio["over_fullscale"]
                ):
                    take.update(
                        source=str(scaled),
                        sha256=file_hash(scaled),
                        blind_ready=True,
                        status="BLIND_READY_METRICS_PENDING",
                    )
            if metric_runner:
                take["metrics"] = metric_runner(raw, request, root=root)
        except (ValueError, OSError, httpx.HTTPError) as error:
            take.update(
                status="ERROR",
                error=type(error).__name__ + ":" + str(error)
                if isinstance(error, ValueError)
                else type(error).__name__,
            )
        exclusive_json(folder / f"take-{index:02}.json", take)
        takes.append(take)
    ready = [t for t in takes if t["blind_ready"]]
    if ready:
        anonymize(ready, folder / "collection", root=root, planned_takes=takes)
    report = {
        "session_id": session_id,
        "plan_hash": plan["hash"],
        "takes": takes,
        "acceptance": None,
        "scope": "SYNTHETIC_CPU_ONLY",
        "human_selection": None,
    }
    exclusive_json(folder / "report.json", report)
    return report


def anonymize(takes, folder, *, root=ROOT, planned_takes=None):
    folder = confined(folder, root)
    planned_takes = takes if planned_takes is None else planned_takes
    identities = [t["identity"] for t in planned_takes]
    if len(set(identities)) != len(identities) or not {
        t["identity"] for t in takes
    } <= set(identities):
        raise ValueError("BLIND_PLAN_INVALID")
    bindings = [
        {k: t.get(k) for k in ("identity", "brief_id", "candidate", "seed")}
        for t in planned_takes
    ]
    group_plan = folder / "private.groups.json"
    if group_plan.exists():
        groups = json.loads(group_plan.read_text(encoding="utf-8"))
        if [b for g in groups for b in g["members"]] != bindings:
            # Compare by identity: briefs may be interleaved in a plan.
            persisted = {b["identity"]: b for g in groups for b in g["members"]}
            if persisted != {b["identity"]: b for b in bindings}:
                raise ValueError("BLIND_RESUME_MISMATCH")
    else:
        groups = []
        used = set()
        for binding in bindings:
            key = (binding["brief_id"] or binding["identity"], binding["candidate"])
            group = next((g for g in groups if tuple(g["key"]) == key), None)
            if group is None:
                for _ in range(100):
                    code = "N" + secrets.token_hex(16)
                    if code not in used:
                        used.add(code)
                        break
                else:
                    raise ValueError("BLIND_CODE_COLLISION")
                group = {"key": list(key), "group": code, "members": []}
                groups.append(group)
            group["members"].append(binding)
        exclusive_json(group_plan, groups)
    group_by_identity = {
        b["identity"]: g["group"] for g in groups for b in g["members"]
    }
    for take in takes:
        source = confined(take["source"], root)
        if file_hash(source) != take["sha256"]:
            raise ValueError("HASH_MISMATCH")
        audio = metrics.audio_record(source)
        if audio["silent"] or audio["over_fullscale"]:
            raise ValueError("AUDIO_NOT_BLIND_READY")
    private = folder / "private.map.json"
    if private.exists():
        mapping = json.loads(private.read_text(encoding="utf-8"))
        if [(m["identity"], m["sha256"]) for m in mapping] != [
            (t["identity"], t["sha256"]) for t in takes
        ]:
            raise ValueError("BLIND_RESUME_MISMATCH")
        if len({m["code"] for m in mapping}) != len(mapping) or any(
            not re.fullmatch(r"N[0-9a-f]{32}", m["code"])
            or m["source"] != t["source"]
            or m.get("group") != group_by_identity[t["identity"]]
            or any(m.get(k) != t.get(k) for k in ("brief_id", "candidate", "seed"))
            for m, t in zip(mapping, takes, strict=True)
        ):
            raise ValueError("BLIND_MAP_INVALID")
    else:
        used = {g["group"] for g in groups}

        def neutral_code():
            for _ in range(100):
                code = "N" + secrets.token_hex(16)
                if code not in used:
                    used.add(code)
                    return code
            raise ValueError("BLIND_CODE_COLLISION")

        mapping = []
        for take in takes:
            mapping.append(
                dict(
                    take, code=neutral_code(), group=group_by_identity[take["identity"]]
                )
            )
        exclusive_json(private, mapping)
    blind = folder / "blind"
    blind.mkdir(exist_ok=True)
    for row in mapping:
        destination = confined(blind / (row["code"] + ".wav"), root)
        if destination.exists():
            if file_hash(destination) != row["sha256"]:
                raise ValueError("HASH_MISMATCH")
            continue
        with (
            confined(row["source"], root).open("rb") as original,
            destination.open("xb") as copied,
        ):
            shutil.copyfileobj(original, copied)
        if file_hash(blind / (row["code"] + ".wav")) != row["sha256"]:
            raise ValueError("HASH_MISMATCH")
    sheet = [
        "# Hoja ciega — pendiente de escucha",
        "",
        "Selección best-of-3: pendiente en otra sesión (≥24 h o sesión distinta).",
        "Sistema/volumen: ______. Todo 5: explicar por qué no 4. D5≥4: uso concreto.",
        "D1 adecuación · D2 mezcla/artefactos · D3 estructura · D4 letra · D5 uso.",
        "Umbrales posteriores: D5≥4 en ≥7/10; medias D1–D5≥3; WER ajustado medio≤15%, peor≤25%.",
        "Sin suelo real: WER ajustado pendiente. Sin selección automática ni apertura del mapa.",
        "",
        "| Dim. | Qué se juzga | 3 = | 5 = |",
        "|---|---|---|---|",
    ]
    rubric = confined(ROOT / "docs/calidad/evaluacion-escucha.md", ROOT).read_text(
        encoding="utf-8-sig"
    )
    sheet += [line for line in rubric.splitlines() if line.startswith("| **D")]
    sheet += [
        "",
        "CLAP: ventana 10 s rand_trunc, semilla no controlada; no score de toda la pista.",
        "",
        "| Código | Audio | WER bruto | WER ajustado | CLAP | PQ | PC | CE | CU | D1 | D2 | D3 | D4 | D5 | Justificación/uso | Cumplimiento/tiempo | naturalidad/tiempo |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    public_rows = list(mapping)
    secrets.SystemRandom().shuffle(public_rows)
    for row in public_rows:
        code = row["code"]
        measured = row.get("metrics") or {}

        def value(task, axis, measured=measured):
            result = measured.get(task, {})
            for key in axis:
                result = result.get(key, {}) if isinstance(result, dict) else None
            return f"{result:.4f}" if type(result) in {int, float} else "PENDING"

        scores = [
            value("audio.transcribe", ("value", "wer", axis))
            for axis in ("raw", "adjusted")
        ]
        scores += [value("audio.clap", ("value", "clap"))]
        scores += [
            value("audio.aesthetics", ("value", "audiobox", axis))
            for axis in ("PQ", "PC", "CE", "CU")
        ]
        sheet.append(
            f"| {code} | [{code}.wav]({code}.wav) | "
            + " | ".join(scores)
            + " | | | | | | | | |"
        )
    sheet += [
        "",
        "Final/outro y arco: requieren toma completa; fragmentos no acreditan resolución.",
    ]
    selection = folder / "selection-pending.json"
    if not selection.exists():
        public_groups = []
        for planned_group in groups:
            group = planned_group["group"]
            members = [row for row in mapping if row["group"] == group]
            codes = [row["code"] for row in members]
            secrets.SystemRandom().shuffle(codes)
            seeds = {row.get("seed") for row in members}
            public_groups.append(
                {
                    "group": group,
                    "codes": codes,
                    "complete": len(members) == 3 and seeds == set(SEEDS),
                    "expected_count": 3,
                    "missing_count": max(0, 3 - len(members)),
                    "chosen": None,
                    "session": None,
                }
            )
        secrets.SystemRandom().shuffle(public_groups)
        exclusive_json(
            selection,
            {
                "groups": public_groups,
                "revealed": False,
            },
        )
    selection_data = json.loads(selection.read_text(encoding="utf-8"))
    sheet += ["", "| Grupo | Códigos | Estado |", "|---|---|---|"]
    for group in selection_data["groups"]:
        expected = {r["code"] for r in mapping if r["group"] == group["group"]}
        if set(group["codes"]) != expected:
            raise ValueError("BLIND_RESUME_MISMATCH")
        status = (
            "completo"
            if group["complete"]
            else f"incompleto: faltan {group['missing_count']}"
        )
        sheet.append(
            f"| {group['group']} | {', '.join(group['codes']) or 'sin audio'} | {status} |"
        )
    if not (blind / "sheet.md").exists():
        with (blind / "sheet.md").open("x", encoding="utf-8") as output:
            output.write("\n".join(sheet) + "\n")
    return [{"code": row["code"], "sha256": row["sha256"]} for row in mapping]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.candidate)
        if args.dry_run:
            for row in plan["rows"]:
                print(
                    f"{row['brief_id']} seed={row['seed']} PLANNED_NOT_READY "
                    + ",".join(row["diagnostics"] or ["DESCRIPTOR_PENDING"])
                )
            print(
                "30 posiciones planificadas; suelo WER, descriptor y preflight real pendientes. Sin inferencia."
            )
            return 0
        execute(plan)
    except (ValueError, OSError, yaml.YAMLError) as error:
        print(
            "Evaluación bloqueada: "
            + (str(error) if isinstance(error, ValueError) else type(error).__name__),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
