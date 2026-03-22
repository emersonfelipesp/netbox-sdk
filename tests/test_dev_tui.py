from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.color import Color
from textual.widgets import Input, OptionList, Select, Static, TextArea

from netbox_cli.api import ApiResponse, ConnectionProbe
from netbox_cli.schema import build_schema_index
from netbox_cli.ui.chrome import SWITCH_TO_DEV_TUI, SWITCH_TO_MAIN_TUI
from netbox_cli.ui.dev_app import NetBoxDevTuiApp, _text_area_syntax_theme_for, run_dev_tui
from netbox_cli.ui.dev_state import DevTuiState
from netbox_cli.ui.widgets import NbxButton, NbxPanelBody, NbxPanelHeader

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
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="netbox-dark")

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
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="netbox-dark")

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
async def test_dev_tui_theme_switch_refreshes_existing_surfaces(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="netbox-dark")

    async with app.run_test(size=(160, 50)) as pilot:
        app._activate_resource("dcim", "devices")
        await pilot.pause()

        app.query_one("#dev_theme_select", Select).value = "dracula"
        await pilot.pause()
        await pilot.pause()

        theme = app.theme_catalog.theme_for("dracula")
        expected_surface = Color.parse(theme.colors["surface"])
        expected_panel = Color.parse(theme.colors["panel"])
        expected_background = Color.parse(theme.colors["background"])

        assert app.query_one("#dev_request_panel", object).styles.background == expected_surface
        assert app.query_one("#dev_response_panel", object).styles.background == expected_surface
        assert app.query_one("#dev_operations_tab", object).styles.background == expected_surface
        assert app.query_one("#dev_response_meta", object).styles.background == expected_panel
        assert (
            app.query_one("#dev_operation_list", OptionList).styles.background
            == expected_background
        )
        assert app.query_one("#dev_body_editor", TextArea).styles.background == expected_background


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


@pytest.mark.asyncio
async def test_dev_tui_operation_search_input_follows_theme_tokens(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="netbox-dark")

    async with app.run_test(size=(160, 50)) as pilot:
        app._activate_resource("dcim", "devices")
        await pilot.pause()
        search = app.query_one("#dev_operation_search", Input)
        search.focus()
        await pilot.pause()
        await pilot.pause()

        theme = app.theme_catalog.theme_for("netbox-dark")

        assert search.styles.background == Color.parse(theme.colors["surface"])
        selection = search.get_component_styles("input--selection")
        cursor = search.get_component_styles("input--cursor")

        assert selection.background == Color.parse(theme.colors["primary"]).with_alpha(0.35)
        assert selection.color == search.styles.color
        assert cursor.background == search.styles.color
        assert cursor.color == Color.parse(theme.colors["background"])


@pytest.mark.asyncio
async def test_dev_tui_topbar_context_tracks_selected_resource(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="netbox-dark")

    async with app.run_test() as pilot:
        app._activate_resource("dcim", "devices")
        await pilot.pause()

        topbar_context = app.query_one("#dev_context_line", Static)
        body_context = app.query_one("#dev_context", Static)

        assert str(topbar_context.content) == "Context: DCIM / Devices"
        assert str(body_context.content) == "DCIM / Devices"


def test_nbx_button_adds_size_classes() -> None:
    button = NbxButton("Send", size="medium", tone="primary", id="example_button")

    assert "nbx-button" in button.classes
    assert "nbx-button--medium" in button.classes
    assert "nbx-tone--primary" in button.classes


def test_nbx_panel_primitives_add_prop_classes() -> None:
    header = NbxPanelHeader("Object Attributes", tone="warning")
    body = NbxPanelBody(surface="panel")

    assert "nbx-panel-header" in header.classes
    assert "nbx-tone--warning" in header.classes
    assert "nbx-panel-body" in body.classes
    assert "nbx-surface--panel" in body.classes


def test_dev_tui_view_selector_requests_main_mode(mock_client, real_index) -> None:
    app = NetBoxDevTuiApp(client=mock_client, index=real_index, theme_name="netbox-dark")
    app.exit = MagicMock()

    app.on_view_changed(MagicMock(value="main"))

    app.exit.assert_called_once_with(result=SWITCH_TO_MAIN_TUI)


def test_run_dev_tui_can_switch_back_into_main_tui(mock_client, real_index) -> None:
    launches: list[tuple[str, str | None, bool | None]] = []

    class FakeDevApp:
        def __init__(self, *, client, index, theme_name):  # noqa: ANN001
            launches.append(("dev", theme_name, None))

        def run(self):
            return SWITCH_TO_MAIN_TUI

    class FakeMainApp:
        def __init__(self, *, client, index, theme_name, demo_mode):  # noqa: ANN001
            launches.append(("main", theme_name, demo_mode))

        def run(self):
            return None

    with (
        patch("netbox_cli.ui.dev_app.NetBoxDevTuiApp", FakeDevApp),
        patch("netbox_cli.ui.app.NetBoxTuiApp", FakeMainApp),
    ):
        run_dev_tui(client=mock_client, index=real_index, theme_name="dracula", demo_mode=False)

    assert launches == [
        ("dev", "dracula", None),
        ("main", None, False),
    ]


def test_run_dev_tui_can_switch_back_to_dev_from_main(mock_client, real_index) -> None:
    launches: list[tuple[str, str | None, bool | None]] = []
    main_runs = 0

    class FakeDevApp:
        def __init__(self, *, client, index, theme_name):  # noqa: ANN001
            launches.append(("dev", theme_name, None))

        def run(self):
            return (
                None
                if len([item for item in launches if item[0] == "dev"]) > 1
                else SWITCH_TO_MAIN_TUI
            )

    class FakeMainApp:
        def __init__(self, *, client, index, theme_name, demo_mode):  # noqa: ANN001
            launches.append(("main", theme_name, demo_mode))

        def run(self):
            nonlocal main_runs
            main_runs += 1
            return SWITCH_TO_DEV_TUI if main_runs == 1 else None

    with (
        patch("netbox_cli.ui.dev_app.NetBoxDevTuiApp", FakeDevApp),
        patch("netbox_cli.ui.app.NetBoxTuiApp", FakeMainApp),
    ):
        run_dev_tui(client=mock_client, index=real_index, theme_name="dracula", demo_mode=False)

    assert launches == [
        ("dev", "dracula", None),
        ("main", None, False),
        ("dev", None, None),
    ]
