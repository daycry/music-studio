"""Admisión real SQLite head0005 y primera entrega HTTP sin GPU."""

import asyncio
import importlib.util
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from app.db import create_db_engine, migrate
from app.models import Job, JobAttempt, JobDependency, Song, User, new_id
from app.settings import ContractSettings
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from synthetic_composition import composition
from test_queue_resolver import Catalog, descriptor

DEFAULT_CATALOG = Catalog()


@pytest.mark.parametrize("size", [200, 400, 800])
@pytest.mark.parametrize("mixed", [False, True])
def test_dispatcher_dependency_query_batches_native(engine, size, mixed):
    import math

    from sqlalchemy import event

    first, owner = add(engine, priority="interactive")
    with Session(engine) as session:
        root = session.get(Job, first).song_id
        parent = Job(
            owner_id=owner,
            song_id=root,
            task="audio.beats",
            lane="cpu",
            request={},
            status="succeeded",
        )
        session.add(parent)
        session.flush()
        for index in range(size - 1):
            row = Job(
                owner_id=owner,
                song_id=root,
                task="music.instrumental",
                lane="gpu",
                request={},
                priority="batch",
            )
            session.add(row)
            session.flush()
            if mixed and index % 2:
                session.add(
                    JobDependency(
                        owner_id=owner, job_id=row.id, depends_on_job_id=parent.id
                    )
                )
        session.commit()
    queries = []

    def observe(connection, cursor, statement, params, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", observe)
    try:
        picked = admission(engine, owner).select()
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    assert picked.id == first
    assert len(queries) <= 3 + math.ceil(size / 400), len(queries)


NOW = datetime(2026, 10, 8, 2, tzinfo=timezone.utc)


def test_dispatcher_selection_semantic_baseline(engine):
    _normal, owner = add(engine)
    interactive, _ = add(engine, priority="interactive")
    add(engine, priority="interactive", not_before="2026-10-09T00:00:00Z")
    candidate = admission(engine, owner).select()
    assert (candidate.id if candidate else None) == interactive


@pytest.mark.parametrize(
    "scenario", ["busy_cpu", "gpu_head", "unknown_busy", "mixed_busy"]
)
def test_dispatcher_available_lanes_native_http(engine, scenario):
    import json
    from contextlib import AsyncExitStack

    from app.queue.backends.http import HttpEngineBackend
    from app.queue.dispatcher import Dispatcher
    from app.queue.resolver import Resolver
    from test_queue_backend import health

    posts = []
    target, owner = add(engine, engine_id="gpu", priority="interactive")
    gpu_queued = target
    if scenario == "gpu_head":
        add(engine, lane="gpu", status="interrupted", engine_id="gpu", support=True)
        target, _ = add(
            engine,
            lane="cpu",
            engine_id="cpu",
            task="audio.beats",
            request={"params": {}, "mode": "cpu", "seed": 1, "timeout_s": 60},
        )
    else:
        add(engine, lane="cpu", status="running", engine_id="cpu")

    def handler(name):
        resident = [None]

        def handle(req):
            if req.url.path == "/v1/health":
                value = health()
                value["engine_id"] = name
                value["loaded"] = resident[0]
                if name == "cpu" and scenario != "gpu_head":
                    value.update(
                        state="busy",
                        job_id="01K70000000000000000000003",
                        loaded={"model_id": "mock", "mode": "cpu"},
                    )
                return httpx.Response(200, json=value)
            if req.url.path == "/v1/models":
                model = descriptor()
                if name == "cpu":
                    if scenario == "unknown_busy":
                        return httpx.Response(200, json=[])
                    if scenario != "mixed_busy":
                        model["tasks"].pop("music.instrumental")
                model["modes"].append({"id": "cpu", "vram_mb": 0, "notes": "synthetic"})
                return httpx.Response(200, json=[model])
            if req.url.path == "/v1/load":
                resident[0] = {"model_id": "mock", "mode": "bf16"}
                return httpx.Response(200, json={"model_id": "mock", "mode": "bf16"})
            if req.url.path == "/v1/jobs":
                body = json.loads(req.content)
                posts.append((name, body))
                return httpx.Response(202, json={"job_id": body["job_id"]})
            raise AssertionError(req.url.path)

        return handle

    async def run():
        settings = ContractSettings(
            engine_token="private-test-only",
            engines={
                "gpu": "http://engine-acestep:8199",
                "cpu": "http://engine-analysis:8199",
            },
        )
        async with AsyncExitStack() as stack:
            backends = {
                name: await stack.enter_async_context(
                    HttpEngineBackend(
                        settings, name, transport=httpx.MockTransport(handler(name))
                    )
                )
                for name in ("gpu", "cpu")
            }
            declarations = {}
            for name in backends:
                recipe = descriptor()
                if name == "cpu" and scenario != "mixed_busy":
                    recipe["tasks"].pop("music.instrumental")
                recipe["modes"].append(
                    {"id": "cpu", "vram_mb": 0, "notes": "synthetic"}
                )
                declarations[name] = ([recipe], name)
            registry = composition(backends, declarations)
            dispatcher = Dispatcher(
                admission(engine, owner, synthetic_registry=registry),
                Resolver(
                    backends,
                    data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
                    synthetic_registry=registry,
                ),
            )
            await dispatcher.dispatch()
            if scenario == "gpu_head":
                assert await dispatcher.dispatch(gpu_queued) is None

    asyncio.run(run())
    expected = (
        []
        if scenario in {"unknown_busy", "mixed_busy"}
        else ["cpu" if scenario == "gpu_head" else "gpu"]
    )
    assert [name for name, body in posts] == expected
    if expected:
        with Session(engine) as session:
            attempt = session.scalar(
                select(JobAttempt).where(JobAttempt.job_id == target)
            )
            assert (
                attempt.status == "submitted"
                and attempt.engine_request.model_dump(mode="json") == posts[0][1]
            )


@pytest.fixture
def engine():
    path = Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / uuid4().hex / "studio.sqlite"
    path.parent.mkdir(parents=True)
    migrate(path)
    engine = create_db_engine(path)
    with engine.connect() as c:
        assert (
            c.execute(text("SELECT version_num FROM alembic_version")).scalar()
            == "0007"
        )
    yield engine
    engine.dispose()


def add(engine, **kwargs):
    with Session(engine) as s:
        owner = s.scalar(select(User.id))
        song = Song(
            id=new_id(),
            owner_id=owner,
            title="Sintética",
            is_dependency_only=kwargs.pop("support", False),
        )
        if song.is_dependency_only:
            s.execute(
                text("INSERT INTO snapshot_import(song_id) VALUES(:id)"),
                {"id": song.id},
            )
        s.add(song)
        s.flush()
        values = {
            "owner_id": owner,
            "song_id": song.id,
            "task": "music.instrumental",
            "lane": "gpu",
            "request": {
                "params": {"style": "literal", "duration_s": 30},
                "seed": 17,
                "mode": "bf16",
                "timeout_s": 60,
            },
            "created_at": "2026-10-08T00:00:00Z",
        }
        values.update(kwargs)
        job = Job(**values)
        s.add(job)
        s.flush()
        if song.is_dependency_only:
            s.execute(
                text("DELETE FROM snapshot_import WHERE song_id=:id"), {"id": song.id}
            )
        s.commit()
        return job.id, owner


def admission(engine, owner, *, synthetic_registry=None):
    assert importlib.util.find_spec("app.queue.admission") is not None, (
        "Falta admisión SQLite transaccional"
    )
    from app.queue.admission import Admission

    return Admission(
        engine,
        owner,
        clock=lambda: NOW,
        synthetic_registry=synthetic_registry or DEFAULT_CATALOG.synthetic_registry,
    )


def resolve(job):
    from app.queue.resolver import Resolver

    return asyncio.run(
        Resolver(
            {"mock": DEFAULT_CATALOG},
            data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
            synthetic_registry=DEFAULT_CATALOG.synthetic_registry,
        ).resolve(job)
    )


def test_dispatcher_admission_priority_dates_support_and_dependencies(engine):
    normal, owner = add(engine)
    interactive, _ = add(engine, priority="interactive")
    future, _ = add(engine, priority="interactive", not_before="2026-10-09T00:00:00Z")
    support, _ = add(
        engine, priority="interactive", support=True, created_at="2026-10-07T00:00:00Z"
    )
    a = admission(engine, owner)
    assert a.select().id == interactive
    first = a.reserve(resolve(a.select()))
    assert first.job_id == interactive
    assert a.reserve(resolve(a.select())) is None
    with Session(engine) as s:
        assert s.get(Job, future).attempt == s.get(Job, support).attempt == 0
        assert s.get(Job, normal).status == "queued"


@pytest.mark.parametrize("lane,limit", [("gpu", 1), ("cpu", 2)])
def test_dispatcher_admission_two_native_connections_capacity(engine, lane, limit):
    ids = []
    for _ in range(4):
        id, owner = add(
            engine,
            lane=lane,
            task="audio.beats" if lane == "cpu" else "music.instrumental",
            request={"params": {}, "seed": 17, "mode": "bf16", "timeout_s": 60},
        )
        ids.append(id)
    a = admission(engine, owner)
    candidates = []
    with Session(engine) as s:
        for id in ids:
            candidates.append(resolve(s.get(Job, id)))
    barrier = threading.Barrier(2)

    def claim(index):
        barrier.wait()
        return a.reserve(candidates[index])

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(claim, range(2)))
    assert sum(r is not None for r in results) == limit
    assert a.reserve(candidates[2]) is None
    with Session(engine) as s:
        assert len(list(s.scalars(select(JobAttempt)))) == limit
        assert sum(s.get(Job, id).attempt for id in ids) == limit


