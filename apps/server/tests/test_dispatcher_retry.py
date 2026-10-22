"""Retry confirmado con identidad nueva y parámetros congelados."""

import asyncio

import pytest
from app.models import Job, JobAttempt
from app.queue.runtime import QueueRuntime
from engine_contract import JobStatus
from sqlalchemy import select
from sqlalchemy.orm import Session
from synthetic_composition import composition
from test_dispatcher_recovery import RecordedBackend, event, prepared, settings
from test_dispatcher_recovery import engine as engine  # noqa: PLC0414


def test_retryable_durable_error_reserves_new_id_frozen_parameters(engine):
    jid, _, claim = prepared(engine)
    backend = RecordedBackend()
    backend.record = JobStatus(job_id=claim.attempt_id, state="error", seq=1)
    backend.events_value = [
        event(
            claim.attempt_id,
            "error",
            {"code": "INTERNAL", "message": "synthetic failure", "retryable": True},
        )
    ]
    with Session(engine) as session, session.begin():
        session.get(Job, jid).request = {
            "params": {"style": "changed", "duration_s": 9},
            "seed": 999,
            "mode": "bf16",
            "timeout_s": 60,
        }

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.sleep(0.6)
            with Session(engine) as session:
                attempts = list(
                    session.scalars(
                        select(JobAttempt)
                        .where(JobAttempt.job_id == jid)
                        .order_by(JobAttempt.ordinal)
                    )
                )
                assert len(attempts) == 2, (
                    "Durable retryable error never reserves next attempt"
                )
                assert attempts[1].id != claim.attempt_id
                assert attempts[1].engine_request.params == claim.request.params
                assert attempts[1].engine_request.seed == 17
                assert attempts[0].terminal.type == "error"
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize("change", ["busy", "identity", "model", "unverified", "mode"])
def test_retry_positive_observation_cannot_authorize_changed_backend(engine, change):
    failed_attempts(engine, 1)
    backend = StatefulRetryBackend()
    original_health = backend.health

    async def changed():
        value = await original_health()
        if backend.health_calls >= 2:
            if change == "busy":
                return value.model_copy(update={"state": "busy"})
            if change == "identity":
                return value.model_copy(update={"image_digest": "changed"})
            if change == "model":
                backend.value["id"] = "foreign"
            if change == "unverified":
                backend.value["tasks"]["music.instrumental"]["verified"] = False
            if change == "mode":
                backend.value["modes"] = [
                    {"id": "offload", "vram_mb": 500, "notes": "synthetic"}
                ]
        return value

    backend.health = changed

    async def run():
        runtime = await paused_runtime(engine, {"alias": backend})
        try:
            await runtime._retry()
            assert not backend.posts and not backend.unloads and backend.loaded is None
            assert runtime.dispatcher.resident is None
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "scenario",
    [
        "failed_load",
        "lost_load_ack",
        "foreign_ack",
        "may_send_first",
        "may_send_second",
        "writer_cancel",
    ],
)
def test_retry_load_and_writer_uncertainty_never_grant_unsafe_dispatch(
    engine, scenario
):
    from app.queue.backends.protocol import BackendFailure
    from engine_contract import LoadedModel
    from test_dispatcher_admission import add

    jid, _, _ = failed_attempts(engine, 1)
    backend = StatefulRetryBackend()
    original_load = backend.load

    async def load(request):
        if scenario == "failed_load":
            raise BackendFailure("SYNTHETIC")
        loaded = await original_load(request)
        if scenario == "lost_load_ack":
            raise BackendFailure("SYNTHETIC_ACK_LOST")
        if scenario == "foreign_ack":
            return LoadedModel(model_id="foreign", mode="bf16")
        return loaded

    backend.load = load

    async def run():
        runtime = await paused_runtime(engine, {"alias": backend})
        try:
            if scenario.startswith("may_send"):
                calls = []

                def may_send(claim):
                    calls.append(claim.attempt_id)
                    return len(calls) < (1 if scenario == "may_send_first" else 2)

                runtime.admission.may_send = may_send
                runtime.admission.may_prepare_send = may_send
            if scenario == "writer_cancel":
                reserve = runtime.retry.reserve

                def cancelled(*args):
                    with Session(engine) as session, session.begin():
                        session.get(
                            Job, jid
                        ).cancel_requested_at = "2026-10-08T02:00:00Z"
                    return reserve(*args)

                runtime.retry.reserve = cancelled
            await runtime._retry()
            assert not backend.posts
            if scenario != "may_send_second":
                assert runtime.dispatcher.resident is None
            else:
                assert runtime.dispatcher.resident.model_id == "mock"
            next_id, _ = add(engine)
            if scenario == "writer_cancel":
                dispatched = await runtime.dispatcher.dispatch(next_id)
                assert dispatched is not None
                assert backend.posts[-1].job_id == dispatched.attempt_id
                assert not backend.unloads
                return
            assert await runtime.dispatcher.dispatch(next_id) is None
            assert not backend.unloads and not backend.posts
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize("scenario", ["failed_load", "foreign_ack", "working_unknown"])
def test_recovery_without_owned_load_ack_preserves_unknown_residency(engine, scenario):
    from app.queue.backends.protocol import BackendFailure
    from engine_contract import LoadedModel
    from test_dispatcher_admission import add

    backend = StatefulRetryBackend()
    jid, _, claim = prepared(engine, backend=backend)
    if scenario == "working_unknown":
        backend.loaded = LoadedModel(model_id="mock", mode="offload")
        backend.record = JobStatus(job_id=claim.attempt_id, state="done", seq=1)
    else:

        async def load(request):
            if scenario == "failed_load":
                raise BackendFailure("SYNTHETIC")
            backend.loaded = LoadedModel(model_id="foreign", mode="bf16")
            return backend.loaded

        backend.load = load

    async def run():
        runtime = await paused_runtime(engine, {"alias": backend})
        try:
            if scenario == "working_unknown":
                await runtime._consume(runtime.recovery.current(claim.attempt_id)[0])
            else:
                with pytest.raises(TimeoutError):
                    async with asyncio.timeout(0.08):
                        await runtime._consume(
                            runtime.recovery.current(claim.attempt_id)[0]
                        )
            assert runtime.dispatcher.resident is None
            next_id, _ = add(engine)
            assert await runtime.dispatcher.dispatch(next_id) is None
            assert not backend.posts and not backend.unloads
            with Session(engine) as session:
                assert session.get(Job, jid).attempt == 1
        finally:
            await runtime.close()

    asyncio.run(run())


