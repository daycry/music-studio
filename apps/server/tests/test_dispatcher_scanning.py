"""Regresiones nativas de ventanas y coste de preselección (sin GPU)."""

import asyncio
import os
from copy import deepcopy
from pathlib import Path

import pytest
from app.models import Job, JobAttempt, JobDependency, Upload
from app.queue.backends.protocol import Submission
from app.queue.dispatcher import Dispatcher
from app.queue.inputs import ResolutionError
from app.queue.resolver import Resolver
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_dispatcher_admission import add, admission
from test_dispatcher_admission import engine as native_engine
from test_queue_resolver import Catalog, descriptor

# Recetas positivas constantes declaradas antes del catálogo y sus mutaciones.
DEFAULT_RECIPE = descriptor()
CPU_MODE_RECIPE = deepcopy(DEFAULT_RECIPE)
CPU_MODE_RECIPE["modes"].append({"id": "cpu", "vram_mb": 0, "notes": "synthetic"})
SOURCE_RECIPE = deepcopy(DEFAULT_RECIPE)
SOURCE_RECIPE["tasks"]["audio.beats"]["inputs"] = [
    {"role": "master", "required": True, "media_types": ["audio/wav"]}
]
HTTP_RECIPES = {}
for _lane, _task in [("cpu", "audio.beats"), ("gpu", "music.instrumental")]:
    _recipe = deepcopy(CPU_MODE_RECIPE)
    _recipe["tasks"] = {_task: _recipe["tasks"][_task]}
    _recipe["tasks"][_task]["inputs"] = [
        {"role": "master", "required": True, "media_types": ["audio/wav"]}
    ]
    HTTP_RECIPES[_lane] = _recipe


def source_job(engine):
    from test_queue_inputs import source_job as original_source_job

    job, owner, root, source, digest, _resolver = original_source_job(engine)
    catalog = Catalog(recipes=[SOURCE_RECIPE])
    catalog.value = deepcopy(SOURCE_RECIPE)
    resolver = Resolver(
        {"mock": catalog}, data_dir=root, synthetic_registry=catalog.synthetic_registry
    )
    return job, owner, root, source, digest, resolver


def positive_load(backend, request):
    from engine_contract import LoadedModel

    backend.loaded = LoadedModel(model_id=request.model_id, mode=request.mode)
    return backend.loaded


def test_clean_snapshot_reader_avoids_job_entities(engine):
    from sqlalchemy import event

    jid, owner = add(engine)
    loaded = {"reader": [], "writer": []}
    with Session(engine) as reader:

        def observe(session, instance):
            if isinstance(instance, Job):
                loaded["reader" if session is reader else "writer"].append(instance.id)

        event.listen(Session, "loaded_as_persistent", observe)
        try:
            pages = list(admission(engine, owner).candidate_batches(reader=reader))
        finally:
            event.remove(Session, "loaded_as_persistent", observe)
    assert [[job.id for job in page] for page in pages] == [[jid]]
    assert all(isinstance(job, Job) for page in pages for job in page)
    assert loaded["writer"] == [jid]
    assert loaded["reader"] == []


@pytest.mark.parametrize("state", ["stale", "dirty", "new", "deleted", "between_pages"])
def test_snapshot_reader_preserves_orm_fallback(engine, state):
    from app.models import Song
    from sqlalchemy import event

    jid, owner = add(engine)
    second, _ = add(engine)
    a = admission(engine, owner)
    loaded = []
    with Session(engine) as reader:
        if state in {"stale", "dirty"}:
            existing = reader.get(Job, jid)
            if state == "stale":
                with Session(engine) as other:
                    other.get(Job, jid).updated_at = "2026-10-08T01:00:00Z"
                    other.commit()
            else:
                existing.priority = "batch"
        elif state == "new":
            pending = Song(owner_id=owner, title="Pendiente")
            reader.add(pending)
        elif state == "deleted":
            removed = reader.get(Job, jid)
            reader.delete(removed)

        def observe(session, instance):
            if session is reader and isinstance(instance, Job):
                loaded.append(instance.id)

        event.listen(Session, "loaded_as_persistent", observe)
        pages = a.candidate_batches(
            reader=reader, size=1 if state == "between_pages" else 400
        )
        try:
            if state in {"dirty", "new", "deleted"}:
                from sqlalchemy.exc import OperationalError

                with pytest.raises(OperationalError, match="database is locked"):
                    next(pages)
                assert not reader.new and not reader.dirty and not reader.deleted
                if state == "dirty":
                    assert existing not in reader and existing.priority == "batch"
                    assert loaded == [second]
                elif state == "new":
                    assert pending.id is not None and loaded == [jid, second]
                else:
                    assert removed not in reader and loaded == [second]
                return
            first = next(pages)
            if state == "between_pages":
                retained = reader.get(Job, second)
                loaded.clear()
                with Session(engine) as other:
                    other.get(Job, second).updated_at = "2026-10-08T01:00:00Z"
                    other.commit()
                remaining = list(pages)
                assert remaining == [[]]
                assert retained not in reader
            elif state == "stale":
                assert [job.id for job in first] == [second]
                assert existing not in reader
                assert loaded == [second]
        finally:
            pages.close()
            event.remove(Session, "loaded_as_persistent", observe)


