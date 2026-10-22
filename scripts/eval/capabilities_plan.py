"""Protocolo íntegro T-10, sin inferencia ni imports de torch en el llamante."""

from itertools import product
from pathlib import PurePosixPath, PureWindowsPath

from scripts.eval.benchmark_plan import new_id

REVISION = "dce621408bee8c31b4fcf4811682eb9359e1bc94"
PROFILES = {"turbo": 8, "sft": 50, "base": 32}
OPERATIONS = (
    "music.song",
    "music.instrumental",
    "music.retake",
    "music.extend",
    "music.repaint",
    "music.cover",
    "music.complete",
    "audio.stems",
)
FEATURES = ("negative_prompt", "bpm", "key", "timbre_ref", "lora")


def data_relative(value, *, project_relative=False):
    """Normaliza la raíz explícita; nunca acepta rutas absolutas ni escapes."""
    text = str(value).replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or PureWindowsPath(text).drive or ".." in path.parts:
        raise ValueError("invalid_data_path")
    parts = path.parts
    if project_relative:
        if not parts or parts[0] != "data":
            raise ValueError("input_requires_project_data_path")
        parts = parts[1:]
    if not parts or parts[0] == "data":
        raise ValueError("invalid_data_path")
    return PurePosixPath(*parts).as_posix()


CONTROLS = {
    "music.retake": [
        {"retake_variance": 0, "retake_seed": 201},
        {"retake_variance": 0.2, "retake_seed": 201},
        {"retake_variance": 0.2, "retake_seed": 202},
    ],
    "music.extend": [{"pad_s": 30, "repainting_start": 60, "repainting_end": 90}],
    "music.repaint": [
        {
            "repaint_mode": m,
            "repaint_strength": 0.5,
            "repaint_wav_crossfade_sec": 0,
            "repainting_start": 20,
            "repainting_end": 30,
        }
        for m in ("aggressive", "balanced", "conservative")
    ],
    "music.cover": [{"audio_cover_strength": s} for s in (1.0, 0.5)],
    "music.complete": [{"complete_track_classes": ["drums", "bass", "guitar"]}],
    "audio.stems": [{"track_name": t} for t in ("vocals", "drums", "bass", "guitar")],
    "negative_prompt": [{"negative_prompt": t} for t in ("", "distortion")],
    "bpm": [{"bpm": b} for b in (None, 80, 120)],
    "key": [{"key": k} for k in ("", "C major", "F# minor")],
    "timbre_ref": [{"reference": r, "python_seed": 501} for r in (None, "A", "B")],
    "lora": [{"lora_scale": s} for s in (0.0, 1.0)],
}


def matrix():
    rows = []
    for profile, surface, case in product(
        PROFILES, ("v1", "native_lab"), OPERATIONS + FEATURES
    ):
        for seed, control in product((101, 102, 103), CONTROLS.get(case, [{}])):
            job_id = new_id()
            prerequisites = []
            if surface == "native_lab" and case in ("music.complete", "audio.stems"):
                prerequisites.append("authorized_multitrack_ground_truth")
            if case == "key":
                prerequisites.append("authorized_tonal_evaluator")
            if surface == "native_lab" and case == "lora":
                prerequisites.extend(
                    ("licensed_consented_lora", "audited_safe_lora_loader")
                )
            rows.append(
                {
                    "job_id": job_id,
                    "case": case,
                    "surface": surface,
                    "profile": profile,
                    "checkpoint": f"acestep-v15-{profile}",
                    "model_id": f"ace-step-1.5-{profile}",
                    "lm": "acestep-5Hz-lm-0.6B",
                    "mode": "bf16",
                    "dtype": "bf16",
                    "backend": "pt",
                    "inference_steps": PROFILES[profile],
                    "guidance_scale": 7.0,
                    "shift": 1.0,
                    "lm_cfg_scale": 2.0,
                    "seed": seed,
                    "lm_seed": seed,
                    "dit_seed": seed,
                    "n_outputs": 1,
                    "duration_s": 90 if case == "music.extend" else 60,
                    "control": dict(control),
                    "prerequisites": prerequisites,
                    "execution_status": "planned",
                    "verdict": None,
                    "verified": False,
                    "audio_output": None,
                    "upstream_revision": REVISION,
                    "command": [
                        "uv",
                        "run",
                        "--frozen",
                        "--no-sync",
                        "--all-packages",
                        "python",
                        "-m",
                        "scripts.eval.capabilities",
                        "execute",
                        "--case-id",
                        job_id,
                    ],
                }
            )
    return rows


def request_for(row, fixture):
    instrumental = row["case"] == "music.instrumental"
    if instrumental:
        style = fixture.get("instrumental_style")
        if not isinstance(style, str) or not style.strip():
            raise ValueError("instrumental_style_prerequisite")
    else:
        style = fixture["style"]
    params = {
        "style": style,
        "lyrics": "[Instrumental]" if instrumental else fixture["lyrics"],
        "duration_s": row["duration_s"],
        "language": "es",
        "inference_steps": row["inference_steps"],
        "shift": row["shift"],
    }
    if row["profile"] != "turbo":
        params["guidance_scale"] = row["guidance_scale"]
    for name in ("negative_prompt", "bpm", "key"):
        if name in row["control"] and row["control"][name] is not None:
            params[name] = row["control"][name]
    if row["case"] == "lora":
        params["lora"] = fixture.get("lora", {}).get("path", "unavailable")
    request = {
        "job_id": row["job_id"],
        "task": row["case"] if row["case"] in OPERATIONS else "music.song",
        "model_id": row["model_id"],
        "mode": row["mode"],
        "seed": row["seed"],
        "n_outputs": 1,
        "timeout_s": 1800,
        "output_dir": f"tmp/{row['job_id']}",
        "params": params,
    }
    if row["case"] == "timbre_ref" and row["control"]["reference"]:
        reference = fixture["references"][row["control"]["reference"]]
        request["inputs"] = [
            {
                **reference,
                "path": data_relative(reference["path"], project_relative=True),
            }
        ]
    return request
