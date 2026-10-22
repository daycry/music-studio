"""Presupuesto puro: reloj real, sin procesos ni mocks de tiempo."""

import math
import time

import pytest
from benchmark_startup import StartupBudget


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.5, "123", None])
def test_absolute_deadline_requires_positive_integer(value):
    with pytest.raises(ValueError, match="startup_deadline_invalid"):
        StartupBudget(value)


@pytest.mark.parametrize(
    "value", [True, False, 0, -1, math.nan, math.inf, -math.inf, "5", None]
)
def test_legacy_timeout_requires_finite_positive_number(value):
    with pytest.raises(ValueError, match="startup_timeout_invalid"):
        StartupBudget.from_timeout(value)


def test_exhausted_budget_cannot_be_renewed():
    deadline = time.perf_counter_ns() - 1
    budget = StartupBudget(deadline)
    assert budget.deadline_ns == deadline
    assert budget.remaining_ns() == 0
    assert budget.remaining_s() == 0
    with pytest.raises(TimeoutError, match="startup_deadline_expired"):
        budget.check()


def test_shared_absolute_deadline_caps_large_legacy_default():
    deadline = time.perf_counter_ns() + 1_000_000_000
    first = StartupBudget.from_timeout(5, deadline_ns=deadline)
    second = StartupBudget.from_timeout(120, deadline_ns=first.deadline_ns)
    assert first.deadline_ns == second.deadline_ns == deadline
    initial_remaining = first.remaining_ns()
    assert 0 < second.remaining_ns() <= initial_remaining <= 1_000_000_000
    first.check()
    second.check()


def test_default_is_converted_once_and_remains_absolute():
    before = time.perf_counter_ns()
    budget = StartupBudget.from_timeout(5)
    after = time.perf_counter_ns()
    assert before + 5_000_000_000 <= budget.deadline_ns <= after + 5_000_000_000
    original = budget.deadline_ns
    assert budget.remaining_s() > 0
    budget.check()
    assert budget.deadline_ns == original


def test_supplied_deadline_does_not_bypass_timeout_validation():
    with pytest.raises(ValueError, match="startup_timeout_invalid"):
        StartupBudget.from_timeout(
            float("nan"), deadline_ns=time.perf_counter_ns() + 1000
        )