@pytest.mark.parametrize("column", ["telemetry", "request"])
def test_snapshot_reader_runs_json_processors_before_writer(engine, column):
    import json

    from sqlalchemy import event

    marker = {"processor_probe": "ámbito"}
    _jid, owner = add(engine, **{column: marker})
    seen, writes = [], []
    original = engine.dialect._json_deserializer

    def deserialize(value):
        result = json.loads(value)
        seen.append(result)
        if result == marker:
            raise ValueError("typed reader JSON probe")
        return result

    def observe(connection, cursor, statement, params, context, many):
        if statement.startswith("UPDATE snapshot_clock"):
            writes.append(statement)

    engine.dialect._json_deserializer = deserialize
    engine.dialect._type_memos.clear()
    engine.clear_compiled_cache()
    event.listen(engine, "before_cursor_execute", observe)
    try:
        with pytest.raises(ValueError, match="typed reader JSON probe"):
            list(admission(engine, owner).candidate_batches())
    finally:
        event.remove(engine, "before_cursor_execute", observe)
        engine.dialect._json_deserializer = original
        engine.dialect._type_memos.clear()
        engine.clear_compiled_cache()
    assert marker in seen
    assert writes == []


def test_snapshot_reader_canonical_processed_values(engine):
    from app.queue.resolver import canonical, snapshot

    request = {"z": [True, None, 17], "á": {"b": 2, "a": "canción"}}
    jid, owner = add(engine, request=request, telemetry={"unused": [1, 2]})
    with Session(engine) as session:
        job = session.get(Job, jid)
        fields = (
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
        expected = canonical({field: getattr(job, field) for field in fields})
    pages = list(admission(engine, owner).candidate_batches())
    output = pages[0][0]
    assert isinstance(output, Job)
    assert output.request == request and isinstance(output.request, dict)
    assert output.telemetry == {"unused": [1, 2]}
    assert snapshot(output) == expected
    assert "canción" in expected and "\\u00" not in expected


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_snapshot_reader_revalidates_every_canonical_field(engine, field):
    from app.models import Song, User, new_id
    from sqlalchemy import event, text, update

    jid, owner = add(engine)
    other_owner = owner
    if field == "owner_id":
        # Fallo controlado de fixture: segundo usuario fuera del dominio local.
        # Se restaura el pragma antes de crear/leer el Job con sus restricciones.
        with engine.begin() as connection:
            connection.execute(text("PRAGMA ignore_check_constraints=ON"))
            try:
                with Session(bind=connection) as session:
                    other_owner = new_id()
                    other_user = User(
                        id=other_owner, owner_id=other_owner, name="projection-other"
                    )
                    session.add(other_user)
                    session.flush()
                    other_owner = other_user.id
            finally:
                connection.execute(text("PRAGMA ignore_check_constraints=OFF"))
    with Session(engine) as session:
        other_song = Song(owner_id=other_owner, title="Otra canción")
        session.add(other_song)
        session.commit()
        values = {
            "id": new_id(),
            "owner_id": other_owner,
            "song_id": other_song.id,
            "task": "audio.beats",
            "lane": "cpu",
            "request": {"params": {"style": "editada"}},
            "model_id": "edited-model",
            "engine_id": "edited-engine",
            "attempt": 1,
            "max_attempts": 2,
            "status": "blocked",
            "priority": "batch",
            "created_at": "2026-10-07T00:00:00.123456Z",
            "updated_at": "2026-10-08T00:00:00.123456Z",
            "deleted_at": "2026-10-08T00:00:00Z",
            "not_before": "2026-10-08T00:00:00Z",
            "cancel_requested_at": "2026-10-08T00:00:00Z",
        }
    changed = []

    def edit(connection, cursor, statement, params, context, many):
        if statement.startswith("UPDATE snapshot_clock") and not changed:
            changed.append(field)
            with Session(engine) as session:
                if field in {"id", "owner_id"}:
                    # Solo esta fixture ensaya identidades normalmente inmutables.
                    # DDL transaccional: se repone el trigger antes del commit.
                    identity_trigger = session.scalar(
                        text("SELECT sql FROM sqlite_master WHERE name='identity_job'")
                    )
                    assert identity_trigger
                    session.execute(text("DROP TRIGGER identity_job"))
                current = session.get(Job, jid)
                # Aislar el campo: no dejar que onupdate cambie también la fecha.
                edits = {"updated_at": current.updated_at, field: values[field]}
                if field == "owner_id":
                    # El nuevo propietario requiere una canción de su dominio.
                    edits["song_id"] = values["song_id"]
                session.execute(
                    update(Job).where(Job.id == jid).values(**edits),
                    execution_options={"synchronize_session": False},
                )
                if field in {"id", "owner_id"}:
                    session.execute(text(identity_trigger))
                session.commit()

    event.listen(engine, "before_cursor_execute", edit)
    try:
        assert list(admission(engine, owner).candidate_batches()) == [[]]
    finally:
        event.remove(engine, "before_cursor_execute", edit)
    assert changed == [field]


@pytest.fixture(name="engine")
def scanning_engine():
    yield from native_engine.__wrapped__()


def queue_heads(engine, count, **changes):
    first, owner = add(engine, priority="interactive", **changes)
    with Session(engine) as session:
        row = session.get(Job, first)
        for _ in range(count - 1):
            session.add(
                Job(
                    owner_id=owner,
                    song_id=row.song_id,
                    task=row.task,
                    lane=row.lane,
                    request=row.request,
                    engine_id=row.engine_id,
                    model_id=row.model_id,
                    priority=row.priority,
                    not_before=row.not_before,
                    created_at=row.created_at,
                )
            )
        session.commit()
    return owner


def dispatcher(engine, owner):
    backend = Catalog(recipes=[DEFAULT_RECIPE, CPU_MODE_RECIPE])

    async def load(request):
        return positive_load(backend, request)

    async def submit(request):
        return Submission(job_id=request.job_id)

    backend.load, backend.submit = load, submit
    return Dispatcher(
        admission(engine, owner, synthetic_registry=backend.synthetic_registry),
        Resolver(
            {"mock": backend},
            data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
            synthetic_registry=backend.synthetic_registry,
        ),
    )


@pytest.mark.parametrize("bad", ["engine", "model", "task", "params"])
@pytest.mark.parametrize("lane", ["cpu", "gpu"])
def test_invalid_head_does_not_abort_automatic(engine, bad, lane):
    changes = {
        "engine": {"engine_id": "absent"},
        "model": {"model_id": "absent"},
        "task": {"task": "music.absent"},
        "params": {"request": {"params": {"duration_s": -1}}},
    }[bad]
    owner = queue_heads(engine, 1, **changes)
    valid, _ = add(
        engine,
        lane=lane,
        task="audio.beats" if lane == "cpu" else "music.instrumental",
        request={"params": {}, "mode": "cpu"}
        if lane == "cpu"
        else {"params": {"duration_s": 30}, "mode": "bf16"},
    )
    d = dispatcher(engine, owner)
    d.resolver.backends["mock"].value["modes"].append(
        {"id": "cpu", "vram_mb": 0, "notes": "synthetic"}
    )
    result = asyncio.run(d.dispatch())
    assert result and result.job_id == valid
    with Session(engine) as session:
        bad_rows = session.scalars(
            select(Job).where(Job.priority == "interactive")
        ).all()
        assert all(row.status == "queued" and row.attempt == 0 for row in bad_rows)
        assert len(session.scalars(select(JobAttempt)).all()) == 1


@pytest.mark.parametrize("bad", ["engine", "model", "task", "params"])
def test_explicit_invalid_does_not_retarget(engine, bad):
    changes = {
        "engine": {"engine_id": "absent"},
        "model": {"model_id": "absent"},
        "task": {"task": "music.absent"},
        "params": {"request": {"params": {"duration_s": -1}}},
    }[bad]
    first, owner = add(engine, **changes)
    valid, _ = add(engine)
    with pytest.raises(ResolutionError):
        asyncio.run(dispatcher(engine, owner).dispatch(first))
    with Session(engine) as session:
        assert session.get(Job, valid).attempt == 0
        assert not session.scalars(select(JobAttempt)).all()


@pytest.mark.parametrize("count", [400, 401, 2001])
@pytest.mark.parametrize("blocker", ["future", "parent", "invalid"])
def test_reaches_runnable_after_multiple_windows(engine, count, blocker):
    changes = {
        "future": {"not_before": "2026-10-08T02:00:00.000001Z"},
        "parent": {},
        "invalid": {"engine_id": "absent"},
    }[blocker]
    owner = queue_heads(engine, count, **changes)
    if blocker == "parent":
        with Session(engine) as session:
            root = session.scalar(
                select(Job.song_id).where(Job.priority == "interactive")
            )
        parent, _ = add(engine, status="blocked", song_id=root)
        with Session(engine) as session:
            for row in session.scalars(
                select(Job).where(Job.priority == "interactive")
            ):
                session.add(
                    JobDependency(
                        owner_id=owner, job_id=row.id, depends_on_job_id=parent
                    )
                )
            session.commit()
    valid, _ = add(engine)
    result = asyncio.run(dispatcher(engine, owner).dispatch())
    assert result and result.job_id == valid
    with Session(engine) as session:
        assert len(session.scalars(select(JobAttempt)).all()) == 1
        heads = session.scalars(select(Job).where(Job.priority == "interactive")).all()
        assert all(row.attempt == 0 for row in heads)
        assert all(
            row.status == ("blocked" if blocker == "parent" else "queued")
            for row in heads
        )


@pytest.mark.parametrize("count", [200, 400])
@pytest.mark.parametrize("busy_lane", ["gpu", "cpu"])
def test_busy_screen_native_sqlite_actual_wav_asgi(
    engine, monkeypatch, count, busy_lane
):
    """SQLite real + HTTP/ASGI; adapter sintético explícito, no engine GPU real."""
    import hashlib
    import io
    import json
    import wave
    from collections import Counter
    from contextlib import AsyncExitStack

    import httpx
    from app.queue.backends.http import HttpEngineBackend
    from app.settings import ContractSettings
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from test_queue_backend import health

    free_lane = "cpu" if busy_lane == "gpu" else "gpu"
    task = lambda lane: "audio.beats" if lane == "cpu" else "music.instrumental"
    owner = queue_heads(
        engine,
        count,
        lane=busy_lane,
        task=task(busy_lane),
        engine_id="busy",
        request={"params": {}, "mode": "cpu" if busy_lane == "cpu" else "bf16"},
    )
    selected, _ = add(
        engine,
        lane=free_lane,
        task=task(free_lane),
        engine_id="free",
        request={"params": {}, "mode": "cpu" if free_lane == "cpu" else "bf16"},
    )
    root = Path(engine.url.database).parent
    (root / "uploads").mkdir()
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 80)
    content = stream.getvalue()
    with Session(engine) as session:
        rows = session.scalars(select(Job)).all()
        for index, row in enumerate(rows):
            relative = f"uploads/{index}.wav"
            (root / relative).write_bytes(content)
            upload = Upload(
                owner_id=owner,
                kind="audio",
                path=relative,
                sha256=hashlib.sha256(content).hexdigest(),
                media_type="audio/wav",
                rights="own",
                consent="n_a",
            )
            session.add(upload)
            session.flush()
            row.request = dict(
                row.request,
                inputs=[{"role": "master", "ref": {"type": "upload", "id": upload.id}}],
            )
        session.commit()
    counts = Counter()
    hashes = []
    original = hashlib.file_digest

    def counted(stream, algorithm):
        hashes.append(str(stream.name))
        return original(stream, algorithm)

    monkeypatch.setattr(hashlib, "file_digest", counted)

    def adapter(name, lane):
        loaded = [None]

        async def endpoint(request):
            counts[name + request.url.path] += 1
            if request.url.path == "/v1/health":
                value = health()
                value["engine_id"] = name
                value["loaded"] = loaded[0]
                if name == "busy":
                    value.update(
                        state="busy",
                        job_id="01K70000000000000000000003",
                        loaded={
                            "model_id": "mock",
                            "mode": "cpu" if lane == "cpu" else "bf16",
                        },
                    )
                return JSONResponse(value)
            if request.url.path == "/v1/models":
                model = deepcopy(HTTP_RECIPES[lane])
                return JSONResponse([model])
            body = await request.json()
            if request.url.path == "/v1/load":
                loaded[0] = {"model_id": body["model_id"], "mode": body["mode"]}
                return JSONResponse(loaded[0])
            return JSONResponse({"job_id": body["job_id"]}, status_code=202)

        return Starlette(
            routes=[
                Route(path, endpoint, methods=[method])
                for path, method in [
                    ("/v1/health", "GET"),
                    ("/v1/models", "GET"),
                    ("/v1/load", "POST"),
                    ("/v1/jobs", "POST"),
                ]
            ]
        )

    async def run():
        settings = ContractSettings(
            engine_token="private-test-only",
            engines={
                "busy": "http://engine-acestep:8199",
                "free": "http://engine-analysis:8199",
            },
        )
        async with AsyncExitStack() as stack:
            backends = {
                name: await stack.enter_async_context(
                    HttpEngineBackend(
                        settings,
                        name,
                        transport=httpx.ASGITransport(app=adapter(name, lane)),
                    )
                )
                for name, lane in [("busy", busy_lane), ("free", free_lane)]
            }
            from synthetic_composition import composition

            registry = composition(
                backends,
                {
                    name: ([HTTP_RECIPES[lane]], name)
                    for name, lane in [("busy", busy_lane), ("free", free_lane)]
                },
            )
            d = Dispatcher(
                admission(engine, owner, synthetic_registry=registry),
                Resolver(backends, data_dir=root, synthetic_registry=registry),
            )
            result = await d.dispatch()
            assert result and result.job_id == selected
            before = dict(counts)
            await d.dispatch()
            assert counts["busy/v1/health"] > before["busy/v1/health"]

    asyncio.run(run())
    proof = {
        "adapter": "synthetic HTTP/ASGI endpoints; native SQLite and distinct owned WAV files",
        "pending_busy": count,
        "busy_lane": busy_lane,
        "endpoint_counts_two_dispatches": dict(counts),
        "hashed_paths": hashes,
        "actual_file_bytes": len(content),
        "files": count + 1,
    }
    (
        Path(os.environ["STUDIO_QUEUE_TEST_ROOT"])
        / f"busy-profile-{busy_lane}-{count}.json"
    ).write_text(json.dumps(proof, indent=2), encoding="utf-8")
    assert len(hashes) == 2, hashes
    assert counts["busy/v1/health"] <= 6, counts
    assert counts["free/v1/jobs"] == 1


