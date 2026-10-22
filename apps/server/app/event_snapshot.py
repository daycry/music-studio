"""Preflight puro de DTOs ya autorizados, sin resolver pertenencia SQLite.

El caller futuro fija lectura WAL, registro y H bajo la barrera compartida y
comprueba autoridad DB/sesión. Ni owner cliente ni estos DTOs acreditan eso.
"""

from app.event_dtos import (
    MAX_SAFE_INTEGER,
    JobStateDTO,
    SnapshotControlDTO,
    encode_snapshot_control,
)
from app.sse import parse_cursor

_ACTIVE = frozenset({"queued", "blocked", "running", "interrupted"})


def _jobs(values, limit):
    if type(values) not in (list, tuple) or len(values) > 1064:
        raise ValueError("SNAPSHOT_LIMIT")
    unique = {}
    for value in values:
        if type(value) is not JobStateDTO:
            raise ValueError("INVALID_SNAPSHOT_JOB")
        # No confiar model_construct/model_copy ni instancias mutadas.
        value = JobStateDTO.model_validate(value.model_dump())
        previous = unique.get(value.job_id)
        if previous is not None and previous != value:
            raise ValueError("CONFLICTING_SNAPSHOT_JOB")
        unique[value.job_id] = value
    if len(unique) > limit:
        raise ValueError("SNAPSHOT_LIMIT")
    return unique


def build_snapshot(*, active, known, epoch, high_water, ts, snapshot_id, reason):
    """Retorna todos los frames o lanza antes de retornar ningún frame.

    Cota por máximos JobStateDTO: strings ASCII sin escapes, 3 ULID de26,
    2 etiquetas de64, status<=11, float<=24, claves/literales<=190:
    <=431 bytes/job (usamos512); cabecera/control<=1024. Por tanto64
    jobs caben en33792 bytes, incluso con H de16 dígitos, dentro de65536.
    Esta cota y su prueba deben revisarse si cambian los máximos del DTO.
    """
    if (
        type(high_water) is not int
        or not 1 <= high_water <= MAX_SAFE_INTEGER
        or type(epoch) is not str
        or len(epoch) != 32
    ):
        raise ValueError("INVALID_CURSOR")
    cursor = parse_cursor(f"{epoch}:{high_water}").wire
    active_jobs = _jobs(active, 1000)
    known_jobs = _jobs(known, 64)
    if any(value.status not in _ACTIVE for value in active_jobs.values()):
        raise ValueError("INVALID_ACTIVE_SNAPSHOT_JOB")
    for identity, value in known_jobs.items():
        if identity in active_jobs:
            if value != active_jobs[identity]:
                raise ValueError("CONFLICTING_SNAPSHOT_JOB")
        elif value.status in _ACTIVE:
            raise ValueError("INVALID_KNOWN_SNAPSHOT_JOB")
    terminal = {k: v for k, v in known_jobs.items() if k not in active_jobs}
    merged = active_jobs | terminal
    ordered = [merged[k] for k in sorted(merged)]
    chunks = [ordered[i : i + 64] for i in range(0, len(ordered), 64)]
    common = {"status": "snapshot", "snapshot_id": snapshot_id}
    controls = [
        dict(
            common,
            phase="begin",
            reason=reason,
            active_count=len(active_jobs),
            known_count=len(terminal),
            chunk_count=len(chunks),
        )
    ]
    controls.extend(
        dict(common, phase="chunk", index=i, jobs=[job.model_dump() for job in chunk])
        for i, chunk in enumerate(chunks)
    )
    controls.append(dict(common, phase="end", chunk_count=len(chunks), cursor=cursor))
    # Validar todos los DTOs antes de cualquier codificación/salida.
    dtos = [
        SnapshotControlDTO.model_validate(
            {"id": high_water, "type": "system.status", "ts": ts, "data": control}
        )
        for control in controls
    ]
    return tuple(encode_snapshot_control(dto) for dto in dtos)
