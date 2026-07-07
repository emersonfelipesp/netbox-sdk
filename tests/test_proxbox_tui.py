"""Tests for the Proxbox-focused Textual request workbench."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.widgets import Input, OptionList, Select, Static

from netbox_sdk.client import ApiResponse, ConnectionProbe
from netbox_sdk.config import Config
from netbox_tui.dev_state import DevTuiState
from netbox_tui.proxbox_app import build_proxbox_tui_app

pytestmark = pytest.mark.suite_tui


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.config = Config(
        base_url="https://netbox.example.com",
        token_key="abc",
        token_secret="def",
        timeout=5.0,
    )
    client.probe_connection = AsyncMock(
        return_value=ConnectionProbe(status=200, version="4.2", ok=True, error=None)
    )
    client.request = AsyncMock(
        return_value=ApiResponse(
            status=200,
            text=json.dumps({"count": 0, "results": []}),
            headers={"Content-Type": "application/json"},
        )
    )
    return client


@pytest.fixture(autouse=True)
def isolate_dev_tui_state():
    with (
        patch("netbox_tui.dev_app.load_dev_tui_state", return_value=DevTuiState()),
        patch("netbox_tui.dev_app.save_dev_tui_state", return_value=None),
    ):
        yield


@pytest.mark.asyncio
async def test_proxbox_tui_mounts_with_proxbox_catalog(mock_client) -> None:
    app = build_proxbox_tui_app(client=mock_client, theme_name="netbox-dark")

    assert app.index.groups() == ["plugins"]
    assert "proxbox/firewall/rules" in app.index.resources("plugins")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        sidebar_title = app.query_one("#dev_sidebar_title", Static)
        assert str(sidebar_title.content) == "Proxbox Resources"

        app._activate_resource("plugins", "proxbox/firewall/rules")
        await pilot.pause()

        method = app.query_one("#dev_method_select", Select)
        path = app.query_one("#dev_path_input", Input)
        operations = app.query_one("#dev_operation_list", OptionList)

        assert str(method.value) == "GET"
        assert path.value == "/api/plugins/proxbox/firewall/rules/"
        assert operations.option_count >= 6