def test_unavailable_catalog_is_distinct_from_invalid_request(engine):
    from app.queue.resolver import CatalogUnavailable

    jid, owner = add(engine, engine_id="mock")
    d = dispatcher(engine, owner)
    d.resolver.backends["mock"].down = True
    with pytest.raises(CatalogUnavailable):
        asyncio.run(d.dispatch(jid))
    with Session(engine) as session:
        assert session.get(Job, jid).status == "queued"
        assert session.get(Job, jid).attempt == 0


@pytest.mark.parametrize("change", ["busy", "identity", "vram"])
def test_selected_health_revalidated_after_screen(engine, monkeypatch, change):
    from engine_contract import Health
    from test_queue_backend import health

    jid, owner = add(engine)
    d = dispatcher(engine, owner)
    backend = d.resolver.backends["mock"]
    calls = []

    async def observed():
        value = health()
        value["engine_id"] = "mock"
        calls.append(value)
        if len(calls) > 1:
            if change == "busy":
                value.update(state="busy", job_id="01K70000000000000000000003")
            elif change == "identity":
                value["engine_version"] = "changed"
            else:
                value["gpu"]["free_mb"] = 1511
        return Health.model_validate(value)

    backend.health = observed
    assert asyncio.run(d.dispatch(jid)) is None
    with Session(engine) as session:
        assert session.get(Job, jid).attempt == 0
        assert not session.scalars(select(JobAttempt)).all()


