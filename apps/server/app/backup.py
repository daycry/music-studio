"""Copias SQLite nativas, publicación atómica y rotación de archivos propios."""

import asyncio
import os
import re
import sqlite3
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Lock

from .db import confine_path
from .logging import SAFE_EVENTS

SAFE_EVENTS.add("backup.failed")

_lock = Lock()
_name = re.compile(r"studio-backup-(\d{8}T\d{6}Z)\.sqlite\Z")


def validate_database(connection):
    """Una copia sólo cuenta si supera las reglas de restauración."""
    if (
        connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
        or connection.execute("PRAGMA foreign_key_check").fetchall()
    ):
        raise ValueError("Invalid SQLite backup references or integrity")
    connection.execute("INSERT INTO song_fts(song_fts) VALUES('integrity-check')")


def backup(database: Path, directory: Path, now=None, *, progress=None) -> Path:
    now = now or datetime.now(timezone.utc)
    directory = confine_path(directory)
    database = confine_path(database)
    directory.mkdir(parents=True, exist_ok=True)
    with _lock:
        descriptor, temporary = tempfile.mkstemp(
            prefix=".backup-", suffix=".sqlite", dir=directory
        )
        os.close(descriptor)
        try:
            with (
                closing(
                    sqlite3.connect(
                        Path(database).resolve().as_uri() + "?mode=ro",
                        uri=True,
                        timeout=0,
                    )
                ) as source,
                closing(sqlite3.connect(temporary)) as destination,
            ):
                source.backup(destination, pages=1, sleep=0.01, progress=progress)
                validate_database(destination)
                destination.commit()
                destination.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                destination.execute("PRAGMA journal_mode=DELETE")
            with open(temporary, "r+b") as stream:
                os.fsync(stream.fileno())
            target = directory / (
                "studio-backup-" + now.strftime("%Y%m%dT%H%M%SZ") + ".sqlite"
            )
            os.replace(temporary, target)
            cutoff = now - timedelta(days=14)
            for candidate in directory.iterdir():
                match = _name.fullmatch(candidate.name)
                if match and candidate != target and not candidate.is_symlink():
                    stamp = datetime.strptime(match[1], "%Y%m%dT%H%M%SZ").replace(
                        tzinfo=timezone.utc
                    )
                    if stamp < cutoff:
                        candidate.unlink()
            return target
        finally:
            Path(temporary).unlink(missing_ok=True)


def due(database: Path, directory: Path, now=None, *, progress=None):
    now = now or datetime.now(timezone.utc)
    latest = None
    if directory.exists():
        for candidate in sorted(
            directory.iterdir(), key=lambda path: path.name, reverse=True
        ):
            if progress is not None:
                progress(0, 0, 0)
            match = _name.fullmatch(candidate.name)
            if match and not candidate.is_symlink():
                try:
                    with closing(sqlite3.connect(":memory:")) as connection:
                        with closing(
                            sqlite3.connect(
                                candidate.resolve().as_uri() + "?mode=ro",
                                uri=True,
                                timeout=0,
                            )
                        ) as origin:
                            origin.backup(
                                connection, pages=1, sleep=0.01, progress=progress
                            )
                        if progress is not None:
                            progress(0, 0, 0)
                        validate_database(connection)
                        latest = datetime.strptime(match[1], "%Y%m%dT%H%M%SZ").replace(
                            tzinfo=timezone.utc
                        )
                        break
                except (sqlite3.Error, ValueError):
                    continue
    if latest is None or now - latest >= timedelta(days=1):
        return backup(database, directory, now, progress=progress)
    return None


def restore_backup(source: Path, target: Path):
    """Restaurar en un destino nuevo, con el backend parado; nunca sobre una BD viva."""
    source, target = confine_path(source), confine_path(target)
    if any(Path(str(target) + suffix).exists() for suffix in ("", "-wal", "-shm")):
        raise FileExistsError("Restore destination must be new")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".restore-", suffix=".sqlite", dir=target.parent
    )
    os.close(descriptor)
    try:
        with (
            closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as origin,
            closing(sqlite3.connect(temporary)) as destination,
        ):
            origin.backup(destination)
            validate_database(destination)
            destination.commit()
            destination.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            destination.execute("PRAGMA journal_mode=DELETE")
        with open(temporary, "r+b") as stream:
            os.fsync(stream.fileno())
        # CREATE exclusivo atómico: no hay ventana de sobreescritura de otra BD.
        os.link(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


class DailyBackup:
    def __init__(self, database, directory, logger):
        self.database, self.directory, self.logger = database, directory, logger
        self.stop = asyncio.Event()
        self.cancel = Event()
        self.initialized = False
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="studio-backup"
        )

    async def run(self):
        if self.initialized:
            await self.wait_interval()
        while not self.stop.is_set():
            try:
                await asyncio.get_running_loop().run_in_executor(
                    self.executor,
                    lambda: due(
                        self.database, self.directory, progress=self.check_cancel
                    ),
                )
            except InterruptedError:
                pass
            except (OSError, ValueError, sqlite3.Error):
                self.logger.error("backup.failed")
            await self.wait_interval()

    async def wait_interval(self):
        try:
            await asyncio.wait_for(self.stop.wait(), timeout=3600)
        except TimeoutError:
            pass

    async def initial(self):
        try:
            await asyncio.get_running_loop().run_in_executor(
                self.executor,
                lambda: due(self.database, self.directory, progress=self.check_cancel),
            )
        except (OSError, ValueError, sqlite3.Error):
            self.logger.error("backup.failed")
        self.initialized = True

    async def close(self):
        self.stop.set()
        self.cancel.set()
        try:
            await self.task
        except asyncio.CancelledError:
            if not self.task.cancelled():
                raise
        finally:
            await asyncio.to_thread(
                self.executor.shutdown, wait=True, cancel_futures=True
            )

    def start(self):
        self.task = asyncio.create_task(self.run())

    def check_cancel(self, status, remaining, total):
        if self.cancel.is_set():
            raise InterruptedError("Backup stopped")
