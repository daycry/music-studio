"""Proyección portable de filas; SQLite sigue siendo la fuente de verdad."""

import hashlib
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from threading import RLock

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from pydantic import BaseModel
from sqlalchemy import Column, Float, Integer, MetaData, Table, select
from sqlalchemy.exc import SQLAlchemyError

from .closure_rows import MemoryRows, SQLRows
from .db import confine_path
from .migrations.cpu_publication_invariants import (
    PRIVATE_FIELDS,
    TABLE_NAMES,
    validate_rows,
)
from .migrations.job_attempt_invariants import validate_attempt
from .migrations.legacy_m1_registry import TABLES as LEGACY_TABLES

_locks = defaultdict(RLock)
_reconcile_lock = RLock()
TABLES = {
    name: table
    for name, table in LEGACY_TABLES.items()
    if name not in {"setting", "provider", "preset"}
}
SCHEMA = Path(__file__).parent / "models" / "song-v1.schema.json"
TIMELINE_SCHEMA = Path(__file__).parent / "models" / "timeline-v1.schema.json"
LOCAL_FIELDS = {
    "is_dependency_only",
    "snapshot_dirty",
    "snapshot_generation",
    *PRIVATE_FIELDS,
}
CHILDREN = {
    "song": [
        ("lyrics_version", "song_id"),
        ("take", "song_id"),
        ("artwork", "song_id"),
        ("video_project", "song_id"),
        ("export", "song_id"),
        ("job", "song_id"),
        ("publication_intent", "song_id"),
    ],
    "video_project": [
        ("shot", "video_project_id"),
        ("render", "video_project_id"),
        ("video_character", "video_project_id"),
    ],
    "shot": [("shot_version", "shot_id")],
    "character": [("character_ref", "character_id")],
    "job": [
        ("job_dependency", "job_id"),
        ("job_attempt", "job_id"),
        ("cpu_execution", "job_id"),
        ("publication_intent_revision", "post_job_id"),
    ],
    "take": [("publication_intent", "take_id")],
    "publication_intent": [("publication_intent_revision", "intent_id")],
}


def canonical_row(row):
    return {
        key: value.model_dump(mode="json") if isinstance(value, BaseModel) else value
        for key, value in row.items()
        if key not in LOCAL_FIELDS
        and not (
            value is None
            and (
                key in {"provenance", "provenance_sha256"}
                or key == "error_code"
                and "variant_index" in row
            )
        )
    }