def test_invalid_selected_input_does_not_unload_resident(engine):
    from app.queue.dispatcher import Resident
    from engine_contract import Health

    job, owner, _root, source, _digest, resolver = source_job(engine)
    source.write_bytes(b"tampered")
    with Session(engine) as session:
        current = session.get(Job, job.id)
        current.task = "music.instrumental"
        session.commit()
    backend = resolver.backends["mock"]
    unloads = []
    state = [True]
    original = backend.health

    async def health():
        value = (await original()).model_dump(mode="json")
        if state[0]:
            value["loaded"] = {"model_id": "prior", "mode": "bf16"}
        return Health.model_validate(value)

    async def unload():
        unloads.append(True)
        state[0] = False

    backend.health, backend.unload = health, unload
    d = Dispatcher(
        admission(engine, owner, synthetic_registry=resolver.synthetic_registry),
        resolver,
    )
    d.resident = Resident(backend, "mock", "prior", "bf16", ("mock", "1", "synthetic"))
    with pytest.raises(ResolutionError):
        asyncio.run(d.dispatch(job.id))
    assert unloads == []


def test_fractional_fifo_and_priority_across_batch_boundary(engine):
    owner = queue_heads(engine, 399, engine_id="absent")
    earlier, _ = add(
        engine,
        priority="interactive",
        id="01K70000000000000000000999",
        created_at="2026-10-08 00:00:00.000001Z",
    )
    later, _ = add(
        engine,
        priority="interactive",
        id="01K70000000000000000000001",
        created_at="2026-10-08T00:00:00.000002Z",
    )
    normal, _ = add(engine, created_at="2026-10-07T23:59:59Z")
    pages = list(admission(engine, owner).candidate_batches())
    ids = [job.id for page in pages for job in page]
    assert len(pages[0]) == 400
    assert ids[-3:] == [earlier, later, normal]
    result = asyncio.run(dispatcher(engine, owner).dispatch())
    assert result and result.job_id == earlier


