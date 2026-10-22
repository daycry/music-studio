"""Contadores agregados con LUID exacto, ruido baseline y browser visible."""

import pytest


def test_windows_luid_mapping_rejects_ambiguous_5070(harness_module):
    observer = harness_module("benchmark_observers")
    assert callable(getattr(observer, "map_5070", None)), "Falta mapping DXGI exacto"
    gpu = {
        "description": "NVIDIA GeForce RTX 5070",
        "vendor_id": 0x10DE,
        "luid_high": 0,
        "luid_low": 0x1234,
    }
    instances = [
        "luid_0x00000000_0x00001234_phys_0",
        "luid_0x00000000_0x00005678_phys_0",
    ]
    assert (
        observer.map_5070([gpu], instances, "NVIDIA GeForce RTX 5070") == instances[0]
    )
    with pytest.raises(ValueError):
        observer.map_5070([gpu, gpu], instances, "NVIDIA GeForce RTX 5070")
    with pytest.raises(ValueError):
        observer.map_5070([gpu], instances[1:], "NVIDIA GeForce RTX 5070")


def test_shared_gpu_requires_two_samples_and_missing_stays_unknown(harness_module):
    observer = harness_module("benchmark_observers")
    assert callable(getattr(observer, "shared_assessment", None)), (
        "Falta observación separada"
    )
    baseline = [10.0] * 10
    assert observer.shared_assessment(baseline, [10, 43, 44])["observed"] is True
    assert observer.shared_assessment(baseline, [10, 43, 10])["observed"] is False
    assert observer.shared_assessment(baseline, [None])["observed"] is None
    assert observer.shared_assessment([], [10])["observed"] is None


def test_sensor_errors_are_null_not_zero_and_pdh_localized_paths(harness_module):
    observer = harness_module("benchmark_observers")
    assert callable(getattr(observer, "parse_nvidia", None)), (
        "Falta sensor NVML separado"
    )
    gpu = observer.parse_nvidia("GPU-a, NVIDIA GeForce RTX 5070, 12227, 1300, 10927")
    assert gpu["used_mb"] == 1300 and gpu["uuid"] == "GPU-a"
    with pytest.raises(ValueError):
        observer.parse_nvidia("N/A")
    assert (
        observer.parse_meminfo(
            "MemAvailable: 1024 kB\nSwapTotal: 2048 kB\nSwapFree: 512 kB\n"
        )["swap_used_mb"]
        == 1.5
    )
    assert (
        observer.counter_paths(
            "Memoria del adaptador GPU",
            "Uso compartido",
            "luid_0x00000000_0x00001234_phys_0",
        )
        == "\\Memoria del adaptador GPU(luid_0x00000000_0x00001234_phys_0)\\Uso compartido"
    )


def test_shared_unknown_when_short_or_nonfinite(harness_module):
    observers = harness_module("benchmark_observers")
    for samples in ([1.0], [float("nan"), 2.0], [float("inf"), 2.0]):
        assert observers.shared_assessment([0.0] * 10, samples)["observed"] is None


def test_command_text_stays_inside_episode_budget(harness_module):
    observers = harness_module("benchmark_observers")
    seen = {}

    def execute(_args, **kwargs):
        seen["timeout"] = kwargs["timeout"]
        return type("Result", (), {"returncode": 0, "stdout": "ok"})()

    assert observers.command_text(["sensor"], execute=execute) == "ok"
    assert 0 < seen["timeout"] <= 1.25
