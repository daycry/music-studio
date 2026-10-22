"""Cadena lógica atómica; el worker CPU real pertenece a T05."""

import asyncio
from copy import deepcopy
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Job, JobDependency, LyricsVersion, Song, Take, User, new_id

from .admission import writer
from .inputs import ResolutionError


@dataclass(frozen=True)
class Chain:
    generation_job_id: str
    post_job_id: str
    take_ids: tuple[str, ...]
    beat_job_ids: tuple[str, ...]


def live_song(session, owner_id, song_id):
    user, song = session.get(User, owner_id), session.get(Song, song_id)
    if not (
        user
        and user.name == "local"
        and not user.deleted_at
        and song
        and song.owner_id == owner_id
        and not song.deleted_at
        and not song.is_dependency_only
    ):
        raise ResolutionError("Owned local live song required")
    return song


def validate_lyrics(session, job, lyrics_version_id):
    lyrics = (
        session.get(LyricsVersion, lyrics_version_id) if lyrics_version_id else None
    )
    if job.task == "music.song":
        if not (
            lyrics
            and lyrics.owner_id == job.owner_id
            and lyrics.song_id == job.song_id
            and not lyrics.deleted_at
            and lyrics.declaration in {"own", "assistant", "public_domain", "licensed"}
            and job.request.get("params", {}).get("lyrics") == lyrics.text
        ):
            raise ResolutionError("Owned declared lyrics version required")
    elif lyrics_version_id is not None or job.request.get("params", {}).get("lyrics"):
        raise ResolutionError("Instrumental cannot bind lyrics")


def validate_request(job):
    body = job.request
    if job.task not in {"music.song", "music.instrumental"} or not isinstance(
        body, dict
    ):
        raise ResolutionError("Generation task required")
    seed, count = body.get("seed"), body.get("n_outputs", 1)
    # Las semillas de variante deben caber en el rango unsigned de 64 bits.
    if (
        type(seed) is not int
        or type(count) is not int
        or not 1 <= count <= 64
        or seed < 0
        or seed + count - 1 > 2**64 - 1
    ):
        raise ResolutionError("Variant seed range overflow or output count invalid")
    inputs = body.get("inputs", [])
    if not isinstance(inputs, list) or any(
        not isinstance(i, dict)
        or set(i) != {"ref", "role"}
        or not isinstance(i["ref"], dict)
        or set(i["ref"]) != {"type", "id"}
        or i["ref"]["type"] not in {"upload", "asset", "take"}
        for i in inputs
    ):
        raise ResolutionError("Stable owned input references required")
    return count, seed


def add_dependents(session, generation, takes):
    """Índices originales, incluso si el retry sólo enlaza un subconjunto."""
    post = Job(
        id=new_id(),
        owner_id=generation.owner_id,
        song_id=generation.song_id,
        task="post.audio",
        lane="cpu",
        priority=generation.priority,
        status="blocked",
        request={
            "inputs": [
                {
                    "role": "source",
                    "ref": {"type": "job", "id": generation.id},
                    "output_index": take.variant_index,
                }
                for take in takes
            ]
        },
    )
    session.add(post)
    session.flush()
    session.add(
        JobDependency(
            owner_id=generation.owner_id,
            job_id=post.id,
            depends_on_job_id=generation.id,
        )
    )
    beat_ids = []
    for take in takes:
        beat = Job(
            id=new_id(),
            owner_id=generation.owner_id,
            song_id=generation.song_id,
            task="audio.beats",
            lane="cpu",
            priority=generation.priority,
            status="blocked",
            request={
                "params": {},
                "inputs": [{"role": "master", "ref": {"type": "take", "id": take.id}}],
            },
        )
        session.add(beat)
        session.flush()
        session.add(
            JobDependency(
                owner_id=generation.owner_id, job_id=beat.id, depends_on_job_id=post.id
            )
        )
        beat_ids.append(beat.id)
    session.flush()
    return Chain(generation.id, post.id, tuple(t.id for t in takes), tuple(beat_ids))


class GenerationChains:
    def __init__(self, engine, owner_id, resolver):
        self.engine, self.owner_id, self.resolver = engine, owner_id, resolver

    async def create(self, song_id, *, task, request, model_id, lyrics_version_id=None):
        job = Job(
            id=new_id(),
            owner_id=self.owner_id,
            song_id=song_id,
            task=task,
            lane="gpu",
            request=deepcopy(request),
            model_id=model_id,
            status="queued",
            priority="normal",
            attempt=0,
            max_attempts=3,
        )
        count, seed = validate_request(job)
        await asyncio.to_thread(self._validate, job, lyrics_version_id)
        resolved = await self.resolver.resolve(job, engine=self.engine)
        if resolved.lane != "gpu" and not (
            resolved.lane == "cpu" and resolved.engine_id == "mock"
        ):
            raise ResolutionError("Generation must be GPU task")
        # El engine-mock es la única excepción controlada: permite ejercitar
        # la cadena completa y su recuperación en el despliegue CPU de M1.
        # Ningún engine real puede convertir una tarea musical en carril CPU.
        job.lane = resolved.lane
        # Capturar el modelo elegido; el retry conserva el original.
        job.model_id = resolved.model_id
        job.engine_id = resolved.engine_id
        _, models = await self.resolver._catalog(resolved.backend)
        model = next(m for m in models if m.id == resolved.model_id)
        return await asyncio.to_thread(
            self._create, job, lyrics_version_id, model, count, seed
        )

    def _validate(self, job, lyrics_version_id):
        with Session(self.engine) as session:
            live_song(session, self.owner_id, job.song_id)
            validate_lyrics(session, job, lyrics_version_id)

    def _create(self, job, lyrics_version_id, model, count, seed):
        with Session(self.engine) as session, session.begin():
            writer(session)
            live_song(session, self.owner_id, job.song_id)
            validate_lyrics(session, job, lyrics_version_id)
            session.add(job)
            session.flush()
            batch = new_id()
            takes = []
            for index in range(count):
                tid = new_id()
                take = Take(
                    id=tid,
                    owner_id=self.owner_id,
                    song_id=job.song_id,
                    job_id=job.id,
                    lyrics_version_id=lyrics_version_id,
                    status="queued",
                    batch_id=batch,
                    variant_index=index,
                    root_id=tid,
                    derivation="original",
                    task=job.task,
                    model_id=model.id,
                    model_version=model.version,
                    seed=seed + index,
                    params=deepcopy(job.request.get("params", {})),
                    commercial_use=model.commercial_use,
                )
                session.add(take)
                takes.append(take)
            session.flush()
            return add_dependents(session, job, takes)
