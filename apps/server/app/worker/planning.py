"""ConstrucciÃ³n de planes privados desde la cadena durable de audio."""

import hashlib

from audio_post.manifest import safe_path

from .contracts import PostPlan, PublicationAuthority, SourceReference
from .packages import TOOL_PIN, canonical_bytes, read_file


def _dump(value):
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _artifact_map(artifacts):
    result = {}
    for artifact in artifacts:
        item = _dump(artifact)
        index = item.get("output_index")
        if type(index) is not int or index in result:
            raise ValueError("PROVENANCE_MISMATCH")
        result[index] = item
    return result


def compose_post_plan(
    *, post, generation, attempt, takes, artifacts, root, execution_id, tool_pin
):
    """Compose an immutable ``PostPlan`` from already-authoritative rows.

    This function deliberately accepts rows selected by the caller instead of
    querying arbitrary IDs. The runtime performs the ownership/status query in
    one transaction and calls this pure composition step with that snapshot.
    """
    if (
        getattr(post, "task", "post.audio") != "post.audio"
        or getattr(post, "lane", "cpu") != "cpu"
    ):
        raise ValueError("POST_JOB_INVALID")
    if post.status not in {"queued", "running"} or generation.status != "succeeded":
        raise ValueError("POST_CHAIN_NOT_READY")
    if attempt.status != "succeeded" or attempt.terminal is None:
        raise ValueError("WINNING_ATTEMPT_NOT_READY")
    provenance = attempt.provenance
    if provenance is None:
        raise ValueError("PROVENANCE_MISSING")
    terminal = _dump(attempt.terminal)
    if terminal.get("type") != "done" or terminal.get("job_id") != attempt.id:
        raise ValueError("PROVENANCE_MISMATCH")
    terminal_artifacts = _artifact_map(terminal.get("data", {}).get("artifacts", []))
    inputs = post.request.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("POST_INPUTS_INVALID")
    by_index = {take.variant_index: take for take in takes}
    entries = []
    pin_sha = hashlib.sha256(canonical_bytes(tool_pin)).hexdigest()
    provenance_sha = hashlib.sha256(canonical_bytes(provenance)).hexdigest()
    terminal_sha = hashlib.sha256(canonical_bytes(terminal)).hexdigest()
    generation_request = (
        generation.request if isinstance(generation.request, dict) else {}
    )
    default_duration = generation_request.get("params", {}).get("duration_s")
    for output_index, item in enumerate(inputs):
        if not isinstance(item, dict):
            raise TypeError("POST_INPUTS_INVALID")
        ref = item.get("ref")
        index = item.get("output_index", 0)
        if (
            not isinstance(ref, dict)
            or ref.get("type") != "job"
            or ref.get("id") != generation.id
            or type(index) is not int
            or index != output_index
        ):
            raise ValueError("POST_INPUTS_INVALID")
        take = by_index.get(index)
        artifact = terminal_artifacts.get(index)
        if take is None or take.job_id != generation.id or artifact is None:
            raise ValueError("PROVENANCE_MISMATCH")
        if not artifact.get("path", "").startswith(f"tmp/{attempt.id}/"):
            raise ValueError("UNSAFE_PATH")
        media_type = artifact.get("media_type")
        if media_type not in {"audio/wav", "audio/flac", "audio/mpeg"}:
            raise ValueError("AUDIO_INPUT_INVALID")
        source_path = safe_path(root, "data/" + artifact["path"])
        payload = read_file(source_path)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != artifact.get("sha256"):
            raise ValueError("PROVENANCE_MISMATCH")
        duration = take.duration_s or take.params.get("duration_s") or default_duration
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError("AUDIO_DURATION_MISSING")
        authority = PublicationAuthority(
            owner_id=post.owner_id,
            song_id=post.song_id,
            post_job_id=post.id,
            generation_job_id=generation.id,
            winning_attempt_id=attempt.id,
            winning_ordinal=attempt.ordinal,
            terminal_seq=terminal["seq"],
            terminal_sha256=terminal_sha,
            take_id=take.id,
            output_index=index,
            seed=take.seed,
            provenance_sha256=provenance_sha,
        )
        source = SourceReference(
            path="data/" + artifact["path"],
            sha256=digest,
            media_type=media_type,
            bytes=len(payload),
            duration_s=float(duration),
        )
        copied = source.model_copy(
            update={"path": f"data/tmp/_server_inputs/{execution_id}/{index}.wav"}
        )
        entries.append({"authority": authority, "source": source, "copy": copied})
    return PostPlan(
        version=1,
        handler="post.audio",
        handler_version=1,
        owner_id=post.owner_id,
        song_id=post.song_id,
        post_job_id=post.id,
        generation_job_id=generation.id,
        request_sha256=hashlib.sha256(canonical_bytes(post.request)).hexdigest(),
        tool_pin_sha256=pin_sha,
        provenance=provenance,
        takes=entries,
    )


def load_tool_pin():
    """Read the immutable server tool pin for plan construction."""
    import json

    return json.loads(read_file(TOOL_PIN, limit=65536))
