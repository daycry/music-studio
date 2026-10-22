"""Ejecución real por /v1 o supervisor hijo privado; no simula música."""

import shutil
import sys
import time
from pathlib import Path

# T-09 usa imports de script; esta raíz también existe en ``python -m`` y el hijo.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.eval.benchmark_runtime import ApiError
from scripts.eval.capabilities_evidence import exclusive_json, file_record
from scripts.eval.capabilities_native import contained, validate_lora
from scripts.eval.capabilities_plan import data_relative, request_for


def copy_outputs(row, artifacts, root, folder):
    outputs = []
    raw = (Path(root) / "data" / "tmp" / row["job_id"]).resolve()
    for artifact in artifacts:
        source = contained(Path(root) / "data", data_relative(artifact["path"]))
        if not source.is_relative_to(raw) or not source.is_file():
            raise ValueError("output_not_raw_job")
        seal = file_record(source)
        if artifact.get("sha256") and seal["sha256"] != artifact["sha256"]:
            raise ValueError("output_hash_changed")
        destination = folder / source.name
        with source.open("rb") as incoming, destination.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        outputs.append({"path": str(destination.relative_to(root)), **seal})
    if not outputs:
        raise ValueError("missing_audio")
    row.update(audio_output=outputs[0]["path"], output_seal=outputs[0], outputs=outputs)


def pending(row, fixture, root):
    missing = []
    for name in row["prerequisites"]:
        if not fixture.get("prerequisites", {}).get(name):
            missing.append(name)
    if "authorized_multitrack_ground_truth" in row["prerequisites"] and not missing:
        from scripts.eval.capabilities_metrics import validate_ground_truth

        try:
            validate_ground_truth(fixture)
        except ValueError as error:
            missing.append(str(error))
    if row["surface"] == "native_lab" and row["case"] == "lora" and not missing:
        try:
            validate_lora(fixture.get("lora", {}), root)
        except ValueError as error:
            missing.append(str(error))
    return missing


def finish(row, folder):
    row["verified"] = False
    exclusive_json(folder / "result.json", row)
    return row


def execute_v1(
    row, fixture, api, root, folder, *, test_double=False, clock=time.monotonic
):
    row = {**row, "test_double": test_double, "audio_output": None}
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    request = request_for(row, fixture)
    exclusive_json(folder / "request.json", request)
    row["input_effective"] = request
    deadline = clock() + request["timeout_s"]
    events = []
    try:
        api.request("POST", "/v1/jobs", request, deadline=deadline)
        while clock() < deadline:
            batch = api.events(
                row["job_id"],
                after=events[-1]["seq"] if events else 0,
                timeout=min(2, deadline - clock()),
            )
            for event in batch:
                if (
                    event.get("job_id") != row["job_id"]
                    or event["seq"] != len(events) + 1
                ):
                    raise ValueError("event_sequence")
                events.append(event)
            terminal = [
                e for e in events if e["type"] in ("done", "error", "cancelled")
            ]
            if terminal:
                if len(terminal) != 1:
                    raise ValueError("multiple_terminal")
                last = terminal[0]
                if last["type"] == "done":
                    copy_outputs(row, last["data"]["artifacts"], root, folder)
                    row.update(
                        execution_status="executed",
                        result=last["data"].get("result"),
                        verdict=None,
                        no_op=None,
                        musical_acceptance=None,
                    )
                else:
                    row.update(
                        execution_status="failed",
                        error=last["data"],
                        verdict="no funciona" if not test_double else None,
                    )
                break
        else:
            api.request("DELETE", f"/v1/jobs/{row['job_id']}")
            raise ApiError("TIMEOUT")
    except ApiError as error:
        row.update(
            execution_status="rejected" if error.status == 422 else "failed",
            error={"code": error.code, "status": error.status},
            verdict="no funciona" if error.status == 422 and not test_double else None,
        )
    except (ValueError, OSError) as error:
        row.update(
            execution_status="failed",
            error={"code": type(error).__name__, "detail": str(error)},
            verdict=None,
        )
    finally:
        exclusive_json(folder / "events.json", events)
        try:
            row["unload"] = api.request("POST", "/v1/unload")
        except (ApiError, OSError) as error:
            row["cleanup_error"] = type(error).__name__
    return finish(row, folder)


def execute_native(
    row,
    fixture,
    supervisor,
    gpu,
    root,
    folder,
    *,
    test_double=False,
    clock=time.monotonic,
):
    from engine_common.runtime import EngineError, VramGuard

    row = {**row, "test_double": test_double, "audio_output": None}
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    missing = pending(row, fixture, root)
    if missing:
        row.update(
            execution_status="pending_prerequisite",
            missing_prerequisites=missing,
            verdict=None,
        )
        return finish(row, folder)
    request = request_for(row, fixture)
    request["params"].pop("lora", None)
    request.update(capability_row=row, fixture=fixture)
    exclusive_json(folder / "request.json", request)
    events = []
    total, free = gpu.snapshot()
    before = {"total_mb": total, "free_mb": free}
    guard = VramGuard(before["total_mb"], before["free_mb"], 512)
    row["vram_cap_mb"] = guard.cap_mb
    deadline = clock() + request["timeout_s"]
    try:
        supervisor.load(
            row["model_id"],
            row["mode"],
            guard.cap_mb,
            before["total_mb"],
            timeout=max(0.001, deadline - clock()),
        )
        raw = Path(root) / "data" / "tmp" / row["job_id"]
        raw.mkdir(parents=True, exist_ok=False)
        supervisor.send(
            {"command": "generate", "request": request, "output_dir": str(raw)}
        )
        while clock() < deadline:
            message = supervisor.receive(max(0.001, deadline - clock()))
            events.append(message)
            if message["kind"] == "error":
                raise EngineError(message["code"])
            if message["kind"] == "result":
                guard.observe(message.get("vram_peak_mb", 0))
                artifacts = [
                    {**a, "path": f"tmp/{row['job_id']}/{a['filename']}"}
                    for a in message["artifacts"]
                ]
                copy_outputs(row, artifacts, root, folder)
                for source in raw.iterdir():
                    if source.is_file() and source.suffix in (".json", ".npy"):
                        with (
                            source.open("rb") as incoming,
                            (folder / source.name).open("xb") as outgoing,
                        ):
                            shutil.copyfileobj(incoming, outgoing)
                row.update(
                    execution_status="executed",
                    verdict=None,
                    result=message.get("result"),
                    musical_acceptance=None,
                )
                if row["case"] == "audio.stems":
                    import soundfile as sf

                    from scripts.eval.capabilities_metrics import (
                        stem_metrics,
                        validate_ground_truth,
                    )

                    gt = validate_ground_truth(fixture)
                    tracks = {}
                    for name, path in gt["tracks"].items():
                        samples, rate = sf.read(
                            contained(root, path), dtype="float32", always_2d=True
                        )
                        if rate != 48000:
                            raise ValueError("ground_truth_rate")
                        tracks[name] = samples.T
                    samples, rate = sf.read(
                        contained(root, row["audio_output"]),
                        dtype="float32",
                        always_2d=True,
                    )
                    if rate != 48000:
                        raise ValueError("output_rate")
                    row["technical_metrics"] = stem_metrics(
                        samples.T, row["control"]["track_name"], tracks
                    )
                break
        else:
            supervisor.send({"command": "cancel"})
            raise EngineError("TIMEOUT")
    except (EngineError, ValueError, OSError) as error:
        row.update(
            execution_status="failed",
            error={"code": getattr(error, "code", type(error).__name__)},
            verdict=None,
        )
    finally:
        supervisor.unload()
        total, free = gpu.snapshot()
        after = {"total_mb": total, "free_mb": free}
        row["unload"] = {
            "child_alive": supervisor.alive,
            "before": before,
            "after": after,
            "free_recovered": abs(after["free_mb"] - before["free_mb"]) <= 300,
        }
        exclusive_json(folder / "events.json", events)
    return finish(row, folder)
