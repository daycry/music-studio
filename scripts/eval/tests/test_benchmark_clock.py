"""Relojes y conversión local Windows con ABI falsa; sin sensores reales."""

from types import SimpleNamespace

import pytest


class Function:
    def __init__(self, operation):
        self.operation = operation

    def __call__(self, *args):
        return self.operation(*args)


def test_local_filetime_conversion_calls_native_api_and_keeps_100ns(
    harness_module, monkeypatch
):
    module = harness_module("benchmark_clock")
    convert = getattr(module, "local_filetime_to_utc", None)
    assert callable(convert), "Falta conversión nativa local→UTC durante adquisición"
    calls = []

    def native(local, utc):
        raw = (local._obj.dwHighDateTime << 32) | local._obj.dwLowDateTime
        calls.append(raw)
        normalized = raw - 198000000000  # CPU: UTC+05:30, no offset fijo de Madrid.
        utc._obj.dwLowDateTime = normalized & 0xFFFFFFFF
        utc._obj.dwHighDateTime = normalized >> 32
        return 1

    kernel = SimpleNamespace(LocalFileTimeToFileTime=Function(native))
    monkeypatch.setattr(module.ctypes, "windll", SimpleNamespace(kernel32=kernel))
    assert convert(134358246000088324) == 134358048000088324
    assert calls == [134358246000088324]
    kernel.LocalFileTimeToFileTime = Function(lambda *args: 0)
    with pytest.raises(ValueError, match="filetime_conversion_failed"):
        convert(134358246000088324)


def test_timezone_snapshot_uses_native_active_dst_and_fails_on_api_error(
    harness_module, monkeypatch
):
    module = harness_module("benchmark_clock")
    snapshot = getattr(module, "timezone_snapshot", None)
    assert callable(snapshot), "Falta zona y estado DST nativos de adquisición"

    def native(output):
        output._obj.Bias = -60
        output._obj.StandardBias = 0
        output._obj.DaylightBias = -60
        output._obj.StandardName = "CPU standard"
        output._obj.DaylightName = "CPU daylight"
        return 2

    kernel = SimpleNamespace(GetTimeZoneInformation=Function(native))
    monkeypatch.setattr(module.ctypes, "windll", SimpleNamespace(kernel32=kernel))
    assert snapshot() == {
        "id": 2,
        "bias_minutes": -60,
        "standard_bias_minutes": 0,
        "daylight_bias_minutes": -60,
        "standard_name": "CPU standard",
        "daylight_name": "CPU daylight",
        "standard_date": [0] * 8,
        "daylight_date": [0] * 8,
    }
    kernel.GetTimeZoneInformation = Function(lambda *args: 0xFFFFFFFF)
    with pytest.raises(ValueError, match="timezone_unavailable"):
        snapshot()


def test_utc_clock_fallback_is_explicit_on_non_windows(harness_module, monkeypatch):
    from datetime import datetime, timezone

    module = harness_module("benchmark_clock")
    monkeypatch.setattr(module.os, "name", "posix")
    result = datetime.fromisoformat(module.utc_now())
    assert result.tzinfo == timezone.utc


@pytest.mark.parametrize(
    "state,bias,standard_month,daylight_month,expected_minutes",
    [
        (0, 0, 0, 0, 0),
        (0, 30, 0, 0, -30),
        (1, 30, 0, 0, -30),
        (2, 30, 0, 0, -30),
        (1, 30, 10, 0, -90),
        (2, 30, 0, 3, 15),
        (1, 30, 0, 3, -30),
        (2, 30, 10, 0, -30),
    ],
)
def test_timezone_offset_ignores_seasonal_bias_without_its_transition_date(
    harness_module, state, bias, standard_month, daylight_month, expected_minutes
):
    zone = {
        "id": state,
        "bias_minutes": bias,
        "standard_bias_minutes": 60,
        "daylight_bias_minutes": -45,
        "standard_name": "CPU standard",
        "daylight_name": "CPU daylight",
        "standard_date": [0, standard_month, 0, 5, 2, 0, 0, 0]
        if standard_month
        else [0] * 8,
        "daylight_date": [0, daylight_month, 0, 5, 2, 0, 0, 0]
        if daylight_month
        else [0] * 8,
    }
    offset = harness_module("benchmark_clock").timezone_offset_ticks(zone)
    assert offset == expected_minutes * 60 * 10000000


def test_plan_already_seals_new_clock_source_and_rejects_change(
    harness_module, tmp_path, monkeypatch
):
    import json

    planner = harness_module("benchmark_plan")
    root = planner.ROOT
    source = root / "scripts/eval/benchmark_clock.py"
    fixtures = {}
    for duration in planner.DURATIONS:
        path = tmp_path / f"{duration}.json"
        path.write_text(
            json.dumps(
                {
                    "task": "music.song",
                    "authorship": {"declared": True, "basis": "original"},
                    "params": {
                        "lyrics": "CPU",
                        "style": "CPU",
                        "language": "es",
                        "duration_s": duration,
                    },
                }
            )
        )
        fixtures[str(duration)] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": planner.file_hash(path),
        }
    plan = planner.build_plan(
        {"fixtures_by_duration": fixtures},
        root=root,
        image_id="sha256:CPU",
        prerequisites_sha256=None,
        observation_method="wddm_auto_v1",
    )
    assert plan["source_hashes"][
        "scripts/eval/benchmark_clock.py"
    ] == planner.file_hash(source)
    planner.verify_plan(plan, root)
    original_hash = planner.file_hash
    monkeypatch.setattr(
        planner,
        "file_hash",
        lambda path: "a" * 64 if path == source else original_hash(path),
    )
    with pytest.raises(ValueError, match="source_changed"):
        planner.verify_plan(plan, root)
