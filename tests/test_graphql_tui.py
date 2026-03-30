"""Tests for the dedicated GraphQL TUI."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.color import Color
from textual.widgets import Input, OptionList, Static, TextArea

from netbox_sdk.client import ApiResponse, ConnectionProbe
from netbox_tui.graphql_app import NetBoxGraphqlTuiApp
from netbox_tui.graphql_state import GraphqlHistoryEntry, GraphqlTuiState

pytestmark = pytest.mark.suite_tui


def _introspection_payload() -> dict[str, object]:
    return {
        "data": {
            "__schema": {
                "queryType": {"name": "Query"},
                "types": [
                    {
                        "kind": "OBJECT",
                        "name": "Query",
                        "description": "Root query",
                        "fields": [
                            {
                                "name": "device_list",
                                "description": "List devices",
                                "args": [
                                    {
                                        "name": "filters",
                                        "description": None,
                                        "defaultValue": None,
                                        "type": {
                                            "kind": "INPUT_OBJECT",
                                            "name": "DeviceFilter",
                                            "ofType": None,
                                        },
                                    },
                                    {
                                        "name": "pagination",
                                        "description": None,
                                        "defaultValue": None,
                                        "type": {
                                            "kind": "INPUT_OBJECT",
                                            "name": "OffsetPaginationInput",
                                            "ofType": None,
                                        },
                                    },
                                ],
                                "type": {
                                    "kind": "LIST",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "DeviceType",
                                        "ofType": None,
                                    },
                                },
                            },
                            {
                                "name": "cable_term",
                                "description": "Union field",
                                "args": [],
                                "type": {
                                    "kind": "UNION",
                                    "name": "TerminationType",
                                    "ofType": None,
                                },
                            },
                        ],
                        "inputFields": [],
                        "enumValues": [],
                        "possibleTypes": [],
                    },
                    {
                        "kind": "OBJECT",
                        "name": "DeviceType",
                        "description": "Device",
                        "fields": [
                            {
                                "name": "id",
                                "description": None,
                                "args": [],
                                "type": {"kind": "SCALAR", "name": "ID", "ofType": None},
                            },
                            {
                                "name": "name",
                                "description": None,
                                "args": [],
                                "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                            },
                            {
                                "name": "status",
                                "description": None,
                                "args": [],
                                "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                            },
                        ],
                        "inputFields": [],
                        "enumValues": [],
                        "possibleTypes": [],
                    },
                    {
                        "kind": "INPUT_OBJECT",
                        "name": "DeviceFilter",
                        "description": "Device filters",
                        "fields": [],
                        "inputFields": [
                            {
                                "name": "name",
                                "description": None,
                                "defaultValue": None,
                                "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                            }
                        ],
                        "enumValues": [],
                        "possibleTypes": [],
                    },
                    {
                        "kind": "INPUT_OBJECT",
                        "name": "OffsetPaginationInput",
                        "description": "Pagination",
                        "fields": [],
                        "inputFields": [
                            {
                                "name": "limit",
                                "description": None,
                                "defaultValue": None,
                                "type": {"kind": "SCALAR", "name": "Int", "ofType": None},
                            },
                            {
                                "name": "offset",
                                "description": None,
                                "defaultValue": None,
                                "type": {"kind": "SCALAR", "name": "Int", "ofType": None},
                            },
                        ],
                        "enumValues": [],
                        "possibleTypes": [],
                    },
                    {
                        "kind": "UNION",
                        "name": "TerminationType",
                        "description": "Union",
                        "fields": [],
                        "inputFields": [],
                        "enumValues": [],
                        "possibleTypes": [
                            {"name": "ConsolePortType"},
                            {"name": "CircuitTerminationType"},
                        ],
                    },
                    {
                        "kind": "OBJECT",
                        "name": "ConsolePortType",
                        "description": "Console port",
                        "fields": [
                            {
                                "name": "id",
                                "description": None,
                                "args": [],
                                "type": {"kind": "SCALAR", "name": "ID", "ofType": None},
                            }
                        ],
                        "inputFields": [],
                        "enumValues": [],
                        "possibleTypes": [],
                    },
                    {
                        "kind": "OBJECT",
                        "name": "CircuitTerminationType",
                        "description": "Circuit termination",
                        "fields": [
                            {
                                "name": "id",
                                "description": None,
                                "args": [],
                                "type": {"kind": "SCALAR", "name": "ID", "ofType": None},
                            }
                        ],
                        "inputFields": [],
                        "enumValues": [],
                        "possibleTypes": [],
                    },
                ],
            }
        }
    }


@pytest.fixture(autouse=True)
def isolate_graphql_tui_state():
    with (
        patch("netbox_tui.graphql_app.load_graphql_tui_state", return_value=GraphqlTuiState()),
        patch("netbox_tui.graphql_app.save_graphql_tui_state", return_value=None),
    ):
        yield


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.probe_connection = AsyncMock(
        return_value=ConnectionProbe(status=200, version="4.2", ok=True, error=None)
    )

    async def graphql_side_effect(query, variables=None):
        if "__schema" in query:
            return ApiResponse(
                status=200,
                text=json.dumps(_introspection_payload()),
                headers={"Content-Type": "application/json"},
            )
        if "bad_field" in query:
            return ApiResponse(
                status=200,
                text=json.dumps({"errors": [{"message": "Invalid field"}]}),
                headers={"Content-Type": "application/json"},
            )
        return ApiResponse(
            status=200,
            text=json.dumps({"data": {"device_list": [{"id": 1, "name": "edge-1"}]}}),
            headers={"Content-Type": "application/json"},
        )

    client.graphql = AsyncMock(side_effect=graphql_side_effect)
    client.request = AsyncMock(
        return_value=ApiResponse(
            status=200,
            text="{}",
            headers={"Content-Type": "application/json", "API-Version": "4.2"},
        )
    )
    return client


@pytest.mark.asyncio
async def test_graphql_tui_loads_introspection_and_builds_query(mock_client) -> None:
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        field_list = app.query_one("#graphql_field_list", OptionList)
        details = app.query_one("#graphql_field_details", Static)

        assert field_list.option_count == 2
        assert "device_list" in str(details.content)

        await pilot.click("#graphql_build_field_button")
        await pilot.pause()

        editor = app.query_one("#graphql_query_editor", TextArea)
        assert "query {" in editor.text
        assert "device_list" in editor.text
        assert "id" in editor.text


@pytest.mark.asyncio
async def test_graphql_tui_guided_snippets_cover_filters_pagination_and_fragments(
    mock_client,
) -> None:
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        await pilot.click("#graphql_insert_filters_button")
        await pilot.pause()
        await pilot.click("#graphql_insert_pagination_button")
        await pilot.pause()

        field_search = app.query_one("#graphql_field_search", Input)
        field_search.value = "cable"
        app._select_root_field("cable_term")
        await pilot.pause()
        await pilot.pause()

        app.on_insert_fragments_button_pressed()
        await pilot.pause()

        editor = app.query_one("#graphql_query_editor", TextArea)
        assert "filters:" in editor.text
        assert "pagination:" in editor.text
        assert "... on ConsolePortType" in editor.text


@pytest.mark.asyncio
async def test_graphql_tui_executes_queries_and_surfaces_graphql_errors(mock_client) -> None:
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")
    app.notify = MagicMock()

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        app.query_one("#graphql_query_editor", TextArea).text = "query { bad_field }"
        app.query_one("#graphql_variables_editor", TextArea).text = json.dumps({"id": 1})
        app.send_query_via_worker()
        await pilot.pause()
        await pilot.pause()

        mock_client.graphql.assert_any_call("query { bad_field }", {"id": 1})
        status = app.query_one("#graphql_response_status", Static)
        body = app.query_one("#graphql_response_body", TextArea)
        summary = app.query_one("#graphql_response_summary", Static)

        assert "GraphQL errors" in str(status.content)
        assert "Invalid field" in body.text
        assert "Errors: Invalid field" in str(summary.content)


@pytest.mark.asyncio
async def test_graphql_tui_invalid_variables_fail_before_request(mock_client) -> None:
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")
    app.notify = MagicMock()

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        initial_calls = mock_client.graphql.await_count
        app.query_one("#graphql_query_editor", TextArea).text = "query { device_list { id } }"
        app.query_one("#graphql_variables_editor", TextArea).text = "[]"
        app.send_query_via_worker()
        await pilot.pause()
        await pilot.pause()

        assert mock_client.graphql.await_count == initial_calls
        status = app.query_one("#graphql_response_status", Static)
        body = app.query_one("#graphql_response_body", TextArea)

        assert "GraphQL request failed" in str(status.content)
        assert "must decode to a JSON object" in body.text
        app.notify.assert_called_with(
            "GraphQL variables must decode to a JSON object.", severity="error"
        )


@pytest.mark.asyncio
async def test_graphql_tui_copy_response_button_copies_formatted_body(mock_client) -> None:
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")
    app.copy_to_clipboard = MagicMock()
    app.notify = MagicMock()

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        app.query_one("#graphql_query_editor", TextArea).text = "query { device_list { id name } }"
        app.send_query_via_worker()
        await pilot.pause()
        await pilot.pause()

        app.on_copy_response_button_pressed()

        copied = app.query_one("#graphql_response_body", TextArea).text
        app.copy_to_clipboard.assert_called_once_with(copied)
        app.notify.assert_called_with(
            "GraphQL response copied to clipboard.", severity="information"
        )


@pytest.mark.asyncio
async def test_graphql_tui_history_selection_restores_saved_query_and_variables(
    mock_client,
) -> None:
    seeded_state = GraphqlTuiState(
        history=[
            GraphqlHistoryEntry(
                title="query { device_list { id } }",
                query_text="query { device_list { id } }",
                variables_text='{"limit": 5}',
            )
        ]
    )
    with (
        patch("netbox_tui.graphql_app.load_graphql_tui_state", return_value=seeded_state),
        patch("netbox_tui.graphql_app.save_graphql_tui_state", return_value=None),
    ):
        app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")

        async with app.run_test(size=(180, 50)) as pilot:
            await pilot.pause()
            await pilot.pause()

            app.on_history_selected(type("Event", (), {"option_index": 0})())
            await pilot.pause()

            assert (
                app.query_one("#graphql_query_editor", TextArea).text
                == "query { device_list { id } }"
            )
            assert app.query_one("#graphql_variables_editor", TextArea).text == '{"limit": 5}'
            assert "Loaded history item" in str(
                app.query_one("#graphql_response_summary", Static).content
            )


@pytest.mark.asyncio
async def test_graphql_tui_introspection_failure_falls_back_to_manual_mode(mock_client) -> None:
    async def failing_graphql(query, variables=None):
        del variables
        if "__schema" in query:
            return ApiResponse(
                status=200,
                text=json.dumps({"errors": [{"message": "Introspection disabled"}]}),
                headers={"Content-Type": "application/json"},
            )
        return ApiResponse(
            status=200,
            text=json.dumps({"data": {"device_list": [{"id": 1}]}}),
            headers={"Content-Type": "application/json"},
        )

    mock_client.graphql = AsyncMock(side_effect=failing_graphql)
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="dracula")

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        details = app.query_one("#graphql_field_details", Static)
        field_list = app.query_one("#graphql_field_list", OptionList)
        assert "Schema introspection unavailable" in str(details.content)
        assert field_list.option_count == 1

        app.query_one("#graphql_query_editor", TextArea).text = "query { device_list { id } }"
        app.send_query_via_worker()
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

        assert "device_list" in app.query_one("#graphql_response_body", TextArea).text


@pytest.mark.asyncio
async def test_graphql_tui_theme_switch_refreshes_existing_surfaces(mock_client) -> None:
    app = NetBoxGraphqlTuiApp(client=mock_client, theme_name="netbox-dark")

    async with app.run_test(size=(180, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        app.query_one("#graphql_theme_select", object).value = "dracula"
        await pilot.pause()
        await pilot.pause()

        theme = app.theme_catalog.theme_for("dracula")
        expected_surface = Color.parse(theme.colors["surface"])
        expected_background = Color.parse(theme.colors["background"])
        expected_panel = Color.parse(theme.colors["panel"])
        expected_primary = Color.parse(theme.colors["primary"])

        assert app.theme_name == "dracula"
        assert app.query_one("#graphql_sidebar", object).styles.background == expected_surface
        assert app.query_one("#graphql_builder_panel", object).styles.background == expected_surface
        assert (
            app.query_one("#graphql_response_panel", object).styles.background == expected_surface
        )
        assert app.query_one("#graphql_response_meta", object).styles.background == expected_panel
        assert (
            app.query_one("#graphql_field_list", OptionList).styles.background
            == expected_background
        )
        assert (
            app.query_one("#graphql_query_editor", TextArea).styles.background
            == expected_background
        )
        assert app.query_one("#graphql_build_field_button", object).styles.color == expected_primary