def test_finite_snapshot_and_current_page_revalidation(engine):
    owner = queue_heads(engine, 400, not_before="2026-10-09T00:00:00Z")
    stale, _ = add(engine)
    pages = admission(engine, owner).candidate_batches()
    assert next(pages) == []
    with Session(engine) as session:
        session.get(Job, stale).cancel_requested_at = "2026-10-08T02:00:00Z"
        session.commit()
    inserted, _ = add(engine, created_at="2026-10-08T00:00:01Z")
    rest = [job.id for page in pages for job in page]
    assert stale not in rest and inserted not in rest
    assert admission(engine, owner).select().id == inserted


@pytest.mark.parametrize(
    "stamp,expected",
    [("2026-10-08 02:00:00Z", True), ("2026-10-08T02:00:00.000001Z", False)],
)
def test_paged_not_before_keeps_microsecond_utc(engine, stamp, expected):
    jid, owner = add(engine, not_before=stamp)
    ids = [
        job.id for page in admission(engine, owner).candidate_batches() for job in page
    ]
    assert (jid in ids) == expected


@pytest.mark.parametrize(
    "window,expected",
    [
        ("01:00-07:00", True),
        ("02:01-07:00", False),
        ("23:00-03:00", True),
        ("23:00-02:00", False),
    ],
)
def test_paged_nightly_keeps_utc_window(engine, window, expected):
    jid, owner = add(engine, priority="nightly")
    a = admission(engine, owner)
    a.nightly_window = window
    assert (
        any(job.id == jid for page in a.candidate_batches() for job in page) == expected
    )


def test_failed_dependency_beyond_window_still_durable_without_attempt(engine):
    owner = queue_heads(engine, 400, not_before="2026-10-09T00:00:00Z")
    parent, _ = add(engine, status="failed")
    with Session(engine) as session:
        root = session.get(Job, parent).song_id
    child, _ = add(engine, status="blocked", song_id=root)
    with Session(engine) as session:
        session.add(
            JobDependency(owner_id=owner, job_id=child, depends_on_job_id=parent)
        )
        session.commit()
    assert not [
        job for page in admission(engine, owner).candidate_batches() for job in page
    ]
    with Session(engine) as session:
        row = session.get(Job, child)
        assert (row.status, row.error_code, row.attempt) == (
            "failed",
            "DEPENDENCY_FAILED",
            0,
        )
        assert not session.scalars(select(JobAttempt)).all()


