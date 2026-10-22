"""Orquestador local del lifespan y de los carriles engine/worker CPU."""

import asyncio
import json
import logging
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import replace
from functools import partial
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Job, JobAttempt, User
from app.publication import PublicationCoordinator
from app.worker.contracts import canonical_sha256
from app.worker.execution import CpuAudioService

from .admission import Admission, Claim, occupancy_filters
from .backends.http import HttpEngineBackend
from .backends.protocol import BackendFailure, ConfirmedAbsent
from .cancellation import Cancellation, local_jobs
from .cleanup import sweep_cancelled
from .dispatcher import Dispatcher, Resident
from .events import EventBus, EventConsumer
from .provenance import MUSIC_TASKS, SelectedProvenance, capture_before_send
from .recovery import Recovery
from .resolver import Resolver
from .retry import FrozenRetryResolver, Retry
from .synthetic_registry import SyntheticRegistry, packaged_mock_registry


class QueueRuntime:
    def __init__(
        self,
        engine,
        settings,
        *,
        backends=None,
        poll_s=0.1,
        control_s=30,
        stream_s=30,
        synthetic_registry=None,
        cpu_service=None,
    ):
        if any(not math.isfinite(v) or v <= 0 for v in (poll_s, control_s, stream_s)):
            raise ValueError("Positive finite runtime bounds required")
        self.engine, self.settings, self.poll_s = engine, settings, poll_s
        self.control_s, self.stream_s = control_s, stream_s
        self.cpu_service = cpu_service
        self.backends = (
            backends
            if backends is not None
            else {
                family: HttpEngineBackend(settings, family)
                for family in settings.engines
            }
        )
        self.owned_clients = backends is None
        self.synthetic_registry = (
            synthetic_registry
            if synthetic_registry is not None
            else packaged_mock_registry(self.backends, settings.engines)
            if self.owned_clients
            else SyntheticRegistry()
        )
        self.synthetic_registry.validate_backends(self.backends)
        self.stop = asyncio.Event()
        self.workers = {}
        self.cpu_workers = {}
        self.bus = EventBus()
        self.publication_coordinator = PublicationCoordinator()
        # ORM after-commit snapshot reconciliation uses the same barrier as
        # queue writers.  The engine attribute keeps the DB hook decoupled
        # from QueueRuntime while preventing snapshot writes from racing a
        # CPU publication CAS.
        self.engine.studio_publication_coordinator = self.publication_coordinator
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="studio-queue"
        )
        self.native = set()
        self.suspended, self.cancel_sent = set(), set()
        self.engine_origins = {}
        self.sweep_s, self._sweep_at = 2.0, 0.0

    async def dbcall(self, function, *args):
        future = self.executor.submit(function, *args)
        self.native.add(future)
        try:
            return await self._completion(asyncio.wrap_future(future))
        finally:
            # _completion waits for the actual native return, even after cancellation.
            self.native.discard(future)

    @staticmethod
    async def _completion(future):
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            while not future.done():
                try:
                    await asyncio.shield(future)
                except asyncio.CancelledError:
                    continue
                except BaseException:
                    if not future.done():
                        raise
                    break
            if not future.cancelled():
                future.exception()
            raise

    async def _close_reader(self, pages, original):
        try:
            await self.dbcall(pages.close)
        except BaseException:
            if original is None:
                raise
            self.logger.warning("queue.reader_cleanup_failed")

    async def control(self, awaitable):
        async with asyncio.timeout(self.control_s):
            return await awaitable

    def _owner(self):
        with Session(self.engine) as session:
            return session.scalar(
                select(User.id).where(User.name == "local", User.deleted_at.is_(None))
            )

    async def start(self):
        self.owner_id = await self.dbcall(self._owner)
        self.admission = Admission(
            self.engine,
            self.owner_id,
            nightly_window=self.settings.nightly_window,
            synthetic_registry=self.synthetic_registry,
        )
        self.resolver = Resolver(
            self.backends,
            data_dir=self.settings.data_dir,
            synthetic_registry=self.synthetic_registry,
        )
        self.dispatcher = Dispatcher(
            self.admission, self.resolver, margin_mb=self.settings.vram_margin_mb
        )
        self.consumer = EventConsumer(
            self.engine,
            self.owner_id,
            self.bus,
            coordinator=self.publication_coordinator,
        )
        self.recovery = Recovery(self.engine, self.owner_id, self.settings.data_dir)
        self.cancellation = Cancellation(self.engine, self.owner_id)
        self.retry = Retry(self.engine, self.owner_id)
        if self.cpu_service is None:
            self.cpu_service = self._default_cpu_service()
        if self.cpu_service is not None and hasattr(
            self.cpu_service, "reconcile_startup"
        ):
            await self.dbcall(self.cpu_service.reconcile_startup)
        if self.backends:
            await self.dbcall(self.recovery.startup)
        await self._sweep_cancelled(force=True)
        self.task = asyncio.create_task(self._run())

    def _default_cpu_service(self):
        """Create the server worker only when the pinned Docker tool exists."""
        # runtime.py vive en apps/server/app/queue; el checkout es parents[4]
        # tanto en Windows como en la imagen Linux (/studio).
        root = Path(__file__).resolve().parents[4]
        pin_path = root / "tools" / "ffmpeg-linux.lock.json"
        try:
            pin = json.loads(pin_path.read_text(encoding="utf-8"))
            ffmpeg = root / pin["dest"] / "bin" / "ffmpeg"
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            return None
        if not ffmpeg.is_file():
            return None
        # En Docker el checkout vive en /studio y los datos en el volumen /data;
        # en local, data_dir es <checkout>/data. El worker siempre recibe la raíz
        # que contiene el directorio ``data`` para resolver tmp/private-contexts.
        data_root = Path(self.settings.data_dir).parent
        return CpuAudioService(
            self.engine,
            data_root,
            coordinator=self.publication_coordinator,
            bus=self.bus,
            ffmpeg=ffmpeg,
            owner_id=self.owner_id,
            logger=getattr(self.engine, "studio_logger", None),
        )

    def _active(self):
        with Session(self.engine, expire_on_commit=False) as session:
            return list(
                session.scalars(
                    select(JobAttempt)
                    .join(Job, Job.id == JobAttempt.job_id)
                    .where(
                        Job.owner_id == self.owner_id,
                        Job.status.in_(["running", "interrupted"]),
                        Job.attempt == JobAttempt.ordinal,
                        JobAttempt.owner_id == self.owner_id,
                        JobAttempt.terminal.is_(None),
                        Job.deleted_at.is_(None),
                        JobAttempt.deleted_at.is_(None),
                        Job.id.in_(local_jobs(self.owner_id).with_only_columns(Job.id)),
                    )
                )
            )

    async def _consume(self, attempt):
        backend = await self._backend_for(attempt.engine_id)
        if backend is None:
            return
        delay, resent = self.poll_s, False
        while not self.stop.is_set():
            current = await self.dbcall(self.recovery.current, attempt.id)
            if current is None or current[0].terminal is not None:
                return
            attempt, cancelled = current
            try:
                health, models = await self.control(self.resolver._catalog(backend))
                if health.engine_id != attempt.engine_id or not any(
                    m.id == attempt.model_id for m in models
                ):
                    raise BackendFailure("RECOVERY_IDENTITY")
                status = await self.control(backend.status(attempt.id))
                if isinstance(status, ConfirmedAbsent):
                    if status.job_id != attempt.id:
                        raise BackendFailure("RECOVERY_IDENTITY")
                    if cancelled:
                        await self.dbcall(
                            self.recovery.uncertain,
                            attempt.id,
                            "Cancelación pendiente sin terminal confirmado",
                        )
                        self.suspended.add(attempt.id)
                        return
                    safe = await self.dbcall(self.recovery.safe_absent, attempt)
                    if not safe or resent:
                        # El engine confirma que no lo tiene: reintento acotado
                        # (failed retryable) en vez de quedar interrumpido.
                        await self.dbcall(
                            self.consumer.accept,
                            attempt.id,
                            attempt.engine_id,
                            self.recovery.lost_event(attempt),
                        )
                        return
                    if (
                        health.state != "idle"
                        or health.job_id is not None
                        or (
                            health.loaded is not None
                            and (health.loaded.model_id, health.loaded.mode)
                            != (attempt.model_id, attempt.mode)
                        )
                    ):
                        raise BackendFailure("RECOVERY_BUSY")
                    resolved = await self._resend_preflight(attempt, backend)
                    if not resolved:
                        raise BackendFailure("RECOVERY_ADMISSION")
                    resent = True
                    if resolved.lane == "gpu":
                        await self._load_resident(resolved, attempt.load_options)
                    if attempt.engine_request.task in MUSIC_TASKS:
                        provenance = attempt.provenance
                        if provenance is None:
                            raise BackendFailure("PROVENANCE_MISSING")
                        selected = SelectedProvenance.from_captured(
                            provenance,
                            backend=backend,
                            registry=self.synthetic_registry,
                        )
                        health = await self.control(backend.health())
                        capture_before_send(
                            selected,
                            attempt.engine_request,
                            attempt.load_options,
                            health,
                            require_loaded=resolved.lane == "gpu",
                        )
                        claim = Claim(
                            attempt.job_id,
                            attempt.id,
                            attempt.engine_request,
                            attempt.load_options,
                            selected,
                        )
                        if not await self.dbcall(
                            partial(
                                self.admission.capture_provenance, allow_submitted=True
                            ),
                            claim,
                            provenance,
                            attempt.provenance_sha256,
                        ):
                            raise BackendFailure("RECOVERY_PROVENANCE")
                    current = await self.dbcall(self.recovery.current, attempt.id)
                    if current is None or current[1] or current[0].terminal:
                        continue
                    ack = await self.control(backend.submit(attempt.engine_request))
                    if ack.job_id != attempt.id:
                        raise BackendFailure("RECOVERY_ACK")
                    await self.dbcall(
                        self.admission.acknowledge,
                        Claim(
                            attempt.job_id,
                            attempt.id,
                            attempt.engine_request,
                            attempt.load_options,
                        ),
                    )
                else:
                    if status.job_id != attempt.id:
                        raise BackendFailure("RECOVERY_IDENTITY")
                    if status.seq < attempt.last_seq:
                        await self.dbcall(
                            self.recovery.uncertain,
                            attempt.id,
                            "Cursor remoto retrocedido sin identidad de reinicio",
                        )
                        self.suspended.add(attempt.id)
                        return
                async with asyncio.timeout(self.stream_s):
                    async for event in backend.events(
                        attempt.id, after=attempt.last_seq
                    ):
                        await self.dbcall(
                            self.consumer.accept, attempt.id, attempt.engine_id, event
                        )
                        if event.type in {"done", "error", "cancelled"}:
                            return
            except (BackendFailure, OSError, ValueError, TimeoutError):
                await self.dbcall(
                    self.recovery.uncertain,
                    attempt.id,
                    "Observación desconocida; intento conservado",
                )
            try:
                await asyncio.wait_for(self.stop.wait(), delay)
            except TimeoutError:
                pass
            delay = min(delay * 2, 5)

    async def _resend_preflight(self, attempt, backend):
        with Session(self.engine) as session:
            job = session.get(Job, attempt.job_id)
            frozen = self.retry.frozen_job(job, attempt, attempt.mode)
        resolver = FrozenRetryResolver(
            self.backends,
            data_dir=self.settings.data_dir,
            synthetic_registry=self.synthetic_registry,
        )
        resolved = await self.control(resolver.resolve(frozen, engine=self.engine))
        if resolved.backend is not backend or resolved.engine_id != attempt.engine_id:
            return False
        if attempt.engine_request.task in MUSIC_TASKS:
            if attempt.provenance is None or resolved.selected_provenance is None:
                return False
            selected = SelectedProvenance.from_captured(
                attempt.provenance, backend=backend, registry=self.synthetic_registry
            )
            if (
                resolved.selected_provenance.descriptor != selected.descriptor
                or resolved.identity
                != (
                    selected.engine_id,
                    selected.engine_version,
                    attempt.provenance.reported_image_digest or "unknown",
                )
                or not selected.binds(attempt.engine_request, attempt.load_options)
            ):
                return False
            resolved = replace(resolved, selected_provenance=selected)
        other = await self.dbcall(
            self.recovery.other_active, attempt.job_id, resolved.lane, attempt.engine_id
        )
        if other:
            return False
        observations = {}
        routed = await self.control(resolver.route(frozen, observations))
        if routed.identity != resolved.identity or not await self.dispatcher._screen(
            routed, observations, {"gpu": other}
        ):
            return False
        health = await self.control(backend.health())
        if (
            self.dispatcher._identity(health) != resolved.identity
            or health.state != "idle"
            or health.job_id is not None
        ):
            return False
        matches = health.loaded is not None and (
            health.loaded.model_id,
            health.loaded.mode,
        ) == (attempt.model_id, attempt.mode)
        if health.loaded is not None and not matches:
            return False
        admitted = (
            resolved.lane == "cpu"
            or matches
            or health.gpu.free_mb - self.settings.vram_margin_mb >= resolved.required_mb
        )
        return resolved if admitted else False

    async def _load_resident(self, resolved, options):
        acknowledged = await self.control(resolved.backend.load(options))
        if (acknowledged.model_id, acknowledged.mode) != (
            options.model_id,
            options.mode,
        ):
            raise BackendFailure("LOAD_IDENTITY")
        if resolved.lane == "gpu":
            self.dispatcher.resident = Resident(
                resolved.backend,
                resolved.engine_id,
                acknowledged.model_id,
                acknowledged.mode,
                resolved.identity,
            )

    async def _backend_for(self, engine_id):
        matches = []
        for backend in self.backends.values():
            try:
                health, _ = await self.control(self.resolver._catalog(backend))
                if health.engine_id == engine_id:
                    matches.append(backend)
            except (BackendFailure, OSError, ValueError, TimeoutError):
                continue
        if len(matches) != 1:
            return None
        backend = matches[0]
        registered = self.engine_origins.setdefault(engine_id, backend.origin)
        return backend if registered == backend.origin else None

    async def _cancel(self):
        for aid, engine_id in await self.dbcall(self.cancellation.pending):
            if aid in self.cancel_sent:
                continue
            backend = await self._backend_for(engine_id)
            if backend is None:
                continue
            try:
                health = await self.control(backend.health())
                if health.engine_id != engine_id or (
                    health.job_id is not None and health.job_id != aid
                ):
                    continue
                status = await self.control(backend.status(aid))
                if isinstance(status, ConfirmedAbsent) or status.job_id != aid:
                    continue
                ack = await self.control(backend.cancel(aid))
                if ack.job_id == aid:
                    self.cancel_sent.add(aid)
            except (BackendFailure, OSError, ValueError, TimeoutError):
                pass

    async def _retry(self):
        observations, rejected = {}, set()
        resolver = FrozenRetryResolver(
            self.backends,
            data_dir=self.settings.data_dir,
            synthetic_registry=self.synthetic_registry,
        )
        occupancy = await self.dbcall(self._retry_occupancy)
        screening = {
            "gpu": any(lane == "gpu" and count for lane, _, count in occupancy)
        }
        pages = self.retry.candidate_batches()
        try:
            while (page := await self.dbcall(next, pages, None)) is not None:
                await self._retry_page(
                    page, resolver, observations, rejected, occupancy, screening
                )
        finally:
            await self._close_reader(pages, sys.exception())

    def _candidate_batches(self):
        """Dos streams reales, un snapshot WAL y una autoridad de orden/FIFO."""
        with Session(self.engine) as reader, reader.begin(), ExitStack() as cleanup:
            queued = self.admission.candidate_batches(reader=reader)
            retries = self.retry.candidate_batches(reader=reader)
            cleanup.callback(queued.close)
            cleanup.callback(retries.close)

            def rows(pages, retry):
                for page in pages:
                    for row in page:
                        yield row if retry else (row, None)

            streams = [rows(queued, False), rows(retries, True)]
            heads = [next(stream, None) for stream in streams]
            page = []
            while any(head is not None for head in heads):
                index = min(
                    (i for i, head in enumerate(heads) if head is not None),
                    key=lambda i: self.admission._order(heads[i][0]),
                )
                page.append(heads[index])
                heads[index] = next(streams[index], None)
                if len(page) == 400:
                    yield page
                    page = []
            if page:
                yield page

    async def _arbitrate(self):
        observations, rejected, screening = {}, set(), {}
        resolver = FrozenRetryResolver(
            self.backends,
            data_dir=self.settings.data_dir,
            synthetic_registry=self.synthetic_registry,
        )
        occupancy = await self.dbcall(self._retry_occupancy)
        screening["gpu"] = any(lane == "gpu" and count for lane, _, count in occupancy)
        pages = self._candidate_batches()
        try:
            while (page := await self.dbcall(next, pages, None)) is not None:
                for job, previous in page:
                    if previous is not None:
                        claim = await self._retry_page(
                            [(job, previous)],
                            resolver,
                            observations,
                            rejected,
                            occupancy,
                            screening,
                        )
                        if claim is not None:
                            occupancy.append((job.lane, previous.engine_id, 1))
                            screening.setdefault("claimed", set()).add(
                                self.engine_origins[previous.engine_id]
                            )
                            if job.lane == "gpu":
                                screening["gpu"] = True
                    else:
                        claim = await self.control(
                            self.dispatcher._dispatch_page(
                                [job], None, observations, screening
                            )
                        )
                        if claim is not None:
                            occupancy.extend(screening.pop("reservations", []))
        finally:
            await self._close_reader(pages, sys.exception())

    async def _dispatch_cpu(self):
        if self.cpu_service is None or len(self.cpu_workers) >= 2:
            return
        # Primero los posts interrumpidos cuyo proceso anterior se prueba muerto
        # (se reanudan sobre su misma cpu_execution); luego los encolados.
        resumable = []
        if hasattr(self.cpu_service, "resumable_jobs"):
            resumable = await self.dbcall(self.cpu_service.resumable_jobs)
        for job_id in resumable:
            if len(self.cpu_workers) >= 2:
                return
            if job_id not in self.cpu_workers:
                self.cpu_workers[job_id] = asyncio.create_task(
                    self._consume_cpu(job_id), name=f"cpu-post-{job_id}"
                )
        candidates = await self.dbcall(self.admission.candidates)
        for job in candidates:
            if len(self.cpu_workers) >= 2:
                break
            if job.task != "post.audio" or job.id in self.cpu_workers:
                continue
            task = asyncio.create_task(
                self._consume_cpu(job.id), name=f"cpu-post-{job.id}"
            )
            self.cpu_workers[job.id] = task

    async def _cancel_cpu(self):
        if self.cpu_service is None or not hasattr(
            self.cpu_service, "pending_cancellations"
        ):
            return
        for job_id in await self.dbcall(self.cpu_service.pending_cancellations):
            await self.dbcall(self.cpu_service.cancel_job, job_id)

    async def _sweep_cancelled(self, force=False):
        """Borra ``data/tmp`` de los jobs cancelados que nadie más necesita (CA-3)."""
        owner = getattr(self, "owner_id", None)
        if owner is None or not hasattr(self, "settings"):
            return
        now = time.monotonic()
        if not force and now < getattr(self, "_sweep_at", 0.0):
            return
        self._sweep_at = now + getattr(self, "sweep_s", 2.0)
        try:
            await self.dbcall(
                sweep_cancelled,
                self.engine,
                owner,
                self.settings.data_dir,
                getattr(self.engine, "studio_logger", None),
            )
        except Exception:  # noqa: BLE001 -- la limpieza nunca para la cola
            self.logger.warning("queue.cleanup_failed")

    async def _consume_cpu(self, job_id):
        try:
            return await self.dbcall(self.cpu_service.execute_job, job_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            try:
                await self.dbcall(
                    self.cpu_service.fail_plan, job_id, "CPU_EXECUTION_FAILED"
                )
            except Exception:  # noqa: BLE001 - conservar el error del worker.
                self.logger.warning("queue.cpu_failure_persist_failed")
            raise

    def _retry_occupancy(self):
        with Session(self.engine) as session:
            active, occupied, owned, live = occupancy_filters(self.owner_id)
            rows = list(
                session.execute(
                    select(Job.lane, Job.engine_id, func.count())
                    .where(
                        active,
                        occupied,
                        owned,
                        live,
                    )
                    .group_by(Job.lane, Job.engine_id)
                )
            )
            return rows

    async def _retry_page(
        self, page, retry_resolver, observations, rejected, occupancy, screening=None
    ):
        if screening is None:
            screening = {}
        for job, previous in page:
            claim = None
            if (
                previous.engine_id in rejected
                or any(engine_id == previous.engine_id for _, engine_id, _ in occupancy)
                or sum(count for lane, _, count in occupancy if lane == job.lane)
                >= {"gpu": 1, "cpu": 2}[job.lane]
            ):
                continue
            matches = []
            for candidate in self.backends.values():
                try:
                    health, _ = await self.control(
                        retry_resolver.observed_catalog(candidate, observations)
                    )
                    if health.engine_id == previous.engine_id:
                        matches.append(candidate)
                except (BackendFailure, OSError, ValueError, TimeoutError):
                    continue
            backend = matches[0] if len(matches) == 1 else None
            if backend is None:
                continue
            registered = self.engine_origins.setdefault(
                previous.engine_id, backend.origin
            )
            if registered != backend.origin:
                continue
            observed = observations[backend.origin][0]
            if observed.state != "idle" or observed.job_id is not None:
                rejected.add(previous.engine_id)
                continue
            try:
                self.resolver.invalidate(backend.origin)
                health, models = await self.control(self.resolver._catalog(backend))
                if health.engine_id != previous.engine_id or self.dispatcher._identity(
                    health
                ) != self.dispatcher._identity(observed):
                    rejected.add(previous.engine_id)
                    continue
                if health.state != "idle" or health.job_id is not None:
                    rejected.add(previous.engine_id)
                    continue
                mode = previous.mode
                if previous.terminal.data["code"] == "VRAM_EXCEEDED":
                    model = next((m for m in models if m.id == previous.model_id), None)
                    if (
                        not model
                        or not any(m.id == "offload" for m in model.modes)
                        or mode == "offload"
                    ):
                        continue
                    mode = "offload"
                frozen = self.retry.frozen_job(job, previous, mode)
                fresh_observations = dict(observations)
                fresh_observations[backend.origin] = (health, models)
                routed = await self.control(
                    retry_resolver.route(frozen, fresh_observations)
                )
                if routed.backend is not backend or not await self.dispatcher._screen(
                    routed, fresh_observations, screening
                ):
                    continue
                retry_resolver.invalidate(backend.origin)
                resolved = await self.control(
                    retry_resolver.resolve(frozen, engine=self.engine)
                )
                if (
                    resolved.backend is not backend
                    or resolved.identity != routed.identity
                ):
                    continue
                await self.dbcall(self.recovery.safe_inputs, previous)
                if not await self.dispatcher._preflight(resolved):
                    continue
                claim = await self.dbcall(
                    self.retry.reserve, job.id, previous.id, resolved
                )
                if claim is None:
                    continue
                if not await self.dbcall(self.admission.may_prepare_send, claim):
                    return claim
                if resolved.lane == "gpu":
                    await self._load_resident(resolved, claim.load_options)
                if claim.selected_provenance is not None:
                    health = await self.control(backend.health())
                    provenance = capture_before_send(
                        claim.selected_provenance,
                        claim.request,
                        claim.load_options,
                        health,
                        require_loaded=resolved.lane == "gpu",
                    )
                    if not await self.dbcall(
                        self.admission.capture_provenance,
                        claim,
                        provenance,
                        canonical_sha256(provenance),
                    ):
                        return claim
                if not await self.dbcall(self.admission.may_send, claim):
                    return claim
                ack = await self.control(backend.submit(claim.request))
                if ack.job_id == claim.attempt_id:
                    await self.dbcall(self.admission.acknowledge, claim)
            except (BackendFailure, OSError, ValueError, TimeoutError):
                self.resolver.invalidate(backend.origin)
            if claim is not None:
                return claim

    async def _run(self):
        while not self.stop.is_set():
            for job_id, task in list(self.cpu_workers.items()):
                if task.done():
                    if not task.cancelled():
                        try:
                            task.result()
                        except Exception:
                            self.logger.exception("queue.cpu_worker_failed")
                    del self.cpu_workers[job_id]
            for aid, task in list(self.workers.items()):
                if task.done():
                    if not task.cancelled() and task.exception():
                        self.logger.warning("queue.observation_failed")
                    del self.workers[aid]
            try:
                await self._cancel_cpu()
                await self._sweep_cancelled()
                if self.backends:
                    await self._cancel()
                    for attempt in await self.dbcall(self._active):
                        if (
                            attempt.id not in self.workers
                            and attempt.id not in self.suspended
                        ):
                            self.workers[attempt.id] = asyncio.create_task(
                                self._consume(attempt)
                            )
                    await self._arbitrate()
                # Prioriza la generación antes de ocupar los dos slots del
                # worker post.audio; el engine-mock CPU comparte ese límite.
                await self._dispatch_cpu()
            except (BackendFailure, ValueError, OSError, TimeoutError):
                self.logger.warning("queue.dispatch_failed")
            except Exception:
                self.logger.exception("queue.dispatch_unexpected_failed")
            try:
                await asyncio.wait_for(self.stop.wait(), self.poll_s)
            except TimeoutError:
                pass

    async def close(self):
        if not hasattr(self, "_closing"):
            self._closing = asyncio.create_task(self._close())
        await self._completion(self._closing)

    async def _close(self):
        self.stop.set()
        if hasattr(self, "task"):
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        for task in self.workers.values():
            task.cancel()
        for task in self.cpu_workers.values():
            task.cancel()
        await asyncio.gather(
            *self.workers.values(), *self.cpu_workers.values(), return_exceptions=True
        )
        self.workers.clear()
        self.cpu_workers.clear()
        await asyncio.gather(
            *(asyncio.wrap_future(future) for future in tuple(self.native)),
            return_exceptions=True,
        )
        if hasattr(self, "dispatcher"):
            await self.dispatcher.close()
        await asyncio.to_thread(self.executor.shutdown, wait=True, cancel_futures=False)
        if self.owned_clients:
            await asyncio.gather(
                *(backend.aclose() for backend in self.backends.values())
            )
