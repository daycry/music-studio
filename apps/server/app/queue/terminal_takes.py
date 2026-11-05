"""Terminales definitivos de generación; nunca alterar publicaciones existentes."""

from sqlalchemy import and_, or_, select, update

from app.models import Asset, PublicationIntent, Take


def retry_mode(attempt):
    """Política del intento congelado; la falta temporal de VRAM no la cambia."""
    if attempt.terminal.data["code"] != "VRAM_EXCEEDED":
        return attempt.mode
    if attempt.mode == "offload":
        return None
    return "offload"


def automatic_retry_pending(job, attempt):
    """El backoff no convierte un fallo retryable en un terminal definitivo."""
    return bool(
        job.status == "failed"
        and not job.cancel_requested_at
        and 1 <= job.attempt < job.max_attempts <= 3
        and attempt is not None
        and not attempt.deleted_at
        and attempt.owner_id == job.owner_id
        and attempt.engine_id == job.engine_id
        and attempt.ordinal == job.attempt
        and attempt.status == "failed"
        and attempt.terminal is not None
        and attempt.terminal.type == "error"
        and attempt.terminal.data["retryable"] is True
        and retry_mode(attempt) is not None
    )


def terminalize_placeholders(session, job, stamp, attempt=None):
    """Caller owns the writer and has authenticated the live local generation."""
    if (
        job.task not in {"music.song", "music.instrumental"}
        or job.status not in {"failed", "cancelled"}
        or automatic_retry_pending(job, attempt)
    ):
        return
    body = job.request
    count, seed = body.get("n_outputs", 1), body.get("seed")
    if type(count) is not int or not 1 <= count <= 64 or type(seed) is not int:
        return
    session.execute(
        update(Take)
        .where(
            Take.job_id == job.id,
            Take.owner_id == job.owner_id,
            Take.song_id == job.song_id,
            Take.deleted_at.is_(None),
            Take.status.in_(["queued", "running"]),
            Take.task == job.task,
            Take.model_id == job.model_id,
            Take.params == body.get("params", {}),
            # Seed usa TEXT decimal: no sumar en SQLite (desborda int64).
            or_(
                *(
                    and_(Take.variant_index == index, Take.seed == seed + index)
                    for index in range(count)
                )
            ),
            ~select(PublicationIntent.id)
            .where(PublicationIntent.take_id == Take.id)
            .exists(),
            ~select(Asset.id)
            .where(Asset.subject_type == "take", Asset.subject_id == Take.id)
            .exists(),
        )
        .values(
            status=job.status,
            error_code=job.error_code if job.status == "failed" else None,
            updated_at=stamp,
        )
    )