@pytest.mark.parametrize("ack", ["valid", "unknown", "timeout", "cancel"])
def test_dispatcher_first_http_post_durable_and_writer_released(engine, ack):
    id, owner = add(engine)
    posts = []

    resident = [None]

    def handler(req):
        # Otra conexión realmente puede adquirir writer durante load y POST.
        if req.method == "POST":
            with engine.begin() as c:
                c.execute(
                    text("UPDATE snapshot_clock SET revision=revision WHERE id=1")
                )
        if req.url.path == "/v1/health":
            from test_queue_backend import health

            return httpx.Response(200, json=dict(health(), loaded=resident[0]))
        if req.url.path == "/v1/models":
            return httpx.Response(200, json=[descriptor()])
        if req.url.path == "/v1/load":
            resident[0] = {"model_id": "mock", "mode": "bf16"}
            return httpx.Response(200, json={"model_id": "mock", "mode": "bf16"})
        if req.url.path == "/v1/jobs":
            import json

            payload = json.loads(req.content)
            posts.append(payload)
            with Session(engine) as s:
                row = s.get(JobAttempt, payload["job_id"])
                assert (
                    row.status == "prepared"
                    and row.engine_request.model_dump(mode="json") == payload
                )
                assert s.get(Job, id).attempt == 1
                if ack == "cancel":
                    s.get(Job, id).cancel_requested_at = "2026-10-08T02:00:00Z"
                    s.commit()
            if ack == "timeout":
                raise httpx.ReadTimeout("synthetic", request=req)
            return httpx.Response(
                202,
                json={"job_id": new_id() if ack == "unknown" else payload["job_id"]},
            )
        raise AssertionError(req.url.path)

    async def run():
        assert importlib.util.find_spec("app.queue") is not None, (
            "Falta dispatcher funcional"
        )
        from app.queue.backends.http import HttpEngineBackend
        from app.queue.dispatcher import Dispatcher
        from app.queue.resolver import Resolver

        settings = ContractSettings(
            engine_token="private-test-only",
            engines={"mock": "http://engine-mock:8199"},
        )
        async with HttpEngineBackend(
            settings, "mock", transport=httpx.MockTransport(handler)
        ) as backend:
            registry = composition(
                {"mock": backend}, {"mock": ([descriptor()], "mock")}
            )
            dispatcher = Dispatcher(
                admission(engine, owner, synthetic_registry=registry),
                Resolver(
                    {"mock": backend},
                    data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
                    synthetic_registry=registry,
                ),
            )
            result = await dispatcher.dispatch()
            assert result is not None
            assert await dispatcher.dispatch() is None

    asyncio.run(run())
    assert len(posts) == 1
    with Session(engine) as s:
        row = s.get(JobAttempt, posts[0]["job_id"])
        assert row.status == ("submitted" if ack == "valid" else "prepared")
        assert row.last_seq == 0 and row.terminal is None
        assert s.get(Job, id).status == "running" and s.get(Job, id).attempt == 1
        assert posts[0]["job_id"] != id