def test_retry_snapshot_pages_are_finite_fifo_and_keep_history(engine):
    from app.models import new_id
    from app.queue.retry import Retry
    from sqlalchemy import event as sql_event
    from sqlalchemy import func

    _, owner, _ = failed_attempts(engine, 801)
    with Session(engine) as session, session.begin():
        jobs = list(session.scalars(select(Job).order_by(Job.id)))
        for index, job in enumerate(jobs):
            job.created_at = f"2026-10-08T01:00:00.{index:06d}Z"
            job.priority = "interactive" if index == 800 else "batch"
        expected = [jobs[-1].id] + [job.id for job in jobs[:-1]]
    queries = []
    materialized = []

    def loaded(session, instance):
        if isinstance(instance, (Job, JobAttempt)):
            materialized.append(len(session.identity_map))

    def observe(connection, cursor, statement, params, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    sql_event.listen(engine, "before_cursor_execute", observe)
    sql_event.listen(Session, "loaded_as_persistent", loaded)
    pages = Retry(engine, owner).candidate_batches()
    try:
        first = next(pages)
        # Writer concurrente: inserción tardía, fecha anterior, excluida del snapshot.
        with Session(engine) as session, session.begin():
            source = session.get(Job, first[0][0].id)
            previous = session.get(JobAttempt, first[0][1].id)
            jid, aid = new_id(), new_id()
            session.add(
                Job(
                    id=jid,
                    owner_id=owner,
                    song_id=source.song_id,
                    task=source.task,
                    lane="gpu",
                    status="failed",
                    attempt=1,
                    created_at="2026-10-07T00:00:00Z",
                    request={},
                )
            )
            body = previous.engine_request.model_dump(mode="json")
            body.update(job_id=aid, output_dir="tmp/" + aid)
            terminal = previous.terminal.model_dump(mode="json")
            terminal["job_id"] = aid
            session.add(
                JobAttempt(
                    id=aid,
                    owner_id=owner,
                    job_id=jid,
                    ordinal=1,
                    engine_id="mock",
                    model_id="mock",
                    mode="bf16",
                    status="failed",
                    last_seq=1,
                    terminal=terminal,
                    engine_request=body,
                    load_options=previous.load_options,
                )
            )
        rest = list(pages)
    finally:
        pages.close()
        sql_event.remove(engine, "before_cursor_execute", observe)
        sql_event.remove(Session, "loaded_as_persistent", loaded)
    assert [len(first)] + [len(page) for page in rest] == [400, 400, 1]
    assert [job.id for page in [first, *rest] for job, _ in page] == expected
    candidate_queries = [query for query in queries if "JOIN job_attempt" in query]
    print(
        {
            "eligible": 801,
            "page_sizes": [400, 400, 1],
            "candidate_selects": len(candidate_queries),
            "peak_ORM_identity_map": max(materialized),
        }
    )
    assert len(candidate_queries) == 1, "Retry snapshot rescanned between bounded pages"
    assert max(materialized) <= 800, "Unbounded retry ORM materialization"
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(JobAttempt)) == 802
    assert len(list(Retry(engine, owner).candidates())) == 802
    assert engine.pool.checkedout() == 0, (
        "Retry snapshot reader retained after completion"
    )


def test_retry_fifo_mixed_fraction_precision_native(engine):
    from app.queue.retry import Retry

    _, owner, _ = failed_attempts(engine, 4)
    stamps = [
        "2026-10-08T01:00:00.123Z",
        "2026-10-08T01:00:00.123001Z",
        "2026-10-08T01:00:00.999999Z",
        "2026-10-08T01:00:01Z",
    ]
    with Session(engine) as session, session.begin():
        jobs = list(session.scalars(select(Job).order_by(Job.id)))
        expected = [job.id for job in jobs]
        for job, stamp in zip(jobs, stamps, strict=True):
            job.priority, job.created_at = "normal", stamp
    assert [job.id for job, _ in Retry(engine, owner).candidates()] == expected


@pytest.mark.parametrize("offset", ["Z", "+02:00", "-05:00"])
@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_retry_not_before_exact_microseconds_and_offset_native(
    engine, monkeypatch, offset, delta
):
    from datetime import datetime, timedelta, timezone

    import app.queue.retry as retry_module

    jid, owner, _ = failed_attempts(engine, 1)
    fixed = datetime(2026, 10, 8, 2, 0, 0, 123456, tzinfo=timezone.utc)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(retry_module, "datetime", Clock)
    zone = timezone(timedelta(hours={"Z": 0, "+02:00": 2, "-05:00": -5}[offset]))
    due = (fixed + timedelta(microseconds=delta)).astimezone(zone).isoformat()
    if offset == "Z":
        due = due.replace("+00:00", "Z")
    with Session(engine) as session, session.begin():
        # El esquema nativo actual sólo admite Z. El offset se prueba en la
        # autoridad pura y su prefiltrado SQLite, sin relajar CHECKs.
        session.get(Job, jid).not_before = (
            (fixed + timedelta(microseconds=delta)).isoformat().replace("+00:00", "Z")
        )
    assert bool(list(retry_module.Retry(engine, owner).candidates())) is (delta <= 0)
    job, attempt = (
        next(retry_module.Retry(engine, owner).candidates())
        if delta <= 0
        else (None, None)
    )
    if job is None:
        with Session(engine) as session:
            job = session.get(Job, jid)
            attempt = session.scalar(select(JobAttempt).where(JobAttempt.job_id == jid))
    job.not_before = due
    assert retry_module.Retry.eligible(job, attempt) is (delta <= 0)
    from sqlalchemy import text

    with engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT julianday(:due) <= julianday(:now)"),
                {"due": due, "now": fixed.isoformat()},
            )
            == 1
        )


@pytest.mark.parametrize("bad", [True, 1, "", "wrong", "2026-10-08T01:00:00"])
def test_retry_bad_date_never_gives_permission(engine, bad):
    from app.queue.retry import Retry

    _jid, owner, _ = failed_attempts(engine, 1)
    job, attempt = next(Retry(engine, owner).candidates())
    job.not_before = bad
    assert not Retry.eligible(job, attempt)


class StatefulRetryBackend(RecordedBackend):
    """Doble local: load/unload/terminal cambian la residencia real observada."""

    def __init__(self, identity="mock"):
        import copy

        from test_queue_resolver import descriptor

        recipe = descriptor()
        recipe["id"] = identity
        recipe["modes"].append({"id": "offload", "vram_mb": 500, "notes": "synthetic"})
        cpu_recipe = copy.deepcopy(recipe)
        for task in cpu_recipe["tasks"].values():
            task["device"] = "cpu"
        super().__init__(
            origin="http://engine-" + identity + ":8199",
            engine_id=identity,
            recipes=[recipe, cpu_recipe],
        )
        self.identity = identity
        self.origin = "http://engine-" + identity + ":8199"
        self.value["id"] = identity
        self.value["modes"].append(
            {"id": "offload", "vram_mb": 500, "notes": "synthetic"}
        )
        self.loaded = None
        self.running = None
        self.unloads = 0
        self.health_calls = 0
        self.force_busy = False

    async def health(self):
        self.health_calls += 1
        await asyncio.sleep(0)
        value = await super().health()
        return value.model_copy(
            update={
                "engine_id": self.identity,
                "loaded": self.loaded,
                "state": "busy" if self.running or self.force_busy else "idle",
                "job_id": self.running,
            }
        )

    async def load(self, request):
        self.loaded = await super().load(request)
        return self.loaded

    async def unload(self):
        assert self.running is None
        self.unloads += 1
        self.loaded = None

    async def submit(self, request):
        self.running = request.job_id
        return await super().submit(request)

    async def events(self, aid, after=0):
        self.running = None
        yield event(
            aid,
            "done",
            {
                "artifacts": [],
                "telemetry": {"mode": self.loaded.mode, "model_revision": "synthetic"},
            },
        )


async def paused_runtime(engine, backends):
    runtime = QueueRuntime(
        engine, settings(), backends=backends, synthetic_registry=composition(backends)
    )
    await runtime.start()
    runtime.task.cancel()
    await asyncio.gather(runtime.task, return_exceptions=True)
    return runtime


