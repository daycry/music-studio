"""Primera entrega callable; reconciliación y eventos pertenecen a U2."""

import asyncio
from dataclasses import dataclass

from app.worker.contracts import canonical_sha256

from .admission import PreclaimResolutionError
from .backends.protocol import BackendFailure, EngineBackend
from .provenance import capture_before_send
from .resolver import CatalogUnavailable, ResolutionError, RouteContext, StaleRoute


@dataclass(frozen=True)
class Resident:
    backend: EngineBackend
    engine_id: str
    model_id: str
    mode: str
    identity: tuple[str, str, str]


class Dispatcher:
    def __init__(self, admission, resolver, *, margin_mb=512):
        if margin_mb < 0:
            raise ValueError("Invalid VRAM margin")
        self.admission, self.resolver, self.margin_mb = admission, resolver, margin_mb
        self.resident = None
        self.native_workers = set()

    async def _native(self, function, *args):
        task = asyncio.create_task(asyncio.to_thread(function, *args))
        self.native_workers.add(task)
        task.add_done_callback(self.native_workers.discard)
        return await asyncio.shield(task)

    async def close(self):
        await asyncio.gather(*self.native_workers, return_exceptions=True)

    @staticmethod
    def _identity(health):
        return health.engine_id, health.engine_version, health.image_digest

    @staticmethod
    def _cpu_resident(observed, models):
        model = next((m for m in models if m.id == observed.loaded.model_id), None)
        return bool(
            model
            and model.provider.type == "local"
            and model.commercial_use
            and model.license
            and model.tasks
            and all(
                task.device == "cpu" and task.verified for task in model.tasks.values()
            )
            and any(mode.id == observed.loaded.mode for mode in model.modes)
        )

    async def _screen(self, routed, observations, occupancy):
        """Sólo descarta, sin unload ni autoridad para admisión final."""
        health = observations[routed.backend.origin][0]
        if routed.backend.origin in occupancy.get("claimed", set()):
            return False
        if health.state != "idle" or health.job_id is not None:
            return False
        if routed.lane == "cpu":
            return health.loaded is None or (
                health.loaded.model_id,
                health.loaded.mode,
            ) == (routed.model_id, routed.mode)
        if "gpu" not in occupancy:
            occupancy["gpu"] = await self._native(self.admission.gpu_active)
        if occupancy["gpu"]:
            return False
        resident = self.resident
        for other in self.resolver.backends.values():
            if other is routed.backend or resident and other is resident.backend:
                continue
            observed, models = await self.resolver.observed_catalog(other, observations)
            if observed.loaded is not None:
                if self._cpu_resident(observed, models):
                    continue
                return False
            if observed.state != "idle" or observed.job_id is not None:
                return False
        return True

    async def _preflight(self, resolved):
        health = await resolved.backend.health()
        if self._identity(health) != resolved.identity:
            self.resolver.invalidate(resolved.backend.origin)
            return False
        if health.state != "idle" or health.job_id is not None:
            return False
        if resolved.lane == "cpu":
            return health.loaded is None or (
                health.loaded.model_id,
                health.loaded.mode,
            ) == (resolved.model_id, resolved.mode)
        if await self._native(self.admission.gpu_active):
            return False
        resident = self.resident
        for other in self.resolver.backends.values():
            if other is resolved.backend or resident and other is resident.backend:
                continue
            observed, models = await self.resolver._catalog(other)
            if observed.loaded is not None:
                # Clasificar primero: una ejecución CPU verificada no retiene VRAM.
                if self._cpu_resident(observed, models):
                    continue
                return False
            if observed.state != "idle" or observed.job_id is not None:
                return False
        target_matches = health.loaded is not None and (
            health.loaded.model_id,
            health.loaded.mode,
        ) == (resolved.model_id, resolved.mode)
        if (
            health.loaded is not None
            and not target_matches
            and (not resident or resident.backend is not resolved.backend)
        ):
            return False
        if resident and (
            resident.backend is not resolved.backend
            or (resident.model_id, resident.mode) != (resolved.model_id, resolved.mode)
        ):
            if await self._native(self.admission.backend_active, resident.engine_id):
                return False
            before = await resident.backend.health()
            if (
                self._identity(before) != resident.identity
                or before.state != "idle"
                or before.job_id is not None
                or before.loaded is None
                or (before.loaded.model_id, before.loaded.mode)
                != (resident.model_id, resident.mode)
            ):
                return False
            await resident.backend.unload()
            after = await resident.backend.health()
            if (
                self._identity(after) != resident.identity
                or after.state != "idle"
                or after.job_id is not None
                or after.loaded is not None
                or after.gpu.free_mb - self.margin_mb < resolved.required_mb
            ):
                return False
            self.resident = None
            health = await resolved.backend.health()
            if (
                self._identity(health) != resolved.identity
                or health.state != "idle"
                or health.job_id is not None
                or health.loaded is not None
            ):
                return False
            target_matches = False
        return (
            target_matches
            or health.gpu.free_mb - self.margin_mb >= resolved.required_mb
        )

    async def dispatch(self, job_id=None):
        pages = self.admission.candidate_batches(job_id)
        observations = {}
        occupancy = {}
        try:
            while (jobs := await self._native(next, pages, None)) is not None:
                claim = await self._dispatch_page(jobs, job_id, observations, occupancy)
                if claim is not None:
                    return claim
        finally:
            await self.close()
            await self._native(pages.close)
        return None

    async def _dispatch_page(self, jobs, job_id, observations, occupancy):
        for job in jobs:
            # post.audio pertenece al worker CPU servidor T05, nunca a EngineBackend.
            if job.task == "post.audio":
                continue
            try:
                routed = await self.resolver.route(job, observations)
                route_context = RouteContext.from_resolved(routed)
                # La observación reutilizada sólo descarta; nunca autoriza un claim.
                if not await self._screen(routed, observations, occupancy):
                    continue
                from .references import check_job_references

                await self._native(
                    check_job_references,
                    self.admission.engine,
                    job,
                    self.resolver.data_dir,
                )
                resolved = await self.resolver.resolve(
                    job, engine=self.admission.engine, expected_route=route_context
                )
                if resolved.identity != routed.identity or (
                    resolved.backend.origin,
                    resolved.model_id,
                    resolved.mode,
                    resolved.lane,
                ) != (routed.backend.origin, routed.model_id, routed.mode, routed.lane):
                    self.resolver.invalidate(resolved.backend.origin)
                    continue
            except StaleRoute:
                self.resolver.invalidate(route_context.origin)
                self.resolver.invalidate(routed.backend.origin)
                continue
            except ResolutionError:
                if job_id is not None:
                    raise
                continue
            except (BackendFailure, OSError):
                self.resolver.invalidate(routed.backend.origin)
                continue
            try:
                if not await self._preflight(resolved):
                    continue
            except (BackendFailure, CatalogUnavailable, OSError):
                self.resolver.invalidate(resolved.backend.origin)
                continue
            try:
                claim = await self._native(self.admission.reserve, resolved)
            except PreclaimResolutionError:
                if job_id is not None:
                    raise
                continue
            if claim is None:
                continue
            occupancy.setdefault("claimed", set()).add(resolved.backend.origin)
            occupancy.setdefault("reservations", []).append(
                (resolved.lane, resolved.engine_id, 1)
            )
            if resolved.lane == "gpu":
                occupancy["gpu"] = True
            try:
                if not await self._native(self.admission.may_prepare_send, claim):
                    return claim
                if resolved.lane == "gpu":
                    acknowledged = await resolved.backend.load(claim.load_options)
                    if (acknowledged.model_id, acknowledged.mode) != (
                        claim.load_options.model_id,
                        claim.load_options.mode,
                    ):
                        raise BackendFailure("LOAD_IDENTITY")
                    self.resident = Resident(
                        resolved.backend,
                        resolved.engine_id,
                        resolved.model_id,
                        resolved.mode,
                        resolved.identity,
                    )
                if claim.selected_provenance is not None:
                    health = await resolved.backend.health()
                    provenance = capture_before_send(
                        claim.selected_provenance,
                        claim.request,
                        claim.load_options,
                        health,
                        require_loaded=resolved.lane == "gpu",
                    )
                    if not await self._native(
                        self.admission.capture_provenance,
                        claim,
                        provenance,
                        canonical_sha256(provenance),
                    ):
                        return claim
                if not await self._native(self.admission.may_send, claim):
                    return claim
                ack = await resolved.backend.submit(claim.request)
                if ack.job_id == claim.attempt_id:
                    await self._native(self.admission.acknowledge, claim)
            except (BackendFailure, ValueError):
                self.resolver.invalidate(resolved.backend.origin)
            return claim
        return None
