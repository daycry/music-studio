"""Postproceso CPU y manifiestos portables, sin estado ni acceso a la BD."""

import math

import numpy as np


def validate_audio(samples, sample_rate, expected_duration_s):
    samples = np.asarray(samples)
    if (
        samples.ndim not in (1, 2)
        or not samples.size
        or isinstance(sample_rate, bool)
        or not isinstance(sample_rate, (int, np.integer))
        or sample_rate <= 0
    ):
        raise ValueError("AUDIO_SHAPE")
    if not np.isfinite(expected_duration_s) or expected_duration_s <= 0:
        raise ValueError("AUDIO_DURATION")
    if not np.isfinite(samples).all():
        raise ValueError("AUDIO_NONFINITE")
    duration = len(samples) / sample_rate
    if abs(duration - expected_duration_s) > expected_duration_s * 0.05:
        raise ValueError("AUDIO_DURATION")
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    if rms <= 1e-3:
        raise ValueError("AUDIO_SILENCE")
    if float(np.mean(np.abs(samples) >= 1.0)) > 0.005:
        raise ValueError("AUDIO_CLIPPING")
    return {
        "duration_s": duration,
        "rms_dbfs": 20 * math.log10(rms),
        "sample_rate": sample_rate,
        "channels": 1 if samples.ndim == 1 else samples.shape[1],
    }


def make_peaks(samples, count=2000):
    samples = np.asarray(samples)
    if samples.ndim == 1:
        samples = samples[:, None]
    if (
        samples.ndim != 2
        or not samples.size
        or not np.isfinite(samples).all()
        or count < 1
    ):
        raise ValueError("AUDIO_SHAPE")
    bins = np.array_split(samples, min(count, len(samples)))
    return {
        "version": 1,
        "channels": samples.shape[1],
        "length": len(samples),
        "data": [
            [[float(b[:, c].min()), float(b[:, c].max())] for b in bins]
            for c in range(samples.shape[1])
        ],
    }


from .manifest import verify_manifest, write_manifest  # noqa: F401


def process_audio(*args, **kwargs):
    from .pipeline import process_audio as process

    return process(*args, **kwargs)


def measure_audio(*args, **kwargs):
    from .pipeline import measure_audio as measure

    return measure(*args, **kwargs)
