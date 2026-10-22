"""T-04 CA-1 en Linux real: un post interrumpido llega a ``ready`` tras reiniciar.

Se ejecuta en Docker (fixture ``actual`` con FFmpeg Linux fijado); en Windows se
salta con el motivo «requiere Linux real».
"""
# ruff: noqa: F811  (el fixture se importa de otro test)

from app import models
from app.publication import PublicationCoordinator
from app.worker.execution import CpuAudioService
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_worker_actual_execution import (  # noqa: F401  (fixture `actual`)
    EXECUTION,
    POST,
    SONG,
    TAKE,
    actual,
)


def _crash_after_prepare(actual):
    """Estado que deja un SIGKILL del server tras reservar y antes de publicar."""
    cpu, run = actual.service._prepare(actual.plan, EXECUTION)
    assert run is not None
    return cpu


def _restart(actual):
    service = CpuAudioService(
        actual.engine,
        actual.root,
        coordinator=PublicationCoordinator(),
        bus=actual.bus,
        ffmpeg=actual.service.ffmpeg,
    )
    assert service.reconcile_startup() == 1
    return service


def _assert_published(actual):
    with Session(actual.engine) as session:
        assert session.get(models.Take, TAKE).status == "ready"
        assert session.scalar(select(models.PublicationIntent)).state == "committed"
        cpu = session.get(models.CpuExecution, EXECUTION)
        assert (cpu.state, cpu.cleanup_state) == ("finished", "confirmed")
        assert session.get(models.Job, POST).status == "succeeded"
        roles = {
            a.role
            for a in session.scalars(
                select(models.Asset).where(models.Asset.subject_id == TAKE)
            )
        }
        assert roles == {"master", "listen", "peaks", "manifest"}
    final = actual.root / f"data/songs/{SONG}/takes/{TAKE}"
    assert (final / "manifest.json").is_file()
    assert not (final.parent / f".pending-{EXECUTION}").exists()


def test_interrupted_post_resumes_to_ready_on_the_same_execution(actual):
    _crash_after_prepare(actual)
    service = _restart(actual)
    assert service.resumable_jobs() == [POST]
    assert service.claim_resume(POST) == EXECUTION
    results = service.execute(actual.plan, execution_id=EXECUTION, resume=True)
    assert [r.status for r in results] == ["success"]
    _assert_published(actual)
    # el WAV crudo ya no lo necesita nadie
    winning = actual.plan.takes[0].authority.winning_attempt_id
    assert not (actual.root / "data/tmp" / winning).exists()


def test_resume_discards_a_half_written_stage_of_the_dead_child(actual):
    _crash_after_prepare(actual)
    stale = actual.root / f"data/songs/{SONG}/takes/.pending-{EXECUTION}/{TAKE}"
    stale.mkdir(parents=True)
    (stale / "master.flac").write_bytes(b"half written")
    service = _restart(actual)
    assert service.claim_resume(POST) == EXECUTION
    service.execute(actual.plan, execution_id=EXECUTION, resume=True)
    _assert_published(actual)