def failed_attempts(engine, size, *, scenario="eligible"):
    """Historias reales head0005; ningún SELECT durante la inserción masiva."""
    from app.models import new_id
    from app.queue.events import EventBus, EventConsumer

    jid, owner, claim = prepared(engine)
    EventConsumer(engine, owner, EventBus()).accept(
        claim.attempt_id,
        "mock",
        event(
            claim.attempt_id,
            "error",
            {"code": "INTERNAL", "message": "synthetic", "retryable": True},
        ),
    )
    with Session(engine) as session, session.begin():
        source = session.get(Job, jid)
        row_owner, song_id = owner, source.song_id
        for index in range(size - 1):
            job_id, aid = new_id(), new_id()
            ordinal = 3 if scenario in {"exhausted", "foreign"} else 1
            job = Job(
                id=job_id,
                owner_id=row_owner,
                song_id=song_id,
                task=source.task,
                lane="gpu",
                status="failed",
                attempt=ordinal,
                engine_id="mock",
                model_id="mock",
                request={},
                priority="interactive",
            )
            if scenario == "future":
                job.not_before = "2099-10-08T02:00:00Z"
            if scenario == "cancelled":
                job.cancel_requested_at = "2026-10-08T02:00:00Z"
            if scenario == "deleted":
                job.deleted_at = "2026-10-08T02:00:00Z"
            body = claim.request.model_dump(mode="json")
            body.update(job_id=aid, output_dir="tmp/" + aid)
            terminal = event(
                aid,
                "error",
                {
                    "code": "INTERNAL",
                    "message": "synthetic",
                    "retryable": scenario != "nonretryable",
                },
            ).model_dump(mode="json")
            session.add(job)
            session.add(
                JobAttempt(
                    id=aid,
                    owner_id=row_owner,
                    job_id=job_id,
                    ordinal=ordinal,
                    engine_id="mock",
                    model_id="mock",
                    mode="bf16",
                    engine_request=body,
                    load_options=claim.load_options,
                    status="failed",
                    last_seq=1,
                    terminal=terminal,
                )
            )
    return jid, owner, claim


def test_retry_reserve_ignores_orphan_interrupted_cpu_job(engine):
    from app.queue.retry import Retry
    from test_dispatcher_admission import add, resolve
    from test_dispatcher_retry import failed_attempts

    jid, owner, claim = failed_attempts(engine, 1)
    add(
        engine,
        status="interrupted",
        lane="cpu",
        task="audio.beats",
        engine_id="mock",
        model_id="mock",
    )

    retry = Retry(engine, owner)
    job, previous = next(retry.candidates())
    resolved = resolve(retry.frozen_job(job, previous, previous.mode))
    assert job.id == jid
    assert retry.reserve(jid, claim.attempt_id, resolved) is not None


@pytest.mark.parametrize("next_engine", ["mock", "other"])
@pytest.mark.parametrize("recovery", [False, True])
def test_acknowledged_residence_allows_actual_next_dispatch(
    engine, next_engine, recovery
):
    from app.queue.dispatcher import Resident
    from app.queue.events import EventBus, EventConsumer
    from engine_contract import LoadRequest
    from test_dispatcher_admission import add

    backend, other = StatefulRetryBackend(), StatefulRetryBackend("other")
    jid, owner, claim = prepared(engine, backend=backend)
    if not recovery:
        EventConsumer(engine, owner, EventBus()).accept(
            claim.attempt_id,
            "mock",
            event(
                claim.attempt_id,
                "error",
                {"code": "VRAM_EXCEEDED", "message": "synthetic", "retryable": True},
            ),
        )

    async def run():
        runtime = await paused_runtime(engine, {"alias": backend, "other": other})
        try:
            if recovery:
                await runtime._consume(runtime.recovery.current(claim.attempt_id)[0])
                assert backend.posts[0] == claim.request
            else:
                await backend.load(LoadRequest(model_id="mock", mode="bf16"))
                runtime.dispatcher.resident = Resident(
                    backend,
                    "mock",
                    "mock",
                    "bf16",
                    runtime.dispatcher._identity(await backend.health()),
                )
                await runtime._retry()
                with Session(engine) as session:
                    current = session.scalar(
                        select(JobAttempt).where(
                            JobAttempt.job_id == jid, JobAttempt.ordinal == 2
                        )
                    )
                assert current.mode == "offload" and backend.loaded.mode == "offload"
                await runtime._consume(current)
            with Session(engine) as session:
                assert session.get(Job, jid).status == "succeeded"
            next_id, _ = add(engine, engine_id=next_engine, model_id=next_engine)
            dispatched = await runtime.dispatcher.dispatch(next_id)
            assert dispatched is not None, (
                "Acknowledged residence lost: next dispatch blocked"
            )
            assert dispatched.request.mode == "bf16"
            target = backend if next_engine == "mock" else other
            assert target.posts[-1].job_id == dispatched.attempt_id
            if not recovery or next_engine != "mock":
                assert backend.unloads == (1 if recovery else 2)
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize("size", [200, 400])
@pytest.mark.parametrize(
    "scenario",
    ["exhausted", "nonretryable", "future", "cancelled", "foreign", "deleted"],
)
def test_retry_history_native_selects_are_bounded_and_tail_survives(
    engine, size, scenario
):
    from app.queue.retry import Retry
    from sqlalchemy import event as sql_event

    jid, owner, _ = failed_attempts(engine, size, scenario=scenario)
    queries = []

    def observe(connection, cursor, statement, params, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    sql_event.listen(engine, "before_cursor_execute", observe)
    try:
        if scenario == "foreign":
            from app.models import new_id

            assert list(Retry(engine, new_id()).candidates()) == []
        candidates = list(Retry(engine, owner).candidates())
    finally:
        sql_event.remove(engine, "before_cursor_execute", observe)
    print(
        {
            "scenario": scenario,
            "rows": size,
            "selects": len(queries),
            "candidates": len(candidates),
        }
    )
    assert [j.id for j, _ in candidates] == [jid]
    assert len(queries) <= 3, "Historical retry N+1"


@pytest.mark.parametrize("size", [200, 400])
def test_busy_retry_observations_bounded_and_public_cpu_dispatch_continues(
    engine, size
):
    import time

    from test_dispatcher_admission import add

    _, _, _ = failed_attempts(engine, size)
    cpu_id, _ = add(
        engine,
        engine_id="other",
        model_id="other",
        task="audio.beats",
        lane="cpu",
        request={"params": {}, "mode": "bf16"},
    )
    busy, other = StatefulRetryBackend(), StatefulRetryBackend("other")
    busy.force_busy = True

    async def run():
        runtime = await paused_runtime(engine, {"alias": busy, "cpu": other})
        ticks = []

        async def heartbeat():
            while True:
                ticks.append(1)
                await asyncio.sleep(0)

        beat = asyncio.create_task(heartbeat())
        try:
            started = time.perf_counter()
            await runtime._retry()
            elapsed = time.perf_counter() - started
            retry_health, retry_models = busy.health_calls, busy.calls
            claim = await runtime.dispatcher.dispatch()
            print(
                {
                    "rows": size,
                    "busy_health": retry_health,
                    "busy_models": retry_models,
                    "heartbeat_ticks": len(ticks),
                    "cpu_posts": len(other.posts),
                    "synthetic_backend_native_sql_retry_seconds": elapsed,
                }
            )
            assert claim is not None and other.posts[-1].job_id == claim.attempt_id
            assert claim.job_id == cpu_id
            assert not busy.posts and not busy.unloads
            assert retry_health <= 4 and retry_models <= 2, (
                "Repeated busy negative observations"
            )
            assert ticks
        finally:
            beat.cancel()
            await asyncio.gather(beat, return_exceptions=True)
            await runtime.close()

    asyncio.run(run())


def test_retry_terminal_string_truth_is_rejected_by_native_validation(engine):
    from app.queue.retry import Retry
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    _, owner, claim = failed_attempts(engine, 1)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE job_attempt SET terminal=json_set(terminal, '$.data.retryable', 'true') WHERE id=:id"
            ),
            {"id": claim.attempt_id},
        )
    candidates = list(Retry(engine, owner).candidates())
    assert len(candidates) == 1
    assert candidates[0][1].terminal.data["retryable"] is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("ordinal", 2),
        ("status", "submitted"),
        ("terminal", None),
    ],
)
def test_retry_pure_authority_retains_attempt_checks(engine, field, value):
    from app.queue.retry import Retry

    _, owner, _ = failed_attempts(engine, 1)
    job, attempt = next(Retry(engine, owner).candidates())
    setattr(attempt, field, value)
    assert not Retry.eligible(job, attempt)


