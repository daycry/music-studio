"""Resolver por capacidades: fixtures sintéticas explícitas, nunca M0."""

import asyncio
import importlib.util
import os
from pathlib import Path

import pytest
from app.models import Job, new_id
from engine_contract import Health, ModelDescriptor


def descriptor():
    return {
        "id": "mock",
        "family": "mock",
        "version": "1",
        "revision": "synthetic",
        "license": "MIT",
        "commercial_use": True,
        "training_data": "synthetic tests",
        "provider": {"type": "local"},
        "weights": [],
        "modes": [{"id": "bf16", "vram_mb": 1000, "notes": "synthetic"}],
        "tasks": {
            "music.instrumental": {
                "verified": True,
                "device": "gpu",
                "params_schema": {
                    "type": "object",
                    "properties": {
                        "style": {"type": "string"},
                        "duration_s": {"type": "number", "minimum": 1, "maximum": 60},
                    },
                    "additionalProperties": False,
                },
                "limits": {"n_outputs": 4},
            },
            "audio.beats": {
                "verified": True,
                "device": "cpu",
                "params_schema": {"type": "object", "additionalProperties": False},
            },
        },
    }


class Catalog:
    origin = "http://engine-mock:8199"

    def __init__(
        self, *, origin="http://engine-mock:8199", engine_id="mock", recipes=None
    ):
        from synthetic_composition import composition, declared_entries

        self.origin = origin
        self.trusted_entries = declared_entries(
            self, recipes or [descriptor()], engine_id=engine_id
        )
        self.synthetic_registry = composition({"declared": self})
        self.value = descriptor()
        self.calls = 0
        self.version = "1"
        self.down = False
        self.loaded = None

    async def load(self, request):
        from engine_contract import LoadedModel

        self.loaded = LoadedModel(model_id=request.model_id, mode=request.mode)
        return self.loaded

    async def health(self):
        if self.down:
            raise OSError("synthetic down")
        return Health(
            engine_id="mock",
            engine_version=self.version,
            image_digest="unknown",
            state="idle",
            loaded=self.loaded,
            gpu={"total_mb": 12000, "free_mb": 10000, "cap_mb": 9488},
        )

    async def models(self):
        self.calls += 1
        return [ModelDescriptor.model_validate(self.value)]


def resolver(catalog, **options):
    assert importlib.util.find_spec("app.queue") is not None, (
        "Falta resolver de capacidades"
    )
    from app.queue.resolver import Resolver

    return Resolver(
        {"mock": catalog},
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        synthetic_registry=catalog.synthetic_registry,
        **options,
    )


def job(**kwargs):
    values = {
        "id": new_id(),
        "owner_id": new_id(),
        "song_id": new_id(),
        "task": "music.instrumental",
        "lane": "gpu",
        "request": {
            "params": {"style": "  canción [Verse]  ", "duration_s": 30},
            "seed": 17,
            "mode": "bf16",
            "n_outputs": 2,
            "timeout_s": 60,
        },
    }
    values.update(kwargs)
    return Job(**values)


def test_queue_resolver_frozen_request_exact_text_cpu_lane():
    async def run():
        r = resolver(Catalog())
        original = job()
        result = await r.resolve(original)
        request, load = result.freeze(new_id())
        assert request.params == original.request["params"]
        assert request.seed == 17 and request.n_outputs == 2
        assert (
            request.output_dir == "tmp/" + request.job_id
            and request.job_id != original.id
        )
        assert load.model_id == request.model_id == "mock"
        cpu = await r.resolve(
            job(
                task="audio.beats",
                lane="gpu",
                request={"params": {}, "mode": "bf16", "seed": 3, "timeout_s": 60},
            )
        )
        assert cpu.lane == "cpu"

    asyncio.run(run())


