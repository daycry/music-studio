"""SQL congelado para las invariantes de la revisión 0001."""

import json
from pathlib import Path

SUBJECTS = {
    "song": "id",
    "take": "song_id",
    "lyrics_version": "song_id",
    "artwork": "song_id",
    "upload": "NULL",
    "character": "NULL",
    "shot_version": "(SELECT v.song_id FROM shot s JOIN video_project v ON v.id=s.video_project_id WHERE s.id=shot_id)",
    "render": "(SELECT song_id FROM video_project WHERE id=video_project_id)",
    "export": "song_id",
}

MEMBERS = dict(
    SUBJECTS,
    user="NULL",
    collection="NULL",
    analysis="(SELECT song_id FROM take WHERE id=take_id)",
    preset="NULL",
    video_project="song_id",
    video_character="(SELECT song_id FROM video_project WHERE id=video_project_id)",
    shot="(SELECT song_id FROM video_project WHERE id=video_project_id)",
    job="song_id",
    job_dependency="(SELECT song_id FROM job WHERE id=job_id)",
    character_ref="NULL",
    setting="NULL",
    provider="NULL",
)
MEMBERS["asset"] = (
    "CASE "
    + " ".join(
        f"WHEN subject_type='{table}' THEN (SELECT {column} FROM \"{table}\" WHERE id=subject_id)"
        for table, column in SUBJECTS.items()
    )
    + " END"
)
MEMBERS["lineage_edge"] = "NULL"
JSON_FIELDS = {
    "song": ["tags"],
    "take": ["params"],
    "lineage_edge": ["section_map"],
    "asset": ["meta"],
    "upload": ["meta"],
    "analysis": ["data"],
    "preset": ["payload"],
    "video_project": ["timeline"],
    "shot_version": ["focus_point"],
    "job": ["request", "telemetry"],
    "setting": ["value"],
    "provider": ["config"],
}