def test_retry_durable_lane_rejection_precedes_http_and_does_not_block_cpu(engine):
    from test_dispatcher_admission import add

    failed_attempts(engine, 200)
    add(engine, status="running", lane="gpu", engine_id="foreign")
    cpu_id, _ = add(
        engine,
        task="audio.beats",
        lane="cpu",
        engine_id="other",
        model_id="other",
        request={"params": {}, "mode": "bf16"},
    )
    backend, other = StatefulRetryBackend(), StatefulRetryBackend("other")

    async def run():
        runtime = await paused_runtime(engine, {"alias": backend, "cpu": other})
        try:
            await runtime._retry()
            assert backend.health_calls == other.health_calls == 0
            assert backend.calls == other.calls == 0
            dispatched = await runtime.dispatcher.dispatch()
            assert dispatched is not None and dispatched.job_id == cpu_id
            assert not backend.posts and not backend.unloads
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("budget", 3),
        ("offload", 2),
        ("nonretryable", 1),
        ("no_offload", 1),
        ("fake_offload", 1),
        ("unverified", 1),
        ("noncommercial", 1),
        ("busy", 1),
        ("cancelled", 1),
        ("future", 1),
    ],
)
def test_retry_budget_three_and_offload_once_verified_only(engine, scenario, expected):
    jid, _, _claim = prepared(engine)
    from test_queue_resolver import descriptor

    recipe = descriptor()
    offload_recipe = descriptor()
    offload_recipe["modes"].append(
        {"id": "offload", "vram_mb": 500, "notes": "synthetic verified task mode"}
    )
    backend = RecordedBackend(recipes=[recipe, offload_recipe])
    if scenario == "offload":
        backend.value["modes"].append(
            {"id": "offload", "vram_mb": 500, "notes": "synthetic verified task mode"}
        )
    if scenario == "fake_offload":
        backend.value["modes"].append(
            {"id": "not-offload-mode", "vram_mb": 500, "notes": "synthetic"}
        )
    if scenario == "unverified":
        backend.value["tasks"]["music.instrumental"]["verified"] = False
    if scenario == "noncommercial":
        backend.value["commercial_use"] = False
    if scenario == "busy":
        original = backend.health

        async def busy():
            return (await original()).model_copy(
                update={"state": "busy", "job_id": "01K70000000000000000000003"}
            )

        backend.health = busy
    if scenario == "cancelled":
        with Session(engine) as session, session.begin():
            session.get(Job, jid).cancel_requested_at = "2026-10-08T02:00:00Z"
    if scenario == "future":
        with Session(engine) as session, session.begin():
            session.get(Job, jid).not_before = "2099-10-08T02:00:00Z"

    async def status(aid):
        return JobStatus(job_id=aid, state="error", seq=1)

    async def events(aid, after=0):
        yield event(
            aid,
            "error",
            {
                "code": "VRAM_EXCEEDED"
                if scenario in {"offload", "no_offload", "fake_offload"}
                else "INTERNAL",
                "message": "synthetic",
                "retryable": scenario != "nonretryable",
            },
        )

    backend.status, backend.events = status, events

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.sleep(0.9)
            with Session(engine) as session:
                attempts = list(
                    session.scalars(
                        select(JobAttempt)
                        .where(JobAttempt.job_id == jid)
                        .order_by(JobAttempt.ordinal)
                    )
                )
                assert len(attempts) == expected
                assert len({a.id for a in attempts}) == expected
                assert all(a.engine_request.seed == 17 for a in attempts)
                assert attempts[0].mode == "bf16"
                assert sum(a.mode == "offload" for a in attempts) == (
                    1 if scenario == "offload" else 0
                )
            assert len(backend.posts) == expected - 1
        finally:
            await runtime.close()

    asyncio.run(run())


def test_two_independent_sqlite_writers_reserve_only_one_next_ordinal(engine):
    from concurrent.futures import ThreadPoolExecutor

    from app.queue.events import EventBus, EventConsumer
    from app.queue.retry import Retry
    from test_dispatcher_admission import resolve

    jid, owner, claim = prepared(engine)
    EventConsumer(engine, owner, EventBus()).accept(
        claim.attempt_id,
        "mock",
        event(
            claim.attempt_id,
            "error",
            {"code": "INTERNAL", "message": "synthetic", "retryable": True},
        ),
    )
    retry = Retry(engine, owner)
    job, previous = next(retry.candidates())
    resolved = resolve(retry.frozen_job(job, previous, previous.mode))
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(lambda _: retry.reserve(jid, claim.attempt_id, resolved), range(2))
        )
    assert sum(result is not None for result in results) == 1
    with Session(engine) as session:
        attempts = list(
            session.scalars(select(JobAttempt).where(JobAttempt.job_id == jid))
        )
        assert sorted(a.ordinal for a in attempts) == [1, 2]
        assert session.get(Job, jid).attempt == 2


