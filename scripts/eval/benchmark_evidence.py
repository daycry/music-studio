"""Evidencia privada inmutable y vista pública por lista permitida."""

import json
import math
import statistics
from pathlib import Path

from benchmark_plan import file_hash

TERMINALS = {"done", "error", "cancelled"}


def exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(
            value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
        )
        stream.write("\n")
    return {"sha256": file_hash(path), "bytes": path.stat().st_size}


def seal_files(folder):
    folder = Path(folder)
    return {
        p.relative_to(folder).as_posix(): {
            "sha256": file_hash(p),
            "bytes": p.stat().st_size,
        }
        for p in sorted(folder.rglob("*"))
        if p.is_file() and p.name != "seal.json"
    }


def validate_seal(folder, seal):
    for relative, item in seal.items():
        path = (Path(folder) / relative).resolve()
        if (
            not path.is_relative_to(Path(folder).resolve())
            or not path.is_file()
            or path.stat().st_size != item["bytes"]
            or file_hash(path) != item["sha256"]
        ):
            raise ValueError("evidence_changed")


def validate_events(events, job_id, *, require_terminal=True):
    if not isinstance(events, list) or any(
        e.get("seq") != i + 1 or e.get("job_id") != job_id for i, e in enumerate(events)
    ):
        raise ValueError("invalid_event_sequence")
    terminals = [e for e in events if e.get("type") in TERMINALS]
    if (
        len(terminals) > 1
        or (terminals and events[-1] != terminals[0])
        or (require_terminal and len(terminals) != 1)
    ):
        raise ValueError("invalid_terminal_count")
    return terminals[0] if terminals else None


def reference_rtf(rows, target):
    keys = ("config_id", "duration_s", "storage", "fixture_sha256", "mode")
    valid = [
        r
        for r in rows
        if all(r.get(k) == target.get(k) for k in keys)
        and r.get("phase") == "warm"
        and r.get("valid") is True
        and r.get("shared_gpu_observed") is False
        and type(r.get("rtf")) in {int, float}
        and math.isfinite(r["rtf"])
        and r["rtf"] > 0
    ]
    if len(valid) != 3 or len({r["run_id"] for r in valid}) != 3:
        return None, []
    return statistics.median(r["rtf"] for r in valid), [r["run_id"] for r in valid]


def enrich_rows(rows):
    results = []
    for row in rows:
        reference, ids = reference_rtf(rows, row)
        ratio = (
            row["rtf"] / reference if reference and row.get("rtf") is not None else None
        )
        observed = row.get("shared_gpu_observed")
        assessment = (
            "unknown"
            if observed is None or ratio is None
            else ("compatible" if observed and ratio > 1.5 else "not_detected")
        )
        results.append(
            {
                **row,
                "reference_rtf": reference,
                "reference_run_ids": ids,
                "rtf_ratio": ratio,
                "spill_assessment": assessment,
            }
        )
    return results


def complete_matrix(plan, rows):
    by_run = {r["run_id"]: r for r in rows}
    return len(by_run) == len(plan["runs"]) and all(
        by_run.get(run["run_id"], {}).get("valid") is True
        or (
            run["config_id"] == "xl-turbo-lm06-int8"
            and by_run.get(run["run_id"], {}).get("status") == "hardware_not_feasible"
            and by_run[run["run_id"]].get("hardware_evidence_sha256")
        )
        for run in plan["runs"]
    )