@pytest.mark.parametrize("state", ["queued", "failed", "cancelled", "succeeded"])
def test_dispatcher_dependencies_durable_without_attempt(engine, state):
    parent, owner = add(engine, status=state)
    with Session(engine) as s:
        parent_song = s.get(Job, parent).song_id
    child, _ = add(engine, status="blocked", song_id=parent_song)
    with Session(engine) as s:
        s.add(JobDependency(owner_id=owner, job_id=child, depends_on_job_id=parent))
        s.commit()
    a = admission(engine, owner)
    picked = a.select()
    with Session(engine) as s:
        row = s.get(Job, child)
        assert row.status == (
            "failed" if state in {"failed", "cancelled"} else "blocked"
        )
        assert row.error_code == (
            "DEPENDENCY_FAILED" if state in {"failed", "cancelled"} else None
        )
        assert row.attempt == 0
    assert not picked or picked.id != child  # U3 owns readiness/unblocking.


def test_dispatcher_uncertain_support_running_counts_global(engine):
    _active, owner = add(
        engine,
        status="interrupted",
        support=True,
        cancel_requested_at="2026-10-08T02:00:00Z",
    )
    candidate, _ = add(engine)
    a = admission(engine, owner)
    assert a.reserve(resolve(a.select())) is None
    with Session(engine) as s:
        assert s.get(Job, candidate).attempt == 0


