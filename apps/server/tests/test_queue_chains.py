"""U3, SQLite nativo; catálogo y backend sintéticos, nunca aceptación musical."""

import asyncio
import copy
import os
from pathlib import Path

import pytest
from app.models import Job, JobDependency, LyricsVersion, Song, Take, new_id
from app.queue.resolver import Resolver
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from test_dispatcher_admission import add
from test_dispatcher_admission import engine as _native_engine
from test_queue_resolver import Catalog

engine = _native_engine


def services(database):
    jid, owner = add(database)
    with Session(database) as session:
        song = session.get(Job, jid).song_id
        session.delete(session.get(Job, jid))
        session.commit()
    from synthetic_composition import chain_recipes

    catalog = Catalog(recipes=chain_recipes())
    catalog.value["modes"].append({"id": "cpu", "vram_mb": 0, "notes": "synthetic"})
    catalog.value["tasks"]["audio.beats"]["inputs"] = [
        {"role": "master", "required": True, "media_types": ["audio/wav", "audio/flac"]}
    ]
    resolver = Resolver(
        {"mock": catalog},
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        synthetic_registry=catalog.synthetic_registry,
    )
    return owner, song, catalog, resolver


def request(n=3, seed=17):
    return {
        "params": {"style": "literal", "duration_s": 30},
        "seed": seed,
        "n_outputs": n,
        "mode": "bf16",
        "timeout_s": 60,
    }


def create(database, owner, song, resolver, **kwargs):
    from app.queue.chains import GenerationChains

    return asyncio.run(
        GenerationChains(database, owner, resolver).create(
            song,
            task="music.instrumental",
            request=kwargs.pop("request", request()),
            model_id="mock",
            **kwargs,
        )
    )


def test_queue_chain_atomic_variants_and_real_edges(engine):
    owner, song, catalog, resolver = services(engine)
    original = copy.deepcopy(catalog.value)
    chain = create(engine, owner, song, resolver)
    with Session(engine) as session:
        takes = list(session.scalars(select(Take).order_by(Take.variant_index)))
        jobs = list(session.scalars(select(Job)))
        assert len(takes) == 3 and len(jobs) == 5
        assert [(t.variant_index, t.seed, t.status, t.job_id) for t in takes] == [
            (i, 17 + i, "queued", chain.generation_job_id) for i in range(3)
        ]
        assert len({t.batch_id for t in takes}) == 1
        assert all(t.root_id == t.id for t in takes)
        gen = session.get(Job, chain.generation_job_id)
        assert (gen.task, gen.lane, gen.status, gen.attempt, gen.max_attempts) == (
            "music.instrumental",
            "gpu",
            "queued",
            0,
            3,
        )
        assert gen.request == request()
        post = session.get(Job, chain.post_job_id)
        assert (post.task, post.lane, post.status) == ("post.audio", "cpu", "blocked")
        assert [x["output_index"] for x in post.request["inputs"]] == [0, 1, 2]
        assert all(
            x["ref"] == {"type": "job", "id": gen.id} and "path" not in x
            for x in post.request["inputs"]
        )
        beats = [session.get(Job, j) for j in chain.beat_job_ids]
        assert [j.request["inputs"] for j in beats] == [
            [{"role": "master", "ref": {"type": "take", "id": t.id}}] for t in takes
        ]
        assert all(
            (j.task, j.lane, j.status) == ("audio.beats", "cpu", "blocked")
            for j in beats
        )
        assert session.scalar(select(func.count()).select_from(JobDependency)) == 4
        assert session.execute(text("PRAGMA journal_mode")).scalar() == "wal"
    assert catalog.value == original


@pytest.mark.parametrize(
    "bad",
    [
        "overflow",
        "seed_bool",
        "unverified",
        "bad_param",
        "trash",
        "foreign",
        "lyrics_missing",
    ],
)
def test_queue_chain_rejects_before_rows(engine, bad):
    owner, song, catalog, resolver = services(engine)
    body = request()
    task = "music.instrumental"
    if bad == "overflow":
        body["seed"] = 2**64 - 2
    if bad == "seed_bool":
        body["seed"] = True
    if bad == "unverified":
        catalog.value["tasks"][task]["verified"] = False
    if bad == "bad_param":
        body["params"]["arbitrary_path"] = "secret"
    if bad == "trash":
        with Session(engine) as s:
            s.get(Song, song).deleted_at = "2026-10-08T00:00:00Z"
            s.commit()
    if bad == "foreign":
        owner = new_id()
    if bad == "lyrics_missing":
        task = "music.song"
    from app.queue.chains import GenerationChains

    with pytest.raises(ValueError):
        asyncio.run(
            GenerationChains(engine, owner, resolver).create(
                song, task=task, request=body, model_id="mock"
            )
        )
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(Job)) == 0
        assert s.scalar(select(func.count()).select_from(Take)) == 0


def test_queue_chain_midinsert_rollback(engine, monkeypatch):
    owner, song, _, resolver = services(engine)
    from app.queue import chains

    real = chains.add_dependents

    def fail(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError("own injected midinsert failure")

    monkeypatch.setattr(chains, "add_dependents", fail)
    with pytest.raises(RuntimeError):
        create(engine, owner, song, resolver)
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(Job)) == 0
        assert s.scalar(select(func.count()).select_from(Take)) == 0


def test_queue_chain_declared_lyrics_version_exact_owned_text(engine):
    import hashlib

    from app.queue.chains import GenerationChains

    owner, song, catalog, resolver = services(engine)
    catalog.value["tasks"]["music.song"] = copy.deepcopy(
        catalog.value["tasks"]["music.instrumental"]
    )
    catalog.value["tasks"]["music.song"]["params_schema"]["properties"]["lyrics"] = {
        "type": "string"
    }
    text_value = "[Verse]\nLetra propia exacta"
    with Session(engine) as s:
        lyrics = LyricsVersion(
            owner_id=owner,
            song_id=song,
            text=text_value,
            source="manual",
            declaration="own",
            sha256=hashlib.sha256(text_value.encode()).hexdigest(),
        )
        s.add(lyrics)
        s.flush()
        lid = lyrics.id
        s.commit()
    body = request(2)
    body["params"]["lyrics"] = text_value
    service = GenerationChains(engine, owner, resolver)
    chain = asyncio.run(
        service.create(
            song,
            task="music.song",
            request=body,
            model_id="mock",
            lyrics_version_id=lid,
        )
    )
    body["params"]["lyrics"] = "mutación posterior del llamador"
    with Session(engine) as s:
        assert all(s.get(Take, tid).lyrics_version_id == lid for tid in chain.take_ids)
        assert (
            s.get(Job, chain.generation_job_id).request["params"]["lyrics"]
            == text_value
        )
    with pytest.raises(ValueError):
        asyncio.run(
            service.create(
                song,
                task="music.song",
                request=body,
                model_id="mock",
                lyrics_version_id=lid,
            )
        )


@pytest.mark.parametrize(
    "mutation",
    ["untyped_path", "bad_ref", "song_task", "cpu_task", "remote", "unsupported_mode"],
)
def test_queue_chain_request_is_stable_typed_and_gpu(engine, mutation):
    owner, song, catalog, resolver = services(engine)
    body = request()
    if mutation == "untyped_path":
        body["inputs"] = [{"role": "source", "path": "uploads/arbitrary.wav"}]
    if mutation == "bad_ref":
        body["inputs"] = [{"role": "source", "ref": {"type": "job", "id": new_id()}}]
    if mutation == "song_task":
        body["params"]["lyrics"] = "undeclared"
    if mutation == "cpu_task":
        catalog.value["tasks"]["music.instrumental"]["device"] = "cpu"
    if mutation == "remote":
        catalog.value["provider"] = {"type": "remote", "name": "synthetic"}
    if mutation == "unsupported_mode":
        body["mode"] = "unsupported"
    with pytest.raises(ValueError):
        create(engine, owner, song, resolver, request=body)