def test_retry_preserves_frozen_owned_input_despite_changed_domain(engine):
    import hashlib

    from app.models import new_id
    from test_dispatcher_admission import add
    from test_queue_resolver import descriptor

    jid, owner = add(
        engine, status="running", attempt=1, engine_id="mock", model_id="mock"
    )
    aid = new_id()
    path = settings().data_dir / "tmp" / "_server_inputs" / aid / "0"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"actual frozen synthetic input")
    wire = {
        "role": "reference",
        "path": path.relative_to(settings().data_dir).as_posix(),
        "media_type": "audio/wav",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    body = {
        "job_id": aid,
        "task": "music.instrumental",
        "model_id": "mock",
        "mode": "bf16",
        "params": {"style": "literal", "duration_s": 30},
        "seed": 17,
        "n_outputs": 1,
        "timeout_s": 60,
        "output_dir": "tmp/" + aid,
        "inputs": [wire],
    }
    with Session(engine) as session, session.begin():
        session.add(
            JobAttempt(
                id=aid,
                owner_id=owner,
                job_id=jid,
                ordinal=1,
                engine_id="mock",
                model_id="mock",
                mode="bf16",
                engine_request=body,
                load_options={"model_id": "mock", "mode": "bf16"},
            )
        )
        session.get(Job, jid).request = {
            "params": {},
            "inputs": [{"broken_original": True}],
        }
    recipe = descriptor()
    recipe["tasks"]["music.instrumental"]["inputs"] = [
        {"role": "reference", "media_types": ["audio/wav"], "required": True}
    ]
    backend = RecordedBackend(recipes=[recipe])
    backend.value = descriptor()
    backend.value["tasks"]["music.instrumental"]["inputs"] = [
        {"role": "reference", "media_types": ["audio/wav"], "required": True}
    ]
    backend.record = JobStatus(job_id=aid, state="error", seq=1)
    backend.events_value = [
        event(
            aid,
            "error",
            {"code": "INTERNAL", "message": "synthetic", "retryable": True},
        )
    ]

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        await runtime.start()
        try:
            await asyncio.sleep(0.6)
            assert len(backend.posts) == 1, (
                "Retry reread domain references instead of frozen inputs"
            )
            assert backend.posts[0].inputs[0].model_dump(mode="json") == wire
            assert path.read_bytes() == b"actual frozen synthetic input"
        finally:
            await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "retry_priority,queued_priority,retry_stamp,queued_stamp,winner",
    [
        (
            "batch",
            "interactive",
            "2026-10-08T02:00:00.000001Z",
            "2026-10-08T02:00:00.000002Z",
            "queued",
        ),
        (
            "interactive",
            "batch",
            "2026-10-08T02:00:00.000002Z",
            "2026-10-08T02:00:00.000001Z",
            "retry",
        ),
        (
            "normal",
            "normal",
            "2026-10-08T02:00:00.000002Z",
            "2026-10-08T02:00:00.000001Z",
            "queued",
        ),
        (
            "normal",
            "normal",
            "2026-10-08T02:00:00.000001Z",
            "2026-10-08T02:00:00.000002Z",
            "retry",
        ),
    ],
)
def test_public_runtime_global_priority_fifo_native(
    engine, retry_priority, queued_priority, retry_stamp, queued_stamp, winner
):
    import threading

    from sqlalchemy import event as sql_event
    from sqlalchemy import text
    from test_dispatcher_admission import add

    retry_id, _, _previous = failed_attempts(engine, 1)
    queued_id, _ = add(engine, engine_id="mock", model_id="mock")
    with Session(engine) as session, session.begin():
        retry = session.get(Job, retry_id)
        retry.priority, retry.created_at = retry_priority, retry_stamp
        queued = session.get(Job, queued_id)
        queued.priority, queued.created_at = queued_priority, queued_stamp
    backend = StatefulRetryBackend()
    queries = []
    sent = None
    release = None
    original_submit = backend.submit

    def query(connection, cursor, statement, params, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(
                {
                    "sql": statement,
                    "params": repr(params),
                    "thread": threading.get_ident(),
                }
            )

    async def run():
        nonlocal sent, release
        sent, release = asyncio.Event(), asyncio.Event()

        async def submit(request):
            ack = await original_submit(request)
            sent.set()
            return ack

        async def events(aid, after=0):
            await release.wait()
            async for value in StatefulRetryBackend.events(backend, aid, after):
                yield value

        backend.submit, backend.events = submit, events
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        sql_event.listen(engine, "before_cursor_execute", query)
        await runtime.start()
        try:
            await asyncio.wait_for(sent.wait(), 5)
            with Session(engine) as session:
                head = session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                states = {
                    jid: {
                        "attempt": session.get(Job, jid).attempt,
                        "status": session.get(Job, jid).status,
                    }
                    for jid in (retry_id, queued_id)
                }
                logical = session.get(JobAttempt, backend.posts[0].job_id).job_id
            print(
                {
                    "native_file": engine.url.database,
                    "head": head,
                    "main_thread": threading.get_ident(),
                    "queries": queries,
                    "first_submission": backend.posts[0].job_id,
                    "logical_id": logical,
                    "retry": retry_id,
                    "queued": queued_id,
                    "states": states,
                    "synthetic_engine": True,
                }
            )
            assert head == "0007"
            assert logical == (queued_id if winner == "queued" else retry_id)
            assert states[retry_id]["attempt"] == (1 if winner == "queued" else 2)
            assert states[queued_id]["attempt"] == (1 if winner == "queued" else 0)
            assert (
                backend.loaded is not None
                and backend.running == backend.posts[0].job_id
            )
        finally:
            release.set()
            await runtime.close()
            sql_event.remove(engine, "before_cursor_execute", query)
        assert not runtime.native and engine.pool.checkedout() == 0

    asyncio.run(run())


@pytest.mark.parametrize("stream", ["retry", "global"])
@pytest.mark.parametrize(
    "scenario", ["single", "multiple", "shutdown", "closefault", "readfault"]
)
def test_native_sqlite_inflight_reader_cancellation_retains_cause_and_closes(
    engine, stream, scenario
):
    import ctypes
    import sys
    import threading

    from sqlalchemy import event as sql_event

    if sys.platform != "win32":
        pytest.skip("Control propio WinEvent; consulta SQLite real")
    failed_attempts(engine, 1)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateEventW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_wchar_p,
    ]
    kernel.CreateEventW.restype = ctypes.c_void_p
    kernel.SetEvent.argtypes = [ctypes.c_void_p]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    entered, release = (
        kernel.CreateEventW(None, 1, 0, None),
        kernel.CreateEventW(None, 1, 0, None),
    )
    assert entered and release
    udf_returned, cursor_closed, originals, trace = [], [], [], []
    armed = [True]

    def hold():
        trace.append({"thread": threading.get_ident(), "phase": "SQLite UDF entered"})
        kernel.SetEvent(entered)
        assert kernel.WaitForSingleObject(release, 0xFFFFFFFF) == 0
        udf_returned.append(True)
        if scenario == "readfault":
            raise OSError("owned SQLite UDF failure after release")
        return 1

    def query(connection, cursor, statement, params, context, many):
        if (
            armed[0]
            and "JOIN job_attempt" in statement
            and statement.lstrip().startswith("SELECT")
        ):
            armed[0] = False
            cursor.connection.create_function("u2_owned_hold", 0, hold)
            trace.append(
                {
                    "sql": statement,
                    "params": repr(params),
                    "thread": threading.get_ident(),
                    "pool_checkedout": engine.pool.checkedout(),
                }
            )
            return statement.replace(
                "WHERE ", "WHERE u2_owned_hold() = 1 AND ", 1
            ), params
        return statement, params

    async def run():
        runtime = await paused_runtime(engine, {"mock": StatefulRetryBackend()})
        original_dbcall = runtime.dbcall
        original_pages = (
            runtime.retry.candidate_batches
            if stream == "retry"
            else runtime._candidate_batches
        )

        def pages():
            iterator = original_pages()
            try:
                yield from iterator
            finally:
                iterator.close()
                cursor_closed.append(True)
                if scenario == "closefault":
                    raise ValueError("owned secondary close fault")

        if stream == "retry":
            runtime.retry.candidate_batches = pages
        else:
            runtime._candidate_batches = pages

        async def capture(function, *args):
            try:
                return await original_dbcall(function, *args)
            except asyncio.CancelledError as cause:
                originals.append(cause)
                raise

        runtime.dbcall = capture
        sql_event.listen(engine, "before_cursor_execute", query, retval=True)
        task = asyncio.create_task(
            runtime._retry() if stream == "retry" else runtime._arbitrate()
        )
        runtime.task = task
        shutdown = None
        ticks = []
        try:
            while kernel.WaitForSingleObject(entered, 0) != 0:
                assert not task.done()
                await asyncio.sleep(0)
            assert engine.pool.checkedout() >= 1
            task.cancel("owned reader cancellation")
            for _ in range(40):
                ticks.append(True)
                await asyncio.sleep(0)
            if scenario in {"multiple", "shutdown"}:
                task.cancel("second owned cancellation")
                await asyncio.sleep(0)
            if scenario == "shutdown":
                shutdown = asyncio.create_task(runtime.close())
                for _ in range(40):
                    await asyncio.sleep(0)
                assert not shutdown.done()
                shutdown.cancel("shutdown cancelled while native pending")
                await asyncio.sleep(0)
                shutdown.cancel("second shutdown cancellation")
                await asyncio.sleep(0)
                assert not shutdown.done() and engine.pool.checkedout() >= 1
            before_release = {
                "task_done": task.done(),
                "native_pending": len(runtime.native),
                "pool_checkedout": engine.pool.checkedout(),
            }
            kernel.SetEvent(release)
            result = (await asyncio.gather(task, return_exceptions=True))[0]
            # gather may manufacture a cancellation result; task.result preserves the cause.
            try:
                task.result()
            except (asyncio.CancelledError, ValueError) as cause:
                actual = cause
            print(
                {
                    "native_file": engine.url.database,
                    "trace": trace,
                    "before_release": before_release,
                    "result": repr(result),
                    "actual": repr(actual),
                    "udf_returned": udf_returned,
                    "reader_finally": cursor_closed,
                    "OS_control": "own WinEvent inside native SQLite UDF; not generic disk hang",
                }
            )
            assert isinstance(actual, asyncio.CancelledError)
            assert actual is originals[0]
            assert (
                before_release["task_done"] is False
                and before_release["native_pending"] >= 1
            )
            assert udf_returned == [True] and cursor_closed == [True] and ticks
            if shutdown is not None:
                outcome = (await asyncio.gather(shutdown, return_exceptions=True))[0]
                assert isinstance(outcome, asyncio.CancelledError)
        finally:
            kernel.SetEvent(release)
            await asyncio.gather(task, return_exceptions=True)
            if shutdown is not None:
                await asyncio.gather(shutdown, return_exceptions=True)
            await runtime.close()
            sql_event.remove(engine, "before_cursor_execute", query)
        assert not runtime.native and engine.pool.checkedout() == 0

    try:
        asyncio.run(run())
    finally:
        kernel.SetEvent(release)
        kernel.CloseHandle(entered)
        kernel.CloseHandle(release)


