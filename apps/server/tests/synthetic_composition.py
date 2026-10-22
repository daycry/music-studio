"""Recetas explícitas de fixtures; nunca aprendidas del catálogo o de su clase."""

from app.queue.synthetic_registry import SyntheticRegistry, TrustedSyntheticEntry
from app.worker.contracts import canonical_sha256
from engine_contract import ModelDescriptor

IMPLEMENTATION = {
    "name": "declared-python-fixture",
    "revision": "fixture-v1",
    "source_sha256": "a" * 64,
    "common_source_sha256": "b" * 64,
}


def declared_entries(backend, recipes, *, engine_id="mock", versions=("1", "2")):
    """Se invoca al construir la composición, antes de recibir /models."""
    return tuple(
        TrustedSyntheticEntry.from_descriptor(
            backend,
            ModelDescriptor.model_validate(recipe),
            recipe_id="fixture-" + canonical_sha256(recipe),
            scope="test",
            engine_id=engine_id,
            engine_version=version,
            implementation=IMPLEMENTATION,
        )
        for recipe in recipes
        for version in versions
    )


def composition(backends, declarations=None):
    entries = []
    for name, backend in backends.items():
        if declarations is None:
            entries.extend(backend.trusted_entries)
        else:
            recipes, engine_id = declarations[name]
            entries.extend(declared_entries(backend, recipes, engine_id=engine_id))
    return SyntheticRegistry(tuple(entries))


def capture(admission, claim, backend):
    """Preparación real antes de inyectar el escenario: ACK, health y CAS SQL."""
    import asyncio

    from app.queue.provenance import capture_before_send

    async def observe():
        if claim.request.mode != "cpu":
            await backend.load(claim.load_options)
        return capture_before_send(
            claim.selected_provenance,
            claim.request,
            claim.load_options,
            await backend.health(),
            require_loaded=claim.request.mode != "cpu",
        )

    value = asyncio.run(observe())
    if not admission.capture_provenance(claim, value, canonical_sha256(value)):
        raise AssertionError(
            "Fixture preparation did not capture its declared evidence"
        )
    if not admission.may_send(claim):
        raise AssertionError("Fixture preparation lacks durable send authority")


def http_runtime(database, settings):
    from app.queue.backends.http import HttpEngineBackend
    from app.queue.runtime import QueueRuntime
    from test_queue_resolver import descriptor

    backends = {name: HttpEngineBackend(settings, name) for name in settings.engines}
    registry = composition(
        backends, {name: ([descriptor()], "mock") for name in backends}
    )
    runtime = QueueRuntime(
        database, settings, backends=backends, synthetic_registry=registry
    )
    runtime.owned_clients = True
    return runtime


def chain_recipes():
    import copy

    from test_queue_resolver import descriptor

    base = descriptor()
    base["modes"].append({"id": "cpu", "vram_mb": 0, "notes": "synthetic"})
    base["tasks"]["audio.beats"]["inputs"] = [
        {"role": "master", "required": True, "media_types": ["audio/wav", "audio/flac"]}
    ]
    song = copy.deepcopy(base)
    song["tasks"]["music.song"] = copy.deepcopy(song["tasks"]["music.instrumental"])
    song["tasks"]["music.song"]["params_schema"]["properties"]["lyrics"] = {
        "type": "string"
    }
    many = copy.deepcopy(base)
    many["tasks"]["music.instrumental"]["limits"]["n_outputs"] = 64
    return [base, song, many]
