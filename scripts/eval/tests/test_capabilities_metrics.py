import importlib
import importlib.util

import numpy as np
import pytest


def test_stem_metrics_compare_real_ground_truth_without_verdict():
    name = "scripts.eval.capabilities_metrics"
    compare = (
        importlib.import_module(name).stem_metrics
        if importlib.util.find_spec(name)
        else lambda *a: {"target_snr_db": 0}
    )
    target = np.ones((2, 100), dtype=np.float32)
    ground_truth = {
        "vocals": target,
        "drums": -target,
        "bass": target * 0.5,
        "guitar": target * 0.25,
    }
    result = compare(target, "vocals", ground_truth)
    assert result["target_snr_db"] is None
    assert result["target_exact"]
    assert result["verdict"] is None
    assert set(result["projection_coefficients"]) == set(ground_truth)


def test_metrics_alignment_and_energy_errors():
    from scripts.eval.capabilities_metrics import (
        TRACKS,
        stem_metrics,
        validate_ground_truth,
    )

    value = np.ones((2, 10), dtype=np.float32)
    with pytest.raises(ValueError, match="four_real"):
        stem_metrics(value, "vocals", {})
    gt = {name: value for name in TRACKS}
    output = value * 0.5
    assert stem_metrics(output, "vocals", gt)["target_snr_db"] == pytest.approx(
        6.0206, abs=0.001
    )
    gt["bass"] = value[:, :5]
    with pytest.raises(ValueError, match="shape_alignment"):
        stem_metrics(output, "vocals", gt)
    with pytest.raises(ValueError, match="ground_truth_prerequisite"):
        validate_ground_truth({})
    fixture = {
        "ground_truth": {
            "tracks": {name: f"{name}.wav" for name in TRACKS},
            "class_acceptance": {"accepted": True, "evaluator": "owner"},
        }
    }
    with pytest.raises(ValueError, match="alignment_prerequisite"):
        validate_ground_truth(fixture)
    fixture["ground_truth"].update(
        mix_coefficients={name: 0.2 for name in TRACKS},
        alignment_frames={name: 0 for name in TRACKS},
    )
    assert validate_ground_truth(fixture) == fixture["ground_truth"]