@pytest.mark.parametrize(
    "lane,old_loaded,unloaded",
    [("cpu", True, False), ("gpu", True, False), ("gpu", False, False)],
)
def test_dispatcher_never_unloads_unknown_model_or_cpu(
    engine, lane, old_loaded, unloaded
):
    _id, owner = add(
        engine,
        lane=lane,
        task="audio.beats" if lane == "cpu" else "music.instrumental",
        request={"params": {}, "mode": "bf16", "seed": 1, "timeout_s": 60},
    )
    calls = []

    resident = [None]

    def handler(req):
        calls.append(req.url.path)
        if req.url.path == "/v1/health":
            from test_queue_backend import health

            value = dict(health(), loaded=resident[0])
            if old_loaded:
                value["loaded"] = {"model_id": "foreign", "mode": "bf16"}
            return httpx.Response(200, json=value)
        if req.url.path == "/v1/models":
            return httpx.Response(200, json=[descriptor()])
        if req.url.path == "/v1/load":
            resident[0] = {"model_id": "mock", "mode": "bf16"}
            return httpx.Response(200, json={"model_id": "mock", "mode": "bf16"})
        if req.url.path == "/v1/jobs":
            import json

            return httpx.Response(
                202, json={"job_id": json.loads(req.content)["job_id"]}
            )
        raise AssertionError(req.url.path)

    async def run():
        assert importlib.util.find_spec("app.queue.dispatcher") is not None, (
            "Falta control de residencia GPU"
        )
        from app.queue.backends.http import HttpEngineBackend
        from app.queue.dispatcher import Dispatcher
        from app.queue.resolver import Resolver

        settings = ContractSettings(
            engine_token="private-test-only",
            engines={"mock": "http://engine-mock:8199"},
        )
        async with HttpEngineBackend(
            settings, "mock", transport=httpx.MockTransport(handler)
        ) as b:
            registry = composition({"mock": b}, {"mock": ([descriptor()], "mock")})
            d = Dispatcher(
                admission(engine, owner, synthetic_registry=registry),
                Resolver(
                    {"mock": b},
                    data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
                    synthetic_registry=registry,
                ),
            )
            result = await d.dispatch()
            assert (result is None) == old_loaded

    asyncio.run(run())
    assert ("/v1/unload" in calls) == unloaded
    if lane == "cpu":
        assert "/v1/load" not in calls