def recommendations(plan, rows):
    if not complete_matrix(plan, rows):
        return "Recomendación pendiente: faltan mediciones u observaciones válidas de toda la matriz."
    candidates = []
    for config in plan["configs"]:
        eligible = [r for r in rows if r["config_id"] == config["config_id"]]
        if eligible and all(
            r.get("valid")
            and r.get("shared_gpu_observed") is False
            and r.get("spill_assessment") == "not_detected"
            for r in eligible
        ):
            candidates.append(
                (
                    statistics.median(r["rtf"] for r in eligible),
                    config["config_id"],
                    eligible,
                )
            )
    if not candidates:
        return "Recomendación pendiente: ningún candidato reúne observaciones válidas sin indicio de presión bajo esta política en todas las duraciones."
    rtf, identity, chosen = min(candidates, key=lambda c: c[0])

    def phase_load(phase):
        values = [
            r["load_s"]
            for r in chosen
            if r["phase"] == phase and r.get("load_s") is not None
        ]
        return f"{statistics.median(values):.3f}" if values else "null"

    load = phase_load("process_cold")
    warm_load = phase_load("warm")
    peak = max(r["vram_peak_mb"] for r in chosen)
    result = f"Default operativo candidato: `{identity}`; RTF mediana {rtf:.4f}, carga cold mediana {load} s, carga warm mediana {warm_load} s, pico {peak:.1f} MiB, sin aumento sharedGPU observado. "
    quality = next((c for c in candidates if c[1] == "sft-lm06"), None)
    if quality:
        result += f"Candidato operacional para modo de alta calidad: `{quality[1]}`, 50 pasos, RTF mediana {quality[0]:.4f}, pico {max(r['vram_peak_mb'] for r in quality[2]):.1f} MiB, sin aumento sharedGPU observado; calidad musical pendiente de escucha."
    else:
        result += "Modo de alta calidad pendiente de ejecución válida y escucha."
    return result


def public_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, int)):
        return f"{value:.4f}" if isinstance(value, float) else str(value)
    # Solamente enumeraciones y ULID de procedencia: nada de rutas/textos libres.
    return (
        str(value)
        if isinstance(value, str) and all(c.isalnum() or c in "_-" for c in value)
        else "redacted"
    )


