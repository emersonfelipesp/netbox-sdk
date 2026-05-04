"""Tests for shared logging setup and log parsing helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from netbox_sdk import logging_runtime

pytestmark = pytest.mark.suite_sdk


def test_setup_logging_writes_json_lines(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    for name in ("netbox_cli", "netbox_sdk"):
        lg = logging.getLogger(name)
        for handler in list(lg.handlers):
            lg.removeHandler(handler)
            handler.close()
    logging_runtime._LOGGING_INITIALIZED = False

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
