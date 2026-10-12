"""Correcciones aditivas; la revisión inicial permanece congelada."""

from .initial_invariants import MEMBERS, SUBJECTS
from .legacy_m1_registry import TABLES

INVERSE = {
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
    "character_ref": ("character", "character_id"),
    "job_dependency": ("job", "job_id"),
}


def install_dirty(connection):
    fields = ",".join(
        '"' + column.name + '"'
        for column in TABLES["song"].columns
        if column.name
        not in {"is_dependency_only", "snapshot_dirty", "snapshot_generation"}
    )
    connection.exec_driver_sql(
        f"CREATE TRIGGER support_song_edit BEFORE UPDATE OF {fields} ON song WHEN OLD.is_dependency_only=1 AND NEW.is_dependency_only=1 BEGIN SELECT RAISE(ABORT,'Support project requires promotion'); END"
    )
    connection.exec_driver_sql(
        "CREATE TABLE snapshot_member (root_id TEXT NOT NULL REFERENCES song(id) DEFERRABLE INITIALLY DEFERRED, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, PRIMARY KEY(root_id,entity_type,entity_id))"
    )
    connection.exec_driver_sql(
        "CREATE INDEX ix_snapshot_member_entity ON snapshot_member(entity_type,entity_id,root_id)"
    )
    connection.exec_driver_sql(
        "CREATE TRIGGER snapshot_member_purge BEFORE DELETE ON song BEGIN DELETE FROM snapshot_member WHERE root_id=OLD.id; END"
    )
    for table in MEMBERS:
        if table in {"setting", "provider", "preset"}:
            continue
        for action, timing, side in [
            ("insert", "AFTER", "NEW"),
            ("update_old", "BEFORE", "OLD"),
            ("update_new", "AFTER", "NEW"),
            ("delete", "BEFORE", "OLD"),
        ]:
            operation = "UPDATE" if action.startswith("update") else action.upper()
            keys = [(repr(table), f"{side}.id")]
            if table in INVERSE and INVERSE[table][0] != "song" and table != "analysis":
                parent, column = INVERSE[table]
                keys.append((repr(parent), f"{side}.{column}"))
            if table == "asset":
                keys.append((f"{side}.subject_type", f"{side}.subject_id"))
            if table == "lineage_edge":
                keys.append((f"{side}.child_type", f"{side}.child_id"))
            selectors = [
                f"SELECT root_id FROM snapshot_member WHERE entity_type={kind} AND entity_id={identifier}"
                for kind, identifier in keys
            ]
            selectors.append(
                f"SELECT song_id FROM entity_song WHERE type='{table}' AND id={side}.id"
            )
            if table == "song":
                selectors.append(f"SELECT {side}.id")
            body = (
                "UPDATE song SET snapshot_dirty=1,snapshot_generation=snapshot_generation+1 WHERE is_dependency_only=0 AND id IN ("
                + " UNION ".join(selectors)
                + ");"
            )
            columns = ""
            if table == "song" and operation == "UPDATE":
                columns = " OF " + ",".join(
                    '"' + column.name + '"'
                    for column in TABLES["song"].columns
                    if column.name not in {"snapshot_dirty", "snapshot_generation"}
                )
            connection.exec_driver_sql(
                f'CREATE TRIGGER dirty_{table}_{action} {timing} {operation}{columns} ON "{table}" BEGIN {body} END'
            )


def canonical_root(identifier):
    return f"(WITH RECURSIVE ancestors(id) AS (SELECT {identifier} UNION SELECT e.parent_id FROM lineage_edge e JOIN ancestors a ON e.child_id=a.id WHERE e.child_type='take' AND e.parent_type='take') SELECT min(id) FROM ancestors WHERE NOT EXISTS(SELECT 1 FROM lineage_edge WHERE child_type='take' AND child_id=ancestors.id AND parent_type='take'))"