def digest(row, table):
    row = canonical_row(row)
    for column in TABLES[table].columns:
        value = row.get(column.name)
        if value is not None and column.name in row:
            if isinstance(column.type, Float):
                row[column.name] = float(value)
            elif isinstance(column.type, Integer) or column.name == "seed":
                row[column.name] = int(value)
    return hashlib.sha256(
        json.dumps(
            row,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def closure(
    song_id, fetch, lookup, batch=None, *, include_attempts=True, available_tables=None
):
    """Cierre dirigido; fetch/lookup consultan identidades o índices de relación."""
    selected = {}
    pending = [("song", song_id)]
    while pending:
        frontier = set(pending) - selected.keys()
        pending = []
        if batch is not None:
            batch.fetch_many(frontier)
        requests = []
        for key in frontier:
            table, identifier = key
            row = fetch(table, identifier)
            if row is None:
                raise ValueError("Incomplete reference closure")
            selected[key] = row
            for column in TABLES[table].columns:
                for fk in column.foreign_keys:
                    value = row.get(column.name)
                    if value is not None:
                        pending.append((fk.column.table.name, value))
            for side in ("child", "parent") if table == "lineage_edge" else ():
                pending.append((row[side + "_type"], row[side + "_id"]))
            if table == "asset":
                if row["subject_type"] in {"lora", "cli_run"}:
                    raise ValueError("External asset validator unavailable")
                pending.append((row["subject_type"], row["subject_id"]))
            children = (
                CHILDREN.get(table, [])
                if table != "song" or identifier == song_id
                else []
            )
            if table == "take" and row["song_id"] == song_id:
                children = [*children, ("analysis", "take_id")]
            requests.extend(
                (child, {column: identifier})
                for child, column in children
                if (include_attempts or child != "job_attempt")
                and (available_tables is None or child in available_tables)
            )
            requests.extend(
                [
                    ("asset", {"subject_type": table, "subject_id": identifier}),
                    ("lineage_edge", {"child_type": table, "child_id": identifier}),
                ]
            )
        if batch is not None:
            batch.lookup_many(requests)
        for name, filters in requests:
            pending.extend((name, row["id"]) for row in lookup(name, filters))
    return selected


def membership(key, index, cache=None):
    if cache is not None and key in cache:
        return cache[key]
    result = _membership(key, index, cache)
    if cache is not None:
        cache[key] = result
    return result


def _membership(key, index, cache):
    table, identifier = key
    row = index[key]
    if table == "song":
        return identifier
    if "song_id" in row:
        return row["song_id"]
    parent = {
        "analysis": ("take", "take_id"),
        "shot": ("video_project", "video_project_id"),
        "video_character": ("video_project", "video_project_id"),
        "shot_version": ("shot", "shot_id"),
        "render": ("video_project", "video_project_id"),
        "job_dependency": ("job", "job_id"),
        "job_attempt": ("job", "job_id"),
        "cpu_execution": ("job", "job_id"),
    }.get(table)
    if parent:
        return membership((parent[0], row[parent[1]]), index, cache)
    if table == "asset":
        return membership((row["subject_type"], row["subject_id"]), index, cache)
    if table == "lineage_edge":
        return membership((row["child_type"], row["child_id"]), index, cache)
    return None


def reject_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {
                "api_key",
                "access_token",
                "authorization",
                "password",
                "secret",
                "engine_token",
            }:
                raise ValueError("Snapshot contains secret fields")
            reject_secrets(item)
    elif isinstance(value, list):
        for item in value:
            reject_secrets(item)


def ordered_dag(parents):
    remaining = {node: set(values) for node, values in parents.items()}
    order = []
    while remaining:
        ready = {node for node, values in remaining.items() if not values}
        if not ready:
            raise ValueError("Snapshot dependency cycle")
        order.extend(sorted(ready))
        remaining = {
            node: values - ready
            for node, values in remaining.items()
            if node not in ready
        }
    return order


def validate_timeline(timeline, shots, characters):
    json.dumps(timeline, allow_nan=False)
    Draft202012Validator(
        json.loads(TIMELINE_SCHEMA.read_text(encoding="utf-8"))
    ).validate(timeline)
    keys = set()
    for shot in timeline["shots"]:
        if (
            shot["key"] in keys
            or not 0 <= shot["t0"] < shot["t1"] <= timeline["duration_s"]
        ):
            raise ValueError("Invalid timeline intervals or keys")
        if shot["key"] not in shots or not set(shot["characters"]) <= characters:
            raise ValueError("Invalid timeline references")
        keys.add(shot["key"])
    if keys != shots:
        raise ValueError("Incomplete timeline shots")
    for title in timeline["titles"]:
        if not 0 <= title["t0"] < title["t1"] <= timeline["duration_s"]:
            raise ValueError("Invalid timeline title interval")


def validate(document, data_dir):
    json.dumps(document, allow_nan=False)
    reject_secrets(document)
    Draft202012Validator(
        json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()
    ).validate(document)
    root = confine_path(data_dir)
    primary = document["rows"]
    dependencies = document.get("dependencies", {}).get(
        "rows", {name: [] for name in TABLES}
    )
    union = {
        name: primary.get(name, []) + dependencies.get(name, []) for name in TABLES
    }
    for table, rows in union.items():
        seen = set()
        for row in rows:
            if row["id"] in seen:
                raise ValueError("Duplicate row")
            seen.add(row["id"])
            if table in {"asset", "upload"}:
                relative = Path(row["path"])
                if (
                    relative.is_absolute()
                    or ".." in relative.parts
                    or "\\" in row["path"]
                    or ":" in row["path"]
                    or not (root / relative).resolve().is_relative_to(root)
                ):
                    raise ValueError("Unsafe asset path")
                if any(
                    part.is_symlink()
                    for part in [root / relative, *(root / relative).parents]
                    if part.is_relative_to(root)
                ):
                    raise ValueError("Asset path symlink")
    songs = primary["song"]
    if len(songs) != 1 or songs[0]["id"] != document["song_id"]:
        raise ValueError("Invalid song closure")
    index = {(table, row["id"]): row for table, rows in union.items() for row in rows}
    owner = songs[0]["owner_id"]
    for table, rows in union.items():
        for row in rows:
            if table == "job_attempt":
                validate_attempt(row)
            if row["owner_id"] != owner:
                raise ValueError("Mixed owners")

            for column in TABLES[table].columns:
                for fk in column.foreign_keys:
                    value = row.get(column.name)
                    if value is not None and (fk.column.table.name, value) not in index:
                        raise ValueError("Incomplete reference closure")
            if (
                table == "asset"
                and (row["subject_type"], row["subject_id"]) not in index
            ):
                raise ValueError("Incomplete asset subject")
            if table == "lineage_edge":
                for side in ("child", "parent"):
                    if (row[side + "_type"], row[side + "_id"]) not in index:
                        raise ValueError("Incomplete lineage subject")
    try:
        validate_rows(index)
    except KeyError as error:
        raise ValueError("Incomplete publication reference closure") from error
    shot_keys = defaultdict(set)
    video_characters = defaultdict(set)
    for row in union["shot"]:
        shot_keys[row["video_project_id"]].add(row["key"])
        if (
            row["current_version_id"] is not None
            and index[("shot_version", row["current_version_id"])]["shot_id"]
            != row["id"]
        ):
            raise ValueError("Invalid shot selection")
    for row in union["video_character"]:
        video_characters[row["video_project_id"]].add(row["character_id"])
    for video in union["video_project"]:
        shots = shot_keys[video["id"]]
        characters = video_characters[video["id"]]
        validate_timeline(video["timeline"], shots, characters)
    parents = {key: set() for key in index}
    for edge in union["lineage_edge"]:
        parents[(edge["child_type"], edge["child_id"])].add(
            (edge["parent_type"], edge["parent_id"])
        )
    ordered_dag(parents)
    take_parents = {row["id"]: set() for row in union["take"]}
    for edge in union["lineage_edge"]:
        if edge["child_type"] == edge["parent_type"] == "take":
            take_parents[edge["child_id"]].add(edge["parent_id"])
    roots = {}
    for identifier in ordered_dag(take_parents):
        roots[identifier] = min(
            (roots[parent] for parent in take_parents[identifier]), default=identifier
        )
        if index[("take", identifier)]["root_id"] != roots[identifier]:
            raise ValueError("Invalid take root")
    jobs = {row["id"]: set() for row in union["job"]}
    for edge in union["job_dependency"]:
        jobs[edge["job_id"]].add(edge["depends_on_job_id"])
    ordered_dag(jobs)

    memberships = {}
    for key, row in index.items():
        table = key[0]
        subject_song = membership(key, index, memberships)
        if table == "asset" and row["subject_type"] in {"lora", "cli_run"}:
            raise ValueError("External asset validator unavailable")
        for column in TABLES[table].columns:
            for fk in column.foreign_keys:
                value = row.get(column.name)
                if value is None:
                    continue
                parent_key = (fk.column.table.name, value)
                parent_song = membership(parent_key, index, memberships)
                # song's own selections must belong to that exact song.
                if (
                    subject_song is not None
                    and parent_song is not None
                    and subject_song != parent_song
                ):
                    raise ValueError("Invalid selected reference belonging")
        if table == "lineage_edge":
            parent_song = membership(
                (row["parent_type"], row["parent_id"]), index, memberships
            )
            if (
                subject_song is not None
                and parent_song is not None
                and subject_song != parent_song
            ):
                raise ValueError("Cross-song lineage")

    access = MemoryRows(union, CHILDREN)
    selected = closure(
        document["song_id"],
        access.fetch,
        access.lookup,
    )
    if selected.keys() != index.keys():
        raise ValueError("Extraneous snapshot rows")
    primary_keys = {(name, row["id"]) for name, rows in primary.items() for row in rows}
    for key in index:
        expected_primary = membership(key, index, memberships) in {
            None,
            document["song_id"],
        }
        actual_primary = key in primary_keys
        if actual_primary != expected_primary:
            raise ValueError("Invalid snapshot section")
    if "dependencies" in document:
        expected = {
            "source_root_id": document["song_id"],
            "owner_id": owner,
            "row_digests": {
                table + "/" + row["id"]: digest(row, table)
                for table, rows in dependencies.items()
                for row in rows
            },
        }
        if document["dependencies"]["provenance"] != expected:
            raise ValueError("Invalid dependency provenance")


def project(engine, song_id):
    with engine.connect() as connection, connection.begin():
        return _project(connection, song_id)


def _project(connection, song_id):
    support = connection.execute(
        select(TABLES["song"].c.is_dependency_only).where(
            TABLES["song"].c.id == song_id
        )
    ).scalar_one_or_none()
    if support is None:
        raise ValueError("Unknown song")
    if support:
        raise ValueError("Cannot project support as root")

    tables = _capability_tables(connection)
    access = SQLRows(connection, tables, canonical_row)
    selected = closure(
        song_id,
        access.fetch,
        access.lookup,
        access,
        include_attempts="job_attempt" in tables,
        available_tables=tables,
    )
    rows = {name: [] for name in TABLES}
    dependencies = {name: [] for name in TABLES}
    memberships = {}
    for key, row in sorted(selected.items()):
        target = (
            rows
            if membership(key, selected, memberships) in {None, song_id}
            else dependencies
        )
        target[key[0]].append(row)
    result = {"version": 1, "song_id": song_id, "rows": rows}
    if any(dependencies.values()):
        result["dependencies"] = {
            "rows": dependencies,
            "provenance": {
                "source_root_id": song_id,
                "owner_id": selected[("song", song_id)]["owner_id"],
                "row_digests": {
                    table + "/" + row["id"]: digest(row, table)
                    for table, values in dependencies.items()
                    for row in values
                },
            },
        }
    return result


def _capability_tables(connection):
    """Une lecture bornée de capacités pour les colonnes réellement présentes."""
    names = {"job_attempt", "take", *TABLE_NAMES}
    available = defaultdict(set)
    for name, column in connection.exec_driver_sql(
        "SELECT m.name,p.name FROM sqlite_master m JOIN pragma_table_info(m.name) p WHERE m.type='table' AND m.name IN ('job_attempt','take','cpu_execution','publication_intent','publication_intent_revision')"
    ):
        available[name].add(column)
    tables = dict(TABLES)
    for name in names:
        if name not in available:
            tables.pop(name, None)
        else:
            original = TABLES[name]
            tables[name] = Table(
                name,
                MetaData(),
                *(
                    Column(c.name, c.type)
                    for c in original.columns
                    if c.name in available[name]
                ),
            )
    return tables


def publish(engine, song_id, data_dir):
    with _locks[(str(engine.url), song_id)]:
        with engine.connect() as connection, connection.begin():
            revision = connection.exec_driver_sql(
                "SELECT revision FROM snapshot_clock WHERE id=1"
            ).scalar_one()
            generation = connection.exec_driver_sql(
                "SELECT snapshot_generation FROM song WHERE id=? AND is_dependency_only=0",
                (song_id,),
            ).scalar_one_or_none()
            if generation is None:
                raise ValueError("Cannot publish support or unknown song")
            document = _project(connection, song_id)
        validate(document, data_dir)
        root = confine_path(data_dir)
        directory = root / "songs" / song_id
        if any(
            part.is_symlink() for part in (Path(data_dir), root / "songs", directory)
        ):
            raise ValueError("Snapshot directory symlink")
        if not directory.resolve().is_relative_to(root):
            raise ValueError("Unsafe snapshot path")
        directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".song-", suffix=".json", dir=directory
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(
                    document,
                    stream,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                )
                stream.flush()
                os.fsync(stream.fileno())
            target = directory / "song.json"
            if target.is_symlink():
                raise ValueError("Snapshot symlink")
            os.replace(temporary, target)
            with engine.begin() as connection:
                # La escritura adquiere el bloqueo SQLite antes de leer el CAS;
                # evita promover un snapshot WAL obsoleto tras otro escritor.
                connection.exec_driver_sql(
                    "UPDATE song SET snapshot_dirty=1 WHERE id=?", (song_id,)
                )
                current = connection.exec_driver_sql(
                    "SELECT snapshot_generation FROM song WHERE id=?", (song_id,)
                ).scalar_one()
                current_revision = connection.exec_driver_sql(
                    "SELECT revision FROM snapshot_clock WHERE id=1"
                ).scalar_one()
                if current == generation and current_revision == revision:
                    connection.exec_driver_sql(
                        "DELETE FROM snapshot_member WHERE root_id=?", (song_id,)
                    )
                    union = {
                        name: document["rows"].get(name, [])
                        + document.get("dependencies", {}).get("rows", {}).get(name, [])
                        for name in TABLES
                    }
                    members = [
                        (song_id, name, row["id"])
                        for name, values in union.items()
                        for row in values
                    ]
                    connection.exec_driver_sql(
                        "INSERT INTO snapshot_member(root_id,entity_type,entity_id) VALUES(?,?,?)",
                        members,
                    )
                    connection.exec_driver_sql(
                        "UPDATE song SET snapshot_dirty=0 WHERE id=? AND snapshot_generation=?",
                        (song_id, generation),
                    )
        finally:
            Path(temporary).unlink(missing_ok=True)


def reconcile(engine, data_dir, *, startup=False):
    """Reconcile one snapshot projection at a time per process.

    Session ``after_commit`` hooks can run concurrently from queue and HTTP
    workers.  Serialising the read/project/publish cycle prevents overlapping
    snapshot writers from contending with the durable queue CAS transactions.
    """
    with _reconcile_lock:
        return _reconcile(engine, data_dir, startup=startup)


def _reconcile(engine, data_dir, *, startup=False):
    if startup:
        with engine.connect() as connection:
            roots = list(
                connection.execute(
                    select(TABLES["song"].c.id).where(
                        TABLES["song"].c.is_dependency_only == False
                    )
                ).scalars()
            )
        for identifier in roots:
            try:
                target = Path(data_dir) / "songs" / identifier / "song.json"
                root = confine_path(data_dir)
                if not target.resolve().is_relative_to(root) or any(
                    part.is_symlink()
                    for part in (Path(data_dir), root / "songs", target.parent, target)
                ):
                    raise ValueError("Snapshot symlink")
                document = json.loads(target.read_text(encoding="utf-8"))
                validate(document, data_dir)
                if document != project(engine, identifier):
                    raise ValueError("Stale snapshot")
            except (OSError, ValueError, SQLAlchemyError, ValidationError):
                with engine.begin() as connection:
                    connection.exec_driver_sql(
                        "UPDATE song SET snapshot_dirty=1 WHERE id=?", (identifier,)
                    )
    with engine.connect() as connection:
        table = TABLES["song"]
        ids = list(
            connection.execute(
                select(table.c.id).where(
                    table.c.is_dependency_only == False, table.c.snapshot_dirty == True
                )
            ).scalars()
        )
    for identifier in ids:
        try:
            publish(engine, identifier, data_dir)
        except (OSError, ValueError, SQLAlchemyError, ValidationError):
            logger = getattr(engine, "studio_logger", None)
            if logger is not None:
                logger.error("snapshot.failed", extra={"song_id": identifier})


def restore(engine, document, data_dir):
    validate(document, data_dir)
    union = {
        name: [
            dict(row)
            for row in document["rows"].get(name, [])
            + document.get("dependencies", {}).get("rows", {}).get(name, [])
        ]
        for name in TABLES
    }
    for row in union["cpu_execution"]:
        if row["state"] in {"prepared", "running", "draining"}:
            row["state"] = "interrupted"
    for name in ("asset", "upload"):
        for source in union[name]:
            target = confine_path(data_dir) / source["path"]
            if target.exists():
                if not target.is_file():
                    raise ValueError("Existing media bytes conflict")
                with target.open("rb") as stream:
                    if (
                        hashlib.file_digest(stream, "sha256").hexdigest()
                        != source["sha256"]
                    ):
                        raise ValueError("Existing media bytes conflict")
    with engine.begin() as connection:
        # Adquirir el único escritor antes de leer colisiones: la caché y las
        # inserciones comparten la misma vista, incluso con otros escritores WAL.
        # No abre la excepción de soporte ni modifica la revisión de publicación.
        connection.exec_driver_sql(
            "UPDATE snapshot_clock SET revision=revision WHERE id=1"
        )
        owner = document["rows"]["song"][0]["owner_id"]
        owners = connection.execute(select(TABLES["user"].c.id)).scalars().all()
        if owners != [owner]:
            raise ValueError(
                "Owner collision; initialize with snapshot user before import"
            )
        # Validar todas las colisiones antes de abrir la excepción de soporte.
        existing_rows = {}
        for name, values in union.items():
            table = TABLES[name]
            cached = existing_rows[name] = {}
            ids = [source["id"] for source in values]
            for start in range(0, len(ids), 400):
                cached.update(
                    (row["id"], dict(row))
                    for row in connection.execute(
                        select(table).where(table.c.id.in_(ids[start : start + 400]))
                    ).mappings()
                )
            for source in values:
                existing = cached.get(source["id"])
                if existing is not None and canonical_row(existing) != source:
                    raise ValueError("Row collision")
        import_ids = [row["id"] for row in union["song"]]
        connection.exec_driver_sql(
            "INSERT INTO snapshot_import(song_id) VALUES(?)",
            [(identifier,) for identifier in import_ids],
        )
        ordered = (
            [
                name
                for name in union
                if name not in {"asset", "lineage_edge", *TABLE_NAMES}
            ]
            + list(TABLE_NAMES)
            + [
                "asset",
                "lineage_edge",
            ]
        )
        for name in ordered:
            rows = union[name]
            table = TABLES[name]
            for source in rows:
                row = dict(source)
                existing = existing_rows[name].get(row["id"])
                if existing is not None:
                    if name == "song" and row["id"] == document["song_id"]:
                        connection.exec_driver_sql(
                            "UPDATE song SET is_dependency_only=0 WHERE id=?",
                            (row["id"],),
                        )
                    continue
                if name == "song":
                    row["is_dependency_only"] = row["id"] != document["song_id"]
                if name == "take":
                    row["root_id"] = row["id"]
                connection.execute(table.insert().values(**row))
        roots = {row["id"]: row["root_id"] for row in union["take"]}
        ids = list(roots)
        table = TABLES["take"]
        for start in range(0, len(ids), 400):
            for identifier, actual in connection.execute(
                select(table.c.id, table.c.root_id).where(
                    table.c.id.in_(ids[start : start + 400])
                )
            ):
                if actual != roots[identifier]:
                    raise ValueError("Invalid imported root")
        connection.exec_driver_sql("DELETE FROM snapshot_import")
    publish(engine, document["song_id"], data_dir)


def restore_new(database, document, data_dir):
    """Inicializar exclusivamente un destino nuevo con el usuario original."""
    from .db import create_db_engine, migrate

    database = confine_path(database)
    if any(Path(str(database) + suffix).exists() for suffix in ("", "-wal", "-shm")):
        raise FileExistsError("Restore destination must be new")
    validate(document, data_dir)
    user = document["rows"]["user"]
    if len(user) != 1 or user[0]["id"] != user[0]["owner_id"]:
        raise ValueError("Invalid snapshot user")
    migrate(database, initial_user=user[0])
    engine = create_db_engine(database)
    try:
        restore(engine, document, data_dir)
    finally:
        engine.dispose()
