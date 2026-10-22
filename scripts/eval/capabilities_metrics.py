"""Medidas técnicas contra multipistas reales; no infieren calidad ni identidad."""

import numpy as np

from scripts.eval.capabilities_evidence import pcm_record

TRACKS = ("vocals", "drums", "bass", "guitar")


def stem_metrics(output, track, ground_truth):
    if set(ground_truth) != set(TRACKS) or track not in TRACKS:
        raise ValueError("four_real_ground_truth_tracks_required")
    pcm_record(output)
    for source in ground_truth.values():
        pcm_record(source)
        if source.shape != output.shape:
            raise ValueError("ground_truth_shape_alignment_mismatch")
    y = output.astype(np.float64).ravel()
    target = ground_truth[track].astype(np.float64).ravel()
    power, error = float(np.dot(target, target)), float(np.dot(y - target, y - target))
    projection = {}
    for name, source in ground_truth.items():
        source = source.astype(np.float64).ravel()
        energy = float(np.dot(source, source))
        projection[name] = float(np.dot(y, source) / energy) if energy else None
    return {
        "target_pcm": pcm_record(ground_truth[track]),
        "output_pcm": pcm_record(output),
        "target_snr_db": float(10 * np.log10(power / error))
        if power and error
        else None,
        "target_exact": bool(
            np.array_equal(output.view(np.uint32), ground_truth[track].view(np.uint32))
        ),
        "target_error_energy": error,
        "projection_coefficients": projection,
        "alignment_policy": "same_frames_no_shift_or_resample",
        "projection_is_not_isolated_bleed": True,
        "verdict": None,
    }


def validate_ground_truth(fixture):
    gt = fixture.get("ground_truth", {})
    if (
        set(gt.get("tracks", {})) != set(TRACKS)
        or gt.get("class_acceptance", {}).get("accepted") is not True
        or not gt.get("class_acceptance", {}).get("evaluator")
    ):
        raise ValueError("ground_truth_prerequisite")
    if set(gt.get("mix_coefficients", {})) != set(TRACKS) or gt.get(
        "alignment_frames"
    ) != {name: 0 for name in TRACKS}:
        raise ValueError("ground_truth_alignment_prerequisite")
    return gt
