"""Tests for the dedicated TUI log viewer."""

from __future__ import annotations

import pytest
from textual.color import Color
from textual.widgets import DataTable, Select, Static

from netbox_cli.logging_runtime import LogEntry
from netbox_cli.ui.logs_app import NetBoxLogsTuiApp


async def _pause_twice(pilot) -> None:
    await pilot.pause()
    await pilot.pause()


@pytest.mark.asyncio
async def test_logs_tui_renders_entries(monkeypatch) -> None:
    monkeypatch.setattr(
        "netbox_cli.ui.logs_app.read_log_entries",
        lambda limit: [
            LogEntry(
                timestamp="2026-03-22T10:00:00Z",
                level="INFO",
                logger="netbox_cli.api",
                message="api request completed",
            ),
            LogEntry(
                timestamp="2026-03-22T10:01:00Z",
                level="ERROR",
                logger="netbox_cli.ui.app",
                message="request failed",
            ),
        ],
    )

    app = NetBoxLogsTuiApp(theme_name="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await _pause_twice(pilot)

        table = app.query_one("#logs_table", DataTable)
        detail = app.query_one("#logs_detail", Static)
        status = app.query_one("#logs_status", Static)

        assert table.row_count == 2
        assert "request failed" in str(detail.content)
        assert "Loaded 2 log entries" in str(status.content)


@pytest.mark.asyncio
async def test_logs_tui_theme_switch_refreshes_surfaces(monkeypatch) -> None:
    monkeypatch.setattr(
        "netbox_cli.ui.logs_app.read_log_entries",
        lambda limit: [
            LogEntry(
                timestamp="2026-03-22T10:00:00Z",
                level="INFO",
                logger="netbox_cli.api",
                message="api request completed",
            )
        ],
    )

    app = NetBoxLogsTuiApp(theme_name="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        app.query_one("#theme_select", Select).value = "netbox-dark"
        await _pause_twice(pilot)

        theme = app.theme_catalog.theme_for("netbox-dark")
        expected_surface = Color.parse(theme.colors["surface"])
        expected_panel = Color.parse(theme.colors["panel"])

        assert app.theme_name == "netbox-dark"
        assert app.query_one("#logs_detail_panel", object).styles.background == expected_surface
        assert app.query_one("#logs_detail", object).styles.background == expected_panel
