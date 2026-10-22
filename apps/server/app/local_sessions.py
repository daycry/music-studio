"""Sesiones efímeras con owner fijo resuelto por el caller interno.

Sin DB, HTTP, persistencia ni resolución de User. La factoría de pruebas
inyecta tiempo/RNG para pruebas funcionales, nunca para rendimiento nativo.
"""

import math
import re
import secrets
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

if __package__:
    from .event_dtos import SessionCredentialDTO
else:  # pytest can import app modules as top-level files in the server image.
    from event_dtos import SessionCredentialDTO

_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", re.ASCII)
_TOKEN = re.compile(r"[A-Za-z0-9_-]{1,64}", re.ASCII)
_CODES = frozenset(
    {"SESSION_REQUIRED", "SERVICE_UNAVAILABLE", "SESSION_LIMIT", "FORBIDDEN_SCOPE"}
)
_LOCK_TIMEOUT_S = 2
_GENERATION_ATTEMPTS = 8


class SessionError(RuntimeError):
    """Código cerrado, sin eco, excepción de fuente aleatoria ni credencial."""

    def __init__(self, code: str):
        self.code = (
            code if type(code) is str and code in _CODES else "SERVICE_UNAVAILABLE"
        )
        super().__init__(self.code)


@dataclass(eq=False, repr=False)
class _Lease:
    binding: object = None
    revoked: bool = False


@dataclass(frozen=True, eq=False)
class SessionBinding:
    """Referencia interna; no wire DTO ni input de cliente."""

    owner_id: str
    issued_at: float
    expires_at: float
    _registry: object = field(repr=False)
    _epoch: object = field(repr=False)
    _lease: _Lease = field(repr=False)


@dataclass(frozen=True, repr=False)
class _Record:
    padded_token: str
    binding: SessionBinding


def _valid_token(value: object) -> bool:
    # Bounds antes de padding/codificación/asignación dependiente de la entrada.
    return (
        type(value) is str
        and 1 <= len(value) <= 64
        and value.isascii()
        and _TOKEN.fullmatch(value) is not None
    )


