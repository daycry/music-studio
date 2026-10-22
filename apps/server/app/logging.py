"""Logs de eventos propios; el texto arbitrario nunca llega al fichero."""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

SAFE_EVENTS = {
    "server.started",
    "server.stopped",
    "request.completed",
    "request.failed",
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        message = (
            record.msg
            if isinstance(record.msg, str)
            and record.msg in SAFE_EVENTS
            and not record.args
            else "[redacted]"
        )
        data = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "proc": "server",
            "msg": message,
        }
        for field in ("job_id", "song_id"):
            value = getattr(record, field, None)
            if isinstance(value, str) and re.fullmatch(r"[0-9A-Z]{1,26}", value):
                data[field] = value
        return json.dumps(data, ensure_ascii=True)


def configure_logging(settings):
    folder = settings.data_dir / "logs"
    if not folder.resolve().is_relative_to(settings.data_dir) or not (
        folder / "server.log"
    ).resolve().is_relative_to(settings.data_dir):
        raise ValueError("Logs must remain inside configured data directory")
    folder.mkdir(parents=True, exist_ok=True)
    name = "studio.server." + hashlib.sha256(str(folder).encode()).hexdigest()[:16]
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = TimedRotatingFileHandler(
            folder / "server.log",
            when="midnight",
            backupCount=14,
            utc=True,
            encoding="utf-8",
            delay=True,
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger
