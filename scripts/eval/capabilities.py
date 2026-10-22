"""CLI T-10: planificar, ejecutar un caso sellado y renderizar informe privado."""

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.eval.capabilities_evidence import (
    exclusive_json,
    file_record,
    render_report,
)
from scripts.eval.capabilities_native import contained, validate_audio_resources
from scripts.eval.capabilities_plan import matrix
from scripts.eval.capabilities_runtime import execute_native, execute_v1, pending

ROOT = Path(__file__).resolve().parents[2]


def load_text(bundle):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("lyrics_declaration") not in ("assistant", "owner", "authorized"):
        raise ValueError("lyrics_rights_required")
    for name, seal in manifest["files"].items():
        if file_record(contained(bundle, name)) != seal:
            raise ValueError("text_bundle_changed")
    return {
        "style": (bundle / "song-caption.txt").read_text(encoding="utf-8"),
        "instrumental_style": (bundle / "instrumental-caption.txt").read_text(
            encoding="utf-8"
        ),
        "lyrics": (bundle / "lyrics.txt").read_text(encoding="utf-8"),
        "lyrics_declaration": manifest["lyrics_declaration"],
        "prerequisites": {},
        "files": {
            str(p.relative_to(bundle)): file_record(p)
            for p in bundle.iterdir()
            if p.is_file()
        },
    }


def prepare_padding(fixture, root, folder):
    import numpy as np
    import soundfile as sf

    source = contained(root, fixture["source"])
    samples, rate = sf.read(source, dtype="float32", always_2d=True)
    if (
        rate != 48000
        or samples.shape != (60 * 48000, 2)
        or not np.isfinite(samples).all()
        or np.max(np.abs(samples)) > 0.8
    ):
        raise ValueError("extension_source_requires_60s_finite_float_stereo48k")
    path = folder / "padded-source.wav"
    padded = np.pad(samples, ((0, 30 * 48000), (0, 0)))
    with path.open("xb") as stream:
        sf.write(stream, padded, rate, subtype="FLOAT", format="WAV")
    fixture["padded_source"] = str(path.relative_to(root))
    exclusive_json(
        folder / "padding.json",
        {
            "source": file_record(source),
            "padded": file_record(path),
            "pad_s": 30,
            "section_map": [
                {"start": 0, "end": 60, "role": "original"},
                {"start": 60, "end": 90, "role": "extension"},
            ],
        },
    )