@pytest.mark.parametrize("change", ["upload_deleted", "file_deleted", "file_changed"])
@pytest.mark.parametrize("explicit", [False, True])
def test_native_input_race_between_resolve_and_reserve(engine, change, explicit):

    head, owner, root, source, _digest, resolver = source_job(engine)
    with Session(engine) as session:
        session.get(Job, head.id).priority = "interactive"
        session.commit()
    tail, _ = add(engine)
    d = Dispatcher(
        admission(engine, owner, synthetic_registry=resolver.synthetic_registry),
        resolver,
    )
    sends = []

    async def load(request):
        return positive_load(resolver.backends["mock"], request)

    async def submit(request):
        sends.append(request.job_id)
        return Submission(job_id=request.job_id)

    resolver.backends["mock"].load = load
    resolver.backends["mock"].submit = submit
    reserve = d.admission.reserve
    changed = []

    def racing_reserve(resolved):
        if resolved.job_id == head.id:
            changed.append(resolved.job_id)
            if change == "upload_deleted":
                with Session(engine) as session:
                    upload = session.scalar(select(Upload))
                    upload.deleted_at = "2026-10-08T02:00:00Z"
                    session.commit()
            elif change == "file_deleted":
                source.unlink()
            else:
                source.write_bytes(b"changed after full resolve")
        return reserve(resolved)

    d.admission.reserve = racing_reserve
    if explicit:
        with pytest.raises(ResolutionError):
            asyncio.run(d.dispatch(head.id))
    else:
        result = asyncio.run(d.dispatch())
        assert result and result.job_id == tail
    assert changed == [head.id]
    with Session(engine) as session:
        assert session.get(Job, head.id).attempt == 0
        assert session.get(Job, tail).attempt == (0 if explicit else 1)
        attempts = session.scalars(select(JobAttempt)).all()
        assert [a.job_id for a in attempts] == ([] if explicit else [tail])
        assert sends == ([] if explicit else [attempts[0].id])
    staging = root / "tmp/_server_inputs"
    assert not staging.exists() or list(staging.iterdir()) == []


@pytest.mark.parametrize("disposition", ["known", "unknown_sql", "unknown_runtime"])
@pytest.mark.parametrize("failure", [ResolutionError, RuntimeError])
def test_native_postcommit_failure_retains_claim_and_staging(
    engine, disposition, failure
):
    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError

    head, owner, root, _source, digest, resolver = source_job(engine)
    with Session(engine) as session:
        session.get(Job, head.id).priority = "interactive"
        session.commit()
    tail, _ = add(engine)
    d = Dispatcher(
        admission(engine, owner, synthetic_registry=resolver.synthetic_registry),
        resolver,
    )
    calls = []

    async def submit(request):
        calls.append(request.job_id)
        return Submission(job_id=request.job_id)

    resolver.backends["mock"].submit = submit
    original = d.admission.reserve
    committed = []

    def after_commit(session):
        committed.append(True)
        raise failure("native commit completed; observation lost")

    def unknown(connection, cursor, statement, params, context, many):
        if committed and statement.startswith("SELECT job_attempt."):
            if disposition == "unknown_runtime":
                raise RuntimeError("independent claim probe unavailable")
            raise OperationalError(statement, params, RuntimeError("probe unavailable"))

    def faulted_reserve(resolved):
        event.listen(Session, "after_commit", after_commit)
        if disposition != "known":
            event.listen(engine, "before_cursor_execute", unknown)
        try:
            return original(resolved)
        finally:
            event.remove(Session, "after_commit", after_commit)
            if disposition != "known":
                event.remove(engine, "before_cursor_execute", unknown)

    d.admission.reserve = faulted_reserve
    expected = RuntimeError if disposition == "unknown_runtime" else failure
    with pytest.raises(expected):
        asyncio.run(d.dispatch())
    assert calls == []
    with Session(engine) as session:
        attempts = session.scalars(select(JobAttempt)).all()
        assert len(attempts) == 1
        attempt = attempts[0]
        assert (attempt.job_id, attempt.status) == (head.id, "prepared")
        assert (
            session.get(Job, head.id).status,
            session.get(Job, head.id).attempt,
        ) == ("running", 1)
        assert session.get(Job, tail).attempt == 0
        wire = attempt.engine_request.inputs[0]
        import hashlib

        assert hashlib.sha256((root / wire.path).read_bytes()).hexdigest() == digest
        assert wire.path.startswith("tmp/_server_inputs/")
    d.admission.reserve = original
    assert asyncio.run(d.dispatch(head.id)) is None
    assert calls == []
    with Session(engine) as session:
        assert len(session.scalars(select(JobAttempt)).all()) == 1


