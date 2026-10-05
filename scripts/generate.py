"""Generación local M0: contrato /v1, postproceso y procedencia inmutable."""

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import yaml
from audio_post import process_audio, write_manifest
from audio_post.manifest import safe_path
from engine_contract import Event, Health, JobRequest, JobStatus, ModelDescriptor
from jsonschema import ValidationError, validate

ROOT = Path(__file__).resolve().parents[1]


def confined(path, root):
    path = Path(path).absolute()
    if not path.resolve().is_relative_to(root.resolve()) or any(
        p.is_symlink() or p.is_junction() for p in (path, *path.parents)
    ):
        raise ValueError("UNSAFE_PATH")
    return path


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--brief")
    result.add_argument("--lyrics")
    result.add_argument("--style")
    result.add_argument("--duration", type=float)
    result.add_argument("--language")
    result.add_argument("--bpm", type=int)
    result.add_argument("--shift", type=float)
    result.add_argument("--seed", type=int)
    result.add_argument("--variants", type=int, default=1)
    result.add_argument("--task", choices=["music.song", "music.instrumental"])
    result.add_argument("--engine")
    result.add_argument(
        "--lyrics-declaration",
        choices=["own", "assistant", "public_domain", "licensed"],
    )
    return result


def read_request(argv=None, *, root=ROOT):
    args = parser().parse_args(argv)
    bpm = args.bpm
    if args.brief:
        if any(
            value is not None
            for value in (
                args.lyrics,
                args.style,
                args.duration,
                args.language,
                args.bpm,
            )
        ):
            raise ValueError("BRIEF_ARGUMENT_CONFLICT")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", args.brief):
            raise ValueError("BRIEF_NOT_FOUND")
        try:
            catalog = yaml.safe_load(
                confined(root / "eval/briefs/briefs.yaml", root).read_text(
                    encoding="utf-8-sig"
                )
            )
        except (OSError, yaml.YAMLError) as error:
            raise ValueError("BRIEF_CATALOG_INVALID") from error
        if (
            not isinstance(catalog, dict)
            or type(catalog.get("version")) is not int
            or catalog["version"] != 1
            or not isinstance(catalog.get("briefs"), dict)
        ):
            raise ValueError("BRIEF_CATALOG_INVALID")
        entry = catalog["briefs"].get(args.brief)
        if entry is None:
            raise ValueError("BRIEF_NOT_FOUND")
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("style"), str)
            or type(entry.get("duration_s")) not in {int, float}
            or not isinstance(entry.get("language"), str)
            or entry.get("task", "music.song")
            not in ("music.song", "music.instrumental")
            or entry.get("lyrics_declaration")
            not in (None, "own", "assistant", "public_domain", "licensed")
            or (
                "bpm" in entry
                and (type(entry["bpm"]) is not int or not 30 <= entry["bpm"] <= 300)
            )
        ):
            raise ValueError("BRIEF_CATALOG_INVALID")
        args.style, args.duration, args.language = (
            entry["style"],
            entry["duration_s"],
            entry["language"],
        )
        args.task = args.task or entry.get("task", "music.song")
        args.lyrics_declaration = args.lyrics_declaration or entry.get(
            "lyrics_declaration"
        )
        if args.task == "music.song":
            args.lyrics = root / "eval/briefs" / f"{args.brief}.txt"
            if not args.lyrics.is_file():
                raise ValueError("BRIEF_LYRICS_MISSING")
        bpm = entry.get("bpm")
    args.task = args.task or "music.song"
    if not args.style or not args.style.strip() or args.duration is None:
        raise ValueError("INVALID_PARAMS")
    if not math.isfinite(args.duration) or not 0 < args.duration <= 600:
        raise ValueError("INVALID_PARAMS")
    if not 1 <= args.variants <= 64 or (args.seed is not None and args.seed < 0):
        raise ValueError("INVALID_PARAMS")
    if bpm is not None and not 30 <= bpm <= 300:
        raise ValueError("INVALID_PARAMS")
    if args.shift is not None and (
        not math.isfinite(args.shift) or not 1 <= args.shift <= 5
    ):
        raise ValueError("INVALID_PARAMS")
    params = {"style": args.style, "duration_s": args.duration}
    if args.shift is not None:
        params["shift"] = args.shift
    if bpm is not None:
        params["bpm"] = bpm
    digest = None
    if args.task == "music.song":
        if not args.lyrics_declaration:
            raise ValueError("LYRICS_DECLARATION_REQUIRED")
        if not args.lyrics or not args.language or not args.language.strip():
            raise ValueError("INVALID_PARAMS")
        payload = confined(root / args.lyrics, root).read_bytes()
        lyrics = payload.decode("utf-8-sig")
        if not lyrics.strip():
            raise ValueError("INVALID_PARAMS")
        params.update(lyrics=lyrics, language=args.language)
        digest = hashlib.sha256(payload).hexdigest()
    elif args.lyrics or args.lyrics_declaration:
        raise ValueError("INSTRUMENTAL_HAS_LYRICS")
    return {
        "task": args.task,
        "params": params,
        "seed": args.seed,
        "n_outputs": args.variants,
        "engine": args.engine,
        "lyrics_declaration": args.lyrics_declaration,
        "lyrics_sha256": digest,
    }


def ulid():
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    return "".join(alphabet[(value >> (5 * i)) & 31] for i in reversed(range(26)))


def environment(root=ROOT):
    result = {}
    path = confined(root / ".env", root)
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip().strip("\"'")
    result.update(os.environ)
    return result


def engine_url(request, config):
    engines = {}
    for item in config.get("STUDIO_ENGINES", "").split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            engines[key.strip()] = value.strip()
    choice = request.get("engine")
    if not choice:
        choice = next(iter(engines), None)
    url = engines.get(choice, choice or "")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("LOCAL_ENGINE_REQUIRED")
    return url.rstrip("/")


def publish_directory(source, destination):
    """Renombra sin sobrescribir; tolera bloqueos breves de Windows."""
    for attempt in range(5):
        if (
            destination.exists()
            or destination.is_symlink()
            or destination.is_junction()
        ):
            raise FileExistsError("PUBLICATION_DESTINATION_EXISTS")
        try:
            source.rename(destination)
            return
        except OSError as error:
            if (
                os.name != "nt"
                or getattr(error, "winerror", None) not in {5, 32}
                or attempt == 4
            ):
                raise
            time.sleep(0.1 * 2**attempt)


def finish_job(call, job_id, model_id, mode, *, cancel, timeout_s=300):
    """Espera el terminal/idle propio y acredita unload dentro de un plazo."""
    deadline = time.monotonic() + min(timeout_s, 300)
    cancelled = False
    unloaded = False

    def request(method, path):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("ENGINE_CLEANUP_TIMEOUT")
        result = call(method, path, timeout=min(5, remaining))
        if time.monotonic() >= deadline:
            raise ValueError("ENGINE_CLEANUP_TIMEOUT")
        return result

    while True:
        status = JobStatus.model_validate(request("GET", f"/v1/jobs/{job_id}"))
        if status.job_id != job_id:
            raise ValueError("ENGINE_CLEANUP_JOB_MISMATCH")
        health = Health.model_validate(request("GET", "/v1/health"))
        if health.job_id not in {None, job_id}:
            raise ValueError("ENGINE_CLEANUP_FOREIGN_JOB")
        if (
            cancel
            and not cancelled
            and status.state not in {"done", "error", "cancelled"}
        ):
            request("DELETE", f"/v1/jobs/{job_id}")
            cancelled = True
            print(
                "Cancelación solicitada; esperando la liberación del engine.",
                flush=True,
            )
        elif (
            status.state in {"done", "error", "cancelled"}
            and health.state == "idle"
            and health.job_id is None
        ):
            if health.loaded is None:
                return
            if (health.loaded.model_id, health.loaded.mode) != (model_id, mode):
                raise ValueError("ENGINE_CLEANUP_FOREIGN_MODEL")
            if unloaded:
                raise ValueError("ENGINE_UNLOAD_UNCONFIRMED")
            try:
                request("POST", "/v1/unload")
            except ValueError as error:
                if str(error) != "ENGINE_HTTP_409":
                    raise
            else:
                unloaded = True
                continue
            # Confirm idle + loaded=None through the next status/health poll.
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("ENGINE_CLEANUP_TIMEOUT")
        time.sleep(min(0.1, remaining))