@pytest.mark.parametrize("size", [200, 400, 801])
@pytest.mark.parametrize(
    "denial", ["invalid", "route", "future", "dependency", "cancelled", "deleted"]
)
def test_global_valid_retry_survives_queued_ineligible_tail_native(
    engine, size, denial
):
    from app.models import JobDependency, new_id

    retry_id, owner, _ = failed_attempts(engine, 1)
    with Session(engine) as session, session.begin():
        retry = session.get(Job, retry_id)
        retry.priority = "batch"
        song_id = retry.song_id
        parent = Job(
            owner_id=owner,
            song_id=song_id,
            task="audio.beats",
            lane="cpu",
            request={},
            status="queued",
            priority="nightly",
            not_before="2099-10-08T00:00:00Z",
        )
        session.add(parent)
        session.flush()
        for _ in range(size):
            job = Job(
                id=new_id(),
                owner_id=owner,
                song_id=song_id,
                task="music.instrumental",
                lane="gpu",
                engine_id="mock",
                model_id="mock",
                request={
                    "params": {"style": "literal", "duration_s": 30},
                    "mode": "bf16",
                },
                priority="interactive",
            )
            if denial == "invalid":
                job.request = {"params": {"impossible": True}, "mode": "bf16"}
            elif denial == "route":
                job.engine_id = "absent"
            elif denial == "future":
                job.not_before = "2099-10-08T00:00:00Z"
            elif denial == "cancelled":
                job.cancel_requested_at = "2026-10-08T02:00:00Z"
            elif denial == "deleted":
                job.deleted_at = "2026-10-08T02:00:00Z"
            session.add(job)
            if denial == "dependency":
                session.add(
                    JobDependency(
                        owner_id=owner, job_id=job.id, depends_on_job_id=parent.id
                    )
                )
    backend = StatefulRetryBackend()

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend},
            synthetic_registry=backend.synthetic_registry,
        )
        sent = asyncio.Event()
        submit = backend.submit

        async def submitted(request):
            result = await submit(request)
            runtime.stop.set()
            sent.set()
            return result

        backend.submit = submitted
        await runtime.start()
        try:
            await asyncio.wait_for(sent.wait(), 10)
            await runtime.task
            with Session(engine) as session:
                assert (
                    session.get(JobAttempt, backend.posts[0].job_id).job_id == retry_id
                )
                assert session.get(Job, retry_id).attempt == 2
                assert (
                    session.scalar(
                        select(JobAttempt.ordinal).where(
                            JobAttempt.id == backend.posts[0].job_id
                        )
                    )
                    == 2
                )
            assert len(backend.posts) == 1
            print(
                {
                    "global_queued_tail": size,
                    "denial": denial,
                    "health": backend.health_calls,
                    "models": backend.calls,
                    "native_file": engine.url.database,
                    "synthetic_engine": True,
                }
            )
        finally:
            await runtime.close()
        assert not runtime.native and engine.pool.checkedout() == 0

    asyncio.run(run())


@pytest.mark.parametrize("size", [200, 400, 801])
def test_global_busy_gpu_negative_once_and_available_cpu_native(engine, size):
    from test_dispatcher_admission import add

    retry_id, owner, _ = failed_attempts(engine, size)
    with Session(engine) as session, session.begin():
        session.get(Job, retry_id).priority = "interactive"
        song = session.get(Job, retry_id).song_id
        for _ in range(size):
            session.add(
                Job(
                    owner_id=owner,
                    song_id=song,
                    task="music.instrumental",
                    lane="gpu",
                    engine_id="mock",
                    model_id="mock",
                    priority="interactive",
                    request={
                        "params": {"style": "literal", "duration_s": 30},
                        "mode": "bf16",
                    },
                )
            )
    cpu_id, _ = add(
        engine,
        task="audio.beats",
        lane="cpu",
        priority="batch",
        engine_id="other",
        model_id="other",
        request={"params": {}, "mode": "bf16"},
    )
    busy, cpu = StatefulRetryBackend(), StatefulRetryBackend("other")
    busy.force_busy = True

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": busy, "cpu": cpu},
            synthetic_registry=composition({"mock": busy, "cpu": cpu}),
        )
        sent = asyncio.Event()
        submit = cpu.submit
        ticks = []

        async def heartbeat():
            while not runtime.stop.is_set():
                ticks.append(True)
                await asyncio.sleep(0)

        async def submitted(request):
            ack = await submit(request)
            runtime.stop.set()
            sent.set()
            return ack

        cpu.submit = submitted
        beat = asyncio.create_task(heartbeat())
        await runtime.start()
        positive = []
        original_resolve = runtime.resolver.resolve

        async def resolve(*args, **kwargs):
            before = (busy.health_calls, busy.calls)
            result = await original_resolve(*args, **kwargs)
            positive.append(
                (before, (busy.health_calls - before[0], busy.calls - before[1]))
            )
            return result

        runtime.resolver.resolve = resolve
        try:
            await asyncio.wait_for(sent.wait(), 10)
            await runtime.task
            with Session(engine) as session:
                assert session.get(JobAttempt, cpu.posts[0].job_id).job_id == cpu_id
                assert session.get(Job, retry_id).attempt == 1
                assert (
                    session.scalar(select(JobAttempt.id).where(JobAttempt.ordinal == 2))
                    is None
                )
            print(
                {
                    "global_busy_rows_each_population": size,
                    "busy_health": busy.health_calls,
                    "busy_models": busy.calls,
                    "cpu_health_fresh_positive": cpu.health_calls,
                    "cpu_models": cpu.calls,
                    "heartbeat": len(ticks),
                    "native_file": engine.url.database,
                    "synthetic_engine": True,
                }
            )
            assert positive == [((1, 1), (1, 1))]
            assert busy.health_calls == busy.calls == 2
            assert not busy.posts and not busy.unloads and ticks
            assert len(cpu.posts) == 1
        finally:
            await runtime.close()
            await beat
        assert not runtime.native and engine.pool.checkedout() == 0

    asyncio.run(run())