@pytest.mark.parametrize(
    "old_state",
    [
        "foreign_loaded",
        "foreign_busy",
        "owned",
        "unload_lie",
        "free_insufficient",
        "identity_changed",
        "cpu_active",
    ],
)
def test_dispatcher_gpu_switch_residence_proof(engine, old_state):
    from app.queue.backends.protocol import Submission, UnloadResult
    from app.queue.dispatcher import Dispatcher, Resident
    from app.queue.resolver import Resolver
    from engine_contract import LoadedModel

    class Fake(Catalog):
        def __init__(self, name):
            super().__init__(origin="http://engine-" + name + ":8199", engine_id=name)
            self.name = name
            self.loaded = None
            self.unloads = self.loads = self.posts = 0

        async def health(self):
            value = await super().health()
            value.engine_id = self.name
            value.loaded = self.loaded
            if self.name == "old":
                value.gpu.free_mb = 500 if old_state == "free_insufficient" else 10000
                if old_state == "foreign_busy":
                    value.state = "busy"
                    value.job_id = "01K70000000000000000000003"
                if old_state == "identity_changed":
                    value.engine_version = "changed"
            return value

        async def unload(self):
            self.unloads += 1
            if old_state != "unload_lie":
                self.loaded = None
            return UnloadResult(freed_mb=1000)

        async def load(self, request):
            self.loads += 1
            self.loaded = LoadedModel(model_id=request.model_id, mode=request.mode)
            return self.loaded

        async def submit(self, request):
            self.posts += 1
            return Submission(job_id=request.job_id)

    id, owner = add(engine, engine_id="new")
    old, new = Fake("old"), Fake("new")
    old.loaded = LoadedModel(model_id="previous", mode="bf16")
    if old_state == "cpu_active":
        add(engine, status="running", engine_id="old", lane="cpu")

    async def run():
        registry = composition({"old": old, "new": new})
        d = Dispatcher(
            admission(engine, owner, synthetic_registry=registry),
            Resolver(
                {"old": old, "new": new},
                data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
                synthetic_registry=registry,
            ),
        )
        if old_state not in {"foreign_loaded", "foreign_busy"}:
            d.resident = Resident(
                old, "old", "previous", "bf16", ("old", "1", "unknown")
            )
        result = await d.dispatch(id)
        assert (result is not None) == (old_state == "owned")
        assert new.posts == new.loads == (1 if old_state == "owned" else 0)
        assert old.unloads == (
            1 if old_state in {"owned", "unload_lie", "free_insufficient"} else 0
        )

    asyncio.run(run())


def test_dispatcher_fifo_fractional_dates(engine):
    _late, owner = add(engine, created_at="2026-10-08T00:00:00.100000Z")
    early, _ = add(engine, created_at="2026-10-08T00:00:00Z")
    assert admission(engine, owner).select().id == early


@pytest.mark.parametrize("kind", ["upload", "asset", "take"])
@pytest.mark.parametrize(
    "mutation",
    [
        "valid",
        "hash",
        "missing",
        "foreign_root",
        "deleted",
        "media",
        "changed_before_claim",
    ],
)
def test_queue_resolver_owned_sqlite_inputs(engine, kind, mutation):
    import hashlib

    from app.models import Asset, Take, Upload
    from app.queue.resolver import ResolutionError, Resolver

    id, owner = add(
        engine,
        task="audio.beats",
        request={"params": {}, "mode": "bf16", "seed": 1, "timeout_s": 60},
    )
    root = Path(engine.url.database).parent
    source = root / "uploads" / "own.wav"
    source.parent.mkdir()
    source.write_bytes(b"owned synthetic input")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with Session(engine) as s:
        j = s.get(Job, id)
        if kind == "upload":
            row = Upload(
                owner_id=owner,
                kind="audio",
                path="uploads/own.wav",
                sha256=digest,
                media_type="audio/wav",
                rights="own",
                consent="n_a",
            )
            s.add(row)
            s.flush()
            ref = {"type": "upload", "id": row.id}
        else:
            take_id = new_id()
            take_song, take_job = j.song_id, j.id
            if mutation == "foreign_root":
                song = Song(owner_id=owner, title="Otro proyecto")
                s.add(song)
                s.flush()
                other = Job(
                    owner_id=owner,
                    song_id=song.id,
                    task="music.instrumental",
                    lane="gpu",
                    request={},
                    status="succeeded",
                )
                s.add(other)
                s.flush()
                take_song, take_job = song.id, other.id
            take = Take(
                id=take_id,
                owner_id=owner,
                song_id=take_song,
                job_id=take_job,
                root_id=take_id,
                batch_id=new_id(),
                status="ready",
                task="music.instrumental",
                derivation="original",
                model_id="mock",
                model_version="synthetic",
                seed=1,
                commercial_use=True,
            )
            s.add(take)
            s.flush()
            row = Asset(
                owner_id=owner,
                subject_type="take",
                subject_id=take.id,
                role="master",
                path="uploads/own.wav",
                sha256=digest,
                media_type="audio/wav",
                bytes=source.stat().st_size,
            )
            s.add(row)
            s.flush()
            ref = {"type": kind, "id": row.id if kind == "asset" else take.id}
        if mutation == "deleted":
            row.deleted_at = "2026-10-08T00:00:00Z"
        j.request = dict(j.request, inputs=[{"role": "master", "ref": ref}])
        s.commit()
    if mutation == "hash":
        source.write_bytes(b"wrong bytes")
    if mutation == "missing":
        source.unlink()
    c = Catalog()
    c.value["tasks"]["audio.beats"]["inputs"] = [
        {
            "role": "master",
            "required": True,
            "media_types": ["audio/flac" if mutation == "media" else "audio/wav"],
        }
    ]
    r = Resolver({"mock": c}, data_dir=root)
    with Session(engine) as s:
        j = s.get(Job, id)
        s.expunge(j)
    if (
        mutation in {"valid", "changed_before_claim"}
        or kind == "upload"
        and mutation == "foreign_root"
    ):
        resolved = asyncio.run(r.resolve(j, engine=engine))
        wire, _ = resolved.freeze(new_id())
        assert (
            wire.inputs[0].sha256 == digest and wire.inputs[0].path == "uploads/own.wav"
        )
        if mutation == "changed_before_claim":
            source.write_bytes(b"changed after resolution")
            with pytest.raises(ResolutionError):
                admission(engine, owner).reserve(resolved)
            with Session(engine) as s:
                assert s.get(Job, id).attempt == 0
        else:
            assert admission(engine, owner).reserve(resolved) is not None
    else:
        with pytest.raises(ResolutionError):
            asyncio.run(r.resolve(j, engine=engine))