class LocalSessionRegistry:
    """Máximo32 sesiones, TTL absoluto28800s y mutaciones síncronas acotadas."""

    def __init__(self, owner_id: str | None):
        self._owner_id = (
            owner_id if type(owner_id) is str and _ULID.fullmatch(owner_id) else None
        )
        self._clock: Callable[[], float] = time.monotonic
        self._token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32)
        self._ttl_s = 28800
        self._capacity = 32
        self._epoch = object()
        self._lock = threading.Lock()
        self._records: list[_Record] = []
        self._closed = False
        self._broken = False
        self._last_time = 0.0

    @classmethod
    def _for_tests(
        cls,
        owner_id: str | None,
        *,
        clock: Callable[[], float],
        token_factory: Callable[[], str] | None = None,
        ttl_s: int = 28800,
        capacity: int = 32,
    ) -> "LocalSessionRegistry":
        """Inyección interna explícita, sólo pruebas deterministas funcionales."""
        if (
            type(ttl_s) is not int
            or not 1 <= ttl_s <= 28800
            or type(capacity) is not int
            or not 1 <= capacity <= 32
            or not callable(clock)
            or (token_factory is not None and not callable(token_factory))
        ):
            raise SessionError("SERVICE_UNAVAILABLE")
        registry = cls(owner_id)
        registry._clock = clock
        if token_factory is not None:
            registry._token_factory = token_factory
        registry._ttl_s = ttl_s
        registry._capacity = capacity
        return registry

    @contextmanager
    def _guard(self) -> Iterator[None]:
        if not self._lock.acquire(timeout=_LOCK_TIMEOUT_S):
            raise SessionError("SERVICE_UNAVAILABLE")
        try:
            yield
        finally:
            self._lock.release()

    def _available(self) -> None:
        if self._closed or self._broken or self._owner_id is None:
            raise SessionError("SERVICE_UNAVAILABLE")

    def _now(self) -> float:
        value = None
        try:
            raw = self._clock()
            if type(raw) in (int, float):
                value = float(raw)
        except Exception:  # noqa: BLE001 — sanitizar cualquier fallo de la fuente privada.
            # Fuera del except al lanzar: tampoco conservamos __context__ secreto.
            value = None
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value < self._last_time
            or not math.isfinite(value + self._ttl_s)
            or value + self._ttl_s <= value
        ):
            self._broken = True
            self._records.clear()
            raise SessionError("SERVICE_UNAVAILABLE")
        self._last_time = value
        return value

    def _purge(self, now: float) -> None:
        self._records = [
            record for record in self._records if record.binding.expires_at > now
        ]

    def _scan(self, padded: str) -> SessionBinding | None:
        found = None
        for record in self._records:
            if secrets.compare_digest(padded, record.padded_token):
                found = record.binding
        return found

    def issue(self, owner_id: str) -> SessionCredentialDTO:
        """El owner aportado debe coincidir con el fijado; no crea autoridad."""
        with self._guard():
            self._available()
            if type(owner_id) is not str or owner_id != self._owner_id:
                raise SessionError("FORBIDDEN_SCOPE")
            self._purge(self._now())
            if len(self._records) >= self._capacity:
                raise SessionError("SESSION_LIMIT")
            token = None
            for _ in range(_GENERATION_ATTEMPTS):
                candidate = None
                failed = False
                try:
                    candidate = self._token_factory()
                except Exception:  # noqa: BLE001 — nunca conservar detalles del RNG.
                    failed = True
                if failed:
                    break
                if (
                    _valid_token(candidate)
                    and self._scan(candidate.ljust(64, "=")) is None
                ):
                    token = candidate
                    break
            if token is None:
                raise SessionError("SERVICE_UNAVAILABLE")
            now = self._now()
            lease = _Lease()
            binding = SessionBinding(
                self._owner_id, now, now + self._ttl_s, self, self._epoch, lease
            )
            lease.binding = binding
            dto = SessionCredentialDTO(session_token=token, expires_in_s=self._ttl_s)
            self._records.append(_Record(token.ljust(64, "="), binding))
            return dto

    def validate(self, raw_header: str) -> SessionBinding:
        with self._guard():
            self._available()
            if not _valid_token(raw_header):
                raise SessionError("SESSION_REQUIRED")
            self._purge(self._now())
            binding = self._scan(raw_header.ljust(64, "="))
            if binding is None:
                raise SessionError("SESSION_REQUIRED")
            return binding

    def _authentic_binding(self, binding: object) -> bool:
        return (
            type(binding) is SessionBinding
            and binding._registry is self
            and binding._epoch is self._epoch
            and binding.owner_id == self._owner_id
            and type(binding._lease) is _Lease
            and binding._lease.binding is binding
        )

    def revalidate(self, binding: SessionBinding) -> float:
        """Revalida y devuelve deadline absoluto para una futura espera idle."""
        with self._guard():
            if self._closed:
                raise SessionError("SESSION_REQUIRED")
            self._available()
            self._purge(self._now())
            if (
                not self._authentic_binding(binding)
                or binding._lease.revoked
                or not any(record.binding is binding for record in self._records)
            ):
                raise SessionError("SESSION_REQUIRED")
            return binding.expires_at

    def revoke(self, binding: SessionBinding) -> None:
        """Idempotente sólo para referencia genuina de este registro/epoch."""
        with self._guard():
            if self._closed or not self._authentic_binding(binding):
                raise SessionError("SESSION_REQUIRED")
            self._available()
            self._purge(self._now())
            binding._lease.revoked = True
            self._records = [
                record for record in self._records if record.binding is not binding
            ]

    def close(self) -> None:
        with self._guard():
            self._closed = True
            self._epoch = object()
            self._records.clear()

    @property
    def active_count(self) -> int:
        with self._guard():
            if self._closed or self._owner_id is None:
                return 0
            self._available()
            self._purge(self._now())
            return len(self._records)