def main(argv=None, *, root=ROOT, api=None, supervisor=None, gpu=None):
    parser = argparse.ArgumentParser(
        description="Matriz T-10 local, sin inferencia implícita"
    )
    parser.add_argument("action", choices=("plan", "execute", "report"))
    parser.add_argument("--session", required=True)
    parser.add_argument(
        "--text-bundle", default="data/inputs/t10-capabilities/original-text-v1"
    )
    parser.add_argument("--case-id")
    parser.add_argument("--resources")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args(argv)
    root = Path(root).resolve()
    folder = contained(root, f"eval/capabilities/{args.session}")
    try:
        if args.action == "plan":
            fixture = load_text(contained(root, args.text_bundle))
            rows = matrix()
            for row in rows:
                row["command"].extend(["--session", args.session])
            sources = {
                p.relative_to(root).as_posix(): file_record(p)
                for p in (root / "scripts/eval").glob("capabilities*.py")
            }
            upstream = root / ".cache/dev-cycle/t17/upstream-acestep"
            upstream_seal = {
                str(p.relative_to(upstream)).replace("\\", "/"): file_record(p)
                for p in upstream.rglob("*.py")
                if not p.name.endswith("_test.py")
            }
            plan = {
                "version": 1,
                "rows": rows,
                "fixture": fixture,
                "text_bundle": args.text_bundle,
                "source_seal": sources,
                "upstream_seal": upstream_seal,
                "cpu_execution_is_not_musical_evidence": True,
                "image_id": "sha256:00c32a76c951a4494a23282edf4e53d946f43f244e0790cbd59e806030bd7f43",
            }
            exclusive_json(folder / "plan.json", plan)
            exclusive_json(folder / "plan-seal.json", file_record(folder / "plan.json"))
            return 0
        if file_record(folder / "plan.json") != json.loads(
            (folder / "plan-seal.json").read_text()
        ):
            raise ValueError("plan_changed")
        plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
        for path, seal in plan["source_seal"].items():
            if file_record(contained(root, path)) != seal:
                raise ValueError("harness_changed_since_plan")
        fixture = load_text(contained(root, plan["text_bundle"]))
        if fixture != plan["fixture"]:
            raise ValueError("original_inputs_changed")
        if args.action == "report":
            rows = []
            for row in plan["rows"]:
                result = folder / row["job_id"] / "result.json"
                rows.append(json.loads(result.read_text()) if result.exists() else row)
            with (folder / "report.md").open("x", encoding="utf-8") as stream:
                stream.write(render_report(rows))
            return 0
        row = next((r for r in plan["rows"] if r["job_id"] == args.case_id), None)
        if row is None:
            raise ValueError("unknown_case")
        attempt = folder / row["job_id"]
        attempt.mkdir(exist_ok=False)
        if args.resources:
            resources = json.loads(
                contained(root, args.resources).read_text(encoding="utf-8")
            )
            allowed = {
                "source",
                "source_id",
                "vocals",
                "references",
                "ground_truth",
                "rights",
                "input_seals",
                "prerequisites",
                "lora",
                "tonal_evaluator",
            }
            if not isinstance(resources, dict) or set(resources) - allowed:
                raise ValueError("resource_override_forbidden")
            for path, seal in resources.get("input_seals", {}).items():
                if file_record(contained(root, path)) != seal:
                    raise ValueError("audio_input_changed")
            fixture.update(resources)
            validate_audio_resources(fixture, root)
            exclusive_json(
                attempt / "resources-receipt.json",
                {
                    "resource_file": args.resources,
                    "resource_seal": file_record(contained(root, args.resources)),
                    "resources_effective": resources,
                    "text_fixture": plan["fixture"],
                },
            )
        if row["case"] == "music.instrumental":
            fixture["style"] = fixture["instrumental_style"]
        missing = pending(row, fixture, root)
        source_cases = (
            "music.retake",
            "music.extend",
            "music.repaint",
            "music.cover",
            "music.complete",
            "audio.stems",
        )
        if (
            row["surface"] == "native_lab"
            and row["case"] in source_cases
            and not fixture.get("source")
        ):
            missing.append("authorized_source_audio")
        if (
            row["case"] == "timbre_ref"
            and row["control"]["reference"]
            and not fixture.get("references")
        ):
            missing.append("authorized_reference_audio")
        if missing:
            exclusive_json(
                attempt / "result.json",
                {
                    **row,
                    "execution_status": "pending_prerequisite",
                    "missing_prerequisites": missing,
                    "verdict": None,
                },
            )
            return 0
        if row["case"] == "music.extend" and row["surface"] == "native_lab":
            prepare_padding(fixture, root, attempt)
        fixture["lineage"] = {
            "parents": [fixture["source"]] if fixture.get("source") else [],
            "derivation": row["case"],
            "root_id": fixture.get("source_id", row["job_id"]),
            "new_artifact_id": row["job_id"],
        }
        if row["surface"] == "v1":
            if api is None:
                from scripts.eval.benchmark_runtime import EngineApi

                api = EngineApi(args.port, os.environ["STUDIO_ENGINE_TOKEN"])
            execute_v1(row, fixture, api, root, attempt)
        else:
            if not Path("/.dockerenv").exists():
                raise ValueError("native_container_required")
            if supervisor is None:
                from engine_common.runtime import NvmlGpu, ProcessSupervisor

                supervisor = ProcessSupervisor(
                    "scripts.eval.capabilities_native:NativeLabAdapter",
                    {
                        "checkpoint": row["checkpoint"],
                        "lm": row["lm"],
                        "resource_root": str(root / "models"),
                        "root": str(root),
                        "source_seal": plan["source_seal"],
                        "upstream_seal": plan["upstream_seal"],
                    },
                )
                gpu = NvmlGpu()
            execute_native(row, fixture, supervisor, gpu, root, attempt)
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"T-10: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
