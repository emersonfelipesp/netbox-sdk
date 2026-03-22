"""Shared logging setup and log-record helpers for the NetBox CLI/TUI."""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from .config import config_path

DEFAULT_LOG_DIRNAME = "logs"
DEFAULT_LOG_FILENAME = "netbox-cli.log"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_TAIL_LIMIT = 200
LOG_FORMAT_VERSION = 1

_LOGGER_NAMESPACE = "netbox_cli"
_LOGGING_INITIALIZED = False


class JsonLogFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "v": LOG_FORMAT_VERSION,
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


@dataclass(slots=True)
class LogEntry:
    timestamp: str
    level: str
    logger: str
    message: str
    module: str = ""
    function: str = ""
    line: int = 0
    exception: str | None = None


def log_dir() -> Path:
    target = config_path().parent / DEFAULT_LOG_DIRNAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def log_file_path() -> Path:
    return log_dir() / DEFAULT_LOG_FILENAME


def setup_logging(level: str = DEFAULT_LOG_LEVEL) -> Path:
    global _LOGGING_INITIALIZED
    target = log_file_path()
    logger = logging.getLogger(_LOGGER_NAMESPACE)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    if not any(
        isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == target
        for handler in logger.handlers
    ):
        handler = RotatingFileHandler(
            target,
            maxBytes=1_048_576,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logger.level)
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)

    if not _LOGGING_INITIALIZED:
        logger.info("logging initialized", extra={"nbx_event": "logging_init"})
        _LOGGING_INITIALIZED = True
    return target


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def _entry_from_payload(payload: dict[str, Any]) -> LogEntry:
    return LogEntry(
        timestamp=str(payload.get("ts") or ""),
        level=str(payload.get("level") or "INFO"),
        logger=str(payload.get("logger") or _LOGGER_NAMESPACE),
        message=str(payload.get("message") or ""),
        module=str(payload.get("module") or ""),
        function=str(payload.get("func") or ""),
        line=int(payload.get("line") or 0),
        exception=str(payload["exception"]) if payload.get("exception") else None,
    )


def _entry_from_plain_text(line: str) -> LogEntry:
    return LogEntry(
        timestamp="",
        level="INFO",
        logger=_LOGGER_NAMESPACE,
        message=line.rstrip(),
    )


def read_log_entries(limit: int = DEFAULT_LOG_TAIL_LIMIT) -> list[LogEntry]:
    path = log_file_path()
    if not path.exists():
        return []

    lines: deque[str] = deque(maxlen=max(1, limit))
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)

    entries: list[LogEntry] = []
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            entries.append(_entry_from_plain_text(line))
            continue
        if isinstance(payload, dict):
            entries.append(_entry_from_payload(payload))
    return entries


def render_log_entries(
    entries: list[LogEntry],
    *,
    include_logger: bool = True,
    include_source: bool = False,
) -> str:
    rendered: list[str] = []
    for entry in entries:
        parts = []
        if entry.timestamp:
            parts.append(entry.timestamp)
        parts.append(entry.level.ljust(8))
        if include_logger and entry.logger:
            parts.append(entry.logger)
        if include_source and entry.module:
            source = entry.module
            if entry.function:
                source = f"{source}.{entry.function}"
            if entry.line:
                source = f"{source}:{entry.line}"
            parts.append(f"[{source}]")
        parts.append(entry.message)
        rendered.append(" ".join(part for part in parts if part))
        if entry.exception:
            rendered.append(entry.exception)
    return "\n".join(rendered)
