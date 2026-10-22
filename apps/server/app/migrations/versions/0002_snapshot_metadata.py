"""Metadatos locales y mantenimiento acotado, posteriores al baseline23."""

from alembic import op

from app.migrations.fix1_invariants import install, install_dirty, install_fts

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.exec_driver_sql(
        "ALTER TABLE song ADD COLUMN is_dependency_only BOOLEAN NOT NULL DEFAULT 0 CHECK(is_dependency_only IN (0,1))"
    )
    connection.exec_driver_sql(
        "ALTER TABLE song ADD COLUMN snapshot_dirty BOOLEAN NOT NULL DEFAULT 1 CHECK(snapshot_dirty IN (0,1))"
    )
    connection.exec_driver_sql(
        "ALTER TABLE song ADD COLUMN snapshot_generation INTEGER NOT NULL DEFAULT 0 CHECK(snapshot_generation>=0)"
    )
    connection.exec_driver_sql(
        "CREATE INDEX ix_song_snapshot_pending ON song(is_dependency_only,snapshot_dirty,id)"
    )
    install(connection)
    install_fts(connection)
    install_dirty(connection)
    connection.exec_driver_sql(
        "CREATE VIEW dispatchable_job AS SELECT j.* FROM job j LEFT JOIN song s ON s.id=j.song_id WHERE s.id IS NULL OR s.is_dependency_only=0"
    )


def downgrade():
    from app.migrations.initial_invariants import install as baseline_install

    connection = op.get_bind()
    for (name,) in connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    ).all():
        connection.exec_driver_sql(f'DROP TRIGGER "{name}"')
    connection.exec_driver_sql("DROP VIEW entity_song")
    connection.exec_driver_sql("DROP VIEW dispatchable_job")
    connection.exec_driver_sql("DROP TABLE snapshot_member")
    connection.exec_driver_sql("DROP TABLE song_fts_identity")
    connection.exec_driver_sql("DROP INDEX ix_song_snapshot_pending")
    for column in ("snapshot_generation", "snapshot_dirty", "is_dependency_only"):
        connection.exec_driver_sql(f"ALTER TABLE song DROP COLUMN {column}")
    baseline_install(connection)
    projection = "INSERT INTO song_fts SELECT s.id,s.title,s.style_prompt,coalesce(l.text,'') FROM song s LEFT JOIN lyrics_version l ON l.id=s.current_lyrics_version_id AND l.deleted_at IS NULL WHERE s.deleted_at IS NULL AND s.id="
    for prefix, table, column in [
        ("song", "song", "id"),
        ("lyrics", "lyrics_version", "song_id"),
    ]:
        for action in ("INSERT", "UPDATE", "DELETE"):
            side = "OLD" if action == "DELETE" else "NEW"
            identifier = f"{side}.{column}"
            body = f"DELETE FROM song_fts WHERE song_id={identifier};"
            if prefix == "lyrics" or action != "DELETE":
                body += projection + identifier + ";"
            if prefix == "lyrics" and action == "UPDATE":
                body += (
                    "DELETE FROM song_fts WHERE song_id=OLD.song_id;"
                    + projection
                    + "OLD.song_id;"
                )
            connection.exec_driver_sql(
                f"CREATE TRIGGER {prefix}_fts_{action.lower()} AFTER {action} ON {table} BEGIN {body} END"
            )
