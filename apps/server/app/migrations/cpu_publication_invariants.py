"""Guardas durables privadas, sin scheduler, procesos ni publicación de archivos."""

import json
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.worker.contracts import (
    ULID,
    CapturedProvenance,
    PostPlan,
    PreparedPackage,
    PrivateModel,
    PublicationAuthority,
    canonical_sha256,
    confined_path,
)

from .job_attempt_invariants import _schema_sql, _utc_sql
from .legacy_m1_registry import TABLES as LEGACY_TABLES

TABLE_NAMES = ("cpu_execution", "publication_intent", "publication_intent_revision")
PRIVATE_FIELDS = {
    "supervisor_epoch",
    "lease_token",
    "process_identity",
    "cleanup_state",
}
CPU_STATES = {
    "prepared": {"running", "interrupted", "failed", "cancelled"},
    "running": {"draining", "interrupted"},
    "draining": {"finished", "interrupted", "failed", "cancelled"},
    "interrupted": {"prepared", "failed", "cancelled"},
    "finished": set(),
    "failed": set(),
    "cancelled": set(),
}
INTENT_STATES = {
    "reserved": {"prepared", "failed", "cancelled", "quarantined"},
    "prepared": {"renamed", "failed", "cancelled", "quarantined"},
    "renamed": {"committed", "quarantined"},
    "committed": set(),
    "failed": {"reserved"},
    "cancelled": {"reserved"},
    "quarantined": set(),
}


class PublicationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class ExecutionOutcome(PrivateModel):
    kind: Literal["all_ready", "mixed", "all_failed"]
    ready_take_ids: list[ULID] = Field(max_length=64)
    failed_take_ids: list[ULID] = Field(max_length=64)


