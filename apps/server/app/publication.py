"""Barrera síncrona de participantes explícitos; no coordina writers por sí sola.

Orden obligatorio: coordinator -> writer/transacción SQLite -> bus. El callback
debe construir el batch antes del commit y retornar sólo después de confirmarlo.
No admite awaits ni trabajo de ficheros, modelos, entradas o red bajo la barrera.
El runtime y los otros escritores todavía deben compartir esta misma instancia.
"""

import math
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from types import TracebackType
from typing import Any, Protocol

MAX_PUBLICATIONS = 1064

_ROLLBACK_SEAL = object()


@dataclass(frozen=True, slots=True)
class _ConfirmedRollback:
    """Evidencia interna; sólo la integración transaccional puede emitirla."""

    primary: BaseException
    traceback: TracebackType | None
    _seal: object


def _confirmed_rollback(primary: BaseException, traceback: TracebackType | None):
    return _ConfirmedRollback(primary, traceback, _ROLLBACK_SEAL)


class PublicationBus(Protocol):
    def publish_confirmed(self, envelope: Any) -> bool: ...

    def mark_gap(self) -> None: ...


class PublicationTimeout(TimeoutError):
    """No se adquirió la barrera dentro del plazo público finito."""


@dataclass(frozen=True)
class CommitPublication:
    value: object
    publications: tuple
    invalidate: bool = False

    def __post_init__(self):
        if (
            type(self.publications) is not tuple
            or len(self.publications) > MAX_PUBLICATIONS
            or type(self.invalidate) is not bool
        ):
            raise ValueError("INVALID_PUBLICATION_BATCH")


@dataclass(frozen=True)
class PublicationOutcome:
    """published confirma el batch solicitado; vacío no afirma eventos emitidos.

    confirmed_count cuenta aceptaciones reales, también si luego falla el batch.
    Una invalidación deliberada sin eventos sólo confirma esa invalidación.
    """

    value: object
    published: bool
    publication_error: Exception | None = None
    gap_error: Exception | None = None
    confirmed_count: int = 0


class PublicationCoordinator:
    def __init__(self, acquisition_timeout=2):
        if (
            type(acquisition_timeout) not in (int, float)
            or not math.isfinite(acquisition_timeout)
            or not 0 < acquisition_timeout <= 2
        ):
            raise ValueError("INVALID_PUBLICATION_DEADLINE")
        self.acquisition_timeout = acquisition_timeout
        self._lock = RLock()

    @contextmanager
    def barrier(self):
        deadline = monotonic() + self.acquisition_timeout
        if not self._lock.acquire(timeout=max(0, deadline - monotonic())):
            raise PublicationTimeout("PUBLICATION_BARRIER_TIMEOUT")
        try:
            yield
        finally:
            self._lock.release()

    def commit_and_publish(
        self,
        commit: Callable[[], CommitPublication | _ConfirmedRollback],
        bus: PublicationBus,
    ) -> PublicationOutcome:
        """Commit incierto propaga el error; publish fallido conserva el valor.

        El error de publicación queda disponible para diagnóstico del caller;
        nunca dispara rollback, resubmission ni un terminal engine inventado.
        La adquisición fallida no ejecuta el callback ni toca el epoch.
        """
        with self.barrier():
            try:
                batch = commit()
            except BaseException as primary:
                try:
                    bus.mark_gap()
                except BaseException as secondary:  # noqa: BLE001 -- primario intacto
                    errors = getattr(primary, "_publication_secondary_errors", ())
                    primary._publication_secondary_errors = (
                        *errors,
                        ("mark_gap", secondary),
                    )
                    primary.add_note(
                        "Secondary mark_gap failure after commit uncertainty"
                    )
                raise
            # Fuera del catch: este rechazo conserva el feed y el error original.
            if type(batch) is _ConfirmedRollback and batch._seal is _ROLLBACK_SEAL:
                raise batch.primary.with_traceback(batch.traceback) from None
            # Un callback defectuoso no puede convertirse en éxito durable.
            if type(batch) is not CommitPublication:
                primary = TypeError("INVALID_COMMIT_RESULT")
                try:
                    bus.mark_gap()
                except BaseException:  # noqa: BLE001 -- resultado incierto
                    primary.add_note(
                        "Secondary mark_gap failure after invalid commit result"
                    )
                raise primary
            confirmed_count = 0
            try:
                if batch.invalidate:
                    bus.mark_gap()
                for envelope in batch.publications:
                    if bus.publish_confirmed(envelope) is not True:
                        raise RuntimeError("PUBLICATION_NOT_CONFIRMED")
                    confirmed_count += 1
            except BaseException as primary:  # resultado durable, interrupción propaga
                secondary = None
                try:
                    bus.mark_gap()
                except BaseException as error:  # noqa: BLE001 -- retener secundario
                    secondary = error
                    primary.add_note(
                        "Secondary mark_gap failure after durable publication failure"
                    )
                if not isinstance(primary, Exception):
                    raise
                return PublicationOutcome(
                    batch.value, False, primary, secondary, confirmed_count
                )
            return PublicationOutcome(
                batch.value, True, confirmed_count=confirmed_count
            )
