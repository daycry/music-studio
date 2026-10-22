import threading
from contextlib import contextmanager

from app.db import create_db_engine, migrate
from app.models import Song
from sqlalchemy import event, text
from sqlalchemy.orm import Session


@contextmanager
def managed_engine(path):
    engine = create_db_engine(path)
    try:
        yield engine
    finally:
        engine.dispose()


def test_fts_first_insert_concurrent_commit_does_not_upgrade_stale_snapshot(tmp_path):
    path = tmp_path / "studio.sqlite"
    migrate(path)
    with managed_engine(path) as engine:
        with engine.connect() as connection:
            owner = connection.execute(text("SELECT id FROM user")).scalar_one()
            initial_connection = connection.connection.driver_connection
        second_prepared = threading.Event()
        first_committed = threading.Event()
        failures = []

        def trace(dbapi, _record):
            def callback(sql):
                if (
                    threading.current_thread().name == "second"
                    and sql.startswith("INSERT INTO song (")
                    and not second_prepared.is_set()
                ):
                    second_prepared.set()
                    if not first_committed.wait(3):
                        failures.append("First commit did not complete")

            dbapi.set_trace_callback(callback)

        event.listen(engine, "connect", trace)
        trace(initial_connection, None)

        def before(connection, cursor, statement, parameters, context, executemany):
            if threading.current_thread().name == "first" and statement.startswith(
                "INSERT INTO song ("
            ):
                assert second_prepared.wait(3)

        event.listen(engine, "before_cursor_execute", before)

        def writer(title):
            try:
                with Session(engine) as session:
                    session.add(Song(owner_id=owner, title=title, style_prompt=""))
                    session.commit()
                if title == "first":
                    first_committed.set()
            except BaseException as error:  # noqa: BLE001 - recoger el hilo propio
                failures.append(error)

        threads = [
            threading.Thread(name=title, target=writer, args=(title,))
            for title in ("first", "second")
        ]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(5)
            assert all(not thread.is_alive() for thread in threads)
            assert not failures
            with engine.connect() as connection:
                assert (
                    connection.execute(text("SELECT count(*) FROM song")).scalar_one()
                    == 2
                )
                assert (
                    connection.exec_driver_sql(
                        "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'first OR second'"
                    ).scalar_one()
                    == 2
                )
        finally:
            second_prepared.set()
            first_committed.set()
            for thread in threads:
                if thread.ident is not None:
                    thread.join(5)


def test_fts_initialization_accepts_empty_database_and_readonly_access_during_writer(
    tmp_path,
):
    path = tmp_path / "studio.sqlite"
    with managed_engine(path) as before, before.connect() as connection:
        assert connection.exec_driver_sql("SELECT 7").scalar_one() == 7
    migrate(path)
    with managed_engine(path) as engine:
        with engine.connect() as writer:
            writer.exec_driver_sql(
                "UPDATE snapshot_clock SET revision=revision WHERE id=1"
            )
            with engine.connect() as reader:
                assert (
                    reader.exec_driver_sql("SELECT count(*) FROM user").scalar_one()
                    == 1
                )
            writer.rollback()
        with Session(engine) as session:
            owner = session.execute(text("SELECT id FROM user")).scalar_one()
            song = Song(owner_id=owner, title="beforeword", style_prompt="")
            session.add(song)
            session.commit()
            song.title = "afterword"
            session.commit()
            assert (
                session.execute(
                    text(
                        "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'afterword'"
                    )
                ).scalar_one()
                == 1
            )
            assert (
                session.execute(
                    text(
                        "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'beforeword'"
                    )
                ).scalar_one()
                == 0
            )
            session.delete(song)
            session.commit()
            assert (
                session.execute(
                    text(
                        "SELECT count(*) FROM song_fts WHERE song_fts MATCH 'afterword'"
                    )
                ).scalar_one()
                == 0
            )