def generate(request, *, config, root=ROOT, client=None):
    if "shift" in request["params"] and (
        type(request["params"]["shift"]) not in {int, float}
        or not 1 <= request["params"]["shift"] <= 5
        or not math.isfinite(request["params"]["shift"])
    ):
        raise ValueError("INVALID_PARAMS")
    token = config.get("STUDIO_ENGINE_TOKEN")
    if not token:
        raise ValueError("ENGINE_TOKEN_REQUIRED")
    url = engine_url(request, config)
    data = confined(root / config.get("STUDIO_DATA_DIR", "data"), root)
    data.mkdir(parents=True, exist_ok=True)
    if client is None:
        with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as owned:
            return generate(request, config=config, root=root, client=owned)
    headers = {"X-Studio-Engine-Token": token}

    def call(method, path, **kwargs):
        response = client.request(method, url + path, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise ValueError("ENGINE_HTTP_" + str(response.status_code))
        return response.json()

    health = Health.model_validate(call("GET", "/v1/health"))
    if health.state != "idle":
        raise ValueError("ENGINE_BUSY")
    descriptors = [ModelDescriptor.model_validate(m) for m in call("GET", "/v1/models")]
    candidates = [
        m
        for m in descriptors
        if m.provider.type == "local" and request["task"] in m.tasks and m.modes
    ]
    candidates = [
        m
        for m in candidates
        if m.tasks[request["task"]].verified
        or config.get("STUDIO_ALLOW_UNVERIFIED") == "1"
    ]
    if not candidates:
        raise ValueError("CAPABILITY_UNAVAILABLE")
    model = candidates[0]
    validate(request["params"], model.tasks[request["task"]].params_schema)
    if request["task"] == "music.song" and not request.get("lyrics_declaration"):
        raise ValueError("LYRICS_DECLARATION_REQUIRED")
    modes = [m.id for m in model.modes]
    mode = "bf16" if "bf16" in modes else modes[0]
    job_id = ulid()
    seed = request["seed"] if request["seed"] is not None else secrets.randbits(32)
    timeout = max(300, math.ceil(request["params"]["duration_s"] * 20 + 300))
    job = JobRequest(
        job_id=job_id,
        task=request["task"],
        model_id=model.id,
        mode=mode,
        params=request["params"],
        seed=seed,
        n_outputs=request["n_outputs"],
        output_dir=f"tmp/{job_id}/",
        timeout_s=timeout,
    )
    ffmpeg = next(
        iter(
            (root / "tools/ffmpeg").glob(
                "*/bin/ffmpeg.exe" if os.name == "nt" else "*/bin/ffmpeg"
            )
        ),
        None,
    )
    if ffmpeg is None:
        raise ValueError("FFMPEG_REQUIRED")
    tool = json.loads((root / "tools/tools.lock.json").read_text(encoding="utf-8"))[
        "tools"
    ]["ffmpeg"]
    accepted = False
    cleanup_attempted = False
    terminal = False
    try:
        response = call("POST", "/v1/jobs", json=job.model_dump(mode="json"))
        accepted = True
        if response.get("job_id") != job_id:
            raise ValueError("ENGINE_JOB_MISMATCH")
        last_seq = 0
        done = None
        deadline = time.monotonic() + timeout
        while not terminal:
            if time.monotonic() >= deadline:
                raise ValueError("TIMEOUT")
            with client.stream(
                "GET",
                url + f"/v1/jobs/{job_id}/events",
                params={"after": last_seq},
                headers=headers,
                timeout=max(0.1, deadline - time.monotonic()),
            ) as stream:
                if stream.status_code >= 400:
                    raise ValueError("ENGINE_HTTP_" + str(stream.status_code))
                for line in stream.iter_lines():
                    if time.monotonic() >= deadline:
                        raise ValueError("TIMEOUT")
                    if not line.strip():
                        continue
                    event = Event.model_validate_json(line)
                    if event.job_id != job_id or event.seq <= last_seq or terminal:
                        raise ValueError("ENGINE_EVENT_INVALID")
                    last_seq = event.seq
                    if event.type == "stage":
                        print("Etapa: " + event.data["stage"], flush=True)
                    elif event.type == "progress":
                        print(f"Progreso: {event.data['fraction']:.1%}", flush=True)
                    elif event.type in {"done", "error", "cancelled"}:
                        terminal = True
                        if event.type != "done":
                            raise ValueError(event.data.get("code", "CANCELLED"))
                        done = event.data
            if not terminal:
                time.sleep(0.1)
        artifacts = done["artifacts"]
        if len(artifacts) != job.n_outputs or {
            a["output_index"] for a in artifacts
        } != set(range(job.n_outputs)):
            raise ValueError("ENGINE_OUTPUTS_INVALID")
        sources = []
        for artifact in sorted(artifacts, key=lambda a: a["output_index"]):
            if not artifact["path"].startswith(f"tmp/{job_id}/") or artifact[
                "media_type"
            ] not in {"audio/wav", "audio/flac"}:
                raise ValueError("ENGINE_ARTIFACT_INVALID")
            source = safe_path(data, artifact["path"])
            with source.open("rb") as handle:
                if (
                    hashlib.file_digest(handle, "sha256").hexdigest()
                    != artifact["sha256"]
                ):
                    raise ValueError("HASH_MISMATCH")
            if artifact["meta"].get("seed") != seed + artifact["output_index"]:
                raise ValueError("ENGINE_SEED_MISMATCH")
            sources.append(source)
        # Release the engine before CPU processing; the finally block also covers failures.
        cleanup_attempted = True
        try:
            finish_job(call, job_id, model.id, mode, cancel=False)
        except BaseException as error:
            print("Aviso: ENGINE_CLEANUP_UNCONFIRMED", file=sys.stderr)
            error.add_note("ENGINE_CLEANUP_UNCONFIRMED")
            raise
        accepted = False
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        parent = safe_path(data, f"cli/{date}")
        parent.mkdir(parents=True, exist_ok=True)
        staging = safe_path(data, f"cli/{date}/.pending-{job_id}")
        staging.mkdir()
        destinations = []
        published = []
        try:
            for index, source in enumerate(sources):
                run_id = job_id if len(sources) == 1 else ulid()
                dest = staging / run_id
                result = process_audio(
                    source,
                    dest,
                    expected_duration_s=job.params["duration_s"],
                    ffmpeg=ffmpeg,
                )
                params = {
                    k: v for k, v in job.params.items() if k not in {"lyrics", "style"}
                }
                manifest = {
                    "manifest_version": 1,
                    "kind": "cli_run",
                    "subject": {"type": "cli_run", "id": run_id},
                    "song_id": None,
                    "created_at": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "provider": {"type": "local"},
                    "models": [
                        {
                            "role": "generator",
                            "id": model.id,
                            "revision": model.revision,
                            "license": model.license,
                            "training_data": model.training_data,
                            "weights": [
                                w.model_dump(mode="json") for w in model.weights
                            ],
                            "commercial_use": model.commercial_use,
                        }
                    ],
                    "pipeline": {
                        "engine_id": health.engine_id,
                        "engine_version": health.engine_version,
                        "image_digest": health.image_digest,
                        "workflow_id": None,
                        "workflow_sha256": None,
                        "custom_nodes": [],
                        "remote_code": [
                            r.model_dump(mode="json") for r in model.remote_code
                        ],
                    },
                    "request": {
                        "task": job.task,
                        "params": params,
                        "seed": seed + index,
                        "lyrics_sha256": request["lyrics_sha256"],
                        "lyrics_declaration": request["lyrics_declaration"],
                        "style_prompt": job.params["style"],
                    },
                    "inputs": (
                        [
                            {
                                "role": "lyrics",
                                "ref": {"type": "cli_input", "id": job_id},
                                "sha256": request["lyrics_sha256"],
                                "rights": "own"
                                if request["lyrics_declaration"] == "assistant"
                                else request["lyrics_declaration"],
                                "consent": "n_a",
                                "commercial_use": request["lyrics_declaration"]
                                != "licensed",
                            }
                        ]
                        if request["lyrics_sha256"]
                        else []
                    ),
                    "lineage": {
                        "parents": [],
                        "derivation": "original",
                        "section_map": None,
                    },
                    "post": result["post"],
                    "outputs": result["outputs"],
                    "run": done["telemetry"],
                    "tools": [
                        {
                            "name": "ffmpeg",
                            "version": tool["release_tag"],
                            "license": tool["license"],
                            "build": tool["asset"],
                            "commercial_use": True,
                        }
                    ],
                }
                write_manifest(dest / "manifest.json", manifest)
                destinations.append(parent / run_id)
            for dest in destinations:
                publish_directory(staging / dest.name, dest)
                published.append(dest)
            return destinations
        except BaseException as error:
            # Only these new directories belong to this publication attempt.
            for dest in published:
                try:
                    shutil.rmtree(dest)
                except OSError:
                    error.add_note("PUBLICATION_CLEANUP_FAILED")
            raise
        finally:
            original_error = sys.exception()
            try:
                shutil.rmtree(staging)
            except OSError:
                if original_error is None:
                    raise
                original_error.add_note("PUBLICATION_CLEANUP_FAILED")
    finally:
        if accepted and not cleanup_attempted:
            primary_error = sys.exception()
            try:
                cleanup_attempted = True
                finish_job(call, job_id, model.id, mode, cancel=not terminal)
            except BaseException:
                print("Aviso: ENGINE_CLEANUP_UNCONFIRMED", file=sys.stderr)
                if primary_error is None:
                    raise
                primary_error.add_note("ENGINE_CLEANUP_UNCONFIRMED")


def main(argv=None):
    try:
        request = read_request(argv)
        for destination in generate(request, config=environment()):
            print("Resultado: " + destination.relative_to(ROOT).as_posix())
        return 0
    except KeyboardInterrupt:
        print("Generación cancelada.", file=sys.stderr)
        return 130
    except (ValueError, ValidationError, OSError, httpx.HTTPError) as error:
        # Do not print request bodies, absolute paths or transport URLs/tokens.
        code = str(error) if isinstance(error, ValueError) else "CLI_IO_ERROR"
        if not code.replace("_", "").isalnum() or len(code) > 80:
            code = "INVALID_RESPONSE_OR_PARAMS"
        print("Error: " + code, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
