"""Resolución local verificada con caché acotada y petición exacta."""

import asyncio
import json
import math
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry
from referencing.exceptions import Unresolvable
from sqlalchemy.orm import Session

from app.migrations.job_attempt_invariants import validate_contract

from .backends.protocol import BackendFailure, EngineBackend
from .inputs import ResolutionError, owned_inputs
from .provenance import MUSIC_TASKS, SelectedProvenance


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


SNAPSHOT_FIELDS = (
    "id",
    "owner_id",
    "song_id",
    "task",
    "lane",
    "request",
    "model_id",
    "engine_id",
    "attempt",
    "max_attempts",
    "status",
    "priority",
    "created_at",
    "updated_at",
    "deleted_at",
    "not_before",
    "cancel_requested_at",
)


def snapshot(job):
    return canonical({field: getattr(job, field) for field in SNAPSHOT_FIELDS})


def snapshot_values(values):
    """Canon de los campos del Job ya convertidos por sus tipos SQLAlchemy."""
    return canonical({field: values[field] for field in SNAPSHOT_FIELDS})


@dataclass(frozen=True)
class Resolved:
    job_id: str
    owner_id: str
    engine_id: str
    model_id: str
    mode: str
    lane: str
    source: str
    payload: str
    data_dir: Path
    backend: EngineBackend
    required_mb: float | None
    identity: tuple[str, str, str]
    selected_provenance: SelectedProvenance | None = None

    def freeze(self, attempt_id):
        body = dict(
            json.loads(self.payload), job_id=attempt_id, output_dir="tmp/" + attempt_id
        )
        return validate_contract(body, "request"), validate_contract(
            {"model_id": self.model_id, "mode": self.mode}, "load"
        )

    def check_inputs(self, job, session):
        if (
            owned_inputs(job, session, self.data_dir)
            != json.loads(self.payload)["inputs"]
        ):
            raise ResolutionError("Input changed during admission")


class CatalogUnavailable(ResolutionError):
    """Observación inválida; no invalida los parámetros del consumidor."""


class StaleRoute(ResolutionError):
    """La observación fresca ya no coincide con la ruta restrictiva elegida."""


@dataclass(frozen=True)
class RouteContext:
    """Restricción sin procedencia ni autoridad, capturada antes del screen."""

    backend: EngineBackend
    origin: str
    identity: tuple[str, str, str]
    model_id: str
    mode: str
    lane: str

    @classmethod
    def from_resolved(cls, routed):
        return cls(
            routed.backend,
            routed.backend.origin,
            routed.identity,
            routed.model_id,
            routed.mode,
            routed.lane,
        )


def closed_schema(value):
    if isinstance(value, dict):
        for key, part in value.items():
            if (
                key in {"$id", "$dynamicRef", "$recursiveRef"}
                or key == "$ref"
                and (not isinstance(part, str) or not part.startswith("#"))
            ):
                raise ResolutionError("Only internal schema references allowed")
            closed_schema(part)
    elif isinstance(value, list):
        for part in value:
            closed_schema(part)


