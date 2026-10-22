"""Pruebas funcionales; los ULID y relojes sintéticos no resuelven usuarios DB."""

import dataclasses
import re
import threading

import pytest
from app.local_sessions import LocalSessionRegistry, SessionError

OWNER = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
OTHER = "01ARZ3NDEKTSV4RRFFQ69G5FAW"


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


def registry(clock=None, tokens=None, **kwargs):
    source = iter(tokens) if tokens is not None else None
    return LocalSessionRegistry._for_tests(
        OWNER,
        clock=clock or Clock(),
        token_factory=(lambda: next(source)) if source is not None else None,
        **kwargs,
    )


def rejects(code, function, *args, **kwargs):
    with pytest.raises(SessionError) as caught:
        function(*args, **kwargs)
    assert caught.value.code == code
    assert str(caught.value) == code
    assert repr(caught.value) == f"SessionError('{code}')"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_real_defaults_and_fixed_owner():
    r = LocalSessionRegistry(OWNER)
    dto = r.issue(OWNER)
    assert set(dto.model_dump()) == {"session_token", "expires_in_s"}
    assert dto.expires_in_s == 28800
    assert re.fullmatch(r"[A-Za-z0-9_-]{43}", dto.session_token)
    binding = r.validate(dto.session_token)
    assert binding.owner_id == OWNER
    assert binding.expires_at == binding.issued_at + 28800
    assert r.revalidate(binding) == binding.expires_at
    assert dto.session_token not in repr(r) + repr(binding)
    rejects("FORBIDDEN_SCOPE", r.issue, OTHER)


@pytest.mark.parametrize("owner", [None, "local", OTHER + "X", 7, True])
def test_unavailable_identity(owner):
    r = LocalSessionRegistry(owner)
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)
    rejects("SERVICE_UNAVAILABLE", r.validate, "valid_token")


def test_absolute_expiry_and_purge_without_eviction():
    clock = Clock()
    r = registry(clock, capacity=1, ttl_s=5)
    token = r.issue(OWNER).session_token
    binding = r.validate(token)
    clock.now = 14
    assert r.validate(token) is binding
    rejects("SESSION_LIMIT", r.issue, OWNER)
    clock.now = 15
    rejects("SESSION_REQUIRED", r.validate, token)
    rejects("SESSION_REQUIRED", r.revalidate, binding)
    assert r.active_count == 0
    assert r.issue(OWNER).session_token != token


def test_expiry_idle_deadline_and_no_sliding():
    clock = Clock()
    r = registry(clock, ttl_s=5)
    binding = r.validate(r.issue(OWNER).session_token)
    clock.now = 14
    assert r.revalidate(binding) == 15
    clock.now = 15
    rejects("SESSION_REQUIRED", r.revalidate, binding)


def test_wrong_owner_cannot_issue():
    r = registry()
    rejects("FORBIDDEN_SCOPE", r.issue, OTHER)
    assert r.active_count == 0


def test_revocation_invalidates_and_is_idempotent():
    r = registry()
    token = r.issue(OWNER).session_token
    binding = r.validate(token)
    r.revoke(binding)
    r.revoke(binding)
    rejects("SESSION_REQUIRED", r.validate, token)
    assert r.active_count == 0


def test_close_invalidates_all():
    r = registry()
    binding = r.validate(r.issue(OWNER).session_token)
    r.close()
    rejects("SESSION_REQUIRED", r.revalidate, binding)
    assert r.active_count == 0


def test_revoke_close_restart_and_foreign_binding():
    r = registry()
    token = r.issue(OWNER).session_token
    binding = r.validate(token)
    foreign = registry()
    rejects("SESSION_REQUIRED", foreign.revalidate, binding)
    rejects("SESSION_REQUIRED", foreign.revoke, binding)
    rejects("SESSION_REQUIRED", foreign.validate, token)
    altered = dataclasses.replace(binding, owner_id=OTHER)
    rejects("SESSION_REQUIRED", r.revalidate, altered)
    rejects("SESSION_REQUIRED", r.revoke, altered)
    r.revoke(binding)
    r.revoke(binding)
    rejects("SESSION_REQUIRED", r.validate, token)
    rejects("SESSION_REQUIRED", r.revalidate, binding)
    live = r.validate(r.issue(OWNER).session_token)
    r.close()
    r.close()
    assert r.active_count == 0
    rejects("SESSION_REQUIRED", r.revalidate, live)
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)
    rejects("SERVICE_UNAVAILABLE", r.validate, token)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        12,
        True,
        b"abc",
        "",
        "a" * 65,
        "a\nb",
        "a\rb",
        "é",
        "a/b",
        "a=b",
        "a b",
        "\ud800",
    ],
)
def test_invalid_header_finite_and_private(raw):
    r = registry()
    r.issue(OWNER)
    rejects("SESSION_REQUIRED", r.validate, raw)
    assert r.active_count == 1


