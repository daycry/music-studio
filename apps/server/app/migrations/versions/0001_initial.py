"""Esquema inicial completo. Downgrade destructivo sólo en bases de prueba.

El SQL se congela en esta revisión: las futuras entidades no alteran su DDL.
Las FK diferidas permiten vaciar ciclos dentro de una única transacción.
"""

from pathlib import Path

from alembic import op

from app.migrations.initial_invariants import install, uninstall

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    for statement in (
        (Path(__file__).with_name("0001_schema.sql"))
        .read_text(encoding="utf-8")
        .split(";\n")
    ):
        if statement.strip():
            connection.exec_driver_sql(statement)
    connection.exec_driver_sql(
        'INSERT INTO "user" (id, owner_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
        (
            "01K70000000000000000000000",
            "01K70000000000000000000000",
            "local",
            "2026-10-07T00:00:00.000000Z",
            "2026-10-07T00:00:00.000000Z",
        ),
    )
    connection.exec_driver_sql(
        "CREATE VIRTUAL TABLE song_fts USING fts5(song_id UNINDEXED, title, style_prompt, lyrics)"
    )
    projection = "INSERT INTO song_fts SELECT s.id,s.title,s.style_prompt,coalesce(l.text,'') FROM song s LEFT JOIN lyrics_version l ON l.id=s.current_lyrics_version_id AND l.deleted_at IS NULL WHERE s.deleted_at IS NULL AND s.id="
    for action in ("INSERT", "UPDATE", "DELETE"):
        identifier = "OLD.id" if action == "DELETE" else "NEW.id"
        body = f"DELETE FROM song_fts WHERE song_id={identifier};"
        if action != "DELETE":
            body += projection + identifier + ";"
        connection.exec_driver_sql(
            f"CREATE TRIGGER song_fts_{action.lower()} AFTER {action} ON song BEGIN {body} END"
        )
    for action in ("INSERT", "UPDATE", "DELETE"):
        identifier = "OLD.song_id" if action == "DELETE" else "NEW.song_id"
        body = (
            f"DELETE FROM song_fts WHERE song_id={identifier};"
            + projection
            + identifier
            + ";"
        )
        if action == "UPDATE":
            body += (
                "DELETE FROM song_fts WHERE song_id=OLD.song_id;"
                + projection
                + "OLD.song_id;"
            )
        connection.exec_driver_sql(
            f"CREATE TRIGGER lyrics_fts_{action.lower()} AFTER {action} ON lyrics_version BEGIN {body} END"
        )
    install(connection)


def downgrade():
    connection = op.get_bind()
    uninstall(connection)
    for prefix in ("song", "lyrics"):
        for action in ("insert", "update", "delete"):
            connection.exec_driver_sql(f"DROP TRIGGER {prefix}_fts_{action}")
    connection.exec_driver_sql("DROP TABLE song_fts")
    tables = [
        "user",
        "collection",
        "song",
        "lyrics_version",
        "take",
        "lineage_edge",
        "asset",
        "upload",
        "analysis",
        "artwork",
        "character",
        "character_ref",
        "preset",
        "video_project",
        "video_character",
        "shot",
        "shot_version",
        "render",
        "export",
        "job",
        "job_dependency",
        "setting",
        "provider",
    ]
    for table in tables:
        connection.exec_driver_sql(f'DELETE FROM "{table}"')
    for table in reversed(tables):
        connection.exec_driver_sql(f'DROP TABLE "{table}"')