def payload(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return json.loads(value) if isinstance(value, str) else value


def typed(value, model):
    return model.model_validate(payload(value), strict=True)


def require_provenance(row):
    value = row.get("provenance")
    if value is None:
        raise PublicationError("PROVENANCE_MISSING")
    provenance = typed(value, CapturedProvenance)
    if canonical_sha256(provenance) != row.get("provenance_sha256"):
        raise PublicationError("PROVENANCE_MISMATCH")
    request = payload(row["engine_request"])
    options = payload(row["load_options"])
    if (provenance.engine_id, provenance.task, provenance.load.model_dump()) != (
        row["engine_id"],
        request["task"],
        options,
    ):
        raise PublicationError("PROVENANCE_MISMATCH")
    return provenance


def validate_row(name, row):
    """Validación Python complementaria; SQL protege también las referencias."""
    if name == "job_attempt":
        if row.get("provenance") is None:
            if row.get("provenance_sha256") is not None:
                raise PublicationError("PROVENANCE_MISMATCH")
        else:
            require_provenance(row)
        return
    if name == "cpu_execution":
        plan = typed(row["plan"], PostPlan)
        if plan.post_job_id != row["job_id"] or plan.owner_id != row["owner_id"]:
            raise PublicationError("CPU_AUTHORITY_MISMATCH")
        if canonical_sha256(plan) != row["plan_sha256"]:
            raise PublicationError("PLAN_SHA_MISMATCH")
        if row.get("outcome") is not None:
            outcome = typed(row["outcome"], ExecutionOutcome)
            ids = {entry.authority.take_id for entry in plan.takes}
            ready, failed = outcome.ready_take_ids, outcome.failed_take_ids
            if (
                len(set(ready + failed)) != len(ready + failed)
                or set(ready + failed) != ids
                or outcome.kind
                != (
                    "mixed"
                    if ready and failed
                    else "all_ready"
                    if ready
                    else "all_failed"
                )
            ):
                raise PublicationError("OUTCOME_MISMATCH")
    elif name == "publication_intent_revision":
        authority = PublicationAuthority.model_validate(
            {
                key: int(row[key]) if key == "seed" else row[key]
                for key in PublicationAuthority.model_fields
            },
            strict=True,
        )
        confined_path(row["stage_path"])
        confined_path(row["final_path"])
        if (
            row["stage_path"]
            != f"songs/{row['song_id']}/takes/.pending-{row['cpu_execution_id']}/{row['take_id']}"
            or row["final_path"] != f"songs/{row['song_id']}/takes/{row['take_id']}"
        ):
            raise PublicationError("PUBLICATION_PATH_MISMATCH")
        if row.get("package") is not None:
            package = typed(row["package"], PreparedPackage)
            if package.authority != authority or canonical_sha256(package) != row.get(
                "package_sha256"
            ):
                raise PublicationError("PACKAGE_MISMATCH")
        elif row.get("package_sha256") is not None:
            raise PublicationError("PACKAGE_MISMATCH")


def validate_rows(index):
    """Validar el grafo portable sin lecturas SQL por intento."""
    for (name, identifier), row in index.items():
        if name == "job_attempt" or name in TABLE_NAMES:
            validate_row(name, row)
        if name == "cpu_execution":
            job = index["job", row["job_id"]]
            p = typed(row["plan"], PostPlan)
            if (
                job["task"],
                job["lane"],
                job["owner_id"],
                job["song_id"],
                job["engine_id"],
                job["model_id"],
            ) != ("post.audio", "cpu", row["owner_id"], p.song_id, None, None):
                raise PublicationError("CPU_AUTHORITY_MISMATCH")
            if p.request_sha256 != canonical_sha256(job["request"]):
                raise PublicationError("CPU_AUTHORITY_MISMATCH")
            for a in (entry.authority for entry in p.takes):
                _authority(a.model_dump(), index, current=False)
        elif name == "publication_intent":
            take = index["take", row["take_id"]]
            if (
                row["owner_id"],
                row["song_id"],
                row["output_index"],
                int(row["seed"]),
            ) != (
                take["owner_id"],
                take["song_id"],
                take["variant_index"],
                int(take["seed"]),
            ):
                raise PublicationError("INTENT_AUTHORITY_MISMATCH")
            active = row.get("active_revision_id")
            if (
                active is not None
                and index["publication_intent_revision", active]["intent_id"]
                != identifier
            ):
                raise PublicationError("INTENT_AUTHORITY_MISMATCH")
            if row["state"] in {"prepared", "renamed", "committed"} and (
                active is None
                or index["publication_intent_revision", active].get("package") is None
            ):
                raise PublicationError("PACKAGE_MISMATCH")
            if row["state"] == "committed" and take["status"] != "ready":
                raise PublicationError("INTENT_AUTHORITY_MISMATCH")
            if row["state"] == "committed":
                package = typed(
                    index["publication_intent_revision", active]["package"],
                    PreparedPackage,
                )
                for role in ("master", "listen", "peaks", "manifest"):
                    f = getattr(package, role)
                    assets = [
                        asset
                        for (table, _), asset in index.items()
                        if table == "asset"
                        and asset["subject_type"] == "take"
                        and asset["subject_id"] == take["id"]
                        and asset["role"] == role
                    ]
                    if len(assets) != 1 or any(
                        assets[0][key] != value
                        for key, value in {
                            "path": f.path[5:],
                            "sha256": f.sha256,
                            "bytes": f.bytes,
                            "media_type": f.media_type,
                        }.items()
                    ):
                        raise PublicationError("PUBLICATION_ASSETS_MISMATCH")
        elif name == "publication_intent_revision":
            root = index["publication_intent", row["intent_id"]]
            cpu = index["cpu_execution", row["cpu_execution_id"]]
            if (
                row["owner_id"],
                row["song_id"],
                row["take_id"],
                row["output_index"],
                int(row["seed"]),
            ) != (
                root["owner_id"],
                root["song_id"],
                root["take_id"],
                root["output_index"],
                int(root["seed"]),
            ):
                raise PublicationError("INTENT_AUTHORITY_MISMATCH")
            entries = typed(cpu["plan"], PostPlan).takes
            actual = {
                key: int(row[key]) if key == "seed" else row[key]
                for key in PublicationAuthority.model_fields
            }
            if cpu["job_id"] != row["post_job_id"] or not any(
                entry.authority.model_dump() == actual
                and entry.source.sha256 == row["source_sha256"]
                for entry in entries
            ):
                raise PublicationError("CPU_AUTHORITY_MISMATCH")
            _authority(
                row,
                index,
                current=root.get("active_revision_id") == identifier
                and root["state"] not in {"failed", "cancelled"},
            )


def validate_connection(connection, name, row):
    """Revalidar el ganador real del ORM con lecturas agrupadas y acotadas."""
    if name != "cpu_execution":
        return
    plan = typed(row["plan"], PostPlan)
    identifiers = {
        "job": {plan.post_job_id, plan.generation_job_id},
        "job_attempt": {entry.authority.winning_attempt_id for entry in plan.takes},
        "take": {entry.authority.take_id for entry in plan.takes},
    }
    index = {}
    for table, ids in identifiers.items():
        resource = LEGACY_TABLES[table]
        for stored in connection.execute(
            select(resource).where(resource.c.id.in_(ids))
        ).mappings():
            index[table, stored["id"]] = dict(stored)
    resource = LEGACY_TABLES["job_dependency"]
    for stored in connection.execute(
        select(resource).where(resource.c.job_id == plan.post_job_id)
    ).mappings():
        index["job_dependency", stored["id"]] = dict(stored)
    index[name, row["id"]] = row
    try:
        validate_rows(index)
    except KeyError as error:
        raise PublicationError("CPU_AUTHORITY_MISMATCH") from error


def _authority(a, index, *, current):
    winner = index["job_attempt", a["winning_attempt_id"]]
    gen = index["job", a["generation_job_id"]]
    take = index["take", a["take_id"]]
    post = index["job", a["post_job_id"]]
    terminal = payload(winner["terminal"])
    provenance = require_provenance(winner)
    if (
        winner["job_id"],
        winner["owner_id"],
        winner["ordinal"],
        winner["last_seq"],
        winner["status"],
        gen["owner_id"],
        gen["song_id"],
        gen["task"],
        post["task"],
        post["lane"],
        post["owner_id"],
        post["song_id"],
    ) != (
        a["generation_job_id"],
        a["owner_id"],
        a["winning_ordinal"],
        a["terminal_seq"],
        "succeeded",
        a["owner_id"],
        a["song_id"],
        provenance.task,
        "post.audio",
        "cpu",
        a["owner_id"],
        a["song_id"],
    ):
        raise PublicationError("WINNER_AUTHORITY_MISMATCH")
    if (
        canonical_sha256(terminal) != a["terminal_sha256"]
        or canonical_sha256(provenance) != a["provenance_sha256"]
    ):
        raise PublicationError("WINNER_AUTHORITY_MISMATCH")
    artifacts = terminal["data"]["artifacts"]
    matches = [
        artifact
        for artifact in artifacts
        if artifact["output_index"] == a["output_index"]
        and artifact["meta"].get("seed") == int(a["seed"])
    ]
    if (
        len(matches) != 1
        or int(take["seed"]) != int(a["seed"])
        or take["variant_index"] != a["output_index"]
    ):
        raise PublicationError("OUTPUT_AUTHORITY_MISMATCH")
    if current and (
        take["job_id"] != gen["id"]
        or gen["attempt"] != a["winning_ordinal"]
        or gen["status"] != "succeeded"
    ):
        raise PublicationError("WINNER_AUTHORITY_MISMATCH")
    if not any(
        r["job_id"] == post["id"] and r["depends_on_job_id"] == gen["id"]
        for (table, _), r in index.items()
        if table == "job_dependency"
    ):
        raise PublicationError("DEPENDENCY_MISMATCH")


def cas(connection, table, identifier, expected_revision, state, **changes):
    if table not in {"cpu_execution", "publication_intent"}:
        raise PublicationError("CAS_TABLE_INVALID")
    allowed = (
        {"outcome", "error_code", "finished_at", *PRIVATE_FIELDS}
        if table == "cpu_execution"
        else {"active_revision_id", "error_code", "committed_at"}
    )
    if (
        changes.keys() - allowed
        or type(expected_revision) is not int
        or expected_revision < 1
    ):
        raise PublicationError("CAS_FIELDS_INVALID")
    current = (
        connection.exec_driver_sql(f'SELECT * FROM "{table}" WHERE id=?', (identifier,))
        .mappings()
        .one_or_none()
    )
    if current is None:
        raise PublicationError("CAS_NOT_FOUND")
    encoded = {
        key: json.dumps(
            payload(value), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        if isinstance(value, (dict, BaseModel))
        else value
        for key, value in changes.items()
    }
    if (
        current["revision"] == expected_revision + 1
        and current["state"] == state
        and all(current[key] == value for key, value in encoded.items())
    ):
        return current["revision"]
    if current["revision"] != expected_revision:
        raise PublicationError("CAS_STALE")
    fields = {"state": state, "revision": expected_revision + 1, **encoded}
    changed = connection.exec_driver_sql(
        f'UPDATE "{table}" SET '
        + ",".join(f'"{key}"=?' for key in fields)
        + " WHERE id=? AND revision=?",
        (*fields.values(), identifier, expected_revision),
    ).rowcount
    if changed != 1:
        raise PublicationError("CAS_STALE")
    return expected_revision + 1


def _raise(condition, message):
    return f"SELECT RAISE(ABORT,'{message}') WHERE {condition};"


def _json_guard(source):
    # SQLite directo recibe las mismas guardas sin UDF ni configuración runtime.
    forbidden = (
        "secret",
        "token",
        "password",
        "credential",
        "ciphertext",
        "authorization",
        "header",
        "apikey",
        "privatekey",
    )
    normalized = "lower(replace(replace(replace(key,'_',''),'-',''),' ',''))"
    predicate = " OR ".join(f"instr({normalized},'{word}')>0" for word in forbidden)
    return _raise(
        f"{source} IS NOT NULL AND (NOT json_valid({source}) OR EXISTS(SELECT 1 FROM json_tree({source}) WHERE (type='real' AND abs(atom)>1.7976931348623157e308) OR ({predicate})))",
        "Unsafe publication JSON",
    )


def _authority_sql(prefix):
    # prefix est une expression de colonne validée; valeurs JSON exactes liées au plan.
    a = lambda key: f"json_extract({prefix},'$.{key}')"
    return (
        "EXISTS(SELECT 1 FROM job_attempt w JOIN job g ON g.id=w.job_id JOIN take t ON t.id="
        + a("take_id")
        + " JOIN job p ON p.id="
        + a("post_job_id")
        + " WHERE w.id="
        + a("winning_attempt_id")
        + " AND w.job_id="
        + a("generation_job_id")
        + " AND w.owner_id="
        + a("owner_id")
        + " AND g.owner_id=w.owner_id AND p.owner_id=w.owner_id AND t.owner_id=w.owner_id"
        " AND g.song_id="
        + a("song_id")
        + " AND p.song_id=g.song_id AND t.song_id=g.song_id"
        " AND w.ordinal="
        + a("winning_ordinal")
        + " AND w.last_seq="
        + a("terminal_seq")
        + " AND w.status='succeeded' AND g.status='succeeded' AND g.attempt=w.ordinal AND (t.job_id=g.id OR EXISTS(SELECT 1 FROM snapshot_import WHERE song_id=g.song_id))"
        " AND g.task IN ('music.song','music.instrumental') AND p.task='post.audio' AND p.lane='cpu' AND p.engine_id IS NULL AND p.model_id IS NULL"
        " AND t.variant_index="
        + a("output_index")
        + f" AND t.seed=({prefix}->'$.seed')"
        " AND w.provenance IS NOT NULL AND w.provenance_sha256="
        + a("provenance_sha256")
        + " AND EXISTS(SELECT 1 FROM job_dependency d WHERE d.job_id=p.id AND d.depends_on_job_id=g.id)"
        " AND (SELECT count(*) FROM json_each(w.terminal,'$.data.artifacts') z WHERE json_extract(z.value,'$.output_index')="
        + a("output_index")
        + f" AND (z.value->'$.meta.seed')=({prefix}->'$.seed'))=1)"
    )


def _schema(model, source):
    # CapturedDescriptor se serializa como objeto /v1, no como su texto interno.
    from engine_contract import ModelDescriptor

    def expand(schema, definitions):
        if isinstance(schema, list):
            return [expand(v, definitions) for v in schema]
        if not isinstance(schema, dict):
            return schema
        if "$ref" in schema:
            return expand(definitions[schema["$ref"].split("/")[-1]], definitions)
        result = {k: expand(v, definitions) for k, v in schema.items() if k != "$defs"}
        if result.get("title") == "CapturedDescriptor":
            public = ModelDescriptor.model_json_schema()
            result = expand(public, public.get("$defs", {}))
        if result.get("pattern", "").startswith("^sha256:"):
            result.pop("pattern")
            result["minLength"] = 71
        if type(result.get("const")) is int:
            number = result.pop("const")
            result["minimum"] = number
            result["maximum"] = number
        return result

    schema = model.model_json_schema()
    schema = expand(schema, schema.get("$defs", {}))
    return _schema_sql(schema, source, {})


def install(connection):
    original = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='entity_song'"
    ).scalar_one()
    connection.exec_driver_sql("DROP VIEW entity_song")
    connection.exec_driver_sql(
        original
        + " UNION ALL SELECT 'cpu_execution',c.id,c.owner_id,j.song_id FROM cpu_execution c JOIN job j ON j.id=c.job_id UNION ALL SELECT 'publication_intent',id,owner_id,song_id FROM publication_intent UNION ALL SELECT 'publication_intent_revision',id,owner_id,song_id FROM publication_intent_revision"
    )
    for name in TABLE_NAMES:
        for action in ("INSERT", "UPDATE"):
            body = ""
            for field in ("created_at", "updated_at", "deleted_at"):
                body += _raise(
                    f"NEW.{field} IS NOT NULL AND NOT coalesce(({_utc_sql('NEW.' + field)}),0)",
                    "Invalid publication UTC",
                )
            if name == "cpu_execution":
                body += _raise(
                    "NOT EXISTS(SELECT 1 FROM job j WHERE j.id=NEW.job_id AND j.owner_id=NEW.owner_id AND j.task='post.audio' AND j.lane='cpu' AND j.engine_id IS NULL AND j.model_id IS NULL)",
                    "CPU authority mismatch",
                )
                body += _raise(
                    "EXISTS(SELECT 1 FROM job_attempt WHERE job_id=NEW.job_id AND ordinal=NEW.ordinal)",
                    "Mixed CPU ordinal",
                )
                body += _raise(
                    "NEW.ordinal<1 OR typeof(NEW.ordinal)!='integer' OR NEW.revision<1 OR typeof(NEW.revision)!='integer' OR NEW.handler!='post.audio' OR NEW.handler_version!=1 OR NEW.contract_version!=1 OR NEW.state NOT IN ('prepared','running','draining','interrupted','finished','failed','cancelled') OR NEW.cleanup_state NOT IN ('not_started','pending','confirmed','unknown')",
                    "Invalid CPU state",
                )
                body += _json_guard("NEW.plan") + _json_guard("NEW.outcome")
                body += _raise(
                    "NEW.outcome IS NOT NULL AND NOT coalesce(("
                    + _schema(ExecutionOutcome, "NEW.outcome")
                    + "),0)",
                    "Invalid CPU outcome",
                )
                body += _raise(
                    "NOT coalesce((" + _schema(PostPlan, "NEW.plan") + "),0)",
                    "Invalid CPU plan",
                )
                body += _raise(
                    "json_extract(NEW.plan,'$.post_job_id') IS NOT NEW.job_id OR json_extract(NEW.plan,'$.owner_id') IS NOT NEW.owner_id OR EXISTS(SELECT 1 FROM json_each(NEW.plan,'$.takes') e WHERE NOT "
                    + _authority_sql("json_extract(e.value,'$.authority')")
                    + ")",
                    "CPU authority mismatch",
                )
                body += _raise(
                    "(SELECT count(DISTINCT json_extract(value,'$.authority.output_index')) FROM json_each(NEW.plan,'$.takes'))!=json_array_length(NEW.plan,'$.takes') OR (SELECT count(DISTINCT json_extract(value,'$.authority.take_id')) FROM json_each(NEW.plan,'$.takes'))!=json_array_length(NEW.plan,'$.takes')",
                    "Duplicate CPU outputs",
                )
                importing_cpu = (
                    "NOT EXISTS(SELECT 1 FROM snapshot_import WHERE song_id=json_extract(NEW.plan,'$.song_id')) AND "
                    if action == "INSERT"
                    else ""
                )
                body += _raise(
                    importing_cpu
                    + "NEW.state IN ('finished','failed','cancelled') AND NEW.cleanup_state NOT IN ('confirmed','not_started')",
                    "CPU custody unknown",
                )
                body += _raise(
                    "NEW.state='finished' AND (NEW.outcome IS NULL OR NEW.finished_at IS NULL)",
                    "CPU outcome missing",
                )
                if action == "UPDATE":
                    body += _raise(
                        "OLD.state='interrupted' AND NEW.state='prepared' AND (OLD.cleanup_state!='confirmed' OR NEW.process_identity IS NOT NULL OR (OLD.lease_token IS NOT NULL AND NEW.lease_token IS OLD.lease_token))",
                        "CPU custody unknown",
                    )
                    body += _raise(
                        "OLD.state IN ('finished','failed','cancelled') AND (NEW.outcome IS NOT OLD.outcome OR NEW.error_code IS NOT OLD.error_code OR NEW.finished_at IS NOT OLD.finished_at)",
                        "Immutable CPU outcome",
                    )
            elif name == "publication_intent":
                body += _raise(
                    "NEW.revision<1 OR typeof(NEW.revision)!='integer' OR NEW.state NOT IN ('reserved','prepared','renamed','committed','failed','cancelled','quarantined') OR NOT EXISTS(SELECT 1 FROM take t WHERE t.id=NEW.take_id AND t.owner_id=NEW.owner_id AND t.song_id=NEW.song_id AND t.variant_index=NEW.output_index AND t.seed=NEW.seed)",
                    "Intent authority mismatch",
                )
                importing = (
                    "NOT EXISTS(SELECT 1 FROM snapshot_import WHERE song_id=NEW.song_id) AND "
                    if action == "INSERT"
                    else ""
                )
                body += _raise(
                    importing
                    + "NEW.active_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM publication_intent_revision r WHERE r.id=NEW.active_revision_id AND r.intent_id=NEW.id)",
                    "Intent revision mismatch",
                )
                body += _raise(
                    importing
                    + "NEW.state IN ('prepared','renamed','committed') AND NOT EXISTS(SELECT 1 FROM publication_intent_revision r WHERE r.id=NEW.active_revision_id AND r.package IS NOT NULL)",
                    "Missing prepared package",
                )
                body += _raise(
                    "NEW.state IN ('prepared','renamed','committed') AND EXISTS(SELECT 1 FROM publication_intent_revision r JOIN job j ON j.id=r.post_job_id WHERE r.id=NEW.active_revision_id AND j.cancel_requested_at IS NOT NULL)",
                    "Publication cancelled",
                )
                body += _raise(
                    "NEW.state='committed' AND NOT EXISTS(SELECT 1 FROM take t WHERE t.id=NEW.take_id AND t.status='ready')",
                    "Publication take not ready",
                )
                if action == "INSERT":
                    body += _raise(
                        "EXISTS(SELECT 1 FROM take t WHERE t.id=NEW.take_id AND t.status='ready') AND NOT EXISTS(SELECT 1 FROM snapshot_import WHERE song_id=NEW.song_id)",
                        "Ready take is immutable",
                    )
                for role in ("master", "listen", "peaks", "manifest"):
                    body += _raise(
                        importing
                        + f"NEW.state='committed' AND NOT EXISTS(SELECT 1 FROM publication_intent_revision r WHERE r.id=NEW.active_revision_id AND (SELECT count(*) FROM asset a WHERE a.subject_type='take' AND a.subject_id=NEW.take_id AND a.role='{role}')=1 AND EXISTS(SELECT 1 FROM asset a WHERE a.subject_type='take' AND a.subject_id=NEW.take_id AND a.role='{role}' AND a.path=substr(json_extract(r.package,'$.{role}.path'),6) AND a.sha256=json_extract(r.package,'$.{role}.sha256') AND a.bytes=json_extract(r.package,'$.{role}.bytes') AND a.media_type=json_extract(r.package,'$.{role}.media_type')))",
                        "Publication assets mismatch",
                    )
            else:
                body += _raise(
                    "NOT EXISTS(SELECT 1 FROM publication_intent i JOIN cpu_execution c ON c.id=NEW.cpu_execution_id WHERE i.id=NEW.intent_id AND i.owner_id=NEW.owner_id AND i.song_id=NEW.song_id AND i.take_id=NEW.take_id AND i.output_index=NEW.output_index AND i.seed=NEW.seed AND c.job_id=NEW.post_job_id AND c.owner_id=NEW.owner_id AND EXISTS(SELECT 1 FROM json_each(c.plan,'$.takes') e WHERE json_extract(e.value,'$.authority.winning_attempt_id')=NEW.winning_attempt_id AND json_extract(e.value,'$.authority.generation_job_id')=NEW.generation_job_id AND json_extract(e.value,'$.authority.winning_ordinal')=NEW.winning_ordinal AND json_extract(e.value,'$.authority.terminal_seq')=NEW.terminal_seq AND json_extract(e.value,'$.authority.terminal_sha256')=NEW.terminal_sha256 AND json_extract(e.value,'$.authority.provenance_sha256')=NEW.provenance_sha256 AND json_extract(e.value,'$.authority.take_id')=NEW.take_id AND json_extract(e.value,'$.authority.output_index')=NEW.output_index AND (json_extract(e.value,'$.authority')->'$.seed')=NEW.seed AND json_extract(e.value,'$.source.sha256')=NEW.source_sha256))",
                    "Revision authority mismatch",
                )
                body += _raise(
                    "NEW.stage_path IS NOT 'songs/'||NEW.song_id||'/takes/.pending-'||NEW.cpu_execution_id||'/'||NEW.take_id OR NEW.final_path IS NOT 'songs/'||NEW.song_id||'/takes/'||NEW.take_id",
                    "Publication path mismatch",
                )
                body += _json_guard("NEW.package")
                body += _raise(
                    "(NEW.package IS NULL)!=(NEW.package_sha256 IS NULL) OR (NEW.package IS NOT NULL AND NOT coalesce(("
                    + _schema(PreparedPackage, "NEW.package")
                    + "),0))",
                    "Invalid publication package",
                )
                comparisons = [
                    f"json_extract(NEW.package,'$.authority.{key}') IS NOT NEW.{key}"
                    for key in PublicationAuthority.model_fields
                    if key != "seed"
                ]
                comparisons.append("(NEW.package->'$.authority.seed') IS NOT NEW.seed")
                body += _raise(
                    "NEW.package IS NOT NULL AND (" + " OR ".join(comparisons) + ")",
                    "Package authority mismatch",
                )
                for role, name_suffix, media in (
                    ("master", "master.flac", "audio/flac"),
                    ("listen", "listen.mp3", "audio/mpeg"),
                    ("peaks", "peaks.json", "application/json"),
                    ("manifest", "manifest.json", "application/json"),
                ):
                    body += _raise(
                        f"NEW.package IS NOT NULL AND (json_extract(NEW.package,'$.{role}.path') IS NOT 'data/'||NEW.final_path||'/{name_suffix}' OR json_extract(NEW.package,'$.{role}.media_type') IS NOT '{media}')",
                        "Package final path mismatch",
                    )
            if action == "INSERT":
                body += _raise(
                    f"EXISTS(SELECT 1 FROM {name} WHERE id=NEW.id)",
                    "Immutable publication identity",
                )
            if action == "UPDATE":
                mutable = {"updated_at", "deleted_at"}
                if name == "cpu_execution":
                    mutable |= {
                        "state",
                        "revision",
                        "outcome",
                        "error_code",
                        "finished_at",
                        *PRIVATE_FIELDS,
                    }
                elif name == "publication_intent":
                    mutable |= {
                        "state",
                        "revision",
                        "active_revision_id",
                        "error_code",
                        "committed_at",
                    }
                else:
                    mutable |= {"package", "package_sha256", "error_code"}
                fixed = set(LEGACY_TABLES[name].columns.keys()) - mutable
                body += _raise(
                    " OR ".join(f"NEW.{key} IS NOT OLD.{key}" for key in sorted(fixed)),
                    "Immutable publication content",
                )
                if name == "publication_intent_revision":
                    body += _raise(
                        "(OLD.package IS NOT NULL AND (NEW.package IS NOT OLD.package OR NEW.package_sha256 IS NOT OLD.package_sha256)) OR (OLD.error_code IS NOT NULL AND NEW.error_code IS NOT OLD.error_code)",
                        "Immutable prepared package",
                    )
                    body += _raise(
                        "OLD.error_code IS NOT NULL AND NEW.package IS NOT OLD.package",
                        "Immutable failed revision",
                    )
                else:
                    states = CPU_STATES if name == "cpu_execution" else INTENT_STATES
                    transitions = " OR ".join(
                        f"(OLD.state='{old}' AND NEW.state IN ({','.join(repr(s) for s in sorted(allowed))}))"
                        for old, allowed in states.items()
                        if allowed
                    )
                    changed = " OR ".join(
                        f"NEW.{key} IS NOT OLD.{key}"
                        for key in sorted(
                            mutable - {"revision", "updated_at", "deleted_at"}
                        )
                    )
                    body += _raise(
                        f"NEW.revision<OLD.revision OR NEW.revision>OLD.revision+1 OR (({changed}) AND NEW.revision!=OLD.revision+1)",
                        "Stale publication CAS",
                    )
                    body += _raise(
                        f"NEW.state!=OLD.state AND NOT ({transitions})",
                        "Illegal publication transition",
                    )
                    if name == "publication_intent":
                        body += _raise(
                            "OLD.active_revision_id IS NOT NULL AND NEW.active_revision_id IS NOT OLD.active_revision_id AND (OLD.state NOT IN ('failed','cancelled') OR NEW.state!='reserved' OR EXISTS(SELECT 1 FROM take WHERE id=OLD.take_id AND status NOT IN ('failed','cancelled')) OR EXISTS(SELECT 1 FROM publication_intent_revision WHERE intent_id=OLD.id AND package IS NOT NULL))",
                            "Cannot replace published revision",
                        )
            connection.exec_driver_sql(
                f"CREATE TRIGGER durable_{name}_{action.lower()} BEFORE {action} ON {name} BEGIN {body} END"
            )
        for action in ("INSERT", "UPDATE", "DELETE"):
            sides = (
                ["OLD", "NEW"]
                if action == "UPDATE"
                else ["OLD"]
                if action == "DELETE"
                else ["NEW"]
            )
            selectors = []
            for side in sides:
                selectors.append(
                    f"SELECT song_id FROM job WHERE id={side}.job_id"
                    if name == "cpu_execution"
                    else f"SELECT {side}.song_id"
                )
                selectors.append(
                    f"SELECT root_id FROM snapshot_member WHERE entity_type='{name}' AND entity_id={side}.id"
                )
            support = " OR ".join(
                f"EXISTS(SELECT 1 FROM song WHERE is_dependency_only=1 AND id IN ({query}) AND NOT EXISTS(SELECT 1 FROM snapshot_import WHERE song_id=song.id))"
                for query in selectors
            )
            connection.exec_driver_sql(
                f"CREATE TRIGGER durable_{name}_support_{action.lower()} BEFORE {action} ON {name} WHEN {support} BEGIN SELECT RAISE(ABORT,'Support project requires validated import or promotion'); END"
            )
            connection.exec_driver_sql(
                f"CREATE TRIGGER durable_{name}_dirty_{action.lower()} AFTER {action} ON {name} BEGIN UPDATE snapshot_clock SET revision=revision+1 WHERE id=1; UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE is_dependency_only=0 AND id IN ({' UNION '.join(selectors)}); END"
            )
        connection.exec_driver_sql(
            f"CREATE TRIGGER durable_{name}_history BEFORE DELETE ON {name} BEGIN SELECT RAISE(ABORT,'Immutable publication history'); END"
        )
    connection.exec_driver_sql(
        "CREATE TRIGGER durable_ready_take BEFORE UPDATE ON take WHEN EXISTS(SELECT 1 FROM publication_intent WHERE take_id=OLD.id AND state='committed') BEGIN SELECT RAISE(ABORT,'Ready take is immutable') WHERE NEW.status!='ready' OR NEW.error_code IS NOT OLD.error_code OR NEW.duration_s IS NOT OLD.duration_s OR NEW.sample_rate IS NOT OLD.sample_rate OR NEW.model_id IS NOT OLD.model_id OR NEW.model_version IS NOT OLD.model_version OR NEW.params IS NOT OLD.params OR NEW.derivation IS NOT OLD.derivation OR NEW.root_id IS NOT OLD.root_id; END"
    )
    for action in ("INSERT", "UPDATE", "DELETE"):
        side = "NEW" if action == "INSERT" else "OLD"
        condition = f"{side}.subject_type='take' AND {side}.role IN ('master','listen','peaks','manifest') AND EXISTS(SELECT 1 FROM publication_intent i WHERE i.take_id={side}.subject_id AND i.state='committed')"
        if action == "INSERT":
            condition += " AND NOT EXISTS(SELECT 1 FROM snapshot_import WHERE song_id=(SELECT song_id FROM take WHERE id=NEW.subject_id))"
        connection.exec_driver_sql(
            f"CREATE TRIGGER durable_ready_asset_{action.lower()} BEFORE {action} ON asset WHEN {condition} BEGIN SELECT RAISE(ABORT,'Ready asset is immutable'); END"
        )
    for action in ("INSERT", "UPDATE"):
        body = _json_guard("NEW.provenance")
        body += _raise(
            "(NEW.provenance IS NULL)!=(NEW.provenance_sha256 IS NULL)",
            "Provenance pair mismatch",
        )
        body += _raise(
            "NEW.provenance_sha256 IS NOT NULL AND (length(NEW.provenance_sha256)!=64 OR NEW.provenance_sha256 GLOB '*[^a-f0-9]*')",
            "Invalid provenance SHA",
        )
        body += _raise(
            "NEW.provenance IS NOT NULL AND (NOT coalesce(("
            + _schema(CapturedProvenance, "NEW.provenance")
            + "),0) OR json_extract(NEW.provenance,'$.engine_id') IS NOT NEW.engine_id OR json_extract(NEW.provenance,'$.task') IS NOT json_extract(NEW.engine_request,'$.task') OR json_extract(NEW.provenance,'$.load.model_id') IS NOT NEW.model_id OR json_extract(NEW.provenance,'$.load.mode') IS NOT NEW.mode)",
            "Provenance authority mismatch",
        )
        if action == "UPDATE":
            body += _raise(
                "OLD.provenance IS NOT NULL AND (NEW.provenance IS NOT OLD.provenance OR NEW.provenance_sha256 IS NOT OLD.provenance_sha256)",
                "Immutable captured provenance",
            )
        body += _raise(
            "EXISTS(SELECT 1 FROM cpu_execution c WHERE c.job_id=NEW.job_id AND c.ordinal=NEW.ordinal)",
            "Mixed CPU ordinal",
        )
        connection.exec_driver_sql(
            f"CREATE TRIGGER durable_provenance_{action.lower()} BEFORE {action} ON job_attempt BEGIN {body} END"
        )
    # Los datos musicales y las autoridades referenciadas no pueden contradecirse.
    for table, columns, predicate in (
        (
            "take",
            "song_id,owner_id,seed,variant_index,job_id",
            "r.take_id=OLD.id AND (NEW.song_id!=r.song_id OR NEW.owner_id!=r.owner_id OR NEW.seed!=r.seed OR NEW.variant_index!=r.output_index OR (NEW.job_id!=OLD.job_id AND i.state NOT IN ('failed','cancelled')) )",
        ),
        (
            "job",
            "song_id,owner_id,task,lane,engine_id,model_id",
            "(r.post_job_id=OLD.id AND (NEW.song_id!=r.song_id OR NEW.owner_id!=r.owner_id OR NEW.task!='post.audio' OR NEW.lane!='cpu' OR NEW.engine_id IS NOT NULL OR NEW.model_id IS NOT NULL)) OR (r.generation_job_id=OLD.id AND (NEW.song_id!=r.song_id OR NEW.owner_id!=r.owner_id OR NEW.task!=OLD.task))",
        ),
        (
            "job_attempt",
            "last_seq,status,terminal,provenance,provenance_sha256",
            "r.winning_attempt_id=OLD.id AND (NEW.last_seq!=r.terminal_seq OR NEW.status!='succeeded' OR NEW.terminal IS NOT OLD.terminal OR NEW.provenance IS NOT OLD.provenance OR NEW.provenance_sha256!=r.provenance_sha256)",
        ),
    ):
        connection.exec_driver_sql(
            f"CREATE TRIGGER durable_parent_{table} BEFORE UPDATE OF {columns} ON {table} BEGIN SELECT RAISE(ABORT,'Frozen publication authority') WHERE EXISTS(SELECT 1 FROM publication_intent_revision r JOIN publication_intent i ON i.id=r.intent_id WHERE {predicate}); END"
        )
    connection.exec_driver_sql(
        "UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE is_dependency_only=0"
    )


def uninstall(connection):
    names = (
        connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'durable_%'"
        )
        .scalars()
        .all()
    )
    for name in names:
        connection.exec_driver_sql(f'DROP TRIGGER "{name}"')
    connection.exec_driver_sql(
        "DELETE FROM snapshot_member WHERE entity_type IN ('cpu_execution','publication_intent','publication_intent_revision')"
    )
    original = connection.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='entity_song'"
    ).scalar_one()
    connection.exec_driver_sql("DROP VIEW entity_song")
    connection.exec_driver_sql(original.split(" UNION ALL SELECT 'cpu_execution'")[0])