def test_shared_arbitration_snapshot_excludes_backdated_insert_native(engine):
    from test_dispatcher_admission import add

    retry_id, _, _ = failed_attempts(engine, 801)
    queued_id, _ = add(engine, engine_id="mock", model_id="mock", priority="batch")

    async def run():
        runtime = await paused_runtime(engine, {"mock": StatefulRetryBackend()})
        pages = runtime._candidate_batches()
        try:
            first = await runtime.dbcall(next, pages)
            late, _ = add(
                engine, priority="interactive", created_at="2026-10-08T00:00:00.000001Z"
            )
            rows = list(first)
            while (page := await runtime.dbcall(next, pages, None)) is not None:
                assert len(page) <= 400
                rows.extend(page)
            ids = [job.id for job, previous in rows]
            assert retry_id in ids and queued_id in ids and late not in ids
            assert len(ids) == len(set(ids)) == 802
            await runtime.dbcall(pages.close)
            next_pages = runtime._candidate_batches()
            try:
                assert late in [
                    job.id for job, _ in await runtime.dbcall(next, next_pages)
                ]
            finally:
                await runtime.dbcall(next_pages.close)
        finally:
            await runtime.dbcall(pages.close)
            await runtime.close()
        assert engine.pool.checkedout() == 0

    asyncio.run(run())


def test_native_reader_close_waits_actual_session_return_under_repeated_cancellation(
    engine,
):
    import threading

    from sqlalchemy import event as sql_event

    failed_attempts(engine, 1)
    entered, release = threading.Event(), threading.Event()
    closing, returned, originals = [], [], []

    def checkin(connection, record):
        if closing:
            entered.set()
            assert release.wait()
            returned.append(True)

    async def run():
        runtime = await paused_runtime(engine, {"mock": StatefulRetryBackend()})
        pages = runtime.retry.candidate_batches()
        assert await runtime.dbcall(next, pages)
        assert engine.pool.checkedout() == 1
        sql_event.listen(engine.pool, "checkin", checkin)
        closing.append(True)
        native = runtime.dbcall

        async def capture(function, *args):
            try:
                return await native(function, *args)
            except asyncio.CancelledError as cause:
                originals.append(cause)
                raise

        runtime.dbcall = capture
        task = asyncio.create_task(runtime._close_reader(pages, None))
        runtime.task = task
        shutdown = None
        try:
            while not entered.is_set():
                assert not task.done()
                await asyncio.sleep(0)
            task.cancel("close cancellation")
            for _ in range(40):
                await asyncio.sleep(0)
            task.cancel("second close cancellation")
            shutdown = asyncio.create_task(runtime.close())
            for _ in range(40):
                await asyncio.sleep(0)
            assert not task.done() and not shutdown.done()
            assert engine.pool.checkedout() == 1 and len(runtime.native) == 1
            release.set()
            await asyncio.gather(task, return_exceptions=True)
            with pytest.raises(asyncio.CancelledError) as caught:
                task.result()
            assert caught.value is originals[0]
            await shutdown
            assert (
                returned == [True]
                and not runtime.native
                and engine.pool.checkedout() == 0
            )
            print(
                {
                    "native_file": engine.url.database,
                    "actual_session_close_checkin_hook": True,
                    "reader_returned": returned,
                    "pool_checkedout": engine.pool.checkedout(),
                    "scope": "threading OS barrier at native pool checkin; no generic kernel I/O preemption claim",
                }
            )
        finally:
            release.set()
            await asyncio.gather(task, return_exceptions=True)
            if shutdown is not None:
                await asyncio.gather(shutdown, return_exceptions=True)
            sql_event.remove(engine.pool, "checkin", checkin)
            await runtime.close()

    asyncio.run(run())


def test_native_standalone_reader_close_fault_keeps_actual_cause(engine):
    failed_attempts(engine, 1)
    fault = ValueError("owned standalone close fault")
    finalizers = []

    async def run():
        runtime = await paused_runtime(engine, {"mock": StatefulRetryBackend()})
        iterator = runtime.retry.candidate_batches()
        assert await runtime.dbcall(next, iterator)
        assert engine.pool.checkedout() == 1

        class Reader:
            def close(self):
                iterator.close()
                finalizers.append(True)
                raise fault

        try:
            with pytest.raises(ValueError) as caught:
                await runtime._close_reader(Reader(), None)
            assert caught.value is fault
            assert finalizers == [True] and engine.pool.checkedout() == 0
        finally:
            await runtime.close()
        assert not runtime.native

    asyncio.run(run())


@pytest.mark.parametrize("occupied", ["gpu", "cpu"])
def test_global_lane_capacity_cpu_two_gpu_one_without_cpu_unload_native(
    engine, occupied
):
    from engine_contract import LoadedModel
    from test_dispatcher_admission import add

    retry_id, _owner, _ = failed_attempts(engine, 1)
    backend = StatefulRetryBackend()
    cpu_a, cpu_b = StatefulRetryBackend("cpu-a"), StatefulRetryBackend("cpu-b")
    for cpu in (cpu_a, cpu_b):
        for task in cpu.value["tasks"].values():
            task["device"] = "cpu"
    cpu_ids = []
    if occupied == "gpu":
        add(engine, status="running", lane="gpu", engine_id="occupied")
        for cpu in (cpu_a, cpu_b):
            jid, _ = add(
                engine,
                task="audio.beats",
                lane="cpu",
                engine_id=cpu.identity,
                model_id=cpu.identity,
                request={"params": {}, "mode": "bf16"},
                priority="batch",
            )
            cpu_ids.append(jid)
    else:
        add(engine, status="running", lane="cpu", engine_id="cpu-a", task="audio.beats")
        cpu_a.loaded = LoadedModel(model_id="cpu-a", mode="bf16")
        cpu_a.running = "01K70000000000000000000003"
        cpu_a.force_busy = True

    async def run():
        runtime = QueueRuntime(
            engine,
            settings(),
            backends={"mock": backend, "cpu-a": cpu_a, "cpu-b": cpu_b},
            synthetic_registry=composition(
                {"mock": backend, "cpu-a": cpu_a, "cpu-b": cpu_b}
            ),
        )
        sent = asyncio.Event()
        target = cpu_b if occupied == "gpu" else backend
        submit = target.submit

        async def submitted(request):
            ack = await submit(request)
            runtime.stop.set()
            sent.set()
            return ack

        target.submit = submitted
        await runtime.start()
        try:
            await asyncio.wait_for(sent.wait(), 5)
            await runtime.task
            with Session(engine) as session:
                if occupied == "gpu":
                    assert session.get(Job, retry_id).attempt == 1
                    assert [
                        session.get(JobAttempt, cpu.posts[0].job_id).job_id
                        for cpu in (cpu_a, cpu_b)
                    ] == cpu_ids
                    assert not backend.posts and backend.loaded is None
                else:
                    assert (
                        session.get(JobAttempt, backend.posts[0].job_id).job_id
                        == retry_id
                    )
                    assert session.get(Job, retry_id).attempt == 2
                    assert cpu_a.loaded.model_id == "cpu-a"
            assert backend.unloads == cpu_a.unloads == cpu_b.unloads == 0
        finally:
            await runtime.close()
        assert not runtime.native and engine.pool.checkedout() == 0

    asyncio.run(run())


