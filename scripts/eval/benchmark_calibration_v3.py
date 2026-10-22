"""Selección de calibración sobre publicaciones v3 supervisadas completas."""

import json
from pathlib import Path

from benchmark_plan import ROOT, digest, file_hash, source_hashes


def validate_lifecycle(lifecycle, context):
    """Comprueba originales sellados de respuesta, también en API standalone."""
    from benchmark_evidence import validate_events
    from benchmark_observation import read_sealed, require_acquisition, stamp

    try:
        for phase in ("loaded", "unloaded"):
            point = lifecycle[phase]
            require_acquisition(point, context, "wddm_auto_v3")
            safe_path(ROOT / point["proof"]["path"])
            proof = json.loads(
                read_sealed(point["proof"], ROOT).read_text(encoding="utf-8")
            )
            require_acquisition(proof, context, "wddm_auto_v3")
            if stamp(proof["finished_utc"]) != stamp(point["observed_at"]) or stamp(
                proof["started_utc"]
            ) > stamp(proof["finished_utc"]):
                raise ValueError("auto_lifecycle_proof_time_mismatch")
            if phase == "unloaded":
                if (
                    proof["response"].get("loaded", "missing") is not None
                    or proof["response"].get("state") != "idle"
                ):
                    raise ValueError("auto_unloaded_health_proof_invalid")
            elif point["event"] == "health_loaded":
                loaded = proof["response"].get("loaded")
                if (
                    not isinstance(loaded, dict)
                    or not loaded.get("model_id")
                    or loaded.get("mode") not in {"bf16", "offload-int8"}
                ):
                    raise ValueError("auto_loaded_health_proof_invalid")
            else:
                events = proof["events"]
                validate_events(
                    events, point["job_id"], require_terminal=point["event"] == "done"
                )
                candidates = [e for e in events if e["type"] == point["event"]]
                if not candidates or (
                    point["event"] == "done"
                    and candidates[-1].get("data", {}).get("executed") is not True
                ):
                    raise ValueError("auto_loaded_event_proof_invalid")
    except (KeyError, TypeError, AttributeError, OSError, json.JSONDecodeError):
        raise ValueError("v3_lifecycle_proof_required") from None


def safe_path(path, root=ROOT):
    """Rechaza enlaces en cada componente, antes de resolverlos."""
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root):
        raise ValueError("v3_path_outside_root")
    for component in (path, *path.parents):
        if component.is_symlink() or component.is_junction():
            raise ValueError("v3_symlink_evidence")
        if component == root:
            break
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("v3_path_outside_root")
    return path


def select_phases(
    envelope, lifecycle, context, *, trusted_receipts, trusted_attempts, now=None
):
    """No recibe muestras normalizadas como sustituto de los originales."""
    from benchmark_episode import read_publications
    from benchmark_observation import validate_samples

    if trusted_receipts is None or trusted_attempts is None:
        raise ValueError("v3_supervisor_anchors_required")
    try:
        if set(envelope) != {"root", "receipts", "attempts", "phases"}:
            raise ValueError("v3_supervised_calibration_schema_required")
        for relative in context["source_hashes"]:
            safe_path(ROOT / relative)
        if context["source_hashes"] != source_hashes(ROOT):
            raise ValueError("auto_complete_source_and_matrix_required")
        if context["lock_sha256"] != file_hash(
            safe_path(ROOT / "models/models.lock.json")
        ):
            raise ValueError("auto_lock_changed")
        root = safe_path(envelope["root"])
        for path in root.rglob("*"):
            safe_path(path)
        receipts, attempts = envelope["receipts"], envelope["attempts"]
        if not receipts or not attempts:
            raise ValueError("v3_complete_inventory_required")
        samples = read_publications(
            root,
            receipts,
            context,
            trusted_receipts=trusted_receipts,
            attempts=attempts,
            trusted_attempts=trusted_attempts,
            now=now,
            historical=True,
        )
        # A rejected/interrupted tick is retained by the reader; it cannot be
        # ignored to accredit uninterrupted observation through preparation.
        if any(attempt["status"] != "accepted" for attempt in attempts):
            raise ValueError("v3_accreditation_observation_interrupted")
        validate_samples(
            samples,
            context,
            now=now,
            historical=True,
            continuous=True,
            method="wddm_auto_v3",
        )
        refs = envelope["phases"]
        if set(refs) != {"baseline", "loaded", "unloaded"}:
            raise ValueError("auto_calibration_samples_required")
        indices = {r["episode_id"]: i for i, r in enumerate(receipts)}
        selected, previous = {}, -1
        for phase in ("baseline", "loaded", "unloaded"):
            if len(refs[phase]) != 10:
                raise ValueError("auto_calibration_samples_required")
            selected[phase] = []
            for ref in refs[phase]:
                if set(ref) != {"episode_id", "receipt_sha256"}:
                    raise ValueError("v3_phase_reference_invalid")
                index = indices[ref["episode_id"]]
                receipt = receipts[index]
                if index <= previous or ref["receipt_sha256"] != digest(receipt):
                    raise ValueError("v3_phase_reference_order_or_seal_invalid")
                prepared = json.loads(
                    (root / receipt["episode_id"] / "prepared.json").read_text(
                        encoding="utf-8"
                    )
                )
                if (
                    prepared["stream"] != phase
                    or prepared["idle"] is not (phase != "loaded")
                    or prepared["phase_started_utc"]
                    != (
                        None if phase == "baseline" else lifecycle[phase]["observed_at"]
                    )
                ):
                    raise ValueError("auto_calibration_phase_context_mismatch")
                selected[phase].append(samples[index])
                previous = index
        return selected, samples
    except (KeyError, TypeError, AttributeError, OSError, json.JSONDecodeError):
        raise ValueError("v3_supervised_calibration_incomplete") from None
