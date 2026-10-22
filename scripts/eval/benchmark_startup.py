"""Plazo absoluto de arranque: sólo cálculo, sin IO ni actores implícitos.

El caller convierte su default una vez al entrar y transmite ``deadline_ns``.
El reloj del SO y su planificación no proporcionan una garantía hard real-time.
"""

import math
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class StartupBudget:
    deadline_ns: int

    def __post_init__(self):
        if type(self.deadline_ns) is not int or self.deadline_ns <= 0:
            raise ValueError("startup_deadline_invalid")

    @classmethod
    def from_timeout(cls, timeout_s=5, *, deadline_ns=None):
        entered_ns = time.perf_counter_ns() if deadline_ns is None else None
        if (
            type(timeout_s) not in (int, float)
            or timeout_s <= 0
            or (type(timeout_s) is float and not math.isfinite(timeout_s))
        ):
            raise ValueError("startup_timeout_invalid")
        if deadline_ns is None:
            # Integer arithmetic also avoids overflow for finite large floats.
            numerator, denominator = timeout_s.as_integer_ratio()
            deadline_ns = entered_ns + numerator * 1_000_000_000 // denominator
        return cls(deadline_ns)

    def remaining_ns(self):
        return max(0, self.deadline_ns - time.perf_counter_ns())

    def remaining_s(self):
        return self.remaining_ns() / 1e9

    def check(self):
        if self.remaining_ns() == 0:
            raise TimeoutError("startup_deadline_expired")
