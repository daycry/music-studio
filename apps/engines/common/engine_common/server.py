"""API autenticada, ejecución en proceso hijo y eventos reanudables."""

import asyncio
import hashlib
import hmac
import os
import shutil
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from engine_contract import (
    CONTRACT_VERSION,
    Event,
    Health,
    JobRequest,
    LoadRequest,
    Telemetry,
)
from fastapi import Depends, FastAPI, Header, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from jsonschema import Draft202012Validator

from .runtime import EngineError, NvmlGpu, ProcessSupervisor, VramGuard

TERMINALS = {"done", "error", "cancelled"}
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONTAINER_DATA_ROOT = Path("/data")


def in_container():
    # El montaje contractual es fijo; una variable del consumidor no amplía
    # las raíces permitidas en el host.
    return os.name == "posix" and Path("/.dockerenv").is_file()


def file_sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def create_app(
    descriptors,
    adapter_factory,
    *,
    token=None,
    data_dir=None,
    gpu=None,
    adapter_options=None,
    engine_id="engine",
    margin_mb=None,
):
    token = token if token is not None else os.environ.get("STUDIO_ENGINE_TOKEN", "")
    if not token:
        raise ValueError("STUDIO_ENGINE_TOKEN es obligatorio")
    container = in_container()
    default_root = CONTAINER_DATA_ROOT if container else PROJECT_ROOT / "data"
    root = Path(data_dir or os.environ.get("STUDIO_DATA_DIR", default_root)).resolve()
    if not root.is_relative_to(PROJECT_ROOT) and not (
        container and root == CONTAINER_DATA_ROOT
    ):
        raise ValueError("STUDIO_DATA_DIR debe estar dentro del proyecto")
    gpu = gpu or NvmlGpu()
    margin = (
        margin_mb
        if margin_mb is not None
        else int(os.environ.get("STUDIO_VRAM_MARGIN_MB", "512"))
    )
    if margin < 0:
        raise ValueError("Margen VRAM no válido")
    supervisor = ProcessSupervisor(adapter_factory, adapter_options)
    lock = threading.RLock()
    jobs = {}
    active = None
    maintenance = False
    guard = VramGuard(0, 0, 0)
    models = {descriptor.id: descriptor for descriptor in descriptors}
    threads = []

    @asynccontextmanager
    async def lifespan(app):
        yield
        with lock:
            if active:
                jobs[active]["cancelled"] = True
                try:
                    supervisor.send({"command": "cancel"})
                except EngineError:
                    pass
        for thread in threads:
            await asyncio.to_thread(thread.join, 2)
        supervisor.unload()

    async def authenticate(x_studio_engine_token: str | None = Header(default=None)):
        if not x_studio_engine_token or not hmac.compare_digest(
            x_studio_engine_token.encode(), token.encode()
        ):
            raise EngineError("UNAUTHORIZED", "Token interno requerido")

    app = FastAPI(lifespan=lifespan, dependencies=[Depends(authenticate)])
    app.state.supervisor = supervisor

    @app.exception_handler(EngineError)
    async def engine_error(request, error):
        status = {
            "BUSY": 409,
            "INVALID_PARAMS": 422,
            "MODEL_NOT_FOUND": 404,
            "UNAUTHORIZED": 401,
            "NOT_FOUND": 404,
            "TIMEOUT": 504,
        }.get(error.code, 500)
        return JSONResponse(
            status_code=status,
            media_type="application/problem+json",
            content={
                "type": "about:blank",
                "title": error.code,
                "status": status,
                "detail": error.message,
                "code": error.code,
                "retryable": error.retryable,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        return await engine_error(
            request, EngineError("INVALID_PARAMS", "Petición no válida")
        )

    def model_mode(model_id, mode):
        if model_id not in models:
            raise EngineError("MODEL_NOT_FOUND")
        model = models[model_id]
        mode = mode or model.modes[0].id
        if mode not in {item.id for item in model.modes}:
            raise EngineError("INVALID_PARAMS", "Modo no declarado")
        return model, mode

    def output_path(request):
        path = root / request.output_dir
        # Ningún ancestro del directorio del job puede ser un enlace.
        for parent in (root, root / "tmp", path):
            if parent.is_symlink() or (
                hasattr(parent, "is_junction") and parent.is_junction()
            ):
                raise EngineError("INVALID_PARAMS", "Directorio de salida enlazado")
        resolved = path.resolve()
        if (
            not resolved.is_relative_to(root / "tmp")
            or resolved != root / "tmp" / request.job_id
        ):
            raise EngineError("INVALID_PARAMS", "Salida fuera del directorio del job")
        return resolved

    def validate(request):
        model, mode = model_mode(request.model_id, request.mode)
        if request.task not in model.tasks:
            raise EngineError("INVALID_PARAMS", "Tarea no declarada")
        task = model.tasks[request.task]
        if list(Draft202012Validator(task.params_schema).iter_errors(request.params)):
            raise EngineError("INVALID_PARAMS", "Parámetros no válidos para la tarea")
        output_path(request)
        for item in request.inputs:
            path = (root / item.path).resolve()
            if not path.is_relative_to(root):
                raise EngineError("INVALID_PARAMS", "Entrada fuera de data/")
            if not path.is_file() or file_sha256(path) != item.sha256:
                raise EngineError("INVALID_PARAMS", "Entrada ausente o hash incorrecto")
            matches = [spec for spec in task.inputs if spec.role == item.role]
            if matches and item.media_type not in matches[0].media_types:
                raise EngineError("INVALID_PARAMS", "Tipo de entrada no permitido")
        for spec in task.inputs:
            if spec.required and not any(
                item.role == spec.role for item in request.inputs
            ):
                raise EngineError("INVALID_PARAMS", "Falta una entrada obligatoria")
        return model, mode

    def load(model_id, mode, deadline=None):
        nonlocal guard
        model, mode = model_mode(model_id, mode)
        if supervisor.alive and supervisor.loaded == (model_id, mode):
            return
        # La medida debe incluir la memoria liberada por el modelo anterior.
        supervisor.unload()
        total, free = gpu.snapshot()
        guard = VramGuard(total, free, margin)
        if (
            any(task.device == "gpu" for task in model.tasks.values())
            and guard.cap_mb <= 0
        ):
            raise EngineError("VRAM_EXCEEDED")
        if deadline is None:
            supervisor.load(model_id, mode, guard.cap_mb, total)
        else:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError("TIMEOUT")
            supervisor.load(model_id, mode, guard.cap_mb, total, timeout=remaining)

    def emit(job, event_type, data):
        with lock:
            if job["state"] in TERMINALS:
                return
            event = Event(
                seq=len(job["events"]) + 1,
                job_id=job["request"].job_id,
                type=event_type,
                data=data,
            )
            job["events"].append(event.model_dump(mode="json"))
            if event_type in TERMINALS:
                job["state"] = event_type

    def run(job):
        nonlocal active
        request = job["request"]
        started = time.monotonic()
        job_guard = None
        load_s = 0

        def telemetry():
            return Telemetry(
                load_s=load_s,
                run_s=time.monotonic() - started,
                vram_peak_mb=job_guard.peak_mb if job_guard else 0,
                vram_cap_mb=guard.cap_mb,
                spilled=job_guard.spilled if job_guard else False,
                mode=job["mode"],
                model_revision=models[request.model_id].revision,
            ).model_dump(mode="json")

        try:
            if (
                supervisor.loaded != (request.model_id, job["mode"])
                or not supervisor.alive
            ):
                emit(job, "stage", {"stage": "loading_model"})
                load(request.model_id, job["mode"], started + request.timeout_s)
                load_s = supervisor.load_s
            job_guard = VramGuard(guard.total_mb, guard.cap_mb, 0)
            if job["cancelled"]:
                raise EngineError("CANCELLED")
            path = output_path(request)
            path.mkdir(parents=True, exist_ok=True)
            supervisor.send(
                {
                    "command": "generate",
                    "request": request.model_dump(mode="json"),
                    "output_dir": str(path),
                }
            )
            job["state"] = "busy"
            while True:
                remaining = request.timeout_s - (time.monotonic() - started)
                if remaining <= 0:
                    raise EngineError("TIMEOUT")
                message = supervisor.receive(remaining)
                if message["kind"] == "event":
                    emit(job, message["type"], message["data"])
                elif message["kind"] == "error":
                    raise EngineError(
                        message["code"],
                        message.get("message"),
                        message.get("retryable", False),
                    )
                elif message["kind"] == "result":
                    if job["cancelled"]:
                        raise EngineError("CANCELLED")
                    job_guard.observe(
                        message.get("vram_peak_mb", 0),
                        message.get("rtf"),
                        message.get("reference_rtf"),
                    )
                    artifacts = []
                    for artifact in message["artifacts"]:
                        filename = artifact.pop("filename")
                        file = (path / filename).resolve()
                        if not file.is_relative_to(path) or not file.is_file():
                            raise EngineError("INTERNAL", "Artefacto no válido")
                        item = {
                            **artifact,
                            "path": file.relative_to(root).as_posix(),
                            "sha256": file_sha256(file),
                        }
                        artifacts.append(item)
                        emit(job, "artifact", item)
                    emit(
                        job,
                        "done",
                        {
                            "artifacts": artifacts,
                            "result": message.get("result"),
                            "telemetry": telemetry(),
                        },
                    )
                    break
        except EngineError as error:
            if error.code in {"TIMEOUT", "VRAM_EXCEEDED", "INTERNAL"}:
                supervisor.unload()
            if error.code == "CANCELLED":
                emit(job, "cancelled", {"telemetry": telemetry()})
            else:
                emit(
                    job,
                    "error",
                    {
                        "code": error.code,
                        "message": error.message,
                        "retryable": error.retryable,
                    },
                )
        except Exception:  # noqa: BLE001 - frontera del adapter: error interno sin detalles privados
            supervisor.unload()
            emit(
                job,
                "error",
                {
                    "code": "INTERNAL",
                    "message": "Fallo interno del engine",
                    "retryable": False,
                },
            )
        finally:
            if job["state"] != "done":
                try:
                    path = output_path(request)
                    if path.exists():
                        shutil.rmtree(path)
                except EngineError:
                    pass
            with lock:
                active = None
                job["finished"] = True

    @app.get("/v1/health", response_model=Health)
    def health():
        total, free = gpu.snapshot()
        with lock:
            loaded_snapshot = supervisor.loaded
            loaded = (
                {"model_id": loaded_snapshot[0], "mode": loaded_snapshot[1]}
                if loaded_snapshot
                else None
            )
            return {
                "contract_version": CONTRACT_VERSION,
                "engine_id": engine_id,
                "engine_version": "0.1.0",
                "image_digest": os.environ.get("STUDIO_IMAGE_DIGEST", "unknown"),
                "state": (
                    "busy"
                    if jobs[active]["state"] in TERMINALS
                    else jobs[active]["state"]
                )
                if active
                else ("loading" if maintenance else "idle"),
                "loaded": loaded,
                "gpu": {"total_mb": total, "free_mb": free, "cap_mb": guard.cap_mb},
                "job_id": active,
            }

    @app.get("/v1/models")
    def get_models():
        return list(models.values())

    @app.post("/v1/load")
    def preload(request: LoadRequest):
        nonlocal maintenance
        with lock:
            if active or maintenance:
                raise EngineError("BUSY")
            maintenance = True
        try:
            load(request.model_id, request.mode)
            return {"model_id": supervisor.loaded[0], "mode": supervisor.loaded[1]}
        finally:
            with lock:
                maintenance = False

    @app.post("/v1/unload")
    def unload():
        nonlocal maintenance
        with lock:
            if active or maintenance:
                raise EngineError("BUSY")
            maintenance = True
        try:
            _, before = gpu.snapshot()
            supervisor.unload()
            _, after = gpu.snapshot()
            return {"freed_mb": max(0, after - before)}
        finally:
            with lock:
                maintenance = False

    @app.post("/v1/estimate")
    def estimate(request: JobRequest):
        _, mode = validate(request)
        return {
            "eta_s": float(request.params.get("duration_s", 1)),
            "vram_mb": next(
                item.vram_mb or 0
                for item in models[request.model_id].modes
                if item.id == mode
            ),
        }

    @app.post("/v1/jobs", status_code=202)
    def submit(request: JobRequest):
        nonlocal active, maintenance
        with lock:
            if request.job_id in jobs:
                return {"job_id": request.job_id}
            if active or maintenance:
                raise EngineError("BUSY")
            maintenance = True
        try:
            _, mode = validate(request)
            with lock:
                job = {
                    "request": request,
                    "mode": mode,
                    "events": [],
                    "state": "loading",
                    "cancelled": False,
                    "finished": False,
                }
                jobs[request.job_id] = job
                active = request.job_id
                thread = threading.Thread(target=run, args=(job,), daemon=True)
                threads.append(thread)
                thread.start()
                return {"job_id": request.job_id}
        finally:
            with lock:
                maintenance = False

    def lookup(job_id):
        with lock:
            if job_id not in jobs:
                raise EngineError("NOT_FOUND")
            return jobs[job_id]

    @app.get("/v1/jobs/{job_id}")
    def status(job_id: str):
        job = lookup(job_id)
        with lock:
            return {"job_id": job_id, "state": job["state"], "seq": len(job["events"])}

    @app.get("/v1/jobs/{job_id}/events")
    async def events(job_id: str, after: int = Query(default=0, ge=0)):
        job = lookup(job_id)

        async def stream():
            cursor = after
            while True:
                with lock:
                    batch = [event for event in job["events"] if event["seq"] > cursor]
                    finished = job["finished"]
                for event in batch:
                    cursor = event["seq"]
                    import json

                    yield json.dumps(event) + "\n"
                if finished:
                    return
                await asyncio.sleep(0.01)

        return StreamingResponse(stream(), media_type="application/x-ndjson")

    @app.delete("/v1/jobs/{job_id}")
    def cancel(job_id: str):
        job = lookup(job_id)
        with lock:
            if job["state"] not in TERMINALS:
                job["cancelled"] = True
                if supervisor.alive:
                    supervisor.send({"command": "cancel"})
            return {"job_id": job_id}

    return app