def test_dispatcher_native_writer_precedes_domain_reads(engine):
    import sqlite3

    from sqlalchemy import event

    id, owner = add(engine)
    observed = []

    def inspect_writer(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("SELECT") and "dispatchable_job" in statement:
            with (
                sqlite3.connect(engine.url.database, timeout=0) as competing,
                pytest.raises(sqlite3.OperationalError, match="locked"),
            ):
                competing.execute(
                    "UPDATE snapshot_clock SET revision=revision WHERE id=1"
                )
            observed.append(statement)

    event.listen(engine, "before_cursor_execute", inspect_writer)
    try:
        assert admission(engine, owner).select(id).id == id
    finally:
        event.remove(engine, "before_cursor_execute", inspect_writer)
    assert len(observed) == 1
    with sqlite3.connect(engine.url.database, timeout=0) as competing:
        competing.execute("UPDATE snapshot_clock SET revision=revision WHERE id=1")


@pytest.mark.parametrize(
    "change",
    [
        "cancel",
        "deleted",
        "request",
        "owner",
        "remote",
        "not_before",
        "nightly",
        "budget",
        "pending",
    ],
)
def test_dispatcher_selection_and_cas_changes(engine, change):
    id, owner = add(engine)
    a = admission(engine, owner)
    selected = a.select()
    resolved = resolve(selected)
    with Session(engine) as s:
        j = s.get(Job, id)
        if change == "cancel":
            j.cancel_requested_at = "2026-10-08T02:00:00Z"
        if change == "deleted":
            s.get(Song, j.song_id).deleted_at = "2026-10-08T02:00:00Z"
        if change == "request":
            j.request = dict(j.request, seed=999)
        if change == "remote":
            j.lane = "remote"
        if change == "not_before":
            j.not_before = "2026-10-09T00:00:00Z"
        if change == "nightly":
            j.priority = "nightly"
        if change == "budget":
            j.max_attempts = 4
        if change == "pending":
            parent_id = new_id()
            s.add(
                Job(
                    id=parent_id,
                    owner_id=owner,
                    song_id=j.song_id,
                    task="post.audio",
                    lane="cpu",
                    status="queued",
                    request={},
                )
            )
            s.flush()
            s.add(
                JobDependency(owner_id=owner, job_id=j.id, depends_on_job_id=parent_id)
            )
        s.commit()
    if change == "owner":
        a = admission(engine, new_id())
    if change == "nightly":
        a.clock = lambda: datetime(2026, 10, 8, 12, tzinfo=timezone.utc)
    assert a.reserve(resolved) is None
    with Session(engine) as s:
        assert s.get(Job, id).attempt == 0