class Resolver:
    def __init__(
        self,
        backends,
        *,
        data_dir,
        ttl_s=30,
        clock=time.monotonic,
        synthetic_registry=None,
    ):
        if not 0 < ttl_s <= 300:
            raise ValueError("Bounded descriptor TTL required")
        self.backends = dict(backends)
        from .synthetic_registry import SyntheticRegistry

        self.synthetic_registry = (
            synthetic_registry
            if synthetic_registry is not None
            else SyntheticRegistry()
        )
        self.synthetic_registry.validate_backends(self.backends)
        self.data_dir, self.ttl_s, self.clock = Path(data_dir), ttl_s, clock
        self._cache = {}

    def invalidate(self, origin):
        self._cache.pop(origin, None)

    async def _catalog(self, backend):
        try:
            health = await backend.health()
            if health.state == "error":
                raise BackendFailure("DOWN")
            identity = (health.engine_id, health.engine_version, health.image_digest)
            old = self._cache.get(backend.origin)
            if old and old[0] == identity and self.clock() < old[1]:
                models = old[2]
            else:
                models = await backend.models()
                if len({model.id for model in models}) != len(models):
                    raise ValueError("Duplicate model")
                self._cache[backend.origin] = (
                    identity,
                    self.clock() + self.ttl_s,
                    models,
                )
            return health, models
        except (BackendFailure, OSError, ValueError):
            self.invalidate(backend.origin)
            raise CatalogUnavailable("Engine catalog unavailable") from None

    def _inputs(self, job, engine):
        if engine is None:
            return owned_inputs(job, None, self.data_dir)
        with Session(engine) as session:
            return owned_inputs(job, session, self.data_dir)

    async def resolve(self, job, *, engine=None, expected_route=None):
        return await self._resolve(job, engine=engine, expected_route=expected_route)

    async def route(self, job, observations):
        """Clasificación sin bytes; observaciones sólo del despacho actual."""
        return await self._resolve(job, observations=observations, routing=True)

    async def observed_catalog(self, backend, observations):
        if backend.origin not in observations:
            try:
                observations[backend.origin] = await self._catalog(backend)
            except CatalogUnavailable as error:
                observations[backend.origin] = error
        observed = observations[backend.origin]
        if isinstance(observed, CatalogUnavailable):
            raise observed
        return observed

    async def _resolve(
        self, job, *, engine=None, observations=None, routing=False, expected_route=None
    ):
        route_key = None
        if expected_route is not None:
            binding = next(
                (
                    (key, backend)
                    for key, backend in self.backends.items()
                    if backend is expected_route.backend
                ),
                None,
            )
            if binding is None:
                raise StaleRoute("Selected backend changed")
            route_key = binding[0]
        if job.lane == "remote":
            raise ResolutionError("Remote disabled")
        allowed = {
            "params",
            "inputs",
            "seed",
            "n_outputs",
            "timeout_s",
            "mode",
            "required_features",
        }
        if not isinstance(job.request, dict) or set(job.request) - allowed:
            raise ResolutionError("Unknown domain request field")
        unavailable = False
        for backend in self.backends.values():
            try:
                if observations is not None:
                    health, models = await self.observed_catalog(backend, observations)
                else:
                    health, models = await self._catalog(backend)
            except CatalogUnavailable:
                unavailable = True
                continue
            if (
                expected_route is not None
                and self.backends.get(route_key) is not expected_route.backend
                and not any(
                    configured is expected_route.backend
                    for configured in self.backends.values()
                )
            ):
                raise StaleRoute("Selected backend changed")
            if expected_route is not None and backend is not expected_route.backend:
                continue
            if expected_route is not None and (
                backend.origin != expected_route.origin
                or (health.engine_id, health.engine_version, health.image_digest)
                != expected_route.identity
            ):
                raise StaleRoute("Selected backend identity changed")
            if job.engine_id and health.engine_id != job.engine_id:
                continue
            for model in models:
                if job.model_id and model.id != job.model_id:
                    continue
                task = model.tasks.get(job.task)
                if (
                    model.provider.type != "local"
                    or not model.commercial_use
                    or not model.license
                    or not task
                    or not task.verified
                ):
                    continue
                preference = "cpu" if task.device == "cpu" else "bf16"
                mode = job.request.get("mode") or preference
                options = [option for option in model.modes if option.id == mode]
                if len(options) != 1:
                    raise ResolutionError("Explicit supported mode required")
                features = job.request.get("required_features", [])
                if not isinstance(features, list) or any(
                    not isinstance(f, str)
                    or f not in task.features
                    or not task.features[f].verified
                    for f in features
                ):
                    raise ResolutionError("Unverified feature")
                params = job.request.get("params", {})
                if isinstance(params, dict) and any(
                    k in task.features and not task.features[k].verified for k in params
                ):
                    raise ResolutionError("Requested feature unverified")
                closed_schema(task.params_schema)
                try:
                    Draft202012Validator.check_schema(task.params_schema)
                    Draft202012Validator(
                        task.params_schema, registry=Registry()
                    ).validate(params)
                except (
                    SchemaError,
                    ValidationError,
                    Unresolvable,
                    TypeError,
                    ValueError,
                ):
                    raise ResolutionError(
                        "Invalid task params schema or params"
                    ) from None
                inputs = (
                    []
                    if routing
                    else await asyncio.to_thread(self._inputs, job, engine)
                )
                roles = {spec.role: spec for spec in task.inputs}
                present = {item["role"] for item in inputs}
                if len(roles) != len(task.inputs) or len(present) != len(inputs):
                    raise ResolutionError("Duplicate input role")
                if (
                    any(
                        i["role"] not in roles
                        or i["media_type"] not in roles[i["role"]].media_types
                        for i in inputs
                    )
                    or not routing
                    and any(
                        spec.required and spec.role not in present
                        for spec in task.inputs
                    )
                ):
                    raise ResolutionError("Required input role or media mismatch")
                count = job.request.get("n_outputs", 1)
                if type(count) is not int or not 1 <= count <= min(
                    64, task.limits.get("n_outputs", 64)
                ):
                    raise ResolutionError("Output limit")
                if expected_route is not None and (model.id, mode, task.device) != (
                    expected_route.model_id,
                    expected_route.mode,
                    expected_route.lane,
                ):
                    raise StaleRoute("Selected route changed")
                try:
                    for field, value in params.items():
                        limit = task.limits.get(field)
                        if (
                            isinstance(limit, list)
                            and len(limit) == 2
                            and all(type(v) in {int, float} for v in limit)
                            and not limit[0] <= value <= limit[1]
                        ):
                            raise ResolutionError("Task range limit")
                        if isinstance(limit, dict) and (
                            "min" in limit
                            and value < limit["min"]
                            or "max" in limit
                            and value > limit["max"]
                        ):
                            raise ResolutionError("Task limit")
                    body = {
                        "task": job.task,
                        "model_id": model.id,
                        "mode": mode,
                        "params": params,
                        "inputs": inputs,
                        "seed": secrets.randbits(63)
                        if job.request.get("seed") is None
                        else job.request["seed"],
                        "n_outputs": count,
                        "timeout_s": job.request.get("timeout_s", 300),
                    }
                    result = Resolved(
                        job.id,
                        job.owner_id,
                        health.engine_id,
                        model.id,
                        mode,
                        task.device,
                        snapshot(job),
                        canonical(body),
                        self.data_dir,
                        backend,
                        options[0].vram_mb,
                        (health.engine_id, health.engine_version, health.image_digest),
                        SelectedProvenance.select(
                            model,
                            health,
                            job.task,
                            model.id,
                            mode,
                            backend=backend,
                            registry=self.synthetic_registry,
                        )
                        if job.task in MUSIC_TASKS and not routing
                        else None,
                    )
                    result.freeze(job.id)
                except (ValueError, TypeError):
                    raise ResolutionError("Invalid immutable engine request") from None
                if result.lane == "gpu" and (
                    result.required_mb is None or not math.isfinite(result.required_mb)
                ):
                    raise ResolutionError("Unknown GPU mode budget")
                return result
        if unavailable:
            raise CatalogUnavailable("Engine catalog unavailable")
        raise ResolutionError("No verified local commercial task")
