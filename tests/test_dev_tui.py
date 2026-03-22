from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.widgets import Input, OptionList, Select, Static, TextArea

from netbox_cli.api import ApiResponse, ConnectionProbe
from netbox_cli.schema import build_schema_index
from netbox_cli.ui.dev_app import NetBoxDevTuiApp, _text_area_syntax_theme_for
from netbox_cli.ui.dev_state import DevTuiState

_OPENAPI_PATH = Path(__file__).parent.parent / "reference" / "openapi" / "netbox-openapi.json"


@pytest.fixture
def real_index():
    return build_schema_index(_OPENAPI_PATH)


@pytest.fixture(autouse=True)
def isolate_dev_tui_state():
    with (
        patch(
            "netbox_cli.ui.dev_app.load_dev_tui_state",
            return_value=DevTuiState(),
        ),
        patch("netbox_cli.ui.dev_app.save_dev_tui_state", return_value=None),
    ):
        yield


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.probe_connection = AsyncMock(
        return_value=ConnectionProbe(status=200, version="4.2", ok=True, error=None)
    )
    client.request = AsyncMock(
        return_value=ApiResponse(
            status=200,
            text=json.dumps({"count": 1, "results": [{"id": 1, "name": "switch01"}]}),
            headers={"Content-Type": "application/json"},
        )
    )
    return client


@pytest.mark.asyncio
async def test_dev_tui_loads_default_operation(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="default")

    async with app.run_test() as pilot:
        app._activate_resource("dcim", "devices")
        await pilot.pause()

        method = app.query_one("#dev_method_select", Select)
        path = app.query_one("#dev_path_input", Input)
        summary = app.query_one("#dev_operation_summary", Static)
        operations = app.query_one("#dev_operation_list", OptionList)

        assert str(method.value) == "GET"
        assert path.value == "/api/dcim/devices/"
        assert "GET /api/dcim/devices/" in str(summary.content)
        assert operations.option_count > 0


@pytest.mark.asyncio
async def test_dev_tui_send_request_uses_current_http_client(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="dracula")

    async with app.run_test() as pilot:
        app._activate_resource("dcim", "devices")
        await pilot.pause()
        app.query_one("#dev_query_input", Input).value = "q=switch01,limit=25"
        await pilot.click("#dev_send_button")
        await pilot.pause()
        await pilot.pause()

        mock_client.request.assert_any_call(
            "GET",
            "/api/dcim/devices/",
            query={"q": "switch01", "limit": "25"},
            payload=None,
        )
        body = app.query_one("#dev_response_body", TextArea)
        status = app.query_one("#dev_response_status", Static)
        assert '"count": 1' in body.text
        assert "HTTP 200" in str(status.content)


@pytest.mark.asyncio
async def test_dev_tui_theme_switch_updates_theme_name(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="default")

    async with app.run_test() as pilot:
        theme_select = app.query_one("#dev_theme_select", Select)
        theme_select.value = "netbox-dark"
        await pilot.pause()
        await pilot.pause()

        assert app.theme_name == "netbox-dark"
        assert app.query_one("#dev_body_editor", TextArea).theme == _text_area_syntax_theme_for(
            "netbox-dark"
        )


@pytest.mark.asyncio
async def test_dev_tui_textareas_follow_app_theme_tokens(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="dracula")

    async with app.run_test() as pilot:
        await pilot.pause()

        body = app.query_one("#dev_body_editor", TextArea)
        response = app.query_one("#dev_response_body", TextArea)

        assert body.theme == "css"
        assert response.theme == "css"
        assert str(body.styles.background) == "Color(40, 42, 54)"
        assert str(response.styles.background) == "Color(40, 42, 54)"
