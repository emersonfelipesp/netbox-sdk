"""Shared logging setup and log-record helpers for the NetBox SDK, CLI, and TUI.

File logging is attached to both the legacy ``netbox_cli`` tree and the ``netbox_sdk``
tree so records from ``logging.getLogger("netbox_sdk....")`` persist without re-rooting
loggers under the old CLI package name.
"""

from __future__ import annotations

import json
import logging
import tempfile
import time
from collections import deque
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from netbox_sdk.config import config_path, legacy_config_path

DEFAULT_LOG_DIRNAME = "logs"
DEFAULT_LOG_FILENAME = "netbox-sdk.log"
LEGACY_LOG_FILENAME = "netbox-cli.log"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_TAIL_LIMIT = 200
LOG_FORMAT_VERSION = 1

_LOGGER_LEGACY = "netbox_cli"
_LOGGER_SDK = "netbox_sdk"
_LOGGING_INITIALIZED = False


class JsonLogFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()
        self.converter = time.gmtime

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
    try:
        target = config_path().parent / DEFAULT_LOG_DIRNAME
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        target = Path(tempfile.gettempdir()) / "netbox-sdk" / DEFAULT_LOG_DIRNAME
        target.mkdir(parents=True, exist_ok=True)
    return target


def log_file_path() -> Path:
    return log_dir() / DEFAULT_LOG_FILENAME


def legacy_log_file_path() -> Path:
    return legacy_config_path().parent / DEFAULT_LOG_DIRNAME / LEGACY_LOG_FILENAME


def active_log_file_path() -> Path:
    current = log_file_path()
    if current.exists():
        return current
    legacy = legacy_log_file_path()
    if legacy.exists():
        return legacy
    return current


def setup_logging(level: str = DEFAULT_LOG_LEVEL) -> Path:
    """Configure rotating JSON file logging for ``netbox_cli.*`` and ``netbox_sdk.*`` loggers."""
    global _LOGGING_INITIALIZED
    target = log_file_path()
    level_no = getattr(logging, level.upper(), logging.INFO)
    shared_handler: RotatingFileHandler | None = None

    for namespace in (_LOGGER_LEGACY, _LOGGER_SDK):
        lg = logging.getLogger(namespace)
        lg.setLevel(level_no)
        lg.propagate = False
        if any(
            isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == target
            for handler in lg.handlers
        ):
            continue
        if shared_handler is None:
            shared_handler = RotatingFileHandler(
                target,
                maxBytes=1_048_576,
                backupCount=5,
                encoding="utf-8",
            )
            shared_handler.setLevel(level_no)
            shared_handler.setFormatter(JsonLogFormatter())
        lg.addHandler(shared_handler)

    if not _LOGGING_INITIALIZED:
        logging.getLogger(_LOGGER_LEGACY).info(
            "logging initialized",
            extra={"nbx_event": "logging_init"},
        )
        _LOGGING_INITIALIZED = True
    return target


def get_logger(name: str) -> logging.Logger:
    """Return a named logger after ensuring file logging is configured."""
    setup_logging()
    return logging.getLogger(name)


def _entry_from_payload(payload: dict[str, Any]) -> LogEntry:
    return LogEntry(
        timestamp=str(payload.get("ts") or ""),
        level=str(payload.get("level") or "INFO"),
        logger=str(payload.get("logger") or _LOGGER_LEGACY),
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
        logger=_LOGGER_LEGACY,
        message=line.rstrip(),
    )


def read_log_entries(limit: int = DEFAULT_LOG_TAIL_LIMIT) -> list[LogEntry]:
    path = active_log_file_path()
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