@pytest.mark.parametrize("exhaust", [True, False])
def test_shared_reader_interleaved_three_pages_native(engine, monkeypatch, exhaust):
    """Runtime real, SQLite0005/WAL y backend sintÃ©tico; sin health/load."""
    import json
    import os
    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    from app.queue.admission import Admission
    from sqlalchemy import event as sql_event
    from sqlalchemy import text

    retry_id, owner, _ = failed_attempts(engine, 801)
    expected = []
    base = datetime(2026, 10, 8, tzinfo=timezone.utc)
    with Session(engine) as session, session.begin():
        song = session.get(Job, retry_id).song_id
        retries = list(session.scalars(select(Job).order_by(Job.id)))
        for index, retry in enumerate(retries):
            priority = ("interactive", "normal", "batch")[index % 3]
            stamp = (
                (base + timedelta(microseconds=index // 2))
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            )
            retry.priority, retry.created_at = priority, stamp
            queued = Job(
                owner_id=owner,
                song_id=song,
                task="music.instrumental",
                lane="gpu",
                priority=priority,
                created_at=stamp,
                request={},
            )
            session.add(queued)
        session.flush()
        expected = [
            (job.id, job.status)
            for job in sorted(session.scalars(select(Job)), key=Admission._order)
        ]
    assert len(expected) == 1602
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == "0007"
        )
        assert connection.scalar(text("PRAGMA journal_mode")).lower() == "wal"
    streams, readers, maps, peaks, queries, returned = [], [], [], [], [], []
    counts = {"queued": [], "retry": []}

    def materialized(session, instance):
        peaks.append(len(session.identity_map))

    def query(connection, cursor, statement, params, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    def checkin(connection, record):
        returned.append(True)

    async def run():
        runtime = await paused_runtime(engine, {"mock": StatefulRetryBackend()})
        backend = runtime.backends["mock"]
        for kind, component in (
            ("queued", runtime.admission),
            ("retry", runtime.retry),
        ):
            original = component.candidate_batches

            def tracked(*args, _original=original, _kind=kind, **kwargs):
                reader = kwargs["reader"]
                readers.append(reader)
                maps.append(reader.identity_map)
                identity_map = reader.identity_map
                iterator = _original(*args, **kwargs)
                streams.append(iterator)
                try:
                    for page in iterator:
                        counts[_kind].append(len(page))
                        assert reader.identity_map is identity_map
                        yield page
                finally:
                    iterator.close()

            monkeypatch.setattr(component, "candidate_batches", tracked)
        pages = runtime._candidate_batches()
        late = None
        seen = []
        failure = None
        sql_event.listen(Session, "loaded_as_persistent", materialized)
        sql_event.listen(engine, "before_cursor_execute", query)
        sql_event.listen(engine.pool, "checkin", checkin)
        try:
            first = await runtime.dbcall(next, pages)
            seen.extend((job.id, job.status) for job, previous in first)
            assert readers[0] is readers[1]
            assert len(first) == 400 and engine.pool.checkedout() == 1
            # Commit concurrent, backdated and highest priority, outside this WAL snapshot.
            with Session(engine) as writer_session, writer_session.begin():
                late_job = Job(
                    owner_id=owner,
                    song_id=song,
                    task="music.instrumental",
                    lane="gpu",
                    priority="interactive",
                    created_at="2020-01-01T00:00:00Z",
                    request={},
                )
                writer_session.add(late_job)
                writer_session.flush()
                late = late_job.id
            if exhaust:
                while (page := await runtime.dbcall(next, pages, None)) is not None:
                    assert 1 <= len(page) <= 400
                    seen.extend((job.id, job.status) for job, previous in page)
                assert seen == expected
                assert len({jid for jid, status in seen}) == 1602
                assert counts == {"queued": [400, 400, 1], "retry": [400, 400, 1]}
                assert maps[0] is maps[1]
            else:
                assert seen == expected[:400]
        except BaseException as cause:
            failure = {"type": type(cause).__name__, "message": str(cause)}
            raise
        finally:
            try:
                await runtime._close_reader(pages, None)
            finally:
                await runtime.close()
                sql_event.remove(Session, "loaded_as_persistent", materialized)
                sql_event.remove(engine, "before_cursor_execute", query)
                sql_event.remove(engine.pool, "checkin", checkin)
                proof = {
                    "native_file": engine.url.database,
                    "migration": "0005",
                    "journal": "wal",
                    "synthetic_backend": "StatefulRetryBackend",
                    "same_session": len(readers) == 2 and readers[0] is readers[1],
                    "pages": counts,
                    "mixed_stream_peak_identity_map": max(peaks, default=0),
                    "candidate_retry_selects": sum(
                        "JOIN job_attempt" in q for q in queries
                    ),
                    "queued_snapshot_selects": sum(
                        "julianday" not in q and "LIMIT" in q for q in queries
                    ),
                    "native_selects": len(queries),
                    "pool_returns": len(returned),
                    "checkedout": engine.pool.checkedout(),
                    "native_pending": len(runtime.native),
                    "streams_closed": [s.gi_frame is None for s in streams],
                    "rows": len(seen),
                    "exhaust": exhaust,
                    "failure": failure,
                    "backend_health_calls": backend.health_calls,
                    "backend_posts": len(backend.posts),
                }
                (
                    Path(os.environ["STUDIO_QUEUE_TEST_ROOT"])
                    / f"shared-reader-{exhaust}.json"
                ).write_text(json.dumps(proof, indent=2), encoding="utf-8")
                print(proof)
        assert not runtime.native and engine.pool.checkedout() == 0
        assert all(stream.gi_frame is None for stream in streams)
        assert (
            backend.health_calls == 0 and not backend.posts and backend.loaded is None
        )
        next_pages = runtime._candidate_batches()
        # Runtime executor is closed; synchronous next poll only reads the same real components.
        try:
            assert next(next_pages)[0][0].id == late
        finally:
            next_pages.close()
        assert engine.pool.checkedout() == 0

    asyncio.run(run())