@pytest.mark.parametrize("count", [200, 400, 2001])
def test_native_durable_gpu_screen_once_per_dispatch_snapshot(engine, count):
    import json
    import time
    from itertools import pairwise

    from sqlalchemy import event

    owner = queue_heads(engine, count)
    busy, _ = add(engine, lane="gpu", status="running", engine_id="other", support=True)
    tail, _ = add(
        engine, lane="cpu", task="audio.beats", request={"params": {}, "mode": "cpu"}
    )
    d = dispatcher(engine, owner)
    d.resolver.backends["mock"].value["modes"].append(
        {"id": "cpu", "vram_mb": 0, "notes": "synthetic"}
    )
    queries, loop_queries, ticks, durations = [], [], [], []

    def observe(connection, cursor, statement, params, context, many):
        if (
            "count(*)" in statement
            and "job.lane = ?" in statement
            and params[0] == "gpu"
        ):
            queries.append(statement)
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                pass
            else:
                loop_queries.append(statement)

    async def run():
        finished = False

        async def heartbeat():
            while not finished:
                ticks.append(time.perf_counter())
                await asyncio.sleep(0.001)

        pulse = asyncio.create_task(heartbeat())
        try:
            start = time.perf_counter()
            result = await d.dispatch()
            durations.append(time.perf_counter() - start)
            assert result and result.job_id == tail
            first_count = len(queries)
            start = time.perf_counter()
            assert await d.dispatch() is None
            durations.append(time.perf_counter() - start)
            return first_count
        finally:
            finished = True
            await pulse

    event.listen(engine, "before_cursor_execute", observe)
    try:
        first_count = asyncio.run(run())
    finally:
        event.remove(engine, "before_cursor_execute", observe)
    proof = {
        "candidates": count,
        "database": "native file SQLite head0005",
        "adapter": "synthetic Catalog",
        "occupancy_selects": [first_count, len(queries) - first_count],
        "occupancy_selects_on_event_loop": len(loop_queries),
        "heartbeat_ticks": len(ticks),
        "dispatch_seconds": durations,
        "max_heartbeat_gap_seconds": max(
            (b - a for a, b in pairwise(ticks)), default=0
        ),
    }
    (
        Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]) / f"durable-gpu-profile-{count}.json"
    ).write_text(json.dumps(proof, indent=2), encoding="utf-8")
    assert proof["occupancy_selects"] == [1, 1], proof
    assert not loop_queries, proof
    assert len(ticks) > 1, proof
    with Session(engine) as session:
        assert session.get(Job, busy).status == "running"
        assert [a.job_id for a in session.scalars(select(JobAttempt))] == [tail]
        assert all(
            j.attempt == 0
            for j in session.scalars(select(Job).where(Job.priority == "interactive"))
        )


@pytest.mark.parametrize("boundary", ["resolve", "preflight"])
def test_native_screen_cache_cannot_authorize_stale_gpu_occupancy(engine, boundary):
    jid, owner = add(engine)
    d = dispatcher(engine, owner)
    calls = []

    async def forbidden(request):
        calls.append(request)
        raise AssertionError("Busy GPU must neither load nor submit")

    d.resolver.backends["mock"].load = forbidden
    d.resolver.backends["mock"].submit = forbidden
    if boundary == "resolve":
        original = d.resolver.resolve

        async def race(job, **kwargs):
            resolved = await original(job, **kwargs)
            add(engine, lane="gpu", status="running", engine_id="other", support=True)
            return resolved

        d.resolver.resolve = race
    else:
        original = d._preflight

        async def race(resolved):
            allowed = await original(resolved)
            assert allowed
            add(engine, lane="gpu", status="running", engine_id="other", support=True)
            return allowed

        d._preflight = race
    assert asyncio.run(d.dispatch(jid)) is None
    assert calls == []
    with Session(engine) as session:
        assert session.get(Job, jid).attempt == 0
        assert not session.scalars(select(JobAttempt)).all()


