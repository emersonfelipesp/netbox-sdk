"""Tests for shared logging setup and log parsing helpers."""

from __future__ import annotations

import logging

from netbox_cli import logging_runtime


def test_setup_logging_writes_json_lines(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    logger = logging.getLogger("netbox_cli")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logging_runtime._LOGGING_INITIALIZED = False

    path = logging_runtime.setup_logging()
    logging.getLogger("netbox_cli.test").info("hello from test")

    entries = logging_runtime.read_log_entries(limit=10)

    assert path.exists()
    assert entries
    assert entries[-1].logger == "netbox_cli.test"
    assert entries[-1].message == "hello from test"


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