def install(connection):
    for table, columns in JSON_FIELDS.items():
        for action in ("INSERT", "UPDATE"):
            body = ""
            for column in columns:
                body += f"SELECT RAISE(ABORT,'Non-finite JSON number') WHERE CASE WHEN json_valid(NEW.\"{column}\") THEN EXISTS(SELECT 1 FROM json_tree(NEW.\"{column}\") WHERE type='real' AND abs(atom)>1.7976931348623157e308) ELSE 0 END;"
            connection.exec_driver_sql(
                f'CREATE TRIGGER finite_json_{table}_{action.lower()} BEFORE {action} ON "{table}" BEGIN {body} END'
            )
    connection.exec_driver_sql(
        "CREATE VIEW entity_song AS "
        + " UNION ALL ".join(
            f"SELECT '{table}' AS type,id,owner_id,{column} AS song_id FROM \"{table}\""
            for table, column in MEMBERS.items()
        )
    )
    relations = json.loads(
        Path(__file__).with_name("initial_relations.json").read_text(encoding="utf-8")
    )
    for table, references in relations.items():
        connection.exec_driver_sql(
            f"CREATE TRIGGER identity_{table} BEFORE UPDATE ON \"{table}\" BEGIN SELECT RAISE(ABORT,'Immutable identity') WHERE NEW.id != OLD.id OR NEW.owner_id != OLD.owner_id; END"
        )
        for action in ("INSERT", "UPDATE"):
            body = ""
            for column, parent in references:
                child_song = MEMBERS[table]
                # Evaluar la expresión del sujeto sobre la fila NEW, no sobre una fila vieja.
                if child_song == "id":
                    child_song = "NEW.id"
                elif child_song in {"song_id", "NULL"}:
                    child_song = "NEW.song_id" if child_song == "song_id" else "NULL"
                else:
                    child_song = f"(SELECT song_id FROM entity_song WHERE type='{table}' AND id=NEW.id)"
                body += f"SELECT RAISE(ABORT,'Invalid reference ownership or song') WHERE EXISTS(SELECT 1 FROM entity_song p WHERE p.type='{parent}' AND p.id=NEW.\"{column}\" AND (p.owner_id != NEW.owner_id OR (p.song_id IS NOT NULL AND {child_song} IS NOT NULL AND p.song_id != {child_song})));"
            for child, child_references in relations.items():
                for column, parent in child_references:
                    if parent == table:
                        body += f"SELECT RAISE(ABORT,'Invalid reverse reference ownership or song') WHERE EXISTS(SELECT 1 FROM \"{child}\" c JOIN entity_song ce ON ce.type='{child}' AND ce.id=c.id JOIN entity_song pe ON pe.type='{table}' AND pe.id=NEW.id WHERE c.\"{column}\"=NEW.id AND (ce.owner_id != pe.owner_id OR (ce.song_id IS NOT NULL AND pe.song_id IS NOT NULL AND ce.song_id != pe.song_id)));"
            connection.exec_driver_sql(
                f'CREATE TRIGGER references_{table}_{action.lower()} AFTER {action} ON "{table}" BEGIN {body} END'
            )
    for action in ("INSERT", "UPDATE"):
        body = ""
        for side in ("child", "parent"):
            body += f"SELECT RAISE(ABORT,'Unknown lineage subject') WHERE NEW.{side}_type NOT IN ({','.join(repr(t) for t in SUBJECTS)});"
            for table in SUBJECTS:
                body += f"SELECT RAISE(ABORT,'Invalid lineage owner or subject') WHERE NEW.{side}_type='{table}' AND NOT EXISTS(SELECT 1 FROM \"{table}\" WHERE id=NEW.{side}_id AND owner_id=NEW.owner_id);"

        def song(side):
            return (
                "CASE "
                + " ".join(
                    f"WHEN NEW.{side}_type='{table}' THEN (SELECT {column} FROM \"{table}\" WHERE id=NEW.{side}_id)"
                    for table, column in SUBJECTS.items()
                )
                + " END"
            )

        body += f"SELECT RAISE(ABORT,'Cross-song lineage') WHERE {song('child')} IS NOT NULL AND {song('parent')} IS NOT NULL AND {song('child')} != {song('parent')};"
        body += "SELECT RAISE(ABORT,'Lineage cycle') WHERE EXISTS(WITH RECURSIVE ancestors(type,id) AS (SELECT NEW.parent_type,NEW.parent_id UNION SELECT e.parent_type,e.parent_id FROM lineage_edge e JOIN ancestors a ON e.child_type=a.type AND e.child_id=a.id) SELECT 1 FROM ancestors WHERE type=NEW.child_type AND id=NEW.child_id);"
        connection.exec_driver_sql(
            f"CREATE TRIGGER lineage_validate_{action.lower()} BEFORE {action} ON lineage_edge BEGIN {body} END"
        )
        body = "SELECT RAISE(ABORT,'External asset validator unavailable') WHERE NEW.subject_type IN ('lora','cli_run'); SELECT RAISE(ABORT,'Invalid asset subject') WHERE NOT EXISTS(SELECT 1 FROM entity_song WHERE type=NEW.subject_type AND id=NEW.subject_id AND owner_id=NEW.owner_id);"
        connection.exec_driver_sql(
            f"CREATE TRIGGER asset_validate_{action.lower()} BEFORE {action} ON asset BEGIN {body} END"
        )
        body = "SELECT RAISE(ABORT,'Job dependency cycle') WHERE EXISTS(WITH RECURSIVE ancestors(id) AS (SELECT NEW.depends_on_job_id UNION SELECT d.depends_on_job_id FROM job_dependency d JOIN ancestors a ON d.job_id=a.id) SELECT 1 FROM ancestors WHERE id=NEW.job_id);"
        connection.exec_driver_sql(
            f"CREATE TRIGGER dependency_validate_{action.lower()} BEFORE {action} ON job_dependency BEGIN {body} END"
        )
        for column, table in (
            ("current_lyrics_version_id", "lyrics_version"),
            ("master_take_id", "take"),
            ("cover_artwork_id", "artwork"),
        ):
            body = f"SELECT RAISE(ABORT,'Invalid song selection') WHERE EXISTS(SELECT 1 FROM {table} WHERE id=NEW.{column} AND (owner_id != NEW.owner_id OR song_id != NEW.id));"
            connection.exec_driver_sql(
                f"CREATE TRIGGER song_{column}_{action.lower()} BEFORE {action} ON song BEGIN {body} END"
            )
    roots = "UPDATE take SET root_id=coalesce((WITH RECURSIVE ancestors(id) AS (SELECT take.id UNION SELECT e.parent_id FROM lineage_edge e JOIN ancestors a ON e.child_id=a.id WHERE e.child_type='take' AND e.parent_type='take') SELECT min(id) FROM ancestors WHERE NOT EXISTS(SELECT 1 FROM lineage_edge WHERE child_type='take' AND child_id=ancestors.id AND parent_type='take')),id);"
    for action in ("INSERT", "UPDATE", "DELETE"):
        connection.exec_driver_sql(
            f"CREATE TRIGGER lineage_roots_{action.lower()} AFTER {action} ON lineage_edge BEGIN {roots} END"
        )
    for table in SUBJECTS:
        connection.exec_driver_sql(
            f"CREATE TRIGGER protect_lineage_{table} BEFORE DELETE ON \"{table}\" BEGIN SELECT RAISE(ABORT,'Referenced lineage subject') WHERE EXISTS(SELECT 1 FROM lineage_edge WHERE (parent_type='{table}' AND parent_id=OLD.id) OR (child_type='{table}' AND child_id=OLD.id)); SELECT RAISE(ABORT,'Referenced asset subject') WHERE EXISTS(SELECT 1 FROM asset WHERE subject_type='{table}' AND subject_id=OLD.id); END"
        )


def uninstall(connection):
    for table in JSON_FIELDS:
        for action in ("insert", "update"):
            connection.exec_driver_sql(f"DROP TRIGGER finite_json_{table}_{action}")
    relations = json.loads(
        Path(__file__).with_name("initial_relations.json").read_text(encoding="utf-8")
    )
    for table in relations:
        connection.exec_driver_sql(f"DROP TRIGGER identity_{table}")
        for action in ("insert", "update"):
            connection.exec_driver_sql(f"DROP TRIGGER references_{table}_{action}")
    for action in ("insert", "update"):
        connection.exec_driver_sql(f"DROP TRIGGER lineage_validate_{action}")
        connection.exec_driver_sql(f"DROP TRIGGER asset_validate_{action}")
        connection.exec_driver_sql(f"DROP TRIGGER dependency_validate_{action}")
        for column in (
            "current_lyrics_version_id",
            "master_take_id",
            "cover_artwork_id",
        ):
            connection.exec_driver_sql(f"DROP TRIGGER song_{column}_{action}")
    for action in ("insert", "update", "delete"):
        connection.exec_driver_sql(f"DROP TRIGGER lineage_roots_{action}")
    for table in SUBJECTS:
        connection.exec_driver_sql(f"DROP TRIGGER protect_lineage_{table}")
    connection.exec_driver_sql("DROP VIEW entity_song")