@pytest.mark.parametrize("bad", [None, b"abc", True, "", "é", "a\nb", "a/b", "x" * 65])
def test_invalid_rng_does_not_admit(bad):
    r = registry(tokens=[bad] * 8)
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)
    assert r.active_count == 0


def test_duplicate_rng_finite_no_overwrite():
    r = registry(tokens=["same_token"] * 9)
    dto = r.issue(OWNER)
    binding = r.validate(dto.session_token)
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)
    assert r.active_count == 1
    assert r.validate(dto.session_token) is binding


def test_rng_retry_and_private_exception():
    r = registry(tokens=["bad/token", "good_token"])
    assert r.issue(OWNER).session_token == "good_token"

    def fail():
        raise ValueError("private_rng_secret")

    r = LocalSessionRegistry._for_tests(OWNER, clock=Clock(), token_factory=fail)
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)


@pytest.mark.parametrize(
    "controls",
    [
        {"ttl_s": True},
        {"ttl_s": 0},
        {"ttl_s": float("nan")},
        {"ttl_s": float("inf")},
        {"ttl_s": 28801},
        {"capacity": True},
        {"capacity": 0},
        {"capacity": 33},
        {"capacity": 1.0},
    ],
)
def test_invalid_controls(controls):
    rejects("SERVICE_UNAVAILABLE", registry, **controls)


@pytest.mark.parametrize("now", [True, "10", float("nan"), float("inf"), -1, 10**400])
def test_invalid_clock(now):
    c = Clock()
    r = registry(c)
    binding = r.validate(r.issue(OWNER).session_token)
    c.now = now
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)
    rejects("SERVICE_UNAVAILABLE", r.revalidate, binding)


def test_clock_regression_fails_closed():
    c = Clock()
    r = registry(c)
    dto = r.issue(OWNER)
    c.now = 9
    rejects("SERVICE_UNAVAILABLE", r.validate, dto.session_token)


def test_clock_exception_does_not_keep_private_context():
    def fail():
        raise ValueError("private_clock_secret")

    r = LocalSessionRegistry._for_tests(OWNER, clock=fail)
    rejects("SERVICE_UNAVAILABLE", r.issue, OWNER)


def test_unknown_exception_code_is_closed():
    error = SessionError("private_secret")
    assert str(error) == "SERVICE_UNAVAILABLE"
    assert "private_secret" not in repr(error)


def test_constant_time_bounded_scan(monkeypatch):
    from app import local_sessions

    r = registry(tokens=[f"token_{i}" for i in range(3)])
    tokens = [r.issue(OWNER).session_token for _ in range(3)]
    original = local_sessions.secrets.compare_digest
    calls = []

    def compare(left, right):
        calls.append((len(left), len(right)))
        return original(left, right)

    monkeypatch.setattr(local_sessions.secrets, "compare_digest", compare)
    r.validate(tokens[0])
    assert calls == [(64, 64)] * 3
    calls.clear()
    rejects("SESSION_REQUIRED", r.validate, "absent")
    assert calls == [(64, 64)] * 3
    calls.clear()
    rejects("SESSION_REQUIRED", r.validate, "x" * 65)
    assert calls == []


def test_thread_capacity_and_revoke_race():
    r = LocalSessionRegistry(OWNER)
    barrier = threading.Barrier(41)
    lock = threading.Lock()
    issued, errors = [], []

    def issue():
        barrier.wait(timeout=10)
        try:
            dto = r.issue(OWNER)
            with lock:
                issued.append(dto.session_token)
        except SessionError as error:
            with lock:
                errors.append(error.code)

    threads = [threading.Thread(target=issue) for _ in range(40)]
    for thread in threads:
        thread.start()
    barrier.wait(timeout=10)
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert len(issued) == len(set(issued)) == r.active_count == 32
    assert errors == ["SESSION_LIMIT"] * 8
    binding = r.validate(issued[0])
    race = threading.Barrier(3)
    outcomes = []

    def validate():
        race.wait(timeout=10)
        try:
            r.revalidate(binding)
            outcomes.append("valid")
        except SessionError as error:
            outcomes.append(error.code)

    def revoke():
        race.wait(timeout=10)
        r.revoke(binding)

    threads = [threading.Thread(target=validate), threading.Thread(target=revoke)]
    for thread in threads:
        thread.start()
    race.wait(timeout=10)
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert outcomes in [["valid"], ["SESSION_REQUIRED"]]
    rejects("SESSION_REQUIRED", r.revalidate, binding)
    assert r.active_count == 31