def install(connection):
    for action in ("INSERT", "UPDATE"):
        connection.exec_driver_sql(
            f"CREATE TRIGGER canonical_take_{action.lower()} BEFORE {action} ON take BEGIN SELECT RAISE(ABORT,'Invalid take root') WHERE NEW.root_id != {canonical_root('NEW.id')}; END"
        )
    for action in ("INSERT", "UPDATE", "DELETE"):
        connection.exec_driver_sql(f"DROP TRIGGER lineage_roots_{action.lower()}")
        sides = (
            ["NEW"]
            if action == "INSERT"
            else ["OLD"]
            if action == "DELETE"
            else ["OLD", "NEW"]
        )
        seeds = " UNION ".join(
            f"SELECT {side}.child_id WHERE {side}.child_type='take' AND {side}.parent_type='take'"
            for side in sides
        )
        descendants = f"WITH RECURSIVE affected(id) AS ({seeds} UNION SELECT e.child_id FROM lineage_edge e JOIN affected a ON e.parent_id=a.id WHERE e.child_type='take' AND e.parent_type='take') SELECT id FROM affected"
        root = canonical_root("take.id")
        connection.exec_driver_sql(
            f"CREATE TRIGGER lineage_roots_{action.lower()} AFTER {action} ON lineage_edge BEGIN UPDATE take SET root_id={root} WHERE id IN ({descendants}) AND root_id != {root}; END"
        )
    for table in (*SUBJECTS, "shot", "video_project"):
        # AFTER sees the new transitive membership of shots and renders as well.
        affected = f"SELECT '{table}' AS type, NEW.id AS id"
        if table == "shot":
            affected += (
                " UNION SELECT 'shot_version',id FROM shot_version WHERE shot_id=NEW.id"
            )
        if table == "video_project":
            affected += " UNION SELECT 'render',id FROM render WHERE video_project_id=NEW.id UNION SELECT 'shot_version',v.id FROM shot_version v JOIN shot s ON s.id=v.shot_id WHERE s.video_project_id=NEW.id"
        column = {
            "shot": "video_project_id",
            "shot_version": "shot_id",
            "render": "video_project_id",
        }.get(
            table,
            "song_id"
            if table in {"take", "artwork", "lyrics_version", "export", "video_project"}
            else "owner_id",
        )
        connection.exec_driver_sql(
            f"CREATE TRIGGER inverse_lineage_{table} AFTER UPDATE OF {column},owner_id ON \"{table}\" BEGIN SELECT RAISE(ABORT,'Cross-song lineage') WHERE EXISTS(WITH affected AS ({affected}), edges AS (SELECT e.id FROM lineage_edge e JOIN affected a ON e.child_type=a.type AND e.child_id=a.id UNION SELECT e.id FROM lineage_edge e JOIN affected a ON e.parent_type=a.type AND e.parent_id=a.id) SELECT 1 FROM edges x JOIN lineage_edge e ON e.id=x.id JOIN entity_song c ON c.type=e.child_type AND c.id=e.child_id JOIN entity_song p ON p.type=e.parent_type AND p.id=e.parent_id WHERE c.song_id IS NOT NULL AND p.song_id IS NOT NULL AND c.song_id != p.song_id); END"
        )


def install_fts(connection):
    for prefix in ("song", "lyrics"):
        for action in ("insert", "update", "delete"):
            connection.exec_driver_sql(f"DROP TRIGGER {prefix}_fts_{action}")
    connection.exec_driver_sql(
        "CREATE TABLE song_fts_identity (rowid INTEGER PRIMARY KEY AUTOINCREMENT, song_id TEXT NOT NULL UNIQUE REFERENCES song(id) DEFERRABLE INITIALLY DEFERRED)"
    )
    connection.exec_driver_sql(
        "INSERT INTO song_fts_identity(song_id) SELECT id FROM song ORDER BY id"
    )
    connection.exec_driver_sql("DELETE FROM song_fts")

    def projection(ids):
        return f"INSERT INTO song_fts(rowid,song_id,title,style_prompt,lyrics) SELECT m.rowid,s.id,s.title,s.style_prompt,coalesce(l.text,'') FROM song s JOIN song_fts_identity m ON m.song_id=s.id LEFT JOIN lyrics_version l ON l.id=s.current_lyrics_version_id AND l.deleted_at IS NULL WHERE s.deleted_at IS NULL AND s.is_dependency_only=0 AND s.id IN ({ids});"

    connection.exec_driver_sql(projection("SELECT id FROM song"))
    for action in ("INSERT", "UPDATE", "DELETE"):
        identifier = "OLD.id" if action == "DELETE" else "NEW.id"
        body = ""
        if action == "INSERT":
            body += "INSERT INTO song_fts_identity(song_id) VALUES(NEW.id);"
        body += f"DELETE FROM song_fts WHERE rowid=(SELECT rowid FROM song_fts_identity WHERE song_id={identifier});"
        body += (
            f"DELETE FROM song_fts_identity WHERE song_id={identifier};"
            if action == "DELETE"
            else projection(identifier)
        )
        columns = (
            " OF title,style_prompt,current_lyrics_version_id,deleted_at,is_dependency_only"
            if action == "UPDATE"
            else ""
        )
        connection.exec_driver_sql(
            f"CREATE TRIGGER song_fts_{action.lower()} AFTER {action}{columns} ON song BEGIN {body} END"
        )
    for action in ("INSERT", "UPDATE", "DELETE"):
        ids = "OLD.song_id" if action == "DELETE" else "NEW.song_id"
        if action == "UPDATE":
            ids += ",OLD.song_id"
        body = (
            f"DELETE FROM song_fts WHERE rowid IN (SELECT rowid FROM song_fts_identity WHERE song_id IN ({ids}));"
            + projection(ids)
        )
        connection.exec_driver_sql(
            f"CREATE TRIGGER lyrics_fts_{action.lower()} AFTER {action} ON lyrics_version BEGIN {body} END"
        )
