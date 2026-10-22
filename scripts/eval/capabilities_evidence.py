"""Custodia inmutable, comparación FLOAT y límites de los veredictos."""

import hashlib
import json
from pathlib import Path

import numpy as np


def file_record(path):
    value = Path(path).read_bytes()
    return {"sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}


def exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)


def pcm_record(samples):
    samples = np.asarray(samples)
    if (
        samples.dtype != np.float32
        or samples.ndim != 2
        or samples.shape[0] != 2
        or not np.isfinite(samples).all()
    ):
        raise ValueError("finite_stereo_float32_required")
    payload = np.ascontiguousarray(samples.astype("<f4", copy=False)).tobytes()
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "frames": samples.shape[1],
        "channels": 2,
        "dtype": "float32",
        "endian": "little",
        "layout": "channels_frames",
        "signed_zero_samples": int(np.sum((samples == 0) & np.signbit(samples))),
    }


def compare_pcm(source, output, start, end, *, crossfade_frames=0):
    pcm_record(source)
    pcm_record(output)
    if (
        source.shape != output.shape
        or not 0 <= start < end <= source.shape[1]
        or crossfade_frames < 0
    ):
        raise ValueError("shape_or_region_mismatch")
    changed = source.view(np.uint32) != output.view(np.uint32)
    ranges = {
        "prefix": (0, start),
        "interior": (start, end),
        "suffix": (end, source.shape[1]),
        "left_band": (
            max(0, start - crossfade_frames),
            min(source.shape[1], start + crossfade_frames),
        ),
        "right_band": (
            max(0, end - crossfade_frames),
            min(source.shape[1], end + crossfade_frames),
        ),
    }
    result = {
        "source": pcm_record(source),
        "output": pcm_record(output),
        "region": [start, end],
        "crossfade_frames_effective": crossfade_frames,
        "outside_bitexact": not bool(
            changed[:, :start].any() or changed[:, end:].any()
        ),
    }
    for name, (left, right) in ranges.items():
        delta = np.abs(
            source[:, left:right].astype(np.float64)
            - output[:, left:right].astype(np.float64)
        )
        result[name] = {
            "frames": [left, right],
            "different_samples": changed[:, left:right].sum(axis=1).tolist(),
            "max_abs_error": delta.max(axis=1).tolist() if right > left else [0.0, 0.0],
        }
    return result


def eligible(row):
    acceptance = row.get("musical_acceptance", {})
    return bool(
        row.get("surface") == "v1"
        and row.get("execution_status") == "executed"
        and row.get("verdict") == "funciona"
        and row.get("audio_output")
        and row.get("output_seal")
        and row.get("technical_acceptance") is True
        and acceptance.get("accepted") is True
        and acceptance.get("evaluator")
        and acceptance.get("observed_at")
        and acceptance.get("evidence_sha256")
        and not row.get("test_double")
        and not row.get("no_op")
    )


def render_report(rows):
    lines = [
        "# Capacidades ACE-Step — evidencia por superficie",
        "",
        "Pruebas CPU y transporte no acreditan calidad musical. Pendiente no significa fallo.",
        "",
        "| Caso | Checkpoint / modo | Superficie | Comando | Audio | Estado | Veredicto | Verificada |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        values = [
            row["case"],
            f"{row['checkpoint']} / {row['mode']}",
            row["surface"],
            " ".join(row["command"]),
            row.get("audio_output") or "—",
            row["execution_status"],
            row.get("verdict") or "pendiente",
            "sí" if eligible(row) else "no",
        ]
        lines.append(
            "| "
            + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values)
            + " |"
        )
    return "\n".join(lines) + "\n"
