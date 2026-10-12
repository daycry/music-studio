"""Guardas aditivas y revisión de lectura; no reescribe revisiones publicadas."""

import json
from pathlib import Path

from .initial_invariants import MEMBERS
from .legacy_m1_registry import TABLES

# Sólo relaciones que transmiten pertenencia, nunca referencias globales legales.
PARENTS = {
    "lyrics_version": ("song", "song_id"),
    "take": ("song", "song_id"),
    "artwork": ("song", "song_id"),
    "video_project": ("song", "song_id"),
    "export": ("song", "song_id"),
    "job": ("song", "song_id"),
    "analysis": ("take", "take_id"),
    "shot": ("video_project", "video_project_id"),
    "render": ("video_project", "video_project_id"),
    "video_character": ("video_project", "video_project_id"),
    "shot_version": ("shot", "shot_id"),
    "job_dependency": ("job", "job_id"),
}


def parent_song(table, side):
    if table == "song":
        return f"{side}.id"
    if table in PARENTS:
        parent, column = PARENTS[table]
        return f"(SELECT song_id FROM entity_song WHERE type='{parent}' AND id={side}.{column})"
    if table == "asset":
        return f"(SELECT song_id FROM entity_song WHERE type={side}.subject_type AND id={side}.subject_id)"
    if table == "lineage_edge":
        return f"(SELECT song_id FROM entity_song WHERE type={side}.child_type AND id={side}.child_id)"
    return "NULL"


def install(connection):
    connection.exec_driver_sql(
        "CREATE TABLE snapshot_clock (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL CHECK(revision>=0))"
    )
    connection.exec_driver_sql("INSERT INTO snapshot_clock VALUES(1,0)")
    # Vacía fuera de restore; las excepciones son transaccionales, por canción.
    connection.exec_driver_sql(
        "CREATE TABLE snapshot_import (song_id TEXT PRIMARY KEY REFERENCES song(id) DEFERRABLE INITIALLY DEFERRED)"
    )
    for table in MEMBERS:
        if table in {"setting", "provider", "preset"}:
            continue
        for action in ("INSERT", "UPDATE", "DELETE"):
            columns = ""
            if table == "song" and action == "UPDATE":
                columns = " OF " + ",".join(
                    '"' + c.name + '"'
                    for c in TABLES["song"].columns
                    if c.name not in {"snapshot_dirty", "snapshot_generation"}
                )
            connection.exec_driver_sql(
                f'CREATE TRIGGER fix2_clock_{table}_{action.lower()} AFTER {action}{columns} ON "{table}" BEGIN UPDATE snapshot_clock SET revision=revision+1 WHERE id=1; END'
            )
        if table not in PARENTS and table not in {"asset", "lineage_edge", "song"}:
            continue
        for action in ("INSERT", "UPDATE", "DELETE"):
            sides = (
                ["NEW"]
                if action == "INSERT"
                else ["OLD"]
                if action == "DELETE"
                else ["OLD", "NEW"]
            )
            expressions = []
            for side in sides:
                expressions.append(parent_song(table, side))
                if table == "lineage_edge":
                    expressions.append(
                        f"(SELECT song_id FROM entity_song WHERE type={side}.parent_type AND id={side}.parent_id)"
                    )
            conditions = [
                f"EXISTS(SELECT 1 FROM song s WHERE s.id={expr} AND s.is_dependency_only=1 AND NOT EXISTS(SELECT 1 FROM snapshot_import i WHERE i.song_id=s.id))"
                for expr in expressions
            ]
            if table == "song" and action == "UPDATE":
                # Dirty/generation bookkeeping and validated promotion remain legal.
                continue
            connection.exec_driver_sql(
                f"CREATE TRIGGER fix2_support_{table}_{action.lower()} BEFORE {action} ON \"{table}\" WHEN {' OR '.join(conditions)} BEGIN SELECT RAISE(ABORT,'Support project requires validated import or promotion'); END"
            )

    for action in ("INSERT", "UPDATE"):
        connection.exec_driver_sql(
            f"CREATE TRIGGER fix2_shot_selection_{action.lower()} AFTER {action} ON shot BEGIN SELECT RAISE(ABORT,'Invalid shot selection') WHERE EXISTS(SELECT 1 FROM shot_version WHERE id=NEW.current_version_id AND shot_id!=NEW.id); END"
        )
    connection.exec_driver_sql(
        "CREATE TRIGGER fix2_version_selection AFTER UPDATE OF shot_id ON shot_version BEGIN SELECT RAISE(ABORT,'Invalid shot selection') WHERE EXISTS(SELECT 1 FROM shot WHERE current_version_id=NEW.id AND id!=NEW.shot_id); END"
    )
    connection.exec_driver_sql(
        "CREATE TRIGGER fix2_version_selection_insert AFTER INSERT ON shot_version BEGIN SELECT RAISE(ABORT,'Invalid shot selection') WHERE EXISTS(SELECT 1 FROM shot WHERE current_version_id=NEW.id AND id!=NEW.shot_id); END"
    )

    relations = json.loads(
        Path(__file__).with_name("initial_relations.json").read_text(encoding="utf-8")
    )
    # Membership descendants are bounded by fixed table paths (depth <= 4).
    for table in (*PARENTS, "song", "asset"):
        affected = {table: "SELECT NEW.id AS id"}
        frontier = [table]
        while frontier:
            parent = frontier.pop()
            for child, (kind, column) in PARENTS.items():
                if kind == parent and child not in affected:
                    affected[child] = (
                        f'SELECT id FROM "{child}" WHERE "{column}" IN ({affected[parent]})'
                    )
                    frontier.append(child)
        if table != "asset":
            affected["asset"] = " UNION ".join(
                f"SELECT id FROM asset WHERE subject_type='{kind}' AND subject_id IN ({ids})"
                for kind, ids in affected.items()
            )
        body = ""
        for child, references in relations.items():
            for column, parent in references:
                if child not in affected and parent not in affected:
                    continue
                clauses = []
                if child in affected:
                    clauses.append(f"c.id IN ({affected[child]})")
                if parent in affected:
                    clauses.append(f'c."{column}" IN ({affected[parent]})')
                body += f"SELECT RAISE(ABORT,'Invalid transitive reference ownership or song') WHERE EXISTS(SELECT 1 FROM \"{child}\" c JOIN entity_song ce ON ce.type='{child}' AND ce.id=c.id JOIN entity_song pe ON pe.type='{parent}' AND pe.id=c.\"{column}\" WHERE ({' OR '.join(clauses)}) AND (ce.owner_id!=pe.owner_id OR (ce.song_id IS NOT NULL AND pe.song_id IS NOT NULL AND ce.song_id!=pe.song_id)));"
        column = PARENTS.get(
            table, ("", "subject_id" if table == "asset" else "owner_id")
        )[1]
        columns = ",subject_type" if table == "asset" else ""
        connection.exec_driver_sql(
            f'CREATE TRIGGER fix2_inverse_{table} AFTER UPDATE OF "{column}",owner_id{columns} ON "{table}" BEGIN {body} END'
        )


def uninstall(connection):
    names = (
        connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'fix2_%'"
        )
        .scalars()
        .all()
    )
    for name in names:
        connection.exec_driver_sql(f'DROP TRIGGER "{name}"')
    connection.exec_driver_sql("DROP TABLE snapshot_import")
    connection.exec_driver_sql("DROP TABLE snapshot_clock")
