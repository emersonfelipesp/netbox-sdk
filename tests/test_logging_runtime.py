"""Tests for shared logging setup and log parsing helpers."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from netbox_sdk import logging_runtime

pytestmark = pytest.mark.suite_sdk


def _reset_logging_runtime_state() -> None:
    for name in ("netbox_cli", "netbox_sdk"):
        lg = logging.getLogger(name)
        for handler in list(lg.handlers):
            lg.removeHandler(handler)
            handler.close()
    logging_runtime._ACTIVE_LOG_FILE = None
    logging_runtime._LOGGING_INITIALIZED = False


def test_setup_logging_writes_json_lines(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    _reset_logging_runtime_state()

    path = logging_runtime.setup_logging()
    logging.getLogger("netbox_cli.test").info("hello from test")
    logging.getLogger("netbox_sdk.test").info("hello from sdk")

    entries = logging_runtime.read_log_entries(limit=10)

    assert path.exists()
    assert entries
    assert entries[-2].logger == "netbox_cli.test"
    assert entries[-2].message == "hello from test"
    assert entries[-1].logger == "netbox_sdk.test"
    assert entries[-1].message == "hello from sdk"


def test_render_log_entries_includes_source_metadata() -> None:
    rendered = logging_runtime.render_log_entries(
        [
            logging_runtime.LogEntry(
                timestamp="2026-03-22T10:00:00Z",
                level="INFO",
                logger="netbox_cli.api",
                message="api request completed",
                module="api",
                function="request",
                line=42,
            )
        ],
        include_source=True,
    )

    assert "2026-03-22T10:00:00Z" in rendered
    assert "netbox_cli.api" in rendered
    assert "[api.request:42]" in rendered


def test_log_dir_falls_back_when_config_path_is_unavailable(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        logging_runtime,
        "config_path",
        lambda: (_ for _ in ()).throw(OSError("read-only")),
    )
    monkeypatch.setattr(logging_runtime.tempfile, "gettempdir", lambda: str(tmp_path))

    assert logging_runtime.log_dir() == Path(tmp_path) / "netbox-sdk" / "logs"


def test_setup_logging_falls_back_when_log_file_cannot_be_opened(tmp_path, monkeypatch) -> None:
    config_root = tmp_path / "config"
    fallback_root = tmp_path / "tmp"
    preferred = config_root / "netbox-sdk" / "logs" / "netbox-sdk.log"
    fallback = fallback_root / "netbox-sdk" / "logs" / "netbox-sdk.log"

    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_root))
    monkeypatch.setattr(logging_runtime.tempfile, "gettempdir", lambda: str(fallback_root))
    _reset_logging_runtime_state()

    class FailingPreferredHandler(RotatingFileHandler):
        def __init__(self, filename, *args, **kwargs) -> None:  # noqa: ANN001, ANN002, ANN003
            if Path(filename) == preferred:
                raise OSError("read-only")
            super().__init__(filename, *args, **kwargs)

    monkeypatch.setattr(logging_runtime, "RotatingFileHandler", FailingPreferredHandler)

    path = logging_runtime.setup_logging()
    logging.getLogger("netbox_cli.test").info("fallback path works")

    assert path == fallback
    assert logging_runtime.active_log_file_path() == fallback
    assert fallback.exists()
    assert any(
        entry.message == "fallback path works"
        for entry in logging_runtime.read_log_entries(limit=5)
    )