@pytest.mark.parametrize(
    "change",
    [
        "unverified",
        "noncommercial",
        "external",
        "mode",
        "params",
        "limits",
        "missinginput",
        "unverifiedfeature",
        "token",
        "rawinput",
        "remote_ref",
    ],
)
def test_queue_resolver_invalid_before_reservation(change):
    async def run():
        c = Catalog()
        j = job()
        if change == "unverified":
            c.value["tasks"][j.task]["verified"] = False
        if change == "noncommercial":
            c.value["commercial_use"] = False
        if change == "external":
            c.value["provider"]["type"] = "external"
        if change == "mode":
            j.request["mode"] = "imaginary"
        if change == "params":
            j.request["params"]["duration_s"] = "30"
        if change == "limits":
            j.request["n_outputs"] = 5
        if change == "missinginput":
            c.value["tasks"][j.task]["inputs"] = [
                {"role": "master", "required": True, "media_types": ["audio/flac"]}
            ]
        if change == "unverifiedfeature":
            j.request["required_features"] = ["stems"]
        if change == "token":
            j.request["params"]["token"] = "forbidden"
        if change == "rawinput":
            j.request["inputs"] = [
                {
                    "role": "master",
                    "path": "arbitrary.wav",
                    "sha256": "a" * 64,
                    "media_type": "audio/wav",
                }
            ]
        if change == "remote_ref":
            c.value["tasks"][j.task]["params_schema"] = {
                "$ref": "https://remote.invalid/schema"
            }
        r = resolver(c)
        from app.queue.resolver import ResolutionError

        with pytest.raises(ResolutionError):
            await r.resolve(j)

    asyncio.run(run())


def test_queue_resolver_cache_ttl_identity_down():
    async def run():
        c = Catalog()
        now = [0.0]
        r = resolver(c, ttl_s=5, clock=lambda: now[0])
        await r.resolve(job())
        await r.resolve(job())
        assert c.calls == 1
        now[0] = 6
        await r.resolve(job())
        assert c.calls == 2
        c.version = "2"
        await r.resolve(job())
        assert c.calls == 3
        c.down = True
        from app.queue.resolver import ResolutionError

        with pytest.raises(ResolutionError):
            await r.resolve(job())
        c.down = False
        await r.resolve(job())
        assert c.calls == 4

    asyncio.run(run())


@pytest.mark.parametrize("case", ["implicit_feature", "range_limit", "cpu_default"])
def test_queue_resolver_native_policy(case):
    async def run():
        c = Catalog()
        j = job()
        r = resolver(c)
        if case == "cpu_default":
            from engine_mock import descriptor as native_descriptor

            c.value = native_descriptor().model_dump(mode="json")
            # Este caso comprueba únicamente la selección CPU por
            # defecto; el contrato real de audio.beats exige un master y
            # se valida en los tests de inputs/engine.
            c.value["tasks"]["audio.beats"]["inputs"] = []
            j.task = "audio.beats"
            j.request = {"params": {}, "seed": 1, "timeout_s": 30}
            value = await r.resolve(j)
            assert value.mode == "cpu" and value.lane == "cpu"
        else:
            if case == "implicit_feature":
                c.value["tasks"][j.task]["features"] = {"style": {"verified": False}}
            else:
                c.value["tasks"][j.task]["limits"] = {"duration_s": [1, 20]}
            from app.queue.resolver import ResolutionError

            with pytest.raises(ResolutionError):
                await r.resolve(j)

    asyncio.run(run())


def test_queue_resolver_null_seed_freezes_concrete_seed():
    async def run():
        j = job()
        j.request["seed"] = None
        value = await resolver(Catalog()).resolve(j)
        request, _ = value.freeze(j.id)
        assert type(request.seed) is int and request.seed >= 0
        assert value.freeze(j.id)[0].seed == request.seed

    asyncio.run(run())


def test_queue_resolver_explicit_healthy_after_unavailable():
    from app.queue.resolver import ResolutionError, Resolver

    bad = Catalog()
    bad.down = True
    good = Catalog(origin="http://engine-healthy:8199")
    from synthetic_composition import composition

    r = Resolver(
        {"bad": bad, "good": good},
        data_dir=Path(os.environ["STUDIO_QUEUE_TEST_ROOT"]),
        synthetic_registry=composition({"bad": bad, "good": good}),
    )

    async def run():
        result = await r.resolve(job(engine_id="mock", model_id="mock"))
        assert result.freeze(new_id())[0].model_id == "mock"
        with pytest.raises(ResolutionError):
            await r.resolve(job(engine_id="absent", model_id="mock"))
        with pytest.raises(ResolutionError):
            await r.resolve(job(engine_id="mock", model_id="absent"))

    asyncio.run(run())
