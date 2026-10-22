"""Conexiones SQLite y migraciones empaquetadas del server."""

from pathlib import Path
from types import SimpleNamespace

from alembic import command
from alembic.config import Config
from jsonschema import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .logging import SAFE_EVENTS

SAFE_EVENTS.add("snapshot.failed")


def confine_path(path: Path):
    path = Path(path)
    root = Path(__file__).resolve().parents[3]
    resolved = path.resolve()
    if not resolved.is_relative_to(root) and not (
        root == Path("/studio") and resolved.is_relative_to(Path("/data"))
    ):
        raise ValueError("Path must remain inside the studio")
    if path.is_symlink():
        raise ValueError("Database or data directory symlink")
    return resolved


def create_db_engine(path: Path, data_dir=None):
    path = confine_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine("sqlite:///" + path.as_posix())
    engine.studio_data_dir = Path(data_dir) if data_dir is not None else None
    if data_dir is not None:
        from .logging import configure_logging

        engine.studio_logger = configure_logging(
            SimpleNamespace(data_dir=confine_path(data_dir))
        )

    @event.listens_for(engine, "connect")
    def configure(connection, record):
        connection.isolation_level = None
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        # FTS5 lee su configuración al preparar el primer statement que lo
        # referencia. Resolver esa lectura en autocommit evita que el primer
        # INSERT de una conexión promueva una vista WAL obsoleta.
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='song_fts'"
        ).fetchone():
            connection.execute("SELECT rowid FROM song_fts LIMIT 0").fetchall()

    @event.listens_for(engine, "begin")
    def begin(connection):
        connection.exec_driver_sql("BEGIN")

    return engine


@event.listens_for(Session, "after_commit")
def snapshots_after_commit(session):
    engine = session.get_bind()
    directory = getattr(engine, "studio_data_dir", None)
    if directory is not None:
        from .publication import PublicationTimeout
        from .snapshots import reconcile

        coordinator = getattr(engine, "studio_publication_coordinator", None)

        try:
            if coordinator is None:
                reconcile(engine, directory)
            else:
                with coordinator.barrier():
                    reconcile(engine, directory)
        except (
            OSError,
            ValueError,
            SQLAlchemyError,
            ValidationError,
            PublicationTimeout,
        ):
            # El commit ya es durable; el siguiente arranque repara la proyección.
            engine.studio_logger.error("snapshot.failed")


def migrate(path: Path, *, initial_user=None):
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    config.attributes["database_path"] = Path(path)
    config.attributes["initial_user"] = initial_user
    command.upgrade(config, "head")


def rebuild_fts(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql("DELETE FROM song_fts")
        connection.exec_driver_sql(
            "INSERT INTO song_fts(rowid,song_id,title,style_prompt,lyrics) SELECT m.rowid,s.id,s.title,s.style_prompt,coalesce(l.text,'') FROM song s JOIN song_fts_identity m ON m.song_id=s.id LEFT JOIN lyrics_version l ON l.id=s.current_lyrics_version_id AND l.deleted_at IS NULL WHERE s.deleted_at IS NULL AND s.is_dependency_only=0"
        )