@pytest.mark.parametrize(
    "boundary",
    [
        "source_open",
        "source_read",
        "destination_open",
        "destination_write",
        "fsync",
        "parent",
        "cleanup",
    ],
)
def test_native_staging_io_failures_remain_failclosed(engine, monkeypatch, boundary):
    from app.queue import inputs

    head, owner, root, source, _digest, resolver = source_job(engine)
    with Session(engine) as session:
        session.get(Job, head.id).priority = "interactive"
        session.commit()
    tail, _ = add(engine)
    d = Dispatcher(
        admission(engine, owner, synthetic_registry=resolver.synthetic_registry),
        resolver,
    )
    visits, sends, failures = [], [], []
    original_open, original_path = Path.open, inputs.confined_path
    original_mkdir, original_rmdir = Path.mkdir, Path.rmdir
    original_resolve = resolver.resolve
    armed = []
    error = (
        PermissionError("source access denied")
        if boundary == "source_open"
        else FileNotFoundError(boundary)
    )

    def fail():
        failures.append(boundary)
        raise error

    class FaultedStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def read(self, size):
            return fail()

        def write(self, chunk):
            return fail()

    def confined(data_root, relative):
        path = original_path(data_root, relative)
        staging = root / "tmp/_server_inputs"
        if path == source and staging.exists() and any(staging.iterdir()):
            armed.append(path)
        return path

    def opening(path, mode="r", *args, **kwargs):
        if path == source and mode == "rb" and armed:
            armed.clear()
            if boundary == "source_open":
                fail()
            if boundary == "cleanup":
                source.unlink()
            stream = original_open(path, mode, *args, **kwargs)
            return FaultedStream(stream) if boundary == "source_read" else stream
        if mode == "xb" and path.parent.parent == root / "tmp/_server_inputs":
            if boundary == "destination_open":
                fail()
            stream = original_open(path, mode, *args, **kwargs)
            return FaultedStream(stream) if boundary == "destination_write" else stream
        return original_open(path, mode, *args, **kwargs)

    def mkdir(path, *args, **kwargs):
        if boundary == "parent" and path == root / "tmp/_server_inputs":
            fail()
        return original_mkdir(path, *args, **kwargs)

    def rmdir(path):
        if boundary == "cleanup" and path.parent == root / "tmp/_server_inputs":
            fail()
        return original_rmdir(path)

    async def resolve(job, **kwargs):
        visits.append(job.id)
        return await original_resolve(job, **kwargs)

    async def submit(request):
        sends.append(request.job_id)
        return Submission(job_id=request.job_id)

    monkeypatch.setattr(inputs, "confined_path", confined)
    monkeypatch.setattr(Path, "open", opening)
    monkeypatch.setattr(Path, "mkdir", mkdir)
    monkeypatch.setattr(Path, "rmdir", rmdir)
    if boundary == "fsync":
        monkeypatch.setattr(inputs.os, "fsync", lambda fd: fail())
    resolver.resolve = resolve
    resolver.backends["mock"].submit = submit
    with pytest.raises(type(error)) as caught:
        asyncio.run(d.dispatch())
    assert caught.value is error
    assert failures == [boundary]
    assert visits == [head.id] and sends == []
    with Session(engine) as session:
        assert session.get(Job, head.id).attempt == 0
        assert session.get(Job, tail).attempt == 0
        assert not session.scalars(select(JobAttempt)).all()
    staging = root / "tmp/_server_inputs"
    if boundary == "cleanup":
        assert len(list(staging.iterdir())) == 1
        assert list(next(staging.iterdir()).iterdir()) == []
    else:
        assert not staging.exists() or not list(staging.iterdir())


@pytest.mark.parametrize("explicit", [False, True])
def test_native_source_disappears_after_staging_confinement(
    engine, monkeypatch, explicit
):
    import hashlib
    import json

    from app.queue import inputs

    head, owner, root, source, digest, resolver = source_job(engine)
    with Session(engine) as session:
        session.get(Job, head.id).priority = "interactive"
        session.commit()
    tail, _ = add(engine)
    d = Dispatcher(
        admission(engine, owner, synthetic_registry=resolver.synthetic_registry),
        resolver,
    )
    sends, visits, removed = [], [], []
    original_path, original_open = inputs.confined_path, Path.open
    original_resolve = resolver.resolve
    armed = []

    def confined(data_root, relative):
        path = original_path(data_root, relative)
        staging = root / "tmp/_server_inputs"
        if path == source and staging.exists() and any(staging.iterdir()):
            armed.append(path)
        return path

    def opening(path, mode="r", *args, **kwargs):
        if path == source and mode == "rb" and armed:
            with original_open(path, "rb") as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == digest
            source.unlink()
            removed.append(str(source))
            armed.clear()
        return original_open(path, mode, *args, **kwargs)

    async def resolve(job, **kwargs):
        visits.append(job.id)
        return await original_resolve(job, **kwargs)

    async def load(request):
        return positive_load(resolver.backends["mock"], request)

    async def submit(request):
        sends.append(request.job_id)
        return Submission(job_id=request.job_id)

    monkeypatch.setattr(inputs, "confined_path", confined)
    monkeypatch.setattr(Path, "open", opening)
    resolver.resolve = resolve
    resolver.backends["mock"].load = load
    resolver.backends["mock"].submit = submit
    try:
        if explicit:
            with pytest.raises(ResolutionError) as caught:
                asyncio.run(d.dispatch(head.id))
            from app.queue.admission import PreclaimResolutionError

            assert isinstance(caught.value, PreclaimResolutionError)
            assert isinstance(caught.value.__cause__, ResolutionError)
            assert isinstance(caught.value.__cause__.__cause__, FileNotFoundError)
        else:
            result = asyncio.run(d.dispatch())
            assert result and result.job_id == tail
    finally:
        staging = root / "tmp/_server_inputs"
        proof = {
            "source": str(source),
            "removed": removed,
            "source_absent": not source.exists(),
            "staging_empty": not staging.exists() or not list(staging.iterdir()),
            "visits": visits,
            "sends": sends,
            "explicit": explicit,
        }
        (
            Path(os.environ["STUDIO_QUEUE_TEST_ROOT"])
            / f"source-open-race-{explicit}-{head.id}.json"
        ).write_text(json.dumps(proof, indent=2), encoding="utf-8")
    assert removed == [str(source)]
    assert proof["staging_empty"]
    assert visits == ([head.id] if explicit else [head.id, tail])
    with Session(engine) as session:
        assert session.get(Job, head.id).attempt == 0
        assert session.get(Job, tail).attempt == (0 if explicit else 1)
        attempts = session.scalars(select(JobAttempt)).all()
        assert [a.job_id for a in attempts] == ([] if explicit else [tail])
        assert sends == ([] if explicit else [attempts[0].id])