def render_report(plan, rows):
    rows = enrich_rows(rows)
    by_run = {r["run_id"]: r for r in rows}
    columns = (
        "config_id",
        "duration_s",
        "storage",
        "phase",
        "repetition",
        "status",
        "vram_peak_mb",
        "vram_cap_mb",
        "load_s",
        "copy_s",
        "idle_vram_used_mb",
        "idle_vram_free_mb",
        "shared_baseline_mb",
        "inference_s",
        "audio_duration_s",
        "rtf",
        "shared_gpu_peak_mb",
        "wsl_mem_available_mb",
        "rtf_ratio",
        "spilled_engine",
        "shared_gpu_observed",
        "spill_assessment",
        "run_id",
    )
    lines = [
        "# Benchmark RTX 5070",
        "",
        f"Sesión: `{public_value(plan['session_id'])}`.",
        "",
        "VRAM en reposo (NVML, plan): usada="
        + public_value(plan.get("baseline", {}).get("used_mb"))
        + " MiB; libre="
        + public_value(plan.get("baseline", {}).get("free_mb"))
        + " MiB. Las columnas idle son la mediana de observaciones previas por grupo; cap pertenece al proceso y shared al ámbito WDDM.",
        "",
        "Tiempos en segundos; memoria en MiB. `run_s` incluye carga; RTF usa el reloj directo sincronizado. Caché de filesystem no controlada.",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for run in plan["runs"]:
        row = {**run, "status": "not_measured", **by_run.get(run["run_id"], {})}
        lines.append(
            "| " + " | ".join(public_value(row.get(c)) for c in columns) + " |"
        )
    lines.extend(
        [
            "",
            recommendations(plan, rows),
            "",
            "NVML/CUDA, sharedGPU WDDM y RAM/swap WSL son ámbitos separados; null conserva una observación ausente.",
        ]
    )
    if plan.get("observation_method") in {
        "wddm_auto_v1",
        "wddm_auto_v2",
        "wddm_auto_v3",
    }:
        lines.extend(
            [
                "",
                f"Método: {plan['observation_method']}; shared_validation_level=provider_verified; shared_independent_validation=false; task_manager_contrast=conflicting_historical.",
                "Política sellada: "
                + public_value(plan.get("observation_policy_sha256"))
                + ".",
                "Dedicada se contrasta con NVML; shared es del proveedor agregado Windows. Sin indicio bajo esta política y cadencia no acredita ausencia causal de spill ni atribución al hijo. El viewport about:blank y la ventana visible son observaciones separadas; no acreditan la UI de M1 ni calidad musical.",
            ]
        )
    deltas = []
    for config in plan.get("configs", []):
        for duration in plan.get("durations_s", []):
            pair = [
                r
                for r in rows
                if r["config_id"] == config["config_id"]
                and r["duration_s"] == duration
                and r["phase"] == "process_cold"
                and r.get("valid")
            ]
            arms = {r["storage"]: r for r in pair}
            if set(arms) == {"bind", "container_copy"} and all(
                arms[a].get("load_s") is not None for a in arms
            ):
                delta = arms["bind"]["load_s"] - arms["container_copy"]["load_s"]
                deltas.append(
                    f"- {public_value(config['config_id'])}, {duration} s: bind−copia={delta:.3f} s"
                    + (
                        "; requiere ADR por superar 30 s absolutos."
                        if abs(delta) > 30
                        else "."
                    )
                )
    if deltas:
        lines.extend(["", "Comparación de carga por parejas:", "", *deltas])
    lines.extend(
        [
            "",
            "Copia y repeticiones por celda (warm exige tres repeticiones válidas distintas; dispersión muestral):",
            "",
            "| config_id | duration_s | storage | copy_s | cold_load_delta_s | break_even_cold_loads | warm_inference_median_s | warm_inference_min_s | warm_inference_max_s | warm_inference_stdev_s | warm_rtf_median | warm_rtf_stdev |",
            "| " + " | ".join(["---"] * 12) + " |",
        ]
    )
    for config in plan.get("configs", []):
        for duration in plan.get("durations_s", []):
            cells = {
                arm: [
                    r
                    for r in rows
                    if r["config_id"] == config["config_id"]
                    and r["duration_s"] == duration
                    and r["storage"] == arm
                    and r.get("valid")
                ]
                for arm in ("bind", "container_copy")
            }
            cold = {
                arm: [r for r in cell if r["phase"] == "process_cold"]
                for arm, cell in cells.items()
            }
            delta = None
            if all(
                len(cold[a]) == 1 and cold[a][0].get("load_s") is not None for a in cold
            ):
                delta = cold["bind"][0]["load_s"] - cold["container_copy"][0]["load_s"]
            for arm, cell in cells.items():
                copies = {r["copy_s"] for r in cell if r.get("copy_s") is not None}
                copy = next(iter(copies)) if len(copies) == 1 else None
                amortization = (
                    copy / delta
                    if arm == "container_copy"
                    and copy is not None
                    and delta is not None
                    and delta > 0
                    else None
                )
                warm = [r for r in cell if r["phase"] == "warm"]
                stats = [None] * 6
                if (
                    len(warm) == 3
                    and len({r["run_id"] for r in warm}) == 3
                    and all(
                        type(r.get(k)) in {int, float} and math.isfinite(r[k])
                        for r in warm
                        for k in ("inference_s", "rtf")
                    )
                ):
                    times = [r["inference_s"] for r in warm]
                    rtfs = [r["rtf"] for r in warm]
                    stats = [
                        statistics.median(times),
                        min(times),
                        max(times),
                        statistics.stdev(times),
                        statistics.median(rtfs),
                        statistics.stdev(rtfs),
                    ]
                values = [
                    config["config_id"],
                    duration,
                    arm,
                    copy,
                    delta,
                    amortization,
                    *stats,
                ]
                lines.append("| " + " | ".join(public_value(v) for v in values) + " |")
    lines.extend(
        [
            "",
            "La copia se paga una vez por contenedor/grupo y no forma parte de inference_s. break_even_cold_loads = copy_s / (carga cold bind − carga cold copia), sólo para ahorro positivo; no implica control de caché.",
        ]
    )
    return "\n".join(lines) + "\n"
